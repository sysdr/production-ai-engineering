#!/usr/bin/env bash
# Run the Day 1 CLI demo (self-contained — does not need ../setup.sh).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

IMAGE="${IMAGE:-aiam-day01-agent}"

# Optional local env (never commit .env — see .gitignore)
if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

if command -v docker >/dev/null 2>&1; then
  if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
    echo "Building image $IMAGE..."
    docker build -t "$IMAGE" .
  fi
  echo "► Running CLI demo in Docker..."
  docker run --rm \
    -e OPENAI_API_KEY="${OPENAI_API_KEY:-}" \
    -e OPENAI_MODEL="${OPENAI_MODEL:-gpt-4o-mini}" \
    "$IMAGE" python main.py
  exit 0
fi

# Local fallback
if [ -f "venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source venv/bin/activate
fi
export PYTHONPATH=.
python3 main.py
