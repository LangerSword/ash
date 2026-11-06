<script lang="ts">
  import { onMount } from "svelte";

  let canvas: HTMLCanvasElement;

  type P = { x: number; y: number; vx: number; vy: number; life: number; max: number; r: number };

  onMount(() => {
    const ctx = canvas.getContext("2d")!;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);

    let W = 0;
    let H = 0;
    let text: HTMLCanvasElement | null = null;
    let alpha: Uint8Array | null = null;
    let tw = 0;
    let th = 0;
    let parts: P[] = [];
    let raf = 0;
    let t0 = 0;
    let ready = false;

    const IVORY: readonly number[] = [242, 236, 223];
    const EMBER: readonly number[] = [212, 68, 42];

    async function setup() {
      try {
        const f = (document as unknown as { fonts: FontFaceSet }).fonts;
        await f.load("300 200px Cormorant");
        await f.ready;
      } catch {
        /* system serif fallback */
      }

      const r = canvas.getBoundingClientRect();
      W = r.width;
      H = r.height;
      canvas.width = Math.round(W * dpr);
      canvas.height = Math.round(H * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      const size = Math.min(W * 0.6, H * 0.9);
      tw = Math.ceil(W);
      th = Math.ceil(H);

      text = document.createElement("canvas");
      text.width = Math.round(tw * dpr);
      text.height = Math.round(th * dpr);
      const tctx = text.getContext("2d")!;
      tctx.scale(dpr, dpr);
      tctx.fillStyle = `rgb(${IVORY[0]},${IVORY[1]},${IVORY[2]})`;
      tctx.textAlign = "center";
      tctx.textBaseline = "middle";
      tctx.font = `300 ${size}px Cormorant, "EB Garamond", Georgia, serif`;
      tctx.fillText("Ash", W / 2, H / 2);

      const img = tctx.getImageData(0, 0, text.width, text.height).data;
      alpha = new Uint8Array(text.width * text.height);
      for (let i = 0, j = 3; i < alpha.length; i++, j += 4) alpha[i] = img[j];

      ready = true;
      t0 = performance.now();

      if (reduce) {
        drawFinal();
        return;
      }
      raf = requestAnimationFrame(frame);
    }

    function erode(cx: number, cy: number, rad: number) {
      const tctx = text!.getContext("2d")!;
      tctx.save();
      tctx.setTransform(1, 0, 0, 1, 0, 0);
      tctx.globalCompositeOperation = "destination-out";
      const g = tctx.createRadialGradient(cx * dpr, cy * dpr, 0, cx * dpr, cy * dpr, rad * dpr);
      g.addColorStop(0, "rgba(0,0,0,1)");
      g.addColorStop(0.7, "rgba(0,0,0,0.9)");
      g.addColorStop(1, "rgba(0,0,0,0)");
      tctx.fillStyle = g;
      tctx.beginPath();
      tctx.arc(cx * dpr, cy * dpr, rad * dpr, 0, Math.PI * 2);
      tctx.fill();
      tctx.restore();
    }

    function hasInk(x: number, y: number) {
      if (!alpha || !text) return false;
      const px = Math.round(x * dpr);
      const py = Math.round(y * dpr);
      if (px < 0 || py < 0 || px >= text.width || py >= text.height) return false;
      return alpha[py * text.width + px] > 30;
    }

    function frame(now: number) {
      const t = (now - t0) / 1000;
      ctx.clearRect(0, 0, W, H);
      if (!text || !ready) return;

      // the ghost that survives
      ctx.save();
      ctx.globalAlpha = t > 3.4 ? 0.1 : 0.04;
      ctx.drawImage(text, 0, 0, tw, th);
      ctx.restore();

      if (t < 3.9) {
        ctx.save();
        ctx.globalAlpha = Math.min(1, t / 0.9);
        ctx.drawImage(text, 0, 0, tw, th);
        ctx.restore();
      }

      const start = 1.25;
      if (t > start) {
        const p = Math.min(1, (t - start) / 2.2);
        const front = W * (0.08 + p * 0.84);
        for (let i = 0; i < 26; i++) {
          const x = front + (Math.random() - 0.5) * W * 0.1;
          const y = H * 0.5 + (Math.random() - 0.5) * H * 0.62;
          const inked = hasInk(x, y);
          erode(x, y, inked ? 7 + Math.random() * 15 : 4 + Math.random() * 8);
          if (inked && Math.random() < 0.85) {
            parts.push({
              x,
              y,
              vx: (Math.random() - 0.5) * 34,
              vy: -10 - Math.random() * 46,
              life: 0,
              max: 1.2 + Math.random() * 1.6,
              r: 0.5 + Math.random() * 1.6,
            });
          }
        }
        const g = ctx.createRadialGradient(front, H * 0.52, 2, front, H * 0.52, W * 0.2);
        g.addColorStop(0, "rgba(212,68,42,0.15)");
        g.addColorStop(1, "rgba(212,68,42,0)");
        ctx.fillStyle = g;
        ctx.fillRect(0, 0, W, H);
      }

      const next: P[] = [];
      for (const q of parts) {
        q.life += 1 / 60;
        q.x += q.vx / 60;
        q.y += q.vy / 60;
        q.vy -= 3 / 60;
        q.vx *= 0.99;
        if (q.life < q.max) {
          const k = 1 - q.life / q.max;
          const c = k > 0.6 ? EMBER : [154, 146, 132];
          ctx.fillStyle = `rgba(${c[0]},${c[1]},${c[2]},${k * 0.8})`;
          ctx.beginPath();
          ctx.arc(q.x, q.y, q.r * (0.5 + k), 0, Math.PI * 2);
          ctx.fill();
          next.push(q);
        }
      }
      parts = next;

      if (t < 6.2) raf = requestAnimationFrame(frame);
    }

    function drawFinal() {
      ctx.clearRect(0, 0, W, H);
      if (!text) return;
      ctx.save();
      ctx.globalAlpha = 0.12;
      ctx.drawImage(text, 0, 0, tw, th);
      ctx.restore();
    }

    void setup();

    const onResize = () => {
      cancelAnimationFrame(raf);
      ready = false;
      void setup();
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
