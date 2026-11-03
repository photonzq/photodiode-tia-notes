"""Read curve values from vector (not bitmap) plots inside a PDF page.

Many datasheet figures are stored as vector line art.  This script lists the
stroked paths inside a clip rectangle of one page, reports the axis-aligned
gridlines (so they can be matched by eye to the tick labels on a rendered
image), and, once two calibration gridlines per axis are given, converts a
chosen path to data coordinates and interpolates it at requested x values.

It is a cross-check for values read by eye from a rendered page; always
compare its output with the rendered image (a path can be a gridline, a
label leader line or an arrow instead of the curve).

Usage
-----
List paths and gridlines inside a clip (PDF points, 1-based page index):
    python vector_curve_extract.py <pdf> <page> --clip x0,y0,x1,y1 --list

Sample one or more paths (indices from --list) at given x values:
    python vector_curve_extract.py <pdf> <page> --clip x0,y0,x1,y1 \
        --paths 12,13 --xcal 100.5:0.01,400.2:1000 --xlog \
        --ycal 80.0:70,230.0:-10 --at 1e5,1e6,1e7

    --xcal / --ycal : two "pt:value" pairs (page coordinate in points and the
                      data value of the gridline at that coordinate).
    --xlog / --ylog : the axis is logarithmic.
    --at            : x values (data units) at which to interpolate.
    --dump          : print every vertex of the selected paths in data units.
"""
import argparse
import math
import sys

import pymupdf


def parse_cal(spec):
    pairs = []
    for part in spec.split(","):
        pt, val = part.split(":")
        pairs.append((float(pt), float(val)))
    if len(pairs) != 2:
        raise SystemExit("calibration needs exactly two pt:value pairs")
    return pairs


def make_map(cal, log):
    (p1, v1), (p2, v2) = cal
    if log:
        l1, l2 = math.log10(v1), math.log10(v2)
        return lambda p: 10 ** (l1 + (p - p1) * (l2 - l1) / (p2 - p1))
    return lambda p: v1 + (p - p1) * (v2 - v1) / (p2 - p1)


def make_inverse(cal, log):
    (p1, v1), (p2, v2) = cal
    if log:
        l1, l2 = math.log10(v1), math.log10(v2)
        return lambda v: p1 + (math.log10(v) - l1) * (p2 - p1) / (l2 - l1)
    return lambda v: p1 + (v - v1) * (p2 - p1) / (v2 - v1)


def path_points(drawing, bezier_steps=8):
    """Return the vertices of a stroked drawing as a list of polylines."""
    lines = []
    current = []
    last = None
    for item in drawing["items"]:
        kind = item[0]
        if kind == "l":
            a, b = item[1], item[2]
            if last is None or abs(a.x - last.x) > 1e-3 or abs(a.y - last.y) > 1e-3:
                if current:
                    lines.append(current)
                current = [(a.x, a.y)]
            current.append((b.x, b.y))
            last = b
        elif kind == "c":
            a, c1, c2, b = item[1], item[2], item[3], item[4]
            if last is None or abs(a.x - last.x) > 1e-3 or abs(a.y - last.y) > 1e-3:
                if current:
                    lines.append(current)
                current = [(a.x, a.y)]
            for k in range(1, bezier_steps + 1):
                t = k / bezier_steps
                x = ((1 - t) ** 3 * a.x + 3 * (1 - t) ** 2 * t * c1.x
                     + 3 * (1 - t) * t ** 2 * c2.x + t ** 3 * b.x)
                y = ((1 - t) ** 3 * a.y + 3 * (1 - t) ** 2 * t * c1.y
                     + 3 * (1 - t) * t ** 2 * c2.y + t ** 3 * b.y)
                current.append((x, y))
            last = b
        elif kind == "re":
            rect = item[1]
            if current:
                lines.append(current)
                current = []
            lines.append([(rect.x0, rect.y0), (rect.x1, rect.y0),
                          (rect.x1, rect.y1), (rect.x0, rect.y1),
                          (rect.x0, rect.y0)])
            last = None
        elif kind == "qu":
            quad = item[1]
            if current:
                lines.append(current)
                current = []
            lines.append([(quad.ul.x, quad.ul.y), (quad.ur.x, quad.ur.y),
                          (quad.lr.x, quad.lr.y), (quad.ll.x, quad.ll.y),
                          (quad.ul.x, quad.ul.y)])
            last = None
    if current:
        lines.append(current)
    return lines


def inside(points, clip):
    return any(clip.x0 <= x <= clip.x1 and clip.y0 <= y <= clip.y1 for x, y in points)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pdf")
    parser.add_argument("page", type=int)
    parser.add_argument("--clip", required=True)
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--paths", default="")
    parser.add_argument("--xcal", default="")
    parser.add_argument("--ycal", default="")
    parser.add_argument("--xlog", action="store_true")
    parser.add_argument("--ylog", action="store_true")
    parser.add_argument("--at", default="")
    parser.add_argument("--dump", action="store_true")
    args = parser.parse_args()

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    doc = pymupdf.open(args.pdf)
    page = doc[args.page - 1]
    x0, y0, x1, y1 = (float(v) for v in args.clip.split(","))
    clip = pymupdf.Rect(x0, y0, x1, y1)

    drawings = []
    for drawing in page.get_drawings():
        if drawing.get("type") not in ("s", "fs"):
            continue
        polys = path_points(drawing)
        pts = [p for poly in polys for p in poly]
        if pts and inside(pts, clip):
            drawings.append((drawing, polys))

    if args.list:
        vertical, horizontal = set(), set()
        for index, (drawing, polys) in enumerate(drawings):
            pts = [p for poly in polys for p in poly]
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            n_seg = sum(len(poly) - 1 for poly in polys)
            straight = all(len(poly) == 2 for poly in polys)
            kind = "line"
            if straight:
                for (ax, ay), (bx, by) in (poly for poly in polys):
                    if abs(ax - bx) < 0.05 and abs(ay - by) > 2:
                        vertical.add(round(ax, 2))
                    elif abs(ay - by) < 0.05 and abs(ax - bx) > 2:
                        horizontal.add(round(ay, 2))
                kind = "straight"
            print(f"[{index}] width={drawing.get('width')} color={drawing.get('color')} "
                  f"segments={n_seg} kind={kind} "
                  f"bbox=({min(xs):.2f},{min(ys):.2f})-({max(xs):.2f},{max(ys):.2f})")
        print("vertical gridline x (pt):", sorted(vertical))
        print("horizontal gridline y (pt):", sorted(horizontal))

    if args.paths:
        if not (args.xcal and args.ycal):
            raise SystemExit("--paths needs --xcal and --ycal")
        xmap = make_map(parse_cal(args.xcal), args.xlog)
        ymap = make_map(parse_cal(args.ycal), args.ylog)
        xinv = make_inverse(parse_cal(args.xcal), args.xlog)
        targets = [float(v) for v in args.at.split(",")] if args.at else []
        for index in (int(v) for v in args.paths.split(",")):
            drawing, polys = drawings[index]
            print(f"path [{index}] width={drawing.get('width')}")
            if args.dump:
                for poly in polys:
                    for (px, py) in poly:
                        print(f"   x={xmap(px):.6g}  y={ymap(py):.6g}")
            for target in targets:
                xt = xinv(target)
                hits = []
                for poly in polys:
                    for (ax, ay), (bx, by) in zip(poly, poly[1:]):
                        lo, hi = min(ax, bx), max(ax, bx)
                        if lo <= xt <= hi and hi > lo:
                            t = (xt - ax) / (bx - ax)
                            hits.append(ymap(ay + t * (by - ay)))
                if hits:
                    vals = ", ".join(f"{h:.4g}" for h in hits)
                    print(f"   x={target:.4g}: y = {vals}")
                else:
                    print(f"   x={target:.4g}: no crossing")


if __name__ == "__main__":
    main()
