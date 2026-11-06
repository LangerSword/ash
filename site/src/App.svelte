<script lang="ts">
  import { onMount } from "svelte";
  import BurnHero from "./components/BurnHero.svelte";
  import TierScroll from "./components/TierScroll.svelte";
  import DemoPanel from "./components/DemoPanel.svelte";
  import UseCase from "./components/UseCase.svelte";
  import Docs from "./components/Docs.svelte";
  import Install from "./components/Install.svelte";
  import { start, stop } from "./lib/store.svelte";

  onMount(() => {
    void start();
    return () => stop();
  });
</script>

<a class="skip" href="#demo">Skip to the live seal</a>

<header class="nav">
  <a class="mark" href="#top">ASH</a>
  <nav aria-label="Sections">
    <a href="#how">How it works</a>
    <a href="#demo">Live seal</a>
    <a href="#docs">Docs</a>
    <a href="#install">Install</a>
  </nav>
  <a class="gh" href="https://github.com/LangerSword/ash" rel="noopener" aria-label="Repository on GitHub">
    <svg width="18" height="18" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
      <path
        d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82a7.4 7.4 0 0 1 2-.27c.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8Z"
      />
    </svg>
  </a>
</header>

<main id="top">
  <section class="masthead">
    <div class="masthead-copy">
      <p class="kicker mono">tamper-responsive seal · arduino uno q</p>
      <h1>Open it the<br />wrong way.<br /><em>It becomes ash.</em></h1>
      <p class="sub">
        A seal for confidential shipments. Break the loop and the key dies in the chip before anyone
        reads a byte.
      </p>
      <div class="actions">
        <a class="btn" data-kind="primary" href="#install">Install the app</a>
        <a class="btn" href="#how">How it decides</a>
      </div>
    </div>
    <div class="masthead-visual">
      <BurnHero />
      <p class="caption mono">try it · the box on your screen is not a video</p>
    </div>
  </section>

  <TierScroll />

  <section class="live" id="demo">
    <div class="live-head">
      <h2>The seal, live.</h2>
      <p>
        This panel talks to the board on the desk over its own API. Seal, bend the loop, cut it, and
        watch the state change. If the board is offline it says so.
      </p>
    </div>
    <DemoPanel />
  </section>

  <UseCase />
  <Docs />
  <Install />
</main>

<footer class="foot">
  <div class="foot-in">
    <div>
      <span class="mark">ASH</span>
      <p>Built at ETHGlobal Mumbai 2026. One board, one loop, one key.</p>
    </div>
    <div class="foot-links">
      <a href="https://github.com/LangerSword/ash" rel="noopener">Source</a>
      <a href="#docs">Limits</a>
      <a href="#install">Install</a>
    </div>
  </div>
</footer>
