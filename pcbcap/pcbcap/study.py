"""Running layouts: one solve, mesh-convergence studies, enclosure-size studies, sweeps.

Why this module exists
----------------------
A single finite-element result has two errors that the solve itself does not report:
  * the discretisation error of the mesh (finite element size), and
  * the truncation error of the enclosure (the "far away" boundary is not at infinity).
This module estimates both by repeating the solve and extrapolating, so that every number the
package reports comes with an estimate of how far it is from the exact solution of the model.
It also runs parameter sweeps that resume after an interruption.

Mesh convergence: what scales with the refinement factor
---------------------------------------------------------
``MeshParams.refine`` = r multiplies three sizes: the size at conductor edges h_e, the core size h_c
and the far size h_f (meshing.resolve_params).  Two things do not scale with r.  (i) Away from an
edge the size grows as h(d) = h_e + g (d - h_e) with the distance d, at the fixed slope g =
MeshParams.grading, until it reaches h_c; the graded zone keeps its shape and only its extent,
(h_c - h_e)/g, scales with r.  (ii) The edge size is capped at the layout's thinnest feature
(meshing.resolve_params), so a level with h_e r above that cap does not refine with r at all;
converge() refuses such levels.

How the error should scale.  For the energy, the finite-element error is the energy of the error
itself: with phi the exact and phi_h the computed potential (same prescribed values),
a(phi_h, phi_h) - a(phi, phi) = a(phi_h - phi, phi_h - phi) + 2 a(phi, phi_h - phi), and the last term
is zero because phi_h - phi is admissible and phi satisfies (2) of fem.py.  phi_h is also the best
approximation of phi in this energy (that is what minimising the energy over the trial functions
means), so the error is at most the energy of phi - I_h phi, the error of interpolating phi on the
mesh.  Near a conductor edge phi - V varies as rho^nu with the distance rho from the edge (fem.py,
Step 2).  Count the interpolation error per unit length of edge, in three zones (k is the element
degree, 2 for P2; for degree-k elements the error energy density is of order h^(2k) times the square
of the (k+1)-th derivatives, which here are of order rho^(nu-k-1)):
  * the elements touching the edge, of size h_e: the energy of rho^nu within rho < h_e, of order
    int_0^h_e rho^(2 nu - 2) rho d rho, i.e. of order h_e^(2 nu);
  * the graded zone, h = g rho: density of order (g rho)^(2k) rho^(2 nu - 2k - 2) = g^(2k) rho^(2 nu - 2),
    integrated with rho d rho up to the zone's outer radius (h_c - h_e)/g: of order
    g^(2k - 2 nu) h_c^(2 nu);
  * the core beyond it, h = h_c: density h_c^(2k) rho^(2 nu - 2k - 2), integrated from (h_c - h_e)/g
    outward: of order h_c^(2k) (h_c/g)^(2 nu - 2k), again of order h_c^(2 nu).
All three scale as r^(2 nu), because h_e and h_c both scale with r.  Regions far from every edge,
where phi is smooth, contribute of order h^(2k) = r^4 for P2.  So once the mesh is fine enough

    C(r) = C_inf + k r^p,     p = 2 nu_min,                                                (1)

where nu_min is the smallest edge exponent in the layout.  With one dielectric around an edge,
nu = pi/alpha for a dielectric angle alpha (fem.py, Step 2): 2/3 at a box edge (p = 4/3) and 1/2 at a
sheet edge (p = 1).  Where two dielectrics meet at the edge the exponent changes.  For a conductor
whose faces bound the angle alpha = alpha_1 + alpha_2, with eps_1 filling alpha_1 next to one face
and eps_2 filling alpha_2 next to the other, the solutions A sin(nu theta) and B sin(nu (alpha - theta))
must have equal values and equal normal fluxes eps d(phi)/d theta on the interface theta = alpha_1,
which gives
    eps_1 cot(nu alpha_1) + eps_2 cot(nu alpha_2) = 0.
Examples (smallest root): a pad's lower edge on FR-4 (4.2 over pi, air over pi/2) has nu = 0.56,
p = 1.12; a film edge at the corner of the alumina (9.7 over pi/2, air over 3 pi/2) has nu = 0.63,
p = 1.26; a sheet edge with alumina over 3 pi/2 and air over pi/2 would have nu = 0.367, p = 0.73.
The order of a layout is therefore expected between about 0.7 and 4/3; study.py measures it rather
than assuming it.  One more effect lowers the measured order: gmsh measures the distance to an edge
from points sampled along it (meshing.py, "Sampling"), which adds to the edge size a part that does
not scale with r unless the sampling is fine enough; meshing.py sets it so.

Richardson extrapolation
------------------------
Three solves at r1 > r2 > r3 determine the three unknowns of (1).  Subtracting (1) at consecutive
levels,
    C1 - C2 = k (r1^p - r2^p),     C2 - C3 = k (r2^p - r3^p),
so the observed order p solves

    (C1 - C2)/(C2 - C3) = (r1^p - r2^p)/(r2^p - r3^p),                                       (2)

which for a constant ratio q = r1/r2 = r2/r3 reduces to p = ln[(C1 - C2)/(C2 - C3)] / ln q
[Richardson and Gaunt 1927]; in general it is found by a root search (brentq).  Then
k = (C2 - C3)/(r2^p - r3^p) and C_inf = C3 - k r3^p.  The extrapolation is made only when
  * the differences C1 - C2 and C2 - C3 have the same sign: the values approach their limit
    monotonically, as (1) requires (and as nothing guarantees, since the meshes are not nested), and
  * p lies between 0.05 and p_max = 2k, the energy order of degree-k elements for a smooth field
    (4 for P2); a larger observed order can only come from noise.  The lower limit is a choice:
    for p = 0.05 and q = 2 the extrapolation step C3 - C_inf is (C2 - C3)/(2^0.05 - 1), 28 times the
    last difference, more leverage than any measured difference supports.
Otherwise no extrapolation is made and the spread of the three values is reported as the
uncertainty.  The difference |C_inf - C3| is reported as the discretisation error of the finest
mesh.

The enclosure (three-dimensional layouts with grounded walls only)
------------------------------------------------------------------
With a grounded enclosure of size R around a 3-D layout that has no ground of its own, the even part
of the field (net charge on A and B together) ends on the enclosure walls.  Why the effect falls as
1/R, for any shape: write the potential of a unit point charge inside the grounded box as the free-
space potential 1/(4 pi eps |r - r'|) plus a regular part G_reg, the potential of the charges the walls
carry.  Seen from a layout much smaller than R, G_reg is nearly constant over the layout, of order
-1/(4 pi eps R_eff) with R_eff proportional to R (for a sphere of radius b around the charge,
exactly -1/(4 pi eps b)).  A conductor with free-space capacitance C0 that carries the charge Q then
sits at V = Q/C0 + Q G_reg = Q (1/C0 - 1/(4 pi eps R_eff)), so
    C(R) = Q/V = C0 / (1 - C0/(4 pi eps R_eff)) = C0 [1 + C0/(4 pi eps R_eff) + ...],
a correction proportional to 1/R.  For a sphere of radius a in a grounded sphere of radius b this
is exact: C = 4 pi eps a b/(b - a) = C0/(1 - a/b).  With a board slab that reaches the walls, eps is
replaced by an effective permittivity of the far field, and R_eff by another multiple of R; the form
is the same.  The odd part carries no net charge, so its far field is a dipole field, of order p/r^2
in potential; its image in the walls produces a field of order p/R^3 at the layout, and an energy
change of order p^2/R^3.  Hence

    C(R) = C_inf + k_R / R + O(R^-2),                                                        (3)

and, since only the even part feels the walls to this order, the changes of C_F and C_A0 between
enclosure sizes are tied: from C_F = f[a(phi_o) - a(phi_e)] and C_A0 = 2 f a(phi_e) (capacitance.py,
Eq. (6)), dC_A0 / dC_F = -2.  enclosure_correction measures the order q of C(R) = C_inf + k R^-q
from three sizes (Eq. (2) with 1/R in the role of r) rather than assuming q = 1.

In 2-D (per unit length) none of this holds: the capacitance of a net to a distant grounded box
behaves as 2 pi eps / ln(R/a), which falls to zero only logarithmically, so there is no finite
"ground at infinity" to extrapolate to; enclosure_correction refuses 2-D layouts.  An open (zero-flux)
enclosure is no model of a distant ground either (geometry.Enclosure); it is refused too.

How the correction is combined with a mesh study.  The correction dC = C_inf - C(R1) is computed on a
coarse mesh (refine 4, the coarsest level of the size studies) and added to the mesh-extrapolated
value at the smallest enclosure R1.  Its own mesh error follows from the derivation above: the
correction is of order C0^2/(4 pi eps R_eff), so a relative mesh error delta in C0 makes a relative
error of about 2 delta in dC.  The capacitances to ground at refine 4 lie a few tenths of a per cent
above their extrapolated values in the 0402 study, so dC carries an error of the order of 1 % of
itself.  This rests on the far field being resolved as well as the near field; the far elements are
much larger (h_f = enclosure extent / 12 times the refine factor), and a direct check, one enclosure
size at two refinements, has not been made.  A layout with its own ground (a plane, a shield) keeps
most of the even field and shows a much smaller k_R.
"""
from __future__ import annotations

import json
import math
import os
import time
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Callable

import numpy as np

from .capacitance import TwoPortResult, two_port
from .fem import Problem
from .geometry import Layout
from .meshing import MeshParams, build_mesh


def lower_priority(threads: int = 2) -> None:
    """Run politely on a shared workstation: below-normal priority and few BLAS threads.

    A field solve can occupy every core for minutes.  On a machine in use for other work
    (calls, meetings) that would make the other work stutter, so a study lowers its own priority.
    The thread limits only take effect if set before NumPy loads its BLAS, which is why the
    command-line entry point calls this first."""
    for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
        os.environ.setdefault(var, str(threads))
    try:
        import psutil
        p = psutil.Process()
        if hasattr(psutil, "BELOW_NORMAL_PRIORITY_CLASS"):
            p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)      # Windows
        else:
            p.nice(10)                                       # POSIX niceness
    except Exception:
        pass


def solve_layout(layout: Layout, params: MeshParams | None = None, order: int = 2,
                 a: str = "A", b: str = "B", keep_fields: bool = False, return_problem: bool = False):
    """Mesh a layout, assemble, and return the two-port result (and the Problem if asked)."""
    t0 = time.perf_counter()
    md = build_mesh(layout, params or MeshParams())
    prob = Problem(layout, md, order=order)
    res = two_port(prob, a, b, keep_fields=keep_fields)
    res.fem["total_seconds"] = time.perf_counter() - t0
    return (res, prob) if return_problem else res


# ------------------------------------------------------------------------------------------------
def richardson(r: list[float], C: list[float], p_max: float = 4.0) -> dict:
    """Extrapolate three values C at refinement factors r (coarse to fine) with Eqs. (1)-(2).

    p_max is the largest order accepted: 2k for degree-k elements (4 for P2, the default; 2 for P1),
    the energy order for a smooth field, which no singular problem can exceed."""
    from scipy.optimize import brentq

    r1, r2, r3 = r
    C1, C2, C3 = C
    d12, d23 = C1 - C2, C2 - C3
    out = dict(finest=C3, extrapolated=None, order=None, error=max(abs(C1 - C3), abs(C2 - C3)),
               monotone=False)
    if d12 == 0 or d23 == 0 or (d12 > 0) != (d23 > 0):
        out["note"] = "not monotone: no extrapolation; error = spread of the three values"
        return out
    rho = d12 / d23

    def g(p):
        return (r1 ** p - r2 ** p) / (r2 ** p - r3 ** p) - rho

    lo, hi = 0.05, p_max          # limits explained in the module docstring
    if g(lo) * g(hi) > 0:
        out["note"] = f"observed order outside ({lo}, {hi}): no extrapolation"
        return out
    p = brentq(g, lo, hi, xtol=1e-12)
    k = d23 / (r2 ** p - r3 ** p)
    C_inf = C3 - k * r3 ** p
    out.update(extrapolated=C_inf, order=p, error=abs(C_inf - C3), monotone=True, note="Richardson, Eq. (2)")
    return out


@dataclass
class Convergence:
    """Results of a mesh-convergence study of one layout."""

    levels: list[dict]
    C_F: dict
    C_A0: dict
    contributions: dict
    last: TwoPortResult | None = field(default=None, repr=False)

    def value(self) -> float:
        """Best estimate of C_F: the extrapolated value when available, else the finest."""
        return self.C_F["extrapolated"] if self.C_F.get("extrapolated") is not None else self.C_F["finest"]

    def to_dict(self) -> dict:
        return dict(levels=self.levels, C_F=self.C_F, C_A0=self.C_A0, contributions=self.contributions)


def check_levels(layout: Layout, params: MeshParams, factors) -> None:
    """Raise ValueError if a level of a convergence study would not refine with its factor.

    meshing.resolve_params caps the edge size at the layout's thinnest feature.  A level whose edge
    size h_e * refine * factor exceeds that cap gets the cap instead, so two levels can end up with the
    same edge size although their factors differ, and Eq. (1) no longer describes the values: the
    Richardson extrapolation would then be wrong without any warning.  (For example, with h_e = 3.75 um
    and a 15-um termination, refine 5.66 and refine 4 both give 15-um edges.)"""
    feat = layout.smallest_feature()
    # the same default as meshing.resolve_params
    base = params.h_edge if params.h_edge is not None else (feat / 1000.0 if layout.dim == 2 else feat / 4.0)
    for f in factors:
        h = base * params.refine * f
        if h > feat * (1.0 + 1e-9):     # 1e-9: equality (h exactly at the cap) is allowed
            raise ValueError(f"level refine {params.refine * f:g}: edge size {h:.4g} mm exceeds the thinnest "
                             f"feature {feat:.4g} mm and would be capped; choose finer levels for a "
                             f"convergence study")


def converge(layout: Layout, factors=(2.0, 1.414, 1.0), params: MeshParams | None = None, order: int = 2,
             a: str = "A", b: str = "B", keep_fields: bool = False, log: Callable | None = print) -> Convergence:
    """Solve at three refinement factors (coarse to fine) and extrapolate C_F and C_A0.

    The default factors step by sqrt(2) (1.414 is its rounded value), so that the finest of three
    levels has twice the resolution of the coarsest at about 2^3 = 8 times its element count in 3-D.
    Every level must refine with its factor (check_levels)."""
    params = params or MeshParams()
    check_levels(layout, params, factors)
    levels, results = [], []
    for r in factors:
        res = solve_layout(layout, replace(params, refine=params.refine * r), order, a, b,
                           keep_fields=keep_fields and r == factors[-1])
        results.append(res)
        lv = dict(refine=r, C_F=res.C_F, C_A0=res.C_A0, dofs=res.fem["dofs"], elements=res.mesh["elements"],
                  seconds=res.fem["total_seconds"], contributions=res.contributions)
        levels.append(lv)
        if log:
            log(f"    refine {r:5.3f}: C_F = {res.C_F:.4f} {res.unit}, C_A0 = {res.C_A0:.4f}, "
                f"{lv['dofs']} DOFs, {lv['seconds']:.1f} s")
    rs = list(factors)
    pm = 2.0 * order
    cf = richardson(rs, [x.C_F for x in results], pm) if len(rs) == 3 else dict(finest=results[-1].C_F)
    ca = richardson(rs, [x.C_A0 for x in results], pm) if len(rs) == 3 else dict(finest=results[-1].C_A0)
    return Convergence(levels, cf, ca, dict(results[-1].contributions), results[-1])


def enclosure_correction(make_layout: Callable[[float], Layout], margins=(8.0, 16.0, 32.0),
                         params: MeshParams | None = None, order: int = 2, a: str = "A", b: str = "B",
                         log: Callable | None = print) -> dict:
    """Correction to an infinitely large enclosure, from coarse solves at two or three sizes.

    ``make_layout(margin)`` returns the layout with its enclosure at that margin; R is the enclosure's
    smallest half-width.  Only 3-D layouts with grounded enclosures are accepted (module docstring).
    With two sizes, Eq. (3) is applied with the 1/R law assumed: from C(R) = C_inf + k/R at R1 and R2,
        R2 C(R2) - R1 C(R1) = (R2 - R1) C_inf,   so   C_inf = (R2 C(R2) - R1 C(R1)) / (R2 - R1).
    With three sizes the decay is measured: Eq. (2) is applied with 1/R in the role of r, which returns
    the observed order q of C(R) = C_inf + k R^-q (q = 1 is expected for a layout without its own
    ground) and the extrapolated C_inf.  If the three values fail the extrapolation test (module
    docstring), the 1/R law is assumed after all and applied to the two largest sizes; the result
    records the order as None in that case.  The correction dC = C_inf - C(R1) is meant to be added
    to a mesh-extrapolated value at the first (smallest) size.

    Defaults: margins of 8, 16 and 32 mm, i.e. doubling steps in R, the base 8 mm being four times the
    length of the largest part studied (an 0805, 2 mm); refine 4, the coarsest level of the size
    studies, because the correction comes from the far field (module docstring).  Both are choices."""
    params = params or MeshParams(refine=4.0)
    vals = []
    for m in margins:
        lay = make_layout(m)
        if lay.dim != 3:
            raise ValueError("enclosure_correction applies to 3-D layouts only; in 2-D the capacitance to a "
                             "distant ground falls as 1/ln R and has no finite limit")
        if any(lay.enclosure.face_condition(f) != "ground" for f in
               [a + s for a in lay.axes for s in ("min", "max")]):
            raise ValueError("enclosure_correction needs grounded enclosure faces; an open box models an "
                             "isolated pair, not a distant ground (geometry.Enclosure)")
        R = _half_size(lay)
        res = solve_layout(lay, params, order, a, b)
        vals.append((R, res.C_F, res.C_A0))
        if log:
            log(f"    enclosure margin {m:g} mm (R = {R:.2f} mm): C_F = {res.C_F:.4f} {res.unit}, "
                f"C_A0 = {res.C_A0:.4f}, {res.fem['dofs']} unknowns, {res.fem['total_seconds']:.1f} s")
    Rs = [v[0] for v in vals]
    F = [v[1] for v in vals]
    A = [v[2] for v in vals]
    out = dict(R=Rs, C_F=F, C_A0=A)
    if len(vals) == 3:
        inv = [1.0 / R for R in Rs]
        rf, ra = richardson(inv, F), richardson(inv, A)
        out.update(order_C_F=rf.get("order"), order_C_A0=ra.get("order"), note_C_F=rf.get("note"))
        F_inf = rf["extrapolated"] if rf.get("extrapolated") is not None else (Rs[2] * F[2] - Rs[1] * F[1]) / (Rs[2] - Rs[1])
        A_inf = ra["extrapolated"] if ra.get("extrapolated") is not None else (Rs[2] * A[2] - Rs[1] * A[1]) / (Rs[2] - Rs[1])
    else:
        F_inf = (Rs[1] * F[1] - Rs[0] * F[0]) / (Rs[1] - Rs[0])
        A_inf = (Rs[1] * A[1] - Rs[0] * A[0]) / (Rs[1] - Rs[0])
    out.update(C_F_inf=F_inf, C_A0_inf=A_inf, dC_F=F_inf - F[0], dC_A0=A_inf - A[0])
    return out


def _half_size(lay: Layout) -> float:
    """Smallest half-width of the enclosure: the distance at which the walls first act."""
    return 0.5 * min(v - u for (u, v) in lay.enclosure.spans.values())


# ------------------------------------------------------------------------------------------------
def sweep(run: Callable[[dict], dict], points: list[dict], cache: str | Path | None = None,
          log: Callable | None = print) -> list[dict]:
    """Evaluate ``run(point)`` for every parameter dict in ``points``, caching results in JSON.

    A sweep can take long; if it is interrupted, rerunning it with the same cache file computes only
    the points that are missing.  Each cached entry stores the point itself, so the cache is also a
    readable record of what was run."""
    store: dict[str, dict] = {}
    path = Path(cache) if cache else None
    if path and path.exists():
        store = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for pt in points:
        key = json.dumps(pt, sort_keys=True)
        if key not in store:
            t0 = time.perf_counter()
            res = run(pt)
            res = dict(point=pt, result=res, seconds=time.perf_counter() - t0)
            store[key] = res
            if path:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(store, indent=1, default=_jsonable), encoding="utf-8", newline="\n")
            if log:
                log(f"  done {pt} in {res['seconds']:.1f} s")
        out.append(store[key])
    return out


def _jsonable(x):
    if isinstance(x, (np.floating, np.integer)):
        return x.item()
    if isinstance(x, np.ndarray):
        return x.tolist()
    if hasattr(x, "to_dict"):
        return x.to_dict()
    raise TypeError(type(x))
