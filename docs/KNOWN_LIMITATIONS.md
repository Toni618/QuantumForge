# Known limitations — 0.2.0

- The product is an engineering release candidate, not a scientifically complete all-domain platform.
- QFT: free scalar lattice only; no interactions, renormalization or scattering engine.
- Quantum: 1-D stationary Schrödinger only; finite-dimensional spin/density checks and small state-vector circuits. No full 2-D/3-D, quantum optics or many-body suite.
- GR: symbolic metric tensor algebra and Schwarzschild equatorial geodesics only. No arbitrary Einstein field-equation initial-value solver, Kerr geodesics or numerical relativity.
- The Schwarzschild geodesic chart stops at the event horizon; horizon-penetrating coordinates are not implemented.
- API uses a local loopback HTTP service. It is not intended to be exposed to a network.
- Tauri source starts a Python backend from bundled resources, but the Python interpreter and third-party runtime dependencies are not embedded. A production installer must bundle a tested backend executable or an embedded Python runtime.
- Independent scientific review and professional security audit have not been performed.
- A Windows installer has not been built or verified in this Linux environment; Rust/Cargo are unavailable here.
