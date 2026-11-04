## 2. The noise of a high-gain TIA

Every comparison in this note is made on the noise referred to the photocurrent, so this chapter derives it first. Section 2.1 gives it exactly for the circuit of Figure 1, and the following sections take its terms one at a time: the floor that the feedback resistor and the photodiode set (Section 2.2), the amplifier's current noise (Section 2.3) and voltage noise (Section 2.4), the rule that matches the two to the summing node (Section 2.5), the signal's own shot noise (Section 2.6) and temperature (Section 2.7). Section 2.8 defines the figure of merit by which Chapters 4–6 compare the designs.

### 2.1 The input-referred noise of the circuit

This section derives the noise of the TIA referred to the photocurrent, for any feedback network, and shows that the loop gain drops out of it (Eq. (7)). The noise analysis treats the feedback element as a general two-port, not as a lumped $R_F\parallel C_F$, because Section 3.4 needs the same result for a resistor with distributed capacitance. The two-port is described by its short-circuit admittances. With $V_1$ the summing-node voltage and $V_2$ the output voltage, the current flowing from the summing node into the network is $I_1 = y_{11}V_1 + y_{12}V_2$. The network is passive and reciprocal, so $y_{12} = y_{21}$, and we write $y_f = -y_{21}$, the transfer admittance from the output to the summing node. For a lumped resistor and capacitor, $y_{11} = y_f = 1/R_F + j\omega C_F$. The photodiode and the amplifier's input capacitances form the source admittance $Y_s = 1/R_{sh} + j\omega C_T$, and the op amp has open-loop gain $A(s)$ with its voltage noise $e_n$ in series with the grounded non-inverting input.

Kirchhoff's current law at the summing node, with a current $I_{in}$ injected into it, reads $I_{in} = Y_sV_1 + I_1 = Y_nV_1 - y_fV_2$, where $Y_n = Y_s + y_{11}$ is the total admittance of the node with the output grounded. The op amp sets $V_2 = A\,(e_n - V_1)$.

*The signal.* With $e_n$ = 0, $V_1 = -V_2/A$, and the node equation gives $I_{in} = -V_2\,(y_f + Y_n/A)$. The transimpedance is therefore

$$
Z_T = \frac{V_2}{I_{in}} = -\frac{1}{y_f + Y_n/A}.
\tag{6}
$$

Where the loop gain $T = Ay_f/Y_n$ is large, $Z_T \to -1/y_f$, which is $-R_F/(1 + j\omega R_FC_F)$ for the lumped network.

*The voltage noise.* With $I_{in}$ = 0, the node equation gives $V_1 = y_fV_2/Y_n$, and the op amp gives $V_2 = A\,(e_n - y_fV_2/Y_n)$, so $V_2 = Ae_n/(1 + Ay_f/Y_n)$. Dividing this output by $|Z_T|$ refers it to the input as a current:

$$
i_{e} = \frac{Ae_n}{1 + Ay_f/Y_n}\left(y_f + \frac{Y_n}{A}\right) = e_n\,Y_n\,\frac{Ay_f + Y_n}{Y_n + Ay_f} = e_n\,Y_n .
\tag{7}
$$

The result is exact: the loop gain cancels completely, so the input-referred voltage-noise current is $e_n$ times the admittance of the summing node. The loop gain decides how far up in frequency the transimpedance keeps its value, that is the bandwidth, but not the input-referred noise density.

*The other sources.* Every other noise source is a current at the summing node and enters as it is. This holds for the op amp's input current noise $i_n$, for the photodiode's own noise, and for the signal's shot noise. It also holds for the thermal noise of the feedback network. A passive network at temperature $T$ has a short-circuit noise current at its port 1 of spectral density $4k_BT\,\mathrm{Re}\{y_{11}\}$; its port-2 noise current flows into the op amp's output, a voltage source, and has no effect. The input-referred noise current density is therefore

$$
S_i(f) = 4k_BT\,\mathrm{Re}\{y_{11}\} + \frac{4k_BT}{R_{sh}} + 2q\,(I_{ph} + I_D) + i_n^2(f) + e_n^2(f)\,\bigl|Y_s + y_{11}\bigr|^2 ,
\tag{8}
$$

in A²/Hz. The second term is the photodiode's noise at zero bias, and the dark-current term replaces it under reverse bias. For the lumped network $\mathrm{Re}\{y_{11}\} = 1/R_F$, and the last term becomes

$$
e_n^2\,|Y_n|^2 = e_n^2\left[\left(\frac{1}{R_F} + \frac{1}{R_{sh}}\right)^2 + \bigl(2\pi f\,(C_T + C_F)\bigr)^2\right].
\tag{9}
$$

With $R_{sh}\to\infty$ and $I_D$ = 0 this is the companion note's Eq. (19), derived there for its own circuit. The rest of this chapter takes Eq. (8) term by term.

### 2.2 The floor set by the feedback resistor and the photodiode

The first two terms of Eq. (8) are the floor that no amplifier can remove:

$$
S_{\mathrm{floor}} = \frac{4k_BT}{R_F} + \frac{4k_BT}{R_{sh}} = \frac{4k_BT}{R_F\parallel R_{sh}} .
\tag{10}
$$

If $R_{sh}\gg R_F$, the floor is the resistor's. If $R_{sh}$ is comparable to or below $R_F$, it is the photodiode's, and raising $R_F$ further hardly lowers it. For the 1-mm extended-InGaAs diode of Table 1, $R_{sh}$ = 14 kΩ gives a Johnson noise of $\sqrt{1.6466\times10^{-20}/1.4\times10^{4}}$ = 1.08 pA/√Hz. With $R_F$ = 1 MΩ the floor is $\sqrt{1.6466\times10^{-20}\,(10^{-6} + 1/1.4\times10^{4})}$ = 1.09 pA/√Hz, so the resistor contributes 1.4% of the power. A resistor of ten times $R_{sh}$ already brings the floor within $10\log_{10}(1.1)$ = 0.41 dB of the diode's own; beyond that, a larger $R_F$ buys almost nothing in noise and, as Sections 3.3 and 8.1 show, costs bandwidth and offset. The photodiode's datasheet confirms this reading of the floor. For the S1336-18BK, the Johnson noise of its typical 2-GΩ shunt resistance is $\sqrt{1.6466\times10^{-20}/2\times10^{9}}$ = 2.87 fA/√Hz, which, divided by its peak responsivity of 0.5 A/W, gives 5.7 fW/√Hz. That is exactly the noise-equivalent power the datasheet lists for it, $5.7\times10^{-15}\ \mathrm{W/Hz^{1/2}}$ (S1336 series, p. 1) [P1]. For the S1336-8BK, 0.4 GΩ gives 6.42 fA/√Hz and 12.8 fW/√Hz, against the listed $1.3\times10^{-14}\ \mathrm{W/Hz^{1/2}}$. The datasheet's noise-equivalent power is thus the shunt resistance's Johnson noise, which supports reading $R_{sh}$ as the diode's noise source at zero bias.

Under reverse bias the diode contributes the shot noise of its dark current, $2qI_D$, instead. The large-area S3584-08 at 70 V, with 10 nA typical, contributes 57 fA/√Hz (Section 1.2), which exceeds the floor of any $R_F$ above 5 MΩ.

### 2.3 The amplifier's current noise

The current noise of a FET-input op amp is, at low frequency, the shot noise of its gate leakage current, $i_n = \sqrt{2qI_B}$. Like any current at the summing node, it competes with the resistor's Johnson noise, and it dominates above the critical resistance

$$
R_{F,\mathrm{crit}} = \frac{4k_BT}{i_n^2} \quad\left(= \frac{2k_BT}{qI_B} = \frac{51.4\ \mathrm{mV}}{I_B}\ \text{for pure shot noise}\right).
\tag{11}
$$

The second form is Eq. (2) with the bias current in place of the photocurrent: the gate current is simply a dark current that the amplifier adds. Table A.2 lists $R_{F,\mathrm{crit}}$ for every part from its datasheet value of $i_n$, and the classes separate cleanly.

- **CMOS electrometers.** ADA4530-1 and OPA928 both specify 0.07 fA/√Hz at 0.1 Hz (ADA4530-1, p. 4; OPA928, p. 4) [D1, D2], so $R_{F,\mathrm{crit}} = 1.6466\times10^{-20}/(7\times10^{-17})^2$ = 3.4 TΩ, far beyond the range of this note.
- **Precision JFET and CMOS parts.** OPA140 and OPA145 specify 0.8 fA/√Hz, OPA320 0.6, OPA828 1.2, OPA827 2.2 and ADA4625-1 4.5 fA/√Hz, all at 1 kHz [D9, D10, D13, D7, D8, D6]. Their critical resistances run from 813 MΩ (ADA4625-1) to 46 GΩ (OPA320).
- **A bias-current-cancelled electrometer.** LMP7721 has a typical bias current of only 3 fA but a current noise of 0.01 pA/√Hz = 10 fA/√Hz at 1 kHz (LMP7721, pp. 6–7) [D3]. That is about 320 times the shot noise of 3 fA, which is 0.031 fA/√Hz. The data sheet attributes the low bias current to "input bias current cancellation amplifier circuitry" (p. 1) [D3]. A cancellation subtracts one DC current from another, but the noises of the two add, so a cancelled bias current says nothing about the current noise. Its $R_{F,\mathrm{crit}}$ is 165 MΩ, and at 1 GΩ its current noise is 7 dB above the floor (Table A.3).
- **A general-purpose CMOS part.** LMC662's data sheet gives 4 fA/√Hz at 1 kHz (Rev. D, p. 6) [D5]. Its revision history, however, states that this value replaced the earlier 0.0002 pA/√Hz, that is 0.2 fA/√Hz, "to align with modern noise test setup" (p. 23). The 4 fA/√Hz therefore describes the test setup rather than the part, and the model uses the earlier 0.2 fA/√Hz. Even that is conservative. A CMOS input without bias-current cancellation draws only the leakage currents $I_1$ and $I_2$ of its two input-protection diodes. They flow in opposite directions, so the bias current is their difference. Each, however, is a stream of independent charges with its own shot noise, and the noise powers add: $i_n = \sqrt{2q(|I_1| + |I_2|)}$. For LMC662's typical bias current of 2 fA (p. 6) this is $\sqrt{2\times1.602\times10^{-19}\ \mathrm{C}\times2\ \mathrm{fA}}$ = 0.025 fA/√Hz if one diode dominates, and 0.057 fA/√Hz if the two leak 10 fA together. With 0.2 fA/√Hz, $R_{F,\mathrm{crit}}$ is 412 GΩ, so LMC662's current noise is negligible at every gain of this note.
- **Low-noise CMOS audio-class parts.** OPA1656 specifies 6 fA/√Hz and OPA2156 19 fA/√Hz at 1 kHz [D11, D12], giving 457 MΩ and 46 MΩ.
- **Zero-drift and auto-zero parts.** OPA388 specifies 100 fA/√Hz at 1 kHz and OPA381 20 fA/√Hz at 10 kHz [D15, D14], giving 1.65 MΩ and 41 MΩ. A plausible mechanism is the charge that the input switches inject at every clock cycle, but the datasheets give only the values.
- **Bipolar parts.** OPA211 specifies 1.7 pA/√Hz at 1 kHz [D17], so $R_{F,\mathrm{crit}}$ = 5.7 kΩ: a bipolar input is unsuitable from 100 kΩ up, except where the photodiode's own shunt resistance is a few kilohms (Section 6.6). At 10 kΩ OPA211's current noise adds $10\log_{10}(1 + R_F/R_{F,\mathrm{crit}})$ = $10\log_{10}(1 + 1.75)$ = 4.4 dB to the resistor's noise, and the low voltage noise of bipolar parts can outweigh their current noise in wide bands (Section 6.9).

*Frequency dependence.* The datasheet current noise of FET-input parts rises at high frequency. For LTC6268-10 it is 7 fA/√Hz at 100 kHz and about 0.18 pA/√Hz at 1 MHz and 0.89 pA/√Hz at 10 MHz; for OPA818 it is 3 fA/√Hz at 10 kHz and 145 fA/√Hz at 1 MHz, from a curve its datasheet labels as simulated. These values are taken from the companion note's records of the two datasheets (its data/specs files) [D18, D20]. Part of this rise is the input transistors' channel noise coupled through their gate capacitance, which Eq. (8) already counts in $e_n\,\omega C_T$, since $C_T$ includes $C_{CM}$ and $C_{DIFF}$. The model adds the datasheet curve as well, which may count that part twice and therefore errs on the pessimistic side. For parts without a curve, $i_n$ is held at its specified value. Below the first point of a curve that starts above 1 kHz and rises, as for the wideband parts, the model continues the rise downwards with the slope from the first point to the first point at least a decade above it. It adds in quadrature the shot noise of the typical bias current, $\sqrt{2qI_{B,\mathrm{typ}}}$, because the shot noise of the gate current is the floor below which the current noise of a FET input cannot fall. Holding the first point flat down to DC instead would overstate the noise at high gain. For OPA818 the floor is 1.1 fA/√Hz, against the 3 fA/√Hz specified at 10 kHz, and at 1 GΩ it lowers the excess noise from 1.5 to 0.5 dB (Section 9.8). The rise matters only at 100 kΩ to 10 MΩ with megahertz bandwidths. OPA818's 145 fA/√Hz at 1 MHz, for example, exceeds the 128 fA/√Hz of a 1-MΩ resistor.

*Temperature.* The gate current of a FET-input op amp "doubles for every 10 °C increase in temperature, while the bias current of bipolar op amps decreases" (Hamamatsu technical note KSPD9001E04, p. 10) [P5]. A part whose current noise is shot noise therefore gains a factor $\sqrt2$ in $i_n$ per 10 °C, and its $R_{F,\mathrm{crit}}$ falls by a factor of 2 per 10 °C, or 64 from 25 °C to 85 °C. Chapter 8 uses the specified maxima at 85 °C for the DC errors.

### 2.4 The amplifier's voltage noise acting on the summing node

The loop holds the summing node at the amplifier's voltage noise $e_n$, so $e_n$ drives a current through everything connected to the node: the resistances $R_F$ and $R_{sh}$, and the whole node capacitance $C_T + C_F$ (Eq. (7)). It is the amplifier term that grows with the photodiode's capacitance and with frequency, and Chapter 4 shows where it dominates. Equation (9) has two parts, and they dominate in different places.

*At low frequency* the voltage noise sees the conductance $1/R_F + 1/R_{sh}$. Compared with the floor of Eq. (10), its contribution is $e_n^2/(R_F\parallel R_{sh})^2$ against $4k_BT/(R_F\parallel R_{sh})$. The voltage noise therefore matters at low frequency only if it exceeds the Johnson voltage noise of the parallel resistance,

$$
e_{n,\mathrm{crit}} = \sqrt{4k_BT\,(R_F\parallel R_{sh})} .
\tag{12}
$$

For a parallel resistance of 100 kΩ or more this is at least $\sqrt{1.6466\times10^{-20}\times10^{5}}$ = 40.6 nV/√Hz, larger than the voltage noise of every part in this survey above 100 Hz. The low-frequency term matters only for diodes with low shunt resistance. For the 14-kΩ extended-InGaAs diode, $e_{n,\mathrm{crit}}$ = 15.2 nV/√Hz, so an amplifier with more voltage noise than that adds more than the diode's own noise. It also matters in the flicker region of CMOS parts: ADA4530-1 has 80 nV/√Hz at 10 Hz (p. 4) [D1].

*At high frequency* the voltage noise sees the node capacitance $C_T + C_F$, and its contribution grows as $f^2$ in power. It equals the floor at

$$
f_e = \frac{\sqrt{4k_BT/(R_F\parallel R_{sh})}}{2\pi\,e_n\,(C_T + C_F)} .
\tag{13}
$$

For a 1-MΩ TIA with OPA1656 (2.9 nV/√Hz at 10 kHz, 11 pF of input capacitance [D11]) on the 20-pF S1336-18BK, with 1 pF of board capacitance and about 0.3 pF of feedback capacitance, $C_T + C_F$ = 32.3 pF and $f_e$ = 128.3 fA/√Hz ÷ (2π × 2.9 nV/√Hz × 32.3 pF) = 218 kHz. On the 380-pF S1336-8BK with ADA4625-1 (3.3 nV/√Hz, 19.9 pF [D6]), $C_T + C_F$ ≈ 402 pF and $f_e$ = 15 kHz at the same gain. Above $f_e$ the voltage noise dominates, and below it the floor does. Chapter 4 maps $f_e$ against the bandwidth for every gain.

*Flicker noise* enters both parts of Eq. (9). In the capacitive part, a $1/f$ density in $e_n^2$ times the $f^2$ of the capacitance still grows as $f$. Flicker noise therefore matters only when $f_e$ falls inside the flicker region. That happens for CMOS parts at the highest gains: the corner of ADA4530-1 is near 300 Hz (80 nV/√Hz at 10 Hz against 14 nV/√Hz at 10 kHz), and a 1-GΩ TIA on a small photodiode has its $f_e$ between 1 and 6 kHz (Section 3.5).

### 2.5 Matching the amplifier to the node impedance

Neither the voltage noise nor the current noise of an amplifier says on its own whether the part suits a given gain, because the node weighs the two differently at each gain and frequency. Their ratio does, and it is the quickest way to place an amplifier class in the gain range. The two amplifier terms of Eq. (8), $i_n^2$ and $e_n^2|Y_n|^2$, are equal when the impedance of the node equals

$$
R_{opt} = \frac{e_n}{i_n} ,
\tag{14}
$$

the familiar optimum source resistance. An amplifier is well matched to a TIA when $R_{opt}$ lies near the node impedance $1/|Y_n|$ over the band, and badly matched when it lies far from it on either side. For a bipolar OPA211, $R_{opt}$ = 1.1 nV ÷ 1.7 pA = 650 Ω. For ADA4625-1 it is 3.3 nV ÷ 4.5 fA = 0.73 MΩ, for OPA140 5.1 nV ÷ 0.8 fA = 6.4 MΩ, and for ADA4530-1 about 16 nV ÷ 0.07 fA = 230 GΩ. The node impedance of a TIA is at most $R_F\parallel R_{sh}$ and falls as $1/(2\pi fC_T)$ above the node's corner. At 1 GΩ with the 20-pF diode, and 29–38 pF in total at the node, it is 2.6–3.4 MΩ at the 1.6-kHz band edge, which suits OPA140; an electrometer's $R_{opt}$ is far above it, so its larger voltage noise costs more than its tiny current noise saves (Section 6.5). This is the single most useful rule for choosing an amplifier class, and Chapter 6 applies it decade by decade.

### 2.6 The signal's shot noise and the noise-equivalent power

The signal's own shot noise is the third term of Eq. (8). Above $I_x$ of Eq. (2) it dominates, and the measurement is shot-noise limited. In the regime of this note signals are usually near or below $I_x$, which is why $R_F$ is chosen large. The noise-equivalent power of the receiver is $\sqrt{S_i}/\mathcal{R}$, with $\mathcal{R}$ the responsivity in A/W. A 1-GΩ TIA with a resistor-limited floor of 4.06 fA/√Hz and a 0.5-A/W silicon diode reaches 8.1 fW/√Hz, the same order as the diode's own 5.7 fW/√Hz of Section 2.2. Below that power level the photodiode and TIA cannot do better, whatever the amplifier; Section 7.4 discusses detectors with internal gain.

### 2.7 Temperature

The floor and the amplifier terms change with temperature at very different rates. The resistor's Johnson noise rises only as $\sqrt{T}$, by 9.6% from 25 °C to 85 °C. The FET gate current doubles every 10 °C, so

$$
I_B(T_A) = I_B(25\ ^\circ\mathrm{C})\cdot 2^{(T_A - 25\ ^\circ\mathrm{C})/10\ ^\circ\mathrm{C}} ,
\tag{15}
$$

a factor of 64 at 85 °C. The photodiode's shunt resistance halves every 5–10 °C (Section 1.2), a factor of 64 to 4000. A design that is resistor-limited at 25 °C can therefore be limited by the photodiode or by the amplifier's gate current at 85 °C. For the S1336-18BK, the datasheet's dark-current coefficient of 1.15 per °C, if it holds over the whole 60 °C, takes its typical 2 GΩ to $2\ \mathrm{G\Omega}/1.15^{60}$ = 0.46 MΩ. With $4k_BT = 1.978\times10^{-20}$ J at 85 °C, the diode's own noise is then $\sqrt{1.978\times10^{-20}/4.6\times10^{5}}$ = 210 fA/√Hz, above the floor of any $R_F$ larger than about 0.5 MΩ. The coefficient is specified as a single number (p. 1) [P1], so this extrapolation is an estimate. It shows that weak-light measurements at high gain need the photodiode kept cool, not only the amplifier.

### 2.8 The figure of merit

The designs of Chapters 4–6 are compared by their excess noise over the floor that no amplifier can remove, integrated over the band of each design:

$$
\Delta N = 10\log_{10}\frac{\int_{f_1}^{f_{-3\,\mathrm{dB}}} S_i(f)\,df}{\int_{f_1}^{f_{-3\,\mathrm{dB}}} \bigl(4k_BT\,\mathrm{Re}\{y_{11}\} + 4k_BT/R_{sh}\bigr)\,df} ,
\tag{16}
$$

with $f_1$ = 1 Hz and $f_{-3\,\mathrm{dB}}$ the −3 dB bandwidth of the design. $\Delta N$ = 0 dB means that the amplifier adds nothing, and 3 dB that it doubles the noise power. The companion note uses the same form with only $R_F$ in the denominator (its Section 3.6). Here the photodiode's shunt noise is included because, at the highest gains, it is part of the floor, and an amplifier should not be blamed for it.

---
