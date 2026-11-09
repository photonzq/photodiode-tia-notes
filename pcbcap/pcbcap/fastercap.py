"""Writing a layout as input for FasterCap, checking what was written, and reading FasterCap's results.

Why this module exists
----------------------
FasterCap (FastFieldSolvers, LGPL 2.1) computes the same electrostatic capacitances as this package
by an unrelated method.  Agreement between the two, within the errors each states, checks both: their
discretisation errors have nothing in common.  This module writes a ``Layout`` as FasterCap's input
files, checks what it wrote against the layout by an independent route, runs FasterCap, and turns its
capacitance matrix into the quantities of ``capacitance.py``.

What FasterCap solves
---------------------
FasterCap's white paper "The Treatment of Dielectrics in FasterCap" (FastFieldSolvers WP130503,
Rev. 02, 2023) describes its formulation.  Every conductor surface and every interface between two
dielectrics is replaced by a sheet of charge in empty space, cut into flat panels that each carry a
constant charge density sigma_k, and the potential anywhere is the free-space integral over the sheets
(its Eq. (21)):
    phi(x) = sum_k sigma_k int_{S_k} dS' / (4 pi eps0 |x - x'|).
Two conditions fix the densities: the potential equals the conductor's potential at the centre of
every conductor panel, and the normal displacement is continuous across every dielectric panel (its
Eqs. (15) and (17), the latter approximated by divided differences at points a short distance either
side of the panel, its Eq. (23) and Fig. 3).  The free charge of a conductor panel is its total charge
times the relative permittivity that touches it (its Eq. (25)).  The potential vanishes at infinity by
construction (its Eq. (18)).  FasterCap returns the Maxwell capacitance matrix: column k holds the
charges on all conductors when conductor k is at 1 V and all others at 0 V, which is the matrix of
``capacitance.py``, Eq. (1).

How a layout becomes FasterCap's input
--------------------------------------
1. Films and sheets that FasterCap cannot describe are replaced (``prepare_layout``, see "Two
   translations are approximate" below).  Mirror symmetries are not used: FasterCap has no symmetry
   option, so the whole layout is exported.
2. Every face of a layout of axis-aligned boxes lies in a plane normal to an axis, at a coordinate
   where some item begins or ends.  ``build_panels`` takes each such plane in turn and cuts it into
   rectangular cells along the coordinates of every item that meets the plane, so that nothing
   changes inside a cell.  Each cell is classified from two points a short distance either side of
   its centre (``probe_distances``), looked up by the painter's order of ``geometry.py``
   (``medium_at``: the item added last wins):

     two sides                                      | FasterCap panel
     -----------------------------------------------+---------------------------------------------------
     the same dielectric, or the same net           | none
     a conductor of net n and permittivity eps      | conductor panel of n with outer permittivity eps
     two different permittivities eps1 < eps2       | dielectric panel, outer eps1, inner eps2, with a
                                                    | reference point on the eps1 side
     a conductor sheet inside one dielectric eps    | conductor panel of the sheet's net, outer eps
     a sheet between two different permittivities  | refused: a panel has one outer permittivity
     two different nets                             | refused: they would be shorted
     a face of the enclosure, grounded export       | conductor panel of "gnd", outer eps of the inside
     a face of the enclosure, free-space export     | none if the enclosure medium touches it; refused
                                                    | if any item does

   The outer permittivity of a conductor panel is the one FasterCap multiplies the panel's total
   charge by to get its free charge (WP130503, Eq. (25)), i.e. that of the medium touching the face.
   The point on the lower-permittivity side becomes the reference point of a dielectric panel.
3. Neighbouring cells of the same kind (and, for an interface, with the lower permittivity on the
   same side) are merged into larger rectangles, greedily: along the first in-plane axis as far as the
   kind holds, then along the second as far as the whole row holds.  A rectangle more than
   ``max_aspect`` times longer than it is wide is cut across into equal pieces, so that no input panel
   is a sliver.  Each rectangle is one quadrilateral panel.  The panels are deliberately coarse:
   FasterCap refines them itself, and its help (InputFile, 3-D chapter 2) advises that "it is best
   working with an input mesh as coarse as possible".  The option ``metal_panel`` overrides this on
   metal: every face of a conductor box (other than the grounded enclosure) is cut into panels no
   longer than ``metal_panel`` times the box's smallest dimension, its thickness.  Thin metal with a
   different permittivity on its two faces is a weak point of the formulation: two facing panels much
   larger than the metal's thickness d have nearly the same potential equation (their coefficients
   differ by about 1.78 d/s for panels of side s), so the split of the charge between the faces,
   which Eq. (25) of WP130503 weights by the two permittivities, is poorly determined.  On the 0402
   of the companion note, though, cutting the metal this way does not make FasterCap solve the model
   with its dielectrics (side note TIA_feedback_layouts, Appendix D).  The options ``fine_window``,
   ``fine_panel`` and ``max_panel`` cut the faces near the part and away from it as well.  To solve the
   exported panels without FasterCap's own refinement, run it with a large -m and a small -d (-m100
   -d0.0001): its link tolerance is -d times -m (m_dEps = m_dEpsRatio * m_dMeshEps in
   Solver/SolveCapacitance.cpp of its source), so -m100 with the default -d1 also compresses the
   interactions, to about 3 links per panel on the 0402.  Cutting every face this way does not make it
   solve the 0402 with its dielectrics either (same appendix).
4. Files (``write_files``): a list file, one conductor file per outer permittivity, all joined into
   one chain with "+" so that panels of the same conductor name in different files form one
   conductor (help, 3-D chapter 3: "panels with the same conductor name in different files will
   belong to the same conductor"), and one dielectric file per pair of permittivities, with a
   reference point on every panel (help, 3-D chapter 4: per-panel reference points override that of
   the D statement).  FasterCap ignores the first line of every file (help, 3-D chapter 2), and reads
   a list file whose first line contains "2D" as a two-dimensional model (2-D chapter 2), so every
   file starts with a comment line that does not.  Lengths are written in metres: FasterCap's own
   example, a cube of 1 x 1 x 1 in its input units, gives capacitances of tens of picofarads
   (Output chapter 3), which is the size of a 1-m cube.

Two translations are exact
--------------------------
* The grounded enclosure becomes a closed conductor box named "gnd".  It imposes phi = 0 on the same
  faces as the finite elements' Dirichlet condition.  Its panels carry the charge of its inner
  surface: outside a closed conductor at 0 V with all charges inside, the potential is 0 everywhere
  (it is 0 on the box and at infinity, and harmonic between them), so its outer surface carries no
  charge.  A board that fills the enclosure meets the box walls, and those faces become "gnd" panels
  with the board's permittivity.
* A mirror-symmetric layout is exported whole.  The finite elements solve a half or a quarter of it,
  which ``capacitance.py`` (section 4) shows to be exact.

Two translations are approximate
--------------------------------
* A conductor sheet lying between two different permittivities (a pad of zero thickness on the board,
  say) cannot be one layer of panels, because a panel has a single outer permittivity.  It is given a
  thickness ``sheet_thickness`` (refused when that option is None), grown into the side of lower
  permittivity, which must hold one dielectric throughout the slab.
* A resistive film carries a potential that varies along it; a FasterCap conductor has one potential.
  The film is therefore cut into ``film_strips`` strips, each a separate conductor of thickness
  ``film_thickness`` grown into the film's side of lower permittivity (the air above the body), with
  gaps ``film_gap`` between neighbouring strips and between the end strips and the terminations.
  Strip k carries the film's DC potential u_k at its centre (``geometry.LinearProfile``).  With the
  Maxwell matrix C of all conductors, the feedback capacitance is C_F = -v^T C u (capacitance.py,
  Eq. (3)), where u holds 1 on net A, 0 on net B and u_k on the strips, and v = 1 - u on those
  conductors.
  How far the staircase lies from the linear potential.  Between two neighbouring strips the potential
  jumps by Delta V = 1/N, N the number of strips.  At a distance r from the junction the potential in
  each of the two half-spaces (permittivities eps_a and eps_b) turns through Delta V over an angle pi,
  so the field is Delta V / (pi r), and its energy per unit length of junction between radii h and
  l is (eps0 eps / (2 pi)) Delta V^2 ln(l / h) in each half-space.  Twice the energy, the quantity of
  capacitance.py's Eq. (1), over a junction of width W is c_j Delta V^2 with
      c_j = eps0 (eps_a + eps_b) W ln(l / h) / pi.
  Only the odd drive has steps (the even drive holds the whole film at 1/2), so the about N junctions
  raise C_F by about
      Delta C_F = N c_j / N^2 = eps0 (eps_a + eps_b) W ln(l / h) / (pi N),
  with l = L_f / N the strip length and h the gap or, for touching strips, the finest panel at the
  junction.  For an 0402 (W = 0.50 mm, L_f = 0.60 mm, alumina 9.7 below and air above) the prefactor
  is 8.854 fF/mm x 10.7 x 0.50 mm / pi = 15.1 fF, so N = 10, 20 and 40 with h = 2 um (ln(l/h) = 3.40,
  2.71 and 2.01) give about 5.1, 2.0 and 0.76 fF.  The error falls only as (ln N)/N;
  ``film_strip_estimate`` evaluates it.  It is an estimate of the size and sign of the error, good to a
  factor of order one (the largest radius is only of the order of l), not a correction to apply.

Reading the results
-------------------
``read_matrix`` takes the last block "Capacitance matrix is:" of FasterCap's output (help, Output
chapter 3).  FasterCap prefixes each conductor name with its group ("g1_"); the prefix is removed.  The
matrix of a collocation method is not exactly symmetric; ``two_port`` reports the largest asymmetry
and uses the symmetric part.  A floating conductor f carries no net charge: from Q_f = C_fn V_n +
C_ff V_f = 0 follows V_f = -C_ff^-1 C_fn V_n, and the charges on the other conductors are
Q_n = (C_nn - C_nf C_ff^-1 C_fn) V_n.  This reduced matrix is exact for the model and replaces C.
Then C_F = -v^T C u, C_A0 = u^T C (u + v) and C_B0 = v^T C (u + v), as in capacitance.py, Eqs. (4)-(5),
with every other conductor, the box included, at 0 V in both drives.

Checking the written geometry without FasterCap
-----------------------------------------------
``gmsh_areas`` finds the area of every kind of panel a second way, which shares no code with the
cells: the layout is split into pieces exactly as ``meshing.build_mesh`` splits it (every item and the
enclosure become OpenCASCADE entities, gmsh's ``fragment`` cuts them along each other's boundaries,
and each volume piece belongs to the item added last), each face of the pieces is classified from
the pieces on its two sides as gmsh's topology reports them, and its exact area is added to its kind.
The areas per kind (conductor net and outer permittivity, or pair of permittivities) must equal those
of the panels; ``compare_areas`` does the comparison.  The two routes share only the table above and
the definition of the layout.

What the export does not do
---------------------------
Nothing magnetic, as in the rest of the package.  Lossy permittivities, which FasterCap accepts as
complex numbers, are not written: every material has one real permittivity (materials.py).
"""
from __future__ import annotations

import json
import math
import os
import re
import subprocess
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from .constants import EPS0
from .geometry import GROUND, Box, Conductor, Dielectric, Film, Layout, LinearProfile, Sheet

M_PER_MM = 1e-3            # FasterCap's lengths are metres (module docstring, step 4)
FF_PER_F = 1e15
OUTSIDE, ENCLOSURE = -2, -1
AXES = ("x", "y", "z")


class ExportError(ValueError):
    """The layout holds something FasterCap's input cannot describe (module docstring)."""


@dataclass
class ExportOptions:
    """How a layout is translated (all lengths in mm).

    boundary        : "ground" (the enclosure becomes a closed grounded box, the exact equivalent of
                      the finite elements' grounded enclosure) or "free" (no enclosure: free space, in
                      which every item must lie strictly inside the enclosure, e.g. a board of finite
                      size).
    films           : "strips" (each film becomes ``film_strips`` strip conductors) or "drop" (films are
                      removed, leaving the face they lay on bare).
    film_strips, film_gap, film_thickness : the strips (module docstring).  The 2-um defaults are
                      choices: thin next to the 15-um terminations, wide enough for the panels.
    sheet_thickness : thickness given to a conductor sheet between two different permittivities;
                      None refuses such sheets.
    max_aspect      : longest side of an input panel over its shortest (module docstring, step 3);
                      10 is a choice that keeps slivers out without multiplying the panels.
    max_panel       : longest side of an input panel; None leaves the merged rectangles whole, since
                      FasterCap refines them where the field needs it.
    metal_panel     : if set, the faces of every conductor box except the grounded enclosure are cut
                      into panels no longer than this factor times the box's smallest dimension (its
                      thickness): 1.0 makes the panels on a 15-um termination 15 um wide (module
                      docstring, step 3).  Conductor sheets are not affected.
    fine_window, fine_panel : if both are set, every face (conductor or dielectric) inside the box
                      fine_window = ((x0, x1), (y0, y1), (z0, z1)) is cut into panels no longer than
                      fine_panel; the window's edges become cut lines on every plane it crosses, so
                      that only the part of a large face inside it is refined.  Meant for the
                      dielectric faces next to thin metal and thin gaps (side note
                      TIA_feedback_layouts, Appendix D).
    """

    boundary: str = "ground"
    films: str = "strips"
    film_strips: int = 10
    film_gap: float = 0.002
    film_thickness: float = 0.002
    sheet_thickness: float | None = None
    max_aspect: float = 10.0
    max_panel: float | None = None
    metal_panel: float | None = None
    fine_window: tuple | None = None
    fine_panel: float | None = None


# ================================================================================================
# What fills a point, and what a face becomes
# ================================================================================================
@dataclass(frozen=True)
class Medium:
    """What fills a volume: kind "dielectric" (eps), "conductor" (net, floating) or "outside"."""

    kind: str
    eps: float = 0.0
    net: str = ""
    floating: bool = False


def _same(a: float, b: float) -> bool:
    return math.isclose(a, b, rel_tol=1e-12, abs_tol=0.0)


def _eps_key(eps: float) -> float:
    return float(round(eps, 12))


def medium_of(layout: Layout, k: int) -> Medium:
    """The medium of item k (an index into layout.items), of the enclosure (ENCLOSURE) or OUTSIDE."""
    if k == OUTSIDE:
        return Medium("outside")
    if k == ENCLOSURE:
        return Medium("dielectric", eps=float(layout.enclosure.material.eps_r))
    r = layout.items[k].role
    if isinstance(r, Dielectric):
        return Medium("dielectric", eps=float(r.eps_r))
    if isinstance(r, Conductor):
        return Medium("conductor", net=r.net, floating=r.floating)
    raise ExportError(f"item {k} fills a volume but is neither a dielectric nor a conductor")


def medium_at(layout: Layout, pts: np.ndarray, candidates=None) -> np.ndarray:
    """The item that fills each point: the index of the last box that contains it (painter's order),
    ENCLOSURE where no box does, OUTSIDE beyond the enclosure.  ``pts`` is (n, 3) in mm.  Sheets fill
    no volume (geometry.Layout), so they are not looked at.  Containment is strict, so the points must
    not lie on a face; they are always taken a distance from faces (``probe_distances``).
    ``candidates`` restricts the search to some boxes, when the others cannot contain the points."""
    pts = np.atleast_2d(np.asarray(pts, dtype=float))
    out = np.full(len(pts), ENCLOSURE, dtype=int)
    ks = range(len(layout.items)) if candidates is None else sorted(candidates)
    for k in ks:
        it = layout.items[k]
        if not isinstance(it, Box):
            continue
        inside = np.ones(len(pts), dtype=bool)
        for i, a in enumerate(AXES):
            lo, hi = it.spans[a]
            inside &= (pts[:, i] > lo) & (pts[:, i] < hi)
        out[inside] = k
    enc = layout.enclosure.spans
    inside_enc = np.ones(len(pts), dtype=bool)
    for i, a in enumerate(AXES):
        lo, hi = enc[a]
        inside_enc &= (pts[:, i] > lo) & (pts[:, i] < hi)
    out[~inside_enc] = OUTSIDE
    return out


def classify(m1: Medium, m2: Medium, sheet, boundary: str, enc_eps: float):
    """What a face between media m1 and m2 becomes (the table of the module docstring).

    ``sheet`` is the role of a sheet lying on the face (a Conductor), or None.  Returns None (no
    panel), ("C", net, eps) for a conductor panel with outer permittivity eps, or ("D", eps_out,
    eps_in) with eps_out < eps_in for a dielectric panel; raises ExportError for what cannot be
    exported."""
    if isinstance(sheet, Film):
        raise ExportError("a film reached the classification; prepare_layout turns films into strips")
    if m2.kind == "outside":
        m1, m2 = m2, m1
    if m1.kind == "outside":
        inner = m2
        if inner.kind == "outside":
            return None
        if sheet is not None:
            if boundary == "ground" and sheet.net == GROUND:
                return None
            raise ExportError(f"a sheet of net {sheet.net!r} lies on the enclosure")
        if boundary == "ground":
            if inner.kind == "dielectric":
                return ("C", GROUND, _eps_key(inner.eps))
            if inner.net == GROUND:
                return None
            raise ExportError(f"net {inner.net!r} touches the grounded enclosure")
        if inner.kind == "dielectric" and _same(inner.eps, enc_eps):
            return None
        raise ExportError("in free space every item must lie inside the enclosure, but one touches it "
                          "(give the board a finite size, parts.Board.size)")
    if sheet is not None:
        for m in (m1, m2):
            if m.kind == "conductor" and m.net != sheet.net:
                raise ExportError(f"a sheet of net {sheet.net!r} touches net {m.net!r}")
        diel = [m for m in (m1, m2) if m.kind == "dielectric"]
        if not diel:
            return None
        if len(diel) == 2 and not _same(diel[0].eps, diel[1].eps):
            raise ExportError(f"a sheet of net {sheet.net!r} lies between permittivities {diel[0].eps:g} and "
                              f"{diel[1].eps:g}; give it a thickness (ExportOptions.sheet_thickness)")
        return ("C", sheet.net, _eps_key(diel[0].eps))
    if m1.kind == "conductor" and m2.kind == "conductor":
        if m1.net == m2.net:
            return None
        raise ExportError(f"nets {m1.net!r} and {m2.net!r} touch")
    if m1.kind == "conductor":
        return ("C", m1.net, _eps_key(m2.eps))
    if m2.kind == "conductor":
        return ("C", m2.net, _eps_key(m1.eps))
    if _same(m1.eps, m2.eps):
        return None
    lo, hi = sorted((m1.eps, m2.eps))
    return ("D", _eps_key(lo), _eps_key(hi))


# ================================================================================================
# Planes, probing distances and cells
# ================================================================================================
def _plane_coords(layout: Layout, axis: str) -> list[float]:
    """Every coordinate along ``axis`` at which an item, a sheet's hole or the enclosure has a face."""
    cs = set(layout.enclosure.spans[axis])
    for it in layout.items:
        cs.update(layout.item_extent(it)[axis])
        if isinstance(it, Sheet):
            for h in it.holes:
                if axis in h:
                    cs.update(h[axis])
    return sorted(cs)


def probe_distances(layout: Layout, cap: float = 1e-3) -> dict[str, float]:
    """How far from a face (mm) the points are taken that tell what lies on either side of it.

    A quarter of the smallest spacing between distinct face coordinates along each axis, so that a
    point taken that far from a face can never reach the next parallel face; capped at 1 um."""
    out = {}
    for a in AXES:
        cs = _plane_coords(layout, a)
        gaps = [q - p for p, q in zip(cs, cs[1:]) if q - p > 1e-9]
        out[a] = min(cap, 0.25 * min(gaps)) if gaps else cap
    return out


def _breakpoints(layout: Layout, normal: str, spans: dict, holes=(), only=None):
    """The coordinates along the two in-plane axes at which the rectangle ``spans`` of a plane normal
    to ``normal`` must be cut: its own edges, those of ``holes``, and those of every item (or of the
    items listed in ``only``) that lie within it."""
    u, v = [a for a in AXES if a != normal]
    bu, bv = set(spans[u]), set(spans[v])
    for h in holes:
        bu.update(h[u])
        bv.update(h[v])
    for k in (range(len(layout.items)) if only is None else only):
        it = layout.items[k]
        ext = layout.item_extent(it)
        bu.update(ext[u])
        bv.update(ext[v])
        if isinstance(it, Sheet):
            for h in it.holes:
                bu.update(h.get(u, ()))
                bv.update(h.get(v, ()))
    bu = np.array(sorted(x for x in bu if spans[u][0] <= x <= spans[u][1]))
    bv = np.array(sorted(x for x in bv if spans[v][0] <= x <= spans[v][1]))
    return u, v, bu, bv


def _cells(layout: Layout, normal: str, at: float, spans: dict, holes=(), only=None):
    """Rectangular cells covering the rectangle ``spans`` of the plane normal = at (``_breakpoints``);
    cells inside a hole are left out.  Returns the cell centres (m, 3) and areas (m,)."""
    u, v, bu, bv = _breakpoints(layout, normal, spans, holes, only)
    uu, vv = np.meshgrid(0.5 * (bu[1:] + bu[:-1]), 0.5 * (bv[1:] + bv[:-1]), indexing="ij")
    area = np.outer(np.diff(bu), np.diff(bv))
    keep = np.ones(uu.shape, dtype=bool)
    for h in holes:
        keep &= ~((uu > h[u][0]) & (uu < h[u][1]) & (vv > h[v][0]) & (vv < h[v][1]))
    pts = np.zeros((int(keep.sum()), 3))
    pts[:, AXES.index(normal)] = at
    pts[:, AXES.index(u)] = uu[keep]
    pts[:, AXES.index(v)] = vv[keep]
    return pts, area[keep]


def _offset(pts: np.ndarray, axis: str, d: float) -> np.ndarray:
    q = pts.copy()
    q[:, AXES.index(axis)] += d
    return q


# ================================================================================================
# Films to strips, sheets to thin boxes
# ================================================================================================
def _sanitize(name: str) -> str:
    s = re.sub(r"[^A-Za-z0-9_]", "_", name)
    return s or "n"


def _thicken_side(layout: Layout, sheet: Sheet, t: float, probe: dict, what: str) -> tuple[int, float]:
    """Side (+1 or -1 along the sheet's normal) into which ``sheet`` can be grown by ``t``: the side of
    lower permittivity, which must hold one dielectric over the whole sheet and through the whole slab.
    Returns the side and that dielectric's permittivity."""
    n = sheet.normal
    pts, _ = _cells(layout, n, sheet.at, sheet.spans, sheet.holes)
    d = probe[n]
    below, above = medium_at(layout, _offset(pts, n, -d)), medium_at(layout, _offset(pts, n, +d))
    meds = {}
    for side, ks in ((-1, below), (+1, above)):
        uniq = set(ks.tolist())
        if len(uniq) != 1:
            raise ExportError(f"{what}: the medium on its {'-+'[side > 0]}{n} side changes along it")
        m = medium_of(layout, uniq.pop())
        if m.kind != "dielectric":
            raise ExportError(f"{what}: a conductor or the enclosure's outside lies against it")
        meds[side] = m
    side = -1 if meds[-1].eps < meds[+1].eps else +1
    k0 = (below if side < 0 else above)[0]
    for depth in (0.5 * t, t - min(d, 0.25 * t)):
        ks = medium_at(layout, _offset(pts, n, side * depth))
        if np.any(ks != k0):
            raise ExportError(f"{what}: the slab of thickness {t} mm on its lower-permittivity side "
                              "does not hold one dielectric throughout")
    lo_slab, hi_slab = sorted((sheet.at, sheet.at + side * t))
    rect = sheet.spans
    for it in layout.items:
        if it is sheet:
            continue
        ext = layout.item_extent(it)
        overlap = all(min(ext[a][1], rect[a][1]) > max(ext[a][0], rect[a][0]) for a in rect)
        if overlap and any(lo_slab < c < hi_slab for c in ext[n]):
            raise ExportError(f"{what}: item {it.name or type(it).__name__} has a face inside the slab")
    return side, meds[side].eps


def _slab_spans(sheet: Sheet, side: int, t: float, along: str | None = None, iv=None) -> dict:
    spans = dict(sheet.spans)
    if along is not None:
        spans[along] = iv
    spans[sheet.normal] = (sheet.at, sheet.at + t) if side > 0 else (sheet.at - t, sheet.at)
    return spans


def prepare_layout(layout: Layout, opt: ExportOptions):
    """The layout as FasterCap will see it: films cut into strips (or dropped), sheets that lie between
    two permittivities thickened, mirror symmetries cleared.  Returns (layout, films, notes): films
    describes the strips of each film, notes lists every change in words."""
    if layout.dim != 3:
        raise ExportError("only three-dimensional layouts can be exported")
    if opt.boundary not in ("ground", "free"):
        raise ValueError("boundary must be 'ground' or 'free'")
    if opt.films not in ("strips", "drop"):
        raise ValueError("films must be 'strips' or 'drop'")
    enc = layout.enclosure
    if enc is None:
        raise ExportError("the layout needs an enclosure")
    if opt.boundary == "ground":
        kinds = {enc.face_condition(f) for f in ("xmin", "xmax", "ymin", "ymax", "zmin", "zmax")}
        if kinds != {"ground"}:
            raise ExportError("FasterCap has no insulating (zero-flux) boundary; use a grounded enclosure "
                              "or a free-space export")
    probe = probe_distances(layout)
    nets_used = set(layout.nets())
    new = Layout(3, layout.name)
    new.enclosure = enc
    new.pair = tuple(layout.pair)
    films, notes, extra = [], [], []
    for k, it in enumerate(layout.items):
        if isinstance(it, Sheet) and isinstance(it.role, Film):
            label = it.name or f"film{k}"
            if opt.films == "drop":
                notes.append(f"film {label} removed")
                continue
            prof = it.role.profile
            if not isinstance(prof, LinearProfile) or prof.axis == it.normal or prof.axis not in it.spans:
                raise ExportError(f"film {label}: only a plain film (LinearProfile along the sheet) can be "
                                  "cut into strips")
            if it.holes:
                raise ExportError(f"film {label}: a film with holes cannot be cut into strips")
            n, gap, t = int(opt.film_strips), float(opt.film_gap), float(opt.film_thickness)
            a = prof.axis
            s0, s1 = it.spans[a]
            ell = (s1 - s0 - (n + 1) * gap) / n
            if n < 1 or ell <= 0:
                raise ExportError(f"film {label}: {n} strips with gaps of {gap} mm do not fit")
            side, eps_side = _thicken_side(layout, it, t, probe, f"film {label}")
            base = _sanitize(label)
            strips = []
            for j in range(n):
                lo = s0 + gap + j * (ell + gap)
                net = f"{base}_s{j + 1:02d}"
                if net in nets_used:
                    raise ExportError(f"strip name {net!r} is already a net of the layout")
                nets_used.add(net)
                u = float(prof(np.array([[lo + 0.5 * ell]]), (a,))[0])
                sp = _slab_spans(it, side, t, a, (lo, lo + ell))
                extra.append(Box(sp["x"], sp["y"], sp["z"], Conductor(net), name=net))
                strips.append(dict(net=net, u=u, span=[lo, lo + ell]))
            films.append(dict(name=label, hi=it.role.hi, lo=it.role.lo, axis=a, normal=it.normal,
                              side=side, side_eps=eps_side, thickness=t, gap=gap, strips=strips))
            notes.append(f"film {label} cut into {n} strips of {ell * 1e3:.3f} um x {t * 1e3:g} um with "
                         f"{gap * 1e3:g}-um gaps, grown into its side of permittivity {eps_side:g}")
            continue
        if isinstance(it, Sheet):
            n_ax = it.normal
            pts, _ = _cells(layout, n_ax, it.at, it.spans, it.holes)
            d = probe[n_ax]
            m_lo = [medium_of(layout, k2) for k2 in medium_at(layout, _offset(pts, n_ax, -d)).tolist()]
            m_hi = [medium_of(layout, k2) for k2 in medium_at(layout, _offset(pts, n_ax, +d)).tolist()]
            differs = any(p.kind == "dielectric" and q.kind == "dielectric" and not _same(p.eps, q.eps)
                          for p, q in zip(m_lo, m_hi))
            if not differs:
                new.items.append(it)
                continue
            label = it.name or f"sheet{k}"
            if opt.sheet_thickness is None:
                raise ExportError(f"sheet {label} lies between two permittivities; set "
                                  "ExportOptions.sheet_thickness to export it as a thin box")
            if it.holes:
                raise ExportError(f"sheet {label}: a sheet with holes cannot be thickened")
            t = float(opt.sheet_thickness)
            side, eps_side = _thicken_side(layout, it, t, probe, f"sheet {label}")
            sp = _slab_spans(it, side, t)
            extra.append(Box(sp["x"], sp["y"], sp["z"], it.role, name=label))
            notes.append(f"sheet {label} given a thickness of {t * 1e3:g} um into its side of permittivity "
                         f"{eps_side:g}")
            continue
        new.items.append(it)
    new.items.extend(extra)
    return new, films, notes


# ================================================================================================
# Panels
# ================================================================================================
@dataclass
class Panels:
    """Quadrilateral panels of an exported layout (lengths in mm).

    quad : (n, 4, 3) corners, in order around each rectangle;
    key  : per panel ("C", net, eps) or ("D", eps_out, eps_in);
    ref  : (n, 3) reference point of a dielectric panel, on its eps_out side (NaN for conductors);
    area : (n,)."""

    quad: np.ndarray
    key: list
    ref: np.ndarray
    area: np.ndarray
    layout: Layout
    probe: dict
    stats: dict = field(default_factory=dict)

    def areas_by_key(self) -> dict:
        out: dict = defaultdict(float)
        for k, a in zip(self.key, self.area):
            out[k] += float(a)
        return dict(out)


def _merge(grid: np.ndarray) -> list[tuple[int, int, int, int, int]]:
    """Greedy cover of the cells of an integer grid (-1: no panel) by rectangles of one value:
    (i0, i1, j0, j1, value) with cells i0 <= i < i1, j0 <= j < j1 (module docstring, step 3)."""
    nu, nv = grid.shape
    used = grid < 0
    out = []
    for i in range(nu):
        for j in range(nv):
            if used[i, j]:
                continue
            val = grid[i, j]
            j1 = j + 1
            while j1 < nv and not used[i, j1] and grid[i, j1] == val:
                j1 += 1
            i1 = i + 1
            while i1 < nu and not used[i1, j:j1].any() and np.all(grid[i1, j:j1] == val):
                i1 += 1
            used[i:i1, j:j1] = True
            out.append((i, i1, j, j1, int(val)))
    return out


def _split(lo_u, hi_u, lo_v, hi_v, max_aspect: float, max_panel: float | None):
    """Cut the rectangle [lo_u, hi_u] x [lo_v, hi_v] into equal pieces so that no piece is longer than
    ``max_aspect`` times its width or longer than ``max_panel``."""
    du, dv = hi_u - lo_u, hi_v - lo_v
    nu = max(1, math.ceil(du / (max_aspect * dv) - 1e-9))
    nv = max(1, math.ceil(dv / (max_aspect * du) - 1e-9))
    if max_panel is not None:
        nu = max(nu, math.ceil(du / max_panel - 1e-9))
        nv = max(nv, math.ceil(dv / max_panel - 1e-9))
    us = np.linspace(lo_u, hi_u, nu + 1)
    vs = np.linspace(lo_v, hi_v, nv + 1)
    return [(us[i], us[i + 1], vs[j], vs[j + 1]) for i in range(nu) for j in range(nv)]


def build_panels(layout: Layout, opt: ExportOptions) -> Panels:
    """The panels of a prepared layout (module docstring, steps 2 and 3)."""
    t0 = time.perf_counter()
    probe = probe_distances(layout)
    enc = layout.enclosure.spans
    enc_eps = float(layout.enclosure.material.eps_r)
    boxes = [k for k, it in enumerate(layout.items) if isinstance(it, Box)]
    sheets = [k for k, it in enumerate(layout.items) if isinstance(it, Sheet)]
    quads, keys, refs = [], [], []
    n_cells = 0
    for a in AXES:
        ia = AXES.index(a)
        for c in _plane_coords(layout, a):
            if not (enc[a][0] <= c <= enc[a][1]):
                continue
            rel_boxes = [k for k in boxes if layout.items[k].spans[a][0] <= c <= layout.items[k].spans[a][1]]
            rel_sheets = [k for k in sheets if layout.items[k].normal == a and abs(layout.items[k].at - c) < 1e-12]
            u, v, bu, bv = _breakpoints(layout, a, None or {b: enc[b] for b in AXES if b != a},
                                        only=rel_boxes + rel_sheets)
            iu, iv = AXES.index(u), AXES.index(v)
            # fine_window: its edges cut this plane, and the cells inside it get their own label
            win = dict(zip(AXES, opt.fine_window)) if (opt.fine_window is not None and opt.fine_panel is not None) else None
            in_plane = win is not None and win[a][0] <= c <= win[a][1]
            if in_plane and len(bu) > 1 and len(bv) > 1:
                bu = np.unique(np.concatenate([bu, [x for x in win[u] if bu[0] < x < bu[-1]]]))
                bv = np.unique(np.concatenate([bv, [x for x in win[v] if bv[0] < x < bv[-1]]]))
            nu, nv = len(bu) - 1, len(bv) - 1
            if nu < 1 or nv < 1:
                continue
            uu, vv = np.meshgrid(0.5 * (bu[1:] + bu[:-1]), 0.5 * (bv[1:] + bv[:-1]), indexing="ij")
            inside = np.zeros(nu * nv, dtype=int)
            if in_plane:
                inside = ((uu.ravel() > win[u][0]) & (uu.ravel() < win[u][1]) &
                          (vv.ravel() > win[v][0]) & (vv.ravel() < win[v][1])).astype(int)
            pts = np.zeros((nu * nv, 3))
            pts[:, ia] = c
            pts[:, iu] = uu.ravel()
            pts[:, iv] = vv.ravel()
            n_cells += len(pts)
            km = medium_at(layout, _offset(pts, a, -probe[a]), rel_boxes)
            kp = medium_at(layout, _offset(pts, a, +probe[a]), rel_boxes)
            ks = np.full(len(pts), -1, dtype=int)
            for k in rel_sheets:
                sh = layout.items[k]
                inside = ((pts[:, iu] > sh.spans[u][0]) & (pts[:, iu] < sh.spans[u][1]) &
                          (pts[:, iv] > sh.spans[v][0]) & (pts[:, iv] < sh.spans[v][1]))
                for h in sh.holes:
                    inside &= ~((pts[:, iu] > h[u][0]) & (pts[:, iu] < h[u][1]) &
                                (pts[:, iv] > h[v][0]) & (pts[:, iv] < h[v][1]))
                ks[inside] = k
            combos, inv = np.unique(np.stack([km, kp, ks, inside], axis=1), axis=0, return_inverse=True)
            inv = inv.ravel()
            labels, label_id = [], {}
            combo_label = np.full(len(combos), -1, dtype=int)
            for j, (m1, m2, s, ins) in enumerate(combos.tolist()):
                role = layout.items[s].role if s >= 0 else None
                med1, med2 = medium_of(layout, m1), medium_of(layout, m2)
                key = classify(med1, med2, role, "ground" if opt.boundary == "ground" else "free", enc_eps)
                if key is None:
                    continue
                side = 0
                if key[0] == "D":
                    side = +1 if _same(med2.eps, key[1]) else -1      # the side holding eps_out
                size = None                                           # metal_panel: panel limit on this face
                if opt.metal_panel is not None and key[0] == "C" and s < 0:
                    k_c = m1 if med1.kind == "conductor" else (m2 if med2.kind == "conductor" else None)
                    if k_c is not None and k_c >= 0:
                        sp = layout.items[k_c].spans
                        size = float(opt.metal_panel) * min(sp[b][1] - sp[b][0] for b in AXES)
                lab = (key, side, size, bool(ins))
                if lab not in label_id:
                    label_id[lab] = len(labels)
                    labels.append(lab)
                combo_label[j] = label_id[lab]
            grid = combo_label[inv].reshape(nu, nv)
            for i0, i1, j0, j1, lab in _merge(grid):
                key, side, size, ins = labels[lab]
                limits = [x for x in (opt.max_panel, size, opt.fine_panel if ins else None) if x is not None]
                limit = min(limits) if limits else None
                for u0, u1, v0, v1 in _split(bu[i0], bu[i1], bv[j0], bv[j1], opt.max_aspect, limit):
                    q = np.zeros((4, 3))
                    q[:, ia] = c
                    q[:, iu] = (u0, u1, u1, u0)
                    q[:, iv] = (v0, v0, v1, v1)
                    quads.append(q)
                    keys.append(key)
                    r = np.full(3, np.nan)
                    if key[0] == "D":
                        r = q.mean(axis=0)
                        r[ia] += side * probe[a]
                    refs.append(r)
    quad = np.array(quads) if quads else np.zeros((0, 4, 3))
    area = np.abs((quad[:, 1] - quad[:, 0]) * 1.0).sum(axis=1) * 0.0 if len(quad) == 0 else \
        np.linalg.norm(np.cross(quad[:, 1] - quad[:, 0], quad[:, 3] - quad[:, 0]), axis=1)
    stats = dict(panels=len(quad), cells=n_cells, seconds=time.perf_counter() - t0, probe_mm=probe,
                 smallest_side_mm=float(min(np.linalg.norm(quad[:, 1] - quad[:, 0], axis=1).min(),
                                            np.linalg.norm(quad[:, 3] - quad[:, 0], axis=1).min())) if len(quad) else None)
    return Panels(quad, keys, np.array(refs) if refs else np.zeros((0, 3)), area, layout, probe, stats)


# ================================================================================================
# Files
# ================================================================================================
def conductor_names(nets) -> dict[str, str]:
    """FasterCap names for the nets: letters, digits and underscores, distinct even ignoring case, and
    never of the form of FasterCap's group prefix ("g1_...")."""
    out, seen = {}, set()
    for net in sorted(nets):
        s = _sanitize(net)
        if re.match(r"^g\d+_", s, flags=re.IGNORECASE):
            s = "n_" + s
        base, j = s, 2
        while s.lower() in seen:
            s, j = f"{base}_{j}", j + 1
        seen.add(s.lower())
        out[net] = s
    return out


def _fmt(v) -> str:
    return " ".join(f"{x:.9e}" for x in np.ravel(v))


def write_files(panels: Panels, out_dir, stem: str, header: list[str]) -> dict:
    """Write ``stem``.lst and its panel files into ``out_dir`` (module docstring, step 4); returns the
    file names and the names given to the conductors."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    nets = sorted({k[1] for k in panels.key if k[0] == "C"})
    names = conductor_names(nets)
    cond, diel = defaultdict(list), defaultdict(list)
    for i, k in enumerate(panels.key):
        (cond[k[2]] if k[0] == "C" else diel[(k[1], k[2])]).append(i)
    first = "* Three-dimensional layout exported by pcbcap.fastercap"
    if "2d" in first.lower():
        raise AssertionError("the first line of the list file must not contain '2D'")
    lines = [first] + [f"* {h}" for h in header]
    files = []
    c_files = sorted(cond)
    for j, eps in enumerate(c_files):
        fn = f"{stem}_c{j + 1}.txt"
        with open(out / fn, "w", encoding="ascii", newline="\n") as f:
            f.write(f"* conductor panels touching relative permittivity {eps:g}\n")
            for i in cond[eps]:
                f.write(f"Q {names[panels.key[i][1]]} {_fmt(panels.quad[i] * M_PER_MM)}\n")
        lines.append(f"C {fn} {eps:.12g} 0 0 0" + (" +" if j < len(c_files) - 1 else ""))
        files.append(fn)
    for j, (lo, hi) in enumerate(sorted(diel)):
        fn = f"{stem}_d{j + 1}.txt"
        idx = diel[(lo, hi)]
        with open(out / fn, "w", encoding="ascii", newline="\n") as f:
            f.write(f"* interface between relative permittivities {lo:g} (outer side, where every reference "
                    f"point lies) and {hi:g}\n")
            for i in idx:
                f.write(f"Q d {_fmt(panels.quad[i] * M_PER_MM)} {_fmt(panels.ref[i] * M_PER_MM)}\n")
        lines.append(f"D {fn} {lo:.12g} {hi:.12g} 0 0 0 {_fmt(panels.ref[idx[0]] * M_PER_MM)}")
        files.append(fn)
    with open(out / f"{stem}.lst", "w", encoding="ascii", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    return dict(list=f"{stem}.lst", panel_files=files, names=names)


@dataclass
class Export:
    layout: Layout              # the prepared layout that was written
    panels: Panels
    meta: dict
    directory: Path


def export(layout: Layout, out_dir, stem: str, opt: ExportOptions | None = None) -> Export:
    """Prepare and write ``layout``; also writes ``stem``.json with everything the reader needs
    (conductor names, floating nets, the strips' potentials)."""
    opt = opt or ExportOptions()
    prepared, films, notes = prepare_layout(layout, opt)
    panels = build_panels(prepared, opt)
    floating = prepared.nets()
    header = [f"layout: {layout.name}",
              f"boundary: {'closed grounded box (the enclosure)' if opt.boundary == 'ground' else 'free space'}",
              "lengths in metres"] + notes
    files = write_files(panels, out_dir, stem, header)
    conductors = {fc: dict(net=net, floating=bool(floating.get(net, False))) for net, fc in files["names"].items()}
    for f in films:
        for s in f["strips"]:
            s["conductor"] = files["names"].get(s["net"])
    meta = dict(format="pcbcap.fastercap 1", layout=layout.name, stem=stem, boundary=opt.boundary,
                options=dict(opt.__dict__), pair=list(prepared.pair), conductors=conductors, films=films,
                notes=notes, files=files, units="m",
                areas_mm2={json.dumps(list(k)): v for k, v in panels.areas_by_key().items()}, stats=panels.stats)
    out = Path(out_dir)
    (out / f"{stem}.json").write_text(json.dumps(meta, indent=1), encoding="utf-8", newline="\n")
    return Export(prepared, panels, meta, out)


# ================================================================================================
# The independent check of the areas
# ================================================================================================
def _on_enclosure(bbox, dom, tol: float = 1e-5) -> bool:
    """Whether a face whose bounding box is ``bbox`` lies in a face of the enclosure ``dom``.  The
    tolerance (mm) absorbs the small margin that OpenCASCADE adds to bounding boxes."""
    lo, hi = bbox[:3], bbox[3:]
    for i, a in enumerate(AXES):
        mid = 0.5 * (lo[i] + hi[i])
        if abs(hi[i] - lo[i]) < 2 * tol and any(abs(mid - c) < tol for c in dom[a]):
            return True
    return False


def gmsh_areas(layout: Layout, boundary: str) -> dict:
    """Area (mm^2) of every kind of panel from gmsh's fragments (module docstring, "Checking the
    written geometry without FasterCap").  ``layout`` is the prepared layout."""
    import gmsh
    from .meshing import _add_block, _add_item

    dom = dict(layout.enclosure.spans)
    enc_eps = float(layout.enclosure.material.eps_r)
    acc: dict = defaultdict(float)
    gmsh.initialize(readConfigFiles=False)
    try:
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.model.add("fastercap_check")
        occ = gmsh.model.occ
        inputs = [(ENCLOSURE, _add_block(occ, 3, dom))]
        for k, it in enumerate(layout.items):
            for dt in _add_item(occ, 3, it, dom):
                inputs.append((k, dt))
        _, omap = occ.fragment([dt for _, dt in inputs], [])
        occ.synchronize()
        owner: dict[int, int] = {}
        sheet_of: dict[int, int] = {}
        for (k, dt), pieces in zip(inputs, omap):
            for pd, ptag in pieces:
                if pd == 3 and dt[0] == 3:
                    owner[ptag] = k                    # painter's order: later items overwrite
                elif pd == 2 and dt[0] == 2:
                    sheet_of[ptag] = k                 # a later sheet wins a shared piece
        for _, s in gmsh.model.getEntities(2):
            up, _ = gmsh.model.getAdjacencies(2, s)
            media = [medium_of(layout, owner[int(v)]) for v in up]
            ks = sheet_of.get(s)
            role = layout.items[ks].role if ks is not None else None
            if len(media) == 1:
                if ks is not None:
                    media = media * 2                  # a sheet inside one volume: the same on both sides
                elif _on_enclosure(gmsh.model.getBoundingBox(2, s), dom):
                    media.append(Medium("outside"))
                else:
                    raise ExportError(f"surface {s} bounds one volume but is neither a sheet nor a face "
                                      "of the enclosure")
            elif len(media) != 2:
                raise ExportError(f"surface {s} has {len(media)} adjacent volumes")
            key = classify(media[0], media[1], role, boundary, enc_eps)
            if key is not None:
                acc[key] += float(occ.getMass(2, s))
    finally:
        gmsh.finalize()
    return dict(acc)


def compare_areas(panel_areas: dict, other_areas: dict) -> dict:
    """Per kind of panel: the panels' area, the other route's area and their relative difference."""
    rows = []
    for k in sorted(set(panel_areas) | set(other_areas), key=str):
        a, b = panel_areas.get(k, 0.0), other_areas.get(k, 0.0)
        rows.append(dict(key=list(k), panels=a, other=b, rel=(a - b) / b if b else math.inf))
    tot_abs = sum(abs(r["panels"] - r["other"]) for r in rows)
    tot = sum(r["other"] for r in rows)
    return dict(rows=rows, total_other=tot, total_abs_difference=tot_abs,
                worst=max((abs(r["rel"]) for r in rows), default=0.0))


# ================================================================================================
# Running FasterCap and reading its results
# ================================================================================================
def run_fastercap(exe, lst, options=("-a0.01",), log=None, threads: int = 2, timeout: float | None = None) -> str:
    """Run FasterCap in its batch mode ("-b", help, Run chapter 2) on the list file ``lst`` and return
    what it printed.  It runs at below-normal priority with ``threads`` OpenMP threads, because it is
    meant to run on a workstation that is in use."""
    lst = Path(lst)
    env = dict(os.environ, OMP_NUM_THREADS=str(threads))
    flags = getattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS", 0)
    log = Path(log) if log is not None else lst.with_suffix(".log")
    t0 = time.perf_counter()
    # FasterCap's output goes straight into the log while it runs, so that a long run can be followed.
    with open(log, "w", encoding="utf-8", newline="\n") as f:
        proc = subprocess.Popen([str(exe), "-b", lst.name, *options], cwd=str(lst.parent), env=env,
                                stdout=f, stderr=subprocess.STDOUT, creationflags=flags)
        try:
            code = proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            # FasterCap buffers what it prints, so a killed run may leave an empty log: say why it ended
            f.write(f"\n* run by pcbcap.fastercap: options {' '.join(options)}, stopped at the time limit "
                    f"of {timeout:g} s\n")
            raise
    text = log.read_text(encoding="utf-8", errors="replace")
    with open(log, "a", encoding="utf-8", newline="\n") as f:
        f.write(f"\n* run by pcbcap.fastercap: options {' '.join(options)}, exit code {code}, "
                f"{time.perf_counter() - t0:.1f} s\n")
    if code != 0:
        raise RuntimeError(f"FasterCap exited with code {code}; see {log}")
    return text


_MATRIX = re.compile(r"Capacitance matrix is:\s*\n\s*Dimension\s+(\d+)\s*x\s*(\d+)\s*\n")


def read_matrix(text: str) -> tuple[list[str], np.ndarray]:
    """The last capacitance matrix in FasterCap's output (F), with the group prefixes removed."""
    found = list(_MATRIX.finditer(text))
    if not found:
        raise ValueError("FasterCap's output holds no 'Capacitance matrix is:' block")
    m = found[-1]
    n = int(m.group(1))
    rows = [r for r in text[m.end():].splitlines() if r.strip()][:n]
    names, vals = [], []
    for r in rows:
        parts = r.split()
        names.append(re.sub(r"^g\d+_", "", parts[0]))
        vals.append([float(x) for x in parts[1:n + 1]])
    C = np.array(vals)
    if C.shape != (n, n):
        raise ValueError(f"could not read a {n} x {n} matrix")
    return names, C


def two_port(meta: dict, names: list[str], C: np.ndarray, a: str | None = None, b: str | None = None) -> dict:
    """C_F, C_A0 and C_B0 (fF) from FasterCap's matrix (module docstring, "Reading the results")."""
    a = a or meta["pair"][0]
    b = b or meta["pair"][1]
    conds = meta["conductors"]
    lookup = {k.lower(): k for k in conds}
    nets, floating = [], []
    for nm in names:
        k = lookup.get(nm.lower())
        if k is None:
            raise ValueError(f"FasterCap reports a conductor {nm!r} that the export does not know")
        nets.append(conds[k]["net"])
        floating.append(conds[k]["floating"])
    missing = set(c["net"] for c in conds.values()) - set(nets)
    if missing:
        raise ValueError(f"FasterCap's matrix lacks the conductors {sorted(missing)}")
    scale = float(np.max(np.abs(np.diag(C))))
    asym = float(np.max(np.abs(C - C.T)) / scale)
    ia, ib = nets.index(a), nets.index(b)
    C_AB, C_BA = float(C[ia, ib]), float(C[ib, ia])
    Cs = 0.5 * (C + C.T)
    fl = [i for i, f in enumerate(floating) if f]
    keep = [i for i, f in enumerate(floating) if not f]
    Cr = Cs[np.ix_(keep, keep)]
    if fl:
        Cr = Cr - Cs[np.ix_(keep, fl)] @ np.linalg.solve(Cs[np.ix_(fl, fl)], Cs[np.ix_(fl, keep)])
    kept = [nets[i] for i in keep]

    def drive(va: float, vb: float) -> np.ndarray:
        pot = {net: 0.0 for net in kept}
        pot[a], pot[b] = va, vb
        for f in meta.get("films", []):
            if f["hi"] not in pot or f["lo"] not in pot:
                raise ValueError(f"film {f['name']}: a terminal is floating or missing")
            vh, vl = pot[f["hi"]], pot[f["lo"]]
            for s in f["strips"]:
                pot[s["net"]] = vl + (vh - vl) * s["u"]
        return np.array([pot[net] for net in kept])

    u, v = drive(1.0, 0.0), drive(0.0, 1.0)
    C_F = -float(v @ Cr @ u) * FF_PER_F
    C_A0 = float(u @ Cr @ (u + v)) * FF_PER_F
    C_B0 = float(v @ Cr @ (u + v)) * FF_PER_F
    return dict(C_F=C_F, C_A0=C_A0, C_B0=C_B0, unit="fF", asymmetry=asym,
                C_AB=-C_AB * FF_PER_F, C_BA=-C_BA * FF_PER_F, conductors=len(names), floating=len(fl))


def film_strip_estimate(n: int, width: float, length: float, eps_a: float, eps_b: float, h: float) -> float:
    """The staircase error Delta C_F (fF) of a film cut into n strips (module docstring); lengths in mm."""
    ell = length / n
    return EPS0 * (eps_a + eps_b) * width * math.log(ell / h) / (math.pi * n)


# ================================================================================================
# Looking at the panels
# ================================================================================================
def _clip_polygon(poly: np.ndarray, win) -> np.ndarray | None:
    """Sutherland-Hodgman clipping of a planar polygon to the box ``win``."""
    pts = [p for p in poly]
    for i in range(3):
        for bound, keep_ge in ((win[i][0], True), (win[i][1], False)):
            out = []
            m = len(pts)
            for j in range(m):
                p, q = pts[j], pts[(j + 1) % m]
                ip = p[i] >= bound if keep_ge else p[i] <= bound
                iq = q[i] >= bound if keep_ge else q[i] <= bound
                if ip:
                    out.append(p)
                if ip != iq:
                    t = (bound - p[i]) / (q[i] - p[i])
                    out.append(p + t * (q - p))
            pts = out
            if len(pts) < 3:
                return None
    return np.array(pts)


def draw_panels(ex: Export, stem=None, window=None, views=None, title: str | None = None,
                ncols: int = 3, panel=(2.6, 2.4), z_stretch: float = 1.0, windows=None):
    """Draw the exported panels from several sides (plotting.VIEWS by default), clipped to ``window``
    (plotting.auto_window of the layout by default).  Conductor panels take the colour of their net
    (film strips alternate two shades of the film colour), dielectric interfaces are translucent, and
    every panel's edges are drawn, so the panels themselves can be inspected.  ``z_stretch`` draws the
    z axis enlarged by that factor, for a window much thinner than it is wide (the figure says so).
    ``windows``, if given, holds one window per view in place of ``window``: a closed grounded box
    hides everything inside it, so each view of the whole model needs its own window that stops short
    of the faces between the viewer and the inside."""
    import matplotlib.pyplot as plt
    from matplotlib.colors import to_rgb
    from matplotlib.patches import Patch
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    from . import plotting

    plotting.use_style()
    p = ex.panels
    win = window if window is not None else plotting.auto_window(ex.layout)
    views = views or plotting.VIEWS
    strip_nets = [s["net"] for f in ex.meta.get("films", []) for s in f["strips"]]
    floating = {c["net"]: c["floating"] for c in ex.meta["conductors"].values()}
    diel_pairs = sorted({k[1:] for k in p.key if k[0] == "D"})
    diel_palette = [plotting.COLORS["cool_accent"], "#C9B99A", plotting.COLORS["teal_accent"],
                    plotting.COLORS["brown_accent"], plotting.COLORS["grey_accent"]]
    diel_color = {pr: diel_palette[j % len(diel_palette)] for j, pr in enumerate(diel_pairs)}
    film_light = "#A99BC8"

    def style(k):
        if k[0] == "D":
            return to_rgb(diel_color[k[1:]]), 0.28
        net = k[1]
        if net in strip_nets:
            return to_rgb(plotting.FILM_COLOR if strip_nets.index(net) % 2 == 0 else film_light), 0.95
        return to_rgb(plotting.net_color(net, floating.get(net, False))), 0.9

    def clipped(w):
        """The panels clipped to the window w, and their colours."""
        lo = np.array([a[0] for a in w])
        hi = np.array([a[1] for a in w])
        polys, colors = [], []
        for i in range(len(p.quad)):
            q = p.quad[i]
            if np.any(q.max(axis=0) < lo) or np.any(q.min(axis=0) > hi):
                continue
            poly = _clip_polygon(q, w)
            if poly is None:
                continue
            rgb, al = style(p.key[i])
            polys.append(poly)
            colors.append((*rgb, al))
        return polys, colors

    if windows is not None and len(windows) != len(views):
        raise ValueError("draw_panels: give one window per view")
    view_windows = [tuple(map(tuple, w)) for w in windows] if windows is not None else [tuple(map(tuple, win))] * len(views)
    cache = {w: clipped(w) for w in dict.fromkeys(view_windows)}
    nrows = -(-len(views) // ncols)
    height = panel[1] * nrows + 0.5
    fig = plt.figure(figsize=(panel[0] * ncols, height))
    for j, (label, elev, azim) in enumerate(views):
        win = view_windows[j]
        polys, colors = cache[win]
        ax = fig.add_subplot(nrows, ncols, j + 1, projection="3d")
        ax.add_collection3d(Poly3DCollection(polys, facecolors=colors, edgecolors=(0.15, 0.15, 0.15, 0.7),
                                             linewidths=0.15))
        ax.set_xlim(*win[0])
        ax.set_ylim(*win[1])
        ax.set_zlim(*win[2])
        ax.set_box_aspect([w[1] - w[0] for w in win])
        ax.view_init(elev=elev, azim=azim)
        plotting._tidy_view_axes(ax, elev, azim)
        if z_stretch != 1.0:
            from matplotlib.ticker import MaxNLocator
            ax.set_box_aspect([win[0][1] - win[0][0], win[1][1] - win[1][0],
                               (win[2][1] - win[2][0]) * z_stretch], zoom=0.8)
            if abs(abs(elev) - 90.0) > 1e-9:          # a view from above or below shows no z axis
                ax.zaxis.set_major_locator(MaxNLocator(3, prune="lower"))
            if abs(elev) < 1e-9:                       # side views: keep the axis letter off the ticks
                ax.xaxis.labelpad = 26
                ax.yaxis.labelpad = 26
        ax.text2D(0.0, 1.0, f"({chr(97 + j)}) {label}", transform=ax.transAxes, va="top")
    handles = []
    nets_drawn = sorted({k[1] for k in p.key if k[0] == "C" and k[1] not in strip_nets})
    for net in nets_drawn:
        handles.append(Patch(facecolor=plotting.net_color(net, floating.get(net, False)),
                             label=f"net {net}" + (" (floating)" if floating.get(net) else "")))
    if strip_nets:
        handles.append(Patch(facecolor=plotting.FILM_COLOR, label=f"film strips ({len(strip_nets)})"))
    for pr in diel_pairs:
        handles.append(Patch(facecolor=diel_color[pr], alpha=0.5, label=f"interface {pr[0]:g} | {pr[1]:g}"))
    fig.legend(handles=handles, loc="lower center", ncol=min(len(handles), 6), bbox_to_anchor=(0.5, 0.0))
    # Margins in inches, so that the note stays clear of the legend on a figure of any height; they are the
    # fractions 0.10, 0.92, 0.97 and 0.045 of the default sheet of six views (5.3 in tall), which they
    # reproduce exactly.
    fig.subplots_adjust(left=0.0, right=0.98, bottom=0.53 / height,
                        top=1.0 - (0.424 if title else 0.159) / height, wspace=0.2, hspace=0.15)
    note = "Lengths in mm. Every outlined rectangle is one input panel of FasterCap."
    if z_stretch != 1.0:
        note += f" The z axis is drawn {z_stretch:g} times enlarged."
    fig.text(0.01, 0.2385 / height, note, ha="left", va="bottom")
    if title:
        fig.suptitle(title)
    if stem is not None:
        plotting.export(fig, stem)
        return None
    return fig
