# Developer Guide — QuantumForge 0.3.0

## Environment
- Python >= 3.11 (validated in dev on 3.14.x venv), Node 22+ recommended for frontend/CI.
- Backend deps: `python -m pip install -e '.[dev]'` (core pinned in `pyproject.toml`; dev extras declare pytest/httpx/pytest-cov/ruff/mypy).
- Frontend deps: `cd frontend && npm ci` (lockfile `frontend/package-lock.json`).

## Repository layout
- `quantumforge/`: scientific core (`core`, `math`, `quantum`, `qft`, `relativity`), `application` (jobs), `storage` (DB/migrations/store), `api` (FastAPI).
- `frontend/`: React+TS+Vite UI.
- `src-tauri/`: Tauri 2 desktop shell.
- `tests/`: pytest suite (core/scientific, API, Phase 1 storage/jobs/API).
- `scripts/`: dev and verification helpers.
- `docs/`: architecture, guides, validation/limitations, methods.

## Running
- API: `PYTHONPATH=. .venv/bin/python -m quantumforge.api.app` or `quantumforge-api`. Env: `QUANTUMFORGE_DB`, `QUANTUMFORGE_PORT`, `QUANTUMFORGE_MAX_WORKERS`.
- Frontend dev: `cd frontend && npm run dev`.
- Build frontend: `cd frontend && npm run build` (`tsc --noEmit && vite build`).

## Storage & migrations
- SQLite path defaults to `quantumforge.sqlite3`; `Database` applies transactional migrations on init (`schema_migrations`, current v1). Legacy 0.2.x `experiments` rows are auto-migrated/preserved.
- Backup/restore: `Database.backup/restore` (restore checkpoints/removes WAL sidecars and re-runs migrations). Project portability: `ExperimentStore.export_project/import_project` (format v1).

## Background jobs
- `quantumforge.application.jobs.JobManager` executes registered compute callables `(params, progress_cb, cancel_event) -> result` in a thread pool, updates experiment status/progress/runtime and persists results/errors. Cancellation is cooperative; timeout enforced via `resource_limits.timeout_seconds` where applicable.

## Adding computations/models
1. Implement pure computation in `quantumforge/<domain>/` (no UI coupling).
2. Register a model key and wrapper in `quantumforge/api/app.py` `COMPUTATIONS` with `(params, progress, cancel)` signature and safe parameter handling.
3. Expose/validate via API schemas as needed; ensure progress/cancellation checks for long operations.
4. Add unit/API tests and document method, units, assumptions, limitations.

## Testing & verification
- Python tests: `PYTHONPATH=. .venv/bin/python -m pytest -q` (all tests) or targeted files.
- API+persistence smoke: `PYTHONPATH=. .venv/bin/python scripts/verify_api.py`.
- Frontend: `cd frontend && npm run build` (typecheck included); lint `npm run lint` when ESLint deps installed.
- Optional (when installed): `python -m ruff check ...`, `python -m mypy quantumforge`, `pytest --cov=quantumforge`.
- Regression: keep all existing 25 baseline tests passing; add tests for schema/migrations, storage integrity, import/export round-trips, jobs/cancellation, and API.

## CI
- `.github/workflows/ci.yml` runs Python (ruff/mypy/pytest+cov, verify script) and frontend (build/lint) on GitHub runners. Windows/Tauri release workflow separate and environment-dependent.

## Conventions
- Preserve scientific correctness and documented limitations; never fabricate results.
- Maintain backward compatibility for legacy experiment endpoints where feasible.
- Prefer explicit schemas/migrations and transactional writes for persistence changes.
