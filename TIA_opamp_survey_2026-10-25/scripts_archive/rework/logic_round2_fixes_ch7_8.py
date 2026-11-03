r"""Reviewed fixes of the logic round of 1 Nov 2026 for Chapters 7 and 8, read by edit_logic_round2.py.

Section 7.1 states its question first and puts the device physics (Eq. (59)) before the verdicts it
explains; Section 7.2 opens with the specification and ends with a verdict; Section 8.9 says what the
front end is before its two variants, and states each variant once, with the macromodel and the
datasheet curve side by side; Section 8.10 gives one window per part.
"""

INTRO_71 = r"""This section asks whether a discrete transistor at the summing node, a FET or a SiGe bipolar transistor, can lower the floor enough to matter below about 0.15 mA, where the noise still sets the dynamic range (Section 6.6.3)."""

WHY_71 = r"""**Why the question arises.** In our analytical model at its SPICE design, OPA855's input noise at 100 MHz, 4.17 pA/√Hz, is $\sqrt{2.87^2 + 2.60^2 + 1.54^2}$ pA/√Hz. Of this, 2.87 pA/√Hz is the Johnson noise of $R_F$, 2.60 pA/√Hz the bipolar input current noise, and 1.54 pA/√Hz its $e_n$ of 0.99 nV/√Hz acting on 2.36 pF of node and feedback capacitance, together with the small $e_n/R_F$ term (Eq. (23)). At this node OPA855 thus loses more to its base current than to its voltage noise. A FET removes the current noise but adds its own capacitance, and Eq. (56) below decides which effect wins. OPA955, with 0.56 pA/√Hz of current noise, has little to remove. OPA818's current noise is negligible in the central treatment of Section 4.7, but its 2.2-nV/√Hz voltage noise on 4.24 pF gives it the largest dark band noise of the three, 84.8 nA rms, and the most to gain (Table A7.1)."""

OPEN_72 = r"""From about 0.15 mA up the dynamic range follows the output amplitude dB for dB (Section 6.6.3, Figure 19), and Section 7.1 shows that no input transistor changes that. Raising $V_{\mathrm{pk}}$ at 100 MHz from OPA818's 2.23 V to 10 V would add $20\log_{10}(10/2.23)$ = 13.0 dB at every photocurrent at unchanged noise; that needs a slew rate of at least $2\pi \times 100\ \mathrm{MHz} \times 10\ \mathrm{V}$ = 6.3 kV/µs and rails of about ±12 V. This section builds that composite: a first stage at the summing node, which sets the noise, driving a fast high-voltage amplifier inside the $R_F$ loop."""

VERDICT_72 = r"""**Verdict.** The high-voltage composite pays wherever the dynamic range follows the ceiling: at a 100-MHz tone it adds 7.8, 9.1, 11.1 and 11.9 dB to OPA818 at 0, 0.1, 1 and 10 mA, although its band noise is 136.5/84.8 = 1.6 times OPA818's. The price is ±15-V rails and 1.04 W in the THS3491, about −47 dBc HD3 at full swing, and robustness only at $G_2$ = 4–5.5 with a total $C_F$ of 0.100–0.125 pF."""

OPEN_89 = r"""The arguments of Sections 8.1–8.8 fix everything except the amplifier. In the balanced pair only the imbalance reaches $R_F$ (Section 8.1), so none of the DC sinks of Sections 8.2–8.5 is needed. Bootstrapping and cascoding add more noise than they remove at 0.5–1 pF and lower the noise gain of the decompensated amplifiers (Sections 8.6 and 8.7), so both photodiodes connect directly to the summing node, within 1–2 mm of it. The imbalance is nulled by trimming the optical split where the optics allow, because that adds nothing at the node and nulls the RIN with the DC (Section 8.8 (b)). Otherwise a 24-kΩ resistor to a ±12-V integrator covers ±0.5 mA for 0.83 pA/√Hz (Section 8.8 (d)), and the current splitter of Section 8.8 (c) is kept for a large imbalance with a noisy laser. Each bias pin is fed through a ferrite bead and a 100-Ω monitor resistor to a single low-inductance capacitor, which keeps the injected noise below 0.1 pA/√Hz per pF from 10 to 200 MHz (Section 8.8 (e)). A second-order low-pass at 200–250 MHz after the TIA sets the noise bandwidth (Section 6.3.3). Table A8.10 lists these parts with their reasons. The front end is designed for 0.5–1 pF in each photodiode and up to 10 mA in each diode, and its two variants differ only in the amplifier and its feedback capacitance:"""

NOTE_89 = r"""*Note on variant A's flagged corners.* The corners flagged in Table A8.11 lie at the upper $C_F$ corner with high open-loop gain, where $NG_\infty = 1 + C_T/C_F$ falls to 6.3–7.7, around the minimum stable gain of 7. There the analytical model finds a second loop-gain crossing at the plotted 4–7 GHz bump, while the main crossover keeps 50–63°. The plotted bump overstates the real one (Table A4.5), as for Table A6.13, but the macromodel shows that these corners do lose margin: the gain margin at 3–4 GHz falls to 1.4–3.1 dB, and 3 dB needs $NG_\infty \ge 7.5$ (Eq. (47), Section 5.5). Variant A therefore needs the tighter $C_F$ tolerance of Section 8.10. The 2-pF designs leave more room: the flag appears at 1 corner of 27 at 2 kΩ."""

WINDOW_810 = r"""- **Window and target.** In the vendor's macromodel the window over ±0.2 pF of photodiode capacitance is 0.157–0.300 pF at 2 kΩ: peaking sets its lower edge, and a 3-dB gain margin at 3–4 GHz, i.e. $C_F \le C_T/6.5$ (Eq. (47)), sets its upper edge (Table A5.8). The total $C_F$ should therefore be 0.230 ± 0.070 pF at 2 kΩ and 0.240 ± 0.055 pF at 1.5 kΩ, or be trimmed (Table A5.9). The datasheet curve gives the wider 0.15–0.36 pF at 2 kΩ and 0.17–0.36 pF at 1.5 kΩ, whose upper edge is the minimum-gain rule $C_F \le C_T/6$; it would accept ±0.1 pF around 0.25 pF at 2 kΩ and about ±0.08 pF at 1.5 kΩ. The OPA855 rows of Table A8.13 are these datasheet-curve designs. No discrete capacitor is needed if the resistor and pads give 0.2–0.25 pF."""

FIXES = [
    # ---- Section 7.1 ----
    ("delete", "**Why the question arises.** In our analytical model at its SPICE design", "have little to remove."),
    ("replace",
     "Section 6.6.3 showed that from about 0.15 mA up the ceiling, not the noise, sets the dynamic range. This section asks whether a discrete FET at the summing node could still lower the floor enough to matter below that. The front end considered is",
     INTRO_71 + "\n\n" + WHY_71 + "\n\nThe front end considered is"),
    ("replace", "In the receiver's range of 0.1–10 mA, no front end can gain more than 0.80 dB over OPA855 or 0.19 dB over OPA955.",
     "In the receiver's range of 0.1–10 mA, no front end can gain more than 0.80 dB over OPA855, 0.19 dB over OPA955 or 2.98 dB over OPA818, each at its own ceiling. The composites below keep the 1.5-V ceiling of their OPA859 buffer, so OPA955, with nearly the same ceiling, is the design they have to beat."),
    ("move", "**Why a pHEMT or a SiGe bipolar transistor rather than a silicon JFET.**", "and low 1/f noise matter.",
     "**Silicon JFETs do not work at 1 pF.**", "before"),
    ("replace", " JFET composites pay off with photodiodes of tens of picofarads, not at 1 pF.", ""),
    ("replace", "- Nothing is specified below 0.5 GHz, so their 1/f and trap noise across 1–150 MHz is unknown.",
     "- No noise is specified below 0.5 GHz, so their 1/f and trap noise in the 150-MHz band is unknown."),
    ("replace", "18 with each kind of transistor ($C_N$ = 0–60 pF, $C_F$ = 0.20–0.60 pF)",
     "18 with the three FETs (six each) and 18 with the bipolar transistor ($C_N$ = 0–60 pF, $C_F$ = 0.20–0.60 pF)"),
    ("replace", "(bias, package and layout, below), Eq. (49) gives 84.2, 77.5, 68.5 and 58.6 dB",
     "(bias, package and layout, below), Eq. (50) gives 84.2, 77.5, 68.5 and 58.6 dB"),
    ("replace", "(`scripts_archive/fet_front_end/phemt_stability_factors.py`)",
     "(`scripts_archive/fet_front_end/phemt_stability_factors.py`, run on the S-parameter files that CEL publishes with CE3512K2)"),
    ("paragraph", "**Where a composite pays off is the ceiling, not the noise.**",
     "A discrete transistor at the summing node therefore lowers the floor by no more than the bound of Table A7.1, which the pHEMT and bipolar composites approach; from 0.1 mA up the dynamic range has to come from the ceiling."),
    # ---- Section 7.2 ----
    ("replace",
     "Section 6.6.3 showed that from about 0.15 mA up the output amplitude sets the dynamic range, and Section 7.1 that no input transistor changes that. This section raises the ceiling instead: a fast, high-voltage amplifier inside the $R_F$ loop takes the output to several volts while a low-noise first stage still sets the noise.",
     OPEN_72),
    ("replace", "It needs a slew rate of $2\\pi f_0V_{\\mathrm{pk}}$, 6.3 kV/µs for 10 V at 100 MHz, rails of ±12 V or more, and a closed-loop bandwidth",
     "Besides that slew rate, $2\\pi f_0V_{\\mathrm{pk}}$, and rails of ±12 V or more, it needs a closed-loop bandwidth"),
    ("replace",
     "These readings, and every other THS3491 curve used here, were checked by drawing them on the rendered figures (`data/digitization_checks/`, `scripts_archive/overlay_digitized.py`); their largest residuals against the figures' vector paths are 0.008 Vpp, 0.005 dB and 0.005°.",
     "These readings, and every other THS3491 curve used here, were checked against the figures' vector paths with `scripts_archive/overlay_digitized.py`, which also draws them on the datasheet figures; the largest residuals, in `data/digitization_checks/`, are 0.008 Vpp, 0.005 dB and 0.005°."),
    ("replace",
     "OPA859, unity-gain stable with 900 MHz of gain–bandwidth and 3.3 nV/√Hz at 1 MHz on ±2.5 V (Section 6.1.1), is the part among our candidates that fits.",
     "Among our unity-gain-stable candidates OPA859, with 900 MHz of gain–bandwidth and 3.3 nV/√Hz at 1 MHz on ±2.5 V (Section 6.1.1), is the one that fits: it reaches its 1.50-V swing at 100 MHz, while the quieter OPA856 (0.91 nV/√Hz) slews only 0.56 V there and THS4304 only 1.26 V (Table A6.26), which would cap the composite at that amplitude times $\\lvert H_2\\rvert$. Its voltage noise is the price, and it dominates the composite's noise (below)."),
    ("replace", "with less $C_L$ the phase margin fails, and with more the bandwidth.",
     "with less $C_L$ the phase margin fails, and with more the bandwidth. A total $C_F$ of 0.100–0.125 pF lies below the 0.2-pF nominal parasitic of one resistor and its pads (Table 1.1), and its −0.1-pF corner reaches 0.000–0.025 pF. It needs $R_F$ split into two series resistors of $R_F/2$, which TI advises for a $C_F$ below 0.15 pF (Section 8.10), and a parasitic measured on the board; the robust window assumes both. Both scans start at 0.10 pF, so smaller values were not explored."),
    ("replace", "with $\\lvert Z_T\\rvert$ = $R_F$ the composite gives 86.6, 85.6, 81.1 and 72.4 dB.",
     "with $\\lvert Z_T\\rvert$ = $R_F$ the composite gives 86.6, 85.6, 81.1 and 72.4 dB. To use OPA818's 70.7 dB at 1 mA in 150 MHz, an ADC whose full scale matches the TIA's largest tone needs a noise spectral density of $-70.7 - 10\\log_{10}(150\\ \\mathrm{MHz})$ = −152.5 dBFS/Hz, and the composite's 81.8 dB needs −163.6 dBFS/Hz."),
    ("replace", "On ±15 V the THS3491 draws 16.7 mA (p9), 0.50 W at rest.",
     "On ±15 V the THS3491 draws 16.7 mA (p9), 0.50 W at rest (Table A7.9)."),
    ("replace", "\n### 7.3 SPICE models, decks and convergence for the composites\n",
     "\n" + VERDICT_72 + "\n\n### 7.3 SPICE models, decks and convergence for the composites\n"),
    # ---- Section 7.3 and its tables ----
    ("replace", "Table A7.10 lists the models.",
     "Table A7.10 lists the models. They are not distributed with this note: the OPA859 [S8] and THS3491 [S21] packages come from TI's product pages and the BFP740ESD model [S22] from Infineon's, and `spice_composite_checks.py` expects them under `spice/models/` and writes the cards of Table A7.10 itself."),
    ("replace", "dynamic range at a 100-MHz tone by Eq. (49) with the buffer's 1.5 V",
     "dynamic range at a 100-MHz tone by Eq. (50) with the buffer's 1.5 V"),
    ("replace", "dynamic range at a 100-MHz tone by Eq. (49). OPA818's design", "dynamic range at a 100-MHz tone by Eq. (50). OPA818's design"),
    ("replace", "and the dynamic range by Eq. (49) with the output held to that swing", "and the dynamic range by Eq. (50) with the output held to that swing"),
    ("replace", "The diagnostic scripts of Appendix B.1, Section 5.3 and Section 6.5 are in `scripts_archive/spice_diagnostics/`.",
     "The diagnostic scripts of Appendix B.1, Section 5.3 and Section 6.5 are in `scripts_archive/spice_diagnostics/`. The composites of Chapter 7 run from `scripts_archive/spice_composite_checks.py` (Section 7.3), with the OPA859, THS3491 and BFP740ESD models of Table A7.10 under `spice/models/`."),

    # ---- Section 8.1 ----
    ("paragraph", "- **A single-ended detector at these currents is not possible.**",
     "- **A single-ended detector cannot carry these currents through $R_F$.** At 2 kΩ the DC alone would need 0.2 V at 0.1 mA, 2 V at 1 mA and 20 V at 10 mA of output swing (Table A6.25). The 5-V parts would lose RF headroom above about 0.8 mA, OPA818 above about 4.4 mA, and every part fails at 10 mA. A single-ended detector, or a pair whose imbalance is too large for the servos of Section 8.8, therefore needs the DC removed before $R_F$. Options A–D (Sections 8.2–8.5) do that, and the 50-Ω termination of Section 2.1 avoids the problem, because its bias tee carries the DC. Option A returns in the balanced pair as the resistive servo of Section 8.8 (d)."),
    # ---- Sections 8.2-8.5 ----
    ("replace", "**Noise.** With $R_s = V_S/I_{\\mathrm{DC}}$, $R_s$ adds three current-noise terms",
     "**Noise.** With $R_s = V_S/I_{\\mathrm{DC}}$ (Table A8.1), $R_s$ adds three current-noise terms"),
    ("replace", "This option is an analytical sketch; the two-stage loop was not modelled.",
     "This option is an analytical sketch; the two-stage loop was not modelled.\n\n**How the four options compare.** For a single-ended detector Option A is recommended: it keeps the photodiode bias fixed and adds only 0.05–0.1 pF and 1.0 % of the shot-noise power at $V_S$ = 5 V (Eq. (69)). Option B needs no servo and is the simplest where $I_{\\mathrm{DC}}$ is roughly constant, but the photodiode bias falls by $I_{\\mathrm{DC}}R_b$ and the node gains 0.1–0.2 pF. Option C still needs a sink and adds the choke's 0.1–0.5 pF and a self-resonance near the band. Option D needs no sink, but its excess over shot noise at 0.1 mA is 5.7 dB, against 1.9 dB for a single 2-kΩ stage (Table A8.3)."),
    # ---- Sections 8.6-8.8 ----
    ("replace", "at 2 pF it breaks even at 200 MHz.", "at 2 pF it breaks even at 200 MHz (Table A8.4)."),
    ("replace", "which is Hobbs' Eq. (14) [A11, p. 44]", "which is the splitting factor of Hobbs' Eq. (8) [A11, p. 44]"),
    ("replace", "because $r_e$ = 257 Ω makes the $e_{cb}\\omega C_e$ term large.",
     "because $r_e$ = 257 Ω makes large the second term of Eq. (76), the voltage noise $e_{cb} = \\sqrt{4k_BT(r_b + r_e/2)}$ acting on $C_e$."),
    ("replace", "The reason is that OPA855's $e_n$ of 0.98 nV/√Hz is itself the Johnson noise of only 59.5 Ω.",
     "The reason is that OPA855's $e_n$ of 0.99 nV/√Hz (the white level of Fig 6-11, Table 3.1) is itself the Johnson noise of only 59.5 Ω."),
    ("paragraph", "**Is an active servo possible?** Yes. It can act in four places:",
     "**Is an active servo possible?** Yes. The imbalance can be corrected on the light (b), on a photocurrent (c) or at the summing node (d), and a fourth servo holds the photodiode bias (e). Each has its own noise mechanism, and a low-noise servo is hard for the reasons in (a). Only (b) and (c) null the RIN with the DC; (b) is preferred where the optics allow because it adds nothing at the node, (d) is the electronic default, and (c) is kept for a large imbalance with a noisy laser (Table A8.10)."),
    ("replace", "his canceller as Eq. (13) [A22, p. 908]", "his canceller as Eq. (7) [A22, p. 908]"),
    ("replace", "affordable at up to about 1 mA per diode.", "affordable at up to about 1 mA per diode (Table A8.7)."),
    ("replace", "For $f_{\\mathrm{HP}}$ = 1 kHz with $R_F$ = 2 kΩ and $R_s$ = 24 kΩ",
     "A few per cent of optical imbalance at 10 mA per diode is 0.2–0.5 mA (Section 1.2); covering ±0.5 mA from a ±12-V integrator takes $R_s$ = 12 V/0.5 mA = 24 kΩ, whose Johnson noise is 0.83 pA/√Hz (Table A8.8). For $f_{\\mathrm{HP}}$ = 1 kHz with $R_F$ = 2 kΩ and $R_s$ = 24 kΩ"),
    # ---- Section 8.9 ----
    ("paragraph", "This is the design that follows from Sections 1.2 and 8.6–8.8", OPEN_89),
    ("replace", "and the larger dynamic range for tones at 150–200 MHz.",
     "and a dynamic range at least equal to variant B's for tones from 150 MHz up."),
    ("replace", "by up to 11 dB. The price is a 21–35° loop whose residual peaking is equalized (Section 6.2.8).",
     "by up to 11 dB. Two descriptions of its loop disagree. The vendor's macromodel, which reproduces OPA818's measured response at a gain of 7 where the datasheet curve fails once the input capacitance is included (Section 5.4), gives 43–50° nominal and 39–45° at the worst capacitance corner, with no peaking and no equalizer. The datasheet curve gives 27–35° nominal and 21–30° at the worst of the 27 corners of Table A8.11, with peaking to be equalized (Section 6.2.8). The first board decides (Appendix C, item 16)."),
    ("span", "*Note on variant A's flagged corners.*", "1 corner of 27 at 2 kΩ.", NOTE_89),
    ("replace", "and at 10 mA per diode to 0.02 and 0.08 dB, because shot noise dominates.",
     "and at 10 mA per diode to 0.02 and 0.08 dB, because shot noise dominates. In the macromodel variant B's dark noise at 100 MHz is 1.6 dB above the central estimate, an upper bound (Section 5.6)."),
    ("replace", "Its larger amplitude outweighs its higher noise even in the dark.",
     "On the central noise estimate its larger amplitude outweighs its higher noise even in the dark. With the macromodel's noise, at the best SPICE designs, it does so only from $I_1 + I_2$ = 30 µA up, and OPA855 leads in the dark, 80.8 against 79.5 dB, since OPA818's dark dynamic range there is 1.5 dB lower (Section 6.6.2, Table A6.33)."),
    ("replace",
     "Variant A keeps a worst case of 45–59° and needs no equalizer. Variant B keeps 21–30° and needs its peaking equalized per board. Its 1.5-kΩ designs, at 21–26° worst case, sit at the edge of the Section 6.2.8 rule.",
     "Variant A keeps a worst case of 45–59° and needs no equalizer, and the macromodel confirms its phase margins, bandwidths and noise within a few degrees and per cent (Section 5.5). On the datasheet curve variant B keeps 21–30° and needs its peaking equalized per board; its 1.5-kΩ designs, at 21–26° worst case, sit at the edge of the Section 6.2.8 rule. In the macromodel it needs no equalizer but is slower: 226 MHz at 1 pF and 2 kΩ, and 333 MHz at 1.5 kΩ. At 1 pF and 2 kΩ its $C_F$ of Table A8.11 is the macromodel's 45°, ±0.1-pF design; accepting 40°, or trimming $C_F$ to ±0.05 pF, gives 259–309 MHz at 0.42–0.50 pF there (Table A5.10), and the loop caps the bandwidth near 375 MHz, which only an equalized design with about 10 dB of peaking approaches."),
    ("replace", "and its datasheet distortion near 100 MHz is 10–20 dB lower.",
     "and its datasheet distortion near 100 MHz is 10–20 dB lower. The macromodels confirm variant B's large-signal advantage below 100 MHz (Table A5.12)."),
    ("delete", "**What the vendors' SPICE macromodels add (Chapter 5).**", "  - Its large-signal advantage below 100 MHz is confirmed (Table A5.12)."),
    # ---- Section 8.10 ----
    ("replace", "The resistor:\n",
     "This section turns the designs into parts. Table A8.13 gives starting values for the two variants of Section 8.9 and for the alternatives that Section 9.2 names: OPA856 and LMH6629 for a straightforward board, and OPA955 once it is released. Three properties of the feedback resistor matter.\n"),
    ("span", "- **At 2 kΩ.** The 0.15–0.36 pF window accommodates", "(Tables A5.8 and A5.9).", WINDOW_810),
    ("replace", "\n- **At 1.5 kΩ.** The window (0.17–0.36 pF) is narrower than ±0.1 pF around any centre, so the parasitic must be held within about ±0.08 pF, or trimmed.", ""),
    ("replace", "- **Noise bandwidth.** Both designs have 420–540 MHz of bandwidth.",
     "- **Noise bandwidth.** Both designs have 420–540 MHz of bandwidth on the datasheet curve, and 481–630 MHz at the macromodel's targets (Table A5.9)."),
    ("replace", " Keep $C_F$ ≤ 0.36 pF, i.e. $NG_\\infty$ ≥ 7.", ""),
    ("replace",
     "- **With 2 pF at the node** (1 pF in each diode) the window is 0.175–0.525 pF at 2 kΩ. A total of 0.35 pF gives 280 MHz at 68°, and ±0.1 pF moves it between 201 and 436 MHz (Section 8.9).",
     "- **With 2 pF at the node** (1 pF in each diode) the macromodel's window is 0.188–0.454 pF at 2 kΩ, and the total $C_F$ should be 0.320 ± 0.130 pF at 2 kΩ and 0.335 ± 0.115 pF at 1.5 kΩ, so ±0.1 pF fits without trimming (Tables A5.8 and A5.9). On the datasheet curve the window is 0.175–0.525 pF, and a total of 0.35 pF gives 280 MHz at 68°, moving between 201 and 436 MHz for ±0.1 pF (`data/results/balanced_detector.json`)."),
    ("replace", "Both tolerate the parasitic corners with ≥ 46° of phase margin.",
     "On the datasheet curves both tolerate the parasitic corners with ≥ 46° of phase margin; in SPICE OPA856 keeps 50–62°, while LMH6629 keeps 41–47°, the gap between its macromodel's gains from the two inputs (Sections 5.3 and 5.5)."),
    ("replace", "which is enough if any peaking is equalized afterwards.",
     "which is enough if any peaking is equalized afterwards. In the macromodel the same design keeps 45.4° at the worst capacitance corner, with no peaking (Table A5.6)."),
    ("replace",
     "*OPA955.* These rows are for planning only; all of its datasheet values are preliminary (the 1–2 MHz difference from Table A6.12 comes from rounding $C_F$ to 0.31 and 0.44 pF).",
     "*OPA955.* These rows are for planning only; all of its datasheet values are preliminary. They add the 2–3 pF that the datasheet curve needs for 45°; its macromodel needs none and is robust at 0.220 ± 0.050 pF with 560 MHz and 46° at the worst corner (Section 6.5, Table A6.32). The 1–2 MHz difference from Table A6.12 comes from rounding $C_F$ to 0.31 and 0.44 pF."),
    ("replace", "The parasitic columns keep the same external capacitor and move the total by ∓0.1 pF.*",
     "The parasitic columns keep the same external capacitor and move the total by ∓0.1 pF. For OPA855 the macromodel narrows the tolerance to 0.230 ± 0.070 pF at 2 kΩ and 0.240 ± 0.055 pF at 1.5 kΩ (Section 8.10).*"),
    # ---- Section 8.11 ----
    ("replace", "### 8.11 What not to do\n\n- **Bootstrapping",
     "### 8.11 What not to do\n\nEach item below follows from a result of this chapter, cited with it.\n\n- **Bootstrapping"),
    ("replace", "It adds the full shot noise of its current and 0.1–0.5 pF.",
     "It adds the full shot noise of its current and 0.1–0.5 pF (Section 8.2, Eq. (34))."),
    ("replace", "It can resonate inside the band (Table A8.9).", "It can resonate inside the band (Section 8.8 (e), Table A8.9)."),
    ("replace",
     "- **DC-coupling 10 mA through a lower $R_F$** without a second stage. It throws away gain that the instrument then has to supply. That is Option D without its second stage.",
     "- **Carrying 10 mA of DC through an $R_F$ small enough to hold it, without a second stage.** On a 5-V part that means $R_F$ ≤ 305 Ω (Section 8.5). At 286 Ω its Johnson noise alone, 7.6 pA/√Hz, exceeds the 5.66 pA/√Hz shot noise of 0.1 mA (Table A1.1), and the instrument's noise reaches the photocurrent through a transimpedance 2 kΩ/286 Ω = 7.0 times smaller (Eq. (8)). Option D restores the gain in a second stage."),
]
