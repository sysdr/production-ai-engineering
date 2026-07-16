#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
API_PORT="${API_PORT:-8082}"
CONTAINER="aiam-day03"
REDIS_CONTAINER="aiam-day03-redis"
IMAGE="aiam-day03-memory"

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

# Avoid duplicate services
running_app=0
running_redis=0
if docker ps --format '{{.Names}}' 2>/dev/null | grep -qx "$CONTAINER"; then
  running_app=1
fi
if docker ps --format '{{.Names}}' 2>/dev/null | grep -qx "$REDIS_CONTAINER"; then
  running_redis=1
fi
if [ "$running_app" -eq 1 ] && [ "$running_redis" -eq 1 ]; then
  echo "Day 3 already running ($CONTAINER + $REDIS_CONTAINER)."
  echo "Dashboard: http://127.0.0.1:${API_PORT}/dashboard"
  exit 0
fi

if ss -ltn 2>/dev/null | grep -q ":${API_PORT} " || \
   netstat -ltn 2>/dev/null | grep -q ":${API_PORT} "; then
  if [ "$running_app" -eq 0 ]; then
    echo "Port ${API_PORT} already in use by another process. Use stop.sh first."
    exit 1
  fi
fi

if command -v docker >/dev/null 2>&1; then
  # Clean partial starts, then bring up compose stack (app + Redis)
  docker rm -f "$CONTAINER" "$REDIS_CONTAINER" >/dev/null 2>&1 || true
  echo "Starting Day 3 via docker compose (Redis + memory API)..."
  docker compose up -d --build
  echo "Started $CONTAINER (+ Redis)"
  echo "Dashboard: http://127.0.0.1:${API_PORT}/dashboard"
  echo "Health:    http://127.0.0.1:${API_PORT}/health"
  exit 0
fi

if [ -f "venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source venv/bin/activate
fi
command -v uvicorn >/dev/null || { echo "uvicorn not found; install deps or use Docker."; exit 1; }
uvicorn app:app --host 127.0.0.1 --port "$API_PORT" --workers 1 &
echo "Local API started at http://127.0.0.1:${API_PORT} (PID $!) — Redis optional via REDIS_URL"
