"""Analytical estimate of the parasitic capacitance across the feedback resistor of a TIA.

Usage:
    python cf_parasitic_estimate.py                     # confirmations and the estimate
    python cf_parasitic_estimate.py --json <out.json>   # also write every number

Every formula evaluated here is derived step by step in
Appendix G of TIA_opamp_survey.md; the equation numbers (G.n) in the comments refer
to that document.  The section "numerical confirmations" at the end evaluates each formula a
second, independent way (quadrature of the defining integral, the arithmetic-geometric mean,
a limiting case with a known answer).  These confirmations check the implementation and the
algebra; they are not a substitute for the derivations.

Units: lengths in mm, capacitance in fF, so that eps0 = 8.8541878128 fF/mm.

Special functions (all from scipy.special, which uses the PARAMETER m = k^2, not the modulus k):
    ellipk(m)        K(m)   = int_0^{pi/2} dtheta / sqrt(1 - m sin^2 theta)        (Eq. (G.14))
    ellipkm1(p)      K(1-p), accurate when p is small (it is K evaluated at parameter 1 - p)
    ellipkinc(phi,m) F(phi|m) = int_0^phi dtheta / sqrt(1 - m sin^2 theta)        (Eq. (G.15))
    ellipj(u,m)[0]   sn(u|m) = sin(phi) where F(phi|m) = u                         (Eq. (G.15))
"""
from __future__ import annotations

import argparse
import cmath
import json
import math
from pathlib import Path

import numpy as np
from scipy.integrate import quad
from scipy.optimize import brentq
from scipy.special import ellipj, ellipk, ellipkinc, ellipkm1

EPS0 = 8.8541878128  # vacuum permittivity in fF/mm (8.8541878128e-12 F/m)


# =====================================================================================
# Special functions (Section G.5 of the note)
# =====================================================================================
def K(m: float) -> float:
    """K(m), complete elliptic integral of the first kind, parameter m in [0, 1) (Eq. (G.14))."""
    return float(ellipk(m))


def K_of_1_minus(m: float) -> float:
    """K(1 - m), computed with ellipkm1 so that it stays accurate for small m."""
    return float(ellipkm1(m))


def ratio(m: float) -> float:
    """K(m)/K(1 - m) for 0 < m < 1: the capacitance per unit length, divided by the permittivity,
    of two electrodes on the edge of a half-plane whose parameter is m (Eq. (G.23))."""
    return K(m) / K_of_1_minus(m)


def ratio_from_p(p: float) -> float:
    """K(1 - p)/K(p), the same ratio written for m = 1 - p; accurate when m is close to 1."""
    return K_of_1_minus(p) / K(p)


def sn(u: float, m: float) -> float:
    """Jacobi sn(u|m), the inverse of the incomplete integral F (Eq. (G.15))."""
    return float(ellipj(u, m)[0])


def F_inc(phi: float, m: float) -> float:
    """F(phi|m), incomplete elliptic integral of the first kind (Eq. (G.15))."""
    return float(ellipkinc(phi, m))


# =====================================================================================
# Two electrodes on the edge of a half-plane (Section G.6)
# =====================================================================================
def parameter_from_points(x1: float, x2: float, x3: float, x4: float) -> float:
    """m = (x2 - x1)(x4 - x3) / ((x4 - x2)(x3 - x1)) for x1 < x2 < x3 < x4 (Eq. (G.17));
    x1 = -inf gives the limit (x4 - x3)/(x4 - x2) (Eq. (G.24))."""
    if x1 == -math.inf:
        return (x4 - x3) / (x4 - x2)
    return (x2 - x1) * (x4 - x3) / ((x4 - x2) * (x3 - x1))


def halfplane(x1: float, x2: float, x3: float, x4: float) -> float:
    """Capacitance per unit length / permittivity between electrodes [x1, x2] and [x3, x4] on the
    edge of a half-plane, the rest of the edge insulating (Eq. (G.23))."""
    return ratio(parameter_from_points(x1, x2, x3, x4))


# =====================================================================================
# Coplanar pads (Section G.7)
# =====================================================================================
def cps(w: float, s: float) -> float:
    """Two coplanar strips of width w and gap s on the edge of a half-plane:
    K(m)/K(1-m) with m = (w/(s+w))^2 (Eq. (G.25)).  Per unit permittivity, one half-space."""
    return ratio((w / (s + w)) ** 2)


def cps_layer_cut(w: float, s: float, d: float) -> float:
    """The same strips on a layer of thickness d whose far face is an insulating cut (Eq. (G.27)):
    m = [sinh(pi w/(2d)) / sinh(pi (s+w)/(2d))]^2."""
    m = (math.sinh(math.pi * w / (2 * d)) / math.sinh(math.pi * (s + w) / (2 * d))) ** 2
    return ratio(m)


# =====================================================================================
# The resistor body (Section G.8)
# =====================================================================================
def body_parameter(L: float, T: float) -> float:
    """m_b with K(1 - m_b)/K(m_b) = 2T/L (Eq. (G.29)).  The left side falls strictly from +inf to 0
    as m_b goes from 0 to 1, so the root is unique; it is bracketed and found by Brent's method."""
    target = 2.0 * T / L
    return brentq(lambda m: K_of_1_minus(m) / K(m) - target, 1e-15, 1 - 1e-15, xtol=1e-16, rtol=1e-15)


def block_without_film(L: float, T: float, g: float) -> dict:
    """Block between the terminations with the film's prescribed potential removed (lower bound,
    Eqs. (G.29)-(G.32)).  Returns the capacitance per unit width / permittivity and the intermediate
    quantities."""
    m_b = body_parameter(L, T)
    s_g = sn(K(m_b) * g / L, m_b)
    mu = m_b * s_g ** 4                                                    # Eq. (G.32)
    return dict(m_b=m_b, sn=s_g, mu=mu, value=K_of_1_minus(mu) / (2.0 * K(mu)))   # Eq. (G.32)


def block_slots_filled(T: float, g: float) -> float:
    """Block with the termination slots filled with metal (upper bound, Eq. (G.28)): T/g."""
    return T / g


# =====================================================================================
# The air above the body, flattened (Section G.9)
# =====================================================================================
def air_flat_without_film(g: float, X: float) -> float:
    """Electrodes [g/2, X] and [-X, -g/2] on the edge of the half-plane above the body, the gap
    insulating (Eq. (G.33))."""
    return cps(X - g / 2.0, g)


def air_flat_with_film(g: float, X: float, n_terms: int = 400000) -> dict:
    """Same electrodes with the film's linear potential prescribed on the gap (Eqs. (G.34)-(G.38)):
    half-strip map zeta = X sin(w), series phi = sum b_n sin(M u) exp(-M v), M = 2n + 1,
    energy (pi/2) sum M b_n^2.  Potentials +-1/2, so the value is C'/eps."""
    ug = math.asin(min(1.0, g / (2.0 * X)))
    M = 2.0 * np.arange(n_terms) + 1.0

    def S(j):
        out = np.empty_like(j)
        zero = j == 0
        out[zero] = ug
        out[~zero] = np.sin(j[~zero] * ug) / j[~zero]
        return out

    I1 = 0.5 * (S(M - 1.0) - S(M + 1.0))                   # int_0^ug sin u sin(M u) du
    I2 = np.cos(M * ug) / M                                 # int_ug^{pi/2} sin(M u) du
    b = (4.0 / math.pi) * ((X / g) * I1 + 0.5 * I2)        # Eq. (G.37)
    terms = M * b ** 2
    value = (math.pi / 2.0) * float(np.sum(terms))         # Eq. (G.38)
    # the terms fall as M^-3 (b_n ~ M^-2), so the remainder after N terms is about N/2 times
    # the last term; reported as the truncation estimate
    tail = 0.5 * float(terms[-1]) * n_terms * (math.pi / 2.0)
    return dict(value=value, tail_estimate=tail, b0=float(b[0]), u_g=ug)


def film_series_boundary(g: float, X: float, u: np.ndarray, n_terms: int = 20000) -> np.ndarray:
    """Partial sum of the series on the bottom edge v = 0, for comparison with the prescribed data."""
    ug = math.asin(min(1.0, g / (2.0 * X)))
    M = 2.0 * np.arange(n_terms) + 1.0
    j1, j2 = M - 1.0, M + 1.0
    S1 = np.where(j1 == 0, ug, np.sin(j1 * ug) / np.where(j1 == 0, 1.0, j1))
    S2 = np.sin(j2 * ug) / j2
    b = (4.0 / math.pi) * ((X / g) * 0.5 * (S1 - S2) + 0.5 * np.cos(M * ug) / M)
    return np.sin(np.outer(u, M)) @ b


# =====================================================================================
# A ground plane under the pads (Section G.10)
# =====================================================================================
def board_over_plane(w: float, s: float, h: float) -> dict:
    """Pads of width w, gap s, on a layer of thickness h over a ground plane, insulating cut on
    the board surface outside the pads (Eqs. (G.39)-(G.41)).  Per unit permittivity of the layer:
    q_odd, q_even = charge on one pad per volt in the odd and even excitations,
    mutual = (q_odd - q_even)/2, to_ground = q_even."""
    a = math.pi / (4.0 * h)
    p_odd = (math.sinh(a * s) / math.sinh(a * (s + 2 * w))) ** 2          # Eq. (G.41)
    p_even = (math.cosh(a * s) / math.cosh(a * (s + 2 * w))) ** 2         # Eq. (G.41)
    q_odd = ratio_from_p(p_odd)
    q_even = ratio_from_p(p_even)
    return dict(q_odd=q_odd, q_even=q_even, mutual=(q_odd - q_even) / 2.0, to_ground=q_even,
                p_odd=p_odd, p_even=p_even)


def guard_in_gap(w: float, s: float, wg: float) -> dict:
    """Pads [s/2, s/2+w] and mirror with a grounded strip of width wg centred in the gap, on the
    edge of the board region (cut elsewhere), Section G.10.5, Eq. (G.43).  By symmetry each excitation lives on
    the quarter-plane x > 0 below the surface, which zeta = q^2 maps onto a half-plane:
      odd  (wall at 0 V):     grounded electrode (-inf, wg^2/4], pad [s^2/4, X^2]
      even (wall insulating): grounded electrode [0, wg^2/4],    pad [s^2/4, X^2]
    Per unit permittivity: mutual = (q_odd - q_even)/2, to_guard = q_even (each pad)."""
    X = s / 2 + w
    p_odd = (s ** 2 - wg ** 2) / (4 * X ** 2 - wg ** 2)                         # 1 - m_odd
    m_even = wg ** 2 * (4 * X ** 2 - s ** 2) / ((4 * X ** 2 - wg ** 2) * s ** 2)
    q_odd = ratio_from_p(p_odd)
    q_even = ratio(m_even) if wg > 0 else 0.0
    return dict(q_odd=q_odd, q_even=q_even, mutual=(q_odd - q_even) / 2.0, to_guard=q_even,
                p_odd=p_odd, m_even=m_even)


def film_weight(r: float) -> float:
    """Average of xi (1 - xi) over the middle fraction r of the film: 1/4 - r^2/12; r = 1 gives
    1/6, the uniform case of Eq. (G.10) (Eq. (G.44))."""
    return 0.25 - r ** 2 / 12.0


def film_to_ground(area: float, T: float, eps_al: float, gap_air: float, h: float, eps_pcb: float) -> float:
    """Capacitance from the film to a plane below the board surface, as three dielectric layers in
    series (Eq. (G.42); parallel-plate approximation, see approximation 10).  fF."""
    return EPS0 * area / (T / eps_al + gap_air + h / eps_pcb)


# =====================================================================================
# Package pins (Section G.11)
# =====================================================================================
def pins(b: float, pitch: float) -> dict:
    """Pins 1 and 3 of a 0.5-mm-pitch package with pin 2 floating between them (Eqs. (G.45)-(G.46)).
    without_middle: pins 1 and 3 alone, gap 2 pitch - b.
    floating_wall:  pin 2 enlarged to an infinite floating wall; by images, coplanar strips with
                    gap 2 (pitch - b)."""
    return dict(without_middle=cps(b, 2 * pitch - b), floating_wall=cps(b, 2 * (pitch - b)))


# =====================================================================================
# Inputs, from data/parasitic_cf/geometry_and_permittivity.md (manufacturer documents, pages
# there).  Body: L, W nominal; T = overall height H (min, nominal, max); a = top termination
# length (min, nominal, max).  Thick-film general-purpose values (Panasonic ERJ, Yageo RC,
# Vishay CRCW, KOA RK73B, TT WCR agree); thin-film parts lie inside the same tolerance bands.
# =====================================================================================
CHIPS = {
    "0201": dict(L=0.60, W=0.30, T=(0.20, 0.23, 0.26), a=(0.05, 0.10, 0.15)),
    "0402": dict(L=1.00, W=0.50, T=(0.30, 0.35, 0.40), a=(0.10, 0.20, 0.30)),
    "0603": dict(L=1.60, W=0.80, T=(0.35, 0.45, 0.55), a=(0.10, 0.30, 0.50)),
    "0805": dict(L=2.00, W=1.25, T=(0.40, 0.50, 0.70), a=(0.20, 0.40, 0.60)),
}
# Land patterns: IPC-7351-based reflow table of Vishay document 28950 (Rev. 12-Jul-2022, p. 1):
# gap s, pad length w along the resistor, pad width l across it, mm
PADS = {
    "0201": dict(w=0.43, l=0.42, s=0.27),
    "0402": dict(w=0.55, l=0.60, s=0.40),
    "0603": dict(w=0.90, l=1.00, s=0.70),
    "0805": dict(w=0.90, l=1.45, s=1.00),
}
# Other published 0402 patterns, for the pad sensitivity: Yageo Mount V.10 Table 1 and KOA Appendix B
PADS_0402_VARIANTS = {"Yageo": dict(w=0.50, l=0.60, s=0.50), "KOA": dict(w=0.40, l=0.30, s=0.50),
                      "Vishay IEC 61188-6-2": dict(w=0.35, l=0.55, s=0.55)}
EPS_AL = (9.4, 10.0)      # 96 % (Kyocera A476, 9.4) to 99.6 % alumina (Kyocera A479U, 10), 1 MHz;
                          # CoorsTek AD-995: 9.7-9.8 at 1 MHz and at 4-5 GHz (no dispersion)
EPS_PCB = (3.65, 4.6)     # R-1650V prepreg 3.65 at 1 GHz to R-1755V 7628 core 4.57 at 100 MHz
EPS_MOULD = (3.1, 4.0)    # Hitachi CEL-9220HF10 3.1 to Panasonic CV8710 4.0, 1 MHz
BOARD_H = 1.6             # board thickness for the cut-layer bound, mm
DSG = dict(pitch=0.50, b=0.25, pad_len=0.50, under_pkg=0.30, wall_metal=(0.1, 0.2))  # OPA855 DSG0008A


# =====================================================================================
# Assembly (Section G.12)
# =====================================================================================
def resistor_on_pads(size: str, film: str = "up", dims: str = "nominal", pads: dict | None = None) -> dict:
    """Resistor on its pads, planes removed under them (Section G.12).  film = "up" (normal
    mounting, film facing the air) or "down" (mounted upside down, film facing the board,
    Section G.10.7).  dims = "nominal": both bounds at the nominal T and a; dims = "extremes":
    the lower bound at (T min, a min), the upper estimate at (T max, a max), i.e. across the
    data-sheet tolerances.  Returns the board, block and air terms as (low, high) pairs in fF,
    the lower bound of the two-dimensional model, a central value and an upper estimate."""
    c, p = CHIPS[size], (pads or PADS[size])
    L, W = c["L"], c["W"]
    i_lo, i_hi = (1, 1) if dims == "nominal" else (0, 2)
    T_lo, T_hi = c["T"][i_lo], c["T"][i_hi]
    w, l, s = p["w"], p["l"], p["s"]
    X = s / 2 + w
    g_long, g_short = L - 2 * c["a"][i_hi], L - 2 * c["a"][i_lo]   # long wraps give the short film
    c_hi, c_lo = min(g_long, s), min(g_short, s)                  # gap between conductors seen from the board
    bare = max(l - W, 0.0)                                        # pad width beyond the body
    # board region: over the body width the conductors are pad + bottom wrap; beyond it the pad alone
    lo_board = EPS_PCB[0] * EPS0 * (cps_layer_cut(X - c_lo / 2, c_lo, BOARD_H) * W + cps_layer_cut(w, s, BOARD_H) * bare)
    board_top = cps(X - c_hi / 2, c_hi)
    if film == "down":                                            # film's linear potential across the gap (Eq. (G.38))
        board_top = air_flat_with_film(c_hi, X)["value"]
    hi_board = EPS_PCB[1] * EPS0 * (board_top * W + cps(w, s) * bare)
    # block: rigorous range in the 2D model (Eqs. (G.28), (G.32)); unchanged by the orientation
    nofilm = block_without_film(L, T_lo, g_short)
    lo_block = EPS_AL[0] * EPS0 * nofilm["value"] * W
    hi_block = EPS_AL[1] * EPS0 * block_slots_filled(T_hi, g_long) * W
    # air above the body (flattened) and above the bare part of the pads
    air_lo = EPS0 * (air_flat_without_film(g_short, X) * W + cps(w, s) * bare)
    air_top = air_flat_with_film(g_long, X)["value"] if film == "up" else air_flat_without_film(g_long, X)
    air_hi = EPS0 * (air_top * W + cps(w, s) * bare)
    out = dict(board=(lo_board, hi_board), block=(lo_block, hi_block), air=(air_lo, air_hi),
               block_detail=dict(m_b=nofilm["m_b"], sn=nofilm["sn"], mu=nofilm["mu"], g_short=g_short, g_long=g_long,
                                 T_lo=T_lo, T_hi=T_hi))
    out["lower_bound_2d"] = lo_board + lo_block
    out["upper_estimate"] = hi_board + hi_block + air_hi
    out["central"] = 0.5 * (lo_board + hi_board) + 0.5 * (lo_block + hi_block) + 0.5 * (air_lo + air_hi)
    return out


def guard_example(size: str, wg: float, t_s: float, film: str) -> dict:
    """A grounded guard strip of width wg in the pad gap, under the body, at a standoff t_s below
    the body's lower face (Section G.10.5).  Board term from the quarter-plane result, film term
    from Eq. (G.10) restricted to the middle of the film, film-to-guard capacitance as layers in
    series.  Central permittivities.  t_s is a stated condition, not a measured value."""
    c, p = CHIPS[size], PADS[size]
    L, W, T = c["L"], c["W"], c["T"][1]
    w, l, s = p["w"], p["l"], p["s"]
    g = L - 2 * c["a"][1]
    e_pcb, e_al = 0.5 * (EPS_PCB[0] + EPS_PCB[1]), 0.5 * (EPS_AL[0] + EPS_AL[1])
    gd = guard_in_gap(w, s, wg)
    board = e_pcb * EPS0 * gd["mutual"] * l
    board_none = e_pcb * EPS0 * cps(w, s) * l
    area = min(wg, g) * W
    d = t_s if film == "down" else t_s + T / e_al
    Cg = EPS0 * area / d
    r = min(wg, g) / g
    return dict(board_with_guard=board, board_without=board_none, Cg=Cg, film_term=-Cg * film_weight(r),
                pad_to_guard=e_pcb * EPS0 * gd["to_guard"] * l, input_node_added=e_pcb * EPS0 * gd["to_guard"] * l + Cg / 2.0)


def body_alone(size: str, dims: str = "nominal") -> dict:
    """The resistor body without board or pads (Section G.13): the block of Eqs. (G.28)/(G.32) plus the
    air of Section G.9 with the terminations alone as electrodes ([g/2, L/2]).
    over_ground: block + air above the film side (the side below faces a test board over ground);
    free_standing: block + air on both faces, film on one of them.  (low, high) in fF; with
    dims = "nominal" both ends at the nominal T and a, with dims = "extremes" the low end at
    (T min, a min) and the high end at (T max, a max)."""
    c = CHIPS[size]
    L, W = c["L"], c["W"]
    i_lo, i_hi = (1, 1) if dims == "nominal" else (0, 2)
    g_long, g_short = L - 2 * c["a"][i_hi], L - 2 * c["a"][i_lo]
    nofilm = block_without_film(L, c["T"][i_lo], g_short)
    block = (EPS_AL[0] * EPS0 * nofilm["value"] * W, EPS_AL[1] * EPS0 * block_slots_filled(c["T"][i_hi], g_long) * W)
    top = (EPS0 * air_flat_without_film(g_short, L / 2) * W, EPS0 * air_flat_with_film(g_long, L / 2)["value"] * W)
    bottom = (EPS0 * air_flat_without_film(g_short, L / 2) * W, EPS0 * air_flat_without_film(g_long, L / 2) * W)
    return dict(block=block, over_ground=(block[0] + top[0], block[1] + top[1]),
                free_standing=(block[0] + top[0] + bottom[0], block[1] + top[1] + bottom[1]))


def cut_per_mm(w_side: float, delta: float, eps_al: float) -> float:
    """Capacitance per mm across a narrow cut of width delta between two film regions of width
    w_side, on the alumina-air interface (Eq. (G.26) with the film regions as electrodes), fF/mm.
    Weighted by (delta_phi/V)^2 it gives the cut's share of the film-pattern term (Eq. (G.49))."""
    return (eps_al + 1.0) * EPS0 * cps(w_side, delta)


def dsg_pins() -> dict:
    pp = pins(DSG["b"], DSG["pitch"])
    under, outside = DSG["under_pkg"], DSG["pad_len"] - DSG["under_pkg"]
    res = {}
    for key, val in pp.items():
        lo = EPS0 * val * ((EPS_MOULD[0] + EPS_PCB[0]) * under + (1.0 + EPS_PCB[0]) * outside)
        hi = EPS0 * val * ((EPS_MOULD[1] + EPS_PCB[1]) * under + (1.0 + EPS_PCB[1]) * outside)
        res[key] = (lo, hi)
    g = DSG["pitch"] - DSG["b"]
    res["wall_metal_term"] = tuple(EPS0 * EPS_MOULD[1] * t / (2 * g) * under for t in DSG["wall_metal"])  # Eq. (G.47)
    return res


# =====================================================================================
# Numerical confirmations (not proofs)
# =====================================================================================
def agm(a: float, b: float) -> float:
    for _ in range(200):
        a, b = 0.5 * (a + b), math.sqrt(a * b)
        if abs(a - b) <= 1e-16 * a:
            break
    return a


def K_by_agm(m: float) -> float:
    """K(m) = pi / (2 AGM(1, sqrt(1-m))) (DLMF 19.8.5), an independent evaluation."""
    return math.pi / (2.0 * agm(1.0, math.sqrt(1.0 - m)))


def K_by_quadrature(m: float) -> float:
    return quad(lambda t: 1.0 / math.sqrt(1.0 - m * math.sin(t) ** 2), 0.0, math.pi / 2, epsabs=1e-14, epsrel=1e-13)[0]


def side_integrals(m: float) -> dict:
    """The four side lengths of the Schwarz-Christoffel rectangle by direct quadrature of
    |dtau / sqrt(tau (tau - m)(tau - 1))| over each interval (Eqs. (G.19)-(G.22))."""
    top = quad(lambda t: 1 / math.sqrt(1 - t), 0, m, weight="alg", wvar=(-0.5, -0.5), epsabs=1e-13)[0]
    left = quad(lambda t: 1 / math.sqrt(t), m, 1, weight="alg", wvar=(-0.5, -0.5), epsabs=1e-13)[0]
    b1 = quad(lambda t: 1 / math.sqrt(t * (t - m)), 1, 2, weight="alg", wvar=(-0.5, 0), epsabs=1e-13)[0]
    b2 = quad(lambda t: 1 / math.sqrt(t * (t - m) * (t - 1)), 2, math.inf, epsabs=1e-13)[0]
    r1 = quad(lambda t: 1 / math.sqrt((t + m) * (t + 1)), 0, 1, weight="alg", wvar=(-0.5, 0), epsabs=1e-13)[0]
    r2 = quad(lambda t: 1 / math.sqrt(t * (t + m) * (t + 1)), 1, math.inf, epsabs=1e-13)[0]
    return dict(top=top, left=left, bottom=b1 + b2, right=r1 + r2, two_K=2 * K(m), two_K1m=2 * K_of_1_minus(m))


def sc_map(t_end: complex, m: float) -> complex:
    """f(t_end) = int_0^{t_end} dtau / (sqrt(tau) sqrt(tau - m) sqrt(tau - 1)), principal square
    roots (analytic in the upper half-plane), integrated from 0 to i along the imaginary axis and
    then along the straight segment from i to t_end; the endpoint singularity is handled with an
    algebraic weight when t_end is a corner."""
    def h(tau):
        return 1.0 / (cmath.sqrt(tau) * cmath.sqrt(tau - m) * cmath.sqrt(tau - 1))

    def cquad(fun, a, b, **kw):
        re = quad(lambda x: fun(x).real, a, b, limit=400, **kw)[0]
        im = quad(lambda x: fun(x).imag, a, b, limit=400, **kw)[0]
        return complex(re, im)

    # leg 1: tau = i y, y from 0 to 1; the integrand behaves as y^-1/2 at y = 0, so it is
    # multiplied by sqrt(y) (smooth) and integrated with the weight y^-1/2
    leg1 = cquad(lambda y: h(1j * max(y, 1e-30)) * 1j * math.sqrt(max(y, 1e-30)), 0.0, 1.0, weight="alg", wvar=(-0.5, 0.0))
    # leg 2: tau = i + u (t_end - i), u from 0 to 1; a corner endpoint gives (1-u)^-1/2
    d = t_end - 1j
    corner = any(abs(t_end - c) < 1e-15 for c in (0.0, m, 1.0))
    if corner:
        leg2 = cquad(lambda u: h(1j + u * d) * d * math.sqrt(1 - u) if u < 1 else 0j, 0.0, 1.0, weight="alg", wvar=(0.0, -0.5))
    else:
        leg2 = cquad(lambda u: h(1j + u * d) * d, 0.0, 1.0)
    return leg1 + leg2


def confirmations() -> dict:
    out = {}
    # C1: K by scipy, AGM and quadrature
    rows = []
    for m in (0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 0.999):
        a, b, c = K(m), K_by_agm(m), K_by_quadrature(m)
        rows.append(dict(m=m, scipy=a, agm=b, quad=c))
        assert abs(a - b) < 1e-13 * a and abs(a - c) < 1e-11 * a
    for m in (1e-6, 0.01, 0.3):
        assert abs(K_of_1_minus(m) - K(1 - m)) < 1e-9 * K(1 - m)
    out["C1_K_three_ways"] = rows
    # C2: the four side lengths of the rectangle
    rows = []
    for m in (0.1, 0.25, 0.6, 0.9):
        si = side_integrals(m)
        rows.append(dict(m=m, **si))
        assert abs(si["top"] - si["two_K"]) < 1e-9 and abs(si["bottom"] - si["two_K"]) < 1e-9
        assert abs(si["left"] - si["two_K1m"]) < 1e-9 and abs(si["right"] - si["two_K1m"]) < 1e-9
    out["C2_side_lengths"] = rows
    # C3: the corners of the map with the principal branches
    m = 0.3
    def h3(tau):
        return 1.0 / (cmath.sqrt(tau) * cmath.sqrt(tau - m) * cmath.sqrt(tau - 1))

    def near0(y):     # integrand times sqrt(y) on (0, 1]; smooth, so y = 0 is replaced by a tiny y
        y = max(y, 1e-30)
        return h3(1j * y) * 1j * math.sqrt(y)

    # f at infinity: along the imaginary axis, tau = i y, y from 0 to infinity
    far = complex(quad(lambda y: near0(y).real, 0.0, 1.0, weight="alg", wvar=(-0.5, 0.0))[0],
                  quad(lambda y: near0(y).imag, 0.0, 1.0, weight="alg", wvar=(-0.5, 0.0))[0])
    far += complex(quad(lambda y: (h3(1j * y) * 1j).real, 1.0, math.inf, limit=400)[0],
                   quad(lambda y: (h3(1j * y) * 1j).imag, 1.0, math.inf, limit=400)[0])
    corners = dict(f_m=sc_map(m, m), f_1=sc_map(1.0, m), f_inf=far)
    expect = dict(f_m=-2 * K(m), f_1=-2 * K(m) - 2j * K_of_1_minus(m), f_inf=-2j * K_of_1_minus(m))
    out["C3_map_corners"] = {k: dict(numeric=str(corners[k]), expected=str(expect[k])) for k in corners}
    for k in corners:
        assert abs(corners[k] - expect[k]) < 1e-7, (k, corners[k], expect[k])
    # C4: the Moebius map sends x1, x2, x3, x4 to 0, m, 1, infinity and keeps the upper half-plane
    x = (-1.3, -0.2, 0.45, 2.0)
    mm = parameter_from_points(*x)
    T = lambda t: (t - x[0]) * (x[2] - x[3]) / ((t - x[3]) * (x[2] - x[0]))
    assert abs(T(x[0])) < 1e-15 and abs(T(x[1]) - mm) < 1e-14 and abs(T(x[2]) - 1) < 1e-14
    assert abs(T(x[3] - 1e-9)) > 1e8 and T(1j + 0.3).imag > 0
    out["C4_moebius"] = dict(points=x, m=mm)
    # C5: coplanar strips agree with the textbook modulus k0 = s/(s+2w) (Landen transformation)
    rows = []
    for w, s in ((0.5, 0.5), (0.3, 0.3), (0.25, 0.75), (1.0, 0.2)):
        k0 = s / (s + 2 * w)
        textbook = K(1 - k0 ** 2) / (2 * K(k0 ** 2))
        rows.append(dict(w=w, s=s, here=cps(w, s), textbook=textbook))
        assert abs(cps(w, s) - textbook) < 1e-12
    out["C5_cps_textbook"] = rows
    # C6: the body formula; a = 0 must give T/L; the wrap positions reproduce g/L
    L, T = 1.0, 0.35
    assert abs(block_without_film(L, T, L)["value"] - T / L) < 1e-10
    det = block_without_film(L, T, 0.5)
    m_b, s_g = det["m_b"], det["sn"]
    t_d, t_c = m_b * s_g ** 2, 1 / s_g ** 2
    top_mid = quad(lambda t: 1 / math.sqrt((m_b - t) * (1 - t)), 0, t_d, weight="alg", wvar=(-0.5, 0))[0]
    bot_mid = quad(lambda t: 1 / math.sqrt(t * (t - m_b) * (t - 1)), t_c, math.inf)[0]
    assert abs(top_mid - 2 * K(m_b) * 0.5 / L) < 1e-9 and abs(bot_mid - 2 * K(m_b) * 0.5 / L) < 1e-9
    assert abs(K_of_1_minus(m_b) / K(m_b) - 2 * T / L) < 1e-12
    assert abs(F_inc(math.asin(s_g), m_b) - K(m_b) * 0.5 / L) < 1e-12
    out["C6_body"] = dict(m_b=m_b, sn=s_g, t_d=t_d, t_c=t_c, top_mid=top_mid, bottom_mid=bot_mid,
                          target=2 * K(m_b) * 0.5 / L)
    # C7: the plane model tends to the half-plane value; the u-form and the sinh/cosh form agree
    # As h grows, q_odd/2 tends to the half-plane value quickly, while q_even (the share taken by
    # the plane) falls only as 1/ln(h): in two dimensions a plane at any finite distance still
    # takes charge (Section G.10).  Both statements are checked.
    w, s = 0.5, 0.5
    rows = []
    for hh in (1.0, 10.0, 1e3, 1e6):
        bp = board_over_plane(w, s, hh)
        rows.append(dict(h=hh, half_q_odd=bp["q_odd"] / 2, q_even=bp["q_even"], q_even_times_ln_h=bp["q_even"] * math.log(hh) if hh > 1 else None))
    out["C7_plane_far"] = dict(rows=rows, halfplane=cps(w, s))
    assert abs(rows[-1]["half_q_odd"] - cps(w, s)) < 1e-9
    assert abs(rows[-1]["q_even_times_ln_h"] / rows[-2]["q_even_times_ln_h"] - 1) < 0.2
    h = 0.2
    u1, u2 = math.cosh(math.pi * s / (2 * h)), math.cosh(math.pi * (s / 2 + w) / h)
    assert abs((u1 - 1) / (u2 - 1) - board_over_plane(w, s, h)["p_odd"]) < 1e-12
    assert abs((u1 + 1) / (u2 + 1) - board_over_plane(w, s, h)["p_even"]) < 1e-12
    for q, test in ((complex(0.37, 0.0), lambda z: abs(z.imag) < 1e-12 and z.real > 1),
                    (complex(0.37, h), lambda z: abs(z.imag) < 1e-9 and z.real < -1),
                    (complex(0.0, 0.3 * h), lambda z: abs(z.real - math.cos(0.3 * math.pi)) < 1e-12),
                    (complex(0.2, 0.5 * h), lambda z: z.imag > 0)):
        assert test(cmath.cosh(math.pi * q / h)), q
    # C8: the film series: film over the whole electrode span gives b0 = 1/2 exactly, energy pi/8
    full = air_flat_with_film(2.0, 1.0, n_terms=2000)
    assert abs(full["b0"] - 0.5) < 1e-14 and abs(full["value"] - math.pi / 8) < 1e-12
    conv = [air_flat_with_film(0.5, 0.75, n_terms=n)["value"] for n in (1000, 10000, 100000, 400000)]
    u = np.array([0.05, 0.2, 0.4, 0.8, 1.2, 1.5])
    data = np.where(np.abs(0.75 * np.sin(u)) < 0.25, 0.75 * np.sin(u) / 0.5, 0.5 * np.sign(u))
    recon = film_series_boundary(0.5, 0.75, u)
    assert np.max(np.abs(recon - data)) < 1e-4
    out["C8_film_series"] = dict(full_film=full["value"], pi_over_8=math.pi / 8, convergence=conv,
                                 boundary_data=data.tolist(), reconstructed=recon.tolist())
    # C9: uniform film coupled to ground: -C_g/6 against the exact RC line, -Y12 R = theta/sinh(theta)
    Rv, Cg, f = 2000.0, 100e-15, 1e6
    th = cmath.sqrt(1j * 2 * math.pi * f * Rv * Cg)
    y = (th / cmath.sinh(th)) / Rv
    c_eff = y.imag / (2 * math.pi * f)
    out["C9_rc_line"] = dict(c_eff_fF=c_eff * 1e15, minus_Cg_over_6_fF=-Cg / 6 * 1e15)
    assert abs(c_eff * 1e15 + Cg / 6 * 1e15) < 1e-3
    # C11: a guard of vanishing width leaves the pads alone, so the quarter-plane result must
    # reproduce the half-plane value; a real guard must lower the mutual capacitance (Rule 6)
    for w, s in ((0.5, 0.5), (0.3, 0.3), (1.0, 0.8)):
        assert abs(guard_in_gap(w, s, 0.0)["mutual"] - cps(w, s)) < 1e-12
    assert guard_in_gap(0.5, 0.5, 0.3)["mutual"] < cps(0.5, 0.5)
    assert abs(film_weight(1.0) - 1.0 / 6.0) < 1e-15
    out["C11_guard"] = dict(wg_0=guard_in_gap(0.5, 0.5, 0.0)["mutual"], wg_0p3=guard_in_gap(0.5, 0.5, 0.3))
    # C10: the cut layer tends to the half-plane value for a thick layer
    assert abs(cps_layer_cut(0.5, 0.5, 1e4) - cps(0.5, 0.5)) < 1e-6
    out["C10_layer"] = dict(d_1p6=cps_layer_cut(0.5, 0.5, 1.6), halfplane=cps(0.5, 0.5))
    return out


# =====================================================================================
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", default=None, help="write all results to this file")
    args = ap.parse_args()
    conf = confirmations()
    print("numerical confirmations passed:", ", ".join(conf))
    res = dict(confirmations=conf, sizes={}, pins=dsg_pins())
    for size in CHIPS:
        res["sizes"][size] = {}
        for film in ("up", "down"):
            for dims in ("nominal", "extremes"):
                r = resistor_on_pads(size, film, dims)
                res["sizes"][size][f"{film}_{dims}"] = r
                print(f"{size} film {film:4s} {dims:8s}: board {r['board'][0]:.1f}-{r['board'][1]:.1f}, "
                      f"block {r['block'][0]:.1f}-{r['block'][1]:.1f}, air {r['air'][0]:.1f}-{r['air'][1]:.1f} fF; "
                      f"lower bound {r['lower_bound_2d']:.1f}, central {r['central']:.1f}, "
                      f"upper estimate {r['upper_estimate']:.1f} fF")
    res["pads_0402_variants"] = {}
    for name, pv in PADS_0402_VARIANTS.items():
        r = resistor_on_pads("0402", "up", "nominal", pv)
        res["pads_0402_variants"][name] = r
        print(f"0402 on {name} pads: board {r['board'][0]:.1f}-{r['board'][1]:.1f}, lower bound "
              f"{r['lower_bound_2d']:.1f}, central {r['central']:.1f}, upper estimate {r['upper_estimate']:.1f} fF")
    res["body_alone"] = {}
    for size in CHIPS:
        for dims in ("nominal", "extremes"):
            b = body_alone(size, dims)
            res["body_alone"][f"{size}_{dims}"] = b
            print(f"{size} body alone {dims:8s}: block {b['block'][0]:.1f}-{b['block'][1]:.1f}, over ground "
                  f"{b['over_ground'][0]:.1f}-{b['over_ground'][1]:.1f}, free-standing "
                  f"{b['free_standing'][0]:.1f}-{b['free_standing'][1]:.1f} fF")
    cut = cut_per_mm(0.2, 0.02, EPS_AL[1])
    res["cut_example"] = dict(per_mm=cut, w_side=0.2, delta=0.02, eps_al=EPS_AL[1])
    print(f"cut 20 um between 0.2-mm film regions on alumina: {cut:.1f} fF/mm")
    res["guard_examples"] = {}
    for film in ("up", "down"):
        ge = guard_example("0402", 0.2, 0.03, film)
        res["guard_examples"][f"0402_wg0.2_ts0.03_film_{film}"] = ge
        print(f"0402, guard 0.2 mm, standoff 30 um, film {film}: board {ge['board_without']:.1f} -> "
              f"{ge['board_with_guard']:.1f} fF, Cg {ge['Cg']:.1f} fF, film term {ge['film_term']:.1f} fF, "
              f"pad to guard {ge['pad_to_guard']:.1f} fF, added at the input node {ge['input_node_added']:.1f} fF")
    p = res["pins"]
    print("DSG pins 1-3: without middle pin {:.1f}-{:.1f} fF, floating wall {:.1f}-{:.1f} fF, wall-metal term {:.1f}-{:.1f} fF"
          .format(*p["without_middle"], *p["floating_wall"], *p["wall_metal_term"]))
    for h in (0.1, 0.2, 0.36):
        bp = board_over_plane(PADS["0402"]["w"], PADS["0402"]["s"], h)
        print(f"0402 pads over a plane at {h} mm: mutual {bp['mutual']:.3f}, to ground {bp['to_ground']:.3f} "
              f"(per unit eps_r eps0 and per mm of pad width); bare half-plane {cps(PADS["0402"]["w"], PADS["0402"]["s"]):.3f}")
    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(json.dumps(res, indent=1, default=float), encoding="utf-8", newline="\n")
        print("written", args.json)


if __name__ == "__main__":
    main()
