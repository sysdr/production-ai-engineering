#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
CONTAINER="aiam-day04"
IMAGE="aiam-day04-ratelimit"
API_PORT="${API_PORT:-8083}"

pkill -f "uvicorn app:app.*${API_PORT}" 2>/dev/null || true
if command -v docker >/dev/null 2>&1; then
  echo "Stopping project containers..."
  docker compose down --remove-orphans >/dev/null 2>&1 || true
  docker stop "$CONTAINER" >/dev/null 2>&1 || true
  docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
  docker rmi -f "$IMAGE" >/dev/null 2>&1 || true

  echo "Stopping all running Docker containers..."
  RUNNING_CONTAINERS="$(docker ps -q 2>/dev/null || true)"
  if [ -n "${RUNNING_CONTAINERS}" ]; then
    docker stop ${RUNNING_CONTAINERS} >/dev/null 2>&1 || true
  fi

  echo "Removing unused Docker resources..."
  docker container prune -f >/dev/null 2>&1 || true
  docker network prune -f >/dev/null 2>&1 || true
  docker image prune -af >/dev/null 2>&1 || true
  docker volume prune -f >/dev/null 2>&1 || true
  docker builder prune -af >/dev/null 2>&1 || true
fi

echo "Removing local caches and generated artifacts..."
python3 - <<'PY'
from pathlib import Path
import shutil

root = Path.cwd()

for path in sorted(root.rglob("*"), key=lambda p: len(p.parts), reverse=True):
    name_lower = path.name.lower()
    if path.is_dir() and (
        path.name in {"node_modules", "venv", ".venv", "ENV", ".pytest_cache", "__pycache__"}
        or "istio" in name_lower
    ):
        shutil.rmtree(path, ignore_errors=True)
    elif path.is_file() and (
        path.suffix in {".pyc", ".pyo"} or "istio" in name_lower
    ):
        path.unlink(missing_ok=True)
PY

echo "Cleanup complete."
