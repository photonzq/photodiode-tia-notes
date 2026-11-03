"""Extract vector polylines (plotted curves) inside a plot frame and read them at given x values.

usage: python -I vcurves.py <pdf> <page1based> <frame x0,y0,x1,y1>
         <xcal xa,fa,xb,fb,log|lin> <ycal ya,va,yb,vb,log|lin> <xmarks f1,f2,...> [halfwin_decades]
Prints, for every stroked path with many points inside the frame: stroke colour, number of points,
x-range covered, and the value at each xmark (linear interpolation in the transformed axes) plus
the median over +/- halfwin (in decades for log x, in axis units for lin x).
"""
import sys, math, statistics
import pymupdf

pdf, pno = sys.argv[1], int(sys.argv[2])
frame = pymupdf.Rect(*map(float, sys.argv[3].split(",")))
xa, fa, xb, fb, xmode = sys.argv[4].split(",")
ya, va, yb, vb, ymode = sys.argv[5].split(",")
xa, fa, xb, fb = map(float, (xa, fa, xb, fb))
ya, va, yb, vb = map(float, (ya, va, yb, vb))
xmarks = [float(v) for v in sys.argv[6].split(",")]
halfwin = float(sys.argv[7]) if len(sys.argv) > 7 else 0.03


def tr(v, mode):
    return math.log10(v) if mode == "log" else v


def itr(t, mode):
    return 10 ** t if mode == "log" else t


def xval(x):
    t = tr(fa, xmode) + (x - xa) / (xb - xa) * (tr(fb, xmode) - tr(fa, xmode))
    return t  # transformed


def yval(y):
    t = tr(va, ymode) + (y - ya) / (yb - ya) * (tr(vb, ymode) - tr(va, ymode))
    return itr(t, ymode)


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
    # sort by x, dedupe
    xs_t = [xval(p.x) for p in pts]
    ys_v = [yval(p.y) for p in pts]
    pairs = sorted(zip(xs_t, ys_v))
    # skip straight grid lines (all same x or same y)
    if max(p[0] for p in pairs) - min(p[0] for p in pairs) < 1e-6:
        continue
    if max(p[1] for p in pairs) - min(p[1] for p in pairs) < 1e-9:
        continue
    n += 1
    col = tuple(round(c, 2) for c in dr["color"])
    print(f"--- path {n}: color={col} width={dr.get('width')} npts={len(pairs)} "
          f"x=[{itr(pairs[0][0], xmode):.4g},{itr(pairs[-1][0], xmode):.4g}]")
    out = []
    for f in xmarks:
        t = tr(f, xmode)
        val = None
        for (x0, y0), (x1, y1) in zip(pairs, pairs[1:]):
            if x0 <= t <= x1 and x1 > x0:
                if ymode == "log":
                    val = 10 ** (math.log10(y0) + (t - x0) / (x1 - x0) * (math.log10(y1) - math.log10(y0)))
                else:
                    val = y0 + (t - x0) / (x1 - x0) * (y1 - y0)
                break
        win = [y for (x, y) in pairs if abs(x - t) <= halfwin]
        med = statistics.median(win) if win else None
        lo = min(win) if win else None
        hi = max(win) if win else None
        out.append(f"{f:.4g}: {val if val is None else round(val, 3)} (median {med if med is None else round(med, 3)}, range {lo if lo is None else round(lo, 3)}-{hi if hi is None else round(hi, 3)})")
    for o in out:
        print("   ", o)
