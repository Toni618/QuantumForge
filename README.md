# QuantumForge 0.4.0

QuantumForge is a local scientific computing workbench. This 0.4.0 build expands the quantum mechanics laboratory (potentials, time-dependent Crank–Nicolson evolution, rectangular-barrier tunneling sweeps, expanded circuits/channels/quantum-information metrics) and black-hole model outputs, and adds a project/experiment management foundation (SQLite schema v1, migrations, provenance, import/export, background jobs) while preserving the 0.2.x scientific engines and API compatibility. It is not a complete general-purpose QFT or numerical-relativity package and is not a verified/signed desktop distribution.

## Implemented scientific scope

- Safe symbolic expression parsing, root finding, adaptive quadrature and ODE integration.
- 1-D stationary Schrödinger eigenproblem with second-order finite differences and Dirichlet boundaries.
- State-vector circuits with H/X/Y/Z/CNOT gates (up to 20 qubits; memory scales exponentially).
- Spin-1/2 operators and density-matrix diagnostics.
- Free real scalar QFT on a 1-D periodic spatial lattice in natural units.
- Special-relativistic Lorentz boosts and Minkowski interval.
- Symbolic metric geometry (Christoffel, Ricci, Einstein tensors) and Schwarzschild vacuum benchmark.
- Equatorial timelike/null Schwarzschild geodesics with DOP853 integration and normalization diagnostics.
- Schwarzschild radius, photon sphere, ISCO and Hawking temperature formulae for the non-rotating uncharged solution.

See `docs/KNOWN_LIMITATIONS.md` for explicit exclusions.

## Run the backend

Python 3.11+:

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pytest -q
quantumforge-api
```

Backend health: `http://127.0.0.1:8765/health`.

## Build the frontend

```bash
cd frontend
npm install
npm run build
```

## Desktop shell

Install Tauri 2 prerequisites and Rust stable/Cargo. `src-tauri` contains the native shell and local backend process supervisor. The Windows CI pipeline is defined in `.github/workflows/windows-release.yml`; it has not yet been run. A Windows installer must be generated and inspected by that pipeline before distribution. No MSI/NSIS file is included here.

## Scientific and security status

Software tests are not independent scientific review. The validation report distinguishes software tests, numerical verification, physical benchmark checks and independent review. Independent scientific review and professional security audit have not been performed. See `docs/VALIDATION_REPORT.md` and `docs/SECURITY_REPORT.md`.
