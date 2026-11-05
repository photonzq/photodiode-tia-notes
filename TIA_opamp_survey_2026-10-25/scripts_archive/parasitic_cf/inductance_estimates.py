"""How much do inductances change the feedback capacitance?  Estimates for Appendix G.

Why this script exists
----------------------
The field solutions of Section G.14 (package pcbcap) are electrostatic: they give the capacitance
across the feedback resistor in the limit of zero frequency, with no magnetic field and therefore
no inductance.  This script estimates, at the frequencies where the two designs of Chapter 4 use
their feedback capacitance, how much the inductances that the electrostatic model leaves out
change what the amplifier sees.  It prints every input with its source, every substitution and
every result.  No field solver is used; everything below is a closed form derived in this file.

Run:  python inductance_estimates.py          (reads ../../data/parasitic_cf/numerical/resistor_3d.json)

The four questions, in the order the script answers them
--------------------------------------------------------
(A) The resistor's own series inductance L_s, inside the chip, in series with R_F only.
(B) The partial self-inductance of straight conductors (traces, via barrels), derived from the
    Neumann formula, which (C) and (D) need.
(C) The inductance of the routing between the amplifier's pins and the resistor, in series with
    the whole feedback network R_F || C_F.
(D) The inductance in series with the photodiode at the summing node.

Units: lengths in mm, inductance in nH, capacitance in fF or pF, resistance in ohm, frequency in Hz.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from scipy.integrate import quad

HERE = Path(__file__).resolve().parent
RECORD_3D = HERE / ".." / ".." / "data" / "parasitic_cf" / "numerical" / "resistor_3d.json"

# ------------------------------------------------------------------------------------------------
# Constant.  mu0 = 4 pi x 1e-7 H/m exactly in the SI before 2019; the 2019 SI measures it as
# 1.25663706212(19) x 1e-6 H/m (CODATA 2018), which differs from 4 pi x 1e-7 by 5.5e-10 relative,
# far below anything that matters here.  In the units of this file:
#     1 H/m = 1e9 nH / 1e3 mm = 1e6 nH/mm,
#     mu0 / (2 pi) = 2e-7 H/m = 2e-7 x 1e6 nH/mm = 0.2 nH/mm.
# ------------------------------------------------------------------------------------------------
MU0_OVER_2PI = 0.2   # nH/mm


def w(f_hz: float) -> float:
    """Angular frequency omega = 2 pi f, in rad/s."""
    return 2.0 * math.pi * f_hz


# ================================================================================================
# (A) The resistor's own series inductance
# ================================================================================================
# Three-element model of a chip resistor (KOA TN-010 [A30], p. 3; Vishay 60107 [A26], Fig. 3):
# R in series with L_s, the two shunted by C_p.  Its admittance between the terminals is
#
#     Y = j w C_p + 1 / (R + j w L_s).                                                    (A1)
#
# Multiplying numerator and denominator of the second term by the complex conjugate R - j w L_s:
#
#     1 / (R + j w L_s) = (R - j w L_s) / (R^2 + w^2 L_s^2).                              (A2)
#
# So Y = G + j w C_eff, with
#
#     G     = R / (R^2 + w^2 L_s^2),
#     C_eff = C_p - (L_s / R^2) / (1 + (w L_s / R)^2).                                     (A3)
#
# While w L_s << R, the bracket (1 + (w L_s/R)^2) is 1 to within (w L_s/R)^2, so
#
#     C_eff = C_p - L_s / R^2,      G = 1/R,                                               (A4)
#
# independent of frequency: the series inductance acts as a negative capacitance L_s/R^2 in
# parallel.  Relative to C_p it is
#
#     (L_s / R^2) / C_p = (Z_c / R)^2,     Z_c = sqrt(L_s / C_p),                         (A5)
#
# so the inductance is negligible whenever R is well above the chip's characteristic impedance Z_c.
#
# What plays the role of C_p.  Everything that couples the two terminals electrostatically bridges
# R and L_s together: the body, the pads, the board, the pins.  The field solution C_F (planes
# removed, FR-4, Section G.14) is therefore used as C_p.  L_s is the inductance of the current
# path inside the chip.
#
# Source of L_s: KOA TN-010, Table 1 (p. 3), three-element parameters of RK73 thick-film flat chips
# fitted to impedance-analyser data: 0201 0.6 nH, 0402 0.7 nH, 0603 1.1 nH, 0805 1.1 nH.  Vishay's
# thin-film fits [A26] (Table 1, p. 1) give far smaller internal inductances (0.00002-0.12 nH) but
# put 0.02-0.27 nH per side into the connection (Fig. 7, p. 3), so the KOA values are the larger
# set and are used here.
L_S_KOA = {"0201": 0.6, "0402": 0.7, "0603": 1.1, "0805": 1.1}     # nH, KOA TN-010 Table 1 p. 3

# Resistances: 2 kohm in both designs of Chapter 4 (Table 4.1), 1.2 kohm on the OPA846 bench
# prototype (Section 3.10), 10 kohm where this note meets the high-gain note.
R_VALUES = (1200.0, 2000.0, 10_000.0)


def part_a(cf_best: dict[str, float]) -> None:
    print("(A) The resistor's own series inductance L_s (in series with R_F only), Eqs. (A4)-(A5)")
    print("    C_p = field-solved C_F (FR-4, planes removed, Section G.14); L_s = KOA TN-010 Table 1 p. 3")
    for size, cp_ff in cf_best.items():
        ls = L_S_KOA[size]
        # Z_c = sqrt(L_s/C_p): L_s in H (x1e-9), C_p in F (x1e-15).
        zc = math.sqrt(ls * 1e-9 / (cp_ff * 1e-15))
        print(f"  {size}: L_s = {ls:.2f} nH, C_p = {cp_ff:.2f} fF, "
              f"Z_c = sqrt({ls:.2f} nH / {cp_ff:.2f} fF) = {zc:.0f} ohm")
        for r in R_VALUES:
            # L_s/R^2 in fF: (L_s [nH] x 1e-9 H) / (R^2 ohm^2) = ... F; x 1e15 -> fF.
            neg_c_ff = ls * 1e-9 / r ** 2 * 1e15
            frac = (zc / r) ** 2
            # validity of (A4): (w L_s / R)^2 at 1 GHz
            val = (w(1e9) * ls * 1e-9 / r) ** 2
            print(f"      R = {r / 1e3:5.1f} kohm: L_s/R^2 = {ls:.2f}e-9 / {r:.0f}^2 = {neg_c_ff:.3f} fF "
                  f"= {100 * frac:.2f} % of C_p;  (w L_s/R)^2 at 1 GHz = {val:.1e}")
    print()


# ================================================================================================
# (B) Partial self-inductance of a straight conductor
# ================================================================================================
# Inductance belongs to a closed current loop.  A loop made of straight segments can be split into
# "partial" inductances (Ruehli's PEEC method): the loop inductance is the sum, over all pairs of
# segments i, j, of s_i s_j M_ij, where M_ij is the partial mutual inductance of the two segments,
# M_ii the partial self-inductance of segment i, and s = +1 or -1 the sense of the current along
# the segment.  This file estimates only the partial self-inductances of the signal segments; the
# limits of that estimate are stated in part (C).
#
# (B1) Two parallel filaments of length l, side by side over the same span, distance d apart.
# The Neumann formula, M = (mu0/4pi) int int (dl . dl') / |r - r'|, with dl . dl' = dx dx' for
# parallel filaments along x, gives
#
#     M(l, d) = (mu0/4pi) int_0^l int_0^l dx dx' / sqrt((x - x')^2 + d^2).
#
# Inner integral: with u = x' - x and int du / sqrt(u^2 + d^2) = asinh(u/d),
#     int_0^l dx' / sqrt((x'-x)^2 + d^2) = asinh((l - x)/d) + asinh(x/d).
# Outer integral: the substitution x -> l - x turns the first term into the second, so the double
# integral is 2 int_0^l asinh(x/d) dx.  An antiderivative is x asinh(x/d) - sqrt(x^2 + d^2) (its
# derivative is asinh(x/d) + x/sqrt(x^2+d^2) - x/sqrt(x^2+d^2) = asinh(x/d)), so
#     int_0^l asinh(x/d) dx = l asinh(l/d) - sqrt(l^2 + d^2) + d.
# Altogether
#
#     M(l, d) = (mu0/2pi) [ l asinh(l/d) - sqrt(l^2 + d^2) + d ].                          (B1)
#
# For l >> d, asinh(l/d) = ln(l/d + sqrt(1 + l^2/d^2)) -> ln(2l/d) and sqrt(l^2+d^2) -> l, so
#     M(l, d) -> (mu0 l / 2pi) [ ln(2l/d) - 1 ]  + O(d).                                   (B2)


def mutual_parallel(l: float, d: float) -> float:
    """Eq. (B1): partial mutual inductance (nH) of two parallel filaments of length l (mm), d apart."""
    return MU0_OVER_2PI * (l * math.asinh(l / d) - math.hypot(l, d) + d)


# (B3) A conductor of finite cross-section is a bundle of filaments.  If the current is spread over
# the cross-section with a fixed distribution g (g >= 0, integral 1) and is the same at every
# point along the length, the partial self-inductance is the average of M over pairs of filaments:
#     L_p = int int g(s) g(s') M(l, |s - s'|) ds ds'.
#
# Thin flat strip of width w (thickness neglected), current uniform across the width.  The
# distance s = |x - x'| between two independent points uniform on [0, w] has the distribution
#     P(s' <= s) = 1 - (1 - s/w)^2      (the complement is the area of two corner triangles of the
#                                       unit square, each (1 - s/w)^2 / 2),
# whose density is 2 (w - s) / w^2.  So
#
#     L_strip(l, w) = int_0^w  2 (w - s) / w^2  M(l, s) ds.                               (B3)
#
# Both simplifications in (B3), the zero thickness and the uniform current, make L_strip larger
# than the true partial self-inductance, never smaller.  First, M(l, d) falls as d grows:
# differentiating (B1), using d/dd asinh(l/d) = -l / (d sqrt(l^2 + d^2)),
#     dM/dd = (mu0/2pi) [ -l^2/(d sqrt(l^2+d^2)) - d/sqrt(l^2+d^2) + 1 ]
#           = (mu0/2pi) [ 1 - sqrt(l^2 + d^2)/d ]  <  0.
# (i) Thickness.  With a thickness t, two current elements at (x, z) and (x', z') are
#     sqrt((x-x')^2 + (z-z')^2) >= |x - x'| apart, so every term of the average of M can only
#     fall.
# (ii) Distribution.  For a conductor much longer than wide, the average of M over g is, apart from
#     terms that do not depend on g, (mu0 l/2pi) times the double integral of g g' (-ln|s - s'|)
#     (Eq. (B2)).  At high frequency the field cannot enter a good conductor, so along its surface
#     the tangential field E = -j w A - grad(phi) vanishes; for a long straight conductor this makes
#     A_z, i.e. int g(s') (-ln|s - s'|) ds', the same at every point of the cross-section.  That is
#     the stationarity condition, with a Lagrange multiplier for int g = 1, of the double integral
#     above, and since -ln|s - s'| is a positive-definite kernel on distributions of zero total
#     weight (its two-dimensional Fourier transform is 2 pi / |k|^2 > 0), the stationary g is the
#     minimum.  So the actual high-frequency distribution gives a smaller average of M than the
#     uniform one.
# The traces here are in that high-frequency regime.  Inside a conductor of resistivity rho the
# current density obeys the diffusion equation  laplacian(J) = j w mu0 J / rho  (Ampere's law
# without displacement current, Faraday's law, and J = E / rho).  Into a flat surface it decays as
# exp(-(1 + j) z / delta): substituting gives (1 + j)^2 / delta^2 = 2 j / delta^2 = j w mu0 / rho,
# so delta = sqrt(2 rho / (w mu0)).  With rho = 1.7e-8 ohm m for copper, delta = 3.7 um at
# 308 MHz and 2.3 um at 801 MHz, against a trace 35 um thick and 200 um wide.
#
# Thin-walled tube of radius a (a plated via barrel), current uniform around the circumference
# (the via is round and nothing near it breaks the symmetry).  Two points at angles theta, theta'
# on the circle are a chord 2 a sin(psi/2) apart, psi = |theta - theta'|, and psi is uniform on
# [0, 2 pi] for independent uniform angles.  So
#
#     L_tube(l, a) = (1/2pi) int_0^{2pi} M(l, 2 a sin(psi/2)) dpsi.                        (B4)
#
# Both integrands have an integrable logarithmic singularity where the distance goes to zero;
# scipy's adaptive quadrature handles it (the 'alg' weight is not needed at these tolerances).
#
# (B5) The geometric-mean-distance (GMD) shortcut, used only as a cross-check.  In (B2) the
# distance enters only through -ln d, so averaging (B2) over the cross-section replaces d by the
# GMD, defined by ln(GMD) = average of ln s:
#     L_p -> (mu0 l / 2pi) [ ln(2l / GMD) - 1 ].
# Uniform strip: average of ln|x - x'| over [0, w]^2.  With x = w u, it is ln w + I, where
#     I = int_0^1 int_0^1 ln|u - u'| du du' = 2 int_0^1 du int_0^u ln(u - u') du'
#       = 2 int_0^1 (u ln u - u) du = 2 (-1/4 - 1/2) = -3/2
# (using int_0^u ln t dt = u ln u - u, and int_0^1 u ln u du = [u^2 ln u / 2]_0^1 - int_0^1 u/2 du
# = -1/4).  So GMD_strip = w e^{-3/2}.
# Tube: ln|a e^{i theta} - a e^{i theta'}| = ln a + ln|1 - e^{i psi}|, and the mean of
# ln|1 - e^{i psi}| over a period is zero (ln|1 - e^{i psi}| = Re ln(1 - e^{i psi}) =
# -Re sum_{n>=1} e^{i n psi}/n, and each term averages to zero), so GMD_tube = a.


def partial_strip(l: float, width: float) -> float:
    """Eq. (B3): partial self-inductance (nH) of a straight thin strip, length l, width ``width`` (mm)."""
    val, _ = quad(lambda s: 2.0 * (width - s) / width ** 2 * mutual_parallel(l, s), 0.0, width,
                  limit=200, epsabs=1e-12, epsrel=1e-10)
    return val


def partial_tube(l: float, a: float) -> float:
    """Eq. (B4): partial self-inductance (nH) of a straight thin-walled tube, length l, radius a (mm)."""
    val, _ = quad(lambda psi: mutual_parallel(l, 2.0 * a * math.sin(psi / 2.0)) / (2.0 * math.pi),
                  0.0, 2.0 * math.pi, limit=200, epsabs=1e-12, epsrel=1e-10)
    return val


def gmd_estimate(l: float, gmd: float) -> float:
    """Eq. (B5): the GMD shortcut, for the cross-check only."""
    return MU0_OVER_2PI * l * (math.log(2.0 * l / gmd) - 1.0)


def part_b() -> None:
    print("(B) Partial self-inductance of straight conductors, Eqs. (B1)-(B5); mu0/2pi = 0.2 nH/mm")
    for l, wd in ((0.35, 0.2), (1.0, 0.2), (2.8, 0.2)):
        exact = partial_strip(l, wd)
        short = gmd_estimate(l, wd * math.exp(-1.5))
        print(f"  strip l = {l:.2f} mm, w = {wd:.2f} mm: Eq. (B3) {exact:.3f} nH; "
              f"GMD shortcut (B5), GMD = w e^-1.5 = {wd * math.exp(-1.5):.4f} mm: {short:.3f} nH")
    l, a = 1.6, 0.15
    print(f"  tube  l = {l:.2f} mm, a = {a:.2f} mm (via, 0.3-mm drill, 1.6-mm board): Eq. (B4) "
          f"{partial_tube(l, a):.3f} nH; GMD shortcut, GMD = a: {gmd_estimate(l, a):.3f} nH")
    print()


# ================================================================================================
# (C) Routing in series with the whole feedback network
# ================================================================================================
# Between the amplifier's output pin and the summing-node pin, the feedback network R_F || C_F sits
# in series with the inductance L_x of the routing (pins, traces, vias).  With Z_F = R_F / (1 + j w
# R_F C_F), i.e. 1/Z_F = 1/R_F + j w C_F, the network the amplifier sees is Z_F' = Z_F + j w L_x and
#
#     Z_F' / Z_F = 1 + j w L_x / Z_F = 1 + j w L_x (1/R_F + j w C_F)
#                = 1 - w^2 L_x C_F + j w L_x / R_F.                                       (C1)
#
# Two small numbers measure the change: delta_1 = w^2 L_x C_F, the fractional change of the
# capacitive part (the capacitance looks larger by 1/(1 - delta_1)), and delta_2 = w L_x / R_F,
# the phase added, in radians.  They are evaluated at the loop crossover, where C_F sets the phase
# margin: 801 MHz for the OPA855 design (SPICE, Section 4.3) and 308 MHz for the OPA846 design
# (SPICE, Section 4.5; the analytical model gives 237 MHz, and the higher value is used).  C_F is
# the total feedback capacitance of each design (Table 4.1): 0.20 pF and 0.75 pF.
#
# L_x is the sum of the partial self-inductances of the routing segments, Eqs. (B3)-(B4), first
# alone and then with an allowance for the package lead and bond wire of the output pin.  The
# datasheets give no package inductance; TI's OPA846 model puts 2.35 nH at the inverting input
# (Table B.1), and that value is taken, as an assumption, for the output pin of either package.
# (The output pin's inductance also carries the load current, which this estimate leaves out.)
#
# What the sum leaves out, and in which direction.  (i) Mutual inductance between perpendicular
# segments is exactly zero (dl . dl' = 0 in the Neumann formula).  (ii) Between the parallel
# segments of these layouts the currents run in opposite directions (the path out to the resistor
# and the path back from it), and opposite currents subtract their mutual inductance; leaving it
# out makes L_x larger.  (iii) The return current, in the ground planes and the supply bypass
# network, also flows opposite to the signal path, and its mutual inductance with it likewise
# lowers the loop inductance; its own partial inductance is left out too, which goes the other way,
# but a wide plane has a far smaller partial inductance than a 0.2-mm trace.  The sum is therefore
# an estimate on the high side, not a bound.
#
# Segment lengths from the layouts (scripts in numerical/):
#  * OPA855 (g_resistor_3d.py, opa855_layout): a 0.2-mm trace from each 0402 pad edge, y = l/2 =
#    0.30 mm (land pattern l = 0.60 mm, pcbcap/parts.py), to the pin at y = 0.65 mm: 0.35 mm each.
#  * OPA846 (g_opa846_3d.py): pins 1 (output, A) at (-1.3, 0.95) and 4 (inverting input, B) at
#    (1.3, -0.95); the resistor's pad centres are hp = s/2 + w/2 from its centre (0402: 0.475 mm,
#    land pattern s = 0.40, w = 0.55 mm).  Lengths are measured centre line to centre line, which
#    includes the stretches inside the pads (an overestimate).
#      double_sided: per side a via through the 1.6-mm board (drill 0.3 mm) and two bottom
#                    traces, (-0.95, 0.95) -> (-0.95, 0) -> (-hp, 0): 0.95 and 0.95 - hp = 0.475 mm;
#      under_body:   the resistor's centre is at (x1 + hp, 1.25 + 0.3 + l/2) = (-0.825, 1.85);
#                    A runs (-1.3, 0.95) -> (-1.3, 1.85): 0.90 mm; B runs from the other pad,
#                    (-0.35, 1.85) -> (-0.35, -0.95) -> (1.3, -0.95): 2.80 + 1.65 mm;
#      around:       the resistor's centre is at (x4 - hp, -1.85) = (0.825, -1.85);
#                    B runs (1.3, -0.95) -> (1.3, -1.85): 0.90 mm; A runs (-1.3, 0.95) ->
#                    (-2.3, 0.95) -> (-2.3, -1.85) -> (0.35, -1.85): 1.00 + 2.80 + 2.65 mm.
TRACE_W = 0.2           # mm, g_opa846_3d.TRACE and the OPA855 traces
BOARD_H = 1.6           # mm
VIA_A = 0.15            # mm, barrel radius (0.3-mm drill, packages.add_via)
PACKAGE_ALLOWANCE = 2.35  # nH, assumption: TI OPA846 model's inverting-input inductance (Table B.1)

LAYOUTS = {
    # name: (list of trace segment lengths in mm, number of vias)
    "OPA855, 0402 beside the pins": ([0.35, 0.35], 0),
    "OPA846 double-sided, 0402": ([0.95, 0.95 - 0.475, 0.95, 0.95 - 0.475], 2),
    "OPA846 same side, under the body, 0402": ([0.90, 2.80, 1.65], 0),
    "OPA846 same side, around, 0402": ([0.90, 1.00, 2.80, 2.65], 0),
}
DESIGNS = {
    # name: (crossover frequency Hz, C_F total pF, R_F ohm), Sections 4.3, 4.5 and Table 4.1
    "OPA855": (801e6, 0.20, 2000.0),
    "OPA846": (308e6, 0.75, 2000.0),
}


def routing_inductance(segments: list[float], vias: int) -> float:
    return sum(partial_strip(l, TRACE_W) for l in segments) + vias * partial_tube(BOARD_H, VIA_A)


def part_c() -> None:
    print("(C) Routing in series with R_F || C_F, Eq. (C1): delta_1 = w^2 L_x C_F, delta_2 = w L_x / R_F")
    for name, (segs, nv) in LAYOUTS.items():
        lr = routing_inductance(segs, nv)
        design = "OPA855" if name.startswith("OPA855") else "OPA846"
        f, cf_pf, rf = DESIGNS[design]
        om = w(f)
        print(f"  {name}: routing {lr:.2f} nH (segments {[round(s, 3) for s in segs]} mm, {nv} vias); "
              f"at {f / 1e6:.0f} MHz, C_F = {cf_pf:.2f} pF, R_F = {rf / 1e3:.0f} kohm")
        for label, lx in (("routing only", lr), (f"routing + {PACKAGE_ALLOWANCE:.2f} nH package", lr + PACKAGE_ALLOWANCE)):
            d1 = om ** 2 * lx * 1e-9 * cf_pf * 1e-12
            d2 = om * lx * 1e-9 / rf
            print(f"      {label}, L_x = {lx:.2f} nH: delta_1 = ({om:.3e})^2 x {lx:.2f}e-9 x {cf_pf:.2f}e-12 "
                  f"= {d1:.4f} ({100 * d1:.2f} %); delta_2 = {om:.3e} x {lx:.2f}e-9 / {rf:.0f} = {d2:.4f} rad "
                  f"({math.degrees(d2):.2f} deg)")
    print()


# ================================================================================================
# (D) Inductance in series with the photodiode
# ================================================================================================
# The photodiode is a current source I_ph in parallel with its capacitance C_D; the path to the
# summing node adds a series inductance L_PD.  Replace the source and C_D by their Thevenin
# equivalent, V = I_ph / (j w C_D) behind 1/(j w C_D); add j w L_PD in series:
#     Z_s = 1/(j w C_D) + j w L_PD = (1 - w^2 L_PD C_D) / (j w C_D);
# and convert back to a Norton source:  I_sc = V / Z_s and Y_s = 1/Z_s, i.e.
#
#     I_sc = I_ph / (1 - w^2 L_PD C_D),     C_D,eff = C_D / (1 - w^2 L_PD C_D).            (D1)
#
# The node therefore sees a photocurrent and a photodiode capacitance both raised by the factor
# 1/(1 - w^2 L_PD C_D), which grows without bound at the series resonance f_s = 1/(2 pi
# sqrt(L_PD C_D)).  C_D = 1 pF (Table 4.1).  L_PD is computed from Eq. (B3) for a 0.2-mm trace of
# the stated length; the lengths are illustrations, not the note's layouts, which put the
# photodiodes directly at the summing node (Section 8.10).  The 5-mm example is a pair of leads of
# 0.45-mm diameter, each a round wire with its current on the surface (Eq. (B4)); their partial
# self-inductances are added, which leaves out the mutual inductance of the two leads.  They carry
# opposite currents (to the summing node and back from the bias bypass), so that mutual term would
# lower the total: the 5-mm value is on the high side.
C_D_PF = 1.0


def part_d() -> None:
    print("(D) Inductance in series with the photodiode, Eq. (D1): factor 1/(1 - w^2 L_PD C_D)")
    cases = [("1-mm trace", partial_strip(1.0, TRACE_W)),
             ("3-mm trace", partial_strip(3.0, TRACE_W)),
             ("two 5-mm leads, 0.45 mm diameter", 2 * partial_tube(5.0, 0.225))]
    for label, lpd in cases:
        fs = 1.0 / (2 * math.pi * math.sqrt(lpd * 1e-9 * C_D_PF * 1e-12))
        parts = []
        for design, (f, _, _) in DESIGNS.items():
            x = w(f) ** 2 * lpd * 1e-9 * C_D_PF * 1e-12
            parts.append(f"{design} at {f / 1e6:.0f} MHz: w^2 L C = {x:.4f}, factor {1 / (1 - x):.4f}")
        print(f"  {label}: L_PD = {lpd:.2f} nH, series resonance with 1 pF at {fs / 1e9:.2f} GHz; "
              + "; ".join(parts))
    print()


# ================================================================================================
# (E) The film beyond first order in frequency (Table G.6, row 5)
# ================================================================================================
# Appendix G treats the resistive film to first order in w (Eqs. (G.7)-(G.8)) and states the
# condition w R_F C << 1 (Table G.6, row 5), whose parameter it quotes at 150 MHz.  At the OPA855
# crossover the same parameter is about 1, so the size of the next term is worth knowing.  The
# standard example is a uniform RC line: total series resistance R = r g and total capacitance to
# ground C = c g over the length g.  Its voltage and current obey
#     dV/dx = -r I,   dI/dx = -j w c V   =>   d2V/dx2 = j w r c V = (theta/g)^2 V,  theta^2 = j w R C.
# With V(0) = V_1 and V(g) = 0 (end B held at virtual ground) the solution is
#     V(x) = V_1 sinh(theta (1 - x/g)) / sinh(theta),
# and the current delivered into B is I_B = -(1/r) dV/dx at x = g = (V_1 / R) theta / sinh(theta).
# Expanding with sinh(theta) = theta (1 + theta^2/6 + theta^4/120 + theta^6/5040 + ...), i.e.
# theta/sinh(theta) = 1/(1 + y), y = theta^2/6 + theta^4/120 + theta^6/5040, and 1/(1+y) =
# 1 - y + y^2 - y^3 + ..., collecting powers of theta^2:
#     theta^2:  -1/6
#     theta^4:  -1/120 + 1/36                      =  7/360
#     theta^6:  -1/5040 + 2 (1/6)(1/120) - 1/216   = -31/15120
# so, with theta^2 = j x and x = w R C,
#     I_B / V_1 = (1/R) [ 1 - j x/6 - 7 x^2/360 + j 31 x^3/15120 + ... ].
# The imaginary part, -(x/6R)(1 - 31 x^2/2520), is j w times the effective capacitance -C/6 (the
# first-order result, the field form of Eq. (G.8) for a film coupled only to ground) multiplied by
# (1 - 31 x^2 / 2520).  The relative correction to the capacitive part is therefore 31 x^2 / 2520.
def part_e() -> None:
    print("(E) The film beyond first order: capacitive part of a uniform RC line scales by (1 - 31 x^2/2520)")
    for f, label in ((150e6, "band edge used in Table G.6"), (801e6, "OPA855 crossover")):
        x = w(f) * 2000.0 * 0.1e-12          # R_F = 2 kohm, C = 0.1 pF, as in Table G.6 row 5
        print(f"  {label}, {f / 1e6:.0f} MHz: x = w R C = {w(f):.3e} x 2000 x 0.1e-12 = {x:.3f}; "
              f"31 x^2/2520 = {31 * x * x / 2520:.4f} ({100 * 31 * x * x / 2520:.2f} %)")
    print()


# ================================================================================================
# (F) The leads of the SOT-23-5, SOIC-8 and PDIP-8 packages, and the high-gain range
# ================================================================================================
# The leads outside the body are part of the path between the amplifier and its feedback network,
# like the routing of (C), so they add to L_x.  Each lead's path from where the routing meets it to
# the body is a chain of straight segments, and their partial self-inductances, Eqs. (B3)-(B4), are
# summed as in (C); the same reasons make the sum an estimate on the high side.  The dimensions are
# those of the package models (pcbcap.packages, whose docstrings give their sources):
#   * gull-wing lead (SOT-23-5 and SOIC-8): the current enters the foot along its soldered length, so
#     half the foot is counted; then the riser, from the pad up to the shoulder's centre (stand-off +
#     shoulder height + half a lead thickness); then the shoulder outside the body.  Strips of the
#     lead's width.
#   * through-hole lead (PDIP-8) with the network on the solder side (g_eight_lead_3d.py, dip8_bottom):
#     the current runs from the bottom pad up the filled hole, a tube of the hole's radius over the
#     board's thickness (Eq. (B4)); up the shoulder from the seating plane to the exit's centre
#     (stand-off + exit height + half a lead thickness); and along the exit to the body.  Strips of
#     the shoulder's width.
# No drawing dimensions the lead frame inside the body (the finger and the bond wire to the die).
# As in (C), the 2.35 nH that TI's OPA846 model puts at its inverting input (Table B.1) stands in for
# it, here for both pins and every package, as an assumption.  Because the assumption is not a
# measurement, the result is also stated the other way round: the largest L_x that keeps delta_1
# below 1 %, L_max = 0.01 / (w^2 C_F), from Eq. (C1).
#
# The high-gain range.  delta_1 = w^2 L_x C_F does not depend on R_F, and delta_2 = w L_x / R_F falls
# as R_F grows, so what decides is the frequency of the loop crossover, where C_F sets the phase
# margin.  That frequency is f_c = GBW C_F / (C_F + C_T) for an amplifier of gain-bandwidth GBW,
# because at high frequency the feedback factor is the capacitive divider C_F / (C_F + C_T) and the
# loop gain GBW / f times it is 1 at f_c.  It varies from design to design, so instead of one bound
# the result is given as the crossover frequency below which delta_1 stays under 1 %:
#     delta_1 = (2 pi f)^2 L_x C_F <= 0.01   <=>   f <= f_1% = sqrt(0.01 / (L_x C_F)) / (2 pi),
# for each package's L_x (the layouts above, both pins counted) and C_F from 0.1 to 1 pF.  For
# comparison: the precision amplifiers of the high-gain note in these packages have gain-bandwidth
# products of a few to 80 MHz (OPA637: 80 MHz at a gain of 10, SBOS165C, p. 12), which bound their
# crossovers; its wideband FET parts reach 230 MHz to 4 GHz (high-gain note, Section 6.1), and only
# they, at its lowest gains, can approach f_1%.  The resistor's own inductance (A) is evaluated for
# the 0805 at 10 kohm.
LEAD_INTERNAL = 2.35      # nH per pin, assumption (TI OPA846 model, Table B.1), as PACKAGE_ALLOWANCE


def lead_paths():
    """{package: [(kind, length mm, width or radius mm), ...]} for one lead (comments above)."""
    import sys
    sys.path.insert(0, str(HERE.parents[2] / "pcbcap"))     # HERE is this script's folder
    from pcbcap import packages as pk
    s23, so8, dip = pk.Sot23(), pk.Soic8(), pk.Dip8()
    out = {}
    for name, p in (("SOT-23-5", s23), ("SOIC-8", so8)):
        riser = p.standoff + p.shoulder_height + p.lead_thickness / 2
        shoulder = max(0.0, (p.lead_span - p.body_width) / 2 - p.foot_length - p.lead_thickness)
        segs = [("strip", p.foot_length / 2, p.lead_width), ("strip", riser, p.lead_width)]
        if shoulder > 0:
            segs.append(("strip", shoulder, p.lead_width))
        out[name] = segs
    shoulder = dip.standoff + dip.exit_height + dip.lead_thickness / 2
    exit_len = dip.row / 2 - dip.lead_thickness / 2 - dip.body_width / 2
    out["PDIP-8"] = [("tube", BOARD_H, dip.drill / 2), ("strip", shoulder, dip.shoulder_width),
                     ("strip", exit_len, dip.shoulder_width)]
    return out


def segment_inductance(kind: str, length: float, size: float) -> float:
    return partial_strip(length, size) if kind == "strip" else partial_tube(length, size)


# Routing of the eight-lead layouts (g_eight_lead_3d.py), centre line to centre line as in (C):
#   SOIC-8 double_sided, 0402 (hp = 0.475): per side a via through the board and the bottom traces
#     (2.2, -0.635) -> (2.2, 0) -> (0.475, 0): 0.635 and 1.725 mm;
#   PDIP-8 dip8_bottom, 0402 for the 2-kohm comparison: per side the bottom traces (3.81, -1.27) ->
#     (3.81, 0) -> (0.475, 0): 1.27 and 3.335 mm (no via: the holes are part of the leads above).
ROUTING_8 = {"SOIC-8": ([0.635, 1.725, 0.635, 1.725], 2), "PDIP-8": ([1.27, 3.335, 1.27, 3.335], 0)}


def part_f(cf_best: dict[str, float]) -> None:
    print("(F) Package leads, Eqs. (B3)-(B4), and Eq. (C1) at the OPA846 crossover and in the high-gain range")
    per_lead = {}
    for name, segs in lead_paths().items():
        parts_ = [segment_inductance(*s) for s in segs]
        per_lead[name] = sum(parts_)
        desc = ", ".join(f"{k} {l:.3f} mm x {sz:.3f} mm: {v:.3f} nH" for (k, l, sz), v in zip(segs, parts_))
        print(f"  {name} lead outside the body: {desc}; total {per_lead[name]:.3f} nH")
    f, cf_pf, rf = DESIGNS["OPA846"]
    om = w(f)
    lmax = 0.01 / (om ** 2 * cf_pf * 1e-12) * 1e9
    print(f"  OPA846 design: {f / 1e6:.0f} MHz, C_F = {cf_pf:.2f} pF, R_F = {rf / 1e3:.0f} kohm; "
          f"L_max for delta_1 = 1 %: 0.01 / (({om:.3e})^2 x {cf_pf:.2f}e-12) = {lmax:.2f} nH")
    for name in ("SOIC-8", "PDIP-8"):
        segs, nv = ROUTING_8[name]
        lr = routing_inductance(segs, nv)
        lx = lr + 2 * per_lead[name] + 2 * LEAD_INTERNAL
        d1 = om ** 2 * lx * 1e-9 * cf_pf * 1e-12
        d2 = om * lx * 1e-9 / rf
        print(f"    {name}: routing {lr:.2f} nH + leads 2 x {per_lead[name]:.2f} nH + inside 2 x {LEAD_INTERNAL:.2f} nH "
              f"= L_x {lx:.2f} nH; delta_1 = {d1:.4f} ({100 * d1:.2f} %), delta_2 = {d2:.4f} rad "
              f"({math.degrees(d2):.2f} deg)")
    # Same accounting for the SOT-23-5 double-sided layout of (C), for comparison.
    segs23, nv23 = LAYOUTS["OPA846 double-sided, 0402"]
    lx23 = routing_inductance(segs23, nv23) + 2 * per_lead["SOT-23-5"] + 2 * LEAD_INTERNAL
    d1 = om ** 2 * lx23 * 1e-9 * cf_pf * 1e-12
    print(f"    SOT-23-5 (same accounting, both pins): L_x {lx23:.2f} nH; delta_1 = {d1:.4f} ({100 * d1:.2f} %)")
    # High-gain range: the crossover frequency below which delta_1 < 1 % (comments above)
    print("  High-gain range: f_1% = sqrt(0.01 / (L_x C_F)) / (2 pi), the crossover below which delta_1 < 1 %")
    lxs = {"SOT-23-5": lx23}
    for name in ("SOIC-8", "PDIP-8"):
        segs, nv = ROUTING_8[name]
        lxs[name] = routing_inductance(segs, nv) + 2 * per_lead[name] + 2 * LEAD_INTERNAL
    for name, lx in lxs.items():
        row = []
        for c in (0.1, 0.2, 0.5, 1.0):
            f1 = math.sqrt(0.01 / (lx * 1e-9 * c * 1e-12)) / (2 * math.pi)
            row.append(f"C_F {c:.1f} pF: {f1 / 1e6:.0f} MHz")
        print(f"    {name}, L_x {lx:.2f} nH: " + "; ".join(row))
    lx = lxs["PDIP-8"]
    for f2, r2 in ((80e6, 10e3), (80e6, 100e3), (10e6, 1e6)):
        om2 = w(f2)
        print(f"    delta_2 = w L_x / R_F with the PDIP-8's L_x at {f2 / 1e6:g} MHz and {r2 / 1e3:g} kohm: "
              f"{om2 * lx * 1e-9 / r2:.2e} rad ({math.degrees(om2 * lx * 1e-9 / r2):.4f} deg)")
    ls = L_S_KOA["0805"]
    print(f"  Resistor's own inductance, Eq. (A4): 0805, L_s = {ls:.1f} nH, at 10 kohm L_s/R^2 = "
          f"{ls * 1e-9 / 1e8 * 1e15:.4f} fF against C_p = {cf_best['0805']:.1f} fF "
          f"({100 * ls * 1e-9 / 1e8 * 1e15 / cf_best['0805']:.3f} %)")
    print()


def main() -> None:
    rec = json.loads(RECORD_3D.read_text(encoding="utf-8"))
    cf_best = {s: rec[f"size_{s}"]["C_F_best"] for s in ("0201", "0402", "0603", "0805")}
    part_a(cf_best)
    part_b()
    part_c()
    part_d()
    part_e()
    part_f(cf_best)


if __name__ == "__main__":
    main()
