"""Review the cross-reference decisions of a built print HTML: every internal link whose preceding words suggest
another document, and every reference that was left as text (with its context)."""
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString

html = Path(sys.argv[1]).read_text(encoding="utf-8")
soup = BeautifulSoup(html, "html.parser")
body = soup.body
SUSPECT = re.compile(r"(companion|\bits\b|datasheet|\bp\.\s*\d|\[[A-Z]\d|TI['’]s|Hobbs|SBO|canceller|['’]s?\s*$)")


def before(node, n=60):
    out = []
    for sib in node.previous_elements:
        if isinstance(sib, NavigableString):
            out.append(str(sib))
            if sum(map(len, out)) > n:
                break
    return "".join(reversed(out))[-n:].replace("\n", " ")


print("== links after suspicious words, after 'Fig.', or inside a bibliography entry")
for a in body.find_all("a", class_="xref"):
    b = before(a)
    in_entry = any(re.match(r"\s*\[[A-Z]\d+\]", li.get_text()) for li in a.find_parents("li"))
    if SUSPECT.search(b[-30:]) or re.search(r"Figs?\.?\s*\d", b[-40:]) or in_entry:
        print(f"  {'[entry] ' if in_entry else ''}...{b[-45:]}[[{a.get_text()}]] -> {a['href']}")

print("== references left as text")
TAG = r"(?:[A-Z]\.\d+|\d+[a-z]?)"
REF = re.compile(r"\bEqs?\.\s*\(" + TAG + r"\)|\b(?:Sections?|Chapters?|Appendix|Appendices|Tables?|Figures?)\s+[A-F]?\.?\d[\w.]*")
SKIP = {"a", "math", "code", "pre", "h1", "h2", "h3", "h4", "h5", "nav", "script", "style", "annotation", "title"}
for s in body.find_all(string=True):
    if any(p.name in SKIP for p in s.parents if p is not None and p.name):
        continue
    t = str(s)
    for m in REF.finditer(t):
        par = s.parent
        if par.name == "em" and par.parent is not None and par.parent.get("id", "").startswith(("tab-", "fig-")) \
                and m.start() == 0:
            continue
        print(f"  ...{t[max(0, m.start() - 45):m.start()]}[[{m.group(0)}]]{t[m.end():m.end() + 20]}".replace("\n", " "))
