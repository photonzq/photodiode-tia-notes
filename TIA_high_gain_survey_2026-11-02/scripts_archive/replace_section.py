"""Replace one section of a chapter file in parts/ by a new text (2 November 2026).

The old section runs from the line START up to, not including, the line END.  The script
refuses to write unless the old section contains the text GUARD, so that a section that
someone else has changed in the meantime is not overwritten.

Usage:  python replace_section.py PART START END NEW_TEXT GUARD
        e.g. python replace_section.py 07_beyond.md "### 7.3" "### 7.4" new_7_3.md "SBOA034, p. 6, Table II"
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
part, start, end, new_path, guard = sys.argv[1:6]
path = ROOT / "parts" / part
text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
i0 = text.index(start)
i1 = text.index(end, i0 + len(start))
old = text[i0:i1]
if guard not in old:
    sys.exit("The old section does not contain the guard text; nothing changed.")
new = pathlib.Path(new_path).read_text(encoding="utf-8").replace("\r\n", "\n").strip("\n")
with open(path, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(text[:i0] + new + "\n\n" + text[i1:])
print(f"{part}: section replaced, {len(old)} -> {len(new)} characters")
