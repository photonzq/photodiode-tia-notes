"""pcbcap: electrostatic field solutions for the parasitic capacitances of printed-circuit layouts.

Scope: electrostatics only
--------------------------
pcbcap solves electrostatic problems and nothing else.  Every conductor is a perfect conductor at
a single potential, the space between conductors is filled with linear, lossless dielectrics, and
there is no magnetic field.  In each solve the package fixes the potential of every conductor (for
example 1 V on one net and 0 V on all others), solves for the potential everywhere between the
conductors, and then reads off the charge that each conductor carries.  Charge per volt is
capacitance.

Fixing the charges and solving for the potentials would describe the same system.  The two views
are related by Q = C V, with C the Maxwell capacitance matrix, and by its inverse V = C^-1 Q.  The
package prescribes potentials because a fixed potential is imposed directly on the finite-element
unknowns, and because each computed field energy is then an upper bound of the exact one
(Dirichlet's principle, derived in fem.py).  The bound holds for each energy, not for C_F, which is
a difference of two energies (capacitance.py); the accuracy of every result is therefore measured
by mesh refinement and Richardson extrapolation (study.py).  The one place where a charge is
prescribed is a floating conductor, whose net charge is zero.

The equation solved.  Electrostatics assumes that no magnetic flux changes in time.  Faraday's law,
curl E = -dB/dt, then gives curl E = 0, so the field derives from a potential, E = -grad(phi).
Gauss's law is div D = rho_free, with D = eps0 eps_r E in a linear isotropic dielectric.  All free
charge sits on the conductor surfaces, which bound the computational region, so rho_free = 0
inside it.  Substituting gives the equation that is solved:

    div( eps0 eps_r(r) grad phi(r) ) = 0      in the dielectric region Omega,

with eps_r constant inside each dielectric item.  In 2-D the same equation is solved in the (x, z)
cross-section of a layout that is taken as uniform along y; capacitances are then per unit length.

The boundary conditions.  The solver class fem.Problem imposes them, and the docstring of fem.py
derives the ones that need no explicit imposition.  The normal n points out of Omega.
  1. Surface of a conductor on a connected net k:  phi = V_k (Dirichlet).  The net "gnd" is always
     at 0 V, and every net that is not driven in a solve is at 0 V.
  2. Surface of a floating conductor f:  phi = U_f, one unknown constant over the whole conductor,
     with net charge zero:  Q_f = (closed surface integral over f of eps0 eps_r dphi/dn) = 0.
  3. A resistor's film between nets hi and lo:  phi = V_lo + (V_hi - V_lo) u, where u rises
     linearly from 0 at the lo end to 1 at the hi end (Dirichlet).  This is the film's DC
     potential: for a rectangular film with its terminations on two opposite sides, the linear
     function is the unique solution of the DC current problem (geometry.LinearProfile derives it).
     At frequency f it stays accurate to second order in 2 pi f R C, with R the film's resistance
     and C the capacitance that loads it (geometry.LinearProfile gives the neglected terms).  It is
     the only trace of a current in the model.
  4. Enclosure face of type "ground":  phi = 0 (Dirichlet).  Face of type "open":  dphi/dn = 0
     (homogeneous Neumann: no field line crosses it).  Neither is an infinitely distant boundary.
     For a 3-D layout in a grounded box, study.enclosure_correction extrapolates the result to a
     box of infinite size.  An open box is no model of a distant ground: around a layout with no
     ground of its own it gives the two-terminal capacitance of the pair (geometry.Enclosure).
  5. Mirror plane, when only half or a quarter of a symmetric layout is solved:  phi = 0 for the
     odd solution and dphi/dn = 0 for the even one (capacitance.py derives which is used when).
  6. Interface between two dielectrics, inside Omega:  phi and eps0 eps_r dphi/dn are continuous
     (no free charge on the interface).  Continuity of phi is built into the elements; continuity
     of the flux follows from the weak form without being imposed (fem.py, Step 5).
Sheets (zero-thickness conductors and films) are boundaries with two faces, and the condition holds
on both faces.

What the package does not model.
  * No magnetic field: no self or mutual inductance of pads, traces, vias, pins or resistor bodies,
    and no skin effect.
  * No conduction current apart from the film potential of condition 3, and no conductor resistance.
  * No frequency dependence: each material has one real permittivity, so there is no loss tangent
    and no dispersion (materials.py shows that loss changes a capacitance only at second order).
  * No retardation and no radiation.
The results are therefore the low-frequency limit of the capacitive coupling.  When they describe a
circuit at a frequency f, three conditions apply, each the first-order correction the model leaves
out:
  * a capacitance C charged through an inductance L looks like C / (1 - (2 pi f)^2 L C), because
    the series impedance 1/(j w C) + j w L equals (1 - w^2 L C)/(j w C); so (2 pi f)^2 L C << 1;
  * a resistance R with an inductance L in series acts, in parallel with its capacitance, as a
    negative capacitance L / R^2, because 1/(R + j w L) = (R - j w L)/(R^2 + w^2 L^2); so this
    should be small next to the capacitance, which needs R much above sqrt(L / C);
  * the film's DC profile needs the second-order terms in 2 pi f R C of condition 3 to be small.
The package does not compute L; those checks have to be made outside it.

What it computes
----------------
For a layout of conductors and dielectrics (a chip resistor on its pads, an amplifier's pins, a
board with planes) the package solves Laplace's equation with the finite-element method and returns
  * the mutual capacitance C_F = -C_AB between two nets (the parasitic capacitance across a
    feedback resistor), including the effect of the resistor's own film,
  * the capacitance of each net to ground,
  * how the mutual capacitance is shared between the materials (board, body, air, ...),
  * the full Maxwell capacitance matrix of any set of nets,
with error estimates from mesh refinement and from the size of the enclosure.

How the package is organised (read the modules in this order)
-------------------------------------------------------------
constants.py    units (mm, fF) and the vacuum permittivity in them
materials.py    permittivities with their sources
geometry.py     the layout vocabulary: boxes, sheets, nets, films, enclosure, mirror symmetry
parts.py        builders: chip resistors, land patterns, boards, planes, solder mask, WSON pins
meshing.py      layout -> labelled mesh (gmsh)
fem.py          the finite-element system: assembly, conditions, solution (scikit-fem, PyAMG)
capacitance.py  capacitances from the solutions, with their derivations
study.py        mesh-convergence and enclosure-size extrapolation, sweeps
analytic.py     exact solutions used by the tests
plotting.py     figures of layouts, meshes and fields
config.py       building a run from a TOML file;  ``python -m pcbcap`` runs one

Minimal example
---------------
>>> from pcbcap import parts, study
>>> from pcbcap.meshing import MeshParams
>>> lay = parts.resistor_on_pads(parts.ChipResistor.from_size("0402"), parts.LandPattern.from_size("0402"))
>>> conv = study.converge(lay, factors=(4.0, 2.83, 2.0),            # the companion note's 0402 levels:
...                       params=MeshParams(h_edge=0.00375, h_core=0.045))   # 86 000 to 0.34 million
>>> conv.value()                        # C_F in fF, enclosure at 10 mm    # elements, about 5 minutes
"""
from . import analytic, capacitance, constants, fem, geometry, materials, meshing, parts, study
from .capacitance import TwoPortResult, maxwell_matrix, two_port
from .fem import Problem
from .geometry import Box, Conductor, Dielectric, Enclosure, Film, Layout, LinearProfile, Rect, Segment, Sheet
from .meshing import MeshData, MeshParams, build_mesh
from .study import converge, enclosure_correction, solve_layout, sweep

__version__ = "1.0.0"
