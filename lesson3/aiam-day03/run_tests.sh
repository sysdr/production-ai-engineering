#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
API="${API_URL:-http://127.0.0.1:8082}"
IMAGE="aiam-day03-memory"

echo "► Unit tests (pytest)"
if command -v docker >/dev/null 2>&1 && docker image inspect "$IMAGE" >/dev/null 2>&1; then
  docker run --rm "$IMAGE" python -m pytest tests/ -v
else
  PYTHONPATH=. python3 -m pytest tests/ -v
fi

echo ""
echo "► API smoke tests against $API"
curl -sf "$API/health" | grep -q healthy && echo "  health OK" || { echo "  health FAIL"; exit 1; }
curl -sf -X POST "$API/demo" -H "Content-Type: application/json" | tee /tmp/aiam-day03-demo.json | grep -q '"demo_runs"' && echo "  demo OK" || { echo "  demo FAIL"; exit 1; }

python3 - <<'PY'
import json
d = json.load(open("/tmp/aiam-day03-demo.json"))
m = d.get("metrics", d)
checks = {
    "memory_ops_total": m.get("memory_ops_total", 0),
    "turns_stored": m.get("turns_stored", 0),
    "cache_hits": m.get("cache_hits", 0),
    "cache_misses": m.get("cache_misses", 0),
    "cache_hit_rate": m.get("cache_hit_rate", 0),
    "ttl_evictions": m.get("ttl_evictions", 0),
    "latency_ms_avg": m.get("latency_ms_avg", 0),
    "demo_runs": m.get("demo_runs", 0),
}
print("  metrics:", checks)
for k, v in checks.items():
    assert float(v) > 0, f"{k} is zero"
# Redis ops should be > 0 when Redis is connected (compose stack)
if m.get("redis_connected"):
    assert m.get("redis_ops", 0) > 0, "redis_ops is zero while redis_connected"
    print("  redis ops OK:", m.get("redis_ops"))
else:
    print("  redis offline (OK for unit-only / no-compose)")
print("  metrics non-zero OK")
PY

curl -sf "$API/metrics" | grep -q memory_ops_total && echo "  /metrics OK" || { echo "  /metrics FAIL"; exit 1; }
curl -sf "$API/dashboard" | grep -q "Memory Systems" && echo "  /dashboard OK" || { echo "  /dashboard FAIL"; exit 1; }
echo "All tests passed."
