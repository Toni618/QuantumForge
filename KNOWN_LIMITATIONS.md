# Known Limitations (0.4.0)

## Scientific scope
- **Quantum:** 1D stationary (FD, Dirichlet) and 1D Crank–Nicolson time evolution on finite domains/grids; idealized rectangular-barrier scattering (transfer-matching, asymptotic plane waves). State-vector circuits limited by exponential memory (safe caps). Finite-dimensional channels/metrics as implemented. Not a general 3D/many-body/large-scale quantum platform.
- **QFT:** free real scalar field on 1D periodic lattice (Gaussian) only — no interactions, renormalization, or scattering engine.
- **Relativity/black holes:** SR + symbolic metric geometry + Schwarzschild parameters/geodesics (equatorial, chart-limited) + analytic Kerr equatorial landmarks + simple redshift helper. No full Kerr geodesics, no RN/FLRW solvers, no lensing/ray-tracing physics engine, no numerical relativity. Accretion-disk view is an explicitly labeled approximate visualization model.
- **Math:** safe expression parsing, root finding, adaptive quadrature; broader symbolic/numeric/plotting suite incomplete.

## Visualization & UX
- 3D studio renders computed data via interactive projection; full WebGL/Three.js GPU renderer/controls/exports not fully integrated in this environment (dependency constraints). Not all specified visualization types/pages/i18n/themes/accessibility/command features implemented.

## Platform & packaging
- In-process background jobs (not durable across restart). Experiment comparison/branching/templates and full validation-record persistence/UI incomplete.
- Tauri/Rust builds and Linux/Windows installers **not built/verified**; bundled backend runtime for end users **not verified**. App may require dev-managed backend in unverified setups.

## Validation, security, compliance
- Automated tests verify covered cases only; no independent scientific peer review, no professional security audit. Lint/type/coverage/ESLint/SCA not executed in this environment. AI assistant not implemented.

## Accuracy statement
Results are numerical/analytic within documented models and tolerances. Unsupported regimes/features must be treated as unavailable, not approximated by fabricated outputs.
