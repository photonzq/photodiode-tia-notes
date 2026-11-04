"""Design sweep of the high-gain TIA note: every amplifier of
data/amplifiers.json on the example photodiodes of data/photodiodes.json at
R_F = 10 kOhm ... 1 GOhm. A part with max_rf (the companion note's fast parts)
is evaluated only up to that R_F.

For each design the feedback capacitance is the smallest value >= C_par
(the resistor's own capacitance, 0.1 pF baseline) that keeps the response
within 0.1 dB of maximally flat; the bandwidth, phase margin, input-referred
noise over [1 Hz, f_3dB], the excess over the feedback resistor's Johnson
noise, the dominant noise term and the DC error at 25 C and 85 C follow.

Usage:  python hg_analysis.py            (writes data/results/)
"""
from __future__ import annotations

import json
import math
import pathlib

import numpy as np

import hg_model as m

OUT = m.DATA / "results"
RFS = [1e4, 1e5, 1e6, 1e7, 1e8, 1e9]
C_PAR = 0.1e-12
C_STRAY = 1e-12
F = np.logspace(-2, 9, 2200)
F_LOW = 1.0

SOURCES = [
    m.Source("S1336-18BK (Si 1.1 mm)", 20e-12, 2e9),
    m.Source("G12180-010A (InGaAs 1 mm)", 55e-12, 125e6),
    m.Source("S1336-8BK (Si 5.8 mm)", 380e-12, 0.4e9),
    m.Source("G12180-050A (InGaAs 5 mm)", 1000e-12, 6.5e6),
    m.Source("G12183-010K (InGaAs to 2.6 um, 1 mm)", 500e-12, 14e3),
]
TERMS = ["R_F", "shunt", "i_n", "e_n_G", "e_n_C"]


def ib_at(amp: m.Amp, temp: str) -> float | None:
    """Maximum bias current at 25 C or 85 C.  At 85 C: the datasheet limit
    at 85 C (or 'at the temperature extremes'); otherwise the geometric
    interpolation between the 25 C and 125 C limits, I25^0.4 * I125^0.6;
    otherwise the 25 C limit doubled every 10 C (x 2^6)."""
    if amp.ib_max25 is None:
        return None
    if temp == "25":
        return amp.ib_max25
    if "85" in amp.ib_hot:
        return amp.ib_hot["85"]
    if "extremes" in amp.ib_hot:
        return amp.ib_hot["extremes"]
    if "125" in amp.ib_hot:
        return amp.ib_max25 ** 0.4 * amp.ib_hot["125"] ** 0.6
    return amp.ib_max25 * 2 ** 6


def design_row(amp: m.Amp, rf: float, src: m.Source) -> dict:
    d, met = m.choose_cf(amp, rf, src, C_PAR, c_stray=C_STRAY, f=F)
    noise = d.noise(F)
    f3 = met["f3"]
    tot = m.integrate(F, noise["total"], F_LOW, f3)
    floor_rf = m.integrate(F, noise["R_F"], F_LOW, f3)
    floor_det = floor_rf + m.integrate(F, noise["shunt"], F_LOW, f3)
    parts = {k: m.integrate(F, noise[k], F_LOW, f3) for k in TERMS}
    dom_band = max(parts, key=parts.get)
    idx = np.searchsorted(F, [f3 / 10, f3])
    dom_spot = []
    for i in idx:
        i = min(i, len(F) - 1)
        dom_spot.append(max(TERMS, key=lambda k: noise[k][i]))
    # mid-band noise gain (above the zero of R_F with the node capacitance) and the
    # amplifier's DC open-loop gain over it: below about 10 the loop cannot hold the
    # summing node and the bandwidth collapses (found in the SPICE checks, Chapter 9)
    c_node = src.c_d + amp.c_in + C_STRAY
    ng_mid = (c_node + met["cf"]) / met["cf"]
    row = {
        "amp": amp.name, "rf": rf, "source": src.name,
        "ng_mid": ng_mid, "a0_over_ng": amp.a0 / ng_mid,
        "cf_pF": met["cf"] * 1e12, "f3_Hz": f3, "pm_deg": met["pm"],
        "ng_at_fx": met["ng_at_fx"], "limited_by": met["limited_by"],
        "i_rms_A": math.sqrt(tot), "dN_vs_RF_dB": 10 * math.log10(tot / floor_rf),
        "dN_vs_detector_dB": 10 * math.log10(tot / floor_det),
        "share": {k: parts[k] / tot for k in TERMS},
        "dominant_in_band": dom_band, "dominant_at_f3_10": dom_spot[0],
        "dominant_at_f3": dom_spot[1],
        "stable_vs_min_gain": bool(met["ng_at_fx"] >= amp.min_gain),
        "c_known": amp.c_known,
    }
    g = (1.0 / rf) + (1.0 / src.r_sh)
    for t in ("25", "85"):
        ib = ib_at(amp, t)
        vos = amp.vos_max
        if ib is None or vos is None:
            row[f"i_err_{t}_A"] = None
        else:
            row[f"i_err_{t}_A"] = ib + vos * g
    return row


def gain_table() -> list[dict]:
    rows = []
    for rf in RFS:
        rows.append({
            "rf": rf,
            "johnson_A_rtHz": math.sqrt(m.FOUR_KT / rf),
            "i_shot_equals_johnson_A": 2 * m.K_B * m.T_REF / (m.Q_E * rf),
            "i_max_10V_A": 10.0 / rf, "i_max_2V4_A": 2.4 / rf,
            "f_res_0p05pF": 1 / (2 * math.pi * rf * 0.05e-12),
            "f_res_0p1pF": 1 / (2 * math.pi * rf * 0.1e-12),
            "f_res_0p2pF": 1 / (2 * math.pi * rf * 0.2e-12),
        })
    return rows


def amp_merits(amps: dict[str, m.Amp]) -> list[dict]:
    rows = []
    for a in amps.values():
        f_in = min(p[0] for p in a.in_pts)
        i_n = float(a.in_(np.array([max(f_in, 1e3) if f_in < 1e3 else f_in]))[0])
        e1k = float(a.en(np.array([1e3]))[0])
        e10 = float(a.en(np.array([10.0]))[0])
        ew = float(a.en(np.array([1e5]))[0])
        rows.append({
            "amp": a.name, "input": a.input, "gbw_MHz": a.gbw / 1e6,
            "min_gain": a.min_gain, "c_in_pF": a.c_in * 1e12 if a.c_known else None,
            "en_10Hz": e10 * 1e9, "en_1kHz": e1k * 1e9, "en_100kHz": ew * 1e9,
            "in_fA": i_n * 1e15,
            "rf_crit_Ohm": m.FOUR_KT / i_n ** 2,
            "r_opt_Ohm": e1k / i_n,
            "ib_max25_fA": a.ib_max25 * 1e15 if a.ib_max25 else None,
            "ib_85_fA": (ib_at(a, "85") or 0) * 1e15 or None,
            "vos_max_uV": a.vos_max * 1e6 if a.vos_max else None,
        })
    return rows


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    amps = m.load_amps()
    (OUT / "gain_table.json").write_text(json.dumps(gain_table(), indent=1))
    (OUT / "amp_merits.json").write_text(json.dumps(amp_merits(amps), indent=1))
    rows = []
    for src in SOURCES:
        for rf in RFS:
            for a in amps.values():
                if a.max_rf is not None and rf > a.max_rf * 1.0001:
                    continue
                rows.append(design_row(a, rf, src))
    (OUT / "designs.json").write_text(json.dumps(rows, indent=1))
    print(f"{len(rows)} designs written to {OUT}")


if __name__ == "__main__":
    main()
