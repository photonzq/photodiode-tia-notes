"""Figures for the SPICE cross-check (Section 10 of the survey).

Usage: python make_spice_figures.py [--spice <spice folder>] [--out <figure folder>] [--only 7 9 ...]

Reads what spice_tia_checks.py saved (spice/results/*.json and the arrays under spice/runs/)
and writes Figures 7-16 as PNG (600 dpi) and PDF in the style of make_figures.py.  No
simulation is run.  The defaults are the folders next to this one (../spice, ../figures).

  7  loop gain of variant A at its worst-gain-margin corner, and what Z_T shows of it;
     voltage injection alone against the double injection (OPA856)
  8  open-loop gain: datasheet curve against the macromodel from each input (OPA855, OPA818)
  9  variant A feedback-capacitance scan, and the gain margin against NG_inf (Eq. (54))
 10  variant B feedback-capacitance scan: margin, bandwidth, peaking
 11  input-referred noise: SPICE against the survey; the OPA818 model's noise terms
 12  noise penalty against worst-case phase margin and against bandwidth, 1 pF / 2 kOhm designs
 13  the OPA846 bench board against total node capacitance
 14  every part's best design at 1 pF / 2 kOhm: bandwidth, worst-case phase margin, noise penalty
 15  dynamic range (Eq. (25), 150 MHz) of the leading designs, SPICE and survey model, against
     I1 + I2 and against the tone frequency; single-chip TIAs from their datasheets
 16  what sets the dynamic range of the OPA818 design: band noise floors and the swing and
     slew-rate ceilings, against the tone and against I1 + I2
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FixedLocator, NullFormatter, NullLocator

import tia_model as tm
from make_figures import COLORS, DASH, LW, configure_plot_style, export, log_axes
from parts_db import PARTS
from run_analysis import noise_inputs, noise_models_for, open_loop_model
from spice_tia_checks import (BENCH, C_PCB_NOM, CF_DCD_pF, DESIGNS, KT, VENDOR_MODELS, datasheet,
                              loop_metrics_from_T, tag)

HERE = Path(__file__).resolve().parent
PANEL = (4.2, 3.24)
DOT = ":"
CD_COLORS = {-0.2: COLORS["primary"], 0.0: COLORS["neutral"], 0.2: COLORS["warm_accent"]}
CONFIG_COLORS = {"1 pF, 2 kOhm": COLORS["primary"], "1 pF, 1.5 kOhm": COLORS["warm_accent"],
                 "2 pF, 2 kOhm": COLORS["cool_accent"], "2 pF, 1.5 kOhm": COLORS["purple_accent"]}
PART_COLORS = {"OPA855": COLORS["primary"], "OPA818": COLORS["warm_accent"], "OPA856": COLORS["cool_accent"],
               "LMH6629": COLORS["purple_accent"], "OPA858": COLORS["teal_accent"], "OPA859": COLORS["brown_accent"],
               "OPA846": COLORS["grey_accent"]}


def config_label(key):
    """'1 pF, 2 kOhm' -> '1 pF, 2 kΩ' for legends."""
    return key.replace("kOhm", "kΩ")


def load(spice, name):
    return json.loads((spice / "results" / f"{name}.json").read_text(encoding="utf-8"))


def wrdata(path):
    return np.loadtxt(path, skiprows=1, ndmin=2)


def panel_label(ax, text, x=0.025, y=0.965):
    ax.text(x, y, text, transform=ax.transAxes, ha="left", va="top", fontweight="bold")


def db(x):
    return 20 * np.log10(np.abs(x))


def phase_deg(x):
    return np.degrees(np.unwrap(np.angle(x)))


def cross_down(f, y, level, start=0):
    """First frequency (log interpolation) above index `start` where y falls through `level`."""
    i = np.where((y[start:-1] > level) & (y[start + 1:] <= level))[0]
    if not len(i):
        return None
    k = start + i[0]
    return float(10 ** np.interp(level, [y[k + 1], y[k]], [np.log10(f[k + 1]), np.log10(f[k])]))


def log_x(ax, lo, hi):
    log_axes(ax, x=True, y=False)
    ax.set_xlim(lo, hi)


def survey_loop(part, R_F, C_D, C_F, f):
    """The survey's loop gain T = A/NG and Z_T (datasheet curve, Eqs. (7)-(8))."""
    p = PARTS[VENDOR_MODELS[part]["db"]]
    ol, *_ = open_loop_model(p)
    C_T = C_D + C_PCB_NOM + p["c_cm"] + p["c_diff"]
    Z, _, T = tm.tia_tf(f, ol, R_F, C_T, C_F)
    return T, Z


def survey_noise(part, R_F, C_D, C_F, f, model="central"):
    p = PARTS[VENDOR_MODELS[part]["db"]]
    C_T = C_D + C_PCB_NOM + p["c_cm"] + p["c_diff"]
    return np.sqrt(tm.noise_components(f, R_F, C_T, C_F, noise_inputs(p), fet_model=model)["total"])


def survey_penalty(part, R_F, C_D, C_F):
    """Band penalty over 10-150 MHz, central and (FET parts) high estimate, as in Table 10.10."""
    p = PARTS[VENDOR_MODELS[part]["db"]]
    f = np.logspace(7, np.log10(150e6), 400)
    ref = np.trapezoid(np.full_like(f, 4 * KT / R_F), f)
    out = []
    for m in ["central"] + (["high"] if "high" in noise_models_for(p) else []):
        out.append(10 * np.log10(np.trapezoid(survey_noise(part, R_F, C_D, C_F, f, m) ** 2, f) / ref))
    return out


# ---------------------------------------------------------------- Figure 7
def fig_hidden_margin(spice, stem):
    R_F, C_D, C_F = 2000.0, 0.8e-12, 0.35e-12
    lp = np.load(spice / "runs" / "loop" / tag("OPA855", R_F, C_D, C_F) / "loop.npy")
    f, T = lp[0], lp[1] + 1j * lp[2]
    # the survey's loop gain on a fine grid, up to the end of the digitized curve (9.7 GHz):
    # its 4-7 GHz bump touches 0 dB by only 0.01 dB at this corner
    fs = np.logspace(7, np.log10(9.7e9), 6000)
    Ts, _ = survey_loop("OPA855", R_F, C_D, C_F, fs)
    m = loop_metrics_from_T(f, T)
    ph, phs = phase_deg(T), phase_deg(Ts)
    i_c = int(np.searchsorted(f, m["f_c_MHz"] * 1e6))
    f180 = cross_down(f, ph, -180.0, i_c)
    ms = loop_metrics_from_T(fs, Ts)
    up = np.where((np.abs(Ts[:-1]) < 1) & (np.abs(Ts[1:]) >= 1) & (fs[1:] > 2e9))[0]
    f_second = float(fs[up[0] + 1]) if len(up) else None
    # Z_T of this corner from the SPICE loop gain, Eq. (7); the nominal design simulated directly
    Z_F = R_F / (1 + 2j * np.pi * f * R_F * C_F)
    Zw = -Z_F * T / (1 + T)
    zn = np.load(spice / "runs" / "zt" / tag("OPA855", R_F, 1e-12, 0.25e-12) / "zt.npy")
    hi = (f > 2e9) & (f < 8e9)
    k_b = int(np.argmax(np.where(hi, np.abs(Zw), 0)))
    # check of Eq. (7) against a directly simulated Z_T: the scan point next to this corner
    cs = spice / "runs" / "cfscan" / "A_OPA855_R2k_D0p80p_F0p340p"
    v, c, z = (wrdata(cs / n) for n in ("vinj.txt", "iinj.txt", "zt.txt"))
    Tv_s = -(v[:, 1] + 1j * v[:, 2]) / (v[:, 3] + 1j * v[:, 4])
    Ti_s = (c[:, 1] + 1j * c[:, 2]) / (1 - (c[:, 1] + 1j * c[:, 2]))
    T_s = (Tv_s * Ti_s - 1) / (Tv_s + Ti_s + 2)
    Zf_s = R_F / (1 + 2j * np.pi * v[:, 0] * R_F * 0.34e-12)
    Z_eq7 = -Zf_s * T_s / (1 + T_s)
    band = (v[:, 0] > 1e6) & (v[:, 0] < 4e9)
    dev = np.max(np.abs(db(Z_eq7[band]) - db(z[band, 1] + 1j * z[band, 2])))
    # above about 5 GHz the photocurrent reaching the output through C_F, which Eq. (7)
    # omits, dominates |Z_T| (at -40 dB and below), so the curve stops there
    show7 = f <= 5e9

    fig, axs = plt.subplots(2, 2, figsize=(2 * PANEL[0], 2 * PANEL[1]), constrained_layout=True)
    ax = axs[0, 0]
    ax.plot(f, db(T), color=COLORS["primary"], lw=LW, label="SPICE, double injection")
    ax.plot(fs, db(Ts), color=COLORS["neutral"], lw=LW, ls=DASH, label=r"analytical model, $A/NG$ (datasheet curve)")
    ax.axhline(0, color=COLORS["annotation"], lw=0.8, ls=DOT)
    g180 = float(np.interp(np.log10(f180), np.log10(f), db(T)))
    ax.plot([m["f_c_MHz"] * 1e6, f180], [0, g180], "o", ms=3.5, color=COLORS["primary"], label="_nolegend_")
    ax.annotate(rf"$f_c$ = {m['f_c_MHz']/1e3:.2f} GHz", xy=(m["f_c_MHz"] * 1e6, 0), xytext=(1.4e8, -14),
                color=COLORS["text"], arrowprops=dict(arrowstyle="-", color=COLORS["annotation"], lw=0.6))
    ax.annotate(f"GM = {m['gm_dB']:.1f} dB\nat {f180/1e9:.1f} GHz", xy=(f180, g180), xytext=(1.6e9, 18),
                color=COLORS["text"], arrowprops=dict(arrowstyle="-", color=COLORS["annotation"], lw=0.6))
    if f_second:
        ax.annotate(f"analytical model: back to\n0 dB at {f_second/1e9:.1f} GHz", xy=(f_second, 0), xytext=(2.7e10, 30),
                    ha="right", color=COLORS["text"],
                    arrowprops=dict(arrowstyle="-", color=COLORS["annotation"], lw=0.6))
    log_x(ax, 1e7, 3e10)
    ax.set_ylim(-35, 65)
    ax.set_xlabel(r"Frequency, $f$ (Hz)")
    ax.set_ylabel(r"Loop gain, $|T|$ (dB)")
    ax.legend(loc="upper right")
    panel_label(ax, "(a)")

    ax = axs[0, 1]
    ax.plot(f, ph, color=COLORS["primary"], lw=LW, label="SPICE, double injection")
    ax.plot(fs, phs, color=COLORS["neutral"], lw=LW, ls=DASH, label="analytical model, datasheet curve")
    ax.axhline(-180, color=COLORS["annotation"], lw=0.8, ls=DOT)
    ax.plot([m["f_c_MHz"] * 1e6], [m["pm_deg"] - 180], "o", ms=3.5, color=COLORS["primary"])
    ax.annotate(f"PM = {m['pm_deg']:.1f}°", xy=(m["f_c_MHz"] * 1e6, m["pm_deg"] - 180), xytext=(1.2e8, -150),
                color=COLORS["text"], arrowprops=dict(arrowstyle="-", color=COLORS["annotation"], lw=0.6))
    ax.annotate(rf"$f_{{180}}$", xy=(f180, -180), xytext=(f180 * 1.3, -150), color=COLORS["text"],
                arrowprops=dict(arrowstyle="-", color=COLORS["annotation"], lw=0.6))
    log_x(ax, 1e7, 3e10)
    ax.set_ylim(-300, -60)
    ax.set_xlabel(r"Frequency, $f$ (Hz)")
    ax.set_ylabel(r"Loop-gain phase, $\angle T$ (°)")
    ax.legend(loc="lower left")
    panel_label(ax, "(b)")

    ax = axs[1, 0]
    ax.plot(f[show7], db(Zw[show7] / R_F), color=COLORS["primary"], lw=LW,
            label=f"0.35 / 0.8 pF: GM {m['gm_dB']:.1f} dB")
    ax.plot(zn[0], db((zn[1] + 1j * zn[2]) / R_F), color=COLORS["neutral"], lw=LW, ls=DASH,
            label="0.25 / 1.0 pF (nominal): GM 5.1 dB")
    ax.axhline(-3, color=COLORS["annotation"], lw=0.8, ls=DOT)
    ax.text(1.15e7, -3.6, "−3 dB", color=COLORS["annotation"], va="top")
    ax.annotate(f"{db(Zw[k_b] / R_F):.1f} dB\nat {f[k_b]/1e9:.1f} GHz".replace("-", "−"), xy=(f[k_b], db(Zw[k_b] / R_F)),
                xytext=(5.5e9, -14), color=COLORS["text"],
                arrowprops=dict(arrowstyle="-", color=COLORS["annotation"], lw=0.6))
    log_x(ax, 1e7, 3e10)
    ax.set_ylim(-45, 6)
    ax.set_xlabel(r"Frequency, $f$ (Hz)")
    ax.set_ylabel(r"Transimpedance, $|Z_T|/R_F$ (dB)")
    ax.legend(loc="lower left", title=r"$C_F$ / $C_D$", title_fontsize=8, alignment="left")
    panel_label(ax, "(c)")

    ax = axs[1, 1]
    R6, C6, F6 = 2000.0, 1e-12, 0.55e-12
    l6 = np.load(spice / "runs" / "loop" / tag("OPA856", R6, C6, F6) / "loop.npy")
    f6, T6, Tv6 = l6[0], l6[1] + 1j * l6[2], l6[3] + 1j * l6[4]
    m6, mv6 = loop_metrics_from_T(f6, T6), loop_metrics_from_T(f6, Tv6)
    ax.plot(f6, db(T6), color=COLORS["cool_accent"], lw=LW, label=f"double injection, Eq. (39): GM {m6['gm_dB']:.1f} dB")
    ax.plot(f6, db(Tv6), color=COLORS["warm_accent"], lw=LW, ls=DASH,
            label=f"voltage injection alone, Eq. (37): GM {mv6['gm_dB']:.1f} dB")
    ax.axhline(0, color=COLORS["annotation"], lw=0.8, ls=DOT)
    if mv6["second_crossing_MHz"]:
        f2 = mv6["second_crossing_MHz"] * 1e6
        ax.annotate(f"false second crossing\nat {f2/1e9:.1f} GHz", xy=(f2, 0), xytext=(1.5e9, 22), ha="center",
                    color=COLORS["text"], arrowprops=dict(arrowstyle="-", color=COLORS["annotation"], lw=0.6))
    log_x(ax, 1e7, 3e10)
    ax.set_ylim(-55, 55)
    ax.set_xlabel(r"Frequency, $f$ (Hz)")
    ax.set_ylabel(r"Loop gain, $|T|$ (dB)")
    ax.legend(loc="lower left")
    panel_label(ax, "(d)")
    export(fig, stem)
    print(f"Fig 7: OPA855 corner C_F 0.35 / C_D 0.8 pF: f_c {m['f_c_MHz']:.0f} MHz, PM {m['pm_deg']:.1f}, GM "
          f"{m['gm_dB']:.2f} dB at {f180/1e9:.2f} GHz; survey PM {ms['pm_deg']:.1f}, back to 0 dB at "
          f"{f_second} Hz (max {db(Ts[fs > 3e9]).max():.2f} dB); Z_T bump {db(Zw[k_b]/R_F):.1f} dB at {f[k_b]/1e9:.2f} GHz, "
          f"in-band max {db(Zw[f < 1e9] / R_F).max():.2f} dB; Eq. (7) vs direct Z_T at 0.34 pF: max {dev:.2f} dB (1 MHz-4 GHz)")
    print(f"       OPA856: double GM {m6['gm_dB']:.1f} dB, voltage-only GM {mv6['gm_dB']:.1f} dB, "
          f"false crossing {mv6['second_crossing_MHz']} MHz")
    mid = (f > m["f_c_MHz"] * 1e6) & (f < f180)
    print(f"       OPA855 corner: |T| between f_c and f_180 spans {db(T[mid]).min():.2f} to {db(T[mid]).max():.2f} dB")


# ---------------------------------------------------------------- Figure 8
def fig_open_loop(spice, stem):
    loop = load(spice, "loop")
    fig, axs = plt.subplots(2, 2, figsize=(2 * PANEL[0], 2 * PANEL[1]), constrained_layout=True)
    for col, part in enumerate(("OPA855", "OPA818")):
        a = np.load(spice / "runs" / "aol" / part / "aol.npy")
        ai = np.load(spice / "runs" / "aol" / part / "aol_inverting.npy")
        fa, Ap = a[0], a[1] + 1j * a[2]
        fi, Am = ai[0], ai[1] + 1j * ai[2]
        pts = np.array([[q[0], q[1], np.nan if q[2] is None else q[2]] for q in PARTS[VENDOR_MODELS[part]["db"]]["ol"]["points"]])
        fc = [v["corners"]["dCF+0.0_dCD+0.0"]["spice"]["f_c_MHz"] * 1e6 for k, v in loop.items() if k.startswith(part + "|")]
        rl = VENDOR_MODELS[part]["rl"]
        for row in (0, 1):
            ax = axs[row, col]
            ax.axvspan(min(fc), max(fc), color=COLORS["highlight"], alpha=0.24, lw=0, label="_nolegend_", zorder=0)
            if row == 0:
                ax.plot(pts[:, 0], pts[:, 1], color=COLORS["neutral"], lw=LW, marker="o", ms=2.5,
                        label="datasheet curve (digitized)")
                ax.plot(fa, db(Ap), color=COLORS["primary"], lw=LW, label=r"macromodel, $A_+$")
                ax.plot(fi, db(Am), color=COLORS["warm_accent"], lw=LW, ls=DASH, label=r"macromodel, $A_-$")
                ax.axhline(0, color=COLORS["annotation"], lw=0.8, ls=DOT)
                ax.set_ylim(-25, 65)
                ax.set_ylabel(r"Open-loop gain, $|A|$ (dB)")
                ax.text(0.97, 0.965, f"{part}, $R_L$ = {rl:g} Ω", transform=ax.transAxes, ha="right", va="top")
                ax.legend(loc="lower left")
            else:
                ok = ~np.isnan(pts[:, 2])
                ax.plot(pts[ok, 0], pts[ok, 2], color=COLORS["neutral"], lw=LW, marker="o", ms=2.5,
                        label="datasheet curve (digitized)")
                ax.plot(fa, phase_deg(Ap), color=COLORS["primary"], lw=LW, label=r"macromodel, $A_+$")
                ax.plot(fi, phase_deg(Am), color=COLORS["warm_accent"], lw=LW, ls=DASH, label=r"macromodel, $A_-$")
                ax.axhline(-180, color=COLORS["annotation"], lw=0.8, ls=DOT)
                ax.set_ylim(-250, -50)
                ax.set_ylabel(r"Open-loop phase, $\angle A$ (°)")
                ax.legend(loc="lower left")
            ax.text(np.sqrt(min(fc) * max(fc)), 0.97, "TIA\ncrossover", transform=ax.get_xaxis_transform(),
                    ha="center", va="top", color=COLORS["annotation"])
            log_x(ax, 1e7, 2e10)
            ax.set_xlabel(r"Frequency, $f$ (Hz)")
            panel_label(ax, "(" + "abcd"[2 * row + col] + ")")
        print(f"Fig 8: {part}: TIA crossovers {min(fc)/1e6:.0f}-{max(fc)/1e6:.0f} MHz; datasheet magnitude to "
              f"{pts[-1, 0]/1e9:.2f} GHz, phase to {pts[~np.isnan(pts[:, 2]), 0][-1]/1e9:.2f} GHz")
        ok = ~np.isnan(pts[:, 2])
        for x in (1e7, 3e7, 1e8, 3e8, 1e9, 3.5e9):
            if x > pts[ok, 0][-1]:
                continue
            pd = float(np.interp(np.log10(x), np.log10(pts[ok, 0]), pts[ok, 2]))
            pp = float(np.interp(np.log10(x), np.log10(fa), phase_deg(Ap)))
            pm_ = float(np.interp(np.log10(x), np.log10(fi), phase_deg(Am)))
            print(f"       {x/1e6:6g} MHz: phase datasheet {pd:7.1f}, A+ {pp:7.1f}, A- {pm_:7.1f}")
        # loop gain of the variant's nominal designs at low frequency, where the phases differ most
        for pt, R_F, C_D, C_F, label in DESIGNS:
            if pt != part:
                continue
            lp = np.load(spice / "runs" / "loop" / tag(pt, R_F, C_D, C_F) / "loop.npy")
            vals = [float(np.interp(np.log10(x), np.log10(lp[0]), db(lp[1] + 1j * lp[2]))) for x in (1e7, 3e7, 1e8)]
            print(f"       {label}: |T| at 10/30/100 MHz = " + " / ".join(f"{v:.1f}" for v in vals) + " dB")
    axs[0, 0].annotate(r"plateau of $A_-$", xy=(2.5e9, 14.7), xytext=(6e8, 30), color=COLORS["text"],
                       arrowprops=dict(arrowstyle="-", color=COLORS["annotation"], lw=0.6))
    export(fig, stem)


# ---------------------------------------------------------------- Figure 9
def _grid(entry, key, q):
    return np.array([np.nan if (r[q] is None) else r[q] for r in entry[key]], float)


def _stable(entry, key):
    """A scan point counts as stable if its loop has a positive phase margin and a gain margin
    of at least 0 dB; beyond that the AC 'response' of an oscillating circuit is meaningless."""
    pm, gm = _grid(entry, key, "pm_deg"), _grid(entry, key, "gm_dB")
    return np.isfinite(pm) & (pm > 0) & ~(gm < 0)


def fig_scan_A(spice, stem):
    scan = load(spice, "cfscan")["A"]
    c_in = load(spice, "params")["OPA855"]["c_in_grounded_pF"]["100MHz"]
    s = scan["1 pF, 2 kOhm"]
    cf = np.array(s["cf_pF"])
    w = s["window_all_corners"]
    fig, axs = plt.subplots(2, 2, figsize=(2 * PANEL[0], 2 * PANEL[1]), constrained_layout=True)
    spec = (("pm_deg", r"Phase margin, PM (°)", 45.0, (0, 90)),
            ("gm_dB", r"Gain margin, GM (dB)", 3.0, (-4, 20)),
            ("peak_dB", r"Peaking of $|Z_T|$ (dB)", 1.0, (0, 8)))
    for ax, (q, ylab, lev, ylim), lab in zip((axs[0, 0], axs[0, 1], axs[1, 0]), spec, "abc"):
        ax.axvspan(w["lo_pF"], w["hi_pF"], color=COLORS["highlight"], alpha=0.24, lw=0, label="_nolegend_", zorder=0)
        for dcd in CF_DCD_pF:
            # the loop gain is a valid small-signal result at every point, so PM and GM are drawn
            # throughout (PM while positive); the closed-loop peaking only where the loop is stable
            k = f"{dcd:+.1f}"
            y = _grid(s["grid"], k, q)
            if q == "pm_deg":
                y = np.where(y > 0, y, np.nan)
            elif q == "peak_dB":
                y = np.where(_stable(s["grid"], k), y, np.nan)
            ax.plot(cf, y, color=CD_COLORS[dcd], lw=LW, label=rf"SPICE, $C_D$ = {1 + dcd:.1f} pF")
        ys = np.array([np.nan if (r[q] is None or not r["stable"]) else r[q] for r in s["survey"]["+0.0"]], float)
        ax.plot(cf, ys, color=COLORS["grey_accent"], lw=LW, ls=DASH, label=r"analytical model, $C_D$ = 1.0 pF")
        ax.axhline(lev, color=COLORS["annotation"], lw=0.8, ls=DOT)
        ax.set_xlim(0.06, 0.6)
        ax.set_ylim(*ylim)
        ax.set_xlabel(r"Total feedback capacitance, $C_F$ (pF)")
        ax.set_ylabel(ylab)
        panel_label(ax, f"({lab})")
    axs[0, 0].legend(loc="lower right")
    axs[0, 0].text(0.5 * (w["lo_pF"] + w["hi_pF"]), 4, f"window\n{w['lo_pF']:.3f}–{w['hi_pF']:.3f} pF",
                   ha="center", va="bottom", color=COLORS["text"])

    ax = axs[1, 1]
    ng = np.logspace(np.log10(4), np.log10(60), 200)
    ax.plot(ng, 20 * np.log10(ng / 5.3), color=COLORS["text"], lw=LW, ls=DASH, label=r"Eq. (47), $|A_-(f_{180})|$ = 5.3")
    for key, e in scan.items():
        cd0 = float(key.split(" pF")[0])
        first = True
        for dcd in CF_DCD_pF:
            C_T = cd0 + dcd + C_PCB_NOM * 1e12 + c_in
            x = 1 + C_T / np.array(e["cf_pF"])
            y = _grid(e["grid"], f"{dcd:+.1f}", "gm_dB")
            ax.plot(x, y, ls="none", marker="o", ms=2.6, mfc="none", mew=0.8, color=CONFIG_COLORS[key],
                    label=config_label(key) if first else "_nolegend_")
            first = False
    ax.axhline(3, color=COLORS["annotation"], lw=0.8, ls=DOT)
    ax.axvline(7.5, color=COLORS["annotation"], lw=0.8, ls=DOT)
    ax.text(7.7, -3.3, r"$NG_\infty$ = 7.5", color=COLORS["annotation"], va="bottom")
    ax.set_xscale("log")
    ax.xaxis.set_major_locator(FixedLocator([4, 5, 7.5, 10, 20, 40, 60]))
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:g}"))
    ax.xaxis.set_minor_locator(NullLocator())
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_xlim(4, 60)
    ax.set_ylim(-4, 22)
    ax.set_xlabel(r"High-frequency noise gain, $NG_\infty = 1 + C_T/C_F$")
    ax.set_ylabel(r"Gain margin, GM (dB)")
    ax.legend(loc="upper left", title="OPA855 configuration, SPICE", title_fontsize=8, alignment="left",
              bbox_to_anchor=(0.06, 1.0))
    panel_label(ax, "(d)")
    export(fig, stem)
    print(f"Fig 9: window 1 pF/2 kOhm {w['lo_pF']:.3f}-{w['hi_pF']:.3f} pF; c_in {c_in:.3f} pF")
    sv = s["survey"]["+0.0"]
    gs = np.array([np.nan if (r["gm_dB"] is None or not r["stable"]) else r["gm_dB"] for r in sv], float)
    g0 = _grid(s["grid"], "+0.0", "gm_dB")
    last = cf[np.where(np.isfinite(gs))[0][-1]]
    print(f"       survey GM - SPICE GM at C_D 1.0 pF: {np.nanmin(gs - g0):.2f} to {np.nanmax(gs - g0):.2f} dB; "
          f"survey stable up to {last:.2f} pF; first survey point flagged unstable: "
          f"{[(c, r['second_crossing'] if 'second_crossing' in r else None) for c, r in zip(cf, sv) if not r['stable']][:1]}")
    dev_all, dev_20 = [], []
    for key, e in scan.items():
        cd0 = float(key.split(" pF")[0])
        for dcd in CF_DCD_pF:
            x = 1 + (cd0 + dcd + C_PCB_NOM * 1e12 + c_in) / np.array(e["cf_pF"])
            d = _grid(e["grid"], f"{dcd:+.1f}", "gm_dB") - 20 * np.log10(x / 5.3)
            dev_all += list(d[np.isfinite(d)])
            dev_20 += list(d[np.isfinite(d) & (x <= 20)])
    print(f"       GM - Eq. (54): NG_inf <= 20: {min(dev_20):.2f} to {max(dev_20):.2f} dB; all: {min(dev_all):.2f} to {max(dev_all):.2f} dB")


# ---------------------------------------------------------------- Figure 10
def fig_scan_B(spice, stem):
    scan = load(spice, "cfscan")["B"]
    present = {f"{C_D*1e12:g} pF, {R_F/1e3:g} kOhm": C_F * 1e12 for part, R_F, C_D, C_F, label in DESIGNS if part == "OPA818"}
    fig, axs = plt.subplots(2, 2, figsize=(2 * PANEL[0], 2 * PANEL[1]), constrained_layout=True)
    for key, e in scan.items():
        col = CONFIG_COLORS[key]
        cf = np.array(e["cf_pF"])
        pm = np.min([_grid(e["grid"], f"{d:+.1f}", "pm_deg") for d in CF_DCD_pF], axis=0)
        pk = np.max([_grid(e["grid"], f"{d:+.1f}", "peak_dB") for d in CF_DCD_pF], axis=0)
        f3 = _grid(e["grid"], "+0.0", "f3_MHz")
        pms = np.min([np.array([np.nan if (r["pm_deg"] is None or not r["stable"]) else r["pm_deg"] for r in e["survey"][f"{d:+.1f}"]])
                      for d in CF_DCD_pF], axis=0)
        lab = config_label(key)
        stable = np.all([_stable(e["grid"], f"{d:+.1f}") for d in CF_DCD_pF], axis=0)
        pk = np.where(stable, pk, np.nan)
        axs[0, 0].plot(cf, pm, color=col, lw=LW, label=lab)
        axs[0, 0].plot(cf, pms, color=col, lw=LW, ls=DASH, label="_nolegend_")
        axs[0, 1].plot(cf, f3, color=col, lw=LW, label=lab)
        axs[1, 0].plot(cf, pk, color=col, lw=LW, label=lab)
        axs[1, 1].plot(pm, f3, color=col, lw=LW, label=lab)
        c0 = present[key]
        y0 = (np.interp(c0, cf, pm), np.interp(c0, cf, f3), np.interp(c0, cf, pk))
        axs[0, 0].plot([c0], [y0[0]], "o", ms=4.5, mfc="white", mew=1.0, color=col)
        axs[0, 1].plot([c0], [y0[1]], "o", ms=4.5, mfc="white", mew=1.0, color=col)
        axs[1, 0].plot([c0], [y0[2]], "o", ms=4.5, mfc="white", mew=1.0, color=col)
        axs[1, 1].plot([y0[0]], [y0[1]], "o", ms=4.5, mfc="white", mew=1.0, color=col)
        p = e["proposals"].get("40|0.05")
        if p:
            axs[0, 1].plot([p["centre_pF"]], [p["f3_nominal_MHz"]], "s", ms=4.0, color=col)
        print(f"Fig 10: B {key}: present {c0:.2f} pF -> worst PM {y0[0]:.1f}, f3 {y0[1]:.0f} MHz; "
              f"max survey worst PM {np.nanmax(pms):.1f}; f3 at 0.15 pF {f3[0]:.0f} MHz, peak {pk[0]:.1f} dB")
    for ax in axs.flat:
        if ax is not axs[1, 1]:
            ax.set_xlim(0.15, 0.8)
            ax.set_xlabel(r"Total feedback capacitance, $C_F$ (pF)")
    ax = axs[0, 0]
    for lev in (45, 40):
        ax.axhline(lev, color=COLORS["annotation"], lw=0.8, ls=DOT)
    ax.text(0.16, 45.6, "45°", ha="left", va="bottom", color=COLORS["annotation"])
    ax.text(0.16, 39.4, "40°", ha="left", va="top", color=COLORS["annotation"])
    ax.text(0.79, 20, "solid: SPICE\ndashed: analytical model", ha="right", va="top", color=COLORS["annotation"])
    ax.set_ylim(0, 60)
    ax.set_ylabel(r"Worst-case phase margin over $C_D$ ± 0.2 pF (°)")
    panel_label(ax, "(a)")
    ax = axs[0, 1]
    ax.axhline(150, color=COLORS["annotation"], lw=0.8, ls=DOT)
    ax.text(0.79, 155, "150 MHz", ha="right", va="bottom", color=COLORS["annotation"])
    ax.plot([], [], "o", ms=4.5, mfc="white", mew=1.0, color=COLORS["neutral"], label="present design")
    ax.plot([], [], "s", ms=4.0, color=COLORS["neutral"], label=r"40°, $C_F$ ± 0.05 pF")
    ax.set_ylim(100, 500)
    ax.set_ylabel(r"Bandwidth at nominal $C_D$, $f_{-3\,\mathrm{dB}}$ (MHz)")
    ax.legend(loc="upper right")
    panel_label(ax, "(b)")
    ax = axs[1, 0]
    ax.axhline(1, color=COLORS["annotation"], lw=0.8, ls=DOT)
    ax.set_ylim(0, 16)
    ax.set_ylabel(r"Largest peaking of $|Z_T|$ over $C_D$ ± 0.2 pF (dB)")
    panel_label(ax, "(c)")
    ax = axs[1, 1]
    for lev in (45, 40):
        ax.axvline(lev, color=COLORS["annotation"], lw=0.8, ls=DOT)
    ax.set_xlim(5, 50)
    ax.set_ylim(150, 450)
    ax.set_xlabel(r"Worst-case phase margin over $C_D$ ± 0.2 pF (°)")
    ax.set_ylabel(r"Bandwidth at nominal $C_D$, $f_{-3\,\mathrm{dB}}$ (MHz)")
    ax.text(0.03, 0.04, r"along each curve $C_F$ rises from" + "\nupper left to bottom right", transform=ax.transAxes,
            ha="left", va="bottom", color=COLORS["annotation"])
    panel_label(ax, "(d)")
    export(fig, stem)


# ---------------------------------------------------------------- Figure 11
NOISE_SET = (("OPA855", 0.25e-12), ("OPA818", 0.55e-12), ("LMH6629", 0.55e-12), ("OPA846", 0.75e-12))


def fig_noise(spice, stem):
    R_F, C_D = 2000.0, 1e-12
    fig, axs = plt.subplots(1, 2, figsize=(2 * PANEL[0], PANEL[1]), constrained_layout=True)
    ax = axs[0]
    for part, C_F in NOISE_SET:
        n = wrdata(spice / "runs" / "noise" / tag(part, R_F, C_D, C_F) / "noise.txt")
        col = PART_COLORS[part]
        name = {"OPA855": "OPA855 (A)", "OPA818": "OPA818 (B)"}.get(part, part)
        ax.plot(n[:, 0], n[:, 1] * 1e12, color=col, lw=LW, label=f"{name}, $C_F$ = {C_F*1e12:.2f} pF")
        fs = np.logspace(6, 9, 300)
        ax.plot(fs, survey_noise(part, R_F, C_D, C_F, fs) * 1e12, color=col, lw=LW, ls=DASH, label="_nolegend_")
        if "high" in noise_models_for(PARTS[VENDOR_MODELS[part]["db"]]):
            ax.fill_between(fs, survey_noise(part, R_F, C_D, C_F, fs) * 1e12,
                            survey_noise(part, R_F, C_D, C_F, fs, "high") * 1e12, color=col, alpha=0.18, lw=0)
    j = tm.johnson_current_asd(R_F) * 1e12
    ax.axhline(j, color=COLORS["neutral"], lw=LW, ls=DOT)
    ax.text(1.15e6, j * 0.93, rf"$R_F$ Johnson ({j:.2f})", color=COLORS["neutral"], va="top")
    ax.plot([], [], color=COLORS["neutral"], lw=LW, label="SPICE")
    ax.plot([], [], color=COLORS["neutral"], lw=LW, ls=DASH, label="analytical model, central estimate")
    ax.fill_between([], [], [], color=COLORS["neutral"], alpha=0.18, lw=0, label="analytical model, central to high (FET)")
    log_axes(ax)
    ax.yaxis.set_major_locator(FixedLocator([2, 3, 5, 10, 20, 30]))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:g}"))
    ax.set_xlim(1e6, 1e9)
    ax.set_ylim(2, 30)
    ax.set_xlabel(r"Frequency, $f$ (Hz)")
    ax.set_ylabel(r"Input-referred current noise (pA/$\sqrt{\mathrm{Hz}}$)")
    ax.legend(loc="upper left")
    panel_label(ax, "(a)", x=0.94)

    ax = axs[1]
    C_F = 0.55e-12
    n = wrdata(spice / "runs" / "noise" / tag("OPA818", R_F, C_D, C_F) / "noise.txt")
    fit = np.load(spice / "runs" / "params" / "OPA818_fit.npy")
    f, en, c_seen, i_n = fit
    C_tot = C_D + C_PCB_NOM + C_F + c_seen
    S = {"$R_F$ Johnson, $\\sqrt{4k_BT/R_F}$": np.full_like(f, 4 * KT / R_F),
         "$e_n/R_F$": (en / R_F) ** 2,
         "model current noise $i_n$ (fitted)": i_n ** 2,
         "$e_n\\,\\omega\\,C_{\\mathrm{tot}}$, $C_{\\mathrm{tot}}$ = 4.27 pF": (en * 2 * np.pi * f * C_tot) ** 2}
    cols = (COLORS["neutral"], COLORS["grey_accent"], COLORS["warm_accent"], COLORS["cool_accent"])
    ax.plot(n[:, 0], n[:, 1] * 1e12, color=COLORS["primary"], lw=LW, label="SPICE, total")
    ax.plot(f, np.sqrt(sum(S.values())) * 1e12, color=COLORS["text"], lw=LW, ls=DASH,
            label="Eq. (19) with the fitted terms")
    for (lab, v), c in zip(S.items(), cols):
        ax.plot(f, np.sqrt(v) * 1e12, color=c, lw=LW, ls=DOT if "Johnson" in lab or "e_n/R_F" in lab else "-", label=lab)
    pts = np.array(PARTS["OPA818"]["in_pts"])
    ax.plot(pts[:, 0], pts[:, 1] * 1e12, color=COLORS["warm_accent"], lw=LW, ls=DASH, marker="o", ms=2.5,
            label=r"datasheet $i_n$ curve")
    log_axes(ax)
    ax.yaxis.set_major_locator(FixedLocator([0.3, 1, 3, 10, 30]))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:g}"))
    ax.set_xlim(1e6, 1e9)
    ax.set_ylim(0.3, 40)
    ax.set_xlabel(r"Frequency, $f$ (Hz)")
    ax.set_ylabel(r"Noise density, input-referred (pA/$\sqrt{\mathrm{Hz}}$)")
    ax.legend(loc="upper left", fontsize=7.0)
    panel_label(ax, "(b)", x=0.94)
    export(fig, stem)
    k = int(np.argmin(np.abs(f - 1e8)))
    print(f"Fig 11: OPA818 at {f[k]/1e6:.0f} MHz: i_n {i_n[k]*1e12:.2f} pA, en*w*C {en[k]*2*np.pi*f[k]*C_tot[k]*1e12:.2f} pA, "
          f"sum {np.sqrt(sum(v[k] for v in S.values()))*1e12:.2f} pA; C_tot {C_tot[k]*1e12:.2f} pF")


# ---------------------------------------------------------------- Figure 12
LABEL_OFFSETS = {  # (dx, dy) in points and alignment, for (a) and (b)
    "OPA855": ((6, -10, "left"), (6, -10, "left")), "OPA818": ((6, -9, "left"), (6, 4, "left")),
    "OPA856": ((6, 2, "left"), (-6, 9, "right")), "LMH6629": ((6, -9, "left"), (6, -9, "left")),
    "OPA858": ((6, 3, "left"), (-2, -11, "center")), "OPA859": ((6, 2, "left"), (-7, 0, "right")),
    "OPA846": ((6, 2, "left"), (-7, 0, "right"))}


def fig_comparison(spice, stem):
    loop, zt, noise = load(spice, "loop"), load(spice, "zt"), load(spice, "noise")
    rows = []
    for part, R_F, C_D, C_F, label in DESIGNS:
        if R_F != 2000.0 or C_D != 1e-12 or part not in LABEL_OFFSETS:   # the original seven; Figure 14 has all
            continue
        key = f"{part}|{label}"
        cs = loop[key]["corners"]
        rows.append(dict(part=part, C_F=C_F,
                         pm=loop[key]["spice_worst_pm"], pm_s=min(c["analytical_datasheet"]["pm_deg"] for c in cs.values()),
                         f3=zt[key]["spice"]["f3_MHz"], f3_s=zt[key]["analytical"]["f3_MHz"],
                         pen=noise[key]["spice_penalty_10_150_dB"], pen_s=survey_penalty(part, R_F, C_D, C_F)))
    fig, axs = plt.subplots(1, 2, figsize=(2 * PANEL[0], PANEL[1]), constrained_layout=True)
    for j, (ax, xs, xsv) in enumerate(zip(axs, ("pm", "f3"), ("pm_s", "f3_s"))):
        for r in rows:
            col = PART_COLORS[r["part"]]
            ax.plot([r[xsv], r[xs]], [r["pen_s"][0], r["pen"]], color=COLORS["annotation"], lw=0.6, zorder=1)
            if len(r["pen_s"]) > 1:
                ax.plot([r[xsv]] * 2, r["pen_s"], color=col, lw=1.0, zorder=1)
            ax.plot([r[xsv]], [r["pen_s"][0]], "o", ms=5, mfc="white", mew=1.0, color=col, zorder=2)
            ax.plot([r[xs]], [r["pen"]], "o", ms=5, color=col, zorder=3)
            name = {"OPA855": "OPA855 (A)", "OPA818": "OPA818 (B)"}.get(r["part"], r["part"])
            dx, dy, ha = LABEL_OFFSETS[r["part"]][j]
            ax.annotate(name, xy=(r[xs], r["pen"]), xytext=(dx, dy), textcoords="offset points",
                        color=COLORS["text"], va="center", ha=ha)
        ax.set_ylabel(r"Noise above $R_F$ Johnson floor, 10–150 MHz (dB)")
        ax.set_ylim(2, 9)
    ax = axs[0]
    ax.axvline(45, color=COLORS["annotation"], lw=0.8, ls=DOT)
    ax.set_xlim(25, 60)
    ax.set_xlabel(r"Worst-case phase margin, $C_F$ ± 0.1 pF and $C_D$ ± 0.2 pF (°)")
    ax.plot([], [], "o", ms=5, color=COLORS["neutral"], label="SPICE")
    ax.plot([], [], "o", ms=5, mfc="white", mew=1.0, color=COLORS["neutral"], label="analytical model")
    ax.plot([], [], color=COLORS["neutral"], lw=1.0, label="up to the high estimate (FET)")
    ax.legend(loc="upper left")
    panel_label(ax, "(a)", x=0.92)
    ax = axs[1]
    ax.axvspan(70, 150, color=COLORS["grey_accent"], alpha=0.12, lw=0, zorder=0)
    ax.text(110, 8.8, "< 150\nMHz", ha="center", va="top", color=COLORS["annotation"])
    ax.set_xlim(70, 560)
    ax.set_xlabel(r"Bandwidth, nominal design, $f_{-3\,\mathrm{dB}}$ (MHz)")
    panel_label(ax, "(b)", x=0.92)
    export(fig, stem)
    for r in rows:
        print(f"Fig 12: {r['part']}: worst PM {r['pm']:.1f} (survey {r['pm_s']:.1f}); f3 {r['f3']:.0f} (survey {r['f3_s']:.0f}) MHz; "
              f"penalty {r['pen']:.2f} (survey {', '.join(f'{x:.2f}' for x in r['pen_s'])}) dB")


# ---------------------------------------------------------------- Figure 13
def fig_bench(spice, stem):
    b = BENCH
    part, R_F, C_F = b["part"], b["R_F"], b["C_F"]
    p = PARTS[VENDOR_MODELS[part]["db"]]
    ol, *_ = open_loop_model(p)
    nz = noise_inputs(p)
    cols = (COLORS["primary"], COLORS["cool_accent"], COLORS["warm_accent"], COLORS["purple_accent"])
    fig, axs = plt.subplots(1, 2, figsize=(2 * PANEL[0], PANEL[1]), constrained_layout=True)
    fs = np.logspace(6, 9, 400)
    for C_T, col in zip(b["C_T"], cols):
        name = f"{part}_R{R_F/1e3:g}k_CT{C_T*1e12:g}p_F{C_F*1e12:.2f}p".replace(".", "p")
        z = wrdata(spice / "runs" / "bench" / f"{name}_zt_noise" / "zt.txt")
        n = wrdata(spice / "runs" / "bench" / f"{name}_zt_noise" / "noise.txt")
        lab = rf"$C_T$ = {C_T*1e12:g} pF"
        axs[0].plot(z[:, 0], db(z[:, 1] + 1j * z[:, 2]), color=col, lw=LW, label=lab)
        axs[1].plot(n[:, 0], n[:, 1] * 1e12, color=col, lw=LW, label=lab)
    C_T, col = 14e-12, cols[2]
    Z, _, _ = tm.tia_tf(fs, ol, R_F, C_T, C_F)
    axs[0].plot(fs, db(Z), color=col, lw=LW, ls=DASH, label="analytical model, 14 pF")
    S = tm.noise_components(fs, R_F, C_T, C_F, nz)["total"]
    axs[1].plot(fs, np.sqrt(S) * 1e12, color=col, lw=LW, ls=DASH, label="analytical model, 14 pF")
    for ax, y, txt in ((axs[0], 20 * np.log10(b["zt_meas"]), "bench: 1.45 kΩ"), (axs[1], b["noise_meas_pA"], "bench: about 7 pA/√Hz")):
        ax.plot([b["f_meas"]], [y], "D", ms=5, color=COLORS["text"], zorder=5, label=txt)
        ax.set_xlabel(r"Frequency, $f$ (Hz)")
    ax = axs[0]
    log_x(ax, 1e6, 1e9)
    ax.set_ylim(55, 94)
    ax.set_ylabel(r"Transimpedance, $|Z_T|$ (dB$\Omega$)")
    ax.legend(loc="upper left")
    panel_label(ax, "(a)", x=0.92)
    ax = axs[1]
    log_axes(ax)
    ax.yaxis.set_major_locator(FixedLocator([3, 5, 7, 10, 20, 30]))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:g}"))
    ax.set_xlim(1e6, 1e9)
    ax.set_ylim(3, 40)
    ax.set_ylabel(r"Input-referred current noise (pA/$\sqrt{\mathrm{Hz}}$)")
    ax.legend(loc="upper left")
    panel_label(ax, "(b)", x=0.92, y=0.08)
    export(fig, stem)
    print("Fig 13: bench board drawn for C_T =", ", ".join(f"{c*1e12:g}" for c in b["C_T"]), "pF")


# ---------------------------------------------------------------- Figure 14
SCAN_LABEL_OFFSETS = {   # part: ((dx, dy, ha) for (a), (dx, dy, ha) for (b)), points
    "OPA855": ((-7, 0, "right"), (0, -10, "center")), "OPA846": ((-7, 0, "right"), (-7, 0, "right")),
    "ADA4899-1": ((-7, 0, "right"), (-7, -4, "right")), "LMH6624": ((-7, 0, "right"), (6, 0, "left")),
    "THS4021": ((0, 9, "center"), (0, -10, "center")), "OPA856": ((6, 0, "left"), (-2, 9, "right")),
    "OPA859": ((6, 0, "left"), (-7, 0, "right")), "ADA4817-1": ((6, 0, "left"), (-7, 0, "right")),
    "OPA847": ((6, 0, "left"), (6, 4, "left")), "ADA4895-1": ((6, 0, "left"), (-7, 0, "right")),
    "LMH6629": ((6, -2, "left"), (6, 0, "left")),
    "OPA955": ((-7, 0, "right"), (6, 0, "left")), "OPA817": ((6, 0, "left"), (-7, 0, "right")),
    "OPA814": ((-7, 0, "right"), (-7, 0, "right")),
}
PEN_MAX = 15.5             # dB; a part above it is drawn at the top edge with its value


def fig_all_parts(spice, stem):
    """Every part at its best design in SPICE (check 'pscan'): noise penalty against
    bandwidth and against the largest worst-case phase margin the part reaches."""
    scan = load(spice, "pscan")
    fig, axs = plt.subplots(1, 2, figsize=(2 * PANEL[0], PANEL[1] + 1.0), constrained_layout=True)
    for part, e in scan.items():
        d = e["design"]
        fet = bool(datasheet(part).get("fet"))
        col = COLORS["warm_accent"] if fet else COLORS["primary"]
        mk = "s" if fet else "o"
        robust = d["kind"].startswith("robust")
        face = col if d.get("tol_pF", 0) >= 0.05 else "white"   # robust over C_F +/- 0.05 pF
        pen = d["noise"]["penalty_dB"]
        off = pen > PEN_MAX
        y = PEN_MAX - 0.35 if off else pen
        for j, (ax, x) in enumerate(zip(axs, (d["f3_nominal_MHz"], e["best_pm"]["worst_pm"]))):
            ax.plot([x], [y], "^" if off else mk, ms=5.5, mfc=face, mew=1.0, color=col, zorder=3)
            name = part if robust or j == 1 else f"{part} ({d['worst_pm']:.0f}°)"
            if off:
                name += f": {pen:.1f} dB, off scale"
            dx, dy, ha = SCAN_LABEL_OFFSETS.get(part, ((6, 0, "left"), (6, 0, "left")))[j]
            ax.annotate(name, xy=(x, y), xytext=(dx, dy), textcoords="offset points", color=COLORS["text"],
                        va="center", ha=ha)
        print(f"Fig 14: {part}: {d['kind']}, C_F {d['cf_pF']:.2f} pF, worst PM {d['worst_pm']:.1f}, f3 "
              f"{d['f3_nominal_MHz'] and round(d['f3_nominal_MHz'])} MHz, penalty {pen:.2f} dB; best worst-case PM "
              f"{e['best_pm']['worst_pm']:.1f} at {e['best_pm']['cf_pF']:.2f} pF")
    for lab, mk, col, face in (("bipolar input", "o", COLORS["primary"], COLORS["primary"]),
                               ("FET input", "s", COLORS["warm_accent"], COLORS["warm_accent"]),
                               ("robust: PM ≥ 45°, GM ≥ 3 dB, peaking ≤ 1 dB\n"
                                "at $C_D$ = 0.8–1.2 pF and $C_F$ ± 0.05 pF", "o", COLORS["neutral"], COLORS["neutral"]),
                               ("no $C_F$ meets them: shown at the $C_F$ of\n"
                                "largest worst-case PM (value in brackets)", "o", COLORS["neutral"], "white")):
        axs[0].plot([], [], mk, ms=5, mfc=face, mew=1.0, color=col, label=lab)
    fig.legend(*axs[0].get_legend_handles_labels(), loc="outside lower center", ncol=2)
    axs[0].axvspan(0, 150, color=COLORS["grey_accent"], alpha=0.12, lw=0, zorder=0)
    axs[0].text(75, 0.3, "< 150 MHz", ha="center", va="bottom", color=COLORS["annotation"])
    axs[0].set_xlim(0, 580)
    axs[0].set_xlabel(r"Bandwidth at the design, nominal $C_D$, $f_{-3\,\mathrm{dB}}$ (MHz)")
    axs[1].axvline(45, color=COLORS["annotation"], lw=0.8, ls=DOT)
    axs[1].set_xlim(15, 78)
    axs[1].set_xlabel(r"Largest worst-case phase margin over $C_F$, $C_D$ ± 0.2 pF (°)")
    for ax, lab in zip(axs, "ab"):
        ax.set_ylim(0, PEN_MAX)
        ax.set_ylabel(r"Noise above $R_F$ Johnson floor, 10–150 MHz (dB)")
        panel_label(ax, f"({lab})", x=0.94 if lab == "a" else 0.025)
    export(fig, stem)


# ---------------------------------------------------------------- Figure 15
DR_COLORS = {"OPA855": COLORS["primary"], "OPA955": COLORS["cool_accent"], "OPA818": COLORS["warm_accent"],
             "LMH6629": COLORS["purple_accent"], "OPA858": COLORS["teal_accent"]}
TIA_STYLE = [(c, ls) for ls in ("-", DASH) for c in (COLORS["primary"], COLORS["warm_accent"], COLORS["cool_accent"],
                                                     COLORS["purple_accent"], COLORS["teal_accent"],
                                                     COLORS["brown_accent"])]
I_RANGE_mA = (0.1, 10.0)        # the receiver's range of I1 + I2, highlighted
DR_NOT_COUNTED = ("LMH6629",)   # its SPICE gain is not counted (input capacitance, Section 11.2)


def _dr_idc_axes(ax):
    log_axes(ax, x=True, y=False)
    ax.set_xlim(1e-3, 20)
    ax.axvspan(*I_RANGE_mA, color=COLORS["highlight"], alpha=0.24, lw=0, label="_nolegend_", zorder=0)
    ax.set_xlabel(r"DC photocurrent, $I_1 + I_2$ (mA)")
    ax.set_ylabel("Dynamic range, 100-MHz tone (dB)")


def _dr_f0_axes(ax, i_dc_mA):
    ax.set_xlim(20, 200)
    ax.set_xlabel(r"Tone frequency, $f_0$ (MHz)")
    ax.set_ylabel(rf"Dynamic range at $I_1 + I_2$ = {i_dc_mA:g} mA (dB)")


def _idc_curve(d):
    return np.array(d["i_dc_A"]) * 1e3, np.array(d["dr_dB"])


def _f0_curve(rows):
    return np.array([x["f0_MHz"] for x in rows]), np.array([x["dr_dB"] for x in rows])


def fig_dynamic_range(spice, stem):
    """Dynamic range (Eq. (25), 150 MHz) of the leading op-amp TIAs, SPICE and survey model,
    and of single-chip TIAs from their datasheets (dr_comparison.py)."""
    r = load(spice, "dr_comparison")
    ops = r["op_amps"]
    tias = {k: v for k, v in r.get("tias", {}).items() if v["record"].get("plotted", True)}
    i_fix = r["definition"]["i_dc_fixed_mA"]
    rows = 2 if tias else 1
    fig, axs = plt.subplots(rows, 2, figsize=(2 * PANEL[0], rows * PANEL[1] + 0.3), constrained_layout=True,
                            squeeze=False)
    # (a) against the photocurrent, 100-MHz tone
    ax = axs[0, 0]
    for part, e in ops.items():
        for k, ls in (("spice", "-"), ("survey", DASH)):
            ax.plot(*_idc_curve(e[k]["vs_idc"]), color=DR_COLORS.get(part, COLORS["neutral"]), lw=LW, ls=ls,
                    label=part if k == "spice" else "_nolegend_")
    ax.plot([], [], color=COLORS["neutral"], lw=LW, label="SPICE, best design")
    ax.plot([], [], color=COLORS["neutral"], lw=LW, ls=DASH, label=r"analytical model, same $C_F$")
    _dr_idc_axes(ax)
    ax.set_ylim(50, 86)
    ax.legend(loc="lower left", ncol=2)
    panel_label(ax, "(a)", x=0.92)
    # (b) against the tone frequency at a fixed photocurrent
    ax = axs[0, 1]
    for part, e in ops.items():
        for k, ls in (("spice", "-"), ("survey", DASH)):
            ax.plot(*_f0_curve(e[k]["vs_f0"]), color=DR_COLORS.get(part, COLORS["neutral"]), lw=LW, ls=ls,
                    label="_nolegend_")
    _dr_f0_axes(ax, i_fix)
    lead = dict(arrowstyle="-", color=COLORS["annotation"], lw=0.6)
    f, y = _f0_curve(ops["OPA818"]["spice"]["vs_f0"])
    f_sr = ops["OPA818"]["f_swing_to_slew_MHz"]
    ax.annotate(f"OPA818: slew rate limits\nabove {f_sr:.3g} MHz", xy=(70, np.interp(70, f, y)), xytext=(95, 76.6),
                va="center", color=COLORS["text"], arrowprops=lead)
    f, y = _f0_curve(ops["LMH6629"]["spice"]["vs_f0"])
    f_sr = ops["LMH6629"]["f_swing_to_slew_MHz"]
    ax.annotate(f"LMH6629: slew rate limits\nabove {f_sr:.3g} MHz", xy=(178, np.interp(178, f, y)),
                xytext=(118, 72.3), va="center", color=COLORS["text"], arrowprops=lead)
    v_sw = ops["OPA855"]["spice"]["vs_f0"][0]["v_pk_V"]
    ax.text(23, 67.2, f"OPA855, OPA955, OPA858:\nswing limits ({v_sw:.2f} V) at every tone", va="top",
            color=COLORS["text"])
    panel_label(ax, "(b)", x=0.92)
    if tias:
        # (c), (d): the single-chip TIAs against the best of the op-amp designs above (SPICE)
        ref = [p for p in ops if p not in DR_NOT_COUNTED]
        env_idc = np.max([_idc_curve(ops[p]["spice"]["vs_idc"])[1] for p in ref], axis=0)
        env_f0 = np.max([_f0_curve(ops[p]["spice"]["vs_f0"])[1] for p in ref], axis=0)
        x_idc = _idc_curve(next(iter(ops.values()))["spice"]["vs_idc"])[0]
        x_f0 = _f0_curve(next(iter(ops.values()))["spice"]["vs_f0"])[0]
        for j, ax in enumerate((axs[1, 0], axs[1, 1])):
            ax.plot(*((x_idc, env_idc) if j == 0 else (x_f0, env_f0)), color=COLORS["neutral"], lw=LW, ls=DASH,
                    label=f"best of {', '.join(ref)} (SPICE)" if j == 0 else "_nolegend_")
            for i, (name, e) in enumerate(tias.items()):
                col, ls = TIA_STYLE[i % len(TIA_STYLE)]
                x, y = _idc_curve(e["vs_idc"]) if j == 0 else _f0_curve(e["vs_f0"])
                ax.plot(x, y, color=col, lw=LW, ls=ls, label=e.get("label", name) if j == 0 else "_nolegend_")
        _dr_idc_axes(axs[1, 0])
        _dr_f0_axes(axs[1, 1], i_fix)
        panel_label(axs[1, 0], "(c)", x=0.92)
        panel_label(axs[1, 1], "(d)", x=0.92)
        h, l = axs[1, 0].get_legend_handles_labels()
        fig.legend(h, l, loc="outside lower center", ncol=3)
    export(fig, stem)
    for part, e in ops.items():
        print(f"Fig 15: {part}: " + " | ".join(f"{k} " + ", ".join(f"{kk} {v:.1f}" for kk, v in e[k]["dr_at_dB"].items())
                                              for k in ("spice", "survey")))
    for name, e in tias.items():
        print(f"Fig 15: {name}: " + ", ".join(f"{kk} {v:.1f}" if v is not None else f"{kk} -"
                                              for kk, v in e["dr_at_dB"].items())
              + (f" (curve ends at {e['dc_limit']['i_dc_max_mA']:g} mA, {e['dc_limit']['dr_dB']:.1f} dB)"
                 if "dc_limit" in e else ""))


# ---------------------------------------------------------------- Figure 16
LIMIT_STYLE = {"swing, ±6.5 V": (COLORS["warm_accent"], "-", "swing on ±6.5 V (5.50 V)"),
               "swing, ±5 V": (COLORS["warm_accent"], DASH, "swing on ±5 V (4.00 V)"),
               "swing, 5-V parts": (COLORS["primary"], DASH, "swing of the 5-V parts (1.52 V)"),
               "slew rate, 2800 V/µs": (COLORS["purple_accent"], DASH, "slew rate 2800 V/µs"),
               "slew rate, 1400 V/µs": (COLORS["purple_accent"], "-", "slew rate 1400 V/µs (OPA818)"),
               "slew rate, 700 V/µs": (COLORS["brown_accent"], DASH, "slew rate 700 V/µs")}


def _dr_arrow(ax, x, lo, hi, text, side="left"):
    """A double arrow from the noise floor to the ceiling, labelled with their ratio in dB."""
    ax.annotate("", xy=(x, hi), xytext=(x, lo),
                arrowprops=dict(arrowstyle="<->", color=COLORS["text"], lw=0.8, shrinkA=0, shrinkB=0))
    ax.text(x * (0.92 if side == "left" else 1.09), np.sqrt(lo * hi), text, ha="right" if side == "left" else "left",
            va="center", color=COLORS["text"])


def fig_dr_limits(spice, stem):
    """What sets the dynamic range of one design (dr_comparison.py, 'limits_example'): the band noise
    floors and the large-signal ceilings, as rms input current, against the tone and against I1 + I2."""
    lim = load(spice, "dr_comparison")["limits_example"]
    fl, a, b = lim["floors_nA"], lim["vs_f0"], lim["vs_idc"]
    fig, axs = plt.subplots(1, 2, figsize=(2 * PANEL[0], PANEL[1] + 0.9), constrained_layout=True, sharey=True)
    # (a) against the tone frequency
    ax = axs[0]
    f = np.array(a["f0_MHz"])
    ceil = {k: np.array(v) for k, v in a["ceilings_nA"].items()}
    tot = fl["total_spice"]
    ax.fill_between(f, tot["1 mA"], ceil["OPA818 on ±6.5 V"], color=COLORS["highlight"], alpha=0.24, lw=0, zorder=0)
    for k, (c, ls, _) in LIMIT_STYLE.items():
        ax.plot(f, ceil[k], color=c, lw=LW, ls=ls)
    floors = [("dark", fl["amp_spice"], "top")] + [(rf"$I_1 + I_2$ = {k}", v, "bottom") for k, v in tot.items()]
    for text, y, va in floors:
        ax.axhline(y, color=COLORS["cool_accent"], lw=LW)
        ax.text(10.6, y * (0.86 if va == "top" else 1.14), text, va=va, color=COLORS["text"])
    ax.axhline(fl["johnson"], color=COLORS["grey_accent"], lw=LW, ls=DASH)
    ax.axvline(lim["B_MHz"], color=COLORS["annotation"], lw=0.8, ls=DOT)
    ax.text(lim["B_MHz"] * 1.04, 3e3, "noise band\nedge", ha="left", va="bottom", color=COLORS["annotation"])
    for x, side in ((30.0, "right"), (lim["f0_MHz"], "left")):
        hi = float(np.interp(np.log10(x), np.log10(f), ceil["OPA818 on ±6.5 V"]))
        _dr_arrow(ax, x, tot["1 mA"], hi, f"{20 * np.log10(hi / tot['1 mA']):.1f} dB", side)
    log_axes(ax, x=True, y=True)
    ax.set_xlim(10, 300)
    ax.set_ylim(10, 1e7)
    ax.xaxis.set_major_locator(FixedLocator([10, 20, 50, 100, 200, 300]))
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:g}"))
    ax.set_xlabel(r"Tone frequency, $f_0$ (MHz)")
    ax.set_ylabel("Input current, rms (nA)")
    panel_label(ax, "(a)", x=0.93, y=0.07)
    # (b) against the photocurrent, 100-MHz tone
    ax = axs[1]
    i_ma = np.array(b["i_dc_A"]) * 1e3
    tot_sp = np.array(b["total_spice_nA"])
    act = lim["ceiling_100MHz"]["i_rms_nA"]
    ax.fill_between(i_ma, tot_sp, act, color=COLORS["highlight"], alpha=0.24, lw=0, zorder=0)
    for k, (c, ls, _) in LIMIT_STYLE.items():
        ax.axhline(b["ceilings_100MHz_nA"][k], color=c, lw=LW, ls=ls)
    ax.plot(i_ma, tot_sp, color=COLORS["cool_accent"], lw=LW)
    ax.plot(i_ma, b["total_survey_nA"], color=COLORS["cool_accent"], lw=LW, ls=DASH)
    ax.plot(i_ma, b["shot_nA"], color=COLORS["teal_accent"], lw=LW, ls=DASH)
    ax.axhline(fl["johnson"], color=COLORS["grey_accent"], lw=LW, ls=DASH)
    for x, side in ((2e-3, "right"), (0.1, "left"), (10.0, "left")):
        lo = float(np.interp(np.log10(x), np.log10(i_ma), tot_sp))
        _dr_arrow(ax, x, lo, act, f"{20 * np.log10(act / lo):.1f} dB", side)
    log_axes(ax, x=True, y=False)
    ax.set_xlim(1e-3, 20)
    ax.set_xlabel(r"DC photocurrent, $I_1 + I_2$ (mA), 100-MHz tone")
    panel_label(ax, "(b)", x=0.93, y=0.07)
    # one legend for both panels
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    h = [Line2D([], [], color=c, lw=LW, ls=ls, label=lab) for c, ls, lab in LIMIT_STYLE.values()]
    h += [Line2D([], [], color=COLORS["cool_accent"], lw=LW, label="total noise, SPICE"),
          Line2D([], [], color=COLORS["cool_accent"], lw=LW, ls=DASH, label="total noise, analytical model"),
          Line2D([], [], color=COLORS["teal_accent"], lw=LW, ls=DASH, label=r"shot noise, $\sqrt{2qI_{\mathrm{DC}}B}$"),
          Line2D([], [], color=COLORS["grey_accent"], lw=LW, ls=DASH, label=r"Johnson noise of $R_F$ alone"),
          Patch(color=COLORS["highlight"], alpha=0.24, lw=0, label="dynamic range of OPA818 on ±6.5 V")]
    fig.legend(handles=h, loc="outside lower center", ncol=4)
    export(fig, stem)
    print(f"Fig 16: {lim['part']} at C_F {lim['cf_pF']:.3f} pF: floors R_F {fl['johnson']:.1f}, amplifier + R_F "
          f"{fl['amp_spice']:.1f} (survey {fl['amp_survey']:.1f}), totals " +
          ", ".join(f"{k} {v:.0f}" for k, v in tot.items()) + " nA rms; ceiling at 100 MHz "
          f"{act / 1e3:.0f} uA rms; DR " + ", ".join(f"{k} {v:.1f}" for k, v in lim["dr_100MHz_dB"].items()) + " dB")


FIGURES = {7: (fig_hidden_margin, "fig07_spice_loop_gain_hidden_margin"),
           8: (fig_open_loop, "fig08_spice_open_loop_gain"),
           9: (fig_scan_A, "fig09_spice_cf_scan_variant_A"),
           10: (fig_scan_B, "fig10_spice_cf_scan_variant_B"),
           11: (fig_noise, "fig11_spice_noise"),
           12: (fig_comparison, "fig12_spice_noise_vs_margin_bandwidth"),
           13: (fig_bench, "fig13_spice_bench_board"),
           14: (fig_all_parts, "fig14_spice_best_design_all_parts"),
           15: (fig_dynamic_range, "fig15_dynamic_range_comparison"),
           16: (fig_dr_limits, "fig16_dynamic_range_limits_opa818")}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--spice", type=Path, default=HERE.parent / "spice", help="folder with results/ and runs/")
    ap.add_argument("--out", type=Path, default=HERE.parent / "figures", help="output folder")
    ap.add_argument("--only", type=int, nargs="*", help="figure numbers to draw (default: all)")
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    configure_plot_style()
    for k, (fn, name) in FIGURES.items():
        if a.only and k not in a.only:
            continue
        fn(a.spice, a.out / name)


if __name__ == "__main__":
    main()
