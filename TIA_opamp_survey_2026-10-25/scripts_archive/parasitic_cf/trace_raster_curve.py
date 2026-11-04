"""Read a curve off a raster (bitmap) plot of |Z|/R versus log frequency and convert
it to the equivalent parallel capacitance of a pure parallel R-C,

    C_eq(f) = sqrt( (R/|Z|)^2 - 1 ) / (2 * pi * f * R).

Two modes.

1. Axis finding (prints the pixel positions of the frame lines and of the tick marks
   so that they can be paired with the axis labels):

       python trace_raster_curve.py axes <image.png>

2. Tracing: in every pixel column between x_start and x_stop, take the dark pixel
   that is lowest (largest row index, i.e. the curve lying lowest on the plot) or
   highest, skipping an optional excluded rectangle (for example an inset), and
   convert it to data coordinates with a two-point calibration of each axis:

       python trace_raster_curve.py trace <image.png> --R 1000
           --xcal px_a:f_a,px_b:f_b      (log axis, f in GHz)
           --ycal py_a:v_a,py_b:v_b      (linear axis)
           --xrange x_start:x_stop [--exclude x0:y0:x1:y1] [--pick lowest|highest]
           [--ylim y_top:y_bottom] [--dark 90] [--step 4]

The darkness threshold (0 = black, 255 = white) separates drawn lines from grey data
symbols.  Results are printed as f/GHz, |Z|/R and C_eq/fF.  The image is only read.
"""
import argparse
import math

import numpy as np
from PIL import Image


def load_gray(path):
    return np.asarray(Image.open(path).convert("L"), dtype=float)


def find_axes(img, dark):
    mask = img < dark
    h, w = mask.shape
    col_counts = mask.sum(axis=0)
    row_counts = mask.sum(axis=1)
    cols = [(x, int(c)) for x, c in enumerate(col_counts) if c > 0.5 * h]
    rows = [(y, int(c)) for y, c in enumerate(row_counts) if c > 0.5 * w]
    print("long vertical dark lines (x, count):", cols)
    print("long horizontal dark lines (y, count):", rows)
    if cols and rows:
        x_axis = cols[0][0]
        y_axis = rows[-1][0]
        # tick marks: short dark runs just right of the left axis / just above the bottom axis
        yt = [y for y in range(h) if mask[y, x_axis + 2:x_axis + 6].sum() >= 3]
        xt = [x for x in range(w) if mask[y_axis - 6:y_axis - 2, x].sum() >= 3]
        print("left axis at x =", x_axis, "; candidate y ticks:", yt)
        print("bottom axis at y =", y_axis, "; candidate x ticks:", xt)


def trace(img, args):
    (pxa, fa), (pxb, fb) = [tuple(float(v) for v in s.split(":")) for s in args.xcal.split(",")]
    (pya, va), (pyb, vb) = [tuple(float(v) for v in s.split(":")) for s in args.ycal.split(",")]
    x0, x1 = (int(v) for v in args.xrange.split(":"))
    excl = [int(v) for v in args.exclude.split(":")] if args.exclude else None
    mask = img < args.dark
    print("    f/GHz    |Z|/R    C_eq/fF   (pixel x, y)")
    for x in range(x0, x1 + 1, args.step):
        ys = np.nonzero(mask[:, x])[0]
        if excl:
            ex0, ey0, ex1, ey1 = excl
            if ex0 <= x <= ex1:
                ys = ys[(ys < ey0) | (ys > ey1)]
        if args.ylim:
            ylo, yhi = (int(v) for v in args.ylim.split(":"))
            ys = ys[(ys >= ylo) & (ys <= yhi)]
        else:
            ys = ys[(ys > min(pya, pyb) - 40) & (ys < max(pya, pyb) + 5)]
        if ys.size == 0:
            continue
        y = ys.max() if args.pick == "lowest" else ys.min()
        f = 10 ** (math.log10(fa) + (x - pxa) * (math.log10(fb) - math.log10(fa)) / (pxb - pxa))
        v = va + (y - pya) * (vb - va) / (pyb - pya)
        c_eq = float("nan")
        if 0 < v < 0.99:
            c_eq = math.sqrt(1 / v ** 2 - 1) / (2 * math.pi * f * 1e9 * args.R) * 1e15
        print(f"    {f:7.3f}  {v:7.4f}  {c_eq:8.2f}   ({x}, {int(y)})")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["axes", "trace"])
    parser.add_argument("image")
    parser.add_argument("--dark", type=float, default=90)
    parser.add_argument("--R", type=float, default=1000.0)
    parser.add_argument("--xcal", default="")
    parser.add_argument("--ycal", default="")
    parser.add_argument("--xrange", default="")
    parser.add_argument("--exclude", default="")
    parser.add_argument("--ylim", default="",
                        help="only rows y_top:y_bottom are searched (keeps frame lines out)")
    parser.add_argument("--pick", choices=["lowest", "highest"], default="lowest")
    parser.add_argument("--step", type=int, default=4)
    args = parser.parse_args()
    img = load_gray(args.image)
    if args.mode == "axes":
        find_axes(img, args.dark)
    else:
        trace(img, args)


if __name__ == "__main__":
    main()
