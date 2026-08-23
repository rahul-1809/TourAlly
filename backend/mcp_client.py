import os
import httpx
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client

# ─── 2.3 Tavily MCP Client + REST Fallback ─────────────────────
async def fallback_tavily_search(query: str, api_key: str) -> str:
    """Direct HTTP REST fallback if Tavily MCP connection fails."""
    url = "https://api.tavily.com/search"
    payload = {
        "api_key": api_key,
        "query": query,
        "max_results": 3  # Limit results to keep token count low
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)
            if response.status_code != 200:
                return f"Tavily search error: Status code {response.status_code}"
            data = response.json()
            results = data.get("results", [])
            if not results:
                return "No search results found."
            
            res_str = ""
            for r in results[:3]:
                title = r.get("title", "No Title")
                content = r.get("content", "")[:500]  # Truncate content snippet
                url_str = r.get("url", "")
                res_str += f"### {title}\nSource: {url_str}\n{content}\n\n"
            return res_str
    except Exception as e:
        return f"Tavily request failed: {str(e)}"

async def tavily_mcp_search(query: str) -> str:
    """Search hotels, neighborhood safety, activities using Tavily SSE MCP Server."""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "Tavily API key not configured."
    
    url = f"https://mcp.tavily.com/mcp/?tavilyApiKey={api_key}"
    try:
        async with sse_client(url) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                # Run tavily_search tool via MCP
                result = await session.call_tool("tavily_search", arguments={"query": query})
                text_content = "".join([c.text for c in result.content if hasattr(c, "text")] or [str(result)])
                if text_content.strip():
                    return text_content[:1200]  # Truncate result context
                return await fallback_tavily_search(query, api_key)
    except Exception as e:
        print(f"[TAVILY MCP] SSE connection failed ({str(e)}). Falling back to direct REST API...")
        return await fallback_tavily_search(query, api_key)

# ─── 2.1 Weather MCP Server Client Helpers ─────────────────────
async def weather_mcp_search(city: str) -> str:
    """Get current weather for a city by running custom weather stdio MCP server."""
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return "OpenWeather API key not configured. Cannot retrieve live weather."
    
    server_path = str(Path(__file__).resolve().parent / "custom_weather_mcp_server.py")
    server_params = StdioServerParameters(
        command=".venv/bin/python",
        args=[server_path]
    )
    try:
        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool("get_current_weather", arguments={"city": city})
                return "".join([c.text for c in result.content if hasattr(c, "text")] or [str(result)])
    except Exception as e:
        return f"Weather MCP Tool Call failed: {str(e)}"

async def forecast_mcp_search(city: str, days: int = 3) -> str:
    """Get weather forecast for a city by running custom weather stdio MCP server."""
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return "OpenWeather API key not configured. Cannot retrieve weather forecast."
    
    server_path = str(Path(__file__).resolve().parent / "custom_weather_mcp_server.py")
    server_params = StdioServerParameters(
        command=".venv/bin/python",
        args=[server_path]
    )
    try:
        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool("get_weather_forecast", arguments={"city": city, "days": days})
                return "".join([c.text for c in result.content if hasattr(c, "text")] or [str(result)])
    except Exception as e:
        return f"Weather Forecast MCP Tool Call failed: {str(e)}"

# ─── 2.2 Aviation stack API Client Helpers ─────────────────────
async def aviation_get_flights(origin_iata: str, destination_iata: str, date: str = None) -> str:
    """Fetch live flight schedules, airlines, routes and details between two IATA airports."""
    api_key = os.getenv("AVIATION_STACK_API_KEY")
    if not api_key:
        return "AviationStack API key not configured. Cannot fetch flight details."
    
    url = "http://api.aviationstack.com/v1/flights"
    params = {
        "access_key": api_key,
        "dep_iata": origin_iata,
        "arr_iata": destination_iata,
        "limit": 5
    }
    if date:
        params["flight_date"] = date
        
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            if response.status_code != 200:
                return f"AviationStack API returned status code {response.status_code}"
            
            data = response.json()
            flights = data.get("data", [])
            if not flights:
                return f"No active flights found between {origin_iata} and {destination_iata}."
            
            res_str = f"Real-Time Flight Options ({origin_iata} ➔ {destination_iata}):\n"
            for f in flights:
                date_str = f.get("flight_date", "N/A")
                airline = f.get("airline", {}).get("name", "N/A")
                flight_num = f.get("flight", {}).get("iata", "N/A")
                status = f.get("flight_status", "N/A")
                dep = f.get("departure", {})
                arr = f.get("arrival", {})
                dep_time = dep.get("scheduled", "N/A")
                arr_time = arr.get("scheduled", "N/A")
                dep_airport = dep.get("airport", origin_iata)
                arr_airport = arr.get("airport", destination_iata)
                
                res_str += (
                    f"- Flight {flight_num} ({airline}) | Status: {status.upper()}\n"
                    f"  Departs: {dep_airport} at {dep_time}\n"
                    f"  Arrives: {arr_airport} at {arr_time}\n"
                )
            return res_str
    except Exception as e:
        return f"AviationStack connection failed: {str(e)}"

def extract_iata_codes(origin_city: str, destination_city: str) -> dict:
    """Uses LLM to lookup 3-letter IATA airport codes for origin and destination cities."""
    from backend import _llm_text, _json_from_llm
    
    system_prompt = (
        "You are an aviation specialist assistant. Your job is to find the 3-letter IATA airport codes "
        "for the given origin and destination cities.\n"
        "Respond ONLY with a JSON object in this format: {\"origin_iata\": \"...\", \"destination_iata\": \"...\"}."
    )
    user_prompt = f"Origin City: {origin_city}, Destination City: {destination_city}"
    try:
        res = _llm_text(system_prompt, user_prompt)
        res_json = _json_from_llm(res)
        return {
            "origin_iata": res_json.get("origin_iata", "").upper(),
            "destination_iata": res_json.get("destination_iata", "").upper()
        }
    except Exception:
        return {"origin_iata": "", "destination_iata": ""}
