# Ash, 3-minute demo script

**Setup:** board on the table, USB to the laptop, `cloudflared` tunnel running, API on :8080,
site open at https://ash.langersword.in/ with the chip reading `ARMED`.

| time | action | say |
|---|---|---|
| 0:00 | Site open on the hero. Click **Open it the wrong way** | "This is a seal. Break it and the key dies before anyone reads a byte." |
| 0:10 | The box burns into ASH on screen | "That is the promise, not a video. The device does the same thing in about 1.3 milliseconds." |
| 0:25 | Click **Seal container** | "Sealing derives a key from the MCU's secret and encrypts the payload. The ledger row is hash-chained." |
| 0:45 | Click **Flex loop (Tier 1)** | "Someone bent the wire. The MCU goes amber and asks 0G whether that's handling or intrusion, with a five-second deadline." |
| 1:00 | Amber bar drains, chip returns to ARMED | "0G said hold. If it had said nothing, the deadline would have wiped the key. Silence is not consent." |
| 1:20 | Click **Cut loop (Tier 0)** | "Now it's cut. No network, no model, no host, the MCU erases the key and reads the page back." |
| 1:35 | Matrix red X, state TAMPERED | "One and a third milliseconds. The payload is noise now, and the record says when." |
| 1:50 | Click **Unseal (test proof)** → 403 | "Unsealing after tamper is refused. The key is gone; there is nothing to release." |
| 2:05 | **Reprovision**, then **Unseal with World ID** | "Second box. This one needs a human: a World ID proof, then a 0G release decision before the MCU hands over the key." |
| 2:25 | QR on screen, scan with the phone | "The QR is a World ID request signed by our RP key; the proof is verified server-side." |
| 2:45 | Payload opens | "That's the whole stack: hardware custody, a model in the loop with a deadline, and a human checkpoint." |
| 2:55 | Close on the disclosures block | "Not a secure element, loop covers one path, sandbox identity. Everything we can't claim is written down." |

**Do not** claim: a settled Hedera payment, a production World identity, or SWD resistance.
