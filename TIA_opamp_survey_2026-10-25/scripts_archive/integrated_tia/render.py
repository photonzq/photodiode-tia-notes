"""Render selected pages of a PDF to PNG.

usage: python -I render.py <pdf> <outprefix> <dpi> <pages>
pages: comma-separated 1-based PDF page indices or ranges, e.g. 1-4,7,9
Prints the printed page label (if any) and output path for each page.
"""
import sys
import pymupdf

pdf, prefix, dpi, pages = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
d = pymupdf.open(pdf)
idx = []
for part in pages.split(","):
    if "-" in part:
        a, b = part.split("-")
        idx.extend(range(int(a), int(b) + 1))
    else:
        idx.append(int(part))
for i in idx:
    if i < 1 or i > d.page_count:
        print("skip", i, "of", d.page_count)
        continue
    pg = d[i - 1]
    out = f"{prefix}_p{i:02d}.png"
    pg.get_pixmap(dpi=dpi).save(out)
    print(i, "label=", pg.get_label(), out)
