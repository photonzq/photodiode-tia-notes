"""What a discrete-FET composite front end could buy at the 1-pF, 2-kOhm node (answer to the
JFET-composite question; device data from fet_front_end/ and ../datasheets/fet_front_end/).

Usage: python fet_composite_bound.py [--spice <spice folder>]

A FET (cascoded common source) at the summing node, followed by an op amp, with R_F from the
final output back to the gate.  Its input-referred noise current density is
    S_i(f) = 4 k T / R_F + 2 q I_G + e_n^2 [ (2 pi f C_T)^2 + 1 / R_F^2 ],
with C_T = C_D + C_PCB + C_F + C_iss + C_rss (the second C_rss: Miller at a cascoded drain gain
of about -1).  Over 0..B the band noise is
    i_B^2 = B (4 k T / R_F + 2 q I_G + e_n^2 / R_F^2) + e_n^2 (2 pi C_T)^2 B^3 / 3.
The second stage's noise, divided by the FET's gain, is neglected.

Four results are printed:
  0. what the op amps' noise at 100 MHz is made of (survey model, Eq. (17), at the SPICE designs'
     C_F): the Johnson noise of R_F, the input current noise and e_n on the total capacitance;
  1. the bound: the dynamic-range gain of a noiseless amplifier (R_F alone) over the SPICE
     designs of OPA855, OPA955 and OPA818 (dr_comparison.json), same ceiling, at I1 + I2 =
     0, 0.1, 1 and 10 mA;
  2. the transit frequency f_T = g_m / (2 pi C_iss) a FET needs to match OPA855's and OPA955's
     band noise, at the optimum C_iss = C_D + C_PCB + C_F, where the e_n term is
     (32 pi / 3) k T Gamma C_x B^3 / f_T (channel noise 4 k T Gamma / g_m, Gamma = 2/3 and 1);
  3. every surveyed device at its datasheet operating point: C_T, e_n C_T noise at 100 MHz,
     band noise with the gate current at 1 uA and at the datasheet's leakage figure.
No simulation.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

K_B, Q_E = 1.380649e-23, 1.602176634e-19
T = 298.15
KT = K_B * T
R_F, B = 2000.0, 150e6
C_D, C_PCB, C_F = 1.0e-12, 0.35e-12, 0.25e-12
C_X = C_D + C_PCB + C_F                       # node capacitance before the FET
I_DC = (0.0, 1e-4, 1e-3, 1e-2)

# name, type, g_m (S), its source, C_in = C_iss or C11 (F), C_rss or C_gd (F), e_n (V/rtHz),
# its source, gate-leakage figure (A) and its source.  Datasheet labels as read from rendered pages.
DEVICES = [
    ("BF862", "Si JFET", 45e-3, "|yfs| 45 TYP at I_DSS (NXP 2000, p4)", 10e-12, 1.9e-12,
     0.8e-9, "0.8 TYP at 100 kHz (p4)", 1e-9, "I_GSS 1 nA MAX (p4)"),
    ("LSBF862", "Si JFET", 42e-3, "Yfs 42 TYP (LS Doc 201195 A2, p2)", 11.5e-12, 3.5e-12,
     0.8e-9, "0.8 TYP at 10 kHz (p2)", 1e-9, "I_GSS 1 nA MAX"),
    ("BF861C", "Si JFET", 25e-3, "|yfs| 20-30 MIN-MAX, mid (NXP Rev 5, Table 7)", 10e-12, 2.1e-12,
     1.0e-9, "about 1.0 at 1 MHz (Fig 14); 1.5 TYP in Table 7", 1e-9, "I_GSS 1 nA MAX"),
    ("CPH3910", "Si JFET", 40e-3, "|yfs| 40 TYP (onsemi Rev 2, p1)", 6.0e-12, 2.3e-12,
     np.sqrt(4 * KT * 2 / 3 / 40e-3), "not stated; channel thermal noise, Gamma 2/3", 1e-9, "I_GSS 1 nA MAX"),
    ("2SK3557", "Si JFET", 35e-3, "|yfs| 35 TYP (onsemi Rev 3, p2)", 10.0e-12, 2.9e-12,
     np.sqrt(4 * KT * 2 / 3 / 35e-3), "not stated above 1 kHz; channel thermal noise", 1e-9, "I_GSS 1 nA MAX"),
    ("J310", "Si JFET", 12e-3, "Re(yfs) 12 TYP at 100 MHz (onsemi J309/D Rev 1, p2)", 7.0e-12, 2.2e-12,
     1.7e-9, "about 1.7 at 100 kHz, still falling (Fairchild MMBFJ310 Fig 11)", 1e-9, "I_GSS 1 nA MAX"),
    ("LSK170", "Si JFET", 22e-3, "Gfs 22 TYP (LS Doc 201110 A22, p2)", 20e-12, 5e-12,
     0.93e-9, "0.93, flat 100 Hz-100 kHz (p6)", 0.5e-9, "I_G 0.5 nA MAX"),
    ("BF545C", "Si JFET", 6.5e-3, "|yfs| 6.5 MAX (NXP Rev 4, Table 7)", 3.0e-12, 0.9e-12,
     np.sqrt(4 * KT * 2 / 3 / 6.5e-3), "not stated; channel thermal noise", 1e-9, "I_GSS 1 nA MAX"),
    ("ATF-34143", "GaAs pHEMT", 152e-3, "|Y21| from S-parameters, 3 V 20 mA, 0.5 GHz (AV02-1283EN p7)",
     1.23e-12, 0.17e-12, 0.36e-9, "sqrt(4kT0 Rn), Rn 8 ohm at 0.5 GHz (p7)", 30e-6, "I_gss 30 TYP at -4 V (p3)"),
    ("ATF-54143", "GaAs pHEMT", 319e-3, "|Y21| from S-parameters, 3 V 40 mA, 0.1 GHz (AV02-0488EN p6)",
     2.61e-12, 0.18e-12, 0.18e-9, "Rn 2 ohm at 0.5 GHz", 200e-6, "I_gss 200 MAX at -3 V"),
    ("ATF-55143", "GaAs pHEMT", 169e-3, "|Y21| from S-parameters, 2 V 20 mA, 0.1 GHz (AV02-0923EN p9)",
     1.28e-12, 0.11e-12, 0.28e-9, "Rn 5 ohm at 0.5 GHz", 95e-6, "I_gss 95 MAX at -2.7 V"),
    ("SAV-551+", "GaAs pHEMT", 208e-3, "|Y21| from the 3 V 15 mA S2P, 0.1 GHz (Rev F)",
     2.02e-12, 0.20e-12, 0.24e-9, "Rn 3.5 ohm at 0.5 GHz (p9)", 95e-6, "I_GSS 95 MAX at -3 V"),
    ("SAV-541+", "GaAs pHEMT", 375e-3, "|Y21| from the S2P (Rev F)",
     2.46e-12, 0.19e-12, 0.20e-9, "Rn 2.5 ohm at 0.5 GHz", 200e-6, "I_GSS 200 MAX"),
    ("CE3512K2", "GaAs pHEMT", 72.9e-3, "|Y21| from S-parameters, 2 V 10 mA, 2 GHz (CDS-0018-05)",
     0.266e-12, 0.0, np.sqrt(4 * KT * 2 / 3 / 72.9e-3), "no data below 2 GHz; channel thermal noise",
     10e-6, "I_GSO 0.4 TYP, 10 MAX at -3 V (p3)"),
    ("CE3520K3", "GaAs pHEMT", 60.0e-3, "|Y21| from S-parameters, 2 V 10 mA, 2 GHz (CDS-0019-04)",
     0.352e-12, 0.0, np.sqrt(4 * KT * 2 / 3 / 60e-3), "no data below 2 GHz; channel thermal noise",
     10e-6, "I_GSO 0.4 TYP, 10 MAX at -3 V (p3)"),
]


def band_noise(e_n, C_T, I_G):
    """rms input noise over 0..B (A) of the FET front end with R_F."""
    s = B * (4 * KT / R_F + 2 * Q_E * I_G + e_n ** 2 / R_F ** 2) + e_n ** 2 * (2 * np.pi * C_T) ** 2 * B ** 3 / 3
    return float(np.sqrt(s))


def db_gain(floor_a, floor_b, i_dc):
    """DR gain (dB) of floor_b over floor_a at the same ceiling, with shot noise of i_dc."""
    sh = 2 * Q_E * i_dc * B
    return 10 * np.log10((floor_a ** 2 + sh) / (floor_b ** 2 + sh))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--spice", type=Path, default=Path(__file__).resolve().parent.parent / "spice")
    a = ap.parse_args()
    r = json.loads((a.spice / "results" / "dr_comparison.json").read_text(encoding="utf-8"))
    import tia_model as tm
    from parts_db import PARTS
    from run_analysis import noise_inputs
    from spice_tia_checks import VENDOR_MODELS
    print("0. Noise at 100 MHz, survey model at the SPICE designs' C_F (pA/rtHz): total = sqrt(R_F^2 + i_n^2 + e_n^2)")
    for p in ("OPA855", "OPA955", "OPA818"):
        d = PARTS[VENDOR_MODELS[p]["db"]]
        cf = r["op_amps"][p]["design"]["cf_pF"] * 1e-12
        c_t = C_D + C_PCB + d["c_cm"] + d["c_diff"]
        nc = tm.noise_components(np.array([100e6]), R_F, c_t, cf, noise_inputs(d))
        s = {k: float(np.sqrt(v[0])) * 1e12 for k, v in nc.items()}
        print(f"   {p}: total {s['total']:.2f} = sqrt({s['RF']:.2f}^2 + {s['i_n']:.2f}^2 + {s['e_n']:.2f}^2); "
              f"e_n {d['en']*1e9:.2f} nV/rtHz on C_T + C_F = {(c_t + cf)*1e12:.2f} pF")
    ops = {}
    for p in ("OPA855", "OPA955", "OPA818"):
        s = r["op_amps"][p]["spice"]
        ops[p] = s["vs_idc"]["i_pk_mA"] * 1e-3 / np.sqrt(2) / 10 ** (s["dr_at_dB"]["0 mA"] / 20)
    i_rf = np.sqrt(4 * KT / R_F * B)
    print(f"R_F alone over 0-150 MHz: {i_rf*1e9:.1f} nA rms; C_x = C_D + C_PCB + C_F = {C_X*1e12:.2f} pF")
    print("1. Noiseless amplifier, DR gain over the SPICE designs (same ceiling), I1 + I2 = 0 / 0.1 / 1 / 10 mA:")
    for p, fl in ops.items():
        print(f"   {p}: floor {fl*1e9:.1f} nA rms -> " + " / ".join(f"{db_gain(fl, i_rf, i):.2f}" for i in I_DC) + " dB")
    print("2. f_T needed at the optimum C_iss = C_x to match the band noise (no gate current):")
    for p in ("OPA855", "OPA955"):
        allowed = ops[p] ** 2 - i_rf ** 2 - B * (2 * KT * 0)        # what the FET's e_n term may add
        for gam in (2 / 3, 1.0):
            f_t = (32 * np.pi / 3) * KT * gam * C_X * B ** 3 / allowed
            print(f"   {p}: e_n term <= {np.sqrt(allowed)*1e9:.1f} nA rms; Gamma {gam:.2f}: f_T >= {f_t/1e9:.2f} GHz, "
                  f"g_m = 2 pi f_T C_x = {2*np.pi*f_t*C_X*1e3:.1f} mS, e_n = {np.sqrt(4*KT*gam/(2*np.pi*f_t*C_X))*1e9:.2f} nV/rtHz")
    print("3. Devices at their datasheet operating points (cascoded; C_T = C_x + C_in + C_rss):")
    print("   device      type        g_m mS  C_in pF  f_T GHz  e_n nV  C_T pF  e_n C_T at 100 MHz pA/rtHz | "
          "band noise nA rms: I_G 1 uA / datasheet | vs OPA855 dark, 0.1 mA, 1 mA (dB)")
    rows = []
    for name, typ, gm, gm_src, c_in, c_rss, e_n, en_src, i_g, ig_src in DEVICES:
        C_T = C_X + c_in + c_rss
        f_t = gm / (2 * np.pi * c_in)
        i_e = e_n * 2 * np.pi * 100e6 * C_T
        lo = band_noise(e_n, C_T, min(1e-6, i_g))
        hi = band_noise(e_n, C_T, i_g)
        g = [db_gain(ops["OPA855"], lo, i) for i in I_DC[:3]]
        rows.append((name, lo, hi))
        print(f"   {name:10s} {typ:10s} {gm*1e3:6.1f} {c_in*1e12:7.2f} {f_t/1e9:7.2f} {e_n*1e9:6.2f} {C_T*1e12:7.2f} "
              f"{i_e*1e12:8.2f} | {lo*1e9:6.1f} / {hi*1e9:6.1f} | " + ", ".join(f"{x:+.2f}" for x in g))
    print("   (positive: better than OPA855; the gate current of the pHEMTs at their operating point is not published)")


if __name__ == "__main__":
    main()
