# Exploratory check for Section 4.11 of the note, kept as the record: the board's gain refitted with the rational datasheet models, and the capacitance to add in each; superseded by tia_pulse_response.note_cases.
# Run from this folder.
import math, sys
import numpy as np
from pathlib import Path as _Path
HERE = _Path(__file__).resolve().parent
ARCH = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ARCH))
import importlib.util
spec = importlib.util.spec_from_file_location("ex2", str(HERE / "explore_olfit2.py"))
import case_studies as cs, tia_model as tm, compare_opa846_1k5_board as cb
src = open(spec.origin, encoding="utf-8").read().split("an = cs.Analytic")[0]
exec(src)
an = cs.Analytic("OPA846"); ol = an.ol
b = cb.read_bins(str(ARCH.parent / "data" / "measurements" / "opa846_1k5_board_per_MHz.csv"))
use = (~b["bad"]) & np.isfinite(b["G"]) & (b["f"] >= 10e6)
f, g = b["f"][use], b["G"][use]
h = cb.chain(f, "rc")
for nz, npl in ((1, 2), (1, 3), (2, 3)):
    r, eg, ep, fm = fit(np.asarray(ol.f), np.asarray(ol.g_db), np.asarray(ol.ph_deg, dtype=float), nz, npl)
    res = cb.fit(f, g, r, h, True)
    m = res["m"]
    # flat increment in this description
    def pk(cf): return tm.loop_metrics(r, R_F, res["ct"], cf)["peaking_dB"]
    out = []
    for target in (0.01, 1.0):
        lo, hi = 0.05e-12, 3e-12
        for _ in range(40):
            mid = 0.5*(lo+hi); lo, hi = (lo, mid) if pk(mid) <= target else (mid, hi)
        mm = tm.loop_metrics(r, R_F, res["ct"], hi)
        out.append(f"{target} dB at +{(hi-res['cf'])*1e12:.3f} pF (PM {mm['pm_deg']:.1f}, f3 {mm['f_3dB']/1e6:.0f})")
    print(f"z{nz} p{npl}: refit C_T {res['ct']*1e12:.3f} C_F {res['cf']*1e12:.3f} K {res['k']:.3f} eps {100*res['eps']:.2f} %: f_c {m['f_c']/1e6:.1f} PM {m['pm_deg']:.2f} GM {m['gm_dB']:.1f} pk {res['pk']:.2f} dB at {res['fpk']/1e6:.0f}; " + "; ".join(out))
