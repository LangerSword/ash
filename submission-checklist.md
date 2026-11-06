# Submission checklist

**Deadline:** 7 Nov 2026, 09:00 IST. **Project:** Ash. **Repo:** github.com/LangerSword/ash
**Live:** https://langersword.github.io/ash/ · **API:** https://api.langersword.in

## 1. Form fields

| Field | Paste |
|---|---|
| Project name | Ash |
| One-liner | A seal that destroys the data if you open it. |
| Description | Use the first two paragraphs of `submission-copy.md`. |
| Repo | https://github.com/LangerSword/ash |
| Live demo | https://langersword.github.io/ash/ |
| Video | (link after recording, under 3 min) |
| Track 1 | 0G - Physical AI: Agents with a Body |
| Track 2 | World - Best Use of IDKit |
| Track 3 | Hedera - AI Agents That Pay: x402 |

## 2. Three picks only

ETHGlobal allows three partner prizes. Arkiv's page states its bonus does not consume a pick; the same
logic does not extend to other sponsors. Do not add a fourth.

## 3. Per-track requirements

### 0G Physical AI ($5,000, plus the real-hardware lane)
- [x] A 0G call inside the decision loop: Tier 1 classification, `gemini-2.5-flash-lite`, 2.05 s median.
- [x] Request id recorded: `18f73aef-3789-40e3-987d-178d2174d79f`, `chatcmpl-20261106104417…`
- [ ] Episode log on 0G Storage. **Not done.** Say so in the video; do not claim it.
- [x] Safe-stop when 0G is unreachable: deadline wipe, logged `0G_UNAVAILABLE`.
- [x] Live hardware demo path (the board on the desk).

### World - Best Use of IDKit ($2,500 / $2,500 split)
- [x] IDKit request with an RP signature from our backend; QR rendered client side.
- [x] Server-side verification path implemented (`/unseal` verifies before release).
- [ ] One successful real proof. **Blocked by a 403 (Cloudflare 1010) on the verify call.** Show the
      QR and the flow, state the block honestly, and show the denied path, which is real.
- [x] Denied / cancelled path: no key, `UNSEAL_DENIED`.

### Hedera - x402 ($6,500 pool)
- [x] A real `402` challenge with payee `0.0.11340251` and the official facilitator.
- [ ] A settled payment with a transaction id. **Not done.** Do not claim it.
- [ ] HCS receipt. Not done.

## 4. Video beats (3 min, see `demo-script.md`)

1. Hero: click the box, it burns into ASH (10 s).
2. Seal a container, show the ledger hash (20 s).
3. Flex the loop: amber, 0G decision, request id on screen (25 s).
4. Cut the loop: TAMPERED, key erased, unseal refused (30 s).
5. Reprovision, unseal with World ID: QR, then the honest note about the verify block (30 s).
6. Show `/attestation` returning 402 and explain the price and the payee (20 s).
7. Close on the limits section of the site (15 s).

## 5. Disclosures to say out loud

- Not a certified secure element; SWD bench access is possible.
- The loop covers one path; a determined enclosure opening is out of scope.
- World identity is a sandbox credential; the verify call is blocked today.
- The Hedera endpoint prices and challenges; no payment has settled.
- No AppImage is published yet; the installer runs from source.

## 6. Final 20 minutes

- [ ] `git status` clean, `.env` untracked.
- [ ] Pages deployment green for the final commit.
- [ ] `https://api.langersword.in/status` returns the board.
- [ ] Video uploaded, link opens in a private window.
- [ ] Submission saved before 08:45 IST.
