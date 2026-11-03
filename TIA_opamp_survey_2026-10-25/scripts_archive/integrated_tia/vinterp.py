"""Collect all stroked segments of one colour inside a frame, build a polyline sorted by x,
and interpolate at given x values (x log or lin, y log or lin).

usage: python -I vinterp.py <pdf> <page1based> <frame x0,y0,x1,y1>
         <xcal xa,fa,xb,fb,log|lin> <ycal ya,va,yb,vb,log|lin> <r,g,b> <xmarks>
"""
import sys, math
import pymupdf

pdf, pno = sys.argv[1], int(sys.argv[2])
frame = pymupdf.Rect(*map(float, sys.argv[3].split(",")))
xa, fa, xb, fb, xmode = sys.argv[4].split(",")
ya, va, yb, vb, ymode = sys.argv[5].split(",")
xa, fa, xb, fb = map(float, (xa, fa, xb, fb))
ya, va, yb, vb = map(float, (ya, va, yb, vb))
col = tuple(float(c) for c in sys.argv[6].split(","))
marks = [float(v) for v in sys.argv[7].split(",")]


def tr(v, m):
    return math.log10(v) if m == "log" else v


def itr(t, m):
    return 10 ** t if m == "log" else t


def xv(x):
    return tr(fa, xmode) + (x - xa) / (xb - xa) * (tr(fb, xmode) - tr(fa, xmode))


def yv(y):
    return tr(va, ymode) + (y - ya) / (yb - ya) * (tr(vb, ymode) - tr(va, ymode))


d = pymupdf.open(pdf)
pg = d[pno - 1]
grow = pymupdf.Rect(frame.x0 - 0.5, frame.y0 - 0.5, frame.x1 + 0.5, frame.y1 + 0.5)
pts = []
for dr in pg.get_drawings():
    c = dr.get("color")
    if c is None or any(abs(a - b) > 0.02 for a, b in zip(c, col)):
        continue
    for it in dr["items"]:
        if it[0] == "l":
            seg = [it[1], it[2]]
        elif it[0] == "c":
            seg = [it[1], it[4]]
        else:
            continue
        for p in seg:
            if grow.contains(p):
                pts.append((xv(p.x), yv(p.y)))
pts = sorted(set((round(a, 6), round(b, 6)) for a, b in pts))
print("points:", len(pts), "x-range:", itr(pts[0][0], xmode), itr(pts[-1][0], xmode))
for m in marks:
    t = tr(m, xmode)
    val = None
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 <= t <= x1 and x1 > x0:
            val = itr(y0 + (t - x0) / (x1 - x0) * (y1 - y0), ymode)
            break
    print(f"  x={m:g}: {val if val is None else round(val, 4)}")
