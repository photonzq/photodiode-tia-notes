# Development probes of the field solver

These scripts were written while the package `pcbcap` and the cases of Section G.14 were built and audited. They are kept as they were run, with their paths made relative to this folder, so that each step of the development can be retraced. Several were written against an earlier interface of the package and may not run against the current one; the package's own checks (`python -m pcbcap.checks list`) and the scripts one folder up are the maintained versions.

| Script | What it did |
|---|---|
| `probe_api.py` | Probed the gmsh and scikit-fem behaviour that the package relies on: how fragmenting volumes with an embedded sheet maps the inputs, physical groups and element types, the degrees of freedom of quadratic elements on a facet, and an exact linear solution with its energy on the unit cube. |
| `smoke_cps.py`, `smoke_cps2.py` | First tests of the two-dimensional solver: coplanar strips in free space against the exact ratio $K(m)/K(1-m)$, now the check `strips_free_space`. |
| `trial3d.py` | First three-dimensional trial of a chip resistor on its pads: element counts, $C_{F,\mathrm{par}}$ and solve times at several refinements with linear and quadratic elements, which set the mesh sizes of the studies. |
| `patch_meshing_sizes.py` | Changed `pcbcap/meshing.py` so that the mesher groups its refinement fields by each item's edge size. |
| `preview_opa846.py` | Drew the three OPA846 layouts from the builder of `g_opa846_3d.py`, to check them by eye before any solve; `inspect_layouts.py` one folder up replaces it. |
| `audit_checks_analytic.py` | Arithmetic and symbolic checks of the package's exact solutions and constants made during the audit of the package: the vacuum permittivity in fF/mm, series plates, the floating slab, coplanar strips. |
| `g14_audit_numeric_checks.py` | Arithmetic and symbolic checks behind the audit of the text of Section G.14, from the records alone: the cross terms of Eqs. (G.52)–(G.53), the edge exponents of Eq. (G.55), the extrapolations of Eqs. (G.56)–(G.57), and the numbers quoted in the text. No solves. |
