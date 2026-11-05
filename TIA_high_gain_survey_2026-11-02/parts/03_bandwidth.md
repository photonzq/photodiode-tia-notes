## 3. Bandwidth, stability and the feedback resistor

Chapter 2 gave the noise density; this chapter gives the band over which it is integrated, and the stability of the loop that sets that band. A high-gain TIA has two bandwidth limits: the amplifier's gain–bandwidth product acting on the node capacitance, and the feedback resistor's own capacitance. Section 3.1 derives the first, together with the feedback capacitance that gives a flat response. Section 3.2 finds the gain at which the second takes over, Section 3.3 treats photodiodes with low shunt resistance, Section 3.4 models the resistor as the distributed line it is, and Section 3.5 weighs four ways to more bandwidth.

### 3.1 The loop and the maximally flat feedback capacitance

Once $R_F$ is chosen, the feedback capacitance $C_F$ is the one value left, and it sets both the flatness and the width of the response. This section derives the $C_F$ of a maximally flat response and the bandwidth it gives (Eqs. (18) and (19)), then two properties of the high-gain loop that keep the analysis simple, and one that limits it. For the lumped network and a photodiode whose shunt resistance is much larger than $R_F$, the admittances of Section 2.1 are $y_f = y_{11} = (1 + sR_FC_F)/R_F$ and $Y_n = [1 + sR_F(C_T + C_F)]/R_F$. Above its open-loop corner a compensated op amp is an integrator, $A(s) = \omega_t/s$ with $\omega_t = 2\pi\,GBW$. Substituting both into Eq. (6) gives

$$
Z_T(s) = -\frac{R_F}{1 + s\left(R_FC_F + \dfrac{1}{\omega_t}\right) + s^2\,\dfrac{R_F\,(C_T + C_F)}{\omega_t}} ,
\tag{17}
$$

a second-order low-pass with natural frequency $\omega_0 = \sqrt{\omega_t/[R_F(C_T + C_F)]}$ and damping set by the coefficient of $s$, $2\zeta/\omega_0 = R_FC_F + 1/\omega_t$. In the regime of this note $1/\omega_t$ is negligible beside $R_FC_F$. The response is maximally flat (Butterworth, $\zeta = 1/\sqrt2$) when $R_FC_F = \sqrt2/\omega_0$, which gives

$$
C_F = \sqrt{\frac{C_T + C_F}{\pi R_F\,GBW}} \approx \sqrt{\frac{C_T}{\pi R_F\,GBW}} ,
\tag{18}
$$

and a −3 dB bandwidth equal to the natural frequency,

$$
f_{-3\,\mathrm{dB}} = \sqrt{\frac{GBW}{2\pi R_F\,(C_T + C_F)}} .
\tag{19}
$$

For $R_F$ = 1 MΩ, $C_T$ = 101 pF and $GBW$ = 20 MHz, Eq. (18) gives $C_F$ = 1.28 pF and Eq. (19) 176 kHz. The model of Appendix B, which evaluates Eq. (6) numerically, gives 175.9 kHz with no peaking and a phase margin of 66° at that $C_F$. The often-quoted design value $C_F = \sqrt{C_T/(2\pi R_F\,GBW)}$, used for example in Eqs. 8–9 of the ADA4625-1 data sheet (Rev. C, p. 28) [D6], is smaller by $\sqrt2$. It gives $\zeta$ = 0.5 and a 1.25-dB peak. The data sheet itself says that this choice "maximizes the signal bandwidth with a 45° phase margin but is marginal for stability" (p. 28), and that the optimum $C_F$ is found on the bench (p. 29) [D6]. The designs of this note use the smallest $C_F$ that keeps the response within 0.1 dB of maximally flat, which lies between the two values and gives phase margins of 63–66°.

Two properties of the high-gain loop simplify the analysis. First, the loop crosses unity at about $f_x \approx GBW\cdot C_F/(C_T + C_F)$, where the noise gain is $(C_T + C_F)/C_F$. In this note's amplifier-limited designs on the 20-pF diode that noise gain at crossover is 4–160 at 100 kΩ, 11–130 at 1 MΩ and 34–220 at 10 MΩ, so $f_x$ is a small fraction of the gain–bandwidth product. For ADA4625-1 at 1 MΩ on the 20-pF diode, for example, the design has $C_F$ = 0.78 pF, a noise gain of 47 at crossover and $f_x \approx$ 18 MHz/47 = 0.38 MHz, far below any second pole of the amplifier. A single-pole model is then adequate, whereas the companion note, whose loop crosses at a noise gain of 7–12 near 1 GHz, needed the digitized open-loop curves. Two parts of this survey need more than a single pole. OPA1656 specifies 20 MHz of bandwidth at unity gain but 53 MHz of gain–bandwidth at a gain of 100 (p. 6) [D11], and its vendor's SPICE model shows why. Its open-loop gain is a single pole of 56 MHz up to about 300 kHz, and then falls faster, with 21° of extra phase lag at 1 MHz and 29° at 3 MHz (Section 9.2). OPA2156 shows the same pattern more mildly: 20 MHz at unity gain, 25 MHz at a gain of 100 (p. 6) [D12], and 8° of extra phase lag at 1 MHz in its SPICE model. The model therefore uses 53 and 25 MHz for these two parts, each multiplied by the shape of its open-loop gain beyond a single pole. Second, decompensated op amps, which are stable only above a minimum noise gain of 7 (OPA657, OPA818) or 10 (LTC6268-10), are stable in every design of this note, because the noise gain at crossover is far larger. Their extra gain–bandwidth therefore counts in full.

One further property of the loop limits the analysis rather than simplifying it. The integrator model $A = \omega_t/s$ holds only above the amplifier's open-loop corner, $GBW/A_0$, where $A_0$ is the DC open-loop gain; below that corner the gain stays at $A_0$. In Eq. (6) the node admittance enters the transimpedance as $Y_n/A$. At frequencies below the open-loop corner it therefore adds $Y_n/A_0$ to the feedback admittance, and its capacitive part acts as an extra feedback capacitance of $(C_T + C_F)/A_0$. That lowers the bandwidth in the same way as a larger $C_F$ would. The extra capacitance is at most a tenth of $C_F$, and the loss of bandwidth correspondingly small, when

$$
A_0 \geq 10\,\frac{C_T + C_F}{C_F} ,
\tag{19a}
$$

that is, when the DC open-loop gain exceeds the mid-band noise gain at least tenfold. The precision op amps of this note, with $A_0$ of 110–154 dB, meet this condition in every design. Four wideband parts, OPA656, OPA657, OPA818 and ADA4817-1, with 65–92 dB, fail it on large photodiodes at high gain, where the noise gain reaches thousands. ADA4817-1 fails it even on the 20-pF photodiode from 1 MΩ up, and OPA818 only on the 500-pF and 1-nF photodiodes. LTC6268-10, with 108 dB, meets it everywhere. For OPA657, whose $A_0$ is 70 dB (a factor of 3,160), the noise gain at 1 GΩ on the 380-pF photodiode with 0.1 pF is about 3,900. Its bandwidth there falls to 963 Hz in SPICE, against 1.59 kHz for the resistor's own pole. The SPICE checks of Section 9.2 found this limit. The model therefore uses each amplifier's datasheet $A_0$ (Table A.1), and Tables 6.1–6.5 leave out the 63 designs of the sweep that fail the condition, which Table A.3 marks.

### 3.2 When the resistor, not the amplifier, sets the bandwidth

A real resistor carries a fraction of a picofarad across itself, so the feedback capacitance can never be smaller than that. This section finds the gain at which the resistor's own capacitance takes the bandwidth over from the amplifier, and how the noise differs on the two sides of that gain. Equation (19) holds while the $C_F$ that Eq. (18) asks for is larger than the resistor's own capacitance $C_{par}$. As $R_F$ grows, Eq. (18) asks for less, and at the crossover gain

$$
R_F^* = \frac{C_T}{\pi\,GBW\,C_{par}^2}
\tag{20}
$$

the bare resistor already provides it. Above $R_F^*$ the loop is overdamped by $C_{par}$ alone, the bandwidth approaches the resistor's pole $f_R = 1/(2\pi R_FC_{par})$ of Eq. (4), and the amplifier's gain–bandwidth no longer matters. With $C_{par}$ = 0.1 pF and $GBW$ = 20 MHz, $R_F^*$ = 15.9 MΩ for $C_T$ = 10 pF, 159 MΩ for 100 pF and 1.59 GΩ for 1 nF. An electrometer with 2 MHz moves these ten times higher, and a wideband part with 200 MHz ten times lower (Appendix A, Table A.4). Above $R_F^*$ an amplifier needs only $GBW \geq C_T/(\pi R_FC_{par}^2)$ to reach the ceiling. At 1 GΩ with 40 pF this is 1.3 MHz, which even the electrometers meet. At $R_F^*$ itself the two formulas differ by $\sqrt2$, because a maximally flat response with its feedback pole at $f_R$ has its −3 dB point at $\sqrt2\,f_R$. Figure 3 plots both ceilings.

![Figure 3](figures/fig2_bandwidth_ceilings.png)

*Figure 3. The two bandwidth ceilings of a TIA. Grey: the resistor's own pole, Eq. (4), for 0.05, 0.1 and 0.2 pF. Coloured: the maximally flat bandwidth of Eq. (19) for a 20-MHz amplifier on 10 pF, 100 pF and 1 nF. The circles mark the crossover gain $R_F^*$ of Eq. (20) for 0.1 pF. Left of a circle the amplifier limits the bandwidth; right of it the resistor does.*

The two regimes differ in their noise as well, and two short formulas show how.

*Amplifier-limited regime.* Ignoring the photodiode's shunt resistance, the voltage noise reaches the floor at $f_e$ of Eq. (13), and the bandwidth is Eq. (19). Their ratio is

$$
\frac{f_e}{f_{-3\,\mathrm{dB}}} = \frac{1}{e_n}\sqrt{\frac{4k_BT}{2\pi\,(C_T + C_F)\,GBW}} ,
\tag{21}
$$

independent of $R_F$. Integrating $1 + (f/f_e)^2$ from 0 to $B$ gives $B\,[1 + B^2/(3f_e^2)]$, so the excess noise over the band is approximately

$$
\Delta N \approx 10\log_{10}\!\left[1 + \frac{1}{3}\left(\frac{f_{-3\,\mathrm{dB}}}{f_e}\right)^{2}\right] .
\tag{22}
$$

For ADA4625-1 on the 20-pF diode ($C_T + C_F$ = 41.7 pF, 18 MHz, 3.3 nV/√Hz), Eq. (21) gives $\sqrt{1.6466\times10^{-20}/(2\pi\times41.7\ \mathrm{pF}\times18\ \mathrm{MHz})}/3.3\ \mathrm{nV}$ = 0.57, and Eq. (22) gives 3.1 dB. The full model, which adds the current noise and the shunt resistance, gives 3.5–3.6 dB at 100 kΩ to 10 MΩ (Table A.3). On the 380-pF diode (402 pF) the ratio is 0.18 and the excess 10.4 dB; the full model gives 11.0 dB. In the amplifier-limited regime, then, the excess noise is fixed by the amplifier's voltage noise, the node capacitance and the gain–bandwidth product, whatever the gain. A faster amplifier buys bandwidth only as $\sqrt{GBW}$ and lets the $e_n\,\omega C$ noise into the band in exchange. The one way to have both is a lower $e_n\,C_T$: a quieter input device, or less capacitance.

*Resistor-limited regime.* With the bandwidth at $f_R$ the ratio becomes

$$
\frac{f_e}{f_R} = \frac{\sqrt{4k_BT\,R_F}\;C_{par}}{e_n\,(C_T + C_F)} ,
\tag{23}
$$

which grows as $\sqrt{R_F}$. At 1 GΩ, 0.1 pF, 3.3 nV/√Hz and 41 pF it is $\sqrt{1.6466\times10^{-11}}\times10^{-13}/(3.3\times10^{-9}\times4.1\times10^{-11})$ = 3.0. The resistor-limited band therefore contains less and less $e_n\,\omega C$ noise as the gain rises. That is why, at the highest gains, almost every FET-input amplifier comes close to the floor, and the choice turns on DC accuracy instead (Chapter 6).

### 3.3 Photodiodes with low shunt resistance

Some photodiodes have a shunt resistance far below the feedback resistors of this note, such as the extended-InGaAs diode of Table 1 with 14 kΩ. Section 2.2 showed what a shunt resistance comparable to or below $R_F$ does to the floor; this section shows what it does to the loop. At low frequency the noise gain is $1 + R_F/R_{sh}$, so the loop crosses unity at about $GBW/(1 + R_F/R_{sh})$. The bandwidth can be no higher:

$$
f_{-3\,\mathrm{dB}} \lesssim GBW\,\frac{R_{sh}}{R_F + R_{sh}} .
\tag{24}
$$

The circuit has become a voltage amplifier of gain $R_F/R_{sh}$, acting on the photovoltage $I_{ph}R_{sh}$ that the diode develops across its own shunt resistance. For the 14-kΩ extended-InGaAs diode and ADA4625-1 (18 MHz), Eq. (24) gives 252 Hz at 1 GΩ, and the full model gives 235 Hz. At 1 MΩ it gives 249 kHz, but the 520 pF at the node raises the noise gain further and the model gives 79 kHz. The same noise gain multiplies the offset voltage: the output error is $V_{OS}(1 + R_F/R_{sh})$. Hamamatsu warns that if the feedback resistance exceeds the shunt resistance, the op amp's voltage noise and offset are multiplied by $(1 + R_f/R_{sh})$ (KSPD9001E04, p. 9) [P5], and Analog Devices gives the same expression for the offset (ADA4530-1, p. 44, Eqs. 19–20) [D1]. With 80 µV of maximum offset and $R_F$ = 1 GΩ on 14 kΩ, the output error is 80 µV × 71 400 = 5.7 V. Together with Eq. (10), this fixes the rule for such diodes: $R_F$ no larger than about ten times $R_{sh}$, and any further gain in a voltage stage after the TIA, where it costs no noise because the diode's own noise already dominates.

### 3.4 The feedback resistor as a distributed RC line

**Why a lumped model is not enough.** In the resistor-limited regime the transimpedance is the feedback resistor's own response, so whatever the resistor's admittance does with frequency becomes the transfer function of the instrument. The usual description of the resistor, a resistance $R$ in parallel with one capacitance $C_{par}$, assumes that every electric field line that leaves the resistor ends on its other terminal. A chip resistor is built differently. It is a resistive film that runs the length of a ceramic body between two metal end caps. In a TIA one end cap sits at the summing node, which the loop holds at virtual ground, and the other sits at the output. At low frequency the potential along the film therefore rises linearly from zero to $V_{out}$. At a fraction $u$ of the way from the summing-node end, where $u$ runs from 0 to 1, it is $u\,V_{out}$. The film has two kinds of parasitic capacitance.

- The first runs from one end cap to the other, through the body, the air and the pads. We call it $C_{ee}$, for end to end. It is an ordinary two-terminal capacitor, and the lumped model describes it correctly.
- The second runs from the film to whatever conductor lies under or beside it, usually the ground plane. We call its total $C_g$. It is spread along the film. The share of it that belongs to a short slice of the film sees the difference between that slice's potential and the conductor's potential. Because the film's potential changes along its length, each slice drives a different current through its share, and the shares cannot be gathered into a single capacitor between two nodes.

A resistive film with capacitance spread along it to a conductor is a uniform RC line. It is the same structure as a long on-chip interconnect or an integrated polysilicon resistor over its substrate, and it is analysed with the same theory as a transmission line. Analog Devices points at the distributed capacitance when it warns that current-noise calculations above the $R_FC_F$ pole are "error prone due to the distributed parasitic nature of $C_F$" (ADA4530-1 data sheet Rev. C, p. 39) [D1]. For integrated TIAs, Knorr and Zimmermann modelled the polysilicon feedback resistor as a uniform RC line to the substrate [[A5]](https://doi.org/10.1109/TCSI.2003.816322); only the abstract of their paper was read (Appendix C, item 2). Seidl, Swoboda and Zimmermann used the same model and built an integrated resistor that removes the effect [[A6]](https://doi.org/10.1049/el:20053310). Their work is described at the end of this section. This note applies the model to a discrete resistor on a circuit board. It does so for two reasons: the model predicts effects that a lumped model cannot (the response can peak, and the resistor's noise rises with frequency), and it changes the layout rules and the limits of equalization.

**The model.** Imagine the film cut into many short slices (Figure 4). Each slice is a small resistor in series with its neighbours, with a small capacitor from the slice to the conductor below. The film is then a ladder of series resistors and shunt capacitors, which is exactly the circuit that SPICE would simulate. In the limit of infinitely many slices the ladder becomes a transmission line whose inductance and shunt conductance are zero, so the standard transmission-line results apply with a series resistance $R$ and a shunt capacitance $C_g$ for the whole line (Appendix B.5, Steps 1 and 2). The quantity that decides how the line behaves is

$$
\theta = \sqrt{j\omega RC_g} = (1 + j)\sqrt{\frac{\omega RC_g}{2}} ,
$$

which plays the role of the line's electrical length. Its real part tells how strongly a signal applied at one end is attenuated before it reaches the other end, and its imaginary part tells how far it is delayed in phase. Both grow together, in proportion to $\sqrt{\omega}$. A signal therefore does not travel along an RC line as a wave. It diffuses into the line, the way heat diffuses into a rod. While $|\theta|$ is well below 1, the whole film follows its low-frequency potential profile and the lumped model holds. When $|\theta|$ approaches 1 and beyond, the far part of the film no longer follows the near end. For 1 GΩ and 0.3 pF, $|\theta| = 1$ at $f = 1/(2\pi RC_g)$ = 530 Hz.

![Figure 4](figures/schem_rc_line.png)

*Figure 4. The feedback resistor's film as a ladder of $N$ slices. Each slice is a resistance $R/N$ in series with its neighbours, with a capacitance $C_g/N$ to the conductor beneath the film, which is held at $a(u)\,V_{out}$ at the position $u$, from 0 at the summing-node end cap to 1 at the output end cap. $C_{ee}$, from end cap to end cap, is an ordinary lumped capacitance. A grounded plane has $a = 0$, a plane driven at a fraction of the output $a = \alpha$, and a graded guard $a = u$. As $N$ grows the ladder becomes the uniform RC line of Eq. (25); Section 9.4 simulates it with $N$ = 20.*

The analysis of Section 2.1 needs two quantities from the feedback network. The first is $y_{11}$, the current that flows into the network from the summing node per volt at the summing node, with the output held at zero. The second is $y_f$, the current that the network delivers into the summing node per volt at the output, with the summing node held at zero. For the line with $C_{ee}$ in parallel they are

$$
y_{11} = \frac{\theta}{R}\coth\theta + j\omega C_{ee}, \qquad
y_f = \frac{\theta}{R\,\sinh\theta} + j\omega C_{ee} .
\tag{25}
$$

The second expression, without $C_{ee}$, is Eq. (1) of Seidl, Swoboda and Zimmermann written as an admittance (their $Z_{\pi0}$ is $1/y_f$; p. 1301) [[A6]](https://doi.org/10.1049/el:20053310). Appendix B.5 derives both expressions from the ladder. When $\theta$ is small, both reduce to the lumped $1/R + j\omega C_{ee}$. The two admittances go straight into Eqs. (6) and (8). The transimpedance uses $y_f$ and the node admittance $Y_n = Y_s + y_{11}$. The noise uses $4k_BT\,\mathrm{Re}\{y_{11}\}$ for the resistor and $e_n^2|Y_s + y_{11}|^2$ for the amplifier's voltage noise. No other change to the analysis is needed, which is why Section 2.1 used the two-port form.

**What the line does at low frequency.** While $|\theta|$ is below about 1, a line over a grounded plane behaves like the resistor with a capacitance $C_{ee} - C_g/6$ across it and a capacitance $C_g/2$ from each end to ground:

$$
y_f \approx \frac{1}{R} + j\omega\Bigl(C_{ee} - \frac{C_g}{6}\Bigr), \qquad
y_{11} \approx \frac{1}{R} + j\omega\Bigl(C_{ee} + \frac{C_g}{3}\Bigr) .
\tag{26}
$$

The capacitance to the plane thus subtracts $C_g/6$ from the end-to-end capacitance in the feedback path. With the output held at zero, both the bridging element and the shunt at the summing node lead from the summing node to ground, so $y_{11}$ contains their sum, $C_{ee} - C_g/6 + C_g/2 = C_{ee} + C_g/3$. This $C_g/3$ is what the amplifier's voltage noise sees in addition to $C_{ee}$. At $C_g = 6C_{ee}$ the feedback capacitance of Eq. (26) vanishes, and with more $C_g$ it becomes negative. The transimpedance then rises with frequency before it falls.

Equation (26) can be derived with nothing more than current division. The derivation also covers a conductor driven to a potential other than ground, which the remedies below need. Let the conductor under the slice at position $u$ be held at the potential $a(u)\,V_{out}$; for a grounded plane, $a = 0$. At low frequency the film stays close to its linear profile $u\,V_{out}$, so the slice's share of the capacitance, $C_g\,du$, passes the current $j\omega C_g\,du\,[a(u) - u]\,V_{out}$ from the conductor into the film. Both ends of the film are held at fixed potentials, the summing node by the loop and the output by the op amp. The injected current therefore divides between the two ends as any current injected into a resistor with held ends does, in inverse proportion to the resistances: $uR$ towards the summing node and $(1-u)R$ towards the output. The fraction that reaches the summing node is $(1-u)R/R = 1-u$. Adding the contributions of all the slices gives the change of the transfer admittance. The same argument with the summing-node end at 1 V and the output at zero gives the change of $y_{11}$. In that case the slice sits at $1-u$ volts, and a conductor that is grounded or driven from the output is at zero. The results are

$$
\Delta y_f = j\omega C_g\int_0^1\bigl[a(u) - u\bigr](1-u)\,du , \qquad
\Delta y_{11} = j\omega C_g\int_0^1 (1-u)^2\,du .
\tag{26a}
$$

For a grounded plane the first integral is $-\int_0^1 u(1-u)\,du = -(\tfrac12 - \tfrac13) = -\tfrac16$, and the second is $\tfrac13$, which gives Eq. (26). The physical reading is direct. A grounded plane drains current out of the film before that current reaches the summing node, so for a given output voltage less current arrives. A feedback capacitor does the opposite, and the plane therefore acts as a negative feedback capacitance. A 400-section ladder evaluated at 0.01 Hz (`hg_model.ladder_y`) gives −0.16667 and +0.33333 for the two coefficients, and a capacitance of $0.50000\,C_g$ from the summing node to ground. The series expansion of Eq. (25), which gives the same coefficients, is in Appendix B.5 (Step 3).

**What it does, in full.** Figure 5 shows the transimpedance $-1/y_f$ of a 1-GΩ resistor with $C_{ee}$ = 0.05 pF for four values of $C_g$, with an ideal amplifier so that only the network is seen. Table 3 gives the numbers. Every frequency scales as $1/(RC)$, so the same curves hold at 10 MΩ with all frequencies a hundred times higher, and the peaking depends only on the ratio $C_g/C_{ee}$.

![Figure 5](figures/fig3_distributed_resistor.png)

*Figure 5. Transimpedance of a 1-GΩ feedback resistor with 0.05 pF end to end and a distributed capacitance $C_g$ to a ground plane, computed from Eq. (25) with an ideal amplifier. The dashed curve is the lumped resistor. The dash-dot curve has 0.3 pF to a plane driven from the output instead of ground, for which the transfer admittance is $y_{11}$ (Eq. (28) with $\alpha = 1$).*

*Table 3. The distributed feedback resistor of Figure 5 in numbers ($R$ = 1 GΩ; divide frequencies by 10 for 10 GΩ or multiply by 100 for 10 MΩ). Peaking is the maximum of $|Z_T|/R$; the lumped pole for comparison is $1/(2\pi RC_{ee})$. "Noise ×2" is the frequency at which the line's input noise current, $4k_BT\,\mathrm{Re}\{y_{11}\}$, has doubled (Eq. (27)). Model of Appendix B, `hg_numbers.py`.*

| $C_{ee}$ | $C_g$ | $C_g/C_{ee}$ | First-order $C_{ee} - C_g/6$ | Peak | −3 dB, plane at ground | Lumped pole | −3 dB, plane at output | Noise ×2 |
|---|---|---|---|---|---|---|---|---|
| 0.05 pF | 0 | 0 | 0.05 pF | none | 3.19 kHz | 3.18 kHz | 3.19 kHz | – |
| 0.05 pF | 0.1 pF | 2 | 0.033 pF | none | 5.22 kHz | 3.18 kHz | 1.86 kHz | 13.9 kHz |
| 0.05 pF | 0.3 pF | 6 | 0 | +4.6 dB at 3.4 kHz | 6.4 kHz | 3.18 kHz | 0.99 kHz | 4.6 kHz |
| 0.05 pF | 0.6 pF | 12 | −0.05 pF | +15.4 dB at 2.5 kHz | 5.3 kHz | 3.18 kHz | 0.58 kHz | 2.3 kHz |
| 0.1 pF | 0.3 pF | 3 | 0.05 pF | +0.1 dB at 1.1 kHz | 3.19 kHz | 1.59 kHz | 0.76 kHz | 4.6 kHz |

Three conclusions follow from the table.

- **Modest ground capacitance helps.** With $C_g/C_{ee}$ = 2 the response stays monotonic and its corner moves from 3.18 kHz to 5.22 kHz, because the plane removes part of the effective feedback capacitance.
- **Large ground capacitance makes the response peak.** At a ratio of 6 the peak is 4.6 dB, and at 12 it is 15.4 dB. A TIA whose resistor sits over a solid ground plane can therefore ring after a step, even with a well-behaved amplifier, and a lumped model that predicts a smooth pole at $1/(2\pi RC_{ee})$ will not show it.
- **An equalizer designed from a lumped measurement will be wrong.** Equalization (Section 3.5) needs the actual response, and near the corner that differs from a single pole by several decibels and tens of degrees.

**Why the low-frequency form fails at the corner.** The scaling of Table 3 has a simple reason, and the same reason limits Eq. (26). When the resistor sets the bandwidth, the corner lies near $\omega = 1/(RC_{ee})$. There $\omega RC_g = C_g/C_{ee}$, so the line's electrical length at its own corner, $|\theta| = \sqrt{C_g/C_{ee}}$, depends only on the ratio of the two capacitances and not on $R$. This also tells when the distributed capacitance matters. Where a deliberate $C_F$ much larger than $C_g$ sets the corner, as in the amplifier-limited regime below $R_F^*$, the line is short at the corner and $C_g$ is a small correction. Where the resistor's own capacitance sets the corner, $|\theta|$ there lies between 1 and 2.6 for the ratios of 1 to 7 that real boards give (see the estimate below), and the low-frequency form is no longer accurate. The numbers of this note therefore come from Eq. (25), or from a ladder where the conductor is not grounded, and Eq. (26) serves only to explain them.

**The line's own noise.** The feedback resistor's contribution to the input-referred noise is a current with the power density $4k_BT\,\mathrm{Re}\{y_{11}\}$ (Eq. (8)). This is Nyquist's theorem applied at the summing node: a passive network at temperature $T$ drives into a short circuit a noise current whose power density is $4k_BT$ times the real part of the admittance it presents there. Carrying the current-division argument of Eq. (26a) one step further gives the first correction to that real part (Appendix B.5, Step 4):

$$
\mathrm{Re}\{y_{11}\} \approx \frac{1}{R}\left[1 + \frac{(\omega RC_g)^2}{45}\right] .
\tag{27}
$$

The line's noise current therefore rises above its low-frequency value. Far above the corner the summing node sees only the part of the film within about one diffusion length of its end, because the capacitance to the plane shunts the rest of the film to ground. A shorter piece of film has a lower resistance, and a lower resistance has a larger Johnson noise current. In this limit $\mathrm{Re}\{y_{11}\}$ grows as $\sqrt{\omega C_g/(2R)}$ (Step 5). For 1 GΩ and 0.3 pF, Eq. (25) gives $R\,\mathrm{Re}\{y_{11}\}$ = 1.08 at 1 kHz, 1.28 at 2 kHz, 1.55 at 3 kHz, 1.83 at 4 kHz and 1.99 at 4.6 kHz. Equation (27) is within 3% of these values up to 2 kHz and overestimates them beyond. It places the doubling at $\omega RC_g = \sqrt{45}$, or 3.6 kHz, where the exact doubling is at 4.6 kHz (Table 3). Averaged from 0 to 4 kHz, the line's noise power is 1.3 times its low-frequency value, or 1.2 dB more. Near and above the resistor's corner the floor of Eq. (10) is therefore not flat, which matters when the response is equalized beyond the corner (Section 3.5).

**Driving the conductor beneath the resistor.** The conductor under the resistor need not be grounded. If it is driven from the output, the integrand of Eq. (26a) changes, and the plane's effect can be reversed, cancelled at low frequency or cancelled completely. For a conductor held at a fixed fraction $\alpha$ of the output, an exact relation follows from superposition alone (Appendix B.5, Step 6). The current into the summing node is the fraction $\alpha$ of the current with the conductor tied to the output, plus the fraction $1 - \alpha$ of the current with the conductor grounded. In terms of the admittances, and with Eq. (26a) for the low-frequency form,

$$
y_f(\alpha) = \alpha\,y_{11} + (1 - \alpha)\,y_{f0}
\approx \frac{1}{R} + j\omega\left[C_{ee} + C_g\left(\frac{\alpha}{2} - \frac{1}{6}\right)\right] ,
\tag{28}
$$

where $y_{f0}$ is the transfer admittance of Eq. (25) over a grounded conductor. Four cases matter.

- **A conductor tied to the output** ($\alpha = 1$) gives $y_f = y_{11} \approx 1/R + j\omega(C_{ee} + C_g/3)$. The conductor now pushes current into the film, most of it near the summing node, and acts as an additional feedback capacitance. The response is monotonic, with the corner of a lumped $R\parallel(C_{ee} + C_g/3)$. For 0.05 and 0.3 pF at 1 GΩ that corner is 0.99 kHz, against 3.2 kHz for the bare resistor (Table 3).
- **A conductor at one third of the output** ($\alpha = 1/3$) cancels the low-frequency effect of $C_g$ on the feedback path. The feedback capacitance is then $C_{ee}$, and the summing node keeps $C_g/3$ to the conductor. What remains is of higher order in $\omega RC_g$, and at the corner it is not small. For 1 GΩ and 0.3 pF at 4 kHz, where $\omega RC_g$ = 7.5, Eqs. (25) and (28) give $R\,(y_f - j\omega C_{ee}) = 0.825 + j\,0.174$ instead of 1. That is why the response ends somewhat below that of a resistor without a conductor beneath it (Section 9.4).
- **A graded guard** is a conductor whose potential follows the film's low-frequency profile, $a(u) = u$. It makes the integrand of Eq. (26a) zero everywhere. No current then flows through $C_g$ at any frequency, the film's potential stays exactly linear, and $y_f = 1/R + j\omega C_{ee}$ exactly (Step 7). The conductor still loads the summing node with $C_g/3$ through $y_{11}$.
- **Strips at graded potentials** approximate the guard. Each strip is held at the potential of the middle of the stretch of film above it. For a strip of width $h$, as a fraction of the length, centred on $m$, the integrand of Eq. (26a) is $(m - u)(1 - u)$. Its part that is linear in $u - m$ averages to zero over the strip, and its quadratic part leaves $h^3/12$ (Step 8). Four strips at $V_{out}/8$, $3V_{out}/8$, $5V_{out}/8$ and $7V_{out}/8$ therefore leave $4\times(1/4)^3/12 = 1/192$ of $C_g$, which is 0.0016 pF for 0.3 pF.

Section 9.4 puts all of these into a loop with the vendors' macromodels. With OPA140, 1 GΩ, 0.05 pF end to end and 0.3 pF beneath, the bandwidth is 4.01 kHz both without a conductor and with the ideal graded guard. Over a grounded plane it is 5.84 kHz, with a 7.45-dB peak and a 54% overshoot in the step response. It is 1.01 kHz with the conductor tied to the output, 3.69 kHz with 2% overshoot at one third of the output, and 3.56 kHz without overshoot with four strips (Table 9.4).

None of these drives changes the line's own noise of Eq. (27). The noise current at the summing node is found with every other terminal of the network held at its potential, and the op amp's output and a guard's driver are both low-impedance sources that hold their nodes. The noise current is therefore that of the line over a grounded conductor, whatever potential the conductor follows (Step 9). A guard restores the transfer function but not the noise. Only a smaller $C_g$, for example a cut-out in the plane, reduces both.

On a board the drive comes from a resistive divider between the output and ground (Figure 6), never from the summing node. The divider's current and its Johnson noise then reach the summing node only through $C_g$. With divider resistors of a few kilohms the noise voltage on the conductor is a few nanovolts per root hertz. Through 0.1 pF at 4 kHz it injects about $4\ \mathrm{nV/\sqrt{Hz}}\times2\pi\times4\ \mathrm{kHz}\times0.1\ \mathrm{pF} = 1\times10^{-17}\ \mathrm{A/\sqrt{Hz}}$, four hundred times less than the 4 fA/√Hz of a 1-GΩ resistor. The strip nearest the summing node is not at the summing node's potential. The guard ring of Section 8.2, which is at that potential, must therefore lie between the two, or the leakage across the gap becomes a DC error.

![Figure 6](figures/schem_guard_drives.png)

*Figure 6. Three ways to drive the conductor beside the feedback resistor, each from the output and never from the summing node. (a) A plane at $V_{out}/3$, from a divider of 2 kΩ over 1 kΩ, cancels the plane's low-frequency effect on the feedback path (Eq. (28) with $\alpha = 1/3$). (b) Four strips at $V_{out}/8$, $3V_{out}/8$, $5V_{out}/8$ and $7V_{out}/8$, each at the mid-point potential of its quarter of the film, from a divider of 1, 2, 2, 2 and 1 kΩ; they leave $C_g/192$. (c) The ideal graded guard, a resistive film beneath $R_F$ that is grounded under the summing-node end and tied to the output at the other. Both films are drawn as four equal slices. Because the summing node is a virtual ground, both rise linearly from zero to $V_{out}$, so the junctions that face each other sit at the same potential, $V_{out}/4$, $V_{out}/2$ and $3V_{out}/4$, and the capacitance $C_g$ between the films carries no current; this is the principle of the capacitive coupled distributed resistor (CCDR) of Seidl, Swoboda and Zimmermann, described at the end of Section 3.4. In all three the summing node keeps its own guard ring at its potential, ground (Section 8.2), between it and the nearest driven copper. Divider resistors of a few kilohms put only nanovolts of noise on the conductor, which reach the summing node through $C_g$.*

**Shielding the resistor: which potential?** A conductor around the resistor acts through Eq. (26a), whether it is a plane below it, a ring beside it or a can over it, and the same rule covers the end caps. A capacitance $C_k$ from a point of the feedback path at position $u_k$ to a conductor at $a_kV_{out}$ changes the transfer admittance by $j\omega C_k(a_k - u_k)(1 - u_k)$. The output end cap, at $u = 1$, therefore never matters: its capacitance only loads the op amp. The summing-node end cap, at $u = 0$, adds $a_kC_k$ to the feedback capacitance and $C_k$ to the capacitance of the summing node. A shield that passes between the two end caps also intercepts part of $C_{ee}$ and turns it into these two end-cap capacitances. Five choices follow.

- **A shield at ground, or at the summing node's potential driven by a buffer,** is at signal ground, $a = 0$. It subtracts $C_g/6$, may remove part of $C_{ee}$ as well, and makes the response peak once the net feedback capacitance turns negative: 7.45 dB with OPA140 for 0.3 pF at 1 GΩ (Table 9.4). This is the right potential for a guard around the summing-node pad and the amplifier's input, where it stops leakage (Section 8.2), but not for copper along the resistor.
- **A shield connected to the summing node itself** gives exactly the transfer admittance of a shield tied to the output, $y_f = y_{11}$ (Appendix B.5, Step 11), so it slows the response just as much. In addition, its own capacitance to its surroundings joins the summing node. That raises $C_T$ and the $e_n\,\omega C$ noise, and it enlarges the area through which leakage reaches the node. It is the worst of the five.
- **A shield tied to the output** gives a smooth, monotonic response, with the corner of $R\parallel(C_{ee} + C_g/3 + C_s)$, where $C_s$ is the capacitance from the summing-node end cap to the shield. For 0.3 pF at 1 GΩ that costs a factor of four in bandwidth (Table 9.4). Its leakage into the summing node is proportional to $V_{out}$, so it acts as a resistance in parallel with $R_F$: a gain error, not an offset.
- **No conductor near the resistor**, a cut-out in the plane with no copper nearby, gives the widest band, that of $R\parallel C_{ee}$, and the smallest rise of the line's noise. The film's remaining capacitance then goes to whatever lies near it, such as the enclosure, other parts or a hand, and is neither known nor constant.
- **A guard driven at one third of the output, or graded strips,** from a divider between the output and ground, gives nearly the band of the bare resistor (3.56–3.69 kHz against 4.01 kHz in Table 9.4), while it shields the film and fixes its surroundings. A single plane at $V_{out}/3$ adds $C_s/3$ through the summing-node end cap. Graded strips, whose first strip is close to zero, add almost nothing.

Shielding therefore pays only when the shield is driven at the potential that the film already has. None of this replaces a shield around the whole front end. At high gain the summing node turns any stray capacitance to a changing voltage into signal. A capacitance of 1 fF to a conductor carrying 1 V at 50 Hz injects $2\pi\times50\ \mathrm{Hz}\times1\ \mathrm{fF}\times1\ \mathrm{V}$ = 0.31 pA, which a 1-GΩ TIA turns into 0.31 mV. The same 1 fF to mains wiring at 230 V gives 72 pA, or 72 mV. The photodiode, the summing node, the feedback network and the amplifier must therefore sit together in a closed, grounded metal enclosure, and any cable to the photodiode must be shielded as well. The copper around the resistor only sets the resistor's surroundings inside that enclosure. Within it, the cut-out is the simple default when nothing near the resistor moves. The driven guard is the better choice when the resistor must be shielded, or when its response must not depend on its surroundings. In both cases the summing-node pad and the amplifier's input keep their own guard ring at the summing node's potential (Section 8.2). Because the rise of the line's noise depends only on $C_g$, whatever drives the conductor, a guard should lie no closer to the film than the shielding requires.

**The integrated precedent.** Seidl, Swoboda and Zimmermann met the problem of this section in an integrated optical receiver for optical-storage drives, built in a modified 0.5-µm silicon BiCMOS process with an integrated pin photodiode [[A6]](https://doi.org/10.1049/el:20053310). Their paper covers five points.

- **The problem.** Their 200-kΩ polysilicon feedback resistor lies on field oxide over the substrate, with $C_{FOX}$ = 66.3 fF between the two. They describe it with Knorr and Zimmermann's uniform-line model, $Z_{\pi0} = R_{poly}\sinh\sqrt S/\sqrt S$ with $S = j\omega R_{poly}C_{FOX}$ (their Eq. (1), p. 1301), which is $1/y_f$ of Eq. (25) without $C_{ee}$. They place its cutoff at the normalized frequency $\omega R_{poly}C_{FOX}$ = 9.18, which is 110 MHz for their resistor (p. 1301). Evaluating Eq. (25) there gives $|\sinh\theta/\theta| = \sqrt2$, so their cutoff is the frequency at which the line's transfer impedance has risen by 3 dB.
- **What it costs.** Their amplifier has 38.9 dB of open-loop gain and a dominant pole at $6.1\times10^9$ s⁻¹, with 4 fF of feedback capacitance and 130 fF at the input, of which 60 fF is the photodiode's. With an ideal 200-kΩ resistor their TIA formula gives 716 MHz. A simulation that includes the parasitic capacitance of a normal polysilicon resistor gives 75 MHz, which matches the 67 MHz measured on their earlier receiver with the same resistor value (p. 1301).
- **The remedy.** Their capacitive coupled distributed resistor (CCDR) places a second resistor directly beneath the polysilicon one: an n-well, whose resistance is lowered by two n⁺ implants (Fig. 1, p. 1301). The polysilicon resistor runs from the output to the summing node. The well runs beneath it from the output to ground, with its grounded end under the summing-node end of the polysilicon resistor (Figs. 1b and 2, p. 1301). Because the summing node is a virtual ground, the two films carry the same potential profile, and the oxide between them sees no voltage. In their words, $C_{FOX}$ then "has no effect" (p. 1301). In the terms of Eq. (26a), the well is a graded guard, $a(u) = u$. The bandwidth is then limited by the well's own capacitance to the substrate and by the stray capacitance of the polysilicon resistor. The authors therefore keep the well's time constant $R_{well}C_{well\text{-}sub}$ small against $R_{poly}C_{FOX}$, using the n⁺ implants to lower $R_{well}$ while the well stays narrow (p. 1301).
- **The result.** The receiver reached −3-dB bandwidths of 615 MHz at 660 nm and 603 MHz at 410 nm, flat within 1 dB, with a transimpedance of 201 kΩ. Its transimpedance–bandwidth products were 123 and 121 THzΩ (Fig. 3 and text, p. 1302). At 660 nm its rise and fall times were 562 and 531 ps, and its sensitivities were −29.4 dBm at 1 Gbit/s and −27.0 dBm at 1.25 Gbit/s, for a bit-error ratio of $10^{-9}$ (p. 1302). Against their earlier receiver, the bandwidth rose from 67 to 615 MHz, about nine times (p. 1302).
- **Its origin.** The authors describe the CCDR as a development of their earlier capacitive coupled voltage divider, in which a single coupling capacitor took the place of the distributed one (p. 1301) [[A7]](https://doi.org/10.1049/el:20031162), [[A8]](https://doi.org/10.1109/ISSCC.2004.1332798). Those two papers were not read (Appendix C, item 15).

**What the integrated remedy offers a board.** The principle carries over to a board directly, but its payoff is different, for three reasons.

- **On a board the limit is usually $C_{ee}$, which no guard removes.** On the chip the distributed capacitance, 66 fF against 4 fF of feedback capacitance, dominated, so removing it multiplied the bandwidth. On a board, $C_{ee}$ of 0.05–0.2 pF is comparable with $C_g/6$ or larger. A graded guard returns the response exactly to that of the resistor without a conductor beneath it, 4.01 kHz in Table 9.4, and no further.
- **The CCDR's connection is the right one for a board.** Its guard runs from the output to ground, not across the feedback resistor, which is what the divider described above does. The guard's current and noise therefore stay out of the summing node.
- **What a guard buys on a board is control.** A conductor under the resistor is often wanted, as a shield for the high-impedance film against pickup, or simply because the ground plane is there. Driven at one third of the output, or as graded strips, it no longer makes the response peak, and to first order the response no longer depends on the unknown $C_g$. That makes an equalizer (Section 3.5) predictable.

**A split resistor with guarded junctions.** The one place where the principle of the CCDR can widen a board's bandwidth is a feedback resistor split into $N$ equal resistors in series. The split divides the end-to-end capacitance by $N$, because the $N$ end-to-end capacitances are then in series (Section 3.5). Each junction between two resistors, however, carries the capacitance $C_j$ of its pads to the plane, at the position $u_k = k/N$ along the string. Equation (26a), with the integral replaced by a sum over the junctions, gives their low-frequency effect on the feedback capacitance as $C_j\sum_k(a_k - u_k)(1 - u_k)$, where $a_kV_{out}$ is the potential of the conductor under junction $k$. As an example, take three 333-MΩ resistors with 0.05 pF each, which give $C_{ee}/3$ = 0.0167 pF for the string, and an assumed 0.2 pF per junction.

- Over a grounded plane the two junctions add $-0.2\ \mathrm{pF}\times[(1/3)(2/3) + (2/3)(1/3)] = -0.089$ pF. The net feedback capacitance is then −0.072 pF, and the response peaks strongly.
- Over a plane tied to the output they add $+0.2\ \mathrm{pF}\times[(2/3)^2 + (1/3)^2] = +0.111$ pF. The net, 0.128 pF, is more than the 0.05 pF of a single resistor, so the split has made things worse.
- If instead each junction pad is surrounded by a guard held at its own low-frequency potential $u_kV_{out}$ (Figure 7), the junction capacitances see no voltage and carry no current. The equal end-to-end capacitances then divide the output voltage in the same ratio as the equal resistors, so the junctions stay at $u_kV_{out}$ at every frequency, and the string is exactly $R\parallel C_{ee}/N$ (Step 10).

![Figure 7](figures/schem_split_resistor.png)

*Figure 7. A 1-GΩ feedback resistor split into three 333-MΩ resistors with guarded junctions, the arrangement proposed above and not simulated (Appendix C, item 16). Each junction pad sits inside a guard held at its own low-frequency potential, $V_{out}/3$ or $2V_{out}/3$, so that the pad's capacitance to its surroundings carries no current, and each resistor body has a strip at its mid-point potential, $V_{out}/6$, $V_{out}/2$ or $5V_{out}/6$. One divider of six equal resistors of 1 kΩ between the output and ground supplies all five potentials. With matched end-to-end capacitances the string is then exactly $R\parallel C_{ee}/3$ (Appendix B.5, Step 10). The summing node keeps its own guard ring at ground.*

This is the principle of the CCDR applied where a board can gain from it. It holds under four conditions. First, the end-to-end capacitances of the parts must match, since a mismatch moves the junction potentials away from their guards' potentials above the corner. Second, the body of each part needs its own strip at its mid-point potential, as in the four-strip case above, and any direct capacitance between pads that are not neighbours must be kept small or intercepted by a guard. Third, the guard nearest the summing node must again be separated from it by the summing node's own guard ring. Fourth, the amplifier must have the gain–bandwidth to use the wider band. By Eq. (20) that takes $GBW \geq C_T/[\pi R(C_{ee}/N)^2]$, which is $20\ \mathrm{pF}/[\pi\times1\ \mathrm{G\Omega}\times(0.0167\ \mathrm{pF})^2]$ = 23 MHz for the three-part string on a 20-pF photodiode. The arrangement has not been simulated or built for this note (Appendix C, item 16).

**How large are $C_{ee}$ and $C_g$?** No resistor datasheet among the sources read gives them separately, so they are board-specific quantities to be measured (Appendix C, item 3). A parallel-plate estimate shows the order of magnitude. Take a 1206 resistor, 3.2 × 1.6 mm, with its film on a 0.55-mm alumina substrate ($\varepsilon_r$ = 9.8), a 35-µm air gap under the part, and the plane under FR-4 ($\varepsilon_r$ = 4.4). These dimensions are assumptions, not data. The three layers in series give

$$
\frac{1}{C_g} = \frac{1}{\varepsilon_0\varepsilon_{Al}A/d_{Al}} + \frac{1}{\varepsilon_0A/d_{gap}} + \frac{1}{\varepsilon_0\varepsilon_{FR4}A/d_{FR4}} ,
\tag{29}
$$

with $A$ = 5.12 mm². The alumina gives 0.81 pF and the gap 1.30 pF. With the plane 0.2 mm below, as on a four-layer board, FR-4 gives 1.00 pF and $C_g$ = 0.33 pF; with the plane 1.5 mm below, as on a two-layer board, $C_g$ = 0.10 pF. Fringing fields are neglected, so these values are a rough guide. With $C_{ee}$ of 0.05–0.1 pF, a 1206 resistor over the inner ground plane of a four-layer board lies at $C_g/C_{ee}$ ≈ 3–7, which in Table 3 ranges from a barely visible peak to more than 4 dB. A two-layer board, or a cut-out in the plane, keeps the ratio near 1–2.

**Field solutions of real layouts.** The side note [*Feedback networks in eight-lead packages and under guard rings*](../TIA_feedback_layouts/TIA_feedback_layouts.md) computes these capacitances with finite-element field solutions for five layouts of this note's range, all on two-layer boards without a plane under the network. Without a guard, the OPA637 in SOIC-8 with an 0805 has 93.3 fF across its feedback resistor and the LMC6001 in PDIP-8 with a 1206 has 88.4 fF, which supports the 0.1 pF of this note's sweeps. The LMC6001 film has only 52 fF to the conductors around it, 0.58 times the capacitance across it, and behaves as a lumped resistor (the side note's Sections 5 and 7). The guard layouts of the ADA4530-1 and LMP7721 data sheets, and the LMC6001 layout with guard rings, pass the guard under the resistor between its pads: a grounded strip under part of the film, the case $a = 0$ of Eq. (26a). They lower the first-order capacitance across the resistor to 11.6–27.4 fF but couple 169–176 fF to the film. The network's own band then ends at 0.58–0.84 of $1/(2\pi RC_F)$ with that first-order $C_F$, its response rises by at most 0.63 dB, and the line's noise power, $4k_BT\,\mathrm{Re}\{y_{11}\}$, lies 1.0–1.8 dB above that of a lumped resistor at $1/(2\pi RC_F)$. Above the crossover gain of Eq. (20) this is the TIA's response; below it the amplifier sets the response, and an external feedback capacitor sized from the first-order value overdamps the loop (the side note's Section 7.3).

**How the model is used in this note.** The sweeps of Chapters 4–6 keep the lumped resistor with $C_{par}$ = 0.1 pF, so that all amplifiers share one baseline that is not tied to an unmeasured board. The distributed model is used for Figure 5 and Table 3, for the layout rules of Section 8.4 and the limits of equalization in Section 3.5, and in the SPICE check of Section 9.4. In the scripts, `hg_model.urc_y` evaluates Eq. (25), and `hg_model.ladder_y` solves an $N$-section ladder under a conductor with any potential profile $a(u)$. For $\omega RC_g$ up to 30, which is five times the corner for the case of Table 3, a ladder of 10 sections is within 4.3% in magnitude and 4.9° in phase of Eq. (25), 20 sections within 1.2% and 1.2°, and 50 sections within 0.2% and 0.2° (`hg_numbers.py`). Section 9.4 uses 20 sections in SPICE.

### 3.5 Four ways to more bandwidth, and what each costs

Sections 3.1–3.4 set the bandwidth that a single feedback resistor allows: the amplifier's ceiling below the crossover gain and the resistor's own pole above it. Four techniques promise more: an equalizer after the TIA, a T-network or a smaller resistor followed by a voltage stage, a resistor split in two, and a bootstrapped photodiode. This section says what each gains and what it costs in noise or offset.

**Equalization.** In the resistor-limited regime the bandwidth can be extended by following the TIA with a filter whose zero cancels the resistor's pole, $(1 + sR_FC_F)/(1 + sR_FC_F/k)$, which widens the band by $k$ (Figure 8). The input-referred noise density of Eq. (8) does not change, because it does not depend on what follows the TIA. The widened band, however, admits more of the rising $e_n\,\omega C$ noise. Equalization is therefore useful up to about $f_e$ of Eq. (13) and costs noise beyond it. Table A.5 evaluates $f_e$ for four amplifiers. On the 20-pF diode at 1 GΩ, $f_e$ is 5.8 kHz for ADA4625-1 and 4.1 kHz for OPA140, against $f_R$ = 1.59 kHz: equalization can gain a factor of 2.6–3.7. For the electrometers ADA4530-1 and OPA928 it is 1.75–1.76 kHz, with their larger voltage noise, so equalization gains nothing. On the 380-pF diode $f_e$ is below $f_R$ for all four (0.08–0.91 kHz), and equalization gains nothing. Equalization also needs an accurate model of the resistor's response. With the distributed line of Section 3.4 a single-pole equalizer leaves errors of several decibels near the corner, and the capacitances depend on the board, so the response must be measured. A practical method is to inject a known current through a small series capacitor from a signal generator, $i = j\omega C_{inj}V$, and fit $C_{ee}$ and $C_g$ to the measured transimpedance. Above the corner the line's own noise also rises, by Eq. (27).

![Figure 8](figures/schem_equalizer.png)

*Figure 8. Equalization and its calibration. The equalizer after the TIA, $(1 + sR_FC_F)/(1 + sR_FC_F/k)$, cancels the resistor's pole and widens the band by $k$; it does not change the input-referred noise density. To measure the resistor's actual response, which the distributed capacitance of Section 3.4 makes differ from a single pole, a generator drives the known current $i = j\omega C_{inj}V$ into the summing node through a small capacitor $C_{inj}$, drawn dashed because it is connected only during the calibration, and $C_{ee}$ and $C_g$ are fitted to the measured transimpedance.*

**The T-network.** A T-network (Figure 9 (a)) replaces the single feedback resistor by a smaller resistor $R_1$ from the summing node to a node T, a resistor $R_2$ from T to the output, and a resistor $R_3$ from T to ground. Because the summing node is a virtual ground, the photocurrent $I$ flows through $R_1$ and sets T to $IR_1$ in magnitude. $R_3$ then draws $IR_1/R_3$ to ground, so $R_2$ carries $I(1 + R_1/R_3)$, and the output is

$$
|V_{out}| = I\left[R_1\left(1 + \frac{R_2}{R_3}\right) + R_2\right] \approx k\,R_1\,I , \qquad k = 1 + \frac{R_2}{R_3} .
\tag{29a}
$$

A 10-MΩ resistor with $k$ = 100 thus gives 1 GΩ. Four properties follow from Eq. (29a) and the circuit.

![Figure 9](figures/schem_t_network.png)

*Figure 9. Two ways to reach 1 GΩ with a 10-MΩ resistor (Table 3.1). (a) A T-network: $R_1$ = 10 MΩ from the summing node to the node T, $R_2$ = 9.9 kΩ from T to the output and $R_3$ = 100 Ω from T to ground, so that $k = 1 + R_2/R_3$ = 100 and the transimpedance is $kR_1$ (Eq. (29a)); the whole Johnson noise current of $R_1$ reaches the input. (b) The same 10 MΩ alone, followed by a voltage stage of gain 100: the same noise floor and offset, and $\sqrt{100}$ = 10 times the amplifier-limited bandwidth of the T (Eq. (29b)).*

- *Noise.* $R_1$ runs from the virtual-ground summing node to the low-impedance node T, so its whole Johnson noise current, $\sqrt{4k_BT/R_1}$, enters the input. That is $k$ times the noise power of a real resistor of $kR_1$, or $10\log_{10}k$ dB more: 20 dB for 10 MΩ with $k$ = 100. $R_2$ and $R_3$ add the noise voltage $\sqrt{4k_BT\,(R_2\parallel R_3)}$ at T. It drives the current $\sqrt{4k_BT\,(R_2\parallel R_3)}/R_1$ through $R_1$, which is smaller than $R_1$'s own noise current by the factor $\sqrt{(R_2\parallel R_3)/R_1}$ and therefore negligible.
- *Offset and low-frequency voltage noise.* With a high-resistance photodiode, the amplifier's noise gain at DC is $1 + R_2/R_3 = k$. The output offset is therefore $kV_{OS}$, which is $V_{OS}/R_1$ referred to the input, $k$ times that of a single resistor; the amplifier's low-frequency voltage noise grows in the same way. The error from the bias current, $I_B$ times the transimpedance, is the same as with a single resistor. TI's application note on photodiode amplifiers with OPA128 states for these reasons that "a very high resistance feedback resistor is often better than a low resistance in a T network" (SBOA061, p. 2) [A2].
- *Loop and bandwidth.* T passes only $1/k$ of the output on to $R_1$, so the loop is that of a TIA with $R_1$ driven by an amplifier with the gain–bandwidth $GBW/k$. By Eq. (19) its amplifier-limited bandwidth is that of Eq. (29b) below: the same as for a single resistor of $kR_1$, whereas $R_1$ alone reaches $\sqrt{k}$ times more. The T does move the resistor's own pole up $k$-fold, to $1/(2\pi R_1C_{par})$. It therefore beats a single resistor only where that resistor is limited by its own capacitance, and only up to Eq. (29b).
- *A voltage stage instead.* A TIA with $R_1$, followed by a voltage stage of gain $k$ (Figure 9 (b)), has the same noise floor and the same multiplied offset, because its floor is again that of $R_1$. Its first stage, however, runs at the noise gain of $R_1$ alone and reaches $\sqrt{k}$ times the bandwidth of the T.

$$
f_{-3\,\mathrm{dB}} = \sqrt{\frac{GBW/k}{2\pi R_1\,(C_T + C_F)}} = \sqrt{\frac{GBW}{2\pi kR_1\,(C_T + C_F)}}
\tag{29b}
$$

Table 3.1 compares the options for 1 GΩ. For ADA4625-1 on the 20-pF photodiode, Eq. (29b) gives $\sqrt{18\ \mathrm{MHz}/(2\pi\times1\ \mathrm{G\Omega}\times41\ \mathrm{pF})}$ = 8.4 kHz, and both T-networks stop near it, at 8.8–9.0 kHz. The voltage stages reach 22 and 88 kHz with the same noise floors. All four lose 6–16 dB of noise density against the single 1-GΩ resistor. That resistor is limited to 1.65 kHz by its own capacitance, but it can be equalized to about $f_e$, 5.8 kHz for this amplifier and photodiode (Table A.5), without losing its floor.

*Table 3.1. Three ways to 1 GΩ of transimpedance, with ADA4625-1 on the 20-pF, 2-GΩ photodiode. Each resistor has 0.1 pF of its own, and each design follows the 0.1-dB rule of Section 1.4. The voltage stage has 45 MHz of gain–bandwidth and 4 nV/√Hz. The floor of a real 1-GΩ resistor and the photodiode is 4.97 fA/√Hz. The output offsets assume 80 µV at each amplifier; a zero-drift voltage stage halves the two-stage values. `t_network_vs_second_stage.py`.*

| Design | Bandwidth | Noise at 100 Hz | Output offset |
|---|---|---|---|
| Single 1-GΩ resistor | 1.65 kHz | 6.71 fA/√Hz | 0.12 mV |
| T-network, 100 MΩ with $k$ = 10 | 9.0 kHz | 13.9 fA/√Hz | 0.84 mV |
| T-network, 10 MΩ with $k$ = 100 | 8.8 kHz | 40.9 fA/√Hz | 8.0 mV |
| 100 MΩ, then a ×10 voltage stage | 22.0 kHz | 13.9 fA/√Hz | 1.6 mV |
| 10 MΩ, then a ×100 voltage stage | 88.2 kHz | 40.9 fA/√Hz | 16 mV |

A T-network or a voltage stage is acceptable wherever $R_1$'s noise does not dominate anyway. That is the case when the signal's own shot noise exceeds it, above $2k_BT/(qR_1)$ by Eq. (2), which is 0.51 nA for 100 MΩ and 5.1 nA for 10 MΩ. It is also the case when the photodiode's shunt resistance lies below $R_1$, so that the diode's own noise dominates (Section 6.6), and on large photodiodes, where $e_n\,\omega C_T$ dominates at the bandwidth needed. Otherwise the better design is the largest resistor whose own pole, or equalized response, covers the band, followed by a voltage stage if more gain is needed. Between a T-network and that voltage stage, the stage is preferable: it is faster, and it can be filtered or AC-coupled. The T-network saves one op amp. It keeps a moderate resistor at the summing node, which is cheaper, more stable and less affected by leakage resistance in parallel with it. And its higher noise gain can stabilize a decompensated op amp.

**Splitting the resistor.** Two resistors of $R_F/2$ in series halve the end-to-end capacitance and are recommended by TI when the required $C_F$ is below about 0.15 pF (OPA818 data sheet, p. 23, as cited in the companion's Section 8.10) [D20]. The junction between them, however, adds capacitance to the plane, so the string is more like the grounded line of Section 3.4, with a larger $C_g/C_{ee}$. A split resistor should therefore sit over a cut-out in the plane, or have each junction guarded at its own fraction of the output (Section 3.4). A plane tied to the output also stops the peaking, but it adds more feedback capacitance than the split removes.

**Bootstrapping the photodiode.** A follower that drives the photodiode's far terminal with the summing node's voltage keeps the voltage across $C_D$ constant. The photodiode's capacitance then carries no signal current, and the op amp sees only its own input capacitance and the board's. Hobbs shows such a circuit, a cascode plus a bootstrap follower around a 100-pF photodiode with a 301-kΩ feedback resistor, reaching about 2 MHz with its carrier-to-noise ratio only 3.3 dB below the shot-noise limit at 1 MHz (Hobbs, OPN April 2001, p. 45, Figs. 8–10) [[A4]](https://doi.org/10.1364/OPN.12.4.000044). The follower's own voltage noise now appears across $C_D$, so the noise is that of the follower's input device times $\omega C_D$. Bootstrapping is thus a way to reach the bandwidth of a small capacitance with the noise of a discrete input device. It helps in the amplifier-limited regime and not above $R_F^*$, where the resistor sets the bandwidth. The companion note found the break-even for its 1-pF node at 1.9–3.7 pF (its Table A8.4), so in this note's regime, with tens of picofarads to nanofarads, bootstrapping is well inside its useful range.

---
