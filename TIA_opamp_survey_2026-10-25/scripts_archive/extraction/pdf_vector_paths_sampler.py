"""Read curves that a datasheet draws as vector paths, as a cross-check on
reading the rendered figure by eye.

Sub-commands
------------
dump <pdf> <page> <clip> <out_json> [--min-items N]
    page : 1-based PDF page index (not the printed page number)
    clip : x0,y0,x1,y1 in PDF points (1/72 inch, y measured downward)
    Stores every drawing path whose bounding box intersects the clip in
    <out_json> (stroke colour, line width, bounding box, straight segments
    and ordered vertices in PDF points; cubic Bezier pieces are subdivided
    into short chords) and prints one summary line per path with at least N
    items (default 1).

grid <json> [--max-width W]
    Lists the x positions of vertical segments and the y positions of
    horizontal segments of all paths with line width <= W (default 0.7 pt),
    i.e. the frame and grid lines, to obtain axis calibration points.

colors <json>
    Lists the distinct (stroke colour, line width) pairs with the number of
    paths and the x/y extent of each, to identify the data curves.

sample <json> SELECTION --xcal p0:v0,p1:v1 --ycal p0:v0,p1:v1
       [--xlog] [--ylog] --at x1,x2,...
    Converts the selected paths to data coordinates with two-point
    calibrations (PDF point position : axis value; a log axis is
    interpolated in log10) and prints, for every requested x value, every y
    value at which a selected path crosses that x (linear interpolation
    within each segment of each path).  'none' = not drawn at that x.

xcross <json> SELECTION --xcal ... --ycal ... [--xlog] [--ylog] --at y1,y2,...
    The transpose of 'sample': prints every x at which a selected path
    crosses each requested y value (e.g. the -3 dB frequencies of a family
    of closed-loop responses drawn in one colour).

chain <json> <out_json> SELECTION [--tol 0.05] [--min-items 5]
    For plots drawn as many loose segments: links segments whose end points
    coincide (within --tol points) into continuous polylines and writes
    them as a new dump-format JSON (index = chain number, longest first),
    on which sample/xcross/table can then be run with --paths.

table <json> SELECTION --xcal ... --ycal ... [--xlog] [--ylog] [--every K]
    Prints the converted vertices (every K-th) of the selection.

SELECTION is any combination of
    --paths 12,15-40          path indices from the dump (ranges allowed)
    --color r,g,b [--ctol t]  stroke colour (0..1 components, tolerance t)
    --width w [--wtol t]      line width in points (tolerance t)
Paths must satisfy every criterion given.
"""
import argparse
import json
import math
import sys

import pymupdf


BEZIER_STEPS = 32  # chords per cubic Bezier segment


def _bezier(p0, p1, p2, p3, steps=BEZIER_STEPS):
    """Points along a cubic Bezier curve, including both end points."""
    out = []
    for k in range(steps + 1):
        t = k / steps
        a, b, c, d = (1 - t) ** 3, 3 * t * (1 - t) ** 2, 3 * t * t * (1 - t), t ** 3
        out.append((a * p0.x + b * p1.x + c * p2.x + d * p3.x,
                    a * p0.y + b * p1.y + c * p2.y + d * p3.y))
    return out


def _segments(path):
    """Straight segments of a path; cubic curves are subdivided finely."""
    segs = []
    for item in path["items"]:
        kind = item[0]
        if kind == "l":
            segs.append((item[1].x, item[1].y, item[2].x, item[2].y))
        elif kind == "c":
            pts = _bezier(item[1], item[2], item[3], item[4])
            segs += [(ax, ay, bx, by) for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:])]
        elif kind == "re":
            r = item[1]
            segs += [(r.x0, r.y0, r.x1, r.y0), (r.x1, r.y0, r.x1, r.y1),
                     (r.x1, r.y1, r.x0, r.y1), (r.x0, r.y1, r.x0, r.y0)]
        elif kind == "qu":
            q = item[1]
            corners = (q.ul, q.ur, q.lr, q.ll, q.ul)
            segs += [(a.x, a.y, b.x, b.y) for a, b in zip(corners[:-1], corners[1:])]
    return segs


def _vertices(path):
    """Ordered vertices of a path (end points of its straight segments)."""
    pts = []
    for ax, ay, bx, by in _segments(path):
        for x, y in ((ax, ay), (bx, by)):
            if not pts or abs(pts[-1][0] - x) > 1e-6 or abs(pts[-1][1] - y) > 1e-6:
                pts.append((x, y))
    return pts


def cmd_dump(args):
    doc = pymupdf.open(args.pdf)
    page = doc[args.page - 1]
    x0, y0, x1, y1 = (float(v) for v in args.clip.split(","))
    clip = pymupdf.Rect(x0, y0, x1, y1)
    out = []
    for idx, path in enumerate(page.get_drawings()):
        rect = path["rect"]
        if not rect.intersects(clip) and not (clip.contains(rect.tl) or clip.contains(rect.br)):
            continue
        color = path.get("color")
        fill = path.get("fill")
        rec = {
            "index": idx,
            "color": [round(c, 3) for c in color] if color else None,
            "fill": [round(c, 3) for c in fill] if fill else None,
            "width": path.get("width"),
            "rect": [round(rect.x0, 3), round(rect.y0, 3), round(rect.x1, 3), round(rect.y1, 3)],
            "n_items": len(path["items"]),
            "vertices": [[round(px, 4), round(py, 4)] for px, py in _vertices(path)],
            "segments": [[round(v, 4) for v in s] for s in _segments(path)],
        }
        out.append(rec)
        if rec["n_items"] >= args.min_items:
            print(f"#{idx:5d} items={rec['n_items']:4d} col={rec['color']} fill={rec['fill']} "
                  f"w={rec['width']} rect={rec['rect']}")
    with open(args.out_json, "w", encoding="utf-8") as fh:
        json.dump(out, fh)
    print(f"stored {len(out)} paths")


def _load_all(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def cmd_grid(args):
    xs, ys = set(), set()
    for rec in _load_all(args.json):
        if rec["width"] is None or rec["width"] > args.max_width:
            continue
        for ax, ay, bx, by in rec["segments"]:
            if abs(ax - bx) < 0.05 and abs(ay - by) > 1.0:
                xs.add(round((ax + bx) / 2, 2))
            if abs(ay - by) < 0.05 and abs(ax - bx) > 1.0:
                ys.add(round((ay + by) / 2, 2))
    print("vertical segments at x =", sorted(xs))
    print("horizontal segments at y =", sorted(ys))


def cmd_colors(args):
    groups = {}
    for rec in _load_all(args.json):
        key = (tuple(rec["color"]) if rec["color"] else None,
               round(rec["width"], 3) if rec["width"] else None)
        g = groups.setdefault(key, {"n": 0, "x0": 1e9, "y0": 1e9, "x1": -1e9, "y1": -1e9})
        g["n"] += 1
        x0, y0, x1, y1 = rec["rect"]
        g["x0"], g["y0"] = min(g["x0"], x0), min(g["y0"], y0)
        g["x1"], g["y1"] = max(g["x1"], x1), max(g["y1"], y1)
    for key, g in sorted(groups.items(), key=lambda kv: -kv[1]["n"]):
        print(f"color={key[0]} width={key[1]} paths={g['n']} "
              f"extent=[{g['x0']:.2f},{g['y0']:.2f},{g['x1']:.2f},{g['y1']:.2f}]")


def _parse_indices(spec):
    out = set()
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-")
            out.update(range(int(a), int(b) + 1))
        elif part:
            out.add(int(part))
    return out


def _select(args):
    recs = _load_all(args.json)
    idx = _parse_indices(args.paths) if args.paths else None
    col = [float(v) for v in args.color.split(",")] if args.color else None
    chosen = []
    for rec in recs:
        if idx is not None and rec["index"] not in idx:
            continue
        if col is not None:
            if rec["color"] is None or any(abs(a - b) > args.ctol for a, b in zip(rec["color"], col)):
                continue
        if args.width is not None:
            if rec["width"] is None or abs(rec["width"] - args.width) > args.wtol:
                continue
        chosen.append(rec)
    if not chosen:
        sys.exit("selection is empty")
    return chosen


def _cal(spec, log):
    (p0, v0), (p1, v1) = [tuple(float(t) for t in part.split(":")) for part in spec.split(",")]
    if log:
        v0, v1 = math.log10(v0), math.log10(v1)

    def to_value(p):
        v = v0 + (p - p0) * (v1 - v0) / (p1 - p0)
        return 10 ** v if log else v

    def to_point(v):
        if log:
            v = math.log10(v)
        return p0 + (v - v0) * (p1 - p0) / (v1 - v0)

    return to_value, to_point


def cmd_sample(args):
    recs = _select(args)
    _, xpt = _cal(args.xcal, args.xlog)
    yval, _ = _cal(args.ycal, args.ylog)
    for xq in (float(v) for v in args.at.split(",")):
        xp = xpt(xq)
        hits = []
        for rec in recs:
            for ax, ay, bx, by in rec["segments"]:
                lo, hi = min(ax, bx), max(ax, bx)
                if hi > lo and lo <= xp <= hi:
                    t = (xp - ax) / (bx - ax)
                    hits.append(yval(ay + t * (by - ay)))
        hits = sorted(set(round(h, 4) for h in hits))
        if hits:
            print(f"x={xq:.4g}: y = " + ", ".join(f"{h:.4g}" for h in hits))
        else:
            print(f"x={xq:.4g}: none")


def cmd_xcross(args):
    recs = _select(args)
    xval, _ = _cal(args.xcal, args.xlog)
    _, ypt = _cal(args.ycal, args.ylog)
    for yq in (float(v) for v in args.at.split(",")):
        yp = ypt(yq)
        hits = []
        for rec in recs:
            for ax, ay, bx, by in rec["segments"]:
                lo, hi = min(ay, by), max(ay, by)
                if hi > lo and lo <= yp <= hi:
                    t = (yp - ay) / (by - ay)
                    hits.append(xval(ax + t * (bx - ax)))
        hits = sorted(set(float(f"{h:.4g}") for h in hits))
        if hits:
            print(f"y={yq:.4g}: x = " + ", ".join(f"{h:.4g}" for h in hits))
        else:
            print(f"y={yq:.4g}: none")


def cmd_chain(args):
    """Join the segments of the selected paths into continuous polylines.

    Segments whose end points coincide within --tol points are linked; each
    resulting chain is written to <out_json> as one record (same format as
    a dump, index = chain number) so that sample/xcross/table can be run on
    it with --paths.
    """
    recs = _select(args)
    segs = [tuple(s) for rec in recs for s in rec["segments"]
            if abs(s[0] - s[2]) + abs(s[1] - s[3]) > 1e-9]

    def key(x, y):
        return (round(x / args.tol), round(y / args.tol))

    ends = {}
    for i, (ax, ay, bx, by) in enumerate(segs):
        ends.setdefault(key(ax, ay), []).append(i)
        ends.setdefault(key(bx, by), []).append(i)
    used = [False] * len(segs)

    def walk(start_pt, seg_i):
        pts = [start_pt]
        cur_i, cur_pt = seg_i, start_pt
        while True:
            used[cur_i] = True
            ax, ay, bx, by = segs[cur_i]
            nxt = (bx, by) if key(ax, ay) == key(*cur_pt) else (ax, ay)
            pts.append(nxt)
            cands = [j for j in ends[key(*nxt)] if not used[j]]
            if len(cands) != 1:
                return pts
            cur_i, cur_pt = cands[0], nxt

    chains = []
    # start from free ends first (degree-1 points), then any leftovers (loops)
    order = sorted(range(len(segs)), key=lambda i: min(len(ends[key(segs[i][0], segs[i][1])]),
                                                       len(ends[key(segs[i][2], segs[i][3])])))
    for i in order:
        if used[i]:
            continue
        ax, ay, bx, by = segs[i]
        start = (ax, ay) if len(ends[key(ax, ay)]) == 1 else (bx, by)
        chains.append(walk(start, i))
    out = []
    for n, pts in enumerate(sorted(chains, key=len, reverse=True)):
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        out.append({"index": n, "color": recs[0]["color"], "fill": None, "width": recs[0]["width"],
                    "rect": [min(xs), min(ys), max(xs), max(ys)], "n_items": len(pts) - 1,
                    "vertices": [list(p) for p in pts],
                    "segments": [[a[0], a[1], b[0], b[1]] for a, b in zip(pts[:-1], pts[1:])]})
        if len(pts) - 1 >= args.min_items:
            print(f"chain {n:4d}: {len(pts) - 1:5d} segments  x {min(xs):.2f}-{max(xs):.2f}  "
                  f"y {min(ys):.2f}-{max(ys):.2f}  start ({pts[0][0]:.2f},{pts[0][1]:.2f}) "
                  f"end ({pts[-1][0]:.2f},{pts[-1][1]:.2f})")
    with open(args.out_json, "w", encoding="utf-8") as fh:
        json.dump(out, fh)
    print(f"stored {len(out)} chains from {len(segs)} segments")


def cmd_table(args):
    recs = _select(args)
    xval, _ = _cal(args.xcal, args.xlog)
    yval, _ = _cal(args.ycal, args.ylog)
    pts = []
    for rec in recs:
        pts.extend(rec["vertices"])
    pts.sort(key=lambda p: p[0])
    for k, (px, py) in enumerate(pts):
        if k % args.every == 0 or k == len(pts) - 1:
            print(f"{xval(px):.5g}\t{yval(py):.5g}")


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("dump")
    p.add_argument("pdf")
    p.add_argument("page", type=int)
    p.add_argument("clip")
    p.add_argument("out_json")
    p.add_argument("--min-items", type=int, default=1)
    p.set_defaults(func=cmd_dump)

    p = sub.add_parser("grid")
    p.add_argument("json")
    p.add_argument("--max-width", type=float, default=0.7)
    p.set_defaults(func=cmd_grid)

    p = sub.add_parser("colors")
    p.add_argument("json")
    p.set_defaults(func=cmd_colors)

    p = sub.add_parser("chain")
    p.add_argument("json")
    p.add_argument("out_json")
    p.add_argument("--paths", default="")
    p.add_argument("--color", default="")
    p.add_argument("--ctol", type=float, default=0.02)
    p.add_argument("--width", type=float, default=None)
    p.add_argument("--wtol", type=float, default=0.02)
    p.add_argument("--tol", type=float, default=0.05)
    p.add_argument("--min-items", type=int, default=5)
    p.set_defaults(func=cmd_chain)

    for name, func in (("sample", cmd_sample), ("xcross", cmd_xcross), ("table", cmd_table)):
        p = sub.add_parser(name)
        p.add_argument("json")
        p.add_argument("--paths", default="")
        p.add_argument("--color", default="")
        p.add_argument("--ctol", type=float, default=0.02)
        p.add_argument("--width", type=float, default=None)
        p.add_argument("--wtol", type=float, default=0.02)
        p.add_argument("--xcal", required=True)
        p.add_argument("--ycal", required=True)
        p.add_argument("--xlog", action="store_true")
        p.add_argument("--ylog", action="store_true")
        if name in ("sample", "xcross"):
            p.add_argument("--at", required=True)
        else:
            p.add_argument("--every", type=int, default=1)
        p.set_defaults(func=func)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
