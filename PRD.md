# Project Requirements Document (PRD) — MediTriage

## 1. Goal & Overview
MediTriage is an AI-driven hospital triage and doctor assignment system. The primary goal is to automate the initial patient intake, classify the severity/ward of the symptoms using a Language Model (LLM) combined with safety-net keyword overrides, and automatically assign the patient to a free doctor in the classified ward. If no doctor is available, the patient is queued.

This system aims to minimize wait times, optimize clinic resources, and ensure critical emergencies are routed and prioritized immediately.

---

## 2. Target Users
*   **Patients:** Submit symptom descriptions and details; receive immediate feedback on priority, assigned doctor, or queue status.
*   **Doctors / Clinical Staff:** Access a dashboard to view their assigned patients, record consultation notes, complete appointments, and manage their status (Free, Busy, On Leave).
*   **Hospital Administrators:** View all active clinics, track appointment queues, and monitor status change logs for audit/operational purposes.

---

## 3. Core Features & Capabilities

### 3.1 Patient Intake & Triage (LangGraph Workflow)
*   **Intake Form:** Capture name, age (accepting natural/free-text format), gender, and query (symptoms description).
*   **Age Normalization:** Parse age from free text (e.g., "thirty-two", "25", "4 years old") using regex maps, falling back to LLM extraction if regex fails.
*   **Ward Classification:** Route the patient to one of three wards:
    *   `emergency` (e.g., severe physical trauma, breathing problems, chest pain)
    *   `mental_health` (e.g., psychiatric distress, anxiety, self-harm crisis)
    *   `general` (e.g., mild fever, routine consultation)
*   **Safety-Net Keyword Override:** Predefined keywords/phrases override the LLM to guarantee immediate routing to emergency (e.g., "chest pain", "difficulty breathing") or mental health (e.g., "suicidal", "overdose").
*   **Priority Classification:** 
    *   Emergency cases are marked **High** priority.
    *   Mental health cases containing crisis keywords are marked **High** priority; others are **Normal**.
    *   General cases are marked **Normal** priority.

### 3.2 Automated & Atomic Doctor Assignment
*   **Doctor Availability Search:** Find a free doctor specializing in the target ward.
*   **Atomic Reservation Guard:** Use conditional updates in the database to prevent two patients from booking the same doctor concurrently (concurrency safeguard).
*   **Queueing System:** If no doctor is free in the target ward, the appointment remains in the `waiting` status, and the patient is assigned a queue position based on priority (FIFO within priority level).

### 3.3 Doctor Dashboard & Actions
*   **Authentication:** Basic password check corresponding to the doctor's name.
*   **My Patients List:** View active (waiting / in-progress) patients assigned to the doctor.
*   **Status Management:** Toggle clinical status (Free, Busy, On Leave). Changing status to "On Leave" or "Busy" handles active/waiting assignments cleanly.
*   **Case Resolution:** Record clinical notes and mark appointments as `done`, which automatically frees up the doctor.
*   **Audit Logging:** Write every status change (who changed it, old status, new status, timestamp) to a database status log.

---

## 4. Technical Requirements
*   **Python:** Backend integration utilizing `Streamlit` for the web interface.
*   **LangGraph:** A structured state-graph machine to handle intake validation, classification routing, priority setting, and database assignment nodes.
*   **Supabase:** PostgreSQL backend containing:
    *   `doctors` table
    *   `appointments` table
    *   `status_log` table
*   **Groq API:** Llama-3-70b class model for fast, low-latency symptom classification.
