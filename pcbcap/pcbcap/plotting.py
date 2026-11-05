"""Figures: layouts, field maps, meshes, convergence.

Why this module exists
----------------------
A number from a field solver is easier to trust when one can see the geometry it was computed for,
the mesh it used and the field it found.  These functions draw all three from the same objects the
solver used, so a figure cannot disagree with the computation.

Style.  The figures follow the project's plotting guide: Matplotlib only, Arial at one font size
(8 pt), Computer Modern only inside $...$, inward ticks on all four spines, no grid, the restrained
palette below, a diverging blue-white-red map only for signed data with a meaningful centre, PNG at
600 dpi plus a PDF with editable (Type 42) text.

What the field maps show
------------------------
* "potential": the odd part phi_o of the field (A at +1/2 V, B at -1/2 V), whose centre 0 V is
  meaningful, so the diverging map is used.  For a layout computed on its x >= 0 half, the x < 0 half
  is drawn by mirror symmetry with the sign that the odd field carries (capacitance.py, section 4).
* "energy": eps |<grad phi>|^2 of one chosen field, where <grad phi> is the gradient averaged over
  each element.  It is twice the energy density of that one drive.  It is not the density of C_F:
  the odd drive's energy integrates to C_F + C_A0/2 (capacitance.py, Eq. (6)), not to C_F.  And
  because the square of an average is at most the average of the square (Jensen's inequality), it
  under-states the density most where the field varies most within an element, at the edges.  It
  spans orders of magnitude (near an edge it grows as rho^(2 nu - 2)), so it is drawn on a
  logarithmic colour scale with a sequential map.
* coupling_map: the density whose integral is C_F, eps (|grad phi_o|^2 - |grad phi_e|^2)
  (capacitance.py, Eq. (6) and section 5), as an exact mean over each element: the element integrals
  of eps |grad phi_o|^2 and eps |grad phi_e|^2 (Problem.elemental, exact quadrature) divided by the
  element's volume.  It is signed (the even field dominates far from the part), so it uses the
  diverging map on a symmetric logarithmic scale.
In 3-D the maps are drawn on the plane y = 0, which is a face of the computed quarter when the layout
uses the y mirror; there the mesh faces are exactly the faces of the elements, so nothing is
interpolated except within each element.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

FONT_SIZE = 8.0
COLORS = {
    "primary": "#385C9E",
    "neutral": "#4D4D4D",
    "warm_accent": "#9E403D",
    "cool_accent": "#477A57",
    "purple_accent": "#6B5B95",
    "teal_accent": "#3F7F82",
    "brown_accent": "#7D5C46",
    "grey_accent": "#6F6F6F",
    "highlight": "#EED671",
    "annotation": "#767676",
    "text": "#272727",
    "axes": "#000000",
    "background": "#FFFFFF",
}
HIGHLIGHT_ALPHA = 0.24
MUTED_CLASSIC_COLORS = ["#385C9E", "#7891B8", "#C4CEDD", "#F7F7F4", "#E2C2BC", "#BE7773", "#9E403D"]
SEQUENTIAL_COLORS = ["#FFFFFF", "#C4CEDD", "#7891B8", "#385C9E", "#1F3460"]
COLOR_CYCLE = [COLORS[k] for k in ("primary", "warm_accent", "cool_accent", "purple_accent", "teal_accent",
                                   "brown_accent", "grey_accent")]
LINEWIDTH = 1.5
DASHED = (0, (5, 2))

NET_COLORS = {"A": COLORS["warm_accent"], "B": COLORS["primary"], "gnd": COLORS["neutral"]}
FILM_COLOR = COLORS["purple_accent"]
DIELECTRIC_STYLE = {   # label -> (face colour, alpha)
    "board": (COLORS["cool_accent"], 0.16),
    "alumina": ("#E9E6DF", 1.0),
    "mould": (COLORS["brown_accent"], 0.14),
    "solder mask": (COLORS["teal_accent"], 0.30),
}


def use_style() -> None:
    """Apply the plotting guide's Matplotlib settings (no external LaTeX)."""
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "figure.facecolor": COLORS["background"], "axes.facecolor": COLORS["background"],
        "axes.edgecolor": COLORS["axes"], "axes.labelcolor": COLORS["text"], "text.color": COLORS["text"],
        "xtick.color": COLORS["axes"], "ytick.color": COLORS["axes"],
        "font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans", "sans-serif"],
        "font.size": FONT_SIZE, "axes.labelsize": FONT_SIZE, "axes.titlesize": FONT_SIZE,
        "xtick.labelsize": FONT_SIZE, "ytick.labelsize": FONT_SIZE, "legend.fontsize": FONT_SIZE,
        "axes.linewidth": 0.8, "axes.prop_cycle": plt.cycler(color=COLOR_CYCLE),
        "axes.spines.top": True, "axes.spines.right": True, "xtick.top": True, "ytick.right": True,
        "xtick.direction": "in", "ytick.direction": "in", "legend.frameon": False, "axes.grid": False,
        "text.usetex": False, "mathtext.fontset": "cm", "axes.formatter.use_mathtext": True,
        "pdf.fonttype": 42, "ps.fonttype": 42, "savefig.facecolor": "white", "savefig.bbox": "tight",
    })


def diverging_cmap():
    from matplotlib.colors import LinearSegmentedColormap
    return LinearSegmentedColormap.from_list("muted_classic", MUTED_CLASSIC_COLORS, N=256)


def sequential_cmap():
    from matplotlib.colors import LinearSegmentedColormap
    return LinearSegmentedColormap.from_list("muted_sequential", SEQUENTIAL_COLORS, N=256)


def export(fig, stem: str | Path) -> None:
    """Save ``stem``.png (600 dpi) and ``stem``.pdf, then close the figure."""
    import matplotlib.pyplot as plt
    stem = Path(stem)
    stem.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(stem.with_suffix(".png"), dpi=600)
    fig.savefig(stem.with_suffix(".pdf"))
    plt.close(fig)


def net_color(net: str, floating: bool = False) -> str:
    if floating:
        return COLORS["grey_accent"]
    return NET_COLORS.get(net, COLORS["teal_accent"])


# ================================================================================================
# Geometry drawings
# ================================================================================================
def _role_style(role):
    from .geometry import Conductor, Dielectric
    if isinstance(role, Dielectric):
        fc, al = DIELECTRIC_STYLE.get(role.name, (COLORS["highlight"], HIGHLIGHT_ALPHA))
        if role.name == "air":
            return None
        return dict(fc=fc, alpha=al, ec="none")
    if isinstance(role, Conductor):
        return dict(fc=net_color(role.net, role.floating), alpha=0.85, ec="none")
    return dict(fc=FILM_COLOR, alpha=1.0, ec="none")


def draw_section(ax, layout, window=None, outline_only: bool = False, lw_sheet: float = 2.4) -> None:
    """Draw the (x, z) cross-section of a 2-D layout (or the y = 0 section of a 3-D one)."""
    from matplotlib.patches import Rectangle
    from .geometry import Film, Rect, Segment

    lay = layout.section_y0() if layout.dim == 3 else layout
    for it in lay.items:
        if isinstance(it, Rect):
            st = _role_style(it.role)
            if st is None:
                continue
            (x0, x1), (z0, z1) = it.x, it.z
            if outline_only:
                ax.add_patch(Rectangle((x0, z0), x1 - x0, z1 - z0, fill=False, ec=COLORS["annotation"], lw=0.4))
            else:
                ax.add_patch(Rectangle((x0, z0), x1 - x0, z1 - z0, **st))
        elif isinstance(it, Segment):
            col = FILM_COLOR if isinstance(it.role, Film) else net_color(it.role.net, it.role.floating)
            if it.normal == "z":
                ax.plot(it.span, [it.at, it.at], color=col, lw=lw_sheet if not outline_only else 1.2,
                        solid_capstyle="butt")
            else:
                ax.plot([it.at, it.at], it.span, color=col, lw=lw_sheet if not outline_only else 1.2,
                        solid_capstyle="butt")
    if window:
        ax.set_xlim(*window[0])
        ax.set_ylim(*window[1])
    ax.set_aspect("equal")
    ax.set_xlabel(r"$x$ (mm)")
    ax.set_ylabel(r"$z$ (mm)")


def draw_top(ax, layout, window=None) -> None:
    """Top view of a 3-D layout: items drawn from the lowest top surface to the highest, so what is
    seen from above lies on top.  Planes are buried; their cut-outs are outlined dashed."""
    from matplotlib.patches import Rectangle
    from .geometry import Box, Sheet

    items = []
    for it in layout.items:
        ext = layout.item_extent(it)
        items.append((ext["z"][1], it, ext))
    for ztop, it, ext in sorted(items, key=lambda r: r[0]):
        if isinstance(it, Sheet) and it.normal == "z" and it.at < 0:
            for h in it.holes:
                ax.add_patch(Rectangle((h["x"][0], h["y"][0]), h["x"][1] - h["x"][0], h["y"][1] - h["y"][0],
                                       fill=False, ec=COLORS["neutral"], lw=0.8, ls=DASHED))
            continue
        st = _role_style(it.role)
        if st is None:
            continue
        if isinstance(it, Box) and it.role.__class__.__name__ == "Dielectric" and it.role.name == "board":
            st = dict(st, alpha=0.08)
        (x0, x1), (y0, y1) = ext["x"], ext["y"]
        if x1 > x0 and y1 > y0:
            ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, **st))
            if it.role.__class__.__name__ == "Dielectric" and it.role.name in ("alumina", "mould"):
                ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, ec=COLORS["neutral"], lw=0.6))
    if window:
        ax.set_xlim(*window[0])
        ax.set_ylim(*window[1])
    ax.set_aspect("equal")
    ax.set_xlabel(r"$x$ (mm)")
    ax.set_ylabel(r"$y$ (mm)")


def draw_iso(ax, layout, window) -> None:
    """Isometric view of a 3-D layout, clipped to ``window`` = ((x0, x1), (y0, y1), (z0, z1)).

    Matplotlib's 3-D axes have no depth buffer.  They draw polygons in the order of their mean depth
    (the painter's algorithm), and that goes wrong for the boxes of a layout, which touch, overlap
    and share faces.  Drawn naively, a termination's top wrap and the film on the body's top face lie
    in the same plane as that face; whichever is sorted last covers the other, and the wrap or the
    film vanishes.  Drawn in the layout's order instead, the inner face of an end cap, which lies
    inside the body, is painted over the body's front face.  Both errors were seen.  This function
    therefore works around the missing depth buffer in four ways; none of them changes the model.

    1. Only surfaces that are really there are drawn.  Each face of each box is cut, as a union of
       axis-aligned rectangles (_rect_minus), wherever
         * a later item (geometry.Layout's painter's order: later items replace earlier ones)
           occupies the face's plane there, including the later item's own boundary: there the later
           item owns the surface, e.g. the body's end face under an end cap, the body's top face
           under a wrap or under the film, a pad's top face under the solder; and
         * an earlier opaque item lies on both sides of the face, i.e. the face is strictly inside
           it: an interface buried in a solid, which cannot be seen.
       A face buried in an earlier translucent item (a dielectric) is kept, so that it shows through.
    2. All faces of all items go into one polygon collection, whose polygons matplotlib sorts by
       depth one by one; separate collections would be sorted as wholes.
    3. With faces cut into pieces, drawn edges would show the cuts as false lines, so no edges are
       drawn; instead each face is shaded by the direction of its normal (SHADE), as if lit from
       above the viewer, which tells the faces of a box apart.
    4. Opacity: conductors and the film are nearly opaque (0.95); the alumina body is drawn
       semi-transparent (ISO_ALUMINA_ALPHA) so that the terminations' inner faces and the film's
       extent show through it, although DIELECTRIC_STYLE keeps it opaque in sections and top
       views; the board is drawn faint (0.10); other dielectrics take their DIELECTRIC_STYLE alpha;
       ground planes are drawn translucent (0.18) with their cut-outs open (_sheet_cells).
    The view is fixed (view_init(elev=24, azim=-58)), and the shading assumes it."""
    from matplotlib.colors import to_rgb
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    from .geometry import Box, Dielectric, Sheet

    eps = 1e-9      # coordinates closer than this are the same plane (mm)

    def clip(iv, w):
        a, b = max(iv[0], w[0]), min(iv[1], w[1])
        return (a, b) if b > a else None

    def alpha_of(it):
        r = it.role
        if isinstance(r, Dielectric):
            if r.name == "board":
                return 0.10
            if r.name == "alumina":
                return ISO_ALUMINA_ALPHA
            return _role_style(r)["alpha"]
        return 0.95

    items = [(k, it) for k, it in enumerate(layout.items) if _role_style(it.role) is not None]
    boxes = [(k, it, layout.item_extent(it)) for k, it in items if isinstance(it, Box)]
    zsheets = [(k, it) for k, it in items if isinstance(it, Sheet) and it.normal == "z"]
    polys, colors = [], []

    def add(n, c, cells, rgb, alpha):
        """Append the rectangles ``cells`` of the plane (axis n) = c as polygons of one colour."""
        u, v = [a for a in "xyz" if a != n]
        for (u0, u1), (v0, v1) in cells:
            pts = []
            for uu, vv in ((u0, v0), (u1, v0), (u1, v1), (u0, v1)):
                q = {n: c, u: uu, v: vv}
                pts.append([q["x"], q["y"], q["z"]])
            polys.append(np.array(pts))
            colors.append((*rgb, alpha))

    for k, it, ext in boxes:
        cl = {a: clip(ext[a], window[i]) for i, a in enumerate("xyz")}
        if any(v is None for v in cl.values()):
            continue
        base = np.array(to_rgb(_role_style(it.role)["fc"]))
        al = alpha_of(it)
        for n in "xyz":
            u, v = [a for a in "xyz" if a != n]
            for side, sign in ((0, -1), (1, +1)):
                c = cl[n][side]
                cells = [(cl[u], cl[v])]
                for k2, it2, ext2 in boxes:                           # rule 1 of the docstring
                    if k2 == k:
                        continue
                    lo, hi = ext2[n]
                    later_owns = k2 > k and lo - eps <= c <= hi + eps
                    buried = k2 < k and alpha_of(it2) >= 0.9 and lo + eps < c < hi - eps
                    if later_owns or buried:
                        cells = _rect_minus(cells, (ext2[u], ext2[v]))
                    if not cells:
                        break
                if n == "z":                                          # a later sheet lying on the face
                    for k2, sh in zsheets:
                        if k2 > k and abs(sh.at - c) <= eps:
                            for cell in _sheet_cells(sh):
                                cells = _rect_minus(cells, cell)
                if cells:
                    add(n, c, cells, np.clip(base * SHADE[(n, sign)], 0.0, 1.0), al)
    for k, sh in zsheets:                                             # the films and planes themselves
        if not (window[2][0] <= sh.at <= window[2][1]):
            continue
        is_plane = getattr(sh.role, "net", None) == "gnd"
        cells = []
        for (x0, x1), (y0, y1) in _sheet_cells(sh):
            cx, cy = clip((x0, x1), window[0]), clip((y0, y1), window[1])
            if cx is not None and cy is not None:
                cells.append((cx, cy))
        if cells:
            add("z", sh.at, cells, np.array(to_rgb(_role_style(sh.role)["fc"])), 0.18 if is_plane else 0.95)
    if polys:
        ax.add_collection3d(Poly3DCollection(polys, facecolors=colors, edgecolors="none"))
    ax.set_xlim(*window[0])
    ax.set_ylim(*window[1])
    ax.set_zlim(*window[2])
    ax.set_box_aspect([window[i][1] - window[i][0] for i in range(3)])
    ax.set_xlabel(r"$x$ (mm)")
    ax.set_ylabel(r"$y$ (mm)")
    ax.set_zlabel(r"$z$ (mm)")
    ax.view_init(elev=24, azim=-58)


# Shading of a face by its outward normal (axis, sign), for the fixed view of draw_iso (camera at
# +x, -y, +z): top faces brightest, then the faces turned towards the viewer, then the rest.
SHADE = {("z", +1): 1.00, ("y", -1): 0.84, ("x", +1): 0.70,
         ("z", -1): 0.60, ("y", +1): 0.76, ("x", -1): 0.66}
# The alumina body in 3-D views: see-through, so that the terminations show inside it.
ISO_ALUMINA_ALPHA = 0.35


def _rect_minus(cells, b):
    """Axis-aligned rectangles ``cells`` [((u0, u1), (v0, v1)), ...] minus the rectangle ``b``.

    Each cell that overlaps b is replaced by up to four cells around the overlap: the strips left and
    right of it over the cell's full height, and the strips below and above it over the overlap's
    width.  Cells that only touch b along an edge are kept whole."""
    (bu0, bu1), (bv0, bv1) = b
    out = []
    for (u0, u1), (v0, v1) in cells:
        iu0, iu1 = max(u0, bu0), min(u1, bu1)
        iv0, iv1 = max(v0, bv0), min(v1, bv1)
        if iu1 <= iu0 or iv1 <= iv0:
            out.append(((u0, u1), (v0, v1)))
            continue
        if u0 < iu0:
            out.append(((u0, iu0), (v0, v1)))
        if iu1 < u1:
            out.append(((iu1, u1), (v0, v1)))
        if v0 < iv0:
            out.append(((iu0, iu1), (v0, iv0)))
        if iv1 < v1:
            out.append(((iu0, iu1), (iv1, v1)))
    return out


def _sheet_cells(it):
    """Rectangles that cover a z-normal sheet minus its holes.

    The x and y coordinates of the sheet's and the holes' edges cut the sheet into a grid of cells;
    a cell lies either wholly inside a hole or wholly outside every hole, so keeping the outside
    cells reproduces the sheet with its cut-outs exactly."""
    xs = sorted({*it.spans["x"], *[c for h in it.holes for c in h["x"]]})
    ys = sorted({*it.spans["y"], *[c for h in it.holes for c in h["y"]]})
    xs = [x for x in xs if it.spans["x"][0] <= x <= it.spans["x"][1]]
    ys = [y for y in ys if it.spans["y"][0] <= y <= it.spans["y"][1]]
    cells = []
    for x0, x1 in zip(xs, xs[1:]):
        for y0, y1 in zip(ys, ys[1:]):
            xm, ym = 0.5 * (x0 + x1), 0.5 * (y0 + y1)
            if not any(h["x"][0] <= xm <= h["x"][1] and h["y"][0] <= ym <= h["y"][1] for h in it.holes):
                cells.append(((x0, x1), (y0, y1)))
    return cells


# ================================================================================================
# Field maps on the section y = 0
# ================================================================================================
def section_triangles(problem):
    """Triangles of the plane y = 0 (3-D, from the faces of the computed quarter) or of the whole
    2-D mesh, as (xz, tri, elem, nodes): vertex coordinates (2, n), triangles (3, k) indexing them,
    the element each triangle belongs to (for element-wise quantities), and the mesh node index of
    each vertex (for nodal values)."""
    md, mesh = problem.md, problem.mesh
    if md.dim == 2:
        return mesh.p, mesh.t, np.arange(mesh.t.shape[1]), np.arange(mesh.p.shape[1])
    if not md.clipped.get("y", False):
        raise ValueError("3-D field maps need a layout with the y mirror (the plane y = 0 is then a mesh face)")
    bf = mesh.boundary_facets()
    yv = mesh.p[1, mesh.facets[:, bf]]
    on = bf[np.all(np.abs(yv) < 1e-9 * max(1.0, np.abs(mesh.p[1]).max()), axis=0)]
    tri_nodes = mesh.facets[:, on]
    used, inv = np.unique(tri_nodes, return_inverse=True)
    xz = mesh.p[[0, 2]][:, used]
    tri = inv.reshape(tri_nodes.shape)
    elem = mesh.f2t[0, on]
    return xz, tri, elem, used


def field_map(ax, problem, phi, quantity: str = "potential", parity: str | None = "odd", window=None,
              levels=None, colorbar: bool = True, outline: bool = True, vlim=None):
    """Map the potential or the energy density of field ``phi`` on the section y = 0.

    parity: 'odd' or 'even' to draw the mirrored x < 0 half of a layout computed on x >= 0 (with the
    sign of that symmetry), or None to draw only what was computed."""
    import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm, TwoSlopeNorm
    from matplotlib.tri import Triangulation

    xz, tri, elem, nodes = section_triangles(problem)
    # Potential at the mesh vertices: the nodal DOFs of P1 and P2 elements are the vertex values.
    vals_v = phi[problem.basis.nodal_dofs[0]][nodes]
    md = problem.md
    mirror = md.clipped.get("x", False) and parity in ("odd", "even")
    X, Z, T = xz[0], xz[1], tri
    if mirror:
        sign = -1.0 if parity == "odd" else 1.0
        X = np.concatenate([X, -X])
        Z = np.concatenate([Z, Z])
        T = np.hstack([tri, tri[[0, 2, 1]] + xz.shape[1]])
        vals_v = np.concatenate([vals_v, sign * vals_v])
    triang = Triangulation(X, Z, T.T)
    if quantity == "potential":
        vmax = vlim if vlim is not None else max(abs(vals_v.min()), abs(vals_v.max()))
        norm = TwoSlopeNorm(vmin=-vmax, vcenter=0.0, vmax=vmax) if vals_v.min() < 0 else None
        im = ax.tripcolor(triang, vals_v, shading="gouraud", cmap=diverging_cmap(), norm=norm, rasterized=True)
        lv = levels if levels is not None else np.linspace(-0.45, 0.45, 19)
        ax.tricontour(triang, vals_v, levels=lv, colors=COLORS["neutral"], linewidths=0.35)
        label = r"Potential $\varphi_o$ (V)"
    elif quantity == "energy":
        from .constants import EPS0
        g = problem.grad_at_elements(phi)                                 # (dim, M) mean gradient
        dens = problem.eps_r_elem * EPS0 * np.sum(g ** 2, axis=0)          # eps |grad phi|^2
        dens_t = dens[elem]
        if mirror:
            dens_t = np.concatenate([dens_t, dens_t])
        pos = dens_t[dens_t > 0]
        lo = vlim[0] if vlim else np.percentile(pos, 2)
        hi = vlim[1] if vlim else pos.max()
        im = ax.tripcolor(triang, facecolors=np.clip(dens_t, lo, hi), shading="flat", cmap=sequential_cmap(),
                          norm=LogNorm(vmin=lo, vmax=hi), rasterized=True)
        label = r"$\varepsilon|\nabla\varphi|^2$ (fF mm$^{-3}$ at 1 V)"
    else:
        raise ValueError("quantity must be 'potential' or 'energy'")
    if outline:
        draw_section(ax, problem.layout, window=None, outline_only=True)
    if window:
        ax.set_xlim(*window[0])
        ax.set_ylim(*window[1])
    ax.set_aspect("equal")
    ax.set_xlabel(r"$x$ (mm)")
    ax.set_ylabel(r"$z$ (mm)")
    if colorbar:
        cb = plt.colorbar(im, ax=ax, shrink=0.85, pad=0.02)
        cb.set_label(label)
        if quantity == "energy":
            from matplotlib.ticker import LogFormatterMathtext
            cb.formatter = LogFormatterMathtext()
            cb.update_ticks()
    return im


def _element_measures(problem) -> np.ndarray:
    """Volume (3-D) or area (2-D) of every element: |det| of the edge vectors / dim!."""
    p, t = problem.mesh.p, problem.mesh.t
    v0 = p[:, t[0]]
    edges = np.stack([p[:, t[k]] - v0 for k in range(1, t.shape[0])], axis=1)   # (dim, dim, M)
    det = np.linalg.det(np.moveaxis(edges, -1, 0))                            # (M,)
    return np.abs(det) / (6.0 if problem.md.dim == 3 else 2.0)


def coupling_map(ax, problem, phi_o, phi_e, window=None, vlim=None, colorbar: bool = True,
                 outline: bool = True):
    """Map the density of C_F, eps (|grad phi_o|^2 - |grad phi_e|^2), on the section y = 0 (module
    docstring).  phi_o and phi_e are the odd and even solutions (A at +-1/2 V, both at 1/2 V).

    The value of each triangle of the section is the exact mean over the element it belongs to.
    The x < 0 half of a layout computed on x >= 0 is drawn by mirror symmetry; both squared
    gradients are even under the mirror, so the density is drawn unchanged there."""
    import matplotlib.pyplot as plt
    from matplotlib.colors import SymLogNorm
    from matplotlib.tri import Triangulation

    xz, tri, elem, _ = section_triangles(problem)
    vol = _element_measures(problem)
    dens = (problem.elemental(phi_o, phi_o) - problem.elemental(phi_e, phi_e)) / vol
    dens_t = dens[elem]
    X, Z, T = xz[0], xz[1], tri
    if problem.md.clipped.get("x", False):
        X = np.concatenate([X, -X])
        Z = np.concatenate([Z, Z])
        T = np.hstack([tri, tri[[0, 2, 1]] + xz.shape[1]])
        dens_t = np.concatenate([dens_t, dens_t])
    triang = Triangulation(X, Z, T.T)
    hi = vlim if vlim is not None else float(np.max(np.abs(dens_t)))
    # Linear within 1e-4 of the largest magnitude, logarithmic above: four decades on each side.
    norm = SymLogNorm(linthresh=1e-4 * hi, vmin=-hi, vmax=hi, base=10)
    im = ax.tripcolor(triang, facecolors=np.clip(dens_t, -hi, hi), shading="flat", cmap=diverging_cmap(),
                      norm=norm, rasterized=True)
    if outline:
        draw_section(ax, problem.layout, window=None, outline_only=True)
    if window:
        ax.set_xlim(*window[0])
        ax.set_ylim(*window[1])
    ax.set_aspect("equal")
    ax.set_xlabel(r"$x$ (mm)")
    ax.set_ylabel(r"$z$ (mm)")
    if colorbar:
        cb = plt.colorbar(im, ax=ax, shrink=0.85, pad=0.02)
        cb.set_label(r"$\varepsilon(|\nabla\varphi_o|^2 - |\nabla\varphi_e|^2)$ (fF mm$^{-3}$)")
        # ticks at 0 and at every other decade on each side, so that the labels do not crowd
        import math
        k_hi = math.floor(math.log10(hi))
        k_lo = math.ceil(math.log10(1e-4 * hi))
        ks = list(range(k_hi, k_lo - 1, -2))
        cb.set_ticks(sorted([-(10.0 ** k) for k in ks] + [0.0] + [10.0 ** k for k in ks]))
    return im


def mesh_map(ax, problem, window=None, parity_mirror: bool = True) -> None:
    """Draw the mesh on the section y = 0 (3-D) or the whole 2-D mesh."""
    from matplotlib.tri import Triangulation
    xz, tri, _, _ = section_triangles(problem)
    X, Z, T = xz[0], xz[1], tri
    if parity_mirror and problem.md.clipped.get("x", False):
        X, Z = np.concatenate([X, -X]), np.concatenate([Z, Z])
        T = np.hstack([tri, tri[[0, 2, 1]] + xz.shape[1]])
    ax.triplot(Triangulation(X, Z, T.T), color=COLORS["neutral"], lw=0.15)
    draw_section(ax, problem.layout, outline_only=True)
    if window:
        ax.set_xlim(*window[0])
        ax.set_ylim(*window[1])
    ax.set_aspect("equal")
    ax.set_xlabel(r"$x$ (mm)")
    ax.set_ylabel(r"$z$ (mm)")


def convergence_plot(ax, conv, label: str = r"$C_F$", unit: str = "fF", exact: float | None = None) -> None:
    """C_F against the number of unknowns for the levels of a ``study.Convergence``, with the
    extrapolated value (dashed) when the extrapolation applies."""
    from matplotlib.ticker import LogFormatterMathtext
    n = [lv["dofs"] for lv in conv.levels]
    c = [lv["C_F"] for lv in conv.levels]
    ax.plot(n, c, "o-", color=COLORS["primary"], lw=LINEWIDTH, ms=3.5, label=f"{label}, finite elements")
    if conv.C_F.get("extrapolated") is not None:
        ax.axhline(conv.C_F["extrapolated"], color=COLORS["neutral"], lw=LINEWIDTH, ls=DASHED,
                   label="Richardson extrapolation")
    if exact is not None:
        ax.axhline(exact, color=COLORS["warm_accent"], lw=LINEWIDTH, ls=DASHED, label="exact")
    ax.set_xscale("log")
    ax.xaxis.set_major_formatter(LogFormatterMathtext())
    ax.set_xlabel("Unknowns")
    ax.set_ylabel(f"{label} ({unit})")
    ax.legend()
