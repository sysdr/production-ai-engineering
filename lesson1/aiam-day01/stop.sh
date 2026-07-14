#!/usr/bin/env bash
set -euo pipefail
CONTAINER="aiam-day01"
pkill -f "uvicorn app:app" 2>/dev/null || true
docker stop "$CONTAINER" >/dev/null 2>&1 || true
docker rm "$CONTAINER" >/dev/null 2>&1 || true
echo "Stopped local uvicorn and Docker container ($CONTAINER)."
