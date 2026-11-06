<script lang="ts">
  const tiers = [
    {
      n: "00",
      title: "Local wipe",
      body: "250 ms of continuous open → erase MASTER, read back 0xFF, record TAMPERED. No network, no host, no model.",
    },
    {
      n: "01",
      title: "Ambiguous event",
      body: "Amber. The MCU sends a feature vector to 0G and starts a deadline. The model may hold until the deadline or ask for a wipe; it can never un-wipe. Silence means wipe, logged as 0G_UNAVAILABLE.",
    },
    {
      n: "02",
      title: "Authorised unseal",
      body: "A World ID proof, then a 0G release|deny, then the MCU releases the payload key. Deny, timeout or no network: no key.",
    },
  ] as const;
</script>

<div class="tiers">
  {#each tiers as t (t.n)}
    <div class="tier" data-tier={t.n === "00" ? 0 : t.n === "01" ? 1 : 2}>
      <div class="num">{t.n}</div>
      <h3>{t.title}</h3>
      <p>{t.body}</p>
    </div>
  {/each}
</div>
<p class="tier-foot">The model is never on the kill path. It is in the loop, with a deadline, and it fails closed.</p>
