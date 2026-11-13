# QuantumForge Implementation Roadmap (status updated 2026-11-11, 0.4.0)

## Completed / verified baselines
- **0.2.1 (Phase 0 stabilization):** audit/backup, frontend build fixed, reproducible config/scripts/CI scaffolding, 25 baseline tests + API/SQLite verification passing in dev env.
- **0.3.0 (Phase 1 foundation):** schema v1 migrations (legacy import), projects/experiments CRUD+archive+duplicate, export/import, provenance/snapshots/seeds, background job manager (progress/cancel/timeout), management UI pages; +7 tests (32 total at that point).
- **0.4.0 (incremental expansion, this pass):** quantum lab expansion — stationary potentials/expectations/convergence helper, Crank–Nicolson time evolution, rectangular tunneling T/R+sweeps (analytic/conservation checks), expanded circuits+sampling, quantum info (partial trace/entropies/fidelity/trace distance/Bloch), Kraus channels; new quantum/relativity/black-hole API endpoints and managed job registrations; Kerr landmarks, Schwarzschild redshift, labeled accretion-disk visualization model; Math lab & data-driven 3D projection studio UI; docs/tests updated. **Verified:** 46 tests passed, 19 API checks passed, frontend build passed.

## Partially implemented (honest)
- 3D visualization: computed-data interactive projection; full WebGL/Three.js GPU pipeline pending dependency/tooling availability in env.
- Validation center: automated benchmarks/tests exist; persisted per-run validation records/UI schema not complete.
- Platform durability: in-process jobs (not restart-durable queue), limited comparison/branching/templates.
- Scientific breadth: QFT remains free 1D periodic scalar; GR/black-hole beyond implemented Schwarzschild/Kerr-landmark subset not complete; math lab limited to safe numeric endpoints.
- UX: core pages present; full 13-page productization, en/fa i18n, themes, command palette, resizable panels, accessibility complete — not finished.

## Not implemented / not verified
- Optional AI assistant (engine-backed, offline-capable, secure secrets/consent) — not implemented.
- Linux/Windows verified installers, bundled backend runtime, clean-install desktop validation — **NOT VERIFIED** (Rust toolchain unavailable).
- Ruff/mypy/pytest-cov/ESLint gate execution, E2E UI tests, security SCA/audit — **NOT RUN/NOT VERIFIED**.
- Independent scientific peer review — not performed.

## Prioritized path forward
1. **Environment/tooling:** provision Rust/Tauri + Node deps (Three.js) + Python dev tools; run lint/type/coverage in CI.
2. **Complete quantum lab:** additional BCs/potentials UX, richer time-dependent analyses/exports, extended channel/circuit validation matrices.
3. **QFT/GR:** scoped, validated extensions (documented models only) — no unsupported claims.
4. **3D & UX:** integrate Three.js WebGL renderer, required controls/exports, full page set, i18n/themes/accessibility/command palette.
5. **Validation platform:** persisted structured validation records and UI per spec.
6. **AI (optional):** schema-validated, engine-mediated assistant with offline mode and consent.
7. **Packaging:** bundle backend, produce/test Linux & Windows installers, clean-install smoke tests.
8. **Docs/compliance:** complete required guides, policies, third-party notices, final audits.

**Release stance:** Engineering Preview until verified against 1.0 acceptance criteria.
