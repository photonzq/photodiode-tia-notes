"""Response of the recommended designs to the total feedback capacitance and to C_PCB.

Usage: python cf_sensitivity.py <out_json>

For each recommended amplifier and both feedback resistors, evaluate a short
list of total C_F values (external part plus resistor/pad parasitic) at
C_PCB = 0.2, 0.35 and 0.5 pF: -3 dB bandwidth, peaking, phase margin and gain
margin.  Optional added input capacitance (C_add) is included where a part
needs it.  The table in Section 8 of the report is printed from this output.
"""
import json
import sys

import tia_model as tm
from parts_db import PARTS
from run_analysis import C_D, open_loop_model

CASES = {
    "OPA855": dict(c_add=0.0, cf={1500.0: (0.15, 0.20, 0.25, 0.30, 0.35, 0.40),
                                   2000.0: (0.15, 0.20, 0.25, 0.30, 0.35, 0.40)}),
    "OPA856": dict(c_add=0.0, cf={1500.0: (0.45, 0.55, 0.65, 0.80, 1.00),
                                   2000.0: (0.40, 0.50, 0.60, 0.70, 0.90)}),
    "LMH6629 (COMP HI)": dict(c_add=0.0, cf={1500.0: (0.50, 0.60, 0.70, 0.85, 1.00),
                                              2000.0: (0.45, 0.55, 0.65, 0.80, 1.00)}),
    "OPA818": dict(c_add=0.0, cf={1500.0: (0.50, 0.60, 0.75, 0.90),
                                   2000.0: (0.45, 0.55, 0.68, 0.80)}),
    "OPA818 +2 pF": dict(part="OPA818", c_add=2.0, cf={1500.0: (0.85, 0.96, 1.10),
                                                        2000.0: (0.65, 0.75, 0.85, 1.00)}),
    "OPA955 +2 pF": dict(part="OPA955", c_add=2.0, cf={1500.0: (0.30, 0.35, 0.45),
                                                        2000.0: (0.25, 0.31, 0.40)}),
}


def main(out_path):
    out = {}
    for label, cs in CASES.items():
        p = PARTS[cs.get("part", label)]
        ol, *_ = open_loop_model(p)
        for R_F, cfs in cs["cf"].items():
            for cf in cfs:
                row = {}
                for c_pcb in (0.2, 0.35, 0.5):
                    C_T = C_D + (c_pcb + cs["c_add"]) * 1e-12 + p["c_cm"] + p["c_diff"]
                    m = tm.loop_metrics(ol, R_F, C_T, cf * 1e-12)
                    row[f"{c_pcb:.2f}"] = dict(f3_MHz=m["f_3dB"] / 1e6, pk_dB=m["peaking_dB"], pm=m["pm_deg"],
                                               gm=m["gm_dB"], stable=m["stable"])
                out[f"{label}|{R_F:.0f}|{cf:.2f}"] = row
                s = " | ".join(f"C_PCB {k}: {v['f3_MHz']:4.0f} MHz, {v['pk_dB']:+.1f} dB, PM {v['pm']:4.1f}, GM {v['gm']:4.1f}"
                               + ("" if v["stable"] else " UNSTABLE") for k, v in row.items())
                print(f"{label:18s} R_F {R_F:5.0f} C_F {cf:.2f} pF: {s}")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)


if __name__ == "__main__":
    main(sys.argv[1])
