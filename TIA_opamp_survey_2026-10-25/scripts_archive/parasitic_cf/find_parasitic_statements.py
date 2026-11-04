"""Locate the pages of local PDFs that state a parasitic or feedback capacitance of a resistor,
its pads or a layout, so that those pages can be rendered and read in full.

Usage: python find_parasitic_statements.py <pdf or folder> [...]

Text extraction is used only to find pages (it loses figures and can split numbers); every
value quoted in the note is read from the rendered page.  For each PDF it prints the page
numbers (1-based, as a PDF viewer counts them) and a short context around each hit.
"""
import re
import sys
from pathlib import Path

import pymupdf

PATTERN = re.compile(
    r"(parasitic|stray|feedback|shunt|pad|layout|guard|shield)[^.]{0,120}?\b\d+(?:\.\d+)?\s?(pF|fF)"
    r"|\b\d+(?:\.\d+)?\s?(pF|fF)[^.]{0,120}?(parasitic|stray|feedback resistor|pad|0201|0402|0603|0805|1206)",
    re.I | re.S)
SIZES = re.compile(r"\b(0201|0402|0603|0805|1206)\b")


def scan(pdf):
    doc = pymupdf.open(pdf)
    hits = []
    for i, page in enumerate(doc):
        text = " ".join(page.get_text().split())
        for m in PATTERN.finditer(text):
            ctx = text[max(0, m.start() - 80):m.end() + 80]
            if re.search(r"resist|R_?F|feedback|pad|layout|parasitic|stray", ctx, re.I):
                hits.append((i + 1, ctx))
        if SIZES.search(text) and re.search(r"parasitic|capacit", text, re.I):
            for m in SIZES.finditer(text):
                ctx = text[max(0, m.start() - 100):m.end() + 100]
                if re.search(r"capacit|pF|fF", ctx, re.I):
                    hits.append((i + 1, ctx))
    return hits


def main(args):
    files = []
    for a in args:
        p = Path(a)
        files += sorted(p.rglob("*.pdf")) if p.is_dir() else [p]
    for f in files:
        try:
            hits = scan(f)
        except Exception as exc:          # a damaged or encrypted file is reported, not fatal
            print(f"== {f.name}: not readable ({exc})")
            continue
        if not hits:
            continue
        print(f"== {f.name}")
        seen = set()
        for page, ctx in hits:
            key = (page, ctx[:60])
            if key in seen:
                continue
            seen.add(key)
            print(f"  p{page}: ...{ctx}...")


if __name__ == "__main__":
    main(sys.argv[1:])
