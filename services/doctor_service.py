"""
Doctor service — CRUD and status management for the doctors table.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from database.client import get_client
import config

logger = logging.getLogger(__name__)


# ── Read ──────────────────────────────────────────────────────────────────────

def get_all_doctors() -> list[dict]:
    """Return all doctors ordered by ward, then name."""
    try:
        result = (
            get_client()
            .table("doctors")
            .select("*")
            .order("ward")
            .order("name")
            .execute()
        )
        return result.data or []
    except Exception as exc:
        logger.error("get_all_doctors failed: %s", exc)
        return []


def get_doctor_by_name(name: str) -> Optional[dict]:
    """Lookup a single doctor by exact name (used for login)."""
    try:
        result = (
            get_client()
            .table("doctors")
            .select("*")
            .eq("name", name)
            .limit(1)
            .execute()
        )
        data = result.data or []
        return data[0] if data else None
    except Exception as exc:
        logger.error("get_doctor_by_name(%s) failed: %s", name, exc)
        return None


def get_doctors_by_ward(ward: str) -> list[dict]:
    """Return all doctors for a given ward."""
    try:
        result = (
            get_client()
            .table("doctors")
            .select("*")
            .eq("ward", ward)
            .order("name")
            .execute()
        )
        return result.data or []
    except Exception as exc:
        logger.error("get_doctors_by_ward(%s) failed: %s", ward, exc)
        return []


# ── Write ─────────────────────────────────────────────────────────────────────

def update_doctor_status(
    doctor_id: str,
    new_status: str,
    changed_by: str = "system",
) -> bool:
    """
    Update a doctor's status and append an entry to status_log.
    Returns True on success, False on failure.
    """
    client = get_client()

    try:
        # Fetch current status for audit log
        current = (
            client.table("doctors")
            .select("status")
            .eq("doctor_id", doctor_id)
            .limit(1)
            .execute()
        )
        old_status: str = (current.data or [{}])[0].get("status", "unknown")

        # Update doctors table
        client.table("doctors").update({"status": new_status}).eq(
            "doctor_id", doctor_id
        ).execute()

        # Audit log
        client.table("status_log").insert(
            {
                "doctor_id":  doctor_id,
                "old_status": old_status,
                "new_status": new_status,
                "changed_by": changed_by,
            }
        ).execute()

        return True

    except Exception as exc:
        logger.error("update_doctor_status(%s → %s) failed: %s", doctor_id, new_status, exc)
        return False


def get_status_log(doctor_id: str, limit: int = 20) -> list[dict]:
    """Return recent status log entries for a given doctor."""
    try:
        result = (
            get_client()
            .table("status_log")
            .select("*")
            .eq("doctor_id", doctor_id)
            .order("timestamp", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []
    except Exception as exc:
        logger.error("get_status_log(%s) failed: %s", doctor_id, exc)
        return []
