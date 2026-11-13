import json
import os
import sqlite3
import time
from pathlib import Path

import pytest

from quantumforge.storage.db import Database, ExperimentStore, SCHEMA_VERSION


def test_migration_creates_schema_and_legacy_import(tmp_path):
    db_path = tmp_path / "legacy.sqlite3"
    # create 0.2.x legacy schema
    con = sqlite3.connect(db_path)
    con.execute("CREATE TABLE experiments (id TEXT PRIMARY KEY, created_at TEXT NOT NULL, model TEXT NOT NULL, config_json TEXT NOT NULL, result_json TEXT NOT NULL, sha256 TEXT NOT NULL)")
    con.execute("INSERT INTO experiments VALUES (?,?,?,?,?,?)", ("abc123", "2026-01-01T00:00:00Z", "demo", json.dumps({"a":1}, sort_keys=True), json.dumps({"b":2}, sort_keys=True), "deadbeef"))
    con.commit(); con.close()

    db = Database(db_path)
    assert db.schema_version() == SCHEMA_VERSION
    store = ExperimentStore(db_path)
    projects = store.list_projects()
    assert any(p["name"] == "Imported 0.2.x Experiments" for p in projects)
    exps = store.list_experiments()
    assert len(exps) == 1
    assert exps[0]["legacy_id"] == "abc123"
    assert exps[0]["status"] == "completed"
    # legacy compatibility lookup
    legacy = store.get("abc123")
    assert legacy["model"] == "demo"


def test_project_crud_duplicate_archive(tmp_path):
    store = ExperimentStore(tmp_path / "p.sqlite3")
    p = store.create_project("Alpha", "desc", {"owner": "x"})
    assert p["name"] == "Alpha" and p["archived"] is False
    got = store.get_project(p["id"])
    assert got["id"] == p["id"]
    upd = store.update_project(p["id"], name="Alpha2", archived=True)
    assert upd["name"] == "Alpha2" and upd["archived"] is True
    listed = store.list_projects(include_archived=False)
    assert all(x["id"] != p["id"] for x in listed)
    dup = store.duplicate_project(p["id"], name="Alpha Copy")
    assert dup["id"] != p["id"] and dup["name"] == "Alpha Copy"


def test_experiment_create_schema_and_snapshot(tmp_path):
    store = ExperimentStore(tmp_path / "e.sqlite3")
    p = store.create_project("P")
    exp = store.create_experiment({
        "project_id": p["id"], "name": "E1", "description": "d", "scientific_domain": "quantum",
        "model": "math.root", "input_parameters": {"expression": "x**2-2", "variable": "x", "bracket": [1,2]},
        "input_units": {"x": "1"}, "initial_conditions": {}, "numerical_method": "brentq",
        "solver_configuration": {"xtol": 1e-10}, "seed": 42, "deterministic": True,
        "provenance": {"note": "t"}
    })
    for k in ["id","name","description","scientific_domain","input_parameters","input_units","initial_conditions","numerical_method","solver_configuration","status","execution","result","error","provenance","software_version","created_at","updated_at","parameter_snapshot","seed"]:
        assert k in exp
    assert exp["seed"] == 42
    assert exp["parameter_snapshot"]["model"] == "math.root"
    assert exp["provenance"]["software"]["quantumforge_version"]


def test_project_export_import_roundtrip(tmp_path):
    store = ExperimentStore(tmp_path / "r.sqlite3")
    p = store.create_project("R")
    store.create_experiment({"project_id": p["id"], "name": "E", "scientific_domain": "math", "model": "math.root", "input_parameters": {"expression":"x-1","variable":"x","bracket":[0,2]}})
    exported = store.export_project(p["id"])
    assert exported["format"] == "quantumforge.project-export"
    assert len(exported["experiments"]) == 1
    imported = store.import_project(exported)
    assert imported["project"]["id"] != p["id"]
    exps = store.list_experiments(project_id=imported["project"]["id"])
    assert len(exps) == 1
    assert exps[0]["name"] == "E"


def test_backup_restore(tmp_path):
    db = tmp_path / "b.sqlite3"
    backup = tmp_path / "backup.sqlite3"
    store = ExperimentStore(db)
    p = store.create_project("B")
    store.backup(backup)
    store.create_project("After")
    assert len(store.list_projects()) >= 2
    store.restore(backup)
    projects = store.list_projects()
    assert any(x["id"] == p["id"] for x in projects)
    assert all(x["name"] != "After" for x in projects)
