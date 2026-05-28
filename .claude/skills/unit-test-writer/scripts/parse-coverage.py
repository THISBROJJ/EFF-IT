#!/usr/bin/env python3
"""
Normalizes coverage output from Jest, pytest-cov, go tool cover, and cargo
tarpaulin into a tab-separated table printed to stdout:

  FILE<TAB>LINE_PCT<TAB>BRANCH_PCT<TAB>FUNC_PCT

Usage:
  python scripts/parse-coverage.py [--format jest|pytest|go|tarpaulin] [file]
  <coverage command> | python scripts/parse-coverage.py

If --format is omitted, the format is auto-detected from content.
Exit 0: parsed successfully. Exit 1: unknown format or no data found.
"""

import argparse
import re
import sys
from pathlib import Path


def detect_format(text: str) -> str:
    if "% Stmts" in text or "% Branch" in text:
        return "jest"
    if re.search(r"Stmts\s+Miss\s+Cover", text):
        return "pytest"
    if re.search(r"\.go:\w+\s+[\d.]+%", text):
        return "go"
    if "|| Total coverage:" in text or re.search(r"\|\|\s+\S+\.rs\s+\|\|", text):
        return "tarpaulin"
    return "unknown"


def parse_jest(text: str) -> list[dict]:
    results = []
    pattern = re.compile(
        r"^\s*([^\|]{2,})\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)",
        re.MULTILINE,
    )
    skip = {"File", "All files", ""}
    for m in pattern.finditer(text):
        name = m.group(1).strip()
        if name in skip or name.startswith("-") or name.startswith("="):
            continue
        results.append({
            "file": name,
            "line_pct": float(m.group(5)),
            "branch_pct": float(m.group(3)),
            "func_pct": float(m.group(4)),
        })
    return results


def parse_pytest(text: str) -> list[dict]:
    results = []
    pattern = re.compile(r"^(\S+\.py)\s+\d+\s+\d+\s+(\d+)%", re.MULTILINE)
    branch_pattern = re.compile(
        r"^(\S+\.py)\s+\d+\s+\d+\s+\d+\s+\d+\s+(\d+)%", re.MULTILINE
    )
    branch_data = {m.group(1): float(m.group(2)) for m in branch_pattern.finditer(text)}
    for m in pattern.finditer(text):
        f = m.group(1)
        line_pct = float(m.group(2))
        results.append({
            "file": f,
            "line_pct": line_pct,
            "branch_pct": branch_data.get(f, line_pct),
            "func_pct": line_pct,
        })
    return results


def parse_go(text: str) -> list[dict]:
    file_pcts: dict[str, list[float]] = {}
    pattern = re.compile(r"^(\S+\.go):\S+\s+([\d.]+)%", re.MULTILINE)
    for m in pattern.finditer(text):
        file_pcts.setdefault(m.group(1), []).append(float(m.group(2)))
    return [
        {
            "file": f,
            "line_pct": sum(pcts) / len(pcts),
            "branch_pct": sum(pcts) / len(pcts),
            "func_pct": sum(pcts) / len(pcts),
        }
        for f, pcts in file_pcts.items()
    ]


def parse_tarpaulin(text: str) -> list[dict]:
    results = []
    pattern = re.compile(
        r"\|\|\s*(\S+\.rs)\s*\|\|\s*\d+/\d+\s*\|\|\s*([\d.]+)%", re.MULTILINE
    )
    for m in pattern.finditer(text):
        pct = float(m.group(2))
        results.append({"file": m.group(1), "line_pct": pct, "branch_pct": pct, "func_pct": pct})
    return results


PARSERS = {"jest": parse_jest, "pytest": parse_pytest, "go": parse_go, "tarpaulin": parse_tarpaulin}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", nargs="?", help="Coverage output file (default: stdin)")
    parser.add_argument("--format", choices=list(PARSERS))
    args = parser.parse_args()

    text = Path(args.file).read_text(encoding="utf-8") if args.file else sys.stdin.read()
    fmt = args.format or detect_format(text)

    if fmt not in PARSERS:
        print("ERROR: Could not detect coverage format. Use --format to specify.", file=sys.stderr)
        return 1

    rows = PARSERS[fmt](text)
    if not rows:
        print("ERROR: No per-file coverage data found in input.", file=sys.stderr)
        return 1

    print("FILE\tLINE_PCT\tBRANCH_PCT\tFUNC_PCT")
    for r in rows:
        print(f"{r['file']}\t{r['line_pct']:.1f}\t{r['branch_pct']:.1f}\t{r['func_pct']:.1f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
