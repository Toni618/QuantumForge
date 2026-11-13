from fastapi.testclient import TestClient
from quantumforge.api.app import app

client = TestClient(app)

def test_health_endpoint():
    r=client.get('/health')
    assert r.status_code==200
    assert r.json()['scientific_backend']=='python'

def test_root_api_endpoint():
    r=client.post('/math/root',json={'expression':'x**2-2','variable':'x','bracket':[1,2]})
    assert r.status_code==200
    assert abs(r.json()['root']-2**0.5)<1e-9

def test_schwarzschild_api_endpoint():
    r=client.post('/relativity/schwarzschild',json={'mass_kg':1.98847e30})
    assert r.status_code==200
    assert abs(r.json()['schwarzschild_radius_m']-2953.34)<1

def test_invalid_mass_rejected():
    r=client.post('/relativity/schwarzschild',json={'mass_kg':-1})
    assert r.status_code==422

def test_qft_free_scalar_endpoint():
    r=client.post('/qft/free-scalar-lattice',json={'mass':1.0,'sites':32,'spacing':0.2})
    assert r.status_code==200
    assert len(r.json()['mode_frequencies'])==32
    assert r.json()['vacuum_energy_lattice']>0

def test_schwarzschild_geometry_is_vacuum():
    r=client.get('/relativity/schwarzschild/geometry')
    assert r.status_code==200
    assert r.json()['ricci_scalar']=='0'
    assert all(v=='0' for row in r.json()['ricci_tensor'] for v in row)

def test_geodesic_endpoint_normalization():
    import math
    r0=10.0
    energy=(r0-2)/math.sqrt(r0*(r0-3))
    angular=math.sqrt(r0*r0/(r0-3))
    r=client.post('/relativity/schwarzschild/geodesic',json={'r0':r0,'energy':energy,'angular_momentum':angular,'radial_velocity':0,'affine_end':1,'samples':50,'kind':'timelike'})
    assert r.status_code==200
    assert r.json()['max_normalization_error']<1e-8
