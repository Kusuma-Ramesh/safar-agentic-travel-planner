"""The LangChain agent: reads the request, calls tools, returns a structured decision.

The agent is a tool-calling (ReAct-style) loop built with ``langchain.agents.create_agent``.
It decides which tools to call and in what order. Its final answer is a JSON
``AgentChoice``; the planner then verifies every ID and recomputes all prices.
"""

from __future__ import annotations

import json
import re
from datetime import date

from .config import resolve_llm_settings
from .models import AgentChoice, ParsedQuery, TripRequest
from .tools.lc_tools import ALL_TOOLS
from .trace import Trace


SYSTEM_PROMPT = """You are an expert Indian domestic travel planning agent.
You must use the available tools to obtain trip information. Never invent
flight IDs, hotel IDs, place IDs, or prices.

Execute these steps:
1. Call search_flights_tool for the outbound journey.
2. If a return is requested, call search_flights_tool for the return journey.
3. Call recommend_hotels_tool once for the destination using the traveller's filters.
4. Call discover_places_tool once for the destination using the traveller's interests.
5. Call get_weather_tool once for the destination and travel dates.
6. Call estimate_budget_tool once using the selected flight and hotel prices.

Tool usage rules:
- Call each required tool only once. Never repeat a tool call.
- Do not retry searches or repeatedly change filters.
- Do not search for cheaper alternatives after estimating the budget.
- If no suitable result exists, use the available results and explain the limitation.
- If the budget is insufficient, clearly mention that the requested budget
  cannot be met. Never invent cheaper prices.
- Use only IDs and prices returned by tools.
- Use indoor places such as museums, markets, temples and monuments on
  rainy days when possible.
- Prefer outdoor places such as parks, beaches, lakes and forts on dry days.
- Use each place at most once.
- Plan 1 to 3 places per day, with fewer on arrival and departure days.
- If a fare is estimated rather than confirmed, disclose this in reasoning.

When all required tools have been called, immediately produce the final answer.
Do not make any additional tool calls.

Return ONLY one valid JSON object, without markdown fences, in this format:

{
  "summary": "One or two sentences describing the trip.",
  "outbound_flight_ids": ["FL0001"],
  "return_flight_ids": ["FL0002"],
  "hotel_id": "HOT0001",
  "days": [
    {
      "place_ids": ["PLC0001"],
      "theme": "Short theme",
      "notes": "Why these places are scheduled for this day."
    }
  ],
  "reasoning": [
    "Flight selection justification.",
    "Hotel selection justification.",
    "Day plan and weather justification."
  ]
}

The days array must contain exactly one entry per trip day, in order.
Use an empty return_flight_ids array when no return is requested.
"""


def is_available() -> bool:
    """True when an LLM provider key is configured."""
    return resolve_llm_settings().provider is not None


def _build_model():
    from langchain.chat_models import init_chat_model
    from langchain_groq import ChatGroq

    settings = resolve_llm_settings()

    if settings.provider is None:
        raise RuntimeError(
            "No LLM configured. Set GROQ_API_KEY, "
            "ANTHROPIC_API_KEY, or OPENAI_API_KEY."
        )

    if settings.provider == "groq":
        model = ChatGroq(
            model=settings.model,
            temperature=0,
            timeout=30,
            max_retries=1,
        )
    else:
        model = init_chat_model(
            settings.model,
            model_provider=settings.provider,
            temperature=0,
        )

    return model, settings


def _request_prompt(request: TripRequest) -> str:
    lines = [
        f"Plan a {request.days}-day trip from {request.origin} to {request.destination}, starting {request.start_date.isoformat()}.",
        f"Travelers: {request.travelers}. Travel style: {request.style}.",
        f"Flight priority: {request.flight_priority}. Hotel priority: {request.hotel_priority}.",
        f"Return flight requested: {'yes' if request.include_return else 'no'}.",
        f"Minimum hotel stars: {request.min_stars}.",
    ]
    if request.max_hotel_price:
        lines.append(f"Maximum hotel price per night: Rs {request.max_hotel_price}.")
    if request.amenities:
        lines.append("Required hotel amenities: " + ", ".join(request.amenities) + ".")
    if request.interests:
        lines.append("Interests (place types): " + ", ".join(request.interests) + ".")
    if request.budget_cap:
        lines.append(f"Total budget cap: Rs {request.budget_cap}.")
    return "\n".join(lines)


def _message_text(content) -> str:
    """Chat model content can be a string or a list of blocks."""
    if isinstance(content, str):
        return content
    return "".join(block.get("text", "") for block in content if isinstance(block, dict))


def _extract_json(text: str) -> dict:
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("The agent did not return a JSON object.")
    return json.loads(text[start : end + 1])


def _trace_from_messages(messages: list, trace: Trace) -> None:
    """Rebuild the tool-call log from the agent's message history."""
    results = {}
    for message in messages:
        if getattr(message, "type", "") == "tool":
            results[getattr(message, "tool_call_id", "")] = _message_text(message.content)
    for message in messages:
        for call in getattr(message, "tool_calls", None) or []:
            output = results.get(call.get("id", ""), "")
            summary = output[:160] + ("..." if len(output) > 160 else "")
            trace.record(call["name"].removesuffix("_tool"), call.get("args", {}), summary or "(no output)")




def run_agent(
    request: TripRequest,
    trace: Trace,
    data,
) -> tuple[AgentChoice, dict]:
    """Use structured AI decisions in production and tool-calling for scripted tests."""

    model, settings = _build_model()

    # Compatibility path for the scripted model used by the test suite.
    if settings.provider == "scripted":
        from langchain.agents import create_agent

        agent_graph = create_agent(
            model,
            ALL_TOOLS,
            system_prompt=SYSTEM_PROMPT,
        )

        result = agent_graph.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": _request_prompt(request),
                    }
                ]
            },
            config={"recursion_limit": 15},
        )

        messages = result["messages"]

        # Keep agent tool calls first in the displayed trace.
        agent_trace = Trace()
        _trace_from_messages(messages, agent_trace)
        trace.steps[0:0] = agent_trace.steps

        choice = AgentChoice.model_validate(
            _extract_json(_message_text(messages[-1].content))
        )

    else:
        # Production path: make decisions from the data already gathered.
        from dataclasses import asdict

        travel_data = asdict(data)

        prompt = f"""
You are an expert Indian domestic travel planning assistant.

Create a trip plan using ONLY the supplied travel data.

TRAVELLER REQUEST:
{_request_prompt(request)}

AVAILABLE TRAVEL DATA:
{json.dumps(travel_data, ensure_ascii=False)}

DECISION RULES:
1. Select outbound and return flights according to the requested priority.
2. Select a hotel according to the requested hotel priority and filters.
3. Respect the traveler's interests when selecting attractions.
4. Create exactly {request.days} itinerary days.
5. Never invent flight IDs, hotel IDs, place IDs or prices.
6. Never select an ID that is absent from the supplied data.
7. Consider weather when distributing indoor and outdoor attractions.
8. Respect the budget where possible. If impossible, explain the limitation.
9. Use each attraction at most once.
10. Provide concise reasoning for your decisions.

Return a structured AgentChoice.
"""

        structured_model = model.with_structured_output(
            AgentChoice,
            method="function_calling",
        )

        choice = structured_model.invoke(prompt)

        if not isinstance(choice, AgentChoice):
            choice = AgentChoice.model_validate(choice)

    engine = {
        "mode": "llm-agent",
        "provider": settings.provider,
        "model": settings.model,
        "note": (
            f"LangChain AI decision engine ({settings.model}) "
            "selected and validated travel options."
        ),
    }

    return choice, engine




def parse_query_with_llm(text: str, today: date) -> ParsedQuery:
    """Extract trip details from free text using structured output."""
    model, _ = _build_model()
    structured = model.with_structured_output(ParsedQuery)
    prompt = (
        f"Today is {today.isoformat()}. Extract trip details from the request. "
        "Cities must be one of: Bangalore, Chennai, Delhi, Goa, Hyderabad, Jaipur, Kolkata, Mumbai. "
        "Interests must be among: park, market, museum, temple, lake, fort, beach, monument. "
        "Style is Budget, Comfort or Luxury. Leave unknown fields empty.\n\nRequest: " + text
    )
    return structured.invoke(prompt)
