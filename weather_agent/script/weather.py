# pip install -qU langchain langchain-ollama
import json
import sys
import urllib.parse
from pathlib import Path
import urllib.request

from langchain.agents import create_agent

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# WMO weather interpretation codes used by Open-Meteo.
WEATHER_CODES = {
    0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
    45: "fog", 48: "freezing fog",
    51: "light drizzle", 53: "moderate drizzle", 55: "dense drizzle",
    56: "light freezing drizzle", 57: "dense freezing drizzle",
    61: "light rain", 63: "moderate rain", 65: "heavy rain",
    66: "light freezing rain", 67: "heavy freezing rain",
    71: "light snow", 73: "moderate snow", 75: "heavy snow", 77: "snow grains",
    80: "light rain showers", 81: "moderate rain showers", 82: "violent rain showers",
    85: "light snow showers", 86: "heavy snow showers",
    95: "thunderstorm", 96: "thunderstorm with light hail", 99: "thunderstorm with heavy hail",
}


def _get_json(url: str, params: dict) -> dict:
    full_url = f"{url}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(full_url, timeout=10) as resp:
        return json.load(resp)


def _find_location(city: str) -> dict | None:
    """Look up a city. Accepts "City" or "City, State/Country"."""
    name, _, region = (part.strip() for part in city.partition(","))
    results = _get_json(GEOCODE_URL, {"name": name, "count": 10}).get("results") or []
    if region:
        region_lower = region.lower()
        for r in results:
            fields = (r.get("admin1", ""), r.get("country", ""), r.get("country_code", ""))
            if any(region_lower == f.lower() for f in fields if f):
                return r
    return results[0] if results else None


def get_weather(city: str) -> str:
    """Get the current weather for a city, e.g. "Columbus, Ohio" or "Paris"."""
    try:
        loc = _find_location(city)
        if loc is None:
            return f"Could not find a location named '{city}'."

        current = _get_json(FORECAST_URL, {
            "latitude": loc["latitude"],
            "longitude": loc["longitude"],
            "current": "temperature_2m,apparent_temperature,relative_humidity_2m,weather_code,wind_speed_10m",
            "temperature_unit": "fahrenheit",
            "wind_speed_unit": "mph",
        })["current"]
    except Exception as e:  # network errors, bad responses
        return f"Could not get weather for '{city}': {e}"

    place = ", ".join(p for p in (loc.get("name"), loc.get("admin1"), loc.get("country")) if p)
    condition = WEATHER_CODES.get(current["weather_code"], f"weather code {current['weather_code']}")
    return (
        f"{place}: {condition}, {current['temperature_2m']}°F "
        f"(feels like {current['apparent_temperature']}°F), "
        f"humidity {current['relative_humidity_2m']}%, wind {current['wind_speed_10m']} mph."
    )


SKILL_PATH = Path(__file__).resolve().parent.parent / "skill" / "weather.md"


def _load_skill() -> str:
    """Use the skill file (minus its frontmatter) as the system prompt."""
    text = SKILL_PATH.read_text(encoding="utf-8")
    if text.startswith("---"):
        text = text.split("---", 2)[-1]
    return text.strip()


if __name__ == "__main__":
    # Requires: pip install -qU langchain langchain-ollama
    # and a local Ollama server with: ollama pull qwen2.5:7b
    agent = create_agent(
        model="ollama:qwen2.5:7b",
        tools=[get_weather],
        system_prompt=_load_skill(),
    )

    question = " ".join(sys.argv[1:]) or input("Ask about the weather: ")
    result = agent.invoke({"messages": [{"role": "user", "content": question}]})
    print(result["messages"][-1].content)
