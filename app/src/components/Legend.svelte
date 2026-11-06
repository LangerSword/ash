<script lang="ts">
  import Matrix from "./Matrix.svelte";
  import type { Mode } from "../lib/types";

  type Props = {
    onDone: () => void;
  };

  let { onDone }: Props = $props();

  const symbols: Array<{ mode: Mode; name: string; meaning: string }> = [
    { mode: "armed", name: "ARMED", meaning: "solid breathing fill · the seal is live" },
    { mode: "amber", name: "TIER 1 / DEADLINE", meaning: "amber bars draining right to left · 0G is deciding" },
    { mode: "wipe", name: "WIPE", meaning: "falling dots · the key is being destroyed" },
    { mode: "tampered", name: "TAMPERED", meaning: "red X · the key is gone" },
    { mode: "unsealed", name: "UNSEALED", meaning: "green diamond · the proof was accepted" },
    { mode: "offline", name: "OFFLINE", meaning: "blank · no board, or no answer" },
  ];
</script>

<div class="backdrop" role="dialog" aria-modal="true" aria-label="Legend">
  <div class="card">
    <div class="head">
      <span class="label">Legend</span>
      <span class="sub">the matrix speaks six states</span>
    </div>

    <ul>
      {#each symbols as s}
        <li>
          <Matrix mode={s.mode} label="" />
          <div>
            <strong>{s.name}</strong>
            <span>{s.meaning}</span>
          </div>
        </li>
      {/each}
    </ul>

    <div class="foot">
      <button class="btn" data-kind="primary" onclick={onDone}>Got it</button>
      <span class="sub">Reopen this with the ? button.</span>
    </div>
  </div>
</div>

<style>
  .backdrop {
    position: fixed;
    inset: 0;
    z-index: 30;
    display: grid;
    place-items: center;
    background: rgba(8, 8, 10, 0.82);
    backdrop-filter: blur(2px);
    padding: 24px;
  }

  .card {
    width: min(560px, 100%);
    max-height: calc(100vh - 48px);
    overflow-y: auto;
    background: var(--surface);
    border: 1px solid var(--border-strong);
    border-radius: var(--radius);
    padding: 22px;
    display: grid;
    gap: 18px;
  }

  .head {
    display: flex;
    align-items: baseline;
    gap: 12px;
  }

  .sub {
    font-size: 11px;
    color: var(--dim);
  }

  ul {
    list-style: none;
    margin: 0;
    padding: 0;
    display: grid;
    gap: 10px;
  }

  li {
    display: grid;
    grid-template-columns: 76px 1fr;
    gap: 14px;
    align-items: center;
  }

  strong {
    display: block;
    font-size: 12px;
    font-weight: 500;
    letter-spacing: 0.06em;
  }

  li span {
    font-size: 11px;
    color: var(--muted);
  }

  .foot {
    display: flex;
    align-items: center;
    gap: 14px;
    border-top: 1px solid var(--border);
    padding-top: 16px;
  }
</style>
