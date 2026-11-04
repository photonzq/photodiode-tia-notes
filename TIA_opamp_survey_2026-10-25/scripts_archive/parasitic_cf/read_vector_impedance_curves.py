"""Convert vector-drawn impedance curves |Z|/R versus frequency (exported with
dump_pdf_vector_paths.py) into data coordinates, and compute for each point the
equivalent parallel capacitance that a pure parallel R-C would need to give the same
|Z|/R:

    C_eq(f) = sqrt( (R/|Z|)^2 - 1 ) / (2 * pi * f * R).

If the curve was drawn from a lumped model whose shunt capacitance C dominates (that is,
R^2 C much larger than the series inductance L), C_eq is flat and equal to C.  A C_eq that
drifts with frequency shows that other elements (series or connection inductance,
capacitance to ground, fixture) shape the curve.

Usage
-----
python read_vector_impedance_curves.py <dump.json> <panel_spec.json> [--csv out.csv]

The panel specification is a JSON list of panels; each panel gives the axis calibration
from two vertical grid lines and two horizontal grid lines read from the dump, the
plot frame, and which path index carries which resistance value:

  [{"name": "0402 flip chip",
    "frame": [x0, y0, x1, y1],
    "x_cal": [[x_pt_a, f_a_GHz], [x_pt_b, f_b_GHz]],      (log axis)
    "y_cal": [[y_pt_a, v_a], [y_pt_b, v_b]],              (linear axis)
    "curves": {"148": 1000, "149": 500},                   (path index -> R in ohm)
    "path_colour": [r, g, b]                               (optional: select by colour)
  }, ...]

A path may hold several sub-curves; with "split": true the path is cut wherever x runs
backwards, and the pieces are reported separately as <index>.<k>.
"""
import argparse
import json
import math


def x_to_f(x, cal):
    (xa, fa), (xb, fb) = cal
    la, lb = math.log10(fa), math.log10(fb)
    return 10 ** (la + (x - xa) * (lb - la) / (xb - xa))


def y_to_v(y, cal):
    (ya, va), (yb, vb) = cal
    return va + (y - ya) * (vb - va) / (yb - ya)


def split_backwards(points):
    """Cut a path into runs that are monotonic in x (a curve drawn right-to-left
    followed by one drawn left-to-right becomes two pieces).  Each piece is returned
    sorted by increasing x."""
    pieces, cur, direction = [], [points[0]], 0
    for p in points[1:]:
        dx = p[0] - cur[-1][0]
        step = 0 if abs(dx) < 1e-3 else (1 if dx > 0 else -1)
        if direction == 0 or step == 0 or step == direction:
            if step != 0:
                direction = step
            cur.append(p)
        else:
            pieces.append(cur)
            cur, direction = [cur[-1], p], step
    pieces.append(cur)
    return [sorted(piece, key=lambda q: q[0]) for piece in pieces]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dump")
    parser.add_argument("spec")
    parser.add_argument("--csv", default="")
    parser.add_argument("--list", action="store_true",
                        help="only list the paths inside each frame with their end points")
    args = parser.parse_args()

    dump = json.load(open(args.dump, encoding="utf-8"))
    spec = json.load(open(args.spec, encoding="utf-8"))
    rows = []
    for panel in spec:
        x0, y0, x1, y1 = panel["frame"]
        print(f"=== {panel['name']}")
        if args.list:
            for i, p in enumerate(dump["paths"]):
                r = p["rect"]
                if r[0] >= x0 - 2 and r[2] <= x1 + 2 and r[1] >= y0 - 2 and r[3] <= y1 + 2:
                    if p["width"] and p["width"] >= 1.0 and len(p["points"]) > 2:
                        for k, piece in enumerate(split_backwards(p["points"])):
                            a, b = piece[0], piece[-1]
                            print(f"  path {i}.{k} n={len(piece)} colour={p['stroke']} "
                                  f"start f={x_to_f(a[0], panel['x_cal']):.3g} GHz v={y_to_v(a[1], panel['y_cal']):.3f} "
                                  f"end f={x_to_f(b[0], panel['x_cal']):.3g} GHz v={y_to_v(b[1], panel['y_cal']):.3f}")
            continue
        for key, r_ohm in panel["curves"].items():
            idx, _, sub = key.partition(".")
            pts = dump["paths"][int(idx)]["points"]
            if sub:
                pts = split_backwards(pts)[int(sub)]
            print(f"--- path {key}: R = {r_ohm} ohm")
            print("    f/GHz    |Z|/R    C_eq/fF")
            for x, y in pts:
                f = x_to_f(x, panel["x_cal"])
                v = y_to_v(y, panel["y_cal"])
                c_eq = float("nan")
                if 0 < v < 0.995:
                    c_eq = math.sqrt(1.0 / v ** 2 - 1.0) / (2 * math.pi * f * 1e9 * r_ohm) * 1e15
                rows.append((panel["name"], key, r_ohm, f, v, c_eq))
                print(f"    {f:7.3f}  {v:7.4f}  {c_eq:8.2f}")
    if args.csv and rows:
        with open(args.csv, "w", encoding="utf-8") as fh:
            fh.write("panel,path,R_ohm,f_GHz,Z_over_R,C_eq_fF\n")
            for row in rows:
                fh.write(",".join(str(v) for v in row) + "\n")


if __name__ == "__main__":
    main()
