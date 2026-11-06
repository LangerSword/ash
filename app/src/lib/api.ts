import type {
  Evidence,
  LedgerRecord,
  McuStatus,
  WorldConfig,
  WorldSignature,
  X402Challenge,
} from "./types";

export class ApiError extends Error {
  status: number;
  body: unknown;
  constructor(message: string, status = 0, body: unknown = null) {
    super(message);
    this.status = status;
    this.body = body;
  }
}

let base = "";

export function setBase(url: string) {
  base = url.replace(/\/$/, "");
}

export function apiBase(): string {
  return base;
}

async function req<T>(path: string, init?: RequestInit, timeoutMs = 12000): Promise<T> {
  if (!base) throw new ApiError("local service is not available");
  const ctl = new AbortController();
  const timer = setTimeout(() => ctl.abort(), timeoutMs);
  try {
    const res = await fetch(base + path, {
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
      const msg = (data as { error?: string } | null)?.error ?? `request failed (${res.status})`;
      throw new ApiError(msg, res.status, data);
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
  status: () => req<McuStatus>("/status", { cache: "no-store" } as RequestInit, 5000),
  ledger: () =>
    req<{ records: LedgerRecord[] }>("/ledger", { cache: "no-store" } as RequestInit, 6000),
  verify: () =>
    req<{ ok: boolean; records: number; detail: string }>("/ledger/verify", undefined, 8000),
  evidence: () => req<Evidence>("/evidence", { cache: "no-store" } as RequestInit, 6000),
  seal: (container: string, owner: string) =>
    req<{ ok: boolean; record: LedgerRecord }>(
      "/seal",
      { method: "POST", body: JSON.stringify({ container, owner }) },
      20000,
    ),
  unseal: (container: string, proof: unknown) =>
    req<{ ok: boolean; payload: string; record: LedgerRecord }>(
      "/unseal",
      { method: "POST", body: JSON.stringify({ container, proof }) },
      45000,
    ),
  flex: () => req<{ open: string; close: string }>("/flex", { method: "POST", body: "{}" }, 20000),
  sim: (closed: 0 | 1) =>
    req<{ mcu: string }>("/sim", { method: "POST", body: JSON.stringify({ closed }) }, 8000),
  reprovision: () => req<{ mcu: string }>("/reprovision", { method: "POST", body: "{}" }, 8000),
  frame: (frames: string[], fps: number) =>
    req<{ frames: number; fps: number }>(
      "/frame",
      { method: "POST", body: JSON.stringify({ frames, fps }) },
      9000,
    ),
  worldConfig: () =>
    req<WorldConfig>("/world/config", { cache: "no-store" } as RequestInit, 5000),
  rpSignature: () => req<WorldSignature>("/world/rp-signature", { method: "POST", body: "{}" }, 12000),
  attestation: async (container: string) => {
    const res = await fetch(base + "/attestation/" + encodeURIComponent(container), {
      headers: { Accept: "application/json" },
    });
    const data = await res.json().catch(() => null);
    return { status: res.status, data } as { status: number; data: X402Challenge | Record<string, unknown> | null };
  },
};
