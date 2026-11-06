<script lang="ts">
  let copied = $state("");

  async function copy(text: string, id: string) {
    try {
      await navigator.clipboard.writeText(text);
      copied = id;
      setTimeout(() => (copied = ""), 1600);
    } catch {
      copied = "fail";
    }
  }

  const one = "curl -fsSL https://langersword.github.io/ash/install.sh | bash";
</script>

<section class="install" id="install">
  <div class="inner">
    <div class="lead">
      <h2>Get the seal running.</h2>
      <p>
        Ash runs on Linux against the board over USB. The installer creates a venv, wires the board's
        API, and puts one command on your path.
      </p>
      <div class="cta">
        <a class="btn" href="https://github.com/LangerSword/ash" rel="noopener">Repository</a>
        <a class="btn ghost" href="#screens">See the app</a>
      </div>
    </div>

    <div class="panels">
      <div class="panel">
        <div class="row">
          <span class="mono">install · linux</span>
          <button class="copy" onclick={() => copy(one, "one")}>
            {copied === "one" ? "copied" : "copy"}
          </button>
        </div>
        <pre><code>{one}</code></pre>
        <p class="note">
          Needs <code>git</code>, <code>python3</code> 3.10+, <code>adb</code>, and the board app
          running. The script prints a check for each before it writes anything.
        </p>
      </div>

      <div class="panel">
        <div class="row">
          <span class="mono">desktop app · appimage</span>
          <span class="badge">in build</span>
        </div>
        <p class="note">
          A packaged AppImage with the device link, the intro, and the legend is specified and under
          construction. There is no download link until it exists.
        </p>
        <pre><code>cd app && npm install
npm run tauri build -- --bundles appimage</code></pre>
        <p class="note">
          Specification:
          <a href="https://github.com/LangerSword/ash/blob/master/docs/DESKTOP_APP.md" rel="noopener"
            >docs/DESKTOP_APP.md</a
          >
        </p>
      </div>
    </div>
  </div>
</section>

<style>
  .install {
    background: var(--surface);
    border-top: 1px solid var(--border);
    border-bottom: 1px solid var(--border);
  }
  .inner {
    max-width: var(--max);
    margin: 0 auto;
    padding: clamp(64px, 10vh, 120px) var(--gutter);
    display: grid;
    grid-template-columns: 0.85fr 1.15fr;
    gap: clamp(28px, 6vw, 80px);
  }
  h2 {
    font-size: clamp(30px, 3.8vw, 48px);
    line-height: 1.03;
    letter-spacing: -0.035em;
    margin: 0 0 16px;
    font-weight: 500;
  }
  .lead p {
    margin: 0 0 24px;
    color: var(--muted);
    font-size: 15px;
    line-height: 1.6;
    max-width: 40ch;
  }
  .cta {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
  }
  .panels {
    display: grid;
    gap: 16px;
    align-content: start;
  }
  .panel {
    border: 1px solid var(--border);
    padding: 16px;
    background: var(--bg);
  }
  .row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
  }
  .mono {
    font-family: var(--mono);
    font-size: 10.5px;
    letter-spacing: 0.13em;
    text-transform: uppercase;
    color: var(--dim);
  }
  .badge {
    font-family: var(--mono);
    font-size: 10px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--amber);
    border: 1px solid rgba(255, 176, 32, 0.3);
    padding: 2px 6px;
  }
  .copy {
    background: none;
    border: 1px solid var(--border-strong);
    color: var(--muted);
    font-family: var(--mono);
    font-size: 10.5px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 3px 8px;
    cursor: pointer;
  }
  .copy:hover {
    color: var(--text);
    border-color: var(--ember);
  }
  pre {
    margin: 0 0 10px;
    padding: 12px;
    background: var(--surface-2);
    border: 1px solid var(--border);
    overflow-x: auto;
  }
  code {
    font-family: var(--mono);
    font-size: 11.5px;
    color: var(--text);
  }
  .note {
    margin: 0;
    color: var(--muted);
    font-size: 12.5px;
    line-height: 1.55;
  }
  .note a {
    color: var(--text);
  }
  @media (max-width: 900px) {
    .inner {
      grid-template-columns: 1fr;
    }
  }
</style>
