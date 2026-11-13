"""Background computation jobs with progress, cancellation, and status tracking."""
from __future__ import annotations

import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable

from quantumforge.storage.db import ExperimentStore, canonical_json, utc_now

# Supported computation models map to callables: (params, progress_cb, cancel_event) -> result
ComputeFn = Callable[[dict[str, Any], Callable[[float, str], None], threading.Event], Any]


class JobManager:
    def __init__(self, store: ExperimentStore, max_workers: int = 2):
        self.store = store
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="qf-job")
        self._jobs: dict[str, dict[str, Any]] = {}
        self._lock = threading.RLock()

    def list_jobs(self) -> list[dict[str, Any]]:
        with self._lock:
            return [self._public(j) for j in self._jobs.values()]

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        with self._lock:
            j = self._jobs.get(job_id)
            return self._public(j) if j else None

    def submit(self, experiment_id: str, model: str, params: dict[str, Any], compute: ComputeFn, resource_limits: dict | None = None) -> dict[str, Any]:
        limits = resource_limits or {}
        job_id = experiment_id
        cancel_event = threading.Event()
        record = {
            "id": job_id,
            "experiment_id": experiment_id,
            "model": model,
            "status": "queued",
            "progress": 0.0,
            "message": "queued",
            "cancel_requested": False,
            "created_at": utc_now(),
            "started_at": None,
            "finished_at": None,
            "error": None,
            "_cancel_event": cancel_event,
        }
        with self._lock:
            self._jobs[job_id] = record
        self.store.update_experiment_status(experiment_id, "queued", "queued", progress=0.0, execution_patch={"job_id": job_id, "resource_limits": limits})
        self.executor.submit(self._run, job_id, model, params, compute, limits)
        return self._public(record)

    def cancel(self, job_id: str) -> bool:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False
            if job["status"] in {"completed", "failed", "cancelled"}:
                return False
            job["cancel_requested"] = True
            job["_cancel_event"].set()
            job["message"] = "cancellation requested"
        self.store.update_experiment_status(job_id, "running", "cancellation requested", progress=job.get("progress"))
        return True

    def _run(self, job_id: str, model: str, params: dict[str, Any], compute: ComputeFn, limits: dict[str, Any]) -> None:
        started = time.time()
        timeout_s = limits.get("timeout_seconds")
        try:
            with self._lock:
                job = self._jobs[job_id]
                job["status"] = "running"
                job["started_at"] = utc_now()
                job["message"] = "running"
            self.store.update_experiment_status(job_id, "running", "running", progress=0.0, execution_patch={"started_at_monotonic": started})

            def progress_cb(p: float, msg: str = "") -> None:
                p = max(0.0, min(1.0, float(p)))
                with self._lock:
                    job = self._jobs.get(job_id)
                    job["progress"] = p
                    if msg:
                        job["message"] = msg
                    if timeout_s and (time.time() - started) > float(timeout_s):
                        job["_cancel_event"].set()
                        raise TimeoutError(f"Resource limit exceeded: timeout_seconds={timeout_s}")
                    if job["_cancel_event"].is_set():
                        raise CancelledError("Cancelled")
                self.store.update_experiment_status(job_id, "running", msg or "running", progress=p)

            cancel_event = self._jobs[job_id]["_cancel_event"]
            result = compute(params, progress_cb, cancel_event)
            runtime = {"duration_seconds": round(time.time() - started, 6)}
            with self._lock:
                job = self._jobs[job_id]
                if job["_cancel_event"].is_set() or job.get("cancel_requested"):
                    raise CancelledError("Cancelled")
                job["status"] = "completed"
                job["progress"] = 1.0
                job["message"] = "completed"
                job["finished_at"] = utc_now()
            self.store.update_experiment_status(job_id, "completed", "completed", result=result, progress=1.0, execution_patch={"runtime": runtime})
        except CancelledError:
            with self._lock:
                job = self._jobs[job_id]
                job["status"] = "cancelled"
                job["message"] = "cancelled"
                job["finished_at"] = utc_now()
            self.store.update_experiment_status(job_id, "cancelled", "cancelled by user", error={"type": "CancelledError", "message": "cancelled"}, progress=job.get("progress", 0.0), execution_patch={"runtime": {"duration_seconds": round(time.time() - started, 6)}})
        except Exception as e:
            err = {"type": type(e).__name__, "message": str(e), "traceback": traceback.format_exc(limit=8)}
            with self._lock:
                job = self._jobs[job_id]
                job["status"] = "failed"
                job["message"] = str(e)
                job["finished_at"] = utc_now()
                job["error"] = err
            self.store.update_experiment_status(job_id, "failed", str(e), error=err, progress=job.get("progress", 0.0), execution_patch={"runtime": {"duration_seconds": round(time.time() - started, 6)}})

    @staticmethod
    def _public(job: dict[str, Any]) -> dict[str, Any]:
        return {k: v for k, v in job.items() if not k.startswith("_")}


class CancelledError(Exception):
    pass
