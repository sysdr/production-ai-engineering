#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
API="${API_URL:-http://127.0.0.1:8086}"
IMAGE="aiam-day07-sandbox"

echo "► Unit + API tests (pytest)"
if command -v docker >/dev/null 2>&1 && docker image inspect "$IMAGE" >/dev/null 2>&1; then
  docker run --rm "$IMAGE" python -m pytest tests/ -v
else
  PYTHONPATH=. python3 -m pytest tests/ -v
fi

echo ""
echo "► API smoke tests against $API"
curl -sf "$API/health" | grep -q healthy && echo "  health OK" || { echo "  health FAIL"; exit 1; }
curl -sf -X POST "$API/demo" -H "Content-Type: application/json" | tee /tmp/aiam-day07-demo.json | grep -q '"demo_runs"' && echo "  demo OK" || { echo "  demo FAIL"; exit 1; }

python3 - <<'PY'
import json
d = json.load(open("/tmp/aiam-day07-demo.json"))
m = d.get("metrics", d)
checks = {
    "executions_total": m.get("executions_total", 0),
    "executions_ok": m.get("executions_ok", 0),
    "executions_blocked": m.get("executions_blocked", 0),
    "executions_timeout": m.get("executions_timeout", 0),
    "executions_error": m.get("executions_error", 0),
    "allowed_module_hits": m.get("allowed_module_hits", 0),
    "blocked_module_hits": m.get("blocked_module_hits", 0),
    "throughput_eps": m.get("throughput_eps", 0),
    "duration_p50_ms": m.get("duration_p50_ms", 0),
    "duration_p95_ms": m.get("duration_p95_ms", 0),
    "duration_p99_ms": m.get("duration_p99_ms", 0),
    "duration_avg_ms": m.get("duration_avg_ms", 0),
    "duration_max_ms": m.get("duration_max_ms", 0),
    "block_rate": m.get("block_rate", 0),
    "timeout_rate": m.get("timeout_rate", 0),
    "ok_rate": m.get("ok_rate", 0),
    "demo_runs": m.get("demo_runs", 0),
}
print("  metrics:", checks)
for k, v in checks.items():
    assert float(v) > 0, f"{k} is zero"
print("  metrics non-zero OK")
PY

curl -sf "$API/metrics" | grep -q executions_total && echo "  /metrics OK" || { echo "  /metrics FAIL"; exit 1; }
curl -sf "$API/dashboard" | grep -q "Sandboxed Code Execution" && echo "  /dashboard OK" || { echo "  /dashboard FAIL"; exit 1; }
echo "All tests passed."
