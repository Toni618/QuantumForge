"""Finite-dimensional quantum operators, states, and information-theoretic quantities."""
from __future__ import annotations

import math

import numpy as np

I2 = np.eye(2, dtype=complex)
SIGMA_X = np.array([[0, 1], [1, 0]], dtype=complex)
SIGMA_Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
SIGMA_Z = np.array([[1, 0], [0, -1]], dtype=complex)
SPIN_HALF = {"Sx": 0.5 * SIGMA_X, "Sy": 0.5 * SIGMA_Y, "Sz": 0.5 * SIGMA_Z}


def density_matrix_diagnostics(rho, atol=1e-10):
    r = np.asarray(rho, dtype=complex)
    if r.ndim != 2 or r.shape[0] != r.shape[1] or r.shape[0] == 0:
        raise ValueError("Density matrix must be a non-empty square matrix")
    herm = float(np.linalg.norm(r - r.conj().T))
    trace = complex(np.trace(r))
    eig = np.linalg.eigvalsh((r + r.conj().T) / 2)
    minimum = float(eig.min())
    purity = float(np.real(np.trace(r @ r)))
    valid = herm <= atol and abs(trace - 1) <= atol and minimum >= -atol
    return {
        "valid_density_matrix": bool(valid),
        "trace_real": float(trace.real),
        "trace_imag": float(trace.imag),
        "hermiticity_residual": herm,
        "minimum_eigenvalue": minimum,
        "eigenvalues": eig.real.tolist(),
        "purity": purity,
    }


def bell_state_density(label: str = "phi_plus"):
    states = {
        "phi_plus": np.array([1, 0, 0, 1], complex) / np.sqrt(2),
        "phi_minus": np.array([1, 0, 0, -1], complex) / np.sqrt(2),
        "psi_plus": np.array([0, 1, 1, 0], complex) / np.sqrt(2),
        "psi_minus": np.array([0, 1, -1, 0], complex) / np.sqrt(2),
    }
    if label not in states:
        raise ValueError("Unknown Bell state label")
    psi = states[label]
    return np.outer(psi, psi.conj())


def bloch_vector(rho):
    r = np.asarray(rho, dtype=complex)
    if r.shape != (2, 2):
        raise ValueError("Bloch vector defined for single-qubit (2x2) density matrices")
    rx = float(np.real(np.trace(r @ SIGMA_X)))
    ry = float(np.real(np.trace(r @ SIGMA_Y)))
    rz = float(np.real(np.trace(r @ SIGMA_Z)))
    return {"x": rx, "y": ry, "z": rz, "norm": float(math.sqrt(rx * rx + ry * ry + rz * rz))}


def partial_trace(rho: np.ndarray, dims: list[int], keep: list[int]) -> np.ndarray:
    """Partial trace over subsystems not in `keep`. dims lists subsystem dimensions in order."""
    rho = np.asarray(rho, dtype=complex)
    dims = [int(d) for d in dims]
    n = len(dims)
    keep = sorted(int(k) for k in keep)
    if rho.shape != (int(np.prod(dims)), int(np.prod(dims))):
        raise ValueError("rho shape must match product of dims")
    if any(k < 0 or k >= n for k in keep):
        raise ValueError("keep index out of range")
    trace_out = [i for i in range(n) if i not in keep]
    # reshape to tensor with indices (i0..i_{n-1}, j0..j_{n-1})
    tensor = rho.reshape(dims + dims)
    # move kept to front, traced paired at end
    current_dims = list(range(2 * n))
    perm = keep + [k + n for k in keep] + trace_out + [k + n for k in trace_out]
    tensor = np.transpose(tensor, axes=perm)
    d_keep = int(np.prod([dims[k] for k in keep])) if keep else 1
    d_tr = int(np.prod([dims[k] for k in trace_out])) if trace_out else 1
    tensor = tensor.reshape(d_keep, d_keep, d_tr, d_tr)
    reduced = np.einsum('abcc->ab', tensor)
    return reduced


def von_neumann_entropy(rho: np.ndarray, base: float = 2.0, atol: float = 1e-12) -> float:
    r = np.asarray(rho, dtype=complex)
    evals = np.linalg.eigvalsh((r + r.conj().T) / 2)
    evals = np.clip(evals.real, 0.0, 1.0)
    nz = evals[evals > atol]
    if nz.size == 0:
        return 0.0
    log = np.log(nz) / np.log(base)
    return float(-np.sum(nz * log))


def entanglement_entropy(state_or_rho: np.ndarray, dims: list[int], keep: list[int], base: float = 2.0) -> float:
    """Entropy of reduced subsystem for a pure statevector or density matrix."""
    arr = np.asarray(state_or_rho)
    dim_total = int(np.prod(dims))
    if arr.ndim == 1:
        if arr.size != dim_total:
            raise ValueError("State vector size mismatch")
        rho = np.outer(arr, np.conj(arr))
    else:
        rho = np.asarray(arr, dtype=complex)
    reduced = partial_trace(rho, dims, keep)
    return von_neumann_entropy(reduced, base=base)


def fidelity(rho: np.ndarray, sigma: np.ndarray) -> float:
    """Uhlmann fidelity F(rho,sigma) in [0,1]."""
    rho = np.asarray(rho, dtype=complex)
    sigma = np.asarray(sigma, dtype=complex)
    if rho.shape != sigma.shape:
        raise ValueError("Shape mismatch")
    # sqrt(rho)
    evals, evecs = np.linalg.eigh((rho + rho.conj().T) / 2)
    evals = np.clip(evals, 0.0, None)
    sqrt_rho = (evecs * np.sqrt(evals)) @ evecs.conj().T
    inner = sqrt_rho @ sigma @ sqrt_rho
    evals2 = np.linalg.eigvalsh((inner + inner.conj().T) / 2)
    evals2 = np.clip(evals2, 0.0, None)
    return float(np.sum(np.sqrt(evals2)) ** 2)


def trace_distance(rho: np.ndarray, sigma: np.ndarray) -> float:
    rho = np.asarray(rho, dtype=complex)
    sigma = np.asarray(sigma, dtype=complex)
    if rho.shape != sigma.shape:
        raise ValueError("Shape mismatch")
    delta = rho - sigma
    evals = np.linalg.eigvalsh((delta.conj().T @ delta))
    # 1/2 * Tr|delta| = 1/2 sum singular values
    sing = np.sqrt(np.clip(evals.real, 0.0, None))
    return float(0.5 * np.sum(sing))


# ---- Quantum channels (Kraus) ----

def apply_channel(rho: np.ndarray, kraus_ops: list[np.ndarray]) -> np.ndarray:
    rho = np.asarray(rho, dtype=complex)
    out = np.zeros_like(rho, dtype=complex)
    for k in kraus_ops:
        k = np.asarray(k, dtype=complex)
        out += k @ rho @ k.conj().T
    return out


def kraus_bit_flip(p: float):
    if not 0 <= p <= 1:
        raise ValueError("p must be in [0,1]")
    return [math.sqrt(1 - p) * I2, math.sqrt(p) * SIGMA_X]


def kraus_phase_flip(p: float):
    if not 0 <= p <= 1:
        raise ValueError("p must be in [0,1]")
    return [math.sqrt(1 - p) * I2, math.sqrt(p) * SIGMA_Z]


def kraus_depolarizing(p: float):
    if not 0 <= p <= 1:
        raise ValueError("p must be in [0,1]")
    # rho -> (1-p)rho + p/3 (XrhoX + YrhoY + ZrhoZ)
    return [math.sqrt(1 - p) * I2, math.sqrt(p / 3) * SIGMA_X, math.sqrt(p / 3) * SIGMA_Y, math.sqrt(p / 3) * SIGMA_Z]


def kraus_amplitude_damping(gamma: float):
    if not 0 <= gamma <= 1:
        raise ValueError("gamma must be in [0,1]")
    K0 = np.array([[1, 0], [0, math.sqrt(1 - gamma)]], complex)
    K1 = np.array([[0, math.sqrt(gamma)], [0, 0]], complex)
    return [K0, K1]


def kraus_phase_damping(lmbda: float):
    if not 0 <= lmbda <= 1:
        raise ValueError("lambda must be in [0,1]")
    K0 = np.array([[1, 0], [0, math.sqrt(1 - lmbda)]], complex)
    K1 = np.array([[0, 0], [0, math.sqrt(lmbda)]], complex)
    return [K0, K1]


def channel_diagnostics(rho: np.ndarray, kraus_ops: list[np.ndarray], atol: float = 1e-10):
    out = apply_channel(rho, kraus_ops)
    # completeness sum K^†K
    dim = rho.shape[0]
    comp = np.zeros((dim, dim), complex)
    for k in kraus_ops:
        k = np.asarray(k, complex)
        comp += k.conj().T @ k
    completeness_residual = float(np.linalg.norm(comp - np.eye(dim)))
    return {
        "input": density_matrix_diagnostics(rho, atol=atol),
        "output": density_matrix_diagnostics(out, atol=atol),
        "completeness_residual": completeness_residual,
        "trace_preserving_within_tolerance": completeness_residual <= 1e-8,
        "output_rho_real": out.real.tolist(),
        "output_rho_imag": out.imag.tolist(),
    }
