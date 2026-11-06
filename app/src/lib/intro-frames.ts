/**
 * The Ash signature, on 13x8.
 *
 * Same choreography as the website hero (site/src/components/HeroBurn.svelte):
 * the wordmark takes ink, holds, then a burn front crosses it left to right,
 * embers fall, and the word reforms out of the ash. 104 bits per frame,
 * row-major, MSB first.
 */
export const SIGNATURE_FPS = 14;

const W = 13;
const H = 8;

type Grid = boolean[];

const blank = (): Grid => new Array<boolean>(W * H).fill(false);

const put = (g: Grid, r: number, c: number) => {
  if (r >= 0 && r < H && c >= 0 && c < W) g[r * W + c] = true;
};

const toBits = (g: Grid): string => g.map((v) => (v ? "1" : "0")).join("");

// 3-wide lowercase glyphs, 5 rows: A with a flat apex (reads at this size), s, h.
const GLYPHS: Record<string, string[]> = {
  A: [".#.", "#.#", "###", "#.#", "#.#"],
  s: [".##", "#..", ".#.", "..#", "##."],
  h: ["#..", "#..", "##.", "#.#", "#.#"],
};

const WORD = "Ash";
const WORD_COLS = 11; // 3 + 1 + 3 + 1 + 3

function glyphCells(): Array<[number, number]> {
  const cells: Array<[number, number]> = [];
  let col = Math.floor((W - WORD_COLS) / 2);
  for (const ch of WORD) {
    const rows = GLYPHS[ch];
    rows.forEach((row, r) => {
      for (let c = 0; c < 3; c += 1) {
        if (row[c] === "#") cells.push([2 + r, col + c]);
      }
    });
    col += 4;
  }
  return cells.sort((a, b) => a[1] - b[1] || a[0] - b[0]);
}

// deterministic, so a build always plays the same film
let seed = 0x51ed270b;
const rnd = () => {
  seed ^= seed << 13;
  seed ^= seed >>> 17;
  seed ^= seed << 5;
  return ((seed >>> 0) % 10000) / 10000;
};

const full = (cells: Array<[number, number]>): Grid => {
  const g = blank();
  for (const [r, c] of cells) put(g, r, c);
  return g;
};

export function buildSignatureFrames(): string[] {
  const cells = glyphCells();
  const frames: string[] = [];

  // 1. ink arrives, left column to right
  for (let step = 0; step <= 6; step += 1) {
    const g = blank();
    const limit = Math.ceil((cells.length * (step + 1)) / 7);
    for (let i = 0; i < limit; i += 1) put(g, cells[i][0], cells[i][1]);
    frames.push(toBits(g));
  }

  // 2. hold, fully inked
  frames.push(toBits(full(cells)));
  frames.push(toBits(full(cells)));

  // 3. burn front crosses the word; cells behind it are eaten, embers drop
  const burnFrames = 20;
  for (let i = 0; i < burnFrames; i += 1) {
    const front = 1 + (i / (burnFrames - 1)) * (W - 1);
    const g = blank();
    for (const [r, c] of cells) {
      if (c > front + (rnd() - 0.5) * 1.2) put(g, r, c);
    }
    const fc = Math.min(W - 1, Math.max(0, Math.round(front)));
    for (let e = 0; e < 2; e += 1) {
      if (rnd() > 0.35) put(g, 5 + Math.floor(rnd() * 3), Math.max(0, fc - (rnd() > 0.5 ? 0 : 1)));
    }
    frames.push(toBits(g));
  }

  // 4. ash falling, the word is gone
  for (let i = 0; i < 3; i += 1) {
    const g = blank();
    for (let e = 0; e < 3; e += 1) put(g, 5 + Math.floor(rnd() * 3), Math.floor(rnd() * W));
    frames.push(toBits(g));
  }

  // 5. the word reforms out of the ash, right to left
  for (let step = 0; step <= 5; step += 1) {
    const g = blank();
    const keep = Math.ceil((cells.length * (step + 1)) / 6);
    for (let i = cells.length - keep; i < cells.length; i += 1) {
      const cell = cells[i];
      if (cell) put(g, cell[0], cell[1]);
    }
    frames.push(toBits(g));
  }

  // 6. settle on the full word
  frames.push(toBits(full(cells)));
  frames.push(toBits(full(cells)));

  return frames;
}

// Back-compat names used by the intro and the first-run screen.
export const INTRO_FPS = SIGNATURE_FPS;
export const buildIntroFrames = buildSignatureFrames;
