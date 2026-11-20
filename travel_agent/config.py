"""Central configuration: paths, city metadata and tunable constants."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("TRAVEL_DATA_DIR", PROJECT_ROOT / "data"))
DB_PATH = Path(os.getenv("TRAVEL_DB_PATH", PROJECT_ROOT / "trips.db"))

# City metadata: coordinates (for Open-Meteo) and airport codes (for display).
CITIES: dict[str, dict] = {
    "Bangalore": {"code": "BLR", "lat": 12.9716, "lon": 77.5946},
    "Chennai": {"code": "MAA", "lat": 13.0827, "lon": 80.2707},
    "Delhi": {"code": "DEL", "lat": 28.6139, "lon": 77.2090},
    "Goa": {"code": "GOI", "lat": 15.2993, "lon": 74.1240},
    "Hyderabad": {"code": "HYD", "lat": 17.3850, "lon": 78.4867},
    "Jaipur": {"code": "JAI", "lat": 26.9124, "lon": 75.7873},
    "Kolkata": {"code": "CCU", "lat": 22.5726, "lon": 88.3639},
    "Mumbai": {"code": "BOM", "lat": 19.0760, "lon": 72.8777},
}

# Per-person, per-day spend on food and local transport (INR) by travel style.
DAILY_LOCAL_EXPENSE: dict[str, int] = {"Budget": 700, "Comfort": 1100, "Luxury": 2200}

# Guests per hotel room when working out how many rooms a party needs.
GUESTS_PER_ROOM = 2

MIN_DAYS, MAX_DAYS = 3, 7

OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
OPEN_METEO_FORECAST_HORIZON_DAYS = 15
HTTP_TIMEOUT_SECONDS = 8

# Outdoor places lose priority on rainy days.
OUTDOOR_PLACE_TYPES = {"park", "beach", "lake", "fort"}
INDOOR_PLACE_TYPES = {"museum", "market", "temple", "monument"}


@dataclass(frozen=True)
class LLMSettings:
    """Which chat model backs the agent. Resolved from environment variables."""

    provider: str | None
    model: str | None



def resolve_llm_settings() -> LLMSettings:
    """Pick an LLM provider from available API keys."""

    forced = os.getenv("LLM_PROVIDER", "").strip().lower()

    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")

    model_override = os.getenv("LLM_MODEL", "").strip()

    if forced == "anthropic" or (not forced and anthropic_key):
        return LLMSettings(
            "anthropic",
            model_override or "claude-sonnet-4-5"
        )

    if forced == "openai" or (not forced and openai_key):
        return LLMSettings(
            "openai",
            model_override or "gpt-4o-mini"
        )

    if forced == "groq" or (not forced and groq_key):
        return LLMSettings(
            "groq",
            model_override or "llama-3.3-70b-versatile"
        )

    return LLMSettings(None, None)

