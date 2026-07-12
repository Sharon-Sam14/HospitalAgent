"""
Triage service — public API consumed by the Streamlit patient view.

Usage:
    from services.triage_service import run_triage
    result = run_triage(form_data)
"""
from __future__ import annotations

import logging
from typing import Any

from agent.graph import build_graph
import config

logger = logging.getLogger(__name__)


def run_triage(form_data: dict[str, Any]) -> dict[str, Any]:
    """
    Execute the full triage LangGraph pipeline.

    Parameters
    ----------
    form_data : dict
        Keys expected:
          - patient_name (str)
          - raw_age      (str)  — free-text age
          - gender       (str)
          - query        (str)  — symptom description

    Returns
    -------
    dict with keys:
      - success          (bool)
      - appointment_id   (str | None)
      - patient_name     (str)
      - ward             (str)
      - priority         (str)
      - reasoning        (str)
      - assigned_doctor  (str | None)  — doctor name or None
      - queue_position   (int | None)  — set when no doctor free
      - llm_failed       (bool)
      - error            (str | None)
    """
    # Build initial state
    initial_state = {
        "patient_name": form_data.get("patient_name", "").strip(),
        "raw_age":      str(form_data.get("raw_age", "")).strip(),
        "gender":       form_data.get("gender", "").strip(),
        "query":        form_data.get("query", "").strip(),
    }

    try:
        graph = build_graph()
        final_state: dict = graph.invoke(initial_state)

        # Surface any internal error set by nodes
        if final_state.get("error"):
            return _error_result(
                final_state["error"],
                patient_name=initial_state["patient_name"],
            )

        return {
            "success":         True,
            "appointment_id":  final_state.get("appointment_id"),
            "patient_name":    final_state.get("patient_name", ""),
            "ward":            final_state.get("ward", config.WARDS[-1]),
            "priority":        final_state.get("priority", config.PRIORITY_NORMAL),
            "reasoning":       final_state.get("reasoning", ""),
            "assigned_doctor": final_state.get("assigned_doctor_name"),
            "queue_position":  final_state.get("queue_position"),
            "llm_failed":      final_state.get("llm_failed", False),
            "error":           None,
        }

    except Exception as exc:
        logger.exception("Unhandled error in triage graph: %s", exc)
        return _error_result(str(exc), patient_name=initial_state["patient_name"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _error_result(error_msg: str, *, patient_name: str = "") -> dict[str, Any]:
    """Return a safe fallback result dict when the graph fails."""
    return {
        "success":         False,
        "appointment_id":  None,
        "patient_name":    patient_name,
        "ward":            "general",
        "priority":        config.PRIORITY_NORMAL,
        "reasoning":       "LLM failure — needs manual review.",
        "assigned_doctor": None,
        "queue_position":  None,
        "llm_failed":      True,
        "error":           error_msg,
    }
