# Exploratory check for Section 4.11 of the note, kept as the record: the second board: phase margin, peaking and bandwidth against the total C_F in the two input-pole fits, the C_F for 0.01-3 dB and 45-60 deg; superseded by compare_opa846_1k5_board.second_board_section.
# Run from this folder.
"""Scratch exploration: second-board C_F scan and noise-location fits (before folding into the archived script)."""
import math
import sys

import numpy as np

from pathlib import Path as _Path
HERE = _Path(__file__).resolve().parent
ARCH = HERE.parent
sys.path.insert(0, str(ARCH))
import compare_opa846_1k5_board as cb
import case_studies as cs
import tia_model as tm

DATA = str(ARCH.parent / "data" / "measurements" / "opa846_1k5_board_per_MHz.csv")
AOL = str(ARCH.parent / "spice" / "runs" / "aol" / "OPA846_inverting" / "aol.txt")
an = cs.Analytic("OPA846")
models = {"datasheet": (an.ol, 6.08e-12, 0.398e-12), "macromodel": (cb.macro_open_loop(AOL), 7.43e-12, 0.318e-12)}
R_F = 1500.0


def peak_db(ol, ct, cf, h=None, f=np.linspace(1e6, 1.5e9, 6000)):
    z = np.abs(tm.tia_tf(f, ol, R_F, ct, cf)[0]) / R_F
    if h is not None:
        z = z * cb.chain(f, h)
    k = int(np.argmax(z))
    lo = np.where(z < 1 / math.sqrt(2) * z[0])[0]
    f3 = f[lo[0]] if len(lo) else float("nan")
    return 20 * math.log10(z[k] / z[0]), f[k], f3


print("=== second board: total C_F scan ===")
for name, (ol, ct, cfp) in models.items():
    print(f"--- {name}: C_T {ct * 1e12:.2f} pF, parasitic C_F {cfp * 1e12:.3f} pF, G_min rule C_F <= {ct / 6 * 1e12:.3f} pF")
    for cf in np.array([0.318, 0.398, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 1.0, 1.1, 1.2]) * 1e-12:
        m = tm.loop_metrics(ol, R_F, ct, cf)
        pk, fpk, f3 = peak_db(ol, ct, cf)
        pks, fpks, f3s = peak_db(ol, ct, cf, "rc")
        print(f"  C_F {cf * 1e12:.3f} pF (added {(cf - cfp) * 1e12:+.3f}): f_c {m['f_c'] / 1e6:.0f} MHz, PM {m['pm_deg']:.1f}, "
              f"GM {m['gm_dB']:.1f} dB, NG_hf {1 + ct / cf:.1f}; TIA peak {pk:+.2f} dB at {fpk / 1e6:.0f}, f3 {f3 / 1e6:.0f} MHz; "
              f"at scope peak {pks:+.2f} dB f3 {f3s / 1e6:.0f} MHz")
    for target in (0.01, 0.1, 1.0, 3.0):
        lo, hi = 0.05e-12, 3e-12
        for _ in range(40):
            mid = 0.5 * (lo + hi)
            ok = tm.loop_metrics(ol, R_F, ct, mid)["peaking_dB"] <= target
            lo, hi = (lo, mid) if ok else (mid, hi)
        m = tm.loop_metrics(ol, R_F, ct, hi)
        print(f"  peaking <= {target} dB: C_F {hi * 1e12:.3f} pF (added {(hi - cfp) * 1e12:.3f}), PM {m['pm_deg']:.1f}, f3 {m['f_3dB'] / 1e6:.0f} MHz")
    for pmt in (45.0, 50.0, 60.0):
        lo, hi = 0.1e-12, 3e-12
        for _ in range(40):
            mid = 0.5 * (lo + hi)
            ok = tm.loop_metrics(ol, R_F, ct, mid)["pm_deg"] >= pmt
            lo, hi = (lo, mid) if ok else (mid, hi)
        m = tm.loop_metrics(ol, R_F, ct, hi)
        print(f"  PM >= {pmt}: C_F {hi * 1e12:.3f} pF, peaking {m['peaking_dB']:.2f} dB, f3 {m['f_3dB'] / 1e6:.0f} MHz, NG_hf {1 + ct / hi:.1f}")
    cfmax = max((tm.loop_metrics(ol, R_F, ct, c)["pm_deg"], c) for c in np.linspace(0.3e-12, 3e-12, 271))
    print(f"  largest PM {cfmax[0]:.1f} deg at C_F {cfmax[1] * 1e12:.2f} pF")
    print(f"  Eq. (15) single pole flat C_F: {17.84 * math.sqrt(ct * 1e12 / (1.5 * 1750)):.3f} pF")
