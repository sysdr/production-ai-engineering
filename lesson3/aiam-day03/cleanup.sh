#!/usr/bin/env bash
# Stop Day 3 services and remove local/runtime artifacts.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
CONTAINER="${CONTAINER:-aiam-day03}"
REDIS_CONTAINER="${REDIS_CONTAINER:-aiam-day03-redis}"
IMAGE="${IMAGE:-aiam-day03-memory}"

echo "► Stopping Day 3 local processes..."
pkill -f "uvicorn app:app.*8082" 2>/dev/null || true
pkill -f "uvicorn app:app --host .* --port 8082" 2>/dev/null || true

echo "► Stopping / removing project containers..."
if command -v docker >/dev/null 2>&1; then
  docker compose down --remove-orphans >/dev/null 2>&1 || true
  docker stop "$CONTAINER" "$REDIS_CONTAINER" >/dev/null 2>&1 || true
  docker rm -f "$CONTAINER" "$REDIS_CONTAINER" >/dev/null 2>&1 || true

  echo "► Removing project image ($IMAGE)..."
  docker rmi -f "$IMAGE" >/dev/null 2>&1 || true

  echo "► Removing unused Docker containers, networks, build cache, and images..."
  docker container prune -f >/dev/null 2>&1 || true
  docker network prune -f >/dev/null 2>&1 || true
  docker builder prune -af >/dev/null 2>&1 || true
  docker image prune -af >/dev/null 2>&1 || true
else
  echo "  docker not found — skipped container/image cleanup"
fi

echo "► Removing local generated artifacts..."
python3 - <<'PY'
from pathlib import Path
import shutil

root = Path.cwd()
dir_names = {
    "node_modules",
    "venv",
    ".venv",
    "ENV",
    ".pytest_cache",
    "__pycache__",
}

for path in sorted(root.rglob("*"), key=lambda p: len(p.parts), reverse=True):
    name_lower = path.name.lower()
    if path.is_dir() and (path.name in dir_names or "istio" in name_lower):
        shutil.rmtree(path, ignore_errors=True)
    elif path.is_file() and (
        path.suffix in {".pyc", ".pyo"} or "istio" in name_lower
    ):
        path.unlink(missing_ok=True)
PY

echo "Cleanup complete."
