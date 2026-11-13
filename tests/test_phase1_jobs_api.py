import time

from fastapi.testclient import TestClient

from quantumforge.api.app import app


def _wait_job(client, exp_id, timeout=10):
    deadline = time.time() + timeout
    while time.time() < deadline:
        r = client.get(f"/experiments/{exp_id}/detail")
        assert r.status_code == 200
        data = r.json()
        status = data["experiment"]["status"]
        if status in {"completed", "failed", "cancelled"}:
            return data
        time.sleep(0.05)
    raise AssertionError("timeout waiting for job")


def test_project_experiment_api_and_background_run():
    with TestClient(app) as client:
        r = client.post("/projects", json={"name": "P1", "description": "d"})
        assert r.status_code == 200
        p = r.json()
        r = client.get("/projects")
        assert any(x["id"] == p["id"] for x in r.json()["projects"])

        r = client.post("/experiments/create", json={
            "project_id": p["id"], "name": "Root", "scientific_domain": "math",
            "model": "math.root", "input_parameters": {"expression": "x**2-2", "variable": "x", "bracket": [1,2]},
            "numerical_method": "brentq", "solver_configuration": {"xtol": 1e-10}, "auto_run": True
        })
        assert r.status_code == 200
        exp = r.json()["experiment"]
        done = _wait_job(client, exp["id"])
        assert done["experiment"]["status"] == "completed"
        assert abs(done["experiment"]["result"]["root"] - 2**0.5) < 1e-9
        assert done["experiment"]["parameter_snapshot"]["model"] == "math.root"

        r = client.get(f"/projects/{p['id']}")
        assert r.status_code == 200
        assert len(r.json()["experiments"]) >= 1

        r = client.get(f"/projects/{p['id']}/export")
        assert r.status_code == 200
        exported = r.json()
        r = client.post("/projects/import", json={"payload": exported, "mode": "new"})
        assert r.status_code == 200
        imported = r.json()["project"]
        assert imported["id"] != p["id"]

        r = client.post(f"/projects/{p['id']}/duplicate", json={"name": "P1 Copy"})
        assert r.status_code == 200
        assert r.json()["name"] == "P1 Copy"

        r = client.patch(f"/projects/{p['id']}", json={"archived": True})
        assert r.status_code == 200 and r.json()["archived"] is True


def test_experiment_cancel_and_history():
    from quantumforge.api.app import COMPUTATIONS
    import time as _t

    def slow(params, progress, cancel):
        for i in range(50):
            if cancel.is_set():
                raise Exception("cancelled")
            progress(i/50, "working")
            _t.sleep(0.02)
        return {"ok": True}

    COMPUTATIONS["test.slow"] = slow
    try:
        with TestClient(app) as client:
            p = client.post("/projects", json={"name": "PC"}).json()
            r = client.post("/experiments/create", json={"project_id": p["id"], "name": "Slow", "model": "test.slow", "input_parameters": {}, "auto_run": True})
            exp = r.json()["experiment"]
            time.sleep(0.05)
            c = client.post(f"/experiments/{exp['id']}/cancel")
            assert c.status_code == 200
            done = _wait_job(client, exp["id"])
            assert done["experiment"]["status"] in {"cancelled", "failed"}
    finally:
        COMPUTATIONS.pop("test.slow", None)
