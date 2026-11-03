"""Copy the one-off scripts of 2–3 November 2026 (schematics, wording and caption edits of the
balanced-photodiode and high-gain notes) from a working folder into the notes' script archives.
Each absolute path in a script is replaced by a path relative to the archived copy, and an
existing file is never overwritten.

Usage: python archive_session_scripts.py <working folder> <folder holding both notes>
"""
import re
import sys
from pathlib import Path

SRC = Path(sys.argv[1])
ROOT = Path(sys.argv[2]).resolve()
W = str(ROOT)

COMP = "TIA_opamp_survey_2026-10-25"
HG = "TIA_high_gain_survey_2026-11-02"
REWORK = ROOT / COMP / "scripts_archive" / "rework"
HG_ARCH = ROOT / HG / "scripts_archive"


def lit(*parts):
    """The raw-string literal of a path below the notes folder, spelled as the scripts spelled it."""
    return 'r"' + "\\".join([W, *parts]) + '"'


def here(up, *parts):
    """A path expression relative to the archived script, `up` folders above it."""
    base = "Path(__file__).resolve().parent" if up == 0 else f"Path(__file__).resolve().parents[{up}]"
    return " / ".join([base] + [f'"{p}"' for p in parts])


COMP_NOTE = [(f"Path({lit(COMP, 'TIA_opamp_survey.md')})", here(2, "TIA_opamp_survey.md"))]
MAKE_SCHEM = [(f"Path({lit(COMP, 'scripts_archive', 'make_schematics.py')})", here(1, "make_schematics.py"))]
HG_SCHEM = [(f"Path({lit(HG, 'scripts_archive', 'hg_schematics.py')})", here(0, "hg_schematics.py"))]
HV_SCHEM = [(f"Path({lit(HG, 'hv_output_stage', 'scripts', 'hv_schematics.py')})",
             here(1, "hv_output_stage", "scripts", "hv_schematics.py"))]

JOBS = [
    ("edit_companion_schematics.py", REWORK, COMP_NOTE),
    ("edit_companion_language.py", REWORK, COMP_NOTE),
    ("edit_section_4_7_context.py", REWORK, COMP_NOTE),
    ("fix_figs_1.py", REWORK, MAKE_SCHEM),
    ("fix_figs_2.py", REWORK, MAKE_SCHEM),
    ("fix_style3.py", REWORK, [
        (f"Path({lit(COMP, 'scripts_archive', 'schematic_style.py')})", here(1, "schematic_style.py")),
        (lit(HG, "hv_output_stage", "scripts", "schematic_style.py"),
         here(3, HG, "hv_output_stage", "scripts", "schematic_style.py")),
        (lit(HG, "scripts_archive", "schematic_style.py"), here(3, HG, "scripts_archive", "schematic_style.py")),
    ]),
    ("src_test.py", REWORK, []),
    ("extract_openings.py", REWORK, []),
    ("edit_fig1_caption.py", HG_ARCH, [(f"Path({lit(HG, 'parts', '01_problem.md')})", here(1, "parts", "01_problem.md"))]),
    ("edit_hg_parts_schematics.py", HG_ARCH, [(f"Path({lit(HG, 'parts')})", here(1, "parts"))]),
    ("edit_hg_scripts_numbers.py", HG_ARCH, [(f"Path({lit(HG, 'scripts_archive')})", here(0))]),
    ("fill_hg_schem.py", HG_ARCH, HG_SCHEM),
    ("fix_hg_schem2.py", HG_ARCH, HG_SCHEM),
    ("fix_fig1_spacing.py", HG_ARCH, HG_SCHEM),
    ("edit_hv_captions.py", HG_ARCH, [(f"Path({lit(HG, 'hv_output_stage', 'hv_output_stage.md')})",
                                      here(1, "hv_output_stage", "hv_output_stage.md"))]),
    ("fix_hv.py", HG_ARCH, HV_SCHEM),
    ("fix_hv_stage_layout.py", HG_ARCH, HV_SCHEM),
    ("fix_hv_stage_layout2.py", HG_ARCH, HV_SCHEM),
    ("urc_checks.py", HG_ARCH, [(f"sys.path.insert(0, {lit(HG, 'scripts_archive')})",
                                 'sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))')]),
    ("fix_ctrl.py", HG_ARCH, []),
    ("fix_tabs.py", HG_ARCH, []),
]

for name, dest, reps in JOBS:
    s = (SRC / name).read_text(encoding="utf-8")
    for old, new in reps:
        assert old in s, f"{name}: path not found: {old}"
        s = s.replace(old, new)
    assert W not in s and not re.search(r"\b[A-Za-z]:\\", s), f"{name}: an absolute path is left"
    out = dest / name
    assert not out.exists(), f"{out} exists already"
    out.write_bytes(s.replace("\r\n", "\n").encode("utf-8"))
    print(f"{name} -> {out.relative_to(ROOT).as_posix()} ({len(reps)} paths made relative)")
