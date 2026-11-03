"""Renumber the figures of the high-gain note and insert its eleven schematics.

Old Figures 1-12 become 2, 3, 5, 10, 11 and 17-23; the schematics take 1, 4, 6-9 and 12-16.
Every edit is anchored on text that must occur exactly once; nothing is written unless all
of them apply.  11_appendix_a.md (generated) carries no figure numbers and is not touched."""
import re
from pathlib import Path

PARTS = Path(__file__).resolve().parents[1] / "parts"
OLD2NEW = {1: 2, 2: 3, 3: 5, 4: 10, 5: 11, 6: 17, 7: 18, 8: 19, 9: 20, 10: 21, 11: 22, 12: 23}

names = ["00_front.md", "01_problem.md", "02_noise.md", "03_bandwidth.md", "04_maps.md", "05_amplifiers.md",
         "06_selection.md", "07_beyond.md", "08_dc_errors.md", "09_checks.md", "10_conclusions.md",
         "12_appendix_b_e.md"]
txt = {n: (PARTS / n).read_text(encoding="utf-8") for n in names}
for n, t in txt.items():
    assert "\r" not in t, n

# ---- 1. renumber the existing singular references, then the plural ones
for n in names:
    txt[n] = re.sub(r"Figure (\d+)", lambda m: f"Figure {OLD2NEW[int(m.group(1))]}", txt[n])


def rep(n, a, b):
    assert txt[n].count(a) == 1, (n, txt[n].count(a), a[:90])
    txt[n] = txt[n].replace(a, b)


rep("04_maps.md", "Figures 4 and 5", "Figures 10 and 11")
rep("12_appendix_b_e.md", "Figures 6–12", "Figures 17–23")
rep("12_appendix_b_e.md", "- `hg_figures.py` draws Figures 1–5.\n",
    "- `hg_figures.py` draws Figures 2, 3, 5, 10 and 11, and `hg_schematics.py` the schematics, Figures 1, "
    "4, 6–9 and 12–16, in the drawing style of `schematic_style.py`.\n")
rep("12_appendix_b_e.md", "| `figures/` | Figures 1–12 as PNG (600 dpi) and PDF |",
    "| `figures/` | Figures 1–23 as PNG (600 dpi) and PDF. The plots keep the names under which they were "
    "first drawn: `fig1`–`fig5` are Figures 2, 3, 5, 10 and 11, and `fig6`–`fig12` are Figures 17–23. "
    "The schematics are the files `schem_*` |")


def fig(num, stem, caption):
    return f"\n![Figure {num}](figures/{stem}.png)\n\n*Figure {num}. {caption}*\n"


def insert_after_line(n, start, block):
    """Insert block after the (unique) line that starts with `start`."""
    t = txt[n]
    i = t.index(start)
    assert t.count(start) == 1, (n, start[:60])
    j = t.index("\n", i) + 1
    txt[n] = t[:j] + block + t[j:]


def insert_before_line(n, start, block):
    t = txt[n]
    assert t.count(start) == 1, (n, start[:60])
    i = t.index(start)
    txt[n] = t[:i] + block.lstrip("\n") + "\n" + t[i:]


CAP = {
    1: ("The inverting TIA of this note with every element of Eq. (8). The photodiode delivers the photocurrent "
        "$I_{ph}$ into the summing node; its cathode sits at ground (zero bias) or at a reverse bias $V_B$. Grey "
        "elements are the capacitances and the shunt resistance that the circuit cannot avoid: the photodiode's "
        "$C_D$ and $R_{sh}$, the board's $C_{PCB}$, the amplifier's input capacitances $C_{CM} + C_{DIFF}$, and "
        "the feedback capacitance $C_F$, the resistor's own $C_{par}$ plus any capacitor $C_{add}$ placed on "
        "purpose. The noise sources are purple: $i_R$, the Johnson noise of $R_F$; $i_{PD}$, the photodiode's "
        "thermal noise $4k_BT/R_{sh}$ together with the shot noise $2q\\,(I_{ph} + I_D)$; the amplifier's "
        "current noise $i_n$; and its voltage noise $e_n$, in series with the grounded non-inverting input. All "
        "but $e_n$ are currents at the summing node and are referred to the input unchanged (Section 2.1)."),
    4: ("The feedback resistor's film as a ladder of $N$ slices. Each slice is a resistance $R/N$ in series with "
        "its neighbours, with a capacitance $C_g/N$ to the conductor beneath the film, which is held at "
        "$a(u)\\,V_{out}$ at the position $u$, from 0 at the summing-node end cap to 1 at the output end cap. "
        "$C_{ee}$, from end cap to end cap, is an ordinary lumped capacitance. A grounded plane has $a = 0$, a "
        "plane driven at a fraction of the output $a = \\alpha$, and a graded guard $a = u$. As $N$ grows the "
        "ladder becomes the uniform RC line of Eq. (25); Section 9.4 simulates it with $N$ = 20."),
    6: ("Three ways to drive the conductor beside the feedback resistor, each from the output and never from the "
        "summing node. (a) A plane at $V_{out}/3$, from a divider of 2 kΩ over 1 kΩ, cancels the plane's "
        "low-frequency effect on the feedback path (Eq. (28) with $\\alpha = 1/3$). (b) Four strips at "
        "$V_{out}/8$, $3V_{out}/8$, $5V_{out}/8$ and $7V_{out}/8$, each at the mid-point potential of its quarter "
        "of the film, from a divider of 1, 2, 2, 2 and 1 kΩ; they leave $C_g/192$. (c) The ideal graded guard, a "
        "resistive film beside $R_F$ that is grounded at the summing-node end and tied to the output at the "
        "other, so that its potential follows that of $R_F$ everywhere; this is the principle of Seidl, Swoboda "
        "and Zimmermann's CCDR. In all three the summing node keeps its own guard ring at its potential, ground "
        "(Section 8.2), between it and the nearest driven copper. Divider resistors of a few kilohms put only "
        "nanovolts of noise on the conductor, which reach the summing node through $C_g$."),
    7: ("A 1-GΩ feedback resistor split into three 333-MΩ resistors with guarded junctions, the arrangement "
        "proposed above and not simulated (Appendix C, item 16). Each junction pad sits inside a guard held at its "
        "own low-frequency potential, $V_{out}/3$ or $2V_{out}/3$, so that the pad's capacitance to its "
        "surroundings carries no current, and each resistor body has a strip at its mid-point potential, "
        "$V_{out}/6$, $V_{out}/2$ or $5V_{out}/6$. One divider of six equal resistors of 1 kΩ between the output "
        "and ground supplies all five potentials. With matched end-to-end capacitances the string is then exactly "
        "$R\\parallel C_{ee}/3$ (Appendix B.5, Step 10). The summing node keeps its own guard ring at ground."),
    8: ("Equalization and its calibration. The equalizer after the TIA, $(1 + sR_FC_F)/(1 + sR_FC_F/k)$, cancels "
        "the resistor's pole and widens the band by $k$; it does not change the input-referred noise density. To "
        "measure the resistor's actual response, which the distributed capacitance of Section 3.4 makes differ "
        "from a single pole, a generator drives the known current $i = j\\omega C_{inj}V$ into the summing node "
        "through a small capacitor $C_{inj}$, drawn dashed because it is connected only during the calibration, "
        "and $C_{ee}$ and $C_g$ are fitted to the measured transimpedance."),
    9: ("Two ways to reach 1 GΩ with a 10-MΩ resistor (Table 3.1). (a) A T-network: $R_1$ = 10 MΩ from the "
        "summing node to the node T, $R_2$ = 9.9 kΩ from T to the output and $R_3$ = 100 Ω from T to ground, so "
        "that $k = 1 + R_2/R_3$ = 100 and the transimpedance is $kR_1$ (Eq. (29a)); the whole Johnson noise "
        "current of $R_1$ reaches the input. (b) The same 10 MΩ alone, followed by a voltage stage of gain 100: "
        "the same noise floor and offset, and $\\sqrt{100}$ = 10 times the amplifier-limited bandwidth of the T "
        "(Eq. (29b))."),
    12: ("The discrete-JFET composite simulated in Section 9.5. J1, an LSBF862 in common source with its gate at "
         "the summing node, is cascoded by J2, whose gate is held at 2.5 V and bypassed. $R_D$ = 1 kΩ from 15 V "
         "carries 10 mA with the drain at 5 V, so the stage's voltage gain $g_mR_D$ is about 33. The integrator "
         "senses the drain against 5 V: its non-inverting input is on the drain and its inverting input returns "
         "to 5 V through 1 kΩ, so the loop settles with the drain at 5 V. With $C_c$ = 106 pF in its feedback its "
         "unity-gain frequency is $1/(2\\pi\\times1\\ \\mathrm{k\\Omega}\\times106\\ \\mathrm{pF})$ = 1.5 MHz, "
         "which with the gain of about 33 gives the composite the 50 MHz of gain–bandwidth assumed in the sweep. "
         "$R_F$ and $C_F$ return from the integrator's output to J1's gate, where the photodiode's $C_D$ and "
         "$R_{sh}$ also sit. In SPICE the integrator is an ideal transconductance-and-capacitor stage."),
    13: ("Gain ranging with T-switches. Each range's feedback resistor connects to the summing node through an "
         "inner switch $S_{in}$ and an outer switch $S_{out}$, and a shunt switch $S_{sh}$ ties their junction to "
         "ground, the summing node's potential, while the range is off. Range 1 is selected: $S_{in}$ and "
         "$S_{out}$ are closed and $S_{sh}$ is open. In range 2 the outer switch carries the output voltage, but "
         "its leakage flows into the closed shunt, and the inner switch sees almost no voltage and so leaks almost "
         "nothing. Each switch's capacitance adds to $C_F$ when closed and to $C_T$ when open, and each change of "
         "range injects charge."),
    14: ("The transdiode logarithmic amplifier. The transistor Q replaces $R_F$: its collector is at the summing "
         "node, its base at ground and its emitter is driven by the output, so its collector current equals the "
         "photocurrent and the output is $-V_T\\ln(I_{ph}/I_S)$ (Eq. (31)). The compensation capacitor $C_C$ "
         "across it sets the bandwidth, $I/(2\\pi V_TC_C)$ (Eq. (33)), and the optional emitter resistor $R_E$ "
         "limits the loop gain at the top of the range (Eq. (34))."),
    15: ("A switched integrator in the arrangement of IVC102. The input switch $S_1$ connects the photodiode "
         "during the integration and disconnects it to hold. The photocurrent charges $C_{int}$, which IVC102 "
         "provides as 10, 30 and 60 pF on chip, alone or together up to 100 pF, and the reset switch $S_2$ "
         "discharges it before each measurement. The ADC samples the output once after the reset, $V_1$, and once "
         "after the integration time $T$, $V_2$. The charge is $C_{int}(V_2 - V_1)$, and the double sampling "
         "removes the reset noise and the charge that $S_2$ injects."),
    16: ("Optical reset of a charge-sensitive preamplifier for a cooled semiconductor detector (LBL-8135, "
         "LBL-13214). The detector's charge is integrated on a feedback capacitor of about 0.5 pF around the input "
         "FET and the rest of the inverting amplifier. When the output crosses the upper threshold of the window "
         "comparator, the LED is switched on; its light raises the current of the FET's drain–gate junction to "
         "0.1–1 µA, which discharges $C_F$ in 1–10 µs, until the lower threshold switches the LED off. Nothing is "
         "added at the gate between resets. Detector, FET, $C_F$ and LED sit together in the cryostat."),
}

# ---- 2. Section 1.1
rep("01_problem.md", "and the output is $V_{out} = -I_{ph}R_F$.\n",
    "and the output is $V_{out} = -I_{ph}R_F$. Figure 1 shows the circuit with every element that the analysis "
    "of this note uses.\n")
insert_before_line("01_problem.md", "These are the conventions of the companion note (its Section 1)",
                   fig(1, "schem_tia_noise", CAP[1]))

# ---- 3. Section 3.4
rep("03_bandwidth.md", "**The model.** Imagine the film cut into many short slices.",
    "**The model.** Imagine the film cut into many short slices (Figure 4).")
insert_after_line("03_bandwidth.md", "which plays the role of the line's electrical length.",
                  fig(4, "schem_rc_line", CAP[4]))
rep("03_bandwidth.md", "On a board the drive comes from a resistive divider between the output and ground, never from "
    "the summing node.",
    "On a board the drive comes from a resistive divider between the output and ground (Figure 6), never from "
    "the summing node.")
insert_after_line("03_bandwidth.md", "On a board the drive comes from a resistive divider between the output and "
                  "ground (Figure 6)", fig(6, "schem_guard_drives", CAP[6]))
rep("03_bandwidth.md", "surrounded by a guard held at its own low-frequency potential $u_kV_{out}$, the junction",
    "surrounded by a guard held at its own low-frequency potential $u_kV_{out}$ (Figure 7), the junction")
insert_after_line("03_bandwidth.md", "- If instead each junction pad is surrounded by a guard",
                  fig(7, "schem_split_resistor", CAP[7]))

# ---- 4. Section 3.5
rep("03_bandwidth.md", "$(1 + sR_FC_F)/(1 + sR_FC_F/k)$, which widens the band by $k$.",
    "$(1 + sR_FC_F)/(1 + sR_FC_F/k)$, which widens the band by $k$ (Figure 8).")
insert_after_line("03_bandwidth.md", "**Equalization.** In the resistor-limited regime", fig(8, "schem_equalizer", CAP[8]))
rep("03_bandwidth.md", "**The T-network.** A T-network replaces the single feedback resistor",
    "**The T-network.** A T-network (Figure 9 (a)) replaces the single feedback resistor")
rep("03_bandwidth.md", "*A voltage stage instead.* A TIA with $R_1$, followed by a voltage stage of gain $k$, has",
    "*A voltage stage instead.* A TIA with $R_1$, followed by a voltage stage of gain $k$ (Figure 9 (b)), has")
insert_after_line("03_bandwidth.md", "A 10-MΩ resistor with $k$ = 100 thus gives 1 GΩ.", fig(9, "schem_t_network", CAP[9]))

# ---- 5. Section 5.8
rep("05_amplifiers.md", "A SPICE model of such a composite confirms the estimate (Section 9.5).",
    "A SPICE model of such a composite confirms the estimate (Section 9.5, Figure 12).")
insert_after_line("05_amplifiers.md", "A SPICE model of such a composite confirms the estimate",
                  fig(12, "schem_jfet_composite", CAP[12]))

# ---- 6. Chapter 7
rep("07_beyond.md", "with a shunt switch that ties their junction to the summing node's potential when open.",
    "with a shunt switch that ties their junction to the summing node's potential when open (Figure 13).")
insert_before_line("07_beyond.md", "The on-resistance of a switch in series with $R_F$ is negligible",
                   fig(13, "schem_gain_ranging", CAP[13]))
rep("07_beyond.md", "gives a transdiode logarithmic amplifier.", "gives a transdiode logarithmic amplifier (Figure 14).")
insert_before_line("07_beyond.md", "**Bandwidth.** The small-signal resistance of the transistor",
                   fig(14, "schem_log_amp", CAP[14]))
rep("07_beyond.md", "and then resets $C_{int}$ with a switch.", "and then resets $C_{int}$ with a switch (Figure 15).")
insert_after_line("07_beyond.md", "A switched integrator collects the photocurrent on a capacitor",
                  fig(15, "schem_integrator", CAP[15]))
rep("07_beyond.md", "an LED optically coupled to the FET is switched on.",
    "an LED optically coupled to the FET is switched on (Figure 16).")
insert_before_line("07_beyond.md", "For a photodiode integrator on a board, the lesson is the same",
                   fig(16, "schem_optical_reset", CAP[16]))

# ---- 7. Section 8.4 points at the drives
rep("08_dc_errors.md", "from a resistive divider between the output and ground (Section 3.4, Table 9.4).",
    "from a resistive divider between the output and ground (Section 3.4, Figure 6, Table 9.4).")

for n in names:
    (PARTS / n).write_text(txt[n], encoding="utf-8", newline="\n")
print("written")
