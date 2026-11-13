# Scientific methods

QuantumForge labels analytic identities separately from numerical approximations. The 1-D stationary Schrödinger solver uses a second-order central finite-difference Hamiltonian and a symmetric tridiagonal eigensolver. Open-system evolution uses DOP853 on the finite-dimensional Lindblad-GKSL equation. Root finding uses Brent-Dekker; quadrature uses QUADPACK adaptive Gauss-Kronrod; ODE integration uses SciPy solve_ivp methods.

The free scalar QFT module is a periodic finite spatial lattice in natural units. The GR geometry engine is symbolic and uses the convention recorded in the API output. Schwarzschild geodesics use adaptive DOP853 integration in geometrized units and monitor the timelike/null normalization constraint.

All methods are finite in scope. An output is not evidence of experimental confirmation, a novel theory, or a general solution to an unrestricted physical problem.
