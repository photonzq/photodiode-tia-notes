## 6. Selection by gain range

This chapter turns Chapters 2–5 into a choice for each gain decade. Table 6 is the summary. Sections 6.1–6.5 give the reasons and the numbers for each decade, and Sections 6.6 and 6.7 treat the two kinds of photodiode that change the rules: those with low shunt resistance and those with large capacitance. Section 6.8 asks what changes when the signal sits at low frequency, where the band integral no longer describes the measurement. Every number comes from the sweep of Appendix B: 21 op amps and three composites, five photodiodes and five gains, each design with the smallest feedback capacitance that keeps it within 0.1 dB of maximally flat, $C_{par}$ = 0.1 pF and 1 pF of board capacitance. The excess noise $\Delta N$ of Eq. (16) is measured against the resistor-plus-diode floor over each design's own band. DC errors are output errors from the maximum bias current and offset, at 25 °C and 85 °C. The room-temperature part of a DC error can be removed by subtracting a dark reading; its change with temperature cannot, unless the dark reading is repeated in operation. Tables 6.1–6.5 leave out the designs whose DC open-loop gain is less than ten times their mid-band noise gain (Section 3.1). Their narrow bandwidth, not low noise, would otherwise rank them among the quietest. Table A.3 marks them with "A".

*Table 6. What dominates and what to choose, by gain decade. "Small" photodiodes are those of tens of picofarads with gigaohm shunt resistance (S1336-18BK); "large" are those of hundreds of picofarads or more (S1336-8BK, G12180-050A). $\Delta N$ and bandwidths from Tables 6.1–6.5 and A.3; DC errors at 85 °C on the small photodiode.*

| $R_F$ | What dominates the noise in band | What sets the bandwidth | What sets the DC error | Choice for a small photodiode | Choice for a large photodiode |
|---|---|---|---|---|---|
| 100 kΩ | $R_F$ up to $f_e$ ≈ 0.6–0.7 of the band, $e_n\,\omega C$ above it; $e_n\,\omega C$ almost throughout for a large diode | the amplifier: 0.5–1.5 MHz for precision parts, 4–18 MHz for wideband parts | offset | ADA4625-1 (3.6 dB, 0.88 MHz) or OPA2156 (3.6 dB, 1.26 MHz); OPA1656 or OPA2156 held to 1 MHz by a larger $C_F$ (2.6–2.7 dB), or OPA1656 at 1.9 MHz (5.9 dB); BF862 or LSK170 composite (0.7–1.1 dB, 1.4–1.6 MHz); wideband FET parts beyond 2 MHz at 13.6–23 dB | IF3601 composite (3–4 dB); otherwise ADA4625-1 or OPA2156 (11–16 dB) |
| 1 MΩ | as at 100 kΩ, everything $\sqrt{10}$ lower in frequency | the amplifier: 0.2–0.5 MHz; wideband parts reach 1.3–1.9 MHz, near the resistor's pole | offset | as at 100 kΩ (3.4–3.5 dB at 0.28–0.39 MHz, or 2.5–2.7 dB held to 0.33 MHz; OPA1656 also at 0.65 MHz with 6.0 dB); OPA818 at the resistor's 1.84 MHz with 9.5 dB | as at 100 kΩ |
| 10 MΩ | $R_F$ and $e_n\,\omega C$ about equal (small); $e_n\,\omega C$ (large) | the resistor (150–180 kHz) for wideband parts; the amplifier (58–150 kHz) for precision parts | offset, plus bias current at 85 °C (3–15 mV for precision parts, 52 mV for OPA656 and OPA657) | OPA818 (2.3 dB, 162 kHz, resistor-limited); OPA2156 (3.6 dB, 121 kHz) or OPA1656 (5.2 dB, 183 kHz); BF862 or LSK170 composite (1.3–1.4 dB, 141–165 kHz) | composite; otherwise ADA4625-1 or OPA2156 (10.9–11.6 dB) |
| 100 MΩ | $R_F$ (small); $e_n\,\omega C$ (large) | the resistor, 16 kHz, for most parts; the amplifier for large diodes (5–10 kHz) | bias current: 30–500 mV at 85 °C for JFET parts, 5 mV for OPA320, 44 µV for ADA4530-1 | OPA818, OPA657 (0.6–1.2 dB) if 0.07–0.5 V at 85 °C is acceptable; OPA1656 (1.5 dB); OPA320 (3.8 dB, 5 mV); ADA4530-1, OPA928 (4.3–5.2 dB, 30–45 µV) | ADA4625-1, OPA2156 (10–11.5 dB) or a composite |
| 1 GΩ | $R_F$ plus the diode's $R_{sh}$; the amplifier's $i_n$ above its $R_{F,\mathrm{crit}}$; $e_n\,\omega C$ for a large diode | the resistor, 1.6 kHz, unless equalized | bias current and leakage: JFET parts 0.3–1 V at 85 °C, OPA320 50 mV, electrometers 60–80 µV | OPA140, OPA828, OPA145 (0.3–0.4 dB) where the temperature is held; OPA320 (0.4 dB, 50 mV); ADA4530-1, OPA928 (1.5–1.7 dB, < 0.1 mV) where DC accuracy decides | OPA828, ADA4625-1 (4.8–5.2 dB) |

The table follows three rules from Chapters 2–3. Below the crossover gain $R_F^*$ the amplifier sets the bandwidth and the excess noise is fixed by $e_n$, $C_T$ and $GBW$ (Eqs. (21)–(22)). Above $R_F^*$ the resistor sets the bandwidth and the voltage noise fades from the band (Eq. (23)). The amplifier's current noise and DC input current gain weight with every decade (Eqs. (11) and (15)).

### 6.1 100 kΩ

*Table 6.1. The four quietest designs and the fastest one for each photodiode at 100 kΩ (excess noise $\Delta N$, Eq. (16); −3 dB bandwidth). Composites are excluded here and shown in Section 6.7.*

<!-- table: table_6_1 -->

At 100 kΩ the floor is 406 fA/√Hz, high enough that every FET input's current noise is negligible (all $R_{F,\mathrm{crit}}$ exceed 1.6 MΩ, Table A.2), and even the bipolar OPA211 competes on the largest photodiode. The amplifier sets the bandwidth, and the voltage noise on the node capacitance decides the excess, as Eq. (22) predicts. The quietest parts are therefore those with the lowest $e_n$ at 0.1–1 MHz and modest input capacitance: OPA1656 and OPA2156 (2.9–3.0 nV/√Hz at 10 kHz), then ADA4625-1 (3.3 nV/√Hz, but 19.9 pF). OPA1656 is missing from Table 6.1, which ranks each part at its own widest flat bandwidth. With 53 MHz of gain–bandwidth at high noise gain, its smallest stable $C_F$ gives 1.94 MHz at 5.9 dB (Table A.3a). OPA2156, with 25 MHz, reaches 1.26 MHz at 3.6 dB. Held to OPA2156's bandwidth by a larger $C_F$, OPA1656 is slightly quieter than OPA2156: 3.56 against 3.64 dB at 100 kΩ, 3.22 against 3.37 dB at 1 MΩ and 3.14 against 3.63 dB at 10 MΩ. Held to 1 MHz, 330 kHz and 100 kHz, the two come within 2.4–3.0 dB of the floor (`hg_equal_bandwidth_check.py`). The fastest is always LTC6268-10, which reaches 2.7–18 MHz by Eq. (19) with its 4-GHz gain–bandwidth product, at 23–39 dB of excess. Between these extremes OPA818, ADA4817-1 and OPA656 trade noise for bandwidth along the line that Eq. (22) describes: at 4.1–15 MHz on the small diode they have 13.6–16.5 dB of excess (Table A.3a). The DC error is that of the offset, 0.1–2 mV, since even 20 pA of bias current makes only 2 µV at 100 kΩ. At this gain, then, the choice is between a low-noise precision part at up to about 1 MHz and a wideband part beyond it, with a discrete-JFET composite (Section 6.7) when both noise and bandwidth matter.

### 6.2 1 MΩ

*Table 6.2. As Table 6.1, at 1 MΩ.*

<!-- table: table_6_2 -->

At 1 MΩ the pattern is the same (Table 6.2), with every frequency $\sqrt{10}$ lower, as Eq. (19) and Eq. (13) both scale as $1/\sqrt{R_F}$. Two changes appear. The zero-drift OPA388 and the bipolar OPA211 have fallen out: OPA388's 100 fA/√Hz is now comparable with the 128 fA/√Hz floor, and OPA211's 1.7 pA/√Hz exceeds it thirteen times. Second, the wideband parts with the smallest input capacitance begin to meet the resistor's ceiling. OPA818 is resistor-limited at 1.84 MHz with 0.1 pF. Equation (4) gives 1.59 MHz for the bare pole, but a design near the crossover gain $R_F^*$ has a response close to maximally flat, whose −3 dB point lies between $f_R$ and $\sqrt2\,f_R$ (Section 3.2). On the extended-InGaAs diode, $R_F$ = 1 MΩ is already 71 times $R_{sh}$, and the diode's own noise takes 79% of the band (Table 4a). Every decent amplifier is then within 1 dB of the floor, but the bandwidth and the offset suffer (Section 6.6).

### 6.3 10 MΩ

*Table 6.3. As Table 6.1, at 10 MΩ.*

<!-- table: table_6_3 -->

At 10 MΩ the two ceilings of Section 3.2 meet (Table 6.3). On the small photodiode, the wideband parts reach the resistor's own pole: OPA818 and LTC6268-10 at 162 kHz, OPA657 at 151 kHz, and OPA656 at 179 kHz, which lies between $f_R$ and $\sqrt2\,f_R$ for the same reason as at 1 MΩ. ADA4817-1 fails the open-loop-gain condition of Section 3.1 on this diode from 1 MΩ up and is left out. Because Eq. (23) now gives $f_e/f_R$ of about 1, the resistor-limited designs carry only 2.3–8.0 dB of excess (Table A.3a). OPA818 is the quietest single op amp here, at 2.3 dB and 162 kHz, within 12% of the fastest, OPA1656 at 183 kHz. The precision and low-noise CMOS parts stay amplifier-limited at 58–183 kHz with 3.5–7.3 dB. The DC error is still dominated by the offset at 25 °C, but at 85 °C the bias current of the JFET parts adds 3–50 mV (Table A.3a). On the large photodiodes nothing changes: the voltage noise takes over 90% of the band, and only a lower $e_n\,C_T$ helps (Section 6.7).

### 6.4 100 MΩ

*Table 6.4. As Table 6.1, at 100 MΩ.*

<!-- table: table_6_4 -->

At 100 MΩ the resistor sets the bandwidth for almost every part on the small photodiodes, at 15–22 kHz (Table 6.4). The designs above the 15.9 kHz of the bare 0.1-pF pole are those near their crossover gain $R_F^*$ (for OPA140 it is 110 MΩ by Eq. (20)), whose response is close to maximally flat with its −3 dB point at up to $\sqrt2\,f_R$ = 22.5 kHz. The excess is small for every FET-input part with a small input capacitance and moderate current noise: 0.6–1.2 dB for OPA818 and OPA657, and 1.5–2.5 dB for OPA1656, OPA828, OPA827 and ADA4625-1. The electrometers have 4.3–5.2 dB because of their larger voltage noise (Table A.3a). The choice now turns on DC accuracy, because the bias current multiplied by 100 MΩ is no longer small. At 25 °C the maximum output errors on the small photodiode are 1.1–7.6 mV for the precision JFET parts and 3.8 mV for OPA818. At 85 °C they are 31–99 mV and 71 mV, 0.13–0.5 V for the other wideband parts, 5.2 mV for OPA320, 0.82 mV for LTC6268-10, and 28–44 µV for the electrometers. For a measurement at a controlled temperature with periodic dark subtraction, OPA818 or OPA1656 gives the lowest noise. For one that must hold its zero over a wide temperature range, OPA320, LTC6268-10 or an electrometer is the better choice, at 3.5–5.2 dB of excess noise instead of 0.6–1.5 dB. LMP7721, at 4.4 dB here, is still usable, because 100 MΩ is below its $R_{F,\mathrm{crit}}$ of 165 MΩ.

### 6.5 1 GΩ

*Table 6.5. As Table 6.1, at 1 GΩ.*

<!-- table: table_6_5 -->

At 1 GΩ the floor is 4.06 fA/√Hz, and three amplifier properties that were negligible at lower gains now decide (Table 6.5).

- **Current noise.** Parts whose $R_{F,\mathrm{crit}}$ lies below 1 GΩ lose: ADA4625-1 (813 MΩ) has 2.7 dB on the small photodiode, OPA1656 (457 MΩ) 4.0 dB, LMP7721 (165 MΩ) 7.1 dB and OPA2156 (46 MΩ) 11.9 dB. The winners on the small photodiode are the parts with sub-femtoampere current noise, OPA140, OPA145 and OPA320 (0.3–0.4 dB), together with OPA828 and OPA657, whose 1.2–1.3 fA/√Hz is below a third of the floor in amplitude and below a tenth in power.
- **Voltage noise on capacitance.** On the 380-pF diode, $f_e$ lies below the resistor's 1.6-kHz pole (Table A.5), and the lowest $e_n$ wins again: OPA828 and ADA4625-1, at 4.8–5.2 dB.
- **DC accuracy.** With maximum bias currents, the output errors at 25 °C are 8.5–75 mV for the JFET parts, 1.1 mV for OPA320 and 58–80 µV for the electrometers. At 85 °C they become 0.31–0.99 V, 50 mV and 58–80 µV.

The electrometers are 1.5–1.7 dB above the floor on the small diode. Their voltage noise is the reason: $f_e$ = 1.75 kHz (Table A.5) lies at the band edge, and their flicker corner lies inside the band (Section 2.4). That is the price of a zero that holds from −40 °C to 85 °C within 20 fA. The choice at 1 GΩ is therefore a choice of what matters more. Where the temperature is controlled and the dark level can be subtracted, OPA140, OPA145 or OPA828 come within 0.4 dB of the floor. Where the zero must hold unattended, OPA320 (0.4 dB, 50 mV at 85 °C) or an electrometer (1.5–1.7 dB, below 0.1 mV) is the answer. At this gain the leakage of the board (Chapter 8) is as large an error as the amplifier's bias current, so the electrometers' guard buffers are part of the reason to choose them.

### 6.6 Photodiodes with low shunt resistance

For the extended-InGaAs photodiode with 14 kΩ of shunt resistance, Eqs. (10), (12) and (24) set three limits that do not depend on the amplifier class.

- **The floor.** Above $R_F \approx 10\,R_{sh}$ = 140 kΩ, the floor is the diode's own 1.08 pA/√Hz, and a larger $R_F$ lowers it by less than 0.4 dB (Section 2.2).
- **The amplifier's voltage noise.** It must stay below $e_{n,\mathrm{crit}} = \sqrt{4k_BT\,(R_F\parallel R_{sh})}$, which is 15.2 nV/√Hz at large $R_F$. The CMOS electrometers fail this in their flicker region; the sweep shows ADA4530-1's $e_n/(R_F\parallel R_{sh})$ term taking 63–97% of the band from 10 MΩ up (Table 4b).
- **The bandwidth and the offset.** The bandwidth falls as $GBW\,R_{sh}/R_F$, to 235 Hz at 1 GΩ for ADA4625-1. The offset grows as $1 + R_F/R_{sh}$, to 5.7 V at 1 GΩ for 80 µV.

The right design is therefore $R_F \approx$ 100–150 kΩ with a low-voltage-noise part: ADA4625-1 or OPA2156, which come within 4.7–5.2 dB of the diode's floor at 250–308 kHz (Table 6.1), or OPA1656, which reaches 488 kHz at 8.0 dB. Any further gain belongs in a voltage stage after the TIA. Since the offset is multiplied by $1 + R_F/R_{sh}$ (about 8 at 100 kΩ), a zero-drift part has a real advantage here, and OPA388 at 100 kΩ has 7.7 dB of excess, 190 kHz and 2.3 mV of error at 85 °C (Table A.3e). Cooling the diode is the most effective single step: two-stage cooling to −20 °C raises the 1-mm diode's shunt resistance from 14 kΩ to 280 kΩ (Table 1), which lowers its floor by $10\log_{10}20$ = 13 dB.

### 6.7 What helps with a large photodiode

For photodiodes of a few hundred picofarads and more, the voltage noise on the capacitance dominates up to 100 MΩ (Table 4a), and no monolithic op amp of the survey comes within 10 dB of the floor. Four remedies exist, and Section 3.5 and Section 5.8 give their physics.

- **A discrete-JFET composite** lowers $e_n\,C_T$ by 11–18 dB (Section 5.8). In the sweep it brings the 380-pF diode to 3.0 dB (IF3601) and the 1-nF diode to 2.1–4.0 dB at 100 kΩ–10 MΩ, at equal or higher bandwidth than the best op amp (Table A.3c–d).
- **Bootstrapping** removes the photodiode's capacitance from the op amp's loop. The noise is that of the bootstrap device's $e_n$ times $\omega C_D$, but the bandwidth is set by the small remaining capacitance (Section 3.5).
- **Reverse bias** cuts the capacitance by up to a factor of 12 (3.7 nF to 300 pF for the S3584-08, Table 1) but adds the dark current's shot noise. It pays below the gain at which that shot noise reaches the resistor's floor, $R_F = 2k_BT/(qI_D)$ by Eq. (2): 5.1 MΩ for 10 nA.
- **Cooling** raises the shunt resistance, by a factor of 77 for the 5-mm InGaAs diode at −20 °C (Table 1). That matters at the highest gains, where the diode's shunt noise joins the voltage noise as the dominant term (Table 4a, G12180-050A at 100 MΩ–1 GΩ).

### 6.8 Signals at low frequency

The excess noise $\Delta N$ of the sweep integrates each design's noise over its whole band, and the upper part of the band dominates that integral. A measurement whose signal sits at low frequency, such as chopped light, a lock-in measurement or a slow modulation, sees instead the noise density near its own frequency. There the amplifiers' 1/f corners decide and the capacitive term is small, so the ranking can differ from that of Tables 6.1–6.5. This section gives the voltage noise an amplifier may have at a given frequency, evaluates the sweep's designs at 10 Hz and 100 Hz (Tables A.8a–b), and states where the choice of Sections 6.1–6.7 changes.

**What an amplifier may add.** At a frequency $f$ the voltage-noise term of Eq. (8) is $e_n^2(f)\,|Y_n(f)|^2$, with $|Y_n|^2 = G^2 + [2\pi f\,(C_T + C_F)]^2$ and $G = 1/R_F + 1/R_{sh}$. Flicker noise raises $e_n^2$ as $1/f$, while the capacitive part of $|Y_n|^2$ falls as $f^2$, so toward low frequency the capacitance matters less, not more, and only the conductance keeps the voltage noise in play. The voltage noise that alone would double the floor of Eq. (10) at the frequency $f$ is

$$
e_{n,\mathrm{crit}}(f) = \frac{\sqrt{4k_BT\,G}}{|Y_n(f)|},
\tag{30a}
$$

which is Eq. (12) where the conductance dominates $|Y_n|$, and $\sqrt{4k_BT\,G}/[2\pi f\,(C_T + C_F)]$ where the capacitance does. Table 6.6 evaluates it at 100 Hz, with 10 pF of amplifier input capacitance and 1 pF of board capacitance. On the small and medium photodiodes it is 41 nV/√Hz at 100 kΩ and hundreds of nanovolts per root hertz above that. On the 14-kΩ photodiode it is about 15 nV/√Hz at every gain, the Johnson voltage noise of $R_{sh}$. On the 380-pF photodiode it falls to 58 and 31 nV/√Hz at 100 MΩ and 1 GΩ, because there the capacitance still dominates $|Y_n|$ at 100 Hz: $2\pi\times100\ \mathrm{Hz}\times391\ \mathrm{pF}$ = 0.25 µS, against $G$ = 3.5 nS at 1 GΩ.

*Table 6.6. The voltage noise $e_{n,\mathrm{crit}}$ of Eq. (30a) at 100 Hz, in nV/√Hz, which alone would double the floor of the resistor and the photodiode, with 10 pF of amplifier input capacitance and 1 pF of board capacitance. `hg_low_frequency_noise.py`.*

<!-- table: table_6_6 -->

**What Tables A.8a–b show.**
- **On a photodiode with low shunt resistance the 1/f corner decides.** On the 14-kΩ photodiode at 100 Hz, ADA4625-1 adds 0.2–0.3 dB to the floor, OPA827 0.3–0.4 dB, OPA828 0.4–0.5 dB and OPA140 0.6–0.7 dB. The zero-drift OPA388, which has no 1/f noise, adds 0.9–1.0 dB at 10 Hz and at 100 Hz alike. OPA1656 and OPA2156 add 2.1–2.3 dB at 100 Hz and 7.4–8.7 dB at 10 Hz, so on this photodiode they suit only a band that stays above about 1 kHz. The electrometers add 3.8–8.7 dB, OPA818 5.9–6.3 dB and LTC6268-10 15.5–16.0 dB, while the discrete-JFET composites stay within 0.1 dB.
- **At 100 kΩ the wideband parts and the electrometers lose.** On the small photodiode at 100 Hz, LTC6268-10 adds 7.6 dB, ADA4817-1 4.4 dB, ADA4530-1 2.5 dB and OPA818 1.5 dB; at 10 Hz OPA1656 and OPA2156 add 2.1–2.5 dB. From 10 MΩ up the voltage noise no longer matters on the small and medium photodiodes.
- **From 10 MΩ up the electrometers lose their noise penalty.** At 100 Hz ADA4530-1 and OPA928 come within 0.1 dB of the floor at 100 MΩ and 1 GΩ on the small photodiode, against 4.3–5.2 dB and 1.5–1.7 dB over the band (Table A.3a). A slow measurement at these gains therefore gives up nothing for the electrometers' DC accuracy and guard buffers (Section 6.5).
- **A large photodiode no longer needs a composite.** At 100 Hz the precision JFET-input parts stay within 0.4 dB of the floor up to 100 MΩ on the 380-pF and 1-nF photodiodes, against 10–20 dB over the band at 100 kΩ–10 MΩ (Tables A.3c–d). At 1 GΩ on the 380-pF photodiode, where $e_{n,\mathrm{crit}}$ is 31 nV/√Hz, ADA4530-1 adds 3.7 dB, OPA818 2.3 dB and ADA4625-1 1.4 dB, the last from its current noise, while OPA828, OPA827 and OPA140 add 0.2–0.4 dB.
- **The current noise, as modelled, changes little.** The model holds each FET input's current noise at its datasheet value below the datasheet's frequency. For a JFET input that value is the shot noise of the gate current, which is white; for the CMOS parts whose current noise exceeds that shot noise (Appendix C, item 20), its behaviour below 1 kHz is not specified. $R_{F,\mathrm{crit}}$ of Eq. (11) therefore still rules out OPA2156 from 100 MΩ up, at every frequency. The bipolar OPA211 grows worse toward low frequency, with 2.3 pA/√Hz at 100 Hz.

**What else changes at low frequency.** Three points follow.

*The feedback resistor's excess noise.* With the output at a DC voltage $V_{out}$, the feedback resistor carries a DC current and adds 1/f excess noise. Its noise index NI is the rms excess noise in microvolts per volt of DC per decade of frequency, and a $1/f$ density integrates over one decade to its value at $f$ times $\sqrt{f\ln 10}$, so that

$$
e_{\mathrm{ex}}(f) = \frac{10^{\mathrm{NI}/20}\ \mathrm{\mu V/V}\times V_{out}}{\sqrt{f\ln 10}}.
\tag{30b}
$$

It stays below the resistor's Johnson noise $\sqrt{4k_BTR_F}$ if $\mathrm{NI} < 20\log_{10}\!\left(\sqrt{4k_BTR_F}\,\sqrt{f\ln 10}/(1\ \mathrm{\mu V/V}\times V_{out})\right)$. At 100 Hz with 10 V across the resistor, that is −24 dB for 100 kΩ and +15.8 dB for 1 GΩ. A high-value resistor's own Johnson noise hides its excess noise, whereas a resistor of 100 kΩ or less with volts across it needs a low-noise type; its datasheet gives the noise index.

*Zero bias.* A reverse-biased photodiode adds the shot noise of its dark current (Section 2.2), and possibly low-frequency excess noise that the model does not include, so a slow measurement favours zero bias wherever the capacitance allows it.

*The gaps in the data.* Below their first datasheet point the model holds the voltage noise of LMC662 and LMC6001A flat from 1 kHz, that of OPA381 from 10 kHz, and that of OPA656 and the BF862 composite from 100 kHz, so their entries in Tables A.8a–b are lower bounds (Appendix C, item 22). The 100-Hz values of OPA320 and LMP7721 continue their datasheet slopes, and that of ADA4530-1 is interpolated between its 10-Hz and 1-kHz values.

---
