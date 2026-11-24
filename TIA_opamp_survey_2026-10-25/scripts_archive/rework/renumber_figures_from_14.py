"""Make room for the new Figure 14 of Section 4.11.9 (the pulse model against the macromodel in SPICE): shift
Figures 14-57 to 15-58 in a Markdown file of the note.

Usage: python renumber_figures_from_14.py FILE EXPECTED_HASH [--dry-run]

EXPECTED_HASH is the first 12 hex digits of the file's SHA-256; the file is written only if it still has that hash.
Outside code blocks and outside inline and display math the script changes the figure captions "*Figure N. ...",
the image lines "![Figure N](...)" and every reference that build/build_pdf.py treats as the note's own
("Figure 47b", "Figures 45-52"), found with the build's patterns as in renumber_figures_from_11.py, of which this is
a copy with another range.  A reference marked as another document's (a possessive, "its", "p. N,", an open
citation bracket) or standing inside quotation marks is left as it is.  Every change and every reference left alone
is printed for review.  Section, table and equation numbers do not change.  Run it before the new Figure 14 is
written into the note, so that its own number is not shifted.
"""
import hashlib
import re
import sys
from pathlib import Path

NUM = r"(?:[A-G](?:(?:\.\d+|\d{1,2})(?:\.\d+)*[a-z]?)?(?!\d)|\d+(?:\.\d+)*[a-z]?)(?![A-Za-z])"
SEP = r"(?:,\s*|\s+and\s+|\s+or\s+|–|\s+to\s+)"
REF_RE = re.compile(r"\b(?P<kw>Figures?)\s+(?P<list>" + NUM + r"(?:" + SEP + NUM + r")*)")
EXTERNAL_BEFORE = re.compile(r"(?:\w['’]s?|\b(?:[Ii]ts|[Tt]heir|[Hh]is|[Hh]er)|canceller as|\bp\.\s*\d+,?|\[[A-Z]\d+,[^\[\]]*)\s*$")
EXTERNAL_AFTER = re.compile(r"^\s*(?:in SBOA|\[A\d|of the companion|in the companion)")
FIRST, LAST, SHIFT = 14, 57, 1


def new_figure(tok):
    m = re.fullmatch(r"(\d+)([a-z]?)", tok)
    if m and FIRST <= int(m.group(1)) <= LAST:
        return f"{int(m.group(1)) + SHIFT}{m.group(2)}"
    return None


def process_text(part, n, log):
    out, pos = [], 0
    for m in REF_RE.finditer(part):
        new_list = re.sub(NUM, lambda t: new_figure(t.group(0)) or t.group(0), m.group("list"))
        if new_list == m.group("list"):
            continue
        ctx = part[max(0, m.start() - 50):m.end() + 15].replace("\n", " ")
        before = part[:m.start()]
        quoted = before.count('"') % 2 == 1 or before.rfind("“") > before.rfind("”")
        if EXTERNAL_BEFORE.search(before) or EXTERNAL_AFTER.match(part[m.end():]) or quoted:
            log.append(f"  KEPT (another document's) line {n}: {m.group(0)}   ... {ctx}")
            continue
        out.append(part[pos:m.start("list")])
        out.append(new_list)
        pos = m.end("list")
        log.append(f"  line {n}: {m.group(0)} -> {m.group('kw')} {new_list}   ... {ctx}")
    out.append(part[pos:])
    return "".join(out)


def process_line_text(text, n, log):
    parts = re.split(r"(\$[^$]+\$)", text)
    return "".join(p if p.startswith("$") and p.endswith("$") and len(p) > 1 else process_text(p, n, log) for p in parts)


def process_line(line, n, log):
    m = re.match(r"^(!\[Figure )(\d+)(\].*)$", line)
    if m:
        if new_figure(m.group(2)):
            log.append(f"  line {n}: image Figure {m.group(2)} -> {new_figure(m.group(2))}")
            return m.group(1) + new_figure(m.group(2)) + m.group(3)
        return line
    m = re.match(r"^(\*Figure )(\d+)(\..*)$", line)
    if m:
        if new_figure(m.group(2)):
            log.append(f"  line {n}: caption Figure {m.group(2)} -> {new_figure(m.group(2))}")
        return m.group(1) + (new_figure(m.group(2)) or m.group(2)) + process_line_text(m.group(3), n, log)
    return process_line_text(line, n, log)


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    path, expected, dry = Path(sys.argv[1]), sys.argv[2], "--dry-run" in sys.argv
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()[:12]
    if digest != expected:
        sys.exit(f"{path.name} has hash {digest}, not {expected}; nothing written")
    text = raw.decode("utf-8")
    newline = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(newline)
    log, out, in_code, in_math = [], [], False, False
    for n, line in enumerate(lines, 1):
        if line.strip().startswith("```"):
            in_code = not in_code
            out.append(line)
            continue
        if line.strip() == "$$":
            in_math = not in_math
            out.append(line)
            continue
        out.append(line if in_code or in_math else process_line(line, n, log))
    print(f"{path.name}: {sum(1 for a, b in zip(lines, out) if a != b)} lines changed")
    print("\n".join(log))
    if not dry:
        new = newline.join(out).encode("utf-8")
        path.write_bytes(new)
        print(f"written; new hash {hashlib.sha256(new).hexdigest()[:12]}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
