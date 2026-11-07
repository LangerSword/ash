/**
 * State art for the 13x8 matrix, in the same shape the board accepts.
 *
 * One source of truth: the app renders these frames and pushes the same frames to
 * the board when the state changes, so a sponsor sees the same picture in the
 * window and on the desk.
 *
 * Each frame is 104 chars of 0/1, row-major (row 0 is the top row).
 */
export type BoardState = "sealed" | "deciding" | "destroyed" | "open" | "offline";

const W = 13;
const H = 8;

const blank = (): boolean[] => new Array<boolean>(W * H).fill(false);
const put = (g: boolean[], r: number, c: number) => {
  if (r >= 0 && r < H && c >= 0 && c < W) g[r * W + c] = true;
};
const bits = (g: boolean[]): string => g.map((v) => (v ? "1" : "0")).join("");

/** the seal breathing: a band that fills and empties, 12 frames over 3 s */
function sealed(): string[] {
  const frames: string[] = [];
  for (let i = 0; i < 12; i += 1) {
    const level = Math.round(3.5 * (1 + Math.sin((i / 12) * Math.PI * 2)));
    const g = blank();
    for (let r = H - Math.max(1, level); r < H; r += 1) {
      for (let c = 0; c < W; c += 1) put(g, r, c);
    }
    frames.push(bits(g));
  }
  return frames;
}

/** the deadline draining right to left, 13 frames */
function deciding(): string[] {
  const frames: string[] = [];
  for (let i = 0; i < 13; i += 1) {
    const g = blank();
    for (let c = i; c < W; c += 1) {
      for (let r = 0; r < H; r += 1) put(g, r, c);
    }
    frames.push(bits(g));
  }
  return frames;
}

/** the X, struck once then blinking */
function destroyed(): string[] {
  const out: string[] = [];
  for (const scale of [0.5, 0.75, 1, 1, 1]) {
    const g = blank();
    for (let i = 0; i < 8; i += 1) {
      const reach = Math.round(i * scale);
      put(g, reach, reach);
      put(g, reach, 12 - reach);
    }
    out.push(bits(g));
  }
  return out;
}

/** the diamond, opening */
function open(): string[] {
  const out: string[] = [];
  for (const radius of [1.2, 2.2, 3.2, 3.2]) {
    const g = blank();
    for (let r = 0; r < H; r += 1) {
      for (let c = 0; c < W; c += 1) {
        if (Math.abs(r - 3.5) + Math.abs(c - 6) < radius) put(g, r, c);
      }
    }
    out.push(bits(g));
  }
  return out;
}

export const STATE_ART: Record<BoardState, { fps: number; frames: string[]; loop: boolean }> = {
  sealed: { fps: 8, frames: sealed(), loop: true },
  deciding: { fps: 12, frames: deciding(), loop: false },
  destroyed: { fps: 5, frames: destroyed(), loop: true },
  open: { fps: 6, frames: open(), loop: true },
  offline: { fps: 1, frames: [bits(blank())], loop: true },
};

/** app mode -> board state */
export function boardState(mode: string): BoardState {
  switch (mode) {
    case "armed":
      return "sealed";
    case "amber":
      return "deciding";
    case "tampered":
    case "wipe":
      return "destroyed";
    case "unsealed":
      return "open";
    default:
      return "offline";
  }
}
