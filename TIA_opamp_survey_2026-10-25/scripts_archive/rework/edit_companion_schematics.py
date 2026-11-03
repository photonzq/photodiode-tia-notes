"""Insert the schematics of Chapters 7 and 8 (Figures 21-31) into TIA_opamp_survey.md, with
their references in the text, the new caption of Figure 1 and the Appendix E row.
Refuses to write unless the note still has the hash it had when it was read."""
import hashlib
from pathlib import Path

DOC = Path(__file__).resolve().parents[2] / "TIA_opamp_survey.md"
EXPECT = "134511f4e4fe"

raw = DOC.read_bytes()
assert hashlib.sha256(raw).hexdigest()[:12] == EXPECT, "note changed since it was read"
s = raw.decode("utf-8")
assert "\r" not in s


def rep(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:80])
    s = s.replace(a, b)


def fig(n, stem, caption):
    return f"\n![Figure {n}](figures/{stem}.png)\n\n*Figure {n}. {caption}*\n"


CAP = {}
CAP[1] = (
    "Inverting TIA for a balanced photodiode pair, with every capacitance that sets stability and noise; "
    "parasitic capacitances are drawn in grey. The upper photodiode delivers $i_1$ into the summing node and the "
    "lower one draws $i_2$ from it, so $R_F$ carries $i_1 - i_2$. $C_D = C_{D,A} + C_{D,B}$ is the capacitance of "
    "both diodes, $C_{\\mathrm{PCB}}$ that of the pads and traces at the node, and $C_{\\mathrm{CM}}$ and "
    "$C_{\\mathrm{DIFF}}$ the amplifier's common-mode and differential input capacitances; together they make the "
    "total capacitance from the inverting node to AC ground, "
    "$C_T = C_D + C_{\\mathrm{PCB}} + C_{\\mathrm{CM}} + C_{\\mathrm{DIFF}}$ (Section 4.1). $C_F$ is the total "
    "feedback capacitance, an optional external capacitor plus the parasitic capacitance of $R_F$ and its pads. "
    "The dashed current source is the optional DC servo of Chapter 8, and $R_S$ the optional 50-Ω "
    "back-termination into the instrument.")
CAP[21] = (
    "The discrete-transistor composite of Section 7.1, with the values of the pHEMT design of Table A7.4 "
    "(CE3512K2 at 10 mA). Q1 works in common source with its gate at the summing node $v_g$, and Q2, of the same "
    "type, works in common gate on top of it, which removes the Miller multiplication of Q1's gate–drain "
    "capacitance. $V_{B2}$ = 1.5 V holds Q2's gate and is bypassed to ground; it puts Q1's drain $v_x$ at 2 V, so "
    "both transistors see 2 V from drain to source and the same gate–source voltage at the shared current. "
    "$R_D$ = 1.1 kΩ from 15 V sets that current, 10 mA, with the drain $v_d$ at 4 V. $C_N$ = 8 pF from the drain to "
    "ground sets the gain–bandwidth product, $g_m/2\\pi(C_N + C_d)$, and with it the loop's crossover. The ideal "
    "level shift $V_{LS}$ = 4.5 V takes the drain's 4 V down to the gate's −0.5 V, so that the OPA859 unity-gain "
    "buffer and the output $v_o$ sit at the gate's DC voltage, as $R_F$ requires; the paragraphs on bias, package "
    "and layout explain why the source is lifted in practice. $R_F$ = 2 kΩ with $C_F$ = 0.55 pF closes the loop, "
    "and 200 Ω loads the buffer as in Chapter 5. The dashed $R_g$ is the optional gate stopper of Eq. (63). The "
    "bipolar design of Table A7.4 has the same circuit with BFP740ESD transistors at 1 mA, $R_D$ = 11.7 kΩ, "
    "$C_N$ = 4 pF, $C_F$ = 0.60 pF and Q1's emitter at −0.73 V. Amplifiers: OPA859 with CE3512K2 or BFP740ESD.")
CAP[22] = (
    "The dual-feedback high-voltage composite of Section 7.2, with the values of its $G_2$ = 5.5 design "
    "(Table A7.7). OPA859 on ±2.5 V, its non-inverting input grounded, is the first stage at the summing node. "
    "THS3491 on ±15 V follows as a non-inverting stage of gain $G_2 = 1 + R_{F2}/R_{G2}$ = 1 + 568 Ω/126 Ω = 5.5, "
    "with $R_{F2}$ interpolated from the datasheet's Table 9-2 and $R_{G2} = R_{F2}/(G_2 - 1)$. $R_F$ = 2 kΩ "
    "returns from the THS3491's output $v_2$, split into two 1-kΩ resistors in series because the total $C_F$ of "
    "0.100 pF lies below the parasitic capacitance of a single resistor (Section 8.10). $C_L$ = 3.25 pF from the "
    "OPA859's output $v_1$ closes the fast local loop that makes the composite stable; without it the circuit is "
    "the plain composite, which is unstable (Table A7.6). The THS3491 drives 100 Ω, the load of its datasheet "
    "characterization. Amplifiers: OPA859 and THS3491.")
CAP[23] = (
    "Option A for a single-ended detector: a resistive DC sink at the summing node, driven by a slow servo. "
    "$R_s = V_S/I_{\\mathrm{DC}}$ (Table A8.1) carries the photocurrent to its far end, which sits $V_S$ below "
    "$V_{\\mathrm{REF}}$: 500 Ω at 10 mA for $V_S$ = 5 V. The 10-nF capacitor makes that end an AC ground; with "
    "$R_s$ it sets a pole at 32 kHz, above which the servo's own noise no longer reaches the node (Eq. (69)), and "
    "the filter resistor keeps the capacitor off the integrator's output. The integrator senses $v_o$ on its "
    "non-inverting input and the set point $V_{set}$ through $R_i$ on its inverting input, with $C_i$ in its "
    "feedback, so it integrates $v_o - V_{set}$ without inversion. If the photocurrent rises, $v_o$ falls, the "
    "integrator lowers the far end of $R_s$, and $R_s$ draws the extra current: the loop through the inverting "
    "TIA is a negative-feedback loop. With $\\tau = R_iC_i$ its unity-gain frequency is $R_F/(2\\pi\\tau R_s)$, as "
    "in Eq. (80), placed at 1–10 kHz. A TIA on a single supply needs a negative rail for the integrator. "
    "Any amplifier.")
CAP[24] = (
    "Option B: the photodiode AC-coupled into the TIA. The photodiode's DC flows through $R_b$ from its anode to "
    "the negative bias $-V_{\\mathrm{bias}}$; 500 Ω drops 5 V at 10 mA. The RF reaches the summing node through "
    "$C_c$ = 10 nF, which with $R_b$ sets the low-frequency corner, $1/(2\\pi R_bC_c)$ = 32 kHz. Because the TIA's "
    "input impedance is a small inductance (Eq. (70)), almost all of the RF photocurrent enters the TIA rather "
    "than $R_b$ (Eq. (71)). Any amplifier.")
CAP[25] = (
    "Option C: an inductive bias tee at the summing node. The 1-µH choke $L_{\\mathrm{ch}}$ isolates the sink's "
    "capacitance and noise from the node at RF, and the photocurrent divides between $L_{\\mathrm{ch}}$ and the "
    "TIA's input inductance in the ratio $L_{\\mathrm{ch}}/(L_{\\mathrm{in}} + L_{\\mathrm{ch}})$. The choke still "
    "needs a sink, here $R_s$ to the bypassed far end and servo of Option A (Figure 23), and its own "
    "self-capacitance of 0.1–0.5 pF, drawn in grey, lands at the summing node. Any amplifier.")
CAP[26] = (
    "Option D: two-stage split gain. The first stage, OPA856 with $R_{F1}$ = 286 Ω and $C_{F1}$ = 1.6 pF, carries "
    "the whole DC: 10 mA through 286 Ω is 2.86 V, inside the 3.05 V that a 5-V part leaves. $C_c$ AC-couples its "
    "output into the second stage, OPA855 at a voltage gain $G_2$ = 7, so that $R_{F1}G_2$ = 2 kΩ; the resistor "
    "to ground gives the second stage's input its DC return and, with $C_c$, sets the low-frequency corner. The "
    "two-stage loop was not modelled. Amplifiers: OPA856 and OPA855.")
CAP[27] = (
    "Bootstrapping a photodiode. A unity-gain follower whose input is the summing node drives the photodiode's "
    "far, bias-side terminal through $C_c$, so the voltage across the photodiode capacitance $C_D$ (grey) stays "
    "constant and $C_D$ carries no current. $R_B$ feeds the DC bias from $+V_B$; the reactance of $C_c$ must stay "
    "well below $R_B$ in the band, or $R_B$ loads the follower. Eq. (73) gives the noise traded, for the 1-mA "
    "bipolar follower of Table A8.4. In the balanced pair the lower photodiode's anode is driven the same way "
    "through a second coupling capacitor. Any amplifier.")
CAP[28] = (
    "Cascoding the balanced pair. A common-base PNP, $Q_A$, passes the upper photodiode's current from its "
    "emitter to its collector at the summing node, and a common-base NPN, $Q_B$, does the same for the lower "
    "photodiode. Each base sits at a DC bias that sets its photodiode's reverse voltage and is bypassed to "
    "ground, so the photodiode capacitance sits at the low-impedance emitter node and the summing node sees only "
    "the two collector–base capacitances, $2C_\\mu$ (grey, 0.1–0.3 pF each). The dashed $R_q = V_q/I_q$ from "
    "±12 V are the optional standing currents of Eq. (76) and Table A8.6, which keep the emitter resistance, and "
    "with it the pole of Eq. (75), out of the band at low photocurrent; the two standing currents cancel at the "
    "summing node when they are equal. Any amplifier.")
CAP[29] = (
    "Servo on the optical split. A tunable splitter, for example a thermo-optic Mach–Zehnder on a photonic chip, "
    "divides the light between the two photodiodes. A slow integrator senses the TIA's output through an RC "
    "low-pass that keeps the RF out, compares it with the set point $V_{\\mathrm{REF}}$, and drives the "
    "splitter's heater until the DC output is zero. Nothing electrical is added at the summing node, and the RIN "
    "cancels together with the DC. Any amplifier.")
CAP[30] = (
    "The photocurrent divider of Hobbs' canceller applied to the pair, in the topology of [A22, Fig. 3]. The "
    "lower photodiode, made slightly stronger than the upper one, feeds the common emitters of the differential "
    "pair Q1/Q2. Q2 delivers the fraction $f$ of that current to the summing node and Q1 returns $1 - f$ to the "
    "supply $+V_{CC}$; the split depends only on the difference of the base voltages. Q2's base sits at a "
    "bypassed bias. The servo integrator senses the TIA's output through an RC low-pass, compares it with "
    "$V_{\\mathrm{REF}}$ and drives Q1's base through a divider of at least 20:1 with an RF bypass, so that its "
    "own noise stays small beside that of the base resistances (Eq. (78)). Q3, a common-base PNP, is the "
    "matching cascode on the upper photodiode, which isolates that photodiode's capacitance and matches the "
    "delay of the divided path (Table A8.10). Any amplifier.")
CAP[31] = (
    "The proposed balanced front end (Section 8.9, Table A8.10). Each photodiode bias, $\\pm V_B$ from a linear "
    "regulator, passes bulk capacitance, a ferrite bead (FB, about 430 Ω at 100 MHz) and a 100-Ω monitor "
    "resistor to one low-inductance 10-nF capacitor at the photodiode pin. The bead and the single capacitor keep "
    "the regulator noise that reaches the summing node through the photodiode capacitance below 0.1 pA/√Hz per "
    "pF from 10 to 200 MHz (Section 8.8 (e), Table A8.9), and the drop across each 100 Ω reads that diode's "
    "current, $I_1$ or $I_2$, at 1 V per 10 mA. Both photodiodes sit at the summing node, within 1–2 mm. The "
    "amplifier is OPA855 on 5 V with $V_{\\mathrm{REF}}$ = 2.58 V (variant A) or OPA818 on ±6.5 V with "
    "$V_{\\mathrm{REF}}$ = 0.1 V (variant B); $R_F$ is 2 kΩ, or 1.5 kΩ for more dynamic range, and the total "
    "$C_F$ 0.25 or 0.55 pF (Tables A8.11 and A8.13). The imbalance servo is that of Section 8.8 (d): the "
    "integrator, on ±12 V, senses the output through 1 kΩ and 1 nF (160 kHz), integrates its difference from "
    "$V_{\\mathrm{REF}}$ without inversion with $\\tau$ = 13 µs, and drives $R_s$ = 24 kΩ through 3.3 kΩ into "
    "10 nF in parallel with 100 pF (4.8 kHz), for ±0.5 mA of range and a high-pass corner of 1 kHz (Eq. (80)). "
    "Where the optics allow, the servo trims the optical split instead (Figure 29) and $R_s$ is left out. A "
    "second-order low-pass at 200–250 MHz sets the noise bandwidth before the ADC. Amplifiers: OPA855 "
    "(variant A) and OPA818 (variant B).")

# Figure 1: new caption
old1 = s[s.index("*Figure 1. Inverting TIA for a balanced photodiode pair"):]
old1 = old1[:old1.index("*\n") + 1]
rep(old1, f"*Figure 1. {CAP[1]}*")

# Section 7.1
rep("**The composite circuit.** The input transistor", "**The composite circuit (Figure 21).** The input transistor")
a = ("- The level shift is an ideal DC source in the simulations and sets the drain voltage. The summing node, and "
     "with it the output, sits at the DC voltage that the input transistor needs for its drain current (bias, "
     "package and layout, below).\n")
rep(a, a + fig(21, "fig21_discrete_composite", CAP[21]))

# Section 7.2
rep("**Two topologies.** In the plain composite,",
    fig(22, "fig22_hv_composite", CAP[22]).lstrip("\n") + "\n**Two topologies (Figure 22).** In the plain composite,")

# Section 8.2, Option A
rep("**Circuit.**\n- A resistor $R_s$ runs from the summing node",
    "**Circuit (Figure 23).**\n- A resistor $R_s$ runs from the summing node")
i = s.index("- For the anode-on-node orientation the far end of $R_s$")
j = s.index("\n", i) + 1
s = s[:j] + fig(23, "fig23_option_a", CAP[23]) + s[j:]

# Section 8.3, Option B
rep("**Circuit.**\n- The photodiode's DC flows through a resistor $R_b$",
    "**Circuit (Figure 24).**\n- The photodiode's DC flows through a resistor $R_b$")
a = "- The TIA never sees the DC, and no servo is needed.\n"
rep(a, a + fig(24, "fig24_option_b", CAP[24]))

# Section 8.4, Option C
a = ("A choke $L_{\\mathrm{ch}}$ in series with the DC path isolates the sink's capacitance and noise from the "
     "summing node at RF.\n")
rep(a, a.replace("at RF.\n", "at RF (Figure 25).\n") + fig(25, "fig25_option_c", CAP[25]))

# Section 8.5, Option D
rep("**Circuit.** A first TIA with a small $R_{F1}$", "**Circuit (Figure 26).** A first TIA with a small $R_{F1}$")
i = s.index("**Circuit (Figure 26).** A first TIA")
j = s.index("\n", i) + 1
s = s[:j] + fig(26, "fig26_option_d", CAP[26]) + s[j:]

# Section 8.6, bootstrapping
rep("**The idea.** The amplifier's voltage noise", "**The idea (Figure 27).** The amplifier's voltage noise")
i = s.index("Hobbs uses the idea on a large-area photodiode")
j = s.index("\n", i) + 1
s = s[:j] + fig(27, "fig27_bootstrap", CAP[27]) + s[j:]

# Section 8.7, cascoding
rep("**The balanced pair needs a complementary pair.**", "**The balanced pair needs a complementary pair (Figure 28).**")
i = s.index("Hobbs' differential noise canceller uses exactly this arrangement")
j = s.index("\n", i) + 1
s = s[:j] + fig(28, "fig28_cascode", CAP[28]) + s[j:]

# Section 8.8 (b), (c), (d), (e)
rep("**(b) Servo on the optical split, preferred where the optics allow.**",
    "**(b) Servo on the optical split, preferred where the optics allow (Figure 29).**")
a = "- It is as fast as its actuator: kilohertz for a thermo-optic phase shifter, ample for drift.\n"
rep(a, a + fig(29, "fig29_optical_servo", CAP[29]))
rep("Applied here, the pair can divide either of two currents:",
    "Applied here, the pair can divide either of two currents, and Figure 30 draws the first:")
i = s.index("- a small third photocurrent from a sample of the light")
j = s.index("\n", i) + 1
s = s[:j] + fig(30, "fig30_current_splitter", CAP[30]) + s[j:]
rep("*The loop.*\n", "*The loop (drawn in Figure 31).*\n")
rep("A single low-inductance capacitor at the pin, fed through a ferrite bead and the monitor resistor, keeps",
    "A single low-inductance capacitor at the pin, fed through a ferrite bead and the monitor resistor "
    "(Figure 31), keeps")

# Section 8.9
rep("Table A8.10 lists these parts with their reasons.",
    "Figure 31 draws the front end, and Table A8.10 lists its parts with their reasons.")
a = "Which variant is better depends on where the RF signal lies (Table A6.28), so both are carried here."
rep(a,fig(31, "fig31_front_end", CAP[31]).lstrip("\n") + "\n" + a)

# Appendix E
rep("| `figures/` | Figures 1–20 as PNG (600 dpi) and PDF.", "| `figures/` | Figures 1–31 as PNG (600 dpi) and PDF.")
rep("`fig01` is Figure 1 (`scripts_archive/make_circuit_figure.py`);",
    "`fig01` and `fig21`–`fig31` are Figure 1 and the schematics of Chapters 7 and 8, Figures 21–31 "
    "(`scripts_archive/make_schematics.py`, in the shared style of `scripts_archive/schematic_style.py`);")

out = s.encode("utf-8")
DOC.write_bytes(out)
print("written", hashlib.sha256(out).hexdigest()[:12], "figures:", s.count("](figures/"))
