import {
  api,
  apiBase,
  ApiError,
  resolveBase,
  type DeviceSnapshot,
  type Evidence,
  type LedgerRecord,
  type McuStatus,
} from "./api";

type LogLine = { at: number; text: string; kind?: "ok" | "err" | "dim" };

export const ui = $state({
  ready: false,
  base: "",
  device: null as DeviceSnapshot | null,
  status: null as McuStatus | null,
  ledger: [] as LedgerRecord[],
  evidence: null as Evidence | null,
  log: [] as LogLine[],
  busy: "",
  error: "",
  amberSince: 0,
  sse: false,
  lastTick: 0,
});

let pollTimer: ReturnType<typeof setInterval> | null = null;
let sse: EventSource | null = null;
let statusMisses = 0;

export function stateLabel(): string {
  if (!ui.device || ui.device.state === "absent" || ui.device.state === "error") return "OFFLINE";
  if (ui.device.state === "forwarded") return "BOOT";
  if (ui.device.state === "unauthorized") return "OFFLINE";
  const s = ui.status;
  if (!s) return "OFFLINE";
  if (s.state === 3) return "TAMPERED";
  if (s.state === 1) return s.amber ? "AMBER" : "ARMED";
  return "OFFLINE";
}

export function logLine(text: string, kind?: LogLine["kind"]) {
  ui.log = [...ui.log.slice(-120), { at: Date.now(), text, kind }];
}

function explain(e: unknown): string {
  if (e instanceof ApiError) return e.message;
  return (e as Error)?.message ?? String(e);
}

export async function refreshDevice() {
  try {
    const d = await api.device();
    ui.device = d;
    if (d.mcu) ui.status = d.mcu;
    if (d.state === "ready") ui.error = "";
  } catch (e) {
    ui.device = { state: "error", serial: "", api: "", detail: explain(e), mcu: null };
  }
}

export async function refreshStatus() {
  try {
    const s = await api.status();
    if (s.amber && !ui.status?.amber) ui.amberSince = Date.now();
    if (!s.amber) ui.amberSince = 0;
    ui.status = s;
    statusMisses = 0;
    ui.lastTick = Date.now();
    if (ui.device && ui.device.state !== "ready") {
      ui.device = { ...ui.device, state: "ready" };
    }
  } catch {
    statusMisses += 1;
    if (statusMisses >= 2 && ui.device && ui.device.state === "ready") {
      ui.device = { ...ui.device, state: "forwarded", detail: "status unavailable" };
    }
  }
}

export async function refreshLedger() {
  try {
    const d = await api.ledger();
    ui.ledger = d.records ?? [];
  } catch {
    /* keep the last known ledger; the chip already reports the outage */
  }
}

export async function refreshEvidence() {
  try {
    ui.evidence = await api.evidence();
  } catch {
    ui.evidence = null;
  }
}

async function action(name: string, fn: () => Promise<unknown>, label: string) {
  if (ui.busy) return;
  ui.busy = name;
  ui.error = "";
  try {
    await fn();
    logLine(`${label} ok`, "ok");
  } catch (e) {
    ui.error = explain(e);
    logLine(`${label}: ${ui.error}`, "err");
  } finally {
    ui.busy = "";
    await Promise.all([refreshStatus(), refreshLedger()]);
  }
}

export function seal(container = "C-001") {
  return action("seal", () => api.seal(container), `seal ${container}`);
}

export function unsealTest(container = "C-001") {
  return action(
    "unseal",
    async () => {
      const r = await api.unseal(container, "good");
      logLine(`payload: ${r.payload.trim().slice(0, 80)}`, "dim");
    },
    `unseal ${container} (test proof)`,
  );
}

export function unsealWithProof(container: string, proof: unknown) {
  return action(
    "unseal",
    async () => {
      const r = await api.unseal(container, JSON.stringify(proof));
      logLine(`payload: ${r.payload.trim().slice(0, 80)}`, "dim");
    },
    `unseal ${container} (world proof)`,
  );
}

export function flexLoop() {
  return action(
    "flex",
    async () => {
      await api.flex();
      ui.amberSince = Date.now();
    },
    "loop flexed (ambiguous)",
  );
}

export function breakLoop() {
  return action("break", async () => {
    await api.sim(0);
    ui.amberSince = Date.now();
  }, "loop opened");
}

export function closeLoop() {
  return action("close", async () => {
    await api.sim(1);
  }, "loop closed");
}

export function reprovision() {
  return action("repro", () => api.reprovision(), "reprovision");
}

function connectSse() {
  if (sse || !ui.base) return;
  try {
    sse = new EventSource(ui.base + "/events");
    sse.addEventListener("status", (ev) => {
      try {
        const s = JSON.parse((ev as MessageEvent).data) as McuStatus;
        if (s.amber && !ui.status?.amber) ui.amberSince = Date.now();
        if (!s.amber) ui.amberSince = 0;
        ui.status = s;
        ui.sse = true;
      } catch {
        /* ignore malformed frame */
      }
    });
    sse.addEventListener("ledger", () => {
      void refreshLedger();
    });
    sse.onerror = () => {
      ui.sse = false;
      sse?.close();
      sse = null;
    };
  } catch {
    ui.sse = false;
  }
}

export async function start() {
  if (ui.ready) return;
  ui.base = await resolveBase();
  await refreshDevice();
  await Promise.all([refreshStatus(), refreshLedger(), refreshEvidence()]);
  ui.ready = true;
  logLine(`api ${apiBase()}`, "dim");
  connectSse();
  if (pollTimer) clearInterval(pollTimer);
  pollTimer = setInterval(() => {
    void refreshDevice();
    if (!ui.sse) void refreshStatus();
  }, 2000);
}

export function stop() {
  if (pollTimer) clearInterval(pollTimer);
  pollTimer = null;
  sse?.close();
  sse = null;
}
