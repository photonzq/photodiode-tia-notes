"""Medium gain (Section 6.9, 4 November 2026): every op amp of the sweep held to common bandwidths at 10 kOhm and
100 kOhm on the 20-pF photodiode, and the model's designs on the companion note's 1-pF node for the cross-check
with that note's own open-loop model.

1. Equal bandwidth. Each part's feedback capacitance is raised from the sweep's value (the smallest C_F within
   0.1 dB of maximally flat) until its -3 dB bandwidth equals the target, by bisection, as in
   hg_equal_bandwidth_check.py. The excess noise is Eq. (16) over [1 Hz, f_target] against the floor of the
   resistor and the photodiode. A part whose own bandwidth falls short of the target gets a dash, and one whose DC
   open-loop gain is less than ten times the mid-band noise gain (C_T + C_F)/C_F gets "A" (Section 3.1).
   Writes data/results/note_tables/table_6_8.md.
2. Cross-check. The designs of the sweep's rule for OPA855, OPA955, OPA858, OPA818 and LMH6629 on the companion's
   node, a 1-pF photodiode pair with 0.35 pF of board capacitance, at 2 kOhm and 10 kOhm: C_F, bandwidth, phase
   margin and the integrated input-referred noise. Writes data/results/medium_gain.json.

Usage: python hg_medium_gain.py
"""
import json
import math

import numpy as np

import hg_model as m
from hg_analysis import C_PAR, C_STRAY
from hg_tables import ORDER, eng

amps = m.load_amps()
SRC = m.Source("S1336-18BK", 20e-12, 2e9)
F = np.logspace(-2, 9.5, 2600)
CASES = [(1e4, (3e6, 10e6, 30e6)), (1e5, (1e6, 3e6, 10e6))]
CROSS_PARTS = ("OPA855", "OPA955", "OPA858", "OPA818", "LMH6629")


def excess(d: m.Design, f3: float, src: m.Source) -> float:
    fn = np.logspace(0, math.log10(f3), 400)
    tot = m.integrate(fn, d.noise(fn)["total"], 1.0, f3)
    floor = (m.FOUR_KT / d.rf + m.FOUR_KT / src.r_sh) * (f3 - 1.0)
    return 10 * math.log10(tot / floor)


def held_to(amp: m.Amp, rf: float, target: float, cf_min: float) -> tuple[float, dict, m.Design]:
    """The C_F >= cf_min that gives the part the bandwidth target, by bisection."""
    lo, hi = cf_min, 200e-12
    for _ in range(60):
        cf = math.sqrt(lo * hi)
        f3 = m.response_metrics(m.Design(amp, rf, cf, SRC, c_stray=C_STRAY), F)["f3"]
        lo, hi = (cf, hi) if f3 > target else (lo, cf)
    d = m.Design(amp, rf, cf, SRC, c_stray=C_STRAY)
    return cf, m.response_metrics(d, F), d


def equal_bandwidth() -> tuple[str, list]:
    rows, cells_of = [], {}
    for name in ORDER:
        if "composite" in name:
            continue
        a = amps[name]
        for rf, targets in CASES:
            if a.max_rf is not None and rf > a.max_rf * 1.0001:
                continue
            d0, met0 = m.choose_cf(a, rf, SRC, C_PAR, c_stray=C_STRAY, f=F)
            for target in targets:
                if met0["f3"] < target * 0.999:
                    cells_of[(name, rf, target)] = "–"
                    continue
                cf, met, d = held_to(a, rf, target, met0["cf"])
                c_node = SRC.c_d + a.c_in + C_STRAY
                a_flag = " A" if a.a0 / ((c_node + cf) / cf) < 10 else ""
                dn = excess(d, met["f3"], SRC)
                cells_of[(name, rf, target)] = f"{dn:.1f}{a_flag}"
                rows.append({"amp": name, "rf": rf, "target_Hz": target, "cf_pF": cf * 1e12, "f3_Hz": met["f3"],
                             "peak_dB": met["peak_db"], "pm_deg": met["pm"], "dN_dB": dn, "a_flag": bool(a_flag)})
    head = ("| Part | " + " | ".join(f"{eng(rf, 'Ω')}, {eng(t, 'Hz')}" for rf, ts in CASES for t in ts) + " |\n"
            "|---|" + "---|" * sum(len(ts) for _, ts in CASES))
    body = []
    for name in ORDER:
        if "composite" in name:
            continue
        cells = [cells_of.get((name, rf, t), "–") for rf, ts in CASES for t in ts]
        if all(c == "–" for c in cells):
            continue
        body.append(f"| {name} | " + " | ".join(cells) + " |")
    return head + "\n" + "\n".join(body), rows


def cross_check() -> list:
    node = m.Source("companion 1-pF node", 1e-12, math.inf)
    out = []
    for name in CROSS_PARTS:
        for rf in (2e3, 1e4):
            d, met = m.choose_cf(amps[name], rf, node, C_PAR, c_stray=0.35e-12, f=F)
            fn = np.logspace(0, math.log10(met["f3"]), 400)
            tot = m.integrate(fn, d.noise(fn)["total"], 1.0, met["f3"])
            out.append({"amp": name, "rf": rf, "cf_pF": met["cf"] * 1e12, "f3_Hz": met["f3"], "pm_deg": met["pm"],
                        "ng_at_fx": met["ng_at_fx"], "limited_by": met["limited_by"],
                        "i_rms_A": math.sqrt(tot), "i_rms_floor_A": math.sqrt(m.FOUR_KT / rf * met["f3"])})
    return out


def main() -> None:
    table, rows = equal_bandwidth()
    out = m.DATA / "results" / "note_tables" / "table_6_8.md"
    out.write_text(table + "\n", encoding="utf-8", newline="\n")
    cross = cross_check()
    (m.DATA / "results" / "medium_gain.json").write_text(json.dumps({"equal_bandwidth": rows, "cross_check": cross},
                                                                    indent=1), encoding="utf-8")
    print(table)
    for r in cross:
        print(f"{r['amp']:8} {r['rf'] / 1e3:4.0f} kOhm: C_F {r['cf_pF']:.3f} pF, f3 {r['f3_Hz'] / 1e6:6.1f} MHz, "
              f"PM {r['pm_deg']:4.1f} deg, NG_x {r['ng_at_fx']:5.1f}, {r['limited_by']}, "
              f"{r['i_rms_A'] * 1e9:.1f} nA rms (floor {r['i_rms_floor_A'] * 1e9:.1f} nA)")


if __name__ == "__main__":
    main()
