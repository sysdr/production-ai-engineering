from tools.registry import ToolOrchestrator
from tools.metrics import METRICS

orch = ToolOrchestrator()


def test_calculate():
    r = orch.call("calculate", {"expression": "2 ** 10"}, ["read"])
    assert r.success and r.output == 1024
    assert r.latency_ms >= 1


def test_permission_denied():
    r = orch.call("write_log", {"message": "hi", "level": "INFO"}, ["read"])
    assert not r.success and r.error is not None and "Permission" in r.error


def test_unknown_tool():
    r = orch.call("hack_the_planet", {}, ["read", "write"])
    assert not r.success


def test_unsafe_expression():
    r = orch.call(
        "calculate",
        {"expression": "__import__('os').system('id')"},
        ["read"],
    )
    assert not r.success


def test_missing_param():
    r = orch.call("echo", {}, ["read"])
    assert not r.success and r.error is not None and "Missing" in r.error


def test_echo_ok():
    r = orch.call("echo", {"message": "hello"}, ["read"], label="echo-test")
    assert r.success and r.output == "hello"


def test_write_log_with_permission():
    r = orch.call(
        "write_log",
        {"message": "deploy", "level": "INFO"},
        ["read", "write"],
    )
    assert r.success and r.output == "logged"


def test_metrics_update_on_call():
    before = METRICS.snapshot()["tool_calls_total"]
    orch.call("calculate", {"expression": "1+1"}, ["read"], label="metrics")
    snap = METRICS.snapshot()
    assert snap["tool_calls_total"] == before + 1
    assert snap["tool_calls_ok"] >= 1
    assert snap["calculate_calls"] >= 1
    assert snap["latency_ms_avg"] > 0
