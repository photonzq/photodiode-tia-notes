"""Numbers for the comparison of a switched integrator with a resistor-limited TIA
(2 November 2026).  Every quantity is a noise charge per measurement, in electrons rms,
at 25 C.

1. The TIA's feedback resistor at its own corner f_R = 1/(2 pi R_F C_par), over the
   measurement time T = 1/(pi f_R) that has the same noise bandwidth (pi/2) f_R:
   Q_R^2 = (4kT/R_F) (pi/2) f_R T^2 = 4 kT C_par, independent of R_F.
2. Reset (kTC) noise of a capacitor, Q^2 = kT C, by equipartition.
3. Parallel noise of the photodiode over T: (4kT/R_sh) T/2 at zero bias, q I T for a
   dark current I (shot noise of the charge collected).
4. Series noise of the amplifier with double sampling: two samples, each through a
   single-pole filter of time constant tau (noise bandwidth 1/(4 tau)):
   Q^2 = 2 e_n^2 C_T^2 / (4 tau) = e_n^2 C_T^2 / (2 tau).
5. Channel charge of a MOS switch, Q_ch = C_ox W L (V_GS - V_T), and the output step it
   gives on an integration capacitor.

Usage:  python integrator_vs_tia.py
"""
import math

K_B, Q_E = 1.380649e-23, 1.602176634e-19
KT = K_B * 298.15


def e(q: float) -> float:
    return q / Q_E


print(f"kT at 25 C = {KT:.4e} J")
print("1. TIA resistor at its corner, Q_R = 2 sqrt(kT C_par):")
for c in (0.05e-12, 0.1e-12, 0.2e-12):
    print(f"   C_par {c * 1e12:.2f} pF: {e(2 * math.sqrt(KT * c)):.0f} e-")

print("2. Reset noise sqrt(kT C):")
for c in (1e-15, 10e-15, 100e-15, 1e-12, 10e-12, 100e-12):
    print(f"   C {c * 1e12:g} pF: {e(math.sqrt(KT * c)):.1f} e-")

T = 1 / (math.pi * 1 / (2 * math.pi * 1e9 * 0.1e-12))    # 1 GOhm, 0.1 pF: T = 2 R_F C_par
print(f"3./4. Example: T = {T * 1e3:.3f} ms (1 GOhm, 0.1 pF, f_R = {1 / (2 * math.pi * 1e9 * 0.1e-12):.0f} Hz)")
q_r = 2 * math.sqrt(KT * 0.1e-12)
q_sh = math.sqrt(4 * KT / 2e9 * T / 2)
q_dark = math.sqrt(Q_E * 1e-12 * T)
print(f"   TIA resistor {e(q_r):.0f} e-; diode shunt 2 GOhm {e(q_sh):.0f} e-; 1 pA dark current {e(q_dark):.0f} e-")
for tau in (T / 10, T / 2):
    for c_t in (32e-12, 400e-12, 1e-9):
        q_s = 3e-9 * c_t / math.sqrt(2 * tau)
        print(f"   series noise, e_n 3 nV/rtHz, C_T {c_t * 1e12:.0f} pF, tau {tau * 1e6:.0f} us: {e(q_s):.0f} e-")
q_s32 = 3e-9 * 32e-12 / math.sqrt(2 * T / 2)
for label, par in (("zero-bias diode, 2 GOhm", q_sh), ("biased diode, 1 pA dark", q_dark)):
    tia = math.sqrt(q_r ** 2 + par ** 2 + q_s32 ** 2)
    integ = math.sqrt(par ** 2 + q_s32 ** 2)
    print(f"   {label}: TIA {e(tia):.0f} e-, integrator {e(integ):.0f} e- "
          f"(ratio {tia / integ:.2f}, {20 * math.log10(tia / integ):.1f} dB)")
q_sh8 = math.sqrt(4 * KT / 0.4e9 * T / 2)                 # S1336-8BK: 0.4 GOhm
q_s400 = 3e-9 * 400e-12 / math.sqrt(2 * T / 2)
tia = math.sqrt(q_r ** 2 + q_sh8 ** 2 + q_s400 ** 2)
integ = math.sqrt(q_sh8 ** 2 + q_s400 ** 2)
print(f"   400 pF node, 0.4 GOhm diode: shunt {e(q_sh8):.0f} e-, series {e(q_s400):.0f} e-; TIA {e(tia):.0f} e-, "
      f"integrator {e(integ):.0f} e- ({20 * math.log10(tia / integ):.1f} dB)")
c_max = 2 * math.sqrt(2 * (T / 10) * KT * 0.1e-12) / 3e-9
print(f"   largest C_T for which the series noise (tau = T/10) stays below the resistor's: {c_max * 1e12:.0f} pF")
i_min = 4 * KT * 0.1e-12 / (Q_E * T)
print(f"   signal current whose own shot noise equals the resistor's: {i_min * 1e12:.1f} pA "
      f"(= 4 pi kT B C_par / q with B = f_R)")

print("5. MOS switch channel charge:")
c_ox = 3.9 * 8.854e-12 / 7e-9                      # F/m^2, 7-nm oxide
q_ch = c_ox * 1e-6 * 0.18e-6 * 1.5
print(f"   C_ox {c_ox * 1e3:.2f} fF/um^2; W/L = 1/0.18 um, 1.5 V overdrive: Q_ch = {e(q_ch):.0f} e-; "
      f"half on 10 fF gives {q_ch / 2 / 10e-15 * 1e3:.0f} mV, on 1 fF {q_ch / 2 / 1e-15:.2f} V")
for c_int in (100e-12, 10e-12, 1e-12, 0.1e-12):
    print(f"   2 pC on {c_int * 1e12:g} pF: {2e-12 / c_int:.3g} V")
