# TourAlly — Database Schema

> **Database**: Supabase (PostgreSQL)
> **Connection**: `DATABASE_URL` environment variable (Supabase direct connection URI)
> **ORM / Driver**: `psycopg` (v3, binary) via LangGraph's `PostgresSaver`

---

## Overview

TourAlly uses Supabase as a managed PostgreSQL backend for two purposes:

| Purpose | Tables | Who manages them |
|---|---|---|
| **LangGraph HITL Checkpointing** | `checkpoints`, `checkpoint_writes`, `checkpoint_migrations` | LangGraph `PostgresSaver.setup()` — auto-created on first run |
| **App-Level Session Tracking** | `travel_sessions`, `agent_run_logs` | Application — created via migration script |

---

## 1. LangGraph Checkpoint Tables

These are created automatically by calling `PostgresSaver.setup()` on startup. **Do not create or modify these manually.**

### `checkpoints`

Stores the full serialised LangGraph graph state at each node execution step.

| Column | Type | Description |
|---|---|---|
| `thread_id` | `TEXT` | Unique conversation/trip thread identifier (UUID) |
| `checkpoint_ns` | `TEXT` | Namespace within the thread (default `""`) |
| `checkpoint_id` | `TEXT` | UUID for this specific checkpoint |
| `parent_checkpoint_id` | `TEXT` | Previous checkpoint UUID (forms a chain) |
| `type` | `TEXT` | Serialisation format (`msgpack`) |
| `checkpoint` | `BYTEA` | Serialised graph state blob |
| `metadata` | `BYTEA` | Serialised metadata (node name, step index, etc.) |

**Primary Key**: `(thread_id, checkpoint_ns, checkpoint_id)`

---

### `checkpoint_writes`

Stores pending writes that haven't been committed to a full checkpoint yet (used for mid-node state recovery).

| Column | Type | Description |
|---|---|---|
| `thread_id` | `TEXT` | Thread identifier |
| `checkpoint_ns` | `TEXT` | Namespace |
| `checkpoint_id` | `TEXT` | Parent checkpoint UUID |
| `task_id` | `TEXT` | Internal LangGraph task ID |
| `idx` | `INTEGER` | Write ordering index |
| `channel` | `TEXT` | State channel name (e.g. `messages`, `itinerary`) |
| `type` | `TEXT` | Serialisation format |
| `blob` | `BYTEA` | Serialised channel value |

**Primary Key**: `(thread_id, checkpoint_ns, checkpoint_id, task_id, idx)`

---

### `checkpoint_migrations`

Single-row table tracking which LangGraph schema migration has been applied.

| Column | Type | Description |
|---|---|---|
| `v` | `INTEGER` | Migration version number |

---

## 2. Application Tables

### `travel_sessions`

Tracks high-level information about each travel planning session (thread).

```sql
CREATE TABLE IF NOT EXISTS travel_sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id       TEXT NOT NULL UNIQUE,
    user_query      TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'planning',
    -- Status values:
    --   'planning'          - agents are running
    --   'awaiting_approval' - HITL interrupt fired, waiting for human
    --   'approved'          - user approved, generating final plan
    --   'revised'           - user requested revision, re-running
    --   'completed'         - final itinerary delivered
    --   'blocked'           - guardrail rejected the query
    destination     TEXT,
    origin          TEXT,
    duration        TEXT,
    budget          TEXT,
    selected_agents TEXT[],
    final_response  TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_travel_sessions_thread_id
    ON travel_sessions (thread_id);

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER travel_sessions_updated_at
    BEFORE UPDATE ON travel_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

---

### `agent_run_logs`

Audit table — logs each specialist agent's execution per session.

```sql
CREATE TABLE IF NOT EXISTS agent_run_logs (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id      TEXT NOT NULL REFERENCES travel_sessions(thread_id) ON DELETE CASCADE,
    agent_name     TEXT NOT NULL,
    -- 'supervisor' | 'flight_agent' | 'hotel_agent' | 'weather_agent'
    -- | 'budget_agent' | 'itinerary_agent' | 'hitl'
    status         TEXT NOT NULL DEFAULT 'running',
    -- 'running' | 'completed' | 'failed' | 'skipped'
    result_summary TEXT,
    error_message  TEXT,
    duration_ms    INTEGER,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_run_logs_thread_id
    ON agent_run_logs (thread_id);
```

---

## 3. Entity Relationship Diagram

```mermaid
erDiagram
    travel_sessions {
        UUID id PK
        TEXT thread_id UK
        TEXT user_query
        TEXT status
        TEXT destination
        TEXT origin
        TEXT duration
        TEXT budget
        TEXT[] selected_agents
        TEXT final_response
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    agent_run_logs {
        UUID id PK
        TEXT thread_id FK
        TEXT agent_name
        TEXT status
        TEXT result_summary
        TEXT error_message
        INTEGER duration_ms
        TIMESTAMPTZ created_at
    }

    checkpoints {
        TEXT thread_id PK
        TEXT checkpoint_ns PK
        TEXT checkpoint_id PK
        TEXT parent_checkpoint_id
        TEXT type
        BYTEA checkpoint
        BYTEA metadata
    }

    checkpoint_writes {
        TEXT thread_id PK
        TEXT checkpoint_ns PK
        TEXT checkpoint_id PK
        TEXT task_id PK
        INTEGER idx PK
        TEXT channel
        TEXT type
        BYTEA blob
    }

    travel_sessions ||--o{ agent_run_logs : "has many"
    travel_sessions ||--o{ checkpoints : "keyed by thread_id"
    checkpoints ||--o{ checkpoint_writes : "has writes"
```

---

## 4. State Flow via `thread_id`

```mermaid
stateDiagram-v2
    [*] --> planning : POST /api/travel (new thread)
    planning --> awaiting_approval : HITL interrupt() fires
    planning --> blocked : Guardrail rejects query
    awaiting_approval --> completed : User approves
    awaiting_approval --> revised : User requests revision
    revised --> awaiting_approval : itinerary_agent re-runs
    completed --> [*]
    blocked --> [*]
```

---

## 5. Supabase Setup Instructions

### Step 1 — Get your connection string

1. Go to [supabase.com](https://supabase.com) → Your Project
2. Navigate to **Settings → Database**
3. Under **Connection string**, select the **URI** tab
4. Copy the full URI: `postgresql://postgres:[password]@db.[ref].supabase.co:5432/postgres`

### Step 2 — Set environment variable

```bash
# backend/.env
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-REF].supabase.co:5432/postgres
```

### Step 3 — Auto-migration on startup

`PostgresSaver.setup()` is called on FastAPI startup and creates all LangGraph checkpoint tables automatically. App tables (`travel_sessions`, `agent_run_logs`) are created via `backend/migrations/001_init.sql`.

---

## 6. Environment Variables Reference

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Optional* | Supabase PostgreSQL connection URI |
| `GROQ_API_KEY` | **Required** | Groq LLM API key |
| `LANGCHAIN_TRACING_V2` | Optional** | Set to `true` to enable LangSmith tracing |
| `LANGCHAIN_API_KEY` | Optional** | LangSmith API key (from smith.langchain.com) |
| `LANGCHAIN_PROJECT` | Optional** | LangSmith project name (e.g. `TourAlly`) |
| `AVIATION_STACK_API_KEY` | **Recommended** | Powers Aviation MCP for real flight data |
| `TAVILY_API_KEY` | Optional | Tavily web search MCP (hotels, budget) |
| `OPENWEATHER_API_KEY` | Optional | OpenWeather MCP server (weather agent) |

> *Falls back to `MemorySaver` (no persistence across restarts) if not set.
> **Falls back to LLM-only flight information if not set.
> **Tracing is simply disabled if LangSmith vars are not set; the app runs normally.
