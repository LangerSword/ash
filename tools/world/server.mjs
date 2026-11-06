// Ash World helper: serves the unseal page, signs IDKit requests, renders QR codes.
// The signing key never leaves this process; the page only receives a signature.
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { signRequest } from "@worldcoin/idkit-core/signing";
import QRCode from "qrcode";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "../..");
const PORT = Number(process.env.WORLD_PORT || 7070);

const env = {};
const envFile = path.join(ROOT, ".env");
if (fs.existsSync(envFile)) {
  for (const line of fs.readFileSync(envFile, "utf8").split("\n")) {
    if (line.includes("=") && !line.trim().startsWith("#")) {
      const i = line.indexOf("=");
      env[line.slice(0, i).trim()] = line.slice(i + 1).trim();
    }
  }
}
const APP_ID = process.env.WORLD_APP_ID || env.WORLD_APP_ID || "";
const RP_ID = process.env.WORLD_RP_ID || env.WORLD_RP_ID || "";
const ACTION = process.env.WORLD_ACTION || env.WORLD_ACTION || "unseal";
const SIGNING_KEY = process.env.WORLD_RP_SIGNING_KEY || env.WORLD_RP_SIGNING_KEY || "";

function json(res, code, body) {
  const data = JSON.stringify(body);
  res.writeHead(code, {
    "Content-Type": "application/json",
    "Content-Length": Buffer.byteLength(data),
    "Access-Control-Allow-Origin": "*",
  });
  res.end(data);
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://localhost:${PORT}`);

  if (req.method === "GET" && url.pathname === "/") {
    const page = path.join(__dirname, "public", "index.html");
    const body = fs.readFileSync(page);
    res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
    return res.end(body);
  }

  if (req.method === "GET" && url.pathname === "/idkit.global.js") {
    const lib = path.join(__dirname, "node_modules/@worldcoin/idkit-core/dist/idkit.global.js");
    const body = fs.readFileSync(lib);
    res.writeHead(200, { "Content-Type": "application/javascript" });
    return res.end(body);
  }

  if (req.method === "GET" && url.pathname === "/api/config") {
    return json(res, 200, { app_id: APP_ID, rp_id: RP_ID, action: ACTION, has_key: Boolean(SIGNING_KEY) });
  }

  if (req.method === "POST" && url.pathname === "/api/rp-signature") {
    try {
      const out = signRequest({ signingKeyHex: SIGNING_KEY, action: ACTION });
      return json(res, 200, {
        sig: out.sig,
        nonce: out.nonce,
        created_at: out.createdAt,
        expires_at: out.expiresAt,
      });
    } catch (e) {
      return json(res, 500, { error: `${e.name}: ${e.message}` });
    }
  }

  if (req.method === "GET" && url.pathname === "/api/qr") {
    const data = url.searchParams.get("data") || "";
    try {
      const svg = await QRCode.toString(data, { type: "svg", margin: 1, width: 260 });
      res.writeHead(200, { "Content-Type": "image/svg+xml" });
      return res.end(svg);
    } catch (e) {
      return json(res, 400, { error: e.message });
    }
  }

  json(res, 404, { error: "not_found" });
});

server.listen(PORT, "127.0.0.1", () => {
  console.log(`world helper on http://127.0.0.1:${PORT} app=${APP_ID} rp=${RP_ID} action=${ACTION} key=${SIGNING_KEY ? SIGNING_KEY.length + " chars" : "MISSING"}`);
});
