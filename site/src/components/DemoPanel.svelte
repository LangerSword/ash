<script lang="ts">
  import MatrixMirror from "./MatrixMirror.svelte";
  import Ledger from "./Ledger.svelte";
  import { api, apiBase } from "../lib/api";
  import {
    breakLoop,
    closeLoop,
    flexLoop,
    reprovision,
    seal,
    stateLabel,
    ui,
    unsealTest,
    unsealWithProof,
  } from "../lib/store.svelte";

  let world = $state<{ phase: "idle" | "starting" | "scan" | "verifying" | "done" | "error"; qr: string; msg: string }>({
    phase: "idle",
    qr: "",
    msg: "",
  });

  async function unsealWorld() {
    if (world.phase === "starting" || world.phase === "scan" || world.phase === "verifying") return;
    world = { phase: "starting", qr: "", msg: "" };
    try {
      const cfg = await api.worldConfig();
      if (!cfg.has_key) throw new Error("World signing key not configured");
      const sig = (await fetch(apiBase() + "/world/rp-signature", { method: "POST" }).then((r) =>
        r.json(),
      )) as { sig: string; nonce: string; created_at: number; expires_at: number };
      const idkit = (window as unknown as {
        IDKit?: {
          request: (a: unknown) => { preset: (c: unknown) => Promise<unknown> };
          proofOfHuman: () => unknown;
        };
      }).IDKit;
      if (!idkit) throw new Error("IDKit bundle not loaded");
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
      world = {
        phase: "scan",
        qr: apiBase() + "/world/qr?data=" + encodeURIComponent(request.connectorURI),
        msg: "Scan with World ID to approve the unseal.",
      };
      const proof = await request.pollUntilCompletion();
      world = { ...world, phase: "verifying", msg: "Proof received. Verifying server-side…" };
      await unsealWithProof("C-001", proof);
      world = { phase: "done", qr: "", msg: "Unsealed with a World proof." };
    } catch (e) {
      world = { phase: "error", qr: "", msg: (e as Error).message || "World flow failed" };
    }
  }

  const deviceReady = $derived(ui.device?.state === "ready");
  const lock = $derived(!deviceReady || ui.busy !== "");

  const hint = $derived.by(() => {
    if (ui.error) return ui.error;
    if (!ui.device) return "Detecting board…";
    if (ui.device.state === "absent") return "No UNO Q on USB. Connect the board.";
    if (ui.device.state === "unauthorized") return "Authorise USB debugging on the board.";
    if (ui.device.state === "forwarded") return "Booting the board app…";
    if (ui.device.state === "error") return ui.device.detail;
    if (ui.status?.amber) return "Tier 1 pending: 0G decision inside the deadline.";
    if (ui.status?.state === 3) return "Key destroyed. Reprovision to run it again.";
    return "";
  });

  const last0g = $derived.by(() => {
    const rec = [...ui.ledger].reverse().find((r) => (r["0g"] as { request_id?: string })?.request_id);
    const g = rec?.["0g"] as { request_id?: string } | undefined;
    return g?.request_id ? g.request_id.slice(0, 18) + "…" : "n/a";
  });

  const master = $derived(ui.status ? (ui.status.master ? "present" : "erased") : "n/a");
  const loopState = $derived(ui.status ? (ui.status.loop ? "open" : "closed") : "n/a");
  const deadline = $derived(ui.evidence ? `${ui.evidence.deadline_ms} ms` : "5 000 ms");

  function ago(at: number): string {
    const s = Math.max(0, Math.round((Date.now() - at) / 1000));
    return s < 60 ? `${s}s ago` : `${Math.round(s / 60)}m ago`;
  }
</script>

<div class="panel">
  <div class="panel-head">
    <span>Live seal · UNO Q {ui.device?.serial ? `· ${ui.device.serial}` : ""}</span>
    <span>{ui.sse ? "sse" : "poll"} · {ui.device?.state ?? "…"}</span>
  </div>

  <div class="panel-body">
    <MatrixMirror />

    <div>
      <div class="controls">
        <button class="btn" data-kind="primary" disabled={lock} data-busy={ui.busy === "seal" ? 1 : 0}
          onclick={() => seal("C-001")}>Seal container</button>
        <button class="btn" disabled={lock} data-busy={ui.busy === "unseal" ? 1 : 0}
          onclick={() => unsealTest("C-001")}>Unseal (test proof)</button>
        <button class="btn" disabled={lock || world.phase === "starting" || world.phase === "scan"}
          data-busy={world.phase === "scan" || world.phase === "verifying" ? 1 : 0}
          onclick={() => unsealWorld()}>Unseal with World ID</button>
        <button class="btn" disabled={lock || ui.status?.state === 3}
          data-busy={ui.busy === "flex" ? 1 : 0} onclick={() => flexLoop()}>Flex loop (Tier 1)</button>
        <button class="btn" data-kind="danger" disabled={lock || ui.status?.state === 3}
          data-busy={ui.busy === "break" ? 1 : 0} onclick={() => breakLoop()}>Cut loop (Tier 0)</button>
        <button class="btn" disabled={lock} data-busy={ui.busy === "close" ? 1 : 0}
          onclick={() => closeLoop()}>Close loop</button>
        <button class="btn" disabled={lock} data-busy={ui.busy === "repro" ? 1 : 0}
          onclick={() => reprovision()}>Reprovision</button>
      </div>

      <div class="hint" aria-live="polite">{hint}</div>

      {#if world.qr || world.msg}
        <div class="qr-box">
          {#if world.qr}
            <img src={world.qr} alt="World ID QR code" width="180" height="180" />
          {/if}
          <div class="qr-msg" data-phase={world.phase}>{world.msg}</div>
        </div>
      {/if}

      <dl class="state-list">
        <dt>state</dt><dd>{stateLabel()}</dd>
        <dt>counter</dt><dd>{ui.status?.counter ?? "n/a"}</dd>
        <dt>master</dt><dd>{master}</dd>
        <dt>loop</dt><dd>{loopState}</dd>
        <dt>deadline</dt><dd>{deadline}</dd>
        <dt>last 0G</dt><dd class="mono-small" title={last0g}>{last0g}</dd>
        <dt>device</dt><dd class="mono-small">{ui.device?.state ?? "…"}</dd>
      </dl>
    </div>
  </div>

  <Ledger records={ui.ledger} />

  <div class="log">
    <h3>Event log</h3>
    <pre>{#if ui.log.length === 0}ready{/if}{#each ui.log as line}{new Date(line.at).toTimeString().slice(0, 8)}  {line.text}
{/each}</pre>
  </div>
</div>
