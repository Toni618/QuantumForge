# Architecture — QuantumForge 0.3.0 (Phase 1)

## Overview
QuantumForge is a local-first scientific computing workstation: Python scientific engines + FastAPI local API + React/TypeScript/Vite frontend + optional Tauri desktop shell. Phase 1 adds a project/experiment management and execution foundation while preserving 0.2.x scientific modules and API compatibility.

## Layers
- **Scientific core (`quantumforge/`)**: pure/computational modules, independent of UI.
  - `core/`, `math/`: safe expressions, units, numerical solvers.
  - `quantum/`: 1D stationary Schrödinger, state-vector circuits, spin/density diagnostics, Lindblad routines (as implemented/tested).
  - `qft/`: free real scalar field on 1D periodic lattice.
  - `relativity/`: SR transforms, symbolic metric geometry, Schwarzschild parameters/geodesics.
- **Application services (`quantumforge/application/`)**
  - `jobs.py`: in-process background job manager (`ThreadPoolExecutor`) for registered computations with progress callbacks, cooperative cancellation, timeout resource limits, and status/error tracking.
- **Persistence (`quantumforge/storage/`)**
  - `db.py`: `Database` (SQLite, WAL, FK, busy timeout, transactional migrations) and `ExperimentStore`.
  - Schema v1: `schema_migrations`, `projects`, `experiments`, `jobs`, `computation_cache` (reserved). Legacy 0.2.x `experiments` table migrated to `experiments_legacy` and rows imported into a default project with preserved legacy IDs/config/results.
  - Features: project CRUD/archive/duplicate, versioned experiment records (parameters/units/ICs/method/solver config, seed/determinism, parameter snapshot, execution/status/runtime history, results/errors, provenance, software/schema versions, timestamps), project JSON export/import (format `quantumforge.project-export` v1), DB backup/restore.
  - `experiments.py`: compatibility wrapper exposing legacy `ExperimentStore.save/get` contract.
- **API (`quantumforge/api/app.py`)**: FastAPI app, loopback CORS for local/Tauri dev.
  - Preserved scientific endpoints: `/health`, math, quantum, QFT, relativity/black-hole, legacy `/experiments` (POST/GET by legacy/content ID).
  - Phase 1 management endpoints: `/projects` CRUD/list/detail, duplicate, export, import; `/experiments` list/detail/create/run/cancel; `/jobs` list/get; `/admin/backup`, `/admin/restore`.
  - Registered executable computation models for background runs: `math.root`, `math.integrate`, `quantum.schrodinger.harmonic`, `quantum.circuit`, `quantum.density.bell`, `qft.free_scalar_lattice`, `relativity.schwarzschild`, `relativity.schwarzschild.geometry`, `relativity.schwarzschild.geodesic`.
- **Frontend (`frontend/`)**: React 18 + TypeScript + Vite SPA (`src/ui/App.tsx`) with management pages (Workspace, Projects, Project details, Experiment details, Experiment history) and preserved scientific lab/validation panels; communicates with local API.
- **Desktop (`src-tauri/`)**: Tauri 2 shell supervising local backend process (bundled exe or Python fallback). Packaging **not verified** in this environment.

## Data & reproducibility model
- Project: id, name, description, archived flag, schema/metadata, timestamps.
- Experiment: unique id (+optional legacy_id), project link, name/description/domain/model, status lifecycle (`pending|queued|running|completed|failed|cancelled`), input parameters & units, initial conditions, numerical method & solver configuration, parameter snapshot, seed/deterministic flags, execution/progress/runtime/status history, result/result reference, structured error, provenance (includes software info), schema/software versions, timestamps.
- Import/export uses explicit format/version; migrations are transactional and forward-applied on open/restore.

## Execution model
- Synchronous scientific endpoints remain for direct lab calls.
- Managed experiment runs are submitted to the background job manager; status/progress persisted to experiment records; cancellation is cooperative (checked between/within registered steps where supported) and timeout-enforced via resource limits.

## Constraints & limitations
- Single-node local SQLite; no multi-user concurrency guarantees beyond WAL/busy timeout.
- Background jobs are in-process threads (suitable for current workloads; long blocking native calls may limit cancellation granularity).
- Desktop installers/Rust builds not verified in current environment. No independent scientific/security audit.
