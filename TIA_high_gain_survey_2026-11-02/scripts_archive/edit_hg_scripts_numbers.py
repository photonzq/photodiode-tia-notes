"""Bring the figure numbers in the plot scripts' docstrings and in the scripts README up to the
renumbering of 3 November 2026 (old 1-5 -> 2, 3, 5, 10, 11; old 6-12 -> 17-23)."""
import re
from pathlib import Path

D = Path(__file__).resolve().parent
OLD2NEW = {1: 2, 2: 3, 3: 5, 4: 10, 5: 11, 6: 17, 7: 18, 8: 19, 9: 20, 10: 21, 11: 22, 12: 23}

for name in ("hg_figures.py", "hg_spice_figures.py"):
    p = D / name
    s = p.read_text(encoding="utf-8")
    s = re.sub(r"Fig\. (\d+)", lambda m: f"Fig. {OLD2NEW[int(m.group(1))]}", s)
    s = s.replace('"""Figures 6-11 of the high-gain TIA note', '"""Figures 17-23 of the high-gain TIA note')
    p.write_text(s, encoding="utf-8", newline="\n")

p = D / "README.md"
s = p.read_text(encoding="utf-8")
pairs = [
    ("| `hg_figures.py` | Figures 1–5 (PNG at 600 dpi and PDF) in `figures/`. Usage: `python hg_figures.py` |\n",
     "| `hg_figures.py` | Figures 2, 3, 5, 10 and 11 (PNG at 600 dpi and PDF) in `figures/`, written as "
     "`fig1`–`fig5`, the names under which they were first drawn. Usage: `python hg_figures.py` |\n"
     "| `hg_schematics.py` | The schematics, Figures 1, 4, 6–9 and 12–16, written as `figures/schem_*`: the circuit "
     "with its noise sources, the feedback resistor as an RC line, the driven conductors and the guarded split "
     "resistor, equalization, the T-network, the discrete-JFET composite of Section 9.5, gain ranging, the log "
     "amplifier, the switched integrator and the optical reset. Each function names the section and the values it "
     "draws. Usage: `python hg_schematics.py [OUT_DIR] [NAME ...]` |\n"
     "| `schematic_style.py` | The drawing style shared with the companion notes: one scale (0.30 in per drawing "
     "unit) and one canvas width (6.5 in), so that all schematics print at the same scale; white background, 1-pt "
     "lines, Arial labels at 8 pt with Computer Modern mathematics; parasitic elements grey, noise sources purple, "
     "light red, guards green, optional parts dashed. Needs schemdraw. |\n"),
    ("| `hg_spice_figures.py` | Figures 6–12 (PNG at 600 dpi and PDF) in `figures/`. Usage: `python hg_spice_figures.py` |\n",
     "| `hg_spice_figures.py` | Figures 17–23 (PNG at 600 dpi and PDF) in `figures/`, written as `fig6`–`fig12`. "
     "Usage: `python hg_spice_figures.py` |\n"),
    ("Order of running: `add_aol.py` (once), `hg_analysis.py`, `hg_numbers.py`, `hg_figures.py`,",
     "Order of running: `add_aol.py` (once), `hg_analysis.py`, `hg_numbers.py`, `hg_figures.py`, `hg_schematics.py`,"),
]
for a, b in pairs:
    assert s.count(a) == 1, a[:60]
    s = s.replace(a, b)
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
