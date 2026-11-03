"""One-off edit of 2 November 2026: replace the hand-copied bodies of Tables 4a, 4b
and 6.1-6.5 in parts/04_maps.md and parts/06_selection.md by placeholders
<!-- table: name -->, which assemble_note.py fills from data/results/note_tables/.
The table body is the block of lines starting with "|" that follows the caption.

Usage:  python edit_table_placeholders.py
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
JOBS = {"04_maps.md": {"*Table 4a.": "table_4a", "*Table 4b.": "table_4b"},
        "06_selection.md": {f"*Table 6.{k}.": f"table_6_{k}" for k in range(1, 6)}}

for fname, captions in JOBS.items():
    path = ROOT / "parts" / fname
    lines = path.read_text(encoding="utf-8").replace("\r\n", "\n").split("\n")
    out, i, done = [], 0, set()
    while i < len(lines):
        out.append(lines[i])
        cap = next((c for c in captions if lines[i].startswith(c)), None)
        i += 1
        if cap is None:
            continue
        while i < len(lines) and lines[i].strip() == "":
            out.append(lines[i])
            i += 1
        if i < len(lines) and lines[i].startswith("|"):
            while i < len(lines) and lines[i].startswith("|"):
                i += 1
            out.append(f"<!-- table: {captions[cap]} -->")
            done.add(cap)
    missing = set(captions) - done
    assert not missing, f"{fname}: no table body after {missing}"
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out))
    print(fname, sorted(done))
