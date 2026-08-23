import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

from mcp_client import (
    tavily_mcp_search,
    weather_mcp_search,
    forecast_mcp_search,
    aviation_get_flights,
    extract_iata_codes,
)

async def test_all_mcp():
    print("=== Test 1: Extract IATA Codes (London, Paris) ===")
    codes = extract_iata_codes("London", "Paris")
    print(f"IATA codes: {codes}")
    
    print("\n=== Test 2: Aviation Get Flights ===")
    origin = codes.get("origin_iata", "LHR")
    dest = codes.get("destination_iata", "CDG")
    flights = await aviation_get_flights(origin, dest)
    print(f"Flights (truncated): {flights[:300]}...")
    
    print("\n=== Test 3: Weather MCP Get Weather (Paris) ===")
    weather = await weather_mcp_search("Paris")
    print(f"Current weather: {weather}")
    
    print("\n=== Test 4: Weather MCP Get Forecast (Paris) ===")
    forecast = await forecast_mcp_search("Paris", days=3)
    print(f"Weather forecast:\n{forecast}")
    
    print("\n=== Test 5: Tavily MCP Search (Best hotels in Paris) ===")
    tavily_res = await tavily_mcp_search("best hotels in Paris")
    print(f"Search results (truncated): {tavily_res[:300]}...")

if __name__ == "__main__":
    # Ensure event loop runs properly
    asyncio.run(test_all_mcp())
