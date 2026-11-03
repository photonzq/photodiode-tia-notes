"""Check that the narrative rework kept every line of content of the old report.

Each non-empty line of the old report is normalized (numbers of sections, equations, tables and
figures removed, the words that name them and the self-references of the voice change dropped,
spaces collapsed) and looked up among the normalized lines of the new report.  Lines that are not
found are printed, so that every one can be traced to an intended edit of rework_plan.py (old
headings, the old front matter and chapter introductions, and the hand edits listed in the plan).

Usage: python check_content_kept.py <old report.md> <new report.md>
"""
import re
import sys

WORDS = re.compile(r"\b(Sections?|Chapters?|Appendix|Appendices|Tables?|Figures?|Eqs?\.)\b")
VOICE = re.compile(r"\b(the survey's|The survey's|this survey's|this survey|This survey|the survey|The survey|"
                   r"our analytical model's|Our analytical model's|our analytical model|Our analytical model|"
                   r"analytical model|Analytical model|our analysis|Our analysis|this note's|this note|This note|"
                   r"survey's model|survey model|Survey model|survey central|analytical central|Survey|Analytical|"
                   r"ours|our|Our|We|we)\b")


def norm(line):
    s = WORDS.sub(" ", line)
    s = VOICE.sub(" ", s)
    s = re.sub(r"\b(?:[A-F]\d*\.)?\d+(?:\.\d+)*[a-f]?\b", "#", s)
    s = re.sub(r"[#\s,–()]+", " ", s)
    return s.strip()


def main():
    old = open(sys.argv[1], encoding="utf-8").read().split("\n")
    new = open(sys.argv[2], encoding="utf-8").read().split("\n")
    new_set = {norm(l) for l in new}
    new_text = " ".join(norm(l) for l in new)
    missing = []
    for i, l in enumerate(old, 1):
        if not l.strip() or l.strip() == "---" or l.startswith("#"):
            continue
        n = norm(l)
        if n in new_set or (len(n) > 40 and n in new_text):
            continue
        missing.append((i, l))
    print(f"{len(old)} old lines; {len(missing)} not found verbatim after normalization")
    for i, l in missing:
        print(f"L{i}: {l[:220]}")


if __name__ == "__main__":
    main()
