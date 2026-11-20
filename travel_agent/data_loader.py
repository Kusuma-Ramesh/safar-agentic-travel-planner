"""Loading and validating the flights, hotels and places JSON datasets."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

from .config import DATA_DIR

logger = logging.getLogger(__name__)

REQUIRED_FIELDS = {
    "flights": {"flight_id", "airline", "from", "to", "departure_time", "arrival_time", "price"},
    "hotels": {"hotel_id", "name", "city", "stars", "price_per_night", "amenities"},
    "places": {"place_id", "name", "city", "type", "rating"},
}


class DataError(RuntimeError):
    """Raised when a dataset is missing or malformed."""


def _read_json(path: Path) -> list[dict[str, Any]]:
    try:
        with path.open(encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError as exc:
        raise DataError(f"Dataset not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise DataError(f"Dataset {path.name} is not valid JSON: {exc}") from exc
    if not isinstance(data, list):
        raise DataError(f"Dataset {path.name} must contain a JSON list.")
    return data


def _validate(name: str, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Drop records with missing fields instead of failing the whole app."""
    required = REQUIRED_FIELDS[name]
    clean = []
    for record in records:
        if required <= record.keys():
            clean.append(record)
        else:
            logger.warning("Skipping malformed %s record: %s", name, record)
    if not clean:
        raise DataError(f"No valid records in {name}.json")
    return clean


@lru_cache(maxsize=1)
def load_flights() -> list[dict[str, Any]]:
    """Flights with a parsed duration in minutes added to each record."""
    flights = _validate("flights", _read_json(DATA_DIR / "flights.json"))
    for flight in flights:
        dep = datetime.fromisoformat(flight["departure_time"])
        arr = datetime.fromisoformat(flight["arrival_time"])
        flight["duration_minutes"] = int((arr - dep).total_seconds() // 60)
    return flights


@lru_cache(maxsize=1)
def load_hotels() -> list[dict[str, Any]]:
    return _validate("hotels", _read_json(DATA_DIR / "hotels.json"))


@lru_cache(maxsize=1)
def load_places() -> list[dict[str, Any]]:
    return _validate("places", _read_json(DATA_DIR / "places.json"))
@lru_cache(maxsize=1)
def load_place_coordinates() -> dict[str, dict[str, float]]:
    """Load and validate geographical coordinates indexed by place ID."""
    records = _read_json(DATA_DIR / "place_coordinates.json")
    coordinates = {}

    for record in records:
        place_id = record.get("place_id")
        lat = record.get("lat")
        lon = record.get("lon")

        if not isinstance(place_id, str) or not place_id:
            logger.warning("Skipping coordinate record with invalid place_id: %s", record)
            continue

        if place_id in coordinates:
            logger.warning("Skipping duplicate coordinate record: %s", place_id)
            continue

        if (
            isinstance(lat, bool) or not isinstance(lat, (int, float))
            or isinstance(lon, bool) or not isinstance(lon, (int, float))
            or not (-90 <= lat <= 90)
            or not (-180 <= lon <= 180)
        ):
            logger.warning("Skipping invalid coordinates for %s", place_id)
            continue

        coordinates[place_id] = {
            "lat": float(lat),
            "lon": float(lon),
        }

    if not coordinates:
        raise DataError("No valid attraction coordinates found.")

    return coordinates


def available_cities() -> list[str]:
    """Cities that appear in the hotel and place datasets."""
    return sorted({h["city"] for h in load_hotels()} & {p["city"] for p in load_places()})


def available_place_types() -> list[str]:
    return sorted({p["type"] for p in load_places()})


def available_amenities() -> list[str]:
    return sorted({a for h in load_hotels() for a in h["amenities"]})
