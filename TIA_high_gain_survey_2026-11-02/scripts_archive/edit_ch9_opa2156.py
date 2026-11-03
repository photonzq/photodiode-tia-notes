"""One-off edit of 2 November 2026: add the OPA2156 gain-bandwidth check to Chapter 9
(parts/09_checks.md) and update its counts and closed-form statistics.  Each replacement
must match exactly once, or nothing is written.

Usage:  python edit_ch9_opa2156.py
"""
import pathlib

PATH = pathlib.Path(__file__).resolve().parent.parent / "parts" / "09_checks.md"

OPA2156_TEXT = (
    "OPA2156 shows the same pattern more mildly. Its data sheet gives 20 MHz at unity gain and 25 MHz at a gain "
    "of 100 (p. 6) [D12]. Its SPICE model (TI SBOMAR0, Rev. B) has a DC gain of 154.5 dB and a gain–bandwidth of "
    "24.8–24.9 MHz from 10 Hz to 100 kHz, and 23.2 MHz at 1 MHz, with a phase of −98.3° there and −100.7° at "
    "3 MHz. It reaches unity gain at 18.7 MHz. At the feedback capacitances designed for 20 MHz, a 25-MHz single "
    "pole matched SPICE within 1.3% from 10 MΩ up, where the 20-MHz model was off by up to 4.4%. With 25 MHz and "
    "its open-loop shape, SPICE and the model agree within 0.7% in bandwidth in all ten designs (Table 9.1). "
)

REPLACEMENTS = [
    ("OPA1656 (SBOMAW6, Rev. C), OPA818", "OPA1656 (SBOMAW6, Rev. C), OPA2156 (SBOMAR0, Rev. B), OPA818"),
    ("In all, 110 TIA designs, 33 noise-characterization decks, an open-loop deck for OPA1656",
     "In all, 120 TIA designs, 36 noise-characterization decks, open-loop decks for OPA1656 and OPA2156"),
    ("Eleven amplifiers were run", "Twelve amplifiers were run"),
    ("the excess noise of all 110 designs", "the excess noise of all 120 designs"),
    ("For the seven precision and low-noise CMOS parts, SPICE confirms the model in every design: the bandwidth "
     "within 7.1% and the excess noise within 0.67 dB, with medians of 0.1–1.2% and 0.02–0.30 dB.",
     "For the eight precision and low-noise CMOS parts, SPICE confirms the model's bandwidth in every design, within "
     "7.1%, with medians of 0.1–1.2%. Their excess noise agrees within 0.67 dB, with medians of 0.02–0.33 dB, except "
     "for OPA2156 on the 380-pF photodiode at 100 MΩ and 1 GΩ. There SPICE gives 1.0 dB more, because OPA2156's "
     "macromodel has 6.5 nV/√Hz at 1 kHz against the data sheet's 4.0 nV/√Hz (Table 9.3)."),
    ("**The gain–bandwidth of OPA1656.** OPA1656 specifies", "**The gain–bandwidth of OPA1656 and OPA2156.** OPA1656 specifies"),
    ("OPA1656 now reaches about twice the bandwidth it had at 20 MHz, with the excess noise that Eq. (22) assigns to "
     "the wider band; at the old bandwidth it is as quiet as before (Section 6.1).",
     OPA2156_TEXT + "OPA1656 and OPA2156 now reach about 1.9 and 1.2 times the bandwidths they had at 20 MHz, with the "
     "excess noise that Eq. (22) assigns to the wider bands; at the old bandwidths they are as quiet as before "
     "(Section 6.1)."),
    ("The precision parts' models reproduce their datasheets: voltage noise within 8% and current noise within 16%.",
     "The precision parts' models reproduce their datasheets, voltage noise within 8% and current noise within 16%, "
     "with one exception: OPA2156's model has 6.5 nV/√Hz at 1 kHz, against 4.0 nV/√Hz in its data sheet."),
    ("For the 267 amplifier-limited designs", "For the 252 amplifier-limited designs"),
    ("For the 87 resistor-limited designs", "For the 82 resistor-limited designs"),
    ("within 1 dB in 73% of the amplifier-limited designs", "within 1 dB in 72% of the amplifier-limited designs"),
    ("excluding those that fail the open-loop-gain rule and OPA1656, whose open-loop gain is not a single pole.",
     "excluding those that fail the open-loop-gain rule, and OPA1656 and OPA2156, whose open-loop gains are not "
     "single poles."),
    ("5. **The gain–bandwidth of OPA1656** is its 53 MHz at a gain of 100, not its 20-MHz unity-gain bandwidth, and "
     "above 300 kHz its open-loop gain needs the shape of its SPICE model (Section 9.2). It now reaches about twice "
     "the bandwidth at its smallest stable $C_F$.",
     "5. **The gain–bandwidths of OPA1656 and OPA2156** are their values at a gain of 100, 53 and 25 MHz, not their "
     "20-MHz unity-gain bandwidths, and above about 300 kHz their open-loop gains need the shapes of their SPICE "
     "models (Section 9.2). At their smallest stable $C_F$ they now reach about 1.9 and 1.2 times the bandwidths "
     "that the note first gave them."),
]

text = PATH.read_text(encoding="utf-8").replace("\r\n", "\n")
for old, new in REPLACEMENTS:
    assert text.count(old) == 1, (text.count(old), old[:70])
    text = text.replace(old, new)
with open(PATH, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(text)
print("Chapter 9 updated for OPA2156")
