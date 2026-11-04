"""Cross-check at 10 kOhm, where this note meets the companion (Section 6.9, 4 November 2026): the companion's
open-loop model, which interpolates the datasheets' open-loop gain and phase, against this note's single-pole
model, both on the companion's node (a 1-pF photodiode pair with 0.35 pF of board capacitance), with
C_par = 0.1 pF and this note's design rule (the smallest C_F >= C_par within 0.1 dB of maximally flat), at
2 kOhm and 10 kOhm, for OPA855, OPA955, OPA858, OPA818 and LMH6629.

It imports the companion's tia_model.py, parts_db.py and run_analysis.py from its scripts_archive (read only) and
this note's designs on the same node from data/results/medium_gain.json (hg_medium_gain.py, run first).
Writes data/results/cross_check_companion.json. Run with python -B so that no bytecode is written into the
companion's folder.

Usage: python -B hg_cross_check_companion.py
"""
import json
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
RES = HERE.parent / "data" / "results"
sys.path.insert(0, str(HERE.parents[1] / "TIA_opamp_survey_2026-10-25" / "scripts_archive"))
import tia_model as tm  # noqa: E402
from parts_db import PARTS  # noqa: E402
from run_analysis import noise_inputs, open_loop_model  # noqa: E402

NAMES = {"OPA855": "OPA855", "OPA955": "OPA955", "OPA858": "OPA858", "OPA818": "OPA818", "LMH6629 (COMP HI)": "LMH6629"}
C_D, C_PCB, C_PAR = 1e-12, 0.35e-12, 0.1e-12
F_SPOT = np.array([10e6, 50e6])

ours = {(r["amp"], r["rf"]): r for r in json.loads((RES / "medium_gain.json").read_text(encoding="utf-8"))["cross_check"]}
rows = []
for key, short in NAMES.items():
    p = PARTS[key]
    ol = open_loop_model(p)[0]
    C_T = C_D + C_PCB + p["c_cm"] + p["c_diff"]
    for rf in (2e3, 1e4):
        cf = tm.design_cf(ol, rf, C_T, 0.1)
        cf_real = max(cf, C_PAR)
        mt = tm.loop_metrics(ol, rf, C_T, cf_real)
        comp = tm.noise_components(F_SPOT, rf, C_T, cf_real, noise_inputs(p), fet_model="central")
        o = ours[(short, rf)]
        rows.append({"amp": short, "rf": rf,
                     "companion": {"cf_pF": cf_real * 1e12, "f3_Hz": mt["f_3dB"], "pm_deg": mt["pm_deg"],
                                   "ng_at_fc": mt["ng_at_fc"], "peaking_dB": mt["peaking_dB"],
                                   "i_n_10MHz_A": float(np.sqrt(comp["total"][0])),
                                   "i_n_50MHz_A": float(np.sqrt(comp["total"][1]))},
                     "this_note": {"cf_pF": o["cf_pF"], "f3_Hz": o["f3_Hz"], "pm_deg": o["pm_deg"]},
                     "f3_difference": o["f3_Hz"] / mt["f_3dB"] - 1.0,
                     "pm_difference_deg": o["pm_deg"] - mt["pm_deg"]})
        r = rows[-1]
        print(f"{short:8} {rf / 1e3:4.0f} kOhm: companion {mt['f_3dB'] / 1e6:6.1f} MHz, PM {mt['pm_deg']:5.1f}; "
              f"this note {o['f3_Hz'] / 1e6:6.1f} MHz, PM {o['pm_deg']:5.1f}; "
              f"difference {100 * r['f3_difference']:+.1f} %, {r['pm_difference_deg']:+.1f} deg")
(RES / "cross_check_companion.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
print("written", (RES / "cross_check_companion.json").name)
