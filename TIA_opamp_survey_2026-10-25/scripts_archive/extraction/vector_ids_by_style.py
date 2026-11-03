"""Select path ids from a pdf_vector_curves.py dump by stroke style and region.

Some datasheet plots draw each curve as hundreds of separate two-point
segments.  This helper lists the ids of all stroked paths in a dump JSON
whose colour and line width match, whose bounding box lies inside a given
plot rectangle and outside optional exclusion rectangles (legend boxes),
so that the ids can be passed to `pdf_vector_curves.py sample --ids`.

Usage
-----
python vector_ids_by_style.py <dump.json> --color r,g,b --width w
       --inside x0,y0,x1,y1 [--exclude x0,y0,x1,y1 ...] [--tol 0.02]
       [--min-span 0.0]

Colours are given in 0..1 units as stored by PyMuPDF.  Coordinates are
PDF points (origin top-left).  --min-span drops paths whose bounding box
is smaller than the given size in both directions (dots).
"""
import argparse
import json


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dump")
    ap.add_argument("--color", required=True)
    ap.add_argument("--width", type=float, required=True)
    ap.add_argument("--inside", required=True)
    ap.add_argument("--exclude", action="append", default=[])
    ap.add_argument("--tol", type=float, default=0.02)
    ap.add_argument("--min-span", type=float, default=0.0)
    a = ap.parse_args()

    with open(a.dump, encoding="utf-8") as fh:
        data = json.load(fh)
    col = [float(v) for v in a.color.split(",")]
    ix0, iy0, ix1, iy1 = (float(v) for v in a.inside.split(","))
    excl = [tuple(float(v) for v in e.split(",")) for e in a.exclude]

    ids = []
    for rec in data["paths"]:
        if rec.get("color") is None or rec.get("width") is None:
            continue
        if any(abs(c - k) > a.tol for c, k in zip(rec["color"], col)):
            continue
        if abs(rec["width"] - a.width) > 0.01:
            continue
        x0, y0, x1, y1 = rec["bbox"]
        if x0 < ix0 or x1 > ix1 or y0 < iy0 or y1 > iy1:
            continue
        if any(x0 >= e[0] and x1 <= e[2] and y0 >= e[1] and y1 <= e[3] for e in excl):
            continue
        if (x1 - x0) < a.min_span and (y1 - y0) < a.min_span:
            continue
        ids.append(rec["id"])
    print(",".join(str(i) for i in ids))


if __name__ == "__main__":
    main()
