from datetime import date

from travel_agent.query_parser import parse_query

TODAY = date(2026, 11, 10)


def test_full_sentence():
    parsed = parse_query("3 day trip from Bangalore to Goa on Feb 12, love beaches and markets under 30000", TODAY)
    assert (parsed.origin, parsed.destination, parsed.days, parsed.budget_cap) == ("Bangalore", "Goa", 3, 30000)
    assert parsed.start_date == "2027-02-12" and set(parsed.interests) == {"beach", "market"}


def test_destination_before_origin_and_aliases():
    parsed = parse_query("a week in Goa from Bengaluru, luxury, 2 lakh budget", TODAY)
    assert (parsed.origin, parsed.destination, parsed.days, parsed.style) == ("Bangalore", "Goa", 7, "Luxury")


def test_lone_city_is_destination():
    assert parse_query("explore Hyderabad", TODAY).destination == "Hyderabad"
    assert parse_query("explore Hyderabad", TODAY).origin is None


def test_couple_and_k_suffix():
    parsed = parse_query("weekend in Jaipur from Mumbai for a couple, 15k budget", TODAY)
    assert parsed.travelers == 2 and parsed.budget_cap == 15000 and parsed.style is None
