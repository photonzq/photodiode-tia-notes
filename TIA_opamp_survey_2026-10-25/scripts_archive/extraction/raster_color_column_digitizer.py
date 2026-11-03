"""Read values off a rendered datasheet plot (PNG) by curve colour.

Two modes
---------
1. Grid detection (to calibrate the axes):

   python digitize_curve.py <png> --grid --box x0,y0,x1,y1 [--dark 400] [--frac 0.5]

   Prints the pixel columns / rows inside the box whose pixels are mostly
   dark (gridlines and the plot frame).  Use these positions, together with
   the axis labels read by eye from the image, to build the calibration.

2. Curve reading:

   python digitize_curve.py <png> --xcal PX1=V1,PX2=V2 [--xlog]
                            --ycal PY1=V1,PY2=V2 [--ylog]
                            --color R,G,B [--tol 60] [--minrun 3]
                            [--win 2] [--maxrun N] [--box x0,y0,x1,y1]
                            --xs 1e5,1e6,...

   For each requested x value the script converts it to a pixel column,
   collects the pixels of that colour (Euclidean RGB distance <= tol) in a
   window of columns, groups them into vertical runs, drops runs shorter
   than --minrun pixels (thin gridlines) or longer than --maxrun pixels
   (vertical gridlines of the same colour), and reports the centre of every
   remaining run converted to the y axis value.  When a column holds no
   matching pixel the line says so; read that point by eye instead.

3. Row reading (near-vertical curves, e.g. output-swing limits):

   same calibration and colour options, but --ys 1.5,-2.0 instead of --xs;
   prints the x positions where the colour crosses each requested y value.

All coordinates are pixels of the PNG given on the command line.  The
output is a reading aid; check every value against the rendered image.
"""
import argparse
import math

import numpy as np
from PIL import Image


def parse_pairs(text):
    pairs = []
    for item in text.split(","):
        px, val = item.split("=")
        pairs.append((float(px), float(val)))
    return pairs


def make_axis(pairs, log):
    (p1, v1), (p2, v2) = pairs
    if log:
        v1, v2 = math.log10(v1), math.log10(v2)
    slope = (v2 - v1) / (p2 - p1)

    def to_val(px):
        val = v1 + (px - p1) * slope
        return 10 ** val if log else val

    def to_px(val):
        if log:
            val = math.log10(val)
        return p1 + (val - v1) / slope

    return to_val, to_px


def runs(indices):
    """Group sorted integer indices into (start, stop) runs."""
    out = []
    if len(indices) == 0:
        return out
    start = prev = indices[0]
    for i in indices[1:]:
        if i == prev + 1:
            prev = i
            continue
        out.append((start, prev))
        start = prev = i
    out.append((start, prev))
    return out


def grid_mode(img, box, dark, frac):
    x0, y0, x1, y1 = box
    sub = img[y0:y1, x0:x1].sum(axis=2)
    mask = sub < dark
    col_frac = mask.mean(axis=0)
    row_frac = mask.mean(axis=1)
    cols = [x0 + i for i, f in enumerate(col_frac) if f >= frac]
    rows = [y0 + i for i, f in enumerate(row_frac) if f >= frac]
    print("vertical lines (px):", [f"{a}-{b}" if a != b else f"{a}" for a, b in runs(cols)])
    print("horizontal lines (px):", [f"{a}-{b}" if a != b else f"{a}" for a, b in runs(rows)])


def curve_mode(img, args):
    x_to_val, x_to_px = make_axis(parse_pairs(args.xcal), args.xlog)
    y_to_val, _ = make_axis(parse_pairs(args.ycal), args.ylog)
    target = np.array([float(v) for v in args.color.split(",")])
    height, width, _ = img.shape
    if args.box:
        bx0, by0, bx1, by1 = (int(v) for v in args.box.split(","))
    else:
        bx0, by0, bx1, by1 = 0, 0, width, height
    dist = np.sqrt(((img - target) ** 2).sum(axis=2))
    match = dist <= args.tol
    for text in args.xs.split(","):
        xval = float(text)
        px = x_to_px(xval)
        col = int(round(px))
        if col < bx0 or col >= bx1:
            print(f"x={xval:g}: column {col} outside box")
            continue
        lo, hi = max(bx0, col - args.win), min(bx1, col + args.win + 1)
        rows = np.where(match[by0:by1, lo:hi].any(axis=1))[0] + by0
        found = [(a, b) for a, b in runs(list(rows))
                 if args.minrun <= b - a + 1 <= args.maxrun]
        if not found:
            print(f"x={xval:g}: column {col}: no matching run")
            continue
        parts = []
        for a, b in found:
            centre = 0.5 * (a + b)
            parts.append(f"rows {a}-{b} -> y={y_to_val(centre):.4g}"
                         f" (edges {y_to_val(a):.4g}..{y_to_val(b):.4g})")
        print(f"x={xval:g}: column {col}: " + "; ".join(parts))


def row_mode(img, args):
    """Inverse reading: for each requested y value, report the x positions
    of the colour runs crossing that pixel row (for near-vertical curves)."""
    x_to_val, _ = make_axis(parse_pairs(args.xcal), args.xlog)
    _, y_to_px = make_axis(parse_pairs(args.ycal), args.ylog)
    target = np.array([float(v) for v in args.color.split(",")])
    height, width, _ = img.shape
    if args.box:
        bx0, by0, bx1, by1 = (int(v) for v in args.box.split(","))
    else:
        bx0, by0, bx1, by1 = 0, 0, width, height
    dist = np.sqrt(((img - target) ** 2).sum(axis=2))
    match = dist <= args.tol
    for text in args.ys.split(","):
        yval = float(text)
        row = int(round(y_to_px(yval)))
        if row < by0 or row >= by1:
            print(f"y={yval:g}: row {row} outside box")
            continue
        lo, hi = max(by0, row - args.win), min(by1, row + args.win + 1)
        cols = np.where(match[lo:hi, bx0:bx1].any(axis=0))[0] + bx0
        found = [(a, b) for a, b in runs(list(cols))
                 if args.minrun <= b - a + 1 <= args.maxrun]
        if not found:
            print(f"y={yval:g}: row {row}: no matching run")
            continue
        parts = []
        for a, b in found:
            centre = 0.5 * (a + b)
            parts.append(f"cols {a}-{b} -> x={x_to_val(centre):.4g}"
                         f" (edges {x_to_val(a):.4g}..{x_to_val(b):.4g})")
        print(f"y={yval:g}: row {row}: " + "; ".join(parts))


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("png")
    parser.add_argument("--grid", action="store_true")
    parser.add_argument("--box", default="")
    parser.add_argument("--dark", type=int, default=400)
    parser.add_argument("--frac", type=float, default=0.5)
    parser.add_argument("--xcal", default="")
    parser.add_argument("--ycal", default="")
    parser.add_argument("--xlog", action="store_true")
    parser.add_argument("--ylog", action="store_true")
    parser.add_argument("--color", default="255,0,0")
    parser.add_argument("--tol", type=float, default=60.0)
    parser.add_argument("--minrun", type=int, default=3)
    parser.add_argument("--win", type=int, default=2)
    parser.add_argument("--maxrun", type=int, default=10**6)
    parser.add_argument("--xs", default="")
    parser.add_argument("--ys", default="",
                        help="row mode: y values at which to report curve x positions")
    args = parser.parse_args()

    img = np.array(Image.open(args.png).convert("RGB")).astype(int)
    if args.grid:
        box = [int(v) for v in args.box.split(",")]
        grid_mode(img, box, args.dark, args.frac)
    elif args.ys:
        row_mode(img, args)
    else:
        curve_mode(img, args)


if __name__ == "__main__":
    main()
