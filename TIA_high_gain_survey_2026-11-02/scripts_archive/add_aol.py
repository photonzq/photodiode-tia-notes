"""Add each amplifier's typical DC open-loop gain (dB) to data/amplifiers.json, read from
the rendered 'open-loop gain' rows of the datasheets (and, for the four parts taken from the
companion note, from its records).  One-off edit, kept for the record.

Usage:  python add_aol.py
"""
import json
import pathlib

P = pathlib.Path(__file__).resolve().parent.parent / "data" / "amplifiers.json"
AOL = {
    "ADA4530-1": (143, "Large signal voltage gain 143 dB typ, 5 V, RL = 2 kOhm (p. 3); 150 and 155 dB at 10 and 15 V (pp. 5-6)"),
    "OPA928": (126, "AOL 126 dB typ, RL = 10 kOhm (p. 4); 120 dB with 2 kOhm"),
    "LMP7721": (111, "Large signal voltage gain 111 dB typ at 5 V, RL = 2 kOhm (p. 6); 107 dB at 2.7 V (p. 5)"),
    "LMC662": (126, "AOL 2000 V/mV typ, sourcing, LMC66xAI (p. 7)"),
    "ADA4625-1": (150, "Large signal voltage gain 150 dB typ, +-18 V, RL = 2 kOhm (p. 3); 145 dB at 5 V (p. 5)"),
    "OPA828": (130, "AOL 130 dB typ, RL = 600 Ohm (p. 6)"),
    "OPA827": (126, "AOL 126 dB typ, RL = 1 kOhm (p. 6)"),
    "OPA140": (126, "AOL 126 dB typ, RL = 10 kOhm and 2 kOhm (p. 7)"),
    "OPA145": (123, "AOL 123 dB typ, RL = 10 kOhm (p. 7)"),
    "OPA1656": (150, "AOL 150 dB typ, RL = 600 Ohm; 154 dB with 2 kOhm (p. 6)"),
    "OPA2156": (154, "AOL 154 dB typ, +-18 V, SOIC (p. 6)"),
    "OPA320": (132, "AOL 132 dB typ, RL = 10 kOhm (p. 8)"),
    "OPA381": (135, "AOL 135 dB typ (p. 3)"),
    "OPA388": (148, "AOL 148 dB typ, RL = 10 kOhm (p. 9)"),
    "OPA656": (75, "AOL 75 dB typ, VCM = 0 V (p. 5)"),
    "OPA211": (110, "AOL row of the OPA211 table, 110 dB as printed (p. 10)"),
    "OPA657": (70, "companion record: 70 dB typ, RL = 100 Ohm (p. 5); 74.8 dB curve plateau (p. 10)"),
    "OPA818": (92, "companion record: 92 dB typ, RL = 100 Ohm (p. 5)"),
    "ADA4817-1": (65, "companion record: 65 dB typ at +-5 V, RL = 100 Ohm (p. 3)"),
    "LTC6268-10": (108, "companion record: 250 V/mV typ, RL = 10 kOhm (p. 4)"),
}
data = json.loads(P.read_text(encoding="utf-8"))
for name, (db, note) in AOL.items():
    data["parts"][name]["aol_db"] = db
    data["parts"][name]["aol_note"] = note
with open(P, "w", encoding="utf-8", newline="\n") as fh:
    json.dump(data, fh, indent=1, ensure_ascii=False)
missing = [k for k in data["parts"] if "aol_db" not in data["parts"][k]]
print("parts without a datasheet AOL (model uses 120 dB):", missing)
