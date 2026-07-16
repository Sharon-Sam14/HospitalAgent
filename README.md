# 🏥 MediTriage — AI Hospital Triage System

MediTriage is an intelligent, agentic hospital triage and clinical assignment system. It automates patient intake, classifies urgency and assigns a ward via a Language Model (LLM) combined with safety-net keyword overrides, and atomically assigns the patient to an available doctor in the database. If no doctors are free, patients are placed in a priority-sorted queue.

Built with **Streamlit**, **LangGraph**, and **Supabase (PostgreSQL)**, it features concurrency-safe slot bookings and full audit logging for clinical status changes.

---

## 🌟 Core Features
*   **AI-Powered Patient Intake & Triage:** Automatically validates fields and parses complex age formats (e.g., "thirty-two", "25").
*   **Dual-Layer Classification:** Uses Groq Cloud SDK (`llama-3.3-70b-versatile`) to classify query symptoms into designated wards, with a robust local regex safety-net keyword matcher overriding LLM calls for high-risk queries.
*   **Multi-Ward Prioritization:**
    *   `emergency` 🚑 (High Priority)
    *   `mental_health` 🧠 (Normal / High Priority if containing active crisis keywords)
    *   `general` 🏥 (Normal Priority)
*   **Atomic Doctor Reservation:** Uses conditional PostgreSQL updates to lock doctor statuses safely during assignment, eliminating booking collisions and double-booking race conditions.
*   **FIFO Patient Queues:** Intelligently calculates waitlist positions for patients when all ward doctors are busy or on leave.
*   **Doctor Portal:** Allows medical staff to secure-log in, manage clinical status (Free, Busy, On Leave), input patient notes, and mark cases as complete (freeing the doctor up).
*   **Admin Log Panel:** Logs doctor status transitions dynamically for administrative oversight.

---

## 📂 Documentation Quick Links
For deep architectural, requirement, design, or phase roadmaps, see the following files:
*   [PRD.md](file:///c:/Users/sharo/Desktop/Hospital%20Agent/PRD.md) — Product Requirements Document (goals, targets, features, parameters).
*   [Architecture.md](file:///c:/Users/sharo/Desktop/Hospital%20Agent/Architecture.md) — Technical layouts, SQL schema, folder lists, and system topology.
*   [Rules.md](file:///c:/Users/sharo/Desktop/Hospital%20Agent/Rules.md) — Coding guardrails, prohibited libraries, and exception handling guidelines.
*   [Phases.md](file:///c:/Users/sharo/Desktop/Hospital%20Agent/Phases.md) — Project milestones, phases, and pending task lists.
*   [Design.md](file:///c:/Users/sharo/Desktop/Hospital%20Agent/Design.md) — Color palettes, typography specifications, and custom CSS stylings.
*   [Memory.md](file:///c:/Users/sharo/Desktop/Hospital%20Agent/Memory.md) — Dynamic context buffer tracking current repository status and next steps.

---

## 🛠️ Tech Stack & Requirements
*   **Python 3.9+**
*   **Streamlit** (UI rendering)
*   **LangGraph** & **LangChain Core/Groq** (Intake agent flow)
*   **Supabase Client** (Postgres DB interactions)
*   **Python Dotenv** (Local environment secrets)

---

## 🚀 Setup & Installation

### 1. Clone & Set Up Directory
Navigate to the project root directory and install dependencies:
```bash
pip install -r requirements.txt
# If not present in requirements.txt, ensure you install:
pip install supabase langgraph langchain-groq python-dotenv pandas
```

### 2. Configure Environment Secrets
Create a `.env` file in the root directory for database scripts, and configure Streamlit's local secrets directory (`.streamlit/secrets.toml`):

#### Root `.env`:
```env
SUPABASE_URL="your-supabase-url"
SUPABASE_KEY="your-supabase-anon-key"
GROQ_API_KEY="your-groq-api-key"
```

#### `.streamlit/secrets.toml`:
```toml
SUPABASE_URL = "your-supabase-url"
SUPABASE_KEY = "your-supabase-anon-key"
GROQ_API_KEY = "your-groq-api-key"

[DOCTOR_PASSWORDS]
"Dr. Sharma" = "sharma123"
"Dr. Iyer" = "iyer123"
"Dr. Khan" = "khan123"
"Dr. Rao" = "rao123"
"Dr. Mehta" = "mehta123"
"Dr. Gupta" = "gupta123"
```

### 3. Initialize Database Schema
Create the tables in your Supabase SQL editor by running the script in [database/schema.sql](file:///c:/Users/sharo/Desktop/Hospital%20Agent/database/schema.sql).

### 4. Seed Doctor Roster
Execute the seed script to populate the doctor roster from `doctors.csv`:
```bash
python database/seed.py
```

### 5. Launch the Web App
Run the Streamlit application:
```bash
streamlit run app.py
```

---

## 🔒 Security & Concurrency Notes
*   **Database Constraints:** Check clauses on `ward`, `priority`, and `status` in the database prevent invalid listings.
*   **Conditional Guard:** Concurrency updates are handled atomically at the DB level, preventing double-bookings.
*   **Safety Netting:** Patient input is keyword-checked locally before reaching LLM endpoints, securing immediate triage for high-risk critical conditions.
