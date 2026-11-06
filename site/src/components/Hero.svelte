<script lang="ts">
  import { onMount } from "svelte";
  import { gsap } from "gsap";
  import { prefersReduced } from "../lib/anim";
  import { stateLabel, ui } from "../lib/store.svelte";

  let root: HTMLElement;

  onMount(() => {
    if (prefersReduced()) return;
    const ctx = gsap.context(() => {
      const tl = gsap.timeline({ defaults: { ease: "power2.out" } });
      tl.from(".line > span", { yPercent: 115, duration: 0.6, stagger: 0.07 })
        .from(".sub", { opacity: 0, y: 8, duration: 0.4 }, "-=0.25")
        .from(".fact", { opacity: 0, y: 8, duration: 0.35, stagger: 0.06 }, "-=0.2");
    }, root);
    return () => ctx.revert();
  });
</script>

<header class="site-header">
  <div class="wordmark">ASH</div>
  <div class="meta">
    <span>ETHGlobal Mumbai · 2026</span>
    <span class="chip" data-state={stateLabel()} aria-live="polite">{stateLabel()}</span>
  </div>
</header>

<section class="hero" bind:this={root}>
  <div class="kicker">Tamper-responsive seal</div>
  <h1>
    <span class="line"><span>A seal that destroys</span></span>
    <span class="line"><span>the data if you open it.</span></span>
  </h1>
  <p class="sub">The key lives in the chip. Cut the loop and it is gone in a millisecond.</p>

  <div class="facts">
    <div class="fact"><b>1 321 µs</b><span>wipe + read-back</span></div>
    <div class="fact"><b>2.05 s</b><span>0G decision, p50</span></div>
    <div class="fact"><b>5 000 ms</b><span>deadline</span></div>
    <div class="fact">
      <b>{ui.device?.state === "ready" ? "connected" : "no board"}</b><span>UNO Q</span>
    </div>
  </div>
</section>
