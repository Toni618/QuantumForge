# FINAL_SCIENTIFIC_VALIDATION_REPORT.md

Date: 2026-11-11 | Software: QuantumForge 0.4.0 (dev) | Python: 3.14.9 (venv)

## Summary
- Automated test suite: **46 passed, 1 warning** (third-party `starlette/testclient`/anyio DeprecationWarning). No QuantumForge deprecations observed.
- API/persistence verification script: **19/19 endpoint checks passed**, SQLite persistence OK.
- Scope: software/numerical verification for covered cases only. **No independent scientific peer review.**

## Baseline preserved (25 tests) — all passing
- Safe expression parsing/rejection, units, root/integration, harmonic oscillator eigenvalues & grid refinement, Bell circuit probabilities/norm, Lindblad trace/positivity, Lorentz invariance & Minkowski interval, Schwarzschild analytic landmarks, experiment store hash/compat, spin Hermiticity/commutators, Bell density physicality, free scalar lattice dispersion/energy/IR zero-mode, Schwarzschild geodesic normalization & photon-sphere orbit, flat/2-sphere/Schwarzschild curvature identities, core API smoke endpoints.

## Phase 1 platform (7 tests) — all passing
- Legacy schema migration/import, project CRUD/duplicate/archive, experiment schema/parameter snapshot/provenance fields, project export/import round-trip, database backup/restore integrity, background experiment run and cancellation/status transitions.

## Quantum expansion — engine (7 tests) — all passing
- **Stationary 1D:** harmonic energies ~[0.5,1.5,2.5] (abs tol 2e-3, 1201 pts), expectation normalization ≈1, grid-convergence trend (finer grid closer to 0.5). Multiple potentials (finite well, barrier, double well, anharmonic) execute with finite spectra.
- **Time-dependent (Crank–Nicolson):** max norm drift < 1e-6 over sampled evolution (harmonic, Gaussian packet), sampled frames produced.
- **Tunneling (rectangular barrier, transfer-matching):** `|T+R-1| < 1e-12` (single case), matches analytic reference to < 1e-12; energy/width/height sweeps conserve to < 1e-10.
- **Circuits:** H+RZ+sampling runs; Bell state probabilities [0.5,0,0,0.5].
- **Quantum information:** Bell reduced state = I/2, von Neumann/entanglement entropy = 1 bit, fidelity/trace distance identities, Bloch norm for maximally mixed state ≈0.
- **Channels (Kraus):** bit/phase flip, depolarizing, amplitude/phase damping — completeness residual < 1e-12, output trace ≈1 (|Δ|<1e-10), min eigenvalue > -1e-10 for tested state/params.

## Quantum expansion — API (4 tests) — all passing
- Custom-potential stationary solve returns expectations/probability densities with harmonic ground energy within 5e-3.
- Time-evolution endpoint norm drift < 1e-5.
- Tunneling endpoints: conservation < 1e-12 (point) and < 1e-10 (sweep).
- Circuit sampling, Bell entanglement entropy metric ≈1 bit, channel application diagnostics consistent.

## Relativity/black-hole additions (3 tests) — all passing
- Kerr landmarks: `a=0` limits (horizon 2M, ISCO 6M) and spin ordering (`ISCO_pro < 6M < ISCO_retro`) for `a=0.5`.
- Schwarzschild redshift (static, r=10 r_s) positive; accretion-disk model returns labeled approximate visualization data.
- API: Kerr parameters, redshift, accretion-disk endpoints respond with expected fields.

## Limitations relevant to validation
- 1D/finitized models, finite grids/domains/steps, idealized scattering, small state-vector circuits, free (Gaussian) 1D lattice QFT only, Schwarzschild-equatorial geodesics and analytic Kerr landmarks (no full Kerr geodesic/ray tracing), visualization disk is an explicit approximation.
- Tolerances chosen per numerical method/grid/solver; results outside tested regimes/parameters are not validated.
- No independent peer review, no experimental cross-validation campaign beyond encoded benchmarks/identities.
