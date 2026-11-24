"""Copy the exploratory checks written while Section 4.11.9 was worked out (the first slew-rate tests, the first
comparisons of the SPICE pulses with the time-domain model, the charge budget at the peak and the probe of the
macromodel's input stage) from a working folder into scripts_archive/board_1k5_diagnostics/, as
archive_board_1k5_diagnostics.py did for Sections 4.11.6-4.11.8.  Each absolute path is replaced by a path relative
to the archived copy, a header line says what the script was for and what replaced it, and an existing file is
never overwritten.

Usage: python archive_spice_check_scratch.py <working folder>
"""
import re
import sys
from pathlib import Path

SRC = Path(sys.argv[1]).resolve()
ARCH = Path(__file__).resolve().parents[1]
DEST = ARCH / "board_1k5_diagnostics"

JOBS = {   # file: what it was for, and what replaced it
    "run_slew_tests.py": "Tests 1 and 2 of the slew-rate limit at four internal slew rates on both rational open loops, "
                         "before the calibration; superseded by tia_pulse_response.note_cases (Table 4.9)",
    "compare_spice_model.py": "the first five SPICE pulses per board against the time-domain model on SPICE's node with "
                              "the macromodel's 3.07 pF added; superseded by spice_board_pulses.py report, which sets each "
                              "description on its own fit of the measured gain. It reads the first version of "
                              "spice/results/board_pulses.json, which spice_board_pulses.py run has since replaced",
    "budget_spice_model.py": "where a pulse's charge has gone by the output's peak, in SPICE and in the model: the share "
                             "that the node's own voltage drives through R_F came out the same in both, which pointed to "
                             "the input stage. It reads the first version of spice/results/board_pulses.json",
    "diag_waveforms.py": "the first five SPICE pulses against the model on its own fit, drawn; superseded by Figure 14. "
                         "It reads the first version of spice/results/board_pulses.json",
    "probe_internal.py": "the macromodel's internal nodes (pin, base, tail, collector loads, integrating node, output) "
                         "during three pulses on the board; superseded by the probe step of spice_board_pulses.py",
}

REPLACE = [   # (pattern, replacement): the working copies' absolute paths and their relative spellings
    (r'Path\(r"[A-Za-z]:[^"]*[/\\]scripts_archive"\)', 'Path(__file__).resolve().parents[1]'),
    (r'Path\(r"[A-Za-z]:[^"]*"\)', 'Path(__file__).resolve().parent'),    # the working folder, where outputs went
    (r'sys\.path\.insert\(0, "\."\)', 'sys.path.insert(0, "..")'),
    (r'"\.\./data/', '"../../data/'),
    (r'"\.\./spice/', '"../../spice/'),
]


def main():
    DEST.mkdir(exist_ok=True)
    for name, purpose in JOBS.items():
        out = DEST / name
        if out.exists():
            print(f"exists, left alone: {out.name}")
            continue
        text = (SRC / name).read_bytes().decode("utf-8").replace("\r\n", "\n")
        for pat, rep in REPLACE:
            text = re.sub(pat, lambda m: rep, text)
        if re.search(r'[A-Za-z]:[/\\]', text):
            sys.exit(f"{name}: an absolute path is left; nothing written for it")
        header = f"# Exploratory check for Section 4.11.9 of the note, kept as the record: {purpose}.\n# Run from this folder.\n"
        out.write_bytes((header + text).encode("utf-8"))
        print(f"written {out.name}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
