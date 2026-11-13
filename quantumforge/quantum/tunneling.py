"""1D quantum scattering/tunneling for piecewise-constant barriers (analytic transfer matching).

Model: plane wave incident from left on a single rectangular barrier/well region in an
otherwise constant potential, using time-independent Schrödinger equation matching.
This is an exact solution of the idealized piecewise-constant model (within floating-point
precision), not an arbitrary fit.
"""
from __future__ import annotations

import cmath
import math

HBAR = 1.0


def _k(E: float, V: float, mass: float, hbar: float) -> complex:
    # k = sqrt(2m(E-V))/hbar; complex for E<V (evanescent)
    val = 2.0 * mass * (E - V)
    if val >= 0:
        return complex(math.sqrt(val) / hbar, 0.0)
    return complex(0.0, math.sqrt(-val) / hbar)


def rectangular_barrier(E: float, V0: float, L: float, mass: float = 1.0, hbar: float = HBAR) -> dict:
    if E <= 0 or L <= 0 or mass <= 0 or hbar <= 0:
        raise ValueError("Require E>0, L>0, mass>0, hbar>0")
    if V0 < 0:
        raise ValueError("Rectangular barrier height V0 must be >= 0 for this model")

    k1 = _k(E, 0.0, mass, hbar)
    k2 = _k(E, V0, mass, hbar)

    # Transfer matrix through region II [0,L]: psi(L)=M00*psi(0)+M01*psi'(0), psi'(L)=M10*psi(0)+M11*psi'(0)
    if abs(k2) < 1e-14:
        M00, M01, M10, M11 = 1.0 + 0j, L + 0j, 0.0 + 0j, 1.0 + 0j
        regime = "threshold (E≈V0)"
    else:
        c = cmath.cos(k2 * L)
        s = cmath.sin(k2 * L)
        M00, M01, M10, M11 = c, s / k2, -k2 * s, c
        regime = "propagating (E>V0)" if E > V0 else ("evanescent/tunneling (E<V0)" if E < V0 else "threshold")

    # Incident 1 from left, transmitted T to right, reflected R: A_denom = i*k1*(M00+i*k1*M01) + (M10+i*k1*M11)
    X = M00 + 1j * k1 * M01
    Y = M10 + 1j * k1 * M11
    denom = 1j * k1 * X + Y
    T_amp = (2j * k1) / denom
    R_amp = (1j * k1 * X - Y) / denom

    T = float(abs(T_amp) ** 2)
    R = float(abs(R_amp) ** 2)

    analytical = None
    if abs(E - V0) > 1e-12:
        if E < V0:
            kappa = math.sqrt(2.0 * mass * (V0 - E)) / hbar
            sinh = math.sinh(kappa * L)
            denom_a = 1.0 + (V0 * V0 * sinh * sinh) / (4.0 * E * (V0 - E))
            analytical = {"T": 1.0 / denom_a, "R": 1.0 - 1.0 / denom_a, "formula": "T=1/(1+V0^2*sinh^2(kappa*L)/(4E(V0-E)))"}
        else:
            k2r = math.sqrt(2.0 * mass * (E - V0)) / hbar
            sin2 = math.sin(k2r * L) ** 2
            denom_a = 1.0 + (V0 * V0 * sin2) / (4.0 * E * (E - V0))
            analytical = {"T": 1.0 / denom_a, "R": 1.0 - 1.0 / denom_a, "formula": "T=1/(1+V0^2*sin^2(k2*L)/(4E(E-V0)))"}

    return {
        "energy": float(E),
        "barrier_height": float(V0),
        "barrier_width": float(L),
        "mass": float(mass),
        "hbar": float(hbar),
        "transmission": T,
        "reflection": R,
        "conservation_error": float(abs(T + R - 1.0)),
        "regime": regime,
        "amplitudes": {"T_real": float(T_amp.real), "T_imag": float(T_amp.imag), "R_real": float(R_amp.real), "R_imag": float(R_amp.imag)},
        "analytical_reference": analytical,
        "model": "Ideal 1D rectangular barrier, plane-wave scattering, transfer/matching solution",
        "assumptions": ["Piecewise-constant potential", "Single barrier region [0,L]", "Asymptotic plane waves, no inelastic effects", "Non-relativistic Schrödinger equation"],
        "limitations": ["Idealized geometry", "Does not include wavepacket dispersion/transients", "Numerical precision limits very near resonances/extreme evanescence"],
    }


def sweep_energy(V0: float, L: float, energies, mass: float = 1.0, hbar: float = HBAR):
    rows = []
    for E in energies:
        e = float(E)
        if e <= 0:
            continue
        rows.append(rectangular_barrier(e, V0, L, mass=mass, hbar=hbar))
    return {"sweep": "energy", "barrier_height": float(V0), "barrier_width": float(L), "results": rows, "conservation_max_error": float(max((r["conservation_error"] for r in rows), default=0.0))}


def sweep_width(E: float, V0: float, widths, mass: float = 1.0, hbar: float = HBAR):
    rows = [rectangular_barrier(E, V0, float(L), mass=mass, hbar=hbar) for L in widths if float(L) > 0]
    return {"sweep": "barrier_width", "energy": float(E), "barrier_height": float(V0), "results": rows, "conservation_max_error": float(max((r["conservation_error"] for r in rows), default=0.0))}


def sweep_height(E: float, heights, L: float, mass: float = 1.0, hbar: float = HBAR):
    rows = [rectangular_barrier(E, float(V0), L, mass=mass, hbar=hbar) for V0 in heights if float(V0) >= 0]
    return {"sweep": "barrier_height", "energy": float(E), "barrier_width": float(L), "results": rows, "conservation_max_error": float(max((r["conservation_error"] for r in rows), default=0.0))}
