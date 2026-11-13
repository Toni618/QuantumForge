#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PY="${PYTHON:-.venv/bin/python}"
echo "== python tests =="
"$PY" -m pytest -q
echo "== api/persistence verification =="
"$PY" scripts/verify_api.py
echo "== frontend typecheck/build =="
(cd frontend && npm run build)
echo "== frontend lint (optional if deps installed) =="
if (cd frontend && npx --no-install eslint --version >/dev/null 2>&1); then
  (cd frontend && npm run lint)
else
  echo "SKIP: eslint dev dependencies not installed"
fi
echo "== python lint/type (optional if installed) =="
if "$PY" -m ruff --version >/dev/null 2>&1; then "$PY" -m ruff check quantumforge tests scripts; else echo "SKIP: ruff not installed"; fi
if "$PY" -m mypy --version >/dev/null 2>&1; then "$PY" -m mypy quantumforge; else echo "SKIP: mypy not installed"; fi
echo "VERIFY_ALL_DONE"
