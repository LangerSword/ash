<script lang="ts">
  import { onMount } from "svelte";
  import type { Connection, Step } from "../lib/connect";

  type Props = {
    conn: Connection;
    busy: string;
    onAction: (kind: Step["action"] extends undefined ? never : NonNullable<Step["action"]>["kind"]) => void;
    compact?: boolean;
  };

  let { conn, busy, onAction, compact = false }: Props = $props();

  // a visible clock: a connection that never resolves must still look alive
  let elapsed = $state(0);
  let since = 0;
  onMount(() => {
    since = performance.now();
    const id = window.setInterval(() => {
      elapsed = Math.floor((performance.now() - since) / 1000);
    }, 1000);
    return () => window.clearInterval(id);
  });

  const dot = (s: Step) =>
    s.state === "ok" ? "ok" : s.state === "fail" ? "fail" : s.state === "action" ? "action" : s.state === "working" ? "working" : "idle";
</script>

<div class="conn" data-ready={conn.ready ? 1 : 0} data-compact={compact ? 1 : 0}>
  <div class="head">
    <span class="label">{conn.headline}</span>
    {#if !conn.ready && conn.transient}
      <span class="clock num">{elapsed}s</span>
    {/if}
  </div>

  <ol>
    {#each conn.steps as s (s.key)}
      <li data-state={dot(s)}>
        <span class="mark" aria-hidden="true"></span>
        <span class="name">{s.label}</span>
        <span class="detail" title={s.detail}>{s.detail}</span>
        {#if s.action}
          <button
            class="mini"
            disabled={busy !== ""}
            data-busy={busy === s.action.kind ? 1 : 0}
            onclick={() => onAction(s.action!.kind)}
          >
            {s.action.label}
          </button>
        {/if}
      </li>
    {/each}
  </ol>

  {#if conn.hint}
    <p class="hint">{conn.hint}</p>
  {/if}
</div>

<style>
  .conn {
    border: 1px solid var(--border);
    border-radius: var(--radius);
    background: var(--surface);
    display: grid;
    gap: 0;
    min-width: 0;
  }

  .conn[data-ready="1"] {
    border-color: #24422a;
    background: #0f1410;
  }

  .head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    padding: 8px 11px;
    border-bottom: 1px solid var(--border);
  }

  .conn[data-ready="1"] .head {
    border-color: #1d3322;
  }

  .conn[data-ready="1"] .head .label {
    color: var(--signal);
  }

  .clock {
    font-size: 11px;
    color: var(--amber);
  }

  ol {
    list-style: none;
    margin: 0;
    padding: 4px 0;
    display: grid;
  }

  li {
    display: grid;
    grid-template-columns: 14px 92px minmax(0, 1fr) auto;
    align-items: center;
    gap: 8px;
    padding: 4px 11px;
    font-size: 11.5px;
    min-height: 26px;
  }

  .mark {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    border: 1px solid var(--border-strong);
    background: transparent;
  }

  li[data-state="ok"] .mark {
    background: var(--signal);
    border-color: var(--signal);
  }

  li[data-state="working"] .mark {
    background: var(--amber);
    border-color: var(--amber);
    animation: pulse 1.2s ease-in-out infinite;
  }

  li[data-state="action"] .mark {
    background: transparent;
    border-color: var(--amber);
  }

  li[data-state="fail"] .mark {
    background: var(--alert);
    border-color: var(--alert);
  }

  @keyframes pulse {
    0%, 100% { opacity: 0.35; }
    50% { opacity: 1; }
  }

  .name {
    color: var(--muted);
  }

  li[data-state="ok"] .name {
    color: var(--text);
  }

  .detail {
    color: var(--dim);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  li[data-state="fail"] .detail {
    color: var(--alert);
  }

  li[data-state="action"] .detail {
    color: var(--amber);
  }

  .mini {
    height: 20px;
    padding: 0 7px;
    font-size: 10px;
    background: transparent;
    color: var(--text);
    border: 1px solid var(--border-strong);
    border-radius: 3px;
    cursor: pointer;
  }

  .mini:hover:not(:disabled) {
    border-color: var(--signal);
    color: var(--signal);
  }

  .mini:disabled {
    opacity: 0.5;
    cursor: default;
  }

  .hint {
    padding: 0 11px 9px 33px;
    font-size: 11px;
    color: var(--dim);
  }

  .conn[data-compact="1"] li {
    grid-template-columns: 14px 78px minmax(0, 1fr) auto;
    font-size: 11px;
  }
</style>
