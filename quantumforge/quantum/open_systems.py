"""Lindblad master-equation integration for finite-dimensional systems."""
import numpy as np
from scipy.integrate import solve_ivp

def lindblad_evolve(rho0, hamiltonian, collapse_operators, t_span, samples=201, rtol=1e-9, atol=1e-11):
    rho0=np.asarray(rho0,dtype=complex); H=np.asarray(hamiltonian,dtype=complex)
    if rho0.ndim!=2 or rho0.shape[0]!=rho0.shape[1] or H.shape!=rho0.shape: raise ValueError("rho0 and Hamiltonian must be matching square matrices")
    d=rho0.shape[0]
    if not np.allclose(H,H.conj().T,atol=1e-10): raise ValueError("Hamiltonian must be Hermitian")
    if not np.allclose(rho0,rho0.conj().T,atol=1e-10) or not np.isclose(np.trace(rho0),1,atol=1e-9): raise ValueError("Initial density matrix must be Hermitian with unit trace")
    eig=np.linalg.eigvalsh(rho0)
    if eig.min() < -1e-9: raise ValueError("Initial density matrix must be positive semidefinite")
    cs=[np.asarray(c,dtype=complex) for c in collapse_operators]
    if any(c.shape!=(d,d) for c in cs): raise ValueError("Collapse operator shape mismatch")
    def rhs(t,y):
        rho=y.reshape(d,d); dr=-1j*(H@rho-rho@H)
        for c in cs:
            cd_c=c.conj().T@c
            dr += c@rho@c.conj().T - 0.5*(cd_c@rho+rho@cd_c)
        return dr.reshape(-1)
    ts=np.linspace(t_span[0],t_span[1],samples)
    sol=solve_ivp(rhs,t_span,rho0.reshape(-1),t_eval=ts,method="DOP853",rtol=rtol,atol=atol)
    if not sol.success: raise RuntimeError(sol.message)
    rhos=sol.y.T.reshape(-1,d,d); traces=[]; min_eigs=[]; herm=[]
    for r in rhos:
        traces.append(float(np.trace(r).real)); min_eigs.append(float(np.linalg.eigvalsh((r+r.conj().T)/2).min()))
        herm.append(float(np.linalg.norm(r-r.conj().T)))
    return {"times":ts.tolist(),"density_matrices_real":rhos.real.tolist(),"density_matrices_imag":rhos.imag.tolist(),
            "trace":traces,"minimum_eigenvalue":min_eigs,"hermiticity_residual":herm,
            "method":"DOP853 integration of Lindblad-GKSL equation","rtol":rtol,"atol":atol}
