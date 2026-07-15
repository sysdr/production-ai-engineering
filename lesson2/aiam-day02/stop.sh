#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
CONTAINER="aiam-day02"
# Only kill Day 2 local server if bound to 8081
pkill -f "uvicorn app:app --host .* --port 8081" 2>/dev/null || true
docker stop "$CONTAINER" >/dev/null 2>&1 || true
docker rm "$CONTAINER" >/dev/null 2>&1 || true
echo "Stopped Day 2 local uvicorn (8081) and Docker container ($CONTAINER)."
