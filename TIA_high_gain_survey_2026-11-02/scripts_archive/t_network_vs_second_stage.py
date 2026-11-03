"""A T-network in the feedback path against a single resistor and against a smaller
resistor followed by a voltage stage, all for 1 GOhm of transimpedance (3 November 2026).

The circuit model is that of the note (hg_model): Z_T = -1/(y_f + Y_n/A) and the
input-referred noise S_i = 4kT Re{y11} + 4kT/R_sh + i_n^2 + e_n^2 |Y_s + y11|^2, with the
feedback network given by its two-port admittances.  For a T with the arm Z1 (R1 in parallel
with C1) at the summing node, the arm R2 at the output and R3 to ground,
    D = Z1 R2 + R2 R3 + R3 Z1,   y11 = (R2 + R3)/D,   y_f = R3/D,
so 1/y_f = Z1 (1 + R2/R3) + R2.  The voltage stage after a TIA is an ideal gain k with a
single pole at GBW2/k and its own input noise e_n2, which refers to the TIA's input as
e_n2/|Z_T1|.  Amplifier: ADA4625-1; photodiode: S1336-18BK (20 pF, 2 GOhm); C_par 0.1 pF.

Usage:  python t_network_vs_second_stage.py
"""
from __future__ import annotations

import dataclasses
import math

import numpy as np

import hg_model as m

AMP = m.load_amps()["ADA4625-1"]
SRC = m.Source("S1336-18BK", 20e-12, 2e9)
C_PAR = 0.1e-12
F = np.logspace(-1, 8, 2700)
FLOOR_1G = m.FOUR_KT / 1e9 + m.FOUR_KT / SRC.r_sh        # A^2/Hz, a real 1-GOhm resistor plus the diode
VOS = 80e-6                                                # V, ADA4625-1 maximum offset (note, Section 3.3)


@dataclasses.dataclass
class TDesign(m.Design):
    r2: float = 9.9e3
    r3: float = 100.0

    def y_fb(self, w):
        z1 = 1.0 / (1.0 / self.rf + 1j * w * self.cf)
        d = z1 * self.r2 + self.r2 * self.r3 + self.r3 * z1
        return (self.r2 + self.r3) / d, -self.r3 / d


def flat_cf(make, c_min: float) -> m.Design:
    """Smallest C1 >= c_min that keeps the response within 0.1 dB of flat (the note's rule)."""
    for cf in c_min * np.logspace(0, 3, 600):
        d = make(cf)
        if m.response_metrics(d, F)["peak_db"] <= 0.1:
            return d
    raise RuntimeError("no flat design")


def band_noise(s_i: np.ndarray, f3: float) -> float:
    """Excess over the real 1-GOhm floor in [1 Hz, f3], dB (Eq. (16) of the note)."""
    return 10 * math.log10(m.integrate(F, s_i, 1.0, f3) / (FLOOR_1G * (f3 - 1.0)))


rows = []
# (a) a single 1-GOhm resistor with its own 0.1 pF
d = flat_cf(lambda cf: m.Design(AMP, 1e9, cf, SRC), C_PAR)
met = m.response_metrics(d, F)
rows.append(("1 GOhm resistor", met["f3"], d.noise(F)["total"], VOS * (1 + 1e9 / SRC.r_sh), d.cf))

# (b) T-networks: R1 with 0.1 pF of its own, R2/R3 = k - 1, for k = 10 and 100
for r1, k in ((1e8, 10), (1e7, 100)):
    r3 = 100.0
    d = flat_cf(lambda cf: TDesign(AMP, r1, cf, SRC, r2=(k - 1) * r3, r3=r3), C_PAR)
    met = m.response_metrics(d, F)
    zt0 = abs(d.zt(np.array([0.1]))[0])
    ng_dc = 1 + (k - 1) + (r1 * k) / SRC.r_sh               # output offset gain at DC
    rows.append((f"T: {r1 / 1e6:g} MOhm x {k}", met["f3"], d.noise(F)["total"], VOS * ng_dc, d.cf,
                 zt0))

# (c) a TIA with R1 followed by a voltage stage of gain k (OPA828-class, 45 MHz, 4 nV/rtHz)
for r1, k in ((1e8, 10), (1e7, 100)):
    d = flat_cf(lambda cf: m.Design(AMP, r1, cf, SRC), C_PAR)
    zt1 = d.zt(F)
    p2 = 1.0 / (1.0 + 1j * F / (45e6 / k))
    zt = np.abs(zt1 * p2)
    f3 = float(F[np.nonzero(zt < zt[0] / math.sqrt(2.0))[0][0]])
    s_i = d.noise(F)["total"] + (4e-9) ** 2 / np.abs(zt1) ** 2
    rows.append((f"{r1 / 1e6:g} MOhm + gain {k}", f3, s_i, VOS * (1 + r1 / SRC.r_sh) * k + VOS * k, d.cf))

print(f"Floor of a real 1-GOhm resistor with the diode: {math.sqrt(FLOOR_1G) * 1e15:.2f} fA/rtHz")
for r in rows:
    name, f3, s_i, vos_out, cf = r[:5]
    s100 = float(np.interp(100.0, F, s_i))
    extra = f", |Z_T(0)| = {r[5] / 1e9:.3f} GOhm" if len(r) > 5 else ""
    print(f"{name:20s}: C_F {cf * 1e12:6.3f} pF, f3 {f3 / 1e3:7.2f} kHz, noise at 100 Hz "
          f"{math.sqrt(s100) * 1e15:6.2f} fA/rtHz, excess over the 1-GOhm floor in band {band_noise(s_i, f3):5.1f} dB, "
          f"output offset {vos_out * 1e3:6.2f} mV{extra}")
