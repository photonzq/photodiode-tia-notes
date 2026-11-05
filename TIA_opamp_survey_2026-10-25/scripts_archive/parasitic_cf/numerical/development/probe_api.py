"""Probe the gmsh and scikit-fem behaviour that the package will rely on."""
import numpy as np
import gmsh
import skfem
from skfem import MeshTet, Basis, ElementTetP1, ElementTetP2, asm, condense, solve
from skfem.models.poisson import laplace

print("skfem", skfem.__version__ if hasattr(skfem, "__version__") else "?", "gmsh", gmsh.__version__)

gmsh.initialize()
gmsh.option.setNumber("General.Terminal", 0)
gmsh.model.add("probe")
occ = gmsh.model.occ
b1 = occ.addBox(-1, -1, -1, 2, 2, 2)          # air
b2 = occ.addBox(-0.3, -0.3, -0.3, 0.6, 0.6, 0.3)  # dielectric inside
r1 = occ.addRectangle(-0.2, -0.2, 0.0, 0.4, 0.4)  # sheet on top face of b2 (z = 0)
out, omap = occ.fragment([(3, b1), (3, b2), (2, r1)], [])
occ.synchronize()
print("fragment out:", out)
for i, m in enumerate(omap):
    print("input", i, "->", m)
# size field
gmsh.model.mesh.field.add("Distance", 1)
curves = gmsh.model.getBoundary([(2, t) for (d, t) in omap[2]], combined=False, oriented=False)
print("sheet boundary curves", curves)
gmsh.model.mesh.field.setNumbers(1, "CurvesList", [abs(t) for (d, t) in curves])
gmsh.model.mesh.field.setNumber(1, "Sampling", 50)
gmsh.model.mesh.field.add("Threshold", 2)
gmsh.model.mesh.field.setNumber(2, "InField", 1)
gmsh.model.mesh.field.setNumber(2, "SizeMin", 0.05)
gmsh.model.mesh.field.setNumber(2, "SizeMax", 0.5)
gmsh.model.mesh.field.setNumber(2, "DistMin", 0.02)
gmsh.model.mesh.field.setNumber(2, "DistMax", 0.8)
gmsh.model.mesh.field.setAsBackgroundMesh(2)
for opt in ("Mesh.MeshSizeExtendFromBoundary", "Mesh.MeshSizeFromPoints", "Mesh.MeshSizeFromCurvature"):
    gmsh.option.setNumber(opt, 0)
vols = gmsh.model.getEntities(3)
print("volumes", vols)
for (d, t) in vols:
    gmsh.model.addPhysicalGroup(3, [t], name=f"vol{t}")
gmsh.model.addPhysicalGroup(2, [t for (d, t) in omap[2]], name="sheet")
gmsh.model.mesh.generate(3)
tags, coords, _ = gmsh.model.mesh.getNodes()
print("nodes", len(tags), "max tag", tags.max())
etypes, etags, enodes = gmsh.model.mesh.getElements(3)
print("element types 3D", etypes, [len(e) for e in etags])
# per-volume tets
for (d, t) in vols:
    et, eg, en = gmsh.model.mesh.getElements(3, t)
    print("vol", t, "types", et, "count", [len(e) for e in eg])
# sheet triangles
for (d, t) in omap[2]:
    et, eg, en = gmsh.model.mesh.getElements(2, t)
    print("sheet surface", t, "types", et, "count", [len(e) for e in eg])
gmsh.finalize()

# skfem probes on a tiny mesh
m = MeshTet().refined(2)
print("MeshTet t sorted?", np.all(np.diff(np.sort(m.t, axis=0), axis=0) >= 0), "facets shape", m.facets.shape,
      "facets sorted per column:", np.all(np.diff(m.facets, axis=0) > 0))
e2 = ElementTetP2()
bfull = Basis(m, e2)
sub = np.arange(0, m.t.shape[1], 2)
bsub = Basis(m, e2, elements=sub)
Kf = asm(laplace, bfull)
Ks = asm(laplace, bsub)
print("N dofs", bfull.N, "K full shape", Kf.shape, "K sub shape", Ks.shape, "nnz", Kf.nnz, Ks.nnz)
print("element_dofs shape", bfull.element_dofs.shape, "doflocs shape", bfull.doflocs.shape)
bf = m.boundary_facets()
dofs = bfull.get_dofs(facets=bf[:5])
print("get_dofs(facets) type", type(dofs).__name__, "all()", dofs.all()[:12], "count", len(dofs.all()))
# Check that the per-facet DOFs of P2 include the edge midpoints: 5 facets -> nodes + edges
x = np.zeros(bfull.N)
D = bfull.get_dofs().all()
x[D] = bfull.doflocs[0, D]   # phi = x on the boundary
phi = solve(*condense(Kf, np.zeros(bfull.N), x=x, D=D))
print("linear solution recovered exactly:", np.max(np.abs(phi - bfull.doflocs[0])))
print("energy of phi = x on unit cube:", phi @ Kf @ phi, "(exact 1.0)")
