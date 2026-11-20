"""LangChain tool wrappers around the plain-Python tools.

Each tool returns a compact JSON string, which is what the model reads. Errors
are returned as ``{"error": ...}`` so the agent can recover instead of crashing.
"""

from __future__ import annotations

import json
from datetime import date

from langchain_core.tools import tool

from ..tools.budget import estimate_budget
from ..tools.flights import pick_flight, search_flights
from ..tools.hotels import pick_hotel, search_hotels
from ..tools.places import search_places
from ..tools.weather import get_weather


def _json(payload) -> str:
    return json.dumps(payload, ensure_ascii=False)


def _csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@tool
def search_flights_tool(origin: str, destination: str, priority: str = "Balanced") -> str:
    """Find flights between two Indian cities from the flights dataset.

    Returns every option (direct, one-stop, or a flagged estimate when the route
    is missing) plus the recommended one. priority is Cheapest, Fastest or Balanced.
    Each option has flight_ids, airline, departure, arrival, duration_minutes, price.
    """
    try:
        options = search_flights(origin, destination)
        best = pick_flight(options, priority)
        return _json({"options": options[:6], "recommended_flight_ids": best["flight_ids"]})
    except ValueError as exc:
        return _json({"error": str(exc)})


@tool
def recommend_hotels_tool(
    city: str,
    min_stars: int = 1,
    max_price_per_night: int = 0,
    amenities: str = "",
    priority: str = "Best value",
) -> str:
    """Find hotels in a city. Filters: min_stars (1-5), max_price_per_night in INR
    (0 means no limit) and amenities as a comma-separated list (wifi, pool, gym,
    breakfast, spa, parking). priority is Best value, Highest rated or Cheapest.
    Returns matching hotels (hotel_id, name, stars, price_per_night) and the recommended hotel_id.
    """
    hotels = search_hotels(city, min_stars, max_price_per_night or None, _csv(amenities))
    if not hotels:
        return _json({"hotels": [], "recommended_hotel_id": None, "note": "No hotel matched. Relax the filters."})
    best = pick_hotel(hotels, priority)
    return _json({"hotels": hotels, "recommended_hotel_id": best["hotel_id"]})


@tool
def discover_places_tool(city: str, interests: str = "", min_rating: float = 0.0) -> str:
    """List attractions in a city ranked by interest match and rating.

    interests is a comma-separated list of place types: park, market, museum,
    temple, lake, fort, beach, monument. Returns place_id, name, type, rating.
    """
    places = search_places(city, _csv(interests), min_rating)
    return _json({"places": places})


@tool
def get_weather_tool(city: str, start_date: str, days: int) -> str:
    """Get the day-by-day weather for a city using the free Open-Meteo API.

    start_date is YYYY-MM-DD. Returns condition, temp_max, temp_min and rain_chance
    for each day. Use it to put indoor activities on rainy days.
    """
    try:
        return _json({"days": get_weather(city, date.fromisoformat(start_date), int(days))})
    except ValueError as exc:
        return _json({"error": str(exc)})


@tool
def estimate_budget_tool(
    outbound_price: int,
    return_price: int,
    hotel_price_per_night: int,
    days: int,
    travelers: int = 1,
    style: str = "Comfort",
) -> str:
    """Estimate total trip cost in INR: flights + hotel + daily food and local travel.

    style is Budget, Comfort or Luxury. Prices are per person for flights and
    per room per night for the hotel.
    """
    try:
        return _json(estimate_budget(outbound_price, return_price, hotel_price_per_night, days, travelers, style))
    except ValueError as exc:
        return _json({"error": str(exc)})


ALL_TOOLS = [
    search_flights_tool,
    recommend_hotels_tool,
    discover_places_tool,
    get_weather_tool,
    estimate_budget_tool,
]
