"""Draw every three-dimensional layout from several sides, and write an interactive page for each.

Run:  python render_layout_views.py [out_dir]        (default: ../../../figures/layout_views)

Why this script exists
----------------------
A field solution is only as good as the geometry it is given, and a geometry is easiest to check by
turning it around.  This script builds the layouts exactly as the study scripts build them (the
OPA855 network of g_resistor_3d.py, the three OPA846 layouts of g_opa846_3d.py and the eight-lead
layouts of g_eight_lead_3d.py) and, without meshing or solving anything, writes for each one
  <name>.png, <name>.pdf   a sheet of six views (pcbcap.plotting.draw_views): from the front left and
                           from the back right above the board, from above, from the front left
                           below the board, and along y and along x;
  <name>_small.png         the same sheet at 90 dpi, for the index page;
  <name>.html              an interactive view (pcbcap.webview), meant to be linked from the note,
                           which loads plotly.min.js from the same folder;
and index.html, which lists them all.  Every view of one layout uses the same window
(plotting.auto_window), so the views show the same piece of the layout from different sides.
"""
from __future__ import annotations

import html
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[4] / "pcbcap"))
sys.path.insert(0, str(HERE.parent))

import matplotlib                                    # noqa: E402
matplotlib.use("Agg")

from pcbcap import plotting, webview                 # noqa: E402

import g_eight_lead_3d as g8                         # noqa: E402
import g_opa846_3d as g846                           # noqa: E402
import g_resistor_3d as g855                         # noqa: E402

SOT23_LABELS = {"A": "net A (output, pin 1)", "B": "net B (inverting input, pin 4)"}
OPA855_LABELS = {"A": "net A (output side)", "B": "net B (inverting input side)"}


def layouts():
    """(file name, layout, title, description, net labels) for each layout."""
    out = [("opa855_network", g855.opa855_layout(with_package=True, plane=True),
            "OPA855 (WSON-8) and its feedback network",
            "The 0402 feedback resistor with its traces to the pins of the OPA855, over a ground plane with a "
            "cut-out under the network: the layout of Section G.14.9 and Figure 50 of the note. Only the pin "
            "edge of the package is modelled.", OPA855_LABELS)]
    for name, what in (("double_sided", "R_F on the bottom side under the package, through two vias"),
                       ("under_body", "R_F above pin 1, with a trace under the body to pin 4"),
                       ("around", "R_F below pin 4, with a trace around the outside of the package")):
        out.append((f"opa846_sot23_{name}_0402", g846.opa846_layout(name, "0402"),
                    f"OPA846 in SOT-23-5: {what} (0402)",
                    "One of the three layouts of Section G.14.10 and Figure 51 of the note, on a four-layer board "
                    "whose two inner ground planes are cut out around the network.", SOT23_LABELS))
    for name, d in g8.LAYOUTS.items():
        out.append((name, g8.build(name), d["title"],
                    "A layout of the eight-lead study (g_eight_lead_3d.py). The package dimensions are those of "
                    "TI's drawings (SOIC-8: D0008A; PDIP-8: P, R-PDIP-T8), as given in pcbcap.packages.",
                    d["labels"]))
    return out


INDEX = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Feedback layouts in three dimensions</title>
<style>
  body {{ margin: 0 auto; max-width: 1000px; padding: 16px; font-family: Arial, sans-serif; color: #272727; }}
  h1 {{ font-size: 20px; }}
  .item {{ margin: 18px 0 26px 0; }}
  .item img {{ width: 100%; border: 1px solid #E0E0E0; }}
  h2 {{ font-size: 16px; margin: 0 0 4px 0; }}
  p {{ font-size: 14px; line-height: 1.45; margin: 4px 0; }}
  a {{ color: #385C9E; }}
</style>
</head>
<body>
<h1>Feedback layouts in three dimensions</h1>
<p>Each layout as the field solver receives it, from six sides, with a link to an interactive view.
Conductors of the output net are red, those of the inverting input blue, grounded ones dark grey,
unconnected pins light grey; the film is purple, the package body brown and translucent, the
resistor body translucent, the board faint green.</p>
{items}
</body>
</html>
"""


def main() -> None:
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parents[3] / "figures" / "layout_views"
    out_dir.mkdir(parents=True, exist_ok=True)
    plotting.use_style()
    items = []
    for name, lay, title, description, labels in layouts():
        win = plotting.auto_window(lay)
        fig = plotting.draw_views(lay, stem=None, window=win)
        fig.savefig(out_dir / f"{name}_small.png", dpi=90)
        plotting.export(fig, out_dir / name)
        webview.write_page(lay, out_dir / f"{name}.html", window=win, net_labels=labels, title=title,
                           description=description)
        items.append(f'<div class="item"><h2>{html.escape(title)}</h2><p>{html.escape(description)} '
                     f'<a href="{name}.html">Interactive view</a>.</p>'
                     f'<a href="{name}.html"><img src="{name}_small.png" alt="{html.escape(title)}"></a></div>')
        print(f"{name}: window {[tuple(round(v, 2) for v in w) for w in win]}")
    (out_dir / "index.html").write_text(INDEX.format(items="\n".join(items)), encoding="utf-8", newline="\n")
    print(f"written to {out_dir}")


if __name__ == "__main__":
    main()
