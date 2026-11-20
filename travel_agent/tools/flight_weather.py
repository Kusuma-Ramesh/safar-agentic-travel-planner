"""Weather-based risk indicators for the selected flight's route endpoints.

This is not airline flight-status tracking. It uses Open-Meteo hourly forecasts
for the departure and arrival cities and reports weather-related conditions only.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
import logging
import time

import requests

from ..config import CITIES, HTTP_TIMEOUT_SECONDS, OPEN_METEO_FORECAST_HORIZON_DAYS, OPEN_METEO_FORECAST_URL
from .weather import _describe

logger = logging.getLogger(__name__)
_CACHE: dict[tuple, tuple[float, dict]] = {}
_CACHE_TTL_SECONDS = 600


def _hour_weather(city: str, when: datetime) -> dict:
    """Return the closest hourly forecast for a city, or an unavailable marker."""
    today = date.today()
    if when.date() < today or when.date() > today + timedelta(days=OPEN_METEO_FORECAST_HORIZON_DAYS):
        return {"available": False, "city": city, "time": when.isoformat(),
                "reason": "Outside the live forecast window; no flight-weather assessment is available."}
    key = (city, when.date().isoformat())
    cached = _CACHE.get(key)
    if cached and time.time() - cached[0] < _CACHE_TTL_SECONDS:
        payload = cached[1]
    else:
        meta = CITIES[city]
        params = {
            "latitude": meta["lat"], "longitude": meta["lon"],
            "hourly": "weather_code,precipitation_probability,wind_speed_10m,wind_gusts_10m,visibility",
            "timezone": "auto", "start_date": when.date().isoformat(), "end_date": when.date().isoformat(),
        }
        try:
            response = requests.get(OPEN_METEO_FORECAST_URL, params=params, timeout=HTTP_TIMEOUT_SECONDS)
            response.raise_for_status()
            payload = response.json()["hourly"]
            _CACHE[key] = (time.time(), payload)
        except (requests.RequestException, KeyError, ValueError, TypeError) as exc:
            logger.warning("Flight weather lookup failed for %s: %s", city, exc)
            return {"available": False, "city": city, "time": when.isoformat(),
                    "reason": "Weather forecast could not be retrieved."}

    times = payload.get("time", [])
    if not times:
        return {"available": False, "city": city, "time": when.isoformat(), "reason": "No hourly forecast returned."}
    target = when.strftime("%Y-%m-%dT%H:00")
    idx = min(range(len(times)), key=lambda i: abs(datetime.fromisoformat(times[i]) - datetime.fromisoformat(target)))
    def val(field):
        values = payload.get(field, [])
        return values[idx] if idx < len(values) else None
    code = val("weather_code")
    label, icon = _describe(code)
    return {
        "available": True, "city": city, "time": times[idx], "condition": label, "icon": icon,
        "precipitation_probability": val("precipitation_probability"),
        "wind_speed_kmh": val("wind_speed_10m"), "wind_gusts_kmh": val("wind_gusts_10m"),
        "visibility_m": val("visibility"), "weather_code": code,
    }


def _risk(readings: list[dict]) -> tuple[str, str]:
    available = [r for r in readings if r.get("available")]
    if not available:
        return "Unavailable", "No live hourly forecast is available for the selected flight times."
    codes = {r.get("weather_code") for r in available}
    rain = max((r.get("precipitation_probability") or 0) for r in available)
    gust = max((r.get("wind_gusts_kmh") or 0) for r in available)
    visibility = min((r.get("visibility_m") for r in available if r.get("visibility_m") is not None), default=None)
    if codes.intersection({65, 82, 95, 96, 99}) or gust >= 70:
        return "High", "Thunderstorm, very heavy rain or strong gusts appear in the forecast window. Check with the airline."
    if rain >= 50 or gust >= 40 or codes.intersection({45, 48, 63, 80, 81}) or (visibility is not None and visibility < 2000):
        return "Moderate", "Rain, wind or reduced visibility may affect airport operations. Recheck closer to departure."
    return "Low", "No major weather signal was detected in the available hourly forecast."


def monitor_selected_flights(origin: str, destination: str, start_date: date, days: int,
                             outbound: dict, returning: dict | None) -> dict:
    """Assess weather near departure and arrival times for selected itinerary legs."""
    legs = []
    for label, option, depart_date in (
        ("Outbound", outbound, start_date),
        ("Return", returning, start_date + timedelta(days=days - 1) if returning else start_date),
    ):
        if not option:
            continue
        depart_dt = datetime.combine(depart_date, datetime.strptime(option["departure"], "%H:%M").time())
        arrive_dt = depart_dt + timedelta(minutes=int(option["duration_minutes"]))
        from_city = origin if label == "Outbound" else destination
        to_city = destination if label == "Outbound" else origin
        readings = [_hour_weather(from_city, depart_dt), _hour_weather(to_city, arrive_dt)]
        level, explanation = _risk(readings)
        legs.append({"leg": label, "from": from_city, "to": to_city, "risk": level,
                     "explanation": explanation, "readings": readings,
                     "is_estimated_flight": bool(option.get("estimated"))})
    levels = [leg["risk"] for leg in legs]
    overall = "High" if "High" in levels else "Moderate" if "Moderate" in levels else "Low" if levels and all(x == "Low" for x in levels) else "Unavailable"
    return {"overall_risk": overall, "legs": legs,
            "disclaimer": "Weather-based indicator only, using city-area forecast coordinates. It does not report actual flight status, delays or cancellations."}
