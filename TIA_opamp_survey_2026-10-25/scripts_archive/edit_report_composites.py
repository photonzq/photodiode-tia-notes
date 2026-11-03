"""One-off report edit of 27 Oct 2026: the composite TIAs.  Section 11.5 is extended with the
discrete-transistor composites (silicon JFET, GaAs pHEMT and SiGe bipolar; Eqs. (66)-(70), Tables
11.5-11.6, the literature [A23]-[A24], and the bias, package and layout of RF transistors at the
summing node), Section 11.6 is the high-voltage output stage (Eqs. (71)-(75), Tables 11.7-11.11),
Section 11.7 the SPICE models, decks and convergence (Tables 11.12-11.13), and the verdict becomes
Section 11.8; the reading guide, Section 0.7, Section 11's introduction and Appendices 1-4 follow.

Every edit is anchored on whole lines (or one exact phrase) that must occur exactly once, so the
script stops without writing if the report has changed underneath it.  The numbers come from
composite_report_numbers.py, composite_tia.py --fine and the saved results of
spice_composite_checks.py.

Usage: python edit_report_composites.py <TIA_opamp_survey.md>
"""
import sys
from pathlib import Path


def _index(lines, prefix):
    idx = [i for i, l in enumerate(lines) if l.startswith(prefix)]
    assert len(idx) == 1, (prefix[:70], len(idx))
    return idx[0]


def replace_line(t, prefix, new):
    lines = t.split("\n")
    lines[_index(lines, prefix)] = new
    return "\n".join(lines)


def append_after(t, prefix, extra):
    lines = t.split("\n")
    i = _index(lines, prefix)
    lines[i] = lines[i] + "\n" + extra
    return "\n".join(lines)


def replace_block(t, start, end, new):
    """Replace the lines from the one starting with `start` up to, not including, the one starting
    with `end`."""
    lines = t.split("\n")
    s, e = _index(lines, start), _index(lines, end)
    assert s < e, (start[:40], end[:40])
    return "\n".join(lines[:s] + new.split("\n") + lines[e:])


def replace_once(t, old, new):
    assert t.count(old) == 1, (old[:70], t.count(old))
    return t.replace(old, new)


# ------------------------------------------------------------------ reading guide and Section 0.7
READ_OLD = "takes one design apart to show what sets it, and asks what a discrete-FET front end would add."
READ_NEW = ("takes one design apart to show what sets it, asks what a discrete transistor at the summing node "
            "would add, and puts a high-voltage output stage inside the feedback loop.")

S07_HEAD_OLD = "### 0.7 Dynamic range: what sets it, single-chip TIAs and a FET front end (Section 11)"
S07_HEAD_NEW = "### 0.7 Dynamic range: what sets it, single-chip TIAs and composite front ends (Section 11)"

S07_FET_OLD = "- **A discrete-FET composite front end cannot gain more than that 0.8 dB over OPA855 at 0.1 mA.**"
S07_NEW = r"""- **A discrete transistor at the summing node can match the best op amp's noise but cannot raise the dynamic range from 0.1 mA up.** Silicon JFETs bring 6–7 pF to a node of 1.6 pF, so their cascoded composites stay below 150 MHz (98–141 MHz at the worst capacitance corner) and are noisier than OPA855 (53.5–55.4 nA rms against 49.6 nA). A GaAs pHEMT (CE3512K2) and a SiGe bipolar transistor (BFP740ESD at 1 mA) give composites that are robust at 150 MHz with 36.5 and 39.1 nA rms, about OPA955's 38.8 nA, because they deliver 46–259 mS of transconductance per picofarad of input capacitance against 5–7 mS/pF for the JFETs. From 0.1 mA up the photocurrent's shot noise hides the difference, within the bound of 0.8 dB over OPA855 at 0.1 mA. In hardware the pHEMT's negative gate voltage, its unspecified gate current and baseband noise, and its stability at microwave frequencies need care (Section 11.5, Tables 11.5–11.6).
- **A fast high-voltage amplifier inside the $R_F$ loop raises the ceiling and gains about 11 dB at 1 mA.** OPA859 driving a THS3491 at a gain of 4–5.5, with a capacitor $C_L$ from the OPA859's output to the summing node, is robust over every capacitance corner (45.0–45.6° of worst-case phase margin, 152–171 MHz of worst-case bandwidth) and swings 6.0–8.3 V at 100 MHz, against 2.23 V for OPA818. At a gain of 5.5 its dynamic range at 100 MHz is 87.3, 86.4, 81.8 and 73.1 dB at 0, 0.1, 1 and 10 mA, 7.8–11.9 dB above OPA818, although its noise (136.5 nA rms) is 1.6 times OPA818's. Without $C_L$ the composite is unstable at every gain from 3 up. At full swing at 100 MHz it carries about −54 dBc HD2 and −47 dBc HD3, because the loop does not suppress the THS3491's harmonics there; a −55-dBc limit on every harmonic would hold the output to 2.5 V and the dynamic range at 1 mA to 71.3 dB (Section 11.6, Tables 11.9–11.10).
- **SPICE runs of the vendors' models confirm the analyses of both composites.** Over 52 designs at nominal capacitances, 48 of them stable, the phase margins agree within 1.3° (within 5.5° for two unstable pHEMT designs that cross over above 1.2 GHz), the gain margins within 0.4 dB and the band noise within 1.0 %. At the worst corner of each design of Tables 11.6 and 11.9 they agree within 0.2° and 0.5 dB. Section 11.7 lists the models, the 406 decks and every convergence message met."""

# ------------------------------------------------------------------ Section 11 heading and introduction
S11_HEAD_OLD = "## 11. Dynamic range compared: the leading designs in SPICE, what limits them, single-chip TIAs and a FET front end"
S11_HEAD_NEW = "## 11. Dynamic range compared: the leading designs in SPICE, what limits them, single-chip TIAs and composite front ends"
S11_LIST_START = "- Section 11.5 asks whether a discrete-FET composite front end would lower the floor enough to matter"
S11_LIST_END = "### 11.1 How the dynamic range is computed"
S11_LIST_NEW = r"""- Section 11.5 asks whether a discrete transistor at the summing node, a silicon JFET, a GaAs pHEMT or a SiGe bipolar transistor, would lower the floor enough to matter, and designs and verifies such composites (Tables 11.3–11.6).
- Section 11.6 raises the ceiling instead, with a fast high-voltage amplifier inside the $R_F$ loop: its stability, noise, slew rate, distortion and power (Tables 11.7–11.11).
- Section 11.7 documents the SPICE models and decks of Sections 11.5–11.6 and the convergence messages met (Tables 11.12–11.13).
- Section 11.8 gives the verdict.
"""

# ------------------------------------------------------------------ Section 11.5
S115_HEAD_OLD = "### 11.5 A discrete-FET composite front end"
S115_HEAD_NEW = "### 11.5 A discrete transistor at the summing node: silicon JFET, GaAs pHEMT and SiGe bipolar composites"
B4_OLD = "- A two-stage loop with a microwave transistor inside it needs its own stability design."
B4_NEW = ("- A loop with a microwave transistor inside it must be stable twice: at baseband, which the compensation of "
          "Eqs. (67)–(68) below secures, and at microwave frequencies, where the transistor alone is potentially unstable "
          "and only the layout can secure it (bias, package and layout, below).")
EVEN_PREFIX = "Even if all four go right, the gain over OPA855 in the receiver's range is at most"

S115_INSERT = r"""
**Why a pHEMT or a SiGe bipolar transistor rather than a silicon JFET.** At a node of a few picofarads, what decides is not the input capacitance alone but the transconductance a device delivers per picofarad of the capacitance it adds, $g_m/C_{\mathrm{iss}} = 2\pi f_T$, the quantity that sets Eq. (65). Above a few tens of megahertz the part of a FET front end's input-referred noise that depends on the device is its voltage noise acting on all the capacitance at the summing node,

$$
i_{n,e}(f) = e_n\,2\pi f\,C_T,
\qquad
e_n^2 = \frac{4k_BT\Gamma}{g_m},
\tag{66}
$$

the $e_n$ term of Eq. (62). Lowering $e_n$ needs a large $g_m$. In a JFET of a given technology that means a wider channel, and the gate capacitance grows in proportion, so the designer can only match $C_{\mathrm{iss}}$ to the rest of the node (Eq. (65)) and must accept the $f_T$ that the technology gives. The way past that compromise is a device with a higher $f_T$, which delivers the same $g_m$ from less capacitance.

Two properties of a device set its $f_T$. The first is how fast its carriers move: the electrons of a pHEMT travel in an InGaAs quantum well, where their mobility at room temperature is several times that in a silicon channel. The second, and larger, is the gate length, since $f_T$ scales with the carrier velocity divided by the gate length, or with the mobility divided by its square in a long channel. Microwave pHEMTs are made with gates a fraction of a micrometre long, while the diffused junction gates of discrete silicon JFETs are several micrometres long. The datasheets of Table A2.3 do not state the gate length; these are general properties of the two technologies. A SiGe heterojunction bipolar transistor reaches a high $f_T$ by another route. Its transconductance is set by the collector current alone, $g_m = qI_C/k_BT$ = 38.9 mS per mA at 298 K, whatever the transistor's size, and its thin, graded base keeps the charge-storage capacitance $g_m\tau_F$ small ($\tau_F$ = 2.15 ps in Infineon's BFP740ESD model [S22]).

Table 11.5 gives the devices at the operating points of the composites below, from their SPICE models. CPH3910 delivers 41.0 mS from 6.01 pF of input capacitance, 6.8 mS per picofarad, and LSBF862 35.2 mS from 7.27 pF, 4.8 mS/pF. CE3512K2 delivers 69.0 mS from 0.27 pF, 259 mS/pF. BFP740ESD delivers 36.8–304 mS from 0.79–1.34 pF at 1–10 mA, 46–226 mS/pF; about 0.5 pF of that capacitance lies outside the transistor itself, in the model's pad, package and protection network. At 100 MHz the term of Eq. (66) is

$$
i_{n,e} = 0.52\ \mathrm{nV/\sqrt{Hz}} \times 2\pi \times 100\ \mathrm{MHz} \times 9.9\ \mathrm{pF} = 3.2\ \mathrm{pA/\sqrt{Hz}}
$$

for CPH3910 at its $C_T$ = 9.9 pF (Table 11.4), more than the 2.9 pA/√Hz of $R_F$ itself, and

$$
i_{n,e} = 0.40\ \mathrm{nV/\sqrt{Hz}} \times 2\pi \times 100\ \mathrm{MHz} \times 1.87\ \mathrm{pF} = 0.47\ \mathrm{pA/\sqrt{Hz}}
$$

for CE3512K2 at its 1.87 pF. The pHEMT's term is seven times smaller although its $e_n$ is only 1.3 times lower: most of the difference is capacitance that the device does not add. The same capacitance sets the bandwidth. A loop with one dominant pole reaches a closed-loop bandwidth $f_{3\,\mathrm{dB}}$ only with a gain–bandwidth product of about $2\pi R_FC_Tf_{3\,\mathrm{dB}}^2$: 2.8 GHz for 150 MHz with the JFET's 9.9 pF, and 0.53 GHz with the pHEMT's 1.87 pF.

What the pHEMT gives up is everything a microwave transistor is not specified for. Its gate is a Schottky barrier whose leakage is specified in microamperes, not the picoamperes to nanoamperes of a silicon JFET's junction; its noise is specified only from 0.5 GHz up (CE3512K2's from 8 GHz); and it is potentially unstable at microwave frequencies. The bipolar transistor gives up a base current, whose shot noise $2qI_B = 2qI_C/\beta$ is known and grows with the bias current. In exchange it comes with a vendor SPICE model, a current gain specified between limits, integrated ESD protection and specified DC characteristics. Silicon JFETs remain the right choice for photodiodes of tens of picofarads, where their large $C_{\mathrm{iss}}$ matches the node, and at low frequencies, where their picoampere gate current and low 1/f noise matter.

**Such front ends in the literature.** Discrete GaAs FETs of this kind have been used at photodiode nodes in quantum-optics detectors. Serikawa and Furusawa [A23] buffer two 2.0-pF silicon photodiodes, 4.6 pF together with the amplifier's input, with a source follower made of CEL's NE3509M04 hetero-junction FET (0.28 nV/√Hz), ahead of a Mini-Circuits CMA-5043+ monolithic microwave amplifier, in a resonant 500-MHz homodyne detector (Sec. III A, p. 4, Fig. 4 and Table I of the arXiv version). They prefer the hetero-junction FET to a bipolar transistor because of the base current's shot noise. They put 150 Ω in series with the gate to stop the follower from oscillating at several gigahertz, with 10 nH in parallel to reduce the resistor's thermal noise at 500 MHz, and they hold the gate at 0 V through ferrite beads and set 10 mA with a 47-Ω source resistor. Bowden, Vianello and Hobson [A24] put a common-source CEL GaAs FET (CE3521M4 in the text, CE3514M4 in Fig. 1; the paper calls it a JFET) between a 2-pF photodiode and an LMH6624 op amp in a resonant 90-MHz detector (Fig. 1, p. 1). They report 1.2 pA/√Hz against the 1.0 pA/√Hz Johnson limit of its 16-kΩ transimpedance, and state that their prototypes with the op amp alone did not get below 3 pA/√Hz at 50 MHz and above (pp. 1–2). Both detectors are resonant, so neither needs a broadband loop with phase margin. The composites below carry the same idea into a broadband TIA with feedback through $R_F$.

**The composite circuit.** The input transistor Q1 works in common source (common emitter) with its gate (base) at the summing node $v_g$. A second transistor of the same type, Q2, works in common gate (common base) above it at node $v_x$, with its gate held at a fixed bias. A resistor $R_D$ runs from $V_{DD}$ = 15 V to Q2's drain $v_d$, a compensation capacitor $C_N$ from $v_d$ to ground, and OPA859 serves as a unity-gain buffer from $v_d$, through a DC level shift, to the output $v_o$. $R_F \parallel C_F$ returns from $v_o$ to the gate, and the buffer also drives 200 Ω, as in Section 10.
- The cascode removes the Miller multiplication of Q1's gate–drain capacitance, so $C_{\mathrm{rss}}$ counts twice in $C_T$ and not $g_mR_D$ times (Eq. (62)).
- The voltage gain from gate to drain at low frequencies is $g_m$ times $R_D$ in parallel with the cascode's output resistance: 9–13 for the JFETs, about 70 for the pHEMT and 350–430 for the bipolar transistor. The gain–bandwidth product is $g_m/2\pi(C_N + C_d)$, where $C_d$ is the capacitance already at the drain node: Q2's gate–drain (collector–base) capacitance and the buffer's 0.62 pF of input capacitance.
- $R_D$'s Johnson current, referred to the gate, is a voltage noise $\sqrt{4k_BT/R_D}/g_m$ in series with Q1's own. A JFET that needs 19–32 mA for its $g_m$ leaves only 220–360 Ω for $R_D$ from the 15-V supply, which adds 0.19–0.21 nV/√Hz; the pHEMT at 10 mA has 1.1 kΩ and 0.06 nV/√Hz.
- The level shift is an ideal DC source in the simulations and sets the drain voltage. The summing node, and with it the output, sits at the DC voltage that the input transistor needs for its drain current (bias, package and layout, below).

Each transistor is described by its common-source two-port admittances at its own operating point: $y_{11}$, $y_{12}$, $y_{21}$ and $y_{22}$ for Q1, and $y'_{11}$ to $y'_{22}$ for Q2, whose gate–source voltage is $-v_x$ and drain–source voltage $v_d - v_x$. The buffer is described by its gain $B$ and input admittance $Y_b$, and $Y_x = j\omega(C_D + C_{\mathrm{PCB}})$ and $Y_F = 1/R_F + j\omega C_F$. The three node equations are then

$$
\begin{aligned}
(Y_x + Y_F + y_{11})\,v_g + y_{12}\,v_x - Y_F B\,v_d &= i_{\mathrm{in}},\\
y_{21}\,v_g + (y_{22} + S')\,v_x - (y'_{12} + y'_{22})\,v_d &= 0,\\
-(y'_{21} + y'_{22})\,v_x + \Big(\frac{1}{R_D} + j\omega C_N + Y_b + y'_{22}\Big)\,v_d &= 0,
\end{aligned}
\tag{67}
$$

with $S' = y'_{11} + y'_{12} + y'_{21} + y'_{22}$, $v_o = Bv_d$ and $Z_T = v_o/i_{\mathrm{in}}$. The loop gain at the buffer's output, where SPICE injects (Section 10.3), follows from the same equations with $i_{\mathrm{in}}$ = 0, the term $-Y_FBv_d$ taken out of the first row, and the feedback side of $R_F \parallel C_F$ driven by 1 V, which puts $Y_F$ on the right of the first row:

$$
T = -B\,v_d.
\tag{68}
$$

Every noise source enters the same equations at its own node, and its input-referred density is its contribution to $v_o$ divided by $Z_T$.
- $R_F$'s Johnson current, a FET's gate current (shot noise $2qI_G$) and a bipolar transistor's base current ($2qI_B$) enter at $v_g$ and are referred to the input unchanged.
- A FET's channel noise is a current $y_{21}e_n$ from drain to source, with $e_n$ its input voltage noise with the gate AC-grounded. Because this current moves the gate, every capacitance at the node carries noise current, the transistor's own $C_{gs}$ included, as Eq. (62) assumes.
- A bipolar transistor's collector shot noise, $2qI_C$, enters at $v_x$ in the same way. The thermal noise of its base resistance $r_b$, $4k_BTr_b$, is instead a voltage in series with the base terminal: the loop holds the transistor's own base–emitter voltage, so this noise moves the summing node without driving the transistor's input capacitance.
- $R_D$'s current enters at $v_d$, Q2's channel or collector noise flows from $v_d$ to $v_x$, and the buffer's voltage noise adds at its input.

For a bipolar transistor these sources give, to first order,

$$
e_n^2 = \frac{2(k_BT)^2}{qI_C} + 4k_BTr_b,
\qquad
i_n^2 = \frac{2qI_C}{\beta},
\tag{69}
$$

so a larger collector current lowers $e_n$ and raises $i_n$. For BFP740ESD at 1 mA, with $r_b$ = 6.41 Ω (the RB and RE of Infineon's model [S22]), $e_n^2 = 2(4.116\times10^{-21}\ \mathrm{J})^2/(1.602\times10^{-19}\ \mathrm{C} \times 1\ \mathrm{mA}) + 4 \times 4.116\times10^{-21}\ \mathrm{J} \times 6.41\ \Omega$ = $2.12\times10^{-19} + 1.06\times10^{-19}\ \mathrm{V^2/Hz}$, so $e_n$ = 0.56 nV/√Hz, and with $\beta$ = 365, $i_n$ = 0.94 pA/√Hz. At 9.97 mA, $e_n$ = 0.36 nV/√Hz and, with $\beta$ = 302, $i_n$ = 3.25 pA/√Hz, more than the 2.9 pA/√Hz of $R_F$. The device data come from ngspice at each composite's own operating point (Section 11.7).

*Table 11.5. The transistors at the operating points of the composites, from their SPICE models at 1 MHz: bias; transconductance $g_m$ = Re($y_{21}$); input capacitance $C_{11}$ = Im($y_{11}$)/ω, with the gate–drain capacitance, package and protection network included, and gate–drain capacitance $C_{gd}$ = −Im($y_{12}$)/ω; output conductance $g_{ds}$ = Re($y_{22}$); $g_m/C_{11}$ and $f_T = g_m/2\pi C_{11}$; the input voltage noise $e_n$ with the gate AC-grounded; and the input current noise. LSBF862: Linear Systems' model [S23]; CPH3910 and CE3512K2: cards built from their datasheets (Section 11.7); BFP740ESD: Infineon's model [S22] with the emitter at −$V_{BE}$. Amplifiers (discrete transistors): LSBF862, CPH3910, CE3512K2, and BFP740ESD at 1, 3 and 10 mA (one per row).*

| Transistor | Bias | $g_m$ (mS) | $C_{11}$ / $C_{gd}$ (pF) | $g_{ds}$ (mS) | $g_m/C_{11}$ (mS/pF) / $f_T$ (GHz) | $e_n$ (nV/√Hz) | Input current noise (pA/√Hz) |
|---|---|---|---|---|---|---|---|
| LSBF862 (Si JFET) | 19.0 mA, $V_{DS}$ 4.84 V | 35.2 | 7.27 / 1.12 | 0.37 | 4.8 / 0.77 | 0.57 | negligible |
| CPH3910 (Si JFET) | 31.6 mA, $V_{DS}$ 4.93 V | 41.0 | 6.01 / 2.30 | 0.63 | 6.8 / 1.09 | 0.52 | negligible |
| CE3512K2 (GaAs pHEMT) | 10.0 mA, $V_{DS}$ 2.00 V, $V_{GS}$ −0.50 V | 69.0 | 0.27 / 0.028 | 2.50 | 259 / 41.2 | 0.40 | 0.57 ($I_G$ = 1 µA, assumed) |
| BFP740ESD (SiGe HBT) | 1.00 mA, $V_{CE}$ 2.03 V | 36.8 | 0.79 / 0.10 | 0.006 | 46 / 7.4 | 0.58 | 0.94 ($\beta$ = 365) |
| BFP740ESD | 2.99 mA | 104.8 | 0.94 / 0.10 | 0.018 | 111 / 17.7 | 0.44 | 1.66 ($\beta$ = 349) |
| BFP740ESD | 9.97 mA | 303.6 | 1.34 / 0.10 | 0.059 | 226 / 36.0 | 0.36 | 3.25 ($\beta$ = 302) |

**What the composites achieve.** Table 11.6 gives, for each transistor, the design that is robust over every capacitance corner and has the largest dynamic range at 0.1 mA, from a scan of $C_N$ = 0–100 pF and $C_F$ = 0.10–1.50 pF. The criteria are those of Section 4.5 over the corners of Section 10.6: phase margin ≥ 45°, gain margin ≥ 3 dB and peaking ≤ 1 dB at every combination of $C_D$ ± 0.2 pF and $C_F$ ± 0.1 pF, and here also $f_{3\,\mathrm{dB}}$ ≥ 150 MHz. Where no design is robust, the table gives the widest-band design that keeps the margins. SPICE confirms Eqs. (67)–(68) on 36 designs at nominal capacitances, 18 with each kind of transistor ($C_N$ = 0–60 pF, $C_F$ = 0.20–0.60 pF). The 34 that are stable agree with the analysis within 0.8° of phase margin, 0.4 dB of gain margin, 1.4 MHz of bandwidth and 0.6 nA (1.0 %) of band noise; the two unstable ones, CE3512K2 without $C_N$, cross over above 1.2 GHz and differ by up to 5.5°. At the worst of the nine corners of each design in Table 11.6, SPICE and the analysis agree within 0.1° and 0.5 dB.
- **The silicon JFETs do not reach 150 MHz.** With about 10 pF at the node they need about 2.8 GHz of gain–bandwidth (above), and their cascodes give 2.2–2.9 GHz with no compensation capacitor at all ($g_m/2\pi C_d$ with $C_d$ = 1.96 and 2.93 pF). LSBF862 reaches 141 MHz at the worst corner (164 MHz nominal) with no compensation capacitor, and CPH3910, whose widest-band design that keeps the margins has $C_N$ = 2 pF, 98 MHz (110 MHz). Their band noise, 53.5 and 55.4 nA, is above OPA855's 49.6 nA. Their voltage noise on about 10 pF contributes 25.9–33.4 nA. Eq. (63) leaves out the second stage and the drain resistor, and in the composite they add 18.5–29.3 nA from the buffer, whose noise the small gate-to-drain gain at high frequencies does not suppress, and 12.9–14.0 nA from $R_D$; that is why CPH3910's 49.4 nA in Table 11.4 becomes 55.4 nA here.
- **The pHEMT composite is robust with $C_N$ = 8 pF and $C_F$ = 0.55 pF.** It has 51.6° of phase margin and 152 MHz at the worst corner (199 MHz nominal). Its 36.5 nA is 35.1 nA of $R_F$ with 6.9 nA from the assumed 1 µA of gate current, 6.3 nA from the channel and 4.5 nA from the buffer. The 8 pF of compensation it needs shows how much gain–bandwidth the pHEMT has to spare.
- **The bipolar composite is robust at every bias current tried.** At 1 mA ($C_N$ = 4 pF, $C_F$ = 0.60 pF) it has 46.3° and 155 MHz at the worst corner and 39.1 nA, of which 11.5 nA is base current, 9.6 nA collector shot noise and 4.7 nA base resistance. Raising the collector current to 3 and 10 mA lowers $e_n$ but raises the base-current noise, so the band noise rises to 41.7 and 54.0 nA. For this node 1 mA is close to the optimum of Eq. (69), and there the composite matches OPA955's 38.8 nA within 0.3 nA.
- **The dynamic range follows.** With the buffer's ceiling of 1.5 V at 100 MHz, which assumes the output is centred in the buffer's range (bias, package and layout, below), Eq. (56) gives 84.2, 77.5, 68.5 and 58.6 dB at 0, 0.1, 1 and 10 mA for the pHEMT composite and 83.3, 77.1, 68.2 and 58.3 dB for the bipolar composite at 1 mA, against 82.9, 76.7, 67.8 and 57.9 dB for OPA955 (Table 11.1). Their transimpedance is 7–10 % low at 100 MHz (1.80–1.85 kΩ), which Eq. (56) credits, as Section 11.2 explains for LMH6629. With $\lvert Z_T\rvert$ = $R_F$ the pHEMT composite gives 83.2, 76.6, 67.6 and 57.7 dB and ties OPA955 within 0.3 dB from the dark to 10 mA, inside the bound of Table 11.3.

*Table 11.6. Discrete-transistor composites at 1 pF and 2 kΩ: compensation $C_N$ and total $C_F$; phase margin, gain margin, peaking and $f_{3\,\mathrm{dB}}$ at the worst of the nine corners ($C_D$ ± 0.2 pF, $C_F$ ± 0.1 pF), from SPICE with the analytical value of Eqs. (67)–(68) in brackets; nominal $f_{3\,\mathrm{dB}}$; band noise over 0–150 MHz from SPICE, with its analytical parts; transimpedance at 100 MHz; dynamic range at a 100-MHz tone by Eq. (56) with the buffer's 1.5 V, and with $\lvert Z_T\rvert$ = $R_F$. The JFET designs do not reach 150 MHz. Amplifiers (composites): LSBF862, CPH3910, CE3512K2, and BFP740ESD at 1, 3 and 10 mA, each with the OPA859 buffer (one per row).*

| Front end | $C_N$ / $C_F$ (pF) | Worst PM (°), GM (dB), peaking (dB), $f_{3\,\mathrm{dB}}$ (MHz) | Nominal $f_{3\,\mathrm{dB}}$ (MHz) | Band noise (nA rms) and its main parts | $\lvert Z_T\rvert$ at 100 MHz (kΩ) | DR at 0 / 0.1 / 1 / 10 mA (dB): Eq. (56); with $\lvert Z_T\rvert = R_F$ |
|---|---|---|---|---|---|---|
| LSBF862 | 0 / 0.10 | 60.3 (60.3), 14.1 (14.1), 0.63 (0.63), 141 (141) | 164 | 53.5: $R_F$ 35.1, channel 33.4, buffer 18.5, $R_D$ 12.9, Q2 7.0 | 1.79 | 80.9 / 76.6 / 68.4 / 58.6; 79.9 / 75.6 / 67.4 / 57.6 |
| CPH3910 | 2 / 0.10 | 67.2 (67.2), 18.8 (18.8), 0.17 (0.16), 98 (98) | 110 | 55.4: $R_F$ 35.1, buffer 29.3, channel 25.9, $R_D$ 14.0, Q2 8.8 | 1.39 | 82.8 / 78.7 / 70.6 / 60.8; 79.6 / 75.5 / 67.4 / 57.6 |
| CE3512K2 | 8 / 0.55 | 51.6 (51.5), 12.2 (12.7), 0.02 (0.02), 152 (152) | 199 | 36.5: $R_F$ 35.1, gate 6.9, channel 6.3, buffer 4.5 | 1.80 | 84.2 / 77.5 / 68.5 / 58.6; 83.2 / 76.6 / 67.6 / 57.7 |
| BFP740ESD, 1 mA | 4 / 0.60 | 46.3 (46.2), 11.1 (11.4), 0.21 (0.21), 155 (155) | 201 | 39.1: $R_F$ 35.1, base 11.5, collector 9.6, buffer 5.7, $r_b$ 4.7 | 1.85 | 83.3 / 77.1 / 68.2 / 58.3; 82.6 / 76.5 / 67.5 / 57.7 |
| BFP740ESD, 3 mA | 8 / 0.55 | 46.7 (46.7), 8.8 (9.1), 0.00 (0.00), 153 (153) | 207 | 41.7: $R_F$ 35.1, base 20.3, collector 6.3, $r_b$ 4.6, buffer 3.9 | 1.81 | 82.9 / 77.2 / 68.4 / 58.5; 82.1 / 76.3 / 67.5 / 57.7 |
| BFP740ESD, 10 mA | 20 / 0.50 | 49.2 (49.2), 8.6 (8.9), 0.00 (0.00), 153 (153) | 208 | 54.0: $R_F$ 35.1, base 39.8, collector 5.6, $r_b$ 4.5, buffer 4.1 | 1.80 | 80.8 / 76.5 / 68.3 / 58.6; 79.8 / 75.6 / 67.4 / 57.6 |

**A bipolar front end at high photocurrent.** A receiver that works mainly at 0.1–10 mA tolerates a bipolar transistor's base current. At $I_1 + I_2$ = 1 mA the photocurrent's own shot noise is $\sqrt{2q \times 1\ \mathrm{mA}}$ = 17.9 pA/√Hz, against 0.94–3.25 pA/√Hz of base-current noise at 1–10 mA of collector current, so the base current adds 0.3–3.3 % to the noise power at 1 mA and a tenth of that at 10 mA. The same shot noise hides every other part of the front end's noise too. At 1 mA the designs of Table 11.6 give 67.4–67.6 dB with $\lvert Z_T\rvert$ = $R_F$, against 67.6 dB for OPA855 and 67.8 dB for OPA955, and the bipolar composite biased at 10 mA gives the same as at 1 mA within 0.1 dB. A bipolar input stage is therefore no obstacle at high photocurrent, but no input transistor raises the dynamic range there either: the bound of Table 11.3, which allows 0.11 dB over OPA855 at 1 mA, holds for every front end that keeps OPA855's ceiling. The bipolar transistor's advantages over the pHEMT are practical ones. Infineon publishes its SPICE model [S22], its current gain is specified between 160 and 400 at 25 mA (BFP740ESD datasheet p11), its pins are protected to ±2 kV HBM (p9), and its DC characteristics are specified. A lower-noise input stage pays only where the amplifier's own noise is large, as in the high-voltage composite of Section 11.6, whose first stage contributes 94–113 nA of its 121–137 nA.

**Using an RF transistor at the summing node: bias, package and layout.** The pHEMT's numbers above hold only if a few practical conditions are met; most of them follow from its being built and specified for microwave amplifiers.
- **The gate sits at $V_{GS}$, and with a grounded source so does the output.** CE3512K2 is a depletion device that carries 10 mA at about −0.5 V (p4) and cuts off between −0.39 and −1.10 V (p3). The bias loop through $R_F$ puts the summing node, and with it the buffer's output, at $V_{GS}$: −0.50 V in the simulation. That leaves 0.90 V of symmetric swing in the OPA859's range of −1.40 to +1.60 V instead of 1.5 V, which is 4.4 dB less ceiling and so 4.4 dB less dynamic range at every photocurrent. Lifting the source to $\lvert V_{GS}\rvert$ restores it, with a stiff, well-bypassed source supply or with a source resistor bypassed far into the gigahertz range, since any impedance left at the source degenerates the stage and its noise adds directly to $e_n$. Serikawa and Furusawa bias their source follower the same way, with the gate at 0 V and 47 Ω from the source setting 10 mA [A23, p. 4]. The gate voltage also follows the part-to-part spread of $V_{GS(\mathrm{off})}$, 0.7 V between minimum and maximum (p3), so the source voltage has to be set for each part, for example by a slow servo on the output's DC level. An enhancement-mode part avoids the negative gate. SAV-551+ needs +0.22 to +0.46 V for 15 mA at 3 V (p2), and ATF-54143 needs about +0.6 V for 60 mA (p10). With the source grounded the output of a SAV-551+ composite would sit at +0.34 V, which costs 1.5 dB of symmetric swing in the same buffer. The bipolar composite puts its emitter at −$V_{BE}$ for the same reason, and its base current then shifts the output by $I_BR_F$, 5–66 mV at 1–10 mA.
- **The gate current must be measured.** The Schottky gate of a pHEMT leaks microamperes. CE3512K2 specifies 0.4 µA typical and 10 µA maximum at $V_{GS}$ = −3 V (p3), with an absolute maximum of 80 µA (p2). No datasheet gives it at the operating point or over temperature, and Table 11.4 and the simulation assume 1 µA. At 1 µA its shot noise adds 6.9 nA to the band noise; at 10 µA it would add 21.9 nA, raising the band noise from 36.5 to 42.0 nA and costing 1.2 dB in the dark. Impact ionization in the channel adds gate current at high drain voltage, a general property of pHEMTs and one more reason to keep $V_{DS}$ within the recommended 1–3 V (p2).
- **Nothing is specified at baseband.** CE3512K2's S-parameters start at 2 GHz and its noise parameters at 8 GHz (its S2P files), and its datasheet gives the noise figure at 12 GHz (p1, p3). SAV-551+ is specified from 45 MHz (p2), but its noise only from 0.5 GHz (noise parameters, pp. 7–9). The 1/f, generation–recombination and random-telegraph noise of these parts across 0.1–150 MHz is unknown. Their small-signal parameters at baseband are not those of the microwave data either. CE3512K2's output conductance is about 2.5 mS from its I–V curves (p4), against Re($y_{22}$) = 5.1 mS in its S-parameters at 2 GHz, and its transconductance 69 mS (p3), against Re($y_{21}$) = 71.0 mS. The designs above use the values at DC; the noise at baseband has to be measured.
- **The transistor alone is potentially unstable at microwave frequencies.** From CE3512K2's S-parameters at 2 V and 10 mA, the Edwards–Sinsky stability factor μ is below 1 from 2.0 to 12.6 GHz, with 0.19 at 2 GHz, and again from 19.9 to 26 GHz, and the file starts at 2 GHz; Rollett's K is 0.23 at 2 GHz and 0.92 at 10 GHz (`scripts_archive/fet_front_end/phemt_stability_factors.py`). The TIA's loop, which crosses over at a few hundred megahertz, neither causes nor suppresses an oscillation there; one would show up as excess noise, a shifted bias point or distortion. The layout has to keep the impedances at the gate and the drain inside the stable region. Both source leads (pins 1 and 3, p2) go to ground through vias at the pads, Q2's gate is bypassed at its pin, and a resistor of a few ohms in series with each drain adds loss at gigahertz frequencies, where the TIA needs no gain. Avago's LNA application circuit terminates the gate and the drain resistively at low frequencies, which improves the low-frequency stability (ATF-54143 p10, Fig. 23, R3 and R4); a TIA's gate cannot take such a resistor without adding its noise.
- **Package and handling.** CE3512K2 comes in a four-lead hollow (air-cavity) plastic Micro-X package (p1), and SAV-551+ and the Avago parts in the four-lead SOT-343 (p1 of each). GaAs gates are sensitive to electrostatic discharge: CEL asks for ESD precautions at all times (p8), and Avago rates ATF-54143 at HBM Class 1A and ATF-34143 and ATF-55143 at HBM Class 0 (p1 of each). The summing node connects to the photodiodes, so any protection added there adds capacitance and leakage to the very node the pHEMT is chosen to keep small. BFP740ESD carries its own ±2 kV protection (p9), whose capacitance is part of its 0.79–1.34 pF. Each transistor dissipates 20 mW at 10 mA and 2 V, well inside CE3512K2's 125 mW (p2).

**A gate stopper costs little at this node.** A resistor $R_g$ in series with the gate adds its Johnson noise to $e_n$,

$$
e_n'^2 = e_n^2 + 4k_BT\,\mathrm{Re}\{Z_g\},
\qquad
Z_g = R_g \parallel j\omega L_g,
\tag{70}
$$

with an optional inductor $L_g$ across it. Like a bipolar transistor's $r_b$, this noise acts on the capacitance of the node outside the transistor. With $R_g$ = 10 Ω alone, 0.41 nV/√Hz adds to the device's 0.40 nV/√Hz, but at this small node the channel's share of the band noise is only 6.3 nA, so the total rises from 36.5 to 37.0 nA, 0.1 dB in the dark. Serikawa and Furusawa's 150 Ω with 10 nH in parallel [A23, p. 4, Table I] costs even less. At 100 MHz, Re{$Z_g$} = 150 Ω × (6.28 Ω)²/[(150 Ω)² + (6.28 Ω)²] = 0.26 Ω, or 0.07 nV/√Hz, while at 3 GHz the resistor damps with 92 Ω."""

WHERE_PREFIX = "**Where a composite would pay off is the ceiling, not the noise.**"
WHERE_NEW = r"""**Where a composite pays off is the ceiling, not the noise.** From about 0.15 mA up the dynamic range follows the output amplitude dB for dB (Section 11.3, Figure 16). Raising $V_{\mathrm{pk}}$ at 100 MHz from OPA818's 2.23 V to 10 V would add $20\log_{10}(10/2.23)$ = 13.0 dB at every photocurrent; that needs a slew rate of at least $2\pi \times 100\ \mathrm{MHz} \times 10\ \mathrm{V}$ = 6.3 kV/µs and rails of about ±12 V. Section 11.6 builds that composite: a low-noise first stage driving a fast high-voltage amplifier inside the $R_F$ loop. To use 70.7 dB in 150 MHz, an ADC whose full scale matches the TIA's largest tone needs a noise spectral density of $-70.7 - 10\log_{10}(150\ \mathrm{MHz})$ = −152.5 dBFS/Hz, and the 81.8 dB of Section 11.6 would need −163.6 dBFS/Hz."""

# ------------------------------------------------------------------ Sections 11.6 and 11.7, verdict 11.8
VERDICT_OLD = "### 11.6 Verdict"
S116 = r"""### 11.6 A high-voltage output stage inside the $R_F$ loop

Section 11.3 showed that from about 0.15 mA up the output amplitude sets the dynamic range, and Section 11.5 that no input transistor changes that. This section raises the ceiling instead: a fast, high-voltage amplifier inside the $R_F$ loop takes the output to several volts while a low-noise first stage still sets the noise. The numbers are for the baseline (1 pF, 0.35 pF of board, 2 kΩ) and come from `scripts_archive/composite_tia.py`, `spice_composite_checks.py` and `composite_report_numbers.py`.

**The output amplifier.** It needs a slew rate of $2\pi f_0V_{\mathrm{pk}}$, 6.3 kV/µs for 10 V at 100 MHz, rails of ±12 V or more, and a closed-loop bandwidth several times the TIA's loop crossover. THS3491 comes closest of the high-voltage current-feedback amplifiers read for this survey (Table A2.4): 900 MHz at a gain of 5 and 2 Vpp, 320 MHz at 10 Vpp, 8000 V/µs at 20 Vpp, supplies of ±7 to ±16 V, ±420 mA of linear output current and 1.7 nV/√Hz (SBOS875C p1). THS3091 and THS3095 give 6000 V/µs at a gain of 5, 305 MHz at a gain of 2 and ±310 mA (SLOS423K p1), THS3061 and THS3062 7000 V/µs, 300 MHz at unity gain and ±145 mA into 50 Ω (SLOS394B p1), and THS3001 6500 V/µs, 420 MHz at unity gain and 100 mA (SLOS217I p1). TI designed THS3491 for better than 40 dB of spurious-free dynamic range with a 100-MHz, 20-Vpp signal into 100 Ω, and its datasheet states how large a signal stays linear (p29). Some internal devices saturate with large signals above 100 MHz and the loop then opens, so Fig 9-4 (p29) gives the maximum recommended output voltage that keeps the amplifier linear. On ±15 V it falls from 26.0 Vpp at 1–10 MHz to 20.1 Vpp at 100 MHz and 14.2 Vpp at 150 MHz. These readings, and every other THS3491 curve used here, were checked by drawing them on the rendered figures (`data/digitization_checks/`, `scripts_archive/overlay_digitized.py`); their largest residuals against the figures' vector paths are 0.008 Vpp, 0.005 dB and 0.005°.

**The first stage.** The composite's loop contains the gains of both stages, so its gain–bandwidth product is that of the first stage times the THS3491's gain $G_2$. A decompensated first stage such as OPA855 or OPA955, with 8–11 GHz of gain–bandwidth and stable only from gains of 7 up (Section 3.2), would put the crossover far beyond the THS3491's bandwidth. The first stage has to be unity-gain stable, because in the topology that works (below) it closes a fast local loop at a noise gain of about 2, and slow enough that its gain–bandwidth times $G_2$ stays within reach of the output stage. OPA859, unity-gain stable with 900 MHz of gain–bandwidth and 3.3 nV/√Hz at 1 MHz on ±2.5 V (Section 3.2), is the survey's part that fits. Its output swing of ±1.5 V then limits the composite's output to about $G_2$ × 1.5 V.

**The THS3491 as a stage.** A current-feedback amplifier at a non-inverting gain $G = 1 + R_{F2}/R_{G2}$ has the closed-loop gain

$$
H_2 = \frac{G(s)}{1 + \big(R_{F2} + G(s)\,Z_i\big)/Z_{OL}},
\qquad
G(s) = 1 + \frac{R_{F2}}{R_{G2}} + sR_{F2}C_n,
\tag{71}
$$

where $Z_{OL}$ is its open-loop transimpedance, $Z_i$ the impedance of its inverting input (15 Ω typical, open-loop measurement, p9) and $C_n$ the capacitance at its inverting node, which acts across $R_{G2}$ and raises the gain at high frequencies. The datasheet states no $C_n$. TI's model of the part [S21], whose header states that it was aligned with the datasheet on ±15 V for the bandwidth at a gain of 5, among other parameters, has 1.2 pF at its internal inverting node. With that value and the model's own $Z_{OL}$ and $Z_i$, Eq. (71) reproduces the model's closed loop at all four gains of Table 9-2 within 0.5 dB and 1.6° up to 3 GHz (Table 11.7).

The datasheet's own two curves do not agree with each other. Fig 8-22 (p16) gives the open-loop transimpedance and phase without load, and Fig 8-1 (p13) the measured closed-loop response in the circuit of Fig 9-1 (p27). Eq. (71) with Fig 8-22 does not reproduce Fig 8-1, with or without $C_n$. With $C_n$ = 1.2 pF it predicts 1.9 GHz with 3.6 dB of peaking at a gain of 5, against 944 MHz with no peaking measured, and no −3-dB point below 5 GHz at a gain of 2. With $C_n$ = 0, the textbook form, it predicts 1.4 GHz with 1.1 dB of peaking at a gain of 5, and 340 MHz at a gain of 2, against 730 MHz measured. The phase of Fig 8-22 agrees with the model's internal transimpedance within 3.4° from 100 to 770 MHz, but its magnitude lies above the model's by 0.8 dB at 100 and 300 MHz, 1.6 dB at 500 MHz and 2.8 dB at 770 MHz (51.8 against 49.0 dBΩ). The model, in contrast, reproduces Fig 8-1 at gains of 5, 10 and 20 within 5–13 % in bandwidth, with 0.4–0.8 dB more peaking; at a gain of 2 it gives about twice the measured bandwidth (Table 11.7). The model's noise matches the datasheet too: 16.2 nV/√Hz at the output at a gain of 5, against 15.9 nV/√Hz from the datasheet's $e_n$, $i_n$ and resistors, and 16.8 mA of supply current against 16.7 mA (p9). The analysis below therefore describes the THS3491 by Eq. (71) with its model's $Z_{OL}$, $Z_i$ and $C_n$, its input by the model's 50 kΩ ∥ 1.5 pF, and its noise by the datasheet's $e_n$, $i_n$ and resistors. It describes the OPA859 by its model's open-loop gain, output impedance, input capacitance (0.82 pF) and voltage noise (Section 10). SPICE runs of the whole composite with both vendor models check the result (below and Section 11.7).

*Table 11.7. THS3491 at the four gains of Table 9-2 in the circuit of Fig 9-1 ($R_L$ = 100 Ω, ±15 V): −3-dB bandwidth and peaking measured by TI (Fig 8-1, read off its vector paths); from TI's model in SPICE [S21], at the load as in Fig 8-1 and pin to pin in brackets; and from Eq. (71) with the model's $Z_{OL}$, $Z_i$ and $C_n$ = 1.2 pF (with its largest deviation from the model's pin-to-pin response up to 3 GHz), with Fig 8-22's $Z_{OL}$ and $C_n$ = 1.2 pF, and with Fig 8-22's $Z_{OL}$ and $C_n$ = 0. Amplifiers: THS3491 (RGT package) at gains of 2, 5, 10 and 20 (one per row).*

| Gain, $R_{F2}$ | Fig 8-1, measured | SPICE model | Eq. (71), model's $Z_{OL}$ | Eq. (71), Fig 8-22, $C_n$ = 1.2 pF | Eq. (71), Fig 8-22, $C_n$ = 0 |
|---|---|---|---|---|---|
| 2, 976 Ω | 730 MHz, 0.20 dB | 1507 (1660) MHz, 1.47 dB | 1689 MHz, 1.58 dB (0.25 dB, 1.2°) | no −3-dB point below 5 GHz, 10.0 dB | 340 MHz, 0 dB |
| 5, 576 Ω | 944 MHz, 0.02 dB | 847 (858) MHz, 0.53 dB | 874 MHz, 0.55 dB (0.45 dB, 1.6°) | 1893 MHz, 3.63 dB | 1400 MHz, 1.10 dB |
| 10, 499 Ω | 755 MHz, 0.13 dB | 717 (723) MHz, 0.55 dB | 730 MHz, 0.55 dB (0.45 dB, 1.4°) | 1437 MHz, 1.94 dB | 1403 MHz, 1.15 dB |
| 20, 383 Ω | 542 MHz, 0.03 dB | 611 (615) MHz, 0.78 dB | 619 MHz, 0.76 dB (0.50 dB, 1.6°) | 1328 MHz, 0.56 dB | 1350 MHz, 0.28 dB |

**Two topologies.** In the plain composite, $R_F \parallel C_F$ runs from the THS3491's output $v_2$ to the summing node $v_s$, and the OPA859, with its non-inverting input grounded, drives the THS3491 directly. In the dual-feedback composite a capacitor $C_L$ also runs from the OPA859's output $v_1$ to the summing node; it closes a fast local loop around the first stage and takes over the feedback at high frequencies. The THS3491 drives 100 Ω, the load of its datasheet characterization, in parallel with its own feedback network and $R_F$. The OPA859 is a Thevenin source $A_1(e_1 - v_s)$ behind its open-loop output impedance $Z_o$, where $e_1$ is its input voltage noise. The THS3491 gives $v_2 = H_2(v_1 + e_2)$ with input admittance $Y_{in2}$, where $e_2$ is its noise referred to its input, 3.0–4.3 nV/√Hz at gains of 5.5 to 4. The node capacitance $C_T = C_D + C_{\mathrm{PCB}} + C_{\mathrm{in1}}$ = 1 + 0.35 + 0.82 pF = 2.17 pF includes the OPA859's input capacitance $C_{\mathrm{in1}}$. With $Y_T = j\omega C_T$, $Y_F = 1/R_F + j\omega C_F$, $Y_L = j\omega C_L$ and $Y_s = Y_T + Y_F + Y_L$, the two node equations are

$$
\begin{aligned}
Y_s\,v_s - (Y_L + Y_FH_2)\,v_1 &= i_{\mathrm{in}} + Y_FH_2\,e_2,\\
(A_1 - Y_LZ_o)\,v_s + \big(1 + Z_o(Y_{in2} + Y_L)\big)\,v_1 &= A_1e_1,
\end{aligned}
\tag{72}
$$

with $Z_T = v_2/i_{\mathrm{in}}$. The loop gain at the first stage's output, where SPICE injects, is

$$
T = \frac{A_1K}{1 + Z_o\big(Y_{in2} + Y_L - Y_LK\big)},
\qquad
K = \frac{Y_L + Y_FH_2}{Y_s},
\tag{73}
$$

which for $Z_o$ = 0 is $T = A_1(Y_L + H_2Y_F)/Y_s$; the plain composite is the case $C_L$ = 0. Every noise source is referred to the input by its contribution to $v_2$ divided by $Z_T$. With $Z_o$ = 0, $e_1$ is seen through $\lvert Y_s\rvert$, so it acts on $C_T + C_F + C_L$, and $e_2$ through $\lvert Y_L + Y_s/A_1\rvert$.

**The plain composite is unstable.** Its loop gain is $A_1H_2Y_F/Y_s$: the first stage's gain–bandwidth times $G_2$, about 0.9 GHz × $G_2$, divided by the noise gain of the TIA. That puts the crossover at 390–640 MHz for $G_2$ = 2–8, where the THS3491 already adds tens of degrees of lag. Even the best total $C_F$ leaves only 15° of phase margin at a gain of 2 and none from 3 up (Table 11.8), so no gain gives a robust design.

*Table 11.8. Plain composite (no $C_L$): the total $C_F$ with the largest worst-corner phase margin at each THS3491 gain, from Eqs. (72)–(73) with the macromodels' parameters (scan of $C_F$ = 0.10–1.50 pF). Amplifiers: OPA859 with THS3491 (one gain per row).*

| $G_2$ | Best $C_F$ (pF) | Nominal crossover (MHz) | Nominal phase margin (°) | Worst-corner phase margin (°) |
|---|---|---|---|---|
| 2 | 0.375 | 393 | 15.2 | 9.0 |
| 3 | 0.325 | 439 | −4.6 | −11.4 |
| 4 | 0.250 | 478 | −23.9 | −32.2 |
| 5 | 0.200 | 545 | −44.9 | −58.1 |
| 6 | 0.175 | 570 | −59.1 | −71.6 |
| 8 | 0.175 | 640 | −82.7 | −93.4 |

**The dual-feedback composite is robust in a narrow window.** $C_L$ closes a local loop around the first stage with a noise gain of $(C_T + C_F + C_L)/C_L$, 1.7–2.0 for the designs below, so the outer loop through the THS3491 no longer has to carry the crossover alone. A first scan over $G_2$ = 2–8, $C_L$ = 0.5–4.0 pF and $C_F$ = 0.10–1.50 pF, and a finer one over $G_2$ = 4–7, $C_L$ = 2.0–4.0 pF in 0.25-pF steps and $C_F$ = 0.100–0.300 pF in 0.025-pF steps, each design over all 27 corners ($C_D$ ± 0.2 pF, $C_F$ ± 0.1 pF and $C_L$ ± 0.1 pF), find robust designs only at $G_2$ = 4–5.5. They are five of the 486 designs of the fine scan, with $C_F$ = 0.100–0.125 pF and 0.55–0.6 pF of $C_L$ per unit of $G_2$; with less $C_L$ the phase margin fails, and with more the bandwidth. Table 11.9 gives the one at each gain with the largest dynamic range at 1 mA. SPICE runs of these four designs at all 27 corners give worst-corner values within 0.2° of phase margin, 0.1 dB of gain margin, 0.01 dB of peaking and 1 MHz of bandwidth of the analysis, and band noise at nominal capacitances within 0.6 nA. Over 16 further designs at nominal capacitances, stable and unstable, SPICE and the analysis agree within 1.3° of phase margin, 0.4 dB of gain margin, 4.5 MHz of bandwidth and 0.8 % of band noise. Described with OPA859's datasheet curve instead of its model, the fine scan would also accept gains of 6 and 7 (29 robust designs at $G_2$ = 4–7). SPICE gives two of these designs, $G_2$ = 6 with $C_F$ = 0.150 pF and $C_L$ = 3.00 pF and $G_2$ = 7 with 0.150 and 3.75 pF, only 34.4° and 36.8° at the worst corner, about 10° less than the datasheet curve predicts.

*Table 11.9. Dual-feedback composites robust over all 27 corners: THS3491 gain and $R_{F2}$; total $C_F$ and $C_L$; phase margin, gain margin, peaking and $f_{3\,\mathrm{dB}}$ at the worst corner from SPICE, with the analysis in brackets; nominal $f_{3\,\mathrm{dB}}$; band noise over 0–150 MHz from SPICE, with its analytical parts; ceiling and transimpedance at 100 MHz; dynamic range at a 100-MHz tone by Eq. (56). OPA818's design of Table 11.1 is given for comparison. Amplifiers: OPA859 with THS3491 at gains of 4, 4.5, 5 and 5.5, and OPA818 (one per row).*

| $G_2$, $R_{F2}$ | $C_F$ / $C_L$ (pF) | Worst PM (°), GM (dB), peaking (dB), $f_{3\,\mathrm{dB}}$ (MHz) | Nominal $f_{3\,\mathrm{dB}}$ (MHz) | Band noise (nA rms): total; first stage, THS3491, $R_F$ | $V_{\mathrm{pk}}$ (V), $\lvert Z_T\rvert$ (kΩ) at 100 MHz | DR at 0 / 0.1 / 1 / 10 mA (dB) |
|---|---|---|---|---|---|---|
| 4, 709 Ω | 0.125 / 2.25 | 45.6 (45.7), 9.9 (9.8), 0.38 (0.37), 155 (155) | 239 | 120.9; 94.0, 67.0, 35.1 | 6.00, 1.85 | 85.5 / 84.3 / 79.2 / 70.2 |
| 4.5, 643 Ω | 0.100 / 2.50 | 45.6 (45.7), 9.4 (9.4), 0.43 (0.42), 171 (170) | 275 | 122.6; 98.5, 63.2, 35.1 | 6.77, 1.89 | 86.3 / 85.1 / 80.1 / 71.1 |
| 5, 576 Ω | 0.100 / 3.00 | 45.3 (45.5), 8.8 (8.8), 0.00 (0.00), 152 (152) | 238 | 131.9; 108.4, 65.4, 35.1 | 7.55, 1.83 | 86.9 / 85.8 / 81.1 / 72.3 |
| 5.5, 568 Ω | 0.100 / 3.25 | 45.0 (45.2), 8.5 (8.5), 0.02 (0.02), 158 (158) | 253 | 136.5; 113.4, 66.1, 35.1 | 8.30, 1.84 | 87.3 / 86.4 / 81.8 / 73.1 |
| OPA818 alone (Table 11.1) | – | – | 262 | 84.8 | 2.23, 1.96 | 79.5 / 77.3 / 70.7 / 61.2 |

**Noise and dynamic range.** The composite is 2.4–2.8 times as noisy as OPA855 (49.6 nA), for two reasons that come with the dual feedback. The first stage's voltage noise, about 3.0 nV/√Hz in its model above 10 MHz, acts on $C_T + C_F + C_L$, 4.5–5.5 pF instead of about 2.4 pF, which gives its 94–113 nA. The THS3491's noise reaches the summing node through $C_L$ ($\lvert Y_L + Y_s/A_1\rvert$ in Eq. (72)) and adds 63–67 nA. The ceiling more than pays for both. At $G_2$ = 5.5 the dynamic range at 100 MHz is 87.3, 86.4, 81.8 and 73.1 dB at 0, 0.1, 1 and 10 mA: 7.8, 9.1, 11.1 and 11.9 dB above OPA818 and 4.4, 9.7, 14.0 and 15.2 dB above OPA955. Its transimpedance at 100 MHz is 1.84 kΩ, 0.7 dB below $R_F$, which Eq. (56) credits as it credits OPA818's 1.96 kΩ (0.2 dB below $R_F$); with $\lvert Z_T\rvert$ = $R_F$ the composite gives 86.6, 85.6, 81.1 and 72.4 dB.

**Large signal: swing, slew rate and the THS3491's limit.** At 100 MHz the ceiling is the OPA859's swing times the THS3491's gain at the tone, 1.5 V × $\lvert H_2\rvert$ = 1.5 V × 5.53 = 8.30 V at $G_2$ = 5.5. That is below the THS3491's recommended 10.05 V (Fig 9-4) and its slew-rate limit, 8000 V/µs / (2π × 100 MHz) = 12.7 V. The output then slews at $2\pi \times 100\ \mathrm{MHz} \times 8.30\ \mathrm{V}$ = 5.2 kV/µs and the OPA859 at 0.94 kV/µs, against their 8.0 and 1.15 kV/µs. SPICE tone runs, done as in Section 10.8, find the output clean up to 0.9 times this ceiling, 7.47 V (THD −137 dBc, the numerical floor of the runs), and clipped at 1.0 times, 8.30 V, where the OPA859's output reaches +1.50/−1.45 V and the THD is −36 dBc. At 150 MHz the analysis takes the OPA859's datasheet slew rate as the limit, 1150 V/µs / (2π × 150 MHz) = 1.22 V, times $\lvert H_2\rvert$ = 5.57, which gives 6.80 V, just below the THS3491's recommended 7.08 V (Fig 9-4). The OPA859's model slews faster than its datasheet value. The composite stays clean in SPICE up to 1.1 times, 7.49 V, with the OPA859 at 1.34 V and 1.27 kV/µs, and clips at 1.2 times, 8.16 V, again at the OPA859's swing. The datasheet values are kept for the dynamic range. The internal saturation behind Fig 9-4 is not in the THS3491's model, since SPICE gives a clean 7.49 V at 150 MHz, above the 7.08 V that Fig 9-4 recommends.

**Distortion.** The macromodels are linear until they clip, so the distortion below their limits has to come from the datasheet. THS3491's table gives, at a gain of 5 into 100 Ω, HD2 of −78, −76, −68 and −60 dBc and HD3 of −81, −75, −61 and −51 dBc at 20, 50, 70 and 100 MHz for 10 Vpp, and −51 dBc HD2 and −47 dBc HD3 at 100 MHz for 20 Vpp (p8). Its Figs 8-13 and 8-14 (p15) give the 100-MHz values against output swing into 100 Ω: HD2 rises from −64.2 dBc at 5 Vpp to −55.0 dBc at 16.6 Vpp, and HD3 from −57.8 dBc at 5 Vpp to a plateau between −49.7 and −51.3 dBc from 10 to 17.5 Vpp. Inside the composite the outer loop does not reduce this distortion at the harmonics. A disturbance $v_e$ at the THS3491's output reaches the closed-loop output as $S\,v_e$, where

$$
S = \frac{v_2(e_2)}{H_2\,e_2}
\tag{74}
$$

is the closed-loop response of Eq. (72) to the THS3491's input-referred source $e_2$, divided by its open-loop response $H_2e_2$. At $G_2$ = 5.5, $\lvert S\rvert$ is −3.1 dB at 100 MHz but +1.3 dB at 200 MHz and +3.1 dB at 300 MHz: at those frequencies $C_L$ carries the feedback, and the path through $R_F$ that sees the THS3491's output is weak. At the full 16.6 Vpp the composite therefore carries about −53.7 dBc HD2 and −46.9 dBc HD3 at 100 MHz. OPA818's datasheet gives, at 100 MHz and a gain of 7 into 1 kΩ, −54 and −50 dBc HD2 and −79 and −67 dBc HD3 at 1 and 2 Vpp, and nothing at its 4.5-Vpp ceiling (Table 6.5); OPA855's is −73/−89 dBc at 1 Vpp (Table 7.12). The composite's HD2 at full swing is thus about OPA818's at 1–2 Vpp, and its HD3 20–32 dB worse. If the receiver needs every harmonic below −50, −55 or −60 dBc at 100 MHz, the output must stay below 7.91, 4.95 or 3.95 Vpp, and the dynamic range at 1 mA falls from 81.8 to 75.4, 71.3 or 69.3 dB (Table 11.10). At tones of 20–50 MHz the THS3491's harmonics at 10 Vpp are 16–30 dB lower than at 100 MHz (p8).

*Table 11.10. Large signal at a 100-MHz tone, $G_2$ = 5.5: THS3491's distortion at a gain of 5 and 100 Ω against output swing (Figs 8-13 and 8-14, p15, read off the vector paths), the composite's at the same swing with $\lvert S\rvert$ = +1.3 dB at 200 MHz and +3.1 dB at 300 MHz (Eq. (74)), and the dynamic range by Eq. (56) with the output held to that swing. Amplifiers: THS3491 alone, and OPA859 with THS3491 at $G_2$ = 5.5 (one swing per row).*

| Output swing (Vpp) | What sets it | THS3491 HD2 / HD3 (dBc) | Composite HD2 / HD3 (dBc) | DR at 0 / 0.1 / 1 / 10 mA (dB) |
|---|---|---|---|---|
| 3.95 | harmonics ≤ −60 dBc | −65.9 / −63.1 | −64.6 / −60.0 | 74.9 / 73.9 / 69.3 / 60.6 |
| 4.95 | harmonics ≤ −55 dBc | −64.3 / −58.1 | −63.0 / −55.0 | 76.8 / 75.8 / 71.3 / 62.6 |
| 7.91 | harmonics ≤ −50 dBc | −61.9 / −53.1 | −60.6 / −50.0 | 80.9 / 79.9 / 75.4 / 66.6 |
| 16.6 | the OPA859's swing | −55.0 / −50.0 | −53.7 / −46.9 | 87.3 / 86.4 / 81.8 / 73.1 |

**Supplies and power.** On ±15 V the THS3491 draws 16.7 mA (p9), 0.50 W at rest. With a sine of amplitude $V_{\mathrm{pk}}$ into the load $R_{\mathrm{load}}$, its output stage draws a rectified current from each rail, and the part dissipates

$$
P_{\mathrm{THS}} = 2V_SI_Q + \frac{2V_S}{\pi}\,\frac{V_{\mathrm{pk}}}{R_{\mathrm{load}}} - \frac{V_{\mathrm{pk}}^2}{2R_{\mathrm{load}}}.
\tag{75}
$$

At $G_2$ = 5.5 the load is 100 Ω in parallel with $R_{F2} + R_{G2}$ = 695 Ω and $R_F$ = 2 kΩ, so $R_{\mathrm{load}}$ = 83.8 Ω. At 8.30 V, $P_{\mathrm{THS}}$ = 2 × 15 V × 16.7 mA + (2 × 15 V/π)(8.30 V/83.8 Ω) − (8.30 V)²/(2 × 83.8 Ω) = 0.50 + 0.95 − 0.41 W = 1.04 W, a junction rise of 1.04 W × 49.6 °C/W = 51 °C in the RGT package (p7). That is safe at room temperature, but continuous full-scale tones need the thermal pad and the board copper that the datasheet's thermal resistance assumes. On ±7.5 V the part draws 15.8 mA (p11), 0.24 W at rest and 0.37 W at its 5.11-V ceiling (Fig 9-4: 10.21 Vpp at 100 MHz). The dynamic range at $G_2$ = 5.5 then becomes 83.1, 82.1, 77.6 and 68.8 dB, 4.2–4.3 dB below ±15 V but still 3.6–7.6 dB above OPA818. TI's model is aligned with the datasheet on ±15 V only (its header). The OPA859 adds 20.2 mA on ±2.5 V, 0.10 W (SPICE operating point).

*Table 11.11. Supplies and dissipation at $G_2$ = 5.5 with a continuous tone at the 100-MHz ceiling (Eq. (75); $I_Q$ from p9 and p11, junction rise with 49.6 °C/W from p7). Amplifiers: THS3491 on ±15 and ±7.5 V (one supply per row).*

| THS3491 supply | Ceiling at 100 MHz (V) | Quiescent (W) | At the ceiling (W) | Junction rise (°C) | DR at 0 / 0.1 / 1 / 10 mA (dB) |
|---|---|---|---|---|---|
| ±15 V | 8.30 (the OPA859's swing) | 0.50 | 1.04 | 51 | 87.3 / 86.4 / 81.8 / 73.1 |
| ±7.5 V | 5.11 (Fig 9-4) | 0.24 | 0.37 | 18 | 83.1 / 82.1 / 77.6 / 68.8 |

**What a lower-noise first stage would add.** The first stage contributes 113.4 nA of the 136.5 nA at $G_2$ = 5.5. A discrete input transistor of Section 11.5 with 0.40 nV/√Hz in place of OPA859's 3.0 nV/√Hz would cut that share, in proportion to the voltage noise and with the transistor's own 0.27 pF neglected, to 15.0 nA, and the total to 76.4 nA if the THS3491's 66.1 nA stayed as it is. That would add 5.0, 3.4, 0.9 and 0.1 dB at 0, 0.1, 1 and 10 mA. Such a composite has three active stages in its loop, and its stability is not studied here (Appendix 1, item 20).

### 11.7 SPICE models, decks and convergence for the composites

The checks of Sections 11.5–11.6 run in ngspice-46, loaded as a shared library with PSpice compatibility, as in Section 10. `scripts_archive/spice_composite_checks.py` writes every deck under `spice/runs/composite/<check>/<case>/`, runs it, keeps its log and stores the results in `spice/results/composite_<check>.json`. Table 11.12 lists the models.

*Table 11.12. Models used in Sections 11.5–11.6. Amplifiers and transistors: OPA859, THS3491, LSBF862, CPH3910, CE3512K2, BFP740ESD (one per row).*

| Part | Model | Source and use |
|---|---|---|
| OPA859 | TI macromodel [S8], as in Section 10 | first stage of the high-voltage composite; unity-gain buffer of the discrete-transistor composites |
| THS3491 | TI model package SBOMBP9: `ths3491.lib`, subcircuit THS3491RGT, model version 1.0 of 16 February 2018 [S21] | translated as in Section 10.2, with its helper subcircuits renamed (Table 11.13); pins INP, INN, OUT, PD_not (tied to the positive supply), VCC, VEE and GND (to ground); its header states alignment with the datasheet on ±15 V |
| LSBF862 | Linear Systems' published card, Rev 2 of 9 February 2026 [S23] | typed in from the PDF for ngspice's NJF model with every parameter unchanged and the model renamed from LSBF862_UPDATED to LSBF862 |
| CPH3910 | NJF card built here: VTO = −1.5 V, BETA = 12.0 mA/V², LAMBDA = 0.0222 V⁻¹, CGS = 3.7 pF, CGD = 2.3 pF, PB = 1000 V | matches the datasheet at $V_{DS}$ = 5 V and $V_{GS}$ = 0: 30 mA (of 20–40 mA), 40 mS, $C_{\mathrm{iss}}$ 6.0 pF and $C_{\mathrm{rss}}$ 2.3 pF (p1), and 0.6 mS of output conductance (Fig 2, p2); PB = 1000 V holds the capacitances constant; its cut-off at 100 µA, −1.41 V, lies inside the datasheet's −0.6 to −1.8 V but not at the typical −1.2 V (p1) |
| CE3512K2 | NJF card built here: VTO = −0.79 V, BETA = 59.5 mA/V², LAMBDA = 0.5 V⁻¹, CGS = 0.238 pF, CGD = 0.028 pF, PB = 1000 V; a separate diode of IS = 1 µA from the gate to −5 V for the gate current | matches 10 mA at $V_{GS}$ ≈ −0.5 V (p4), 69 mS (p3) and 2.5 mS of output conductance (p4) at $V_{DS}$ = 2 V, and $C_{11}$ = 0.266 pF and $C_{gd}$ = 0.028 pF from the S-parameters at 2 GHz; ngspice includes the diode's shot noise |
| BFP740ESD | Infineon's Gummel–Poon model with package and ESD network, version 2.0 of June 2011, valid to 10 GHz (its header) [S22] | subcircuit pins C, B, E1 and E2; both emitters on an ideal DC source at −$V_{BE}$ |

The decks are these.
- **THS3491 alone.** Its operating point and noise at a gain of 5; the circuit of Fig 9-1 at the four gains of Table 9-2; and its open-loop transimpedance as Fig 8-22 defines it, with the non-inverting input grounded, an AC current into the inverting input and the output fed back for DC only, through 1 GH. The internal transimpedance follows from the quantities at the pin: with $Z_{in}$ the measured inverting-input impedance and $C_n$ = 1.2 pF, $Z_i = Z_{in}/(1 - sC_nZ_{in})$ and $Z_{OL,\mathrm{int}} = Z_{OL,\mathrm{pin}}(1 + sC_nZ_i)$.
- **Loop gain and transimpedance.** Middlebrook's double injection (Section 10.3), at the OPA859's output in the high-voltage composite and at the buffer's output in the discrete-transistor composites, then the transimpedance; 100 points per decade from 100 kHz to 5 GHz.
- **Noise.** The `noise` analysis referred to the photocurrent source, at 50 points per decade from 100 kHz to 1 GHz, in a deck of its own; the band integral runs over exactly 0–150 MHz, as in Section 11.1.
- **Transistor data for Eqs. (67)–(68).** At each transistor's operating point inside its composite: its common-source two-port admittances (gate driven, then drain driven), its DC currents and its input voltage noise; and the buffer's gain and input admittance with its loads.
- **Tones.** A sine photocurrent at 100 and 150 MHz from 0.5 to 1.3 times the analytical ceiling, 48 periods at 256 points per period, with the last 32 analysed through a Hann window, as in Section 10.8.

Every log is scanned for the messages that mark a convergence aid, a failure or a warning, and `spice/results/composite_convergence.json` lists them by deck with what was done about each. Table 11.13 summarizes them, together with the netlist problems met while the decks were set up.

*Table 11.13. Convergence messages and netlist issues in the 406 decks of Sections 11.5–11.7, counted from their logs. Amplifiers and transistors: all of Table 11.12.*

| Issue | Where | What it meant and what was done |
|---|---|---|
| "Starting dynamic gmin stepping", then "Dynamic gmin stepping completed" | 317 decks, all of them with the OPA859 or the THS3491 macromodel; the bipolar composites, the stand-alone transistor decks and the THS3491's open-loop decks converge without it | Newton iteration from the initial guess does not converge, and ngspice's automatic gmin stepping finds the operating point. The points it finds are the expected ones (THS3491 16.8 mA, OPA859 20.2 mA, outputs within millivolts of their targets, the designed drain and collector currents), so nothing was changed. |
| "redefinition of .subckt femt, ignored", then "Mismatch: 5 formal but 3 actual params" and "Undefined parameter [glff]" | every deck with both TI models | Both libraries define the noise subcircuits FEMT and VNSE, with different parameter lists, and ngspice keeps the first definition for both models. The translated THS3491 library has all its helper subcircuits renamed THS3491_⟨name⟩, in the subcircuit-name token of each X statement only, since the model also has a node named VICM; the vendor file is untouched. All 3,601 stored results of the THS3491-only decks are the same with and without the renaming. |
| "unrecognized parameter (isr) – ignored", and the same for nr, zxti, alpha, vk and mj | the 26 decks with LSBF862 | These parameters of the card, among them PSpice's recombination current (ISR, NR) and impact ionization (ALPHA, VK), do not exist in ngspice's JFET model. M = 0.33 and MFG are accepted without effect, so the card's junction capacitances keep the exponent 0.5: $C_{gd}$ = 1.12 pF at the operating point, against 1.6 pF with M = 0.33. The card is used as published. |
| "setplot noise1" finds no such plot | a deck with `op` and three `ac` analyses before `noise` | The noise analysis runs in a deck of its own. |
| "has no value, DC 0 assumed", for current-sensing sources inside the OPA859 model | 380 decks | A note on zero-valued sources, with no effect. |
| Singular matrix, time step too small, source stepping, errors | none | All 406 decks, the 36 transient tone runs included, ran to completion. |

### 11.8 Verdict"""

V1_OLD = "- **For dynamic range at 0.1–10 mA, the discrete op-amp TIA of this survey remains the answer.**"
V1_NEW = r"""- **For dynamic range at 0.1–10 mA, a single op amp is the simplest answer and the high-voltage composite the best.** OPA818 (variant B) gives the most of any single amplifier from about 70 µA up, for tones below about 145 MHz, and OPA855, or OPA955 once released, the most in the dark and at the highest tones (Sections 11.2–11.3). The OPA859–THS3491 composite of Section 11.6 adds 7.8–11.9 dB to OPA818 from the dark to 10 mA at a 100-MHz tone, at the cost of about −47 dBc HD3 at full swing, ±15-V rails and a narrow stability window."""
VFET_OLD = "- **A discrete-FET front end does not pay at 1 pF.**"
VFET_NEW = r"""- **A discrete transistor at the summing node does not raise the dynamic range at 0.1–10 mA, whatever its type.** Silicon JFETs cannot reach 150 MHz in a robust composite at 1 pF and are noisier than OPA855. A GaAs pHEMT or a SiGe bipolar transistor gives a robust 150-MHz composite with about the noise of OPA955 (36.5–39.1 nA) and ties it from 0.1 mA up. At high photocurrent a bipolar transistor's base current costs nothing, but the photocurrent's shot noise hides every front end alike (Section 11.5).
- **A fast high-voltage output stage inside the $R_F$ loop is the composite that pays.** OPA859 with a THS3491 at a gain of 4–5.5 and a capacitor $C_L$ from the OPA859's output to the summing node is robust over every corner. At $G_2$ = 5.5 it gives 81.8 dB at 1 mA and a 100-MHz tone, 11.1 dB above OPA818, with 8.3 V of swing on ±15 V and 1.0 W in the THS3491. Without $C_L$ the composite is unstable at every gain from 3 up (Section 11.6).
- **The composites' analyses are verified in SPICE with the vendors' models (Section 11.7).** The THS3491's datasheet curves were checked against each other: its open-loop transimpedance (Fig 8-22) does not describe its measured closed loop (Fig 8-1), so the analysis uses its model, which does at gains of 5–20."""

# ------------------------------------------------------------------ Appendix 1
A1_START = "20. **The discrete-FET front end (Section 11.5).**"
A1_END = "## Appendix 2. References"
A1_NEW = r"""20. **The composite front ends (Sections 11.5–11.7).**
    - No pHEMT datasheet gives the gate current at the operating point, or any noise below 0.5 GHz. Table 11.6 and Section 11.5 assume 1 µA; a measurement of the chosen part at its bias and temperature would replace it. The $e_n$ of CPH3910, 2SK3557, BF545C and the two CEL parts in Table 11.4 is the channel-thermal value, and the CPH3910 and CE3512K2 SPICE cards match their datasheets at one operating point only.
    - Whether Broadcom still makes the ATF parts was not settled. NXP's BF862 model file and Nexperia's PMBFJ310 datasheet were not obtained.
    - The stability of the discrete composites at microwave frequencies depends on the layout, which no model here contains. CE3512K2 alone is potentially unstable from 2.0 to 12.6 GHz and from 19.9 to 26 GHz, and its S-parameters start at 2 GHz.
    - THS3491: the datasheet gives no capacitance at the inverting input, so the model's 1.2 pF is used; its Fig 8-22 does not reproduce its Fig 8-1 (Table 11.7); its model differs from Fig 8-1 at a gain of 2; and the internal saturation behind Fig 9-4 is not in the model. The model is aligned with the datasheet on ±15 V only, so the ±7.5-V figures of Section 11.6 rest on Fig 9-4 alone.
    - The distortion of the high-voltage composite is estimated from the THS3491's datasheet at a gain of 5 and the loop's factor of Eq. (74). The OPA859's own distortion at its 3-Vpp output inside the loop is not included, and OPA818's datasheet gives no distortion at its own ceiling, so the two cannot be compared at equal distortion.
    - A composite with a discrete low-noise input transistor, a unity buffer and the THS3491 could lower the high-voltage composite's noise from 136.5 to about 76 nA (Section 11.6); its stability is not studied.
    - Which ADCs reach the −152.5 to −163.6 dBFS/Hz that 70.7–81.8 dB in 150 MHz would need is not studied.
"""

# ------------------------------------------------------------------ Appendix 2
A23_CAPTION_OLD = ("*Table A2.3. Discrete-FET datasheets of Section 11.5 (Table 11.4), with the copy used; local copies "
                   "are in `datasheets/fet_front_end/`.")
A23_CAPTION_NEW = ("*Table A2.3. Discrete-transistor datasheets of Section 11.5 (Tables 11.4–11.6), with the copy used; "
                   "local copies are in `datasheets/fet_front_end/` and `datasheets/bjt_front_end/`.")
A23_AMPS_OLD = "Amplifiers (discrete FETs): every device of Table 11.4 (one per row or group).*"
A23_AMPS_NEW = "Amplifiers (discrete transistors): every device of Tables 11.4 and 11.5 (one per row or group).*"
A23_ATF_OLD = ("| ATF-34143, ATF-54143, ATF-55143 | Avago (Broadcom) | AV02-1283EN, AV02-0488EN, AV02-0923EN (2012), "
               "distributor copies | S-parameters, noise resistance, gate leakage |")
A23_ATF_NEW = ("| ATF-34143, ATF-54143, ATF-55143 | Avago (Broadcom) | AV02-1283EN, AV02-0488EN, AV02-0923EN (2012), "
               "distributor copies | S-parameters, noise resistance, gate leakage; package, enhancement mode and ESD "
               "classes (p1 of each); the bias and low-frequency termination of the LNA circuit (ATF-54143 p10, Fig. 23) |")
A23_SAV_OLD = ("| SAV-551+, SAV-541+ | Mini-Circuits | Rev F (ECO-010314), with their S2P files | S-parameters, noise "
               "resistance, gate leakage; SAV-551+ active (DigiKey, 27 October 2026) |")
A23_SAV_NEW = ("| SAV-551+, SAV-541+ | Mini-Circuits | Rev F (ECO-010314), with their S2P files | S-parameters, noise "
               "resistance, gate leakage; for SAV-551+ also the frequency range and package (p1), the operating gate "
               "voltage and the noise figure (p2) and the range of the noise parameters (p7); SAV-551+ active (DigiKey, "
               "27 October 2026) |")
A23_CEL_PREFIX = "| CE3512K2, CE3520K3 | CEL |"
A23_CEL_NEW = ("| CE3512K2, CE3520K3 | CEL | CDS-0018-05 Issue B (November 2018) and CDS-0019-04 Issue C (July 2019), "
               "with their S2P files | S-parameters and noise parameters (S2P files); gate leakage, cut-off voltage and "
               "transconductance (p3); for CE3512K2 also the package (p1), pins, maximum ratings and recommended bias "
               "(p2), I–V curves (p4) and ESD caution (p8); CE3512K2 active (DigiKey, 27 October 2026) |\n"
               "| BFP740ESD | Infineon | Data Sheet Rev. 1.1 (8 October 2012), distributor copy (Farnell); SPICE model "
               "[S22] | $h_{FE}$, $f_T$, $C_{CB}$ and $V_{(BR)CEO}$ (p11); maximum $I_C$, $P_{\\mathrm{tot}}$ and ESD "
               "rating (p9) |")
A24_TABLE = r"""*Table A2.4. High-voltage output amplifiers of Section 11.6, with the copy used; local copies are in `datasheets/hv_output_stage/`. Amplifiers: THS3491, THS3091/THS3095, THS3061/THS3062, THS3001 (one per row).*

| Part | Maker | Document and revision used | Values read |
|---|---|---|---|
| THS3491 | TI | SBOS875C (August 2017, revised February 2023) | features (p1); thermal resistance (p7); bandwidth, slew rate, distortion and noise (p8); inverting-input impedance and supply current on ±15 V (p9); supply current on ±7.5 V (p11); Figs 8-1 (p13), 8-13 and 8-14 (p15), 8-22 (p16); Fig 9-1 and Table 9-2 (p27); the text on the maximum recommended output voltage and Fig 9-4 (p29) |
| THS3091, THS3095 | TI | SLOS423K (September 2003, revised April 2023) | features (p1) |
| THS3061, THS3062 | TI | SLOS394B (July 2002, revised November 2009) | features (p1) |
| THS3001 | TI | SLOS217I (July 1998, revised December 2024) | features (p1) |
"""
APPNOTES_HEAD = "### Application notes and articles"
A22_LAST = "  - the shot noise of a divided current, Appendix A, Eqs. (A3)–(A5) (pp. 919–920)."
A23_A24 = r"""- **[A23]** T. Serikawa and A. Furusawa, "500 MHz resonant photodetector for high-quantum-efficiency, low-noise homodyne measurement", *Review of Scientific Instruments* 89(6), 063120 (2018). https://doi.org/10.1063/1.5029859. Read in full in its arXiv version, arXiv:1803.06462v2. Cited for the photodiodes and the capacitance at the node, the NE3509M04 source follower and the reason for preferring it to a bipolar transistor, the gate resistor with its parallel inductor, and the bias (Sec. III A, p. 4, Fig. 4 and Table I).
- **[A24]** W. Bowden, A. Vianello and R. Hobson, "A low-noise resonant input transimpedance amplified photodetector", *Review of Scientific Instruments* 90, 106106 (2019). https://doi.org/10.1063/1.5114896. Read in full in its arXiv version, arXiv:1910.11941v1. Cited for the common-source CEL FET between the photodiode and the op amp (Fig. 1, pp. 1–2), the measured 1.2 pA/√Hz against 1.0 pA/√Hz (abstract and p. 2), and the prototypes with the op amp alone (pp. 1–2)."""
SIM_HEAD_OLD = "### Simulator and simulation models (Section 10)"
SIM_HEAD_NEW = "### Simulator and simulation models (Sections 10 and 11)"
SIM_PARA_OLD = ("The TI model packages [S3]–[S13] and [S18]–[S20] are not redistributed with this survey; they are "
                "downloaded from the product pages (Section 10.12).")
SIM_PARA_NEW = ("The TI model packages [S3]–[S13] and [S18]–[S21], and the Infineon and Linear Systems models "
                "[S22]–[S23], are not redistributed with this survey; they are downloaded from the manufacturers' pages "
                "(Section 10.12).")
S20_PREFIX = "- **[S20]**"
S21_S23 = r"""- **[S21]** Texas Instruments, *THS3491* model package SBOMBP9 (TINA-TI and PSpice "All In One" model, version 1.0 of 16 February 2018; file `ths3491.lib`, subcircuit THS3491RGT). https://www.ti.com/lit/zip/sbombp9
- **[S22]** Infineon Technologies, *BFP740ESD Gummel–Poon SPICE model*, version 2.0 (June 2011), file `bfp740esd-spice-v2.mdl`. https://www.infineon.com/assets/row/public/documents/24/70/bfp740esd-spice-v2.mdl
- **[S23]** Linear Systems, *Updated LSBF862 SPICE Model*, Rev 2 (9 February 2026); local copy `datasheets/fet_front_end/LSBF862_LinearSystems_SPICE_Rev2_2026-02-09.pdf`."""

# ------------------------------------------------------------------ Appendix 3
A3_DS_OLD = "and `fet_front_end/` the discrete FETs of Section 11.5 (Table A2.3) |"
A3_DS_NEW = ("`fet_front_end/` the discrete FETs and `bjt_front_end/` the bipolar transistor of Section 11.5 (Table A2.3), "
             "and `hv_output_stage/` the high-voltage amplifiers of Section 11.6 (Table A2.4) |")
A3_APPNOTES_OLD = "| `appnotes/` | the application notes and articles [A1]–[A22], and the ngspice manual [S1] |"
A3_APPNOTES_NEW = "| `appnotes/` | the application notes and articles [A1]–[A24], and the ngspice manual [S1] |"
A3_RESULTS_PREFIX = "| `spice/results/` |"
A3_NEW_ROWS = r"""| `spice/runs/composite/<check>/<case>/` | every ngspice deck of Sections 11.5–11.7 with its log and data files; `spice/runs/_models/` also holds the translated THS3491 library with its renamed subcircuits, `fet_cards.lib` and the translated BFP740ESD model (vendor files, not for redistribution) |
| `spice/results/composite_*.json` | one file per check of `scripts_archive/spice_composite_checks.py`; `composite_convergence.json` lists every convergence message by deck, with what was done about it (Table 11.13), and `composite_overlay_curves.json` the SPICE curves drawn on the THS3491 figures |
| `data/results/composite_analytical.json`, `composite_hv_fine_scan.json` | the analytical scans of Sections 11.5–11.6 (`scripts_archive/composite_tia.py`; the fine scan with `--fine`) |
| `data/digitization_checks/` | the THS3491 and OPA859 datasheet figures rendered with the readings drawn on them, the residuals against the figures' vector paths, TI's measured Fig 8-1 curves, and a manifest with the SHA-256 of every source (`scripts_archive/overlay_digitized.py`) |"""
A3_SCRIPTS_OLD = "the TINA-TI netlist extractor is `extract_tina_model.py`, the diagnostics are in `spice_diagnostics/` |"
A3_SCRIPTS_NEW = ("the TINA-TI netlist extractor is `extract_tina_model.py`, the diagnostics are in `spice_diagnostics/`; the "
                  "composites of Sections 11.5–11.7 use `composite_tia.py`, `spice_composite_checks.py`, "
                  "`overlay_digitized.py`, `composite_report_numbers.py` and `fet_front_end/phemt_stability_factors.py` |")

# ------------------------------------------------------------------ Appendix 4
A4_ADD = r"""
**High-voltage amplifier and RF transistors of Sections 11.5–11.6**
- THS3491: the open-loop transimpedance of Fig 8-22 (p16) does not reproduce the measured closed loop of Fig 8-1 (p13) through Eq. (71) with the 15-Ω inverting input (p9). Without a capacitance at the inverting node it gives 340 MHz at a gain of 2 against 730 MHz measured, and with 1.2 pF it gives 1.9 GHz and 3.6 dB of peaking at a gain of 5 against 944 MHz with none. Its magnitude lies above TI's model by 0.8 dB at 100–300 MHz and by 2.8 dB at 770 MHz, while its phase agrees with the model within 3.4°; the model reproduces Fig 8-1 at gains of 5–20 (Table 11.7).
- THS3491: no capacitance is given for the inverting input, although it sets the response at low gains (Eq. (71)); TI's model has 1.2 pF.
- SAV-551+: page 1 offers it as a replacement for Avago's ATF-55143, while footnote b on the same page names ATF-54143."""


def main():
    path = Path(sys.argv[1])
    with open(path, encoding="utf-8", newline="") as fh:      # keep the report's LF line ends
        t = fh.read()
    t = replace_once(t, READ_OLD, READ_NEW)
    t = replace_line(t, S07_HEAD_OLD, S07_HEAD_NEW)
    t = replace_line(t, S07_FET_OLD, S07_NEW)
    t = replace_line(t, S11_HEAD_OLD, S11_HEAD_NEW)
    t = replace_block(t, S11_LIST_START, S11_LIST_END, S11_LIST_NEW)
    t = replace_line(t, S115_HEAD_OLD, S115_HEAD_NEW)
    t = replace_line(t, B4_OLD, B4_NEW)
    t = append_after(t, EVEN_PREFIX, S115_INSERT)
    t = replace_line(t, WHERE_PREFIX, WHERE_NEW)
    t = replace_line(t, VERDICT_OLD, S116)
    t = replace_line(t, V1_OLD, V1_NEW)
    t = replace_line(t, VFET_OLD, VFET_NEW)
    t = replace_block(t, A1_START, A1_END, A1_NEW)
    t = replace_once(t, A23_CAPTION_OLD, A23_CAPTION_NEW)
    t = replace_once(t, A23_AMPS_OLD, A23_AMPS_NEW)
    t = replace_line(t, A23_ATF_OLD, A23_ATF_NEW)
    t = replace_line(t, A23_SAV_OLD, A23_SAV_NEW)
    t = replace_line(t, A23_CEL_PREFIX, A23_CEL_NEW)
    t = replace_line(t, APPNOTES_HEAD, A24_TABLE + "\n" + APPNOTES_HEAD)
    t = append_after(t, A22_LAST, A23_A24)
    t = replace_line(t, SIM_HEAD_OLD, SIM_HEAD_NEW)
    t = replace_once(t, SIM_PARA_OLD, SIM_PARA_NEW)
    t = append_after(t, S20_PREFIX, S21_S23)
    t = replace_once(t, A3_DS_OLD, A3_DS_NEW)
    t = replace_line(t, A3_APPNOTES_OLD, A3_APPNOTES_NEW)
    t = append_after(t, A3_RESULTS_PREFIX, A3_NEW_ROWS)
    t = replace_once(t, A3_SCRIPTS_OLD, A3_SCRIPTS_NEW)
    t = t.rstrip("\n") + "\n" + A4_ADD + "\n"
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(t)
    print("written", len(t.splitlines()), "lines")


if __name__ == "__main__":
    main()
