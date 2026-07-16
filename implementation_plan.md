# Implementation Plan — Frontend & Backend Integration

This plan outlines the steps to replace the mock memory data in the Streamlit frontend (`app.py` and views) with direct backend calls using the Supabase client and the LangGraph triage service agent.

## User Review Required

> [!IMPORTANT]
> The database integration relies on `st.secrets` (configured in `.streamlit/secrets.toml`). We verified that the Supabase client connects successfully and the seeding script works.

---

## Proposed Changes

### UI & Styling (`app.py`)

#### [MODIFY] [app.py](file:///c:/Users/sharo/Desktop/Hospital%20Agent/app.py)
*   Update `_init()` to fetch doctors and appointments from the database rather than hardcoding `_APPOINTMENTS` and `_DOCTORS`.
*   Replace `_mock_triage()` with a call to `services.triage_service.run_triage(form_data)`.
*   Replace doctor login logic to fetch records from Supabase and verify credentials against `config.DOCTOR_PASSWORDS`.
*   Update doctor dashboard status toggles, metrics, active patient lists, and note-saving utilities to call functions from `doctor_service.py` and `appointment_service.py`.
*   Update the admin view to query/add/remove doctors from the `doctors` table and load system-wide appointments directly from the `appointments` table.

---

### View Routing Stubs (`views/`)

#### [MODIFY] [patient_view.py](file:///c:/Users/sharo/Desktop/Hospital%20Agent/views/patient_view.py)
*   Clean up views stub referencing the old prototype and direct imports.

#### [MODIFY] [doctor_view.py](file:///c:/Users/sharo/Desktop/Hospital%20Agent/views/doctor_view.py)
*   Clean up dashboard stub file to verify structure.

---

## Verification Plan

### Automated Verification
*   Execute `streamlit run app.py` locally and verify the logs for successful Supabase connection.

### Manual Verification
1.  **Patient Flow:** Submit a test patient intake form (e.g. name: "Jane Doe", age: "28", symptoms: "Severe chest pain and shortness of breath"). Verify that the intake routes to the `emergency` ward with a `high` priority and atomically assigns a free emergency doctor.
2.  **Doctor Flow:** Log in as one of the assigned doctors (e.g. "Dr. Khan"). Verify status toggle modifies database status. Modify patient clinical notes and ensure the notes persist to Supabase. Mark the patient as "Seen" and verify the doctor status shifts back to "Free".
3.  **Admin Flow:** Log in as `admin`. View active rosters and verify database logs. Add a new doctor and remove a doctor to ensure full CRUD operates on the remote Postgres tables.
