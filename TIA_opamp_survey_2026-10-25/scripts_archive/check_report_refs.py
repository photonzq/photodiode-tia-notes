"""Consistency checks for the assembled report: equation tags and references,
table captions and references, section references, caption amplifier statements."""
import re
import sys

t = open(sys.argv[1], encoding="utf-8").read()
BS = chr(92)

tags = [int(x) for x in re.findall(re.escape(BS + "tag{") + r"(\d+)\}", t)]
print("tags:", len(tags), "in order:", tags == list(range(1, len(tags) + 1)), "max", max(tags) if tags else None)

refs = {int(x) for x in re.findall(r"Eqs?\.\s*\((\d+)\)", t)}
refs |= {int(x) for x in re.findall(r"Eqs\.\s*\(\d+\)[–-]\((\d+)\)", t)}
refs |= {int(x) for x in re.findall(r"Eqs\.\s*\(\d+\)(?:,| and)\s*\((\d+)\)", t)}
print("Eq refs beyond tags:", sorted(r for r in refs if tags and r > max(tags)))
print("tags never referenced:", sorted(set(tags) - refs))

caps = set(re.findall(r"^\*Table ([A-Z]?\d+\.\d+[a-z]?)\.", t, flags=re.M))
caps |= set(re.findall(r"^#### Table (\d+[a-z])\.", t, flags=re.M))
trefs = set(re.findall(r"Tables? ([A-Z]?\d+\.\d+[a-z]?)", t))
trefs |= set(re.findall(r"Tables? [A-Z]?\d+\.\d+[a-z]?(?: and|,| to|–) ?([A-Z]?\d+\.\d+[a-z]?)", t))
print("table captions:", len(caps))
print("table refs without caption:", sorted(r for r in trefs if r not in caps))
dup = sorted(c for c in caps if len(re.findall(r"^\*Table " + re.escape(c) + r"\.", t, flags=re.M)) > 1)
print("duplicate captions:", dup)

heads = set(re.findall(r"^#{2,3} (\d+(?:\.\d+)?)\b", t, flags=re.M))
srefs = set(re.findall(r"Sections? (\d+\.\d+)", t))
srefs |= set(re.findall(r"Sections? \d+\.\d+(?:–|, | and )(\d+\.\d+)", t))
print("section refs without heading:", sorted(s for s in srefs if s not in heads))

bad = []
for m in re.finditer(r"^\*Table ([A-Z]?\d+\.\d+[a-z]?)\.(.*?)\*\s*$", t, flags=re.M):
    cap = m.group(2)
    if not re.search(r"Amplifier|amplifier|Transistors|Front ends", cap):
        bad.append(m.group(1))
print("captions without an amplifier statement:", bad)
print("figure refs:", sorted(set(re.findall(r"Figure (\d+)", t))))
print("[A22] citations:", len(re.findall(r"\[A22", t)), " [A11] citations:", len(re.findall(r"\[A11", t)))
