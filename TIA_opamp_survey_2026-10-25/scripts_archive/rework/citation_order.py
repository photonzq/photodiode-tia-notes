"""Where each figure and table of a Markdown note is cited, against where it stands.

For every figure: its line, the line and section of its first citation in running text (captions
and the image line excluded), and whether running text of the figure's own section cites it; a
figure with no citation in its own section is flagged. For every table caption: whether running
text cites it at all, and whether a table that stands in the body is cited in its own section.
Used for the consistency sweep of 3 November 2026 on both TIA notes.

Usage: python citation_order.py <note.md>
"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
lines = Path(sys.argv[1]).read_text(encoding="utf-8").split("\n")
section, heading, current, cur_no = [], [], "", ""
for ln in lines:
    if re.match(r"#{2,4} ", ln):
        current = ln.lstrip("#").strip()
        cur_no = current.split()[0]
    heading.append(current[:58])
    section.append(cur_no)

caption_line = [False] * len(lines)
in_cap = False
for i, ln in enumerate(lines):
    if ln.startswith("*Figure") or ln.startswith("*Table") or ln.startswith("!["):
        in_cap = True
    elif not ln.startswith("- *"):
        in_cap = False
    caption_line[i] = in_cap

TAB = r"[A-Z]\.\d+[a-z]?|[A-Z]?\d+(?:\.\d+)?[a-z]?"


def expand(first, rest, pat):
    names = [first] + re.findall(pat, rest)
    if "–" in rest and len(names) == 2:
        pa, pb = re.match(r"(.*?)(\d+)$", names[0]), re.match(r"(.*?)(\d+)$", names[1])
        if pa and pb and pa.group(1) == pb.group(1):
            return [f"{pa.group(1)}{k}" for k in range(int(pa.group(2)), int(pb.group(2)) + 1)]
    return names


fig_cites, tab_cites = {}, {}
for i, ln in enumerate(lines):
    if caption_line[i]:
        continue
    for m in re.finditer(r"Figures? (\d+)((?:\s*(?:,|and|–|to)\s*\d+)*)", ln):
        for n in expand(m.group(1), m.group(2), r"\d+"):
            fig_cites.setdefault(int(n), []).append(i)
    for m in re.finditer(rf"Tables? ({TAB})((?:\s*(?:,|and|–|to)\s*(?:{TAB}))*)", ln):
        for t in expand(m.group(1), m.group(2), TAB):
            tab_cites.setdefault(t, []).append(i)

print("Figure  line  first  section of first citation / own-section citation")
for i, ln in enumerate(lines):
    m = re.match(r"!\[Figure (\d+)\]", ln)
    if not m:
        continue
    n = int(m.group(1))
    cites = fig_cites.get(n, [])
    first = cites[0] + 1 if cites else None
    local = [c for c in cites if section[c] == section[i]]
    flag = "" if local else "   <- NOT cited in its own section " + section[i]
    print(f"{n:6d} {i + 1:5d} {str(first):>6}  {heading[cites[0]] if cites else '-'}{flag}")

print()
for i, ln in enumerate(lines):
    m = re.match(rf"\*Table ({TAB})\.", ln)
    if not m:
        continue
    t = m.group(1)
    cites = tab_cites.get(t, [])
    if not cites:
        print(f"Table {t} (line {i + 1}): never cited in running text")
    elif not t.startswith("A") and not any(section[c] == section[i] for c in cites):
        print(f"Table {t} (line {i + 1}): not cited in its own section {section[i]}; first in {heading[cites[0]]}")
print("tables checked:", sum(1 for ln in lines if re.match(rf"\*Table ({TAB})\.", ln)))
