from datetime import date, timedelta

import pytest

from travel_agent.formatting import to_json, to_text
from travel_agent.models import TripRequest
from travel_agent.planner import plan_trip


def make_request(**overrides) -> TripRequest:
    base = dict(origin="Bangalore", destination="Goa", start_date=date.today() + timedelta(days=30), days=3)
    base.update(overrides)
    return TripRequest(**base)


def test_plan_has_every_section_from_the_brief():
    plan = plan_trip(make_request(), use_agent=False)
    assert plan["title"].startswith("Your 3-Day Trip to Goa")
    assert plan["flight"]["outbound"] and plan["hotel"]["name"]
    assert len(plan["itinerary"]) == 3 and all(d["weather"] for d in plan["itinerary"])
    assert plan["budget"]["total"] == plan["budget"]["flights"] + plan["budget"]["hotel"] + plan["budget"]["local"]
    assert plan["reasoning"] and plan["trace"]
    text = to_text(plan)
    for heading in ("Flight Selected:", "Hotel Booked:", "Weather:", "Itinerary:", "Total Cost:"):
        assert heading in text
    assert '"budget"' in to_json(plan)


@pytest.mark.parametrize("days", [3, 5, 7])
def test_each_place_used_at_most_once(days):
    plan = plan_trip(make_request(days=days), use_agent=False)
    ids = [a["place_id"] for d in plan["itinerary"] for a in d["activities"] if a["place_id"]]
    assert len(ids) == len(set(ids))
    assert len(plan["itinerary"]) == days


def test_budget_cap_triggers_cheaper_choices():
    loose = plan_trip(make_request(budget_cap=None, flight_priority="Fastest", hotel_priority="Highest rated"), use_agent=False)
    cap = loose["budget"]["total"] - 1500
    tight = plan_trip(make_request(budget_cap=cap, flight_priority="Fastest", hotel_priority="Highest rated"), use_agent=False)
    assert tight["budget"]["total"] < loose["budget"]["total"]


def test_impossible_budget_is_flagged_not_hidden():
    plan = plan_trip(make_request(budget_cap=1000), use_agent=False)
    assert plan["budget"]["status"] == "over" and any("over your" in w for w in plan["warnings"])


def test_estimated_fare_is_warned():
    plan = plan_trip(make_request(origin="Delhi"), use_agent=False)
    assert any("estimate" in w.lower() for w in plan["warnings"])


def test_rainy_days_get_indoor_places(monkeypatch):
    from travel_agent import planner

    def fake_weather(city, start, days):
        return [{"date": (start + timedelta(days=i)).isoformat(), "condition": "Rain" if i == 1 else "Clear sky",
                 "icon": "rain" if i == 1 else "sun", "temp_max": 30, "temp_min": 24,
                 "rain_chance": 90 if i == 1 else 5, "source": "forecast"} for i in range(days)]

    monkeypatch.setattr(planner, "get_weather", fake_weather)
    plan = plan_trip(make_request(destination="Goa", origin="Bangalore", days=4), use_agent=False)
    wet_day = plan["itinerary"][1]
    types = [a["type"] for a in wet_day["activities"] if a["kind"] == "place"]
    assert types and all(t in {"museum", "market", "temple", "monument"} for t in types)


@pytest.mark.parametrize("bad", [
    dict(origin="Goa", destination="Goa"), dict(days=2), dict(days=9), dict(travelers=0), dict(origin="Paris"),
])
def test_invalid_requests_raise(bad):
    with pytest.raises(ValueError):
        plan_trip(make_request(**bad), use_agent=False)
