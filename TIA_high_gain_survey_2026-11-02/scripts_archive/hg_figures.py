"""Figures of the high-gain TIA note (analytic model of hg_model.py, no
simulation).  Writes figures/fig<N>_<name>.png (600 dpi) and .pdf.

    Fig. 2  current window and noise floor against R_F
    Fig. 3  bandwidth ceilings against R_F
    Fig. 5  feedback resistor as a distributed RC line: transimpedance
    Fig. 10  dominant noise term over R_F and frequency (two photodiodes)
    Fig. 11  input-referred noise spectra at the five gain decades

Usage:  python hg_figures.py
"""
from __future__ import annotations

import math
import pathlib

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
from matplotlib.ticker import LogFormatterMathtext, LogLocator

import hg_model as m

FIG = pathlib.Path(__file__).resolve().parent.parent / "figures"
FONT_SIZE = 8.0
COLORS = {
    "primary": "#385C9E", "neutral": "#4D4D4D", "warm_accent": "#9E403D",
    "cool_accent": "#477A57", "purple_accent": "#6B5B95", "teal_accent": "#3F7F82",
    "brown_accent": "#7D5C46", "grey_accent": "#6F6F6F", "highlight": "#EED671",
    "annotation": "#767676", "text": "#272727", "axes": "#000000",
    "background": "#FFFFFF",
}
CYCLE = [COLORS[k] for k in ("primary", "warm_accent", "cool_accent", "purple_accent",
                              "teal_accent", "brown_accent", "grey_accent")]
LW = 1.5
DASH = (0, (5, 2))


def configure_plot_style() -> None:
    plt.rcParams.update({
        "figure.facecolor": COLORS["background"], "axes.facecolor": COLORS["background"],
        "axes.edgecolor": COLORS["axes"], "axes.labelcolor": COLORS["text"],
        "text.color": COLORS["text"], "xtick.color": COLORS["axes"],
        "ytick.color": COLORS["axes"], "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "DejaVu Sans", "sans-serif"],
        "font.size": FONT_SIZE, "axes.labelsize": FONT_SIZE, "axes.titlesize": FONT_SIZE,
        "xtick.labelsize": FONT_SIZE, "ytick.labelsize": FONT_SIZE,
        "legend.fontsize": FONT_SIZE, "axes.linewidth": 0.8,
        "axes.prop_cycle": plt.cycler(color=CYCLE), "axes.spines.top": True,
        "axes.spines.right": True, "xtick.top": True, "ytick.right": True,
        "xtick.direction": "in", "ytick.direction": "in", "legend.frameon": False,
        "axes.grid": False, "text.usetex": False, "mathtext.fontset": "cm",
        "axes.formatter.use_mathtext": True, "pdf.fonttype": 42, "ps.fonttype": 42,
        "savefig.facecolor": "white", "savefig.bbox": "tight",
    })


def log_axes(ax, x=True, y=True) -> None:
    for axis, on in ((ax.xaxis, x), (ax.yaxis, y)):
        if on:
            axis.set_major_formatter(LogFormatterMathtext())
            axis.set_major_locator(LogLocator(base=10, numticks=20))


def export(fig, name: str) -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / f"{name}.png", dpi=600)
    fig.savefig(FIG / f"{name}.pdf")
    plt.close(fig)


# ------------------------------------------------------------------ Fig. 2
def fig_current_window() -> None:
    rf = np.logspace(3, 10, 300)
    fig, ax = plt.subplots(figsize=(4.2, 3.24), constrained_layout=True)
    ax.plot(rf, 10.0 / rf, color=COLORS["primary"], lw=LW, label=r"$I_{\max}$, 10 V swing")
    ax.plot(rf, 2.4 / rf, color=COLORS["primary"], lw=LW, ls=DASH, label=r"$I_{\max}$, 2.4 V swing")
    ax.plot(rf, 2 * m.K_B * m.T_REF / (m.Q_E * rf), color=COLORS["warm_accent"], lw=LW,
            label=r"$2k_BT/(qR_F)$: shot = Johnson")
    ax.plot(rf, np.sqrt(m.FOUR_KT / rf), color=COLORS["cool_accent"], lw=LW,
            label=r"$\sqrt{4k_BT/R_F}$ in 1 Hz")
    ax.axvspan(1e5, 1e9, color=COLORS["highlight"], alpha=0.24, lw=0, zorder=0)
    ax.axvspan(1.5e3, 2e3, color=COLORS["grey_accent"], alpha=0.35, lw=0, zorder=0)
    ax.text(2.3e3, 2e-15, "companion note", ha="left", va="bottom",
            color=COLORS["annotation"])
    ax.text(1e7, 2e-15, "this note", ha="center", va="bottom", color=COLORS["annotation"])
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlim(1e3, 1e10); ax.set_ylim(1e-15, 1e-2)
    log_axes(ax)
    ax.set_xlabel(r"Feedback resistance, $R_F$ ($\Omega$)")
    ax.set_ylabel(r"Current (A), or noise current in 1 Hz (A)")
    ax.legend(loc="upper right")
    export(fig, "fig1_current_window")


# ------------------------------------------------------------------ Fig. 3
def fig_bandwidth() -> None:
    rf = np.logspace(4, 10, 400)
    gbw = 20e6
    fig, ax = plt.subplots(figsize=(4.2, 3.24), constrained_layout=True)
    for c_par, ls in ((0.05e-12, DASH), (0.1e-12, "-"), (0.2e-12, (0, (1.5, 1.5)))):
        ax.plot(rf, 1 / (2 * math.pi * rf * c_par), color=COLORS["neutral"], lw=LW, ls=ls,
                label=rf"$1/(2\pi R_F C_{{par}})$, {c_par * 1e12:g} pF")
    for c_t, col in ((10e-12, COLORS["primary"]), (100e-12, COLORS["warm_accent"]),
                     (1e-9, COLORS["cool_accent"])):
        ax.plot(rf, np.sqrt(gbw / (2 * math.pi * rf * c_t)), color=col, lw=LW,
                label=rf"$\sqrt{{GBW/(2\pi R_F C_T)}}$, $C_T$ = {c_t * 1e12:g} pF")
        r_star = c_t / (math.pi * gbw * (0.1e-12) ** 2)
        ax.plot([r_star], [math.sqrt(gbw / (2 * math.pi * r_star * c_t))], "o", ms=4,
                color=col, mfc="white")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlim(1e4, 1e10); ax.set_ylim(1e2, 1e8)
    log_axes(ax)
    ax.set_xlabel(r"Feedback resistance, $R_F$ ($\Omega$)")
    ax.set_ylabel(r"$-3$ dB bandwidth (Hz)")
    ax.legend(loc="lower left", fontsize=FONT_SIZE - 0.5)
    export(fig, "fig2_bandwidth_ceilings")


# ------------------------------------------------------------------ Fig. 5
def fig_distributed() -> None:
    f = np.logspace(1, 6, 600)
    w = 2 * math.pi * f
    rf, cee = 1e9, 0.05e-12
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(4.2, 4.6), sharex=True,
                                   constrained_layout=True)
    cases = [(0.0, COLORS["neutral"], DASH, r"lumped, $C_g$ = 0"),
             (0.1e-12, COLORS["primary"], "-", r"$C_g$ = 0.1 pF"),
             (0.3e-12, COLORS["warm_accent"], "-", r"$C_g$ = 0.3 pF ($=6C_{ee}$)"),
             (0.6e-12, COLORS["cool_accent"], "-", r"$C_g$ = 0.6 pF")]
    for cg, col, ls, lab in cases:
        _, y21 = m.urc_y(w, rf, cg, cee)
        zt = 1.0 / (-y21)          # ideal amplifier: Z_T = -1/y21 (magnitude, phase)
        ax1.plot(f, 20 * np.log10(np.abs(zt) / rf), color=col, lw=LW, ls=ls, label=lab)
        ax2.plot(f, np.degrees(np.angle(zt)), color=col, lw=LW, ls=ls)
    # plane under the resistor driven from the output: the line's capacitance
    # then returns to the output node and the transfer admittance is y11
    y11, _ = m.urc_y(w, rf, 0.3e-12, cee)
    zt = 1.0 / y11
    ax1.plot(f, 20 * np.log10(np.abs(zt) / rf), color=COLORS["purple_accent"], lw=LW,
             ls=(0, (6, 2, 1.5, 2)), label=r"$C_g$ = 0.3 pF to the output")
    ax2.plot(f, np.degrees(np.angle(zt)), color=COLORS["purple_accent"], lw=LW,
             ls=(0, (6, 2, 1.5, 2)))
    ax1.set_ylabel(r"$|Z_T|/R_F$ (dB)")
    ax1.set_ylim(-20, 8)
    ax1.legend(loc="lower left")
    ax2.set_ylabel(r"Phase of $Z_T$ (deg)")
    ax2.set_xlabel("Frequency (Hz)")
    for ax in (ax1, ax2):
        ax.set_xscale("log")
        log_axes(ax, y=False)
    ax1.text(0.98, 0.62, "$R_F$ = 1 G$\\Omega$\n$C_{ee}$ = 0.05 pF\nideal amplifier",
             transform=ax1.transAxes, ha="right", va="top")
    export(fig, "fig3_distributed_resistor")


# ------------------------------------------------------------------ Fig. 10
TERM_ORDER = ["R_F", "shunt", "i_n", "e_n_G", "e_n_C"]
TERM_LABEL = {"R_F": r"$R_F$ Johnson", "shunt": r"diode $R_{sh}$ Johnson",
              "i_n": r"amplifier $i_n$", "e_n_G": r"$e_n/(R_F\parallel R_{sh})$",
              "e_n_C": r"$e_n\,\omega C$"}
TERM_COLOR = [COLORS["primary"], COLORS["cool_accent"], COLORS["warm_accent"],
              COLORS["purple_accent"], COLORS["brown_accent"]]


def dominance(amp: m.Amp, src: m.Source, rf_grid, f_grid):
    dom = np.zeros((len(f_grid), len(rf_grid)), dtype=int)
    f3 = np.zeros(len(rf_grid))
    for j, rf in enumerate(rf_grid):
        d, met = m.choose_cf(amp, rf, src, 0.1e-12, f=np.logspace(-2, 9, 900))
        f3[j] = met["f3"]
        nz = d.noise(f_grid)
        stack = np.vstack([nz[k] for k in TERM_ORDER])
        dom[:, j] = np.argmax(stack, axis=0)
    return dom, f3


def fig_dominance() -> None:
    amps = m.load_amps()
    rf_grid = np.logspace(4, 10, 61)
    f_grid = np.logspace(-2, 8, 201)
    srcs = [m.Source("Si 1.1 mm, 20 pF, 2 G$\\Omega$", 20e-12, 2e9),
            m.Source("InGaAs 5 mm, 1 nF, 6.5 M$\\Omega$", 1e-9, 6.5e6)]
    cmap = ListedColormap(TERM_COLOR)
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.4), sharey=True, constrained_layout=True)
    for ax, src in zip(axes, srcs):
        dom, f3 = dominance(amps["ADA4625-1"], src, rf_grid, f_grid)
        ax.pcolormesh(rf_grid, f_grid, dom, cmap=cmap, vmin=-0.5, vmax=4.5,
                      shading="nearest", rasterized=True)
        ax.fill_between(rf_grid, f3, 1e8, color="white", alpha=0.55, lw=0)
        ax.plot(rf_grid, f3, color="black", lw=LW, label=r"$f_{-3\,\mathrm{dB}}$")
        ax.set_xscale("log"); ax.set_yscale("log")
        log_axes(ax)
        ax.set_xlim(1e4, 1e10); ax.set_ylim(1e-2, 1e8)
        ax.set_xlabel(r"Feedback resistance, $R_F$ ($\Omega$)")
        ax.set_title(src.name + ", ADA4625-1")
    axes[0].set_ylabel("Frequency (Hz)")
    handles = [Patch(color=c, label=TERM_LABEL[k]) for k, c in zip(TERM_ORDER, TERM_COLOR)]
    handles.append(plt.Line2D([], [], color="black", lw=LW, label=r"$f_{-3\,\mathrm{dB}}$ (pale above)"))
    fig.legend(handles=handles, loc="outside lower center", ncol=3)
    export(fig, "fig4_dominant_term_maps")


# ------------------------------------------------------------------ Fig. 11
def fig_spectra() -> None:
    amps = m.load_amps()
    src = m.Source("S1336-8BK", 380e-12, 0.4e9)
    f = np.logspace(-2, 8, 800)
    fig, ax = plt.subplots(figsize=(4.2, 3.24), constrained_layout=True)
    for rf, col in zip([1e5, 1e6, 1e7, 1e8, 1e9], CYCLE):
        d, met = m.choose_cf(amps["ADA4625-1"], rf, src, 0.1e-12)
        nz = d.noise(f)
        ax.plot(f, np.sqrt(nz["total"]), color=col, lw=LW,
                label=rf"$R_F$ = $10^{{{int(round(math.log10(rf)))}}}$ $\Omega$")
        ax.plot(f, np.sqrt(nz["R_F"] + nz["shunt"]), color=col, lw=LW, ls=DASH)
        i3 = np.searchsorted(f, met["f3"])
        ax.plot([f[i3]], [np.sqrt(nz["total"][i3])], "o", ms=4, color=col, mfc="white")
    ax.set_xscale("log"); ax.set_yscale("log")
    log_axes(ax)
    ax.set_xlim(1e-2, 1e8); ax.set_ylim(1e-15, 1e-9)
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel(r"Input-referred noise (A/$\sqrt{\mathrm{Hz}}$)")
    ax.legend(loc="upper left", fontsize=FONT_SIZE - 0.5)
    ax.text(0.98, 0.04, "S1336-8BK (380 pF, 0.4 G$\\Omega$), ADA4625-1\n"
            "dashed: $R_F$ + diode floor; circles: $f_{-3\\,\\mathrm{dB}}$",
            transform=ax.transAxes, ha="right", va="bottom")
    export(fig, "fig5_noise_spectra")


def main() -> None:
    configure_plot_style()
    fig_current_window()
    fig_bandwidth()
    fig_distributed()
    fig_dominance()
    fig_spectra()
    print("figures written to", FIG)


if __name__ == "__main__":
    main()
