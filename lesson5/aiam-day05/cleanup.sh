#!/usr/bin/env bash
# Stop Day 5 containers and remove unused Docker resources, containers and images.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
CONTAINER="aiam-day05"
IMAGE="aiam-day05-security"
API_PORT="${API_PORT:-8084}"

# Stop any local uvicorn dev server on this port.
pkill -f "uvicorn app:app.*${API_PORT}" 2>/dev/null || true

if command -v docker >/dev/null 2>&1; then
  # Stop and remove this project's container.
  docker stop "$CONTAINER" >/dev/null 2>&1 || true
  docker rm -f "$CONTAINER" >/dev/null 2>&1 || true

  # Tear down compose services and their network.
  docker compose down --remove-orphans >/dev/null 2>&1 || true

  # Remove this project's image.
  docker rmi -f "$IMAGE" >/dev/null 2>&1 || true

  # Remove unused Docker resources (stopped containers, dangling images,
  # unused networks, and build cache). Volumes are left intact.
  docker container prune -f >/dev/null 2>&1 || true
  docker image prune -f >/dev/null 2>&1 || true
  docker network prune -f >/dev/null 2>&1 || true
  docker builder prune -f >/dev/null 2>&1 || true
fi

echo "Cleanup complete — containers, project image, and unused Docker resources removed."
