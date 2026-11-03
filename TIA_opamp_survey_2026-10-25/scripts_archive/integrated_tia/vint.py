"""Integrate a plotted noise-density curve (vector data) over linear frequency.

usage: python -I vint.py <pdf> <page1based> <frame x0,y0,x1,y1>
         <xcal xa,fa,xb,fb,log> <ycal ya,va,yb,vb,log|lin> <f_lo> <f_hi>[,<f_hi2>,...] [yscale]
For each stroked path in the frame: sqrt( integral of y(f)^2 df ) from f_lo to f_hi (trapezoid in f,
y interpolated log-linearly between plotted points).  yscale multiplies y (e.g. 1e-12 for pA/rtHz).
Below the first plotted point the first value is held (only matters if f_lo < first point).
"""
import sys, math
import pymupdf

pdf, pno = sys.argv[1], int(sys.argv[2])
frame = pymupdf.Rect(*map(float, sys.argv[3].split(",")))
xa, fa, xb, fb, xmode = sys.argv[4].split(",")
ya, va, yb, vb, ymode = sys.argv[5].split(",")
xa, fa, xb, fb = map(float, (xa, fa, xb, fb))
ya, va, yb, vb = map(float, (ya, va, yb, vb))
f_lo = float(sys.argv[6])
f_his = [float(v) for v in sys.argv[7].split(",")]
yscale = float(sys.argv[8]) if len(sys.argv) > 8 else 1.0


def fval(x):
    t = math.log10(fa) + (x - xa) / (xb - xa) * (math.log10(fb) - math.log10(fa))
    return 10 ** t


def yval(y):
    if ymode == "log":
        t = math.log10(va) + (y - ya) / (yb - ya) * (math.log10(vb) - math.log10(va))
        return 10 ** t
    return va + (y - ya) / (yb - ya) * (vb - va)


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
    if len(pts) < 20:
        continue
    pairs = sorted((fval(p.x), yval(p.y)) for p in pts)
    if pairs[-1][0] / pairs[0][0] < 1.01:
        continue
    n += 1
    # dense resampling on a log grid
    res = []
    for f_hi in f_his:
        N = 4000
        lf0, lf1 = math.log10(f_lo), math.log10(f_hi)
        grid = [10 ** (lf0 + (lf1 - lf0) * k / N) for k in range(N + 1)]

        def interp(f):
            if f <= pairs[0][0]:
                return pairs[0][1]
            if f >= pairs[-1][0]:
                return pairs[-1][1]
            for (x0, y0), (x1, y1) in zip(pairs, pairs[1:]):
                if x0 <= f <= x1 and x1 > x0:
                    w = (math.log10(f) - math.log10(x0)) / (math.log10(x1) - math.log10(x0))
                    return 10 ** (math.log10(y0) + w * (math.log10(y1) - math.log10(y0)))
            return pairs[-1][1]

        vals = [(interp(f) * yscale) ** 2 for f in grid]
        tot = 0.0
        for k in range(N):
            tot += 0.5 * (vals[k] + vals[k + 1]) * (grid[k + 1] - grid[k])
        res.append(f"{f_lo:.3g}-{f_hi:.3g} Hz: rms = {math.sqrt(tot):.4g}")
    col = tuple(round(c, 2) for c in dr["color"])
    print(f"path {n} color={col} f=[{pairs[0][0]:.3g},{pairs[-1][0]:.3g}]  " + " | ".join(res))
