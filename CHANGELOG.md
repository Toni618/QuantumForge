# Changelog

## 0.3.0 — 2026-11-11 (Phase 1 foundation)
- Added versioned SQLite schema (v1) with migrations, projects, experiments, jobs metadata, and legacy 0.2.x experiment migration.
- Added project CRUD, duplication, archive, and JSON import/export (round-trip) plus database backup/restore.
- Added experiment records with parameters/units/initial conditions/method/solver config, status/runtime, results/errors, provenance, software version, timestamps, seeds/snapshots.
- Added background job execution service with progress, cancellation, resource limits (timeout), and status transitions.
- Added Phase 1 API endpoints and integrated Workspace/Projects/Project/Experiment/History pages in frontend.
- Preserved existing scientific endpoints and legacy `/experiments` compatibility; all 25 existing Python tests remain passing.

## 0.2.1 — 2026-11-11 (stabilization)
- Frontend dependency installation fixed and production build verified (`tsc --noEmit && vite build`).
- Added reproducible tooling/configs: `pyproject.toml` dev extras and ruff/mypy/coverage settings, frontend ESLint config, `frontend/package-lock.json`.
- Added development/verification scripts (`scripts/`) and CI workflow for Python/frontend checks.
- Verified in Linux dev environment: pytest 25/25 passed (1 third-party warning), all implemented API endpoints verified, SQLite experiment persistence verified.
- Not verified in this environment: ruff/mypy/pytest-cov/ESLint execution (tools/packages unavailable), Rust/Tauri builds, Linux/Windows installers.

## 0.2.0 — 2026-11-11
- Added spin-1/2 operator module and density-matrix physicality diagnostics.
- Added finite periodic 1-D free scalar lattice QFT module.
- Added symbolic metric tensor engine and Schwarzschild vacuum benchmark.
- Added equatorial Schwarzschild geodesic integrator and normalization diagnostics.
- Expanded FastAPI endpoints and replaced the minimal UI with a multi-workspace React scientific workbench.
- Added Tauri backend process supervision source and Windows CI release pipeline definition.
- Added explicit QFT/GR scope, validation, security and release limitation documentation.
