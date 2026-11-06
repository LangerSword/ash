<script lang="ts">
  import { api } from "../lib/api";

  type EvmState = "idle" | "connecting" | "verified" | "error";
  let account = $state("");
  let state = $state<EvmState>("idle");
  let note = $state("");

  const projectId = import.meta.env.VITE_WC_PROJECT_ID ?? "";
  const hasEvm = $derived(typeof window !== "undefined" && "ethereum" in window);

  async function connectEvm() {
    const eth = (window as unknown as { ethereum?: { request: (a: unknown) => Promise<unknown> } })
      .ethereum;
    if (!eth) {
      state = "error";
      note = "No EVM wallet detected in this browser.";
      return;
    }
    state = "connecting";
    note = "";
    try {
      const accounts = (await eth.request({ method: "eth_requestAccounts" })) as string[];
      const acct = accounts?.[0];
      if (!acct) throw new Error("wallet returned no account");
      const { message } = await api.walletNonce("evm", acct);
      const signature = (await eth.request({
        method: "personal_sign",
        params: [message, acct],
      })) as string;
      await api.walletVerify("evm", acct, signature);
      account = acct;
      state = "verified";
    } catch (e) {
      state = "error";
      note = (e as Error).message || "wallet connection failed";
    }
  }
</script>

<div class="wallet">
  <div class="wallet-row">
    <span class="label">EVM wallet</span>
    <span class="value" data-ok={state === "verified" ? 1 : 0} title={account}>
      {#if state === "verified"}verified · {account.slice(0, 8)}…{account.slice(-4)}
      {:else if state === "connecting"}waiting for signature…
      {:else if state === "error"}{note}
      {:else if hasEvm}not connected
      {:else}no injected wallet{/if}
    </span>
    <button class="btn" onclick={connectEvm} disabled={state === "connecting" || state === "verified"}>
      {state === "verified" ? "Verified" : "Connect"}
    </button>
  </div>

  <div class="wallet-row">
    <span class="label">Hedera wallet</span>
    <span class="value">
      {#if projectId}WalletConnect configured · HashPack / Blade{/if}
      {#if !projectId}WalletConnect not configured{/if}
    </span>
    <button class="btn" disabled={true} title="Needs VITE_WC_PROJECT_ID and a Hedera dApp connector">
      {projectId ? "Connect" : "Unavailable"}
    </button>
  </div>
</div>
<p class="wallet-note">Wallets prove control here. They do not hold the payload key.</p>
