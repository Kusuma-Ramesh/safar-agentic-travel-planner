"""Trip planning pipeline.

``gather`` runs the tools, ``choose_rule_based`` makes decisions with
deterministic rules, and ``assemble`` turns any decision (from the rules or the
LLM agent) into the final, verified trip plan. Money is always recomputed here,
never taken from model output.
"""

from __future__ import annotations
from .tools.flight_weather import monitor_selected_flights

import time
from dataclasses import dataclass
from datetime import date, timedelta

from .config import CITIES, INDOOR_PLACE_TYPES, OUTDOOR_PLACE_TYPES
from .data_loader import load_hotels
from .models import AgentChoice, DayChoice, TripRequest
from .tools.budget import estimate_budget, rooms_needed
from .tools.flights import explain_flight_choice, pick_flight, search_flights
from .tools.hotels import explain_hotel_choice, pick_hotel, search_hotels
from .tools.places import search_places
from .tools.weather import get_weather, is_rainy, weather_source_note
from .trace import Trace


@dataclass
class Gathered:
    """Raw results from every tool for one trip request."""

    outbound_options: list[dict]
    return_options: list[dict]
    hotels: list[dict]
    places: list[dict]
    weather: list[dict]
    hotel_filter_relaxed: bool = False


# ---------------------------------------------------------------------------
# Step 1: gather data with the tools
# ---------------------------------------------------------------------------
def gather(request: TripRequest, trace: Trace | None = None) -> Gathered:
    trace = trace or Trace()

    started = time.perf_counter()
    outbound = search_flights(request.origin, request.destination)
    trace.record(
        "search_flights",
        {"from": request.origin, "to": request.destination},
        f"{len(outbound)} option(s); cheapest ₹{outbound[0]['price']:,}.",
        started,
    )
    returning: list[dict] = []
    if request.include_return:
        started = time.perf_counter()
        returning = search_flights(request.destination, request.origin)
        trace.record(
            "search_flights",
            {"from": request.destination, "to": request.origin},
            f"{len(returning)} option(s); cheapest ₹{returning[0]['price']:,}.",
            started,
        )

    started = time.perf_counter()
    hotels = search_hotels(request.destination, request.min_stars, request.max_hotel_price, request.amenities)
    relaxed = False
    if not hotels:
        hotels = search_hotels(request.destination)
        relaxed = True
    trace.record(
        "recommend_hotels",
        {"city": request.destination, "min_stars": request.min_stars, "max_price": request.max_hotel_price,
         "amenities": request.amenities},
        f"{len(hotels)} hotel(s)" + (" (filters relaxed: nothing matched)." if relaxed else " match the filters."),
        started,
    )

    started = time.perf_counter()
    places = search_places(request.destination, request.interests)
    trace.record(
        "discover_places",
        {"city": request.destination, "interests": request.interests},
        f"{len(places)} attraction(s); top rated {places[0]['name']} ({places[0]['rating']}).",
        started,
    )

    started = time.perf_counter()
    weather = get_weather(request.destination, request.start_date, request.days)
    trace.record(
        "get_weather",
        {"city": request.destination, "start": request.start_date.isoformat(), "days": request.days},
        weather_source_note(weather),
        started,
    )
    return Gathered(outbound, returning, hotels, places, weather, relaxed)


# ---------------------------------------------------------------------------
# Step 2: decisions
# ---------------------------------------------------------------------------
def _trip_total(request: TripRequest, outbound: dict, returning: dict | None, hotel: dict) -> int:
    return estimate_budget(
        outbound["price"],
        returning["price"] if returning else 0,
        hotel["price_per_night"],
        request.days,
        request.travelers,
        request.style,
    )["total"]

def _optimize_choices_for_budget(
    request: TripRequest,
    data: Gathered,
    outbound: dict,
    returning: dict | None,
    hotel: dict,
) -> tuple[dict, dict | None, dict, bool]:
    """Find the cheapest available combination when the initial choice exceeds budget."""

    if not request.budget_cap:
        return outbound, returning, hotel, False

    current_total = _trip_total(request, outbound, returning, hotel)

    if current_total <= request.budget_cap:
        return outbound, returning, hotel, False

    best = None

    outbound_options = data.outbound_options
    return_options = data.return_options if request.include_return else [None]

    for out in outbound_options:
        for ret in return_options:
            for stay in data.hotels:
                total = _trip_total(request, out, ret, stay)

                candidate = (total, out, ret, stay)

                if best is None or total < best[0]:
                    best = candidate

    if best is None:
        return outbound, returning, hotel, False

    _, best_outbound, best_return, best_hotel = best

    return best_outbound, best_return, best_hotel, True



def choose_rule_based(request: TripRequest, data: Gathered) -> AgentChoice:
    """Pick flights and hotel with the user's priorities, then fit to budget."""
    reasoning: list[str] = []
    outbound = pick_flight(data.outbound_options, request.flight_priority)
    returning = pick_flight(data.return_options, request.flight_priority) if request.include_return else None
    hotel = pick_hotel(data.hotels, request.hotel_priority)


    reasoning.append(explain_flight_choice(outbound, data.outbound_options, request.flight_priority))
    if returning:
        reasoning.append("Return: " + explain_flight_choice(returning, data.return_options, request.flight_priority))
    reasoning.append(explain_hotel_choice(hotel, data.hotels, request.hotel_priority))

    if request.budget_cap and _trip_total(request, outbound, returning, hotel) > request.budget_cap:
        reasoning.append(f"First pick was over the ₹{request.budget_cap:,} budget, so cheaper options were tried.")
        cheapest_hotel = pick_hotel(data.hotels, "Cheapest")
        if _trip_total(request, outbound, returning, cheapest_hotel) < _trip_total(request, outbound, returning, hotel):
            hotel = cheapest_hotel
            reasoning.append(f"Switched hotel to {hotel['name']} (₹{hotel['price_per_night']:,}/night).")
        if _trip_total(request, outbound, returning, hotel) > request.budget_cap:
            outbound = pick_flight(data.outbound_options, "Cheapest")
            returning = pick_flight(data.return_options, "Cheapest") if request.include_return else None
            reasoning.append("Switched to the cheapest available flights.")
        if _trip_total(request, outbound, returning, hotel) > request.budget_cap and data.hotel_filter_relaxed is False:
            all_city_hotels = [h for h in load_hotels() if h["city"] == request.destination]
            fallback = pick_hotel(all_city_hotels, "Cheapest")
            if fallback and fallback["price_per_night"] < hotel["price_per_night"]:
                hotel = fallback
                reasoning.append(f"Relaxed hotel filters and picked {hotel['name']} to save more.")

    return AgentChoice(
        summary="",
        outbound_flight_ids=outbound["flight_ids"],
        return_flight_ids=returning["flight_ids"] if returning else [],
        hotel_id=hotel["hotel_id"],
        days=[],
        reasoning=reasoning,
    )


def _resolve_flight(options: list[dict], ids: list[str], priority: str) -> dict:
    """Find the option the agent named; fall back to the priority pick if it is invalid."""
    for option in options:
        if sorted(option["flight_ids"]) == sorted(ids):
            return option
    return pick_flight(options, priority)


# ---------------------------------------------------------------------------
# Step 3: itinerary
# ---------------------------------------------------------------------------
def _clock_minutes(hhmm: str) -> int:
    return int(hhmm[:2]) * 60 + int(hhmm[3:])

def _flight_arrival_date(
    departure_date: date,
    departure_time: str,
    duration_minutes: int,
) -> date:
    """Calculate the calendar date on which a flight arrives."""

    departure_minutes = _clock_minutes(departure_time)
    arrival_day_offset = (
        departure_minutes + duration_minutes
    ) // (24 * 60)

    return departure_date + timedelta(days=arrival_day_offset)


def _day_slots(index: int, total_days: int, arrival: dict, returning: dict | None) -> list[str]:
    """Which parts of the day are free for sightseeing."""
    arrival_day = arrival.get("arrival_day_offset", 0)
    if index < arrival_day:
        return []
    if index == arrival_day:
        minutes = _clock_minutes(arrival["arrival"])
        slots = ["Afternoon", "Evening"] if minutes < 12 * 60 else ["Evening"] if minutes < 17 * 60 else []
        if index == total_days - 1:
            return slots[:1]
        return slots
    if index == total_days - 1:
        if not returning:
            return ["Morning", "Afternoon"]
        departs = _clock_minutes(returning["departure"])
        return ["Morning", "Afternoon"] if departs >= 18 * 60 else ["Morning"] if departs >= 13 * 60 else []
    return ["Morning", "Afternoon"]


def _place_score(place: dict, rainy: bool) -> tuple:
    """Prioritise selected interests, then consider weather and ratings."""

    score = place["rating"]

    if rainy and place["type"] in OUTDOOR_PLACE_TYPES:
        score -= 1.5

    if rainy and place["type"] in INDOOR_PLACE_TYPES:
        score += 0.3

    return (
        bool(place.get("interest_match")),
        score,
    )

def _activity(slot: str, place: dict, note: str = "") -> dict:
    return {
        "slot": slot,
        "kind": "place",
        "title": place["name"],
        "type": place["type"],
        "rating": place["rating"],
        "place_id": place["place_id"],
        "note": note,
    }


def _rule_based_days(places: list[dict], slots_per_day: list[list[str]], weather: list[dict]) -> list[list[dict]]:
    """Spread places over days; send indoor spots to the rainiest days."""
    counts = [0] * len(slots_per_day)
    remaining = len(places)
    while remaining:
        progressed = False
        for i, slots in enumerate(slots_per_day):
            if remaining and counts[i] < len(slots):
                counts[i] += 1
                remaining -= 1
                progressed = True
        if not progressed:
            break

    pool = list(places)
    rainy_flags = [is_rainy(w) for w in weather]
    assignment: dict[int, list[dict]] = {}
    for i in sorted(range(len(counts)), key=lambda k: (not rainy_flags[k], k)):
        picked = []
        for _ in range(counts[i]):
            best = max(pool, key=lambda p: _place_score(p, rainy_flags[i]))
            pool.remove(best)
            picked.append(best)
        # Outdoor first on dry days (cooler mornings); indoor first on wet days.
        picked.sort(key=lambda p: (p["type"] in OUTDOOR_PLACE_TYPES) == rainy_flags[i])
        assignment[i] = picked

    days = []
    for i, slots in enumerate(slots_per_day):
        activities = []
        for slot, place in zip(slots, assignment.get(i, [])):
            note = ""
            if rainy_flags[i] and place["type"] in INDOOR_PLACE_TYPES:
                note = "Indoor pick for a wetter day."
            activities.append(_activity(slot, place, note))
        days.append(activities)
    return days


def _agent_days(
    choice: AgentChoice,
    places_by_id: dict[str, dict],
    slots_per_day: list[list[str]],
) -> list[list[dict]] | None:
    """Validate AI activities against available sightseeing time slots."""

    if len(choice.days) != len(slots_per_day):
        return None

    used: set[str] = set()
    days = []

    for day, available_slots in zip(choice.days, slots_per_day):

        # Reject sightseeing scheduled when the traveller is unavailable.
        if len(day.place_ids) > len(available_slots):
            return None

        activities = []

        for slot, place_id in zip(available_slots, day.place_ids):
            if place_id not in places_by_id or place_id in used:
                return None

            place = places_by_id[place_id]

            # If matching attractions exist, prioritise them over other categories.
            has_interest_matches = any(
                p.get("interest_match")
                for p in places_by_id.values()
            )

            if has_interest_matches and not place.get("interest_match"):
                return None

            used.add(place_id)
            activities.append(
                _activity(slot, places_by_id[place_id], "")
            )

        days.append(activities)

    return days if used else None
def _fill_unused_slots(
    activity_days: list[list[dict]],
    places: list[dict],
    slots_per_day: list[list[str]],
    weather: list[dict],
) -> list[list[dict]]:
    """Fill unused sightseeing slots without repeating attractions."""

    used = {
        activity["place_id"]
        for day in activity_days
        for activity in day
        if activity.get("place_id")
    }

    remaining = [
        place for place in places
        if place["place_id"] not in used
    ]

    for i, slots in enumerate(slots_per_day):
        rainy = is_rainy(weather[i])

        for slot in slots[len(activity_days[i]):]:
            if not remaining:
                break

            best = max(
                remaining,
                key=lambda place: _place_score(place, rainy),
            )

            remaining.remove(best)

            note = ""
            if rainy and best["type"] in INDOOR_PLACE_TYPES:
                note = "Indoor pick for a wetter day."

            activity_days[i].append(_activity(slot, best, note))

    return activity_days


def _day_theme(activities: list[dict], index: int, total: int, slots: list[str]) -> str:
    types = []
    for activity in activities:
        if activity["kind"] == "place" and activity["type"] not in types:
            types.append(activity["type"])
    base = " and ".join(t.title() for t in types[:2]) if types else ("Open day" if slots else "Travel day")
    if index == 0 and types:
        return f"Arrival: {base}"
    if index == total - 1 and types:
        return f"Last day: {base}"
    return base


def build_itinerary(
    request: TripRequest,
    data: Gathered,
    outbound: dict,
    returning: dict | None,
    choice: AgentChoice,
) -> list[dict]:
    places_by_id = {p["place_id"]: p for p in data.places}
    slots_per_day = [_day_slots(i, request.days, outbound, returning) for i in range(request.days)]

    activity_days = _agent_days(choice, places_by_id, slots_per_day)
    agent_driven = activity_days is not None
    if activity_days is None:
        activity_days = _rule_based_days(data.places, slots_per_day, data.weather)

    itinerary = []
    for i in range(request.days):
        day_date = request.start_date + timedelta(days=i)
        activities = activity_days[i]
        logistics: list[str] = []
        if i == outbound.get("arrival_day_offset", 0):
            logistics.append(
                f"Land in {request.destination} at {outbound['arrival']} ({outbound['airline']}), then check in at the hotel."
            )
        if i < outbound.get("arrival_day_offset", 0):
            logistics.append("Overnight travel. You land on the next day.")
        if i == 0:
            logistics.insert(0, f"Depart {request.origin} at {outbound['departure']}.")
        if i == request.days - 1 and returning:
            return_arrival_date = _flight_arrival_date(
                day_date,
                returning["departure"],
                returning["duration_minutes"],
            )

            logistics.append(
                f"Check out and fly home at {returning['departure']} "
                f"({returning['airline']}), arriving in {request.origin} "
                f"on {return_arrival_date.strftime('%d %b %Y')} "
                f"at {returning['arrival']}."
            )
        elif i == request.days - 1:
            logistics.append("Check out of the hotel.")

        if not activities and slots_per_day[i]:
            activities = [{
                "slot": slots_per_day[i][0],
                "kind": "free",
                "title": "Open day",
                "type": "free",
                "rating": None,
                "place_id": None,
                "note": "Every attraction in the dataset is already planned. Revisit a favourite or explore local food.",
            }]
        elif not activities and not slots_per_day[i]:
            activities = [{
                "slot": "Day",
                "kind": "travel",
                "title": "Travel day",
                "type": "travel",
                "rating": None,
                "place_id": None,
                "note": "Time is taken up by flights and hotel check-in or check-out.",
            }]

        if 0 < i < request.days - 1 and any(a["kind"] == "place" for a in activities):
            activities.append({
                "slot": "Evening",
                "kind": "free",
                "title": "Evening at leisure",
                "type": "free",
                "rating": None,
                "place_id": None,
                "note": "Local food and a relaxed walk.",
            })

        theme = _day_theme(activities, i, request.days, slots_per_day[i])
        notes = ""
        if agent_driven and i < len(choice.days):
            theme = choice.days[i].theme or theme
            notes = choice.days[i].notes
        itinerary.append({
            "day": i + 1,
            "date": day_date.isoformat(),
            "weekday": day_date.strftime("%a"),
            "theme": theme,
            "notes": notes,
            "weather": data.weather[i],
            "activities": activities,
            "logistics": logistics,
        })
    return itinerary


# ---------------------------------------------------------------------------
# Step 4: assemble the final plan
# ---------------------------------------------------------------------------
def _format_range(start: date, days: int) -> str:
    end = start + timedelta(days=days - 1)
    if start.month == end.month:
        return f"{start.strftime('%b')} {start.day}\u2013{end.day}"
    return f"{start.strftime('%b')} {start.day} \u2013 {end.strftime('%b')} {end.day}"


def assemble(
    request: TripRequest,
    data: Gathered,
    choice: AgentChoice,
    engine: dict,
    trace: Trace,
) -> dict:
    outbound = _resolve_flight(data.outbound_options, choice.outbound_flight_ids, request.flight_priority)
    returning = (
        _resolve_flight(data.return_options, choice.return_flight_ids, request.flight_priority)
        if request.include_return
        else None
    )
    hotel = next((h for h in data.hotels if h["hotel_id"] == choice.hotel_id), None) or pick_hotel(
        data.hotels, request.hotel_priority
    )
    outbound, returning, hotel, optimized_for_budget = (
        _optimize_choices_for_budget(
            request,
            data,
            outbound,
            returning,
            hotel,
        )
    )

    budget = estimate_budget(
        outbound["price"],
        returning["price"] if returning else 0,
        hotel["price_per_night"],
        request.days,
        request.travelers,
        request.style,
    )
    trace.record(
        "estimate_budget",
        {"days": request.days, "travelers": request.travelers, "style": request.style},
        f"Total ₹{budget['total']:,}.",
    )
    if request.budget_cap:
        budget["cap"] = request.budget_cap
        budget["difference"] = request.budget_cap - budget["total"]
        budget["status"] = "within" if budget["difference"] >= 0 else "over"
    else:
        budget["cap"], budget["difference"], budget["status"] = None, None, None

    itinerary = build_itinerary(request, data, outbound, returning, choice)
    flight_weather = monitor_selected_flights(
        request.origin,
        request.destination,
        request.start_date,
        request.days,
        outbound,
        returning,
    )

    warnings: list[str] = []
    for label, option in (("Outbound", outbound), ("Return", returning)):
        if option and option.get("estimated"):
            warnings.append(f"{label} fare is an estimate. {option['note']}")
    if data.hotel_filter_relaxed:
        warnings.append("No hotel matched every filter, so the filters were relaxed to show the closest options.")
    if budget["status"] == "over":
        if optimized_for_budget:
            warnings.append(
                f"This plan is ₹{-budget['difference']:,} over your "
                f"₹{request.budget_cap:,} budget even after selecting "
                "the cheapest available combination."
            )
        else:
            warnings.append(
                f"This plan is ₹{-budget['difference']:,} over your "
                f"₹{request.budget_cap:,} budget."
            )
    if any(d["source"] != "forecast" for d in data.weather):
        warnings.append(weather_source_note(data.weather))
    warnings.append(
        "Flight times come from the sample dataset and are applied to your travel dates. Confirm availability before booking."
    )


    reasoning = [
        (
            f"Outbound flight: {outbound['airline']} "
            f"({', '.join(outbound['flight_ids'])}), "
            f"Rs {outbound['price']:,} per traveller."
        )
    ]

    if returning:
        reasoning.append(
            f"Return flight: {returning['airline']} "
            f"({', '.join(returning['flight_ids'])}), "
            f"Rs {returning['price']:,} per traveller."
        )

    reasoning.append(
        f"Hotel: {hotel['name']} ({hotel['stars']}-star), "
        f"Rs {hotel['price_per_night']:,} per night. "
        f"{budget['rooms']} room(s) for {budget['nights']} night(s) "
        f"= Rs {budget['hotel']:,}."
    )

    reasoning.append(
        f"Verified estimated total: flights Rs {budget['flights']:,} "
        f"+ hotel Rs {budget['hotel']:,} "
        f"+ food and local travel Rs {budget['local']:,} "
        f"= Rs {budget['total']:,}."
    )

    if request.budget_cap:
        if budget["status"] == "within":
            reasoning.append(
                f"The plan is Rs {budget['difference']:,} "
                f"within your Rs {request.budget_cap:,} budget."
            )
        else:
            reasoning.append(
                f"The plan exceeds your Rs {request.budget_cap:,} "
                f"budget by Rs {-budget['difference']:,}."
            )

    rainy_days = [
        i + 1 for i, w in enumerate(data.weather) if is_rainy(w)
    ]

    if rainy_days:
        reasoning.append(
            "Rain is likely on Day "
            + ", ".join(map(str, rainy_days))
            + ", so indoor attractions were prioritised where possible."
        )

    reasoning.append(
        f"Budget uses {budget['rooms']} room(s) for "
        f"{budget['nights']} night(s) and "
        f"Rs {budget['daily_local_per_person']:,} per person per day "
        f"for food and local travel."
    )

    summary = choice.summary or (
        f"{request.days} days in {request.destination} from {request.origin}, "
        f"{request.travelers} traveller"
        f"{'s' if request.travelers > 1 else ''}, "
        f"{request.style.lower()} style. Total Rs {budget['total']:,}."
    )

    return {
        "title": (
            f"Your {request.days}-Day Trip to {request.destination} "
            f"({_format_range(request.start_date, request.days)})"
        ),
        "summary": summary,
        "request": request.to_dict(),
        "engine": engine,
        "route": {
            "origin": request.origin,
            "destination": request.destination,
            "origin_code": CITIES[request.origin]["code"],
            "destination_code": CITIES[request.destination]["code"],
        },
        "flight": {
            "outbound": outbound,
            "return": returning,
        },
        "flight_weather": flight_weather,
        "hotel": {
            **hotel,
            "nights": budget["nights"],
            "rooms": budget["rooms"],
            "total": budget["hotel"],
        },
        "weather_note": weather_source_note(data.weather),
        "itinerary": itinerary,
        "budget": budget,
        "reasoning": reasoning,
        "warnings": warnings,
        "trace": trace.steps,
    }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def plan_trip(request: TripRequest, use_agent: bool = True) -> dict:
    """Plan a trip using gathered data and an optional LangChain AI decision."""

    from . import agent

    request.validate()

    # Gather travel data exactly once.
    trace = Trace()
    data = gather(request, trace)

    if use_agent and agent.is_available():
        try:
            choice, engine = agent.run_agent(request, trace, data)
            return assemble(request, data, choice, engine, trace)

        except Exception as exc:
            fallback_note = (
                f"The LLM agent failed ({type(exc).__name__}); "
                "used the rule-based planner instead."
            )

            choice = choose_rule_based(request, data)

            engine = {
                "mode": "rule-based",
                "provider": None,
                "model": None,
                "note": fallback_note,
            }

            plan = assemble(request, data, choice, engine, trace)
            plan["warnings"].insert(0, fallback_note)
            return plan

    choice = choose_rule_based(request, data)

    engine = {
        "mode": "rule-based",
        "provider": None,
        "model": None,
        "note": "No LLM key configured. The same tools ran under deterministic rules.",
    }

    return assemble(request, data, choice, engine, trace)

