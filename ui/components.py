"""HTML building blocks for the Streamlit UI.

Every function returns a single-line HTML string (no blank lines or indentation)
so Streamlit's markdown parser never turns it into a code block.
All dynamic text is escaped.
"""

from __future__ import annotations

import re
from datetime import date, timedelta
from html import escape

_STROKE = 'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"'
_CLOUD = "M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"

ICONS: dict[str, str] = {
    "plane": '<path d="M17.8 19.2 16 11l3.5-3.5C21 6 21.5 4 21 3c-1-.5-3 0-4.5 1.5L13 8 4.8 6.2c-.5-.1-.9.1-1.1.5l-.2.4c-.2.5-.1 1 .3 1.3L9 12l-2 3H4l-1 1 3 2 2 3 1-1v-3l3-2 3.5 5.3c.3.4.8.5 1.3.3l.4-.2c.4-.3.6-.7.5-1.2z"/>',
    "star": '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>',
    "bed": '<path d="M3 18V6M3 14h18v4M21 14v-2a3 3 0 0 0-3-3h-7v5"/><circle cx="7" cy="11" r="1.5"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    "partly": f'<path d="M12 3v1.5M4.2 6.2l1 1M2.5 12H4M19.8 6.2l-1 1"/><path d="M7 12.5a4 4 0 0 1 7.2-2.3"/><path d="{_CLOUD.replace("M18 10", "M19 14").replace("h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z", "h-.7A5.5 5.5 0 0 0 8 15.2 3.9 3.9 0 0 0 9 22h10a4 4 0 0 0 0-8z")}" transform="translate(0 -2)"/>',
    "cloud": f'<path d="{_CLOUD}"/>',
    "rain": '<path d="M20 16.6A5 5 0 0 0 18 7h-1.26A8 8 0 1 0 4 15.25"/><path d="M8 19v2M8 13v2M16 19v2M16 13v2M12 21v2M12 15v2"/>',
    "storm": '<path d="M19 16.9A5 5 0 0 0 18 7h-1.26a8 8 0 1 0-11.62 9"/><path d="m13 11-4 6h6l-4 6"/>',
    "fog": '<path d="M5 8h14M3 12h18M6 16h12M9 20h6"/>',
    "snow": '<path d="M12 2v20M4.2 7l15.6 10M19.8 7 4.2 17"/>',
    "route": '<circle cx="6" cy="19" r="2"/><circle cx="18" cy="5" r="2"/><path d="M8 19h6a4 4 0 0 0 0-8h-4a4 4 0 0 1 0-8h6"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
}
WEATHER_COLORS = {"sun": "#E39B0B", "partly": "#E39B0B", "cloud": "#5B6B78", "rain": "#3A7CA5", "storm": "#6B4FA0", "fog": "#7D8B96", "snow": "#5B8FB9"}


def _single_line(html: str) -> str:
    return re.sub(r">\s+<", "><", " ".join(html.split()))


def icon(name: str, color: str | None = None) -> str:
    style = f' style="color:{color};stroke:{color}"' if color else ""
    return f"<svg {_STROKE}{style} aria-hidden=\"true\">{ICONS[name]}</svg>"


def e(value) -> str:
    return escape(str(value))


def money(amount: int | float) -> str:
    return f"\u20b9{int(round(amount)):,}"


def short_date(iso: str) -> str:
    return date.fromisoformat(iso).strftime("%a %d %b")


def duration(minutes: int) -> str:
    hours, mins = divmod(int(minutes), 60)
    return f"{hours}h {mins:02d}m" if hours and mins else f"{hours}h" if hours else f"{mins}m"


# --------------------------------------------------------------------------
def banner(engine: dict | None, llm_label: str | None) -> str:
    if llm_label:
        badge = f'<span class="badge"><i></i>{e(llm_label)}</span>'
    else:
        badge = '<span class="badge offline"><i></i>Offline planner. Add an API key to switch on the LLM agent</span>'
    return _single_line(f"""
    <div class="banner">
      <div class="brand">
        <div class="logo">{icon("route")}Safar</div>
        {badge}
      </div>
      <h1>Plan the whole trip in one go.</h1>
      <p class="lede">Tell Safar where you are going. It checks flights, hotels, places and the weather, then
      hands back a day-by-day plan with a budget you can trust.</p>
    </div>""")


def understood_chips(parsed: dict) -> str:
    chips = []
    if parsed.get("origin") and parsed.get("destination"):
        chips.append(f"{parsed['origin']} to {parsed['destination']}")
    elif parsed.get("destination"):
        chips.append(f"To {parsed['destination']}")
    if parsed.get("start_date"):
        chips.append(short_date(parsed["start_date"]))
    if parsed.get("days"):
        chips.append(f"{parsed['days']} days")
    if parsed.get("travelers"):
        chips.append(f"{parsed['travelers']} traveller(s)")
    if parsed.get("budget_cap"):
        chips.append(f"Budget {money(parsed['budget_cap'])}")
    if parsed.get("style"):
        chips.append(parsed["style"])
    for interest in parsed.get("interests", []):
        chips.append(interest.title())
    if not chips:
        return ""
    return _single_line('<div class="understood">' + "".join(f'<span class="chip">{e(c)}</span>' for c in chips) + "</div>")


# --------------------------------------------------------------------------
def _flight_kind_tag(option: dict) -> str:
    if option.get("estimated"):
        return '<span class="tag warn">Estimated fare</span>'
    if option["stops"]:
        return f'<span class="tag muted">1 stop via {e(option["via"])}</span>'
    return '<span class="tag">Direct</span>'


def boarding_pass(plan: dict) -> str:
    route, request, budget = plan["route"], plan["request"], plan["budget"]
    out = plan["flight"]["outbound"]
    ret = plan["flight"]["return"]
    start = date.fromisoformat(request["start_date"])
    end = start + timedelta(days=request["days"] - 1)
    arrives = out["arrival"] + (" +1" if out.get("arrival_day_offset") else "")

    return_row = ""
    if ret:
        return_row = (
            f'<div class="pass-return"><b>Return</b><span>{e(ret["from"])} to {e(ret["to"])}</span>'
            f'<span>{e(ret["departure"])} to {e(ret["arrival"])}</span><span>{e(ret["airline"])}</span>'
            f'<span>{money(ret["price"])} each</span>{_flight_kind_tag(ret)}</div>'
        )

    if budget["status"] == "within":
        status = f'<div class="status within">{money(budget["difference"])} under your {money(budget["cap"])} budget</div>'
    elif budget["status"] == "over":
        status = f'<div class="status over">{money(-budget["difference"])} over your {money(budget["cap"])} budget</div>'
    else:
        status = ""

    return _single_line(f"""
    <section class="pass" aria-label="Trip summary">
      <div class="pass-main">
        <div class="pass-kicker">{e(start.strftime('%d %b'))} to {e(end.strftime('%d %b %Y'))}
          <span class="tag muted">{request['days']} days</span>
          <span class="tag muted">{request['travelers']} traveller{'s' if request['travelers'] > 1 else ''}</span>
          {_flight_kind_tag(out)}</div>
        <div class="pass-route">
          <div class="pass-code">{e(route['origin_code'])}</div>
          <div class="pass-line">{icon('plane')}</div>
          <div class="pass-code">{e(route['destination_code'])}</div>
        </div>
        <div class="pass-cities"><span>{e(route['origin'])}</span><span>{e(route['destination'])}</span></div>
        <dl class="pass-grid">
          <div><dt>Departs</dt><dd>{e(out['departure'])}</dd></div>
          <div><dt>Arrives</dt><dd>{e(arrives)}</dd></div>
          <div><dt>Flight time</dt><dd>{e(duration(out['duration_minutes']))}</dd></div>
          <div><dt>Airline</dt><dd>{e(out['airline'])}</dd></div>
          <div><dt>Fare</dt><dd>{money(out['price'])}</dd></div>
        </dl>
        {return_row}
      </div>
      <aside class="pass-stub">
        <div><div class="label">Estimated total</div><div class="total">{money(budget['total'])}</div>
          <div class="sub">{money(budget['per_person'])} per person</div></div>
        {status}
      </aside>
    </section>""")

def flight_weather_card(plan: dict) -> str:
    """Display weather-based risk indicators for selected flight legs."""

    monitor = plan.get("flight_weather") or {}
    if not monitor:
        return ""

    colors = {
        "Low": "#237A57",
        "Moderate": "#A66A00",
        "High": "#B42318",
        "Unavailable": "#687782",
    }

    overall = monitor.get("overall_risk", "Unavailable")
    cards = []

    for leg in monitor.get("legs", []):
        readings = []

        for item in leg.get("readings", []):
            if item.get("available"):
                rain = item.get("precipitation_probability")
                gust = item.get("wind_gusts_kmh")

                details = []
                if rain is not None:
                    details.append(f"{rain}% rain")
                if gust is not None:
                    details.append(f"gusts {gust} km/h")

                readings.append(
                    f'<div class="wx-flight-point">'
                    f'<b>{e(item.get("city", "Airport area"))}</b>'
                    f'<span>{e(item.get("condition", "Unknown"))} '
                    f'&middot; {e(item.get("time", "").replace("T", " "))}</span>'
                    f'<small>{e(", ".join(details) if details else "Hourly forecast available")}</small>'
                    f'</div>'
                )
            else:
                readings.append(
                    f'<div class="wx-flight-point">'
                    f'<b>{e(item.get("city", "Airport area"))}</b>'
                    f'<span>Forecast unavailable</span>'
                    f'<small>{e(item.get("reason", "No forecast data"))}</small>'
                    f'</div>'
                )

        risk = leg.get("risk", "Unavailable")

        estimate_note = (
            '<small>Selected flight is a sample fare estimate.</small>'
            if leg.get("is_estimated_flight")
            else ""
        )

        cards.append(
            f'<div class="wx-flight-leg">'
            f'<div class="wx-flight-head">'
            f'<b>{e(leg.get("leg", "Flight"))}: '
            f'{e(leg.get("from", ""))} &rarr; {e(leg.get("to", ""))}</b>'
            f'<span style="color:{colors.get(risk, colors["Unavailable"])};font-weight:700">'
            f'{e(risk)} weather risk</span>'
            f'</div>'
            f'<div class="wx-flight-points">{"".join(readings)}</div>'
            f'<p>{e(leg.get("explanation", ""))}</p>'
            f'{estimate_note}'
            f'</div>'
        )

    return _single_line(
        f'<section class="wx-flight-card">'
        f'<div class="wx-flight-title">'
        f'<h3>Flight Weather Monitor</h3>'
        f'<span style="color:{colors.get(overall, colors["Unavailable"])};font-weight:700">'
        f'Overall: {e(overall)}</span>'
        f'</div>'
        f'{"".join(cards)}'
        f'<p class="wx-flight-disclaimer">'
        f'{e(monitor.get("disclaimer", "Weather indicator only; not live flight status."))}'
        f'</p>'
        f'</section>'
    )


def section(title: str, sub: str = "") -> str:
    sub_html = f'<p class="sec-sub">{e(sub)}</p>' if sub else ""
    return _single_line(f'<h2 class="sec">{e(title)}</h2>{sub_html}')


def weather_strip(plan: dict) -> str:
    cards = []
    for day in plan["itinerary"]:
        w = day["weather"]
        wet = (w.get("rain_chance") or 0) >= 50
        temp = f'{w["temp_max"]}\u00b0<small>/ {w["temp_min"]}\u00b0</small>' if w["temp_max"] is not None else "n/a"
        rain = f'<div class="wx-rain">{w["rain_chance"]}% chance of rain</div>' if w.get("rain_chance") is not None else ""
        basis = "" if w["source"] == "forecast" else f'<div class="wx-rain" style="color:#5B6B78">{"Typical for these dates" if w["source"] == "historical" else "Seasonal estimate"}</div>'
        cards.append(
            f'<div class="wx-day{" wet" if wet else ""}"><div class="wx-date">Day {day["day"]}, {e(short_date(day["date"]))}</div>'
            f'{icon(w["icon"], WEATHER_COLORS.get(w["icon"]))}<div class="wx-temp">{temp}</div>'
            f'<div class="wx-cond">{e(w["condition"])}</div>{rain}{basis}</div>'
        )
    return _single_line(f'<div class="wx">{"".join(cards)}</div>')


def _stars(count: int) -> str:
    return '<div class="stars" role="img" aria-label="' + f"{count} out of 5 stars" + '">' + "".join(
        icon("star").replace("<svg ", '<svg class="off" ' if i >= count else "<svg ") for i in range(5)
    ) + "</div>"


def timeline(plan: dict) -> str:
    days_html = []
    for day in plan["itinerary"]:
        w = day["weather"]
        wx = (
            f'<div class="day-wx">{icon(w["icon"], WEATHER_COLORS.get(w["icon"]))}'
            f'{w["temp_max"] if w["temp_max"] is not None else "-"}\u00b0 {e(w["condition"])}</div>'
        )
        logistics = "".join(f'<div class="logi">{icon("plane")}<span>{e(line)}</span></div>' for line in day["logistics"])
        acts = []
        for a in day["activities"]:
            rating = f'<span class="act-rate">{icon("star")}{a["rating"]}</span>' if a.get("rating") else ""
            kind = f'<span class="tag muted">{e(a["type"])}</span>' if a["kind"] == "place" else ""
            note = f'<div class="act-note">{e(a["note"])}</div>' if a.get("note") else ""
            acts.append(
                f'<div class="act {"free" if a["kind"] != "place" else ""}"><div class="act-slot">{e(a["slot"])}</div>'
                f'<div><div class="act-title">{e(a["title"])}{kind}{rating}</div>{note}</div></div>'
            )
        day_note = f'<div class="day-note">{e(day["notes"])}</div>' if day.get("notes") else ""
        days_html.append(
            f'<article class="day"><div class="day-head"><div><div class="day-title">Day {day["day"]}: {e(day["theme"])}</div>'
            f'<div class="day-meta">{e(short_date(day["date"]))}</div></div>{wx}</div>{day_note}{logistics}{"".join(acts)}</article>'
        )
    return _single_line(f'<div class="tl">{"".join(days_html)}</div>')


def hotel_card(plan: dict) -> str:
    hotel = plan["hotel"]
    amenities = "".join(f'<span class="chip">{e(a.title())}</span>' for a in hotel["amenities"])
    return _single_line(f"""
    <div class="card"><h3>Where you stay</h3>
      <div class="hotel-name">{e(hotel['name'])}</div>
      {_stars(hotel['stars'])}
      <div class="chips" style="margin-bottom:14px">{amenities}</div>
      <div class="kv"><span>Price per night</span><b>{money(hotel['price_per_night'])}</b></div>
      <div class="kv"><span>{hotel['nights']} night{'s' if hotel['nights'] != 1 else ''}, {hotel['rooms']} room{'s' if hotel['rooms'] != 1 else ''}</span><b>{money(hotel['total'])}</b></div>
    </div>""")


def budget_card(plan: dict) -> str:
    b = plan["budget"]
    rows = [("Flights", b["flights"], "#0B4F6C"), ("Hotel", b["hotel"], "#F5B841"), ("Food and local travel", b["local"], "#7FB7BE")]
    total = b["total"] or 1
    bar = "".join(f'<i style="width:{amount / total * 100:.2f}%;background:{color}"></i>' for _, amount, color in rows)
    legend = "".join(
        f'<div class="legend"><i style="background:{color}"></i><span>{label}</span>'
        f'<span class="amt">{money(amount)}</span><span class="pct">{amount / total * 100:.0f}%</span></div>'
        for label, amount, color in rows
    )
    meter = ""
    if b["cap"]:
        share = min(b["total"] / b["cap"] * 100, 100)
        over = b["status"] == "over"
        meter = (
            f'<div class="meter{" over" if over else ""}" role="img" aria-label="Budget used"><i style="width:{share:.0f}%"></i></div>'
            f'<div style="font-size:13.5px;color:#5B6B78">{money(b["total"])} of {money(b["cap"])} budget</div>'
        )
    return _single_line(f"""
    <div class="card"><h3>Budget breakdown</h3>
      <div class="bar" role="img" aria-label="Cost split">{bar}</div>{legend}
      <div class="total-row"><span>Total</span><span class="n">{money(b['total'])}</span></div>{meter}
    </div>""")


def reasoning_list(plan: dict) -> str:
    items = "".join(f"<li>{e(r)}</li>" for r in plan["reasoning"])
    return _single_line(f'<ul class="why">{items}</ul>')


def notices(plan: dict) -> str:
    return _single_line("".join(f'<div class="notice">{e(w)}</div>' for w in plan["warnings"]))


def trace_table(plan: dict) -> str:
    rows = []
    for step in plan["trace"]:
        args = ", ".join(f"{k}={v}" for k, v in step["inputs"].items() if v not in (None, "", []))
        ms = f'{step["ms"]} ms' if step.get("ms") is not None else ""
        rows.append(f'<tr><td><code>{e(step["tool"])}</code></td><td>{e(args)}</td><td>{e(step["summary"])}</td><td>{e(ms)}</td></tr>')
    return _single_line(
        '<table class="trace"><thead><tr><th>Tool</th><th>Input</th><th>Result</th><th>Time</th></tr></thead><tbody>'
        + "".join(rows) + "</tbody></table>"
    )


def notice(text: str, kind: str = "") -> str:
    return _single_line(f'<div class="notice {kind}">{e(text)}</div>')


def how_steps() -> str:
    steps = [
        ("1", "Understand", "Reads your request, in plain words or from the form, and pulls out cities, dates, budget and interests."),
        ("2", "Call tools", "Searches the flights, hotels and places files and asks Open-Meteo for the weather."),
        ("3", "Decide", "Ranks options by your priorities, puts indoor places on rainy days and fits the plan to your budget."),
        ("4", "Verify", "Checks every ID against the data and recalculates all prices in code, never from model output."),
        ("5", "Present", "Shows the itinerary, weather, hotel and costs, with the reasoning behind each choice."),
    ]
    return _single_line('<div class="steps">' + "".join(
        f'<div class="step"><div class="n">{n}</div><b>{t}</b><span>{d}</span></div>' for n, t, d in steps) + "</div>")


def empty_state() -> str:
    return _single_line("""
    <div class="empty"><h2>Your plan will appear here</h2>
    <p>Fill in the form above and choose Plan my trip, or describe the trip in your own words.
    Try one of these to see how it works.</p></div>""")
