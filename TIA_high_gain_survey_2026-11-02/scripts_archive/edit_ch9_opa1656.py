"""One-off edit of 2 November 2026: add the OPA1656 gain-bandwidth check to Chapter 9
(parts/09_checks.md) and update its counts and the closed-form statistics.  Each
replacement must match exactly once, or nothing is written.

Usage:  python edit_ch9_opa1656.py
"""
import pathlib

PATH = pathlib.Path(__file__).resolve().parent.parent / "parts" / "09_checks.md"

OPA1656_PARAGRAPH = (
    "**The gain–bandwidth of OPA1656.** OPA1656 specifies 20 MHz of bandwidth at unity gain and 53 MHz of "
    "gain–bandwidth at a gain of 100 (p. 6) [D11], and the analytic model first used the 20 MHz. Its SPICE "
    "model (TI SBOMAW6, Rev. C) settles which value applies. An AC analysis with the loop closed at DC only, "
    "through a 1-TH inductor, and the inverting input held at signal ground by 1 F, gives the open-loop gain "
    "directly (`hg_spice_gbw_check.py`). Its DC gain is 155 dB, and its gain–bandwidth, $|A|f$, is 55.6–56.2 MHz "
    "from 10 Hz to 100 kHz and 55.1 MHz at 300 kHz. Above that it falls, to 47.3 MHz at 1 MHz and 30.4 MHz at "
    "3 MHz, where the phase is −111.5° and −119.0° instead of −90°. Unity gain is reached at 21.1 MHz, which is "
    "the data sheet's 20 MHz. At the feedback capacitances designed for 20 MHz, SPICE gave bandwidths within 1% "
    "of a 53-MHz single pole in seven of the ten designs and within 5% in two more, but 2–16% below the 20-MHz "
    "model. The exception was 100 kΩ on the 20-pF photodiode, whose loop crosses over near 3 MHz, where the extra "
    "phase lag acts. Redesigned for a 53-MHz single pole, that design peaked by 2.7 dB in SPICE, and the 1-MΩ "
    "design on 20 pF and the 100-kΩ design on 380 pF were 20–24% wider in SPICE than in the model. The model "
    "therefore uses 53 MHz multiplied by the macromodel's open-loop shape beyond a single pole "
    "(`add_aol_shape.py`). With it, SPICE and the model agree within 2.5% in bandwidth and 0.25 dB in excess "
    "noise in all ten designs (Table 9.1). OPA1656 now reaches about twice the bandwidth it had at 20 MHz, with "
    "the excess noise that Eq. (22) assigns to the wider band; at the old bandwidth it is as quiet as before "
    "(Section 6.1)."
)

REPLACEMENTS = [
    ("OPA320 (SBOM437, Rev. G, file `OPAx320-Q1.LIB`), OPA818",
     "OPA320 (SBOM437, Rev. G, file `OPAx320-Q1.LIB`), OPA1656 (SBOMAW6, Rev. C), OPA818"),
    ("In all, 100 TIA designs, 30 noise-characterization decks",
     "In all, 110 TIA designs, 33 noise-characterization decks, an open-loop deck for OPA1656"),
    ("Ten amplifiers were run at the five gains on the 20-pF and 380-pF silicon photodiodes. Figure 6 compares "
     "the bandwidth and the excess noise of all 100 designs",
     "Eleven amplifiers were run at the five gains on the 20-pF and 380-pF silicon photodiodes. Figure 6 compares "
     "the bandwidth and the excess noise of all 110 designs"),
    ("For the six precision parts, SPICE confirms the model in every design",
     "For the seven precision and low-noise CMOS parts, SPICE confirms the model in every design"),
    ("For the 282 amplifier-limited designs", "For the 267 amplifier-limited designs"),
    ("For the 92 resistor-limited designs", "For the 87 resistor-limited designs"),
    ("within 1 dB in 73% of the amplifier-limited designs, and underestimates it in all of them, by a median of "
     "0.64 dB",
     "within 1 dB in 72% of the amplifier-limited designs, and underestimates it in all of them, by a median of "
     "0.65 dB"),
    ("excluding those that fail the open-loop-gain rule. Left",
     "excluding those that fail the open-loop-gain rule and OPA1656, whose open-loop gain is not a single pole. "
     "Left"),
    ("Four of the checks' findings change or qualify the analysis.",
     "Five of the checks' findings change or qualify the analysis."),
]

text = PATH.read_text(encoding="utf-8").replace("\r\n", "\n")
for old, new in REPLACEMENTS:
    assert text.count(old) == 1, (text.count(old), old[:60])
    text = text.replace(old, new)

# the OPA1656 paragraph goes after Table 9.2, before Section 9.3
anchor = "<!-- table: table_9_2 -->\n"
assert text.count(anchor) == 1
text = text.replace(anchor, anchor + "\n" + OPA1656_PARAGRAPH + "\n")

# a fifth finding in Section 9.8, after the fourth
item4 = "4. **The low-current noise of logarithmic amplifiers**"
i = text.index(item4)
j = text.index("\n", i)
item5 = ("5. **The gain–bandwidth of OPA1656** is its 53 MHz at a gain of 100, not its 20-MHz unity-gain "
         "bandwidth, and above 300 kHz its open-loop gain needs the shape of its SPICE model (Section 9.2). "
         "It now reaches about twice the bandwidth at its smallest stable $C_F$.")
text = text[:j + 1] + item5 + "\n" + text[j + 1:]

with open(PATH, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(text)
print("Chapter 9 updated")
