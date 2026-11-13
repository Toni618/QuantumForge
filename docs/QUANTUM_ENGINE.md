# Quantum Engine — Scientific Notes (0.4.0)

## Scope
Implemented, test-backed 1D/finite-dimensional quantum models. Not a general multidimensional or large-scale quantum simulator.

## Stationary 1D Schrödinger equation
- Equation: `Hψ = Eψ`, `H = -(ħ²/2m)d²/dx² + V(x)` (defaults `ħ=1`, `m=1`, dimensionless unless specified).
- Discretization: second-order central finite differences on uniform grid, Dirichlet boundaries `ψ(x_min)=ψ(x_max)=0`.
- Solver: symmetric tridiagonal eigensolver (`scipy.linalg.eigh_tridiagonal`) for lowest states.
- Outputs: energies, normalized wavefunctions/probability densities, expectation values `<x>, <x²>, σ_x, <T>, <V>, <H>`, grid metadata.
- Potentials: harmonic, infinite/finite well (numerical), rectangular barrier/step, quartic double well, anharmonic, and safe custom expressions in `x` via restricted parser (no unrestricted eval).
- Convergence: grid-refinement helper provided; discretization/boundary/domain errors apply.

## Time-dependent evolution
- Method: Crank–Nicolson scheme `(I + iΔt/2ħ H)ψ^{n+1} = (I - iΔt/2ħ H)ψ^n` with sparse tridiagonal LU solve.
- Properties: unconditionally stable for linear Hermitian H; norm preserved up to linear-solve/roundoff (monitored as `norm_drift_max`).
- Initial state: Gaussian wavepacket `ψ(x,0)=N exp(-(x-x0)²/(4σ²)+ik0x)` normalized on grid.
- Limitations: finite domain reflections, `O(Δt², Δx²)` discretization error, sampled frames only.

## Quantum tunneling (scattering)
- Model: ideal 1D rectangular barrier, plane-wave, non-relativistic, transfer-matrix/matching solution (exact for piecewise-constant model in floating point).
- Outputs: transmission `T`, reflection `R`, amplitudes, regime, conservation error `|T+R-1|`, analytical reference formulas for `E≠V0` (`sinh` evanescent / `sin` propagating cases).
- Sweeps: energy, barrier width, barrier height.
- Limitations: idealized asymptotic states, no wavepacket transients/inelastic effects.

## Circuits and quantum information
- State-vector simulator, little-endian qubit indexing, memory `O(2^n)` (bounded; refused above safe limit). Gates: H,X,Y,Z,S,T,RX/RY/RZ,CNOT/CX,CZ,SWAP,CY,CH,CS; optional measurement sampling from final probabilities.
- Density/spin tools: Pauli/spin-½ operators, density-matrix diagnostics (Hermiticity, trace, positivity, purity, eigenvalues), Bell states, Bloch vector (1 qubit).
- Information quantities: partial trace, von Neumann entropy, entanglement entropy of reduced subsystems, fidelity (Uhlmann), trace distance.
- Channels (Kraus): bit flip, phase flip, depolarizing, amplitude damping, phase damping; diagnostics include completeness residual and output physicality checks (trace/positivity/Hermiticity).

## Validation
Automated tests cover harmonic benchmarks/convergence, potential runs, CN norm stability, tunneling conservation/analytical agreement, circuit probabilities/sampling, information identities, and channel CPTP-related diagnostics for covered cases. No independent peer review.
