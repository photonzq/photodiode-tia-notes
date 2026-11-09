"""Contact sheets of the specification-table titles and the rows that Table A.9
cites (input range and input bias current), for reading the table or section
numbers from the rendered pages.  Each strip is labelled with the part, the
1-based PDF page and the row; the clip heights are in points and were found
with vcm_table_sources.py.

Usage:  python -P vcm_table_sheets.py NOTE_FOLDER OUT_DIR
        (NOTE_FOLDER is TIA_high_gain_survey_2026-11-02; the companion's
        datasheets are taken from its sibling folder)
"""
import pathlib
import sys

import pymupdf
from PIL import Image, ImageDraw

HG = pathlib.Path(sys.argv[1]) / "datasheets" / "opamps"
CO = pathlib.Path(sys.argv[1]).parent / "TIA_opamp_survey_2026-10-25" / "datasheets"
OUT = pathlib.Path(sys.argv[2])

# part: (pdf, [(page, y0, y1, label), ...])
ITEMS = {
    "ADA4530-1": (HG / "ada4530-1.pdf", [(4, 538, 612, "title"), (4, 632, 650, "IB"), (5, 166, 184, "IVR")]),
    "OPA928": (HG / "opa928.pdf", [(6, 72, 106, "title"), (6, 132, 152, "IB"), (6, 330, 410, "VCM, CMRR")]),
    "LMP7721": (HG / "lmp7721.pdf", [(6, 188, 216, "title"), (6, 276, 294, "IB"), (6, 392, 410, "CMVR")]),
    "LMC6001A": (HG / "lmc6001.pdf", [(4, 340, 368, "title"), (4, 408, 428, "IB"), (5, 150, 200, "CM range")]),
    "LMC662": (HG / "lmc662.pdf", [(6, 72, 106, "title"), (6, 362, 380, "IB"), (6, 480, 540, "VCM")]),
    "ADA4625-1": (HG / "ada4625-1-4625-2.pdf", [(3, 68, 124, "title"), (3, 216, 232, "IB"), (3, 292, 308, "IVR")]),
    "OPA828": (HG / "opa828.pdf", [(5, 72, 106, "title"), (5, 321, 338, "IB"), (5, 503, 548, "VCM")]),
    "OPA827": (HG / "opa827.pdf", [(6, 66, 100, "title"), (6, 196, 214, "IB"), (6, 296, 324, "VCM")]),
    "OPA140": (HG / "opa140.pdf", [(7, 72, 106, "title"), (7, 219, 236, "IB"), (7, 355, 385, "VCM")]),
    "OPA145": (HG / "opa145.pdf", [(6, 72, 106, "title"), (6, 409, 427, "IB"), (6, 564, 594, "VCM")]),
    "OPA1656": (HG / "opa1656.pdf", [(6, 72, 106, "title"), (6, 548, 566, "IB"), (6, 595, 624, "VCM")]),
    "OPA2156": (HG / "opa2156.pdf", [(5, 66, 100, "title"), (5, 306, 324, "IB"), (5, 523, 636, "VCM")]),
    "OPA320": (HG / "opa320.pdf", [(7, 396, 428, "title"), (7, 616, 634, "IB"), (7, 530, 580, "VCM")]),
    "OPA381": (HG / "opa381.pdf", [(3, 70, 100, "title"), (3, 210, 226, "IB"), (3, 292, 316, "VCM")]),
    "OPA388": (HG / "opa388.pdf", [(7, 420, 452, "title"), (8, 168, 186, "IB"), (8, 440, 520, "VCM")]),
    "OPA656": (HG / "opa656.pdf", [(5, 72, 106, "title"), (5, 481, 498, "IB"), (5, 550, 650, "range")]),
    "OPA657": (CO / "opa657.pdf", [(5, 66, 100, "title"), (5, 472, 490, "IB"), (5, 556, 612, "range")]),
    "OPA818": (CO / "opa818.pdf", [(5, 72, 106, "title"), (5, 581, 598, "IB"), (5, 709, 726, "range+"), (6, 124, 140, "range-")]),
    "ADA4817-1": (CO / "ada4817-1_distributor_copy.pdf", [(3, 60, 130, "title"), (3, 395, 480, "IB, range")]),
    "LTC6268-10": (CO / "ltc6268-10_distributor_copy.pdf", [(3, 295, 330, "title"), (3, 420, 436, "IB"), (3, 703, 718, "IVR")]),
    "OPA858": (CO / "opa858.pdf", [(6, 72, 106, "title"), (6, 444, 462, "IB"), (6, 572, 676, "VIH/VIL")]),
    "OPA211": (HG / "opa211.pdf", [(8, 66, 100, "title"), (8, 226, 244, "IB"), (8, 382, 446, "VCM")]),
    "OPA855": (CO / "opa855.pdf", [(6, 72, 106, "title"), (6, 449, 466, "IB"), (6, 589, 672, "VIH/VIL")]),
    "OPA955": (CO / "opa955.pdf", [(5, 70, 100, "title"), (5, 445, 462, "IB"), (5, 585, 668, "VIH/VIL")]),
    "LMH6629": (CO / "lmh6629.pdf", [(5, 70, 100, "title"), (6, 160, 176, "CMVR"), (6, 319, 336, "IB")]),
}

GROUPS = [["ADA4530-1", "OPA928", "LMP7721", "LMC6001A", "LMC662"],
          ["ADA4625-1", "OPA828", "OPA827", "OPA140", "OPA145"],
          ["OPA1656", "OPA2156", "OPA320", "OPA381", "OPA388"],
          ["OPA656", "OPA657", "OPA818", "ADA4817-1", "LTC6268-10"],
          ["OPA858", "OPA211", "OPA855", "OPA955", "LMH6629"]]

for gi, group in enumerate(GROUPS, 1):
    strips = []
    for name in group:
        pdf, items = ITEMS[name]
        doc = pymupdf.open(pdf)
        for page, y0, y1, label in items:
            pg = doc[page - 1]
            pix = pg.get_pixmap(dpi=130, clip=pymupdf.Rect(30, y0, pg.rect.x1 - 30, y1))
            im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            head = Image.new("RGB", (im.width, 16), (235, 235, 235))
            ImageDraw.Draw(head).text((4, 2), f"{name}  p. {page}  {label}", fill=(150, 0, 0))
            strips += [head, im]
    w = max(s.width for s in strips)
    sheet = Image.new("RGB", (w, sum(s.height + 2 for s in strips)), "white")
    y = 0
    for s in strips:
        sheet.paste(s, (0, y))
        y += s.height + 2
    sheet.save(OUT / f"sheet{gi}.png")
    print("sheet", gi, sheet.size)
