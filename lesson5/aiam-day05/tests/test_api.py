import pytest
from fastapi.testclient import TestClient

from app import app
from security.metrics import METRICS


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
    assert metrics["scans_total"] > 0
    assert metrics["scans_clean"] > 0
    assert metrics["scans_blocked"] > 0
    assert metrics["secrets_detected"] > 0
    assert metrics["pii_detected"] > 0
    assert metrics["redactions_total"] > 0
    assert metrics["hmac_signs"] > 0
    assert metrics["hmac_verifications_ok"] > 0
    assert metrics["hmac_verifications_fail"] > 0
    assert metrics["latency_ms_avg"] > 0
    assert len(body["scans"]) >= 6
    events = metrics["recent_events"]
    assert events
    assert all(event["id"] > 0 and event["timestamp"] for event in events)


def test_scan_endpoint(client):
    r = client.post(
        "/scan",
        json={"text": "leak sk-abc123abc123abc123abc123abc123ab", "label": "api"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["clean"] is False
    assert "openai_key" in body["findings"]


def test_sign_verify_endpoint(client):
    signed = client.post("/sign", json={"payload": '{"ok":true}'})
    assert signed.status_code == 200
    sig = signed.json()["signature"]
    verified = client.post(
        "/verify", json={"payload": '{"ok":true}', "signature": sig}
    )
    assert verified.status_code == 200
    assert verified.json()["valid"] is True


def test_dashboard_html(client):
    r = client.get("/dashboard")
    assert r.status_code == 200
    assert "Security Hardening" in r.text
    assert "Run demo" in r.text
