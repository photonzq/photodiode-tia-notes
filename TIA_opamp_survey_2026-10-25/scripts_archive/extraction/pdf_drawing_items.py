"""Print the path items of selected drawings on a PDF page, converted to data units.

Usage
-----
python drawing_items.py <pdf> <page> --frame X0,Y0,X1,Y1 --xrange XL,XR --yrange YB,YT
                        [--xlog] [--ylog] --select x0,y0,x1,y1 [--minitems N]
                        [--bezier-steps K]

Every drawing whose bounding box lies inside the --select rectangle (PDF points)
and that has at least --minitems path items is printed: stroke colour, width and
its vertices in data units.  Cubic Bezier segments are sampled at K points, so
smooth hand-drawn curves (common in older datasheets) can be read numerically.
Use this only as a cross-check of a visual reading of the rendered figure.
"""
import argparse
import math

import pymupdf


def to_data(x, y, frame, xr, yr, xlog, ylog):
    fx0, fy0, fx1, fy1 = frame
    u = (x - fx0) / (fx1 - fx0)
    w = (fy1 - y) / (fy1 - fy0)
    if xlog:
        xv = 10 ** (math.log10(xr[0]) + u * (math.log10(xr[1]) - math.log10(xr[0])))
    else:
        xv = xr[0] + u * (xr[1] - xr[0])
    if ylog:
        yv = 10 ** (math.log10(yr[0]) + w * (math.log10(yr[1]) - math.log10(yr[0])))
    else:
        yv = yr[0] + w * (yr[1] - yr[0])
    return xv, yv


def bezier(p0, p1, p2, p3, t):
    s = 1 - t
    x = s**3 * p0.x + 3 * s**2 * t * p1.x + 3 * s * t**2 * p2.x + t**3 * p3.x
    y = s**3 * p0.y + 3 * s**2 * t * p1.y + 3 * s * t**2 * p2.y + t**3 * p3.y
    return x, y


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("page", type=int)
    ap.add_argument("--frame", required=True)
    ap.add_argument("--xrange", required=True)
    ap.add_argument("--yrange", required=True)
    ap.add_argument("--xlog", action="store_true")
    ap.add_argument("--ylog", action="store_true")
    ap.add_argument("--select", required=True)
    ap.add_argument("--minitems", type=int, default=1)
    ap.add_argument("--bezier-steps", type=int, default=8)
    a = ap.parse_args()
    frame = tuple(float(v) for v in a.frame.split(","))
    xr = tuple(float(v) for v in a.xrange.split(","))
    yr = tuple(float(v) for v in a.yrange.split(","))
    sel = pymupdf.Rect(*(float(v) for v in a.select.split(",")))
    page = pymupdf.open(a.pdf)[a.page - 1]
    for i, d in enumerate(page.get_drawings()):
        r = pymupdf.Rect(d["rect"])
        if not sel.contains(r) or len(d["items"]) < a.minitems:
            continue
        col = d.get("color")
        col = tuple(round(c, 3) for c in col) if col else None
        print(f"[{i}] items={len(d['items'])} color={col} width={d.get('width')}")
        pts = []
        for it in d["items"]:
            if it[0] == "l":
                pts += [(it[1].x, it[1].y), (it[2].x, it[2].y)]
            elif it[0] == "c":
                for k in range(a.bezier_steps + 1):
                    pts.append(bezier(it[1], it[2], it[3], it[4], k / a.bezier_steps))
            elif it[0] == "re":
                rr = it[1]
                pts += [(rr.x0, rr.y0), (rr.x1, rr.y1)]
        last = None
        for x, y in pts:
            xv, yv = to_data(x, y, frame, xr, yr, a.xlog, a.ylog)
            key = (round(xv, 6), round(yv, 6))
            if key == last:
                continue
            last = key
            print(f"    {xv:.5g}\t{yv:.5g}")


if __name__ == "__main__":
    main()
