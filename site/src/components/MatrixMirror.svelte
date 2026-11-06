<script lang="ts">
  import { onMount } from "svelte";
  import { ui } from "../lib/store.svelte";

  let now = $state(0);

  onMount(() => {
    // 15 fps is enough for a 13x8 matrix and keeps the main thread quiet.
    now = performance.now();
    const id = setInterval(() => {
      now = performance.now();
    }, 66);
    return () => clearInterval(id);
  });

  type Mode = "armed" | "amber" | "tampered" | "unsealed" | "offline";

  const mode = $derived.by<Mode>(() => {
    const d = ui.device;
    if (!d || d.state !== "ready") return "offline";
    const s = ui.status;
    if (!s) return "offline";
    if (s.state === 3) return "tampered";
    if (s.state === 1) return s.amber ? "amber" : "armed";
    return "offline";
  });

  const cells = $derived.by<boolean[]>(() => {
    const out = new Array<boolean>(104).fill(false);
    const t = now;
    if (mode === "offline") return out;

    if (mode === "armed") {
      const phase = (t % 4000) / 4000;
      const level = 1 + Math.round(3.5 * (1 + Math.sin(phase * Math.PI * 2)));
      for (let r = 8 - level; r < 8; r++) for (let c = 0; c < 13; c++) out[r * 13 + c] = true;
      return out;
    }

    if (mode === "amber") {
      const elapsed = ui.amberSince ? t - ui.amberSince : 0;
      const left = Math.max(0, 1 - elapsed / 5000);
      const bars = Math.ceil(left * 13);
      for (let c = 13 - bars; c < 13; c++) for (let r = 0; r < 8; r++) out[r * 13 + c] = true;
      return out;
    }

    if (mode === "tampered") {
      if (Math.floor(t / 400) % 2 === 0) {
        for (let i = 0; i < 8; i++) {
          out[i * 13 + i] = true;
          out[i * 13 + (7 - i)] = true;
        }
      }
      return out;
    }

    // unsealed: diamond
    for (let r = 0; r < 8; r++) {
      for (let c = 0; c < 13; c++) {
        if (Math.abs(r - 3.5) + Math.abs(c - 6) < 3.2) out[r * 13 + c] = true;
      }
    }
    return out;
  });
</script>

<div class="matrix-wrap">
  <div class="matrix" data-mode={mode} aria-hidden="true">
    {#each cells as on}
      <div class="cell" data-on={on ? 1 : 0}></div>
    {/each}
  </div>
  <div class="matrix-legend">
    <span>13 × 8 · device mirror</span>
    <span>{mode}</span>
  </div>
</div>
