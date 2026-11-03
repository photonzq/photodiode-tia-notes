"""Edit of 2 November 2026: set the gain-bandwidth product of one amplifier in
data/amplifiers.json, with a note on where the value comes from.

Usage:  python set_gbw.py PART MHZ "NOTE"
        e.g. python set_gbw.py OPA2156 25 "25 MHz at G = 100, 20 MHz unity-gain (p. 6); ..."
"""
import json
import pathlib
import sys

PATH = pathlib.Path(__file__).resolve().parent.parent / "data" / "amplifiers.json"
part_name, mhz, note = sys.argv[1], float(sys.argv[2]), sys.argv[3]

data = json.loads(PATH.read_text(encoding="utf-8"))
part = data["parts"][part_name]
part["gbw"] = int(mhz) if mhz == int(mhz) else mhz
part["gbw_note"] = note
with open(PATH, "w", encoding="utf-8", newline="\n") as fh:
    json.dump(data, fh, indent=1, ensure_ascii=False)
print(part_name, "gbw =", part["gbw"], "MHz")
