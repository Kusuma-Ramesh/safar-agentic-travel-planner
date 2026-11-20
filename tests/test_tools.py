from datetime import date, timedelta

import pytest
import requests

from travel_agent.tools import weather
from travel_agent.tools.budget import estimate_budget
from travel_agent.tools.flights import pick_flight, search_flights
from travel_agent.tools.hotels import pick_hotel, search_hotels
from travel_agent.tools.places import search_places


def test_direct_flights_sorted_cheapest_first():
    options = search_flights("Bangalore", "Goa")
    assert options and all(o["type"] == "direct" for o in options)
    assert [o["price"] for o in options] == sorted(o["price"] for o in options)


def test_flight_priorities_differ():
    options = search_flights("Bangalore", "Goa")
    assert pick_flight(options, "Cheapest")["price"] == min(o["price"] for o in options)
    assert pick_flight(options, "Fastest")["duration_minutes"] == min(o["duration_minutes"] for o in options)


def test_missing_route_falls_back_to_flagged_estimate():
    option = search_flights("Delhi", "Goa")[0]
    assert option["type"] == "estimated" and option["estimated"] is True


def test_same_city_rejected():
    with pytest.raises(ValueError):
        search_flights("Goa", "Goa")


def test_hotel_filters():
    hotels = search_hotels("Goa", min_stars=4, max_price_per_night=6000, required_amenities=["wifi"])
    assert all(h["stars"] >= 4 and h["price_per_night"] <= 6000 and "wifi" in h["amenities"] for h in hotels)
    assert pick_hotel(hotels, "Cheapest")["price_per_night"] == min(h["price_per_night"] for h in hotels)


def test_places_rank_interest_first():
    places = search_places("Goa", interests=["market"])
    assert places[0]["type"] == "market" and places[0]["interest_match"]


def test_budget_math_matches_brief_example():
    # Brief: Rs 4800 flight, Rs 3200 x 2 nights hotel, Rs 2500 food and travel = 13,700.
    budget = estimate_budget(4800, 0, 3200, days=3, travelers=1, style="Comfort")
    assert budget["flights"] == 4800 and budget["hotel"] == 6400
    assert budget["total"] == 4800 + 6400 + budget["local"]


def test_budget_scales_with_travelers_and_rooms():
    budget = estimate_budget(1000, 1000, 2000, days=3, travelers=3, style="Budget")
    assert budget["rooms"] == 2 and budget["hotel"] == 2000 * 2 * 2 and budget["flights"] == 6000


def test_weather_falls_back_to_seasonal_estimate_offline():
    days = weather.get_weather("Goa", date.today() + timedelta(days=5), 3)
    assert len(days) == 3 and all(d["source"] == "estimate" for d in days)


def test_weather_parses_open_meteo_forecast(monkeypatch):
    start = date.today() + timedelta(days=2)
    payload = {"daily": {
        "time": [(start + timedelta(days=i)).isoformat() for i in range(2)],
        "weather_code": [0, 63], "temperature_2m_max": [31.2, 28.7],
        "temperature_2m_min": [24.0, 23.1], "precipitation_probability_max": [5, 80],
    }}

    class Response:
        def raise_for_status(self): ...
        def json(self): return payload

    monkeypatch.setattr(requests, "get", lambda *a, **k: Response())
    days = weather.get_weather("Goa", start, 2)
    assert [d["source"] for d in days] == ["forecast", "forecast"]
    assert days[0]["condition"] == "Clear sky" and days[1]["icon"] == "rain" and weather.is_rainy(days[1])
