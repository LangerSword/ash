<script lang="ts">
  const glyphs = [
    {
      label: "ARMED",
      note: "key held, loop closed",
      cells: "0000000000000 0000000000000 0011111111100 0010000000100 0010111110100 0010000000100 0011111111100 0000000000000",
    },
    {
      label: "AMBER",
      note: "deadline running",
      cells: "0000000000000 0011111111100 0000000000000 0011111111100 0000000000000 0011111111100 0000000000000 0000000000000",
    },
    {
      label: "TAMPERED",
      note: "master erased, terminal",
      cells: "0000000000000 0100000000010 0010000000100 0001000001000 0000100010000 0001000001000 0010000000100 0100000000010",
    },
    {
      label: "UNSEALED",
      note: "proof accepted, key released",
      cells: "0000000000000 0000010000000 0000111000000 0001111100000 0011111110000 0001111100000 0000111000000 0000010000000",
    },
  ];

  const challenge = `{
  "x402Version": 2,
  "error": "payment required",
  "accepts": [{
    "scheme": "exact",
    "network": "hedera:testnet",
    "amount": "10000000",
    "asset": "0.0.0",
    "payTo": "0.0.11344783",
    "extra": { "feePayer": "0.0.9185802" }
  }]
}`;
  const events = [
    { t: "09:12:04", e: "SEALED", d: "container C-001, key derived on the MCU" },
    { t: "09:14:31", e: "AMBER", d: "edges 2, open 180 ms, deadline 5 000 ms" },
    { t: "09:14:34", e: "0G · HOLD", d: "handling, not intrusion; request id recorded" },
    { t: "09:19:02", e: "TAMPERED", d: "loop cut, master erased, read-back 0xFF" },
    { t: "09:19:40", e: "UNSEAL_DENIED", d: "no key exists; release refused" },
  ];
</script>

<section class="evidence" id="evidence">
  <div class="head">
    <h2>What the device leaves behind.</h2>
    <p>
      A seal is only useful if the other side can check it. Four matrix states, one chained episode
      log, and a record anyone can buy for a cent.
    </p>
  </div>

  <div class="glyphs">
    {#each glyphs as g}
      <figure>
        <div class="matrix" aria-hidden="true">
          {#each g.cells.split(" ") as row}
            {#each row.split("") as bit}
              <span class:on={bit === "1"}></span>
            {/each}
          {/each}
        </div>
        <figcaption>
          <b>{g.label}</b>
          <span>{g.note}</span>
        </figcaption>
      </figure>
    {/each}
  </div>

  <div class="split">
    <div class="log">
      <div class="log-head">
        <span class="mono">episode · C-001</span>
        <span class="mono">hash chained</span>
      </div>
      <ol>
        {#each events as ev}
          <li>
            <span class="time mono">{ev.t}</span>
            <span class="ev mono" class:hot={ev.e === "TAMPERED"}>{ev.e}</span>
            <span class="desc">{ev.d}</span>
          </li>
        {/each}
      </ol>
      <p class="foot-note">
        Times from a rehearsal run. Every record carries the previous record's hash, so a gap or a
        rewrite is visible without trusting the server.
      </p>
    </div>

    <div class="challenge">
      <div class="log-head">
        <span class="mono">GET /attestation/C-001</span>
        <span class="mono">402</span>
      </div>
      <pre><code>{challenge}</code></pre>
      <p class="foot-note">
        The live response from the deployed API. HBAR on testnet today; USDC is the production asset.
        Settlement is not claimed until a transaction id exists.
      </p>
    </div>
  </div>
</section>

<style>
  .evidence {
    max-width: var(--max);
    margin: 0 auto;
    padding: clamp(64px, 10vh, 120px) var(--gutter);
  }
  .head {
    display: grid;
    grid-template-columns: 1fr 0.85fr;
    gap: clamp(24px, 5vw, 72px);
    align-items: end;
    margin-bottom: 40px;
    padding-bottom: 24px;
    border-bottom: 1px solid var(--border);
  }
  h2 {
    font-size: clamp(30px, 4vw, 52px);
    line-height: 1.02;
    letter-spacing: -0.035em;
    margin: 0;
  }
  .head p {
    margin: 0;
    color: var(--muted);
    font-size: 14.5px;
    line-height: 1.6;
    max-width: 46ch;
  }
  .glyphs {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1px;
    background: var(--border);
    border: 1px solid var(--border);
    margin-bottom: 48px;
  }
  figure {
    margin: 0;
    padding: 22px 20px;
    background: var(--bg);
  }
  .matrix {
    display: grid;
    grid-template-columns: repeat(13, 1fr);
    gap: 3px;
    max-width: 150px;
    aspect-ratio: 13 / 8;
    margin-bottom: 16px;
  }
  .matrix span {
    background: var(--text);
    opacity: 0.12;
  }
  .matrix span.on {
    background: var(--text);
    opacity: 0.88;
  }
  figcaption b {
    display: block;
    font-family: var(--mono);
    font-size: 10.5px;
    letter-spacing: 0.14em;
    margin-bottom: 4px;
  }
  figcaption span {
    color: var(--muted);
    font-size: 12.5px;
  }
  .split {
    display: grid;
    grid-template-columns: 1.1fr 0.9fr;
    gap: clamp(24px, 4vw, 56px);
  }
  .log-head {
    display: flex;
    justify-content: space-between;
    padding-bottom: 10px;
    border-bottom: 1px solid var(--border-strong);
  }
  .mono {
    font-family: var(--mono);
    font-size: 10px;
    letter-spacing: 0.13em;
    text-transform: uppercase;
    color: var(--dim);
  }
  ol {
    list-style: none;
    margin: 0;
    padding: 0;
  }
  li {
    display: grid;
    grid-template-columns: 74px 108px 1fr;
    gap: 10px;
    padding: 12px 0;
    border-bottom: 1px solid var(--border);
    align-items: baseline;
  }
  .time {
    color: var(--dim);
  }
  .ev {
    color: var(--text);
  }
  .ev.hot {
    color: var(--ember);
  }
  .desc {
    color: var(--muted);
    font-size: 13px;
  }
  .foot-note {
    margin: 14px 0 0;
    color: var(--dim);
    font-size: 12px;
    line-height: 1.55;
    max-width: 52ch;
  }
  pre {
    margin: 0;
    padding: 16px;
    background: var(--surface);
    border: 1px solid var(--border);
    overflow-x: auto;
  }
  code {
    font-family: var(--mono);
    font-size: 11.5px;
    line-height: 1.7;
    color: var(--text);
  }
  @media (max-width: 900px) {
    .head,
    .split {
      grid-template-columns: 1fr;
    }
    .glyphs {
      grid-template-columns: repeat(2, 1fr);
    }
    li {
      grid-template-columns: 64px 1fr;
    }
    .desc {
      grid-column: 1 / -1;
    }
  }
</style>
