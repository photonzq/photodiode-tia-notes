"""Find -3 dB (or other drop) frequencies of plotted gain curves (vector data).

usage: python -I vbw.py <pdf> <page1based> <frame x0,y0,x1,y1>
         <xcal xa,fa,xb,fb,log> <ycal ya,va,yb,vb,lin> <f_ref> <drop_dB>[,<drop2>...]
For each stroked path: value at f_ref, peak value, and the first frequency above f_ref where the
curve falls drop_dB below its value at f_ref.
"""
import sys, math
import pymupdf

pdf, pno = sys.argv[1], int(sys.argv[2])
frame = pymupdf.Rect(*map(float, sys.argv[3].split(",")))
xa, fa, xb, fb, _ = sys.argv[4].split(",")
ya, va, yb, vb, _ = sys.argv[5].split(",")
xa, fa, xb, fb = map(float, (xa, fa, xb, fb))
ya, va, yb, vb = map(float, (ya, va, yb, vb))
f_ref = float(sys.argv[6])
drops = [float(v) for v in sys.argv[7].split(",")]


def fval(x):
    return 10 ** (math.log10(fa) + (x - xa) / (xb - xa) * (math.log10(fb) - math.log10(fa)))


def yval(y):
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
    if pairs[-1][0] / pairs[0][0] < 1.5:
        continue
    if max(p[1] for p in pairs) - min(p[1] for p in pairs) < 1e-6:
        continue
    n += 1
    # value at f_ref
    vref = None
    for (x0, y0), (x1, y1) in zip(pairs, pairs[1:]):
        if x0 <= f_ref <= x1 and x1 > x0:
            w = (math.log10(f_ref) - math.log10(x0)) / (math.log10(x1) - math.log10(x0))
            vref = y0 + w * (y1 - y0)
            break
    if vref is None:
        vref = pairs[0][1]
    peak = max(pairs, key=lambda p: p[1])
    out = []
    for dd in drops:
        target = vref - dd
        fx = None
        for (x0, y0), (x1, y1) in zip(pairs, pairs[1:]):
            if x0 >= f_ref and y0 >= target > y1:
                w = (y0 - target) / (y0 - y1)
                fx = 10 ** (math.log10(x0) + w * (math.log10(x1) - math.log10(x0)))
                break
        out.append(f"-{dd:g} dB at {fx/1e6:.0f} MHz" if fx else f"-{dd:g} dB: not reached")
    col = tuple(round(c, 2) for c in dr["color"])
    print(f"path {n} color={col}: ref {vref:.2f} at {f_ref/1e6:g} MHz; peak {peak[1]:.2f} at {peak[0]/1e6:.0f} MHz; " + "; ".join(out))
