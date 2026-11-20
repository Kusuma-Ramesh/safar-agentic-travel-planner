"""Human-readable and JSON renderings of a trip plan."""

from __future__ import annotations

import json
from datetime import date


def _flight_line(option: dict) -> str:
    kind = "estimated fare" if option.get("estimated") else "direct" if option["stops"] == 0 else f"1 stop via {option['via']}"
    return f"{option['airline']} (\u20b9{option['price']:,}) \u2013 departs {option['from']} at {option['departure']}, arrives {option['arrival']} [{kind}]"


def to_json(plan: dict) -> str:
    return json.dumps(plan, indent=2, ensure_ascii=False, default=str)


def to_text(plan: dict) -> str:
    """Plain-text itinerary in the layout used by the project brief."""
    flight, budget, hotel = plan["flight"], plan["budget"], plan["hotel"]
    lines = [plan["title"], "=" * len(plan["title"]), "", plan["summary"], "", "Flight Selected:",
             f"- {_flight_line(flight['outbound'])}"]
    if flight["return"]:
        lines.append(f"- Return: {_flight_line(flight['return'])}")
    lines += ["", "Hotel Booked:",
              f"- {hotel['name']} (\u20b9{hotel['price_per_night']:,}/night, {hotel['stars']}-star, {', '.join(hotel['amenities'])})",
              "", "Weather:"]
    for day in plan["itinerary"]:
        w = day["weather"]
        temp = f" ({w['temp_max']}\u00b0C)" if w["temp_max"] is not None else ""
        lines.append(f"- Day {day['day']}: {w['condition']}{temp}")
    lines += ["", "Itinerary:"]
    for day in plan["itinerary"]:
        picks = [a["title"] for a in day["activities"] if a["kind"] == "place"] or [day["activities"][0]["title"]]
        lines.append(f"Day {day['day']} ({day['weekday']} {date.fromisoformat(day['date']).strftime('%b %d')}): {', '.join(picks)}")
    lines += ["", "Estimated Total Budget:",
              f"- Flights: \u20b9{budget['flights']:,}",
              f"- Hotel: \u20b9{budget['hotel']:,}",
              f"- Food & Travel: \u20b9{budget['local']:,}",
              "-" * 37, f"Total Cost: \u20b9{budget['total']:,}"]
    if budget["status"]:
        lines.append(
            f"Budget cap \u20b9{budget['cap']:,}: "
            + (f"\u20b9{budget['difference']:,} to spare" if budget["status"] == "within" else f"\u20b9{-budget['difference']:,} over")
        )
    if plan["reasoning"]:
        lines += ["", "Why we chose this:"] + [f"- {r}" for r in plan["reasoning"]]
    if plan["warnings"]:
        lines += ["", "Notes:"] + [f"- {w}" for w in plan["warnings"]]
    return "\n".join(lines)
