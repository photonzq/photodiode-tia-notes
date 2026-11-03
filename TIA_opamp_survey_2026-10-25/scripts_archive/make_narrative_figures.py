"""Comparison charts of the narrative version of the survey (27 Oct 2026): every analysed part's
bandwidth and phase margin, its noise, and its dynamic range, each with the 50-ohm benchmark where it
applies, and the benchmark chart itself.  They draw, as charts, what the appendix tables list.

  fig17_bandwidth_phase_margin_all_parts   robust bandwidth and flat-design phase margin, both R_F
  fig18_noise_penalty_all_parts            band noise over the R_F Johnson floor, both R_F, with the
                                           50-ohm benchmark
  fig19_dynamic_range_all_parts            electronic dynamic range in the dark and at 0.1, 1 and 10 mA
                                           (2 kOhm) of the ten amplifiers of the dynamic-range table,
                                           with the 50-ohm benchmark at P_max = -10 dBm
  fig20_benchmark_50ohm                    the designs against the 50-ohm benchmark: small-signal
                                           advantage and usable dynamic range against photocurrent

Reads data/results/results.json (run_analysis.py) and data/results/benchmark_50ohm.json
(benchmark_50ohm.py); no simulation.  Follows the project plotting guide (Arial 8 pt, 1.5-pt lines,
the muted palette, 600-dpi PNG and PDF).

Usage: python make_narrative_figures.py [--fig-dir <dir>]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.ticker import FixedLocator, LogFormatterMathtext, NullFormatter, NullLocator

import benchmark_50ohm as bm

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FONT_SIZE = 8.0
COLORS = {"primary": "#385C9E", "neutral": "#4D4D4D", "warm_accent": "#9E403D",
          "cool_accent": "#477A57", "purple_accent": "#6B5B95", "teal_accent": "#3F7F82",
          "brown_accent": "#7D5C46", "grey_accent": "#6F6F6F", "highlight": "#EED671",
          "annotation": "#767676", "text": "#272727", "axes": "#000000", "background": "#FFFFFF"}
DASH = (0, (5, 2))
LW = 1.5
FET_PARTS = {"OPA818", "OPA858", "OPA859", "OPA657", "LTC6268-10", "ADA4817-1"}


def configure_plot_style() -> None:
    plt.rcParams.update({
        "figure.facecolor": COLORS["background"], "axes.facecolor": COLORS["background"],
        "axes.edgecolor": COLORS["axes"], "axes.labelcolor": COLORS["text"], "text.color": COLORS["text"],
        "xtick.color": COLORS["axes"], "ytick.color": COLORS["axes"],
        "font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans", "sans-serif"],
        "font.size": FONT_SIZE, "axes.labelsize": FONT_SIZE, "axes.titlesize": FONT_SIZE,
        "xtick.labelsize": FONT_SIZE, "ytick.labelsize": FONT_SIZE, "legend.fontsize": FONT_SIZE,
        "axes.linewidth": 0.8, "axes.spines.top": True, "axes.spines.right": True,
        "xtick.top": True, "ytick.right": True, "xtick.direction": "in", "ytick.direction": "in",
        "legend.frameon": False, "axes.grid": False, "text.usetex": False, "mathtext.fontset": "cm",
        "axes.formatter.use_mathtext": True, "pdf.fonttype": 42, "ps.fonttype": 42,
        "savefig.facecolor": "white", "savefig.bbox": "tight"})


def export(fig, stem: Path) -> None:
    fig.savefig(stem.with_suffix(".png"), dpi=600)
    fig.savefig(stem.with_suffix(".pdf"))
    plt.close(fig)


def short(name: str) -> str:
    return name.replace(" (COMP HI)", " HI").replace(" (COMP LO)", " LO")


def get(d, *keys):
    for k in keys:
        if not isinstance(d, dict) or k not in d:
            return None
        d = d[k]
    return d


def robust(res, name, rf):
    d = get(res, name, f"RF_{rf}", "designs", "robust45")
    if not d or d.get("f3_MHz") is None or not d.get("stable", True):
        return None, None
    return d["f3_MHz"], d.get("C_add_pF", 0.0)


def flat_pm(res, name, rf):
    d = get(res, name, f"RF_{rf}", "designs", "flat")
    if not d or d.get("pm_deg") is None or not d.get("stable", True):
        return None
    return d["pm_deg"]


def penalty(res, name, rf, est="central"):
    return get(res, name, f"RF_{rf}", "noise", "flat", est, "band_penalty_dB", "10-150 MHz")


def dr_cancelled(res, name, i_ma):
    return get(res, name, "RF_2000", "dr", "flat", "ac", "high-Z", "100 MHz", "dr_with_dc_cancelled",
               f"{i_ma:g} mA", "DR_150MHz_dB")


def part_axis(ax, names):
    ax.set_ylim(len(names) - 0.4, -0.6)
    ax.yaxis.set_major_locator(FixedLocator(range(len(names))))
    ax.set_yticklabels([short(n) for n in names])
    ax.tick_params(axis="y", which="both", right=False)


def fig_bandwidth(res, stem):
    names = sorted(res, key=lambda n: -(robust(res, n, 2000)[0] or 0.0))
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.4, 4.6), sharey=True, constrained_layout=True)
    for i, n in enumerate(names):
        for rf, filled in ((2000, True), (1500, False)):
            f3, add = robust(res, n, rf)
            if f3 is None:
                continue
            col = COLORS["warm_accent"] if add and add > 0.01 else COLORS["primary"]
            a1.plot(f3 * 1e6, i, marker="o", ms=4.5, color=col, mfc=col if filled else "white", mew=1.0, ls="none")
        if robust(res, n, 2000)[0] is None and robust(res, n, 1500)[0] is None:
            a1.text(3.3e7, i, "no robust design", va="center", color=COLORS["annotation"])
        for rf, filled in ((2000, True), (1500, False)):
            pm = flat_pm(res, n, rf)
            if pm is None:
                continue
            a2.plot(pm, i, marker="o", ms=4.5, color=COLORS["primary"], mfc=COLORS["primary"] if filled else "white",
                    mew=1.0, ls="none")
        if flat_pm(res, n, 2000) is None and flat_pm(res, n, 1500) is None:
            a2.text(2, i, "no stable flat design", va="center", color=COLORS["annotation"])
    a1.set_xscale("log")
    a1.xaxis.set_major_formatter(LogFormatterMathtext())
    a1.xaxis.set_minor_formatter(NullFormatter())
    a1.set_xlim(3e7, 1.5e9)
    a1.axvspan(150e6, 200e6, color=COLORS["highlight"], alpha=0.24, lw=0, zorder=0)
    a1.set_xlabel(r"Bandwidth with $\geq 45^\circ$ and $\leq 1$ dB peaking (Hz)")
    a2.axvline(45, color=COLORS["annotation"], lw=LW, ls=DASH)
    a2.set_xlim(0, 90)
    a2.set_xlabel(r"Phase margin of the flat design ($^\circ$)")
    part_axis(a1, names)
    a2.tick_params(axis="y", which="both", left=False)
    handles = [Line2D([], [], marker="o", ms=4.5, color=COLORS["primary"], ls="none", label=r"$R_F$ = 2 k$\Omega$"),
               Line2D([], [], marker="o", ms=4.5, color=COLORS["primary"], mfc="white", ls="none",
                      label=r"$R_F$ = 1.5 k$\Omega$"),
               Line2D([], [], marker="o", ms=4.5, color=COLORS["warm_accent"], ls="none", label="input C added")]
    a1.legend(handles=handles, loc="lower right")
    a1.text(0.02, 0.995, "(a)", transform=a1.transAxes, va="top")
    a2.text(0.02, 0.995, "(b)", transform=a2.transAxes, va="top")
    export(fig, stem)


def fig_noise(res, bench, stem):
    names = sorted([n for n in res if penalty(res, n, 2000) is not None], key=lambda n: penalty(res, n, 2000))
    fig, ax = plt.subplots(figsize=(4.2, 4.6), constrained_layout=True)
    for i, n in enumerate(names):
        for rf, filled, dy in ((2000, True, -0.12), (1500, False, 0.12)):
            p = penalty(res, n, rf)
            if p is None:
                continue
            ph = penalty(res, n, rf, "high")
            col = COLORS["warm_accent"] if n in FET_PARTS else COLORS["primary"]
            if ph is not None and ph > p + 0.05:
                ax.plot([p, ph], [i + dy] * 2, color=col, lw=1.0)
            ax.plot(p, i + dy, marker="o", ms=4.5, color=col, mfc=col if filled else "white", mew=1.0, ls="none")
    for rf, ls in (("2000", DASH), ("1500", ":")):
        ax.axvline(bench["penalty_vs_RF_dB"][rf], color=COLORS["neutral"], lw=LW, ls=ls)
    ax.set_xlim(0, 32)
    ax.set_xlabel(r"Noise above the $R_F$ Johnson floor, 10–150 MHz (dB)")
    part_axis(ax, names)
    handles = [Line2D([], [], marker="o", ms=4.5, color=COLORS["primary"], ls="none", label=r"bipolar, 2 k$\Omega$"),
               Line2D([], [], marker="o", ms=4.5, color=COLORS["primary"], mfc="white", ls="none",
                      label=r"bipolar, 1.5 k$\Omega$"),
               Line2D([], [], marker="o", ms=4.5, color=COLORS["warm_accent"], ls="none", label="FET or CMOS"),
               Line2D([], [], color=COLORS["neutral"], lw=LW, ls=DASH, label="50-$\\Omega$ benchmark,\n"
                      r"NF 2 dB, vs 2 k$\Omega$"),
               Line2D([], [], color=COLORS["neutral"], lw=LW, ls=":", label=r"the same, vs 1.5 k$\Omega$")]
    ax.legend(handles=handles, loc="upper right")
    export(fig, stem)


DR_PARTS = ("OPA818", "OPA955", "LMH6629 (COMP HI)", "OPA855", "OPA858", "OPA843", "OPA859", "THS4304",
            "OPA846", "OPA856")   # the ten amplifiers of the report's dynamic-range table at 2 kOhm


def fig_dr(res, bench, stem):
    names = sorted([n for n in DR_PARTS if dr_cancelled(res, n, 1) is not None], key=lambda n: -dr_cancelled(res, n, 1))
    currents = (0, 0.1, 1, 10)
    cols = {0: COLORS["neutral"], 0.1: COLORS["primary"], 1: COLORS["warm_accent"], 10: COLORS["cool_accent"]}
    marks = {0: "D", 0.1: "o", 1: "s", 10: "^"}
    fig, ax = plt.subplots(figsize=(5.6, 3.2), constrained_layout=True)
    for i, n in enumerate(names):
        for i_ma in currents:
            v = dr_cancelled(res, n, i_ma)
            if v is not None:
                ax.plot(v, i, marker=marks[i_ma], ms=4.5, color=cols[i_ma], ls="none")
    ref = bench["per_pmax"]["-10 dBm"]["dr_electronic_dB"]
    for i_ma in currents:
        ax.axvline(ref[f"{i_ma:g} mA"], color=cols[i_ma], lw=LW, ls=DASH)
    ax.set_xlim(40, 90)
    ax.set_xlabel("Electronic dynamic range in 150 MHz, 100-MHz tone (dB)")
    part_axis(ax, names)
    handles = [Line2D([], [], marker=marks[k], ms=4.5, color=cols[k], ls="none",
                      label="dark" if k == 0 else f"{k:g} mA") for k in currents]
    handles.append(Line2D([], [], color=COLORS["neutral"], lw=LW, ls=DASH, label="50-$\\Omega$ benchmark,\n$-10$ dBm, NF 2 dB,\nat each current"))
    ax.legend(handles=handles, loc="center left", bbox_to_anchor=(1.02, 0.5))
    export(fig, stem)


def fig_benchmark(stem):
    """Small-signal advantage over the benchmark, and usable dynamic range, against photocurrent."""
    i_dc = np.logspace(-5, np.log10(2e-2), 600)
    n50 = bm.bench_noise0()
    designs = bm.designs()
    style = {"OPA955": (COLORS["teal_accent"], "-"), "OPA855": (COLORS["primary"], "-"),
             "OPA818": (COLORS["warm_accent"], "-"), "CE3512K2 composite": (COLORS["purple_accent"], DASH),
             "HV composite (G2 = 5.5)": (COLORS["cool_accent"], "-")}
    # the names the report uses: the composites of Sections 7.1 and 7.2
    labels = {"CE3512K2 composite": "pHEMT composite", "HV composite (G2 = 5.5)": "high-voltage composite"}
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.4, 3.24), constrained_layout=True)
    for name, d in designs.items():
        col, ls = style[name]
        nt = bm.noise(d["n0"], i_dc)
        nb = bm.noise(n50, i_dc)
        a1.plot(i_dc * 1e3, 20 * np.log10(nb / nt), color=col, lw=LW, ls=ls, label=labels.get(name, name))
        a2.plot(i_dc * 1e3, bm.usable(d["i_max"], nt, i_dc), color=col, lw=LW, ls=ls)
    for p, col in ((-20.0, COLORS["grey_accent"]), (-10.0, COLORS["neutral"]), (0.0, COLORS["brown_accent"])):
        a2.plot(i_dc * 1e3, bm.usable(bm.bench_imax(p), bm.noise(n50, i_dc), i_dc), color=col, lw=LW, ls=":",
                label=f"50 $\\Omega$, {p:g} dBm")
    for ax in (a1, a2):
        ax.set_xscale("log")
        ax.xaxis.set_major_formatter(LogFormatterMathtext())
        ax.xaxis.set_minor_formatter(NullFormatter())
        ax.set_xlim(1e-2, 20)
        ax.axvspan(0.1, 10, color=COLORS["highlight"], alpha=0.24, lw=0, zorder=0)
        ax.set_xlabel(r"DC photocurrent of the pair, $I_1 + I_2$ (mA)")
    a1.axhline(0, color=COLORS["annotation"], lw=0.8)
    a1.set_ylim(-1, 20)
    a1.set_ylabel("Advantage over the 50-$\\Omega$ benchmark,\nsame small signal (dB)")
    a1.legend(loc="upper right")
    a2.set_ylim(30, 85)
    a2.set_ylabel("Usable dynamic range in 150 MHz (dB)")
    a2.legend(loc="lower right")
    a1.text(0.03, 0.93, "(a)", transform=a1.transAxes)
    a2.text(0.03, 0.93, "(b)", transform=a2.transAxes)
    export(fig, stem)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--fig-dir", type=Path, default=ROOT / "figures")
    a = ap.parse_args()
    configure_plot_style()
    res = json.loads((ROOT / "data" / "results" / "results.json").read_text(encoding="utf-8"))
    bench = json.loads((ROOT / "data" / "results" / "benchmark_50ohm.json").read_text(encoding="utf-8"))["benchmark"]
    a.fig_dir.mkdir(parents=True, exist_ok=True)
    fig_bandwidth(res, a.fig_dir / "fig17_bandwidth_phase_margin_all_parts")
    fig_noise(res, bench, a.fig_dir / "fig18_noise_penalty_all_parts")
    fig_dr(res, bench, a.fig_dir / "fig19_dynamic_range_all_parts")
    fig_benchmark(a.fig_dir / "fig20_benchmark_50ohm")
    print("wrote fig17-fig20 to", a.fig_dir)


if __name__ == "__main__":
    main()
