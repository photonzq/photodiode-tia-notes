"""Physical constants and the unit system of the package.

Why this module exists
----------------------
Every number in the package is a length, a permittivity or a capacitance.  Choosing the units once,
here, and deriving the one constant that depends on that choice keeps the rest of the code free of
conversion factors that a reader would otherwise have to check line by line.

The unit system
---------------
* Lengths are in millimetres (mm).  A chip resistor is 0.6-2 mm long and a board 1.6 mm thick, so
  every coordinate is a number of order 0.01-100.  The choice of length unit does not change the
  conditioning of the linear system: under a change of scale x -> lambda x, every entry
  int eps grad N_i . grad N_j dV of the stiffness matrix scales by lambda^(d-2) (gradients by 1/lambda
  each, the volume element by lambda^d), so the whole matrix is multiplied by one number and its
  condition number is unchanged.  The unit does matter for the geometry kernel: gmsh and its
  OpenCASCADE kernel use absolute tolerances (of order 1e-7 in model units) when they intersect and
  fragment shapes, so coordinates of order 1 in mm keep every feature (15 um and up) far above them.
* Capacitances are in femtofarads (fF) for three-dimensional models and in femtofarads per
  millimetre (fF/mm) for two-dimensional cross-sections, which describe a structure that is uniform
  along the third axis.
* Potentials are in volts.  The problem is linear, so a solution for one set of conductor potentials
  scales with them, and capacitance (charge per volt) does not depend on the voltage used.  The
  drives are chosen so that the formulas of capacitance.py need no rescaling: 1 V and 0 V on two nets,
  or +1/2 V and -1/2 V (odd drive) and +1/2 V on both (even drive) in the mirror-symmetric shortcut.

The vacuum permittivity in these units
---------------------------------------
The SI value recommended by CODATA 2018 [E. Tiesinga, P. J. Mohr, D. B. Newell and B. N. Taylor,
"CODATA recommended values of the fundamental physical constants: 2018", Rev. Mod. Phys. 93, 025010
(2021)], also used by the analytic script of the companion note, is

    eps0 = 8.8541878128(13) x 1e-12 F/m.

One farad per metre equals 1e15 fF per 1e3 mm = 1e12 fF/mm.  Hence

    eps0 = 8.8541878128e-12 * 1e12 fF/mm = 8.8541878128 fF/mm.

Check of the scaling: a parallel-plate capacitor of area A (mm^2) and gap d (mm) has
C = eps0 * eps_r * A / d, which with A in mm^2 and d in mm gives (fF/mm) * mm = fF, as required.
The "(13)" is the standard uncertainty in the last two digits, a relative 1.5e-10.  Later
adjustments move the value by amounts of that order, far below every other uncertainty here.
"""

EPS0 = 8.8541878128
"""Vacuum permittivity in fF/mm (see the module docstring for the conversion)."""

LENGTH_UNIT = "mm"
CAPACITANCE_UNIT_3D = "fF"
CAPACITANCE_UNIT_2D = "fF/mm"
