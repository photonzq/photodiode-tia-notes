"""Compare a measured OPA846 TIA (R_F = 1.2 kOhm) with the analytical model.

Usage: python opa846_1k2_check.py

Measured on the bench: |Z_T(50 MHz)| = 1.45 kOhm (peaking from the feedback
parasitics) and an input-referred noise of about 7 pA/rtHz at 50 MHz.

For a range of total input capacitance C_T, find the total feedback
capacitance C_F that reproduces |Z_T(50 MHz)| = 1.45 kOhm with the OPA846
open-loop curve, then print the loop figures and the input-referred noise at
50 MHz split into its terms (Eq. (17) of the survey, central model).  Also
prints the noise as a function of C_tot alone, and the instrument floor that
would add the missing noise in quadrature.
"""
import numpy as np

import tia_model as tm
from parts_db import PARTS
from run_analysis import open_loop_model, noise_inputs

R_F = 1200.0
F0 = 50e6
ZT_MEAS = 1450.0
I_MEAS = 7e-12

p = PARTS["OPA846"]
ol, *_ = open_loop_model(p)
nz = noise_inputs(p)
c_amp = (p["c_cm"] + p["c_diff"]) * 1e12
print(f"OPA846: C_CM + C_DIFF = {c_amp:.2f} pF, e_n = {p['en']*1e9:.2f} nV/rtHz, i_n = {p['in_']*1e12:.2f} pA/rtHz")
print(f"R_F = {R_F:.0f} ohm: Johnson {tm.johnson_current_asd(R_F)*1e12:.2f} pA/rtHz\n")


def zt_at(C_T, C_F, f=F0):
    Z, _, _ = tm.tia_tf(np.array([f]), ol, R_F, C_T, C_F)
    return abs(Z[0])


cf_grid = np.logspace(np.log10(0.02e-12), np.log10(3e-12), 400)
print("C_T (pF) | C_F giving 1.45 kOhm at 50 MHz | stable, PM, f_c | peak (dB) at f | f_-3dB | noise at 50 MHz: total (R_F, i_n, e_n term) | output noise at 50 MHz")
for C_T_pF in (3.0, 4.0, 5.15, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 20.0, 25.0, 30.0, 40.0):
    C_T = C_T_pF * 1e-12
    z = np.array([zt_at(C_T, cf) for cf in cf_grid])
    roots = []
    for i in range(len(cf_grid) - 1):
        if (z[i] - ZT_MEAS) * (z[i + 1] - ZT_MEAS) < 0:
            lo, hi = cf_grid[i], cf_grid[i + 1]
            for _ in range(40):
                mid = np.sqrt(lo * hi)
                if (zt_at(C_T, lo) - ZT_MEAS) * (zt_at(C_T, mid) - ZT_MEAS) <= 0:
                    hi = mid
                else:
                    lo = mid
            roots.append(np.sqrt(lo * hi))
    if not roots:
        print(f"{C_T_pF:6.2f} | no C_F gives 1.45 kOhm at 50 MHz (max {z.max():.0f} ohm, min {z.min():.0f} ohm)")
        continue
    for cf in roots:
        m = tm.loop_metrics(ol, R_F, C_T, cf)
        comp = tm.noise_components(np.array([F0]), R_F, C_T, cf, nz)
        tot = np.sqrt(comp["total"][0]) * 1e12
        parts = ", ".join(f"{np.sqrt(comp[k][0])*1e12:.2f}" for k in ("RF", "i_n", "e_n"))
        print(f"{C_T_pF:6.2f} | {cf*1e12:.3f} pF | {m['stable']}, {m['pm_deg']:.1f} deg, {m['f_c']/1e6:.0f} MHz | "
              f"{m['peaking_dB']:+.2f} dB at {m['f_peak']/1e6:.0f} MHz | {m['f_3dB']/1e6:.0f} MHz | "
              f"{tot:.2f} pA ({parts}) | {tot*ZT_MEAS*1e-3:.2f} nV/rtHz")

print("\nInput-referred noise at 50 MHz against C_tot = C_T + C_F (central model):")
for c in (4, 5, 5.35, 6, 8, 10, 12, 13.6, 16, 20):
    S = (4 * tm.K_B * tm.T_ROOM / R_F + p["in_"] ** 2
         + p["en"] ** 2 * ((1 / R_F) ** 2 + (2 * np.pi * F0 * c * 1e-12) ** 2))
    print(f"  C_tot {c:5.2f} pF: {np.sqrt(S)*1e12:.2f} pA/rtHz")

S_model = (4 * tm.K_B * tm.T_ROOM / R_F + p["in_"] ** 2
           + p["en"] ** 2 * ((1 / R_F) ** 2 + (2 * np.pi * F0 * 5.35e-12) ** 2))
extra = np.sqrt(max(I_MEAS ** 2 - S_model, 0))
v_extra_tia = extra * ZT_MEAS
for label, fac in (("high-impedance probe at the TIA output", 1.0), ("50-ohm instrument behind a 50-ohm back-termination", 0.5)):
    v = v_extra_tia * fac
    p_dbm = 10 * np.log10(v ** 2 / 50 / 1e-3)
    print(f"\nMissing noise for a 1-pF photodiode (C_tot 5.35 pF): {extra*1e12:.2f} pA/rtHz input-referred, "
          f"{v_extra_tia*1e9:.2f} nV/rtHz at the TIA output; at a {label}: {v*1e9:.2f} nV/rtHz = {p_dbm:.1f} dBm/Hz")

# Eq. (28) of the survey: C_tot implied by the measured noise (datasheet typical e_n, i_n)
c_noise = np.sqrt(I_MEAS ** 2 - 4 * tm.K_B * tm.T_ROOM / R_F - p["in_"] ** 2 - (p["en"] / R_F) ** 2) / (p["en"] * 2 * np.pi * F0)
print(f"\nEq. (28): C_tot implied by {I_MEAS*1e12:.1f} pA/rtHz at {F0/1e6:.0f} MHz = {c_noise*1e12:.2f} pF")

# Same budget with the guaranteed maximum e_n = 1.3 nV/rtHz and i_n = 3.5 pA/rtHz (OPA846 p3)
S_max = (4 * tm.K_B * tm.T_ROOM / R_F + 3.5e-12 ** 2
         + 1.3e-9 ** 2 * ((1 / R_F) ** 2 + (2 * np.pi * F0 * 5.35e-12) ** 2))
print(f"1-pF photodiode with MAX e_n and i_n: {np.sqrt(S_max)*1e12:.2f} pA/rtHz at 50 MHz")

# Eq. (29): lower bound on C_tot from the peaking, any second-order low-pass: |H| <= 1/(1 - (f/f0)^2)
c_peak = p["gbw"] * (1 - R_F / ZT_MEAS) / (2 * np.pi * R_F * F0 ** 2)
print(f"Eq. (29): single-pole bound from |Z_T(50 MHz)| = {ZT_MEAS:.0f} ohm: C_tot >= {c_peak*1e12:.1f} pF")

# Diagnostic: noise at 10 MHz, where the capacitive term is small
for label, c in (("C_tot 5.35 pF", 5.35e-12), ("C_tot 13.6 pF", 13.6e-12)):
    S10 = (4 * tm.K_B * tm.T_ROOM / R_F + p["in_"] ** 2
           + p["en"] ** 2 * ((1 / R_F) ** 2 + (2 * np.pi * 10e6 * c) ** 2))
    print(f"Noise at 10 MHz, {label}: {np.sqrt(S10)*1e12:.2f} pA/rtHz")
S10_floor = (4 * tm.K_B * tm.T_ROOM / R_F + p["in_"] ** 2
             + p["en"] ** 2 * ((1 / R_F) ** 2 + (2 * np.pi * 10e6 * 5.35e-12) ** 2) + extra ** 2)
print(f"Noise at 10 MHz, C_tot 5.35 pF plus a white floor of {extra*1e12:.2f} pA/rtHz: {np.sqrt(S10_floor)*1e12:.2f} pA/rtHz")

# Band penalty (10-150 MHz, Eq. (19)) for the fitted circuit and for the Fig 5 robust design
from run_analysis import F_NOISE
for label, rf, ct, cf in (("fitted bench circuit, 1.2 kOhm, C_T 14 pF, C_F 0.295 pF", 1200.0, 14e-12, 0.295e-12),
                          ("Fig 5 robust design, 2 kOhm, C_T 13.15 pF, C_F 1.17 pF", 2000.0, 13.15e-12, 1.17e-12)):
    comp = tm.noise_components(F_NOISE, rf, ct, cf, nz)
    S_ref = np.full_like(F_NOISE, 4 * tm.K_B * tm.T_ROOM / rf)
    pen = tm.band_average_penalty_db(F_NOISE, comp["total"], S_ref, 10e6, 150e6)
    c50 = tm.noise_components(np.array([F0]), rf, ct, cf, nz)
    i50 = np.sqrt(c50["total"][0])
    print(f"{label}: {i50*1e12:.2f} pA/rtHz at 50 MHz = {20*np.log10(i50/tm.johnson_current_asd(rf)):.1f} dB above R_F; "
          f"band penalty 10-150 MHz {pen:.1f} dB")
