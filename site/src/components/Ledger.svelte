<script lang="ts">
  import type { LedgerRecord } from "../lib/api";

  let { records = [] as LedgerRecord[] }: { records?: LedgerRecord[] } = $props();

  const shown = $derived(records.slice(-8).reverse());

  function clock(at?: number): string {
    if (!at) return "n/a";
    const d = new Date(at * 1000);
    return d.toTimeString().slice(0, 8);
  }

  function decision(r: LedgerRecord): string {
    const g = r["0g"] as { decision?: string } | undefined;
    return g?.decision ?? "n/a";
  }
</script>

<div class="ledger">
  <h3>Ledger</h3>
  {#if shown.length === 0}
    <div class="ledger-empty">No records yet. Seal a container to start the chain.</div>
  {:else}
    <div class="table-wrap">
    <table>
      <thead>
        <tr><th>event</th><th>container</th><th>time</th><th>0G</th><th>hash</th></tr>
      </thead>
      <tbody>
        {#each shown as r (r.hash ?? `${r.event}-${r.at}`)}
          <tr>
            <td class="event" data-event={r.event}>{r.event}</td>
            <td>{r.container ?? "n/a"}</td>
            <td>{clock(r.at)}</td>
            <td>{decision(r)}</td>
            <td title={r.hash ?? ""}>{(r.hash ?? "").slice(0, 8) || "n/a"}</td>
          </tr>
        {/each}
      </tbody>
    </table>
    </div>
  {/if}
</div>
