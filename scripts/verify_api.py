"""Verify all QuantumForge API endpoints and SQLite experiment persistence.
Run with backend dependencies installed (uses FastAPI TestClient).
"""
from __future__ import annotations

import json
import math
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

fd, db_path = tempfile.mkstemp(prefix="qf_verify_", suffix=".sqlite3")
os.close(fd)
os.environ["QUANTUMFORGE_DB"] = db_path

from fastapi.testclient import TestClient  # noqa: E402
from quantumforge.api import app as api_app  # noqa: E402


def main() -> int:
    failures = []
    results = []
    with TestClient(api_app.app) as c:
        def check(name, resp, cond=True):
            ok = resp.status_code < 400 and cond
            results.append({"endpoint": name, "status": resp.status_code, "ok": ok})
            if not ok:
                failures.append((name, resp.status_code, getattr(resp, "text", "")[:300]))
            return resp

        r = check("GET /health", c.get("/health"))
        d = r.json()
        assert d.get("status") == "ok" and d.get("scientific_backend") == "python"

        r = check("POST /math/root", c.post("/math/root", json={"expression": "x**2-2", "variable": "x", "bracket": [1, 2]}))
        assert abs(r.json()["root"] - math.sqrt(2)) < 1e-9

        r = check("POST /math/integrate", c.post("/math/integrate", json={"expression": "x**2", "variable": "x", "bracket": [0, 1]}))
        assert abs(r.json()["value"] - 1 / 3) < 1e-10

        r = check("POST /quantum/schrodinger/harmonic", c.post("/quantum/schrodinger/harmonic", json={"omega": 1.0, "points": 801, "states": 3}))
        assert len(r.json()["energies"]) == 3

        r = check("POST /quantum/circuit", c.post("/quantum/circuit", json={"n_qubits": 2, "operations": [{"gate": "H", "target": 0}, {"gate": "CNOT", "control": 0, "target": 1}]}))
        probs = r.json()["probabilities"]
        assert abs(probs[0] - 0.5) < 1e-9 and abs(probs[3] - 0.5) < 1e-9

        r = check("POST /quantum/schrodinger/evolve", c.post("/quantum/schrodinger/evolve", json={"potential": {"type": "harmonic", "omega": 1.0}, "points": 201, "dt": 0.02, "steps": 20, "sample_every": 10}))
        assert r.json()["norm_drift_max"] < 1e-5

        r = check("POST /quantum/tunneling/rectangular", c.post("/quantum/tunneling/rectangular", json={"energy": 0.5, "barrier_height": 1.0, "barrier_width": 1.0}))
        assert r.json()["conservation_error"] < 1e-12

        r = check("GET /quantum/spin/operators", c.get("/quantum/spin/operators"))
        assert "Sx" in r.json() and "Sy" in r.json() and "Sz" in r.json()

        r = check("GET /quantum/density/bell", c.get("/quantum/density/bell"))
        assert r.json()["diagnostics"]["valid_density_matrix"] is True

        bell = r.json()
        r = check("POST /quantum/density/diagnostics", c.post("/quantum/density/diagnostics", json={"real": bell["real"], "imag": bell["imag"]}))
        assert r.json()["valid_density_matrix"] is True

        r = check("POST /quantum/info/metrics", c.post("/quantum/info/metrics", json={"rho_real": bell["real"], "rho_imag": bell["imag"], "dims": [2,2], "keep": [0]}))
        assert abs(r.json()["entanglement_entropy_bits"] - 1.0) < 1e-10

        r = check("POST /quantum/channel/apply", c.post("/quantum/channel/apply", json={"real": [[1,0],[0,0]], "imag": [[0,0],[0,0]], "channel": "depolarizing", "p": 0.2}))
        assert r.json()["completeness_residual"] < 1e-12

        r = check("POST /qft/free-scalar-lattice", c.post("/qft/free-scalar-lattice", json={"mass": 1.0, "sites": 32, "spacing": 0.2}))
        assert len(r.json()["mode_frequencies"]) == 32 and r.json()["vacuum_energy_lattice"] > 0

        r = check("POST /relativity/lorentz", c.post("/relativity/lorentz", json=[0.3, 0.2, 0.1]))
        assert r.json()["metric_invariance_residual"] < 1e-12

        r = check("POST /relativity/schwarzschild", c.post("/relativity/schwarzschild", json={"mass_kg": 1.98847e30}))
        assert abs(r.json()["schwarzschild_radius_m"] - 2953.34) < 10

        r = check("GET /relativity/schwarzschild/geometry", c.get("/relativity/schwarzschild/geometry"))
        assert r.json()["ricci_scalar"] == "0"

        r0 = 10.0
        energy = (r0 - 2) / math.sqrt(r0 * (r0 - 3))
        angular = math.sqrt(r0 * r0 / (r0 - 3))
        r = check("POST /relativity/schwarzschild/geodesic", c.post("/relativity/schwarzschild/geodesic", json={"r0": r0, "energy": energy, "angular_momentum": angular, "radial_velocity": 0, "affine_end": 1, "samples": 50, "kind": "timelike"}))
        assert r.json()["max_normalization_error"] < 1e-8

        payload = {"model": "verify", "config": {"a": 1}, "result": {"b": 2}}
        r = check("POST /experiments", c.post("/experiments", json=payload))
        eid = r.json()["id"]
        r = check(f"GET /experiments/{eid}", c.get(f"/experiments/{eid}"))
        row = r.json()
        assert row["id"] == eid and row["model"] == "verify"
        assert json.loads(row["config_json"]) == payload["config"]
        assert json.loads(row["result_json"]) == payload["result"]
        assert row["sha256"] == r.json()["sha256"]

        from quantumforge.storage.experiments import ExperimentStore
        row2 = ExperimentStore(db_path).get(eid)
        assert row2["sha256"] == row["sha256"]

    try:
        Path(db_path).unlink(missing_ok=True)
    except Exception:
        pass

    print(f"ENDPOINTS_VERIFIED={len(results)} FAILURES={len(failures)}")
    if failures:
        for f in failures:
            print("FAIL:", f)
        return 1
    print("ALL_ENDPOINTS_OK")
    print("SQLITE_PERSISTENCE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
