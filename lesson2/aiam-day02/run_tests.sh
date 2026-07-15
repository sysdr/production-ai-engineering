#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
API="${API_URL:-http://127.0.0.1:8081}"
IMAGE="aiam-day02-tools"

echo "► Unit tests (pytest)"
if command -v docker >/dev/null 2>&1 && docker image inspect "$IMAGE" >/dev/null 2>&1; then
  docker run --rm "$IMAGE" python -m pytest tests/ -v
else
  PYTHONPATH=. python3 -m pytest tests/ -v
fi

echo ""
echo "► API smoke tests against $API"
curl -sf "$API/health" | grep -q healthy && echo "  health OK" || { echo "  health FAIL"; exit 1; }
curl -sf -X POST "$API/demo" -H "Content-Type: application/json" | tee /tmp/aiam-day02-demo.json | grep -q '"demo_runs"' && echo "  demo OK" || { echo "  demo FAIL"; exit 1; }

python3 - <<'PY'
import json
d = json.load(open("/tmp/aiam-day02-demo.json"))
m = d.get("metrics", d)
checks = {
    "tool_calls_total": m.get("tool_calls_total", 0),
    "tool_calls_ok": m.get("tool_calls_ok", 0),
    "tool_calls_denied": m.get("tool_calls_denied", 0),
    "tool_calls_unsafe_blocked": m.get("tool_calls_unsafe_blocked", 0),
    "calculate_calls": m.get("calculate_calls", 0),
    "echo_calls": m.get("echo_calls", 0),
    "write_log_calls": m.get("write_log_calls", 0),
    "latency_ms_avg": m.get("latency_ms_avg", 0),
    "demo_runs": m.get("demo_runs", 0),
}
print("  metrics:", checks)
for k, v in checks.items():
    assert float(v) > 0, f"{k} is zero"
print("  metrics non-zero OK")
PY

curl -sf "$API/metrics" | grep -q tool_calls_total && echo "  /metrics OK" || { echo "  /metrics FAIL"; exit 1; }
curl -sf "$API/dashboard" | grep -q "Tool Execution" && echo "  /dashboard OK" || { echo "  /dashboard FAIL"; exit 1; }
echo "All tests passed."
