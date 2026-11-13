# Numerical methods

| Problem | Method | Main diagnostics / limits |
|---|---|---|
| 1-D stationary Schrödinger | Second-order central finite difference; symmetric tridiagonal eigensolver | Dirichlet boundaries, grid spacing, wavefunction normalization; finite domain/grid error |
| Root finding | Brent-Dekker (`root_scalar`) | Bracket required; convergence flag, iterations, function calls |
| 1-D quadrature | QUADPACK adaptive Gauss-Kronrod | Absolute error estimate, absolute/relative tolerances |
| ODE integration | SciPy `solve_ivp` (RK45, DOP853, Radau, BDF, LSODA) | Solver status, function evaluations, tolerances |
| Lindblad evolution | DOP853 integration of GKSL master equation | Trace, Hermiticity residual and minimum eigenvalue diagnostics |
| Free scalar QFT | Exact discrete Fourier modes on finite periodic lattice | Lattice spacing/volume, zero-mode infrared warning, free-field approximation |
| Schwarzschild geodesics | DOP853 integration of second-order geodesic equations | Adaptive tolerances, four-velocity normalization residual; coordinate chart ends at horizon |

No solver's success flag alone proves physical validity. Users should vary resolution, domain and tolerances for convergence studies before interpreting computed outputs as controlled approximations.
