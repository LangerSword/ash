import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const envFile = path.resolve(__dirname, "../../.env");
const env = {};
for (const line of fs.readFileSync(envFile, "utf8").split("\n")) {
  if (line.includes("=") && !line.trim().startsWith("#")) { const i = line.indexOf("="); env[line.slice(0, i).trim()] = line.slice(i + 1).trim(); }
}
const { Client, AccountCreateTransaction, Hbar, PrivateKey } = await import("@hiero-ledger/sdk");
const client = Client.forTestnet();
client.setOperator(env.HEDERA_ACCOUNT_ID, PrivateKey.fromString(env.HEDERA_PRIVATE_KEY));
const key = PrivateKey.generateECDSA();
const tx = await new AccountCreateTransaction()
  .setKey(key.publicKey)
  .setInitialBalance(new Hbar(5))
  .setAccountMemo("ash vendor payout")
  .execute(client);
const receipt = await tx.getReceipt(client);
console.log("VENDOR_ID=" + receipt.accountId.toString());
console.log("VENDOR_KEY=" + key.toStringDer());
client.close();
