<script lang="ts">
  import { onMount } from "svelte";

  let canvas: HTMLCanvasElement;
  let state = $state<"sealed" | "burning" | "ash">("sealed");
  let reduced = false;

  type Seg = { x1: number; y1: number; x2: number; y2: number; at: number };
  type P = { x: number; y: number; vx: number; vy: number; life: number; max: number; r: number };

  onMount(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    reduced = mq.matches;
    const ctx = canvas.getContext("2d")!;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    let segs: Seg[] = [];
    let parts: P[] = [];
    let raf = 0;
    let start = 0;
    let W = 0;
    let H = 0;

    function build() {
      const rect = canvas.getBoundingClientRect();
      W = rect.width;
      H = rect.height;
      canvas.width = Math.round(W * dpr);
      canvas.height = Math.round(H * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      const x = W * 0.2;
      const y = H * 0.34;
      const w = W * 0.6;
      const h = H * 0.4;
      const lid = h * 0.26;
      segs = [];
      const push = (x1: number, y1: number, x2: number, y2: number, delay: number) => {
        const len = Math.hypot(x2 - x1, y2 - y1);
        const n = Math.max(1, Math.round(len / 5));
        for (let i = 0; i < n; i++) {
          const t0 = i / n;
          const t1 = (i + 1) / n;
          segs.push({
            x1: x1 + (x2 - x1) * t0,
            y1: y1 + (y2 - y1) * t0,
            x2: x1 + (x2 - x1) * t1,
            y2: y1 + (y2 - y1) * t1,
            at: delay + t0 * 0.32 + Math.random() * 0.18,
          });
        }
      };
      // body
      push(x, y + lid, x + w, y + lid, 0);
      push(x, y + lid, x, y + h, 0.05);
      push(x + w, y + lid, x + w, y + h, 0.05);
      push(x, y + h, x + w, y + h, 0.1);
      // lid
      push(x, y, x + w, y, 0.02);
      push(x, y, x, y + lid, 0.03);
      push(x + w, y, x + w, y + lid, 0.03);
      // seam + hinge
      push(x + w * 0.08, y + lid, x + w * 0.72, y + lid, 0.12);
      push(x + w * 0.78, y + lid, x + w * 0.92, y + lid, 0.14);
    }

    function base() {
      ctx.clearRect(0, 0, W, H);
      const x = W * 0.2;
      const y = H * 0.34;
      const w = W * 0.6;
      const h = H * 0.4;
      // floor line
      ctx.strokeStyle = "rgba(236,233,228,0.08)";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(W * 0.12, y + h + 10);
      ctx.lineTo(W * 0.88, y + h + 10);
      ctx.stroke();
      // lid gap
      ctx.strokeStyle = "rgba(236,233,228,0.05)";
      ctx.beginPath();
      ctx.moveTo(x, y + h * 0.26);
      ctx.lineTo(x + w, y + h * 0.26);
      ctx.stroke();
    }

    function drawSealed(alpha: number, t: number) {
      base();
      ctx.strokeStyle = `rgba(236,233,228,${0.72 * alpha})`;
      ctx.lineWidth = 1.35;
      for (const s of segs) {
        ctx.beginPath();
        ctx.moveTo(s.x1, s.y1);
        ctx.lineTo(s.x2, s.y2);
        ctx.stroke();
      }
      // status LED
      const x = W * 0.2;
      const y = H * 0.34;
      const w = W * 0.6;
      const h = H * 0.4;
      const pulse = 0.55 + 0.45 * Math.sin(t / 700);
      ctx.fillStyle = `rgba(90,212,106,${0.85 * pulse})`;
      ctx.beginPath();
      ctx.arc(x + w * 0.94, y + h - 14, 2.6, 0, Math.PI * 2);
      ctx.fill();
    }

    function burn(now: number) {
      const t = (now - start) / 1000;
      base();
      const alive: Seg[] = [];
      for (const s of segs) {
        if (t > s.at) {
          if (Math.random() < 0.55) {
            parts.push({
              x: s.x1,
              y: s.y1,
              vx: (Math.random() - 0.5) * 26,
              vy: -14 - Math.random() * 34,
              life: 0,
              max: 1.1 + Math.random() * 1.2,
              r: 0.6 + Math.random() * 1.5,
            });
          }
        } else alive.push(s);
      }
      segs = alive;

      // heat front
      const p = Math.min(1, t / 1.9);
      const gx = W * 0.2 + W * 0.6 * p;
      const grad = ctx.createRadialGradient(gx, H * 0.55, 2, gx, H * 0.55, W * 0.22);
      grad.addColorStop(0, "rgba(255,90,31,0.28)");
      grad.addColorStop(1, "rgba(255,90,31,0)");
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, W, H);

      // remaining strokes, ember at the front
      for (const s of segs) {
        const d = Math.abs(s.x1 - gx);
        const hot = Math.max(0, 1 - d / 40);
        ctx.strokeStyle = hot > 0.2 ? `rgba(255,${120 + hot * 90 | 0},40,${0.5 + hot * 0.5})` : "rgba(236,233,228,0.6)";
        ctx.lineWidth = 1.35;
        ctx.beginPath();
        ctx.moveTo(s.x1, s.y1);
        ctx.lineTo(s.x2, s.y2);
        ctx.stroke();
      }

      // particles
      const next: P[] = [];
      for (const q of parts) {
        q.life += 1 / 60;
        if (q.life < q.max) {
          q.x += q.vx / 60;
          q.y += q.vy / 60;
          q.vy -= 4 / 60;
          const k = 1 - q.life / q.max;
          ctx.fillStyle = k > 0.55 ? `rgba(255,140,60,${k})` : `rgba(150,148,142,${k * 0.8})`;
          ctx.beginPath();
          ctx.arc(q.x, q.y, q.r * (0.6 + k), 0, Math.PI * 2);
          ctx.fill();
          next.push(q);
        }
      }
      parts = next;

      if (t > 2.1) {
        state = "ash";
        cancelAnimationFrame(raf);
        drawAsh();
        return;
      }
      raf = requestAnimationFrame(burn);
    }

    function drawAsh() {
      base();
      const x = W * 0.2;
      const w = W * 0.6;
      const y = H * 0.34;
      const h = H * 0.4;
      // residue pile
      ctx.fillStyle = "rgba(120,116,110,0.22)";
      ctx.beginPath();
      ctx.ellipse(x + w / 2, y + h + 8, w * 0.34, 7, 0, 0, Math.PI * 2);
      ctx.fill();
      for (let i = 0; i < 60; i++) {
        ctx.fillStyle = `rgba(180,175,168,${0.05 + Math.random() * 0.12})`;
        const px = x + w / 2 + (Math.random() - 0.5) * w * 0.62;
        const py = y + h + 4 - Math.random() * 10;
        ctx.fillRect(px, py, 1.4, 1.4);
      }
      // wordmark
      const size = Math.min(W * 0.22, 74);
      ctx.font = `600 ${size}px ui-monospace, SFMono-Regular, Menlo, monospace`;
      ctx.fillStyle = "rgba(236,233,228,0.92)";
      ctx.textBaseline = "middle";
      const chars = "ASH".split("");
      const gap = size * 0.34;
      const total = chars.length * size * 0.62 + gap * 2;
      let cx = W / 2 - total / 2;
      for (const c of chars) {
        ctx.fillText(c, cx, y + h * 0.42);
        cx += size * 0.62 + gap;
      }
      ctx.font = "10px ui-monospace, monospace";
      ctx.fillStyle = "rgba(154,149,140,0.9)";
      ctx.textAlign = "center";
      ctx.fillText("KEY ERASED · 1.3 ms", W / 2, y + h * 0.42 + size * 0.78);
      ctx.textAlign = "start";
    }

    function loop(now: number) {
      if (state === "burning") burn(now);
      else if (state === "ash") drawAsh();
      else drawSealed(1, now);
    }

    function tick(now: number) {
      loop(now);
      if (state === "sealed") raf = requestAnimationFrame(tick);
    }

    build();
    if (reduced) state = "sealed";
    raf = requestAnimationFrame(tick);

    const onResize = () => {
      build();
      if (state === "ash") drawAsh();
    };
    window.addEventListener("resize", onResize);

    (window as unknown as { __burn?: () => void }).__burn = () => {
      if (state === "burning") return;
      if (reduced) {
        state = "ash";
        drawAsh();
        return;
      }
      state = "burning";
      start = performance.now();
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(burn);
    };

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", onResize);
    };
  });

  export function ignite() {
    (window as unknown as { __burn?: () => void }).__burn?.();
  }
</script>

<div class="burn">
  <canvas bind:this={canvas} aria-hidden="true"></canvas>
  <div class="burn-cta">
    {#if state === "sealed"}
      <button class="btn ghost" onclick={ignite}>Open it the wrong way</button>
      <span class="hint">sealed · armed</span>
    {:else if state === "burning"}
      <span class="hint hot">loop broken · erasing key</span>
    {:else}
      <button class="btn ghost" onclick={() => location.reload()}>Seal another</button>
      <span class="hint">nothing left to open</span>
    {/if}
  </div>
</div>

<style>
  .burn {
    position: relative;
    width: 100%;
    height: clamp(340px, 52vh, 520px);
    border: 1px solid var(--border);
    background:
      radial-gradient(120% 90% at 50% 10%, rgba(255, 90, 31, 0.05), transparent 60%),
      var(--surface);
  }
  canvas {
    display: block;
    width: 100%;
    height: 100%;
  }
  .burn-cta {
    position: absolute;
    inset: auto 0 14px 0;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
  }
  .hint {
    font-family: var(--mono);
    font-size: 10.5px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--dim);
  }
  .hint.hot {
    color: var(--ember);
  }
  @media (max-width: 720px) {
    .burn {
      max-height: 46vh;
    }
  }
</style>
