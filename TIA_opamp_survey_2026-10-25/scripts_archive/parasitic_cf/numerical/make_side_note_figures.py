"""Figures 1-3 of the side note TIA_feedback_layouts, from the recorded results and the layout builders.

Usage:  python make_side_note_figures.py [figure numbers ...] [--out <folder>]
        (default: all three, into TIA_feedback_layouts/figures of the repository)

Why this script exists
----------------------
The side note on eight-lead packages and guarded layouts shows the layouts it computes and the
response of the guarded ones.  Every number drawn here comes from the JSON records in
data/parasitic_cf/numerical/ (eight_lead_3d.json from g_eight_lead_3d.py, opa846_3d.json from
g_opa846_3d.py, guard_ladder.json from g_guard_ladder.py), and every layout from the builders those
scripts used, so a figure cannot disagree with the numbers in the text.  No mesh is made and nothing
is solved.

  Figure 1  The OPA846 in SO-8: the three layouts in three dimensions, and C_F of each beside the
            SOT-23-5 layouts of Section G.14.10 of the balanced-photodiode note.
  Figure 2  The high-gain layouts without a guard: OPA637 in SOIC-8 and LMC6001 in PDIP-8.
  Figure 3  The guarded layouts: LMC6001 in PDIP-8 with guard rings, and ADA4530-1 and LMP7721 in
            SOIC-8 with the guards of their data sheets.
  Figure 4  The guarded networks against frequency (g_guard_ladder.draw).

The three-dimensional panels use make_numerical_figures.iso_axes, which explains the two Matplotlib
behaviours it works around, pcbcap.plotting.draw_iso, and the axis tidying of
pcbcap.plotting.draw_views (_tidy_view_axes: at most four ticks per axis, the bare axis letters with
the unit stated once below the panels, the box at 0.8 of its cell so that the z label stays inside).
Each layout is seen from the side that shows its feedback network: the parts on the solder side of
the PDIP-8 boards from below, the flat SOIC-8 layouts with the resistor beside the package from 35
degrees above.  Style: the project's plotting guide, through pcbcap.plotting (Arial 8 pt,
restrained palette, 600-dpi PNG plus PDF with editable text).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[4] / "pcbcap"))
sys.path.insert(0, str(HERE.parent))

import matplotlib                                                 # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                   # noqa: E402
import numpy as np                                                # noqa: E402

import g_eight_lead_3d as g8                                      # noqa: E402
import g_guard_ladder as gl                                       # noqa: E402
from make_numerical_figures import iso_axes, panel                # noqa: E402
from pcbcap import plotting as pl                                 # noqa: E402

REPO = HERE.parents[4]
DATA = HERE.parents[3] / "data" / "parasitic_cf" / "numerical"
C = pl.COLORS


def load(name: str) -> dict:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def union_window(layouts):
    """The smallest window that holds pl.auto_window of every layout, so that panels share a scale."""
    wins = [pl.auto_window(lay) for lay in layouts]
    return tuple((min(w[a][0] for w in wins), max(w[a][1] for w in wins)) for a in range(3))


def bar_labels(ax, xs, vals, fmt="{:.0f}", dy=2.0):
    for x, v in zip(xs, vals):
        if np.isfinite(v):
            ax.text(x, v + dy, fmt.format(v), ha="center", va="bottom")


def draw_layout(ax, lay, window, elev: float = 24.0, azim: float = -58.0, zoom: float = 0.8) -> None:
    """draw_iso with draw_views' axis tidying (module docstring).  ``zoom`` replaces the tidying's
    0.8: a figure whose cells are wider than the sheets' leaves its labels room for a larger box, and
    each value below was chosen by eye on the rendered figure, as the largest without a clash."""
    pl.draw_iso(ax, lay, window, elev=elev, azim=azim)
    pl._tidy_view_axes(ax, elev, azim)
    ax.set_box_aspect([hi - lo for lo, hi in window], zoom=zoom)
    # A 3-D axes paints a white background over its whole cell, which would hide the tick numbers of
    # the panel to its left; a transparent background shows them (make_numerical_figures.fig51).
    ax.set_facecolor("none")


# ================================================================================================
SO8 = ("opa846_so8_double_sided_0402", "opa846_so8_vias_under_0402", "opa846_so8_under_body_0402")
SO8_NAMES = {"opa846_so8_double_sided_0402": "$R_F$ under the package,\nvias in the pads",
             "opa846_so8_vias_under_0402": "$R_F$ under the package,\nvias under the body",
             "opa846_so8_under_body_0402": "$R_F$ beyond the package,\ntraces under the body"}
SOT23_MATCH = {"opa846_so8_double_sided_0402": "double_sided_0402",     # the SOT-23-5 counterparts
               "opa846_so8_under_body_0402": "under_body_0402"}


def fig1(out: Path):
    """The OPA846 in SO-8: three layouts, and C_F of each beside the SOT-23-5 counterparts."""
    eight, sot = load("eight_lead_3d.json"), load("opa846_3d.json")
    fig = plt.figure(figsize=(6.5, 4.0), constrained_layout=True)
    # The narrow fourth column keeps room for the z-axis label of panel (c), which the layout does
    # not see because the 3-D axes are kept out of it (make_numerical_figures.iso_axes).
    gs = fig.add_gridspec(2, 4, height_ratios=[0.9, 0.65], width_ratios=[1.0, 1.0, 1.0, 0.25])
    ax = fig.add_subplot(gs[1, :])          # the 2-D panel first (iso_axes, point 1)
    xs = np.arange(len(SO8))
    so8 = [eight[k]["table"]["C_F"] for k in SO8]
    s23 = [sot[SOT23_MATCH[k]]["table"]["refine_5.66"]["C_F"] if k in SOT23_MATCH else np.nan for k in SO8]
    ax.bar(xs - 0.18, so8, width=0.34, color=C["primary"], label="SO-8")
    ax.bar(xs + 0.18, s23, width=0.34, color=C["grey_accent"], label="SOT-23-5, the companion's Table G.14")
    bar_labels(ax, xs - 0.18, so8)
    bar_labels(ax, xs + 0.18, s23)
    ax.set_xticks(xs)
    ax.set_xticklabels([f"layout ({'abc'[k]})" for k in range(len(SO8))])
    ax.set_xlim(-0.6, len(xs) - 0.4)
    ax.set_ylim(0, 1.45 * max(v for v in so8 + s23 if np.isfinite(v)))
    ax.set_ylabel(r"$C_{F,\mathrm{par}}$ (fF)")
    ax.legend(loc="upper right", ncol=2)
    panel(ax, "(d)")
    lays = [g8.build(k) for k in SO8]
    win = union_window(lays)
    cells = [(gs[0, k], f"({'abc'[k]}) {SO8_NAMES[name]}") for k, name in enumerate(SO8)]
    axes = iso_axes(fig, cells)
    for k, (a3, lay) in enumerate(zip(axes, lays)):
        draw_layout(a3, lay, win, zoom=1.0)
        if k < len(axes) - 1:                # one height scale: only the last panel carries the z axis
            a3.set_zticklabels([])
            a3.set_zlabel("")
    pl.export(fig, out / "fig1_opa846_so8")


# ================================================================================================
# (layout, panel title, elevation of the view in degrees, negative from below; whether the z axis
# keeps its letter: on the flat SOIC-8 layouts seen from 35 degrees Matplotlib puts it on the board,
# and in a row of three the first panel's letter, beyond its tick numbers, reaches the second panel)
UNGUARDED = (("opa637_so8_bottom_0805", "OPA637 in SOIC-8, 0805 under the\npackage on the bottom side, from below", -28.0, True),
             ("lmc6001_dip8_bottom_1206", "LMC6001 in PDIP-8, 1206 on the\nsolder side, from below", -28.0, True))
GUARDED = (("lmc6001_dip8_bottom_guard_1206", "LMC6001 in PDIP-8 with guard\nrings joined to pin 3, from below", -28.0, False),
           ("ada4530_so8_1206", "ADA4530-1 in SOIC-8, 1206 and\nthe guard of its data sheet", 35.0, False),
           ("lmp7721_so8_1206", "LMP7721 in SOIC-8, 1206 and\nthe guard of its data sheet", 35.0, False))


def layout_row(out: Path, cases, stem: str, height: float, zoom: float) -> None:
    """One row of three-dimensional panels, each layout in its own window (pl.auto_window) and seen
    from its own elevation."""
    fig = plt.figure(figsize=(6.5, height), constrained_layout=True)
    gs = fig.add_gridspec(1, len(cases))
    axes = iso_axes(fig, [(gs[0, k], f"({'abc'[k]}) {title}") for k, (_, title, _, _) in enumerate(cases)])
    for a3, (name, _, elev, zletter) in zip(axes, cases):
        lay = g8.build(name)
        draw_layout(a3, lay, pl.auto_window(lay), elev=elev, zoom=zoom)
        if not zletter:
            a3.set_zlabel("")
    pl.export(fig, out / stem)


def fig2(out: Path):
    """The high-gain layouts without a guard."""
    layout_row(out, UNGUARDED, "fig2_high_gain_layouts", 2.8, zoom=1.1)


def fig3(out: Path):
    """The guarded high-gain layouts."""
    layout_row(out, GUARDED, "fig3_guarded_layouts", 2.6, zoom=0.85)


def fig4(out: Path):
    """The guarded networks against frequency; g_guard_ladder.draw draws it."""
    gl.response(str(DATA / "guard_ladder.json"), figure=str(out / "fig4_guard_response"))


FIGURES = {1: fig1, 2: fig2, 3: fig3, 4: fig4}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("numbers", nargs="*", type=int)
    ap.add_argument("--out", default=str(REPO / "TIA_feedback_layouts" / "figures"))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    pl.use_style()
    for k in a.numbers or sorted(FIGURES):
        FIGURES[k](out)
        print("figure", k, "done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
