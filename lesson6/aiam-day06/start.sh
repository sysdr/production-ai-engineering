#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
API_PORT="${API_PORT:-8085}"
CONTAINER="aiam-day06"
IMAGE="aiam-day06-observability"

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

# Prevent duplicate services: if our container already runs, do nothing.
if docker ps --format '{{.Names}}' 2>/dev/null | grep -qx "$CONTAINER"; then
  echo "Day 6 already running ($CONTAINER)."
  echo "Dashboard: http://127.0.0.1:${API_PORT}/dashboard"
  exit 0
fi

# Refuse to start if the port is occupied by something we do not manage.
if ss -ltn 2>/dev/null | grep -q ":${API_PORT} " || \
   netstat -ltn 2>/dev/null | grep -q ":${API_PORT} "; then
  if ! docker ps --format '{{.Names}}' 2>/dev/null | grep -qx "$CONTAINER"; then
    echo "Port ${API_PORT} already in use. Use stop.sh first."
    exit 1
  fi
fi

if command -v docker >/dev/null 2>&1; then
  docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
  echo "Starting Day 6 via docker compose..."
  docker compose up -d --build
  echo "Started $CONTAINER"
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
echo "Local API started at http://127.0.0.1:${API_PORT} (PID $!)"
