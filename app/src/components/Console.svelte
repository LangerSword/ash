<script lang="ts">
  import Matrix from "./Matrix.svelte";
  import Ledger from "./Ledger.svelte";
  import WorldQR from "./WorldQR.svelte";
  import Legend from "./Legend.svelte";
  import Connection from "./Connection.svelte";
  import { ui } from "../lib/ui.svelte";
  import { connection } from "../lib/connect";
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
  const conn = $derived(connection(ui.device, ui.runtime?.service ?? null, ui.runtime?.udev_ok ?? true));

  const heroWord = $derived(
    mode === "armed" ? "Sealed" : mode === "amber" ? "Deciding" : mode === "tampered" ? "Destroyed" : mode === "unsealed" ? "Open" : "Offline",
  );
  const heroLine = $derived(
    mode === "armed"
      ? "the key is in the chip · the loop is intact"
      : mode === "amber"
        ? "someone touched the loop · 0G has seconds to answer"
        : mode === "tampered"
          ? "the key is gone · the payload is noise now"
          : mode === "unsealed"
            ? "released to a verified human"
            : "no board on USB",
  );
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

  function onConnAction(kind: "start_board" | "udev" | "retry") {
    if (kind === "start_board") void startBoard();
    else if (kind === "udev") void installUdev();
    else void ui.boot();
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
      <span class="wordmark">Ash</span>
      <span class="meta">tamper-responsive seal</span>
    </div>

    <div class="device">
      {#if ui.device?.serial}
        <span>UNO Q · {ui.device.serial}</span>
      {:else}
        <span>{conn.headline}</span>
      {/if}
      {#if ui.runtime?.service.mock}
        <span class="tag" data-kind="warn">0G mock</span>
      {/if}
    </div>

    <div class="state">
      <span class="chip" data-state={mode} aria-live="polite">{chip}</span>
      <button class="icon" title="Legend" aria-label="Open legend" onclick={() => (legendOpen = true)}>?</button>
    </div>
  </header>

  <div class="mid">
    <section class="mirror">
      <div class="hero" data-state={mode}>
        <span class="hero-word">{heroWord}</span>
        <span class="hero-line">{heroLine}</span>
        <div class="assure">
          <span class="assure-chip" data-ok={ui.verify ? (ui.verify.ok ? 1 : 0) : -1}>
            {ui.verify ? (ui.verify.ok ? `chain verified · ${ui.verify.records}` : `chain broken · ${ui.verify.detail}`) : "chain unchecked"}
          </span>
          <span class="assure-chip" data-ok={ui.status?.master ? 1 : 0}>key hardware-bound</span>
          <span class="assure-chip" data-ok={1}>release needs a human</span>
        </div>
      </div>

      <Matrix mode={mode} {amberSince} deadlineMs={deadline} />

      <dl class="kv">
        <dt>key</dt>
        <dd>{ui.status ? (ui.status.master ? "in the chip" : "destroyed") : "—"}</dd>
        <dt>loop</dt>
        <dd>{ui.status ? (ui.status.loop ? "open" : "closed") : "—"}</dd>
        <dt>opens</dt>
        <dd>{ui.status?.counter ?? "—"}</dd>
        <dt>last record</dt>
        <dd class="hash" title={ui.ledger.at(-1)?.hash ?? ""}>{ui.lastHash}</dd>
      </dl>

      <details class="more">
        <summary>Details</summary>
        <dl class="kv">
          <dt>deadline</dt>
          <dd>{deadline} ms</dd>
          <dt>last decision</dt>
          <dd title={last0g?.id ?? ""}>{last0g ? `${last0g.id.slice(0, 14)}… · 0G` : "—"}</dd>
          <dt>service</dt>
          <dd>{ui.runtime?.service.mode ?? "—"}</dd>
          <dt>build</dt>
          <dd>{ui.runtime?.version ?? "—"}</dd>
        </dl>
      </details>

      {#if !conn.ready}
        <Connection {conn} busy={boardBusy} onAction={onConnAction} compact />
      {/if}
      {#if toolNote}<p class="tool-note">{toolNote}</p>{/if}
    </section>

    <section class="controls">
      <div class="group">
        <div class="group-head">
          <span class="label">Seal a case</span>
          <span class="note">key derived in the chip, payload encrypted here</span>
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
            data-kind={sealed ? "plain" : "primary"}
            disabled={!canAct || !container.trim() || sealed}
            data-busy={ui.busy === "seal" ? 1 : 0}
            onclick={() => ui.seal(container.trim(), owner)}
          >
            {sealed ? "Already sealed" : "Seal container"}
          </button>
        </div>
      </div>

      <div class="group">
        <div class="group-head">
          <span class="label">Open it</span>
          <span class="note">a human, then a 0G release decision</span>
        </div>
        <div class="row">
          <button
            class="btn"
            data-kind={sealed ? "primary" : "plain"}
            disabled={!canAct || !container.trim()}
            data-busy={ui.busy === "unseal" ? 1 : 0}
            onclick={() => (worldOpen = true)}
          >
            Unseal with World ID
          </button>
          <span class="note">{sealed ? `${container} is sealed` : "nothing sealed yet"}</span>
        </div>
      </div>

      <details class="group attacks">
        <summary>
          <span class="label">What can happen to it</span>
          <span class="note">on the real board · demo rig</span>
        </summary>
        <div class="row">
          <button
            class="btn"
            disabled={!canAct || ui.status?.state === 3}
            data-busy={ui.busy === "flex" ? 1 : 0}
            onclick={() => ui.flex()}
          >
            Someone handled it
            <span class="tier">Tier 1</span>
          </button>
          <button
            class="btn"
            data-kind="danger"
            disabled={!canAct || ui.status?.state === 3}
            data-busy={ui.busy === "cut" ? 1 : 0}
            onclick={cut}
          >
            {confirmCut ? "Confirm · the key dies" : "Someone cut the loop"}
            <span class="tier">Tier 0</span>
          </button>
          <button
            class="btn"
            disabled={!canAct}
            data-busy={ui.busy === "reprovision" ? 1 : 0}
            onclick={() => ui.reprovision()}
          >
            Reset the seal
          </button>
        </div>
      </details>

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
              ? "The key lives in the chip. Cut the loop and it is gone in a millisecond."
              : "Controls unlock when the board answers."}
          </p>
        </div>
      {/if}

      <details class="log">
        <summary>Activity log</summary>
        <pre class="scroll">{#each ui.lines.slice(-7) as line}<span class="t">{new Date(line.at).toLocaleTimeString([], { hour12: false })}</span> {line.text}
{/each}{#if ui.lines.length === 0}<span class="t">--:--:--</span> waiting
{/if}</pre>
      </details>
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
    grid-template-rows: 52px minmax(0, 1fr) minmax(320px, 44%);
    height: 100%;
    min-height: 0;
  }

  header {
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    align-items: center;
    gap: 16px;
    padding: 0 20px;
    border-bottom: 1px solid var(--border);
  }

  .brand {
    display: flex;
    align-items: baseline;
    gap: 10px;
  }

  .wordmark {
    font-family: var(--serif);
    font-size: 24px;
    letter-spacing: 0.02em;
    font-weight: 400;
    line-height: 1;
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
    grid-template-columns: minmax(320px, 420px) minmax(0, 1fr);
    gap: 0;
    border-bottom: 1px solid var(--border);
    min-height: 0;
    overflow: hidden;
  }

  .mirror {
    padding: 20px;
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

  .hero {
    display: grid;
    gap: 4px;
    padding-bottom: 4px;
  }

  .hero-word {
    font-family: var(--serif);
    font-size: 58px;
    line-height: 1.05;
    font-weight: 300;
    letter-spacing: -0.01em;
    color: var(--text);
  }

  .hero[data-state="armed"] .hero-word { color: var(--signal); }
  .hero[data-state="amber"] .hero-word { color: var(--amber); }
  .hero[data-state="tampered"] .hero-word { color: var(--alert); }
  .hero[data-state="offline"] .hero-word { color: var(--dim); }

  .hero-line {
    font-size: 12px;
    color: var(--muted);
  }

  .assure {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 8px;
  }

  .assure-chip {
    font-size: 10.5px;
    letter-spacing: 0.02em;
    color: var(--muted);
    border: 1px solid var(--border);
    border-radius: 999px;
    padding: 2px 8px;
  }

  .assure-chip[data-ok="1"] {
    color: var(--signal);
    border-color: #24422a;
  }

  .assure-chip[data-ok="0"] {
    color: var(--alert);
    border-color: #4a2626;
  }

  .more,
  .log {
    border-top: 1px solid var(--border);
    padding-top: 10px;
  }

  .more summary,
  .log summary {
    font-size: 10.5px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--dim);
    cursor: pointer;
    list-style: none;
  }

  .more summary::-webkit-details-marker,
  .log summary::-webkit-details-marker {
    display: none;
  }

  .more summary::before,
  .log summary::before {
    content: "+ ";
    color: var(--muted);
  }

  .more[open] summary::before,
  .log[open] summary::before {
    content: "− ";
  }

  .more .kv {
    margin-top: 10px;
  }

  .hash {
    color: var(--dim);
    font-size: 11px;
  }

  .kv dd {
    white-space: normal;
    overflow-wrap: anywhere;
  }

  .tool-note {
    font-size: 11px;
    color: var(--dim);
    overflow-wrap: anywhere;
  }

  .controls {
    padding: 20px;
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

  .attacks summary {
    display: flex;
    align-items: baseline;
    gap: 10px;
    cursor: pointer;
    list-style: none;
  }

  .attacks summary::-webkit-details-marker {
    display: none;
  }

  .attacks summary .label::before {
    content: "+ ";
    color: var(--muted);
  }

  .attacks[open] summary .label::before {
    content: "− ";
  }

  .attacks[open] {
    gap: 10px;
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

  .tier {
    font-size: 9px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--dim);
    border: 1px solid var(--border);
    border-radius: 999px;
    padding: 1px 5px;
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
    font-size: 11px;
    line-height: 1.6;
    color: var(--text);
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
    color: var(--muted);
    margin-right: 6px;
  }

  /* a tiled window is shorter than the design size; degrade, don't clip */
  @media (max-height: 760px) and (min-width: 861px) {
    .console {
      grid-template-rows: 48px minmax(0, 1fr) minmax(210px, 40%);
    }

    .mirror,
    .controls {
      padding: 14px;
    }

    .log pre {
      max-height: 64px;
    }
  }

  @media (max-width: 860px) {
    .console {
      display: block;
      height: 100%;
      overflow-y: auto;
    }

    header {
      position: sticky;
      top: 0;
      z-index: 2;
      height: 52px;
      background: var(--bg);
      grid-template-columns: 1fr auto;
    }

    .device {
      display: none;
    }

    .mid {
      display: block;
    }

    .mirror,
    .controls {
      overflow: visible;
      min-height: auto;
    }
  }
</style>
