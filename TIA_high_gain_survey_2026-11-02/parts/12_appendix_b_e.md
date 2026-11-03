## Appendix B. Methods

### B.1 Data and conventions

Every datasheet value was read from a rendered image of the page, not from extracted text. `scripts_archive/spec_rows.py` renders the rows of a specification table, or the figure above or below a caption, as image strips labelled with their PDF page, and text search only locates the strips. The values are collected in `data/amplifiers.json` and `data/photodiodes.json` with their pages. Four conventions apply to them.

- **Noise between datasheet points** is interpolated linearly in log-log. Below the first point it is held flat, except where the first point lies at or below 1 kHz and the two lowest points fall with frequency. That case is flicker noise, and it is continued downward with the slope of those two points, capped at the slope of a $1/f$ power density. Above the last point the density is held flat. Current noise given only as a curve that starts above 1 kHz and rises, as for the wideband parts, is continued below its first point with the slope from that point to the first point at least a decade above it, and the shot noise of the typical bias current is added in quadrature as its floor (Section 2.3). The tables of Appendix A show only datasheet values, not extrapolations.
- **The gain–bandwidth product** is the value at a gain of 100 for OPA1656 and OPA2156, and the unity-gain bandwidth for OPA211, the one other part that gives two values. OPA1656 specifies 20 MHz at unity gain and 53 MHz at a gain of 100 (p. 6) [D11], and OPA2156 20 and 25 MHz (p. 6) [D12]. Their SPICE models showed open-loop gains that are single poles of 56 and 25 MHz up to about 300 kHz, with extra roll-off and phase lag above that (Section 9.2). The model therefore uses 53 and 25 MHz, each multiplied by the shape of its macromodel's open-loop gain beyond a single pole, which is tabulated in `data/amplifiers.json` (`add_aol_shape.py`). OPA211 specifies 45 and 80 MHz (p. 9) [D17]; the model keeps 45 MHz, which is conservative and has not been checked against its SPICE model (Appendix C, item 19).
- **The flicker noise of LTC6268-10** below 20 kHz is not given as a curve. It is estimated from its 0.1–10 Hz noise of 12.6 µV peak to peak (companion record, p. 3). The estimate assumes a pure $1/f$ density $K/f$ and a peak-to-peak value of 6.6 times the rms, so that $K = (12.6\ \mu\mathrm{V}/6.6)^2/\ln100 = 7.9\times10^{-13}\ \mathrm{V^2}$. That gives 0.89 µV/√Hz at 1 Hz and 28 nV/√Hz at 1 kHz. The $1/f$ shape and the factor 6.6 are assumptions.
- **The maximum bias current at 85 °C** is the datasheet limit at 85 °C, or "at the temperature extremes", where one is given. Otherwise it is the geometric interpolation between the limits at 25 °C and 125 °C, $I_{25}^{0.4}I_{125}^{0.6}$, which corresponds to a constant doubling interval between the two. Otherwise it is the 25 °C limit doubled every 10 °C (Eq. (15)). For the bipolar OPA211 the 125 °C limit of 200 nA is used, since bipolar bias currents fall with temperature.
- **The discrete-JFET composites** use the JFET's noise and capacitance, an assumed composite gain–bandwidth product of 50 MHz, and the shot noise of the JFET's maximum gate current as their current noise.

### B.2 What is reused from the companion note, and what is new

The companion note's analysis, and its SPICE method, were built for a different circuit: a 1-pF balanced pair at 1.5–2 kΩ and 150 MHz. Four parts of it are reused unchanged.

- **Its noise theory.** Section 2.1 generalizes its Eq. (23) to a two-port feedback network and a finite shunt resistance. With $R_{sh}\to\infty$ and a lumped network the two coincide.
- **Its conventions:** 25 °C, typical values, $C_T$ including $C_{CM}$ and $C_{DIFF}$, and an excess-noise figure of merit of the same form.
- **Its digitized curves** for LTC6268-10, OPA657, OPA818 and ADA4817-1, and its device data for BF862.
- **The capacitive-matching rule** for discrete FETs (its Eq. (58), here Eq. (30)).

Its SPICE tools are reused in Chapter 9: the ngspice shared library driven from Python, the translation of TI's noiseless resistors, and the LSBF862 model card. Its SPICE check of the open-loop model is not repeated. That check tested fast amplifiers near a loop crossover of 0.5–1 GHz, where the macromodels' higher poles decide the phase margin. In the high-gain TIA the loop crosses over at noise gains of tens to thousands, far below those poles (Section 3.1). Chapter 9 instead checks the complete designs against the vendors' macromodels. That check found the one limit of the single-pole model that matters here, the finite DC open-loop gain.

Six considerations are new in this note, and each changes a result.

1. **The photodiode's shunt resistance.** It enters the floor (Eq. (10)), the voltage-noise term (Eqs. (9), (12)), the bandwidth (Eq. (24)) and the offset (Eq. (38)). It is needed because at high gain $R_{sh}$ is often comparable to or smaller than $R_F$. For the 5-mm InGaAs diode it is already below 10 MΩ.
2. **The feedback resistor as a distributed RC line** (Section 3.4). It is needed because above $R_F^*$ the resistor's own frequency response is the transimpedance. A lumped $R\parallel C$ misses both the subtraction of the ground capacitance (Eq. (26)) and the peaking that follows from it (Table 3), and therefore mispredicts the response, the equalization and the resistor's noise above its corner (Eq. (27)). Analog Devices warns about the same "distributed parasitic nature of $C_F$" (ADA4530-1, p. 39) [D1]. Over a grounded conductor the exact two-port of Eq. (25) is used, because it has no discretization error. For a conductor driven from the output, `hg_model.ladder_y` solves a ladder of 200–400 sections. In SPICE a ladder of 20 sections is used, which stays within about 1% and 1° of Eq. (25) up to five times the corner (Sections 3.4 and 9.4). The sweeps keep a lumped 0.1 pF, because $C_{ee}$ and $C_g$ depend on the board and have not been measured. The distributed model sets the layout rules and the limits.
3. **Flicker noise and the full frequency range.** The analysis runs from 0.01 Hz to 100 MHz. That range is needed because the bands of high-gain TIAs reach down to the flicker region of CMOS amplifiers and up to the rising current noise of wideband FET parts.
4. **Temperature** (Sections 2.7 and 8.5). It is needed because at high gain the bias current and the shunt resistance change by orders of magnitude between 25 °C and 85 °C, while the floor hardly changes.
5. **The design rule for $C_F$.** The smallest value at or above the resistor's own capacitance that keeps the response within 0.1 dB of maximally flat (Section 1.4). It replaces the companion's phase-margin windows, because in the high-gain regime the resistor's capacitance often already exceeds what stability requires.
6. **The amplifier's DC open-loop gain** (Section 3.1). It is needed because on large photodiodes at high gain the mid-band noise gain reaches thousands. A wideband amplifier then loses bandwidth unless its open-loop gain is at least ten times that noise gain. At the companion's noise gains of 7–12 the condition never mattered.

### B.3 The SPICE checks

Chapter 9 describes the checks and their results. This section records how they were set up, so that they can be repeated.

The TIA decks of Section 9.2 and the noise decks of Section 9.3 are written and run by `hg_spice.py` for ngspice and by `hg_ltspice.py` for LTspice. Both take the designs from `data/results/designs.json` and compute the same metrics as the analytic sweep. ngspice-46 is loaded as the shared library that KiCad 10 installs, through `ngspice_shared.py`, which was taken over from the companion note, and its noise analyses run as decks separate from the AC analyses. LTspice runs headless, as `LTspice.exe -b -ascii` on each netlist in the netlist's own folder. Its raw output, an ASCII file in UTF-16, is parsed in Python, and its noise output for a current-source input is named `i(inoise)`. The vendors' model files are kept in `spice/models/`, one folder per part, and are not for redistribution (`spice/models/README.md`). The LTspice models are those of the LTspice library. Each run's deck, log and arrays are in `spice/runs/`, and the summaries are in `spice/results/`. `hg_spice_tables.py` writes Tables 9.1–9.6, and `hg_spice_figures.py` draws Figures 17–23.

Four of the checks needed particular settings.

- **The open-loop gains of OPA1656 and OPA2156** of Section 9.2 come from an AC analysis with the loop closed at DC only, through a 1-TH inductor from the output to the inverting input, which 1 F holds at signal ground (`hg_spice_gbw_check.py`).

- **The distributed resistor** of Section 9.4 is a 20-section ladder. Each section's conductor is driven from the output by a voltage-controlled source, at the potential that the treatment under test prescribes. The model column of Table 9.4 uses a 200-section ladder (`hg_model.ladder_y`).
- **The composite** of Section 9.5 uses an ideal second stage, because with OPA140's macromodel there the DC solver found latched operating points. Its $C_F$ is found in SPICE, by raising it in steps of 20% until the peak is at most 0.1 dB.
- **The logarithmic amplifiers** of Section 9.6 run from a 5-V supply, with 10 pF at the input, at currents from 100 pA to 10 mA.

### B.4 Reproducing the numbers

All numbers of this note come from the scripts in `scripts_archive/`, which its `README.md` indexes. They need Python 3 with NumPy, SciPy and Matplotlib, and PyMuPDF and Pillow for the PDF tools. The SPICE checks also need the ngspice shared library of KiCad 10 and LTspice.

- `hg_model.py` is the circuit model of Eqs. (6), (8) and (25). It also holds the ladder of Section 3.4, the interpolation of the datasheet curves, the datasheet open-loop gain and the design rule for $C_F$.
- `hg_analysis.py` runs the sweep of Chapter 6 and writes `data/results/designs.json`, `gain_table.json` and `amp_merits.json`.
- `hg_numbers.py` computes the numbers quoted in Chapters 3, 5 and 7: the distributed line, the ladder error, the plate estimate, equalization, composites and the log amplifier. It writes `data/results/numbers.json`.
- `hg_figures.py` draws Figures 2, 3, 5, 10 and 11, and `hg_schematics.py` the schematics, Figures 1, 4, 6–9 and 12–16, in the drawing style of `schematic_style.py`.
- `hg_tables.py` and `hg_appendix_tables.py` write the tables of Chapters 4 and 6 and of Appendix A.
- `hg_spice.py` and `hg_ltspice.py` run the SPICE checks of Chapter 9, and `hg_spice_tables.py` and `hg_spice_figures.py` write its tables and figures.
- `add_aol.py` adds the datasheet open-loop gains, with their pages, to `data/amplifiers.json`.
- `hg_spice_gbw_check.py` measures the open-loop gain of OPA1656 or OPA2156 in SPICE and compares the part's designs with the model at both data-sheet values; `set_gbw_opa1656.py`, `set_gbw.py` and `add_aol_shape.py` then store their gain–bandwidths and open-loop shapes in `data/amplifiers.json`; `hg_equal_bandwidth_check.py` compares OPA1656 and OPA2156 at equal bandwidths.
- `integrator_vs_tia.py` computes the noise charges of Section 7.3 and Table 7.1, `t_network_vs_second_stage.py` the T-networks and voltage stages of Table 3.1, and `set_in_lmc662.py` sets LMC662's current noise to the value of Section 2.3.
- `assemble_note.py` assembles this note from `parts/` and inserts the generated tables.

The analytic scripts run in under a minute, and the SPICE checks in a few minutes.

### B.5 Derivations for the distributed resistor

This section derives the results of Section 3.4 step by step. Steps 1–3 follow the standard theory of transmission lines. Steps 4–10 use only Kirchhoff's laws, current division and superposition. Throughout, the film has the total resistance $R$ and the total capacitance $C_g$ to the conductor beneath it. A position along the film is given as the fraction $u$ of its length, from 0 at the summing-node end to 1 at the output end.

**Step 1. The film as a transmission line.** Cut the film into slices of length $dx$. A slice has the series resistance $r\,dx$ and the capacitance $c\,dx$ to the conductor, where $r = R/\ell$ and $c = C_g/\ell$ are the resistance and the capacitance per unit length of a film of length $\ell$. Across one slice, the voltage falls by the current times the slice's resistance. Along one slice, the current falls by the current that the slice's capacitance passes to the grounded conductor. In the limit of thin slices,

$$
\frac{dV}{dx} = -r\,I , \qquad \frac{dI}{dx} = -j\omega c\,V .
\tag{B.1}
$$

These are the telegrapher's equations of a transmission line whose series impedance per unit length is $r$, with no inductance, and whose shunt admittance per unit length is $j\omega c$, with no conductance. Every result for transmission lines therefore holds with these two substitutions. The propagation constant is $\gamma = \sqrt{r\cdot j\omega c}$, and the characteristic impedance is $Z_0 = \sqrt{r/(j\omega c)}$. For the whole length, $\gamma\ell = \sqrt{j\omega RC_g} = \theta$ and $Z_0 = R/\theta$. Because $\sqrt{j} = (1+j)/\sqrt2$, the attenuation and the phase shift per unit length are equal, which is the mark of diffusion rather than of a travelling wave. Over the diffusion length $\delta = \sqrt{2/(\omega rc)}$, a signal entering at one end falls by a factor of $e$, and its phase lags by one radian.

**Step 2. The two admittances.** A transmission line of electrical length $\theta$ and characteristic impedance $Z_0$ relates the voltage $V_1$ and the current $I_1$ entering its near end to the voltage $V_2$ and the current $I_2$ leaving its far end through its chain matrix:

$$
\begin{pmatrix} V_1 \\ I_1 \end{pmatrix} =
\begin{pmatrix} \cosh\theta & Z_0\sinh\theta \\ \sinh\theta/Z_0 & \cosh\theta \end{pmatrix}
\begin{pmatrix} V_2 \\ I_2 \end{pmatrix} .
\tag{B.2}
$$

With the far end held at zero, $V_2 = 0$, the first row gives $V_1 = Z_0\sinh\theta\,I_2$ and the second gives $I_1 = \cosh\theta\,I_2$. The near end therefore draws $y_{11} = I_1/V_1 = \cosh\theta/(Z_0\sinh\theta) = (\theta/R)\coth\theta$. With the near end held at zero and 1 V at the far end, the first row gives $I_2 = -\cosh\theta/(Z_0\sinh\theta)$. The second row then gives $I_1 = \sinh\theta/Z_0 - \cosh^2\theta/(Z_0\sinh\theta) = -1/(Z_0\sinh\theta)$, because $\cosh^2\theta - \sinh^2\theta = 1$. The current delivered into the near-end node is $-I_1$, so $y_{f0} = 1/(Z_0\sinh\theta) = \theta/(R\sinh\theta)$. The end-to-end capacitance is a separate path between the two ends and adds $j\omega C_{ee}$ to both admittances, which gives Eq. (25).

**Step 3. The low-frequency expansion.** For small $\theta$, $\sinh\theta = \theta + \theta^3/6 + \theta^5/120 + \dots$ and $\cosh\theta = 1 + \theta^2/2 + \theta^4/24 + \dots$. Dividing the series term by term gives

$$
\frac{\theta}{\sinh\theta} = 1 - \frac{\theta^2}{6} + \frac{7\theta^4}{360} - \dots , \qquad
\theta\coth\theta = 1 + \frac{\theta^2}{3} - \frac{\theta^4}{45} + \dots .
\tag{B.3}
$$

With $\theta^2 = j\omega RC_g$, the terms in $\theta^2$ are imaginary and give the capacitances of Eq. (26). The term in $\theta^4 = -(\omega RC_g)^2$ of $\theta\coth\theta$ is real and gives Eq. (27). Steps 4 and 5 obtain the same results without series.

**Step 4. The noise term by current division.** The real part of $y_{11}$ follows from two rounds of the argument behind Eq. (26a). Hold the summing-node end at 1 V and the output end at zero, with the conductor grounded. Without capacitance, the film's potential is $v_0(u) = 1 - u$, and the current $1/R$ flows through it.

In the first round, the slice at $u$ draws the current $j\omega C_g\,du\,v_0(u)$ into its capacitance. A current drawn out of a resistor whose ends are held is supplied by the two ends in inverse proportion to the resistances to them, so the summing node supplies the fraction $1 - u$. In total the summing node supplies the extra current $j\omega C_g\int_0^1(1-u)^2\,du = j\omega C_g/3$, which is the capacitive part of $y_{11}$ in Eq. (26).

The currents drawn in the first round also lower the film's potential. A current $i$ drawn out of the film at $u'$, with both ends held, lowers the potential at $u'$ by $i$ times the resistance seen there. That resistance is $u'R$ in parallel with $(1-u')R$, or $u'(1-u')R$. The change falls linearly to zero towards each end, so at any position $u$ it is $-i\,R\,g(u,u')$, with $g(u,u') = u(1-u')$ for $u \leq u'$ and $g(u,u') = u'(1-u)$ for $u \geq u'$. Adding the changes caused by all the slices gives the change of potential after the first round:

$$
v_1(u) = -j\omega RC_g\int_0^1 g(u,u')\,(1-u')\,du' = -j\omega RC_g\,F(u) .
\tag{B.4}
$$

Carrying out the integral separately for $u' < u$ and $u' > u$ gives $F(u) = (1-u)\bigl(\tfrac12u^2 - \tfrac13u^3\bigr) + \tfrac13u(1-u)^3$.

In the second round, the slice at $u$ draws the additional current $j\omega C_g\,du\,v_1(u)$, of which the summing node again supplies the fraction $1 - u$. The summing node therefore supplies the further current

$$
j\omega C_g\int_0^1 v_1(u)\,(1-u)\,du = \omega^2RC_g^2\int_0^1 F(u)\,(1-u)\,du = \frac{\omega^2RC_g^2}{45} ,
\tag{B.5}
$$

because $\int_0^1(1-u)^2\bigl(\tfrac12u^2 - \tfrac13u^3\bigr)du = \tfrac1{90}$ and $\int_0^1\tfrac13u(1-u)^4\,du = \tfrac1{90}$. This current is in phase with the applied voltage, so it adds to the conductance: $\mathrm{Re}\{y_{11}\} = (1/R)[1 + (\omega RC_g)^2/45]$, which is Eq. (27).

**Step 5. The high-frequency limit.** Far above the corner, the far end of the line no longer matters, and from the summing node the line looks like an infinitely long ladder. Adding one more slice at the front of an infinite ladder leaves its input admittance $Y$ unchanged, so

$$
\frac{1}{Y} = r\,dx + \frac{1}{j\omega c\,dx + Y} .
\tag{B.6}
$$

Moving the last term to the left and keeping the terms of first order in $dx$ gives $j\omega c\,dx/Y^2 = r\,dx$, so $Y = \sqrt{j\omega c/r} = (1+j)\sqrt{\omega c/(2r)}$. In terms of the totals, its real part is $\sqrt{\omega C_g/(2R)}$. This equals $1/(r\delta)$, the conductance of one diffusion length of film. At high frequency the line's noise current is therefore that of a resistor one diffusion length long, and that length shrinks as $1/\sqrt{\omega}$.

**Step 6. A conductor at a fraction of the output.** The line and its conductor form a network with three terminals: the summing-node end, the output end and the conductor. The network delivers the current $y_{f0}$ into the summing node per volt at the output, and some current $y_c$ per volt on the conductor, while a volt on the summing node itself drives the current $y_{11}$ out of it into the network. If all three terminals are raised together by 1 V, nothing inside changes and no current flows, so $y_{f0} + y_c - y_{11} = 0$, or $y_c = y_{11} - y_{f0}$. By superposition, with the summing node at zero, the output at $V_{out}$ and the conductor at $\alpha V_{out}$, the current into the summing node is

$$
y_{f0}V_{out} + y_c\,\alpha V_{out} = \bigl[\alpha\,y_{11} + (1-\alpha)\,y_{f0}\bigr]V_{out} ,
\tag{B.7}
$$

which is Eq. (28). Its low-frequency form follows from Eq. (26): $\alpha(C_{ee} + C_g/3) + (1-\alpha)(C_{ee} - C_g/6) = C_{ee} + C_g(\alpha/2 - 1/6)$.

**Step 7. The graded guard.** Suppose that at some frequency the film's potential is exactly linear, $uV_{out}$, and that the conductor under each point is held at the same potential. Then no voltage appears across the distributed capacitance, no current flows through it, and the current in the film is the same at every point, $V_{out}/R$. A constant current through a uniform film produces exactly the linear potential that was assumed. The assumption is therefore consistent with Kirchhoff's laws everywhere, and since a linear circuit with given sources has only one solution, it is the solution. The current into the summing node is $V_{out}/R$ plus the current through $C_{ee}$, so $y_f = 1/R + j\omega C_{ee}$ at every frequency. The input admittance $y_{11}$ is unchanged, because with the output held at zero the guard is at zero too.

**Step 8. Graded strips.** A strip that covers $m - h/2 \leq u \leq m + h/2$ and is held at $mV_{out}$ contributes the integral of $(m - u)(1 - u)$ over its width to Eq. (26a). With $u = m + t$, the integrand is $-t(1 - m - t) = -(1-m)\,t + t^2$. The term in $t$ is odd and integrates to zero over the symmetric interval, and the term in $t^2$ gives $\int_{-h/2}^{h/2}t^2\,dt = h^3/12$. Four strips of width 1/4 give $4\times(1/4)^3/12 = 1/192$.

**Step 9. The noise with a driven conductor.** The thermal noise of a passive network, seen at one of its terminals while all its other terminals are held at fixed potentials, is a noise current whose power density is $4k_BT$ times the real part of the admittance seen at that terminal. This is Nyquist's theorem for the one-port that results when the other terminals are held. In the TIA the output end is held by the op amp and the conductor by its driver, both low-impedance sources. Noise currents injected into those terminals flow into the sources without changing any voltage, so they do not reach the summing node. The noise current at the summing node is therefore set by the admittance seen there with the output and the conductor both at signal ground. That admittance is $y_{11}$ of the line over a grounded conductor, whatever the conductor's drive. For a graded guard, whose potential differs from point to point, the same holds slice by slice.

**Step 10. A split resistor with guarded junctions.** Take $N$ equal resistors of $R/N$ in series, each with the end-to-end capacitance $C_{ee}$, with the summing node at zero and the output at $V_{out}$. Surround junction $k$ with a guard held at $u_kV_{out}$, where $u_k = k/N$. Try the solution in which every junction sits at $u_kV_{out}$. Each resistor then carries $V_{out}/R$, and each end-to-end capacitance carries $j\omega C_{ee}V_{out}/N$, the same in every section. The current that enters each junction from one side therefore equals the current that leaves it on the other, and the junction capacitances to the guards see no voltage. Every node obeys Kirchhoff's current law, so this is the solution. The current into the summing node is $V_{out}(1/R + j\omega C_{ee}/N)$, and the string is exactly $R\parallel C_{ee}/N$. If the end-to-end capacitances differ, the capacitive division no longer matches the resistive one above the corner. The junctions then move away from their guards' potentials, and the junction capacitances carry current again.

**Step 11. A shield connected to the summing node.** Join the conductor to the summing-node end of the line. The current that reaches the summing node from the output now arrives by two paths: through the film, $y_{f0}$ per volt at the output, and through the shield. Apply the argument of Step 6 at the output end. With 1 V on the output and the other two terminals at zero, the output drives the current $y_{22}$ into the network, of which $y_{f0}$ arrives at the summing-node end, so the rest, $y_{22} - y_{f0}$, arrives at the shield. A uniform line looks the same from either end, so $y_{22} = y_{11}$. The total current into the joined node is therefore $y_{f0} + (y_{11} - y_{f0}) = y_{11}$, exactly the transfer admittance of a shield tied to the output (Eq. (28) with $\alpha = 1$).

## Appendix C. Open questions and unknowns

1. **Germanium photodiodes.** No datasheet of a germanium photodiode was read; a university mirror of the Teledyne Judson J16 datasheet returned an error. Germanium is placed in the low-shunt-resistance class of Section 6.6 from general knowledge only, and its capacitance and shunt resistance should be added from a datasheet.
2. **The distributed-line model of Knorr and Zimmermann** [[A5]](https://doi.org/10.1109/TCSI.2003.816322) was read as an abstract only. Its transfer impedance, which Seidl, Swoboda and Zimmermann quote as their Eq. (1) [[A6]](https://doi.org/10.1049/el:20053310), agrees with Eq. (25). The full paper would show which simplified design formulas they derive and how their measured integrated resistors compare with Eq. (25).
3. **The capacitances $C_{ee}$ and $C_g$ of real chip resistors** over real boards are not known. Section 3.4 gives a parallel-plate estimate for a 1206 resistor (0.10–0.33 pF to the plane). A measurement on the actual board, with the injection method of Section 3.5, should replace it, for each resistor size and for a plane cut-out.
4. **The gate current of the discrete JFETs** at their operating point is specified only as a maximum (0.1–1 nA). The composites' current noise above 10 MΩ depends on it, and it should be measured at the intended drain voltage and temperature.
5. **Input capacitance.** The datasheets of LMP7721, LMC6001 and LMC662 do not specify it, and the model uses 8 pF for them. The designs with these parts therefore carry an unknown error in their $e_n\,\omega C$ term.
6. **The excess noise of logarithmic amplifiers at low currents.** AD8304's measured noise and its macromodel lie 5–20 times above the shot-noise bound of Eq. (35) at 1–100 nA, and the measured spectra rise towards the edge of the bandwidth (Section 9.6). The mechanism inside the amplifier was not identified. A low-noise logarithmic front end would need it.
7. **The application sections of the ADA4530-1 data sheet** on contamination, cleaning and handling, solder paste, guard planes, via fences, cables and connectors (pp. 37–43) were not read in detail. They would add practical rules to Chapter 8.
8. **Parts not read.** The OPA128 electrometer, whose data-sheet link returned an error, and AD549 were not read. OPA128 appears only through TI's application note SBOA061.
9. **The flicker noise of LTC6268-10** is estimated from its 0.1–10 Hz peak-to-peak value (Appendix B.1). Its datasheet curve below 20 kHz, if one exists in a later revision, should replace the estimate.
10. **The high-frequency current noise of FET-input op amps.** Where the model adds a datasheet curve to $e_n\,\omega C_T$, it may count the same mechanism twice. Where a part has no curve, the model holds $i_n$ flat and may undercount. Both matter only at 100 kΩ–10 MΩ with megahertz bandwidths.
11. **The voltage noise of OPA827 below 1 kHz** is not in its specification table. The model continues it nearly flat from the 1-kHz and 10-kHz values, which underestimates any flicker noise.
12. **The offset of LMC6001A.** Its specification-table row could not be read unambiguously, so its DC errors are not given.
13. **The voltage and temperature coefficients of high-value resistors**, which matter when 10 V lies across 1 GΩ, were not taken from any resistor datasheet.
14. **The Art of Electronics x-chapter on transimpedance amplifiers** could not be downloaded, because its host's TLS certificate had expired, and it was not consulted.
15. **The capacitive coupled voltage divider** of Seidl, Knorr and Zimmermann [[A7]](https://doi.org/10.1049/el:20031162), [[A8]](https://doi.org/10.1109/ISSCC.2004.1332798) was not read. It is the lumped predecessor of the integrated resistor of Section 3.4, and it may contain the guarded junction of a split resistor in integrated form.
16. **The split resistor with guarded junctions** of Section 3.4 has not been simulated or built. A SPICE run with three resistors, their pad capacitances and the guard divider would test it, including its sensitivity to mismatched end-to-end capacitances, and a board measurement with the injection method of Section 3.5 would confirm it.
17. **The noise of the ADA4817-1 macromodel** exceeds its data sheet: 16.2 against 11.8 nV/√Hz at 1 kHz, and 33 fA/√Hz of current noise at 10 Hz (Section 9.3). Which of the two describes the part could only be settled by a measurement.
18. **The composite's second stage** was ideal in SPICE (Section 9.5), because the DC solver latched with an op amp's macromodel in its place. The second stage's own noise, estimated at about 0.3 dB of excess, and its overload and recovery were therefore not checked.
19. **The gain–bandwidth of OPA211.** The model uses its unity-gain bandwidth, 45 MHz, although its data sheet also gives 80 MHz at a gain of 100 (Appendix B.1). For OPA1656 and OPA2156, which showed the same pattern, their SPICE models settled the question in favour of the value at a gain of 100 (Section 9.2). OPA211, a bipolar part, matters only at the lowest gains, so its value was not checked.
20. **The current noise of CMOS inputs.** For LMC662 the data sheet's own revision history shows that its current-noise figure follows the test setup, and the model uses the earlier, lower value (Section 2.3). Other CMOS data sheets also give current noise well above the shot noise of the part's own typical bias current, $\sqrt{2qI_{B,\mathrm{typ}}}$: OPA1656 6 fA/√Hz against 1.8 fA/√Hz for 10 pA, OPA2156 19 fA/√Hz against 1.3 fA/√Hz for 5 pA, and OPA320 0.6 fA/√Hz against 0.25 fA/√Hz for 0.2 pA. Whether these figures are also limited by the test setup could only be settled by measurement. At the gains of this note it matters for OPA1656 and OPA2156 above about 100 MΩ, where their current noise sets their excess noise.
21. **The first opto-electronic feedback preamplifier** of Goulding, Walton and Malone [A9] was not read. Section 7.3 describes the optical reset from two later reports of the same laboratory [A10], [A11].
22. **Low-frequency noise (Section 6.8).** Below the first point of its datasheet data the model holds an amplifier's voltage noise flat: LMC662 and LMC6001A from 1 kHz, OPA381 from 10 kHz, and OPA656 and the BF862 composite from 100 kHz. Their entries in Tables A.8a–b are therefore lower bounds, which the noise curves of their datasheets, where they exist, would replace. The current noise of the CMOS parts below 1 kHz (item 20), the noise index of the feedback resistor chosen and the low-frequency noise of a biased photodiode are not known here.

## Appendix D. References

**Photodiodes**

- [P1] Hamamatsu Photonics, Si photodiodes S1336 series, Cat. No. KSPD1022E09, Jul. 2023.
- [P2] Hamamatsu Photonics, InGaAs PIN photodiodes G12180 series, Cat. No. KIRD1121E11, Feb. 2024.
- [P3] Hamamatsu Photonics, InGaAs PIN photodiodes G12183 series, Cat. No. KIRD1119E10, Feb. 2025.
- [P4] Hamamatsu Photonics, Si PIN photodiodes S3204-08/S3584-08 series, Cat. No. KPIN1051E10, Jan. 2012.
- [P5] Hamamatsu Photonics, Si photodiodes, technical note, Cat. No. KSPD9001E04, Dec. 2025.

**Amplifiers, front-end devices, logarithmic amplifiers and integrators**

- [D1] Analog Devices, ADA4530-1 data sheet, Rev. C.
- [D2] Texas Instruments, OPA928 data sheet, revised Apr. 2024.
- [D3] Texas Instruments, LMP7721 data sheet, revised Dec. 2014.
- [D4] Texas Instruments, LMC6001 data sheet, SNOS694I, Sep. 2015.
- [D5] Texas Instruments, LMC66x data sheet, revised Feb. 2024.
- [D6] Analog Devices, ADA4625-1/ADA4625-2 data sheet, Rev. C.
- [D7] Texas Instruments, OPA828 data sheet, SBOS671D, Dec. 2022.
- [D8] Texas Instruments, OPA827 data sheet, SBOS376I, Jul. 2016.
- [D9] Texas Instruments, OPA140 data sheet, SBOS498F, Mar. 2023.
- [D10] Texas Instruments, OPA145 data sheet, SBOS427F, Mar. 2021.
- [D11] Texas Instruments, OPA1656 data sheet, SBOS901C, Sep. 2022.
- [D12] Texas Instruments, OPA2156 data sheet, SBOS900B, Jun. 2019.
- [D13] Texas Instruments, OPA320 data sheet, SBOS513F, Dec. 2016.
- [D14] Texas Instruments, OPA381 data sheet, SBOS313B, Nov. 2004.
- [D15] Texas Instruments, OPA388 data sheet, SBOS777D, Jul. 2020.
- [D16] Texas Instruments, OPA656 data sheet, SBOS196I, Feb. 2024.
- [D17] Texas Instruments, OPA211 data sheet, SBOS377L, Jan. 2020.
- [D18] Linear Technology (Analog Devices), LTC6268-10/LTC6269-10 data sheet, 626810f, Rev. F, Apr. 2015, through the companion note's record.
- [D19] Texas Instruments, OPA657 data sheet, SBOS197F, Aug. 2015, through the companion note's record.
- [D20] Texas Instruments, OPA818 data sheet, SBOS940B, Dec. 2025, through the companion note's record.
- [D21] Analog Devices, ADA4817-1/ADA4817-2 data sheet, Rev. A, Mar. 2009, through the companion note's record.
- [D22] InterFET, IF3601 data sheet, IF35076-R01, Apr. 2022.
- [D23] Linear Integrated Systems, LSK170 data sheet, Doc. 201110 Rev. A22, Nov. 2019.
- [D24] NXP, BF862 product specification, Jan. 2000, through the companion note's device table.
- [D25] Texas Instruments, LOG112/LOG2112 data sheet, SBOS246D, Apr. 2005.
- [D26] Texas Instruments, LOG114 data sheet, SBOS301C, Dec. 2025.
- [D27] Texas Instruments, DDC264 data sheet, SBAS368D, Dec. 2016.
- [D28] Texas Instruments, OPT101 data sheet, SBBS002B, Jun. 2015.
- [D29] Analog Devices, AD8304 data sheet, Rev. A, Aug. 2002.
- [D30] Analog Devices, ADL5303 data sheet, Rev. D, Oct. 2020.
- [D31] Burr-Brown (Texas Instruments), IVC102 data sheet, PDS-1329A, Jun. 1996, TI literature number SBFS009.

**Application notes and articles**

- [A1] *Comparison of Noise Performance Between a FET Transimpedance Amplifier and a Switched Integrator*, Burr-Brown/Texas Instruments SBOA034. https://www.ti.com/lit/pdf/sboa034
- [A2] *Designing Photodiode Amplifier Circuits with OPA128* (AB-077), Burr-Brown/Texas Instruments SBOA061. https://www.ti.com/lit/pdf/sboa061
- [A3] S. Cherian, *What You Need to Know about Transimpedance Amplifiers – Part 1*, Texas Instruments SSZTBC4. https://www.ti.com/lit/pdf/ssztbc4
- [A4] P. C. D. Hobbs, "Photodiode front ends: the REAL story", *Optics & Photonics News* 12(4), 42–45 (April 2001); the publisher's online library numbers the pages 44–47. https://doi.org/10.1364/OPN.12.4.000044
- [A5] J. Knorr and H. Zimmermann, "A transmission-line approach for modeling feedback resistors in integrated transimpedance amplifiers", *IEEE Transactions on Circuits and Systems I: Fundamental Theory and Applications* 50(9), 1192–1196 (2003). https://doi.org/10.1109/TCSI.2003.816322. Only the abstract was read (Appendix C, item 2).
- [A6] C. Seidl, R. Swoboda and H. Zimmermann, "Optical receiver IC with capacitive coupled distributed resistors resulting in effectively reduced parasitic capacitance", *Electronics Letters* 41(23), 1301–1302 (2005). https://doi.org/10.1049/el:20053310
- [A7] C. Seidl, J. Knorr and H. Zimmermann, "Simple feedback network for bandwidth enhancement of transimpedance amplifiers", *Electronics Letters* 39(25), 1849–1851 (2003). https://doi.org/10.1049/el:20031162. Not read (Appendix C, item 15).
- [A8] C. Seidl, J. Knorr and H. Zimmermann, "Single-stage 378 MHz 178 kΩ transimpedance amplifier with capacitive-coupled voltage dividers", *IEEE International Solid-State Circuits Conference*, 2004, pp. 470–471. https://doi.org/10.1109/ISSCC.2004.1332798. Not read (Appendix C, item 15).
- [A9] F. S. Goulding, J. T. Walton and D. F. Malone, "An opto-electronic feedback preamplifier for high-resolution nuclear spectroscopy", *Nuclear Instruments and Methods* 71, 273–279 (1969). https://doi.org/10.1016/0029-554X%2869%2990314-0. Read only by its title (Appendix C, item 21).
- [A10] D. A. Landis, N. W. Madden and F. S. Goulding, "Energy-dependent losses in pulsed-feedback preamplifiers", *IEEE Transactions on Nuclear Science* 26(1), 428–432 (1979). https://doi.org/10.1109/TNS.1979.4329670. Read as the laboratory report LBL-8135 (November 1978), https://www.osti.gov/servlets/purl/6257751, whose page numbers the text cites.
- [A11] D. A. Landis, C. P. Cork, N. W. Madden and F. S. Goulding, "Transistor reset preamplifier for high rate high resolution spectroscopy", *IEEE Transactions on Nuclear Science* 29(1), 619–624 (1982). https://doi.org/10.1109/TNS.1982.4335922. Read as the laboratory report LBL-13214 (1981), https://www.osti.gov/servlets/purl/5804423, whose page numbers the text cites.

**SPICE models and simulators** (Chapter 9)

- Texas Instruments PSpice models: OPA928 (SBOMCC0, Rev. A), OPA140 (SBOM493, Rev. D), OPA828 (SBOMAJ0, Rev. D), OPA320 (SBOM437, Rev. G, file `OPAx320-Q1.LIB`), OPA1656 (SBOMAW6, Rev. C), OPA2156 (SBOMAR0, Rev. B), OPA818 (SBOMB74B) and OPA657 (SBOM137, Rev. F).
- Analog Devices: the ADA4817-1 model, Rev. 2.1, which the companion note's folder of this repository includes, and the models of the LTspice library: ADA4530-1 (`ADI1.lib`), ADA4625-1 (`ADA4625-1.sub`), LTC6268-10 (`LTC2.lib`), AD8304 (`AD8304.lib`) and ADL5303 (`ADL5303.sub`).
- Linear Integrated Systems: the published LSBF862 model card, as typed in the companion note's scripts.
- ngspice-46, as the shared library installed with KiCad 10, and LTspice from Analog Devices, run headless.

**Companion note**

- [C1] *Operational amplifiers for a balanced-photodiode transimpedance amplifier: 1 pF, 1.5–2 kΩ, ≥ 150 MHz, 0.1–10 mA of DC photocurrent*, design study and amplifier survey, October–November 2026.

## Appendix E. Files

| Path | Contents |
|---|---|
| `TIA_high_gain_survey.md` | This note, assembled from `parts/` by `scripts_archive/assemble_note.py` |
| `TIA_high_gain_survey.pdf`, `index.html` | This note as a PDF and as a web page, built by `build/build_pdf.py` and `build/make_web_html.py` at the root of the repository |
| `parts/` | The chapters as separate files, the source of the note |
| `figures/` | Figures 1–23 as PNG (600 dpi) and PDF. The plots keep the names under which they were first drawn: `fig1`–`fig5` are Figures 2, 3, 5, 10 and 11, and `fig6`–`fig12` are Figures 17–23. The schematics are the files `schem_*` |
| `data/photodiodes.json` | The photodiode examples of Table 1 with their pages |
| `data/amplifiers.json` | The amplifier data of Table A.1 with their pages, including the DC open-loop gains |
| `data/results/` | The output of the analysis scripts: `designs.json`, `gain_table.json`, `amp_merits.json`, `numbers.json` and `tables.md` |
| `data/results/note_tables/` | The table bodies that `assemble_note.py` inserts into the chapters |
| `spice/models/` | The vendors' SPICE models, one folder per part. They are not part of the public repository, which holds only `spice/models/README.md` with the source of each |
| `spice/results/` | The summaries of the SPICE checks of Chapter 9 |
| `spice/runs/` | The decks, logs and arrays of each SPICE run, written when the checks are run; not part of the public repository |
| `scripts_archive/` | The model, the analysis, the SPICE checks, the figures and the PDF tools, indexed in `scripts_archive/README.md` |
| `datasheets/`, `appnotes/`, `papers/` | The datasheets, application notes and papers read for this note; not part of the public repository (Appendix D gives each document's source) |

---
