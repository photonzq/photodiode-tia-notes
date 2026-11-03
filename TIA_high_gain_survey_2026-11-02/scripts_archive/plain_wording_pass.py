"""Plain-wording pass over the chapter files of the high-gain note (3 November 2026): headings
rewritten in plain words, section and chapter openings given the reason for the section and what
it delivers, and two cross-references to the companion note's noise equation corrected.

The pairs are read from a text file (default: plain_wording_pass_pairs.txt next to this script).
A line "=== FILE <part> <hash>" names the file in parts/ that the following pairs edit and its
hash before the edit. A file is written only if it still has that hash and every old text of its
pairs occurs exactly once. Run assemble_note.py afterwards.

Usage: python plain_wording_pass.py [PAIRS_FILE]
"""
import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARTS = HERE.parent / "parts"
PAIRS = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "plain_wording_pass_pairs.txt"


def read_pairs(path):
    """Return {file name: (expected hash, [(old, new), ...])}, keeping the text exactly."""
    files, current, old, new, mode = {}, None, [], [], None
    for line in path.read_text(encoding="utf-8").split("\n"):
        if line.startswith("=== FILE "):
            name, digest = line[len("=== FILE "):].split()
            files[name] = (digest, [])
            current = name
        elif line == "=== OLD":
            mode, old, new = "old", [], []
        elif line == "=== NEW":
            mode = "new"
        elif line == "=== END":
            files[current][1].append(("\n".join(old), "\n".join(new)))
            mode = None
        elif mode == "old":
            old.append(line)
        elif mode == "new":
            new.append(line)
    return files


files = read_pairs(PAIRS)
edited = {}
for name, (expected, pairs) in files.items():
    raw = (PARTS / name).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()[:12]
    assert digest == expected, f"{name} changed since the pairs were drafted ({digest})"
    s = raw.decode("utf-8")
    for k, (old, new) in enumerate(pairs, 1):
        n = s.count(old)
        assert n == 1, f"{name}, pair {k}: old text found {n} times: {old[:80]!r}"
        s = s.replace(old, new)
    edited[name] = (s.encode("utf-8"), len(pairs))

for name, (out, n) in edited.items():
    (PARTS / name).write_bytes(out)
    print(f"{name}: {n} pairs applied; written {hashlib.sha256(out).hexdigest()[:12]}")
