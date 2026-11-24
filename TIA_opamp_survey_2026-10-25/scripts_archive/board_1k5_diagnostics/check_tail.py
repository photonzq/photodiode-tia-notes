# Exploratory check for Section 4.11 of the note, kept as the record: the inverse transform of the curve's Z_T over the window: its precursor before t = 0; superseded by the precursor printed by tia_pulse_response.run_case.
# Run from this folder.
import sys, numpy as np
from pathlib import Path as _Path
HERE = _Path(__file__).resolve().parent
ARCH = HERE.parent
sys.path.insert(0, str(ARCH))
import case_studies as cs, tia_pulse_response as tp
ol = cs.Analytic("OPA846").ol
for name, o in (("curve", ol),):
    t, h, hs = tp.linear_impulse(o, 1500.0, 6.08e-12, 0.398e-12)
    pk = np.max(np.abs(h))
    for a, b in ((0, 5e-9), (5e-9, 20e-9), (20e-9, 40e-9), (40e-9, 80e-9), (80e-9, 200e-9), (200e-9, 350e-9), (350e-9, 390e-9), (390e-9, 400e-9)):
        m = (t >= a) & (t < b)
        print(f"{name} {a*1e9:5.0f}-{b*1e9:5.0f} ns: max |h| {np.max(np.abs(h[m]))/pk:.2e} of peak, mean {np.mean(h[m])/pk:+.2e}")
# DC and low-frequency behaviour of the curve
f = np.array([1e2, 1e3, 1e4, 1e5, 1e6, 3e6, 1e7])
A = ol.A(f)
print("curve |A| dB and phase at", f, 20*np.log10(np.abs(A)), np.degrees(np.angle(A)))
