"""Figures for the TIA amplifier survey.

Usage: python make_figures.py <results_dir> <figure_dir>

Reads <results_dir>/results.json (from run_analysis.py) and parts_db.PARTS and
writes PNG (600 dpi) and PDF files following the project plotting guide.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import LogFormatterMathtext, NullFormatter

import tia_model as tm
from parts_db import PARTS
from run_analysis import (C_D, C_PCB_NOM, open_loop_model, noise_inputs)

FONT_SIZE = 8.0
COLORS = {"primary": "#385C9E", "neutral": "#4D4D4D", "warm_accent": "#9E403D",
          "cool_accent": "#477A57", "purple_accent": "#6B5B95", "teal_accent": "#3F7F82",
          "brown_accent": "#7D5C46", "grey_accent": "#6F6F6F", "highlight": "#EED671",
          "annotation": "#767676", "text": "#272727", "axes": "#000000", "background": "#FFFFFF"}
COLOR_CYCLE = [COLORS[k] for k in ("primary", "warm_accent", "cool_accent", "purple_accent",
                                   "teal_accent", "brown_accent", "grey_accent", "neutral")]
LINESTYLES = ["-", (0, (5, 2)), "-", "-", (0, (5, 2)), (0, (5, 2)), "-", (0, (5, 2))]
DASH = (0, (5, 2))
LW = 1.5


def configure_plot_style() -> None:
    plt.rcParams.update({
        "figure.facecolor": COLORS["background"], "axes.facecolor": COLORS["background"],
        "axes.edgecolor": COLORS["axes"], "axes.labelcolor": COLORS["text"], "text.color": COLORS["text"],
        "xtick.color": COLORS["axes"], "ytick.color": COLORS["axes"],
        "font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans", "sans-serif"],
        "font.size": FONT_SIZE, "axes.labelsize": FONT_SIZE, "axes.titlesize": FONT_SIZE,
        "xtick.labelsize": FONT_SIZE, "ytick.labelsize": FONT_SIZE, "legend.fontsize": FONT_SIZE,
        "axes.linewidth": 0.8, "axes.prop_cycle": plt.cycler(color=COLOR_CYCLE),
        "axes.spines.top": True, "axes.spines.right": True, "xtick.top": True, "ytick.right": True,
        "xtick.direction": "in", "ytick.direction": "in", "legend.frameon": False,
        "axes.grid": False, "text.usetex": False, "mathtext.fontset": "cm",
        "axes.formatter.use_mathtext": True, "pdf.fonttype": 42, "ps.fonttype": 42,
        "savefig.facecolor": "white", "savefig.bbox": "tight"})


def export(fig, stem: Path) -> None:
    fig.savefig(stem.with_suffix(".png"), dpi=600)
    fig.savefig(stem.with_suffix(".pdf"))
    plt.close(fig)


def log_axes(ax, x=True, y=True):
    if x:
        ax.set_xscale("log")
        ax.xaxis.set_major_formatter(LogFormatterMathtext())
        ax.xaxis.set_minor_formatter(NullFormatter())
    if y:
        ax.set_yscale("log")
        ax.yaxis.set_major_formatter(LogFormatterMathtext())
        ax.yaxis.set_minor_formatter(NullFormatter())


def design_cf(res, name, R_F, tag):
    d = res[name][f"RF_{R_F:.0f}"]["designs"].get(tag, {})
    return None if d.get("C_F_real_pF") is None else d["C_F_real_pF"] * 1e-12


def fig_noise(res, parts, R_F, tag, stem, f_max=1e9):
    """Input-referred current noise ASD vs frequency (central model; band to the upper estimate)."""
    f = np.logspace(6, np.log10(f_max), 600)
    fig, ax = plt.subplots(figsize=(4.2, 3.24), constrained_layout=True)
    for i, name in enumerate(parts):
        p = PARTS[name]
        cf = design_cf(res, name, R_F, tag)
        if cf is None:
            continue
        C_T = C_D + C_PCB_NOM + p["c_cm"] + p["c_diff"]
        nz = noise_inputs(p)
        c = COLOR_CYCLE[i % len(COLOR_CYCLE)]
        lo = np.sqrt(tm.noise_components(f, R_F, C_T, cf, nz, fet_model="central")["total"]) * 1e12
        ax.plot(f, lo, color=c, lw=LW, ls=LINESTYLES[i % len(LINESTYLES)], label=name)
        if p.get("in_pts") and (p.get("fet") or p.get("in_curve_is_physical")):
            hi = np.sqrt(tm.noise_components(f, R_F, C_T, cf, nz, fet_model="high")["total"]) * 1e12
            ax.fill_between(f, lo, hi, color=c, alpha=0.18, lw=0, label="_nolegend_")
    i_rf = tm.johnson_current_asd(R_F) * 1e12
    ax.axhline(i_rf, color=COLORS["neutral"], lw=LW, ls=":", label="_nolegend_")
    ax.text(1.15e6, i_rf * 0.86, rf"$R_F$ Johnson ({i_rf:.2f})", color=COLORS["neutral"], va="top")
    for idc, txt in ((1e-4, "0.1 mA"), (1e-3, "1 mA")):
        s = tm.shot_current_asd(idc) * 1e12
        ax.axhline(s, color=COLORS["annotation"], lw=LW, ls=DASH, label="_nolegend_")
        ax.text(1.15e6, s * 1.06, f"shot noise, {txt} ({s:.1f})", color=COLORS["annotation"], va="bottom")
    log_axes(ax)
    ax.set_xlim(1e6, f_max)
    ax.set_ylim(1, 60)
    ax.set_xlabel(r"Frequency, $f$ (Hz)")
    ax.set_ylabel(r"Input-referred current noise (pA/$\sqrt{\mathrm{Hz}}$)")
    ax.legend(loc="lower right", ncol=2, handlelength=2.2, columnspacing=1.0)
    export(fig, stem)


def fig_response(res, parts, R_F, tag, stem):
    """Transimpedance magnitude |Z_T| in dB-ohm."""
    f = np.logspace(6, 9.6, 1500)
    fig, ax = plt.subplots(figsize=(4.2, 3.24), constrained_layout=True)
    for i, name in enumerate(parts):
        p = PARTS[name]
        cf = design_cf(res, name, R_F, tag)
        if cf is None:
            continue
        ol, *_ = open_loop_model(p)
        C_T = C_D + C_PCB_NOM + p["c_cm"] + p["c_diff"]
        Z, _, _ = tm.tia_tf(f, ol, R_F, C_T, cf)
        ax.plot(f, 20 * np.log10(np.abs(Z)), color=COLOR_CYCLE[i % len(COLOR_CYCLE)], lw=LW,
                ls=LINESTYLES[i % len(LINESTYLES)], label=name)
    ax.axhline(20 * np.log10(R_F) - 3, color=COLORS["annotation"], lw=LW, ls=":", label="_nolegend_")
    ax.text(1.1e6, 20 * np.log10(R_F) - 3.4, "−3 dB", color=COLORS["annotation"], va="top")
    ax.axvspan(150e6, 200e6, color=COLORS["highlight"], alpha=0.24, lw=0, label="_nolegend_", zorder=0)
    log_axes(ax, x=True, y=False)
    ax.set_xlim(1e6, 4e9)
    ax.set_ylim(20 * np.log10(R_F) - 20, 20 * np.log10(R_F) + 6)
    ax.set_xlabel(r"Frequency, $f$ (Hz)")
    ax.set_ylabel(r"Transimpedance, $|Z_T|$ (dB$\Omega$)")
    ax.legend(loc="lower left", ncol=2, handlelength=2.2)
    export(fig, stem)


LANDSCAPE_OFFSETS = {   # label offsets in points (third item: draw a leader line)
    "OPA846": (-30, 7), "THS4021": (5, 2), "OPA856": (-62, -30, True), "LMH6624": (-44, -22, True),
    "ADA4895-1": (30, 30, True), "LTC6228": (-75, -14, True), "LMH6629 (COMP HI)": (5, -9),
    "LMH6629 (COMP LO)": (6, -13), "THS4271": (5, 4), "AD8045": (5, -9),
    "LTC6268-10": (-20, -11), "OPA847": (5, -4), "AD8099": (5, 1), "OPA955": (-12, -11),
    "OPA843": (-36, -3), "LT6230-10": (-56, 3, True), "LT6200-10": (12, -16, True),
}


def fig_landscape(stem):
    """Amplifier landscape: e_n vs GBW, marker area ~ input capacitance."""
    fig, ax = plt.subplots(figsize=(4.2, 3.24), constrained_layout=True)
    for name, p in PARTS.items():
        c_amp = (p["c_cm"] + p["c_diff"]) * 1e12
        col = COLORS["warm_accent"] if p.get("fet") else COLORS["primary"]
        mk = "s" if p["g_min"] <= 1.5 else "o"
        ax.scatter(p["gbw"], p["en"] * 1e9, s=12 * min(max(c_amp, 0.3), 8.0), color=col, marker=mk,
                   alpha=0.75, edgecolors="none")
        label = name.replace(" (COMP HI)", " HI").replace(" (COMP LO)", " LO")
        off = LANDSCAPE_OFFSETS.get(name, (4, 3))
        arrow = dict(arrowstyle="-", lw=0.6, color=COLORS["annotation"]) if len(off) > 2 else None
        ax.annotate(label, (p["gbw"], p["en"] * 1e9), xytext=off[:2], textcoords="offset points",
                    color=COLORS["text"], arrowprops=arrow)
    log_axes(ax)
    ax.set_xlim(2e8, 2e10)
    ax.set_ylim(0.5, 8)
    ax.set_xlabel("Gain-bandwidth product, GBW (Hz)")
    ax.set_ylabel(r"Input voltage noise, $e_n$ (nV/$\sqrt{\mathrm{Hz}}$)")
    ax.scatter([], [], color=COLORS["primary"], marker="o", label="bipolar, decompensated")
    ax.scatter([], [], color=COLORS["primary"], marker="s", label="bipolar, unity-gain stable")
    ax.scatter([], [], color=COLORS["warm_accent"], marker="o", label="FET, decompensated")
    ax.scatter([], [], color=COLORS["warm_accent"], marker="s", label="FET, unity-gain stable")
    ax.legend(loc="upper right", bbox_to_anchor=(1.0, 0.99), handletextpad=0.2, borderaxespad=0.2)
    export(fig, stem)


def fig_bw_vs_penalty(res, R_F, tag, stem):
    """Bandwidth of the robust design (phase margin >= 45 deg, <= 1 dB peaking) vs
    the in-band noise penalty over the R_F Johnson floor (10-150 MHz)."""
    fig, ax = plt.subplots(figsize=(4.2, 3.24), constrained_layout=True)
    for name, p in PARTS.items():
        x = res[name][f"RF_{R_F:.0f}"]
        d = x["designs"].get(tag)
        nz = x["noise"].get(tag)
        if not d or not nz:
            continue
        pen = nz["central"]["band_penalty_dB"]["10-150 MHz"]
        added = d.get("C_add_pF", 0.0) > 0.01
        col = COLORS["warm_accent"] if added else COLORS["primary"]
        mk = "s" if p.get("fet") else "o"
        ax.scatter(d["f3_MHz"] * 1e6, pen, color=col, marker=mk, s=24, edgecolors="none", zorder=3)
        if "high" in nz:
            ph = nz["high"]["band_penalty_dB"]["10-150 MHz"]
            ax.plot([d["f3_MHz"] * 1e6] * 2, [pen, ph], color=col, lw=1.0, zorder=2)
        label = name.replace(" (COMP HI)", " HI").replace(" (COMP LO)", " LO")
        off = {"THS4304": (-40, -3), "OPA859": (5, -9), "OPA955": (-44, -4), "OPA855": (5, 3),
               "LMH6629 (COMP LO)": (-52, 5), "LMH6629 (COMP HI)": (-28, -11),
               "LT6200-10": (-46, -3), "OPA843": (-36, 1), "ADA4899-1": (-50, -3),
               "ADA4895-1": (4, -5), "LMH6624": (4, 3)}.get(name, (4, 2))
        ax.annotate(label, (d["f3_MHz"] * 1e6, pen), xytext=off, textcoords="offset points")
    ax.axvspan(150e6, 200e6, color=COLORS["highlight"], alpha=0.24, lw=0, zorder=0)
    log_axes(ax, x=True, y=False)
    ax.set_xlim(3e7, 1.2e9)
    ax.set_ylim(2.0, 15.5)
    ax.set_xlabel(r"Bandwidth with $\geq 45^\circ$ phase margin, $f_{-3\,\mathrm{dB}}$ (Hz)")
    ax.set_ylabel(r"Noise above $R_F$ Johnson floor, 10–150 MHz (dB)")
    ax.scatter([], [], color=COLORS["primary"], marker="o", s=24, label="bipolar")
    ax.scatter([], [], color=COLORS["primary"], marker="s", s=24, label="FET")
    ax.scatter([], [], color=COLORS["warm_accent"], marker="o", s=24, label="needs added input C")
    ax.legend(loc="upper right", bbox_to_anchor=(1.0, 0.80))
    export(fig, stem)


def fig_dr_vs_idc(res, parts, R_F, tag, stem, f0=100e6):
    """Dynamic range in 150 MHz vs DC photocurrent, DC-coupled vs DC-cancelled."""
    i_dc = np.logspace(-6, -2, 200)
    band = np.linspace(1e4, 150e6, 20001)
    fig, ax = plt.subplots(figsize=(4.2, 3.24), constrained_layout=True)
    for i, name in enumerate(parts):
        p = PARTS[name]
        s = p.get("dr")
        cf = design_cf(res, name, R_F, tag)
        if not s or cf is None:
            continue
        ol, *_ = open_loop_model(p)
        nz = noise_inputs(p)
        C_T = C_D + C_PCB_NOM + p["c_cm"] + p["c_diff"]
        Z, _, _ = tm.tia_tf(np.array([f0]), ol, R_F, C_T, cf)
        VOL, VOH = s["swing_light"]
        lo_icr, hi_icr = s["icr"]
        v_slew = s["sr"] * 1e6 / (2 * np.pi * f0)
        base = tm.noise_components(band, R_F, C_T, cf, nz)
        S0 = np.trapezoid(base["total"], band)
        dr_c, dr_cancel = [], []
        for idc in i_dc:
            n_rms = np.sqrt(S0 + 2 * tm.Q_E * idc * (band[-1] - band[0]))
            # DC-coupled: centre the output if the input common-mode range allows it,
            # for both photodiode orientations, and keep the better one
            mid = 0.5 * (VOH + VOL)
            vref = min(mid + idc * R_F, min(hi_icr, VOH))          # photocurrent into the node
            vout = vref - idc * R_F
            head1 = max(0.0, min(VOH - vout, vout - VOL))
            vref = max(mid - idc * R_F, max(lo_icr, VOL))          # photocurrent out of the node
            vout = vref + idc * R_F
            head2 = max(0.0, min(VOH - vout, vout - VOL))
            v_pk = min(max(head1, head2), v_slew)
            dr_c.append(20 * np.log10(max(v_pk, 1e-9) / abs(Z[0]) / np.sqrt(2) / n_rms))
            v_pk2 = min(0.5 * (VOH - VOL), v_slew)
            dr_cancel.append(20 * np.log10(v_pk2 / abs(Z[0]) / np.sqrt(2) / n_rms))
        c = COLOR_CYCLE[i % len(COLOR_CYCLE)]
        ax.plot(i_dc * 1e3, dr_cancel, color=c, lw=LW, ls="-", label=f"{name}")
        ax.plot(i_dc * 1e3, dr_c, color=c, lw=LW, ls=DASH, label="_nolegend_")
    log_axes(ax, x=True, y=False)
    ax.set_xlim(1e-3, 10)
    ax.set_ylim(20, 90)
    ax.set_xlabel(r"DC photocurrent, $I_{\mathrm{DC}}$ (mA)")
    ax.set_ylabel("Dynamic range in 150 MHz (dB)")
    ax.plot([], [], color=COLORS["neutral"], lw=LW, ls="-", label="DC cancelled")
    ax.plot([], [], color=COLORS["neutral"], lw=LW, ls=DASH, label="DC coupled")
    ax.legend(loc="lower left", ncol=2, handlelength=2.2)
    export(fig, stem)


def main(results_dir: Path, fig_dir: Path, top: list[str]) -> None:
    configure_plot_style()
    fig_dir.mkdir(parents=True, exist_ok=True)
    res = json.load(open(results_dir / "results.json", encoding="utf-8"))
    top = [n for n in top if n in res]
    fig_noise(res, top, 2000.0, "flat", fig_dir / "fig02_input_noise_2k")
    fig_response(res, top, 2000.0, "flat", fig_dir / "fig03_transimpedance_2k")
    fig_landscape(fig_dir / "fig04_landscape_en_gbw")
    fig_bw_vs_penalty(res, 2000.0, "robust45", fig_dir / "fig05_bandwidth_vs_noise_penalty_2k")
    fig_dr_vs_idc(res, ["OPA855", "LMH6629 (COMP HI)", "OPA846", "OPA818"], 2000.0, "flat",
                  fig_dir / "fig06_dynamic_range_vs_idc_2k")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3].split(";") if len(sys.argv) > 3 else
         ["OPA855", "OPA858", "OPA955", "LMH6629 (COMP HI)", "OPA856", "OPA859", "OPA846", "OPA818"])
