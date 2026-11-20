"""Data models shared by the planner, the agent and the UI."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date

from pydantic import BaseModel, Field

from .config import CITIES, DAILY_LOCAL_EXPENSE, MAX_DAYS, MIN_DAYS

FLIGHT_PRIORITIES = ["Balanced", "Cheapest", "Fastest"]
HOTEL_PRIORITIES = ["Best value", "Highest rated", "Cheapest"]
TRAVEL_STYLES = list(DAILY_LOCAL_EXPENSE)


@dataclass
class TripRequest:
    """Everything the traveller asked for."""

    origin: str
    destination: str
    start_date: date
    days: int = 3
    travelers: int = 1
    style: str = "Comfort"
    interests: list[str] = field(default_factory=list)
    flight_priority: str = "Balanced"
    hotel_priority: str = "Best value"
    min_stars: int = 1
    max_hotel_price: int | None = None
    amenities: list[str] = field(default_factory=list)
    budget_cap: int | None = None
    include_return: bool = True

    def validate(self) -> None:
        """Raise ``ValueError`` with a user-readable message for bad input."""
        if self.origin not in CITIES:
            raise ValueError(f"Unknown origin '{self.origin}'. Choose one of: {', '.join(CITIES)}.")
        if self.destination not in CITIES:
            raise ValueError(f"Unknown destination '{self.destination}'. Choose one of: {', '.join(CITIES)}.")
        if self.origin == self.destination:
            raise ValueError("Origin and destination must be different cities.")
        if not MIN_DAYS <= self.days <= MAX_DAYS:
            raise ValueError(f"Trip length must be between {MIN_DAYS} and {MAX_DAYS} days.")
        if not 1 <= self.travelers <= 8:
            raise ValueError("Travelers must be between 1 and 8.")
        if self.style not in DAILY_LOCAL_EXPENSE:
            raise ValueError(f"Travel style must be one of: {', '.join(DAILY_LOCAL_EXPENSE)}.")
        if self.flight_priority not in FLIGHT_PRIORITIES:
            raise ValueError(f"Flight priority must be one of: {', '.join(FLIGHT_PRIORITIES)}.")
        if self.hotel_priority not in HOTEL_PRIORITIES:
            raise ValueError(f"Hotel priority must be one of: {', '.join(HOTEL_PRIORITIES)}.")
        if self.budget_cap is not None and self.budget_cap <= 0:
            raise ValueError("Budget must be a positive amount.")

    def to_dict(self) -> dict:
        data = asdict(self)
        data["start_date"] = self.start_date.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "TripRequest":
        data = dict(data)
        data["start_date"] = date.fromisoformat(data["start_date"])
        return cls(**data)


class DayChoice(BaseModel):
    """The agent's pick of places for one day."""

    place_ids: list[str] = Field(default_factory=list, description="Place IDs for this day, in visiting order.")
    theme: str = ""
    notes: str = ""


class AgentChoice(BaseModel):
    """Structured decision produced by the agent (or by the rule-based planner)."""

    summary: str = ""
    outbound_flight_ids: list[str] = Field(default_factory=list)
    return_flight_ids: list[str] = Field(default_factory=list)
    hotel_id: str = ""
    days: list[DayChoice] = Field(default_factory=list)
    reasoning: list[str] = Field(default_factory=list)


class ParsedQuery(BaseModel):
    """Trip details pulled out of a free-text request."""

    origin: str | None = None
    destination: str | None = None
    start_date: str | None = Field(default=None, description="ISO date YYYY-MM-DD")
    days: int | None = None
    travelers: int | None = None
    budget_cap: int | None = Field(default=None, description="Total budget in INR")
    interests: list[str] = Field(default_factory=list)
    style: str | None = None
