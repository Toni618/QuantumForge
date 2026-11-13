"""SQLite database, migrations, and persistence foundation for QuantumForge 0.3.0."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import random
import shutil
import sqlite3
import sys
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from quantumforge import __version__

SCHEMA_VERSION = 1
EXPERIMENT_STATUSES = {"pending", "queued", "running", "completed", "failed", "cancelled"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False, default=str)


def new_id() -> str:
    return uuid.uuid4().hex


def content_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def software_info() -> dict[str, Any]:
    return {
        "quantumforge_version": __version__,
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
    }


class Database:
    def __init__(self, path: str | os.PathLike[str] = "quantumforge.sqlite3"):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._init()

    def connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=30.0, isolation_level=None, check_same_thread=False)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        db.execute("PRAGMA journal_mode = WAL")
        db.execute("PRAGMA synchronous = NORMAL")
        db.execute("PRAGMA busy_timeout = 30000")
        return db

    def _init(self) -> None:
        with self._lock, self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                db.execute(
                    "CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)"
                )
                row = db.execute("SELECT MAX(version) AS v FROM schema_migrations").fetchone()
                current = int(row["v"] or 0)
                for version, fn in self._migrations():
                    if version > current:
                        fn(db)
                        db.execute(
                            "INSERT INTO schema_migrations(version, applied_at) VALUES (?, ?)",
                            (version, utc_now()),
                        )
                db.execute("COMMIT")
            except Exception:
                db.execute("ROLLBACK")
                raise

    def _migrations(self) -> list[tuple[int, Callable[[sqlite3.Connection], None]]]:
        return [(1, self._migrate_v1)]

    def _migrate_v1(self, db: sqlite3.Connection) -> None:
        # Legacy experiments table (0.2.x) -> preserve as experiments_legacy and migrate rows.
        tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        if "experiments" in tables:
            cols = {r[1] for r in db.execute("PRAGMA table_info(experiments)").fetchall()}
            if "project_id" not in cols:
                db.execute("ALTER TABLE experiments RENAME TO experiments_legacy")

        db.execute(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                archived INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                schema_version INTEGER NOT NULL DEFAULT 1,
                metadata_json TEXT NOT NULL DEFAULT '{}'
            )
            """
        )
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS experiments (
                id TEXT PRIMARY KEY,
                legacy_id TEXT UNIQUE,
                project_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                scientific_domain TEXT NOT NULL,
                model TEXT NOT NULL,
                status TEXT NOT NULL,
                input_parameters_json TEXT NOT NULL,
                input_units_json TEXT NOT NULL,
                initial_conditions_json TEXT NOT NULL,
                numerical_method TEXT NOT NULL,
                solver_configuration_json TEXT NOT NULL,
                parameter_snapshot_json TEXT NOT NULL,
                seed INTEGER,
                deterministic INTEGER NOT NULL DEFAULT 0,
                execution_json TEXT NOT NULL,
                result_json TEXT,
                result_reference TEXT,
                error_json TEXT,
                provenance_json TEXT NOT NULL,
                schema_version INTEGER NOT NULL DEFAULT 1,
                software_version TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT,
                cancelled_at TEXT,
                FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
            """
        )
        db.execute("CREATE INDEX IF NOT EXISTS idx_experiments_project ON experiments(project_id)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_experiments_status ON experiments(status)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_experiments_created ON experiments(created_at)")
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                experiment_id TEXT NOT NULL,
                status TEXT NOT NULL,
                progress REAL NOT NULL DEFAULT 0,
                message TEXT NOT NULL DEFAULT '',
                cancel_requested INTEGER NOT NULL DEFAULT 0,
                resource_limits_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                started_at TEXT,
                finished_at TEXT,
                FOREIGN KEY(experiment_id) REFERENCES experiments(id) ON DELETE CASCADE
            )
            """
        )
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS computation_cache (
                cache_key TEXT PRIMARY KEY,
                experiment_id TEXT,
                result_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

        # Migrate legacy rows into a default imported project.
        legacy_rows = []
        try:
            legacy_rows = db.execute("SELECT * FROM experiments_legacy").fetchall()
        except sqlite3.Error:
            legacy_rows = []
        if legacy_rows:
            existing_default = db.execute(
                "SELECT id FROM projects WHERE name = ?", ("Imported 0.2.x Experiments",)
            ).fetchone()
            if existing_default:
                project_id = existing_default["id"]
            else:
                project_id = new_id()
                now = utc_now()
                db.execute(
                    "INSERT INTO projects(id,name,description,archived,created_at,updated_at,schema_version,metadata_json) VALUES (?,?,?,?,?,?,?,?)",
                    (project_id, "Imported 0.2.x Experiments", "Auto-migrated from QuantumForge 0.2.x schema", 0, now, now, SCHEMA_VERSION, canonical_json({"source": "migration_v1"})),
                )
            for row in legacy_rows:
                rowd = dict(row)
                legacy_id = str(rowd.get("id"))
                if db.execute("SELECT 1 FROM experiments WHERE legacy_id = ?", (legacy_id,)).fetchone():
                    continue
                config = json.loads(rowd.get("config_json") or "{}")
                result = json.loads(rowd.get("result_json") or "{}")
                created = rowd.get("created_at") or utc_now()
                domain = infer_domain(rowd.get("model", "legacy"))
                exp_id = new_id()
                provenance = {
                    "migrated_from_legacy": True,
                    "legacy_sha256": rowd.get("sha256"),
                    "software": {"quantumforge_version": "0.2.x-migrated", "migrated_to": __version__},
                }
                db.execute(
                    """
                    INSERT INTO experiments(
                        id, legacy_id, project_id, name, description, scientific_domain, model, status,
                        input_parameters_json, input_units_json, initial_conditions_json, numerical_method,
                        solver_configuration_json, parameter_snapshot_json, seed, deterministic,
                        execution_json, result_json, result_reference, error_json, provenance_json,
                        schema_version, software_version, created_at, updated_at, started_at, completed_at, cancelled_at
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        exp_id, legacy_id, project_id, f"Legacy {rowd.get('model','experiment')}", "Migrated legacy record",
                        domain, str(rowd.get("model", "legacy")), "completed",
                        canonical_json(config), canonical_json({}), canonical_json({}), "legacy",
                        canonical_json({"legacy": True}), canonical_json({"config": config}),
                        None, 0,
                        canonical_json({"status_history": [{"status": "completed", "at": created, "message": "migrated"}], "progress": 1.0}),
                        canonical_json(result), None, None, canonical_json(provenance),
                        SCHEMA_VERSION, __version__, created, created, created, created, None,
                    ),
                )

    def schema_version(self) -> int:
        with self.connect() as db:
            row = db.execute("SELECT MAX(version) AS v FROM schema_migrations").fetchone()
            return int(row["v"] or 0)

    def backup(self, destination: str | os.PathLike[str]) -> str:
        dest = Path(destination)
        dest.parent.mkdir(parents=True, exist_ok=True)
        with self._lock, self.connect() as src, sqlite3.connect(str(dest)) as dst:
            src.backup(dst)
        return str(dest)

    def restore(self, source: str | os.PathLike[str]) -> None:
        src = Path(source)
        if not src.exists():
            raise FileNotFoundError(str(src))
        # validate sqlite file
        conn = sqlite3.connect(str(src))
        try:
            conn.execute("PRAGMA schema_version")
        finally:
            conn.close()
        with self._lock:
            # Best-effort checkpoint/cleanup of WAL sidecars so restore is authoritative.
            try:
                with self.connect() as db:
                    db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            except Exception:
                pass
            tmp = Path(self.path + ".restore_tmp")
            shutil.copy2(src, tmp)
            os.replace(tmp, self.path)
            for suffix in ("-wal", "-shm"):
                side = Path(self.path + suffix)
                try:
                    if side.exists():
                        side.unlink()
                except Exception:
                    pass
        # re-run migrations on restored DB for forward compatibility
        self._init()


def infer_domain(model: str) -> str:
    m = (model or "").lower()
    if "quantum" in m or "circuit" in m or "schrodinger" in m or "density" in m or "spin" in m:
        return "quantum"
    if "qft" in m or "scalar" in m:
        return "qft"
    if "relativity" in m or "lorentz" in m or "geodesic" in m or "metric" in m or "schwarzschild" in m or "black" in m:
        return "relativity"
    if "math" in m or "root" in m or "integrat" in m:
        return "mathematics"
    return "general"


class ExperimentStore:
    """Compatibility + Phase 1 storage API."""

    def __init__(self, path: str | os.PathLike[str] = "quantumforge.sqlite3"):
        self.db = Database(path)
        self.path = self.db.path

    # ---- legacy API (0.2.x) ----
    def save(self, model, config, result):
        payload = {"model": model, "config": config, "result": result}
        digest = content_hash(payload)
        legacy_id = digest[:16]
        # store as a completed experiment in default project for compatibility
        project = self.ensure_default_project()
        now = utc_now()
        with self.db.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                # idempotent by legacy_id
                row = db.execute("SELECT id FROM experiments WHERE legacy_id = ?", (legacy_id,)).fetchone()
                if row:
                    exp_id = row["id"]
                else:
                    exp_id = new_id()
                provenance = {"legacy_compat": True, "software": software_info(), "sha256": digest}
                self._upsert_experiment_row(
                    db,
                    exp_id=exp_id,
                    legacy_id=legacy_id,
                    project_id=project["id"],
                    name=f"Legacy {model}",
                    description="Saved via legacy /experiments API",
                    scientific_domain=infer_domain(str(model)),
                    model=str(model),
                    status="completed",
                    input_parameters=config or {},
                    input_units={},
                    initial_conditions={},
                    numerical_method="legacy",
                    solver_configuration={"legacy": True},
                    parameter_snapshot={"config": config},
                    seed=None,
                    deterministic=False,
                    execution={"progress": 1.0, "status_history": [{"status": "completed", "at": now, "message": "legacy save"}]},
                    result=result,
                    result_reference=None,
                    error=None,
                    provenance=provenance,
                    started_at=now,
                    completed_at=now,
                    cancelled_at=None,
                    created_at=now,
                    updated_at=now,
                )
                db.execute("COMMIT")
            except Exception:
                db.execute("ROLLBACK")
                raise
        return {"id": legacy_id, "sha256": digest}

    def get(self, eid):
        with self.db.connect() as db:
            row = db.execute("SELECT * FROM experiments WHERE legacy_id = ?", (eid,)).fetchone()
            if row is None:
                # also allow native experiment id lookup for compatibility
                row = db.execute("SELECT * FROM experiments WHERE id = ?", (eid,)).fetchone()
            if row is None:
                raise KeyError(eid)
            d = dict(row)
            if d.get("legacy_id") == eid or (d.get("legacy_id") and len(str(eid)) == 16):
                # legacy-shaped response expected by old tests/scripts
                return {
                    "id": d.get("legacy_id") or d.get("id"),
                    "created_at": d.get("created_at"),
                    "model": d.get("model"),
                    "config_json": canonical_json(json.loads(d.get("input_parameters_json") or "{}")),
                    "result_json": canonical_json(json.loads(d.get("result_json") or "null")),
                    "sha256": (json.loads(d.get("provenance_json") or "{}").get("sha256") or d.get("legacy_id") or ""),
                }
            return self._experiment_to_dict(d)

    # ---- project API ----
    def ensure_default_project(self) -> dict[str, Any]:
        with self.db.connect() as db:
            row = db.execute("SELECT * FROM projects WHERE archived = 0 ORDER BY created_at ASC LIMIT 1").fetchone()
            if row:
                return self._project_to_dict(dict(row))
            now = utc_now()
            pid = new_id()
            db.execute("BEGIN IMMEDIATE")
            db.execute(
                "INSERT INTO projects(id,name,description,archived,created_at,updated_at,schema_version,metadata_json) VALUES (?,?,?,?,?,?,?,?)",
                (pid, "Default Project", "Default workspace project", 0, now, now, SCHEMA_VERSION, canonical_json({"default": True})),
            )
            db.execute("COMMIT")
            row = db.execute("SELECT * FROM projects WHERE id = ?", (pid,)).fetchone()
            return self._project_to_dict(dict(row))

    def list_projects(self, include_archived: bool = True) -> list[dict[str, Any]]:
        q = "SELECT * FROM projects"
        params: tuple[Any, ...] = ()
        if not include_archived:
            q += " WHERE archived = 0"
        q += " ORDER BY updated_at DESC"
        with self.db.connect() as db:
            rows = db.execute(q, params).fetchall()
        return [self._project_to_dict(dict(r)) for r in rows]

    def create_project(self, name: str, description: str = "", metadata: dict | None = None) -> dict[str, Any]:
        if not (name or "").strip():
            raise ValueError("Project name is required")
        now = utc_now()
        pid = new_id()
        with self.db.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute(
                "INSERT INTO projects(id,name,description,archived,created_at,updated_at,schema_version,metadata_json) VALUES (?,?,?,?,?,?,?,?)",
                (pid, name.strip(), description or "", 0, now, now, SCHEMA_VERSION, canonical_json(metadata or {})),
            )
            db.execute("COMMIT")
            row = db.execute("SELECT * FROM projects WHERE id = ?", (pid,)).fetchone()
        return self._project_to_dict(dict(row))

    def get_project(self, project_id: str) -> dict[str, Any]:
        with self.db.connect() as db:
            row = db.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        if not row:
            raise KeyError(project_id)
        return self._project_to_dict(dict(row))

    def update_project(self, project_id: str, name: str | None = None, description: str | None = None, archived: bool | None = None, metadata: dict | None = None) -> dict[str, Any]:
        with self.db.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
            if not row:
                db.execute("ROLLBACK")
                raise KeyError(project_id)
            cur = dict(row)
            new_name = (name.strip() if isinstance(name, str) and name.strip() else cur["name"])
            new_desc = description if description is not None else cur["description"]
            new_arch = int(bool(archived)) if archived is not None else int(cur["archived"])
            new_meta = metadata if metadata is not None else json.loads(cur["metadata_json"] or "{}")
            now = utc_now()
            db.execute(
                "UPDATE projects SET name=?, description=?, archived=?, updated_at=?, metadata_json=? WHERE id=?",
                (new_name, new_desc, new_arch, now, canonical_json(new_meta), project_id),
            )
            db.execute("COMMIT")
            row = db.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        return self._project_to_dict(dict(row))

    def duplicate_project(self, project_id: str, name: str | None = None) -> dict[str, Any]:
        with self.db.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            src = db.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
            if not src:
                db.execute("ROLLBACK")
                raise KeyError(project_id)
            now = utc_now()
            new_pid = new_id()
            srcd = dict(src)
            new_name = name.strip() if isinstance(name, str) and name.strip() else f"{srcd['name']} (Copy)"
            db.execute(
                "INSERT INTO projects(id,name,description,archived,created_at,updated_at,schema_version,metadata_json) VALUES (?,?,?,?,?,?,?,?)",
                (new_pid, new_name, srcd.get("description") or "", 0, now, now, SCHEMA_VERSION, srcd.get("metadata_json") or canonical_json({})),
            )
            exps = db.execute("SELECT * FROM experiments WHERE project_id = ?", (project_id,)).fetchall()
            for er in exps:
                e = dict(er)
                new_eid = new_id()
                db.execute(
                    """
                    INSERT INTO experiments(
                        id, legacy_id, project_id, name, description, scientific_domain, model, status,
                        input_parameters_json, input_units_json, initial_conditions_json, numerical_method,
                        solver_configuration_json, parameter_snapshot_json, seed, deterministic,
                        execution_json, result_json, result_reference, error_json, provenance_json,
                        schema_version, software_version, created_at, updated_at, started_at, completed_at, cancelled_at
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        new_eid, None, new_pid, e["name"], e.get("description") or "", e["scientific_domain"], e["model"],
                        e["status"], e["input_parameters_json"], e["input_units_json"], e["initial_conditions_json"],
                        e["numerical_method"], e["solver_configuration_json"], e["parameter_snapshot_json"], e.get("seed"),
                        e.get("deterministic", 0), e["execution_json"], e.get("result_json"), e.get("result_reference"),
                        e.get("error_json"), e["provenance_json"], e.get("schema_version", SCHEMA_VERSION), e.get("software_version", __version__),
                        e.get("created_at") or now, now, e.get("started_at"), e.get("completed_at"), e.get("cancelled_at"),
                    ),
                )
            db.execute("COMMIT")
            row = db.execute("SELECT * FROM projects WHERE id = ?", (new_pid,)).fetchone()
        return self._project_to_dict(dict(row))

    # ---- experiment API ----
    def list_experiments(self, project_id: str | None = None, limit: int | None = None) -> list[dict[str, Any]]:
        q = "SELECT * FROM experiments"
        params: list[Any] = []
        if project_id:
            q += " WHERE project_id = ?"
            params.append(project_id)
        q += " ORDER BY created_at DESC"
        if limit:
            q += " LIMIT ?"
            params.append(int(limit))
        with self.db.connect() as db:
            rows = db.execute(q, tuple(params)).fetchall()
        return [self._experiment_to_dict(dict(r)) for r in rows]

    def get_experiment(self, experiment_id: str) -> dict[str, Any]:
        with self.db.connect() as db:
            row = db.execute("SELECT * FROM experiments WHERE id = ? OR legacy_id = ?", (experiment_id, experiment_id)).fetchone()
        if not row:
            raise KeyError(experiment_id)
        return self._experiment_to_dict(dict(row))

    def create_experiment(self, payload: dict[str, Any]) -> dict[str, Any]:
        project_id = payload.get("project_id") or self.ensure_default_project()["id"]
        self.get_project(project_id)
        now = utc_now()
        exp_id = new_id()
        seed = payload.get("seed")
        if seed is None and payload.get("deterministic"):
            seed = random.randint(0, 2**31 - 1)
        data = self._normalize_experiment_payload(payload, exp_id=exp_id, project_id=project_id, now=now, seed=seed)
        with self.db.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                self._insert_experiment(db, data)
                db.execute("COMMIT")
            except Exception:
                db.execute("ROLLBACK")
                raise
            row = db.execute("SELECT * FROM experiments WHERE id = ?", (exp_id,)).fetchone()
        return self._experiment_to_dict(dict(row))

    def update_experiment_status(self, experiment_id: str, status: str, message: str = "", result: Any = None, error: Any = None, progress: float | None = None, execution_patch: dict | None = None) -> dict[str, Any]:
        if status not in EXPERIMENT_STATUSES:
            raise ValueError(f"Invalid status: {status}")
        now = utc_now()
        with self.db.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                row = db.execute("SELECT * FROM experiments WHERE id = ?", (experiment_id,)).fetchone()
                if not row:
                    raise KeyError(experiment_id)
                cur = self._experiment_to_dict(dict(row))
                execution = cur.get("execution") or {}
                history = execution.get("status_history") or []
                history.append({"status": status, "at": now, "message": message})
                execution["status_history"] = history
                if progress is not None:
                    execution["progress"] = float(progress)
                if execution_patch:
                    execution.update(execution_patch)
                started_at = cur.get("started_at")
                completed_at = cur.get("completed_at")
                cancelled_at = cur.get("cancelled_at")
                if status == "running" and not started_at:
                    started_at = now
                if status in {"completed", "failed"}:
                    completed_at = now
                if status == "cancelled":
                    cancelled_at = now
                    completed_at = now
                db.execute(
                    """
                    UPDATE experiments SET status=?, execution_json=?, result_json=?, error_json=?,
                        updated_at=?, started_at=?, completed_at=?, cancelled_at=?
                    WHERE id=?
                    """,
                    (
                        status,
                        canonical_json(execution),
                        canonical_json(result) if result is not None else (canonical_json(cur.get("result")) if cur.get("result") is not None else None),
                        canonical_json(error) if error is not None else (canonical_json(cur.get("error")) if cur.get("error") is not None else None),
                        now, started_at, completed_at, cancelled_at, experiment_id,
                    ),
                )
                db.execute("COMMIT")
                row = db.execute("SELECT * FROM experiments WHERE id = ?", (experiment_id,)).fetchone()
            except Exception:
                db.execute("ROLLBACK")
                raise
        return self._experiment_to_dict(dict(row))

    # ---- import/export/backup/restore ----
    def export_project(self, project_id: str) -> dict[str, Any]:
        project = self.get_project(project_id)
        experiments = self.list_experiments(project_id=project_id)
        return {
            "format": "quantumforge.project-export",
            "format_version": 1,
            "exported_at": utc_now(),
            "software": software_info(),
            "project": project,
            "experiments": experiments,
        }

    def import_project(self, payload: dict[str, Any], mode: str = "new") -> dict[str, Any]:
        if payload.get("format") != "quantumforge.project-export":
            raise ValueError("Unsupported import format")
        if int(payload.get("format_version", 0)) != 1:
            raise ValueError("Unsupported import format version")
        proj = payload.get("project") or {}
        exps = payload.get("experiments") or []
        if not isinstance(exps, list):
            raise ValueError("Invalid experiments payload")
        now = utc_now()
        with self.db.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                new_pid = new_id()
                name = str(proj.get("name") or "Imported Project")
                if mode != "overwrite":
                    name = f"{name} (Imported)"
                db.execute(
                    "INSERT INTO projects(id,name,description,archived,created_at,updated_at,schema_version,metadata_json) VALUES (?,?,?,?,?,?,?,?)",
                    (new_pid, name, str(proj.get("description") or ""), 0, now, now, SCHEMA_VERSION, canonical_json(proj.get("metadata") or {"imported": True})),
                )
                imported_ids = []
                for e in exps:
                    if not isinstance(e, dict):
                        raise ValueError("Invalid experiment entry")
                    data = self._normalize_experiment_payload(e, exp_id=new_id(), project_id=new_pid, now=now, seed=e.get("seed"), preserve_identity=False)
                    # preserve historical timestamps where present
                    data["created_at"] = e.get("created_at") or data["created_at"]
                    data["started_at"] = e.get("started_at")
                    data["completed_at"] = e.get("completed_at")
                    data["cancelled_at"] = e.get("cancelled_at")
                    data["status"] = e.get("status") or data["status"]
                    data["result_json"] = canonical_json(e.get("result")) if e.get("result") is not None else None
                    data["error_json"] = canonical_json(e.get("error")) if e.get("error") is not None else None
                    self._insert_experiment(db, data)
                    imported_ids.append(data["id"])
                db.execute("COMMIT")
            except Exception:
                db.execute("ROLLBACK")
                raise
        return {"project": self.get_project(new_pid), "imported_experiment_ids": imported_ids}

    def backup(self, destination: str) -> str:
        return self.db.backup(destination)

    def restore(self, source: str) -> None:
        self.db.restore(source)

    # ---- internals ----
    def _normalize_experiment_payload(self, payload: dict[str, Any], exp_id: str, project_id: str, now: str, seed: Any, preserve_identity: bool = True) -> dict[str, Any]:
        name = str(payload.get("name") or payload.get("model") or "Experiment")
        model = str(payload.get("model") or payload.get("computation", {}).get("model") or "unknown")
        domain = str(payload.get("scientific_domain") or infer_domain(model))
        status = str(payload.get("status") or "pending")
        if status not in EXPERIMENT_STATUSES:
            status = "pending"
        inputs = payload.get("input_parameters") or payload.get("config") or {}
        units = payload.get("input_units") or {}
        initial = payload.get("initial_conditions") or {}
        numerical_method = str(payload.get("numerical_method") or payload.get("solver_configuration", {}).get("method") or "default")
        solver_cfg = payload.get("solver_configuration") or {}
        deterministic = bool(payload.get("deterministic", seed is not None))
        provenance = payload.get("provenance") or {}
        provenance.setdefault("software", software_info())
        provenance.setdefault("schema_version", SCHEMA_VERSION)
        snapshot = {
            "input_parameters": inputs,
            "input_units": units,
            "initial_conditions": initial,
            "numerical_method": numerical_method,
            "solver_configuration": solver_cfg,
            "seed": seed,
            "model": model,
            "scientific_domain": domain,
            "snapshot_at": now,
        }
        execution = payload.get("execution") or {"progress": 0.0, "status_history": [{"status": status, "at": now, "message": "created"}], "runtime": {}}
        if "progress" not in execution:
            execution["progress"] = 0.0
        return {
            "id": exp_id if not preserve_identity or not payload.get("id") else str(payload.get("id")),
            "legacy_id": None,
            "project_id": project_id,
            "name": name,
            "description": str(payload.get("description") or ""),
            "scientific_domain": domain,
            "model": model,
            "status": status,
            "input_parameters_json": canonical_json(inputs),
            "input_units_json": canonical_json(units),
            "initial_conditions_json": canonical_json(initial),
            "numerical_method": numerical_method,
            "solver_configuration_json": canonical_json(solver_cfg),
            "parameter_snapshot_json": canonical_json(snapshot),
            "seed": seed,
            "deterministic": 1 if deterministic else 0,
            "execution_json": canonical_json(execution),
            "result_json": canonical_json(payload.get("result")) if payload.get("result") is not None else None,
            "result_reference": payload.get("result_reference"),
            "error_json": canonical_json(payload.get("error")) if payload.get("error") is not None else None,
            "provenance_json": canonical_json(provenance),
            "schema_version": SCHEMA_VERSION,
            "software_version": __version__,
            "created_at": payload.get("created_at") or now,
            "updated_at": now,
            "started_at": payload.get("started_at"),
            "completed_at": payload.get("completed_at"),
            "cancelled_at": payload.get("cancelled_at"),
        }

    def _insert_experiment(self, db: sqlite3.Connection, data: dict[str, Any]) -> None:
        db.execute(
            """
            INSERT INTO experiments(
                id, legacy_id, project_id, name, description, scientific_domain, model, status,
                input_parameters_json, input_units_json, initial_conditions_json, numerical_method,
                solver_configuration_json, parameter_snapshot_json, seed, deterministic,
                execution_json, result_json, result_reference, error_json, provenance_json,
                schema_version, software_version, created_at, updated_at, started_at, completed_at, cancelled_at
            ) VALUES (:id,:legacy_id,:project_id,:name,:description,:scientific_domain,:model,:status,
                :input_parameters_json,:input_units_json,:initial_conditions_json,:numerical_method,
                :solver_configuration_json,:parameter_snapshot_json,:seed,:deterministic,
                :execution_json,:result_json,:result_reference,:error_json,:provenance_json,
                :schema_version,:software_version,:created_at,:updated_at,:started_at,:completed_at,:cancelled_at)
            """,
            data,
        )

    def _upsert_experiment_row(self, db: sqlite3.Connection, **kwargs) -> None:
        data = {
            "id": kwargs["exp_id"], "legacy_id": kwargs.get("legacy_id"), "project_id": kwargs["project_id"],
            "name": kwargs["name"], "description": kwargs.get("description", ""), "scientific_domain": kwargs["scientific_domain"],
            "model": kwargs["model"], "status": kwargs["status"],
            "input_parameters_json": canonical_json(kwargs.get("input_parameters") or {}),
            "input_units_json": canonical_json(kwargs.get("input_units") or {}),
            "initial_conditions_json": canonical_json(kwargs.get("initial_conditions") or {}),
            "numerical_method": kwargs.get("numerical_method") or "default",
            "solver_configuration_json": canonical_json(kwargs.get("solver_configuration") or {}),
            "parameter_snapshot_json": canonical_json(kwargs.get("parameter_snapshot") or {}),
            "seed": kwargs.get("seed"), "deterministic": 1 if kwargs.get("deterministic") else 0,
            "execution_json": canonical_json(kwargs.get("execution") or {}),
            "result_json": canonical_json(kwargs.get("result")) if kwargs.get("result") is not None else None,
            "result_reference": kwargs.get("result_reference"),
            "error_json": canonical_json(kwargs.get("error")) if kwargs.get("error") is not None else None,
            "provenance_json": canonical_json(kwargs.get("provenance") or {}),
            "schema_version": SCHEMA_VERSION, "software_version": __version__,
            "created_at": kwargs.get("created_at") or utc_now(), "updated_at": kwargs.get("updated_at") or utc_now(),
            "started_at": kwargs.get("started_at"), "completed_at": kwargs.get("completed_at"), "cancelled_at": kwargs.get("cancelled_at"),
        }
        existing = db.execute("SELECT 1 FROM experiments WHERE id = ?", (data["id"],)).fetchone()
        if existing:
            db.execute(
                """
                UPDATE experiments SET legacy_id=:legacy_id, project_id=:project_id, name=:name, description=:description,
                scientific_domain=:scientific_domain, model=:model, status=:status,
                input_parameters_json=:input_parameters_json, input_units_json=:input_units_json,
                initial_conditions_json=:initial_conditions_json, numerical_method=:numerical_method,
                solver_configuration_json=:solver_configuration_json, parameter_snapshot_json=:parameter_snapshot_json,
                seed=:seed, deterministic=:deterministic, execution_json=:execution_json, result_json=:result_json,
                result_reference=:result_reference, error_json=:error_json, provenance_json=:provenance_json,
                schema_version=:schema_version, software_version=:software_version, updated_at=:updated_at,
                started_at=:started_at, completed_at=:completed_at, cancelled_at=:cancelled_at
                WHERE id=:id
                """,
                data,
            )
        else:
            self._insert_experiment(db, data)

    def _project_to_dict(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": row["id"], "name": row["name"], "description": row.get("description") or "",
            "archived": bool(row.get("archived")), "created_at": row.get("created_at"), "updated_at": row.get("updated_at"),
            "schema_version": row.get("schema_version", SCHEMA_VERSION), "metadata": json.loads(row.get("metadata_json") or "{}"),
        }

    def _experiment_to_dict(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": row["id"], "legacy_id": row.get("legacy_id"), "project_id": row["project_id"],
            "name": row["name"], "description": row.get("description") or "",
            "scientific_domain": row.get("scientific_domain"), "model": row.get("model"), "status": row.get("status"),
            "input_parameters": json.loads(row.get("input_parameters_json") or "{}"),
            "input_units": json.loads(row.get("input_units_json") or "{}"),
            "initial_conditions": json.loads(row.get("initial_conditions_json") or "{}"),
            "numerical_method": row.get("numerical_method"),
            "solver_configuration": json.loads(row.get("solver_configuration_json") or "{}"),
            "parameter_snapshot": json.loads(row.get("parameter_snapshot_json") or "{}"),
            "seed": row.get("seed"), "deterministic": bool(row.get("deterministic")),
            "execution": json.loads(row.get("execution_json") or "{}"),
            "result": json.loads(row.get("result_json")) if row.get("result_json") else None,
            "result_reference": row.get("result_reference"),
            "error": json.loads(row.get("error_json")) if row.get("error_json") else None,
            "provenance": json.loads(row.get("provenance_json") or "{}"),
            "schema_version": row.get("schema_version", SCHEMA_VERSION),
            "software_version": row.get("software_version"),
            "created_at": row.get("created_at"), "updated_at": row.get("updated_at"),
            "started_at": row.get("started_at"), "completed_at": row.get("completed_at"), "cancelled_at": row.get("cancelled_at"),
        }
