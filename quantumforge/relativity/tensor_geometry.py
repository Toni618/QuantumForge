"""Symbolic metric geometry with convention R^rho_{ sigma mu nu}.
Metric signature and coordinates are supplied by the caller.
"""
from __future__ import annotations
import sympy as sp

def metric_geometry(metric, coordinates):
    x = tuple(sp.sympify(v) for v in coordinates)
    g = sp.Matrix(metric)
    n = len(x)
    if g.shape != (n,n): raise ValueError("Metric shape must match coordinate count")
    if any(not sp.sympify(g[i,j]).equals(g[j,i]) for i in range(n) for j in range(n)):
        raise ValueError("Metric must be symmetric")
    det = sp.simplify(g.det())
    if det == 0: raise ValueError("Metric is singular")
    gi = sp.simplify(g.inv())
    gamma = [[ [sp.S.Zero for _ in range(n)] for _ in range(n)] for _ in range(n)]
    for a in range(n):
      for b in range(n):
       for c in range(n):
        gamma[a][b][c] = sp.simplify(sum(gi[a,d]*(sp.diff(g[d,c],x[b])+sp.diff(g[d,b],x[c])-sp.diff(g[b,c],x[d])) for d in range(n))/2)
    # R^rho_{ sigma mu nu} = d_mu Gamma^rho_{nu sigma} - d_nu Gamma^rho_{mu sigma}
    # + Gamma^rho_{mu lambda}Gamma^lambda_{nu sigma} - Gamma^rho_{nu lambda}Gamma^lambda_{mu sigma}
    ricci = sp.MutableDenseMatrix.zeros(n,n)
    for s in range(n):
      for nu in range(n):
       total = 0
       for rho in range(n):
        total += sp.diff(gamma[rho][nu][s],x[rho])-sp.diff(gamma[rho][rho][s],x[nu])
        for lam in range(n):
         total += gamma[rho][rho][lam]*gamma[lam][nu][s]-gamma[rho][nu][lam]*gamma[lam][rho][s]
       ricci[s,nu] = sp.simplify(total)
    scalar = sp.simplify(sum(gi[i,j]*ricci[i,j] for i in range(n) for j in range(n)))
    einstein = sp.simplify(ricci - g*scalar/2)
    def serial_matrix(m): return [[str(sp.simplify(m[i,j])) for j in range(m.cols)] for i in range(m.rows)]
    return {"coordinates":[str(v) for v in x], "metric":serial_matrix(g),
            "inverse_metric":serial_matrix(gi), "determinant":str(sp.factor(det)),
            "christoffel_symbols": [[[str(gamma[a][b][c]) for c in range(n)] for b in range(n)] for a in range(n)],
            "ricci_tensor":serial_matrix(ricci), "ricci_scalar":str(scalar),
            "einstein_tensor":serial_matrix(einstein),
            "convention":"R^rho_{ sigma mu nu}=partial_mu Gamma^rho_{nu sigma}-partial_nu Gamma^rho_{mu sigma}+Gamma^rho_{mu lambda}Gamma^lambda_{nu sigma}-Gamma^rho_{nu lambda}Gamma^lambda_{mu sigma}"}

def schwarzschild_metric():
    t,r,theta,phi = sp.symbols('t r theta phi', real=True, positive=True)
    M = sp.symbols('M', positive=True, real=True)
    f = 1-2*M/r
    g = sp.diag(-f, 1/f, r**2, r**2*sp.sin(theta)**2)
    return metric_geometry(g, (t,r,theta,phi))
