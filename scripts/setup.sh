#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

"$ROOT_DIR/scripts/check-prerequisites.sh"

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from .env.example"
else
  echo "Existing .env preserved."
fi

mkdir -p data/raw data/processed data/predictions data/performance data/samples data/workflow-status

echo "SentinelOps setup complete."
