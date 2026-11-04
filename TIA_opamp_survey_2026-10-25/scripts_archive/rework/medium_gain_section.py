"""Add Section 6.10 (larger feedback resistors, up to 10 kOhm) and Tables A6.38-A6.39 to the balanced-photodiode note,
with the box, the chapter overview, the opening of Chapter 6, Section 9.2 and Appendices C and E (4 November 2026),
and drop the date from the subtitle.

The pairs are read from medium_gain_section_pairs.txt next to this script; @@TABLE_A6_38@@ and @@TABLE_A6_39@@ in a
new text are replaced by data/results/table_a6_38.md and table_a6_39.md, which medium_gain.py writes. Each old text
must occur once, and the note is written only if it still has the hash it had when the pairs were drafted.

Usage: python medium_gain_section.py [EXPECTED_HASH]
"""
import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DOC = ROOT / "TIA_opamp_survey.md"
EXPECTED = sys.argv[1] if len(sys.argv) > 1 else "1f3e2d353a1c"


def read_pairs(path):
    """Return the (old, new) pairs of a pairs file; text between the markers is kept exactly."""
    pairs, old, new, mode = [], [], [], None
    for line in path.read_text(encoding="utf-8").split("\n"):
        if line == "=== OLD":
            mode, old, new = "old", [], []
        elif line == "=== NEW":
            mode = "new"
        elif line == "=== END":
            pairs.append(("\n".join(old), "\n".join(new)))
            mode = None
        elif mode == "old":
            old.append(line)
        elif mode == "new":
            new.append(line)
    return pairs


raw = DOC.read_bytes()
digest = hashlib.sha256(raw).hexdigest()[:12]
assert digest == EXPECTED, f"note changed since the pairs were drafted ({digest})"
s = raw.decode("utf-8")
tables = {n: (ROOT / "data" / "results" / f"table_a6_{n}.md").read_text(encoding="utf-8").strip("\n") for n in (38, 39)}
pairs = read_pairs(HERE / "medium_gain_section_pairs.txt")
for old, new in pairs:
    n = s.count(old)
    assert n == 1, f"{n} occurrences of: {old[:80]!r}"
for old, new in pairs:
    for k, t in tables.items():
        new = new.replace(f"@@TABLE_A6_{k}@@", t)
    s = s.replace(old, new)
assert "@@TABLE" not in s
DOC.write_bytes(s.encode("utf-8"))
print(f"{len(pairs)} pairs applied; note hash {hashlib.sha256(s.encode('utf-8')).hexdigest()[:12]}")
