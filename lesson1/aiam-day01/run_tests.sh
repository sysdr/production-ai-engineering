#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
API="${API_URL:-http://127.0.0.1:8080}"

echo "► Unit tests (pytest)"
if command -v docker >/dev/null 2>&1 && docker image inspect aiam-day01-agent >/dev/null 2>&1; then
  docker run --rm aiam-day01-agent python -m pytest tests/ -v
else
  PYTHONPATH=. python3 -m pytest tests/ -v
fi

echo ""
echo "► API smoke tests against $API"
curl -sf "$API/health" | grep -q healthy && echo "  health OK" || { echo "  health FAIL"; exit 1; }
curl -sf -X POST "$API/demo" -H "Content-Type: application/json" | tee /tmp/aiam-demo.json | grep -q '"demo_runs"' && echo "  demo OK" || { echo "  demo FAIL"; exit 1; }
# Metrics must be non-zero after demo
TOKENS=$(python3 - <<'PY'
import json
d=json.load(open("/tmp/aiam-demo.json"))
m=d.get("metrics", d)
print(m.get("tokens_total", 0))
PY
)
REQS=$(python3 - <<'PY'
import json
d=json.load(open("/tmp/aiam-demo.json"))
m=d.get("metrics", d)
print(m.get("requests_total", 0))
PY
)
BLOCKED=$(python3 - <<'PY'
import json
d=json.load(open("/tmp/aiam-demo.json"))
m=d.get("metrics", d)
print(m.get("requests_blocked", 0))
PY
)
COST=$(python3 - <<'PY'
import json
d=json.load(open("/tmp/aiam-demo.json"))
m=d.get("metrics", d)
print(m.get("cost_usd_total", 0))
PY
)
echo "  metrics: requests=$REQS tokens=$TOKENS blocked=$BLOCKED cost=$COST"
python3 - <<PY
tokens=int("$TOKENS"); reqs=int("$REQS"); blocked=int("$BLOCKED"); cost=float("$COST")
assert reqs > 0, "requests_total is zero"
assert tokens > 0, "tokens_total is zero"
assert blocked > 0, "requests_blocked is zero (expected injection demos)"
assert cost > 0, "cost_usd_total is zero"
print("  metrics non-zero OK")
PY
curl -sf "$API/metrics" | grep -q requests_total && echo "  /metrics OK" || { echo "  /metrics FAIL"; exit 1; }
curl -sf "$API/dashboard" | grep -q "Secure Agent" && echo "  /dashboard OK" || { echo "  /dashboard FAIL"; exit 1; }
echo "All tests passed."
