"""Rule-based extraction of trip details from a free-text request.

Used when no LLM is configured, and as a safety net when LLM parsing fails.
"""

from __future__ import annotations

import re
from datetime import date

from .config import CITIES, MAX_DAYS, MIN_DAYS
from .models import ParsedQuery

CITY_ALIASES = {"bengaluru": "Bangalore", "bombay": "Mumbai", "calcutta": "Kolkata", "madras": "Chennai", "new delhi": "Delhi"}
MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], start=1)}
INTEREST_WORDS = {
    "beach": ["beach", "beaches", "sea", "water sports"],
    "temple": ["temple", "temples", "spiritual"],
    "museum": ["museum", "museums", "art"],
    "market": ["market", "markets", "shopping", "bazaar"],
    "park": ["park", "parks", "nature", "garden"],
    "lake": ["lake", "lakes"],
    "fort": ["fort", "forts", "heritage", "history", "historic"],
    "monument": ["monument", "monuments", "heritage", "history", "historic"],
}


def _find_cities(text: str) -> list[tuple[int, str]]:
    lowered = text.lower()
    found = []
    for name in list(CITIES) + list(CITY_ALIASES):
        for match in re.finditer(rf"\b{re.escape(name.lower())}\b", lowered):
            found.append((match.start(), CITY_ALIASES.get(name, name)))
    return sorted(found)


def _parse_cities(text: str) -> tuple[str | None, str | None]:
    """Decide origin and destination from the words just before each city."""
    lowered = text.lower()
    origin = destination = None
    origin_explicit = False
    unassigned: list[str] = []
    for position, city in _find_cities(text):
        prefix = lowered[max(0, position - 15):position]
        if re.search(r"\bfrom\s+$", prefix) and origin is None:
            origin, origin_explicit = city, True
        elif re.search(r"\b(to|in|at|visit|towards|for)\s+$", prefix) and destination is None:
            destination = city
        elif city not in (origin, destination):
            unassigned.append(city)
    for city in unassigned:
        if origin is None and destination is not None and city != destination:
            origin = city
        elif destination is None and origin is not None and city != origin:
            destination = city
        elif origin is None and destination is None:
            origin = city
        elif destination is None and city != origin:
            destination = city
    if origin is not None and destination is None and not origin_explicit:
        origin, destination = None, origin  # a lone city is the destination
    return origin, destination


def _parse_date(text: str, today: date) -> str | None:
    iso = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", text)
    if iso:
        return iso.group(0)
    lowered = text.lower()
    month_pattern = "|".join(MONTHS)
    for pattern, day_first in (
        (rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+(?:of\s+)?({month_pattern})[a-z]*\b", True),
        (rf"\b({month_pattern})[a-z]*\s+(\d{{1,2}})(?:st|nd|rd|th)?\b", False),
    ):
        match = re.search(pattern, lowered)
        if match:
            day, month = (int(match.group(1)), MONTHS[match.group(2)]) if day_first else (int(match.group(2)), MONTHS[match.group(1)])
            try:
                candidate = date(today.year, month, day)
                if candidate < today:
                    candidate = date(today.year + 1, month, day)
                return candidate.isoformat()
            except ValueError:
                return None
    return None


def parse_query(text: str, today: date | None = None) -> ParsedQuery:
    """Best-effort extraction. Unknown fields stay ``None``."""
    today = today or date.today()
    lowered = text.lower()
    origin, destination = _parse_cities(text)

    days = None
    match = re.search(r"\b(\d{1,2})\s*[- ]?\s*(?:day|days|night|nights)\b", lowered)
    if match:
        days = int(match.group(1)) + (1 if "night" in match.group(0) else 0)
        days = max(MIN_DAYS, min(MAX_DAYS, days))
    elif "weekend" in lowered:
        days = 3
    elif "week" in lowered:
        days = 7

    travelers = None
    match = re.search(r"\b(\d{1,2})\s*(?:people|persons|travell?ers|adults|pax|friends)\b", lowered) or re.search(
        r"\bfamily of (\d{1,2})\b", lowered)
    if match:
        travelers = int(match.group(1))
    elif "couple" in lowered or "honeymoon" in lowered:
        travelers = 2
    elif "solo" in lowered:
        travelers = 1

    budget = None
    match = re.search(r"(?:under|below|within|budget(?: of)?|max(?:imum)?|upto|up to)\s*(?:rs\.?|inr|\u20b9)?\s*(\d[\d,]*)\s*(k|thousand|lakh)?", lowered)
    if not match:
        match = re.search(r"(?:rs\.?|inr|\u20b9)\s*(\d[\d,]*)\s*(k|thousand|lakh)?", lowered)
    if not match:
        match = re.search(r"(\d[\d,]*)\s*(k|thousand|lakh)\b(?:\s*(?:rs|inr|rupees))?\s*(?:budget|total|max)", lowered)
    if match:
        amount = int(match.group(1).replace(",", ""))
        suffix = match.group(2)
        amount *= 1000 if suffix in {"k", "thousand"} else 100000 if suffix == "lakh" else 1
        budget = amount if amount >= 1000 else None

    interests = [kind for kind, words in INTEREST_WORDS.items() if any(re.search(rf"\b{w}\b", lowered) for w in words)]
    style = "Budget" if re.search(r"\b(cheap|backpack|budget[- ]friendly|budget trip|on a budget)", lowered) else (
        "Luxury" if re.search(r"\b(luxury|premium|5-star|five star)", lowered) else None)

    return ParsedQuery(
        origin=origin, destination=destination, start_date=_parse_date(text, today), days=days,
        travelers=travelers, budget_cap=budget, interests=interests, style=style,
    )
