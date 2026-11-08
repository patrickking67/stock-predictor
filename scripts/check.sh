#!/usr/bin/env bash
# The one check command: lint, format check, JS syntax check, tests.
# Usage: scripts/check.sh   (uses .venv if present, else python3 on PATH)
set -euo pipefail
cd "$(dirname "$0")/.."

if [ -x .venv/bin/python ]; then
  PY=.venv/bin/python
else
  PY=python3
fi

echo "== ruff check"
"$PY" -m ruff check .
echo "== ruff format --check"
"$PY" -m ruff format --check .
if command -v node >/dev/null 2>&1; then
  echo "== node --check static/*.js"
  for f in static/*.js; do node --check "$f"; done
else
  echo "== node not found, skipping JS syntax check"
fi
echo "== pytest"
"$PY" -m pytest
echo "All checks passed."
