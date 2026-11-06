// A minimal x402 (exact, Hedera) facilitator we run ourselves.
// It verifies the transfer semantics, adds the fee payer's signature, executes,
// and returns the transaction id. The fee payer is our own testnet account.
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const env = {};
for (const line of fs.readFileSync(path.resolve(__dirname, "../../.env"), "utf8").split("\n")) {
  if (line.includes("=") && !line.trim().startsWith("#")) {
    const i = line.indexOf("=");
    env[line.slice(0, i).trim()] = line.slice(i + 1).trim();
  }
}

const { Client, PrivateKey, Transaction, AccountId } = await import("@hiero-ledger/sdk");
const key = PrivateKey.fromString(env.HEDERA_PRIVATE_KEY);
const feePayer = env.HEDERA_FEE_PAYER || env.HEDERA_ACCOUNT_ID;
const payTo = env.HEDERA_PAY_TO;
const amount = BigInt(env.HEDERA_AMOUNT || "10000000");
const client = Client.forTestnet().setOperator(env.HEDERA_ACCOUNT_ID, key);

const body = (req) =>
  new Promise((resolve, reject) => {
    let b = "";
    req.on("data", (c) => (b += c));
    req.on("end", () => {
      try {
        resolve(JSON.parse(b || "{}"));
      } catch (e) {
        reject(e);
      }
    });
  });

function entriesOf(raw) {
  if (!raw) return [];
  if (Array.isArray(raw)) return raw;
  if (raw instanceof Map) return [...raw.entries()];
  // Hedera's SDK wraps these in an internal transfer map: {_map: Map, __map}
  if (raw._map instanceof Map) return [...raw._map.entries()];
  if (raw.__map instanceof Map) return [...raw.__map.entries()];
  return Object.entries(raw).filter(([k]) => !k.startsWith("_"));
}

function tiny(v) {
  if (v && typeof v === "object") {
    if ("_valueInTinybar" in v) return BigInt(v._valueInTinybar);
    if (typeof v.toTinybars === "function") return BigInt(v.toTinybars().toString());
  }
  if (typeof v === "bigint") return v;
  return BigInt(String(v));
}

function inspect(payload) {
  const tx = Transaction.fromBytes(Buffer.from(payload.transaction, "base64"));
  const txPayer = tx.transactionId?.accountId?.toString();
  const transfers = entriesOf(tx.hbarTransfers).map(([k, v]) => [String(k), tiny(v)]);
  return { tx, txPayer, transfers };
}

const server = http.createServer(async (req, res) => {
  const send = (code, obj) => {
    res.writeHead(code, { "Content-Type": "application/json" });
    res.end(JSON.stringify(obj));
  };
  if (req.method === "GET" && req.url === "/supported") {
    return send(200, { kinds: [{ scheme: "exact", network: "hedera:testnet" }] });
  }
  if (req.method !== "POST") return send(405, { error: "method" });
  let b;
  try {
    b = await body(req);
  } catch {
    return send(400, { isValid: false, invalidReason: "bad_json" });
  }
  const payload = b.paymentPayload?.payload ?? b.paymentPayload;
  const reqs = b.paymentRequirements ?? b.accepts?.[0] ?? {};
  if (!payload?.transaction) return send(400, { isValid: false, invalidReason: "missing_transaction" });

  let ins;
  try {
    const dbgTx = Transaction.fromBytes(Buffer.from(payload.transaction, "base64"));
    const raw = dbgTx.hbarTransfers;
    fs.writeFileSync(
      "/tmp/hbar_shape.json",
      JSON.stringify({
        ctor: raw?.constructor?.name,
        isArray: Array.isArray(raw),
        isMap: raw instanceof Map,
        keys: raw && typeof raw === "object" ? Object.keys(raw).slice(0, 5) : [],
        sample: raw && typeof raw === "object" ? Object.entries(raw).slice(0, 2) : String(raw),
      }, null, 1),
    );
    ins = inspect(payload);
  } catch (e) {
    return send(400, { isValid: false, invalidReason: "undecodable_transaction", invalidMessage: String(e) });
  }

  const toPayTo = ins.transfers.filter(([a]) => a === payTo).reduce((s, [, v]) => s + v, 0n);
  const sum = ins.transfers.reduce((s, [, v]) => s + v, 0n);
  const valid =
    ins.txPayer === feePayer &&
    toPayTo === amount &&
    sum === 0n &&
    String(reqs.payTo ?? payTo) === payTo;

  if (req.url === "/verify") {
    return send(200, {
      isValid: valid,
      payer: ins.txPayer ?? "",
      invalidReason: valid ? undefined : ins.txPayer !== feePayer ? "fee_payer_mismatch" : "amount_mismatch",
    });
  }

  if (req.url === "/settle") {
    if (!valid) return send(400, { isValid: false, invalidReason: "invalid_payload" });
    try {
      ins.tx.sign(key);
      const sent = await ins.tx.execute(client);
      const receipt = await sent.getReceipt(client);
      const txId = sent.transactionId.toString();
      console.log("settled", txId, receipt.status.toString());
      return send(200, { success: true, transaction: txId, network: "hedera:testnet", status: receipt.status.toString() });
    } catch (e) {
      console.error("settle failed", String(e));
      return send(400, { isValid: false, invalidReason: "settle_failed", invalidMessage: String(e).slice(0, 300) });
    }
  }

  return send(404, { error: "not found" });
});

server.listen(7090, "127.0.0.1", () => console.log("facilitator on 127.0.0.1:7090 feePayer", feePayer, "payTo", payTo));
