"""Group the mesher's refinement features by per-item edge size (pcbcap/meshing.py)."""
import sys
from pathlib import Path

p = Path(sys.argv[1])
s = p.read_text(encoding="utf-8")


def rep(old, new):
    global s
    n = s.count(old)
    if n != 1:
        raise SystemExit(f"expected one match, found {n}: {old[:90]!r}")
    s = s.replace(old, new)


rep('''def _feature_entities(gmsh, layout: Layout, dim: int, owner_of_piece, sheet_pieces, dom, clipped) -> list[int]:
    """Tags of the entities near which the mesh is refined: in 3-D the edges (curves) of every
    conductor and film piece, in 2-D their corners (points).  These are where the field is singular
    (see the module docstring)."""
    want = dim - 2  # curves (1) in 3-D, points (0) in 2-D
    ents: set[int] = set()
''', '''def _feature_entities(gmsh, layout: Layout, dim: int, owner_of_piece, sheet_pieces, dom, clipped,
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
        ms = layout.items[k].mesh_size
        return rp.h_edge if ms is None else max(ms * rp.scale, 0.5 * rp.h_edge)

    def claim(tags, h):
        for t in tags:
            size_of[t] = min(size_of.get(t, math.inf), h)
''')

rep('''    for ptag, k in owner_of_piece.items():
        if k >= 0 and isinstance(layout.items[k].role, Conductor):
            ents.update(t for _, t in boundary_down([(dim, ptag)]))
    for k, tags in sheet_pieces.items():
        ents.update(t for _, t in boundary_down([(dim - 1, t) for t in tags]))''',
    '''    for ptag, k in owner_of_piece.items():
        if k >= 0 and isinstance(layout.items[k].role, Conductor):
            claim([t for _, t in boundary_down([(dim, ptag)])], size_for(k))
    for k, tags in sheet_pieces.items():
        claim([t for _, t in boundary_down([(dim - 1, t) for t in tags])], size_for(k))''')

rep('''    return sorted(t for t in ents if not _on_inert_boundary(gmsh, want, t, layout, dom, clipped))''',
    '''    groups: dict[float, list[int]] = {}
    for t, h in size_of.items():
        if not _on_inert_boundary(gmsh, want, t, layout, dom, clipped):
            groups.setdefault(h, []).append(t)
    return {h: sorted(v) for h, v in groups.items()}''')

rep('''    bulk = (2.0 if dim == 2 else 6.0) * meas / rp.h_core ** dim
    rings = 2 * math.pi / rp.grading ** 2 * max(math.log(rp.h_core / rp.h_edge), 1.0)
    if dim == 2:
        return bulk + len(feature_tags) * rings
    length = sum(gmsh.model.occ.getMass(1, t) for t in feature_tags)
    return bulk + length / rp.h_edge * rings / 4.0''',
    '''    bulk = (2.0 if dim == 2 else 6.0) * meas / rp.h_core ** dim
    total = bulk
    for h, tags in feature_tags.items():
        rings = 2 * math.pi / rp.grading ** 2 * max(math.log(max(rp.h_core, h) / h), 1.0)
        if dim == 2:
            total += len(tags) * rings
        else:
            total += sum(gmsh.model.occ.getMass(1, t) for t in tags) / h * rings / 4.0
    return total''')

rep('''    f = gmsh.model.mesh.field
    fields = []
    if feature_tags:
        f.add("Distance", 1)
        f.setNumbers(1, "CurvesList" if dim == 3 else "PointsList", feature_tags)
        if dim == 3:
            f.setNumber(1, "Sampling", 40)
        f.add("Threshold", 2)
        f.setNumber(2, "InField", 1)
        f.setNumber(2, "SizeMin", rp.h_edge)
        f.setNumber(2, "SizeMax", rp.h_far)
        d0 = rp.h_edge                               # keep the smallest size within one element
        d1 = d0 + (rp.h_far - rp.h_edge) / rp.grading  # growth limited to `grading` per unit length
        f.setNumber(2, "DistMin", d0)
        f.setNumber(2, "DistMax", d1)
        fields.append(2)
    # Core box: h_core inside, h_far outside, with a transition layer as wide as the growth needs.
    cbb = layout.bounding_box(only_conductors=True)
    m = rp.core_margin
    f.add("Box", 3)
    names = ("X", "Y", "Z") if dim == 3 else ("X", "Y")
    for nm, a in zip(names, layout.axes):
        lo = max(cbb[a][0] - m, dom[a][0])
        hi = min(cbb[a][1] + m, dom[a][1])
        f.setNumber(3, f"{nm}Min", lo)
        f.setNumber(3, f"{nm}Max", hi)
    f.setNumber(3, "VIn", rp.h_core)
    f.setNumber(3, "VOut", rp.h_far)
    f.setNumber(3, "Thickness", (rp.h_far - rp.h_core) / rp.grading)
    fields.append(3)
    f.add("Min", 4)
    f.setNumbers(4, "FieldsList", fields)
    f.setAsBackgroundMesh(4)''',
    '''    f = gmsh.model.mesh.field
    fields = []
    fid = 0
    for h, tags in feature_tags.items():
        # one graded field per edge size: h at the features, growing by `grading` per unit distance
        fid += 1
        f.add("Distance", fid)
        f.setNumbers(fid, "CurvesList" if dim == 3 else "PointsList", tags)
        if dim == 3:
            f.setNumber(fid, "Sampling", 40)
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
    cbb = layout.bounding_box(only_conductors=True)
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
    f.setAsBackgroundMesh(fid)''')

rep('''        feature_tags = _feature_entities(gmsh, layout, dim, owner_of_piece, sheet_pieces, dom, clipped)''',
    '''        feature_tags = _feature_entities(gmsh, layout, dim, owner_of_piece, sheet_pieces, dom, clipped, rp)''')

rep('''    max_elements: float | None = None''',
    '''    max_elements: float | None = None
    scale: float = 1.0      # set by resolve_params: the refine factor applied (scales per-item sizes)''')

rep('''    return replace(params, h_edge=h_edge_r, h_core=max(h_core * r, h_edge_r), h_far=h_far * r,
                   core_margin=margin, refine=1.0, max_elements=max_el)''',
    '''    return replace(params, h_edge=h_edge_r, h_core=max(h_core * r, h_edge_r), h_far=h_far * r,
                   core_margin=margin, refine=1.0, max_elements=max_el, scale=r)''')

p.write_text(s, encoding="utf-8", newline="\n")
print("patched", p)
