"""
MediTriage — AI Hospital Triage System
Frontend prototype: all data mocked in st.session_state.
Wire to the real backend by replacing _mock_triage() with triage_service.run_triage()
and replacing session_state doctor/appointment reads with service calls.
"""
from __future__ import annotations

import time
import uuid
from datetime import datetime, timedelta

import streamlit as st

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="MediTriage — AI Hospital Triage",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
# MOCK SEED DATA
# ══════════════════════════════════════════════════════════════════════════════

_DOCTORS_SEED: list[dict] = [
    {"id": "d1", "name": "Dr. Sharma",  "ward": "general",      "specialization": "General Practice",    "shift_start": "09:00", "shift_end": "17:00", "status": "free"},
    {"id": "d2", "name": "Dr. Iyer",    "ward": "general",      "specialization": "Internal Medicine",   "shift_start": "09:15", "shift_end": "17:15", "status": "busy"},
    {"id": "d3", "name": "Dr. Khan",    "ward": "emergency",    "specialization": "Emergency Medicine",  "shift_start": "08:30", "shift_end": "16:30", "status": "free"},
    {"id": "d4", "name": "Dr. Rao",     "ward": "emergency",    "specialization": "Emergency Medicine",  "shift_start": "08:30", "shift_end": "16:30", "status": "on_leave"},
    {"id": "d5", "name": "Dr. Mehta",   "ward": "mental_health","specialization": "Psychiatry",          "shift_start": "10:00", "shift_end": "18:00", "status": "free"},
    {"id": "d6", "name": "Dr. Gupta",   "ward": "mental_health","specialization": "Clinical Psychology", "shift_start": "10:00", "shift_end": "18:00", "status": "busy"},
]

_APPTS_SEED: list[dict] = [
    {"id": "a1", "patient_name": "Arjun Mehta", "age": 34, "gender": "Male",
     "query": "Severe chest pain radiating to left arm, sweating profusely",
     "ward": "emergency", "priority": "high", "status": "in_progress",
     "assigned_doctor_id": "d3", "notes": "",
     "created_at": datetime.now() - timedelta(minutes=15)},
    {"id": "a2", "patient_name": "Priya Nair", "age": 27, "gender": "Female",
     "query": "Severe anxiety and panic attacks, feeling very overwhelmed",
     "ward": "mental_health", "priority": "normal", "status": "waiting",
     "assigned_doctor_id": "d5", "notes": "",
     "created_at": datetime.now() - timedelta(minutes=8)},
    {"id": "a3", "patient_name": "Ravi Kumar", "age": 52, "gender": "Male",
     "query": "Persistent cough for 2 weeks, mild fever and fatigue",
     "ward": "general", "priority": "normal", "status": "waiting",
     "assigned_doctor_id": "d1", "notes": "",
     "created_at": datetime.now() - timedelta(minutes=3)},
]

# ══════════════════════════════════════════════════════════════════════════════
# DOMAIN CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════

EMERGENCY_KEYWORDS = {
    "chest pain", "can't breathe", "cannot breathe", "difficulty breathing",
    "unconscious", "stroke", "seizure", "bleeding heavily", "heavy bleeding",
    "heart attack", "severe burn", "not breathing", "stopped breathing",
    "choking", "anaphylaxis", "broken bone", "fracture", "hemorrhage",
}
CRISIS_KEYWORDS = {
    "suicidal", "want to die", "self-harm", "self harm", "overdose",
    "kill myself", "harm myself", "end my life", "don't want to live",
    "dont want to live",
}
MENTAL_KEYWORDS = {
    "anxiety", "panic", "depression", "depressed", "hallucination",
    "bipolar", "ptsd", "trauma", "psychosis", "psychiatric", "schizophrenia",
}

WARD_LABELS  = {"emergency": "Emergency",  "mental_health": "Mental Health", "general": "General"}
WARD_EMOJIS  = {"emergency": "🚑",         "mental_health": "🧠",            "general": "🏥"}
WARD_COLORS  = {"emergency": "danger",     "mental_health": "accent",        "general": "info"}
STATUS_LABELS = {"free": "Free",           "busy": "Busy",                   "on_leave": "On Leave"}
STATUS_COLORS = {"free": "success",        "busy": "warning",                "on_leave": "muted"}
SPEC_MAP     = {"general": "General Practice", "emergency": "Emergency Medicine", "mental_health": "Psychiatry"}
WORD_NUM     = {
    "zero":0,"one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"seven":7,
    "eight":8,"nine":9,"ten":10,"eleven":11,"twelve":12,"thirteen":13,
    "fourteen":14,"fifteen":15,"sixteen":16,"seventeen":17,"eighteen":18,
    "nineteen":19,"twenty":20,"thirty":30,"forty":40,"fifty":50,
    "sixty":60,"seventy":70,"eighty":80,"ninety":90,
}

# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════

# Admin credentials (mock — replace with st.secrets in production)
_ADMIN_USERNAME = "admin"
_ADMIN_PASSWORD = "admin123"  # any value accepted in real demo; change here to set a real one


def _init_state() -> None:
    defaults: dict = {
        "theme":         "light",
        "doctor":        None,
        "admin":         False,   # True once admin logs in
        "triage_result": None,
        "doctors":       [dict(d) for d in _DOCTORS_SEED],
        "appointments":  [dict(a) for a in _APPTS_SEED],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# ══════════════════════════════════════════════════════════════════════════════
# CSS INJECTION  (single <style> block, rebuilt on every rerun)
# ══════════════════════════════════════════════════════════════════════════════

_LIGHT = dict(
    bg="#F5F8FA", surface="#FFFFFF", primary="#0F766E", ph="#0B5E57",
    accent="#1E3A8A", text="#0F172A", muted="#475569", border="#E2E8F0",
    success="#16A34A", warning="#D97706", danger="#DC2626", info="#0284C7",
    sh="#F0F4F8", shadow="0 1px 3px rgba(0,0,0,0.08),0 1px 2px rgba(0,0,0,0.04)",
)
_DARK = dict(
    bg="#0B1220", surface="#111827", primary="#2DD4BF", ph="#5EEAD4",
    accent="#60A5FA", text="#E5E7EB", muted="#94A3B8", border="#1F2937",
    success="#22C55E", warning="#F59E0B", danger="#F87171", info="#38BDF8",
    sh="#1C2333", shadow="0 2px 8px rgba(0,0,0,0.4)",
)


def _inject_css(theme: str) -> None:
    c = _DARK if theme == "dark" else _LIGHT
    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── CSS Variables ── */
:root {{
  --bg:{c['bg']};--surface:{c['surface']};--primary:{c['primary']};--ph:{c['ph']};
  --accent:{c['accent']};--text:{c['text']};--muted:{c['muted']};--border:{c['border']};
  --success:{c['success']};--warning:{c['warning']};--danger:{c['danger']};--info:{c['info']};
  --sh:{c['sh']};--shadow:{c['shadow']};--r:10px;
}}

/* ── Global ── */
html,body,[class*="css"]{{font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif!important}}
.stApp,.main,.block-container{{background-color:var(--bg)!important}}
p,li{{color:var(--text);line-height:1.65}}
h1,h2,h3,h4,h5,h6{{color:var(--text)!important;font-weight:600}}
label{{color:var(--text)!important;font-weight:500!important;font-size:.875rem!important}}
small{{color:var(--muted)!important}}

/* ── Sidebar ── */
[data-testid="stSidebar"]{{background-color:var(--surface)!important;border-right:1px solid var(--border)!important}}
[data-testid="stSidebar"] *{{color:var(--text)!important}}
[data-testid="stSidebarContent"]{{padding-top:1.5rem}}

/* ── Top bar ── */
[data-testid="stHeader"]{{background-color:var(--bg)!important;border-bottom:none!important}}
[data-testid="stDecoration"]{{display:none!important}}

/* ── Main content padding ── */
.block-container{{padding-top:1.5rem!important;padding-bottom:3rem!important}}

/* ── Inputs ── */
.stTextInput>div>div>input,
.stTextArea>div>div>textarea,
.stNumberInput>div>div>input{{
  background-color:var(--surface)!important;color:var(--text)!important;
  border:1.5px solid var(--border)!important;border-radius:8px!important;
  font-size:.9rem!important;transition:border-color 0.15s ease!important;
  padding:.45rem .75rem!important}}
.stTextInput>div>div>input:focus,
.stTextArea>div>div>textarea:focus{{
  border-color:var(--primary)!important;
  box-shadow:0 0 0 3px rgba(15,118,110,0.12)!important;outline:none!important}}
.stTextInput>label,.stTextArea>label{{margin-bottom:.3rem!important}}

/* ── Selectbox ── */
.stSelectbox>div>div{{
  background-color:var(--surface)!important;border:1.5px solid var(--border)!important;
  border-radius:8px!important;color:var(--text)!important}}
[data-testid="stSelectboxVirtualDropdown"]{{
  background-color:var(--surface)!important;border:1px solid var(--border)!important;
  border-radius:8px!important}}

/* ── Primary button (teal) ── */
.stButton>button,
[data-testid="stFormSubmitButton"]>button{{
  background-color:var(--primary)!important;color:#fff!important;
  border:none!important;border-radius:8px!important;
  font-weight:600!important;font-size:.875rem!important;
  padding:.5rem 1.25rem!important;
  transition:background-color 0.15s ease!important;box-shadow:none!important;
  letter-spacing:.01em}}
.stButton>button:hover,
[data-testid="stFormSubmitButton"]>button:hover{{background-color:var(--ph)!important}}
.stButton>button:focus-visible{{outline:2px solid var(--primary)!important;outline-offset:2px!important}}

/* ── Secondary button (ghost) ── */
.stButton>button[kind="secondary"]{{
  background-color:transparent!important;color:var(--text)!important;
  border:1.5px solid var(--border)!important}}
.stButton>button[kind="secondary"]:hover{{background-color:var(--sh)!important}}

/* ── Radio ── */
.stRadio>div>label>div p{{color:var(--text)!important}}
.stRadio [data-testid="stMarkdownContainer"] p{{color:var(--text)!important}}

/* ── Expander ── */
[data-testid="stExpander"]{{
  background-color:var(--surface)!important;border:1px solid var(--border)!important;
  border-radius:var(--r)!important}}
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary p{{color:var(--text)!important}}
[data-testid="stExpander"] summary:hover{{background-color:var(--sh)!important}}

/* ── Container with border ── */
[data-testid="stVerticalBlockBorderWrapper"]{{
  border:1px solid var(--border)!important;border-radius:var(--r)!important;
  background-color:var(--surface)!important;
  box-shadow:var(--shadow)!important;padding:.1rem .75rem!important}}

/* ── Dataframe ── */
[data-testid="stDataFrame"]{{
  border-radius:var(--r)!important;border:1px solid var(--border)!important;overflow:hidden!important}}
[data-testid="stDataFrame"] th{{
  background-color:var(--sh)!important;color:var(--muted)!important;
  font-size:.75rem!important;text-transform:uppercase!important;letter-spacing:.5px!important}}

/* ── Toggle ── */
[data-testid="stToggle"] span{{color:var(--muted)!important;font-size:.8rem!important}}
[data-testid="stToggle"]>label{{justify-content:flex-end!important}}

/* ── Status spinner ── */
[data-testid="stStatus"]{{
  background-color:var(--surface)!important;border:1px solid var(--border)!important;
  border-radius:var(--r)!important;color:var(--text)!important}}

/* ── Toast ── */
[data-testid="stToast"]{{
  background-color:var(--surface)!important;border:1px solid var(--border)!important;
  color:var(--text)!important;border-radius:var(--r)!important;
  box-shadow:var(--shadow)!important}}

/* ── Alert boxes ── */
[data-testid="stAlert"]{{border-radius:var(--r)!important}}

/* ── Divider ── */
hr{{border-color:var(--border)!important;margin:.75rem 0!important}}

/* ── Scrollbar ── */
::-webkit-scrollbar{{width:5px;height:5px}}
::-webkit-scrollbar-thumb{{background:var(--border);border-radius:3px}}
::-webkit-scrollbar-track{{background:var(--bg)}}

/* ═══════════════ CUSTOM HTML COMPONENTS ═══════════════════ */

/* Wordmark */
.mt-wm{{font-size:1.45rem;font-weight:700;color:var(--primary)!important;
  letter-spacing:-.5px;margin:0;line-height:1.3;user-select:none}}
.mt-wm .lt{{color:var(--text)!important;font-weight:300}}

/* Teal gradient divider */
.mt-div{{height:2px;background:linear-gradient(90deg,var(--primary) 0%,transparent 100%);
  border:none;margin:.25rem 0 1.1rem;border-radius:1px}}

/* Badges / pills */
.badge{{
  display:inline-flex;align-items:center;gap:3px;
  padding:3px 10px;border-radius:999px;
  font-size:.7rem;font-weight:600;letter-spacing:.3px;
  white-space:nowrap;line-height:1.5}}
.bs{{background:rgba(22,163,74,.12);color:var(--success);border:1px solid rgba(22,163,74,.3)}}
.bw{{background:rgba(217,119,6,.12);color:var(--warning);border:1px solid rgba(217,119,6,.3)}}
.bd{{background:rgba(220,38,38,.12);color:var(--danger);border:1px solid rgba(220,38,38,.3)}}
.bi{{background:rgba(2,132,199,.12);color:var(--info);border:1px solid rgba(2,132,199,.3)}}
.ba{{background:rgba(30,58,138,.12);color:var(--accent);border:1px solid rgba(30,58,138,.3)}}
.bm{{background:rgba(71,85,105,.12);color:var(--muted);border:1px solid rgba(71,85,105,.3)}}
.bp{{background:rgba(15,118,110,.12);color:var(--primary);border:1px solid rgba(15,118,110,.3)}}

/* Disclaimer banner */
.disclaimer{{
  background:rgba(2,132,199,.07);border:1px solid rgba(2,132,199,.3);
  border-left:4px solid var(--info);border-radius:8px;
  padding:.7rem 1rem;color:var(--info)!important;
  font-size:.875rem;font-weight:500;margin-bottom:1.25rem}}

/* Confirmation cards */
.c-ok{{background:rgba(22,163,74,.05);border:1px solid rgba(22,163,74,.25);
  border-radius:var(--r);padding:1.4rem 1.5rem;margin:.5rem 0}}
.c-q {{background:rgba(217,119,6,.05);border:1px solid rgba(217,119,6,.25);
  border-radius:var(--r);padding:1.4rem 1.5rem;margin:.5rem 0}}
.c-ok h4,.c-q h4{{margin:0 0 .5rem;color:var(--text)!important;font-size:1.05rem}}
.c-ok p,.c-q p{{margin:.2rem 0;color:var(--text)!important}}

/* Patient queue card */
.pcard{{
  background:var(--surface);border:1px solid var(--border);
  border-left:4px solid var(--border);border-radius:var(--r);
  padding:.9rem 1.15rem .7rem;box-shadow:var(--shadow);margin-bottom:.1rem}}
.pcard.hp{{border-left-color:var(--danger)}}
.pcard.np{{border-left-color:var(--info)}}
.pc-row{{display:flex;justify-content:space-between;align-items:flex-start;
  flex-wrap:wrap;gap:.35rem;margin-bottom:.45rem}}
.pc-name{{font-size:1rem;font-weight:600;color:var(--text)!important;margin:.1rem 0 .15rem}}
.pc-meta{{font-weight:400;color:var(--muted)!important;font-size:.85rem}}
.pc-sym{{font-size:.875rem;color:var(--muted)!important;margin:0;line-height:1.55}}
.pc-time{{font-size:.72rem;color:var(--muted)!important;padding-top:2px}}

/* Empty state */
.es{{text-align:center;padding:3.5rem 1rem;color:var(--muted)!important}}
.es .esi{{font-size:3rem;margin-bottom:.5rem;display:block}}
.es p{{color:var(--muted)!important;font-size:.95rem}}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def _b(label: str, cls: str) -> str:
    return f'<span class="badge {cls}">{label}</span>'

def _ward_badge(ward: str) -> str:
    cm = {"emergency": "bd", "mental_health": "ba", "general": "bi"}
    return _b(f"{WARD_EMOJIS.get(ward,'')} {WARD_LABELS.get(ward,ward)}", cm.get(ward,"bi"))

def _priority_badge(priority: str) -> str:
    return _b("⚠ High Priority", "bd") if priority == "high" else _b("Normal", "bm")

def _status_badge(status: str) -> str:
    cm = {"free": "bs", "busy": "bw", "on_leave": "bm"}
    return _b(f"● {STATUS_LABELS.get(status, status)}", cm.get(status, "bm"))

def _wait(created_at: datetime) -> str:
    m = max(0, int((datetime.now() - created_at).total_seconds() / 60))
    return f"{m}m ago" if m < 60 else f"{m//60}h {m%60}m ago"

def _parse_age(raw: str) -> int:
    raw = raw.strip()
    try:
        v = int(raw)
        return v if 0 < v < 150 else 0
    except ValueError:
        tokens = raw.lower().replace("-", " ").split()
        total = sum(WORD_NUM.get(t, 0) for t in tokens)
        return total if 0 < total < 150 else 0

def _mock_triage(name: str, raw_age: str, gender: str, query: str) -> dict:
    """Keyword-based mock triage — replace with triage_service.run_triage() for real backend."""
    q = query.lower()
    ward, priority, reason = "general", "normal", "General symptoms — routed to general ward."

    for kw in EMERGENCY_KEYWORDS:
        if kw in q:
            ward, priority, reason = "emergency", "high", f"Emergency keyword detected: '{kw}'."
            break
    else:
        for kw in CRISIS_KEYWORDS:
            if kw in q:
                ward, priority, reason = "mental_health", "high", f"Crisis keyword detected: '{kw}'."
                break
        else:
            for kw in MENTAL_KEYWORDS:
                if kw in q:
                    ward, priority, reason = "mental_health", "normal", f"Mental health keyword: '{kw}'."
                    break

    age = _parse_age(raw_age)

    # Mock atomic doctor assignment
    free = [d for d in st.session_state.doctors if d["ward"] == ward and d["status"] == "free"]
    doctor = None
    if free:
        doctor = free[0]
        for d in st.session_state.doctors:
            if d["id"] == doctor["id"]:
                d["status"] = "busy"

    waiting = [a for a in st.session_state.appointments if a["ward"] == ward and a["status"] == "waiting"]
    qpos = len(waiting) + 1 if not doctor else None

    appt_id = uuid.uuid4().hex[:8]
    st.session_state.appointments.append({
        "id": appt_id, "patient_name": name, "age": age, "gender": gender,
        "query": query, "ward": ward, "priority": priority,
        "status": "in_progress" if doctor else "waiting",
        "assigned_doctor_id": doctor["id"] if doctor else None,
        "notes": "", "created_at": datetime.now(), "reasoning": reason,
    })

    return {
        "ward": ward, "priority": priority, "reasoning": reason,
        "assigned_doctor": doctor["name"] if doctor else None,
        "queue_position": qpos,
    }

# ══════════════════════════════════════════════════════════════════════════════
# SHARED HEADER (wordmark + theme toggle + divider)
# ══════════════════════════════════════════════════════════════════════════════

def _render_header() -> None:
    c1, _, c2 = st.columns([5, 2, 2])
    with c1:
        st.markdown('<p class="mt-wm">Medi<span class="lt">Triage</span> 🏥</p>',
                    unsafe_allow_html=True)
    with c2:
        is_dark = st.session_state.theme == "dark"
        toggled = st.toggle(
            "☀️ Light" if is_dark else "🌙 Dark",
            value=is_dark,
            key="theme_toggle",
        )
        st.session_state.theme = "dark" if toggled else "light"
    st.markdown('<div class="mt-div"></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# VIEW 1 — PATIENT INTAKE
# ══════════════════════════════════════════════════════════════════════════════

def render_patient_view() -> None:
    _render_header()

    st.markdown(
        '<div class="disclaimer">ℹ️ <strong>Demo / prototype only</strong> '
        '— do not enter real patient data.</div>',
        unsafe_allow_html=True,
    )

    # ── If we have a result, show confirmation ────────────────────────────────
    if st.session_state.triage_result:
        _render_confirmation(st.session_state.triage_result)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("← Submit another patient", key="another", type="secondary"):
            st.session_state.triage_result = None
            st.rerun()
        return

    # ── Intake form (centered) ────────────────────────────────────────────────
    _, col, _ = st.columns([1, 2.2, 1])
    with col:
        with st.container(border=True):
            st.markdown("#### 🩺 Patient Intake")
            st.markdown(
                '<p style="color:var(--muted);margin-top:-.35rem;font-size:.875rem">'
                "Describe your symptoms — we'll route you to the right ward.</p>",
                unsafe_allow_html=True,
            )
            st.divider()

            with st.form("intake_form"):
                name    = st.text_input("Full Name ✱", placeholder="e.g. Arjun Mehta")
                raw_age = st.text_input("Age ✱", placeholder='e.g. "32" or "thirty two"')
                gender  = st.radio("Gender", ["Female", "Male", "Other", "Prefer not to say"],
                                   horizontal=True)
                query   = st.text_area("Symptoms ✱", height=110,
                                       placeholder="e.g. chest pain for 2 hours, shortness of breath…")
                submitted = st.form_submit_button("Submit for Triage →", use_container_width=True)

    # ── Process after form submit ─────────────────────────────────────────────
    if submitted:
        if not name.strip() or not raw_age.strip() or not query.strip():
            st.error("Please fill in all required fields: Name, Age, and Symptoms.")
            return

        with st.status("Routing to the right ward…", expanded=True) as s:
            st.write("🔍 Analysing symptoms…")
            time.sleep(0.45)
            st.write("👨‍⚕️ Checking doctor availability…")
            time.sleep(0.35)
            st.write("📋 Assigning ward…")
            time.sleep(0.25)
            s.update(label="✅ Triage complete", state="complete", expanded=False)

        result = _mock_triage(name.strip(), raw_age.strip(), gender, query.strip())
        st.session_state.triage_result = result
        st.toast("Patient submitted successfully!")
        st.rerun()


def _render_confirmation(result: dict) -> None:
    ward     = result["ward"]
    priority = result["priority"]
    doctor   = result.get("assigned_doctor")
    qpos     = result.get("queue_position")

    wb = _ward_badge(ward)
    pb = _priority_badge(priority)

    if doctor:
        st.markdown(f"""
<div class="c-ok">
  <h4>✅ You're all set!</h4>
  <div style="margin-bottom:.65rem">{wb} &nbsp; {pb}</div>
  <p>Assigned to <strong>{doctor}</strong> in the
     <strong>{WARD_LABELS[ward]}</strong> ward.</p>
  <p style="font-size:.85rem;color:var(--muted)!important">
     Please proceed to the {WARD_EMOJIS[ward]} {WARD_LABELS[ward]} reception.</p>
</div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
<div class="c-q">
  <h4>⏳ Added to Queue</h4>
  <div style="margin-bottom:.65rem">{wb} &nbsp; {pb}</div>
  <p>No doctor is currently free in <strong>{WARD_LABELS[ward]}</strong>.
     You are <strong>#{qpos}</strong> in the queue.</p>
  <p style="font-size:.85rem;color:var(--muted)!important">
     Please take a seat — a doctor will be available shortly.</p>
</div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# VIEW 2 — DOCTOR DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

def render_doctor_view() -> None:
    _render_header()

    if not st.session_state.doctor:
        _render_login()
        return

    doc = st.session_state.doctor

    # ── Doctor info header ────────────────────────────────────────────────────
    c1, c2 = st.columns([5, 1])
    with c1:
        st.markdown(
            f'<h3 style="margin:0 0 .15rem">Welcome, {doc["name"]}</h3>'
            f'<p style="color:var(--muted);font-size:.875rem;margin:0">'
            f'{WARD_LABELS.get(doc["ward"],doc["ward"])} Ward &nbsp;·&nbsp; '
            f'Shift {doc["shift_start"]}–{doc["shift_end"]}</p>',
            unsafe_allow_html=True,
        )
        st.markdown(_status_badge(doc["status"]), unsafe_allow_html=True)
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Sign Out", key="signout", type="secondary"):
            st.session_state.doctor = None
            st.toast("Signed out.")
            st.rerun()

    st.divider()

    # ── Status override ────────────────────────────────────────────────────────
    with st.expander("🔄 Update My Availability"):
        opts = ["Free", "Busy", "On Leave"]
        fwd  = {"Free": "free", "Busy": "busy", "On Leave": "on_leave"}
        rev  = {v: k for k, v in fwd.items()}
        cur  = rev.get(doc["status"], "Free")
        new_lbl = st.radio("Set status", opts, index=opts.index(cur),
                           horizontal=True, key="dr_status_radio")
        new_status = fwd[new_lbl]
        if new_status != doc["status"]:
            doc["status"] = new_status
            for d in st.session_state.doctors:
                if d["id"] == doc["id"]:
                    d["status"] = new_status
            st.session_state.doctor = doc
            st.toast(f"Status updated → {new_lbl}")
            st.rerun()

    # ── Patient queue ─────────────────────────────────────────────────────────
    st.markdown("### 📋 My Queue")

    my_appts = sorted(
        [a for a in st.session_state.appointments
         if a.get("assigned_doctor_id") == doc["id"]
         and a["status"] in ("waiting", "in_progress")],
        key=lambda a: (0 if a["priority"] == "high" else 1, a["created_at"]),
    )

    if not my_appts:
        st.markdown(
            '<div class="es"><span class="esi">🩺</span>'
            '<p>No patients in your queue.</p></div>',
            unsafe_allow_html=True,
        )
    else:
        for appt in my_appts:
            _render_patient_card(appt, doc)

    # ── Completed today ────────────────────────────────────────────────────────
    done = sorted(
        [a for a in st.session_state.appointments
         if a.get("assigned_doctor_id") == doc["id"] and a["status"] == "done"],
        key=lambda a: a["created_at"], reverse=True,
    )
    if done:
        st.divider()
        st.markdown(f"### ✅ Completed Today &nbsp; ({len(done)})")
        for a in done:
            st.markdown(
                f'<p style="color:var(--muted);font-size:.875rem;margin:.2rem 0">'
                f'✓ &nbsp;<strong>{a["patient_name"]}</strong> · '
                f'{WARD_LABELS.get(a["ward"],a["ward"])} ward</p>',
                unsafe_allow_html=True,
            )


def _render_patient_card(appt: dict, doc: dict) -> None:
    hp  = appt["priority"] == "high"
    cls = "pcard hp" if hp else "pcard np"
    wb  = _ward_badge(appt["ward"])
    pb  = _priority_badge(appt["priority"])
    wt  = _wait(appt["created_at"])

    # ── Display card (pure HTML — no interactive widgets inside) ──────────────
    st.markdown(f"""
<div class="{cls}">
  <div class="pc-row">
    <div>{pb} &nbsp; {wb}</div>
    <span class="pc-time">⏱ {wt}</span>
  </div>
  <p class="pc-name">{appt['patient_name']}
    <span class="pc-meta"> · {appt['age']} yrs · {appt['gender']}</span>
  </p>
  <p class="pc-sym">{appt['query']}</p>
</div>
""", unsafe_allow_html=True)

    # ── Interactive actions (native Streamlit) ────────────────────────────────
    with st.expander("📝 Notes & Actions", expanded=hp):
        nk = f"note_{appt['id']}"
        if nk not in st.session_state:
            st.session_state[nk] = appt.get("notes", "")

        notes = st.text_area(
            "Clinical notes",
            value=st.session_state[nk],
            height=80,
            key=f"ta_{appt['id']}",
            label_visibility="collapsed",
            placeholder="Add clinical notes here…",
        )

        bc1, bc2 = st.columns([1, 2])
        with bc1:
            if st.button("💾 Save Note", key=f"save_{appt['id']}", type="secondary"):
                appt["notes"] = notes
                st.session_state[nk] = notes
                st.toast("Note saved.")
        with bc2:
            if st.button("✅ Mark Seen", key=f"seen_{appt['id']}"):
                appt["status"] = "done"
                # Free up doctor
                for d in st.session_state.doctors:
                    if d["id"] == doc["id"]:
                        d["status"] = "free"
                        doc["status"] = "free"
                st.session_state.doctor = doc
                st.toast(f"✅ {appt['patient_name']} marked as seen. You are now free.")
                st.rerun()

    st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)


def _render_login() -> None:
    _, col, _ = st.columns([1, 2, 1])
    with col:
        with st.container(border=True):
            st.markdown("#### 🔐 Doctor Login")
            st.markdown(
                '<p style="color:var(--muted);font-size:.85rem;margin-top:-.3rem">'
                "Select your name and enter any password to continue.</p>",
                unsafe_allow_html=True,
            )
            st.divider()

            names    = [d["name"] for d in st.session_state.doctors]
            selected = st.selectbox("Your name", names, key="login_name_sel")
            pwd      = st.text_input("Password", type="password",
                                     key="login_pwd",
                                     placeholder="Any password (demo mode)")

            if st.button("Sign In →", use_container_width=True, key="login_btn"):
                if pwd.strip():
                    doctor = next(
                        (dict(d) for d in st.session_state.doctors
                         if d["name"] == selected), None
                    )
                    if doctor:
                        st.session_state.doctor = doctor
                        st.toast(f"Welcome back, {doctor['name']}!")
                        st.rerun()
                else:
                    st.error("Please enter a password.")

            st.markdown(
                '<p style="color:var(--muted);font-size:.75rem;text-align:center;margin-top:.5rem">'
                "Any password accepted in demo mode.</p>",
                unsafe_allow_html=True,
            )

# ══════════════════════════════════════════════════════════════════════════════
# VIEW 3 — ADMIN — MANAGE DOCTORS
# ══════════════════════════════════════════════════════════════════════════════

def _render_admin_login() -> None:
    """Admin login gate — mirrors the doctor login pattern."""
    _, col, _ = st.columns([1, 2, 1])
    with col:
        with st.container(border=True):
            st.markdown("#### 🔑 Admin Login")
            st.markdown(
                '<p style="color:var(--muted);font-size:.85rem;margin-top:-.3rem">'
                "This area contains patient data. Please authenticate to continue.</p>",
                unsafe_allow_html=True,
            )
            st.divider()

            username = st.text_input("Username", key="admin_user",
                                     placeholder="Enter admin username")
            password = st.text_input("Password", type="password",
                                     key="admin_pwd",
                                     placeholder="Enter admin password")

            if st.button("Sign In →", use_container_width=True, key="admin_login_btn"):
                if username.strip() == _ADMIN_USERNAME and password.strip() == _ADMIN_PASSWORD:
                    st.session_state.admin = True
                    st.toast("✅ Welcome, Admin!")
                    st.rerun()
                elif not username.strip() or not password.strip():
                    st.error("Please enter both username and password.")
                else:
                    st.error("Invalid credentials. Please try again.")

            st.markdown(
                f'<p style="color:var(--muted);font-size:.75rem;text-align:center;margin-top:.5rem">'
                f'Demo credentials — username: <code>{_ADMIN_USERNAME}</code> '
                f'/ password: <code>{_ADMIN_PASSWORD}</code></p>',
                unsafe_allow_html=True,
            )


def render_admin_view() -> None:
    _render_header()

    # ── Auth gate ─────────────────────────────────────────────────────────────
    if not st.session_state.admin:
        _render_admin_login()
        return

    # ── Admin header ──────────────────────────────────────────────────────────
    c1, c2 = st.columns([5, 1])
    with c1:
        st.markdown("### ⚙️ Manage Doctors")
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Sign Out", key="admin_signout", type="secondary"):
            st.session_state.admin = False
            st.toast("Admin signed out.")
            st.rerun()

    import pandas as pd

    # ── Doctor table ──────────────────────────────────────────────────────────
    df = pd.DataFrame([{
        "Name":           d["name"],
        "Ward":           WARD_LABELS.get(d["ward"], d["ward"]),
        "Specialization": d["specialization"],
        "Shift":          f"{d['shift_start']} – {d['shift_end']}",
        "Status":         STATUS_LABELS.get(d["status"], d["status"]),
    } for d in st.session_state.doctors])

    st.dataframe(df, use_container_width=True, hide_index=True)

    st.divider()

    # ── Add doctor ────────────────────────────────────────────────────────────
    with st.expander("➕ Add a New Doctor"):
        with st.form("add_doctor_form"):
            ac1, ac2 = st.columns(2)
            with ac1:
                new_name = st.text_input("Full name", placeholder="Dr. Example")
                new_ward = st.selectbox("Ward", ["emergency", "mental_health", "general"],
                                        format_func=lambda x: WARD_LABELS[x])
                new_spec = st.text_input("Specialization",
                                         placeholder="e.g. Cardiology (leave blank for default)")
            with ac2:
                new_ss = st.text_input("Shift Start (HH:MM)", value="09:00")
                new_se = st.text_input("Shift End   (HH:MM)", value="17:00")

            add_btn = st.form_submit_button("➕ Add Doctor", use_container_width=True)

        if add_btn:
            if not new_name.strip():
                st.error("Doctor name is required.")
            elif any(d["name"].lower() == new_name.strip().lower()
                     for d in st.session_state.doctors):
                st.warning(f"'{new_name}' already exists in the list.")
            else:
                st.session_state.doctors.append({
                    "id":             f"d{uuid.uuid4().hex[:6]}",
                    "name":           new_name.strip(),
                    "ward":           new_ward,
                    "specialization": new_spec.strip() or SPEC_MAP.get(new_ward, "General Practice"),
                    "shift_start":    new_ss,
                    "shift_end":      new_se,
                    "status":         "free",
                })
                st.toast(f"✅ {new_name.strip()} added successfully!")
                st.rerun()

    # ── Remove doctor ─────────────────────────────────────────────────────────
    with st.expander("🗑 Remove a Doctor"):
        rm_names = [d["name"] for d in st.session_state.doctors]
        rm_sel   = st.selectbox("Select doctor to remove", rm_names, key="rm_sel")
        if st.button("Remove", key="rm_btn", type="secondary"):
            st.session_state.doctors = [d for d in st.session_state.doctors
                                        if d["name"] != rm_sel]
            st.toast(f"{rm_sel} removed from the roster.")
            st.rerun()

    # ── Appointments overview ─────────────────────────────────────────────────
    st.divider()
    st.markdown("### 📊 Appointments Overview")

    appts = st.session_state.appointments
    if not appts:
        st.info("No appointments yet — submit one from the Patient Intake page.")
    else:
        def _doc_name(did):
            return next((d["name"] for d in st.session_state.doctors
                         if d["id"] == did), "Unassigned")

        adf = pd.DataFrame([{
            "Patient":  a["patient_name"],
            "Age":      a.get("age") or "–",
            "Ward":     WARD_LABELS.get(a["ward"], a["ward"]),
            "Priority": a["priority"].title(),
            "Status":   a["status"].replace("_", " ").title(),
            "Doctor":   _doc_name(a.get("assigned_doctor_id")),
            "Queued":   _wait(a["created_at"]),
        } for a in sorted(appts, key=lambda x: x["created_at"], reverse=True)])

        st.dataframe(adf, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# MAIN — ROUTING
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    _init_state()
    _inject_css(st.session_state.theme)

    # ── Sidebar navigation ────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown(
            '<p class="mt-wm" style="margin-bottom:1.25rem">'
            'Medi<span class="lt">Triage</span></p>',
            unsafe_allow_html=True,
        )

        view = st.radio(
            "Navigation",
            ["🏥 Patient Intake", "🩺 Doctor Dashboard", "⚙️ Admin — Manage Doctors"],
            label_visibility="collapsed",
            key="nav_view",
        )

        st.markdown("---")

        # Session status — Doctor
        if st.session_state.doctor:
            d = st.session_state.doctor
            st.markdown(
                f'{_status_badge(d["status"])}'
                f'<p style="margin:.35rem 0 0;font-size:.8rem;color:var(--muted)">'
                f'{d["name"]}</p>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<p style="font-size:.8rem;color:var(--muted)">🩺 Doctor: not logged in</p>',
                unsafe_allow_html=True,
            )

        # Session status — Admin
        if st.session_state.admin:
            st.markdown(
                _b("● Admin", "bp") +
                '<p style="margin:.35rem 0 0;font-size:.8rem;color:var(--muted)">'
                'Admin session active</p>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<p style="font-size:.8rem;color:var(--muted)">⚙️ Admin: not logged in</p>',
                unsafe_allow_html=True,
            )

        # Appointment quick stats
        appts = st.session_state.appointments
        waiting_n  = sum(1 for a in appts if a["status"] == "waiting")
        active_n   = sum(1 for a in appts if a["status"] == "in_progress")
        done_n     = sum(1 for a in appts if a["status"] == "done")

        st.markdown(
            f'<div style="margin-top:.75rem">'
            f'<p style="font-size:.72rem;color:var(--muted);margin:.15rem 0">'
            f'⏳ Waiting: <strong style="color:var(--warning)">{waiting_n}</strong></p>'
            f'<p style="font-size:.72rem;color:var(--muted);margin:.15rem 0">'
            f'🔵 Active: <strong style="color:var(--info)">{active_n}</strong></p>'
            f'<p style="font-size:.72rem;color:var(--muted);margin:.15rem 0">'
            f'✅ Done: <strong style="color:var(--success)">{done_n}</strong></p>'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<p style="font-size:.68rem;color:var(--muted);margin-top:2rem">'
            'MediTriage · Demo v0.1<br>'
            '<em>Not for real patient data.</em></p>',
            unsafe_allow_html=True,
        )

    # ── Route ─────────────────────────────────────────────────────────────────
    if view == "🏥 Patient Intake":
        render_patient_view()
    elif view == "🩺 Doctor Dashboard":
        render_doctor_view()
    else:
        render_admin_view()


if __name__ == "__main__":
    main()
