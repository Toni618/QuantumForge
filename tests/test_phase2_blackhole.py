from fastapi.testclient import TestClient
from quantumforge.api.app import app
from quantumforge.relativity.black_holes import kerr_parameters, gravitational_redshift_schwarzschild, accretion_disk_model

client = TestClient(app)


def test_kerr_landmarks_limits():
    k = kerr_parameters(0.0)
    assert abs(k['event_horizon_r_plus'] - 2.0) < 1e-12
    assert abs(k['isco_prograde'] - 6.0) < 1e-9  # Schwarzschild limit
    k2 = kerr_parameters(0.5)
    assert k2['isco_prograde'] < 6.0 < k2['isco_retrograde']


def test_redshift_and_accretion_model():
    z = gravitational_redshift_schwarzschild(10.0)
    assert z['redshift_z'] > 0
    d = accretion_disk_model(6.0, 20.0, n_r=20, n_phi=24)
    assert len(d['emissivity']) == 20
    assert 'approximate visualization model' in d['scientific_status']


def test_blackhole_api_endpoints():
    r = client.get('/relativity/kerr', params={'spin_a': 0.3})
    assert r.status_code == 200
    assert r.json()['event_horizon_r_plus'] > 1.0
    r = client.get('/relativity/schwarzschild/redshift', params={'r_over_rs': 5.0})
    assert r.status_code == 200
    r = client.post('/blackhole/accretion-disk', json={'r_inner': 6.0, 'r_outer': 15.0, 'n_r': 10, 'n_phi': 16})
    assert r.status_code == 200
    assert 'emissivity' in r.json()
