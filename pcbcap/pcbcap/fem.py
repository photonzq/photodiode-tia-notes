"""The finite-element discretisation: assembly, boundary conditions, solution.

Why this module exists
----------------------
It turns a labelled mesh (``meshing.py``) into a symmetric linear system for the potential and
solves it.  ``capacitance.py`` then reads capacitances off the solutions.  Everything specific to
capacitance lives there; this module only solves "Laplace's equation with these potentials on
these conductors".

The problem being solved: electrostatics only
---------------------------------------------
This module solves an electrostatic boundary-value problem and nothing else.  There is no magnetic
field and therefore no inductance.  No current flows, except that a resistor's film carries the
potential its own current sets (condition (1c) below).  Every material has one real permittivity
that does not depend on frequency.  The conductors' potentials are prescribed, the potential
between them is solved for, and capacitance.py then reads the conductors' charges off the solution.

Where the equation comes from.  Electrostatics assumes that no magnetic flux changes in time.
Faraday's law, curl E = -dB/dt, then reads curl E = 0, so the field is the gradient of a potential,
E = -grad phi.  Dropping dB/dt is exactly what removes inductance from the model.  Gauss's law reads
div D = rho_free, and in a linear, isotropic dielectric D = eps E with eps = eps0 * eps_r.  All free
charge sits on conductor surfaces, which bound the computational region instead of lying inside it,
so rho_free = 0 there.  Substituting E = -grad phi and D = eps E into Gauss's law and multiplying by
-1 gives

    div( eps(r) grad phi ) = 0    in Omega,                                               (1)

where Omega, the dielectric region, is everything inside the enclosure that is not conductor, and
eps is constant inside each dielectric item.  In 2-D the same equation is solved in the (x, z)
cross-section of a layout taken as uniform along y; the capacitances are then per unit length.

Boundary conditions.  Equation (1) determines phi once one condition is given at every point of the
boundary of Omega.  Below, n is the unit normal pointing out of Omega and d/dn = n . grad.
  (1a) Surface of a conductor on a connected net k:   phi = V_k                       (Dirichlet)
       The net "gnd" is always at 0 V, and every net that is not driven in a solve is at 0 V.
  (1b) Surface of a floating conductor f:   phi = U_f, one unknown constant over all of f, and
       zero net charge,  Q_f = oint_f eps d(phi)/dn dS = 0.
       The charge density follows from Gauss's law on a thin pillbox across the surface: inside the
       conductor D = 0, so sigma = D . m, where m = -n is the normal pointing out of the conductor
       into the dielectric; with D = -eps grad phi this is sigma = eps d(phi)/dn.
  (1c) A resistor's film between nets hi and lo:   phi = V_lo + (V_hi - V_lo) u(r)   (Dirichlet)
       Here u rises linearly from 0 at the lo end to 1 at the hi end (geometry.LinearProfile).  This
       is the film's DC potential: at DC its current obeys Ohm's law and charge conservation, so
       phi solves Laplace's equation in the film with the termination potentials at both ends and no
       current through the side edges, and for a rectangular film with its terminations on two
       opposite sides the linear function is the unique solution (derived in geometry.LinearProfile).
       At frequency omega the film also sheds displacement current to its surroundings, and the
       profile stays linear only to first order in omega R C, with R the film's resistance and C the
       capacitance that loads it; the first neglected terms are 7 (omega R C)^2 / 360 in conductance
       and 31 (omega R C)^2 / 2520 in capacitance (geometry.LinearProfile and the companion note
       after its Eq. (G.8)).
  (1d) Enclosure face of type "ground":   phi = 0                                      (Dirichlet)
       Enclosure face of type "open":     eps d(phi)/dn = 0               (homogeneous Neumann)
  (1e) Mirror plane, odd solution:        phi = 0                                      (Dirichlet)
       Mirror plane, even solution:       eps d(phi)/dn = 0               (homogeneous Neumann)
       capacitance.py derives which solution is used for what.
Sheets (zero-thickness conductors and films) are boundaries with two faces; the condition holds on
both faces.  Inside Omega, on an interface between two dielectrics,
  (1f) phi and the normal flux eps d(phi)/dn are continuous.  phi is continuous because a jump
       would be a dipole layer, which a dielectric interface does not carry; the normal flux is
       continuous because the interface carries no free charge.
The two halves of (1f) enter differently.  Continuity of phi is built into the functions the
method uses (Step 1 below requires them to be continuous), so it holds by construction.  Continuity
of the normal flux, like the zero-charge part of (1b), is never imposed: the weak form implies it, as
Step 5 shows.  Such conditions are called natural.

Weak (variational) form, step by step.  In 2-D every step below holds with volumes replaced by
areas, surfaces by curves and edges by corner points.

Step 1, the allowed functions.  Call a function w on Omega admissible if
  * it is continuous and its gradient is square-integrable, so that int eps |grad w|^2 dV is
    finite.  Continuity is needed for two reasons: a jump of w across a surface would make grad w a
    delta function on that surface, with infinite energy; and the interface terms of Step 4
    combine as written only if w has a single value on each interface;
  * it vanishes wherever phi is prescribed: on the conductors of connected nets (1a), on the films
    (1c), and on the Dirichlet halves of (1d) and (1e);
  * it is constant, w = w_f, on each floating conductor f.
The admissible functions are exactly the differences of two candidate potentials.  Two functions
with the same prescribed values differ by one that vanishes there, and two functions that are each
constant on f differ by one that is constant on f.

Step 2, the regions and the smoothness of phi.  Split Omega into the regions Omega_k of constant
permittivity: the part of each dielectric item that no later item covers (geometry.Layout resolves
overlaps in painter's order), plus the enclosure's own medium.  Inside Omega_k, eps is a constant
eps_k, so (1) reads eps_k laplacian(phi) = 0: phi is harmonic there, hence smooth.  It is not smooth
at the edges and corners of conductors.  Consider a straight edge where one dielectric fills the
angle alpha around a conductor at potential V: alpha = 3 pi/2 at the edge of a box, 2 pi at the
edge of a sheet.  In polar coordinates (r, theta) about the edge, the separable solutions of
Laplace's equation are phi = V + c r^nu sin(nu theta).  phi = V on both faces, theta = 0 and
theta = alpha, requires sin(nu alpha) = 0, so the leading term has nu = pi/alpha: 2/3 at a box
edge, 1/2 at a sheet edge.  The gradient therefore grows as r^(pi/alpha - 1), at worst as r^(-1/2).
That is still square-integrable: |grad phi|^2 r dr ~ r^(2 pi/alpha - 1) dr has a finite integral at
r = 0 because 2 pi/alpha - 1 > -1.  Where two dielectrics meet at the edge, the exponent depends on
their permittivity ratio but stays positive, since an exponent <= 0 would make the energy near the
edge infinite.  meshing.py grades the mesh towards the edges because of this singularity.

Step 3, Green's identity.  For each region, the divergence theorem applied to the vector w F gives
int_V w div(F) dV = oint_{dV} w F.n dS - int_V grad(w).F dV; here F = eps grad phi.  Near an edge
the identity is applied to the region with a thin tube of radius rho removed around the edge.  The
integral over the tube's surface is at most (tube area, proportional to rho) times |grad phi|
(proportional to rho^(pi/alpha - 1)), i.e. proportional to rho^(pi/alpha).  That goes to zero with
rho, so in the limit the identity holds as written.  At a corner, a small ball replaces the tube,
with area proportional to rho^2, and the same conclusion follows.  Summing over the regions,

    0 = - sum_k int_{Omega_k} w div(eps grad phi) dV
      = int_Omega eps grad(w).grad(phi) dV - sum_k oint_{boundary of Omega_k} w eps d(phi)/dn_k dS,

where n_k is the outward normal of region k.

Step 4, the surface terms.  They are of three kinds.
  * On the outer boundary of Omega they vanish: w = 0 where phi is prescribed, and
    eps d(phi)/dn = 0 on the Neumann faces.
  * On a floating conductor f, w = w_f is constant and leaves the integral, so the term is
    -w_f oint_f eps d(phi)/dn dS = -w_f Q_f, which is zero by (1b).  For a floating sheet the
    integral runs over both of its faces, and Q_f is the charge on both.
  * An interface between regions k and l appears twice, once with n_k and once with n_l = -n_k.
    Because w is continuous it has a single value there, and the two contributions add to
    -int w (eps_k d(phi_k)/dn_k - eps_l d(phi_l)/dn_k) dS, i.e. w times the jump of the normal
    flux, which is zero by (1f).
So the exact phi satisfies

    a(phi, w) := int_Omega eps grad(phi).grad(w) dV = 0    for every admissible w.          (2)

Step 5, the converse: why the flux half of (1f) and the zero charge of (1b) are natural.  Suppose a
continuous function phi has the prescribed values, is smooth inside each region, and satisfies
(2).  Running Steps 3 and 4 backwards, (2) says that the volume terms -int w div(eps grad phi) dV,
the floating-conductor terms -w_f Q_f and the interface terms add to zero for every admissible w.
Choosing w nonzero only inside one region shows that div(eps grad phi) = 0 there.  With the volume
terms gone, choosing w nonzero only near one patch of one interface shows that the flux jump
vanishes on that patch.  Finally, choosing w = 1 on one floating conductor, falling to 0 within a
short distance of it, shows Q_f = 0.  So a solution of (2) obeys (1), the flux continuity of (1f)
and the zero-charge condition, none of which was imposed.  (The continuity of phi itself was
assumed, through the admissible functions.)  In the finite-element solution these natural
conditions hold in the weak sense of (3), on average against each basis function, and pointwise
only in the limit of a fine mesh; the floating conductor's discrete charge, however, is exactly zero
(paragraph "Floating conductors" below).

Step 6, the energy minimum.  The field energy is W = (1/2) a(phi, phi).  For any admissible w and
any number t,
    a(phi + t w, phi + t w) = a(phi, phi) + 2 t a(phi, w) + t^2 a(w, w),
and phi + t w runs through all functions with the prescribed values as w and t vary (Step 1).  The
term linear in t vanishes for every w exactly when (2) holds.  The quadratic term is positive for
every admissible w that is not identically zero.  eps > 0, so a(w, w) = 0 only if grad w = 0
everywhere, i.e. if w is constant on each connected part of Omega.  Such a w is zero wherever the
part touches a Dirichlet boundary, and it equals w_f where the part touches a floating conductor f,
which passes the same constant to every other part touching f.  So w vanishes identically provided
every connected component of Omega together with its floating conductors touches a Dirichlet
boundary.  This holds whenever the layout has a grounded enclosure face or at least one connected
net and no dielectric pocket is sealed off from them by floating metal alone.  Under that condition
the solution of (2) is the unique minimiser of the energy among all functions with the prescribed
values.  This is Dirichlet's principle (Section G.4.2 of the companion note,
Eq. (G.12)).

Step 7, the prescribed values as a load.  Write phi = phi_D + phi_0, where phi_D is any function
with the prescribed values and phi_0 is admissible.  By linearity of a in its first argument, (2)
becomes
    a(phi_0, w) = - a(phi_D, w)    for every admissible w:
a problem for an admissible unknown, driven by a load that comes from the prescribed potentials.
Its matrix form is Eq. (4) below.

Finite elements.  The potential is approximated by continuous piecewise polynomials of degree 1 or
2 on the mesh (Lagrange elements P1 or P2 [Brenner and Scott 2008]):
    phi_h = sum_j phi_j N_j(r),
where N_j is the basis function of degree of freedom (DOF) j (a node, or for P2 also an edge
midpoint) and phi_j its value there.  Requiring (2) for every basis function w = N_i of a free DOF
gives the linear system

    sum_j K_ij phi_j = 0   for every free i,    K_ij = a(N_j, N_i) = int eps grad N_i . grad N_j dV.   (3)

K is the stiffness matrix: symmetric (a is symmetric), and sparse (N_i and N_j overlap only on
elements sharing both DOFs).  Split the DOFs into free ones (f) and prescribed ones (p); the rows
of (3) for the free DOFs read K_ff phi_f + K_fp phi_p = 0, i.e.

    K_ff phi_f = - K_fp phi_p,                                                              (4)

which is Step 7 with phi_D the finite-element function that has the prescribed values at the
prescribed DOFs and zero at the free ones.  K_ff is positive definite: for any nonzero vector x of
free values, x^T K_ff x = a(w, w) for the admissible function w = sum_{i free} x_i N_i, and
a(w, w) > 0 by Step 6.  So (4) has exactly one solution.

Why each solve over-estimates its energy.  phi_h minimises the energy over a subset of the
functions with the prescribed values: those that are piecewise polynomial on the mesh.  The
minimum over a subset can never lie below the minimum over the whole set, so a(phi_h, phi_h) is
never below the exact minimum.  This needs the elements to reproduce the prescribed data exactly,
and here they do: the conductor potentials are constants and the film potentials are linear, both
polynomials of degree at most 1, the LinearProfile's clip points lie on the film's ends and hence
on mesh lines (geometry.LinearProfile), and boxes and sheets are meshed without any approximation
of their shape.  A user-supplied profile that is not piecewise linear on the mesh is not reproduced
exactly, and the bound is then lost.  A floating conductor's potential is free in both problems
and does not affect the argument.

Two limits of this statement.  First, it holds for each energy separately; C_F is a difference of
two energies (capacitance.py, Eq. (6)) and is bounded in neither direction.  Second, the meshes of a
convergence study are generated afresh at each level, not by subdividing the previous one, so the
trial spaces are not nested: every energy lies above the exact one, but nothing guarantees that it
falls monotonically from level to level.  study.richardson therefore tests that the computed values
approach their limit monotonically before it extrapolates.

Assembly.  K is assembled by scikit-fem [Gustafsson and McBain 2020]: for each element it
integrates grad N_i . grad N_j with a quadrature rule, multiplies by the element's eps, and adds the
result into K.  Two facts make this exact.  First, every element lies in one region: meshing.py
fragments all items against each other before meshing, so no element crosses an item boundary and
eps is constant on each element.  Second, gmsh's first-order tetrahedra and triangles have straight
sides, so the gradients of P2 basis functions are linear in space, their products are quadratic,
and a quadrature rule of degree 2 integrates them exactly (for P1 the gradients are constant).
Elements of a conductor are left out: all their DOFs are prescribed to one value, so the field and
the energy inside them are zero.

Conductors.  Every DOF that lies in or on a conductor of net n gets the potential of net n.  For a
box conductor these are all DOFs of its elements; for a sheet, the DOFs on its element faces
(including P2 edge DOFs).  Films get the potential V_lo + (V_hi - V_lo) u(r) at their DOFs, where u
is the film's profile (geometry.LinearProfile); a linear u is reproduced exactly by P1 and P2.

Floating conductors.  A conductor connected to nothing has an unknown potential and zero net
charge.  All its DOFs are tied to one shared unknown: phi = P phi_r, where P is a 0/1 matrix that
copies the shared value to every DOF of the conductor and leaves other DOFs unchanged.  The test
functions are tied the same way (Step 1: w is constant on f), so Galerkin's condition becomes
P^T K P phi_r = 0 on the free reduced DOFs.  The row of the shared unknown is the sum of the rows of
K over the conductor's DOFs:
    sum_{i in f} (K phi)_i = sum_{i in f} a(phi, N_i) = a(phi, chi_f),   chi_f = sum_{i in f} N_i.
chi_f equals 1 on the conductor: the Lagrange basis functions add up to 1 everywhere, and on the
conductor's own faces every basis function of a DOF outside f is zero.  Away from the conductor
chi_f falls to 0 within one layer of elements.  For the exact potential, Green's identity (Steps 3
and 4, with chi_f in place of w) turns a(phi, chi_f) into the surface integral of chi_f eps d(phi)/dn
over the boundary of Omega, which is oint_f eps d(phi)/dn dS = Q_f, provided chi_f = 1 on f and 0 on
every other boundary.  The second part needs the layer of elements around f not to reach another
conductor, film or grounded face: on a facet shared with such a set chi_f would be nonzero.  With
the graded meshes here, whose elements at a conductor's edges are smaller than the gaps between
conductors, it holds.  The row of the shared unknown then states that the conductor's charge is
zero, Q_f = 0.  For the finite-element solution, a(phi_h, chi_f) is the discrete charge; the equation
makes it exactly zero, and it converges to the true charge of the computed field as the mesh is
refined.

Solving.  System (4), with P applied when floating conductors are present, is solved either by a
sparse direct factorisation (SuperLU through SciPy) or, for large 3-D systems, by the conjugate-
gradient method preconditioned with smoothed-aggregation algebraic multigrid [Bell, Olson and
Schroder 2022].  The iteration is asked for a relative residual |r|/|b| of 1e-10 (r = b - A x for
the system A x = b); an iterative solve whose residual stays above 1e-7 is rejected with an error
(the factorisation reaches rounding level), and the residual reached is recorded with every solve
(stats["solves"]).  The effect of the iteration
error on the energy is second order.  Write the computed potential as phi = phi* + e, with phi* the
exact solution of (4) and e zero on the prescribed DOFs; then
a(phi, phi) = a(phi*, phi*) + 2 a(phi*, e) + a(e, e), and a(phi*, e) = 0 by (3).  The energy error is
therefore a(e, e) = e^T A e, which equals r^T A^-1 r because e = -A^-1 r, and it is at most
|r|^2 / lambda_min(A).  How this compares with the energy that gives the capacitance is not
known without lambda_min, which the solver does not compute.  (Normalising by b^T A^-1 b instead
would mislead: that quantity is the energy of the free unknowns' response to the prescribed values,
which exceeds a(phi*, phi*) by a factor of the order of the domain size over the element size.)  The
size of the iteration error is therefore a matter for a direct check, a repeat of a solve at a
tighter tolerance; the recorded residuals serve that purpose.  The direct factorisation has no such
error beyond rounding.
"""
from __future__ import annotations

import hashlib
import time

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

from .constants import EPS0
from .geometry import GROUND, Box, Conductor, Dielectric, Film, Layout, Rect, Segment, Sheet
from .meshing import MeshData

# Above these numbers of free unknowns the iterative solver is used instead of factorisation.
# These are practical choices, not derived limits.  A sparse LU factorisation of a 3-D finite-element
# matrix fills in strongly: with a nested-dissection ordering its factor has of order N^(4/3) entries
# in 3-D against N log N in 2-D (A. George, SIAM J. Numer. Anal. 10, 345 (1973)), and SuperLU's
# default ordering does no better.  In one trial a 3-D factorisation of 62 000 unknowns took about
# 1.5 GB, so the 3-D limit is set three times lower, where the factorisation needs a few hundred MB
# and is still faster than building the multigrid hierarchy.  The 2-D limit has not been tested at
# its value: the largest 2-D systems solved in this project have about 58 000 unknowns, factorised
# directly without difficulty.
DIRECT_LIMIT = {2: 600_000, 3: 20_000}
# Elements per assembly chunk, which bounds the temporary memory of assembly.  For P2 tetrahedra each
# element contributes 10 x 10 = 100 matrix entries, stored before summation as a value and two
# indices, 24 bytes in all, so one chunk of 150 000 elements holds 150 000 x 100 x 24 B = 0.36 GB of
# triplets, plus the basis gradients at the 4 quadrature points (10 functions x 3 components x 4
# points x 8 B = 960 B per element, 0.14 GB).  The value keeps assembly below about 0.5 GB on top of
# the mesh; it is a choice for a workstation shared with other work.
CHUNK = 150_000


class Problem:
    """Finite-element discretisation of a meshed layout.

    Parameters
    ----------
    layout : the Layout that was meshed.
    md     : its MeshData.
    order  : 1 or 2, the polynomial degree of the Lagrange elements.
    """

    def __init__(self, layout: Layout, md: MeshData, order: int = 2):
        from skfem import Basis, ElementTetP1, ElementTetP2, ElementTriP1, ElementTriP2, MeshTet, MeshTri

        t0 = time.perf_counter()
        self.layout, self.md, self.order, self.dim = layout, md, order, md.dim
        mesh_cls = MeshTet if md.dim == 3 else MeshTri
        # scikit-fem wants C-ordered arrays (it would otherwise copy them and print a notice).
        self.mesh = mesh_cls(np.ascontiguousarray(md.p), np.ascontiguousarray(md.t))
        elem = {(3, 1): ElementTetP1, (3, 2): ElementTetP2, (2, 1): ElementTriP1, (2, 2): ElementTriP2}[(md.dim, order)]()
        self.elem = elem
        # intorder 2 integrates the product of two linear gradients (P2) exactly; for P1 the
        # gradients are constant and any rule is exact.
        self.basis = Basis(self.mesh, elem, intorder=2)
        self.N = self.basis.N

        # --- permittivity of every element (0 for conductor elements, which are not assembled) ---
        self.eps_r_elem = np.zeros(md.t.shape[1])
        self.is_conductor_elem = np.zeros(md.t.shape[1], dtype=bool)
        enc_eps = layout.enclosure.material.eps_r
        for k in np.unique(md.owner):
            sel = md.owner == k
            if k < 0:
                self.eps_r_elem[sel] = enc_eps
                continue
            role = layout.items[k].role
            if isinstance(role, Dielectric):
                self.eps_r_elem[sel] = role.eps_r
            else:
                self.is_conductor_elem[sel] = True

        self.K = self._assemble()
        self._dof_sets()
        self._solvers: dict[str, object] = {}
        self.stats = dict(dofs=self.N, order=order, assemble_seconds=time.perf_counter() - t0)

    # ---------------------------------------------------------------------------------------------
    def _assemble(self) -> sp.csr_matrix:
        """K = sum over dielectric elements of eps0 * eps_r * int grad N_i . grad N_j (Eq. (3))."""
        from skfem import Basis, asm
        from skfem.models.poisson import laplace

        K = sp.csr_matrix((self.N, self.N))
        for eps in np.unique(self.eps_r_elem[~self.is_conductor_elem]):
            elems = np.nonzero((self.eps_r_elem == eps) & ~self.is_conductor_elem)[0]
            for c0 in range(0, len(elems), CHUNK):
                part = elems[c0:c0 + CHUNK]
                # The basis restricted to these elements shares the global DOF numbering, so the
                # matrix it returns is N x N and can be added directly.
                b = Basis(self.mesh, self.elem, intorder=2, elements=part, dofs=self.basis.dofs)
                K = K + (EPS0 * eps) * asm(laplace, b)
        return K.tocsr()

    # ---------------------------------------------------------------------------------------------
    def _facet_index(self, nodes: np.ndarray) -> np.ndarray:
        """Indices of mesh facets (faces in 3-D, edges in 2-D) given by their node lists.

        scikit-fem stores each facet as its sorted node indices.  A facet given by gmsh is sorted the
        same way and encoded, like the stored ones, as one integer (base-N digits), so the lookup is a
        sorted search instead of a Python loop."""
        f = np.sort(self.mesh.facets, axis=0).astype(np.int64)
        q = np.sort(nodes, axis=0).astype(np.int64)
        n = np.int64(self.mesh.p.shape[1])
        # A 3-D key is (i0 n + i1) n + i2 with node indices below n, so the largest key is n^3 - 1,
        # which must stay below 2^63 (int64).  That allows n <= 2^21 = 2 097 152 nodes; 2 000 000 is
        # that bound rounded down.
        if self.dim == 3 and n > 2_000_000:
            raise RuntimeError("facet keys would overflow int64; mesh too large")
        if self.dim == 3:
            fk, qk = (f[0] * n + f[1]) * n + f[2], (q[0] * n + q[1]) * n + q[2]
        else:
            fk, qk = f[0] * n + f[1], q[0] * n + q[1]
        order = np.argsort(fk)
        pos = np.searchsorted(fk[order], qk)
        pos = np.clip(pos, 0, len(fk) - 1)
        idx = order[pos]
        if not np.array_equal(fk[idx], qk):
            raise RuntimeError("a sheet facet is not a facet of the mesh")
        return idx

    def _dof_sets(self) -> None:
        """Collect, once, the DOFs of every net, film, enclosure face and symmetry plane."""
        md, layout, b = self.md, self.layout, self.basis
        self.net_dofs: dict[str, np.ndarray] = {}
        self.floating: dict[str, bool] = layout.nets()
        self.films: list[tuple[Film, np.ndarray]] = []
        parts: dict[str, list[np.ndarray]] = {}
        for k, it in enumerate(layout.items):
            role = it.role
            if isinstance(role, Dielectric):
                continue
            if isinstance(it, (Box, Rect)):
                elems = np.nonzero(md.owner == k)[0]
                if len(elems) == 0:
                    continue   # entirely covered by later items or outside the clipped domain
                dofs = np.unique(b.element_dofs[:, elems])
            else:
                if k not in md.facets:
                    continue
                dofs = b.get_dofs(facets=self._facet_index(md.facets[k])).all()
            if isinstance(role, Film):
                self.films.append((role, np.unique(dofs)))
            else:
                parts.setdefault(role.net, []).append(dofs)
        self.net_dofs = {n: np.unique(np.concatenate(v)) for n, v in parts.items()}

        # Boundary facets of the domain, classified by the face of the box they lie on.
        bf = self.mesh.boundary_facets()
        mid = self.mesh.p[:, self.mesh.facets[:, bf]].mean(axis=1)   # (dim, nbf) facet centroids
        scale = max(v - u for u, v in md.domain.values())
        # A facet lies on a face of the box when its centroid's coordinate equals the face's.  The
        # tolerance must exceed the rounding of coordinates that gmsh puts exactly on the face (a few
        # units of 1e-16 relative, i.e. about 1e-14 mm here) and stay below the distance from the face
        # to the centroid of any facet inside (at least a third of the smallest element, about 1e-3 mm
        # at the finest meshes).  1e-9 of the domain size, 1e-8 to 1e-7 mm, lies far inside that window.
        tol = 1e-9 * scale
        self.face_dofs: dict[str, np.ndarray] = {}
        self.sym_dofs: dict[str, np.ndarray] = {}
        for r, a in enumerate(md.axes):
            lo, hi = md.domain[a]
            for side, val in (("min", lo), ("max", hi)):
                on = bf[np.abs(mid[r] - val) < tol]
                dofs = b.get_dofs(facets=on).all() if len(on) else np.zeros(0, dtype=np.int64)
                if side == "min" and md.clipped.get(a, False):
                    self.sym_dofs[a] = dofs        # the cut plane a = 0 of a mirror symmetry
                else:
                    self.face_dofs[a + side] = dofs

    # ---------------------------------------------------------------------------------------------
    def dirichlet(self, volts: dict[str, float], sym: dict[str, str] | None = None):
        """Prescribed values for one solve.

        volts : potential of each connected net; nets not listed are held at 0 V (they are AC
                grounds), and the net "gnd" is always 0 V.
        sym   : for each clipped axis, "odd" (phi = 0 on the cut plane) or "even" (zero normal flux,
                nothing imposed).  See capacitance.py for when each applies.

        Returns (mask, values) over all DOFs.  The rules, in the order applied:
          1. grounded enclosure faces: 0 V;
          2. the cut plane of an odd solve: 0 V;
          3. films: their linear potential;
          4. connected nets: their potential, overriding 1-3 where they touch, because a
             conductor's potential is the physical one;
          5. floating nets: one potential each, fixed in two situations and free otherwise.
             (a) In an odd solve every floating net is at 0 V.  check_symmetry makes every
                 floating net its own mirror image (a mirror image must carry the same net), and
                 the odd potential obeys phi(-x) = -phi(x), so the single potential U_f of such a
                 net equals -U_f, i.e. U_f = 0.  This holds whether or not the net touches the
                 plane x = 0; a net made of two mirrored pieces is one conductor at 0 V carrying
                 charges +q and -q.  (Companion note, Eq. (G.46): the floating wall at 0 V.)
             (b) If some of its DOFs are already prescribed by rules 1-4, the whole conductor takes
                 that value, since a conductor has one potential; the prescribed values must agree.
             Otherwise its DOFs share one free unknown with zero net charge (_reduction).
        Two configurations are refused because they contradict the model: a connected net at a
        non-zero potential touching the odd cut plane (it would be shorted to its mirror image) or
        touching a grounded enclosure face (it would be shorted to ground).
        """
        sym = sym or {}
        mask = np.zeros(self.N, dtype=bool)
        val = np.zeros(self.N)
        enc = self.layout.enclosure
        grounded_face = np.zeros(self.N, dtype=bool)
        for face, dofs in self.face_dofs.items():                       # rule 1
            if enc.face_condition(face) == "ground":
                mask[dofs] = True
                val[dofs] = 0.0
                grounded_face[dofs] = True
        odd = False
        for a, kind in sym.items():                                      # rule 2
            if kind == "odd":
                odd = True
                mask[self.sym_dofs[a]] = True
                val[self.sym_dofs[a]] = 0.0
            elif kind != "even":
                raise ValueError("symmetry kind must be 'odd' or 'even'")
        for film, dofs in self.films:                                    # rule 3
            vh, vl = self._net_volts(film.hi, volts), self._net_volts(film.lo, volts)
            mask[dofs] = True
            val[dofs] = film.potential(self.basis.doflocs[:, dofs], self.md.axes, vh, vl)
        for net, dofs in self.net_dofs.items():                          # rule 4
            if self.floating.get(net, False):
                continue
            mask[dofs] = True
            val[dofs] = self._net_volts(net, volts)
        for net, dofs in self.net_dofs.items():                          # rule 5
            if not self.floating.get(net, False):
                continue
            if odd:                                                      # (a)
                mask[dofs] = True
                val[dofs] = 0.0
                continue
            pre = dofs[mask[dofs]]                                       # (b)
            if pre.size:
                v = val[pre]
                if np.max(v) - np.min(v) > 1e-12 * max(1.0, float(np.max(np.abs(v)))):
                    raise ValueError(f"floating net {net!r} touches prescribed potentials from {np.min(v):g} "
                                     f"to {np.max(v):g} V; a conductor has one potential")
                mask[dofs] = True
                val[dofs] = float(v[0])
        for net, dofs in self.net_dofs.items():                          # refused configurations
            if self.floating.get(net, False) or self._net_volts(net, volts) == 0.0:
                continue
            for a, kind in sym.items():
                if kind == "odd" and np.intersect1d(dofs, self.sym_dofs[a]).size:
                    raise ValueError(f"net {net!r} touches the plane {a} = 0, where the odd potential is 0")
            if grounded_face[dofs].any():
                raise ValueError(f"net {net!r} at {self._net_volts(net, volts):g} V touches a grounded "
                                 f"enclosure face")
        return mask, val

    @staticmethod
    def _net_volts(net: str, volts: dict[str, float]) -> float:
        if net == GROUND:
            return 0.0
        return float(volts.get(net, 0.0))

    # ---------------------------------------------------------------------------------------------
    def _reduction(self, mask: np.ndarray):
        """The matrix P of the module docstring: one shared unknown per floating net.

        Returns (P, red_mask) where red_mask marks the reduced DOFs that are prescribed."""
        rep = np.arange(self.N)
        for net, dofs in self.net_dofs.items():
            if self.floating.get(net, False):
                dofs = dofs[~mask[dofs]]          # a DOF also prescribed elsewhere stays prescribed
                if len(dofs):
                    rep[dofs] = dofs[0]
        uniq, red = np.unique(rep, return_inverse=True)
        P = sp.csr_matrix((np.ones(self.N), (np.arange(self.N), red)), shape=(self.N, len(uniq)))
        red_mask = np.zeros(len(uniq), dtype=bool)
        red_mask[red[mask]] = True
        return P, red, red_mask

    def solve(self, volts: dict[str, float], sym: dict[str, str] | None = None,
              rtol: float = 1e-10) -> np.ndarray:
        """Solve (3) for the given net potentials and symmetry conditions; return phi at every DOF."""
        mask, val = self.dirichlet(volts, sym)
        P, red, red_mask = self._reduction(mask)
        # Without floating conductors P is the identity; skip the (costly) triple product then.
        Kr = self.K if P.shape[1] == self.N else (P.T @ self.K @ P).tocsr()
        # Prescribed values on the reduced DOFs (all copies of a prescribed DOF carry its value).
        xr = np.zeros(Kr.shape[0])
        xr[red[mask]] = val[mask]
        free = ~red_mask
        A = Kr[free][:, free].tocsr()
        rhs = -Kr[free][:, red_mask] @ xr[red_mask]
        key = hashlib.sha1(red_mask.tobytes() + P.indices.tobytes()).hexdigest()
        t0 = time.perf_counter()
        xf, info = self._linear_solve(key, A, rhs, rtol)
        xr[free] = xf
        phi = P @ xr
        self.stats.setdefault("solves", []).append(dict(free=int(free.sum()), seconds=time.perf_counter() - t0, **info))
        return phi

    def _linear_solve(self, key: str, A: sp.csr_matrix, rhs: np.ndarray, rtol: float):
        """Solve A x = rhs, reusing a factorisation or multigrid hierarchy for the same A."""
        n = A.shape[0]
        if n == 0:
            return np.zeros(0), dict(method="none")
        if key not in self._solvers:
            if n <= DIRECT_LIMIT[self.dim]:
                self._solvers[key] = ("lu", spla.splu(A.tocsc()))
            else:
                import pyamg
                # max_coarse: the multigrid hierarchy stops coarsening at 500 unknowns, where the
                # coarsest system is solved directly in negligible time.  A choice; it affects the
                # iteration count, not the solution, which the residual test below checks.
                ml = pyamg.smoothed_aggregation_solver(A, symmetry="hermitian", max_coarse=500)
                self._solvers[key] = ("amg", ml)
        kind, s = self._solvers[key]
        if kind == "lu":
            x = s.solve(rhs)
            res = np.linalg.norm(A @ x - rhs) / max(np.linalg.norm(rhs), 1e-300)
            return x, dict(method="direct", rel_residual=float(res))
        residuals: list[float] = []
        # maxiter is a ceiling, not a target: if the iteration stops at it without reaching rtol, the
        # residual test below rejects the result.  The iteration count is recorded with each solve.
        x = s.solve(rhs, tol=rtol, accel="cg", maxiter=500, residuals=residuals)
        res = np.linalg.norm(A @ x - rhs) / max(np.linalg.norm(rhs), 1e-300)
        if res > 1e3 * rtol:
            raise RuntimeError(f"AMG-CG did not converge: relative residual {res:.2e}")
        return x, dict(method="amg-cg", iterations=len(residuals) - 1, rel_residual=float(res))

    # ---------------------------------------------------------------------------------------------
    def bilinear(self, phi: np.ndarray, psi: np.ndarray) -> float:
        """a(phi, psi) = phi^T K psi = int eps grad phi . grad psi over the (clipped) domain."""
        return float(phi @ (self.K @ psi))

    def elemental(self, phi: np.ndarray, psi: np.ndarray) -> np.ndarray:
        """Per-element values of int_e eps grad phi . grad psi (zero on conductor elements).

        Their sum equals ``bilinear`` up to rounding; ``capacitance.py`` uses them to say in which
        material the coupling is stored."""
        from skfem import Functional
        from skfem.helpers import dot, grad

        form = Functional(lambda w: dot(grad(w["a"]), grad(w["b"])))
        vals = form.elemental(self.basis, a=self.basis.interpolate(phi), b=self.basis.interpolate(psi))
        out = EPS0 * self.eps_r_elem * vals
        out[self.is_conductor_elem] = 0.0
        return out

    def grad_at_elements(self, phi: np.ndarray) -> np.ndarray:
        """Mean gradient of phi over each element, shape (dim, M); for plots of the field."""
        g = self.basis.interpolate(phi).grad          # (dim, M, quadrature points)
        return g.mean(axis=2)
