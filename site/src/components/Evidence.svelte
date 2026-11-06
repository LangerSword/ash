<script lang="ts">
  const rows = [
    ["flash page erase", "874 µs", "STM32U585, 8 KB page"],
    ["wipe + read-back", "1 321 µs", "erase, verify 0xFF, counter"],
    ["bridge round trip", "p50 6.19 ms / p95 7.20 ms", "1 000 calls, 0 errors"],
    ["Tier 1 decision", "2.05 s median, p95 2.11 s", "gpt-4.1-mini via 0G Router"],
    ["decision cost", "$0.000038", "0G Router trace, micro-USD"],
    ["deadline", "5 000 ms", "max(5000, 2 × p95)"],
  ] as const;
</script>

<div class="table-wrap">
<table class="evidence-table">
  <thead><tr><th>what</th><th>measured</th><th>where</th></tr></thead>
  <tbody>
    {#each rows as r (r[0])}
      <tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td></tr>
    {/each}
  </tbody>
</table>
</div>
<p class="caption">Every number came from a run on the board during this event. Request ids and ledger hashes are in the repository.</p>
