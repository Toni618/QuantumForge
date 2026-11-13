import math
import numpy as np
import pytest

from quantumforge.quantum.schrodinger import solve_1d, stationary_convergence, evolve_1d_cn
from quantumforge.quantum.tunneling import rectangular_barrier, sweep_energy, sweep_width, sweep_height
from quantumforge.quantum.circuits import simulate
from quantumforge.quantum.operators import (
    partial_trace, von_neumann_entropy, entanglement_entropy, fidelity, trace_distance,
    bloch_vector, kraus_bit_flip, kraus_phase_flip, kraus_depolarizing,
    kraus_amplitude_damping, kraus_phase_damping, channel_diagnostics,
    bell_state_density, density_matrix_diagnostics
)


def test_stationary_harmonic_with_expectations_and_convergence():
    r = solve_1d(None, potential_spec={"type": "harmonic", "omega": 1.0}, points=1201, states=3)
    assert r["energies"] == pytest.approx([0.5, 1.5, 2.5], abs=2e-3)
    assert r["expectation_values"][0]["normalization"] == pytest.approx(1.0, abs=1e-9)
    conv = stationary_convergence(None, grids=[401, 801, 1201], states=1, potential_spec={"type": "harmonic", "omega": 1.0})
    e = [row["energies"][0] for row in conv["results"]]
    assert abs(e[-1] - 0.5) < abs(e[0] - 0.5)


def test_stationary_various_potentials_run():
    specs = [
        {"type": "finite_well", "depth": 20.0, "width": 2.0},
        {"type": "barrier", "height": 5.0, "width": 1.0},
        {"type": "double_well", "a": 0.5, "b": 3.0},
        {"type": "anharmonic", "omega": 1.0, "lambda": 0.05},
    ]
    for spec in specs:
        r = solve_1d(None, potential_spec=spec, x_min=-6, x_max=6, points=801, states=2)
        assert len(r["energies"]) == 2
        assert all(np.isfinite(r["energies"]))


def test_time_dependent_cn_norm_stability():
    r = evolve_1d_cn({"type": "harmonic", "omega": 1.0}, x_min=-8, x_max=8, points=401, dt=0.02, steps=120, sample_every=20)
    assert r["norm_drift_max"] < 1e-6
    assert len(r["samples"]) >= 2


def test_tunneling_conservation_and_analytical():
    t = rectangular_barrier(E=0.5, V0=1.0, L=1.0)
    assert t["conservation_error"] < 1e-12
    assert t["analytical_reference"] is not None
    assert abs(t["transmission"] - t["analytical_reference"]["T"]) < 1e-12
    sweep = sweep_energy(V0=1.0, L=1.0, energies=np.linspace(0.1, 2.0, 20))
    assert sweep["conservation_max_error"] < 1e-10
    sw = sweep_width(E=0.8, V0=1.2, widths=[0.2, 0.5, 1.0])
    sh = sweep_height(E=0.8, heights=[0.5, 1.0, 1.5], L=1.0)
    assert sw["conservation_max_error"] < 1e-10 and sh["conservation_max_error"] < 1e-10


def test_circuit_expanded_gates_and_sampling():
    r = simulate(1, [{"gate": "H", "target": 0}, {"gate": "RZ", "target": 0, "theta": math.pi / 2}], shots=2000, seed=7)
    assert abs(sum(r["probabilities"]) - 1.0) < 1e-12
    assert r["measurement_samples"]["shots"] == 2000
    bell = simulate(2, [{"gate": "H", "target": 0}, {"gate": "CNOT", "control": 0, "target": 1}])
    assert bell["probabilities"] == pytest.approx([0.5, 0, 0, 0.5])


def test_quantum_information_quantities():
    phi = np.array([1, 0, 0, 1], complex) / math.sqrt(2)
    s = entanglement_entropy(phi, [2, 2], keep=[0], base=2)
    assert abs(s - 1.0) < 1e-12
    rho_a = partial_trace(np.outer(phi, np.conj(phi)), [2, 2], keep=[0])
    assert np.allclose(rho_a, 0.5 * np.eye(2))
    assert abs(von_neumann_entropy(rho_a, base=2) - 1.0) < 1e-12
    rho = bell_state_density("phi_plus")
    assert abs(fidelity(rho, rho) - 1.0) < 1e-12
    assert abs(trace_distance(rho, rho)) < 1e-12
    b = bloch_vector(0.5 * np.eye(2))
    assert abs(b["norm"]) < 1e-12


def test_quantum_channels_cptp_like_checks():
    rho = np.array([[0.6, 0.2], [0.2, 0.4]], complex)
    channels = [kraus_bit_flip(0.1), kraus_phase_flip(0.2), kraus_depolarizing(0.3), kraus_amplitude_damping(0.25), kraus_phase_damping(0.4)]
    for k in channels:
        d = channel_diagnostics(rho, k)
        assert d["completeness_residual"] < 1e-12
        assert abs(d["output"]["trace_real"] - 1.0) < 1e-10
        assert d["output"]["minimum_eigenvalue"] > -1e-10
