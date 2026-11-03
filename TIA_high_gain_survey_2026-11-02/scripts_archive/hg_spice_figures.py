"""Figures 17-23 of the high-gain TIA note: the SPICE checks (ngspice and LTspice) against
the analytic model, and the closed-form approximations against the exact model.

    Fig. 17   parity plots: bandwidth and excess noise, SPICE against the analytic model
    Fig. 18   input-referred noise spectra, SPICE against the analytic model, four designs
    Fig. 19   the macromodels' own voltage noise against the datasheet values
    Fig. 20   distributed feedback resistor in a loop: transimpedance and step response
    Fig. 21  discrete-JFET composite against the monolithic op amp, input-referred noise
    Fig. 22  logarithmic amplifiers: output law, bandwidth and noise against current
    Fig. 23  the closed forms of Chapter 3 against the full model

Reads spice/results/*.json and the saved arrays in spice/runs/; writes figures/.
Usage:  python hg_spice_figures.py
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import hg_model as m
from hg_figures import (COLORS, CYCLE, DASH, LW, FONT_SIZE, configure_plot_style, export, log_axes)

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "spice" / "results"
RUNS = ROOT / "spice" / "runs"
PART_COLOR = {"OPA928": COLORS["primary"], "OPA140": COLORS["warm_accent"], "OPA828": COLORS["cool_accent"],
              "OPA320": COLORS["purple_accent"], "OPA818": COLORS["teal_accent"], "OPA657": COLORS["brown_accent"],
              "ADA4817-1": COLORS["grey_accent"], "ADA4530-1": "#1F3A6B", "ADA4625-1": "#C26A3F",
              "LTC6268-10": "#2E5E3E", "OPA1656": "#B8860B", "OPA2156": "#7A4A8C"}


def load(name: str) -> dict:
    return json.loads((RES / f"{name}.json").read_text())


# ------------------------------------------------------------------ Fig. 17
def fig_parity() -> None:
    sweep = {(r["amp"], r["rf"], r["source"].split(" ")[0]): r
             for r in json.loads((m.DATA / "results" / "designs.json").read_text())}
    rows = load("designs")["designs"] + load("lt_designs")["designs"]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 3.4), constrained_layout=True)
    for r in rows:
        flag = sweep[(r["part"], r["rf"], r["source"])]["a0_over_ng"] < 10
        kw = dict(color=PART_COLOR[r["part"]], ms=4, mfc="white" if flag else PART_COLOR[r["part"]],
                  marker="s" if r.get("engine") == "LTspice" else "o", ls="none")
        ax1.plot(r["f3_model"], r["f3_spice"], **kw)
        ax2.plot(r["dN_model"], r["dN_spice"], **kw)
    for ax, lo, hi in ((ax1, 1e2, 3e7), (ax2, 0, 36)):
        ax.plot([lo, hi], [lo, hi], color=COLORS["neutral"], lw=0.8, ls=DASH)
        ax.set_xlim(lo, hi); ax.set_ylim(lo, hi)
    ax1.set_xscale("log"); ax1.set_yscale("log"); log_axes(ax1)
    ax1.set_xlabel(r"$f_{-3\,\mathrm{dB}}$, analytic model (Hz)")
    ax1.set_ylabel(r"$f_{-3\,\mathrm{dB}}$, SPICE (Hz)")
    ax2.set_xlabel(r"$\Delta N$, analytic model (dB)")
    ax2.set_ylabel(r"$\Delta N$, SPICE (dB)")
    handles = [plt.Line2D([], [], color=c, marker="o", ls="none", ms=4, label=p) for p, c in PART_COLOR.items()]
    handles += [plt.Line2D([], [], color=COLORS["neutral"], marker="s", ls="none", ms=4, label="LTspice (squares)"),
                plt.Line2D([], [], color=COLORS["neutral"], marker="o", ls="none", ms=4, mfc="white",
                           label=r"open: $A_0 < 10\,NG$")]
    fig.legend(handles=handles, loc="outside right center", fontsize=FONT_SIZE - 0.5)
    export(fig, "fig6_spice_parity")


# ------------------------------------------------------------------ Fig. 18
def fig_spectra() -> None:
    cases = [("designs", "OPA140_S1336-18BK_1e+09", "OPA140, 1 G$\\Omega$, 20 pF"),
             ("lt_designs", "ADA4625-1_S1336-8BK_1e+06", "ADA4625-1, 1 M$\\Omega$, 380 pF"),
             ("designs", "OPA818_S1336-18BK_1e+07", "OPA818, 10 M$\\Omega$, 20 pF"),
             ("designs", "OPA657_S1336-8BK_1e+08", "OPA657, 100 M$\\Omega$, 380 pF")]
    fig, axes = plt.subplots(2, 2, figsize=(7.0, 5.0), constrained_layout=True)
    for ax, (check, case, title) in zip(axes.ravel(), cases):
        d = np.load(RUNS / check / case / "compare.npy")
        f, s_sp, s_mo, z_sp, z_mo = d
        ax.plot(f, s_sp, color=COLORS["primary"], lw=LW, label="SPICE, input noise")
        ax.plot(f, s_mo, color=COLORS["warm_accent"], lw=LW, ls=DASH, label="model, input noise")
        ax2 = ax.twinx()
        ax2.plot(f, z_sp / z_sp[0], color=COLORS["cool_accent"], lw=1.0, label=r"SPICE, $|Z_T|/|Z_T(0)|$")
        ax2.plot(f, z_mo / z_mo[0], color=COLORS["grey_accent"], lw=1.0, ls=DASH, label=r"model, $|Z_T|/|Z_T(0)|$")
        for a in (ax, ax2):
            a.set_xscale("log"); a.set_yscale("log")
        ax2.set_ylim(1e-3, 3)
        log_axes(ax); log_axes(ax2, x=False)
        ax.set_xlim(0.1, 1e8)
        ax.set_title(title)
        ax.set_xlabel("Frequency (Hz)")
        ax.set_ylabel(r"A/$\sqrt{\mathrm{Hz}}$")
        ax2.set_ylabel(r"$|Z_T|/|Z_T(0)|$")
        if ax is axes[0, 0]:
            h1, l1 = ax.get_legend_handles_labels()
            h2, l2 = ax2.get_legend_handles_labels()
            ax.legend(h1 + h2, l1 + l2, loc="upper left", fontsize=FONT_SIZE - 1)
    export(fig, "fig7_spice_spectra")


# ------------------------------------------------------------------ Fig. 19
def fig_models() -> None:
    ng = load("models")["models"]
    lt = load("lt_models")["models"]
    amps = m.load_amps()
    fig, ax = plt.subplots(figsize=(4.6, 3.6), constrained_layout=True)
    for part, res in list(ng.items()) + list(lt.items()):
        f = np.array(res["en"]["f"])
        e = np.array(res["en"]["inoise"])
        sel = (f >= 1) & (f <= 1e7)
        ax.plot(f[sel], e[sel] * 1e9, color=PART_COLOR[part], lw=1.2, label=part)
        pts = sorted(amps[part].en_pts)
        if len(pts) <= 6:
            ax.plot([p[0] for p in pts], [p[1] * 1e9 for p in pts], "o", color=PART_COLOR[part], ms=4, mfc="white")
    ax.set_xscale("log"); ax.set_yscale("log"); log_axes(ax)
    ax.set_xlim(1, 1e7); ax.set_ylim(1, 1000)
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel(r"$e_n$ (nV/$\sqrt{\mathrm{Hz}}$)")
    ax.legend(loc="upper right", fontsize=FONT_SIZE - 1, ncol=2)
    ax.text(0.02, 0.03, "lines: macromodels; circles: datasheet values", transform=ax.transAxes,
            fontsize=FONT_SIZE - 0.5)
    export(fig, "fig8_macromodel_noise")


# ------------------------------------------------------------------ Fig. 20
def fig_distributed() -> None:
    res = load("distributed")["distributed"]
    labels = ["lumped (no plane)", "plane at ground", "plane at output", "plane at 1/3 output",
              "four strips, graded", "ideal graded guard"]
    colors = [COLORS["neutral"], COLORS["warm_accent"], COLORS["purple_accent"], COLORS["cool_accent"],
              COLORS["teal_accent"], COLORS["primary"]]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 3.3), constrained_layout=True)
    for lab, col in zip(labels, colors):
        case = "OPA140_" + lab.replace(" ", "_").replace("/", "")
        f, zs, za, _, _ = np.load(RUNS / "distributed" / case / "compare.npy")
        ax1.plot(f, 20 * np.log10(zs / 1e9), color=col, lw=LW, label=lab)
        ax1.plot(f, 20 * np.log10(za / 1e9), color=col, lw=0.9, ls=DASH)
        t, v = np.load(RUNS / "distributed" / case / "step.npy")
        ax2.plot((t - 0.5e-3) * 1e3, -v / 0.1, color=col, lw=LW)
    ax1.set_xscale("log"); log_axes(ax1, y=False)
    ax1.set_xlim(10, 1e5); ax1.set_ylim(-20, 10)
    ax1.set_xlabel("Frequency (Hz)")
    ax1.set_ylabel(r"$|Z_T|/R_F$ (dB)")
    ax1.legend(loc="lower left", fontsize=FONT_SIZE - 1)
    ax1.text(0.03, 0.97, "solid: SPICE (OPA140 model)\ndashed: Eq. (6) with the ladder",
             transform=ax1.transAxes, ha="left", va="top", fontsize=FONT_SIZE - 0.5)
    ax2.set_xlim(-0.2, 2.0); ax2.set_ylim(-0.1, 1.8)
    ax2.set_xlabel("Time after a 100-pA step (ms)")
    ax2.set_ylabel("Output / final value")
    ax2.text(0.98, 0.04, r"$R_F$ = 1 G$\Omega$, $C_{ee}$ = 0.05 pF, $C_g$ = 0.3 pF, 20 pF diode",
             transform=ax2.transAxes, ha="right", va="bottom", fontsize=FONT_SIZE - 0.5)
    export(fig, "fig9_spice_distributed")


# ------------------------------------------------------------------ Fig. 21
def fig_composite() -> None:
    amps = m.load_amps()
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.2), constrained_layout=True, sharey=True)
    sweep = json.loads((m.DATA / "results" / "designs.json").read_text())
    for ax, (src, label, (c_d, r_sh)) in zip(axes, (("S1336-8BK", "380 pF, 0.4 G$\\Omega$", (380e-12, 0.4e9)),
                                                   ("G12180-050A", "1 nF, 6.5 M$\\Omega$", (1e-9, 6.5e6)))):
        case = f"LSBF862_OPA140_{src}_1e+06"
        f, s_sp, s_op = np.load(RUNS / "composite" / case / "compare.npy")
        name = "S1336-8BK (Si 5.8 mm)" if src == "S1336-8BK" else "G12180-050A (InGaAs 5 mm)"
        comp = next(r for r in sweep if r["amp"] == "BF862 composite" and r["rf"] == 1e6 and r["source"] == name)
        d = m.Design(amps["BF862 composite"], 1e6, comp["cf_pF"] * 1e-12, m.Source(src, c_d, r_sh))
        ax.plot(f, s_sp, color=COLORS["primary"], lw=LW, label="LSBF862 cascode, SPICE")
        ax.plot(f, np.sqrt(d.noise(f)["total"]), color=COLORS["cool_accent"], lw=LW, ls=DASH,
                label="BF862 composite, model")
        ax.plot(f, s_op, color=COLORS["warm_accent"], lw=LW, ls=DASH, label="OPA140 alone, model")
        floor = math.sqrt(m.FOUR_KT / 1e6 + m.FOUR_KT / r_sh)
        ax.axhline(floor, color=COLORS["neutral"], lw=0.8, ls=(0, (1.5, 1.5)), label="resistor + diode floor")
        ax.set_xscale("log"); ax.set_yscale("log"); log_axes(ax)
        ax.set_xlim(1, 1e7); ax.set_ylim(5e-14, 3e-11)
        ax.set_xlabel("Frequency (Hz)")
        ax.set_title(f"$R_F$ = 1 M$\\Omega$, {label}")
    axes[0].set_ylabel(r"Input-referred noise (A/$\sqrt{\mathrm{Hz}}$)")
    axes[0].legend(loc="upper left", fontsize=FONT_SIZE - 1)
    export(fig, "fig10_spice_composite")


# ------------------------------------------------------------------ Fig. 22
AD8304_TPC9_1KHZ = {1e-9: 40.0, 1e-8: 5.5, 1e-7: 1.0, 1e-6: 0.17, 1e-5: 0.15}   # read by eye, uV/rtHz


def fig_logamp() -> None:
    res = load("lt_logamp")["logamp"]
    vt = m.K_B * m.T_REF / m.Q_E
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(7.2, 2.9), constrained_layout=True)
    i = np.logspace(-10, -2, 200)
    for part, col in (("AD8304", COLORS["primary"]), ("ADL5303", COLORS["warm_accent"])):
        rows = res[part]
        ii = np.array([r["i_in"] for r in rows])
        ax1.plot(ii, [r["v_log"] for r in rows], "o-", color=col, ms=3.5, lw=1.0, label=f"{part}, LTspice")
        ax2.plot(ii, [r["f3"] for r in rows], "o-", color=col, ms=3.5, lw=1.0, label=f"{part}, LTspice")
        ax3.plot(ii, [r["vn_1k"] * 1e6 for r in rows], "o-", color=col, ms=3.5, lw=1.0, label=f"{part}, LTspice")
    ax1.plot(i, 0.2 * np.log10(i / 1e-10), color=COLORS["neutral"], lw=1.0, ls=DASH, label="200 mV/decade from 100 pA")
    ax2.plot(i, i / (2 * math.pi * vt * 1.5e-12), color=COLORS["neutral"], lw=1.0, ls=DASH,
             label=r"Eq. (33), $C_C$ = 1.5 pF")
    ax2.plot([1e-9], [2e3], "*", color=COLORS["cool_accent"], ms=8, label="AD8304 data sheet, 1 nA")
    scale = 0.2 / math.log(10)
    ax3.plot(i, scale * np.sqrt(4 * m.Q_E / i) * 1e6, color=COLORS["neutral"], lw=1.0, ls=DASH,
             label="Eq. (35), shot-noise bound")
    ax3.plot(list(AD8304_TPC9_1KHZ), list(AD8304_TPC9_1KHZ.values()), "s", color=COLORS["cool_accent"], ms=4,
             mfc="white", label="AD8304 measured (TPC 9)")
    for ax in (ax1, ax2, ax3):
        ax.set_xscale("log"); log_axes(ax, y=False)
        ax.set_xlabel("Input current (A)")
        ax.set_xlim(1e-10, 1e-2)
    for ax in (ax2, ax3):
        ax.set_yscale("log"); log_axes(ax, x=False)
    ax1.set_ylabel(r"$V_{LOG}$ (V)")
    ax2.set_ylabel(r"$f_{-3\,\mathrm{dB}}$ (Hz)")
    ax2.set_ylim(1e2, 3e7)
    ax3.set_ylabel(r"Noise at 1 kHz ($\mu$V/$\sqrt{\mathrm{Hz}}$)")
    ax1.legend(loc="upper left", fontsize=FONT_SIZE - 1.5)
    ax2.legend(loc="upper left", fontsize=FONT_SIZE - 1.5)
    ax3.legend(loc="upper right", fontsize=FONT_SIZE - 1.5)
    export(fig, "fig11_spice_logamp")


# ------------------------------------------------------------------ Fig. 23
def fig_closed_forms() -> None:
    rows = json.loads((m.DATA / "results" / "designs.json").read_text())
    amps = m.load_amps()
    srcs = {"S1336-18BK (Si 1.1 mm)": (20e-12, 2e9), "G12180-010A (InGaAs 1 mm)": (55e-12, 125e6),
            "S1336-8BK (Si 5.8 mm)": (380e-12, 0.4e9), "G12180-050A (InGaAs 5 mm)": (1e-9, 6.5e6)}
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 3.3), constrained_layout=True)
    amp_ratio, res_ratio, dn_diff = [], [], []
    for r in rows:
        # the closed forms assume a single-pole amplifier: parts with a measured open-loop
        # shape (OPA1656) are left out, as are designs failing the open-loop-gain rule
        if (r["source"] not in srcs or "composite" in r["amp"] or r["a0_over_ng"] < 10
                or amps[r["amp"]].aol_shape):
            continue
        a = amps[r["amp"]]
        c_d, r_sh = srcs[r["source"]]
        c_t = c_d + a.c_in + 1e-12 + r["cf_pF"] * 1e-12
        rf = r["rf"]
        if r["limited_by"] == "amplifier":
            f3 = math.sqrt(a.gbw / (2 * math.pi * rf * c_t))                       # Eq. (19)
            e = float(a.en(np.array([f3]))[0])
            ratio = math.sqrt(m.FOUR_KT / (2 * math.pi * c_t * a.gbw)) / e        # Eq. (21)
            dn = 10 * math.log10(1 + (1 / ratio) ** 2 / 3)                        # Eq. (22)
            col = COLORS["primary"]
            ax2.plot(dn, r["dN_vs_RF_dB"], "o", color=col, ms=3, alpha=0.7)
            amp_ratio.append(r["f3_Hz"] / f3)
            dn_diff.append(r["dN_vs_RF_dB"] - dn)
        else:
            f3 = 1 / (2 * math.pi * rf * 0.1e-12)                                  # Eq. (4)
            col = COLORS["warm_accent"]
            res_ratio.append(r["f3_Hz"] / f3)
        ax1.plot(f3, r["f3_Hz"], "o", color=col, ms=3, alpha=0.7)
    dn_diff = np.array(dn_diff)
    print(f"Fig. 23: {len(amp_ratio)} amplifier-limited designs, f3/Eq.(19) = {min(amp_ratio):.3f}-{max(amp_ratio):.3f}; "
          f"{len(res_ratio)} resistor-limited, f3/f_R = {min(res_ratio):.3f}-{max(res_ratio):.3f}; "
          f"Eq. (22) within 1 dB in {100 * np.mean(np.abs(dn_diff) <= 1):.0f}%, "
          f"underestimates in {100 * np.mean(dn_diff > 0):.0f}%, median difference {np.median(dn_diff):.2f} dB")
    ax1.plot([1e2, 3e7], [1e2, 3e7], color=COLORS["neutral"], lw=0.8, ls=DASH)
    ax1.plot([1e2, 3e7], [1e2 * math.sqrt(2), 3e7 * math.sqrt(2)], color=COLORS["neutral"], lw=0.8,
             ls=(0, (1.5, 1.5)))
    ax1.set_xscale("log"); ax1.set_yscale("log"); log_axes(ax1)
    ax1.set_xlim(1e2, 3e7); ax1.set_ylim(1e2, 3e7)
    ax1.set_xlabel(r"Eq. (19) (blue) or Eq. (4) (red) (Hz)")
    ax1.set_ylabel(r"$f_{-3\,\mathrm{dB}}$, full model (Hz)")
    ax1.text(0.03, 0.97, r"dashed: 1:1; dotted: $\sqrt{2}$:1", transform=ax1.transAxes, va="top",
             fontsize=FONT_SIZE - 0.5)
    ax2.plot([0, 20], [0, 20], color=COLORS["neutral"], lw=0.8, ls=DASH)
    ax2.set_xlim(0, 20); ax2.set_ylim(0, 25)
    ax2.set_xlabel(r"Eq. (22) (dB)")
    ax2.set_ylabel(r"Excess over $R_F$ alone, full model (dB)")
    ax2.text(0.03, 0.97, "amplifier-limited designs;\nthe full model adds $i_n$, $R_{sh}$ and $1/f$",
             transform=ax2.transAxes, va="top", fontsize=FONT_SIZE - 0.5)
    export(fig, "fig12_closed_form_checks")


def main() -> None:
    configure_plot_style()
    fig_parity()
    fig_spectra()
    fig_models()
    fig_distributed()
    fig_composite()
    fig_logamp()
    fig_closed_forms()
    print("figures 6-12 written")


if __name__ == "__main__":
    main()
