"""Exact solutions used to test the solver.

Why this module exists
----------------------
A field solver is only trustworthy if it reproduces problems whose answer is known exactly.  Each
function below gives such an answer, with the derivation in its docstring, so that a failed check
can be traced to the solver and not to the reference.  What each one exercises in checks.py:
  * parallel_plate: dielectric interfaces (continuity of the normal flux), insulating side walls,
    and the 3-D mesher (checks layered_plates_2d and layered_plates_3d);
  * coplanar_halfplane: zero-thickness conductors and their edge singularities, an air/dielectric
    interface through the conductors' plane (checks strips_free_space, strips_on_interface, and the
    2-D reference of extrusion_3d_vs_2d);
  * floating_slab: a floating conductor, one shared unknown with zero net charge (check
    floating_slab);
  * linear_block: the prescribed linear potential of a film (check film_linear_block).
The mirror-symmetric shortcut and the agreement between 2-D and 3-D models have no closed form of
their own; checks.py tests them as identities (mirror_vs_full, extrusion_3d_vs_2d).  coaxial() is
kept as a reference for users; no check uses it.

Units: lengths in mm, eps0 in fF/mm (constants.py), so 3-D capacitances come out in fF and 2-D
ones (per unit length) in fF/mm.
"""
from __future__ import annotations

import math

from scipy.special import ellipk, ellipkm1

from .constants import EPS0


def parallel_plate(area: float, layers: list[tuple[float, float]]) -> float:
    """Capacitance of two plates of ``area`` separated by dielectric ``layers`` [(thickness, eps_r)],
    stacked between them, with insulating (zero-flux) side walls.

    Derivation.  Try a field that is uniform in each layer and normal to the plates.  It satisfies
    Laplace's equation in each layer and the zero-flux condition on the side walls (the field is
    parallel to them).  At each interface the normal displacement D = eps E must be continuous (no free
    charge), so D is the same in every layer and E_i = D/(eps0 eps_i).  The voltage is the sum of the
    drops, V = D sum_i d_i/(eps0 eps_i), and the charge per area is D, so
        C = area * eps0 / sum_i (d_i/eps_i).
    By uniqueness this trial field is the solution, so the result is exact.  One layer gives the
    familiar eps0 eps_r area/d."""
    return area * EPS0 / sum(d / e for d, e in layers)


def coplanar_halfplane(w: float, s: float) -> float:
    """Capacitance per unit length, divided by eps0 eps_r, between two coplanar strips of width w and
    gap s on the edge of a half-plane of permittivity eps_r (the field fills one side only):

        K(m)/K(1 - m),   m = (w/(s + w))^2,

    with K the complete elliptic integral of the first kind in the parameter convention
    (K(m) = int_0^(pi/2) dt/sqrt(1 - m sin^2 t)).  Derived step by step in the companion note,
    Sections G.5-G.7, Eqs. (G.14)-(G.25): a Moebius map sends the four strip ends to 0, m, 1 and
    infinity, and the Schwarz-Christoffel map of the half-plane onto a rectangle turns the problem into
    a parallel plate of width 2K(m) and separation 2K(1 - m).

    Strips with dielectrics on both sides of their plane.  Let phi_h(x, z), z >= 0, be the solution
    of the half-plane problem: the strip potentials on the strips and zero normal derivative,
    d(phi_h)/dz = 0, on the rest of the plane z = 0.  Define phi(x, z) = phi_h(x, |z|) on the whole
    plane, with permittivity eps_1 above and eps_2 below.  This phi
      * satisfies Laplace's equation in each half (each half is a copy of phi_h),
      * takes the strip potentials on both faces of the strips,
      * is continuous across the plane outside the strips (both sides equal phi_h(x, 0)), and
      * has d(phi)/dz = 0 on both sides of the plane outside the strips, so the normal flux
        eps d(phi)/dz is 0 on both sides and therefore continuous, whatever eps_1 and eps_2 are.
    It thus meets every condition of the two-dielectric problem, and by uniqueness it is the solution.
    The charge on a strip is the flux leaving it on both faces: eps_1 times the half-plane flux above
    plus eps_2 times the same flux below, so
        C' = eps0 (eps_1 + eps_2) K(m)/K(1 - m),
    and for one dielectric on both sides (eps_1 = eps_2 = eps_r), twice the half-plane value.
    """
    m = (w / (s + w)) ** 2
    return float(ellipk(m) / ellipkm1(m))


def floating_slab(area: float, gap: float, slab: float, eps_r: float = 1.0) -> float:
    """Capacitance of two parallel plates of ``area`` and separation ``gap`` with a floating
    conductor slab of thickness ``slab`` between them, parallel to the plates and covering their
    whole area, with insulating side walls (per unit depth in 2-D, where ``area`` is a width).

    Derivation.  The slab is a conductor at an unknown potential U with zero net charge.  Try a field
    that is uniform and normal to the plates in each of the two gaps, of thicknesses d_1 and d_2 with
    d_1 + d_2 = gap - slab.  Zero net charge on the slab means the charge -Q on its upper face and +Q
    on its lower face are equal and opposite, so the displacement D = Q/area is the same in both gaps.
    The voltage between the plates is then D d_1/(eps0 eps_r) + D d_2/(eps0 eps_r), the drop inside
    the slab being zero, and
        C = Q/V = eps0 eps_r area / (gap - slab),
    independent of where the slab sits.  The trial field satisfies Laplace's equation in each gap, the
    plate potentials, a constant potential on the slab with zero net charge, and zero flux through the
    side walls (it is parallel to them), so by uniqueness it is the solution."""
    return EPS0 * eps_r * area / (gap - slab)


def coaxial(a: float, b: float, eps_r: float = 1.0) -> float:
    """Capacitance per unit length of coaxial circular cylinders of radii a < b (fF/mm).

    Derivation.  By symmetry the field is radial; Gauss's law on a cylinder of radius r and unit
    length with charge lambda per unit length gives E = lambda/(2 pi eps r).  Integrating from a to b,
    V = lambda ln(b/a)/(2 pi eps), so C' = lambda/V = 2 pi eps0 eps_r / ln(b/a)."""
    return 2.0 * math.pi * EPS0 * eps_r / math.log(b / a)


def linear_block(T: float, g: float, eps_r: float) -> float:
    """Capacitance per unit length of a dielectric block of height T between two vertical electrodes at
    x = -g/2 and x = +g/2 (potentials -V/2 and +V/2), with the linear potential phi = V x/g prescribed on
    its top face and an insulating bottom face:  C' = eps0 eps_r T/g.

    Derivation.  phi = V x/g satisfies Laplace's equation, takes the right values on both electrodes and
    on the top face, and has zero vertical derivative, so the bottom face carries no flux.  By
    uniqueness it is the solution.  Its field V/g fills the area g T, so the energy per unit length is
    (1/2) eps (V/g)^2 g T = (1/2) (eps T/g) V^2, and C' = eps T/g.  This is the upper bound (G.28) of the
    companion note, where the termination slots are filled with metal; it is exact for this geometry,
    which makes it a test of the prescribed-film machinery."""
    return EPS0 * eps_r * T / g
