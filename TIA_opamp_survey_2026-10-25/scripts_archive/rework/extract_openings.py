"""List every heading of a Markdown note with the first prose paragraph after it (images,
captions, tables and display maths skipped), to review titles and section openings."""
import sys
from pathlib import Path

src, dst = Path(sys.argv[1]), Path(sys.argv[2])
lines = src.read_text(encoding="utf-8").splitlines()
out = []
i = 0
while i < len(lines):
    ln = lines[i]
    if ln.startswith("#"):
        out.append(f"\n[{i + 1}] {ln}")
        j = i + 1
        para = []
        while j < len(lines):
            t = lines[j]
            if t.startswith("#"):
                break
            if not t.strip():
                if para:
                    break
                j += 1
                continue
            if t.startswith(("![", "*Table", "*Figure", "|", "$$", "<!--", "---")):
                if para:
                    break
                j += 1
                continue
            para.append(t.strip())
            j += 1
        text = " ".join(para)
        out.append("    " + (text[:700] + (" ..." if len(text) > 700 else "")))
    i += 1
dst.write_text("\n".join(out), encoding="utf-8")
print(len([o for o in out if o.startswith("\n[")]), "headings")
