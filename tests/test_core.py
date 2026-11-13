import numpy as np
import pytest
from quantumforge.core.expressions import parse_expression, ExpressionError
from quantumforge.core.units import convert
from quantumforge.math.solvers import find_root, integrate_function
from quantumforge.quantum.schrodinger import solve_1d, harmonic_oscillator
from quantumforge.quantum.circuits import simulate
from quantumforge.quantum.open_systems import lindblad_evolve
from quantumforge.relativity.special import lorentz_boost, minkowski_interval
from quantumforge.relativity.black_holes import schwarzschild_parameters
from quantumforge.storage.experiments import ExperimentStore

def test_safe_parser_and_reject_code():
    assert str(parse_expression("sin(x)**2 + cos(x)**2",("x",))) == "sin(x)**2 + cos(x)**2"
    with pytest.raises(ExpressionError): parse_expression("__import__('os').system('id')",("x",))

def test_units():
    assert convert(1,"km","m")==1000
    with pytest.raises(ValueError): convert(1,"m","s")

def test_root_and_integral():
    assert find_root("x**2-2","x",(1,2))["root"] == pytest.approx(np.sqrt(2),abs=1e-9)
    assert integrate_function("x**2","x",0,1)["value"] == pytest.approx(1/3,abs=1e-10)

def test_harmonic_oscillator_benchmark():
    r=solve_1d(harmonic_oscillator,points=1601,states=4)
    assert r["energies"] == pytest.approx([0.5,1.5,2.5,3.5],abs=3e-4)
    assert r["normalization"] == pytest.approx([1]*4,abs=1e-10)

def test_bell_state_probabilities_and_norm():
    r=simulate(2,[{"gate":"H","target":0},{"gate":"CNOT","control":0,"target":1}])
    assert r["probabilities"] == pytest.approx([0.5,0,0,0.5])
    assert r["norm"] == pytest.approx(1)

def test_lindblad_trace_and_positivity():
    rho=np.array([[0,0],[0,1]],complex); H=np.zeros((2,2),complex); c=np.array([[0,1],[0,0]],complex)
    r=lindblad_evolve(rho,H,[c],(0,2),samples=31)
    assert np.asarray(r["trace"]) == pytest.approx(np.ones(31),abs=1e-8)
    assert min(r["minimum_eigenvalue"]) > -1e-8

def test_lorentz_invariance():
    b=np.array([0.3,0.2,0.1]); L=lorentz_boost(b); eta=np.diag([-1,1,1,1])
    assert np.linalg.norm(L.T@eta@L-eta)<1e-12
    x=np.array([5.,1.,2.,3.]); assert minkowski_interval(x)==pytest.approx(minkowski_interval(L@x))

def test_schwarzschild_landmarks():
    r=schwarzschild_parameters(1.98847e30)
    assert r["schwarzschild_radius_m"]==pytest.approx(2953.34,rel=2e-3)
    assert r["isco_radius_m"]==pytest.approx(3*r["schwarzschild_radius_m"])

def test_experiment_store_hash(tmp_path):
    s=ExperimentStore(tmp_path/"runs.sqlite3"); saved=s.save("demo",{"a":1},{"b":2}); row=s.get(saved["id"])
    assert row["sha256"]==saved["sha256"] and row["model"]=="demo"

def test_harmonic_grid_refinement():
    coarse=solve_1d(harmonic_oscillator,points=401,states=1)["energies"][0]
    fine=solve_1d(harmonic_oscillator,points=801,states=1)["energies"][0]
    finer=solve_1d(harmonic_oscillator,points=1601,states=1)["energies"][0]
    assert abs(finer-0.5) < abs(fine-0.5) < abs(coarse-0.5)
