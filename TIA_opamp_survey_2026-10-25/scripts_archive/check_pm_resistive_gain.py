"""Sanity check: phase margin of the interpolated open-loop models at a resistive noise gain.

A TIA with very large C_T and C_F (zero and pole far below crossover) behaves
like a resistive stage with noise gain 1 + C_T/C_F.  The datasheets state the
phase margin at the minimum stable gain (OPA818: about 50 deg at 7 V/V,
p16; OPA855: 62 deg at 7 V/V in the text, about 74 deg from Fig 6-10).
Also prints the largest phase margin reachable in the 1-pF TIA for each part.
"""
import numpy as np

import tia_model as tm
from parts_db import PARTS
from run_analysis import open_loop_model, C_D, C_PCB_NOM

for name in ("OPA818", "OPA855", "OPA955", "ADA4817-1", "LTC6228"):
    p = PARTS[name]
    ol, *_ = open_loop_model(p)
    for g in (p["g_min"], 10.0):
        C_F = 100e-12
        C_T = (g - 1) * C_F
        m = tm.loop_metrics(ol, 2000.0, C_T, C_F)
        print(f"{name:10s} resistive noise gain {g:4.1f}: f_c = {m['f_c']/1e6:7.1f} MHz, PM = {m['pm_deg']:5.1f} deg")
    # best achievable PM in the TIA (R_F = 2 k, nominal C_T), over stable C_F values
    C_T = C_D + C_PCB_NOM + p["c_cm"] + p["c_diff"]
    best = None
    for cf in tm.CF_SCAN:
        m = tm.loop_metrics(ol, 2000.0, C_T, cf)
        if m["stable"] and (best is None or m["pm_deg"] > best[1]["pm_deg"]):
            best = (cf, m)
    if best:
        cf, m = best
        print(f"{'':10s} best TIA PM at 2 kOhm: {m['pm_deg']:5.1f} deg at C_F = {cf*1e12:.3f} pF "
              f"(f3 = {m['f_3dB']/1e6:.0f} MHz, peaking {m['peaking_dB']:.2f} dB, |NG(fc)| = {m['ng_at_fc']:.1f})")
