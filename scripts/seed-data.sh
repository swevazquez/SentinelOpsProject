#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

RUN_ID="${1:-local-seed}"
RAW_PATH="data/raw/telemetry_${RUN_ID}.csv"
FEATURE_PATH="data/processed/features_${RUN_ID}.csv"
PYTHON_BIN="${PYTHON_BIN:-python3}"

"$PYTHON_BIN" -m services.simulator.telemetry \
  --run-id "$RUN_ID" \
  --hours 24 \
  --raw-dir data/raw

"$PYTHON_BIN" -m services.spark_jobs.features \
  --input "$RAW_PATH" \
  --processed-dir data/processed

echo "Seeded Sprint 1 data:"
echo "  raw telemetry: $RAW_PATH"
echo "  processed features: $FEATURE_PATH"
