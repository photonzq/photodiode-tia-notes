"""Follow the shift of Figures 10-53 to 11-54 (renumber_figures_from_10.py, which made room for the new Figure 10
of Section 4.11) in the files outside the note that point at those numbers: the repository's README, the archive's
README and the Appendix G index, the docstrings and comments of the current scripts, the text of the interactive
layout pages, and pcbcap's one pointer.

Usage: python renumber_pointers_figure_10.py [--dry-run]

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
    ("README.md", "| `figures/` | Figures 1–53 as PNG and PDF; Appendix E of the note maps",
     "| `figures/` | Figures 1–54 as PNG and PDF; Appendix E of the note maps", 1),
    (ARCH + "README.md", "old Figures 7–16 are Figures 10–16 and 24–26", "old Figures 7–16 are Figures 11–17 and 25–27", 1),
    (ARCH + "README.md", "# Figure 1 and Figures 28-33 and 35-39 (schematics)",
     "# Figure 1 and Figures 29-34 and 36-40 (schematics)", 1),
    (ARCH + "README.md", "(Figures 28–33 and 35–39: the two composites", "(Figures 29–34 and 36–40: the two composites", 1),
    (ARCH + "README.md", "`fig17_bandwidth_phase_margin_all_parts` (Figure 17: robust",
     "`fig17_bandwidth_phase_margin_all_parts` (Figure 18: robust", 1),
    (ARCH + "README.md", "`fig18_noise_penalty_all_parts` (Figure 20: band penalty",
     "`fig18_noise_penalty_all_parts` (Figure 21: band penalty", 1),
    (ARCH + "README.md", "`fig19_dynamic_range_all_parts` (Figure 22: electronic",
     "`fig19_dynamic_range_all_parts` (Figure 23: electronic", 1),
    (ARCH + "README.md", "`fig20_benchmark_50ohm` (Figure 27: small-signal", "`fig20_benchmark_50ohm` (Figure 28: small-signal", 1),
    (ARCH + "README.md", "it also draws Figure 34 (`figures/fig26b_sink_vs_plain`",
     "it also draws Figure 35 (`figures/fig26b_sink_vs_plain`", 1),
    (ARCH + "parasitic_cf/INDEX.md", "Draws Figures 40–45 of Appendix G", "Draws Figures 41–46 of Appendix G", 1),
    (ARCH + "parasitic_cf/INDEX.md", "The potentials in Figures 42–44 come from", "The potentials in Figures 43–45 come from", 1),
    (ARCH + "parasitic_cf/INDEX.md", "and the OPA855 network of Figure 45.", "and the OPA855 network of Figure 46.", 1),
    (ARCH + "parasitic_cf/INDEX.md", "(the mesh of Figures 47c and 48)", "(the mesh of Figures 48c and 49)", 1),
    (ARCH + "parasitic_cf/INDEX.md", "for the text beside Figure 48.", "for the text beside Figure 49.", 1),
    (ARCH + "parasitic_cf/INDEX.md",
     "Draws Figures 46–53, in the files `fig44`–`fig51`, from the records (Figures 47c and 48 solve the 0402 model once).",
     "Draws Figures 47–54, in the files `fig44`–`fig51`, from the records (Figures 48c and 49 solve the 0402 model once).", 1),
    (ARCH + "sink_vs_plain_hv.py", "With --figure it also draws Figure 34 of the note",
     "With --figure it also draws Figure 35 of the note", 1),
    (ARCH + "sink_vs_plain_hv.py", '"""Figure 34: Eqs. (1) and (2) in dB', '"""Figure 35: Eqs. (1) and (2) in dB', 1),
    (ARCH + "sink_vs_plain_hv.py", 'print(f"Figure 34 written to', 'print(f"Figure 35 written to', 1),
    (ARCH + "make_schematics.py", "and Figures 28 onwards).", "and Figures 29 onwards).", 1),
    (NUM + "g_closed_forms_2d.py", "# Figure 45 so that A lies at +x", "# Figure 46 so that A lies at +x", 1),
    (NUM + "g_eight_lead_3d.py", "Figure 48).  The OPA846 cases", "Figure 49).  The OPA846 cases", 1),
    (NUM + "make_numerical_figures.py",
     '"""Figures 46-53 of Appendix G (the numerical section; files fig44-fig51), from the recorded results.',
     '"""Figures 47-54 of Appendix G (the numerical section; files fig44-fig51), from the recorded results.', 1),
    (NUM + "make_numerical_figures.py", "Only Figures 47c and 48 (fig44, fig45) need a field",
     "Only Figures 48c and 49 (fig44, fig45) need a field", 1),
    (NUM + "make_numerical_figures.py", "The feedback network of Figure 45 in three dimensions",
     "The feedback network of Figure 46 in three dimensions", 1),
    (NUM + "field_regions.py", "those of Figures 47c and 48 (make_numerical_figures.py, solved_0402)",
     "those of Figures 48c and 49 (make_numerical_figures.py, solved_0402)", 1),
    (NUM + "render_layout_views.py", "and Figure 53 of the note", "and Figure 54 of the note", 1),
    (NUM + "render_layout_views.py", "and Figure 52 of the note", "and Figure 53 of the note", 1),
    (NUM + "development/check_iso_faces.py", "view of the published Figures 47, 52 and 53, files fig44, fig50 and fig51).",
     "view of the published Figures 48, 53 and 54, files fig44, fig50 and fig51).", 1),
    ("pcbcap/pcbcap/parts.py", "Symbols as in the companion note's Figure 40.", "Symbols as in the companion note's Figure 41.", 1),
    (VIEWS + "index.html", "Figure 53 of the note", "Figure 54 of the note", 3),
    (VIEWS + "index.html", "Figure 52 of the note", "Figure 53 of the note", 1),
    (VIEWS + "opa846_sot23_around_0402.html", "Figure 53 of the note", "Figure 54 of the note", 1),
    (VIEWS + "opa846_sot23_double_sided_0402.html", "Figure 53 of the note", "Figure 54 of the note", 1),
    (VIEWS + "opa846_sot23_under_body_0402.html", "Figure 53 of the note", "Figure 54 of the note", 1),
    (VIEWS + "opa855_network.html", "Figure 52 of the note", "Figure 53 of the note", 1),
]
PATTERNS = [  # (file, regex with three groups, replacement, expected count): every match is one of the note's figures
    (ARCH + "parasitic_cf/make_parasitic_cf_figures.py", r"(Figures )(40)(-45)", lambda m: "Figures 41-46", 1),
    (ARCH + "parasitic_cf/make_parasitic_cf_figures.py", r"(Figure )(4[0-5])(\b)", shift, 12),
    (NUM + "field_regions.py", r"(Figure )(48)([ab]?\b)", shift, 5),
    (NUM + "g_resistor_3d.py", r"(Figure )(45)(\b)", shift, 5),
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
