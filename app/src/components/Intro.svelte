<script lang="ts">
  import { onMount } from "svelte";
  import gsap from "gsap";
  import { api } from "../lib/api";
  import { buildIntroFrames, INTRO_FPS } from "../lib/intro-frames";

  type Props = {
    reduced?: boolean;
    onDone: () => void;
    onBoard: (note: string) => void;
  };

  let { reduced = false, onDone, onBoard }: Props = $props();

  let root: HTMLDivElement;
  let boxPath: SVGPathElement;
  let lid: SVGGElement;
  let burnRect: SVGRectElement;
  let burnLine: SVGLineElement;
  let mark: SVGTextElement;
  let particles: SVGCircleElement[] = [];

  let finished = false;
  let tl: gsap.core.Timeline | null = null;

  const TARGETS = Array.from({ length: 18 }, (_, i) => ({
    x: 168 + (i / 17) * 64,
    y: 176 + (i % 3) * 2,
  }));

  function finish(immediate = false) {
    if (finished) return;
    finished = true;
    if (tl) {
      tl.kill();
      tl = null;
    }
    if (root) {
      gsap.set(root.querySelectorAll("[data-particle]"), { opacity: 0 });
      gsap.set([boxPath, lid], { opacity: 0 });
      gsap.set(mark, { opacity: 1, letterSpacing: "0.32em", y: 0 });
    }
    window.setTimeout(() => onDone(), immediate ? 0 : 180);
  }

  function skip(e: Event) {
    e.preventDefault();
    finish();
  }

  onMount(() => {
    // Fire the same beats at the board. If the endpoint is missing, say so once.
    api
      .frame(buildIntroFrames(), INTRO_FPS)
      .then((r) => onBoard(`board intro · ${r.frames} frames @ ${r.fps} fps`))
      .catch(() => onBoard("Board intro unavailable (no /frame); shown in-app only."));

    if (reduced) {
      gsap.set([boxPath, lid], { opacity: 0 });
      gsap.set(particles, { opacity: 0 });
      gsap.fromTo(mark, { opacity: 0 }, { opacity: 1, duration: 0.4, ease: "power1.out" });
      const t = window.setTimeout(() => finish(true), 900);
      return () => window.clearTimeout(t);
    }

    const len = boxPath.getTotalLength();
    gsap.set(boxPath, { strokeDasharray: len, strokeDashoffset: len });
    gsap.set(mark, { opacity: 0, letterSpacing: "0.6em" });
    gsap.set(particles, { opacity: 0 });
    gsap.set(burnRect, { attr: { width: 0 } });

    tl = gsap.timeline({
      defaults: { ease: "power2.out" },
      onComplete: () => finish(),
    });

    tl.to(boxPath, { strokeDashoffset: 0, duration: 0.8, ease: "power2.inOut" }, 0)
      .to(lid, { rotate: -62, svgOrigin: "120 58", duration: 0.5 }, 0.78)
      .to(burnRect, { attr: { width: 124 }, duration: 0.95, ease: "none" }, 1.3)
      .to(burnLine, { attr: { x1: 244, x2: 244 }, duration: 0.95, ease: "none" }, 1.3)
      .to([boxPath, lid], { opacity: 0.12, duration: 0.35 }, 1.8)
      .to([boxPath, lid], { opacity: 0, duration: 0.3 }, 2.0)
      .to(burnLine, { opacity: 0, duration: 0.25 }, 2.2)
      .to(particles, { opacity: 1, duration: 0.12, stagger: 0.012 }, 1.85)
      .to(
        particles,
        {
          attr: { cx: (i: number) => TARGETS[i].x, cy: (i: number) => TARGETS[i].y },
          duration: 0.72,
          stagger: 0.014,
          ease: "power2.inOut",
        },
        1.95,
      )
      .to(particles, { opacity: 0, duration: 0.28 }, 2.68)
      .to(mark, { opacity: 1, letterSpacing: "0.32em", duration: 0.62 }, 2.62)
      .to({}, { duration: 0.3 }, 3.24);

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
      <mask id="burn">
        <rect x="0" y="0" width="400" height="220" fill="white" />
        <rect bind:this={burnRect} x="120" y="40" width="0" height="122" fill="black" />
      </mask>
    </defs>

    <g mask="url(#burn)">
      <path
        bind:this={boxPath}
        d="M120 58 H240 V144 H120 Z"
        fill="none"
        stroke="#e8e8e8"
        stroke-width="1"
      />
      <g bind:this={lid}>
        <path d="M120 58 H240" fill="none" stroke="#e8e8e8" stroke-width="1" />
        <path d="M120 58 L106 48" fill="none" stroke="#5f5f66" stroke-width="1" />
      </g>
      <path d="M120 92 H240" fill="none" stroke="#2e2e33" stroke-width="1" stroke-dasharray="2 3" />
    </g>

    <line
      bind:this={burnLine}
      x1="120"
      y1="46"
      x2="120"
      y2="156"
      stroke="#ffb020"
      stroke-width="1.5"
      opacity="0.9"
    />

    {#each TARGETS as _, i}
      <circle
        bind:this={particles[i]}
        data-particle
        cx={120 + (i % 6) * 20}
        cy={60 + Math.floor(i / 6) * 22}
        r="1.4"
        fill="#8a8a8a"
      />
    {/each}

    <text
      bind:this={mark}
      x="180"
      y="200"
      text-anchor="middle"
      fill="#e8e8e8"
      font-family="ui-monospace, SFMono-Regular, Menlo, monospace"
      font-size="40"
      letter-spacing="8"
    >
      ASH
    </text>
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
    color: var(--dim);
  }

  @media (prefers-reduced-motion: reduce) {
    .hint {
      opacity: 0.6;
    }
  }
</style>
