"""One-off edit of 2 November 2026: replace Section 3.4 of parts/03_bandwidth.md
by an expanded text, keeping two paragraph blocks of the old section unchanged
(Figure 3 with Table 3 and its conclusions, and the estimate of C_ee and C_g).

Usage:  python edit_section_3_4.py NEW_TEXT.md

NEW_TEXT.md holds the new section, from its heading to its last paragraph.  A
line %%KEEP_FULL%% in it is replaced by the old block that starts with
"**What it does, in full.**", and a line %%KEEP_SIZE%% by the old block that
starts with "**How large are $C_{ee}$ and $C_g$?**".  The script refuses to run
if the old section is not the expected version.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PART = ROOT / "parts" / "03_bandwidth.md"
START = "### 3.4 The feedback resistor as a distributed RC line"
END = "### 3.5 Beyond the resistor's corner"
OLD_MARK = "No SPICE simulation of the distributed resistor was run for this note"


def block(text: str, lead: str, next_lead: str) -> str:
    i = text.index(lead)
    j = text.index(next_lead, i)
    return text[i:j].strip("\n")


text = PART.read_text(encoding="utf-8").replace("\r\n", "\n")
i0, i1 = text.index(START), text.index(END)
old = text[i0:i1]
if OLD_MARK not in old:
    sys.exit("Section 3.4 is not the expected version; nothing changed.")

keep_full = block(old, "**What it does, in full.**", "**The line's own noise.**")
keep_full = keep_full.replace("for which the transfer admittance is $y_{11}$ (Eq. (28)).",
                              "for which the transfer admittance is $y_{11}$ (Eq. (28) with $\\alpha = 1$).")
keep_size = block(old, "**How large are $C_{ee}$ and $C_g$?**", "**How the model is used in this note.**")

new = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8").replace("\r\n", "\n").strip("\n")
assert new.count("%%KEEP_FULL%%") == 1 and new.count("%%KEEP_SIZE%%") == 1
new = new.replace("%%KEEP_FULL%%", keep_full).replace("%%KEEP_SIZE%%", keep_size)

with open(PART, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(text[:i0] + new + "\n\n" + text[i1:])
print(f"Section 3.4: {len(old)} -> {len(new)} characters")
