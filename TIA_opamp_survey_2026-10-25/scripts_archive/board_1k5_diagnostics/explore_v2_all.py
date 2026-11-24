# Exploratory check for Section 4.11 of the note, kept as the record: the capacitance to add for every stable fit of Table 4.4; superseded by second_board_section.
# Run from this folder.
import math, sys
import numpy as np
from pathlib import Path as _Path
HERE = _Path(__file__).resolve().parent
ARCH = HERE.parent
sys.path.insert(0, str(ARCH))
import case_studies as cs, tia_model as tm, compare_opa846_1k5_board as cb
an = cs.Analytic("OPA846"); R_F = 1500.0
mac = cb.macro_open_loop(str(ARCH.parent / "spice" / "runs" / "aol" / "OPA846_inverting" / "aol.txt"))
fits = [("datasheet","rc",an.ol,6.08e-12,0.398e-12),("datasheet","rc2",an.ol,5.88e-12,0.354e-12),("datasheet","rc1",an.ol,5.98e-12,0.354e-12),("datasheet","none",an.ol,6.20e-12,0.450e-12),
        ("macro","rc",mac,7.43e-12,0.318e-12),("macro","rc2",mac,7.20e-12,0.276e-12),("macro","rc1",mac,7.33e-12,0.274e-12),("macro","none",mac,7.53e-12,0.366e-12)]
def cf_for(ol, ct, target):
    lo, hi = 0.05e-12, 3e-12
    for _ in range(40):
        mid = 0.5*(lo+hi); lo, hi = (lo, mid) if tm.loop_metrics(ol, R_F, ct, mid)["peaking_dB"] <= target else (mid, hi)
    return hi
for name, kind, ol, ct, cfp in fits:
    out = []
    for target in (0.01, 0.1, 1.0, 3.0):
        c = cf_for(ol, ct, target); m = tm.loop_metrics(ol, R_F, ct, c)
        out.append(f"{target} dB: +{(c-cfp)*1e12:.3f} (tot {c*1e12:.3f}, PM {m['pm_deg']:.1f}, f3 {m['f_3dB']/1e6:.0f})")
    print(f"{name:9s} {kind:4s}: " + "; ".join(out) + f"; G_min edge tot {ct/6*1e12:.3f} (+{(ct/6-cfp)*1e12:.3f})")
