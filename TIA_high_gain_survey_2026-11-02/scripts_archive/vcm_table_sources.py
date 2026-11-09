"""Locate, for Table A.9, the specification table that holds each part's
input-range row and input-bias-current row, and render the table's title and
those rows for reading.

Text extraction only locates candidate lines (table titles and the rows); the
citations in data/ib_vs_vcm.json were then read from the rendered crops.

For each part it prints the title lines ("Table n", "n.n Electrical
Characteristics", "... ELECTRICAL CHARACTERISTICS") found on the pages given,
and the rows that match the range and bias-current terms, with their page and
height on the page, and writes one PNG per part (the title lines and rows
stacked as strips) to OUT_DIR.

Usage:  python -P vcm_table_sources.py OUT_DIR
"""
from __future__ import annotations

import pathlib
import re
import sys

import pymupdf
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
HG = ROOT / "datasheets" / "opamps"
CO = ROOT.parent / "TIA_opamp_survey_2026-10-25" / "datasheets"

# part: (pdf, 1-based pages that hold the range and bias-current rows)
PARTS = {
    "ADA4530-1": (HG / "ada4530-1.pdf", [3, 4, 5, 6, 7, 8]),
    "OPA928": (HG / "opa928.pdf", [4, 5, 6, 7, 8, 9]),
    "LMP7721": (HG / "lmp7721.pdf", [5, 6]),
    "LMC6001A": (HG / "lmc6001.pdf", [4, 5]),
    "LMC662": (HG / "lmc662.pdf", [6]),
    "ADA4625-1": (HG / "ada4625-1-4625-2.pdf", [3, 5]),
    "OPA828": (HG / "opa828.pdf", [5]),
    "OPA827": (HG / "opa827.pdf", [6]),
    "OPA140": (HG / "opa140.pdf", [7]),
    "OPA145": (HG / "opa145.pdf", [6]),
    "OPA1656": (HG / "opa1656.pdf", [6]),
    "OPA2156": (HG / "opa2156.pdf", [5]),
    "OPA320": (HG / "opa320.pdf", [7]),
    "OPA381": (HG / "opa381.pdf", [3]),
    "OPA388": (HG / "opa388.pdf", [7, 8]),
    "OPA656": (HG / "opa656.pdf", [5]),
    "OPA657": (CO / "opa657.pdf", [5]),
    "OPA818": (CO / "opa818.pdf", [5, 6]),
    "ADA4817-1": (CO / "ada4817-1_distributor_copy.pdf", [3]),
    "LTC6268-10": (CO / "ltc6268-10_distributor_copy.pdf", [3]),
    "OPA858": (CO / "opa858.pdf", [6]),
    "OPA211": (HG / "opa211.pdf", [8]),
    "OPA855": (CO / "opa855.pdf", [6]),
    "OPA955": (CO / "opa955.pdf", [5]),
    "LMH6629": (CO / "lmh6629.pdf", [5, 6]),
}

TITLE = re.compile(r"(^Table\s+\d+[-.\d]*)|(\d+\.\d+\s+Electrical Characteristics)|(ELECTRICAL CHARACTERISTICS)"
                   r"|(Electrical Characteristics)", re.I)
ROW = re.compile(r"(common[- ]mode (input )?(voltage )?range)|(input voltage range)|(\bIVR\b)|(\bCMVR\b)"
                 r"|(input common[- ]mode)|(input bias current)|(\bI_?B\b)|(most (positive|negative) input)"
                 r"|(V\s?IH)|(V\s?IL)", re.I)


def lines_of(page):
    out = []
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            text = "".join(span["text"] for span in line["spans"]).strip()
            if text:
                out.append((line["bbox"], text))
    return out


def strip(page, y0, y1, dpi=170):
    rect = pymupdf.Rect(page.rect.x0 + 20, max(page.rect.y0, y0 - 3), page.rect.x1 - 20, min(page.rect.y1, y1 + 3))
    pix = page.get_pixmap(dpi=dpi, clip=rect)
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def main() -> None:
    out_dir = pathlib.Path(sys.argv[1])
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, (pdf, pages) in PARTS.items():
        doc = pymupdf.open(pdf)
        print(f"==== {name}  ({pdf.name}, {doc.page_count} pages)")
        strips = []
        for pno in pages:
            page = doc[pno - 1]
            for bbox, text in lines_of(page):
                kind = "TITLE" if TITLE.search(text) and len(text) < 120 else ("row" if ROW.search(text) else None)
                if kind:
                    print(f"  p. {pno:2d}  y {bbox[1]:6.1f}  {kind:5s}  {text[:110]}")
                    if kind == "TITLE" or len(strips) < 40:
                        strips.append(strip(page, bbox[1], bbox[3] if kind == "TITLE" else bbox[3] + 2))
        if strips:
            w = max(s.width for s in strips)
            h = sum(s.height + 6 for s in strips)
            sheet = Image.new("RGB", (w, h), "white")
            y = 0
            for s in strips:
                sheet.paste(s, (0, y))
                y += s.height + 6
            sheet.save(out_dir / f"{name}.png")


if __name__ == "__main__":
    main()
