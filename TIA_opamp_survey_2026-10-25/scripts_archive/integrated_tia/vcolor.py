"""Collect all stroked segments of each colour inside a frame (curves drawn as many short paths)
and read them at given x values.

usage: python -I vcolor.py <pdf> <page1based> <frame x0,y0,x1,y1>
         <xcal xa,fa,xb,fb,log|lin> <ycal ya,va,yb,vb,log|lin> <xmarks> [halfwin] [min_segments]
halfwin: half-window for the median, in decades (log x) or axis units (lin x).
min_segments: colours with fewer stroked segments are ignored (default 20; use 2 for sparse
              curves such as integrated-noise or bandwidth-vs-temperature plots).
"""
import sys, math, statistics, collections
import pymupdf

pdf, pno = sys.argv[1], int(sys.argv[2])
frame = pymupdf.Rect(*map(float, sys.argv[3].split(",")))
xa, fa, xb, fb, xmode = sys.argv[4].split(",")
ya, va, yb, vb, ymode = sys.argv[5].split(",")
xa, fa, xb, fb = map(float, (xa, fa, xb, fb))
ya, va, yb, vb = map(float, (ya, va, yb, vb))
marks = [float(v) for v in sys.argv[6].split(",")]
halfwin = float(sys.argv[7]) if len(sys.argv) > 7 else 0.02
min_segments = int(sys.argv[8]) if len(sys.argv) > 8 else 20


def tr(v, m):
    return math.log10(v) if m == "log" else v


def itr(t, m):
    return 10 ** t if m == "log" else t


def xv(x):
    return tr(fa, xmode) + (x - xa) / (xb - xa) * (tr(fb, xmode) - tr(fa, xmode))


def yv(y):
    return itr(tr(va, ymode) + (y - ya) / (yb - ya) * (tr(vb, ymode) - tr(va, ymode)), ymode)


d = pymupdf.open(pdf)
pg = d[pno - 1]
grow = pymupdf.Rect(frame.x0 - 0.5, frame.y0 - 0.5, frame.x1 + 0.5, frame.y1 + 0.5)
segs = collections.defaultdict(list)
for dr in pg.get_drawings():
    col = dr.get("color")
    if col is None:
        continue
    for it in dr["items"]:
        if it[0] == "l":
            p, q = it[1], it[2]
        elif it[0] == "c":
            p, q = it[1], it[4]
        else:
            continue
        if grow.contains(p) and grow.contains(q):
            segs[tuple(round(c, 2) for c in col)].append((p, q))
for col, ss in segs.items():
    if len(ss) < min_segments:
        continue
    pts = []
    for p, q in ss:
        pts.append((xv(p.x), yv(p.y)))
        pts.append((xv(q.x), yv(q.y)))
    xs = [p[0] for p in pts]
    if max(xs) - min(xs) < 1e-6:
        continue
    out = []
    for m in marks:
        t = tr(m, xmode)
        win = [y for (x, y) in pts if abs(x - t) <= halfwin]
        if win:
            out.append(f"{m:g}: median {statistics.median(win):.3g} (min {min(win):.3g}, max {max(win):.3g}, n={len(win)})")
        else:
            out.append(f"{m:g}: none")
    print(f"colour {col}: {len(ss)} segments, x=[{itr(min(xs), xmode):.3g},{itr(max(xs), xmode):.3g}]")
    for o in out:
        print("    ", o)
