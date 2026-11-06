"""Number the first three figures of Section G.14 in the order in which they are cited and placed.

Usage: python reorder_g14_figures.py [--dry-run]

Section G.14.2 cites and places the checks of the field solver before Section G.14.4 cites the model and its
field, yet they were numbered 47, 45 and 46. This edit renumbers them 45 (checks), 46 (model) and 47 (field), in
the note, in its mirrored template numerical_section_template.md, and in the pointers of parasitic_cf/INDEX.md,
field_regions.py, g_eight_lead_3d.py and development/check_iso_faces.py. The image files keep their names
(fig46_* is now Figure 45, fig44_* Figure 46 and fig45_* Figure 47). Every replacement carries enough context to
occur exactly as often as listed; nothing is written unless all of them do.
"""
import sys
from pathlib import Path

NOTE_DIR = Path(__file__).resolve().parents[2]            # TIA_opamp_survey_2026-10-25
NUM = "scripts_archive/parasitic_cf/numerical/"
G14 = [  # the same text stands in the note and in the template
    ("dimensions (Figure 47b)", "dimensions (Figure 45b)"),
    ("![Figure 47](figures/fig46_", "![Figure 45](figures/fig46_"),
    ("*Figure 47. Checks of the field solver", "*Figure 45. Checks of the field solver"),
    ("Figure 45 shows the model of an 0402", "Figure 46 shows the model of an 0402"),
    ("![Figure 45](figures/fig44_", "![Figure 46](figures/fig44_"),
    ("*Figure 45. The three-dimensional model", "*Figure 46. The three-dimensional model"),
    ("Figure 46 shows the field on the", "Figure 47 shows the field on the"),
    ("middle mesh of Figure 45c,", "middle mesh of Figure 46c,"),
    ("window of Figure 46b the density", "window of Figure 47b the density"),
    ("![Figure 46](figures/fig45_", "![Figure 47](figures/fig45_"),
    ("*Figure 46. The field of the 0402 model of Figure 45 on the plane",
     "*Figure 47. The field of the 0402 model of Figure 46 on the plane"),
]
EDITS = (
    [("TIA_opamp_survey.md", old, new, 1) for old, new in G14]
    + [(NUM + "numerical_section_template.md", old, new, 1) for old, new in G14]
    + [
        ("scripts_archive/parasitic_cf/INDEX.md", "(the mesh of Figures 45c and 46)", "(the mesh of Figures 46c and 47)", 1),
        ("scripts_archive/parasitic_cf/INDEX.md", "for the text beside Figure 46.", "for the text beside Figure 47.", 1),
        ("scripts_archive/parasitic_cf/INDEX.md", "(Figures 45c and 46 solve the 0402 model once)",
         "(Figures 46c and 47 solve the 0402 model once)", 1),
        (NUM + "field_regions.py", "Figure 46", "Figure 47", 5),
        (NUM + "g_eight_lead_3d.py", "Figure 46).  The OPA846 cases", "Figure 47).  The OPA846 cases", 1),
        (NUM + "development/check_iso_faces.py", "the published Figures 45, 51 and 52, files fig44",
         "the published Figures 46, 51 and 52, files fig44", 1),
    ]
)


def main():
    dry = "--dry-run" in sys.argv
    texts, ok = {}, True
    for rel, old, new, want in EDITS:
        text = texts.setdefault(rel, (NOTE_DIR / rel).read_bytes().decode("utf-8"))
        got = text.count(old)
        print(f"{'ok ' if got == want else 'BAD'} {rel}: {got} of {want}  {old[:58]!r}")
        ok &= got == want
        texts[rel] = text.replace(old, new)
    if not ok:
        sys.exit("a count did not match; nothing written")
    if dry:
        print("dry run; nothing written")
        return
    for rel, text in texts.items():
        (NOTE_DIR / rel).write_bytes(text.encode("utf-8"))
    print(f"written: {len(texts)} files")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
