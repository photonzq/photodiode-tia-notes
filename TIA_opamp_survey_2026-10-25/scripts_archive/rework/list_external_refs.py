"""List the references of a note that point outside it (to the companion note or to a cited document),
and the caption labels, so that the build can leave the former as text and anchor the latter."""
import re
import sys
from pathlib import Path

md = Path(sys.argv[1]).read_text(encoding="utf-8")
text = re.sub(r"\$\$.*?\$\$", " ", md, flags=re.S)
text = re.sub(r"\$[^$\n]*\$", " ", text)
REF = re.compile(r"\b(Eqs?\.\s*\([^)]*\)|(?:Sections?|Chapters?|Appendix|Appendices|Tables?|Figures?)\s+[A-F]?\.?\d[\w.]*)")
print("== references with 'companion', 'its' or a document name just before them")
for m in REF.finditer(text):
    before = text[max(0, m.start() - 70):m.start()].replace("\n", " ")
    after = text[m.end():m.end() + 25].replace("\n", " ")
    if re.search(r"companion|\bits\b|TI['’]s|Hobbs|\[A\d+\]|\[S\d+\]|datasheet|SBOA|SBOS|note['’]s", before[-45:]) or \
            re.match(r"\s*(of the companion|in the companion|of \[|in \[|\[A|\[S|of SBOA|in SBOA|of its)", after):
        print(f"  ...{before[-45:]}[[{m.group(0)}]]{after}")
print("== equation references")
print(sorted(set(re.findall(r"Eqs?\.\s*\([^)]*\)(?:\s*(?:,|and|–|-|to|or)\s*\([^)]*\))*", text)))[:200])
print("== caption labels")
for m in re.finditer(r"^\*(Table|Figure) ([^ ]+?)\.\s", md, flags=re.M):
    print(" ", m.group(1), m.group(2), end=";")
print()
print("== equation tags", sorted(set(re.findall(r"\\tag\{([^}]*)\}", md))))
