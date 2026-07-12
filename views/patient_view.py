"""
Patient intake view — STUB for backend wiring.

When connecting the real backend, replace this with:
    from services.triage_service import run_triage
    result = run_triage(form_data)

The full mock UI lives in app.py → render_patient_view().
"""
import streamlit as st


def render() -> None:
    """Called by app.py routing when patient view is selected."""
    # Imported here to avoid circular dependency
    from app import render_patient_view  # noqa: PLC0415
    render_patient_view()
