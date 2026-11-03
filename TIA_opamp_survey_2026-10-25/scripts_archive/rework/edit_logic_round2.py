"""Logic round of 1 Nov 2026: rewrites the opening and the chapter openings of the note as an
argument, rebuilds the conclusions chapter (thirteen overlapping sections merged into seven, every
number kept), applies the reviewed fixes inside the chapters, and renumbers the references to the
conclusions.  The new text is in logic_round2_text.py, the reviewed fixes in logic_round2_fixes.py
(publication and conclusions) and in logic_round2_fixes_ch*.py (one module per group of chapters).

Every edit is an exact replacement of text that must occur exactly once, so the script fails loudly
instead of editing the wrong place.  The operations are
    ("replace", old, new)                 old occurs exactly once
    ("paragraph", opening, new)           the single-line paragraph that starts with `opening`
    ("span", start, end, new)             from `start` (once) to the first `end` after it, inclusive
    ("delete", start, end)                the same span removed, with the blank line after it
    ("move", start, end, anchor, where)   the span cut out and put as its own block before or
                                          after the paragraph containing `anchor` (where = "before"
                                          or "after"; `anchor` must start or end that paragraph)
It reads and writes with LF line endings.

Usage: python edit_logic_round2.py <note before.md> <note after.md>
"""
import importlib
import re
import sys

import logic_round2_text as T
import logic_round2_fixes as F

CHAPTER_MODULES = ["logic_round2_fixes_ch1_4", "logic_round2_fixes_ch5",
                   "logic_round2_fixes_ch6", "logic_round2_fixes_ch7_8"]
MAX_SPAN = 40000


def read(p):
    with open(p, encoding="utf-8", newline="") as fh:
        return fh.read()


def write(p, s):
    with open(p, "w", encoding="utf-8", newline="") as fh:
        fh.write(s)


def find_once(text, s, what=""):
    n = text.count(s)
    assert n == 1, (what or s[:90], n)
    return text.index(s)


def once(text, old, new, what=""):
    find_once(text, old, what)
    return text.replace(old, new)


def paragraph(text, opening, new):
    """Replace the single-line paragraph that starts with `opening`."""
    hits = [m for m in re.finditer(r"^" + re.escape(opening) + r".*$", text, re.M)]
    assert len(hits) == 1, (opening[:60], len(hits))
    m = hits[0]
    return text[:m.start()] + new + text[m.end():]


def locate(text, start, end):
    i = find_once(text, start)
    j = text.find(end, i)
    assert j >= 0, ("end not found after start", start[:60], end[:60])
    j += len(end)
    assert j - i <= MAX_SPAN, ("span too long", start[:60], j - i)
    return i, j


def cut(text, i, j):
    """Remove text[i:j] and the blank line that separated it from what followed."""
    before, after = text[:i], text[j:]
    if before.endswith("\n\n") and after.startswith("\n\n"):
        after = after[2:]
    elif before.endswith("\n") and after.startswith("\n\n"):
        after = after[1:]
    return before + after


def move(text, start, end, anchor, where):
    i, j = locate(text, start, end)
    block = text[i:j]
    text = cut(text, i, j)
    k = find_once(text, anchor)
    if where == "before":
        assert k == 0 or text[k - 1] == "\n", ("anchor does not start a line", anchor[:60])
        return text[:k] + block + "\n\n" + text[k:]
    assert where == "after", where
    k += len(anchor)
    assert text[k:k + 1] == "\n", ("anchor does not end a line", anchor[:60])
    return text[:k] + "\n\n" + block + text[k:]


def apply(text, item):
    kind = item[0]
    if kind == "replace":
        return once(text, item[1], item[2])
    if kind == "paragraph":
        return paragraph(text, item[1], item[2])
    if kind == "span":
        i, j = locate(text, item[1], item[2])
        return text[:i] + item[3] + text[j:]
    if kind == "delete":
        i, j = locate(text, item[1], item[2])
        return cut(text, i, j)
    if kind == "move":
        return move(text, *item[1:5])
    raise ValueError(kind)


def section_bodies(chapter):
    """Old Chapter 9 split at its '### 9.N' headings: {N: body without heading}."""
    parts = re.split(r"^### 9\.(\d+) [^\n]*\n", chapter, flags=re.M)
    return {int(parts[i]): parts[i + 1].strip("\n") for i in range(1, len(parts), 2)}


def rebuild_ch9(text):
    start = text.index("## 9. Conclusions and recommendations")
    end = text.index("\n---\n\n## Appendix A. Tables")
    old = section_bodies(text[start:end])
    assert sorted(old) == list(range(1, 14)), sorted(old)
    flags = old[11]
    assert flags.startswith("1. **Every design below 50° of phase margin.**"), flags[:60]
    floor = once(old[12], "The table gives, at 100 MHz,", "Table A9.4 gives, at 100 MHz,")
    checks = old[13]
    for a, b in F.CH9_CHECK_NOTES:
        checks = once(checks, a, b)
    table = old[7][old[7].index("*Table 9.1."):]
    new = "\n\n".join([
        "## 9. Conclusions and recommendations", T.CH9_OPEN, T.CH9_1,
        T.CH9_2_HEAD, table, T.CH9_2_BODY, T.CH9_3, T.CH9_4,
        T.CH9_5_HEAD + "\n\n" + flags,
        T.CH9_6_HEAD + "\n\n" + floor,
        T.CH9_7_HEAD + "\n\n" + checks])
    return text[:start] + new + "\n" + text[end:]


def main():
    text = read(sys.argv[1])
    # the opening of the note, up to the rule before Chapter 1
    head_end = text.index("\n---\n\n## 1. What we are designing")
    text = T.FRONT.strip("\n") + "\n" + text[head_end:]
    # chapter openings
    text = paragraph(text, "The receiver needs a front end that turns the RF difference current", T.CH1_OPEN)
    text = paragraph(text, "Three kinds of front end can turn the difference current of the pair", T.CH2_OPEN)
    text = paragraph(text, "This chapter derives, from the circuit of Figure 1, every equation", T.CH4_OPEN)
    text = paragraph(text, "With the model of Chapter 4 checked against the macromodels in Chapter 5", T.CH6_OPEN)
    text = paragraph(text, "With the amplifier chosen, two parts of the front end remain", T.CH8_OPEN)
    # the conclusions, and the references into them from other chapters
    text = rebuild_ch9(text)
    for a, b in F.CH9_REFERENCES:
        text = once(text, a, b)
    # reviewed fixes: publication first, then chapter by chapter
    groups = [("logic_round2_fixes", F.FIXES)]
    for name in CHAPTER_MODULES:
        try:
            groups.append((name, importlib.import_module(name).FIXES))
        except ModuleNotFoundError:
            print(f"(no {name}.py)")
    total = 0
    for name, fixes in groups:
        for n, item in enumerate(fixes):
            try:
                text = apply(text, item)
            except AssertionError as e:
                raise SystemExit(f"{name}, fix {n} ({item[0]}): {e}")
        total += len(fixes)
        print(f"{name}: {len(fixes)} fixes applied")
    assert "\r" not in text
    write(sys.argv[2], text)
    print(f"written {len(text.splitlines())} lines; {total} reviewed fixes applied")


if __name__ == "__main__":
    main()
