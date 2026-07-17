#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
API="${API_URL:-http://127.0.0.1:8085}"
IMAGE="aiam-day06-observability"

echo "► Unit + API tests (pytest)"
if command -v docker >/dev/null 2>&1 && docker image inspect "$IMAGE" >/dev/null 2>&1; then
  docker run --rm "$IMAGE" python -m pytest tests/ -v
else
  PYTHONPATH=. python3 -m pytest tests/ -v
fi

echo ""
echo "► API smoke tests against $API"
curl -sf "$API/health" | grep -q healthy && echo "  health OK" || { echo "  health FAIL"; exit 1; }
curl -sf -X POST "$API/demo" -H "Content-Type: application/json" | tee /tmp/aiam-day06-demo.json | grep -q '"demo_runs"' && echo "  demo OK" || { echo "  demo FAIL"; exit 1; }

python3 - <<'PY'
import json
d = json.load(open("/tmp/aiam-day06-demo.json"))
m = d.get("metrics", d)
checks = {
    "requests_total": m.get("requests_total", 0),
    "requests_ok": m.get("requests_ok", 0),
    "requests_error": m.get("requests_error", 0),
    "error_rate": m.get("error_rate", 0),
    "throughput_rps": m.get("throughput_rps", 0),
    "latency_p50_ms": m.get("latency_p50_ms", 0),
    "latency_p95_ms": m.get("latency_p95_ms", 0),
    "latency_p99_ms": m.get("latency_p99_ms", 0),
    "latency_avg_ms": m.get("latency_avg_ms", 0),
    "latency_max_ms": m.get("latency_max_ms", 0),
    "logs_info": m.get("logs_info", 0),
    "logs_warn": m.get("logs_warn", 0),
    "logs_error": m.get("logs_error", 0),
    "demo_runs": m.get("demo_runs", 0),
}
print("  metrics:", checks)
for k, v in checks.items():
    assert float(v) > 0, f"{k} is zero"
print("  metrics non-zero OK")
PY

curl -sf "$API/metrics" | grep -q requests_total && echo "  /metrics OK" || { echo "  /metrics FAIL"; exit 1; }
curl -sf "$API/dashboard" | grep -q "Observability Stack" && echo "  /dashboard OK" || { echo "  /dashboard FAIL"; exit 1; }
echo "All tests passed."
