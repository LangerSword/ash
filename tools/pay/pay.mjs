// Pay an Ash x402 endpoint on Hedera testnet, end to end.
// Usage: node pay.mjs https://api.langersword.in/attestation/C-001
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const envFile = path.resolve(__dirname, "../../.env");
const env = {};
for (const line of fs.readFileSync(envFile, "utf8").split("\n")) {
  if (line.includes("=") && !line.trim().startsWith("#")) {
    const i = line.indexOf("=");
    env[line.slice(0, i).trim()] = line.slice(i + 1).trim();
  }
}

const { x402Client, x402HTTPClient } = await import("@x402/core/client");
const { createClientHederaSigner, ExactHederaScheme } = await import("@x402/hedera");
const { PrivateKey } = await import("@hiero-ledger/sdk");

const account = env.HEDERA_ACCOUNT_ID;
const key = env.HEDERA_PRIVATE_KEY;
const url = process.argv[2];
if (!account || !key || !url) {
  console.error("need HEDERA_ACCOUNT_ID, HEDERA_PRIVATE_KEY and a URL");
  process.exit(1);
}

const signer = createClientHederaSigner(account, PrivateKey.fromString(key), {
  network: "hedera:testnet",
});
const client = new x402Client().register("hedera:*", new ExactHederaScheme(signer));
client.setSpendControls(false);
const http = new x402HTTPClient(client);

const first = await fetch(url);
console.log("first status", first.status);
if (first.status !== 402) {
  console.log(await first.text());
  process.exit(0);
}
const body = await first.json();
const accepts = body.accepts ?? [];
console.log("accepts", accepts.length, accepts[0]?.scheme, accepts[0]?.network);

const payload = await client.createPaymentPayload(body);
console.log("payload keys", Object.keys(payload));
const header = Buffer.from(JSON.stringify(payload)).toString("base64");
console.log("accepted", JSON.stringify(payload.accepted));
console.log("payload.payload keys", Object.keys(payload.payload || {}));
console.log("header len", header.length);

const paid = await fetch(url, { headers: { "X-PAYMENT": header } });
console.log("paid status", paid.status);
console.log(await paid.text());
