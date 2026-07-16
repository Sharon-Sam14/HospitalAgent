# AI Development Rules & Guardrails — MediTriage

To maintain system integrity, concurrency safety, and professional code standards, follow these guidelines when editing the MediTriage codebase.

---

## 1. Allowed and Prohibited Libraries

### Allowed Libraries (Preferred Stack):
*   **Web UI:** Streamlit (`streamlit`).
*   **Database:** Supabase (`supabase` python SDK).
*   **AI Agent Workflows:** LangGraph (`langgraph`) and LangChain (`langchain_groq`, `langchain_core`).
*   **Data Processing:** Pandas (`pandas`).
*   **Environment Management:** `python-dotenv`.

### Prohibited Libraries (Do NOT Add):
*   **UI/CSS Frameworks:** Do **NOT** install Tailwind CSS, Bootstrap, or any Node-based CSS compilation pipelines. Stick purely to Streamlit widgets and vanilla CSS injected via `st.markdown("<style>...</style>", unsafe_allow_html=True)`.
*   **Other DB Drivers:** Do not introduce raw `psycopg2` or `asyncpg` directly unless writing low-level database admin tools. Keep client interactions standardized via the Supabase client wrapper `database/client.py`.
*   **Alternative Agent Frameworks:** Do not introduce AutoGen, CrewAI, or Semantic Kernel. Maintain the workflow structure using LangGraph StateGraph.

---

## 2. Concurrency & Database Security Rules

### Concurrency Guards (Critical):
1.  **Atomic Doctor Booking:** Doctor status transitions MUST be guarded against race conditions. When assigning a doctor, never fetch the doctor's status, check it in Python, and write it back. Instead, perform an atomic update where the status is updated conditionally:
    ```python
    # Correct (atomic check):
    client.table("doctors").update({"status": "busy"}).eq("doctor_id", doc_id).eq("status", "free").execute()
    ```
2.  **No Double-Booking:** If the conditional update above returns an empty list (meaning 0 rows were affected because the doctor was taken by another thread in the last millisecond), the node must fallback to the next candidate doctor or queue the patient.

### Security Guardrails:
*   **Secrets Exposure:** Never commit secrets, passwords, or API keys directly to code repositories. Always query credentials through `config.py`, which securely reads from Streamlit `secrets.toml` or OS environment variables via `.env`.
*   **Row Level Security (RLS):** Keep Supabase RLS enabled on all tables (`doctors`, `appointments`, `status_log`).

---

## 3. Error Handling & System Resilience

### Rule 1: No App Crashes
Streamlit is an active rendering loop. An unhandled exception will crash the user's dashboard view.
*   Always wrap service layers, database operations, and LLM queries in `try-except` blocks.
*   Return standard error states (e.g. dicts containing `{"success": False, "error": "error message"}`) rather than letting exceptions bubble up to UI modules.

### Rule 2: LLM Fallback (Graceful Degradation)
If the Groq API times out, throws a rate limit error, or is down:
*   Catch the error in `agent/nodes.py` (specifically `router_node`).
*   Default the patient's ward routing to the `general` ward.
*   Append a flag: `llm_failed = True` and write `"LLM failure — needs manual review."` into the `reasoning` column.
*   Notify the doctor dashboard UI that manual triage is required for that patient record.

---

## 4. Coding Style and Project Standards

*   **Type Safety:** Maintain type hints for all public functions, database interactions, and LangGraph components. Use `from __future__ import annotations` at the top of new Python files.
*   **Caching Configs:** Compile the state graph exactly once. Use `@lru_cache(maxsize=1)` to load the LangGraph instance.
*   **Directory Isolation:**
    *   Keep SQL declarations in `database/schema.sql`.
    *   Maintain UI elements inside `views/` or `app.py`.
    *   Do not import UI code inside the `agent/` or `services/` logic (prevents circular dependencies).
*   **Audit Logging:** Every time a doctor's status is updated, create an entry in the `status_log` table documenting the timestamp, old status, new status, and the user who triggered the update.
