# QuantumForge — Final Release Checklist (as of 0.4.0, 2026-11-11)

## Automated / executable checks (this environment)
- [x] Python test suite: `PYTHONPATH=. .venv/bin/python -m pytest -q` → **46 passed, 1 warning** (third-party Starlette/anyio deprecation; no QuantumForge deprecations). Includes 25 baseline + 7 Phase 1 + 7 quantum expansion + 4 quantum API expansion + 3 black-hole/model tests.
- [x] API & SQLite persistence verification: `PYTHONPATH=. .venv/bin/python scripts/verify_api.py` → **19 endpoints verified, 0 failures, ALL_ENDPOINTS_OK, SQLITE_PERSISTENCE_OK**.
- [x] Frontend typecheck + production build: `cd frontend && npm run build` → **PASS** (tsc + Vite).
- [ ] Ruff/mypy/pytest-cov/ESLint execution: **NOT VERIFIED** (tools/packages not installed in env; configs present).
- [ ] Full CI run on clean runners: **NOT VERIFIED** locally (workflow files present).

## Core platform
- [x] Project/experiment management, versioned SQLite schema/migrations, legacy migration, import/export, backup/restore (Phase 1) — verified by tests.
- [x] Background job execution with progress/cooperative cancellation/timeout limits — verified for covered cases.
- [ ] Durable job queue across process restart, job recovery, experiment comparison/branching/templates: **PARTIAL/NOT IMPLEMENTED**.

## Scientific scope (implemented & test-backed subset)
- [x] 1D stationary Schrödinger (FD Dirichlet) with multiple potentials, expectations, convergence helper.
- [x] Time-dependent 1D evolution (Crank–Nicolson) with norm-drift diagnostics.
- [x] Rectangular-barrier tunneling T/R and sweeps with conservation/analytic checks.
- [x] Expanded circuits (common gates, rotations, controlled ops, sampling), quantum info metrics (partial trace, entropies, fidelity, trace distance, Bloch), Kraus channels with diagnostics.
- [x] Free 1D periodic scalar lattice QFT (Gaussian/free) preserved.
- [x] SR transforms, symbolic metric geometry, Schwarzschild params/geometry/geodesics preserved; Kerr analytic landmarks, Schwarzschild redshift helper, labeled accretion-disk visualization model added.
- [x] Safe math expression parsing, root finding, integration.
- [ ] Full 1.0 lab breadth (all potentials/BC variants, arbitrary custom-potential UX completeness, multidimensional/advanced QFT, RN/FLRW/full Kerr geodesics/lensing/ray tracing, complete symbolic/numeric math suite, etc.): **PARTIAL/NOT IMPLEMENTED**.

## Visualization & UX
- [x] Data-driven 2D plots and computed-data 3D projection view in frontend (rotatable). No fabricated scientific data.
- [ ] Full WebGL/Three.js GPU scene with all required controls/export/animation and every target visualization type: **PARTIAL** (Three.js dependency install unavailable in env; projection fallback implemented).
- [x] Workspace/Projects/Project/Experiment/History + scientific panels; Math lab and 3D studio pages added (scoped).
- [ ] All 13 required pages as fully featured products, i18n (fa/en), light/dark themes, command palette/shortcuts/resizable panels/accessibility completeness: **PARTIAL/NOT IMPLEMENTED**.

## AI assistant
- [ ] Optional offline-capable AI assistant with structured engine-backed workflow, secure secrets, consent/labels: **NOT IMPLEMENTED**.

## Validation center
- [x] Built-in benchmark checks and automated tests with numerical/identity verification for covered cases.
- [ ] Persisted validation records with full required schema/references/tolerances per run and UI validation center product: **PARTIAL/NOT IMPLEMENTED**.

## Desktop packaging & runtime
- [ ] Tauri/Rust build, bundled/provisioned backend runtime, Linux AppImage/deb/rpm, Windows installer/uninstaller: **NOT VERIFIED/NOT BUILT** (Rust toolchain unavailable: `cargo`/`rustc` not configured). Windows CI config exists but unrun here.
- [ ] Clean-install startup without manually started dev server: **NOT VERIFIED**.

## Security & compliance
- [x] Safe expression parsing (restricted), local loopback API posture, basic input validation in paths.
- [ ] Comprehensive security hardening, dependency audit, secure secret storage, full import/path/IPC hardening, independent audit: **PARTIAL/NOT VERIFIED**.
- [ ] Required policy/license/third-party documents complete and reviewed: **PARTIAL**.

## Documentation
- [x] Core architecture/user/developer/quantum notes and roadmap/status docs updated for 0.4.0.
- [ ] Full required documentation set complete and scientifically exhaustive for all claimed 1.0 features: **PARTIAL**.

## Release decision
- **Classification:** **Engineering Preview (0.4.0)** — not Alpha/Beta/RC/Production.
- **Blockers to 1.0 Production:** incomplete scientific lab breadth vs full spec, no verified installers (Linux/Windows), incomplete 3D WebGL pipeline/deps, missing AI assistant, incomplete validation-record product/UI, incomplete i18n/themes/accessibility, unrun lint/type/coverage/security audits, incomplete required documentation/policies, no independent scientific/security review.
