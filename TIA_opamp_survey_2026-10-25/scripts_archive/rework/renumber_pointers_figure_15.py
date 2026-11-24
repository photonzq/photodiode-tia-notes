"""Follow the shift of Figures 15-58 to 16-59 (renumber_figures_from_15.py, which made room for the new Figure 15 of
Section 4.11.9) in the files outside the note that point at those numbers: the repository's README, the archive's
README and the Appendix G index, the docstrings and comments of the current scripts, the text of the interactive
layout pages, and pcbcap's one pointer.  The files and strings are those that renumber_pointers_figure_14.py updated,
at their present numbers.

Usage: python renumber_pointers_figure_15.py [--dry-run]

Each entry gives the text to replace and how often it must occur; nothing is written unless every entry matches.
Historical one-off edit scripts, their README rows and the run records keep the numbers of their time, and so do the
docstrings and README rows that use the numbering of the report before its narrative order (the README's
"Numbering" paragraph converts those). Pointers to other documents' figures stay as they are.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]           # TIA_notes
NOTE = "TIA_opamp_survey_2026-10-25/"
ARCH = NOTE + "scripts_archive/"
NUM = ARCH + "parasitic_cf/numerical/"
VIEWS = NOTE + "figures/layout_views/"


def shift(m):
    """Add one to the figure number in group 2."""
    return m.group(1) + str(int(m.group(2)) + 1) + m.group(3)


EXACT = [  # (file, old, new, expected count); applied in this order
    ("README.md", "| `figures/` | Figures 1–58 as PNG and PDF; Appendix E of the note maps",
     "| `figures/` | Figures 1–59 as PNG and PDF; Appendix E of the note maps", 1),
    (ARCH + "README.md", "old Figures 7–16 are Figures 15–21 and 29–31", "old Figures 7–16 are Figures 16–22 and 30–32", 1),
    (ARCH + "README.md", "# Figure 1 and Figures 33-38 and 40-44 (schematics)",
     "# Figure 1 and Figures 34-39 and 41-45 (schematics)", 1),
    (ARCH + "README.md", "(Figures 33–38 and 40–44: the two composites", "(Figures 34–39 and 41–45: the two composites", 1),
    (ARCH + "README.md", "`fig17_bandwidth_phase_margin_all_parts` (Figure 22: robust",
     "`fig17_bandwidth_phase_margin_all_parts` (Figure 23: robust", 1),
    (ARCH + "README.md", "`fig18_noise_penalty_all_parts` (Figure 25: band penalty",
     "`fig18_noise_penalty_all_parts` (Figure 26: band penalty", 1),
    (ARCH + "README.md", "`fig19_dynamic_range_all_parts` (Figure 27: electronic",
     "`fig19_dynamic_range_all_parts` (Figure 28: electronic", 1),
    (ARCH + "README.md", "`fig20_benchmark_50ohm` (Figure 32: small-signal", "`fig20_benchmark_50ohm` (Figure 33: small-signal", 1),
    (ARCH + "README.md", "it also draws Figure 39 (`figures/fig26b_sink_vs_plain`",
     "it also draws Figure 40 (`figures/fig26b_sink_vs_plain`", 1),
    (ARCH + "parasitic_cf/INDEX.md", "Draws Figures 45–50 of Appendix G", "Draws Figures 46–51 of Appendix G", 1),
    (ARCH + "parasitic_cf/INDEX.md", "The potentials in Figures 47–49 come from", "The potentials in Figures 48–50 come from", 1),
    (ARCH + "parasitic_cf/INDEX.md", "and the OPA855 network of Figure 50.", "and the OPA855 network of Figure 51.", 1),
    (ARCH + "parasitic_cf/INDEX.md", "(the mesh of Figures 52c and 53)", "(the mesh of Figures 53c and 54)", 1),
    (ARCH + "parasitic_cf/INDEX.md", "for the text beside Figure 53.", "for the text beside Figure 54.", 1),
    (ARCH + "parasitic_cf/INDEX.md",
     "Draws Figures 51–58, in the files `fig44`–`fig51`, from the records (Figures 52c and 53 solve the 0402 model once).",
     "Draws Figures 52–59, in the files `fig44`–`fig51`, from the records (Figures 53c and 54 solve the 0402 model once).", 1),
    (ARCH + "sink_vs_plain_hv.py", "With --figure it also draws Figure 39 of the note",
     "With --figure it also draws Figure 40 of the note", 1),
    (ARCH + "sink_vs_plain_hv.py", '"""Figure 39: Eqs. (1) and (2) in dB', '"""Figure 40: Eqs. (1) and (2) in dB', 1),
    (ARCH + "sink_vs_plain_hv.py", 'print(f"Figure 39 written to', 'print(f"Figure 40 written to', 1),
    (ARCH + "make_schematics.py", "and Figures 33 onwards).", "and Figures 34 onwards).", 1),
    (NUM + "g_closed_forms_2d.py", "# Figure 50 so that A lies at +x", "# Figure 51 so that A lies at +x", 1),
    (NUM + "g_eight_lead_3d.py", "Figure 53).  The OPA846 cases", "Figure 54).  The OPA846 cases", 1),
    (NUM + "make_numerical_figures.py",
     '"""Figures 51-58 of Appendix G (the numerical section; files fig44-fig51), from the recorded results.',
     '"""Figures 52-59 of Appendix G (the numerical section; files fig44-fig51), from the recorded results.', 1),
    (NUM + "make_numerical_figures.py", "Only Figures 52c and 53 (fig44, fig45) need a field",
     "Only Figures 53c and 54 (fig44, fig45) need a field", 1),
    (NUM + "make_numerical_figures.py", "The feedback network of Figure 50 in three dimensions",
     "The feedback network of Figure 51 in three dimensions", 1),
    (NUM + "field_regions.py", "those of Figures 52c and 53 (make_numerical_figures.py, solved_0402)",
     "those of Figures 53c and 54 (make_numerical_figures.py, solved_0402)", 1),
    (NUM + "render_layout_views.py", "and Figure 58 of the note", "and Figure 59 of the note", 1),
    (NUM + "render_layout_views.py", "and Figure 57 of the note", "and Figure 58 of the note", 1),
    (NUM + "development/check_iso_faces.py", "view of the published Figures 52, 57 and 58, files fig44, fig50 and fig51).",
     "view of the published Figures 53, 58 and 59, files fig44, fig50 and fig51).", 1),
    ("pcbcap/pcbcap/parts.py", "Symbols as in the companion note's Figure 45.", "Symbols as in the companion note's Figure 46.", 1),
    (VIEWS + "index.html", "Figure 58 of the note", "Figure 59 of the note", 3),
    (VIEWS + "index.html", "Figure 57 of the note", "Figure 58 of the note", 1),
    (VIEWS + "opa846_sot23_around_0402.html", "Figure 58 of the note", "Figure 59 of the note", 1),
    (VIEWS + "opa846_sot23_double_sided_0402.html", "Figure 58 of the note", "Figure 59 of the note", 1),
    (VIEWS + "opa846_sot23_under_body_0402.html", "Figure 58 of the note", "Figure 59 of the note", 1),
    (VIEWS + "opa855_network.html", "Figure 57 of the note", "Figure 58 of the note", 1),
]
PATTERNS = [  # (file, regex with three groups, replacement, expected count): every match is one of the note's figures
    (ARCH + "parasitic_cf/make_parasitic_cf_figures.py", r"(Figures )(45)(-50)", lambda m: "Figures 46-51", 1),
    (ARCH + "parasitic_cf/make_parasitic_cf_figures.py", r"(Figure )(4[5-9]|50)(\b)", shift, 12),
    (NUM + "field_regions.py", r"(Figure )(53)([ab]?\b)", shift, 5),
    (NUM + "g_resistor_3d.py", r"(Figure )(50)(\b)", shift, 5),
]


def main():
    dry = "--dry-run" in sys.argv
    texts, ok = {}, True
    for rel, old, new, want in EXACT:
        path = ROOT / rel
        text = texts.setdefault(rel, path.read_bytes().decode("utf-8"))
        got = text.count(old)
        print(f"{'ok ' if got == want else 'BAD'} {rel}: {got} of {want}  {old[:60]!r}")
        ok &= got == want
        texts[rel] = text.replace(old, new)
    for rel, pat, rep, want in PATTERNS:
        path = ROOT / rel
        text = texts.setdefault(rel, path.read_bytes().decode("utf-8"))
        for m in re.finditer(pat, text):
            line = text.count("\n", 0, m.start()) + 1
            print(f"      {rel}:{line}: {m.group(0)!r} -> {rep(m)!r}")
        new_text, got = re.subn(pat, rep, text)
        print(f"{'ok ' if got == want else 'BAD'} {rel}: {got} of {want}  /{pat}/")
        ok &= got == want
        texts[rel] = new_text
    if not ok:
        sys.exit("a count did not match; nothing written")
    if dry:
        print("dry run; nothing written")
        return
    for rel, text in texts.items():
        (ROOT / rel).write_bytes(text.encode("utf-8"))
    print(f"written: {len(texts)} files")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
