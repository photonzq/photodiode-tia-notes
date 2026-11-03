"""Compare the open-loop models with the closed-loop and TIA data printed in the datasheets.

Usage: python check_datasheet_examples.py

A. Resistive closed-loop gain at the minimum stable gain: peaking and -3 dB
   bandwidth of A/(1 + A/G) from the interpolated open-loop curve, against the
   datasheet table or curve.  (The datasheet circuits also contain R_F/R_G and
   input capacitance, so agreement within ~1 dB and ~20 % is the expectation.)
B. TIA examples printed in the datasheets, recomputed with the same model.
C. TI's TIA-calculator curves, recomputed with Eq. 1 of the datasheets
   (f = sqrt(GBW / (2 pi R_F C_TOT)), C_TOT without C_F and without PCB) and
   with the model's flat design at C_PCB = 0.
"""
import numpy as np

import tia_model as tm
from parts_db import PARTS
from run_analysis import open_loop_model

F = tm.F_GRID


def resistive(ol, g):
    A = ol.A(F)
    H = np.abs((A / g) / (1 + A / g))
    pk = 20 * np.log10(H.max())
    below = np.where(H < 1 / np.sqrt(2))[0]
    f3 = F[below[0]] if len(below) else np.nan
    return pk, F[np.argmax(H)], f3


print("A. Resistive gain at the minimum stable gain")
cases_a = [("OPA846", 7, "+3.1 dB at ~350 MHz, -3 dB 499 MHz (curve, p4)"),
           ("OPA847", 12, "4.5 dB typ / 7 dB max (table p3); curve 4.6 dB, 596 MHz"),
           ("OPA818", 7, "1.4 dB, 765 MHz (EC p5); ~50 deg PM (p16)"),
           ("OPA855", 5.3, "inverting -7 V/V test circuit, noise gain 5.3: 4.3 dB (curve) / 5 dB (text)"),
           ("OPA855", 7, "2.5 GHz SSBW (table)"),
           ("OPA955", 5.3, "noise gain 5.3: ~4 dB (curve) / 5 dB (text)"),
           ("OPA858", 7, "< 1 dB peaking, 1.2 GHz SSBW"),
           ("LMH6629 (COMP HI)", 10, "WSON-8: 900 MHz, no peaking (table)")]
for name, g, ref in cases_a:
    ol, *_ = open_loop_model(PARTS[name])
    pk, fpk, f3 = resistive(ol, g)
    m = tm.loop_metrics(ol, 2000.0, (g - 1) * 100e-12, 100e-12)
    print(f"  {name:18s} G = {g:4.1f}: model peaking {pk:4.1f} dB at {fpk/1e6:5.0f} MHz, -3 dB {f3/1e6:5.0f} MHz, "
          f"PM {m['pm_deg']:4.1f} deg  | datasheet: {ref}")

print("\nB. Datasheet TIA examples")
ol856, *_ = open_loop_model(PARTS["OPA856"])
print("  OPA856 measured (Fig 9-2): R_F 1 k, C_F 1 pF external, C_IN ~4 pF; measured +0.7 dB near 160 MHz, -3 dB ~220 MHz")
for C_T in (3.5e-12, 4.0e-12, 4.5e-12):
    for C_F in (1.0e-12, 1.1e-12, 1.2e-12):
        m = tm.loop_metrics(ol856, 1000.0, C_T, C_F)
        print(f"    C_T {C_T*1e12:.1f} pF, C_F {C_F*1e12:.1f} pF: -3 dB {m['f_3dB']/1e6:5.0f} MHz, "
              f"peaking {m['peaking_dB']:4.2f} dB at {m['f_peak']/1e6:4.0f} MHz, PM {m['pm_deg']:4.1f} deg")

ol855, *_ = open_loop_model(PARTS["OPA855"])
print("  OPA855 Fig 9-8: R_F 1 k, C_D 1 pF (C_T = 1.8 pF with the amplifier, no PCB); +0.7 dB near 0.6 GHz, -3 dB ~1.09 GHz")
for C_pcb in (0.0, 0.2e-12):
    C_T = 1.8e-12 + C_pcb
    cf = tm.design_cf(ol855, 1000.0, C_T, 0.7)
    m = tm.loop_metrics(ol855, 1000.0, C_T, cf)
    print(f"    C_PCB {C_pcb*1e12:.1f} pF: C_F for 0.7 dB = {cf*1e12:.3f} pF -> -3 dB {m['f_3dB']/1e6:5.0f} MHz, "
          f"peak at {m['f_peak']/1e6:4.0f} MHz, PM {m['pm_deg']:4.1f} deg")

ol955, *_ = open_loop_model(PARTS["OPA955"])
print("  OPA955 front page: R_F 10 k, C_F 0.1 pF, C_IN 4.7 pF; -3 dB ~112 MHz, no peaking")
for C_T in (4.7e-12, 5.8e-12):
    for C_F in (0.10e-12, 0.15e-12, 0.20e-12):
        m = tm.loop_metrics(ol955, 10e3, C_T, C_F)
        print(f"    C_T {C_T*1e12:.1f} pF, C_F {C_F*1e12:.2f} pF: -3 dB {m['f_3dB']/1e6:5.0f} MHz, "
              f"peaking {m['peaking_dB']:4.2f} dB, PM {m['pm_deg']:4.1f} deg")

ol6629, *_ = open_loop_model(PARTS["LMH6629 (COMP HI)"])
print("  LMH6629 Fig 60: R_F 1.2 k, C_F 0.6 pF, C_D 10 pF (C_IN = 15.7 pF with C_CM + C_DIFF); 'around 200 MHz' (calculated)")
m = tm.loop_metrics(ol6629, 1200.0, 15.7e-12, 0.6e-12)
print(f"    model: -3 dB {m['f_3dB']/1e6:5.0f} MHz, peaking {m['peaking_dB']:4.2f} dB, PM {m['pm_deg']:4.1f} deg, |NG(fc)| {m['ng_at_fc']:.1f}")

print("\nA2. Calibrated open-loop variants (table GBW, text phase margin) at the same resistive gains")
for name, g, ref in [("OPA855", 7, "2.5 GHz SSBW (table), ~3.1 GHz (Fig 6-1)"),
                     ("OPA855", 5.3, "4.3 dB (curve) / 5 dB (text)"),
                     ("OPA858", 7, "< 1 dB peaking, 1.2 GHz SSBW (table)"),
                     ("OPA859", 1, "unity-gain buffer, see datasheet SSBW")]:
    p = PARTS[name]
    ol, *_ = open_loop_model(p)
    cal = p["ol"]["calibrate"]
    olc = tm.calibrated_interp(ol, cal["gain_scale_dB"], cal["pm_target_deg"], cal["g_noise"])
    pk, fpk, f3 = resistive(olc, g)
    print(f"  {name:7s} G = {g:4.1f} ({olc.note.split('; ')[-1]}): peaking {pk:4.1f} dB at {fpk/1e6:5.0f} MHz, "
          f"-3 dB {f3/1e6:5.0f} MHz | datasheet: {ref}")

print("\nC. TI TIA-calculator curves: Eq. 1 (no C_F, no PCB) and the model's flat design at C_PCB = 0")
cases_c = [("OPA859", 2000.0, 1.0, 199.4), ("OPA859", 2000.0, 0.5, 235.0), ("OPA859", 5000.0, 1.0, 126.1),
           ("OPA858", 5000.0, 1.0, 310.0), ("OPA858", 10e3, 1.0, 220.6), ("OPA858", 20e3, 1.0, 155.9),
           ("OPA855", 6000.0, 1.0, 343.5), ("OPA855", 12e3, 1.0, 242.9),
           ("OPA818", 20e3, 1.0, 79.5), ("OPA856", 1000.0, 1.0, 311.0), ("OPA856", 5000.0, 1.0, 139.0)]
for name, R_F, c_pd, ti in cases_c:
    p = PARTS[name]
    c_amp = p["c_cm"] + p["c_diff"]
    C_T = c_pd * 1e-12 + c_amp
    eq1 = np.sqrt(p["gbw"] / (2 * np.pi * R_F * C_T)) / 1e6
    ol, *_ = open_loop_model(p)
    cf = tm.design_cf(ol, R_F, C_T, 0.01)
    m = tm.loop_metrics(ol, R_F, C_T, cf) if np.isfinite(cf) else None
    model = (f"model flat: C_F {cf*1e12:.3f} pF, {m['f_3dB']/1e6:5.0f} MHz, PM {m['pm_deg']:4.1f} deg"
             if m else "model: no flat design")
    print(f"  {name:7s} R_F {R_F/1e3:4.1f} k, C_PD {c_pd:.1f} pF: TI {ti:6.1f} MHz | Eq. 1 {eq1:6.1f} MHz | {model}")
