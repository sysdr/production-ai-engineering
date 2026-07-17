import json
import logging

from observability.logging_config import JSONFormatter, setup_logger
from observability.metrics import Histogram, MetricsStore
from observability.service import ObservabilityService


def test_histogram_percentiles():
    h = Histogram()
    for v in range(1, 101):
        h.observe(v)
    assert h.count() == 100
    assert h.percentile(50) == 50
    assert h.percentile(95) == 95
    assert h.percentile(99) == 99
    assert h.maximum() == 100
    assert 50 <= h.avg() <= 51


def test_histogram_empty():
    h = Histogram()
    assert h.percentile(95) == 0.0
    assert h.avg() == 0.0
    assert h.maximum() == 0.0


def test_metrics_store_records_request():
    store = MetricsStore()
    store.record_request(
        route="/chat", status_code=200, latency_ms=120, level="INFO"
    )
    store.record_request(
        route="/chat", status_code=500, latency_ms=800, level="ERROR"
    )
    snap = store.snapshot()
    assert snap["requests_total"] == 2
    assert snap["requests_ok"] == 1
    assert snap["requests_error"] == 1
    assert snap["error_rate"] == 0.5
    assert snap["latency_max_ms"] == 800
    assert snap["logs_error"] == 1
    assert snap["routes"]["/chat"]["count"] == 2
    assert len(snap["recent_events"]) == 2


def test_json_formatter_emits_valid_json():
    record = logging.LogRecord(
        name="aiam.obs",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="hello",
        args=(),
        exc_info=None,
    )
    record.route = "/chat"
    record.status = 200
    record.latency_ms = 12.5
    record.request_id = "abc123"
    payload = json.loads(JSONFormatter().format(record))
    assert payload["level"] == "INFO"
    assert payload["route"] == "/chat"
    assert payload["status"] == 200
    assert payload["latency_ms"] == 12.5


def test_setup_logger_is_idempotent():
    a = setup_logger("aiam.test")
    b = setup_logger("aiam.test")
    assert a is b
    assert len(a.handlers) == 1


def test_service_demo_populates_metrics():
    svc = ObservabilityService(seed=7)
    result = svc.run_demo(count=40)
    m = result["metrics"]
    assert m["requests_total"] > 40
    assert m["requests_ok"] > 0
    assert m["requests_error"] > 0
    assert m["error_rate"] > 0
    assert m["latency_p50_ms"] > 0
    assert m["latency_p95_ms"] >= m["latency_p50_ms"]
    assert m["latency_p99_ms"] >= m["latency_p95_ms"]
    assert m["latency_max_ms"] > 0
    assert m["logs_info"] > 0
    assert m["logs_warn"] > 0
    assert m["logs_error"] > 0
    # METRICS is a process-wide singleton; other tests may have run demos too.
    assert m["demo_runs"] >= 1
    assert m["throughput_rps"] > 0
