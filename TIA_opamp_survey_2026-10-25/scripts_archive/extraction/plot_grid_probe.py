"""Probe a rendered datasheet plot (PNG) for gridlines and curve crossings.

The script only measures pixel positions; converting them to data values
(frequency, dB, degrees, nV/rtHz ...) is done by the reader from the axis
labels, so every reading can still be checked against the image itself.

Usage
-----
python plot_grid_probe.py <png> grid [--frac 0.5] [--dark 140]
    Lists vertical and horizontal gridlines: columns/rows in which at least
    FRAC of the pixels are darker than DARK (0-255 grey level).  Adjacent
    columns/rows are merged and reported as (start, end, centre).

python plot_grid_probe.py <png> col <x> [--dark 200] [--half 1]
    Lists every dark run met while walking down column x (averaged over
    x-half .. x+half).  Each run is reported as (y_start, y_end, centre,
    length, mean grey).  Gridlines show up as short runs at the gridline
    rows; a curve shows up as an extra run, usually longer (thicker) and,
    for grey curves, with a mean grey level well above 0.

python plot_grid_probe.py <png> row <y> [--dark 200] [--half 1]
    Same as 'col' but walking along row y.

Coordinates are pixel indices of the PNG (x to the right, y downwards).
"""
import argparse

import numpy as np
from PIL import Image


def load_grey(path: str) -> np.ndarray:
    """Return the image as a 2-D uint8 array of grey levels."""
    return np.asarray(Image.open(path).convert("L"), dtype=np.uint8)


def true_runs(mask: np.ndarray) -> list[tuple[int, int]]:
    """Return (start, end) index pairs, inclusive, of consecutive True values."""
    runs = []
    start = None
    for i, flag in enumerate(mask):
        if flag and start is None:
            start = i
        elif not flag and start is not None:
            runs.append((start, i - 1))
            start = None
    if start is not None:
        runs.append((start, len(mask) - 1))
    return runs


def cmd_grid(grey: np.ndarray, frac: float, dark: int) -> None:
    mask = grey < dark
    col_frac = mask.mean(axis=0)
    row_frac = mask.mean(axis=1)
    print(f"image size (w x h) = {grey.shape[1]} x {grey.shape[0]}")
    print("vertical lines (x_start, x_end, x_centre, fraction):")
    for s, e in true_runs(col_frac >= frac):
        print(f"  {s:5d} {e:5d} {0.5 * (s + e):8.1f} {col_frac[s:e + 1].max():.2f}")
    print("horizontal lines (y_start, y_end, y_centre, fraction):")
    for s, e in true_runs(row_frac >= frac):
        print(f"  {s:5d} {e:5d} {0.5 * (s + e):8.1f} {row_frac[s:e + 1].max():.2f}")


def cmd_line(grey: np.ndarray, axis: str, pos: int, half: int, dark: int) -> None:
    if axis == "col":
        strip = grey[:, max(pos - half, 0):pos + half + 1].astype(float)
        profile = strip.mean(axis=1)
    else:
        strip = grey[max(pos - half, 0):pos + half + 1, :].astype(float)
        profile = strip.mean(axis=0)
    print(f"{axis} {pos}: runs darker than {dark} (start, end, centre, length, mean grey)")
    for s, e in true_runs(profile < dark):
        seg = profile[s:e + 1]
        print(f"  {s:5d} {e:5d} {0.5 * (s + e):8.1f} {e - s + 1:4d} {seg.mean():6.1f}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("png")
    parser.add_argument("mode", choices=["grid", "col", "row"])
    parser.add_argument("pos", nargs="?", type=int, default=None)
    parser.add_argument("--frac", type=float, default=0.5)
    parser.add_argument("--dark", type=int, default=None)
    parser.add_argument("--half", type=int, default=1)
    args = parser.parse_args()

    grey = load_grey(args.png)
    if args.mode == "grid":
        cmd_grid(grey, args.frac, args.dark if args.dark is not None else 140)
    else:
        if args.pos is None:
            parser.error("col/row mode needs a pixel position")
        cmd_line(grey, args.mode, args.pos, args.half,
                 args.dark if args.dark is not None else 200)


if __name__ == "__main__":
    main()
