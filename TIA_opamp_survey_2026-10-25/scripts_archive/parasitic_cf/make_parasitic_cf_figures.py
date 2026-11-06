"""Figures 39-44 of the note, Appendix G: the parasitic capacitance across the feedback resistor.

Usage: python make_parasitic_cf_figures.py [outdir]      (default: ../../figures)

fig38  an 0402 resistor on its land pattern, top view and cross-section, drawn to scale (Figure 39)
fig39  the idealised cross-section, its three regions, and the boundary conditions of each (Figure 40)
fig40  the coplanar pads: physical plane -> t-plane (Moebius map) -> rectangle (Schwarz-Christoffel
       map), with the analytic equipotentials and field lines of Eq. (G.23) (Figure 41)
fig41  the resistor body without the film: the analytic potential of Eq. (G.32), and the filled-slot
       construction of Eq. (G.28) (Figure 42)
fig42  pads over a ground plane: the half-strip and its image under zeta = cosh(pi q / h) (Eqs. (G.39)-(G.41);
       Figure 43)
fig43  the OPA855 pin geometry (DSG0008A land pattern) and the two bounding constructions of Eqs. (G.45)-(G.46)
       (Figure 44)

Every potential drawn here is computed from the closed-form maps of Appendix G, using
cf_parasitic_estimate.py (same folder) for the formulas and scipy.special.elliprf for the map
f(t) = -2 sqrt(t/m) R_F(1 - t/m, 1 - t, 1) (Section G.6 of the note).  Nothing is solved numerically on a mesh.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon, Rectangle
from scipy.special import elliprf

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cf_parasitic_estimate as est  # noqa: E402

FONT_SIZE = 8.0
COLORS = {
    "primary": "#385C9E", "neutral": "#4D4D4D", "warm_accent": "#9E403D", "cool_accent": "#477A57",
    "purple_accent": "#6B5B95", "teal_accent": "#3F7F82", "brown_accent": "#7D5C46",
    "grey_accent": "#6F6F6F", "highlight": "#EED671", "annotation": "#767676", "text": "#272727",
    "axes": "#000000", "background": "#FFFFFF",
}
# roles in these drawings
C_A = COLORS["warm_accent"]       # conductor A: output side (amplifier output / FB pin)
C_B = COLORS["primary"]           # conductor B: inverting-input side
C_FILM = COLORS["purple_accent"]  # resistive film
C_CU = COLORS["brown_accent"]     # copper pads
C_TERM = COLORS["grey_accent"]    # terminations
C_BOARD = COLORS["cool_accent"]   # FR-4 (light tint)
C_CUT = COLORS["annotation"]      # insulating cuts
LW = 1.5


def configure_plot_style() -> None:
    plt.rcParams.update({
        "figure.facecolor": COLORS["background"], "axes.facecolor": COLORS["background"],
        "axes.edgecolor": COLORS["axes"], "axes.labelcolor": COLORS["text"], "text.color": COLORS["text"],
        "xtick.color": COLORS["axes"], "ytick.color": COLORS["axes"], "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "DejaVu Sans", "sans-serif"], "font.size": FONT_SIZE,
        "axes.labelsize": FONT_SIZE, "axes.titlesize": FONT_SIZE, "xtick.labelsize": FONT_SIZE,
        "ytick.labelsize": FONT_SIZE, "legend.fontsize": FONT_SIZE, "axes.linewidth": 0.8,
        "axes.spines.top": True, "axes.spines.right": True, "xtick.top": True, "ytick.right": True,
        "xtick.direction": "in", "ytick.direction": "in", "legend.frameon": False, "axes.grid": False,
        "text.usetex": False, "mathtext.fontset": "cm", "axes.formatter.use_mathtext": True,
        "pdf.fonttype": 42, "ps.fonttype": 42, "savefig.facecolor": "white", "savefig.bbox": "tight",
        # equipotentials of both signs are drawn alike; field lines are drawn dashed explicitly
        "contour.negative_linestyle": "solid",
    })


def export(fig, outdir: Path, stem: str) -> None:
    fig.savefig(outdir / f"{stem}.png", dpi=600)
    fig.savefig(outdir / f"{stem}.pdf")
    plt.close(fig)


def panel_label(ax, text, x=0.01, y=0.99):
    ax.text(x, y, text, transform=ax.transAxes, ha="left", va="top", fontsize=FONT_SIZE)


def dim(ax, p0, p1, label, text_offset=(0.0, 0.0), color=COLORS["text"], ha="center", va="center"):
    """Dimension arrow between p0 and p1 with a label at the midpoint plus an offset (data units)."""
    ax.annotate("", xy=p1, xytext=p0, arrowprops=dict(arrowstyle="<->", lw=0.6, color=color, shrinkA=0, shrinkB=0))
    mx, my = 0.5 * (p0[0] + p1[0]) + text_offset[0], 0.5 * (p0[1] + p1[1]) + text_offset[1]
    ax.text(mx, my, label, ha=ha, va=va, fontsize=FONT_SIZE, color=color)


def sc_f(t, m):
    """The Schwarz-Christoffel map f(t) = int_0^t dtau / sqrt(tau (tau - m)(tau - 1)) in the upper
    half-plane, written with Carlson's integral (Section G.6 of the note): f = -2 sqrt(t/m) R_F(1 - t/m, 1 - t, 1)."""
    t = np.asarray(t, dtype=complex)
    return -2.0 * np.sqrt(t / m) * elliprf(1.0 - t / m, 1.0 - t, 1.0 + 0.0j)


def check_carlson_form():
    """Confirm the Carlson form against the direct path integral of the estimate script."""
    m = 0.3
    for t in (0.2 + 0.3j, -0.7 + 0.05j, 0.65 + 0.01j, 1.8 + 0.4j, 3.0 + 2.0j):
        a, b = complex(sc_f(t, m)), est.sc_map(t, m)
        assert abs(a - b) < 1e-7, (t, a, b)


# ------------------------------------------------------------------------------ geometry helpers
def nominal_0402():
    """The nominal 0402 of the estimate: body from the thick-film data sheets, pads from the
    IPC-7351-based table (both in cf_parasitic_estimate.py, sources in geometry_and_permittivity.md)."""
    c, p = est.CHIPS["0402"], est.PADS["0402"]
    a = c["a"][1]
    return dict(L=c["L"], W=c["W"], T=c["T"][1], a=a, g=c["L"] - 2 * a, w=p["w"], l=p["l"], s=p["s"])


# ------------------------------------------------------------------------- Figure 39
def fig_geometry(outdir: Path):
    G = nominal_0402()
    L, W, T, a, g, w, l, s = (G[k] for k in ("L", "W", "T", "a", "g", "w", "l", "s"))
    X = s / 2 + w
    t_cu, t_sol, t_term = 0.035, 0.02, 0.02
    z0 = t_cu + t_sol                     # bottom face of the body
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6.5, 5.4), constrained_layout=True,
                                   gridspec_kw=dict(height_ratios=[1.0, 0.95]))
    # (a) top view
    ax = ax1
    ax.add_patch(Rectangle((-1.15, -0.66), 2.3, 1.16, fc=C_BOARD, alpha=0.10, ec="none"))
    for sgn, col in ((1, C_A), (-1, C_B)):
        x_in, x_out = sgn * s / 2, sgn * X
        ax.add_patch(Rectangle((min(x_in, x_out), -l / 2), w, l, fc=C_CU, alpha=0.55, ec=C_CU, lw=0.8))
    ax.add_patch(Rectangle((-L / 2, -W / 2), L, W, fc="#F7F7F4", ec=COLORS["neutral"], lw=0.8))
    ax.add_patch(Rectangle((-g / 2, -W / 2 + 0.03), g, W - 0.06, fc=C_FILM, alpha=0.45, ec="none"))
    for sgn in (1, -1):
        x_in = sgn * g / 2
        ax.add_patch(Rectangle((min(x_in, sgn * L / 2), -W / 2), a, W, fc=C_TERM, alpha=0.75, ec=COLORS["neutral"], lw=0.6))
    dim(ax, (-L / 2, 0.36), (L / 2, 0.36), r"$L$", (0, 0.04))
    dim(ax, (-g / 2, -0.36), (g / 2, -0.36), r"$g$", (0, -0.045))
    dim(ax, (g / 2, -0.36), (L / 2, -0.36), r"$a$", (0, -0.045))
    dim(ax, (-X, -0.52), (-s / 2, -0.52), r"$w$", (0, -0.045))
    dim(ax, (-s / 2, -0.52), (s / 2, -0.52), r"$s$", (0, -0.045))
    dim(ax, (-0.98, -l / 2), (-0.98, l / 2), r"$l$", (-0.05, 0))
    dim(ax, (0.98, -W / 2), (0.98, W / 2), r"$W$", (0.06, 0))
    ax.text(0.0, 0.0, "film", ha="center", va="center", color="white", fontsize=FONT_SIZE)
    ax.text(X - 0.12, l / 2 - 0.06, "pad", ha="center", va="top", fontsize=FONT_SIZE)
    ax.annotate("termination", xy=(-L / 2 + a / 2, W / 2 - 0.05), xytext=(-0.88, 0.43), ha="center", va="center",
                fontsize=FONT_SIZE, arrowprops=dict(arrowstyle="-", lw=0.5, color=COLORS["annotation"]))
    ax.set_xlim(-1.15, 1.15)
    ax.set_ylim(-0.66, 0.5)
    ax.set_aspect("equal")
    ax.set_xlabel(r"$x$ (mm)")
    ax.set_ylabel(r"$y$ (mm)")
    panel_label(ax1, "(a)")
    # (b) cross-section through the resistor axis
    ax = ax2
    ax.add_patch(Rectangle((-1.15, -0.32), 2.3, 0.32, fc=C_BOARD, alpha=0.18, ec="none"))
    ax.text(-1.1, -0.29, "FR-4 board", ha="left", va="bottom", fontsize=FONT_SIZE)
    ax.text(1.1, 0.60, "air", ha="right", va="top", fontsize=FONT_SIZE)
    for sgn in (1, -1):
        x_in, x_out = sgn * s / 2, sgn * X
        ax.add_patch(Rectangle((min(x_in, x_out), 0), w, t_cu, fc=C_CU, ec="none"))
        ax.add_patch(Rectangle((min(sgn * g / 2, sgn * L / 2), t_cu), a, t_sol, fc=C_TERM, alpha=0.35, ec="none"))
        # solder fillet from the outer pad edge up the end face
        xf = sgn * L / 2
        ax.add_patch(Polygon([(xf, z0 + 0.6 * T), (xf, t_cu), (sgn * (X - 0.03), t_cu)], closed=True,
                             fc=C_TERM, alpha=0.35, ec="none"))
    ax.add_patch(Rectangle((-L / 2, z0), L, T, fc="#F7F7F4", ec=COLORS["neutral"], lw=0.8))
    ax.add_patch(Rectangle((-g / 2, z0 + T), g, 0.012, fc=C_FILM, ec="none"))
    for sgn in (1, -1):
        xe = sgn * L / 2
        xi = sgn * g / 2
        pts = [(xi, z0 + T), (xe, z0 + T), (xe, z0), (xi, z0)]
        xs, zs = zip(*pts)
        ax.plot(xs, zs, color=C_TERM, lw=2.2, solid_capstyle="butt")
    ax.text(0.0, z0 + T / 2, "alumina", ha="center", va="center", fontsize=FONT_SIZE)
    ax.text(0.0, z0 + T + 0.03, "film", ha="center", va="bottom", fontsize=FONT_SIZE, color=C_FILM)
    dim(ax, (L / 2 + 0.06, z0), (L / 2 + 0.06, z0 + T), r"$T$", (0.05, 0))
    dim(ax, (-g / 2, z0 + T + 0.10), (g / 2, z0 + T + 0.10), r"$g$", (0, 0.04))
    dim(ax, (-L / 2, z0 + T + 0.10), (-g / 2, z0 + T + 0.10), r"$a$", (0, 0.04))
    dim(ax, (-s / 2, -0.07), (s / 2, -0.07), r"$s$", (0, -0.045))
    dim(ax, (s / 2, -0.07), (X, -0.07), r"$w$", (0, -0.045))
    ax.plot([-0.5, 0.0], [-0.24, -0.24], color=COLORS["text"], lw=1.2)
    ax.text(-0.25, -0.225, "0.5 mm", ha="center", va="bottom", fontsize=FONT_SIZE)
    ax.set_xlim(-1.15, 1.15)
    ax.set_ylim(-0.32, 0.66)
    ax.set_aspect("equal")
    ax.set_xlabel(r"$x$ (mm)")
    ax.set_ylabel(r"$z$ (mm)")
    panel_label(ax2, "(b)")
    export(fig, outdir, "fig38_parasitic_cf_geometry_0402")


# ------------------------------------------------------------------------- Figure 40
def fig_regions(outdir: Path):
    G = nominal_0402()
    L, T, g, w, s = G["L"], G["T"], G["g"], G["w"], G["s"]
    X = s / 2 + w
    fig = plt.figure(figsize=(6.5, 3.9), constrained_layout=True)
    gs = fig.add_gridspec(2, 3, height_ratios=[1.25, 0.75])
    ax = fig.add_subplot(gs[0, :])
    # idealised cross-section with the three regions
    ax.add_patch(Rectangle((-1.2, -0.45), 2.4, 0.45, fc=C_BOARD, alpha=0.18, ec="none"))
    ax.add_patch(Rectangle((-L / 2, 0), L, T, fc="#F7F7F4", ec="none"))
    for sgn, col in ((1, C_A), (-1, C_B)):
        ax.plot([sgn * s / 2, sgn * X], [0, 0], color=col, lw=2.6, solid_capstyle="butt")
        ax.plot([sgn * g / 2, sgn * L / 2, sgn * L / 2, sgn * g / 2], [T, T, 0, 0], color=col, lw=2.6, solid_capstyle="butt")
    ax.plot([-g / 2, g / 2], [T, T], color=C_FILM, lw=2.6, solid_capstyle="butt")
    ax.plot([-1.2, -X], [0, 0], color=C_CUT, lw=1.0, ls=(0, (5, 2)))
    ax.plot([X, 1.2], [0, 0], color=C_CUT, lw=1.0, ls=(0, (5, 2)))
    gap = min(g, s)          # the cut runs only where neither a pad nor a bottom wrap lies
    ax.plot([-gap / 2, gap / 2], [0, 0], color=C_CUT, lw=1.0, ls=(0, (5, 2)))
    ax.text(0, -0.25, r"region I: board, $\varepsilon_\mathrm{pcb}$", ha="center", va="center")
    ax.text(0, T / 2, "region II:\nblock, $\\varepsilon_\\mathrm{al}$", ha="center", va="center")
    ax.text(0, T + 0.22, r"region III: air, $\varepsilon = 1$", ha="center", va="center")
    ax.text(X + 0.02, 0.05, r"A, $+V/2$", color=C_A, ha="left", va="bottom")
    ax.text(-X - 0.02, 0.05, r"B, $-V/2$", color=C_B, ha="right", va="bottom")
    ax.text(0.0, T + 0.05, "film", color=C_FILM, ha="center", va="bottom")
    ax.text(1.18, -0.03, "cut", color=C_CUT, ha="right", va="top")
    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-0.45, T + 0.38)
    ax.set_aspect("equal")
    ax.set_xlabel(r"$x$ (mm)")
    ax.set_ylabel(r"$z$ (mm)")
    panel_label(ax, "(a)")
    # (b) region I as a half-plane problem
    ax = fig.add_subplot(gs[1, 0])
    ax.add_patch(Rectangle((-1.2, -0.9), 2.4, 0.9, fc=C_BOARD, alpha=0.18, ec="none"))
    ax.plot([-1.2, -X], [0, 0], color=C_CUT, lw=1.0, ls=(0, (5, 2)))
    ax.plot([-s / 2, s / 2], [0, 0], color=C_CUT, lw=1.0, ls=(0, (5, 2)))
    ax.plot([X, 1.2], [0, 0], color=C_CUT, lw=1.0, ls=(0, (5, 2)))
    ax.plot([s / 2, X], [0, 0], color=C_A, lw=2.6, solid_capstyle="butt")
    ax.plot([-X, -s / 2], [0, 0], color=C_B, lw=2.6, solid_capstyle="butt")
    ax.text(0, -0.45, r"$\varepsilon_\mathrm{pcb}$", ha="center", va="center")
    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-0.9, 0.25)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    panel_label(ax, "(b)")
    # (c) region II as a rectangle
    ax = fig.add_subplot(gs[1, 1])
    ax.add_patch(Rectangle((-L / 2, 0), L, T, fc="#F7F7F4", ec="none"))
    for sgn, col in ((1, C_A), (-1, C_B)):
        ax.plot([sgn * g / 2, sgn * L / 2, sgn * L / 2, sgn * g / 2], [T, T, 0, 0], color=col, lw=2.6, solid_capstyle="butt")
    ax.plot([-g / 2, g / 2], [T, T], color=C_FILM, lw=2.6, solid_capstyle="butt")
    ax.plot([-g / 2, g / 2], [0, 0], color=C_CUT, lw=1.0, ls=(0, (5, 2)))
    ax.plot([g / 2, g / 2], [0, T], color=COLORS["neutral"], lw=0.8, ls=":")
    ax.plot([-g / 2, -g / 2], [0, T], color=COLORS["neutral"], lw=0.8, ls=":")
    ax.text(0, T / 2, r"$\varepsilon_\mathrm{al}$", ha="center", va="center")
    ax.set_xlim(-0.65, 0.65)
    ax.set_ylim(-0.15, T + 0.15)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    panel_label(ax, "(c)")
    # (d) region III flattened
    ax = fig.add_subplot(gs[1, 2])
    ax.plot([-1.2, -X], [0, 0], color=C_CUT, lw=1.0, ls=(0, (5, 2)))
    ax.plot([X, 1.2], [0, 0], color=C_CUT, lw=1.0, ls=(0, (5, 2)))
    ax.plot([g / 2, X], [0, 0], color=C_A, lw=2.6, solid_capstyle="butt")
    ax.plot([-X, -g / 2], [0, 0], color=C_B, lw=2.6, solid_capstyle="butt")
    ax.plot([-g / 2, g / 2], [0, 0], color=C_FILM, lw=2.6, solid_capstyle="butt")
    ax.text(0, 0.45, r"$\varepsilon = 1$", ha="center", va="center")
    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-0.25, 0.9)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    panel_label(ax, "(d)")
    export(fig, outdir, "fig39_parasitic_cf_regions")


# ------------------------------------------------------------------------- Figure 41
def fig_cps_maps(outdir: Path):
    G = nominal_0402()
    w, s = G["w"], G["s"]
    x1, x2, x3, x4 = -s / 2 - w, -s / 2, s / 2, s / 2 + w
    m = est.parameter_from_points(x1, x2, x3, x4)
    Km, K1 = est.K(m), est.K_of_1_minus(m)
    T = lambda z: (z - x1) * (x3 - x4) / ((z - x4) * (x3 - x1))
    phi_levels = np.array([-0.4, -0.3, -0.2, -0.1, 0.0, 0.1, 0.2, 0.3, 0.4])
    psi_levels = np.linspace(0.05, 0.95, 10)
    fig, axs = plt.subplots(1, 3, figsize=(6.5, 2.5), constrained_layout=True, gridspec_kw=dict(width_ratios=[1.25, 1.0, 1.0]))
    # (a) physical plane, both half-spaces (the same potential solves both, Section G.7.3)
    ax = axs[0]
    xx = np.linspace(-1.6, 1.6, 641)
    yy = np.linspace(1e-4, 1.2, 241)
    Xg, Yg = np.meshgrid(xx, yy)
    Fz = sc_f(T(Xg + 1j * Yg), m)
    phi = -0.5 - Fz.imag / (2 * K1)
    psi = -Fz.real / (2 * Km)
    for sgn in (1, -1):
        ax.contour(Xg, sgn * Yg, phi, levels=phi_levels, colors=COLORS["neutral"], linewidths=0.6)
        ax.contour(Xg, sgn * Yg, psi, levels=psi_levels, colors=COLORS["annotation"], linewidths=0.5, linestyles=[(0, (3, 2))])
    ax.add_patch(Rectangle((-1.6, -1.2), 3.2, 1.2, fc=C_BOARD, alpha=0.12, ec="none", zorder=0))
    ax.plot([x3, x4], [0, 0], color=C_A, lw=2.6, solid_capstyle="butt")
    ax.plot([x1, x2], [0, 0], color=C_B, lw=2.6, solid_capstyle="butt")
    ax.set_xlim(-1.6, 1.6)
    ax.set_ylim(-1.2, 1.2)
    ax.set_aspect("equal")
    ax.set_xlabel(r"$x$ (mm)")
    ax.set_ylabel(r"$z$ (mm)")
    panel_label(ax, "(a)")
    # (b) t-plane
    ax = axs[1]
    tr = np.linspace(-1.5, 2.5, 401)
    ti = np.linspace(1e-4, 2.0, 201)
    TR, TI = np.meshgrid(tr, ti)
    Ft = sc_f(TR + 1j * TI, m)
    ax.contour(TR, TI, -0.5 - Ft.imag / (2 * K1), levels=phi_levels, colors=COLORS["neutral"], linewidths=0.6)
    ax.contour(TR, TI, -Ft.real / (2 * Km), levels=psi_levels, colors=COLORS["annotation"], linewidths=0.5, linestyles=[(0, (3, 2))])
    ax.plot([0, m], [0, 0], color=C_B, lw=2.6, solid_capstyle="butt")
    ax.plot([1, 2.5], [0, 0], color=C_A, lw=2.6, solid_capstyle="butt")
    for xv, lab in ((0, r"$0$"), (m, r"$m$"), (1, r"$1$")):
        ax.plot([xv], [0], "o", ms=2.5, color=COLORS["text"])
        ax.text(xv + {0: -0.05, 1: 0.0}.get(xv, 0.06), -0.08, lab, ha={0: "right", 1: "center"}.get(xv, "left"), va="top")
    ax.set_xlim(-1.5, 2.5)
    ax.set_ylim(-0.3, 2.0)
    ax.set_aspect("equal")
    ax.set_xlabel(r"$\mathrm{Re}\,t$")
    ax.set_ylabel(r"$\mathrm{Im}\,t$")
    panel_label(ax, "(b)")
    # (c) rectangle
    ax = axs[2]
    for p in phi_levels:
        yv = -2 * K1 * (p + 0.5)
        ax.plot([-2 * Km, 0], [yv, yv], color=COLORS["neutral"], lw=0.6)
    for q in psi_levels:
        ax.plot([-2 * Km * q, -2 * Km * q], [-2 * K1, 0], color=COLORS["annotation"], lw=0.5, ls=(0, (3, 2)))
    ax.plot([-2 * Km, 0], [0, 0], color=C_B, lw=2.6, solid_capstyle="butt")
    ax.plot([-2 * Km, 0], [-2 * K1, -2 * K1], color=C_A, lw=2.6, solid_capstyle="butt")
    ax.plot([-2 * Km, -2 * Km], [-2 * K1, 0], color=C_CUT, lw=1.0, ls=(0, (5, 2)))
    ax.plot([0, 0], [-2 * K1, 0], color=C_CUT, lw=1.0, ls=(0, (5, 2)))
    ax.text(-Km, 0.12, r"$2K(m)$", ha="center", va="bottom")
    ax.text(0.12, -K1, r"$2K(1-m)$", ha="left", va="center", rotation=90)
    ax.set_xlim(-2 * Km - 0.3, 0.75)
    ax.set_ylim(-2 * K1 - 0.3, 0.75)
    ax.set_aspect("equal")
    ax.set_xlabel(r"$\mathrm{Re}\,f$")
    ax.set_ylabel(r"$\mathrm{Im}\,f$")
    panel_label(ax, "(c)")
    export(fig, outdir, "fig40_parasitic_cf_cps_maps")
    return m


# ------------------------------------------------------------------------- Figure 42
def fig_body(outdir: Path):
    G = nominal_0402()
    L, T, g = G["L"], G["T"], G["g"]
    d = est.block_without_film(L, T, g)
    mb, sg = d["m_b"], d["sn"]
    t_d, t_c = mb * sg ** 2, 1.0 / sg ** 2
    m2 = 1.0 - t_d / t_c
    Kb, K1b = est.K(mb), est.K_of_1_minus(mb)
    K12 = est.K_of_1_minus(m2)
    r = np.logspace(-6, 6, 900)
    th = np.linspace(1e-5, math.pi - 1e-5, 500)
    Rg, THg = np.meshgrid(r, th)
    t = Rg * np.exp(1j * THg)
    Fb = sc_f(t, mb)
    x = -Fb.real * (L / 2) / (2 * Kb)
    z = T + Fb.imag * T / (2 * K1b)
    F2 = sc_f((t_c - t_d) / (t_c - t), m2)
    phi = 0.5 * (-F2.imag) / (2 * K12)           # 0 on the symmetry line, 1/2 on the termination
    fig, ax = plt.subplots(figsize=(4.2, 2.0), constrained_layout=True)
    levels = np.linspace(0.05, 0.45, 9)
    ax.contour(x, z, phi, levels=levels, colors=COLORS["neutral"], linewidths=0.6)
    ax.contour(-x, z, -phi, levels=-levels[::-1], colors=COLORS["neutral"], linewidths=0.6)
    ax.plot([0, 0], [0, T], color=COLORS["neutral"], lw=0.6)
    for sgn, col in ((1, C_A), (-1, C_B)):
        ax.plot([sgn * g / 2, sgn * L / 2, sgn * L / 2, sgn * g / 2], [T, T, 0, 0], color=col, lw=2.6, solid_capstyle="butt")
        ax.plot([sgn * g / 2, sgn * g / 2], [0, T], color=col, lw=0.8, ls=":")
    ax.plot([-g / 2, g / 2], [T, T], color=C_CUT, lw=1.0, ls=(0, (5, 2)))
    ax.plot([-g / 2, g / 2], [0, 0], color=C_CUT, lw=1.0, ls=(0, (5, 2)))
    ax.set_xlim(-L / 2 - 0.05, L / 2 + 0.05)
    ax.set_ylim(-0.05, T + 0.05)
    ax.set_aspect("equal")
    ax.set_xlabel(r"$x$ (mm)")
    ax.set_ylabel(r"$z$ (mm)")
    export(fig, outdir, "fig41_parasitic_cf_body_without_film")
    return d


# ------------------------------------------------------------------------- Figure 44
def fig_pins(outdir: Path):
    fig = plt.figure(figsize=(6.5, 3.4), constrained_layout=True)
    gs = fig.add_gridspec(2, 2, width_ratios=[1.15, 1.0])
    ax = fig.add_subplot(gs[:, 0])
    pitch, b, plen = 0.5, 0.25, 0.5
    xc = -0.95
    ax.add_patch(Rectangle((-1.0, -1.0), 2.0, 2.0, fc=COLORS["neutral"], alpha=0.06, ec=COLORS["neutral"], lw=0.8, ls=(0, (5, 2))))
    ax.add_patch(Rectangle((-0.45, -0.8), 0.9, 1.6, fc=C_CU, alpha=0.30, ec=C_CU, lw=0.6))
    ax.text(0.0, 0.0, "thermal pad\n(VS$-$)", ha="center", va="center")
    names = {1: "FB", 2: "NC", 3: r"IN$-$", 4: "IN+"}
    cols = {1: C_A, 2: COLORS["neutral"], 3: C_B, 4: COLORS["neutral"]}
    for k, yv in ((1, 0.75), (2, 0.25), (3, -0.25), (4, -0.75)):
        ax.add_patch(Rectangle((xc - plen / 2, yv - b / 2), plen, b, fc=cols[k], alpha=0.55 if k in (1, 3) else 0.25, ec=cols[k], lw=0.6))
        ax.text(xc, yv, str(k), ha="center", va="center")
        ax.text(0.52, yv, names[k], ha="left", va="center")
    # 0402 feedback resistor alongside pins 1-3, as in the datasheet's layout example
    xr = -1.85
    for yv, col in ((0.75, C_A), (-0.25, C_B)):
        ax.add_patch(Rectangle((xr - 0.30, yv - 0.25), 0.60, 0.50, fc=C_CU, alpha=0.55, ec=C_CU, lw=0.6))
        ax.plot([xr + 0.30, xc - plen / 2], [yv, yv], color=C_CU, lw=3.0, alpha=0.55, solid_capstyle="butt")
    ax.add_patch(Rectangle((xr - 0.25, 0.25 - 0.5), 0.5, 1.0, fc="#F7F7F4", ec=COLORS["neutral"], lw=0.8))
    ax.text(xr, 0.25, r"$R_F$", ha="center", va="center")
    ax.plot([-2.25, -1.75], [-1.12, -1.12], color=COLORS["text"], lw=1.2)
    ax.text(-2.0, -1.10, "0.5 mm", ha="center", va="bottom")
    ax.set_xlim(-2.35, 1.05)
    ax.set_ylim(-1.2, 1.15)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    panel_label(ax, "(a)")
    # (b) cross-section through pins 1-3, middle pin removed
    def section(ax, wall: bool, label: str):
        ax.add_patch(Rectangle((-1.0, -0.5), 2.0, 0.5, fc=C_BOARD, alpha=0.18, ec="none"))
        ax.add_patch(Rectangle((-1.0, 0.0), 2.0, 0.5, fc=COLORS["neutral"], alpha=0.06, ec="none"))
        ax.plot([-pitch - b / 2, -pitch + b / 2], [0, 0], color=C_A, lw=2.6, solid_capstyle="butt")
        ax.plot([pitch - b / 2, pitch + b / 2], [0, 0], color=C_B, lw=2.6, solid_capstyle="butt")
        if wall:
            ax.add_patch(Rectangle((-b / 2, -0.5), b, 1.0, fc=COLORS["neutral"], alpha=0.35, ec=COLORS["neutral"], lw=0.6))
            ax.plot([-b / 2 + (-b / 2 - (-pitch + b / 2)), -b / 2 + (-b / 2 - (-pitch - b / 2))], [0, 0],
                    color=C_A, lw=1.2, ls=(0, (2, 1.5)), solid_capstyle="butt")
        ax.text(-pitch, 0.04, "pin 1", ha="center", va="bottom", color=C_A)
        ax.text(pitch, 0.04, "pin 3", ha="center", va="bottom", color=C_B)
        if wall:
            ax.text(0.0, 0.42, "floating wall", ha="center", va="top")
            ax.text(0.25, -0.04, "image", ha="center", va="top", color=C_A)
        ax.text(0.95, 0.45, "mould", ha="right", va="top")
        ax.text(0.95, -0.45, "board", ha="right", va="bottom")
        ax.set_xlim(-1.0, 1.0)
        ax.set_ylim(-0.5, 0.5)
        ax.set_aspect("equal")
        ax.set_xticks([])
        ax.set_yticks([])
        panel_label(ax, label)
    section(fig.add_subplot(gs[0, 1]), False, "(b)")
    section(fig.add_subplot(gs[1, 1]), True, "(c)")
    export(fig, outdir, "fig43_parasitic_cf_pins_dsg")


# ------------------------------------------------------------------------- Figure 43
def fig_plane(outdir: Path):
    G = nominal_0402()
    w, s = G["w"], G["s"]
    h = 0.2
    u1, u2 = math.cosh(math.pi * s / (2 * h)), math.cosh(math.pi * (s / 2 + w) / h)
    # odd excitation: electrodes (-inf, 1] at 0 V and [u1, u2] at 1/2
    x2, x3, x4 = 1.0, u1, u2
    mo = (x4 - x3) / (x4 - x2)
    Ko, K1o = est.K(mo), est.K_of_1_minus(mo)
    xx = np.linspace(1e-4, 1.4, 561)
    dd = np.linspace(1e-5, h - 1e-5, 161)
    Xg, Dg = np.meshgrid(xx, dd)
    zeta = np.cosh(math.pi * (Xg + 1j * Dg) / h)
    Tm = (x4 - x3) / (x4 - zeta)
    F = sc_f(Tm, mo)
    phi = 0.5 * (-F.imag) / (2 * K1o)
    fig, axs = plt.subplots(2, 1, figsize=(6.5, 3.0), constrained_layout=True, gridspec_kw=dict(height_ratios=[1.0, 0.9]))
    ax = axs[0]
    ax.add_patch(Rectangle((-1.4, 0), 2.8, h, fc=C_BOARD, alpha=0.18, ec="none"))
    lev = np.linspace(0.05, 0.45, 9)
    ax.contour(Xg, Dg, phi, levels=lev, colors=COLORS["neutral"], linewidths=0.6)
    ax.contour(-Xg, Dg, -phi, levels=-lev[::-1], colors=COLORS["neutral"], linewidths=0.6)
    ax.plot([-1.4, 1.4], [h, h], color=COLORS["text"], lw=2.6)
    ax.plot([s / 2, s / 2 + w], [0, 0], color=C_A, lw=2.6, solid_capstyle="butt")
    ax.plot([-s / 2 - w, -s / 2], [0, 0], color=C_B, lw=2.6, solid_capstyle="butt")
    ax.plot([0, 0], [0, h], color=COLORS["neutral"], lw=0.8, ls=":")
    ax.text(1.38, h - 0.012, "ground plane", ha="right", va="bottom")
    ax.set_xlim(-1.4, 1.4)
    ax.set_ylim(h + 0.02, -0.06)
    ax.set_aspect("equal")
    ax.set_xlabel(r"$x$ (mm)")
    ax.set_ylabel("depth (mm)")
    panel_label(ax, "(a)")
    ax = axs[1]
    # schematic of the zeta axis (not to scale beyond the marked points; log-like compression)
    def squash(v):
        return np.sign(v) * np.log1p(np.abs(v))
    segs = [((-200, -1), COLORS["text"], "-", 2.6), ((-1, 1), COLORS["neutral"], ":", 1.2),
            ((1, u1), C_CUT, (0, (5, 2)), 1.0), ((u1, u2), C_A, "-", 2.6), ((u2, 30 * u2), C_CUT, (0, (5, 2)), 1.0)]
    for (a_, b_), col, ls, lw in segs:
        ax.plot(squash(np.array([a_, b_])), [0, 0], color=col, ls=ls, lw=lw, solid_capstyle="butt")
    for v, lab in ((-1, r"$-1$"), (1, r"$1$"), (u1, r"$u_1$"), (u2, r"$u_2$")):
        ax.plot([squash(v)], [0], "o", ms=2.5, color=COLORS["text"])
        ax.text(squash(v), -0.25, lab, ha="center", va="top")
    ax.text(squash(-20), 0.25, "plane", ha="center", va="bottom")
    ax.text(0.0, 0.25, "wall", ha="center", va="bottom")
    ax.text(squash(math.sqrt(u1 * u2)), 0.25, "pad A", ha="center", va="bottom", color=C_A)
    ax.set_xlim(squash(-200), squash(30 * u2))
    ax.set_ylim(-0.9, 0.9)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlabel(r"$\mathrm{Re}\,\zeta$ (compressed scale)")
    panel_label(ax, "(b)")
    export(fig, outdir, "fig42_parasitic_cf_plane_map")


def main():
    outdir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2] / "figures"
    outdir.mkdir(parents=True, exist_ok=True)
    configure_plot_style()
    check_carlson_form()
    fig_geometry(outdir)
    fig_regions(outdir)
    m = fig_cps_maps(outdir)
    d = fig_body(outdir)
    fig_pins(outdir)
    fig_plane(outdir)
    print("figures written to", outdir, "| CPS m =", round(m, 6), "| body m_b =", round(d["m_b"], 6))


if __name__ == "__main__":
    main()
