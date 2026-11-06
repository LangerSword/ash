//! The device link: adb detection, the forward, the board's own /status.
//! Owned by Rust so the device screen still works when the Python service is down.

use serde::Serialize;
use std::process::Command;
use std::time::{Duration, SystemTime, UNIX_EPOCH};

use crate::config;

pub const APP_PATH: &str = "/home/arduino/ArduinoApps/ash-fw";
pub const UDEV_PATH: &str = "/etc/udev/rules.d/99-ash-unoq.rules";
const UDEV_RULE: &str = include_str!("../resources/99-ash-unoq.rules");

#[derive(Clone, Debug, Serialize)]
pub struct DeviceSnapshot {
    pub state: String,
    pub serial: String,
    pub detail: String,
    pub board_base: String,
    pub at: u64,
}

impl Default for DeviceSnapshot {
    fn default() -> Self {
        Self {
            state: "starting".into(),
            serial: String::new(),
            detail: String::new(),
            board_base: String::new(),
            at: epoch(),
        }
    }
}

fn epoch() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0)
}

fn adb(args: &[&str]) -> Result<String, String> {
    let out = Command::new("adb")
        .args(args)
        .output()
        .map_err(|e| format!("adb is not available on PATH: {e}"))?;
    if !out.status.success() {
        let err = String::from_utf8_lossy(&out.stderr).trim().to_string();
        return Err(if err.is_empty() {
            format!("adb {} failed", args.join(" "))
        } else {
            err
        });
    }
    Ok(String::from_utf8_lossy(&out.stdout).to_string())
}

fn devices() -> Result<Vec<(String, String)>, String> {
    let out = adb(&["devices"])?;
    let mut rows = Vec::new();
    for line in out.lines().skip(1) {
        let mut parts = line.split('\t');
        let serial = parts.next().unwrap_or("").trim().to_string();
        let status = parts.next().unwrap_or("").trim().to_string();
        if !serial.is_empty() && !status.is_empty() {
            rows.push((serial, status));
        }
    }
    Ok(rows)
}

/// Reuse an existing forward to tcp:8080 for this serial, else bind the preferred port.
pub fn ensure_forward(serial: &str, preferred: u16) -> Result<u16, String> {
    if let Ok(list) = adb(&["forward", "--list"]) {
        for line in list.lines() {
            let cols: Vec<&str> = line.split_whitespace().collect();
            if cols.len() >= 3 && cols[0] == serial && cols[2] == "tcp:8080" {
                if let Some(port) = cols[1].strip_prefix("tcp:").and_then(|p| p.parse::<u16>().ok())
                {
                    return Ok(port);
                }
            }
        }
    }
    let mut last = String::new();
    for port in [preferred, 8092, 8093, 8094, 8095, 8096, 8097, 8098, 8099] {
        let local = format!("tcp:{port}");
        match adb(&["-s", serial, "forward", &local, "tcp:8080"]) {
            Ok(_) => return Ok(port),
            Err(e) => last = e,
        }
    }
    Err(format!("could not forward a port to the board: {last}"))
}

pub fn probe(base: &str) -> Option<serde_json::Value> {
    let url = format!("{base}/status");
    let resp = ureq::get(&url).timeout(Duration::from_millis(1500)).call().ok()?;
    let text = resp.into_string().ok()?;
    let v: serde_json::Value = serde_json::from_str(&text).ok()?;
    if v.get("mcu").is_some() || v.get("state").is_some() {
        Some(v)
    } else {
        None
    }
}

/// Pick the local port the app will use for the board forward, before any board exists.
pub fn choose_port(preferred_serial: &str) -> u16 {
    if let Ok(rows) = devices() {
        let chosen = rows
            .iter()
            .find(|(s, _)| !preferred_serial.is_empty() && s == preferred_serial)
            .or_else(|| rows.first());
        if let Some((serial, status)) = chosen {
            if status == "device" {
                if let Ok(port) = ensure_forward(serial, 8081) {
                    return port;
                }
            }
        }
    }
    8081
}

pub fn poll(preferred_serial: &str, port: u16) -> DeviceSnapshot {
    let mut snap = DeviceSnapshot {
        at: epoch(),
        ..Default::default()
    };

    let rows = match devices() {
        Ok(rows) => rows,
        Err(e) => {
            snap.state = "error".into();
            snap.detail = e;
            return snap;
        }
    };
    if rows.is_empty() {
        snap.state = "absent".into();
        snap.detail = "no adb device".into();
        return snap;
    }

    let chosen = rows
        .iter()
        .find(|(s, _)| !preferred_serial.is_empty() && s == preferred_serial)
        .or_else(|| rows.first())
        .cloned()
        .unwrap_or_default();
    let (serial, status) = chosen;
    snap.serial = serial.clone();

    if status != "device" {
        snap.state = "unauthorized".into();
        snap.detail = status;
        return snap;
    }

    if rows.len() > 1 && (preferred_serial.is_empty() || preferred_serial != serial) {
        snap.detail = format!("{} boards connected; using {serial}", rows.len());
    }

    let local = match ensure_forward(&serial, port) {
        Ok(p) => p,
        Err(e) => {
            snap.state = "error".into();
            snap.detail = e;
            return snap;
        }
    };
    let base = format!("http://127.0.0.1:{local}");
    snap.board_base = base.clone();

    match probe(&base) {
        Some(_) => snap.state = "ready".into(),
        None => {
            snap.state = "forwarded".into();
            if snap.detail.is_empty() {
                snap.detail = "the board's app is not answering".into();
            }
        }
    }
    snap
}

pub fn start_board_app(serial: &str) -> Result<String, String> {
    if serial.is_empty() {
        return Err("no board serial: connect the UNO Q first".into());
    }
    let out = adb(&["-s", serial, "shell", "arduino-app-cli", "app", "start", APP_PATH])
        .map_err(|e| format!("start board app failed: {e}"))?;
    let text = out.trim();
    Ok(if text.is_empty() {
        "board app start requested".to_string()
    } else {
        text.lines().last().unwrap_or(text).to_string()
    })
}

pub fn udev_present() -> bool {
    std::path::Path::new(UDEV_PATH).exists()
}

pub fn install_udev() -> Result<String, String> {
    if udev_present() {
        return Ok(format!("{UDEV_PATH} already present"));
    }
    if Command::new("pkexec").arg("--version").output().is_err() {
        return Err(format!(
            "pkexec is not available. Add the rule by hand:\n{UDEV_RULE}\n  sudo install -m 644 <file> {UDEV_PATH}"
        ));
    }
    let tmp = std::env::temp_dir().join("99-ash-unoq.rules");
    std::fs::write(&tmp, UDEV_RULE).map_err(|e| format!("could not stage the rule: {e}"))?;

    let steps: [(&str, Vec<&str>); 3] = [
        ("install", vec!["-m", "644", tmp.to_str().unwrap_or(""), UDEV_PATH]),
        ("udevadm", vec!["control", "--reload-rules"]),
        ("udevadm", vec!["trigger"]),
    ];
    for (cmd, args) in steps {
        let out = Command::new("pkexec")
            .arg(cmd)
            .args(&args)
            .output()
            .map_err(|e| format!("pkexec {cmd} failed: {e}"))?;
        if !out.status.success() {
            let err = String::from_utf8_lossy(&out.stderr).trim().to_string();
            return Err(if err.is_empty() {
                format!("pkexec {cmd} was refused or cancelled")
            } else {
                err
            });
        }
    }
    config::log_line("udev: 99-ash-unoq.rules installed");
    Ok(format!("{UDEV_PATH} installed; replug the board once"))
}
