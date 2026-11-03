## 7. Beyond a single linear TIA

Equation (5) showed that a resistor-limited TIA has a window of about five decades of current, $V_{sw}/\sqrt{k_BT/C_{par}}$ = 93.8 dB for 10 V of swing and 0.1 pF. Changing $R_F$ moves the window but does not widen it. Signals spanning more than five decades, such as optical power meters, absorbance measurements and laser-diode test, therefore need gain ranging, a logarithmic amplifier, or an integrator. This chapter treats the three, and then the point at which a detector with internal gain is the better answer.

### 7.1 Gain ranging

Several feedback resistors, selected by switches, extend the window decade by decade, but the switches bring three errors of their own into the summing node.

- **Leakage of the off switches.** An open switch with off-resistance $R_{off}$ and the output voltage across it injects $V_{out}/R_{off}$. To keep that below a current $I_{allowed}$ the switch needs $R_{off} \geq V_{out}/I_{allowed}$: $5\times10^{14}$ Ω for 20 fA at 10 V. A switch placed between a resistor and the output does not escape the problem, because the unselected resistor then connects the summing node to a floating node whose leakage reaches the summing node through it. The standard remedy is a T-arrangement of two series switches with a shunt switch that ties their junction to the summing node's potential when open (Figure 13). The inner switch then sees almost no voltage and leaks almost nothing, while the outer switch's leakage goes to the shunt.
- **Capacitance.** Each switch's capacitance adds to $C_F$ of its range when closed and to $C_T$ when open, which lowers the bandwidth (Eq. (4)) and raises the $e_n\,\omega C$ term (Eq. (9)).
- **Charge injection.** Opening or closing a switch injects a charge $Q_{inj}$ into the summing node, which appears at the output as $\Delta V_{out} = Q_{inj}/C_F$. With 1 pC on 0.1 pF this is 10 V, enough to saturate the output, after which the circuit recovers with the time constant $R_FC_F$, 0.1 ms at 1 GΩ and 0.1 pF, or longer if the amplifier saturated. A range change at high gain is therefore a slow event, and dielectric relaxation in the board (Section 8.3) can lengthen it further.

![Figure 13](figures/schem_gain_ranging.png)

*Figure 13. Gain ranging with T-switches. Each range's feedback resistor connects to the summing node through an inner switch $S_{in}$ and an outer switch $S_{out}$, and a shunt switch $S_{sh}$ ties their junction to ground, the summing node's potential, while the range is off. Range 1 is selected: $S_{in}$ and $S_{out}$ are closed and $S_{sh}$ is open. In range 2 the outer switch carries the output voltage, but its leakage flows into the closed shunt, and the inner switch sees almost no voltage and so leaks almost nothing. Each switch's capacitance adds to $C_F$ when closed and to $C_T$ when open, and each change of range injects charge.*

The on-resistance of a switch in series with $R_F$ is negligible at the gains of this note. Keeping the switch out of the signal path altogether, by sensing the output at the selected resistor's output end, removes even that error.

### 7.2 Logarithmic amplifiers

**Principle.** Replacing $R_F$ by a bipolar transistor, with its collector at the summing node, its base at ground and its emitter driven by the output, gives a transdiode logarithmic amplifier (Figure 14). The collector current equals the photocurrent, so the output is

$$
V_{out} = -V_T\ln\frac{I_{ph}}{I_S} , \qquad V_T = \frac{k_BT}{q} ,
\tag{31}
$$

with $I_S$ the transistor's saturation current: 59.2 mV per decade at 25 °C, $V_T\ln10 = 25.69\ \mathrm{mV}\times2.303$. Equation (31) has two temperature dependences. The slope is proportional to the absolute temperature, +0.34%/°C at 25 °C. $I_S$ changes much faster, roughly doubling every few degrees. A second, matched transistor carrying a reference current $I_{ref}$ cancels $I_S$, giving a log-ratio amplifier,

$$
V_{out} = K\log_{10}\frac{I_1}{I_2} ,
\tag{32}
$$

and a gain stage with a temperature-dependent resistor compensates the slope. Integrated parts work this way. LOG112 has 7.5 decades from 100 pA to 3.5 mA, a scale factor of 0.5 V per decade and internal resistors that compensate the change of gain with temperature (LOG112 data sheet, p. 1) [D25]. Its log conformity error is 0.2% maximum over 1 nA–100 µA and 0.13% typical over 7.5 decades, and its gain changes by 0.01%/°C maximum (p. 3). LOG114 covers eight decades from 100 pA to 10 mA on a single 5-V supply, with 0.375 V per decade (LOG114 data sheet, p. 1) [D26]. Analog Devices' AD8304 covers the same 160 dB, 100 pA to 10 mA, from a single supply of 3.0–5.5 V (AD8304 data sheet Rev. A, p. 1) [D29]. ADL5303 has the same architecture and nearly the same specifications in a 16-lead package (ADL5303 data sheet Rev. D, pp. 1 and 3) [D30]. In both, the photocurrent flows in the collector of a scaled NPN transistor in the feedback path of a low-offset JFET amplifier, and the summing node is held at 0.5 V, with guard pins on either side of the input that follow it (AD8304, p. 1). The slope at the VLOG pin is laser-trimmed to 200 mV per decade, which is 10 mV per decibel of optical power, within 196–204 mV for AD8304 at 25 °C, and the intercept is trimmed to 100 pA (p. 2). The law conformance error is 0.1 dB typical and 0.7 dB maximum from 1 nA to 1 mA (p. 2). Both parts also bias the photodiode adaptively, with about 0.1 V at 100 pA rising linearly to 2 V at 10 mA. That keeps the dark current small at low light and the diode fast at high light (p. 1).

![Figure 14](figures/schem_log_amp.png)

*Figure 14. The transdiode logarithmic amplifier. The transistor Q replaces $R_F$: its collector is at the summing node, its base at ground and its emitter is driven by the output, so its collector current equals the photocurrent and the output is $-V_T\ln(I_{ph}/I_S)$ (Eq. (31)). The compensation capacitor $C_C$ across it sets the bandwidth, $I/(2\pi V_TC_C)$ (Eq. (33)), and the optional emitter resistor $R_E$ limits the loop gain at the top of the range (Eq. (34)).*

**Bandwidth.** The small-signal resistance of the transistor is $r_e = V_T/I$, which falls from 257 MΩ at 100 pA to 25.7 Ω at 1 mA. With a compensation capacitor $C_C$ across it, the log amplifier is a TIA with $R_F = r_e$ and $C_F = C_C$, and its bandwidth is the feedback pole,

$$
f_{-3\,\mathrm{dB}} = \frac{1}{2\pi r_eC_C} = \frac{I}{2\pi V_TC_C} .
\tag{33}
$$

The bandwidth is proportional to the current. With $C_C$ = 10 pF it is 62 Hz at 100 pA, 620 Hz at 1 nA, 6.2 kHz at 10 nA and 62 kHz at 100 nA (Table A.7). The measured 3-dB response of LOG112 has the same slope and lies a factor of about 1.5–2 below Eq. (33). With 10 pF its curves pass about 30–40 Hz at 100 pA and 0.3–0.6 kHz at 1 nA, and they flatten at 30–500 kHz at high currents, where the amplifier takes over (p. 6, upper right; read by eye) [D25]. AD8304 and ADL5303 give about 2 kHz at 1 nA, rising in proportion to the current up to 10 MHz (AD8304, p. 1; ADL5303, p. 1) [D29], [D30]. Their LTspice models follow Eq. (33) from 100 pA to about 1 µA, with an effective $C_C$ of about 1.5 pF when 10 pF of photodiode capacitance sits at the input (Section 9.6). A log amplifier is thus fast at the top of its range and slow at the bottom, so a falling optical signal is followed much more slowly than a rising one.

**Stability.** The loop of a transdiode log amplifier runs from the output through the emitter, which a common-base transistor passes to the collector with a current gain near 1, into the node impedance $Z_n$ of the summing node and back to the op amp's input. Its loop gain is therefore

$$
T(s) = A(s)\,\frac{Z_n(s)}{r_e + R_E} ,
\tag{34}
$$

with $R_E$ an optional resistor in series with the emitter. At high currents $r_e$ is small, and with a capacitive node, $Z_n = 1/(sC_T)$, Eq. (34) has two integrators in the loop, the op amp's and the node's. Without compensation it would oscillate at the top of the range. $R_E$ limits the loop gain, and $C_C$ provides a feedback path that dominates at high frequency, as $C_F$ does in a TIA. The minimum $C_C$ therefore grows with the largest current, and Eq. (33) then sets the bandwidth at the smallest current. LOG112 states the trade explicitly. The smallest usable capacitor is set by the maximum of $I_2$ and the minimum of $I_1$, and "larger values of $C_C$ make the LOG112 and LOG2112 more stable, but reduce the frequency response" (p. 8) [D25]. Its curves of minimum $C_C$ run from below 2 pF to beyond 1 µF as the current ratio grows (p. 6, upper left). The datasheet also suggests switching $C_C$ according to the output level to get the highest overall bandwidth (p. 8). A wide dynamic range and a high bandwidth at the low end exclude each other, through Eqs. (33) and (34).

**Noise.** The transistor's collector current carries its own shot noise, $2qI$, which adds to the photocurrent's $2qI$. The input-referred noise of a log amplifier is therefore

$$
i_n^2 = 4qI , \qquad \frac{v_{n,out}}{V_T} = \sqrt{\frac{4q}{I}} ,
\tag{35}
$$

3 dB above the shot noise of the signal itself, plus the op amp's own terms. At 1 nA the relative noise is $\sqrt{4\times1.602\times10^{-19}/10^{-9}}$ = $2.53\times10^{-5}$ per √Hz, or 650 nV/√Hz at the core's 59.2-mV/decade output. In a 1-kHz band that is a relative error of $8.0\times10^{-4}$, which corresponds to $8.0\times10^{-4}/\ln10$ = 0.035% of a decade. At the low end the op amp's bias current sets the limit. LOG112 specifies ±5 pA, doubling every 10 °C, with 30 nV/√Hz and 4 fA/√Hz at 1 kHz (p. 3), so at 100 pA its bias current is already 5% of the signal at 25 °C. At the high end the transistor's bulk resistances distort the law: at 4.5 mA on ±5 V supplies, or 10 mA on ±12 V, the total output error of LOG112 "can be between 15% and 25%" (p. 9) [D25].

Real log amplifiers are much noisier than Eq. (35) at low currents. AD8304's output noise at 1 kHz, read by eye from its measured spectra, is about 40, 5.5 and 1.0 µV/√Hz at 1, 10 and 100 nA (AD8304, p. 5, TPC 9) [D29]. Equation (35), scaled to its 200 mV per decade, gives 2.2, 0.70 and 0.22 µV/√Hz. The vendor's LTspice model reproduces the measurement within about 10% (Section 9.6). The excess, 5–20 times at 1–100 nA, comes from the amplifier's own circuit rather than from the input current. Its mechanism was not identified (Appendix C, item 6). At 1 kHz and above about 1 µA the measured noise flattens near 0.15 µV/√Hz.

**When to use one.** A log amplifier is the right choice when the signal spans more than five decades, the measurement is ratiometric or logarithmic by nature (absorbance, optical power in dBm), and the bandwidth needed at the low end is modest. Equation (35) sets only the floor of the noise penalty, 3 dB against shot noise. Real log amplifiers lie well above it at low currents, so their data-sheet noise curves, not Eq. (35), belong in a noise budget. For bandwidth at low currents, or linear accuracy better than the conformity error, gain ranging (Section 7.1) or two TIAs of different gains in parallel are better.

### 7.3 Switched integrators and current-input ADCs

A switched integrator collects the photocurrent on a capacitor $C_{int}$ in the op amp's feedback path for a time $T$, reads the output, and then resets $C_{int}$ with a switch (Figure 15). It has no feedback resistor. Whether that matters depends on how large the resistor's noise is compared with the other noise of a measurement. The comparison is clearest when every noise is counted as a charge per measurement, because an integrator measures charge: the mean current over $T$ is the charge collected divided by $T$.

![Figure 15](figures/schem_integrator.png)

*Figure 15. A switched integrator in the arrangement of IVC102. The input switch $S_1$ connects the photodiode during the integration and disconnects it to hold. The photocurrent charges $C_{int}$, which IVC102 provides as 10, 30 and 60 pF on chip, alone or together up to 100 pF, and the reset switch $S_2$ discharges it before each measurement. The ADC samples the output once after the reset, $V_1$, and once after the integration time $T$, $V_2$. The charge is $C_{int}(V_2 - V_1)$, and the double sampling removes the reset noise and the charge that $S_2$ injects.*

**The feedback resistor's noise as a charge.** A resistor is a noise source that never stops. Its Johnson noise current, with the power density $4k_BT/R_F$, keeps adding charge for as long as the measurement lasts. Averaging white noise over a time $T$ passes a noise bandwidth of $1/(2T)$, so the noise charge that the resistor adds in one measurement has the variance

$$
Q_R^2 = \frac{4k_BT}{R_F}\cdot\frac{1}{2T}\cdot T^2 = \frac{2k_BT\,T}{R_F} .
\tag{35a}
$$

A TIA at its resistor-limited corner, $f_R = 1/(2\pi R_FC_{par})$ of Eq. (4), has the noise bandwidth of a single pole, $(\pi/2)f_R$. Setting this equal to $1/(2T)$ gives the equivalent measurement time $T = 1/(\pi f_R) = 2R_FC_{par}$, and Eq. (35a) becomes

$$
Q_R = 2\sqrt{k_BT\,C_{par}} ,
\tag{35b}
$$

independent of $R_F$ and of the bandwidth. At 25 °C this is 179, 253 and 358 electrons rms for 0.05, 0.1 and 0.2 pF. It equals the reset noise of a capacitor of $4C_{par}$, but it is spread over the whole measurement instead of being frozen at one instant, so no double sampling can remove it. Equation (35b) is the charge form of Eq. (36). The signal's own shot noise, $\sqrt{qIT}$ as a charge, equals $Q_R$ at $I = 4k_BT\,C_{par}/(qT)$. With $T = 1/(\pi f_R)$ that is $4\pi k_BT\,f_RC_{par}/q$, the $I_{\min,\mathrm{shot}}$ of Eq. (36) for the bandwidth $f_R$: 51 pA for 1 GΩ and 0.1 pF.

**The integrator's own noise.** An integrator is read by correlated double sampling. One sample of the output, $V_1$, is taken just after the reset switch opens, a second, $V_2$, after the time $T$, and the charge is $Q = C_{int}(V_2 - V_1)$. Five sources of noise remain.

- *Shot noise of the signal and the dark current.* The number of electrons collected in $T$, $IT/q$, follows Poisson statistics, so its standard deviation is its square root, and the noise charge is $\sqrt{qIT}$. This is the true limit, and the integrator can reach it.
- *The photodiode's own thermal noise.* At zero bias the diode's shunt resistance adds $2k_BT\,T/R_{sh}$ to the variance, which is Eq. (35a) with $R_{sh}$ in place of $R_F$. The integrator cannot remove it, because it belongs to the detector.
- *Reset noise.* By equipartition, $\tfrac12C_{int}\langle V^2\rangle = \tfrac12k_BT$, so the opening switch freezes on the capacitor a random charge with the standard deviation $\sqrt{k_BT\,C_{int}}$: 400 electrons for 1 pF. Double sampling removes it exactly. The first sample is $V_1 = V_{ref} + v_{kTC} + v_{inj}$, where $v_{inj}$ is the step caused by the charge that the switch injects (below). The second is $V_2 = V_1 + Q_{sig}/C_{int}$, plus the noise added during $T$. Their difference contains neither $v_{kTC}$ nor $v_{inj}$.
- *The amplifier's voltage noise on the node capacitance.* Referred to the input, $e_n$ acts as a charge $e_nC_T$, where $C_T$ is all the capacitance at the summing node, $C_{int}$ included. If each sample is read through a filter with the time constant $\tau$, whose noise bandwidth is $1/(4\tau)$, two independent samples give the variance of Eq. (35c) below.
- *Flicker noise and leakage.* Double sampling acts as a high-pass filter on the amplifier's $1/f$ noise, whose contribution therefore grows only slowly with $T$. The leakage of the open switch and the op amp's bias current are integrated with the signal, as an offset together with its shot noise, and both roughly double every 10 °C.

$$
\sigma_Q^2 = 2\,e_n^2C_T^2\cdot\frac{1}{4\tau} = \frac{e_n^2C_T^2}{2\tau}
\tag{35c}
$$

Equation (35c) is the term $e_n\,\omega C_T$ of a TIA in another form. In both circuits the amplifier's voltage noise enters as $e_nC_T$ times the square root of the readout bandwidth, and an integrator does not escape it. An integrator therefore removes exactly one term, the feedback resistor's.

**When the integrator wins.** Table 7.1 compares a 1-GΩ TIA with 0.1 pF, whose corner is 1.59 kHz, with an integrator that measures over the equivalent $T$ = 0.2 ms.

*Table 7.1. Noise charge per measurement, in electrons rms, of a 1-GΩ TIA with 0.1 pF and of a switched integrator, for $T$ = 0.2 ms at 25 °C and an amplifier with 3 nV/√Hz. The node capacitance is 32 pF for the 20-pF photodiode (20 pF, 11 pF of amplifier input and 1 pF of board) and 400 pF for the 380-pF photodiode. The amplifier's series noise, Eq. (35c) with $\tau = T/2$, is counted in both circuits. `integrator_vs_tia.py`.*

| Photodiode | Resistor, Eq. (35b) | Photodiode's own noise | Amplifier, Eq. (35c) | TIA, total | Integrator, total | Integrator better by |
|---|---|---|---|---|---|---|
| 20 pF, zero bias, 2 GΩ shunt resistance | 253 | 179 | 42 | 313 | 184 | 4.6 dB |
| 20 pF, reverse-biased, 1 pA of dark current | 253 | 35 | 42 | 259 | 55 | 13.4 dB |
| 380 pF, zero bias, 0.4 GΩ shunt resistance | 253 | 400 | 530 | 711 | 664 | 0.6 dB |

The integrator thus wins when four conditions hold.

1. The signal current lies below $I_{\min,\mathrm{shot}}$ of Eq. (36), where the resistor's noise exceeds the signal's own shot noise.
2. The photodiode's own parallel noise lies below the resistor's: a shunt resistance above $R_F$ at zero bias, or, under reverse bias, a dark current below $2k_BT/(qR_F)$, which is 51 pA for 1 GΩ. Cooling helps in both cases.
3. The node capacitance is small enough that Eq. (35c) stays below Eq. (35b). With $\tau = T/10$ = 20 µs, 3 nV/√Hz and 0.1 pF, this requires $C_T < 2\sqrt{2\tau\,k_BT\,C_{par}}/e_n$ = 86 pF.
4. A sampled output is acceptable.

On photodiodes of hundreds of picofarads both circuits are limited by $e_nC_T$, and only a quieter input device or less capacitance helps (Sections 5.8 and 6.7). An integrator also decouples the dynamic range from the noise. A TIA's $R_F$ is limited by the largest current, $R_F \leq V_{sw}/I_{\max}$ (Eq. (3)), and with it the resistor's noise floor. An integrator's full scale, a charge of $C_{int}V_{sw}$ per measurement, carries no resistor noise, and its range in current can be moved by choosing $T$. TI's comparison of the two architectures for a 100-pF photodiode with 100 nA of full-scale current shows the combined effect (SBOA034, p. 6, Table II) [A1]:

- **Optimized for noise**, a TIA with OPA124 (0.5 pF of feedback capacitance) reaches 3.2 kHz of signal bandwidth with 200 µV rms of noise and 94 dB of signal-to-noise ratio. A switched integrator with ACF2101 (100 pF) reaches 50 Hz with 35 µV rms and 109 dB.
- **Optimized for bandwidth**, a TIA with OPA627 reaches 3.2 kHz with 400 µV rms and 88 dB, and the integrator (1.5 pF) 3.35 kHz with 100 µV rms and 100 dB.

At the same bandwidth the integrator wins by 12 dB in that example. Without double sampling, the reset noise stays in the measurement, and an integrator beats a resistor-limited TIA only if $\sqrt{k_BT\,C_{int}} < 2\sqrt{k_BT\,C_{par}}$, that is, if $C_{int} < 4C_{par}$. For 0.1 pF that means less than 0.4 pF, which leaves little full-scale charge.

**Why image sensors read about one electron.** Image sensors show what an integrator can do when the capacitance is small. A floating diffusion of about 1 fF converts one electron into $q/C$ = 160 µV, and its reset noise, $\sqrt{k_BT\times1\ \mathrm{fF}}$ = 12.7 electrons, is removed by double sampling. The series noise of Eq. (35c) scales with $C_T$, so going from the 32 pF of a discrete photodiode's node to 1 fF divides it by 32,000. Even the small in-pixel transistor, which is far noisier than a precision op amp, then reaches about one electron. The pinned photodiode is what makes this possible. It transfers its whole charge to the floating diffusion, so the collecting area does not load the sense node. A discrete photodiode at an integrator's input has no such transfer: its tens of picofarads to nanofarads sit at the summing node, which is why condition 3 above decides the case for board designs.

**Charge injection by the reset switch.** A MOS switch that turns off releases its channel charge, $Q_{ch} = C_{ox}WL(V_{GS} - V_T)$, where $C_{ox}$ is the gate capacitance per unit area, $W$ and $L$ the channel width and length, and $V_{GS} - V_T$ the gate overdrive. Part of this charge, together with the charge that the falling gate couples through its overlap capacitance, lands on the summing node and from there on $C_{int}$. For an on-chip switch with a 7-nm oxide, $C_{ox} = \varepsilon_{ox}/t_{ox}$ = 3.9 × 8.854 pF/m ÷ 7 nm = 4.93 fF/µm². With $W/L$ = 1 µm/0.18 µm and 1.5 V of overdrive, $Q_{ch}$ = 4.93 fF/µm² × 0.18 µm² × 1.5 V = 1.33 fC, or 8,300 electrons. About half of it gives a step of 67 mV on 10 fF and of 0.67 V on 1 fF. For IVC102 the data sheet's offset, at most ±20 mV on 100 pF after 1 ms of zero input current, includes the switch's charge injection (p. 2, note 2), so the injected charge is at most 2 pC. The same 2 pC gives 0.02 V on 100 pF, 0.2 V on 10 pF, 2 V on 1 pF and 20 V on 0.1 pF.

For accuracy, charge injection is mostly harmless. The reset switch always opens at the same node voltages, the reference level, so the injected charge does not depend on the signal, and its random part is the thermal noise frozen at turn-off, the reset noise above. Both appear in $V_1$ and cancel in $V_2 - V_1$. Charge injection therefore costs headroom rather than accuracy, and it limits how small $C_{int}$, and so how high the gain, can be: on 1 pF, the 2 pC of IVC102's specification already takes a tenth of a ±10-V swing. Five reset effects remain after double sampling.

- *Signal-dependent injection.* Switches that open at a signal-dependent voltage, such as sampling switches, inject a signal-dependent charge; a reset switch does not.
- *Dielectric absorption of $C_{int}$.* After a reset the capacitor gives back part of its previous voltage, an error proportional to the previous measurement's signal (Section 8.3). C0G, PTFE or polystyrene capacitors keep it small.
- *Leakage of the open switch.* It adds charge, its shot noise and its temperature drift during the integration.
- *Timing.* The first sample must wait until the op amp has recovered from the injection step, and no clock edge may fall within the integration.
- *Dead time.* The reset interrupts the measurement unless two integrators alternate, as in DDC264.

Four measures reduce the injection itself. A dummy switch of half the size, driven by the opposite clock, forms its channel as the main switch's channel collapses, and so takes up the charge that the main switch releases on its side. Complementary NMOS and PMOS switches in parallel release charges of opposite sign. A slow gate edge lets the released charge flow back through the still-conducting channel to the low-impedance side, the op amp's output. Charge balancing avoids the reset altogether: a comparator triggers fixed charge packets from a reference capacitor whenever the integrator reaches a threshold, and the packets are counted. Each packet's injection is the same, so it becomes a gain error rather than an offset.

**Resetting with light.** Charge-sensitive preamplifiers for cooled semiconductor radiation detectors have long avoided both the feedback resistor and the reset switch. An opto-electronic feedback preamplifier for high-resolution nuclear spectroscopy was published in 1969 by Goulding, Walton and Malone [[A9]](https://doi.org/10.1016/0029-554X%2869%2990314-0), which was read here only by its title. Two later reports from the same laboratory describe the method and its limits [[A10]](https://doi.org/10.1109/TNS.1979.4329670), [[A11]](https://doi.org/10.1109/TNS.1982.4335922).

- *How it works.* The input JFET integrates the detector's charge on a feedback capacitor of about 0.5 pF, and the output rises in steps. When the output exceeds an upper threshold, an LED optically coupled to the FET is switched on (Figure 16). Its light raises the current through the FET's drain–gate junction to about 0.1–1 µA, many orders of magnitude above the detector's leakage, and that current drives the output back. At a lower threshold the LED is switched off again. The reset takes 1–10 µs. The detector, the feedback capacitor, the LED and the FET sit together in the cryostat, cooled nearly to the temperature of liquid nitrogen (Landis, Madden and Goulding, LBL-8135, p. 3) [A10].
- *Why it was used.* Between resets the reset path is the FET's own drain–gate junction, which is already part of the input. Nothing is added at the gate, neither a resistor nor a switch, so the input capacitance is the smallest possible (Landis, Cork, Madden and Goulding, LBL-13214, p. 1) [A11], and the charge-restoration path adds no noise at low frequency (LBL-8135, p. 5). Only the series noise of Eq. (35c) and the shot noise of the leakage remain. The measured squared resolution followed $1/\tau$ with the shaping time $\tau$, which is the signature of pure series noise, and reached 500 eV at very low energies with a 13-pF germanium detector and a 0.5-pF feedback capacitor (LBL-8135, p. 5). With 2.96 eV per electron–hole pair in germanium at 77 K, 500 eV of full width at half maximum is $500/(2.355\times2.96)$ ≈ 72 electrons rms.
- *What it costs.* The reports list five limits. Only one detector polarity can be used, because the reset current flows in one direction through the junction. After-effects of the light pulse can last hundreds of microseconds, so the dead time after a reset is much longer than the reset itself. They come from charge stored in parts of the FET, from light that some LEDs still emit after they are switched off, and from light reaching the detector's surface, to which germanium is particularly sensitive at the LED's long wavelengths. The LED's output, its coupling to the FET and the FET's sensitivity to light are poorly controlled, so the reset speed varies from unit to unit. LED drive currents of up to 100 mA cause crosstalk between the channels of a multi-detector system (LBL-13214, p. 1; LBL-8135, p. 4). Finally, a pulse that triggers a reset is lost, which makes the losses depend on the pulse size: with a 2-V reset range and 0.2-V pulses, every tenth pulse is lost. Delaying the reset until the triggering event has been processed removes this loss; a prompt reset lost 25% of the counts in a 5.1-MeV peak, a delayed one none (LBL-8135, pp. 3, 6–7).
- *What replaced it.* In a pulsed transistor reset, a low-leakage transistor with a small collector–base capacitance injects a reset current of about 50 µA into the input. It adds less than 0.4 pF, works with either detector polarity, needs only small switching currents and shows no slow after-effects (LBL-13214, pp. 1–2).

![Figure 16](figures/schem_optical_reset.png)

*Figure 16. Optical reset of a charge-sensitive preamplifier for a cooled semiconductor detector (LBL-8135, LBL-13214). The detector's charge is integrated on a feedback capacitor of about 0.5 pF around the input FET and the rest of the inverting amplifier. When the output crosses the upper threshold of the window comparator, the LED is switched on; its light raises the current of the FET's drain–gate junction to 0.1–1 µA, which discharges $C_F$ in 1–10 µs, until the lower threshold switches the LED off. Nothing is added at the gate between resets. Detector, FET, $C_F$ and LED sit together in the cryostat.*

For a photodiode integrator on a board, the lesson is the same as for the reset switch. What matters is what the reset element adds to the summing node between resets: its capacitance, its leakage and their noise. A photodiode front end could be reset optically in the same way, with a small auxiliary photodiode connected so that its photocurrent opposes the signal's and lit by an LED during the reset; its capacitance and dark current then join the summing node, and the after-effects and dead time come with it. With a photodiode of tens of picofarads or more, the few tenths of a picofarad that a low-leakage switch adds are negligible, and double sampling handles its injection, so a switch remains the practical choice.

**Parts.** A complete single-channel switched integrator is IVC102. It combines a FET-input op amp, three on-chip integrating capacitors of 10, 30 and 60 pF, and low-leakage FET switches for integration, hold and reset. Its data sheet presents it as a precision, lower-noise alternative to transimpedance circuits that need a very high feedback resistance (IVC102 data sheet, p. 1) [D31]. Its output is $V_O = -I_{IN}T_{INT}/C_{INT}$, so the gain is set by the integration time rather than by a resistor. With all three capacitors, 100 pF, and an integration time of 1 ms, a current of 1 pA gives $10^{-12}\ \mathrm{A}\times10^{-3}\ \mathrm{s}/10^{-10}\ \mathrm{F}$ = 10 µV at the output, and 100 nA gives 1 V. Its input bias current is 100 fA typical and 750 fA maximum, its nonlinearity is 0.005% typical, and its op amp has 10 nV/√Hz at 1 kHz and 2 MHz of gain–bandwidth (p. 2). The capacitors are specified only within 80–120 pF, which matches the gain error of +25%/−17% maximum (p. 2), so the gain must be calibrated. A reset settles to 0.01% in 6 µs (p. 2).

Integrators suit low-bandwidth, many-channel and pulsed measurements, and they are built into current-input ADCs. DDC264, for example, integrates 64 channels with a dual switched integrator per channel, 20-bit conversion, a noise of 6.3 ppm of full scale, and integration times from 160 µs to 1 s, "allowing currents from fAs to µAs to be continuously measured" (DDC264 data sheet, p. 1) [D27]. Their output is sampled, with the aliasing that implies.

**For a board design.** An integrator such as IVC102, or a current-input ADC such as DDC264, is worth its sampled output when the currents lie below a few tens of picoamperes, the photodiode is small or reverse-biased with little dark current, the measurement is sampled or frame-based anyway, and a wide dynamic range is wanted at low noise. A TIA remains the better choice for a continuous analog output, at currents above $I_{\min,\mathrm{shot}}$, and on large photodiodes, where $e_nC_T$ limits both circuits.

### 7.4 When to change the detector

The TIA reaches the shot-noise limit when the photocurrent exceeds $I_x$ of Eq. (2). Its largest usable feedback resistance is in turn limited by the bandwidth $B$ through the resistor's own pole, $R_F \leq 1/(2\pi BC_{par})$. Together these give the smallest photocurrent that a TIA can measure at the shot-noise limit in a bandwidth $B$, without equalization:

$$
I_{\min,\mathrm{shot}} = \frac{2k_BT}{q}\cdot2\pi BC_{par} = \frac{4\pi k_BT\,BC_{par}}{q} .
\tag{36}
$$

With $C_{par}$ = 0.1 pF this is 32 pA in 1 kHz, 32 nA in 1 MHz and 32 fA in 1 Hz, where it needs $R_F$ = 1.6 TΩ. Equalization over a factor $k$ (Section 3.5) lowers it by up to $k$, as long as the band stays below $f_e$. Below $I_{\min,\mathrm{shot}}$ the resistor's noise dominates, and the signal-to-noise ratio falls in proportion to the photocurrent instead of its square root. There a switched integrator helps if the measurement can be sampled (Section 7.3), and so does a detector with internal gain: an avalanche photodiode, a photomultiplier or a photon counter. With gain $M$ and excess noise factor $F$, the noise referred to the primary photocurrent is

$$
S_{i,\mathrm{prim}} = 2qI_{ph}F + \frac{S_{\mathrm{amp}}}{M^2} ,
\tag{37}
$$

so the gain divides the amplifier's and the resistor's noise by $M^2$ at the price of the factor $F$ on the shot noise. Internal gain pays when $S_{\mathrm{amp}}/M^2$ would otherwise exceed $2qI_{ph}F$, that is, below about $I_{\min,\mathrm{shot}}$ of Eq. (36). Hobbs makes the opposite point for currents above it. A well-designed front end often makes an expensive avalanche photodiode or photomultiplier unnecessary. In his case it was a bootstrapped cascode with a 2-MHz bandwidth, whose measured noise stayed within 0.5–1 dB of the shot noise up to 1 MHz (Hobbs, OPN April 2001, p. 45) [[A4]](https://doi.org/10.1364/OPN.12.4.000044).

---
