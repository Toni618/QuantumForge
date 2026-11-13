# Quantum field theory engine — implemented scope (0.2.0)

The implemented QFT model is a free real scalar field on a one-dimensional periodic spatial lattice, in natural units `ℏ=c=1`. For `N` sites and spacing `a`, the discrete lattice dispersion is

`ω_k² = m² + (2/a sin(πk/N))²`.

The finite-lattice vacuum energy is `E0 = 1/2 Σ_k ω_k`. For a strictly positive spectrum, the equal-time two-point covariance at lattice displacement `j` is computed by the discrete inverse Fourier transform of `1/(2ω_k)`. For a massless periodic field, the zero mode is infrared singular; the covariance is intentionally omitted and an explicit warning is returned.

This is a finite-volume Gaussian/free-field calculation. It is not an interacting QFT engine: no φ⁴ vertices, perturbative amplitudes, renormalization, gauge fields, fermionic path integrals, scattering cross sections, or curved-spacetime particle creation are implemented.
