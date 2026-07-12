"""
LangGraph state definition for the hospital triage agent.
All nodes read from and write to this TypedDict.
"""
from __future__ import annotations

from typing import Optional, TypedDict


class TriageState(TypedDict, total=False):
    # ── Raw form inputs ──────────────────────────────────────
    patient_name: str
    raw_age: str          # free-text age as typed by the patient
    age: Optional[int]    # normalised integer age
    gender: str
    query: str            # symptom description

    # ── Classification outputs ───────────────────────────────
    ward: str             # emergency | mental_health | general
    reasoning: str        # LLM explanation or fallback message
    priority: str         # high | normal
    llm_failed: bool      # True if Groq timed out / errored

    # ── Assignment outputs ───────────────────────────────────
    assigned_doctor_id: Optional[str]
    assigned_doctor_name: Optional[str]
    queue_position: Optional[int]   # set only when no doctor is free
    appointment_id: Optional[str]

    # ── Error tracking ───────────────────────────────────────
    error: Optional[str]
