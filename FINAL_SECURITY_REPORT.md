# FINAL_SECURITY_REPORT.md

Date: 2026-11-11 | Status: **self-assessed engineering notes — NOT an independent security audit**

## Implemented / present
- **Safe math parsing:** restricted AST-based expression parser (`quantumforge.core.expressions`) for user math/custom potentials; no unrestricted `eval`.
- **API posture:** FastAPI bound to loopback in run config; CORS restricted to Tauri localhost and local dev origins in app config.
- **Input validation:** Pydantic request models/field constraints for many endpoints; domain checks in solvers (grid sizes, parameter bounds, matrix shapes, physical constraints e.g. positivity/mass/subluminal where applicable).
- **Storage:** SQLite with parameterized queries, transactions, FK/WAL; project import format/version checks; backup/restore path handling basic.
- **Dependencies:** pinned core versions in `pyproject.toml` (0.2.1/0.3 baseline pins retained) with dev extras declared.

## Gaps / not verified
- **No dependency vulnerability scan executed** (no `pip-audit`/SCA run in env).
- **No secure secret storage implementation** for AI/provider keys (AI assistant not implemented).
- **No comprehensive local IPC/auth hardening review** for Tauri bridge; desktop runtime unverified.
- **Import/export/path hardening** not exhaustively threat-modeled (e.g. large payload/resource exhaustion, archive/path traversal beyond basic handling).
- **Resource limits:** partial (state-vector memory cap, bounded grids/samples/shots, job timeout support) but not a complete sandbox/quotas system.
- **Logging/error sanitization:** basic exception messages returned; no formal redaction policy.
- **No penetration testing, no third-party audit, no signed update mechanism verified.**

## Recommendations (release blockers for production claims)
1. Run SCA (pip-audit/npm audit) and remediate; pin/update via lockfiles.
2. Add strict schema/size validation and quotas for imports/uploads and long-running jobs.
3. Implement secure credential storage and explicit consent flows before any AI assistant/network features.
4. Harden Tauri IPC/command allowlists and packaged backend lifecycle; verify on target OSes.
5. Commission independent security review before any production/commercial claim.
