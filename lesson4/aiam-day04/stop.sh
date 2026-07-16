#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
CONTAINER="aiam-day04"
API_PORT="${API_PORT:-8083}"
pkill -f "uvicorn app:app.*${API_PORT}" 2>/dev/null || true
docker stop "$CONTAINER" >/dev/null 2>&1 || true
docker rm "$CONTAINER" >/dev/null 2>&1 || true
docker compose down --remove-orphans >/dev/null 2>&1 || true
echo "Stopped Day 4 ($CONTAINER)."
