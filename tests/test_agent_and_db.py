"""Runs the real LangChain agent graph with a scripted model (no API key, no network)."""

import json
from datetime import date, timedelta

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from travel_agent import agent, db
from travel_agent.models import TripRequest
from travel_agent.planner import plan_trip


class ScriptedToolModel(BaseChatModel):
    """Calls two tools, then answers with a JSON decision."""

    step: int = 0

    @property
    def _llm_type(self) -> str:
        return "scripted"

    def bind_tools(self, tools, **kwargs):
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        self.step += 1
        if self.step == 1:
            message = AIMessage(content="", tool_calls=[
                {"name": "search_flights_tool", "args": {"origin": "Bangalore", "destination": "Goa"}, "id": "c1"},
                {"name": "discover_places_tool", "args": {"city": "Goa"}, "id": "c2"},
            ])
        else:
            tool_text = next(m.content for m in messages if getattr(m, "tool_call_id", "") == "c1")
            flight_id = json.loads(tool_text)["recommended_flight_ids"]
            decision = {
                "summary": "Agent-built Goa trip.", "outbound_flight_ids": flight_id, "return_flight_ids": [],
                "hotel_id": "HOT-DOES-NOT-EXIST",  # must be rejected and replaced by the planner
                "days": [{"place_ids": ["PLC0026"], "theme": "Museums", "notes": "Indoor start"},
                         {"place_ids": ["PLC9999"], "theme": "Invalid", "notes": ""},
                         {"place_ids": [], "theme": "Rest", "notes": ""}],
                "reasoning": ["Cheapest direct flight."],
            }
            message = AIMessage(content="```json\n" + json.dumps(decision) + "\n```")
        return ChatResult(generations=[ChatGeneration(message=message)])


def test_agent_pipeline_verifies_model_output(monkeypatch):
    from travel_agent.config import LLMSettings

    monkeypatch.setattr(agent, "is_available", lambda: True)
    monkeypatch.setattr(agent, "_build_model", lambda: (ScriptedToolModel(), LLMSettings("scripted", "fake")))
    request = TripRequest("Bangalore", "Goa", date.today() + timedelta(days=20), days=3, include_return=False)
    plan = plan_trip(request, use_agent=True)

    assert plan["engine"]["mode"] == "llm-agent"
    assert [s["tool"] for s in plan["trace"]][:2] == ["search_flights", "discover_places"]
    assert plan["hotel"]["hotel_id"] != "HOT-DOES-NOT-EXIST"  # invalid hotel replaced
    assert plan["budget"]["total"] == plan["budget"]["flights"] + plan["budget"]["hotel"] + plan["budget"]["local"]
    # Day plan had an invalid place id, so the planner discarded it and rebuilt the itinerary.
    assert all(a["place_id"] != "PLC9999" for d in plan["itinerary"] for a in d["activities"])


def test_agent_failure_falls_back_to_rules(monkeypatch):
    monkeypatch.setattr(agent, "is_available", lambda: True)

    def boom(*args, **kwargs):
        raise RuntimeError("model unavailable")

    monkeypatch.setattr(agent, "run_agent", boom)
    request = TripRequest("Bangalore", "Goa", date.today() + timedelta(days=20), days=3)
    plan = plan_trip(request, use_agent=True)
    assert plan["engine"]["mode"] == "rule-based" and "failed" in plan["warnings"][0]


def test_saved_trips_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "trips.db")
    plan = plan_trip(TripRequest("Bangalore", "Goa", date.today() + timedelta(days=20)), use_agent=False)
    trip_id = db.save_trip(plan)
    assert db.list_trips()[0]["trip_id"] == trip_id
    assert db.load_trip(trip_id)["title"] == plan["title"]
    db.delete_trip(trip_id)
    assert db.load_trip(trip_id) is None
