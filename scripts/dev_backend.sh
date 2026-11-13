#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
exec "${PYTHON:-.venv/bin/python}" -m quantumforge.api.app
