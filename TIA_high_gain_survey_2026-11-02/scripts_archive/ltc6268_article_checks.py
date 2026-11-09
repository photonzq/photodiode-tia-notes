"""Hand checks of the numbers in Brisebois (LT Journal 25(2), 2015) and of
the inductive-source condition behind its photomultiplier oscillation.

Plain checks: each line prints the value, the article's value where there is
one, and the relative difference.
"""
import math

TWO_PI = 2 * math.pi


def show(label, value, unit, ref=None):
    if ref is None:
        print(f"{label:58s} {value:12.4g} {unit}")
    else:
        err = (value - ref) / ref
        print(f"{label:58s} {value:12.4g} {unit}   article {ref:g}   diff {err:+.1%}")


print("--- CV + I noise at 1 MHz")
cv_ltc = TWO_PI * 1e6 * 0.55e-12 * 4e-9
show("LTC6268-10 CV term (0.55 pF, 4 nV/rtHz)", cv_ltc * 1e15, "fA/rtHz", 14)
show("LTC6268-10 CV + I with i_n = 50 fA/rtHz", math.hypot(cv_ltc, 50e-15) * 1e15, "fA/rtHz", 52)
cv_opa = TWO_PI * 1e6 * 5.2e-12 * 4.8e-9
show("OPA657 CV term (5.2 pF, 4.8 nV/rtHz)", cv_opa * 1e15, "fA/rtHz")
show("OPA657 CV + I with i_n = 1.3 fA/rtHz", math.hypot(cv_opa, 1.3e-15) * 1e15, "fA/rtHz", 156)

print("--- feedback capacitance from the measured bandwidths at 402 kOhm")
RF = 402e3
show("C_F from 4 MHz", 1 / (TWO_PI * 4e6 * RF) * 1e15, "fF", 100)
show("C_F from 34 MHz", 1 / (TWO_PI * 34e6 * RF) * 1e15, "fF", 11.6)
show("bandwidth from 88 ns, 0.35/t_r", 0.35 / 88e-9 / 1e6, "MHz", 4)
show("bandwidth from 10.3 ns, 0.35/t_r", 0.35 / 10.3e-9 / 1e6, "MHz", 34)

print("--- amplifier ceiling sqrt(GBW/(2 pi R_F C_T)) at 402 kOhm, GBW 4 GHz")
GBW = 4e9
C_T_for_34 = GBW / (TWO_PI * RF * 34e6 ** 2)
show("C_T that puts the amplifier ceiling at 34 MHz", C_T_for_34 * 1e12, "pF")
show("  of which outside the amplifier (minus 0.55 pF)", (C_T_for_34 - 0.55e-12) * 1e12, "pF")
for cpar in (100e-15, 11.6e-15):
    rstar = C_T_for_34 / (math.pi * GBW * cpar ** 2)
    show(f"crossover gain R_F* with C_par = {cpar*1e15:.1f} fF", rstar / 1e3, "kOhm")

print("--- femtoamp test: charge and capacitance from the 200 mV step")
q = 0.5 * 0.190 * 1.25 / 1e12
show("charge, triangle 190 mV x 1.25 s / 1 TOhm", q * 1e12, "pC", 0.12)
show("capacitance Q / 200 mV", q / 0.2 * 1e12, "pF", 0.6)
show("time constant 1 TOhm x 0.6 pF", 1e12 * 0.6e-12, "s")

print("--- photomultiplier: where the inductive source cancels the node")
# Noise gain with a source C_S behind a series inductance L, a capacitance
# C_node directly at the summing node and C_F across R_F (R_F neglected,
# since 1.82 kOhm with 1 pF has its corner at 87 MHz):
#   NG = 1 + [C_node + C_S / (1 - w^2 L C_S)] / C_F
# NG = 0 where  w^2 = (1 / (L C_S)) * (1 + C_S / (C_node + C_F)).
f_osc = 1.05e9
w = TWO_PI * f_osc
C_S, C_F = 10e-12, 1e-12
for C_node in (0.55e-12, 1.05e-12, 1.55e-12):
    L = (1 + C_S / (C_node + C_F)) / (w ** 2 * C_S)
    show(f"L that puts NG = 0 at 1.05 GHz, C_node = {C_node*1e12:.2f} pF", L * 1e9, "nH")


def wire_l(length_m, radius_m):
    """Partial self-inductance of a straight round wire (low frequency form)."""
    l_cm = length_m * 100
    return 2 * l_cm * (math.log(2 * length_m / radius_m) - 0.75) * 1e-9


for d in (0.5e-3, 0.8e-3, 1.0e-3):
    show(f"straight wire 19 mm long, {d*1e3:.1f} mm diameter", wire_l(19.05e-3, d / 2) * 1e9, "nH")

print("--- the same condition for the companion's OPA855 design")
# C_D = 1 pF (the pair), C_node = C_CM + C_DIFF + C_PCB = 0.35 + 0.80 pF,
# C_F = 0.20 pF (design) and 0.25 pF (Section 8.10).
C_D, C_node = 1e-12, 1.15e-12
for C_Fx in (0.20e-12, 0.25e-12):
    for L in (0.5e-9, 1e-9, 2e-9, 3e-9, 5e-9):
        w2 = (1 + C_D / (C_node + C_Fx)) / (L * C_D)
        f0 = math.sqrt(1 / (L * C_D)) / TWO_PI
        show(f"C_F {C_Fx*1e12:.2f} pF, L {L*1e9:.1f} nH: NG = 0 at (series res. {f0/1e9:.2f} GHz)",
             math.sqrt(w2) / TWO_PI / 1e9, "GHz")
