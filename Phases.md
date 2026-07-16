# Project Phased Roadmap — MediTriage

Building a robust, AI-powered system requires systematic steps. Below is the breakdown of development phases for MediTriage.

---

## Phase 1: Database Schema & Seeding (Status: Done)
*   [x] Set up Supabase PostgreSQL project.
*   [x] Design and execute SQL schema (`database/schema.sql`) creating `doctors`, `appointments`, and `status_log` tables.
*   [x] Establish constraints, default UUID triggers, check clauses, and appropriate indexes.
*   [x] Set up Row Level Security (RLS) policies for anonymous API connections.
*   [x] Create a roster CSV (`doctors.csv`) outlining doctor shifts and initial states.
*   [x] Write an idempotent seeding script (`database/seed.py`) to parse CSV files and upsert doctor listings.

---

## Phase 2: LangGraph Orchestration (Status: Done)
*   [x] Formulate StateGraph schema in `agent/state.py` containing patient metadata and assignment results.
*   [x] Implement the `intake_node` to validate input criteria and normalize free-text age values using Regex and LLM fallbacks.
*   [x] Program the `router_node` to classify patient symptoms using Groq API LLM and establish hardcoded safety-net keyword overrides.
*   [x] Program the `ward_node` to specify patient priority (High vs. Normal) based on ward categorization.
*   [x] Program the `doctor_assign_node` to search available doctors, implement concurrency-safe booking logic, and calculate FIFO queue rankings.
*   [x] Compile and cache the compiled LangGraph workflow.

---

## Phase 3: Streamlit Interface & Visual Layout (Status: Done)
*   [x] Design a modern web dashboard in `app.py`.
*   [x] Write custom CSS stylings mimicking premium medical software (Inter font, responsive layout, glassmorphic inputs, hidden Streamlit headers).
*   [x] Design side-panel navigation routing users between the **Patient Intake Form**, **Doctor Dashboard**, and **Admin Audit Panel**.
*   [x] Build forms, login pop-ups, tables, and metric blocks using mock/state lists.

---

## Phase 4: Backend Integration & Wiring (Status: In Progress)
*   [ ] Replace session-state mock lists with direct database queries.
*   [ ] Connect the Patient View intake submission to call `services/triage_service.run_triage`.
*   [ ] Connect the Doctor login panel to fetch doctor credentials and passwords from `st.secrets` database.
*   [ ] Bind the Doctor Dashboard to display active appointments assigned to the logged-in doctor via `appointment_service.py`.
*   [ ] Implement doctor actions (record clinic notes, toggle status, resolve and close cases) to directly interact with Supabase tables.

---

## Phase 5: Verification & Stress Testing (Status: Planned)
*   [ ] Test edge cases (e.g., age values like "newborn", "unknown", negative or extreme numbers).
*   [ ] Verify the safety-net keywords override LLM classification successfully.
*   [ ] Conduct race-condition simulation: trigger concurrent patient bookings to check database lock safety and verify that no doctor gets double-booked.
*   [ ] Verify that doctor status updates successfully insert rows into the audit `status_log`.

---

## Phase 6: Production Deployment (Status: Planned)
*   [ ] Deploy the Streamlit codebase onto Streamlit Cloud.
*   [ ] Set environment configurations (`SUPABASE_URL`, `SUPABASE_KEY`, `GROQ_API_KEY`, `DOCTOR_PASSWORDS`) in Streamlit Cloud Settings.
*   [ ] Tighten RLS policies in Supabase, replacing full-access anon policies with restricted roles.
