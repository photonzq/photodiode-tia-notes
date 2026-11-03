"""Read curve values off a rendered datasheet plot (PNG) by pixel colour.

The axes are calibrated by the user from two known gridlines per axis; the
script then converts the pixel rows of a coloured curve into data values.
It is an aid for reading plots against their gridlines, not a substitute
for looking at the plot: always check the result against the image.

Subcommands
-----------
frame <png> [--xbox X0,X1] [--ybox Y0,Y1] [--dark 110] [--min-frac 0.6]
    List pixel rows and columns that are mostly dark inside the box (axis
    frame and major gridlines), to locate calibration lines.

probe <png> --px X --ybox Y0,Y1
    Print the RGB colour of each non-white pixel in one pixel column,
    to choose the --rgb value of a curve.

trace <png> --xcal PX1,V1,PX2,V2[,log] --ycal PY1,V1,PY2,V2[,log]
      --rgb R,G,B [--tol 70] --x V [V ...] [--xbox X0,X1] [--ybox Y0,Y1]
      [--band 1] [--skip-grid]
    For each requested x value, find the pixels of the given colour in a
    narrow column band and print every contiguous run of matching rows
    with its centre converted to a y value.  --skip-grid ignores rows and
    columns that are mostly dark (gridlines), useful for black curves.

cross <png> --xcal ... --ycal ... --rgb R,G,B [--tol 70] --y V [V ...]
      [--xbox X0,X1] [--ybox Y0,Y1] [--skip-grid]
    Scan the columns left to right, take the centre row of the matching
    pixels in each column, and print every x value at which that centre
    crosses each requested y value (linear interpolation between columns).
    Useful for edge timing on transient plots and for -3 dB frequencies.

Pixel coordinates are those of the PNG itself (x to the right, y down).
"""
import argparse
import math

import numpy as np
from PIL import Image


def load(path):
    img = Image.open(path).convert("RGB")
    return np.asarray(img).astype(int)


def parse_box(spec, limit):
    if not spec:
        return 0, limit - 1
    a, b = (int(float(v)) for v in spec.split(","))
    return max(0, a), min(limit - 1, b)


def parse_cal(spec):
    parts = spec.split(",")
    p1, v1, p2, v2 = (float(v) for v in parts[:4])
    is_log = len(parts) > 4 and parts[4].strip().lower() == "log"
    return p1, v1, p2, v2, is_log


def value_to_pixel(value, cal):
    p1, v1, p2, v2, is_log = cal
    if is_log:
        t = (math.log10(value) - math.log10(v1)) / (math.log10(v2) - math.log10(v1))
    else:
        t = (value - v1) / (v2 - v1)
    return p1 + t * (p2 - p1)


def pixel_to_value(pixel, cal):
    p1, v1, p2, v2, is_log = cal
    t = (pixel - p1) / (p2 - p1)
    if is_log:
        return 10 ** (math.log10(v1) + t * (math.log10(v2) - math.log10(v1)))
    return v1 + t * (v2 - v1)


def dark_mask(arr, dark):
    return arr.max(axis=2) < dark


def cmd_frame(args):
    arr = load(args.png)
    h, w, _ = arr.shape
    x0, x1 = parse_box(args.xbox, w)
    y0, y1 = parse_box(args.ybox, h)
    mask = dark_mask(arr, args.dark)[y0:y1 + 1, x0:x1 + 1]
    row_frac = mask.mean(axis=1)
    col_frac = mask.mean(axis=0)
    print(f"image {w}x{h}")
    print("rows (y, dark fraction):",
          [(y0 + i, round(float(f), 2)) for i, f in enumerate(row_frac) if f >= args.min_frac])
    print("cols (x, dark fraction):",
          [(x0 + i, round(float(f), 2)) for i, f in enumerate(col_frac) if f >= args.min_frac])


def cmd_probe(args):
    arr = load(args.png)
    h, _, _ = arr.shape
    y0, y1 = parse_box(args.ybox, h)
    for y in range(y0, y1 + 1):
        r, g, b = arr[y, args.px]
        if min(r, g, b) < 235:
            print(y, (int(r), int(g), int(b)))


def runs(rows):
    """Group sorted row indices into contiguous runs."""
    out = []
    for r in rows:
        if out and r - out[-1][-1] <= 1:
            out[-1].append(r)
        else:
            out.append([r])
    return out


def cmd_trace(args):
    arr = load(args.png)
    h, w, _ = arr.shape
    xcal = parse_cal(args.xcal)
    ycal = parse_cal(args.ycal)
    x0, x1 = parse_box(args.xbox, w)
    y0, y1 = parse_box(args.ybox, h)
    target = np.array([int(v) for v in args.rgb.split(",")])
    dist = np.sqrt(((arr - target) ** 2).sum(axis=2))
    match = dist <= args.tol
    grid_rows = set()
    grid_cols = set()
    if args.skip_grid:
        dm = dark_mask(arr, args.dark)
        sub = dm[y0:y1 + 1, x0:x1 + 1]
        grid_rows = {y0 + i for i, f in enumerate(sub.mean(axis=1)) if f >= args.grid_frac}
        grid_cols = {x0 + i for i, f in enumerate(sub.mean(axis=0)) if f >= args.grid_frac}
    for xv in args.x:
        px = value_to_pixel(xv, xcal)
        centre = int(round(px))
        cols = [c for c in range(centre - args.band, centre + args.band + 1)
                if x0 <= c <= x1 and c not in grid_cols]
        if not cols:
            print(f"x={xv:g}: pixel {px:.1f} outside box or on gridline")
            continue
        rows = sorted({y for c in cols for y in range(y0, y1 + 1)
                       if match[y, c] and y not in grid_rows})
        if not rows:
            print(f"x={xv:g} (px {px:.1f}): no matching pixels")
            continue
        parts = []
        for run in runs(rows):
            yc = 0.5 * (run[0] + run[-1])
            parts.append(f"rows {run[0]}-{run[-1]} -> y={pixel_to_value(yc, ycal):.4g}")
        print(f"x={xv:g} (px {px:.1f}): " + "; ".join(parts))


def cmd_cross(args):
    arr = load(args.png)
    h, w, _ = arr.shape
    xcal = parse_cal(args.xcal)
    ycal = parse_cal(args.ycal)
    x0, x1 = parse_box(args.xbox, w)
    y0, y1 = parse_box(args.ybox, h)
    target = np.array([int(v) for v in args.rgb.split(",")])
    dist = np.sqrt(((arr - target) ** 2).sum(axis=2))
    match = dist <= args.tol
    grid_rows = set()
    grid_cols = set()
    if args.skip_grid:
        dm = dark_mask(arr, args.dark)
        sub = dm[y0:y1 + 1, x0:x1 + 1]
        grid_rows = {y0 + i for i, f in enumerate(sub.mean(axis=1)) if f >= args.grid_frac}
        grid_cols = {x0 + i for i, f in enumerate(sub.mean(axis=0)) if f >= args.grid_frac}
    centres = []
    for c in range(x0, x1 + 1):
        if c in grid_cols:
            continue
        rows = [y for y in range(y0, y1 + 1) if match[y, c] and y not in grid_rows]
        if rows:
            centres.append((c, 0.5 * (min(rows) + max(rows))))
    for yv in args.y:
        row = value_to_pixel(yv, ycal)
        hits = []
        for (ca, ra), (cb, rb) in zip(centres, centres[1:]):
            if (ra - row) * (rb - row) <= 0 and ra != rb:
                xc = ca + (row - ra) * (cb - ca) / (rb - ra)
                hits.append(f"{pixel_to_value(xc, xcal):.4g} (px {xc:.1f})")
        print(f"y={yv:g} (row {row:.1f}): " + (", ".join(hits) if hits else "no crossing"))


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("frame")
    p.add_argument("png")
    p.add_argument("--xbox", default="")
    p.add_argument("--ybox", default="")
    p.add_argument("--dark", type=int, default=110)
    p.add_argument("--min-frac", type=float, default=0.6)
    p.set_defaults(func=cmd_frame)

    p = sub.add_parser("probe")
    p.add_argument("png")
    p.add_argument("--px", type=int, required=True)
    p.add_argument("--ybox", default="")
    p.set_defaults(func=cmd_probe)

    p = sub.add_parser("trace")
    p.add_argument("png")
    p.add_argument("--xcal", required=True)
    p.add_argument("--ycal", required=True)
    p.add_argument("--rgb", required=True)
    p.add_argument("--tol", type=float, default=70)
    p.add_argument("--x", type=float, nargs="+", required=True)
    p.add_argument("--xbox", default="")
    p.add_argument("--ybox", default="")
    p.add_argument("--band", type=int, default=1)
    p.add_argument("--skip-grid", action="store_true")
    p.add_argument("--dark", type=int, default=110)
    p.add_argument("--grid-frac", type=float, default=0.5)
    p.set_defaults(func=cmd_trace)

    p = sub.add_parser("cross")
    p.add_argument("png")
    p.add_argument("--xcal", required=True)
    p.add_argument("--ycal", required=True)
    p.add_argument("--rgb", required=True)
    p.add_argument("--tol", type=float, default=70)
    p.add_argument("--y", type=float, nargs="+", required=True)
    p.add_argument("--xbox", default="")
    p.add_argument("--ybox", default="")
    p.add_argument("--skip-grid", action="store_true")
    p.add_argument("--dark", type=int, default=110)
    p.add_argument("--grid-frac", type=float, default=0.5)
    p.set_defaults(func=cmd_cross)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
