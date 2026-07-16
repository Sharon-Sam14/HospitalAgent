# Workspace Memory Document — MediTriage

This file serves as a memory buffer and state snapshot of the MediTriage project to keep AI agents aligned and contextually aware without needing to reread the entire repository.

---

## 1. Project Context
*   **System Name:** MediTriage — AI Hospital Triage System
*   **Main Goal:** Streamline patient intake, perform automated LLM classification of symptoms into medical wards (`general`, `emergency`, `mental_health`), prioritize severity, and atomically assign patients to doctors or manage waiting queues using Supabase PostgreSQL.

---

## 2. Current Implementation State

### 2.1 Database Layer (Supabase)
*   **Tables & Indexes:** Configured via `database/schema.sql`. Includes `doctors`, `appointments`, and `status_log` tables. Custom indexes ensure performant sorting of waiting queues and doctor searches. RLS policies are enabled.
*   **Seeding:** Script `database/seed.py` successfully reads `doctors.csv` and uses idempotent upsert queries to populate the roster.

### 2.2 Orchestration Layer (LangGraph)
*   **Graph Design:** Defined in `agent/graph.py` as `intake` → `router` → `ward` → `doctor_assign` → `END`.
*   **Intake Node:** Cleans inputs, verifies fields, and normalizes age inputs (handling word formats like "twenty-two").
*   **Router Node:** Queries Groq API (`llama-3.3-70b-versatile`) with temperature `0.1` for ward routing. Includes a safety override checking symptom strings against predefined keyword lists first (e.g. "chest pain" -> `emergency`).
*   **Ward Node:** Assigns priority level (`high` vs `normal`). High priority is forced for emergencies or mental health cases featuring active crisis keywords.
*   **Doctor Assign Node:** Connects to Supabase, writes the appointment record, searches for free doctors in the assigned ward, and uses an atomic SQL filter (`status = 'free'`) during the update to prevent booking race conditions. Places patients in a queue if no staff are free.

### 2.3 Interface Layer (Streamlit)
*   **Dashboard (`app.py`):** Configured with custom styling to hide Streamlit branding elements, inject Inter typography, set CSS color tokens, and structure responsive column views.
*   **View Stub Routing:** Separated into `views/patient_view.py` and `views/doctor_view.py` to route UI segments to app render actions.
*   **Mock State:** The UI contains mock/mock-up session state structures that need to be fully linked to backend services in `services/`.

---

## 3. Next Steps & Todo List

### Phase 4 Backend Integration:
*   [ ] **Patient Intake Linkage:** Connect `app.py` forms to trigger `services/triage_service.run_triage(form_data)` instead of pushing to session state dicts.
*   [ ] **Doctor Login Integration:** Replace the default admin login credentials in the UI with a credentials lookup using `config.DOCTOR_PASSWORDS` and the `doctors` table in Supabase.
*   [ ] **Doctor Dashboard Linkage:** Wire up the doctor view to fetch the database roster, retrieve active appointments for the logged-in doctor, display clinical history tables, and write consultations notes.
*   [ ] **Status State Synchronization:** Link doctor status toggles directly to database updates and trigger `status_log` updates.

### Testing & Verification:
*   [ ] **Verification Checks:** Run manual queries checking the accuracy of ward routing on borderline symptom descriptions.
*   [ ] **Roster Seeding Test:** Run seeding script and verify upsert counts.
*   [ ] **Concurrency Test:** Perform simultaneous patient triage operations to guarantee that atomic locking prevents double-booking of any doctor.
