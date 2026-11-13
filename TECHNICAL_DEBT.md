# QuantumForge — Technical Debt (post 0.2.1 stabilization)

## Resolved/improved in 0.2.1
- Frontend dependencies installed with lockfile; production build and TS check verified.
- Reproducibility/tooling scaffolding added: `pyproject.toml` dev extras and lint/type/coverage configs, frontend ESLint config/scripts, dev/verify scripts, CI workflow for Python+frontend.
- Explicit API+SQLite verification script added and passing.
- Version metadata bumped to 0.2.1 in core package/frontend config.

## Remaining debt / gaps
### Tooling enforcement (environment-limited now)
- `ruff`, `mypy`, `pytest-cov`, and frontend ESLint packages not installed locally; configured checks not executed here (must pass in CI/provisioned env).
- Third-party deprecation warning persists in tests under current dependency/Python stack (`starlette/httpx/anyio` interaction) — not a QuantumForge code regression but should be monitored.

### Architecture & data
- Monolithic API and minimal experiment storage (no projects, schema versioning/migrations, rich provenance, export/import format, history management).
- No background job system (progress/cancellation/limits) for long computations.
- Reproducibility metadata (seeds, software/dependency snapshots, deterministic controls) incomplete.

### Frontend/UX
- Single-page implementation with mixed concerns; no project/experiment management UI, no i18n, limited accessibility/shortcuts/panels.
- Visualization limited to 2D SVG plots; no real 3D/WebGL/Three.js data-driven engine.

### Scientific scope
- Quantum: stationary 1D focus; no complete time-dependent/tunneling workflows exposed, limited gate/channel coverage vs 1.0 goals.
- QFT: free 1D periodic scalar lattice only; no interacting/validated advanced methods.
- GR/black holes: Schwarzschild-centric subset; no fully validated RN/Kerr/FLRW/lensing/numerical relativity capabilities.
- Validation results not persisted as structured, reference-traceable records.

### Desktop/packaging/security
- Backend runtime bundling/embedding incomplete and unverified; no Rust toolchain locally.
- Linux/Windows installers not built or tested in this environment.
- Security hardening incomplete (no comprehensive scanning, secret storage, local auth/resource-limit framework, import/path hardening system).

### Documentation
- Required 1.0 documentation set incomplete; existing docs need alignment with 0.2.1 verified status and future milestones.
