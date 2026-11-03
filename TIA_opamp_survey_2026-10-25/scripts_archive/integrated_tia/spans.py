"""Print text spans (with bbox centre, in PDF points) inside a clip rectangle.

usage: python -I spans.py <pdf> <page1based> <x0> <y0> <x1> <y1>
"""
import sys
import pymupdf

pdf, pno = sys.argv[1], int(sys.argv[2])
x0, y0, x1, y1 = map(float, sys.argv[3:7])
d = pymupdf.open(pdf)
pg = d[pno - 1]
print("page size", pg.rect)
clip = pymupdf.Rect(x0, y0, x1, y1)
for b in pg.get_text("dict", clip=clip)["blocks"]:
    for l in b.get("lines", []):
        for s in l["spans"]:
            r = pymupdf.Rect(s["bbox"])
            if r.intersects(clip) and s["text"].strip():
                print(f"{s['text']!r:24s} cx={(r.x0 + r.x1) / 2:7.2f} cy={(r.y0 + r.y1) / 2:7.2f}  bbox=({r.x0:.1f},{r.y0:.1f},{r.x1:.1f},{r.y1:.1f})")
# frame-like rectangles and long lines from vector drawings
rects = []
for dr in pg.get_drawings():
    r = dr["rect"]
    if r.intersects(clip) and r.width > 60 and r.height > 40:
        rects.append((round(r.x0, 1), round(r.y0, 1), round(r.x1, 1), round(r.y1, 1)))
for r in sorted(set(rects)):
    print("rect", r)
