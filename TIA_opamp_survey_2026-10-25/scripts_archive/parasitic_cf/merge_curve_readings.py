"""Merge curve readings into one CSV table.

Inputs are pairs  <label>=<file>  where <file> is either
  * a CSV written by read_vector_impedance_curves.py (columns panel, path, R_ohm, f_GHz,
    Z_over_R, C_eq_fF), or
  * a text file written by trace_raster_curve.py (rows "f |Z|/R C_eq (x, y)"), in which
    case the resistance is given in the label as  <label>@<R_ohm>.

Usage
-----
python merge_curve_readings.py <out.csv> "<label>=<file>" ["<label>@<R>=<file>" ...]

The output has the columns source, panel, path, R_ohm, f_GHz, Z_over_R, C_eq_fF.
"""
import csv
import sys


def main() -> None:
    out = sys.argv[1]
    rows = []
    for item in sys.argv[2:]:
        label, _, path = item.partition("=")
        if path.lower().endswith(".csv"):
            with open(path, encoding="utf-8") as fh:
                for r in csv.DictReader(fh):
                    rows.append([label, r["panel"], r["path"], r["R_ohm"], r["f_GHz"],
                                 r["Z_over_R"], r["C_eq_fF"]])
        else:
            name, _, r_ohm = label.partition("@")
            with open(path, encoding="utf-8") as fh:
                for line in fh:
                    parts = line.split()
                    if len(parts) < 3 or not parts[0][0].isdigit():
                        continue
                    rows.append([name, "raster trace", "lowest dark curve", r_ohm,
                                 parts[0], parts[1], parts[2]])
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["source", "panel", "path", "R_ohm", "f_GHz", "Z_over_R", "C_eq_fF"])
        w.writerows(rows)
    print(f"{len(rows)} rows -> {out}")


if __name__ == "__main__":
    main()
