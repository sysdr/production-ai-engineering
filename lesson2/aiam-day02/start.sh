#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
API_PORT="${API_PORT:-8081}"
CONTAINER="aiam-day02"
IMAGE="aiam-day02-tools"

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

# Avoid duplicate services
if docker ps --format '{{.Names}}' 2>/dev/null | grep -qx "$CONTAINER"; then
  echo "Container $CONTAINER already running."
  echo "Dashboard: http://127.0.0.1:${API_PORT}/dashboard"
  exit 0
fi
if pgrep -f "uvicorn app:app" >/dev/null 2>&1; then
  # Allow Day 1 on 8080; only block if something already binds our port
  if ss -ltn 2>/dev/null | grep -q ":${API_PORT} " || \
     netstat -ltn 2>/dev/null | grep -q ":${API_PORT} "; then
    echo "Port ${API_PORT} already in use. Use stop.sh first."
    exit 0
  fi
fi

if command -v docker >/dev/null 2>&1; then
  if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
    echo "Building image $IMAGE..."
    docker build -t "$IMAGE" .
  fi
  docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
  docker run -d \
    --name "$CONTAINER" \
    -p "${API_PORT}:8081" \
    "$IMAGE"
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
