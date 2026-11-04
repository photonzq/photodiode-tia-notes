## 5. The amplifier classes

The 25 op amps of this survey fall into seven classes, and three discrete JFETs stand for an eighth, the composite front end. Four of the op amps, OPA858, OPA855, OPA955 and LMH6629, are taken from the companion note's records for the 10-kΩ and 100-kΩ decades (Section 6.9). Table 5 summarizes them by the quantities of Chapters 2 and 3, and Table A.1 gives every value with its datasheet page. The parts are examples of their classes, chosen from what was available as a datasheet, not an exhaustive market scan.

*Table 5. The amplifier classes by the quantities that matter for a high-gain TIA (typical values at 25 °C from Table A.1). $R_{F,\mathrm{crit}}$ is Eq. (11) and $R_{opt}$ Eq. (14), the latter with $e_n$ at 1 kHz or the nearest specified frequency. $A_0$ is the DC open-loop gain, which must exceed ten times the mid-band noise gain (Section 3.1). For the wideband bipolar parts, whose current noise rises below about 100 kHz, $i_n$, $R_{F,\mathrm{crit}}$ and $R_{opt}$ are given at the white level above 1 MHz.*

| Class | Examples | $e_n$, white (nV/√Hz) | $i_n$ (fA/√Hz) | $C_{CM}+C_{DIFF}$ (pF) | $I_B$ max, 25 °C / 85 °C | $GBW$ (MHz) | $A_0$ (dB) | $R_{F,\mathrm{crit}}$ | $R_{opt}$ |
|---|---|---|---|---|---|---|---|---|---|
| CMOS electrometer | ADA4530-1, OPA928, LMC6001A | 14–22 | 0.07–0.13 | 8–9 | 20–25 fA / 20 fA–2 pA | 1.3–2.5 | 126–143 (LMC6001A not given) | 1–3.4 TΩ | 0.17–0.23 TΩ |
| Cancelled-bias CMOS | LMP7721 | 6.5 | 10 | not given | 20 fA / 0.9 pA | 17 | 111 | 165 MΩ | 0.65 MΩ |
| Precision JFET | ADA4625-1, OPA828, OPA827, OPA140, OPA145 | 3.3–7 | 0.8–4.5 | 9–20 | 8–75 pA / 0.3–1 nA | 5.5–45 | 123–150 | 0.8–26 GΩ | 0.7–9 MΩ |
| Low-noise CMOS | OPA1656, OPA2156, OPA320 | 2.9–7 at 10 kHz | 0.6–19 | 9–11 | 0.9–40 pA / 0.05–1.5 nA | 20–53 | 132–154 | 0.05–46 GΩ | 0.2–14 MΩ |
| Wideband FET | OPA656, OPA657, OPA818, ADA4817-1, LTC6268-10, OPA858 | 2.2–6 | 1.3–16 at 0.1 MHz, rising | 0.55–5.2 | 20 fA–25 pA / 0.9 pA–5 nA | 230–5500 | 65–108 | 0.3–63 GΩ | 0.6–49 MΩ |
| Zero-drift and auto-zero CMOS | OPA388, OPA381 | 7; 70 at 10 kHz for OPA381 | 20–100 | 3.5–6.5 | 50–350 pA / 0.4–3 nA | 10–18 | 135–148 | 1.65–41 MΩ | 70 kΩ–3.5 MΩ |
| Bipolar | OPA211 | 1.1 | 1700 | 10 | 175 nA / 190 nA | 45 | 110 | 5.7 kΩ | 650 Ω |
| Wideband bipolar | OPA855, OPA955, LMH6629 | 0.69–0.99 | 550–2600 above 1 MHz | 0.8–5.7 | 5–23 µA / 10–37 µA | 4000–11000 | 76–78 | 2.4–54 kΩ | 0.27–1.4 kΩ |
| Discrete-JFET composite | IF3601, LSK170, BF862 + op amp | 0.35–0.9 | from gate current, ≤ 6–18 | 12–710 | 0.1–1 nA (maxima) | set by the design | set by the design | ≥ 51 MΩ at the maxima | – |

### 5.1 CMOS electrometers

Electrometer amplifiers are built for the smallest possible input current, and at the highest gains of this note that current, multiplied by $R_F$, is the DC error (Chapter 8). ADA4530-1 and OPA928 specify a bias current of 20 fA maximum at 25 °C, and ±20 fA maximum from −40 °C to 85 °C, at a relative humidity below 50% (ADA4530-1, p. 3; OPA928, p. 4) [D1, D2]. Both have an integrated guard buffer, whose output follows the input common-mode voltage within 100 µV (ADA4530-1) or 50 µV (OPA928) maximum, to drive a guard ring around the inputs (Chapter 8). Their current noise of 0.07 fA/√Hz is far below the Johnson noise of any resistor in this note. Their weakness is voltage noise: ADA4530-1 has 80 nV/√Hz at 10 Hz, 16 at 1 kHz and 14 at 10 kHz (p. 4), and OPA928 18 nV/√Hz at 100 Hz and 15 at 1 kHz (p. 4). With 8–9 pF of input capacitance and gain–bandwidth products of 2–2.5 MHz, they are slow and noisy on capacitance. LMC6001A, an older part, has 25 fA maximum, 22 nV/√Hz and 1.3 MHz (LMC6001, pp. 4, 9) [D4]. By Eq. (14) their optimum source resistance is hundreds of gigaohms, far above the node impedance of any TIA with a photodiode on it (Section 2.5). They belong where DC accuracy at the highest gains, over temperature and humidity, matters more than the last decibel of noise (Section 6.5).

### 5.2 A bias-current-cancelled CMOS amplifier

LMP7721 shows that a femtoampere bias current does not by itself mean low current noise. It reaches a typical bias current of 3 fA through cancellation circuitry (p. 1), with 20 fA maximum at 25 °C and 900 fA at 85 °C, 6.5 nV/√Hz at 1 kHz and 17 MHz (LMP7721, pp. 6–7) [D3]. Its current noise of 10 fA/√Hz is the trap described in Section 2.3: it exceeds the Johnson noise of any $R_F$ above 165 MΩ, and at 1 GΩ it adds 7.1 dB to the floor on the small photodiode (Table A.3a). The datasheet does not specify its input capacitance. LMP7721 suits 1–100 MΩ, where its low voltage noise and femtoampere bias current help, but not 1 GΩ.

### 5.3 Precision JFET op amps

The precision JFET op amps are the general-purpose class of this note: their voltage noise and current noise are both moderate, and their ratio matches the node impedances of most designs. ADA4625-1, OPA828, OPA827, OPA140 and OPA145 combine 3.3–7 nV/√Hz with 0.8–4.5 fA/√Hz and 9–20 pF [D6–D10]. Their bias currents are picoamperes at 25 °C (8–75 pA maximum) and double every 10 °C. At 85 °C the maxima are 0.3–1 nA, from the datasheet limits at 85 °C or interpolated between those at 25 °C and 125 °C (Appendix B.1). Their optimum source resistances of 0.7–9 MΩ (Eq. (14)) lie in the middle of the node impedances of this note. That is why they are the best general choice from 1 MΩ to 1 GΩ wherever DC accuracy at elevated temperature does not decide. Within the class:

- **ADA4625-1** has the lowest voltage noise, 5.5/3.6/3.3 nV/√Hz at 10/100/1000 Hz (p. 4) [D6], and suits large capacitances. Its 4.5 fA/√Hz limits it to about 800 MΩ.
- **OPA140 and OPA145** have the lowest current noise, 0.8 fA/√Hz (pp. 7 and 6) [D9, D10], and suit 1 GΩ on small diodes.
- **OPA828** has the widest bandwidth, 45 MHz (p. 6) [D7], with 4 nV/√Hz at 1 kHz and 1.2 fA/√Hz.
- **OPA827** lies between them, with 4 nV/√Hz, 2.2 fA/√Hz and 22 MHz (p. 6) [D8].

### 5.4 Low-noise CMOS op amps

The low-noise CMOS op amps match the voltage noise of the best JFET parts at 10 kHz and above, though not at low frequency, which makes them the quietest choice at the lower gains, whose bands reach far above 10 kHz. OPA1656 and OPA2156 reach 2.9–3.0 nV/√Hz at 10 kHz, as low as the best JFET parts, with only 1.9 pF of common-mode input capacitance, although their differential capacitance is 9.1 pF (OPA1656, p. 6; OPA2156, pp. 5–6) [D11, D12]. Both specify 20 MHz at unity gain. At a gain of 100, OPA1656 specifies 53 MHz and OPA2156 25 MHz. For both the higher figure applies at the noise gains of this note, as their SPICE models confirm (Section 9.2). Their flicker noise is high: 11.8–12 nV/√Hz at 100 Hz. So is their current noise: 6 and 19 fA/√Hz at 1 kHz, which limits them to 457 MΩ and 46 MΩ. Their bias currents are 20–40 pA maximum. At equal bandwidth they are the quietest choices at 100 kΩ to 10 MΩ on small and medium photodiodes, and both can trade their extra gain–bandwidth for more bandwidth, OPA1656 for about twice as much (Section 6.1). Above 10 MΩ their current noise limits them. OPA320 is a 5-V rail-to-rail CMOS part with 8.5 nV/√Hz at 1 kHz, 0.6 fA/√Hz, 0.9 pA maximum bias current at 25 °C and 50 pA at 85 °C (pp. 7–8) [D13]. Its low bias current over temperature makes it a good compromise at 1 GΩ (Section 6.5).

### 5.5 Wideband FET op amps

The wideband FET op amps are built for speed: they give the widest bandwidth at the lowest gains, and as the gain rises they are the first to reach the resistor's own pole (Section 3.2). OPA656, OPA657, OPA818, ADA4817-1 and LTC6268-10 offer 230 MHz to 4 GHz of gain–bandwidth with 0.55–5.2 pF of input capacitance [D16, D19, D20, D21, D18]. OPA858, a CMOS part taken from the companion note for the 10-kΩ and 100-kΩ decades, offers 5.5 GHz with 0.82 pF and 5 pA of maximum bias current [D32]. OPA657, OPA818 and LTC6268-10 are decompensated, stable only above a noise gain of 7 or 10, which every design of this note exceeds (Section 3.1). Their white voltage noise is 2.2–6 nV/√Hz, but their flicker corners lie at 1–50 kHz. OPA818 has 8.4 nV/√Hz at 1 kHz. For LTC6268-10, its 0.1–10 Hz noise of 12.6 µV peak to peak implies about 28 nV/√Hz at 1 kHz, an estimate explained in Appendix B.1. Their current noise rises with frequency (Section 2.3). Their bias currents are picoamperes at 25 °C, nanoamperes at 85 °C, except LTC6268-10, a CMOS part, with 20 fA and 0.9 pA. They give the widest bandwidth at 100 kΩ to 1 MΩ, at a high noise cost (Section 6.1). At 10 MΩ and above they reach the resistor's ceiling, and with a small photodiode they come close to the floor there (Sections 6.3–6.4). Their DC open-loop gains are low: 65–92 dB for OPA656, OPA657, OPA818 and ADA4817-1, and 108 dB for LTC6268-10 (Table A.1). On large photodiodes at high gain, where the mid-band noise gain reaches thousands, the first four fail the condition of Section 3.1 and lose bandwidth, and Tables 6.1–6.5 leave those designs out. ADA4817-1 fails it on every photodiode from 1 MΩ up.

### 5.6 Zero-drift and auto-zero op amps

Zero-drift and auto-zero op amps are built for the smallest offset, which matters wherever a large low-frequency noise gain multiplies it. OPA388 has 0.25 µV of typical offset and 0.005 µV/°C of drift, but 100 fA/√Hz of current noise and 350 pA of maximum bias current (pp. 7–8) [D15]. OPA381, an auto-zero part marketed for transimpedance use, has 20 fA/√Hz at 10 kHz and a voltage noise of 70 nV/√Hz at 10 kHz, falling to 10 nV/√Hz above 1 MHz (p. 3) [D14]. Their current noise limits them to 1.65 MΩ and 41 MΩ (Eq. (11)), and in the sweep they are 5–26 dB above the floor (Table A.3). Their offset advantage matters only where the offset, multiplied by $1 + R_F/R_{sh}$, dominates the DC error, which is the case for low-shunt-resistance photodiodes (Section 6.6).

### 5.7 Bipolar op amps

A bipolar input has the lowest voltage noise of the op amps in this survey, but the shot noise of its base current gives it by far the largest current noise. OPA211 has 1.1 nV/√Hz at 1 kHz but 1.7 pA/√Hz and 175 nA of maximum bias current (p. 8) [D17]. Its optimum source resistance of 650 Ω is two to six orders of magnitude below the node impedances of this note. It has a place only on photodiodes with a shunt resistance of a few kilohms at the lowest gain, where its voltage noise competes with the diode's own noise. Even there the low-noise FET parts are as good (Section 6.6).

Three wideband bipolar parts of the companion note, OPA855, OPA955 and LMH6629, serve the 10-kΩ and 100-kΩ decades [D33, D34, D35]. They combine 0.69–0.99 nV/√Hz of voltage noise with 4–11 GHz of gain–bandwidth and 0.8–5.7 pF of input capacitance, and they are decompensated, stable above a noise gain of 7 or 10, which every design at these gains exceeds. Above 1 MHz the current noise of OPA855 and LMH6629 is 2.5–2.6 pA/√Hz, so that $R_{F,\mathrm{crit}}$ = 2.4–2.6 kΩ, and that of OPA955 is 0.55 pA/√Hz, so that $R_{F,\mathrm{crit}}$ = 54 kΩ; below about 100 kHz it rises as $1/f$. Their maximum bias currents are 5–23 µA at 25 °C. At 10 kΩ their low voltage noise wins in bands of tens of megahertz despite their current noise, while at 100 kΩ only OPA955 remains competitive (Section 6.9). OPA955's data sheet is Advance Information, for a preproduction part.

### 5.8 Discrete-JFET composites

When the voltage noise on a large capacitance dominates, as it does for every photodiode above a few hundred picofarads (Chapter 4), the cure is an input device with less $e_n$ per unit of capacitance than any op amp's. A discrete JFET in front of an op amp provides it. The JFET is a common-source stage, often cascoded, inside the op amp's feedback loop, and $R_F$ returns from the final output to its gate. Three devices from the companion note's folder show the range:

- **IF3601**, 0.35 nV/√Hz at 100 Hz, 175 mS, 650 pF of input capacitance at $V_{GS}$ = −4 V, and 0.1 nA maximum gate leakage at −10 V (IF3601 data sheet, pp. 1–3) [D22]. Its capacitance curve shows about 290 pF at −4 V and 900 pF at 0 V, which does not match the table, so the table value is used.
- **LSK170**, 0.9 nV/√Hz at 1 kHz (1.9 maximum) and 1.4 at 10 Hz, 22 mS, 20 pF, and 0.5 nA maximum gate operating current (LSK170 data sheet, p. 2) [D23].
- **BF862**, 0.8 nV/√Hz at 100 kHz, 10 pF, and 1 nA maximum gate leakage, from the companion's device table [D24].

For a family of FETs with the same transit frequency $f_T = g_m/(2\pi C_{iss})$, the channel noise is $e_n^2 = 4k_BT\Gamma/g_m = 4k_BT\Gamma/(2\pi f_TC_{iss})$, with $\Gamma \approx 2/3$. The $e_n\,\omega C$ term then has the power $e_n^2\omega^2(C_x + C_{iss})^2 \propto (C_x + C_{iss})^2/C_{iss}$, where $C_x$ is the node capacitance without the FET. Setting its derivative with respect to $C_{iss}$ to zero, $2(C_x + C_{iss})/C_{iss} - (C_x + C_{iss})^2/C_{iss}^2 = 0$, gives the optimum

$$
C_{iss} = C_x ,
\tag{30}
$$

the capacitive-matching rule (the companion's Eq. (58)). At the optimum the noise power grows only in proportion to $C_x$, whereas for a fixed amplifier it grows as $C_x^2$. A device should therefore be chosen with an input capacitance near that of the photodiode. The comparison against ADA4625-1, the lowest-noise op amp of the survey, confirms the rule. With the input capacitance of each device included, the product $e_n\,C_T$ at 10 kHz falls by these factors (Table A.6, from `hg_numbers.py`):

- **100 pF:** 3.0 dB (IF3601), 10.9 dB (LSK170) and 12.9 dB (BF862);
- **380 pF:** 10.8, 11.2 and 12.5 dB;
- **1 nF:** 15.0, 11.2 and 12.4 dB;
- **3.7 nF:** 18.0, 11.3 and 12.3 dB.

The small devices win on small diodes, and IF3601 wins on large ones. Since the $e_n\,\omega C$ noise integrates as the cube of the bandwidth, equal noise allows the bandwidth to grow by the 2/3 power of the amplitude ratio: 2.3–4.0 times for the cases above.

In the sweep the composites are modelled with an assumed composite gain–bandwidth product of 50 MHz, a design choice rather than a datasheet value. Their current noise is the shot noise of the maximum gate current, which overstates it because the typical gate current is not specified. With these assumptions IF3601 brings the 380-pF silicon photodiode from 11.1 dB of excess noise with ADA4625-1 to 3.0 dB, at the same bandwidth of about 290 kHz at 100 kΩ. It brings the 1-nF InGaAs photodiode from 14.8 dB to 4.0 dB, at 228 kHz instead of 179 kHz (Table A.3). On the small photodiode BF862 and LSK170 composites come within 0.7–1.4 dB of the floor at 100 kΩ to 10 MΩ, against 3.5–3.6 dB for ADA4625-1. Above 10 MΩ the maximum gate currents of 0.1–1 nA, whose shot noise is 5.7–18 fA/√Hz, compete with the resistor. The composites' advantage there depends on the actual gate current, which must be measured (Appendix C, item 4). Gate current also rises with drain–gate voltage through impact ionization, so the drain voltage of a composite for high gain should be kept low.

A SPICE model of such a composite confirms the estimate (Section 9.5, Figure 12). An LSBF862 common-source stage with a cascode and a 1-kΩ drain load, followed by an integrator, brings the 380-pF photodiode from 12.4–12.6 dB of excess noise with OPA140 to 2.8 dB, at 1.8 times the bandwidth. It brings the 1-nF photodiode from 12.5–16.5 dB to 3.1–5.2 dB. The SPICE composite is 1.7–2.4 dB quieter than the analytic BF862 estimate and about 15% slower, because the LSBF862 model card's noise and capacitances differ from the BF862 data-sheet values (Table 9.5).

![Figure 12](figures/schem_jfet_composite.png)

*Figure 12. The discrete-JFET composite simulated in Section 9.5. J1, an LSBF862 in common source with its gate at the summing node, is cascoded by J2, whose gate is held at 2.5 V and bypassed. $R_D$ = 1 kΩ from 15 V carries 10 mA with the drain at 5 V, so the stage's voltage gain $g_mR_D$ is about 33. The integrator senses the drain against 5 V: its non-inverting input is on the drain and its inverting input returns to 5 V through 1 kΩ, so the loop settles with the drain at 5 V. With $C_c$ = 106 pF in its feedback its unity-gain frequency is $1/(2\pi\times1\ \mathrm{k\Omega}\times106\ \mathrm{pF})$ = 1.5 MHz, which with the gain of about 33 gives the composite the 50 MHz of gain–bandwidth assumed in the sweep. $R_F$ and $C_F$ return from the integrator's output to J1's gate, where the photodiode's $C_D$ and $R_{sh}$ also sit. In SPICE the integrator is an ideal transconductance-and-capacitor stage.*

### 5.9 Integrated photodiode-amplifiers

OPT101 integrates a 2.29 × 2.29 mm photodiode with a TIA and a 1-MΩ feedback resistor, and gives 14 kHz of bandwidth at 0.45 A/W (650 nm) from a single 2.7–36 V supply (OPT101 data sheet, p. 1) [D28]. Integration removes the board's leakage and stray capacitance at the summing node, which is the dominant practical problem of a discrete TIA at high gain (Chapter 8), at the price of a fixed gain and a fixed photodiode.

---
