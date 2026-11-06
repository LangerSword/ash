<script lang="ts">
  import Matrix from "./Matrix.svelte";
  import Ledger from "./Ledger.svelte";
  import WorldQR from "./WorldQR.svelte";
  import Legend from "./Legend.svelte";
  import { ui } from "../lib/ui.svelte";
  import { deviceHint } from "../lib/failures";
  import { cmd } from "../lib/tauri";

  let container = $state("C-001");
  let owner = $state("human-001");
  let worldOpen = $state(false);
  let legendOpen = $state(false);
  let confirmCut = $state(false);
  let boardBusy = $state("");
  let toolNote = $state("");

  const mode = $derived(ui.mode);
  const chip = $derived(
    mode === "armed"
      ? "ARMED"
      : mode === "amber"
        ? "AMBER"
        : mode === "tampered"
          ? "TAMPERED"
          : mode === "unsealed"
            ? "UNSEALED"
            : "OFFLINE",
  );
  const hint = $derived(deviceHint(ui.device?.state ?? "starting", ui.device?.detail ?? ""));
  const deadline = $derived(ui.evidence?.deadline_ms ?? 5000);
  const last0g = $derived(ui.last0g);

  let amberSince = $state(0);
  $effect(() => {
    if (mode === "amber" && !amberSince) amberSince = performance.now();
    else if (mode !== "amber" && amberSince) amberSince = 0;
  });

  let cutTimer: number | undefined;
  $effect(() => () => window.clearTimeout(cutTimer));

  const canAct = $derived(ui.ready && ui.busy === "");
  const sealed = $derived(ui.ledger.some((r) => r.event === "SEALED" && r.container === container));

  function cut() {
    if (!confirmCut) {
      confirmCut = true;
      cutTimer = window.setTimeout(() => (confirmCut = false), 4000);
      return;
    }
    confirmCut = false;
    window.clearTimeout(cutTimer);
    void ui.breakLoop();
  }

  async function startBoard() {
    boardBusy = "board";
    try {
      const out = await cmd<string>("start_board_app");
      toolNote = out;
      ui.event(out);
      await ui.pull();
    } catch (e) {
      toolNote = e instanceof Error ? e.message : String(e);
      ui.event(`start board app failed: ${toolNote}`);
    } finally {
      boardBusy = "";
    }
  }

  async function installUdev() {
    boardBusy = "udev";
    try {
      const out = await cmd<string>("install_udev");
      toolNote = out;
      ui.event(out);
    } catch (e) {
      toolNote = e instanceof Error ? e.message : String(e);
      ui.event(`udev: ${toolNote}`);
    } finally {
      boardBusy = "";
    }
  }
</script>

<div class="console">
  <header>
    <div class="brand">
      <span class="wordmark">ASH</span>
      <span class="meta">{ui.runtime?.version ?? "0.1.0"} · {ui.runtime?.service.mode ?? "…"}</span>
    </div>

    <div class="device">
      {#if ui.device?.serial}
        <span>UNO Q · {ui.device.serial}</span>
      {:else}
        <span>{hint.line || "detecting…"}</span>
      {/if}
      {#if ui.runtime?.service.mock}
        <span class="tag" data-kind="warn">0G mock</span>
      {/if}
      <span class="tag">sandbox identity</span>
    </div>

    <div class="state">
      <span class="chip" data-state={mode} aria-live="polite">{chip}</span>
      <button class="icon" title="Legend" aria-label="Open legend" onclick={() => (legendOpen = true)}>?</button>
    </div>
  </header>

  <div class="mid">
    <section class="mirror">
      <Matrix mode={mode} {amberSince} deadlineMs={deadline} />
      <dl class="kv">
        <dt>state</dt>
        <dd>{chip} · counter {ui.status?.counter ?? "—"} · master {ui.status ? (ui.status.master ? "present" : "erased") : "—"}</dd>
        <dt>loop</dt>
        <dd>{ui.status ? (ui.status.loop ? "open" : "closed") : "—"}</dd>
        <dt>deadline</dt>
        <dd>{deadline} ms</dd>
        <dt>last 0G</dt>
        <dd title={last0g?.id ?? ""}>
          {last0g ? `${last0g.id.slice(0, 18)}… · ${last0g.latency || "?"} ms` : "—"}
        </dd>
        <dt>last hash</dt>
        <dd class="hash" title={ui.ledger.at(-1)?.hash ?? ""}>{ui.lastHash}</dd>
      </dl>

      {#if !ui.serviceOk}
        <p class="offline">
          Local service unavailable. The ledger is empty until it answers.
          <span>Retrying every second.</span>
        </p>
      {:else if hint.line}
        <p class="offline" data-kind="warn">
          {hint.line}
          {#if hint.action}<span>{hint.action}</span>{/if}
        </p>
      {/if}

      {#if ui.device?.state === "forwarded" || ui.device?.state === "absent" || ui.device?.state === "unauthorized"}
        <div class="tool-row">
          {#if ui.device?.state === "forwarded"}
            <button class="btn" disabled={boardBusy !== ""} onclick={startBoard} data-busy={boardBusy === "board" ? 1 : 0}>
              Start board app
            </button>
          {/if}
          {#if ui.runtime && !ui.runtime.udev_ok}
            <button class="btn" disabled={boardBusy !== ""} onclick={installUdev} data-busy={boardBusy === "udev" ? 1 : 0}>
              Install udev rule
            </button>
          {/if}
        </div>
      {/if}
      {#if toolNote}<p class="tool-note">{toolNote}</p>{/if}
    </section>

    <section class="controls">
      <div class="group">
        <div class="group-head">
          <span class="label">Seal</span>
          <span class="note">key derived on the MCU, payload encrypted here</span>
        </div>
        <div class="row">
          <input
            class="field"
            bind:value={container}
            aria-label="Container id"
            spellcheck="false"
            maxlength="24"
            placeholder="C-001"
          />
          <button
            class="btn"
            data-kind="primary"
            disabled={!canAct || !container.trim()}
            data-busy={ui.busy === "seal" ? 1 : 0}
            onclick={() => ui.seal(container.trim(), owner)}
          >
            Seal container
          </button>
        </div>
      </div>

      <div class="group">
        <div class="group-head">
          <span class="label">Unseal</span>
          <span class="note">World proof, then a 0G release decision</span>
        </div>
        <div class="row">
          <button
            class="btn"
            disabled={!canAct || !container.trim()}
            data-busy={ui.busy === "unseal" ? 1 : 0}
            onclick={() => (worldOpen = true)}
          >
            Unseal with World ID
          </button>
          <span class="note">{sealed ? "seal found" : "no seal yet"}</span>
        </div>
      </div>

      <div class="group">
        <div class="group-head">
          <span class="label">Fault injection</span>
          <span class="note">the rig on the desk, not a simulation</span>
        </div>
        <div class="row">
          <button
            class="btn"
            disabled={!canAct || ui.status?.state === 3}
            data-busy={ui.busy === "flex" ? 1 : 0}
            onclick={() => ui.flex()}
          >
            Flex loop · Tier 1
          </button>
          <button
            class="btn"
            data-kind="danger"
            disabled={!canAct || ui.status?.state === 3}
            data-busy={ui.busy === "cut" ? 1 : 0}
            onclick={cut}
          >
            {confirmCut ? "Confirm · wipe the key" : "Break loop · Tier 0"}
          </button>
          <button
            class="btn"
            disabled={!canAct}
            data-busy={ui.busy === "reprovision" ? 1 : 0}
            onclick={() => ui.reprovision()}
          >
            Reprovision
          </button>
        </div>
      </div>

      {#if ui.failure}
        <div class="msg" data-kind="err" role="alert">
          <p>{ui.failure.cause}</p>
          <p class="action">{ui.failure.action}</p>
          {#if ui.failure.detail}<p class="detail">{ui.failure.detail}</p>{/if}
        </div>
      {:else if ui.notice}
        <div class="msg" data-kind="ok">
          <p>{ui.notice}</p>
        </div>
      {:else}
        <div class="msg" data-kind="idle">
          <p>
            {ui.ready
              ? "Ready. The key lives in the chip; the ledger is hash-chained."
              : "Controls unlock when the board answers."}
          </p>
        </div>
      {/if}

      <div class="log">
        <span class="label">Event log</span>
        <pre class="scroll">{#each ui.lines.slice(-7) as line}<span class="t">{new Date(line.at).toLocaleTimeString([], { hour12: false })}</span> {line.text}
{/each}{#if ui.lines.length === 0}<span class="t">--:--:--</span> waiting
{/if}</pre>
      </div>
    </section>
  </div>

  <Ledger
    records={ui.ledger}
    verify={ui.verify}
    busy={ui.busy}
    {container}
    onVerify={() => ui.verifyLedger()}
    onAttest={() => ui.readAttestation(container)}
  />
</div>

{#if worldOpen}
  <WorldQR {container} onClose={() => (worldOpen = false)} />
{/if}

{#if legendOpen}
  <Legend
    onDone={() => {
      legendOpen = false;
      ui.saveConfig({ legend_seen: true });
    }}
  />
{/if}

<style>
  .console {
    display: grid;
    grid-template-rows: 44px minmax(0, 1fr) minmax(190px, 34%);
    height: 100%;
    min-height: 0;
  }

  header {
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    align-items: center;
    gap: 16px;
    padding: 0 14px;
    border-bottom: 1px solid var(--border);
  }

  .brand {
    display: flex;
    align-items: baseline;
    gap: 10px;
  }

  .wordmark {
    font-size: 14px;
    letter-spacing: 0.34em;
    font-weight: 500;
  }

  .meta {
    font-size: 10px;
    color: var(--dim);
    letter-spacing: 0.04em;
  }

  .device {
    display: flex;
    align-items: center;
    gap: 8px;
    justify-content: center;
    font-size: 11px;
    color: var(--muted);
    min-width: 0;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
  }

  .tag {
    font-size: 9px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--dim);
    border: 1px solid var(--border);
    border-radius: 999px;
    padding: 1px 6px;
  }

  .tag[data-kind="warn"] {
    color: var(--amber);
    border-color: #4a3a18;
  }

  .state {
    display: flex;
    align-items: center;
    gap: 8px;
    justify-content: flex-end;
  }

  .icon {
    width: 22px;
    height: 22px;
    display: grid;
    place-items: center;
    background: transparent;
    border: 1px solid var(--border-strong);
    border-radius: 999px;
    color: var(--muted);
    font-size: 11px;
    cursor: pointer;
  }

  .icon:hover {
    color: var(--text);
    border-color: #3b3b42;
  }

  .mid {
    display: grid;
    grid-template-columns: minmax(280px, 360px) minmax(0, 1fr);
    gap: 0;
    border-bottom: 1px solid var(--border);
    min-height: 0;
    overflow: hidden;
  }

  .mirror {
    padding: 14px;
    display: grid;
    gap: 12px;
    align-content: start;
    border-right: 1px solid var(--border);
    min-width: 0;
    min-height: 0;
    overflow-y: auto;
    scrollbar-width: thin;
    scrollbar-color: #2e2e33 transparent;
  }

  .hash {
    color: var(--dim);
    font-size: 11px;
  }

  .kv dd {
    white-space: normal;
    overflow-wrap: anywhere;
  }

  .offline {
    font-size: 11px;
    color: var(--muted);
    border-left: 1px solid var(--amber);
    padding-left: 9px;
  }

  .offline span {
    display: block;
    color: var(--dim);
    margin-top: 2px;
  }

  .tool-row {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }

  .tool-note {
    font-size: 11px;
    color: var(--dim);
    overflow-wrap: anywhere;
  }

  .controls {
    padding: 14px;
    display: grid;
    gap: 12px;
    align-content: start;
    min-width: 0;
    min-height: 0;
    overflow-y: auto;
    scrollbar-width: thin;
    scrollbar-color: #2e2e33 transparent;
  }

  .group {
    display: grid;
    gap: 7px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--border);
  }

  .group-head {
    display: flex;
    align-items: baseline;
    gap: 10px;
  }

  .note {
    font-size: 10px;
    color: var(--dim);
  }

  .row {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
  }

  .row .field {
    width: 120px;
  }

  .msg {
    font-size: 12px;
    border-left: 2px solid var(--border-strong);
    padding: 2px 0 2px 10px;
    display: grid;
    gap: 2px;
  }

  .msg p {
    color: var(--muted);
  }

  .msg[data-kind="err"] {
    border-color: var(--alert);
  }

  .msg[data-kind="err"] p:first-child {
    color: var(--alert);
  }

  .msg[data-kind="ok"] {
    border-color: var(--signal);
  }

  .msg[data-kind="ok"] p {
    color: var(--signal);
  }

  .msg .action {
    color: var(--text);
  }

  .msg .detail {
    font-size: 10px;
    color: var(--dim);
    overflow-wrap: anywhere;
  }

  .log {
    display: grid;
    gap: 5px;
    min-height: 0;
  }

  .log pre {
    margin: 0;
    font-size: 10px;
    line-height: 1.5;
    color: var(--muted);
    max-height: 84px;
    min-height: 42px;
    padding: 8px;
    background: #08080a;
    border: 1px solid var(--border);
    border-radius: 2px;
    white-space: pre-wrap;
    user-select: text;
  }

  .log .t {
    color: var(--dim);
    margin-right: 5px;
  }

  @media (max-width: 860px) {
    header {
      grid-template-columns: 1fr auto;
    }

    .device {
      display: none;
    }

    .mid {
      grid-template-columns: 1fr;
      overflow-y: auto;
    }

    .mirror,
    .controls {
      overflow: visible;
    }

    .mirror {
      border-right: 0;
      border-bottom: 1px solid var(--border);
    }
  }
</style>
