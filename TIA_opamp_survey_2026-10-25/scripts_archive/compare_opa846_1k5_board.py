"""Section 4.11 of the note: a measured OPA846 board at R_F = 1.5 kOhm (0603 resistor, no fitted feedback capacitor)
against Sections 4.10 and 3.10, through the shape of its shot-noise-calibrated gain and through its noise.

Usage:
    python compare_opa846_1k5_board.py [--data CSV] [--aol AOL_TXT] [--figure [OUT_STEM]]

--data    the board's per-1-MHz table, by default ../data/measurements/opa846_1k5_board_per_MHz.csv.  In every
          1 MHz bin the measurement's own analysis fitted the output noise against the total photocurrent,
          S(I) = S0 + 2 q G^2 I, over 20 records from 1.94 uA to 4.90 mA and one without light; the slope gives the
          gain G (photocurrent to the voltage at the scope input) and the floor the input-referred noise, with the
          scope's own noise (a record with the TIA off) subtracted.  Bins with tones or too little shot noise are
          flagged there and left out here.
--aol     the macromodel's inverting-input open-loop run of spice_tia_checks.py aol
          (../spice/runs/aol/OPA846_inverting/aol.txt, kept locally; spice/results/aol.json holds its summary).
--figure  draws Figure 10 (../figures/fig37c_opa846_1k5_board.png and .pdf, or OUT_STEM).
No simulation is run.  Every number of Section 4.11 and Table 4.4 is printed.

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
T_K, K_B = 295.0, 1.380649e-23
E_N, I_N = 1.2e-9, 2.8e-12      # datasheet typical values (Table A6.1)
SR, GBW = 625e6, 1750e6         # V/s, Hz (OPA846 p. 3)
NOTE_CT, NOTE_CF = 5.15e-12, (0.05e-12, 0.08e-12, 0.12e-12)
CHAINS = {"none": "no chain", "rc": "50 ohm into 14 pF", "rc2": "and a 2nd-order 200 MHz front end",
          "rc1": "and a 1st-order 200 MHz front end"}


def read_bins(path):
    rows = [r for r in csv.reader(line for line in open(path, encoding="utf-8") if not line.startswith("#"))]
    head, data = rows[0], rows[1:]
    ix = {k: i for i, k in enumerate(head)}

    def col(name):
        return np.array([float(r[ix[name]]) if r[ix[name]] not in ("", "nan") else np.nan for r in data])

    f = 0.5 * (col("f_low_MHz") + col("f_high_MHz")) * 1e6
    return dict(f=f, G=col("G_V_per_A"), sG=col("G_sigma_V_per_A"), i=col("i_TIA_A_per_rtHz"),
                si=col("i_TIA_sigma_A_per_rtHz"), bad=col("flagged") > 0)


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


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--data", default=str(HERE.parent / "data" / "measurements" / "opa846_1k5_board_per_MHz.csv"))
    ap.add_argument("--aol", default=str(HERE.parent / "spice" / "runs" / "aol" / "OPA846_inverting" / "aol.txt"))
    ap.add_argument("--figure", nargs="?", const=str(HERE.parent / "figures" / "fig37c_opa846_1k5_board"), default=None)
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
    if a.figure:
        draw(f, g, fits, models, b, usen, a0, a.figure)


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


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    main()
