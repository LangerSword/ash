import { invoke } from "@tauri-apps/api/core";
import type { RuntimeInfo } from "./types";

export const inTauri = typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;

const DEV_RUNTIME: RuntimeInfo = {
  device: {
    state: "ready",
    serial: "3017640407",
    detail: "browser preview",
    board_base: "http://127.0.0.1:8081",
    at: Math.floor(Date.now() / 1000),
  },
  service: { mode: "attached", base: "http://127.0.0.1:8080", detail: "browser preview", mock: false },
  config: {
    serial: "",
    api_port: 8080,
    legend_seen: false,
    intro_seen: false,
    world_sub: "",
    last_ledger_hash: "",
  },
  log_path: "~/.local/state/ash/app.log",
  version: "0.1.0-dev",
  udev_ok: true,
};

export async function cmd<T>(name: string, args?: Record<string, unknown>): Promise<T> {
  if (!inTauri) {
    if (name === "runtime_info") return DEV_RUNTIME as T;
    if (name === "append_log") return undefined as T;
    if (name === "save_runtime") return undefined as T;
    throw new Error("not running inside the desktop shell");
  }
  return invoke<T>(name, args);
}
