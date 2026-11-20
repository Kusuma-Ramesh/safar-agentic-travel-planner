"""Global CSS for the Streamlit app.

Palette
  lagoon   #0B4F6C  primary, route codes, stub
  deep     #082F44  banner
  marigold #F5B841  highlight (hotel, selection)
  mist     #EDF1F4  page background
  ink      #0F2233  text
  slate    #5B6B78  secondary text
  rain     #3A7CA5  weather and rain accents
Type: Bricolage Grotesque for display, Instrument Sans for text.
"""

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700;12..96,800&family=Instrument+Sans:wght@400;500;600;700&display=swap');

:root {
  --lagoon: #0B4F6C; --deep: #082F44; --marigold: #F5B841; --mist: #EDF1F4;
  --ink: #0F2233; --slate: #5B6B78; --line: #D5DEE4; --rain: #3A7CA5;
  --ok: #2F7D5B; --bad: #B4412F; --card: #FFFFFF;
  --display: 'Bricolage Grotesque', 'Segoe UI', system-ui, sans-serif;
  --text: 'Instrument Sans', 'Segoe UI', system-ui, -apple-system, sans-serif;
}

html, body, [data-testid="stAppViewContainer"], .stApp { background: var(--mist); }
html, body, .stApp, .stMarkdown, p, label, input, textarea, button, [data-baseweb] { font-family: var(--text); color: var(--ink); }
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stHeader"] { display: none !important; visibility: hidden; }
.block-container { max-width: 1180px; padding: 1.25rem 1.25rem 4rem; }
h1, h2, h3, h4 { font-family: var(--display); letter-spacing: -0.015em; color: var(--ink); }
:focus-visible { outline: 3px solid var(--marigold) !important; outline-offset: 2px; }

/* ---------- banner ---------- */
.banner { background: radial-gradient(1200px 400px at 85% -20%, #14729A 0%, rgba(20,114,154,0) 60%), var(--deep);
  border-radius: 28px; padding: 28px 40px 110px; color: #fff; }
.banner .brand { display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
.banner .logo { display: flex; align-items: center; gap: 10px; font-family: var(--display); font-weight: 800; font-size: 22px; letter-spacing: -0.02em; }
.banner .logo svg { width: 26px; height: 26px; stroke: var(--marigold); }
.banner .badge { font-size: 13px; font-weight: 600; padding: 7px 14px; border-radius: 999px; background: rgba(255,255,255,.1); border: 1px solid rgba(255,255,255,.18); color: #E7F2F7; }
.banner .badge i { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 8px; background: #7BE0B0; }
.banner .badge.offline i { background: var(--marigold); }
.banner h1 { font-size: clamp(34px, 5.2vw, 60px); line-height: 1.02; font-weight: 800; margin: 44px 0 14px; color: #fff; max-width: 15ch; }
.banner p.lede { font-size: 18px; line-height: 1.5; color: #C9DDE8; max-width: 52ch; margin: 0; }

/* ---------- search card ---------- */
.st-key-search { background: var(--card); border-radius: 24px; padding: 26px 28px 22px; margin: -84px 20px 8px; position: relative; z-index: 2;
  box-shadow: 0 1px 2px rgba(8,47,68,.06), 0 24px 48px -24px rgba(8,47,68,.35); }
[data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] label { font-size: 13px !important; font-weight: 600; color: var(--slate) !important; }
[data-baseweb="select"] > div, [data-baseweb="input"], [data-baseweb="base-input"], [data-testid="stDateInput"] [data-baseweb="input"],
[data-testid="stNumberInput"] [data-baseweb="input"], textarea { border-radius: 12px !important; border-color: var(--line) !important; background: #fff !important; }
[data-baseweb="select"] > div:focus-within, [data-baseweb="input"]:focus-within, textarea:focus { border-color: var(--lagoon) !important; box-shadow: 0 0 0 3px rgba(11,79,108,.15) !important; }
textarea { font-size: 16px !important; line-height: 1.5; }
[data-baseweb="tag"] { background: #E3EFF4 !important; border-radius: 8px !important; }
[data-baseweb="tag"] span { color: var(--lagoon) !important; font-weight: 600; }
[data-testid="stExpander"] { border: 1px solid var(--line) !important; border-radius: 14px !important; background: #FAFCFD; }
[data-testid="stExpander"] summary p { font-weight: 600; }

/* buttons */
.stButton > button, [data-testid="stDownloadButton"] button, [data-testid^="stBaseButton"] { border-radius: 12px; font-weight: 600; min-height: 46px; border: 1px solid var(--line); background: #fff; color: var(--ink); transition: background .15s, border-color .15s, color .15s; }
.stButton > button:hover, [data-testid="stDownloadButton"] button:hover { border-color: var(--lagoon); color: var(--lagoon); }
.stButton > button[kind="primary"], [data-testid="stBaseButton-primary"] { background: var(--lagoon); border-color: var(--lagoon); color: #fff; min-height: 52px; font-size: 16px; }
.stButton > button[kind="primary"]:hover, [data-testid="stBaseButton-primary"]:hover { background: #09405A; border-color: #09405A; color: #fff; }
.stButton > button[kind="primary"] p, [data-testid="stBaseButton-primary"] p { color: #fff; }

/* tabs */
[data-baseweb="tab-list"] { gap: 6px; border-bottom: 1px solid var(--line); }
[data-baseweb="tab"] { height: 46px; padding: 0 16px; background: transparent; border-radius: 10px 10px 0 0; }
[data-baseweb="tab"] p { font-weight: 600; font-size: 15px; color: var(--slate); }
[aria-selected="true"][data-baseweb="tab"] p { color: var(--lagoon); }
[data-baseweb="tab-highlight"] { background: var(--lagoon) !important; height: 3px !important; }
[data-baseweb="tab-border"] { display: none; }

/* ---------- boarding pass ---------- */
.pass { display: grid; grid-template-columns: minmax(0, 1fr) 250px; background: var(--card); border-radius: 26px; position: relative;
  box-shadow: 0 1px 2px rgba(8,47,68,.06), 0 28px 56px -28px rgba(8,47,68,.4); margin: 10px 0 18px; }
.pass-main { padding: 28px 32px 26px; min-width: 0; }
.pass-kicker { font-size: 13px; font-weight: 600; color: var(--slate); display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
.pass-route { display: flex; align-items: center; gap: 18px; margin: 10px 0 2px; }
.pass-code { font-family: var(--display); font-weight: 800; font-size: clamp(44px, 7vw, 76px); letter-spacing: -0.03em; line-height: 1; color: var(--lagoon); }
.pass-line { flex: 1; min-width: 60px; display: flex; align-items: center; color: var(--marigold); }
.pass-line::before, .pass-line::after { content: ""; flex: 1; border-top: 2px dotted #B9C8D2; }
.pass-line svg { width: 30px; height: 30px; margin: 0 10px; transform: rotate(45deg); stroke: var(--lagoon); fill: var(--marigold); }
.pass-cities { display: flex; justify-content: space-between; font-size: 15px; color: var(--slate); font-weight: 500; }
.pass-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 16px 22px; margin-top: 24px; padding-top: 20px; border-top: 1px dashed var(--line); }
.pass-grid dt { font-size: 12.5px; color: var(--slate); font-weight: 600; margin: 0 0 3px; }
.pass-grid dd { margin: 0; font-size: 17px; font-weight: 600; font-variant-numeric: tabular-nums; }
.pass-return { margin-top: 18px; padding: 12px 14px; background: #F4F8FA; border-radius: 14px; font-size: 14.5px; display: flex; gap: 10px 18px; flex-wrap: wrap; align-items: center; }
.pass-return b { font-weight: 700; }
.pass-stub { background: var(--lagoon); color: #fff; border-radius: 0 26px 26px 0; padding: 28px 26px; display: flex; flex-direction: column; justify-content: space-between; position: relative; border-left: 2px dashed rgba(255,255,255,.35); }
.pass-stub::before, .pass-stub::after { content: ""; position: absolute; left: -15px; width: 28px; height: 28px; border-radius: 50%; background: var(--mist); }
.pass-stub::before { top: -14px; } .pass-stub::after { bottom: -14px; }
.pass-stub .label { font-size: 13px; font-weight: 600; color: #B8D8E6; }
.pass-stub .total { font-family: var(--display); font-weight: 800; font-size: 40px; letter-spacing: -0.02em; line-height: 1.05; margin: 6px 0 4px; font-variant-numeric: tabular-nums; }
.pass-stub .sub { font-size: 14px; color: #D3E6EF; }
.pass-stub .status { margin-top: 18px; font-size: 13.5px; font-weight: 600; padding: 8px 12px; border-radius: 10px; background: rgba(255,255,255,.12); }
.pass-stub .status.over { background: #F6D7D0; color: #7A2517; }
.pass-stub .status.within { background: #D6F1E3; color: #14513A; }
.tag { display: inline-block; font-size: 12px; font-weight: 700; padding: 3px 9px; border-radius: 999px; background: #E3EFF4; color: var(--lagoon); vertical-align: middle; }
.tag.warn { background: #FCEBC4; color: #6B4A00; }
.tag.muted { background: #EEF1F4; color: var(--slate); }

/* ---------- section titles ---------- */
.sec { font-family: var(--display); font-size: 24px; font-weight: 700; letter-spacing: -0.015em; margin: 30px 0 4px; }
.sec-sub { color: var(--slate); font-size: 14.5px; margin: 0 0 14px; max-width: 70ch; }

/* ---------- weather ---------- */
.wx { display: grid; grid-template-columns: repeat(auto-fit, minmax(128px, 1fr)); gap: 12px; }
.wx-day { background: var(--card); border-radius: 18px; padding: 16px 16px 14px; box-shadow: 0 1px 2px rgba(8,47,68,.06); }
.wx-day.wet { background: #E6F0F7; }
.wx-date { font-size: 13px; font-weight: 600; color: var(--slate); }
.wx-day svg { width: 30px; height: 30px; margin: 8px 0 4px; display: block; }
.wx-temp { font-family: var(--display); font-weight: 700; font-size: 26px; font-variant-numeric: tabular-nums; }
.wx-temp small { font-family: var(--text); font-size: 14px; color: var(--slate); font-weight: 500; margin-left: 4px; }
.wx-cond { font-size: 14px; font-weight: 500; }
.wx-rain { font-size: 12.5px; color: var(--rain); font-weight: 600; margin-top: 4px; }

/* ---------- timeline ---------- */
.tl { position: relative; padding-left: 34px; }
.tl::before { content: ""; position: absolute; left: 11px; top: 10px; bottom: 10px; border-left: 2px solid var(--line); }
.day { position: relative; background: var(--card); border-radius: 20px; padding: 20px 22px 8px; margin-bottom: 14px; box-shadow: 0 1px 2px rgba(8,47,68,.06); }
.day::before { content: ""; position: absolute; left: -31px; top: 26px; width: 14px; height: 14px; border-radius: 50%; background: var(--lagoon); box-shadow: 0 0 0 4px var(--mist); }
.day-head { display: flex; justify-content: space-between; gap: 12px; align-items: flex-start; flex-wrap: wrap; margin-bottom: 8px; }
.day-title { font-family: var(--display); font-weight: 700; font-size: 20px; letter-spacing: -0.01em; }
.day-meta { font-size: 13.5px; color: var(--slate); font-weight: 500; margin-top: 2px; }
.day-wx { display: flex; align-items: center; gap: 6px; font-size: 13.5px; font-weight: 600; color: var(--slate); background: #F1F5F8; padding: 6px 10px; border-radius: 10px; white-space: nowrap; }
.day-wx svg { width: 18px; height: 18px; }
.logi { display: flex; gap: 10px; align-items: flex-start; font-size: 14px; color: var(--slate); padding: 6px 0; }
.logi svg { width: 16px; height: 16px; flex: none; margin-top: 3px; stroke: var(--slate); }
.act { display: grid; grid-template-columns: 84px minmax(0, 1fr); gap: 14px; padding: 12px 0; border-top: 1px solid #EDF1F4; }
.act-slot { font-size: 13px; font-weight: 600; color: var(--slate); padding-top: 2px; }
.act-title { font-weight: 600; font-size: 16.5px; display: flex; gap: 8px 10px; align-items: center; flex-wrap: wrap; }
.act-rate { display: inline-flex; align-items: center; gap: 3px; font-size: 13.5px; font-weight: 600; font-variant-numeric: tabular-nums; }
.act-rate svg { width: 14px; height: 14px; fill: var(--marigold); stroke: var(--marigold); }
.act-note { font-size: 14px; color: var(--slate); margin-top: 3px; }
.act.free .act-title { color: var(--slate); font-weight: 500; }
.day-note { font-size: 14px; color: var(--slate); padding: 4px 0 10px; }

/* ---------- side cards ---------- */
.card { background: var(--card); border-radius: 20px; padding: 22px; box-shadow: 0 1px 2px rgba(8,47,68,.06); margin-bottom: 14px; }
.card h3 { font-size: 13px; font-weight: 600; color: var(--slate); font-family: var(--text); letter-spacing: 0; margin: 0 0 10px; }
.hotel-name { font-family: var(--display); font-weight: 700; font-size: 24px; letter-spacing: -0.015em; line-height: 1.15; }
.stars { display: flex; gap: 2px; margin: 8px 0 12px; }
.stars svg { width: 17px; height: 17px; fill: var(--marigold); stroke: var(--marigold); }
.stars svg.off { fill: none; stroke: #C9D4DC; }
.chips { display: flex; flex-wrap: wrap; gap: 6px; }
.chip { font-size: 13px; font-weight: 600; padding: 5px 11px; border-radius: 999px; background: #EEF3F6; color: var(--ink); }
.kv { display: flex; justify-content: space-between; gap: 12px; font-size: 14.5px; padding: 9px 0; border-top: 1px solid #EDF1F4; font-variant-numeric: tabular-nums; }
.kv:first-of-type { border-top: 0; }
.kv span:first-child { color: var(--slate); }
.kv b { font-weight: 700; }
.bar { display: flex; height: 14px; border-radius: 8px; overflow: hidden; margin: 6px 0 16px; background: #E3EAEF; }
.bar i { display: block; height: 100%; }
.legend { display: flex; align-items: center; gap: 10px; font-size: 14.5px; padding: 7px 0; font-variant-numeric: tabular-nums; }
.legend i { width: 12px; height: 12px; border-radius: 4px; flex: none; }
.legend .amt { margin-left: auto; font-weight: 700; }
.legend .pct { color: var(--slate); width: 42px; text-align: right; }
.total-row { display: flex; justify-content: space-between; align-items: baseline; border-top: 2px solid var(--ink); margin-top: 8px; padding-top: 12px; }
.total-row .n { font-family: var(--display); font-weight: 800; font-size: 28px; font-variant-numeric: tabular-nums; }
.meter { height: 8px; background: #E3EAEF; border-radius: 6px; overflow: hidden; margin: 10px 0 6px; }
.meter i { display: block; height: 100%; background: var(--ok); }
.meter.over i { background: var(--bad); }
.why { margin: 0; padding: 0; list-style: none; }
.why li { font-size: 14.5px; line-height: 1.5; padding: 10px 0 10px 18px; border-top: 1px solid #EDF1F4; position: relative; max-width: 78ch; }
.why li:first-child { border-top: 0; }
.why li::before { content: ""; position: absolute; left: 0; top: 18px; width: 6px; height: 6px; border-radius: 50%; background: var(--marigold); }
.notice { background: #FFF6E0; border: 1px solid #F3DDA0; color: #5C4200; border-radius: 14px; padding: 12px 16px; font-size: 14px; line-height: 1.5; margin-bottom: 8px; }
.notice.info { background: #E9F2F7; border-color: #CFE2EC; color: #0B3C57; }
.notice.error { background: #FBE9E5; border-color: #F0C7BE; color: #7A2517; }
.trace { width: 100%; border-collapse: collapse; font-size: 13.5px; }
.trace th { text-align: left; color: var(--slate); font-weight: 600; padding: 6px 10px 6px 0; }
.trace td { padding: 9px 10px 9px 0; border-top: 1px solid #EDF1F4; vertical-align: top; }
.trace code { background: #EEF3F6; border-radius: 6px; padding: 2px 6px; font-size: 12.5px; }

/* ---------- empty state & how it works ---------- */
.empty { text-align: left; padding: 34px 6px 8px; }
.empty h2 { font-size: 30px; margin: 0 0 8px; }
.empty p { color: var(--slate); font-size: 16px; max-width: 58ch; line-height: 1.55; }
.steps { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 14px; margin: 8px 0 18px; }
.step { background: var(--card); border-radius: 18px; padding: 18px; box-shadow: 0 1px 2px rgba(8,47,68,.06); }
.step .n { font-family: var(--display); font-weight: 800; font-size: 28px; color: var(--lagoon); }
.step b { display: block; margin: 4px 0 4px; font-size: 16px; }
.step span { font-size: 14px; color: var(--slate); line-height: 1.45; }
.understood { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px; }

@media (max-width: 820px) {
  .banner { padding: 22px 22px 100px; border-radius: 22px; }
  .st-key-search { margin: -80px 4px 8px; padding: 20px 16px 16px; }
  .pass { grid-template-columns: 1fr; }
  .pass-stub { border-radius: 0 0 26px 26px; border-left: 0; border-top: 2px dashed rgba(255,255,255,.35); }
  .pass-stub::before, .pass-stub::after { top: -14px; bottom: auto; }
  .pass-stub::before { left: -14px; } .pass-stub::after { left: auto; right: -14px; }
  .pass-main { padding: 22px 20px; }
  .act { grid-template-columns: 1fr; gap: 2px; }
  .tl { padding-left: 24px; } .day::before { left: -23px; }
}
@media (prefers-reduced-motion: reduce) { * { transition: none !important; animation: none !important; } }

/* ---------- flight weather monitor ---------- */
.wx-flight-card {
    background: #fff;
    border: 1px solid #dce4e8;
    border-radius: 16px;
    padding: 18px 20px;
    margin: 16px 0 22px;
    color: #172b36;
}

.wx-flight-title,
.wx-flight-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
}

.wx-flight-title h3 {
    font-size: 1.05rem;
    margin: 0;
    font-weight: 700;
}

.wx-flight-leg {
    border-top: 1px solid #e7ecef;
    margin-top: 14px;
    padding-top: 13px;
}

.wx-flight-points {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
    margin-top: 10px;
}

.wx-flight-point {
    background: #f5f8f9;
    border-radius: 10px;
    padding: 10px;
    display: flex;
    flex-direction: column;
    gap: 3px;
}

.wx-flight-point span {
    font-size: .9rem;
}

.wx-flight-point small,
.wx-flight-leg small {
    font-size: .76rem;
    color: #60717b;
}

.wx-flight-leg p {
    font-size: .84rem;
    color: #42545e;
    margin: 9px 0 3px;
}

.wx-flight-disclaimer {
    font-size: .75rem;
    color: #667780;
    margin: 15px 0 0;
}

@media (max-width: 640px) {
    .wx-flight-points {
        grid-template-columns: 1fr;
    }
}

</style>
"""
