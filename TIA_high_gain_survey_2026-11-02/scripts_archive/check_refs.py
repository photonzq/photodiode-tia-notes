"""Check the internal references of TIA_high_gain_survey.md: equation tags in
order and unique, every cited equation, section, table and figure present,
and no control characters.

Usage:  python check_refs.py
"""
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = pathlib.Path(__file__).resolve().parent.parent
TEXT = (ROOT / "TIA_high_gain_survey.md").read_text(encoding="utf-8")
problems = []


def external(start: int) -> bool:
    """A reference to the companion note ("the companion's Eq. (58)", "its
    Section 4.6") is not an internal reference."""
    before = TEXT[max(0, start - 16):start]
    return "companion" in before or before.rstrip().endswith("its")

bad = [i for i, c in enumerate(TEXT) if ord(c) < 32 and c != "\n"]
if bad:
    problems.append(f"control characters at {bad[:5]}")

tags = [int(t) for t in re.findall(r"\\tag\{(\d+)\}", TEXT)]
if tags != list(range(1, len(tags) + 1)):
    problems.append(f"equation tags not 1..N in order: {tags}")
n_eq = len(tags)

for m in re.finditer(r"Eqs?\.\s*\((\d+)\)(?:\s*(?:–|and|,)\s*\((\d+)\))?", TEXT):
    if external(m.start()):
        continue
    for g in m.groups():
        if g and not 1 <= int(g) <= n_eq:
            problems.append(f"equation reference ({g}) out of range near: {TEXT[m.start()-40:m.end()]!r}")

headings = set()
for h in re.findall(r"^#{2,4} (.+)$", TEXT, flags=re.M):
    m = re.match(r"(\d+(?:\.\d+)*)\.?\s", h)
    if m:
        headings.add(m.group(1).rstrip("."))
    m = re.match(r"Appendix ([A-E])\.", h)
    if m:
        headings.add(m.group(1))
    m = re.match(r"([A-E]\.\d+)", h)
    if m:
        headings.add(m.group(1))
for m in re.finditer(r"Sections? (\d+(?:\.\d+)*)(?:\s*(?:–|and)\s*(\d+(?:\.\d+)*))?", TEXT):
    if external(m.start()):
        continue
    for g in m.groups():
        if g and g not in headings:
            problems.append(f"section {g} not found near: {TEXT[m.start()-50:m.end()]!r}")
for m in re.finditer(r"Appendix ([A-E])(\.\d+)?", TEXT):
    key = m.group(1) + (m.group(2) or "")
    if key not in headings and m.group(1) not in headings:
        problems.append(f"appendix {key} not found")

captions = set(re.findall(r"^\*Table ([A-Z]?\.?[0-9]+(?:\.[0-9]+)?[a-e]?)\.", TEXT, flags=re.M))
for m in re.finditer(r"Tables? ([A-Z]\.\d+[a-e]?|\d+(?:\.\d+)?[ab]?)(?:\s*(?:–|and)\s*([A-Z]\.\d+[a-e]?|\d+(?:\.\d+)?))?", TEXT):
    for g in m.groups():
        if not g:
            continue
        ctx = TEXT[max(0, m.start() - 40):m.start()]
        if "companion" in ctx or "data sheet" in ctx or "its Table" in TEXT[max(0, m.start() - 5):m.end()]:
            continue
        if g not in captions and not (g + "a" in captions):
            problems.append(f"table {g} has no caption near: {TEXT[m.start()-40:m.end()]!r}")

figs = set(re.findall(r"^\*Figure (\d+)\.", TEXT, flags=re.M))
for m in re.finditer(r"Figures? (\d+)(?:\s*(?:–|and)\s*(\d+))?", TEXT):
    for g in m.groups():
        if g and g not in figs:
            problems.append(f"figure {g} has no caption")
for img in re.findall(r"\]\((figures/[^)]+)\)", TEXT):
    if not (ROOT / img).exists():
        problems.append(f"missing figure file {img}")

print(f"equations: {n_eq}; tables: {len(captions)}; figures: {len(figs)}; headings: {len(headings)}")
if problems:
    print(f"{len(problems)} problems:")
    for p in problems:
        print(" -", p)
    sys.exit(1)
print("no problems found")
