#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
CONTAINER="aiam-day03"
REDIS_CONTAINER="aiam-day03-redis"
# Only kill Day 3 local server if bound to 8082
pkill -f "uvicorn app:app --host .* --port 8082" 2>/dev/null || true
pkill -f "uvicorn app:app.*8082" 2>/dev/null || true
docker compose down --remove-orphans >/dev/null 2>&1 || true
docker stop "$CONTAINER" "$REDIS_CONTAINER" >/dev/null 2>&1 || true
docker rm "$CONTAINER" "$REDIS_CONTAINER" >/dev/null 2>&1 || true
echo "Stopped Day 3 local uvicorn (8082) and Docker containers ($CONTAINER, $REDIS_CONTAINER)."
