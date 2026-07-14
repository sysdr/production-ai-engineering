#!/usr/bin/env bash
# Stop AIAM Day 1 services and remove unused Docker resources for this project.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

CONTAINER="${CONTAINER:-aiam-day01}"
IMAGE="${IMAGE:-aiam-day01-agent}"

echo "► Stopping local processes..."
pkill -f "uvicorn app:app" 2>/dev/null || true

echo "► Stopping / removing project containers..."
if command -v docker >/dev/null 2>&1; then
  docker stop "$CONTAINER" >/dev/null 2>&1 || true
  docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
  # Compose project leftovers (if any)
  docker compose down --remove-orphans >/dev/null 2>&1 || true

  echo "► Removing project image ($IMAGE)..."
  docker rmi -f "$IMAGE" >/dev/null 2>&1 || true

  echo "► Pruning unused Docker containers, networks, dangling images..."
  docker container prune -f >/dev/null 2>&1 || true
  docker network prune -f >/dev/null 2>&1 || true
  docker image prune -f >/dev/null 2>&1 || true
else
  echo "  docker not found — skipped container/image cleanup"
fi

echo "► Removing local caches (venv, node_modules, pytest, pyc, Istio)..."
rm -rf \
  "$SCRIPT_DIR/venv" \
  "$SCRIPT_DIR/.venv" \
  "$SCRIPT_DIR/node_modules" \
  "$SCRIPT_DIR/.pytest_cache" \
  "$SCRIPT_DIR"/__pycache__ \
  "$SCRIPT_DIR"/istio* \
  "$SCRIPT_DIR"/Istio* \
  2>/dev/null || true

find "$SCRIPT_DIR" -type d -name '__pycache__' -prune -exec rm -rf {} + 2>/dev/null || true
find "$SCRIPT_DIR" -type d -name '.pytest_cache' -prune -exec rm -rf {} + 2>/dev/null || true
find "$SCRIPT_DIR" -type d -name 'node_modules' -prune -exec rm -rf {} + 2>/dev/null || true
find "$SCRIPT_DIR" -type d \( -name 'venv' -o -name '.venv' \) -prune -exec rm -rf {} + 2>/dev/null || true
find "$SCRIPT_DIR" -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete 2>/dev/null || true
find "$SCRIPT_DIR" -iname '*istio*' -exec rm -rf {} + 2>/dev/null || true

echo "Cleanup complete."
