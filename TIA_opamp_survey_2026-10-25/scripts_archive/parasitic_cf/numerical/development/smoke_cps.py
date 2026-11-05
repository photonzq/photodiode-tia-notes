"""Smoke test: coplanar strips in free space, 2-D, against the exact K(m)/K(1-m) result."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[5] / "pcbcap"))
from scipy.special import ellipk, ellipkm1

from pcbcap.constants import EPS0
from pcbcap.geometry import Layout, Film, LinearProfile
from pcbcap.meshing import MeshParams
from pcbcap.study import solve_layout, converge

s, w = 0.5, 0.5
m = (w / (s + w)) ** 2
exact = 2 * EPS0 * ellipk(m) / ellipkm1(m)
print("exact C' =", exact, "fF/mm")

for sym in (True, False):
    lay = Layout(2, "cps")
    lay.add_segment("z", 0.0, (s / 2, s / 2 + w), net="A", name="A")
    lay.add_segment("z", 0.0, (-s / 2 - w, -s / 2), net="B", name="B")
    lay.set_enclosure({"x": (-60, 60), "z": (-60, 60)}, boundary="open")
    lay.set_symmetry(mirror_x=sym)
    for order in (1, 2):
        t0 = time.perf_counter()
        res = solve_layout(lay, MeshParams(h_edge=0.01, h_core=0.05, h_far=6.0), order=order)
        print(f"sym={sym} P{order}: C' = {res.C_F:.6f}  rel err {res.C_F/exact-1:+.2e}  C_A0 {res.C_A0:.3e} "
              f"dofs {res.fem['dofs']} {time.perf_counter()-t0:.1f}s  method {res.method} shares {res.contributions} check {res.checks}")

lay = Layout(2, "cps")
lay.add_segment("z", 0.0, (s / 2, s / 2 + w), net="A", name="A")
lay.add_segment("z", 0.0, (-s / 2 - w, -s / 2), net="B", name="B")
lay.set_enclosure({"x": (-60, 60), "z": (-60, 60)}, boundary="open")
lay.set_symmetry(mirror_x=True)
conv = converge(lay, factors=(2.0, 1.414, 1.0), params=MeshParams(h_edge=0.02, h_core=0.1, h_far=6.0), order=2)
print("converge:", conv.C_F, "rel err of extrapolated", conv.C_F["extrapolated"] / exact - 1 if conv.C_F["extrapolated"] else None)
