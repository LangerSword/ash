<script lang="ts">
  import { onMount } from "svelte";
  import { words } from "../lib/words";

  let wrap: HTMLDivElement;
  let svg: SVGSVGElement;

  onMount(() => {
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce) {
      svg.classList.add("drawn", "broken");
      return;
    }
    let killed = false;
    let ctx: { revert: () => void } | null = null;

    void (async () => {
      const gsapMod = await import("gsap");
      const stMod = await import("gsap/ScrollTrigger");
      if (killed) return;
      const gsap = gsapMod.gsap ?? gsapMod.default;
      const ScrollTrigger = stMod.ScrollTrigger ?? stMod.default;
      gsap.registerPlugin(ScrollTrigger);

      ctx = gsap.context(() => {
        const line = svg.querySelector<SVGPathElement>("#wire")!;
        const len = line.getTotalLength();
        gsap.set(line, { strokeDasharray: len, strokeDashoffset: len });

        const tl = gsap.timeline({
          scrollTrigger: {
            trigger: wrap,
            start: "top 75%",
            end: "bottom 60%",
            scrub: 0.6,
            onUpdate: (self) => {
              svg.classList.toggle("broken", self.progress > 0.68);
            },
          },
        });
        tl.to(line, { strokeDashoffset: 0, duration: 1, ease: "none" }, 0)
          .to(".loop-note", { opacity: 1, y: 0, duration: 0.3, stagger: 0.12 }, 0.55);
      }, wrap);
    })();

    return () => {
      killed = true;
      ctx?.revert();
    };
  });
</script>

<section class="loop" id="loop" bind:this={wrap}>
  <div class="copy">
    <h2 use:words>One wire. It is the whole sensor.</h2>
    <p>
      The loop runs through the lid and into the board. The firmware samples it every millisecond. A
      break is not a log entry. It is the end of the key.
    </p>
    <ul>
      <li class="loop-note"><span class="mono">open</span><b>250 ms</b><span>continuous, no debounce</span></li>
      <li class="loop-note"><span class="mono">erase</span><b>874 µs</b><span>eight kilobyte page</span></li>
      <li class="loop-note"><span class="mono">verify</span><b>0xFF</b><span>read back before the state changes</span></li>
    </ul>
  </div>

  <div class="stage">
    <svg bind:this={svg} viewBox="0 0 520 520" role="img" aria-label="A wire loop runs from the case edge, through the lid, to the microcontroller. A break leaves a gap at the board.">
      <g class="case">
        <rect x="128" y="150" width="300" height="250" rx="2" />
        <line x1="128" y1="212" x2="428" y2="212" class="seam" />
        <circle cx="150" cy="181" r="2.4" class="pin" />
        <circle cx="406" cy="181" r="2.4" class="pin" />
      </g>

      <rect x="286" y="286" width="118" height="76" rx="1" class="mcu" />
      <text x="345" y="330" class="label" text-anchor="middle">STM32U585</text>

      <path
        id="wire"
        d="M 12 452 L 92 452 L 92 181 L 150 181 L 300 181 L 300 286"
        fill="none"
        class="wire"
      />

      <g class="break">
        <circle cx="300" cy="238" r="4.5" class="spark" />
        <circle cx="300" cy="238" r="13" class="spark-ring" />
      </g>

      <g class="tags">
        <text x="12" y="482" class="label">loop</text>
        <text x="300" y="470" class="label hot">break</text>
      </g>
    </svg>
    <p class="mono caption">schematic · one conductor, one key</p>
  </div>
</section>

<style>
  .loop {
    max-width: var(--max);
    margin: 0 auto;
    padding: clamp(72px, 12vh, 140px) var(--gutter);
    display: grid;
    grid-template-columns: 0.9fr 1.1fr;
    gap: clamp(28px, 6vw, 88px);
    align-items: center;
    border-top: 1px solid var(--border);
  }

  h2 {
    font-size: clamp(30px, 4vw, 54px);
    line-height: 1.02;
    letter-spacing: -0.02em;
    margin: 0 0 18px;
  }

  .copy p {
    margin: 0 0 32px;
    color: var(--muted);
    font-size: 15px;
    line-height: 1.6;
    max-width: 42ch;
  }

  ul {
    list-style: none;
    margin: 0;
    padding: 0;
    border-top: 1px solid var(--border);
  }

  li {
    display: grid;
    grid-template-columns: 64px 96px 1fr;
    gap: 12px;
    align-items: baseline;
    padding: 12px 0;
    border-bottom: 1px solid var(--border);
    font-size: 13px;
    color: var(--muted);
  }

  .loop-note {
    opacity: 0;
    transform: translateY(10px);
  }

  .mono {
    font-family: var(--mono);
    font-size: 10px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--dim);
  }

  li b {
    font-family: var(--mono);
    font-weight: 400;
    font-size: 12.5px;
    color: var(--text);
  }

  .stage {
    position: relative;
  }

  svg {
    width: 100%;
    height: auto;
    display: block;
  }

  .case rect,
  .case .seam {
    fill: none;
    stroke: var(--border-strong);
    stroke-width: 1.1;
  }

  .case .seam {
    stroke-dasharray: 3 4;
  }

  .pin {
    fill: var(--dim);
  }

  .mcu {
    fill: var(--surface);
    stroke: var(--border-strong);
    stroke-width: 1.1;
  }

  .wire {
    stroke: var(--text);
    stroke-width: 1.4;
    stroke-linecap: square;
  }

  .label {
    fill: var(--dim);
    font-family: var(--mono);
    font-size: 9px;
    letter-spacing: 0.16em;
    text-transform: uppercase;
  }

  .label.hot {
    fill: var(--ember);
  }

  .break {
    opacity: 0;
    transition: opacity 160ms linear;
  }

  .spark {
    fill: var(--ember);
  }

  .spark-ring {
    fill: none;
    stroke: var(--ember);
    stroke-width: 1;
    opacity: 0.4;
  }

  svg.broken .break {
    opacity: 1;
  }

  svg.broken .wire {
    stroke: var(--muted);
  }

  svg.broken .mcu {
    stroke: var(--ember);
  }

  .caption {
    position: absolute;
    right: 0;
    bottom: -18px;
    margin: 0;
  }

  @media (max-width: 900px) {
    .loop {
      grid-template-columns: 1fr;
      padding-top: 64px;
    }
    .stage {
      order: -1;
    }
    li {
      grid-template-columns: 56px 84px 1fr;
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .loop-note {
      opacity: 1;
      transform: none;
    }
  }
</style>
