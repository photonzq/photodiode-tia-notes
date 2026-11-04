"""Phase margin, bandwidth and noise versus deliberately added input capacitance.

Usage: python added_cap_tradeoff.py <out_json>

Decompensated amplifiers on a 1-pF photodiode reach a low noise gain at
crossover.  Adding capacitance C_add from the inverting node to ground raises
the noise gain and the phase margin, at the cost of e_n * w * C noise.  For each
C_add this script reports
  - the largest phase margin over stable C_F >= 0.2 pF, the minimum total of Table 1.1,
  - the widest design with PM >= 40 deg and peaking <= 1 dB,
  - the widest design with PM >= 45 deg and peaking <= 1 dB,
  - for the last one, the input-referred noise at 100 MHz and the
    10-150 MHz band penalty (central noise model; FET parts also 'high').
"""
import json
import sys

import numpy as np

import tia_model as tm
from parts_db import PARTS
from run_analysis import (C_D, C_PCB_NOM, C_FPAR_NOM, F_NOISE, open_loop_model,
                          noise_inputs, noise_models_for)

PARTS_SHOWN = ["OPA818", "OPA846", "OPA955", "OPA855"]
C_ADD = [0, 1, 2, 3, 4, 5, 6, 8, 10, 12]


def widest(ol, R_F, C_T, pm_min, pk_max=1.0):
    best = None
    for cf in tm.CF_SCAN:
        if cf < C_FPAR_NOM:
            continue
        m = tm.loop_metrics(ol, R_F, C_T, cf)
        if m["stable"] and m["pm_deg"] >= pm_min and m["peaking_dB"] <= pk_max:
            if best is None or m["f_3dB"] > best[1]["f_3dB"]:
                best = (cf, m)
    return best


def max_pm(ol, R_F, C_T):
    best = None
    for cf in tm.CF_SCAN:
        if cf < C_FPAR_NOM:
            continue
        m = tm.loop_metrics(ol, R_F, C_T, cf)
        if m["stable"] and (best is None or m["pm_deg"] > best[1]["pm_deg"]):
            best = (cf, m)
    return best


def noise(p, R_F, C_T, C_F):
    nz = noise_inputs(p)
    out = {}
    S_ref = np.full_like(F_NOISE, 4 * tm.K_B * tm.T_ROOM / R_F)
    for fm in noise_models_for(p):
        if fm == "low":
            continue
        c100 = tm.noise_components(np.array([100e6]), R_F, C_T, C_F, nz, fet_model=fm)
        cN = tm.noise_components(F_NOISE, R_F, C_T, C_F, nz, fet_model=fm)
        out[fm] = dict(i_100MHz_pA=float(np.sqrt(c100["total"][0]) * 1e12),
                       penalty_10_150_dB=float(tm.band_average_penalty_db(F_NOISE, cN["total"], S_ref, 10e6, 150e6)))
    return out


def main(out_path):
    res = {}
    for name in PARTS_SHOWN:
        p = PARTS[name]
        ol, *_ = open_loop_model(p)
        for R_F in (1500.0, 2000.0):
            C_T0 = C_D + C_PCB_NOM + p["c_cm"] + p["c_diff"]
            for c_add in C_ADD:
                C_T = C_T0 + c_add * 1e-12
                row = dict(C_T_pF=C_T * 1e12)
                b = max_pm(ol, R_F, C_T)
                if b:
                    row["max_pm"] = dict(C_F_pF=b[0] * 1e12, pm_deg=b[1]["pm_deg"], f3_MHz=b[1]["f_3dB"] / 1e6,
                                         peaking_dB=b[1]["peaking_dB"])
                for pm_min in (40.0, 45.0):
                    w = widest(ol, R_F, C_T, pm_min)
                    if w:
                        cf, m = w
                        row[f"pm{pm_min:.0f}"] = dict(C_F_pF=cf * 1e12, pm_deg=m["pm_deg"], f3_MHz=m["f_3dB"] / 1e6,
                                                      peaking_dB=m["peaking_dB"], noise=noise(p, R_F, C_T, cf))
                res[f"{name}|{R_F:.0f}|{c_add}"] = row
                mp = row.get("max_pm")
                r45 = row.get("pm45")
                r40 = row.get("pm40")
                txt = f"{name:7s} R_F {R_F:5.0f} C_add {c_add:2d} pF (C_T {C_T*1e12:5.2f}): "
                txt += (f"max PM {mp['pm_deg']:4.1f} at C_F {mp['C_F_pF']:.2f} ({mp['f3_MHz']:4.0f} MHz)" if mp else "no stable C_F")
                for tag, r in (("PM>=40", r40), ("PM>=45", r45)):
                    if r:
                        nzs = "; ".join(f"{k}: {v['i_100MHz_pA']:.2f} pA, {v['penalty_10_150_dB']:.1f} dB"
                                        for k, v in r["noise"].items())
                        txt += f" | {tag}: C_F {r['C_F_pF']:.2f} pF, {r['f3_MHz']:4.0f} MHz, PM {r['pm_deg']:4.1f} [{nzs}]"
                    else:
                        txt += f" | {tag}: none"
                print(txt)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)


if __name__ == "__main__":
    main(sys.argv[1])
