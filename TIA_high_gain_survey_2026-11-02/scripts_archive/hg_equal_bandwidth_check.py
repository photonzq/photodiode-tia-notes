"""Excess noise of OPA1656 and OPA2156 at equal bandwidth (2 November 2026).

OPA1656's designs in the sweep use the smallest C_F within 0.1 dB of maximally flat, which
with its 53-MHz gain-bandwidth gives about twice OPA2156's bandwidth and more noise in that
wider band.  This script raises OPA1656's C_F until its bandwidth equals OPA2156's at
100 kOhm, 1 MOhm and 10 MOhm on the 20-pF photodiode, and compares the excess noise of
Eq. (16) over [1 Hz, f_-3dB].

Usage:  python hg_equal_bandwidth_check.py
"""
import math

import numpy as np

import hg_model as m

amps = m.load_amps()
src = m.Source("S1336-18BK", 20e-12, 2e9)
f = np.logspace(-2, 9, 2200)


def excess(d: m.Design, f3: float) -> float:
    fn = np.logspace(0, math.log10(f3), 400)
    tot = m.integrate(fn, d.noise(fn)["total"], 1.0, f3)
    floor = (m.FOUR_KT / d.rf + m.FOUR_KT / src.r_sh) * (f3 - 1.0)
    return 10 * math.log10(tot / floor)


def held_to(part: str, rf: float, target: float) -> tuple[float, dict, m.Design]:
    """The C_F that gives the part the bandwidth target, by bisection."""
    lo, hi = 0.1e-12, 50e-12
    for _ in range(60):
        cf = math.sqrt(lo * hi)
        f3 = m.response_metrics(m.Design(amps[part], rf, cf, src), f)["f3"]
        lo, hi = (cf, hi) if f3 > target else (lo, cf)
    d = m.Design(amps[part], rf, cf, src)
    return cf, m.response_metrics(d, f), d


print("OPA1656 held to OPA2156's own (smallest stable C_F) bandwidth:")
for rf in (1e5, 1e6, 1e7):
    d2, m2 = m.choose_cf(amps["OPA2156"], rf, src, 0.1e-12)
    target = m2["f3"]
    cf, met, d1 = held_to("OPA1656", rf, target)
    print(f"{rf:.0e}: OPA2156 C_F {d2.cf * 1e12:.3f} pF, f3 {target / 1e3:.1f} kHz, dN {excess(d2, target):.2f} dB | "
          f"OPA1656 C_F {cf * 1e12:.3f} pF, f3 {met['f3'] / 1e3:.1f} kHz, peak {met['peak_db']:.2f} dB, "
          f"dN {excess(d1, met['f3']):.2f} dB")

print("Both held to round bandwidths:")
for rf, target in ((1e5, 1e6), (1e6, 330e3), (1e7, 100e3)):
    cells = []
    for part in ("OPA1656", "OPA2156"):
        cf, met, d = held_to(part, rf, target)
        cells.append(f"{part} C_F {cf * 1e12:.3f} pF, f3 {met['f3'] / 1e3:.1f} kHz, dN {excess(d, met['f3']):.2f} dB")
    print(f"{rf:.0e}, {target / 1e3:g} kHz: " + " | ".join(cells))
