-- ============================================================
-- AI Hospital Triage System — Supabase Schema
-- Run this in the Supabase SQL Editor (Project > SQL Editor > New query)
-- ============================================================

-- Enable uuid generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- Table: doctors
-- ============================================================
CREATE TABLE IF NOT EXISTS public.doctors (
    doctor_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL UNIQUE,
    ward        TEXT NOT NULL CHECK (ward IN ('emergency', 'mental_health', 'general')),
    specialization TEXT NOT NULL DEFAULT 'General Practice',
    status      TEXT NOT NULL DEFAULT 'free' CHECK (status IN ('free', 'busy', 'on_leave')),
    shift_start TIME NOT NULL DEFAULT '09:00',
    shift_end   TIME NOT NULL DEFAULT '17:00',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- Table: appointments
-- ============================================================
CREATE TABLE IF NOT EXISTS public.appointments (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_name        TEXT NOT NULL,
    age                 INTEGER CHECK (age > 0 AND age < 150),
    gender              TEXT,
    query               TEXT NOT NULL,
    ward                TEXT CHECK (ward IN ('emergency', 'mental_health', 'general')),
    reasoning           TEXT,
    assigned_doctor_id  UUID REFERENCES public.doctors(doctor_id) ON DELETE SET NULL,
    priority            TEXT NOT NULL DEFAULT 'normal' CHECK (priority IN ('high', 'normal')),
    status              TEXT NOT NULL DEFAULT 'waiting' CHECK (status IN ('waiting', 'in_progress', 'done')),
    notes               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- Table: status_log  (audit trail)
-- ============================================================
CREATE TABLE IF NOT EXISTS public.status_log (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doctor_id   UUID NOT NULL REFERENCES public.doctors(doctor_id) ON DELETE CASCADE,
    old_status  TEXT NOT NULL,
    new_status  TEXT NOT NULL,
    changed_by  TEXT NOT NULL DEFAULT 'system',   -- 'system' or doctor name
    timestamp   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- Indexes
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_doctors_ward_status
    ON public.doctors (ward, status);

CREATE INDEX IF NOT EXISTS idx_appointments_doctor_status
    ON public.appointments (assigned_doctor_id, status);

CREATE INDEX IF NOT EXISTS idx_appointments_ward_status_priority
    ON public.appointments (ward, status, priority DESC, created_at ASC);

CREATE INDEX IF NOT EXISTS idx_status_log_doctor
    ON public.status_log (doctor_id, timestamp DESC);

-- ============================================================
-- Row Level Security (RLS)
-- Using anon key — allow all operations for now (demo / prototype)
-- Tighten these before any production use.
-- ============================================================
ALTER TABLE public.doctors      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.appointments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.status_log   ENABLE ROW LEVEL SECURITY;

-- Full access for anon role (demo only)
CREATE POLICY "anon_all_doctors"      ON public.doctors      FOR ALL TO anon USING (true) WITH CHECK (true);
CREATE POLICY "anon_all_appointments" ON public.appointments FOR ALL TO anon USING (true) WITH CHECK (true);
CREATE POLICY "anon_all_status_log"   ON public.status_log  FOR ALL TO anon USING (true) WITH CHECK (true);
