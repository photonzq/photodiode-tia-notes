# Exploratory check for Section 4.11 of the note, kept as the record: the capacitance to add with a 540-ohm resistor at the node; superseded by second_board_section.
# Run from this folder.
import math, sys
import numpy as np
from pathlib import Path as _Path
HERE = _Path(__file__).resolve().parent
ARCH = HERE.parent
sys.path.insert(0, str(ARCH))
import case_studies as cs
an = cs.Analytic("OPA846"); ol = an.ol; R_F = 1500.0
ff = np.linspace(1e6, 1.5e9, 8000)
def zt(ct, cf, rx):
    s = 2j*np.pi*ff; zf = R_F/(1+s*R_F*cf); ng = 1 + zf*(s*ct + (1/rx if rx else 0)); t = ol.A(ff)/ng
    return np.abs(-zf*t/(1+t))
def pk(ct, cf, rx):
    z = zt(ct, cf, rx); return 20*math.log10(z.max()/z[0])
for (ct, cfp, rx) in ((5.50e-12, 0.20e-12, 540.0), (6.08e-12, 0.398e-12, None)):
    for target in (0.01, 1.0):
        lo, hi = 0.05e-12, 3e-12
        for _ in range(40):
            mid = 0.5*(lo+hi); lo, hi = (lo, mid) if pk(ct, mid, rx) <= target else (mid, hi)
        print(f"C_T {ct*1e12:.2f} R_x {rx}: peaking <= {target} dB at C_F {hi*1e12:.3f} pF, added {(hi-cfp)*1e12:.3f} pF")
