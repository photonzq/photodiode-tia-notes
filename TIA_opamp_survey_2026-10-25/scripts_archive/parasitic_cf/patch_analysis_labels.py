"""Bring the comments and table labels of the analysis scripts in line with Table 1.1 of the note: the parasitic
feedback capacitance is 0.08 pF (corners 0.05-0.12 pF, Appendix G), and 0.2 pF is the minimum total C_F of every
design, with corners of the total at -/+0.1 pF.  The numbers the scripts compute do not change; starting_values.py
now subtracts 0.08 pF, not 0.2 pF, to give the external capacitor of Table A8.13.

Usage: python patch_analysis_labels.py <scripts_archive folder>
Every replacement must match exactly once.
"""
import sys
from pathlib import Path

root = Path(sys.argv[1])
EDITS = {
    "run_analysis.py": [
        ("C_FPAR_NOM, C_FPAR_RANGE = 0.20e-12, (0.1e-12, 0.3e-12)    # parasitic feedback capacitance of R_F (Table 1.1)",
         "C_FPAR_NOM, C_FPAR_RANGE = 0.20e-12, (0.1e-12, 0.3e-12)    # minimum total C_F of every design and its -/+0.1 pF\n"
         "# corners (Table 1.1); the names are historical: the parasitic itself is 0.08 pF, 0.05-0.12 pF (Appendix G)"),
    ],
    "case_studies.py": [
        ("total feedback capacitance C_F = 0.20 pF for OPA855 (the\nparasitic floor; no capacitor is fitted) and 0.75 pF for OPA846",
         "total feedback capacitance C_F = 0.20 pF for OPA855 (the\nminimum total of Table 1.1: 0.12 pF fitted beside the 0.08-pF parasitic) and 0.75 pF for OPA846"),
        ("with C_F >= 0.20 pF (the parasitic floor of Table 1.1), is chosen;",
         "with C_F >= 0.20 pF (the minimum total of Table 1.1), is chosen;"),
        ("CF_FLOOR_pF = 0.20\n", "CF_FLOOR_pF = 0.20   # minimum total C_F of Table 1.1\n"),
        ("below the 0.20-pF parasitic floor. Where no $C_F$ of the grid meets all three",
         "below the 0.20-pF minimum total of Table 1.1. Where no $C_F$ of the grid meets all three"),
    ],
    "medium_gain.py": [
        ("the nominal 0.35 pF of board capacitance, for the nominal 0.2-pF feedback parasitic (Table A6.38) and for 0.1 pF\n(Table A6.39).",
         "the nominal 0.35 pF of board capacitance, for 0.2 pF across R_F, the minimum total of the 2-kOhm designs (Table A6.38),\n"
         "and for 0.1 pF, close to the parasitic alone (Table A6.39)."),
        ("the total C_F never below the parasitic. At these resistances",
         "the total C_F never below the value across R_F. At these resistances"),
        ("f\"*Table A6.{number}. Larger feedback resistors with {cfpar * 1e12:.1f} pF of feedback parasitic \"\n"
         "           f\"{'(the nominal value)' if cfpar > 0.15e-12 else '(an optimistic layout)'}: the robust design of each \"",
         "f\"*Table A6.{number}. Larger feedback resistors with {cfpar * 1e12:.1f} pF across $R_F$, \"\n"
         "           f\"{'the minimum total of the 2-kΩ designs (Table 1.1)' if cfpar > 0.15e-12 else 'close to the parasitic alone (Table 1.1)'}: the robust design of each \""),
    ],
    "starting_values.py": [
        ('"""Recommended starting component values and their tolerance to the feedback parasitic.',
         '"""Recommended starting component values and their tolerance (Table A8.13).'),
        ("C_F) evaluate the nominal response (C_PCB = 0.35 pF) and the response when the\n"
         "resistor/pad parasitic is 0.1 pF lower or higher than the nominal 0.2 pF with\n"
         "the same external capacitor (total C_F - 0.1 pF and + 0.1 pF), and at the\n"
         "C_PCB corners 0.2 and 0.5 pF.  Writes a Markdown table.",
         "C_F) evaluate the nominal response (C_PCB = 0.35 pF) and the response when the\n"
         "total C_F is 0.1 pF lower or higher (the tolerance of the fitted capacitor and of\n"
         "the parasitic, Table 1.1), and at the C_PCB corners 0.2 and 0.5 pF.  The external\n"
         "capacitor is the total minus the 0.08-pF parasitic of Table 1.1 (Appendix G).\n"
         "Writes a Markdown table."),
        ('"| Design | $R_F$ | Total $C_F$ target (external with 0.2 pF parasitic) | Nominal: $f_{-3\\\\,\\\\mathrm{dB}}$, PM, peaking | "\n'
         '            "$C_{F,\\\\mathrm{par}}$ 0.1 pF (total −0.1) | $C_{F,\\\\mathrm{par}}$ 0.3 pF (total +0.1) | $C_{\\\\mathrm{PCB}}$ 0.2 / 0.5 pF | "',
         '"| Design | $R_F$ | Total $C_F$ target (external) | Nominal: $f_{-3\\\\,\\\\mathrm{dB}}$, PM, peaking | "\n'
         '            "Total −0.1 pF | Total +0.1 pF | $C_{\\\\mathrm{PCB}}$ 0.2 / 0.5 pF | "'),
        ("        ext = cf - 0.2\n", "        ext = cf - C_FPAR_PF\n"),
        ("DESIGNS = [  # label, part, R_F, C_add (pF), target total C_F (pF)",
         "C_FPAR_PF = 0.08   # parasitic feedback capacitance of Table 1.1 (Appendix G)\n\n"
         "DESIGNS = [  # label, part, R_F, C_add (pF), target total C_F (pF)"),
    ],
}
for name, edits in EDITS.items():
    p = root / name
    s = p.read_text(encoding="utf-8")
    for old, new in edits:
        assert s.count(old) == 1, (name, s.count(old), old[:80])
        s = s.replace(old, new)
    p.write_text(s, encoding="utf-8", newline="\n")
    print("patched", name)
