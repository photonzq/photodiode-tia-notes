"""Section 4.11 of the note: a measured OPA846 board at R_F = 1.5 kOhm (0603 resistor, no fitted feedback capacitor)
against Sections 4.10 and 3.10, through the shape of its shot-noise-calibrated gain and through its noise; where its
excess noise can come from; and how much feedback capacitance a second board needs.

Usage:
    python compare_opa846_1k5_board.py [--data CSV] [--aol AOL_TXT] [--figure [OUT_STEM]]
                                       [--figure-noise [OUT_STEM]] [--figure-second [OUT_STEM]]

--data    the board's per-1-MHz table, by default ../data/measurements/opa846_1k5_board_per_MHz.csv.  In every
          1 MHz bin the measurement's own analysis fitted the output noise against the total photocurrent,
          S(I) = S0 + 2 q G^2 I, over 20 records from 1.94 uA to 4.90 mA and one without light; the slope gives the
          gain G (photocurrent to the voltage at the scope input) and the floor the input-referred noise, with the
          scope's own noise (a record with the TIA off, on the same +/-50 mV range as the record without light)
          subtracted.  Bins with tones or too little shot noise are flagged there and left out here.
--aol     the macromodel's inverting-input open-loop run of spice_tia_checks.py aol
          (../spice/runs/aol/OPA846_inverting/aol.txt, kept locally; spice/results/aol.json holds its summary).
--figure  draws Figure 10 (../figures/fig37c_opa846_1k5_board.png and .pdf, or OUT_STEM).
--figure-noise   draws Figure 11, where the excess noise can arise (../figures/fig37d_opa846_1k5_noise).
--figure-second  draws Figure 12, the second board (../figures/fig37e_opa846_1k5_second_board).
No simulation is run.  Every number of Sections 4.11.2-4.11.7 and of Tables 4.4-4.7 is printed; the pulse
responses of Section 4.11.8 come from tia_pulse_response.py --note.

What is fitted (equation numbers of the note)
---------------------------------------------
The measured gain is the TIA's transimpedance times the chain behind it:
    G(f) = K |Z_T(f; C_T, C_F)| |H_chain(f)|.
Z_T is Eqs. (8)-(10): Z_F = R_F/(1 + j w R_F C_F), NG = 1 + j w C_T Z_F, T = A/NG, Z_T = -Z_F T/(1 + T), with
R_F = 1500 ohm.  A(f) is either the datasheet open-loop curve (our analytical model, Section 3.5) or the
macromodel's own gain from the inverting input, A_- = -v(out)/v(inm); C_T is the total capacitance from the summing
node to AC ground, the amplifier's own 3.8 pF (datasheet) or 3.07 pF (macromodel) included.

The chain, Eq. (36i): the TIA drives a cable through R_S = 50 ohm into the scope's 1 Mohm || C_in, C_in = 14 pF.
With the source matched to the cable (R_S = Z_0) nothing returns from the source end, and the voltage at the open
far end is V_out exp(-j beta l)/(1 + j w R_S C_in), whatever the cable length, so
    |H_chain| = |H_scope| / sqrt(1 + (2 pi f R_S C_in)^2),
a pole at 1/(2 pi R_S C_in) = 227 MHz.  The scope's front end H_scope (-3 dB at 200 MHz, flat to +0.3/-3 dB up to it)
is taken as flat, as a second-order Butterworth or as a single pole at 200 MHz; the case without any chain shows what
ignoring it does.

The search, Eqs. (36j) and (36k): for each (C_T, C_F) the model shape M_k = |Z_T(f_k)| |H_chain(f_k)| at the bin
centres f_k is compared with G_k by the rms relative residual
    eps = sqrt( (1/N) sum_k (1 - K M_k/G_k)^2 ),
with every bin weighted alike (the statistical 1-sigma of G_k, 0.28 % typically, is far below the model's own error),
and the scale that minimises it follows in closed form,
    K = sum_k (M_k/G_k) / sum_k (M_k/G_k)^2.
A coarse grid (C_T 2-16 pF in 0.25 pF, C_F 0.02-1.2 pF in 0.02 pF) is refined around its best point (0.025 pF and
0.002 pF).  |Z_F T/(1 + T)| is finite and resonant also for an unstable loop, so the candidates are ranked by eps and
the first whose loop passes tia_model.loop_metrics (one crossing, 180 deg + angle T(f_c) > 0, no second crossing above
1.2 f_c) is the fit; the unconstrained minimum is printed beside it.  How tightly a fit is fixed is shown by every
stable loop within 1.2 eps of the best.

The noise: Eq. (19), i^2 = 4kT/R_F + i_n^2 + e_n^2 [1/R_F^2 + (w C_tot)^2], with T = 295 K and the datasheet's
e_n = 1.2 nV/rtHz and i_n = 2.8 pA/rtHz, against the measured input-referred noise from 25 MHz up; the excess is also
fitted as a white term at the TIA input or at the scope input (divided by G(f) there).

Where the excess arises (Section 4.11.6, Eqs. (36l)-(36o), Table 4.5).  A source reaches the scope through its own
transfer function, so each location leaves its own shape in the TIA's output noise X = S0 - S_scope (V^2/Hz):
    a white current w at the summing node      X_x = w^2 G^2
    a white voltage u at the scope's input     X_x = u^2               (input-referred u/G)
    a voltage e_x in series with the + input   X_x = e_x^2 G^2 |1/R_F + j w C_tot|^2   (grows with f, like e_n)
The excess is printed band by band, at the scope and input-referred, with C_tot of each gain fit; its shape over
25-100 MHz, where it does not depend on e_n C_tot, is compared with the two white hypotheses; each hypothesis's
fit is turned into what it requires of the board (the resistor or the DC current at the node, the amplifier's i_n,
the e_n C_tot product); and the gain is refitted with a resistor R_x from the summing node to ground, which enters
the loop as NG = 1 + Z_F (1/R_x + j w C_T), to see whether the measured gain can tell it.

The second board (Section 4.11.7, Tables 4.6 and 4.7): for every stable fit, the feedback capacitance to add for
0.01, 0.1, 1 and 3 dB of transimpedance peaking (bisection on tia_model.loop_metrics), the edge of the
minimum-gain rule C_F <= C_T/(G_min - 1) with G_min = 7, and for the two input-pole fits the loop, the response
at the TIA and at the scope, the noise at 100 MHz (Eq. (19) with the added C_F in C_tot) and the rms noise of
Eq. (19) at the TIA output over 1-200 and 1-1000 MHz, for added capacitances from 0 to 0.65 pF.

The distortion thresholds of the board: Eq. (36h) with H_e = A/(1 + A/NG) of each fit.
"""
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

import numpy as np

import case_studies as cs
import tia_model as tm

HERE = Path(__file__).resolve().parent
PART = "OPA846"
R_F = 1500.0
R_SERIES = 50.0                 # ohm, series output resistor (matched to the cable)
C_SCOPE = 14e-12                # F, scope input capacitance (1 Mohm +/-1 % || 14 pF +/-1 pF, PicoScope 3000D series)
F_SCOPE = 200e6                 # Hz, scope bandwidth (-3 dB)
C_IN_MACRO = 3.07e-12           # F, the macromodel's input capacitance (spice/results/params.json)
T_K, K_B, Q_E = 295.0, 1.380649e-23, 1.602176634e-19
E_N, I_N = 1.2e-9, 2.8e-12      # datasheet typical values (Table A6.1)
I_N_MAX = 3.5e-12               # datasheet maximum at 25 C (OPA846 p. 3)
I_B_MAX = 19e-6                 # input bias current, maximum at 25 C (OPA846 p. 3)
SR, GBW = 625e6, 1750e6         # V/s, Hz (OPA846 p. 3)
G_MIN = 7.0                     # minimum stable gain (OPA846 p. 1)
NOTE_CT, NOTE_CF = 5.15e-12, (0.05e-12, 0.08e-12, 0.12e-12)
CHAINS = {"none": "no chain", "rc": "50 ohm into 14 pF", "rc2": "and a 2nd-order 200 MHz front end",
          "rc1": "and a 1st-order 200 MHz front end"}
BANDS = ((25e6, 50e6), (50e6, 75e6), (75e6, 100e6), (100e6, 125e6), (125e6, 150e6), (150e6, 175e6), (175e6, 200e6))
ADDED = (0.0, 0.30e-12, 0.41e-12, 0.45e-12, 0.50e-12, 0.55e-12, 0.60e-12, 0.65e-12)


def sgnsqrt(x):
    return math.copysign(math.sqrt(abs(x)), x)


def read_bins(path):
    rows = [r for r in csv.reader(line for line in open(path, encoding="utf-8") if not line.startswith("#"))]
    head, data = rows[0], rows[1:]
    ix = {k: i for i, k in enumerate(head)}

    def col(name):
        return np.array([float(r[ix[name]]) if r[ix[name]] not in ("", "nan") else np.nan for r in data])

    f = 0.5 * (col("f_low_MHz") + col("f_high_MHz")) * 1e6
    return dict(f=f, G=col("G_V_per_A"), sG=col("G_sigma_V_per_A"), i=col("i_TIA_A_per_rtHz"),
                si=col("i_TIA_sigma_A_per_rtHz"), bad=col("flagged") > 0, s0=col("S0_V2_per_Hz"),
                ss0=col("S0_sigma_V2_per_Hz"), ssc=col("S_scope_V2_per_Hz"), sssc=col("S_scope_sigma_V2_per_Hz"))


def macro_open_loop(path):
    d = np.loadtxt(path, skiprows=1)
    f = d[:, 0]
    a = -(d[:, 1] + 1j * d[:, 2]) / (d[:, 3] + 1j * d[:, 4])          # A_- = -v(out)/v(inm)
    ph = np.degrees(np.unwrap(np.angle(a)))
    ph -= 360.0 * np.round((ph[np.argmin(abs(f - 10e6))] + 90.0) / 360.0)   # about -90 deg at 10 MHz
    return tm.InterpOpenLoop.from_points([(fi, 20 * math.log10(abs(ai)), pi) for fi, ai, pi in zip(f, a, ph)],
                                         note="macromodel, inverting input")


def chain(f, kind):
    """|H_chain|, Eq. (36i): the 50-ohm source into C_SCOPE, and the scope's front end."""
    f = np.asarray(f, dtype=float)
    if kind == "none":
        return np.ones_like(f)
    h = 1.0 / np.sqrt(1.0 + (2 * math.pi * f * R_SERIES * C_SCOPE) ** 2)
    if kind == "rc1":
        h = h / np.sqrt(1.0 + (f / F_SCOPE) ** 2)
    elif kind == "rc2":
        h = h / np.sqrt(1.0 + (f / F_SCOPE) ** 4)
    return h


def residual(f, g, ol, h, ct, cf):
    """Eqs. (36j) and (36k): the rms relative residual and the scale K."""
    z = np.abs(tm.tia_tf(f, ol, R_F, ct, cf)[0]) * h
    u = z / g
    k = np.sum(u) / np.sum(u * u)
    return float(np.sqrt(np.mean((1.0 - k * u) ** 2))), float(k)


def is_stable(ol, ct, cf):
    m = tm.loop_metrics(ol, R_F, ct, cf)
    return bool(m["stable"]) and np.isfinite(m["pm_deg"]) and m["pm_deg"] > 0, m


def grid_best(f, g, ol, h, ct_grid, cf_grid, stable_only):
    cand = sorted((*residual(f, g, ol, h, ct, cf), ct, cf) for ct in ct_grid for cf in cf_grid)
    if not stable_only:
        return cand[0]
    for c in cand:
        if is_stable(ol, c[2], c[3])[0]:
            return c
    return None


def fit(f, g, ol, h, stable_only):
    eps, k, ct, cf = grid_best(f, g, ol, h, np.arange(2e-12, 16.01e-12, 0.25e-12), np.arange(0.02e-12, 1.201e-12, 0.02e-12),
                               stable_only)
    eps, k, ct, cf = grid_best(f, g, ol, h, np.arange(max(ct - 0.5e-12, 1e-12), ct + 0.501e-12, 0.025e-12),
                               np.arange(max(cf - 0.04e-12, 0.002e-12), cf + 0.0401e-12, 0.002e-12), stable_only)
    ok, m = is_stable(ol, ct, cf)
    fpk, pk = tia_peak(ol, ct, cf)
    return dict(eps=eps, k=k, ct=ct, cf=cf, stable=ok, m=m, fpk=fpk, pk=pk)


def tia_peak(ol, ct, cf):
    ff = np.logspace(6, 9.5, 4000)
    z = np.abs(tm.tia_tf(ff, ol, R_F, ct, cf)[0])
    k = int(np.argmax(z))
    return float(ff[k]), 20 * math.log10(z[k] / R_F)


def stability_boundary(ol, ct):
    """The C_F at which the loop of node C_T reaches zero phase margin (bisection; stable above it)."""
    lo, hi = 0.002e-12, 1.5e-12
    if is_stable(ol, ct, lo)[0]:
        return lo
    for _ in range(24):
        mid = 0.5 * (lo + hi)
        lo, hi = (lo, mid) if is_stable(ol, ct, mid)[0] else (mid, hi)
    return hi


def he(ol, f, ct, cf):
    A = ol.A(np.atleast_1d(f))
    NG = tm.tia_tf(np.atleast_1d(f), ol, R_F, ct, cf)[1]
    return float(np.abs(A / (1 + A / NG))[0])


# ---------------------------------------------------------------------------------------------------------------
# Section 4.11.6: where the excess noise arises
# ---------------------------------------------------------------------------------------------------------------
def zt_rx(f, ol, ct, cf, rx):
    """Z_T and T with a resistor R_x from the summing node to ground: NG = 1 + Z_F (1/R_x + j w C_T)."""
    # Eqs. (8)-(10) with the node admittance j w C_T extended by 1/R_x: the noise gain becomes 1 + Z_F Y_node with
    # Y_node = 1/R_x + j w C_T, while the signal path, Z_T = -Z_F T/(1 + T), keeps its form.
    s = 2j * np.pi * np.asarray(f, dtype=float)
    zf = R_F / (1 + s * R_F * cf)
    ng = 1 + zf * (s * ct + 1.0 / rx)
    t = ol.A(f) / ng
    return -zf * t / (1 + t), t


def stable_rx(ol, ct, cf, rx):
    # the stability test of Section 3.5 (first crossing of |T| = 1 with positive phase margin, no second crossing
    # above 1.2 f_c) for the loop with R_x; returns (stable, phase margin in degrees)
    ff = tm.F_GRID
    t = zt_rx(ff, ol, ct, cf, rx)[1]
    mag, ph = np.abs(t), np.degrees(np.unwrap(np.angle(t)))
    idx = np.where((mag[:-1] >= 1) & (mag[1:] < 1))[0]
    if not len(idx):
        return False, float("nan")
    i = idx[0]
    pm = 180 + ph[i]
    return bool(pm > 0 and not np.any(mag[ff > 1.2 * ff[i]] >= 1)), float(pm)


def fit_rx(f, g, ol, h, rx):
    """The gain fit of Eqs. (36j)-(36k) with R_x at the summing node (grid 0.05 pF by 0.005 pF, stable loops only)."""
    cand = []
    for ct in np.arange(4.0e-12, 8.001e-12, 0.05e-12):
        for cf in np.arange(0.05e-12, 0.6001e-12, 0.005e-12):
            z = np.abs(zt_rx(f, ol, ct, cf, rx)[0]) * h           # model shape M_k = |Z_T| |H_chain|
            u = z / g                                            # M_k / G_k
            k = np.sum(u) / np.sum(u * u)                        # Eq. (36k)
            cand.append((float(np.sqrt(np.mean((1.0 - k * u) ** 2))), float(k), ct, cf))   # Eq. (36j)
    for eps, k, ct, cf in sorted(cand):                          # best residual first; the first stable loop wins
        ok, pm = stable_rx(ol, ct, cf, rx)
        if ok:
            return dict(eps=eps, k=k, ct=ct, cf=cf, pm=pm)
    return None


def noise_section(b, fits, models, f_gain, g_gain):
    """Prints the numbers of Section 4.11.6 and Table 4.5; returns what Figure 11 draws."""
    use = (~b["bad"]) & np.isfinite(b["i"]) & (b["f"] >= 25e6)
    f, g = b["f"][use], b["G"][use]
    # X of Eq. (36l): the floor without light minus the oscilloscope's own record (both on the +/-50 mV range)
    x = (b["s0"] - b["ssc"])[use]                                       # the TIA's output noise at the scope, V^2/Hz
    # Eq. (19) split into its white part a0 and its capacitive part e_n^2 w^2 C_tot^2 = wn C_tot^2
    a0 = 4 * K_B * T_K / R_F + I_N ** 2 + E_N ** 2 / R_F ** 2
    wn = (E_N * 2 * math.pi * f) ** 2
    ctots = {name: fits[(name, "rc", True)]["ct"] + fits[(name, "rc", True)]["cf"] for name in models}
    print("\nSection 4.11.6: the excess band by band (TIA's output noise at the scope minus Eq. (19) through G)")
    bands = {}
    for name, c in ctots.items():
        ex = x - g ** 2 * (a0 + wn * c ** 2)                    # X_x = X - G^2 [Eq. (19)], at the oscilloscope
        rows = []
        for lo, hi in BANDS:
            m = (f >= lo) & (f < hi)
            # band averages in power; the input-referred excess divides by the band's rms gain
            e, gi, xx = float(np.mean(ex[m])), math.sqrt(float(np.mean(g[m] ** 2))), float(np.mean(x[m]))
            mod = float(np.mean(g[m] ** 2 * (a0 + wn[m] * c ** 2)))
            rows.append(dict(lo=lo, hi=hi, ex=e, g=gi, x=xx, model=mod))
            print(f"  {name:10s} C_tot {c * 1e12:.2f} pF, {lo / 1e6:3.0f}-{hi / 1e6:3.0f} MHz: TIA noise {math.sqrt(xx) * 1e9:5.2f}, "
                  f"Eq. (19) {math.sqrt(mod) * 1e9:5.2f}, excess {sgnsqrt(e) * 1e9:+6.2f} nV/rtHz at the scope; "
                  f"input-referred {sgnsqrt(e) / gi * 1e12:+5.2f} pA/rtHz (G {gi:.0f} V/A)")
        bands[name] = rows
    # The shape test of Eq. (36m) in the band where the excess does not depend on e_n C_tot: from 25-50 to 75-100 MHz
    # a white current at the node scales with G (so the amplitude ratio is G's ratio), a white voltage at the
    # oscilloscope does not (ratio 1).
    r0 = bands["datasheet"]
    print(f"  the shape over 25-100 MHz (datasheet C_tot): the excess at the scope grows {sgnsqrt(r0[2]['ex']) / sgnsqrt(r0[0]['ex']):.2f} times "
          f"from 25-50 to 75-100 MHz while G grows {r0[2]['g'] / r0[0]['g']:.2f} times; a white source at the input predicts "
          f"{r0[2]['g'] / r0[0]['g']:.2f}, one at the scope 1.00")
    # a 10 % error in e_n C_tot, at each band
    c = ctots["datasheet"]
    for lo, hi in ((25e6, 50e6), (75e6, 100e6), (150e6, 175e6)):
        m = (f >= lo) & (f < hi)
        # (1.1 e_n C)^2 - (e_n C)^2 = 0.21 (e_n C)^2 of extra power in the capacitive term, through G^2
        d = float(np.mean(g[m] ** 2 * wn[m] * c ** 2)) * (1.1 ** 2 - 1)
        print(f"  {lo / 1e6:.0f}-{hi / 1e6:.0f} MHz: +10 % in e_n C_tot adds {math.sqrt(d) * 1e9:.2f} nV/rtHz in quadrature to Eq. (19) "
              f"against an excess of {sgnsqrt(np.mean((x - g ** 2 * (a0 + wn * c ** 2))[m])) * 1e9:.2f} nV/rtHz")
    # the two white hypotheses with the capacitance free (the fit of Figure 10d), and what each needs
    # Input-referred, i^2 = a0 + C_tot^2 wn + (w^2 for a white current at the node, or u^2/G^2 for a white voltage
    # at the oscilloscope): linear in the two unknowns (amplitude^2, C_tot^2), solved by weighted least squares with
    # the 1-sigma of i^2 from the measurement's analysis.
    i2 = b["i"][use] ** 2
    si = 2 * b["i"][use] * b["si"][use]
    fits_n = {}
    for label, colv in (("input", np.ones_like(wn)), ("scope", 1.0 / g ** 2)):
        d2 = np.column_stack([colv, wn])
        q, *_ = np.linalg.lstsq(d2 / si[:, None], (i2 - a0) / si, rcond=None)
        rr = (i2 - a0 - d2 @ q) / i2
        amp, cc = math.sqrt(max(q[0], 0.0)), math.sqrt(max(q[1], 0.0))
        fits_n[label] = dict(amp=amp, ctot=cc, rms=float(np.sqrt(np.mean(rr * rr))))
        # only e_n C_tot is fixed by the noise; the e_n each needs on the node the gain fixes is e_n cc / C_tot(gain)
        need = ", ".join(f"e_n {E_N * cc / ct_ * 1e9:.2f} nV/rtHz at the {n} fit's {ct_ * 1e12:.2f} pF" for n, ct_ in ctots.items())
        unit = f"{amp * 1e12:.2f} pA/rtHz" if label == "input" else f"{amp * 1e9:.2f} nV/rtHz"
        print(f"  white at the {label}: {unit}, C_tot {cc * 1e12:.2f} pF (e_n C_tot {E_N * cc * 1e21:.2f} nV pF/rtHz; {need}), "
              f"rms relative residual {100 * fits_n[label]['rms']:.1f} %")
    w = fits_n["input"]["amp"]
    # what a white current at the node requires
    r_th = 4 * K_B * T_K / w ** 2                         # thermal noise alone: 4kT/R = w^2
    # Eq. (36n): with the resistor's own e_n/R_x, 4kT x + e_n^2 (2x/R_F + x^2) = w^2 for x = 1/R_x, a quadratic in x
    aq, bq, cq = E_N ** 2, 4 * K_B * T_K + 2 * E_N ** 2 / R_F, -w ** 2      # e_n^2 x^2 + (4kT + 2 e_n^2/R_F) x - w^2 = 0, x = 1/R_x
    r_x = 1.0 / ((-bq + math.sqrt(bq * bq - 4 * aq * cq)) / (2 * aq))     # the positive root
    i_x = w ** 2 / (2 * Q_E)                              # shot noise 2 q I = w^2
    i_n_need = math.hypot(I_N, w)                         # the amplifier's i_n that would carry the excess too
    print(f"  a white current of {w * 1e12:.2f} pA/rtHz at the node is the thermal noise of {r_th:.0f} ohm, or of {r_x:.0f} ohm with "
          f"the e_n/R_x it adds; the shot noise of {i_x * 1e6:.0f} uA; or an amplifier i_n of {i_n_need * 1e12:.2f} pA/rtHz "
          f"against {I_N * 1e12:.1f} typical and {I_N_MAX * 1e12:.1f} maximum")
    # can the gain see such a resistor?  Refit the gain with R_x in the loop
    rx_fits = {}
    for name, (ol, _) in models.items():
        h = chain(f_gain, "rc")
        r = fit_rx(f_gain, g_gain, ol, h, r_x)
        rx_fits[name] = r
        print(f"  gain fit with R_x = {r_x:.0f} ohm at the node ({name}): C_T {r['ct'] * 1e12:.2f} pF, C_F {r['cf'] * 1e12:.3f} pF, "
              f"K {r['k']:.3f}, eps {100 * r['eps']:.2f} % (without R_x {100 * fits[(name, 'rc', True)]['eps']:.2f} %), PM {r['pm']:.1f} deg, "
              f"C_tot {(r['ct'] + r['cf']) * 1e12:.2f} pF, which with the noise fit's e_n C_tot needs e_n "
              f"{E_N * fits_n['input']['ctot'] / (r['ct'] + r['cf']) * 1e9:.2f} nV/rtHz")
    # a voltage at the + input: the third line of Eq. (36m); its size from the 25-50 MHz excess, then extrapolated
    m1 = (f >= 25e6) & (f < 50e6)
    f1 = float(np.mean(f[m1]))
    ex1 = float(np.mean((x - g ** 2 * (a0 + wn * c ** 2))[m1])) / float(np.mean(g[m1] ** 2))
    e_x = math.sqrt(ex1) / abs(1 / R_F + 2j * math.pi * f1 * c)
    for ft in (100e6, 162.5e6):
        print(f"  a voltage at the + input giving the 25-50 MHz excess: e_x = {e_x * 1e9:.2f} nV/rtHz; at {ft / 1e6:.1f} MHz it would add "
              f"{e_x * abs(1 / R_F + 2j * math.pi * ft * c) * 1e12:.2f} pA/rtHz input-referred")
    # aliasing: at 1 GS/s the bins of 25-100 MHz have images at 900-975 MHz
    r = fits[("datasheet", "rc", True)]
    fa = np.array([900e6, 975e6])
    ia = np.sqrt(a0 + (E_N * 2 * math.pi * fa * c) ** 2)          # Eq. (19) there, input-referred
    va = np.abs(tm.tia_tf(fa, r["ol"], R_F, r["ct"], r["cf"])[0]) * ia   # at the TIA's output
    print(f"  aliasing at 1 GS/s: Eq. (19) at the TIA output is {va[0] * 1e9:.2f} and {va[1] * 1e9:.2f} nV/rtHz at 900 and 975 MHz, "
          f"{va[0] * chain(fa, 'rc')[0] * 1e9:.2f} and {va[1] * chain(fa, 'rc')[1] * 1e9:.2f} nV/rtHz behind the 227-MHz pole, before "
          f"the oscilloscope's own 200-MHz front end")
    # the low-frequency excess
    lf = (~b["bad"]) & np.isfinite(b["i"]) & (b["f"] >= 10e6) & (b["f"] < 25e6)
    print("  below 25 MHz: " + "; ".join(
        f"{fi / 1e6:.1f} MHz {ii * 1e12:.1f} pA/rtHz (floor {math.sqrt(s0) * 1e9:.1f}, scope {math.sqrt(ss) * 1e9:.1f} nV/rtHz)"
        for fi, ii, s0, ss in zip(b["f"][lf], b["i"][lf], b["s0"][lf], b["ssc"][lf])))
    return dict(f=f, g=g, x=x, a0=a0, ctots=ctots, fits=fits_n, bands=bands, r_x=r_x, rx_fits=rx_fits, s0=b["s0"][use],
                ssc=b["ssc"][use], lf=dict(f=b["f"][lf], i=b["i"][lf]))


# ---------------------------------------------------------------------------------------------------------------
# Section 4.11.7: the second board
# ---------------------------------------------------------------------------------------------------------------
def cf_for_peaking(ol, ct, target_db, nt=None):
    """The smallest total C_F with at most target_db of transimpedance peaking (bisection)."""
    # peaking falls monotonically as C_F grows on these nodes, so 40 halvings of [0.05, 3] pF fix it to < 1e-23 F
    lo, hi = 0.05e-12, 3e-12
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        lo, hi = (lo, mid) if tm.loop_metrics(ol, R_F, ct, mid)["peaking_dB"] <= target_db else (mid, hi)
    return hi


def response_at_scope(ol, ct, cf, kind, f=np.linspace(1e6, 1.5e9, 6000)):
    # |Z_T|/R_F times the chain of Eq. (36i): its peaking relative to the low-frequency value, and its -3-dB point
    z = np.abs(tm.tia_tf(f, ol, R_F, ct, cf)[0]) / R_F * chain(f, kind)
    k = int(np.argmax(z))
    below = np.where(z < z[0] / math.sqrt(2))[0]
    return 20 * math.log10(z[k] / z[0]), float(f[below[0]]) if len(below) else float("nan")


def rms_noise(ol, ct, cf, f_hi):
    """rms of Eq. (19) at the TIA output from 1 MHz to f_hi (V), with C_tot = C_T + C_F."""
    # v_rms^2 = integral |Z_T(f)|^2 i^2(f) df: the input-referred density of Eq. (19) through the transimpedance
    f = np.linspace(1e6, f_hi, 20000)
    i2 = 4 * K_B * T_K / R_F + I_N ** 2 + E_N ** 2 * (1 / R_F ** 2 + (2 * math.pi * f * (ct + cf)) ** 2)
    z2 = np.abs(tm.tia_tf(f, ol, R_F, ct, cf)[0]) ** 2
    return math.sqrt(float(np.trapezoid(z2 * i2, f)))


def second_board_section(fits, models, rx_fits, r_x):
    print("\nSection 4.11.7: the second board; feedback capacitance to add, by fit")
    incs = {}
    for name in models:
        for kind in ("rc", "rc2", "rc1", "none"):
            # each stable fit of Table 4.4 is a complete loop; the increment is the target C_F minus the fit's own
            r = fits[(name, kind, True)]
            ol, ct, cfp = r["ol"], r["ct"], r["cf"]
            row = {}
            for target in (0.01, 0.1, 1.0, 3.0):
                c = cf_for_peaking(ol, ct, target)
                m = tm.loop_metrics(ol, R_F, ct, c)
                row[target] = dict(add=c - cfp, total=c, pm=m["pm_deg"], gm=m["gm_dB"], f3=m["f_3dB"])
            # the minimum-gain rule of Section 6.2.4: 1 + C_T/C_F >= G_min, i.e. C_F <= C_T/(G_min - 1)
            edge = ct / (G_MIN - 1)
            row["edge"] = dict(add=edge - cfp, total=edge)
            incs[(name, kind)] = row
            print(f"  {name:10s} {kind:4s} (C_T {ct * 1e12:.2f}, C_F {cfp * 1e12:.3f} pF): " + "; ".join(
                f"{t} dB +{row[t]['add'] * 1e12:.3f} pF (total {row[t]['total'] * 1e12:.3f}, PM {row[t]['pm']:.1f} deg, "
                f"GM {row[t]['gm']:.1f} dB, f3 {row[t]['f3'] / 1e6:.0f} MHz)" for t in (0.01, 0.1, 1.0, 3.0))
                + f"; G_min edge total {edge * 1e12:.3f} pF (+{(edge - cfp) * 1e12:.3f})")
    print("  peaking with a given capacitance added, every fit with the chain: " + "; ".join(
        f"{name} {kind}: " + ", ".join(
            f"+{add * 1e12:.2f} pF {tm.loop_metrics(fits[(name, kind, True)]['ol'], R_F, fits[(name, kind, True)]['ct'], fits[(name, kind, True)]['cf'] + add)['peaking_dB']:.2f} dB"
            for add in (0.45e-12, 0.50e-12, 0.55e-12, 0.60e-12))
        for name in models for kind in ("rc", "rc2", "rc1")))
    for name, r in rx_fits.items():
        ol = models[name][0]

        # peaking of the loop with R_x, relative to its low-frequency value
        def pk(cf):
            z = np.abs(zt_rx(np.linspace(1e6, 1.5e9, 8000), ol, r["ct"], cf, r_x)[0])
            return 20 * math.log10(z.max() / z[0])
        out = []
        for target in (0.01, 1.0):
            lo, hi = 0.05e-12, 3e-12
            for _ in range(40):
                mid = 0.5 * (lo + hi)
                lo, hi = (lo, mid) if pk(mid) <= target else (mid, hi)
            out.append(f"{target} dB +{(hi - r['cf']) * 1e12:.3f} pF")
        print(f"  {name:10s} with R_x = {r_x:.0f} ohm (C_T {r['ct'] * 1e12:.2f}, C_F {r['cf'] * 1e12:.3f} pF): " + "; ".join(out))
    for name in models:
        # the most phase margin any C_F gives on the fitted node (0.40-2.00 pF in 0.01-pF steps)
        r = fits[(name, "rc", True)]
        best = max((tm.loop_metrics(r["ol"], R_F, r["ct"], c)["pm_deg"], c) for c in np.arange(0.40e-12, 2.001e-12, 0.01e-12))
        print(f"  {name}: the largest phase margin on the fitted node is {best[0]:.1f} deg, at C_F = {best[1] * 1e12:.2f} pF in total")
    print("  detail, the two input-pole fits:")
    detail = {}
    for name in models:
        r = fits[(name, "rc", True)]
        ol, ct, cfp = r["ol"], r["ct"], r["cf"]
        rows = []
        for add in ADDED:
            cf = cfp + add
            m = tm.loop_metrics(ol, R_F, ct, cf)
            pk_s, f3_s = response_at_scope(ol, ct, cf, "rc")
            # Eq. (19) at 100 MHz with the added capacitance in C_tot
            i100 = math.sqrt(4 * K_B * T_K / R_F + I_N ** 2 + E_N ** 2 * (1 / R_F ** 2 + (2 * math.pi * 100e6 * (ct + cf)) ** 2))
            v200, v1000 = rms_noise(ol, ct, cf, 200e6), rms_noise(ol, ct, cf, 1000e6)
            rows.append(dict(add=add, cf=cf, pm=m["pm_deg"], gm=m["gm_dB"], f_c=m["f_c"], ng_hf=1 + ct / cf, pk=m["peaking_dB"],
                             f3=m["f_3dB"], pk_s=pk_s, f3_s=f3_s, i100=i100, v200=v200, v1000=v1000))
            print(f"    {name:10s} +{add * 1e12:.2f} pF (total {cf * 1e12:.3f}): f_c {m['f_c'] / 1e6:.0f} MHz, PM {m['pm_deg']:.1f} deg, "
                  f"GM {m['gm_dB']:.1f} dB, 1 + C_T/C_F {1 + ct / cf:.1f}; TIA peak {m['peaking_dB']:+.2f} dB, f3 {m['f_3dB'] / 1e6:.0f} MHz; "
                  f"at the scope peak {pk_s:+.2f} dB, f3 {f3_s / 1e6:.0f} MHz; Eq. (19) at 100 MHz {i100 * 1e12:.2f} pA/rtHz; "
                  f"rms noise at the TIA output {v200 * 1e6:.1f} uV (1-200 MHz), {v1000 * 1e6:.1f} uV (1-1000 MHz)")
        detail[name] = rows
    return dict(incs=incs, detail=detail)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--data", default=str(HERE.parent / "data" / "measurements" / "opa846_1k5_board_per_MHz.csv"))
    ap.add_argument("--aol", default=str(HERE.parent / "spice" / "runs" / "aol" / "OPA846_inverting" / "aol.txt"))
    ap.add_argument("--figure", nargs="?", const=str(HERE.parent / "figures" / "fig37c_opa846_1k5_board"), default=None)
    ap.add_argument("--figure-noise", nargs="?", const=str(HERE.parent / "figures" / "fig37d_opa846_1k5_noise"), default=None)
    ap.add_argument("--figure-second", nargs="?", const=str(HERE.parent / "figures" / "fig37e_opa846_1k5_second_board"),
                    default=None)
    a = ap.parse_args()
    b = read_bins(a.data)
    use = (~b["bad"]) & np.isfinite(b["G"]) & (b["f"] >= 10e6)
    f, g = b["f"][use], b["G"][use]
    band = (f >= 20e6) & (f < 40e6)
    i20, ipk = int(np.argmin(abs(f - 20.5e6))), int(np.argmax(g))
    print(f"{use.sum()} unflagged bins, {f.min() / 1e6:.1f}-{f.max() / 1e6:.1f} MHz; G over 20-40 MHz (quadrature mean) "
          f"{math.sqrt(np.mean(g[band] ** 2)):.1f} V/A; G {g[i20]:.0f} V/A at {f[i20] / 1e6:.1f} MHz ({g[i20] / R_F:.3f} R_F), "
          f"peak {g[ipk]:.0f} V/A at {f[ipk] / 1e6:.1f} MHz ({g[ipk] / g[i20]:.3f} x, {20 * math.log10(g[ipk] / g[i20]):.2f} dB), "
          f"{g[-1]:.0f} V/A at {f[-1] / 1e6:.1f} MHz")
    for kind, label in CHAINS.items():
        h = chain(np.array([100.5e6, f[ipk]]), kind)
        print(f"  chain {kind} ({label}): {20 * math.log10(h[0]):.2f} dB at 100.5 MHz, {20 * math.log10(h[1]):.2f} dB at the peak; "
              f"TIA peak implied: {g[ipk] / chain(f[ipk], kind) / (g[i20] / chain(f[i20], kind)):.2f} x the 20.5-MHz value")

    an = cs.Analytic(PART)
    models = {"datasheet": (an.ol, an.c_in), "macromodel": (macro_open_loop(a.aol), C_IN_MACRO)}
    fits = {}
    print("Table 4.4 (stable fits) and the unconstrained minima:")
    for name, (ol, c_in) in models.items():
        for kind in CHAINS:
            h = chain(f, kind)
            for stable_only in (True, False):
                r = fit(f, g, ol, h, stable_only)
                r.update(ol=ol, c_in=c_in, kind=kind)
                fits[(name, kind, stable_only)] = r
                m = r["m"]
                print(f"  {name:10s} {kind:4s} {'stable' if stable_only else 'free  '}: C_T {r['ct'] * 1e12:.2f} pF "
                      f"(external {(r['ct'] - c_in) * 1e12:.2f}), C_F {r['cf'] * 1e12:.3f} pF, K {r['k']:.3f}, eps {100 * r['eps']:.2f} %, "
                      f"f_c {m['f_c'] / 1e6:.0f} MHz, PM {m['pm_deg']:.1f} deg, GM {m['gm_dB']:.1f} dB, stable {r['stable']}, "
                      f"TIA peak {r['pk']:+.1f} dB at {r['fpk'] / 1e6:.0f} MHz")
    print("stable loops within 1.2 eps of the best, chain rc:")
    for name, (ol, c_in) in models.items():
        r = fits[(name, "rc", True)]
        h = chain(f, "rc")
        acc = []
        for ct in np.arange(r["ct"] - 1.5e-12, r["ct"] + 1.501e-12, 0.05e-12):
            for cf in np.arange(max(r["cf"] - 0.15e-12, 0.005e-12), r["cf"] + 0.1501e-12, 0.005e-12):
                eps, k = residual(f, g, ol, h, ct, cf)
                if eps <= 1.2 * r["eps"]:
                    ok, m = is_stable(ol, ct, cf)
                    if ok:
                        acc.append((ct, cf, m["pm_deg"], k))
        acc = np.array(acc)
        print(f"  {name}: {len(acc)} loops; C_T {acc[:, 0].min() * 1e12:.2f}-{acc[:, 0].max() * 1e12:.2f} pF, "
              f"C_F {acc[:, 1].min() * 1e12:.3f}-{acc[:, 1].max() * 1e12:.3f} pF, PM {acc[:, 2].min():.1f}-{acc[:, 2].max():.1f} deg, "
              f"K {acc[:, 3].min():.3f}-{acc[:, 3].max():.3f}")
        print(f"    zero phase margin at the fitted C_T ({r['ct'] * 1e12:.2f} pF): C_F = {stability_boundary(ol, r['ct']) * 1e12:.3f} pF")
    print("the note's parasitic alone (C_T 5.15 pF):")
    for name, (ol, c_in) in models.items():
        ct = NOTE_CT if name == "datasheet" else NOTE_CT - an.c_in + C_IN_MACRO
        print(f"  {name}: " + ", ".join(f"{cf * 1e12:.2f} pF -> PM {tm.loop_metrics(ol, R_F, ct, cf)['pm_deg']:.1f} deg"
                                        for cf in NOTE_CF) + f"; zero PM at C_F = {stability_boundary(ol, ct) * 1e12:.3f} pF")

    print("third-harmonic thresholds, Eq. (36h), against the flat design of Section 4.10:")
    cases = [("flat", an.ol, an.C_T(1e-12), 0.70e-12)] + [
        (n, fits[(n, "rc", True)]["ol"], fits[(n, "rc", True)]["ct"], fits[(n, "rc", True)]["cf"]) for n in models]
    for f0 in (20e6, 40e6, 50e6, 60e6, 75e6, 100e6, 150e6):
        parts = []
        for label, ol, ct, cf in cases:
            h3 = he(ol, 3 * f0, ct, cf)
            v_sr = SR / (2 * math.pi * f0)
            parts.append(f"{label}: |H_e(3f)| {h3:.1f}, -60 dBc {v_sr * math.sqrt(12e-3 * GBW / (f0 * h3)):.3f} V, "
                         f"-40 dBc {v_sr * math.sqrt(12e-2 * GBW / (f0 * h3)):.3f} V")
        print(f"  {f0 / 1e6:g} MHz: " + "; ".join(parts))

    usen = (~b["bad"]) & np.isfinite(b["i"]) & (b["f"] >= 25e6)
    fn, i2, si = b["f"][usen], b["i"][usen] ** 2, 2 * b["i"][usen] * b["si"][usen]
    a0 = 4 * K_B * T_K / R_F + I_N ** 2 + E_N ** 2 / R_F ** 2
    x = (E_N * 2 * math.pi * fn) ** 2
    ctot = fits[("datasheet", "rc", True)]["ct"] + fits[("datasheet", "rc", True)]["cf"]
    print(f"noise, Eq. (19): floor {math.sqrt(a0) * 1e12:.2f} pA/rtHz (4kT/R_F {math.sqrt(4 * K_B * T_K / R_F) * 1e12:.2f}, "
          f"i_n {I_N * 1e12:.1f}, e_n/R_F {E_N / R_F * 1e12:.2f}); C_tot of the gain fit {ctot * 1e12:.2f} pF")
    for ft in (25.5e6, 30.5e6, 50.5e6, 75.5e6, 99.5e6, 126.5e6, 150.5e6, 175.5e6, 199.5e6):
        k = int(np.argmin(abs(fn - ft)))
        model = a0 + (E_N * 2 * math.pi * fn[k] * ctot) ** 2
        ex = i2[k] - model
        print(f"  {fn[k] / 1e6:5.1f} MHz: measured {math.sqrt(i2[k]) * 1e12:.2f}, Eq. (19) {math.sqrt(model) * 1e12:.2f} pA/rtHz, "
              f"excess {math.copysign(math.sqrt(abs(ex)), ex) * 1e12:+.2f} pA/rtHz "
              f"({10 * math.log10(i2[k] / model):+.1f} dB)")
    gn = b["G"][usen]
    for label, col in (("white at the TIA input", np.ones_like(x)), ("white at the scope input, / G(f)", 1.0 / gn ** 2)):
        d2 = np.column_stack([col, x])
        q, *_ = np.linalg.lstsq(d2 / si[:, None], (i2 - a0) / si, rcond=None)
        rr = (i2 - a0 - d2 @ q) / i2
        amp = math.sqrt(max(q[0], 0.0))
        unit = f"{amp * 1e12:.2f} pA/rtHz (thermal noise of {4 * K_B * T_K / q[0]:.0f} ohm)" if label.startswith("white at the TIA") \
            else f"{amp * 1e9:.2f} nV/rtHz"
        print(f"  excess {label}: {unit}, C_tot {math.sqrt(max(q[1], 0.0)) * 1e12:.2f} pF, rms relative residual in i^2 "
              f"{100 * float(np.sqrt(np.mean(rr * rr))):.1f} %")
    nz = noise_section(b, fits, models, f, g)
    sb = second_board_section(fits, models, nz["rx_fits"], nz["r_x"])
    if a.figure:
        draw(f, g, fits, models, b, usen, a0, a.figure)
    if a.figure_noise:
        draw_noise(nz, a.figure_noise)
    if a.figure_second:
        draw_second(fits, sb, a.figure_second)


def draw(f, g, fits, models, b, usen, a0, stem):
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
    from make_case_figures import PANEL, panel_label
    from make_figures import COLORS, DASH, LW, configure_plot_style, export

    configure_plot_style()
    blue, red, grey, green = COLORS["primary"], COLORS["warm_accent"], COLORS["neutral"], COLORS["cool_accent"]
    fig, axs = plt.subplots(2, 2, figsize=(2 * PANEL[0], 2 * PANEL[1]), constrained_layout=True)

    # (a) the search: eps over (C_T, C_F) for the datasheet curve and the 50-ohm/14-pF chain, the stability boundary
    ax = axs[0, 0]
    ol = models["datasheet"][0]
    h = chain(f, "rc")
    cts = np.arange(4.0e-12, 9.001e-12, 0.05e-12)
    cfs = np.arange(0.0, 0.8001e-12, 0.005e-12)
    eps = np.array([[residual(f, g, ol, h, ct, cf)[0] for ct in cts] for cf in cfs])
    cs_ = ax.contour(cts * 1e12, cfs * 1e12, 100 * eps, levels=(2.5, 3, 4, 6, 10), colors=COLORS["grey_accent"],
                     linewidths=0.8)
    ax.clabel(cs_, fmt=lambda v: f"{v:g} %", fontsize=7)
    ctb = np.arange(4.0e-12, 9.001e-12, 0.1e-12)
    bnd = np.array([stability_boundary(ol, ct) for ct in ctb])
    ax.fill_between(ctb * 1e12, 0, bnd * 1e12, color=COLORS["highlight"], alpha=0.24, lw=0, zorder=0)
    ax.plot(ctb * 1e12, bnd * 1e12, color=red, lw=LW, label="zero phase margin (stable above)")
    rs, rf = fits[("datasheet", "rc", True)], fits[("datasheet", "rc", False)]
    ax.plot(rf["ct"] * 1e12, rf["cf"] * 1e12, "o", color=red, mfc="white", mew=1.2, ms=6,
            label=f"best without the constraint ({100 * rf['eps']:.2f} %)")
    ax.plot(rs["ct"] * 1e12, rs["cf"] * 1e12, "o", color=blue, ms=6, label=f"best stable loop ({100 * rs['eps']:.2f} %)")
    ax.errorbar([NOTE_CT * 1e12], [0.08], yerr=[[0.03], [0.04]], fmt="s", color=grey, ms=5, capsize=2, elinewidth=1.0,
                label="the note's parasitic alone (Table 1.1)")
    ax.set_xlim(4, 9)
    ax.set_ylim(0, 0.8)
    ax.set_xlabel(r"Node capacitance $C_T$ (pF)")
    ax.set_ylabel(r"Feedback capacitance $C_F$ (pF)")
    hnd, lab = ax.get_legend_handles_labels()
    hnd.append(Patch(color=COLORS["highlight"], alpha=0.24, lw=0))
    lab.append("unstable loop")
    ax.legend(hnd, lab, loc="upper right", fontsize=7.2)
    panel_label(ax, "(a)", x=0.025)

    # (b) the chain behind the TIA, Eq. (36i)
    ax = axs[0, 1]
    ff = np.linspace(1e6, 200e6, 400)
    for kind, col, ls, lab in (("rc", blue, "-", r"50 $\Omega$ into 14 pF"),
                               ("rc2", green, DASH, r"the same, and a 2nd-order 200-MHz front end"),
                               ("rc1", red, ":", r"the same, and a 1st-order 200-MHz front end")):
        ax.plot(ff / 1e6, 20 * np.log10(chain(ff, kind)), color=col, lw=LW, ls=ls, label=lab)
    ax.axvline(f[int(np.argmax(g))] / 1e6, color=COLORS["annotation"], lw=0.8, ls=":")
    ax.text(f[int(np.argmax(g))] / 1e6 - 3, -0.4, "measured\npeak", ha="right", va="top", fontsize=7.2)
    ax.set_xlim(0, 200)
    ax.set_ylim(-6, 0.5)
    ax.set_xlabel("Frequency (MHz)")
    ax.set_ylabel(r"Chain behind the TIA, $|H_{\mathrm{chain}}|$ (dB)")
    ax.legend(loc="lower left", fontsize=7.2)
    panel_label(ax, "(b)", x=0.94)

    # (c) the measured gain, the stable fits with the chain, the TIA alone, and the fit that ignores the chain
    ax = axs[1, 0]
    ax.plot(f / 1e6, g, "o", ms=2.2, color=grey, label="measured $G$")
    fq = np.linspace(10e6, 200e6, 400)
    for name, col, lab in (("datasheet", blue, "datasheet curve"), ("macromodel", red, "macromodel $A_-$")):
        r = fits[(name, "rc", True)]
        z = np.abs(tm.tia_tf(fq, r["ol"], R_F, r["ct"], r["cf"])[0])
        ax.plot(fq / 1e6, r["k"] * z * chain(fq, "rc"), color=col, lw=LW,
                label=f"fit, {lab}, with the chain")
        if name == "datasheet":
            ax.plot(fq / 1e6, r["k"] * z, color=col, lw=LW, ls=DASH, label="its TIA alone")
    r0 = fits[("datasheet", "none", True)]
    z0 = np.abs(tm.tia_tf(fq, r0["ol"], R_F, r0["ct"], r0["cf"])[0])
    ax.plot(fq / 1e6, r0["k"] * z0, color=green, lw=LW, ls=":", label="fit ignoring the chain (datasheet curve)")
    ax.set_xlim(0, 200)
    ax.set_ylim(0, None)
    ax.set_xlabel("Frequency (MHz)")
    ax.set_ylabel(r"Gain $G$ (V/A)")
    ax.legend(loc="upper left", fontsize=7.2)
    panel_label(ax, "(c)", x=0.94)

    # (d) the input-referred noise against Eq. (19)
    ax = axs[1, 1]
    fn = b["f"][usen]
    ax.errorbar(fn / 1e6, b["i"][usen] * 1e12, yerr=b["si"][usen] * 1e12, fmt="o", ms=2.2, color=grey, elinewidth=0.8,
                label="measured, scope noise subtracted")
    i2, si = b["i"][usen] ** 2, 2 * b["i"][usen] * b["si"][usen]
    xx = (E_N * 2 * math.pi * fn) ** 2
    q, *_ = np.linalg.lstsq(np.column_stack([np.ones_like(xx), xx]) / si[:, None], (i2 - a0) / si, rcond=None)
    w2, c2f = max(q[0], 0.0), max(q[1], 0.0)
    rs = fits[("datasheet", "rc", True)]
    c_gain = rs["ct"] + rs["cf"]
    fq = np.linspace(20e6, 200e6, 300)
    for extra, c, col, ls, lab in (
            (0.0, c_gain, blue, "-", f"Eq. (19), $C_{{tot}}$ = {c_gain * 1e12:.2f} pF of the gain fit"),
            (w2, math.sqrt(c2f), green, DASH,
             f"Eq. (19) + {math.sqrt(w2) * 1e12:.1f} pA/$\\sqrt{{\\mathrm{{Hz}}}}$ white, $C_{{tot}}$ = {math.sqrt(c2f) * 1e12:.2f} pF (fit)"),
            (0.0, 5.35e-12, red, "-", r"Eq. (19), $C_{tot}$ = 5.35 pF, the note's node")):
        ax.plot(fq / 1e6, np.sqrt(a0 + extra + (E_N * 2 * math.pi * fq * c) ** 2) * 1e12, color=col, lw=LW, ls=ls, label=lab)
    ax.set_xlim(0, 200)
    ax.set_ylim(0, 12)
    ax.set_xlabel("Frequency (MHz)")
    ax.set_ylabel(r"Input-referred noise (pA/$\sqrt{\mathrm{Hz}}$)")
    ax.legend(loc="lower right", fontsize=7.2)
    panel_label(ax, "(d)", x=0.025)
    export(fig, Path(stem))
    print(f"Figure 10 written to {stem}.png and .pdf")


def draw_noise(nz, stem):
    """Figure 11: the noise at the scope and the excess referred to the input, against the two white hypotheses."""
    import matplotlib.pyplot as plt
    from make_case_figures import PANEL, panel_label
    from make_figures import COLORS, DASH, LW, configure_plot_style, export, log_axes

    configure_plot_style()
    blue, red, grey, green, purple = (COLORS["primary"], COLORS["warm_accent"], COLORS["neutral"], COLORS["cool_accent"],
                                      COLORS["purple_accent"])
    fig, axs = plt.subplots(1, 2, figsize=(2 * PANEL[0], 1.15 * PANEL[1]), constrained_layout=True)
    f, g, x, a0 = nz["f"], nz["g"], nz["x"], nz["a0"]
    wn = (E_N * 2 * math.pi * f) ** 2
    c_ds, c_mm = nz["ctots"]["datasheet"], nz["ctots"]["macromodel"]

    # (a) at the scope's input
    ax = axs[0]
    ax.plot(f / 1e6, np.sqrt(nz["s0"]) * 1e9, "o", ms=1.8, color=COLORS["grey_accent"], label="floor without light, $S_0$")
    ax.plot(f / 1e6, np.sqrt(nz["ssc"]) * 1e9, "-", lw=1.0, color=COLORS["grey_accent"], label="oscilloscope alone (TIA off)")
    ax.plot(f / 1e6, np.sqrt(x) * 1e9, "o", ms=2.2, color=grey, label="the TIA's part, $S_0 - S_{\\mathrm{scope}}$")
    for c, col, lab in ((c_ds, blue, "datasheet-curve fit"), (c_mm, red, "fit with the macromodel's $A_-$")):
        ax.plot(f / 1e6, np.sqrt(g ** 2 * (a0 + wn * c ** 2)) * 1e9, color=col, lw=LW,
                label=f"Eq. (19) through $G$, {c * 1e12:.2f} pF ({lab})")
    ex = x - g ** 2 * (a0 + wn * c_ds ** 2)
    ok = ex > 0
    ax.plot(f[ok] / 1e6, np.sqrt(ex[ok]) * 1e9, "s", ms=2.2, color=green, label="excess with 6.47 pF")
    u = nz["fits"]["scope"]["amp"]
    ax.axhline(u * 1e9, color=green, lw=LW, ls=DASH, label=f"white at the scope, {u * 1e9:.1f} nV/$\\sqrt{{\\mathrm{{Hz}}}}$")
    ax.set_xlim(0, 200)
    ax.set_ylim(3, 100)
    log_axes(ax, x=False, y=True)
    ax.set_xlabel("Frequency (MHz)")
    ax.set_ylabel(r"Noise at the oscilloscope's input (nV/$\sqrt{\mathrm{Hz}}$)")
    ax.legend(loc="upper left", fontsize=6.8, ncol=1)
    panel_label(ax, "(a)", x=0.93)

    # (b) the excess referred to the input, and the two white hypotheses scaled to it over 25-100 MHz
    ax = axs[1]
    for c, col, mk, lab in ((c_ds, blue, "o", "datasheet-curve fit"), (c_mm, red, "s", "fit with the macromodel's $A_-$")):
        e = (x - g ** 2 * (a0 + wn * c ** 2)) / g ** 2
        ok = e > 0
        ax.plot(f[ok] / 1e6, np.sqrt(e[ok]) * 1e12, mk, ms=2.2, color=col, mfc=col if col == blue else "white",
                label=f"excess with {c * 1e12:.2f} pF ({lab})")
    e = (x - g ** 2 * (a0 + wn * c_ds ** 2)) / g ** 2
    m = (f >= 25e6) & (f < 100e6)
    w_in = math.sqrt(float(np.mean(e[m])))
    u_sc = math.sqrt(float(np.mean(e[m] * g[m] ** 2)))
    ax.plot(f / 1e6, np.full_like(f, w_in) * 1e12, color=green, lw=LW,
            label=f"white at the node, {w_in * 1e12:.1f} pA/$\\sqrt{{\\mathrm{{Hz}}}}$ (25–100 MHz)")
    ax.plot(f / 1e6, u_sc / g * 1e12, color=purple, lw=LW, ls=DASH,
            label=f"white at the scope, {u_sc * 1e9:.1f} nV/$\\sqrt{{\\mathrm{{Hz}}}}$ / $G$ (25–100 MHz)")
    ax.plot(nz["lf"]["f"] / 1e6, nz["lf"]["i"] * 1e12, "^", ms=2.6, color=grey, label="total below 25 MHz")
    ax.axvspan(25, 100, color=COLORS["highlight"], alpha=0.24, lw=0, zorder=0)
    ax.text(62.5, 0.62, "excess nearly\nindependent of $e_nC_{\\mathrm{tot}}$", ha="center", va="bottom", fontsize=7.0)
    ax.set_xlim(0, 200)
    ax.set_ylim(0.5, 200)
    log_axes(ax, x=False, y=True)
    ax.set_xlabel("Frequency (MHz)")
    ax.set_ylabel(r"Excess referred to the input (pA/$\sqrt{\mathrm{Hz}}$)")
    ax.legend(loc="upper right", fontsize=6.8)
    panel_label(ax, "(b)", x=0.025)
    export(fig, Path(stem))
    print(f"Figure 11 written to {stem}.png and .pdf")


def draw_second(fits, sb, stem):
    """Figure 12: peaking against the added feedback capacitance, and the responses of the first and second boards."""
    import matplotlib.pyplot as plt
    from make_case_figures import PANEL, panel_label
    from make_figures import COLORS, DASH, LW, configure_plot_style, export

    configure_plot_style()
    blue, red = COLORS["primary"], COLORS["warm_accent"]
    fig, axs = plt.subplots(1, 2, figsize=(2 * PANEL[0], 1.15 * PANEL[1]), constrained_layout=True)
    ax = axs[0]
    adds = np.arange(0.0, 0.801e-12, 0.01e-12)
    for name, col in (("datasheet", blue), ("macromodel", red)):
        for kind, ls, lab in (("rc", "-", "14-pF chain"), ("rc2", DASH, "and a 2nd-order front end"), ("rc1", ":", "and a 1st-order front end")):
            r = fits[(name, kind, True)]
            pk = [tm.loop_metrics(r["ol"], R_F, r["ct"], r["cf"] + d)["peaking_dB"] for d in adds]
            ax.plot(adds * 1e12, pk, color=col, ls=ls, lw=LW, label=f"{'datasheet curve' if name == 'datasheet' else 'macromodel' + chr(39) + 's $A_-$'}, {lab}")
            edge = sb["incs"][(name, kind)]["edge"]["add"]
            if edge <= 0.8e-12:
                ax.plot([edge * 1e12], [0.0], marker="v", color=col, ms=5, ls="none")
    ax.axhline(1.0, color=COLORS["annotation"], lw=0.8, ls=DASH)
    ax.axvspan(0.45, 0.55, color=COLORS["highlight"], alpha=0.24, lw=0, zorder=0)
    ax.text(0.5, 9.5, "0.5 pF\n± 0.05 pF", ha="center", va="top", fontsize=7.2)
    ax.text(0.79, 1.15, "1 dB", ha="right", va="bottom", fontsize=7.2, color=COLORS["annotation"])
    ax.set_xlim(0, 0.8)
    ax.set_ylim(-0.3, 16)
    ax.set_xlabel(r"Feedback capacitance added to the board, $\Delta C_F$ (pF)")
    ax.set_ylabel("Transimpedance peaking (dB)")
    ax.legend(loc="upper right", fontsize=6.8)
    panel_label(ax, "(a)", x=0.025)

    ax = axs[1]
    ff = np.logspace(6.7, 9.3, 600)
    r = fits[("datasheet", "rc", True)]
    cols = (COLORS["neutral"], COLORS["purple_accent"], blue, COLORS["cool_accent"])
    for add, col in zip((0.0, 0.41e-12, 0.50e-12, 0.55e-12), cols):
        z = np.abs(tm.tia_tf(ff, r["ol"], R_F, r["ct"], r["cf"] + add)[0]) / R_F
        m = tm.loop_metrics(r["ol"], R_F, r["ct"], r["cf"] + add)
        lab = "board as built" if add == 0 else f"+{add * 1e12:.2f} pF"
        ax.plot(ff / 1e6, 20 * np.log10(z), color=col, lw=LW, label=f"{lab}, {m['pm_deg']:.0f}°")
        ax.plot(ff / 1e6, 20 * np.log10(z * chain(ff, "rc")), color=col, lw=1.0, ls=DASH)
    rm = fits[("macromodel", "rc", True)]
    z = np.abs(tm.tia_tf(ff, rm["ol"], R_F, rm["ct"], rm["cf"] + 0.55e-12)[0]) / R_F
    ax.plot(ff / 1e6, 20 * np.log10(z), color=red, lw=1.0, label="+0.55 pF, fit with the macromodel's $A_-$")
    ax.set_xscale("log")
    ax.set_xlim(5, 2000)
    ax.set_ylim(-15, 14)
    ax.set_xlabel("Frequency (MHz)")
    ax.set_ylabel(r"$|Z_T|/R_F$ (dB)")
    ax.legend(loc="lower left", fontsize=6.8)
    panel_label(ax, "(b)", x=0.025)
    export(fig, Path(stem))
    print(f"Figure 12 written to {stem}.png and .pdf")


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    main()
