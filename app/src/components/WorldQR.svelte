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

  async function start() {
    phase = "starting";
    failure = null;
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
        width: 240,
        margin: 1,
        errorCorrectionLevel: "M",
        color: { dark: "#0b0b0c", light: "#e8e8e8" },
      });
      phase = "scan";
      message = "Scan with World ID to approve the release.";
      ui.event(`world request · ${container}`);
      request.pollUntilCompletion().then(
        async (proof) => {
          if (closed) return;
          phase = "verifying";
          message = "Proof received. Verifying server-side, then asking 0G.";
          const out = await ui.unseal(container, proof);
          if (closed) return;
          if (out) {
            phase = "done";
            payload = out.payload;
            message = "Released. The ledger records the release.";
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
  <div class="card">
    <div class="head">
      <span class="label">Unseal · World ID</span>
      <span class="mono-dim">{container}</span>
    </div>

    {#if phase === "scan" || phase === "verifying"}
      <div class="qr">
        {#if qr}<img src={qr} alt="World ID QR code" width="240" height="240" />{/if}
        <div class="qr-note">
          {#if phase === "verifying"}
            <span class="pulse" data-kind="amber"></span>
          {:else}
            <span class="pulse"></span>
          {/if}
          {message}
        </div>
      </div>
      <p class="fine">
        The proof is verified against {apiBase() || "the configured service"} and the World developer
        API. Sandbox credentials only.
      </p>
    {:else if phase === "done"}
      <div class="result" data-kind="ok">
        <strong>Released</strong>
        <p>{message}</p>
        <pre>{payload}</pre>
      </div>
    {:else if phase === "error"}
      <div class="result" data-kind="err">
        <strong>No release</strong>
        <p>{failure?.cause}</p>
        <p class="action">{failure?.action}</p>
        {#if failure?.detail}<pre>{failure.detail}</pre>{/if}
      </div>
    {:else}
      <div class="starting">
        <span class="pulse" data-kind="amber"></span>
        Building the World request…
      </div>
    {/if}

    <div class="foot">
      {#if phase === "error" && failure?.cause.includes("No proof")}
        <button class="btn" onclick={() => start()}>Try again</button>
      {/if}
      <button class="btn" onclick={close}>{phase === "done" ? "Close" : "Cancel"}</button>
    </div>
  </div>
</div>

<style>
  .backdrop {
    position: fixed;
    inset: 0;
    z-index: 35;
    display: grid;
    place-items: center;
    background: rgba(8, 8, 10, 0.86);
    padding: 24px;
  }

  .card {
    width: min(460px, 100%);
    max-height: 100%;
    overflow-y: auto;
    background: var(--surface);
    border: 1px solid var(--border-strong);
    border-radius: var(--radius);
    padding: 20px;
    display: grid;
    gap: 16px;
  }

  .head {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    font-size: 12px;
  }

  .qr {
    display: grid;
    justify-items: center;
    gap: 12px;
  }

  .qr img {
    display: block;
    border-radius: 2px;
  }

  .qr-note {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    color: var(--muted);
    text-align: center;
  }

  .pulse {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--signal);
    animation: pulse 1.4s ease-in-out infinite;
  }

  .pulse[data-kind="amber"] {
    background: var(--amber);
  }

  @keyframes pulse {
    0%, 100% { opacity: 0.3; }
    50% { opacity: 1; }
  }

  .fine {
    font-size: 11px;
    color: var(--dim);
    text-align: center;
  }

  .starting {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    color: var(--muted);
    padding: 24px 0;
  }

  .result {
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 14px;
    font-size: 12px;
    display: grid;
    gap: 8px;
  }

  .result[data-kind="ok"] {
    border-color: #2c5b33;
  }

  .result[data-kind="err"] {
    border-color: #4a2626;
  }

  .result strong {
    font-weight: 500;
    letter-spacing: 0.06em;
  }

  .result[data-kind="ok"] strong {
    color: var(--signal);
  }

  .result[data-kind="err"] strong {
    color: var(--alert);
  }

  .result p {
    color: var(--muted);
  }

  .result .action {
    color: var(--text);
  }

  pre {
    margin: 0;
    padding: 10px;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 2px;
    font-size: 11px;
    color: var(--muted);
    white-space: pre-wrap;
    word-break: break-all;
    max-height: 120px;
    overflow: auto;
    user-select: text;
  }

  .foot {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
    border-top: 1px solid var(--border);
    padding-top: 14px;
  }
</style>
