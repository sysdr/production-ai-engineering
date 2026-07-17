"""AIAM Day 6 — FastAPI metrics API and live observability dashboard."""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse, Response
from pydantic import BaseModel, Field

from observability.logging_config import setup_logger
from observability.metrics import METRICS
from observability.service import ObservabilityService

log = setup_logger("aiam.obs")
svc: ObservabilityService = ObservabilityService()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global svc
    svc = ObservabilityService()
    log.info("service_ready", extra={"route": "startup", "status": 200})
    yield


app = FastAPI(
    title="AIAM Day 6 — Observability Stack",
    version="1.0.0",
    lifespan=lifespan,
)


class SimulateBody(BaseModel):
    route: str | None = Field(default=None, max_length=64)


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "healthy", "service": "aiam-day06"}


FAVICON_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
    '<rect width="32" height="32" rx="8" fill="#0b1f2a"/>'
    '<text x="16" y="22" text-anchor="middle" font-size="14" '
    'font-family="sans-serif" font-weight="700" fill="#38bdf8">O6</text>'
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


@app.post("/simulate")
def simulate(body: SimulateBody) -> dict[str, Any]:
    return svc.simulate_request(body.route)


@app.post("/demo")
def run_demo() -> dict[str, Any]:
    return svc.run_demo()


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>AIAM Day 6 — Observability Stack Dashboard</title>
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="shortcut icon" href="/favicon.ico">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=Source+Sans+3:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root {
  --bg: #061018;
  --bg-2: #0b1f2a;
  --panel: rgba(14, 45, 58, 0.62);
  --panel-solid: #123040;
  --line: rgba(56, 189, 248, 0.28);
  --text: #e8f6fb;
  --muted: #8fb6c6;
  --accent: #38bdf8;
  --accent-2: #0ea5e9;
  --warn: #fbbf24;
  --danger: #fca5a5;
  --ok: #86efac;
  --shadow: 0 18px 50px rgba(2, 12, 18, 0.45);
}
* { box-sizing: border-box; }
body {
  margin: 0; min-height: 100vh; color: var(--text);
  font-family: "Source Sans 3", system-ui, sans-serif;
  background:
    radial-gradient(900px 520px at 88% -8%, rgba(56, 189, 248, 0.16), transparent 55%),
    radial-gradient(700px 480px at -5% 20%, rgba(14, 165, 233, 0.12), transparent 50%),
    linear-gradient(165deg, var(--bg-2) 0%, var(--bg) 55%, #03080c 100%);
  background-attachment: fixed;
}
.shell { max-width: 1180px; margin: 0 auto; padding: 1.75rem 1.5rem 2.5rem; }
.hero {
  display: flex; flex-wrap: wrap; justify-content: space-between; align-items: flex-end;
  gap: 1.25rem; margin-bottom: 1.5rem; padding: 1.5rem 1.6rem;
  border: 1px solid var(--line); border-radius: 20px;
  background: linear-gradient(135deg, rgba(56, 189, 248, 0.12), transparent 42%), var(--panel);
  box-shadow: var(--shadow);
}
.eyebrow { margin: 0 0 0.4rem; font-size: 0.75rem; font-weight: 600; letter-spacing: 0.16em; text-transform: uppercase; color: var(--accent); }
.hero h1 { margin: 0; font-family: Fraunces, Georgia, serif; font-size: clamp(1.7rem, 3.5vw, 2.35rem); }
.sub { margin: 0.55rem 0 0; color: var(--muted); max-width: 40rem; line-height: 1.45; }
.chips { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-top: 0.9rem; }
.chip { font-size: 0.72rem; font-weight: 600; padding: 0.28rem 0.55rem; border-radius: 999px; border: 1px solid var(--line); color: var(--muted); }
.actions { display: flex; flex-direction: column; align-items: flex-end; gap: 0.45rem; }
button {
  background: linear-gradient(180deg, #7dd3fc, var(--accent)); color: #06202b; border: none;
  border-radius: 999px; padding: 0.8rem 1.35rem; font-weight: 700; cursor: pointer;
}
button:disabled { opacity: 0.55; cursor: not-allowed; }
#status { color: var(--muted); font-size: 0.85rem; min-height: 1.2em; }
.layout { display: grid; gap: 1.1rem; grid-template-columns: minmax(0, 1.7fr) minmax(280px, 1fr); }
@media (max-width: 900px) { .layout { grid-template-columns: 1fr; } }
.pane { border: 1px solid var(--line); border-radius: 18px; background: var(--panel); padding: 1.15rem 1.2rem; box-shadow: var(--shadow); }
.pane-head { display: flex; justify-content: space-between; margin-bottom: 0.95rem; }
.pane-head h2 { margin: 0; font-family: Fraunces, Georgia, serif; font-size: 1.15rem; }
.pane-head span { color: var(--muted); font-size: 0.8rem; }
.grid { display: grid; gap: 0.75rem; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); }
.metric { background: var(--panel-solid); border: 1px solid rgba(255,255,255,0.06); border-radius: 14px; padding: 0.95rem; }
.metric .label { color: var(--muted); font-size: 0.75rem; }
.metric .value { margin-top: 0.45rem; font-family: Fraunces, Georgia, serif; font-size: 1.5rem; font-weight: 700; font-variant-numeric: tabular-nums; }
.metric .value.warn { color: var(--warn); }
.metric .value.danger { color: var(--danger); }
.metric .value.ok { color: var(--ok); }
#events { list-style: none; padding: 0; margin: 0; max-height: 30rem; overflow: auto; }
#events li { margin-bottom: 0.55rem; padding: 0.7rem 0.8rem; border-radius: 12px; border: 1px solid rgba(56, 189, 248, 0.12); background: rgba(4, 14, 20, 0.35); font-size: 0.86rem; color: var(--muted); }
.tag-INFO { color: var(--ok); font-weight: 600; }
.tag-WARNING { color: var(--warn); font-weight: 600; }
.tag-ERROR { color: var(--danger); font-weight: 600; }
#updated { color: var(--muted); font-size: 0.8rem; margin-top: 0.85rem; }
.routes { margin-top: 1rem; }
.routes table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
.routes th, .routes td { text-align: left; padding: 0.4rem 0.5rem; border-bottom: 1px solid rgba(56,189,248,0.12); }
.routes th { color: var(--muted); font-weight: 600; }
</style>
</head>
<body>
<div class="shell">
  <header class="hero">
    <div>
      <p class="eyebrow">AIAM Day 6</p>
      <h1>Observability Stack</h1>
      <p class="sub">Structured JSON logs, a latency histogram (p50/p95/p99), and RED metrics (Rate, Errors, Duration) for a production AI gateway.</p>
      <div class="chips">
        <span class="chip">JSON logging</span>
        <span class="chip">Latency histogram</span>
        <span class="chip">p50 / p95 / p99</span>
        <span class="chip">Error rate</span>
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
      <div class="routes">
        <div class="pane-head"><h2>Per-route</h2><span>traffic breakdown</span></div>
        <table><thead><tr><th>Route</th><th>Requests</th><th>Errors</th></tr></thead>
        <tbody id="routes"><tr><td colspan="3">No traffic yet — run the demo.</td></tr></tbody></table>
      </div>
    </section>
    <aside class="pane">
      <div class="pane-head"><h2>Recent log events</h2><span>Latest 12</span></div>
      <ul id="events"><li>No events yet — run the demo.</li></ul>
      <div id="updated"></div>
    </aside>
  </main>
</div>
<script>
function fmt(n){ return (typeof n === 'number') ? n : 0; }
function pct(n){ return (typeof n === 'number') ? (n * 100).toFixed(1) + '%' : '0%'; }
function esc(v){ return String(v==null?'':v).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;'); }
function metric(label, value, cls){
  return '<div class="metric"><div class="label">'+label+'</div><div class="value '+(cls||'')+'">'+value+'</div></div>';
}
function render(d){
  document.getElementById('metrics').innerHTML =
    metric('Requests total', fmt(d.requests_total)) +
    metric('OK', fmt(d.requests_ok), 'ok') +
    metric('Errors', fmt(d.requests_error), fmt(d.requests_error) > 0 ? 'danger' : '') +
    metric('Error rate', pct(d.error_rate), fmt(d.error_rate) > 0 ? 'warn' : 'ok') +
    metric('Throughput (rps)', fmt(d.throughput_rps)) +
    metric('p50 latency (ms)', fmt(d.latency_p50_ms)) +
    metric('p95 latency (ms)', fmt(d.latency_p95_ms), 'warn') +
    metric('p99 latency (ms)', fmt(d.latency_p99_ms), 'danger') +
    metric('Avg latency (ms)', fmt(d.latency_avg_ms)) +
    metric('Max latency (ms)', fmt(d.latency_max_ms)) +
    metric('Logs INFO', fmt(d.logs_info), 'ok') +
    metric('Logs WARN', fmt(d.logs_warn), 'warn') +
    metric('Logs ERROR', fmt(d.logs_error), 'danger') +
    metric('Demo runs', fmt(d.demo_runs));

  var routes = d.routes || {};
  var keys = Object.keys(routes);
  var rt = document.getElementById('routes');
  if (!keys.length) { rt.innerHTML = '<tr><td colspan="3">No traffic yet — run the demo.</td></tr>'; }
  else {
    rt.innerHTML = keys.map(function(k){
      var r = routes[k];
      return '<tr><td>'+esc(k)+'</td><td>'+fmt(r.count)+'</td><td>'+fmt(r.errors)+'</td></tr>';
    }).join('');
  }

  var events = d.recent_events || [];
  var ul = document.getElementById('events');
  if (!events.length) { ul.innerHTML = '<li>No events yet — run the demo.</li>'; }
  else {
    ul.innerHTML = events.map(function(e){
      var cls = 'tag-' + (e.level || 'INFO');
      var when = e.timestamp ? new Date(e.timestamp).toLocaleTimeString() : '';
      return '<li><span class="'+cls+'">['+esc(e.level)+']</span> '+esc(e.route||'')
        +' · '+fmt(e.status)+' · '+fmt(e.latency_ms)+'ms · '+esc(when)+'<br>'+esc(e.detail||'')+'</li>';
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
