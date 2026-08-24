# TourAlly

TourAlly is an AI-powered multi-agent travel planner built with LangGraph, Model Context Protocol (MCP), FastAPI, React, and Supabase. It uses a supervisor-specialist architecture, input guardrails, human-in-the-loop (HITL) checkpointer pauses, and real-time currency conversions.

---

## Key Features

- **Input Guardrails**: Restricts queries strictly to travel-related topics.
- **Supervisor-Specialist Routing**: Intelligently routes planning prompts only to necessary specialists (Flights, Hotels, Weather, Budget).
- **Aviation MCP**: Queries live flight schedules and routes via AviationStack API.
- **Tavily MCP**: Powers web search integration for real-time accommodation listings.
- **Custom Weather MCP**: Retrieves active weather forecasts from OpenWeather.
- **Real-Time Currency Conversion**: Resolves traveler origin location and formats all budget ranges and itinerary prices strictly in their home currency using ExchangeRate-API.
- **PDF Export**: Generates clean, printer-friendly page stylesheets enabling users to download plans as PDF files.
- **State Persistence**: LangGraph session serialization using Supabase PostgreSQL.
- **Observability**: Direct LangSmith tracing integration.

---

## Technical Architecture

```mermaid
flowchart TD
    User(["👤 User"])
    React["⚛️ React UI\n(dist/ :3000)"]
    FastAPI["🚀 FastAPI\n(app.py :8000)"]

    subgraph LangGraph ["🧠 State Machine Node Chain"]
        Supervisor["🛡️ Supervisor & Guardrail"]
        Flight["✈️ Flight Specialist"]
        Hotel["🏨 Hotel Specialist"]
        Weather["🌤️ Weather Specialist"]
        Budget["💰 Budget Specialist"]
        Itinerary["🗺️ Itinerary Compiler"]
        HITL["👁️ HITL Pause (Interrupt)"]
        Finalize["✅ Finalize Node"]
    end

    subgraph Tools ["🔌 MCP Adapters"]
        AviationMCP["AviationStack API"]
        Tavily["Tavily Search"]
        WeatherMCP["OpenWeather API"]
    end

    User --> React
    React -- "REST API" --> FastAPI
    FastAPI --> Supervisor
    Supervisor --> Flight & Hotel & Weather & Budget
    Flight & Hotel & Weather & Budget --> Itinerary
    Itinerary --> HITL
    HITL -- "Approve" --> Finalize
    HITL -- "Revise" --> Itinerary
    Flight --> AviationMCP
    Hotel --> Tavily
    Weather --> WeatherMCP
    Finalize --> FastAPI
    HITL -.->|serialize| Supabase[("🗄️ Supabase PostgreSQL")]
```

For in-depth explanations of nodes, data models, and execution stages, please refer to:
*   [System Architecture Guide](./SYSTEM_ARCHITECTURE.md)
*   [Database Schema Guide](./DATABASE_SCHEMA.md)

---

## Quick Start (Docker Compose - Recommended)

Make sure you have **Docker** and **Docker Compose** installed.

1.  **Configure API Keys**:
    Create a `backend/.env` file in the root workspace directory matching this template:
    ```env
    GROQ_API_KEY=gsk_your_groq_key
    EXCHANGE_RATE_API_KEY=b71d15f8a87bfacd3f0a6726
    DATABASE_URL=postgresql://postgres:[password]@db.[ref].supabase.co:5432/postgres
    
    # Optional integrations:
    AVIATION_STACK_API_KEY=your_aviationstack_key
    TAVILY_API_KEY=your_tavily_key
    OPENWEATHER_API_KEY=your_openweather_key
    ```
2.  **Launch Stack**:
    ```bash
    docker compose up --build
    ```
3.  **Access Services**:
    *   **Frontend Client**: `http://localhost:3000`
    *   **Backend REST API**: `http://localhost:8000` (Health Check: `/health`)

To shut down the active services:
```bash
docker compose down
```

---

## Quick Start (Local Manual Execution)

If running services directly on the host machine:

### 1. Backend Server Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run migrations
python migrations/run_migrations.py

# Launch server
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
React development server will spin up on `http://localhost:5173`.
