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
    let pristine: HTMLCanvasElement | null = null;
    let work: HTMLCanvasElement | null = null;
    let alpha: Uint8Array | null = null;
    let parts: P[] = [];
    let raf = 0;
    let t0 = 0;
    let ready = false;

    const IVORY: readonly number[] = [242, 236, 223];
    const EMBER: readonly number[] = [212, 68, 42];

    const CYCLE = 15;
    const T_IN = 0.9;
    const T_BURN = 1.5;
    const BURN_LEN = 2.4;
    const T_GONE = T_BURN + BURN_LEN + 0.4;
    const T_RESPAWN = 6.4;
    const RESPAWN_LEN = 1.4;

    const body =
      "A tamper-responsive seal for confidential shipments. Break the loop and the key dies in the chip, before anyone reads a byte.";

    function layout() {
      const r = canvas.getBoundingClientRect();
      W = r.width;
      H = r.height;
      canvas.width = Math.round(W * dpr);
      canvas.height = Math.round(H * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      pristine = document.createElement("canvas");
      pristine.width = Math.round(W * dpr);
      pristine.height = Math.round(H * dpr);
      const p = pristine.getContext("2d")!;
      p.scale(dpr, dpr);

      // wordmark
      const size = Math.min(W * 0.6, H * 0.62);
      p.fillStyle = `rgb(${IVORY[0]},${IVORY[1]},${IVORY[2]})`;
      p.textAlign = "center";
      p.textBaseline = "middle";
      p.font = `300 ${size}px Cormorant, "EB Garamond", Georgia, serif`;
      p.fillText("Ash", W / 2, H * 0.4);

      // statement, bottom left
      const fs = W < 700 ? 19 : 23;
      const maxw = Math.min(460, W * 0.72);
      p.font = `300 ${fs}px Cormorant, "EB Garamond", Georgia, serif`;
      p.textAlign = "left";
      p.textBaseline = "alphabetic";
      p.fillStyle = `rgba(${IVORY[0]},${IVORY[1]},${IVORY[2]},0.92)`;
      const words = body.split(" ");
      const lines: string[] = [];
      let line = "";
      for (const w of words) {
        const test = line ? line + " " + w : w;
        if (p.measureText(test).width > maxw && line) {
          lines.push(line);
          line = w;
        } else line = test;
      }
      if (line) lines.push(line);
      const lh = fs * 1.36;
      const bottom = W < 700 ? 96 : 56;
      const startY = H - bottom - (lines.length - 1) * lh;
      lines.forEach((l, i) => p.fillText(l, 32, startY + i * lh));

      work = document.createElement("canvas");
      work.width = pristine.width;
      work.height = pristine.height;

      const w = work.getContext("2d")!;
      w.drawImage(pristine, 0, 0);

      const img = w.getImageData(0, 0, work.width, work.height).data;
      alpha = new Uint8Array(work.width * work.height);
      for (let i = 0, j = 3; i < alpha.length; i++, j += 4) alpha[i] = img[j];

      ready = true;
    }

    function resetWork() {
      if (!work || !pristine) return;
      const w = work.getContext("2d")!;
      w.setTransform(1, 0, 0, 1, 0, 0);
      w.clearRect(0, 0, work.width, work.height);
      w.drawImage(pristine, 0, 0);
    }

    function erode(cx: number, cy: number, rad: number) {
      if (!work) return;
      const w = work.getContext("2d")!;
      w.save();
      w.setTransform(1, 0, 0, 1, 0, 0);
      w.globalCompositeOperation = "destination-out";
      const g = w.createRadialGradient(cx * dpr, cy * dpr, 0, cx * dpr, cy * dpr, rad * dpr);
      g.addColorStop(0, "rgba(0,0,0,1)");
      g.addColorStop(0.65, "rgba(0,0,0,0.92)");
      g.addColorStop(1, "rgba(0,0,0,0)");
      w.fillStyle = g;
      w.beginPath();
      w.arc(cx * dpr, cy * dpr, rad * dpr, 0, Math.PI * 2);
      w.fill();
      w.restore();
    }

    function hasInk(x: number, y: number) {
      if (!alpha || !work) return false;
      const px = Math.round(x * dpr);
      const py = Math.round(y * dpr);
      if (px < 0 || py < 0 || px >= work.width || py >= work.height) return false;
      return alpha[py * work.width + px] > 30;
    }

    function spawn(x: number, y: number, n: number) {
      for (let i = 0; i < n; i++) {
        parts.push({
          x,
          y,
          vx: (Math.random() - 0.5) * 36,
          vy: -12 - Math.random() * 48,
          life: 0,
          max: 1.2 + Math.random() * 1.7,
          r: 0.5 + Math.random() * 1.7,
        });
      }
    }

    function frame(now: number) {
      const abs = (now - t0) / 1000;
      const t = abs % CYCLE;
      ctx.clearRect(0, 0, W, H);
      if (!work || !pristine || !ready) return;

      // entrance / respawn alpha
      let alphaIn = 1;
      if (t < T_IN) alphaIn = t / T_IN;
      else if (t >= T_RESPAWN && t < T_RESPAWN + RESPAWN_LEN) {
        alphaIn = (t - T_RESPAWN) / RESPAWN_LEN;
      } else if (t >= T_RESPAWN + RESPAWN_LEN) alphaIn = 1;

      // at the top of each cycle, rebuild the text
      if (t < 0.12) resetWork();

      if (t >= T_RESPAWN && t < T_RESPAWN + 0.15) resetWork();

      if (t < T_GONE || t >= T_RESPAWN) {
        ctx.save();
        ctx.globalAlpha = Math.max(0, Math.min(1, alphaIn));
        ctx.drawImage(work, 0, 0, W, H);
        ctx.restore();
      }

      // burn
      if (t >= T_BURN && t < T_BURN + BURN_LEN) {
        const p = (t - T_BURN) / BURN_LEN;
        const front = W * (0.04 + p * 0.96);
        for (let i = 0; i < 30; i++) {
          const x = front + (Math.random() - 0.5) * W * 0.09;
          const y = Math.random() * H;
          const inked = hasInk(x, y);
          erode(x, y, inked ? 8 + Math.random() * 16 : 4 + Math.random() * 9);
          if (inked && Math.random() < 0.7) spawn(x, y, 1 + (Math.random() < 0.3 ? 1 : 0));
        }
        const g = ctx.createRadialGradient(front, H * 0.45, 2, front, H * 0.45, W * 0.22);
        g.addColorStop(0, "rgba(212,68,42,0.14)");
        g.addColorStop(1, "rgba(212,68,42,0)");
        ctx.fillStyle = g;
        ctx.fillRect(0, 0, W, H);
      }

      // embers
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

      raf = requestAnimationFrame(frame);
    }

    async function setup() {
      try {
        const f = (document as unknown as { fonts: FontFaceSet }).fonts;
        await f.load("300 200px Cormorant");
        await f.ready;
      } catch {
        /* serif fallback */
      }
      layout();
      t0 = performance.now();

      if (reduce) {
        const w = work!.getContext("2d")!;
        ctx.drawImage(pristine!, 0, 0, W, H);
        return;
      }
      raf = requestAnimationFrame(frame);
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
