"""Insert Section 11, Section 0.7 and their cross-references into the report (one-off assembly)."""
import sys
from pathlib import Path

report, scratch = Path(sys.argv[1]), Path(sys.argv[2])
with open(report, encoding="utf-8", newline="") as fh:
    t = fh.read()
assert "\r\n" not in t
read = lambda n: (scratch / n).read_text(encoding="utf-8").replace("\r\n", "\n").rstrip("\n") + "\n"

part1, part2, fig15, s07 = read("section11_part1.md"), read("section11_part2.md"), read("fig15_block.md"), read("section0_7_draft.md")
a = "### 11.3 What limits the dynamic range: the OPA818 design taken apart\n"
assert part1.count(a) == 1
part1 = part1.replace(a, fig15 + "\n" + a)
b = "In the dark its 196 nA of noise puts it 4.9–6.1 dB behind."
assert part2.count(b) == 1
part2 = part2.replace(b, "In the dark its 196 nA of noise puts it 4.9 dB behind OPA818 and 6.1 dB behind OPA855.")
section11 = part1 + "\n" + part2
s07 = s07.replace(
    "- **Single-chip TIAs**: TIA_VERDICT (Section 11.4).\n",
    "- **No single-chip lidar TIA comes within 10 dB at 1 mA.** Their linear input ranges are 3–250 µA, against 0.77–1.14 mA for the "
    "op-amp designs; the best, LMH32401 at 2 kΩ, gives 57.2 dB at 1 mA against 67.6–70.7 dB. The only integrated lead is a "
    "coherent-receiver TIA with a differential input for a balanced pair, MACOM's MATA-006801: on its product-page figures it would "
    "match OPA818 at 1 mA and exceed it by 2.1 dB at 10 mA. Its datasheet is available only on request (Section 11.4).\n")
assert "TIA_VERDICT" not in s07

A2_2 = """
*Table A2.2. Single-chip TIA datasheets of Section 11.4, with the copy used; local copies are in `datasheets/integrated_tia/`. Status and 1ku price as listed on ti.com (26 October 2026) and analog.com (27 October 2026). Amplifiers (single-chip TIAs): every part of Table 11.2 and of the text of Section 11.4 (one per row).*

| Part | Maker | Document and revision used | Status, 1ku price |
|---|---|---|---|
| LMH32401 | TI | SBOS965D (October 2019, revised January 2023) | Active, USD 5.26 |
| LMH32404 | TI | SBOSA05C (August 2021, revised November 2022) | Active, USD 10.72 |
| LMH34400 | TI | SBOSA56C (March 2022, revised October 2023) | Active, USD 1.44 |
| OPA857 | TI | SBOS630D (December 2013, revised August 2016) | Active, USD 2.59 |
| MAX40660, MAX40661 | ADI (Maxim) | 19-100541 Rev 4 (January 2021), distributor copy; Rev 6 is current | Production, USD 5.67 and 5.37 |
| MAX40662 | ADI (Maxim) | 19-100714 Rev 1 (September 2020), distributor copy | Recommended for new designs, USD 15.27 |
| MAX40658, MAX40659 | ADI (Maxim) | 19-100082 Rev 2 (June 2018), distributor copy; Rev 4 is current | Production, USD 4.00 and 5.49 |
| LTC6561 | ADI (Linear Technology) | Rev 0 (June 2018), broker copy; Rev C is current | Recommended for new designs, USD 6.27 |
| LTC6560 | ADI (Linear Technology) | product page only; the datasheet (Rev B) was not obtained | Recommended for new designs, USD 2.45 |
| HMC799LP3E | ADI (Hittite) | v01.1009, distributor copy | Last time buy |
| ADA4355 | ADI | Rev A (October 2020), distributor copy | Recommended for new designs, USD 159.90 |
| PHY1095, PHY1090 | Phyworks (Maxim) | 19-5689 and 19-5686 (January 2011), archive copies | Not recommended for new designs |
| MAX3654 | Maxim | 19-3745 Rev 0 (July 2005), archive copy | Last time buy |
| MATA-006801 | MACOM | product page only; datasheet on request | not shown |
"""

ITEM19 = """19. **Single-chip TIAs (Section 11.4).**
    - MATA-006801's figures come from its product page. Its datasheet, available on request, would settle the gain setting at which its 3 mApp of linear input holds, its noise within 150 MHz (16 pA/√Hz is a figure for a 45-GHz amplifier), and its low-frequency and DC behaviour.
    - The linear input ranges of Table 11.2 follow each datasheet's own criterion, about 1–3 % of gain change (1-dB compression for HMC799), and several are read off curves.
    - Centring LMH32401's asymmetric window with a deliberate imbalance (±475 µA) is untested.
    - Three ADI copies are older than the current revisions (MAX40660/61 Rev 4 against Rev 6, MAX40658/59 Rev 2 against Rev 4, LTC6561 Rev 0 against Rev C).
"""

EDITS = [
    ("\n---\n\n## Appendix 1. Open questions and unknowns\n",
     "\n---\n\n" + section11 + "\n---\n\n## Appendix 1. Open questions and unknowns\n"),
    ("(Section 10.10).\n\n---\n\n## 1. The design problem",
     "(Section 10.10).\n\n" + s07 + "\n---\n\n## 1. The design problem"),
    ("None can take 0.1–10 mA of DC at 1.5–2 kΩ (Section 7.7).\n",
     "None can take 0.1–10 mA of DC at 1.5–2 kΩ (Section 7.7). Section 11.4 compares their dynamic range with the op-amp designs, "
     "with the balanced pair's imbalance servoed to zero.\n"),
    ("None specifies operation with milliamperes of DC.\n",
     "None specifies operation with milliamperes of DC. With the balanced pair's imbalance servoed to zero, the DC no longer decides; "
     "their linear input range then does, and it leaves the best of them, LMH32401, 10.5–13.5 dB behind the op-amp designs at 1 mA "
     "(Section 11.4).\n"),
    ("| TPH2861, TPH2865Q | 3PEAK | AA20231203A3, AA20240603A2 | not checked |\n",
     "| TPH2861, TPH2865Q | 3PEAK | AA20231203A3, AA20240603A2 | not checked |\n" + A2_2),
    ("| `datasheets/` | datasheets of every part in Section 3; `market_scan_candidates/` holds the market-scan extras |",
     "| `datasheets/` | datasheets of every part in Section 3; `market_scan_candidates/` holds the market-scan extras, and "
     "`integrated_tia/` the single-chip TIAs of Section 11.4 (Table A2.2) |"),
    ("| `data/results/results.json` | complete analysis output |",
     "| `data/integrated_tias.json` | the single-chip TIA records of Section 11.4 (Table 11.2), with page and figure citations |\n"
     "| `data/results/results.json` | complete analysis output |"),
]
for old, new in EDITS:
    c = t.count(old)
    assert c == 1, (c, old[:80])
    t = t.replace(old, new)

# Appendix 1, item 19 after item 18 (the last item before Appendix 2)
k = t.index("\n## Appendix 2.")
head, tail = t[:k], t[k:]
head = head.rstrip("\n") + "\n" + ITEM19 + "\n"
t = head + tail
assert t.count("\n18. **The OPA846 macromodel**") == 1 and t.count("\n19. **Single-chip TIAs") == 1

with open(report, "w", encoding="utf-8", newline="") as fh:
    fh.write(t)
print("assembled; Section 11 is", len(section11.splitlines()), "lines")
