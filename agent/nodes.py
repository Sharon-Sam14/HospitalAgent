"""
LangGraph node functions for the hospital triage agent.

Nodes (in execution order):
  1. intake_node        — validate & normalise inputs (age text → int)
  2. router_node        — classify ward via LLM + safety-net keyword override
  3. ward_node          — set priority, enrich state
  4. doctor_assign_node — atomic DB doctor assignment or queue placement
"""
from __future__ import annotations

import json
import re
import logging
from typing import Any

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

from agent.state import TriageState
from agent.prompts import WARD_CLASSIFICATION_PROMPT, AGE_PARSE_PROMPT
import config

logger = logging.getLogger(__name__)

# ── LLM singleton ─────────────────────────────────────────────────────────────
def _get_llm() -> ChatGroq:
    return ChatGroq(
        api_key=config.GROQ_API_KEY,
        model=config.LLM_MODEL,
        temperature=config.LLM_TEMPERATURE,
        timeout=config.LLM_TIMEOUT_SECONDS,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Node 1 — intake_node
# ═══════════════════════════════════════════════════════════════════════════════

def _parse_age_regex(raw: str) -> int | None:
    """
    Try to parse age from a string using regex + word-to-number map.
    Returns None if unable to parse.
    """
    raw = raw.strip().lower()

    # Direct digit match
    match = re.search(r"\b(\d{1,3})\b", raw)
    if match:
        val = int(match.group(1))
        if 0 < val < 150:
            return val

    # Word-based: "thirty two", "twenty-five", etc.
    tokens = re.split(r"[\s\-]+", raw)
    total = 0
    for token in tokens:
        num = config.WORD_TO_NUM.get(token)
        if num is not None:
            total += num
    if 0 < total < 150:
        return total

    return None


def _parse_age_llm(raw: str) -> int | None:
    """Fallback: ask LLM to extract age as integer."""
    try:
        llm = _get_llm()
        prompt = AGE_PARSE_PROMPT.format(raw_age=raw)
        response = llm.invoke([HumanMessage(content=prompt)])
        text = response.content.strip()
        val = int(re.search(r"\d+", text).group())
        return val if 0 < val < 150 else None
    except Exception:
        return None


def intake_node(state: TriageState) -> TriageState:
    """Validate required fields; normalise age text → int."""
    updates: dict[str, Any] = {}

    # Required field checks
    for field in ("patient_name", "query"):
        if not state.get(field, "").strip():
            updates["error"] = f"Missing required field: {field}"
            return {**state, **updates}

    # Age normalisation
    raw_age: str = state.get("raw_age", "").strip()
    age = _parse_age_regex(raw_age)
    if age is None:
        age = _parse_age_llm(raw_age)
    if age is None:
        age = 0  # Unknown — store as 0, flag in reasoning later

    updates["age"] = age
    updates["llm_failed"] = False  # reset

    return {**state, **updates}


# ═══════════════════════════════════════════════════════════════════════════════
# Node 2 — router_node
# ═══════════════════════════════════════════════════════════════════════════════

def _keyword_override(query: str) -> tuple[str, str] | None:
    """
    Check query against hardcoded safety-net keywords.
    Returns (ward, reasoning) if a keyword matches, else None.
    Emergency keywords take precedence over crisis keywords.
    """
    q_lower = query.lower()

    for kw in config.EMERGENCY_KEYWORDS:
        if kw in q_lower:
            return (
                "emergency",
                f"Safety-net override: detected emergency keyword '{kw}'.",
            )

    for kw in config.CRISIS_KEYWORDS:
        if kw in q_lower:
            return (
                "mental_health",
                f"Safety-net override: detected crisis keyword '{kw}'.",
            )

    return None


def _call_llm_classify(state: TriageState) -> tuple[str, str]:
    """
    Call Groq LLM to classify ward.
    Returns (ward, reasoning). Falls back to ('general', fallback_msg) on error.
    """
    prompt = WARD_CLASSIFICATION_PROMPT.format(
        query=state.get("query", ""),
        age=state.get("age", "unknown"),
        gender=state.get("gender", "unknown"),
    )

    try:
        llm = _get_llm()
        response = llm.invoke([HumanMessage(content=prompt)])
        raw = response.content.strip()

        # Strip markdown code fences if present
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        parsed = json.loads(raw)
        ward = parsed.get("ward", "general").lower()
        reasoning = parsed.get("reasoning", "LLM provided no reasoning.")

        # Validate ward value
        if ward not in config.WARDS:
            ward = "general"
            reasoning += " [Ward corrected to general — LLM returned invalid ward]"

        return ward, reasoning

    except TimeoutError:
        logger.warning("Groq LLM timed out — falling back to 'general' ward.")
        return "general", "LLM timeout — needs manual review."

    except Exception as exc:
        logger.error("LLM classification failed: %s", exc)
        return "general", f"LLM failure — needs manual review. ({type(exc).__name__})"


def router_node(state: TriageState) -> TriageState:
    """Classify ward via safety-net keywords first, then LLM."""
    if state.get("error"):
        return state  # pass-through on prior error

    query: str = state.get("query", "")

    # Safety-net keyword override (always takes precedence)
    override = _keyword_override(query)
    if override:
        ward, reasoning = override
        return {**state, "ward": ward, "reasoning": reasoning, "llm_failed": False}

    # LLM classification
    ward, reasoning = _call_llm_classify(state)
    llm_failed = "LLM failure" in reasoning or "LLM timeout" in reasoning

    return {**state, "ward": ward, "reasoning": reasoning, "llm_failed": llm_failed}


# ═══════════════════════════════════════════════════════════════════════════════
# Node 3 — ward_node
# ═══════════════════════════════════════════════════════════════════════════════

def ward_node(state: TriageState) -> TriageState:
    """
    Set priority based on ward classification.
    emergency  → always high
    mental_health + crisis keyword → high
    mental_health (general distress) → normal
    general → normal
    """
    if state.get("error"):
        return state

    ward: str = state.get("ward", "general")
    reasoning: str = state.get("reasoning", "")
    query: str = state.get("query", "").lower()

    if ward == "emergency":
        priority = config.PRIORITY_HIGH
    elif ward == "mental_health":
        # Elevate to high if any crisis keyword present
        priority = (
            config.PRIORITY_HIGH
            if any(kw in query for kw in config.CRISIS_KEYWORDS)
            else config.PRIORITY_NORMAL
        )
    else:
        priority = config.PRIORITY_NORMAL

    # Flag unknown age in reasoning
    age = state.get("age", 0)
    if age == 0:
        reasoning = f"[Age unknown — could not parse '{state.get('raw_age', '')}'] " + reasoning

    return {**state, "priority": priority, "reasoning": reasoning}


# ═══════════════════════════════════════════════════════════════════════════════
# Node 4 — doctor_assign_node
# ═══════════════════════════════════════════════════════════════════════════════

def doctor_assign_node(state: TriageState) -> TriageState:
    """
    1. Save appointment to DB.
    2. Atomically try to assign a free doctor in the same ward.
    3. If successful: link doctor to appointment, log status change.
    4. If no free doctor: leave appointment in 'waiting', compute queue position.
    """
    if state.get("error"):
        return state

    from database.client import get_client  # lazy import — avoids Streamlit secret access at module load
    from datetime import datetime, timezone

    client = get_client()
    ward: str = state.get("ward", "general")
    priority: str = state.get("priority", config.PRIORITY_NORMAL)

    # ── Step 1: Insert appointment (unassigned initially) ──
    appt_data = {
        "patient_name": state.get("patient_name", "Unknown"),
        "age": state.get("age") or None,
        "gender": state.get("gender", ""),
        "query": state.get("query", ""),
        "ward": ward,
        "reasoning": state.get("reasoning", ""),
        "priority": priority,
        "status": config.APPT_STATUS_WAITING,
        "assigned_doctor_id": None,
    }

    try:
        appt_result = client.table("appointments").insert(appt_data).execute()
        appointment_id: str = appt_result.data[0]["id"]
    except Exception as exc:
        logger.error("Failed to insert appointment: %s", exc)
        return {**state, "error": f"DB insert failed: {exc}"}

    # ── Step 2: Find free doctors in ward (ordered by name for determinism) ──
    try:
        doctors_result = (
            client.table("doctors")
            .select("doctor_id, name")
            .eq("ward", ward)
            .eq("status", config.DOCTOR_STATUS_FREE)
            .order("name")
            .execute()
        )
        candidates: list[dict] = doctors_result.data or []
    except Exception as exc:
        logger.error("Failed to query doctors: %s", exc)
        candidates = []

    # ── Step 3: Atomic assignment loop ──
    assigned_doctor_id = None
    assigned_doctor_name = None

    for candidate in candidates:
        doc_id: str = candidate["doctor_id"]
        doc_name: str = candidate["name"]

        try:
            # Conditional update — only succeeds if status is STILL 'free'
            update_result = (
                client.table("doctors")
                .update({"status": config.DOCTOR_STATUS_BUSY})
                .eq("doctor_id", doc_id)
                .eq("status", config.DOCTOR_STATUS_FREE)   # <-- atomic guard
                .execute()
            )

            if update_result.data:  # rows affected → assignment successful
                assigned_doctor_id = doc_id
                assigned_doctor_name = doc_name

                # Link doctor to appointment
                client.table("appointments").update(
                    {
                        "assigned_doctor_id": doc_id,
                        "status": config.APPT_STATUS_IN_PROGRESS,
                    }
                ).eq("id", appointment_id).execute()

                # Audit log
                client.table("status_log").insert(
                    {
                        "doctor_id": doc_id,
                        "old_status": config.DOCTOR_STATUS_FREE,
                        "new_status": config.DOCTOR_STATUS_BUSY,
                        "changed_by": "system",
                    }
                ).execute()

                break  # done

        except Exception as exc:
            logger.warning("Atomic update failed for doctor %s: %s", doc_id, exc)
            continue  # try next candidate

    # ── Step 4: Queue position if no doctor assigned ──
    queue_position = None
    if assigned_doctor_id is None:
        try:
            count_result = (
                client.table("appointments")
                .select("id", count="exact")
                .eq("ward", ward)
                .eq("status", config.APPT_STATUS_WAITING)
                .execute()
            )
            # The newly inserted appointment is included in the count
            # Queue position = count (they are at the back)
            queue_position = count_result.count or 1
        except Exception:
            queue_position = None

    return {
        **state,
        "appointment_id": appointment_id,
        "assigned_doctor_id": assigned_doctor_id,
        "assigned_doctor_name": assigned_doctor_name,
        "queue_position": queue_position,
    }
