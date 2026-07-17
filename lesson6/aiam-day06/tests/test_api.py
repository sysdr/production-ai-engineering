import pytest
from fastapi.testclient import TestClient

from app import app
from observability.metrics import METRICS


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


def test_demo_updates_metrics(client):
    before = METRICS.snapshot()["demo_runs"]
    r = client.post("/demo")
    assert r.status_code == 200
    m = r.json()["metrics"]
    assert m["demo_runs"] == before + 1
    assert m["requests_total"] > 0
    assert m["requests_ok"] > 0
    assert m["requests_error"] > 0
    assert m["error_rate"] > 0
    assert m["latency_p50_ms"] > 0
    assert m["latency_p95_ms"] > 0
    assert m["latency_p99_ms"] > 0
    assert m["latency_avg_ms"] > 0
    assert m["latency_max_ms"] > 0
    assert m["logs_info"] > 0
    assert m["logs_warn"] > 0
    assert m["logs_error"] > 0
    assert m["throughput_rps"] > 0
    events = m["recent_events"]
    assert events
    assert all(e["id"] > 0 and e["timestamp"] for e in events)


def test_simulate_endpoint(client):
    r = client.post("/simulate", json={"route": "/chat"})
    assert r.status_code == 200
    body = r.json()
    assert body["route"] == "/chat"
    assert "latency_ms" in body


def test_metrics_endpoint(client):
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "requests_total" in r.json()


def test_dashboard_html(client):
    r = client.get("/dashboard")
    assert r.status_code == 200
    assert "Observability Stack" in r.text
    assert "Run demo" in r.text
