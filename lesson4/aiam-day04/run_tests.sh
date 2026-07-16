#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
API="${API_URL:-http://127.0.0.1:8083}"
IMAGE="aiam-day04-ratelimit"

echo "► Unit tests (pytest)"
if command -v docker >/dev/null 2>&1 && docker image inspect "$IMAGE" >/dev/null 2>&1; then
  docker run --rm "$IMAGE" python -m pytest tests/ -v
else
  PYTHONPATH=. python3 -m pytest tests/ -v
fi

echo ""
echo "► API smoke tests against $API"
curl -sf "$API/health" | grep -q healthy && echo "  health OK" || { echo "  health FAIL"; exit 1; }
curl -sf -X POST "$API/demo" -H "Content-Type: application/json" | tee /tmp/aiam-day04-demo.json | grep -q '"demo_runs"' && echo "  demo OK" || { echo "  demo FAIL"; exit 1; }

python3 - <<'PY'
import json
d = json.load(open("/tmp/aiam-day04-demo.json"))
m = d.get("metrics", d)
checks = {
    "requests_total": m.get("requests_total", 0),
    "requests_allowed": m.get("requests_allowed", 0),
    "requests_throttled": m.get("requests_throttled", 0),
    "tokens_input_total": m.get("tokens_input_total", 0),
    "tokens_output_total": m.get("tokens_output_total", 0),
    "spend_usd_total": m.get("spend_usd_total", 0),
    "users_tracked": m.get("users_tracked", 0),
    "budget_alerts": m.get("budget_alerts", 0),
    "latency_ms_avg": m.get("latency_ms_avg", 0),
    "demo_runs": m.get("demo_runs", 0),
}
print("  metrics:", checks)
for k, v in checks.items():
    assert float(v) > 0, f"{k} is zero"
print("  metrics non-zero OK")
PY

curl -sf "$API/metrics" | grep -q requests_total && echo "  /metrics OK" || { echo "  /metrics FAIL"; exit 1; }
curl -sf "$API/dashboard" | grep -q "Rate Limiting" && echo "  /dashboard OK" || { echo "  /dashboard FAIL"; exit 1; }
echo "All tests passed."
