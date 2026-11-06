"""List how build/build_pdf.py will treat every cross-reference of a note, without building it.

Usage: python check_xref_links.py <note.md> [--all]

The build turns "Eq. (12)", "Section 6.2.4", "Table 3", "Figure 4", "Appendix B" and their lists into links
to the note's own targets, unless the text just before the reference marks it as another document's: a
possessive ("the high-gain note's Table 3", "TI's Figure 54"), "its" or "their", a page number ("p. 19,
Figure 50"), or an open citation bracket ("[A22, ..."). A reference to another document that lacks such a
marker is linked to this note's target of the same number if one exists, which is wrong. This script applies
the build's patterns (copied from build/build_pdf.py: TAG, NUM, SEP, REF_RE, EXTERNAL_BEFORE, EXTERNAL_AFTER)
to the Markdown, splitting each paragraph and table cell where pandoc splits the text: at inline math, links
and emphasis. It prints every reference that would be linked, with its target and context, so that each can
be read, and every one left unresolved. With --all it also prints those left as text.
"""
import re
import sys

TAG = r"(?:[A-Z]\.\d+|\d+[a-z]?)"
NUM = r"(?:[A-G](?:(?:\.\d+|\d{1,2})(?:\.\d+)*[a-z]?)?(?!\d)|\d+(?:\.\d+)*[a-z]?)(?![A-Za-z])"
SEP = r"(?:,\s*|\s+and\s+|\s+or\s+|–|\s+to\s+)"
EQN = r"\(" + TAG + r"\)"
REF_RE = re.compile(
    r"(?P<eqs>\bEqs?\.\s*" + EQN + r"(?:\s*(?:,|and|–|-|to|or)\s*" + EQN + r")*)"
    r"|\b(?P<kw>Sections?|Chapters?|Appendix|Appendices|Tables?|Figures?)\s+(?P<list>" + NUM + r"(?:" + SEP + NUM + r")*)")
EXTERNAL_BEFORE = re.compile(r"(?:\w['’]s?|\b(?:[Ii]ts|[Tt]heir|[Hh]is|[Hh]er)|canceller as|\bp\.\s*\d+,?|\[[A-Z]\d+,[^\[\]]*)\s*$")
EXTERNAL_AFTER = re.compile(r"^\s*(?:in SBOA|\[A\d|of the companion|in the companion)")
KIND = {"Section": "section", "Sections": "section", "Chapter": "chapter", "Chapters": "chapter",
        "Appendix": "appendix", "Appendices": "appendix", "Table": "table", "Tables": "table",
        "Figure": "figure", "Figures": "figure"}


def anchors_of(lines):
    """The targets the build would find: headings, table and figure captions, equation tags."""
    a = set()
    for ln in lines:
        m = re.match(r"^## (\d+)\.\s", ln)
        if m:
            a.add(("chapter", m.group(1)))
            a.add(("section", m.group(1)))      # as the build: "Section 3" may name a top-level part
        m = re.match(r"^#{2,4} Appendix ([A-G])\.", ln)
        if m:
            a.add(("appendix", m.group(1)))
        m = re.match(r"^#{2,4} ([A-G]\d+)\.\s", ln)       # "A6. Tables of Chapter 6", as the build
        if m:
            a.add(("appendix", m.group(1)))
        m = re.match(r"^#{2,4} (\d+\.\d+(?:\.\d+)?|[A-G]\.\d+(?:\.\d+)?)\s", ln)
        if m:
            a.add(("section", m.group(1)))
            if m.group(1)[0].isalpha():
                a.add(("appendix", m.group(1)))
        m = re.match(r"^\*Table ([A-G]?\d*\.?\d+(?:\.\d+)?[a-z]?)\.\s", ln)
        if m:
            a.add(("table", m.group(1)))
        m = re.match(r"^\*Figure (\d+)\.\s", ln)
        if m:
            a.add(("figure", m.group(1)))
        for t in re.findall(r"\\tag\{(" + TAG + r")\}", ln):
            a.add(("eq", t))
    return a


def segments(text):
    """Split a line where pandoc would end a text node: inline math, links (whose text is skipped, as the
    build skips <a>), code and emphasis markers."""
    text = re.sub(r"\$[^$]+\$", "\x00", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", "\x00", text)
    text = re.sub(r"`[^`]*`", "\x00", text)
    text = text.replace("**", "\x00").replace("*", "\x00")
    return text.split("\x00")


def main(path, show_all):
    lines = open(path, encoding="utf-8").read().split("\n")
    anchors = anchors_of(lines)
    in_code = in_math = False
    linked, external, unresolved = [], [], []
    for n, ln in enumerate(lines, 1):
        if ln.strip().startswith("```"):
            in_code = not in_code
            continue
        if ln.strip() == "$$":
            in_math = not in_math
            continue
        if in_code or in_math or ln.startswith("#"):
            continue
        cells = ln.split("|") if ln.lstrip().startswith("|") else [ln]
        own_caption = re.match(r"^\*(Table|Figure) [^ ]+\.\s", ln)
        for cell in cells:
            for seg in segments(cell):
                for m in REF_RE.finditer(seg):
                    if own_caption and seg is not None and m.start() == 0 and cell is cells[0]:
                        continue
                    ctx = seg[max(0, m.start() - 40):m.end() + 10].strip()
                    if EXTERNAL_BEFORE.search(seg[:m.start()]) or EXTERNAL_AFTER.match(seg[m.end():]):
                        external.append((n, m.group(0), ctx))
                        continue
                    if m.group("eqs"):
                        keys = [("eq", t) for t in re.findall(r"\((" + TAG + r")\)", m.group(0))]
                    else:
                        kind = KIND[m.group("kw")]
                        keys = []
                        for k in re.findall(NUM, m.group("list")):
                            if kind == "figure":
                                k = re.sub(r"[a-z]$", "", k)
                            keys.append((kind, k))
                    for key in keys:
                        hit = key in anchors or (key[0] == "table" and ("appendix", key[1]) in anchors)
                        (linked if hit else unresolved).append((n, f"{key[0]} {key[1]}", ctx))
    print(f"{len(linked)} references would be linked to targets of this note:")
    for n, k, c in linked:
        print(f"  line {n}: {k}   ... {c}")
    print(f"{len(unresolved)} references would stay unresolved (left as text, logged by the build):")
    for n, k, c in unresolved:
        print(f"  line {n}: {k}   ... {c}")
    print(f"{len(external)} references are marked as another document's and stay text")
    if show_all:
        for n, k, c in external:
            print(f"  line {n}: {k}   ... {c}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")       # the notes use Ω, µ and en dashes
    main(sys.argv[1], "--all" in sys.argv)
