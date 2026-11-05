"""Capacitances from field solutions: the feedback (mutual) capacitance and its companions.

Why this module exists
----------------------
``fem.py`` solves for the potential with given conductor potentials.  This module chooses those
potentials and combines the solutions into the capacitances that a circuit sees, explains why each
combination is the right one, and records where in the layout (in which material) the coupling
is stored.

1. The capacitance matrix as an energy
--------------------------------------
Let conductors (nets) 1..n be at potentials V_1..V_n, with ground (net "gnd", the enclosure if
grounded, and every other conductor held at 0 V) at 0 V.  By linearity of Laplace's equation the
potential is phi = sum_j V_j psi_j, where psi_j is the solution with net j at 1 V and all others at
0 V, and the charges are Q_i = sum_j C_ij V_j (Maxwell's capacitance matrix).  The entries are
field integrals:

    C_ij = a(psi_i, psi_j) = int eps grad psi_i . grad psi_j dV.                          (1)

Proof.  Green's first identity on the dielectric region Omega with outward normal n gives
    a(psi_i, psi_j) = oint_{boundary of Omega} psi_i eps d(psi_j)/dn dS - int psi_i div(eps grad psi_j) dV.
The volume term vanishes by Laplace's equation (and the interface terms by flux continuity, fem.py
Step 4).  On the boundary, eps d(psi_j)/dn = 0 on insulating faces, and psi_i is 1 on net i and 0 on
every other connected conductor and on grounded faces.  On a floating conductor f, psi_i is not 0
but its own constant potential U_f; that term is U_f oint_f eps d(psi_j)/dn dS = U_f Q_f, and it
vanishes because a floating conductor carries no net charge.  What remains is
oint_{net i} eps d(psi_j)/dn dS.  The charge on a conductor is its surface charge density
sigma = eps E . n_c integrated over its surface, where n_c points out of the conductor, i.e.
n_c = -n, and E = -grad psi_j; so sigma = eps grad psi_j . n and the remaining integral is the charge
on net i when net j is at 1 V, which is C_ij.  (Matrix C is symmetric because a(.,.) is.)

2. The feedback capacitance is the mutual capacitance
------------------------------------------------------
In a transimpedance amplifier the feedback resistor joins the output (net A) to the inverting
input (net B), which the amplifier holds at virtual ground.  A swing V_A of the output induces on B
the charge Q_B = C_BA V_A (with V_B = 0), so a current jw C_BA V_A flows onto B from the
circuit.  C_BA is never positive.  psi_A, the potential with A at 1 V and everything else at 0 V,
obeys the maximum principle (a solution of Laplace's equation takes its extremes on the boundary;
the companion note uses this for its Rule 6), so 0 <= psi_A <= 1.  Next to B, where psi_A = 0, it
therefore cannot decrease into the dielectric: d(psi_A)/dn_c >= 0, with n_c pointing out of B.  The
charge density on B, sigma = -eps d(psi_A)/dn_c, is then nowhere positive, so Q_B = C_BA <= 0.  The
current that the coupling delivers into node B is jw (-C_BA) V_A, and the capacitance in parallel
with the resistor is therefore

    C_F = -C_AB.                                                                           (2)

This is Section G.2.2 of the companion note.  The capacitance of each node to ground (all other
conductors) is the row sum, C_A0 = C_AA + C_AB, the charge on A when A and B are both at 1 V.

3. With a resistive film between A and B
-----------------------------------------
A film joining A to B is not one conductor: its potential varies along it.  The companion note
(Section G.2.3, Eqs. (G.6)-(G.9)) shows that to first order in frequency the admittance between
A and B is 1/R + jw C_F with the expression (3) below.  The terms left out are of second order in
omega R C, with C the capacitance that loads the film; for a uniform RC line they are a conductance
7 (omega R C)^2 / 360 relative to 1/R and a change of 31 (omega R C)^2 / 2520 relative to C_F (the
note's paragraph after Eq. (G.8); geometry.LinearProfile).  The result is

    C_F = -v^T C u,                                                                        (3)

where C is the capacitance matrix of all conductors with the film divided into many small pieces,
u is the vector of their DC potentials when A is at 1 V and B at 0 V, and v = 1 - u (the potentials
when B is at 1 V and A at 0 V).  By (1) and linearity, v^T C u = a(phi_v, phi_u), where phi_u is the
field with A at 1 V, B at 0 V and the film at its DC potential u, and phi_v the field with A at 0 V,
B at 1 V and the film at v.  Hence the field form used here,

    C_F   = -a(phi_u, phi_v),                                                              (4)
    C_A0  =  a(phi_u, phi_u + phi_v),     C_B0 = a(phi_v, phi_u + phi_v),                    (5)

the shunts to ground at the two ends (the note's u^T C (u + v) and v^T C (u + v)).  Without a film
(4)-(5) reduce to (2) and the row sums, since then phi_u = psi_A and phi_v = psi_B.

4. Mirror symmetry: half or a quarter of the work, exactly
-----------------------------------------------------------
Suppose the layout is its own mirror image under x -> -x when A and B are exchanged (a resistor
centred at x = 0), and the film profile satisfies u(-x) = 1 - u(x).  Split each drive into its even
and odd parts:
    phi_e = (phi_u + phi_v)/2   : A at 1/2, B at 1/2, film at 1/2,
    phi_o = (phi_u - phi_v)/2   : A at +1/2, B at -1/2, film at u - 1/2.
By the symmetry and the uniqueness of the solution, phi_e(-x) = phi_e(x) and phi_o(-x) = -phi_o(x).
(The mirror image of a solution solves the mirrored problem, which is the same problem; the
solution is unique; so the solution equals its mirror image, up to the sign that the odd data
carry.)  Two consequences on the plane x = 0: an odd function vanishes there, so phi_o = 0 is a
Dirichlet condition; an even function has zero x-derivative there, so the normal flux of phi_e
vanishes, which is the natural (Neumann) condition and needs nothing imposed.  Each part can thus be
solved on the half x >= 0 alone.

Substituting phi_u = phi_e + phi_o and phi_v = phi_e - phi_o into (4)-(5):
    -a(phi_u, phi_v) = a(phi_o, phi_o) - a(phi_e, phi_e)      (the cross terms cancel),
    a(phi_u, phi_u + phi_v) = 2 a(phi_e, phi_e) + 2 a(phi_o, phi_e) = 2 a(phi_e, phi_e),
because a(phi_o, phi_e) is the integral of an odd function over a symmetric domain and vanishes.
Each energy over the full domain is twice its value over the half, because |grad phi|^2 is even.
A further mirror y -> -y with nets unchanged makes both parts even in y (zero flux on y = 0) and
doubles once more.  With f = 2^(number of mirror planes):

    C_F  = f [ a_h(phi_o, phi_o) - a_h(phi_e, phi_e) ],    C_A0 = C_B0 = 2 f a_h(phi_e, phi_e),   (6)

with a_h the energy form over the computed part.  Nothing is approximated: (6) equals (4)-(5).

5. What the material shares mean
---------------------------------
The integral in (4) is a sum over elements, so C_F splits into shares, one per material: board,
alumina, air, and so on.  The share of material k is
    S_k = -int_{material k} eps grad phi_u . grad phi_v dV = f [ a_h,k(phi_o) - a_h,k(phi_e) ],
the part of (6) below that lies in that material.  The shares add up to C_F exactly.  They are not
the capacitances of separate sub-problems, and they are not energies (a share can be negative where
the even field is stronger than the odd one).  What they are, exactly, is a sensitivity:

    S_k = eps_k dC_F/d(eps_k),   i.e.  S_k = dC_F / d(ln eps_k).                            (7)

Proof.  Each energy in (6) is a minimum over potentials whose prescribed values do not depend on
the permittivities, E(eps) = min_phi a_eps(phi, phi).  Changing eps_k changes the minimum, to first
order, only through the explicit eps_k in a_eps, not through the minimiser (the first-order change of
the minimiser does not change a stationary value).  So dE/d(eps_k) = int_{material k} |grad phi|^2 dV,
and eps_k dE/d(eps_k) is the energy in material k.  Applying this to both energies of (6) gives (7).
The shares add up to C_F because C_F is homogeneous of degree 1 in the permittivities (scaling all of
them by s scales every energy by s), and for such a function Euler's theorem gives
sum_k eps_k dC_F/d(eps_k) = C_F.  So a share answers a design question exactly: raising material k's
permittivity by 1 % raises C_F by S_k x 1 %.

6. Signs and checks
-------------------
Without a film, C_F = -C_AB >= 0 by the maximum-principle argument of section 2.  With a film the
sign is not fixed: the film's own coupling to ground enters (3) with a negative weight (the
companion note's Eq. (G.10), a term -C_g/6 for a film coupled only to ground), and a film close to a
ground plane can in principle make C_F negative.  Each computed energy is an upper bound for its
exact value (fem.py), but C_F is a difference of two of them and has no such guarantee; ``study.py``
therefore estimates its discretisation error by refinement.  The sum of the shares is compared with
C_F as a consistency check of the assembly.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

import numpy as np

from .constants import CAPACITANCE_UNIT_2D, CAPACITANCE_UNIT_3D
from .fem import Problem
from .geometry import Dielectric


@dataclass
class TwoPortResult:
    """Capacitances between nets A and B of a layout, and where the coupling is stored."""

    C_F: float
    C_A0: float
    C_B0: float
    unit: str
    method: str
    contributions: dict[str, float]
    energies: dict[str, float]
    checks: dict[str, float]
    mesh: dict = field(default_factory=dict)
    fem: dict = field(default_factory=dict)
    fields: dict | None = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d.pop("fields", None)
        return d


def _labels(problem: Problem) -> np.ndarray:
    """A material label for every element ('conductor' for conductor elements)."""
    lay, md = problem.layout, problem.md
    labels = np.empty(md.t.shape[1], dtype=object)
    for k in np.unique(md.owner):
        sel = md.owner == k
        if k < 0:
            labels[sel] = lay.enclosure.material.name
        else:
            role = lay.items[k].role
            labels[sel] = role.name if isinstance(role, Dielectric) else "conductor"
    return labels


def _shares(problem: Problem, per_element: np.ndarray) -> dict[str, float]:
    labels = _labels(problem)
    out: dict[str, float] = {}
    for lab in np.unique(labels):
        if lab == "conductor":
            continue
        out[str(lab)] = float(per_element[labels == lab].sum())
    return out


def two_port(problem: Problem, a: str = "A", b: str = "B", keep_fields: bool = False) -> TwoPortResult:
    """C_F, C_A0 and C_B0 between nets ``a`` and ``b`` (Eqs. (4)-(6) of the module docstring)."""
    lay, md = problem.layout, problem.md
    f = 2 ** (int(md.clipped.get("x", False)) + int(md.clipped.get("y", False)))
    unit = CAPACITANCE_UNIT_3D if md.dim == 3 else CAPACITANCE_UNIT_2D
    sym_even = {ax: "even" for ax, c in md.clipped.items() if c}

    if md.clipped.get("x", False):
        if tuple(lay.pair) != (a, b):
            raise ValueError(f"the x mirror pairs nets {lay.pair}, but C_F was asked between {a} and {b}")
        # Even part: A and B at 1/2 (the film then sits at 1/2 everywhere), flux-free on x = 0.
        phi_e = problem.solve({a: 0.5, b: 0.5}, sym=sym_even)
        # Odd part: A at +1/2, B at -1/2 (film at u - 1/2), phi = 0 on x = 0.
        phi_o = problem.solve({a: 0.5, b: -0.5}, sym={**sym_even, "x": "odd"})
        E_e, E_o = problem.bilinear(phi_e, phi_e), problem.bilinear(phi_o, phi_o)
        C_F = f * (E_o - E_e)                                   # Eq. (6)
        C_A0 = C_B0 = 2.0 * f * E_e                             # Eq. (6)
        per_el = f * (problem.elemental(phi_o, phi_o) - problem.elemental(phi_e, phi_e))
        energies = dict(a_odd=E_o, a_even=E_e, factor=f)
        method = "mirror"
        fields = dict(phi_even=phi_e, phi_odd=phi_o) if keep_fields else None
    else:
        phi_u = problem.solve({a: 1.0, b: 0.0}, sym=sym_even)
        phi_v = problem.solve({a: 0.0, b: 1.0}, sym=sym_even)
        a_uv = problem.bilinear(phi_u, phi_v)
        C_F = -f * a_uv                                         # Eq. (4)
        C_A0 = f * problem.bilinear(phi_u, phi_u + phi_v)       # Eq. (5)
        C_B0 = f * problem.bilinear(phi_v, phi_u + phi_v)
        per_el = -f * problem.elemental(phi_u, phi_v)
        energies = dict(a_uv=a_uv, factor=f)
        method = "direct"
        fields = dict(phi_u=phi_u, phi_v=phi_v) if keep_fields else None

    shares = _shares(problem, per_el)
    total = sum(shares.values())
    checks = dict(shares_minus_CF=total - C_F, shares_rel=(total - C_F) / C_F if C_F else float("nan"))
    return TwoPortResult(C_F=float(C_F), C_A0=float(C_A0), C_B0=float(C_B0), unit=unit, method=method,
                         contributions=shares, energies=energies, checks=checks,
                         mesh=dict(md.stats), fem=_fem_stats(problem), fields=fields)


def maxwell_matrix(problem: Problem, nets: list[str]) -> tuple[list[str], np.ndarray]:
    """The capacitance matrix C_ij = a(psi_i, psi_j) (Eq. (1)) for the listed nets.

    Each net in turn is set to 1 V with all other connected nets at 0 V.  Films follow their
    terminals (V_lo + (V_hi - V_lo) u), so with films present the entries are the film-loaded
    quantities of Eqs. (4)-(5).  Requires no x mirror: a single net at 1 V is not symmetric
    under the exchange of A and B.  A y mirror is allowed (every net maps to itself)."""
    md = problem.md
    if md.clipped.get("x", False):
        raise ValueError("maxwell_matrix needs a layout without the x mirror; use two_port")
    f = 2 ** int(md.clipped.get("y", False))
    sym = {"y": "even"} if md.clipped.get("y", False) else {}
    psis = [problem.solve({n: 1.0}, sym=sym) for n in nets]
    C = np.array([[f * problem.bilinear(pi, pj) for pj in psis] for pi in psis])
    return list(nets), C


def _fem_stats(problem: Problem) -> dict:
    s = dict(problem.stats)
    s["solves"] = [dict(x) for x in s.get("solves", [])]
    return s
