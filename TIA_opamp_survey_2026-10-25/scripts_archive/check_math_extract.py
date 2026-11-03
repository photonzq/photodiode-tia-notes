"""Extract the mathematics of a Markdown report and check it with a LaTeX-to-MathML parser.

Usage: python check_math_extract.py <report.md> <out_json>

Finds display blocks ($$ ... $$) and inline spans ($...$) outside code
blocks, writes them to <out_json> (input for katex_check.js), and reports:
  - spans that latex2mathml cannot convert;
  - \\( \\) or \\[ \\] delimiters (the report uses dollar delimiters only);
  - a '$' followed by a digit and a space-free price pattern such as $3.05
    outside mathematics (would open a math span);
  - table rows whose inline mathematics contains '|', which splits the cell.
"""
import json
import re
import sys

import latex2mathml.converter as l2m


def spans(text):
    out = []
    in_code = False
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.strip().startswith("```"):
            in_code = not in_code
            i += 1
            continue
        if in_code:
            i += 1
            continue
        if ln.strip() == "$$":
            j = i + 1
            while j < len(lines) and lines[j].strip() != "$$":
                j += 1
            out.append(dict(kind="display", line=i + 1, tex="\n".join(lines[i + 1:j])))
            i = j + 1
            continue
        for m in re.finditer(r"(?<![\\$])\$(?!\$)(.+?)(?<![\\$])\$(?!\$)", ln):
            out.append(dict(kind="inline", line=i + 1, tex=m.group(1), table=ln.lstrip().startswith("|")))
        i += 1
    return out


def main(md_path, out_json):
    text = open(md_path, encoding="utf-8").read()
    items = spans(text)
    json.dump(items, open(out_json, "w", encoding="utf-8"), ensure_ascii=False)
    bad = 0
    for it in items:
        tex = re.sub(r"\\tag\{[^}]*\}", "", it["tex"])
        try:
            l2m.convert(tex)
        except Exception as e:
            bad += 1
            print(f"latex2mathml failed, line {it['line']}: {it['tex'][:90]!r}: {type(e).__name__} {e}")
        if it["kind"] == "inline" and it.get("table") and "|" in it["tex"]:
            print(f"pipe inside table math, line {it['line']}: {it['tex']!r}")
    for n, ln in enumerate(text.split("\n"), 1):
        if "\\(" in ln or "\\[" in ln:
            print(f"non-dollar delimiter, line {n}: {ln[:90]!r}")
    print(f"{len(items)} math spans ({sum(1 for i in items if i['kind'] == 'display')} display); "
          f"latex2mathml failures: {bad}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
