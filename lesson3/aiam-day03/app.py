"""AIAM Day 3 — FastAPI metrics API and live memory dashboard."""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse, Response
from pydantic import BaseModel, Field

from memory.metrics import METRICS
from memory.service import MemoryService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)-12s] %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)

svc: MemoryService = MemoryService(redis_url=os.getenv("REDIS_URL"))


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global svc
    svc = MemoryService(redis_url=os.getenv("REDIS_URL"))
    svc.refresh_redis_status()
    yield


app = FastAPI(
    title="AIAM Day 3 — Memory Systems",
    version="1.0.0",
    lifespan=lifespan,
)


class StoreBody(BaseModel):
    session_id: str = Field(min_length=1, max_length=128)
    user: str = Field(min_length=1, max_length=4000)
    assistant: str = Field(min_length=1, max_length=4000)


class CacheBody(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    value: str = Field(default="", max_length=4000)


@app.get("/health")
def health() -> dict[str, Any]:
    redis_ok = svc.refresh_redis_status()
    return {
        "status": "healthy",
        "service": "aiam-day03",
        "redis": "connected" if redis_ok else "offline",
    }


FAVICON_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
    '<rect width="32" height="32" rx="8" fill="#0c1929"/>'
    '<text x="16" y="22" text-anchor="middle" font-size="14" '
    'font-family="sans-serif" font-weight="700" fill="#38bdf8">M3</text>'
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


@app.post("/memory/store")
def memory_store(body: StoreBody) -> dict[str, Any]:
    return svc.store_turn(body.session_id, body.user, body.assistant, label="api")


@app.get("/memory/{session_id}")
def memory_get(session_id: str) -> dict[str, Any]:
    history = svc.get_history(session_id, label="api")
    return {"session_id": session_id, "history": history}


@app.post("/cache/lookup")
def cache_lookup(body: CacheBody) -> dict[str, Any]:
    return svc.cache_lookup(body.query, label="api")


@app.post("/cache/store")
def cache_store(body: CacheBody) -> dict[str, Any]:
    if not body.value:
        return {"error": "value required"}
    return svc.cache_store(body.query, body.value, label="api")


@app.post("/demo")
def run_demo() -> dict[str, Any]:
    return svc.run_demo()


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>AIAM Day 3 — Memory Systems Dashboard</title>
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="shortcut icon" href="/favicon.ico">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Literata:opsz,wght@7..72,500;7..72,700&family=Source+Sans+3:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root {
  --bg: #07111c;
  --bg-2: #0c1929;
  --panel: rgba(20, 48, 78, 0.55);
  --panel-solid: #14304e;
  --line: rgba(56, 189, 248, 0.28);
  --text: #e8f4fc;
  --muted: #8fb4cc;
  --accent: #38bdf8;
  --accent-2: #0ea5e9;
  --warn: #fbbf24;
  --danger: #fca5a5;
  --ok: #86efac;
  --shadow: 0 18px 50px rgba(4, 16, 32, 0.45);
}
* { box-sizing: border-box; }
body {
  margin: 0;
  min-height: 100vh;
  color: var(--text);
  font-family: "Source Sans 3", system-ui, sans-serif;
  background:
    radial-gradient(900px 520px at 88% -8%, rgba(56, 189, 248, 0.18), transparent 55%),
    radial-gradient(700px 480px at -5% 20%, rgba(14, 165, 233, 0.14), transparent 50%),
    linear-gradient(165deg, var(--bg-2) 0%, var(--bg) 55%, #040a12 100%);
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
    linear-gradient(135deg, rgba(56, 189, 248, 0.14), transparent 42%),
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
  font-family: Literata, Georgia, serif;
  font-size: clamp(1.7rem, 3.5vw, 2.35rem);
  font-weight: 700; line-height: 1.15; letter-spacing: -0.02em;
}
.sub { margin: 0.55rem 0 0; color: var(--muted); max-width: 40rem; line-height: 1.45; }
.layers {
  display: flex; flex-wrap: wrap; gap: 0.4rem; margin-top: 0.9rem;
}
.layer-chip {
  font-size: 0.72rem; font-weight: 600; letter-spacing: 0.04em;
  padding: 0.28rem 0.55rem; border-radius: 999px;
  border: 1px solid var(--line); color: var(--muted); background: rgba(6, 20, 36, 0.35);
}
.actions {
  display: flex; flex-direction: column; align-items: flex-end; gap: 0.45rem;
}
button {
  background: linear-gradient(180deg, #7dd3fc, var(--accent));
  color: #0c1929; border: none; border-radius: 999px;
  padding: 0.8rem 1.35rem; font-weight: 600; cursor: pointer; font-size: 0.95rem;
  box-shadow: 0 10px 24px rgba(14, 165, 233, 0.35);
  transition: transform 0.15s ease, box-shadow 0.15s ease, opacity 0.15s ease;
}
button:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 14px 28px rgba(14, 165, 233, 0.45); }
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
  font-family: Literata, Georgia, serif;
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
.metric:nth-child(4)::before, .metric:nth-child(5)::before { background: var(--warn); }
.metric:nth-child(7)::before { background: var(--ok); }
.metric:nth-child(n+9)::before { background: var(--accent-2); }
.metric:hover { transform: translateY(-2px); border-color: rgba(56, 189, 248, 0.45); }
.metric .label {
  color: var(--muted); font-size: 0.75rem; font-weight: 500;
  letter-spacing: 0.02em; line-height: 1.3;
}
.metric .value {
  margin-top: 0.45rem;
  font-family: Literata, Georgia, serif;
  font-size: clamp(1.35rem, 2.4vw, 1.75rem);
  font-weight: 700; letter-spacing: -0.02em;
  color: var(--text); font-variant-numeric: tabular-nums;
}
#events { list-style: none; padding: 0; margin: 0; max-height: 28rem; overflow: auto; }
#events li {
  display: grid; gap: 0.2rem;
  margin-bottom: 0.55rem; padding: 0.7rem 0.8rem;
  border-radius: 12px;
  border: 1px solid rgba(56, 189, 248, 0.12);
  background: rgba(6, 20, 36, 0.35);
  font-size: 0.86rem; color: var(--muted);
  animation: fade 0.35s ease both;
}
.tag-ok { color: var(--ok); font-weight: 600; }
.tag-error { color: var(--danger); font-weight: 600; }
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
      <p class="eyebrow">AIAM Day 3</p>
      <h1>Memory Systems</h1>
      <p class="sub">Live metrics for sliding-window sessions, semantic cache hits, TTL eviction, and Redis-backed persistence.</p>
      <div class="layers">
        <span class="layer-chip">Short-term window</span>
        <span class="layer-chip">Semantic cache</span>
        <span class="layer-chip">TTL eviction</span>
        <span class="layer-chip">Redis store</span>
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
function pct(n){ return (typeof n === 'number') ? (n * 100).toFixed(1) + '%' : '0%'; }
function esc(value){
  return String(value == null ? '' : value)
    .replaceAll('&', '&amp;').replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;').replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}
function render(d){
  document.getElementById('metrics').innerHTML =
    '<div class="metric"><div class="label">Memory ops</div><div class="value">'+fmt(d.memory_ops_total)+'</div></div>'+
    '<div class="metric"><div class="label">Turns stored</div><div class="value">'+fmt(d.turns_stored)+'</div></div>'+
    '<div class="metric"><div class="label">Sessions active</div><div class="value">'+fmt(d.sessions_active)+'</div></div>'+
    '<div class="metric"><div class="label">Cache hits</div><div class="value">'+fmt(d.cache_hits)+'</div></div>'+
    '<div class="metric"><div class="label">Cache misses</div><div class="value">'+fmt(d.cache_misses)+'</div></div>'+
    '<div class="metric"><div class="label">Hit rate</div><div class="value">'+pct(d.cache_hit_rate)+'</div></div>'+
    '<div class="metric"><div class="label">TTL evictions</div><div class="value">'+fmt(d.ttl_evictions)+'</div></div>'+
    '<div class="metric"><div class="label">Redis ops</div><div class="value">'+fmt(d.redis_ops)+'</div></div>'+
    '<div class="metric"><div class="label">Redis</div><div class="value">'+(d.redis_connected ? 'ON' : 'OFF')+'</div></div>'+
    '<div class="metric"><div class="label">Avg latency (ms)</div><div class="value">'+fmt(d.latency_ms_avg)+'</div></div>'+
    '<div class="metric"><div class="label">Demo runs</div><div class="value">'+fmt(d.demo_runs)+'</div></div>';
  var events = d.recent_events || [];
  var ul = document.getElementById('events');
  if (!events.length) {
    ul.innerHTML = '<li>No events yet — run the demo.</li>';
  } else {
    ul.innerHTML = events.map(function(e){
      var cls = 'tag-' + (e.status||'ok');
      var when = e.timestamp ? new Date(e.timestamp).toLocaleTimeString() : '';
      return '<li data-event-id="'+fmt(e.id)+'"><span class="'+cls+'">['
        + esc(e.status||'ok')+']</span> '+esc(e.label||e.op||'')
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
