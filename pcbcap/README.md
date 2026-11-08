# pcbcap: field solutions for the parasitic capacitances of printed-circuit layouts

`pcbcap` computes the electrostatic capacitances of layouts made of conductors and dielectrics: a chip resistor on its pads, an amplifier's pins, traces, a board with ground planes and cut-outs. It solves Laplace's equation with the finite-element method in two dimensions (cross-sections, per unit length) or three, and it reports each number together with an estimate of how far it is from the exact solution of the model.

It was written for Appendix G of the companion note on balanced-photodiode amplifiers (`TIA_opamp_survey_2026-10-25/`), where it checks the closed-form estimate of the capacitance across the feedback resistor and computes what the closed forms cannot. It is general, however: any layout made of axis-aligned boxes and rectangles can be described and solved.

## What it solves: electrostatics only

`pcbcap` solves electrostatic problems and nothing else. Every conductor is a perfect conductor at a single potential, the space between the conductors is filled with linear, lossless dielectrics, and there is no magnetic field. In each solve the package fixes the potential of every conductor (for example 1 V on one net and 0 V on all others), solves for the potential everywhere between the conductors, and then reads off the charge that each conductor carries. Charge per volt is capacitance.

Fixing the charges and solving for the potentials would describe the same system. The two views are related by $\mathbf Q = \mathbf C\mathbf V$, where $\mathbf C$ is the Maxwell capacitance matrix, and by its inverse $\mathbf V = \mathbf C^{-1}\mathbf Q$. The package prescribes potentials because a fixed potential is imposed directly on the finite-element unknowns, and because each computed field energy is then an upper bound of the exact one (Dirichlet's principle, derived in `pcbcap/fem.py`). The bound holds for each energy, not for $C_F$, which is a difference of two energies; the accuracy of every result is therefore measured by mesh refinement and Richardson extrapolation (`pcbcap/study.py`). The one place where a charge is prescribed is a floating conductor, whose net charge is zero.

**The equation.** Electrostatics assumes that no magnetic flux changes in time. Faraday's law, $\nabla\times\mathbf E = -\partial\mathbf B/\partial t$, then gives $\nabla\times\mathbf E = 0$, so the field derives from a potential, $\mathbf E = -\nabla\varphi$. Gauss's law is $\nabla\cdot\mathbf D = \rho_\mathrm{free}$, with $\mathbf D = \varepsilon_0\varepsilon_r\mathbf E$ in a linear isotropic dielectric. All free charge sits on the conductor surfaces, which bound the computational region, so $\rho_\mathrm{free} = 0$ inside it. Substituting gives the equation that is solved:

$$
\nabla\cdot\bigl(\varepsilon_0\,\varepsilon_r(\mathbf r)\,\nabla\varphi(\mathbf r)\bigr) = 0
\qquad \text{in the dielectric region } \Omega ,
$$

with $\varepsilon_r$ constant inside each dielectric item. In 2-D the same equation is solved in the $(x, z)$ cross-section of a layout that is taken as uniform along $y$; capacitances are then per unit length.

**The boundary conditions.** In the table, $\mathbf n$ is the unit normal pointing out of $\Omega$.

| Where | Condition | Kind |
|---|---|---|
| Surface of a conductor on a connected net $k$ | $\varphi = V_k$; the net `gnd` and every net not driven in a solve are at 0 V | Dirichlet |
| Surface of a floating conductor $f$ | $\varphi = U_f$, one unknown constant, and net charge $Q_f = \oint_f \varepsilon_0\varepsilon_r\,\partial\varphi/\partial n\,\mathrm dS = 0$ | constant potential, zero charge |
| A resistor's film between nets hi and lo | $\varphi = V_\mathrm{lo} + (V_\mathrm{hi} - V_\mathrm{lo})\,u$, with $u$ rising linearly from 0 at the lo end to 1 at the hi end | Dirichlet |
| Enclosure face of type `"ground"` | $\varphi = 0$ | Dirichlet |
| Enclosure face of type `"open"` | $\partial\varphi/\partial n = 0$ (no field line crosses it) | homogeneous Neumann |
| Mirror plane, odd or even solution | $\varphi = 0$ for the odd solution, $\partial\varphi/\partial n = 0$ for the even one | Dirichlet or Neumann |
| Interface between two dielectrics, inside $\Omega$ | $\varphi$ and $\varepsilon_0\varepsilon_r\,\partial\varphi/\partial n$ continuous (no free charge on it) | $\varphi$: built into the continuous elements; flux: natural, implied by the weak form |

The film's potential is its DC potential. For a rectangular film with its terminations on two opposite sides, the linear function is the unique solution of the DC current problem: it is harmonic, it takes the termination potentials, and its normal derivative vanishes on the side edges (`geometry.LinearProfile`). At a frequency $f$ it stays accurate to second order in $2\pi f RC$, with $R$ the film's resistance and $C$ the capacitance that loads it. The first neglected terms are $7(2\pi fRC)^2/360$ in conductance and $31(2\pi fRC)^2/2520$ in capacitance (companion note, after its Eq. (G.8)). This is the only trace of a current in the model. Sheets (zero-thickness conductors and films) are boundaries with two faces, and the condition holds on both.

Neither kind of enclosure face is an infinitely distant boundary. For a 3-D layout in a grounded box, `study.enclosure_correction` extrapolates the result to a box of infinite size; its docstring derives why the change falls as $1/R$. An open box is no model of a distant ground: around a layout with no ground of its own, the even drive stores no energy there, and the result is the two-terminal capacitance $C_m + C_{A0}C_{B0}/(C_{A0}+C_{B0})$ of the pair, not its mutual capacitance $C_m$ (`geometry.Enclosure`). In 2-D the capacitance to a distant ground falls only as $1/\ln R$, so there is no finite limit to extrapolate to. The docstring of `pcbcap/fem.py` derives the equation, the weak form, and why the zero-charge and flux-continuity conditions need no explicit imposition.

**What it does not model.**

- No magnetic field: no self or mutual inductance of pads, traces, vias, pins or resistor bodies, and no skin effect.
- No conduction current apart from the film potential above, and no conductor resistance.
- No frequency dependence: each material has one real permittivity, so there is no loss tangent and no dispersion. These are assumptions about the materials, separate from the quasi-static one; `pcbcap/materials.py` shows that loss changes a capacitance only at second order in the loss tangents.
- No retardation and no radiation.

The results are therefore the low-frequency limit of the capacitive coupling. Three conditions apply when they describe a circuit at a frequency $f$; each is the first-order correction that the model leaves out.

- A capacitance $C$ charged through an inductance $L$ looks like $C/(1-\omega^2LC)$ with $\omega = 2\pi f$, because $1/(j\omega C) + j\omega L = (1-\omega^2LC)/(j\omega C)$. So $\omega^2LC \ll 1$ is needed.
- A resistance $R$ with an inductance $L$ in series acts, in parallel with its capacitance, as a negative capacitance $L/R^2$, because $1/(R+j\omega L) = (R-j\omega L)/(R^2+\omega^2L^2)$. So $L/R^2$ must be small next to that capacitance, which needs $R \gg \sqrt{L/C}$.
- The film's DC profile needs the second-order terms in $2\pi fRC$ given above to be small.

The package does not compute $L$; those checks have to be made separately.

## What it computes

- The **mutual capacitance** $C_F = -C_{AB}$ between two nets: the capacitance in parallel with a feedback resistor joining them. It includes the resistor's own film, whose potential varies along it.
- The **capacitance of each net to ground**, meaning all other conductors.
- **Where the coupling is stored**: the share of $C_F$ in each material (board, alumina, air, mould compound). The shares add up to $C_F$.
- The **Maxwell capacitance matrix** of any set of nets.
- **Error estimates.**
  - The mesh error comes from three meshes and Richardson extrapolation.
  - The effect of the finite enclosure comes from three enclosure sizes and extrapolation to an infinitely distant one.

## How it works, in brief

Each module's docstring derives what that module does; the code comments justify each non-trivial step.

1. **Describing the layout** (`geometry.py`). The layout is a list of boxes and zero-thickness sheets.
   - Each item is a dielectric, a conductor on a named net, or a resistive film between two nets.
   - Overlapping boxes follow painter's order: a later item replaces an earlier one where they overlap.
   - Mirror symmetries can be declared. They are checked, and they let the solver compute a half or a quarter of the layout exactly.
2. **Meshing** (`meshing.py`). gmsh splits all items along each other's boundaries and meshes the result.
   - The elements shrink towards conductor edges, where the field is singular.
   - An element-count estimate refuses meshes that would not fit in memory.
3. **Solving** (`fem.py`). scikit-fem assembles the stiffness matrix with P1 or P2 Lagrange elements.
   - Conductors fix the potential. Floating conductors share one unknown with zero net charge. Films carry their DC potential.
   - The system is solved by sparse factorisation or by multigrid-preconditioned conjugate gradients (PyAMG).
4. **Capacitances** (`capacitance.py`). They are field integrals: $C_{ij} = \int\varepsilon\,\nabla\psi_i\cdot\nabla\psi_j\,\mathrm dV$. With a film, $C_F = -\int\varepsilon\,\nabla\varphi_u\cdot\nabla\varphi_v\,\mathrm dV$, the field form of $-\mathbf v^{\mathsf T}\mathbf C\mathbf u$. The module docstring derives both, and the even/odd decomposition used for symmetric layouts.
5. **Beyond first order in frequency** (`distributed.py`). The capacitances above hold the film at its DC potential, exact to first order in $\omega RC$. When a conductor close under the film (a guard trace, say) loads it with a capacitance several times $C_F$, that order is not enough at the amplifier's bandwidth. The module divides the film into finite elements along its length, solves the capacitance matrix of their hat functions, and adds the film's resistance, which gives the feedback impedance at any frequency. Its low-frequency limit is the $C_F$ of `capacitance.py`.
6. **Error estimates** (`study.py`). Richardson extrapolation over three meshes, and extrapolation in $1/R$ over three grounded enclosure sizes (3-D only). The docstring derives the expected convergence order, $p = 2\nu$ with $\nu$ the smallest edge exponent of the layout (about 0.7–4/3 for these layouts), and why the enclosure error falls as $1/R$ for a layout without its own ground.

## Installing and running

The package needs Python 3.11 or later and NumPy, SciPy, Matplotlib, gmsh, scikit-fem and PyAMG (all from pip). psutil is optional; with it, runs lower their own priority. From this folder:

```bash
python -m pip install -e .
```

Or, without installing, run the commands below from this folder, where Python finds the package directly.

Run a study described by a TOML file (the schema is in `pcbcap/config.py`):

```bash
python -m pcbcap run examples/0402_fr4.toml
```

Use the package from Python:

```python
from pcbcap import parts, study
from pcbcap.meshing import MeshParams
lay = parts.resistor_on_pads(parts.ChipResistor.from_size("0805"), parts.LandPattern.from_size("0805"))
# the 0805 levels of Appendix G; every level must refine with its factor (study.check_levels)
conv = study.converge(lay, factors=(4.0, 3.36, 2.83), params=MeshParams(h_edge=0.00375, h_core=0.045))
print(conv.value(), "fF")
```

`examples/custom_layout.py` builds a layout by hand: two traces with and without a grounded guard. It also computes a Maxwell matrix.

### Parts and packages

`parts.py` builds chip resistors (0201 to 1206) on their land patterns, boards with planes and solder mask, and the pin edge of a WSON package. `packages.py` adds the leaded packages, SOT-23-5, SOIC-8 (gull-wing leads) and PDIP-8 (leads through plated holes), with vias, traces and parts mounted on the bottom side; a resistor can stand along either axis (`resistor_assembly(..., axis="y")`). Each package's docstring gives every dimension with the drawing and page it comes from, and says which dimensions no drawing gives and how they were chosen.

### Looking at a layout

A layout can be checked by eye before anything is meshed. `plotting.draw_views(layout, stem)` draws it from six sides on one sheet (from the front left and the back right above the board, from above, from below, and along x and y) and saves a PNG and a PDF. `webview.write_page(layout, "layout.html")` writes a page that a browser turns, zooms and inspects part by part. It is drawn by plotly (`python -m pip install plotly`, or the extra `web` of this package). Both use the faces of `plotting.visible_faces`, which are also those of the published three-dimensional views. Only surfaces that exist are drawn, the dielectrics are translucent, and the conductors take the colour of their net.

```python
from pcbcap import plotting, webview
plotting.draw_views(lay, "views/my_layout")              # views/my_layout.png and .pdf
webview.write_page(lay, "views/my_layout.html", title="My layout")
```

### Exporting a layout to FasterCap

`fastercap.py` writes a layout as input for FasterCap, a free boundary-element capacitance solver (FastFieldSolvers, LGPL 2.1), so that a result can be checked by a method whose discretisation error has nothing in common with this package's. Its docstring explains how each face of the layout becomes a panel, which translations are exact (the grounded enclosure becomes a closed grounded conductor; a symmetric layout is exported whole) and which are not (a resistive film becomes a row of strip conductors, which overstate $C_F$ by an amount it estimates; a conductor sheet between two permittivities needs a small thickness), and how FasterCap's Maxwell matrix is turned back into $C_F$, $C_{A0}$ and $C_{B0}$.

```python
from pcbcap import fastercap as fc
ex = fc.export(lay, "out/my_layout", "my_layout", fc.ExportOptions(boundary="ground", film_strips=20))
check = fc.compare_areas(ex.panels.areas_by_key(), fc.gmsh_areas(ex.layout, "ground"))   # geometry check
fc.draw_panels(ex, "out/my_layout_views")                                                # look at it
text = fc.run_fastercap("FasterCap.exe", "out/my_layout/my_layout.lst", ("-a0.001",))
print(fc.two_port(ex.meta, *fc.read_matrix(text)))
```

The panels come from cells of the layout's planes, classified by the painter's order; `gmsh_areas` finds the area of every kind of panel a second way, from gmsh's fragments, and the two must agree (checks `fastercap_export_box` and `fastercap_export_free`). The companion note's `scripts_archive/parasitic_cf/numerical/fastercap_validation.py` uses this to check Section G.14; its results and convergence tables are in `data/parasitic_cf/fastercap/README.md`.

### Cost

A quarter of a 3-D chip resistor at the finest mesh used in Appendix G has a few hundred thousand elements (0.34 million for the 0402 at refine 2) and takes one to two minutes per solve. The full-domain feedback networks with an amplifier package take 0.6–1.0 million elements and 0.8–1.3 million unknowns; the OPA846 cases used about 3.5–4.5 GB each. The 2-D cases take seconds. Every run lowers its priority and limits itself to two threads, because it is meant to run on a workstation that is in use.

## Checks

`python -m pcbcap.checks list` lists the checks against exact solutions and internal identities. Run each one alone:

```bash
python -m pcbcap.checks run strips_free_space
```

Each check prints what it exercises, the mesh, the computed and reference values, the relative error, its tolerance and the time. It does not abort on failure, so the output shows what went wrong. Current results (relative error, with the tolerance in brackets):

| Check | Exercises | Result |
|---|---|---|
| strips_free_space | edge singularities, open enclosure, mirror shortcut | $1.0\times10^{-4}$ ($3\times10^{-4}$) |
| strips_on_interface | dielectric interface through the conductors | $1.0\times10^{-4}$ ($3\times10^{-4}$) |
| mirror_vs_full | even/odd decomposition against the full solve | $6.7\times10^{-6}$ ($2\times10^{-4}$) |
| layered_plates_2d, layered_plates_3d | flux continuity at interfaces, 3-D mesher | $1\times10^{-14}$, $3\times10^{-16}$ ($10^{-9}$) |
| floating_slab | floating conductor, zero net charge | $5\times10^{-15}$ ($10^{-9}$) |
| film_linear_block | prescribed film potential | $3\times10^{-15}$ ($10^{-9}$) |
| extrusion_3d_vs_2d | 3-D against 2-D, edge convergence, Richardson extrapolation | $-5.9\times10^{-4}$ (its own reported error, $2.8\times10^{-3}$) |
| symmetry_declaration | a false symmetry is rejected | rejected |
| resistor_section_shares | builder, film, material shares | $3\times10^{-13}$ ($10^{-9}$) |
| uniform_rc_line | the film as finite elements (`distributed.py`) against the exact uniform RC line, for both admittances; no mesh | $1.2\times10^{-3}$ ($10^{-2}$) on the convergence order, 2.002 against 2 |
| fastercap_export_box | export of an 0402 for FasterCap with its film as strips and the grounded box as a conductor: the panels' areas, kind by kind, against gmsh's fragments | $0$ ($10^{-9}$) |
| fastercap_export_free | the same in free space, with a board of finite size and the film removed | $4\times10^{-16}$ ($10^{-9}$) |
| fastercap_reader | reading FasterCap's matrix, eliminating a floating conductor and forming $C_F$ with film strips, against a direct computation | $0$ ($10^{-12}$) |

The values are those recorded in `TIA_opamp_survey_2026-10-25/data/parasitic_cf/numerical/checks.json`. In the extrusion check the errors of the three 3-D meshes against the exact 2-D value fall with local orders 0.94 and 1.02, close to the order 1 expected for a sheet edge; the three-level extrapolation, which does not know the exact value, finds 0.86 and lands $5.9\times10^{-4}$ below it, inside the error it reports.

In addition, the scripts of Appendix G reproduce every closed form of that appendix to $10^{-6}$–$10^{-4}$: `TIA_opamp_survey_2026-10-25/scripts_archive/parasitic_cf/numerical/g_closed_forms_2d.py`.

## Limits

- **Geometry.** Items are axis-aligned boxes, rectangles and line segments. A solder fillet, for example, is approximated by a staircase of boxes.
- **Physics.** Electrostatics: no inductance, no retardation (the three conditions above). Separately, the dielectrics are lossless and their permittivity does not depend on frequency, which are assumptions about the materials.
- **Films.** Films have zero thickness. A plain rectangular film carries a linear potential; a patterned film needs its DC potential supplied as a function, which the elements then reproduce only approximately.
- **Enclosure.** The enclosure is a grounded or insulating box. For a 3-D layout in a grounded box, `study.enclosure_correction` extrapolates the result to an infinitely distant ground; an insulating box models an isolated pair instead. Real grounds near a layout, such as planes or pins, belong in the layout itself.

## References

- C. Geuzaine and J.-F. Remacle, "Gmsh: A 3-D finite element mesh generator with built-in pre- and post-processing facilities", *Int. J. Numer. Methods Eng.* **79**(11), 1309–1331 (2009). https://doi.org/10.1002/nme.2579
- T. Gustafsson and G. D. McBain, "scikit-fem: A Python package for finite element assembly", *J. Open Source Softw.* **5**(52), 2369 (2020). https://doi.org/10.21105/joss.02369
- N. Bell, L. N. Olson and J. Schroder, "PyAMG: Algebraic Multigrid Solvers in Python", *J. Open Source Softw.* **7**(72), 4142 (2022). https://doi.org/10.21105/joss.04142
- S. C. Brenner and L. R. Scott, *The Mathematical Theory of Finite Element Methods*, 3rd ed., Springer (2008): the variational formulation (Chapter 2) and the Lagrange elements (Chapter 3). https://doi.org/10.1007/978-0-387-75934-0
- I. Babuška and A. K. Aziz, "On the angle condition in the finite element method", *SIAM J. Numer. Anal.* **13**(2), 214–226 (1976). https://doi.org/10.1137/0713021
- M. Křížek, "On the maximum angle condition for linear tetrahedral elements", *SIAM J. Numer. Anal.* **29**(2), 513–520 (1992). https://doi.org/10.1137/0729031
- A. George, "Nested dissection of a regular finite element mesh", *SIAM J. Numer. Anal.* **10**(2), 345–363 (1973). https://doi.org/10.1137/0710032
- E. Tiesinga, P. J. Mohr, D. B. Newell and B. N. Taylor, "CODATA recommended values of the fundamental physical constants: 2018", *Rev. Mod. Phys.* **93**, 025010 (2021). https://doi.org/10.1103/RevModPhys.93.025010
- L. F. Richardson and J. A. Gaunt, "The deferred approach to the limit", *Phil. Trans. R. Soc. A* **226**, 299–361 (1927). https://doi.org/10.1098/rsta.1927.0008
