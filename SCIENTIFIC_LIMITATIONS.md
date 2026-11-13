# QuantumForge — Scientific Limitations (0.2.1)

> Scope unchanged from 0.2.0 baseline; no scientific algorithms modified in Phase 0.2.1. Claims must remain within implemented, tested behavior.

## Quantum mechanics
- 1D stationary Schrödinger eigenproblem via finite differences with Dirichlet boundaries; discretization and finite-domain truncation introduce error.
- Potentials/models exposed are limited to implemented API/UI paths (e.g. harmonic oscillator workflow); not a general multidimensional or arbitrary-boundary solver.
- Time-dependent wavepacket propagation/tunneling analysis as a complete, validated lab workflow is not implemented.
- State-vector circuit simulation is exponentially memory-limited (small qubit counts only) and not equivalent to large-scale quantum hardware.
- Quantum information/noise model coverage is partial relative to 1.0 targets.

## Quantum field theory
- Free real scalar field on a 1D periodic spatial lattice in natural units (Gaussian/free theory).
- No validated interacting dynamics, renormalization, scattering, or continuum-extrapolation program.
- Massless periodic zero mode causes IR divergence in field covariance (handled/reported).

## General relativity & black holes
- Symbolic metric geometry for supplied metrics under documented conventions; validated focus includes Minkowski/Schwarzschild/benchmark cases covered by tests.
- Geodesics: equatorial Schwarzschild timelike/null numerical integration in supported chart/domain with normalization diagnostics; horizon/chart limitations apply.
- No complete, validated implementations of RN/Kerr/FLRW workflows, gravitational lensing/ray-tracing physics engine, or numerical relativity (3+1/ADM evolution).
- Any visualization beyond computed numeric/analytic outputs must not be presented as a physical simulation.

## Validation & assurance
- 25 automated tests and 15 endpoint/persistence checks passed in this environment; this is software/numerical verification for covered cases only.
- **No independent scientific peer review** and **no professional security audit** performed.
- Ruff/mypy/pytest-cov/ESLint enforcement not executed locally in this session (configs added; CI/provisioned verification required).
