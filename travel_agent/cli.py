"""Command-line interface: ``python -m travel_agent.cli "3 days Delhi to Goa under 25000"``."""

from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta

from .formatting import to_json, to_text
from .models import TripRequest
from .planner import plan_trip
from .query_parser import parse_query


def build_request(args: argparse.Namespace) -> TripRequest:
    parsed = parse_query(args.query) if args.query else None
    origin = args.origin or (parsed.origin if parsed else None)
    destination = args.destination or (parsed.destination if parsed else None)
    if not origin or not destination:
        raise ValueError("Say where you are flying from and to, e.g. 'Delhi to Goa', or use --origin/--destination.")
    start = args.start or (parsed.start_date if parsed else None)
    return TripRequest(
        origin=origin,
        destination=destination,
        start_date=date.fromisoformat(start) if start else date.today() + timedelta(days=21),
        days=args.days or (parsed.days if parsed and parsed.days else 3),
        travelers=args.travelers or (parsed.travelers if parsed and parsed.travelers else 1),
        style=args.style or (parsed.style if parsed and parsed.style else "Comfort"),
        interests=parsed.interests if parsed else [],
        budget_cap=args.budget or (parsed.budget_cap if parsed else None),
        include_return=not args.one_way,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Agentic AI travel planner")
    parser.add_argument("query", nargs="?", help="Free-text request, e.g. '3 days in Goa from Bangalore, love beaches'")
    parser.add_argument("--origin")
    parser.add_argument("--destination")
    parser.add_argument("--start", help="Start date, YYYY-MM-DD")
    parser.add_argument("--days", type=int)
    parser.add_argument("--travelers", type=int)
    parser.add_argument("--style", choices=["Budget", "Comfort", "Luxury"])
    parser.add_argument("--budget", type=int, help="Total budget in INR")
    parser.add_argument("--one-way", action="store_true")
    parser.add_argument("--json", action="store_true", help="Print the full plan as JSON")
    parser.add_argument("--no-agent", action="store_true", help="Skip the LLM agent and use rule-based planning")
    args = parser.parse_args(argv)

    try:
        plan = plan_trip(build_request(args), use_agent=not args.no_agent)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    print(to_json(plan) if args.json else to_text(plan))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
