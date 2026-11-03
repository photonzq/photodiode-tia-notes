"""Plain-wording pass over the balanced-photodiode note (3 November 2026): headings rewritten in
plain words, and section openings given the reason for the section and what it delivers.

The old/new pairs are read from a text file (default: plain_wording_pass_pairs.txt next to this
script). The note is written only if it still has the hash it had when the pairs were drafted and
every old text occurs exactly once.

Usage: python plain_wording_pass.py [PAIRS_FILE] [EXPECTED_HASH]
"""
import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOC = HERE.parents[1] / "TIA_opamp_survey.md"
PAIRS = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "plain_wording_pass_pairs.txt"
EXPECTED = sys.argv[2] if len(sys.argv) > 2 else "d99b7b7909dc"


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
for k, (old, new) in enumerate(pairs, 1):
    n = s.count(old)
    assert n == 1, f"pair {k}: old text found {n} times: {old[:80]!r}"
    s = s.replace(old, new)

out = s.encode("utf-8")
DOC.write_bytes(out)
print(f"{len(pairs)} pairs applied; written {hashlib.sha256(out).hexdigest()[:12]}")
