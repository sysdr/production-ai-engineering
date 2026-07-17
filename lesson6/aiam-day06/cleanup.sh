#!/usr/bin/env bash
# Stop Day 6 services and remove project and unused Docker resources.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
CONTAINER="aiam-day06"
IMAGE="aiam-day06-observability"
API_PORT="${API_PORT:-8085}"

pkill -f "uvicorn app:app.*${API_PORT}" 2>/dev/null || true

if command -v docker >/dev/null 2>&1; then
  docker compose down --remove-orphans >/dev/null 2>&1 || true
  docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
  docker rmi -f "$IMAGE" >/dev/null 2>&1 || true
  docker system prune -af >/dev/null 2>&1 || true
fi

echo "Cleanup complete — Day 6 services, project image, and unused Docker resources removed."
