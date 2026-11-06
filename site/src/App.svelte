<script lang="ts">
  import HeroBurn from "./components/HeroBurn.svelte";
  import TierScroll from "./components/TierScroll.svelte";
  import Evidence from "./components/Evidence.svelte";
  import UseCase from "./components/UseCase.svelte";
  import Docs from "./components/Docs.svelte";
  import Install from "./components/Install.svelte";
</script>

<a class="skip" href="#how">Skip to the seal</a>

<header class="nav">
  <a class="mark" href="#top">Ash <span class="kanji">灰</span></a>
  <div class="nav-right">
    <nav aria-label="Sections">
      <a href="#how">The seal</a>
      <a href="#evidence">Evidence</a>
      <a href="#docs">Docs</a>
      <a href="#install">Install</a>
    </nav>
    <a class="gh" href="https://github.com/LangerSword/ash" rel="noopener" aria-label="Repository on GitHub">
      <svg width="17" height="17" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
        <path
          d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82a7.4 7.4 0 0 1 2-.27c.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8Z"
        />
      </svg>
    </a>
  </div>
</header>

<main id="top">
  <section class="hero">
    <h1 class="sr-only">Ash, a seal that destroys the data if you open it</h1>
    <div class="stage"><HeroBurn /></div>

    <div class="hero-meta">
      <p>
        <em>Ash</em> is a tamper-responsive seal for confidential shipments. Break the loop and the key
        dies in the chip, before anyone reads a byte.
      </p>
      <a class="hero-link" href="#install">Install the app</a>
    </div>

    <p class="vertical" aria-hidden="true">灰になる</p>
    <p class="hero-caption mono">one burn, then ash</p>
  </section>

  <TierScroll />
  <Evidence />
  <UseCase />
  <Docs />
  <Install />
</main>

<footer class="foot">
  <div class="foot-in">
    <div>
      <span class="mark">Ash <span class="kanji">灰</span></span>
      <p>Built at ETHGlobal Mumbai 2026. One board, one loop, one key.</p>
    </div>
    <div class="foot-links">
      <a href="https://github.com/LangerSword/ash" rel="noopener">Source</a>
      <a href="#docs">Limits</a>
      <a href="#install">Install</a>
    </div>
  </div>
</footer>
