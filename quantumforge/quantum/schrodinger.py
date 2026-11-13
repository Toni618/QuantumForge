"""1-D stationary and time-dependent Schrödinger solvers (dimensionless defaults)."""
from __future__ import annotations

import numpy as np
from scipy.linalg import eigh_tridiagonal, solve_banded
from scipy.sparse import diags
from scipy.sparse.linalg import splu

from .potentials import potential_from_spec

HBAR = 1.0


def harmonic_oscillator(x, omega=1.0):
    return 0.5 * omega * omega * x * x


def _validate_grid(x_min, x_max, points, states, mass, hbar):
    if points < 101 or points > 20001:
        raise ValueError("points must be in [101, 20001]")
    if states < 1 or states >= points - 2:
        raise ValueError("Invalid number of eigenstates")
    if not x_min < x_max or mass <= 0 or hbar <= 0:
        raise ValueError("Invalid domain, mass, or hbar")


def _normalize_psi(psi: np.ndarray, x: np.ndarray) -> np.ndarray:
    norm = float(np.trapezoid(np.abs(psi) ** 2, x))
    if norm <= 0 or not np.isfinite(norm):
        raise ValueError("Wavefunction normalization failed")
    psi = psi / np.sqrt(norm)
    nz = np.flatnonzero(np.abs(psi) > 1e-12)
    if len(nz) and psi[nz[0]] < 0:
        psi = -psi
    return psi


def expectation_values(x: np.ndarray, psi: np.ndarray, v: np.ndarray, mass: float = 1.0, hbar: float = HBAR):
    dx = x[1] - x[0]
    prob = np.abs(psi) ** 2
    norm = float(np.trapezoid(prob, x))
    x_exp = float(np.trapezoid(x * prob, x))
    x2_exp = float(np.trapezoid(x * x * prob, x))
    # second derivative with Dirichlet endpoints
    d2 = np.zeros_like(psi, dtype=complex)
    d2[1:-1] = (psi[2:] - 2 * psi[1:-1] + psi[:-2]) / (dx * dx)
    kinetic_density = -0.5 * (hbar * hbar / mass) * np.conj(psi) * d2
    kinetic = float(np.trapezoid(kinetic_density.real, x))
    potential_e = float(np.trapezoid((v * prob).real, x))
    total = kinetic + potential_e
    return {
        "normalization": norm,
        "x_expectation": x_exp,
        "x2_expectation": x2_exp,
        "x_std": float(np.sqrt(max(x2_exp - x_exp * x_exp, 0.0))),
        "kinetic_energy": kinetic,
        "potential_energy": potential_e,
        "total_energy_expectation": total,
    }


def solve_1d(potential, x_min=-8.0, x_max=8.0, points=1201, states=6, mass=1.0, hbar=HBAR, potential_spec: dict | None = None):
    """Stationary 1D Schrödinger eigenproblem (Dirichlet, 2nd-order FD).

    `potential` may be a callable V(x) or ignored when `potential_spec` is provided.
    """
    _validate_grid(x_min, x_max, points, states, mass, hbar)
    x = np.linspace(x_min, x_max, points)
    dx = x[1] - x[0]
    if potential_spec is not None:
        v = potential_from_spec(x, potential_spec)
    else:
        v = np.asarray(potential(x), dtype=float)
    if v.shape != x.shape or not np.all(np.isfinite(v)):
        raise ValueError("Potential must return finite values matching the grid")

    kinetic = hbar * hbar / (2.0 * mass * dx * dx)
    diagonal = 2.0 * kinetic + v[1:-1]
    off = np.full(points - 3, -kinetic)
    energies, vectors = eigh_tridiagonal(diagonal, off, select="i", select_range=(0, states - 1))

    wavefunctions = []
    norms = []
    expectations = []
    for i in range(states):
        psi = np.zeros(points, dtype=complex)
        psi[1:-1] = vectors[:, i]
        psi = _normalize_psi(psi.real.astype(complex), x)
        wavefunctions.append(psi.real.tolist())
        norms.append(float(np.trapezoid(np.abs(psi) ** 2, x)))
        expectations.append(expectation_values(x, psi, v, mass=mass, hbar=hbar))

    prob_densities = [[(float(abs(psi_i) ** 2)) for psi_i in wf] for wf in wavefunctions]
    return {
        "x": x.tolist(),
        "potential": v.tolist(),
        "energies": energies.tolist(),
        "wavefunctions": wavefunctions,
        "probability_densities": prob_densities,
        "normalization": norms,
        "expectation_values": expectations,
        "grid_spacing": float(dx),
        "points": points,
        "states": states,
        "mass": float(mass),
        "hbar": float(hbar),
        "potential_spec": potential_spec,
        "method": "second-order central finite differences + symmetric tridiagonal eigensolver",
        "boundary_condition": "Dirichlet psi(x_min)=psi(x_max)=0",
        "units": "dimensionless unless physical SI parameters are supplied",
        "limitations": [
            "Finite domain and grid introduce discretization and boundary-truncation error.",
            "Second-order spatial stencil.",
            "Potential barriers/wells are resolved only to grid scale; very high/abrupt features approximate limiting behavior.",
            "This is a 1-D stationary solver, not a general 3-D or time-dependent solver.",
        ],
    }


def stationary_convergence(potential, grids, states=1, x_min=-8.0, x_max=8.0, mass=1.0, hbar=HBAR, potential_spec=None):
    """Compute lowest eigenvalues across grid sizes for convergence inspection."""
    rows = []
    for pts in grids:
        r = solve_1d(potential, x_min=x_min, x_max=x_max, points=int(pts), states=states, mass=mass, hbar=hbar, potential_spec=potential_spec)
        rows.append({"points": int(pts), "grid_spacing": r["grid_spacing"], "energies": r["energies"]})
    return {
        "study": "stationary_grid_convergence",
        "states": states,
        "results": rows,
        "note": "Decreasing grid spacing should reduce discretization error for well-resolved states/boundaries.",
    }


# ---- Time-dependent solver (Crank–Nicolson, Dirichlet) ----

def gaussian_wavepacket(x: np.ndarray, x0: float, k0: float, sigma: float):
    norm = (1.0 / (2.0 * np.pi * sigma * sigma)) ** 0.25
    psi = norm * np.exp(-((x - x0) ** 2) / (4.0 * sigma * sigma) + 1j * k0 * x)
    return psi.astype(complex)


def evolve_1d_cn(
    potential_spec: dict,
    x_min=-10.0,
    x_max=10.0,
    points=801,
    dt=0.01,
    steps=400,
    mass=1.0,
    hbar=HBAR,
    packet: dict | None = None,
    sample_every: int = 10,
):
    """Crank–Nicolson time evolution: (I + i*dt/2*H) psi^{n+1} = (I - i*dt/2*H) psi^n.

    Unconditionally stable for this linear Schrödinger equation and norm-preserving for
    Hermitian H up to linear-solve error. Dirichlet boundaries psi=0 at endpoints.
    """
    if points < 101 or points > 5001:
        raise ValueError("points must be in [101, 5001]")
    if dt <= 0 or steps < 1 or steps > 20000:
        raise ValueError("Invalid dt/steps")
    if sample_every < 1:
        sample_every = 1
    x = np.linspace(x_min, x_max, points)
    dx = x[1] - x[0]
    v = potential_from_spec(x, potential_spec)
    n = points - 2
    kinetic = hbar * hbar / (2.0 * mass * dx * dx)
    diag_h = 2.0 * kinetic + v[1:-1]
    off_h = np.full(n - 1, -kinetic)

    # sparse tridiagonal H (interior)
    H = diags([off_h, diag_h, off_h], offsets=[-1, 0, 1], format="csc", dtype=complex)
    I = diags([np.ones(n, dtype=complex)], [0], format="csc")
    alpha = 1j * dt / (2.0 * hbar)
    A = (I + alpha * H).tocsc()
    B = (I - alpha * H).tocsc()
    lu = splu(A)

    pkt = packet or {"x0": -3.0, "k0": 2.0, "sigma": 0.5}
    psi = np.zeros(points, dtype=complex)
    psi[:] = gaussian_wavepacket(x, float(pkt.get("x0", -3.0)), float(pkt.get("k0", 2.0)), float(pkt.get("sigma", 0.5)))
    psi[0] = 0.0
    psi[-1] = 0.0
    psi = _normalize_psi(psi, x)

    times = [0.0]
    norms = [float(np.trapezoid(np.abs(psi) ** 2, x))]
    x_expect = [expectation_values(x, psi, v, mass, hbar)["x_expectation"]]
    energies = [expectation_values(x, psi, v, mass, hbar)["total_energy_expectation"]]
    samples = [{"t": 0.0, "psi_real": psi.real.tolist(), "psi_imag": psi.imag.tolist(), "probability_density": (np.abs(psi) ** 2).tolist()}]

    for step in range(1, steps + 1):
        rhs = B.dot(psi[1:-1])
        psi[1:-1] = lu.solve(rhs)
        psi[0] = 0.0
        psi[-1] = 0.0
        t = step * dt
        if step % sample_every == 0 or step == steps:
            ev = expectation_values(x, psi, v, mass, hbar)
            times.append(t)
            norms.append(ev["normalization"])
            x_expect.append(ev["x_expectation"])
            energies.append(ev["total_energy_expectation"])
            samples.append({"t": t, "psi_real": psi.real.tolist(), "psi_imag": psi.imag.tolist(), "probability_density": (np.abs(psi) ** 2).tolist()})

    norm_drift = float(max(abs(nm - 1.0) for nm in norms))
    return {
        "x": x.tolist(),
        "potential": v.tolist(),
        "dt": float(dt),
        "steps": steps,
        "times": times,
        "norm": norms,
        "x_expectation": x_expect,
        "total_energy_expectation": energies,
        "samples": samples,
        "norm_drift_max": norm_drift,
        "potential_spec": potential_spec,
        "packet": pkt,
        "method": "Crank–Nicolson (sparse tridiagonal), Dirichlet boundaries",
        "stability": "Unconditionally stable linear scheme for Hermitian H; norm preserved up to linear-solve/roundoff error.",
        "units": "dimensionless unless physical SI parameters are supplied",
        "limitations": [
            "Finite spatial domain and grid; reflections can occur at boundaries for outgoing packets.",
            "Time discretization error O(dt^2); spatial discretization error O(dx^2).",
            "Sampled frames only are returned to bound payload size.",
        ],
    }
