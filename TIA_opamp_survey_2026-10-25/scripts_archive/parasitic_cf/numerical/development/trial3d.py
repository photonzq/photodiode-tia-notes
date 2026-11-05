import sys, time, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[5] / "pcbcap"))
import psutil
from pcbcap import parts, study
from pcbcap.meshing import MeshParams, build_mesh
from pcbcap.fem import Problem
from pcbcap.capacitance import two_port
study.lower_priority(2)
proc = psutil.Process()
res = parts.ChipResistor.from_size("0402")
pads = parts.LandPattern.from_size("0402")
lay = parts.resistor_on_pads(res, pads, parts.Board(), parts.Mount(), enclosure_half=8.0)
print(lay.summary())
print("smallest feature", lay.smallest_feature())
for refine in (2.0, 1.4):
    t0 = time.perf_counter()
    md = build_mesh(lay, MeshParams(refine=refine))
    t1 = time.perf_counter()
    print(f"refine {refine}: mesh {md.stats['nodes']} nodes {md.stats['elements']} tets in {t1-t0:.1f}s; h_edge {md.stats['h_edge']:.4f} h_core {md.stats['h_core']:.3f} h_far {md.stats['h_far']:.2f}")
    for order in (1, 2):
        t1 = time.perf_counter()
        prob = Problem(lay, md, order=order)
        r = two_port(prob)
        print(f"   P{order}: C_F {r.C_F:.3f} fF, C_A0 {r.C_A0:.2f} fF, dofs {prob.N}, {time.perf_counter()-t1:.1f}s, RSS {proc.memory_info().rss/1e9:.2f} GB, shares {{{', '.join(f'{k}: {v:.2f}' for k, v in r.contributions.items())}}}, solves {[ (s['method'], s.get('iterations')) for s in r.fem['solves']]}")
