### A4. Tables of Chapter 4: Two design examples: OPA855 and OPA846 at 2 kΩ

*Table A4.1. The two designs at $C_D$ = 1 pF in our analytical model (datasheet open-loop curve, central noise estimate) and in SPICE with the vendors' macromodels. The dynamic range is Eq. (27) in 150 MHz for a 100-MHz tone, with the amplitude of Eq. (26), 1.525 V for OPA855 and 0.995 V for OPA846, and the transimpedance at 100 MHz of the same column; the usable figure is Eq. (28); the last row uses the amplitude at which the OPA846 macromodel's THD reaches −40 dBc at 100 MHz, 0.66 V. Amplifiers: OPA855 ($C_F$ = 0.20 pF) and OPA846 ($C_F$ = 0.75 pF), $R_F$ = 2 kΩ.*

| Quantity | OPA855, model | OPA855, SPICE | OPA846, model | OPA846, SPICE |
|---|---|---|---|---|
| Crossover $f_c$ (MHz) | 795 | 801 | 237 | 308 |
| Phase margin (°) | 58.4 | 59.6 | 34.1 | 44.7 |
| Gain margin (dB) | 8.0 | 6.8 | 5.8 | 11.6 |
| $f_{-3\,\mathrm{dB}}$ (MHz) | 557 | 563 | 233 | 163 |
| Peaking (dB) | 0.00 | 0.00 | 0.00 | 0.00 |
| $\lvert Z_T\rvert$ at 100 MHz (kΩ) | 1.996 | 2.001 | 1.935 | 1.712 |
| Step: overshoot (%) | 4.0 | 4.2 | 2.2 | 0.0 |
| Step: rise, 10–90 % (ps) | 600 | 603 | 1475 | 2130 |
| Step: settling to 1 % (ns) | 1.95 | 1.92 | 5.39 | 5.05 |
| Noise at 10 MHz (pA/√Hz) | 3.91 | 3.86 | 4.08 | 4.08 |
| Noise at 50 MHz (pA/√Hz) | 3.97 | 3.91 | 4.64 | 4.41 |
| Noise at 100 MHz (pA/√Hz) | 4.17 | 4.10 | 6.07 | 5.34 |
| Noise at 150 MHz (pA/√Hz) | 4.47 | 4.40 | 7.90 | 6.63 |
| Noise at 200 MHz (pA/√Hz) | 4.87 | 4.79 | 9.91 | 8.15 |
| Penalty over 10–150 MHz (dB) | 3.13 | 3.01 | 6.01 | 5.03 |
| Band noise, 0–150 MHz (nA rms) | 50.2 | 49.5 | 69.0 | 61.9 |
| Output noise, unfiltered (mV rms) | – | 0.540 | – | 0.274 |
| Output noise to 150 MHz (mV rms) | – | 0.099 | – | 0.108 |
| Dynamic range at 0 mA (dB) | 80.6 | 80.7 | 74.4 | 76.4 |
| Dynamic range at 0.1 mA (dB) | 76.0 | 76.0 | 71.4 | 72.9 |
| Dynamic range at 1 mA (dB) | 67.6 | 67.6 | 64.0 | 65.1 |
| Dynamic range at 10 mA (dB) | 57.8 | 57.8 | 54.3 | 55.4 |
| Dynamic range at 20 mA (dB) | 54.8 | 54.8 | 51.4 | 52.4 |
| Usable dynamic range at 0.1 mA (dB) | 58.3 | 58.4 | 57.2 | 57.6 |
| Dynamic range at 0 / 0.1 / 1 / 10 mA with the −40-dBc amplitude (dB) | – | – | – | 72.9 / 69.3 / 61.5 / 51.8 |

*Table A4.2. The two designs against the photodiode capacitance with $C_F$ fixed at the design value: SPICE, with our analytical model in brackets. $C_T$ and $NG_\infty = 1 + C_T/C_F$ use the datasheets' input capacitances (OPA855 0.8 pF, OPA846 3.8 pF); the macromodels contain 0.80 and 3.07 pF. The noise is without photocurrent. Amplifiers: OPA855 ($C_F$ = 0.20 pF) and OPA846 ($C_F$ = 0.75 pF), $R_F$ = 2 kΩ.*

| Part | $C_D$ (pF) | $C_T$ (pF) | $NG_\infty$ | $f_c$ (MHz) | Phase margin (°) | Gain margin (dB) | $f_{-3\,\mathrm{dB}}$ (MHz) | Peaking (dB) | Overshoot (%) | Noise at 100 MHz (pA/√Hz) | Penalty, 10–150 MHz (dB) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| OPA855 | 0 | 1.15 | 6.75 | 1414 | 64.1 (57.1) | 2.0 | 518 (517) | 0.00 (0.00) | 0.7 (0.1) | 3.93 (3.99) | 2.71 (2.83) |
| OPA855 | 0.25 | 1.40 | 8.00 | 1164 | 63.7 (59.1) | 3.5 | 539 (537) | 0.00 (0.00) | 0.7 (0.4) | 3.97 (4.03) | 2.77 (2.89) |
| OPA855 | 0.5 | 1.65 | 9.25 | 1002 | 62.5 (59.5) | 4.7 | 554 (550) | 0.00 (0.00) | 1.5 (1.2) | 4.01 (4.07) | 2.84 (2.96) |
| OPA855 | 0.75 | 1.90 | 10.50 | 888 | 61.1 (59.0) | 5.8 | 561 (556) | 0.00 (0.00) | 2.7 (2.5) | 4.05 (4.11) | 2.92 (3.04) |
| OPA855 | 1 | 2.15 | 11.75 | 801 | 59.6 (58.4) | 6.8 | 563 (557) | 0.00 (0.00) | 4.2 (4.0) | 4.10 (4.17) | 3.01 (3.13) |
| OPA855 | 1.25 | 2.40 | 13.00 | 733 | 58.1 (57.7) | 7.7 | 561 (553) | 0.07 (0.02) | 5.9 (5.5) | 4.16 (4.22) | 3.10 (3.23) |
| OPA855 | 1.5 | 2.65 | 14.25 | 678 | 56.7 (56.9) | 8.5 | 556 (548) | 0.19 (0.10) | 7.5 (7.0) | 4.22 (4.28) | 3.20 (3.33) |
| OPA855 | 2 | 3.15 | 16.75 | 595 | 54.0 (54.9) | 9.9 | 542 (532) | 0.52 (0.34) | 10.5 (9.8) | 4.35 (4.42) | 3.43 (3.56) |
| OPA855 | 2.5 | 3.65 | 19.25 | 535 | 51.5 (53.0) | 11.1 | 525 (514) | 0.88 (0.62) | 13.3 (12.3) | 4.50 (4.57) | 3.68 (3.81) |
| OPA855 | 3 | 4.15 | 21.75 | 488 | 49.3 (51.4) | 12.1 | 508 (497) | 1.24 (0.90) | 15.8 (14.6) | 4.67 (4.74) | 3.95 (4.08) |
| OPA855 | 4 | 5.15 | 26.75 | 422 | 45.5 (48.5) | 13.9 | 476 (464) | 1.91 (1.44) | 20.2 (18.5) | 5.04 (5.12) | 4.52 (4.66) |
| OPA855 | 5 | 6.15 | 31.75 | 376 | 42.5 (46.1) | 15.4 | 447 (436) | 2.52 (1.92) | 23.9 (21.7) | 5.45 (5.54) | 5.12 (5.27) |
| OPA846 | 0 | 4.15 | 6.53 | 369 | 43.1 (30.7) | 10.5 | 147 (246) | 0.00 (0.00) | 0.0 (0.4) | 4.96 (5.53) | 4.46 (5.28) |
| OPA846 | 0.25 | 4.40 | 6.87 | 351 | 43.6 (31.7) | 10.7 | 151 (245) | 0.00 (0.00) | 0.0 (0.5) | 5.05 (5.66) | 4.60 (5.46) |
| OPA846 | 0.5 | 4.65 | 7.20 | 335 | 44.0 (32.6) | 11.0 | 156 (242) | 0.00 (0.00) | 0.0 (0.7) | 5.14 (5.79) | 4.74 (5.65) |
| OPA846 | 0.75 | 4.90 | 7.53 | 321 | 44.4 (33.4) | 11.3 | 160 (237) | 0.00 (0.00) | 0.0 (1.2) | 5.24 (5.93) | 4.88 (5.83) |
| OPA846 | 1 | 5.15 | 7.87 | 308 | 44.7 (34.1) | 11.6 | 163 (233) | 0.00 (0.00) | 0.0 (2.2) | 5.34 (6.07) | 5.03 (6.01) |
| OPA846 | 1.25 | 5.40 | 8.20 | 296 | 44.9 (34.7) | 11.8 | 167 (228) | 0.00 (0.04) | 0.0 (3.5) | 5.45 (6.22) | 5.18 (6.20) |
| OPA846 | 1.5 | 5.65 | 8.53 | 285 | 45.1 (35.3) | 12.1 | 170 (223) | 0.00 (0.10) | 0.0 (4.8) | 5.56 (6.36) | 5.33 (6.38) |
| OPA846 | 2 | 6.15 | 9.20 | 265 | 45.3 (36.4) | 12.6 | 176 (214) | 0.00 (0.27) | 0.0 (7.3) | 5.79 (6.66) | 5.65 (6.75) |
| OPA846 | 2.5 | 6.65 | 9.87 | 248 | 45.4 (36.6) | 13.1 | 179 (206) | 0.00 (0.47) | 0.7 (9.5) | 6.03 (6.97) | 5.97 (7.11) |
| OPA846 | 3 | 7.15 | 10.53 | 234 | 45.4 (36.4) | 13.6 | 181 (199) | 0.00 (0.68) | 1.9 (11.5) | 6.28 (7.29) | 6.29 (7.46) |
| OPA846 | 4 | 8.15 | 11.87 | 210 | 45.1 (35.9) | 14.5 | 181 (188) | 0.00 (1.11) | 4.6 (15.0) | 6.82 (7.94) | 6.94 (8.16) |
| OPA846 | 5 | 9.15 | 13.20 | 191 | 44.5 (35.5) | 15.3 | 178 (179) | 0.12 (1.54) | 7.3 (18.0) | 7.39 (8.60) | 7.59 (8.82) |

*Table A4.3. Total $C_F$ chosen anew at each photodiode capacitance: the widest bandwidth with a phase margin of at least 45°, a gain margin of at least 3 dB and at most 1 dB of peaking at that $C_D$, never below the 0.20-pF parasitic floor. Where no $C_F$ of the grid meets all three ("no"), the one with the smallest shortfall, $(45 - \phi_M)^+/45 + (3 - \mathrm{GM})^+/3 + (\mathrm{peaking} - 1)^+/1$, is given. SPICE scans 0.10–0.60 pF in 0.02-pF steps for OPA855 and 0.30–2.00 pF in 0.05-pF steps for OPA846; our analytical model is scanned on the same grid without the gain-margin criterion, which it does not give reliably (Section 5.3). Amplifiers: OPA855 and OPA846, $R_F$ = 2 kΩ.*

| Part | $C_D$ (pF) | $C_F$, SPICE (pF) | Meets | Phase margin (°) | Gain margin (dB) | $f_{-3\,\mathrm{dB}}$ (MHz) | Peaking (dB) | Penalty (dB) | $C_F$, model (pF) | Meets | Phase margin, model (°) | $f_{-3\,\mathrm{dB}}$, model (MHz) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| OPA855 | 0 | 0.20 | no | 64.1 | 2.0 | 518 | 0.00 | 2.71 | 0.20 | yes | 57.1 | 517 |
| OPA855 | 0.25 | 0.20 | yes | 63.7 | 3.5 | 539 | 0.00 | 2.77 | 0.20 | yes | 59.1 | 537 |
| OPA855 | 0.5 | 0.20 | yes | 62.5 | 4.7 | 554 | 0.00 | 2.84 | 0.20 | yes | 59.5 | 550 |
| OPA855 | 0.75 | 0.20 | yes | 61.1 | 5.8 | 561 | 0.00 | 2.92 | 0.20 | yes | 59.0 | 556 |
| OPA855 | 1 | 0.20 | yes | 59.6 | 6.8 | 563 | 0.00 | 3.01 | 0.20 | yes | 58.4 | 557 |
| OPA855 | 1.25 | 0.20 | yes | 58.1 | 7.7 | 561 | 0.07 | 3.10 | 0.20 | yes | 57.7 | 553 |
| OPA855 | 1.5 | 0.20 | yes | 56.7 | 8.5 | 556 | 0.19 | 3.20 | 0.20 | yes | 56.9 | 548 |
| OPA855 | 2 | 0.20 | yes | 54.0 | 9.9 | 542 | 0.52 | 3.43 | 0.20 | yes | 54.9 | 532 |
| OPA855 | 2.5 | 0.20 | yes | 51.5 | 11.1 | 525 | 0.88 | 3.68 | 0.20 | yes | 53.0 | 514 |
| OPA855 | 3 | 0.22 | yes | 52.7 | 11.4 | 484 | 0.73 | 3.96 | 0.20 | yes | 51.4 | 497 |
| OPA855 | 4 | 0.24 | yes | 52.1 | 12.5 | 439 | 0.84 | 4.54 | 0.22 | yes | 51.8 | 445 |
| OPA855 | 5 | 0.26 | yes | 52.0 | 13.3 | 404 | 0.89 | 5.16 | 0.24 | yes | 52.4 | 405 |
| OPA846 | 0 | 0.70 | no | 43.1 | 11.0 | 168 | 0.00 | 4.44 | 0.75 | no | 30.7 | 246 |
| OPA846 | 0.25 | 0.75 | no | 43.6 | 10.7 | 151 | 0.00 | 4.60 | 0.80 | no | 31.8 | 196 |
| OPA846 | 0.5 | 0.75 | no | 44.0 | 11.0 | 156 | 0.00 | 4.74 | 0.80 | no | 32.7 | 199 |
| OPA846 | 0.75 | 0.80 | no | 44.4 | 10.8 | 141 | 0.00 | 4.91 | 0.85 | no | 33.7 | 177 |
| OPA846 | 1 | 0.80 | no | 44.8 | 11.1 | 144 | 0.00 | 5.06 | 0.85 | no | 34.5 | 180 |
| OPA846 | 1.25 | 0.80 | yes | 45.2 | 11.4 | 147 | 0.00 | 5.21 | 0.90 | no | 35.4 | 161 |
| OPA846 | 1.5 | 0.75 | yes | 45.1 | 12.1 | 170 | 0.00 | 5.33 | 0.90 | no | 36.2 | 164 |
| OPA846 | 2 | 0.75 | yes | 45.3 | 12.6 | 176 | 0.00 | 5.65 | 0.95 | no | 37.7 | 150 |
| OPA846 | 2.5 | 0.75 | yes | 45.4 | 13.1 | 179 | 0.00 | 5.97 | 0.95 | no | 39.1 | 153 |
| OPA846 | 3 | 0.75 | yes | 45.4 | 13.6 | 181 | 0.00 | 6.29 | 1.00 | no | 40.4 | 141 |
| OPA846 | 4 | 0.75 | yes | 45.1 | 14.5 | 181 | 0.00 | 6.94 | 1.10 | no | 42.8 | 120 |
| OPA846 | 5 | 0.80 | yes | 45.9 | 14.8 | 167 | 0.00 | 7.62 | 1.20 | no | 44.9 | 104 |

*Table A4.4. Large-signal limits in the macromodels: the amplitude of Eq. (26) from the datasheet's swing and slew rate, and the output amplitudes at which the THD of harmonics 2–5 (Eq. (48)) reaches −60 and −40 dBc, with their fraction of Eq. (26) in brackets, and the second and third harmonics at the amplitude of Eq. (26). The amplitude is stepped by 0.1 from 0.5 to 1.3 times Eq. (26), and for OPA846 also at 0.05, 0.1, 0.15, 0.2, 0.3 and 0.4 times; where the THD does not cross a level within that range, the bound is given. 1-MΩ load, OPA855 on ±2.5 V, OPA846 on ±6 V. Amplifiers: OPA855 ($C_F$ = 0.20 pF) and OPA846 ($C_F$ = 0.75 pF), $R_F$ = 2 kΩ, $C_D$ = 1 pF.*

| Part | Tone | Amplitude of Eq. (26) | Set by | SPICE: amplitude at THD = −60 dBc | at THD = −40 dBc | At the amplitude of Eq. (26): HD2, HD3 |
|---|---|---|---|---|---|---|
| OPA855 | 20 MHz | 1.525 V | swing | 1.42 V (0.93 ×) | 1.60 V (1.05 ×) | −61.4, −49.9 dBc |
| OPA855 | 50 MHz | 1.525 V | swing | 1.37 V (0.90 ×) | 1.54 V (1.01 ×) | −58.4, −44.9 dBc |
| OPA855 | 100 MHz | 1.525 V | swing | 1.34 V (0.88 ×) | 1.51 V (0.99 ×) | −55.6, −41.0 dBc |
| OPA855 | 150 MHz | 1.525 V | swing | 1.34 V (0.88 ×) | 1.51 V (0.99 ×) | −53.8, −39.5 dBc |
| OPA855 | 200 MHz | 1.525 V | swing | 1.34 V (0.88 ×) | 1.51 V (0.99 ×) | −52.6, −39.5 dBc |
| OPA846 | 20 MHz | 4.300 V | swing | 4.16 V (0.97 ×) | above 5.59 V (1.3 ×) | −60.8, −65.7 dBc |
| OPA846 | 50 MHz | 1.989 V | slew rate | 0.407 V (0.20 ×) | 2.41 V (1.21 ×) | −44.6, −49.2 dBc |
| OPA846 | 100 MHz | 0.995 V | slew rate | 0.0775 V (0.08 ×) | 0.659 V (0.66 ×) | −36.2, −42.4 dBc |
| OPA846 | 150 MHz | 0.663 V | slew rate | below 0.0332 V (0.05 ×) | 0.282 V (0.43 ×) | −32.4, −40.2 dBc |
| OPA846 | 200 MHz | 0.497 V | slew rate | below 0.0249 V (0.05 ×) | 0.151 V (0.30 ×) | −30.0, −41.0 dBc |
