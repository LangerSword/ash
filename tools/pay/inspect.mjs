import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const env = {};
for (const line of fs.readFileSync(path.resolve(__dirname, "../../.env"), "utf8").split("\n")) {
  if (line.includes("=") && !line.trim().startsWith("#")) { const i = line.indexOf("="); env[line.slice(0, i).trim()] = line.slice(i + 1).trim(); }
}
const { x402Client } = await import("@x402/core/client");
const { createClientHederaSigner, ExactHederaScheme } = await import("@x402/hedera");
const { PrivateKey, Transaction } = await import("@hiero-ledger/sdk");

const url = "http://127.0.0.1:8080/attestation/C-001";
const first = await fetch(url);
const body = await first.json();
const signer = createClientHederaSigner(env.HEDERA_ACCOUNT_ID, PrivateKey.fromString(env.HEDERA_PRIVATE_KEY), { network: "hedera:testnet" });
const client = new x402Client().register("hedera:*", new ExactHederaScheme(signer));
client.setSpendControls(false);
const payload = await client.createPaymentPayload(body);
const tx = Transaction.fromBytes(Buffer.from(payload.payload.transaction, "base64"));
console.log("requirements", JSON.stringify(body.accepts[0]));
console.log("tx type", tx.constructor.name, "txid", tx.transactionId?.toString());
console.log("hbar", JSON.stringify(tx.hbarTransfers, (k, v) => (typeof v === "bigint" ? v.toString() : v)));
console.log("tokens", JSON.stringify(tx.tokenTransfers, (k, v) => (typeof v === "bigint" ? v.toString() : v)));
console.log("payer account", env.HEDERA_ACCOUNT_ID, "fee payer", body.accepts[0].extra.feePayer);
