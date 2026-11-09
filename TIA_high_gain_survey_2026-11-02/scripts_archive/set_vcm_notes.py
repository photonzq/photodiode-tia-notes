"""One-off edit for Section 8.6: states in data/amplifiers.json the input
common-mode voltage at which each bias current of Table A.1 is specified,
where that is not mid-supply, and corrects two text fields that the reading
of the datasheets for Table A.9 showed to be wrong (LMP7721's low-supply
table is 2.5 V, not 2.7 V; OPA656's +-6 V is its largest supply, while its
bias current is specified at +-5 V).

Each old text must match exactly, or nothing is written.  Only text fields
change; no number used by the model is touched.

Usage:  python set_vcm_notes.py
"""
import json
import pathlib

AMPS = pathlib.Path(__file__).resolve().parent.parent / "data" / "amplifiers.json"

EDITS = [
    ("ADA4530-1", "cite",
     "pp. 3-4 (5 V table); 10 V and 15 V tables pp. 4-7 give the same noise, IB and CIN",
     "pp. 3-4 (5 V table, IB at V_CM = V_SY/2; the typical IB is printed as '<1' fA); 10 V and 15 V tables "
     "pp. 4-7 give the same noise, IB and CIN"),
    ("OPA928", "cite",
     "pp. 4-5 (first table); a later table on p. 8 lists IB max 75 fA",
     "pp. 4-5 (first table, 4.5-8 V, IB at V_CM = V+ - 3 V; the 8-16 V table on p. 6 gives the same IB at "
     "V_S/2); the 16-36 V table on p. 8 lists IB max 75 fA"),
    ("LMP7721", "cite",
     "pp. 6-7 (5 V table); 2.7 V table pp. 5-6",
     "pp. 6-7 (5 V table); 2.5 V table pp. 5-6; IB at V_CM = 1 V in both"),
    ("LMC662", "cite",
     "pp. 6-7; current noise: p. 23 (revision history)",
     "pp. 6-7 (5 V, IB at V_CM = 1.5 V); current noise: p. 23 (revision history)"),
    ("OPA656", "supply",
     "+-6 V (p. 2)",
     "+-4 to +-6 V (p. 4); IB specified at +-5 V (p. 5)"),
]


def main() -> None:
    data = json.loads(AMPS.read_text(encoding="utf-8"))
    parts = data["parts"]
    for name, field, old, new in EDITS:
        have = parts[name].get(field)
        if have == new:
            print(f"{name}.{field}: already set")
            continue
        if have != old:
            raise SystemExit(f"{name}.{field} is {have!r}, expected {old!r}; nothing written")
    for name, field, old, new in EDITS:
        parts[name][field] = new
        print(f"{name}.{field}: {new}")
    AMPS.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8", newline="\n")
    print("written", AMPS.name)


if __name__ == "__main__":
    main()
