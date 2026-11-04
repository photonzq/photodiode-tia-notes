"""Point the two scripts of the parasitic-capacitance estimate at Appendix G of the note.

Usage: python patch_scripts_appendix_g.py <scripts_archive/parasitic_cf folder>

- equation numbers P1-P49 in comments and docstrings become (G.1)-(G.49);
- "Section n of the derivation" and the other section numbers become G.n;
- the figure script writes Figures 38-43 as figures/fig38_parasitic_cf_... - fig43_..., in the note's folder.
Every replacement must match at least once; no P-number may survive.
"""
import re
import sys
from pathlib import Path

folder = Path(sys.argv[1])
FIG = {"pcf1_geometry_0402": "fig38_parasitic_cf_geometry_0402", "pcf2_regions": "fig39_parasitic_cf_regions",
       "pcf3_cps_maps": "fig40_parasitic_cf_cps_maps", "pcf4_body_without_film": "fig41_parasitic_cf_body_without_film",
       "pcf6_plane_map": "fig42_parasitic_cf_plane_map", "pcf5_pins_dsg": "fig43_parasitic_cf_pins_dsg"}


def renumber(s: str) -> str:
    s = re.sub(r"(Eqs?\.\s+)P(\d+)", r"\1(G.\2)", s)
    for _ in range(3):  # later members of a list: "P29-P32", "P28/P32", "P28, P32"
        s = re.sub(r"(\(G\.\d+\)\s?[-/,]\s?)P(\d+)", r"\1(G.\2)", s)
    s = re.sub(r"Section (\d+(?:\.\d+)?) of the derivation", r"Section G.\1 of the note", s)
    s = re.sub(r"\(Section (\d+(?:\.\d+)?)\)", r"(Section G.\1)", s)
    s = re.sub(r"(?<![G.\d])Section (\d+(?:\.\d+)?)(?=[ ,.;:)])", r"Section G.\1", s)
    s = s.replace("see A10)", "see approximation 10)")
    return s


# ---------------------------------------------------------------- the estimate
p = folder / "cf_parasitic_estimate.py"
s = p.read_text(encoding="utf-8")
old = "data/parasitic_cf/parasitic_cf_derivation.md; the equation numbers (P..) in the comments refer"
assert s.count(old) == 1
s = s.replace(old, "Appendix G of TIA_opamp_survey.md; the equation numbers (G.n) in the comments refer")
s = renumber(s)
assert not re.search(r"\bP\d+\b", s), re.findall(r".{30}\bP\d+\b.{10}", s)[:5]
assert "derivation.md" not in s
p.write_text(s, encoding="utf-8", newline="\n")

# ---------------------------------------------------------------- the figures
p = folder / "make_parasitic_cf_figures.py"
s = p.read_text(encoding="utf-8")
head_old = s[:s.index('"""', 3) + 3]
head_new = '''"""Figures 38-43 of the note, Appendix G: the parasitic capacitance across the feedback resistor.

Usage: python make_parasitic_cf_figures.py [outdir]      (default: ../../figures)

fig38  an 0402 resistor on its land pattern, top view and cross-section, drawn to scale (Figure 38)
fig39  the idealised cross-section, its three regions, and the boundary conditions of each (Figure 39)
fig40  the coplanar pads: physical plane -> t-plane (Moebius map) -> rectangle (Schwarz-Christoffel
       map), with the analytic equipotentials and field lines of Eq. (G.23) (Figure 40)
fig41  the resistor body without the film: the analytic potential of Eq. (G.32), and the filled-slot
       construction of Eq. (G.28) (Figure 41)
fig42  pads over a ground plane: the half-strip and its image under zeta = cosh(pi q / h) (Eqs. (G.39)-(G.41);
       Figure 42)
fig43  the OPA855 pin geometry (DSG0008A land pattern) and the two bounding constructions of Eqs. (G.45)-(G.46)
       (Figure 43)

Every potential drawn here is computed from the closed-form maps of Appendix G, using
cf_parasitic_estimate.py (same folder) for the formulas and scipy.special.elliprf for the map
f(t) = -2 sqrt(t/m) R_F(1 - t/m, 1 - t, 1) (Section G.6 of the note).  Nothing is solved numerically on a mesh.
"""'''
s = head_new + s[len(head_old):]
for a, b in FIG.items():
    assert s.count(f'"{a}"') == 1, a
    s = s.replace(f'"{a}"', f'"{b}"')
for k, n in (("pcf1", "38"), ("pcf2", "39"), ("pcf3", "40"), ("pcf4", "41"), ("pcf5", "43"), ("pcf6", "42")):
    s = s.replace(f"# ------------------------------------------------------------------------------ {k}\n",
                  f"# ------------------------------------------------------------------------- Figure {n}\n")
old = 'Path(__file__).resolve().parents[2] / "figures" / "parasitic_cf"'
assert s.count(old) == 1
s = s.replace(old, 'Path(__file__).resolve().parents[2] / "figures"')
s = renumber(s)
assert "pcf" not in s and "derivation" not in s, [m for m in re.findall(r".{20}(?:pcf|derivation).{20}", s)]
assert not re.search(r"\bP\d+\b", s)
p.write_text(s, encoding="utf-8", newline="\n")
print("patched")
