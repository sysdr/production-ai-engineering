import pytest
from fastapi.testclient import TestClient

from app import app
from tools.metrics import METRICS


@pytest.fixture()
def client():
    # Context manager runs FastAPI lifespan (and avoids stale TestClient state).
    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


def test_demo_updates_metrics(client):
    before_demo = METRICS.snapshot()["demo_runs"]
    r = client.post("/demo")
    assert r.status_code == 200
    body = r.json()
    metrics = body["metrics"]
    assert metrics["demo_runs"] == before_demo + 1
    assert metrics["tool_calls_total"] > 0
    assert metrics["tool_calls_ok"] > 0
    assert metrics["tool_calls_denied"] > 0
    assert metrics["tool_calls_unsafe_blocked"] > 0
    assert metrics["calculate_calls"] > 0
    assert metrics["echo_calls"] > 0
    assert metrics["write_log_calls"] > 0
    assert metrics["latency_ms_avg"] > 0
    assert len(body["results"]) >= 5
    events = metrics["recent_events"]
    assert events
    assert all(event["id"] > 0 and event["timestamp"] for event in events)
    assert any(event["expected"] for event in events)


def test_dashboard_html(client):
    r = client.get("/dashboard")
    assert r.status_code == 200
    assert "Tool Execution" in r.text
    assert "Run demo" in r.text
