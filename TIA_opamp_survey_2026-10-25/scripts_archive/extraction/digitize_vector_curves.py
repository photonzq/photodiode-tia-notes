"""Read curve coordinates from a vector-graphics figure in a PDF page.

Many datasheet plots are stored as vector paths (frame rectangle, thin grid
lines, thicker coloured polylines for the curves).  This script lists the
stroked paths inside a clip rectangle, maps them to data units using the plot
frame and the axis ranges you read off the rendered figure, and interpolates
each curve at requested abscissae.  It is a cross-check for values read by
eye from a rendered image, not a replacement for looking at the figure.

Usage
-----
python digitize_vector_curves.py <pdf> <page> --clip x0,y0,x1,y1
       [--list]
       [--frame x0,y0,x1,y1]        (default: largest stroked rectangle)
       --x xmin,xmax,log|lin --y ymin,ymax,log|lin
       [--y2 ymin,ymax,log|lin --y2color r,g,b]
       [--at v1,v2,...] [--cross y1,y2,...] [--minwidth 0.5] [--minpts 6]

* <page> is the 1-based PDF page index.
* Clip and frame are in PDF points (1/72 inch), origin top-left.
* Axis ranges refer to the frame edges: xmin at the left edge, xmax at the
  right edge, ymin at the bottom edge, ymax at the top edge.
* Curves are grouped by stroke colour; paths with fewer than --minpts
  vertices (legend samples, tick marks) are ignored.
* --y2/--y2color map curves of that colour (e.g. a phase trace) to a
  secondary y axis.
* --at interpolates y at the given x values; --cross reports every x at
  which a curve crosses the given y levels (e.g. -3 dB points).
* Grid lines (thin strokes) are reported in data units so the calibration
  can be checked against the printed tick labels.
"""
import argparse
import math
from collections import defaultdict

import pymupdf


def parse_axis(spec):
    lo, hi, kind = spec.split(",")
    return float(lo), float(hi), kind.strip().lower()


def to_data(coord, edge_lo, edge_hi, axis, invert=False):
    """Map a page coordinate to a data value along one axis."""
    lo, hi, kind = axis
    frac = (coord - edge_lo) / (edge_hi - edge_lo)
    if invert:
        frac = 1.0 - frac
    if kind == "log":
        return 10 ** (math.log10(lo) + frac * (math.log10(hi) - math.log10(lo)))
    return lo + frac * (hi - lo)


def path_points(drawing):
    pts = []
    for item in drawing["items"]:
        kind = item[0]
        if kind == "l":
            p0, p1 = item[1], item[2]
            if not pts or (abs(pts[-1][0] - p0.x) > 1e-6 or abs(pts[-1][1] - p0.y) > 1e-6):
                pts.append((p0.x, p0.y))
            pts.append((p1.x, p1.y))
        elif kind == "c":
            p0, p3 = item[1], item[4]
            if not pts or (abs(pts[-1][0] - p0.x) > 1e-6 or abs(pts[-1][1] - p0.y) > 1e-6):
                pts.append((p0.x, p0.y))
            pts.append((p3.x, p3.y))
    return pts


def interp(points, xq, xlog, ylog):
    """Interpolate y at xq on a polyline given in data units (sorted by x)."""
    best = None
    for (x0, y0), (x1, y1) in zip(points[:-1], points[1:]):
        if min(x0, x1) <= xq <= max(x0, x1) and x0 != x1:
            fx0, fx1, fq = (math.log10(x0), math.log10(x1), math.log10(xq)) if xlog else (x0, x1, xq)
            t = (fq - fx0) / (fx1 - fx0)
            if ylog:
                y = 10 ** (math.log10(y0) + t * (math.log10(y1) - math.log10(y0)))
            else:
                y = y0 + t * (y1 - y0)
            best = y if best is None else best
            # keep the first crossing; report multiple crossings separately
    return best


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pdf")
    ap.add_argument("page", type=int)
    ap.add_argument("--clip", required=True)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--frame", default="")
    ap.add_argument("--x", default="")
    ap.add_argument("--y", default="")
    ap.add_argument("--y2", default="")
    ap.add_argument("--y2color", default="")
    ap.add_argument("--at", default="")
    ap.add_argument("--cross", default="")
    ap.add_argument("--minwidth", type=float, default=0.5)
    ap.add_argument("--minpts", type=int, default=6)
    args = ap.parse_args()

    doc = pymupdf.open(args.pdf)
    page = doc[args.page - 1]
    clip = pymupdf.Rect(*(float(v) for v in args.clip.split(",")))
    def overlaps(r):
        # grid lines have zero-width bounding boxes, which Rect.intersects rejects
        return (r.x0 <= clip.x1 and r.x1 >= clip.x0 and r.y0 <= clip.y1 and r.y1 >= clip.y0)

    drawings = [d for d in page.get_drawings() if overlaps(d["rect"])]

    if args.list:
        for d in drawings:
            col = tuple(round(c, 2) for c in (d.get("color") or ()))
            print(d["type"], col, round(d.get("width") or 0, 2),
                  [round(v, 1) for v in d["rect"]], "items", len(d["items"]))

    # frame: explicit or the largest stroked rectangle inside the clip
    if args.frame:
        frame = pymupdf.Rect(*(float(v) for v in args.frame.split(",")))
    else:
        rects = []
        for d in drawings:
            for item in d["items"]:
                if item[0] == "re" and d["type"] in ("s", "fs"):
                    rects.append(item[1])
        if not rects:
            print("no frame rectangle found; pass --frame")
            return
        frame = max(rects, key=lambda r: r.width * r.height)
    print(f"frame (pt): x {frame.x0:.2f}..{frame.x1:.2f}, y {frame.y0:.2f}..{frame.y1:.2f}")
    if not (args.x and args.y):
        return

    xax = parse_axis(args.x)
    yax = parse_axis(args.y)
    y2ax = parse_axis(args.y2) if args.y2 else None
    y2col = tuple(round(float(c), 2) for c in args.y2color.split(",")) if args.y2color else None

    # grid lines (thin strokes) for calibration check
    vgrid, hgrid = set(), set()
    for d in drawings:
        if (d.get("width") or 0) >= args.minwidth:
            continue
        for item in d["items"]:
            if item[0] != "l":
                continue
            p0, p1 = item[1], item[2]
            if abs(p0.x - p1.x) < 0.05 and frame.x0 - 0.5 <= p0.x <= frame.x1 + 0.5:
                vgrid.add(round(p0.x, 2))
            if abs(p0.y - p1.y) < 0.05 and frame.y0 - 0.5 <= p0.y <= frame.y1 + 0.5:
                hgrid.add(round(p0.y, 2))
    gx = [to_data(v, frame.x0, frame.x1, xax) for v in sorted(vgrid)]
    gy = [to_data(v, frame.y0, frame.y1, yax, invert=True) for v in sorted(hgrid)]
    print("vertical grid lines at x =", ", ".join(f"{v:.4g}" for v in gx))
    print("horizontal grid lines at y =", ", ".join(f"{v:.4g}" for v in gy))

    # curves grouped by colour
    groups = defaultdict(list)
    for d in drawings:
        if d["type"] not in ("s", "fs") or (d.get("width") or 0) < args.minwidth:
            continue
        pts = path_points(d)
        if len(pts) < args.minpts:
            continue
        # drop the frame itself
        if any(item[0] == "re" for item in d["items"]):
            continue
        col = tuple(round(c, 2) for c in (d.get("color") or ()))
        groups[col].append(pts)

    xq = [float(v) for v in args.at.split(",")] if args.at else []
    yc = [float(v) for v in args.cross.split(",")] if args.cross else []
    for col, paths in groups.items():
        use_y2 = y2ax is not None and y2col is not None and col == y2col
        ax = y2ax if use_y2 else yax
        print(f"\ncurve colour {col}  ({'y2' if use_y2 else 'y'} axis), {len(paths)} path(s)")
        for k, pts in enumerate(paths):
            data = [(to_data(px, frame.x0, frame.x1, xax),
                     to_data(py, frame.y0, frame.y1, ax, invert=True)) for px, py in pts]
            data_sorted = sorted(data, key=lambda t: t[0])
            print(f"  path {k}: {len(data)} pts, x {data_sorted[0][0]:.4g}..{data_sorted[-1][0]:.4g},"
                  f" y {min(t[1] for t in data):.4g}..{max(t[1] for t in data):.4g}")
            for q in xq:
                if data_sorted[0][0] <= q <= data_sorted[-1][0]:
                    y = interp(data, q, xax[2] == "log", ax[2] == "log")
                    if y is not None:
                        print(f"    x={q:.4g}: y={y:.4g}")
            for level in yc:
                # every crossing of the horizontal line y = level along the path
                for (x0, y0), (x1, y1) in zip(data[:-1], data[1:]):
                    if (y0 - level) * (y1 - level) <= 0 and y0 != y1:
                        if ax[2] == "log":
                            t = (math.log10(level) - math.log10(y0)) / (math.log10(y1) - math.log10(y0))
                        else:
                            t = (level - y0) / (y1 - y0)
                        if xax[2] == "log":
                            xc = 10 ** (math.log10(x0) + t * (math.log10(x1) - math.log10(x0)))
                        else:
                            xc = x0 + t * (x1 - x0)
                        print(f"    crosses y={level:.4g} at x={xc:.4g}")


if __name__ == "__main__":
    main()
