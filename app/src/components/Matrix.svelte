<script lang="ts">
  import { onMount } from "svelte";
  import type { Mode } from "../lib/types";
  import { STATE_ART, boardState } from "../lib/state-frames";

  type Props = {
    mode: Mode;
    amberSince?: number;
    deadlineMs?: number;
    label?: string;
    scale?: "full" | "mini";
  };

  let { mode, amberSince = 0, deadlineMs = 5000, label = "13 × 8 · the seal", scale = "full" }: Props = $props();

  let now = $state(0);
  let mounted = $state(false);

  onMount(() => {
    mounted = true;
    now = performance.now();
    const id = window.setInterval(() => {
      now = performance.now();
    }, 66);
    return () => window.clearInterval(id);
  });

  // The deadline is a clock, so amber is drawn from the real remaining time;
  // every other state is a fixed film from the shared art.
  const cells = $derived.by<boolean[]>(() => {
    if (mode === "amber") {
      const at = amberSince || now;
      const left = Math.max(0, 1 - (now - at) / Math.max(1, deadlineMs));
      const bars = Math.ceil(left * 13);
      const out = new Array<boolean>(104).fill(false);
      for (let c = 13 - bars; c < 13; c += 1) for (let r = 0; r < 8; r += 1) out[r * 13 + c] = true;
      return out;
    }
    const art = STATE_ART[boardState(mode)];
    const idx = mounted ? Math.floor(now / (1000 / art.fps)) % art.frames.length : 0;
    const frame = art.frames[idx];
    return Array.from({ length: 104 }, (_, i) => frame[i] === "1");
  });
</script>

<div class="matrix-wrap">
  <div class="matrix" data-mode={mode} data-scale={scale} aria-hidden="true">
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
    gap: 10px;
  }

  .matrix {
    display: grid;
    grid-template-columns: repeat(13, 1fr);
    gap: 2px;
    width: 100%;
    max-width: 400px;
    aspect-ratio: 13 / 8;
    padding: 7px;
    border: 1px solid var(--border);
    background: #0d0a08;
    border-radius: var(--radius);
  }

  .matrix[data-scale="mini"] {
    max-width: 92px;
    gap: 1px;
    padding: 4px;
  }

  .cell {
    background: #1a1512;
    border-radius: 1px;
  }

  .matrix[data-mode="armed"] .cell[data-on="1"],
  .matrix[data-mode="unsealed"] .cell[data-on="1"] {
    background: var(--signal);
  }

  .matrix[data-mode="amber"] .cell[data-on="1"],
  .matrix[data-mode="wipe"] .cell[data-on="1"] {
    background: var(--amber);
  }

  .matrix[data-mode="tampered"] .cell[data-on="1"] {
    background: var(--ember);
  }

  .matrix[data-mode="offline"] .cell {
    background: #14100d;
  }

  .matrix-meta {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    font-size: 11px;
    letter-spacing: 0.04em;
    color: var(--dim);
  }

  .matrix[data-scale="mini"] + .matrix-meta {
    display: none;
  }

  .matrix-meta [data-mode="amber"] { color: var(--amber); }
  .matrix-meta [data-mode="tampered"] { color: var(--ember); }
  .matrix-meta [data-mode="armed"],
  .matrix-meta [data-mode="unsealed"] { color: var(--signal); }
</style>
