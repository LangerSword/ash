# Security notes and disclosed limitations

1. **Not a certified secure element.** Bench probing (SWD) is out of scope; RDP is unverified.
2. **The loop covers one path.** Cutting the case elsewhere, or shorting the loop, is not detected.
3. **Host sees K at seal time.** We wipe it from memory and test for it, but we cannot defend a
   sender host compromised before sealing.
4. **Unseal permit issuer** runs on the host in this prototype. No offline bypass; recovery is
   destructive.
5. **World identity is sandbox-only** (mock proofs; not production identity).
6. **Network egress:** direct on ETHGlobal WiFi; when the USB relay is used,
   "Board network egress is via a USB-attached laptop relay; decisions are made by 0G, not the relay."
7. **Hedera and the 0G uploader may run off-device** (the MPU has no Node).
8. **No battery-backed RTC.** The clock is set from the laptop at session start; the monotonic
   counter is the only trusted time source.
