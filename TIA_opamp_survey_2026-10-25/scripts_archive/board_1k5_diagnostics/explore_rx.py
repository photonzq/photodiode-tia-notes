# Exploratory check for Section 4.11 of the note, kept as the record: the gain refitted with a resistor of 0.54-6.6 kOhm from the summing node to ground (a coarse grid); compare_opa846_1k5_board.fit_rx keeps the 673-ohm case.
# Run from this folder.
"""Scratch: does a ~540-ohm resistor at the summing node fit the measured gain?  And the noise fits with C_tot held."""
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
an = cs.Analytic("OPA846")
ol = an.ol
R_F = 1500.0
b = cb.read_bins(DATA)
use = (~b["bad"]) & np.isfinite(b["G"]) & (b["f"] >= 10e6)
f, g = b["f"][use], b["G"][use]
h = cb.chain(f, "rc")


def zt_rx(ff, ct, cf, rx):
    s = 2j * np.pi * ff
    zf = R_F / (1 + s * R_F * cf)
    ng = 1 + zf * (s * ct + (1.0 / rx if rx else 0.0))
    t = ol.A(ff) / ng
    return -zf * t / (1 + t), t


def eps(ct, cf, rx):
    z = np.abs(zt_rx(f, ct, cf, rx)[0]) * h
    u = z / g
    k = np.sum(u) / np.sum(u * u)
    return float(np.sqrt(np.mean((1 - k * u) ** 2))), float(k)


def stable(ct, cf, rx):
    ff = tm.F_GRID
    t = zt_rx(ff, ct, cf, rx)[1]
    mag = np.abs(t)
    ph = np.degrees(np.unwrap(np.angle(t)))
    idx = np.where((mag[:-1] >= 1) & (mag[1:] < 1))[0]
    if not len(idx):
        return False, float("nan")
    i = idx[0]
    pm = 180 + ph[i]
    second = np.any(mag[ff > 1.2 * ff[i]] >= 1)
    return (pm > 0 and not second), pm


for rx in (None, 6600.0, 2000.0, 1000.0, 700.0, 540.0):
    best = None
    for ct in np.arange(3e-12, 12.01e-12, 0.1e-12):
        for cf in np.arange(0.1e-12, 0.8e-12, 0.01e-12):
            e, k = eps(ct, cf, rx)
            if best is None or e < best[0]:
                ok, pm = stable(ct, cf, rx)
                if ok:
                    best = (e, k, ct, cf, pm)
    e, k, ct, cf, pm = best
    print(f"R_x {rx if rx else 'none'}: eps {100 * e:.2f} %, K {k:.3f}, C_T {ct * 1e12:.2f} pF, C_F {cf * 1e12:.3f} pF, PM {pm:.1f}")
