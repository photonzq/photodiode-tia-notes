## 1. The circuit, the photodiode, and what each gain decade fixes

### 1.1 The circuit and the symbols

The circuit is the ordinary inverting TIA. The photodiode connects the op amp's inverting input, the summing node, to ground, either directly (zero bias, the photovoltaic mode) or through a bias voltage (reverse bias, the photoconductive mode). The feedback resistor $R_F$ runs from the output back to the summing node, and the non-inverting input is grounded. The circuit holds the summing node at virtual ground, so the photocurrent $I_{ph}$ flows through $R_F$ and the output is $V_{out} = -I_{ph}R_F$. Figure 1 shows the circuit with every element that the analysis of this note uses.

The symbols used throughout are these.

- $I_{ph}$ is the photocurrent, $C_D$ the photodiode's capacitance, $R_{sh}$ its shunt resistance and $I_D$ its dark current under reverse bias. The series resistance of the diode, tens of ohms, is negligible at the frequencies of this note.
- $e_n$ and $i_n$ are the op amp's input voltage- and current-noise densities, $C_{CM}$ and $C_{DIFF}$ its common-mode and differential input capacitances, $GBW$ its gain–bandwidth product, $I_B$ its input bias current and $V_{OS}$ its offset voltage.
- $C_T = C_D + C_{CM} + C_{DIFF} + C_{PCB}$ is the total capacitance from the summing node to AC ground, with $C_{PCB}$ that of the pads and traces. With the non-inverting input grounded, the differential capacitance also connects the node to ground, so it adds to $C_T$.
- $C_F$ is the total capacitance across $R_F$: the resistor's own parasitic capacitance $C_{par}$ plus any capacitor added on purpose.
- $T$ = 298.15 K (25 °C), the temperature of the datasheet tables, so $4k_BT = 1.6466\times10^{-20}$ J and $k_BT/q = 25.69$ mV, with $k_B$ Boltzmann's constant and $q$ the electron charge.

![Figure 1](figures/schem_tia_noise.png)

*Figure 1. The inverting TIA of this note with every element of Eq. (8). The photodiode delivers the photocurrent $I_{ph}$ into the summing node; its cathode sits at ground (zero bias) or at a reverse bias $V_B$. Grey elements are the capacitances and the shunt resistance that the circuit cannot avoid: the photodiode's $C_D$ and $R_{sh}$, the board's $C_{PCB}$, the amplifier's common-mode input capacitance $C_{CM}$ from its inverting input to ground, its differential input capacitance $C_{DIFF}$ between its two inputs, and the feedback capacitance $C_F$, the resistor's own $C_{par}$ plus any capacitor $C_{add}$ placed on purpose. $C_{DIFF}$ ends on the non-inverting input, which is grounded, so it connects the summing node to ground just as $C_{CM}$ does; that is why the two add in $C_T$. The noise sources are purple: $i_R$, the Johnson noise of $R_F$; $i_{PD}$, the photodiode's thermal noise $4k_BT/R_{sh}$ together with the shot noise $2q\,(I_{ph} + I_D)$; the amplifier's current noise $i_n$; and its voltage noise $e_n$, drawn between the grounded non-inverting pin and the amplifier. Through the loop the summing node follows $e_n$, so $e_n$ drives a current through every capacitance at the node, $C_{DIFF}$ included (Eq. (9)). All but $e_n$ are currents at the summing node and are referred to the input unchanged (Section 2.1).*

These are the conventions of the companion note (its Section 1), which the present note keeps wherever the two overlap.

### 1.2 The photodiode as the amplifier sees it

The amplifier does not care what the photodiode is made of. It sees a current source $I_{ph}$ in parallel with a capacitance $C_D$ and a resistance $R_{sh}$, which is the equivalent circuit Hamamatsu gives for its silicon photodiodes, together with a series resistance (KSPD9001E04, p. 2) [P5]. The material enters only through the values of $C_D$ and $R_{sh}$, their dependence on bias and temperature, and the dark current. Hamamatsu obtains $R_{sh}$ from the dark current measured at a reverse bias of 10 mV (KSPD9001E04, p. 4) [P5]. It is therefore the slope resistance of the diode near zero bias, and at zero bias its Johnson noise $4k_BT/R_{sh}$ is the diode's own noise in the dark.

Table 1 collects examples from four Hamamatsu datasheets: small and medium silicon photodiodes, a large-area silicon PIN diode, InGaAs diodes from 0.3 to 5 mm, and InGaAs diodes extended to 2.6 µm. They span the whole range a high-gain TIA meets.

*Table 1. Capacitance and shunt resistance of example photodiodes at 25 °C unless stated. $C_t$ is the terminal capacitance at the stated reverse bias $V_R$; $R_{sh}$ is measured at $V_R$ = 10 mV. The last column is the frequency $1/(2\pi R_{sh}C_t)$ above which the capacitance, not the shunt resistance, sets the photodiode's admittance (typical values). Sources: S1336 series KSPD1022E09, p. 1 [P1]; S3204/S3584 series KPIN1051E10, p. 1 and the capacitance curve on p. 3, read by eye [P4]; G12180 series KIRD1121E11, p. 1 (diameters) and p. 3, with footnote \*6 for the bias of the three smallest [P2]; G12183 series KIRD1119E10, pp. 1 and 3 [P3].*

| Photodiode | Material, size | $C_t$ (typ) | Bias for $C_t$ | $R_{sh}$ min / typ | $1/(2\pi R_{sh}C_t)$ |
|---|---|---|---|---|---|
| S1336-18BK | Si, 1.1 × 1.1 mm | 20 pF | 0 V, 10 kHz | 0.5 / 2 GΩ | 4.0 Hz |
| S1336-5BK | Si, 2.4 × 2.4 mm | 65 pF | 0 V, 10 kHz | 0.3 / 1 GΩ | 2.4 Hz |
| S1336-44BK | Si, 3.6 × 3.6 mm | 150 pF | 0 V, 10 kHz | 0.2 / 0.6 GΩ | 1.8 Hz |
| S1336-8BK | Si, 5.8 × 5.8 mm | 380 pF | 0 V, 10 kHz | 0.1 / 0.4 GΩ | 1.0 Hz |
| S3204-08 | Si PIN, 18 × 18 mm | about 1.7 nF; 130 pF | 0.1 V; 70 V | not given; dark current 6 nA typ at 70 V | – |
| S3584-08 | Si PIN, 28 × 28 mm | about 3.7 nF; 300 pF | 0.1 V; 70 V | not given; dark current 10 nA typ at 70 V | – |
| G12180-003A | InGaAs, ⌀0.3 mm | 5 pF | 5 V, 1 MHz | 200 / 1000 MΩ | 32 Hz |
| G12180-010A | InGaAs, ⌀1 mm | 55 pF | 5 V, 1 MHz | 25 / 125 MΩ | 23 Hz |
| G12180-030A | InGaAs, ⌀3 mm | 450 pF | 1 V, 1 MHz | 4 / 20 MΩ | 18 Hz |
| G12180-050A | InGaAs, ⌀5 mm | 1000 pF | 1 V, 1 MHz | 1.3 / 6.5 MΩ | 24 Hz |
| G12180-250A | InGaAs, ⌀5 mm, cooled to −20 °C | 1000 pF | 1 V, 1 MHz | 90 / 500 MΩ | 0.3 Hz |
| G12183-003K | InGaAs to 2.6 µm, ⌀0.3 mm | 50 pF | 0 V, 1 MHz | 20 / 100 kΩ | 32 kHz |
| G12183-010K | InGaAs to 2.6 µm, ⌀1 mm | 500 pF | 0 V, 1 MHz | 2.8 / 14 kΩ | 23 kHz |
| G12183-030K | InGaAs to 2.6 µm, ⌀3 mm | 4 nF | 0 V, 1 MHz | 0.25 / 1.4 kΩ | 28 kHz |
| G12183-210K | InGaAs to 2.6 µm, ⌀1 mm, cooled to −20 °C | 400 pF | 0 V, 1 MHz | 55 / 280 kΩ | 1.4 kHz |

Four points follow from the table.

- **The capacitance grows with area, and the shunt resistance falls with it.** Within one series the product $R_{sh}C_t$ is roughly constant. In the S1336 series it is 40 ms for the smallest and 152 ms for the largest diode, and in the G12180 series 5–9 ms. The corner $1/(2\pi R_{sh}C_t)$ in the last column is therefore a property of the material and its temperature rather than of the size.
- **The material sets the shunt resistance by orders of magnitude.** Silicon diodes have gigaohms, InGaAs diodes megaohms to a gigaohm, and InGaAs extended to 2.6 µm only kilohms to 100 kΩ. For the extended diodes the corner lies at 23–32 kHz, so their admittance is resistive over the whole band of a high-gain TIA. Germanium diodes, not tabulated here because no datasheet was read (Appendix C, item 1), fall in the same low-resistance class.
- **Reverse bias trades capacitance for dark current.** The 28 × 28 mm S3584-08 falls from about 3.7 nF at 0.1 V to 300 pF at 70 V, read from its capacitance curve, but then carries 10 nA of dark current (typical), whose shot noise $\sqrt{2qI_D}$ = 57 fA/√Hz exceeds the Johnson noise of a 10-MΩ resistor (40.6 fA/√Hz).
- **Cooling raises the shunt resistance.** Cooling the 5-mm InGaAs diode to −20 °C raises its typical shunt resistance from 6.5 MΩ to 500 MΩ, a factor of 77, and cooling the 1-mm extended diode raises it from 14 kΩ to 280 kΩ, a factor of 20.

**Temperature.** The shunt resistance falls fast with temperature, at a rate that depends on the diode. For the S1336 series the dark current at 10 mV rises by a factor of 1.15 per °C (S1336 series, p. 1) [P1]. Since $R_{sh}$ is that voltage divided by that current, it halves every $\ln 2/\ln 1.15$ = 4.96 °C. For the G12180 series the curves of shunt resistance against temperature are straight lines on a log scale, about six decades from −40 °C to +100 °C (G12180 series, p. 5, read by eye) [P2]. That is a decade per 23–25 °C, or a halving every 7–8 °C. Analog Devices states, for the large-area photodiodes it has in mind, that the shunt resistance halves every 10 °C (ADA4530-1 data sheet Rev. C, p. 44) [D1]. A design that must work at 85 °C should therefore expect $R_{sh}$ to be $2^{60/5}\approx4000$ times smaller than at 25 °C for a diode like the S1336, and $2^{60/10} = 64$ times smaller for one that follows the 10-°C rule.

### 1.3 What each gain decade fixes before any amplifier is chosen

Four quantities depend on $R_F$ alone, and they frame everything that follows.

**The noise floor.** The feedback resistor's Johnson noise is a current of density

$$
i_R = \sqrt{\frac{4k_BT}{R_F}}
\tag{1}
$$

at the summing node, where it adds to the signal like a photocurrent. No amplifier can reduce it. For $R_F$ = 1 MΩ, $i_R = \sqrt{1.6466\times10^{-20}\ \mathrm{J}/10^{6}\ \Omega}$ = 128 fA/√Hz.

**The shot-noise crossover.** A photocurrent $I$ carries shot noise of density $\sqrt{2qI}$. Setting $2qI$ equal to $4k_BT/R_F$ gives the current above which the light's own noise exceeds the resistor's:

$$
I_x = \frac{2k_BT}{qR_F} = \frac{51.4\ \mathrm{mV}}{R_F}.
\tag{2}
$$

At 25 °C, $2k_BT/q = 2\times25.69$ mV = 51.4 mV, so $I_x$ is 514 nA at 100 kΩ and 51.4 pA at 1 GΩ. Above $I_x$ the measurement is limited by the light, and a larger $R_F$ gains nothing in noise. Below $I_x$ the resistor dominates, and a larger $R_F$ helps as $\sqrt{R_F}$ in signal-to-noise ratio, because the signal grows as $R_F$ and the resistor's noise voltage as $\sqrt{R_F}$.

**The full-scale current.** An output that can swing $V_{sw}$ carries at most

$$
I_{\max} = \frac{V_{sw}}{R_F}.
\tag{3}
$$

For a ±15-V part with 10 V of usable swing this is 100 µA at 100 kΩ and 10 nA at 1 GΩ. For a 5-V rail-to-rail part with about 2.4 V it is 24 µA and 2.4 nA. Any DC current, dark current or background light included, uses part of this range.

**The resistor's own bandwidth.** A resistor with parasitic capacitance $C_{par}$ across it has the pole

$$
f_R = \frac{1}{2\pi R_FC_{par}}.
\tag{4}
$$

A TIA cannot be faster than this unless its response is equalized afterwards (Section 3.5). The parasitic capacitance of a surface-mount resistor and its pads is of the order of 0.1 pF. Analog Devices uses 100 fF as "a practical minimum stray capacitance value" for resistors up to 1 TΩ (ADA4530-1 data sheet Rev. C, p. 39, Table 9) [D1]. Texas Instruments (TI) writes that the feedback resistor "has a parasitic shunt capacitance that may be as large as 0.2 pF" (SSZTBC4, p. 1) [A3], and older TI application notes, written for leaded resistors, use 0.4–0.5 pF (SBOA061, p. 2, Fig. 3; SBOA034, pp. 4 and 7) [A2, A1]. With 0.1 pF, $f_R$ is 15.9 MHz at 100 kΩ, 159 kHz at 10 MΩ and 1.59 kHz at 1 GΩ.

The four quantities combine into a result that holds at every gain. Over the bandwidth of the resistor's own pole, the Johnson noise of $R_F$ integrates to an output voltage of $\sqrt{k_BT/C_{par}}$, independent of $R_F$. The single-pole noise bandwidth is $(\pi/2)f_R = 1/(4R_FC_{par})$, so the output noise power is $(4k_BT/R_F)\,R_F^2/(4R_FC_{par}) = k_BT/C_{par}$. The DC dynamic range of a resistor-limited TIA over its full band is therefore

$$
DR = \frac{V_{sw}}{\sqrt{k_BT/C_{par}}},
\tag{5}
$$

the same for every $R_F$. With $C_{par}$ = 0.1 pF, $\sqrt{k_BT/C_{par}} = \sqrt{4.116\times10^{-21}\ \mathrm{J}/10^{-13}\ \mathrm{F}}$ = 203 µV rms, so a 10-V swing gives $10\ \mathrm{V}/203\ \mu\mathrm{V} = 4.9\times10^{4}$, or 93.8 dB. Choosing $R_F$ moves this window of about five decades along the current axis, together with the bandwidth, but does not widen it. A wider window needs gain ranging or a logarithmic amplifier (Chapter 7).

Table 2 evaluates Eqs. (1)–(4) for the five decades of this note, and Figure 2 plots the currents over a wider range of $R_F$, with the companion note's regime marked for comparison.

*Table 2. What each gain decade fixes: the resistor's noise floor, Eq. (1); the shot-noise crossover, Eq. (2); the full-scale current for 10 V and 2.4 V of swing, Eq. (3); and the resistor's own pole for 0.05, 0.1 and 0.2 pF, Eq. (4). 25 °C.*

| $R_F$ | $\sqrt{4k_BT/R_F}$ | $I_x = 2k_BT/(qR_F)$ | $I_{\max}$ at 10 V | $I_{\max}$ at 2.4 V | $f_R$ at 0.05 / 0.1 / 0.2 pF |
|---|---|---|---|---|---|
| 100 kΩ | 406 fA/√Hz | 514 nA | 100 µA | 24 µA | 31.8 / 15.9 / 7.96 MHz |
| 1 MΩ | 128 fA/√Hz | 51.4 nA | 10 µA | 2.4 µA | 3.18 / 1.59 / 0.796 MHz |
| 10 MΩ | 40.6 fA/√Hz | 5.14 nA | 1 µA | 240 nA | 318 / 159 / 79.6 kHz |
| 100 MΩ | 12.8 fA/√Hz | 514 pA | 100 nA | 24 nA | 31.8 / 15.9 / 7.96 kHz |
| 1 GΩ | 4.06 fA/√Hz | 51.4 pA | 10 nA | 2.4 nA | 3.18 / 1.59 / 0.796 kHz |

![Figure 2](figures/fig1_current_window.png)

*Figure 2. The current window of a TIA against its feedback resistance: the full-scale current for 10 V and 2.4 V of swing, Eq. (3); the current whose shot noise equals the resistor's Johnson noise, Eq. (2); and the resistor's Johnson noise in a 1-Hz band, Eq. (1). Above the red line the light's own noise dominates; between the red and green lines the resistor's noise does. The shaded band is the range of this note; the grey band at 1.5–2 kΩ is the companion note's.*

### 1.4 Conventions of the analysis

The analysis in Chapters 2–6 uses the following conventions. Appendix B lists them with the scripts that apply them.

- **Values.** Typical values at 25 °C from the datasheets, with each page cited in Table A.1. Maxima are used for the DC errors, which Chapter 8 also evaluates at 85 °C.
- **Feedback capacitance.** The resistor's own capacitance is $C_{par}$ = 0.1 pF unless stated, with 0.05 and 0.2 pF as the range. The board adds $C_{PCB}$ = 1 pF at the summing node. The total feedback capacitance $C_F$ is the smallest value at or above $C_{par}$ that keeps the transimpedance within 0.1 dB of maximally flat (Section 3.1). If $C_{par}$ alone already achieves that, the design is called resistor-limited.
- **Noise band and excess noise.** Noise is integrated over 1 Hz to the −3 dB bandwidth $f_{-3\,\mathrm{dB}}$ of each design. The excess noise $\Delta N$ is the ratio, in decibels, of the total to the floor that no amplifier can remove: the Johnson noise of $R_F$ plus the diode's own shunt noise, integrated over the same band (Eq. (16)).
- **Photodiode bias.** The photodiode is at zero bias unless stated, so it contributes $4k_BT/R_{sh}$ and no dark current.

---
