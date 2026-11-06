<script lang="ts">
  import Connection from "./Connection.svelte";
  import { connection } from "../lib/connect";
  import type { DeviceSnapshot, ServiceInfo } from "../lib/types";

  type Props = {
    device: DeviceSnapshot | null;
    service: ServiceInfo | null;
    busy: string;
    udevOk: boolean;
    onContinue: () => void;
    onAction: (kind: "start_board" | "udev" | "retry") => void;
  };

  let { device, service, busy, udevOk, onContinue, onAction }: Props = $props();

  const conn = $derived(connection(device, service, udevOk));
</script>

<div class="step">
  <div class="step-head">
    <span class="label">First run · 2 of 4</span>
    <h1>Device check</h1>
  </div>

  <Connection {conn} {busy} onAction={onAction} />

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
