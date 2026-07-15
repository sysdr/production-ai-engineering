"""AIAM Day 2 — FastAPI metrics API and live tool-execution dashboard."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse, Response
from pydantic import BaseModel, Field

from tools.metrics import METRICS
from tools.registry import ToolOrchestrator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)-12s] %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)

# Eager init so CLI/tests work; lifespan keeps a fresh instance for the server.
orch: ToolOrchestrator = ToolOrchestrator()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global orch
    orch = ToolOrchestrator()
    yield


app = FastAPI(
    title="AIAM Day 2 — Tool Execution",
    version="1.0.0",
    lifespan=lifespan,
)


class ToolCallBody(BaseModel):
    tool: str = Field(min_length=1, max_length=64)
    params: dict[str, Any] = Field(default_factory=dict)
    permissions: list[str] = Field(default_factory=lambda: ["read"])
    label: str = "api"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy", "service": "aiam-day02"}


FAVICON_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
    '<rect width="32" height="32" rx="8" fill="#0d2f28"/>'
    '<text x="16" y="22" text-anchor="middle" font-size="14" '
    'font-family="sans-serif" font-weight="700" fill="#5eead4">T2</text>'
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


@app.post("/tools/call")
def tools_call(body: ToolCallBody) -> dict[str, Any]:
    result = orch.call(
        body.tool,
        body.params,
        body.permissions,
        label=body.label,
    )
    return result.model_dump()


DEMO_STEPS: list[tuple[str, str, dict[str, Any], list[str]]] = [
    ("CALC_OK", "calculate", {"expression": "3 * (7 + 2)"}, ["read"]),
    ("UNSAFE", "calculate", {"expression": "__import__('os')"}, ["read"]),
    ("ECHO", "echo", {"message": "Hello from Layer 3!"}, ["read"]),
    (
        "WRITE_OK",
        "write_log",
        {"message": "deploy v1.2", "level": "INFO"},
        ["read", "write"],
    ),
    (
        "WRITE_DENIED",
        "write_log",
        {"message": "sneaky write", "level": "INFO"},
        ["read"],
    ),
    ("UNKNOWN", "nonexistent", {}, ["read", "write"]),
]


@app.post("/demo")
def run_demo() -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for label, tool, params, perms in DEMO_STEPS:
        r = orch.call(tool, params, perms, label=label)
        results.append(
            {
                "label": label,
                "tool": tool,
                "status": "ok" if r.success else "error",
                "output": r.output,
                "error": r.error,
                "latency_ms": r.latency_ms,
            }
        )
    METRICS.bump_demo()
    return {"results": results, "metrics": METRICS.snapshot()}


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>AIAM Day 2 — Tool Execution Dashboard</title>
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="shortcut icon" href="/favicon.ico">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,700&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root {
  --bg: #071a16;
  --bg-2: #0d2f28;
  --panel: rgba(20, 72, 62, 0.55);
  --panel-solid: #16483e;
  --line: rgba(110, 231, 183, 0.28);
  --text: #e6f7f1;
  --muted: #95c4b6;
  --accent: #5eead4;
  --accent-2: #14b8a6;
  --warn: #fbbf24;
  --danger: #fca5a5;
  --ok: #a7f3d0;
  --shadow: 0 18px 50px rgba(4, 28, 22, 0.45);
}
* { box-sizing: border-box; }
body {
  margin: 0;
  min-height: 100vh;
  color: var(--text);
  font-family: "IBM Plex Sans", system-ui, sans-serif;
  background:
    radial-gradient(900px 520px at 88% -8%, rgba(94, 234, 212, 0.18), transparent 55%),
    radial-gradient(700px 480px at -5% 20%, rgba(20, 184, 166, 0.16), transparent 50%),
    linear-gradient(165deg, var(--bg-2) 0%, var(--bg) 55%, #04110e 100%);
  background-attachment: fixed;
}
body::before {
  content: "";
  position: fixed; inset: 0; pointer-events: none; z-index: 0;
  background-image:
    linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px);
  background-size: 48px 48px;
  mask-image: radial-gradient(ellipse at center, black 20%, transparent 75%);
}
.shell {
  position: relative; z-index: 1;
  max-width: 1180px; margin: 0 auto;
  padding: 1.75rem 1.5rem 2.5rem;
}
.hero {
  display: flex; flex-wrap: wrap; justify-content: space-between; align-items: flex-end;
  gap: 1.25rem; margin-bottom: 1.5rem;
  padding: 1.5rem 1.6rem;
  border: 1px solid var(--line);
  border-radius: 20px;
  background:
    linear-gradient(135deg, rgba(94, 234, 212, 0.14), transparent 42%),
    linear-gradient(180deg, rgba(255,255,255,0.05), transparent),
    var(--panel);
  box-shadow: var(--shadow);
  backdrop-filter: blur(10px);
  animation: rise 0.55s ease-out both;
}
.eyebrow {
  margin: 0 0 0.4rem;
  font-size: 0.75rem; font-weight: 600; letter-spacing: 0.16em; text-transform: uppercase;
  color: var(--accent);
}
.hero h1 {
  margin: 0;
  font-family: Fraunces, Georgia, serif;
  font-size: clamp(1.7rem, 3.5vw, 2.35rem);
  font-weight: 700; line-height: 1.15; letter-spacing: -0.02em;
}
.sub { margin: 0.55rem 0 0; color: var(--muted); max-width: 38rem; line-height: 1.45; }
.layers {
  display: flex; flex-wrap: wrap; gap: 0.4rem; margin-top: 0.9rem;
}
.layer-chip {
  font-size: 0.72rem; font-weight: 600; letter-spacing: 0.04em;
  padding: 0.28rem 0.55rem; border-radius: 999px;
  border: 1px solid var(--line); color: var(--muted); background: rgba(6, 30, 24, 0.35);
}
.actions {
  display: flex; flex-direction: column; align-items: flex-end; gap: 0.45rem;
}
button {
  background: linear-gradient(180deg, #99f6e4, var(--accent));
  color: #042f2e; border: none; border-radius: 999px;
  padding: 0.8rem 1.35rem; font-weight: 600; cursor: pointer; font-size: 0.95rem;
  box-shadow: 0 10px 24px rgba(20, 184, 166, 0.35);
  transition: transform 0.15s ease, box-shadow 0.15s ease, opacity 0.15s ease;
}
button:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 14px 28px rgba(20, 184, 166, 0.45); }
button:disabled { opacity: 0.55; cursor: not-allowed; transform: none; }
#status { color: var(--muted); font-size: 0.85rem; min-height: 1.2em; text-align: right; }
.layout {
  display: grid; gap: 1.1rem;
  grid-template-columns: minmax(0, 1.7fr) minmax(280px, 1fr);
  align-items: start;
}
@media (max-width: 900px) {
  .layout { grid-template-columns: 1fr; }
  .actions { align-items: flex-start; }
  #status { text-align: left; }
}
.pane {
  border: 1px solid var(--line);
  border-radius: 18px;
  background: var(--panel);
  backdrop-filter: blur(10px);
  box-shadow: var(--shadow);
  padding: 1.15rem 1.2rem 1.25rem;
  animation: rise 0.65s ease-out both;
}
.events-pane { animation-delay: 0.08s; }
.pane-head {
  display: flex; align-items: baseline; justify-content: space-between;
  gap: 0.75rem; margin-bottom: 0.95rem;
}
.pane-head h2 {
  margin: 0;
  font-family: Fraunces, Georgia, serif;
  font-size: 1.15rem; font-weight: 500;
}
.pane-head span { color: var(--muted); font-size: 0.8rem; }
.grid {
  display: grid; gap: 0.75rem;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
}
.metric {
  position: relative; overflow: hidden;
  background: linear-gradient(180deg, rgba(255,255,255,0.05), transparent 55%), var(--panel-solid);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 14px;
  padding: 0.95rem 0.95rem 0.85rem;
  transition: border-color 0.2s ease, transform 0.2s ease;
}
.metric::before {
  content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 3px;
  background: var(--accent); opacity: 0.85;
}
.metric:nth-child(3)::before, .metric:nth-child(4)::before { background: var(--danger); }
.metric:nth-child(5)::before { background: var(--warn); }
.metric:nth-child(n+8)::before { background: var(--accent-2); }
.metric:hover { transform: translateY(-2px); border-color: rgba(94, 234, 212, 0.45); }
.metric .label {
  color: var(--muted); font-size: 0.75rem; font-weight: 500;
  letter-spacing: 0.02em; line-height: 1.3;
}
.metric .value {
  margin-top: 0.45rem;
  font-family: Fraunces, Georgia, serif;
  font-size: clamp(1.35rem, 2.4vw, 1.75rem);
  font-weight: 700; letter-spacing: -0.02em;
  color: var(--text); font-variant-numeric: tabular-nums;
}
#events { list-style: none; padding: 0; margin: 0; max-height: 28rem; overflow: auto; }
#events li {
  display: grid; gap: 0.2rem;
  margin-bottom: 0.55rem; padding: 0.7rem 0.8rem;
  border-radius: 12px;
  border: 1px solid rgba(110, 231, 183, 0.12);
  background: rgba(6, 30, 24, 0.35);
  font-size: 0.86rem; color: var(--muted);
  animation: fade 0.35s ease both;
}
.tag-ok { color: var(--ok); font-weight: 600; }
.tag-denied, .tag-blocked, .tag-failed { color: var(--danger); font-weight: 600; }
#updated { color: var(--muted); font-size: 0.8rem; margin-top: 0.85rem; }
@keyframes rise {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes fade {
  from { opacity: 0; }
  to { opacity: 1; }
}
</style>
</head>
<body>
<div class="shell">
  <header class="hero">
    <div>
      <p class="eyebrow">AIAM Day 2</p>
      <h1>Tool Execution &amp; Validation</h1>
      <p class="sub">Live Layer 3 metrics — schema checks, permission gates, and unsafe expression blocking.</p>
      <div class="layers">
        <span class="layer-chip">L3 Tools</span>
        <span class="layer-chip">Schema validation</span>
        <span class="layer-chip">Permission RBAC</span>
        <span class="layer-chip">Sandbox eval</span>
      </div>
    </div>
    <div class="actions">
      <button id="demoBtn" onclick="runDemo()">Run demo</button>
      <span id="status"></span>
    </div>
  </header>
  <main class="layout">
    <section class="pane metrics-pane">
      <div class="pane-head">
        <h2>Live metrics</h2>
        <span>Auto-refresh every 1s</span>
      </div>
      <div class="grid" id="metrics">Loading metrics…</div>
    </section>
    <aside class="pane events-pane">
      <div class="pane-head">
        <h2>Recent events</h2>
        <span>Latest 10</span>
      </div>
      <ul id="events"><li>No events yet — run the demo.</li></ul>
      <div id="updated"></div>
    </aside>
  </main>
</div>
<script>
function fmt(n){ return (typeof n === 'number') ? n : 0; }
function esc(value){
  return String(value == null ? '' : value)
    .replaceAll('&', '&amp;').replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;').replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}
function eventStatus(e){
  if (!e.expected) return e.status || 'ok';
  if (e.status === 'blocked') return 'expected block';
  if (e.status === 'denied') return 'expected deny';
  return 'expected reject';
}
function render(d){
  document.getElementById('metrics').innerHTML =
    '<div class="metric"><div class="label">Tool calls total</div><div class="value">'+fmt(d.tool_calls_total)+'</div></div>'+
    '<div class="metric"><div class="label">OK</div><div class="value">'+fmt(d.tool_calls_ok)+'</div></div>'+
    '<div class="metric"><div class="label">Denied</div><div class="value">'+fmt(d.tool_calls_denied)+'</div></div>'+
    '<div class="metric"><div class="label">Failed</div><div class="value">'+fmt(d.tool_calls_failed)+'</div></div>'+
    '<div class="metric"><div class="label">Unsafe blocked</div><div class="value">'+fmt(d.tool_calls_unsafe_blocked)+'</div></div>'+
    '<div class="metric"><div class="label">Avg latency (ms)</div><div class="value">'+fmt(d.latency_ms_avg)+'</div></div>'+
    '<div class="metric"><div class="label">Demo runs</div><div class="value">'+fmt(d.demo_runs)+'</div></div>'+
    '<div class="metric"><div class="label">calculate</div><div class="value">'+fmt(d.calculate_calls)+'</div></div>'+
    '<div class="metric"><div class="label">echo</div><div class="value">'+fmt(d.echo_calls)+'</div></div>'+
    '<div class="metric"><div class="label">write_log</div><div class="value">'+fmt(d.write_log_calls)+'</div></div>';
  var events = d.recent_events || [];
  var ul = document.getElementById('events');
  if (!events.length) {
    ul.innerHTML = '<li>No events yet — run the demo.</li>';
  } else {
    ul.innerHTML = events.map(function(e){
      var cls = 'tag-' + (e.status||'ok');
      var when = e.timestamp ? new Date(e.timestamp).toLocaleTimeString() : '';
      return '<li data-event-id="'+fmt(e.id)+'"><span class="'+cls+'">['
        + esc(eventStatus(e))+']</span> '+esc(e.label||e.tool||'')
        + ' · #'+fmt(e.id)+' · '+esc(when)+' · '+fmt(e.latency_ms)+'ms'
        + '<br>'+esc(e.detail||'')+'</li>';
    }).join('');
  }
  document.getElementById('updated').textContent = 'Last updated: ' + new Date().toLocaleTimeString();
}
function refresh(){
  fetch('/metrics?t='+Date.now()).then(function(r){ return r.json(); }).then(render)
    .catch(function(){ document.getElementById('metrics').innerHTML = 'Error loading metrics'; });
}
function runDemo(){
  var btn = document.getElementById('demoBtn');
  var st = document.getElementById('status');
  btn.disabled = true; st.textContent = 'Running demo…';
  fetch('/demo', { method:'POST' }).then(function(r){ return r.json(); }).then(function(d){
    render(d.metrics || d);
    st.textContent = 'Demo complete — metrics updated.';
    btn.disabled = false;
    setTimeout(function(){ st.textContent=''; }, 2500);
  }).catch(function(e){
    st.textContent = 'Error: ' + e;
    btn.disabled = false;
  });
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
