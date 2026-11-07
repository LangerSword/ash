<script lang="ts">
  import { onMount } from "svelte";

  let wrap: HTMLDivElement;
  let acts: HTMLDivElement[] = [];

  const data = [
    {
      k: "01",
      t: "Cut",
      body: "The loop opens. No network, no host, no model. The MCU erases the key and reads the page back.",
      facts: ["874 µs erase, 1.32 ms with read-back", "0 network calls", "TAMPERED, terminal"],
    },
    {
      k: "02",
      t: "Bend",
      body: "An ambiguous event. The MCU goes amber and asks 0G: handling or intrusion. Silence means wipe.",
      facts: ["5 000 ms deadline", "2.05 s median decision", "fails closed"],
    },
    {
      k: "03",
      t: "Ask",
      body: "A human wants in. A World ID proof, then a 0G release decision. Deny, timeout, cancel: no key.",
      facts: ["proof verified server-side", "nullifier bound to one container", "UNSEAL_DENIED is recorded"],
    },
  ];

  onMount(() => {
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce) return;

    let killed = false;
    let mm: { revert: () => void } | null = null;

    void (async () => {
      const gsapMod = await import("gsap");
      const stMod = await import("gsap/ScrollTrigger");
      if (killed) return;
      const gsap = gsapMod.gsap ?? gsapMod.default;
      const ScrollTrigger = stMod.ScrollTrigger ?? stMod.default;
      gsap.registerPlugin(ScrollTrigger);

      mm = gsap.matchMedia();

      // Desktop: pin the section and scrub through the three responses.
      mm.add("(min-width: 861px)", () => {
        gsap.set(acts.slice(1), { autoAlpha: 0, y: 40 });
        const tl = gsap.timeline({
          scrollTrigger: {
            trigger: wrap,
            start: "top top",
            end: "+=2400",
            pin: true,
            scrub: 0.6,
            anticipatePin: 1,
          },
        });
        acts.forEach((el, i) => {
          if (i === 0) return;
          tl.to(acts[i - 1], { autoAlpha: 0, y: -40, duration: 0.6 }, i - 0.1)
            .to(el, { autoAlpha: 1, y: 0, duration: 0.6 }, i - 0.1);
        });
        return () => {
          gsap.set(acts, { clearProps: "all" });
        };
      });

      // Mobile: no pin, no scrub. Each response enters once as it reaches the viewport.
      mm.add("(max-width: 860px)", () => {
        gsap.set(acts, { autoAlpha: 0, y: 26 });
        acts.forEach((el) => {
          gsap.to(el, {
            autoAlpha: 1,
            y: 0,
            duration: 0.6,
            ease: "power2.out",
            scrollTrigger: { trigger: el, start: "top 86%", once: true },
          });
        });
        return () => {
          gsap.set(acts, { clearProps: "all" });
        };
      });
    })();

    return () => {
      killed = true;
      mm?.revert();
    };
  });
</script>

<section class="tiers" bind:this={wrap} id="how">
  <div class="sticky">
    <div class="rail">
      <div class="rail-head">
        <span class="mono">three responses, one device</span>
        <h2>It does not guess.<br />It decides how long to hope.</h2>
      </div>

      <div class="stage">
        {#each data as a, i}
          <div class="act" bind:this={acts[i]}>
            <div class="act-copy">
              <span class="num mono">{a.k}</span>
              <h3>{a.t}</h3>
              <p>{a.body}</p>
            </div>
            <ul class="facts">
              {#each a.facts as f}
                <li class="mono">{f}</li>
              {/each}
            </ul>
          </div>
        {/each}
        <div class="rule" aria-hidden="true"></div>
      </div>
    </div>
  </div>
</section>

<style>
  .tiers {
    border-top: 1px solid var(--border);
    background: linear-gradient(180deg, rgba(255, 90, 31, 0.03), transparent 40%);
  }
  .sticky {
    height: 100dvh;
    display: flex;
    align-items: center;
  }
  .rail {
    width: 100%;
    max-width: var(--max);
    margin: 0 auto;
    padding: 0 var(--gutter);
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: clamp(24px, 6vw, 96px);
    align-items: center;
  }
  .rail-head h2 {
    font-size: clamp(28px, 3.4vw, 44px);
    line-height: 1.06;
    letter-spacing: -0.03em;
    margin: 14px 0 0;
    font-weight: 500;
  }
  .mono {
    font-family: var(--mono);
    font-size: 10.5px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--dim);
  }
  .stage {
    position: relative;
    min-height: 280px;
    display: grid;
    align-items: center;
  }
  .act {
    grid-area: 1 / 1;
    display: grid;
    gap: 26px;
    align-content: center;
  }
  .num {
    color: var(--ember);
    display: block;
    margin-bottom: 6px;
  }
  h3 {
    font-size: clamp(40px, 6vw, 72px);
    line-height: 0.95;
    letter-spacing: -0.04em;
    margin: 0 0 10px;
    font-weight: 500;
  }
  .act p {
    margin: 0;
    max-width: 42ch;
    color: var(--muted);
    font-size: 15px;
    line-height: 1.55;
  }
  .facts {
    list-style: none;
    margin: 0;
    padding: 0;
    display: grid;
    gap: 0;
    border-top: 1px solid var(--border);
  }
  .facts li {
    padding: 10px 0;
    border-bottom: 1px solid var(--border);
    color: var(--text);
    font-size: 11.5px;
    letter-spacing: 0.06em;
  }
  .rule {
    position: absolute;
    left: -28px;
    top: 0;
    bottom: 0;
    width: 1px;
    background: var(--border);
  }
  @media (max-width: 860px) {
    .sticky {
      height: auto;
      min-height: 0;
    }
    .rail {
      grid-template-columns: 1fr;
      padding-top: 56px;
      padding-bottom: 56px;
    }
    .stage {
      min-height: 0;
      display: block;
    }
    .act {
      position: static;
      margin-top: 40px;
    }
    .rule {
      display: none;
    }
  }
</style>
