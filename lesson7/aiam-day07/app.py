"""FastAPI service for AIAM Day 07 — Sandboxed Code Execution."""
from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel, Field

from sandbox.metrics import METRICS
from sandbox.service import SandboxService

app = FastAPI(title="AIAM Day 07 — Sandboxed Code Execution", version="1.0.0")
svc = SandboxService()

FAVICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
<rect width="64" height="64" rx="14" fill="#0f2a24"/>
<path d="M18 34h28v6H18zm4-12h20v6H22z" fill="#34d399"/>
</svg>"""


class ExecuteBody(BaseModel):
    code: str = Field(min_length=1, max_length=8000)
    label: str = Field(default="adhoc", max_length=80)
    timeout: float = Field(default=2.0, gt=0.05, le=10.0)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy", "service": "aiam-day07-sandbox"}


@app.get("/favicon.svg")
def favicon_svg() -> Response:
    return Response(content=FAVICON_SVG, media_type="image/svg+xml")


@app.get("/favicon.ico")
def favicon_ico() -> Response:
    return Response(content=FAVICON_SVG, media_type="image/svg+xml")


@app.get("/metrics")
def metrics() -> dict[str, Any]:
    return METRICS.snapshot()


@app.post("/execute")
def execute(body: ExecuteBody) -> dict[str, Any]:
    return svc.execute(body.code, timeout=body.timeout, label=body.label)


@app.post("/demo")
def run_demo() -> dict[str, Any]:
    return svc.run_demo()


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>AIAM Day 7 — Sandboxed Code Execution Dashboard</title>
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="shortcut icon" href="/favicon.ico">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=Source+Sans+3:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root {
  --bg: #061410;
  --bg-2: #0b221c;
  --panel: rgba(14, 48, 40, 0.62);
  --panel-solid: #12362e;
  --line: rgba(52, 211, 153, 0.28);
  --text: #e8fbf4;
  --muted: #8fc6b4;
  --accent: #34d399;
  --accent-2: #10b981;
  --warn: #fbbf24;
  --danger: #fca5a5;
  --ok: #86efac;
  --shadow: 0 18px 50px rgba(2, 18, 12, 0.45);
}
* { box-sizing: border-box; }
body {
  margin: 0; min-height: 100vh; color: var(--text);
  font-family: "Source Sans 3", system-ui, sans-serif;
  background:
    radial-gradient(900px 520px at 88% -8%, rgba(52, 211, 153, 0.16), transparent 55%),
    radial-gradient(700px 480px at -5% 20%, rgba(16, 185, 129, 0.12), transparent 50%),
    linear-gradient(165deg, var(--bg-2) 0%, var(--bg) 55%, #030c09 100%);
  background-attachment: fixed;
}
.shell { max-width: 1180px; margin: 0 auto; padding: 1.75rem 1.5rem 2.5rem; }
.hero {
  display: flex; flex-wrap: wrap; justify-content: space-between; align-items: flex-end;
  gap: 1.25rem; margin-bottom: 1.5rem; padding: 1.5rem 1.6rem;
  border: 1px solid var(--line); border-radius: 20px;
  background: linear-gradient(135deg, rgba(52, 211, 153, 0.12), transparent 42%), var(--panel);
  box-shadow: var(--shadow);
}
.eyebrow { margin: 0 0 0.4rem; font-size: 0.75rem; font-weight: 600; letter-spacing: 0.16em; text-transform: uppercase; color: var(--accent); }
.hero h1 { margin: 0; font-family: Fraunces, Georgia, serif; font-size: clamp(1.7rem, 3.5vw, 2.35rem); }
.sub { margin: 0.55rem 0 0; color: var(--muted); max-width: 40rem; line-height: 1.45; }
.chips { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-top: 0.9rem; }
.chip { font-size: 0.72rem; font-weight: 600; padding: 0.28rem 0.55rem; border-radius: 999px; border: 1px solid var(--line); color: var(--muted); }
.actions { display: flex; flex-direction: column; align-items: flex-end; gap: 0.45rem; }
button {
  background: linear-gradient(180deg, #6ee7b7, var(--accent)); color: #06201a; border: none;
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
#events li { margin-bottom: 0.55rem; padding: 0.7rem 0.8rem; border-radius: 12px; border: 1px solid rgba(52, 211, 153, 0.12); background: rgba(4, 20, 14, 0.35); font-size: 0.86rem; color: var(--muted); }
.tag-OK { color: var(--ok); font-weight: 600; }
.tag-BLOCKED { color: var(--danger); font-weight: 600; }
.tag-TIMEOUT { color: var(--warn); font-weight: 600; }
.tag-ERROR { color: var(--danger); font-weight: 600; }
#updated { color: var(--muted); font-size: 0.8rem; margin-top: 0.85rem; }
</style>
</head>
<body>
<div class="shell">
  <header class="hero">
    <div>
      <p class="eyebrow">AIAM Day 7</p>
      <h1>Sandboxed Code Execution</h1>
      <p class="sub">Subprocess isolation, allowlisted imports, and timeout enforcement for untrusted AI-generated code.</p>
      <div class="chips">
        <span class="chip">Subprocess isolation</span>
        <span class="chip">Blocked dangerous imports</span>
        <span class="chip">Timeout enforcement</span>
        <span class="chip">Blocked OS / network</span>
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
      <div class="pane-head"><h2>Recent executions</h2><span>Latest 12</span></div>
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
    metric('Executions total', fmt(d.executions_total)) +
    metric('OK', fmt(d.executions_ok), 'ok') +
    metric('Blocked', fmt(d.executions_blocked), fmt(d.executions_blocked) > 0 ? 'danger' : '') +
    metric('Timeouts', fmt(d.executions_timeout), fmt(d.executions_timeout) > 0 ? 'warn' : '') +
    metric('Errors', fmt(d.executions_error), fmt(d.executions_error) > 0 ? 'danger' : '') +
    metric('OK rate', pct(d.ok_rate), 'ok') +
    metric('Block rate', pct(d.block_rate), fmt(d.block_rate) > 0 ? 'warn' : 'ok') +
    metric('Timeout rate', pct(d.timeout_rate), fmt(d.timeout_rate) > 0 ? 'warn' : 'ok') +
    metric('Throughput (eps)', fmt(d.throughput_eps)) +
    metric('Allowed imports', fmt(d.allowed_module_hits), 'ok') +
    metric('Blocked imports', fmt(d.blocked_module_hits), 'danger') +
    metric('p50 duration (ms)', fmt(d.duration_p50_ms)) +
    metric('p95 duration (ms)', fmt(d.duration_p95_ms), 'warn') +
    metric('p99 duration (ms)', fmt(d.duration_p99_ms), 'danger') +
    metric('Avg duration (ms)', fmt(d.duration_avg_ms)) +
    metric('Max duration (ms)', fmt(d.duration_max_ms)) +
    metric('Demo runs', fmt(d.demo_runs));

  var events = d.recent_events || [];
  var ul = document.getElementById('events');
  if (!events.length) { ul.innerHTML = '<li>No events yet — run the demo.</li>'; }
  else {
    ul.innerHTML = events.slice(0, 12).map(function(e){
      var cls = 'tag-' + (e.outcome || 'OK');
      var when = e.timestamp ? new Date(e.timestamp).toLocaleTimeString() : '';
      return '<li><span class="'+cls+'">['+esc(e.outcome)+']</span> '+esc(e.label||'')
        +' · '+fmt(e.duration_ms)+'ms · '+esc(when)+'<br>'+esc(e.detail||'')+'</li>';
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
