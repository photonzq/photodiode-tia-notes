import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[5] / "pcbcap"))
from scipy.special import ellipk, ellipkm1
from pcbcap.constants import EPS0
from pcbcap.geometry import Layout
from pcbcap.meshing import MeshParams
from pcbcap.study import solve_layout
s, w = 0.5, 0.5
m = (w / (s + w)) ** 2
exact = 2 * EPS0 * ellipk(m) / ellipkm1(m)
for R in (60.0, 240.0):
    lay = Layout(2, "cps")
    lay.add_segment("z", 0.0, (s / 2, s / 2 + w), net="A", name="A")
    lay.add_segment("z", 0.0, (-s / 2 - w, -s / 2), net="B", name="B")
    lay.set_enclosure({"x": (-R, R), "z": (-R, R)}, boundary="open")
    lay.set_symmetry(mirror_x=True)
    for he in (0.004, 0.001, 0.00025):
        t0 = time.perf_counter()
        res = solve_layout(lay, MeshParams(h_edge=he, h_core=0.05, h_far=R / 10), order=2)
        print(f"R={R} h_edge={he}: rel err {res.C_F/exact-1:+.3e}  dofs {res.fem['dofs']}  {time.perf_counter()-t0:.1f}s")
