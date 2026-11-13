import numpy as np
import sympy as sp
from quantumforge.quantum.operators import SPIN_HALF, density_matrix_diagnostics, bell_state_density
from quantumforge.qft.lattice_scalar import free_scalar_lattice
from quantumforge.relativity.geodesics import schwarzschild_geodesic
from quantumforge.relativity.tensor_geometry import metric_geometry

def test_spin_operators_are_hermitian_and_commute():
    sx,sy,sz=SPIN_HALF.values()
    for a in (sx,sy,sz): assert np.allclose(a,a.conj().T)
    assert np.allclose(sx@sy-sy@sx,1j*sz)

def test_bell_density_matrix_is_physical():
    d=density_matrix_diagnostics(bell_state_density())
    assert d['valid_density_matrix'] and abs(d['purity']-1)<1e-12

def test_free_scalar_lattice_dispersion_and_energy():
    r=free_scalar_lattice(1.0,32,0.2)
    assert len(r['mode_frequencies'])==32
    assert r['vacuum_energy_lattice']>0
    assert len(r['equal_time_field_covariance'])==32
    assert np.all(np.asarray(r['mode_frequencies'])>0)

def test_massless_scalar_zero_mode_is_reported():
    r=free_scalar_lattice(0.0,16,0.5)
    assert r['equal_time_field_covariance'] is None and r['infrared_note']

def test_schwarzschild_circular_orbit_normalization():
    # Circular timelike orbit at r=10M: E=sqrt((r-2)/(r-3)), L=sqrt(r^2/(r-3)).
    r=10.0; E=(r-2)/np.sqrt(r*(r-3)); L=np.sqrt(r*r/(r-3))
    out=schwarzschild_geodesic(r,E,L,0,1.0,50,'timelike')
    assert out['success'] and out['max_normalization_error']<1e-8
    assert np.max(np.abs(np.asarray(out['coordinates']['r'])-r))<1e-7

def test_flat_metric_has_zero_curvature():
    t,x=sp.symbols('t x', real=True)
    out=metric_geometry([[-1,0],[0,1]],(t,x))
    assert out['ricci_scalar']=='0'
    assert all(v=='0' for row in out['ricci_tensor'] for v in row)

def test_unit_two_sphere_has_ricci_scalar_two():
    theta,phi=sp.symbols('theta phi', real=True)
    out=metric_geometry([[1,0],[0,sp.sin(theta)**2]],(theta,phi))
    assert sp.simplify(sp.sympify(out['ricci_scalar'])-2)==0

def test_schwarzschild_photon_sphere_null_geodesic():
    r=3.0
    out=schwarzschild_geodesic(r,1.0,3*np.sqrt(3),0,1.0,50,'null')
    assert out['success'] and out['max_normalization_error']<1e-10
    assert np.max(np.abs(np.asarray(out['coordinates']['r'])-3.0))<1e-8
