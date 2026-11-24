"""Replace Section 4.11 of the note (from its heading to the end of its last paragraph, before the rule that closes
Chapter 4) with a new text, here the version in ten subsections that adds the noise diagnosis, the second board and
the pulse response.

Usage: python replace_section_4_11.py NOTE EXPECTED_HASH NEW_SECTION_MD [--dry-run]

EXPECTED_HASH is the first 12 hex digits of the note's SHA-256; the note is written only if it still has that hash.
The old section must start with the line "### 4.11 A measured OPA846 board at 1.5 kΩ with only the parasitic
feedback capacitance" and be followed, after its text, by a line "---" and the heading of Chapter 5; both must occur
exactly once.  The new text keeps the note's line endings.  The script prints the line numbers replaced, the counts
of equations, tables and figures in the old and the new text, and the new hash.
"""
import hashlib
import re
import sys
from pathlib import Path

HEAD = "### 4.11 A measured OPA846 board at 1.5 kΩ with only the parasitic feedback capacitance"
NEXT = "## 5. SPICE cross-check with the vendors' macromodels"


def counts(text):
    return dict(tags=re.findall(r"\\tag\{([^}]*)\}", text), tables=re.findall(r"^\*Table (\d+\.\d+)\.", text, re.M),
                figures=re.findall(r"^!\[Figure (\d+)\]", text, re.M))


def main():
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    note, expected, new_path, dry = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3]), "--dry-run" in sys.argv
    raw = note.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()[:12]
    if digest != expected:
        sys.exit(f"{note.name} has hash {digest}, not {expected}; nothing written")
    text = raw.decode("utf-8")
    nl = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(nl)
    starts = [i for i, ln in enumerate(lines) if ln == HEAD]
    nexts = [i for i, ln in enumerate(lines) if ln == NEXT]
    if len(starts) != 1 or len(nexts) != 1:
        sys.exit(f"heading found {len(starts)} times, next chapter {len(nexts)} times; nothing written")
    s, e = starts[0], nexts[0]
    k = e - 1
    while k > s and lines[k].strip() in ("", "---"):
        k -= 1
    old = nl.join(lines[s:k + 1])
    new = new_path.read_bytes().decode("utf-8").replace("\r\n", "\n").strip("\n").split("\n")
    out = lines[:s] + new + lines[k + 1:]
    print(f"replacing lines {s + 1}-{k + 1} ({k + 1 - s} lines) with {len(new)} lines")
    for label, c in (("old", counts(old)), ("new", counts(nl.join(new)))):
        print(f"  {label}: equations {', '.join(c['tags'])}; tables {', '.join(c['tables'])}; figures {', '.join(c['figures'])}")
    if dry:
        print("dry run; nothing written")
        return
    data = nl.join(out).encode("utf-8")
    note.write_bytes(data)
    print(f"written; new hash {hashlib.sha256(data).hexdigest()[:12]}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
