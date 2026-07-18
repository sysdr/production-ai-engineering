import pytest
from fastapi.testclient import TestClient

from app import app
from sandbox.metrics import METRICS


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


def test_execute_safe(client):
    r = client.post("/execute", json={"code": "print(2+2)", "label": "add"})
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert "4" in body["output"]


def test_execute_blocked(client):
    r = client.post("/execute", json={"code": "import os\nprint(1)", "label": "os"})
    assert r.status_code == 200
    body = r.json()
    assert body["blocked"] is True
    assert body["ok"] is False


def test_demo_updates_metrics(client):
    before = METRICS.snapshot()["demo_runs"]
    r = client.post("/demo")
    assert r.status_code == 200
    m = r.json()["metrics"]
    assert m["demo_runs"] == before + 1
    assert m["executions_total"] > 0
    assert m["executions_ok"] > 0
    assert m["executions_blocked"] > 0
    assert m["executions_timeout"] > 0
    assert m["executions_error"] > 0
    assert m["allowed_module_hits"] > 0
    assert m["blocked_module_hits"] > 0
    assert m["duration_avg_ms"] > 0
    assert m["duration_max_ms"] > 0
    assert m["duration_p50_ms"] > 0
    assert m["duration_p95_ms"] > 0
    assert m["duration_p99_ms"] > 0
    assert m["throughput_eps"] > 0
    assert m["block_rate"] > 0
    assert m["timeout_rate"] > 0
    assert m["ok_rate"] > 0
    assert m["recent_events"]


def test_metrics_endpoint(client):
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "executions_total" in r.json()


def test_dashboard_html(client):
    r = client.get("/dashboard")
    assert r.status_code == 200
    assert "Sandboxed Code Execution" in r.text
    assert "Run demo" in r.text
