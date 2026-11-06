// Create an IDKit request against our RP, print the connector URL, poll for the proof.
// Usage: node make_request.mjs
import fs from "node:fs";

const cfg = Object.fromEntries(
  fs
    .readFileSync(new URL("../../.env", import.meta.url), "utf8")
    .split("\n")
    .filter((l) => l.includes("=") && !l.trim().startsWith("#"))
    .map((l) => {
      const i = l.indexOf("=");
      return [l.slice(0, i).trim(), l.slice(i + 1).trim()];
    }),
);

const container = process.env.ASH_CONTAINER || "W-1";

// A seal with an owner, so the 0G release decision has something to release.
const sealed = await fetch("http://127.0.0.1:8080/seal", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ container, owner: "human-001" }),
}).then((r) => r.json());
console.log("SEALED", container, sealed?.record?.hash?.slice(0, 12) ?? sealed);

const sig = await fetch("http://127.0.0.1:8080/world/rp-signature", { method: "POST" }).then((r) =>
  r.json(),
);

const { IDKit, proofOfHuman } = await import("@worldcoin/idkit-core");

const request = await IDKit.request({
  app_id: cfg.WORLD_APP_ID,
  action: cfg.WORLD_ACTION,
  allow_legacy_proofs: true,
  environment: "production",
  rp_context: {
    rp_id: cfg.WORLD_RP_ID,
    nonce: sig.nonce,
    signature: sig.sig,
    created_at: sig.created_at,
    expires_at: sig.expires_at,
  },
}).preset(proofOfHuman());

const uri = request.connectorURL ?? request._connectorURI ?? "";
fs.writeFileSync("/tmp/connector.txt", uri);
console.log("CONNECTOR", uri);

try {
  const result = await request.pollUntilCompletion({ timeout: 240000 });
  fs.writeFileSync("/tmp/proof.json", JSON.stringify(result, null, 2));
  console.log("PROOF_OK", JSON.stringify(result).slice(0, 200));
  const unseal = await fetch("http://127.0.0.1:8080/unseal", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ container, proof: result }),
  });
  const body = await unseal.text();
  console.log("UNSEAL", unseal.status, body.slice(0, 300));
} catch (e) {
  fs.writeFileSync("/tmp/proof_error.txt", String(e));
  console.log("PROOF_ERR", String(e).slice(0, 200));
}
