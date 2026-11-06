mod config;
mod device;
mod service;

use serde::Serialize;
use std::sync::Mutex;
use tauri::{Manager, State};

pub struct AppState {
    pub cfg: Mutex<config::Config>,
    pub device: Mutex<device::DeviceSnapshot>,
    pub service: Mutex<service::ServiceInfo>,
    pub child: Mutex<Option<std::process::Child>>,
    pub board_port: u16,
}

#[derive(Serialize)]
struct RuntimeInfo {
    device: device::DeviceSnapshot,
    service: service::ServiceInfo,
    config: config::Config,
    log_path: String,
    version: String,
    udev_ok: bool,
}

#[tauri::command]
fn runtime_info(state: State<'_, AppState>) -> RuntimeInfo {
    let dev = state.device.lock().map(|d| d.clone()).unwrap_or_default();
    let svc = state.service.lock().map(|s| s.clone()).unwrap_or_default();
    let cfg = state.cfg.lock().map(|c| c.clone()).unwrap_or_default();
    RuntimeInfo {
        device: dev,
        service: svc,
        config: cfg,
        log_path: config::log_path().display().to_string(),
        version: env!("CARGO_PKG_VERSION").to_string(),
        udev_ok: device::udev_present(),
    }
}

#[tauri::command]
fn start_board_app(state: State<'_, AppState>) -> Result<String, String> {
    let serial = state
        .device
        .lock()
        .map(|d| d.serial.clone())
        .unwrap_or_default();
    let out = device::start_board_app(&serial)?;
    config::log_line(&format!("board app: {out}"));
    Ok(out)
}

#[tauri::command]
fn install_udev() -> Result<String, String> {
    device::install_udev()
}

#[tauri::command]
fn save_config(state: State<'_, AppState>, patch: serde_json::Value) -> Result<(), String> {
    let mut cfg = state.cfg.lock().map_err(|e| e.to_string())?;
    config::merge(&mut cfg, &patch);
    config::save(&cfg).map_err(|e| format!("could not write config: {e}"))?;
    Ok(())
}

#[tauri::command]
fn append_log(line: String) {
    config::log_line(&line);
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let cfg = config::load();
    let board_port = device::choose_port(&cfg.serial);
    config::log_line(&format!(
        "app: start v{} board_port={board_port}",
        env!("CARGO_PKG_VERSION")
    ));

    let state = AppState {
        cfg: Mutex::new(cfg.clone()),
        device: Mutex::new(device::DeviceSnapshot::default()),
        service: Mutex::new(service::ServiceInfo::default()),
        child: Mutex::new(None),
        board_port,
    };

    let app = tauri::Builder::default()
        .manage(state)
        .invoke_handler(tauri::generate_handler![
            runtime_info,
            start_board_app,
            install_udev,
            save_config,
            append_log
        ])
        .setup(move |app| {
            let handle = app.handle().clone();
            let serial = cfg.serial.clone();
            std::thread::spawn(move || {
                let state = handle.state::<AppState>();
                loop {
                    let snap = device::poll(&serial, state.board_port);
                    if let Ok(mut slot) = state.device.lock() {
                        *slot = snap;
                    }
                    std::thread::sleep(std::time::Duration::from_secs(2));
                }
            });

            let handle = app.handle().clone();
            let serial = cfg.serial.clone();
            std::thread::spawn(move || {
                let exe = std::env::current_exe().unwrap_or_default();
                let dir = exe
                    .parent()
                    .map(|p| p.to_path_buf())
                    .unwrap_or_else(std::env::temp_dir);
                let (info, child) = service::ensure(board_port, &serial, &dir);
                let state = handle.state::<AppState>();
                {
                    let mut slot = state.service.lock().expect("service lock");
                    *slot = info;
                }
                {
                    let mut slot = state.child.lock().expect("child lock");
                    *slot = child;
                }
                config::log_line("service: ready");
            });
            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("failed to build Ash");

    app.run(|handle, event| {
        if matches!(event, tauri::RunEvent::Exit) {
            if let Ok(mut slot) = handle.state::<AppState>().child.lock() {
                if let Some(mut child) = slot.take() {
                    let _ = child.kill();
                    let _ = child.wait();
                }
            }
            config::log_line("app: exit");
        }
    });
}
