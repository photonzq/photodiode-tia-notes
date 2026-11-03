"""Read values off a rendered datasheet plot by colour (a reading aid).

The plot image is a PNG clip rendered from the datasheet (for example with
render_pdf_pages.py --clip ... --dpi 300).  All positions are pixel
coordinates of that PNG.  The tool never guesses the axis calibration: the
user supplies two reference pixels per axis (normally the plot frame edges or
two labelled gridlines) and their axis values, after checking them by eye.

Sub-commands
------------
lines   <png> [--dark 90] [--frac 0.5]
        List rows and columns that contain long dark runs (plot frame) and
        long mid-grey runs (gridlines), to help locate the calibration pixels.

colour  <png> <x0> <y0> <x1> <y1>
        Most common colours inside a box (for example a legend line), to
        obtain the exact colour of a curve.

sample  <png> --cal X0PX,X0VAL,X1PX,X1VAL,XSCALE,Y0PX,Y0VAL,Y1PX,Y1VAL,YSCALE
        --rgb R,G,B [--tol 60] [--box x0,y0,x1,y1] --at v1,v2,...
        [--win W]
        For each requested x value, report the curve's y value.  Per column
        the curve position is the median row of the matching pixels, after
        removing vertical runs longer than --maxrun pixels (gridlines drawn in
        a similar colour).  With --win W the per-column values within +/-W of
        the requested x (decades for a log x axis, axis units for a linear
        one) are summarised as mean, min and max; otherwise a 3-column window
        is used.

cross   <png> --cal ... --rgb R,G,B [--tol 60] [--box ...] --level L
        [--from XVAL] [--direction down|up]
        Report the x value where the curve first passes the level L
        (direction 'down' = value falls through L as x increases).

XSCALE / YSCALE are 'log' or 'lin'.  --box limits the search to the plot
interior (exclude frame, legend and labels).  Reported values carry the
pixel-quantisation step (one pixel converted to axis units).
"""
import argparse
import math
import sys

import numpy as np
from PIL import Image


def load(path):
    return np.asarray(Image.open(path).convert("RGB")).astype(float)


def parse_cal(text):
    parts = text.split(",")
    if len(parts) != 10:
        raise SystemExit("--cal needs 10 comma-separated fields")
    x0p, x0v, x1p, x1v = (float(v) for v in parts[0:4])
    xs = parts[4].strip()
    y0p, y0v, y1p, y1v = (float(v) for v in parts[5:9])
    ys = parts[9].strip()
    return (x0p, x0v, x1p, x1v, xs), (y0p, y0v, y1p, y1v, ys)


def px_to_val(p, axis):
    p0, v0, p1, v1, scale = axis
    t = (p - p0) / (p1 - p0)
    if scale == "log":
        return 10 ** (math.log10(v0) + t * (math.log10(v1) - math.log10(v0)))
    return v0 + t * (v1 - v0)


def val_to_px(v, axis):
    p0, v0, p1, v1, scale = axis
    if scale == "log":
        t = (math.log10(v) - math.log10(v0)) / (math.log10(v1) - math.log10(v0))
    else:
        t = (v - v0) / (v1 - v0)
    return p0 + t * (p1 - p0)


def colour_mask(img, rgb, tol, box):
    diff = img - np.array(rgb, dtype=float)[None, None, :]
    dist = np.sqrt((diff ** 2).sum(axis=2))
    mask = dist <= tol
    if box is not None:
        x0, y0, x1, y1 = box
        keep = np.zeros_like(mask)
        keep[int(y0):int(y1) + 1, int(x0):int(x1) + 1] = True
        mask &= keep
    return mask


MINRUN = 1


def drop_long_runs(rows, maxrun):
    """Keep runs of consecutive rows with MINRUN <= length <= maxrun.

    Runs longer than maxrun are vertical lines (gridlines); runs shorter than
    MINRUN are thin horizontal gridlines or anti-aliasing specks.
    """
    if rows.size == 0:
        return rows
    keep = []
    start = 0
    for i in range(1, rows.size + 1):
        if i == rows.size or rows[i] != rows[i - 1] + 1:
            if MINRUN <= i - start <= maxrun:
                keep.extend(rows[start:i].tolist())
            start = i
    return np.array(keep, dtype=int)


def column_rows(mask, col, maxrun):
    if col < 0 or col >= mask.shape[1]:
        return np.array([], dtype=int)
    rows = np.nonzero(mask[:, col])[0]
    return drop_long_runs(rows, maxrun)


def column_y(mask, col, maxrun, half=1):
    rows = [column_rows(mask, c, maxrun) for c in range(col - half, col + half + 1)]
    rows = np.concatenate(rows) if rows else np.array([], dtype=int)
    if rows.size == 0:
        return None, None
    return float(np.median(rows)), float(rows.max() - rows.min())


def cmd_lines(args):
    img = load(args.png)
    grey = img.mean(axis=2)
    h, w = grey.shape
    dark = grey < args.dark
    mid = (grey > 100) & (grey < 215) & (np.ptp(img, axis=2) < 25)
    print(f"image {w}x{h}")
    for name, m in (("dark", dark), ("grey", mid)):
        rows = [r for r in range(h) if m[r].sum() > args.frac * w]
        cols = [c for c in range(w) if m[:, c].sum() > args.frac * h]
        print(f"{name} rows: {rows}")
        print(f"{name} cols: {cols}")


def cmd_colour(args):
    img = load(args.png).astype(int)
    region = img[args.y0:args.y1 + 1, args.x0:args.x1 + 1].reshape(-1, 3)
    values, counts = np.unique(region, axis=0, return_counts=True)
    order = np.argsort(-counts)[:5]
    for i in order:
        print("RGB", values[i].tolist(), "count", int(counts[i]))


def cmd_sample(args):
    img = load(args.png)
    xax, yax = parse_cal(args.cal)
    rgb = [float(v) for v in args.rgb.split(",")]
    box = [float(v) for v in args.box.split(",")] if args.box else None
    mask = colour_mask(img, rgb, args.tol, box)
    for v in (float(s) for s in args.at.split(",")):
        col = int(round(val_to_px(v, xax)))
        if args.win > 0:
            if xax[4] == "log":
                lo = int(round(val_to_px(v * 10 ** (-args.win), xax)))
                hi = int(round(val_to_px(v * 10 ** args.win, xax)))
            else:
                lo = int(round(val_to_px(v - args.win, xax)))
                hi = int(round(val_to_px(v + args.win, xax)))
            vals = []
            for c in range(lo, hi + 1):
                rows = column_rows(mask, c, args.maxrun)
                if rows.size:
                    vals.append(px_to_val(float(np.median(rows)), yax))
            if not vals:
                print(f"x={v:g}: no matching pixels in cols {lo}-{hi}")
                continue
            vals = np.array(vals)
            print(f"x={v:g} (cols {lo}-{hi}, n={vals.size}): mean={vals.mean():.4g}"
                  f"  min={vals.min():.4g}  max={vals.max():.4g}")
            continue
        y, spread = column_y(mask, col, args.maxrun)
        if y is None:
            print(f"x={v:g}: no matching pixels in column {col}")
            continue
        val = px_to_val(y, yax)
        dv = abs(px_to_val(y + 1, yax) - val)
        print(f"x={v:g} (col {col}): y={val:.4g}  (row {y:.1f}, line spread {spread:.0f} px,"
              f" 1 px = {dv:.3g})")


def cmd_cross(args):
    img = load(args.png)
    xax, yax = parse_cal(args.cal)
    rgb = [float(v) for v in args.rgb.split(",")]
    box = [float(v) for v in args.box.split(",")] if args.box else None
    mask = colour_mask(img, rgb, args.tol, box)
    start = int(round(val_to_px(args.from_x, xax))) if args.from_x else 0
    prev = None
    for col in range(start, mask.shape[1]):
        y, _ = column_y(mask, col, args.maxrun, half=0)
        if y is None:
            continue
        val = px_to_val(y, yax)
        passed = val <= args.level if args.direction == "down" else val >= args.level
        if passed:
            if prev is None:
                print(f"curve already past level at first column {col}")
                return
            pcol, pval = prev
            frac = 0.0 if val == pval else (args.level - pval) / (val - pval)
            xcol = pcol + frac * (col - pcol)
            xv = px_to_val(xcol, xax)
            dx = abs(px_to_val(xcol + 1, xax) - xv)
            print(f"crossing of {args.level:g} at x={xv:.4g} (col {xcol:.1f}; 1 px = {dx:.3g};"
                  f" bracketing cols {pcol}->{col})")
            return
        prev = (col, val)
    print("no crossing found")


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("lines")
    a.add_argument("png")
    a.add_argument("--dark", type=float, default=90)
    a.add_argument("--frac", type=float, default=0.5)
    b = sub.add_parser("colour")
    b.add_argument("png")
    for k in ("x0", "y0", "x1", "y1"):
        b.add_argument(k, type=int)
    for name in ("sample", "cross"):
        c = sub.add_parser(name)
        c.add_argument("png")
        c.add_argument("--cal", required=True)
        c.add_argument("--rgb", required=True)
        c.add_argument("--tol", type=float, default=60)
        c.add_argument("--box", default="")
        c.add_argument("--maxrun", type=int, default=40)
        c.add_argument("--minrun", type=int, default=1)
        if name == "sample":
            c.add_argument("--at", required=True)
            c.add_argument("--win", type=float, default=0.0)
        else:
            c.add_argument("--level", type=float, required=True)
            c.add_argument("--from", dest="from_x", type=float, default=None)
            c.add_argument("--direction", choices=("down", "up"), default="down")
    args = ap.parse_args()
    global MINRUN
    MINRUN = getattr(args, "minrun", 1)
    {"lines": cmd_lines, "colour": cmd_colour, "sample": cmd_sample, "cross": cmd_cross}[args.cmd](args)


if __name__ == "__main__":
    main()
