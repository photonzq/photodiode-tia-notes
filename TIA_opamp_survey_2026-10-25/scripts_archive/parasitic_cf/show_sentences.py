"""Print, for every line of a Markdown file that matches a regular expression, the sentences that match.

Usage: python show_sentences.py <file.md> <regex> [first_line last_line]
"""
import re
import sys

pat = re.compile(sys.argv[2])
lines = open(sys.argv[1], encoding="utf-8").read().split("\n")
lo, hi = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (1, len(lines))
for i in range(lo, hi + 1):
    s = lines[i - 1]
    if not pat.search(s):
        continue
    sents = re.split(r"(?<=[.;:])\s+(?=[A-Z*(\[$|])", s)
    for h in (x for x in sents if pat.search(x)):
        print(f"{i}: {h[:600]}")
