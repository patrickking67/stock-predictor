#!/usr/bin/env bash
# Start the Flask dev server on http://127.0.0.1:4110 (override with PORT).
# Reads ALPHA_VANTAGE_API_KEY from the environment if set; it is optional.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ -x .venv/bin/python ]; then
  PY=.venv/bin/python
else
  PY=python3
fi

exec "$PY" -m flask --app main run --host 127.0.0.1 --port "${PORT:-4110}"
