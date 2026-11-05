"""Checks of the solver against exact solutions and internal identities, run one at a time.

Why this module exists, and why it is not a test suite
------------------------------------------------------
A solver that has not reproduced known answers cannot be trusted with unknown ones.  Each check
below solves a problem whose answer is known exactly (analytic.py gives the derivations) or an
identity the method must satisfy, and prints everything needed to judge the result: what the check
exercises, the mesh, the computed value, the reference value, the relative error, the tolerance and
the time.  Nothing aborts: a failing check prints its numbers like a passing one, so the reason can
be read off the output.  Checks are run individually so that each result is looked at before the
next is started.

Usage (from the folder that contains the package folder ``pcbcap``):
    python -m pcbcap.checks list
    python -m pcbcap.checks run <name> [--record checks.json]

``--record`` adds the result to a JSON file (one entry per check), from which a validation table
can be made.

How the tolerances were set
---------------------------
A tolerance here guards against a regression; it does not by itself prove accuracy.  The accuracy
argument is the convergence of the error with the element size, which meshing.py and the check
extrusion_3d_vs_2d show.  The tolerances are:
  * 1e-9 for problems whose exact potential is piecewise linear (uniform fields between plates, the
    floating slab, the linear film block).  The elements contain the exact solution, so only rounding
    remains; with about 1e3-1e5 unknowns and double precision, 1e-9 is far above rounding.
  * 3e-4 for the 2-D strips with edge singularities.  With edge elements of 1/1000 of the smallest
    feature, the first runs of these checks gave relative errors of 1.0e-4 (checks.json).  The
    tolerance is three times that, a margin chosen to absorb mesh changes between gmsh versions; the
    factor 3 is a choice, not a derived number.
  * 2e-4 for mirror_vs_full, which compares two numerical solutions on different meshes, each with a
    discretisation error of about 1e-4 at these settings: their difference can reach the sum.
  * For extrusion_3d_vs_2d, the error that the Richardson extrapolation itself reports (study.py), so
    that the check tests the error bars quoted for the 3-D results.
  * 0 for symmetry_declaration, which checks a yes-or-no outcome.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from pathlib import Path

from . import analytic, parts
from .constants import EPS0
from .geometry import Film, Layout, LinearProfile
from .meshing import MeshParams, build_mesh
from .study import solve_layout

CHECKS: dict[str, tuple[str, str, object]] = {}


def register(name: str, title: str, exercises: str):
    def deco(fn):
        CHECKS[name] = (title, exercises, fn)
        return fn
    return deco


def _mesh_line(res) -> str:
    m, f = res.mesh, res.fem
    return (f"mesh {m.get('nodes')} nodes, {m.get('elements')} elements, h_edge {m.get('h_edge', 0):.2e} mm; "
            f"{f.get('dofs')} unknowns (P{f.get('order')}); method {res.method}")


def _strips(eps_below=1.0, mirror=True, R=200.0, s=0.5, w=0.5) -> Layout:
    """Two coplanar zero-thickness strips of width w, gap s, in a square open enclosure of half-size R."""
    lay = Layout(2, "coplanar strips")
    if eps_below != 1.0:
        lay.add_rect((-R, R), (-R, 0.0), eps_r=eps_below, label="below")
    lay.add_segment("z", 0.0, (s / 2, s / 2 + w), net="A", name="strip A")
    lay.add_segment("z", 0.0, (-s / 2 - w, -s / 2), net="B", name="strip B")
    lay.set_enclosure({"x": (-R, R), "z": (-R, R)}, boundary="open")
    lay.set_symmetry(mirror_x=mirror)
    return lay


# ================================================================================================
@register("strips_free_space", "Coplanar strips in free space (2-D)",
          "zero-thickness conductors, edge singularities, open enclosure, mirror shortcut")
def _strips_free_space():
    # Exact: one K(m)/K(1-m) per half-plane (analytic.coplanar_halfplane), both half-planes air.
    exact = 2 * EPS0 * analytic.coplanar_halfplane(0.5, 0.5)
    res = solve_layout(_strips(), MeshParams(h_far=20.0))
    # Size of the truncation by the open (zero-flux) box of half-size R = 200 mm.  The odd drive has
    # charges +-Q' per unit length, a line dipole p = Q' d far away, whose potential is
    # p cos(theta) / (2 pi eps0 r).  Inside a zero-flux circle of radius R the correction that cancels
    # its normal field at r = R is the uniform-field potential p r cos(theta) / (2 pi eps0 R^2).  It
    # adds Q' d^2 / (2 pi eps0 R^2) to the voltage between the strips' charge centroids, so
    # 1/C' grows by d^2 / (2 pi eps0 R^2) and C' changes by -C'^2 d^2 / (2 pi eps0 R^2).  For these
    # strips the odd charge density is proportional to 1/sqrt((x^2 - a^2)(b^2 - x^2)) on a < |x| < b
    # (a = 0.25, b = 0.75 mm), whose centroids are d = 0.932 mm apart, and C'/eps0 = 1.563, so the
    # relative change is -1.563 x 0.932^2 / (2 pi x 200^2) = -5.4e-6 for a circle.  The box is a square,
    # which changes this by a factor of order 1; either way it is twenty times below the 1e-4 error.
    return dict(computed=res.C_F, reference=exact, unit="fF/mm", tolerance=3e-4,
                lines=[_mesh_line(res), "open box at 200 mm: truncation estimated at about -5e-6 relative "
                       "(line dipole in a zero-flux circle; see the comment in checks.py)"])


@register("strips_on_interface", "Coplanar strips on an air/dielectric interface (2-D)",
          "dielectric interface through the conductors' plane")
def _strips_on_interface():
    # Exact: eps0 (eps_1 + eps_2) K(m)/K(1-m) (analytic.coplanar_halfplane, second paragraph).
    exact = EPS0 * (4.2 + 1.0) * analytic.coplanar_halfplane(0.5, 0.5)
    res = solve_layout(_strips(eps_below=4.2), MeshParams(h_far=20.0))
    return dict(computed=res.C_F, reference=exact, unit="fF/mm", tolerance=3e-4, lines=[_mesh_line(res)])


@register("mirror_vs_full", "Mirror shortcut against the full-domain solve (2-D)",
          "the even/odd decomposition of capacitance.py, Eq. (6), against Eq. (4)")
def _mirror_vs_full():
    a = solve_layout(_strips(eps_below=4.2, mirror=True, R=60.0), MeshParams(h_far=6.0))
    b = solve_layout(_strips(eps_below=4.2, mirror=False, R=60.0), MeshParams(h_far=6.0))
    return dict(computed=a.C_F, reference=b.C_F, unit="fF/mm", tolerance=2e-4,
                lines=["half domain: " + _mesh_line(a), "full domain: " + _mesh_line(b),
                       "the two meshes differ, so the difference is bounded by their discretisation errors"])


@register("layered_plates_2d", "Plates with two dielectric layers in series (2-D)",
          "interface condition (continuous normal flux), insulating side walls")
def _layered_plates_2d():
    lay = Layout(2, "layered plates")
    lay.add_rect((-1, 1), (0.0, 0.4), eps_r=4.0, label="lower")
    lay.add_segment("z", 1.0, (-1, 1), net="A")
    lay.add_segment("z", 0.0, (-1, 1), net="B")
    lay.set_enclosure({"x": (-1, 1), "z": (0.0, 1.0)}, boundary="open")
    res = solve_layout(lay, MeshParams(h_edge=0.01, h_core=0.05, h_far=0.1))
    exact = analytic.parallel_plate(2.0, [(0.4, 4.0), (0.6, 1.0)])   # width 2 mm, per mm of depth
    return dict(computed=res.C_F, reference=exact, unit="fF/mm", tolerance=1e-9,
                lines=[_mesh_line(res), "the exact potential is piecewise linear, so the elements contain it"])


@register("layered_plates_3d", "Plates with two dielectric layers in series (3-D)",
          "3-D mesher, sheets on enclosure faces, dielectric boxes")
def _layered_plates_3d():
    lay = Layout(3, "layered plates 3-D")
    lay.add_box((-1, 1), (-1, 1), (0.0, 0.4), eps_r=4.0, label="lower")
    lay.add_sheet("z", 1.0, {"x": (-1, 1), "y": (-1, 1)}, net="A")
    lay.add_sheet("z", 0.0, {"x": (-1, 1), "y": (-1, 1)}, net="B")
    lay.set_enclosure({"x": (-1, 1), "y": (-1, 1), "z": (0.0, 1.0)}, boundary="open")
    res = solve_layout(lay, MeshParams(h_edge=0.2, h_core=0.2, h_far=0.3), order=1)
    exact = analytic.parallel_plate(4.0, [(0.4, 4.0), (0.6, 1.0)])
    return dict(computed=res.C_F, reference=exact, unit="fF", tolerance=1e-9, lines=[_mesh_line(res)])


@register("floating_slab", "Floating conductor slab between plates (2-D)",
          "floating conductor: one shared unknown, zero net charge (fem.py)")
def _floating_slab():
    # A slab 0.2 mm thick at an unknown potential between plates 2 mm wide and 1 mm apart, filling the
    # width: analytic.floating_slab derives C' = eps0 x width / (gap - slab), exactly.
    lay = Layout(2, "floating slab")
    lay.add_rect((-1, 1), (0.3, 0.5), net="F", floating=True, name="slab")
    lay.add_segment("z", 1.0, (-1, 1), net="A")
    lay.add_segment("z", 0.0, (-1, 1), net="B")
    lay.set_enclosure({"x": (-1, 1), "z": (0.0, 1.0)}, boundary="open")
    res = solve_layout(lay, MeshParams(h_edge=0.02, h_core=0.05, h_far=0.1))
    exact = analytic.floating_slab(area=2.0, gap=1.0, slab=0.2)
    return dict(computed=res.C_F, reference=exact, unit="fF/mm", tolerance=1e-9, lines=[_mesh_line(res)])


@register("film_linear_block", "Block with the film's linear potential on top (2-D)",
          "prescribed film potential (geometry.LinearProfile), mirror shortcut with a film")
def _film_linear_block():
    g, T, eps = 0.6, 0.35, 9.7
    lay = Layout(2, "linear block")
    lay.add_rect((-g / 2, g / 2), (0.0, T), eps_r=eps, label="alumina")
    lay.add_segment("x", g / 2, (0.0, T), net="A")
    lay.add_segment("x", -g / 2, (0.0, T), net="B")
    lay.add_segment("z", T, (-g / 2, g / 2), film=Film("A", "B", LinearProfile("x", -g / 2, g / 2)))
    lay.set_enclosure({"x": (-g / 2, g / 2), "z": (0.0, T)}, boundary="open")
    lay.set_symmetry(mirror_x=True)
    res = solve_layout(lay, MeshParams(h_edge=0.01, h_core=0.03, h_far=0.05))
    exact = analytic.linear_block(T, g, eps)
    return dict(computed=res.C_F, reference=exact, unit="fF/mm", tolerance=1e-9,
                lines=[_mesh_line(res), "this is the upper bound (G.28) of the companion note, exact here"])


@register("extrusion_3d_vs_2d", "3-D model uniform along y against the 2-D model",
          "3-D mesher, quarter-domain shortcut (x and y mirrors), convergence and Richardson extrapolation "
          "(study.py) as used for every 3-D result, against the 2-D solver")
def _extrusion():
    # Strips spanning the full depth 2D with flux-free y faces: the 3-D field is the 2-D field
    # repeated along y, so C_3D = 2D * C'_2D exactly.  Both models end at the same zero-flux box of
    # half-size R in (x, z), so they solve the same truncated problem and the truncation (about -6e-3
    # at R = 6 mm by the estimate in strips_free_space) cancels in the comparison.  The 2-D reference
    # uses edge elements of 0.1 um.  Its own discretisation error is not measured here; by the first-
    # order fall with the edge size seen in strips_free_space (1.0e-4 at 0.5 um), it is about 2e-5,
    # a tenth of the 3-D error bar that the check tests.
    #
    # The 3-D model is solved at three levels of MeshParams.refine, 4, 2 and 1.  The refine factor
    # multiplies the edge, core and far sizes (h_edge, h_core, h_far); the slope of the size growth
    # away from the edges (MeshParams.grading) stays fixed, so the graded zone keeps its shape while
    # its extent shrinks with the factor.  study.converge refines the resistor models of Appendix G
    # in the same way, with steps of sqrt(2) or 2.  (Refining only the edge size, as a first version of
    # this check did, leaves the error of the coarse bulk mesh in place, and the extrapolation then
    # converges to the value for that bulk mesh, about 5e-4 above the reference.)  The check passes
    # when the extrapolated value lies within the discretisation error that study.richardson itself
    # reports, |C_inf - C_finest|: that is the error bar quoted for every 3-D result, so the check
    # tests that those error bars are honest.
    #
    # Sizes: R = 6 mm keeps the 3-D mesh small; D = 1 mm makes the strips twice as long as they are
    # wide.  The base sizes at refine 1 (edge 7.5 um, core 37.5 um, far 0.25 mm) were chosen so that the
    # finest level stays below about 1e6 unknowns, and the core margin of 0.4 mm covers the strips'
    # near field (0.4 mm is 0.8 strip widths).  These are choices for this check, not derived values.
    from .study import richardson
    R, D = 6.0, 1.0
    lay3 = Layout(3, "extruded strips")
    lay3.add_sheet("z", 0.0, {"x": (0.25, 0.75), "y": (-D, D)}, net="A")
    lay3.add_sheet("z", 0.0, {"x": (-0.75, -0.25), "y": (-D, D)}, net="B")
    lay3.set_enclosure({"x": (-R, R), "y": (-D, D), "z": (-R, R)}, boundary="open")
    lay3.set_symmetry(mirror_x=True, mirror_y=True)
    r2 = solve_layout(_strips(R=R), MeshParams(h_edge=1e-4, h_far=1.0))
    base = MeshParams(h_edge=0.0075, h_core=0.0375, h_far=0.25, core_margin=0.4)
    factors = (4.0, 2.0, 1.0)
    vals, lines, edges = [], [], []
    for f in factors:
        r3 = solve_layout(lay3, MeshParams(h_edge=base.h_edge, h_core=base.h_core, h_far=base.h_far,
                                           core_margin=base.core_margin, refine=f))
        vals.append(r3.C_F / (2 * D))
        edges.append(r3.mesh["h_edge"])
        lines.append(f"3-D, refine {f:g} (h_edge {r3.mesh['h_edge']:.4f} mm): {vals[-1]:.6f} fF/mm, "
                     f"rel. error {vals[-1] / r2.C_F - 1:+.3e}; " + _mesh_line(r3))
    rich = richardson(list(factors), vals)
    tol = rich["error"] / r2.C_F
    lines.append(f"Richardson: observed order {rich['order']:.3f}, extrapolated {rich['extrapolated']:.6f} fF/mm, "
                 f"reported error {rich['error']:.6f} fF/mm ({tol:.2e} relative, used as the tolerance)")
    lines.append("2-D: " + _mesh_line(r2))
    data = dict(h_edge=edges, refine=list(factors), values=vals, reference=r2.C_F, order=rich["order"],
                extrapolated=rich["extrapolated"], reported_error=rich["error"])
    return dict(computed=rich["extrapolated"], reference=r2.C_F, unit="fF/mm", tolerance=tol, lines=lines,
                data=data)


@register("symmetry_declaration", "A false symmetry declaration is rejected",
          "Layout.check_symmetry, which guards the halving and quartering of the domain")
def _symmetry_declaration():
    lay = _strips(R=10.0)
    lay.add_rect((0.1, 0.2), (0.5, 0.6), eps_r=3.0, label="lopsided")    # breaks the x mirror
    try:
        build_mesh(lay, MeshParams(h_far=2.0))
        return dict(computed=0.0, reference=1.0, unit="", tolerance=0.0,
                    lines=["NOT rejected: the asymmetric layout was meshed as if symmetric"])
    except ValueError as e:
        return dict(computed=1.0, reference=1.0, unit="", tolerance=0.0, lines=[f"rejected with: {e}"])


@register("resistor_section_shares", "Material shares of C_F add up (2-D section of an 0402)",
          "chip-resistor builder, section y = 0, film, per-material shares (capacitance.py, section 5)")
def _resistor_section_shares():
    lay = parts.resistor_on_pads(parts.ChipResistor.from_size("0402"), parts.LandPattern.from_size("0402"),
                                 enclosure_half=3.0)
    lay.check_symmetry()
    res = solve_layout(lay.section_y0(), MeshParams(h_far=0.5))
    total = sum(res.contributions.values())
    shares = ", ".join(f"{k} {v:.3f}" for k, v in res.contributions.items())
    return dict(computed=total, reference=res.C_F, unit="fF/mm", tolerance=1e-9,
                lines=[_mesh_line(res), f"C_F = {res.C_F:.4f} fF/mm; shares: {shares}",
                       f"C_A0 = {res.C_A0:.4f} fF/mm (grounded enclosure at 3 mm)"])


# ================================================================================================
def run_check(name: str, record: str | None = None) -> dict:
    title, exercises, fn = CHECKS[name]
    print(f"[{name}] {title}")
    print(f"  exercises: {exercises}")
    t0 = time.perf_counter()
    try:
        out = fn()
    except Exception:
        print("  ERROR while running the check:")
        print("  " + traceback.format_exc().replace("\n", "\n  "))
        return dict(name=name, verdict="ERROR")
    dt = time.perf_counter() - t0
    c, r, tol = out["computed"], out["reference"], out["tolerance"]
    rel = (c / r - 1.0) if r else (c - r)
    verdict = "PASS" if abs(rel) <= tol else "FAIL"
    for line in out.get("lines", []):
        print(f"  {line}")
    print(f"  computed   {c:.10g} {out['unit']}")
    print(f"  reference  {r:.10g} {out['unit']}")
    print(f"  rel. error {rel:+.3e}   tolerance {tol:.0e}   -> {verdict}")
    print(f"  time {dt:.1f} s")
    result = dict(name=name, title=title, exercises=exercises, computed=c, reference=r, unit=out["unit"],
                  rel_error=rel, tolerance=tol, verdict=verdict, seconds=dt, lines=out.get("lines", []),
                  data=out.get("data"))
    if record:
        path = Path(record)
        data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        data[name] = result
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=1), encoding="utf-8", newline="\n")
    return result


def main(argv=None) -> int:
    from .study import lower_priority
    lower_priority(2)
    ap = argparse.ArgumentParser(prog="python -m pcbcap.checks")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    r = sub.add_parser("run")
    r.add_argument("name")
    r.add_argument("--record", default=None)
    args = ap.parse_args(argv)
    if args.cmd == "list":
        for k, (title, ex, _) in CHECKS.items():
            print(f"{k:26s} {title}")
        return 0
    if args.name not in CHECKS:
        print(f"unknown check {args.name!r}; use 'list'")
        return 2
    run_check(args.name, args.record)
    return 0


if __name__ == "__main__":
    sys.exit(main())
