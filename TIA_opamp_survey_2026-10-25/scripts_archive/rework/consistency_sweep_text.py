"""Consistency sweep of the balanced-photodiode note's text (3 November 2026): the two composites
named and pointed to wherever they appear before Chapter 7, figures and tables cited in the
sections that hold them, abbreviations defined at first use, the analytical model called by one
name, and "gain-bandwidth" spelled with an en dash throughout.

The pairs are read from consistency_sweep_pairs.txt next to this script (each old text must occur
once); the spelling change must find exactly the expected number of hyphenated forms. The note is
written only if it still has the hash it had when the pairs were drafted.

Usage: python consistency_sweep_text.py [EXPECTED_HASH]
"""
import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOC = HERE.parents[1] / "TIA_opamp_survey.md"
EXPECTED = sys.argv[1] if len(sys.argv) > 1 else "9fbaeeeb5011"
HYPHENATED = 10


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

pairs = read_pairs(HERE / "consistency_sweep_pairs.txt")
for k, (old, new) in enumerate(pairs, 1):
    n = s.count(old)
    assert n == 1, f"pair {k}: old text found {n} times: {old[:80]!r}"
    s = s.replace(old, new)

n = s.count("gain-bandwidth")
assert n == HYPHENATED, f"expected {HYPHENATED} hyphenated 'gain-bandwidth', found {n}"
s = s.replace("gain-bandwidth", "gain–bandwidth")

out = s.encode("utf-8")
DOC.write_bytes(out)
print(f"{len(pairs)} pairs and {n} spellings applied; written {hashlib.sha256(out).hexdigest()[:12]}")
