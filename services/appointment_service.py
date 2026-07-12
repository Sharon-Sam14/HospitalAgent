"""
Appointment service — CRUD, queue management, notes, and status transitions.
"""
from __future__ import annotations

import logging
from typing import Optional

from database.client import get_client
import config
from services.doctor_service import update_doctor_status

logger = logging.getLogger(__name__)


# ── Read ──────────────────────────────────────────────────────────────────────

def get_appointments_for_doctor(doctor_id: str) -> list[dict]:
    """
    Return active appointments (waiting / in_progress) assigned to a doctor.
    Sorted: priority=high first, then oldest first (emergency never waits).
    """
    try:
        result = (
            get_client()
            .table("appointments")
            .select("*, doctors(name, ward, specialization)")
            .eq("assigned_doctor_id", doctor_id)
            .in_("status", [config.APPT_STATUS_WAITING, config.APPT_STATUS_IN_PROGRESS])
            .execute()
        )
        rows = result.data or []

        # Python-side sort: high priority first, then by created_at ascending
        rows.sort(
            key=lambda r: (
                0 if r.get("priority") == config.PRIORITY_HIGH else 1,
                r.get("created_at", ""),
            )
        )
        return rows
    except Exception as exc:
        logger.error("get_appointments_for_doctor(%s) failed: %s", doctor_id, exc)
        return []


def get_all_waiting_appointments(ward: Optional[str] = None) -> list[dict]:
    """Return all waiting appointments, optionally filtered by ward."""
    try:
        query = (
            get_client()
            .table("appointments")
            .select("*")
            .eq("status", config.APPT_STATUS_WAITING)
        )
        if ward:
            query = query.eq("ward", ward)
        result = query.order("created_at").execute()
        return result.data or []
    except Exception as exc:
        logger.error("get_all_waiting_appointments failed: %s", exc)
        return []


def get_queue_position(ward: str, appointment_id: str) -> int:
    """
    Return the 1-indexed position of this appointment in the ward's waiting queue.
    Lower = closer to front.
    """
    try:
        # Fetch all waiting appointments for this ward ordered by priority (high first), then time
        result = (
            get_client()
            .table("appointments")
            .select("id, priority, created_at")
            .eq("ward", ward)
            .eq("status", config.APPT_STATUS_WAITING)
            .execute()
        )
        rows = result.data or []
        rows.sort(
            key=lambda r: (
                0 if r.get("priority") == config.PRIORITY_HIGH else 1,
                r.get("created_at", ""),
            )
        )
        for i, row in enumerate(rows, start=1):
            if row["id"] == appointment_id:
                return i
        return len(rows)  # fallback: put at end
    except Exception as exc:
        logger.error("get_queue_position failed: %s", exc)
        return -1


def get_appointment_by_id(appointment_id: str) -> Optional[dict]:
    """Fetch a single appointment by ID."""
    try:
        result = (
            get_client()
            .table("appointments")
            .select("*")
            .eq("id", appointment_id)
            .limit(1)
            .execute()
        )
        data = result.data or []
        return data[0] if data else None
    except Exception as exc:
        logger.error("get_appointment_by_id(%s) failed: %s", appointment_id, exc)
        return None


# ── Write ─────────────────────────────────────────────────────────────────────

def mark_appointment_done(appointment_id: str, doctor_id: str, doctor_name: str) -> bool:
    """
    Mark an appointment as done.
    Flip the assigned doctor's status back to free.
    Both actions are logged in status_log (via update_doctor_status).
    Returns True on success.
    """
    client = get_client()
    try:
        # 1. Mark appointment done
        client.table("appointments").update(
            {"status": config.APPT_STATUS_DONE}
        ).eq("id", appointment_id).execute()

        # 2. Free up the doctor
        update_doctor_status(
            doctor_id=doctor_id,
            new_status=config.DOCTOR_STATUS_FREE,
            changed_by=doctor_name,
        )

        return True
    except Exception as exc:
        logger.error("mark_appointment_done(%s) failed: %s", appointment_id, exc)
        return False


def update_appointment_notes(appointment_id: str, notes: str) -> bool:
    """Persist doctor notes on an appointment."""
    try:
        get_client().table("appointments").update({"notes": notes}).eq(
            "id", appointment_id
        ).execute()
        return True
    except Exception as exc:
        logger.error("update_appointment_notes(%s) failed: %s", appointment_id, exc)
        return False


def get_done_appointments_for_doctor(doctor_id: str, limit: int = 20) -> list[dict]:
    """Return recently completed appointments for a doctor (for history view)."""
    try:
        result = (
            get_client()
            .table("appointments")
            .select("*")
            .eq("assigned_doctor_id", doctor_id)
            .eq("status", config.APPT_STATUS_DONE)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []
    except Exception as exc:
        logger.error("get_done_appointments_for_doctor(%s) failed: %s", doctor_id, exc)
        return []
