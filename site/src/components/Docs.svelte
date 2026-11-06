<section class="docs" id="docs">
  <div class="col">
    <h2>Read it before you trust it.</h2>
    <p class="lede">
      The short version: one board, one loop, one key. Everything the demo does is in the repo, and
      everything that is not real is written down.
    </p>

    <div class="links">
      <a href="https://github.com/LangerSword/ash" rel="noopener">Repository</a>
      <a href="https://github.com/LangerSword/ash/blob/master/docs/SECURITY.md" rel="noopener">Security model</a>
      <a href="https://github.com/LangerSword/ash/blob/master/docs/ARCHITECTURE.md" rel="noopener">Architecture</a>
    </div>
  </div>

  <div class="acc">
    <details open>
      <summary><span>Quickstart</span><span class="mono">01</span></summary>
      <div class="body">
        <p>Linux, Python 3.12, an Arduino UNO Q over USB, and the board app running.</p>
        <pre><code>git clone https://github.com/LangerSword/ash
cd ash && python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
ASH_MCU=board ASH_WORLD=idkit python device/demo_api.py</code></pre>
        <p>Open <code>http://127.0.0.1:8080/site/</code>. The panel reads the board's real state.</p>
      </div>
    </details>

    <details>
      <summary><span>API</span><span class="mono">02</span></summary>
      <div class="body">
        <p>Everything the app and the panel use is a plain HTTP call.</p>
        <pre><code>GET  /status        state, counter, master, loop, amber
GET  /device        adb state, serial, forwarded port
POST /seal          encrypt a payload under a derived key
POST /unseal        release the key after proof and policy
POST /sim           drive the loop: flex, cut, close
GET  /ledger        hash-chained episode records
GET  /attestation/:c  402 challenge, then the signed record</code></pre>
        <p>Errors are one sentence of cause and one of action. No stack traces on the wire.</p>
      </div>
    </details>

    <details>
      <summary><span>What is not claimed</span><span class="mono">03</span></summary>
      <div class="body">
        <ul>
          <li>Not a certified secure element. A bench attacker with SWD can read the MCU.</li>
          <li>The loop covers one path. A determined opening of the enclosure is out of scope.</li>
          <li>World identity is a sandbox credential. Proofs are test proofs.</li>
          <li>The Hedera endpoint returns a correct 402. Settlement is not yet executed end to end.</li>
          <li>Payloads are decrypted on the host at seal time and at unseal time. The host sees the plaintext then.</li>
        </ul>
      </div>
    </details>
  </div>
</section>

<style>
  .docs {
    max-width: var(--max);
    margin: 0 auto;
    padding: clamp(64px, 10vh, 120px) var(--gutter);
    display: grid;
    grid-template-columns: 0.9fr 1.1fr;
    gap: clamp(28px, 6vw, 88px);
    border-top: 1px solid var(--border);
  }
  h2 {
    font-size: clamp(28px, 3.4vw, 44px);
    line-height: 1.04;
    letter-spacing: -0.035em;
    margin: 0 0 16px;
    font-weight: 500;
  }
  .lede {
    margin: 0;
    color: var(--muted);
    font-size: 15px;
    line-height: 1.6;
    max-width: 44ch;
  }
  .links {
    margin-top: 26px;
    display: grid;
    gap: 8px;
  }
  .links a {
    color: var(--text);
    font-size: 13.5px;
    text-decoration: none;
    border-bottom: 1px solid var(--border);
    padding-bottom: 8px;
    width: fit-content;
  }
  .links a:hover {
    border-color: var(--ember);
  }
  .acc {
    border-top: 1px solid var(--border-strong);
  }
  details {
    border-bottom: 1px solid var(--border);
  }
  summary {
    cursor: pointer;
    list-style: none;
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    padding: 16px 0;
    font-size: 15px;
  }
  summary::-webkit-details-marker {
    display: none;
  }
  summary:hover {
    color: var(--ember);
  }
  .body {
    padding: 0 0 20px;
    color: var(--muted);
    font-size: 13.5px;
    line-height: 1.6;
  }
  .body p {
    margin: 0 0 10px;
    max-width: 62ch;
  }
  pre {
    margin: 0 0 12px;
    padding: 14px;
    background: var(--surface-2);
    border: 1px solid var(--border);
    overflow-x: auto;
  }
  code {
    font-family: var(--mono);
    font-size: 11.5px;
    line-height: 1.7;
    color: var(--text);
  }
  ul {
    margin: 0;
    padding-left: 18px;
    display: grid;
    gap: 8px;
  }
  @media (max-width: 860px) {
    .docs {
      grid-template-columns: 1fr;
    }
  }
</style>
