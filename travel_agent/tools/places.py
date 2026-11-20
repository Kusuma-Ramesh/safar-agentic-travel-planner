"""Places discovery: rank attractions by rating and interest match."""

from __future__ import annotations

from collections.abc import Iterable

from ..data_loader import load_places


def search_places(city: str, interests: Iterable[str] = (), min_rating: float = 0.0) -> list[dict]:
    """Attractions in ``city`` ranked by interest match, then rating.

    Each result carries ``interest_match`` so callers can explain the ranking.
    """
    wanted = {i.lower() for i in interests}
    results = []
    for place in load_places():
        if place["city"] != city or place["rating"] < min_rating:
            continue
        results.append({**place, "interest_match": place["type"].lower() in wanted})
    return sorted(results, key=lambda p: (not p["interest_match"], -p["rating"], p["name"]))
