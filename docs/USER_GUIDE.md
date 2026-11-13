# User Guide — QuantumForge 0.3.0

## Start
- **Backend:** Python 3.11+ with dependencies installed (`python -m pip install -e '.[dev]'` in a venv). Run `quantumforge-api` (binds to `127.0.0.1:8765` by default). DB path via `QUANTUMFORGE_DB`.
- **Frontend:** `cd frontend && npm install && npm run dev` (Vite). For production assets: `npm run build`.
- **Desktop:** Tauri shell source in `src-tauri/` (requires Rust toolchain and platform prerequisites) — not verified in all environments.
The UI status must show **ENGINE CONNECTED** before running computations.

## Workspace & projects
- **Workspace:** overview of recent projects and experiments.
- **Projects:** create projects (name/description), open project details, import a previously exported project JSON.
- **Project details:** rename, duplicate, archive/unarchive, export project JSON; create experiments from supported computation models and run them in background; browse project experiments.

## Experiments
- **Create:** choose model/domain, enter parameters, save as draft or **Save & run**. Each experiment records configuration, parameter snapshot, provenance/software/version metadata, timestamps, and execution status.
- **Run/cancel:** managed runs execute in background with progress/status; cancellable while queued/running (cooperative/timeout-limited by model).
- **Experiment details:** view status/progress, configuration snapshot, execution/provenance, job info, errors, and JSON result.
- **History:** global list of experiments across projects.

Supported managed computation models (Phase 1): `math.root`, `quantum.schrodinger.harmonic`, `qft.free_scalar_lattice`, `relativity.schwarzschild`, `relativity.schwarzschild.geometry` (and additional registered models via API).

## Scientific labs (preserved)
Quantum mechanics (1D harmonic Schrödinger, Bell density diagnostics), QFT (free scalar lattice), Relativity (Schwarzschild geometry), Black-hole physics (parameters, equatorial geodesic), and Validation panels remain available and call real numerical/symbolic computations. Results include method/assumption notes and raw JSON.

## Import/export & backup
- **Project export/import:** JSON format `quantumforge.project-export` v1 (download from Project details; import from Projects). Import creates a new project copy with experiments.
- **Database backup/restore:** available via admin API endpoints (`/admin/backup`, `/admin/restore`) for local maintenance; restore re-applies migrations.

## Interpretation & limitations
- Finite-grid/integrated results are numerical approximations; symbolic tensor results follow documented conventions.
- QFT is a free 1D periodic lattice model (no interactions/renormalization). GR/black-hole coverage is Schwarzschild-focused/equatorial where implemented.
- Not a complete QFT/numerical-relativity platform, not a large-scale quantum simulator, not independently peer-reviewed or security-audited. See `docs/KNOWN_LIMITATIONS.md` and `SCIENTIFIC_LIMITATIONS.md`.
