## 8. DC errors, leakage and guarding

At 100 MΩ and above, Chapter 6 found that the amplifiers differ more in DC accuracy than in noise. This chapter collects the DC errors and the board-level effects that are as large as the amplifier's own errors at those gains.

### 8.1 The DC error budget

The output error of the TIA in the dark has three sources: the offset voltage, multiplied by the low-frequency noise gain; the bias current; and any leakage current into the summing node, both multiplied by $R_F$:

$$
V_{err} = V_{OS}\left(1 + \frac{R_F}{R_{sh}}\right) + \bigl(I_B + I_{leak}\bigr)R_F .
\tag{38}
$$

Analog Devices gives the same terms for a photodiode TIA (ADA4530-1 data sheet, p. 44, Eqs. 17–20) [D1]. Table A.3 evaluates Eq. (38) without leakage, with the maximum $V_{OS}$ and the maximum $I_B$ at 25 °C and 85 °C, for every design. On the small, high-shunt-resistance photodiode the offset dominates up to about 10 MΩ and the bias current above, as Section 6.4 described. On the 14-kΩ photodiode the offset term dominates at every gain, because $R_F/R_{sh}$ reaches 71 at 1 MΩ.

A resistor in series with the non-inverting input, equal to $R_F\parallel R_{sh}$, cancels the bias-current error when the two input currents match, as in bipolar parts. TI's OPA128 photodiode circuit uses 400 MΩ there, bypassed by 1000 pF so that its Johnson noise does not reach the amplifier (SBOA061, p. 2, Fig. 3) [A2]. For FET-input parts the two bias currents do not match. The OPA656 data sheet therefore recommends no resistor at the non-inverting input, because the bias currents "do not match but are so low to begin with (< 20 pA) that dc errors due to input bias currents are negligible" (OPA656 data sheet, p. 14) [D16]. Unbypassed, any resistance $R$ there adds $\sqrt{4k_BTR}$ to $e_n$, which the node capacitance then turns into current noise (the companion's Section 3.10).

### 8.2 Leakage and guarding

A leakage resistance $R_{ins}$ from a conductor at potential $\Delta V$ to the summing node injects $\Delta V/R_{ins}$, which Eq. (38) multiplies by $R_F$. Analog Devices writes that it is "very difficult to maintain high insulation resistance values in glass epoxy (such as FR-4) PCB materials", and that "resistance values of 10 TΩ to 100 TΩ are achievable" (ADA4530-1 data sheet, p. 34) [D1]. With 10 V across 10 TΩ, that is 1 pA, or 1 mV at the output of a 1-GΩ TIA. That is comparable with the bias current of a precision JFET part at 25 °C and fifty times the 20-fA limit of an electrometer. The cure is a guard: a conductor that surrounds the summing node and is held at the summing node's own potential. The insulation between guard and node then sees only the offset voltage, microvolts, and its leakage becomes negligible, while the leakage from other conductors flows into the guard instead of the node. For the inverting TIA with its non-inverting input grounded, the summing node is at ground potential, so the guard is a ground ring around it. For a single-supply TIA with the non-inverting input at a mid-supply voltage, the guard must be driven at that voltage. The integrated guard buffers of ADA4530-1 and OPA928 do exactly this, within 100 µV and 50 µV maximum (Section 5.1). Hamamatsu likewise recommends guard rings and PTFE terminals for photodiode amplifiers at high gain (KSPD9001E04, p. 10) [P5].

### 8.3 Dielectric relaxation

Every insulator polarizes with a delay after the voltage across it changes, and the polarization current that follows can last for minutes. Analog Devices measured it on two board laminates with a large alternating test voltage. FR-4 "requires 1 hour to dissipate the dielectric relaxation current to less than 10 fA", while Rogers 4350B, a ceramic-filled laminate, "requires less than 20 sec to dissipate the dielectric relaxation current to less than 1 fA" (ADA4530-1 data sheet, p. 35) [D1]. For a high-gain TIA this matters whenever a voltage near the summing node changes: when the photodiode's bias is switched, after a range change (Section 7.1), or after the output has saturated. A feedback or integration capacitor, if one is added, should likewise have a low-absorption dielectric.

### 8.4 Humidity, contamination and the layout of the summing node

The insulation resistance of the board depends on moisture. Analog Devices writes that at lower temperatures, below about 70 °C, "the insulation resistance creates more significant leakage current errors than the amplifier itself", so that "the relative humidity of the air is the most important error source at lower temperatures" (ADA4530-1 data sheet, p. 35) [D1]. Its bias-current limits are therefore specified at a relative humidity below 50% (p. 3). Flux residues and handling contamination have the same effect, and the same data sheet devotes sections to cleaning and handling, solder paste, guard rings, guard planes and via fences, cables and connectors (pp. 37–43). These were not read in detail for this note (Appendix C, item 7).

Section 3.4 adds three layout rules for the feedback resistor and the summing node.

- **No grounded plane under the feedback resistor.** A grounded plane makes the response peak (Table 3). Either cut the plane away, or replace it under the resistor by copper driven at one third of the output, or by strips at graded potentials, from a resistive divider between the output and ground (Section 3.4, Figure 6, Table 9.4). Copper tied to the output also stops the peaking, but it divides the bandwidth by three to four. Copper around the resistor should never be tied to the summing node itself, which slows the response as much as tying it to the output and adds to the node's capacitance and leakage. The strip nearest the summing node must be separated from it by the summing node's own guard ring.
- **A short summing node.** Keep it with the photodiode close by, because every picofarad there adds to $C_T$ and thus to the $e_n\,\omega C$ noise. A photodiode at the end of a cable adds the cable's capacitance in full, together with the noise that the cable's movement generates.
- **The guard ring of Section 8.2** around the summing node and the non-inverting input, on both sides of the board where possible.
- **A shielded enclosure for the whole front end.** The photodiode, the summing node, the feedback network and the amplifier belong together in a closed, grounded metal enclosure, with any cable to the photodiode shielded as well. At 1 GΩ, 1 fF of stray capacitance to a 1-V, 50-Hz source already gives 0.31 mV at the output (Section 3.4). Copper around the feedback resistor does not replace this enclosure; it only sets the resistor's surroundings inside it.

### 8.5 Temperature

Section 2.7 showed that the bias current of a FET input doubles every 10 °C (Eq. (15)) and that the photodiode's shunt resistance halves every 5–10 °C, while the resistor's noise rises only as $\sqrt{T}$. Both effects enter Eq. (38): the bias-current term grows by 64 from 25 °C to 85 °C, and the offset term by the growth of $R_F/R_{sh}$. For the S1336-18BK at 1 GΩ, $R_F/R_{sh}$ rises from 0.5 at 25 °C to about 2200 at 85 °C, using the dark-current coefficient as in Section 2.7, so that 25 µV of offset becomes a 55-mV error. Weak-light measurements at high gain therefore need the photodiode, and preferably the whole summing node, at a controlled temperature, and a cooled photodiode where the shunt resistance limits the floor (Section 6.7).

---
