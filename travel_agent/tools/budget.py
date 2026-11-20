"""Budget estimation: flights + hotel + daily local spend."""

from __future__ import annotations

import math

from ..config import DAILY_LOCAL_EXPENSE, GUESTS_PER_ROOM


def rooms_needed(travelers: int) -> int:
    return max(1, math.ceil(travelers / GUESTS_PER_ROOM))


def estimate_budget(
    outbound_price: int,
    return_price: int,
    hotel_price_per_night: int,
    days: int,
    travelers: int = 1,
    style: str = "Comfort",
) -> dict:
    """Itemised trip cost in INR.

    * Flights are priced per traveller.
    * Hotel nights = days - 1, one room per two guests.
    * Food & local travel is a per-person daily allowance by travel style.
    """
    if days < 1 or travelers < 1:
        raise ValueError("days and travelers must be at least 1")
    if style not in DAILY_LOCAL_EXPENSE:
        raise ValueError(f"Unknown travel style: {style}")

    nights = max(days - 1, 0)
    rooms = rooms_needed(travelers)
    flights_total = (outbound_price + return_price) * travelers
    hotel_total = hotel_price_per_night * nights * rooms
    local_total = DAILY_LOCAL_EXPENSE[style] * days * travelers
    total = flights_total + hotel_total + local_total
    return {
        "flights": flights_total,
        "hotel": hotel_total,
        "local": local_total,
        "total": total,
        "per_person": round(total / travelers),
        "nights": nights,
        "rooms": rooms,
        "travelers": travelers,
        "daily_local_per_person": DAILY_LOCAL_EXPENSE[style],
    }
