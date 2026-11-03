"""Read curve data from vector (path-drawn) plots in a PDF page.

Many datasheet plots are drawn as vector paths, so the plotted curve can be
sampled directly from the page drawing instead of being read by eye.  This is
a cross-check for visual readings of rendered figures, not a replacement: the
axis calibration (frame position and end-of-axis values) must be confirmed on
the rendered image.

Sub-commands
------------
dump    List every drawing that intersects a clip rectangle (PDF points):
        stroke colour, line width, bounding box and number of segments.
        python vector_curve_reader.py dump <pdf> <page> <x0,y0,x1,y1>

sample  Sample one drawn curve at requested x values.
        python vector_curve_reader.py sample <pdf> <page> <x0,y0,x1,y1>
            --index N            (drawing index printed by 'dump')
            --frame X0,Y0,X1,Y1  (plot frame in PDF points: left, top,
                                  right, bottom edges of the axis box)
            or --frame-index M   (use the rectangle of drawing M, the axis
                                  box, as the frame)
            --xrange XL,XR       (data values at the left and right edges)
            --yrange YB,YT       (data values at the bottom and top edges)
            [--xlog] [--ylog]
            --at v1,v2,...       (x values to sample)

vertices  Same arguments as 'sample' without --at: print every drawn vertex
          of the curve in data units (x, y).

cross     Same arguments as 'sample' without --at, plus --level L: print the
          curve maximum and every x at which the curve crosses y = L
          (for example the -3 dB frequency of a normalised response).

Page numbers are 1-based PDF page indices.  Curves are linearly interpolated
between drawn vertices in the plot's own (log or linear) coordinates; Bezier
segments are approximated by their end points.

Calibration note: in the plots checked so far the axis-end tick labels are
centred on the stroke centre-line of the axis-box rectangle, while curves are
pre-clipped half a line width inside it.  Use the box rectangle itself as the
frame, and confirm against tick-label positions on the rendered image.
"""
import argparse
import math

import pymupdf


def load_drawings(pdf: str, page_no: int, clip_spec: str):
    doc = pymupdf.open(pdf)
    page = doc[page_no - 1]
    clip = pymupdf.Rect(*(float(v) for v in clip_spec.split(",")))
    drawings = [d for d in page.get_drawings() if pymupdf.Rect(d["rect"]).intersects(clip)]
    return drawings


def vertices(drawing) -> list[tuple[float, float]]:
    pts: list[tuple[float, float]] = []
    for item in drawing["items"]:
        kind = item[0]
        if kind == "l":
            p0, p1 = item[1], item[2]
            seq = [p0, p1]
        elif kind == "c":
            seq = [item[1], item[4]]
        elif kind == "re":
            r = item[1]
            seq = [r.tl, r.tr, r.br, r.bl]
        elif kind == "qu":
            q = item[1]
            seq = [q.ul, q.ur, q.lr, q.ll]
        else:
            continue
        for p in seq:
            xy = (round(p.x, 4), round(p.y, 4))
            if not pts or pts[-1] != xy:
                pts.append(xy)
    return pts


def cmd_dump(args) -> None:
    drawings = load_drawings(args.pdf, args.page, args.clip)
    for i, d in enumerate(drawings):
        col = d.get("color")
        col = tuple(round(c, 3) for c in col) if col else None
        fill = d.get("fill")
        fill = tuple(round(c, 3) for c in fill) if fill else None
        r = d["rect"]
        print(f"[{i:3d}] n={len(d['items']):4d} color={col} fill={fill} "
              f"width={d.get('width')} rect=({r.x0:.2f},{r.y0:.2f},{r.x1:.2f},{r.y1:.2f}) "
              f"dashes={d.get('dashes')}")


def to_unit(v: float, lo: float, hi: float, log: bool) -> float:
    if log:
        return (math.log10(v) - math.log10(lo)) / (math.log10(hi) - math.log10(lo))
    return (v - lo) / (hi - lo)


def from_unit(u: float, lo: float, hi: float, log: bool) -> float:
    if log:
        return 10 ** (math.log10(lo) + u * (math.log10(hi) - math.log10(lo)))
    return lo + u * (hi - lo)


def cmd_sample(args) -> None:
    drawings = load_drawings(args.pdf, args.page, args.clip)
    pts = vertices(drawings[args.index])
    if args.frame_index is not None:
        r = drawings[args.frame_index]["rect"]
        fx0, fy0, fx1, fy1 = r.x0, r.y0, r.x1, r.y1
    else:
        fx0, fy0, fx1, fy1 = (float(v) for v in args.frame.split(","))
    print(f"frame used: ({fx0:.4f},{fy0:.4f},{fx1:.4f},{fy1:.4f})")
    xl, xr = (float(v) for v in args.xrange.split(","))
    yb, yt = (float(v) for v in args.yrange.split(","))
    # Convert vertices to unit plot coordinates (u along x, w along y upward).
    uw = [((x - fx0) / (fx1 - fx0), (fy1 - y) / (fy1 - fy0)) for x, y in pts]
    print(f"curve has {len(uw)} vertices; x-span in data units: "
          f"{from_unit(min(u for u, _ in uw), xl, xr, args.xlog):.4g} .. "
          f"{from_unit(max(u for u, _ in uw), xl, xr, args.xlog):.4g}")
    for xv in (float(v) for v in args.at.split(",")):
        u = to_unit(xv, xl, xr, args.xlog)
        hits = []
        for (u0, w0), (u1, w1) in zip(uw, uw[1:]):
            if (u0 - u) * (u1 - u) <= 0 and u0 != u1:
                t = (u - u0) / (u1 - u0)
                hits.append(w0 + t * (w1 - w0))
        if not hits:
            print(f"x={xv:.4g}: outside drawn curve")
            continue
        vals = ", ".join(f"{from_unit(w, yb, yt, args.ylog):.4g}" for w in hits)
        print(f"x={xv:.4g}: y={vals}")


def curve_data(args):
    """Return the selected curve as a list of (x, y) data-unit pairs."""
    drawings = load_drawings(args.pdf, args.page, args.clip)
    pts = vertices(drawings[args.index])
    if args.frame_index is not None:
        r = drawings[args.frame_index]["rect"]
        fx0, fy0, fx1, fy1 = r.x0, r.y0, r.x1, r.y1
    else:
        fx0, fy0, fx1, fy1 = (float(v) for v in args.frame.split(","))
    xl, xr = (float(v) for v in args.xrange.split(","))
    yb, yt = (float(v) for v in args.yrange.split(","))
    data = []
    for x, y in pts:
        u = (x - fx0) / (fx1 - fx0)
        w = (fy1 - y) / (fy1 - fy0)
        data.append((from_unit(u, xl, xr, args.xlog), from_unit(w, yb, yt, args.ylog)))
    return data


def cmd_vertices(args) -> None:
    """Print every drawn vertex of the curve in data units."""
    for x, y in curve_data(args):
        print(f"{x:.5g}\t{y:.5g}")


def cmd_cross(args) -> None:
    """Print every x at which the curve crosses the level y = args.level."""
    data = curve_data(args)
    level = args.level
    ymax = max(data, key=lambda t: t[1])
    print(f"curve maximum: y={ymax[1]:.4g} at x={ymax[0]:.4g}")
    for (x0, y0), (x1, y1) in zip(data, data[1:]):
        if (y0 - level) * (y1 - level) <= 0 and y0 != y1:
            t = (level - y0) / (y1 - y0)
            if args.xlog:
                xc = 10 ** (math.log10(x0) + t * (math.log10(x1) - math.log10(x0)))
            else:
                xc = x0 + t * (x1 - x0)
            direction = "falling" if y1 < y0 else "rising"
            print(f"crosses y={level:g} ({direction}) at x={xc:.4g}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_dump = sub.add_parser("dump")
    p_dump.add_argument("pdf")
    p_dump.add_argument("page", type=int)
    p_dump.add_argument("clip")
    p_dump.set_defaults(func=cmd_dump)
    p_s = sub.add_parser("sample")
    p_s.add_argument("pdf")
    p_s.add_argument("page", type=int)
    p_s.add_argument("clip")
    p_s.add_argument("--index", type=int, required=True)
    p_s.add_argument("--frame", default="")
    p_s.add_argument("--frame-index", type=int, default=None,
                     help="use the rectangle of this drawing (the axis box) as the frame")
    p_s.add_argument("--xrange", required=True)
    p_s.add_argument("--yrange", required=True)
    p_s.add_argument("--xlog", action="store_true")
    p_s.add_argument("--ylog", action="store_true")
    p_s.add_argument("--at", required=True)
    p_s.set_defaults(func=cmd_sample)
    for name, func, helptext in (("vertices", cmd_vertices, "print all curve vertices in data units"),
                                 ("cross", cmd_cross, "find where the curve crosses --level")):
        p = sub.add_parser(name, help=helptext)
        p.add_argument("pdf")
        p.add_argument("page", type=int)
        p.add_argument("clip")
        p.add_argument("--index", type=int, required=True)
        p.add_argument("--frame", default="")
        p.add_argument("--frame-index", type=int, default=None)
        p.add_argument("--xrange", required=True)
        p.add_argument("--yrange", required=True)
        p.add_argument("--xlog", action="store_true")
        p.add_argument("--ylog", action="store_true")
        if name == "cross":
            p.add_argument("--level", type=float, required=True)
        p.set_defaults(func=func)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
