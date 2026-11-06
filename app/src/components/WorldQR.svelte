<script lang="ts">
  import QRCode from "qrcode";
  import { onMount } from "svelte";
  import { api, ApiError, apiBase } from "../lib/api";
  import { explain, type Failure } from "../lib/failures";
  import { ui } from "../lib/ui.svelte";

  type Props = {
    container: string;
    onClose: () => void;
  };

  let { container, onClose }: Props = $props();

  type Phase = "starting" | "scan" | "verifying" | "done" | "error";
  let phase = $state<Phase>("starting");
  let qr = $state("");
  let message = $state("");
  let failure = $state<Failure | null>(null);
  let payload = $state("");
  let closed = false;

  const idkit = (window as unknown as {
    IDKit?: {
      request: (a: unknown) => { preset: (c: unknown) => Promise<unknown> };
      proofOfHuman: () => unknown;
    };
  }).IDKit;

  const steps = $derived([
    { key: "request", label: "Request", note: "signed by the seal's relying party" },
    { key: "scan", label: "Scan", note: "World app proves a human is present" },
    { key: "verify", label: "Verify", note: "server-side, against World" },
    { key: "release", label: "Release", note: "0G decides, then the MCU hands over the key" },
  ]);

  function stepState(i: number): "done" | "active" | "todo" | "fail" {
    const idx = phase === "starting" ? 0 : phase === "scan" ? 1 : phase === "verifying" ? 2 : phase === "done" ? 4 : 2;
    if (phase === "error") {
      if (i < 1) return "done";
      return i === 1 ? "fail" : "todo";
    }
    if (i < idx) return "done";
    if (i === idx) return "active";
    return "todo";
  }

  async function start() {
    phase = "starting";
    failure = null;
    payload = "";
    try {
      const cfg = await api.worldConfig();
      if (!cfg.has_key) throw new ApiError("World signing key is not configured on the backend");
      if (!idkit) throw new ApiError("IDKit bundle is not loaded");
      const sig = await api.rpSignature();
      const builder = idkit.request({
        app_id: cfg.app_id,
        action: cfg.action,
        rp_context: {
          rp_id: cfg.rp_id,
          nonce: sig.nonce,
          created_at: sig.created_at,
          expires_at: sig.expires_at,
          signature: sig.sig,
        },
        allow_legacy_proofs: true,
        environment: "production",
      });
      const request = (await builder.preset(idkit.proofOfHuman())) as {
        connectorURI: string;
        pollUntilCompletion: () => Promise<unknown>;
      };
      qr = await QRCode.toDataURL(request.connectorURI, {
        width: 560,
        margin: 2,
        errorCorrectionLevel: "M",
        color: { dark: "#0b0b0c", light: "#efe9dd" },
      });
      phase = "scan";
      message = "Scan with the World app";
      ui.event(`world request · ${container}`);
      request.pollUntilCompletion().then(
        async (proof) => {
          if (closed) return;
          phase = "verifying";
          message = "Proof received. Verifying, then asking 0G.";
          const out = await ui.unseal(container, proof);
          if (closed) return;
          if (out) {
            phase = "done";
            payload = out.payload;
            message = "Released. The ledger records it.";
          } else {
            phase = "error";
            failure = ui.failure ?? {
              cause: "The release was refused.",
              action: "Read the ledger for the reason.",
            };
          }
        },
        (e: unknown) => {
          if (closed) return;
          phase = "error";
          failure = {
            cause: "No proof was returned, so nothing was released.",
            action: "Scan a fresh proof, or close this panel.",
          };
          message = e instanceof Error ? e.message : "";
        },
      );
    } catch (e) {
      phase = "error";
      failure = explain(e, ui.runtime?.log_path);
      if (/IDKit bundle/i.test(String(e))) {
        failure = {
          cause: "The World ID widget did not load.",
          action: "The bundled idkit.global.js is missing from this build; the rest of the app still works.",
        };
      }
    }
  }

  function close() {
    closed = true;
    onClose();
  }

  onMount(() => {
    void start();
    return () => {
      closed = true;
    };
  });
</script>

<div class="backdrop" role="dialog" aria-modal="true" aria-label="Unseal with World ID">
  <div class="card" data-phase={phase}>
    <header>
      <div class="title">
        <span class="label">Unseal · World ID</span>
        <h2>{phase === "done" ? "Released" : phase === "error" ? "Not released" : "Prove a human"}</h2>
      </div>
      <div class="head-right">
        <span class="container">{container}</span>
        <button class="icon" aria-label="Close" onclick={close}>×</button>
      </div>
    </header>

    <div class="body">
      <div class="qr-panel" data-live={phase === "scan" || phase === "verifying" ? 1 : 0}>
        {#if phase === "starting"}
          <div class="qr-skeleton"><span class="pulse" data-kind="amber"></span></div>
        {:else if phase === "done"}
          <div class="seal-mark" aria-hidden="true">
            <svg viewBox="0 0 120 120"><path d="M30 62 L52 84 L92 38" fill="none" stroke="#5ad46a" stroke-width="2" /></svg>
          </div>
        {:else if phase === "error"}
          <div class="seal-mark" data-kind="err" aria-hidden="true">
            <svg viewBox="0 0 120 120">
              <path d="M38 38 L82 82 M82 38 L38 82" fill="none" stroke="#ff5c5c" stroke-width="2" />
            </svg>
          </div>
        {:else if qr}
          <img src={qr} alt="World ID QR code" width="288" height="288" data-dim={phase === "verifying" ? 1 : 0} />
        {:else}
          <div class="qr-skeleton"><span class="pulse" data-kind="red"></span></div>
        {/if}
        <div class="qr-caption">
          <strong>
            {phase === "error"
              ? "Nothing was released"
              : message || "Preparing the request…"}
          </strong>
          <span>
            {phase === "done"
              ? "the payload key was released"
              : phase === "error"
                ? "the proof was rejected; the key stayed in the chip"
                : "point the World app at this code"}
          </span>
        </div>
      </div>

      <div class="detail">
        <ol class="steps">
          {#each steps as s, i (s.key)}
            <li data-state={stepState(i)}>
              <span class="dot" aria-hidden="true">{i + 1}</span>
              <span class="name">{s.label}</span>
              <span class="note">{s.note}</span>
            </li>
          {/each}
        </ol>

        {#if phase === "done"}
          <div class="panel" data-kind="ok">
            <span class="panel-head">Payload</span>
            <pre>{payload}</pre>
            <p class="fine">Recorded in the ledger with the World nullifier and the 0G decision.</p>
          </div>
        {:else if phase === "error"}
          <div class="panel" data-kind="err" role="alert">
            <span class="panel-head">No release</span>
            <p class="cause">{failure?.cause}</p>
            <p class="action">{failure?.action}</p>
            {#if failure?.detail}<pre class="detail-box">{failure.detail}</pre>{/if}
          </div>
        {:else}
          <div class="panel">
            <span class="panel-head">What happens</span>
            <p class="cause">
              The proof is verified server-side against {apiBase() || "the local service"}. If it is valid, 0G
              decides release or deny, and only then does the MCU derive the key.
            </p>
            <p class="fine">World ID proofs from this build are sandbox credentials.</p>
          </div>
        {/if}
      </div>
    </div>

    <footer>
      <span class="foot-note">Esc closes · nothing is released without a valid proof</span>
      <div class="foot-actions">
        {#if phase === "error"}
          <button class="btn" onclick={() => start()}>Try again</button>
        {/if}
        <button class="btn" data-kind={phase === "done" ? "primary" : "plain"} onclick={close}>
          {phase === "done" ? "Done" : "Cancel"}
        </button>
      </div>
    </footer>
  </div>
</div>

<style>
  .backdrop {
    position: fixed;
    inset: 0;
    z-index: 35;
    display: grid;
    place-items: center;
    background: rgba(6, 6, 8, 0.9);
    padding: 32px;
  }

  .card {
    width: min(820px, 100%);
    max-height: calc(100vh - 64px);
    overflow-y: auto;
    background: var(--surface);
    border: 1px solid var(--border-strong);
    border-radius: 6px;
    display: grid;
    grid-template-rows: auto 1fr auto;
  }

  header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 20px;
    padding: 24px 26px 20px;
    border-bottom: 1px solid var(--border);
  }

  h2 {
    font-size: 26px;
    font-weight: 400;
    letter-spacing: -0.01em;
    margin-top: 6px;
  }

  .head-right {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .container {
    font-size: 12px;
    letter-spacing: 0.06em;
    color: var(--muted);
    border: 1px solid var(--border-strong);
    border-radius: 999px;
    padding: 4px 12px;
  }

  .icon {
    width: 28px;
    height: 28px;
    display: grid;
    place-items: center;
    background: transparent;
    border: 1px solid var(--border-strong);
    border-radius: 999px;
    color: var(--muted);
    font-size: 16px;
    line-height: 1;
    cursor: pointer;
  }

  .icon:hover {
    color: var(--text);
    border-color: #3b3b42;
  }

  .body {
    display: grid;
    grid-template-columns: 340px minmax(0, 1fr);
    gap: 0;
  }

  .qr-panel {
    padding: 26px;
    display: grid;
    justify-items: center;
    align-content: center;
    gap: 18px;
    border-right: 1px solid var(--border);
    background: #0d0d0f;
  }

  .qr-panel img {
    display: block;
    width: 288px;
    height: 288px;
    border-radius: 3px;
    transition: opacity 200ms linear;
  }

  .qr-panel img[data-dim="1"] {
    opacity: 0.45;
  }

  .qr-skeleton,
  .seal-mark {
    width: 288px;
    height: 288px;
    display: grid;
    place-items: center;
    border: 1px solid var(--border);
    border-radius: 3px;
    background: #08080a;
  }

  .seal-mark svg {
    width: 132px;
    height: 132px;
  }

  .seal-mark[data-kind="err"] {
    border-color: #4a2626;
    background: #120a0a;
  }

  .qr-caption {
    display: grid;
    gap: 4px;
    text-align: center;
    max-width: 30ch;
  }

  .qr-caption strong {
    font-weight: 400;
    font-size: 15px;
    color: var(--text);
  }

  .qr-caption span {
    font-size: 11.5px;
    color: var(--dim);
  }

  .pulse {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--signal);
    animation: pulse 1.4s ease-in-out infinite;
  }

  .pulse[data-kind="amber"] { background: var(--amber); }
  .pulse[data-kind="red"] { background: var(--alert); }

  @keyframes pulse {
    0%, 100% { opacity: 0.25; }
    50% { opacity: 1; }
  }

  .detail {
    padding: 24px 26px;
    display: grid;
    gap: 20px;
    align-content: start;
    min-width: 0;
  }

  .steps {
    list-style: none;
    margin: 0;
    padding: 0;
    display: grid;
    gap: 2px;
  }

  .steps li {
    display: grid;
    grid-template-columns: 26px 88px minmax(0, 1fr);
    align-items: center;
    gap: 12px;
    padding: 9px 0;
    border-bottom: 1px solid #17171a;
    font-size: 12.5px;
  }

  .steps li:last-child {
    border-bottom: 0;
  }

  .dot {
    width: 22px;
    height: 22px;
    display: grid;
    place-items: center;
    border-radius: 50%;
    border: 1px solid var(--border-strong);
    font-size: 10.5px;
    color: var(--dim);
  }

  li[data-state="active"] .dot {
    border-color: var(--amber);
    color: var(--amber);
    box-shadow: inset 0 0 0 3px #151007;
  }

  li[data-state="done"] .dot {
    border-color: #2c5b33;
    color: var(--signal);
    background: #0f1410;
  }

  li[data-state="fail"] .dot {
    border-color: #4a2626;
    color: var(--alert);
    background: #150a0a;
  }

  .name {
    color: var(--muted);
  }

  li[data-state="active"] .name,
  li[data-state="done"] .name {
    color: var(--text);
  }

  .note {
    color: var(--dim);
    font-size: 11.5px;
  }

  .panel {
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 16px;
    display: grid;
    gap: 8px;
    background: #0d0d0f;
  }

  .panel[data-kind="ok"] { border-color: #2c5b33; }
  .panel[data-kind="err"] { border-color: #4a2626; }

  .panel-head {
    font-size: 10px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--dim);
  }

  .panel[data-kind="ok"] .panel-head { color: var(--signal); }
  .panel[data-kind="err"] .panel-head { color: var(--alert); }

  .cause {
    font-size: 13px;
    color: var(--text);
    line-height: 1.5;
  }

  .action {
    font-size: 12.5px;
    color: var(--muted);
  }

  .fine {
    font-size: 11px;
    color: var(--dim);
  }

  pre {
    margin: 0;
    padding: 12px;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 3px;
    font-size: 11.5px;
    color: var(--muted);
    white-space: pre-wrap;
    word-break: break-word;
    max-height: 132px;
    overflow: auto;
    user-select: text;
  }

  .detail-box {
    color: var(--dim);
    font-size: 11px;
  }

  footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    padding: 18px 26px;
    border-top: 1px solid var(--border);
  }

  .foot-note {
    font-size: 11px;
    color: var(--dim);
  }

  .foot-actions {
    display: flex;
    gap: 8px;
  }

  @media (max-width: 760px) {
    .body {
      grid-template-columns: 1fr;
    }

    .qr-panel {
      border-right: 0;
      border-bottom: 1px solid var(--border);
    }

    .card {
      width: 100%;
    }
  }
</style>
