"""
Doctor dashboard view — STUB for backend wiring.

When connecting the real backend, replace mock data reads with:
    from services.doctor_service import get_doctor_by_name, update_doctor_status
    from services.appointment_service import get_appointments_for_doctor, mark_appointment_done

The full mock UI lives in app.py → render_doctor_view().
"""
import streamlit as st


def render() -> None:
    """Called by app.py routing when doctor view is selected."""
    from app import render_doctor_view  # noqa: PLC0415
    render_doctor_view()
