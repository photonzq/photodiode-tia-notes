"""Follow the shift of Figures 9-52 to 10-53 (renumber_figures_from_9.py, which made room for the new Figure 9 of
Section 4.10) in the files outside the note that point at those numbers: the repository's README, the archive's
README and the Appendix G index, the docstrings and comments of the current scripts, the text of the interactive
layout pages, and pcbcap's one pointer.

Usage: python renumber_pointers_figure_9.py [--dry-run]

Each entry gives the text to replace and how often it must occur; nothing is written unless every entry matches.
Historical one-off edit scripts, their README rows and the run records keep the numbers of their time, and so do the
docstrings and README rows that use the numbering of the report before its narrative order (the README's
"Numbering" paragraph converts those). Pointers to other documents' figures stay as they are.

Four entries also correct pointers that were already out of date before this shift: the repository README's figure
count (Figures 1-51, since the new Figure 33 of 7 November it has been 1-52), the archive README's conversion of the
old Figures 7-16 and its row for make_narrative_figures.py (both still in the numbering of 27 October, before
Chapter 4 added Figures 3-8), and two docstrings that named the numerical model and field figures by their file
numbers (Figures 44c and 45) instead of the note's numbers.
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
    ("README.md", "| `figures/` | Figures 1–51 as PNG and PDF; Appendix E of the note maps",
     "| `figures/` | Figures 1–53 as PNG and PDF; Appendix E of the note maps", 1),
    (ARCH + "README.md", "old Figures 7–16 are Figures 3–9 and 17–19", "old Figures 7–16 are Figures 10–16 and 24–26", 1),
    (ARCH + "README.md", "# Figure 1 and Figures 27-32 and 34-38 (schematics)",
     "# Figure 1 and Figures 28-33 and 35-39 (schematics)", 1),
    (ARCH + "README.md", "(Figures 27–32 and 34–38: the two composites", "(Figures 28–33 and 35–39: the two composites", 1),
    (ARCH + "README.md", "`fig17_bandwidth_phase_margin_all_parts` (Figure 10: robust",
     "`fig17_bandwidth_phase_margin_all_parts` (Figure 17: robust", 1),
    (ARCH + "README.md", "`fig18_noise_penalty_all_parts` (Figure 13: band penalty",
     "`fig18_noise_penalty_all_parts` (Figure 20: band penalty", 1),
    (ARCH + "README.md", "`fig19_dynamic_range_all_parts` (Figure 15: electronic",
     "`fig19_dynamic_range_all_parts` (Figure 22: electronic", 1),
    (ARCH + "README.md", "`fig20_benchmark_50ohm` (Figure 20: small-signal", "`fig20_benchmark_50ohm` (Figure 27: small-signal", 1),
    (ARCH + "README.md", "it also draws Figure 33 (`figures/fig26b_sink_vs_plain`",
     "it also draws Figure 34 (`figures/fig26b_sink_vs_plain`", 1),
    (ARCH + "parasitic_cf/INDEX.md", "Draws Figures 39–44 of Appendix G", "Draws Figures 40–45 of Appendix G", 1),
    (ARCH + "parasitic_cf/INDEX.md", "The potentials in Figures 41–43 come from", "The potentials in Figures 42–44 come from", 1),
    (ARCH + "parasitic_cf/INDEX.md", "and the OPA855 network of Figure 44.", "and the OPA855 network of Figure 45.", 1),
    (ARCH + "parasitic_cf/INDEX.md", "(the mesh of Figures 46c and 47)", "(the mesh of Figures 47c and 48)", 1),
    (ARCH + "parasitic_cf/INDEX.md", "for the text beside Figure 47.", "for the text beside Figure 48.", 1),
    (ARCH + "parasitic_cf/INDEX.md",
     "Draws Figures 45–52, in the files `fig44`–`fig51`, from the records (Figures 46c and 47 solve the 0402 model once).",
     "Draws Figures 46–53, in the files `fig44`–`fig51`, from the records (Figures 47c and 48 solve the 0402 model once).", 1),
    (ARCH + "sink_vs_plain_hv.py", "With --figure it also draws Figure 33 of the note",
     "With --figure it also draws Figure 34 of the note", 1),
    (ARCH + "sink_vs_plain_hv.py", '"""Figure 33: Eqs. (1) and (2) in dB', '"""Figure 34: Eqs. (1) and (2) in dB', 1),
    (ARCH + "sink_vs_plain_hv.py", 'print(f"Figure 33 written to', 'print(f"Figure 34 written to', 1),
    (ARCH + "make_schematics.py", "and Figures 27 onwards).", "and Figures 28 onwards).", 1),
    (NUM + "g_closed_forms_2d.py", "# Figure 44 so that A lies at +x", "# Figure 45 so that A lies at +x", 1),
    (NUM + "g_eight_lead_3d.py", "Figure 47).  The OPA846 cases", "Figure 48).  The OPA846 cases", 1),
    (NUM + "make_numerical_figures.py",
     '"""Figures 45-52 of Appendix G (the numerical section; files fig44-fig51), from the recorded results.',
     '"""Figures 46-53 of Appendix G (the numerical section; files fig44-fig51), from the recorded results.', 1),
    (NUM + "make_numerical_figures.py", "Only Figures 44c and 45 need a field",
     "Only Figures 47c and 48 (fig44, fig45) need a field", 1),
    (NUM + "make_numerical_figures.py", "The feedback network of Figure 44 in three dimensions",
     "The feedback network of Figure 45 in three dimensions", 1),
    (NUM + "field_regions.py", "those of Figures 44c and 45 (make_numerical_figures.py, solved_0402)",
     "those of Figures 47c and 48 (make_numerical_figures.py, solved_0402)", 1),
    (NUM + "render_layout_views.py", "and Figure 52 of the note", "and Figure 53 of the note", 1),
    (NUM + "render_layout_views.py", "and Figure 51 of the note", "and Figure 52 of the note", 1),
    (NUM + "development/check_iso_faces.py", "view of the published Figures 46, 51 and 52, files fig44, fig50 and fig51).",
     "view of the published Figures 47, 52 and 53, files fig44, fig50 and fig51).", 1),
    ("pcbcap/pcbcap/parts.py", "Symbols as in the companion note's Figure 39.", "Symbols as in the companion note's Figure 40.", 1),
    (VIEWS + "index.html", "Figure 52 of the note", "Figure 53 of the note", 3),
    (VIEWS + "index.html", "Figure 51 of the note", "Figure 52 of the note", 1),
    (VIEWS + "opa846_sot23_around_0402.html", "Figure 52 of the note", "Figure 53 of the note", 1),
    (VIEWS + "opa846_sot23_double_sided_0402.html", "Figure 52 of the note", "Figure 53 of the note", 1),
    (VIEWS + "opa846_sot23_under_body_0402.html", "Figure 52 of the note", "Figure 53 of the note", 1),
    (VIEWS + "opa855_network.html", "Figure 51 of the note", "Figure 52 of the note", 1),
]
PATTERNS = [  # (file, regex with three groups, replacement, expected count): every match is one of the note's figures
    (ARCH + "parasitic_cf/make_parasitic_cf_figures.py", r"(Figures )(39)(-44)", lambda m: "Figures 40-45", 1),
    (ARCH + "parasitic_cf/make_parasitic_cf_figures.py", r"(Figure )(39|4[0-4])(\b)", shift, 12),
    (NUM + "field_regions.py", r"(Figure )(47)([ab]?\b)", shift, 5),
    (NUM + "g_resistor_3d.py", r"(Figure )(44)(\b)", shift, 5),
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
