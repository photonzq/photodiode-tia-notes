"""Building a layout by hand: two coupled traces on FR-4, with and without a guard trace.

Run from the pcbcap folder:  python examples/custom_layout.py      (under a minute)

Why this example exists
-----------------------
The builders of pcbcap.parts cover chip resistors, but any layout made of axis-aligned boxes and
sheets can be described directly.  This example shows the steps for a layout the builders do not
know: two parallel traces (nets A and B) 3 mm long on a 1.6-mm FR-4 board, 0.2 mm wide with a
0.3-mm gap.  It computes their mutual capacitance, then adds a grounded guard trace between them and
computes the Maxwell capacitance matrix, which shows the guard taking the coupling (Rule 6 of the
companion note's Section G.4.3: grounding a conductor never raises a mutual capacitance).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pcbcap import Layout, MeshParams, Problem, build_mesh, maxwell_matrix, study   # noqa: E402

study.lower_priority(2)
H, T_CU, LEN, WID, GAP = 1.6, 0.035, 3.0, 0.2, 0.3


def traces(guard: bool) -> Layout:
    lay = Layout(3, "two traces" + (" with a guard" if guard else ""))
    lay.add_box((-6, 6), (-6, 6), (-H, 0.0), material="FR4", label="board")
    # Traces run along y; A at +x, B at -x, symmetric about x = 0 and y = 0.
    lay.add_box((GAP / 2, GAP / 2 + WID), (-LEN / 2, LEN / 2), (0.0, T_CU), net="A")
    lay.add_box((-GAP / 2 - WID, -GAP / 2), (-LEN / 2, LEN / 2), (0.0, T_CU), net="B")
    if guard:
        lay.add_box((-0.05, 0.05), (-LEN / 2, LEN / 2), (0.0, T_CU), net="gnd")
    lay.set_enclosure({"x": (-6, 6), "y": (-6, 6), "z": (-H - 6, 6)}, boundary="ground")
    return lay


params = MeshParams(h_edge=0.01, h_core=0.08, refine=2.0)

# 1. Mutual capacitance with the mirror shortcut (x mirror exchanges A and B, y mirror keeps them).
lay = traces(guard=False)
lay.set_symmetry(mirror_x=True, mirror_y=True)
res = study.solve_layout(lay, params)
print(f"two traces: C_F = -C_AB = {res.C_F:.2f} fF, C_A0 = {res.C_A0:.2f} fF; "
      f"shares {', '.join(f'{k} {v:.2f}' for k, v in res.contributions.items())}")

# 2. With the guard: the Maxwell matrix of nets A and B (the guard is ground).  maxwell_matrix needs no
#    x mirror, so only the y mirror is declared.
lay = traces(guard=True)
lay.set_symmetry(mirror_y=True)
prob = Problem(lay, build_mesh(lay, params), order=2)
nets, C = maxwell_matrix(prob, ["A", "B"])
print(f"with a grounded guard: C_AA = {C[0, 0]:.2f} fF, C_AB = {C[0, 1]:.2f} fF, so C_F = {-C[0, 1]:.2f} fF")
