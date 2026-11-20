"""Weather lookup via the free Open-Meteo API, with graceful fallbacks.

Order of preference for every requested date:
1. Live forecast (dates within Open-Meteo's ~16 day horizon).
2. Historical weather for the same dates a year earlier ("typical conditions").
3. A built-in seasonal estimate when the network is unavailable.
"""

from __future__ import annotations

import logging
import time
from datetime import date, timedelta

import requests

from ..config import (
    CITIES,
    HTTP_TIMEOUT_SECONDS,
    OPEN_METEO_ARCHIVE_URL,
    OPEN_METEO_FORECAST_HORIZON_DAYS,
    OPEN_METEO_FORECAST_URL,
)

logger = logging.getLogger(__name__)

# WMO weather interpretation codes -> (label, icon key)
WMO_CODES: dict[int, tuple[str, str]] = {
    0: ("Clear sky", "sun"),
    1: ("Mostly clear", "sun"),
    2: ("Partly cloudy", "partly"),
    3: ("Overcast", "cloud"),
    45: ("Fog", "fog"),
    48: ("Fog", "fog"),
    51: ("Light drizzle", "rain"),
    53: ("Drizzle", "rain"),
    55: ("Heavy drizzle", "rain"),
    56: ("Freezing drizzle", "rain"),
    57: ("Freezing drizzle", "rain"),
    61: ("Light rain", "rain"),
    63: ("Rain", "rain"),
    65: ("Heavy rain", "rain"),
    66: ("Freezing rain", "rain"),
    67: ("Freezing rain", "rain"),
    71: ("Light snow", "snow"),
    73: ("Snow", "snow"),
    75: ("Heavy snow", "snow"),
    77: ("Snow grains", "snow"),
    80: ("Rain showers", "rain"),
    81: ("Rain showers", "rain"),
    82: ("Violent showers", "storm"),
    85: ("Snow showers", "snow"),
    86: ("Snow showers", "snow"),
    95: ("Thunderstorm", "storm"),
    96: ("Thunderstorm with hail", "storm"),
    99: ("Thunderstorm with hail", "storm"),
}

# Approximate monthly average highs (Celsius) and rain chance (%) per city.
# Used only when Open-Meteo cannot be reached. Shown to users as an estimate.
SEASONAL_NORMALS: dict[str, dict[str, list[int]]] = {
    "Delhi": {"high": [21, 24, 30, 37, 40, 39, 35, 34, 34, 33, 28, 23], "rain": [10, 10, 8, 6, 10, 30, 60, 65, 40, 10, 3, 5]},
    "Mumbai": {"high": [31, 31, 33, 33, 34, 32, 30, 30, 31, 34, 34, 32], "rain": [2, 2, 2, 3, 10, 60, 85, 80, 60, 20, 8, 3]},
    "Bangalore": {"high": [28, 31, 34, 35, 34, 30, 28, 28, 29, 29, 27, 27], "rain": [5, 5, 8, 20, 40, 45, 50, 50, 50, 50, 30, 10]},
    "Chennai": {"high": [29, 31, 33, 35, 38, 37, 35, 35, 34, 32, 29, 28], "rain": [15, 5, 5, 8, 15, 20, 25, 30, 30, 55, 70, 55]},
    "Hyderabad": {"high": [29, 32, 36, 38, 40, 35, 31, 30, 31, 31, 29, 28], "rain": [5, 5, 8, 12, 20, 45, 55, 60, 55, 25, 10, 5]},
    "Kolkata": {"high": [26, 29, 34, 36, 36, 34, 32, 32, 32, 32, 29, 26], "rain": [8, 12, 15, 30, 45, 70, 85, 85, 75, 40, 8, 4]},
    "Goa": {"high": [32, 32, 33, 33, 33, 30, 29, 29, 30, 32, 33, 33], "rain": [0, 0, 2, 5, 20, 85, 95, 90, 70, 30, 10, 2]},
    "Jaipur": {"high": [23, 26, 32, 38, 41, 39, 34, 32, 34, 34, 29, 24], "rain": [5, 8, 6, 5, 10, 25, 60, 65, 40, 8, 3, 3]},
}


def _describe(code: int | None) -> tuple[str, str]:
    return WMO_CODES.get(int(code), ("Mixed conditions", "partly")) if code is not None else ("Mixed conditions", "partly")


def _day_record(day: date, code, high, low, rain_chance, source: str) -> dict:
    label, icon = _describe(code)
    return {
        "date": day.isoformat(),
        "condition": label,
        "icon": icon,
        "temp_max": None if high is None else round(high),
        "temp_min": None if low is None else round(low),
        "rain_chance": None if rain_chance is None else round(rain_chance),
        "source": source,
    }


def _fetch_forecast(lat: float, lon: float, start: date, end: date) -> dict[str, dict]:
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
        "timezone": "auto",
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
    }
    response = requests.get(OPEN_METEO_FORECAST_URL, params=params, timeout=HTTP_TIMEOUT_SECONDS)
    response.raise_for_status()
    daily = response.json()["daily"]
    return {
        day: _day_record(
            date.fromisoformat(day),
            daily["weather_code"][i],
            daily["temperature_2m_max"][i],
            daily["temperature_2m_min"][i],
            daily["precipitation_probability_max"][i],
            "forecast",
        )
        for i, day in enumerate(daily["time"])
    }


def _same_day_last_year(day: date) -> date:
    try:
        return day.replace(year=day.year - 1)
    except ValueError:  # 29 February
        return day.replace(year=day.year - 1, day=28)


def _fetch_historical(lat: float, lon: float, days: list[date]) -> dict[str, dict]:
    """Weather for the same calendar dates one year earlier, keyed by the *requested* date."""
    past = [_same_day_last_year(d) for d in days]
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": "auto",
        "start_date": min(past).isoformat(),
        "end_date": max(past).isoformat(),
    }
    response = requests.get(OPEN_METEO_ARCHIVE_URL, params=params, timeout=HTTP_TIMEOUT_SECONDS)
    response.raise_for_status()
    daily = response.json()["daily"]
    by_past_date = {t: i for i, t in enumerate(daily["time"])}
    result = {}
    for requested, earlier in zip(days, past):
        i = by_past_date.get(earlier.isoformat())
        if i is None:
            continue
        precipitation = daily["precipitation_sum"][i] or 0
        rain_chance = 80 if precipitation >= 5 else 55 if precipitation >= 1 else 20 if precipitation > 0 else 5
        result[requested.isoformat()] = _day_record(
            requested,
            daily["weather_code"][i],
            daily["temperature_2m_max"][i],
            daily["temperature_2m_min"][i],
            rain_chance,
            "historical",
        )
    return result


def _seasonal_estimate(city: str, day: date) -> dict:
    normals = SEASONAL_NORMALS.get(city)
    if normals is None:
        return _day_record(day, None, None, None, None, "estimate")
    month = day.month - 1
    high, rain = normals["high"][month], normals["rain"][month]
    code = 63 if rain >= 55 else 80 if rain >= 30 else 1 if high >= 30 else 2
    return _day_record(day, code, high, high - 9, rain, "estimate")


_CACHE: dict[tuple, tuple[float, list[dict]]] = {}
_CACHE_TTL_SECONDS = 600


def get_weather(city: str, start: date, days: int) -> list[dict]:
    """Day-by-day weather for ``days`` days starting on ``start`` (cached 10 min).

    Never raises for network problems: they degrade to historical or seasonal data.
    """
    key = (city, start, days)
    cached = _CACHE.get(key)
    if cached and time.time() - cached[0] < _CACHE_TTL_SECONDS:
        return [dict(d) for d in cached[1]]
    result = _get_weather_uncached(city, start, days)
    _CACHE[key] = (time.time(), result)
    return [dict(d) for d in result]


def _get_weather_uncached(city: str, start: date, days: int) -> list[dict]:
    if city not in CITIES:
        raise ValueError(f"Unknown city: {city}")
    lat, lon = CITIES[city]["lat"], CITIES[city]["lon"]
    requested = [start + timedelta(days=i) for i in range(days)]
    today = date.today()
    horizon = today + timedelta(days=OPEN_METEO_FORECAST_HORIZON_DAYS)

    results: dict[str, dict] = {}
    live_days = [d for d in requested if today <= d <= horizon]
    if live_days:
        try:
            results.update(_fetch_forecast(lat, lon, live_days[0], live_days[-1]))
        except (requests.RequestException, KeyError, ValueError) as exc:
            logger.warning("Open-Meteo forecast failed: %s", exc)

    missing = [d for d in requested if d.isoformat() not in results]
    if missing:
        try:
            results.update(_fetch_historical(lat, lon, missing))
        except (requests.RequestException, KeyError, ValueError) as exc:
            logger.warning("Open-Meteo archive failed: %s", exc)

    return [results.get(d.isoformat()) or _seasonal_estimate(city, d) for d in requested]


def is_rainy(day_weather: dict) -> bool:
    return (day_weather.get("rain_chance") or 0) >= 50 or day_weather.get("icon") in {"rain", "storm"}


def weather_source_note(forecast: list[dict]) -> str:
    sources = {d["source"] for d in forecast}
    if sources == {"forecast"}:
        return "Live forecast from Open-Meteo."
    if "forecast" in sources:
        return "Live Open-Meteo forecast where available; other days use typical conditions from last year."
    if "historical" in sources:
        return "Beyond the 16-day forecast window, so this shows weather from the same dates last year (Open-Meteo archive)."
    return "Open-Meteo was unreachable, so this is a seasonal estimate."
