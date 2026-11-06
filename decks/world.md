# World — Best Use of IDKit pitch (8 slides)

**Deck style:** black, monospace, one idea per slide.

---

**1 · Cover**
ASH · the seal asks a human before it gives up the key
World · Best Use of IDKit · ETHGlobal Mumbai 2026

**2 · The trust moment**
Releasing the payload key is irreversible: once opened with the key, the contents exist outside the seal.
That is the one moment a product must know a *specific human* is present — not a session, not a cookie.

**3 · The credential, and why it is the minimum**
Selfie Check / Proof of Human: "one unique human is here, now".
Passport/NFC would be more assurance than this action needs. We say that out loud.

**4 · The flow**
QR → World App approves → IDKit result → **server-side verify** against
`developer.world.org/api/v4/verify/{rp_id}` → nullifier → bound to that container.
The client never decides anything.

**5 · The denial path is the product**
Cancel, expire, or verify-fail → `UNSEAL_DENIED` in the ledger, no key, LED stays red.
A proof that cannot fail is not a checkpoint.

**6 · Why not a login**
A login authenticates a session. This authenticates a *release*: scoped to one container, one action,
one moment, with a nullifier that cannot be replayed.

**7 · What is honest**
Sandbox identity today; proofs are test credentials. The flow, the verification and the denial are real.

**8 · Ask**
For field deployments, is Selfie Check enough, or does the insurer require Passport/NFC for unsealing?
