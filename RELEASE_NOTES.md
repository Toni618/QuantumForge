# QuantumForge Release Notes — 0.4.0 (Engineering Preview)

Date: 2026-11-11

## Highlights
- **Quantum mechanics expansion:** multi-potential 1D stationary solver (expectations, convergence helper), Crank–Nicolson time-dependent evolution with norm diagnostics, rectangular-barrier tunneling (T/R, sweeps, analytic/conservation checks), expanded circuit simulator and sampling, quantum information metrics (partial trace, entropies, fidelity, trace distance, Bloch) and Kraus noise channels with diagnostics.
- **Black-hole/GR additions:** Kerr analytic equatorial landmarks, Schwarzschild gravitational redshift, labeled approximate accretion-disk visualization model; preserved Schwarzschild geometry/geodesics and SR tools.
- **API & managed execution:** new scientific endpoints and background job registrations for added computations; 19 verified endpoint checks including persistence.
- **Frontend:** enhanced Quantum/Black-hole panels, Math laboratory, and data-driven 3D visualization studio (projection fallback; full WebGL pending dependencies).
- **Platform:** Phase 1 project/experiment/provenance foundation preserved and verified.

## Verification (this environment)
- Pytest: **46 passed, 1 third-party warning**.
- API/SQLite verification: **19 passed, 0 failures**.
- Frontend production build: **PASS**.

## Known limitations / not verified
- Not a complete 1.0 product: many specified labs/features, i18n/themes, full 3D WebGL, AI assistant, persisted validation-record product, and exhaustive docs remain partial or unimplemented.
- Desktop installers (Linux/Windows), Rust/Tauri builds, bundled runtime, clean-install tests: **NOT VERIFIED** (Rust unavailable).
- Ruff/mypy/pytest-cov/ESLint, E2E, security SCA/audit: **NOT RUN/VERIFIED**.
- No independent scientific peer review or professional security audit.

**Classification: Engineering Preview (0.4.0).**
