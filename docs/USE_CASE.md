# The use case, and why Hedera

## The product in one sentence

A seal for physical shipments of data: if anyone opens the case, the contents become unreadable, and the
break is recorded in a form the receiver, the insurer, and an auditor can all check without trusting us.

## Who pays, and for what

| Buyer | What they ship | What they buy | Why the seal |
|---|---|---|---|
| **Litigation support / law firms** | Laptops and drives with privileged discovery, settlement drafts, expert reports | One seal per shipment + one verification per receipt | A courier opening the case is a privilege breach with a notification duty. A plastic seal proves nothing after the fact |
| **Clinical trial sponsors and CROs** | Patient-derived samples, blinded data, trial master files | Seal + custody record retained for the trial's life | The record has to survive an inspection years later; expiry is set to the retention period, not to our business |
| **Hardware and IP teams** | Prototypes, firmware images, tooling | Seal per prototype + attestation per handover | The prototype is worth more than the courier's insurance; the design files must not survive a curious customs officer |
| **Insurers** | The above, underwritten | Per-attestation read of the custody record | They will not accept a PDF from the shipper; they will accept a record they can check |
| **Evidence handlers / labs** | Sealed samples and drives | Seal + chain-of-custody record | Chain of custody is the evidence's admissibility |

**Revenue shape:** a one-off device (₹4–6k BOM at scale), a per-seal fee (₹200–500), and a per-verification
fee (₹0.80–1.00, i.e. $0.01). The insurer, not the shipper, tends to pay the verification because it
reduces their loss.

## Three concrete scenarios

**1. The settlement draft.**
A Mumbai firm sends a laptop with a settlement draft to counsel in Delhi. The case is sealed at 09:12;
the courier's depot scanner logs nothing unusual; the case arrives with the loop intact and the receiver
verifies the record for a cent before opening. If the loop had been cut, the draft would be ciphertext
and the firm would know the exact minute — not "sometime in transit".

**2. The blinded sample.**
A CRO ships 40 blinded samples to a lab. Each seal carries a retention expiry equal to the trial's
record-retention period. A missing seal at receipt is not a lost parcel; it is a documented custody gap
that the sponsor can attach to the deviation report without asking anyone to re-create a log.

**3. The prototype.**
A hardware team ships a board to a contract manufacturer. The firmware image is on the device inside the
case, encrypted under the seal's key. A customs inspection that opens the case destroys the key; the
manufacturer receives a bricked image and a record saying why, which is exactly what the team wants
compared with a copied firmware.

## Why Hedera, specifically

The attestation is a **one-cent read by software**, often by an agent acting for an insurer. That shapes
every requirement:

1. **Fixed, low fees and fast finality.** A $0.01 attestation only works on a network where the fee is
   small, predictable, and settled in seconds. On a general-purpose L1 the fee can exceed the price of
   the thing being sold.
2. **HTS USDC settlement.** The shipment is insured in dollars; the attestation is priced in dollars. The
   buyer pays in USDC over HTS, not in a volatile token it has to hedge.
3. **The facilitator pays the network fee.** The paying agent needs USDC, not HBAR. Software that pays
   per request should not have to hold a gas token; the `x402` exact scheme on Hedera puts the fee on the
   facilitator.
4. **HCS as an independent audit line.** Every settled payment writes a receipt to a Hedera Consensus
   Service topic. A regulator can read that topic off the mirror node with none of our code in the loop.
   That is the difference between "our database says so" and "the network says so".
5. **Scheduled transactions.** Retention and renewal reminders can be scheduled on-network instead of in
   a cron job we have to keep alive.
6. **x402 `exact` is per-request by design.** One attestation, one price, one payment — no subscription,
   no API key, no invoice. That is what an agent can actually do at 3 a.m.

## Why not a normal database

The parties do not trust each other. The shipper controls the device, the courier is the suspect, the
receiver wants proof, and the insurer wants a record it can price. A database owned by any one of them is
only as good as that party's willingness to show it. The seal's record is signed by the device, chained,
and anchored where all of them can read it.

## What is honest today

- The device, the wipe, the 0G decision and the World checkpoint are real and measured.
- The Hedera endpoint returns a correct `402` challenge with a real payee and the official facilitator;
  settlement is not yet executed end to end. Pitch it as "priced and payable", not "paid".
- The seal is a proof of concept, not a certified secure element. It is evidence, not impenetrability.
