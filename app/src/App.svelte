<script lang="ts">
  import { onMount } from "svelte";
  import { ui } from "./lib/ui.svelte";
  import Intro from "./components/Intro.svelte";
  import DeviceCheck from "./components/DeviceCheck.svelte";
  import WorldStep from "./components/WorldStep.svelte";
  import Legend from "./components/Legend.svelte";
  import Console from "./components/Console.svelte";
  import { cmd } from "./lib/tauri";

  type Step = "boot" | "intro" | "device" | "world" | "legend" | "console";

  let step = $state<Step>("boot");
  let reduced = $state(false);

  onMount(async () => {
    reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    await ui.boot();
    const cfg = ui.runtime?.config;
    if (!cfg) {
      step = "device";
      return;
    }
    if (!cfg.intro_seen) step = "intro";
    else if (!cfg.legend_seen) step = "legend";
    else step = "console";
  });

  function afterIntro() {
    ui.saveConfig({ intro_seen: true });
    step = "device";
  }

  function afterDevice() {
    void ui.loadWorld();
    step = "world";
  }

  function afterWorld() {
    step = "legend";
  }

  function afterLegend() {
    ui.saveConfig({ legend_seen: true });
    step = "console";
  }

  async function startBoard() {
    try {
      const out = await cmd<string>("start_board_app");
      ui.event(out);
      await ui.pull();
    } catch (e) {
      ui.event(`start board app failed: ${e instanceof Error ? e.message : String(e)}`);
    }
  }

  async function installUdev() {
    try {
      ui.event(await cmd<string>("install_udev"));
    } catch (e) {
      ui.event(`udev: ${e instanceof Error ? e.message : String(e)}`);
    }
  }
</script>

{#if step === "boot"}
  <div class="boot"></div>
{:else if step === "intro"}
  <Intro
    {reduced}
    onDone={afterIntro}
    onBoard={(note) => ui.event(note)}
  />
{:else if step === "device"}
  <div class="page scroll">
    <DeviceCheck
      device={ui.device}
      service={ui.runtime?.service ?? null}
      busy=""
      onContinue={afterDevice}
      onStartBoard={startBoard}
      onInstallUdev={installUdev}
    />
  </div>
{:else if step === "world"}
  <div class="page scroll">
    <WorldStep config={ui.worldConfig} onContinue={afterWorld} />
  </div>
{:else}
  <Console />
  {#if step === "legend"}
    <Legend onDone={afterLegend} />
  {/if}
{/if}

<style>
  .boot {
    height: 100%;
    background: var(--bg);
  }

  .page {
    height: 100%;
    background: var(--bg);
  }
</style>
