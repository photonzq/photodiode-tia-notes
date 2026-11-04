"""Section 6.10: larger feedback resistors, up to the 10 kOhm at which the companion note takes over (4 November 2026).

The analysis of Chapter 6 at R_F = 2, 3, 5 and 10 kOhm for the ten amplifiers carried forward, on the 1-pF node with
the nominal 0.35 pF of board capacitance, for the nominal 0.2-pF feedback parasitic (Table A6.38) and for 0.1 pF
(Table A6.39). For each part and R_F:
- the robust design of run_analysis.robust_design without added input capacitance: the widest bandwidth with a phase
  margin of at least 45 deg and at most 1 dB of peaking, the total C_F never below the parasitic. At these resistances
  the noise gain needs no added capacitance for stability; added capacitance only lets the loop's peaking carry the
  response past the resistor's own pole, at a cost in noise, so the widest design with added capacitance (the full
  rule of Table A9.2) is kept in the JSON file for comparison, not in the tables;
- its -3 dB bandwidth, phase margin and total C_F;
- the band-average input-referred noise over 10 MHz to the lower of 150 MHz and the bandwidth, against the Johnson
  noise of R_F (the 'central' FET model of Section 3.7);
- the DC photocurrent of the pair whose shot noise equals that noise, I_eq = S_TIA/(2q), above which the light
  dominates.
Writes data/results/medium_gain.json and data/results/table_a6_38.md and table_a6_39.md (captions included).

Usage: python medium_gain.py
"""
import json
from pathlib import Path

import numpy as np

import run_analysis as ra
import tia_model as tm
from parts_db import PARTS

HERE = Path(__file__).resolve().parent
RES = HERE.parent / "data" / "results"
NAMES = ["OPA855", "OPA955", "LMH6629", "OPA856", "OPA858", "OPA859", "THS4304", "OPA818", "OPA846", "OPA843"]
LABEL = {"LMH6629": "LMH6629 (COMP HI)"}
R_FS = (2e3, 3e3, 5e3, 10e3)
C_FPARS = (0.2e-12, 0.1e-12)
F = np.linspace(1e4, 400e6, 40001)


FULL_C_ADD = ra.C_ADD_SCAN


def noise_of(p, rf, d):
    """Band penalty over 10 MHz to min(150 MHz, f_3dB) and the pair's photocurrent whose shot noise equals it."""
    f_hi = min(150e6, d["f3_MHz"] * 1e6)
    comp = tm.noise_components(F, rf, d["C_T_pF"] * 1e-12, d["C_F_real_pF"] * 1e-12, ra.noise_inputs(p),
                               fet_model="central")
    s_ref = np.full_like(F, 4 * tm.K_B * tm.T_ROOM / rf)
    m = (F >= 10e6) & (F <= f_hi)
    s_avg = np.trapezoid(comp["total"][m], F[m]) / (F[m][-1] - F[m][0])
    return {"band_MHz": [10.0, f_hi / 1e6], "penalty_dB": tm.band_average_penalty_db(F, comp["total"], s_ref, 10e6, f_hi),
            "i_eq_uA": s_avg / (2 * tm.Q_E) * 1e6}


def design(name, rf, cfpar):
    p = PARTS[LABEL.get(name, name)]
    ol = ra.open_loop_model(p)[0]
    c_t0 = ra.C_D + ra.C_PCB_NOM + p["c_cm"] + p["c_diff"]
    ra.C_ADD_SCAN = (0.0,)
    d = ra.robust_design(ol, rf, c_t0, cfpar)
    ra.C_ADD_SCAN = FULL_C_ADD
    wide = ra.robust_design(ol, rf, c_t0, cfpar)
    row = {"amp": name, "rf": rf, "c_fpar_pF": cfpar * 1e12, "design": d,
           "widest_with_added_capacitance": None if wide is None else {**wide, **noise_of(p, rf, wide)}}
    if d is not None:
        row.update(noise_of(p, rf, d))
    cal = p["ol"].get("calibrate")
    if cal:   # the calibrated open-loop curve of Table A6.7 (OPA855, OPA858, OPA859), with no added capacitance
        ol_cal = tm.calibrated_interp(ol, cal["gain_scale_dB"], cal["pm_target_deg"], cal["g_noise"])
        ra.C_ADD_SCAN = (0.0,)
        dc = ra.robust_design(ol_cal, rf, c_t0, cfpar)
        ra.C_ADD_SCAN = FULL_C_ADD
        row["calibrated"] = None if dc is None else {**dc, **noise_of(p, rf, dc)}
    return row


def table(rows, cfpar, number):
    cap = (f"*Table A6.{number}. Larger feedback resistors with {cfpar * 1e12:.1f} pF of feedback parasitic "
           f"{'(the nominal value)' if cfpar > 0.15e-12 else '(an optimistic layout)'}: the robust design of each "
           "amplifier carried forward (the widest bandwidth with a phase margin of at least 45° and at most 1 dB of "
           "peaking, as in Table A9.2, but with no capacitance added at the input) on the 1-pF node with 0.35 pF of "
           "board capacitance. Each cell gives the −3 dB "
           "bandwidth and the phase margin; the band-average input-referred noise over 10 MHz to the lower of 150 MHz "
           "and the bandwidth, against the Johnson noise of $R_F$ (central FET model, Section 3.7); and the DC "
           "photocurrent of the pair whose shot noise equals that noise. Each open-loop curve as plotted; Section 6.10 "
           "gives OPA858 with its calibrated curve (Table A6.7). Amplifiers: the ten carried forward. "
           "`medium_gain.py`.*")
    head = "| Part | " + " | ".join(f"{rf / 1e3:g} kΩ" for rf in R_FS) + " |\n|---|" + "---|" * len(R_FS)
    lines = [cap, "", head]
    for name in NAMES:
        cells = []
        for rf in R_FS:
            r = next(x for x in rows if x["amp"] == name and x["rf"] == rf and abs(x["c_fpar_pF"] - cfpar * 1e12) < 1e-9)
            d = r["design"]
            cells.append("needs added input capacitance" if d is None else
                         f"{d['f3_MHz']:.0f} MHz, {d['pm_deg']:.0f}°; {r['penalty_dB']:.1f} dB; {r['i_eq_uA']:.0f} µA")
        lines.append(f"| {LABEL.get(name, name)} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def main():
    rows = [design(n, rf, c) for n in NAMES for c in C_FPARS for rf in R_FS]
    (RES / "medium_gain.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    for number, cfpar in ((38, 0.2e-12), (39, 0.1e-12)):
        (RES / f"table_a6_{number}.md").write_text(table(rows, cfpar, number) + "\n", encoding="utf-8", newline="\n")
        print(table(rows, cfpar, number), "\n")


if __name__ == "__main__":
    main()
