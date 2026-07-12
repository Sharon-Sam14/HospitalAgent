"""
Seed script — reads doctors.csv and upserts into Supabase.

Usage (from repo root OR from inside database/):
    python database/seed.py
    python seed.py

Credentials are loaded automatically from the .env file in the repo root.
You can also export them manually before running:
    $env:SUPABASE_URL = "..."
    $env:SUPABASE_KEY = "..."
"""
from __future__ import annotations

import csv
import os
import sys
from pathlib import Path

# Allow running from repo root or from inside database/
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# ── Auto-load .env from repo root ─────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    _env_path = ROOT / ".env"
    if _env_path.exists():
        load_dotenv(_env_path, override=False)  # don't override already-set vars
        print(f"[INFO] Loaded environment from {_env_path}")
except ImportError:
    pass  # python-dotenv not installed; rely on manually exported vars

# Set env vars before importing client (if not already set)
def _require_env(var: str) -> str:
    val = os.environ.get(var)
    if not val:
        raise EnvironmentError(
            f"Missing environment variable: {var}\n"
            f"Add it to '{ROOT / '.env'}' or export it manually:\n"
            f"  PowerShell:  $env:{var} = 'your-value'\n"
            f"  CMD/bash:    set {var}=your-value"
        )
    return val


def load_csv(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [row for row in reader if row.get("doctor_name", "").strip()]


# Ward → default specialization mapping
SPECIALIZATION_MAP: dict[str, str] = {
    "general": "General Practice",
    "emergency": "Emergency Medicine",
    "mental_health": "Psychiatry",
}

# CSV status → DB status mapping
STATUS_MAP: dict[str, str] = {
    "active": "free",
    "free": "free",
    "busy": "busy",
    "on_leave": "on_leave",
}


def build_doctor_record(row: dict) -> dict:
    ward = row.get("ward", "general").strip().lower()
    csv_status = row.get("status", "active").strip().lower()
    db_status = STATUS_MAP.get(csv_status, "free")

    # Convert slot time to shift start; shift end = shift_start + 8 h (default)
    shift_start = row.get("next_slot", "09:00").strip() or "09:00"

    return {
        "name": row["doctor_name"].strip(),
        "ward": ward,
        "specialization": SPECIALIZATION_MAP.get(ward, "General Practice"),
        "status": db_status,
        "shift_start": shift_start,
        "shift_end": "17:00",  # default 8-hour shift
    }


def seed():
    _require_env("SUPABASE_URL")
    _require_env("SUPABASE_KEY")

    from database.client import get_client  # noqa: PLC0415

    csv_path = ROOT / "doctors.csv"
    if not csv_path.exists():
        print(f"[ERROR] doctors.csv not found at {csv_path}")
        sys.exit(1)

    rows = load_csv(csv_path)
    records = [build_doctor_record(r) for r in rows]

    print(f"[INFO] Seeding {len(records)} doctors …")

    client = get_client()
    result = (
        client.table("doctors")
        .upsert(records, on_conflict="name")  # idempotent on name
        .execute()
    )

    if hasattr(result, "data") and result.data:
        print(f"[OK]   Upserted {len(result.data)} doctor records:")
        for doc in result.data:
            print(f"       • {doc['name']} — {doc['ward']} ({doc['status']})")
    else:
        print("[WARN] Upsert returned no data; check Supabase for errors.")


if __name__ == "__main__":
    seed()
