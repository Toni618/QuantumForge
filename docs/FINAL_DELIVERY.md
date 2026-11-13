# QuantumForge 0.2.0 — delivery status

## Delivered in this source build
- Python scientific package source and wheel.
- FastAPI local computational API.
- React/TypeScript desktop frontend source.
- Tauri 2 desktop shell source with backend process supervision.
- Quantum spin/density-matrix features, free scalar lattice QFT, symbolic Schwarzschild metric geometry, and Schwarzschild equatorial geodesic integration.
- 23 executable Python tests and scientific-method/limitation/security documentation.
- Windows GitHub Actions release workflow source.

## Verified in this environment
- Python test suite: 25 passed.
- Python bytecode compilation: passed.
- Python wheel: built as `quantumforge-0.2.0-py3-none-any.whl`.
- Wheel install/import smoke check: passed when using the environment's already-installed scientific dependencies.
- API smoke checks: health, spin operators, Bell density matrix, Schwarzschild geometry, free scalar lattice and geodesic endpoints returned successful responses.
- Schwarzschild vacuum benchmark: Ricci scalar and all Ricci tensor components simplify to zero.
- Circular-orbit geodesic benchmark: four-velocity normalization residual below 1e-8 in the test.

## Not verified / not delivered
- React production build: blocked because npm registry DNS/network access was unavailable; no `node_modules` cache was present.
- Tauri compilation: not run; Rust and Cargo are absent in this environment.
- Windows MSI/NSIS installer: not produced or inspected. A CI workflow is provided but has not run.
- Linux AppImage/DEB/RPM: not produced.
- Embedded Python runtime is planned in the Windows workflow through PyInstaller but has not been built or validated here.
- Independent scientific review: not performed.
- Professional security audit and code signing: not performed.
- Full interacting QFT, arbitrary Einstein PDE solver, Kerr engine and many other requested domains remain out of scope.

**Release classification:** engineering source build / pre-release. Not ready for commercial sale or distribution as a finished desktop installer.
