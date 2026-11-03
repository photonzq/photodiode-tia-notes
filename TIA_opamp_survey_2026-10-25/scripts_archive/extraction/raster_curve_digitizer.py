"""Read curve values off a rendered datasheet plot (PNG) by pixel colour.

Intended for typical-characteristic plots rendered from a PDF at 300 dpi or
more.  Every path is given on the command line.

Modes
-----
lines <png> --box x0,y0,x1,y1 [--dark 110] [--gray 235] [--frac 0.6]
    List image columns and rows inside the box that are covered by long
    straight lines (frame edges are dark, gridlines are light gray).  Use the
    printed pixel positions of gridlines with known values to calibrate.

trace <png> --xcal p1:v1,p2:v2 --ycal q1:w1,q2:w2 [--xlog] [--ylog]
      --color r,g,b [--tol 80] --at v,v,... [--band 1] [--box x0,y0,x1,y1]
    For each requested x value, find pixels whose colour lies within --tol
    (Euclidean RGB distance) of --color in the matching column (+/- band
    columns), group them into vertical runs, and print the y value of the
    centre of each run plus the run extent, so steep or overlapping parts of
    a curve are visible.  --xcal / --ycal give two (pixel:value) pairs per
    axis, normally two gridlines; --xlog / --ylog map the axis in log10.

sweep <png> (same calibration and colour options) --from v --to v --n N
    Print the curve centre at N points spaced evenly (log or linear) between
    two x values.  Useful for locating minima, maxima and crossings.

colors <png> --box x0,y0,x1,y1 [--n 8]
    List the most frequent saturated or near-black colours inside the box,
    to identify the RGB value of each curve.

column <png> --col c [--rows r0,r1] [--maxval 230]
    Print every pixel down one image column whose darkest channel is below
    --maxval (shows curve, gridline and legend pixels with their colours).

pulse <png> --frame x0,y0,x1,y1 --xspan T --yspan V --base a,b --top a,b
      --split c [--dark 60] [--exclude x0,y0,x1,y1]
    Pulse-response edges: the frame spans T time units horizontally and V
    amplitude units vertically; the near-black trace (all channels within
    --dark of black) is followed column by column; the baseline and the
    flat top are medians over the column ranges --base and --top; rising
    crossings are searched left of column --split and falling ones right of
    it.  Prints amplitude, 10-90 % rise, 90-10 % fall, 50 % width and the
    largest excursions beyond the top and below the baseline.

Readings are only as good as the calibration; check them against
gridlines in the rendered image.
"""
import argparse
import math

import numpy as np
from PIL import Image


def load(png):
    img = Image.open(png).convert("RGB")
    return np.asarray(img).astype(int)


def parse_pairs(spec):
    pairs = []
    for part in spec.split(","):
        p, v = part.split(":")
        pairs.append((float(p), float(v)))
    return pairs


def make_map(pairs, log):
    (p1, v1), (p2, v2) = pairs
    if log:
        v1, v2 = math.log10(v1), math.log10(v2)

    def to_pix(v):
        vv = math.log10(v) if log else v
        return p1 + (vv - v1) * (p2 - p1) / (v2 - v1)

    def to_val(p):
        vv = v1 + (p - p1) * (v2 - v1) / (p2 - p1)
        return 10 ** vv if log else vv

    return to_pix, to_val


def runs(rows):
    if len(rows) == 0:
        return []
    out = []
    start = prev = rows[0]
    for r in rows[1:]:
        if r != prev + 1:
            out.append((start, prev))
            start = r
        prev = r
    out.append((start, prev))
    return out


def column_hits(arr, col, color, tol, band, box):
    h, w, _ = arr.shape
    y0, y1 = 0, h - 1
    if box is not None:
        y0, y1 = int(box[1]), int(box[3])
    hits = set()
    for c in range(col - band, col + band + 1):
        if c < 0 or c >= w:
            continue
        seg = arr[y0:y1 + 1, c, :]
        d = np.sqrt(((seg - np.array(color)) ** 2).sum(axis=1))
        for r in np.nonzero(d <= tol)[0]:
            hits.add(int(r) + y0)
    return runs(sorted(hits))


def cmd_lines(a):
    arr = load(a.png)
    x0, y0, x1, y1 = (int(float(v)) for v in a.box.split(","))
    sub = arr[y0:y1 + 1, x0:x1 + 1, :]
    mx = sub.max(axis=2)
    mn = sub.min(axis=2)
    dark = mx <= a.dark
    gray = (mn >= 120) & (mx <= a.gray) & ((mx - mn) <= 20) & (~dark)
    hgt, wid = dark.shape
    for name, mask in (("dark", dark), ("gray", gray)):
        colfrac = mask.sum(axis=0) / hgt
        rowfrac = mask.sum(axis=1) / wid
        cols = [i + x0 for i in np.nonzero(colfrac >= a.frac)[0]]
        rows = [i + y0 for i in np.nonzero(rowfrac >= a.frac)[0]]
        print(f"{name} columns (frac>={a.frac}): {group_print(cols)}")
        print(f"{name} rows    (frac>={a.frac}): {group_print(rows)}")


def group_print(idx):
    if not idx:
        return "none"
    parts = []
    for s, e in runs(list(idx)):
        parts.append(f"{(s + e) / 2:.1f}" + (f"[{s}-{e}]" if e > s else ""))
    return " ".join(parts)


def setup_maps(a):
    xp, xv = make_map(parse_pairs(a.xcal), a.xlog)
    yp, yv = make_map(parse_pairs(a.ycal), a.ylog)
    color = tuple(int(v) for v in a.color.split(","))
    box = None
    if a.box:
        box = tuple(float(v) for v in a.box.split(","))
    return xp, xv, yp, yv, color, box


def report(arr, xval, xp, yv, color, tol, band, box, offset=0, minrun=1):
    """Curve value at xval.

    With offset > 0 the columns col-offset and col+offset are sampled
    instead of col itself (this steps off a gridline drawn exactly at col)
    and, when each side shows exactly one run, the two centres are averaged.
    Runs shorter than minrun pixels (gridline crossings) are ignored.
    """
    col = int(round(xp(xval)))
    cols = [col] if offset <= 0 else [col - offset, col + offset]
    per_col = []
    for c in cols:
        rr = [r for r in column_hits(arr, c, color, tol, band, box)
              if r[1] - r[0] + 1 >= minrun]
        per_col.append((c, rr))
    if all(not rr for _, rr in per_col):
        return f"x={xval:.6g} col={col}: no pixels of that colour"
    items = []
    for c, rr in per_col:
        for s, e in rr:
            cc = (s + e) / 2
            items.append(f"[c{c}] y={yv(cc):.4g} (rows {s}-{e}: {yv(e):.4g}..{yv(s):.4g})")
    tail = ""
    if offset > 0 and all(len(rr) == 1 for _, rr in per_col):
        centres = [(rr[0][0] + rr[0][1]) / 2 for _, rr in per_col]
        tail = f"  => mean y={yv(sum(centres) / 2):.4g}"
    return f"x={xval:.6g} col={col}: " + " | ".join(items) + tail


def cmd_trace(a):
    arr = load(a.png)
    xp, xv, yp, yv, color, box = setup_maps(a)
    for v in a.at.split(","):
        print(report(arr, float(v), xp, yv, color, a.tol, a.band, box,
                     a.offset, a.minrun))


def cmd_sweep(a):
    arr = load(a.png)
    xp, xv, yp, yv, color, box = setup_maps(a)
    lo, hi = float(a.frm), float(a.to)
    for i in range(a.n):
        t = i / (a.n - 1)
        if a.xlog:
            v = 10 ** (math.log10(lo) + t * (math.log10(hi) - math.log10(lo)))
        else:
            v = lo + t * (hi - lo)
        print(report(arr, v, xp, yv, color, a.tol, a.band, box,
                     a.offset, a.minrun))


def cmd_colors(a):
    arr = load(a.png)
    x0, y0, x1, y1 = (int(float(v)) for v in a.box.split(","))
    sub = arr[y0:y1 + 1, x0:x1 + 1, :].reshape(-1, 3)
    mx = sub.max(axis=1)
    mn = sub.min(axis=1)
    pick = sub[((mx - mn) > 40) | (mx < 60)]
    if len(pick) == 0:
        print("no saturated or near-black pixels")
        return
    vals, counts = np.unique(pick, axis=0, return_counts=True)
    for i in np.argsort(-counts)[:a.n]:
        print(tuple(int(v) for v in vals[i]), int(counts[i]))


def cmd_column(a):
    arr = load(a.png)
    h = arr.shape[0]
    r0, r1 = 0, h - 1
    if a.rows:
        r0, r1 = (int(v) for v in a.rows.split(","))
    for r in range(r0, r1 + 1):
        p = arr[r, a.col, :]
        if p.min() < a.maxval:
            print(r, tuple(int(v) for v in p))


def cmd_pulse(a):
    arr = load(a.png)
    fx0, fy0, fx1, fy1 = (float(v) for v in a.frame.split(","))
    t_per_px = a.xspan / (fx1 - fx0)
    v_per_px = a.yspan / (fy1 - fy0)
    ex = None
    if a.exclude:
        ex = tuple(float(v) for v in a.exclude.split(","))
    trace = []
    for c in range(int(fx0) + 6, int(fx1) - 5):
        col = arr[int(fy0) + 6:int(fy1) - 5, c, :]
        d = np.sqrt((col ** 2).sum(axis=1))
        rows = np.nonzero(d <= a.dark)[0] + int(fy0) + 6
        if ex is not None and ex[0] <= c <= ex[2]:
            rows = rows[(rows < ex[1]) | (rows > ex[3])]
        if len(rows) == 0:
            continue
        rr = runs(list(int(r) for r in rows))
        s, e = max(rr, key=lambda t: t[1] - t[0])
        trace.append((c, (s + e) / 2))
    b0, b1 = (int(v) for v in a.base.split(","))
    t0, t1 = (int(v) for v in a.top.split(","))
    base = float(np.median([r for c, r in trace if b0 <= c <= b1]))
    top = float(np.median([r for c, r in trace if t0 <= c <= t1]))
    amp = base - top

    def cross(level, rising):
        target = base - level * amp
        prev = None
        for c, r in trace:
            if prev is not None:
                pc, pr = prev
                if rising and c < a.split and pr > target >= r:
                    return pc + (pr - target) / (pr - r) * (c - pc)
                if (not rising) and c > a.split and pr < target <= r:
                    return pc + (target - pr) / (r - pr) * (c - pc)
            prev = (c, r)
        return None

    r10, r50, r90 = cross(0.1, True), cross(0.5, True), cross(0.9, True)
    f90, f50, f10 = cross(0.9, False), cross(0.5, False), cross(0.1, False)
    print(f"baseline row {base:.1f}, top row {top:.1f}, amplitude {amp * v_per_px:.4g}")
    if None not in (r10, r90):
        print(f"rise 10-90 %: {(r90 - r10) * t_per_px:.3g}")
    if None not in (f90, f10):
        print(f"fall 90-10 %: {(f10 - f90) * t_per_px:.3g}")
    if None not in (r50, f50):
        print(f"50 % width: {(f50 - r50) * t_per_px:.3g}")
        print(f"50 % rise at {(r50 - fx0) * t_per_px:.3g}, 50 % fall at {(f50 - fx0) * t_per_px:.3g} (from frame left)")
    inside = [r for c, r in trace if r50 is not None and f50 is not None and r50 < c < f50]
    if inside:
        print(f"largest excursion above flat top: {(top - min(inside)) * v_per_px:.3g}")
    after = [r for c, r in trace if f10 is not None and c > f10]
    if after:
        print(f"largest excursion below baseline after the fall: {(max(after) - base) * v_per_px:.3g}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="mode", required=True)

    p = sub.add_parser("colors")
    p.add_argument("png")
    p.add_argument("--box", required=True)
    p.add_argument("--n", type=int, default=8)
    p.set_defaults(func=cmd_colors)

    p = sub.add_parser("column")
    p.add_argument("png")
    p.add_argument("--col", type=int, required=True)
    p.add_argument("--rows", default="")
    p.add_argument("--maxval", type=int, default=230)
    p.set_defaults(func=cmd_column)

    p = sub.add_parser("pulse")
    p.add_argument("png")
    p.add_argument("--frame", required=True)
    p.add_argument("--xspan", type=float, required=True)
    p.add_argument("--yspan", type=float, required=True)
    p.add_argument("--base", required=True)
    p.add_argument("--top", required=True)
    p.add_argument("--split", type=int, required=True)
    p.add_argument("--dark", type=float, default=60)
    p.add_argument("--exclude", default="")
    p.set_defaults(func=cmd_pulse)

    p = sub.add_parser("lines")
    p.add_argument("png")
    p.add_argument("--box", required=True)
    p.add_argument("--dark", type=int, default=110)
    p.add_argument("--gray", type=int, default=235)
    p.add_argument("--frac", type=float, default=0.6)
    p.set_defaults(func=cmd_lines)

    for name, func in (("trace", cmd_trace), ("sweep", cmd_sweep)):
        p = sub.add_parser(name)
        p.add_argument("png")
        p.add_argument("--xcal", required=True)
        p.add_argument("--ycal", required=True)
        p.add_argument("--xlog", action="store_true")
        p.add_argument("--ylog", action="store_true")
        p.add_argument("--color", required=True)
        p.add_argument("--tol", type=float, default=80)
        p.add_argument("--band", type=int, default=0)
        p.add_argument("--box", default="")
        p.add_argument("--offset", type=int, default=0)
        p.add_argument("--minrun", type=int, default=1)
        if name == "trace":
            p.add_argument("--at", required=True)
        else:
            p.add_argument("--from", dest="frm", required=True)
            p.add_argument("--to", required=True)
            p.add_argument("--n", type=int, default=21)
        p.set_defaults(func=func)

    a = ap.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
