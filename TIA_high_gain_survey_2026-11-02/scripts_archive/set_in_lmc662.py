"""Edit of 2 November 2026: set the input current noise of LMC662 in data/amplifiers.json to
the 0.2 fA/rtHz of its data sheet's Revision C instead of the 4 fA/rtHz of Revision D.

Revision D (SNOSC51D, Feb. 2024) gives 4 fA/rtHz at 1 kHz (p. 6), and its revision history
(p. 23) states that this replaced 0.0002 pA/rtHz "to align with modern noise test setup".
The physical floor, the shot noise of the ~2-fA input leakage, is about 0.025 fA/rtHz.

Usage:  python set_in_lmc662.py
"""
import json
import pathlib

PATH = pathlib.Path(__file__).resolve().parent.parent / "data" / "amplifiers.json"

data = json.loads(PATH.read_text(encoding="utf-8"))
part = data["parts"]["LMC662"]
assert part["in_"] in ({"1000": 4}, {"1000": 0.2}), part["in_"]
part["in_"] = {"1000": 0.2}
part["in_note"] = ("0.2 fA/rtHz at 1 kHz from Revision C, as quoted in the Revision D history (p. 23): "
                   "'Changed input current noise density from 0.0002pA/rtHz to 4fA/rtHz to align with modern "
                   "noise test setup'. Revision D gives 4 fA/rtHz (p. 6). The shot noise of the ~2-fA input "
                   "leakage is about 0.025 fA/rtHz.")
part["cite"] = "pp. 6-7; current noise: p. 23 (revision history)"
with open(PATH, "w", encoding="utf-8", newline="\n") as fh:
    json.dump(data, fh, indent=1, ensure_ascii=False)
print("LMC662 in_ =", part["in_"])
