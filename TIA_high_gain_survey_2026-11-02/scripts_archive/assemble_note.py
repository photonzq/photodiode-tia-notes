"""Assemble the note TIA_high_gain_survey.md from the chapter files in parts/,
in file-name order, with LF line endings.  A line <!-- table: name --> in a
chapter file is replaced by the generated table body
data/results/note_tables/<name>.md (written by hg_tables.py and
hg_spice_tables.py), so that the chapters' tables always match the results.

Usage:  python assemble_note.py
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
PARTS = sorted((ROOT / "parts").glob("*.md"))
OUT = ROOT / "TIA_high_gain_survey.md"
TABLES = ROOT / "data" / "results" / "note_tables"


def fill_tables(text: str) -> str:
    out = []
    for line in text.split("\n"):
        s = line.strip()
        if s.startswith("<!-- table:") and s.endswith("-->"):
            name = s[len("<!-- table:"):-3].strip()
            out.append((TABLES / f"{name}.md").read_text(encoding="utf-8").strip("\n"))
        else:
            out.append(line)
    return "\n".join(out)


chunks = []
for part in PARTS:
    text = part.read_text(encoding="utf-8").replace("\r\n", "\n").strip("\n")
    chunks.append(fill_tables(text))
with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
    fh.write("\n\n".join(chunks) + "\n")
print(f"{OUT.name}: {len(PARTS)} parts, {sum(len(c) for c in chunks)} characters")
