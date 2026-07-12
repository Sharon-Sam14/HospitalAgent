"""
app.py — Streamlit entrypoint for the AI Hospital Triage System.

Routing:
  - Sidebar "Patient" tab  → patient_view.render()  (no login required)
  - Sidebar "Doctor" tab   → doctor_view.render()   (login gated in view)
"""
import streamlit as st

st.set_page_config(
    page_title="AI Hospital Triage System",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Import views after set_page_config
from views import patient_view, doctor_view  # noqa: E402

# ── Sidebar navigation ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏥 Hospital Triage")
    st.markdown("---")
    view = st.radio(
        "Select View",
        options=["Patient Intake", "Doctor Dashboard"],
        key="nav_view",
    )
    st.markdown("---")
    st.caption("AI Hospital Triage System · Demo")

# ── Route to the correct view ─────────────────────────────────────────────────
if view == "Patient Intake":
    patient_view.render()
else:
    doctor_view.render()
