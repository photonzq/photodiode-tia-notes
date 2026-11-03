"""Stack clipped regions of PDF pages into one PNG (vertically).

usage: python -I montage.py <out.png> <dpi> <pdf>:<page1based>:<x0>,<y0>,<x1>,<y1> [...]
Clip coordinates in PDF points; use 'full' for the whole page.
"""
import sys
import pymupdf

out, dpi = sys.argv[1], int(sys.argv[2])
pix_list = []
for spec in sys.argv[3:]:
    pdf, pno, rect = spec.rsplit(":", 2)
    d = pymupdf.open(pdf)
    pg = d[int(pno) - 1]
    clip = pg.rect if rect == "full" else pymupdf.Rect(*map(float, rect.split(",")))
    pix_list.append(pg.get_pixmap(dpi=dpi, clip=clip))
W = max(p.width for p in pix_list)
H = sum(p.height for p in pix_list) + 6 * (len(pix_list) - 1)
canvas = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, W, H), False)
canvas.clear_with(255)
y = 0
for p in pix_list:
    if p.alpha:
        p = pymupdf.Pixmap(p, 0)
    if p.colorspace != pymupdf.csRGB:
        p = pymupdf.Pixmap(pymupdf.csRGB, p)
    p.set_origin(0, y)
    canvas.copy(p, p.irect)
    y += p.height + 6
canvas.save(out)
print("saved", out, W, H)
