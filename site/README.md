# Ash site

Frontend lives here. Read [`../website-brief-v2.md`](../website-brief-v2.md) first — it is the
contract (structure, copy, design tokens, GSAP choreography, API shapes, wallet flows, acceptance).

Stack: Svelte 5 + Vite + TypeScript, GSAP + ScrollTrigger, plain CSS tokens.

```bash
cd site
npm install
npm run dev          # http://127.0.0.1:5173
```

The demo panel talks to `http://127.0.0.1:8080` (run `python3 device/demo_api.py` from the repo root).
Everything outside the panel works with the API down.

Owner: Ananya (`@wckdnya`). Backend: Lakshaya.
