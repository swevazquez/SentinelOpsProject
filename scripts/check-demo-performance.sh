#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"

"$PYTHON_BIN" -m scripts.demo_performance \
  --project-root "$ROOT_DIR" \
  --runs "${DEMO_RUNS:-3}" \
  --hours "${DEMO_HOURS:-24}" \
  --max-seconds "${DEMO_MAX_SECONDS:-5}" \
  --run-prefix "${DEMO_RUN_PREFIX:-demo-performance}" \
  --output "${DEMO_PERFORMANCE_OUTPUT:-data/performance/latest-demo-performance.json}"
