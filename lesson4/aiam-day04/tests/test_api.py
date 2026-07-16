import pytest
from fastapi.testclient import TestClient

from app import app
from ratelimit.metrics import METRICS


@pytest.fixture()
def client():
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
    assert metrics["requests_total"] > 0
    assert metrics["requests_allowed"] > 0
    assert metrics["requests_throttled"] > 0
    assert metrics["tokens_input_total"] > 0
    assert metrics["tokens_output_total"] > 0
    assert metrics["spend_usd_total"] > 0
    assert metrics["users_tracked"] > 0
    assert metrics["budget_alerts"] > 0
    assert metrics["latency_ms_avg"] > 0
    assert len(body["results"]) >= 3
    events = metrics["recent_events"]
    assert events
    assert all(event["id"] > 0 and event["timestamp"] for event in events)


def test_check_endpoint(client):
    r = client.post(
        "/check",
        json={
            "user_id": "api_user",
            "tier": "standard",
            "input_tokens": 1000,
            "output_tokens": 500,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["allowed"] is True
    assert body["cost_usd"] > 0


def test_dashboard_html(client):
    r = client.get("/dashboard")
    assert r.status_code == 200
    assert "Rate Limiting" in r.text
    assert "Run demo" in r.text
