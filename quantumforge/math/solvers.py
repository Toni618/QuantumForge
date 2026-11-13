"""Numerical mathematics routines with explicit solver metadata."""
from __future__ import annotations
import numpy as np
from scipy.integrate import solve_ivp, quad
from scipy.optimize import root_scalar
from scipy.linalg import solve
from quantumforge.core.expressions import parse_expression
import sympy as sp

def find_root(expression: str, variable: str, bracket: tuple[float,float], xtol: float=1e-10):
    if not bracket[0] < bracket[1] or xtol <= 0: raise ValueError("Invalid bracket or tolerance")
    expr = parse_expression(expression, (variable,))
    symbol = sp.Symbol(variable, real=True)
    f = sp.lambdify(symbol, expr, modules="numpy")
    result = root_scalar(f, bracket=bracket, method="brentq", xtol=xtol)
    if not result.converged: raise RuntimeError(f"Root solver failed: {result.flag}")
    return {"root": float(result.root), "iterations": result.iterations, "function_calls": result.function_calls,
            "converged": bool(result.converged), "method": "Brent-Dekker", "xtol": xtol}

def integrate_ode(rhs, t_span, y0, method="DOP853", rtol=1e-9, atol=1e-11, t_eval=None):
    if method not in {"RK45","DOP853","Radau","BDF","LSODA"}: raise ValueError("Unsupported integration method")
    if rtol <= 0 or atol <= 0: raise ValueError("Tolerances must be positive")
    result = solve_ivp(rhs, t_span, np.asarray(y0,dtype=float), method=method, rtol=rtol, atol=atol, t_eval=t_eval)
    if not result.success: raise RuntimeError(result.message)
    return {"t": result.t.tolist(), "y": result.y.tolist(), "method": method,
            "nfev": result.nfev, "njev": result.njev, "nlu": result.nlu,
            "rtol": rtol, "atol": atol, "message": result.message}

def integrate_function(expression: str, variable: str, lower: float, upper: float, epsabs=1e-10, epsrel=1e-10):
    expr = parse_expression(expression, (variable,))
    symbol = sp.Symbol(variable, real=True)
    f = sp.lambdify(symbol, expr, modules="numpy")
    value, error = quad(f, lower, upper, epsabs=epsabs, epsrel=epsrel)
    return {"value": value, "estimated_absolute_error": error, "method": "QUADPACK adaptive Gauss-Kronrod",
            "epsabs": epsabs, "epsrel": epsrel}
