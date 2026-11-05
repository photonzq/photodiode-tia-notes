"""Look at the three-dimensional layouts as the solver receives them, before any mesh is made.

Why this script exists
----------------------
The field solutions are only as good as the geometry they are given.  This script builds the layouts
of g_resistor_3d.py (the OPA855 network) and g_opa846_3d.py (the three OPA846 layouts) exactly as the
study scripts build them and, without meshing or solving anything,
  1. draws each one from above, in an isometric view, and in an (x, z) section through the feedback
     pins, so that positions, heights and contacts can be compared with the package drawings;
  2. checks that the metal of every net is one connected piece: two boxes of the same net are taken
     as connected when their closed x, y and z intervals all overlap or touch (to 1e-9 mm).  A net in
     several pieces is not wrong for the solver (all pieces get the net's potential), but it would
     mean that the geometry differs from the intended layout, for example a lead that does not reach
     its pad;
  3. writes every item with its role and extent to a text file, for reading next to the drawings.

Run:  python inspect_layouts.py [out_dir]        (default: ../../../figures/inspect, not published)
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[4] / "pcbcap"))
sys.path.insert(0, str(HERE.parent))

import matplotlib                                   # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt                     # noqa: E402
from matplotlib.patches import Rectangle            # noqa: E402

from pcbcap import plotting                         # noqa: E402
from pcbcap.geometry import Box, Conductor, Dielectric, Film, Sheet   # noqa: E402

import g_opa846_3d as g846                          # noqa: E402
import g_resistor_3d as g855                        # noqa: E402

TOL = 1e-9


def layouts():
    """(name, layout, (x window, y window, z window), y of the section) for each layout."""
    out = [("opa855_network_plane", g855.opa855_layout(with_package=True, plane=True),
            ((-1.6, 1.4), (-0.8, 2.0), (-0.4, 1.0)), 0.0)]
    for name in ("double_sided", "under_body", "around"):
        lay = g846.opa846_layout(name, "0402")
        y_sec = 0.95 if name != "around" else -0.95    # the pin row that carries the feedback net
        out.append((f"opa846_{name}_0402", lay, ((-2.8, 2.8), (-2.6, 2.6), (-1.9, 1.4)), y_sec))
    return out


def section_at_y(ax, lay, y, window):
    """(x, z) section of a 3-D layout at the plane y = const: every box that the plane cuts."""
    for it in lay.items:
        if not isinstance(it, Box):
            continue
        ext = lay.item_extent(it)
        if not (ext["y"][0] - TOL <= y <= ext["y"][1] + TOL):
            continue
        st = plotting._role_style(it.role)
        if st is None:
            continue
        (x0, x1), (z0, z1) = ext["x"], ext["z"]
        if it.role.__class__.__name__ == "Dielectric" and it.role.name == "board":
            st = dict(st, alpha=0.15)
        ax.add_patch(Rectangle((x0, z0), x1 - x0, z1 - z0, **st))
    for it in lay.items:   # sheets cut by the plane: planes (normal z) and films
        if isinstance(it, Sheet) and it.normal == "z":
            sp = it.spans
            if sp["y"][0] - TOL <= y <= sp["y"][1] + TOL:
                col = plotting.FILM_COLOR if isinstance(it.role, Film) else plotting.net_color(it.role.net)
                segs = [(sp["x"][0], sp["x"][1])]
                for h in it.holes:   # leave the cut-out open where the section crosses it
                    if h["y"][0] < y < h["y"][1]:
                        segs = [(a, h["x"][0]) for a, b in segs if a < h["x"][0]] + \
                               [(h["x"][1], b) for a, b in segs if b > h["x"][1]]
                for a, b in segs:
                    ax.plot([a, b], [it.at, it.at], color=col, lw=1.6, solid_capstyle="butt")
    ax.set_xlim(*window[0])
    ax.set_ylim(*window[2])
    ax.set_aspect("equal")
    ax.set_xlabel(r"$x$ (mm)")
    ax.set_ylabel(r"$z$ (mm)")


def touching(e1, e2) -> bool:
    return all(e1[a][0] <= e2[a][1] + TOL and e2[a][0] <= e1[a][1] + TOL for a in "xyz")


def net_pieces(lay):
    """For each net, the connected pieces of its boxes (lists of item names)."""
    boxes = {}
    for it in lay.items:
        if isinstance(it, Box) and isinstance(it.role, Conductor):
            boxes.setdefault(it.role.net, []).append(it)
    pieces = {}
    for net, items in boxes.items():
        ext = [lay.item_extent(it) for it in items]
        parent = list(range(len(items)))

        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                if touching(ext[i], ext[j]):
                    parent[find(i)] = find(j)
        groups = {}
        for i, it in enumerate(items):
            groups.setdefault(find(i), []).append(it.name)
        pieces[net] = list(groups.values())
    return pieces


def describe(lay) -> list[str]:
    lines = [f"layout: {lay.name}"]
    for it in lay.items:
        ext = lay.item_extent(it)
        r = it.role
        if isinstance(r, Dielectric):
            role = f"dielectric {r.name} (eps_r {r.eps_r})"
        elif isinstance(r, Film):
            role = f"film {r.lo} -> {r.hi}"
        else:
            role = f"conductor net {r.net}" + (" (floating)" if r.floating else "")
        kind = type(it).__name__
        span = "  ".join(f"{a} {ext[a][0]:+.4f}..{ext[a][1]:+.4f}" for a in "xyz" if a in ext)
        lines.append(f"  {kind:5s} {it.name:24s} {role:34s} {span}")
    return lines


def main() -> None:
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parents[3] / "figures" / "inspect"
    out_dir.mkdir(parents=True, exist_ok=True)
    plotting.use_style()
    report = []
    for name, lay, win, y_sec in layouts():
        fig = plt.figure(figsize=(7.0, 2.6))
        ax1 = fig.add_subplot(1, 3, 1)
        plotting.draw_top(ax1, lay, window=(win[0], win[1]))
        ax1.axhline(y_sec, color="k", lw=0.4, ls=":")
        ax2 = fig.add_subplot(1, 3, 2, projection="3d")
        plotting.draw_iso(ax2, lay, win)
        ax3 = fig.add_subplot(1, 3, 3)
        section_at_y(ax3, lay, y_sec, win)
        ax3.set_title(f"section at y = {y_sec:+.2f} mm", fontsize=7)
        fig.suptitle(lay.name, fontsize=8)
        fig.tight_layout()
        fig.savefig(out_dir / f"{name}.png", dpi=220)
        plt.close(fig)
        pieces = net_pieces(lay)
        report += describe(lay)
        report.append("  connected pieces of metal per net:")
        for net, groups in sorted(pieces.items()):
            flag = "" if len(groups) == 1 or net == "gnd" else "   <-- more than one piece"
            report.append(f"    {net}: {len(groups)} piece(s){flag}")
            if len(groups) > 1:
                for g in groups:
                    report.append(f"        {g}")
        report.append("")
    (out_dir / "layout_items.txt").write_text("\n".join(report), encoding="utf-8")
    print("\n".join(line for line in report if "piece" in line or line.startswith("layout")))
    print(f"figures and item list in {out_dir}")


if __name__ == "__main__":
    main()
