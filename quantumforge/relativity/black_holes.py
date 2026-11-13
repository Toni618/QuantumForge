"""Black hole models: Schwarzschild (exact) and Kerr equatorial/orbit landmarks (analytic formulas).

All Kerr formulas use geometrized units G=c=M=1 with spin parameter a in [0,1).
Results are analytic model outputs for idealized vacuum solutions, not full ray-traced images.
"""
from __future__ import annotations

import math

G = 6.67430e-11
C = 299_792_458.0
HBAR = 1.054571817e-34
K_B = 1.380649e-23
M_SUN = 1.98847e30


def schwarzschild_parameters(mass_kg: float):
    if mass_kg <= 0:
        raise ValueError("Mass must be positive")
    rs = 2 * G * mass_kg / C**2
    return {
        "mass_kg": mass_kg,
        "schwarzschild_radius_m": rs,
        "photon_sphere_radius_m": 1.5 * rs,
        "isco_radius_m": 3 * rs,
        "hawking_temperature_K": HBAR * C**3 / (8 * math.pi * G * mass_kg * K_B),
        "gravitational_redshift_factor_at_r": "sqrt(1-r_s/r) (static observer, r>r_s)",
        "gravitational_time_dilation_note": "Proper time dτ = dt*sqrt(1-r_s/r) for static clocks at radius r.",
        "light_bending_weak_field_note": "Deflection ≈ 4GM/(c^2*b) for impact parameter b >> r_s.",
        "model": "Schwarzschild vacuum black hole; non-rotating, uncharged",
        "status": "Exact analytic expressions for the stated idealized spacetime",
    }


def kerr_parameters(spin_a: float):
    """Kerr landmarks in units M=1 (radii in GM/c^2). spin_a = J/M^2 in [0,1)."""
    a = float(spin_a)
    if not (0 <= a < 1):
        raise ValueError("Kerr spin parameter a must satisfy 0 <= a < 1 for this model")
    r_plus = 1 + math.sqrt(1 - a * a)
    r_minus = 1 - math.sqrt(1 - a * a)
    # ergosphere equatorial boundary r_ergo(theta=pi/2)=2M
    r_ergo_eq = 2.0
    # photon circular orbits (equatorial, prograde/retrograde) Bardeen-Press-Teukolsky
    z1 = 1 + (1 - a * a) ** (1 / 3) * ((1 + a) ** (1 / 3) + (1 - a) ** (1 / 3))
    z2 = math.sqrt(3 * a * a + z1 * z1)
    r_ph_pro = 2 * (1 + math.cos((2 / 3) * math.acos(-a)))
    r_ph_retro = 2 * (1 + math.cos((2 / 3) * math.acos(a)))
    # ISCO (Bardeen 1972) equatorial
    def isco(prograde: bool):
        s = 1 if prograde else -1
        z1k = 1 + (1 - a * a) ** (1 / 3) * ((1 + a) ** (1 / 3) + (1 - a) ** (1 / 3))
        z2k = math.sqrt(3 * a * a + z1k * z1k)
        return 3 + z2k - s * math.sqrt((3 - z1k) * (3 + z1k + 2 * z2k))

    return {
        "spin_a": a,
        "units": "geometrized units G=c=M=1; radii in GM/c^2",
        "event_horizon_r_plus": r_plus,
        "inner_horizon_r_minus": r_minus,
        "ergosphere_equatorial_radius": r_ergo_eq,
        "photon_orbit_prograde": r_ph_pro,
        "photon_orbit_retrograde": r_ph_retro,
        "isco_prograde": isco(True),
        "isco_retrograde": isco(False),
        "model": "Kerr vacuum black hole; equatorial analytic landmarks",
        "assumptions": ["Ideal Kerr solution", "0 <= a < 1 (no extremal/naked singularity modeling)", "Equatorial-plane formulas for photon/ISCO orbits"],
        "limitations": ["No full Kerr geodesic integrator in this build", "No ray-traced horizon image; visualization must be labeled as model/approximation"],
    }


def gravitational_redshift_schwarzschild(r_over_rs: float):
    if r_over_rs <= 1:
        raise ValueError("r must be > r_s (outside horizon)")
    z_plus_1 = 1.0 / math.sqrt(1.0 - 1.0 / r_over_rs)
    return {"r_over_r_s": float(r_over_rs), "frequency_ratio_observed_emitted": 1.0 / z_plus_1, "redshift_z": z_plus_1 - 1.0, "model": "Static emitter/observer in Schwarzschild spacetime"}


def accretion_disk_model(r_inner: float, r_outer: float, n_r: int = 80, n_phi: int = 120):
    """Simple thin-disk emissivity profile model (Page-Thorne-like qualitative scaling) for visualization.
    NOT a full GRMHD/ray-traced disk.
    """
    if r_inner <= 0 or r_outer <= r_inner or n_r < 4 or n_phi < 8:
        raise ValueError("Invalid disk parameters")
    r = np.linspace(r_inner, r_outer, n_r)
    phi = np.linspace(0, 2 * math.pi, n_phi, endpoint=False)
    R, P = np.meshgrid(r, phi, indexing="ij")
    # qualitative emissivity: peaks outside inner edge, falls off ~r^-3
    emissivity = (1.0 / (R**3)) * np.maximum(0.0, 1.0 - np.sqrt(np.maximum(r_inner, 1e-9) / R))
    emax = float(np.max(emissivity)) or 1.0
    emissivity = emissivity / emax
    X = R * np.cos(P)
    Y = R * np.sin(P)
    Z = 0.03 * (R / r_outer)  # slight illustrative thickness cue only
    return {
        "model": "Parameterized thin-disk emissivity proxy (visualization aid)",
        "scientific_status": "approximate visualization model, not a radiative-transfer or GRMHD solution",
        "r_inner": float(r_inner), "r_outer": float(r_outer),
        "x": X.tolist(), "y": Y.tolist(), "z": Z.tolist(), "emissivity": emissivity.tolist(),
        "note": "Use for qualitative structure; label separately from physical simulation outputs.",
    }

import numpy as np  # placed at end to keep earlier numeric helpers simple; used by accretion_disk_model
