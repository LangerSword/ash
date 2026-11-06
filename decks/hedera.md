# Hedera — x402 pitch (8 slides)

**Deck style:** black, monospace, one idea per slide.

---

**1 · Cover**
ASH · the custody record is a one-cent API call
Hedera · AI Agents That Pay: x402 · ETHGlobal Mumbai 2026

**2 · The paid resource**
`GET /attestation/:container` — the signed custody record for one sealed case.
The buyer is an insurer, a customs broker, or a receiving agent. Not a human with a browser.

**3 · The flow**
`402` with `scheme: exact`, `network: hedera:testnet`, a USDC asset, a payee, and the facilitator's
fee payer → the agent signs a `TransferTransaction` → `verify` → `settle` → `200` with the tx id and a
HashScan link.

**4 · Why Hedera, not a generic L1**
Fixed low fees and seconds of finality make a $0.01 read viable. HTS USDC matches the currency the
shipment is insured in. The facilitator pays the network fee, so the agent needs no HBAR.

**5 · The audit line**
Every settled payment writes a receipt to an HCS topic. A regulator can read it off the mirror node
with none of our code in the loop.

**6 · Economics**
Per seal: ₹200–500. Per verification: $0.01. An insurer pays the cent because it lowers the loss.
One device serves many shipments.

**7 · What is honest**
The 402 challenge is live with a real payee (`0.0.11340251`) and the official facilitator
(`x402.org`, fee payer `0.0.9185802`). End-to-end settlement is not yet executed; we do not claim it.

**8 · Ask**
Which facilitator do you recommend for production: official, Launa, or self-run — and do you want
HCS receipts on every payment or batched per day?
