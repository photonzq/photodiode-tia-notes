"""Flag section references whose surrounding words share little with the section they cite.

For each "Section N" (or "Sections N and M", "Sections N–M") in running text, the twenty words
before the reference are compared with the cited section's heading and its first 120 words; a
reference whose context shares fewer than two content words with the target is printed for a
reader to check. A heuristic for finding references left behind by reorganizations; most flags
are fine. Used in the consistency sweep of 3 November 2026.

Usage: python section_ref_overlap.py <note.md> [min_shared]
"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
text = Path(sys.argv[1]).read_text(encoding="utf-8")
MIN = int(sys.argv[2]) if len(sys.argv) > 2 else 2
STOP = set("""a an the and or of to in on at by for with from as is are be was were it its this that these
those which what how why when where not no than then there their our we can only also into each per
over under up down out more most less least very all any some one two three four five six seven eight
nine ten section sections chapter table figure eq eqs see below above here same other between both""".split())


def words(s):
    s = re.sub(r"\$[^$]*\$", " ", s)
    return {w for w in re.findall(r"[a-z][a-z\-]{2,}", s.lower()) if w not in STOP}


lines = text.split("\n")
heads = {}
for i, ln in enumerate(lines):
    m = re.match(r"#{2,4} (\d+(?:\.\d+)*|[A-F](?:\.\d+)?)\.? (.*)", ln)
    if m:
        body = " ".join(lines[i + 1:i + 12])
        heads[m.group(1)] = (m.group(2), words(m.group(2) + " " + " ".join(body.split()[:120])))

flags = 0
for i, ln in enumerate(lines):
    if ln.startswith("#") or ln.startswith("|"):
        continue
    for m in re.finditer(r"Sections? (\d+(?:\.\d+)+)((?:(?:, | and |–)\d+(?:\.\d+)+)*)", ln):
        targets = [m.group(1)] + re.findall(r"\d+(?:\.\d+)+", m.group(2))
        ctx = words(" ".join(ln[:m.start()].split()[-20:]))
        best = max((len(ctx & heads[t][1]) for t in targets if t in heads), default=-1)
        if best < MIN:
            flags += 1
            pre = " ".join(ln[:m.start()].split()[-14:])
            print(f"{i + 1}: ...{pre} [{m.group(0)}] -> {', '.join(heads.get(t, ('?',))[0][:50] for t in targets)}")
print(f"\n{flags} references flagged (fewer than {MIN} shared content words)")
