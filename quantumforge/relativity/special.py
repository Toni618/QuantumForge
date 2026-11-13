"""Special-relativistic transformations in SI units, metric signature (-,+,+,+)."""
import numpy as np
C=299_792_458.0

def lorentz_boost(beta):
    b=np.asarray(beta,dtype=float)
    if b.shape!=(3,) or not np.all(np.isfinite(b)): raise ValueError("beta must be a finite 3-vector")
    b2=float(b@b)
    if b2>=1: raise ValueError("Speed must be subluminal: |v| < c")
    if b2==0: return np.eye(4)
    gamma=1/np.sqrt(1-b2); mat=np.eye(4); mat[0,0]=gamma; mat[0,1:]=-gamma*b; mat[1:,0]=-gamma*b
    mat[1:,1:]+=((gamma-1)/b2)*np.outer(b,b)
    return mat

def minkowski_interval(event):
    x=np.asarray(event,dtype=float)
    if x.shape!=(4,): raise ValueError("event must be (ct, x, y, z)")
    return float(-x[0]**2+x[1:]@x[1:])
