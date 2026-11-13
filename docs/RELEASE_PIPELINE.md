# Windows release pipeline

`.github/workflows/windows-release.yml` defines a Windows runner pipeline. It installs the pinned Python project, packages the API into a PyInstaller one-file executable, installs/builds the React frontend, installs Tauri CLI 2, builds MSI and NSIS bundles, then checks that installer files exist and prints SHA-256 hashes.

The workflow has been authored but **has not been executed** in this environment. It is not evidence that a Windows installer exists. Code signing is not configured. A maintainer must run the workflow on GitHub Actions and inspect the resulting artifacts before publishing.
