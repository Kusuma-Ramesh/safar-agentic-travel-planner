"""Headless run of the Streamlit app with Streamlit's AppTest."""

from pathlib import Path

from streamlit.testing.v1 import AppTest


def run_app() -> AppTest:
    at = AppTest.from_file(str(Path(__file__).resolve().parent.parent / "app.py"), default_timeout=60)
    at.run()
    return at


def test_app_loads_without_errors():
    at = run_app()
    assert not at.exception
    assert any("Plan my trip" in b.label for b in at.button)


def test_plan_from_form_and_from_text():
    at = run_app()
    at.button[[b.label for b in at.button].index("Plan my trip")].click().run()
    assert not at.exception and at.session_state["plan"]["route"]["destination"] == "Goa"

    at.text_area(key="nl_text").set_value("3 days in Jaipur from Mumbai for a couple under 40000").run()
    at.button[[b.label for b in at.button].index("Plan my trip")].click().run()
    plan = at.session_state["plan"]
    assert not at.exception
    assert (plan["route"]["origin"], plan["route"]["destination"], plan["request"]["days"]) == ("Mumbai", "Jaipur", 3)
    assert plan["request"]["travelers"] == 2 and plan["request"]["budget_cap"] == 40000


def test_same_city_shows_friendly_error():
    at = run_app()
    at.selectbox(key="destination").set_value("Bangalore").run()
    at.button[[b.label for b in at.button].index("Plan my trip")].click().run()
    assert not at.exception and "different cities" in at.session_state["error"]
