#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]
use std::{process::{Child, Command, Stdio}, sync::Mutex};
use tauri::{Manager, RunEvent};
struct BackendProcess(Mutex<Option<Child>>);
fn main() {
    let mut app = tauri::Builder::default().setup(|app| {
        let resource = app.path().resource_dir()?;
        let packaged_backend = resource.join("backend");
        let backend_root = if packaged_backend.join("quantumforge").is_dir() || packaged_backend.join("QuantumForgeBackend.exe").is_file() || packaged_backend.join("QuantumForgeBackend").is_file() {
            packaged_backend
        } else {
            std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("..")
        };
        let bundled = backend_root.join(if cfg!(windows) { "QuantumForgeBackend.exe" } else { "QuantumForgeBackend" });
        let mut cmd = if bundled.is_file() {
            Command::new(bundled)
        } else {
            let python_path = std::env::var("QUANTUMFORGE_PYTHON").unwrap_or_else(|_| if cfg!(windows) { "python".into() } else { "python3".into() });
            let mut fallback = Command::new(python_path);
            fallback.arg("-m").arg("quantumforge.api.app").current_dir(&backend_root).env("PYTHONPATH", &backend_root);
            fallback
        };
        let app_data = app.path().app_data_dir()?;
        std::fs::create_dir_all(&app_data)?;
        cmd.env("QUANTUMFORGE_PORT", "8765")
            .env("QUANTUMFORGE_DB", app_data.join("quantumforge.sqlite3"))
            .stdin(Stdio::null()).stdout(Stdio::null()).stderr(Stdio::null());
        let child = cmd.spawn().map_err(|e| format!("Could not start local Python backend: {e}"))?;
        app.manage(BackendProcess(Mutex::new(Some(child))));
        Ok(())
    }).build(tauri::generate_context!()).expect("error while building QuantumForge");
    app.run(|handle, event| {
        if let RunEvent::Exit = event {
            if let Some(state) = handle.try_state::<BackendProcess>() {
                if let Ok(mut guard) = state.0.lock() {
                    if let Some(mut child) = guard.take() { let _ = child.kill(); let _ = child.wait(); }
                }
            }
        }
    });
}
