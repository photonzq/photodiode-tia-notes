# Geometry and permittivity inputs for the feedback-resistor capacitance estimate

An analytical estimate of the capacitance that shunts a surface-mount feedback resistor needs two kinds of input: the geometry of the conductors (the resistor terminations and the board pads) and the relative permittivity of the materials between and around them (the alumina body, the board laminate, the solder mask and, next to the amplifier, the package mould compound). This file collects those inputs from manufacturer documents (and, for the solder mask at GHz frequencies, one IPC conference paper); it contains no measured capacitances. Every number was read from the rendered page image of the document named in the table, and page numbers count as a PDF viewer counts them. The machine-readable version, with one record per value, the full document title, document number, revision, URL and local file name, is `geometry_and_permittivity.json` in the same folder. The documents themselves are in `appnotes/parasitic_cf/materials/`.

Manufacturer values are typical or nominal values unless the document states a guaranteed limit, and the tolerances quoted below are the ones printed next to each dimension.

## 1. Chip-resistor body dimensions

The terminations are the two electrodes of the parasitic capacitor, so their geometry sets the estimate: the body length $L$ and width $W$, the body thickness $H$ (overall height including terminations and coatings), the length $a$ of the termination metal on the top face (the face that carries the resistive film), and the length $b$ of the termination metal on the bottom face (the face soldered to the board), both measured from the chip end. The manufacturers label these differently. Panasonic uses $a$, $b$ and $T$; Yageo uses $I_1$ (top), $I_2$ (bottom) and $H$; Vishay D/CRCW uses $T_2$ (top) and $T_1$ (bottom); Vishay TNPW uses one column $T_t/T_b$ for both; KOA uses $c$ (top), $d$ (bottom) and $t$; TT Electronics uses $C$ (top), $A$ (bottom) and $T$. The assignment of each label to the top or bottom face was read from the dimension drawing of each data sheet. All dimensions are in millimetres.

### 1.1 Thick-film general-purpose parts

| Size | Part | $L$ | $W$ | $H$ | top $a$ | bottom $b$ | Source, page |
|---|---|---|---|---|---|---|---|
| 0201 | Panasonic ERJ1G | $0.60 \pm 0.03$ | $0.30 \pm 0.03$ | $0.23 \pm 0.03$ | $0.10 \pm 0.05$ | $0.15 \pm 0.05$ | Panasonic AOA0000C301, p. 3 |
| 0201 | Yageo RC0201 | $0.60 \pm 0.03$ | $0.30 \pm 0.03$ | $0.23 \pm 0.03$ | $0.10 \pm 0.05$ | $0.15 \pm 0.05$ | Yageo RC_L V.14, p. 4, Table 1 |
| 0201 | KOA RK73B1H | $0.6 \pm 0.03$ | $0.3 \pm 0.03$ | $0.23 \pm 0.03$ | $0.1 \pm 0.05$ | $0.15 \pm 0.05$ | KOA RK73B, p. 1 |
| 0201 | TT WCR0201 | $0.6 \pm 0.03$ | $0.3 \pm 0.03$ | $0.23 \pm 0.03$ | $0.1 \pm 0.05$ | $0.15 \pm 0.05$ | TT WCR, p. 1 |
| 0402 | Panasonic ERJ2G | $1.00 \pm 0.05$ | $0.50 \pm 0.05$ | $0.35 \pm 0.05$ | $0.20 \pm 0.10$ | $0.25 \pm 0.05$ | Panasonic AOA0000C301, p. 3 |
| 0402 | Yageo RC0402 | $1.00 \pm 0.05$ | $0.50 \pm 0.05$ | $0.35 \pm 0.05$ | $0.20 \pm 0.10$ | $0.25 \pm 0.10$ | Yageo RC_L V.14, p. 4, Table 1 |
| 0402 | Vishay CRCW0402 e3 | $1.0 \pm 0.05$ | $0.5 \pm 0.05$ | $0.35 \pm 0.05$ | $0.2 \pm 0.10$ | $0.25 \pm 0.10$ | Vishay 20035, p. 11 |
| 0402 | KOA RK73B1E | $1.0^{+0.1}_{-0.05}$ | $0.5 \pm 0.05$ | $0.35 \pm 0.05$ | $0.2 \pm 0.1$ | $0.25^{+0.05}_{-0.1}$ | KOA RK73B, p. 1 |
| 0402 | TT WCR0402 | $1.0 \pm 0.1$ | $0.5 \pm 0.05$ | $0.35 \pm 0.05$ | $0.2 \pm 0.1$ | $0.25 \pm 0.1$ | TT WCR, p. 1 |
| 0603 | Panasonic ERJ3G | $1.60 \pm 0.15$ | $0.80^{+0.15}_{-0.05}$ | $0.45 \pm 0.10$ | $0.30 \pm 0.20$ | $0.30 \pm 0.15$ | Panasonic AOA0000C301, p. 3 |
| 0603 | Yageo RC0603 | $1.60 \pm 0.10$ | $0.80 \pm 0.10$ | $0.45 \pm 0.10$ | $0.25 \pm 0.15$ | $0.25 \pm 0.15$ | Yageo RC_L V.14, p. 4, Table 1 |
| 0603 | Vishay CRCW0603 e3 | $1.55^{+0.10}_{-0.05}$ | $0.85 \pm 0.10$ | $0.45 \pm 0.05$ | $0.3 \pm 0.20$ | $0.3 \pm 0.20$ | Vishay 20035, p. 11 |
| 0603 | KOA RK73B1J | $1.6 \pm 0.2$ | $0.8 \pm 0.1$ | $0.45 \pm 0.1$ | $0.3 \pm 0.1$ | $0.3 \pm 0.1$ | KOA RK73B, p. 1 |
| 0603 | TT WCR0603 | $1.6 \pm 0.1$ | $0.8 \pm 0.1$ | $0.45 \pm 0.1$ | $0.3 \pm 0.2$ | $0.3 \pm 0.2$ | TT WCR, p. 1 |
| 0805 | Panasonic ERJ6G | $2.00 \pm 0.20$ | $1.25 \pm 0.10$ | $0.60 \pm 0.10$ | $0.40 \pm 0.20$ | $0.40 \pm 0.20$ | Panasonic AOA0000C301, p. 3 |
| 0805 | Yageo RC0805 | $2.00 \pm 0.10$ | $1.25 \pm 0.10$ | $0.50 \pm 0.10$ | $0.35 \pm 0.20$ | $0.35 \pm 0.20$ | Yageo RC_L V.14, p. 4, Table 1 |
| 0805 | Vishay CRCW0805 e3 | $2.0^{+0.20}_{-0.10}$ | $1.25 \pm 0.15$ | $0.5 \pm 0.10$ | $0.3 \pm 0.20$ | $0.3^{+0.20}_{-0.10}$ | Vishay 20035, p. 11 |
| 0805 | KOA RK73B2A | $2.0 \pm 0.2$ | $1.25 \pm 0.1$ | $0.5 \pm 0.1$ | $0.4 \pm 0.2$ | $0.3^{+0.2}_{-0.1}$ | KOA RK73B, p. 1 |
| 0805 | TT WCR0805 | $2.0 \pm 0.15$ | $1.25^{+0.15}_{-0.1}$ | $0.55 \pm 0.1$ | $0.4 \pm 0.2$ | $0.4 \pm 0.2$ | TT WCR, p. 1 |
| 1206 | Panasonic ERJ8G | $3.20^{+0.05}_{-0.20}$ | $1.60^{+0.05}_{-0.15}$ | $0.60 \pm 0.10$ | $0.50 \pm 0.20$ | $0.50 \pm 0.20$ | Panasonic AOA0000C301, p. 3 |
| 1206 | Yageo RC1206 | $3.10 \pm 0.10$ | $1.60 \pm 0.10$ | $0.55 \pm 0.10$ | $0.45 \pm 0.20$ | $0.45 \pm 0.20$ | Yageo RC_L V.14, p. 4, Table 1 |
| 1206 | Vishay CRCW1206 e3 | $3.2^{+0.10}_{-0.20}$ | $1.6 \pm 0.15$ | $0.55 \pm 0.05$ | $0.4 \pm 0.20$ | $0.45 \pm 0.20$ | Vishay 20035, p. 11 |
| 1206 | KOA RK73B2B | $3.2 \pm 0.2$ | $1.6 \pm 0.2$ | $0.6 \pm 0.1$ | $0.5 \pm 0.3$ | $0.4^{+0.2}_{-0.1}$ | KOA RK73B, p. 1 |
| 1206 | TT WCR1206 | $3.1 \pm 0.15$ | $1.55^{+0.15}_{-0.1}$ | $0.55 \pm 0.1$ | $0.45 \pm 0.2$ | $0.45 \pm 0.2$ | TT WCR, p. 1 |

The 1206 rows were added for the high-gain layouts of Section G.14's eight-lead study; Table G.2 of the note stops at 0805. Panasonic marks the ERJ8G "not recommended for new design" (p. 3). In the TT table one merged cell gives $C$ and $A$ for the 1206 as well. The value used for the model (pcbcap `parts.CHIP_SIZES`) follows the rule of Table G.2: $L$ = 3.20 and $W$ = 1.60, printed by most makers; $H$ = 0.55, printed by three of five, with the range 0.45–0.70 that spans all five; and, since the five nominal values of $a$ are 0.40, 0.45 (twice) and 0.50 (twice), their median 0.45 with the tolerance $\pm 0.20$ that four of them print.

The Vishay D/CRCW e3 data sheet starts at size 0402 and has no 0201 row. The Panasonic precision thick-film series (ERJ1R, 2R, 3R/3E and 6R/6E; document AOA0000C304, p. 4, dated 29-May-25) lists the same dimensions as the general-purpose ERJ series above, and the KOA precision thick-film RK73H (p. 1, dated 10/26/25) lists the same numbers as RK73B. In the TT WCR table a cell without a printed tolerance takes the table's default of $\pm 0.1$ mm, and for 0603 and 0805 a single merged cell gives both $C$ and $A$.

### 1.2 Thin-film precision parts

| Size | Part | $L$ | $W$ | $H$ | top $a$ | bottom $b$ | Source, page |
|---|---|---|---|---|---|---|---|
| 0201 | Panasonic ERA1A | $0.60 \pm 0.03$ | $0.30 \pm 0.03$ | $0.23 \pm 0.03$ | $0.15 \pm 0.05$ | $0.15 \pm 0.05$ | Panasonic AOA0000C307, p. 3 |
| 0201 | Yageo RT0201 | $0.60 \pm 0.03$ | $0.30 \pm 0.03$ | $0.23 \pm 0.03$ | $0.10 \pm 0.05$ | $0.15 \pm 0.05$ | Yageo RT V.17, p. 4, Table 1 |
| 0201 | Vishay TNPW0201 e3 | $0.6 \pm 0.05$ | $0.3 \pm 0.05$ | $0.23 \pm 0.03$ | $0.12 \pm 0.05$ | $0.12 \pm 0.05$ | Vishay 28758, p. 15 |
| 0201 | KOA RN73H1H | $0.6 \pm 0.05$ | $0.3 \pm 0.05$ | $0.25 \pm 0.05$ | $0.15 \pm 0.05$ | $0.15 \pm 0.05$ | KOA RN73H, p. 1 |
| 0201 | TT PCF0201 | $0.58 \pm 0.05$ | $0.29 \pm 0.05$ | $\le 0.26$ | $0.12 \pm 0.05$ | $0.15 \pm 0.05$ | TT PCF, p. 2 |
| 0402 | Panasonic ERA2A | $1.00 \pm 0.10$ | $0.50^{+0.10}_{-0.05}$ | $0.35 \pm 0.05$ | $0.15 \pm 0.10$ | $0.25 \pm 0.10$ | Panasonic AOA0000C307, p. 3 |
| 0402 | Yageo RT0402 | $1.00 \pm 0.10$ | $0.50 \pm 0.05$ | $0.30 \pm 0.05$ | $0.20 \pm 0.10$ | $0.25 \pm 0.10$ | Yageo RT V.17, p. 4, Table 1 |
| 0402 | Vishay TNPW0402 e3 | $1.0 \pm 0.05$ | $0.5 \pm 0.05$ | $0.35 \pm 0.05$ | $0.2 \pm 0.10$ | $0.2 \pm 0.10$ | Vishay 28758, p. 15 |
| 0402 | KOA RN73H1E | $1.0^{+0.1}_{-0.05}$ | $0.5 \pm 0.05$ | $0.35 \pm 0.05$ | $0.25 \pm 0.1$ | $0.25^{+0.05}_{-0.1}$ | KOA RN73H, p. 1 |
| 0402 | TT PCF0402 | $1.0 \pm 0.1$ | $0.5 \pm 0.05$ | $\le 0.55$ | $0.2 \pm 0.15$ | $0.25 \pm 0.15$ | TT PCF, p. 2 |
| 0603 | Panasonic ERA3A | $1.60 \pm 0.20$ | $0.80 \pm 0.20$ | $0.45 \pm 0.10$ | $0.30 \pm 0.20$ | $0.30 \pm 0.20$ | Panasonic AOA0000C307, p. 3 |
| 0603 | Yageo RT0603 | $1.60 \pm 0.10$ | $0.80 \pm 0.10$ | $0.45 \pm 0.10$ | $0.25 \pm 0.15$ | $0.25 \pm 0.15$ | Yageo RT V.17, p. 4, Table 1 |
| 0603 | Vishay TNPW0603 e3 | $1.55 \pm 0.05$ | $0.85 \pm 0.10$ | $0.45 \pm 0.10$ | $0.3 \pm 0.20$ | $0.3 \pm 0.20$ | Vishay 28758, p. 15 |
| 0603 | KOA RN73H1J | $1.6 \pm 0.2$ | $0.8 \pm 0.1$ | $0.45 \pm 0.1$ | $0.3 \pm 0.1$ | $0.3 \pm 0.1$ | KOA RN73H, p. 1 |
| 0603 | TT PCF0603 | $1.6 \pm 0.2$ | $0.8 \pm 0.2$ | $\le 0.65$ | $0.3 \pm 0.25$ | $0.35 \pm 0.25$ | TT PCF, p. 2 |
| 0805 | Panasonic ERA6A | $2.00 \pm 0.20$ | $1.25 \pm 0.10$ | $0.50 \pm 0.10$ | $0.40 \pm 0.25$ | $0.40 \pm 0.25$ | Panasonic AOA0000C307, p. 3 |
| 0805 | Yageo RT0805 | $2.00 \pm 0.10$ | $1.25 \pm 0.10$ | $0.50 \pm 0.10$ | $0.35 \pm 0.20$ | $0.35 \pm 0.20$ | Yageo RT V.17, p. 4, Table 1 |
| 0805 | Vishay TNPW0805 e3 | $2.0 \pm 0.1$ | $1.25 \pm 0.15$ | $0.45 \pm 0.10$ | $0.4 \pm 0.20$ | $0.4 \pm 0.20$ | Vishay 28758, p. 15 |
| 0805 | KOA RN73H2A | $2.0 \pm 0.2$ | $1.25 \pm 0.2$ | $0.5 \pm 0.1$ | $0.4 \pm 0.2$ | $0.3^{+0.2}_{-0.1}$ | KOA RN73H, p. 1 |
| 0805 | TT PCF0805 | $2.0 \pm 0.2$ | $1.25 \pm 0.2$ | $\le 0.65$ | $0.3 \pm 0.25$ | $0.4 \pm 0.25$ | TT PCF, p. 2 |

The Vishay TNPW table gives a single column $T_t/T_b$, so the same value appears for the top and bottom terminations. The TT PCF table gives the thickness only as a maximum. The KOA RN73H table prints the inch length of the 0201 part as "0.24" where ".024" is meant; the millimetre value $0.6 \pm 0.05$ is the one used. KOA's RN73R (p. 1, dated 10/24/25) lists the same numbers as RN73H for 0402, 0603 and 0805, and the older RN73 sheet carries an "EOL" watermark across its page.

### 1.3 Construction: film face, termination coverage and substrate

All eight construction drawings that were checked (Panasonic ERJ, AOA0000C301 p. 2; Panasonic ERA, AOA0000C307 p. 3; Yageo RC, p. 4 Fig. 9; Yageo RT, p. 4 Fig. 5; Vishay D/CRCW, drawing p. 11 and text p. 4; Vishay TNPW, drawing p. 15 and text p. 5; KOA RK73B and RN73H, p. 1) put the resistive film on the top face of the substrate, under a protective coating, so the part is mounted film-side up. In every drawing the termination covers the end face and wraps onto the top face (length $a$) and the bottom face (length $b$). None of the drawings shows the termination continuing onto the long side faces; they show it only as an edge profile at the chip end, and none of the texts states side-face coverage, so that point is not documented in these sources. Yageo shows inner electrodes on both the top and bottom faces (RC Fig. 9), and Vishay TNPW states that "inner contacts are deposited on both sides" (p. 5).

## 2. Recommended land patterns

The pads under the terminations form the larger part of the parasitic capacitor on the board side, so the estimate needs the gap between the pads, the pad length along the resistor axis, the pad width across it and the overall length. The manufacturers define these with different letters, and each definition below was read from the land-pattern drawing.

- **Panasonic** (DMM0000COL17, p. 1, dated 24-Dec-25): $a$ is the gap between the inner edges of the two pads, $b$ the overall length from outer edge to outer edge, and $c$ the pad width. The pad length is not given; it follows from $\ell_\mathrm{pad} = (b - a)/2$, evaluated as $(b_\mathrm{min} - a_\mathrm{max})/2$ to $(b_\mathrm{max} - a_\mathrm{min})/2$. For 0402 this gives $(1.4 - 0.6)/2 = 0.40$ mm to $(1.6 - 0.5)/2 = 0.55$ mm. The same table applies to the general-purpose ERJ and the high-precision ERA series and does not distinguish reflow from flow soldering.
- **Yageo** ("Chip resistors mounting", PYu-R_Mount_10, V.10, February 13, 2018, p. 4, Fig. 4): $A$ is the overall length, $B$ the gap, $C$ the pad length and $D$ the pad width. Table 1 is for reflow and Table 2 for wave soldering.
- **Vishay D/CRCW** (document 20035, p. 11) and **Vishay Draloric/Beyschlag thin film** (document 28950, Rev. 12-Jul-2022, p. 1, which the TNPW data sheet cites on its p. 15): $G$ is the gap, $Y$ the pad length, $X$ the pad width and $Z$ the overall length. Document 28950 gives two reflow tables, one based on IPC-7351 and one on IEC 61188-6-2.
- **KOA** (Appendix B, p. 1 for reflow, dated 04/15/26): $A$ is the gap, $B$ the overall length, $C$ the pad width and $D$ the pad length. KOA's pads are narrower than the chip body for 0402 to 0805 ($C < W$) and as wide as the body for 0201.

All values are in millimetres and are for reflow soldering unless stated. In every row with a stated pad length, overall $=$ gap $+ 2 \times$ pad length holds exactly.

| Size | Source, page | Gap | Pad length | Pad width | Overall length |
|---|---|---|---|---|---|
| 0201 | Panasonic DMM0000COL17, p. 1 | 0.3 to 0.4 | 0.20 to 0.30 (derived) | 0.25 to 0.35 | 0.8 to 0.9 |
| 0201 | Yageo Mount V.10, p. 4, Table 1 | 0.3 | 0.35 | 0.4 | 1.0 |
| 0201 | Vishay 28950, p. 1, IPC-7351 | 0.27 | 0.43 | 0.42 | 1.13 |
| 0201 | Vishay 28950, p. 1, IEC 61188-6-2 | 0.30 | 0.24 | 0.32 | 0.78 |
| 0201 | KOA Appendix B, p. 1 | 0.25 | 0.225 | 0.3 | 0.7 |
| 0402 | Panasonic DMM0000COL17, p. 1 | 0.5 to 0.6 | 0.40 to 0.55 (derived) | 0.4 to 0.6 | 1.4 to 1.6 |
| 0402 | Yageo Mount V.10, p. 4, Table 1 | 0.5 | 0.5 | 0.6 | 1.5 |
| 0402 | Vishay 20035 (CRCW), p. 11 | 0.45 | 0.6 | 0.6 | 1.65 |
| 0402 | Vishay 28950, p. 1, IPC-7351 | 0.40 | 0.55 | 0.60 | 1.50 |
| 0402 | Vishay 28950, p. 1, IEC 61188-6-2 | 0.55 | 0.35 | 0.55 | 1.25 |
| 0402 | KOA Appendix B, p. 1 | 0.5 | 0.4 | 0.3 | 1.3 |
| 0603 | Panasonic DMM0000COL17, p. 1 | 0.7 to 0.9 | 0.55 to 0.75 (derived) | 0.8 to 1.0 | 2.0 to 2.2 |
| 0603 | Yageo Mount V.10, p. 4, Table 1 | 0.8 | 0.9 | 0.8 | 2.6 |
| 0603 | Vishay 20035 (CRCW), p. 11 | 0.75 | 0.75 | 1.00 | 2.25 |
| 0603 | Vishay 28950, p. 1, IPC-7351 | 0.70 | 0.90 | 1.00 | 2.50 |
| 0603 | Vishay 28950, p. 1, IEC 61188-6-2 | 0.90 | 0.55 | 0.90 | 2.00 |
| 0603 | KOA Appendix B, p. 1 | 1.0 | 0.5 | 0.6 | 2.0 |
| 0805 | Panasonic DMM0000COL17, p. 1 | 1.0 to 1.4 | 0.9 to 1.4 (derived) | 0.9 to 1.4 | 3.2 to 3.8 |
| 0805 | Yageo Mount V.10, p. 4, Table 1 | 1.2 | 0.9 | 1.2 | 3.0 |
| 0805 | Vishay 20035 (CRCW), p. 11 | 1.00 | 0.95 | 1.45 | 2.90 |
| 0805 | Vishay 28950, p. 1, IPC-7351 | 1.00 | 0.90 | 1.45 | 2.80 |
| 0805 | Vishay 28950, p. 1, IEC 61188-6-2 | 1.10 | 0.65 | 1.30 | 2.40 |
| 0805 | KOA Appendix B, p. 1 | 1.3 | 0.6 | 1.05 | 2.5 |
| 1206 | Vishay 20035 (CRCW), p. 11 | 1.50 | 1.05 | 1.80 | 3.60 |
| 1206 | Vishay 28950, p. 1, IPC-7351 | 1.75 | 1.15 | 1.80 | 4.05 |
| 1206 | Vishay 28950, p. 1, IEC 61188-6-2 | 2.10 | 0.80 | 1.65 | 3.70 |

For the 1206 only the two Vishay documents were read; the model uses the IPC-7351 row of Vishay 28950, as for the other sizes.

The wave- and flow-soldering patterns are in the JSON file. They have longer pads, while the gap is the same (KOA), larger (Yageo) or smaller (Vishay D/CRCW) than for reflow: for example, Yageo Table 2 gives 0603 as gap 0.90, pad length 0.90, width 0.80, overall 2.70; Vishay 20035 gives 0603 wave as 0.65, 1.10, 1.25, 2.85; and KOA Appendix B p. 3 (dated 3/28/25) gives 0603 flow as 1.0, 0.7, 0.8, 2.4. The Vishay 28950 0402 pattern also has an IPC and an IEC variant, which differ by 0.15 mm in gap and 0.20 mm in pad length; the choice between them changes the pad-to-pad geometry of the estimate.

## 3. Relative permittivity of the alumina substrate

The alumina body fills the space between the two terminations, so its relative permittivity $\varepsilon_r$ multiplies the body contribution to the capacitance. Thick-film chips are usually built on 96 % alumina and thin-film chips on 99.5 to 99.6 % alumina; the first table records what the substrate makers state for those grades, and the second records what the resistor makers state about their substrates.

| Material (Al$_2$O$_3$ content) | $\varepsilon_r$ | Frequency | Method, remarks | Source, page |
|---|---|---|---|---|
| Kyocera AO476O / A476 (96 %) | 9.4 | 1 MHz | JIS C 2141; loss angle $4 \times 10^{-4}$ | Kyocera catalog 008/026/2505, p. 3 |
| Kyocera AO473O / A473 (92 %) | 9.0 | 1 MHz | JIS C 2141; loss angle $6 \times 10^{-4}$ | Kyocera catalog 008/026/2505, p. 3 |
| Kyocera AO479S / A479S (99.5 %) | 9.9 | 1 MHz | JIS C 2141; loss angle $1 \times 10^{-4}$ | Kyocera catalog 008/026/2505, p. 3 |
| Kyocera AO479M, AO479G (99.5 %) | 9.9 | 1 MHz | JIS C 2141 | Kyocera catalog 008/026/2505, p. 3 |
| Kyocera AO479U / A479U (99.6 %) | 10 | 1 MHz | JIS C 2141; loss angle $< 1 \times 10^{-4}$ | Kyocera catalog 008/026/2505, p. 3 |
| Kyocera A473 (content not stated on the page) | 9.1 and 8.5 | 1 MHz and 2 GHz | representative values; loss tangent $5 \times 10^{-4}$ and $10 \times 10^{-4}$ | Kyocera semiconductor-components web page "Alumina", Material Properties |
| Kyocera A476 (content not stated on the page) | 9.4 | 1 MHz | no 2 GHz value given | same web page |
| CeramTec Rubalit 708S C ($\ge 96.0$ %) | 9.8 | 1 MHz | sheet footnote: $\pm 10$ % measurement tolerance for all values; loss factor $\le 5 \times 10^{-3}$ | CeramTec CA240158/EN/2601/IM, p. 2 |
| CeramTec Rubalit 708 D ($\ge 95.8$ %) | 8.3 to 11.3 | 1 MHz | loss factor $\le 10 \times 10^{-3}$ | CeramTec CA240158/EN/2601/IM, p. 2 |
| CeramTec Rubalit 710F C (99.6 %, printed as "+/- 99.6") | 8.5 to 11.5 | 1 MHz | loss factor $\le 10 \times 10^{-3}$ | CeramTec CA240158/EN/2601/IM, p. 2 |
| CeramTec Rubalit 708S C, 708 HP C ($\ge 96.0$ %), 708 D ($\ge 95.8$ %) | 8.3 to 11.3 | 10 MHz, 100 MHz and 1 GHz | 2 mm thick sample, $R_a \le 0.4$ µm | CeramTec CA210105/EN/2111/IM, p. 2 |
| CeramTec Rubalit 710F C (99.6 %) | 8.5 to 11.5 | 10 MHz, 100 MHz and 1 GHz | same conditions | CeramTec CA210105/EN/2111/IM, p. 2 |
| CoorsTek AD-995-I2 (nominal 99.5 %) | 9.7 and 9.8 | 1 MHz and 4 to 5 GHz | ASTM D150 at 1 MHz; TE$_{011}$ resonator at 4 to 5 GHz | CoorsTek 02084 Rev. E, p. 1 |
| CoorsTek AD-995-I4, AD-996-SI (min. 99.5 %), AD-995-LT (nominal 99.5 %) | 9.8 and 9.8 | 1 MHz and 4 to 5 GHz | same methods | CoorsTek 02084 Rev. E, p. 1 |
| CoorsTek ADS-96R and SuperStrate 996 (substrate grades) | not found | | | CoorsTek 02381 F, p. 2 (no dielectric-constant row) |

Three comments bear on how these numbers are used. First, Kyocera's grade A473 is a 92 % alumina in Kyocera's own table; the 96 % grade is A476. Second, the CeramTec ranges are wide and symmetric: 8.3 to 11.3 is $9.8 \pm 1.5$ and 8.5 to 11.5 is $10.0 \pm 1.5$, so they are tolerance bands rather than measurements of a frequency dependence; the 2022 sheet gives the same band at 10 MHz, 100 MHz and 1 GHz. Third, the CoorsTek 02084 grades are structural and semiconductor-equipment aluminas, not substrate grades, but they show that a 99.5 % alumina has the same permittivity at 1 MHz (9.7 to 9.8) as at 4 to 5 GHz (9.8). The CoorsTek substrate overview (02381 F) lists strength, thermal and dielectric-strength data but no dielectric constant, its per-product data sheets on GlobalSpec refused automated access (HTTP 403), and CoorsTek offers its substrate design guides on request only. The Maruwa site was offline for emergency maintenance (notice dated 27 October 2026), so the Maruwa HA-96 and HA-996 sheets could not be opened; a search-engine summary quoted 9.8 (HA-96-2) and 9.9 (HA-996) at 1 MHz, but these could not be checked against the documents and are not used.

### Substrate purity stated by resistor makers

Most resistor data sheets do not state the purity. Panasonic labels the part "Alumina substrate" (ERJ and ERA construction drawings), Vishay writes "high grade (Al$_2$O$_3$) ceramic substrate" (D/CRCW p. 4, TNPW p. 5), Yageo writes "high-grade ceramic body" (RC and RT p. 4) and KOA labels "Ceramic Substrate" (RK73B, RN73H p. 1). Three documents do state a purity:

| Resistor | Stated substrate | Source, page |
|---|---|---|
| TT Electronics WCR (thick film) | "high alumina substrate (96% minimum)" | TT WCR, issue 09.26, p. 1, Construction |
| TT Electronics PCF (thin film, nichrome) | "96% alumina substrate" | TT PCF, issue 07.26, p. 2, Construction |
| Vishay Thin Film precision chips (flip-chip and wrap-around, 0201 to 0603) | "high performance 99.5 % alumina substrates" | Vishay 60107, Rev. 04-Feb-09, p. 1, Experimental |

The TT PCF entry shows that a thin-film chip is not necessarily built on 99.5 % alumina.

## 4. FR-4 laminates and solder mask

The board laminate lies under the pads and the solder mask lies on top of the board between them, so both enter the pad-to-pad (fringing) part of the estimate. FR-4 permittivity depends on the resin-to-glass ratio of the particular core or prepreg, which is why two of the three data sheets tabulate it by glass style and resin content.

| Laminate | $\varepsilon_r$ at 100 MHz | $\varepsilon_r$ at 1 GHz | Conditions | Source, page |
|---|---|---|---|---|
| Isola 370HR | 4.24 | 4.17 | IPC-TM-650 2.5.5.3 (100 MHz) and 2.5.5.9 (1 GHz); construction not stated; also 4.04 at 2 GHz, 3.92 at 5 and 10 GHz | Isola 370HR data sheet (Rev. C, last updated April 15, 2021), p. 2, Typical Values Table |
| Panasonic R-1755V, 0.8 mm sample | not given | 4.44 | IPC TM-650 2.5.5.9, C-24/23/50; 4.70 at 1 MHz | Panasonic No. 19070536 (Jul. 2019), p. 2 |
| Panasonic R-1755V, 7628 or 2116 cloth, 46 % resin | 4.57 | 4.44 | 4.70 at 1 MHz | Panasonic No. 19070536, p. 3 |
| Panasonic R-1755V, 1080 cloth, 60 % resin | 4.24 | 4.14 | 4.38 at 1 MHz | Panasonic No. 19070536, p. 3 |
| Panasonic R-1755V, all listed cores (106 to 7628) | 4.05 to 4.70 | 3.95 to 4.63 | typical, not guaranteed | Panasonic No. 19070536, p. 3 |
| Panasonic R-1650V prepreg, all listed styles (65 to 80 % resin) | 3.78 to 4.13 | 3.65 to 4.02 | typical, not guaranteed | Panasonic No. 19070536, p. 5 |
| Ventec VT-47, resin content 50 % | not given | 4.27 (specification $\le 5.2$) | IPC-TM-650 2.5.5.9 | Ventec VT-47 properties sheet (published 19/03/20), p. 2 |
| Ventec VT-47 core 0.059 in, 8 $\times$ 7628, 44 % resin | not given | 4.28 | "DK values are for impedance design" | Ventec VT-47 process guide (version 12/08/2025), p. 3 |
| Ventec VT-47, all listed cores / prepregs | not given | 3.75 to 4.35 / 3.45 to 4.25 | same | Ventec VT-47 process guide, pp. 3 and 2 |

The glass-rich constructions that make up most of a 1.6 mm board (7628 and 2116 at about 41 to 46 % resin) sit at about 4.2 to 4.6 between 100 MHz and 1 GHz in the Panasonic and Ventec tables, consistent with Isola's 4.17 to 4.24, while the resin-rich prepregs (which form the layer under the outer copper in a foil-built stackup) fall to about 3.5 to 4.0 at 1 GHz.

| Solder mask | $\varepsilon_r$ | Frequency | Conditions | Source, page |
|---|---|---|---|---|
| Taiyo PSR-4000 G24K / CA-40 G24 (green, screen-print LPI) | 4.1 initial, 4.8 after humidity | 1 MHz | Taiyo in-house method; humidity treatment 25 to 65 °C cycling at 90 % RH for 7 days, measured at room temperature; dissipation factor 0.024 and 0.041 | Taiyo technical data (Japanese) MS-00150100 / MS-00140800, 2016.02, p. 4 (archived copy) |
| Taiyo PSR-4000 EG23 / CA-40 G23K (black) | 4.5 initial, 4.9 after humidity | 1 MHz | same method; dissipation factor 0.025 and 0.042 | Taiyo MS-00139200 / MS-00137100, 2016.02, p. 4 (archived copy) |
| Taiyo PSR-4000 D10ME / CA-40 D10 (black, matte) | 3.5 initial, 3.7 conditioned | 1 MHz | same method; dissipation factor 0.02 and 0.03 | Taiyo technical data sheet MS-00255201 / MS-00255301, Feb. 2016, p. 4 (archived copy) |
| Peters Elpemer 2467 | about 3.7 | 1 MHz | "based on IPC 4101 A"; dissipation factor about 0.029 (1 to 100 MHz) | Peters Technical Report Elpemer 2467, p. 5 |
| Taiyo America LPI solder mask "LPI C" (product not named) | 3.22, 3.29 and 3.48 | 3.2 GHz | split-post dielectric resonator at 21.1 °C / 15 % RH, 29.4 °C / 55 % RH and 37.8 °C / 95 % RH; read from the plotted points, $\pm 0.02$ | IPC paper S12-2 (Intel and Taiyo America, 2005), p. 7, Fig. 10 |

The Taiyo data sheets were taken from archived copies because the original links on the Taiyo Holdings site now redirect to a news page and the Taiyo America product pages offer the data sheets only through a request form. The PSR-4000 values show that the permittivity of a cured LPI mask at 1 MHz lies between about 3.5 and 4.5 depending on the formulation and rises by 0.2 to 0.7 after humidity exposure; the IPC paper shows the same humidity dependence at GHz frequencies.

## 5. Epoxy mould compound

The mould compound of the amplifier package surrounds the leads that the feedback network connects to, so its permittivity enters any estimate that includes the package side of the loop. No semiconductor-vendor document stating the compound permittivity of a QFN or WSON package was found.

| Compound | $\varepsilon_r$ | Frequency | Remarks | Source, page |
|---|---|---|---|---|
| Panasonic CV8710U and CV8710MYC | 4.0 | 1 MHz | JIS K6911; fused-silica filler 88 to 88.5 wt%; intended for laminate-substrate packages (PoP, MCP, mould underfill, FBGA), not leadframe QFN | Panasonic Data Sheet No. 200908-3 (Sep. 2020), p. 2 |
| Hitachi Chemical (now Resonac) CEL-9220HF10 | 3.1 | 1 MHz | dissipation factor 1.1 %; spherical filler 90 wt%; package type not stated; copy attached to a TI E2E forum post | Hitachi Chemical technical data sheet (2016), p. 1, Table 3 |

The Sumitomo Bakelite EME-G700 and EME-G770 data sheets were not found on the web. Kyocera's KE-G compounds appeared only as listings on a third-party materials database whose full data sheets need a login (behind login, e.g. https://plastics.ulprospector.com/plastics/en/datasheet/277082/kyocera-ke-g240v), so they were not opened. A search result for a distributor page quotes 4.0 at 1000 kHz for Henkel's QFN compound GR900, but neither that page nor a Henkel data sheet was opened, so the value is not used. On TI's E2E forum, TI declined to give the permittivity of the PCA9306-Q1 mould compounds, saying it "isn't information that I can share on a public forum".

## 6. Leadframe thickness of a 0.5 mm pitch WSON

The leadframe thickness sets the height of the exposed metal at the package side, which matters if the estimate includes the amplifier's own pins. The TI DSG0008A outline (8-pin WSON, 2 mm by 2 mm, 0.5 mm pitch; drawing 4218900/E 08/2022, in the OPA855 data sheet SBOS622D, p. 38) does not state the leadframe thickness. It gives a "side wall metal thickness, DIM A" of 0.1 mm (option 1) or 0.2 mm (option 2), a package height of 0.7 to 0.8 mm, a standoff of 0.00 to 0.05 mm, terminals 0.18 to 0.32 mm wide and 0.2 to 0.4 mm long, and an exposed pad of $0.9 \pm 0.1$ mm by $1.6 \pm 0.1$ mm. For a different, older TI leadless package, the 14-pin QFN RGY, the application report SCBA017D (p. 6, Figure 2) labels the side view "0.20 NOMINAL LEAD FRAME", and the application note SLUA271C (p. 3) states that TI QFN and SON packages "use conventional copper leadframe technology" without giving a thickness.

## Values that could not be found

The leadframe thickness of the DSG package is not stated in TI's outline drawing. No public data sheet gives the dielectric constant of the CoorsTek ADS-96R or SuperStrate 996 substrates, and the Maruwa HA-96 and HA-996 sheets could not be opened because the Maruwa site was offline. The Sumitomo EME-G700 and EME-G770 mould-compound data sheets and any semiconductor-vendor statement of a QFN or WSON compound permittivity were not found. None of the chip-resistor documents states whether the terminations cover the long side faces, and only TT Electronics and one Vishay technical note state the purity of the alumina substrate. The Vishay D/CRCW e3 data sheet has no 0201 size, and the Panasonic land-pattern table gives no pad length, which is therefore derived above. No FR-4 data sheet in this set gives a value at 100 MHz other than Isola 370HR and Panasonic R-1755V/R-1650V.
