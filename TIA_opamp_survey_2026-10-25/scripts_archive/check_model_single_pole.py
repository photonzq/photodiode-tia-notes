"""Check tia_model against the closed-form single-pole Butterworth results.

For A(s) = w_A / s (finite A0 = 1e5 here), the exact Butterworth design is
(R_F C_F)^2 = 2 R_F C_T / w_A - 1/w_A^2 and f_3dB = sqrt(GBW / (2 pi R_F (C_T + C_F))),
with zero peaking and a phase margin of about 65.5 degrees.
"""
import numpy as np

import tia_model as tm

R_F, C_T, GBW = 2000.0, 2.5e-12, 1.6e9
ol = tm.OpenLoopModel(A0=1e5, f_p1=GBW / 1e5)

cf_exact = tm.butterworth_cf_single_pole(R_F, C_T, GBW)
f3_exact = tm.butterworth_f3_single_pole(R_F, C_T, cf_exact, GBW)
m_exact = tm.loop_metrics(ol, R_F, C_T, cf_exact)
print(f"closed form : C_F = {cf_exact*1e12:.4f} pF, f3 = {f3_exact/1e6:.2f} MHz")
print(f"model @ C_F : f3 = {m_exact['f_3dB']/1e6:.2f} MHz, peaking = {m_exact['peaking_dB']:.4f} dB, "
      f"PM = {m_exact['pm_deg']:.2f} deg, f_c = {m_exact['f_c']/1e6:.1f} MHz, |NG(f_c)| = {m_exact['ng_at_fc']:.2f}")
for target in (0.01, 0.05, 1.0, 2.0):
    cf = tm.design_cf(ol, R_F, C_T, target)
    m = tm.loop_metrics(ol, R_F, C_T, cf)
    print(f"design for {target:4.2f} dB peaking: C_F = {cf*1e12:.4f} pF, f3 = {m['f_3dB']/1e6:.1f} MHz, "
          f"PM = {m['pm_deg']:.1f} deg")

# Second-order theory: 1 dB peaking <-> zeta = 0.5225; check the bandwidth ratio
zeta = 0.5225
w_ratio = np.sqrt(1 - 2 * zeta ** 2 + np.sqrt(2 - 4 * zeta ** 2 + 4 * zeta ** 4))
print(f"2nd-order f3/f0 at 1 dB peaking: {w_ratio:.3f}")

# Noise sanity: e_n = 1 nV/rtHz, i_n = 2 pA/rtHz at 100 MHz
nz = tm.NoiseInputs(en_flat=1e-9, in_flat=2e-12)
f = np.array([1e6, 1e8])
comp = tm.noise_components(f, R_F, C_T, cf_exact, nz)
hand = np.sqrt(4 * tm.K_B * tm.T_ROOM / R_F + (2e-12) ** 2
               + (1e-9) ** 2 * ((1 / R_F) ** 2 + (2 * np.pi * 1e8 * (C_T + cf_exact)) ** 2))
print(f"noise @100 MHz model {np.sqrt(comp['total'][1])*1e12:.4f} pA/rtHz, hand {hand*1e12:.4f} pA/rtHz")
