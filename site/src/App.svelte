<script lang="ts">
  import { onMount } from "svelte";
  import Hero from "./components/Hero.svelte";
  import Section from "./components/Section.svelte";
  import TierStack from "./components/TierStack.svelte";
  import DemoPanel from "./components/DemoPanel.svelte";
  import Evidence from "./components/Evidence.svelte";
  import Disclosures from "./components/Disclosures.svelte";
  import WalletPanel from "./components/WalletPanel.svelte";
  import Footer from "./components/Footer.svelte";
  import { start, stop } from "./lib/store.svelte";

  onMount(() => {
    void start();
    return () => stop();
  });
</script>

<a class="skip" href="#demo">Skip to the live seal</a>

<div class="shell">
  <Hero />

  <main>
    <Section title="The problem">
      <div class="prose">
        <p>
          Confidential material still moves in boxes. Discovery files, prototypes, samples, evidence.
          The only protection is a plastic seal and a signature.
        </p>
        <p>
          A plastic seal proves nothing. A server-side delete can be paused, rolled back, or subpoenaed.
        </p>
        <p>
          <strong>Ash</strong> puts the detector and the key in the same offline computer, inside the seal.
          Break the loop and the key is gone. Bend it, and a model decides whether that was handling or
          intrusion — against a deadline, where silence means wipe.
        </p>
      </div>
      <p class="caption">
        NIST SP 800-88r2 recognises cryptographic erase · ISO 17712 is the mechanical seal it upgrades ·
        DPDP Act 2023 s.8(7) requires erasure
      </p>
    </Section>

    <Section title="How it works">
      <TierStack />
    </Section>

    <Section id="demo" title="Live seal">
      <DemoPanel />
      <p class="caption">
        The panel talks to the board over USB. If the board is absent it says so and disables the controls;
        nothing on this page invents a device state.
      </p>
    </Section>

    <Section title="Evidence">
      <Evidence />
    </Section>

    <Section title="What breaks without 0G">
      <div class="prose">
        <p>
          Nothing detects the ambiguous case. The seal falls back to a hard rule: any interruption wipes.
          Safe, and unusable for normal handling.
        </p>
      </div>
    </Section>

    <Section title="Disclosures">
      <Disclosures />
    </Section>

    <Section title="Wallets">
      <WalletPanel />
    </Section>
  </main>

  <Footer />
</div>
