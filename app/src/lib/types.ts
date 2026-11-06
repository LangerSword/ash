export type McuStatus = {
  state: number;
  counter: number;
  master: number;
  loop: number;
  amber?: number;
};

export type Mode = "armed" | "amber" | "tampered" | "unsealed" | "offline" | "wipe";

export type DeviceState =
  | "starting"
  | "absent"
  | "unauthorized"
  | "forwarded"
  | "ready"
  | "external"
  | "error";

export type DeviceSnapshot = {
  state: DeviceState;
  serial: string;
  detail: string;
  board_base: string;
  at: number;
};

export type ServiceInfo = {
  mode: "starting" | "attached" | "spawned" | "unavailable";
  base: string;
  detail: string;
  mock: boolean;
};

export type Config = {
  serial: string;
  api_port: number;
  legend_seen: boolean;
  intro_seen: boolean;
  world_sub: string;
  last_ledger_hash: string;
};

export type RuntimeInfo = {
  device: DeviceSnapshot;
  service: ServiceInfo;
  config: Config;
  log_path: string;
  version: string;
  udev_ok: boolean;
};

export type LedgerRecord = {
  event: string;
  container?: string;
  at?: number;
  hash?: string;
  human?: string;
  reason?: string;
  note?: string;
  owner?: string;
  payload_sha256?: string;
  mock?: boolean;
  "0g"?: Record<string, unknown>;
  meta?: Record<string, unknown>;
};

export type Evidence = {
  erase_us: number;
  wipe_us: number;
  bridge_p50_ms: number;
  bridge_p95_ms: number;
  tier1_p50_s: number;
  tier1_cost_usd_micro: number;
  deadline_ms: number;
  mock?: boolean;
  world?: string;
};

export type WorldConfig = {
  app_id: string;
  rp_id: string;
  action: string;
  has_key: boolean;
};

export type WorldSignature = {
  sig: string;
  nonce: string;
  created_at: number;
  expires_at: number;
};

export type X402Accept = {
  scheme?: string;
  network?: string;
  amount?: string;
  asset?: string;
  payTo?: string;
  extra?: Record<string, unknown>;
};

export type X402Challenge = {
  x402Version?: number;
  error?: string;
  accepts?: X402Accept[];
};
