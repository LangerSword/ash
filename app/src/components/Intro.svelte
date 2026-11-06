<script lang="ts">
  import { onMount } from "svelte";
  import gsap from "gsap";

  type Props = {
    reduced?: boolean;
    onDone: () => void;
    onBoard: (note: string) => void;
  };

  let { reduced = false, onDone, onBoard }: Props = $props();

  let root: HTMLDivElement;
  let burnRect: SVGRectElement;
  let burnEdge: SVGLineElement;
  let mark: SVGTextElement;
  let embers: SVGCircleElement[] = [];

  let finished = false;
  let tl: gsap.core.Timeline | null = null;

  // embers start along the word and fall away from the front
  const EMBERS = Array.from({ length: 16 }, (_, i) => ({
    x: 44 + i * 18,
    y: 96 + (i % 4) * 12,
  }));

  function finish(immediate = false) {
    if (finished) return;
    finished = true;
    if (tl) {
      tl.kill();
      tl = null;
    }
    if (root) {
      gsap.set(embers, { opacity: 0 });
      gsap.set(mark, { opacity: 1, y: 0, letterSpacing: "0" });
      gsap.set(burnRect, { attr: { width: 0 } });
    }
    window.setTimeout(() => onDone(), immediate ? 0 : 160);
  }

  function skip(e: Event) {
    e.preventDefault();
    finish();
  }

  onMount(() => {
    // The board plays the same film; Rust fires it the first time the board answers.
    onBoard("board signature armed");

    if (reduced) {
      gsap.set(embers, { opacity: 0 });
      gsap.fromTo(mark, { opacity: 0 }, { opacity: 1, duration: 0.4, ease: "power1.out" });
      const t = window.setTimeout(() => finish(true), 900);
      return () => window.clearTimeout(t);
    }

    gsap.set(embers, { opacity: 0 });
    gsap.set(mark, { opacity: 0, y: 10, letterSpacing: "0.06em" });
    gsap.set(burnRect, { attr: { width: 0 } });
    gsap.set(burnEdge, { opacity: 0 });

    tl = gsap.timeline({ defaults: { ease: "power2.out" }, onComplete: () => finish() });

    tl.to(mark, { opacity: 1, y: 0, letterSpacing: "0em", duration: 0.75 }, 0)
      .to({}, { duration: 0.25 }, 0.75)
      // burn: the front crosses the word left to right
      .to(burnEdge, { opacity: 0.6, duration: 0.12 }, 0.95)
      .to(burnRect, { attr: { width: 336 }, duration: 1.35, ease: "none" }, 1.0)
      .to(burnEdge, { attr: { x1: 356, x2: 356 }, duration: 1.35, ease: "none" }, 1.0)
      .to(embers, { opacity: 1, duration: 0.1, stagger: { each: 0.07, from: "start" } }, 1.02)
      .to(
        embers,
        {
          attr: { cy: (i: number) => EMBERS[i].y + 70, cx: (i: number) => EMBERS[i].x + 10 },
          duration: 0.9,
          stagger: 0.035,
          ease: "power1.in",
        },
        1.1,
      )
      .to(embers, { opacity: 0, duration: 0.35 }, 1.85)
      .to(burnEdge, { opacity: 0, duration: 0.2 }, 2.3)
      // reform: the mask retreats, the word comes back right to left
      .to(burnRect, { attr: { width: 0 }, duration: 0.85, ease: "power2.inOut" }, 2.55)
      .to({}, { duration: 0.35 }, 3.45);

    const keys = (e: KeyboardEvent) => {
      if (e.key === "Escape" || e.key === "Enter" || e.key === " ") finish();
    };
    window.addEventListener("keydown", keys);
    return () => {
      window.removeEventListener("keydown", keys);
      if (tl) tl.kill();
    };
  });
</script>

<div
  class="intro"
  bind:this={root}
  role="presentation"
  onclick={skip}
  onkeydown={(e) => {
    if (e.key === "Escape") finish();
  }}
>
  <svg viewBox="0 0 360 220" aria-hidden="true">
    <defs>
      <mask id="ash-burn">
        <rect x="0" y="0" width="360" height="220" fill="white" />
        <rect bind:this={burnRect} x="12" y="30" width="0" height="150" fill="black" />
      </mask>
    </defs>

    <g mask="url(#ash-burn)">
      <text
        bind:this={mark}
        x="180"
        y="132"
        text-anchor="middle"
        fill="#efe9dd"
        font-family="Cormorant, 'EB Garamond', Georgia, serif"
        font-weight="300"
        font-size="96"
      >
        Ash
      </text>
    </g>

    <line
      bind:this={burnEdge}
      x1="12"
      y1="34"
      x2="12"
      y2="152"
      stroke="#d4442a"
      stroke-width="1"
      opacity="0"
    />

    {#each EMBERS as e, i}
      <circle
        bind:this={embers[i]}
        data-ember
        cx={e.x}
        cy={e.y}
        r="1.3"
        fill="#d4442a"
      />
    {/each}
  </svg>

  <div class="hint">click to skip</div>
</div>

<style>
  .intro {
    position: fixed;
    inset: 0;
    z-index: 40;
    display: grid;
    place-content: center;
    justify-items: center;
    background: var(--bg);
    cursor: pointer;
  }

  svg {
    width: min(78vw, 560px);
    height: auto;
  }

  .hint {
    margin-top: 18px;
    font-size: 11px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--muted);
  }
</style>
