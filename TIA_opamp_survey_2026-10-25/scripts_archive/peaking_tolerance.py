"""Designs that accept transimpedance peaking (equalized later) but must never oscillate.

Usage: python peaking_tolerance.py <out_json>     (all parts, writes JSON)
       python peaking_tolerance.py bench          (the 1.2-kOhm bench board only)

For each part, feedback resistor and total feedback capacitance C_F, evaluate
the nominal loop (C_D = 1 pF, C_PCB = 0.35 pF) and all corners of
  - C_F +/- 0.1 pF                   (resistor and pad parasitic),
  - C_T +/- 0.2 pF                   (photodiode and board),
  - open-loop gain scaled to the datasheet GBW MIN (or -2 dB where no MIN is
    given) and +1.5 dB              (part-to-part and temperature spread),
and report the worst-case phase margin and gain margin, whether every corner
is stable (single crossing, positive phase margin), the range of the
transimpedance peak (height and frequency) that an equalizer would have to
follow, the input-referred noise (central model) and the unfiltered output
noise.
"""
import itertools
import json
import sys

import numpy as np

import tia_model as tm
from parts_db import PARTS
from run_analysis import C_D, C_PCB_NOM, F_NOISE, noise_inputs, open_loop_model

GAIN_LO_DB = {"OPA846": 20 * np.log10(1275 / 1750), "OPA847": 20 * np.log10(3100 / 3900)}
CASES = {
    "OPA846": (0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.6, 0.74, 0.86),
    "OPA818": (0.1, 0.15, 0.2, 0.3, 0.4, 0.49, 0.55, 0.62),
    "OPA847": (0.1, 0.15, 0.2, 0.3, 0.35, 0.45),
    "OPA955": (0.1, 0.15, 0.2, 0.25, 0.3, 0.4),
    "OPA855": (0.15, 0.2, 0.25, 0.3, 0.35),
}
R_LIST = (1200.0, 1500.0, 2000.0)
F_OUT = np.logspace(5, np.log10(3e9), 4000)


class Scaled:
    """Open-loop model with the magnitude scaled by a constant (dB)."""
    def __init__(self, base, db):
        self.base, self.k = base, 10 ** (db / 20)

    def A(self, f):
        return self.k * self.base.A(f)


def main(out_path):
    res = {}
    for name, cfs in CASES.items():
        p = PARTS[name]
        ol, *_ = open_loop_model(p)
        nz = noise_inputs(p)
        lo_db = GAIN_LO_DB.get(name, -2.0)
        models = {"nominal": ol, "gain low": Scaled(ol, lo_db), "gain high": Scaled(ol, +1.5)}
        C_T0 = C_D + C_PCB_NOM + p["c_cm"] + p["c_diff"]
        for R_F in R_LIST:
            for cf in cfs:
                nom = tm.loop_metrics(ol, R_F, C_T0, cf * 1e-12)
                worst_pm, worst_gm, all_stable = np.inf, np.inf, True
                pk_rng, fpk_rng = [], []
                for (mk, olm), dcf, dct in itertools.product(models.items(), (-0.1, 0.0, 0.1), (-0.2, 0.0, 0.2)):
                    c = max(cf + dcf, 0.05)
                    m = tm.loop_metrics(olm, R_F, C_T0 + dct * 1e-12, c * 1e-12)
                    if not m["stable"]:
                        all_stable = False
                        continue
                    worst_pm = min(worst_pm, m["pm_deg"])
                    if np.isfinite(m["gm_dB"]):
                        worst_gm = min(worst_gm, m["gm_dB"])
                    pk_rng.append(m["peaking_dB"])
                    fpk_rng.append(m["f_peak"])
                comp = tm.noise_components(F_NOISE, R_F, C_T0, cf * 1e-12, nz)
                S_ref = np.full_like(F_NOISE, 4 * tm.K_B * tm.T_ROOM / R_F)
                pen = tm.band_average_penalty_db(F_NOISE, comp["total"], S_ref, 10e6, 150e6)
                c100 = tm.noise_components(np.array([100e6]), R_F, C_T0, cf * 1e-12, nz)
                Z, _, _ = tm.tia_tf(F_OUT, ol, R_F, C_T0, cf * 1e-12)
                S_out = tm.noise_components(F_OUT, R_F, C_T0, cf * 1e-12, nz)["total"] * np.abs(Z) ** 2
                v_rms = np.sqrt(np.trapezoid(S_out, F_OUT)) if nom["stable"] else np.nan
                row = dict(part=name, R_F=R_F, C_F_pF=cf, nominal=dict(
                    stable=nom["stable"], pm=nom["pm_deg"], gm=nom["gm_dB"], peak_dB=nom["peaking_dB"],
                    f_peak_MHz=nom["f_peak"] / 1e6, f3_MHz=nom["f_3dB"] / 1e6),
                    all_corners_stable=all_stable, worst_pm=worst_pm, worst_gm=worst_gm,
                    peak_range_dB=(min(pk_rng), max(pk_rng)) if pk_rng else None,
                    f_peak_range_MHz=(min(fpk_rng) / 1e6, max(fpk_rng) / 1e6) if fpk_rng else None,
                    noise_100MHz_pA=float(np.sqrt(c100["total"][0]) * 1e12), penalty_10_150_dB=pen,
                    v_out_rms_mV=v_rms * 1e3)
                res[f"{name}|{R_F:.0f}|{cf:.2f}"] = row
                n = row["nominal"]
                pk = row["peak_range_dB"]
                fp = row["f_peak_range_MHz"]
                print(f"{name} {R_F/1e3:.1f}k C_F {cf:.2f}: nominal PM {n['pm']:5.1f}, peak {max(n['peak_dB'],0):5.1f} dB at "
                      f"{n['f_peak_MHz']:4.0f} MHz, f3 {n['f3_MHz']:4.0f} | corners: all stable {all_stable}, worst PM "
                      f"{worst_pm:5.1f}, worst GM {worst_gm:4.1f} dB, peak {pk[0] if pk else float('nan'):4.1f}-"
                      f"{pk[1] if pk else float('nan'):4.1f} dB at {fp[0] if fp else 0:4.0f}-{fp[1] if fp else 0:4.0f} MHz | "
                      f"noise {row['noise_100MHz_pA']:.2f} pA at 100 MHz, penalty {pen:.1f} dB, v_out {row['v_out_rms_mV']:.2f} mV rms")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, default=float)


def bench_board(C_T_list=(12e-12, 14e-12, 16e-12), cfs=(0.3, 0.5, 0.7, 0.9, 1.1, 1.3, 1.6, 2.0)):
    """The 1.2-kOhm OPA846 bench board of Section 5.5 (about 14 pF at the node):
    nominal and worst-case loop for a range of total C_F (corners as in main(),
    with C_T +/- 1 pF because the board capacitance is only inferred)."""
    p = PARTS["OPA846"]
    ol, *_ = open_loop_model(p)
    nz = noise_inputs(p)
    models = {"nominal": ol, "gain low": Scaled(ol, GAIN_LO_DB["OPA846"]), "gain high": Scaled(ol, +1.5)}
    for C_T in C_T_list:
        for cf in cfs:
            nom = tm.loop_metrics(ol, 1200.0, C_T, cf * 1e-12)
            pms, gms, pks, ok = [], [], [], True
            for (mk, olm), dcf, dct in itertools.product(models.items(), (-0.1, 0.0, 0.1), (-1.0, 0.0, 1.0)):
                m = tm.loop_metrics(olm, 1200.0, C_T + dct * 1e-12, max(cf + dcf, 0.05) * 1e-12)
                if not m["stable"]:
                    ok = False
                    continue
                pms.append(m["pm_deg"])
                pks.append(m["peaking_dB"])
                if np.isfinite(m["gm_dB"]):
                    gms.append(m["gm_dB"])
            c50 = tm.noise_components(np.array([50e6]), 1200.0, C_T, cf * 1e-12, nz)
            Z, _, _ = tm.tia_tf(np.array([50e6]), ol, 1200.0, C_T, cf * 1e-12)
            print(f"bench board C_T {C_T*1e12:.0f} pF, C_F {cf:.1f} pF: nominal PM {nom['pm_deg']:5.1f}, peak "
                  f"{max(nom['peaking_dB'],0):4.1f} dB at {nom['f_peak']/1e6:4.0f} MHz, f3 {nom['f_3dB']/1e6:4.0f} MHz, "
                  f"|Z_T(50 MHz)| {abs(Z[0]):.0f} ohm | corners all stable {ok}, worst PM {min(pms) if pms else float('nan'):5.1f}, "
                  f"worst GM {min(gms) if gms else float('nan'):4.1f} dB, peak {min(pks) if pks else float('nan'):4.1f}-"
                  f"{max(pks) if pks else float('nan'):4.1f} dB | noise at 50 MHz {np.sqrt(c50['total'][0])*1e12:.2f} pA/rtHz")


if __name__ == "__main__":
    if sys.argv[1] == "bench":
        bench_board()
    else:
        main(sys.argv[1])
