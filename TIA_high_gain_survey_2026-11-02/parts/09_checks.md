## 9. Checking the model against SPICE and against its own approximations

Chapters 2–8 rest on an analytic model: the exact relations of Section 2.1 evaluated with datasheet values, a single-pole amplifier, and, for the feedback resistor, the distributed line of Section 3.4. This chapter tests that model in two ways. The first replaces the single-pole amplifier and the datasheet noise with the manufacturers' own SPICE macromodels, in the same circuits and at the same feedback capacitances. The second compares the approximate formulas of Chapter 3, which the text uses to explain the results, with the full model they approximate. The checks found one effect that the original analytic model left out, the amplifier's finite DC open-loop gain, and that effect is now in the model and in Section 3.1.

### 9.1 How the checks were run

Two simulators were used.

- **ngspice-46**, loaded as the shared library that KiCad 10 installs and driven from Python (`scripts_archive/ngspice_shared.py`, from the companion note), ran the Texas Instruments PSpice models and the Analog Devices model of ADA4817-1. These are OPA928 (SBOMCC0, Rev. A), OPA140 (SBOM493, Rev. D), OPA828 (SBOMAJ0, Rev. D), OPA320 (SBOM437, Rev. G, file `OPAx320-Q1.LIB`), OPA1656 (SBOMAW6, Rev. C), OPA2156 (SBOMAR0, Rev. B), OPA818 (SBOMB74B), OPA657 (SBOM137, Rev. F) and ADA4817-1 (Rev. 2.1), and, for the designs at 10 kΩ of Section 9.8, OPA855 (SBOMB43D, Rev. D), OPA858 (SBOMBK7), LMH6629 (SNOM133) and OPA955 (SLOM544, a netlist that TI supplies only inside a TINA-TI file). The TI models' "noiseless" resistors, which ngspice would otherwise make noisy at about 27 K, were translated to noiseless ngspice resistors, as in the companion note (its Appendix B.1).
- **LTspice**, run headless on netlists written by `scripts_archive/hg_ltspice.py` (`LTspice.exe -b -ascii`, with its ASCII output parsed in Python), ran the Analog Devices models that ship with LTspice. These are ADA4530-1 (`ADI1.lib`), ADA4625-1 (`ADA4625-1.sub`, encrypted), LTC6268-10 (`LTC2.lib`) and the logarithmic amplifiers AD8304 (`AD8304.lib`) and ADL5303 (`ADL5303.sub`, encrypted). The encrypted models can only be run in LTspice.

Each TIA deck holds the macromodel, $R_F$ and the $C_F$ of the analytic design, the photodiode as $C_D$ and a (noisy) $R_{sh}$, 1 pF of board capacitance, and a 10-kΩ load, all at 25 °C. The decks on the companion's 1-pF node in Section 9.8 use the companion's board capacitance, supplies and loads instead. An AC analysis gives the transimpedance. A noise analysis referred to the photocurrent source gives the input-referred noise density directly in A/√Hz, the quantity of Eq. (8). From these the same metrics as in Chapter 6 follow: the −3 dB bandwidth, the peaking, and the excess noise $\Delta N$ of Eq. (16) over [1 Hz, $f_{-3\,\mathrm{dB}}$]. In all, 120 TIA designs, 21 designs at 10 kΩ, 36 noise-characterization decks, open-loop decks for OPA1656 and OPA2156, 12 distributed-resistor cases, 6 composite front ends and 18 logarithmic-amplifier operating points were run, which takes a few minutes. The scripts are `hg_spice.py`, `hg_spice_medium.py` and `hg_ltspice.py`, and the summaries are in `spice/results/`.

### 9.2 The TIA designs

The most direct check builds the designs of the sweep in SPICE, with each vendor's macromodel in place of the single-pole amplifier and the datasheet noise, and compares their bandwidth and excess noise with the analytic model. Twelve amplifiers were run at the five gains from 100 kΩ to 1 GΩ on the 20-pF and 380-pF silicon photodiodes. Figure 17 compares the bandwidth and the excess noise of all 120 designs with the analytic model, and Table 9.1 summarizes the deviations for each amplifier.

![Figure 17](figures/fig6_spice_parity.png)

*Figure 17. The TIA designs of the sweep in SPICE against the analytic model: −3 dB bandwidth (left) and excess noise $\Delta N$ of Eq. (16) (right). Circles: ngspice; squares: LTspice; open symbols: designs whose DC open-loop gain is less than ten times the mid-band noise gain (Section 3.1). The dashed lines are 1:1.*

*Table 9.1. SPICE against the analytic model for each amplifier: the median and the largest deviation of the bandwidth (SPICE over model, minus 1) and of $\Delta N$ (SPICE minus model) over that amplifier's designs, excluding the designs whose DC open-loop gain is less than ten times the mid-band noise gain (last column), which Table 9.2 treats. `hg_spice_tables.py`.*

<!-- table: table_9_1 -->

For the eight precision and low-noise CMOS parts, SPICE confirms the model's bandwidth in every design, within 7.1%, with medians of 0.1–1.2%. Their excess noise agrees within 0.67 dB, with medians of 0.02–0.33 dB, except for OPA2156 on the 380-pF photodiode at 100 MΩ and 1 GΩ. There SPICE gives 1.0 dB more, because OPA2156's macromodel has 6.5 nV/√Hz at 1 kHz against the data sheet's 4.0 nV/√Hz (Table 9.3). The conclusions of Sections 6.1–6.5 for these parts therefore stand as computed. For the wideband parts the agreement is looser but still sufficient for the ranking. OPA818's bandwidth is up to 19% higher in SPICE. Its excess noise is up to 1.7 dB higher, because its model's noise at megahertz frequencies exceeds the datasheet values the model uses. LTC6268-10's excess noise is up to 2.2 dB higher, at 1 GΩ on the large photodiode, because its macromodel has more flicker noise (37 nV/√Hz at 1 kHz) than the estimate of Appendix B.1 (28 nV/√Hz). Figure 18 shows four of the designs in full: the input-referred noise spectra and the normalized transimpedance, SPICE against model.

![Figure 18](figures/fig7_spice_spectra.png)

*Figure 18. Input-referred noise density (left axes) and normalized transimpedance (right axes) of four designs, SPICE (solid) against the analytic model (dashed): OPA140 at 1 GΩ on the 20-pF photodiode, ADA4625-1 at 1 MΩ on 380 pF (in LTspice), OPA818 at 10 MΩ on 20 pF and OPA657 at 100 MΩ on 380 pF. The fourth, OPA657, fails the open-loop-gain rule of Section 3.1: its transimpedance falls well before the resistor's own pole.*

**The finite open-loop gain.** The first run of these checks, made while the analytic model still used a DC open-loop gain of 120 dB for every amplifier, found that OPA657 and ADA4817-1 lost most of their bandwidth on the 380-pF photodiode at high gain. At 1 GΩ, for example, OPA657 reached 963 Hz in SPICE against the resistor's 1.59 kHz. The reason is the mid-band noise gain, $(C_T + C_F)/C_F$. Above the noise gain's zero, the loop gain is the open-loop gain divided by this noise gain. On 380 pF with $C_F$ = 0.1 pF the noise gain is about 3,900, while these two wideband amplifiers have DC open-loop gains of only 70 dB (OPA657, 3,160) and 65 dB (ADA4817-1, 1,780) (Table A.1). The loop gain is then below unity, the loop cannot hold the summing node at virtual ground, and the transimpedance falls early. The analytic model now uses each amplifier's datasheet open-loop gain (Table A.1), and Table 9.2 compares the affected designs. The model follows SPICE within 10–35%, pessimistic for OPA657 because its datasheet's 70 dB is lower than its macromodel's. The rule for design is Eq. (19a) of Section 3.1: the DC open-loop gain should exceed the mid-band noise gain at least tenfold. Tables 6.1–6.5 exclude the 63 designs of the sweep that fail it, which are marked "A" in Table A.3. All are wideband parts with 65–92 dB of open-loop gain on photodiodes of 55 pF or more, or on the 20-pF diode for ADA4817-1.

*Table 9.2. The designs on the 380-pF photodiode whose DC open-loop gain is less than ten times the mid-band noise gain: the datasheet open-loop gain, the noise gain $(C_T + C_F)/C_F$, the bandwidth in SPICE and in the analytic model with the datasheet open-loop gain, and the resistor's own pole for comparison.*

<!-- table: table_9_2 -->

**The gain–bandwidth of OPA1656 and OPA2156.** OPA1656 specifies 20 MHz of bandwidth at unity gain and 53 MHz of gain–bandwidth at a gain of 100 (p. 6) [D11], and the analytic model first used the 20 MHz. Its SPICE model (TI SBOMAW6, Rev. C) settles which value applies. An AC analysis with the loop closed at DC only, through a 1-TH inductor, and the inverting input held at signal ground by 1 F, gives the open-loop gain directly (`hg_spice_gbw_check.py`). Its DC gain is 155 dB, and its gain–bandwidth, $|A|f$, is 55.6–56.2 MHz from 10 Hz to 100 kHz and 55.1 MHz at 300 kHz. Above that it falls, to 47.3 MHz at 1 MHz and 30.4 MHz at 3 MHz, where the phase is −111.5° and −119.0° instead of −90°. Unity gain is reached at 21.1 MHz, which is the data sheet's 20 MHz. At the feedback capacitances designed for 20 MHz, SPICE gave bandwidths within 1% of a 53-MHz single pole in seven of the ten designs and within 5% in two more, but 2–16% below the 20-MHz model. The exception was 100 kΩ on the 20-pF photodiode, whose loop crosses over near 3 MHz, where the extra phase lag acts. Redesigned for a 53-MHz single pole, that design peaked by 2.7 dB in SPICE, and the 1-MΩ design on 20 pF and the 100-kΩ design on 380 pF were 20–24% wider in SPICE than in the model. The model therefore uses 53 MHz multiplied by the macromodel's open-loop shape beyond a single pole (`add_aol_shape.py`). With it, SPICE and the model agree within 2.5% in bandwidth and 0.25 dB in excess noise in all ten designs (Table 9.1). OPA2156 shows the same pattern more mildly. Its data sheet gives 20 MHz at unity gain and 25 MHz at a gain of 100 (p. 6) [D12]. Its SPICE model (TI SBOMAR0, Rev. B) has a DC gain of 154.5 dB and a gain–bandwidth of 24.8–24.9 MHz from 10 Hz to 100 kHz, and 23.2 MHz at 1 MHz, with a phase of −98.3° there and −100.7° at 3 MHz. It reaches unity gain at 18.7 MHz. At the feedback capacitances designed for 20 MHz, a 25-MHz single pole matched SPICE within 1.3% from 10 MΩ up, where the 20-MHz model was off by up to 4.4%. With 25 MHz and its open-loop shape, SPICE and the model agree within 0.7% in bandwidth in all ten designs (Table 9.1). OPA1656 and OPA2156 now reach about 1.9 and 1.2 times the bandwidths they had at 20 MHz, with the excess noise that Eq. (22) assigns to the wider bands; at the old bandwidths they are as quiet as before (Section 6.1).

### 9.3 The macromodels' own noise

The analytic model takes its noise from the datasheets, and the SPICE models carry their own. Table 9.3 compares the two. Each model's input voltage noise was taken from a unity-gain buffer with its non-inverting input driven, and its input current noise from the same circuit with a noiseless 100-MΩ resistor in series, as the excess over the voltage noise. Figure 19 shows the voltage-noise spectra against the datasheet points.

*Table 9.3. Input voltage noise at 1 kHz and input current noise at 10 Hz of each macromodel, against the datasheet values used by the analytic model (Table A.1). For LTC6268-10 the datasheet column is the estimate of Appendix B.1.*

<!-- table: table_9_3 -->

![Figure 19](figures/fig8_macromodel_noise.png)

*Figure 19. Input voltage-noise density of the twelve macromodels of Table 9.3 (lines) against the datasheet values (circles).*

The precision parts' models reproduce their datasheets, voltage noise within 8% and current noise within 16%, with one exception: OPA2156's model has 6.5 nV/√Hz at 1 kHz, against 4.0 nV/√Hz in its data sheet. Two wideband models put their low-frequency current noise, 0.25–0.35 fA/√Hz for OPA818 and OPA657, below the shot noise of their own typical bias currents (1.1 and 0.8 fA/√Hz). The analytic model keeps the shot noise as the floor (Section 2.3, Appendix B.1), which is the physical lower limit. The ADA4817-1 model is noisier than its datasheet: 16.2 against 11.8 nV/√Hz at 1 kHz, and 33 fA/√Hz of current noise at 10 Hz. That accounts for its largest deviations in Table 9.1.

### 9.4 The distributed feedback resistor in a loop

Section 3.4 derived the behaviour of a feedback resistor with distributed capacitance to the conductor beneath it with an ideal amplifier. This check puts it into a real loop. A 1-GΩ resistor is modelled as a ladder of 20 sections, with 0.05 pF end to end and 0.3 pF to the conductor beneath it, on the 20-pF photodiode. The conductor beneath is varied in six ways: absent, grounded, driven from the output, driven at one third of the output, split into four strips each driven at the mid-point potential of its quarter, and graded ideally. The ideal graded guard is the arrangement of Seidl, Swoboda and Zimmermann's integrated resistor (Section 3.4). The drives are ideal voltage-controlled sources. Table 9.4 and Figure 20 give the transimpedance and the response to a 100-pA step for OPA140 and OPA928. The model column evaluates Eq. (6) with the ladder's admittances (`hg_model.ladder_y`) and a single-pole amplifier.

*Table 9.4. A 1-GΩ feedback resistor with 0.05 pF end to end and 0.3 pF to the conductor beneath it, on the 20-pF photodiode, for six treatments of that conductor: bandwidth in SPICE and in the model, peaking in SPICE and in the model, and the step overshoot in SPICE.*

<!-- table: table_9_4 -->

![Figure 20](figures/fig9_spice_distributed.png)

*Figure 20. The six treatments of Table 9.4 with OPA140: transimpedance in SPICE (solid) and in the model (dashed), and the SPICE response to a 100-pA step, normalized to its final value. The curves without a conductor and with the ideal graded guard coincide.*

SPICE and the model agree within 1% in bandwidth and 0.1 dB in peaking for five of the six treatments, and within 6% and 0.2 dB for the four strips. The predictions of Section 3.4 hold in a real loop.

- **A grounded plane makes the response peak and ring.** The peak is 7.45 dB with OPA140 and 13 dB with OPA928, and the step overshoots by 54% and 74%. OPA928's slower loop adds to the peak.
- **A plane driven from the output gives a smooth response,** but a quarter of the bandwidth: 1.01 kHz against 4.01 kHz for the resistor without a plane.
- **A plane driven at one third of the output removes the first-order effect** (Eq. (28)). It gives 3.69 kHz with 2% overshoot.
- **Four strips at graded potentials** give 3.56 kHz without overshoot.
- **The ideal graded guard** reproduces the resistor without a plane exactly, 4.01 kHz, because no voltage appears across the distributed capacitance.

### 9.5 The discrete-JFET composite

The composite of Section 5.8 was built from Linear Systems' LSBF862 card, the second-source BF862, as typed into the companion note's scripts. J1 is a common-source stage biased at 10 mA, with a cascode J2 and a 1-kΩ drain load, so $g_mR_D \approx 33$. It is followed by an integrator whose unity-gain frequency of 1.5 MHz gives the composite about the 50 MHz assumed in the analytic model. $C_F$ was chosen in SPICE by the rule of Section 1.4.

The second stage is an ideal transconductance-and-capacitor integrator, not an op amp macromodel. With OPA140's macromodel there, the DC solver repeatedly found latched states, with J1 cut off and the op amp's input clamps conducting. The ideal stage leaves out the second stage's own noise. An op amp's 5 nV/√Hz divided by $g_mR_D \approx 33$ is about 0.15 nV/√Hz, beside the LSBF862 model's 0.6 nV/√Hz, so it would add about 0.3 dB to the excess noise. Table 9.5 and Figure 21 compare the composite with the analytic BF862 composite and with OPA140 alone.

*Table 9.5. The LSBF862 cascode composite in SPICE against the analytic BF862 composite and OPA140 alone (analytic model): bandwidth and excess noise $\Delta N$ over [1 Hz, $f_{-3\,\mathrm{dB}}$].*

<!-- table: table_9_5 -->

![Figure 21](figures/fig10_spice_composite.png)

*Figure 21. Input-referred noise at $R_F$ = 1 MΩ on the 380-pF and 1-nF photodiodes: the LSBF862 cascode composite in SPICE, the analytic BF862 composite, OPA140 alone, and the resistor-plus-diode floor.*

SPICE confirms the composite's advantage. On the 380-pF photodiode it brings the excess noise from 12.4–12.6 dB with OPA140 to 2.8 dB, at 1.8 times the bandwidth. On the 1-nF photodiode it brings 12.5–16.5 dB down to 3.1–5.2 dB. The SPICE composite is 1.7–2.4 dB quieter than the analytic estimate and about 15% slower. The LSBF862 card's channel noise and capacitances differ from the BF862 datasheet values that the analytic model uses.

### 9.6 The logarithmic amplifiers

AD8304 and ADL5303 were run from 100 pA to 10 mA, with 10 pF at the input to stand for a photodiode. Each run gives the operating point, the small-signal bandwidth of $V_{LOG}$ and its noise. Table 9.6 and Figure 22 compare them with Eqs. (31), (33) and (35) and with AD8304's measured noise.

*Table 9.6. AD8304 and ADL5303 macromodels against current: the output $V_{LOG}$; the −3 dB bandwidth of $V_{LOG}$, with Eq. (33) for an effective compensation capacitance of 1.5 pF; the output noise at 1 kHz, with AD8304's measured noise read by eye from its data sheet (Rev. A, p. 5, TPC 9) and the shot-noise bound of Eq. (35) at 200 mV per decade.*

<!-- table: table_9_6 -->

![Figure 22](figures/fig11_spice_logamp.png)

*Figure 22. AD8304 and ADL5303 in LTspice against current: output voltage (left), bandwidth (centre) and output noise at 1 kHz (right), with the 200 mV/decade law, Eq. (33) and Eq. (35), and AD8304's data-sheet values.*

Four results follow, each against an equation of Section 7.2.

- **The law.** The models follow 197 mV per decade from 1 nA to 10 mA, against the data sheet's 200 mV per decade (AD8304 Rev. A, p. 2) [D29]. The decade below 1 nA is compressed to 149 mV, consistent with the data sheet specifying the law's conformance from 1 nA only.
- **The bandwidth** is proportional to the current from 100 pA to about 1 µA, as Eq. (33) states. With 10 pF at the input, an effective compensation capacitance of 1.5 pF reproduces 4.1 kHz at 1 nA and 40 kHz at 10 nA. The data sheet quotes about 2 kHz at 1 nA (p. 1) under its own test conditions. Above 1 µA the bandwidth saturates near 3.2 MHz, with up to 9 dB of peaking at 10 µA in the model.
- **The noise is far above the shot-noise bound at low currents.** The macromodel gives 43, 6.0 and 1.0 µV/√Hz at 1 nA, 10 nA and 100 nA. AD8304's measured spectra give about 40, 5.5 and 1.0 µV/√Hz. Equation (35) at 200 mV per decade gives 2.2, 0.70 and 0.22 µV/√Hz. The vendor's model reproduces the measurement within about 10%, and both lie 5–20 times above the bound of Eq. (35) at 1–100 nA. Equation (35) is therefore a floor that a real log amplifier does not reach at low currents. The measured spectra (TPC 9) rise with frequency towards the bandwidth edge, which points to the loop's own noise rather than to the input current's.
- **At high currents** the noise flattens at 0.15 µV/√Hz, the output stage's floor.

### 9.7 How well the approximate formulas of Chapter 3 hold

Chapter 3 explains the results with approximate formulas: the bandwidth $\sqrt{GBW/(2\pi R_FC_T)}$ of Eq. (19) below $R_F^*$, the resistor's pole $f_R$ of Eq. (4) above it, and the excess noise of Eq. (22). Figure 23 compares them with the full model over the sweep.

![Figure 23](figures/fig12_closed_form_checks.png)

*Figure 23. The approximate formulas of Chapter 3 against the full model, for the designs of the sweep on the four photodiodes with gigaohm-to-megaohm shunt resistance, excluding those that fail the open-loop-gain rule, and OPA1656 and OPA2156, whose open-loop gains are not single poles. Left: bandwidth against Eq. (19) for amplifier-limited designs (blue) and against Eq. (4) for resistor-limited designs (red). Right: excess noise over the resistor alone against Eq. (22), amplifier-limited designs.*

- **Amplifier-limited bandwidth.** For the 252 amplifier-limited designs, the full model's bandwidth is 1.06–1.09 times Eq. (19). The design rule allows 0.1 dB of peaking, so its response is slightly less damped than maximally flat.
- **Resistor-limited bandwidth.** For the 82 resistor-limited designs it is 0.92–1.42 times $f_R$. Section 3.2 explains why it lies between $f_R$ and $\sqrt2\,f_R$, and somewhat below $f_R$ where the loop adds a pole.
- **Excess noise.** Eq. (22) predicts the full model's excess noise within 1 dB in 72% of the amplifier-limited designs, and underestimates it in all of them, by a median of 0.65 dB. The larger differences come from the terms that Eq. (22) leaves out: the amplifier's current noise and the photodiode's shunt resistance, which the full model includes.

The approximate formulas therefore describe the mechanism correctly, and the tables of the note use the full model.

### 9.8 The designs at 10 kΩ, where the notes meet

Section 6.9 ranks the fast parts at 10 kΩ with this note's single-pole model, which leaves out the excess phase of their open-loop curves, and compares that model with the companion's, which includes it. This check runs the vendors' macromodels of those parts at 10 kΩ, so that the ranking and the comparison do not rest on the two models alone. It covers two settings.

- **The 20-pF photodiode of the sweep**, in the decks of Section 9.1. OPA818, OPA858, OPA855, OPA955 and LMH6629 are each run at three designs: the sweep's own design, and the designs of Table 6.8 held to 10 MHz and to 30 MHz, the bandwidths at which that table ranks the FET parts first and the bipolar parts first. Table 9.7 gives the results.
- **The companion's node**, a 1-pF photodiode pair with 0.35 pF of board capacitance, with the companion's supplies and loads: ±2.5 V and 200 Ω for OPA855 and OPA955, and ±6.5 V and 100 Ω for OPA818. Each of the three parts is run at this note's design for 0.1 pF of feedback parasitic, 0.100 pF for OPA855 and OPA955 and 0.195 pF for OPA818, and at the companion's design for 0.2 pF, the minimum total of its 2-kΩ designs, which is 0.206 pF for all three (its Table A6.38). The loop gain is read by Middlebrook's double injection, which combines a voltage and a current injected at the amplifier's output into the loop gain of the intact circuit, as in the companion's Section 5.2. Table 9.8 compares SPICE with both notes' models at the same $C_F$.

The macromodels are TI's for OPA855 (SBOMB43D, Rev. D), OPA858 (SBOMBK7), LMH6629 (SNOM133, with its COMP pin high, the mode for gains of 10 and more) and OPA955 (SLOM544), the files that the companion uses, and OPA818's model of Section 9.1. TI supplies OPA955's model only inside a TINA-TI file, from which the companion copied the netlist out unchanged, and the part itself is in preproduction (Section 6.9). The 21 designs run in a few seconds (`hg_spice_medium.py`).

*Table 9.7. The designs at 10 kΩ on the 20-pF photodiode (S1336-18BK) in SPICE against the analytic model: the sweep's own design and the designs of Table 6.8 held to 10 MHz and 30 MHz. $\Delta N$ is the excess noise of Eq. (16) over [1 Hz, $B$] for both, where $B$ is the model's bandwidth for the sweep's design and the column's bandwidth for the designs of Table 6.8. Both bandwidths are interpolated on the SPICE run's grid of 40 points per decade, which reads the model's 30 MHz as 29.7 MHz. `hg_spice_medium.py`.*

<!-- table: table_9_7 -->

**On the 20-pF photodiode the macromodels confirm the model and the ranking of Table 6.8.** The bandwidths agree within 3.1% in fourteen of the fifteen designs, and no design peaks by more than 0.11 dB. The exception is LMH6629 held to 30 MHz, which reaches 26.8 MHz in SPICE, 9.8% short; its sweep's design is 2.7% short. The excess noise agrees within 0.52 dB, and within 0.84 dB for LMH6629's own design, whose macromodel is 9% quieter at 30 MHz because it carries less input capacitance than its data sheet gives, as the companion found at 2 kΩ (its Section 5.6). Both crossings of Table 6.8 hold. At 10 MHz the FET parts OPA818 and OPA858 come within 5.6–5.8 dB of the floor in SPICE, and the bipolar production parts LMH6629 and OPA855 within 7.2–8.0 dB, against 5.3–5.9 dB and 7.3–8.0 dB in the model. At 30 MHz those two bipolar parts lead: LMH6629 and OPA855 come within 8.3 and 9.3 dB, and OPA818 and OPA858 within 13.4 and 13.5 dB, against 8.8, 9.5, 13.0 and 13.8 dB in the model. OPA955 leads both groups in SPICE as in the model, with 1.7 dB at 10 MHz and 5.5 dB at 30 MHz, against 1.8 and 5.6 dB. OPA818's noise density is 1–6% higher in SPICE, as at the higher gains of Section 9.2, and that of OPA858, OPA855 and OPA955 is 1–4% lower.

*Table 9.8. The designs at 10 kΩ on the companion's node, a 1-pF photodiode pair with 0.35 pF of board capacitance, with the companion's supplies and loads: SPICE against the companion's open-loop model and this note's single-pole model, at the same $C_F$. The phase margin in SPICE comes from Middlebrook's double injection. The noise is the band average of the input-referred noise over 10 MHz to the lower of 150 MHz and the companion model's bandwidth, against the Johnson noise of $R_F$, the measure of the companion's Table A6.38. `hg_spice_medium.py`.*

<!-- table: table_9_8 -->

**On the companion's node the macromodels' bandwidths lie between the two models', or within 1% of both where the feedback capacitance sets the bandwidth.** For OPA855 SPICE gives 215 MHz at 0.100 pF, between the companion's 207 MHz and this note's 219 MHz, with 67.5° of phase margin against 69.4° and 68.9°. At 0.206 pF it gives 84 MHz and 78.8°, which the companion's model reproduces within 0.2% and 0.4°, while this note's gives 86 MHz and 84.4°. OPA855's noise is 0.3 dB below both models'. OPA955 gives 229 MHz at 0.100 pF, between the companion's 244 MHz and this note's 217 MHz, and 85 MHz at 0.206 pF, within 1% of both. Its phase margin also lies between the two models', 62.7° against 54.0° and 71.9° at 0.100 pF and 70.7° against 55.4° and 85.4° at 0.206 pF, because its macromodel has far less phase lag above 300 MHz than its datasheet curve (the companion's Section 5.3). Its noise agrees with the companion's estimate within 0.05 dB and lies 0.5–0.9 dB below this note's. The two models' voltage-noise terms are equal, and the difference lies in the current noise. OPA955's datasheet curve rises above about 10 MHz, from 0.60 pA/√Hz at 10 MHz to 1.49 pA/√Hz at 150 MHz, and this note adds that rise in full, while the companion's model keeps 0.56 pA/√Hz across the band. On the 20-pF photodiode the rise costs only 0.1 dB, because there $e_n\,\omega C_T$ dominates. OPA818 shows the spread between the two models that Section 6.9 found. SPICE gives 120 MHz at 0.195 pF and 115 MHz at 0.206 pF, while the companion's model gives 12% more and this note's 7% less, and its phase margin of 55–57° lies 9° above the companion's and 9° below this note's. OPA818's noise is 2.2 dB above the companion's central estimate and 1.4 dB above this note's, because its macromodel's noise density at tens of megahertz is higher than either model's: 1.82 pA/√Hz at 10 MHz, against 1.40 and 1.52 pA/√Hz. The companion found the same at 2 kΩ, where OPA818's macromodel had 1.6 dB more noise and 15.5° more phase margin than its analysis (its Section 5.6). At 10 kΩ, then, the single-pole model comes as close to the macromodels as the companion's open-loop model does: within 2.3%, 5.2% and 7.2% in bandwidth for OPA855, OPA955 and OPA818, against 3.6%, 6.5% and 12.3%. This supports 10 kΩ as the point where the two notes meet.

### 9.9 What the checks change

Five of the checks' findings change or qualify the analysis.

1. **The DC open-loop gain** must exceed ten times the mid-band noise gain (Section 3.1). This excludes four of the wideband amplifiers, OPA656, OPA657, OPA818 and ADA4817-1, from large photodiodes at high gain. The model and Tables 6.1–6.5 now apply the rule.
2. **The low-frequency current noise of the wideband parts** is taken as the shot noise of their typical bias current below their specified frequencies, not as the specified high-frequency value (Section 2.3). This lowers OPA818's excess noise at 1 GΩ from 1.5 dB to 0.5 dB.
3. **The discrete-JFET composite** performs at least as well in SPICE as estimated (Section 5.8).
4. **The low-current noise of logarithmic amplifiers** is set by their circuits, 5–20 times above the shot-noise bound at 1–100 nA. Their data-sheet noise curves, not Eq. (35), belong in a noise budget (Section 7.2).
5. **The gain–bandwidths of OPA1656 and OPA2156** are their values at a gain of 100, 53 and 25 MHz, not their 20-MHz unity-gain bandwidths, and above about 300 kHz their open-loop gains need the shapes of their SPICE models (Section 9.2). At their smallest stable $C_F$ they now reach about 1.9 and 1.2 times the bandwidths that the note first gave them.

The other results hold: the precision parts' bandwidths and noise (Table 9.1), the distributed resistor's peaking and its board-level remedies (Table 9.4), the approximate formulas' account of the mechanisms (Section 9.7), and the designs at 10 kΩ with the ranking of Table 6.8 (Section 9.8).

---
