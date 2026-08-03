#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

MODE="${1:-config}"

if [[ "$MODE" != "config" && "$MODE" != "live" ]]; then
  echo "Usage: bash scripts/check-compose.sh [config|live]" >&2
  exit 2
fi

if [[ ! -f .env ]]; then
  echo "Missing .env. Run ./scripts/setup.sh first; secrets remain local and are not committed." >&2
  exit 1
fi

if ! command -v docker >/dev/null 2>&1 || ! docker compose version >/dev/null 2>&1; then
  echo "Docker Compose is required for this validation." >&2
  exit 1
fi

echo "Validating the resolved Docker Compose configuration..."
docker compose config --quiet
echo "Compose configuration is valid."

if [[ "$MODE" == "config" ]]; then
  exit 0
fi

cleanup() {
  docker compose down
}
trap cleanup EXIT INT TERM

echo "Starting the stack and waiting for service health..."
docker compose up --build --wait
curl --fail --silent http://127.0.0.1:8000/api/health
printf '\n'
docker compose ps
