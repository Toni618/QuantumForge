# QuantumForge — Existing Features (0.2.1, verified by inspection and executed checks)

## Verified in current session
- **Backend tests:** 25/25 pytest tests passing (`.venv`, Python 3.14.9) with 1 third-party warning.
- **API verification script:** 15 endpoint checks passed (health, math, quantum, QFT, relativity/black-hole, experiments) and SQLite persistence confirmed (save/get and reopen via fresh store).
- **Frontend:** dependency install completed, TypeScript compile + Vite production build succeeded (`frontend/dist` produced).

## Scientific engines (implemented, unchanged in 0.2.1)
- **Core/math:** safe symbolic expression parsing, unit conversion, root finding, numerical integration.
- **Quantum mechanics:** 1D stationary Schrödinger finite-difference eigensolver (Dirichlet), harmonic potential helper, state-vector circuit simulation (H/X/Y/Z/CNOT, practical small-n limit), spin-1/2 operators, density-matrix diagnostics, Bell state density, Lindblad/open-system evolution (as covered by tests).
- **QFT:** free real scalar field on 1D periodic spatial lattice (natural units): dispersion/mode frequencies, vacuum energy, equal-time covariance with IR zero-mode handling.
- **Relativity/GR:** Lorentz boosts & metric invariance/Minkowski interval, Schwarzschild analytic parameters, symbolic metric geometry (Christoffel/Ricci/Einstein/scalar), Schwarzschild metric/geometry endpoint, equatorial timelike/null Schwarzschild geodesics with normalization diagnostics.

## Application/API
- FastAPI local service (`quantumforge.api.app`, v0.2.1) with loopback-oriented CORS for Tauri/local dev.
- SQLite experiment store: content-addressed save/get for `{model, config, result}`.

## Frontend
- React/TypeScript/Vite SPA with domain panels (Overview, Quantum, QFT, Relativity, Black hole, Validation), backend health polling, API-driven computations, SVG plots and raw JSON display. Build verified.

## Desktop
- Tauri 2 shell and bundle configuration present; backend process supervision logic present. **Packaging/build NOT VERIFIED** in this environment (Rust unavailable).

## Tooling & reproducibility additions (0.2.1)
- `pyproject.toml`: version bump, dev extras declared, pytest/ruff/mypy/coverage configuration.
- Frontend: `package-lock.json`, ESLint flat config, npm scripts (`build`, `typecheck`, `lint`).
- Scripts: backend/frontend dev, Python tests, frontend build, API/persistence verifier, aggregate verifier.
- CI workflow: `.github/workflows/ci.yml` for Python + frontend checks (execution in GitHub environment not run here).

## Not yet implemented (1.0 scope)
Project/experiment lifecycle & provenance platform, background jobs, expanded quantum/QFT/GR labs, real 3D visualization engine, mathematical lab, AI assistant, persisted validation center, full multi-page UX/i18n, migrations/portable formats, security hardening, and verified cross-platform installers remain future work.
