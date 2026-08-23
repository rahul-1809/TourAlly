# TourAlly 🌍✈️

> **AI-powered multi-agent travel planner** with Supervisor, Input Guardrails, Human-In-The-Loop approval, and MCP tool integration.

Built with **LangGraph + MCP + FastAPI + React + Supabase**.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🛡️ **Input Guardrails** | LLM validates every query is travel-related before processing |
| 🧠 **Supervisor Agent** | Intelligently selects only the agents needed for your request |
| ✈️ **Flight Agent** | Queries real flight routes, schedules & fares via **Aviation MCP** (AviationStack API) |
| 🏨 **Hotel Agent** | Finds accommodation options and neighbourhoods |
| 🌤️ **Weather Agent** | Gets live weather forecasts via custom OpenWeather MCP server |
| 💰 **Budget Agent** | Estimates total cost and feasibility for your trip |
| 🗺️ **Itinerary Agent** | Synthesises all results into a structured day-by-day plan |
| 👁️ **Human-In-The-Loop** | Review and approve (or revise) the draft plan before finalising |
| 🔭 **LangSmith Observability** | Full trace of every agent step, LLM call, and MCP tool invocation |
| 💾 **State Persistence** | LangGraph checkpointing via Supabase PostgreSQL |
| ⚡ **Premium React UI** | Dark mode, glassmorphism, animated agent steps |

---

## 🏗️ Architecture Overview

```mermaid
flowchart TD
    User(["👤 User"])
    React["⚛️ React + Vite\nfrontend :5173"]
    FastAPI["🚀 FastAPI\nbackend :8000"]

    subgraph LangGraph ["🧠 LangGraph State Machine"]
        Supervisor["🛡️ Supervisor\n+ Guardrail"]
        Flight["✈️ Flight Agent"]
        Hotel["🏨 Hotel Agent"]
        Weather["🌤️ Weather Agent"]
        Budget["💰 Budget Agent"]
        Itinerary["🗺️ Itinerary Agent"]
        HITL["👁️ HITL Approval\n[INTERRUPT]"]
        Finalize["✅ Finalize"]
    end

    subgraph Tools ["🔧 MCP Tool Layer"]
        AviationMCP["✈️ Aviation MCP\nAviationStack API"]
        Tavily["🔍 Tavily MCP\nWeb Search"]
        WeatherMCP["☁️ Custom Weather MCP\nOpenWeather API"]
    end

    Supabase[("🗄️ Supabase\nPostgreSQL")]
    Groq["🤖 Groq API\nLLaMA-3.3-70b"]

    User --> React
    React -- "REST /api/*" --> FastAPI
    FastAPI --> Supervisor
    Supervisor --> Flight & Hotel & Weather & Budget
    Flight --> AviationMCP
    Hotel --> Tavily
    Weather --> WeatherMCP
    Flight & Hotel & Weather & Budget --> Itinerary
    Itinerary --> HITL
    HITL -- "Approved" --> Finalize
    HITL -- "Revise" --> Itinerary
    Finalize --> FastAPI
    Supervisor & Flight & Hotel & Weather & Budget & Itinerary --> Groq
    HITL -- "checkpoint" --> Supabase
```

For the full architecture, see [SYSTEM_ARCHITECTURE.md](./SYSTEM_ARCHITECTURE.md).

---

## 📁 Project Structure

```
TourAlly/
├── backend/
│   ├── app.py                        # FastAPI app & REST endpoints
│   ├── backend.py                    # LangGraph agent graph
│   ├── mcp_client.py                 # MCP client helpers (Tavily + Weather)
│   ├── custom_weather_mcp_server.py  # Custom FastMCP weather server
│   ├── migrations/
│   │   ├── 001_init.sql              # App table migrations
│   │   └── run_migrations.py        # Migration runner
│   ├── requirements.txt
│   ├── .env.example
│   └── .gitignore
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx                   # Root component + state management
│   │   ├── main.jsx
│   │   ├── styles/
│   │   │   └── global.css            # Design tokens + global styles
│   │   ├── api/
│   │   │   └── travel.js             # API call wrappers
│   │   └── components/
│   │       ├── Header/
│   │       ├── TripForm/
│   │       ├── ChatPanel/
│   │       ├── AgentSteps/
│   │       ├── HitlPanel/
│   │       └── ItineraryCard/
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
│
├── DATABASE_SCHEMA.md
├── IMPLEMENTATION_PLAN.md
├── SYSTEM_ARCHITECTURE.md
└── README.md                         ← You are here
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **Node.js 20+**
- **Supabase account** (free tier works) — [supabase.com](https://supabase.com)
- **Groq API key** (free) — [console.groq.com](https://console.groq.com)

### Optional (for real data)
- **Tavily API key** (free tier) — [tavily.com](https://tavily.com)
- **OpenWeather API key** (free tier) — [openweathermap.org/api](https://openweathermap.org/api)

---

### Step 1 — Clone the repo

```bash
git clone https://github.com/your-username/TourAlly.git
cd TourAlly
```

---

### Step 2 — Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate          # macOS / Linux
# .venv\Scripts\Activate.ps1      # Windows PowerShell

# Install dependencies
pip install -r requirements.txt
```

---

### Step 3 — Configure Environment Variables

```bash
cp .env.example .env
```

Edit `backend/.env`:

```env
# Required
GROQ_API_KEY=gsk_...

# Supabase PostgreSQL (for HITL state persistence)
# Settings → Database → Connection string → URI
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-REF].supabase.co:5432/postgres

# LangSmith Observability (optional but highly recommended)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls__...         # From smith.langchain.com
LANGCHAIN_PROJECT=TourAlly

# Optional — enables real flight data
AVIATION_STACK_API_KEY=xyz789...

# Optional — enables real web search for hotels/budget
TAVILY_API_KEY=tvly-...

# Optional — enables live weather data
OPENWEATHER_API_KEY=abc123...
```

> **Note**: The app works with just `GROQ_API_KEY`. Tavily and Weather fall back to LLM-generated responses. Without `DATABASE_URL`, it uses in-memory state (no persistence across restarts). Without `LANGCHAIN_API_KEY`, tracing is simply disabled.

---

### Step 4 — Run Database Migrations

```bash
# This creates the travel_sessions and agent_run_logs tables in Supabase
# LangGraph checkpoint tables are created automatically on first run
python migrations/run_migrations.py
```

---

### Step 5 — Start the Backend

```bash
# From the backend/ directory
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`. Check `http://localhost:8000/health` to verify.

---

### Step 6 — Frontend Setup

```bash
# Open a new terminal
cd frontend
npm install
npm run dev
```

The React app will be available at `http://localhost:5173`.

---

### Step 7 — (Optional) Run the Weather MCP Server

The custom weather MCP server is started automatically as a subprocess by the backend. You only need to run it manually if you want to test it in isolation:

```bash
cd backend
python custom_weather_mcp_server.py
```

---

### 🐳 Running with Docker Compose (Recommended)

To run the entire application using Docker Compose:

1. Make sure you have **Docker** and **Docker Compose** installed.
2. Ensure you have created your `backend/.env` file with at least `GROQ_API_KEY` (or `GROQ_API_KEY_FALLBACK`) defined.
3. Build and launch the containers:
   ```bash
   docker compose up --build
   ```
4. The services will be accessible at:
   - Frontend React app: `http://localhost:3000` (proxies `/api` to the backend)
   - Backend FastAPI server: `http://localhost:8000`
5. To stop the containers:
   ```bash
   docker compose down
   ```

---

## 🎯 Usage

```mermaid
sequenceDiagram
    actor User
    participant UI as React UI
    participant API as FastAPI
    participant LG as LangGraph
    participant DB as Supabase

    User->>UI: Enter travel query
    UI->>API: POST /api/travel
    API->>LG: run_travel_agent()
    LG->>DB: Save checkpoint per node
    Note over LG: Agents run in sequence
    LG-->>API: interrupt() — plan ready
    API-->>UI: awaiting_approval: true
    UI-->>User: Show draft plan + HITL panel

    alt User Approves
        User->>UI: Click Approve
        UI->>API: POST /api/travel/approve approved=true
        API->>LG: resume_travel_agent()
        LG-->>API: final_response
        API-->>UI: status: completed
        UI-->>User: Show final itinerary ✅
    else User Requests Revision
        User->>UI: Add feedback + Click Revise
        UI->>API: POST /api/travel/approve approved=false
        API->>LG: resume with feedback
        LG->>LG: itinerary_agent re-runs
        LG-->>API: interrupt() again
        API-->>UI: awaiting_approval: true
        UI-->>User: Show revised draft 🔄
    end
```

---

## 🔌 API Reference

### `POST /api/travel`

Start or resume a travel planning session.

```json
// Request
{
  "message": "Plan a 5-day trip to Paris from New York with a $3,000 budget",
  "thread_id": null   // omit or null to start a new session
}

// Response
{
  "thread_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "awaiting_approval",
  "content": "Here's your draft Paris travel plan...",
  "awaiting_approval": true,
  "agents_run": ["supervisor", "flight_agent", "hotel_agent", "weather_agent", "itinerary_agent"]
}
```

### `POST /api/travel/approve`

Approve or request revision of the draft plan.

```json
// Approve
{ "thread_id": "...", "approved": true, "feedback": "" }

// Request revision
{ "thread_id": "...", "approved": false, "feedback": "Add more budget options" }
```

### `GET /health`

```json
{
  "status": "ok",
  "version": "1.0.0",
  "features": { "groq_llm": true, "tavily_mcp": true, "weather_mcp": true, "supabase_checkpointing": true }
}
```

---

## 🗄️ Database

TourAlly uses Supabase (PostgreSQL) for:

1. **LangGraph checkpoints** — auto-managed, enables HITL pause/resume
2. **Session tracking** — `travel_sessions` and `agent_run_logs` tables

See [DATABASE_SCHEMA.md](./DATABASE_SCHEMA.md) for full schema documentation.

---

## 🐳 Docker

```bash
# Build and run both services
docker compose up --build

# Frontend → http://localhost:3000
# Backend  → http://localhost:8000
```

Make sure `backend/.env` is configured before running Docker.

---

## 🧪 Testing the Guardrail

The input guardrail blocks non-travel queries. Try these to see it in action:

| Query | Expected Result |
|---|---|
| *"Plan a trip to Paris"* | ✅ Allowed — starts planning |
| *"What's the weather in Bali?"* | ✅ Allowed — weather + itinerary |
| *"How do I hack a website?"* | 🚫 Blocked — guardrail message |
| *"Write me a poem"* | 🚫 Blocked — guardrail message |
| *"What's the capital of France?"* | ✅ Allowed — travel knowledge query |

---

## 📚 Documentation

| Document | Description |
|---|---|
| [DATABASE_SCHEMA.md](./DATABASE_SCHEMA.md) | Full Supabase schema, table definitions, ERD |
| [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) | Phase-by-phase build plan with task checklists |
| [SYSTEM_ARCHITECTURE.md](./SYSTEM_ARCHITECTURE.md) | Architecture diagrams, API design, data flow |

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| LLM | Groq LLaMA-3.3-70b |
| Agent Framework | LangGraph 1.2 |
| Observability | **LangSmith** (tracing + evaluation) |
| Tool Calling | MCP (langchain-mcp-adapters) |
| Flight Data | **Aviation MCP** (AviationStack API) |
| Web Search | Tavily MCP (hotels, budget) |
| Weather | Custom FastMCP + OpenWeather API |
| API Server | FastAPI + Uvicorn |
| State Persistence | LangGraph PostgresSaver + Supabase |
| Frontend | React 18 + Vite 5 |
| Styling | CSS Modules (no frameworks) |

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit changes: `git commit -m 'Add my feature'`
4. Push to branch: `git push origin feature/my-feature`
5. Open a Pull Request

---

## 📄 License

This project is licensed under the Apache-2.0 License — see the [LICENSE](./LICENSE) file for details.

---

## 🙏 Acknowledgements

Inspired by [entbappy/Multi-Agent-System-using-LangGraph-MCP-Supervisor-Guardrails-HITL](https://github.com/entbappy/Multi-Agent-System-using-LangGraph-MCP-Supervisor-Guardrails-HITL).

Built as a demonstration of LangGraph + MCP patterns with supervisor, guardrail, and HITL concepts.
