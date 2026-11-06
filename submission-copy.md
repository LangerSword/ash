# Submission copy

**Title:** Ash — a seal that destroys the data if you open it

**One-liner:** A tamper-responsive seal for confidential shipments: open the case without
authorisation and the key dies, the contents become noise, and an agent pays a cent to verify it.

**Description:**
Confidential material still moves in boxes — discovery files, prototypes, samples, evidence — and the
only protection is a plastic seal and a signature. Ash puts the detector and the key in the same
offline computer inside the seal. A hard break erases the key in about a millisecond, with no network
and no host in the path. An ambiguous event goes to 0G, which decides hold or wipe against a
five-second deadline, and silence means wipe. Unsealing needs a World ID proof and a 0G release
decision before the MCU releases the payload key. The custody record is hash-chained, and any agent
can read it for a cent over x402 on Hedera.

**Tracks:** 0G Physical AI · World (Best Use of IDKit) · Hedera (AI Agents That Pay: x402)

**Repo:** https://github.com/LangerSword/ash
**Live:** https://ash.langersword.in/ (API: https://api.langersword.in)

**What is real / what is not:** real MCU wipe and key derivation, real 0G Router decisions with
request ids, real World IDKit request flow; sandbox World identity, dev-mode loop simulation, and
Hedera settlement not yet executed.
