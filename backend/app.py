import os
import time
import nest_asyncio
from fastapi import FastAPI, HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional

from langgraph.checkpoint.postgres import PostgresSaver

# Import the LangGraph API wrappers
from backend import run_travel_agent, resume_travel_agent

# Apply nest_asyncio to support nested event loops in sync-in-async environments (e.g. LangGraph checkpointer calls)
nest_asyncio.apply()

app = FastAPI(
    title="TourAlly API",
    description="Backend REST API for TourAlly Multi-Agent Travel Planner, powered by LangGraph, MCP, Groq, and Supabase.",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    # ─── Environment Validation ───
    groq_key = os.getenv("GROQ_API_KEY") or os.getenv("GROQ_API_KEY_FALLBACK")
    if not groq_key:
        print("❌ CRITICAL ERROR: GROQ_API_KEY or GROQ_API_KEY_FALLBACK environment variable is missing!")
        print("Please check your backend/.env configuration.")
        raise RuntimeError("Missing required GROQ_API_KEY configuration.")

    print("✅ Environment Validation Passed: Groq API Key is configured.")

    optional_keys = {
        "AVIATION_STACK_API_KEY": "Aviation Stack Flight API integration",
        "TAVILY_API_KEY": "Tavily Web Search hotel & budget integration",
        "OPENWEATHER_API_KEY": "OpenWeather API custom weather MCP integration",
        "LANGCHAIN_API_KEY": "LangSmith execution observability tracing"
    }
    for key, desc in optional_keys.items():
        if not os.getenv(key):
            print(f"⚠️ Warning: Optional environment variable {key} is missing. {desc} will be disabled.")

    db_url = os.getenv("DATABASE_URL")
    if db_url:
        print("Initializing PostgresSaver checkpointer database...")
        try:
            with PostgresSaver.from_conn_string(db_url) as saver:
                saver.setup()
            print("PostgresSaver checkpointer database initialized.")
        except Exception as e:
            print(f"Error initializing PostgresSaver checkpointer: {e}")
    else:
        print("No DATABASE_URL found. Running with MemorySaver checkpointer.")

# CORS middleware to allow connection from Vite React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom telemetry request logging middleware
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        print(
            f"📥 Request: {request.method} {request.url.path} | "
            f"Response Status: {response.status_code} | "
            f"Duration: {process_time:.2f}ms"
        )
        return response

app.add_middleware(RequestLoggingMiddleware)

# ─── Pydantic Request Models ──────────────────────────────────
class TravelRequest(BaseModel):
    message: str = Field(..., description="Travel query, e.g. 'Plan a 3-day trip to Paris from London'")
    thread_id: Optional[str] = Field(None, description="Optional unique session/thread identifier")

class ApproveRequest(BaseModel):
    thread_id: str = Field(..., description="Active session/thread ID to resume")
    approved: bool = Field(..., description="Approval status (True to finalise, False to request revision)")
    feedback: Optional[str] = Field("", description="Human revision instructions/feedback")

# ─── Endpoints ────────────────────────────────────────────────
@app.post("/api/travel")
async def travel_endpoint(request: TravelRequest):
    """Initiates a travel planning session or sends a new query within an existing session."""
    try:
        result = run_travel_agent(request.message, request.thread_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/travel/approve")
async def approve_endpoint(request: ApproveRequest):
    """Resumes graph execution after a human-in-the-loop pause, sending approval/feedback."""
    try:
        result = resume_travel_agent(request.thread_id, request.approved, request.feedback)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
@app.get("/api/health")
async def health_endpoint():
    """Verify backend health and active key integrations."""
    return {
        "status": "ok",
        "integrations": {
            "supabase_checkpointing": bool(os.getenv("DATABASE_URL")),
            "aviation_mcp": bool(os.getenv("AVIATION_STACK_API_KEY")),
            "tavily_mcp": bool(os.getenv("TAVILY_API_KEY")),
            "weather_mcp": bool(os.getenv("OPENWEATHER_API_KEY")),
            "langsmith_observability": bool(os.getenv("LANGCHAIN_API_KEY"))
        }
    }

# ─── Global Exception Handler ──────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal Server Error: {str(exc)}"}
    )
