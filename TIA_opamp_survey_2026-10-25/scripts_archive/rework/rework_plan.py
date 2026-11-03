"""Plan of the narrative rework of the survey report (27 Oct 2026), read by rework_narrative.py.

The new order follows the design as it was worked out: what we are designing (Chapter 1), the
approaches and the 50-ohm benchmark (2), a first op-amp TIA worked through (3), the theory (4), the
SPICE cross-check (5), the op amps compared in charts (6), composite front ends (7), the proposed
front end with its DC handling (8), conclusions (9); the tables go to Appendix A, the SPICE how-to to
Appendix B, and the old appendices 1-4 become C-F.  All old content is kept; PLAN lists every old
block once (or in two ranges), with its new heading, the hand edits it needs, and the new text
around it.  Reference conventions are those of rework_narrative.py: in new text every section,
chapter and appendix is written in the new numbering between U+27E6/U+27E7 brackets, existing
equations, tables and figures by their old numbers, and new ones as [[E:key]], [[F:key]], and
'*Table Nk.' captions.
"""
import re

L, R = "⟦", "⟧"


def T(text):
    return ("text", text)


def B(key, heading, **opts):
    return ("block", key, heading, opts)


KEEP_INLINE = {"1.1": "1.1", "0.2": "3.1", "8.0": "9.1"}
FIXED_TABLES = {"10.1": "B.1", "10.2": "B.2", "A2.1": "D.1", "A2.2": "D.2", "A2.3": "D.3", "A2.4": "D.4",
                "A3.1": "E.1"}
APPENDIX_MAP = {"1": "C", "2": "D", "3": "E", "4": "F"}
DROP = {"front", "ch0", "ch1", "ch3", "ch4", "ch6", "ch7", "ch8", "ch11"}
APPENDIX_A_MARKER = "<<APPENDIX_A_TABLES>>"

S = "Section"
SECTION_MAP = {
    "0.1": (S, "9.1"), "0.2": ("Chapter", "3"), "0.3": (S, "9.6"), "0.4": (S, "9.9"), "0.5": (S, "9.12"),
    "0.6": (S, "9.2"), "0.7": (S, "9.3"),
    "1.1": (S, "1.1"), "1.2": (S, "1.3"), "1.3": (S, "1.4"), "1.4": (S, "1.5"), "1.5": (S, "1.2"),
    "2.1": (S, "4.1"), "2.2": (S, "4.2"), "2.3": (S, "4.3"), "2.4": (S, "4.4"), "2.5": (S, "4.5"),
    "2.6": (S, "4.6"), "2.7": (S, "4.7"), "2.8": (S, "4.8"),
    "3.1": (S, "2.2"), "3.2": (S, "6.1.1"), "3.3": (S, "2.3"), "3.4": (S, "2.4"), "3.5": (S, "2.5"),
    "3.6": (S, "6.1.2"),
    "4.1": (S, "4.9"), "4.2": (S, "6.2.1"), "4.3": (S, "6.2.2"), "4.4": (S, "6.2.3"), "4.5": (S, "6.2.4"),
    "4.6": (S, "6.2.5"), "4.7": (S, "6.2.6"), "4.8": (S, "6.2.7"), "4.9": (S, "6.2.8"),
    "5.1": (S, "6.3.1"), "5.2": (S, "6.3.2"), "5.3": (S, "6.3.3"), "5.4": (S, "6.3.4"), "5.5": (S, "4.10"),
    "6.1": (S, "6.4.1"), "6.2": (S, "6.4.2"), "6.3": (S, "6.4.3"), "6.4": (S, "6.4.4"),
    "7.1": (S, "8.1"), "7.2": (S, "8.2"), "7.3": (S, "8.3"), "7.4": (S, "8.4"), "7.5": (S, "8.5"),
    "7.6": (S, "2.1"), "7.7": (S, "2.5"), "7.8": (S, "8.6"), "7.9": (S, "8.7"), "7.10": (S, "8.8"),
    "7.11": (S, "8.9"), "7.12": (S, "8.11"),
    "8.1": (S, "9.7"), "8.2": (S, "9.8"), "8.3": (S, "8.10"), "8.4": (S, "9.10"), "8.5": (S, "9.11"),
    "10.1": (S, "5.1"), "10.2": ("Appendix", "B.1"), "10.3": (S, "5.2"), "10.4": (S, "5.3"), "10.5": (S, "5.4"),
    "10.6": (S, "5.5"), "10.7": (S, "5.6"), "10.8": (S, "5.7"), "10.9": (S, "5.8"), "10.10": (S, "6.5"),
    "10.11": (S, "5.9"), "10.12": ("Appendix", "B.2"),
    "11.1": (S, "6.6.1"), "11.2": (S, "6.6.2"), "11.3": (S, "6.6.3"), "11.4": (S, "6.7"), "11.5": (S, "7.1"),
    "11.6": (S, "7.2"), "11.7": (S, "7.3"), "11.8": (S, "9.4"),
}

CHAPTER_TITLES = {"1": "What we are designing", "2": "The approaches, and the 50-Ω benchmark",
                  "3": "A first op-amp TIA, worked through", "4": "TIA theory",
                  "5": "SPICE cross-check with the vendors' macromodels", "6": "The op amps compared",
                  "7": "Composite front ends", "8": "The proposed front end",
                  "9": "Conclusions and recommendations"}

EXPECTED_FIGS = {"1": 1, "4": 2, "7": 3, "8": 4, "9": 5, "10": 6, "11": 7, "12": 8, "13": 9, "new:bw": 10,
                 "3": 11, "5": 12, "new:noise": 13, "2": 14, "new:dr": 15, "6": 16, "14": 17, "15": 18,
                 "16": 19, "new:bench": 20}


def skip_eq_spans(text):
    """The reference list: its equation numbers belong to the cited papers."""
    a = text.find("## Appendix D. References")
    if a >= 0:
        b = text.find("## Appendix E.", a)
        yield (a, b if b >= 0 else len(text))


# Self-references of the old text, in the first-person plural of the narrative.  Specific phrases
# first, then the general forms.
VOICE = [
    (r"\bthe highest dynamic range of the survey\b", "the highest dynamic range of all the candidates"),
    (r"\bHighest dynamic range of the survey\b", "Highest dynamic range of all the candidates"),
    (r"\bIts survey entries\b", "Its entries"),
    (r"\bThe parts this survey ranked\b", "The parts we ranked"),
    (r"\bso this survey reports both views\b", "so we report both views"),
    (r"\bThe survey reports a range\b", "We report a range"),
    (r"\bThis survey uses\b", "We use"),
    (r"\bare this survey's estimates\b", "are our estimates"),
    (r"\bThe designs are those of the survey:", "The designs are those chosen with our analytical model:"),
    (r"\bthe difference between the survey's and SPICE's phase margins\b",
     "the difference between the analytical and the SPICE phase margins"),
    (r"\ban asterisk marks the survey's second crossing\b", "an asterisk marks a second crossing in our analysis"),
    (r"\bThe 1-pF photodiode of the survey\b", "The 1-pF photodiode of our baseline"),
    (r"\bthe survey's 1-pF photodiode on this board\b", "our 1-pF baseline photodiode on this board"),
    (r"\bis the survey's part that fits\b", "is the part among our candidates that fits"),
    (r"\bThe survey method differs\b", "Our method differs"),
    (r"\bfor the baseline of this survey\b", "for our baseline"),
    (r"\bThe survey chose\b", "We chose"),
    (r"\bthe survey's(?=[.,;:)])", "ours"),
    (r"\bthe survey's model\b", "our analytical model"),
    (r"\bThe survey's model\b", "Our analytical model"),
    (r"\bthe survey model's\b", "our analytical model's"),
    (r"\bThe survey model's\b", "Our analytical model's"),
    (r"\bthe survey model\b", "our analytical model"),
    (r"\bThe survey model\b", "Our analytical model"),
    (r"\bsurvey's model\b", "analytical model"),
    (r"\bsurvey model\b", "analytical model"),
    (r"\bSurvey model\b", "Analytical model"),
    (r"\bsurvey central\b", "analytical central"),
    (r"\bSurvey method\b", "Analytical method"),
    (r"\bSurvey noise\b", "Analytical noise"),
    (r"\bSurvey:", "Analytical:"),
    (r"\bSurvey \$", "Analytical $"),
    (r"\bthe survey's equations\b", "our equations"),
    (r"\bThe survey's equations\b", "Our equations"),
    (r"\bthis survey's\b", "this note's"),
    (r"\bthis survey\b", "this note"),
    (r"\bThis survey\b", "This note"),
    (r"\bthe survey's\b", "our"),
    (r"\bThe survey's\b", "Our"),
    (r"\bthe survey\b", "our analysis"),
    (r"\bThe survey\b", "Our analysis"),
]

GLOBAL_REPLACE = []

# ---------------------------------------------------------------------------------------------- text
FRONT = r"""
# Operational amplifiers for a balanced-photodiode transimpedance amplifier: 1 pF, 1.5–2 kΩ, ≥ 150 MHz, 0.1–10 mA of DC photocurrent

Design study and amplifier survey, 25 October 2026, revised 26 and 27 October 2026.

We are designing the front end of a balanced optical receiver: a pair of photodiodes with 1 pF in total at the summing node, a transimpedance of 1.5–2 kΩ, at least 150 MHz of bandwidth, and 0.1–10 mA of DC photocurrent with a small RF signal on top. The aim is the widest dynamic range. This note follows the design in the order in which we worked it out. ⟦Chapter 1⟧ states the problem and why the DC photocurrent shapes it. ⟦Chapter 2⟧ looks at the approaches: a plain 50-Ω termination followed by an RF amplifier, which sets the benchmark every design must beat; the op-amp TIA and how we chose its candidates; single-chip TIAs; and composite front ends. ⟦Chapter 3⟧ works the most promising simple design, OPA855 at 2 kΩ, through four bench-unit equations and sets it against the benchmark. ⟦Chapter 4⟧ derives the theory behind those equations and checks it against the datasheets and a bench measurement, and ⟦Chapter 5⟧ checks it against the manufacturers' SPICE macromodels. ⟦Chapter 6⟧ compares every candidate in charts, in bandwidth and stability, noise and dynamic range, and then the leading designs in SPICE, the single-chip TIAs and the benchmark. ⟦Chapter 7⟧ asks what a discrete transistor at the summing node or a high-voltage stage inside the loop adds. ⟦Chapter 8⟧ handles the DC photocurrent and gives the proposed front end in two variants with starting component values, and ⟦Chapter 9⟧ collects the conclusions and the ranked picks. The tables behind the charts are in ⟦Appendix A⟧; ⟦Appendix B⟧ explains how to run the SPICE checks from a script, and ⟦Appendices C–F⟧ hold the open questions, the references, the files and the datasheet inconsistencies.
"""

CH1 = r"""
## 1. What we are designing

The receiver needs a front end that turns the RF difference current of a balanced photodiode pair into a voltage with as little added noise and as much headroom as possible. This chapter states the question and the conditions (⟦Section 1.1⟧), explains what the photocurrent figures mean for a balanced pair (⟦Section 1.2⟧), shows the circuit (⟦Section 1.3⟧), and lists the assumed values and the conventions used throughout (⟦Sections 1.4 and 1.5⟧).
"""

CONVENTION_DR = r"""- "Shot-noise clearance" at a DC photocurrent is the ratio, in dB, of the photocurrent shot-noise density to all other noise densities at the same frequency.
- "Dynamic range" is the electronic dynamic range of Eq. (25) unless it is called usable. The electronic figure assumes that the light can supply any tone up to the TIA's ceiling; the usable figure of Eq. (⟦E:optical⟧) also caps the tone at $I_{\mathrm{DC}}/\sqrt2$ rms, the most the light can supply (⟦Section 4.8⟧)."""

STATUS = r"""**Status of every number.** Every phase margin, bandwidth and noise figure in this note is an **analytical estimate**, closed-form theory plus each amplifier's datasheet open-loop curve, unless it is labelled SPICE. The SPICE numbers come from the manufacturers' macromodels: ⟦Chapter 5⟧ checks the analytical estimates against them, and ⟦Sections 6.5–6.6⟧, ⟦Section 6.8⟧ and ⟦Chapter 7⟧ use them directly. ⟦Section 9.13⟧ lists the cases where only a simulation or a measurement can settle the answer."""

CH2 = r"""
## 2. The approaches, and the 50-Ω benchmark

Three kinds of front end can turn the difference current of the pair into a voltage at 150–200 MHz, and we look at each before choosing. The simplest needs no feedback at all: the pair terminated in 50 Ω and followed by an RF amplifier (⟦Section 2.1⟧). It is easy to build, has gigahertz of bandwidth and no swing limit at the photodiodes, and it sets the benchmark that every other design in this note has to beat. The second is the inverting op-amp TIA of Figure 1, built around a commercial voltage-feedback amplifier. Most of this note is about choosing that amplifier, and ⟦Sections 2.2–2.4⟧ explain how we found and screened the candidates. The third is a single-chip TIA, made for lidar or for coherent receivers (⟦Section 2.5⟧). Two refinements of the op-amp TIA, composite front ends with a discrete transistor at the summing node or a high-voltage stage inside the loop, and the circuits that keep the DC photocurrent out of the feedback resistor, are introduced in ⟦Section 2.6⟧ and treated in ⟦Chapters 7 and 8⟧.
"""

BENCH_INTRO = r"""The oldest front end needs no transimpedance amplifier: the photodiode pair is terminated in $R_0$ = 50 Ω at the summing node, a bias tee carries the DC, and an RF low-noise amplifier, or a 50-Ω instrument, follows. It has gigahertz of bandwidth and no swing limit at the photodiodes, and at high photocurrent it is competitive. In the list of ways to remove a large DC current it is Option E (⟦Section 8.1⟧). We use it as the benchmark for every design in this note: a TIA is worth building only where it beats this chain, and this section states what that takes.

**The chain.** We take the termination in parallel with the amplifier's matched input, so the photocurrent sees $R_0/2$ = 25 Ω, and the termination is the 50-Ω source to which the amplifier's noise figure refers. An rms photocurrent $I$ at the tone then delivers to the amplifier the power $(IR_0/2)^2/R_0 = I^2R_0/4$. The amplifier's input noise, referred to its 50-Ω source, is the available power $Fk_BT$ per hertz, the source's own $k_BT$ and the amplifier's $(F-1)k_BT$, with $F = 10^{\mathrm{NF}/10}$ its noise factor, $k_B$ Boltzmann's constant and $T$ = 298.15 K. Setting $I^2R_0/4$ per hertz equal to $Fk_BT$ gives the noise density referred to the photocurrent:

$$
P = \frac{I^2R_0}{4},
\qquad
S_{50} = \frac{4Fk_BT}{R_0}.
\tag{⟦E:bench-noise⟧}
$$

With a noiseless amplifier ($F$ = 1) this is the Johnson noise of 50 Ω, $\sqrt{4\times1.381\times10^{-23}\ \mathrm{J/K}\times298.15\ \mathrm{K}/50\ \Omega}$ = 18.15 pA/√Hz. With NF = 2 dB ($F$ = 1.585) it is $\sqrt{1.585}\times18.15$ = 22.85 pA/√Hz, and over $B$ = 150 MHz it integrates to $22.85\ \mathrm{pA/\sqrt{Hz}}\times\sqrt{1.5\times10^{8}\ \mathrm{Hz}}$ = 279.8 nA rms. Against the Johnson noise $4k_BT/R_F$ of the feedback resistor the chain is noisier by $10\log_{10}(FR_F/R_0)$: 18.0 dB at 2 kΩ and 16.8 dB at 1.5 kΩ."""

BENCH_NOISE = r"""**Noise against shot noise.** The chain's noise $S_{50}$ equals the shot noise $2qI_{\mathrm{DC}}$ of the pair at"""

BENCH_REST = r"""**Ceiling and dynamic range.** The amplifier's input compresses at a power $P_{\max}$: its input-referred 1-dB compression point, or the level at which its distortion reaches what the receiver tolerates. By Eq. (⟦E:bench-noise⟧) the largest undistorted rms photocurrent, and the dynamic range in the noise bandwidth $B$ with the shot noise of $I_{\mathrm{DC}} = I_1 + I_2$ included, are

$$
I_{\max,50} = 2\sqrt{\frac{P_{\max}}{R_0}},
\qquad
\mathrm{DR}_{50} = 20\log_{10}\frac{I_{\max,50}}{\sqrt{\left(S_{50} + 2qI_{\mathrm{DC}}\right)B}}.
\tag{⟦E:bench-ceiling⟧}
$$

In the dark the second form reduces to the dynamic range of any RF receiver, $10\log_{10}[P_{\max}/(Fk_BTB)]$:

$$
\mathrm{DR}_{50}\big|_{I_{\mathrm{DC}}=0} = P_{\max}[\mathrm{dBm}] - \mathrm{NF}[\mathrm{dB}] + 173.9 - 10\log_{10}B[\mathrm{Hz}]
= P_{\max}[\mathrm{dBm}] - \mathrm{NF}[\mathrm{dB}] + 92.1\ \mathrm{dB},
\tag{⟦E:bench-dark⟧}
$$

where 173.9 dB is $-10\log_{10}[k_BT/(1\ \mathrm{mW}\cdot1\ \mathrm{s})]$ at 25 °C and $10\log_{10}(1.5\times10^{8})$ = 81.8 dB.

We do not tie the benchmark to one amplifier. We take NF = 2 dB, which good 50-Ω low-noise amplifiers reach at 100 MHz, and three input compression levels, $P_{\max}$ = −20, −10 and 0 dBm; Table N1 gives the family. At −10 dBm, for example, $I_{\max,50} = 2\sqrt{10^{-4}\ \mathrm{W}/50\ \Omega}$ = 2.83 mA rms, and Eq. (⟦E:bench-dark⟧) gives −10 − 2 + 92.1 = 80.1 dB in the dark. With 1 mA of photocurrent the shot noise adds $\sqrt{2qI_{\mathrm{DC}}B}$ = 219.2 nA rms to the 279.8 nA, in power, and the dynamic range falls to $20\log_{10}(2.83\ \mathrm{mA}/355.5\ \mathrm{nA})$ = 78.0 dB.

*Table N1. The 50-Ω benchmark family: the photodiode pair terminated in 50 Ω in parallel with the 50-Ω input of an amplifier of 2 dB noise figure, whose input compresses at $P_{\max}$. Noise 22.85 pA/√Hz, 279.8 nA rms in 150 MHz in the dark; dynamic range in 150 MHz (Eq. (⟦E:bench-ceiling⟧)); "usable" caps the tone at $I_{\mathrm{DC}}/\sqrt2$ rms (Eq. (⟦E:optical⟧)). No op amp.*

| $P_{\max}$ (input) | $I_{\max,50}$ (mA rms) | Fully modulated light passes up to $I_1 + I_2$ (mA) | Electronic dynamic range at $I_1 + I_2$ = 0 / 0.1 / 1 / 10 / 20 mA (dB) | Usable dynamic range at 0.1 / 1 / 10 / 20 mA (dB) |
|---|---|---|---|---|
| −20 dBm | 0.894 | 1.26 | 70.1 / 69.8 / 68.0 / 61.6 / 58.9 | 47.8 / 66.0 / 61.6 / 58.9 |
| −10 dBm | 2.83 | 4.00 | 80.1 / 79.8 / 78.0 / 71.6 / 68.9 | 47.8 / 66.0 / 71.6 / 68.9 |
| 0 dBm | 8.94 | 12.6 | 90.1 / 89.8 / 88.0 / 81.6 / 78.9 | 47.8 / 66.0 / 79.5 / 78.9 |

**What the light can supply.** Eq. (⟦E:bench-ceiling⟧) gives an electronic dynamic range: it assumes that the light can drive a tone up to the amplifier's ceiling. In a balanced pair the light cannot drive a tone larger than $I_{\mathrm{DC}}/\sqrt2$ rms, the optical limit of Eq. (⟦E:optical⟧) (⟦Section 4.8⟧). Below $I_{\mathrm{DC}} = \sqrt2\,I_{\max,50}$, which is 1.26, 4.0 and 12.6 mA for the three compression levels, no light can drive the chain into compression, and its usable dynamic range is the same whatever $P_{\max}$ is: 47.8 dB at 0.1 mA and 66.0 dB at 1 mA. A higher compression level helps only above that photocurrent.

**What a TIA must do to beat it.** For the same signal a TIA beats the chain where its band noise is lower, where its ceiling is higher, or both. Three comparisons settle where that is.

*Small signal.* For the same small tone, the TIA's signal-to-noise ratio exceeds the chain's by the ratio of the band noises, $A = 20\log_{10}(i_{n,B,50}/i_{n,B})$, with $i_{n,B,50} = \sqrt{(S_{50} + 2qI_{\mathrm{DC}})B}$ for the chain and $i_{n,B}$ of Eq. (56) for the TIA. Both carry the same shot noise, so $A$ is positive whenever the TIA's own band noise is below the chain's, $\int_0^B S_{i,0}\,df < S_{50}B$, which for NF = 2 dB means less than 22.85 pA/√Hz on average over the band. Every design we carry forward meets that, by 6.2 dB (the high-voltage composite of ⟦Section 7.2⟧) to 17.7 dB in the dark, and $A$ shrinks toward zero as the shot noise takes over. The receiver of ⟦Section 1.1⟧, a small RF signal on 0.1–10 mA, is in this regime.

*Electronic dynamic range.* The TIA's ceiling $I_{\max}$ equals the chain's when the chain compresses at $P_{\mathrm{eq}}$, and their electronic dynamic ranges are equal when it compresses at $P_x$:

$$
P_{\mathrm{eq}} = \frac{R_0}{4}\,I_{\max}^2,
\qquad
P_x\,[\mathrm{dBm}] = P_{\mathrm{eq}}\,[\mathrm{dBm}] + A\,[\mathrm{dB}].
\tag{⟦E:bench-px⟧}
$$

The second form follows from Eq. (⟦E:bench-ceiling⟧): equal dynamic ranges need $I_{\max,50}/i_{n,B,50} = I_{\max}/i_{n,B}$, i.e. $I_{\max,50} = I_{\max}\,10^{A/20}$, and since the power goes as the square of the current that is $A$ decibels more power than $P_{\mathrm{eq}}$. A chain that compresses above $P_x$ has the larger electronic dynamic range, one that compresses below it the smaller.

*Usable dynamic range.* Up to $I_{\mathrm{DC}} = \sqrt2\,I_{\max}$ the light limits the tone in both front ends, and the TIA leads by $A$. Above it the TIA clips while the chain still follows the light, and the chain overtakes the TIA where the chain's light-limited dynamic range exceeds the TIA's electronic one. To keep its lead with fully modulated light up to $I_{\mathrm{DC}}$, the TIA needs $I_{\max} \ge (I_{\mathrm{DC}}/\sqrt2)\,10^{-A/20}$, i.e. an output amplitude

$$
V_{\mathrm{pk}} = \sqrt2\,|Z_T|\,I_{\max} \ge |Z_T|\,I_{\mathrm{DC}}\,10^{-A/20},
\tag{⟦E:bench-vpk⟧}
$$

which tends to $R_FI_{\mathrm{DC}}$ at high photocurrent, where $A \to 0$. For a 2-kΩ TIA at 10 mA, with $A$ = 0.63 dB (OPA855, ⟦Section 6.8⟧), that is 1.994 kΩ × 10 mA × $10^{-0.63/20}$ = 18.5 V, against the 1.5–2.2 V of the op amps (⟦Section 6.4⟧) and the 8.3 V of the high-voltage composite (⟦Section 7.2⟧).

**Verdict.** For a small signal every design we carry forward beats the benchmark at every photocurrent, by 15–18 dB in the dark for the quietest and by less than 1 dB at 10 mA. For large signals the benchmark is strong from about 1.2 mA up: a chain that compresses at −20 dBm or above follows fully modulated light up to 1.26 mA, while a 5-V op-amp TIA clips at 0.54 mA rms and follows it only up to 0.76 mA. ⟦Section 3.3⟧ sets the first worked design against the benchmark, ⟦Section 6.8⟧ every leading design, and ⟦Chapter 7⟧ asks what it takes to raise a TIA's ceiling."""

COMPOSITES_OVERVIEW = r"""
### 2.6 Composite front ends and the DC photocurrent

An op-amp TIA leaves two quantities to the amplifier that a discrete stage can improve. Its noise floor is set by the amplifier's input transistors; a low-noise transistor at the summing node, a silicon JFET, a GaAs pHEMT or a SiGe bipolar transistor, can take over that role while the op amp supplies the loop gain (⟦Section 7.1⟧). Its ceiling is set by the amplifier's output swing and slew rate; a fast high-voltage amplifier inside the $R_F$ loop can raise it (⟦Section 7.2⟧). Both are composites, whose loop closes around two or three active stages, and their stability needs its own analysis, which ⟦Chapter 7⟧ gives with SPICE verification.

The DC photocurrent shapes every option. In a single-ended detector, 10 mA through 2 kΩ would need 20 V; in the balanced pair only the imbalance $I_1 - I_2$ reaches $R_F$ (⟦Section 1.2⟧). ⟦Chapter 8⟧ covers the ways of removing a DC current that remains: a resistive sink driven by a slow servo, AC coupling, an inductive bias tee and a two-stage split of the gain (⟦Sections 8.2–8.5⟧); bootstrapping and cascoding the photodiodes (⟦Sections 8.6 and 8.7⟧); and servos for the imbalance and the photodiode bias (⟦Section 8.8⟧). It ends with the proposed balanced front end (⟦Section 8.9⟧).
"""

CH3 = r"""
## 3. A first op-amp TIA, worked through

Before any derivation, we put the most promising candidate through the four equations that carry the numbers of this note. The amplifier is OPA855, a decompensated bipolar op amp with 8 GHz of gain-bandwidth product and about 1 nV/√Hz of input voltage noise, which ⟦Chapter 6⟧ confirms as the best production part. The feedback resistor is 2 kΩ, and the photodiode pair puts 1 pF on the summing node. The four equations are bench-unit forms of results that ⟦Chapter 4⟧ derives: the input-referred noise, the noise of an instrument behind the TIA referred to the same photocurrent, the bandwidth of a maximally flat design with the stability condition of a decompensated amplifier, and the shot-noise-limited dynamic range. ⟦Section 3.2⟧ substitutes OPA855's datasheet values into them, ⟦Section 3.3⟧ sets the result against the 50-Ω benchmark, and ⟦Section 3.4⟧ lists what the four equations cannot settle.
"""

CH3_SUBST = r"""
### 3.2 OPA855 at 2 kΩ: the worked substitution

Table 0.2 lists the inputs, each with its datasheet source.
"""

CH3_BENCH = r"""
### 3.3 The first design against the 50-Ω benchmark

We now set this design against the 50-Ω benchmark of ⟦Section 2.1⟧, with a 2-dB noise figure, using the spot values of Eq. (1) at 100 MHz.

**Noise.** The dark TIA's 4.17 pA/√Hz is $20\log_{10}(22.85/4.17)$ = 14.8 dB below the chain's 22.85 pA/√Hz (Eq. (⟦E:bench-noise⟧)). With photocurrent the shot noise is common to both. At $I_{\mathrm{DC}}$ = 1 mA it is 17.90 pA/√Hz: the TIA gives 18.38 pA/√Hz and the chain $\sqrt{22.85^2 + 17.90^2}$ = 29.03 pA/√Hz, so the TIA still leads by $20\log_{10}(29.03/18.38)$ = 4.0 dB. At 10 mA the shot noise is 56.61 pA/√Hz, the TIA gives 56.76 pA/√Hz and the chain $\sqrt{22.85^2 + 56.61^2}$ = 61.05 pA/√Hz, a lead of 0.63 dB. For a small RF signal on the DC, as in the receiver of ⟦Section 1.1⟧, the TIA therefore wins at every photocurrent, by an amount that shrinks as the shot noise takes over.

**Ceiling.** The design's largest tone at 100 MHz is $V_{\mathrm{pk}}/(\sqrt2\,|Z_T|)$ = 1.525 V/(√2 × 1.996 kΩ) = 0.540 mA rms. A chain reaches the same current when it compresses at $P_{\mathrm{eq}} = (R_0/4)I_{\max}^2$ = 12.5 Ω × (0.540 mA)² = 3.65 µW, i.e. −24.4 dBm (Eq. (⟦E:bench-px⟧)). A low-noise amplifier that compresses at −10 dBm has a ceiling 14.4 dB higher.

**Dynamic range.** Eq. (4) gives the TIA 67.8 dB at 1 mA, and with the amplifier's own noise included it has 67.6 dB (Table 6.3). The chain that compresses at −10 dBm has 78.0 dB (Table N1), 10.4 dB more, but only for a tone of 2.83 mA rms, which the light cannot supply: at 1 mA the largest tone is 0.71 mA rms (Eq. (⟦E:optical⟧)). On that tone the chain's dynamic range is 66.0 dB, 1.6 dB below the TIA's. The benchmark overtakes this design only above about 1.2 mA, where the light can drive a tone larger than the TIA's 0.54-mA ceiling (⟦Section 6.8⟧).

### 3.4 What the four equations leave open

The worked example answers the first questions and leaves the harder ones open. Its noise is within 0.23 dB of the shot noise at 1 mA, so at the planned photocurrents the amplifier's noise matters only near 0.1 mA and at the top of the band. Its 1.525-V output amplitude, not its noise, sets the dynamic range from about 0.15 mA up (⟦Section 6.6.3⟧). Its stability rests on a feedback capacitance of 0.15–0.36 pF that the parasitics of the resistor and its pads largely set, and Eq. (3) gives a bandwidth but no phase margin: for a decompensated amplifier near its minimum stable gain, the phase margin depends on the amplifier's higher poles. ⟦Chapter 4⟧ therefore derives the equations with their assumptions and builds the open-loop model that gives the phase margins, ⟦Chapter 5⟧ checks that model against the manufacturers' SPICE macromodels, and ⟦Chapter 6⟧ applies both to every candidate.
"""

CH4_INTRO = r"""This chapter derives, from the circuit of Figure 1, every equation used later, ending at the bench-unit forms of ⟦Chapter 3⟧. Symbols are defined where they first appear in each section. The chapter closes with the two checks of the model that need no simulator: the closed-loop and TIA data printed in the datasheets (⟦Section 4.9⟧) and a bench measurement on an OPA846 board (⟦Section 4.10⟧)."""

OPTICAL = r"""It is stored with the results but not tabulated.

**Electronic and usable dynamic range.** Eq. (25) counts the largest tone the electronics can pass and assumes that the light can supply it. We call it the electronic dynamic range, and every dynamic range in this note is of this kind unless it is called usable. The light sets a second ceiling. In the balanced pair the signal is the difference current $i_1(t) - i_2(t)$. If the two beams are modulated sinusoidally, $i_{1,2}(t) = I_{1,2}\left(1 \pm m_{1,2}\cos 2\pi f_0t\right)$ with modulation depths $m_{1,2} \le 1$, the tone's amplitude is $I_1m_1 + I_2m_2 \le I_1 + I_2 = I_{\mathrm{DC}}$. Balanced heterodyne detection meets the same bound: a local oscillator of power $P_{\mathrm{LO}}$ beating with a signal of power $P_S$ gives the amplitude $2\mathcal{R}\sqrt{P_{\mathrm{LO}}P_S} \le \mathcal{R}\left(P_{\mathrm{LO}} + P_S\right) = I_{\mathrm{DC}}$, with $\mathcal{R}$ the responsivity, and the two are equal only for equal powers. The largest tone the light can supply is therefore $I_{\mathrm{DC}}/\sqrt2$ rms, and the usable dynamic range is set by the smaller of the two ceilings, against the same noise:

$$
I_{\mathrm{tone}} \le \frac{I_{\mathrm{DC}}}{\sqrt2},
\qquad
\mathrm{DR}_{B,\mathrm{usable}} = 20\log_{10}\frac{\min\!\left(I_{\max}(f_0),\; I_{\mathrm{DC}}/\sqrt2\right)}{i_{n,B}},
\tag{⟦E:optical⟧}
$$

with $I_{\max}(f_0) = V_{\mathrm{pk}}/(\sqrt2\,|Z_T(f_0)|)$ the numerator of Eq. (25) and $i_{n,B} = \sqrt{\int_0^B S_i(f)\,df}$ its denominator. In the dark the light supplies no tone at all. The two figures differ only above $I_{\mathrm{DC}} = \sqrt2\,I_{\max}$, where the light could drive the TIA past its ceiling: for OPA855 on 5 V at 2 kΩ, with $I_{\max}$ = 1.525 V/(√2 × 1.996 kΩ) = 0.540 mA rms, that is 0.76 mA. Below it the light, not the TIA, limits the largest tone, and a better amplifier gains only through lower noise. We use the usable figure where a front end with a much higher ceiling, the 50-Ω chain of ⟦Section 2.1⟧, is compared with the TIAs (⟦Sections 3.3 and 6.8⟧)."""

CH5_INTRO = r"""Our analytical model rests on each amplifier's datasheet open-loop curve and on the hand model of ⟦Chapter 4⟧. In this chapter we run the manufacturers' SPICE macromodels of seven candidates through the same circuits:"""

CH6 = r"""
## 6. The op amps compared

With the model of ⟦Chapter 4⟧ checked against the macromodels in ⟦Chapter 5⟧, we now compare the candidates. ⟦Section 6.1⟧ collects their datasheet specifications and what a designer must know beyond them. ⟦Sections 6.2–6.4⟧ compare every analysed part, at both feedback resistors, in stability and bandwidth, noise and dynamic range, from the analytical model; each opens with a chart, and the tables behind the charts are in ⟦Appendix A6⟧. ⟦Section 6.5⟧ lets SPICE find every part's best design. ⟦Section 6.6⟧ recomputes the dynamic range of the leading designs from their macromodels and takes one apart to show what sets it, ⟦Section 6.7⟧ adds the single-chip TIAs on the same definition, and ⟦Section 6.8⟧ sets the leading designs against the 50-Ω benchmark.

### 6.1 The candidates' datasheet specifications

We start from the datasheets. ⟦Section 6.1.1⟧ explains the specification tables, which give for every analysed part the values a TIA design depends on, and ⟦Section 6.1.2⟧ collects, part by part, what a designer must know that those tables do not show.
"""

CH6_BW = r"""
### 6.2 Stability and bandwidth

Figure ⟦F:bw⟧ shows the result for every analysed part at both feedback resistors: (a) the widest bandwidth with a phase margin of at least 45° and at most 1 dB of peaking, the robust design, and (b) the phase margin of the flat design. At 2 kΩ seven configurations reach 150 MHz robustly without added input capacitance: OPA855 (539 MHz), LMH6629 with the COMP pin high (276 MHz) and low (171 MHz), OPA856 (231 MHz), OPA859 (211 MHz), THS4304 (191 MHz) and OPA843 (150 MHz). OPA858, with its open-loop curve as plotted, OPA955 and OPA818 get there only with 0.25, 3 and 8 pF added at the input, and nine parts have no robust design at all. Among the decompensated parts with the lowest noise, OPA955, OPA818 and OPA846 have flat designs below 45° (36°, 32° and 34°), and OPA847 has no stable flat design; ⟦Sections 6.2.6 and 6.2.8⟧ explain why, and what it costs to accept. Tables 4.2 and 4.3 give the numbers behind the figure, and the sections below explain them.

![Figure ⟦F:bw⟧](figures/fig17_bandwidth_phase_margin_all_parts.png)

*Figure ⟦F:bw⟧. Stability and bandwidth of every analysed part, $C_D$ = 1 pF, nominal parasitics, from the analytical model with the datasheet open-loop curves. (a) Widest bandwidth with phase margin ≥ 45° and ≤ 1 dB of peaking (the robust design) at $R_F$ = 2 kΩ (filled) and 1.5 kΩ (open); dark red where input capacitance had to be added to reach 45° (0.25 pF for OPA858 at 2 kΩ, 1–8 pF for the others). The shaded band is 150–200 MHz. (b) Phase margin of the flat design; the dashed line marks 45°. Amplifiers: all 25 analysed parts, 26 configurations (LMH6629 with the COMP pin high and low), sorted by robust bandwidth at 2 kΩ; OPA858 with its open-loop curve as plotted (Table 4.4 gives its calibrated variant). Values from Tables 4.2 and 4.3.*
"""

CH6_NOISE_FIG = r"""Figure ⟦F:noise⟧ ranks every analysed part with a stable flat design by its band noise above the Johnson floor of $R_F$, over 10–150 MHz, at both feedback resistors. The bipolar parts with sub-nanovolt $e_n$ and little input capacitance lead: at 2 kΩ OPA955 is 0.9 dB above the floor, OPA855 3.1 dB and OPA856 3.2 dB. For the FET-input parts and OPA955 a bar runs to the high estimate of ⟦Section 4.7⟧, which lies 0.3–2.7 dB above the central one. All of them lie below the 50-Ω benchmark, which with a 2-dB noise figure is 18.0 dB above the 2-kΩ floor and 16.8 dB above the 1.5-kΩ floor (Eq. (⟦E:bench-noise⟧)). In the dark a TIA is therefore more sensitive than the plain termination by the difference: 17.1 dB for OPA955, 14.9 dB for OPA855 and 0.9 dB for OPA657, the noisiest part.

![Figure ⟦F:noise⟧](figures/fig18_noise_penalty_all_parts.png)

*Figure ⟦F:noise⟧. Input-referred noise integrated over 10–150 MHz, relative to the Johnson noise of $R_F$ (the band penalty), flat design, $C_D$ = 1 pF, from the analytical model, at $R_F$ = 2 kΩ (filled) and 1.5 kΩ (open). Dark red marks FET- or CMOS-input parts; a horizontal bar extends to the high estimate where it differs (OPA858, OPA859, OPA818, LTC6268-10 and OPA955). The dashed and dotted lines mark the 50-Ω benchmark with a 2-dB noise figure against the same floors, 18.0 dB at 2 kΩ and 16.8 dB at 1.5 kΩ (Eq. (⟦E:bench-noise⟧)). Amplifiers: the 21 configurations with a stable flat design (one per row), sorted by the penalty at 2 kΩ; OPA657 has one only at 2 kΩ. Values for the ten amplifiers of Tables 5.1 and 5.3 from those tables, for the others from `data/results/results.json`.*
"""

CH6_DR = r"""
### 6.4 Dynamic range

Figure ⟦F:dr⟧ shows the electronic dynamic range (Eq. (25)) in 150 MHz for a 100-MHz tone of the ten amplifiers carried forward, at $R_F$ = 2 kΩ with the imbalance servoed to zero, in the dark and at $I_1 + I_2$ = 0.1, 1 and 10 mA. In the dark the quietest parts lead, OPA955 with 82.9 dB. From 0.1 mA up the order follows the output amplitude instead: OPA818, with 2.23 V at 100 MHz, leads with 78.0, 70.7 and 61.1 dB, 3.1 dB ahead of OPA855 at 1 mA, and OPA856, slew-limited to 0.56 V, trails OPA855 by 8.5–8.6 dB at every current. The dashed lines mark the 50-Ω benchmark compressing at −10 dBm. In this electronic measure it leads every amplifier from 0.1 mA up, by 1.8 dB (OPA818) to 12.4 dB (OPA856) at 0.1 mA and by 7.3 to 19.0 dB at 1 mA, but most of the tones that lead assumes are larger than the light can supply, which ⟦Section 6.8⟧ accounts for. Table 6.3 gives the numbers, and the sections below derive them.

![Figure ⟦F:dr⟧](figures/fig19_dynamic_range_all_parts.png)

*Figure ⟦F:dr⟧. Electronic dynamic range (Eq. (25)) in 150 MHz for a 100-MHz tone, $R_F$ = 2 kΩ, $C_D$ = 1 pF, flat design, imbalance servoed to zero, from the analytical model; dark (diamonds) and $I_1 + I_2$ = 0.1, 1 and 10 mA. The dashed lines, in the colour of each current, mark the 50-Ω benchmark compressing at −10 dBm with a 2-dB noise figure (Table N1); its dark and 0.1-mA lines nearly coincide (80.1 and 79.8 dB). Amplifiers: the ten of Table 6.3 (one per row), sorted by the value at 1 mA. Values from Table 6.3.*
"""

CH6_SPICE = r"""
### 6.5 Eleven further amplifiers, and every part's best design in SPICE

The comparisons above use the datasheet open-loop curves. With the macromodels checked in ⟦Chapter 5⟧, we can also let SPICE find each part's best design, and add eleven amplifiers: OPA955, eight parts that our analytical comparison found less suitable, and OPA817 and OPA814, which it left out.
"""

CH6_DR_SPICE = r"""
### 6.6 Dynamic range of the leading designs in SPICE

⟦Section 6.4⟧ gives the dynamic range of every candidate from our analytical model, and ⟦Chapter 5⟧ checks the leading designs' noise and stability against the manufacturers' macromodels. Here we return to dynamic range, the receiver's priority. ⟦Section 6.6.1⟧ states how it is computed. ⟦Section 6.6.2⟧ recomputes it for the five leading amplifiers at their best designs in SPICE (Table 10.13), from the macromodels' own noise and transimpedance, and compares our analytical model at the same feedback capacitance (Table 11.1, Figure 15(a)–(b)). ⟦Section 6.6.3⟧ takes one design, OPA818, apart: which noise sets the floor and which large-signal limit sets the ceiling at each photocurrent and tone, and what a faster amplifier or a higher supply would buy (Figure 16). ⟦Section 6.7⟧ then puts single-chip TIAs on the same definition, and ⟦Section 6.8⟧ the 50-Ω benchmark.
"""

CH6_BENCH = r"""
### 6.8 The designs against the 50-Ω benchmark

We now set the leading designs against the benchmark family of ⟦Section 2.1⟧, with both definitions of ⟦Section 4.8⟧: the electronic dynamic range of Eq. (57), and the usable dynamic range of Eq. (⟦E:optical⟧), which caps the tone at what the light can supply. The designs are the three leading op amps at their best SPICE designs (Table 11.1), the CE3512K2 pHEMT composite (Table 11.6) and the OPA859–THS3491 composite at a gain of 5.5 (Table 11.9); their band noise and their ceiling at a 100-MHz tone come from those tables. The benchmark is the 50-Ω chain with a 2-dB noise figure, compressing at −20, −10 or 0 dBm (Table N1). Tables N2 and N3 give the numbers, and Figure ⟦F:bench⟧ draws them.

**Small signal.** For the same small tone, a design's advantage is $A = 20\log_{10}(i_{n,B,50}/i_{n,B})$, the ratio of the band noises with the shot noise of the pair in both (Figure ⟦F:bench⟧(a)); it does not depend on the chain's compression level. In the dark it is 17.7 dB for the pHEMT composite, 17.2 dB for OPA955, 15.0 dB for OPA855, 10.4 dB for OPA818 and 6.2 dB for the high-voltage composite, in the order of their dark band noise, 36.5, 38.8, 49.6, 84.8 and 136.5 nA rms against the chain's 279.8 nA. For OPA855 at 1 mA, for example, the shot noise $\sqrt{2qI_{\mathrm{DC}}B}$ = 219.2 nA rms brings the TIA to $\sqrt{49.6^2 + 219.2^2}$ = 224.8 nA and the chain to $\sqrt{279.8^2 + 219.2^2}$ = 355.5 nA, and $A = 20\log_{10}(355.5/224.8)$ = 4.0 dB. The common shot noise compresses every lead in the same way: at 1 mA they are 2.8–4.1 dB, and at 10 mA 0.5–0.6 dB. No design falls behind at any photocurrent.

**Electronic dynamic range.** The chain's electronic dynamic range equals a design's when the chain compresses at $P_x = P_{\mathrm{eq}} + A$ (Eq. (⟦E:bench-px⟧)), and a chain that compresses above $P_x$ has more. For the op amps and the pHEMT composite $P_{\mathrm{eq}}$ is −24.4 to −20.9 dBm, so $P_x$ falls from −10.6 to −5.9 dBm in the dark to −20.4 to −17.3 dBm at 1 mA and −23.7 to −20.3 dBm at 10 mA. A 50-Ω amplifier that compresses at −10 dBm therefore has the larger electronic dynamic range from 0.1 mA up. The high-voltage composite, with $P_{\mathrm{eq}}$ = −9.0 dBm, needs a chain that compresses above −2.7 dBm in the dark and above −8.5 dBm at 10 mA.

**Usable dynamic range.** The chain's higher ceiling counts only for tones the light can supply (Figure ⟦F:bench⟧(b)). Up to $I_{\mathrm{DC}} = \sqrt2\,I_{\max}$ of a design, 0.76–0.83 mA for OPA955, OPA855 and the pHEMT composite, 1.14 mA for OPA818 and 4.50 mA for the high-voltage composite, the light limits both, and the design leads by $A$. Above it the design clips, while the chain follows the light up to its own clip point, $\sqrt2\,I_{\max,50}$ = 1.26, 4.0 or 12.6 mA. The chain overtakes OPA955, OPA855 and the pHEMT composite at 1.16–1.25 mA whatever its compression level, because the light still limits the chain there. It overtakes OPA818 at 1.56 mA if it compresses at −10 dBm or above, and at 6.04 mA if it compresses at −20 dBm. It overtakes the high-voltage composite only if it compresses above that design's $P_{\mathrm{eq}}$ of −9.0 dBm: a 0-dBm chain does so above 5.0 mA. Over 0.1–10 mA the best usable dynamic range of any design is 59.1 dB at 0.1 mA (pHEMT composite; OPA955 59.0 dB), 69.6 dB at 1 mA (OPA818) and 73.1 dB at 10 mA (high-voltage composite), against 47.8, 66.0 and 71.6 dB for the chain that compresses at −10 dBm.

**What it takes to stay ahead.** A design keeps its lead over every chain up to a photocurrent $I_{\mathrm{DC}}$ only if it can pass the full-modulation tone there, which by Eq. (⟦E:bench-vpk⟧) takes an output amplitude of $|Z_T|\,I_{\mathrm{DC}}\,10^{-A/20}$. For OPA855 that is 1.994 kΩ × 1 mA × $10^{-4.0/20}$ = 1.26 V at 1 mA, which its 1.525 V covers, and 18.5 V at 10 mA. For 10 mA in each diode it is 1.994 kΩ × 20 mA × $10^{-0.33/20}$ = 38 V. The op amps have 1.5–2.2 V, and the high-voltage composite 8.3 V, enough to 4.5 mA. A smaller $R_F$ lowers the requirement in proportion and costs noise that the shot noise hides at high photocurrent (Eq. (26)), which is why the benchmark's strength lies there.

![Figure ⟦F:bench⟧](figures/fig20_benchmark_50ohm.png)

*Figure ⟦F:bench⟧. The leading designs against the 50-Ω benchmark: the pair terminated in 50 Ω in parallel with the input of an amplifier of 2 dB noise figure; 150-MHz noise band, 100-MHz tone, imbalance servoed to zero. (a) Small-signal advantage $A$ (Eq. (⟦E:bench-px⟧)), the ratio of the benchmark's band noise to the design's, with the shot noise of $I_1 + I_2$ in both; it does not depend on the benchmark's compression level. (b) Usable dynamic range (Eq. (⟦E:optical⟧)), with the tone limited by the design's ceiling or by the light, whichever is lower; dotted, the benchmark compressing at −20, −10 and 0 dBm at the input. The three dotted curves coincide below 1.26 mA, where the light, not the amplifier, limits the benchmark, and separate at 1.26, 4.0 and 12.6 mA. The shaded band is the planned 0.1–10 mA. Designs: OPA955, OPA855 and OPA818 at their best SPICE designs at 1 pF and 2 kΩ (Table 11.1); the CE3512K2 pHEMT composite (Table 11.6); OPA859 with THS3491 at $G_2$ = 5.5 (Table 11.9). Values in Tables N2 and N3.*

*Table N2. The leading designs against the 50-Ω benchmark: ceiling and small-signal advantage. The dark band noise is $i_{n,B}$ of Eq. (56) at $I_{\mathrm{DC}}$ = 0; $I_{\max}$ is the largest tone at 100 MHz, rms, and fully modulated light reaches it at $I_1 + I_2 = \sqrt2\,I_{\max}$; $P_{\mathrm{eq}}$ is the compression level at which the benchmark has the same ceiling, $A$ the small-signal advantage and $P_x$ the compression level at which the benchmark's electronic dynamic range equals the design's (Eq. (⟦E:bench-px⟧)). Benchmark: 2 dB noise figure, 279.8 nA rms in 150 MHz in the dark. Front ends: OPA955, OPA855, OPA818 (best SPICE designs at 1 pF and 2 kΩ, Table 11.1); CE3512K2 pHEMT composite (Table 11.6); OPA859 with THS3491 at $G_2$ = 5.5 (Table 11.9); one per row.*

| Design | Dark band noise (nA rms) | $I_{\max}$ (mA rms); full modulation up to (mA) | $P_{\mathrm{eq}}$ (dBm) | $A$ at $I_1 + I_2$ = 0 / 0.1 / 1 / 10 / 20 mA (dB) | $P_x$ at 0 / 0.1 / 1 / 10 / 20 mA (dBm) |
|---|---|---|---|---|---|
| OPA955 | 38.8 | 0.544; 0.77 | −24.3 | 17.2 / 11.2 / 4.1 / 0.6 / 0.3 | −7.2 / −13.1 / −20.3 / −23.7 / −24.0 |
| OPA855 | 49.6 | 0.541; 0.76 | −24.4 | 15.0 / 10.6 / 4.0 / 0.6 / 0.3 | −9.3 / −13.8 / −20.4 / −23.7 / −24.0 |
| OPA818 | 84.8 | 0.803; 1.14 | −20.9 | 10.4 / 8.4 / 3.6 / 0.6 / 0.3 | −10.6 / −12.5 / −17.3 / −20.3 / −20.6 |
| CE3512K2 pHEMT composite | 36.5 | 0.589; 0.83 | −23.6 | 17.7 / 11.3 / 4.1 / 0.6 / 0.3 | −5.9 / −12.3 / −19.5 / −23.0 / −23.3 |
| OPA859 + THS3491, $G_2$ = 5.5 | 136.5 | 3.182; 4.50 | −9.0 | 6.2 / 5.5 / 2.8 / 0.5 / 0.3 | −2.7 / −3.5 / −6.2 / −8.5 / −8.7 |

*Table N3. The leading designs against the 50-Ω benchmark: usable dynamic range in 150 MHz (Eq. (⟦E:optical⟧)) and the photocurrent above which the benchmark's usable dynamic range is the larger, for each compression level ("none" means not up to 100 mA). Front ends: those of Table N2, and in the last three rows the benchmark itself.*

| Design | Usable dynamic range at $I_1 + I_2$ = 0.1 / 1 / 10 / 20 mA (dB) | Benchmark ahead above, for $P_{\max}$ = −20 / −10 / 0 dBm (mA) |
|---|---|---|
| OPA955 | 59.0 / 67.8 / 57.9 / 54.9 | 1.17 / 1.17 / 1.17 |
| OPA855 | 58.4 / 67.6 / 57.8 / 54.8 | 1.16 / 1.16 / 1.16 |
| OPA818 | 56.2 / 69.6 / 61.2 / 58.2 | 6.04 / 1.56 / 1.56 |
| CE3512K2 pHEMT composite | 59.1 / 68.5 / 58.6 / 55.6 | 1.25 / 1.25 / 1.25 |
| OPA859 + THS3491, $G_2$ = 5.5 | 53.3 / 68.7 / 73.1 / 70.1 | none / none / 5.00 |
| 50-Ω benchmark, −20 dBm | 47.8 / 66.0 / 61.6 / 58.9 | – |
| 50-Ω benchmark, −10 dBm | 47.8 / 66.0 / 71.6 / 68.9 | – |
| 50-Ω benchmark, 0 dBm | 47.8 / 66.0 / 79.5 / 78.9 | – |
"""

CH7 = r"""
## 7. Composite front ends

⟦Section 6.6.3⟧ shows that from about 0.15 mA up the ceiling, not the noise, sets the dynamic range of every op-amp design, and ⟦Section 6.8⟧ that the 50-Ω benchmark overtakes them above about 1.2 mA for the same reason. This chapter asks what a second active device adds. ⟦Section 7.1⟧ places a discrete transistor at the summing node, a silicon JFET, a GaAs pHEMT or a SiGe bipolar transistor, to lower the floor, and designs and verifies such composites. ⟦Section 7.2⟧ raises the ceiling instead, with a fast high-voltage amplifier inside the $R_F$ loop: its stability, noise, slew rate, distortion and power. ⟦Section 7.3⟧ documents the SPICE models and decks of both and the convergence messages met.
"""

CH8 = r"""
## 8. The proposed front end: DC photocurrent, servos and starting values

With the amplifier chosen, two parts of the front end remain: what happens to the DC photocurrent, and the component values of the board. ⟦Section 8.1⟧ states the constraint the DC imposes. ⟦Sections 8.2–8.5⟧ give four ways of removing a large DC current, which matter for a single-ended detector and for an imbalance too large to servo; the fifth, the 50-Ω termination, is the benchmark of ⟦Section 2.1⟧. ⟦Sections 8.6 and 8.7⟧ explain why bootstrapping and cascoding the photodiodes do not pay at 0.5–1 pF, and ⟦Section 8.8⟧ covers the servos for the imbalance and for the photodiode bias and why they are hard to make quiet. ⟦Section 8.9⟧ gives the proposed balanced front end in two variants, OPA855 and OPA818, ⟦Section 8.10⟧ its starting component values, and ⟦Section 8.11⟧ lists what not to do.
"""

CH9 = r"""
## 9. Conclusions and recommendations

We now collect what the preceding chapters establish: the three decisions that settle the choice of amplifier (⟦Section 9.1⟧), what the SPICE cross-check changes (⟦Section 9.2⟧), what sets the dynamic range and how the alternatives compare with the op-amp designs and with the 50-Ω benchmark (⟦Sections 9.3–9.5⟧), the leading amplifiers with their ranking and the recommended picks (⟦Sections 9.6–9.10⟧), the flags a designer must respect (⟦Section 9.11⟧), the noise floor the next stage must respect (⟦Section 9.12⟧), and what only a simulation or a measurement can settle (⟦Section 9.13⟧).
"""

CH9_BENCH = r"""
### 9.5 Against the 50-Ω benchmark

- **For the receiver as specified, a small RF signal on 0.1–10 mA, every design we carry forward beats a plain 50-Ω termination with a 2-dB amplifier at every photocurrent.** OPA855 leads by 15.0 dB in the dark, 10.6 dB at 0.1 mA, 4.0 dB at 1 mA and 0.6 dB at 10 mA; OPA955 and the pHEMT composite lead by 17.2 and 17.7 dB in the dark and 11.2 and 11.3 dB at 0.1 mA, and the high-voltage composite, the noisiest, by 6.2 dB in the dark (⟦Section 6.8⟧, Figure ⟦F:bench⟧(a)). For this a TIA needs only less band noise than the chain, whose 22.85 pA/√Hz integrate to 279.8 nA rms in 150 MHz; the designs here have 2.0–7.7 times less in the dark.
- **For large signals the benchmark wins from about 1.2 mA up.** A TIA on a 5-V op amp clips at 0.54 mA rms, so it follows fully modulated light only up to $I_1 + I_2$ = 0.76 mA, while a 50-Ω chain that compresses at −20 dBm follows it to 1.26 mA, and one at −10 dBm to 4.0 mA. The chain's usable dynamic range overtakes OPA855's and OPA955's at 1.16–1.17 mA and OPA818's at 1.56 mA (6.04 mA for a chain at −20 dBm).
- **The compression level that matches a design** is $P_{\mathrm{eq}} = (R_0/4)I_{\max}^2$: −24.4 dBm for OPA855, −24.3 dBm for OPA955, −23.6 dBm for the pHEMT composite, −20.9 dBm for OPA818 and −9.0 dBm for the high-voltage composite. A chain compressing at −10 dBm has more electronic dynamic range than every op-amp design from 0.1 mA up, but most of the tones that assumes are larger than the light can supply.
- **What a TIA needs to beat it at every photocurrent is an output amplitude of $|Z_T|\,I_{\mathrm{DC}}\,10^{-A/20}$**, about 18.5 V at 10 mA and 2 kΩ (Eq. (⟦E:bench-vpk⟧)). The high-voltage composite of ⟦Section 7.2⟧, with 8.3 V, comes closest: no chain that compresses at −10 dBm or below overtakes it, and a 0-dBm chain only above 5.0 mA.
"""

CH9_SIDE = r"""
### 9.10 OPA846, OPA818 and OPA847 side by side

Table 8.2 sets the three short-listed decompensated parts side by side at 2 kΩ and 1 pF. OPA818 is the best of the three: it has the largest amplitude (2.23 V at 100 MHz, from its 1400 V/µs), the largest uncorrected imbalance (5.50 mA) and the highest dynamic range (70.7 dB at 1 mA), but its phase margin cannot exceed 34° on a 1-pF photodiode, so it belongs in a second stage or in a 33° TIA whose peaking is verified and equalized. OPA846 reaches a similar 34.5° with less than half the slew rate and more input capacitance, and OPA847, with a minimum stable gain of 12, has no stable flat design at all.
"""

APPENDIX_A = r"""
## Appendix A. Tables

The tables behind the charts and the text of ⟦Chapters 1–9⟧, grouped by the chapter that discusses them and numbered in the order of the sections they belong to. Each caption names the amplifiers it covers. Three short tables stay in the text: the assumed values (Table 1.1), the inputs to the worked example (Table 0.2) and the ranking (Table 8.0). Tables 10.1–10.2, A2.1–A2.4 and A3.1 belong to their own appendices.

""" + APPENDIX_A_MARKER

APPENDIX_B = r"""
## Appendix B. Running the SPICE checks

This appendix holds the practical side of ⟦Chapter 5⟧: how ngspice is driven from a script, with the pitfalls met on the way (⟦Appendix B.1⟧), and how to reproduce every SPICE number of this note (⟦Appendix B.2⟧).
"""

FILES_FIGURES = r"""| `figures/` | Figures 1–20 as PNG (600 dpi) and PDF. The file names keep the order in which the figures were drawn: `fig01` is ⟦Figure 1⟧ (`scripts_archive/make_circuit_figure.py`); `fig02`–`fig06` are ⟦Figures 14, 11, 2, 12 and 16⟧ (`scripts_archive/make_figures.py`); `fig07`–`fig16` are ⟦Figures 3–9 and 17–19⟧ (`scripts_archive/make_spice_figures.py`); and `fig17`–`fig20` are ⟦Figures 10, 13, 15 and 20⟧ (`scripts_archive/make_narrative_figures.py`) |"""

FILES_BENCH_ROW = r"""| `data/results/composite_analytical.json`, `composite_hv_fine_scan.json` | the analytical scans of Sections 11.5–11.6 (`scripts_archive/composite_tia.py`; the fine scan with `--fine`) |
| `data/results/benchmark_50ohm.json` | the 50-Ω benchmark family and the leading designs against it (⟦Sections 2.1 and 6.8⟧; Tables N1, N2 and N3), from `scripts_archive/benchmark_50ohm.py`, whose `--tables` option prints the table rows |"""

# ---------------------------------------------------------------------------------------------- plan
PLAN = [
    T(FRONT),
    T(CH1),
    B("1.1", "### 1.1 The question and why DC photocurrent comes first"),
    B("1.5", "### 1.2 The balanced photodiode pair: what the photocurrent figures mean", replace=[
        ("The tables of Sections 0 and 4–8 use $I_{\\mathrm{DC}}$ = 0.1, 1 and 10 mA.",
         "The tables use $I_{\\mathrm{DC}}$ = 0.1, 1 and 10 mA."),
        ("Every table in Sections 0 and 3–8 uses $C_D$ = 1 pF at the summing node",
         "Unless it states otherwise, every table uses $C_D$ = 1 pF at the summing node"),
        ("with the same nominal parasitics and design rules as Section 4.",
         "with the same nominal parasitics and design rules as ⟦Section 6.2⟧.")]),
    B("1.2", "### 1.3 The circuit", replace=[
        ("the optional DC servo of Section 7.*", "the optional DC servo of ⟦Chapter 8⟧.*")]),
    B("1.3", "### 1.4 Assumed values", replace=[
        ("| per datasheet | Section 3 tables |", "| per datasheet | Table 3a |"),
        ("| designed per amplifier, never below $C_{F,\\mathrm{par}}$ | Section 4 |",
         "| designed per amplifier, never below $C_{F,\\mathrm{par}}$ | ⟦Section 6.2⟧ |"),
        ("±5 V to ±6.5 V for the others (Section 3) |", "±5 V to ±6.5 V for the others (Table 3c) |")]),
    B("1.4", "### 1.5 Conventions", replace=[
        ('- "Shot-noise clearance" at a DC photocurrent is the ratio, in dB, of the photocurrent shot-noise density to all other noise densities at the same frequency.',
         CONVENTION_DR),
        ("**Status of every number.** Every phase margin, bandwidth and noise figure in Sections 0–9 is an **analytical estimate** from the datasheet open-loop curve. Section 9 lists the cases where only a simulation or a measurement can settle the answer. Section 10 then runs the manufacturers' SPICE macromodels and compares.",
         STATUS)]),

    T(CH2),
    B("7.6", "### 2.1 The plain 50-Ω termination: the benchmark", replace=[
        ("At high photocurrent the oldest front end becomes competitive: the photodiode terminated in 50 Ω, followed by an RF LNA, with a bias tee carrying the DC.",
         BENCH_INTRO),
        ("**Noise.** If the LNA has noise factor $F$ referred to a 50-Ω source, the input-referred current noise is $F\\cdot4k_BT/R_0$ with $R_0$ = 50 Ω. This equals the shot noise at",
         BENCH_NOISE),
        ("- The bandwidth is $1/(2\\pi\\cdot50\\,\\Omega\\cdot1\\,\\mathrm{pF})$ = 3.2 GHz.",
         "- The bandwidth is $1/(2\\pi\\cdot25\\,\\Omega\\cdot1\\,\\mathrm{pF})$ = 6.4 GHz with the termination and the amplifier's input in parallel, and 3.2 GHz into the amplifier's 50 Ω alone."),
        ("- There is no swing limit at the photodiode: the RF voltage is only $50\\,\\Omega\\times i_{\\mathrm{RF}}$.",
         "- There is no swing limit at the photodiode: the RF voltage is only $(R_0/2)\\,i_{\\mathrm{RF}}$, 25 mV for 1 mA."),
        ("**Verdict.** It is a strong option for the 5–10 mA end of the range. The TIA is clearly better below 1–2 mA.",
         BENCH_REST)]),
    B("3.1", "### 2.2 The op-amp TIA: how the candidate list was built", replace=[
        ("Fully differential amplifiers (LTC6409) and integrated TIAs are listed in Sections 3.3, 3.5 and 7.7.",
         "Fully differential amplifiers (LTC6409) and integrated TIAs are listed in Sections 3.3 and 3.5."),
        ("fail on stability (Section 4).*", "fail on stability (⟦Section 6.2⟧).*")]),
    B("3.3", "### 2.3 Parts with datasheets in hand that were not analysed", replace=[
        ("The exclusion reasons below are derived here with Eq. (3) and Eq. (18) where the datasheet gives none.",
         "Table 3e lists the parts whose datasheets we read but did not analyse in full, with the reason for each. OPA817, OPA814 and LMH6609 reach only 59–75 MHz at 2 kΩ, OPA699 about 140 MHz with 11 dB more noise than the 2-kΩ floor, LTC6409 is a fully differential amplifier, and OPA857 and LMH32401 are integrated TIAs (Section 3.5). Where the datasheet gives no reason, we derive it with Eq. (3) and Eq. (18).")]),
    B("3.4", "### 2.4 Candidates found in the market scan but not modelled", replace=[
        ("These parts passed the selection rule, or came close, but no open-loop curve was digitized for them, so they do not appear in Sections 4–6.",
         "Table 3f lists the parts that passed the selection rule, or came close, but for which no open-loop curve was digitized, so they do not appear in ⟦Sections 6.2–6.4⟧. Among them, TPH2861 from 3PEAK is an OPA855-class part and a possible second source."),
        ("| The −10 version (Section 4) shows", "| The −10 version (⟦Section 6.2⟧) shows")]),
    B("3.5", "### 2.5 Single-chip TIAs", replace=[
        ("None can take 0.1–10 mA of DC at 1.5–2 kΩ (Section 7.7). Section 11.4 compares",
         "None can take 0.1–10 mA of DC at 1.5–2 kΩ, for the reasons below. Section 11.4 compares")]),
    B("7.7", None, replace=[
        ("Integrated TIAs were checked as an alternative (Sections 3.3 and 3.5), and none fits the 0.1–10 mA requirement.\n\n",
         "")]),
    T(COMPOSITES_OVERVIEW),

    T(CH3),
    B("0.2", "### 3.1 Four equations in bench units", range=(None, "*Table 0.2."), replace=[
        ("All four are derived in Section 2. Symbols:", "All four are derived in ⟦Chapter 4⟧. Symbols:")]),
    T(CH3_SUBST),
    B("0.2", None, range=("*Table 0.2.", None), replace=[
        ("| $C_F$ | 0.20 pF (resistor and pad parasitic; no discrete capacitor) | Section 4 |",
         "| $C_F$ | 0.20 pF (resistor and pad parasitic; no discrete capacitor) | ⟦Section 6.2⟧ |")]),
    T(CH3_BENCH),

    B("ch2", "## 4. TIA theory", replace=[
        ("This section derives, from the circuit of Figure 1, every equation used later, and ends at the bench-unit forms of Section 0. Symbols are defined where they first appear in each subsection.",
         CH4_INTRO)]),
    B("2.1", "### 4.1 Total input capacitance"),
    B("2.2", "### 4.2 Transimpedance, noise gain and loop gain"),
    B("2.3", "### 4.3 Single-pole closed forms: the Butterworth design", replace=[
        ("Eq. (12) becomes the form quoted in Section 0:", "Eq. (12) becomes the form quoted in ⟦Chapter 3⟧:"),
        ("- The numerical model used in Sections 4–6 reproduces", "- The numerical model used in ⟦Sections 6.2–6.4⟧ reproduces")]),
    B("2.4", "### 4.4 Decompensated amplifiers: the noise gain at crossover"),
    B("2.5", "### 4.5 The open-loop model behind every phase margin"),
    B("2.6", "### 4.6 Noise referred to the photocurrent", replace=[
        ("Eq. (17) becomes Eq. (1) of Section 0:", "Eq. (17) becomes Eq. (1) of ⟦Chapter 3⟧:")]),
    B("2.7", "### 4.7 High-frequency current noise of FET-input amplifiers: a bounded range"),
    B("2.8", "### 4.8 Dynamic range: definitions", replace=[
        ("It is stored with the results but not tabulated.", OPTICAL),
        ("With the DC photocurrent removed (Section 7),", "With the DC photocurrent removed (⟦Chapter 8⟧),"),
        ("Section 7 uses this.", "⟦Chapter 8⟧ uses this.")]),
    B("4.1", "### 4.9 How the model is evaluated, and what the datasheets say about it"),
    B("5.5", "### 4.10 A bench measurement: OPA846 at $R_F$ = 1.2 kΩ"),

    B("ch10", "## 5. SPICE cross-check with the vendors' macromodels", replace=[
        ("Sections 2–9 rest on each amplifier's datasheet open-loop curve and the hand model of Section 2. This section runs the manufacturers' SPICE macromodels of seven candidates through the same circuits:",
         CH5_INTRO),
        ("The section is organised as follows:", "The chapter is organised as follows:"),
        ("- Section 10.10 adds the further amplifiers and finds every part's best design in SPICE.",
         "- Section 10.10, in the comparison of ⟦Chapter 6⟧, adds the further amplifiers and finds every part's best design in SPICE.")]),
    B("10.1", "### 5.1 What the cross-check found"),
    B("10.3", "### 5.2 Middlebrook's double injection: what it measures, and what it adds to a plain TIA simulation"),
    B("10.4", "### 5.3 What is extracted from each macromodel, and how it predicts the closed loop"),
    B("10.5", "### 5.4 The datasheets' own test circuits as referee"),
    B("10.6", "### 5.5 The TIA designs in SPICE"),
    B("10.7", "### 5.6 Noise", replace=[
        ("Variant A's noise figures in Sections 5–7 stand.", "Variant A's noise figures in ⟦Sections 6.3, 6.4 and 8.9⟧ stand."),
        ("Each point is one design as chosen in Sections 4 and 7, not each amplifier's best",
         "Each point is one design as chosen in ⟦Sections 6.2 and 8.9⟧, not each amplifier's best")]),
    B("10.8", "### 5.7 Large-signal limits"),
    B("10.9", "### 5.8 The bench board in SPICE"),
    B("10.11", "### 5.9 What the cross-check changes in our analysis, and what it leaves open", replace=[
        ("  Section 9 lists the measurements.", "  ⟦Section 9.13⟧ lists the measurements.")]),

    T(CH6),
    B("3.2", "#### 6.1.1 Specification tables"),
    B("3.6", "#### 6.1.2 What a TIA designer must know that the tables do not show"),
    T(CH6_BW),
    B("4.2", "#### 6.2.1 Results at $R_F$ = 2 kΩ"),
    B("4.3", "#### 6.2.2 Results at $R_F$ = 1.5 kΩ"),
    B("4.4", "#### 6.2.3 Calibrated open-loop variants"),
    B("4.5", "#### 6.2.4 The feedback-capacitance window of the leading parts", replace=[
        ("vary by about ±0.1 pF (Section 1). A useful design", "vary by about ±0.1 pF (⟦Section 1.4⟧). A useful design")]),
    B("4.6", "#### 6.2.5 Sensitivity to the board: parasitic corners"),
    B("4.7", "#### 6.2.6 Decompensated amplifiers on a 1-pF photodiode: why OPA818, OPA846 and OPA847 fail, and what added capacitance buys"),
    B("4.8", "#### 6.2.7 Transimpedance responses and the bandwidth–noise trade"),
    B("4.9", "#### 6.2.8 Accepting peaking that is equalized later: how much phase margin is enough"),
    B("ch5", "### 6.3 Noise", replace=[
        ("- The ten amplifiers shown are those with a usable design at ≥ 150 MHz, plus the two short-listed parts.",
         "- The tables show ten amplifiers, those with a usable design at ≥ 150 MHz plus the two short-listed parts; Figure ⟦F:noise⟧ adds every other part with a stable flat design.")]),
    T(CH6_NOISE_FIG),
    B("5.1", "#### 6.3.1 Input-referred noise and its components"),
    B("5.2", "#### 6.3.2 Band-integrated noise"),
    B("5.3", "#### 6.3.3 Totals with photocurrent, and the output noise referred to the input", replace=[
        ("The dynamic ranges of Section 6 assume such a filter.", "The dynamic ranges of ⟦Section 6.4⟧ assume such a filter.")]),
    B("5.4", "#### 6.3.4 With DC photocurrent: shot-noise clearance"),
    T(CH6_DR),
    B("6.1", "#### 6.4.1 DC current that $R_F$ can carry: the uncorrected imbalance", replace=[
        ("limits of Section 3 gives Table 6.1.", "limits of ⟦Section 6.1⟧ gives Table 6.1."),
        ("Sections 7.2–7.6 show how to do that.", "Sections 7.2–7.5 and 7.6 show how to do that.")]),
    B("6.2", "#### 6.4.2 Largest RF amplitude"),
    B("6.3", "#### 6.4.3 Dynamic range in 150 MHz"),
    B("6.4", "#### 6.4.4 Linearity and overload recovery", replace=[
        ("| see Section 3 table |", "| see Table 3c |")]),
    T(CH6_SPICE),
    B("10.10", None),
    T(CH6_DR_SPICE),
    B("11.1", "#### 6.6.1 How the dynamic range is computed"),
    B("11.2", "#### 6.6.2 The leading op-amp designs: SPICE against our analytical model"),
    B("11.3", "#### 6.6.3 What limits the dynamic range: the OPA818 design taken apart"),
    B("11.4", "### 6.7 Single-chip TIAs", replace=[
        ("Section 3.5 listed the single-chip TIAs on the market, and Section 7.7 showed that none can carry 0.1–10 mA of DC through its input.",
         "Section 3.5 listed the single-chip TIAs on the market and showed that none can carry 0.1–10 mA of DC through its input.")]),
    T(CH6_BENCH),

    T(CH7),
    B("11.5", "### 7.1 A discrete transistor at the summing node: silicon JFET, GaAs pHEMT and SiGe bipolar composites", replace=[
        ("drives 200 Ω, as in Section 10.", "drives 200 Ω, as in ⟦Chapter 5⟧.")]),
    B("11.6", "### 7.2 A high-voltage output stage inside the $R_F$ loop", replace=[
        ("voltage noise (Section 10).", "voltage noise (⟦Chapter 5⟧).")]),
    B("11.7", "### 7.3 SPICE models, decks and convergence for the composites", replace=[
        ("loaded as a shared library with PSpice compatibility, as in Section 10.",
         "loaded as a shared library with PSpice compatibility, as in ⟦Chapter 5⟧."),
        ("| TI macromodel [S8], as in Section 10 |", "| TI macromodel [S8], as in ⟦Chapter 5⟧ |")]),

    T(CH8),
    B("7.1", "### 8.1 The constraint", replace=[
        ("Options A–E (Sections 7.2–7.6) remove a large DC current.",
         "Options A–D (Sections 7.2–7.5) remove a large DC current, and so does Option E, the 50-Ω termination of Section 7.6."),
        ("\n\nSections 7.2–7.7 compare five ways of removing a large DC current, and the integrated TIAs. Sections 7.8 and 7.9 explain bootstrapping and cascoding the photodiodes. Section 7.10 covers servos for the imbalance and for the photodiode bias, and why they are hard to make quiet. Section 7.11 gives the proposed balanced front end in two variants, OPA855 and OPA818, and Section 7.12 lists what not to do.",
         "")]),
    B("7.2", "### 8.2 Option A (recommended for a single-ended detector): resistive DC sink at the summing node, driven by a slow servo", replace=[
        ("corners of Section 4.", "corners of Section 4.6.")]),
    B("7.3", "### 8.3 Option B: photodiode AC-coupled into the TIA, DC returned through a bias resistor"),
    B("7.4", "### 8.4 Option C: inductive bias tee at the summing node"),
    B("7.5", "### 8.5 Option D: two-stage split gain"),
    B("7.8", "### 8.6 Bootstrapping the photodiodes"),
    B("7.9", "### 8.7 Cascoding the photodiodes"),
    B("7.10", "### 8.8 Servos for the imbalance and for the photodiode bias"),
    B("7.11", "### 8.9 The proposed balanced front end: two variants", replace=[
        ("(note below)", "(see the note on the flagged corners in Section 7.11)"),
        ("**What the vendors' SPICE macromodels add (Section 10).** The tables above use the datasheet open-loop curves.",
         "**What the vendors' SPICE macromodels add (⟦Chapter 5⟧).** Tables 7.12 and 7.13 use the datasheet open-loop curves.")]),
    B("8.3", "### 8.10 Starting component values"),
    B("7.12", "### 8.11 What not to do"),

    T(CH9),
    B("0.1", "### 9.1 The three decisions that settle the choice", replace=[
        ("With nominal parasitics (Section 1), the parts", "With nominal parasitics (⟦Section 1.4⟧), the parts"),
        ("OPA847 (minimum stable gain 12) reaches only 9°. Section 4 has the derivation and the validation against TI's own TIA data.",
         "OPA847 (minimum stable gain 12) reaches only 9°. ⟦Sections 4.4 and 4.9⟧ give the derivation and the validation against TI's own TIA data, and ⟦Section 6.2.6⟧ the results.")]),
    B("0.6", "### 9.2 What the SPICE cross-check changes"),
    B("0.7", "### 9.3 Dynamic range: what sets it, single-chip TIAs and composite front ends"),
    B("11.8", "### 9.4 The verdict on dynamic range and on the composites"),
    T(CH9_BENCH),
    B("0.3", "### 9.6 The leading amplifiers at a glance", replace=[
        ("Conventions for the table below:",
         "Table 0.3 collects the figures of the eight leading amplifiers at 2 kΩ. Its columns follow these conventions:")]),
    B("8.1", "### 9.7 Ranking and the reasons behind it"),
    B("8.2", "### 9.8 The picks in brief"),
    B("0.4", "### 9.9 The picks in detail", replace=[
        ("Its dark noise there is up to 1.6 dB higher than estimated here (Section 10).",
         "Its dark noise there is up to 1.6 dB higher than estimated here (⟦Chapter 5⟧).")]),
    T(CH9_SIDE),
    B("8.4", None),
    B("8.5", "### 9.11 Flags: marginal, parasitic-sensitive, or needing simulation"),
    B("0.5", "### 9.12 The noise floor referred to the photocurrent, and the instrument it tolerates"),
    B("ch9", "### 9.13 What only SPICE or a measurement can settle", replace=[
        ("Section 10 has since run the manufacturers' macromodels; items 1–4 say what that settled.",
         "⟦Chapter 5⟧ runs the manufacturers' macromodels; items 1–4 say what that settles.")]),

    T(APPENDIX_A),
    T(APPENDIX_B),
    B("10.2", "### B.1 Running ngspice from a script: a working guide", replace=[
        ("`spice_tia_checks.py` writes every deck of this section into its own folder",
         "`spice_tia_checks.py` writes every deck of ⟦Chapter 5⟧ into its own folder"),
        ("`spice_report_tables.py` turns those into the tables below.",
         "`spice_report_tables.py` turns those into the tables of ⟦Chapter 5⟧.")]),
    B("10.12", "### B.2 Reproducing the runs", replace=[
        ("`dr_comparison.py` (Section 11) and", "`dr_comparison.py` (⟦Section 6.6⟧) and"),
        ("   - the tables of this section in `spice/results/tables.md`.",
         "   - the tables of ⟦Chapter 5⟧ in `spice/results/tables.md`.")]),
    B("app1", "## Appendix C. Open questions and unknowns", replace=[
        ("None changes the ranking of Section 8, except possibly items 1 and 2.",
         "None changes the ranking of ⟦Section 9.7⟧, except possibly items 1 and 2."),
        ("They enter Sections 2.6, 6 and 9.", "They enter ⟦Sections 4.6, 6.4 and 9.13⟧."),
        ("None of these parts is among the ten in Sections 5–6, so those tables are unaffected.",
         "None of these parts is among the ten in ⟦Sections 6.3 and 6.4⟧, so those tables are unaffected."),
        ("Variant B's margins in Sections 4, 7 and 8 rest on the curve, Section 10 on the model.",
         "Variant B's margins in ⟦Sections 6.2, 8.9 and 8.10⟧ rest on the curve, those of ⟦Chapter 5⟧ on the model."),
        ("Its margins in Section 10 are therefore optimistic.", "Its margins in ⟦Chapter 5⟧ are therefore optimistic.")]),
    B("app2", "## Appendix D. References"),
    B("app2:datasheets", "### Datasheets", replace=[
        ("Amplifiers: every part of Section 3 (one per row).*", "Amplifiers: every part of ⟦Section 6.1⟧ (one per row).*")]),
    B("app2:application_notes_and_articles", "### Application notes and articles"),
    B("app2:books", "### Books"),
    B("app2:simulator_and_simulation_models", "### Simulator and simulation models (⟦Chapters 5–7⟧)"),
    B("app3", "## Appendix E. Files", replace=[
        ("| `figures/` | Figures 1–16 as PNG (600 dpi) and PDF; Figures 7–14 (Section 10) and 15–16 (Section 11) from `scripts_archive/make_spice_figures.py` |",
         FILES_FIGURES),
        ("| `datasheets/` | datasheets of every part in Section 3;", "| `datasheets/` | datasheets of every part of ⟦Chapters 2 and 6⟧;"),
        ("| `data/results/tables.md` | tables generated from it (Sections 3–6) |",
         "| `data/results/tables.md` | tables generated from it (⟦Sections 6.1–6.4⟧) |"),
        ("| `data/results/report_numbers.md` | secondary tables (Sections 0, 5 and 6), including",
         "| `data/results/report_numbers.md` | secondary tables (⟦Sections 6.3, 6.4 and 9.12⟧), including"),
        ("every ngspice deck of Section 10 with its log and data files",
         "every ngspice deck of ⟦Chapter 5⟧ and ⟦Section 6.5⟧ with its log and data files"),
        ("`tables.md` with the tables of Section 10, and `dr_comparison.json` with the dynamic-range comparison of Section 11 (`scripts_archive/dr_comparison.py`) |",
         "`tables.md` with the tables of ⟦Chapter 5⟧, and `dr_comparison.json` with the dynamic-range comparison of ⟦Section 6.6⟧ (`scripts_archive/dr_comparison.py`) |"),
        ("| `data/results/composite_analytical.json`, `composite_hv_fine_scan.json` | the analytical scans of Sections 11.5–11.6 (`scripts_archive/composite_tia.py`; the fine scan with `--fine`) |",
         FILES_BENCH_ROW),
        ("`composite_report_numbers.py` and `fet_front_end/phemt_stability_factors.py` |",
         "`composite_report_numbers.py` and `fet_front_end/phemt_stability_factors.py`; the 50-Ω benchmark and the charts of ⟦Chapter 6⟧ use `benchmark_50ohm.py` and `make_narrative_figures.py` |")]),
    B("app4", "## Appendix F. Datasheet inconsistencies found during extraction", replace=[
        ("- Figure 3 shows 12 kΩ ∥ 0.1 µF ∥ 100 pF on +IN;", "- The datasheet's Fig. 3 shows 12 kΩ ∥ 0.1 µF ∥ 100 pF on +IN;")]),
]


def _new_table_refs(s):
    """'Table N1', 'Tables N2 and N3' in new text -> bracketed new-table markers.  A caption line
    keeps its own id plain ('*Table N1. ...'), so that the engine moves it to Appendix A."""
    def wrap(m):
        return m.group(1) + re.sub(r"N\d", lambda k: L + "T:" + k.group(0) + R, m.group(2))

    out = []
    for line in s.split("\n"):
        head = ""
        if line.startswith("*Table N"):
            head, line = line.split(". ", 1)
            head += ". "
        out.append(head + re.sub(r"\b(Tables? )(N\d(?:(?:, and |, | and |–)N\d)*)", wrap, line))
    return "\n".join(out)


def _apply(item):
    if item[0] == "text":
        return ("text", _new_table_refs(item[1]))
    kind, key, heading, opts = item
    if "replace" in opts:
        opts = dict(opts, replace=[(a, _new_table_refs(b)) for a, b in opts["replace"]])
    return (kind, key, heading, opts)


PLAN = [_apply(i) for i in PLAN]
