"""
Central configuration for the Hospital Triage System.
All values are read from Streamlit secrets (secrets.toml locally,
Streamlit Cloud secrets manager in production).
"""
from __future__ import annotations

import streamlit as st

# ── Supabase ─────────────────────────────────────────────────
SUPABASE_URL: str = st.secrets["SUPABASE_URL"]
SUPABASE_KEY: str = st.secrets["SUPABASE_KEY"]

# ── Groq / LLM ───────────────────────────────────────────────
GROQ_API_KEY: str = st.secrets["GROQ_API_KEY"]
LLM_MODEL: str = "llama-3.3-70b-versatile"
LLM_TIMEOUT_SECONDS: int = 15          # seconds before we fall back to 'general'
LLM_TEMPERATURE: float = 0.1           # low for deterministic classification

# ── Doctor passwords ─────────────────────────────────────────
# Stored as a dict in secrets:  [DOCTOR_PASSWORDS] "Dr. Khan" = "pass"
DOCTOR_PASSWORDS: dict[str, str] = dict(st.secrets.get("DOCTOR_PASSWORDS", {}))

# ── Domain constants ─────────────────────────────────────────
WARDS: list[str] = ["emergency", "mental_health", "general"]

PRIORITY_HIGH: str = "high"
PRIORITY_NORMAL: str = "normal"

DOCTOR_STATUS_FREE: str = "free"
DOCTOR_STATUS_BUSY: str = "busy"
DOCTOR_STATUS_LEAVE: str = "on_leave"

APPT_STATUS_WAITING: str = "waiting"
APPT_STATUS_IN_PROGRESS: str = "in_progress"
APPT_STATUS_DONE: str = "done"

# ── Safety-net keyword overrides ─────────────────────────────
# These phrases in the patient query ALWAYS override the LLM's ward classification.
# Order matters: EMERGENCY_KEYWORDS checked first.

EMERGENCY_KEYWORDS: frozenset[str] = frozenset({
    "chest pain",
    "can't breathe",
    "cannot breathe",
    "difficulty breathing",
    "unconscious",
    "stroke",
    "seizure",
    "bleeding heavily",
    "heavy bleeding",
    "heart attack",
    "severe burn",
    "not breathing",
    "stopped breathing",
    "choking",
    "anaphylaxis",
    "allergic reaction",
    "head injury",
    "spinal injury",
    "broken bone",
    "fracture",
})

CRISIS_KEYWORDS: frozenset[str] = frozenset({
    "suicidal",
    "want to die",
    "self-harm",
    "self harm",
    "selfharm",
    "overdose",
    "kill myself",
    "harm myself",
    "end my life",
    "don't want to live",
    "dont want to live",
})

# ── Age parsing ───────────────────────────────────────────────
# Word-to-digit map used by the regex-based age normaliser
WORD_TO_NUM: dict[str, int] = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
    "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
    "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
    "eighteen": 18, "nineteen": 19, "twenty": 20, "thirty": 30,
    "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70,
    "eighty": 80, "ninety": 90, "hundred": 100,
}
