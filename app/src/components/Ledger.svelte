<script lang="ts">
  import type { LedgerRecord } from "../lib/types";

  type Props = {
    records: LedgerRecord[];
    verify: { ok: boolean; detail: string; records: number } | null;
    busy: string;
    container: string;
    onVerify: () => void;
    onAttest: () => void;
  };

  let { records, verify, busy, container, onVerify, onAttest }: Props = $props();

  const rows = $derived([...records].reverse().slice(0, 8));

  function hhmmss(at?: number): string {
    if (!at) return "—";
    const d = new Date(at * 1000);
    return [d.getHours(), d.getMinutes(), d.getSeconds()]
      .map((n) => String(n).padStart(2, "0"))
      .join(":");
  }

  function g0(r: LedgerRecord): { text: string; title: string } {
    const g = (r["0g"] ?? r.meta ?? {}) as { decision?: string; request_id?: string; reason?: string };
    if (g.decision) return { text: g.decision, title: JSON.stringify(g) };
    if (g.request_id) return { text: g.request_id.slice(0, 8), title: g.request_id };
    if (g.reason) return { text: String(g.reason).slice(0, 12), title: String(g.reason) };
    return { text: "—", title: "" };
  }
</script>

<section class="ledger">
  <div class="bar">
    <span class="label">Ledger · last 8</span>
    <div class="bar-actions">
      {#if verify}
        <span class="verify" data-ok={verify.ok ? 1 : 0} title={verify.detail}>
          {verify.ok ? `chain ok · ${verify.records}` : `mismatch at ${verify.detail}`}
        </span>
      {/if}
      <button class="btn" disabled={busy !== ""} onclick={onVerify} data-busy={busy === "verify" ? 1 : 0}>
        Verify chain
      </button>
      <button class="btn" disabled={busy !== ""} onclick={onAttest} title={`Read /attestation/${container} (x402)`}>
        Attestation
      </button>
    </div>
  </div>

  <div class="table-scroll scroll">
    <table>
      <thead>
        <tr>
          <th>event</th>
          <th>container</th>
          <th>time</th>
          <th>0G</th>
          <th>hash</th>
        </tr>
      </thead>
      <tbody>
        {#each rows as r (r.hash ?? `${r.event}-${r.at}`)}
          <tr data-event={r.event}>
            <td>{r.event}</td>
            <td>{r.container ?? "—"}</td>
            <td class="num">{hhmmss(r.at)}</td>
            <td title={g0(r).title}>{g0(r).text}</td>
            <td class="hash" title={r.hash ?? ""}>{(r.hash ?? "").slice(0, 8) || "—"}</td>
          </tr>
        {:else}
          <tr>
            <td colspan="5" class="empty">No episodes yet. Seal a container.</td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
</section>

<style>
  .ledger {
    display: grid;
    grid-template-rows: auto minmax(0, 1fr);
    min-height: 200px;
    border-top: 1px solid var(--border);
  }

  .bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 10px 16px;
    border-bottom: 1px solid var(--border);
  }

  .bar-actions {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .bar .btn {
    height: 24px;
    padding: 0 8px;
    font-size: 11px;
  }

  .verify {
    font-size: 11px;
    color: var(--muted);
    font-variant-numeric: tabular-nums;
  }

  .verify[data-ok="1"] {
    color: var(--signal);
  }

  .verify[data-ok="0"] {
    color: var(--alert);
  }

  .table-scroll {
    min-height: 0;
  }

  table {
    width: 100%;
    table-layout: fixed;
    border-collapse: collapse;
    font-size: 12px;
    font-variant-numeric: tabular-nums;
  }

  th:nth-child(1) { width: 32%; }
  th:nth-child(2) { width: 16%; }
  th:nth-child(3) { width: 11%; }
  th:nth-child(4) { width: 15%; }
  th:nth-child(5) { width: 26%; }

  th {
    position: sticky;
    top: 0;
    background: var(--bg);
    text-align: left;
    font-weight: 400;
    color: var(--dim);
    letter-spacing: 0.12em;
    text-transform: uppercase;
    padding: 8px 16px;
    border-bottom: 1px solid var(--border);
  }

  td {
    padding: 6px 16px;
    border-bottom: 1px solid #16161a;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  tr[data-event="TAMPERED"] td:first-child,
  tr[data-event="UNSEAL_DENIED"] td:first-child {
    color: var(--alert);
  }

  tr[data-event="SEALED"] td:first-child,
  tr[data-event="UNSEALED"] td:first-child {
    color: var(--signal);
  }

  .hash {
    color: var(--dim);
    font-size: 10px;
  }

  .empty {
    color: var(--dim);
    padding: 14px;
  }
</style>
