"""Small SI unit system with dimensional vectors (L, M, T, I, Theta, N, J)."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Unit:
    symbol: str
    scale: float
    dimensions: tuple[int, ...]

UNITS = {
    "1": Unit("1",1.0,(0,0,0,0,0,0,0)),
    "m": Unit("m",1.0,(1,0,0,0,0,0,0)), "km": Unit("km",1e3,(1,0,0,0,0,0,0)),
    "cm": Unit("cm",1e-2,(1,0,0,0,0,0,0)),
    "kg": Unit("kg",1.0,(0,1,0,0,0,0,0)), "g": Unit("g",1e-3,(0,1,0,0,0,0,0)),
    "s": Unit("s",1.0,(0,0,1,0,0,0,0)), "ms": Unit("ms",1e-3,(0,0,1,0,0,0,0)),
    "A": Unit("A",1.0,(0,0,0,1,0,0,0)), "K": Unit("K",1.0,(0,0,0,0,1,0,0)),
    "mol": Unit("mol",1.0,(0,0,0,0,0,1,0)), "cd": Unit("cd",1.0,(0,0,0,0,0,0,1)),
    "Hz": Unit("Hz",1.0,(0,0,-1,0,0,0,0)), "N": Unit("N",1.0,(1,1,-2,0,0,0,0)),
    "J": Unit("J",1.0,(2,1,-2,0,0,0,0)), "W": Unit("W",1.0,(2,1,-3,0,0,0,0)),
    "Pa": Unit("Pa",1.0,(-1,1,-2,0,0,0,0)),
}

def convert(value: float, source: str, target: str) -> float:
    try: a, b = UNITS[source], UNITS[target]
    except KeyError as exc: raise ValueError(f"Unsupported unit: {exc.args[0]}") from exc
    if a.dimensions != b.dimensions: raise ValueError(f"Dimension mismatch: {source} cannot convert to {target}")
    return float(value) * a.scale / b.scale

def require_same_dimensions(*symbols: str) -> tuple[int, ...]:
    if not symbols: return UNITS["1"].dimensions
    try: dims = [UNITS[s].dimensions for s in symbols]
    except KeyError as exc: raise ValueError(f"Unsupported unit: {exc.args[0]}") from exc
    if any(d != dims[0] for d in dims[1:]): raise ValueError("Dimensionally inconsistent quantities")
    return dims[0]
