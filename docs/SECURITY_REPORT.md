# Security report — engineering review, not an audit

## Controls present
- Equation expressions are parsed through a restricted SymPy expression parser; arbitrary Python evaluation is not exposed as an API operation.
- API binds to loopback (`127.0.0.1`) only.
- CORS allowlist is limited to Tauri origins and local Vite development origins.
- Pydantic validates request shapes and bounded grid/site/sample counts.
- Tauri process is launched as a child and terminated on normal application exit.

## Remaining risks
- No authentication token is currently required on loopback API requests; another local process could call the API.
- No independent penetration test or dependency vulnerability audit was conducted.
- Python runtime/dependency bundling and signed installer supply-chain controls remain incomplete.
- Resource limits are endpoint-specific and not a general per-user CPU/memory quota.

Severity: no independent severity-rated finding process has been performed. This report is an internal engineering note only.
