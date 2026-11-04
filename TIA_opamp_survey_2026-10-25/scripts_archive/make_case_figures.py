"""Figures of the two design examples of Chapter 4 (OPA855 and OPA846 at R_F = 2 kOhm).

Usage: python make_case_figures.py [--spice <spice folder>] [--out <figure folder>] [--only NAME ...]

Reads what case_studies.py saved (spice/results/case_studies.json and case_studies_curves.json)
and evaluates our analytical model (Chapter 3) with the datasheet values for the dashed curves.
No simulation is run.  Writes PNG (600 dpi) and PDF in the style of make_figures.py:

  fig33_case_opa855_simulation   OPA855 design: transimpedance, loop gain, step, noise and its
                                 terms at C_D = 1 pF; transimpedance and noise at C_D = 0-5 pF
  fig35_case_opa846_simulation   the same for the OPA846 design
  fig36_case_design_space        both designs against the feedback capacitance (C_D = 1 pF) and
                                 against the photodiode capacitance (C_F fixed, and C_F chosen
                                 anew at each C_D)
  fig37_case_large_signal_dr     the largest output amplitude against frequency (Eq. (26) and the
                                 macromodels' -60 and -40 dBc points) and the dynamic range in
                                 150 MHz against I1 + I2 (Eq. (27))

Where the curves come from (equation numbers of the note as of 4 November 2026):
  solid, "SPICE"       the vendor's macromodel in ngspice, as saved by case_studies.py run:
                       loop gain by Middlebrook's double injection (Eqs. (37)-(39)), Z_T with a
                       1-A AC photocurrent, the .noise analysis referred to that source, and a
                       transient step; none of it is recomputed here.
  dashed, "analytical model" / "model"
                       our analytical model of Chapter 3, computed here or in case_studies.py with
                       case_studies.Analytic (the datasheet open-loop curve interpolated by
                       tia_model.InterpOpenLoop, the datasheet e_n(f), i_n and C_CM + C_DIFF):
      (a), (b)         tia_model.tia_tf: Z_F (Eq. (8)), NG and T = A/NG (Eq. (10)) and
                       Z_T = -Z_F T/(1 + T) (Eq. (9)) on 1200 log-spaced points, 100 kHz-10 GHz,
                       with C_T = C_D + 0.35 pF + C_CM + C_DIFF (Eq. (7));
      (c)              Analytic.step: the inverse Fourier transform of that Z_T times the
                       spectrum of the SPICE source's 20-ps ramp (derivation in its docstring);
      (d)              Analytic.noise: Eq. (19) and its terms 4kT/R_F, i_n^2 and
                       e_n^2 [1/R_F^2 + (w C_tot)^2], C_tot = C_T + C_F;
      design space     the model rows of case_studies.json, written by Analytic.loop
                       (tia_model.loop_metrics, the metrics of Section 3.5) on the same C_D and
                       C_F points as SPICE; the noise penalty is Eq. (21) of Analytic.noise;
      grey dashed      Eq. (47), GM = 20 log10(NG_inf/5.3) with NG_inf = 1 + C_T/C_F (Eq. (11))
                       and the OPA855 macromodel's own 0.80 pF of input capacitance;
      large signals    Eq. (26) from the datasheet's swing and slew rate (case_studies.vpk_claim);
                       the dynamic range is Eq. (27) with the model's or SPICE's noise and |Z_T|,
                       as saved by case_studies.py (case_studies.dynamic_range).
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

import tia_model as tm
from case_studies import CASES, C_D_NOM, F0, Analytic, cd_key, load_results
from make_figures import COLORS, DASH, LW, configure_plot_style, export, log_axes
from run_analysis import C_PCB_NOM

HERE = Path(__file__).resolve().parent
PANEL = (4.2, 3.24)
DOT = ":"
PART_COLORS = {"OPA855": COLORS["primary"], "OPA846": COLORS["warm_accent"]}
FAMILY_CD = (0.0, 0.5, 1.0, 2.0, 3.0, 5.0)
FAMILY_COLORS = {0.0: COLORS["primary"], 0.5: COLORS["teal_accent"], 1.0: COLORS["neutral"],
                 2.0: COLORS["cool_accent"], 3.0: COLORS["purple_accent"], 5.0: COLORS["warm_accent"]}
STEMS = {"OPA855": "fig33_case_opa855_simulation", "OPA846": "fig35_case_opa846_simulation"}


def panel_label(ax, text, x=0.025, y=0.965):
    ax.text(x, y, text, transform=ax.transAxes, ha="left", va="top", fontweight="bold")


def cd_label(c):
    return f"{c:g} pF"


# ---------------------------------------------------------------- per-design figure
def fig_case(res, part, stem):
    cs, r = CASES[part], res[part]
    an = Analytic(part)
    R_F, C_F = cs["R_F"], cs["C_F"]
    cur = r["curves"]
    nom = r["nominal"]
    fig, axs = plt.subplots(3, 2, figsize=(2 * PANEL[0], 3 * PANEL[1]), constrained_layout=True)

    # (a) transimpedance at the nominal design
    ax = axs[0, 0]
    f = np.array(cur["zt_f_Hz"])
    z_s = np.array(cur["zt_dB"][cd_key(C_D_NOM * 1e12)])
    # our analytical model: Z_T (Eq. (9)) and T = A/NG (Eq. (10)) from the interpolated datasheet
    # open-loop curve, C_T of Eq. (7) at C_D = 1 pF, on 1200 log-spaced points from 100 kHz to 10 GHz
    fm = np.logspace(5, 10, 1200)
    Zm, _, Tm = tm.tia_tf(fm, an.ol, R_F, an.C_T(C_D_NOM), C_F)
    ax.plot(f, z_s, color=COLORS["neutral"], lw=LW, label="SPICE")
    ax.plot(fm, 20 * np.log10(np.abs(Zm)), color=COLORS["neutral"], lw=LW, ls=DASH, label="analytical model")
    ax.axhline(20 * math.log10(R_F / math.sqrt(2)), color=COLORS["annotation"], lw=0.8, ls=DOT)
    log_axes(ax, x=True, y=False)
    ax.set_xlim(1e6, 1e10)
    ax.set_ylim(20, 72)
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel(r"$|Z_T|$ (dB$\Omega$)")
    s, m = nom["spice"], nom["analytical"]
    ax.text(0.03, 0.06, f"$-3$ dB: SPICE {s['f3_MHz']:.0f} MHz, model {m['f3_MHz']:.0f} MHz",
            transform=ax.transAxes, ha="left", va="bottom")
    ax.legend(loc="lower left", bbox_to_anchor=(0.0, 0.12))
    panel_label(ax, "(a)")

    # (b) loop gain: magnitude (left) and phase (right)
    ax = axs[0, 1]
    fl = np.array(cur["loop_f_Hz"])
    ax.plot(fl, cur["loop_dB"], color=COLORS["neutral"], lw=LW, label=r"$|T|$, SPICE")
    ax.plot(fm, 20 * np.log10(np.abs(Tm)), color=COLORS["neutral"], lw=LW, ls=DASH, label=r"$|T|$, model")
    ax.axhline(0, color=COLORS["annotation"], lw=0.8, ls=DOT)
    log_axes(ax, x=True, y=False)
    ax.set_xlim(1e6, 3e10)
    ax.set_ylim(-40, 80)
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel(r"Loop gain $|T|$ (dB)")
    ax2 = ax.twinx()
    ph_s = np.array(cur["loop_deg"])
    ph_m = np.degrees(np.unwrap(np.angle(Tm)))
    ax2.plot(fl, ph_s, color=COLORS["primary"], lw=LW, label=r"$\angle T$, SPICE")
    ax2.plot(fm, ph_m, color=COLORS["primary"], lw=LW, ls=DASH, label=r"$\angle T$, model")
    ax2.axhline(-180, color=COLORS["primary"], lw=0.8, ls=DOT)
    ax2.set_ylim(-300, 60)
    ax2.set_ylabel(r"Loop phase $\angle T$ (deg)", color=COLORS["primary"])
    ax2.tick_params(axis="y", colors=COLORS["primary"])
    for x in (s["f_c_MHz"],):
        ax.axvline(x * 1e6, color=COLORS["annotation"], lw=0.8, ls=DOT)
    ax.text(0.97, 0.95, f"SPICE: $f_c$ {s['f_c_MHz']:.0f} MHz, $\\phi_M$ {s['pm_deg']:.1f}°, GM {s['gm_dB']:.1f} dB\n"
                        f"model: $f_c$ {m['f_c_MHz']:.0f} MHz, $\\phi_M$ {m['pm_deg']:.1f}°, GM {m['gm_dB']:.1f} dB",
            transform=ax.transAxes, ha="right", va="top")
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="lower left", ncol=1)
    panel_label(ax, "(b)", x=0.025, y=0.80)

    # (c) step response
    ax = axs[1, 0]
    t_s, v_s = np.array(cur["step_t_ns"]), np.array(cur["step_mV"])
    v_s = v_s - np.mean(v_s[t_s < 1.9])          # the output's DC level before the step (bias current x R_F)
    # the model's step, saved by case_studies.py: Analytic.step, the inverse FFT of Z_T(f) times the
    # spectrum of the 20-ps ramp of the SPICE source
    t_m, v_m = np.array(cur["step_analytical_t_ns"]), np.array(cur["step_analytical_mV"])
    ax.plot(t_s, v_s, color=COLORS["neutral"], lw=LW, label="SPICE")
    ax.plot(t_m, v_m, color=COLORS["neutral"], lw=LW, ls=DASH, label="analytical model")
    t_end = 8.0 if part == "OPA855" else 14.0
    ax.set_xlim(1.0, t_end)
    ax.set_ylim(-1, 26)
    ax.set_xlabel("Time (ns)")
    ax.set_ylabel("Output (mV)")
    ax.text(0.97, 0.06, f"SPICE: {s['overshoot_pct']:.1f} % overshoot, {s['rise_10_90_ps']:.0f} ps rise,\n"
                        f"1 % settling {s['settle_1pct_ns']:.2f} ns\n"
                        f"model: {m['overshoot_pct']:.1f} %, {m['rise_10_90_ps']:.0f} ps, {m['settle_1pct_ns']:.2f} ns",
            transform=ax.transAxes, ha="right", va="bottom")
    ax.legend(loc="upper right")
    panel_label(ax, "(c)")

    # (d) input-referred noise and its terms
    ax = axs[1, 1]
    fn = np.array(cur["noise_f_Hz"])
    n_s = np.array(cur["noise_in_pA"][cd_key(C_D_NOM * 1e12)])
    fq = np.logspace(6, 9, 600)
    # Eq. (19) with the datasheet e_n(f), i_n and C_tot = C_T + C_F (Analytic.noise, central estimate)
    tot, comp = an.noise(R_F, C_D_NOM, C_F, fq)
    ax.plot(fn, n_s, color=COLORS["neutral"], lw=LW, label="SPICE")
    ax.plot(fq, tot * 1e12, color=COLORS["neutral"], lw=LW, ls=DASH, label="analytical model")
    # the terms of Eq. (19) with the datasheet values
    s_rf, s_in, s_en = (np.sqrt(comp[k]) * 1e12 for k in ("RF", "i_n", "e_n"))
    ax.plot(fq, s_rf, color=COLORS["cool_accent"], lw=LW, ls=DASH, label=r"$\sqrt{4k_BT/R_F}$")
    ax.plot(fq, s_in, color=COLORS["purple_accent"], lw=LW, ls=DASH, label=r"$i_n$")
    ax.plot(fq, s_en, color=COLORS["primary"], lw=LW, ls=DASH,
            label=r"$e_n\sqrt{1/R_F^2+(\omega C_{\mathrm{tot}})^2}$")
    for i_dc, lab in ((1e-4, "0.1 mA"), (1e-3, "1 mA")):
        lvl = math.sqrt(2 * tm.Q_E * i_dc) * 1e12
        ax.axhline(lvl, color=COLORS["annotation"], lw=0.8, ls=DOT)
        ax.text(1.15e6, lvl * 1.06, f"shot noise, {lab}", ha="left", va="bottom", color=COLORS["annotation"])
    log_axes(ax)
    ax.set_xlim(1e6, 1e9)
    ax.set_ylim(0.08, 40)
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel(r"Input-referred noise (pA/$\sqrt{\mathrm{Hz}}$)")
    ax.legend(loc="lower right", ncol=1)
    panel_label(ax, "(d)")

    # (e) transimpedance against the photodiode capacitance, C_F fixed
    ax = axs[2, 0]
    for c in FAMILY_CD:
        ax.plot(f, cur["zt_dB"][cd_key(c)], color=FAMILY_COLORS[c], lw=LW, label=r"$C_D$ = " + cd_label(c))
    ax.axhline(20 * math.log10(R_F / math.sqrt(2)), color=COLORS["annotation"], lw=0.8, ls=DOT)
    log_axes(ax, x=True, y=False)
    ax.set_xlim(1e7, 5e9)
    ax.set_ylim(30, 72)
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel(r"$|Z_T|$ (dB$\Omega$), SPICE")
    ax.legend(loc="lower left", ncol=2)
    panel_label(ax, "(e)")

    # (f) input-referred noise against the photodiode capacitance
    ax = axs[2, 1]
    for c in FAMILY_CD:
        ax.plot(fn, cur["noise_in_pA"][cd_key(c)], color=FAMILY_COLORS[c], lw=LW, label=r"$C_D$ = " + cd_label(c))
    log_axes(ax)
    ax.set_xlim(1e6, 1e9)
    ax.set_ylim(1.2, 60)
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel(r"Input-referred noise (pA/$\sqrt{\mathrm{Hz}}$), SPICE")
    ax.legend(loc="lower right", ncol=2)
    panel_label(ax, "(f)")
    export(fig, stem)


# ---------------------------------------------------------------- design space
def fig_design_space(res, stem):
    fig, axs = plt.subplots(3, 2, figsize=(2 * PANEL[0], 3 * PANEL[1]), constrained_layout=True)
    nomk = cd_key(C_D_NOM * 1e12)
    for part in CASES:
        r, col = res[part], PART_COLORS[part]
        cf = np.array(r["cf_scan"]["cf_pF"])
        g = r["cf_scan"]["by_cd"][nomk]
        # a SPICE point counts as unstable when its gain margin is 0 dB or less or its phase margin
        # is negative (the macromodel then oscillates near 3 GHz); those points are not drawn
        unstable_s = np.array([x["pm_deg"] is None or x["pm_deg"] < 0 or (x["gm_dB"] is not None and x["gm_dB"] <= 0.0)
                               for x in g["spice"]])
        pm_s = np.array([np.nan if (x["pm_deg"] is None or u) else x["pm_deg"] for x, u in zip(g["spice"], unstable_s)])
        # the model's rows were written by Analytic.loop (tia_model.loop_metrics) at the same points; a
        # second crossing of |T| = 1 (on OPA855's plotted 4-7 GHz bump) counts as unstable and is not drawn
        pm_m = np.array([np.nan if (x["pm_deg"] is None or not x["stable"]) else x["pm_deg"] for x in g["analytical"]])
        f3_s = np.array([np.nan if (x["f3_MHz"] is None or u) else x["f3_MHz"] for x, u in zip(g["spice"], unstable_s)])
        f3_m = np.array([np.nan if (x["f3_MHz"] is None or not x["stable"]) else x["f3_MHz"] for x in g["analytical"]])
        design = r["design"]["C_F_pF"]
        k = int(np.argmin(np.abs(cf - design)))
        for ax, ys, ym in ((axs[0, 0], pm_s, pm_m), (axs[0, 1], f3_s, f3_m)):
            ax.plot(cf, ys, color=col, lw=LW, label=f"{part}, SPICE")
            ax.plot(cf, ym, color=col, lw=LW, ls=DASH, label=f"{part}, model")
            ax.plot([cf[k]], [ys[k]], "o", color=col, ms=5, mfc="white", mew=1.2, zorder=5)
        if unstable_s.any():
            j = int(np.argmax(unstable_s))
            x_u = cf[j]
            axs[0, 0].annotate(f"{part} oscillates in SPICE\nfrom {x_u:.2f} pF", xy=(cf[j - 1], pm_s[j - 1]),
                               xytext=(cf[j - 1] + 0.12, pm_s[j - 1] + 12), ha="left", va="bottom", color=col,
                               arrowprops=dict(arrowstyle="-", color=col, lw=0.8))
        # against the photodiode capacitance, C_F fixed
        sw = r["cd_sweep"]
        cd = np.array([x["C_D_pF"] for x in sw])
        get = lambda src, q: np.array([np.nan if x[src][q] is None else x[src][q] for x in sw])
        axs[1, 0].plot(cd, get("spice", "pm_deg"), "o-", color=col, lw=LW, ms=3.5, label=f"{part}, SPICE")
        axs[1, 0].plot(cd, get("analytical", "pm_deg"), color=col, lw=LW, ls=DASH, label=f"{part}, model")
        axs[1, 1].plot(cd, get("spice", "f3_MHz"), "o-", color=col, lw=LW, ms=3.5, label=f"{part}, SPICE, $C_F$ fixed")
        axs[1, 1].plot(cd, get("analytical", "f3_MHz"), color=col, lw=LW, ls=DASH, label=f"{part}, model, $C_F$ fixed")
        rd = r["redesign"]
        f3_rd = np.array([np.nan if e["spice"].get("f3_MHz") is None else e["spice"]["f3_MHz"] for e in rd])
        ok = np.array([e["spice"]["meets"] for e in rd])
        axs[1, 1].plot(cd, f3_rd, color=col, lw=LW, ls=DOT, label=f"{part}, SPICE, $C_F$ chosen at each $C_D$")
        axs[1, 1].plot(cd[ok], f3_rd[ok], "s", color=col, ms=4, mfc="white", mew=1.1)
        axs[1, 1].plot(cd[~ok], f3_rd[~ok], "x", color=col, ms=5, mew=1.2)
        axs[2, 0].plot(cd, get("spice", "gm_dB"), "o-", color=col, lw=LW, ms=3.5, label=f"{part}, gain margin")
        axs[2, 0].plot(cd, get("spice", "peak_dB"), "^", color=col, ls=DASH, lw=LW, ms=3.5, label=f"{part}, peaking")
        pen_s = np.array([x["spice"]["noise"]["penalty_10_150_dB"] for x in sw])
        # Eq. (21): Eq. (19) integrated over 10-150 MHz against the Johnson noise of R_F (Analytic.noise)
        pen_m = np.array([x["analytical"]["noise"]["penalty_10_150_dB"] for x in sw])
        axs[2, 1].plot(cd, pen_s, "o-", color=col, lw=LW, ms=3.5, label=f"{part}, SPICE")
        axs[2, 1].plot(cd, pen_m, color=col, lw=LW, ls=DASH, label=f"{part}, model")
    # OPA855 gain margin from Eq. (47), with the macromodel's own 0.80 pF of input capacitance
    cdx = np.linspace(0.0, 5.0, 200)
    ng = 1 + (cdx + C_PCB_NOM * 1e12 + 0.80) / (CASES["OPA855"]["C_F"] * 1e12)
    axs[2, 0].plot(cdx, 20 * np.log10(ng / 5.3), color=COLORS["annotation"], lw=0.9, ls=DASH,
                   label="OPA855, Eq. (47)")
    a = axs[0, 0]
    a.axhline(45, color=COLORS["annotation"], lw=0.8, ls=DOT)
    a.set_xlabel(r"Total feedback capacitance $C_F$ (pF), $C_D$ = 1 pF")
    a.set_ylabel(r"Phase margin $\phi_M$ (deg)")
    a.set_xlim(0.1, 2.0)
    a.set_ylim(0, 90)
    a.legend(loc="upper right")
    panel_label(a, "(a)")
    a = axs[0, 1]
    a.axhline(150, color=COLORS["annotation"], lw=0.8, ls=DOT)
    a.set_xlabel(r"Total feedback capacitance $C_F$ (pF), $C_D$ = 1 pF")
    a.set_ylabel(r"$-3$-dB bandwidth (MHz)")
    a.set_xlim(0.1, 2.0)
    a.set_ylim(0, 900)
    a.legend(loc="upper right")
    panel_label(a, "(b)")
    a = axs[1, 0]
    a.axhline(45, color=COLORS["annotation"], lw=0.8, ls=DOT)
    a.set_xlabel(r"Photodiode capacitance $C_D$ (pF), $C_F$ fixed")
    a.set_ylabel(r"Phase margin $\phi_M$ (deg)")
    a.set_xlim(0, 5)
    a.set_ylim(20, 75)
    a.legend(loc="lower left", ncol=2)
    panel_label(a, "(c)")
    a = axs[1, 1]
    a.axhline(150, color=COLORS["annotation"], lw=0.8, ls=DOT)
    a.set_xlabel(r"Photodiode capacitance $C_D$ (pF)")
    a.set_ylabel(r"$-3$-dB bandwidth (MHz)")
    a.set_xlim(0, 5)
    a.set_ylim(0, 1000)
    a.legend(loc="upper right", fontsize=7.2)
    panel_label(a, "(d)")
    a = axs[2, 0]
    a.axhline(3, color=COLORS["annotation"], lw=0.8, ls=DOT)
    a.axhline(1, color=COLORS["annotation"], lw=0.8, ls=DOT)
    a.set_xlabel(r"Photodiode capacitance $C_D$ (pF), $C_F$ fixed")
    a.set_ylabel("Gain margin and peaking (dB), SPICE")
    a.set_xlim(0, 5)
    a.set_ylim(0, 18)
    a.legend(loc="lower right", bbox_to_anchor=(1.0, 0.16))
    panel_label(a, "(e)")
    a = axs[2, 1]
    a.set_xlabel(r"Photodiode capacitance $C_D$ (pF), $C_F$ fixed")
    a.set_ylabel("Noise penalty, 10–150 MHz (dB)")
    a.set_xlim(0, 5)
    a.set_ylim(0, 10)
    a.legend(loc="upper left")
    panel_label(a, "(f)", x=0.94)
    export(fig, stem)


# ---------------------------------------------------------------- large signals, dynamic range
def fig_large_signal_dr(res, stem):
    fig, axs = plt.subplots(1, 2, figsize=(2 * PANEL[0], PANEL[1] + 0.4), constrained_layout=True)
    ax = axs[0]
    fq = np.logspace(math.log10(1e7), math.log10(3e8), 300)
    from case_studies import vpk_claim
    for part in CASES:
        col = PART_COLORS[part]
        # Eq. (26): the smaller of the datasheet's half swing (light load) and SR/(2 pi f)
        v = [vpk_claim(part, x)[0] for x in fq]
        ax.plot(fq, v, color=col, lw=LW, label=f"{part}, Eq. (26)")
        tone = res[part]["tone"]
        fr = np.array([float(k.split()[0]) * 1e6 for k in tone])
        v40 = np.array([np.nan if t["v_at_thd_m40"] is None else t["v_at_thd_m40"] for t in tone.values()])
        v60 = np.array([np.nan if t["v_at_thd_m60"] is None else t["v_at_thd_m60"] for t in tone.values()])
        ax.plot(fr, v40, "o", color=col, ms=5, label=f"{part}, SPICE, THD $-40$ dBc")
        ax.plot(fr, v60, "s", color=col, ms=5, mfc="white", mew=1.2, label=f"{part}, SPICE, THD $-60$ dBc")
    log_axes(ax)
    ax.set_xlim(1e7, 3e8)
    ax.set_ylim(0.05, 8)
    ax.set_xlabel("Tone frequency (Hz)")
    ax.set_ylabel("Output amplitude (V peak)")
    ax.legend(loc="lower left", fontsize=7.2)
    panel_label(ax, "(a)", x=0.94)

    ax = axs[1]
    for part in CASES:
        col = PART_COLORS[part]
        d = res[part]["dr"]["curve"]
        i = np.array(d["i_dc_mA"])
        ax.plot(i, d["spice"], color=col, lw=LW, label=f"{part}, SPICE noise")
        # Eq. (27) with the model's Eq. (19) noise and |Z_T(100 MHz)| (case_studies.dynamic_range)
        ax.plot(i, d["model"], color=col, lw=LW, ls=DASH, label=f"{part}, model noise")
    # OPA846 with the amplitude at which its macromodel reaches -40 dBc at 100 MHz
    r46 = res["OPA846"]["dr"]
    if "m40" in r46.get("at_thd", {}):
        shift = 20 * math.log10(r46["at_thd"]["m40"]["v_pk_V"] / r46["vpk_V"])
        i = np.array(r46["curve"]["i_dc_mA"])
        ax.plot(i, np.array(r46["curve"]["spice"]) + shift, color=PART_COLORS["OPA846"], lw=LW, ls=DOT,
                label=f"OPA846, SPICE, at $-40$ dBc ({r46['at_thd']['m40']['v_pk_V']:.2f} V)")
    ax.set_xscale("log")
    from matplotlib.ticker import LogFormatterMathtext, NullFormatter
    ax.xaxis.set_major_formatter(LogFormatterMathtext())
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_xlim(1e-3, 20)
    ax.set_ylim(45, 85)
    ax.set_xlabel(r"DC photocurrent $I_1 + I_2$ (mA)")
    ax.set_ylabel("Dynamic range in 150 MHz, 100-MHz tone (dB)")
    ax.legend(loc="lower left", fontsize=7.2)
    panel_label(ax, "(b)", x=0.94)
    export(fig, stem)


FIGS = {"opa855": lambda res, out: fig_case(res, "OPA855", out / STEMS["OPA855"]),
        "opa846": lambda res, out: fig_case(res, "OPA846", out / STEMS["OPA846"]),
        "space": lambda res, out: fig_design_space(res, out / "fig36_case_design_space"),
        "large": lambda res, out: fig_large_signal_dr(res, out / "fig37_case_large_signal_dr")}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--spice", default=str(HERE.parent / "spice"))
    ap.add_argument("--out", default=str(HERE.parent / "figures"))
    ap.add_argument("--only", nargs="+", default=list(FIGS), choices=list(FIGS))
    a = ap.parse_args()
    configure_plot_style()
    res = load_results(Path(a.spice))
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for k in a.only:
        FIGS[k](res, out)
        print("drawn", k)


if __name__ == "__main__":
    main()
