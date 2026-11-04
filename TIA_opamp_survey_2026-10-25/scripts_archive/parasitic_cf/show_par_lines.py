"""Print the sentences of chosen lines of a Markdown file that mention the parasitic feedback capacitance.

Usage: python show_par_lines.py <note.md> <line> [<line> ...]   (no line numbers: every matching line)
"""
import re
import sys

PAT = re.compile(r"0\.20[ -]pF|0\.2[ -]pF|0\.1–0\.3|parasitic floor|parasitic-limited|parasitic only|"
                 r"parasitic-only|C_\{F,\\mathrm\{par\}\}|0\.206|0\.2-pF")
lines = open(sys.argv[1], encoding="utf-8").read().split("\n")
nums = [int(x) for x in sys.argv[2:]] or [i + 1 for i, s in enumerate(lines) if PAT.search(s)]
for i in nums:
    s = lines[i - 1]
    sents = re.split(r"(?<=[.;])\s+(?=[A-Z*(\[$])", s)
    hits = [x for x in sents if PAT.search(x)]
    print(f"--- {i} ({len(s)} chars):")
    for h in hits:
        print("   *", h[:900])
