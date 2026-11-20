"""Flight search: direct flights first, one-stop connections as a fallback."""

from __future__ import annotations

from datetime import datetime

from ..data_loader import load_flights

# Minimum layover for a one-stop connection.
MIN_LAYOVER_MINUTES = 60
# Longer waits are not offered as a sensible connection.
MAX_LAYOVER_MINUTES = 10 * 60


def _time_of_day(iso: str) -> str:
    return datetime.fromisoformat(iso).strftime("%H:%M")


def _direct_option(flight: dict) -> dict:
    return {
        "type": "direct",
        "flight_ids": [flight["flight_id"]],
        "airline": flight["airline"],
        "from": flight["from"],
        "to": flight["to"],
        "departure": _time_of_day(flight["departure_time"]),
        "arrival": _time_of_day(flight["arrival_time"]),
        "duration_minutes": flight["duration_minutes"],
        "price": flight["price"],
        "stops": 0,
        "via": None,
    }


def _connecting_options(source: str, destination: str) -> list[dict]:
    """Pair legs source->hub and hub->destination with a workable layover.

    The sample dataset covers different dates per flight, so layovers are worked
    out from clock times only: the wait is the gap between landing and the next
    departure, rolling over to the next day when needed.
    """
    flights = load_flights()
    first_legs = [f for f in flights if f["from"] == source and f["to"] != destination]
    options = []
    for first in first_legs:
        for second in flights:
            if second["from"] != first["to"] or second["to"] != destination:
                continue
            land = datetime.fromisoformat(first["arrival_time"]).time()
            depart = datetime.fromisoformat(second["departure_time"]).time()
            layover = (depart.hour * 60 + depart.minute) - (land.hour * 60 + land.minute)
            if layover < MIN_LAYOVER_MINUTES:
                layover += 24 * 60  # overnight connection
            if layover > MAX_LAYOVER_MINUTES:
                continue
            options.append(
                {
                    "type": "one-stop",
                    "flight_ids": [first["flight_id"], second["flight_id"]],
                    "airline": f"{first['airline']} + {second['airline']}",
                    "from": source,
                    "to": destination,
                    "departure": _time_of_day(first["departure_time"]),
                    "arrival": _time_of_day(second["arrival_time"]),
                    "duration_minutes": first["duration_minutes"] + layover + second["duration_minutes"],
                    "price": first["price"] + second["price"],
                    "stops": 1,
                    "via": first["to"],
                }
            )
    return options


def _estimated_option(source: str, destination: str) -> dict:
    """Last-resort estimate when the dataset has no way to fly this route.

    Uses the reverse route's average fare when it exists, otherwise the average
    fare of the whole dataset. Always flagged ``estimated`` so the UI can say so.
    """
    flights = load_flights()
    reverse = [f for f in flights if f["from"] == destination and f["to"] == source]
    basis = reverse or flights
    price = round(sum(f["price"] for f in basis) / len(basis), -1)
    duration = round(sum(f["duration_minutes"] for f in basis) / len(basis) / 30) * 30
    return {
        "type": "estimated",
        "flight_ids": [],
        "airline": "Estimated fare",
        "from": source,
        "to": destination,
        "departure": "09:00",
        "arrival": f"{(9 * 60 + duration) // 60 % 24:02d}:{(9 * 60 + duration) % 60:02d}",
        "duration_minutes": int(duration),
        "price": int(price),
        "stops": 0,
        "via": None,
        "estimated": True,
        "note": (
            "No flight on this route in the dataset. Fare is the average of "
            + ("the reverse route" if reverse else "all dataset flights")
            + "; check live prices before booking."
        ),
    }


def search_flights(source: str, destination: str, allow_connections: bool = True) -> list[dict]:
    """Flight options from ``source`` to ``destination``, cheapest first.

    Falls back in order: direct flights, one-stop connections, then a flagged
    estimate so a trip can still be budgeted when the dataset has a gap.
    """
    if source == destination:
        raise ValueError("Origin and destination must be different cities.")
    direct = [_direct_option(f) for f in load_flights() if f["from"] == source and f["to"] == destination]
    options = direct or (_connecting_options(source, destination) if allow_connections else [])
    options = options or [_estimated_option(source, destination)]
    for option in options:
        departure_minutes = int(option["departure"][:2]) * 60 + int(option["departure"][3:])
        option["arrival_day_offset"] = (departure_minutes + option["duration_minutes"]) // (24 * 60)
    return sorted(options, key=lambda o: (o["price"], o["duration_minutes"]))


def pick_flight(options: list[dict], priority: str = "Balanced") -> dict | None:
    """Select the best option for a priority: Cheapest, Fastest or Balanced."""
    if not options:
        return None
    if priority == "Cheapest":
        return min(options, key=lambda o: (o["price"], o["duration_minutes"]))
    if priority == "Fastest":
        return min(options, key=lambda o: (o["duration_minutes"], o["price"]))
    # Balanced: normalise price and duration, weight price slightly higher.
    prices = [o["price"] for o in options]
    durations = [o["duration_minutes"] for o in options]

    def score(option: dict) -> float:
        price_part = (option["price"] - min(prices)) / ((max(prices) - min(prices)) or 1)
        time_part = (option["duration_minutes"] - min(durations)) / ((max(durations) - min(durations)) or 1)
        return 0.6 * price_part + 0.4 * time_part

    return min(options, key=score)


def explain_flight_choice(chosen: dict, options: list[dict], priority: str) -> str:
    cheapest = min(options, key=lambda o: o["price"])
    fastest = min(options, key=lambda o: o["duration_minutes"])
    if chosen.get("estimated"):
        return chosen["note"]
    kind = "direct flight" if chosen["stops"] == 0 else f"one-stop via {chosen['via']}"
    note = f"Chose {chosen['airline']} ({kind}, ₹{chosen['price']:,}) on a {priority.lower()} priority."
    if chosen is not cheapest and chosen["price"] > cheapest["price"]:
        note += f" The cheapest option is ₹{cheapest['price']:,} but takes {cheapest['duration_minutes']} min."
    if chosen is not fastest and chosen["duration_minutes"] > fastest["duration_minutes"]:
        note += f" The fastest is {fastest['duration_minutes']} min at ₹{fastest['price']:,}."
    return note
