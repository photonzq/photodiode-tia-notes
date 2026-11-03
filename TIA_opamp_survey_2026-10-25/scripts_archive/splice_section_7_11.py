"""Replace Section 7.11 of the front-end part file with the two-variant version."""
from pathlib import Path

part = Path("report_part7b_frontend.md")
new = Path("section_7_11_two_variants.md").read_text(encoding="utf-8")
s = part.read_text(encoding="utf-8")
a = s.index("### 7.11 The proposed balanced front end")
b = s.index("### 7.12 What not to do")
part.write_text(s[:a] + new + s[b:], encoding="utf-8")
print("replaced", b - a, "characters with", len(new))
