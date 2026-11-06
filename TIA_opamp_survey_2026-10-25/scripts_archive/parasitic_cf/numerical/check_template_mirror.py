"""Check that Section G.14 of the note still contains numerical_section_template.md with its placeholders filled.

Usage: python check_template_mirror.py [NOTE] [TEMPLATE]

The template holds the text of Section G.14 with placeholders <<name>> where add_numerical_section.py put numbers
from the run records, and later text changes go into the note and the template together. This check walks through
the template and, for each line, looks for the next line of the note's Section G.14 (from its heading to the next
"### G." heading) that matches it: a line without placeholders must be identical, and in a line with placeholders
each placeholder stands for any text. It prints every template line that has no match, then the counts, and the
number of lines of the note's G.14 that the template does not hold (text added to the note alone).
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTE = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parents[2] / "TIA_opamp_survey.md"
TEMPLATE = Path(sys.argv[2]) if len(sys.argv) > 2 else HERE / "numerical_section_template.md"


def matcher(t):
    if "<<" not in t:
        return lambda n: n == t
    pattern = re.compile("^" + "".join(".+?" if p.startswith("<<") else re.escape(p)
                                       for p in re.split(r"(<<[^>]+>>)", t)) + "$")
    return lambda n: pattern.match(n) is not None


def main():
    note = NOTE.read_text(encoding="utf-8").split("\n")
    tmpl = TEMPLATE.read_text(encoding="utf-8").rstrip("\n").split("\n")
    start = note.index(tmpl[0])
    end = next((k for k in range(start + 1, len(note)) if note[k].startswith("### G.")), len(note))
    j, missing, extra = start, [], 0
    for i, t in enumerate(tmpl):
        ok = matcher(t)
        k = next((k for k in range(j, end) if ok(note[k])), None)
        if k is None:
            missing.append((i + 1, t))
            continue
        extra += sum(1 for line in note[j:k] if line.strip())
        j = k + 1
    extra += sum(1 for line in note[j:end] if line.strip())
    for i, t in missing:
        print(f"template line {i} has no match in the note's G.14: {t[:150]}")
    print(f"{len(tmpl)} template lines, {len(tmpl) - len(missing)} found in order in the note's G.14 "
          f"(lines {start + 1}-{end}), {len(missing)} not found; {extra} non-blank lines of the note's G.14 "
          f"are not in the template")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
