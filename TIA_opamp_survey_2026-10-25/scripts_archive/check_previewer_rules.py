"""Check the inline mathematics of a Markdown note against the strictest previewer rules.

Usage: python check_previewer_rules.py <note.md> [...]

Markdown previewers (VS Code's markdown-it with texmath, remark-math in Obsidian and elsewhere, GitHub)
parse $...$ only under conditions that the KaTeX checks of check_math_extract.py and katex_check.js do not
test, because those parse each span after it has been found. A span that a previewer does not recognise
shows as raw text. This script finds every inline span with the pattern of check_math_extract.py and
reports
  - a space just inside either dollar sign;
  - a digit right after the closing dollar sign;
  - a letter or digit glued before the opening dollar sign;
  - a '|' inside the mathematics of a table row, which GitHub reads as a cell boundary before the math.
Display blocks ($$ on their own lines) and code blocks are skipped.
"""
import re
import sys

SPAN = re.compile(r"(?<![\\$])\$(?!\$)(.+?)(?<![\\$])\$(?!\$)")


def check(path):
    bad = 0
    in_code = in_math = False
    for n, ln in enumerate(open(path, encoding="utf-8").read().split("\n"), 1):
        if ln.strip().startswith("```"):
            in_code = not in_code
            continue
        if ln.strip() == "$$":
            in_math = not in_math
            continue
        if in_code or in_math:
            continue
        for m in SPAN.finditer(ln):
            s, e, inner = m.start(), m.end(), m.group(1)
            before = ln[s - 1] if s > 0 else " "
            after = ln[e] if e < len(ln) else " "
            problems = []
            if inner[0] == " " or inner[-1] == " ":
                problems.append("space just inside a dollar sign")
            if after.isdigit():
                problems.append("digit after the closing dollar sign")
            if before.isalnum():
                problems.append("letter or digit before the opening dollar sign")
            if ln.lstrip().startswith("|") and "|" in inner:
                problems.append("'|' inside table mathematics")
            for p in problems:
                bad += 1
                print(f"{path}, line {n}: {p}: {ln[max(0, s - 5):e + 5]!r}")
    print(f"{path}: {bad} problems")
    return bad


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(1 if sum(check(p) for p in sys.argv[1:]) else 0)
