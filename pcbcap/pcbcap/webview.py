"""Interactive three-dimensional views of a layout, as stand-alone HTML pages.

Why this module exists
----------------------
The static views (plotting.draw_iso and plotting.draw_views) show a layout from a few fixed
directions.  A page written by this module lets a reader of the online note turn, zoom and inspect
the same geometry in a browser, part by part.  The pages are meant to be linked from the note, not
embedded in it.  The rendering, the camera controls and the legend are those of plotly (plotly.py and
plotly.js, MIT licence); this module only hands plotly the faces of the layout.

What a page shows, and how
--------------------------
* The faces are those of plotting.visible_faces, the function that also feeds draw_iso, so the two
  kinds of view cannot disagree.  Only surfaces that exist are drawn (a face covered by a later item
  or buried in an opaque one is left out), with the opacities of the static views: board 0.10, mould
  0.14, alumina 0.35, conductors and films 0.95, ground planes 0.18.
* Each item of the layout becomes one plotly mesh (Mesh3d), two triangles per rectangle, named after
  the item, so that pointing at a part names it and its net.  The meshes are grouped in the legend by
  kind (board, ground planes, package body, resistor body, film, one group per net); a click on a
  group's entry hides or shows the whole group.
* Plotly lights each face from its normal (flat shading) with a light that moves with the camera, so
  the faces are passed unshaded (visible_faces with shade=None), unlike in the static views.
* The scene keeps the true proportions (aspectmode "data"), and the camera starts where the static
  figures look from: elevation 24 degrees, azimuth -58 degrees.  Plotly's camera "eye" is a point in
  the scene's normalised coordinates, so the direction (cos e cos a, cos e sin a, sin e) of
  plotting.view_shade is scaled to a distance of 2.3, at which the whole window fits a narrow
  browser window beside the legend (checked at 800 pixels wide).
* WebGL blends translucent surfaces in the order it draws them, without sorting every face by depth,
  so where several translucent surfaces overlap the blend can change with the viewing direction.
  The metal is nearly opaque and is not affected.

The plotly.js library (about 4.7 MB) is written once into the folder of the pages, as plotly.min.js,
and every page loads it from there (``plotlyjs="directory"``), so the pages work without a network
connection and depend on no outside server.  ``plotlyjs="cdn"`` loads it from plotly's server instead.
"""
from __future__ import annotations

import html
from pathlib import Path

import numpy as np

from . import plotting
from .geometry import GROUND, Conductor, Dielectric, Film, Sheet

GROUP_LABELS = {"board": "board", "mould": "package body (mould)", "alumina": "resistor body (alumina)",
                "solder mask": "solder mask", "film": "resistive film", "planes": "ground planes"}


def _group(it, net_labels: dict[str, str]) -> tuple[str, str]:
    """Legend group of an item and the group's label."""
    r = it.role
    if isinstance(r, Dielectric):
        return r.name, GROUP_LABELS.get(r.name, r.name)
    if isinstance(r, Film):
        return "film", GROUP_LABELS["film"]
    if isinstance(it, Sheet) and r.net == GROUND and it.name.startswith("plane"):
        return "planes", GROUP_LABELS["planes"]
    if r.net == GROUND and it.name.startswith("guard"):
        return "guard", "guard ring (at +IN, ground)"
    label = net_labels.get(r.net, "ground" if r.net == GROUND else f"net {r.net}")
    return f"net:{r.net}", label + (" (not connected)" if r.floating else "")


def _rgb(c) -> str:
    return "rgb({:d},{:d},{:d})".format(*(int(round(255 * float(v))) for v in c))


def figure(layout, window=None, net_labels: dict[str, str] | None = None, title: str = ""):
    """A plotly figure of ``layout`` (see the module docstring)."""
    import plotly.graph_objects as go

    net_labels = net_labels or {}
    win = window if window is not None else plotting.auto_window(layout)
    faces = plotting.visible_faces(layout, win, shade=None)
    by_item: dict[int, list] = {}
    for poly, rgb, alpha, k in faces:
        by_item.setdefault(k, []).append((poly, rgb, alpha))
    fig = go.Figure()
    shown = set()
    # Draw the opaque items first and the translucent ones after them, so that WebGL blends the
    # translucent surfaces over metal that is already drawn.
    order = sorted(by_item, key=lambda k: (by_item[k][0][2] < 0.9, k))
    for k in order:
        it = layout.items[k]
        group, glabel = _group(it, net_labels)
        quads = by_item[k]
        verts = np.concatenate([q[0] for q in quads])                # 4 corners per rectangle
        n = len(quads)
        base = 4 * np.arange(n)
        i = np.concatenate([base, base])                              # two triangles per rectangle:
        j = np.concatenate([base + 1, base + 2])                      # corners (0, 1, 2) and (0, 2, 3)
        kk = np.concatenate([base + 2, base + 3])
        role = it.role
        what = f"net {role.net}" if isinstance(role, Conductor) else (
            f"film {role.lo} to {role.hi}" if isinstance(role, Film) else role.name)
        fig.add_trace(go.Mesh3d(
            x=verts[:, 0], y=verts[:, 1], z=verts[:, 2], i=i, j=j, k=kk,
            color=_rgb(quads[0][1]), opacity=float(quads[0][2]), flatshading=True,
            lighting=dict(ambient=0.55, diffuse=0.6, specular=0.05, roughness=0.9, fresnel=0.05),
            name=glabel, legendgroup=group, showlegend=group not in shown,
            hovertemplate=f"{html.escape(it.name or 'item')}<br>{html.escape(what)}<extra></extra>"))
        shown.add(group)
    e, a = np.radians(plotting.DEFAULT_VIEW[0]), np.radians(plotting.DEFAULT_VIEW[1])
    eye = 2.3 * np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])
    axis = dict(showbackground=False, gridcolor="#E0E0E0", zerolinecolor="#C0C0C0", color="#272727")
    fig.update_layout(
        title=dict(text=html.escape(title), x=0.01, font=dict(size=14)) if title else None,
        font=dict(family="Arial, sans-serif", size=12, color="#272727"),
        paper_bgcolor="#FFFFFF", margin=dict(l=0, r=0, t=40 if title else 10, b=0),
        legend=dict(groupclick="togglegroup", itemclick="toggle", bgcolor="rgba(255,255,255,0.8)"),
        scene=dict(aspectmode="data",
                   xaxis=dict(title="x (mm)", range=list(win[0]), **axis),
                   yaxis=dict(title="y (mm)", range=list(win[1]), **axis),
                   zaxis=dict(title="z (mm)", range=list(win[2]), **axis),
                   camera=dict(eye=dict(x=float(eye[0]), y=float(eye[1]), z=float(eye[2])),
                               up=dict(x=0, y=0, z=1))))
    return fig


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  body {{ margin: 0; font-family: Arial, sans-serif; color: #272727; background: #FFFFFF; }}
  header {{ padding: 12px 16px 4px 16px; max-width: 980px; }}
  h1 {{ font-size: 18px; margin: 0 0 6px 0; }}
  p {{ font-size: 14px; line-height: 1.45; margin: 4px 0; }}
  .viewer {{ height: 78vh; min-height: 420px; }}
  a {{ color: #385C9E; }}
</style>
</head>
<body>
<header>
<h1>{title}</h1>
{description}
<p>Drag to turn, scroll to zoom, right-drag to move.  Click an entry of the legend to hide or show that group.</p>
</header>
<div class="viewer">{body}</div>
</body>
</html>
"""


def write_page(layout, path, window=None, net_labels=None, title: str = "", description: str = "",
               plotlyjs: str = "directory") -> Path:
    """Write ``layout`` as a stand-alone HTML page to ``path`` and return the path.

    ``description`` is HTML placed under the title (one or more <p> paragraphs; a plain string is
    wrapped in one).  With ``plotlyjs`` "directory" the page loads plotly.min.js from its own folder,
    which is written there if it is missing; with "cdn" it loads it from plotly's server."""
    from plotly.offline import get_plotlyjs

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig = figure(layout, window=window, net_labels=net_labels)
    if plotlyjs == "directory":
        lib = path.parent / "plotly.min.js"
        if not lib.exists():
            lib.write_text(get_plotlyjs(), encoding="utf-8")
        include = "plotly.min.js"
    elif plotlyjs == "cdn":
        include = "cdn"
    else:
        raise ValueError("plotlyjs must be 'directory' or 'cdn'")
    body = fig.to_html(full_html=False, include_plotlyjs=include, default_height="100%", default_width="100%",
                       config=dict(displaylogo=False, responsive=True,
                                   toImageButtonOptions=dict(format="png", scale=3)))
    desc = description if description.lstrip().startswith("<") else (
        f"<p>{html.escape(description)}</p>" if description else "")
    path.write_text(PAGE.format(title=html.escape(title or layout.name), description=desc, body=body),
                    encoding="utf-8", newline="\n")
    return path
