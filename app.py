"""Safar: premium Streamlit front end for the agentic travel planner.

Run with:  streamlit run app.py
"""

from __future__ import annotations

import sqlite3
from datetime import date, timedelta

import pandas as pd
import streamlit as st
from ui.destination_map import render_destination_map

from travel_agent import agent, db
from travel_agent.config import CITIES, MAX_DAYS, MIN_DAYS, resolve_llm_settings
from travel_agent.data_loader import (
    DataError,
    available_amenities,
    available_place_types,
    load_flights,
    load_hotels,
    load_places,
)
from travel_agent.formatting import to_json, to_text
from travel_agent.models import FLIGHT_PRIORITIES, HOTEL_PRIORITIES, TRAVEL_STYLES, TripRequest
from travel_agent.planner import plan_trip
from travel_agent.query_parser import parse_query
from ui import components as ui
from ui.styles import CSS

st.set_page_config(page_title="Safar | AI travel planner", page_icon="\u2708\ufe0f", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)

CITY_OPTIONS = sorted(CITIES)
EXAMPLES = [
    "4 days in Goa from Bangalore for 2 people, museums and forts, under 40000",
    "Weekend in Kolkata from Mumbai, love temples and beaches",
    "5 day trip Delhi to Jaipur on a budget",
]


# --------------------------------------------------------------------------
# State
# --------------------------------------------------------------------------
def init_state() -> None:
    defaults = {
        "origin": "Bangalore", "destination": "Goa", "start_date": date.today() + timedelta(days=10),
        "days": 4, "travelers": 2, "style": "Comfort", "interests": [], "flight_priority": "Balanced",
        "hotel_priority": "Best value", "min_stars": 1, "max_hotel_price": 0, "amenities": [],
        "budget_cap": 0, "include_return": True, "nl_text": "", "nl_applied": "", "understood": {},
        "plan": None, "error": None, "viewing_id": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def apply_nl_text(text: str) -> dict:
    """Fill the form from a free-text request. Uses the LLM when configured."""
    parsed = None
    if agent.is_available():
        try:
            parsed = agent.parse_query_with_llm(text, date.today())
        except Exception:  # noqa: BLE001 - fall back to the rule-based parser
            parsed = None
    parsed = parsed or parse_query(text)
    data = parsed.model_dump()

    if data["origin"] in CITIES:
        st.session_state["origin"] = data["origin"]
    if data["destination"] in CITIES:
        st.session_state["destination"] = data["destination"]
    if data["start_date"]:
        try:
            st.session_state["start_date"] = max(date.fromisoformat(data["start_date"]), date.today())
        except ValueError:
            pass
    if data["days"]:
        st.session_state["days"] = max(MIN_DAYS, min(MAX_DAYS, int(data["days"])))
    if data["travelers"]:
        st.session_state["travelers"] = max(1, min(8, int(data["travelers"])))
    if data["budget_cap"]:
        st.session_state["budget_cap"] = int(data["budget_cap"])
    if data["style"] in TRAVEL_STYLES:
        st.session_state["style"] = data["style"]
    valid_types = set(available_place_types())
    interests = [i for i in data["interests"] if i in valid_types]
    if interests:
        st.session_state["interests"] = interests
    return data


def request_plan() -> None:
    """Button callback: apply any new description to the form, then ask for a run."""
    text = st.session_state.get("nl_text", "").strip()
    if text and text != st.session_state.get("nl_applied"):
        st.session_state["understood"] = apply_nl_text(text)
        st.session_state["nl_applied"] = text
    st.session_state["run_requested"] = True


def use_example(text: str) -> None:
    st.session_state["nl_text"] = text
    request_plan()


def build_request() -> TripRequest:
    ss = st.session_state
    return TripRequest(
        origin=ss["origin"], destination=ss["destination"], start_date=ss["start_date"], days=int(ss["days"]),
        travelers=int(ss["travelers"]), style=ss["style"] or "Comfort", interests=list(ss["interests"]),
        flight_priority=ss["flight_priority"] or "Balanced", hotel_priority=ss["hotel_priority"],
        min_stars=int(ss["min_stars"]), max_hotel_price=int(ss["max_hotel_price"]) or None,
        amenities=list(ss["amenities"]), budget_cap=int(ss["budget_cap"]) or None, include_return=bool(ss["include_return"]),
    )


def run_plan() -> None:
    st.session_state["error"] = None
    try:
        request = build_request()
        with st.spinner("Checking flights, hotels, places and the weather..."):
            st.session_state["plan"] = plan_trip(request)
    except ValueError as exc:
        st.session_state["error"] = str(exc)
    except DataError as exc:
        st.session_state["error"] = f"Trip data could not be loaded. {exc}"
    except Exception as exc:  # noqa: BLE001 - never show a stack trace to the traveller
        st.session_state["error"] = f"Something went wrong while planning ({type(exc).__name__}). Try again."


# --------------------------------------------------------------------------
# Sections
# --------------------------------------------------------------------------
def render_banner() -> None:
    settings = resolve_llm_settings()
    label = f"LangChain agent with {settings.model}" if settings.provider else None
    st.markdown(ui.banner(None, label), unsafe_allow_html=True)


def render_search_card() -> None:
    with st.container(key="search"):
        st.text_area(
            "Describe your trip (optional)", key="nl_text", height=84,
            placeholder="e.g. 4 days in Goa from Bangalore for 2 people, museums and forts, under 40000",
        )
        understood = ui.understood_chips(st.session_state["understood"]) if st.session_state["understood"] else ""
        if understood:
            st.markdown(understood, unsafe_allow_html=True)

        c1, c2, c3, c4, c5 = st.columns([1.25, 1.25, 1.1, 0.8, 0.8])
        c1.selectbox("From", CITY_OPTIONS, key="origin")
        c2.selectbox("To", CITY_OPTIONS, key="destination")
        c3.date_input("Start date", key="start_date", min_value=date.today(), format="DD/MM/YYYY")
        c4.number_input("Days", MIN_DAYS, MAX_DAYS, key="days", step=1)
        c5.number_input("Travellers", 1, 8, key="travelers", step=1)

        d1, d2, d3 = st.columns([1.6, 1.3, 1.1])
        d1.multiselect("Interests", available_place_types(), key="interests", placeholder="Any place type")
        with d2:
            st.segmented_control("Travel style", TRAVEL_STYLES, key="style", selection_mode="single")
        d3.number_input("Total budget in \u20b9 (0 for no limit)", 0, 1_000_000, key="budget_cap", step=1000)

        with st.expander("More preferences"):
            e1, e2, e3 = st.columns(3)
            e1.selectbox("Flight priority", FLIGHT_PRIORITIES, key="flight_priority")
            e2.selectbox("Hotel priority", HOTEL_PRIORITIES, key="hotel_priority")
            e3.toggle("Include return flight", key="include_return")
            f1, f2, f3 = st.columns(3)
            f1.slider("Minimum hotel stars", 1, 5, key="min_stars")
            f2.number_input("Max hotel price per night in \u20b9 (0 for no limit)", 0, 100_000, key="max_hotel_price", step=500)
            f3.multiselect("Hotel must have", available_amenities(), key="amenities", placeholder="Any amenities")

        st.button("Plan my trip", type="primary", use_container_width=True, on_click=request_plan)


def render_actions(plan: dict, prefix: str, allow_save: bool = True) -> None:
    dest = plan["route"]["destination"].lower()
    start = plan["request"]["start_date"]
    a, b, c, _ = st.columns([1, 1.2, 1.2, 3])
    if allow_save and a.button("Save trip", key=f"{prefix}_save"):
        try:
            db.save_trip(plan)
            st.toast("Trip saved")
        except (sqlite3.Error, OSError):
            st.warning("Could not save the trip on this machine.")
    b.download_button("Download JSON", to_json(plan), f"safar-{dest}-{start}.json", "application/json", key=f"{prefix}_json")
    c.download_button("Download text", to_text(plan), f"safar-{dest}-{start}.txt", "text/plain", key=f"{prefix}_txt")


def render_plan(plan: dict, prefix: str, allow_save: bool = True) -> None:
    st.markdown(ui.boarding_pass(plan), unsafe_allow_html=True)
    render_actions(plan, prefix, allow_save)

    flight_weather_html = ui.flight_weather_card(plan)
    if flight_weather_html:
        st.markdown(flight_weather_html, unsafe_allow_html=True)

    if plan["warnings"]:
        st.markdown(ui.notices(plan), unsafe_allow_html=True)

    st.markdown(ui.section("Weather", plan["weather_note"]), unsafe_allow_html=True)
    st.markdown(ui.weather_strip(plan), unsafe_allow_html=True)

    left, right = st.columns([1.55, 1], gap="large")
    with left:
        st.markdown(ui.section("Day by day"), unsafe_allow_html=True)
        st.markdown(ui.timeline(plan), unsafe_allow_html=True)
    with right:
        st.markdown(ui.section("Stay and cost"), unsafe_allow_html=True)
        st.markdown(ui.hotel_card(plan), unsafe_allow_html=True)
        st.markdown(ui.budget_card(plan), unsafe_allow_html=True)

    st.markdown(ui.section("Why Safar chose this"), unsafe_allow_html=True)
    st.markdown(ui.reasoning_list(plan), unsafe_allow_html=True)
    with st.expander("How the plan was built"):
        st.markdown(ui.notice(plan["engine"]["note"], "info"), unsafe_allow_html=True)
        st.markdown(ui.trace_table(plan), unsafe_allow_html=True)


def tab_plan() -> None:
    if st.session_state["error"]:
        st.markdown(ui.notice(st.session_state["error"], "error"), unsafe_allow_html=True)
    plan = st.session_state["plan"]
    if plan:
        render_plan(plan, "current")
        return
    st.markdown(ui.empty_state(), unsafe_allow_html=True)
    cols = st.columns(len(EXAMPLES))
    for col, text in zip(cols, EXAMPLES):
        col.button(text, key=f"ex_{text[:12]}", on_click=use_example, args=(text,), use_container_width=True)


def tab_explore() -> None:
    st.markdown(ui.section("Explore the data", "The flights, hotels and places Safar plans from. Filter to see what is available."), unsafe_allow_html=True)
    which = st.segmented_control("Dataset", ["Flights", "Hotels", "Places"], default="Flights", key="explore_set") or "Flights"

    if which == "Flights":
        df = pd.DataFrame(load_flights())
        c1, c2, c3 = st.columns(3)
        src = c1.multiselect("From", CITY_OPTIONS, key="fx_from")
        dst = c2.multiselect("To", CITY_OPTIONS, key="fx_to")
        cap = c3.slider("Max fare in \u20b9", int(df["price"].min()), int(df["price"].max()), int(df["price"].max()), key="fx_price")
        view = df[df["price"] <= cap]
        view = view[view["from"].isin(src)] if src else view
        view = view[view["to"].isin(dst)] if dst else view
        view = view.assign(departs=view["departure_time"].str[11:16], arrives=view["arrival_time"].str[11:16])
        view = view[["flight_id", "airline", "from", "to", "departs", "arrives", "duration_minutes", "price"]]
        st.dataframe(view, hide_index=True, use_container_width=True, column_config={
            "price": st.column_config.NumberColumn("Fare", format="\u20b9%d"),
            "duration_minutes": st.column_config.NumberColumn("Minutes"),
        })
        total = len(df)
    elif which == "Hotels":
        df = pd.DataFrame(load_hotels())
        c1, c2, c3, c4 = st.columns(4)
        cities = c1.multiselect("City", CITY_OPTIONS, key="hx_city")
        stars = c2.slider("Minimum stars", 1, 5, 1, key="hx_stars")
        cap = c3.slider("Max price per night in \u20b9", int(df["price_per_night"].min()), int(df["price_per_night"].max()), int(df["price_per_night"].max()), key="hx_price")
        amen = c4.multiselect("Must have", available_amenities(), key="hx_amen")
        view = df[(df["stars"] >= stars) & (df["price_per_night"] <= cap)]
        view = view[view["city"].isin(cities)] if cities else view
        for a in amen:
            view = view[view["amenities"].apply(lambda items, a=a: a in items)]
        view = view.assign(amenities=view["amenities"].apply(lambda items: ", ".join(items)))
        st.dataframe(view[["hotel_id", "name", "city", "stars", "price_per_night", "amenities"]], hide_index=True, use_container_width=True,
                     column_config={"price_per_night": st.column_config.NumberColumn("Per night", format="\u20b9%d")})
        total = len(df)
    else:
        df = pd.DataFrame(load_places())
        c1, c2, c3 = st.columns(3)
        cities = c1.multiselect("City", CITY_OPTIONS, key="px_city")
        types = c2.multiselect("Type", available_place_types(), key="px_type")
        rating = c3.slider("Minimum rating", 3.0, 5.0, 3.0, 0.1, key="px_rating")
        view = df[df["rating"] >= rating]
        view = view[view["city"].isin(cities)] if cities else view
        view = view[view["type"].isin(types)] if types else view
        st.dataframe(view[["place_id", "name", "city", "type", "rating"]], hide_index=True, use_container_width=True)
        st.markdown("### Explore destination on map")

        map_city = st.selectbox(
            "Choose destination to explore",
            CITY_OPTIONS,
            index=CITY_OPTIONS.index("Goa") if "Goa" in CITY_OPTIONS else 0,
            key="destination_map_city",
        )

        render_destination_map(
            city=map_city,
            selected_types=types or None,
        )
        st.markdown(ui.notice("In this sample file, a place's name and its type do not always agree (for example a name with 'Lake' typed as museum). Safar plans using the type field and shows both."), unsafe_allow_html=True)
        total = len(df)
    st.caption(f"Showing {len(view)} of {total} records")


def tab_saved() -> None:
    st.markdown(ui.section("Saved trips", "Trips you saved on this machine."), unsafe_allow_html=True)
    try:
        trips = db.list_trips()
    except (sqlite3.Error, OSError):
        st.markdown(ui.notice("Saved trips are not available on this machine.", "error"), unsafe_allow_html=True)
        return
    if not trips:
        st.markdown(ui.notice("Nothing saved yet. Plan a trip and choose Save trip.", "info"), unsafe_allow_html=True)
        return
    for trip in trips:
        c1, c2, c3 = st.columns([5, 1, 1])
        c1.markdown(
            f"**{trip['origin']} to {trip['destination']}**  \n"
            f"{ui.short_date(trip['start_date'])}, {trip['trip_days']} days, {trip['travelers']} traveller(s), {ui.money(trip['total_cost'])}"
        )
        if c2.button("Open", key=f"open_{trip['trip_id']}"):
            st.session_state["viewing_id"] = trip["trip_id"]
        if c3.button("Delete", key=f"del_{trip['trip_id']}"):
            db.delete_trip(trip["trip_id"])
            if st.session_state["viewing_id"] == trip["trip_id"]:
                st.session_state["viewing_id"] = None
            st.rerun()
    viewing = st.session_state["viewing_id"]
    if viewing:
        plan = db.load_trip(viewing)
        if plan:
            st.divider()
            render_plan(plan, f"saved{viewing}", allow_save=False)


def tab_how() -> None:
    st.markdown(ui.section("How Safar works", "A LangChain agent decides which tools to call. Code checks everything it says."), unsafe_allow_html=True)
    st.markdown(ui.how_steps(), unsafe_allow_html=True)
    st.markdown(ui.section("The five tools"), unsafe_allow_html=True)
    st.markdown(
        "| Tool | Source | What it does |\n|---|---|---|\n"
        "| Flight search | flights.json | Direct flights, then one-stop connections. Cheapest, fastest or balanced pick |\n"
        "| Hotel recommendation | hotels.json | Filters by city, stars, price and amenities. Highest rated, cheapest or best value |\n"
        "| Places discovery | places.json | Ranks attractions by interest match and rating |\n"
        "| Weather lookup | Open-Meteo API | Live forecast, with last year's weather or a seasonal estimate beyond the forecast window |\n"
        "| Budget estimation | Calculated | Flights, hotel nights and daily food and local travel |"
    )
    st.markdown(ui.section("Good to know"), unsafe_allow_html=True)
    st.markdown(ui.reasoning_list({"reasoning": [
        "The sample flight file covers 25 of the 56 possible routes. When a route is missing, Safar tries a one-stop connection, then shows a clearly labelled estimated fare.",
        "Flights in the sample file have fixed 2025 dates. Safar uses their departure and arrival times and applies them to your travel dates.",
        "Weather is live for the next 16 days. Beyond that it shows the same dates last year from Open-Meteo, or a seasonal estimate if the API cannot be reached.",
        "Without an API key the same tools run under fixed rules. Add ANTHROPIC_API_KEY or OPENAI_API_KEY to a .env file and the LangChain agent takes over the decisions.",
    ]}), unsafe_allow_html=True)


# --------------------------------------------------------------------------
def main() -> None:
    init_state()
    render_banner()
    render_search_card()
    if st.session_state.pop("run_requested", False):
        run_plan()

    t_plan, t_explore, t_saved, t_how = st.tabs(["Trip plan", "Explore data", "Saved trips", "How it works"])
    with t_plan:
        tab_plan()
    with t_explore:
        tab_explore()
    with t_saved:
        tab_saved()
    with t_how:
        tab_how()


main()
