import os
from collections import Counter
from pathlib import Path
import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Load environment variables
load_dotenv(Path(__file__).resolve().parent / ".env")

# Initialize FastMCP Server
mcp = FastMCP("Weather MCP Server")

@mcp.tool()
async def get_current_weather(city: str) -> str:
    """Get the current weather conditions for a given city."""
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return "Error: OPENWEATHER_API_KEY is not configured in backend/.env"
    
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            if response.status_code == 404:
                return f"Error: City '{city}' not found."
            if response.status_code != 200:
                return f"Error: Could not retrieve weather for {city}. Status code: {response.status_code}"
            
            data = response.json()
            main = data.get("main", {})
            weather = data.get("weather", [{}])[0]
            temp = main.get("temp", "N/A")
            feels_like = main.get("feels_like", "N/A")
            desc = weather.get("description", "N/A")
            humidity = main.get("humidity", "N/A")
            
            return (
                f"Current weather in {city}:\n"
                f"- Temperature: {temp}°C (feels like {feels_like}°C)\n"
                f"- Conditions: {desc.capitalize()}\n"
                f"- Humidity: {humidity}%"
            )
    except httpx.RequestError as e:
        return f"Error: Network timeout or connection error: {str(e)}"

@mcp.tool()
async def get_weather_forecast(city: str, days: int = 3) -> str:
    """Get the weather forecast for a given city for a specified number of days (1-5)."""
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return "Error: OPENWEATHER_API_KEY is not configured in backend/.env"
    
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            if response.status_code == 404:
                return f"Error: City '{city}' not found."
            if response.status_code != 200:
                return f"Error: Could not retrieve forecast for {city}. Status code: {response.status_code}"
            
            data = response.json()
            forecast_list = data.get("list", [])
            
            # OpenWeather 5-day forecast returns measurements every 3 hours. Group by date.
            daily_readings = {}
            for item in forecast_list:
                dt_txt = item.get("dt_txt", "")
                if not dt_txt:
                    continue
                date = dt_txt.split(" ")[0]
                if date not in daily_readings:
                    daily_readings[date] = []
                daily_readings[date].append(item)
            
            summary = f"Weather forecast for {city} over the next {days} days:\n"
            for i, (date, readings) in enumerate(list(daily_readings.items())[:days]):
                temps = [r.get("main", {}).get("temp", 0.0) for r in readings]
                descriptions = [r.get("weather", [{}])[0].get("description", "") for r in readings]
                avg_temp = sum(temps) / len(temps) if temps else 0.0
                common_desc = Counter(descriptions).most_common(1)[0][0] if descriptions else "N/A"
                summary += f"- {date}: Avg Temp: {avg_temp:.1f}°C, Conditions: {common_desc.capitalize()}\n"
                
            return summary
    except httpx.RequestError as e:
        return f"Error: Network timeout or connection error: {str(e)}"

if __name__ == "__main__":
    # Start the FastMCP stdio server
    mcp.run()
