# FINAL_BUILD_REPORT.md

Date: 2026-11-11 | Environment: Linux (workspace), Python 3.14.9 venv, Node v26.13.0/npm 12.2.2

## Executed builds/tests
| Component | Command | Result |
|---|---|---|
| Python tests | `PYTHONPATH=. .venv/bin/python -m pytest -q` | **PASS** — 46 passed, 1 warning (third-party Starlette/anyio deprecation) |
| API + SQLite verification | `PYTHONPATH=. .venv/bin/python scripts/verify_api.py` | **PASS** — 19 endpoints verified, 0 failures, ALL_ENDPOINTS_OK, SQLITE_PERSISTENCE_OK |
| Frontend typecheck/build | `cd frontend && npm run build` (`tsc --noEmit && vite build`) | **PASS** — Vite production build succeeded (`frontend/dist/`) |

## Not executed / not verified
| Component | Status | Reason |
|---|---|---|
| Ruff | NOT RUN | `ruff` not installed in venv; registry install unavailable |
| mypy | NOT RUN | `mypy` not installed |
| pytest-cov | NOT RUN | `pytest-cov` not installed |
| ESLint | NOT RUN | ESLint dev deps not installed/fetchable |
| Frontend tests (Playwright/Vitest) | NOT CONFIGURED/RUN | No suite present/executed |
| Tauri desktop build (Linux) | NOT VERIFIED | `cargo`/`rustc` unavailable (`rustup` not configured) |
| Linux AppImage/deb/rpm | NOT BUILT | Rust/Tauri toolchain and packaging steps not run |
| Windows MSI/NSIS installer | NOT BUILT/NOT VERIFIED | Requires Windows/Rust toolchain/CI; not available locally |
| Backend bundled executable (PyInstaller/Tauri resource) | NOT VERIFIED | Not produced/tested in this pass |
| Clean-install startup (packaged app) | NOT VERIFIED | No packaged artifacts |

## CI
- Workflows present: `.github/workflows/ci.yml` (added 0.2.1), `.github/workflows/windows-release.yml` (existing). Local execution in GitHub runners: **not performed here**.

## Artifacts
- Source tree updated to 0.4.0; frontend production assets buildable (`frontend/dist/` when built). No distributable desktop installers produced.
