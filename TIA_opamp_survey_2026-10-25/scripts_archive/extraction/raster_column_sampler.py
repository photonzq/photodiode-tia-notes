"""Help read values off a rendered datasheet plot (PNG).

Two sub-commands
----------------
grid    List the pixel positions of long straight lines (axes and
        gridlines), to calibrate the pixel <-> value mapping.

        python plot_digitize.py grid <png> [--dark 110] [--frac 0.5]
                                     [--box x0,y0,x1,y1]

sample  For each requested x value, list the runs of curve-coloured pixels
        found in that pixel column, converted to plot units.

        python plot_digitize.py sample <png>
            --xcal PX1:VAL1,PX2:VAL2 --xscale log|lin
            --ycal PY1:VAL1,PY2:VAL2 --yscale log|lin
            --gray LO,HI          (pixel grey level range of the curve)
            [--rgb R,G,B --tol T] (alternative: colour match for colour plots)
            [--box x0,y0,x1,y1]   (plot-area box in pixels; runs outside ignored)
            [--halfwidth 1]       (columns either side to merge)
            --x 1e5,1e6,...

The grey level of a pixel is the mean of its R, G and B values.  Runs that
coincide with horizontal gridlines can be suppressed with --skiprows (a
comma-separated list of pixel rows found by 'grid', +-2 px).  Always check the
output against the image: this tool locates pixels, it does not know which
curve is which.
"""
import argparse
import math

import numpy as np
from PIL import Image


def load(path):
    img = np.asarray(Image.open(path).convert("RGB")).astype(float)
    return img


def runs(mask_1d):
    """Return (start, stop) index pairs of True runs in a 1-D boolean array."""
    out = []
    start = None
    for i, v in enumerate(mask_1d):
        if v and start is None:
            start = i
        elif not v and start is not None:
            out.append((start, i - 1))
            start = None
    if start is not None:
        out.append((start, len(mask_1d) - 1))
    return out


def parse_box(spec, shape):
    if not spec:
        return 0, 0, shape[1] - 1, shape[0] - 1
    x0, y0, x1, y1 = (int(float(v)) for v in spec.split(","))
    return x0, y0, x1, y1


def cmd_grid(args):
    img = load(args.png)
    gray = img.mean(axis=2)
    x0, y0, x1, y1 = parse_box(args.box, gray.shape)
    sub = gray[y0:y1 + 1, x0:x1 + 1] < args.dark
    col_frac = sub.mean(axis=0)
    row_frac = sub.mean(axis=1)
    print("vertical lines (x px):")
    for a, b in runs(col_frac > args.frac):
        print(f"  x={x0 + (a + b) / 2:.1f}  width={b - a + 1}  frac={col_frac[a:b + 1].max():.2f}")
    print("horizontal lines (y px):")
    for a, b in runs(row_frac > args.frac):
        print(f"  y={y0 + (a + b) / 2:.1f}  width={b - a + 1}  frac={row_frac[a:b + 1].max():.2f}")


def make_map(cal, scale):
    (p1, v1), (p2, v2) = [tuple(float(t) for t in item.split(":")) for item in cal.split(",")]
    if scale == "log":
        l1, l2 = math.log10(v1), math.log10(v2)
        to_px = lambda v: p1 + (math.log10(v) - l1) * (p2 - p1) / (l2 - l1)
        to_val = lambda p: 10 ** (l1 + (p - p1) * (l2 - l1) / (p2 - p1))
    else:
        to_px = lambda v: p1 + (v - v1) * (p2 - p1) / (v2 - v1)
        to_val = lambda p: v1 + (p - p1) * (v2 - v1) / (p2 - p1)
    return to_px, to_val


def cmd_sample(args):
    img = load(args.png)
    gray = img.mean(axis=2)
    x0, y0, x1, y1 = parse_box(args.box, gray.shape)
    if args.rgb:
        target = np.array([float(v) for v in args.rgb.split(",")])
        mask = np.sqrt(((img - target) ** 2).sum(axis=2)) <= args.tol
    else:
        lo, hi = (float(v) for v in args.gray.split(","))
        mask = (gray >= lo) & (gray <= hi)
    skip = set()
    if args.skiprows:
        for r in args.skiprows.split(","):
            r = int(float(r))
            skip.update(range(r - 2, r + 3))
    xpx, xval = make_map(args.xcal, args.xscale)
    _, yval = make_map(args.ycal, args.yscale)
    # Columns occupied by vertical gridlines (and their anti-aliased edges).
    dark = gray[y0:y1 + 1, :] < args.dark
    gridcol = dark.mean(axis=0) > 0.5
    blocked = gridcol.copy()
    for shift in range(1, args.gridpad + 1):
        blocked[shift:] |= gridcol[:-shift]
        blocked[:-shift] |= gridcol[shift:]
    for xv in (float(v) for v in args.x.split(",")):
        col = int(round(xpx(xv)))
        if col < x0 or col > x1:
            print(f"x={xv:g}: column {col} outside box")
            continue
        if args.avoidgrid and blocked[col]:
            for step in range(1, 15):
                if col - step >= x0 and not blocked[col - step]:
                    col = col - step
                    break
                if col + step <= x1 and not blocked[col + step]:
                    col = col + step
                    break
        xv_used = xval(col)
        lo_c, hi_c = col - args.halfwidth, col + args.halfwidth
        colmask = mask[:, lo_c:hi_c + 1].any(axis=1).copy()
        colmask[:y0] = False
        colmask[y1 + 1:] = False
        for r in skip:
            if 0 <= r < len(colmask):
                colmask[r] = False
        found = runs(colmask)
        desc = []
        for a, b in found:
            yc = (a + b) / 2
            desc.append(f"y={yc:.1f}px({b - a + 1})->{yval(yc):.4g}"
                        f" [{yval(b):.4g}..{yval(a):.4g}]")
        print(f"x={xv:g} (col {col}, x_used={xv_used:.4g}): "
              + ("; ".join(desc) if desc else "no curve pixels"))


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("grid")
    g.add_argument("png")
    g.add_argument("--dark", type=float, default=110.0)
    g.add_argument("--frac", type=float, default=0.5)
    g.add_argument("--box", default="")
    s = sub.add_parser("sample")
    s.add_argument("png")
    s.add_argument("--xcal", required=True)
    s.add_argument("--xscale", default="log", choices=["log", "lin"])
    s.add_argument("--ycal", required=True)
    s.add_argument("--yscale", default="lin", choices=["log", "lin"])
    s.add_argument("--gray", default="0,90")
    s.add_argument("--rgb", default="")
    s.add_argument("--tol", type=float, default=40.0)
    s.add_argument("--box", default="")
    s.add_argument("--halfwidth", type=int, default=1)
    s.add_argument("--skiprows", default="")
    s.add_argument("--dark", type=float, default=110.0)
    s.add_argument("--avoidgrid", action="store_true",
                   help="shift each sample column off vertical gridlines")
    s.add_argument("--gridpad", type=int, default=2,
                   help="columns either side of a gridline treated as blocked")
    s.add_argument("--x", required=True)
    args = parser.parse_args()
    if args.cmd == "grid":
        cmd_grid(args)
    else:
        cmd_sample(args)


if __name__ == "__main__":
    main()
