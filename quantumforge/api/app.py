from __future__ import annotations

import math
import os
import threading
from typing import Any

import numpy as np
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from quantumforge import __version__
from quantumforge.application.jobs import CancelledError, JobManager
from quantumforge.math.solvers import find_root, integrate_function
from quantumforge.qft.lattice_scalar import free_scalar_lattice
from quantumforge.quantum.circuits import simulate
from quantumforge.quantum.operators import (
    SPIN_HALF,
    bell_state_density,
    bloch_vector,
    channel_diagnostics,
    density_matrix_diagnostics,
    entanglement_entropy,
    fidelity,
    kraus_amplitude_damping,
    kraus_bit_flip,
    kraus_depolarizing,
    kraus_phase_damping,
    kraus_phase_flip,
    partial_trace,
    trace_distance,
    von_neumann_entropy,
)
from quantumforge.quantum.schrodinger import evolve_1d_cn, harmonic_oscillator, solve_1d, stationary_convergence
from quantumforge.quantum.tunneling import rectangular_barrier, sweep_energy, sweep_height, sweep_width
from quantumforge.relativity.black_holes import accretion_disk_model, gravitational_redshift_schwarzschild, kerr_parameters, schwarzschild_parameters
from quantumforge.relativity.geodesics import schwarzschild_geodesic
from quantumforge.relativity.special import lorentz_boost
from quantumforge.relativity.tensor_geometry import schwarzschild_metric
from quantumforge.storage.db import ExperimentStore, software_info

app = FastAPI(title="QuantumForge Local Scientific API", version=__version__)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["tauri://localhost", "https://tauri.localhost", "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Content-Type"],
)

store = ExperimentStore(os.environ.get("QUANTUMFORGE_DB", "quantumforge.sqlite3"))
jobs = JobManager(store, max_workers=int(os.environ.get("QUANTUMFORGE_MAX_WORKERS", "2")))


class RootRequest(BaseModel):
    expression: str
    variable: str = "x"
    bracket: tuple[float, float]
    xtol: float = Field(1e-10, gt=0)


class SchrodingerRequest(BaseModel):
    x_min: float = -8
    x_max: float = 8
    points: int = 1201
    states: int = 6
    omega: float = 1.0
    potential: dict | None = None
    mass: float = 1.0
    hbar: float = 1.0


class TimeEvolveRequest(BaseModel):
    potential: dict = Field(default_factory=lambda: {"type": "harmonic", "omega": 1.0})
    x_min: float = -10
    x_max: float = 10
    points: int = 401
    dt: float = 0.02
    steps: int = 120
    mass: float = 1.0
    hbar: float = 1.0
    packet: dict | None = None
    sample_every: int = 10


class TunnelingRequest(BaseModel):
    energy: float = Field(gt=0)
    barrier_height: float = Field(ge=0)
    barrier_width: float = Field(gt=0)
    mass: float = 1.0
    hbar: float = 1.0


class TunnelingSweepRequest(BaseModel):
    sweep: str = "energy"
    energy: float = Field(default=0.8, gt=0)
    barrier_height: float = Field(default=1.0, ge=0)
    barrier_width: float = Field(default=1.0, gt=0)
    values: list[float] = Field(default_factory=lambda: [0.1, 0.2, 0.5, 0.8, 1.0, 1.5, 2.0])
    mass: float = 1.0
    hbar: float = 1.0


class CircuitRequest(BaseModel):
    n_qubits: int = Field(ge=1, le=20)
    operations: list[dict]
    shots: int | None = Field(default=None, ge=1, le=200000)
    seed: int | None = None


class BlackHoleRequest(BaseModel):
    mass_kg: float = Field(gt=0)


class QFTRequest(BaseModel):
    mass: float = Field(ge=0)
    sites: int = Field(default=64, ge=4, le=4096)
    spacing: float = Field(default=0.25, gt=0)


class GeodesicRequest(BaseModel):
    r0: float = Field(gt=2)
    energy: float = Field(gt=0)
    angular_momentum: float = 0
    radial_velocity: int = Field(default=-1, ge=-1, le=1)
    affine_end: float = Field(default=50, gt=0, le=10000)
    samples: int = Field(default=1000, ge=20, le=20000)
    kind: str = "timelike"


class DensityRequest(BaseModel):
    real: list[list[float]]
    imag: list[list[float]] | None = None


# -------- Scientific endpoints (preserved) --------
@app.get("/health")
def health():
    return {"status": "ok", "version": __version__, "scientific_backend": "python", "schema_version": store.db.schema_version()}


@app.post("/math/root")
def root(req: RootRequest):
    try:
        return find_root(req.expression, req.variable, req.bracket, req.xtol)
    except Exception as e:
        raise HTTPException(422, str(e))


@app.post("/math/integrate")
def integrate(req: RootRequest):
    try:
        return integrate_function(req.expression, req.variable, *req.bracket, epsabs=req.xtol, epsrel=req.xtol)
    except Exception as e:
        raise HTTPException(422, str(e))


@app.post("/quantum/schrodinger/harmonic")
def schrodinger(req: SchrodingerRequest):
    try:
        if req.potential:
            return solve_1d(None, req.x_min, req.x_max, req.points, req.states, req.mass, req.hbar, potential_spec=req.potential)
        return solve_1d(lambda x: harmonic_oscillator(x, req.omega), req.x_min, req.x_max, req.points, req.states, req.mass, req.hbar)
    except Exception as e:
        raise HTTPException(422, str(e))


@app.post("/quantum/schrodinger/evolve")
def schrodinger_evolve(req: TimeEvolveRequest):
    try:
        return evolve_1d_cn(req.potential, req.x_min, req.x_max, req.points, req.dt, req.steps, req.mass, req.hbar, req.packet, req.sample_every)
    except Exception as e:
        raise HTTPException(422, str(e))


@app.post("/quantum/tunneling/rectangular")
def tunneling_rectangular(req: TunnelingRequest):
    try:
        return rectangular_barrier(req.energy, req.barrier_height, req.barrier_width, req.mass, req.hbar)
    except Exception as e:
        raise HTTPException(422, str(e))


@app.post("/quantum/tunneling/sweep")
def tunneling_sweep(req: TunnelingSweepRequest):
    try:
        if req.sweep == "energy":
            return sweep_energy(req.barrier_height, req.barrier_width, req.values, req.mass, req.hbar)
        if req.sweep == "width":
            return sweep_width(req.energy, req.barrier_height, req.values, req.mass, req.hbar)
        if req.sweep == "height":
            return sweep_height(req.energy, req.values, req.barrier_width, req.mass, req.hbar)
        raise ValueError("sweep must be energy, width, or height")
    except Exception as e:
        raise HTTPException(422, str(e))


@app.post("/quantum/circuit")
def circuit(req: CircuitRequest):
    try:
        return simulate(req.n_qubits, req.operations, shots=req.shots, seed=req.seed)
    except Exception as e:
        raise HTTPException(422, str(e))


@app.post("/quantum/info/partial-trace")
def info_partial_trace(payload: dict):
    try:
        rho = np.asarray(payload.get("rho_real", payload.get("real")), dtype=float).astype(complex)
        if payload.get("rho_imag") or payload.get("imag"):
            rho += 1j * np.asarray(payload.get("rho_imag", payload.get("imag")), dtype=float)
        dims = payload["dims"]
        keep = payload["keep"]
        out = partial_trace(rho, dims, keep)
        return {"real": out.real.tolist(), "imag": out.imag.tolist(), "diagnostics": density_matrix_diagnostics(out)}
    except Exception as e:
        raise HTTPException(422, str(e))


@app.post("/quantum/info/metrics")
def info_metrics(payload: dict):
    try:
        def asrho(keyr, keyi):
            r = np.asarray(payload[keyr], dtype=float).astype(complex)
            if payload.get(keyi):
                r += 1j * np.asarray(payload[keyi], dtype=float)
            return r
        rho = asrho("rho_real", "rho_imag") if "rho_real" in payload else asrho("real", "imag")
        res = {"rho_diagnostics": density_matrix_diagnostics(rho)}
        if rho.shape == (2, 2):
            res["bloch_vector"] = bloch_vector(rho)
        if "sigma_real" in payload or "sigma" in payload:
            sigma = asrho("sigma_real", "sigma_imag") if "sigma_real" in payload else asrho("sigma", "sigma_imag")
            res["fidelity"] = fidelity(rho, sigma)
            res["trace_distance"] = trace_distance(rho, sigma)
        if "dims" in payload and "keep" in payload:
            res["entanglement_entropy_bits"] = entanglement_entropy(rho, payload["dims"], payload["keep"], base=2)
            res["reduced_entropy_bits"] = von_neumann_entropy(partial_trace(rho, payload["dims"], payload["keep"]), base=2)
        else:
            res["von_neumann_entropy_bits"] = von_neumann_entropy(rho, base=2)
        return res
    except Exception as e:
        raise HTTPException(422, str(e))


@app.post("/quantum/channel/apply")
def channel_apply(payload: dict):
    try:
        rho = np.asarray(payload.get("real"), dtype=float).astype(complex)
        if payload.get("imag"):
            rho += 1j * np.asarray(payload.get("imag"), dtype=float)
        name = payload.get("channel", "depolarizing")
        p = float(payload.get("p", payload.get("gamma", payload.get("lambda", 0.1))))
        if name == "bit_flip":
            kraus = kraus_bit_flip(p)
        elif name == "phase_flip":
            kraus = kraus_phase_flip(p)
        elif name == "depolarizing":
            kraus = kraus_depolarizing(p)
        elif name == "amplitude_damping":
            kraus = kraus_amplitude_damping(p)
        elif name == "phase_damping":
            kraus = kraus_phase_damping(p)
        else:
            raise ValueError("Unsupported channel")
        out = channel_diagnostics(rho, kraus)
        out["channel"] = name
        out["parameter"] = p
        return out
    except Exception as e:
        raise HTTPException(422, str(e))


@app.get("/quantum/spin/operators")
def spin_operators():
    return {name: {"real": m.real.tolist(), "imag": m.imag.tolist()} for name, m in SPIN_HALF.items()}


@app.post("/quantum/density/diagnostics")
def density_diagnostics(req: DensityRequest):
    try:
        rho = np.asarray(req.real, dtype=float).astype(complex)
        if req.imag is not None:
            rho += 1j * np.asarray(req.imag, dtype=float)
        return density_matrix_diagnostics(rho)
    except Exception as e:
        raise HTTPException(422, str(e))


@app.get("/quantum/density/bell")
def bell_density():
    rho = bell_state_density()
    return {"real": rho.real.tolist(), "imag": rho.imag.tolist(), "diagnostics": density_matrix_diagnostics(rho)}


@app.post("/qft/free-scalar-lattice")
def qft_free_scalar(req: QFTRequest):
    try:
        return free_scalar_lattice(req.mass, req.sites, req.spacing)
    except Exception as e:
        raise HTTPException(422, str(e))


@app.post("/relativity/lorentz")
def lorentz(beta: list[float]):
    try:
        m = lorentz_boost(beta)
        eta = np.diag([-1, 1, 1, 1])
        residual = float(np.linalg.norm(m.T @ eta @ m - eta))
        return {"matrix": m.tolist(), "metric_invariance_residual": residual, "convention": "metric (-,+,+,+); beta=v/c"}
    except Exception as e:
        raise HTTPException(422, str(e))


@app.post("/relativity/schwarzschild")
def black_hole(req: BlackHoleRequest):
    try:
        return schwarzschild_parameters(req.mass_kg)
    except Exception as e:
        raise HTTPException(422, str(e))


@app.post("/relativity/schwarzschild/geodesic")
def geodesic(req: GeodesicRequest):
    try:
        return schwarzschild_geodesic(req.r0, req.energy, req.angular_momentum, req.radial_velocity, req.affine_end, req.samples, req.kind)
    except Exception as e:
        raise HTTPException(422, str(e))


@app.get("/relativity/schwarzschild/geometry")
def schwarzschild_geometry():
    try:
        return schwarzschild_metric()
    except Exception as e:
        raise HTTPException(422, str(e))


@app.get("/relativity/kerr")
def kerr(spin_a: float = 0.5):
    try:
        return kerr_parameters(spin_a)
    except Exception as e:
        raise HTTPException(422, str(e))


@app.get("/relativity/schwarzschild/redshift")
def schwarzschild_redshift(r_over_rs: float = 10.0):
    try:
        return gravitational_redshift_schwarzschild(r_over_rs)
    except Exception as e:
        raise HTTPException(422, str(e))


@app.post("/blackhole/accretion-disk")
def accretion_disk(payload: dict):
    try:
        return accretion_disk_model(float(payload.get("r_inner", 6.0)), float(payload.get("r_outer", 20.0)), int(payload.get("n_r", 60)), int(payload.get("n_phi", 90)))
    except Exception as e:
        raise HTTPException(422, str(e))


# -------- Legacy experiment endpoints (preserved contract) --------
@app.post("/experiments")
def save_experiment(payload: dict):
    if not all(k in payload for k in ("model", "config", "result")):
        raise HTTPException(422, "Expected model, config, result")
    try:
        return store.save(payload["model"], payload["config"], payload["result"])
    except Exception as e:
        raise HTTPException(422, str(e))


@app.get("/experiments/{experiment_id}")
def get_experiment(experiment_id: str):
    try:
        return store.get(experiment_id)
    except KeyError:
        raise HTTPException(404, "Experiment not found")


# -------- Project & experiment management (Phase 1) --------
class ProjectCreate(BaseModel):
    name: str
    description: str = ""
    metadata: dict = Field(default_factory=dict)


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    archived: bool | None = None
    metadata: dict | None = None


class ExperimentCreate(BaseModel):
    project_id: str | None = None
    name: str
    description: str = ""
    scientific_domain: str = "general"
    model: str = "unknown"
    input_parameters: dict = Field(default_factory=dict)
    input_units: dict = Field(default_factory=dict)
    initial_conditions: dict = Field(default_factory=dict)
    numerical_method: str = "default"
    solver_configuration: dict = Field(default_factory=dict)
    seed: int | None = None
    deterministic: bool = False
    provenance: dict = Field(default_factory=dict)
    auto_run: bool = False
    resource_limits: dict = Field(default_factory=dict)


class ImportPayload(BaseModel):
    payload: dict
    mode: str = "new"


COMPUTATIONS = {}


def _register_computations():
    def c_root(params, progress, cancel):
        progress(0.2, "validating"); 
        if cancel.is_set(): raise CancelledError()
        out = find_root(params["expression"], params.get("variable", "x"), tuple(params["bracket"]), float(params.get("xtol", 1e-10)))
        progress(1.0, "done"); return out

    def c_integrate(params, progress, cancel):
        progress(0.2, "integrating");
        if cancel.is_set(): raise CancelledError()
        out = integrate_function(params["expression"], params.get("variable", "x"), *params["bracket"], epsabs=float(params.get("xtol", 1e-10)), epsrel=float(params.get("xtol", 1e-10)))
        progress(1.0, "done"); return out

    def c_schrodinger(params, progress, cancel):
        progress(0.1, "building Hamiltonian");
        if cancel.is_set(): raise CancelledError()
        potential = params.get("potential")
        if potential:
            out = solve_1d(None, float(params.get("x_min", -8)), float(params.get("x_max", 8)), int(params.get("points", 1201)), int(params.get("states", 6)), float(params.get("mass", 1.0)), float(params.get("hbar", 1.0)), potential_spec=potential)
        else:
            omega = float(params.get("omega", 1.0))
            out = solve_1d(lambda x: harmonic_oscillator(x, omega), float(params.get("x_min", -8)), float(params.get("x_max", 8)), int(params.get("points", 1201)), int(params.get("states", 6)), float(params.get("mass", 1.0)), float(params.get("hbar", 1.0)))
        progress(1.0, "done"); return out

    def c_schrodinger_evolve(params, progress, cancel):
        progress(0.1, "evolving (Crank–Nicolson)");
        if cancel.is_set(): raise CancelledError()
        out = evolve_1d_cn(params.get("potential", {"type": "harmonic", "omega": 1.0}), float(params.get("x_min", -10)), float(params.get("x_max", 10)), int(params.get("points", 401)), float(params.get("dt", 0.02)), int(params.get("steps", 120)), float(params.get("mass", 1.0)), float(params.get("hbar", 1.0)), params.get("packet"), int(params.get("sample_every", 10)))
        progress(1.0, "done"); return out

    def c_tunneling(params, progress, cancel):
        progress(0.2, "computing scattering coefficients");
        if cancel.is_set(): raise CancelledError()
        out = rectangular_barrier(float(params["energy"]), float(params["barrier_height"]), float(params["barrier_width"]), float(params.get("mass", 1.0)), float(params.get("hbar", 1.0)))
        progress(1.0, "done"); return out

    def c_tunneling_sweep(params, progress, cancel):
        progress(0.1, "running sweep");
        if cancel.is_set(): raise CancelledError()
        sweep = params.get("sweep", "energy")
        if sweep == "energy": out = sweep_energy(float(params.get("barrier_height", 1.0)), float(params.get("barrier_width", 1.0)), params.get("values", []), float(params.get("mass", 1.0)), float(params.get("hbar", 1.0)))
        elif sweep == "width": out = sweep_width(float(params.get("energy", 0.8)), float(params.get("barrier_height", 1.0)), params.get("values", []), float(params.get("mass", 1.0)), float(params.get("hbar", 1.0)))
        elif sweep == "height": out = sweep_height(float(params.get("energy", 0.8)), params.get("values", []), float(params.get("barrier_width", 1.0)), float(params.get("mass", 1.0)), float(params.get("hbar", 1.0)))
        else: raise ValueError("Unsupported sweep")
        progress(1.0, "done"); return out

    def c_circuit(params, progress, cancel):
        progress(0.1, "simulating");
        if cancel.is_set(): raise CancelledError()
        out = simulate(int(params["n_qubits"]), params.get("operations", [])); progress(1.0, "done"); return out

    def c_bell(params, progress, cancel):
        progress(0.2, "computing"); rho = bell_state_density(); out = {"real": rho.real.tolist(), "imag": rho.imag.tolist(), "diagnostics": density_matrix_diagnostics(rho)}; progress(1.0, "done"); return out

    def c_qft(params, progress, cancel):
        progress(0.1, "computing modes");
        if cancel.is_set(): raise CancelledError()
        out = free_scalar_lattice(float(params.get("mass", 1.0)), int(params.get("sites", 64)), float(params.get("spacing", 0.25))); progress(1.0, "done"); return out

    def c_schwarzschild(params, progress, cancel):
        progress(0.2, "computing"); out = schwarzschild_parameters(float(params["mass_kg"])); progress(1.0, "done"); return out

    def c_geometry(params, progress, cancel):
        progress(0.1, "computing tensor geometry");
        if cancel.is_set(): raise CancelledError()
        out = schwarzschild_metric(); progress(1.0, "done"); return out

    def c_geodesic(params, progress, cancel):
        progress(0.1, "integrating geodesic");
        if cancel.is_set(): raise CancelledError()
        out = schwarzschild_geodesic(float(params["r0"]), float(params["energy"]), float(params.get("angular_momentum", 0)), int(params.get("radial_velocity", -1)), float(params.get("affine_end", 50)), int(params.get("samples", 1000)), str(params.get("kind", "timelike")))
        progress(1.0, "done"); return out

    COMPUTATIONS.update({
        "math.root": c_root,
        "math.integrate": c_integrate,
        "quantum.schrodinger.harmonic": c_schrodinger,
        "quantum.schrodinger.evolve": c_schrodinger_evolve,
        "quantum.tunneling.rectangular": c_tunneling,
        "quantum.tunneling.sweep": c_tunneling_sweep,
        "quantum.circuit": c_circuit,
        "quantum.density.bell": c_bell,
        "qft.free_scalar_lattice": c_qft,
        "relativity.schwarzschild": c_schwarzschild,
        "relativity.schwarzschild.geometry": c_geometry,
        "relativity.schwarzschild.geodesic": c_geodesic,
    })

_register_computations()


@app.get("/projects")
def list_projects(include_archived: bool = True):
    return {"projects": store.list_projects(include_archived=include_archived)}


@app.post("/projects")
def create_project(req: ProjectCreate):
    try:
        return store.create_project(req.name, req.description, req.metadata)
    except Exception as e:
        raise HTTPException(422, str(e))


@app.get("/projects/{project_id}")
def get_project(project_id: str):
    try:
        return {"project": store.get_project(project_id), "experiments": store.list_experiments(project_id=project_id)}
    except KeyError:
        raise HTTPException(404, "Project not found")


@app.patch("/projects/{project_id}")
def update_project(project_id: str, req: ProjectUpdate):
    try:
        return store.update_project(project_id, name=req.name, description=req.description, archived=req.archived, metadata=req.metadata)
    except KeyError:
        raise HTTPException(404, "Project not found")
    except Exception as e:
        raise HTTPException(422, str(e))


@app.post("/projects/{project_id}/duplicate")
def duplicate_project(project_id: str, payload: dict | None = None):
    try:
        name = (payload or {}).get("name")
        return store.duplicate_project(project_id, name=name)
    except KeyError:
        raise HTTPException(404, "Project not found")
    except Exception as e:
        raise HTTPException(422, str(e))


@app.get("/projects/{project_id}/export")
def export_project(project_id: str):
    try:
        return store.export_project(project_id)
    except KeyError:
        raise HTTPException(404, "Project not found")


@app.post("/projects/import")
def import_project(req: ImportPayload):
    try:
        return store.import_project(req.payload, mode=req.mode)
    except Exception as e:
        raise HTTPException(422, str(e))


@app.post("/admin/backup")
def backup_db(payload: dict):
    dest = payload.get("destination")
    if not dest:
        raise HTTPException(422, "destination required")
    try:
        path = store.backup(dest)
        return {"status": "ok", "path": path}
    except Exception as e:
        raise HTTPException(422, str(e))


@app.post("/admin/restore")
def restore_db(payload: dict):
    src = payload.get("source")
    if not src:
        raise HTTPException(422, "source required")
    try:
        store.restore(src)
        # rebind jobs store db state (best-effort)
        return {"status": "ok", "schema_version": store.db.schema_version()}
    except Exception as e:
        raise HTTPException(422, str(e))


@app.get("/experiments")
def list_experiments(project_id: str | None = None, limit: int | None = None):
    return {"experiments": store.list_experiments(project_id=project_id, limit=limit)}


@app.get("/experiments/{experiment_id}/detail")
def get_experiment_detail(experiment_id: str):
    try:
        exp = store.get_experiment(experiment_id)
        job = jobs.get_job(experiment_id)
        return {"experiment": exp, "job": job}
    except KeyError:
        raise HTTPException(404, "Experiment not found")


@app.post("/experiments/create")
def create_experiment(req: ExperimentCreate):
    try:
        payload = req.model_dump()
        payload.setdefault("provenance", {}).setdefault("created_via", "api")
        exp = store.create_experiment(payload)
        job = None
        if req.auto_run and req.model in COMPUTATIONS:
            job = jobs.submit(exp["id"], req.model, exp.get("input_parameters") or {}, COMPUTATIONS[req.model], req.resource_limits)
        return {"experiment": store.get_experiment(exp["id"]), "job": job}
    except Exception as e:
        raise HTTPException(422, str(e))


@app.post("/experiments/{experiment_id}/run")
def run_experiment(experiment_id: str, payload: dict | None = None):
    try:
        exp = store.get_experiment(experiment_id)
        model = exp.get("model")
        if model not in COMPUTATIONS:
            raise HTTPException(422, f"No executable computation registered for model '{model}'")
        limits = (payload or {}).get("resource_limits") or {}
        job = jobs.submit(exp["id"], model, exp.get("input_parameters") or {}, COMPUTATIONS[model], limits)
        return {"experiment": store.get_experiment(exp["id"]), "job": job}
    except KeyError:
        raise HTTPException(404, "Experiment not found")


@app.post("/experiments/{experiment_id}/cancel")
def cancel_experiment(experiment_id: str):
    ok = jobs.cancel(experiment_id)
    if not ok:
        # allow marking queued/running DB records as cancelled if job not tracked
        try:
            exp = store.get_experiment(experiment_id)
            if exp.get("status") in {"queued", "running", "pending"}:
                store.update_experiment_status(experiment_id, "cancelled", "cancelled (no active job)", progress=exp.get("execution", {}).get("progress", 0.0))
                ok = True
        except KeyError:
            raise HTTPException(404, "Experiment not found")
    return {"cancelled": bool(ok), "experiment": store.get_experiment(experiment_id)}


@app.get("/jobs")
def list_jobs():
    return {"jobs": jobs.list_jobs()}


@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    j = jobs.get_job(job_id)
    if not j:
        raise HTTPException(404, "Job not found")
    return j


def run():
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("QUANTUMFORGE_PORT", "8765")), log_level="info")


if __name__ == "__main__":
    run()
