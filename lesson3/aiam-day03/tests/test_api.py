import pytest
from fastapi.testclient import TestClient

from app import app
from memory.metrics import METRICS


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "healthy"
    assert body["service"] == "aiam-day03"


def test_demo_updates_metrics(client):
    before_demo = METRICS.snapshot()["demo_runs"]
    r = client.post("/demo")
    assert r.status_code == 200
    body = r.json()
    metrics = body["metrics"]
    assert metrics["demo_runs"] == before_demo + 1
    assert metrics["memory_ops_total"] > 0
    assert metrics["turns_stored"] > 0
    assert metrics["cache_hits"] > 0
    assert metrics["cache_misses"] > 0
    assert metrics["cache_hit_rate"] > 0
    assert metrics["ttl_evictions"] > 0
    assert metrics["latency_ms_avg"] > 0
    assert len(body["results"]) >= 4
    events = metrics["recent_events"]
    assert events
    assert all(event["id"] > 0 and event["timestamp"] for event in events)


def test_dashboard_html(client):
    r = client.get("/dashboard")
    assert r.status_code == 200
    assert "Memory Systems" in r.text
    assert "Run demo" in r.text
