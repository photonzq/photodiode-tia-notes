"""Allowed total feedback capacitance window for each leading amplifier.

Usage: python cf_window.py <out_json>

For R_F = 1.5 kOhm and 2 kOhm and the nominal and extreme PCB capacitance,
scan the total C_F and keep the values that are stable with phase margin
>= 45 deg, gain margin >= 3 dB and peaking <= 1 dB.  Reports the window and
the response at its geometric centre (the recommended starting value).
"""
import json
import sys

import numpy as np

import tia_model as tm
from parts_db import PARTS
from run_analysis import C_D, open_loop_model

PARTS_SHOWN = ["OPA855", "OPA858", "LMH6629 (COMP HI)", "OPA856", "OPA859", "THS4304", "OPA843",
               "OPA846", "OPA818", "OPA955"]
GRID = np.logspace(np.log10(0.05e-12), np.log10(3e-12), 240)


def window(ol, R_F, C_T, pm_min=45.0, gm_min=3.0, pk_max=1.0):
    ok = []
    for cf in GRID:
        m = tm.loop_metrics(ol, R_F, C_T, cf)
        gm_ok = (not np.isfinite(m["gm_dB"])) or m["gm_dB"] >= gm_min
        if m["stable"] and m["pm_deg"] >= pm_min and m["peaking_dB"] <= pk_max and gm_ok:
            ok.append(cf)
    if not ok:
        return None
    lo, hi = min(ok), max(ok)
    mid = np.sqrt(lo * hi)
    m = tm.loop_metrics(ol, R_F, C_T, mid)
    return dict(cf_min_pF=lo * 1e12, cf_max_pF=hi * 1e12, cf_mid_pF=mid * 1e12,
                f3_mid_MHz=m["f_3dB"] / 1e6, pm_mid_deg=m["pm_deg"], gm_mid_dB=m["gm_dB"],
                peaking_mid_dB=m["peaking_dB"],
                f3_at_min_MHz=tm.loop_metrics(ol, R_F, C_T, lo)["f_3dB"] / 1e6,
                f3_at_max_MHz=tm.loop_metrics(ol, R_F, C_T, hi)["f_3dB"] / 1e6)


def main(out_path):
    out = {}
    for name in PARTS_SHOWN:
        p = PARTS[name]
        ol, *_ = open_loop_model(p)
        for R_F in (1500.0, 2000.0):
            for c_pcb in (0.2e-12, 0.35e-12, 0.5e-12):
                C_T = C_D + c_pcb + p["c_cm"] + p["c_diff"]
                w = window(ol, R_F, C_T)
                out[f"{name}|{R_F:.0f}|{c_pcb*1e12:.2f}"] = w
                if w:
                    print(f"{name:18s} R_F={R_F:5.0f} C_PCB={c_pcb*1e12:.2f}: C_F {w['cf_min_pF']:.3f}-{w['cf_max_pF']:.3f} pF "
                          f"(f3 {w['f3_at_min_MHz']:.0f}-{w['f3_at_max_MHz']:.0f} MHz); centre {w['cf_mid_pF']:.3f} pF -> "
                          f"{w['f3_mid_MHz']:.0f} MHz, PM {w['pm_mid_deg']:.0f}, GM {w['gm_mid_dB']:.1f} dB, pk {w['peaking_mid_dB']:.2f} dB")
                else:
                    print(f"{name:18s} R_F={R_F:5.0f} C_PCB={c_pcb*1e12:.2f}: no C_F meets PM>=45, GM>=3, peaking<=1 dB")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)


if __name__ == "__main__":
    main(sys.argv[1])
