"""Draw the TIA schematic with its parasitic elements (Figure 1 of the survey).

Usage: python make_circuit_figure.py <output_stem>
Writes <output_stem>.png (600 dpi) and <output_stem>.pdf.
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon, Circle

FONT_SIZE = 8.0
COLORS = {"primary": "#385C9E", "neutral": "#4D4D4D", "warm_accent": "#9E403D",
          "cool_accent": "#477A57", "annotation": "#767676", "text": "#272727",
          "axes": "#000000"}
LW = 1.1


def style():
    plt.rcParams.update({
        "font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans", "sans-serif"],
        "font.size": FONT_SIZE, "text.usetex": False, "mathtext.fontset": "cm",
        "pdf.fonttype": 42, "ps.fonttype": 42, "savefig.facecolor": "white",
        "savefig.bbox": "tight", "figure.facecolor": "white", "text.color": COLORS["text"]})


def wire(ax, pts, color=COLORS["axes"], ls="-"):
    pts = np.array(pts, dtype=float)
    ax.plot(pts[:, 0], pts[:, 1], color=color, lw=LW, ls=ls, solid_capstyle="round")


def dot(ax, x, y):
    ax.add_patch(Circle((x, y), 0.045, color=COLORS["axes"], zorder=5))


R_BODY, R_N, R_AMP = 0.84, 4, 0.13   # every resistor: same zig-zag body length, count and amplitude


def resistor_h(ax, x0, x1, y, color=COLORS["axes"]):
    """Horizontal resistor between x0 and x1: a fixed-size zig-zag body centred
    in the gap (n excursions above and n below the wire) and plain leads."""
    xc = 0.5 * (x0 + x1)
    xs = np.linspace(xc - R_BODY / 2, xc + R_BODY / 2, 2 * R_N + 2)
    ys = [y] + [y + (R_AMP if i % 2 else -R_AMP) for i in range(1, 2 * R_N + 1)] + [y]
    wire(ax, [(x0, y), (xs[0], y)], color)
    ax.plot(xs, ys, color=color, lw=LW)
    wire(ax, [(xs[-1], y), (x1, y)], color)


def resistor_v(ax, x, y0, y1, color=COLORS["axes"]):
    """Vertical resistor between y0 (top) and y1 (bottom), same body as resistor_h."""
    yc = 0.5 * (y0 + y1)
    ys = np.linspace(yc + R_BODY / 2, yc - R_BODY / 2, 2 * R_N + 2)
    xs = [x] + [x + (R_AMP if i % 2 else -R_AMP) for i in range(1, 2 * R_N + 1)] + [x]
    wire(ax, [(x, y0), (x, ys[0])], color)
    ax.plot(xs, ys, color=color, lw=LW)
    wire(ax, [(x, ys[-1]), (x, y1)], color)


def cap_v(ax, x, y_top, y_bot, w=0.22, gap=0.09, color=COLORS["axes"], ls="-"):
    """Vertical capacitor (plates horizontal) between y_top and y_bot."""
    ym = 0.5 * (y_top + y_bot)
    wire(ax, [(x, y_top), (x, ym + gap)], color, ls)
    wire(ax, [(x, ym - gap), (x, y_bot)], color, ls)
    ax.plot([x - w, x + w], [ym + gap] * 2, color=color, lw=1.6)
    ax.plot([x - w, x + w], [ym - gap] * 2, color=color, lw=1.6)


def cap_h(ax, x0, x1, y, h=0.22, gap=0.09, color=COLORS["axes"]):
    xm = 0.5 * (x0 + x1)
    wire(ax, [(x0, y), (xm - gap, y)], color)
    wire(ax, [(xm + gap, y), (x1, y)], color)
    ax.plot([xm - gap] * 2, [y - h, y + h], color=color, lw=1.6)
    ax.plot([xm + gap] * 2, [y - h, y + h], color=color, lw=1.6)


def ground(ax, x, y, color=COLORS["axes"]):
    for i, half in enumerate((0.20, 0.13, 0.06)):
        yy = y - 0.07 * i
        ax.plot([x - half, x + half], [yy, yy], color=color, lw=LW)


def label(ax, x, y, s, ha="left", va="center", color=COLORS["text"], **kw):
    ax.text(x, y, s, ha=ha, va=va, color=color, fontsize=FONT_SIZE, **kw)


def main(stem: Path) -> None:
    style()
    fig, ax = plt.subplots(figsize=(6.3, 3.4))
    ax.set_xlim(0.0, 12.6)
    ax.set_ylim(-0.25, 6.4)
    ax.set_aspect("equal")
    ax.axis("off")

    y_in = 2.9      # inverting-input node
    y_ni = 1.9      # non-inverting input
    x_amp = 7.0     # left edge of op-amp triangle
    # op-amp
    tri = Polygon([[x_amp, 1.35], [x_amp, 3.45], [x_amp + 1.9, 2.4]], closed=True,
                  fill=False, ec=COLORS["axes"], lw=LW)
    ax.add_patch(tri)
    label(ax, x_amp + 0.12, y_in, r"$-$", va="center")
    label(ax, x_amp + 0.12, y_ni, r"$+$", va="center")
    label(ax, x_amp + 0.55, 2.4, r"$A(s)$", va="center")
    x_out = x_amp + 1.9

    # input node wiring
    wire(ax, [(1.2, y_in), (x_amp, y_in)])
    for xd in (1.2, 2.25, 3.2, 4.55, 5.45, 6.2):
        dot(ax, xd, y_in)

    # balanced photodiode pair.  PD_A (upper): anode at the node, cathode to +V_B.
    # PD_B (lower): cathode at the node, anode to -V_B.  Both triangles point up
    # (anode below, cathode bar above).  The node receives i_1 - i_2.
    xpd = 1.2

    def photodiode(y_anode, y_cathode):
        ax.add_patch(Polygon([[xpd - 0.22, y_anode], [xpd + 0.22, y_anode], [xpd, y_cathode]],
                             closed=True, fill=False, ec=COLORS["axes"], lw=LW))
        ax.plot([xpd - 0.22, xpd + 0.22], [y_cathode, y_cathode], color=COLORS["axes"], lw=1.6)

    def light(y_c):
        """Two parallel incident-light arrows aimed at the diode centred at y_c,
        spaced perpendicular to their direction and stopping short of the symbol."""
        d = np.array([np.cos(np.radians(-40.0)), np.sin(np.radians(-40.0))])
        p = np.array([-d[1], d[0]])
        for k in (-1, 1):
            tip = np.array([xpd - 0.34, y_c]) + 0.13 * k * p
            ax.annotate("", xy=tip, xytext=tip - 0.55 * d,
                        arrowprops=dict(arrowstyle="->", lw=0.9, color=COLORS["warm_accent"],
                                        shrinkA=0, shrinkB=0))

    # PD_A above the node
    wire(ax, [(xpd, y_in), (xpd, 3.35)])
    photodiode(3.35, 3.72)
    wire(ax, [(xpd, 3.72), (xpd, 4.3)])
    label(ax, xpd, 4.4, r"$+V_B$ (decoupled)", ha="center", va="bottom")
    light(0.5 * (3.35 + 3.72))
    ax.annotate("", xy=(xpd + 0.38, 3.12), xytext=(xpd + 0.38, 3.77),
                arrowprops=dict(arrowstyle="->", lw=0.9, color=COLORS["primary"]))
    label(ax, xpd + 0.45, 3.5, r"$i_1$", color=COLORS["primary"])
    # PD_B below the node
    wire(ax, [(xpd, y_in), (xpd, 2.45)])
    photodiode(2.08, 2.45)
    wire(ax, [(xpd, 2.08), (xpd, 1.35)])
    label(ax, xpd, 1.22, r"$-V_B$ (decoupled)", ha="center", va="top")
    light(0.5 * (2.08 + 2.45))
    ax.annotate("", xy=(xpd + 0.38, 2.1), xytext=(xpd + 0.38, 2.75),
                arrowprops=dict(arrowstyle="->", lw=0.9, color=COLORS["primary"]))
    label(ax, xpd + 0.45, 2.42, r"$i_2$", color=COLORS["primary"])
    label(ax, 0.45, 3.25, "light", color=COLORS["warm_accent"], ha="center")

    # C_D, C_PCB, C_CM to ground
    for xc, name in ((2.25, r"$C_D$"), (3.2, r"$C_{\mathrm{PCB}}$"), (4.55, r"$C_{\mathrm{CM}}$")):
        cap_v(ax, xc, y_in, 1.55)
        ground(ax, xc, 1.55)
        label(ax, xc + 0.28, 2.2, name)
    # C_DIFF between inputs
    x_cd = 6.2
    cap_v(ax, x_cd, y_in, y_ni)
    label(ax, x_cd - 0.12, 1.72, r"$C_{\mathrm{DIFF}}$", ha="right", va="top")
    wire(ax, [(x_cd, y_ni), (x_amp, y_ni)])
    dot(ax, x_cd, y_ni)
    # non-inverting input to V_REF with decoupling
    wire(ax, [(x_cd, y_ni), (x_cd, 1.0), (5.45, 1.0)])
    label(ax, 5.35, 1.0, r"$V_{\mathrm{REF}}$ (AC ground)", ha="right")

    # feedback network: R_F and C_F in parallel
    x_fb_l, x_fb_r = 5.45, 9.6
    y_rf, y_cf = 4.35, 5.35
    wire(ax, [(x_fb_l, y_in), (x_fb_l, y_cf)])
    dot(ax, x_fb_l, y_rf)
    resistor_h(ax, x_fb_l, x_fb_r, y_rf)
    label(ax, 0.5 * (x_fb_l + x_fb_r), y_rf - 0.32, "$R_F$ = 1.5 or 2 kΩ", ha="center", va="top")
    wire(ax, [(x_fb_l, y_cf), (6.9, y_cf)])
    cap_h(ax, 6.9, 8.15, y_cf)
    wire(ax, [(8.15, y_cf), (x_fb_r, y_cf)])
    label(ax, 7.52, y_cf + 0.35, r"$C_F = C_{F,\mathrm{ext}} + C_{F,\mathrm{par}}$", ha="center", va="bottom")
    wire(ax, [(x_fb_r, y_cf), (x_fb_r, 2.4)])
    dot(ax, x_fb_r, y_rf)
    wire(ax, [(x_out, 2.4), (x_fb_r, 2.4)])
    dot(ax, x_fb_r, 2.4)

    # output: series back-termination and instrument
    resistor_h(ax, x_fb_r, 11.1, 2.4)
    label(ax, 10.35, 2.72, "$R_S$ = 50 Ω", ha="center", va="bottom")
    wire(ax, [(11.1, 2.4), (11.8, 2.4)])
    resistor_v(ax, 11.8, 2.4, 1.15)
    ground(ax, 11.8, 1.15)
    label(ax, 11.8, 0.8, "50 Ω input\n(or high-Z)", ha="center", va="top")
    label(ax, x_fb_r + 0.12, 2.15, r"$v_o$", va="top")

    # optional DC sink (Section 7)
    wire(ax, [(3.2, y_in), (3.2, 3.75), (3.9, 3.75)], color=COLORS["cool_accent"], ls=(0, (4, 2)))
    ax.add_patch(Circle((4.15, 3.75), 0.25, fill=False, ec=COLORS["cool_accent"], lw=LW, ls="--"))
    ax.annotate("", xy=(4.15, 3.55), xytext=(4.15, 3.95),
                arrowprops=dict(arrowstyle="->", lw=0.8, color=COLORS["cool_accent"]))
    label(ax, 4.15, 4.12, "optional DC\nservo (Sec. 7)", color=COLORS["cool_accent"],
          ha="center", va="bottom")

    # node annotation
    label(ax, 0.2, -0.05, r"$C_T = C_D + C_{\mathrm{PCB}} + C_{\mathrm{CM}} + C_{\mathrm{DIFF}}$,"
          r"   $C_D = C_{D,A} + C_{D,B}$", ha="left", va="bottom")
    fig.savefig(stem.with_suffix(".png"), dpi=600)
    fig.savefig(stem.with_suffix(".pdf"))
    plt.close(fig)


if __name__ == "__main__":
    main(Path(sys.argv[1]))
