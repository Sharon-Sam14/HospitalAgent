"""
MediTriage — AI Hospital Triage System
Real backend integration: Supabase database and LangGraph workflow.
"""
from __future__ import annotations

import time
import uuid
from datetime import datetime

import pandas as pd
import streamlit as st

from services.triage_service import run_triage
from services.doctor_service import get_all_doctors, get_doctor_by_name, update_doctor_status
from services.appointment_service import (
    get_appointments_for_doctor,
    get_done_appointments_for_doctor,
    mark_appointment_done,
    update_appointment_notes,
)
from database.client import get_client
import config

# ══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="MediTriage — AI Hospital Triage",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════
WARD_LABELS = {"emergency": "Emergency", "mental_health": "Mental Health", "general": "General"}
WARD_EMOJIS = {"emergency": "🚑", "mental_health": "🧠", "general": "🏥"}
STATUS_LABELS = {"free": "Free", "busy": "Busy", "on_leave": "On Leave"}
SPEC_MAP = {"general": "General Practice", "emergency": "Emergency Medicine", "mental_health": "Psychiatry"}

_ADMIN_USER = "admin"
_ADMIN_PASS = "admin123"

# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE INITIALISATION
# ══════════════════════════════════════════════════════════════════════════════
def _init() -> None:
    defs: dict = {
        "doctor": None,
        "admin": False,
        "triage_result": None,
    }
    for k, v in defs.items():
        if k not in st.session_state:
            st.session_state[k] = v

# ══════════════════════════════════════════════════════════════════════════════
# CSS INJECTION
# ══════════════════════════════════════════════════════════════════════════════
_THEME = dict(
    bg="#F5F8FA", surface="#FFFFFF", primary="#0F766E", ph="#0B5E57", accent="#1E3A8A",
    text="#0F172A", muted="#475569", border="#E2E8F0", danger="#DC2626", warning="#D97706",
    success="#16A34A", info="#0284C7", sh="#F0F4F8", shadow="0 4px 6px -1px rgba(0,0,0,0.1)"
)

def _inject_css() -> None:
    c = _THEME
    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

:root {{
  --bg:{c['bg']};--surface:{c['surface']};--primary:{c['primary']};--primary-hover:{c['ph']};
  --accent:{c['accent']};--text:{c['text']};--muted:{c['muted']};--border:{c['border']};
  --danger:{c['danger']};--warning:{c['warning']};--success:{c['success']};--info:{c['info']};
  --sh:{c['sh']};--shadow:{c['shadow']};--r:8px;
}}

[data-testid="stHeader"] {{ background: transparent !important; }}
footer {{ visibility: hidden !important; }}
[data-testid="stToolbar"] {{ display:none!important }}
[data-testid="stDecoration"] {{ display:none!important }}

div.block-container {{
  padding-top: 2rem !important;
  padding-bottom: 2rem !important;
  padding-left: 2.5rem !important;
  padding-right: 2.5rem !important;
  max-width: none !important;
}}
.stApp, [data-testid="stAppViewContainer"],
[data-testid="stMainBlockContainer"] {{ background: var(--bg) !important; }}

[data-testid="stSidebar"] {{
  background: var(--surface) !important;
  border-right: 1px solid var(--border) !important;
}}
[data-testid="stSidebar"] * {{ color: var(--text) !important; }}

html, body, [class*="css"] {{
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}}
p, li {{ color: var(--text); line-height: 1.65; }}
h1, h2, h3, h4, h5, h6 {{ color: var(--text) !important; font-weight: 600 !important; }}
label {{ color: var(--text) !important; font-weight: 500 !important; font-size: 0.875rem !important; }}

.stTextInput>div>div>input,
.stTextArea>div>div>textarea,
.stNumberInput>div>div>input {{
  background: var(--surface) !important; color: var(--text) !important;
  border: 1.5px solid var(--border) !important; border-radius: var(--r) !important;
  font-family: inherit !important; font-size: 0.9rem !important;
  transition: border-color .15s ease !important;
}}
.stTextInput>div>div>input:focus,
.stTextArea>div>div>textarea:focus {{
  border-color: var(--primary) !important;
  box-shadow: 0 0 0 3px rgba(15,118,110,.12) !important; outline: none !important;
}}

.stSelectbox * {{
  color: var(--text) !important;
}}
.stSelectbox>div>div {{
  background: var(--surface) !important; border: 1.5px solid var(--border) !important;
  border-radius: var(--r) !important;
}}
div[data-baseweb="popover"] {{
  background-color: var(--surface) !important;
}}
div[data-baseweb="popover"] * {{
  color: var(--text) !important;
}}



.stButton>button,
[data-testid="stFormSubmitButton"]>button {{
  background: var(--primary) !important; color: #fff !important; border: none !important;
  border-radius: var(--r) !important; font-weight: 600 !important; font-size: 0.875rem !important;
  padding: 0.5rem 1.25rem !important; transition: background .15s ease !important;
  box-shadow: none !important;
}}
.stButton>button:hover,
[data-testid="stFormSubmitButton"]>button:hover {{ background: var(--primary-hover) !important; }}

.stButton>button[kind="secondary"] {{
  background: transparent !important; color: var(--text) !important;
  border: 1.5px solid var(--border) !important;
}}
.stButton>button[kind="secondary"]:hover {{ background: var(--sh) !important; }}

[data-testid="stExpander"] {{
  background: var(--surface) !important; border: 1px solid var(--border) !important;
  border-radius: var(--r) !important;
}}
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary p {{ color: var(--text) !important; }}
[data-testid="stExpander"] summary:hover {{ background: var(--sh) !important; }}

[data-testid="stDataFrame"],
[data-testid="stDataEditor"] {{
  border-radius: var(--r) !important;
  border: 1px solid var(--border) !important;
  overflow: hidden !important;
}}

[data-testid="stVerticalBlockBorderWrapper"] {{
  border: 1px solid var(--border) !important; border-radius: var(--r) !important;
  background: var(--surface) !important; box-shadow: var(--shadow) !important;
}}

.card {{
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 8px; padding: 1.25rem;
  box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); margin-bottom: 0.5rem;
  transition: border-color .2s ease, box-shadow .2s ease, transform .15s ease;
}}
.card:hover {{
  border-color: var(--primary);
  box-shadow: 0 8px 16px -2px rgba(0,0,0,0.15);
  transform: translateY(-2px);
}}
.card.hp {{ border-left: 4px solid var(--danger); }}
.card.np {{ border-left: 4px solid var(--info); }}

.card-row {{ display: flex; justify-content: space-between; align-items: flex-start;
             flex-wrap: wrap; gap: 0.3rem; margin-bottom: 0.5rem; }}
.c-name {{ font-size: 1rem; font-weight: 600; color: var(--text) !important; margin: 0.2rem 0 0.1rem; }}
.c-meta {{ font-size: 0.8rem; color: var(--muted) !important; margin: 0 0 0.35rem; }}
.c-sym  {{ font-size: 0.875rem; color: var(--muted) !important; margin: 0; line-height: 1.55;
           display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }}
.c-time {{ font-size: 0.72rem; color: var(--muted) !important; }}

.stat {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px;
         padding: 1rem 1.25rem; text-align: center; box-shadow: var(--shadow); }}
.sv   {{ font-size: 2rem; font-weight: 700; color: var(--primary) !important; margin: 0; line-height: 1; }}
.sl   {{ font-size: 0.7rem; color: var(--muted) !important; margin: 0.3rem 0 0;
         text-transform: uppercase; letter-spacing: 0.5px; }}

.badge {{ display: inline-flex; align-items: center; gap: 3px; padding: 3px 10px;
           border-radius: 999px; font-size: 0.7rem; font-weight: 600; letter-spacing: 0.3px; white-space: nowrap; }}
.bs {{ background: rgba(22,163,74,0.12); color: var(--success); border: 1px solid rgba(22,163,74,0.3); }}
.bw {{ background: rgba(217,119,6,0.12); color: var(--warning); border: 1px solid rgba(217,119,6,0.3); }}
.bd {{ background: rgba(220,38,38,0.12); color: var(--danger); border: 1px solid rgba(220,38,38,0.3); }}
.bi {{ background: rgba(2,132,199,0.12); color: var(--info); border: 1px solid rgba(2,132,199,0.3); }}
.ba {{ background: rgba(30,58,138,0.12); color: var(--accent); border: 1px solid rgba(30,58,138,0.3); }}
.bm {{ background: rgba(71,85,105,0.12); color: var(--muted); border: 1px solid rgba(71,85,105,0.3); }}
.bp {{ background: rgba(15,118,110,0.12); color: var(--primary); border: 1px solid rgba(15,118,110,0.3); }}

.disclaimer {{
  background: rgba(2,132,199,0.07); border: 1px solid rgba(2,132,199,0.3);
  border-left: 4px solid var(--info); border-radius: 8px;
  padding: 0.75rem 1rem; color: var(--info) !important;
  font-size: 0.875rem; font-weight: 500; margin-bottom: 1.25rem;
}}

.c-ok {{ background: rgba(22,163,74,0.05); border: 1px solid rgba(22,163,74,0.25);
         border-radius: 8px; padding: 1.5rem; }}
.c-q  {{ background: rgba(217,119,6,0.05); border: 1px solid rgba(217,119,6,0.25);
         border-radius: 8px; padding: 1.5rem; }}
.c-ok h4, .c-q h4 {{ margin: 0 0 0.5rem; color: var(--text) !important; font-size: 1.05rem; }}
.c-ok p, .c-q p {{ margin: 0.2rem 0; color: var(--text) !important; }}

.es {{ text-align: center; padding: 4rem 1rem; color: var(--muted); }}
.esi {{ font-size: 3.5rem; margin-bottom: 0.75rem; display: block; }}
.es p {{ color: var(--muted) !important; font-size: 1rem; }}

@media (max-width: 768px) {{
  div.block-container {{
    padding-left: 1rem !important;
    padding-right: 1rem !important;
    padding-top: 1.25rem !important;
  }}
  .card {{ padding: 0.875rem !important; }}
  h1, h2, h3, h4 {{ font-size: 1.2rem !important; }}
  .sv {{ font-size: 1.5rem !important; }}
  .disclaimer {{ font-size: 0.8rem !important; }}
}}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# HELPER UTILITIES
# ══════════════════════════════════════════════════════════════════════════════
def _b(label: str, cls: str) -> str:
    return f'<span class="badge {cls}">{label}</span>'

def _wb(ward: str) -> str:
    cm = {"emergency": "bd", "mental_health": "ba", "general": "bi"}
    return _b(f"{WARD_EMOJIS.get(ward,'')} {WARD_LABELS.get(ward,ward)}", cm.get(ward,"bi"))

def _pb(priority: str) -> str:
    return _b("⚠ High Priority", "bd") if priority == "high" else _b("Normal", "bm")

def _sb(status: str) -> str:
    cm = {"free": "bs", "busy": "bw", "on_leave": "bm"}
    return _b(f"● {STATUS_LABELS.get(status,status)}", cm.get(status,"bm"))

def _wait(t: datetime | str) -> str:
    if isinstance(t, str):
        t = t.replace("Z", "+00:00")
        try:
            t = datetime.fromisoformat(t)
        except ValueError:
            return "unknown"
    if t.tzinfo is not None:
        from datetime import timezone
        diff = datetime.now(timezone.utc) - t
    else:
        diff = datetime.now() - t
    m = max(0, int(diff.total_seconds() / 60))
    return f"{m}m ago" if m < 60 else f"{m//60}h {m%60}m ago"

# ══════════════════════════════════════════════════════════════════════════════
# SHARED HEADER
# ══════════════════════════════════════════════════════════════════════════════
def _header() -> None:
    st.markdown('<h2 style="margin:0; color:var(--primary);">🏥 MediTriage</h2>', unsafe_allow_html=True)
    st.markdown('<div style="height: 2px; background-color: var(--primary); margin: 0.5rem 0 1.5rem 0;"></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# VIEW 1 — PATIENT INTAKE
# ══════════════════════════════════════════════════════════════════════════════
def patient_view() -> None:
    _header()

    st.markdown(
        '<div class="disclaimer">ℹ️ <strong>Demo / prototype only</strong> — do not enter real patient data.</div>',
        unsafe_allow_html=True,
    )

    if st.session_state.triage_result:
        _show_confirmation(st.session_state.triage_result)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("← Submit another patient", key="another", type="secondary"):
            st.session_state.triage_result = None
            st.rerun()
        return

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container(border=True):
            st.markdown("### Patient Intake")
            st.markdown(
                '<p style="color:var(--muted); font-size:0.9rem; margin-top:-0.3rem;">'
                "Provide your information and symptoms for clinical triage.</p>",
                unsafe_allow_html=True,
            )
            st.divider()

            with st.form("intake_form"):
                name = st.text_input("Full Name ✱", placeholder="e.g. Arjun Mehta")
                raw_age = st.text_input("Age ✱", placeholder='"32" or "thirty two"')
                gender = st.radio("Gender", ["Female", "Male", "Other", "Prefer not to say"], horizontal=True)
                query = st.text_area("Symptoms ✱", height=120, placeholder="Describe symptoms (e.g. chest pain for 2 hours)...")
                submitted = st.form_submit_button("Submit for Triage →", use_container_width=True)

    if submitted:
        if not name.strip() or not raw_age.strip() or not query.strip():
            st.error("Please fill in all required fields: Name, Age, and Symptoms.")
        else:
            with st.spinner("Routing to the right ward..."):
                form_data = {
                    "patient_name": name.strip(),
                    "raw_age": raw_age.strip(),
                    "gender": gender,
                    "query": query.strip(),
                }
                result = run_triage(form_data)
            
            if result.get("success"):
                st.session_state.triage_result = result
                st.toast("Patient submitted successfully!")
                st.rerun()
            else:
                st.error(f"Triage failed: {result.get('error', 'Unknown error')}")

def _show_confirmation(result: dict) -> None:
    ward, priority = result["ward"], result["priority"]
    doc, qpos = result.get("assigned_doctor"), result.get("queue_position")
    wb, pb = _wb(ward), _pb(priority)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if doc:
            st.markdown(f"""
<div class="c-ok">
  <h4>✅ Triage Result: Assigned</h4>
  <div style="margin-bottom:.65rem">{wb} &nbsp; {pb}</div>
  <p>Assigned to <strong>{doc}</strong> in the <strong>{WARD_LABELS.get(ward, ward)}</strong> ward.</p>
  <p style="font-size:.85rem;color:var(--muted)!important">Please proceed to receptionist in ward {WARD_EMOJIS.get(ward,'')} {WARD_LABELS.get(ward, ward)}.</p>
</div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
<div class="c-q">
  <h4>⏳ Triage Result: Waitlisted</h4>
  <div style="margin-bottom:.65rem">{wb} &nbsp; {pb}</div>
  <p>No doctor is currently free in <strong>{WARD_LABELS.get(ward, ward)}</strong>. Status: <strong>Waitlisted</strong> (Queue Position #{qpos}).</p>
  <p style="font-size:.85rem;color:var(--muted)!important">Please take a seat in the waiting hall.</p>
</div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# VIEW 2 — DOCTOR DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
def doctor_view() -> None:
    _header()

    if not st.session_state.doctor:
        _doctor_login()
        return

    doc = st.session_state.doctor

    # Welcome Header
    h1, h2 = st.columns([5, 1])
    with h1:
        st.markdown(
            f'<h3 style="margin:0">Welcome, {doc["name"]} — {WARD_LABELS.get(doc["ward"], doc["ward"])}</h3>',
            unsafe_allow_html=True,
        )
    with h2:
        if st.button("Sign Out", key="dr_so", type="secondary", use_container_width=True):
            st.session_state.doctor = None
            st.toast("Signed out.")
            st.rerun()

    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
    opts = ["Free", "Busy", "On Leave"]
    fwd = {"Free": "free", "Busy": "busy", "On Leave": "on_leave"}
    rev = {v: k for k, v in fwd.items()}
    cur = rev.get(doc["status"], "Free")

    sc1, sc2 = st.columns([2, 4])
    with sc1:
        nl = st.radio("Status Toggle", opts, index=opts.index(cur), horizontal=True, key="dr_status_r", label_visibility="collapsed")
        ns = fwd[nl]
        if ns != doc["status"]:
            if update_doctor_status(doc["doctor_id"], ns, changed_by=doc["name"]):
                doc["status"] = ns
                st.session_state.doctor = doc
                st.toast(f"Status updated → {nl}")
                st.rerun()
    with sc2:
        st.markdown(f'<div style="padding-top: 0.15rem;">{_sb(doc["status"])}</div>', unsafe_allow_html=True)

    st.divider()

    # Load active appointments and history live
    active_appointments = get_appointments_for_doctor(doc["doctor_id"])
    done_appointments = get_done_appointments_for_doctor(doc["doctor_id"])

    queue_n = len(active_appointments)
    high_n = sum(1 for a in active_appointments if a["priority"] == "high")
    done_n = len(done_appointments)

    s1, s2, s3 = st.columns(3)
    with s1:
        st.markdown(f'<div class="stat"><p class="sv">{queue_n}</p><p class="sl">In Queue</p></div>', unsafe_allow_html=True)
    with s2:
        st.markdown(f'<div class="stat"><p class="sv" style="color:var(--danger)!important">{high_n}</p><p class="sl">High Priority</p></div>', unsafe_allow_html=True)
    with s3:
        st.markdown(f'<div class="stat"><p class="sv" style="color:var(--success)!important">{done_n}</p><p class="sl">Completed Today</p></div>', unsafe_allow_html=True)

    st.divider()

    st.markdown("### 📋 My Queue")
    if not active_appointments:
        st.markdown(
            '<div class="es"><span class="esi">🩺</span><p>No patients in your queue.</p></div>',
            unsafe_allow_html=True,
        )
    else:
        for i in range(0, len(active_appointments), 2):
            row = active_appointments[i:i + 2]
            gcols = st.columns(2)
            for j, appt in enumerate(row):
                with gcols[j]:
                    _patient_card(appt, doc)

def _patient_card(appt: dict, doc: dict) -> None:
    hp = appt["priority"] == "high"
    cls = "card hp" if hp else "card np"
    wb = _wb(appt["ward"])
    pb = _pb(appt["priority"])
    wt = _wait(appt["created_at"])

    st.markdown(f"""
<div class="{cls}">
  <div class="card-row">
    <div>{pb} &nbsp; {wb}</div>
    <span class="c-time">⏱ {wt}</span>
  </div>
  <p class="c-name">{appt['patient_name']}</p>
  <p class="c-meta">{appt['age']} yrs &nbsp;·&nbsp; {appt['gender']}</p>
  <p class="c-sym">{appt['query']}</p>
</div>
""", unsafe_allow_html=True)

    with st.expander("Notes"):
        nk = f"n_{appt['id']}"
        if nk not in st.session_state:
            st.session_state[nk] = appt.get("notes") or ""
        notes = st.text_area("Clinical Notes", value=st.session_state[nk], height=75,
                             key=f"ta_{appt['id']}", label_visibility="collapsed")
        if notes != st.session_state[nk]:
            if update_appointment_notes(appt["id"], notes):
                st.session_state[nk] = notes
                appt["notes"] = notes
                st.toast("Notes saved.")

    if st.button("✅ Mark Seen", key=f"ms_{appt['id']}", use_container_width=True):
        if mark_appointment_done(appt["id"], doc["doctor_id"], doc["name"]):
            new_doc = get_doctor_by_name(doc["name"])
            if new_doc:
                new_doc["id"] = new_doc["doctor_id"]
                st.session_state.doctor = new_doc
            st.toast(f"✅ {appt['patient_name']} marked as seen.")
            st.rerun()
    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

def _doctor_login() -> None:
    _, col, _ = st.columns([1, 2, 1])
    with col:
        with st.container(border=True):
            st.markdown("#### 🔐 Doctor Login")
            st.markdown(
                '<p style="color:var(--muted);font-size:.85rem;margin-top:-.3rem">'
                "Select your name and enter password to continue.</p>",
                unsafe_allow_html=True,
            )
            st.divider()
            
            doctors = get_all_doctors()
            names = [d["name"] for d in doctors]
            if not names:
                st.warning("No doctors registered in database.")
                return
                
            sel = st.selectbox("Your name", names, key="dl_name")
            pwd = st.text_input("Password", type="password", key="dl_pwd", placeholder="Password")
            if st.button("Sign In →", use_container_width=True, key="dl_btn"):
                if pwd.strip():
                    expected = config.DOCTOR_PASSWORDS.get(sel)
                    if expected and pwd.strip() == expected:
                        doctor = get_doctor_by_name(sel)
                        if doctor:
                            doctor["id"] = doctor["doctor_id"]
                            st.session_state.doctor = doctor
                            st.toast(f"Welcome, {doctor['name']}!")
                            st.rerun()
                        else:
                            st.error("Profile lookup failed.")
                    else:
                        st.error("Invalid password.")
                else:
                    st.error("Please enter password.")

# ══════════════════════════════════════════════════════════════════════════════
# VIEW 3 — ADMIN — MANAGE DOCTORS
# ══════════════════════════════════════════════════════════════════════════════
def admin_view() -> None:
    _header()

    if not st.session_state.admin:
        _admin_login()
        return

    ah1, ah2 = st.columns([6, 1])
    with ah1:
        st.markdown("### ⚙️ Manage Doctors")
    with ah2:
        if st.button("Sign Out", key="adm_so", type="secondary", use_container_width=True):
            st.session_state.admin = False
            st.toast("Admin signed out.")
            st.rerun()

    db_doctors = get_all_doctors()

    with st.expander("➕ Add Doctor"):
        with st.form("add_doc_form"):
            fc1, fc2, fc3 = st.columns(3)
            with fc1:
                new_name = st.text_input("Full name", placeholder="Dr. Jane Smith")
                new_ward = st.selectbox("Ward", ["emergency", "mental_health", "general"], format_func=lambda x: WARD_LABELS[x])
            with fc2:
                new_spec = st.text_input("Specialization", placeholder="e.g. Cardiology")
                new_shift = st.text_input("Shift Hours", value="09:00 - 17:00")
            with fc3:
                st.markdown("<br>", unsafe_allow_html=True)
                add_btn = st.form_submit_button("Add Doctor", use_container_width=True)

        if add_btn:
            if not new_name.strip():
                st.error("Doctor name is required.")
            elif any(d["name"].lower() == new_name.strip().lower() for d in db_doctors):
                st.warning(f"'{new_name}' already exists in registry.")
            else:
                start, end = "09:00", "17:00"
                if "-" in new_shift:
                    parts = [p.strip() for p in new_shift.split("-")]
                    if len(parts) == 2:
                        start, end = parts[0], parts[1]

                client = get_client()
                try:
                    client.table("doctors").insert({
                        "name": new_name.strip(),
                        "ward": new_ward,
                        "specialization": new_spec.strip() or SPEC_MAP.get(new_ward, "General Practice"),
                        "shift_start": start,
                        "shift_end": end,
                        "status": "free",
                    }).execute()
                    st.toast(f"✅ {new_name.strip()} added successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to add doctor: {e}")

    st.markdown("#### 👨‍⚕️ Doctor Database")
    df = pd.DataFrame([{
        "ID": d["doctor_id"],
        "Name": d["name"],
        "Ward": d["ward"],
        "Specialization": d["specialization"],
        "Shift": f"{d['shift_start']} - {d['shift_end']}",
        "Status": d["status"],
    } for d in db_doctors])

    edited = st.data_editor(
        df,
        use_container_width=True,
        hide_index=True,
        key="doc_editor",
        column_config={
            "ID": st.column_config.TextColumn("ID", disabled=True),
            "Ward": st.column_config.SelectboxColumn("Ward", options=["emergency", "mental_health", "general"], required=True),
            "Status": st.column_config.SelectboxColumn("Status", options=["free", "busy", "on_leave"], required=True),
        },
    )

    if edited is not None:
        for i, row in edited.iterrows():
            d = db_doctors[i]
            changed = {}
            if row["Name"] != d["name"]:
                changed["name"] = row["Name"]
            if row["Ward"] != d["ward"]:
                changed["ward"] = row["Ward"]
            if row["Specialization"] != d["specialization"]:
                changed["specialization"] = row["Specialization"]
            if row["Status"] != d["status"]:
                changed["status"] = row["Status"]
            
            shift_str = str(row["Shift"]).strip()
            start, end = d["shift_start"], d["shift_end"]
            if "-" in shift_str:
                parts = [p.strip() for p in shift_str.split("-")]
                if len(parts) == 2:
                    start, end = parts[0], parts[1]
            if start != d["shift_start"] or end != d["shift_end"]:
                changed["shift_start"] = start
                changed["shift_end"] = end
                
            if changed:
                try:
                    get_client().table("doctors").update(changed).eq("doctor_id", d["doctor_id"]).execute()
                    if "status" in changed:
                        get_client().table("status_log").insert({
                            "doctor_id": d["doctor_id"],
                            "old_status": d["status"],
                            "new_status": changed["status"],
                            "changed_by": "admin",
                        }).execute()
                    st.toast(f"Updated {d['name']}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to update doctor {d['name']}: {e}")

    with st.expander("🗑 Remove Doctor"):
        rm_names = [d["name"] for d in db_doctors]
        rm_sel = st.selectbox("Select doctor", rm_names, key="rm_sel")
        if st.button("Remove Doctor", key="rm_btn", type="secondary"):
            try:
                get_client().table("doctors").delete().eq("name", rm_sel).execute()
                st.toast(f"{rm_sel} removed.")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to remove doctor: {e}")

    st.divider()
    st.markdown("#### 📊 System Appointments log")
    try:
        res = get_client().table("appointments").select("*").order("created_at", desc=True).execute()
        appts = res.data or []
    except Exception as e:
        appts = []
        st.error(f"Failed to fetch appointments: {e}")

    if not appts:
        st.info("No appointments yet.")
    else:
        def _dname(did: str) -> str:
            if not did:
                return "Unassigned"
            match = next((d["name"] for d in db_doctors if d["doctor_id"] == did), None)
            return match or "Unassigned"

        adf = pd.DataFrame([{
            "Patient": a["patient_name"],
            "Age": a.get("age") or "–",
            "Ward": WARD_LABELS.get(a["ward"], a["ward"]),
            "Priority": a["priority"].title(),
            "Status": a["status"].replace("_", " ").title(),
            "Doctor": _dname(a.get("assigned_doctor_id", "")),
            "Queued": _wait(a["created_at"]),
        } for a in appts])

        st.dataframe(adf, use_container_width=True, hide_index=True)

def _admin_login() -> None:
    _, col, _ = st.columns([1, 2, 1])
    with col:
        with st.container(border=True):
            st.markdown("#### 🔑 Admin Access")
            st.divider()
            user = st.text_input("Username", key="al_user")
            pwd = st.text_input("Password", type="password", key="al_pwd")
            if st.button("Sign In →", use_container_width=True, key="al_btn"):
                if user.strip() == _ADMIN_USER and pwd.strip() == _ADMIN_PASS:
                    st.session_state.admin = True
                    st.toast("✅ Admin Session Active")
                    st.rerun()
                else:
                    st.error("Invalid credentials.")

# ══════════════════════════════════════════════════════════════════════════════
# MAIN ROUTING
# ══════════════════════════════════════════════════════════════════════════════
def main() -> None:
    _init()
    _inject_css()

    with st.sidebar:
        st.markdown('<p class="wm">Medi<span class="lt">Triage</span></p>', unsafe_allow_html=True)
        view = st.radio(
            "Navigation",
            ["🏥 Patient Intake", "🩺 Doctor Dashboard", "⚙️ Admin — Manage Doctors"],
            label_visibility="collapsed",
            key="nav_v",
        )
        st.markdown("---")

        if st.session_state.doctor:
            d = st.session_state.doctor
            st.markdown(f'{_sb(d["status"])}<p style="margin:.35rem 0 0;font-size:.8rem;color:var(--muted)">{d["name"]}</p>', unsafe_allow_html=True)
        else:
            st.markdown('<p style="font-size:.8rem;color:var(--muted)">🩺 Doctor: not logged in</p>', unsafe_allow_html=True)

        if st.session_state.admin:
            st.markdown(_b("● Admin", "bp") + '<p style="margin:.35rem 0 0;font-size:.8rem;color:var(--muted)">Admin session active</p>', unsafe_allow_html=True)
        else:
            st.markdown('<p style="font-size:.8rem;color:var(--muted)">⚙️ Admin: not logged in</p>', unsafe_allow_html=True)

        # Fetch status stats dynamically from Supabase
        try:
            res = get_client().table("appointments").select("status").execute()
            status_data = res.data or []
            wn = sum(1 for a in status_data if a["status"] == "waiting")
            an = sum(1 for a in status_data if a["status"] == "in_progress")
            dn = sum(1 for a in status_data if a["status"] == "done")
        except Exception:
            wn, an, dn = 0, 0, 0

        st.markdown(
            f'<div style="margin-top:.75rem">'
            f'<p style="font-size:.72rem;color:var(--muted);margin:.15rem 0">⏳ Waiting: <strong style="color:var(--warning)">{wn}</strong></p>'
            f'<p style="font-size:.72rem;color:var(--muted);margin:.15rem 0">🔵 Active: <strong style="color:var(--info)">{an}</strong></p>'
            f'<p style="font-size:.72rem;color:var(--muted);margin:.15rem 0">✅ Done: <strong style="color:var(--success)">{dn}</strong></p>'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<p style="font-size:.68rem;color:var(--muted);margin-top:2rem">MediTriage · Demo v0.2.1<br><em>Not for real patient data.</em></p>',
            unsafe_allow_html=True,
        )

    if view == "🏥 Patient Intake":
        patient_view()
    elif view == "🩺 Doctor Dashboard":
        doctor_view()
    else:
        admin_view()

if __name__ == "__main__":
    main()
