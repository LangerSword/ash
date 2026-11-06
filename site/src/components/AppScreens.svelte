<script lang="ts">
  import { onMount } from "svelte";

  type Mcu = {
    state: number;
    counter: number;
    master: number;
    loop: number;
    amber?: number;
  };
  type Device = { state: string; serial: string; detail?: string; mcu: Mcu | null };
  type Rec = {
    at: number;
    container: string;
    event: string;
    hash: string;
    header?: Record<string, unknown>;
  };

  type Tab = "device" | "seal" | "legend";

  let tab = $state<Tab>("device");
  let device = $state<Device | null>(null);
  let rec = $state<Rec | null>(null);
  let live = $state(false);
  let checked = $state(false);
  let photoOk = $state(true);

  const legend = [
    ["solid", "ARMED", "key held, loop closed"],
    ["bars", "AMBER", "deadline running"],
    ["dots", "WIPE", "erasing the master"],
    ["cross", "TAMPERED", "terminal, no key"],
    ["diamond", "UNSEALED", "key released"],
  ];

  function stateName(s: number) {
    return ["BOOT", "ARMED", "AMBER", "TAMPERED", "UNSEALED"][s] ?? "UNKNOWN";
  }

  function short(h: string) {
    return h ? h.slice(0, 12) + "…" + h.slice(-6) : "";
  }

  onMount(() => {
    let alive = true;
    const base = "https://api.langersword.in";
    const get = async (p: string) => {
      const ctl = new AbortController();
      const t = setTimeout(() => ctl.abort(), 6000);
      try {
        const r = await fetch(base + p, { signal: ctl.signal });
        if (!r.ok) throw new Error(String(r.status));
        return await r.json();
      } finally {
        clearTimeout(t);
      }
    };
    void (async () => {
      try {
        const [d, l] = await Promise.all([get("/device"), get("/ledger")]);
        if (!alive) return;
        device = d as Device;
        const records = (l as { records?: Rec[] }).records ?? [];
        rec = records[0] ?? null;
        live = true;
      } catch {
        live = false;
      } finally {
        if (alive) checked = true;
      }
    })();
    return () => {
      alive = false;
    };
  });
</script>

<section class="app" id="screens">
  <div class="head">
    <h2>The screens you actually use.</h2>
    <p>
      Three states of the desktop app, drawn from the live API. No mock data: if the board is offline,
      the window says so.
    </p>
  </div>

  <div class="layout">
    <div class="frame-wrap">
      <div class="tabs" role="tablist" aria-label="App screens">
        <button role="tab" aria-selected={tab === "device"} class:on={tab === "device"} onclick={() => (tab = "device")}>
          Device
        </button>
        <button role="tab" aria-selected={tab === "seal"} class:on={tab === "seal"} onclick={() => (tab = "seal")}>
          Seal
        </button>
        <button role="tab" aria-selected={tab === "legend"} class:on={tab === "legend"} onclick={() => (tab = "legend")}>
          Legend
        </button>
      </div>

      <div class="window">
        <div class="bar">
          <span class="mono">ash · {tab}</span>
          <span class="mono status" class:live>
            {#if !checked}checking{:else if live}live{:else}offline{/if}
          </span>
        </div>

        {#if tab === "device"}
          <div class="body">
            <div class="line"><span>link</span><b>{device ? device.state : checked ? "unreachable" : "…"}</b></div>
            <div class="line"><span>serial</span><b>{device?.serial ?? "n/a"}</b></div>
            <div class="line"><span>state</span><b>{device?.mcu ? stateName(device.mcu.state) : "n/a"}</b></div>
            <div class="line"><span>counter</span><b>{device?.mcu?.counter ?? "n/a"}</b></div>
            <div class="line"><span>master</span><b>{device?.mcu ? (device.mcu.master ? "present" : "erased") : "n/a"}</b></div>
            <div class="line"><span>loop</span><b>{device?.mcu ? (device.mcu.loop ? "open" : "closed") : "n/a"}</b></div>
            <p class="note">
              {#if live}
                Read at load from <code>/device</code>. Reconnect is automatic; the window never invents a state.
              {:else}
                The board is not reachable from this page right now. The app shows the same thing, with the
                adb command that fixes it.
              {/if}
            </p>
          </div>
        {:else if tab === "seal"}
          <div class="body">
            {#if rec}
              <div class="line"><span>event</span><b>{rec.event}</b></div>
              <div class="line"><span>container</span><b>{rec.container}</b></div>
              <div class="line"><span>at</span><b>{new Date(rec.at * 1000).toISOString().replace("T", " ").slice(0, 19)}Z</b></div>
              <div class="line"><span>cipher</span><b>{String(rec.header?.alg ?? "n/a")}</b></div>
              <div class="line"><span>size</span><b>{String(rec.header?.size ?? "n/a")} B</b></div>
              <div class="line hash"><span>hash</span><b>{short(rec.hash)}</b></div>
              <p class="note">
                The latest record from <code>/ledger</code>, hash-chained to the previous one. Payload stays
                encrypted; the header is authenticated as AAD.
              </p>
            {:else}
              <p class="empty">No ledger reachable. The app keeps the last record on disk and marks it stale.</p>
            {/if}
          </div>
        {:else}
          <div class="body">
            <p class="note top">First run shows this once, then stays behind the ? button.</p>
            <ul class="legend">
              {#each legend as [glyph, name, meaning]}
                <li>
                  <span class="glyph {glyph}" aria-hidden="true"></span>
                  <b>{name}</b>
                  <span>{meaning}</span>
                </li>
              {/each}
            </ul>
          </div>
        {/if}
      </div>
    </div>

    <div class="side">
      <figure class="shot" data-slot="app-desk">
        <img
          src="/shots/app-desk.jpg"
          alt="The Ash board on a desk, app open"
          loading="lazy"
          onerror={() => (photoOk = false)}
        />
        {#if !photoOk}
          <div class="ph">
            <span class="mono">photo slot</span>
            <p>The running app against the board goes here. Drop a JPEG at <code>/shots/app-desk.jpg</code>.</p>
          </div>
        {/if}
        <figcaption class="mono">the board on the desk</figcaption>
      </figure>
      <p class="side-note">
        These are the app's own screens, not illustrations. When the desktop build lands, this slot takes a
        photograph of the running window against the board.
      </p>
    </div>
  </div>
</section>

<style>
  .app {
    max-width: var(--max);
    margin: 0 auto;
    padding: clamp(64px, 10vh, 120px) var(--gutter);
    border-top: 1px solid var(--border);
  }
  .head {
    display: grid;
    grid-template-columns: 1fr 0.8fr;
    gap: clamp(24px, 5vw, 80px);
    align-items: end;
    padding-bottom: 26px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 40px;
  }
  h2 {
    font-size: clamp(32px, 4.2vw, 58px);
    line-height: 1;
    letter-spacing: -0.015em;
    margin: 0;
  }
  .head p {
    margin: 0;
    color: var(--muted);
    font-size: 14.5px;
    line-height: 1.6;
    max-width: 44ch;
  }
  .layout {
    display: grid;
    grid-template-columns: 1.15fr 0.85fr;
    gap: clamp(28px, 5vw, 72px);
    align-items: start;
  }
  .tabs {
    display: flex;
    gap: 2px;
    margin-bottom: -1px;
  }
  .tabs button {
    font-family: var(--mono);
    font-size: 10px;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: var(--dim);
    background: none;
    border: 1px solid transparent;
    border-bottom: none;
    padding: 9px 14px;
    cursor: pointer;
  }
  .tabs button:hover {
    color: var(--text);
  }
  .tabs button.on {
    color: var(--text);
    border-color: var(--border);
    background: var(--surface);
  }
  .window {
    border: 1px solid var(--border);
    background: var(--surface);
  }
  .bar {
    display: flex;
    justify-content: space-between;
    padding: 10px 14px;
    border-bottom: 1px solid var(--border);
  }
  .status.live {
    color: var(--signal);
  }
  .body {
    padding: 8px 14px 16px;
  }
  .line {
    display: grid;
    grid-template-columns: 92px 1fr;
    gap: 10px;
    padding: 9px 0;
    border-bottom: 1px solid var(--border);
    font-family: var(--mono);
    font-size: 11.5px;
  }
  .line span {
    color: var(--dim);
    font-size: 10px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    align-self: center;
  }
  .line b {
    font-weight: 400;
    color: var(--text);
  }
  .line.hash b {
    color: var(--ember);
  }
  .note {
    margin: 14px 0 0;
    color: var(--muted);
    font-size: 12.5px;
    line-height: 1.55;
    font-family: var(--sans);
  }
  .note.top {
    margin: 4px 0 12px;
  }
  code {
    font-family: var(--mono);
    font-size: 11px;
    color: var(--text);
  }
  .empty {
    margin: 12px 0;
    color: var(--muted);
    font-size: 13px;
  }
  .legend {
    list-style: none;
    margin: 0;
    padding: 0;
  }
  .legend li {
    display: grid;
    grid-template-columns: 26px 92px 1fr;
    gap: 10px;
    align-items: center;
    padding: 10px 0;
    border-bottom: 1px solid var(--border);
    font-size: 12.5px;
  }
  .legend b {
    font-family: var(--mono);
    font-size: 10px;
    letter-spacing: 0.12em;
    font-weight: 400;
  }
  .legend span:last-child {
    color: var(--muted);
  }
  .glyph {
    width: 18px;
    height: 12px;
    background: var(--text);
  }
  .glyph.solid {
    opacity: 0.9;
  }
  .glyph.bars {
    background: repeating-linear-gradient(180deg, var(--text) 0 2px, transparent 2px 4px);
  }
  .glyph.dots {
    background: radial-gradient(circle, var(--ember) 1px, transparent 1.4px) 0 0 / 4px 4px;
  }
  .glyph.cross {
    background: none;
    position: relative;
  }
  .glyph.cross::before,
  .glyph.cross::after {
    content: "";
    position: absolute;
    inset: 5px 0 auto;
    height: 1px;
    background: var(--ember);
    transform: rotate(28deg);
  }
  .glyph.cross::after {
    transform: rotate(-28deg);
  }
  .glyph.diamond {
    background: none;
    border: 1px solid var(--text);
    transform: rotate(45deg) scale(0.62);
  }
  .side {
    display: grid;
    gap: 16px;
  }
  .shot {
    margin: 0;
    border: 1px solid var(--border);
    background: var(--surface);
    aspect-ratio: 4 / 3;
    position: relative;
    overflow: hidden;
  }
  .shot img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
  }
  .shot figcaption {
    position: absolute;
    left: 12px;
    bottom: 10px;
    color: var(--text);
    background: rgba(11, 9, 7, 0.72);
    padding: 3px 7px;
  }
  .ph {
    position: absolute;
    inset: 0;
    display: grid;
    align-content: center;
    gap: 10px;
    padding: 22px;
    background: var(--surface);
  }
  .ph p {
    margin: 0;
    color: var(--muted);
    font-size: 12.5px;
    line-height: 1.55;
    max-width: 34ch;
  }
  .side-note {
    margin: 0;
    color: var(--muted);
    font-size: 13px;
    line-height: 1.6;
  }
  @media (max-width: 900px) {
    .head,
    .layout {
      grid-template-columns: 1fr;
      align-items: start;
    }
  }
</style>
