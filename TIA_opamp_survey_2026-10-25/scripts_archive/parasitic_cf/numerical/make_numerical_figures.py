"""Figures 45-52 of Appendix G (the numerical section; files fig44-fig51), from the recorded results.

Usage:  python make_numerical_figures.py [file numbers 44-51 ...]      (default: all)

Why this script exists
----------------------
The numerical section of Appendix G shows the three-dimensional model, its field, its validation,
its convergence and its results.  Every figure here is drawn from
  * the JSON records written by checks (pcbcap.checks), g_closed_forms_2d.py, g_resistor_3d.py and
    g_opa846_3d.py in data/parasitic_cf/numerical/ (checks.json, closed_forms_2d.json,
    resistor_3d.json, opa846_3d.json), and
  * the same layout builders those scripts used,
so a figure cannot disagree with the numbers in the text.  Only Figures 44c and 45 need a field
solution; they solve the 0402 model once at the middle mesh of its convergence study, about 0.23
million unknowns (17 s on an idle machine, 58 s on a loaded one in this project's runs).

Style: the project's plotting guide, through pcbcap.plotting (Arial 8 pt, restrained palette,
600-dpi PNG plus PDF with editable text).
"""
from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[4] / "pcbcap"))
sys.path.insert(0, str(HERE.parent))

import matplotlib.pyplot as plt                                   # noqa: E402
import numpy as np                                                # noqa: E402
from matplotlib.ticker import LogFormatterMathtext                 # noqa: E402

import g_resistor_3d as g3                                        # noqa: E402
from pcbcap import plotting as pl                                 # noqa: E402
from pcbcap import study                                          # noqa: E402

NOTE = HERE.parents[3]
DATA = NOTE / "data" / "parasitic_cf" / "numerical"
FIGS = NOTE / "figures"
C = pl.COLORS


def load(name: str) -> dict:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def panel(ax, label: str) -> None:
    """Panel label above the axes, left-aligned, so that it never covers data."""
    ax.set_title(label, loc="left")


def iso_axes(fig, cells):
    """3-D axes that fill the grid cells of ``cells``, a list of (grid slot, panel label) pairs.

    Workaround for two matplotlib behaviours (version 3.10):
    1. Constrained layout shrinks a 3-D axes until its tick labels fit inside its grid cell, which
       left the 3-D views small and off-centre.  So a blank placeholder axes takes each cell in the
       layout and carries the panel label, the layout is computed once (canvas.draw), and each 3-D
       axes is then created at its placeholder's position and kept out of the layout
       (set_in_layout(False)); its tick labels may reach into the cell's margins.  The placeholders
       stay, invisible except for their labels, to hold the cells.  Call this after every 2-D panel
       of the figure exists, so that the layout computed here is the final one.
    2. A 3-D axes draws its box inside the largest square, in inches, that fits its position,
       centred in it (Axes3D.apply_aspect).  A wide cell therefore leaves blank margins beside the
       box; set_box_aspect(..., zoom=...) enlarges the box inside the square.  This is also why the
       panel label sits on the placeholder: on the 3-D axes, set_title would place it at the left of
       that square, in the middle of the figure."""
    holders = []
    for slot, label in cells:
        holder = fig.add_subplot(slot)
        holder.axis("off")                      # no frame or ticks; the title is still drawn
        panel(holder, label)
        holders.append(holder)
    fig.canvas.draw()
    axes = []
    for holder in holders:
        ax = fig.add_axes(holder.get_position(), projection="3d")
        ax.set_in_layout(False)
        axes.append(ax)
    return axes


_SOLVED = {}


def solved_0402():
    """The 0402 model solved once at the middle mesh (refine 2.83), keeping its fields."""
    if "p" not in _SOLVED:
        res, prob = study.solve_layout(g3.layout("0402"), replace(g3.BASE, refine=2.83), order=2,
                                       keep_fields=True, return_problem=True)
        _SOLVED.update(r=res, p=prob)
    return _SOLVED["r"], _SOLVED["p"]


# ================================================================================================
def fig44():
    """The three-dimensional model of an 0402 on its pads: view, section, mesh."""
    lay = g3.layout("0402")
    fig = plt.figure(figsize=(6.5, 5.2), constrained_layout=True)
    gs = fig.add_gridspec(2, 2, height_ratios=[1.45, 1.0])
    # The 2-D panels are drawn first, so that the layout which iso_axes computes already includes
    # their final tick labels and the 3-D panel's position does not change afterwards.
    ax = fig.add_subplot(gs[1, 0])
    pl.draw_section(ax, lay, ((-0.9, 0.9), (-0.25, 0.5)))
    panel(ax, "(b)")
    ax = fig.add_subplot(gs[1, 1])
    _, prob = solved_0402()
    pl.mesh_map(ax, prob, ((0.12, 0.62), (-0.04, 0.46)))
    panel(ax, "(c)")
    (ax,) = iso_axes(fig, [(gs[0, :], "(a)")])
    win = ((-1.0, 1.0), (-0.6, 0.6), (-0.25, 0.45))
    pl.draw_iso(ax, lay, win)
    # zoom > 1 enlarges the drawn box inside its square (iso_axes, point 2); 1.25 was chosen by eye
    # so that the tick labels still clear the panels below.
    ax.set_box_aspect([w[1] - w[0] for w in win], zoom=1.25)
    ax.set_xticks([-1.0, -0.5, 0.0, 0.5, 1.0])
    ax.set_yticks([-0.5, 0.0, 0.5])
    ax.set_zticks([0.0, 0.4])
    pl.export(fig, FIGS / "fig44_parasitic_cf_numerical_model")


def fig45():
    """The field of the 0402 model on the section y = 0: the odd drive's potential, and the density
    of C_F, eps (|grad phi_o|^2 - |grad phi_e|^2), whose integral is C_F (pcbcap.plotting.coupling_map)."""
    res, prob = solved_0402()
    phi_o, phi_e = res.fields["phi_odd"], res.fields["phi_even"]
    fig, axs = plt.subplots(2, 1, figsize=(6.5, 4.6), constrained_layout=True)
    win = ((-0.9, 0.9), (-0.3, 0.6))
    pl.field_map(axs[0], prob, phi_o, "potential", parity="odd", window=win, vlim=0.5)
    panel(axs[0], "(a)")
    pl.coupling_map(axs[1], prob, phi_o, phi_e, window=win)
    panel(axs[1], "(b)")
    pl.export(fig, FIGS / "fig45_parasitic_cf_numerical_field")


LABELS = {"G25_pads_halfplane": "Eq. (G.25) pads, half-plane", "G27_cut_layer": "Eq. (G.27) cut layer",
          "G28_block_upper": "Eq. (G.28) body, upper bound", "G32_block_lower": "Eq. (G.32) body, lower bound",
          "G33_air_no_film": "Eq. (G.33) air, no film", "G38_air_with_film": "Eq. (G.38) air with film",
          "G41_plane_0p10": "Eq. (G.41) plane at 0.10 mm", "G41_plane_0p20": "Eq. (G.41) plane at 0.20 mm",
          "G41_plane_0p36": "Eq. (G.41) plane at 0.36 mm", "G43_guard": "Eq. (G.43) guard strip",
          "G45_pins_no_middle": "Eq. (G.45) pins, pin 2 removed", "G46_pins_wall": "Eq. (G.46) pins, floating wall"}


def fig46():
    """Validation: each closed form against its numerical solution; 3-D against 2-D convergence."""
    cf = load("closed_forms_2d.json")
    ck = load("checks.json")
    fig, axs = plt.subplots(1, 2, figsize=(6.5, 3.0), constrained_layout=True,
                            gridspec_kw=dict(width_ratios=[1.35, 1.0]))
    ax = axs[0]
    names = [k for k in LABELS if k in cf]
    # true values, unclipped: Eq. (G.28), whose exact potential the elements contain, sits at rounding level
    vals = [abs(cf[k]["rel_error"]) for k in names]
    y = np.arange(len(names))[::-1]
    ax.barh(y, vals, color=C["primary"], height=0.6, left=1e-16)
    ax.set_yticks(y)
    ax.set_yticklabels([LABELS[k] for k in names])
    ax.set_xscale("log")
    ax.xaxis.set_major_formatter(LogFormatterMathtext())
    ax.set_xlim(1e-16, 1e-2)
    ax.set_xticks([1e-16, 1e-12, 1e-8, 1e-4])
    ax.set_xlabel(r"$|C_\mathrm{field}/C_\mathrm{closed} - 1|$")
    panel(ax, "(a)")
    ax = axs[1]
    d = ck["extrusion_3d_vs_2d"]["data"]
    h = np.array(d["h_edge"])
    err = np.array(d["values"]) / d["reference"] - 1
    ax.loglog(h, err, "o-", color=C["primary"], lw=pl.LINEWIDTH, ms=4, label="3-D against 2-D")
    ax.loglog(h, err[0] * h / h[0], color=C["neutral"], lw=pl.LINEWIDTH, ls=pl.DASHED, label="slope 1")
    ax.xaxis.set_major_formatter(LogFormatterMathtext())
    ax.yaxis.set_major_formatter(LogFormatterMathtext())
    ax.set_xlabel(r"Element size at edges, $h_\mathrm{edge}$ (mm)")
    ax.set_ylabel("Relative error")
    ax.legend(loc="lower right")
    panel(ax, "(b)")
    pl.export(fig, FIGS / "fig46_parasitic_cf_numerical_validation")


def fig47():
    """Convergence of the 0402 result in the mesh and in the enclosure size."""
    r = load("resistor_3d.json")["size_0402"]
    fig, axs = plt.subplots(1, 2, figsize=(6.5, 2.7), constrained_layout=True)
    ax = axs[0]
    lv = r["convergence"]["levels"]
    n = [x["dofs"] for x in lv]
    c = [x["C_F"] for x in lv]
    ax.plot(n, c, "o-", color=C["primary"], lw=pl.LINEWIDTH, ms=4, label="finite elements, enclosure 8 mm")
    ext = r["convergence"]["C_F"].get("extrapolated")
    if ext is not None:
        ax.axhline(ext, color=C["neutral"], lw=pl.LINEWIDTH, ls=pl.DASHED, label="extrapolated in the mesh")
    ax.set_xscale("log")
    ax.xaxis.set_major_formatter(LogFormatterMathtext())
    ax.set_xlabel("Unknowns")
    ax.set_ylabel(r"$C_{F,\mathrm{par}}$ (fF)")
    ax.legend(loc="upper right")
    panel(ax, "(a)")
    ax = axs[1]
    e = r["enclosure"]
    inv = 1.0 / np.array(e["R"])
    ax.plot(inv, e["C_F"], "o", color=C["primary"], ms=4, label="coarsest mesh")
    q = e.get("order_C_F") or 1.0
    xs = np.linspace(0, inv.max() * 1.05, 50)
    k = (e["C_F"][0] - e["C_F_inf"]) / inv[0] ** q
    ax.plot(xs, e["C_F_inf"] + k * xs ** q, color=C["neutral"], lw=pl.LINEWIDTH, ls=pl.DASHED,
            label=rf"$C_\infty + k\,R^{{-{q:.2f}}}$")
    ax.set_xlabel(r"Inverse enclosure half-width, $1/R$ (mm$^{-1}$)")
    ax.set_ylabel(r"$C_{F,\mathrm{par}}$ (fF)")
    ax.set_xlim(0, inv.max() * 1.1)
    ax.legend(loc="upper right")
    panel(ax, "(b)")
    pl.export(fig, FIGS / "fig47_parasitic_cf_numerical_convergence")


def fig48():
    """The field solution for each size against the bracket of Appendix G (same permittivities)."""
    r = load("resistor_3d.json")
    sizes = [s for s in ("0201", "0402", "0603", "0805") if f"size_{s}" in r]
    fig, ax = plt.subplots(figsize=(4.2, 3.24), constrained_layout=True)
    for i, s in enumerate(sizes):
        d = r[f"size_{s}"]
        an = d["analytic"]
        ax.plot([i, i], [an["lower_bound"], an["upper_estimate"]], color=C["neutral"], lw=6, alpha=0.25,
                solid_capstyle="butt", label="Appendix G, lower bound to upper estimate" if i == 0 else "_nolegend_")
        ax.plot([i - 0.18, i + 0.18], [an["central"]] * 2, color=C["neutral"], lw=pl.LINEWIDTH,
                label="Appendix G, central value" if i == 0 else "_nolegend_")
        fin = d["convergence"]["C_F"].get("extrapolated") or d["convergence"]["C_F"]["finest"]
        ax.plot(i, fin, "o", mfc="white", mec=C["primary"], ms=5,
                label="field solution, enclosure 8 mm" if i == 0 else "_nolegend_")
        ax.plot(i, d["C_F_best"], "o", color=C["primary"], ms=5,
                label="field solution, no nearby ground" if i == 0 else "_nolegend_")
    ax.set_xticks(range(len(sizes)))
    ax.set_xticklabels(sizes)
    ax.set_xlim(-0.5, len(sizes) - 0.5)
    ax.set_xlabel("Resistor size")
    ax.set_ylabel(r"$C_{F,\mathrm{par}}$ of resistor and pads (fF)")
    ax.legend(loc="upper left")
    pl.export(fig, FIGS / "fig48_parasitic_cf_numerical_sizes")


def fig49():
    """C_F against the board's permittivity, relative to FR-4, for the 0402 and the 0805."""
    r = load("resistor_3d.json")
    fig, ax = plt.subplots(figsize=(6.5, 3.2), constrained_layout=True)
    for s, col in (("0402", C["primary"]), ("0805", C["warm_accent"])):
        key = f"substrates_{s}"
        if key not in r:
            continue
        rows = r[key]["rows"]
        eps = np.array([x["eps_pcb"] for x in rows])
        rel = np.array([x["relative_to_FR4"] for x in rows])
        ax.plot(eps, rel, "o-", color=col, lw=pl.LINEWIDTH, ms=3.5, label=f"{s}, field solution")
        an = np.array([x["analytic"]["central"] for x in rows])
        ref = next(x for x in rows if x["eps_pcb"] == 4.2)["analytic"]["central"]
        ax.plot(eps, an / ref, color=col, lw=pl.LINEWIDTH, ls=pl.DASHED, label=f"{s}, Appendix G central value")
    # Material names at their points.  The curves rise at about 24 degrees on this canvas; the labels
    # are rotated by +35 degrees, so each one rises away from the curve instead of crossing it.  They sit
    # above the upper (0402) curve.  Three materials cluster between 3.45 and 3.71.  Two parallel labels
    # separate only by moving across the text direction, (-sin 35, cos 35) for the one on the left, so
    # the I-Tera label is shifted up and to the left (-8, 10) points; MEGTRON 6, only 0.05 to the right
    # of RO4350B, goes below the lower (0805) curve and runs down to the left.
    rows = {s: r[f"substrates_{s}"]["rows"] for s in ("0402", "0805") if f"substrates_{s}" in r}
    below = {"MEGTRON 6 (1 GHz)"}
    shift = {"I-Tera MT40": (-8, 10)}
    if "0402" in rows:
        for k, x in enumerate(rows["0402"]):
            if x["material"] in below and "0805" in rows:
                ax.annotate(x["material"], (x["eps_pcb"], rows["0805"][k]["relative_to_FR4"]),
                            textcoords="offset points", xytext=(4, -7), ha="right", va="top", rotation=35,
                            rotation_mode="anchor", color=C["annotation"])
            else:
                ax.annotate(x["material"], (x["eps_pcb"], x["relative_to_FR4"]), textcoords="offset points",
                            xytext=shift.get(x["material"], (-2, 7)), ha="left", va="bottom", rotation=35,
                            rotation_mode="anchor", color=C["annotation"], annotation_clip=False)
    ax.set_xlabel(r"Relative permittivity of the board, $\varepsilon_\mathrm{pcb}$")
    ax.set_ylabel(r"$C_{F,\mathrm{par}}$ relative to FR-4 ($\varepsilon_\mathrm{pcb}$ = 4.2)")
    ax.set_xlim(0.8, 5.0)
    ax.set_ylim(0.62, 1.12)
    ax.legend(loc="lower right")
    pl.export(fig, FIGS / "fig49_parasitic_cf_numerical_substrates")


def fig50():
    """The feedback network of Figure 44 in three dimensions, and what each part adds."""
    r = load("resistor_3d.json").get("opa855_layout")
    lay = g3.opa855_layout()
    fig = plt.figure(figsize=(6.5, 3.2), constrained_layout=True)
    # The narrow middle column stays empty.  It keeps room for the z-axis label of the 3-D panel,
    # which the layout does not see (iso_axes) and which otherwise ran into panel (b)'s label.
    gs = fig.add_gridspec(1, 3, width_ratios=[1.6, 0.22, 1.0])
    if r is not None:                       # the 2-D panel first (iso_axes, point 1)
        t = r["table"]
        # all three at the finer of the two mesh levels (levels[-1] = 5.66), at which the plane variant
        # was also solved (g_resistor_3d.py, opa855_layout)
        fine = t[f"refine_{t['levels'][-1]}"]
        labels = ["resistor\nand pads", "whole\nnetwork", "network,\nplane cut out"]
        vals = [fine["alone"], fine["network"], t["plane_cutout"]["network"]]
        ax = fig.add_subplot(gs[0, 2])
        ax.bar(range(3), vals, color=[C["grey_accent"], C["primary"], C["cool_accent"]], width=0.6)
        for i, v in enumerate(vals):
            ax.text(i, v + 1, f"{v:.0f}", ha="center", va="bottom")
        ax.set_xticks(range(3))
        ax.set_xticklabels(labels)
        ax.set_ylabel(r"$C_{F,\mathrm{par}}$, enclosure 8 mm (fF)")
        ax.set_ylim(0, max(vals) * 1.2)
        panel(ax, "(b)")
    (ax,) = iso_axes(fig, [(gs[0, 0], "(a)")])
    pl.draw_iso(ax, lay, ((-1.4, 0.95), (-0.45, 2.0), (-0.2, 0.9)))
    pl.export(fig, FIGS / "fig50_parasitic_cf_numerical_opa855")


def fig51():
    """The OPA846 in SOT-23-5: the three layouts in three dimensions, and C_F of each."""
    import g_opa846_3d as g8
    rec = DATA / "opa846_3d.json"
    r = json.loads(rec.read_text(encoding="utf-8")) if rec.exists() else {}
    fig = plt.figure(figsize=(6.5, 4.0), constrained_layout=True)
    # The narrow fourth column of the top row stays empty.  It keeps room for the z-axis label of
    # panel (c), which the layout does not see because the 3-D axes are kept out of it (iso_axes).
    gs = fig.add_gridspec(2, 4, height_ratios=[0.9, 0.65], width_ratios=[1.0, 1.0, 1.0, 0.25])
    names = {"double_sided": r"$R_F$ under the package", "under_body": "trace under the body",
             "around": "trace around the package"}
    ax = fig.add_subplot(gs[1, :])          # the 2-D panel first (iso_axes, point 1)
    xs = np.arange(len(g8.LAYOUTS))
    for j, (size, col) in enumerate((("0402", C["primary"]), ("0603", C["warm_accent"]))):
        vals = [r.get(f"{lay}_{size}", {}).get("table", {}).get("refine_5.66", {}).get("C_F", np.nan)
                for lay in g8.LAYOUTS]
        ax.bar(xs + (j - 0.5) * 0.36, vals, width=0.34, color=col, label=f"{size} $R_F$")
        for x, v in zip(xs + (j - 0.5) * 0.36, vals):
            if np.isfinite(v):
                ax.text(x, v + 3, f"{v:.0f}", ha="center", va="bottom")
    # No reference line: the about 0.3 pF inferred on the bench board of Section 3.10 (Section G.13.5)
    # comes from a layout that is not recorded and may be a poor one, so it is no benchmark here.
    ax.set_xticks(xs)
    ax.set_xticklabels([names[l] for l in g8.LAYOUTS])
    # Fixed limits, so that the layout (and with it the 3-D panels above) does not depend on whether
    # the record already holds every bar: an empty axes would put the outer labels at its edges.
    ax.set_xlim(-0.6, len(xs) - 0.4)
    ax.set_ylabel(r"$C_{F,\mathrm{par}}$ (fF)")
    tallest = max([p.get_height() for p in ax.patches if np.isfinite(p.get_height())] or [100.0])
    ax.set_ylim(0, 1.35 * tallest)        # room for the value labels and the legend above the bars
    ax.legend(loc="upper right", ncol=2)
    panel(ax, "(d)")
    cells = [(gs[0, k], f"({'abc'[k]}) {names[layout]}") for k, layout in enumerate(g8.LAYOUTS)]
    axes = iso_axes(fig, cells)
    for k, (ax, layout) in enumerate(zip(axes, g8.LAYOUTS)):
        pl.draw_iso(ax, g8.opa846_layout(layout, "0402"), ((-2.8, 2.8), (-2.8, 2.8), (-2.2, 1.3)))
        ax.set_zticks([-1.6, 0.0, 1.0])
        # A 3-D axes paints a white background over its whole cell, which hid the z-axis numbers of
        # the panel to its left; a transparent background shows them.  The three panels share one
        # height scale, so only the last one carries the z-axis numbers and label.
        ax.set_facecolor("none")
        if k < len(axes) - 1:
            ax.set_zticklabels([])
            ax.set_zlabel("")
    pl.export(fig, FIGS / "fig51_parasitic_cf_numerical_opa846")


FIGURES = {44: fig44, 45: fig45, 46: fig46, 47: fig47, 48: fig48, 49: fig49, 50: fig50, 51: fig51}


def main() -> int:
    study.lower_priority(2)
    pl.use_style()
    which = [int(a) for a in sys.argv[1:]] or list(FIGURES)
    for n in which:
        FIGURES[n]()
        print(f"Figure {n} written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
