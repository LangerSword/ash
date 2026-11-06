<script lang="ts">
  import type { WorldConfig } from "../lib/types";

  type Props = {
    config: WorldConfig | null;
    onContinue: () => void;
  };

  let { config, onContinue }: Props = $props();
</script>

<div class="step">
  <div class="step-head">
    <span class="label">First run · 3 of 4</span>
    <h1>Sign in with World</h1>
  </div>

  <p class="body">
    World proves a human is present when a container is <em>unsealed</em>. It is not needed to seal, to
    read the ledger, or to break the loop. The app stores no World credentials; the relying-party key
    lives on the local service.
  </p>

  <dl class="rows">
    <div class="row">
      <dt>app</dt>
      <dd>{config?.app_id ?? "unavailable"}</dd>
    </div>
    <div class="row">
      <dt>rp</dt>
      <dd>{config?.rp_id ?? "unavailable"}</dd>
    </div>
    <div class="row">
      <dt>action</dt>
      <dd>{config?.action ?? "unseal"}</dd>
    </div>
    <div class="row">
      <dt>signing key</dt>
      <dd data-ok={config?.has_key ? 1 : 0}>{config?.has_key ? "present" : "missing"}</dd>
    </div>
  </dl>

  <p class="sandbox">
    <span>SANDBOX</span> Proofs from this build are World ID sandbox credentials. They are not a
    production identity, and the app says so wherever they appear.
  </p>

  <p class="body dim">
    You will scan a QR with the World app at unseal time. Continuing does not enable or disable
    unsealing; it only closes this explanation.
  </p>

  <div class="foot">
    <button class="btn" data-kind="primary" onclick={onContinue}>Continue</button>
  </div>
</div>

<style>
  .step {
    max-width: 620px;
    margin: 0 auto;
    padding: 56px 24px 40px;
    display: grid;
    gap: 22px;
  }

  h1 {
    font-size: 22px;
    font-weight: 500;
    letter-spacing: -0.01em;
    margin-top: 6px;
  }

  .body {
    font-size: 13px;
    color: var(--muted);
    max-width: 58ch;
  }

  .body em {
    color: var(--text);
    font-style: normal;
  }

  .dim {
    color: var(--dim);
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
    grid-template-columns: 110px 1fr;
    gap: 12px;
    padding: 10px 14px;
    background: var(--surface);
    font-size: 12px;
  }

  dt {
    color: var(--dim);
  }

  dd {
    margin: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  dd[data-ok="1"] {
    color: var(--signal);
  }

  .sandbox {
    font-size: 12px;
    color: var(--muted);
    border: 1px solid #4a3a18;
    background: #151007;
    border-radius: var(--radius);
    padding: 12px 14px;
  }

  .sandbox span {
    color: var(--amber);
    letter-spacing: 0.1em;
    margin-right: 8px;
  }

  .foot {
    border-top: 1px solid var(--border);
    padding-top: 18px;
  }
</style>
