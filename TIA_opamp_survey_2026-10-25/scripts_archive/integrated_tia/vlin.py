"""Read plotted curves (vector data) with linear x and y axes at given x values.

usage: python -I vlin.py <pdf> <page1based> <frame x0,y0,x1,y1> <xa,va,xb,vb> <ya,wa,yb,wb> <xmarks>
x calibration: PDF x = xa -> value va, xb -> vb ; y calibration: PDF y = ya -> wa, yb -> wb.
"""
import sys
import pymupdf

pdf, pno = sys.argv[1], int(sys.argv[2])
frame = pymupdf.Rect(*map(float, sys.argv[3].split(",")))
xa, va, xb, vb = map(float, sys.argv[4].split(","))
ya, wa, yb, wb = map(float, sys.argv[5].split(","))
marks = [float(v) for v in sys.argv[6].split(",")]
d = pymupdf.open(pdf)
pg = d[pno - 1]
grow = pymupdf.Rect(frame.x0 - 1, frame.y0 - 1, frame.x1 + 1, frame.y1 + 1)
n = 0
for dr in pg.get_drawings():
    if dr.get("color") is None:
        continue
    pts = []
    for it in dr["items"]:
        if it[0] == "l":
            pts.extend([it[1], it[2]])
        elif it[0] == "c":
            pts.extend([it[1], it[4]])
    pts = [p for p in pts if grow.contains(p)]
    if len(pts) < 8:
        continue
    pairs = sorted((va + (p.x - xa) / (xb - xa) * (vb - va), wa + (p.y - ya) / (yb - ya) * (wb - wa)) for p in pts)
    if pairs[-1][0] - pairs[0][0] < 1e-6 or max(q[1] for q in pairs) - min(q[1] for q in pairs) < 1e-6:
        continue
    n += 1
    out = []
    for m in marks:
        v = None
        for (x0, y0), (x1, y1) in zip(pairs, pairs[1:]):
            if x0 <= m <= x1 and x1 > x0:
                v = y0 + (m - x0) / (x1 - x0) * (y1 - y0)
                break
        out.append(f"{m:g}: {None if v is None else round(v, 3)}")
    col = tuple(round(c, 2) for c in dr["color"])
    print(f"path {n} color={col} npts={len(pairs)} x=[{pairs[0][0]:.3g},{pairs[-1][0]:.3g}]  " + "; ".join(out))
