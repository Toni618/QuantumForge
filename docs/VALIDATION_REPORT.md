# Validation report — 0.2.0

## Verification layers

- Software tests: executable pytest suite; run locally with `python -m pytest -q`.
- Numerical verification: unit normalization, finite-grid output checks, density-matrix diagnostics, and geodesic normalization residuals.
- Physical validation: analytic identities/benchmarks for Pauli commutators, Bell-state purity, Schwarzschild vacuum Ricci tensor, and a circular timelike Schwarzschild orbit.
- Independent scientific review: **not performed**. No external reviewer, publication reproduction campaign, or independent audit is claimed.

## Known limits

Passing this test suite does not establish correctness for arbitrary user models. The QFT benchmark is a free lattice scalar field; GR benchmarks use a prescribed Schwarzschild metric. No general Einstein PDE solver or interacting QFT is validated.
