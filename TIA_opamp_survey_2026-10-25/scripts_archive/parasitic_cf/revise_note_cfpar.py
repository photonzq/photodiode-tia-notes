"""Revise the balanced-photodiode note to the estimated parasitic feedback capacitance and add Appendix G.

Usage: python revise_note_cfpar.py <TIA_opamp_survey.md> <appendix_G.md> <expected sha256 prefix>

Table 1.1 takes C_F,par = 0.08 pF (corners 0.05-0.12 pF) from Appendix G. Every design keeps its total C_F:
0.2 pF becomes the minimum total, which the tolerance of the total (a fitted capacitor's +-0.05 pF plus the
parasitic's corners, about +-0.1 pF) sets, and the corners of +-0.1 pF become corners of the total. The text
that called 0.2 pF the parasitic, the external capacitors of Tables 4.1 and A8.13, the external-capacitor column
of Tables A6.9-A6.10 (now the total) and their corner labels follow. Appendix D gains the references of
Appendix G, Appendix E its files, and Appendix G is appended. Every replacement must match the stated number of
times, and the file must have the expected hash before the edit.
"""
import hashlib
import re
import sys

note_path, app_path, sha_prefix = sys.argv[1], sys.argv[2], sys.argv[3]
raw = open(note_path, "rb").read()
sha = hashlib.sha256(raw).hexdigest()
assert sha.startswith(sha_prefix), f"note changed: sha {sha[:12]}"
t = raw.decode("utf-8")
assert "\r" not in t
app = open(app_path, encoding="utf-8").read()


def rep(old, new, count=1):
    global t
    n = t.count(old)
    assert n == count, f"{n} matches instead of {count}: {old[:100]!r}"
    t = t.replace(old, new)


R = [
    # front box
    (r"and a bandwidth $B$ allows at most $R_F = 1/(2\pi BC_{F,\mathrm{par}})$: 5.3 kΩ at 150 MHz for our nominal 0.2 pF of feedback parasitic, and 10.6 kΩ for 0.1 pF.",
     r"and a bandwidth $B$ allows at most $R_F = 1/(2\pi BC_F)$: 10.6 kΩ at 150 MHz for 0.1 pF across the resistor, close to its parasitic alone (Table 1.1), and 5.3 kΩ for 0.2 pF."),
    # Table 1.1
    (r"| $C_{F,\mathrm{par}}$ | parasitic feedback capacitance of $R_F$, its pads and the layout | 0.20 pF nominal, 0.1–0.3 pF corners | specified range 0.1–0.3 pF; Texas Instruments (TI) quotes up to 0.2 pF for the resistor alone [A2] |",
     r"| $C_{F,\mathrm{par}}$ | parasitic feedback capacitance of $R_F$, its pads and the amplifier's pins | 0.08 pF nominal, 0.05–0.12 pF corners | Appendix G: an 0402 or 0201 beside the amplifier's FB pin, with the planes removed under the feedback network; Texas Instruments (TI) quotes up to 0.2 pF for the resistor alone [A2] |"),
    (r"| $C_F$ | total feedback capacitance, $C_{F,\mathrm{ext}}+C_{F,\mathrm{par}}$ | designed per amplifier, never below $C_{F,\mathrm{par}}$ | Section 6.2 |",
     r"| $C_F$ | total feedback capacitance, $C_{F,\mathrm{ext}}+C_{F,\mathrm{par}}$ | designed per amplifier, at least 0.2 pF; corners ±0.1 pF | Section 6.2; the minimum and the corners come from the tolerance of the total, a fitted capacitor's ±0.05 pF plus the corners of $C_{F,\mathrm{par}}$ (Section G.14) |"),
    # design labels and the grid
    ("If that is below 0.2 pF, the realised design uses $C_F$ = 0.2 pF, the parasitic floor.",
     "If that is below 0.2 pF, the realised design uses $C_F$ = 0.2 pF, the minimum total of Table 1.1: below it the ±0.1 pF tolerance of the total costs most of the phase margin (Section 6.2.8)."),
    ("whose first point above the 0.2-pF floor is 0.206 pF, so it can come out slightly narrower than a flat design on the floor:",
     "whose first point above the 0.2-pF minimum is 0.206 pF, so it can come out slightly narrower than a flat design at the minimum:"),
    ("the robust design was read on the grid, whose first point above the 0.2-pF floor is 0.206 pF.",
     "the robust design was read on the grid, whose first point above the 0.2-pF minimum total is 0.206 pF."),
    # Chapter 4
    ("its loop has phase to spare, the parasitic capacitance of the feedback resistor sets the design, and the question is how far that parasitic and the photodiode may move.",
     "its loop has phase to spare, the feedback capacitance sets the design, and the question is how far that capacitance and the photodiode may move."),
    ("| $C_F$ | 0.20 pF: the flat design needs 0.19 pF, below the parasitic floor of Table 1.1, so no discrete capacitor is fitted | 0.75 pF: the flat design needs 0.745 pF; 0.55 pF fitted beside the 0.20-pF parasitic | Table A6.5 |",
     "| $C_F$ | 0.20 pF: the flat design needs 0.19 pF, below the 0.2-pF minimum total of Table 1.1; 0.12 pF fitted beside the 0.08-pF parasitic | 0.75 pF: the flat design needs 0.745 pF; 0.67 pF fitted beside the 0.08-pF parasitic | Table A6.5; Appendix G |"),
    ("No feedback capacitor is fitted: the design needs 0.19 pF, less than the 0.20 pF that the 2-kΩ resistor and its pads bring ($C_{F,\\mathrm{par}}$).",
     "$C_F$ = 0.20 pF is a 0.12-pF capacitor $C_{F,\\mathrm{ext}}$ fitted beside the 0.08 pF that the resistor, its pads and the amplifier's pins bring ($C_{F,\\mathrm{par}}$, Appendix G): the flat design needs 0.19 pF, and every design keeps at least 0.2 pF in total (Table 1.1)."),
    ("so a 0.55-pF capacitor $C_{F,\\mathrm{ext}}$ is fitted beside the 0.20 pF of the resistor and its pads, 0.75 pF in total.",
     "so a 0.67-pF capacitor $C_{F,\\mathrm{ext}}$ is fitted beside the 0.08 pF of the resistor, its pads and the amplifier's pins, 0.75 pF in total."),
    ("the feedback capacitance is set largely by the parasitics of the resistor and its pads.",
     "the feedback capacitance carries the tolerances of the fitted capacitor and of the parasitics of the resistor, its pads and the amplifier's pins."),
    ("give the widest-band $C_F$ that meets the three criteria, never below the 0.20-pF parasitic floor.",
     "give the widest-band $C_F$ that meets the three criteria, never below the 0.20-pF minimum total of Table 1.1."),
    ("At $C_D$ = 0 no $C_F$ at or above the floor gives 3 dB of gain margin (2.0 dB at 0.20 pF), so a photodiode smaller than 0.15 pF needs capacitance added at the node or a resistor with less parasitic capacitance.",
     "At $C_D$ = 0 no $C_F$ at or above that minimum gives 3 dB of gain margin (2.0 dB at 0.20 pF), so a photodiode smaller than 0.15 pF needs capacitance added at the node, or a total $C_F$ below the minimum, with the tolerance risk of Section 6.2.8."),
    ("Its stability rests on a feedback capacitance that the parasitics of the resistor and its pads largely set.",
     "Its stability rests on a feedback capacitance of 0.20 pF, made of a fitted capacitor and the parasitics of the resistor, its pads and the pins, each with its tolerance."),
    # Chapter 5
    ("AD8099 has none, so its 0.2-pF parasitic $C_F$ alone is used.",
     "AD8099 has none, so it is simulated at the 0.2-pF minimum total."),
    ("The ±0.1 pF that Table A8.13 allows for the resistor and pads does not fit. The parasitic must be measured on the first board and trimmed with pad copper, as the notes to Table A8.13 describe.",
     "The ±0.1 pF that Table A8.13 allows for the fitted capacitor and the parasitic does not fit. The total must be measured on the first board and trimmed with pad copper, as the notes to Table A8.13 describe."),
    # Chapter 6
    ('"Required / realised" $C_F$ is the total feedback capacitance the flat design calls for, and what a board with 0.2 pF of parasitic actually has.',
     '"Required / realised" $C_F$ is the total feedback capacitance the flat design calls for, and the total realised, at least the 0.2-pF minimum of Table 1.1.'),
    ("on the datasheet curve ±0.1 pF of parasitic variation stays inside it",
     "on the datasheet curve ±0.1 pF of variation in the total stays inside it"),
    ("A board is built with one external feedback capacitor, chosen before its parasitic capacitances are known, and the parasitics then land somewhere in their tolerance. To see what that does, we froze the flat design's external $C_F$ and set $C_{\\mathrm{PCB}}$ to 0.2 or 0.5 pF and $C_{F,\\mathrm{par}}$ to 0.1 or 0.3 pF, the corners of the ranges in Table 1.1.",
     "A board is built with one external feedback capacitor, chosen before its parasitic capacitances are known, and the capacitor and the parasitics then land somewhere in their tolerances. To see what that does, we froze the flat design's total $C_F$, moved it by −0.1 or +0.1 pF, the corners of Table 1.1, and set $C_{\\mathrm{PCB}}$ to 0.2 or 0.5 pF."),
    ("- **$C_{F,\\mathrm{par}}$ matters, $C_{\\mathrm{PCB}}$ hardly at all.** The board capacitance at the input moves every design by only 1–5 %. The parasitic feedback capacitance is the sensitive quantity.",
     "- **The feedback capacitance matters, $C_{\\mathrm{PCB}}$ hardly at all.** The board capacitance at the input moves every design by only 1–5 %. The total feedback capacitance is the sensitive quantity."),
    ("Their flat designs rely on the parasitic alone. If an 0201 resistor with small pads gives only 0.1 pF, OPA855 and OPA858 fall to 35–38° with 3.0–3.8 dB of peaking and OPA955 to 17–18° with 8.0–8.7 dB; with 0.3 pF OPA855 and OPA858 give a well-damped 320 MHz at 2 kΩ. These parts are therefore safest with a deliberate total of about 0.25 pF (Section 8.10).",
     "Their flat designs sit at the 0.2-pF minimum. If the total comes out at 0.1 pF, OPA855 and OPA858 fall to 35–38° with 3.0–3.8 dB of peaking and OPA955 to 17–18° with 8.0–8.7 dB; at 0.3 pF OPA855 and OPA858 give a well-damped 320 MHz at 2 kΩ. These parts are therefore safest with a total of about 0.25 pF (Section 8.10)."),
    ("Their flat designs sit at 28–34°, and 0.1 pF of parasitic takes OPA818 to 24–27° with 2.4–2.8 dB of peaking and OPA846 to 27–33°.",
     "Their flat designs sit at 28–34°, and a total 0.1 pF lower takes OPA818 to 24–27° with 2.4–2.8 dB of peaking and OPA846 to 27–33°."),
    ("- the total $C_F$ moved by ±0.1 pF (resistor and pad parasitic);",
     "- the total $C_F$ moved by ±0.1 pF (the fitted capacitor and the parasitic, Table 1.1);"),
    ("At that size the ±0.1 pF parasitic is at most a quarter of $C_F$.",
     "At that size the ±0.1 pF tolerance is at most a quarter of $C_F$."),
    ("**Designs with $C_F$ ≤ 0.2 pF are governed by the parasitic, not by the nominal margin.**",
     "**Designs with $C_F$ ≤ 0.2 pF are governed by the tolerance of the total, not by the nominal margin.**"),
    ("Such designs need the parasitic controlled to better than ±0.1 pF, or a larger $C_F$:",
     "Such designs need the total controlled to better than ±0.1 pF, or a larger $C_F$:"),
    ("**The resistor's own capacitance now sets the bandwidth.** Its pole, $1/(2\\pi R_FC_{F,\\mathrm{par}})$, lies at 398 MHz for 2 kΩ with our nominal 0.2 pF, but at 159 MHz for 5 kΩ and 80 MHz for 10 kΩ. A band of 150 MHz therefore needs $R_F \\le 1/(2\\pi\\times150\\ \\mathrm{MHz}\\times0.2\\ \\mathrm{pF})$ = 5.3 kΩ, or 10.6 kΩ if the layout holds the parasitic to 0.1 pF. Table A6.38 runs the analysis of this chapter at 2, 3, 5 and 10 kΩ with 0.2 pF, and Table A6.39 with 0.1 pF.",
     "**The feedback capacitance now sets the bandwidth.** Its pole, $1/(2\\pi R_FC_F)$, lies at 398 MHz for 2 kΩ with 0.2 pF, but at 159 MHz for 5 kΩ and 80 MHz for 10 kΩ. A band of 150 MHz therefore needs $R_F \\le 1/(2\\pi\\times150\\ \\mathrm{MHz}\\times0.2\\ \\mathrm{pF})$ = 5.3 kΩ, or 10.6 kΩ with 0.1 pF. Table A6.38 runs the analysis of this chapter at 2, 3, 5 and 10 kΩ with 0.2 pF across the resistor, the minimum total of the 2-kΩ designs, which at these resistances means a fitted capacitor of about 0.12 pF; Table A6.39 runs it with 0.1 pF, close to the parasitic alone (0.08 pF, Table 1.1)."),
    ("with the 0.2-pF parasitic as its only feedback capacitance.", "with 0.2 pF as its whole feedback capacitance."),
    ("10 kΩ serves 150 MHz only if the parasitic is held to about 0.1 pF.",
     "10 kΩ serves 150 MHz only with about 0.1 pF across the resistor, the parasitic alone of a careful layout (Table 1.1)."),
    # Chapter 7
    ("split into two 1-kΩ resistors in series because the total $C_F$ of 0.100 pF lies below the parasitic capacitance of a single resistor (Section 8.10).",
     "split into two 1-kΩ resistors in series, as TI advises for a total $C_F$ below 0.15 pF (Section 8.10): 0.100 pF is too small to be set with a fitted capacitor beside a single resistor's parasitic."),
    ("A total $C_F$ of 0.100–0.125 pF lies below the 0.2-pF nominal parasitic of one resistor and its pads (Table 1.1), and its −0.1-pF corner reaches 0.000–0.025 pF. It needs $R_F$ split into two series resistors of $R_F/2$, which TI advises for a $C_F$ below 0.15 pF (Section 8.10), and a parasitic measured on the board; the robust window assumes both.",
     "A total $C_F$ of 0.100–0.125 pF lies below the 0.2-pF minimum of Table 1.1 and within the corners of one resistor's parasitic, 0.05–0.12 pF, and its −0.1-pF corner reaches 0.000–0.025 pF, below what any resistor and pads give. It needs $R_F$ split into two series resistors of $R_F/2$, which TI advises for a $C_F$ below 0.15 pF (Section 8.10), and a total measured and trimmed on the board; the robust window assumes both."),
    # Chapter 8
    ("against a resistor parasitic of 0.2 ± 0.1 pF.", "against the 0.2-pF minimum total and its ±0.1 pF tolerance (Table 1.1)."),
    ("which no longer contains the ±0.1 pF spread around the 0.2-pF parasitic:", "which no longer contains the ±0.1 pF spread around the 0.2-pF minimum total:"),
    ("Its body and pads give the 0.1–0.3 pF of parasitic capacitance assumed throughout. TI quotes up to 0.2 pF for the resistor alone [A2].",
     "Its body, its pads and the amplifier's pins give about 0.08 pF of parasitic capacitance, 0.05–0.12 pF at the corners (Table 1.1, Appendix G), and more for a precision part with deep trim cuts (Section G.13.2). TI quotes up to 0.2 pF for the resistor alone [A2]."),
    ("The external capacitor is the target total minus the 0.2-pF nominal parasitic. Discrete RF capacitors are available down to 0.1 pF in 0.1-pF steps, typically with ±0.05 pF tolerance.",
     "The external capacitor is the target total minus the 0.08-pF nominal parasitic. Discrete RF capacitors are available down to 0.1 pF in 0.1-pF steps, typically with ±0.05 pF tolerance; that tolerance and the corners of the parasitic make the ±0.1 pF of the total assumed throughout (Table 1.1)."),
    ("The OPA855 rows of Table A8.13 are these datasheet-curve designs. No discrete capacitor is needed if the resistor and pads give 0.2–0.25 pF.",
     "The OPA855 rows of Table A8.13 are these datasheet-curve designs. With the 0.08 pF of Table 1.1 they need 0.17 pF fitted at 2 kΩ and 0.19 pF at 1.5 kΩ, and the macromodel's targets 0.15 and 0.16 pF."),
    ("- **Adjusting on the board.** Measure the peaking of the first board and trim with pad copper. A 0.1-pF capacitor is the right part only if the parasitic proves to be about 0.15 pF or less.",
     "- **Adjusting on the board.** These values lie between the 0.1-pF steps of the discrete parts: fit the step below and add pad copper, then measure the peaking of the first board and trim."),
    ("On the datasheet curves both tolerate the parasitic corners with ≥ 46° of phase margin;",
     "On the datasheet curves both tolerate the ±0.1-pF corners of the total with ≥ 46° of phase margin;"),
    # Chapter 9
    ("and ±0.1 pF of resistor parasitic moves it only between 175 and 235 MHz.", "and ±0.1 pF on the total moves it only between 175 and 235 MHz."),
    ("The resistor's own capacitance then sets the band: 150 MHz needs $R_F \\le$ 5.3 kΩ with 0.2 pF of parasitic, or 10.6 kΩ with 0.1 pF.",
     "The feedback capacitance then sets the band: 150 MHz needs $R_F \\le$ 5.3 kΩ with 0.2 pF across the resistor, or 10.6 kΩ with 0.1 pF, close to its parasitic alone (Table 1.1)."),
    ("2. **OPA855 and OPA858 with no external $C_F$.** The design rests on a parasitic that, at 0.1 pF, gives 36–38° and 3–3.6 dB of peaking (Table A6.9). Aim for 0.25 pF total and verify.",
     "2. **OPA855 and OPA858 at the 0.2-pF minimum.** The design rests on a total of 0.2 pF; if it comes out at 0.1 pF, it gives 36–38° and 3–3.6 dB of peaking (Table A6.9). Aim for 0.25 pF total and verify."),
    ("3. **Any external $C_F$ below 0.1 pF.** It is not a reproducible discrete part (Table A8.13, OPA855 rows). Use pad geometry, or two series resistors, as the datasheets advise.",
     "3. **Any external $C_F$ below 0.1 pF**, which a total below about 0.18 pF needs beside the 0.08-pF parasitic. It is not a reproducible discrete part. Use pad geometry, or two series resistors, as the datasheets advise."),
    ("5. **The actual parasitic feedback capacitance of the chosen resistor and pads.** Measure it",
     "5. **The actual parasitic feedback capacitance of the chosen resistor, pads and pins.** Appendix G estimates 0.05–0.12 pF for the layout of this note. Measure it"),
    # appendix tables
    ("never below the 0.20-pF parasitic floor.", "never below the 0.20-pF minimum total of Table 1.1."),
    ("$C_{\\mathrm{PCB}}$ = 0.35 pF, $C_{F,\\mathrm{par}}$ = 0.2 pF. Amplifiers: all 25 analysed parts, 26 configurations (one per row; LMH6629 in COMP HI and COMP LO).*",
     "$C_{\\mathrm{PCB}}$ = 0.35 pF, total $C_F$ at least 0.2 pF. Amplifiers: all 25 analysed parts, 26 configurations (one per row; LMH6629 in COMP HI and COMP LO).*"),
    ("*Table A6.9. Parasitic corners, $R_F$ = 2 kΩ, flat design ($f_{-3\\,\\mathrm{dB}}$, phase margin, peaking).",
     "*Table A6.9. Corners of the board's capacitances, $R_F$ = 2 kΩ, flat design ($f_{-3\\,\\mathrm{dB}}$, phase margin, peaking): the realised total $C_F$ moved by −0.1 or +0.1 pF, and $C_{\\mathrm{PCB}}$ of 0.2 or 0.5 pF."),
    ("| Part | External $C_F$ (pF) | $C_{\\mathrm{PCB}}$ / $C_{F,\\mathrm{par}}$ = 0.2 / 0.1 pF | 0.2 / 0.3 | 0.5 / 0.1 | 0.5 / 0.3 |",
     "| Part | Total $C_F$ (pF) | $C_{\\mathrm{PCB}}$ = 0.2 pF, total −0.1 pF | 0.2 pF, +0.1 pF | 0.5 pF, −0.1 pF | 0.5 pF, +0.1 pF |"),
    ("*Table A6.10. Parasitic corners, $R_F$ = 1.5 kΩ, flat design.",
     "*Table A6.10. Corners of the board's capacitances, $R_F$ = 1.5 kΩ, flat design, as in Table A6.9."),
    ("| Part | External $C_F$ (pF) | 0.2 / 0.1 pF | 0.2 / 0.3 | 0.5 / 0.1 | 0.5 / 0.3 |",
     "| Part | Total $C_F$ (pF) | $C_{\\mathrm{PCB}}$ = 0.2 pF, total −0.1 pF | 0.2 pF, +0.1 pF | 0.5 pF, −0.1 pF | 0.5 pF, +0.1 pF |"),
    ("Larger feedback resistors with 0.2 pF of feedback parasitic (the nominal value):",
     "Larger feedback resistors with 0.2 pF across $R_F$, the minimum total of the 2-kΩ designs (Table 1.1):"),
    ("Larger feedback resistors with 0.1 pF of feedback parasitic (an optimistic layout):",
     "Larger feedback resistors with 0.1 pF across $R_F$, close to the parasitic alone (Table 1.1):"),
    ("*Table A8.13. Recommended starting values (nominal $C_{\\mathrm{PCB}}$ = 0.35 pF, $C_{F,\\mathrm{par}}$ = 0.2 pF) and their tolerance.",
     "*Table A8.13. Recommended starting values (nominal $C_{\\mathrm{PCB}}$ = 0.35 pF, $C_{F,\\mathrm{par}}$ = 0.08 pF) and their tolerance."),
    ("The parasitic columns keep the same external capacitor and move the total by ∓0.1 pF.",
     "The external capacitor is the total minus the 0.08-pF parasitic; the two tolerance columns move the total by ∓0.1 pF."),
    ("| Nominal: $f_{-3\\,\\mathrm{dB}}$, PM, peaking | Parasitic 0.1 pF | Parasitic 0.3 pF |",
     "| Nominal: $f_{-3\\,\\mathrm{dB}}$, PM, peaking | Total −0.1 pF | Total +0.1 pF |"),
    ("| 0.25 pF (0.05 pF: no discrete part; pad overlap) |", "| 0.25 pF (0.17 pF: 0.1 pF and pad overlap) |"),
    ("| 0.27 pF (0.07 pF: pad overlap) |", "| 0.27 pF (0.19 pF: a 0.2-pF part) |"),
    ("| 0.55 pF (0.35 pF; e.g. 0.3 + pad) |", "| 0.55 pF (0.47 pF; e.g. 0.4 + pad) |"),
    ("| 0.65 pF (0.45 pF) |", "| 0.65 pF (0.57 pF) |", 2),
    ("| 0.55 pF (0.35 pF) |", "| 0.55 pF (0.47 pF) |", 3),
    ("| 0.75 pF (0.55 pF) |", "| 0.75 pF (0.67 pF) |"),
    ("| 0.31 pF (0.11 pF) |", "| 0.31 pF (0.23 pF) |"),
    ("| 0.44 pF (0.24 pF) |", "| 0.44 pF (0.36 pF) |"),
    # Appendix C
    ("7. **The parasitic feedback capacitance** of the resistor and pads actually used is assumed as 0.2 ± 0.1 pF.",
     "7. **The parasitic feedback capacitance** of the resistor, pads and pins actually used is estimated at 0.08 pF, with corners at 0.05 and 0.12 pF, by a two-dimensional model that leaves out the package interior and a patterned film (Appendix G). The bench board of Section 3.10 points to about 0.3 pF in another layout (Section G.13.5)."),
    ("Above about 5 kΩ the bandwidth follows the feedback parasitic, so its actual value on the board, 0.1–0.3 pF, decides whether 150 MHz is reached.",
     "Above about 5 kΩ the bandwidth follows the feedback capacitance, so its actual value on the board, 0.05–0.12 pF for the parasitic alone by Appendix G, decides whether 150 MHz is reached."),
    # Appendix E
    ("| `figures/` | Figures 1–37 as PNG (600 dpi) and PDF.", "| `figures/` | Figures 1–43 as PNG (600 dpi) and PDF."),
    ("the two schematics from `scripts_archive/make_schematics.py` and the simulations from `scripts_archive/make_case_figures.py` |",
     "the two schematics from `scripts_archive/make_schematics.py` and the simulations from `scripts_archive/make_case_figures.py`; `fig38`–`fig43` are Figures 38–43 of Appendix G (`scripts_archive/parasitic_cf/make_parasitic_cf_figures.py`) |"),
    ("the application notes and articles [A1]–[A24], and the ngspice manual [S1] |",
     "the application notes and articles [A1]–[A34], with the documents behind Appendix G in `appnotes/parasitic_cf/`, and the ngspice manual [S1] |"),
    ("Section 6.10 (Tables A6.38–A6.39): the robust designs at 2–10 kΩ for both feedback parasitics,",
     "Section 6.10 (Tables A6.38–A6.39): the robust designs at 2–10 kΩ for both feedback capacitances,"),
    ("the design examples of Chapter 4 use `case_studies.py` and `make_case_figures.py` |",
     "the design examples of Chapter 4 use `case_studies.py` and `make_case_figures.py`; the estimate of Appendix G and its figures use the scripts in `scripts_archive/parasitic_cf/`, indexed in its `INDEX.md` |"),
]
for item in R:
    old, new = item[0], item[1]
    rep(old, new, item[2] if len(item) > 2 else 1)

# Tables A6.9 and A6.10: the external capacitor becomes the total of the realised flat design
TOTALS = {
    "A6.9": {"OPA855": "0.20", "OPA858": "0.20", "OPA955": "0.20", "LMH6629 (COMP HI)": "0.54", "OPA856": "0.58",
             "OPA859": "0.54", "THS4304": "0.68", "OPA843": "0.92", "OPA846": "0.74", "OPA818": "0.49"},
    "A6.10": {"OPA855": "0.22", "OPA858": "0.21", "OPA955": "0.22", "LMH6629 (COMP HI)": "0.62", "OPA856": "0.68",
              "OPA859": "0.62", "THS4304": "0.78", "OPA843": "1.07", "OPA846": "0.87", "OPA818": "0.59"},
}
EXT = {
    "A6.9": {"OPA855": "0.00", "OPA858": "0.00", "OPA955": "0.00", "LMH6629 (COMP HI)": "0.34", "OPA856": "0.38",
             "OPA859": "0.34", "THS4304": "0.48", "OPA843": "0.72", "OPA846": "0.54", "OPA818": "0.29"},
    "A6.10": {"OPA855": "0.02", "OPA858": "0.01", "OPA955": "0.02", "LMH6629 (COMP HI)": "0.42", "OPA856": "0.48",
              "OPA859": "0.42", "THS4304": "0.58", "OPA843": "0.87", "OPA846": "0.67", "OPA818": "0.39"},
}
for tab, start_key in (("A6.9", "*Table A6.9. Corners of the board's capacitances"),
                       ("A6.10", "*Table A6.10. Corners of the board's capacitances")):
    a = t.index(start_key)
    b = t.index("\n\n*Table", a + 10)
    block = t[a:b]
    for part, total in TOTALS[tab].items():
        old = f"\n| {part} | {EXT[tab][part]} |"
        assert block.count(old) == 1, (tab, part)
        assert abs(float(total) - float(EXT[tab][part]) - 0.20) < 0.0101, (tab, part)
        block = block.replace(old, f"\n| {part} | {total} |")
    t = t[:a] + block + t[b:]

# Appendix D: the references of Appendix G
A_NEW = """
- **[A25]** J. Schurr, R. H. Judaschke and S. A. Awan, "Resistance standards with very small calculable AC-DC difference at frequencies up to 2 MHz for the calibration of precision LCR meters", *Measurement Science and Technology* 36, 015030 (2025). https://doi.org/10.1088/1361-6501/ad9169. Read in its arXiv version, arXiv:2407.17805v3, whose pages are cited. Source of the free-standing capacitances of Section G.13.2 and of the film-to-case model of Section G.2.3.
- **[A26]** Vishay Intertechnology, *Frequency Response of Thin Film Chip Resistors*, technical note 60107, Rev. 04-Feb-09 (measurements and models by Modelithics). https://www.vishay.com/docs/60107/freqresp.pdf
- **[A27]** Vishay Dale Thin Film, *FC: High Frequency (Up to 40 GHz) Resistor, Thin Film Surface Mount Chip*, datasheet 60093, Rev. 11-May-2026. https://www.vishay.com/docs/60093/fcseries.pdf
- **[A28]** Vishay Sfernice, *CH: High Frequency 70 GHz Thin Film Chip Resistor*, datasheet 53014, Rev. 03-Jul-2026. https://www.vishay.com/docs/53014/ch.pdf
- **[A29]** Vishay Beyschlag, *Resistors in Microwave Applications*, application note 28871, Rev. 19-Mar-13. https://www.vishay.com/docs/28871/resistorsmicrowaveapp.pdf
- **[A30]** KOA Corporation, *High-frequency characteristics of resistors*, technical note KDST_TN-010_v0100-EN, 2021. https://www.koaspeer.com/pdfs/technical_notes/High-frequency_characteristics_EN.pdf
- **[A31]** G. Brisebois, "Op Amp Combines Femtoamp Bias Current with 4GHz Gain Bandwidth Product, Shines New Light on Photonics Applications", *LT Journal of Analog Innovation* 25(2), July 2015; PDF pages are cited. https://www.analog.com/media/en/technical-documentation/tech-articles/lt-journal-article/LTJournal-V25N2-00-df-LTC6268-GlenBrisebois.pdf
- **[A32]** Analog Devices, "Transimpedance Amplifier Noise Considerations", technical article on the LTC6268, 18 February 2015. https://www.analog.com/en/resources/technical-articles/transimpedance-amplifier-noise-considerations.html
- **[A33]** Linear Technology, *Demo Manual DC2414A: LTC6268 and LTC6268-10 3-Channel SOT-23 Transimpedance Amplifier*, dc2414af (schematic Rev 3, 9 June 2016). https://www.analog.com/media/en/technical-documentation/user-guides/DC2414AF.PDF
- **[A34]** Texas Instruments, *Reference Design Maximizing Transimpedance Bandwidth for LIDAR and Time-of-Flight Applications*, TIDA-060025, design guide TIDUEL3A (November 2018, revised April 2022), with its bill of materials TIDRXT2 and layer plots TIDRXT6. https://www.ti.com/lit/pdf/TIDUEL3"""
B_NEW = """
- **[B3]** D. Gilbarg and N. S. Trudinger, *Elliptic Partial Differential Equations of Second Order*, Springer, 2001 (Classics in Mathematics). Its Section 8.1, the weak maximum principle for operators in divergence form, is used in Section G.4.3.
- **[B4]** L. V. Ahlfors, *Complex Analysis*, 3rd ed., McGraw-Hill, 1979. Its Chapter 4, with the argument principle, is used in Section G.6.
- **[B5]** F. W. J. Olver et al. (eds.), *NIST Digital Library of Mathematical Functions*, https://dlmf.nist.gov, the online edition of the *NIST Handbook of Mathematical Functions* (Cambridge University Press, 2010). Its Chapters 19 and 22, on the elliptic integrals and Jacobi's elliptic functions, are used in Sections G.5–G.10."""
i = t.index("\n- **[A24]**")
j = t.index("\n", i + 1)
t = t[:j] + A_NEW + t[j:]
i = t.index("\n- **[B2]**")
j = t.index("\n", i + 1)
t = t[:j] + B_NEW + t[j:]

# Appendix E: the data of Appendix G
row = ("| `data/parasitic_cf/` | Appendix G: the measured capacitances across chip resistors (`resistor_shunt_capacitance.md`, "
       "`.json`, with the curve readings in `resistor_curve_readings.csv`) and across feedback networks on TIA boards "
       "(`tia_feedback_parasitics.md`, `.json`, with `inferred_values.json`), the resistor dimensions, land patterns and "
       "permittivities (`geometry_and_permittivity.md`, `.json`), and every number of the estimate (`analytic_estimate.json`, "
       "from `scripts_archive/parasitic_cf/cf_parasitic_estimate.py`) |\n")
anchor = "| `data/digitization_checks/` |"
assert t.count(anchor) == 1
t = t.replace(anchor, row + anchor)

# Appendix G at the end
t = t.rstrip("\n") + "\n\n---\n\n" + app.rstrip("\n") + "\n"
open(note_path, "w", encoding="utf-8", newline="\n").write(t)
print("written; sha", hashlib.sha256(t.encode("utf-8")).hexdigest()[:12], "lines", t.count("\n"))
