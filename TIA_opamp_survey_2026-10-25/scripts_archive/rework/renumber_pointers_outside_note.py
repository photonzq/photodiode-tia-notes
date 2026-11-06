"""Follow the shift of Sections 8.6-8.11 to 8.7-8.12 and of Figures 33-51 to 34-52 (renumber_section_8_6_figure_33.py)
in the files outside the note that point at those numbers: the high-gain note and its part file, the archive's
README and the Appendix G index, the docstrings and comments of the current scripts, the text of the interactive
layout pages, and pcbcap's one pointer.

Usage: python renumber_pointers_outside_note.py [--dry-run]

Each entry gives the text to replace and how often it must occur; nothing is written unless every entry matches.
Historical one-off edit scripts, their README rows and the run records keep the numbers of their time. Pointers to
other documents' figures stay as they are (the AD620 data sheet's Figure 50 in the side note and in pcbcap, and the
OPA657 data sheet's Figure 35 in data/parasitic_cf/tia_feedback_parasitics.md).
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]           # TIA_notes
NOTE = "TIA_opamp_survey_2026-10-25/"
ARCH = NOTE + "scripts_archive/"
NUM = ARCH + "parasitic_cf/numerical/"
VIEWS = NOTE + "figures/layout_views/"


def shift(lo, hi):
    """A replacement function that adds one to a figure number between lo and hi."""
    return lambda m: m.group(1) + str(int(m.group(2)) + 1) + m.group(3)


EXACT = [  # (file, old, new, expected count)
    ("TIA_high_gain_survey_2026-11-02/TIA_high_gain_survey.md",
     "as cited in the companion's Section 8.10)", "as cited in the companion's Section 8.11)", 1),
    ("TIA_high_gain_survey_2026-11-02/parts/03_bandwidth.md",
     "as cited in the companion's Section 8.10)", "as cited in the companion's Section 8.11)", 1),
    (ARCH + "make_schematics.py", "1-kOhm resistors (Section 8.10)", "1-kOhm resistors (Section 8.11)", 1),
    (ARCH + "make_schematics.py", '"""Section 8.6: a unity-gain follower', '"""Section 8.7: a unity-gain follower', 1),
    (ARCH + "make_schematics.py", '"""Section 8.7: a common-base PNP', '"""Section 8.8: a common-base PNP', 1),
    (ARCH + "make_schematics.py", '"""Section 8.8 (b): a slow integrator', '"""Section 8.9 (b): a slow integrator', 1),
    (ARCH + "make_schematics.py", '"""Section 8.8 (c), the topology', '"""Section 8.9 (c), the topology', 1),
    (ARCH + "make_schematics.py", '"""Section 8.9 and Table A8.10: the proposed', '"""Section 8.10 and Table A8.10: the proposed', 1),
    (ARCH + "make_schematics.py", "imbalance servo of Section 8.8 (d):", "imbalance servo of Section 8.9 (d):", 1),
    (ARCH + "parasitic_cf/inductance_estimates.py", "at the summing node (Section 8.10).", "at the summing node (Section 8.11).", 1),
    (ARCH + "README.md", "# Figure 1 and Figures 21-31 (schematics)", "# Figure 1 and Figures 27-32 and 34-38 (schematics)", 1),
    (ARCH + "README.md",
     "`fig21`–`fig31` (Figures 21–31: the two composites of Chapter 7, Options A–D, bootstrapping, cascoding, the "
     "optical-split and current-splitter servos, and the proposed front end of Chapter 8). Each function's docstring "
     "names the section and table its part values come from, with the numbering of 3 November 2026 (Figures 21–31 are "
     "Figures 27–37 since 4 November);",
     "`fig21`–`fig31` (Figures 27–32 and 34–38: the two composites of Chapter 7, Options A–D, bootstrapping, cascoding, "
     "the optical-split and current-splitter servos, and the proposed front end of Chapter 8). Each function's "
     "docstring names the section and table its part values come from;", 1),
    (ARCH + "parasitic_cf/INDEX.md", "Draws Figures 38–43 of Appendix G", "Draws Figures 39–44 of Appendix G", 1),
    (ARCH + "parasitic_cf/INDEX.md", "The potentials in Figures 40–42 come from", "The potentials in Figures 41–43 come from", 1),
    (ARCH + "parasitic_cf/INDEX.md", "and the OPA855 network of Figure 43.", "and the OPA855 network of Figure 44.", 1),
    (ARCH + "parasitic_cf/INDEX.md", "(the mesh of Figures 44c and 45)", "(the mesh of Figures 45c and 46)", 1),
    (ARCH + "parasitic_cf/INDEX.md", "for the text beside Figure 45.", "for the text beside Figure 46.", 1),
    (ARCH + "parasitic_cf/INDEX.md",
     "Draws Figures 44–51 from the records (Figures 44c and 45 solve the 0402 model once). | "
     "`python make_numerical_figures.py [figure numbers]` |",
     "Draws Figures 45–52, in the files `fig44`–`fig51`, from the records (Figures 45c and 46 solve the 0402 model "
     "once). | `python make_numerical_figures.py [file numbers 44–51]` |", 1),
    (NUM + "g_closed_forms_2d.py", "# Figure 43 so that A lies at +x", "# Figure 44 so that A lies at +x", 1),
    (NUM + "g_eight_lead_3d.py", "Figure 45).  The OPA846 cases", "Figure 46).  The OPA846 cases", 1),
    (NUM + "make_numerical_figures.py", '"""Figures 44-51 of Appendix G (the numerical section), from the recorded results.',
     '"""Figures 45-52 of Appendix G (the numerical section; files fig44-fig51), from the recorded results.', 1),
    (NUM + "make_numerical_figures.py", "python make_numerical_figures.py [figure numbers ...]",
     "python make_numerical_figures.py [file numbers 44-51 ...]", 1),
    (NUM + "make_numerical_figures.py", "The feedback network of Figure 43 in three dimensions",
     "The feedback network of Figure 44 in three dimensions", 1),
    (NUM + "render_layout_views.py", "and Figure 51 of the note", "and Figure 52 of the note", 1),
    (NUM + "render_layout_views.py", "and Figure 50 of the note", "and Figure 51 of the note", 1),
    (NUM + "development/check_iso_faces.py", "view of the published Figures 44, 50 and 51).",
     "view of the published Figures 45, 51 and 52, files fig44, fig50 and fig51).", 1),
    ("pcbcap/pcbcap/parts.py", "Symbols as in the companion note's Figure 38.", "Symbols as in the companion note's Figure 39.", 1),
    (VIEWS + "index.html", "Figure 51 of the note", "Figure 52 of the note", 3),
    (VIEWS + "index.html", "Figure 50 of the note", "Figure 51 of the note", 1),
    (VIEWS + "opa846_sot23_around_0402.html", "Figure 51 of the note", "Figure 52 of the note", 1),
    (VIEWS + "opa846_sot23_double_sided_0402.html", "Figure 51 of the note", "Figure 52 of the note", 1),
    (VIEWS + "opa846_sot23_under_body_0402.html", "Figure 51 of the note", "Figure 52 of the note", 1),
    (VIEWS + "opa855_network.html", "Figure 50 of the note", "Figure 51 of the note", 1),
]
PATTERNS = [  # (file, regex with three groups, replacement, expected count): every match is one of the note's figures
    (ARCH + "parasitic_cf/make_parasitic_cf_figures.py", r"(Figures )(38)(-43)", lambda m: "Figures 39-44", 1),
    (ARCH + "parasitic_cf/make_parasitic_cf_figures.py", r"(Figure )(3[89]|4[0-3])(\b)", shift(38, 43), 12),
    (NUM + "field_regions.py", r"(Figure )(45)([ab]?\b)", shift(45, 45), 5),
    (NUM + "g_resistor_3d.py", r"(Figure )(43)(\b)", shift(43, 43), 5),
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
