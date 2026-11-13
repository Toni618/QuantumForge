# Relativity engine — implemented scope (0.2.0)

Special relativity includes Lorentz boosts and Minkowski interval calculations using signature `(-,+,+,+)` and `β=v/c`.

The symbolic metric engine accepts a finite-dimensional symmetric non-singular metric and coordinates, computes its inverse, determinant, Christoffel symbols, Ricci tensor, Ricci scalar and Einstein tensor. The Riemann convention is explicitly returned by the API:

`R^ρ_{ σμν}=∂μΓ^ρ_{νσ}−∂νΓ^ρ_{μσ}+Γ^ρ_{μλ}Γ^λ_{νσ}−Γ^ρ_{νλ}Γ^λ_{μσ}`.

A Schwarzschild metric in coordinates `(t,r,θ,φ)` is included as a symbolic vacuum benchmark. This is symbolic differential geometry, not a numerical solver for arbitrary Einstein initial-value problems.

The geodesic integrator covers equatorial timelike and null geodesics of Schwarzschild spacetime in geometrized units `G=c=M=1`. It integrates the second-order geodesic equations with SciPy DOP853 and reports the four-velocity normalization residual. The Schwarzschild coordinate chart terminates at the horizon; the current integrator stops at that coordinate boundary and does not continue through it.

Black-hole scalar formulae cover the non-rotating, uncharged Schwarzschild solution only. Kerr, numerical relativity, accretion dynamics, gravitational lensing ray tracing and Penrose diagram construction are not implemented.
