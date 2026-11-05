# Feedback networks in eight-lead packages and under guard rings

Side note to the two transimpedance-amplifier notes: field solutions of SOIC-8 and PDIP-8 layouts, guarded feedback resistors as distributed lines, and the inductance of the leads.

> This note was created with significant AI assistance. It may contain errors, so check the cited datasheet pages, tables and scripts before relying on a figure. The note itself is dedicated to the public domain under CC0 1.0; no copyright is reserved.

## 1. What this note adds to the two notes

The capacitance across the feedback resistor sets the bandwidth of a transimpedance amplifier (TIA) wherever the resistor, rather than the amplifier, limits it, and it decides how large an external feedback capacitor every other design needs. Both notes of this repository take that capacitance from particular layouts. The [balanced-photodiode note](../TIA_opamp_survey_2026-10-25/TIA_opamp_survey.md) computes it with finite-element field solutions for an 0402 or 0603 resistor beside the OPA855 and around the OPA846 in its SOT-23-5 package (its Sections G.14.9 and G.14.10), and its designs use 0.08 pF with corners at 0.05 and 0.12 pF (its Table 1.1). The [high-gain note](../TIA_high_gain_survey_2026-11-02/TIA_high_gain_survey.md) assumes 0.1 pF for its sweeps. It also treats the resistor as a distributed RC line, with an end-to-end capacitance $C_{ee}$ and a capacitance $C_g$ from the resistive film to the conductor beneath it, which it estimates with parallel plates and lists as still to be measured (its Section 3.4 and its Appendix C, item 3).

Three questions were left open, and this note answers them with the same solver, the finite-element package pcbcap at the root of this repository, and the same conventions.

1. The OPA846 also comes in an SO-8 package (data sheet [1], p. 2). Does that package change the capacitance of the balanced-photodiode note's Section G.14.10?
2. The precision and electrometer amplifiers of the high-gain note come in SOIC-8 and PDIP-8 packages, and their data sheets show guard rings that surround the summing node and pass under the feedback resistor. What capacitance do such layouts have, and what does a guard under the resistor do to its response and to its noise?
3. Both notes compute electrostatic capacitances, which leave out every inductance. The leads of SOIC-8 and PDIP-8 packages are longer than those of the SOT-23-5. Can their inductance still be left out?

The answers, with the sections that derive them, are these.

- **The OPA846 in SO-8** has 56.1 fF across its feedback network with the resistor, an 0402, under the package, the same as the 56.0 fF of the SOT-23-5. With the resistor beyond the package it has 57.5 fF, against 72.0 fF for the SOT-23-5 counterpart. Moving the vias from the pads to under the body raises the first value to 66.5 fF (Section 3).
- **The inductance of the leads** changes the effect of the feedback capacitance at the 308-MHz loop crossover of the balanced-photodiode note's 2-kΩ OPA846 design by 2.3 % in SOT-23-5, 2.9 % in SOIC-8 and 4.0 % in PDIP-8, far less than the ±13 % tolerance of that capacitance. In the high-gain range it stays below 1 % for loop crossovers up to 133–559 MHz, far above the crossovers of the amplifiers that come in these packages (Section 4).
- **High-gain layouts without a guard** give 93.3 fF for the OPA637 in SOIC-8 with an 0805 resistor and 88.4 fF for the LMC6001 in PDIP-8 with a 1206 resistor, which supports the high-gain note's 0.1 pF (Section 5).
- **A guard that passes under the resistor** lowers the first-order capacitance to 11.6–27.4 fF, but it couples 169–176 fF to the film, six to fifteen times as much. At its own corner the resistor is then a distributed line. Its bandwidth is 0.58–0.84 of the corner that the first-order capacitance predicts, as if the capacitance were 20.0–32.7 fF; its response rises by at most 0.63 dB before it falls; and its Johnson noise rises by 1.0–1.8 dB at the predicted corner and by 0.5–1.0 dB averaged over the band. Against the same PDIP-8 layout without a guard, the guard still widens the band 2.7 times (Sections 6 and 7.2).
- **Whether the amplifier matters** depends on the gain. Far above the crossover gain of the high-gain note's Eq. (20), 4.0–9.5 GΩ for these layouts with their amplifiers on its 20-pF photodiode, the network alone sets the TIA's response. Below it the amplifier sets the response and the network its damping: an external feedback capacitor sized from the first-order value then overdamps the loop and gives 7–35 % less bandwidth than the design intends (Section 7.3).

Section 8 states what each of the two notes takes from these results. Every three-dimensional layout of this note can also be turned and zoomed on an interactive page of its own, which Appendix A lists.

## 2. The models

The capacitance between two nets depends on every conductor near them, so each package is modelled from its drawing, at the middle of each tolerance, as the balanced-photodiode note's Section G.14.10 does for the SOT-23-5. This section states the dimensions, the boards and the mesh, and two checks of the mesh.

### 2.1 The two packages

Table 1 lists the dimensions of the two package models and the drawings they come from. The SOIC-8 follows TI's drawing D0008A (4214825/C), on p. 29 of the OPA846 data sheet [1] with the example land pattern on p. 30; the same drawing is in the data sheets of the LMC662 [5, p. 30], the LMP7721 [3, p. 32] and the OPA627/OPA637 [6, p. 43]. TI gives no lower limit of the package height, so the body's thickness is taken from Analog Devices' drawing of the same JEDEC outline (MS-012), which gives a height of 1.35–1.75 mm [2, p. 52, Figure 139]: its midpoint, 1.55 mm, less the stand-off of 0.18 mm. The PDIP-8 follows TI's drawing P (R-PDIP-T8, 4040082/E), on p. 33 of the LMC662 data sheet [5] and p. 25 of the LMC6001 data sheet [4]. TI does not dimension the body's thickness either; Analog Devices' drawing of the same JEDEC outline (MS-001) gives 2.92–4.95 mm with 3.30 mm nominal [7, p. 19, Figure 50], and the nominal value is taken.

*Table 1. The two package models (mm): the range that each drawing gives and the value used. The pitch, the rows and the lead dimensions are those of the leads outside the body.*

| Dimension | SOIC-8, drawing | SOIC-8, model | PDIP-8, drawing | PDIP-8, model |
|---|---|---|---|---|
| Body, length × width | 4.81–5.00 × 3.81–3.98 | 4.905 × 3.895 | 9.02–10.16 × 6.10–6.60 | 9.59 × 6.35 |
| Body thickness | not given; height at most 1.75 | 1.37 | not given; seated height at most 5.08 | 3.30 |
| Stand-off | 0.11–0.25 | 0.18 | at least 0.51 | 0.51 |
| Pitch | 1.27 | 1.27 | 2.54 | 2.54 |
| Across the rows | 5.80–6.19 from tip to tip | 5.995 | 7.62–8.26 at the gauge plane | 7.62 between the leads' centre lines |
| Lead width × thickness | 0.31–0.51 × 0.13–0.25 | 0.41 × 0.19 | shoulder 1.14–1.78, pin 0.38–0.53; thickness 0.25 | 1.46 and 0.455; 0.25 |
| Foot, or lead below the seating plane | foot 0.41–1.27 | 0.84 | at least 3.18 | 3.18 |
| Land pattern | pads 1.55 × 0.6, rows 5.4 apart (TI's example) | the same | not given | holes of 0.8 drill, round pads of 1.6 |

Each gull-wing lead of the SOIC-8 is built like those of the SOT-23-5: a foot on its pad, a riser at the inner end of the foot, and a shoulder from the body's side, at half the body's thickness. Each PDIP-8 lead is a horizontal exit from the body, a vertical shoulder down to the seating plane, on which the package stands, and a narrow pin through the plated hole and out below the board. The lead frame, the die and the bond wires inside the body are left out, as for the SOT-23-5, because no drawing gives them (the balanced-photodiode note's Section G.11). A round hole filled with solder around its lead is modelled as a square of the same far field. The balanced-photodiode note's Eq. (G.58) gives that square's side as $s = 0.8472\,d$, which is 0.678 mm for the 0.8-mm drill. Each round pad becomes the square of the same area, with the side $d_{pad}\sqrt{\pi}/2$ = 1.6 mm × 0.8862 = 1.418 mm, which keeps the pad's capacitance to a nearby plane.

### 2.2 Resistors, boards and nets

The OPA846 layouts carry an 0402 resistor, as in the balanced-photodiode note's 2-kΩ designs. The high-gain layouts carry a 1206, the size of the high-gain note's own estimate (its Section 3.4), except the OPA637 layout, which keeps an 0805, because its vias at the inner ends of the pads of pins 2 and 6 would land on the pads of a 1206. The 1206 body follows the rule of the balanced-photodiode note's Table G.2: 3.20 × 1.60 mm, 0.55 mm thick with 0.45 and 0.70 mm as corners, and terminations wrapping 0.45 mm onto the top face. These are the values most of five makers print: Panasonic ERJ (AOA0000C301, p. 3), Yageo RC (RC_L V.14, p. 4, Table 1), Vishay CRCW (20035, p. 11), KOA RK73B (p. 1) and TT Electronics WCR (p. 1). Its pads are those of the IPC-7351 table of Vishay document 28950 (Rev. 12-Jul-2022, p. 1): 1.15 mm long and 1.80 mm wide, 1.75 mm apart. The repository's file `TIA_opamp_survey_2026-10-25/data/parasitic_cf/geometry_and_permittivity.md` lists every value with its page.

The OPA846 layouts lie on the four-layer FR-4 board of the balanced-photodiode note's Section G.14.10, 1.6 mm thick with ground planes 0.2 mm inside each face, which are cut away 0.5 mm beyond the package's pads and the network. The high-gain layouts lie on a two-layer board with no plane near the network, the usual practice around a high-impedance input. Each layout sits in a grounded box: 16 mm wide for the SOIC-8 layouts and 24 mm wide for the PDIP-8 ones, with 8 or 12 mm of air above and below the board.

In every layout the net A is the amplifier's output and the net B its inverting input, the summing node. The non-inverting input, both supplies and every guard are at AC ground: in a TIA the guard is held at the potential of the non-inverting input. Each pin with no internal connection is a floating conductor of its own. The following are assumptions, because no document dimensions them: traces 0.2 mm wide, 0.3 mm of clearance, vias with a 0.3-mm drill and pads 0.55 mm wide, the resistor's body 30 µm above its pads, and guard rings 0.3 mm wide with 0.3 mm of clearance to the summing node's copper.

### 2.3 The mesh, and two checks of it

The leads, holes, traces and guard rings of these packages are several times longer than those of the SOT-23-5 network, and at the element sizes of the balanced-photodiode note's Section G.14.10 they would need 1.4–2.5 million elements, more than the workstation's memory allows. Every conductor except the resistor therefore gets coarser edges than in that section: 7.5 µm times the mesh's refinement factor, which is 5.66 for the OPA846 layouts, 11.3 for the SOIC-8 high-gain layouts and 16 for the PDIP-8 layouts. The resistor, its pads and its solder keep the 15-µm edges of that section, because most of the coupling lies there. The meshes have 0.70–1.09 million elements.

Two checks measure what these choices change. The SOT-23-5 layout (a) of the balanced-photodiode note's Table G.14, solved with the coarse edges, gives 56.15 fF against the published 56.03 fF, 0.21 % more, and capacitances to ground 0.4 % above the published ones, with 0.58 instead of 1.08 million elements. The OPA637 layout solved at refinement 16 instead of 11.3 gives 93.38 fF against 93.29 fF, 0.1 % more. Each value of this note comes from one mesh, and an error of a few tenths of a percent is expected, as in the balanced-photodiode note's Section G.14.10.

## 3. The OPA846 in SO-8

The balanced-photodiode note computes its 2-kΩ OPA846 design in the SOT-23-5 package. The amplifier also comes in SO-8 [1, p. 2], whose wider body leaves more room between the pins, so the routing of the feedback network can change. Figure 1 shows three layouts with the standard pinout of a single amplifier: pin 2 the inverting input, pin 3 the non-inverting input, pin 4 the negative supply, pin 6 the output, pin 7 the positive supply, and pins 1, 5 and 8 not connected.

- **Layout (a)** puts the resistor on the bottom side, centred under the package, reached through vias at the inner ends of the pads of pins 2 and 6. This is what the data sheet advises for boards with parts on both sides [1, p. 18, item c], and it is the SO-8 counterpart of the SOT-23-5 layout (a).
- **Layout (b)** is the same with the vias under the body, 0.3 mm inside the inner ends of the pads, each joined to its pad by a short trace. In layout (a) the vias lie in the pads, under the solder paste, and TI's land-pattern notes ask for such vias to be filled, plugged or tented [8, p. 39, note 5]; vias beside the pads under the body are covered by the solder mask and need nothing special.
- **Layout (c)** puts the resistor on the top side, beyond the end of the package at pins 4 and 5, with a trace from each of pins 2 and 6 running inward under the body and along it to the resistor. It is the SO-8 counterpart of the SOT-23-5 layout (b).

![Figure 1](figures/fig1_opa846_so8.png)

*Figure 1. The OPA846 in SO-8 with its feedback resistor, an 0402, in the three layouts of Section 3: (a) on the bottom side under the package, through vias in the pads of pins 2 and 6; (b) the same with the vias under the body; (c) on the top side beyond pins 4 and 5, with a trace from each of pins 2 and 6 under the body. The output's net is red, the summing node's net blue, the grounded pins dark grey and the unconnected pins mid grey; the film is purple, and the board with its two planes (green) and the package's mould (brown) are drawn translucent. Lengths in mm; $z$ is measured up from the board's top surface. (d) $C_F$ of each layout beside its SOT-23-5 counterpart from the balanced-photodiode note's Table G.14.*

Table 2 gives the results. The resistor's own share of the coupling, the part that lies in its alumina body, is the same 21.5 fF in all three layouts; the routing makes the differences, as in the SOT-23-5.

*Table 2. The OPA846 in SO-8 with an 0402 (fF): $C_F$, the capacitance across the feedback network, beside its SOT-23-5 counterpart; the capacitances to ground of the output's net ($C_{A0}$) and of the summing node's net ($C_{B0}$); and the shares of $C_F$ that lie in the board, the resistor's alumina, the mould and the air. One mesh each, 0.85–0.92 million elements.*

| Layout | $C_F$ | SOT-23-5 counterpart | $C_{A0}$ | $C_{B0}$ | Board, alumina, mould, air |
|---|---|---|---|---|---|
| (a) under the package, vias in the pads | 56.1 | 56.0 | 304 | 304 | 25.1, 21.5, 3.0, 6.4 |
| (b) under the package, vias under the body | 66.5 | – | 297 | 298 | 34.5, 21.5, 3.6, 6.9 |
| (c) beyond the package, traces under the body | 57.5 | 72.0 | 286 | 363 | 24.1, 21.5, 5.6, 6.3 |

Three points follow.

- **With the resistor under the package, the package type makes no difference.** Layout (a) gives 56.1 fF in SO-8 and 56.0 fF in SOT-23-5: the resistor and its vias dominate, and both packages put them at similar distances.
- **Vias under the body cost 10 fF.** In layout (b) the two via barrels, one of each net, stand 2.7 mm apart through the board instead of 4.4 mm, and the board's share rises from 25.1 to 34.5 fF. Vias in the pads, filled or tented, give the lower value.
- **The wider body helps the top-side layout.** In layout (c) the two traces run under the body along opposite rows of pins, 2.65 mm apart, and $C_F$ is 57.5 fF. In the SOT-23-5 counterpart the trace from the resistor's far pad passes 0.40 mm from the output pin's pad, and $C_F$ is 72.0 fF (the balanced-photodiode note's Section G.14.10). The price in SO-8 is a larger capacitance at the summing node, 363 fF, because the summing node's trace runs beside the grounded pins 3 and 4.

All three values lie inside the 53–72 fF of the SOT-23-5 layouts, so the nominal 0.08 pF of the balanced-photodiode note's Table 1.1, with its corners at 0.05 and 0.12 pF, holds for the SO-8 as well.

## 4. The inductance of the leads

The field solutions are electrostatic: they contain no magnetic field and therefore no inductance (the balanced-photodiode note's Section G.14.1). That is adequate while the inductance in the path of the feedback current is too small to change the feedback network at the loop's crossover frequency, where the feedback capacitance sets the phase margin. The leads of SOIC-8 and PDIP-8 packages are longer than those of the SOT-23-5, so this section estimates their inductance and its effect.

**What a series inductance does.** Between the output pin and the summing-node pin, the feedback network $R_F \parallel C_F$ lies in series with the inductance $L_x$ of its connections: traces, vias, the leads outside the body, and the lead frame and bond wire inside it. With $1/Z_F = 1/R_F + j\omega C_F$, the network that the amplifier sees is $Z_F' = Z_F + j\omega L_x$, and

$$
\frac{Z_F'}{Z_F} = 1 + j\omega L_x\left(\frac{1}{R_F} + j\omega C_F\right) = 1 - \omega^2 L_xC_F + j\,\frac{\omega L_x}{R_F} .
\tag{1}
$$

Two small numbers therefore measure the change:

$$
\delta_1 = \omega^2 L_xC_F , \qquad \delta_2 = \frac{\omega L_x}{R_F} .
\tag{2}
$$

The first is the fractional change of the capacitive part: the capacitance looks larger by the factor $1/(1 - \delta_1)$. The second is the phase added, in radians. Both are evaluated at the loop crossover.

**The inductance of a straight conductor.** A lead or trace is a chain of straight segments, and the inductance of the path is estimated as the sum of their partial self-inductances, which the Neumann formula gives. Two parallel filaments of length $l$ that lie side by side over the same span, a distance $d$ apart, have the partial mutual inductance

$$
M(l, d) = \frac{\mu_0}{4\pi}\int_0^l\!\!\int_0^l \frac{\mathrm dx\,\mathrm dx'}{\sqrt{(x - x')^2 + d^2}}
= \frac{\mu_0}{2\pi}\left[\,l\,\mathrm{asinh}\frac{l}{d} - \sqrt{l^2 + d^2} + d\,\right] ,
\tag{3}
$$

where the inner integral is $\mathrm{asinh}((l - x)/d) + \mathrm{asinh}(x/d)$, the substitution $x \to l - x$ makes the two terms equal, and $x\,\mathrm{asinh}(x/d) - \sqrt{x^2 + d^2}$ is an antiderivative of $\mathrm{asinh}(x/d)$. A conductor of finite cross-section is a bundle of such filaments, and its partial self-inductance is the average of $M$ over pairs of points of its cross-section. For a thin strip of width $w$ with uniform current, the distance $s$ between two random points of the width has the density $2(w - s)/w^2$, and for a thin-walled tube of radius $a$ two points at the angle $\psi$ apart are the chord $2a\sin(\psi/2)$ apart, with $\psi$ uniform:

$$
L_{strip}(l, w) = \int_0^w \frac{2(w - s)}{w^2}\,M(l, s)\,\mathrm ds , \qquad
L_{tube}(l, a) = \frac{1}{2\pi}\int_0^{2\pi} M\!\left(l,\ 2a\sin\frac{\psi}{2}\right)\mathrm d\psi .
\tag{4}
$$

The sum of partial self-inductances is an estimate on the high side. The strip's zero thickness and uniform current both make $L_{strip}$ larger than the true value. The mutual inductance between the parallel segments of the path out to the resistor and the path back from it, which carry opposite currents, would subtract. The return current in the planes and the bypass network would subtract as well.

**The leads.** The current enters a gull-wing lead along its soldered foot, so half the foot is counted; then the riser, from the pad up to the middle of the shoulder; then the stretch of shoulder outside the body. Each is a strip of the lead's width. In a PDIP-8 lead with the network on the solder side, the current runs up the filled hole, a tube of the hole's radius through the 1.6-mm board, then up the shoulder from the seating plane to the exit, and along the exit to the body, each a strip of the shoulder's width. Equation (4) with the dimensions of Table 1 gives 0.266 nH per lead of the SOT-23-5, 0.546 nH per lead of the SOIC-8 and 1.361 nH per lead of the PDIP-8 (Table 3). No drawing dimensions the lead frame and bond wire inside the body. TI's model of the OPA846 puts 2.35 nH at its inverting input (the balanced-photodiode note's Table B.1), and that value is taken for each of the two pins in every package, as an assumption.

*Table 3. Partial self-inductance of one lead outside the body, by Eq. (4), with the dimensions of Table 1 and of the SOT-23-5 model of the balanced-photodiode note's Section G.14.10.*

| Package | Segments of one lead (length × width or radius, mm) | Inductance (nH) |
|---|---|---|
| SOT-23-5 | half the foot 0.225 × 0.40: 0.049; riser 0.600 × 0.40: 0.216 | 0.266 |
| SOIC-8 | half the foot 0.420 × 0.41: 0.126; riser 0.960 × 0.41: 0.418; shoulder outside the body 0.020 × 0.41: 0.001 | 0.546 |
| PDIP-8 | filled hole, a tube 1.600 long of radius 0.400: 0.438; shoulder 2.285 × 1.46: 0.840; exit 0.510 × 1.46: 0.084 | 1.361 |

**The 2-kΩ OPA846 design.** The balanced-photodiode note's OPA846 design has $R_F$ = 2 kΩ, a total feedback capacitance of 0.75 pF (its Table 4.1) and a loop crossover of 308 MHz in SPICE (its Section 4.5). With the routing of layout (a) in each package, both leads and both internal allowances, $L_x$ is 8.11 nH in SOT-23-5, 10.14 nH in SOIC-8 (4.35 nH of traces and vias, 2 × 0.55 nH of leads and 2 × 2.35 nH inside) and 14.37 nH in PDIP-8 (6.94 nH of traces under the package, 2 × 1.36 nH and 2 × 2.35 nH; a PDIP-8 version of the 2-kΩ network with an 0402 on the solder side). For the SOIC-8, Eq. (2) gives

$$
\delta_1 = (2\pi\times308\ \mathrm{MHz})^2\times10.14\ \mathrm{nH}\times0.75\ \mathrm{pF} = 0.0285 ,
\qquad
\delta_2 = \frac{2\pi\times308\ \mathrm{MHz}\times10.14\ \mathrm{nH}}{2\ \mathrm{k\Omega}} = 0.0098\ \mathrm{rad} ,
\tag{5}
$$

that is 2.85 % and 0.56°. The same arithmetic gives 2.28 % for the SOT-23-5 and 4.03 % and 0.80° for the PDIP-8. Put the other way round, $\delta_1$ stays below 1 % while $L_x \le 0.01/(\omega^2C_F)$ = 3.56 nH. The package therefore moves the effective feedback capacitance at the crossover by 2–4 %, mostly through the assumed internal allowance, while the note's designs already carry ±0.1 pF, ±13 % of 0.75 pF, as the tolerance of that capacitance (the balanced-photodiode note's Section G.15). The electrostatic values hold for these designs within that margin, and the SO-8 is no worse than the SOT-23-5 by more than 0.6 percentage points.

**The high-gain range.** The first number of Eq. (2) does not depend on $R_F$, and the second falls as $R_F$ grows, so the loop crossover decides. Setting $\delta_1$ = 0.01 gives the crossover frequency below which the inductance changes the feedback capacitance by less than 1 %:

$$
f_{1\%} = \frac{1}{2\pi}\sqrt{\frac{0.01}{L_xC_F}} .
\tag{6}
$$

For the PDIP-8 with $C_F$ = 1 pF it is $\sqrt{0.01/(14.37\ \mathrm{nH}\times1\ \mathrm{pF})}/(2\pi)$ = 133 MHz. Table 4 gives the rest. A loop crosses over at $f_c = GBW\,C_F/(C_F + C_T)$, below the amplifier's gain–bandwidth product $GBW$, because at high frequency the feedback factor is the capacitive divider $C_F/(C_F + C_T)$, where $C_T$ is the total capacitance at the summing node. The electrometers of the high-gain note have gain–bandwidth products of 1.3–17 MHz (its Table A.1), and the OPA637 has 80 MHz at a gain of 10 [6, p. 12]. Their crossovers lie far below every entry of Table 4, so the leads' inductance is negligible for them. Only the wideband FET amplifiers of the high-gain note, with 230 MHz to 4 GHz (its Section 5.5), could approach $f_{1\%}$ at its lowest gains. The phase term is negligible throughout: with the PDIP-8's $L_x$ at 80 MHz and 10 kΩ, $\delta_2$ is $7.2\times10^{-4}$ rad, 0.04°. The resistor's own inductance acts as the negative capacitance $-L_s/R^2$ in parallel with it; for an 0805, $L_s$ = 1.1 nH (KOA's Table 1, p. 3, in its technical note TN-010, the balanced-photodiode note's reference [A30]), which at 10 kΩ is 0.011 fF, 0.014 % of its capacitance.

*Table 4. The loop crossover frequency below which the inductance $L_x$ of the network's connections changes the feedback capacitance by less than 1 %, Eq. (6) (MHz).*

| Package, $L_x$ | $C_F$ = 0.1 pF | 0.2 pF | 0.5 pF | 1.0 pF |
|---|---|---|---|---|
| SOT-23-5, 8.11 nH | 559 | 395 | 250 | 177 |
| SOIC-8, 10.14 nH | 500 | 353 | 224 | 158 |
| PDIP-8, 14.37 nH | 420 | 297 | 188 | 133 |

## 5. High-gain layouts without a guard

The high-gain note runs its amplifier sweeps with 0.1 pF across the feedback resistor, a value consistent with measured parts and with the balanced-photodiode note's estimate (that note's Section G.15). This section checks it on two layouts with the amplifiers and packages of that range, and Figure 2 shows them.

- **The OPA637 in SOIC-8** (data sheet [6], p. 3; its PDIP-8 version is withdrawn, p. 33) carries an 0805 on the bottom side, centred under the package, reached through vias at the inner ends of the pads of pins 2 and 6.
- **The LMC6001 in PDIP-8** (data sheet [4], p. 3) carries a 1206 on the solder side between the leads of pins 2 and 6, centred under the package, with a trace from each pad.

![Figure 2](figures/fig2_high_gain_layouts.png)

*Figure 2. The high-gain layouts without a guard (Section 5), both seen from below: (a) the OPA637 in SOIC-8 with an 0805 under the package on the bottom side, reached through vias in the pads of pins 2 and 6; (b) the LMC6001 in PDIP-8 with a 1206 on the solder side between the leads of pins 2 and 6. Colours as in Figure 1. Each panel has its own scale; lengths in mm, and $z$ is measured up from the board's top surface. From below, the numbers of the $x$ and $y$ axes are left out.*

*Table 5. The high-gain layouts without a guard (fF), on a two-layer board with no plane near the network. Columns as in Table 2.*

| Layout | $C_F$ | $C_{A0}$ | $C_{B0}$ | Board, alumina, mould, air |
|---|---|---|---|---|
| OPA637, SOIC-8, 0805 under the package | 93.3 | 263 | 267 | 43.0, 39.6, 4.4, 6.2 |
| LMC6001, PDIP-8, 1206 on the solder side | 88.4 | 453 | 454 | 41.4, 30.8, 9.5, 6.7 |

Both values lie close to the high-gain note's 0.1 pF (Table 5). The board and the resistor's alumina carry about equal shares; with no plane near the network, the field lines between the two nets' traces, pads and holes run through the board, and the PDIP-8's long leads add 9.5 fF through the mould. For $R_F$ = 1 GΩ the resistor's own pole, $f_R = 1/(2\pi R_FC_F)$, lies at

$$
f_R = \frac{1}{2\pi\times1\ \mathrm{G\Omega}\times93.3\ \mathrm{fF}} = 1.71\ \mathrm{kHz}
\tag{7}
$$

for the OPA637 layout and at 1.80 kHz for the LMC6001 layout, against 1.59 kHz for 0.1 pF. These two layouts keep the network free of copper beneath the resistor. With a guard they change, as the next two sections show.

## 6. Guards under the resistor: the first-order capacitance

At the highest gains the summing node needs a guard against leakage (the high-gain note's Section 8.2). The layouts that the amplifiers' makers publish draw that guard around the whole summing node, and since one pad of the feedback resistor belongs to the summing node, the guard passes under the resistor's body between its two pads. The high-gain note's Section 3.4 warns that copper at signal ground under the film acts as a negative feedback capacitance and can make the response peak. This section computes three such layouts, which Figure 3 shows.

- **The LMC6001 in PDIP-8 with guard rings** is the layout of Section 5 with a grounded ring around the summing node on both sides of the board: on the solder side around the pad of pin 2, its trace and the resistor's input pad, passing under the resistor between its pads; on the component side around the pad of pin 2. Both rings are joined to the pad of pin 3, the non-inverting input. The LMC6001 [4, p. 19] and OPA627/OPA637 [6, p. 21] data sheets show guard rings of this kind.
- **The ADA4530-1 in SOIC-8** has a pinout of its own: pin 1 the non-inverting input, pins 2 and 7 the guard buffer's outputs, pin 3 an internal connection, left open here, pin 4 the negative supply, pin 5 the positive supply, pin 6 the output and pin 8 the inverting input [2, p. 10]. ADI's Figure 122 shows the TIA layout [2, p. 42]: the guard ring, driven from pin 7, "is extended around" the left half of the feedback resistor and of a feedback capacitor, "to ensure that the entire high impedance node is surrounded by guard". The model has the resistor, a 1206, beside the row of pins 6, 7 and 8 and parallel to it, and the guard as a ring 0.3 mm wide around pin 8, its trace and the resistor's input half; the figure's filled guard shape becomes a ring, its feedback capacitor is left out, and so are the guard plane and via fence that the data sheet describes on pp. 42–43.
- **The LMP7721 in SOIC-8** has pin 1 the non-inverting input, pins 2, 5 and 7 unconnected, pin 3 the negative supply, pin 4 the output, pin 6 the positive supply and pin 8 the inverting input [3, p. 3]. TI's Figure 54 shows a guard trace that encircles both inputs and is tied to the two unconnected pins beside them, 2 and 7, and the text beside it asks for guard traces "on both sides of the PCB" [3, p. 25]. That figure shows no feedback resistor, so the model places the 1206 as in the ADA4530-1 layout, beside pin 8 with the guard passing between its pads. The guard loop closes under the body between pins 2 and 7 and is joined between the two sides by two vias. The output, pin 4, sits at the far corner, so its trace runs around the other end of the package.

![Figure 3](figures/fig3_guarded_layouts.png)

*Figure 3. The guarded high-gain layouts (Sections 6 and 7): (a) the LMC6001 in PDIP-8 with guard rings on both sides, joined to pin 3, seen from below; (b) the ADA4530-1 in SOIC-8 with a 1206 and the guard of ADI's Figure 122, driven from pin 7; (c) the LMP7721 in SOIC-8 with a 1206 and the guard of TI's Figure 54 on both sides, tied to pins 2 and 7. The guards are dark grey, like the grounded pins; other colours as in Figure 1. Each panel has its own scale; lengths in mm, and $z$ is measured up from the board's top surface.*

*Table 6. The guarded layouts (fF), each with the LMC6001 layout without a guard for comparison. $C_F$ is the first-order capacitance, the electrostatic value with the film at its DC potential; other columns as in Table 2.*

| Layout | $C_F$ | $C_{A0}$ | $C_{B0}$ | Board, alumina, mould, air |
|---|---|---|---|---|
| LMC6001, PDIP-8, no guard (Table 5) | 88.4 | 453 | 454 | 41.4, 30.8, 9.5, 6.7 |
| LMC6001, PDIP-8, guard rings | 27.4 | 564 | 860 | 13.1, 16.4, 8.1, −10.1 |
| ADA4530-1, SOIC-8, guard of ADI's Figure 122 | 21.8 | 346 | 464 | 12.7, 18.4, 2.4, −11.7 |
| LMP7721, SOIC-8, guard of TI's Figure 54 | 11.6 | 573 | 479 | 4.6, 17.9, 1.7, −12.5 |

The guard rings cut the first-order capacitance of the PDIP-8 layout from 88.4 to 27.4 fF, by a factor of 3.2, and the two vendor layouts give 21.8 and 11.6 fF (Table 6). Two mechanisms act together. First, the guard intercepts part of the field that ran from one termination to the other through the board and the air, and turns it into capacitance from each termination to the guard. Second, the guard lies under the film at signal ground, the case $a = 0$ of the high-gain note's Eq. (26a): a stretch of film at the position $u$ from the summing-node end, with the capacitance $C_k$ to the guard, adds $-C_k\,u(1 - u)$ to the feedback capacitance, because the current it draws through $C_k$ is supplied partly through the summing node. The negative share of the air shows where both happen: there the fields that the two nets drive end on the guard and run in the same direction, so that region subtracts from $C_F$.

The guard's price at the summing node is its capacitance to ground: $C_{B0}$ of the PDIP-8 layout rises from 454 to 860 fF. That 0.41 pF adds to $C_T$; against the 20-pF photodiode of the high-gain note's examples it is 2 %.

The first-order values describe the resistor only at frequencies where the capacitance along the film draws little current. Section 7 shows that the film's capacitance to the guard is six to fifteen times these values, so at the resistor's own corner they no longer suffice.

## 7. The guarded resistor as a distributed line

The first-order capacitance is exact to first order in $\omega R_FC$, where $C$ is any capacitance that loads the film (the balanced-photodiode note's Section G.14.1). At the resistor's own corner, $\omega R_FC_F$ = 1, so a film whose capacitance to the guard, $C_g$, is several times $C_F$ has $\omega R_FC_g = C_g/C_F$ well above 1 there: it is a distributed RC line, the high-gain note's Section 3.4, with the field solution in place of the uniform line. This section computes its full response and noise, first for the network alone (Section 7.2) and then inside the amplifier's loop (Section 7.3).

### 7.1 How the film is computed

**The method.** The film is divided along its length into $n$ = 10 elements, and its potential is written as a sum of the hat functions of their nodes, so that node 0 is the summing node's termination with its whole net, node 10 the output's, and nodes 1–9 points of the film (Appendix B). One field solution per node, with that node at 1 V and everything else at 0 V, gives the 11 × 11 capacitance matrix $\mathbf C$ between the nodes; the eleven solves of one layout share one mesh of 1.03–1.23 million elements. The film's resistance gives the conductance matrix $\mathbf G$ of ten resistors $R_F/10$ in a chain. At the angular frequency $\omega$ the nodes obey $(\mathbf G + j\omega\mathbf C)\,\mathbf V = \mathbf I$, with no current injected at the inner nodes. Eliminating the inner nodes gives two admittances: $y_F$, the current that the network delivers into the summing node per volt at the output, with the summing node held at 0 V, whose inverse $Z_F = 1/y_F$ is the transimpedance with an ideal amplifier; and $y_{11}$, the admittance at the summing node with the output held at 0 V. By Nyquist's theorem the film then drives the noise current

$$
S_i = 4k_BT\,\mathrm{Re}\{y_{11}\}
\tag{8}
$$

into the summing node, one-sided, at the temperature $T$, so $R_F\,\mathrm{Re}\{y_{11}\}$ is the film's noise power relative to that of a lumped resistor, $4k_BT/R_F$ (the high-gain note derives the same for the uniform line, its Eq. (27)). At low frequency $y_F$ tends to $1/R_F + j\omega C_F$ with exactly the first-order $C_F$, and the ten-element solutions reproduce Table 6 to within 0.15 %: 27.45, 21.83, 11.61 and 88.40 fF.

The film's capacitance to the grounded conductors, $C_g$, follows from the same matrix: it is the capacitance of the film to everything outside the network when the film and both terminations are at the same potential, the row sums of the inner nodes scaled by $n/(n - 1)$ (Appendix B). At the first-order corner $f_1 = 1/(2\pi R_FC_F)$ the electrical length of the line, in the sense of the high-gain note's Section 3.4, is

$$
|\theta_1| = \sqrt{\omega_1R_FC_g} = \sqrt{\frac{C_g}{C_F}} ,
\tag{9}
$$

for example $\sqrt{169.4\ \mathrm{fF}/21.83\ \mathrm{fF}}$ = 2.79 for the ADA4530-1 layout.

**How accurate ten elements are.** The same field solutions also give the capacitance matrix of five elements, exactly and without a new solve, because the hat functions of five elements are sums of those of ten and the field equation is linear (Appendix B). The error of linear elements falls as $1/n^2$, so the difference between five and ten elements, divided by 3, estimates the error of ten. For the four layouts it is below 0.2 % for every bandwidth, below 0.4 % for every value at $f_1$ and below 0.7 % at $3f_1$, although $|\theta|$ reaches 4–7 there; the films couple strongly to their own terminations and, through the alumina, to their other parts, so that their potential varies smoothly along their length. Against the exact uniform line, the same estimate agrees with the true error, and ten elements are within 2.3 % at $|\theta|$ = 4 (Appendix B).

### 7.2 The network alone

With an ideal amplifier the transimpedance is $-Z_F$, so Figure 4 and Table 7 describe the feedback network by itself. Section 7.3 shows when a TIA with a real amplifier follows it.

![Figure 4](figures/fig4_guard_response.png)

*Figure 4. The feedback network of the guarded layouts of Figure 3 and of the PDIP-8 layout without a guard (Figure 2(b)) against frequency at $R_F$ = 1 GΩ; for another $R_F$ every frequency scales as $1/R_F$. (a) $|Z_F|/R_F$ and (b) the phase of $Z_F$, with the film in ten elements (solid) and as the lumped $R_F\parallel C_F$ with the first-order $C_F$ of Table 6 (dashed). (c) The film's noise power relative to a lumped resistor, $R_F\,\mathrm{Re}\{y_{11}\}$ of Eq. (8); the lumped resistor gives 1 (grey, dashed).*

*Table 7. The guarded networks with the film in ten elements: $C_g$; the electrical length $|\theta_1|$ at the first-order corner $f_1$, Eq. (9); $f_1$ and the −3-dB frequency $f_{-3\,\mathrm{dB}}$ at $R_F$ = 1 GΩ; the capacitance $C_{bw} = 1/(2\pi R_Ff_{-3\,\mathrm{dB}})$ that a lumped network would need for that bandwidth; the largest rise of $|Z_F|$ above $R_F$; $|Z_F|/R_F$ and its phase at $f_1$, where the lumped model gives 0.707 and −45°; and the film's noise power relative to a lumped resistor at $f_1$ and averaged from 0 to $f_{-3\,\mathrm{dB}}$.*

| Layout | $C_g$ (fF) | $\lvert\theta_1\rvert$ | $f_1$, $f_{-3\,\mathrm{dB}}$ (kHz) | $C_{bw}$ (fF) | Largest rise | At $f_1$: $\lvert Z_F\rvert/R_F$, phase | Noise at $f_1$; mean to $f_{-3\,\mathrm{dB}}$ |
|---|---|---|---|---|---|---|---|
| LMC6001, PDIP-8, no guard | 51.6 | 0.76 | 1.80, 1.80 | 88.2 | none | 0.708, −45.2° | +0.03 dB; +0.01 dB |
| LMC6001, PDIP-8, guard rings | 174.7 | 2.52 | 5.80, 4.86 | 32.7 | 0.12 dB at 0.24 $f_1$ | 0.614, −61.5° | +1.01 dB; +0.49 dB |
| ADA4530-1, SOIC-8, guard | 169.4 | 2.79 | 7.29, 5.81 | 27.4 | 0.19 dB at 0.24 $f_1$ | 0.589, −62.5° | +1.51 dB; +0.77 dB |
| LMP7721, SOIC-8, guard | 176.4 | 3.90 | 13.71, 7.95 | 20.0 | 0.63 dB at 0.19 $f_1$ | 0.438, −71.0° | +1.80 dB; +1.00 dB |

Figure 4 and Table 7 show four results.

- **Without a guard the lumped model holds.** The PDIP-8 film has only 51.6 fF to the grounded conductors around it, 0.58 of $C_F$, and $|\theta_1|$ = 0.76. Its −3-dB frequency lies within 0.2 % of the first-order corner, and its noise rises by 0.01 dB over the band.
- **With a guard the band ends before the first-order corner.** The guarded films have 169–176 fF to the guard and $|\theta_1|$ = 2.5–3.9. Their −3-dB frequencies are 0.84, 0.80 and 0.58 of the first-order corner, so the bandwidth is that of a lumped network with 32.7, 27.4 and 20.0 fF, not 27.4, 21.8 and 11.6 fF. For the LMP7721, $C_{bw} = 1/(2\pi\times1\ \mathrm{G\Omega}\times7.95\ \mathrm{kHz})$ = 20.0 fF. Around and above the corner, $y_F$ written as $G + j\omega C$ has $G$ = 0.74–0.78 of $1/R_F$ and $C$ = 25–42 fF: the guard draws part of the film's current before it reaches the summing node, and the capacitance that the guard does not intercept takes over.
- **The response barely peaks.** It rises by 0.12–0.63 dB at 0.19–0.24 of the first-order corner before it falls. The first-order capacitance stays positive in all three layouts, unlike the resistor over a grounded plane of the high-gain note's Table 3, which peaks by 4.6 dB once the plane's $C_g$ reaches six times $C_{ee}$.
- **The resistor's noise rises near the corner.** Its noise power is 1.01–1.80 dB above that of a lumped resistor at the first-order corner and 0.49–1.00 dB above it on average from 0 to the −3-dB frequency. Above about ten times the corner it levels off at 1.4–1.6 times the lumped value, because the film's potential is then set by its capacitances to its terminations, to the guard and to its own other parts, whereas over a plane, with capacitance only to ground, it keeps rising as $\sqrt\omega$ (the high-gain note's Section 3.4).

The PDIP-8 pair shows the trade in one layout. The guard widens the band from 1.80 to 4.86 kHz at 1 GΩ, 2.7 times, and costs 0.49 dB of the resistor's noise power averaged over the wider band. Without a guard, a resistor 2.7 times smaller would give that band and 2.7 times the noise power, 4.3 dB more. As a way to bandwidth the guard therefore remains the better one, but it makes the response a distributed one: an equalizer designed from the first-order capacitance would be wrong at $f_1$ by 1.2 dB for the PDIP-8 rings, 1.6 dB for the ADA4530-1 layout and 4.2 dB for the LMP7721 layout. A guard that ends at the resistor's input pad instead of passing under its body would keep most of the film away from the guard; that variant has not been computed.

### 7.3 Inside the amplifier's loop

A real amplifier shares the response wherever its loop gain is not large, so whether Section 7.2 describes the TIA depends on the amplifier, the photodiode and the gain. At the summing node, at the voltage $v_-$, the photocurrent $I$ enters, the network delivers $y_Fv_o$ and draws $y_{11}v_-$, and the photodiode with the amplifier's input draws $Y_Dv_-$. With $v_o = -Av_-$, where $A$ is the open-loop gain, Kirchhoff's current law gives $I + y_Fv_o + (Y_D + y_{11})\,v_o/A = 0$, so

$$
Z_T = \frac{v_o}{I} = -\frac{1}{y_F + Y_n/A} , \qquad Y_n = Y_D + y_{11} ,
\tag{10}
$$

the two-port form of the high-gain note's Eq. (6). With the loop gain $T = Ay_F/Y_n$ it reads $Z_T = -Z_F\,T/(1 + T)$: where $|T| \gg 1$ the network alone sets the response, and near the loop's crossover, $|T|$ = 1, the amplifier shares it. The network enters the loop twice, through $y_F$ and through $y_{11}$.

Equation (10) is evaluated for each guarded layout with the amplifier it was drawn for, on the high-gain note's 20-pF photodiode, the S1336-18BK with a 2-GΩ shunt resistance (its Table 1). The amplifiers have gain–bandwidth products of 1.3 MHz (LMC6001), 2 MHz (ADA4530-1) and 17 MHz (LMP7721) and 8 pF of input capacitance (the high-gain note's Table A.1; the LMC6001 and LMP7721 data sheets give none, and 8 pF is that note's assumption, its Appendix C, item 5). The amplifier is an integrator, $A = 2\pi\,GBW/(j\omega)$, as in the high-gain note's Eq. (17). The total capacitance at the summing node, $C_T$, is then 28.5–28.9 pF, including the network's own capacitance to ground. The comparison is the lumped first-order network in the same loop, $y_F = 1/R_F + j\omega C_F$ and $y_{11} = 1/R_F + j\omega(C_F + C_{B0})$, where $C_{B0}$ is the first-order capacitance of the summing node's end to ground from the same matrix, so that the two agree at low frequency.

The high-gain note's Eq. (20) divides the gains into two regimes. Below the crossover gain $R_F^* = C_T/(\pi\,GBW\,C_F^2)$ the amplifier limits the bandwidth, and above it the resistor does. For the ADA4530-1 layout,

$$
R_F^* = \frac{28.46\ \mathrm{pF}}{\pi\times2\ \mathrm{MHz}\times(21.83\ \mathrm{fF})^2} = 9.5\ \mathrm{G\Omega} ,
\tag{11}
$$

and it is 9.4 GΩ for the LMC6001 rings and 4.0 GΩ for the LMP7721 layout. Table 8 therefore evaluates 1, 10 and 100 GΩ. At 1 GΩ a flat response needs more feedback capacitance than these networks have, so the table adds the case with an ideal external capacitor across the resistor, of the size that makes the first-order total equal to the maximally flat value of the high-gain note's Eq. (18); at 10 and 100 GΩ the networks already exceed that value, and no capacitor is added.

*Table 8. The guarded networks inside the loop of their amplifiers on the 20-pF photodiode: the −3-dB frequency of the network alone (ideal amplifier, Section 7.2), of the loop with the film in ten elements, and of the loop with the lumped first-order network; the largest rise of $\lvert Z_T\rvert$ above its DC value; and the loop's phase margin. The external capacitor is the one of a maximally flat design sized from the first-order value. `g_guard_loop.py`.*

| Layout and amplifier | $R_F$; external capacitor | $f_{-3\,\mathrm{dB}}$ (Hz): network alone; loop; loop, lumped | Rise (dB): loop; loop, lumped | Phase margin: loop; loop, lumped |
|---|---|---|---|---|
| LMC6001 with guard rings | 1 GΩ; none | 4863; 3737; 3998 | 5.96; 6.90 | 34°; 26° |
| | 1 GΩ; 56.7 fF | 1936; 2489; 2668 | 0.09; 0 | 73°; 66° |
| | 10 GΩ; none | 486; 558; 817 | 0.47; 0 | 82°; 67° |
| | 100 GΩ; none | 48.6; 49.4; 60.7 | 0.14; 0 | 89°; 87° |
| ADA4530-1 with its guard | 1 GΩ; none | 5812; 4627; 4997 | 5.67; 6.96 | 36°; 26° |
| | 1 GΩ; 45.6 fF | 2398; 3048; 3334 | 0.12; 0 | 74°; 66° |
| | 10 GΩ; none | 581; 664; 1028 | 0.51; 0 | 82°; 67° |
| | 100 GΩ; none | 58.1; 59.0; 76.4 | 0.21; 0 | 89°; 87° |
| LMP7721 with its guard | 1 GΩ; none | 7948; 9206; 13760 | 1.60; 3.54 | 73°; 39° |
| | 1 GΩ; 11.5 fF | 5524; 6314; 9737 | 0.55; 0 | 82°; 66° |
| | 10 GΩ; none | 795; 820; 1682 | 0.70; 0 | 88°; 79° |
| | 100 GΩ; none | 79.5; 79.7; 140 | 0.63; 0 | 90°; 89° |

Table 8 answers the question in three regimes.

- **Far above $R_F^*$ the network sets the response.** At 100 GΩ the loop's −3-dB frequency lies within 0.3–1.6 % of the network's own, with phase margins of 89–90°: Figure 4 is then the TIA's response, and the amplifier does not change it. The lumped first-order model would overestimate that bandwidth by 23–75 %.
- **Near $R_F^*$ both matter.** At 10 GΩ the loop's −3-dB frequency is 3–15 % above the network's own, because the loop's second-order response lifts it a little near its corner, and the lumped model would overestimate it 1.5–2.1 times.
- **Below $R_F^*$ the amplifier sets the response, and the network sets its damping.** At 1 GΩ the guarded networks alone are too small for these amplifiers on 28.5–28.9 pF, and the loop peaks by 1.6–6.0 dB with phase margins of 34–73°. The lumped model predicts more peaking, 3.5–7.0 dB, and less margin, 26–39°, because near the crossover the network's effective capacitance, the $C$ of 25–42 fF in Section 7.2, exceeds the first-order value. An external capacitor sized from the first-order value therefore overdamps the loop: phase margins of 73–82° instead of the intended 66°, −3-dB frequencies 7–35 % below the flat design's, and, for the LMP7721 layout, a 0.55-dB rise that the network brings with it. The external capacitor of a guarded layout has to be sized from the computed response, Eq. (10) with $y_F$ and $y_{11}$ of the field solution, or trimmed on the bench.

Two points hold in every regime. The resistor's noise current at the summing node, Eq. (8), does not depend on the amplifier, so the noise of Section 7.2, referred to the input, holds in every loop. And without a guard the two models agree in the loop as well: for the LMC6001 layout of Section 5 they give 2521 and 2532 Hz at 1 GΩ and 188.6 and 188.3 Hz at 10 GΩ.

## 8. What the two notes take from this

**The balanced-photodiode note.** The OPA846 in SO-8 gives 56–67 fF, inside the 53–72 fF of the SOT-23-5 layouts of its Section G.14.10, so its Table 1.1 value of 0.08 pF, with corners at 0.05 and 0.12 pF, covers both packages. The inductance of the leads, which its field solutions leave out, changes the effect of the 2-kΩ OPA846 design's feedback capacitance at the crossover by 2.3–4.0 %, inside its ±0.1-pF tolerance.

**The high-gain note.**

- Its 0.1 pF matches two unguarded layouts of its own range, 93.3 and 88.4 fF (Section 5).
- For the capacitances that its Appendix C, item 3, lists as still to be measured, the field solutions give $C_g$ = 52 fF for the PDIP-8 layout without a guard and 169–176 fF for the layouts with a guard under the resistor. These are computed values for these layouts, which a measurement with the injection method of its Section 3.5 should still confirm.
- A guard that passes under the resistor, as in the layouts the amplifiers' makers publish, is the case $a = 0$ of its Section 3.4, and Section 7 quantifies it: the network's band ends at 0.58–0.84 of the first-order corner, its response rises by at most 0.63 dB, and the resistor's noise rises by 1.0–1.8 dB at that corner. Above its crossover gain this is the TIA's response; below it, an external capacitor sized from the first-order value overdamps the loop (Section 7.3).
- The inductance of the leads is negligible at its gains (Section 4).

## Appendix A. Files

The scripts and records of this note lie in the folder of the balanced-photodiode note, beside those of its Appendix G; the paths below are relative to the repository.

- `pcbcap/pcbcap/packages.py` builds the SOT-23-5, SOIC-8 and PDIP-8 models, and its docstrings give every dimension with its source.
- `pcbcap/pcbcap/distributed.py` divides the film into elements and computes $y_F$, $y_{11}$ and the error estimate of Appendix B; the check `python -m pcbcap.checks run uniform_rc_line` compares it with the exact uniform line.
- `TIA_opamp_survey_2026-10-25/scripts_archive/parasitic_cf/numerical/g_eight_lead_3d.py` builds and solves the layouts of Sections 3, 5 and 6; `run_eight_lead.sh` runs them all and writes `TIA_opamp_survey_2026-10-25/data/parasitic_cf/numerical/eight_lead_3d.json`.
- `TIA_opamp_survey_2026-10-25/scripts_archive/parasitic_cf/numerical/g_guard_ladder.py` solves the layouts of Section 7 with the film in ten elements (`guard_ladder.json` in the same data folder) and evaluates them (`guard_ladder_response.json`).
- `TIA_opamp_survey_2026-10-25/scripts_archive/parasitic_cf/numerical/g_guard_loop.py` evaluates Eq. (10) for Table 8 from the same record (`guard_loop.json`).
- `TIA_opamp_survey_2026-10-25/scripts_archive/parasitic_cf/inductance_estimates.py` evaluates Eqs. (1)–(6), its part (F) for this note.
- `TIA_opamp_survey_2026-10-25/scripts_archive/parasitic_cf/numerical/make_side_note_figures.py` draws Figures 1–4 from the records.

The interactive pages show each layout in three dimensions, with every net, pin and dielectric named:

- the OPA846 in SO-8, layouts (a), (b) and (c): https://photonzq.github.io/photodiode-tia-notes/TIA_opamp_survey_2026-10-25/figures/layout_views/opa846_so8_double_sided_0402.html, https://photonzq.github.io/photodiode-tia-notes/TIA_opamp_survey_2026-10-25/figures/layout_views/opa846_so8_vias_under_0402.html and https://photonzq.github.io/photodiode-tia-notes/TIA_opamp_survey_2026-10-25/figures/layout_views/opa846_so8_under_body_0402.html;
- the OPA637 and the LMC6001 without a guard: https://photonzq.github.io/photodiode-tia-notes/TIA_opamp_survey_2026-10-25/figures/layout_views/opa637_so8_bottom_0805.html and https://photonzq.github.io/photodiode-tia-notes/TIA_opamp_survey_2026-10-25/figures/layout_views/lmc6001_dip8_bottom_1206.html;
- the guarded layouts: https://photonzq.github.io/photodiode-tia-notes/TIA_opamp_survey_2026-10-25/figures/layout_views/lmc6001_dip8_bottom_guard_1206.html, https://photonzq.github.io/photodiode-tia-notes/TIA_opamp_survey_2026-10-25/figures/layout_views/ada4530_so8_1206.html and https://photonzq.github.io/photodiode-tia-notes/TIA_opamp_survey_2026-10-25/figures/layout_views/lmp7721_so8_1206.html;
- all layouts, including those of the balanced-photodiode note's Sections G.14.9 and G.14.10: https://photonzq.github.io/photodiode-tia-notes/TIA_opamp_survey_2026-10-25/figures/layout_views/index.html.

## Appendix B. The film in finite elements

This appendix derives the model of Section 7 and its two checks. The module `pcbcap/pcbcap/distributed.py` implements it.

### B.1 The potential along the film

Let $u$ run along the film from 0 at the summing node's termination to 1 at the output's. With $n$ equal elements, the film's potential is written as

$$
V(u) = \sum_{j=0}^{n} V_j\,h_j(u) , \qquad h_j(u) = \max\bigl(0,\ 1 - |nu - j|\bigr) ,
\tag{B.1}
$$

the hat functions of the nodes $u_j = j/n$. Node 0 stands for the summing node's termination together with its whole net (pad, trace, lead), node $n$ for the output's, and the nodes in between for points of the film. The potential is taken as uniform across the film's width, which holds when the film's surroundings do not vary across its width, as for a guard that crosses under the resistor at right angles to its axis. Because $\sum_j (j/n)\,h_j(u) = u$, the DC profile, linear from the summing node to the output, is exactly the node vector $u_j = j/n$.

### B.2 The capacitance matrix

Let $\psi_j$ be the field with node $j$ at 1 V and every other conductor at 0 V, so that the film carries the potential $h_j$. The capacitance matrix between the nodes is

$$
C_{jk} = \int \varepsilon\,\nabla\psi_j\cdot\nabla\psi_k\,\mathrm dV ,
\tag{B.2}
$$

the Maxwell matrix of the balanced-photodiode note's Section G.14.1, with the nodes as nets. The solver imposes $h_j$ by dividing the film into $n$ films, each with a linear potential between its two nodes, so that the kinks of $h_j$ lie on mesh lines. One layout thus needs $n + 1$ = 11 solves. The row sum $\sum_k C_{jk}$ is the capacitance of node $j$ to everything outside the network. For a film with uniform capacitance to its surroundings, each inner node carries $C_g/n$ of it and each end node $C_g/(2n)$ besides its net's own; $C_g$ is therefore taken as $n/(n - 1)$ times the sum over the inner nodes.

### B.3 The conductance matrix

Let the film have the sheet resistance $R_s$, the length $g$ and the width $w$, so that $R = R_sg/w$, and let $s = gu$ be the distance along it. The power it dissipates is $P = (w/R_s)\int_0^g (\mathrm dV/\mathrm ds)^2\,\mathrm ds$. On one element of length $g/n$ the potential is linear from $V_a$ to $V_b$, so $\mathrm dV/\mathrm ds = (V_b - V_a)\,n/g$, whose square integrates over the element to $(V_b - V_a)^2\,n/g$; with $w/R_s = g/R$ each element contributes

$$
P_{ab} = \frac{n}{R}\,(V_b - V_a)^2 , \qquad \mathbf G = \frac{n}{R}\begin{pmatrix} 1 & -1 \\ -1 & 1 \end{pmatrix} \ \text{per element},
\tag{B.3}
$$

so that $\mathbf G$ is the matrix of a chain of $n$ resistors $R/n$. For the linear profile, $P = n\times(n/R)\times(1/n)^2 = 1/R$, the power of 1 V across $R$.

### B.4 The two admittances

At the angular frequency $\omega$ the nodal equations are $\mathbf Y\mathbf V = \mathbf I$ with $\mathbf Y = \mathbf G + j\omega\mathbf C$ and $\mathbf I$ the currents injected at the nodes. Let $i$ be the summing node, $o$ the output and $\mathrm I$ the inner nodes, which carry no injected current. With the output at 1 V and the summing node held at 0 V, the inner nodes take $\mathbf V_{\mathrm I} = -\mathbf Y_{\mathrm{II}}^{-1}\mathbf Y_{\mathrm Io}$, and the current that the network delivers into the summing node is

$$
y_F = -\left(Y_{io} - \mathbf Y_{i\mathrm I}\,\mathbf Y_{\mathrm{II}}^{-1}\,\mathbf Y_{\mathrm Io}\right) , \qquad Z_F = \frac{1}{y_F} .
\tag{B.4}
$$

With the summing node at 1 V and the output held at 0 V, the current that the summing node supplies is

$$
y_{11} = Y_{ii} - \mathbf Y_{i\mathrm I}\,\mathbf Y_{\mathrm{II}}^{-1}\,\mathbf Y_{\mathrm Ii} .
\tag{B.5}
$$

### B.5 The low-frequency limit and the noise

At $\omega$ = 0 the inner nodes take the DC profile and $y_F = 1/R$. To first order in $\omega$ they keep it, and each node $j$ draws the displacement current $j\omega(\mathbf C\mathbf u)_j$. The resistive chain, with both ends held, delivers the fraction $v_j = 1 - u_j$ of a current injected at node $j$ to the summing node, in inverse proportion to the resistances to the two ends. Summing over the nodes gives

$$
y_F = \frac{1}{R} + j\omega C_F + O(\omega^2) , \qquad C_F = -\mathbf v^{\mathsf T}\mathbf C\,\mathbf u ,
\tag{B.6}
$$

which is the first-order capacitance of the electrostatic solution, $-\int\varepsilon\,\nabla\varphi_u\cdot\nabla\varphi_v\,\mathrm dV$, written in the node basis. In this model only the film dissipates, because every dielectric is lossless. A passive network in thermal equilibrium at the temperature $T$, with every terminal but one held at a fixed potential, drives into that terminal a noise current with the one-sided spectral density $4k_BT\,\mathrm{Re}\{y\}$, where $y$ is the admittance seen there (Nyquist's theorem). The summing node is held by the loop, the output by the amplifier and the guard by its own source, so the film's noise at the summing node is Eq. (8) with $y_{11}$ of Eq. (B.5).

### B.6 The error estimate

A hat function of $n/m$ elements is a sum of those of $n$ elements with the coefficients of linear interpolation,

$$
H_J(u) = \sum_j P_{jJ}\,h_j(u) , \qquad P_{jJ} = \max\left(0,\ 1 - \frac{|j - mJ|}{m}\right) ,
\tag{B.7}
$$

exactly, because $H_J$ is linear between the coarse nodes, which are also fine nodes. The field equation and its boundary conditions are linear, so the field of the potential $H_J$ is $\sum_j P_{jJ}\psi_j$, and the capacitance matrix of the coarse elements is

$$
\mathbf C' = \mathbf P^{\mathsf T}\,\mathbf C\,\mathbf P ,
\tag{B.8}
$$

from the same field solutions. The end nodes remain the same nets. With linear elements the error falls as $1/n^2$: if $y_n = y + K/n^2$ and $y_{n/2} = y + 4K/n^2$, the error of $n$ elements is

$$
y_n - y \approx \frac{y_{n/2} - y_n}{3} ,
\tag{B.9}
$$

Richardson's rule, which Section 7 applies with $n$ = 10 and $m$ = 2.

### B.7 The check against the uniform line

For a film whose only capacitance is $C_g$, spread uniformly to ground, the line equations give exactly (the high-gain note's Eq. (25) without $C_{ee}$)

$$
y_F = \frac{\theta}{R\sinh\theta} , \qquad y_{11} = \frac{\theta\coth\theta}{R} , \qquad \theta^2 = j\omega RC_g .
\tag{B.10}
$$

For this case Eq. (B.2) becomes the consistent mass matrix of linear elements, $(C_g/n)$ times $\bigl(\begin{smallmatrix} 1/3 & 1/6 \\ 1/6 & 1/3 \end{smallmatrix}\bigr)$ per element, the integral of $C_g\,h_jh_k$ over one element. Evaluated with Eqs. (B.4) and (B.5), ten elements are within 0.014 %, 0.21 %, 0.90 %, 2.3 % and 8.3 % of $y_F$ at $|\theta|$ = 1, 2, 3, 4 and 6, and within 0.026 %, 0.21 %, 0.44 %, 0.66 % and 1.5 % of $y_{11}$. The order of convergence between 16 and 32 elements is 2.002 for $y_F$ and 2.000 for $y_{11}$. The estimate (B.9) gives 2.40 % at $|\theta|$ = 4 where the true error of ten elements is 2.30 %, and 9.2 % at $|\theta|$ = 6 against 8.3 %. The pcbcap check `uniform_rc_line` runs this comparison.

## References

The two notes of this repository are cited by name and linked in Section 1. Page numbers are the PDF pages of each document.

- [1] Texas Instruments, OPA846 data sheet, SBOS250E, revised Dec. 2008.
- [2] Analog Devices, ADA4530-1 data sheet, Rev. C.
- [3] Texas Instruments, LMP7721 data sheet, SNOSAW6E, revised Dec. 2014.
- [4] Texas Instruments, LMC6001 data sheet, SNOS694I, revised Sep. 2015.
- [5] Texas Instruments, LMC66x (LMC662) data sheet, SNOSC51D, revised Feb. 2024.
- [6] Texas Instruments, OPA627/OPA637 data sheet, SBOS165C, revised Jan. 2025.
- [7] Analog Devices, AD620 data sheet, Rev. H.
- [8] Texas Instruments, OPA855 data sheet, SBOS622D, revised May 2025.
