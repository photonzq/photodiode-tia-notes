"""Digitize curves drawn as vector paths in a PDF datasheet plot.

Many datasheet plots are stored as vector line art, so a curve can be read
from the path coordinates instead of from a raster image.  This helper has
two sub-commands.

dump
    python pdf_vector_curves.py dump <pdf> <page> <x0,y0,x1,y1> <out.json>
        [--min-points 2]

    Lists every stroked path whose bounding box intersects the clip
    rectangle (PDF points, page 1-based), with its line width, dash pattern,
    colour and bounding box, plus the text spans inside the clip (useful for
    locating tick labels).  Straight horizontal or vertical two-point lines
    are reported separately as grid/axis candidates.  Full point lists are
    written to <out.json>.

sample
    python pdf_vector_curves.py sample <paths.json> --ids 3,4
        --xcal X1:V1,X2:V2 [--xlog] --ycal Y1:V1,Y2:V2 [--ylog]
        --at v1,v2,...

    Converts the points of the chosen paths (ids from the dump listing,
    several ids are concatenated into one curve) to data units using two
    reference positions per axis (page coordinate : data value), and
    linearly interpolates the curve at the requested x values (in log10 x
    if --xlog).  Values outside the curve's x range are reported as None.
    The curve's data-space end points are printed as well.  Negative
    numbers must be passed in the --opt=value form (e.g. --at=-40,25).

The page coordinate system is PyMuPDF's: origin top-left, y downwards,
units of 1/72 inch.  Calibrate against gridlines (from the dump listing)
rather than the plot frame, which can be offset by about 0.5 pt.  Always
confirm curve identity against a rendered image of the same plot.
"""
import argparse
import json
import math
import sys

import pymupdf


def bezier_points(p0, p1, p2, p3, n=8):
    """Sample a cubic Bezier segment at n+1 points (end points included)."""
    out = []
    for k in range(n + 1):
        t = k / n
        a = (1 - t) ** 3
        b = 3 * (1 - t) ** 2 * t
        c = 3 * (1 - t) * t ** 2
        d = t ** 3
        out.append((a * p0.x + b * p1.x + c * p2.x + d * p3.x,
                    a * p0.y + b * p1.y + c * p2.y + d * p3.y))
    return out


def flatten(drawing):
    """Return the drawing's items as one list of (x, y) points per sub-path."""
    subpaths = []
    current = []
    last = None
    for item in drawing["items"]:
        kind = item[0]
        if kind == "l":
            p, q = item[1], item[2]
            if last is None or abs(last[0] - p.x) > 1e-3 or abs(last[1] - p.y) > 1e-3:
                if current:
                    subpaths.append(current)
                current = [(p.x, p.y)]
            current.append((q.x, q.y))
            last = (q.x, q.y)
        elif kind == "c":
            pts = bezier_points(item[1], item[2], item[3], item[4])
            if last is None or abs(last[0] - pts[0][0]) > 1e-3 or abs(last[1] - pts[0][1]) > 1e-3:
                if current:
                    subpaths.append(current)
                current = [pts[0]]
            current.extend(pts[1:])
            last = pts[-1]
        elif kind == "re":
            r = item[1]
            if current:
                subpaths.append(current)
                current = []
            subpaths.append([(r.x0, r.y0), (r.x1, r.y0), (r.x1, r.y1), (r.x0, r.y1), (r.x0, r.y0)])
            last = None
        elif kind == "qu":
            qd = item[1]
            if current:
                subpaths.append(current)
                current = []
            subpaths.append([(qd.ul.x, qd.ul.y), (qd.ur.x, qd.ur.y), (qd.lr.x, qd.lr.y),
                             (qd.ll.x, qd.ll.y), (qd.ul.x, qd.ul.y)])
            last = None
    if current:
        subpaths.append(current)
    return subpaths


def cmd_dump(args):
    doc = pymupdf.open(args.pdf)
    page = doc[args.page - 1]
    x0, y0, x1, y1 = (float(v) for v in args.clip.split(","))
    clip = pymupdf.Rect(x0, y0, x1, y1)
    records = []
    grid = []
    for drawing in page.get_drawings():
        rect = drawing["rect"]
        if not rect.intersects(clip) and not (clip.contains(rect.tl) or clip.contains(rect.br)):
            continue
        for sub in flatten(drawing):
            xs = [p[0] for p in sub]
            ys = [p[1] for p in sub]
            if max(xs) < x0 or min(xs) > x1 or max(ys) < y0 or min(ys) > y1:
                continue
            rec = {
                "id": len(records),
                "seqno": drawing.get("seqno"),
                "type": drawing.get("type"),
                "width": drawing.get("width"),
                "dashes": drawing.get("dashes"),
                "color": drawing.get("color"),
                "fill": drawing.get("fill"),
                "n": len(sub),
                "bbox": [round(min(xs), 2), round(min(ys), 2), round(max(xs), 2), round(max(ys), 2)],
                "points": [[round(p[0], 3), round(p[1], 3)] for p in sub],
            }
            records.append(rec)
            if len(sub) == 2:
                if abs(sub[0][0] - sub[1][0]) < 0.05:
                    grid.append(("V", round(sub[0][0], 2), rec["id"], rec["width"]))
                elif abs(sub[0][1] - sub[1][1]) < 0.05:
                    grid.append(("H", round(sub[0][1], 2), rec["id"], rec["width"]))
    spans = []
    for block in page.get_text("dict", clip=clip)["blocks"]:
        for line in block.get("lines", []):
            for span in line["spans"]:
                text = span["text"].strip()
                if text:
                    b = span["bbox"]
                    spans.append({"text": text, "bbox": [round(v, 2) for v in b],
                                  "cx": round((b[0] + b[2]) / 2, 2), "cy": round((b[1] + b[3]) / 2, 2)})
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump({"pdf_page": args.page, "clip": [x0, y0, x1, y1], "paths": records, "text": spans}, fh, indent=1)
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("paths with >= %d points:" % args.min_points)
    for rec in records:
        if rec["n"] >= args.min_points and not (rec["n"] == 2 and any(g[2] == rec["id"] for g in grid)):
            print(f"  id={rec['id']:4d} seq={rec['seqno']} w={rec['width']} dash={rec['dashes']} "
                  f"col={rec['color']} fill={rec['fill']} n={rec['n']} bbox={rec['bbox']}")
    print("straight grid/axis candidates (orientation, position, id, width):")
    for g in sorted(grid):
        print("  ", g)
    print("text spans:")
    for s in spans:
        print(f"   '{s['text']}' cx={s['cx']} cy={s['cy']}")


def parse_cal(spec):
    pairs = []
    for part in spec.split(","):
        pos, val = part.split(":")
        pairs.append((float(pos), float(val)))
    return pairs


def make_map(cal, log):
    (p1, v1), (p2, v2) = cal
    if log:
        v1, v2 = math.log10(v1), math.log10(v2)
    slope = (v2 - v1) / (p2 - p1)

    def to_data(p):
        v = v1 + (p - p1) * slope
        return 10 ** v if log else v

    return to_data


def cmd_sample(args):
    with open(args.paths, encoding="utf-8") as fh:
        data = json.load(fh)
    by_id = {rec["id"]: rec for rec in data["paths"]}
    fx = make_map(parse_cal(args.xcal), args.xlog)
    fy = make_map(parse_cal(args.ycal), args.ylog)
    pts = []
    for i in (int(v) for v in args.ids.split(",")):
        pts.extend(by_id[i]["points"])
    curve = sorted((fx(x), fy(y)) for x, y in pts)
    print(f"curve x-range {curve[0][0]:.4g} .. {curve[-1][0]:.4g};  y at ends {curve[0][1]:.4g}, {curve[-1][1]:.4g}")
    ylo = min(c[1] for c in curve)
    yhi = max(c[1] for c in curve)
    print(f"curve y-range {ylo:.4g} .. {yhi:.4g}")
    tx = (lambda v: math.log10(v)) if args.xlog else (lambda v: v)
    for target in (float(v) for v in args.at.split(",")):
        t = tx(target)
        val = None
        for (xa, ya), (xb, yb) in zip(curve, curve[1:]):
            ta, tb = tx(xa), tx(xb)
            if ta <= t <= tb:
                val = ya if tb == ta else ya + (yb - ya) * (t - ta) / (tb - ta)
                break
        print(f"  x={target:.4g}  y={'None' if val is None else format(val, '.4g')}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("dump")
    d.add_argument("pdf")
    d.add_argument("page", type=int)
    d.add_argument("clip")
    d.add_argument("out")
    d.add_argument("--min-points", type=int, default=2)
    s = sub.add_parser("sample")
    s.add_argument("paths")
    s.add_argument("--ids", required=True)
    s.add_argument("--xcal", required=True)
    s.add_argument("--xlog", action="store_true")
    s.add_argument("--ycal", required=True)
    s.add_argument("--ylog", action="store_true")
    s.add_argument("--at", required=True)
    args = parser.parse_args()
    if args.cmd == "dump":
        cmd_dump(args)
    else:
        cmd_sample(args)


if __name__ == "__main__":
    main()
