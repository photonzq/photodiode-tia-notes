"""Arithmetic and symbolic checks behind the audit of Section G.14 (field solutions).

Reads only the JSON records in data/parasitic_cf/numerical/ and the closed-form script
cf_parasitic_estimate.py (numpy/scipy only).  No meshing, no finite-element solves.
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
import sympy as sp
from scipy.optimize import brentq

NOTE = Path(__file__).resolve().parents[4]          # the note's folder
D = NOTE / "data" / "parasitic_cf" / "numerical"
r3 = json.load(open(D / "resistor_3d.json", encoding="utf-8"))
cf = json.load(open(D / "closed_forms_2d.json", encoding="utf-8"))
ck = json.load(open(D / "checks.json", encoding="utf-8"))
EPS0 = 8.8541878128  # fF/mm

print("=== (a) Eqs. (G.52)-(G.53): cross terms")
ex, ey, ez, ox, oy, oz = sp.symbols("ex ey ez ox oy oz")
ge, go = sp.Matrix([ex, ey, ez]), sp.Matrix([ox, oy, oz])
gu, gv = ge + go, ge - go
print("grad u . grad v - (|grad e|^2 - |grad o|^2) =", sp.simplify(gu.dot(gv) - (ge.dot(ge) - go.dot(go))))
print("grad u . (grad u + grad v) =", sp.expand(gu.dot(gu + gv)))
cAA, cAB = sp.symbols("cAA cAB")
C = sp.Matrix([[cAA, cAB], [cAB, cAA]])
vo = sp.Matrix([sp.Rational(1, 2), -sp.Rational(1, 2)])
ve = sp.Matrix([sp.Rational(1, 2), sp.Rational(1, 2)])
ao, ae = (vo.T * C * vo)[0], (ve.T * C * ve)[0]
print("a(phi_o) - a(phi_e) =", sp.simplify(ao - ae), "; 2 a(phi_e) =", sp.simplify(2 * ae), "; a(phi_o) =", sp.simplify(ao))

print("=== (b) sphere in a grounded sphere")
a, b, eps, u = sp.symbols("a b eps u", positive=True)
Cs = 4 * sp.pi * eps * a * b / (b - a)
print(sp.simplify(Cs - 4 * sp.pi * eps * a / (1 - a / b)), sp.series(Cs.subs(b, 1 / u), u, 0, 3))


def rich(r, Cv):
    r1, r2, r3_ = r
    C1, C2, C3 = Cv
    rho = (C1 - C2) / (C2 - C3)
    p = brentq(lambda p: (r1**p - r2**p) / (r2**p - r3_**p) - rho, 0.05, 8)
    k = (C2 - C3) / (r2**p - r3_**p)
    return p, C3 - k * r3_**p


print("=== (c) Richardson recomputation, mesh and enclosure")
for s in ("0201", "0402", "0603", "0805"):
    d = r3[f"size_{s}"]
    lv = d["convergence"]["levels"]
    r = [x["refine"] for x in lv]
    Cv = [x["C_F"] for x in lv]
    p, Cinf = rich(r, Cv)
    Cinf1 = Cv[2] - (Cv[1] - Cv[2]) / (r[1] - r[2]) * r[2]
    e = d["enclosure"]
    q, Finf = rich([1 / R for R in e["R"]], e["C_F"])
    Finf1 = (e["R"][2] * e["C_F"][2] - e["R"][1] * e["C_F"][1]) / (e["R"][2] - e["R"][1])
    best, an = d["C_F_best"], d["analytic"]
    print(f"{s}: p={p:.3f} Cinf={Cinf:.4f} (p=1: {Cinf1-Cinf:+.3f}); q={q:.3f} (q=1: {Finf1-Finf:+.4f}); "
          f"enclosure {100*d['enclosure_correction']/best:.1f}% of best; position {100*(best-an['lower_bound'])/(an['upper_estimate']-an['lower_bound']):.1f}%; "
          f"below central {100*(1-best/an['central']):.2f}%; refine-4 level above limit {Cv[0]-Cinf:.3f} fF; dC_A0/dC_F {e['dC_A0']/e['dC_F']:.2f}")

print("=== (d) substrates: field ratio vs analytic-central ratio; shares")
for s in ("0402", "0805"):
    rows = r3[f"substrates_{s}"]["rows"]
    ref = next(x for x in rows if x["eps_pcb"] == 4.2)
    for x in rows:
        an_rel = x["analytic"]["central"] / ref["analytic"]["central"]
        print(f"  {s} eps {x['eps_pcb']:.2f}: field {x['relative_to_FR4']:.4f} analytic {an_rel:.4f} "
              f"({100*(an_rel/x['relative_to_FR4']-1):+.2f}%); air {x['shares']['air']:.2f} alumina {x['shares']['alumina']:.2f} "
              f"board {x['shares']['board']:.2f}; C_A0 {x['C_A0']:.1f}")

print("=== (e) details, corners, middle-mesh offset")
for k, v in r3["details_0402"]["table"].items():
    print(f"  {k:28s} {v['C_F']:.3f} {v['delta']:+.3f}")
ec = r3["eps_corners_0402"]["table"]
print("  corners %:", 100 * (ec["low"]["C_F"] / ec["nominal"]["C_F"] - 1), 100 * (ec["high"]["C_F"] / ec["nominal"]["C_F"] - 1))
print("  0402 refine 2.83 minus extrapolated:", r3["size_0402"]["convergence"]["levels"][1]["C_F"] - r3["size_0402"]["convergence"]["C_F"]["extrapolated"])

print("=== (f) Section G.8 body with film")
k_al = 9.7 * EPS0 * 0.5
g8 = cf["G8_block_with_film"]
lo, hi = g8["bracket"]
print("  ", k_al, k_al * g8["numeric"], k_al * lo, k_al * hi, k_al * (0.5 * (lo + hi) - g8["numeric"]))

print("=== (g) OPA855 network")
o = r3["opa855_layout"]["table"]
a_, b_ = o["refine_6.73"], o["refine_5.66"]
print("  added", a_["added"], b_["added"], "; fine-coarse", b_["network"] - a_["network"],
      "; fig50 plane bar", o["plane_cutout"]["network"] + (b_["network"] - a_["network"]), "raw", o["plane_cutout"]["network"])

print("=== (h) closed-form rows")
for k in ("G41_plane_0p10", "G41_plane_0p20", "G41_plane_0p36", "G43_guard"):
    c = cf[k]
    print(f"  {k}: closed {c['closed']:.6f} numeric {c['numeric']:.6f} rel {c['rel_error']:.2e} C_F/C_A0 {c['closed']/c['to_ground'][1]:.2e}")

print("=== (i) square via against round via")
print("  4/pi =", 4 / math.pi, "; equivalent radius of a square of side d:", math.gamma(0.25) ** 2 / (4 * math.pi ** 1.5), "d")

print("=== (j) 2-D truncation at R = 200 mm, pads of Eq. (G.25)")
s_, X = 0.40, 0.75
x = np.linspace(s_ / 2, X, 400001)[1:-1]
sig = 1.0 / np.sqrt((x**2 - (s_ / 2) ** 2) * (X**2 - x**2))
xc = np.trapezoid(x * sig, x) / np.trapezoid(sig, x)
Cfull = 2 * cf["G25_pads_halfplane"]["closed"]
p_eps = 2 * Cfull * xc
print(f"  centroid {xc:.4f} mm, p/eps0 {p_eps:.3f} mm, W_out/W = {p_eps**2/(8*math.pi*200.0**2)/(0.5*Cfull):.2e}")

print("=== (k) parallel-plate 0.3 fF of approximation 14 / Section G.10.7")
g, s2, W, ts = 0.6, 0.4, 0.5, 0.03
print("  ", EPS0 * W / ts * 2 * (g / 3) * ((g - s2) / (2 * g)) ** 3)

print("=== (l) film down, estimate at the same permittivities")
sys.path.insert(0, str(NOTE / "scripts_archive" / "parasitic_cf"))
import cf_parasitic_estimate as ana  # noqa: E402
ana.EPS_PCB, ana.EPS_AL = (4.2, 4.2), (9.7, 9.7)
up, dn = ana.resistor_on_pads("0402", "up", "nominal"), ana.resistor_on_pads("0402", "down", "nominal")
fd = r3["film_down_0402"]["table"]
print("  estimate central", dn["central"] - up["central"], "upper", dn["upper_estimate"] - up["upper_estimate"],
      "; field", fd["down"]["C_F"] - fd["up"]["C_F"])
