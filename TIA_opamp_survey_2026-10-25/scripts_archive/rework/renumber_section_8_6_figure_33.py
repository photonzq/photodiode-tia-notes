"""Make room for a new Section 8.6 and a new Figure 33: shift Sections 8.6-8.11 to 8.7-8.12 and Figures 33-51 to
34-52 in a Markdown file of the note.

Usage: python renumber_section_8_6_figure_33.py FILE EXPECTED_HASH [--dry-run]

EXPECTED_HASH is the first 12 hex digits of the file's SHA-256; the file is written only if it still has that hash.
The script changes, outside code blocks and outside inline and display math:
  - the headings "### 8.6 ..." to "### 8.11 ..." (and any deeper "8.x.y");
  - figure captions "*Figure N. ..." and image lines "![Figure N](...)" for N = 33-51;
  - every reference that build/build_pdf.py would treat as this note's own: "Section 8.8 (d)", "Sections 8.6 and
    8.7", "Figures 44-51", "Figure 51(d)", found with the build's patterns (TAG, NUM, SEP, REF_RE, EXTERNAL_BEFORE,
    EXTERNAL_AFTER, as in check_xref_links.py).
A reference marked as another document's ("the companion note's Section 8.4", "TI's Figure 40", "p. 19, Figure 50"),
or standing inside quotation marks (a datasheet's own words, such as OPA657's "See Figure 34"), is left as it is. Every change and every reference left alone is printed with its line and context, for review.
Tables, equations and appendix sections keep their numbers.
"""
import hashlib
import re
import sys
from pathlib import Path

TAG = r"(?:[A-Z]\.\d+|\d+[a-z]?)"
NUM = r"(?:[A-G](?:(?:\.\d+|\d{1,2})(?:\.\d+)*[a-z]?)?(?!\d)|\d+(?:\.\d+)*[a-z]?)(?![A-Za-z])"
SEP = r"(?:,\s*|\s+and\s+|\s+or\s+|–|\s+to\s+)"
REF_RE = re.compile(r"\b(?P<kw>Sections?|Figures?)\s+(?P<list>" + NUM + r"(?:" + SEP + NUM + r")*)")
EXTERNAL_BEFORE = re.compile(r"(?:\w['’]s?|\b(?:[Ii]ts|[Tt]heir|[Hh]is|[Hh]er)|canceller as|\bp\.\s*\d+,?|\[[A-Z]\d+,[^\[\]]*)\s*$")
EXTERNAL_AFTER = re.compile(r"^\s*(?:in SBOA|\[A\d|of the companion|in the companion)")


def new_section(tok):
    m = re.fullmatch(r"8\.(\d+)((?:\.\d+)*[a-z]?)", tok)
    if m and 6 <= int(m.group(1)) <= 11:
        return f"8.{int(m.group(1)) + 1}{m.group(2)}"
    return None


def new_figure(tok):
    m = re.fullmatch(r"(\d+)([a-z]?)", tok)
    if m and 33 <= int(m.group(1)) <= 51:
        return f"{int(m.group(1)) + 1}{m.group(2)}"
    return None


def remap_list(text, fn):
    return re.sub(NUM, lambda m: fn(m.group(0)) or m.group(0), text)


def process_text(part, n, log):
    """Renumber the references in a piece of text that holds no math."""
    out, pos = [], 0
    for m in REF_RE.finditer(part):
        fn = new_section if m.group("kw").startswith("Section") else new_figure
        new_list = remap_list(m.group("list"), fn)
        if new_list == m.group("list"):
            continue
        ctx = part[max(0, m.start() - 50):m.end() + 15].replace("\n", " ")
        before = part[:m.start()]
        quoted = before.count('"') % 2 == 1 or before.rfind("“") > before.rfind("”")   # a datasheet's words, quoted
        if EXTERNAL_BEFORE.search(before) or EXTERNAL_AFTER.match(part[m.end():]) or quoted:
            log.append(f"  KEPT (another document's) line {n}: {m.group(0)}   ... {ctx}")
            continue
        out.append(part[pos:m.start("list")])
        out.append(new_list)
        pos = m.end("list")
        log.append(f"  line {n}: {m.group(0)} -> {m.group('kw')} {new_list}   ... {ctx}")
    out.append(part[pos:])
    return "".join(out)


def process_line(line, n, log):
    m = re.match(r"^(#{2,4} )(8\.\d+(?:\.\d+)*)(\s.*)$", line)
    if m and new_section(m.group(2)):
        log.append(f"  line {n}: heading {m.group(2)} -> {new_section(m.group(2))}")
        return m.group(1) + new_section(m.group(2)) + process_line_text(m.group(3), n, log)
    m = re.match(r"^(!\[Figure )(\d+)(\].*)$", line)
    if m:
        if new_figure(m.group(2)):
            log.append(f"  line {n}: image Figure {m.group(2)} -> {new_figure(m.group(2))}")
            return m.group(1) + new_figure(m.group(2)) + m.group(3)
        return line
    m = re.match(r"^(\*Figure )(\d+)(\..*)$", line)
    if m:
        head = m.group(1) + (new_figure(m.group(2)) or m.group(2))
        if new_figure(m.group(2)):
            log.append(f"  line {n}: caption Figure {m.group(2)} -> {new_figure(m.group(2))}")
        return head + process_line_text(m.group(3), n, log)
    return process_line_text(line, n, log)


def process_line_text(text, n, log):
    """Leave inline math alone and renumber the references in the rest."""
    parts = re.split(r"(\$[^$]+\$)", text)
    return "".join(p if p.startswith("$") and p.endswith("$") and len(p) > 1 else process_text(p, n, log) for p in parts)


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
    changed = sum(1 for a, b in zip(lines, out) if a != b)
    print(f"{path.name}: {changed} lines changed")
    print("\n".join(log))
    if not dry:
        new = newline.join(out).encode("utf-8")
        path.write_bytes(new)
        print(f"written; new hash {hashlib.sha256(new).hexdigest()[:12]}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
