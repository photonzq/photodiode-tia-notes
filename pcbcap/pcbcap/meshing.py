"""Turning a Layout into a labelled finite-element mesh with gmsh.

Why this module exists
----------------------
The finite-element method (``fem.py``) needs the region of space divided into simple elements
(tetrahedra in 3-D, triangles in 2-D) such that
  (1) every element lies in exactly one material or one conductor, so that the permittivity is
      constant on it and the integrals over it are exact for polynomials;
  (2) every zero-thickness conductor or film is made of element faces (edges in 2-D), so that its
      prescribed potential can be imposed on the degrees of freedom that lie on it;
  (3) the elements are small where the field changes fast and large where it is smooth.
This module builds such a mesh from a ``Layout`` with the gmsh library [Geuzaine and Remacle 2009]
and returns plain arrays: node coordinates, element connectivity, the layout item that owns each
element, and the element faces that make up each sheet.

How (1) and (2) are achieved: the "fragment" operation
------------------------------------------------------
Every box, rectangle, sheet and segment of the layout (after clipping to the computational domain,
see below) is created as a separate entity of gmsh's OpenCASCADE geometry kernel, together with the
enclosure.  gmsh's ``fragment`` then splits all of them along each other's boundaries so that the
result is a set of non-overlapping pieces that share their common faces.  For every input entity
it reports which output pieces it covers.  A piece covered by several overlapping boxes is given to
the one added last (the painter's order documented in ``geometry.py``); the enclosure is first, so
any piece not covered by an item is enclosure medium.  A sheet's pieces become internal faces of the
mesh, so after meshing they consist of element faces, as (2) requires.  Because the pieces share
faces, the mesh is conforming: neighbouring elements meet face to face, which the continuous
(H^1-conforming) finite elements of ``fem.py`` require.

How (3) is achieved: element size fields
----------------------------------------
Near an edge of a conductor or film the potential varies as rho^nu with the distance rho from the
edge, with nu between about 0.37 and 2/3 for the edges in these layouts (fem.py, Step 2; study.py
derives the exponents), so the field grows as rho^(nu - 1) and most of the error of a coarse mesh
comes from there.  The mesh is therefore graded: the target element size is
    h(d) = h_edge                                           for d <= d0,
    h(d) = h_edge + (h_far - h_edge) * (d - d0)/(d1 - d0)    for d0 < d < d1,
    h(d) = h_far                                            for d >= d1,
where d is the distance to the nearest conductor or film edge (3-D) or corner (2-D).  This is
gmsh's "Threshold" field applied to a "Distance" field.  With d0 = h_edge and
d1 - d0 = (h_far - h_edge)/grading, the size grows by ``grading`` (g, 0.3 by default) per unit distance:
h(d) = h_edge + g (d - h_edge).  An element of size h at distance d therefore has a neighbour, at
distance d + h, of size h + g h = (1 + g) h: neighbouring sizes differ by at most the factor 1 + g =
1.3, which keeps the elements well shaped.  The value 0.3 is a choice; it also sets the constant of
the discretisation error in the graded zone (study.py), so a smaller g would cost more elements
for a smaller error at every level, while the convergence order stays the same.  A second field caps
the size at h_core inside a box around the components (the "core"), where the field varies on the
scale of the components even away from edges; the smaller of the two fields applies everywhere.

Which lines count as edges.  Only physical edges of conductors and films.  A line where a part is
cut by a mirror plane, or where a grounded sheet meets the grounded enclosure, is an edge of the
computed piece but not of the conductor, and the field is not singular there, so such lines are left
out (``_on_inert_boundary``).  The same holds on an "open" face: it is a plane of even reflection, a
part that meets it at a right angle continues in its mirror image, and the line where it meets the
face is no physical edge either (only a sheet lying in the face plane has edges there).  Such lines
are at present still refined; that costs elements but not accuracy.  Corners of dielectrics
carry singular fields too (a right-angled alumina corner in air has nu = 0.73), but weaker ones than
the conductor edges, so they are left to the core size; their error falls with the order
2 nu = 1.47, faster than that of the conductor edges, and does not set the order of a study.

How the distance is measured.  gmsh's Distance field computes the distance to points sampled along
each curve ("Sampling" points per curve), not to the curve itself.  Between two samples, a point on
the curve is up to half the sample spacing, l / (2 (S - 1)) for a curve of length l and S samples,
from the nearest sample, and the field reports that distance instead of zero.  That does no harm as
long as it stays below d0 = h_edge, where the target size is flat; beyond it the size at the curve
would grow by g times the excess, by an amount that does not scale with ``refine``.  _size_fields
therefore sets S >= l_max / (2 h) + 1 for each group of curves of edge size h, with l_max the
longest curve of the group.  (Before this rule a fixed S = 40 was used; it under-refined curves
longer than 78 h, for example 1-mm edges at h = 7.5 um by up to 21 % in size.)

A single ``refine`` factor multiplies h_edge, h_core, h_far and the items' own edge sizes; the
slope ``grading`` is not multiplied, and the edge size is capped at the thinnest feature.  The
consequences for a convergence study are worked out in ``study.py``.

Symmetry clipping
-----------------
If the layout declares mirror symmetry (``Layout.set_symmetry``), the computational domain is the
part of the enclosure with x >= 0 (and/or y >= 0).  Every item is clipped to that part before it is
created.  ``capacitance.py`` explains which boundary condition the cut plane receives and why the
full-domain result follows exactly.
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass, field, replace

import numpy as np

from .geometry import Box, Conductor, Dielectric, Film, Interval, Layout, Rect, Segment, Sheet


# ================================================================================================
@dataclass
class MeshParams:
    """Element-size controls (all in mm).  ``None`` means "choose a default from the layout".

    h_edge  : size at conductor and film edges.  The error from the edge zone falls as h_edge^(2 nu)
              (study.py), i.e. roughly in proportion to h_edge.  In 2-D, where an edge is a point,
              halving h_edge adds only ln 2 / ln(1 + grading) = 2.6 rings of elements around it (the
              rings grow by the factor 1 + grading), so a very small edge size is cheap: the 2-D default
              is the smallest feature / 1000, for which coplanar strips came out 1.0e-4 above their
              exact value (feature / 400 gave 3e-4) in the checks.  In 3-D the number of elements
              along an edge also grows as 1/h_edge, so the edge size is costly; the 3-D default is the
              smallest feature / 4.  That makes refine = 4, the coarsest level used in the studies,
              exactly the level at which the edge size reaches the thinnest feature (its cap,
              resolve_params), so levels refine 1 to 4 all refine uniformly.
    h_core  : largest size inside the core box.  It resolves the field between the components, which
              varies on the scale of the components themselves (the thin features are taken care of
              by h_edge), so the default is a fraction of the largest extent of the signal conductors
              (Layout.core_bounding_box): 1/60 of it in 2-D, 1/15 in 3-D.  These fractions are choices
              that balance cost; h_core scales with refine, so its effect is part of what a
              convergence study measures and extrapolates.  (Tying it to the smallest feature instead
              would ask, for a 15-um termination, for micrometre elements over millimetres of board.)
    max_elements : protects a shared machine from an accidental multi-gigabyte mesh.  build_mesh
              refuses to mesh when the core box alone would need more elements (_bulk_count, an
              approximate lower bound), and refuses the mesh when the count actually meshed is
              larger, before any assembly memory is spent.
              Defaults 1.5e6 (3-D) and 2e6 (2-D).  The 3-D value follows from measured memory: the
              OPA846 cases, 0.85-0.99 million tetrahedra (1.1-1.3 million P2 unknowns), took about
              3.5-4.5 GB per solve, so 1.5 million tetrahedra is about 6 GB, the most a shared
              workstation should give one solve.  A 2-D element costs far less; 2e6 is a choice.
    h_far   : largest size anywhere.  Default: one twelfth of the largest enclosure dimension, a
              choice: far from the layout the field is smooth and varies on the scale of the
              distance itself, and h_far scales with refine like the other sizes.
    grading : growth of the size per unit distance from an edge (dimensionless), 0.3 by default;
              see the module docstring.
    core_margin : the core box is the bounding box of the signal conductors and films
              (Layout.core_bounding_box: every net but ground) grown by this margin.  Default:
              1.5 * (its largest dimension) capped at 2 mm.  A choice: the field between the nets
              decays with distance from them on the scale of their own extent, so a margin of 1.5
              extents keeps the region of strong field inside the box; the cap keeps a large layout
              from asking for h_core over a large volume.  The margin does not scale with refine.
    refine  : factor applied to h_edge, h_core, h_far and the items' own edge sizes (mesh_size).
    algorithm : gmsh algorithm number (2-D default 6 "Frontal-Delaunay", 3-D default 1 "Delaunay").
    """

    h_edge: float | None = None
    h_core: float | None = None
    h_far: float | None = None
    grading: float = 0.3
    core_margin: float | None = None
    refine: float = 1.0
    algorithm: int | None = None
    optimize: bool = True
    threads: int = 2
    save_msh: str | None = None
    verbose: bool = False
    max_elements: float | None = None
    scale: float = 1.0      # set by resolve_params: the refine factor applied (scales per-item sizes)


@dataclass
class MeshData:
    """A labelled mesh, independent of gmsh.

    p      : (dim, N) node coordinates; rows are the layout's axes ((x, y, z) or (x, z)).
    t      : (dim + 1, M) node indices of each element.
    owner  : (M,) index into ``layout.items`` of the item that fills each element, or -1 for the
             enclosure medium.
    facets : {item index: (dim, k) node indices of the element faces (edges in 2-D) that make up that
             sheet or segment}.
    domain : the computational box after symmetry clipping.
    clipped: {axis: True if the domain was cut at axis = 0 by a mirror symmetry}.
    """

    dim: int
    axes: tuple[str, ...]
    p: np.ndarray
    t: np.ndarray
    owner: np.ndarray
    facets: dict[int, np.ndarray]
    domain: dict[str, Interval]
    clipped: dict[str, bool]
    params: MeshParams
    stats: dict = field(default_factory=dict)


# ================================================================================================
def computational_domain(layout: Layout) -> tuple[dict[str, Interval], dict[str, bool]]:
    """The enclosure, cut at x = 0 and/or y = 0 when the layout is mirror symmetric.

    The cut requires the enclosure itself to be symmetric about that plane; otherwise the clipped
    domain would not be exactly half of the full one."""
    if layout.enclosure is None:
        raise ValueError("the layout needs an enclosure (Layout.set_enclosure)")
    dom = dict(layout.enclosure.spans)
    clipped = {a: False for a in layout.axes}
    for axis, active in (("x", layout.mirror_x), ("y", layout.mirror_y)):
        if not active:
            continue
        lo, hi = dom[axis]
        if abs(lo + hi) > 1e-9 * max(1.0, abs(lo), abs(hi)):
            raise ValueError(f"mirror symmetry in {axis} needs an enclosure symmetric about {axis} = 0")
        dom[axis] = (0.0, hi)
        clipped[axis] = True
    return dom, clipped


def _clip(iv: Interval, dom: Interval) -> Interval | None:
    """Intersection of two intervals; None when empty or of zero length."""
    a, b = max(iv[0], dom[0]), min(iv[1], dom[1])
    return (a, b) if b > a else None


def resolve_params(layout: Layout, params: MeshParams) -> MeshParams:
    """Fill in the defaults documented in ``MeshParams`` and apply ``refine``."""
    feat = layout.smallest_feature()
    enc = layout.enclosure.spans
    big = max(v - u for u, v in enc.values())
    two_d = layout.dim == 2
    cbb = layout.core_bounding_box()
    size = max(v - u for u, v in cbb.values())          # largest extent of the conductors
    h_edge = params.h_edge if params.h_edge is not None else (feat / 1000.0 if two_d else feat / 4.0)
    h_core = params.h_core if params.h_core is not None else (size / 60.0 if two_d else size / 15.0)
    h_far = params.h_far if params.h_far is not None else big / 12.0
    margin = params.core_margin if params.core_margin is not None else min(1.5 * size, 2.0)
    r = params.refine
    max_el = params.max_elements if params.max_elements is not None else (2e6 if two_d else 1.5e6)
    # The edge size never exceeds the thinnest feature: elements larger than a 15-um termination
    # or a 30-um stand-off cannot fill it without slivers, flat tetrahedra with angles close to 180
    # degrees.  Such elements violate the maximum-angle condition under which the interpolation error
    # is bounded (I. Babuska and A. K. Aziz, SIAM J. Numer. Anal. 13, 214 (1976), for triangles;
    # M. Krizek, SIAM J. Numer. Anal. 29, 513 (1992), for tetrahedra).  What was observed here is only
    # the cost: in a trial, one run of the OPA855 network with 21-um edge elements took 54 min in
    # total, against 1.5 min with 15-um ones; which step was slow was not isolated.
    h_edge_r = min(h_edge * r, feat)
    return replace(params, h_edge=h_edge_r, h_core=max(h_core * r, h_edge_r), h_far=h_far * r,
                   core_margin=margin, refine=1.0, max_elements=max_el, scale=r)


def estimate_elements(layout: Layout, rp: MeshParams, dom: dict[str, Interval]) -> float:
    """Rough a-priori number of elements, for planning runs without building any geometry.

    It counts every edge of every conductor, including lines that mesh generation later leaves
    unrefined (mirror planes, grounded walls), so it over-estimates layouts with large sheets.
    ``build_mesh`` itself checks the more accurate ``_estimate_from_model`` instead.

    The counts are those of _estimate_from_model (see its docstring for the derivation), with the
    feature lengths replaced by a bound: in 2-D, 4 corners per conductor item; in 3-D, 4 times the
    sum of each conductor item's extents, i.e. the 12 edges of a box counted as 4 of each length."""
    cbb = layout.core_bounding_box()
    m = rp.core_margin
    meas = 1.0
    for a in layout.axes:
        lo, hi = max(cbb[a][0] - m, dom[a][0]), min(cbb[a][1] + m, dom[a][1])
        meas *= max(hi - lo, 0.0)
    bulk = _PER_CELL[layout.dim] * meas / rp.h_core ** layout.dim
    n_feat = sum(1 for it in layout.items if not isinstance(it.role, Dielectric))
    if layout.dim == 2:
        edges = 4 * n_feat * _corner_count(rp.h_edge, rp.h_core, rp.grading)
    else:
        length = sum(4 * sum(v - u for u, v in layout.item_extent(it).values())
                     for it in layout.items if not isinstance(it.role, Dielectric))
        edges = length * _edge_count_per_length(rp.h_edge, rp.h_core, rp.grading)
    return bulk + edges


# Simplices per unit measure at target size h (the size gmsh aims at is the edge length): a regular
# triangle of side h has area (sqrt(3)/4) h^2, so about 4/sqrt(3) = 2.31 of them fit in h^2; a regular
# tetrahedron of edge h has volume h^3 / (6 sqrt(2)), so about 6 sqrt(2) = 8.49 of them fit in h^3.
_PER_CELL = {2: 4.0 / math.sqrt(3.0), 3: 6.0 * math.sqrt(2.0)}


def _corner_count(h_e: float, h_c: float, g: float) -> float:
    """Elements in the graded zone around a 2-D corner (derivation in _estimate_from_model)."""
    h_c = max(h_c, h_e)
    return _PER_CELL[2] * (2 * math.pi / g ** 2) * (math.log(h_c / h_e) - 1.0 + h_e / h_c)


def _edge_count_per_length(h_e: float, h_c: float, g: float) -> float:
    """Elements per unit length in the graded zone around a 3-D edge (derivation in
    _estimate_from_model)."""
    h_c = max(h_c, h_e)
    return _PER_CELL[3] * (math.pi / g ** 2) * (h_c - h_e) ** 2 / (h_e * h_c ** 2)


# ================================================================================================
def build_mesh(layout: Layout, params: MeshParams | None = None, estimate_only: bool = False):
    """Mesh ``layout`` and return a ``MeshData`` (see the module docstring for the method).

    With ``estimate_only`` the geometry is built and fragmented but not meshed, and the estimated
    number of elements (``_estimate_from_model``) is returned instead: a quick way to size a run."""
    import gmsh  # imported here so that the rest of the package can be used without gmsh

    params = params or MeshParams()
    if layout.mirror_x or layout.mirror_y:
        layout.check_symmetry()
    dom, clipped = computational_domain(layout)
    rp = resolve_params(layout, params)
    dim = layout.dim
    axes = layout.axes
    t0 = time.perf_counter()

    gmsh.initialize(readConfigFiles=False)
    try:
        gmsh.option.setNumber("General.Terminal", 1 if params.verbose else 0)
        gmsh.option.setNumber("General.NumThreads", max(1, int(params.threads)))
        gmsh.model.add(layout.name or "layout")
        occ = gmsh.model.occ

        # -- 1. create the enclosure and every (clipped) item as OCC entities --------------------
        inputs: list[tuple[int, tuple[int, int]]] = []  # (item index or -1, (dim, tag))
        inputs.append((-1, _add_block(occ, dim, dom)))
        for k, it in enumerate(layout.items):
            for dt in _add_item(occ, dim, it, dom):
                inputs.append((k, dt))

        # -- 2. fragment: split everything into non-overlapping, face-sharing pieces ------------
        out, omap = occ.fragment([dt for _, dt in inputs], [])
        occ.synchronize()

        # -- 3. ownership: later items win for volumes; sheets keep their own pieces ------------
        owner_of_piece: dict[int, int] = {}       # top-dimensional piece tag -> item index (-1 = enclosure)
        sheet_pieces: dict[int, set[int]] = {}    # item index -> lower-dimensional piece tags
        for (k, dt), pieces in zip(inputs, omap):
            for (pd, ptag) in pieces:
                if pd == dim:
                    if dt[0] == dim:
                        owner_of_piece[ptag] = k   # inputs are in painter's order: overwrite
                elif pd == dim - 1 and dt[0] == dim - 1:
                    sheet_pieces.setdefault(k, set()).add(ptag)
        # A lower-dimensional piece claimed by two sheets goes to the later one.
        seen: dict[int, int] = {}
        for k in sorted(sheet_pieces):
            for ptag in sheet_pieces[k]:
                seen[ptag] = k
        sheet_pieces = {}
        for ptag, k in seen.items():
            sheet_pieces.setdefault(k, set()).add(ptag)

        # Physical groups: not needed by the solver, but they make an exported .msh readable.
        by_owner: dict[int, list[int]] = {}
        for ptag, k in owner_of_piece.items():
            by_owner.setdefault(k, []).append(ptag)
        for k, tags in by_owner.items():
            nm = "enclosure" if k < 0 else f"{k}:{layout.items[k].name or type(layout.items[k]).__name__}"
            gmsh.model.addPhysicalGroup(dim, sorted(tags), name=nm)
        for k, tags in sheet_pieces.items():
            gmsh.model.addPhysicalGroup(dim - 1, sorted(tags), name=f"{k}:{layout.items[k].name or 'sheet'}")

        # -- 4. element-size fields, and a check that the mesh will fit -------------------------
        feature_tags = _feature_entities(gmsh, layout, dim, owner_of_piece, sheet_pieces, dom, clipped, rp)
        est = _estimate_from_model(gmsh, layout, rp, feature_tags, dim, dom)
        if estimate_only:
            return est
        # Two guards against a mesh too large for memory.  Before meshing, the bulk count alone (the
        # core box filled at h_core, an approximate lower bound of the final count) must not exceed
        # max_elements: if it does, the mesh is certainly too large.  The full estimate is not used
        # for this, because it over-counts compact layouts (_estimate_from_model).  After meshing,
        # the actual count is checked (below), before any assembly memory is spent.
        lower = _bulk_count(layout, rp, dom, dim)
        if lower > rp.max_elements:
            raise ValueError(f"the core box alone needs about {lower:.3g} elements, above max_elements = "
                             f"{rp.max_elements:.3g} (h_core {rp.h_core:.3g} mm); coarsen the mesh or raise "
                             "max_elements deliberately")
        _size_fields(gmsh, layout, dim, rp, feature_tags, dom)

        # -- 5. mesh -----------------------------------------------------------------------------
        alg = rp.algorithm if rp.algorithm is not None else (6 if dim == 2 else 1)
        if dim == 2:
            gmsh.option.setNumber("Mesh.Algorithm", alg)
        else:
            gmsh.option.setNumber("Mesh.Algorithm3D", alg)
        gmsh.option.setNumber("Mesh.Optimize", 1 if rp.optimize else 0)
        gmsh.model.mesh.generate(dim)
        _, elem_tags, _ = gmsh.model.mesh.getElements(dim)
        n_meshed = sum(len(t) for t in elem_tags)
        if n_meshed > rp.max_elements:
            raise ValueError(f"the mesh has {n_meshed} elements, above max_elements = {rp.max_elements:.3g}; "
                             "coarsen the mesh or raise max_elements deliberately")
        if rp.save_msh:
            gmsh.write(rp.save_msh)

        # -- 6. extract arrays ----------------------------------------------------------------------
        md = _extract(gmsh, layout, dim, axes, owner_of_piece, sheet_pieces, dom, clipped, rp)
    finally:
        gmsh.finalize()
    md.stats["mesh_seconds"] = time.perf_counter() - t0
    md.stats["estimated_elements"] = est
    return md


# ------------------------------------------------------------------------------------------------
def _add_block(occ, dim: int, spans: dict[str, Interval]) -> tuple[int, int]:
    """A box (3-D) or a rectangle in the gmsh (x, y) plane standing for (x, z) (2-D)."""
    if dim == 3:
        (x0, x1), (y0, y1), (z0, z1) = spans["x"], spans["y"], spans["z"]
        return (3, occ.addBox(x0, y0, z0, x1 - x0, y1 - y0, z1 - z0))
    (x0, x1), (z0, z1) = spans["x"], spans["z"]
    return (2, occ.addRectangle(x0, z0, 0.0, x1 - x0, z1 - z0))


def _rect_surface(occ, normal: str, at: float, spans: dict[str, Interval]) -> int:
    """A planar rectangle normal to ``normal`` at coordinate ``at``, built from its four corners
    (gmsh's addRectangle only makes rectangles normal to z)."""
    a, b = [ax for ax in ("x", "y", "z") if ax != normal]
    (a0, a1), (b0, b1) = spans[a], spans[b]

    def pt(u, v):
        c = {normal: at, a: u, b: v}
        return occ.addPoint(c["x"], c["y"], c["z"])

    p = [pt(a0, b0), pt(a1, b0), pt(a1, b1), pt(a0, b1)]
    lines = [occ.addLine(p[i], p[(i + 1) % 4]) for i in range(4)]
    loop = occ.addCurveLoop(lines)
    return occ.addPlaneSurface([loop])


def _add_item(occ, dim: int, it, dom: dict[str, Interval]) -> list[tuple[int, int]]:
    """Create the part of item ``it`` that lies inside the computational domain.

    Returns the list of (dim, tag) entities created (empty when the item lies outside the domain,
    as the mirror half of a symmetric part does)."""
    if isinstance(it, (Box, Rect)):
        spans = {a: _clip(v, dom[a]) for a, v in it.spans.items()}
        if any(v is None for v in spans.values()):
            return []
        return [_add_block(occ, dim, spans)]
    if isinstance(it, Sheet):
        if not (dom[it.normal][0] <= it.at <= dom[it.normal][1]):
            return []
        spans = {a: _clip(v, dom[a]) for a, v in it.spans.items()}
        if any(v is None for v in spans.values()):
            return []
        s = _rect_surface(occ, it.normal, it.at, spans)
        tags = [(2, s)]
        for h in it.holes:
            hs = {a: _clip(v, spans[a]) for a, v in h.items()}
            if any(v is None for v in hs.values()):
                continue
            hole = _rect_surface(occ, it.normal, it.at, hs)
            tags, _ = occ.cut(tags, [(2, hole)], removeObject=True, removeTool=True)
        return list(tags)
    if isinstance(it, Segment):
        if not (dom[it.normal][0] <= it.at <= dom[it.normal][1]):
            return []
        span = _clip(it.span, dom[it.along])
        if span is None:
            return []
        if it.normal == "z":   # horizontal: varies in x at height z = at; gmsh (x, y) = (x, z)
            p0, p1 = occ.addPoint(span[0], it.at, 0.0), occ.addPoint(span[1], it.at, 0.0)
        else:                  # vertical: x = at, varies in z
            p0, p1 = occ.addPoint(it.at, span[0], 0.0), occ.addPoint(it.at, span[1], 0.0)
        return [(1, occ.addLine(p0, p1))]
    raise TypeError(type(it))


def _feature_entities(gmsh, layout: Layout, dim: int, owner_of_piece, sheet_pieces, dom, clipped,
                      rp: MeshParams) -> dict[float, list[int]]:
    """The entities near which the mesh is refined, grouped by their edge size: in 3-D the edges
    (curves) of every conductor and film piece, in 2-D their corners (points).  These are where the
    field is singular (see the module docstring).

    An item may set its own edge size (``mesh_size``, scaled by the same refine factor as h_edge), for
    example a ground plane far from the parts, whose cut-out edge does not need the resolution of a
    resistor's termination.  A curve shared by items of different sizes takes the smallest."""
    want = dim - 2  # curves (1) in 3-D, points (0) in 2-D
    size_of: dict[int, float] = {}

    def size_for(k: int) -> float:
        # An item's own size is scaled by the same refine factor as h_edge.  It may not fall below
        # half the layout's edge size, the same floor as gmsh's global Mesh.MeshSizeMin set in
        # _size_fields; a smaller value could not be honoured anyway.
        ms = layout.items[k].mesh_size
        return rp.h_edge if ms is None else max(ms * rp.scale, 0.5 * rp.h_edge)

    def claim(tags, h):
        for t in tags:
            size_of[t] = min(size_of.get(t, math.inf), h)

    def boundary_down(dimtags):
        cur = list(dimtags)
        while cur and cur[0][0] > want:
            cur = gmsh.model.getBoundary(cur, combined=False, oriented=False, recursive=False)
            cur = list({(d, abs(t)) for d, t in cur})
        return cur

    for ptag, k in owner_of_piece.items():
        if k >= 0 and isinstance(layout.items[k].role, Conductor):
            claim([t for _, t in boundary_down([(dim, ptag)])], size_for(k))
    for k, tags in sheet_pieces.items():
        claim([t for _, t in boundary_down([(dim - 1, t) for t in tags])], size_for(k))
    # Leave out curves (points) that lie in a plane where the field has no edge singularity:
    #  * a mirror-symmetry plane: a part cut by it continues on the other side, so the cut line is
    #    not an edge of the physical conductor;
    #  * a grounded enclosure face: there the potential is prescribed (0) on both the wall and a
    #    grounded sheet that meets it, so nothing is singular.
    # Curves on an "open" (insulating) face are kept.  They are not singular either: an open face is a
    # plane of even reflection, and a part meeting it at a right angle continues in its mirror image.
    # Refining there costs elements but not accuracy; it is left as it is because the recorded checks
    # were computed with it.  (Only a sheet lying in an open face would have true edges in it.)
    groups: dict[float, list[int]] = {}
    for t, h in size_of.items():
        if not _on_inert_boundary(gmsh, want, t, layout, dom, clipped):
            groups.setdefault(h, []).append(t)
    return {h: sorted(v) for h, v in groups.items()}


def _on_inert_boundary(gmsh, edim: int, tag: int, layout: Layout, dom, clipped) -> bool:
    """True when entity (edim, tag) lies entirely in a mirror plane or a grounded enclosure face."""
    xmin, ymin, zmin, xmax, ymax, zmax = gmsh.model.getBoundingBox(edim, tag)
    if layout.dim == 3:
        lo, hi = {"x": xmin, "y": ymin, "z": zmin}, {"x": xmax, "y": ymax, "z": zmax}
    else:                                   # gmsh (x, y) stands for the layout's (x, z)
        lo, hi = {"x": xmin, "z": ymin}, {"x": xmax, "z": ymax}
    scale = max(v - u for u, v in dom.values())
    # OCC enlarges bounding boxes by its absolute geometric tolerance (1e-7 in model units by
    # default, i.e. 1e-7 mm), so a curve lying exactly in a face reports a box up to that far from it.
    # 1e-7 of the domain size (1.6e-6 to 7e-6 mm here) is above that margin and far below the distance
    # between any face and a curve that does not lie in it (at least the thinnest feature, 10 um).
    tol = 1e-7 * scale
    for a in layout.axes:
        for side, val in (("min", dom[a][0]), ("max", dom[a][1])):
            if abs(lo[a] - val) < tol and abs(hi[a] - val) < tol:
                if side == "min" and clipped.get(a, False):
                    return True
                if layout.enclosure.face_condition(a + side) == "ground":
                    return True
    return False


def _bulk_count(layout: Layout, rp: MeshParams, dom, dim: int) -> float:
    """Elements needed to fill the core box at size h_core: _PER_CELL * measure / h_core^dim.

    It is an approximate lower bound of the final count.  The mesh fills the box with elements no
    larger than about h_core, and a regular simplex has the largest measure among simplices of
    edge length up to h, so no fewer than about measure / (h_core^dim / _PER_CELL) of them fit.
    "About", because gmsh treats the size as a target, not a strict maximum."""
    cbb = layout.core_bounding_box()
    m = rp.core_margin
    meas = 1.0
    for a in layout.axes:
        lo, hi = max(cbb[a][0] - m, dom[a][0]), min(cbb[a][1] + m, dom[a][1])
        meas *= max(hi - lo, 0.0)
    return _PER_CELL[dim] * meas / rp.h_core ** dim


def _estimate_from_model(gmsh, layout: Layout, rp: MeshParams, feature_tags, dim: int, dom) -> float:
    """Number of elements to expect, computed from the actual geometry before meshing.

    Derivation.  A region meshed at target size h holds about _PER_CELL[dim] / h^dim simplices per
    unit measure (regular simplices, see _PER_CELL).
      * Bulk: inside the core box the size is at most h_core, so the box holds about
        _PER_CELL * measure / h_core^dim elements.
      * Around a feature the size is h(d) = h_e + g d (g = grading) out to the distance where it
        reaches h_core, d_max = (h_c - h_e)/g.  Substituting u = h_e + g d (so d = (u - h_e)/g and
        dd = du/g):
          2-D, around a corner, counting rings of circumference 2 pi d:
            int_0^d_max 2 pi d / h(d)^2 dd = (2 pi / g^2) int_h_e^h_c (u - h_e)/u^2 du
                                           = (2 pi / g^2) [ln(h_c/h_e) - 1 + h_e/h_c];
          3-D, per unit length of an edge, counting cylindrical shells of area 2 pi d per length:
            int_0^d_max 2 pi d / h(d)^3 dd = (2 pi / g^2) int_h_e^h_c (u - h_e)/u^3 du
                                           = (2 pi / g^2) [1/(2 h_e) - 1/h_c + h_e/(2 h_c^2)]
                                           = (pi / g^2) (h_c - h_e)^2 / (h_e h_c^2),
        each multiplied by _PER_CELL.  The 3-D count grows as 1/h_e and has no logarithm.
    Curve lengths are the actual lengths of the feature curves (occ.getMass).  What the estimate
    leaves out, and in which direction: graded zones of nearby edges overlap (for example the two
    edges of a 35-um copper pad), and summing them counts the overlap twice (too high); the zone is
    counted again inside the core box's bulk (too high); the transition from h_core to h_far outside the
    core box is not counted (too low).  It is a guard against a mesh that would not fit in memory, not
    a prediction.  (A first version used 6 tetrahedra per cell and a 3-D count of (l/h_e) times a
    logarithm / 4; for the OPA846 cases it gave 0.43-0.60 million against 0.85-0.99 million tetrahedra
    meshed.)  The estimate is stored with the mesh statistics so that it can be compared with the
    count actually meshed."""
    total = _bulk_count(layout, rp, dom, dim)
    for h, tags in feature_tags.items():
        if dim == 2:
            total += len(tags) * _corner_count(h, rp.h_core, rp.grading)
        else:
            total += sum(gmsh.model.occ.getMass(1, t) for t in tags) * _edge_count_per_length(h, rp.h_core, rp.grading)
    return total


def _size_fields(gmsh, layout: Layout, dim: int, rp: MeshParams, feature_tags, dom) -> None:
    """Set the background size field: min(threshold on the distance to features, core box)."""
    f = gmsh.model.mesh.field
    fields = []
    fid = 0
    for h, tags in feature_tags.items():
        # one graded field per edge size: h at the features, growing by `grading` per unit distance
        fid += 1
        f.add("Distance", fid)
        f.setNumbers(fid, "CurvesList" if dim == 3 else "PointsList", tags)
        if dim == 3:
            # Samples per curve (module docstring, "How the distance is measured"): the largest gap
            # between a point of a curve and its nearest sample, l / (2 (S - 1)), must stay below h,
            # where the target size is still flat.  With l_max the longest curve of this group,
            # S = ceil(l_max / (2 h)) + 2 satisfies l_max / (2 (S - 1)) < h.  At least 40, the earlier
            # fixed value, is kept for short curves.
            l_max = max(gmsh.model.occ.getMass(1, t) for t in tags)
            f.setNumber(fid, "Sampling", max(40, int(math.ceil(l_max / (2.0 * h))) + 2))
        fid += 1
        f.add("Threshold", fid)
        f.setNumber(fid, "InField", fid - 1)
        f.setNumber(fid, "SizeMin", h)
        f.setNumber(fid, "SizeMax", rp.h_far)
        d0 = h                                       # keep the smallest size within one element
        d1 = d0 + (rp.h_far - h) / rp.grading        # growth limited to `grading` per unit length
        f.setNumber(fid, "DistMin", d0)
        f.setNumber(fid, "DistMax", d1)
        fields.append(fid)
    # Core box: h_core inside, h_far outside, with a transition layer as wide as the growth needs.
    cbb = layout.core_bounding_box()
    m = rp.core_margin
    fid += 1
    f.add("Box", fid)
    names = ("X", "Y", "Z") if dim == 3 else ("X", "Y")
    for nm, a in zip(names, layout.axes):
        lo = max(cbb[a][0] - m, dom[a][0])
        hi = min(cbb[a][1] + m, dom[a][1])
        f.setNumber(fid, f"{nm}Min", lo)
        f.setNumber(fid, f"{nm}Max", hi)
    f.setNumber(fid, "VIn", rp.h_core)
    f.setNumber(fid, "VOut", rp.h_far)
    f.setNumber(fid, "Thickness", (rp.h_far - rp.h_core) / rp.grading)
    fields.append(fid)
    fid += 1
    f.add("Min", fid)
    f.setNumbers(fid, "FieldsList", fields)
    f.setAsBackgroundMesh(fid)
    # Use only the background field: sizes inherited from points, boundaries or curvature would
    # override the documented grading.
    gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
    # Global bounds on the size: the mesher may go down to half the edge size where its algorithm
    # needs smaller elements to close the mesh around a corner (a choice that leaves it room without
    # letting it refine without limit), and never above the far size.
    gmsh.option.setNumber("Mesh.MeshSizeMin", 0.5 * rp.h_edge)
    gmsh.option.setNumber("Mesh.MeshSizeMax", rp.h_far)


def _extract(gmsh, layout, dim, axes, owner_of_piece, sheet_pieces, dom, clipped, rp) -> MeshData:
    """Read nodes and elements back from gmsh into contiguous NumPy arrays."""
    tags, coords, _ = gmsh.model.mesh.getNodes()
    coords = coords.reshape(-1, 3)
    # gmsh node tags need not be contiguous; map tag -> row index.
    index = np.full(int(tags.max()) + 1, -1, dtype=np.int64)
    index[tags.astype(np.int64)] = np.arange(len(tags))
    elem_type = 4 if dim == 3 else 2          # 4-node tetrahedron / 3-node triangle
    face_type = 2 if dim == 3 else 1          # 3-node triangle / 2-node line
    nper = dim + 1

    t_list, own_list = [], []
    for ptag, k in owner_of_piece.items():
        etypes, _, enodes = gmsh.model.mesh.getElements(dim, ptag)
        for et, en in zip(etypes, enodes):
            if et != elem_type:
                raise RuntimeError(f"unexpected element type {et} (only linear simplices are used)")
            conn = index[en.astype(np.int64)].reshape(-1, nper)
            t_list.append(conn)
            own_list.append(np.full(len(conn), k, dtype=np.int64))
    t = np.vstack(t_list).T
    owner = np.concatenate(own_list)

    facets: dict[int, np.ndarray] = {}
    for k, ptags in sheet_pieces.items():
        rows = []
        for ptag in ptags:
            etypes, _, enodes = gmsh.model.mesh.getElements(dim - 1, ptag)
            for et, en in zip(etypes, enodes):
                if et == face_type:
                    rows.append(index[en.astype(np.int64)].reshape(-1, dim))
        if rows:
            facets[k] = np.vstack(rows).T

    # Keep only nodes used by elements, and renumber them 0..N-1.
    used = np.unique(t)
    remap = np.full(len(tags), -1, dtype=np.int64)
    remap[used] = np.arange(len(used))
    t = remap[t]
    facets = {k: remap[v] for k, v in facets.items()}
    if any((v < 0).any() for v in facets.values()):
        raise RuntimeError("a sheet node is not a node of any element: the mesh is not conforming")
    xyz = coords[used]
    p = xyz.T.copy() if dim == 3 else xyz[:, :2].T.copy()   # 2-D: gmsh (x, y) is the layout's (x, z)
    stats = dict(nodes=p.shape[1], elements=t.shape[1], h_edge=rp.h_edge, h_core=rp.h_core,
                 h_far=rp.h_far, grading=rp.grading, core_margin=rp.core_margin)
    return MeshData(dim, axes, p, t, owner, facets, dom, clipped, rp, stats)
