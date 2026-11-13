import math
import numpy as np
from fastapi.testclient import TestClient
from quantumforge.api.app import app

client = TestClient(app)


def test_schrodinger_custom_potential_and_expectations():
    r = client.post('/quantum/schrodinger/harmonic', json={
        'potential': {'type': 'harmonic', 'omega': 1.0},
        'x_min': -8, 'x_max': 8, 'points': 801, 'states': 2
    })
    assert r.status_code == 200
    d = r.json()
    assert 'expectation_values' in d and 'probability_densities' in d
    assert abs(d['energies'][0] - 0.5) < 5e-3


def test_time_evolution_endpoint_norm():
    r = client.post('/quantum/schrodinger/evolve', json={
        'potential': {'type': 'harmonic', 'omega': 1.0},
        'points': 301, 'dt': 0.02, 'steps': 80, 'sample_every': 20,
        'packet': {'x0': -2.0, 'k0': 1.5, 'sigma': 0.6}
    })
    assert r.status_code == 200
    d = r.json()
    assert d['norm_drift_max'] < 1e-5
    assert len(d['samples']) >= 2


def test_tunneling_endpoints():
    r = client.post('/quantum/tunneling/rectangular', json={'energy': 0.5, 'barrier_height': 1.0, 'barrier_width': 1.0})
    assert r.status_code == 200
    d = r.json()
    assert d['conservation_error'] < 1e-12
    r = client.post('/quantum/tunneling/sweep', json={'sweep': 'energy', 'barrier_height': 1.0, 'barrier_width': 1.0, 'values': [0.2, 0.5, 1.2, 2.0]})
    assert r.status_code == 200
    assert r.json()['conservation_max_error'] < 1e-10


def test_circuit_shots_and_info_metrics_channel():
    r = client.post('/quantum/circuit', json={'n_qubits': 1, 'operations': [{'gate': 'H', 'target': 0}], 'shots': 500, 'seed': 1})
    assert r.status_code == 200
    assert r.json()['measurement_samples']['shots'] == 500

    bell = client.get('/quantum/density/bell').json()
    rho = [[complex(a,b) for a,b in zip(row_r, row_i)] for row_r,row_i in zip(bell['real'], bell['imag'])]
    # send as real/imag
    r = client.post('/quantum/info/metrics', json={'rho_real': bell['real'], 'rho_imag': bell['imag'], 'dims': [2,2], 'keep': [0]})
    assert r.status_code == 200
    d = r.json()
    assert abs(d['entanglement_entropy_bits'] - 1.0) < 1e-10

    r = client.post('/quantum/channel/apply', json={'real': [[1,0],[0,0]], 'imag': [[0,0],[0,0]], 'channel': 'depolarizing', 'p': 0.25})
    assert r.status_code == 200
    out = r.json()
    assert abs(out['output']['trace_real'] - 1.0) < 1e-10
    assert out['completeness_residual'] < 1e-12
