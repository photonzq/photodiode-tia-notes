"""Add Section 6.9 (noise at low frequencies) and Table A6.37 to the balanced-photodiode note, with the
references to them in Chapter 6, Section 9.2 and Appendix C (3 November 2026).

The pairs are read from low_frequency_section_pairs.txt next to this script; @@TABLE_A6_37@@ in a new
text is replaced by data/results/table_a6_37.md, which low_frequency_noise.py writes. Each old text
must occur once, and the note is written only if it still has the hash it had when the pairs were
drafted.

Usage: python low_frequency_section.py [EXPECTED_HASH]
"""
import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DOC = ROOT / "TIA_opamp_survey.md"
EXPECTED = sys.argv[1] if len(sys.argv) > 1 else "fab4d2add47d"


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
table = (ROOT / "data" / "results" / "table_a6_37.md").read_text(encoding="utf-8").strip("\n")

pairs = read_pairs(HERE / "low_frequency_section_pairs.txt")
for k, (old, new) in enumerate(pairs, 1):
    n = s.count(old)
    assert n == 1, f"pair {k}: old text found {n} times: {old[:80]!r}"
    s = s.replace(old, new.replace("@@TABLE_A6_37@@", table))

out = s.encode("utf-8")
DOC.write_bytes(out)
print(f"{len(pairs)} pairs applied; written {hashlib.sha256(out).hexdigest()[:12]}")
