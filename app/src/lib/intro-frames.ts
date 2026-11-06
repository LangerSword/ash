/**
 * The intro, expressed as 13x8 frames for the board's LED matrix.
 * Same beats as the in-app timeline: draw, lid, burn, falling ash, the wordmark.
 * Every frame is 104 chars of 0/1, row-major (row 0 is the top row).
 */
export const INTRO_FPS = 12;

const W = 13;
const H = 8;

type Grid = boolean[];

const blank = (): Grid => new Array<boolean>(W * H).fill(false);

const put = (g: Grid, r: number, c: number) => {
  if (r >= 0 && r < H && c >= 0 && c < W) g[r * W + c] = true;
};

const rectPerimeter = (r0: number, c0: number, r1: number, c1: number): Array<[number, number]> => {
  const out: Array<[number, number]> = [];
  for (let c = c0; c <= c1; c += 1) out.push([r0, c]);
  for (let r = r0 + 1; r <= r1; r += 1) out.push([r, c1]);
  for (let c = c1 - 1; c >= c0; c -= 1) out.push([r1, c]);
  for (let r = r1 - 1; r > r0; r -= 1) out.push([r, c0]);
  return out;
};

const toBits = (g: Grid): string => g.map((v) => (v ? "1" : "0")).join("");

// deterministic noise so the frames are stable between builds
let seed = 0x9e3779b9;
const rnd = () => {
  seed ^= seed << 13;
  seed ^= seed >>> 17;
  seed ^= seed << 5;
  return ((seed >>> 0) % 1000) / 1000;
};

const WORD_ASH: Record<string, string[]> = {
  A: [".#.", "#.#", "###", "#.#", "#.#"],
  S: [".##", "#..", ".#.", "..#", "##."],
  H: ["#.#", "#.#", "###", "#.#", "#.#"],
};

function wordmark(partial: number): Grid {
  const g = blank();
  const letters = ["A", "S", "H"];
  const cells: Array<[number, number]> = [];
  letters.forEach((ch, li) => {
    const rows = WORD_ASH[ch];
    const c0 = 2 + li * 4;
    rows.forEach((row, r) => {
      for (let c = 0; c < 3; c += 1) {
        if (row[c] === "#") cells.push([2 + r, c0 + c]);
      }
    });
  });
  const n = Math.floor(cells.length * partial);
  for (let i = 0; i < n; i += 1) put(g, cells[i][0], cells[i][1]);
  return g;
}

export function buildIntroFrames(): string[] {
  const frames: string[] = [];
  const per = rectPerimeter(2, 2, 5, 10);

  // 0-5: the box draws itself
  for (let i = 0; i < 6; i += 1) {
    const g = blank();
    const n = Math.min(per.length, 4 + i * 5);
    for (let k = 0; k < n; k += 1) put(g, per[k][0], per[k][1]);
    frames.push(toBits(g));
  }

  // 6-9: the lid lifts away from the top edge
  for (let i = 1; i <= 4; i += 1) {
    const g = blank();
    for (let k = 4 + i * 5; k < per.length; k += 1) put(g, per[k][0], per[k][1]);
    for (let k = 0; k < i; k += 1) {
      put(g, 1 - Math.min(1, Math.floor(k / 2)), 2 + k * 2);
      put(g, 0, 3 + k * 2);
    }
    frames.push(toBits(g));
  }

  // 10-24: the burn front eats the box from the top-left corner
  for (let i = 0; i < 15; i += 1) {
    const g = blank();
    const front = (i + 1) * 1.4;
    for (const [r, c] of per) {
      const d = (c - 2) * 0.85 + (r - 2) * 1.9;
      if (d > front) put(g, r, c);
      else if (rnd() > 0.55) put(g, r, c);
    }
    // embers drop from the front
    for (let k = 0; k < 3; k += 1) {
      const c = Math.min(W - 1, 2 + Math.floor(front) + Math.floor(rnd() * 3));
      put(g, 5 + Math.floor(rnd() * 2), c);
    }
    frames.push(toBits(g));
  }

  // 25-35: residue falls
  const ash: Array<{ r: number; c: number }> = [];
  for (let i = 0; i < 9; i += 1) ash.push({ r: 3 + Math.floor(rnd() * 3), c: 2 + Math.floor(rnd() * 9) });
  for (let i = 0; i < 11; i += 1) {
    const g = blank();
    for (const [idx, p] of ash.entries()) {
      const fall = Math.min(2, Math.floor((i - idx * 0.4) / 3));
      put(g, p.r + fall, p.c);
    }
    frames.push(toBits(g));
  }

  // 36-42: the wordmark settles
  for (let i = 0; i < 7; i += 1) frames.push(toBits(wordmark((i + 1) / 7)));

  return frames;
}
