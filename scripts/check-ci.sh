#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"
RUN_ID="${RUN_ID:-ci-smoke}"
RAW_PATH="data/raw/telemetry_${RUN_ID}.csv"
FEATURE_PATH="data/processed/features_${RUN_ID}.csv"

echo "Checking repository scaffold..."
test -f README.md
test -f docker-compose.yml
test -f pyproject.toml
test -d services/api
test -d services/agent
test -d services/ml
test -d services/spark-jobs
test -d services/simulator
test -d data/predictions
test -d data/models
test -d airflow/dags
test -d frontend/dashboard
test -d tests/unit

echo "Checking generated data is not tracked..."
if git ls-files data/raw data/processed data/predictions data/models | grep -Ev '(^data/raw/\.gitkeep$|^data/processed/\.gitkeep$|^data/predictions/\.gitkeep$|^data/models/\.gitkeep$)' >/dev/null; then
  echo "Generated raw, processed, prediction, or model data files must not be committed."
  git ls-files data/raw data/processed data/predictions data/models
  exit 1
fi

echo "Running unit tests..."
"$PYTHON_BIN" -m unittest discover -s tests

echo "Running Sprint 1 workflow smoke test..."
./scripts/seed-data.sh "$RUN_ID"

test -f "$RAW_PATH"
test -f "$FEATURE_PATH"

raw_lines="$(wc -l < "$RAW_PATH" | tr -d ' ')"
feature_lines="$(wc -l < "$FEATURE_PATH" | tr -d ' ')"

if [[ "$raw_lines" != "97" ]]; then
  echo "Expected 97 raw telemetry CSV lines, found ${raw_lines}."
  exit 1
fi

if [[ "$feature_lines" != "5" ]]; then
  echo "Expected 5 processed feature CSV lines, found ${feature_lines}."
  exit 1
fi

echo "Checking Airflow DAG syntax..."
for dag_path in airflow/dags/*.py; do
  "$PYTHON_BIN" -m py_compile "$dag_path"
done

echo "Checking Markdown files are readable..."
while IFS= read -r doc_path; do
  test -r "$doc_path"
  test -s "$doc_path"
done < <(find docs -name '*.md' -type f)

echo "CI checks passed."
