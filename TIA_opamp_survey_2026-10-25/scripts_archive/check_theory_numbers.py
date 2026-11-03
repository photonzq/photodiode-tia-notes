"""Numbers quoted in the theory section of the survey (Section 2).

Everything here is analytical: single-pole op-amp A(s) = w_A / s (A0 = 1e6),
thermal and shot references at 25 C, and the closed-form crossover criterion.
"""
import numpy as np

import tia_model as tm

kT = tm.K_B * tm.T_ROOM
print(f"kT/q at 25 C = {kT / tm.Q_E * 1e3:.3f} mV, 4kT = {4 * kT:.4e} J")
for R in (1500.0, 2000.0, 50.0):
    print(f"Johnson current of {R:6.0f} ohm: {tm.johnson_current_asd(R) * 1e12:.3f} pA/rtHz; "
          f"Johnson voltage {np.sqrt(4 * kT * R) * 1e9:.3f} nV/rtHz")
for I in (1e-5, 1e-4, 1e-3, 1e-2):
    print(f"shot noise of {I * 1e3:7.3f} mA: {tm.shot_current_asd(I) * 1e12:.3f} pA/rtHz")
for R in (1500.0, 2000.0, 50.0):
    print(f"photocurrent where shot = Johnson of {R:.0f} ohm: {2 * kT / (tm.Q_E * R) * 1e6:.2f} uA")

# Single-pole TIA, R_F = 2k, C_T = 2.5 pF, GBW = 1.6 GHz (illustration only)
R_F, C_T, GBW = 2000.0, 2.5e-12, 1.6e9
ol = tm.OpenLoopModel(A0=1e6, f_p1=GBW / 1e6)
cf_bw = tm.butterworth_cf_single_pole(R_F, C_T, GBW)
m = tm.loop_metrics(ol, R_F, C_T, cf_bw)
print(f"\nButterworth: C_F = {cf_bw * 1e12:.4f} pF, f3 = {m['f_3dB'] / 1e6:.1f} MHz, PM = {m['pm_deg']:.1f} deg,"
      f" f_c = {m['f_c'] / 1e6:.1f} MHz, |NG(f_c)| = {m['ng_at_fc']:.2f}, NG_inf = {m['ng_hf']:.2f},"
      f" ratio = {m['ng_at_fc'] / m['ng_hf']:.3f}")
cf_g = np.sqrt(C_T / (2 * np.pi * R_F * GBW))
m = tm.loop_metrics(ol, R_F, C_T, cf_g)
print(f"C_F = sqrt(C_T/(2 pi R_F GBW)) = {cf_g * 1e12:.4f} pF: peaking = {m['peaking_dB']:.2f} dB, "
      f"f3 = {m['f_3dB'] / 1e6:.1f} MHz, PM = {m['pm_deg']:.1f} deg")
for pk in (0.5, 1.0, 2.0, 3.0):
    cf = tm.design_cf(ol, R_F, C_T, pk)
    m = tm.loop_metrics(ol, R_F, C_T, cf)
    print(f"peaking {pk:.1f} dB: C_F/C_F,BW = {cf / cf_bw:.3f}, f3/f3,BW = "
          f"{m['f_3dB'] / tm.butterworth_f3_single_pole(R_F, C_T, cf_bw, GBW):.3f}, PM = {m['pm_deg']:.1f} deg")

# Bench-unit constants
print(f"\nf3 constant: sqrt(1e6/(2 pi 1e3 1e-12))/1e6 = {np.sqrt(1e6 / (2 * np.pi * 1e3 * 1e-12)) / 1e6:.3f} MHz")
print(f"C_F constant: sqrt(2e-12/(2 pi 1e3 1e6))*1e12 = {np.sqrt(2e-12 / (2 * np.pi * 1e3 * 1e6)) * 1e12:.3f} pF")
print(f"C_T,min constant: 2/(2 pi 1e3 1e6) = {2 / (2 * np.pi * 1e3 * 1e6) * 1e12:.2f} pF")
print(f"e_n*w*C constant: 2 pi 1e-9 1e6 1e-12 / 1e-12 = {2 * np.pi * 1e-9 * 1e6 * 1e-12 / 1e-12:.4e} pA per (nV MHz pF)")
print(f"4kT in pA^2 kOhm: {4 * kT / 1e3 / 1e-24:.3f};  2q in pA^2/mA: {2 * tm.Q_E * 1e-3 / 1e-24:.2f}")
