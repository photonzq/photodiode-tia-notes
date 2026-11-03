r"""Reviewed fixes of the logic round of 1 Nov 2026 for Chapter 5, read by edit_logic_round2.py.

The chapter opening becomes a short purpose and roadmap; Section 5.1, which listed the findings before
the method, becomes the motivation (why a cross-check, what a macromodel can and cannot settle); the
findings are stated once, in Section 5.9.  Every number of the old Section 5.1 is either in the new
Section 5.9 or in Sections 5.3-5.8.
"""

OPENING = r"""Every phase margin, bandwidth and noise density of Chapter 4 comes from our own model, fed with datasheet curves. Before Chapter 6 compares the candidates on those numbers, this chapter tests the model against the manufacturers' SPICE macromodels in the same circuits. The first seven amplifiers are the leading candidates:
- OPA855 and OPA818, the two variants of the proposed front end (Section 8.9);
- OPA856, OPA858, OPA859 and LMH6629 (COMP pin high);
- OPA846, the amplifier of the bench board of Section 4.10.

Section 5.1 explains why the cross-check is needed and what a macromodel can and cannot settle. Sections 5.2 and 5.3 give the method: Middlebrook's double injection, which reads the loop gain of the intact circuit, and the small-signal quantities extracted from each macromodel, with which our equations predict the closed loop. Sections 5.4–5.8 give the results: the datasheets' own test circuits as referee, the TIA designs with scans of their feedback capacitance, the noise, the large-signal limits and the bench board. Eleven further amplifiers run through the same fixtures and test circuits (Section 5.1), and Section 6.5 finds every part's best design in SPICE. Section 5.9 collects what the cross-check found and what it changes in our analysis. The simulator is ngspice-46, driven from a Python script without a schematic; Appendix B.1 is a working guide to running it this way, and Appendix B.2 says how to reproduce every number."""

SECTION_51 = r"""### 5.1 Why a SPICE cross-check, and what a macromodel can settle

The analytical model of Chapter 4 evaluates Eqs. (13), (14) and (23) with two inputs per amplifier: the open-loop curve digitized from its datasheet and a pure input capacitance taken from the datasheet. Both inputs are weakest where our designs are marginal. Several curves end near 1 GHz (OPA818's at 0.96 GHz, Figure 4), so a gain margin at gigahertz frequencies rests on extrapolation or, for OPA855, on a plotted 4–7 GHz bump that Table A4.5 shows to be exaggerated. A datasheet curve gives the gain from the non-inverting input, while a TIA drives the inverting one. And three TI datasheets state a phase margin or GBW that disagrees with their own plotted curve (Table A4.2). Section 4.5 therefore reads every phase margin below about 50° with the results of this chapter.

A vendor's macromodel can settle three things. It is a complete circuit, so its small-signal quantities, measured in simple fixtures and put into our equations, test whether the equations leave anything out (Section 5.3). It extends to tens of gigahertz, so the double injection of Section 5.2 reads its loop gain, and both margins, beyond the end of the datasheet curves. And where a datasheet contradicts itself, the closed-loop test circuit printed in it decides which description is consistent with it (Section 5.4).

A macromodel cannot settle what it does not contain. It is the vendor's fit to a chosen set of the part's characteristics, and the TI models list which ones (Table B.1). Where a model is fitted to the datasheet's closed-loop response, agreeing with that response confirms the fit, not the model (Section 5.4), so where the datasheet and the macromodel disagree, neither is automatically right. An input capacitance or a current noise that a model gets wrong stays open whatever SPICE gives, and board parasitics at gigahertz frequencies, unit-to-unit spread and temperature are outside every model used here.

The designs checked are those that Chapters 6 and 8 choose with the analytical model; Section 5.5 lists them with their values, so that this chapter does not depend on the later ones. Variant A is OPA855 on 5 V and variant B is OPA818 on ±6.5 V, the two variants of the proposed front end (Section 8.9), each in four configurations: 1 or 2 pF at the node, and 2 or 1.5 kΩ. A corner is one of the nine combinations of the total $C_F$ moved by 0 or ±0.1 pF and $C_D$ by 0 or ±0.2 pF. Eleven further amplifiers run through the same fixtures and test circuits:
- OPA955, the candidate with the largest gain-bandwidth product and the lowest noise penalty, which TI supplies only as a TINA-TI file that stores the netlist as plain text (Appendix B.1);
- eight parts that our analysis found less suitable, OPA657, OPA847, LMH6624, THS4021, ADA4817-1, AD8099, ADA4899-1 and ADA4895-1, to see whether their models agree with that verdict;
- OPA817 and OPA814, which our analysis left out (Table A2.4).

Sections 5.3–5.5 report them under their own headings, and Section 6.5 finds their best designs."""

SECTION_59 = r"""### 5.9 What the cross-check found, and what it changes

**Our method holds, except for gain margins.** Fed with each macromodel's own quantities, its open-loop gain, input admittance, output impedance and noise sources, our equations reproduce every SPICE result of the first seven parts: the loop gain to 0.1° of phase margin and 0.1 dB of gain margin, the bandwidth to 1 % and the noise density to 0.3 % (Section 5.3, Table A5.4). With the simpler inputs used throughout this note, one open-loop curve and a pure input capacitance, the phase margin moves by at most 1.8° for OPA855, OPA818, OPA858 and OPA859, 2.6° for OPA856, 3.1° for OPA846 and 6.4° for LMH6629. The gain margin, however, comes out 4–7 dB optimistic for OPA855, OPA818, OPA858 and LMH6629, because above 1 GHz the gain from the inverting input differs from that from the non-inverting input and the output impedance loads the feedback network. Above 1 GHz the datasheet curves also differ from the macromodels by more than this error, so our gain margins from the curves differ from SPICE in both directions. Over the nominal designs and the worst of their nine corners they are about 1.1 dB above SPICE for OPA855 (Figure 5b), 2.3–2.5 dB above for LMH6629 and 5.1 dB above for OPA859, and 4.5–4.9 dB below for OPA818, 5.7–5.8 dB below for OPA846, 11.8–12.4 dB below for OPA858 and 17.1–18.3 dB below for OPA856 (the SPICE values are in Table A5.6, ours in `spice/results/loop.json`). Gain margins from the datasheet curves are therefore indicative only; the phase margins from the curves differ from SPICE as Sections 5.4 and 5.5 describe.

**Variant A (OPA855) is confirmed, with a tighter window of $C_F$.** In all four configurations SPICE gives 62.5–69.1° of phase margin, 291–548 MHz and noise within 2.5 % of our analysis. The new information is the gain margin at about 3.4 GHz, set by the plateau of $A_-$ (Table A5.3). It follows Eq. (47), GM = $20\log_{10}(NG_\infty/5.3)$, so 3 dB needs $NG_\infty \ge 7.5$, i.e. $C_F \le C_T/6.5$; the datasheet's minimum gain of 7 leaves 2.4 dB, and below $NG_\infty$ = 5.3 the model oscillates at about 3 GHz. At the upper corner ($C_F$ + 0.1 pF with $C_D$ − 0.2 pF) the margin is only 1.4–3.1 dB. Together with ≥ 45° and ≤ 1 dB of peaking at all three photodiode capacitances, this gives windows of 0.157–0.300 pF (2 kΩ) and 0.181–0.298 pF (1.5 kΩ) for the 1-pF designs, whose total $C_F$ must therefore be held to 0.230 ± 0.070 pF or 0.240 ± 0.055 pF, or trimmed on the first board, instead of the ±0.1 pF of Table A8.13. The 2-pF designs, with windows of 0.188–0.454 pF and 0.217–0.453 pF, keep ±0.1 pF at 0.320 ± 0.130 and 0.335 ± 0.115 pF (Tables A5.8 and A5.9). The corners that lose this margin are those at which Table A8.11 flags a second crossing on the plotted 4–7 GHz bump; the mechanism differs, but the flags mark a real loss of margin.

**Variant B (OPA818) is more stable and slower in the vendor's model.** SPICE gives 43–50° nominal and 39–45° at the worst of the nine capacitance corners, against our 27–35° and 23–30° (21–30° over the 27 corners of Table A8.11, which add the spread of open-loop gain), with no peaking, and 226–333 MHz against our 302–442 MHz (Section 5.5). Section 5.4 favours the model: it reproduces the datasheet's measured response at a gain of 7, 758 MHz and 1.37 dB of peaking against 765 MHz and 1.4 dB, while the datasheet's open-loop curve, used with the part's input capacitance, predicts 4.3 dB. Because TI fits this model to that closed-loop data, the test shows the curve to be inconsistent rather than the model to be independently confirmed; the first board decides (Appendix C, item 16). If the model is right:
- variant B needs no equalizer;
- at 1 pF and 2 kΩ the 0.55 pF of Table A8.11 is the 45°, ±0.1-pF design, and accepting 40°, or trimming $C_F$ to ±0.05 pF, buys 15–37 % of bandwidth there (309 MHz at 0.42 pF) and 6–20 % in the other configurations (Table A5.10);
- the loop caps the bandwidth near 331–434 MHz whatever $C_F$ is, which only an equalized design with about 10 dB of peaking approaches.

In the model its dark noise is 7.83 against our central 6.49 pA/√Hz at 100 MHz, 1.6 dB above the central estimate and 1.0 dB above the high one. The model adds a rising current noise, 1.6–1.9 times the datasheet's curve, on top of the $e_n\omega C$ of its own input capacitance, so the SPICE value is an upper bound (Section 5.6). Variant B's dynamic-range lead at high photocurrent and for tones below about 100 MHz (Table A6.28, Section 8.9) is unaffected: the slew and swing limits are confirmed (Section 5.7), and the noise change is small next to the 3–11-dB lead. Only in the dark at a 100-MHz tone, where variant B leads by only 0.6 dB on the central estimate (Section 8.9), does the extra noise exceed the lead; at their best SPICE designs OPA818 overtakes OPA855 from $I_1 + I_2$ = 30 µA (Section 6.6.2).

**The other parts of the first seven** differ from our analysis in the direction that Sections 5.3 and 5.4 explain.
- **OPA858's open-loop gain is the table's 5.5 GHz**, not the plotted curve's: the macromodel's gain is 4–5 dB below the curve, and it reproduces the closed-loop table at a gain of 7. Its 2-kΩ design at 0.25 pF has 49° nominal and 33° at the low-$C_F$ corner, so the plotted-curve entries of Tables A9.1 and A9.2 (539 MHz, 58°) are optimistic, as Section 6.2.3 warned, and the calibrated entries are the ones to use.
- **LMH6629's model has 1.3 pF at the inverting input against the datasheet's 5.7 pF** ($C_{CM}$ 1.7 pF plus a simulated $C_{DIFF}$ of 4 pF), so its SPICE noise is low: 4.76 against 7.65 pA/√Hz at 200 MHz. SPICE cannot settle this; a measurement of the input capacitance must.
- **OPA856 agrees within 4° and 10 %**, with the macromodel the optimistic one (Section 5.4), and **OPA859 within 3° of our calibrated curve (Table A6.7) and 12 % in bandwidth**. The spot noise of both agrees within 0.5 dB.
- **OPA846 lies between the two descriptions.** For its datasheet's test circuit the macromodel gives 1.4 dB of peaking and the curve with its input capacitance 5.6 dB, against 3.1 dB measured, so its 2-kΩ design lies between our 34° and SPICE's 45°. SPICE confirms the bench board of Section 4.10 in kind: about 15 pF at the node for the measured 7 pA/√Hz at 50 MHz, 7–8° of phase margin and a +17 dB resonance at 130–150 MHz (Section 5.8).

**Large signals.** The amplitudes of Table A6.28 are where the macromodels limit hard, within 7 %: the THD reaches −40 dBc at 0.98–1.07 times them, and −60 dBc needs a swing-limited output below 0.88–0.93 of them. Below these limits the models are nearly linear, so the datasheets' distortion figures remain the reference for small signals (Section 5.7).

**All eighteen macromodels at their best designs (Section 6.5).** One rule for all parts at 1 pF and 2 kΩ, 45°, 3 dB and ≤ 1 dB of peaking over $C_D$ ± 0.2 pF and $C_F$ ± 0.05 pF, ranks them (Table A6.32, Figure 17).
- **OPA955 is the strongest**: 0.90 dB above the Johnson floor and 560 MHz without added capacitance. With OPA855's 5-V supply and 1.52-V swing, it improves the dark noise by about 2 dB without changing the large-signal limit. Its datasheet is advance information, the part is preproduction, and its macromodel is conservative against its datasheet's test circuit.
- **OPA855 follows at 3.01 dB and 535 MHz, then OPA858 at 4.08 dB and 446 MHz.**
- **The parts our analysis found less suitable stay so.** Six reach no robust design at any $C_F$: OPA846, OPA847, ADA4895-1, OPA657, LMH6624 and THS4021. Two verdicts change in detail. LMH6624's macromodel follows its datasheet's closed-loop curve better than its plotted open-loop phase does and is far more stable than our analytical model, but it still reaches no robust design (29° worst case). Uncompensated AD8099 has a robust window in its model (202 MHz, 5.1 dB) where our analysis found none. OPA847's model fails its own datasheet's test circuit by 42 % in bandwidth, so this cross-check says nothing reliable about OPA847.
- **The JFET-input OPA817 and OPA814 confirm Table A2.4**: robust only below 100 MHz, with 13.7–14.9 dB of noise penalty.

**What SPICE cannot settle.** Each of these needs a measurement (Section 9.7):
- the input capacitance of LMH6629 (5.7 or 1.3 pF) and of ADA4899-1 (4.4 or 0.40 pF);
- the high-frequency current noise of the FET parts: the OPA818 model adds one, and the OPA858 and OPA859 models have none;
- OPA847's high-frequency current noise: its model gives 10.8 pA/√Hz at 100 MHz, about four times the datasheet's 2.5 pA/√Hz, which is plotted only to 10 MHz;
- OPA955's production performance;
- board parasitics at 1–5 GHz, which set variant A's gain margin;
- unit-to-unit spread."""

TABLE_A54 = r"""**How Table A5.4 is read.**
- **The two-port column reproduces SPICE**: to 0.1° of phase margin, 0.1 dB of gain margin and 1 % of bandwidth for the thirteen designs of the first seven amplifiers, and the noise to 0.3 %. The closed-loop simulation therefore holds nothing that Eqs. (13), (23) and (45) and the quantities of Table A5.2 do not.
  - For the further amplifiers of Section 6.5 the agreement is within 0.3°, 0.1 dB, 1.4 % and 1.5 %, with one exception, OPA847: 4.0°, 1.3 dB and 9 %. Its output couples back to its inverting input (Table A5.2), which Eq. (45) leaves out.
- **Our method differs from it by method alone**: one open-loop curve and a pure input capacitance, with the same model's numbers.
  - The phase margin moves by at most 1.8° for OPA855, OPA818, OPA858 and OPA859. It moves by 6.4° for LMH6629, whose $A_-$ and $A_+$ part by 7° at 1 GHz, near its 801-MHz crossover (Table A5.3), and by 2.6° for OPA856 and 3.1° for OPA846, whose two gains differ by only 5° and 0° even at 1 GHz, far above their 208-MHz and 308-MHz crossovers; the input admittance and the loaded output impedance of Eq. (45) account for the rest. For OPA955 our method is 9° optimistic: its gain from the inverting input has 10–18° more lag than from the non-inverting input at 1–3 GHz (Table A5.3).
  - The bandwidth moves by at most 6 % for the first seven amplifiers.
  - The gain margin is 4.6–4.9 dB optimistic for OPA855, 6.0–7.0 dB for OPA818, 4.1 dB for OPA858 and 5.4 dB for LMH6629. The cause is $A_-$ against $A_+$ above 2 GHz and the loaded output impedance.
- **Every difference between our analysis and SPICE in Sections 5.5–5.7 is therefore a difference of parameters**, datasheet against macromodel, except these gain-margin offsets and the phase-margin offsets of LMH6629 (6.4°) and OPA955 (9°)."""

READING_A55 = r"""**Reading Table A5.5.** The phase margins of the last column, Eq. (46) with the macromodel's quantities, agree with SPICE within 2.3° for the first seven parts, and for the further amplifiers within 0.5° except OPA847 (19.4° against 33.3°; its output couples back to its input), ADA4817-1 (53.3° against 49.2°) and ADA4899-1 (60.0° against 55.5°). Eq. (46) does not reproduce the closed-loop peaking where the response extends to several gigahertz (OPA855, OPA859): there the signal also passes from input to output through the feedback network, which Eq. (46) leaves out. Across these circuits the macromodels reproduce the stated margins of OPA855, OPA818, OPA858 and OPA859 within 4°, and LMH6629's stated bandwidth within 8 %. Two verdicts change a design conclusion: OPA818's, whose test circuit crosses over where variant B's TIA does, and OPA858's, which settles the conflict in its datasheet; the others say which description to trust for each part. Part by part:"""

FIXES = [
    # opening and Section 5.1
    ("span", "Our analytical model rests on each amplifier's datasheet open-loop curve and on the hand model of Chapter 4.",
     "the closed-loop test circuit printed in each datasheet (Section 5.4).", OPENING),
    ("span", "### 5.1 What the cross-check found", "with 13.7–14.9 dB of noise penalty.", SECTION_51),
    # Section 5.2
    ("replace", "Section 6.2.8 makes the same point for peaking that is equalized later.",
     "Figure 11 (Section 6.2.7) shows the same for OPA818 and OPA846, whose responses are flat at 32–34° of phase margin."),
    ("replace",
     "In a TIA, $Z_1$ is the amplifier's output impedance in parallel with its load: 4–37 Ω in these models (Table A5.2). $Z_2$ is the feedback network: kilohms in band, but only about 100 Ω at 5 GHz, where $C_F$ and $C_T$ in series are nearly a short (0.25 pF in series with 2.2 pF is 140 Ω there). A single voltage injection is therefore accurate at crossover and wrong at the gain-margin frequency.",
     "In a TIA, $Z_1$ is the amplifier's output impedance, 4–37 Ω in these models (Table A5.2), in parallel with its load. $Z_2$ is the feedback network: kilohms in band, but only about 140 Ω at 5 GHz, where $C_F$ and $C_T$ in series are a low impedance (0.25 pF in series with 2.2 pF). A single voltage injection is therefore accurate at crossover, but at the gain-margin frequency only where $Z_1 \\ll Z_2$ still holds: for variant A it gives the same gain margins as the double injection, and for OPA856 it is 18.5 dB off (Table A5.1)."),
    ("delete", "The original paper [S2] was not available for this note", "the derivation above stands on its own."),
    ("replace", "The publisher's copy was not available for this note; Section 5.2 derives the combination formula independently.",
     "Section 5.2 derives the combination formula in full."),
    ("replace",
     "Between $f_c$ and $f_{180}$ = 3.5 GHz the loop gain stays between −2.1 and 0 dB, on the plateau of $A_-$ (Figure 4a), so the gain margin is only 1.9 dB.",
     "Between $f_c$ and $f_{180}$ = 3.5 GHz, the frequency at which the loop phase reaches −180° (Section 5.5), the loop gain stays between −2.1 and 0 dB, on the plateau of $A_-$, the open-loop gain from the inverting input (Section 5.3, Figure 4a), so the gain margin is only 1.9 dB."),
    # Section 5.3
    ("replace", "(none does in the first seven models; OPA847's does, Section 6.5)",
     "(none does in the first seven models; OPA847's does, as noted below)"),
    ("replace", "whose 2011 model carries 4.8 mA against 12.6 mA. This affects nothing small-signal.",
     "whose 2011 model carries 4.8 mA against 12.6 mA. The supply current does not enter the quantities measured here, but a model biased this differently may not describe the part, and Section 5.4 finds it peaking less than the datasheet's measured response (Appendix C, item 18)."),
    ("replace",
     "- **The two inputs.** $A_-$ and $A_+$ agree within 0.3 dB and 7° up to 1 GHz for every model, so the phase margins do not depend on which input a curve describes. At 3 GHz they differ by 0.7–1.9 dB and 13–21° for the three Green-Williams-Lis models and LMH6629, and by more above. The gain margins do depend on it.",
     "- **The two inputs.** For the first seven models $A_-$ and $A_+$ agree within 0.3 dB and 7° up to 1 GHz, so their phase margins depend on which input a curve describes by a few degrees at most, most for LMH6629, whose two gains part by 7° at 1 GHz, near its 801-MHz crossover. OPA955 differs by 0.5 dB and 10° at 1 GHz, OPA657 by 10° and OPA847 by 0.4 dB. At 3 GHz the gains of OPA855, OPA818, OPA856 and LMH6629 differ by 0.7–1.9 dB and 13–21°, and by more above, so the gain margins do depend on it."),
    ("span", "**How Table A5.4 is read.**", "except these gain-margin offsets.", TABLE_A54),
    # Section 5.4: the cautions first, then the reading
    ("replace", "Across the seven circuits it lies at 1–3 GHz, close enough to the 240–1250 MHz crossovers",
     "Across the five circuits of the first seven parts that have gain-setting resistors (OPA856 and OPA859 are tested as buffers) it lies at 1–3 GHz, close enough to their 240–1250 MHz crossovers"),
    ("move", "Two cautions apply.", "comes on top.", "**Reading Table A5.5.**", "before"),
    ("replace", "The TI Green-Williams-Lis models are fitted to the datasheet's closed-loop gain and phase (Table B.1)",
     "The models of OPA855, OPA818, OPA856 and OPA955 (TI's Green-Williams-Lis macromodels, Table B.1) are fitted to the datasheet's closed-loop gain and phase"),
    ("replace", "including the ±1.5 dB of open-loop gain used in Section 6.2.8, comes on top.",
     "including the spread of open-loop gain used in Section 6.2.8 (+1.5 dB, and down to the datasheet minimum GBW or −2 dB), comes on top."),
    ("paragraph", "**Reading Table A5.5.** The phase margins of the last column agree with SPICE within 2.3°.", READING_A55),
    ("replace", "- **OPA818: the macromodel is right and the curve is not.**",
     "- **OPA818: the curve is inconsistent with the datasheet's own closed-loop data, and the macromodel, fitted to that data, reproduces it.**"),
    ("replace", "A two-pole loop with 1.4 dB of peaking has about 51° of margin, which is what SPICE gives (54°).",
     r"A two-pole loop with 1.4 dB of peaking has about 51° of margin, close to the 54° that SPICE gives: its damping ratio $\zeta$ follows from the peak $M_p = 1/(2\zeta\sqrt{1-\zeta^2})$, and its phase margin from $\mathrm{PM} = \arctan\left(2\zeta/\sqrt{\sqrt{1+4\zeta^4}-2\zeta^2}\right)$; $M_p = 10^{1.4/20}$ = 1.175 gives $\zeta$ = 0.487 and PM = 51°."),
    ("replace", "so the macromodel's TIA margins are the credible ones for variant B.",
     "so the macromodel's TIA margins are the more credible ones for variant B until the first board settles them (Appendix C, item 16)."),
    ("replace", "The macromodel gives 1.4 dB (optimistic by about 10° of margin); the curve with $C_{\\mathrm{in}}$ gives 5.6 dB (pessimistic).",
     "The macromodel gives 1.4 dB, optimistic by about 10° of margin: by the same relations the measured 3.1 dB ($M_p$ = 1.429) means $\\zeta$ = 0.378 and about 41°, against about 51° for 1.4 dB. The curve with $C_{\\mathrm{in}}$ gives 5.6 dB (pessimistic)."),
    # Section 5.5
    ("span", "- **What it means for the design.** The scan below (Tables A5.8 and A5.9) shows", "$R_F$'s own parasitics at gigahertz.",
     "- **The scan below finds how far $C_F$ may move before this margin falls under 3 dB** (Tables A5.8 and A5.9)."),
    ("replace",
     "- **Consequences.** In the vendor's model, variant B needs no equalizer at $C_F$ = 0.55–0.65 pF. The scan below (Table A5.10) shows what a smaller $C_F$ buys: 15–37 % more bandwidth at 1 pF and 2 kΩ, if 40° is enough or $C_F$ is trimmed to ±0.05 pF.",
     "- **Consequences.** In the vendor's model, variant B needs no equalizer at $C_F$ = 0.55–0.65 pF; the scan below shows what a smaller $C_F$ buys (Table A5.10)."),
    ("replace", "required at all three photodiode capacitances: phase margin ≥ 45°, gain margin ≥ 3 dB, and peaking ≤ 1 dB.",
     "required at all three photodiode capacitances: phase margin ≥ 45°, gain margin ≥ 3 dB, and peaking ≤ 1 dB. For variant B, whose gain margin is 14–19 dB everywhere, Table A5.10 asks for the phase margin alone, at 45° or 40°; its 40° designs peak by up to 1.53 dB at a corner, more than the 1 dB of variant A's window."),
    ("replace",
     "- **Our analytical model's upper edges lie 0.04–0.07 pF higher.** They sit at the second crossing of the plotted 4–7 GHz bump, close to the minimum-gain rule.",
     "- **Our analytical model's upper edges lie 0.04–0.07 pF higher.** They sit at the second crossing of the plotted 4–7 GHz bump, close to the minimum-gain rule.\n- **The corners that our analysis flags are those that lose gain margin here.** The macromodel has no 4–7 GHz bump but loses margin at the same corners, at about 3.4 GHz, through the plateau of $A_-$, so the flags of Table A8.11 mark a real loss of margin. How large that loss is on a board depends on parasitics no model here contains: the output pin, the feedback pads and $R_F$'s own parasitics at gigahertz."),
    ("replace",
     "- **The present designs are the 45°, ±0.1-pF designs** (Figure 6). At 1 pF and 2 kΩ the scan returns 0.55 pF, the value of Table A8.11. At 2 pF it returns 0.57 and 0.69 pF against the present 0.55 and 0.65 pF.",
     "- **At 1 pF and 2 kΩ the design of Table A8.11 is the 45°, ±0.1-pF design** (Figure 6): the scan returns 0.55 pF, the value of that table. At 2 pF the 45°, ±0.1-pF designs are 0.57 and 0.69 pF, 0.02–0.04 pF above the 0.55 and 0.65 pF of Table A8.11, which keep 44.3° and 43.4° at their worst corner (Table A5.6)."),
    ("replace", "  - At 1 pF and 2 kΩ, against 226 MHz now:", "  - At 1 pF and 2 kΩ, against the 226 MHz of the design of Table A8.11:"),
    ("replace", "Open circles mark the present designs (Table A8.11)", "Open circles mark the designs of Table A8.11"),
    ("replace", "the trade that $C_F$ sets, with the present designs marked;", "the trade that $C_F$ sets, with the designs of Table A8.11 marked;"),
    ("replace", "Below about 0.35 pF the bandwidth stops rising while the peaking grows, to 10.8–14.5 dB at 0.15 pF:",
     "Below about 0.35 pF the bandwidth stops rising while the peaking, largest over the three photodiode capacitances, grows to 10.8–14.5 dB at 0.15 pF:"),
    ("replace", "**Other parts.**\n",
     "**Other parts.** For the other five of the first seven, SPICE moves the margins in the direction that Sections 5.3 and 5.4 explain; the ranges are over the nine corners.\n"),
    ("replace",
     "- **OPA858**: its margin collapses at the low-$C_F$ corner (33° at 0.15 pF). It needs the larger $C_F$ or the added capacitance that Section 6.2.3 already recommended for the calibrated curve.",
     "- **OPA858**: its margin collapses at the low-$C_F$ corner (33° at 0.15 pF). In SPICE its window at 1 pF and 2 kΩ is 0.225–1.153 pF, and its best design, 0.280 ± 0.050 pF, keeps 45.9° at 446 MHz (Table A6.32); the alternative is the added input capacitance that Section 6.2.3 recommends for the calibrated curve."),
    # Section 5.6
    ("replace", "- **OPA855 and OPA856 agree within 2 % and 0.2 dB.**",
     "- **OPA855 and OPA856 agree within 2.5 % and 0.2 dB**: within 2 % from 10 MHz up, and 2.4 % at 1 MHz."),
    ("replace", "OPA855 agrees within 2 %.", "OPA855 agrees within 2 % from 10 MHz up (2.4 % at 1 MHz)."),
    ("replace",
     "- **OPA855 (variant A) is the only one of the seven with all three at once**: under 3.5 dB of penalty (3.02 dB), more than 45° at the worst corner (48.7°) and more than 200 MHz (431 MHz).",
     "- **Four designs meet both requirements of this note, 45° at the worst corner and 150 MHz**: OPA855 (3.02 dB, 48.7°, 431 MHz), OPA856 (3.27 dB, 50.0°, 184 MHz), OPA859 (5.91 dB, 49.7°, 196 MHz) and OPA818 (7.95 dB, 45.4°, 226 MHz). OPA855 is the quietest of them and has 1.9 times the bandwidth of the next, OPA818 (431 against 226 MHz)."),
    ("replace",
     "- **OPA818 (variant B) is the noisiest in the dark (7.95 dB) at 45.4° and 226 MHz.** Its case rests on the larger output swing of Table A6.28, which a dark-noise penalty does not show.",
     "- **OPA818's case (variant B) rests on the larger output swing of Table A6.28**, which a dark-noise penalty does not show."),
    # Section 5.7
    ("replace", " Each run takes 0.3 s.", ""),
    # Section 5.8
    ("replace", "The 1-pF photodiode of our baseline (5.15 pF in total) gives only 5.1–5.2 pA/√Hz in both.",
     "The baseline's total node capacitance of 5.15 pF (1-pF photodiode, 0.35 pF of board and the datasheet's 3.8 pF) gives only 5.1–5.2 pA/√Hz in both; in SPICE that total includes the model's 3.07 pF."),
    ("replace", "our analytical model gives 2° and +30 dB at 115–135 MHz.", "our analytical model gives 2° and +30 dB at 123 MHz."),
    ("replace", "A 10-MHz reading near 6.7 pA/√Hz would still point to an instrument floor instead (Section 4.10).",
     "A 10-MHz reading near 6.7–7.4 pA/√Hz would still point to an instrument floor instead (Section 4.10)."),
    # Section 5.9
    ("span", "### 5.9 What the cross-check changes in our analysis, and what it leaves open", "lists the measurements.", SECTION_59),
]
