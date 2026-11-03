"""Edit of 2 November 2026: set the gain-bandwidth product of OPA1656 in data/amplifiers.json
to the data sheet's value at a gain of 100, 53 MHz (p. 6), instead of its unity-gain bandwidth,
20 MHz, after the check of hg_spice_gbw_check.py.  TI's PSpice model (SBOMAW6, Rev. C) has
55-56 MHz of gain-bandwidth from 10 Hz to 300 kHz, 47 MHz at 1 MHz and unity gain at 21 MHz.

Usage:  python set_gbw_opa1656.py
"""
import json
import pathlib

PATH = pathlib.Path(__file__).resolve().parent.parent / "data" / "amplifiers.json"

data = json.loads(PATH.read_text(encoding="utf-8"))
part = data["parts"]["OPA1656"]
assert part["gbw"] in (20, 53), part["gbw"]
part["gbw"] = 53
part["gbw_note"] = ("53 MHz gain-bandwidth at G = 100, 20 MHz unity-gain bandwidth (p. 6). The model uses 53 MHz: "
                    "TI's PSpice model SBOMAW6 Rev. C has 55-56 MHz from 10 Hz to 300 kHz, 47 MHz at 1 MHz, "
                    "30 MHz at 3 MHz and unity gain at 21 MHz (hg_spice_gbw_check.py).")
with open(PATH, "w", encoding="utf-8", newline="\n") as fh:
    json.dump(data, fh, indent=1, ensure_ascii=False)
print("OPA1656 gbw =", part["gbw"], "MHz")
