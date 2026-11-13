# Build guide

## Python backend

Python 3.11+ is required. From the project root:

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pytest -q
quantumforge-api
```

## React frontend

```bash
cd frontend
npm install
npm run build
```

## Tauri desktop source

Install the Tauri 2 system prerequisites, Rust stable/Cargo, and the platform WebView dependencies. Then:

```bash
cd src-tauri
cargo tauri build
```

The current shell expects a Python interpreter and installed project dependencies at runtime. A self-contained commercial Windows installer requires a bundled backend runtime and must be built and tested on a Windows CI runner. No MSI/NSIS artifact is included in this source package.
