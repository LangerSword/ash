<script lang="ts">
  import { onMount } from "svelte";

  let canvas: HTMLCanvasElement;

  type Seg = { x1: number; y1: number; x2: number; y2: number; draw: number; burn: number; spawned?: boolean };
  type P = { x: number; y: number; vx: number; vy: number; life: number; max: number; r: number };

  onMount(() => {
    const ctx = canvas.getContext("2d")!;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    let W = 0;
    let H = 0;
    let segs: Seg[] = [];
    let parts: P[] = [];
    let raf = 0;
    let t0 = performance.now();

    const INK = [22, 20, 15] as const;
    const EMBER = [178, 58, 26] as const;
    const ASH = [122, 115, 102] as const;

    function build() {
      const r = canvas.getBoundingClientRect();
      W = r.width;
      H = r.height;
      canvas.width = Math.round(W * dpr);
      canvas.height = Math.round(H * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      const w = Math.min(W * 0.72, 620);
      const h = w * 0.58;
      const x = (W - w) / 2;
      const y = (H - h) / 2 - 10;
      const lid = h * 0.3;
      segs = [];
      const line = (x1: number, y1: number, x2: number, y2: number, d: number) => {
        const len = Math.hypot(x2 - x1, y2 - y1);
        const n = Math.max(1, Math.round(len / 6));
        for (let i = 0; i < n; i++) {
          const a = i / n;
          const b = (i + 1) / n;
          const bx = x1 + (x2 - x1) * a;
          const by = y1 + (y2 - y1) * a;
          segs.push({
            x1: bx,
            y1: by,
            x2: x1 + (x2 - x1) * b,
            y2: y1 + (y2 - y1) * b,
            draw: d + a * 0.32,
            burn: 0.06 + bx / W * 0.5 + Math.random() * 0.3,
          });
        }
      };
      // lid
      line(x, y, x + w, y, 0.0);
      line(x, y, x, y + lid, 0.03);
      line(x + w, y, x + w, y + lid, 0.03);
      // body
      line(x, y + lid, x + w, y + lid, 0.06);
      line(x, y + lid, x, y + h, 0.1);
      line(x + w, y + lid, x + w, y + h, 0.1);
      line(x, y + h, x + w, y + h, 0.14);
      // seam, hinge, latch
      line(x + w * 0.06, y + lid, x + w * 0.66, y + lid, 0.16);
      line(x + w * 0.72, y + lid, x + w * 0.94, y + lid, 0.18);
      line(x + w * 0.5, y + lid - 6, x + w * 0.5, y + lid + 6, 0.2);
      // registration marks
      const m = 14;
      for (const [cx, cy] of [
        [x - m, y - m],
        [x + w + m, y - m],
        [x - m, y + h + m],
        [x + w + m, y + h + m],
      ]) {
        line(cx - 5, cy, cx + 5, cy, 0);
        line(cx, cy - 5, cx, cy + 5, 0);
      }
    }

    const ease = (v: number) => 1 - Math.pow(1 - Math.max(0, Math.min(1, v)), 3);

    function frame(now: number) {
      const t = (now - t0) / 1000;
      ctx.clearRect(0, 0, W, H);

      const burnStart = 1.55;
      const burnEnd = 3.9;

      // particles
      if (t > burnStart) {
        for (const s of segs) {
          if (!s.spawned && t > burnStart + s.burn * 1.7) {
            s.spawned = true;
            if (Math.random() < 0.5)
              parts.push({
                x: s.x1,
                y: s.y1,
                vx: (Math.random() - 0.5) * 22,
                vy: -12 - Math.random() * 30,
                life: 0,
                max: 1.4 + Math.random() * 1.4,
                r: 0.5 + Math.random() * 1.4,
              });
          }
        }
      }

      for (const s of segs) {
        const drawAt = s.draw;
        const burnAt = burnStart + s.burn * 1.7;
        if (t < burnAt) {
          const appear = ease((t - drawAt) / 0.5);
          if (appear <= 0) continue;
          const hot = Math.min(1, Math.max(0, (t - (burnAt - 0.5)) / 0.5));
          const c = hot > 0 ? EMBER.map((v, i) => Math.round(INK[i] + (v - INK[i]) * hot)) : INK;
          ctx.strokeStyle = `rgba(${c[0]},${c[1]},${c[2]},${0.82 * appear})`;
          ctx.lineWidth = 1.15;
          ctx.beginPath();
          ctx.moveTo(s.x1, s.y1);
          ctx.lineTo(s.x2 + (s.x2 - s.x1) * (1 - appear), s.y2 + (s.y2 - s.y1) * (1 - appear));
          ctx.stroke();
        }
      }

      // heat bloom
      if (t > burnStart && t < burnEnd + 0.4) {
        const p = Math.min(1, (t - burnStart) / (burnEnd - burnStart));
        const gx = W * 0.2 + W * 0.6 * p;
        const g = ctx.createRadialGradient(gx, H * 0.5, 4, gx, H * 0.5, W * 0.2);
        g.addColorStop(0, "rgba(178,58,26,0.16)");
        g.addColorStop(1, "rgba(178,58,26,0)");
        ctx.fillStyle = g;
        ctx.fillRect(0, 0, W, H);
      }

      // ash particles
      const next: P[] = [];
      for (const q of parts) {
        q.life += 1 / 60;
        q.x += q.vx / 60;
        q.y += q.vy / 60;
        q.vy -= 2.2 / 60;
        q.vx *= 0.995;
        if (q.life < q.max) {
          const k = 1 - q.life / q.max;
          ctx.fillStyle = `rgba(${ASH[0]},${ASH[1]},${ASH[2]},${k * 0.65})`;
          ctx.beginPath();
          ctx.arc(q.x, q.y, q.r * (0.5 + k), 0, Math.PI * 2);
          ctx.fill();
          next.push(q);
        }
      }
      parts = next;

      // pile
      if (t > burnEnd - 0.4) {
        const k = Math.min(1, (t - (burnEnd - 0.4)) / 0.8);
        const w = Math.min(W * 0.72, 620);
        const h = w * 0.58;
        const x = (W - w) / 2;
        const y = (H - h) / 2 - 10;
        ctx.fillStyle = `rgba(90,84,74,${0.1 * k})`;
        ctx.beginPath();
        ctx.ellipse(x + w / 2, y + h + 6, w * 0.33 * k, 6 * k, 0, 0, Math.PI * 2);
        ctx.fill();
        for (let i = 0; i < 70; i++) {
          ctx.fillStyle = `rgba(70,65,57,${(0.04 + Math.random() * 0.09) * k})`;
          const px = x + w / 2 + (Math.random() - 0.5) * w * 0.64 * k;
          const py = y + h + 4 - Math.random() * 9;
          ctx.fillRect(px, py, 1.3, 1.3);
        }
      }

      if (t < 6.5) raf = requestAnimationFrame(frame);
    }

    build();
    if (reduce) {
      // final frame only
      const w = Math.min(W * 0.72, 620);
      const h = w * 0.58;
      const x = (W - w) / 2;
      const y = (H - h) / 2 - 10;
      ctx.fillStyle = "rgba(90,84,74,0.1)";
      ctx.beginPath();
      ctx.ellipse(x + w / 2, y + h + 6, w * 0.33, 6, 0, 0, Math.PI * 2);
      ctx.fill();
      for (let i = 0; i < 70; i++) {
        ctx.fillStyle = `rgba(70,65,57,${0.04 + Math.random() * 0.09})`;
        ctx.fillRect(x + w / 2 + (Math.random() - 0.5) * w * 0.64, y + h + 4 - Math.random() * 9, 1.3, 1.3);
      }
    } else {
      raf = requestAnimationFrame(frame);
    }

    const onResize = () => {
      build();
      t0 = performance.now();
      if (reduce) return;
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(frame);
    };
    window.addEventListener("resize", onResize);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", onResize);
    };
  });
</script>

<canvas bind:this={canvas} aria-hidden="true"></canvas>

<style>
  canvas {
    display: block;
    width: 100%;
    height: 100%;
  }
</style>
