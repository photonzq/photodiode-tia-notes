"""Copy the exploratory checks written while Section 4.11.6-4.11.8 was worked out (the noise split, the second-board
scan, the resistor at the summing node, the rational open-loop fits and the curve's precursor) from a working folder
into scripts_archive/board_1k5_diagnostics/.  Each absolute path in a script is replaced by a path relative to the
archived copy, a header line says what the script was for, and an existing file is never overwritten.

Usage: python archive_board_1k5_diagnostics.py <working folder>
"""
import re
import sys
from pathlib import Path

SRC = Path(sys.argv[1]).resolve()
ARCH = Path(__file__).resolve().parents[1]
DEST = ARCH / "board_1k5_diagnostics"
NOTE_DIR = ARCH.parent.as_posix()          # the scripts spelled the note's folder with forward slashes

JOBS = {   # file: what it was for, and what replaced it
    "noise_split.py": "the board's noise floor split into a white part at the node and one at the oscilloscope, with the "
                      "capacitance free and band by band; superseded by compare_opa846_1k5_board.noise_section",
    "explore_v2_noise.py": "the second board: phase margin, peaking and bandwidth against the total C_F in the two input-pole "
                           "fits, the C_F for 0.01-3 dB and 45-60 deg; superseded by compare_opa846_1k5_board.second_board_section",
    "explore_rx.py": "the gain refitted with a resistor of 0.54-6.6 kOhm from the summing node to ground (a coarse grid); "
                     "compare_opa846_1k5_board.fit_rx keeps the 673-ohm case",
    "explore_rx2.py": "the capacitance to add with a 540-ohm resistor at the node; superseded by second_board_section",
    "explore_v2_all.py": "the capacitance to add for every stable fit of Table 4.4; superseded by second_board_section",
    "explore_olfit.py": "tia_model.fit_open_loop (two poles and a delay) on the OPA846 curve: its loop misses the curve's "
                        "phase margin by 2-3 deg, the reason for the rational fit of tia_pulse_response.py",
    "explore_olfit2.py": "rational fits with 0-2 zeros and 2-3 higher poles to the datasheet curve and the macromodel's A_-, "
                         "and their loops against the curves'; the choice of one zero and three poles",
    "explore_olfit3.py": "the board's gain refitted with the rational datasheet models, and the capacitance to add in each; "
                         "superseded by tia_pulse_response.note_cases",
    "check_tail.py": "the inverse transform of the curve's Z_T over the window: its precursor before t = 0; superseded by "
                     "the precursor printed by tia_pulse_response.run_case",
}


def sanitise(text):
    text = text.replace(f'r"{NOTE_DIR}/scripts_archive"', "str(ARCH)")
    text = text.replace(f'r"{NOTE_DIR}/data/measurements/opa846_1k5_board_per_MHz.csv"',
                        'str(ARCH.parent / "data" / "measurements" / "opa846_1k5_board_per_MHz.csv")')
    text = text.replace(f'r"{NOTE_DIR}/spice/runs/aol/OPA846_inverting/aol.txt"',
                        'str(ARCH.parent / "spice" / "runs" / "aol" / "OPA846_inverting" / "aol.txt")')
    text = text.replace(f'r"{NOTE_DIR}/data/results/tia_pulse_response_opa846_1k5.json"',
                        'str(ARCH.parent / "data" / "results" / "tia_pulse_response_opa846_1k5.json")')
    text = text.replace(f'r"{SRC.as_posix()}/explore_olfit2.py"', 'str(HERE / "explore_olfit2.py")')
    text = text.replace(f'r"{SRC.as_posix()}"', "str(HERE)")
    lines = text.split("\n")
    k = next(i for i, ln in enumerate(lines) if "sys.path.insert(0," in ln)
    lines[k:k] = ["from pathlib import Path as _Path", "HERE = _Path(__file__).resolve().parent", "ARCH = HERE.parent"]
    return "\n".join(lines)


def main():
    DEST.mkdir(exist_ok=True)
    for name, purpose in JOBS.items():
        out = DEST / name
        if out.exists():
            print(f"exists, left alone: {out.name}")
            continue
        text = sanitise((SRC / name).read_bytes().decode("utf-8").replace("\r\n", "\n"))
        if re.search(r'[A-Za-z]:[/\\][^"\n]*', text.split('"""', 2)[-1] if text.startswith('"""') else text):
            sys.exit(f"{name}: an absolute path is left; nothing written for it")
        header = f"# Exploratory check for Section 4.11 of the note, kept as the record: {purpose}.\n# Run from this folder.\n"
        out.write_bytes((header + text).encode("utf-8"))
        print(f"written {out.name}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
