import { ApiError } from "./api";
import type { X402Challenge } from "./types";

export type Failure = {
  cause: string;
  action: string;
  detail?: string;
};

const f = (cause: string, action: string, detail?: string): Failure => ({ cause, action, detail });

export function explain(e: unknown, logPath = "~/.local/state/ash/app.log"): Failure {
  if (e instanceof ApiError && e.status === 402) {
    const c = e.body as X402Challenge | null;
    const a = c?.accepts?.[0];
    if (a?.amount) {
      const amount = Number(a.amount) / 1e6;
      return f(
        `Payment required: ${amount} ${a.asset ?? "USDC"} to ${a.payTo ?? "the payee"} on ${a.network ?? "hedera"}.`,
        "The app does not pay automatically. Settle it with the agent key, then read the attestation again.",
        e.message,
      );
    }
    return f(
      "This attestation is unpaid (x402).",
      "Read the price and payee from the challenge; the app never auto-pays.",
      e.message,
    );
  }

  const msg = e instanceof Error ? e.message : String(e);

  if (/hedera_not_configured/i.test(msg)) {
    return f(
      "Hedera is not configured on the local service.",
      "Set HEDERA_PAY_TO and X402_FACILITATOR in the service environment, then retry.",
      msg,
    );
  }
  if (/ERR:not_armed|key_destroyed|key destroyed/i.test(msg)) {
    return f(
      "The MASTER key is gone: a tamper event destroyed it.",
      "Reprovision the board to run the seal again. This is a dev build.",
      msg,
    );
  }
  if (/WorldError|world:/i.test(msg)) {
    return f(
      "No World proof was accepted, so nothing was released.",
      "Scan a fresh proof with World ID, or cancel the release.",
      msg,
    );
  }
  if (/0g/i.test(msg) && /deny|denied|refus/i.test(msg)) {
    return f(
      "0G refused the release.",
      "Read the request id in the ledger; the model's reason is shown verbatim.",
      msg,
    );
  }
  if (/no seal for container|no seal/i.test(msg)) {
    return f(
      "There is no sealed container with that id.",
      "Seal it first, then unseal.",
      msg,
    );
  }
  if (/0g_timeout|deadline|UNAVAILABLE/i.test(msg)) {
    return f(
      "0G did not answer before the deadline; the seal fails closed.",
      "Re-arm the board to continue. Silence is not consent.",
      msg,
    );
  }
  if (/timed out|AbortError/i.test(msg)) {
    return f(
      "The local service did not answer in time.",
      "Check the board link, then retry.",
      msg,
    );
  }
  if (/Failed to fetch|network error|ECONNREFUSED/i.test(msg)) {
    return f(
      "The local service is unreachable.",
      "Start it, or reconnect the board, then retry.",
      msg,
    );
  }
  if (/No space left|ENOSPC/i.test(msg)) {
    return f(
      "The disk is full, so the payload could not be written.",
      "Free space on the volume holding ~/.local/share/ash, then retry.",
      msg,
    );
  }
  if (/Permission denied|EACCES|EPERM/i.test(msg)) {
    return f(
      "Permission denied while writing the sealed payload.",
      "Check ownership of the payload path, then retry.",
      msg,
    );
  }
  if (/Cannot connect to the board|board app|not answering/i.test(msg)) {
    return f(
      "The board's app is not answering on its forwarded port.",
      "Use Start board app, or restart the app on the board.",
      msg,
    );
  }
  return f(msg || "The action failed.", `See ${logPath} for the full trace, then retry.`);
}

export function deviceHint(state: string, detail: string): { line: string; action: string } {
  switch (state) {
    case "ready":
      return { line: "", action: "" };
    case "absent":
      return {
        line: "No UNO Q on USB. The ledger is still readable; sealing is disabled.",
        action: "Connect the board over USB.",
      };
    case "unauthorized":
      return {
        line: "The board is connected but USB debugging is not authorised.",
        action: "On the UNO Q, allow USB debugging for this computer.",
      };
    case "forwarded":
      return {
        line: "The board is connected, but its app is not answering yet.",
        action: "Start the board app below, or wait for the boot to finish.",
      };
    case "error":
      return {
        line: detail || "adb failed to reach the board.",
        action: "Replug the board, then retry.",
      };
    case "external":
      return {
        line: "The device link is owned by another process.",
        action: "Close the other Ash service, or use its API.",
      };
    default:
      return { line: "Detecting the board over USB…", action: "" };
  }
}
