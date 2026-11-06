#!/usr/bin/env python3
"""Catch Svelte expressions hidden inside <pre> blocks.

A literal like `GET /attestation/{container}` inside <pre> is compiled as a JS
expression, throws `container is not defined` at module load, and leaves the
whole page blank while the HTTP status is still 200. This is a build-time
invariant, so it runs here rather than in the browser.

Run:  python3 tools/check_braces.py
Exit: 0 clean, 1 findings (including the planted control failing to be caught)
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "site/src"


def shipped() -> list[Path]:
    """Components reachable from App.svelte; dead files cannot fail the check."""
    seen: set[Path] = set()
    stack = [SRC / "App.svelte"]
    out: list[Path] = []
    while stack:
        p = stack.pop().resolve()
        if p in seen or not p.exists():
            continue
        seen.add(p)
        out.append(p)
        for m in re.finditer(r'import\s+\w+\s+from\s+"(\.[^"]+)"', p.read_text()):
            q = (p.parent / m.group(1)).resolve()
            stack.append(q.with_suffix(".svelte") if q.suffix == "" else q)
    return out


DECL = re.compile(r"(?:const|let|var|function|class)\s+([A-Za-z_$][\w$]*)")


def declared(src: str) -> set[str]:
    names = set(DECL.findall(src))
    for m in re.finditer(r"import\s+([\s\S]*?)\s+from\s+[\"']", src):
        chunk = m.group(1)
        chunk = chunk.replace("{", " ").replace("}", " ").replace("*", " ")
        for part in chunk.split(","):
            part = part.strip().split(" as ")[-1].strip()
            if re.fullmatch(r"[A-Za-z_$][\w$]*", part):
                names.add(part)
    return names


def findings(files: list[Path]) -> list[str]:
    """Only undeclared identifiers break the page; declared ones render a value."""
    bad: list[str] = []
    for f in files:
        src = f.read_text()
        known = declared(src)
        for block in re.findall(r"<pre>.*?</pre>", src, re.S):
            for expr in re.findall(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}", block):
                if expr not in known:
                    bad.append(f"{f.name}: {{{expr}}}")
    return bad


def main() -> int:
    real = findings(shipped())
    for f in real:
        print(f"  FAIL  bare expression in a code block: {f}")

    # Control: plant a brace in a copy of a real component and require a hit.
    sample = (SRC / "components/Docs.svelte").read_text().replace(
        "</code></pre>", "GET /x/{oops}</code></pre>", 1
    )
    tmp = SRC / "components/_brace_control.svelte"
    tmp.write_text(sample)
    try:
        caught = bool(findings([tmp]))
    finally:
        tmp.unlink(missing_ok=True)

    print(f"  {'PASS' if caught else 'FAIL'}  control: planted {{{{oops}}}} {'caught' if caught else 'MISSED'}")
    if not caught:
        print("the detector is blind; do not trust the clean result")
        return 1
    if real:
        return 1
    print("  PASS  no bare expressions inside <pre> blocks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
