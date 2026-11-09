"""Checking the field solutions of Section G.14 with FasterCap, a solver unrelated to pcbcap.

Usage (from this folder):
    python fastercap_validation.py list
    python fastercap_validation.py export <case>|all     # input files, geometry check, panel views
    python fastercap_validation.py run <case> [--tol 0.01 0.003 0.001 0.0003] [--galerkin] [--timeout s]
    python fastercap_validation.py pcbcap r0402_nofilm   # the film-free 0402 in pcbcap (box and enclosure studies)
    python fastercap_validation.py fastcap2 <case> [--options "-o3 -t0.001"] [--timeout s]   # the same panels in FastCap 2.0
    python fastercap_validation.py fastcap2-plan <case> [--orders 2 3] [--depth n]   # FastCap2's partitioning, from the panels alone
    python fastercap_validation.py backfill <case> [--timeout-tag m100_g_d0.0001 --timeout 1800]   # checks of each solve, from the logs
    python fastercap_validation.py report                # data/parasitic_cf/fastercap/README.md

Why this script exists
----------------------
pcbcap solves Laplace's equation by finite elements inside a grounded box; FasterCap solves the same
equations by boundary elements in free space.  pcbcap/pcbcap/fastercap.py explains both methods and how
a layout is translated into FasterCap's input.  Their discretisation errors are unrelated, so agreement
within the errors each states checks both.  The cases:
  * cube_free and cube_eps4p2_free: a conductor cube of 1 mm alone in space, in air and in a medium of
    relative permittivity 4.2.  The capacitance of a cube of edge a is 0.6606782(1) x 4 pi eps0 a
    (C.-O. Hwang and M. Mascagni, "Electrical capacitance of the unit cube", J. Appl. Phys. 95, 3798
    (2004), abstract; https://doi.org/10.1063/1.1664031), 73.510 fF for 1 mm, and 4.2 times that in the
    medium.  They check FasterCap and the export against a known answer.
  * r0402_nofilm_box8: the 0402 model of Section G.14.4 (g_resistor_3d.layout, the same permittivities
    and dimensions) with its film removed, in the same grounded box of half-width 8 mm.  Both programs
    solve exactly the same model: the box becomes a grounded conductor (exact) and nothing is translated
    approximately.  This is the like-for-like test.
  * r0402_nofilm_free8, _free16, _free32: the same in free space on boards 16, 32 and 64 mm square,
    extrapolated in 1/R, against pcbcap's extrapolation over boxes of the same sizes (Eq. (G.57)).
  * r0402_nofilm_air_box8 and r0402_nofilm_finemetal_box8: the two tests of the side note's
    Appendix D, which ask whether the thin metal is why FasterCap fails on r0402_nofilm_box8.  The
    first is that model with every permittivity 1, where the split of the charge between the two faces
    of a metal no longer enters the capacitance; pcbcap solves the same (command "pcbcap
    r0402_nofilm_air").  The second keeps the dielectrics and cuts every face of the metal into panels
    no wider than the metal is thick (fastercap.ExportOptions.metal_panel = 1), against pcbcap's
    r0402_nofilm.
  * r0402_nofilm_fine_box8 cuts, in addition, every face inside a window of 1.7 x 0.7 x 0.47 mm around
    the part into panels of 30 um or less (ExportOptions.fine_window, fine_panel), and
    r0402_nofilm_fine_max1_box8, _max0p5_, _max0p25_ also cut every face outside the window into panels
    no longer than 1, 0.5 and 0.25 mm (ExportOptions.max_panel); r0402_nofilm_air_fine_max0p5_box8 is the
    0.5-mm case in the uniform medium, its control against pcbcap's r0402_nofilm_air.  They are solved on the panels as
    exported: "run <case> --mesh 100 --galerkin --extra d0.0001" (FasterCap's -m100 stops its own
    refinement; -d, the "direct potential interaction coefficient to mesh refinement ratio", sets the
    compression of the interaction links relative to -m, FasterCap help, Run chapter 1, so -m100 alone,
    with the default -d1, also compresses the links: 3.4 links per panel on r0402_nofilm_fine_box8,
    against 418 to 534 in the converged uniform-medium runs at -m0.07 to -m0.035).
  * r0402_strips10_box8, _strips20_, _strips40_: the published 0402 with its film cut into 10, 20 and 40
    strips (2 um thick, 2-um gaps), against Table G.11 (40.15 fF in the 8-mm box, extrapolated in the
    mesh).  The strips overstate C_F by about 5.1, 2.0 and 0.76 fF (fastercap.py, "Two translations are
    approximate"), so this case checks the film only to that level.
What each command writes, under data/parasitic_cf/fastercap/:
  * <case>/: FasterCap's input (<case>.lst and its panel files), <case>.json (what the reader needs),
    geometry_check.json (the panel areas against gmsh's fragments), one log per FasterCap run and
    results.json (every run's numbers);
  * views/: the panels seen from six sides (export); every new geometry is looked at before it is run;
  * <case>/fastcap2/ (fastcap2): the case's panel files in FastCap 2.0's format, FastCap2's own console
    output of every run (fastcap2_<options>.log) and results.json;
  * pcbcap_r0402_nofilm.json: pcbcap's convergence and enclosure studies of the film-free 0402;
  * README.md (report): the convergence tables of both programs.  They are kept here, not in the note.
Every FasterCap run is at below-normal priority with two threads (pcbcap.fastercap.run_fastercap), and
the pcbcap studies run as in g_resistor_3d.py (two threads, lowered priority).
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import subprocess
import sys
import time
from dataclasses import replace
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[4] / "pcbcap"))
sys.path.insert(0, str(HERE.parent))

import g_resistor_3d as g3                                # noqa: E402
from pcbcap import fastercap as fc                        # noqa: E402
from pcbcap import materials as mat                       # noqa: E402
from pcbcap import parts, study                           # noqa: E402
from pcbcap.constants import EPS0                         # noqa: E402
from pcbcap.geometry import Film, Layout, Sheet           # noqa: E402

DATA = HERE.parents[3] / "data" / "parasitic_cf" / "fastercap"
# FasterCap's executable: the environment variable FASTERCAP, else the installer's default location.
EXE = os.environ.get("FASTERCAP", r"C:\Program Files (x86)\FastFieldSolvers\FasterCap\FasterCap.exe")
CUBE = 0.6606782                    # C / (4 pi eps0 a) of a cube (Hwang and Mascagni 2004)
TOLS = (0.01, 0.003, 0.001, 0.0003)
TABLE_G11_0402_BOX8 = (40.15, 0.07)  # C_F (fF) and its discretisation error, 8-mm box (Table G.11)
TABLE_G11_0402_FREE = 42.5           # C_F (fF) with no ground nearby (Table G.11)


def cube(eps: float) -> Layout:
    lay = Layout(3, f"cube of 1 mm in a medium of eps {eps:g}")
    lay.add_box((-0.5, 0.5), (-0.5, 0.5), (-0.5, 0.5), net="A", name="cube")
    lay.set_enclosure(margin=2.0, material="air" if eps == 1.0 else mat.custom("medium", eps))
    return lay


def r0402(half: float = 8.0, film: bool = True, board_half: float | None = None,
          eps_pcb: float = g3.EPS_PCB, eps_al: float = g3.EPS_AL) -> Layout:
    """The 0402 of Section G.14.4 (g_resistor_3d.layout).  With ``board_half`` the board is that size
    (a free-space model) and the enclosure, which then only has to contain it, is 1 mm larger.
    ``eps_pcb`` and ``eps_al`` replace the permittivities of the board and of the body; 1 and 1 give
    the uniform medium of case r0402_nofilm_air_box8."""
    board = None
    if board_half is not None:
        board = parts.Board(material=mat.custom("FR4", eps_pcb), size=(2 * board_half, 2 * board_half))
        half = board_half + 1.0
    lay = g3.layout("0402", eps_pcb=eps_pcb, eps_al=eps_al, half=half, board=board)
    if not film:
        lay.items = [it for it in lay.items if not (isinstance(it, Sheet) and isinstance(it.role, Film))]
        lay.name += ", film removed"
    return lay


def cube_on_block(size: float = 40.0) -> Layout:
    """A conductor cube of 1 mm whose centre lies on the top face of a dielectric block (eps 4.2) of
    size x size x size/2 mm.  For a conductor that is its own mirror image in the plane between two
    half-spaces, the free-space potential already meets the interface conditions (its normal field on
    the plane is zero), so the capacitance is exactly (eps1 + eps2)/2 = 2.6 times that in air; a finite
    block gives somewhat less, because the field far from the cube leaves it.  The case tests the
    export's conductor faces in two media and its dielectric panels against that bound."""
    lay = Layout(3, f"cube on a dielectric block of {size:g} mm")
    lay.add_box((-size / 2, size / 2), (-size / 2, size / 2), (-size / 2, 0.0), eps_r=4.2, label="block")
    lay.add_box((-0.5, 0.5), (-0.5, 0.5), (-0.5, 0.5), net="A", name="cube")
    lay.set_enclosure(margin=1.0)
    return lay


CASES = {
    "cube_free": dict(make=lambda: cube(1.0), opt=dict(boundary="free"), exact=CUBE * 4 * math.pi * EPS0),
    "cube_on_block40_free": dict(make=lambda: cube_on_block(40.0), opt=dict(boundary="free"),
                                 exact=2.6 * CUBE * 4 * math.pi * EPS0),   # the half-space limit, an upper bound
    "cube_eps4p2_free": dict(make=lambda: cube(4.2), opt=dict(boundary="free"),
                             exact=4.2 * CUBE * 4 * math.pi * EPS0),
    "r0402_nofilm_box8": dict(make=lambda: r0402(8.0, film=False), opt=dict(boundary="ground", films="drop")),
    "r0402_nofilm_free8": dict(make=lambda: r0402(film=False, board_half=8.0), opt=dict(boundary="free", films="drop")),
    "r0402_nofilm_free16": dict(make=lambda: r0402(film=False, board_half=16.0), opt=dict(boundary="free", films="drop")),
    "r0402_nofilm_free32": dict(make=lambda: r0402(film=False, board_half=32.0), opt=dict(boundary="free", films="drop")),
    # The two tests of the side note's Appendix D, both in the grounded 8-mm box: every permittivity 1,
    # so that the split of the charge between the two faces of a metal drops out of the free charge; and
    # the dielectrics kept, with every face of the metal cut into panels no wider than the metal is thick.
    "r0402_nofilm_air_box8": dict(make=lambda: r0402(8.0, film=False, eps_pcb=1.0, eps_al=1.0),
                                  opt=dict(boundary="ground", films="drop")),
    "r0402_nofilm_finemetal_box8": dict(make=lambda: r0402(8.0, film=False),
                                        opt=dict(boundary="ground", films="drop", metal_panel=1.0)),
    # A third test: the metal as in finemetal, and every face within the part's window, dielectric ones
    # included (the alumina's faces and the board's top around the pads), cut into panels of 30 um or
    # less, the size of the stand-off.
    # The same panels in a uniform medium, a check of the FastCap 2.0 set-up against pcbcap's
    # r0402_nofilm_air (FastCap 2.0 never refines, so it needs the fine panels).
    "r0402_nofilm_air_fine_box8": dict(make=lambda: r0402(8.0, film=False, eps_pcb=1.0, eps_al=1.0),
                                       opt=dict(boundary="ground", films="drop", metal_panel=1.0,
                                                fine_window=((-0.85, 0.85), (-0.35, 0.35), (-0.02, 0.45)),
                                                fine_panel=0.03)),
    "r0402_nofilm_fine_box8": dict(make=lambda: r0402(8.0, film=False),
                                   opt=dict(boundary="ground", films="drop", metal_panel=1.0,
                                            fine_window=((-0.85, 0.85), (-0.35, 0.35), (-0.02, 0.45)),
                                            fine_panel=0.03)),
    # A fourth test: the panels of r0402_nofilm_fine_box8, and every face outside the part's window (the
    # board's top beyond the window, the board's bottom 1.6 mm below the pads, the box) cut into panels no
    # longer than 1, 0.5 and 0.25 mm (fastercap.ExportOptions.max_panel).  In r0402_nofilm_fine_box8 those
    # faces are whole: up to 16 mm, the box 14 panels and the board's bottom one panel.  Solved without
    # refinement (-m100) and with the interaction links kept down to the input panels (-d small).
    "r0402_nofilm_fine_max1_box8": dict(make=lambda: r0402(8.0, film=False),
                                        opt=dict(boundary="ground", films="drop", metal_panel=1.0,
                                                 fine_window=((-0.85, 0.85), (-0.35, 0.35), (-0.02, 0.45)),
                                                 fine_panel=0.03, max_panel=1.0)),
    "r0402_nofilm_fine_max0p5_box8": dict(make=lambda: r0402(8.0, film=False),
                                          opt=dict(boundary="ground", films="drop", metal_panel=1.0,
                                                   fine_window=((-0.85, 0.85), (-0.35, 0.35), (-0.02, 0.45)),
                                                   fine_panel=0.03, max_panel=0.5)),
    "r0402_nofilm_fine_max0p25_box8": dict(make=lambda: r0402(8.0, film=False),
                                           opt=dict(boundary="ground", films="drop", metal_panel=1.0,
                                                    fine_window=((-0.85, 0.85), (-0.35, 0.35), (-0.02, 0.45)),
                                                    fine_panel=0.03, max_panel=0.25)),
    # The control of the fourth test: the same panels as r0402_nofilm_fine_max0p5_box8 in the uniform medium,
    # solved the same way, against pcbcap's r0402_nofilm_air.
    "r0402_nofilm_air_fine_max0p5_box8": dict(make=lambda: r0402(8.0, film=False, eps_pcb=1.0, eps_al=1.0),
                                              opt=dict(boundary="ground", films="drop", metal_panel=1.0,
                                                       fine_window=((-0.85, 0.85), (-0.35, 0.35), (-0.02, 0.45)),
                                                       fine_panel=0.03, max_panel=0.5)),
    "r0402_strips10_box8": dict(make=lambda: r0402(8.0), opt=dict(boundary="ground", films="strips", film_strips=10)),
    "r0402_strips20_box8": dict(make=lambda: r0402(8.0), opt=dict(boundary="ground", films="strips", film_strips=20)),
    "r0402_strips40_box8": dict(make=lambda: r0402(8.0), opt=dict(boundary="ground", films="strips", film_strips=40)),
    # Free space, because FasterCap does not solve the grounded-box models reliably (README.md): the film
    # as 10, 20 and 40 strips on the 16-mm board, and 20 strips on the 32- and 64-mm boards for the
    # extrapolation to an infinite board.
    "r0402_strips10_free8": dict(make=lambda: r0402(board_half=8.0), opt=dict(boundary="free", films="strips", film_strips=10)),
    "r0402_strips20_free8": dict(make=lambda: r0402(board_half=8.0), opt=dict(boundary="free", films="strips", film_strips=20)),
    "r0402_strips40_free8": dict(make=lambda: r0402(board_half=8.0), opt=dict(boundary="free", films="strips", film_strips=40)),
    "r0402_strips20_free16": dict(make=lambda: r0402(board_half=16.0), opt=dict(boundary="free", films="strips", film_strips=20)),
    "r0402_strips20_free32": dict(make=lambda: r0402(board_half=32.0), opt=dict(boundary="free", films="strips", film_strips=20)),
}
VIEWED = ("cube_free", "r0402_nofilm_box8", "r0402_nofilm_free8", "r0402_strips10_box8", "r0402_nofilm_air_box8",
          "r0402_nofilm_finemetal_box8", "r0402_nofilm_fine_box8", "r0402_nofilm_air_fine_box8",
          "r0402_nofilm_fine_max1_box8", "r0402_nofilm_fine_max0p5_box8", "r0402_nofilm_fine_max0p25_box8",
          "r0402_nofilm_air_fine_max0p5_box8")
PART_WINDOW = ((-0.85, 0.85), (-0.35, 0.35), (-0.02, 0.45))   # the 0402, its pads and solder (mm)


def _export(name: str):
    """Export case ``name``; returns (fc.Export, fc.ExportOptions)."""
    spec = CASES[name]
    opt = fc.ExportOptions(**spec["opt"])
    return fc.export(spec["make"](), DATA / name, name, opt), opt


def largest_sides(ex, opt) -> dict:
    """The longest panel side (mm) inside and outside the fine window, and on the grounded box, so that
    the limits fine_panel and max_panel can be checked on what was written.  A panel counts as inside
    when its centre lies inside the window."""
    q = ex.panels.quad
    side = np.maximum(np.linalg.norm(q[:, 1] - q[:, 0], axis=1), np.linalg.norm(q[:, 3] - q[:, 0], axis=1))
    centre = q.mean(axis=1)
    inside = np.zeros(len(q), dtype=bool)
    if opt.fine_window is not None:
        inside = np.all([(centre[:, i] > w[0]) & (centre[:, i] < w[1]) for i, w in enumerate(opt.fine_window)], axis=0)
    box = np.array([k[0] == "C" and k[1] == "gnd" for k in ex.panels.key])
    out = dict(inside_window=float(side[inside].max()) if inside.any() else None,
               outside_window=float(side[~inside].max()) if (~inside).any() else None,
               box=float(side[box].max()) if box.any() else None,
               panels_inside_window=int(inside.sum()), panels_box=int(box.sum()))
    return out


def cmd_export(name: str) -> None:
    ex, opt = _export(name)
    cmp_ = fc.compare_areas(ex.panels.areas_by_key(), fc.gmsh_areas(ex.layout, opt.boundary))
    rec = dict(case=name, panels=ex.panels.stats["panels"], cells=ex.panels.stats["cells"],
               smallest_side_mm=ex.panels.stats["smallest_side_mm"], worst_relative_area_difference=cmp_["worst"],
               total_area_mm2=cmp_["total_other"], rows=cmp_["rows"], notes=ex.meta["notes"],
               largest_side_mm=largest_sides(ex, opt))
    (DATA / name / "geometry_check.json").write_text(json.dumps(rec, indent=1), encoding="utf-8", newline="\n")
    print(f"{name}: {rec['panels']} panels; areas against gmsh's fragments: worst relative difference "
          f"{rec['worst_relative_area_difference']:.1e} over {len(cmp_['rows'])} kinds")
    ls = rec["largest_side_mm"]
    print(f"  longest panel side: {ls['inside_window']} mm inside the fine window ({ls['panels_inside_window']} panels), "
          f"{ls['outside_window']} mm outside it, {ls['box']} mm on the box ({ls['panels_box']} panels)")
    for n in ex.meta["notes"]:
        print("  " + n)
    if name in VIEWED:
        fc.draw_panels(ex, DATA / "views" / name, title=ex.layout.name)
        if ex.meta["films"]:
            z = [it.spans["z"] for it in ex.layout.items if it.name.startswith("R_film_s")]
            z0, z1 = min(a for a, _ in z), max(b for _, b in z)
            win = ((-0.42, 0.42), (-0.32, 0.32), (z0 - 0.04, z1 + 0.03))
            fc.draw_panels(ex, DATA / "views" / f"{name}_film", window=win, z_stretch=4.0,
                           title=ex.layout.name + ": the film's strips and the terminations")
        if name.startswith("r0402_nofilm") and name.endswith("_box8"):
            fc.draw_panels(ex, DATA / "views" / f"{name}_part", window=PART_WINDOW, z_stretch=1.0,
                           title=ex.layout.name + ": the panels on and around the part")
        if opt.boundary == "ground" and opt.max_panel is not None:
            # The whole model: the closed box hides its inside, so each view stops 0.05 mm short of the
            # box's faces between the viewer and the board (fc.draw_panels, windows).
            enc = ex.layout.enclosure.spans
            (x0, x1), (y0, y1), (z0, z1) = enc["x"], enc["y"], enc["z"]
            g = 0.05
            fc.draw_panels(ex, DATA / "views" / f"{name}_whole",
                           views=[("from above, box lid left out", 90.0, -90.0),
                                  ("from below, box floor left out", -90.0, -90.0),
                                  ("front left, lid and near walls left out", 24.0, -58.0)],
                           windows=[((x0, x1), (y0, y1), (z0, z1 - g)), ((x0, x1), (y0, y1), (z0 + g, z1)),
                                    ((x0 + g, x1), (y0 + g, y1), (z0, z1 - g))],
                           panel=(3.4, 3.4),
                           title=ex.layout.name + f": the whole model, panels outside the part's window "
                                                  f"no longer than {opt.max_panel:g} mm")
        if opt.boundary == "free" and not name.startswith("cube"):
            enc = ex.layout.enclosure.spans
            win = (enc["x"], enc["y"], (-1.9, 0.6))
            fc.draw_panels(ex, DATA / "views" / f"{name}_whole", window=win, z_stretch=2.0,
                           title=ex.layout.name + ": the whole board in free space")
        print(f"  views written to {DATA / 'views'}")


def cmd_view(name: str, out: Path, z_stretch: float = 1.0) -> None:
    """Export case ``name`` into ``out`` rather than its own folder (which a running FasterCap may be
    reading), print the extent of every box of the layout within PART_WINDOW, and draw the panels of the
    part at the given z stretch (1: true proportions), to check the part's dimensions by eye."""
    spec = CASES[name]
    opt = fc.ExportOptions(**spec["opt"])
    out.mkdir(parents=True, exist_ok=True)
    ex = fc.export(spec["make"](), out, name, opt)
    print(f"{name}: boxes within the part's window (mm):")
    for it in ex.layout.items:
        sp = getattr(it, "spans", None)
        if sp is None or isinstance(it, Sheet):
            continue
        inside = all(sp[a][0] < PART_WINDOW[i][1] and sp[a][1] > PART_WINDOW[i][0] for i, a in enumerate("xyz"))
        if not inside or (sp["x"][1] - sp["x"][0] > 5.0):          # leave out the board and the enclosure
            continue
        role = it.role
        what = f"net {role.net}" if hasattr(role, "net") else f"eps {getattr(role, 'eps_r', '?')}"
        ext = "  ".join(f"{a} {sp[a][0]:+.4f}..{sp[a][1]:+.4f} ({sp[a][1] - sp[a][0]:.4f})" for a in "xyz")
        print(f"  {it.name or type(it).__name__:24s} {what:10s} {ext}")
    fc.draw_panels(ex, out / f"{name}_part_true", window=PART_WINDOW, z_stretch=z_stretch,
                   title=ex.layout.name + (": the part at true proportions" if z_stretch == 1.0 else
                                           f": the part, z drawn {z_stretch:g} times enlarged"))
    print(f"  view written to {out / (name + '_part_true')}.png")


# ================================================================================================
# FastCap 2.0 (the MIT program, FastFieldSolvers' Windows port) on the same panels
# ================================================================================================
FASTCAP2 = os.environ.get("FASTCAP2", r"C:\Program Files (x86)\FastFieldSolvers\FastCap2\FastCap2.exe")
# FastCap 2.0 takes one reference point per dielectric file and no per-panel point (its user's guide,
# PDF p. 15, section 1.3).  In these layouts every dielectric file holds the exposed faces of one convex
# body, so a point inside that body, flagged '-' (the inner side), serves all its panels.  Keyed by the
# body's relative permittivity; points in metres.
FASTCAP2_INNER = {4.2: (0.0, 0.0, -8.0e-4),     # the FR-4 board's centre (1.6 mm thick, top face at z = 0)
                  9.7: (0.0, 0.0, 2.4e-4)}      # the 0402 body's centre (z from 0.065 to 0.415 mm)


def _quad_normal(c: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Centre and (unnormalised) normal of a planar quadrilateral given as a (4, 3) array."""
    return c.mean(axis=0), np.cross(c[1] - c[0], c[3] - c[0])


def fastcap2_files(name: str, out: Path) -> dict:
    """Write case ``name``'s FasterCap input in FastCap 2.0's format into ``out``: every panel file's
    first line becomes a title line beginning with '0' (guide, PDF pp. 12-13); dielectric panels lose
    their per-panel reference points; every D line gets the point inside its body (FASTCAP2_INNER)
    with '-'.  Checks that this point lies on the inner side of every panel of its file, i.e. on the
    side opposite to the panel's own reference point.  Returns the list file's name and the files."""
    src = DATA / name
    out.mkdir(parents=True, exist_ok=True)
    lines = (src / f"{name}.lst").read_text(encoding="utf-8").splitlines()
    new, files = [], []
    for line in lines:
        tok = line.split()
        if not tok or tok[0] not in ("C", "D"):
            new.append(line)
            continue
        fn = tok[1]
        rows = (src / fn).read_text(encoding="utf-8").splitlines()
        title = "0 " + rows[0].lstrip("* ").strip()
        q = [r.split() for r in rows[1:] if r.startswith("Q")]
        if tok[0] == "C":
            body = [" ".join(r) for r in q]
            new.append(line)
        else:
            hi = float(tok[3])
            inner = FASTCAP2_INNER.get(round(hi, 6))
            if inner is None:
                raise ValueError(f"{fn}: no inner point known for permittivity {hi:g}")
            p = np.array(inner)
            for r in q:
                c = np.array([float(x) for x in r[2:14]]).reshape(4, 3)
                ref = np.array([float(x) for x in r[14:17]])
                ctr, nrm = _quad_normal(c)
                if np.sign(np.dot(p - ctr, nrm)) != -np.sign(np.dot(ref - ctr, nrm)) or np.dot(p - ctr, nrm) == 0:
                    raise ValueError(f"{fn}: the inner point is not on the inner side of a panel at {ctr}")
            body = [" ".join(r[:14]) for r in q]
            title = (f"0 interface between relative permittivities {tok[2]} and {tok[3]}; its reference point, "
                     f"in the list file, lies inside the body of permittivity {tok[3]}")
            new.append(f"D {fn} {tok[2]} {tok[3]} 0 0 0 {p[0]:.9e} {p[1]:.9e} {p[2]:.9e} -")
        (out / fn).write_text("\n".join([title] + body) + "\n", encoding="ascii", newline="\n")
        files.append(fn)
    lst = f"{name}.lst"
    (out / lst).write_text("\n".join(new) + "\n", encoding="ascii", newline="\n")
    return dict(list=lst, files=files)


class _Fastcap2Log:
    """Receives FastCap2's console output: FastCap2 calls log(text, colour) for every piece of text its
    console window would show (port help, 'SetLogCallback Method').  Each piece keeps the time it
    arrived, in seconds from t0."""
    _public_methods_ = ["log"]

    def __init__(self) -> None:
        self.t0 = time.time()
        self.parts: list[tuple[float, str]] = []

    def log(self, text, colour) -> None:
        self.parts.append((time.time() - self.t0, str(text)))

    def text(self) -> str:
        pieces = [p for _, p in self.parts]
        return ("" if any("\n" in p for p in pieces) else "\n").join(pieces)

    def first(self, pattern: str) -> float | None:
        """Seconds from t0 to the first piece of output containing ``pattern`` (None if none did)."""
        return next((t for t, p in self.parts if pattern in p), None)


def _without_temp_folder(text: str) -> str:
    """FastCap2's output with the temporary folder of run_fastcap2 removed from the file names it
    prints, so that a kept log names the case's files only."""
    return re.sub(r"[A-Za-z]:\\(?:[^\\\s]+\\)*fc2_[A-Za-z0-9_]+\\", "", text)


def _fastcap2_progress(text: str) -> dict:
    """How far a FastCap2 run got, read from its console output.  With ITRDAT and RAWDAT off (the
    Windows build's mulGlobal.h) the program prints the share of multiplies done by multipole
    expansions once its set-up is done, then for every column of the capacitance matrix a line
    'Starting on column k (name)' followed by the number of every GMRES iteration (gmres in
    capsolve.c), and 'gmres: WARNING exiting without converging' if a column reaches the limit."""
    share = re.findall(r"Percentage of multiplies done by multipole: ([0-9.]+)%", text)
    columns = []
    for seg in text.split("Starting on column ")[1:]:
        head, _, body = seg.partition("\n")
        m = re.match(r"(\d+) \(([^)]*)\)", head)
        its = [int(x) for line in body.splitlines() if re.fullmatch(r"\s*(\d+\s*)+", line) for x in line.split()]
        columns.append(dict(column=int(m.group(1)) if m else None,
                            conductor=re.sub(r"%GROUP\d+$", "", m.group(2)) if m else None,
                            iterations=max(its) if its else 0))
    return dict(setup_done="ITERATION DATA" in text, multipole_share=float(share[-1]) if share else None,
                columns=columns, not_converged="exiting without converging" in text)


def run_fastcap2(folder: Path, lst: str, options: str, timeout: float) -> dict:
    """Run FastCap2 through its automation object FastCap2.Document (port help, 'FastCap2 Automation
    Overview' and 'Run Method') on ``folder``/``lst``.  The files are copied into a temporary folder
    whose path has no spaces, and the list file there names them by absolute path, since FastCap2's
    working directory is its own.  FastCap2 is set to below-normal priority once it runs.  Its console
    output arrives through SetLogCallback; the waiting loop pumps COM messages so that the callback is
    served.  A run still going after ``timeout`` seconds is stopped (port help, 'Stop Method').  Returns
    the conductor names, the capacitance matrix (F), the return status, the solve time and memory (all
    None for a stopped run), FastCap2's output and whether the run was stopped."""
    import shutil
    import tempfile
    import pythoncom
    import psutil
    import win32com.client
    import win32com.server.util
    tmp = Path(tempfile.mkdtemp(prefix="fc2_"))
    if " " in str(tmp):
        raise RuntimeError(f"the temporary folder {tmp} has a space in its path")
    for f in folder.iterdir():
        if f.suffix in (".txt",):
            shutil.copy2(f, tmp / f.name)
    rows = []
    for line in (folder / lst).read_text(encoding="utf-8").splitlines():
        tok = line.split()
        if tok and tok[0] in ("C", "D"):
            tok[1] = str(tmp / tok[1])
            line = " ".join(tok)
        rows.append(line)
    (tmp / lst).write_text("\n".join(rows) + "\n", encoding="ascii", newline="\n")
    pythoncom.CoInitialize()
    sink = _Fastcap2Log()
    names = C = status = solve_s = mem = None
    stopped = False
    t0 = sink.t0 = time.time()
    fc2 = win32com.client.Dispatch("FastCap2.Document")
    try:
        fc2.SetLogCallback(win32com.server.util.wrap(sink), "log")
        if not fc2.Run(f"-l{tmp / lst} {options}"):
            raise RuntimeError("FastCap2 refused to start the run")
        time.sleep(1.0)
        for proc in psutil.process_iter(["name", "create_time"]):
            if (proc.info["name"] or "").lower() == "fastcap2.exe" and proc.info["create_time"] >= t0 - 5:
                try:
                    proc.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
                except psutil.Error:
                    pass
        while fc2.IsRunning:
            pythoncom.PumpWaitingMessages()
            if time.time() - t0 > timeout:
                fc2.Stop()
                stopped = True
                break
            time.sleep(0.02)
        pythoncom.PumpWaitingMessages()

        def get(attr):
            v = getattr(fc2, attr)
            return v() if callable(v) else v
        if not stopped:
            names = [re.sub(r"%GROUP\d+$", "", str(s)) for s in get("GetCondNames")]
            C = np.array(get("GetCapacitance"), dtype=float)
            status = get("GetReturnStatus")
            solve_s = get("GetSolveTime")
            mem = get("GetSolveMemory")
    finally:
        try:
            fc2.Quit()
        except Exception:
            pass
        shutil.rmtree(tmp, ignore_errors=True)
    return dict(names=names, C=C, status=status, solve_seconds=solve_s, memory=mem,
                wall_seconds=time.time() - t0, log=sink.text(), stopped=stopped,
                input_summary_s=sink.first("INPUT SUMMARY"), iteration_data_s=sink.first("ITERATION DATA"))


def fastcap2_plan(name: str, order: int, depth: int | None = None) -> dict:
    """What FastCap2's partitioning will make of case ``name`` (its panel files in FastCap 2.0's format,
    written by fastcap2_files), computed from the panel centres alone, without FastCap2.

    The program (placeq in mulSetup.c) puts every panel centre into a grid of cubes of side
    1.01 L0 / 2^level, where L0 is the largest extent of the centres after one correction: any direction
    in which the centres span less than the largest panel (its longer diagonal, or its longest edge for a
    triangle: max_diag in initcalcp, calcp.c) is widened by half that panel on each side ("Make sure cube
    isn't smaller than a tile").  One large panel thus enlarges every cube.  Left to itself it goes one level
    deeper until every occupied cube, or more than 90 % of them (EXRTSH), holds at most (order + 1)^2
    centres (multerms in mulMulti.c); ``depth`` stands for the option -d, which fixes the level instead.
    Each dielectric panel brings two more centres, its evaluation points (add_dummy_panels in input.c),
    which are counted here at the panel's own centre.  The program allocates side^3 cube pointers on
    every level (8 bytes each: FastCap2.exe is a 64-bit program, PE machine type 0x8664).  The
    overlapped preconditioner inverts, for every occupied cube of the finest level, the matrix of the
    real panels in that cube and its 26 neighbours (olmulMatPrecond in mulMats.c, NEAR), at about n^3
    operations each.  The direct interactions (calcp) are those between the centres of a cube and the
    real panels of the cubes up to NNBRS = 2 away (mulGlobal.h; getnbrs in mulSetup.c), one stored
    number each.  Returns these numbers for every level down to the chosen one."""
    out = DATA / name / "fastcap2"
    lst = (out / f"{name}.lst").read_text(encoding="utf-8").splitlines()
    centres, weights, diags = [], [], []
    for line in lst:
        tok = line.split()
        if not tok or tok[0] not in ("C", "D"):
            continue
        for row in (out / tok[1]).read_text(encoding="utf-8").splitlines()[1:]:
            r = row.split()
            if not r or r[0] not in ("Q", "T"):
                continue
            n = 4 if r[0] == "Q" else 3
            c = np.array([float(x) for x in r[2:2 + 3 * n]]).reshape(n, 3)
            centres.append(c.mean(axis=0))
            weights.append(3 if tok[0] == "D" else 1)
            if n == 4:
                diags.append(max(np.linalg.norm(c[2] - c[0]), np.linalg.norm(c[3] - c[1])))
            else:
                diags.append(max(np.linalg.norm(c[(k + 1) % 3] - c[k]) for k in range(3)))
    P = np.array(centres)
    w = np.array(weights)
    real = np.ones_like(w)
    lo, hi = P.min(axis=0), P.max(axis=0)
    tile = float(max(diags))
    grow = (hi - lo) < tile                     # placeq: "Make sure cube isn't smaller than a tile"
    lo = np.where(grow, lo - 0.5 * tile, lo)
    hi = np.where(grow, hi + 0.5 * tile, hi)
    L0 = float((hi - lo).max())
    limit = (order + 1) ** 2
    levels, pointer_bytes = [], 8 * (1 + 8 + 64)          # levels 0, 1 and 2
    for level in range(3, 21):
        side = 2 ** level
        pointer_bytes += 8 * side ** 3
        idx = np.floor((P - lo) / (1.01 * L0 / side)).astype(np.int64)
        key = (idx[:, 0] * side + idx[:, 1]) * side + idx[:, 2]
        cubes, inv = np.unique(key, return_inverse=True)
        count = np.bincount(inv, weights=w)
        exact = float(np.mean(count <= limit))
        rec = dict(level=level, cube_side_um=1.01 * L0 / side * 1e6, occupied=int(cubes.size),
                   most_centres=int(count.max()), exact_fraction=exact, pointer_MB=pointer_bytes / 1e6)
        chosen = (level == depth) if depth is not None else (exact == 1.0 or exact > 0.9)
        if chosen:
            nreal = np.bincount(inv, weights=real)
            cidx = np.stack([cubes // side ** 2, (cubes // side) % side, cubes % side], axis=1)
            lookup = dict(zip(cubes.tolist(), nreal.tolist()))

            def around(i, j, k, reach):
                return sum(lookup.get(((i + di) * side + (j + dj)) * side + (k + dk), 0)
                           for di in range(-reach, reach + 1) for dj in range(-reach, reach + 1)
                           for dk in range(-reach, reach + 1))
            work, biggest, direct = 0.0, 0, 0.0
            for c, (i, j, k) in enumerate(cidx):
                n = around(i, j, k, 1)          # the preconditioner's block: this cube and its 26 neighbours
                work += float(n) ** 3
                biggest = max(biggest, int(n))
                direct += count[c] * around(i, j, k, 2)
            rec.update(precond_operations=work, largest_block=biggest, direct_entries=direct,
                       direct_MB=8 * direct / 1e6)
            levels.append(rec)
            break
        levels.append(rec)
    return dict(case=name, order=order, limit=limit, panels=int(len(P)), centres=int(w.sum()),
                largest_panel_mm=tile * 1e3, widened="".join(a for a, g in zip("xyz", grow) if g),
                largest_extent_mm=L0 * 1e3, levels=levels, depth=levels[-1]["level"])


def cmd_fastcap2_plan(name: str, orders: list[int], depth: int | None) -> None:
    """Print fastcap2_plan for case ``name`` at each expansion order (and the fixed depth, if given)."""
    out = DATA / name / "fastcap2"
    if not (out / f"{name}.lst").exists():
        fastcap2_files(name, out)
    for order in orders:
        p = fastcap2_plan(name, order, depth)
        print(f"{name}, order {order}, depth {'fixed at ' + str(depth) if depth is not None else 'automatic'}: "
              f"{p['panels']} panels ({p['centres']} centres with the evaluation points), largest panel "
              f"{p['largest_panel_mm']:.2f} mm across, root cube {p['largest_extent_mm']:.2f} mm "
              f"(widened in {p['widened'] or 'no direction'}), at most {p['limit']} centres per cube")
        for lv in p["levels"]:
            line = (f"  level {lv['level']:2d}: cube {lv['cube_side_um']:9.1f} um, {lv['occupied']:6d} occupied, "
                    f"at most {lv['most_centres']:5d} centres, {100 * lv['exact_fraction']:5.1f} % within the limit, "
                    f"pointers {lv['pointer_MB']:8.1f} MB")
            if "precond_operations" in lv:
                line += (f"; preconditioner {lv['precond_operations']:.2e} operations, "
                         f"largest block {lv['largest_block']} panels; direct {lv['direct_entries']:.2e} "
                         f"entries ({lv['direct_MB']:.0f} MB)")
            print(line)


def cmd_fastcap2(name: str, options: str, timeout: float) -> None:
    """Convert case ``name`` (fastcap2_files), run FastCap2 on it (run_fastcap2), keep FastCap2's console
    output in <case>/fastcap2/fastcap2_<options>.log and record the result in <case>/fastcap2/results.json.

    The default options follow FastCap's user's guide, Section 2.1 (PDF p. 17): third-order multipole
    expansions with the iterative loop's tolerance at 0.001, for about ten times the default accuracy,
    and the partitioning depth chosen by the program.  The program deepens the partitioning until more
    than 90 % of the occupied cubes hold no more panels than an expansion has terms, (order + 1)^2
    (placeq in mulSetup.c, EXRTSH in mulGlobal.h).  A depth of 0 (-d0, every interaction computed
    directly) is no practical exact mode: the overlapped preconditioner (PRECOND OL in mulGlobal.h)
    inverts the matrix of each finest cube with its neighbours by Gauss-Jordan elimination
    (olmulMatPrecond in mulMats.c, invert in direct.c), and with a single cube that is the whole N x N
    matrix, about N^3 operations along columns of a row-stored matrix.  On this laptop the uniform case of
    7939 panels had not finished in an hour that way.

    The fine 0402 cases need a fixed depth of 9.  Their largest panel (a box or board face left whole,
    about 23 mm across) is wider than the spread of the panel centres, so the program widens its root
    cube to about 41 mm (fastcap2_plan).  At depth 8 the cubes are then about 160 um wide and the
    preconditioner's blocks reach 2700 to 3000 panels, 2.5e11 to 3.5e11 operations (the uniform case
    had not finished its set-up in 20 minutes); left to itself the program would go to depth 11 in the
    uniform case (78.5 GB of cube pointers) and stop at depth 3 in the dielectric case (one block of 10 103
    panels).  Depth 9 gives cubes of about 80 um, blocks of 750 to 810 panels (2e10 to 2.6e10 operations)
    and 1.2 GB of cube pointers.  The option -z makes the program print its set-up and solve times.
    Sources: github.com/ediloren/FastCap2, src/ (branch master, the M.I.T. code) and FASTCAP/ (branch
    WinMSVS, the Windows build used here)."""
    out = DATA / name / "fastcap2"
    conv = fastcap2_files(name, out)
    meta = json.loads((DATA / name / f"{name}.json").read_text(encoding="utf-8"))
    r = run_fastcap2(out, conv["list"], options, timeout)
    r["log"] = _without_temp_folder(r["log"])
    tag = re.sub(r"[^A-Za-z0-9.]+", "_", options).strip("_") or "default"
    log_path = out / f"fastcap2_{tag}.log"
    log_path.write_text(r["log"], encoding="utf-8", newline="\n")
    levels = re.findall(r"Number of partitioning levels:\s*(\d+)", r["log"])
    rec = dict(options=options, log=log_path.name, partitioning_levels=int(levels[-1]) if levels else None,
               wall_seconds=r["wall_seconds"], stopped=r["stopped"], **_fastcap2_progress(r["log"]))
    if r["input_summary_s"] is not None and r["iteration_data_s"] is not None:
        rec["setup_wall_seconds"] = r["iteration_data_s"] - r["input_summary_s"]   # matrices and preconditioner
    res_path = out / "results.json"
    results = json.loads(res_path.read_text(encoding="utf-8")) if res_path.exists() else {}
    if r["stopped"]:
        results[options] = rec
        res_path.write_text(json.dumps(results, indent=1, default=float), encoding="utf-8", newline="\n")
        tail = "\n".join(r["log"].splitlines()[-15:])
        raise TimeoutError(f"{name}: FastCap2 {options} stopped after {timeout:g} s; its output so far is in "
                           f"{log_path}, ending with:\n{tail}")
    rec.update(names=r["names"], C_fF=(r["C"] * fc.FF_PER_F).tolist(), status=r["status"],
               solve_seconds=r["solve_seconds"], memory=r["memory"])
    results[options] = rec                      # the matrix is kept even if the reduction below fails
    res_path.write_text(json.dumps(results, indent=1, default=float), encoding="utf-8", newline="\n")
    tp = fc.two_port(meta, r["names"], r["C"])
    rec.update(**tp)
    results[options] = rec
    res_path.write_text(json.dumps(results, indent=1, default=float), encoding="utf-8", newline="\n")
    print(f"{name} FastCap2 {options}: C_F = {tp['C_F']:.3f} fF, C_A0 = {tp['C_A0']:.3f} fF, C_B0 = {tp['C_B0']:.3f} fF, "
          f"status {r['status']}, partitioning levels {rec['partitioning_levels']}, solve {r['solve_seconds']} s, "
          f"wall {r['wall_seconds']:.0f} s")
    print("  matrix (fF):", np.array2string(r["C"] * fc.FF_PER_F, precision=3), "names", r["names"])


def history(text: str, meta: dict) -> list[dict]:
    """C_F, C_A0 and the panel count after every refinement step of an automatic FasterCap run: each
    step prints its matrix, then its statistics (FasterCap help, Output chapter 1)."""
    out = []
    blocks = re.split(r"(?=Capacitance matrix is:)", text)
    for b in blocks[1:]:
        try:
            names, C = fc.read_matrix(b)
        except ValueError:
            continue
        panels = re.findall(r"Number of panels after refinement: (\d+)", b)
        change = re.findall(r"Weighted Frobenius norm of the difference between capacitance \(auto option\): ([0-9.eE+-]+)", b)
        rec = dict(panels=int(panels[0]) if panels else None, change=float(change[0]) if change else None)
        nets = {c["net"] for c in meta.get("conductors", {}).values()}
        if meta.get("pair") and set(meta["pair"]) <= nets:
            tp = fc.two_port(meta, names, C)
            rec.update(C_F=tp["C_F"], C_A0=tp["C_A0"])
        else:
            rec.update(C=float(C[0, 0]) * fc.FF_PER_F)
        out.append(rec)
    return out


def cmd_history(name: str, log: str) -> None:
    meta = json.loads((DATA / name / f"{name}.json").read_text(encoding="utf-8"))
    for k, r in enumerate(history((DATA / name / log).read_text(encoding="utf-8", errors="replace"), meta)):
        print(f"  step {k + 1}: " + ", ".join(f"{a} {v:.4g}" if isinstance(v, float) else f"{a} {v}" for a, v in r.items()))


def _summary(text: str) -> dict:
    """Panel count, time and memory of the last iteration in FasterCap's output."""
    panels = re.findall(r"Number of panels after refinement: (\d+)", text)
    total = re.findall(r"Total time: ([0-9.eE+-]+)s", text)
    mem = re.findall(r"Total allocated memory: (\d+) kilobytes", text)
    return dict(panels=int(panels[-1]) if panels else None, seconds=float(total[-1]) if total else None,
                memory_MB=int(mem[-1]) / 1024 if mem else None,
                iterations=len(re.findall(r"Iteration number #", text)))


def solve_stats(text: str) -> dict:
    """The GMRES iterations of every solve (FasterCap prints one line 'GMRES Iteration: 0 1 2 ...' per solve,
    in the order of its matrix's rows), and the links, links per panel and largest relative refinement value
    of the last step."""
    iters = [len(line.split()) - 2 for line in text.splitlines() if line.startswith("GMRES Iteration")]
    links = re.findall(r"Number of links: (\d+)", text)
    panels = re.findall(r"Number of panels after refinement: (\d+)", text)
    maxref = re.findall(r"Max Mesh relative refinement value: ([0-9.eE+-]+)", text)
    # FasterCap keeps its links on disk when five times their memory (its option -f) exceeds the free memory
    out = dict(gmres=iters, out_of_core="Going out-of-core" in text)
    if links and panels:
        out.update(links=int(links[-1]), links_per_panel=int(links[-1]) / int(panels[-1]))
    if maxref:
        out["max_refinement_value"] = float(maxref[-1])
    return out


def column_checks(meta: dict, names: list[str], C: np.ndarray) -> dict:
    """What each solve gives by itself, for a model in the grounded box (net "gnd").  Column k of FasterCap's
    matrix is one solve, conductor k at 1 V and every other at 0 V (pcbcap.fastercap, "What FasterCap
    solves").  Inside the closed box every field line from A or B ends on a conductor, so the free charges
    of the A solve add to zero (Gauss's law on a surface just inside the box), and so do those of the B
    solve; closure_A and closure_B are those sums over the driven conductor's own charge.  The A and B
    solves alone then give C_F (-C[B,A] and -C[A,B]) and C_A0 (-C[gnd,A], the charge the A solve leaves on
    the box); the box's own solve, the slowest to converge, enters neither.  The box's solve gives C_A0 a
    second time, as the charge it puts on A, -C[A,gnd]: the two must be equal (reciprocity, which makes
    every capacitance matrix of conductors and dielectrics symmetric), so their difference measures the error
    of the solution, provided the box's solve converged (its GMRES iterations below 1000)."""
    lookup = {k.lower(): v["net"] for k, v in meta["conductors"].items()}
    nets = [lookup[n.lower()] for n in names]
    a, b = meta["pair"]
    ia, ib, ig = nets.index(a), nets.index(b), nets.index("gnd")
    col_a, col_b = C[:, ia] * fc.FF_PER_F, C[:, ib] * fc.FF_PER_F
    return dict(C_F_from_A=float(-col_a[ib]), C_F_from_B=float(-col_b[ia]),
                C_A0_from_box=float(-col_a[ig]), C_B0_from_box=float(-col_b[ig]),
                C_A0_from_box_solve=float(-C[ia, ig] * fc.FF_PER_F), C_B0_from_box_solve=float(-C[ib, ig] * fc.FF_PER_F),
                closure_A=float(col_a.sum() / col_a[ia]), closure_B=float(col_b.sum() / col_b[ib]))


def cmd_run(name: str, tols, galerkin: bool, timeout: float, extra=(), meshes=()) -> None:
    folder = DATA / name
    meta = json.loads((folder / f"{name}.json").read_text(encoding="utf-8"))
    res_path = folder / "results.json"
    results = json.loads(res_path.read_text(encoding="utf-8")) if res_path.exists() else {}
    # Either the automatic mode at each tolerance (-a), or a fixed refinement at each mesh value (-m, smaller
    # is finer).  The automatic mode stops on a small change between two refinements and then keeps refining
    # into ill-conditioned systems on these layouts (README.md), so the fixed series is the one relied on.
    series = [[f"-m{m:g}"] for m in meshes] if meshes else [[f"-a{tol:g}"] for tol in tols]
    for first in series:
        opts = first + (["-g"] if galerkin else []) + list(extra)
        tag = "_".join(o.lstrip("-") for o in opts)
        t0 = time.perf_counter()
        try:
            text = fc.run_fastercap(EXE, folder / f"{name}.lst", opts, log=folder / f"fastercap_{tag}.log",
                                    timeout=timeout)
        except subprocess.TimeoutExpired:
            print(f"{name} {' '.join(opts)}: no result within {timeout:g} s; larger tolerances only")
            results[tag] = dict(options=opts, timeout=timeout)
            res_path.write_text(json.dumps(results, indent=1), encoding="utf-8", newline="\n")
            break
        names, C = fc.read_matrix(text)
        rec = dict(options=opts, wall_seconds=time.perf_counter() - t0, **_summary(text))
        if name.startswith("cube"):
            c = float(C[0, 0]) * fc.FF_PER_F
            exact = CASES[name]["exact"]
            rec.update(C=c, exact=exact, rel_error=c / exact - 1.0)
            print(f"{name} {' '.join(opts):14s} C = {c:9.4f} fF ({c / exact - 1:+.3%}), {rec['panels']} panels, "
                  f"{rec['wall_seconds']:.1f} s")
        else:
            tp = fc.two_port(meta, names, C)
            rec.update(tp)
            rec.update(solve_stats(text))
            if any(c["net"] == "gnd" for c in meta["conductors"].values()):
                rec.update(column_checks(meta, names, C))
            print(f"{name} {' '.join(opts):14s} C_F = {tp['C_F']:8.3f} fF, C_A0 = {tp['C_A0']:8.3f} fF, "
                  f"asymmetry {tp['asymmetry']:.1e}, {rec['panels']} panels, {rec['wall_seconds']:.1f} s")
        results[tag] = rec
        res_path.write_text(json.dumps(results, indent=1), encoding="utf-8", newline="\n")


def cmd_orientation(name: str, opts) -> None:
    """Check how FasterCap reads the per-panel reference points: rewrite the case's dielectric statements
    with one reference point inside each dielectric body, flagged '-' (the inner side), and without the
    per-panel points, run both inputs and compare.  Equal results show that FasterCap uses the per-panel
    points as fastercap.write_files writes them.  ``inner`` maps each dielectric file to a point (m)
    inside the one convex body that holds all its panels; it is given here for the film-free 0402 on the
    16-mm board (the board's centre and the alumina body's centre)."""
    inner = {f"{name}_d1.txt": "0 0 -8.0e-04", f"{name}_d2.txt": "0 0 2.4e-04"}
    folder = DATA / name
    lines = (folder / f"{name}.lst").read_text(encoding="utf-8").splitlines()
    out = []
    for line in lines:
        if line.startswith("D "):
            parts = line.split()
            out.append(f"D {parts[1]}.inner {parts[2]} {parts[3]} 0 0 0 {inner[parts[1]]} -")
            rows = (folder / parts[1]).read_text(encoding="utf-8").splitlines()
            (folder / f"{parts[1]}.inner").write_text(
                "\n".join([rows[0]] + [" ".join(r.split()[:14]) for r in rows[1:] if r.startswith("Q")]) + "\n",
                encoding="ascii", newline="\n")
        else:
            out.append(line)
    (folder / "orientation_check.lst").write_text("\n".join(out) + "\n", encoding="ascii", newline="\n")
    meta = json.loads((folder / f"{name}.json").read_text(encoding="utf-8"))
    res = {}
    for label, lst in (("per-panel points", f"{name}.lst"), ("one inner point per body", "orientation_check.lst")):
        text = fc.run_fastercap(EXE, folder / lst, opts, log=folder / f"orientation_{lst}.log")
        res[label] = fc.two_port(meta, *fc.read_matrix(text))
        print(f"  {label}: C_F = {res[label]['C_F']:.4f} fF, C_A0 = {res[label]['C_A0']:.4f} fF")
    (folder / "orientation_check.json").write_text(json.dumps(dict(options=list(opts), results=res), indent=1),
                                                   encoding="utf-8", newline="\n")


def cmd_pcbcap(case: str = "r0402_nofilm") -> None:
    """The film-free 0402 in pcbcap, exactly as full_study of g_resistor_3d.py runs the published one:
    three meshes in the 8-mm box, and three boxes at the coarsest mesh.  Case "r0402_nofilm_air" is the
    same model with every permittivity 1 (FasterCap case r0402_nofilm_air_box8): the three meshes in
    the 8-mm box only, since FasterCap solves it in that box."""
    study.lower_priority(2)
    lv = g3.LEVELS["0402"]
    if case == "r0402_nofilm_air":
        print(f"  uniform medium, mesh convergence, refine levels {lv}:")
        conv = study.converge(r0402(8.0, film=False, eps_pcb=1.0, eps_al=1.0), factors=lv, params=g3.BASE, order=2)
        out = dict(case=case, convergence=conv.to_dict(), C_F_box8=conv.value(), discretisation_error=conv.C_F["error"])
        DATA.mkdir(parents=True, exist_ok=True)
        (DATA / "pcbcap_r0402_nofilm_air.json").write_text(json.dumps(out, indent=1, default=float),
                                                           encoding="utf-8", newline="\n")
        print(f"  C_F in the 8-mm box, uniform medium: {conv.value():.3f} +- {conv.C_F['error']:.3f} fF")
        return
    print(f"  mesh convergence, refine levels {lv}:")
    conv = study.converge(r0402(8.0, film=False), factors=lv, params=g3.BASE, order=2)
    print(f"  enclosure sizes {g3.ENCLOSURE} mm at refine {lv[0]}:")
    enc = study.enclosure_correction(lambda m: r0402(m, film=False), margins=g3.ENCLOSURE,
                                     params=replace(g3.BASE, refine=lv[0]), order=2)
    out = dict(case="r0402_nofilm", convergence=conv.to_dict(), enclosure=enc,
               C_F_box8=conv.value(), discretisation_error=conv.C_F["error"],
               C_F_no_ground=conv.value() + enc["dC_F"])
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "pcbcap_r0402_nofilm.json").write_text(json.dumps(out, indent=1, default=float), encoding="utf-8",
                                                  newline="\n")
    print(f"  C_F in the 8-mm box {conv.value():.3f} +- {conv.C_F['error']:.3f} fF; "
          f"with no ground nearby {out['C_F_no_ground']:.3f} fF")


def _fmt_run(tag: str, r: dict) -> str:
    opts = " ".join(r.get("options", [tag]))
    if "C_F" in r:
        return (f"| {opts} | {r.get('panels', '')} | {r['C_F']:.3f} | {r['C_A0']:.3f} | {r['C_AB']:.3f} / {r['C_BA']:.3f} | "
                f"{r['asymmetry']:.1e} | {r.get('wall_seconds', 0):.1f} |")
    if "C" in r:
        return f"| {opts} | {r.get('panels', '')} | {r['C']:.4f} | {r['exact']:.4f} | {r['rel_error']:+.3%} | {r.get('wall_seconds', 0):.1f} |"
    return f"| {opts} | no result within {r.get('timeout', 0):g} s | | | | | |"


def _fastcap2_stop(name: str, r: dict) -> str:
    """How far a stopped FastCap2 run got, in one phrase, from its log when the log was kept."""
    secs = f"{r.get('wall_seconds', 0):.0f} s"
    log = DATA / name / "fastcap2" / r["log"] if r.get("log") else None
    if log is None or not log.exists():
        return f"no result: stopped after {secs}, output not kept"
    p = _fastcap2_progress(log.read_text(encoding="utf-8"))
    if not p["setup_done"]:
        return f"no result: set-up unfinished when stopped after {secs}"
    if not p["columns"]:
        return f"no result: stopped after {secs}, before the first column"
    c = p["columns"][-1]
    return (f"no result: GMRES on column {c['column']} ({c['conductor']}) at iteration {c['iterations']} "
            f"when stopped after {secs}")


FIXED_MESH_CASES = ("r0402_nofilm_fine_box8", "r0402_nofilm_fine_max1_box8", "r0402_nofilm_fine_max0p5_box8",
                    "r0402_nofilm_fine_max0p25_box8", "r0402_nofilm_air_fine_max0p5_box8")
PCBCAP_BOX8 = {"r0402_nofilm": (39.77, 54.08), "r0402_nofilm_air": (9.870, 25.350)}   # C_F, C_A0 (fF)


def cmd_backfill(name: str, timeout_tag: str | None = None, timeout: float | None = None) -> None:
    """Bring the records of case ``name`` up to date with its logs: every run of a model in the grounded box
    gets the checks of each solve (solve_stats, column_checks), which cmd_run has recorded only since they were
    added.  With ``timeout_tag`` and ``timeout``, also record that the run of that tag ended at the time limit
    without a result, which cmd_run did not save before it wrote such records (the log of that run is empty,
    since FasterCap buffers what it prints and the run was killed)."""
    folder = DATA / name
    meta = json.loads((folder / f"{name}.json").read_text(encoding="utf-8"))
    res_path = folder / "results.json"
    results = json.loads(res_path.read_text(encoding="utf-8")) if res_path.exists() else {}
    for tag, rec in results.items():
        log = folder / f"fastercap_{tag}.log"
        if "C_F" not in rec or not log.exists():
            continue
        text = log.read_text(encoding="utf-8", errors="replace")
        names, C = fc.read_matrix(text)
        rec.update(solve_stats(text))
        if any(c["net"] == "gnd" for c in meta["conductors"].values()):
            rec.update(column_checks(meta, names, C))
        print(f"{name} {tag}: checks of each solve added")
    if timeout_tag is not None:
        opts = ["-" + o for o in timeout_tag.split("_")]
        results[timeout_tag] = dict(options=opts, timeout=float(timeout))
        print(f"{name} {timeout_tag}: recorded as stopped at the time limit of {timeout:g} s")
    res_path.write_text(json.dumps(results, indent=1), encoding="utf-8", newline="\n")


def fixed_mesh_table() -> list[str]:
    """The runs that solve the exported panels without refinement (-m100), one row per log, with the checks
    of each solve (column_checks) next to pcbcap's values for the same model."""
    rows = []
    for name in FIXED_MESH_CASES:
        folder = DATA / name
        meta_path = folder / f"{name}.json"
        if not meta_path.exists():
            continue
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        far = meta["options"].get("max_panel")
        ref = PCBCAP_BOX8["r0402_nofilm_air" if "_air_" in name else "r0402_nofilm"]
        def d_of(path):
            m = re.search(r"_d([0-9.eE+-]+)\.log$", path.name)
            return float(m.group(1)) if m else 1.0

        for log in sorted(folder.glob("fastercap_m100*.log"), key=lambda p: -d_of(p)):
            d = f"{d_of(log):g}" + (" (default)" if d_of(log) == 1.0 else "")
            text = log.read_text(encoding="utf-8", errors="replace")
            try:
                names, C = fc.read_matrix(text)
            except ValueError:
                # FasterCap buffers what it prints, so a run that ends without a result leaves at most the
                # footer of run_fastercap: a time limit, or an exit code (4294967295 when stopped by hand)
                limit = re.findall(r"stopped at the time limit of ([0-9.]+) s", text)
                end = re.findall(r"exit code (-?\d+), ([0-9.]+) s", text)
                tag = log.stem.removeprefix("fastercap_")
                res_path = folder / "results.json"
                rec = json.loads(res_path.read_text(encoding="utf-8")).get(tag, {}) if res_path.exists() else {}
                if limit or "timeout" in rec:
                    what = f"no result within the time limit of {float(limit[-1]) if limit else rec['timeout']:.0f} s"
                elif end and end[-1][0] == "4294967295":
                    what = f"no result: stopped by hand after {float(end[-1][1]):.0f} s"
                elif end:
                    what = f"no result: exit code {end[-1][0]} after {float(end[-1][1]):.0f} s"
                else:
                    what = "no result"
                rows.append(f"| {name} | {'whole faces' if far is None else f'{far:g} mm'} | | {d} | | | | "
                            f"{what} | | | |")
                continue
            st, cc = solve_stats(text), column_checks(meta, names, C)
            panels = re.findall(r"Number of panels after refinement: (\d+)", text)
            secs = re.findall(r"Total time: ([0-9.eE+-]+)s", text)
            rows.append(f"| {name} | {'whole faces' if far is None else f'{far:g} mm'} | {panels[-1]} | {d} | "
                        f"{st['links_per_panel']:.0f} | {', '.join(map(str, st['gmres']))} | "
                        f"{cc['closure_A']:+.2%} / {cc['closure_B']:+.2%} | "
                        f"{cc['C_F_from_A']:.2f} / {cc['C_F_from_B']:.2f} | "
                        f"{cc['C_A0_from_box']:.2f} / {cc['C_A0_from_box_solve']:.2f} | "
                        f"{ref[0]:g} / {ref[1]:g} | {float(secs[-1]):.0f}"
                        f"{', links on disk' if st['out_of_core'] else ''} |")
    head = ["| Case | Panels outside the part's window | Solver panels | -d | Links per panel | "
            "GMRES iterations (box, B, A) | Charge closure, A / B solve | $C_F$ from the A / B solve | "
            "$C_{A0}$ from the A / box solve | pcbcap $C_F$ / $C_{A0}$ | Time (s) |",
            "|---|---|---|---|---|---|---|---|---|---|---|"]
    return head + rows if rows else []


def cmd_report() -> None:
    """Write data/parasitic_cf/fastercap/README.md from the records: the geometry checks, every
    FasterCap run (a convergence series per case), FastCap2's runs and pcbcap's studies of the
    film-free 0402."""
    out = ["# FasterCap checks of the field solutions of Section G.14", "",
           "These are the results of `scripts_archive/parasitic_cf/numerical/fastercap_validation.py`, whose docstring "
           "describes every case; `pcbcap/pcbcap/fastercap.py` explains how a layout becomes FasterCap's input and how "
           "its matrix is read. They are kept here, not in the note. Capacitances in fF.", "",
           "## What the runs show", "",
           "* The export is right. Every kind of panel has the area that gmsh's fragments give to within 1e-13 "
           "(table below); every panel view was looked at; a cube of 1 mm comes out at the exact 73.510 fF "
           "(0.6606782 x 4 pi eps0 a, Hwang and Mascagni, J. Appl. Phys. 95, 3798 (2004)) to +0.08 % with "
           "collocation and -0.08 % with Galerkin, and exactly 4.2 times that in a medium of 4.2; per-panel "
           "reference points and one inner point per dielectric body give the same 0402 result to 1e-5.",
           "* FasterCap's automatic mode (-a) stops on a small change between two refinements, not on a small "
           "error: the cube on a dielectric block stops at -12 % of the half-space bound at -a0.003, while fixed "
           "refinements (-m 0.1 to 0.02, Galerkin) rise smoothly to 2.46 times the cube in air.",
           "* FasterCap does not solve the 0402 model reliably. In the grounded 8-mm box, and in free space once "
           "the panels pass about 10 000, its GMRES solves stop converging (the 1000-iteration limit) and "
           "C_A0 turns negative; the fixed Galerkin refinement fails the "
           "same way at 64 000 to 113 000 panels. Before that point the free-space C_F lies at 31 to 35 fF "
           "and has not settled, so it neither confirms nor contradicts pcbcap's 42.09 fF (the same film-free "
           "0402 with no ground nearby) or 39.77 +- 0.07 fF (in the 8-mm box). The cube and block cases run "
           "cleanly up to the largest refinement kept, 148 375 panels (the block, Galerkin -m0.02, 28 GMRES "
           "iterations). A Galerkin run of the free-space 0402 at -m0.1 was stopped by hand before FasterCap "
           "printed anything, so its log is empty.",
           "* The thin metal is not the cause (the side note's Appendix D). In a uniform medium "
           "(r0402_nofilm_air_box8, every permittivity 1) FasterCap converges smoothly, with 10-25 GMRES "
           "iterations, to C_F 9.63 fF and C_A0 25.30 fF at 52 691 panels, against pcbcap's 9.870 +- 0.017 "
           "and 25.350 +- 0.015 fF (-2.5 % and -0.2 %); the 2.5 % is FasterCap's collocation error, since its "
           "Galerkin scheme on fixed meshes (-m 0.07, 0.05, 0.035 -g: 14 122 to 52 691 panels, 6-14 GMRES "
           "iterations) gives C_F 9.85, 9.87, 9.81 fF and C_A0 25.37, 25.51, 25.45 fF, within 0.6 % and 0.7 % "
           "of pcbcap. The next mesh (-m0.025 -g) stopped with exit code 1 after 212 s without printing "
           "anything. With the dielectrics and every face of the metal cut "
           "into panels no wider than the metal is thick (r0402_nofilm_finemetal_box8), its first step "
           "(15 008 panels, every solve converged) gives C_F 30.0 fF and C_A0 87.2 fF, and the refinement breaks "
           "down as before; the run did not finish within 1800 s. A third case (r0402_nofilm_fine_box8) also cuts "
           "every face inside a window of 1.7 x 0.7 x 0.47 mm around the part, dielectric ones included, into "
           "panels of 30 um or less (fastercap.ExportOptions.fine_window, fine_panel; 10 111 input panels). "
           "Its automatic collocation run gives 23-32 and 81-100 fF over seven steps, then fails (GMRES at 1000, "
           "exit code 1 after 390 s), and a Galerkin run at -m0.07 exited with code 1 after 21 s without "
           "printing anything. Solved on its panels as exported, and with the faces away from the part cut "
           "finer as well, it gives the results of the section \"Solving the exported panels as they are\" below.",
           "* The input was checked again for errors in its dielectric part (the side note's Appendix D) and none "
           "was found: the panel files carry permittivities 1, 4.2 and 9.7 on the right faces (pad undersides 4.2, "
           "terminations' inner faces 9.7, the box walls beside the board 4.2), the '+' chain returns three "
           "conductors (g1_A, g1_B, g1_gnd), coordinates are written in metres to ten significant digits, faces are "
           "classified by probing at most 1 um off them, and reference points lie 1 um off each dielectric panel on "
           "the lower-permittivity side. FasterCap's dielectric answers break reciprocity: at 12 233 panels in the "
           "box the box's row gives -88 and -92 fF for its coupling to B and A, its column -43 and -40 fF, and in "
           "free space C_AB and C_BA differ by 7 %, while the uniform-medium matrices are symmetric to about 1 %. "
           "FasterCap's source (github.com/ediloren/FasterCap, Solver/Autorefine.cpp, CAutoRefine::PotEstimateOpt) "
           "computes a dielectric panel's row from the source panel's exact potential at points one twentieth of "
           "the centroid distance either side when the centroids lie closer than the longer side of the two "
           "panels, and from field quadratures (orders 5, 3, 2) or a point-charge formula farther out.",
           "* FasterCap's \"not diagonally dominant\" warnings do not mark bad solutions in the grounded box: "
           "every row of a conductor inside the box sums to zero, so rounding alone sets them off, and the "
           "converged uniform-medium runs show them too. A negative C_A0 does mark a bad solution.",
           "* FastCap 2.0 (the M.I.T. program, in FastFieldSolvers' Windows build 3.6) gives no result on these "
           "panel sets and is not used further; the side note's Appendix D explains why it should be avoided for "
           "models like these. In r0402_nofilm_air_fine_box8 (7939 panels) the grounded box is six panels, one per "
           "face, 16 x 16 and 16 x 17.6 mm, whose centroids lie 7.9 to 9.7 mm from the centroid of the metal; in "
           "r0402_nofilm_fine_box8 the box has 14 such panels and the board's bottom face is one 16-mm panel 1.74 mm "
           "below the metal's centroid. FastCap2 widens its root cube by the largest panel's diagonal in every "
           "direction in which the panel centres spread less than that panel (placeq in mulSetup.c), here from "
           "17.6 to 41.4 mm, so at depth 8 its overlapped preconditioner inverts blocks of up to 2690 panels "
           "(2.5e11 operations) and the uniform case's set-up did not finish in 20 minutes. At depth 9 the set-up "
           "finished (84 % of the multiplies by multipole expansions), but GMRES on the box's column reached "
           "iteration 7448 of the 7939 the program allows (MAXITER in mulGlobal.h, one per panel) without reaching "
           "the tolerance 0.001 before the 20-minute limit, in the uniform medium whose answer pcbcap gives to "
           "0.2 %. FastCap2's expansions place each panel's charge at its centroid (mulQ2Multi in mulMulti.c, "
           "mulQ2Local in mulLocal.c): seen from the metal's centroid, the six box faces then act on the part "
           "19 to 28 % too strongly and the board's bottom face 3.2 times too strongly "
           "(fastcap2_large_panels.py). The program would need the far faces cut into panels small compared with "
           "their distance from the part. The dielectric case was not run at depth 8 or 9. Left to itself the "
           "program would choose depth 11 for the uniform case (78.5 GB of cube pointers) and depth 3 for the "
           "dielectric case (one preconditioner block of 10 103 panels); the runs with -d0 (no partitioning) "
           "stopped after one hour inverting the full matrix.",
           "* The strip cases (the film as 10 to 40 strips) were exported and checked but not run, since the "
           "film-free model already fails.",
           "* Solved on its panels as exported (next section), FasterCap reproduces the uniform medium within "
           "0.3 % and with a symmetric matrix, but with the dielectrics its matrix breaks reciprocity in the "
           "coupling to the box by about 50 % (C_A0 69 to 70 fF from the A solve, 45 to 47 fF from the box's "
           "solve, against pcbcap's 54.08 fF), however finely the faces away from the part are cut. The coarse "
           "faces away from the part are not why it fails.", "",
           "## Solving the exported panels as they are", "",
           "FasterCap's option -m sets how far it refines the panels, and -d sets the tolerance of its interaction "
           "links relative to -m: the solver takes the link tolerance as d times m (m_dEps = m_dEpsRatio * "
           "m_dMeshEps in Solver/SolveCapacitance.cpp, github.com/ediloren/FasterCap). CAutoRefine::RefineMutual "
           "(Solver/Autorefine.cpp) splits the larger of two clusters of panels until RefineCriteria, an estimate "
           "of their coupling normalised by the area of the largest conductor group, falls below that tolerance, "
           "and then joins the two clusters by a single link that treats each cluster's charge as one. A run "
           "with -m100 keeps the input panels, since none needs refining at that value, but with the default -d1 "
           "it also builds its links to the tolerance 100: 3.4 links per panel on r0402_nofilm_fine_box8, "
           "against 418 to 534 in the converged uniform-medium runs at -m0.07 to -m0.035. The results of that "
           "run (C_F 37.18 fF, C_A0 90.58 fF, the box's row and column a factor of two apart) are those of the "
           "compressed links, not of the panels. The runs below keep -m100 and tighten the links with -d. In the "
           "table, C_F comes from the A and the B solve separately, and C_A0 from the A solve (the charge it "
           "leaves on the box) and from the box's solve (the charge it puts on A); the two C_A0 must be equal "
           "(reciprocity), provided the box's solve converged (below 1000 iterations). The charge closure is the "
           "sum of each solve's charges over the driven conductor's own: inside the closed box it is zero.", "",
           "* The uniform medium on the panels of the 0.5-mm case (r0402_nofilm_air_fine_max0p5_box8: the metal in "
           "panels of 30 um or less, the box in panels of 0.5 mm) checks the method. With -d0.0001 it gives C_F "
           "9.843 fF and C_A0 25.344 fF, against pcbcap's 9.870 +- 0.017 and 25.350 +- 0.015 fF (-0.27 % and "
           "-0.02 %), and its two C_A0 agree within 0.4 %. With -d0.001 the same panels give 8.96 and 24.53 fF "
           "(-9.2 % and -3.2 %). FasterCap therefore solves panels as exported once the links are this tight.",
           "* With the dielectrics, the faces away from the part (the board's top beyond the window, its bottom "
           "face 1.6 mm below the pads, and the box) were cut into panels no longer than 1, 0.5 and 0.25 mm. "
           "FasterCap's own measure of its coarsest panel, the largest relative refinement value, falls from 94.6 "
           "with the faces whole to 0.85, 0.53 and 0.22. At -d0.001 every solve on the refined panels converged "
           "and closes within 0.3 % (with the faces whole the box's solve stopped at 1000 iterations); C_F stays "
           "at 36.9 to 37.6 fF and the A solve's C_A0 at 69.0 fF with the faces whole and 69.5, 69.7 "
           "and 70.2 fF with them cut, so refining the far faces moves C_A0 by about 1 fF, away from pcbcap's "
           "54.08 fF. The box's solve, converged within 74 to 485 iterations, gives C_A0 45.4, 47.4 and 45.6 fF: "
           "these matrices break reciprocity by about 50 %, on panels whose uniform medium is reciprocal within "
           "0.4 %.",
           "* Tighter links were tried as far as the workstation allowed. With the faces whole, -d0.001 and "
           "-d0.0001 give C_F 37.25 and 40.42 fF and the A solve's C_A0 69.0 and 71.6 fF; tightening the links "
           "raises both, as it does in the uniform medium, and moves C_A0 further from pcbcap's value (the box's "
           "solve stopped at 1000 iterations in both, so reciprocity is untested there). On the refined panels "
           "-d0.0001 needs more memory than was free: FasterCap keeps its links on disk when five times their "
           "memory exceeds the free memory (its option -f, default 5), as the uniform control did with 1761 MB of "
           "links against 1416 MB free. The 0.5-mm case with the dielectrics held 2.3 GB of links on disk and read "
           "them back at about 68 MB/s, about 34 s per GMRES iteration, so it was stopped after 26 minutes; the "
           "1-mm case gave no result within its limit of 1800 s, and -d0.00001 with the faces whole was stopped "
           "after 33 minutes. Kept in memory (-f0), the 0.5-mm case would need about 3 GB.", "",
           *fixed_mesh_table(), "",
           "## Geometry checks", "",
           "Every kind of panel (a conductor net with the permittivity it touches, or a pair of permittivities) has the same "
           "area in the exported panels as in gmsh's fragments of the same layout; the views are in `views/`.", "",
           "| Case | Panels | Cells | Kinds | Worst relative area difference |", "|---|---|---|---|---|"]
    for name in CASES:
        g = DATA / name / "geometry_check.json"
        if g.exists():
            rec = json.loads(g.read_text(encoding="utf-8"))
            out.append(f"| {name} | {rec['panels']} | {rec['cells']} | {len(rec['rows'])} | "
                       f"{rec['worst_relative_area_difference']:.1e} |")
    out.append("")
    for name in CASES:
        res = DATA / name / "results.json"
        if not res.exists():
            continue
        runs = json.loads(res.read_text(encoding="utf-8"))
        out += [f"## {name}", ""]
        if name.startswith("cube_on_block"):
            out += ["The reference is the half-space limit, 2.6 times the cube in air: an upper bound for the finite "
                    "block, not its exact value.", "",
                    "| FasterCap options | Panels | C | Half-space limit | Below the limit | Time (s) |",
                    "|---|---|---|---|---|---|"]
        elif name.startswith("cube"):
            out += ["| FasterCap options | Panels | C | Exact | Error | Time (s) |", "|---|---|---|---|---|---|"]
        else:
            out += ["| FasterCap options | Panels | $C_F$ | $C_{A0}$ | $-C_{AB}$ / $-C_{BA}$ | Asymmetry | Time (s) |",
                    "|---|---|---|---|---|---|---|"]
        out += [_fmt_run(tag, r) for tag, r in runs.items()] + [""]
    # FastCap 2.0 on the same panels (cmd_fastcap2): one table over every case run in it.
    f2 = [(name, json.loads((DATA / name / "fastcap2" / "results.json").read_text(encoding="utf-8")))
          for name in CASES if (DATA / name / "fastcap2" / "results.json").exists()]
    if f2:
        out += ["## FastCap 2.0 on the same panels", "",
                "Each case's panels in FastCap 2.0's format (`<case>/fastcap2/`, with one reference point inside each "
                "dielectric body), run by the FastFieldSolvers build of FastCap2 through its automation object "
                "(`cmd_fastcap2`); `fastcap2_<options>.log` is its console output. -o is the order of the multipole "
                "expansions, -t the tolerance of the iterative solution and -d the depth of the partitioning into "
                "cubes (without -d the program chooses it).", "",
                "| Case | FastCap2 options | Partitioning levels | $C_F$ | $C_{A0}$ | $-C_{AB}$ / $-C_{BA}$ | Asymmetry | "
                "Solve time (s) |", "|---|---|---|---|---|---|---|---|"]
        for name, runs in f2:
            for tag, r in runs.items():
                if "C_F" in r:
                    out.append(f"| {name} | {tag} | {r.get('partitioning_levels', '')} | {r['C_F']:.3f} | "
                               f"{r['C_A0']:.3f} | {r['C_AB']:.3f} / {r['C_BA']:.3f} | {r['asymmetry']:.1e} | "
                               f"{r.get('solve_seconds', '')} |")
                else:
                    out.append(f"| {name} | {tag} | {r.get('partitioning_levels', '')} | {_fastcap2_stop(name, r)} "
                               f"| | | | |")
        out.append("")
    # Every log, step by step: the automatic mode prints the matrix after each refinement step, so these
    # tables are the convergence record, including the runs that broke down.
    out += ["## Refinement steps of every run", "",
            "Each automatic run (-a) prints its matrix after every refinement step; a fixed run (-m) has one step. "
            "GMRES failures are FasterCap's \"not converging after 1000 iterations\"; matrix warnings are its "
            "\"not diagonally dominant\" and \"non-negative off-diagonal\" messages. In free space a correct "
            "Maxwell matrix cannot trigger them; in the grounded box every row of an enclosed conductor sums to "
            "zero, so rounding alone can trigger the first.", ""]
    for name in CASES:
        folder = DATA / name
        if not folder.exists():
            continue
        meta_path = folder / f"{name}.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
        for log in sorted(folder.glob("*.log")):
            text = log.read_text(encoding="utf-8", errors="replace")
            steps = history(text, meta)
            if not steps:
                continue
            fails = len(re.findall(r"not converging after", text))
            warns = len(re.findall(r"not diagonally dominant|non-negative off-diagonal", text))
            iters = [len(l.split()) - 2 for l in text.splitlines() if l.startswith("GMRES Iteration")]
            out += [f"### {name}, {log.name}", "",
                    f"GMRES iterations per solve: {', '.join(map(str, iters))}. GMRES failures: {fails}; "
                    f"matrix warnings: {warns}.", ""]
            if "C_F" in steps[0]:
                out += ["| Step | Panels | Change of the matrix | $C_F$ | $C_{A0}$ |", "|---|---|---|---|---|"]
                out += [f"| {k + 1} | {s['panels']} | {s['change'] if s['change'] is not None else ''} | "
                        f"{s['C_F']:.3f} | {s['C_A0']:.3f} |" for k, s in enumerate(steps)]
            else:
                out += ["| Step | Panels | Change of the matrix | C |", "|---|---|---|---|"]
                out += [f"| {k + 1} | {s['panels']} | {s['change'] if s['change'] is not None else ''} | {s['C']:.3f} |"
                        for k, s in enumerate(steps)]
            out.append("")
    pc = DATA / "pcbcap_r0402_nofilm.json"
    if pc.exists():
        rec = json.loads(pc.read_text(encoding="utf-8"))
        conv, enc = rec["convergence"], rec["enclosure"]
        out += ["## pcbcap, the film-free 0402", "",
                "| Mesh refine | $C_F$ in the 8-mm box |", "|---|---|"]
        for lv in conv["levels"]:
            out.append(f"| {lv.get('refine', lv.get('factor', ''))} | {lv.get('C_F', float('nan')):.4f} |")
        out += ["", f"Extrapolated in the mesh: {rec['C_F_box8']:.4f} fF, discretisation error {rec['discretisation_error']:.4f} fF; "
                f"enclosure correction {enc['dC_F']:+.4f} fF; with no ground nearby {rec['C_F_no_ground']:.4f} fF.", ""]
    pa = DATA / "pcbcap_r0402_nofilm_air.json"
    if pa.exists():
        rec = json.loads(pa.read_text(encoding="utf-8"))
        conv = rec["convergence"]
        out += ["## pcbcap, the film-free 0402 in a uniform medium (every permittivity 1)", "",
                "| Mesh refine | $C_F$ in the 8-mm box | $C_{A0}$ |", "|---|---|---|"]
        for lv in conv["levels"]:
            out.append(f"| {lv.get('refine', '')} | {lv['C_F']:.4f} | {lv['C_A0']:.4f} |")
        out += ["", f"Extrapolated in the mesh: C_F {conv['C_F']['extrapolated']:.4f} +- {conv['C_F']['error']:.4f} fF, "
                f"C_A0 {conv['C_A0']['extrapolated']:.4f} +- {conv['C_A0']['error']:.4f} fF.", ""]
    (DATA / "README.md").write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {DATA / 'README.md'}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="fastercap_validation.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    e = sub.add_parser("export")
    e.add_argument("case")
    r = sub.add_parser("run")
    r.add_argument("case")
    r.add_argument("--tol", type=float, nargs="+", default=list(TOLS))
    r.add_argument("--galerkin", action="store_true")
    r.add_argument("--timeout", type=float, default=1800.0)
    r.add_argument("--extra", nargs="*", default=[], help="further FasterCap options, e.g. -ap")
    r.add_argument("--mesh", type=float, nargs="*", default=[], help="fixed refinements (-m), instead of --tol")
    sub.add_parser("pcbcap").add_argument("case", choices=["r0402_nofilm", "r0402_nofilm_air"])
    f2 = sub.add_parser("fastcap2", help="the case in FastCap 2.0 (default options: its user's guide, Section 2.1)")
    f2.add_argument("case")
    f2.add_argument("--options", default="-o3 -t0.001")
    f2.add_argument("--timeout", type=float, default=1200.0)
    f2p = sub.add_parser("fastcap2-plan", help="FastCap2's automatic partitioning of the case, from its panels alone")
    f2p.add_argument("case")
    f2p.add_argument("--orders", type=int, nargs="+", default=[2, 3])
    f2p.add_argument("--depth", type=int, default=None, help="a fixed depth (FastCap2's -d), instead of its own choice")
    v = sub.add_parser("view")
    v.add_argument("case")
    v.add_argument("--out", type=Path, required=True, help="folder for the export and the drawing (not the case's)")
    v.add_argument("--z-stretch", type=float, default=1.0)
    o = sub.add_parser("orientation")
    o.add_argument("case", choices=["r0402_nofilm_free8"])
    bf = sub.add_parser("backfill", help="add the checks of each solve to a case's records, from its logs")
    bf.add_argument("case")
    bf.add_argument("--timeout-tag", default=None, help="also record this run (e.g. m100_g_d0.0001) as stopped "
                                                        "at the time limit")
    bf.add_argument("--timeout", type=float, default=None)
    sub.add_parser("report")
    args = ap.parse_args(argv)
    if args.cmd == "list":
        for k in CASES:
            print(k)
    elif args.cmd == "export":
        for k in (CASES if args.case == "all" else [args.case]):
            cmd_export(k)
    elif args.cmd == "run":
        cmd_run(args.case, args.tol, args.galerkin, args.timeout, [e if e.startswith('-') else '-' + e for e in args.extra], args.mesh)
    elif args.cmd == "pcbcap":
        cmd_pcbcap(args.case)
    elif args.cmd == "view":
        cmd_view(args.case, args.out, args.z_stretch)
    elif args.cmd == "fastcap2":
        cmd_fastcap2(args.case, args.options, args.timeout)
    elif args.cmd == "fastcap2-plan":
        cmd_fastcap2_plan(args.case, args.orders, args.depth)
    elif args.cmd == "orientation":
        cmd_orientation(args.case, ("-a0.01", "-ap"))
    elif args.cmd == "backfill":
        if (args.timeout_tag is None) != (args.timeout is None):
            ap.error("--timeout-tag and --timeout go together")
        cmd_backfill(args.case, args.timeout_tag, args.timeout)
    elif args.cmd == "report":
        cmd_report()
    return 0


if __name__ == "__main__":
    sys.exit(main())
