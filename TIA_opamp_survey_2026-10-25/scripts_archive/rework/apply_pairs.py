"""Apply a file of old/new text pairs to the balanced-photodiode note (3 November 2026).

A pairs file holds blocks that run from a line "=== OLD" through "=== NEW" to "=== END"; text between the markers
is kept exactly, and lines outside the blocks are comments. Each old text must occur exactly once, and the note is
written only if it still has the hash it had when the pairs were drafted.

Usage: python apply_pairs.py PAIRS_FILE EXPECTED_HASH
"""
import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOC = HERE.parents[1] / "TIA_opamp_survey.md"
if len(sys.argv) != 3:
    sys.exit(__doc__)
PAIRS, EXPECTED = Path(sys.argv[1]), sys.argv[2]


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
pairs = read_pairs(PAIRS)
for old, new in pairs:
    n = s.count(old)
    assert n == 1, f"{n} occurrences of: {old[:80]!r}"
    s = s.replace(old, new)
DOC.write_bytes(s.encode("utf-8"))
print(f"{len(pairs)} pairs applied; note hash {hashlib.sha256(s.encode('utf-8')).hexdigest()[:12]}")
