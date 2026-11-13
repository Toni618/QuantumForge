"""Standard 1D potential models and safe custom potential evaluation."""
from __future__ import annotations

import numpy as np

from quantumforge.core.expressions import parse_expression


def potential_from_spec(x: np.ndarray, spec: dict) -> np.ndarray:
    """Return V(x) for a potential specification.

    Supported types:
      - harmonic: {omega, mass}
      - infinite_well: {width, center, v_outside}
      - finite_well: {depth, width, center}
      - barrier: {height, width, center}
      - step: {height, position}
      - double_well: {a, b} for V=a*x^4-b*x^2 (symmetric quartic)
      - anharmonic: {omega, lambda}
      - custom: {expression} in variable x (safe parser)
    """
    ptype = (spec or {}).get("type", "harmonic")
    x = np.asarray(x, dtype=float)

    if ptype == "harmonic":
        omega = float(spec.get("omega", 1.0))
        mass = float(spec.get("mass", 1.0))
        return 0.5 * mass * omega * omega * x * x

    if ptype == "infinite_well":
        width = float(spec.get("width", 2.0))
        center = float(spec.get("center", 0.0))
        v_out = float(spec.get("v_outside", 1e6))
        left, right = center - width / 2, center + width / 2
        v = np.full_like(x, v_out, dtype=float)
        inside = (x >= left) & (x <= right)
        v[inside] = 0.0
        return v

    if ptype == "finite_well":
        depth = float(spec.get("depth", 10.0))
        width = float(spec.get("width", 2.0))
        center = float(spec.get("center", 0.0))
        left, right = center - width / 2, center + width / 2
        v = np.zeros_like(x, dtype=float)
        outside = (x < left) | (x > right)
        v[outside] = depth
        return v

    if ptype == "barrier":
        height = float(spec.get("height", 5.0))
        width = float(spec.get("width", 1.0))
        center = float(spec.get("center", 0.0))
        left, right = center - width / 2, center + width / 2
        v = np.zeros_like(x, dtype=float)
        inside = (x >= left) & (x <= right)
        v[inside] = height
        return v

    if ptype == "step":
        height = float(spec.get("height", 1.0))
        position = float(spec.get("position", 0.0))
        v = np.zeros_like(x, dtype=float)
        v[x >= position] = height
        return v

    if ptype == "double_well":
        a = float(spec.get("a", 1.0))
        b = float(spec.get("b", 4.0))
        # V(x)=a*x^4 - b*x^2; minima near +/-sqrt(b/(2a)) when b>0
        return a * x**4 - b * x**2

    if ptype == "anharmonic":
        omega = float(spec.get("omega", 1.0))
        lam = float(spec.get("lambda", 0.1))
        return 0.5 * omega * omega * x * x + lam * x**4

    if ptype == "custom":
        expr_str = str(spec.get("expression", "0"))
        expr = parse_expression(expr_str, ("x",))
        import sympy as sp
        f = sp.lambdify(sp.Symbol("x", real=True), expr, modules=["numpy"])
        v = np.asarray(f(x), dtype=float)
        if v.shape != x.shape:
            v = np.broadcast_to(v, x.shape).astype(float)
        return v

    raise ValueError(f"Unsupported potential type: {ptype}")


def potential_metadata(spec: dict) -> dict:
    ptype = (spec or {}).get("type", "harmonic")
    notes = {
        "harmonic": "V(x)=1/2*m*omega^2*x^2",
        "infinite_well": "Finite numerical approximation with large v_outside inside domain",
        "finite_well": "Rectangular finite well: V=depth outside, 0 inside",
        "barrier": "Rectangular barrier: V=height inside, 0 outside",
        "step": "Heaviside-like potential step",
        "double_well": "Quartic double well V=a*x^4-b*x^2",
        "anharmonic": "Quartic anharmonic oscillator V=1/2*omega^2*x^2+lambda*x^4",
        "custom": "User-defined safe symbolic expression in x",
    }
    return {"type": ptype, "definition": notes.get(ptype, "custom"), "parameters": spec}
