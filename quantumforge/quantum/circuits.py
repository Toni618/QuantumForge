"""State-vector quantum circuit simulator (little-endian qubit indexing)."""
from __future__ import annotations

import math

import numpy as np

I = np.eye(2, dtype=complex)
H = np.array([[1, 1], [1, -1]], complex) / np.sqrt(2)
X = np.array([[0, 1], [1, 0]], complex)
Y = np.array([[0, -1j], [1j, 0]], complex)
Z = np.diag([1, -1]).astype(complex)
S = np.diag([1, 1j]).astype(complex)
T = np.diag([1, np.exp(1j * np.pi / 4)]).astype(complex)


def Rx(theta: float) -> np.ndarray:
    c, s = math.cos(theta / 2), math.sin(theta / 2)
    return np.array([[c, -1j * s], [-1j * s, c]], complex)


def Ry(theta: float) -> np.ndarray:
    c, s = math.cos(theta / 2), math.sin(theta / 2)
    return np.array([[c, -s], [s, c]], complex)


def Rz(theta: float) -> np.ndarray:
    return np.diag([np.exp(-1j * theta / 2), np.exp(1j * theta / 2)]).astype(complex)


GATES_1Q = {"H": H, "X": X, "Y": Y, "Z": Z, "S": S, "T": T, "I": I}


def memory_estimate_bytes(n_qubits: int) -> int:
    # complex128 amplitudes
    return int((2**n_qubits) * 16)


def _apply_single(state, gate, target, n):
    if target < 0 or target >= n:
        raise ValueError("Target qubit out of range")
    tensor = state.reshape((2,) * n)
    axis = n - 1 - target
    moved = np.moveaxis(tensor, axis, 0)
    updated = np.tensordot(gate, moved, axes=(1, 0))
    return np.moveaxis(updated, 0, axis).reshape(-1)


def _apply_controlled(state, gate, control, target, n):
    if control == target or min(control, target) < 0 or max(control, target) >= n:
        raise ValueError("Invalid control/target")
    new = state.copy()
    dim = 2**n
    for idx in range(dim):
        if ((idx >> control) & 1) and not ((idx >> target) & 1):
            i1 = idx
            i0 = idx ^ (1 << target)
            v0, v1 = state[i0], state[i1]
            # apply gate on target subspace
            nv0 = gate[0, 0] * v0 + gate[0, 1] * v1
            nv1 = gate[1, 0] * v0 + gate[1, 1] * v1
            new[i0], new[i1] = nv0, nv1
    return new


def _apply_swap(state, q1, q2, n):
    if q1 == q2 or min(q1, q2) < 0 or max(q1, q2) >= n:
        raise ValueError("Invalid SWAP targets")
    dim = 2**n
    new = state.copy()
    for idx in range(dim):
        b1 = (idx >> q1) & 1
        b2 = (idx >> q2) & 1
        if b1 != b2:
            j = idx ^ (1 << q1) ^ (1 << q2)
            if idx < j:
                new[idx], new[j] = state[j], state[idx]
    return new


def simulate(n_qubits, operations, shots: int | None = None, seed: int | None = None):
    if n_qubits < 1 or n_qubits > 20:
        raise ValueError("State-vector simulator supports 1..20 qubits (memory grows as 2^n)")
    mem = memory_estimate_bytes(n_qubits)
    if mem > 256 * 1024 * 1024:
        raise ValueError("Refusing allocation above 256 MiB for state vector; reduce qubit count")
    state = np.zeros(2**n_qubits, complex)
    state[0] = 1.0
    for op in operations:
        name = str(op["gate"]).upper()
        target = int(op.get("target", 0))
        if name in GATES_1Q:
            state = _apply_single(state, GATES_1Q[name], target, n_qubits)
        elif name == "RX":
            state = _apply_single(state, Rx(float(op.get("theta", 0.0))), target, n_qubits)
        elif name == "RY":
            state = _apply_single(state, Ry(float(op.get("theta", 0.0))), target, n_qubits)
        elif name == "RZ":
            state = _apply_single(state, Rz(float(op.get("theta", 0.0))), target, n_qubits)
        elif name in {"CNOT", "CX"}:
            state = _apply_controlled(state, X, int(op["control"]), target, n_qubits)
        elif name == "CZ":
            # controlled-Z via diagonal phase on |11>
            c, t = int(op["control"]), target
            if c == t or min(c, t) < 0 or max(c, t) >= n_qubits:
                raise ValueError("Invalid CZ control/target")
            for idx in range(len(state)):
                if ((idx >> c) & 1) and ((idx >> t) & 1):
                    state[idx] *= -1
        elif name == "SWAP":
            state = _apply_swap(state, int(op["target"]), int(op.get("target2", op.get("control"))), n_qubits)
        elif name in {"CY", "CH", "CS"}:
            base = {"CY": Y, "CH": H, "CS": S}[name]
            state = _apply_controlled(state, base, int(op["control"]), target, n_qubits)
        else:
            raise ValueError(f"Unsupported gate: {name}")

    probs = np.abs(state) ** 2
    result = {
        "state_real": state.real.tolist(),
        "state_imag": state.imag.tolist(),
        "probabilities": probs.tolist(),
        "norm": float(np.vdot(state, state).real),
        "n_qubits": n_qubits,
        "memory_estimate_bytes": mem,
        "basis_order": "computational basis; qubit 0 is least-significant bit (little-endian label)",
        "supported_gates": sorted(list(GATES_1Q.keys()) + ["RX", "RY", "RZ", "CNOT/CX", "CZ", "SWAP", "CY", "CH", "CS"]),
        "limitations": ["State-vector simulation scales as O(2^n) in memory/time.", "No mid-circuit measurement/collapse in this API; measurement sampling is from final state."],
    }
    if shots is not None:
        shots = int(shots)
        if shots < 1 or shots > 200000:
            raise ValueError("shots must be in [1,200000]")
        rng = np.random.default_rng(seed)
        outcomes = rng.choice(len(probs), size=shots, p=probs / probs.sum())
        counts = {format(i, f"0{n_qubits}b")[::-1]: 0 for i in range(len(probs))}
        # report bitstring with qubit 0 leftmost for readability
        raw_counts = np.bincount(outcomes, minlength=len(probs))
        counts_labeled = {format(i, f"0{n_qubits}b"): int(raw_counts[i]) for i in range(len(probs))}
        result["measurement_samples"] = {"shots": shots, "seed": seed, "counts_by_basis_index": counts_labeled}
    return result
