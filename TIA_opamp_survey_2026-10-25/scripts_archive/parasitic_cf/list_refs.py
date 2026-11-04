"""List every cross-reference of the derivation draft with its line, for classification.

Usage: python list_refs.py <derivation.md>
"""
import re
import sys

text = open(sys.argv[1], encoding="utf-8").read().split("\n")
pat = re.compile(r"(Sections?\s+[0-9][0-9.]*(?:\s*(?:to|and|,|–)\s*[0-9][0-9.]*)*"
                 r"|Chapters?\s+\d+|Tables?\s+[A-Z]?[0-9.]+[a-z]?|Figures?\s+[A-Z]?\d+[a-z]?"
                 r"|Eqs?\.\s*\([^)]*\)(?:\s*(?:to|and|,|–)\s*\([^)]*\))*|\[P\d\]|approximations?\s+A\d+"
                 r"|of the note|the note's|the companion|high-gain note|Appendix\s+[A-Z]\S*"
                 r"|confirmations?\s+C\d+|\(C\d+\))")
for i, s in enumerate(text, 1):
    for m in pat.finditer(s):
        a, b = max(0, m.start() - 50), min(len(s), m.end() + 30)
        print(f"{i}: [{m.group(0)}]  ...{s[a:b]}...")
