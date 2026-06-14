#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Required: Python 3.12 or later was not found. Set PYTHON_BIN or install Python 3.12+." >&2
  exit 1
fi

if ! "$PYTHON_BIN" -c 'import sys; raise SystemExit(sys.version_info < (3, 12))'; then
  version="$("$PYTHON_BIN" --version 2>&1)"
  echo "Required: Python 3.12 or later. Found ${version}." >&2
  exit 1
fi

echo "Required: $("$PYTHON_BIN" --version 2>&1)"

if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  echo "Optional: $(docker compose version)"
else
  echo "Optional: Docker Compose not found; required only for Airflow and PostgreSQL review."
fi

echo "Local prerequisites satisfied."
