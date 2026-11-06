import { api, ApiError, setBase } from "./api";
import { cmd } from "./tauri";
import { explain, type Failure } from "./failures";
import type {
  Config,
  Evidence,
  LedgerRecord,
  McuStatus,
  RuntimeInfo,
  WorldConfig,
} from "./types";

type Line = { at: number; text: string };

class Ui {
  runtime = $state<RuntimeInfo | null>(null);
  status = $state<McuStatus | null>(null);
  evidence = $state<Evidence | null>(null);
  ledger = $state<LedgerRecord[]>([]);
  worldConfig = $state<WorldConfig | null>(null);
  serviceOk = $state(false);
  busy = $state("");
  failure = $state<Failure | null>(null);
  notice = $state("");
  lines = $state<Line[]>([]);
  verify = $state<{ ok: boolean; detail: string; records: number } | null>(null);

  private running = false;
  private tick = 0;
  private lastDevice = "";

  get device() {
    return this.runtime?.device ?? null;
  }

  get ready() {
    return this.device?.state === "ready" && this.serviceOk;
  }

  get mode(): "armed" | "amber" | "tampered" | "unsealed" | "offline" {
    if (!this.serviceOk) return "offline";
    const s = this.status;
    if (!s) return "offline";
    if (s.state === 3) return "tampered";
    if (s.state === 2) return "unsealed";
    if (s.state === 1) return s.amber ? "amber" : "armed";
    return "offline";
  }

  get lastHash(): string {
    const h = this.ledger.at(-1)?.hash ?? "";
    return h ? h.slice(0, 12) : "—";
  }

  get last0g(): { id: string; latency: number } | null {
    for (let i = this.ledger.length - 1; i >= 0; i -= 1) {
      const r = this.ledger[i];
      const g = (r["0g"] ?? r.meta ?? {}) as { request_id?: string; latency_ms?: number };
      if (g.request_id) return { id: g.request_id, latency: Number(g.latency_ms ?? 0) };
    }
    return null;
  }

  event(text: string) {
    this.lines = [...this.lines.slice(-39), { at: Date.now(), text }];
    void cmd("append_log", { line: text }).catch(() => undefined);
  }

  async boot() {
    await this.pullRuntime();
    if (this.runtime?.config.intro_seen === undefined) return;
    this.loop();
  }

  stop() {
    this.running = false;
  }

  private async loop() {
    if (this.running) return;
    this.running = true;
    while (this.running) {
      await this.pull();
      await new Promise((r) => setTimeout(r, 1000));
    }
  }

  private async pullRuntime() {
    try {
      this.runtime = await cmd<RuntimeInfo>("runtime_info");
      const svc = this.runtime.service;
      if (svc.mode !== "unavailable" && svc.base) setBase(svc.base);
    } catch (e) {
      this.failure = explain(e, this.runtime?.log_path);
    }
  }

  async pull() {
    await this.pullRuntime();
    const svc = this.runtime?.service;
    if (!svc || svc.mode === "starting" || svc.mode === "unavailable" || !svc.base) {
      this.serviceOk = false;
      this.tick += 1;
      return;
    }
    try {
      const st = await api.status();
      this.status = st;
      this.serviceOk = true;
      if (this.device?.state === "ready" && this.lastDevice !== "ready") {
        this.refresh();
      }
      this.lastDevice = this.device?.state ?? "";
      if (this.tick % 2 === 0) {
        const l = await api.ledger();
        this.ledger = l.records;
      }
      if (!this.evidence) {
        this.evidence = await api.evidence().catch(() => null);
      }
    } catch {
      this.serviceOk = false;
      this.status = null;
    }
    this.tick += 1;
  }

  async refresh() {
    try {
      const [st, l] = await Promise.all([api.status(), api.ledger()]);
      this.status = st;
      this.ledger = l.records;
      this.serviceOk = true;
    } catch {
      this.serviceOk = false;
    }
  }

  async loadWorld() {
    try {
      this.worldConfig = await api.worldConfig();
    } catch {
      this.worldConfig = null;
    }
  }

  private async run<T>(name: string, fn: () => Promise<T>): Promise<T | null> {
    if (this.busy) return null;
    this.busy = name;
    this.failure = null;
    this.notice = "";
    try {
      return await fn();
    } catch (e) {
      this.failure = explain(e, this.runtime?.log_path);
      this.event(`${name} failed: ${this.failure.cause}`);
      return null;
    } finally {
      this.busy = "";
      await this.refresh();
    }
  }

  seal(container: string, owner: string) {
    return this.run("seal", async () => {
      const out = await api.seal(container, owner);
      this.notice = `Sealed ${container} · ${out.record.payload_sha256?.slice(0, 12) ?? ""}…`;
      this.event(`sealed ${container} · hash ${out.record.hash?.slice(0, 10) ?? ""}`);
      return out;
    });
  }

  unseal(container: string, proof: unknown) {
    return this.run("unseal", async () => {
      try {
        const out = await api.unseal(container, proof);
        this.notice = `Unsealed ${container} · ${out.payload.slice(0, 60)}`;
        this.event(`unsealed ${container} · hash ${out.record.hash?.slice(0, 10) ?? ""}`);
        return out;
      } catch (e) {
        if (e instanceof ApiError && /0g/i.test(e.message)) {
          const l = await api.ledger().catch(() => null);
          if (l) this.ledger = l.records;
        }
        throw e;
      }
    });
  }

  flex() {
    return this.run("flex", async () => {
      this.event("flex loop · ambiguous event, Tier 1");
      const out = await api.flex();
      this.notice = "Ambiguous event resolved; see the ledger for the decision.";
      return out;
    });
  }

  async breakLoop() {
    return this.run("cut", async () => {
      this.event("loop open · Tier 0 armed");
      const out = await api.sim(0);
      this.notice = "Loop open. The MCU wipes after 250 ms.";
      return out;
    });
  }

  reprovision() {
    return this.run("reprovision", async () => {
      this.event("reprovision · dev hook");
      const out = await api.reprovision();
      this.notice = "Board reprovisioned and re-armed.";
      return out;
    });
  }

  verifyLedger() {
    return this.run("verify", async () => {
      const out = await api.verify();
      this.verify = { ok: out.ok, detail: out.detail, records: out.records };
      this.event(`ledger verify · ${out.ok ? "ok" : out.detail}`);
      return out;
    });
  }

  async readAttestation(container: string) {
    this.failure = null;
    this.notice = "";
    try {
      const out = await api.attestation(container);
      if (out.status === 402) {
        const body = out.data as { accepts?: Array<Record<string, unknown>> };
        const a = body?.accepts?.[0] ?? {};
        const amount = Number(a.amount ?? 0) / 1e6;
        this.failure = {
          cause: `Payment required: ${amount} ${a.asset ?? "USDC"} to ${a.payTo ?? "the payee"} on ${a.network ?? "hedera"}.`,
          action: "The app does not pay automatically. The agent's key settles it server-side.",
        };
        return;
      }
      if (out.status === 200) {
        const d = out.data as { tx_id?: string; hashscan?: string };
        this.notice = `Settled · tx ${d.tx_id ?? "?"}`;
        this.event(`attestation paid · tx ${d.tx_id ?? "?"}`);
        return;
      }
      this.failure = explain(new ApiError(String((out.data as { error?: string })?.error ?? "attestation failed"), out.status));
    } catch (e) {
      this.failure = explain(e, this.runtime?.log_path);
    }
  }

  saveConfig(patch: Partial<Config>) {
    if (!this.runtime) return;
    this.runtime = { ...this.runtime, config: { ...this.runtime.config, ...patch } };
    void cmd("save_config", { patch }).catch(() => undefined);
  }
}

export const ui = new Ui();
