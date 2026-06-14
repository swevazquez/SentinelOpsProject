#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -f .env ]]; then
  echo "Missing .env. Run ./scripts/setup.sh first."
  exit 1
fi

"$ROOT_DIR/scripts/check-prerequisites.sh"

if ! command -v docker >/dev/null 2>&1 || ! docker compose version >/dev/null 2>&1; then
  echo "Docker Compose is required to start the Airflow and PostgreSQL services." >&2
  exit 1
fi

docker compose up --build
