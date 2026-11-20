"""Hotel recommendation: filter by city, stars, price and amenities, then rank."""

from __future__ import annotations

from collections.abc import Iterable

from ..data_loader import load_hotels


def search_hotels(
    city: str,
    min_stars: int = 1,
    max_price_per_night: int | None = None,
    required_amenities: Iterable[str] = (),
) -> list[dict]:
    """Hotels in ``city`` that satisfy every filter."""
    required = {a.lower() for a in required_amenities}
    results = []
    for hotel in load_hotels():
        if hotel["city"] != city or hotel["stars"] < min_stars:
            continue
        if max_price_per_night is not None and hotel["price_per_night"] > max_price_per_night:
            continue
        if not required <= {a.lower() for a in hotel["amenities"]}:
            continue
        results.append(hotel)
    return results


def _value_score(hotel: dict) -> float:
    """Stars and amenity count per thousand rupees: higher is better value."""
    quality = hotel["stars"] + 0.25 * len(hotel["amenities"])
    return quality / (hotel["price_per_night"] / 1000)


def pick_hotel(options: list[dict], priority: str = "Best value") -> dict | None:
    """Select a hotel: ``Highest rated``, ``Cheapest`` or ``Best value``."""
    if not options:
        return None
    if priority == "Highest rated":
        return max(options, key=lambda h: (h["stars"], len(h["amenities"]), -h["price_per_night"]))
    if priority == "Cheapest":
        return min(options, key=lambda h: (h["price_per_night"], -h["stars"]))
    return max(options, key=_value_score)


def explain_hotel_choice(chosen: dict, options: list[dict], priority: str) -> str:
    note = (
        f"Chose {chosen['name']} ({chosen['stars']}-star, ₹{chosen['price_per_night']:,}/night) "
        f"from {len(options)} matching hotel(s) on a '{priority.lower()}' priority."
    )
    cheaper = [h for h in options if h["price_per_night"] < chosen["price_per_night"]]
    if cheaper:
        cheapest = min(cheaper, key=lambda h: h["price_per_night"])
        note += f" {cheapest['name']} is cheaper at ₹{cheapest['price_per_night']:,}/night ({cheapest['stars']}-star)."
    return note
