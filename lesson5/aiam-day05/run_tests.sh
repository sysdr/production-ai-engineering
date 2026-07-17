#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
API="${API_URL:-http://127.0.0.1:8084}"
IMAGE="aiam-day05-security"

echo "► Unit tests (pytest)"
if command -v docker >/dev/null 2>&1 && docker image inspect "$IMAGE" >/dev/null 2>&1; then
  docker run --rm "$IMAGE" python -m pytest tests/ -v
else
  PYTHONPATH=. python3 -m pytest tests/ -v
fi

echo ""
echo "► API smoke tests against $API"
curl -sf "$API/health" | grep -q healthy && echo "  health OK" || { echo "  health FAIL"; exit 1; }
curl -sf -X POST "$API/demo" -H "Content-Type: application/json" | tee /tmp/aiam-day05-demo.json | grep -q '"demo_runs"' && echo "  demo OK" || { echo "  demo FAIL"; exit 1; }

python3 - <<'PY'
import json
d = json.load(open("/tmp/aiam-day05-demo.json"))
m = d.get("metrics", d)
checks = {
    "scans_total": m.get("scans_total", 0),
    "scans_clean": m.get("scans_clean", 0),
    "scans_blocked": m.get("scans_blocked", 0),
    "secrets_detected": m.get("secrets_detected", 0),
    "pii_detected": m.get("pii_detected", 0),
    "redactions_total": m.get("redactions_total", 0),
    "hmac_signs": m.get("hmac_signs", 0),
    "hmac_verifications_ok": m.get("hmac_verifications_ok", 0),
    "hmac_verifications_fail": m.get("hmac_verifications_fail", 0),
    "latency_ms_avg": m.get("latency_ms_avg", 0),
    "demo_runs": m.get("demo_runs", 0),
}
print("  metrics:", checks)
for k, v in checks.items():
    assert float(v) > 0, f"{k} is zero"
print("  metrics non-zero OK")
PY

curl -sf "$API/metrics" | grep -q scans_total && echo "  /metrics OK" || { echo "  /metrics FAIL"; exit 1; }
curl -sf "$API/dashboard" | grep -q "Security Hardening" && echo "  /dashboard OK" || { echo "  /dashboard FAIL"; exit 1; }
echo "All tests passed."
