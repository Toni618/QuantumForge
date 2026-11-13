"""Equatorial timelike/null Schwarzschild geodesics in G=c=M=1 units."""
from __future__ import annotations
import numpy as np
from scipy.integrate import solve_ivp

def schwarzschild_geodesic(r0: float, energy: float, angular_momentum: float,
                           radial_velocity: float, affine_end: float = 50.0,
                           samples: int = 1000, kind: str = "timelike"):
    vals = [r0, energy, angular_momentum, radial_velocity, affine_end]
    if not all(np.isfinite(v) for v in vals): raise ValueError("All parameters must be finite")
    if r0 <= 2.0 or energy <= 0 or affine_end <= 0: raise ValueError("Require r0>2M, energy>0, affine_end>0")
    if samples < 20 or samples > 20000: raise ValueError("samples must be in [20,20000]")
    if kind not in {"timelike","null"}: raise ValueError("kind must be timelike or null")
    f = 1-2/r0
    # Normalize initial four-velocity from conserved energy E=f u^t and L=r^2 u^phi.
    ut = energy/f
    uphi = angular_momentum/(r0*r0)
    kappa = 1.0 if kind == "timelike" else 0.0
    radicand = energy*energy - f*(kappa + angular_momentum**2/r0**2)
    if radicand < -1e-12: raise ValueError("Initial constants do not permit a real radial velocity at r0")
    ur = float(np.sign(radial_velocity)*np.sqrt(max(0.0,radicand)))
    y0 = np.array([0.0,r0,0.0,ut,ur,uphi])
    def rhs(lam,y):
        t,r,phi,ut_,ur_,uphi_ = y
        if r <= 2.0+1e-8: raise RuntimeError("Geodesic reached the Schwarzschild coordinate horizon; chart terminates here")
        ff=1-2/r
        g_ttr=1/(r*(r-2))
        g_rtt=ff/(r*r)
        g_rrr=-1/(r*(r-2))
        g_rpp=-(r-2)
        g_prp=1/r
        return [ut_,ur_,uphi_, -2*g_ttr*ut_*ur_, -g_rtt*ut_**2-g_rrr*ur_**2-g_rpp*uphi_**2, -2*g_prp*ur_*uphi_]
    def horizon(lam,y): return y[1]-2.0-1e-7
    horizon.terminal=True; horizon.direction=-1
    sol=solve_ivp(rhs,(0,affine_end),y0,method="DOP853",rtol=1e-10,atol=1e-12,
                  dense_output=False,events=horizon,max_step=affine_end/100)
    if not sol.success: raise RuntimeError(sol.message)
    states=sol.y.T
    r=states[:,1]; ff=1-2/r
    norm=-ff*states[:,3]**2 + states[:,4]**2/ff + r*r*states[:,5]**2
    target=-kappa
    return {"coordinates":{"affine_parameter":sol.t.tolist(),"t":states[:,0].tolist(),"r":r.tolist(),"phi":states[:,2].tolist()},
            "four_velocity_norm":norm.tolist(),"normalization_target":target,
            "max_normalization_error":float(np.max(np.abs(norm-target))),
            "model":"Equatorial Schwarzschild geodesic", "kind":kind,
            "units":"geometrized units G=c=M=1; r in units of GM/c^2",
            "method":"DOP853 adaptive integration of second-order geodesic equations",
            "rtol":1e-10,"atol":1e-12,"success":bool(sol.success),
            "termination":"horizon chart boundary reached" if sol.t_events[0].size else "requested affine interval completed"}
