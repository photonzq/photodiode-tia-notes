"""Section 8.6 of the high-gain note: the input common-mode range and the input
bias current against the input common-mode voltage of the 25 op amps.

Reads data/ib_vs_vcm.json, whose cells hold the datasheet readings with their
pages, and
  - returns the body of Table A.9 (table_a9(), used by hg_appendix_tables.py);
  - draws Figure A.1 (figures/fig_ib_vcm.png at 600 dpi and .pdf): for each
    part, its guaranteed input range, its typical range where that is wider,
    the span in which its plotted bias current stays within twice its
    mid-supply value, and the common-mode voltage of its bias-current
    specification, all as fractions of the supply of its curve, with the
    datasheet, the table or section and the figure each row is drawn from
    written beside it.

The figure departs from the default 4.2 x 3.24 in canvas because it has one
row per part (25 rows); it is 6.5 in wide, the text width of the note.

Usage:  python hg_common_mode.py          (draws the figure, prints Table A.9)
"""
from __future__ import annotations

import json
import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402
from matplotlib.transforms import blended_transform_factory  # noqa: E402

from hg_tables import ORDER  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "ib_vs_vcm.json"
FIG = ROOT / "figures" / "fig_ib_vcm"

FONT_SIZE = 8.0
COLORS = {
    "primary": "#385C9E",
    "neutral": "#4D4D4D",
    "warm_accent": "#9E403D",
    "grey_accent": "#6F6F6F",
    "light": "#C4CEDD",
    "annotation": "#767676",
    "text": "#272727",
    "axes": "#000000",
    "background": "#FFFFFF",
}


def load() -> dict:
    return json.loads(DATA.read_text(encoding="utf-8"))["parts"]


def parts_in_order(parts: dict) -> list[str]:
    names = [n for n in ORDER if n in parts]
    missing = sorted(set(parts) - set(names))
    if missing:
        raise SystemExit(f"parts missing from ORDER: {missing}")
    return names


def table_a9() -> str:
    parts = load()
    out = ["*Table A.9. Input common-mode range and input bias current against the input common-mode voltage "
           "(Section 8.6, Figure A.1). $V_-$ and $V_+$ are the negative and positive supply rails. The range is the "
           "guaranteed one, with the typical limits in brackets where they are wider. The curve values are read by "
           "eye from the datasheets' typical plots, at 25 °C unless stated and with the sign as printed; where two "
           "values are given for one point they belong to the two inputs. The fifth column gives the current near "
           "$V_-$, at mid-supply and near the top of the input range, in that order. The sixth gives the span in "
           "which the plotted current stays within twice its mid-supply value, or within the band stated. Every "
           "value names the one table, section or figure of its datasheet that it comes from, with its PDF page; "
           "§ marks a numbered section, which is how TI numbers its specification tables. The datasheets are those "
           "of Appendix D. `data/ib_vs_vcm.json`, `hg_common_mode.py`.*",
           "",
           "| Part | Input range | $I_B$ specified at | Curve | $I_B$ near $V_-$ / at mid-supply / near the top "
           "| Within 2× of mid-supply | Non-inverting input at $V_-$ |",
           "|---|---|---|---|---|---|---|"]
    for name in parts_in_order(parts):
        p = parts[name]
        out.append(f"| {name} [{p['doc']}] | {p['range']} | {p['spec']} | {p['curve']} | {p['values']} | "
                   f"{p['window']} | {p['vminus']} |")
    return "\n".join(out)


def figure_a1_markdown() -> str:
    """The image line and caption of Figure A.1 for Appendix A."""
    return ("![Figure A.1](figures/fig_ib_vcm.png)\n\n"
            "*Figure A.1. Where each op amp of Table A.9 may hold its inputs, and where the bias current of its "
            "datasheet applies, against the input common-mode voltage as a fraction of the supply of its curve, "
            "which the label gives. Light bars: the guaranteed input range. Thin grey lines: the typical range, where "
            "it is wider. Dark blue bars: the span in which the plotted bias current stays within twice its "
            "mid-supply value, or within the band given in Table A.9 where that value is too small to read, drawn "
            "only inside the guaranteed range. Red diamonds: the common-mode voltage of the datasheet's "
            "bias-current specification. Rows without a blue bar have no curve. The column on the right gives the "
            "datasheet of Appendix D, its table or section (§) that holds the input range and the bias-current "
            "condition, with the page where the table has no number, and its figure that the blue bar is read from; "
            "Table A.9 gives the pages. ADA4530-1 is shown "
            "at 125 °C, where its curves resolve the change, and OPA381, whose curve states no supply, is placed for "
            "5 V. `hg_common_mode.py`.*")


def configure_plot_style() -> None:
    plt.rcParams.update({
        "figure.facecolor": COLORS["background"],
        "axes.facecolor": COLORS["background"],
        "axes.edgecolor": COLORS["axes"],
        "axes.labelcolor": COLORS["text"],
        "text.color": COLORS["text"],
        "xtick.color": COLORS["axes"],
        "ytick.color": COLORS["axes"],
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "DejaVu Sans", "sans-serif"],
        "font.size": FONT_SIZE,
        "axes.labelsize": FONT_SIZE,
        "axes.titlesize": FONT_SIZE,
        "xtick.labelsize": FONT_SIZE,
        "ytick.labelsize": FONT_SIZE,
        "legend.fontsize": FONT_SIZE,
        "axes.linewidth": 0.8,
        "axes.spines.top": True,
        "axes.spines.right": True,
        "xtick.top": True,
        "ytick.right": False,
        "xtick.direction": "in",
        "ytick.direction": "in",
        "legend.frameon": False,
        "axes.grid": False,
        "text.usetex": False,
        "mathtext.fontset": "cm",
        "axes.formatter.use_mathtext": True,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "savefig.facecolor": "white",
        "savefig.bbox": "tight",
    })


def figure_a1() -> list[str]:
    """Draw Figure A.1 and return one check line per part."""
    configure_plot_style()
    parts = load()
    names = parts_in_order(parts)
    # Fixed layout: part labels on the left, the bars in the middle and the
    # source of each row (datasheet; table or section; figure) on the right.
    fig = plt.figure(figsize=(6.5, 6.4))
    ax = fig.add_axes((0.235, 0.085, 0.455, 0.815))
    to_fig_x = blended_transform_factory(fig.transFigure, ax.transData)
    checks = []
    for i, name in enumerate(names):
        p = parts[name]
        mp = p["map"]
        vs = mp["vs"]
        g, t, w = mp["g"], mp["t"], mp["w"]
        # The window is drawn only inside the guaranteed range, or inside the
        # typical range where no guaranteed range is given.
        lo, hi = g if g else t
        if t:
            ax.plot([t[0] / vs, t[1] / vs], [i, i], color=COLORS["grey_accent"], linewidth=1.0,
                    solid_capstyle="butt", zorder=1)
        if g:
            ax.barh(i, (g[1] - g[0]) / vs, left=g[0] / vs, height=0.62, color=COLORS["light"],
                    linewidth=0, zorder=2)
        if w:
            w0, w1 = max(w[0], lo), min(w[1], hi)
            ax.barh(i, (w1 - w0) / vs, left=w0 / vs, height=0.28, color=COLORS["primary"],
                    linewidth=0, zorder=3)
        src = p["src"]
        source = f"[{p['doc']}] {src['table']}; {src['curve'] or 'no curve'}"
        ax.text(0.705, i, source, transform=to_fig_x, va="center", ha="left",
                color=COLORS["text"] if src["curve"] else COLORS["annotation"], clip_on=False)
        for s in mp["spec"]:
            ax.plot(s / vs, i, marker="D", markersize=4.0, color=COLORS["warm_accent"],
                    linestyle="none", zorder=4)
        checks.append(f"{name:12s} vs {vs:5.1f} V  range {lo / vs:+.3f} to {hi / vs:.3f}  "
                      f"window {'-' if not w else f'{max(w[0], lo) / vs:+.3f} to {min(w[1], hi) / vs:.3f}'}  "
                      f"spec {[round(s / vs, 3) for s in mp['spec']]}")
    for x in (0.0, 1.0):
        ax.axvline(x, color=COLORS["annotation"], linewidth=0.8, linestyle=(0, (5, 2)), zorder=0)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels([f"{n}, {parts[n]['label']}" for n in names])
    ax.set_ylim(len(names) - 0.4, -0.6)
    ax.set_xlim(-0.06, 1.06)
    ax.set_xticks([0.0, 0.25, 0.5, 0.75, 1.0])
    ax.set_xticklabels(["0", "0.25", "0.5", "0.75", "1"])
    # Mathtext drops a subscript minus that ends a text, so the rails are
    # named in the axis label, where text follows every subscript.
    ax.set_xlabel(r"Input common-mode voltage, $(V_{CM} - V_{{-}})/(V_{{+}} - V_{{-}})$," "\n"
                  "from the negative rail (0) to the positive rail (1)")
    fig.text(0.705, 0.905, "Source: datasheet; table or §; figure", ha="left", va="bottom",
             color=COLORS["text"])
    handles = [Patch(facecolor=COLORS["light"], edgecolor="none", label="Guaranteed input range"),
               Line2D([0], [0], color=COLORS["grey_accent"], linewidth=1.0, label="Typical range, where wider"),
               Patch(facecolor=COLORS["primary"], edgecolor="none",
                     label="Plotted $I_B$ near its mid-supply value"),
               Line2D([0], [0], marker="D", markersize=4.0, color=COLORS["warm_accent"], linestyle="none",
                      label="$V_{CM}$ of the datasheet's $I_B$")]
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 0.995), ncol=2)
    FIG.parent.mkdir(exist_ok=True)
    fig.savefig(FIG.with_suffix(".png"), dpi=600)
    fig.savefig(FIG.with_suffix(".pdf"))
    plt.close(fig)
    return checks


def main() -> None:
    for line in figure_a1():
        print(line)
    print("written", FIG.with_suffix(".png").name, "and", FIG.with_suffix(".pdf").name)
    print()
    print(table_a9())


if __name__ == "__main__":
    main()
