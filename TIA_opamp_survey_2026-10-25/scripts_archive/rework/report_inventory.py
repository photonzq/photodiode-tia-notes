"""Inventory of the survey report's blocks, used to plan the narrative rework of 27 Oct 2026.

For every section block (a '##' or '###' heading up to the next one) it prints the line range, the
tables, equation tags and figures it holds, and the first and last prose paragraphs (shortened),
so that each block can be placed in the new order without reading the whole report at once.

Usage: python report_inventory.py <report.md> [--full <first line> <last line>]
"""
import re
import sys

TABLE_CAPTION = re.compile(r"^\*Table ([^ ]+?)\.? ")
TAG = re.compile(r"\\tag\{([^}]+)\}")
FIGURE = re.compile(r"^!\[(Figure \d+)\]", re.M)
NOT_PROSE = re.compile(r"^\s*[-+=_^{}()\\|$!#]")


def blocks(lines):
    heads = [i for i, l in enumerate(lines) if re.match(r"^#{2,3} ", l)] + [len(lines)]
    return list(zip(heads[:-1], heads[1:]))


def main():
    path = sys.argv[1]
    lines = open(path, encoding="utf-8").read().split("\n")
    if "--full" in sys.argv:
        a, b = int(sys.argv[-2]), int(sys.argv[-1])
        print("\n".join(lines[a - 1:b]))
        return
    for a, b in blocks(lines):
        blk = lines[a:b]
        text = "\n".join(blk)
        tabs = [TABLE_CAPTION.match(l).group(1) for l in blk if TABLE_CAPTION.match(l)]
        paras = [l for l in blk[1:] if l.strip() and not l.startswith("*Table") and not NOT_PROSE.match(l)]
        first = paras[0][:260] if paras else ""
        last = paras[-1][-200:] if paras else ""
        print(f"L{a + 1}-{b} ({b - a} lines) {lines[a]}")
        print(f"   tables {tabs} eqs {TAG.findall(text)} figs {FIGURE.findall(text)}")
        print(f"   FIRST: {first}")
        print(f"   LAST:  ...{last}")


if __name__ == "__main__":
    main()
