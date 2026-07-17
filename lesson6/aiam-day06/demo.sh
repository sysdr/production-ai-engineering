#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
IMAGE="aiam-day06-observability"

if command -v docker >/dev/null 2>&1; then
  if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
    echo "Building image $IMAGE..."
    docker build -t "$IMAGE" .
  fi
  echo "► Running CLI demo in Docker..."
  docker run --rm "$IMAGE" python main.py
  exit 0
fi

if [ -f "venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source venv/bin/activate
fi
export PYTHONPATH=.
python3 main.py
