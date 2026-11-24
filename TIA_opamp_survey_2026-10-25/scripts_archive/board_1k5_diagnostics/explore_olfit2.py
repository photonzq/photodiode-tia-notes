# Exploratory check for Section 4.11 of the note, kept as the record: rational fits with 0-2 zeros and 2-3 higher poles to the datasheet curve and the macromodel's A_-, and their loops against the curves'; the choice of one zero and three poles.
# Run from this folder.
"""Scratch: a rational open-loop model for the time-domain simulation, fitted to the datasheet curve and the macromodel A_-."""
import math
import sys

import numpy as np
from scipy.optimize import least_squares

from pathlib import Path as _Path
HERE = _Path(__file__).resolve().parent
ARCH = HERE.parent
sys.path.insert(0, str(ARCH))
import case_studies as cs
import compare_opa846_1k5_board as cb
import tia_model as tm

R_F = 1500.0
N_DELAY = 10


class Rational:
    def __init__(self, a0, fp1, zeros, poles, tau, n_delay=N_DELAY):
        self.a0, self.fp1, self.zeros, self.poles, self.tau, self.n = a0, fp1, tuple(zeros), tuple(poles), tau, n_delay

    def A(self, f):
        s = 2j * np.pi * np.asarray(f, dtype=float)
        a = self.a0 / (1 + s / (2 * np.pi * self.fp1))
        for z in self.zeros:
            a = a * (1 + s / (2 * np.pi * z))
        for p in self.poles:
            a = a / (1 + s / (2 * np.pi * p))
        if self.tau > 0:
            a = a / (1 + s * self.tau / self.n) ** self.n
        return a


def fit(f, g_db, ph, nz, npl, fmin=1e6, fmax=1.2e9, w_band=(80e6, 700e6)):
    a0 = 10 ** (g_db[np.argmin(f)] / 20)
    sel = (f >= 3e6) & (f <= 30e6)
    gbw0 = float(np.median(10 ** (g_db[sel] / 20) * f[sel])) if sel.any() else 1.5e9
    m = (f >= fmin) & (f <= fmax)
    fm, gm, pm = f[m], g_db[m], ph[m]
    w = np.where((fm >= w_band[0]) & (fm <= w_band[1]), 3.0, 1.0)

    def unpack(x):
        fp1 = 10 ** x[0]
        zs = [10 ** v for v in x[1:1 + nz]]
        ps = [10 ** v for v in x[1 + nz:1 + nz + npl]]
        tau = x[-1] * 1e-12
        return Rational(a0, fp1, zs, ps, tau)

    def resid(x):
        r = unpack(x)
        a = r.A(fm)
        rg = (20 * np.log10(np.abs(a)) - gm) * w
        php = np.degrees(np.unwrap(np.angle(a)))
        ok = ~np.isnan(pm)
        rp = (php[ok] - pm[ok]) / 6.0 * w[ok]
        return np.concatenate([rg, rp])

    best = None
    for zs0 in ([300e6, 600e6, 1000e6][:nz],):
        for ps0 in ([800e6, 1500e6, 3000e6, 5000e6][:npl],):
            for tau0 in (100.0, 250.0, 400.0):
                x0 = [math.log10(gbw0 / a0)] + [math.log10(v) for v in zs0] + [math.log10(v) for v in ps0] + [tau0]
                lb = [x0[0] - 1] + [7.5] * nz + [7.5] * npl + [0.0]
                ub = [x0[0] + 1] + [10.5] * nz + [11.0] * npl + [800.0]
                sol = least_squares(resid, x0, bounds=(lb, ub))
                if best is None or sol.cost < best.cost:
                    best = sol
    r = unpack(best.x)
    a = r.A(fm)
    eg = 20 * np.log10(np.abs(a)) - gm
    php = np.degrees(np.unwrap(np.angle(a)))
    ok = ~np.isnan(pm)
    return r, eg, php[ok] - pm[ok], fm


an = cs.Analytic("OPA846")
ol = an.ol
mac = cb.macro_open_loop(str(ARCH.parent / "spice" / "runs" / "aol" / "OPA846_inverting" / "aol.txt"))
cases = {"datasheet": (ol, ol.f, ol.g_db, ol.ph_deg, [(6.08e-12, 0.398e-12), (6.08e-12, 0.937e-12)]),
         "macromodel": (mac, mac.f, mac.g_db, mac.ph_deg, [(7.43e-12, 0.318e-12), (7.43e-12, 0.864e-12)])}
for name, (ref, f, g, p, designs) in cases.items():
    print(f"=== {name}: {len(f)} points, {f.min():.3g}-{f.max():.3g} Hz")
    for nz, npl in ((0, 2), (1, 2), (1, 3), (2, 3)):
        r, eg, ep, fm = fit(np.asarray(f), np.asarray(g), np.asarray(p, dtype=float), nz, npl)
        band = (fm >= 80e6) & (fm <= 700e6)
        print(f" zeros {nz} poles {npl}: fp1 {r.fp1 / 1e3:.1f} kHz (GBW {r.a0 * r.fp1 / 1e6:.0f} MHz), zeros {[round(z / 1e6) for z in r.zeros]}, "
              f"poles {[round(q / 1e6) for q in r.poles]} MHz, tau {r.tau * 1e12:.0f} ps; rms {np.sqrt(np.mean(eg ** 2)):.2f} dB "
              f"{np.sqrt(np.mean(ep ** 2)):.2f} deg; 80-700 MHz max |dB| {np.max(np.abs(eg[band])):.2f}")
        for ct, cf in designs:
            a = tm.loop_metrics(ref, R_F, ct, cf)
            b = tm.loop_metrics(r, R_F, ct, cf)
            print(f"    C_T {ct * 1e12:.2f} C_F {cf * 1e12:.3f}: ref f_c {a['f_c'] / 1e6:.1f} PM {a['pm_deg']:.2f} GM {a['gm_dB']:.1f} pk {a['peaking_dB']:.2f} f3 {a['f_3dB'] / 1e6:.0f}; "
                  f"fit f_c {b['f_c'] / 1e6:.1f} PM {b['pm_deg']:.2f} GM {b['gm_dB']:.1f} pk {b['peaking_dB']:.2f} f3 {b['f_3dB'] / 1e6:.0f}")
