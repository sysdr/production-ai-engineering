"""AIAM Day 4 — FastAPI metrics API and live rate-limit dashboard."""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse, Response
from pydantic import BaseModel, Field

from ratelimit.metrics import METRICS
from ratelimit.service import RateLimitService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)-12s] %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)

svc: RateLimitService = RateLimitService(
    budget_usd=float(os.getenv("BUDGET_USD", "10.0"))
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global svc
    svc = RateLimitService(budget_usd=float(os.getenv("BUDGET_USD", "10.0")))
    yield


app = FastAPI(
    title="AIAM Day 4 — Rate Limiting & Cost Control",
    version="1.0.0",
    lifespan=lifespan,
)


class CheckBody(BaseModel):
    user_id: str = Field(min_length=1, max_length=128)
    tier: str = Field(default="standard", pattern="^(standard|premium|admin)$")
    input_tokens: int = Field(default=0, ge=0, le=10_000_000)
    output_tokens: int = Field(default=0, ge=0, le=10_000_000)
    label: str = "api"


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "healthy", "service": "aiam-day04"}


FAVICON_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
    '<rect width="32" height="32" rx="8" fill="#2a1a0d"/>'
    '<text x="16" y="22" text-anchor="middle" font-size="14" '
    'font-family="sans-serif" font-weight="700" fill="#fbbf24">R4</text>'
    "</svg>"
)


@app.get("/favicon.ico")
@app.get("/favicon.svg")
def favicon() -> Response:
    return Response(content=FAVICON_SVG, media_type="image/svg+xml")


@app.get("/metrics")
def metrics() -> JSONResponse:
    return JSONResponse(
        METRICS.snapshot(),
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "Pragma": "no-cache",
        },
    )


@app.post("/check")
def check_request(body: CheckBody) -> dict[str, Any]:
    return svc.check_request(
        body.user_id,
        tier=body.tier,
        input_tokens=body.input_tokens,
        output_tokens=body.output_tokens,
        label=body.label,
    )


@app.get("/status/{user_id}")
def user_status(user_id: str) -> dict[str, Any]:
    return svc.rate_limiter.status(user_id)


@app.post("/demo")
def run_demo() -> dict[str, Any]:
    return svc.run_demo()


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>AIAM Day 4 — Rate Limiting Dashboard</title>
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="shortcut icon" href="/favicon.ico">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=Manrope:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root {
  --bg: #120c08;
  --bg-2: #2a1a0d;
  --panel: rgba(68, 42, 20, 0.55);
  --panel-solid: #3d2614;
  --line: rgba(251, 191, 36, 0.28);
  --text: #fef3e2;
  --muted: #c9a882;
  --accent: #fbbf24;
  --accent-2: #f59e0b;
  --warn: #fb923c;
  --danger: #fca5a5;
  --ok: #86efac;
  --shadow: 0 18px 50px rgba(20, 10, 4, 0.45);
}
* { box-sizing: border-box; }
body {
  margin: 0; min-height: 100vh; color: var(--text);
  font-family: Manrope, system-ui, sans-serif;
  background:
    radial-gradient(900px 520px at 88% -8%, rgba(251, 191, 36, 0.16), transparent 55%),
    radial-gradient(700px 480px at -5% 20%, rgba(245, 158, 11, 0.12), transparent 50%),
    linear-gradient(165deg, var(--bg-2) 0%, var(--bg) 55%, #080504 100%);
  background-attachment: fixed;
}
.shell { max-width: 1180px; margin: 0 auto; padding: 1.75rem 1.5rem 2.5rem; }
.hero {
  display: flex; flex-wrap: wrap; justify-content: space-between; align-items: flex-end;
  gap: 1.25rem; margin-bottom: 1.5rem; padding: 1.5rem 1.6rem;
  border: 1px solid var(--line); border-radius: 20px;
  background: linear-gradient(135deg, rgba(251, 191, 36, 0.12), transparent 42%), var(--panel);
  box-shadow: var(--shadow);
}
.eyebrow { margin: 0 0 0.4rem; font-size: 0.75rem; font-weight: 600; letter-spacing: 0.16em; text-transform: uppercase; color: var(--accent); }
.hero h1 { margin: 0; font-family: "DM Serif Display", Georgia, serif; font-size: clamp(1.7rem, 3.5vw, 2.35rem); }
.sub { margin: 0.55rem 0 0; color: var(--muted); max-width: 40rem; line-height: 1.45; }
.chips { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-top: 0.9rem; }
.chip { font-size: 0.72rem; font-weight: 600; padding: 0.28rem 0.55rem; border-radius: 999px; border: 1px solid var(--line); color: var(--muted); }
.actions { display: flex; flex-direction: column; align-items: flex-end; gap: 0.45rem; }
button {
  background: linear-gradient(180deg, #fde68a, var(--accent)); color: #2a1a0d; border: none;
  border-radius: 999px; padding: 0.8rem 1.35rem; font-weight: 700; cursor: pointer;
}
button:disabled { opacity: 0.55; cursor: not-allowed; }
#status { color: var(--muted); font-size: 0.85rem; min-height: 1.2em; }
.layout { display: grid; gap: 1.1rem; grid-template-columns: minmax(0, 1.7fr) minmax(280px, 1fr); }
@media (max-width: 900px) { .layout { grid-template-columns: 1fr; } }
.pane { border: 1px solid var(--line); border-radius: 18px; background: var(--panel); padding: 1.15rem 1.2rem; box-shadow: var(--shadow); }
.pane-head { display: flex; justify-content: space-between; margin-bottom: 0.95rem; }
.pane-head h2 { margin: 0; font-family: "DM Serif Display", Georgia, serif; font-size: 1.15rem; }
.pane-head span { color: var(--muted); font-size: 0.8rem; }
.grid { display: grid; gap: 0.75rem; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); }
.metric { background: var(--panel-solid); border: 1px solid rgba(255,255,255,0.06); border-radius: 14px; padding: 0.95rem; }
.metric .label { color: var(--muted); font-size: 0.75rem; }
.metric .value { margin-top: 0.45rem; font-family: "DM Serif Display", Georgia, serif; font-size: 1.5rem; font-weight: 700; font-variant-numeric: tabular-nums; }
#events { list-style: none; padding: 0; margin: 0; max-height: 28rem; overflow: auto; }
#events li { margin-bottom: 0.55rem; padding: 0.7rem 0.8rem; border-radius: 12px; border: 1px solid rgba(251, 191, 36, 0.12); background: rgba(20, 12, 6, 0.35); font-size: 0.86rem; color: var(--muted); }
.tag-ok { color: var(--ok); font-weight: 600; }
.tag-throttled { color: var(--danger); font-weight: 600; }
#updated { color: var(--muted); font-size: 0.8rem; margin-top: 0.85rem; }
</style>
</head>
<body>
<div class="shell">
  <header class="hero">
    <div>
      <p class="eyebrow">AIAM Day 4</p>
      <h1>Rate Limiting &amp; Cost Control</h1>
      <p class="sub">Token-bucket throttling, per-user spend tracking, and budget alerts for production AI workloads.</p>
      <div class="chips">
        <span class="chip">Token bucket</span>
        <span class="chip">Tier limits</span>
        <span class="chip">Cost tracking</span>
        <span class="chip">Budget alerts</span>
      </div>
    </div>
    <div class="actions">
      <button id="demoBtn" onclick="runDemo()">Run demo</button>
      <span id="status"></span>
    </div>
  </header>
  <main class="layout">
    <section class="pane">
      <div class="pane-head"><h2>Live metrics</h2><span>Auto-refresh every 1s</span></div>
      <div class="grid" id="metrics">Loading metrics…</div>
    </section>
    <aside class="pane">
      <div class="pane-head"><h2>Recent events</h2><span>Latest 10</span></div>
      <ul id="events"><li>No events yet — run the demo.</li></ul>
      <div id="updated"></div>
    </aside>
  </main>
</div>
<script>
function fmt(n){ return (typeof n === 'number') ? n : 0; }
function money(n){ return '$' + (typeof n === 'number' ? n.toFixed(4) : '0.0000'); }
function pct(n){ return (typeof n === 'number') ? (n * 100).toFixed(1) + '%' : '0%'; }
function esc(v){ return String(v==null?'':v).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;'); }
function render(d){
  document.getElementById('metrics').innerHTML =
    '<div class="metric"><div class="label">Requests total</div><div class="value">'+fmt(d.requests_total)+'</div></div>'+
    '<div class="metric"><div class="label">Allowed</div><div class="value">'+fmt(d.requests_allowed)+'</div></div>'+
    '<div class="metric"><div class="label">Throttled</div><div class="value">'+fmt(d.requests_throttled)+'</div></div>'+
    '<div class="metric"><div class="label">Throttle rate</div><div class="value">'+pct(d.throttle_rate)+'</div></div>'+
    '<div class="metric"><div class="label">Input tokens</div><div class="value">'+fmt(d.tokens_input_total)+'</div></div>'+
    '<div class="metric"><div class="label">Output tokens</div><div class="value">'+fmt(d.tokens_output_total)+'</div></div>'+
    '<div class="metric"><div class="label">Spend (USD)</div><div class="value">'+money(d.spend_usd_total)+'</div></div>'+
    '<div class="metric"><div class="label">Budget left</div><div class="value">'+money(d.budget_remaining_usd)+'</div></div>'+
    '<div class="metric"><div class="label">Users tracked</div><div class="value">'+fmt(d.users_tracked)+'</div></div>'+
    '<div class="metric"><div class="label">Budget alerts</div><div class="value">'+fmt(d.budget_alerts)+'</div></div>'+
    '<div class="metric"><div class="label">Avg latency (ms)</div><div class="value">'+fmt(d.latency_ms_avg)+'</div></div>'+
    '<div class="metric"><div class="label">Demo runs</div><div class="value">'+fmt(d.demo_runs)+'</div></div>';
  var events = d.recent_events || [];
  var ul = document.getElementById('events');
  if (!events.length) { ul.innerHTML = '<li>No events yet — run the demo.</li>'; }
  else {
    ul.innerHTML = events.map(function(e){
      var cls = 'tag-' + (e.status||'ok');
      var when = e.timestamp ? new Date(e.timestamp).toLocaleTimeString() : '';
      return '<li><span class="'+cls+'">['+esc(e.status)+']</span> '+esc(e.label||e.tier||'')
        +' · '+esc(e.user||'')+' · '+esc(when)+' · '+fmt(e.latency_ms)+'ms<br>'+esc(e.detail||'')+'</li>';
    }).join('');
  }
  document.getElementById('updated').textContent = 'Last updated: ' + new Date().toLocaleTimeString();
}
function refresh(){
  fetch('/metrics?t='+Date.now()).then(function(r){ return r.json(); }).then(render)
    .catch(function(){ document.getElementById('metrics').innerHTML = 'Error loading metrics'; });
}
function runDemo(){
  var btn = document.getElementById('demoBtn'); var st = document.getElementById('status');
  btn.disabled = true; st.textContent = 'Running demo…';
  fetch('/demo', { method:'POST' }).then(function(r){ return r.json(); }).then(function(d){
    render(d.metrics || d); st.textContent = 'Demo complete — metrics updated.'; btn.disabled = false;
    setTimeout(function(){ st.textContent=''; }, 2500);
  }).catch(function(e){ st.textContent = 'Error: ' + e; btn.disabled = false; });
}
refresh(); setInterval(refresh, 1000);
</script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard() -> HTMLResponse:
    return HTMLResponse(
        DASHBOARD_HTML,
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "Pragma": "no-cache",
        },
    )
