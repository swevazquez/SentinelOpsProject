#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

RUN_ID="${1:-local-seed}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

"$PYTHON_BIN" -m services.workflows.sprint1 \
  --run-id "$RUN_ID" \
  --project-root "$ROOT_DIR" \
  --hours 24
