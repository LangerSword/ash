use serde::{Deserialize, Serialize};
use std::path::PathBuf;

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Config {
    #[serde(default)]
    pub serial: String,
    #[serde(default = "default_api_port")]
    pub api_port: u16,
    #[serde(default)]
    pub legend_seen: bool,
    #[serde(default)]
    pub intro_seen: bool,
    #[serde(default)]
    pub world_sub: String,
    #[serde(default)]
    pub last_ledger_hash: String,
}

fn default_api_port() -> u16 {
    8080
}

impl Default for Config {
    fn default() -> Self {
        Self {
            serial: String::new(),
            api_port: default_api_port(),
            legend_seen: false,
            intro_seen: false,
            world_sub: String::new(),
            last_ledger_hash: String::new(),
        }
    }
}

pub fn home() -> PathBuf {
    std::env::var_os("HOME")
        .map(PathBuf::from)
        .unwrap_or_else(|| PathBuf::from("/tmp"))
}

fn xdg(env: &str, fallback: &str) -> PathBuf {
    std::env::var_os(env)
        .map(PathBuf::from)
        .unwrap_or_else(|| home().join(fallback))
}

pub fn config_path() -> PathBuf {
    xdg("XDG_CONFIG_HOME", ".config").join("ash").join("config.json")
}

pub fn state_dir() -> PathBuf {
    xdg("XDG_STATE_HOME", ".local/state").join("ash")
}

pub fn data_dir() -> PathBuf {
    xdg("XDG_DATA_HOME", ".local/share").join("ash")
}

pub fn log_path() -> PathBuf {
    state_dir().join("app.log")
}

pub fn load() -> Config {
    let path = config_path();
    match std::fs::read_to_string(&path) {
        Ok(text) => serde_json::from_str(&text).unwrap_or_default(),
        Err(_) => Config::default(),
    }
}

pub fn save(cfg: &Config) -> std::io::Result<()> {
    let path = config_path();
    if let Some(parent) = path.parent() {
        std::fs::create_dir_all(parent)?;
    }
    let text = serde_json::to_string_pretty(cfg).unwrap_or_default();
    std::fs::write(path, text)
}

pub fn merge(cfg: &mut Config, patch: &serde_json::Value) {
    if let Some(v) = patch.get("serial").and_then(|v| v.as_str()) {
        cfg.serial = v.to_string();
    }
    if let Some(v) = patch.get("api_port").and_then(|v| v.as_u64()) {
        cfg.api_port = v as u16;
    }
    if let Some(v) = patch.get("legend_seen").and_then(|v| v.as_bool()) {
        cfg.legend_seen = v;
    }
    if let Some(v) = patch.get("intro_seen").and_then(|v| v.as_bool()) {
        cfg.intro_seen = v;
    }
    if let Some(v) = patch.get("world_sub").and_then(|v| v.as_str()) {
        cfg.world_sub = v.to_string();
    }
    if let Some(v) = patch.get("last_ledger_hash").and_then(|v| v.as_str()) {
        cfg.last_ledger_hash = v.to_string();
    }
}

/// Append one line to ~/.local/state/ash/app.log, creating the directory if needed.
pub fn log_line(line: &str) {
    let path = log_path();
    if let Some(parent) = path.parent() {
        let _ = std::fs::create_dir_all(parent);
    }
    let stamp = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0);
    if let Ok(mut f) = std::fs::OpenOptions::new().create(true).append(true).open(path) {
        use std::io::Write;
        let _ = writeln!(f, "[{stamp}] {line}");
    }
}
