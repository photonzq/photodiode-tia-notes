# Exploratory check for Section 4.11 of the note, kept as the record: tia_model.fit_open_loop (two poles and a delay) on the OPA846 curve: its loop misses the curve's phase margin by 2-3 deg, the reason for the rational fit of tia_pulse_response.py.
# Run from this folder.
import math, sys
import numpy as np
from pathlib import Path as _Path
HERE = _Path(__file__).resolve().parent
ARCH = HERE.parent
sys.path.insert(0, str(ARCH))
import case_studies as cs, tia_model as tm, compare_opa846_1k5_board as cb
an = cs.Analytic("OPA846"); ol = an.ol; R_F = 1500.0
pts = list(zip(ol.f, ol.g_db, ol.ph_deg))
print("curve points:", len(pts), "f range", ol.f.min()/1e6, ol.f.max()/1e6, "MHz")
for p in pts: print(f"  {p[0]/1e6:9.3f} MHz {p[1]:6.2f} dB {p[2]:7.1f} deg")
for nhi in (2, 3):
    m, rg, rp = tm.fit_open_loop(pts, n_hi_poles=nhi, use_delay=True)
    print(f"n_hi {nhi}: A0 {m.A0:.1f}, f_p1 {m.f_p1/1e3:.1f} kHz, GBW {m.gbw/1e6:.0f} MHz, hi {[round(x/1e6) for x in m.f_poles_hi]} MHz, tau {m.tau*1e12:.0f} ps; rms {rg:.2f} dB {rp:.2f} deg")
    for ct, cf in ((6.08e-12, 0.398e-12), (6.08e-12, 0.937e-12)):
        a = tm.loop_metrics(ol, R_F, ct, cf); b = tm.loop_metrics(m, R_F, ct, cf)
        print(f"   C_F {cf*1e12:.3f}: curve f_c {a['f_c']/1e6:.1f} PM {a['pm_deg']:.2f} pk {a['peaking_dB']:.2f}; fit f_c {b['f_c']/1e6:.1f} PM {b['pm_deg']:.2f} pk {b['peaking_dB']:.2f}")
