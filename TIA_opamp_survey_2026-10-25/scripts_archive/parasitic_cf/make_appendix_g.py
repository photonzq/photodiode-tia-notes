"""Turn the standalone derivation of the parasitic feedback capacitance into Appendix G of the note.

Usage: python make_appendix_g.py <parasitic_cf_derivation.md> <out_appendix_g.md>

What it does:
- headings: the draft's sections 1-14 become G.1-G.14, its subsections G.n.m;
- equations: (P1)-(P49) become (G.1)-(G.49), tags and references alike;
- tables: P1-P3 become G.1-G.3, and the five tables without a caption get captions G.4-G.8;
- figures: P1-P6 become Figures 38-43 in the order in which they stand (P6 before P5), with the files
  renamed to figures/fig38_... - fig43_...;
- citations: the draft's own list [P1]-[P8] is replaced by the note's conventions: datasheet pages as
  "OPA855 p29", articles and books by their entries [A25]-[A34] and [B3]-[B5] of Appendix D, and the data
  collections by their paths;
- references to the draft's own sections get the prefix G.; references to the note's sections, tables and
  equations stay as they are;
- the opening, Section 1's account of Table 1.1, Section 13 (citations, Table G.8 and the bench board) and
  Section 14 are rewritten for the value the note adopts.
Every replacement must match the stated number of times.
"""
import re
import sys

src, out = sys.argv[1], sys.argv[2]
t = open(src, encoding="utf-8").read().replace("\r\n", "\n")


def rep(old, new, count=1, text=None):
    """Replace old by new in text (default: the whole draft) exactly count times."""
    global t
    s = t if text is None else text
    n = s.count(old)
    assert n == count, f"{n} matches instead of {count}: {old[:90]!r}"
    s = s.replace(old, new)
    if text is None:
        t = s
    return s


# ---------------------------------------------------------------- split the draft
i2 = t.index("## 2 Which capacitance the amplifier sees")
i13 = t.index("## 13 Comparison with measurements")
i14 = t.index("## 14 What this means for the note")
head, body, s13 = t[:i2], t[i2:i13], t[i13:i14]
tab_start = head.index("*Table P1.")
tab_end = head.index("For the note's layout")
table_p1 = head[tab_start:tab_end]  # caption, table and the paragraph on smaller pads

# ---------------------------------------------------------------- the opening and Section G.1
HEAD = r"""## Appendix G. Parasitic capacitance across the feedback resistor

Table 1.1 takes the parasitic feedback capacitance $C_{F,\mathrm{par}}$ as 0.08 pF, with corners at 0.05 and 0.12 pF. This appendix derives that value from the geometry of a chip resistor on its land pattern and of the amplifier's pins. The value matters wherever the parasitic is a large part of the total feedback capacitance. The 2-kΩ OPA855 design of Section 4.2 has 0.20 pF in total, of which 0.08 pF is the parasitic and 0.12 pF a fitted capacitor, and the feedback zero, the phase margin and the peaking all move with the total (Section 6.2.5).

Every formula is derived from electrostatics in the order in which it is used, and each special function is defined where it first appears. Each approximation is stated together with the direction in which it moves the result, and the estimate is compared with published measurements at the end. The script `scripts_archive/parasitic_cf/cf_parasitic_estimate.py` evaluates every formula and checks each one numerically a second way, and `scripts_archive/parasitic_cf/make_parasitic_cf_figures.py` draws Figures 38–43 from the same formulas. Those numerical checks confirm the arithmetic; they are not part of any argument.

### G.1 The estimate in brief

Table G.1 gives the capacitance across a chip resistor on its land pattern, with the power and ground planes removed under it, as the OPA855 datasheet asks (p29). It is evaluated at the nominal dimensions of Table G.2, on the IPC-7351 land pattern. Each contribution has a range from two sources: the two bounds that bracket each idealised problem, and the permittivity ranges of Table G.3. The lower bound is rigorous within the two-dimensional model; the upper estimate takes the upper end of every term. The last column spreads the body's dimensions over their datasheet tolerances.

"""
HEAD_AFTER = r"""For the layout of this note, an 0402 beside OPA855 pins 1–3 (Figure 43), the resistor and pads give 35–51 fF at nominal dimensions, with a central value of 45 fF and 29–70 fF across the tolerances. The two-dimensional model adds at most about 25 fF for the pins (Section G.11), less where pin 4 and the thermal pad shield them. On top come the package interior and, for a patterned thin-film part, its film, which the model does not compute. The sum is about 0.04–0.08 pF at nominal dimensions and at most about 0.1 pF across the tolerances. The vendors' measured body values run 5–15 fF above the model's body term in 0402 (Section G.13.1), which moves the estimate towards the upper part of that range. Measured careful single-resistor layouts in 0603 and 0805, which include traces and pins, give 0.10–0.14 pF (Section G.13.3).

Table 1.1 therefore takes 0.08 pF as the nominal value, the upper end of the range at nominal dimensions, where the vendors' body values place it. Its lower corner, 0.05 pF, adds the lower bound for the resistor and pads at nominal dimensions, 35 fF, to that for the pins without their grounded neighbours, 15 fF. Its upper corner, 0.12 pF, is the largest value across the tolerances, about 0.1 pF, with 0.02 pF added for what the model leaves out: the package interior, the film pattern of a plain or lightly trimmed film, and the field around the ends (Section G.12). A precision thin-film part with deep trim cuts can exceed it (Section G.13.2).

Mounting the resistor upside down changes these numbers by less than 2 fF in this layout (Section G.10.7). Ground under the resistor would lower $C_{F,\mathrm{par}}$ but adds capacitance at the summing node, which is a loss for the OPA855 design (Section G.10.6).

"""
table_p1 = rep("*Table P1. Capacitance across the resistor and its pads (fF), planes removed, film facing up.*",
               "*Table G.1. Capacitance across the resistor and its pads (fF), planes removed, film facing up; the "
               "amplifier's pins are added in Section G.11.*", text=table_p1)
table_p1 = rep("Vishay 28950; Table P2)", "Vishay 28950; Table G.2)", text=table_p1)
head = HEAD + table_p1 + HEAD_AFTER

# ---------------------------------------------------------------- Section G.13
s13 = rep("The measured values below are taken from the two collections in this folder ([P4], [P5]), which give "
          "each source with its page.",
          "The measured values below are cited with their sources, and the collections "
          "`data/parasitic_cf/resistor_shunt_capacitance.md` and `data/parasitic_cf/tia_feedback_parasitics.md` give "
          "every value with its page and the way it was read.", text=s13)
s13 = rep("\n| Size | Model, nominal dimensions (fF) |",
          "\n*Table G.7. The body's capacitance in the model against the vendors' fitted values over a ground plane "
          "(fF). Vishay FC: [A26, p. 1, Table 1] and [A27, p. 3]; Vishay CH: read from the internal-impedance curves "
          "of [A28, pp. 7–8]; Vishay Beyschlag MCT and MCU: [A29, p. 4 and p. 5, Fig. 7]; KOA RK73: [A30, p. 3, "
          "Table 1]. Resistors alone, without the amplifier.*\n\n| Size | Model, nominal dimensions (fF) |", text=s13)
s13 = rep("The highest vendor values, KOA's, come from a fixture that KOA does not describe ([P5]).",
          "The highest vendor values, KOA's, come from a fixture that KOA does not describe [A30].", text=s13)
s13 = rep('"A typical 0805 resistor has about 70fF of capacitance in air" ([P4], DC2414A manual, p. 2).',
          '"A typical 0805 resistor has about 70fF of capacitance in air" [A33, p. 2].', text=s13)
s13 = rep("between 10 and 110 MHz ([P3], p. 7, Table 1).", "between 10 and 110 MHz [A25, p. 7, Table 1].", text=s13)
s13 = rep("The photographs in [P3] (p. 4, Figure 2) show", "The photographs of [A25, p. 4, Fig. 2] show", text=s13)
s13 = rep("KOA states that its thick-film RK73 values do not depend on the resistance ([P5]),",
          "KOA states that its thick-film RK73 values do not depend on the resistance [A30, p. 3],", text=s13)
OLD_133 = s13[s13.index("The board-level collection ([P4]) gives four totals"):s13.index("The model's resistor-on-pads values")]
NEW_133 = r"""Four boards give measured totals for single unshielded resistors (Table G.8).

*Table G.8. Measured totals across a single unshielded feedback resistor on a board, with its traces and the amplifier's pins. Amplifiers: LTC6268-10, LTC6268 and OPA858.*

| Board | Measured total | Source |
|---|---|---|
| LTC6268-10, 0805 at 402 kΩ, basic layout | 0.10 pF | LTC6268-10 p14, Figs 4–5; [A31, p. 3, Fig. 4] |
| LTC6268 article, 0603 at 499 kΩ, basic layout | 0.13 pF | [A32, Figs 6–7] |
| DC2414A, careful layout on a laminate with $\varepsilon_r$ = 3.4 | about 0.1 pF; the manual's +30–40 % for FR-4 gives 0.13–0.14 pF | [A33, pp. 1–3] |
| TIDA-060025, OPA858 with two 0201 resistors in series, each beside a 0.15-pF capacitor | no visible excess over the intended 75 fF, inferred from the measured edges | [A34, pp. 6, 8, 14, 18] |

"""
s13 = s13.replace(OLD_133, NEW_133)
s13 = rep("With ground copper under the resistor, the collection gives:", "With ground copper under the resistor, the "
          "same boards give:", text=s13)
s13 = rep("- at most 11.6 fF for the 0805 of the LTC6268-10 board, with a wide ground trace under the whole body;",
          "- at most 11.6 fF for the 0805 of the LTC6268-10 board, with a wide ground trace under the whole body "
          "(LTC6268-10 p14–p15, Figs 6–7; [A31, pp. 3–4]);", text=s13)
s13 = rep("- at most 28.5 fF for the 0603 of the LTC6268 article;",
          r"- at most 28.5 fF for the 0603 of the LTC6268 article, from its measured 11.2 MHz at 499 kΩ, "
          r"$1/(2\pi\times499\ \mathrm{k\Omega}\times11.2\ \mathrm{MHz})$ [A32, Figs 8–9];", text=s13)
s13 = rep("- about 33 fF and about 7 fF for the two shielded channels of the DC2414A.",
          "- about 33 fF and about 7 fF for the two shielded channels of the DC2414A [A33, pp. 1–2].", text=s13)
s13 = rep("These are reductions by factors of 3 to more than 8 ([P4]).",
          "These are reductions by factors of 3 to more than 8.", text=s13)
s13 = s13.rstrip("\n") + "\n\n" + r"""### 13.5 The bench board of SECTIONX 3.10

The OPA846 board of SECTIONX 3.10 has no fitted feedback capacitor, and its measured transimpedance and noise at 50 MHz point to about 0.3 pF across its 1.2-kΩ resistor, with about 14 pF at the summing node (Table A3.7). That is two and a half times the upper corner of Table 1.1. The value is inferred from the loop, not measured directly, and it rests on the node capacitance, itself inferred because the photodiode's capacitance and connection were not recorded (Appendix C, item 11); nor does the note record that board's resistor size or traces. OPA846 has no FB pin (Table A6.4), so its feedback network cannot sit beside an FB pin as in Figure 43, and the traces that join its output and inverting-input pins add a coupling that this estimate leaves out (Eq. (P48)). The bench board shows what a layout other than the one assumed here can carry. For an actual board, the measurement of SECTIONX 9.7, item 5, settles the value.

"""

# ---------------------------------------------------------------- Section G.14 (replaces the draft's 14 and its list)
S14 = r"""### G.14 How the note uses the estimate

**Table 1.1.** $C_{F,\mathrm{par}}$ = 0.08 pF, with corners at 0.05 and 0.12 pF (Section G.1). The value holds for an 0402 or 0201 resistor beside the amplifier's pins, with the planes removed under the feedback network, and for a plain or lightly trimmed film. A precision thin-film part with deep trim cuts can add several tens of femtofarads (Section G.13.2), and a layout with traces between the resistor and the pins adds their coupling (Eq. (G.48)).

**The minimum total of 0.2 pF.** The note's designs keep a total $C_F$ of at least 0.2 pF, and the tolerance of the total, not the parasitic, sets that floor. The total is a fitted capacitor, typically ±0.05 pF (Section 8.10), plus the parasitic, whose corners lie 0.03 pF below and 0.04 pF above its nominal value. It is therefore known to about ±0.1 pF, the corner used throughout (Sections 5.1, 6.2.5 and 6.2.8). Section 6.2.8 shows that a design whose total is 0.2 pF or less is governed by that tolerance rather than by its nominal margin: OPA855 at 0.15 pF falls from 44–50° to 16–19° at the corners. The flat and robust designs are therefore realised at 0.2 pF or more (Section 1.5).

**The OPA855 design.** Its flat design needs 0.19 pF and is realised at the 0.2-pF minimum: 0.08 pF of parasitic and a fitted 0.12 pF (Sections 4.2 and 8.10).

**Ground under the resistor.** Ground under the feedback network would lower the parasitic, but at 2 kΩ every design fits a capacitor anyway, so the capacitance it adds at the summing node is only a loss (Section G.10.6). The planes stay removed, as the OPA855 datasheet asks.

**Larger feedback resistors.** At 3–10 kΩ the parasitic alone may be the whole feedback capacitance. Section 6.10 gives the designs with 0.2 pF across the resistor (Table A6.38) and with 0.1 pF (Table A6.39); the second is the one nearest this estimate. The high-gain note's 10-kΩ SPICE checks, in its Section 9.8, run the designs of Table A6.38.

**The high-gain note's value.** That note takes the resistor's own capacitance as 0.1 pF, with 0.05 and 0.2 pF as its range. The measured values of that quantity span 25–65 fF for bodies over a ground plane (Section G.13.1) and 83–123 fF for free-standing patterned thin-film parts (Section G.13.2), and this estimate gives 0.08 pF with the pads and pins, so 0.1 pF is consistent with both.

**Designs that need less.** A design that needs less feedback capacitance than the parasitic gives has two remedies: two resistors in series, as the OPA855 datasheet advises below 0.15 pF (p29), or ground under the resistor at the price of Section G.10.6.
"""

# ---------------------------------------------------------------- citations in the body
for old, new, n in [
    ("([P1], p. 29, Section 9.4.1 and Figure 9-12)", "(OPA855 p29, its Section 9.4.1 and Fig 9-12)", 1),
    ("([P1], p. 3, Table 5-1; Figure P5a)", "(OPA855 p3, its Table 5-1; Figure P5a)", 1),
    ("([P1], p. 3, Table 5-1)", "(OPA855 p3, its Table 5-1)", 1),
    ("([P1], p. 38: body 1.9–2.1 mm, terminals 0.2–0.4 mm long)", "(OPA855 p38: body 1.9–2.1 mm, terminals 0.2–0.4 mm long)", 1),
    ('([P1], p. 38, "side wall metal thickness")', '(OPA855 p38, "side wall metal thickness")', 1),
    ("([P1], p. 38)", "(OPA855 p38)", 1),
    ("([P1], p. 39)", "(OPA855 p39)", 2),
    ("([P1], p. 29)", "(OPA855 p29)", 1),
    ("(DSG0008A land pattern, [P1] p. 39)", "(DSG0008A land pattern, OPA855 p39)", 1),
    ("([P1] p. 29, Figure 9-12)", "(OPA855 p29, Fig 9-12)", 1),
    ("([P2], pp. 14–15)", "(p14–p15)", 1),
    ("where $u = v = 1/2$ ([P3], p. 3, Eq. (2)).", "where $u = v = 1/2$ [A25, p. 3, Eq. (2)].", 1),
    ("Vishay's thin-film note [P5] gives 99.5 %", "Vishay's thin-film note [A26, p. 1] gives 99.5 %", 1),
    ("for the wrap-around version ([P5], p. 1, Table 1).", "for the wrap-around version [A26, p. 1, Table 1].", 1),
    ("this is the weak maximum principle [P6];", "this is the weak maximum principle [B3, Section 8.1];", 1),
    ("$k = \\sqrt m$ ([P7], §19.2(ii)).", "$k = \\sqrt m$ [B5, §19.2(ii)].", 1),
    ("the Jacobi function sn ([P7], §22.16(i))", "the Jacobi function sn [B5, §22.16(i)]", 1),
    ("([P7], §19.8(i))", "[B5, §19.8(i)]", 1),
    ("Carlson's symmetric elliptic integral ([P7], §19.16(i)), not the resistor.",
     "Carlson's symmetric elliptic integral [B5, §19.16(i)], not the resistor.", 1),
    ("$-2F(\\arcsin\\sqrt{t/m}\\,|\\,m)$ ([P7], §19.25(i), with the homogeneity of $\\mathcal R_F$),",
     "$-2F(\\arcsin\\sqrt{t/m}\\,|\\,m)$, by [B5, §19.25(i)] and the homogeneity of $\\mathcal R_F$,", 1),
    ("the descending Landen transformation ([P7], §19.8(ii)).", "the descending Landen transformation [B5, §19.8(ii)].", 1),
    ("([P7], §19.12)", "[B5, §19.12]", 1),
    ("which is 1 inside the rectangle and 0 outside ([P8], Ch. 4).", "which is 1 inside the rectangle and 0 outside [B4, Ch. 4].", 1),
    ('([P4] collection, "Package and pins")', '(collection `data/parasitic_cf/tia_feedback_parasitics.md`, "Package and pins")', 1),
    ("(Appendix B, p. 1): 0.5, 0.4, 0.3.", "KOA'S_APPENDIX_B", 1),
    ("For a design that must get below the parasitic floor,", "For a design that must get below the parasitic,", 1),
    ("The collection `geometry_and_permittivity.md` gives", "The collection `data/parasitic_cf/geometry_and_permittivity.md` gives", 1),
    ("(Eq. (11) of the note)", "(Eq. (11))", 1),
    ("Eq. (7) of the note", "Eq. (7)", 2),
    ("Eq. (19) of the note", "Eq. (19)", 1),
    ("Data sheets and papers call several", "Datasheets and papers call several", 1),
    ("sets the feedback zero of a transimpedance amplifier (TIA), so that", "sets the feedback zero of the TIA, so that", 1),
]:
    body = rep(old, new, n, text=body)
body = rep("  - KOA KOA'S_APPENDIX_B", "  - KOA's Appendix B (p. 1): 0.5, 0.4, 0.3.", text=body)

# ---------------------------------------------------------------- captions for the tables that had none
for old, new in [
    ("\n| Half-block | Side of $\\mathcal R$ | Image of |",
     "\n*Table G.4. The half-block of the body placed on the rectangle $\\mathcal R$ of Section 6: each side, the side "
     "of $\\mathcal R$ it becomes, and the part of the real axis whose image that side is.*\n\n"
     "| Half-block | Side of $\\mathcal R$ | Image of |"),
    ("\n| Depth of the plane, $h$ |",
     "\n*Table G.5. The pads of an 0402 over a ground plane at depth $h$: the mutual capacitance across $R_F$ and each "
     "pad's capacitance to the plane, per unit $\\varepsilon_{\\mathrm{pcb}}\\varepsilon_0$ and per millimetre of pad "
     "width.*\n\n| Depth of the plane, $h$ |"),
    ("\n| | Approximation | Direction | Size or bound |",
     "\n*Table G.6. Every approximation of the estimate, with the direction in which it moves the result and its size "
     "or bound.*\n\n| No. | Approximation | Direction | Size or bound |"),
]:
    body = rep(old, new, text=body)

# ---------------------------------------------------------------- reassemble and apply the mechanical renumbering
t = head + body + s13 + S14
# protect the datasheet's own section number before the section prefixes are added
t = rep("its Section 9.4.1", "its SECTIONX 9.4.1")
# headings
t = re.sub(r"^## 13 Comparison with measurements", "### G.13 Comparison with measurements", t, flags=re.M)
t = re.sub(r"^## (\d+) ", r"### G.\1 ", t, flags=re.M)
t = re.sub(r"^### (\d+\.\d+) ", r"#### G.\1 ", t, flags=re.M)
# equation tags and references
t = re.sub(r"\\tag\{P(\d+)\}", r"\\tag{G.\1}", t)
t = re.sub(r"\(P(\d+)\)", r"(G.\1)", t)
# tables
t = re.sub(r"Table P(\d)\b", r"Table G.\1", t)
# figures, in the order in which they stand
FIG = {"1": "38", "2": "39", "3": "40", "4": "41", "6": "42", "5": "43"}
t = re.sub(r"Figure P(\d)", lambda m: "Figure " + FIG[m.group(1)], t)
t = re.sub(r"\]\(\.\./\.\./figures/parasitic_cf/pcf(\d)_([a-z0-9_]+)\.png\)",
           lambda m: f"](figures/fig{FIG[m.group(1)]}_parasitic_cf_{m.group(2)}.png)", t)
# the draft's own sections get the prefix G.
SEC = re.compile(r"\b(Sections?) (\d+(?:\.\d+)*(?:(?: to | and |, |–)\d+(?:\.\d+)*)*)")


def prefix(m):
    nums = re.sub(r"(?<![\d.])(\d+(?:\.\d+)*)", r"G.\1", m.group(2))
    return f"{m.group(1)} {nums}"


# only inside the converted draft: the rewritten parts already carry their prefixes or are the note's own
cut_a = t.index("### G.1 The estimate in brief")
cut_b = t.index("Table 1.1 therefore takes 0.08 pF")
cut_c = t.index("### G.14 How the note uses the estimate")
mid = SEC.sub(prefix, t[t.index("### G.2 Which capacitance"):cut_c])
t = t[:t.index("### G.2 Which capacitance")] + mid + t[cut_c:]
assert t.count("SECTIONX ") == 4, t.count("SECTIONX ")
t = t.replace("SECTIONX ", "Section ")
# approximations are numbered 1-15, so that they cannot be read as the note's Appendix A
t = re.sub(r"(pproximations?) A(\d+) and A(\d+)", r"\1 \2 and \3", t)
t = re.sub(r"(pproximations?) A(\d+)", r"\1 \2", t)
t = re.sub(r"^\| A(\d+) \|", r"| \1 |", t, flags=re.M)
# spelling of the note
t = t.replace("data-sheet", "datasheet").replace("data sheet", "datasheet")
# leftovers that must not survive
assert not re.search(r"\(P\d", t)
for bad in ("[P1]", "[P2]", "[P3]", "[P4]", "[P5]", "[P6]", "[P7]", "[P8]", "Table P", "Figure P",
            "data sheet", "of the note", "this document", "This document", "parasitic_cf/pcf"):
    assert bad not in t, bad
assert "\r" not in t
open(out, "w", encoding="utf-8", newline="\n").write(t.rstrip("\n") + "\n")
print("written", out, len(t.split("\n")), "lines")
