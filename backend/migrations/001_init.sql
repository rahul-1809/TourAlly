-- ============================================================
-- TourAlly — Application Table Migrations
-- Run this ONCE against your Supabase project via:
--   psql $DATABASE_URL -f 001_init.sql
-- OR paste into Supabase SQL Editor
-- ============================================================

-- Enable UUID generation (already available in Supabase)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ─── travel_sessions ─────────────────────────────────────────
-- Tracks every travel-planning session (1 session = 1 LangGraph thread)
CREATE TABLE IF NOT EXISTS travel_sessions (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id       TEXT        NOT NULL UNIQUE,
    user_query      TEXT        NOT NULL,
    status          TEXT        NOT NULL DEFAULT 'planning',
    -- Allowed status values:
    --   'planning'          → agents are actively running
    --   'awaiting_approval' → HITL interrupt fired, waiting for user
    --   'approved'          → user approved, generating final itinerary
    --   'revised'           → user requested a revision, re-running
    --   'completed'         → final itinerary delivered
    --   'blocked'           → guardrail rejected the query
    destination     TEXT,
    origin          TEXT,
    duration        TEXT,
    budget          TEXT,
    selected_agents TEXT[],         -- e.g. ['flight_agent', 'hotel_agent']
    final_response  TEXT,           -- final itinerary markdown
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_travel_sessions_thread_id
    ON travel_sessions (thread_id);

-- Auto-bump updated_at on every UPDATE
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS travel_sessions_updated_at ON travel_sessions;
CREATE TRIGGER travel_sessions_updated_at
    BEFORE UPDATE ON travel_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ─── agent_run_logs ──────────────────────────────────────────
-- Audit log of every specialist agent execution within a session
CREATE TABLE IF NOT EXISTS agent_run_logs (
    id             UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id      TEXT        NOT NULL
                               REFERENCES travel_sessions(thread_id)
                               ON DELETE CASCADE,
    agent_name     TEXT        NOT NULL,
    -- Agent values: 'supervisor' | 'flight_agent' | 'hotel_agent' |
    --               'weather_agent' | 'budget_agent' | 'itinerary_agent' | 'hitl'
    status         TEXT        NOT NULL DEFAULT 'running',
    -- Status values: 'running' | 'completed' | 'failed' | 'skipped'
    result_summary TEXT,
    error_message  TEXT,
    duration_ms    INTEGER,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_run_logs_thread_id
    ON agent_run_logs (thread_id);
