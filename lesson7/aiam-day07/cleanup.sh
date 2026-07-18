#!/usr/bin/env bash
# Stop Day 7 containers and remove unused Docker resources, containers and images.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
CONTAINER="aiam-day07"
IMAGE="aiam-day07-sandbox"
API_PORT="${API_PORT:-8086}"

pkill -f "uvicorn app:app.*${API_PORT}" 2>/dev/null || true

if command -v docker >/dev/null 2>&1; then
  docker compose down --remove-orphans >/dev/null 2>&1 || true
  docker stop "$CONTAINER" >/dev/null 2>&1 || true
  docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
  docker rmi -f "$IMAGE" >/dev/null 2>&1 || true
  docker container prune -f >/dev/null 2>&1 || true
  docker image prune -af >/dev/null 2>&1 || true
  docker network prune -f >/dev/null 2>&1 || true
  docker builder prune -af >/dev/null 2>&1 || true
  docker volume prune -f >/dev/null 2>&1 || true
fi

echo "Cleanup complete — containers, project image, and unused Docker resources removed."
