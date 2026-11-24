"""Move Figure 12 of Section 4.11.7 (its image line and caption) to just before the caption of a given table, so
that the built PDF splits neither its caption nor a table's caption from its table.  It was run twice: first
before Table 4.6 (which left Table 4.7's caption alone at the foot of a page), then before Table 4.7, the order
in which the text cites them (Table 4.6, Figure 12, Table 4.7).

Usage: python move_figure_12.py NOTE EXPECTED_HASH [--before "Table 4.7"] [--dry-run]

The note is written only if its SHA-256 starts with EXPECTED_HASH, the image line and the caption that follows it
each occur once, and the caption of the target table occurs once.
"""
import hashlib
import sys
from pathlib import Path


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    note, expected, dry = Path(sys.argv[1]), sys.argv[2], "--dry-run" in sys.argv
    target = sys.argv[sys.argv.index("--before") + 1] if "--before" in sys.argv else "Table 4.6"
    raw = note.read_bytes()
    if hashlib.sha256(raw).hexdigest()[:12] != expected:
        sys.exit("hash differs; nothing written")
    lines = raw.decode("utf-8").split("\n")
    img = [i for i, ln in enumerate(lines) if ln.startswith("![Figure 12](")]
    cap = [i for i, ln in enumerate(lines) if ln.startswith("*Figure 12. ")]
    tab = [i for i, ln in enumerate(lines) if ln.startswith(f"*{target}. ")]
    if not (len(img) == len(cap) == len(tab) == 1 and cap[0] == img[0] + 2 and lines[img[0] + 1] == ""):
        sys.exit(f"image {img}, caption {cap}, {target} {tab}: not as expected; nothing written")
    i = img[0]
    block = lines[i:i + 3]
    rest = lines[:i - 1] + lines[i + 3:] if lines[i - 1] == "" else lines[:i] + lines[i + 3:]
    t = next(k for k, ln in enumerate(rest) if ln.startswith(f"*{target}. "))
    out = rest[:t] + block + [""] + rest[t:]
    print(f"moved lines {i + 1}-{i + 3} to before {target} (now line {t + 1})")
    if dry:
        return
    data = "\n".join(out).encode("utf-8")
    note.write_bytes(data)
    print(f"written; new hash {hashlib.sha256(data).hexdigest()[:12]}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
