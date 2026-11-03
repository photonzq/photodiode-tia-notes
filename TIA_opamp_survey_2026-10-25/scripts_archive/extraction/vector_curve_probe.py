"""Probe vector-drawn plot curves in a PDF page (cross-check for visual readings).

Many older datasheets draw their typical-characteristic plots as vector paths.
This tool lists the paths inside a clip rectangle and, given an axis
calibration, interpolates each path's value at requested x positions.

Usage
-----
List mode (find the frame, gridlines and curves; coordinates in PDF points):
    python vector_curve_probe.py <pdf> <page> <x0,y0,x1,y1> --list

Query mode:
    python vector_curve_probe.py <pdf> <page> <x0,y0,x1,y1>
        --xcal PT_A:VAL_A,PT_B:VAL_B [--xlog]
        --ycal PT_A:VAL_A,PT_B:VAL_B [--ylog]
        --query 1e5,1e6,... [--minwidth 0.6] [--minseg 4]

* <page> is the 1-based PDF page index.
* --xcal gives two x positions in points with the data value they represent
  (for example the left and right frame edges); --xlog for a log axis.
  --ycal likewise for y.
* Paths with stroke width below --minwidth or fewer than --minseg segments
  are skipped in query mode (gridlines are thin single segments).
* Bezier segments are flattened by sampling.
"""
import argparse
import math

import pymupdf


def flatten(items, n_bezier=12):
    """Turn a drawing's items into a list of polylines [(x, y), ...]."""
    lines = []
    current = []
    last = None
    for it in items:
        kind = it[0]
        if kind == "l":
            p1, p2 = it[1], it[2]
            if last is None or abs(p1.x - last.x) > 1e-3 or abs(p1.y - last.y) > 1e-3:
                if len(current) > 1:
                    lines.append(current)
                current = [(p1.x, p1.y)]
            current.append((p2.x, p2.y))
            last = p2
        elif kind == "c":
            p0, c1, c2, p3 = it[1], it[2], it[3], it[4]
            if last is None or abs(p0.x - last.x) > 1e-3 or abs(p0.y - last.y) > 1e-3:
                if len(current) > 1:
                    lines.append(current)
                current = [(p0.x, p0.y)]
            for k in range(1, n_bezier + 1):
                t = k / n_bezier
                x = ((1 - t) ** 3 * p0.x + 3 * (1 - t) ** 2 * t * c1.x
                     + 3 * (1 - t) * t ** 2 * c2.x + t ** 3 * p3.x)
                y = ((1 - t) ** 3 * p0.y + 3 * (1 - t) ** 2 * t * c1.y
                     + 3 * (1 - t) * t ** 2 * c2.y + t ** 3 * p3.y)
                current.append((x, y))
            last = p3
        elif kind == "re":
            r = it[1]
            if len(current) > 1:
                lines.append(current)
            current = []
            lines.append([(r.x0, r.y0), (r.x1, r.y0), (r.x1, r.y1), (r.x0, r.y1), (r.x0, r.y0)])
            last = None
        elif kind == "qu":
            q = it[1]
            if len(current) > 1:
                lines.append(current)
            current = []
            lines.append([(q.ul.x, q.ul.y), (q.ur.x, q.ur.y), (q.lr.x, q.lr.y),
                          (q.ll.x, q.ll.y), (q.ul.x, q.ul.y)])
            last = None
    if len(current) > 1:
        lines.append(current)
    return lines


def make_map(cal, log):
    (pa, va), (pb, vb) = cal
    if log:
        va, vb = math.log10(va), math.log10(vb)

    def to_val(p):
        v = va + (p - pa) * (vb - va) / (pb - pa)
        return 10 ** v if log else v

    def to_pt(v):
        if log:
            v = math.log10(v)
        return pa + (v - va) * (pb - pa) / (vb - va)

    return to_val, to_pt


def parse_cal(text):
    pairs = []
    for part in text.split(","):
        p, v = part.split(":")
        pairs.append((float(p), float(v)))
    return pairs


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pdf")
    ap.add_argument("page", type=int)
    ap.add_argument("clip")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--xcal")
    ap.add_argument("--ycal")
    ap.add_argument("--xlog", action="store_true")
    ap.add_argument("--ylog", action="store_true")
    ap.add_argument("--query", default="")
    ap.add_argument("--cross", default="",
                    help="comma-separated y data values; report the x data values where each curve crosses them")
    ap.add_argument("--minwidth", type=float, default=0.6)
    ap.add_argument("--minseg", type=int, default=4)
    args = ap.parse_args()

    doc = pymupdf.open(args.pdf)
    page = doc[args.page - 1]
    x0, y0, x1, y1 = (float(v) for v in args.clip.split(","))
    clip = pymupdf.Rect(x0, y0, x1, y1)

    paths = []
    for d in page.get_drawings():
        r = d.get("rect")
        if r is None or not clip.intersects(r):
            continue
        width = d.get("width") or 0.0
        for poly in flatten(d["items"]):
            xs = [p[0] for p in poly]
            ys = [p[1] for p in poly]
            if max(xs) < x0 or min(xs) > x1 or max(ys) < y0 or min(ys) > y1:
                continue
            paths.append({"w": width, "poly": poly, "fill": d.get("fill"),
                          "bbox": (min(xs), min(ys), max(xs), max(ys))})

    if args.list or not args.xcal:
        for i, p in enumerate(paths):
            b = p["bbox"]
            print(f"#{i:3d} w={p['w']:.2f} n={len(p['poly']):3d} "
                  f"bbox=({b[0]:.2f},{b[1]:.2f},{b[2]:.2f},{b[3]:.2f}) fill={p['fill']}")
        return

    xval, xpt = make_map(parse_cal(args.xcal), args.xlog)
    yval, ypt = make_map(parse_cal(args.ycal), args.ylog)
    queries = [float(q) for q in args.query.split(",") if q.strip()]
    crosses = [float(q) for q in args.cross.split(",") if q.strip()]

    curves = [p for p in paths if p["w"] >= args.minwidth and len(p["poly"]) >= args.minseg]
    for i, p in enumerate(curves):
        b = p["bbox"]
        print(f"curve {i}: w={p['w']:.2f} n={len(p['poly'])} x-range {xval(b[0]):.4g} .. {xval(b[2]):.4g}"
              f"  y-range {yval(b[3]):.4g} .. {yval(b[1]):.4g}")
    print()
    for q in queries:
        xq = xpt(q)
        row = []
        for i, p in enumerate(curves):
            hits = []
            poly = p["poly"]
            for (xa, ya), (xb, yb) in zip(poly[:-1], poly[1:]):
                if (xa - xq) * (xb - xq) <= 0 and abs(xb - xa) > 1e-9:
                    t = (xq - xa) / (xb - xa)
                    hits.append(yval(ya + t * (yb - ya)))
            if hits:
                row.append(f"c{i}=" + "/".join(f"{h:.4g}" for h in hits))
        print(f"x={q:.4g}: " + "  ".join(row))
    for c in crosses:
        yq = ypt(c)
        row = []
        for i, p in enumerate(curves):
            hits = []
            poly = p["poly"]
            for (xa, ya), (xb, yb) in zip(poly[:-1], poly[1:]):
                if (ya - yq) * (yb - yq) <= 0 and abs(yb - ya) > 1e-9:
                    t = (yq - ya) / (yb - ya)
                    hits.append(xval(xa + t * (xb - xa)))
            if hits:
                row.append(f"c{i}=" + "/".join(f"{h:.4g}" for h in hits))
        print(f"y={c:.4g} crossed at x: " + "  ".join(row))


if __name__ == "__main__":
    main()
