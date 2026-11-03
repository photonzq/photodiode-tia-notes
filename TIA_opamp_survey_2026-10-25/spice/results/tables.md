### Macromodel parameters

| Amplifier | $I_Q$ (mA): SPICE / datasheet | $e_n$ (nV/√Hz): SPICE / datasheet | $i_n$ at 10 / 100 MHz (pA/√Hz): SPICE fit | $C_{\mathrm{in}}$ (pF): SPICE / datasheet $C_{CM} + C_{DIFF}$ | capacitance driven by $e_n$ (pF) | $R_{\mathrm{in}}$ | $Z_o$ at 100 MHz / 1 GHz (Ω) | unity gain from IN+ (GHz) |
|---|---|---|---|---|---|---|---|---|
| OPA855 | 17.5 / 17.8 | 0.97 / 0.99 | 2.54 / 2.52 | 0.80 / 0.80 | 0.80 | 4.99 kΩ | 9.5 / 10.8 | 5.19 |
| OPA818 | 27.7 / 27.7 | 2.18 / 2.20 | 1.15 / 4.22 | 2.37 / 2.40 | 2.37 | 43 MΩ | 4.5 / 8.4 | 1.42 |
| OPA856 | 17.2 / 17.2 | 0.91 / 0.91 | 2.59 / 2.59 | 1.10 / 1.10 | 1.10 | 4.49 kΩ | 6.7 / 8.4 | 0.78 |
| OPA858 | 20.2 / 20.5 | 2.44 / 2.50 | 0.00 / 0.03 | 0.82 / 0.82 | 0.82 | 35 MΩ | 7.1 / 7.6 | 3.27 |
| LMH6629 (COMP HI) | 16.0 / 15.5 | 0.69 / 0.69 | 2.60 / 2.60 | 1.30 / 5.70 | 1.29 | 3.52 kΩ | 17.5 / 17.6 | 2.85 |
| OPA859 | 20.2 / 20.5 | 3.03 / 3.30 | 0.01 / 0.03 | 0.82 / 0.82 | 0.82 | 35 MΩ | 6.3 / 8.6 | 0.94 |
| OPA846 | 4.8 / 12.6 | 1.13 / 1.20 | 2.82 / 3.20 | 3.07 / 3.80 | 2.28 | 4.14 kΩ | 37.2 / 36.2 | 1.56 |
| OPA657 | 14.0 / 14.0 | 4.74 / 4.80 | 0.02 / 0.21 | 5.20 / 5.20 | 5.20 | 918.48 kΩ | 9.6 / 75.7 | 0.75 |
| OPA847 | 18.2 / 18.1 | 0.86 / 0.85 | 3.48 / 10.81 | 7.61 / 3.70 | 2.15 | 0.22 kΩ | 2.8 / 14.1 | 0.90 |
| LMH6624 | 12.0 / 12.0 | 0.89 / 0.92 | 2.07 / 2.13 | 3.80 / 2.90 | 3.53 | 4.25 kΩ | 25.7 / 39.9 | 0.59 |
| THS4021 | 7.9 / 7.5 | 1.26 / 1.20 | 1.06 / 1.41 | 2.62 / 1.50 | 2.44 | 9.54 kΩ | 20.5 / 20.2 | 0.54 |
| ADA4817-1 | 19.0 / 19.0 | 3.39 / 4.00 | 0.05 / 0.05 | 1.60 / 1.40 | 1.60 | 5 MΩ | 8.8 / 50.4 | 0.39 |
| AD8099 | 15.0 / 15.0 | 0.88 / 0.95 | 2.40 / 2.40 | 5.10 / 2.00 | 5.10 | 4.00 kΩ | 17.7 / 11.7 | 1.71 |
| ADA4899-1 | 14.7 / 14.7 | 0.93 / 1.00 | 2.45 / 2.45 | 0.40 / 4.40 | 0.40 | 4.00 kΩ | 23.0 / 23.1 | 0.24 |
| ADA4895-1 | 2.9 / 3.0 | 0.93 / 1.00 | 1.52 / 1.52 | 14.00 / 14.00 | 14.00 | 10.00 kΩ | 49.9 / 41.9 | 0.75 |
| OPA955 | 20.2 / 20.2 | 0.80 / 0.81 | 0.55 / 0.55 | 1.10 / 1.10 | 1.10 | 203 MΩ | 9.1 / 15.2 | 6.54 |
| OPA817 | 23.5 / 23.5 | 4.44 / 4.50 | 0.02 / 0.03 | 3.00 / 3.00 | 3.00 | 28 MΩ | 8.5 / 12.5 | 0.39 |
| OPA814 | 16.0 / 16.0 | 5.33 / 5.30 | 0.01 / 0.03 | 2.70 / 2.70 | 2.70 | 35 MΩ | 12.7 / 14.6 | 0.27 |

### Open-loop gain: macromodel / datasheet curve

| Amplifier | 100 MHz | 300 MHz | 1 GHz | 3 GHz | from IN− at 1 GHz | from IN− at 3 GHz |
|---|---|---|---|---|---|---|
| OPA855 | 38.2 dB, −92° / 38.2 dB, −83° | 28.7 dB, −93° / 28.7 dB, −87° | 18.4 dB, −98° / 18.6 dB, −101° | 12.8 dB, −125° / 13.2 dB, −154° | +0.3 dB, −1° | +1.9 dB, −13° |
| OPA818 | 28.3 dB, −95° / 28.4 dB, −101° | 19.0 dB, −106° / 18.4 dB, −123° | 5.7 dB, −157° / 3.6 dB, phase not plotted | −14.9 dB, −181° / not plotted | +0.0 dB, −4° | −0.9 dB, −13° |
| OPA856 | 19.7 dB, −94° / 20.9 dB, −95° | 9.7 dB, −101° / 10.9 dB, −104° | −3.1 dB, −109° / −0.3 dB, −125° | −14.8 dB, −101° / −10.6 dB, −187° | +0.2 dB, −5° | −0.7 dB, −15° |
| OPA858 | 34.6 dB, −92° / 38.9 dB, −83° | 25.0 dB, −98° / 29.4 dB, −87° | 13.9 dB, −116° / 19.0 dB, −102° | 0.8 dB, −152° / 9.2 dB, −151° | −0.0 dB, −0° | −0.0 dB, −0° |
| LMH6629 (COMP HI) | 34.0 dB, −94° / 31.7 dB, −96° | 24.3 dB, −102° / 22.3 dB, −104° | 12.9 dB, −127° / 11.5 dB, −145° | −1.2 dB, −176° / not plotted | −0.1 dB, −7° | −0.7 dB, −21° |
| OPA859 | 20.0 dB, −93° / 19.0 dB, −86° | 10.4 dB, −100° / 9.0 dB, −94° | −1.0 dB, −117° / −2.5 dB, −112° | −9.0 dB, −141° / −9.3 dB, −151° | −0.0 dB, −0° | +0.0 dB, −0° |
| OPA846 | 26.4 dB, −100° / 23.8 dB, −104° | 16.7 dB, −121° / 15.4 dB, −134° | 4.8 dB, −190° / 4.8 dB, phase not plotted | −20.5 dB, −384° / not plotted | +0.1 dB, −0° | +0.8 dB, −1° |
| OPA657 | 23.8 dB, −106° / 27.8 dB, −113° | 12.7 dB, −136° / 16.2 dB, −154° | −5.4 dB, −191° / −3.6 dB, −231° | −29.4 dB, −238° / not plotted | +0.1 dB, −10° | +1.1 dB, −28° |
| OPA847 | 29.4 dB, −115° / 31.8 dB, −102° | 18.2 dB, −161° / 23.5 dB, −130° | −3.2 dB, −249° / 13.3 dB, phase not plotted | −18.5 dB, −308° / not plotted | −0.4 dB, +1° | −6.0 dB, +14° |
| LMH6624 | 21.2 dB, −113° / 20.0 dB, −130° | 9.7 dB, −154° / 7.0 dB, −197° | −11.1 dB, −244° / not plotted | −43.6 dB, −326° / not plotted | −0.0 dB, −1° | −0.1 dB, −4° |
| THS4021 | 20.4 dB, −105° / 23.5 dB, −126° | 15.5 dB, −174° / 12.8 dB, −163° | −15.8 dB, −310° / −9.8 dB, phase not plotted | −61.9 dB, −446° / not plotted | +0.0 dB, +0° | +1.0 dB, −1° |
| ADA4817-1 | 11.7 dB, −100° / 10.6 dB, −100° | 2.0 dB, −119° / 1.5 dB, −116° | −9.0 dB, −188° / −6.0 dB, −180° | −36.0 dB, −387° / not plotted | +0.0 dB, −0° | −0.0 dB, +0° |
| AD8099 | 30.9 dB, −98° / 31.6 dB, −102° | 21.2 dB, −113° / 22.9 dB, −140° | 8.4 dB, −162° / 11.4 dB, phase not plotted | −12.1 dB, −244° / −10.0 dB, phase not plotted | −0.0 dB, −0° | −0.0 dB, +0° |
| ADA4899-1 | 8.5 dB, −106° / 9.6 dB, −100° | −2.6 dB, −125° / 0.7 dB, −122° | −14.5 dB, −187° / −9.0 dB, phase not plotted | −36.4 dB, −345° / not plotted | +0.0 dB, −0° | −0.0 dB, +0° |
| ADA4895-1 | 23.0 dB, −118° / 23.6 dB, −118° | 12.2 dB, −141° / 12.9 dB, −142° | −6.6 dB, −229° / 0.9 dB, −219° | −35.6 dB, −295° / not plotted | −0.0 dB, −6° | −0.0 dB, −18° |
| OPA955 | 40.3 dB, −91° / 40.9 dB, −94° | 30.5 dB, −95° / 31.2 dB, −102° | 19.2 dB, −97° / 20.3 dB, −125° | 9.5 dB, −109° / 9.8 dB, −183° | +0.5 dB, −10° | −2.4 dB, −18° |

### Datasheet test circuits

| Amplifier and circuit | Datasheet statement | SPICE: $f_{-3\,\mathrm{dB}}$, peak; PM at $f_c$ | Datasheet curve, no $C_{\mathrm{in}}$ (Table 4.1) | Datasheet curve with $C_{CM} + C_{DIFF}$ | Macromodel parameters, Eq. (53) |
|---|---|---|---|---|---|
| OPA855, non-inverting, 453 Ω / 75 Ω, $R_L$ = 200 Ω, ±2.5 V | 62° at noise gain 7 (p18) | 3446 MHz, 0.64 dB; 59.9° at 1138 MHz | 5371 MHz, 6.20 dB; 73.9° at 1245 MHz | 4183 MHz, 3.54 dB; 55.2° at 1152 MHz | 3606 MHz, 2.42 dB; 59.3° at 1151 MHz |
| OPA818, non-inverting, 301 Ω / 50.5 Ω, $R_L$ = 100 Ω, ±5 V | about 50° at noise gain 7 (p16); 765 MHz and 1.4 dB peaking (p5) | 758 MHz, 1.37 dB; 54.0° at 370 MHz | 664 MHz, 1.22 dB; 51.7° at 352 MHz | 669 MHz, 4.26 dB; 39.9° at 344 MHz | 783 MHz, 1.86 dB; 54.0° at 370 MHz |
| OPA858, non-inverting, 453 Ω / 75 Ω, $R_L$ = 200 Ω, ±2.5 V | 55° at noise gain 7 (p18); 1.2 GHz and < 1 dB peaking at G = 7 (p6) | 1338 MHz, 0.42 dB; 58.1° at 702 MHz | 2555 MHz, 0.00 dB; 70.0° at 1277 MHz | 2690 MHz, 2.86 dB; 51.0° at 1186 MHz | 1376 MHz, 0.51 dB; 58.1° at 702 MHz |
| OPA856, unity-gain buffer, $R_L$ = 200 Ω, ±2.5 V | about 57° as a unity-gain buffer (p16) | 1075 MHz, 0.02 dB; 65.8° at 787 MHz | 2398 MHz, 0.69 dB; 56.1° at 961 MHz | 2398 MHz, 0.69 dB; 56.1° at 961 MHz | 1039 MHz, 0.05 dB; 68.1° at 777 MHz |
| LMH6629 (COMP HI), non-inverting, 249 Ω / 27.4 Ω, $R_L$ = 100 Ω, ±2.5 V | 900 MHz, no peaking at Av = +10, RL = 100 ohm, COMP high (p5) | 834 MHz, 0.00 dB; 64.1° at 452 MHz | 589 MHz, 0.01 dB; 71.2° at 388 MHz | 789 MHz, 1.37 dB; 54.0° at 369 MHz | 854 MHz, 0.00 dB; 63.8° at 455 MHz |
| OPA859, unity-gain buffer, $R_L$ = 200 Ω, ±2.5 V | about 63° as a unity-gain buffer (p18); 1.8 GHz at G = 1 (p6) | 1620 MHz, 1.03 dB; 62.7° at 917 MHz | 1251 MHz, 0.00 dB; 74.1° at 757 MHz | 1251 MHz, 0.00 dB; 74.1° at 757 MHz | 1429 MHz, 6.12 dB; 64.9° at 901 MHz |
| OPA846, non-inverting, 300 Ω / 50 Ω, $R_L$ = 100 Ω, ±5 V | 500 MHz at G = +7, RG = 50 ohm (p3); +3.1 dB near 350 MHz, −3 dB at 499 MHz (p4 curve) | 521 MHz, 1.38 dB; 51.0° at 261 MHz | 670 MHz, 2.33 dB; 53.7° at 245 MHz | 579 MHz, 5.58 dB; 41.4° at 237 MHz | 592 MHz, 2.02 dB; 49.7° at 267 MHz |
| OPA657, non-inverting, 453 Ω / 75.5 Ω, $R_L$ = 100 Ω, ±5 V | 350 MHz and 7 dB peaking at G = +7 (p5); RF/RG not printed, 453/75.5 ohm from the page header | 360 MHz, 5.84 dB; 34.4° at 190 MHz | 488 MHz, 6.58 dB; 29.0° at 282 MHz | 427 MHz, 23.90 dB; 5.1° at 256 MHz | 368 MHz, 6.08 dB; 34.4° at 190 MHz |
| OPA847, non-inverting, 431 Ω / 39.2 Ω, $R_L$ = 100 Ω, ±5 V | 600 MHz and 4.5 dB peaking (7 dB max) at G = +12, RG = 39.2 ohm (p3, p10) | 347 MHz, 5.34 dB; 33.3° at 186 MHz | 839 MHz, 10.96 dB; 31.6° at 407 MHz | 752 MHz, 15.71 dB; 18.0° at 381 MHz | 374 MHz, 11.98 dB; 19.4° at 210 MHz |
| LMH6624, non-inverting, 500 Ω / 55.6 Ω, $R_L$ = 100 Ω, ±6 V | no table value at Av = +10; curve with RF = 500 ohm, RL not printed: about 215 MHz, +0.7 dB (p11 Fig 14) | 212 MHz, 0.34 dB; 57.8° at 108 MHz | 195 MHz, 1.69 dB; 49.9° at 100 MHz | 198 MHz, 2.90 dB; 44.8° at 100 MHz | 219 MHz, 0.43 dB; 57.3° at 109 MHz |
| THS4021, non-inverting, 220 Ω / 24.4 Ω, $R_L$ = 150 Ω, ±15 V | 290 MHz at G = +10, +/−15 V (p6, SOIC); curve +1.6 dB (p10 Fig 5-1) | 336 MHz, 1.38 dB; 72.5° at 97 MHz | 307 MHz, 2.00 dB; 47.4° at 140 MHz | 311 MHz, 2.25 dB; 45.7° at 140 MHz | 337 MHz, 1.55 dB; 72.5° at 97 MHz |
| ADA4817-1, unity-gain buffer, $R_L$ = 100 Ω, ±5 V | 1050 MHz at G = +1 (p3); curve +3.1 dB (p8 Fig 8) | 1109 MHz, 3.31 dB; 49.2° at 396 MHz | 1302 MHz, 1.81 dB; 56.5° at 374 MHz | 1302 MHz, 1.81 dB; 56.5° at 374 MHz | 866 MHz, 1.10 dB; 53.3° at 378 MHz |
| AD8099, non-inverting, 250 Ω / 250 Ω with 1.5 pF across $R_F$, 50 Ω in series with IN+, CC network 50 Ω ∥ 1.5 pF then 4 pF to −$V_S$, $R_L$ = 1 kΩ, ±5 V | 700 MHz and 3.1 dB peaking at G = +2 with the SOIC compensation network (p17 Table 4, Fig 61) | 803 MHz, 4.34 dB; 46.6° at 400 MHz | not applicable (externally compensated) | not applicable (externally compensated) | not applicable (externally compensated) |
| ADA4899-1, unity-gain buffer, 24.9 Ω in series with IN+, $R_L$ = 1 kΩ, ±5 V | 605 MHz at G = +1 with RS = 24.9 ohm, RL = 1 kohm (p14 Table 4); curve +0.8 dB (p6 Fig 5) | 513 MHz, 0.77 dB; 55.5° at 269 MHz | 920 MHz, 7.63 dB; 52.5° at 342 MHz | 920 MHz, 7.63 dB; 52.5° at 342 MHz | 409 MHz, 0.45 dB; 60.0° at 233 MHz |
| ADA4895-1, non-inverting, 249 Ω / 27.7 Ω, $R_L$ = 1 kΩ, ±2.5 V | 216 MHz at G = +10, +/−2.5 V (p4 Table 3); curve +2.1 dB (p10 Fig 8) | 222 MHz, 2.04 dB; 46.7° at 115 MHz | 268 MHz, 1.11 dB; 55.9° at 146 MHz | 298 MHz, 3.91 dB; 39.4° at 140 MHz | 240 MHz, 2.29 dB; 46.6° at 115 MHz |
| OPA955, non-inverting, 453 Ω / 75.5 Ω, $R_L$ = 200 Ω, ±2.5 V | 2.8 GHz at G = +7, 100 mVpp (p5, advance information); curve 2.95 GHz with +1.3 dB, RF = 453 ohm (p7 Fig 6-1) | 2354 MHz, 3.68 dB; 41.7° at 1169 MHz | 3195 MHz, 3.82 dB; 39.7° at 1437 MHz | 2499 MHz, 14.56 dB; 15.9° at 1272 MHz | 2491 MHz, 4.29 dB; 41.7° at 1169 MHz |

### TIA loop, corners, response

| Design | SPICE nominal: $f_c$, PM, GM | SPICE over 9 corners: worst PM / worst GM | Survey model (datasheet curve): PM nominal / worst of 9 | SPICE $f_{-3\,\mathrm{dB}}$, peak | Survey $f_{-3\,\mathrm{dB}}$, peak | Step: overshoot, 10–90 % |
|---|---|---|---|---|---|---|
| OPA855 (A), 1 pF, 2 kΩ, $C_F$ = 0.25 pF | 942 MHz, 65.3°, 5.1 dB | 48.7° / 1.9 dB | 63.1° / 48.9° (second crossing at 1 corner) | 431 MHz, 0.00 dB | 421 MHz, 0.00 dB | 0.3 %, 798 ps |
| OPA855 (A), 2 pF, 2 kΩ, $C_F$ = 0.35 pF | 880 MHz, 69.1°, 5.5 dB | 60.4° / 3.1 dB | 67.9° / 61.2° | 291 MHz, 0.00 dB | 280 MHz, 0.00 dB | 0.0 %, 1188 ps |
| OPA855 (A), 1 pF, 1.5 kΩ, $C_F$ = 0.27 pF | 1032 MHz, 62.5°, 4.5 dB | 47.3° / 1.4 dB | 59.7° / 46.8° (second crossing at 1 corner) | 548 MHz, 0.00 dB | 539 MHz, 0.00 dB | 1.2 %, 621 ps |
| OPA855 (A), 2 pF, 1.5 kΩ, $C_F$ = 0.40 pF | 1006 MHz, 67.5°, 4.4 dB | 60.7° / 2.3 dB | 65.6° / 60.5° | 342 MHz, 0.00 dB | 330 MHz, 0.00 dB | 0.0 %, 999 ps |
| OPA818 (B), 1 pF, 2 kΩ, $C_F$ = 0.55 pF | 371 MHz, 48.9°, 16.1 dB | 45.4° / 14.8 dB | 32.9° / 29.9° | 226 MHz, 0.00 dB | 331 MHz, 0.00 dB | 0.7 %, 1510 ps |
| OPA818 (B), 2 pF, 2 kΩ, $C_F$ = 0.55 pF | 307 MHz, 49.5°, 17.9 dB | 44.3° / 16.6 dB | 34.8° / 30.3° | 231 MHz, 0.00 dB | 302 MHz, 0.00 dB | 3.5 %, 1467 ps |
| OPA818 (B), 1 pF, 1.5 kΩ, $C_F$ = 0.55 pF | 386 MHz, 43.3°, 15.2 dB | 39.0° / 14.1 dB | 26.8° / 22.8° | 333 MHz, 0.01 dB | 442 MHz, 0.79 dB | 4.0 %, 1009 ps |
| OPA818 (B), 2 pF, 1.5 kΩ, $C_F$ = 0.65 pF | 356 MHz, 46.9°, 16.1 dB | 43.4° / 15.0 dB | 31.1° / 28.1° | 268 MHz, 0.00 dB | 373 MHz, 0.00 dB | 2.7 %, 1258 ps |
| OPA856, 1 pF, 2 kΩ, $C_F$ = 0.55 pF | 208 MHz, 57.1°, 42.2 dB | 50.0° / 39.2 dB | 53.2° / 46.3° | 184 MHz, 0.11 dB | 205 MHz, 0.11 dB | 7.0 %, 1866 ps |
| LMH6629, 1 pF, 2 kΩ, $C_F$ = 0.55 pF | 801 MHz, 45.1°, 11.6 dB | 41.1° / 9.8 dB | 52.0° / 45.9° | 169 MHz, 0.00 dB | 229 MHz, 0.00 dB | 0.0 %, 2057 ps |
| OPA858, 1 pF, 2 kΩ, $C_F$ = 0.25 pF | 605 MHz, 48.9°, 26.7 dB | 32.6° / 23.0 dB | 62.4° / 49.3° | 508 MHz, 0.01 dB | 417 MHz, 0.00 dB | 5.6 %, 678 ps |
| OPA859, 1 pF, 2 kΩ, $C_F$ = 0.54 pF | 233 MHz, 57.1°, 19.9 dB | 49.7° / 18.2 dB | 62.5° / 55.2° | 196 MHz, 0.09 dB | 175 MHz, 0.02 dB | 6.6 %, 1741 ps |
| OPA846, 1 pF, 2 kΩ, $C_F$ = 0.75 pF | 308 MHz, 44.7°, 11.6 dB | 43.4° / 10.4 dB | 34.1° / 32.1° | 163 MHz, 0.00 dB | 233 MHz, 0.00 dB | 0.0 %, 2130 ps |
| OPA657, 1 pF, 2 kΩ, $C_F$ = 0.99 pF | 204 MHz, 36.1°, 12.3 dB | 34.7° / 11.4 dB | 16.3° / 15.2° | 162 MHz, 0.00 dB | 321 MHz, 0.00 dB | 0.0 %, 2200 ps |
| OPA847, 1 pF, 2 kΩ, $C_F$ = 0.35 pF | 170 MHz, 30.5°, 9.8 dB | 22.1° / 9.1 dB | 9.0° / 4.6° | 271 MHz, 4.27 dB | 551 MHz, 11.45 dB | 39.8 %, 1167 ps |
| LMH6624, 1 pF, 2 kΩ, $C_F$ = 1.17 pF | 203 MHz, 29.7°, 8.0 dB | 28.7° / 7.3 dB | 2.2° / 0.7° | 120 MHz, 0.00 dB | 232 MHz, 19.71 dB | 0.0 %, 2626 ps |
| THS4021, 1 pF, 2 kΩ, $C_F$ = 0.66 pF | 254 MHz, 12.6°, 0.3 dB | −17.1° / −0.1 dB | 3.4° / 0.5° | 322 MHz, 19.41 dB | 352 MHz, 17.73 dB | 31.2 %, 1212 ps |
| ADA4817-1, 1 pF, 2 kΩ, $C_F$ = 0.82 pF | 109 MHz, 48.5°, 19.7 dB | 44.0° / 18.4 dB | 48.7° / 44.1° | 120 MHz, 0.87 dB | 115 MHz, 1.00 dB | 13.6 %, 2802 ps |
| ADA4899-1, 1 pF, 2 kΩ, $C_F$ = 1.28 pF | 117 MHz, 61.3°, 20.5 dB | 59.3° / 19.6 dB | 49.9° / 46.9° | 74 MHz, 0.00 dB | 76 MHz, 0.87 dB | 0.0 %, 4679 ps |
| ADA4895-1, 1 pF, 2 kΩ, $C_F$ = 1.31 pF | 119 MHz, 33.4°, 14.7 dB | 31.2° / 14.1 dB | 34.6° / 32.5° | 127 MHz, 0.62 dB | 130 MHz, 0.02 dB | 11.1 %, 2782 ps |
| AD8099, 1 pF, 2 kΩ, $C_F$ = 0.20 pF | 216 MHz, 16.4°, 20.4 dB | 3.5° / 8.8 dB | −21.3° / −33.5° (second crossing at 1 corner) | 324 MHz, 9.96 dB | 492 MHz, 9.65 dB | 59.6 %, 887 ps |
| OPA955, 1 pF, 2 kΩ, $C_F$ = 0.25 pF | 954 MHz, 55.9°, no −180° crossing | 42.0° / 41.2 dB | 38.8° / 29.6° | 459 MHz, 0.00 dB | 530 MHz, 0.00 dB | 0.0 %, 747 ps |

### OPA855 1 pF 2 kOhm corner grid

| Total $C_F$ | $C_D$ − 0.2 pF | $C_D$ nominal | $C_D$ + 0.2 pF |
|---|---|---|---|
| 0.15 pF | 51.7° / 8.2 dB (50.9°) | 50.1° / 9.0 dB (50.0°) | 48.7° / 9.7 dB (48.9°) |
| 0.25 pF | 65.9° / 4.4 dB (63.0°) | 65.3° / 5.1 dB (63.1°) | 64.6° / 5.8 dB (62.9°) |
| 0.35 pF | 68.5° / 1.9 dB (62.7° *) | 69.2° / 2.6 dB (65.0°) | 69.5° / 3.2 dB (66.0°) |

### OPA855 1 pF 1.5 kOhm corner grid

| Total $C_F$ | $C_D$ − 0.2 pF | $C_D$ nominal | $C_D$ + 0.2 pF |
|---|---|---|---|
| 0.17 pF | 50.2° / 7.2 dB (48.4°) | 48.7° / 7.9 dB (47.5°) | 47.3° / 8.7 dB (46.8°) |
| 0.27 pF | 63.1° / 3.7 dB (59.4°) | 62.5° / 4.5 dB (59.7°) | 61.7° / 5.1 dB (59.5°) |
| 0.37 pF | 65.8° / 1.4 dB (59.4° *) | 66.6° / 2.1 dB (61.4°) | 66.9° / 2.8 dB (62.9°) |

### Consistency

| Design | $C_T$ of the model (pF) | Survey method, Eqs. (7)–(8): PM, GM, $f_{-3\,\mathrm{dB}}$ | Two-port, Eq. (52): PM, GM, $f_{-3\,\mathrm{dB}}$ | SPICE: PM, GM, $f_{-3\,\mathrm{dB}}$ | Noise, Eq. (17) against SPICE, 10–200 MHz |
|---|---|---|---|---|---|
| OPA855 (A), 1 pF, 2 kΩ, $C_F$ = 0.25 pF | 2.17 | 65.7°, 9.9 dB, 438 MHz | 65.3°, 5.2 dB, 431 MHz | 65.3°, 5.1 dB, 431 MHz | within 0.0 % |
| OPA855 (A), 2 pF, 2 kΩ, $C_F$ = 0.35 pF | 3.18 | 69.9°, 10.4 dB, 295 MHz | 69.1°, 5.6 dB, 291 MHz | 69.1°, 5.5 dB, 291 MHz | within 0.0 % |
| OPA855 (A), 1 pF, 1.5 kΩ, $C_F$ = 0.27 pF | 2.17 | 63.2°, 9.1 dB, 553 MHz | 62.5°, 4.5 dB, 547 MHz | 62.5°, 4.5 dB, 548 MHz | within 0.2 % |
| OPA855 (A), 2 pF, 1.5 kΩ, $C_F$ = 0.40 pF | 3.18 | 68.9°, 9.3 dB, 346 MHz | 67.5°, 4.5 dB, 342 MHz | 67.5°, 4.4 dB, 342 MHz | within 0.2 % |
| OPA818 (B), 1 pF, 2 kΩ, $C_F$ = 0.55 pF | 3.75 | 50.6°, 23.1 dB, 222 MHz | 48.9°, 16.2 dB, 226 MHz | 48.9°, 16.1 dB, 226 MHz | within 0.0 % |
| OPA818 (B), 2 pF, 2 kΩ, $C_F$ = 0.55 pF | 4.76 | 50.8°, 24.8 dB, 227 MHz | 49.5°, 17.9 dB, 231 MHz | 49.5°, 17.9 dB, 231 MHz | within 0.0 % |
| OPA818 (B), 1 pF, 1.5 kΩ, $C_F$ = 0.55 pF | 3.75 | 45.1°, 21.2 dB, 323 MHz | 43.3°, 15.2 dB, 333 MHz | 43.3°, 15.2 dB, 333 MHz | within 0.0 % |
| OPA818 (B), 2 pF, 1.5 kΩ, $C_F$ = 0.65 pF | 4.76 | 48.6°, 22.8 dB, 261 MHz | 46.9°, 16.1 dB, 268 MHz | 46.9°, 16.1 dB, 268 MHz | within 0.0 % |
| OPA856, 1 pF, 2 kΩ, $C_F$ = 0.55 pF | 2.47 | 54.5°, – dB, 191 MHz | 57.1°, 42.2 dB, 184 MHz | 57.1°, 42.2 dB, 184 MHz | within 0.2 % |
| LMH6629, 1 pF, 2 kΩ, $C_F$ = 0.55 pF | 2.67 | 51.5°, 17.0 dB, 172 MHz | 45.1°, 11.6 dB, 169 MHz | 45.1°, 11.6 dB, 169 MHz | within 0.1 % |
| OPA858, 1 pF, 2 kΩ, $C_F$ = 0.25 pF | 2.19 | 49.2°, 30.8 dB, 505 MHz | 48.9°, 26.7 dB, 508 MHz | 48.9°, 26.7 dB, 508 MHz | within 0.0 % |
| OPA859, 1 pF, 2 kΩ, $C_F$ = 0.54 pF | 2.19 | 57.3°, 18.6 dB, 195 MHz | 57.1°, 19.9 dB, 196 MHz | 57.1°, 19.9 dB, 196 MHz | within 0.1 % |
| OPA846, 1 pF, 2 kΩ, $C_F$ = 0.75 pF | 4.46 | 41.6°, 9.9 dB, 172 MHz | 44.7°, 11.6 dB, 163 MHz | 44.7°, 11.6 dB, 163 MHz | within 0.3 % |
| OPA657, 1 pF, 2 kΩ, $C_F$ = 0.99 pF | 6.61 | 39.2°, 17.0 dB, 151 MHz | 36.2°, 12.3 dB, 161 MHz | 36.1°, 12.3 dB, 162 MHz | within 0.0 % |
| OPA847, 1 pF, 2 kΩ, $C_F$ = 0.35 pF | 8.98 | −2.0°, – dB, 251 MHz | 34.5°, 8.5 dB, 296 MHz | 30.5°, 9.8 dB, 271 MHz | within 0.0 % |
| LMH6624, 1 pF, 2 kΩ, $C_F$ = 1.17 pF | 5.20 | 29.8°, 8.8 dB, 128 MHz | 29.8°, 8.0 dB, 119 MHz | 29.7°, 8.0 dB, 120 MHz | within 0.4 % |
| THS4021, 1 pF, 2 kΩ, $C_F$ = 0.66 pF | 4.01 | 12.2°, 0.3 dB, 320 MHz | 12.9°, 0.4 dB, 322 MHz | 12.6°, 0.3 dB, 322 MHz | within 0.2 % |
| ADA4817-1, 1 pF, 2 kΩ, $C_F$ = 0.82 pF | 2.98 | 48.6°, 20.9 dB, 119 MHz | 48.5°, 19.7 dB, 119 MHz | 48.5°, 19.7 dB, 120 MHz | within 0.2 % |
| ADA4899-1, 1 pF, 2 kΩ, $C_F$ = 1.28 pF | 1.77 | 55.9°, 20.9 dB, 84 MHz | 61.4°, 20.5 dB, 73 MHz | 61.3°, 20.5 dB, 74 MHz | within 1.5 % |
| ADA4895-1, 1 pF, 2 kΩ, $C_F$ = 1.31 pF | 15.49 | 36.1°, 16.2 dB, 123 MHz | 33.4°, 14.7 dB, 127 MHz | 33.4°, 14.7 dB, 127 MHz | within 1.0 % |
| AD8099, 1 pF, 2 kΩ, $C_F$ = 0.20 pF | 6.51 | 15.0°, 20.4 dB, 325 MHz | 16.4°, 20.4 dB, 324 MHz | 16.4°, 20.4 dB, 324 MHz | within 0.1 % |
| OPA955, 1 pF, 2 kΩ, $C_F$ = 0.25 pF | 2.47 | 65.0°, – dB, 451 MHz | 55.9°, – dB, 459 MHz | 55.9°, – dB, 459 MHz | within 0.0 % |

### Noise

| Design | 50 MHz | 100 MHz | 200 MHz | Penalty 10–150 MHz: SPICE / survey central (high) |
|---|---|---|---|---|
| OPA855 (A), 1 pF, 2 kΩ, $C_F$ = 0.25 pF | 3.92 / 3.97 | 4.11 / 4.18 | 4.83 / 4.91 | 3.02 / 3.15 dB |
| OPA855 (A), 2 pF, 2 kΩ, $C_F$ = 0.35 pF | 3.99 / 4.05 | 4.40 / 4.47 | 5.73 / 5.83 | 3.50 / 3.64 dB |
| OPA855 (A), 1 pF, 1.5 kΩ, $C_F$ = 0.27 pF | 4.28 / 4.33 | 4.47 / 4.52 | 5.14 / 5.21 | 2.50 / 2.60 dB |
| OPA855 (A), 2 pF, 1.5 kΩ, $C_F$ = 0.40 pF | 4.35 / 4.40 | 4.74 / 4.80 | 6.03 / 6.13 | 2.93 / 3.03 dB |
| OPA818 (B), 1 pF, 2 kΩ, $C_F$ = 0.55 pF | 4.85 / 4.19 (4.42) | 7.83 / 6.49 (7.00) | 14.51 / 11.86 (12.84) | 7.95 / 6.37 (7.00) dB |
| OPA818 (B), 2 pF, 2 kΩ, $C_F$ = 0.55 pF | 5.29 / 4.67 (4.88) | 8.89 / 7.69 (8.13) | 16.78 / 14.45 (15.26) | 9.01 / 7.78 (8.24) dB |
| OPA818 (B), 1 pF, 1.5 kΩ, $C_F$ = 0.55 pF | 5.21 / 4.60 (4.82) | 8.06 / 6.77 (7.25) | 14.63 / 12.01 (12.98) | 7.00 / 5.54 (6.11) dB |
| OPA818 (B), 2 pF, 1.5 kΩ, $C_F$ = 0.65 pF | 5.66 / 5.09 (5.28) | 9.20 / 8.04 (8.46) | 17.12 / 14.83 (15.63) | 8.10 / 6.96 (7.38) dB |
| OPA856, 1 pF, 2 kΩ, $C_F$ = 0.55 pF | 3.98 / 3.96 | 4.25 / 4.23 | 5.18 / 5.17 | 3.27 / 3.23 dB |
| LMH6629, 1 pF, 2 kΩ, $C_F$ = 0.55 pF | 3.95 / 4.22 | 4.12 / 5.10 | 4.76 / 7.65 | 3.05 / 4.62 dB |
| OPA858, 1 pF, 2 kΩ, $C_F$ = 0.25 pF | 3.63 / 3.65 (4.36) | 4.85 / 4.86 (6.73) | 8.05 / 8.08 (12.02) | 4.02 / 4.05 (6.65) dB |
| OPA859, 1 pF, 2 kΩ, $C_F$ = 0.54 pF | 4.14 / 4.30 (4.93) | 6.10 / 6.44 (7.94) | 11.08 / 11.55 (14.58) | 5.91 / 6.34 (8.06) dB |
| OPA846, 1 pF, 2 kΩ, $C_F$ = 0.75 pF | 4.41 / 4.64 | 5.34 / 6.07 | 8.15 / 9.91 | 5.03 / 6.01 dB |
| OPA657, 1 pF, 2 kΩ, $C_F$ = 0.99 pF | 11.84 / 11.97 | 22.78 / 23.05 | 45.06 / 45.63 | 17.07 / 17.17 dB |
| OPA847, 1 pF, 2 kΩ, $C_F$ = 0.35 pF | 7.27 / 4.10 | 11.39 / 4.81 | 17.54 / 6.97 | 10.99 / 4.16 dB |
| LMH6624, 1 pF, 2 kΩ, $C_F$ = 1.17 pF | 3.95 / 4.02 | 4.93 / 4.85 | 7.73 / 7.28 | 4.28 / 4.19 dB |
| THS4021, 1 pF, 2 kΩ, $C_F$ = 0.66 pF | 3.61 / 3.95 | 4.82 / 4.57 | 8.09 / 6.47 | 3.99 / 3.75 dB |
| ADA4817-1, 1 pF, 2 kΩ, $C_F$ = 0.82 pF | 5.21 / 5.65 | 8.66 / 9.41 | 16.28 / 17.84 | 8.80 / 9.53 dB |
| ADA4899-1, 1 pF, 2 kΩ, $C_F$ = 1.28 pF | 3.89 / 4.49 | 4.16 / 5.90 | 5.09 / 9.66 | 3.08 / 5.75 dB |
| ADA4895-1, 1 pF, 2 kΩ, $C_F$ = 1.31 pF | 5.84 / 6.20 | 10.18 / 10.98 | 19.40 / 21.20 | 10.15 / 10.80 dB |
| AD8099, 1 pF, 2 kΩ, $C_F$ = 0.20 pF | 4.18 / 4.04 | 5.25 / 4.50 | 8.22 / 6.82 | 4.81 / 3.73 dB |
| OPA955, 1 pF, 2 kΩ, $C_F$ = 0.25 pF | 3.02 / 3.03 (3.07) | 3.24 / 3.25 (3.39) | 4.00 / 4.02 (4.41) | 0.91 / 0.93 (1.24) dB |

### Tone

| Amplifier, design | Tone | Table 6.2b amplitude | SPICE: amplitude at THD = −60 dBc | at THD = −40 dBc | At the Table 6.2b amplitude: HD2, HD3 |
|---|---|---|---|---|---|
| OPA855 (A), 1 pF, 2 kΩ | 20 MHz | 1.52 V | 1.42 V (0.93 ×) | 1.59 V (1.04 ×) | −61.4, −49.9 dBc |
| OPA855 (A), 1 pF, 2 kΩ | 50 MHz | 1.52 V | 1.38 V (0.90 ×) | 1.54 V (1.01 ×) | −58.4, −45.1 dBc |
| OPA855 (A), 1 pF, 2 kΩ | 100 MHz | 1.52 V | 1.35 V (0.89 ×) | 1.52 V (1.00 ×) | −55.6, −41.8 dBc |
| OPA855 (A), 1 pF, 2 kΩ | 150 MHz | 1.52 V | 1.35 V (0.88 ×) | 1.52 V (0.99 ×) | −54.2, −40.8 dBc |
| OPA855 (A), 1 pF, 2 kΩ | 200 MHz | 1.52 V | 1.35 V (0.88 ×) | 1.52 V (1.00 ×) | −53.5, −40.9 dBc |
| OPA818 (B), 1 pF, 2 kΩ | 20 MHz | 5.50 V | 5.09 V (0.93 ×) | 5.41 V (0.98 ×) | −45.5, −40.6 dBc |
| OPA818 (B), 1 pF, 2 kΩ | 50 MHz | 4.46 V | 4.43 V (0.99 ×) | 4.61 V (1.03 ×) | −58.9, −56.8 dBc |
| OPA818 (B), 1 pF, 2 kΩ | 100 MHz | 2.23 V | 2.22 V (1.00 ×) | 2.32 V (1.04 ×) | −61.8, −61.3 dBc |
| OPA818 (B), 1 pF, 2 kΩ | 150 MHz | 1.49 V | 1.50 V (1.01 ×) | 1.56 V (1.05 ×) | −69.0, −69.7 dBc |
| OPA818 (B), 1 pF, 2 kΩ | 200 MHz | 1.11 V | 1.15 V (1.03 ×) | 1.19 V (1.07 ×) | −92.1, −93.7 dBc |

### OPA846 bench board

| Total node capacitance $C_T$ | SPICE: PM, GM | SPICE: $\lvert Z_T\rvert$ at 50 MHz; peak | SPICE noise at 10 / 50 MHz (pA/√Hz) | Survey model: PM; $\lvert Z_T\rvert$ at 50 MHz; peak | Survey noise at 10 / 50 MHz (pA/√Hz) |
|---|---|---|---|---|---|
| 5.15 pF | 12.6°, 13.8 dB | 1.25 kΩ; +12.1 dB at 234 MHz | 4.78 / 5.10 | 1.3°; 1.28 kΩ; +31.9 dB at 213 MHz | 4.77 / 5.19 |
| 12 pF | 8.3°, 17.9 dB | 1.34 kΩ; +16.4 dB at 151 MHz | 4.84 / 6.32 | 1.6°; 1.41 kΩ; +30.7 dB at 134 MHz | 4.85 / 6.69 |
| 14 pF | 7.7°, 18.8 dB | 1.37 kΩ; +17.1 dB at 141 MHz | 4.86 / 6.80 | 1.8°; 1.45 kΩ; +29.6 dB at 123 MHz | 4.88 / 7.25 |
| 16 pF | 7.2°, 19.6 dB | 1.40 kΩ; +17.7 dB at 132 MHz | 4.89 / 7.32 | 2.1°; 1.49 kΩ; +28.4 dB at 115 MHz | 4.91 / 7.85 |

### Variant A C_F windows

| Configuration | SPICE, nominal $C_D$ | SPICE, $C_D$ ± 0.2 pF | Survey model, $C_D$ ± 0.2 pF | Minimum-gain rule $C_T/6$, $C_D$ − 0.2 pF / nominal |
|---|---|---|---|---|
| 1 pF, 2 kΩ | 0.150–0.331 pF (peaking / GM) | 0.157–0.300 pF (peaking / GM) | 0.151–0.340 pF (peaking / second crossing) | 0.325 / 0.358 pF |
| 1 pF, 1.5 kΩ | 0.174–0.329 pF (peaking / GM) | 0.181–0.298 pF (peaking / GM) | 0.176–0.340 pF (peaking / second crossing) | 0.325 / 0.358 pF |
| 2 pF, 2 kΩ | 0.182–0.485 pF (peaking / GM) | 0.188–0.454 pF (peaking / GM) | 0.177–0.520 pF (peaking / second crossing) | 0.492 / 0.525 pF |
| 2 pF, 1.5 kΩ | 0.211–0.484 pF (peaking / GM) | 0.217–0.453 pF (peaking / GM) | 0.208–0.520 pF (peaking / second crossing) | 0.492 / 0.525 pF |

### Variant A proposed C_F

| Configuration | Total $C_F$ (tolerance) | Nine corners: worst PM / worst GM / largest peaking | $f_{-3\,\mathrm{dB}}$: nominal (range over corners) | Noise at 100 / 200 MHz (pA/√Hz); penalty 10–150 MHz |
|---|---|---|---|---|
| 1 pF, 2 kΩ | 0.230 ± 0.070 pF | 50.9° / 3.0 dB / 0.87 dB | 481 MHz (327–684 MHz) | 4.11 / 4.81; 3.02 dB |
| 1 pF, 1.5 kΩ | 0.240 ± 0.055 pF | 50.2° / 3.1 dB / 0.89 dB | 630 MHz (476–796 MHz) | 4.46 / 5.12; 2.49 dB |
| 2 pF, 2 kΩ | 0.320 ± 0.130 pF | 51.1° / 3.1 dB / 0.92 dB | 330 MHz (204–567 MHz) | 4.39 / 5.71; 3.49 dB |
| 2 pF, 1.5 kΩ | 0.335 ± 0.115 pF | 50.5° / 3.0 dB / 0.93 dB | 438 MHz (286–658 MHz) | 4.72 / 5.98; 2.90 dB |

### Variant B smaller C_F

| Configuration | Present design: total $C_F$, $f_{-3\,\mathrm{dB}}$ | Requirement over the corners | Smallest $C_F$ meeting it at exactly that $C_F$: SPICE / survey model | Proposed total $C_F$ (tolerance) | Nine corners: worst PM | $f_{-3\,\mathrm{dB}}$ nominal (range) | Peaking nominal (largest) | Noise at 100 / 200 MHz; penalty |
|---|---|---|---|---|---|---|---|---|
| 1 pF, 2 kΩ | 0.55 pF, 226 MHz | PM ≥ 45°, $C_F$ ± 0.1 pF | 0.443 pF / none | 0.55 ± 0.1 pF | 45.4° | 226 MHz (169–294) | 0.00 dB (0.20 dB) | 7.83 / 14.51; 7.95 dB |
| | | PM ≥ 45°, $C_F$ ± 0.05 pF | 0.443 pF / none | 0.50 ± 0.05 pF | 45.4° | 259 MHz (223–294) | 0.00 dB (0.20 dB) | 7.78 / 14.40; 7.89 dB |
| | | PM ≥ 40°, $C_F$ ± 0.1 pF | 0.368 pF / none | 0.47 ± 0.1 pF | 40.2° | 279 MHz (210–341) | 0.02 dB (1.35 dB) | 7.75 / 14.33; 7.86 dB |
| | | PM ≥ 40°, $C_F$ ± 0.05 pF | 0.368 pF / none | 0.42 ± 0.05 pF | 40.2° | 309 MHz (277–341) | 0.39 dB (1.35 dB) | 7.70 / 14.22; 7.80 dB |
| 2 pF, 2 kΩ | 0.55 pF, 231 MHz | PM ≥ 45°, $C_F$ ± 0.1 pF | 0.462 pF / none | 0.57 ± 0.1 pF | 45.5° | 221 MHz (172–271) | 0.00 dB (0.49 dB) | 8.91 / 16.83; 9.03 dB |
| | | PM ≥ 45°, $C_F$ ± 0.05 pF | 0.462 pF / none | 0.52 ± 0.05 pF | 45.5° | 245 MHz (220–271) | 0.04 dB (0.49 dB) | 8.86 / 16.71; 8.98 dB |
| | | PM ≥ 40°, $C_F$ ± 0.1 pF | 0.391 pF / none | 0.50 ± 0.1 pF | 40.8° | 255 MHz (204–299) | 0.14 dB (1.53 dB) | 8.84 / 16.66; 8.96 dB |
| | | PM ≥ 40°, $C_F$ ± 0.05 pF | 0.391 pF / none | 0.45 ± 0.05 pF | 40.8° | 276 MHz (253–299) | 0.62 dB (1.53 dB) | 8.78 / 16.55; 8.91 dB |
| 1 pF, 1.5 kΩ | 0.55 pF, 333 MHz | PM ≥ 45° | not reached: best worst case 44.7° at 0.70 pF / none | – | – | – | – | – |
| | | PM ≥ 40°, $C_F$ ± 0.1 pF | 0.469 pF / none | 0.57 ± 0.1 pF | 40.1° | 319 MHz (242–391) | 0.00 dB (0.78 dB) | 8.08 / 14.68; 7.02 dB |
| | | PM ≥ 40°, $C_F$ ± 0.05 pF | 0.469 pF / none | 0.52 ± 0.05 pF | 40.1° | 354 MHz (318–391) | 0.13 dB (0.78 dB) | 8.03 / 14.57; 6.96 dB |
| 2 pF, 1.5 kΩ | 0.65 pF, 268 MHz | PM ≥ 45°, $C_F$ ± 0.1 pF | 0.589 pF / none | 0.69 ± 0.1 pF | 45.0° | 246 MHz (195–301) | 0.00 dB (0.16 dB) | 9.25 / 17.22; 8.14 dB |
| | | PM ≥ 45°, $C_F$ ± 0.05 pF | 0.589 pF / none | 0.64 ± 0.05 pF | 45.0° | 273 MHz (245–301) | 0.00 dB (0.16 dB) | 9.19 / 17.10; 8.09 dB |
| | | PM ≥ 40°, $C_F$ ± 0.1 pF | 0.485 pF / none | 0.59 ± 0.1 pF | 40.3° | 299 MHz (245–347) | 0.09 dB (1.21 dB) | 9.14 / 16.98; 8.04 dB |
| | | PM ≥ 40°, $C_F$ ± 0.05 pF | 0.485 pF / none | 0.54 ± 0.05 pF | 40.3° | 322 MHz (297–347) | 0.46 dB (1.21 dB) | 9.08 / 16.87; 7.99 dB |

### Best design of every part, 1 pF, 2 kOhm

| Amplifier | Window meeting all criteria (edges set by) | Design: total $C_F$ | Worst PM / GM / peaking over its corners | $f_{-3\,\mathrm{dB}}$ nominal (range) | Noise at 100 MHz; penalty 10–150 MHz | Largest worst-case PM (at $C_F$) |
|---|---|---|---|---|---|---|
| OPA955 | 0.167–0.813 pF (pm / pm) | 0.220 ± 0.050 pF | 46.0° / – / 0.62 dB | 560 MHz (396–739) | 3.24 pA/√Hz; 0.90 dB | 58.0° (0.35 pF) |
| OPA855 | 0.159–0.300 pF (peak / gm) | 0.210 ± 0.050 pF | 50.9° / 4.1 dB / 0.87 dB | 535 MHz (400–684) | 4.11 pA/√Hz; 3.01 dB | 68.5° (0.35 pF) |
| OPA858 | 0.225–1.153 pF (pm / pm) | 0.280 ± 0.050 pF | 45.9° / 23.6 dB / 0.46 dB | 446 MHz (338–555) | 4.88 pA/√Hz; 4.08 dB | 56.0° (0.45 pF) |
| LMH6629 (COMP HI) | 0.351–0.482 pF (pm / pm) | 0.405 ± 0.050 pF | 45.1° / 12.4 dB / 0.00 dB | 276 MHz (220–364) | 4.10 pA/√Hz; 3.01 dB | 45.6° (0.40 pF) |
| OPA818 | 0.443–0.912 pF (pm / pm) | 0.495 ± 0.050 pF | 45.1° / 15.8 dB / 0.24 dB | 262 MHz (226–297) | 7.77 pA/√Hz; 7.89 dB | 49.1° (0.65 pF) |
| OPA859 | 0.441 pF to beyond 2.40 pF (peak / –) | 0.495 ± 0.050 pF | 50.1° / 19.1 dB / 0.94 dB | 209 MHz (193–227) | 6.03 pA/√Hz; 5.82 dB | 71.7° (1.55 pF) |
| AD8099 | 0.587–1.087 pF (pm / pm) | 0.640 ± 0.050 pF | 45.1° / 14.5 dB / 0.00 dB | 202 MHz (174–232) | 5.42 pA/√Hz; 5.05 dB | 47.4° (0.80 pF) |
| OPA856 | 0.447 pF to beyond 2.40 pF (peak / –) | 0.500 ± 0.050 pF | 50.0° / 41.7 dB / 0.97 dB | 196 MHz (182–211) | 4.24 pA/√Hz; 3.25 dB | 72.5° (1.65 pF) |
| ADA4899-1 | 0.654 pF to beyond 2.40 pF (peak / –) | 0.705 ± 0.050 pF | 47.5° / 22.5 dB / 0.99 dB | 119 MHz (114–126) | 4.04 pA/√Hz; 2.86 dB | 65.3° (2.35 pF) |
| ADA4817-1 | 0.826 pF to beyond 2.40 pF (peak / –) | 0.880 ± 0.050 pF | 48.0° / 18.3 dB / 0.97 dB | 115 MHz (110–121) | 8.78 pA/√Hz; 8.91 dB | 66.2° (2.40 pF) |
| OPA817 | 0.959 pF to beyond 2.40 pF (peak / –) | 1.010 ± 0.050 pF | 50.0° / 25.8 dB / 0.99 dB | 97 MHz (94–101) | 15.37 pA/√Hz; 13.68 dB | 70.6° (2.40 pF) |
| OPA814 | 1.089 pF to beyond 2.40 pF (peak / –) | 1.140 ± 0.050 pF | 50.9° / 29.2 dB / 1.00 dB | 81 MHz (78–83) | 17.76 pA/√Hz; 14.93 dB | 70.2° (2.40 pF) |
| THS4021 | none | 0.50 pF (criteria not met) | 22.0° / 1.4 dB / 9.59 dB | 314 MHz (310–317) | 4.73 pA/√Hz; 3.84 dB | 22.0° (0.50 pF) |
| OPA847 | none | 0.65 pF (criteria not met) | 41.3° / 7.4 dB / 0.42 dB | 206 MHz (203–209) | 11.42 pA/√Hz; 11.01 dB | 41.3° (0.65 pF) |
| LMH6624 | none | 1.10 pF (criteria not met) | 29.2° / 8.1 dB / 0.00 dB | 176 MHz (170–177) | 4.90 pA/√Hz; 4.24 dB | 29.2° (1.10 pF) |
| OPA846 | none | 0.80 pF (criteria not met) | 44.5° / 10.9 dB / 0.00 dB | 144 MHz (142–147) | 5.36 pA/√Hz; 5.06 dB | 44.5° (0.80 pF) |
| OPA657 | none | 1.15 pF (criteria not met) | 36.6° / 11.0 dB / 0.00 dB | 108 MHz (106–109) | 23.25 pA/√Hz; 17.25 dB | 36.6° (1.15 pF) |
| ADA4895-1 | none | 2.05 pF (criteria not met) | 39.1° / 11.3 dB / 0.00 dB | 58 MHz (58–59) | 10.57 pA/√Hz; 10.47 dB | 39.1° (2.05 pF) |

### C_F scan rules (text)

1 pF, 2 kOhm, C_D 0.8 pF: GM 3 dB at C_F 0.300 pF, NG 7.51; GM 0 dB at C_F 0.454 pF, NG 5.30
1 pF, 2 kOhm, C_D 1.0 pF: GM 3 dB at C_F 0.331 pF, NG 7.50; GM 0 dB at C_F 0.500 pF, NG 5.30
1 pF, 2 kOhm, C_D 1.2 pF: GM 3 dB at C_F 0.362 pF, NG 7.50; GM 0 dB at C_F 0.546 pF, NG 5.30
1 pF, 2 kOhm: worst-case PM reaches 45° at C_F 0.135 pF
1 pF, 1.5 kOhm, C_D 0.8 pF: GM 3 dB at C_F 0.298 pF, NG 7.55; GM 0 dB at C_F 0.452 pF, NG 5.31
1 pF, 1.5 kOhm, C_D 1.0 pF: GM 3 dB at C_F 0.329 pF, NG 7.54; GM 0 dB at C_F 0.499 pF, NG 5.31
1 pF, 1.5 kOhm, C_D 1.2 pF: GM 3 dB at C_F 0.360 pF, NG 7.53; GM 0 dB at C_F 0.545 pF, NG 5.31
1 pF, 1.5 kOhm: worst-case PM reaches 45° at C_F 0.159 pF
2 pF, 2 kOhm, C_D 1.8 pF: GM 3 dB at C_F 0.454 pF, NG 7.49; GM 0 dB: not reached
2 pF, 2 kOhm, C_D 2.0 pF: GM 3 dB at C_F 0.485 pF, NG 7.49; GM 0 dB: not reached
2 pF, 2 kOhm, C_D 2.2 pF: GM 3 dB at C_F 0.516 pF, NG 7.49; GM 0 dB: not reached
2 pF, 2 kOhm: worst-case PM reaches 45° at C_F 0.160 pF
2 pF, 1.5 kOhm, C_D 1.8 pF: GM 3 dB at C_F 0.453 pF, NG 7.51; GM 0 dB: not reached
2 pF, 1.5 kOhm, C_D 2.0 pF: GM 3 dB at C_F 0.484 pF, NG 7.51; GM 0 dB: not reached
2 pF, 1.5 kOhm, C_D 2.2 pF: GM 3 dB at C_F 0.515 pF, NG 7.51; GM 0 dB: not reached
2 pF, 1.5 kOhm: worst-case PM reaches 45° at C_F 0.188 pF
B 1 pF, 2 kOhm: at the smallest C_F 0.15 pF, nominal f3 375 MHz with 10.6 dB peaking; crossover 244 MHz
B 1 pF, 1.5 kOhm: at the smallest C_F 0.15 pF, nominal f3 434 MHz with 13.7 dB peaking; crossover 279 MHz
B 2 pF, 2 kOhm: at the smallest C_F 0.15 pF, nominal f3 331 MHz with 11.5 dB peaking; crossover 215 MHz
B 2 pF, 1.5 kOhm: at the smallest C_F 0.15 pF, nominal f3 384 MHz with 14.4 dB peaking; crossover 246 MHz

### Hidden margin (text)

OPA855 (A), 1 pF, 2 kΩ, $C_F$ = 0.25 pF, corner dCF+0.1_dCD-0.2: GM 1.9 dB; |Z_T|/R_F bump −11.1 dB at 3.43 GHz; in-band peak 0.00 dB
OPA855 (A), 2 pF, 2 kΩ, $C_F$ = 0.35 pF, corner dCF+0.1_dCD-0.2: GM 3.1 dB; |Z_T|/R_F bump −18.0 dB at 3.43 GHz; in-band peak 0.00 dB
OPA855 (A), 1 pF, 1.5 kΩ, $C_F$ = 0.27 pF, corner dCF+0.1_dCD-0.2: GM 1.4 dB; |Z_T|/R_F bump −6.7 dB at 3.43 GHz; in-band peak 0.00 dB
OPA855 (A), 2 pF, 1.5 kΩ, $C_F$ = 0.40 pF, corner dCF+0.1_dCD-0.2: GM 2.3 dB; |Z_T|/R_F bump −13.3 dB at 3.43 GHz; in-band peak 0.00 dB
