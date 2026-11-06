<script lang="ts">
  import { onMount } from "svelte";
  import type { Mode } from "../lib/types";

  type Props = {
    mode: Mode;
    amberSince?: number;
    deadlineMs?: number;
    label?: string;
  };

  let { mode, amberSince = 0, deadlineMs = 5000, label = "13 × 8 · device mirror" }: Props = $props();

  let now = $state(0);

  onMount(() => {
    now = performance.now();
    const id = window.setInterval(() => {
      now = performance.now();
    }, 66);
    return () => window.clearInterval(id);
  });

  const cells = $derived.by<boolean[]>(() => {
    const out = new Array<boolean>(104).fill(false);
    const t = now;

    if (mode === "offline") return out;

    if (mode === "armed") {
      const phase = (t % 4000) / 4000;
      const level = 1 + Math.round(3.5 * (1 + Math.sin(phase * Math.PI * 2)));
      for (let r = 8 - level; r < 8; r += 1) for (let c = 0; c < 13; c += 1) out[r * 13 + c] = true;
      return out;
    }

    if (mode === "amber") {
      const elapsed = amberSince ? t - amberSince : 0;
      const left = Math.max(0, 1 - elapsed / Math.max(1, deadlineMs));
      const bars = Math.ceil(left * 13);
      for (let c = 13 - bars; c < 13; c += 1) for (let r = 0; r < 8; r += 1) out[r * 13 + c] = true;
      return out;
    }

    if (mode === "tampered") {
      if (Math.floor(t / 400) % 2 === 0) {
        for (let i = 0; i < 8; i += 1) {
          out[i * 13 + i] = true;
          out[i * 13 + (7 - i)] = true;
        }
      }
      return out;
    }

    if (mode === "wipe") {
      for (let i = 0; i < 7; i += 1) {
        const y = Math.floor((t / 90 + i * 3) % 8);
        out[y * 13 + Math.floor(1 + i * 1.7)] = true;
      }
      return out;
    }

    for (let r = 0; r < 8; r += 1) {
      for (let c = 0; c < 13; c += 1) {
        if (Math.abs(r - 3.5) + Math.abs(c - 6) < 3.2) out[r * 13 + c] = true;
      }
    }
    return out;
  });
</script>

<div class="matrix-wrap">
  <div class="matrix" data-mode={mode} aria-hidden="true">
    {#each cells as on, i}
      <div class="cell" data-on={on ? 1 : 0} data-i={i}></div>
    {/each}
  </div>
  <div class="matrix-meta">
    <span>{label}</span>
    <span data-mode={mode}>{mode}</span>
  </div>
</div>

<style>
  .matrix-wrap {
    display: grid;
    gap: 8px;
  }

  .matrix {
    display: grid;
    grid-template-columns: repeat(13, 1fr);
    gap: 2px;
    width: 100%;
    max-width: 400px;
    aspect-ratio: 13 / 8;
    padding: 6px;
    border: 1px solid var(--border);
    background: #08080a;
    border-radius: var(--radius);
  }

  .cell {
    background: #131316;
    border-radius: 1px;
  }

  .matrix[data-mode="armed"] .cell[data-on="1"] {
    background: var(--signal);
  }

  .matrix[data-mode="amber"] .cell[data-on="1"] {
    background: var(--amber);
  }

  .matrix[data-mode="tampered"] .cell[data-on="1"] {
    background: var(--alert);
  }

  .matrix[data-mode="unsealed"] .cell[data-on="1"],
  .matrix[data-mode="wipe"] .cell[data-on="1"] {
    background: var(--signal);
  }

  .matrix[data-mode="offline"] .cell {
    background: #101012;
  }

  .matrix-meta {
    display: flex;
    justify-content: space-between;
    font-size: 11px;
    letter-spacing: 0.04em;
    color: var(--dim);
  }

  .matrix-meta [data-mode="amber"] {
    color: var(--amber);
  }

  .matrix-meta [data-mode="tampered"] {
    color: var(--alert);
  }

  .matrix-meta [data-mode="armed"],
  .matrix-meta [data-mode="unsealed"] {
    color: var(--signal);
  }
</style>
