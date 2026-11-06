<script lang="ts">
  import type { DeviceSnapshot, ServiceInfo } from "../lib/types";
  import { deviceHint } from "../lib/failures";

  type Props = {
    device: DeviceSnapshot | null;
    service: ServiceInfo | null;
    busy: string;
    onContinue: () => void;
    onStartBoard: () => void;
    onInstallUdev: () => void;
  };

  let { device, service, busy, onContinue, onStartBoard, onInstallUdev }: Props = $props();

  const hint = $derived(deviceHint(device?.state ?? "starting", device?.detail ?? ""));
  const boardFound = $derived(
    device?.state === "ready" || device?.state === "forwarded" || device?.state === "unauthorized",
  );
</script>

<div class="step">
  <div class="step-head">
    <span class="label">First run · 2 of 4</span>
    <h1>Device check</h1>
  </div>

  <dl class="rows">
    <div class="row">
      <dt>USB link</dt>
      <dd>
        <span data-ok={boardFound ? 1 : 0}>
          {device?.state === "ready"
            ? `ready · ${device.serial}`
            : device?.state === "forwarded"
              ? `board found · ${device.serial}`
              : device?.state === "unauthorized"
                ? "not authorised"
                : device?.state === "absent"
                  ? "no board"
                  : (device?.state ?? "starting")}
        </span>
      </dd>
    </div>
    <div class="row">
      <dt>Board app</dt>
      <dd>
        <span data-ok={device?.state === "ready" ? 1 : 0}>
          {device?.state === "ready" ? "answering on the forwarded port" : "not answering"}
        </span>
      </dd>
    </div>
    <div class="row">
      <dt>Local service</dt>
      <dd>
        <span data-ok={service?.mode !== "unavailable" ? 1 : 0}>
          {service?.mode === "attached"
            ? `attached · ${service.base}`
            : service?.mode === "spawned"
              ? `spawned · ${service.base}`
              : "unavailable"}
        </span>
      </dd>
    </div>
  </dl>

  {#if hint.line}
    <p class="hint" data-kind={device?.state === "unauthorized" || device?.state === "error" ? "warn" : "note"}>
      {hint.line}
    </p>
  {/if}

  <div class="actions">
    {#if device?.state === "absent"}
      <span class="quiet">Connect the UNO Q over USB. It appears within two seconds.</span>
    {/if}
    {#if device?.state === "forwarded"}
      <button class="btn" disabled={busy !== ""} onclick={onStartBoard} data-busy={busy === "board" ? 1 : 0}>
        Start board app
      </button>
    {/if}
    {#if device?.state === "unauthorized"}
      <span class="quiet">Allow USB debugging on the board, then reconnect.</span>
    {/if}
    <button class="btn" onclick={onInstallUdev}>Install udev rule</button>
  </div>

  <div class="caveats">
    <p><span>Without a board</span> the ledger is readable and the controls stay disabled.</p>
    <p><span>Without a network</span> the 0G tier is unavailable. The seal fails closed, and says so before you act.</p>
  </div>

  <div class="foot">
    <button class="btn" data-kind="primary" onclick={onContinue}>Continue</button>
    <span class="quiet">You can finish setup without the board.</span>
  </div>
</div>

<style>
  .step {
    max-width: 620px;
    margin: 0 auto;
    padding: 56px 24px 40px;
    display: grid;
    gap: 26px;
  }

  h1 {
    font-size: 22px;
    font-weight: 500;
    letter-spacing: -0.01em;
    margin-top: 6px;
  }

  .rows {
    display: grid;
    gap: 1px;
    background: var(--border);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    margin: 0;
  }

  .row {
    display: grid;
    grid-template-columns: 140px 1fr;
    gap: 12px;
    padding: 11px 14px;
    background: var(--surface);
  }

  dt {
    color: var(--dim);
    font-size: 12px;
  }

  dd {
    margin: 0;
    font-size: 12px;
  }

  dd span[data-ok="1"] {
    color: var(--signal);
  }

  dd span[data-ok="0"] {
    color: var(--muted);
  }

  .hint {
    font-size: 12px;
    color: var(--muted);
    border-left: 1px solid var(--border-strong);
    padding-left: 12px;
  }

  .hint[data-kind="warn"] {
    color: var(--amber);
    border-color: var(--amber);
  }

  .actions {
    display: flex;
    gap: 8px;
    align-items: center;
    flex-wrap: wrap;
  }

  .caveats {
    display: grid;
    gap: 6px;
    border-top: 1px solid var(--border);
    padding-top: 16px;
    font-size: 12px;
    color: var(--muted);
  }

  .caveats span {
    color: var(--text);
  }

  .foot {
    display: flex;
    align-items: center;
    gap: 14px;
    border-top: 1px solid var(--border);
    padding-top: 18px;
  }

  .quiet {
    font-size: 11px;
    color: var(--dim);
  }
</style>
