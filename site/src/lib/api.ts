export type McuStatus = {
  state: number;
  counter: number;
  master: number;
  loop: number;
  amber?: number;
};

export type DeviceSnapshot = {
  state: "starting" | "ready" | "forwarded" | "unauthorized" | "absent" | "error";
  serial: string;
  api: string;
  detail: string;
  mcu: McuStatus | null;
};

export type LedgerRecord = {
  event: string;
  container?: string;
  at?: number;
  hash?: string;
  human?: string;
  reason?: string;
  "0g"?: Record<string, unknown>;
  mock?: boolean;
};

export type Evidence = {
  erase_us: number;
  wipe_us: number;
  bridge_p50_ms: number;
  bridge_p95_ms: number;
  tier1_p50_s: number;
  tier1_cost_usd_micro: number;
  deadline_ms: number;
};

export class ApiError extends Error {
  status: number;
  constructor(message: string, status = 0) {
    super(message);
    this.status = status;
  }
}

let base: string | null = null;

export function apiBase(): string {
  return base ?? "";
}

export async function resolveBase(): Promise<string> {
  if (base !== null) return base;
  const w = window as unknown as { ASH_API?: string };
  if (w.ASH_API) {
    base = w.ASH_API.replace(/\/$/, "");
    return base;
  }
  try {
    const r = await fetch("./config.json", { cache: "no-store" });
    if (r.ok) {
      const cfg = (await r.json()) as { apiBase?: string };
      if (cfg.apiBase) {
        base = cfg.apiBase.replace(/\/$/, "");
        return base;
      }
    }
  } catch {
    /* no config: fall back to the local API */
  }
  base = "http://127.0.0.1:8080";
  return base;
}

async function req<T>(path: string, init?: RequestInit, timeoutMs = 12000): Promise<T> {
  const b = await resolveBase();
  const ctl = new AbortController();
  const timer = setTimeout(() => ctl.abort(), timeoutMs);
  try {
    const res = await fetch(b + path, {
      ...init,
      signal: ctl.signal,
      headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    });
    const text = await res.text();
    let data: unknown = null;
    try {
      data = text ? JSON.parse(text) : null;
    } catch {
      throw new ApiError(`non-JSON response (${res.status})`, res.status);
    }
    if (!res.ok) {
      const msg =
        (data as { error?: string } | null)?.error ?? `request failed (${res.status})`;
      throw new ApiError(msg, res.status);
    }
    return data as T;
  } catch (e) {
    if (e instanceof ApiError) throw e;
    if ((e as Error).name === "AbortError") throw new ApiError("request timed out");
    throw new ApiError((e as Error).message || "network error");
  } finally {
    clearTimeout(timer);
  }
}

export const api = {
  device: () => req<DeviceSnapshot>("/device", { cache: "no-store" } as RequestInit, 5000),
  status: () => req<McuStatus>("/status", { cache: "no-store" } as RequestInit, 5000),
  ledger: () => req<{ records: LedgerRecord[] }>("/ledger", { cache: "no-store" } as RequestInit, 6000),
  evidence: () => req<Evidence>("/evidence", { cache: "no-store" } as RequestInit, 6000),
  seal: (container: string, owner = "") =>
    req<{ ok: boolean; record: LedgerRecord }>("/seal", {
      method: "POST",
      body: JSON.stringify({ container, owner }),
    }),
  unseal: (container: string, proof: string | Record<string, unknown>) =>
    req<{ ok: boolean; payload: string; record: LedgerRecord }>(
      "/unseal",
      { method: "POST", body: JSON.stringify({ container, proof }) },
      30000,
    ),
  flex: () => req<{ open: string; close: string }>("/flex", { method: "POST", body: "{}" }, 15000),
  sim: (closed: 0 | 1) =>
    req<{ mcu: string }>("/sim", { method: "POST", body: JSON.stringify({ closed }) }, 8000),
  reprovision: () =>
    req<{ mcu: string }>("/reprovision", { method: "POST", body: "{}" }, 8000),
  worldConfig: () =>
    req<{ app_id: string; rp_id: string; action: string; has_key: boolean }>("/world/config", {
      cache: "no-store",
    } as RequestInit, 5000),
  walletNonce: (chain: "evm" | "hedera", account: string) =>
    req<{ message: string; nonce: string }>(
      `/wallet/nonce?chain=${chain}&account=${encodeURIComponent(account)}`,
      { cache: "no-store" } as RequestInit,
      6000,
    ),
  walletVerify: (chain: "evm" | "hedera", account: string, signature: string) =>
    req<{ ok: boolean; account: string; chain: string }>("/wallet/verify", {
      method: "POST",
      body: JSON.stringify({ chain, account, signature }),
    }),
};
