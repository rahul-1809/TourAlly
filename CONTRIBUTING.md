# Contributing to TourAlly

Thank you for contributing to TourAlly! We appreciate your support in making this multi-agent travel planner better. Please follow these guidelines to set up your environment, follow our workflow, and understand the system architecture.

---

## 🛠️ Local Development Setup

TourAlly is organized as a monorepos containing both frontend and backend layers:

### 1. Backend Setup (FastAPI + LangGraph)
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and fill in the required API keys (Groq is required; others like AviationStack, Tavily, OpenWeather are optional and fall back gracefully to LLM estimation).
5. Start the backend development server:
   ```bash
   uvicorn app:app --host 0.0.0.0 --port 8000 --loop asyncio
   ```
   *Note: You must run uvicorn with `--loop asyncio` to prevent `nest_asyncio` / `uvloop` loop patching incompatibilities.*

### 2. Frontend Setup (React + Vite)
1. Navigate to the frontend directory:
   ```bash
   cd ../frontend
   ```
2. Install npm dependencies:
   ```bash
   npm install
   ```
3. Start the dev server:
   ```bash
   npm run dev
   ```
4. The frontend will be active at `http://localhost:5173/`, proxying `/api` requests to port `8000`.

---

## 🧠 System Architecture

- **Supervisor Agent Pattern**: The supervisor node (`supervisor_node`) evaluates queries via the input guardrails and determines which specialist agents (Flight, Hotel, Weather, Budget) need to run.
- **Model Context Protocol (MCP)**:
  - Custom Weather MCP Server (`custom_weather_mcp_server.py`): Starts via standard stdio pipe and fetches real-time forecasts from OpenWeather.
  - Tavily Search MCP: Connects via SSE protocol to fetch hotels and regional budgets.
- **Human-in-the-Loop (HITL)**: LangGraph state machines pause at the review node (`hitl_node`) via `interrupt()`, awaiting user feedback or approval via the frontend.

---

## 🚀 Git and PR Guidelines

1. **Branch Names**: Use clear prefixes for branch names:
   - `feat/feature-name` for new features
   - `fix/bug-description` for bug fixes
   - `docs/changes` for documentation updates
2. **Code Style**:
   - Python: Ensure code is formatted cleanly and matches pep8 rules. Keep comments and docstrings intact.
   - React/JS: Use functional components, state hooks, and CSS styling tokens.
3. **Commit Messages**: Write clear, descriptive commits. Prefix messages where appropriate (e.g., `feat: add request logging middleware`).
