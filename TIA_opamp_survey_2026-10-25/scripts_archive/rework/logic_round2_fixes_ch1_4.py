r"""Reviewed fixes of the logic round of 1 Nov 2026 for Chapters 1-4, read by edit_logic_round2.py.

Each entry is an operation of edit_logic_round2.apply().  The anchors are those of the note after the
new opening, the chapter openings and the rebuilt conclusions have been put in, and they are applied
in this order.  The 2-pF option moves from Section 1.2 to a new Section 6.3.5; the numerical method
of Section 4.9 moves to the end of Section 4.5; the paragraph relating the bench board to Figure 12
moves from Section 4.10 to Section 6.2.7.
"""

OPTION_2PF = r"""#### 6.3.5 The 2-pF option: 1 pF in each diode

With 1 pF in each diode of the pair the node carries 2 pF (Section 1.2). Tables A1.3 and A1.4 give the leading amplifiers for that option, with the same nominal parasitics and design rules as Section 6.2; their last column repeats the 1-pF band penalty of Tables A6.15 and A6.17 for comparison. The option changes five things.
- **Noise.** The band penalty rises by about 0.5 dB for OPA855, OPA856, OPA955 and LMH6629, whose $e_n$ is below 1 nV/√Hz, and by 0.8–2.2 dB for the others. The added picofarad raises the $e_n$ term of Eq. (23) by $e_n^2(2\pi f)^2\left[(C_{\mathrm{tot}} + 1\ \mathrm{pF})^2 - C_{\mathrm{tot}}^2\right]$, which grows with both $e_n$ and $C_{\mathrm{tot}}$: OPA846 (1.2 nV/√Hz on 5.9 pF) goes from 6.0 to 6.8 dB, OPA818 from 6.3 to 7.8 dB and OPA859 from 6.4 to 8.6 dB at 2 kΩ.
- **Bandwidth.** Robust bandwidths fall by 2–17 %: OPA855 from 539 to 521 MHz, LMH6629 from 276 to 257 MHz, OPA856 from 231 to 198 MHz, OPA859 from 211 to 175 MHz at 2 kΩ.
- **Stability of the decompensated parts improves slightly.** The flat designs of OPA846 and OPA818 move from 34° and 32° to 37° and 35°, and 45° needs 6 pF of added capacitance instead of 8 pF at 2 kΩ. OPA955 needs 2 pF added instead of 3 pF, which gives the same 466 MHz.
- **OPA855's $C_F$ window widens.** At 2 kΩ it becomes 0.175–0.525 pF (0.204–0.525 pF at 1.5 kΩ), against 0.15–0.36 pF at 1 pF, because its upper limit $C_T/(G_{\min}-1)$ grows with $C_T$. Inside the window $C_F$ alone sets the bandwidth from 576 MHz at 0.175 pF to 176 MHz at 0.50 pF, so a 200–300 MHz design no longer needs a post-filter to define its bandwidth (Section 8.10).
- **With photocurrent the difference shrinks.** At $I_1 + I_2$ = 1 mA, OPA855's total noise rises by only 0.03 dB at 100 MHz and 0.11 dB at 200 MHz."""

SELECTION = r"""**Selection rule.** A voltage-feedback amplifier qualified by one of three routes, each aimed at a term of the bench-unit equations of Section 3.1.
- A low-noise part qualified with a GBW of at least about 800 MHz (at least 1 GHz if decompensated) and $e_n$ ≤ 3 nV/√Hz (bipolar) or ≤ 6 nV/√Hz (FET). By Eq. (9), 800 MHz gives $12.62\sqrt{800/(2\times2.35)}$ = 165 MHz at 2 kΩ on the 2.35 pF of the OPA855 design of Section 3.2, so a slower part misses 150 MHz even with an input capacitance as small as OPA855's.
- A part with unusually low input capacitance qualified at a lower GBW, because a low capacitance lowers $C_{\mathrm{tot}}$ both in the bandwidth of Eq. (9) and in the $e_n$ term of Eq. (7).
- A part with ±5 V of output swing qualified with a GBW of at least 500 MHz, because the dynamic range grows with the output amplitude (Eq. (10)).

**Result.** 25 parts were analysed in full, with LMH6629 in two compensation settings, so 26 configurations; Table A2.3 groups them. Five of the analysed parts fall below the GBW floor of the first route: THS4271, AD8045 and ADA4817-1, with 400–410 MHz; ADA4899-1, one of the six starting parts, whose GBW is not specified (about 300–370 MHz derived); and OPA843, whose 800 MHz misses the 1-GHz floor for decompensated parts ($G_{\min}$ = 3). They were analysed all the same. The first four miss 150 MHz, as the floor predicts, and OPA843 reaches it only marginally (Section 6.2.1)."""

VALUE_TYPES = r"""**Datasheet value types.** Each datasheet value carries a label. TYP marks a typical value, which is not guaranteed. MIN and MAX mark limits guaranteed at 25 °C unless stated, by test or, where the datasheet says so, by design. CURVE marks a value read from a typical-characteristics plot, given with its reading uncertainty, and SCOPE and PHOTO mark values read from an oscilloscope trace or a raster photograph. SIM marks a value that the manufacturer labels as simulated, TEXT a value stated in prose, and DERIVED a value computed here from datasheet data. n.s. marks a value the datasheet does not specify.

Datasheet citations such as "p9" or "Fig 6-11" refer to the PDF pages and figures of the revisions listed in Appendix D, which gives each document's literature number and source; the documents themselves are available from their manufacturers."""

ASSUMPTIONS_23 = r"""Eq. (23) assumes that the amplifier's noise is represented by $e_n$ and $i_n$ at its inputs, as the datasheets give it, that $e_n$ acts on the whole of $C_{\mathrm{tot}}$, including the amplifier's own input capacitance, and that $e_n$ and $i_n$ are uncorrelated. Section 4.7 shows where the last two fail for FET inputs, and Section 5.3 finds that OPA846's macromodel drives only 2.28 pF of its 3.07 pF with its $e_n$."""

R_SER = r"""A fifth source is the Johnson noise of the photodiodes' series resistance $R_{\mathrm{ser}}$. In each diode it drives a current of density $4k_BTR_{\mathrm{ser}}(2\pi fC)^2$ into the node, with $C$ that diode's capacitance, so for equal resistances the pair contributes $4k_BTR_{\mathrm{ser}}(2\pi f)^2(C_{D,A}^2 + C_{D,B}^2)$. It is left out of the tables because $R_{\mathrm{ser}}$ is not specified (Appendix C, item 6). With 20 Ω in front of the whole 1 pF it reaches, at 200 MHz, $1.647\times10^{-20}\ \mathrm{J}\times20\ \Omega\times(2\pi\times2\times10^{8}\ \mathrm{Hz}\times10^{-12}\ \mathrm{F})^2 = 5.20\times10^{-25}\ \mathrm{A^2/Hz}$, i.e. 0.72 pA/√Hz, which adds 0.27 dB to the 2-kΩ floor there. For the baseline pair, two 0.5-pF diodes with 20 Ω each, $C_{D,A}^2 + C_{D,B}^2 = C_D^2/2$, so the density is $0.72/\sqrt2$ = 0.51 pA/√Hz, which adds $10\log_{10}(1 + 0.51^2/2.87^2)$ = 0.14 dB."""

TABLE_A45 = r"""**What Table A4.5 shows.** The model reproduces the datasheets' closed-loop data well enough to rank the amplifiers, within the limits below.
- Where the datasheet shows a real or simulated TIA response, the model reproduces the bandwidth to within 5 %.
- The resistive comparisons use $A/(1 + A/G)$ and so leave out the amplifier's input capacitance, which the TIA model includes in $C_T$. Without it, the model reproduces the phase margin at each decompensated part's minimum gain to within a few degrees, except OPA846, whose peaking it puts about 1 dB low. With it, the capacitance and the low gain-setting resistors form a pole at 1–3 GHz that costs 12–19° at these crossovers, and the OPA818 and OPA846 curves predict more peaking than their datasheets show (4.3 against 1.4 dB, and 5.6 against 3.1 dB; Section 5.4). The TIA phase margins of these two parts in this note are therefore, if anything, pessimistic, as the vendors' macromodels confirm (Sections 5.4 and 5.9).
- The 4–7 GHz region of the OPA855 and OPA955 curves, the OPA858 curve as plotted, and the LMH6629 curve are not trustworthy in detail. The text points out each place where that matters.
- The vendors' front-page "TIA bandwidth" curves are calculations, 10–15 % optimistic at 2 kΩ because they leave out $C_F$ and the board capacitance (Section 4.3). The formula quoted there reproduces them within 1 % (last row of Table A4.5), so they are no test of the model, and they say nothing about phase margin."""

ITEM2_4_10 = r"""2. **The noise at 10 MHz, where the capacitive term is small.** Eq. (24) gives 4.86 pA/√Hz for 13.6 pF and 4.77 pA/√Hz for 5.35 pF. An instrument floor is white at the TIA's output, so referred to the photocurrent it grows as $|Z_T|$ falls from 1.45 kΩ at 50 MHz to about $R_F$ = 1.2 kΩ at 10 MHz. The missing $\sqrt{7^2 - 5.16^2}$ = 4.73 pA/√Hz then becomes $4.73\times1.45/1.2$ = 5.72 pA/√Hz, and the total $\sqrt{4.77^2 + 5.72^2}$ = 7.44 pA/√Hz; a floor white at the input would give $\sqrt{4.77^2 + 4.73^2}$ = 6.72 pA/√Hz. A resistance at the non-inverting input cannot be told apart from a larger node capacitance this way, because its noise scales with $f\,C_{\mathrm{tot}}$ like the capacitive term; the peak frequency of item 1, or a look at the network on that input, settles it."""

FIXES = [
    # ---- Chapter 1 ----
    ("replace",
     "**Question.** Which commercially available operational amplifier gives the most sensitive inverting photodiode transimpedance amplifier (TIA) with the widest dynamic range under these conditions?",
     "**Question.** Which commercially available operational amplifier gives the most sensitive inverting photodiode transimpedance amplifier (TIA) with the widest dynamic range under these conditions, and how does such a TIA compare with the other front ends that could serve the receiver?"),
    ("replace",
     "The DC photocurrent belongs to the pair, not to one photodiode: a single-ended detector cannot carry 10 mA through 1.5–2 kΩ with any candidate (Section 6.4.1). In the pair the DC currents cancel at the summing node and only their imbalance reaches $R_F$ (Section 1.2).",
     "The DC photocurrent is that of the pair: the two DC currents cancel at the summing node, so only their imbalance reaches $R_F$, while the shot noise is that of their sum (Section 1.2)."),
    ("replace", "The planned 0.1–10 mA is therefore 4 to 390 times above the crossover:",
     "For 2 kΩ the planned 0.1–10 mA is therefore 4 to 390 times above the crossover (Table A1.1):"),
    ("replace", "over most of the planned operating range, so we report both views.",
     "over most of the planned operating range, so we report both the band penalty against the Johnson floor and the shot-noise clearance at the planned currents (Section 1.5)."),
    ("replace",
     "A single-ended detector cannot be built around any candidate at these currents. At 2 kΩ, 10 mA would need 20 V across $R_F$, and the largest DC current that any candidate can carry through $R_F$ is 1.5–1.7 mA for the 5-V parts, 4.3 mA for OPA846 and 5.5 mA for OPA818 (Table A6.25).",
     "A single-ended detector would put all of it through $R_F$: at 2 kΩ, 10 mA would need 20 V, none of the ten amplifiers carried forward can carry more than 5.5 mA (OPA818), and the ±12-V AD8021 and ±15-V THS4021, which have the swing, are not stable at this operating point (Section 6.4.1, Table A6.25)."),
    ("span", "**What an uncorrected imbalance costs.** The imbalance shifts the output by",
     "The imbalance is therefore servoed to zero (Section 8.8).",
     r"**What an uncorrected imbalance costs.** The reference voltage $V_{\mathrm{REF}}$ on the non-inverting input (Figure 1) is set to centre the output at zero imbalance, with a swing $V_{\mathrm{sw}}$ available on either side (Eq. (30)). An imbalance shifts the output by $\Delta I\,R_F$ and leaves only $V_{\mathrm{sw}} - |\Delta I|R_F$ for the RF signal, so an imbalance of either sign costs headroom from the first microampere: the dynamic range falls by $20\log_{10}\left[V_{\mathrm{sw}}/(V_{\mathrm{sw}} - |\Delta I|R_F)\right]$. A few per cent of optical imbalance at 10 mA per diode is 0.2–0.5 mA, which costs OPA855 at 2 kΩ 2.6–9.3 dB of dynamic range (Table A1.2), so the imbalance is servoed to zero (Section 8.8)."),
    ("replace",
     "Tables A1.3 and A1.4 give the leading amplifiers for that option, with the same nominal parasitics and design rules as Section 6.2. The last column repeats the 1-pF band penalty of Tables A6.15 and A6.17 for comparison.",
     "Section 6.3.5 states what that option changes, once Sections 6.2–6.3 have introduced the parts and their designs, and Tables A1.3 and A1.4 give the leading amplifiers for it."),
    ("delete", "**What the 2-pF option changes.**", "and 0.11 dB at 200 MHz."),
    ("replace", "\n### 6.4 Dynamic range\n", "\n" + OPTION_2PF + "\n\n### 6.4 Dynamic range\n"),
    ("replace", "With 2 pF at the node, OPA855's $C_F$ alone can set 200–300 MHz (Section 1.2).",
     "With 2 pF at the node, OPA855's $C_F$ alone can set 200–300 MHz (Section 6.3.5)."),
    # Table 1.1
    ("replace", "1 pF in each diode (Section 1.2) | specification of the task |",
     "1 pF in each diode (Section 1.2) | design specification |"),
    ("replace", "| 0.35 pF nominal, 0.2–0.5 pF corners | task range 0.2–0.5 pF |",
     "| 0.35 pF nominal, 0.2–0.5 pF corners | specified range 0.2–0.5 pF |"),
    ("replace", "| 0.20 pF nominal, 0.1–0.3 pF corners | task range 0.1–0.3 pF;",
     "| 0.20 pF nominal, 0.1–0.3 pF corners | specified range 0.1–0.3 pF;"),
    ("replace", "| 1.5 kΩ and 2 kΩ | specification of the task |", "| 1.5 kΩ and 2 kΩ | design specification |"),
    ("replace",
     "| Supply | per amplifier: 5 V single for the 5-V parts; ±5 V to ±6.5 V for the others (Table A6.3) | | datasheet recommended range |",
     "| – | supply voltage per amplifier | 5 V single for the 5-V parts; ±5 V to ±6.5 V for the others (Table A6.3) | datasheet recommended range |"),
    # Section 1.5
    ("replace",
     "noise figures appear only as translations for choosing an instrument (Eqs. (8) and (26)).",
     "noise figures appear only as translations for choosing an instrument (Eqs. (8) and (26)), and in the 50-Ω benchmark of Section 2.1, whose amplifier is specified by its noise figure and its input compression level."),
    ("replace", "\"Penalty\" is the ratio of the total input-referred noise to the Johnson noise",
     "\"Penalty\" is the ratio of the total input-referred noise without photocurrent to the Johnson noise"),
    ("replace",
     "Up to 8 pF of capacitance may be added deliberately at the inverting node if that is the only way to reach 45°.",
     r"Up to 8 pF of capacitance may be added deliberately at the inverting node if that is the only way to reach 45°. The robust design is read on the logarithmic grid of $C_F$ of Section 4.5, whose first point above the 0.2-pF floor is 0.206 pF, so it can come out slightly narrower than a flat design on the floor: OPA855 gives 539 MHz robust at 0.21 pF and 557 MHz flat at 0.20 pF with 58° (Table A6.5)."),
    ("replace",
     "the range of total $C_F$ that keeps the phase margin ≥ 45°, the gain margin ≥ 3 dB and the peaking ≤ 1 dB.",
     "the range of total $C_F$ that keeps the phase margin ≥ 45°, the gain margin ≥ 3 dB and the peaking ≤ 1 dB, and, for a decompensated amplifier, keeps the high-frequency noise gain $1 + C_T/C_F$ at or above the minimum stable gain $G_{\\min}$ (Section 6.2.4)."),
    ("span", "**Datasheet value types.** Values are labelled:", "- DERIVED: computed here from datasheet data.", VALUE_TYPES),
    ("replace", "Every phase margin, bandwidth and noise figure in this note is an **analytical estimate**",
     "Every phase margin, bandwidth and noise value in this note is an **analytical estimate**"),

    # ---- Chapter 2 ----
    ("replace", "In the list of ways to remove a large DC current it is Option E (Section 8.1).",
     "Because its bias tee carries the DC photocurrent, it needs none of the circuits of Sections 8.2–8.5 that keep a large DC current out of a TIA's feedback resistor."),
    ("replace", "Three comparisons settle where that is.",
     r"Three comparisons settle where that is. For the TIA they use three quantities that Chapters 4 and 6 derive: its input-referred noise density without photocurrent, $S_{i,0}(f)$ (Eq. (23) with $I_{\mathrm{DC}} = 0$); its band noise with the shot noise included, $i_{n,B} = \sqrt{\int_0^B S_{i,0}\,df + 2qI_{\mathrm{DC}}B}$ (Eq. (49)); and its ceiling, the largest undistorted rms tone, $I_{\max} = V_{\mathrm{pk}}/(\sqrt2\,|Z_T|)$, with $V_{\mathrm{pk}}$ its largest output amplitude (Eq. (30)) and $|Z_T|$ its transimpedance at the tone (Eq. (13))."),
    ("replace", "for the chain and $i_{n,B}$ of Eq. (49) for the TIA", "for the chain and $i_{n,B}$ for the TIA"),
    ("replace",
     "Every design we carry forward meets that, by 6.2 dB (the high-voltage composite of Section 7.2) to 17.7 dB in the dark, and $A$ shrinks toward zero as the shot noise takes over.",
     "$A$ shrinks toward zero as the photocurrent grows and the shared shot noise takes over; Section 6.8 shows that every design we carry forward keeps a positive $A$ at every photocurrent."),
    ("replace",
     "In a balanced pair the light cannot drive a tone larger than $I_{\\mathrm{DC}}/\\sqrt2$ rms, the optical limit of Eq. (32) (Section 4.8).",
     "In a balanced pair the light cannot drive a tone larger than $I_{\\mathrm{DC}}/\\sqrt2$ rms, because the tone's peak cannot exceed the total photocurrent $I_1 + I_2$, whether the light is intensity-modulated or a heterodyne beat (Eq. (32), Section 4.8)."),
    ("replace",
     "*Usable dynamic range.* Up to $I_{\\mathrm{DC}} = \\sqrt2\\,I_{\\max}$ the light limits the tone in both front ends, and the TIA leads by $A$.",
     "*Usable dynamic range.* For a chain that compresses above $P_{\\mathrm{eq}}$, the light limits the tone in both front ends up to $I_{\\mathrm{DC}} = \\sqrt2\\,I_{\\max}$, and the TIA leads by $A$."),
    ("replace",
     "For a 2-kΩ TIA at 10 mA, with $A$ = 0.63 dB (OPA855, Section 6.8), that is 1.994 kΩ × 10 mA × $10^{-0.63/20}$ = 18.5 V, against the 1.5–2.2 V of the op amps (Section 6.4) and the 8.3 V of the high-voltage composite (Section 7.2).",
     "At 2 kΩ and 10 mA that limit is $R_FI_{\\mathrm{DC}}$ = 20 V; Section 6.8 evaluates Eq. (6) for each leading design and sets it against the design's output amplitude."),
    ("span", "**Verdict.** For a small signal every design we carry forward beats the benchmark",
     "and Chapter 7 asks what it takes to raise a TIA's ceiling.",
     "Section 3.3 applies these three comparisons to the first worked design, Section 6.8 to every leading design, and Section 9.4 collects the outcome; Chapter 7 asks what it takes to raise a TIA's ceiling."),
    ("replace", "**The parts named in the task.** OPA847, OPA846, OPA818, OPA855, OPA856 and ADA4899-1.",
     "**The starting list.** Six parts were on the list from the start of the study: OPA847, OPA846, OPA818, OPA855, OPA856 and ADA4899-1."),
    ("replace", "**The search.** It then extended across manufacturers:",
     "**The search.** From these six, the search extended across manufacturers:"),
    ("span", "**Selection rule.** A part qualified if it is a voltage-feedback amplifier", "Table A2.3 groups them.", SELECTION),
    ("replace", "Values are datasheet typicals (Table A6.1). The figure is a map, not a ranking",
     "Values are datasheet typicals (Tables A6.1 and A6.2). The figure is a map, not a ranking"),
    ("replace", "OPA699 about 140 MHz with 11 dB more noise than the 2-kΩ floor,",
     "OPA699 about 140 MHz with 11 dB more noise than the 2-kΩ floor at 100 MHz,"),
    ("replace", "Where the datasheet gives no reason, we derive it with Eq. (9) and Eq. (24).",
     "Where the datasheet gives no reason, we derive it with the bench-unit bandwidth and noise equations of Section 3.1, Eqs. (9) and (7)."),
    ("replace",
     "Table A2.4 covers the two integrated TIAs whose datasheets were read: OPA857 and LMH32401.\n\nThe market scan also found:",
     "In the balanced pair with its imbalance servoed to zero (Sections 1.2 and 8.8), a single-chip TIA carries no DC, so what decides is its linear input range against its noise; Section 6.7 compares both with the op-amp designs on the definition of Eq. (50). Two classes exist. The first is built for pulsed microampere-level signals in lidar and APD receivers, with high transimpedance, input clamps, and DC ranges of microamperes to about 3 mA. Table A2.4 covers the two whose datasheets were read, OPA857 and LMH32401, and the market scan also found:"),
    ("delete", "All of them are lidar or APD front ends:", "with the balanced pair's imbalance servoed to zero."),
    ("span", "**LMH32401** comes closest. It has a 2-kΩ setting, 462 MHz at 1 pF", "adds noise (p9, p21–p23).",
     "**LMH32401** comes closest. It has a 2-kΩ setting, 450 MHz at 1 pF (Table A2.4; 461 MHz read from its Fig 6-1, Table A6.34) and 8.7 pA/√Hz at 100 MHz, 6.4 dB above the 2-kΩ OPA855 design (LMH32401 p11–p12, Figs 6-1 and 6-11). Its DC limits matter for a single-ended detector, which would put the whole photocurrent on its input: it carries only 0.7 mA without its ambient-light cancellation, and the cancellation is limited to 2 mA (minimum) to 3 mA (typical), works only with the photodiode sinking current, and adds noise (p9, p21–p23)."),
    ("paragraph", "The lidar TIAs (MAX40658–MAX40662, LTC6560/6561, LMH32404, LMH34400, HMC799) are built for pulsed",
     "The other lidar TIAs (MAX40658–MAX40662, LTC6560/6561, LMH32404, LMH34400, HMC799) specify no operation with milliamperes of DC. The second class, the TIAs of coherent optical receivers, is made for this topology: a balanced pair with one photodiode on each of two inputs, whose DC each input removes with its own loop. Their gain control holds the output at a few hundred millivolts, which limits their linear input at the gains where their noise is published. Section 6.7 treats both classes, together with three optical-communication TIAs that are not linear amplifiers in this sense, and finds every single-chip TIA with public figures at least 8.8 dB behind the op-amp designs at 1 mA; the best lidar TIA, LMH32401, is 10.4–13.5 dB behind."),
    ("paragraph", "The DC photocurrent shapes every option.",
     "The DC photocurrent constrains every option. In the balanced pair only the imbalance reaches $R_F$ (Section 1.2). Chapter 8 gives four ways of removing a large DC current, a resistive sink driven by a slow servo, AC coupling, an inductive bias tee and a two-stage split of the gain, which matter for a single-ended detector and for an imbalance too large to servo (Sections 8.2–8.5). It shows why bootstrapping and cascoding the photodiodes do not pay at 0.5–1 pF (Sections 8.6 and 8.7), gives the servos for the imbalance and for the photodiode bias (Section 8.8), and ends with the proposed balanced front end (Section 8.9)."),

    # ---- Chapter 3 ----
    ("replace",
     "for a full-scale tone of peak output voltage $V_{\\mathrm{pk}}$ (V) (Eq. (33)):",
     "for a full-scale tone of peak output voltage $V_{\\mathrm{pk}}$ (V), valid where the shot noise dominates the band noise and $|Z_T| = R_F$ at the tone, in practice from $I_{\\mathrm{DC}}$ = 1 mA up (Eq. (33)):"),
    ("replace", "Table 3.1 lists the inputs, each with its datasheet source.",
     "Table 3.1 lists the inputs, each with its datasheet source. Three results below come from the numerical model of Section 4.5, which evaluates Eq. (13) with the open-loop curve digitized from the datasheet: the transimpedance at 100 MHz (1.996 kΩ), the bandwidth and phase margin of the flat design (557 MHz, 58°) and the full dynamic range (67.6 dB, Table A6.29)."),
    ("replace", "| $C_F$ | 0.20 pF (resistor and pad parasitic; no discrete capacitor) | Section 6.2 |",
     "| $C_F$ | 0.20 pF: the flat design needs 0.19 pF, below the parasitic floor of Table 1.1, so no discrete capacitor is fitted | Table A6.5 |"),
    ("replace", "| $f$, $B$ | 100 MHz, 150 MHz | task |", "| $f$, $B$ | 100 MHz, 150 MHz | design specification |"),
    ("replace", "The model, using the measured-shape open-loop curve, gives 557 MHz at 58° phase margin.",
     "The numerical model gives 557 MHz at 58° of phase margin at the same $C_F$ (Table A6.5)."),
    ("replace", "(5.05 pF present), which is why those two need the full model.",
     "(5.05 pF present); both pass, and both still have too little phase margin (Section 3.1)."),
    ("replace",
     "The dark TIA's 4.17 pA/√Hz is $20\\log_{10}(22.85/4.17)$ = 14.8 dB below the chain's 22.85 pA/√Hz (Eq. (1)).",
     "The dark TIA's 4.17 pA/√Hz at 100 MHz is $20\\log_{10}(22.85/4.17)$ = 14.8 dB below the chain's 22.85 pA/√Hz (Eq. (1)); integrated over the band, the measure $A$ of Section 2.1, the lead is 15.0 dB with the vendor's macromodel (Section 6.8)."),
    ("paragraph", "**Dynamic range.** Eq. (10) gives the TIA 67.8 dB at 1 mA",
     r"**Dynamic range.** At 1 mA the design has the 67.6 dB found in Section 3.2. The chain that compresses at −10 dBm has 78.0 dB (Table A2.2), 10.4 dB more, but only for a tone of 2.83 mA rms, which the light cannot supply: at 1 mA the largest tone is 0.71 mA rms (Eq. (32)). On that tone the chain's dynamic range is 66.0 dB, 1.6 dB below the TIA's, although the light already exceeds the TIA's ceiling. From $I_{\mathrm{DC}} = \sqrt2\times0.540$ mA = 0.76 mA up, the TIA's largest tone stays at 0.54 mA rms while the chain's grows with the light, and from about 1.2 mA up the chain's larger tone outweighs the TIA's lower noise (Section 6.8)."),
    ("replace",
     "Its 1.525-V output amplitude, not its noise, sets the dynamic range from about 0.15 mA up (Section 6.6.3).",
     "Its 1.525-V output amplitude, not its noise, sets the dynamic range from a few tens of microamperes up (31–63 µA for the 5-V parts, Eq. (51) of Section 6.6.3)."),
    ("replace", "Its stability rests on a feedback capacitance of 0.15–0.36 pF that the parasitics",
     "Its stability rests on a feedback capacitance of 0.15–0.36 pF (the $C_F$ window of Section 6.2.4; the vendor's macromodel narrows it to 0.157–0.300 pF, Section 5.5) that the parasitics"),

    # ---- Chapter 4 ----
    ("replace", "All capacitance between the inverting node and AC ground adds. The non-inverting input",
     "The stability, the bandwidth and the noise derived below all depend on the capacitance from the inverting node to AC ground, which sets the noise gain and multiplies $e_n$ in the noise. All capacitance between the inverting node and AC ground adds. The non-inverting input"),
    ("replace", "Here $C_{\\mathrm{CM}}$ is the datasheet common-mode capacitance of one input to ground",
     "Here $C_D = C_{D,A} + C_{D,B}$ is the capacitance of both photodiodes, $C_{\\mathrm{PCB}}$ the pad and trace capacitance at the inverting node, $C_{\\mathrm{CM}}$ the datasheet common-mode capacitance of one input to ground"),
    ("replace", "The feedback network is $R_F$ in parallel with the total feedback capacitance $C_F$:",
     "Three functions describe the TIA: its transimpedance, which turns the photocurrent into a voltage; its noise gain, which acts on the amplifier's voltage noise; and its loop gain, which decides whether it is stable. The feedback network is $R_F$ in parallel with the total feedback capacitance $C_F$:"),
    ("replace", "and the phase margin is $\\phi_M = 180^\\circ + \\angle T(j2\\pi f_c)$.",
     "and the phase margin is $\\phi_M = 180^\\circ + \\angle T(j2\\pi f_c)$. Two consequences matter for the design. In band, where $|T| \\gg 1$, $Z_T \\approx -Z_F$, so $R_F$ and $C_F$ alone set the gain. Near crossover $T/(1+T)$ peaks when the margin is small, while $Z_F$ is already rolling off, so a flat $|Z_T|$ does not prove an adequate margin (Section 5.2, Figure 11)."),
    ("replace", "Above its dominant pole a compensated amplifier behaves as $A(s)=\\omega_A/s$",
     "For a single-pole amplifier the loop has a closed form, which gives the $C_F$ of a flat response and the bandwidth it reaches. Above its dominant pole a compensated amplifier behaves as $A(s)=\\omega_A/s$"),
    ("replace", "The bandwidth expression is TI's Eq. (18) in SBOA122 [A1]", "The bandwidth expression is TI's Eq. (12) in SBOA122 [A1]"),
    ("replace", "The numerical model used in Sections 6.2–6.4 reproduces 206.1 MHz",
     "The numerical model of Section 4.5, used in Sections 6.2–6.4, reproduces 206.1 MHz"),
    ("replace", "For the single-pole amplifier the model gives Table A4.1.",
     "For the single-pole amplifier the model gives Table A4.1: 1 dB of peaking yields 1.28 times the Butterworth bandwidth with 0.69 of its $C_F$ and 54.3° of phase margin, and 3 dB yields 1.46 times at 41.8°."),
    ("replace",
     "*What it means for decompensated parts.* At its minimum stable gain, a decompensated amplifier has $\\phi_A$ ≈ 50–55°. Subtracting a 15–25° noise-gain lead leaves 30–35°.",
     "*What it means for decompensated parts.* At its minimum stable gain a decompensated amplifier typically has $\\phi_A$ ≈ 50–55°; OPA855, with 62° stated and about 74° on its curve (Table A4.2), is the exception. The noise-gain lead then leaves little: in the OPA818 and OPA846 designs of Table A6.11, $\\phi_A$ = 48.2–55.3° and $\\angle NG$ = 14.1–23.5° leave $\\phi_M$ = 31.6–34.5°."),
    ("replace", "There are only two remedies:", "There are only two ways to raise the phase margin:"),
    ("replace", "where $\\phi_A$ is larger. That needs more $C_T$, hence more noise;",
     "where $\\phi_A$ is larger. That needs more $C_T$, hence more noise, because lowering $C_F$ instead raises the noise-gain lead at least as much as $\\phi_A$ (Table A6.11, Section 6.2.6);"),
    ("replace", "as OPA855 is here: its $\\phi_A$ is 80–83° at the 2-kΩ crossover.",
     "as OPA855 is here: its $\\phi_A$ is 80–83° at the 2-kΩ crossover.\n\nThe alternative, accepting the low margin and equalizing the peaking, is examined in Section 6.2.8."),
    ("paragraph", "The single-pole forms ignore the higher poles that make a decompensated amplifier decompensated.",
     "The single-pole forms ignore the higher poles that make a decompensated amplifier decompensated, and near its minimum stable gain those poles set the phase margin (Section 4.4). Every analytical phase margin in this note therefore rests on the amplifier's own open-loop data; this section says where those data come from and how far they can be trusted."),
    ("replace", "It is reported alongside as the pessimistic case (Section 6.2.3).",
     "It is reported alongside the plotted curve (Section 6.2.3). For all three parts the vendors' macromodels side with the stated values rather than with the plotted curves (Section 5.4)."),
    ("move", "For every candidate and both feedback resistors, Eqs. (13)–(14) were evaluated", "then refined by bisection.",
     "**Limits that apply to every number derived this way.**", "before"),
    ("replace", "For every candidate and both feedback resistors, Eqs. (13)–(14) were evaluated with the open-loop model of Section 4.5 on",
     "**How the loop is evaluated.** For every candidate and both feedback resistors, Eqs. (13)–(14) were evaluated with this open-loop model on"),
    ("replace", "$C_F$ was scanned from 0.02 to 3 pF on a logarithmic grid of 160 values, then refined by bisection.",
     "$C_F$ was scanned from 0.02 to 3 pF on a logarithmic grid of 160 values. The flat and 1-dB designs were then refined by bisection; the robust design was read on the grid, whose first point above the 0.2-pF floor is 0.206 pF."),
    ("replace", "- The model omits package and board parasitics beyond $C_{\\mathrm{PCB}}$ and $C_{F,\\mathrm{par}}$.",
     "- The model omits package and board parasitics beyond $C_{\\mathrm{PCB}}$ and $C_{F,\\mathrm{par}}$.\n- Above the highest plotted frequency, about 1 GHz for most parts, the loop gain is the curve's last segment continued, so a gain margin or second crossing found there is only indicative; the upper limit of $C_F$ is therefore the manufacturers' minimum-gain rule (Section 6.2.4).\n- The curves give the gain from the non-inverting input, while the TIA drives the inverting one. Above 1 GHz the two differ, which with the loaded output impedance makes this method's gain margins 4–7 dB optimistic (Sections 5.3 and 5.9)."),
    ("replace", "Phase margins below about 50° in this note should still be read as \"needs SPICE or a measurement\".",
     "Phase margins below about 50° should be read with the SPICE results of Chapter 5 where they cover the design, and as needing a measurement otherwise."),
    ("replace", "Four independent sources are present in Figure 1:",
     "The smallest RF photocurrent the TIA can resolve is set by its noise; referring every source to the photocurrent puts the TIA, the shot noise and the 50-Ω benchmark in the same units. Four independent sources are present in Figure 1:"),
    ("replace", "Three features of Eq. (23) organise the whole comparison:",
     ASSUMPTIONS_23 + "\n\nThree features of Eq. (23) organise the whole comparison:"),
    ("replace", "At 100 MHz this, not $e_n$, is the largest amplifier contribution in OPA855 and OPA856 (Table A6.16).",
     "Section 6.3.1 shows that at 100 MHz this, not $e_n$, is the largest amplifier contribution in OPA855 and OPA856."),
    ("paragraph", "A fifth source is the Johnson noise of the photodiode's series resistance $R_s$.", R_SER),
    ("replace", "**Reference levels at 25 °C.** These follow from Eq. (24).",
     "**Reference levels at 25 °C.** Table A4.3 lists the levels that follow from Eq. (24): the Johnson noise of both feedback resistors and of 50 Ω, the shot noise of the four photocurrents, and the crossover current derived next."),
    ("replace", "This is the capacitive-noise term of TI's Eq. (19) in SBOA122 [A1]",
     "This is the capacitive-noise term of TI's Eq. (13) in SBOA122 [A1]"),
    ("replace",
     "*Example.* An instrument with a 10-dB noise figure behind a 2-kΩ TIA adds 1.44 pA/√Hz, half the 2.87 pA/√Hz Johnson noise of $R_F$.",
     "*Example.* For the 2-kΩ OPA855 design at 100 MHz, Section 3.2 finds that an instrument with a 10-dB noise figure adds 1.44 pA/√Hz, half the 2.87 pA/√Hz Johnson noise of $R_F$."),
    ("replace", "It is 16 times the long-channel induced gate noise (0.28 pA/√Hz).",
     "It is 16.6 times the long-channel induced gate noise (0.28 pA/√Hz)."),
    ("replace", "and continues its last slope beyond the plotted range.",
     "and continues its last slope beyond the plotted range. Here $i_{n,\\mathrm{curve}}(f)$ is the datasheet's current-noise curve, $i_{n,\\mathrm{white}}$ its flat level, and $C_{\\mathrm{in}} = C_{\\mathrm{CM}} + C_{\\mathrm{DIFF}}$ the amplifier's own input capacitance."),
    ("replace", "The low value differs from the central by less than 0.2 dB and is not tabulated.",
     "The low value differs from the central by less than 0.2 dB and is not tabulated. For the parts of Chapter 6 the high estimate lies 0.3–2.7 dB above the central one in band noise (Section 6.3), and OPA955, whose curve also rises, is treated the same way."),
    ("replace", "**DC-coupled photocurrent limit.** Let $V_{\\mathrm{OL}}$",
     "The dynamic range is the largest RF photocurrent the TIA passes undistorted divided by its band noise. This section states the two limits on that photocurrent, the DC through $R_F$ and the RF swing, and then defines the dynamic range in its electronic and usable forms.\n\n**DC-coupled photocurrent limit.** Let $V_{\\mathrm{OL}}$"),
    ("replace", "the output falls by $I_{\\mathrm{DC}}R_F$ from", "the output falls by $|\\Delta I|R_F$ from"),
    ("replace", "In a single-ended detector this limits the photocurrent; in the balanced pair it limits the imbalance that can be left uncorrected.",
     "Here $\\Delta I = I_1 - I_2$ is the DC through $R_F$: in the balanced pair the imbalance (Section 1.2), which this limits where it is left uncorrected, and in a single-ended detector the whole photocurrent."),
    ("replace", "It is stored with the results but not tabulated.", "It is stored in `data/results/results.json` but not tabulated."),
    ("replace",
     "The two figures differ only above $I_{\\mathrm{DC}} = \\sqrt2\\,I_{\\max}$, where the light could drive the TIA past its ceiling: for OPA855 on 5 V at 2 kΩ, with $I_{\\max}$ = 1.525 V/(√2 × 1.996 kΩ) = 0.540 mA rms, that is 0.76 mA.",
     "The two figures agree above $I_{\\mathrm{DC}} = \\sqrt2\\,I_{\\max}$, where the light could drive the TIA past its ceiling, and differ below it: for the OPA855 design of Section 3.3, whose ceiling is 0.540 mA rms, that is 0.76 mA."),
    ("replace", "In this regime a smaller $R_F$ costs no sensitivity, because the shot noise, not the resistor, sets the floor.",
     "In this regime a smaller $R_F$ costs no sensitivity, because the shot noise, not the resistor, sets the floor. It does cost loop stability with a decompensated amplifier, because a smaller $R_F$ lowers the noise gain at crossover (Section 6.2.2)."),
    ("replace", "**Noise added by a DC sink.** Removing $I_{\\mathrm{DC}}$",
     "**Noise added by a DC sink.** Eq. (33) presumes that the DC has been removed before $R_F$, and whatever removes it adds noise at the summing node. Removing $I_{\\mathrm{DC}}$"),
    ("replace", "Chapter 8 uses this.", "Sections 8.2–8.4 apply it to Options A–C."),
    ("replace", "### 4.9 How the model is evaluated, and what the datasheets say about it", "### 4.9 What the datasheets say about the model"),
    ("replace",
     "Before any of these numbers is used, the model must reproduce the closed-loop and TIA data printed in the datasheets. Table A4.5 collects every such comparison.",
     "Before the model's phase margins and bandwidths are used, it must reproduce the closed-loop and TIA data printed in the datasheets. Table A4.5 collects every such comparison. They test the loop and bandwidth part of the model, Sections 4.2–4.5; Section 4.10 tests the noise of Section 4.6 and the peaking together on one board."),
    ("span", "**Conclusions from Table A4.5.**", "for about 14 pF at the amplifier input.", TABLE_A45),
    ("span", "Not recorded with the result (Appendix C):", "- the noise floor of the measuring instrument.",
     "Four pieces of information that would pin the circuit down were not recorded with the result (Appendix C, item 11):\n- the photodiode capacitance at the operating bias;\n- how the photodiode is connected to the amplifier;\n- the frequency of the response peak;\n- the noise floor of the measuring instrument."),
    ("replace", "Part-to-part spread therefore cannot account for 7 pA/√Hz.",
     "Part-to-part spread therefore cannot account for 7 pA/√Hz. Eq. (35) takes the noise as measured without photocurrent."),
    ("replace", "\\qquad x = f/f_0 < 1,$$", "\\qquad x = f/f_n < 1,$$"),
    ("replace", "Combining this with $f_0^2 = \\mathrm{GBW}/(2\\pi R_F C_{\\mathrm{tot}})$ from Eq. (17)",
     "Combining this with $f_n^2 = \\mathrm{GBW}/(2\\pi R_F C_{\\mathrm{tot}})$, the natural frequency $\\omega_0/2\\pi$ of Eq. (17),"),
    ("replace",
     "**Reading.** The two independent results point to the same circuit: about 14 pF at the summing node and about 0.3 pF of feedback capacitance.",
     "**Reading.** The two independent results point to the same circuit. The noise puts the total node capacitance, $C_F$ included, near 13.6 pF (the numerical model, with the datasheet noise curves, reaches 7 pA/√Hz at $C_T$ = 13.1 pF; Section 5.8), and the peaking requires $C_T$ ≥ 14 pF. The smallest design of Table A4.7 that reproduces 1.45 kΩ, 14 pF with 0.295 pF, meets both, so the board has about 14 pF at the summing node and about 0.3 pF of feedback capacitance."),
    ("replace", "but a board in this state rings near 120 MHz and has little room before oscillating.",
     "but a board in this state rings near 120 MHz and has little room before oscillating. Section 6.2.8 gives the change that makes it robust: raising the total $C_F$ to 0.9–1.1 pF leaves 22–28° in the worst case and keeps 193–199 MHz."),
    ("paragraph", "2. **The noise at 10 MHz, where the capacitive term is small.**", ITEM2_4_10),
    ("move", "**Relation to Figure 12.** The OPA846 point in Figure 12", "whenever about 13–14 pF sits at its input.",
     "with OPA955 (with 3 pF added) next to it.*", "after"),
    ("replace", "**Relation to Figure 12.** The OPA846 point in Figure 12 is",
     "**The bench board of Section 4.10 and Figure 12.** The OPA846 point in Figure 12 is"),
    # the list of checks in the conclusions (kept from the old Section 9.13)
    ("replace",
     "Below about 50° the hand model and the macromodel can differ by 5–10°; TI's OPA858 reference design shows 55° against 45.9° [A7].",
     "Below about 50° the datasheet curves and the macromodels can differ by 11.3–16.7° (OPA846, OPA818, OPA858; Section 5.6), and a hand calculation by 9.1° (Section 4.5): TI's OPA858 reference design shows 55° against 45.9° [A7]."),
    ("replace", "   - its series resistance, which adds $4k_BTR_s(\\omega C_D)^2$ of noise;",
     "   - its series resistance $R_{\\mathrm{ser}}$, which adds $4k_BTR_{\\mathrm{ser}}\\omega^2(C_{D,A}^2 + C_{D,B}^2)$ of noise (Section 4.6);"),
]
