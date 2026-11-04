## 4. Which term dominates, at which gain and frequency

Chapters 2 and 3 give each noise term and each bandwidth limit as a formula. This chapter puts them together for the photodiodes of Table 1, so that the dominant term can be read off for any gain and frequency. The results come from the full model (Eqs. (6) and (8), with the design rule of Section 1.4), not from the approximations.

### 4.1 Maps of the largest noise term

Figure 10 shows, for every feedback resistance from 10 kΩ to 10 GΩ and every frequency from 0.01 Hz to 100 MHz, which of the five terms of Eq. (8) is largest. The amplifier is ADA4625-1, a low-noise JFET op amp that is a reasonable choice over most of the range. The left panel is the small silicon photodiode (20 pF, 2 GΩ) and the right panel the large InGaAs photodiode (1 nF, 6.5 MΩ). The black line is the −3 dB bandwidth of each design, and frequencies above it are paled, because noise there is filtered out.

![Figure 10](figures/fig4_dominant_term_maps.png)

*Figure 10. The largest term of the input-referred noise, Eq. (8), against feedback resistance and frequency, for ADA4625-1 with $C_{par}$ = 0.1 pF and 1 pF of board capacitance. Left: S1336-18BK-like photodiode, 20 pF and 2 GΩ. Right: G12180-050A-like photodiode, 1 nF and 6.5 MΩ. The black line is the −3 dB bandwidth of the design at each $R_F$, and the region above it is paled.*

Five regions appear, and each has a boundary given by an equation of Chapters 2–3.

- **The resistor's Johnson noise** (blue) fills the low-frequency part of the band wherever $R_F$ is below the photodiode's shunt resistance and below the amplifier's $R_{F,\mathrm{crit}}$. Its upper edge is $f_e$ of Eq. (13), which falls as $1/\sqrt{R_F}$.
- **The voltage noise on the node capacitance** (brown) fills the band above $f_e$. In the amplifier-limited regime, left of the kink in the black line, Eq. (21) fixes $f_e/f_{-3\,\mathrm{dB}}$ independently of $R_F$. The brown wedge under the black line therefore has the same relative height at every gain up to the kink. For the small diode $f_e$ is 0.57 of the bandwidth, which leaves the upper 43% of the band dominated by $e_n\,\omega C$. For the large diode $f_e/f_{-3\,\mathrm{dB}} \approx$ 0.1, so it dominates almost the whole band.
- **The resistor's own ceiling.** The kink in the black line is the crossover gain $R_F^*$ of Eq. (20): $40.9\ \mathrm{pF}/(\pi\times18\ \mathrm{MHz}\times(0.1\ \mathrm{pF})^2)$ = 72 MΩ for the small diode and 1.8 GΩ for the large one. Right of the kink the bandwidth follows the resistor's pole, and the brown wedge shrinks, as Eq. (23) predicts.
- **The amplifier's current noise** (red) takes over at the right edge of the left panel, above $R_{F,\mathrm{crit}}$ = 813 MΩ for ADA4625-1 (Eq. (11)). An amplifier with less current noise, such as OPA140 with 25.7 GΩ, moves this boundary off the map.
- **The photodiode's own shunt noise** (green) takes over in the right panel above $R_F \approx R_{sh}$ = 6.5 MΩ, as Eq. (10) predicts. There a larger $R_F$ no longer lowers the floor. Beyond about 1 GΩ the bandwidth also starts to fall faster than the resistor's pole, because the noise gain $1 + R_F/R_{sh}$ eats the loop gain (Eq. (24)).

The fifth term, the voltage noise on the conductance (purple), appears only in the bottom-left corner of both maps. There the flicker noise of ADA4625-1 below 1 Hz meets the small conductance of a 10-kΩ resistor. For this amplifier it never matters within the band. It does matter for a CMOS amplifier on a low-shunt-resistance photodiode (Table 4b).

### 4.2 Noise spectra of the six gain decades

Figure 11 shows the input-referred noise density itself, for the six gain decades, with ADA4625-1 on the 380-pF silicon photodiode. Each curve is flat at the floor of Eq. (10) at low frequency (dashed), turns up at $f_e$, and rises as $f$ above it, along a single asymptote $e_n\,2\pi f\,C_T$ that is the same for every gain. Only the 10-kΩ curve rises again below about 10 Hz, where the amplifier's flicker noise acts on the conductance $1/R_F$ (Section 6.8). The circles mark the bandwidth of each design. Raising $R_F$ by a decade lowers the floor by $\sqrt{10}$ but moves $f_e$ down by $\sqrt{10}$ as well, and the bandwidth down by $\sqrt{10}$ while the amplifier limits it. The band of every design up to 100 MΩ therefore ends in the same position relative to the asymptote, about 5.5 times above $f_e$ (Eq. (21) gives $f_e/f_{-3\,\mathrm{dB}}$ = 0.18), so the voltage noise dominates every one of them.

![Figure 11](figures/fig5_noise_spectra.png)

*Figure 11. Input-referred noise density of a TIA with ADA4625-1 on a 380-pF, 0.4-GΩ silicon photodiode (S1336-8BK) at $R_F$ = 10 kΩ to 1 GΩ. Solid: total, Eq. (8). Dashed: the floor of Eq. (10). Circles: the −3 dB bandwidth of each design.*

### 4.3 How much each term contributes

Table 4a gives the two largest terms in the band of each design, and their shares of the integrated noise power, for ADA4625-1 on all five photodiodes of the sweep. Table 4b gives the same for the electrometer ADA4530-1. The pattern of Figures 10 and 11 holds across all of them, and the shares show how strongly one term dominates.

*Table 4a. The two largest terms of Eq. (8) in the band [1 Hz, $f_{-3\,\mathrm{dB}}$] and their shares of the noise power, with the bandwidth of the design; "R" marks a resistor-limited design. ADA4625-1, $C_{par}$ = 0.1 pF. `hg_analysis.py`, `hg_tables.py`.*

<!-- table: table_4a -->

*Table 4b. As Table 4a, for the electrometer ADA4530-1.*

<!-- table: table_4b -->

Four observations summarize the tables.

- **With a small, high-shunt-resistance photodiode**, the band splits roughly evenly between the resistor and the voltage noise up to about 10 MΩ. The resistor takes over at 100 MΩ. At 1 GΩ the amplifier's current noise joins it for ADA4625-1, whose $R_{F,\mathrm{crit}}$ is 813 MΩ, while the resistor stays largest for the electrometer.
- **With a large photodiode**, the voltage noise takes 89–98% of the noise power at every gain up to 100 MΩ, and the electrometer, with four to five times more voltage noise, is worse there than the JFET part.
- **With a photodiode whose shunt resistance is a few megohms**, that resistance dominates above $R_F \approx R_{sh}$, whatever the amplifier.
- **With a photodiode of 14 kΩ**, the diode's noise dominates from 1 MΩ up for the JFET part. For the CMOS electrometer, the voltage noise on the conductance dominates instead, because its flicker noise (80 nV/√Hz at 10 Hz) exceeds $e_{n,\mathrm{crit}}$ = 15.2 nV/√Hz of Eq. (12). Its bandwidth also collapses to 28 Hz at 1 GΩ, by Eq. (24) with its 2-MHz gain–bandwidth product.

---
