## Gain table

| $R_F$ | $\sqrt{4k_BT/R_F}$ | $2k_BT/(qR_F)$ | $I_{\max}$ at 10 V | $I_{\max}$ at 2.4 V | $1/(2\pi R_FC_{par})$, 0.05 / 0.1 / 0.2 pF |
|---|---|---|---|---|---|
| 10 kΩ | 1.28 pA/√Hz | 5.14 µA | 1 mA | 240 µA | 318 MHz / 159 MHz / 79.6 MHz |
| 100 kΩ | 406 fA/√Hz | 514 nA | 100 µA | 24 µA | 31.8 MHz / 15.9 MHz / 7.96 MHz |
| 1 MΩ | 128 fA/√Hz | 51.4 nA | 10 µA | 2.4 µA | 3.18 MHz / 1.59 MHz / 796 kHz |
| 10 MΩ | 40.6 fA/√Hz | 5.14 nA | 1 µA | 240 nA | 318 kHz / 159 kHz / 79.6 kHz |
| 100 MΩ | 12.8 fA/√Hz | 514 pA | 100 nA | 24 nA | 31.8 kHz / 15.9 kHz / 7.96 kHz |
| 1 GΩ | 4.06 fA/√Hz | 51.4 pA | 10 nA | 2.4 nA | 3.18 kHz / 1.59 kHz / 796 Hz |



## Amplifier figures of merit

| Part | Input | GBW (MHz) | $C_{CM}+C_{DIFF}$ (pF) | $e_n$ at 10 Hz / 1 kHz / 100 kHz (nV/√Hz) | $i_n$ (fA/√Hz) | $R_{F,\mathrm{crit}}=4k_BT/i_n^2$ | $I_B$ max 25 °C / 85 °C | $V_{OS}$ max (µV) |
|---|---|---|---|---|---|---|---|---|
| ADA4530-1 | CMOS electrometer, integrated guard buffer | 2 | 8 | 80 / 16 / – | 0.07 | 3.36e+03 GΩ | 20 fA / 20 fA | 40 |
| OPA928 | CMOS electrometer, integrated guard buffer | 2.5 | 9 | – / 15 / – | 0.07 | 3.36e+03 GΩ | 20 fA / 20 fA | 25 |
| LMP7721 | CMOS electrometer, bias-current cancellation | 17 | not specified | – / 6.5 / – | 10 | 165 MΩ | 20 fA / 900 fA | 150 |
| LMC6001A | CMOS electrometer | 1.3 | not specified | – / 22 / – | 0.13 | 974 GΩ | 25 fA / 2 pA | n/a |
| LMC662 | CMOS, general purpose | 1.4 | not specified | – / 22 / – | 0.2 | 412 GΩ | n/a / n/a | 3e+03 |
| ADA4625-1 | JFET | 18 | 19.9 | 5.5 / 3.3 / – | 4.5 | 813 MΩ | 75 pA / 987 pA | 80 |
| OPA828 | JFET | 45 | 15 | 7.5 / 4 / – | 1.2 | 11.4 GΩ | 8 pA / 400 pA | 300 |
| OPA827 | JFET | 22 | 18 | – / 4 / – | 2.2 | 3.4 GΩ | 10 pA / 500 pA | 150 |
| OPA140 | JFET, rail-to-rail output | 11 | 17 | 8 / 5.1 / – | 0.8 | 25.7 GΩ | 10 pA / 306 pA | 120 |
| OPA145 | JFET | 5.5 | 9.3 | 9 / 7 / – | 0.8 | 25.7 GΩ | 10 pA / 600 pA | 150 |
| OPA1656 | CMOS, low noise | 53 | 11 | – / 4.3 / – | 6 | 457 MΩ | 20 pA / 1.28 nA | 1e+03 |
| OPA2156 | CMOS, low noise | 25 | 11 | – / 4 / – | 19 | 45.6 MΩ | 40 pA / 1.5 nA | 200 |
| OPA320 | CMOS, rail-to-rail | 20 | 9 | – / 8.5 / – | 0.6 | 45.7 GΩ | 900 fA / 50 pA | 150 |
| OPA381 | CMOS, auto-zero, transimpedance-oriented | 18 | 3.5 | – / – / 26.5 | 20 | 41.2 MΩ | 50 pA / 3.2 nA | 25 |
| OPA388 | CMOS, zero drift | 10 | 6.5 | 7 / 7 / – | 100 | 1.65 MΩ | 350 pA / 400 pA | 5 |
| OPA656 | JFET, wideband | 230 | 3 | – / – / 6 | 5 | 659 MΩ | 20 pA / 5 nA | 1.8e+03 |
| OPA657 | JFET, wideband, decompensated | 1.6e+03 | 5.2 | 38.7 / 6.24 / 4.86 | 1.3 | 9.74 GΩ | 20 pA / 5 nA | 1.8e+03 |
| OPA818 | FET, wideband, decompensated | 2.7e+03 | 2.4 | – / 8.4 / 2.25 | 3 | 1.83 GΩ | 25 pA / 700 pA | 1.25e+03 |
| ADA4817-1 | FET, wideband | 410 | 1.4 | – / 11.8 / 4.24 | 2.5 | 2.63 GΩ | 20 pA / 1.28 nA | 2e+03 |
| LTC6268-10 | CMOS, wideband, decompensated | 4e+03 | 0.55 | 281 / 28.4 / 5.1 | 7 | 336 MΩ | 20 fA / 900 fA | 700 |
| OPA858 | CMOS, wideband, decompensated | 5.5e+03 | 0.82 | – / 25.2 / 3.57 | 0.51 | 63.3 GΩ | 5 pA / 320 pA | 5e+03 |
| OPA211 | bipolar, low noise | 45 | 10 | 2 / 1.1 / – | 1.7e+03 | 5.7 kΩ | 175 nA / 190 nA | 125 |
| OPA855 | bipolar, wideband, decompensated | 8e+03 | 0.8 | – / 2.85 / 1.03 | 3.52e+04 | 13.3 Ω | 18.5 µA / 23.3 µA | 1.5e+03 |
| OPA955 | bipolar, wideband, decompensated; preproduction | 1.1e+04 | 1.1 | – / 1.56 / 0.793 | 717 | 32 kΩ | 5 µA / 9.8 µA | 1.5e+03 |
| LMH6629 | bipolar, wideband, decompensated | 4e+03 | 5.7 | – / 0.89 / 0.69 | 6.4e+03 | 402 Ω | 23 µA / 37 µA | 780 |
| IF3601 composite | discrete JFET + op amp (assumed composite GBW 50 MHz) | 50 | 710 | – / – / – | 5.66 | 514 MΩ | 100 pA / 6.4 nA | n/a |
| LSK170 composite | discrete JFET + op amp (assumed composite GBW 50 MHz) | 50 | 25 | 1.4 / 0.9 / – | 12.7 | 103 MΩ | 500 pA / 32 nA | n/a |
| BF862 composite | discrete JFET + op amp (assumed composite GBW 50 MHz) | 50 | 11.9 | – / – / 0.8 | 17.9 | 51.4 MΩ | 1 nA / 64 nA | n/a |



## Designs (f_-3dB [R = resistor-limited]; excess over R_F + diode floor in [1 Hz, f_-3dB]; DC output error at 85 C)

**S1336-18BK (Si 1.1 mm)**

| Part | 10 kΩ | 100 kΩ | 1 MΩ | 10 MΩ | 100 MΩ | 1 GΩ |
|---|---|---|---|---|---|---|
| ADA4530-1 | 888 kHz; 6.8 dB; 40 µV | 322 kHz; 5.0 dB; 40 µV | 109 kHz; 4.5 dB; 40 µV | 35.3 kHz; 4.3 dB; 40 µV | 11.3 kHz; 4.3 dB; 44 µV | 2.03 kHz R; 1.7 dB; 80 µV |
| OPA928 | 997 kHz; 7.9 dB; 25 µV | 362 kHz; 6.1 dB; 25 µV | 121 kHz; 5.7 dB; 25 µV | 38.3 kHz; 5.4 dB; 25 µV | 12.2 kHz; 5.2 dB; 28 µV | 1.96 kHz R; 1.5 dB; 58 µV |
| LMP7721 | 2.94 MHz; 7.0 dB; 1.5e+02 µV | 997 kHz; 6.3 dB; 1.5e+02 µV | 326 kHz; 6.2 dB; 1.5e+02 µV | 104 kHz; 6.2 dB; 1.6e+02 µV | 21 kHz R; 4.4 dB; 2.5e+02 µV | 1.65 kHz R; 7.1 dB; 1.1 mV |
| LMC6001A | 698 kHz; 9.3 dB; n/a | 256 kHz; 6.7 dB; n/a | 86.7 kHz; 5.9 dB; n/a | 28.4 kHz; 5.7 dB; n/a | 9.07 kHz; 5.6 dB; n/a | 2.2 kHz R; 3.1 dB; n/a |
| LMC662 | 730 kHz; 9.4 dB; n/a | 268 kHz; 6.9 dB; n/a | 89.8 kHz; 6.1 dB; n/a | 29.4 kHz; 6.0 dB; n/a | 9.39 kHz; 5.8 dB; n/a | 2.17 kHz R; 3.1 dB; n/a |
| ADA4625-1 | 2.62 MHz; 3.9 dB; 90 µV | 878 kHz; 3.6 dB; 1.8e+02 µV | 284 kHz; 3.5 dB; 1.1 mV | 90.8 kHz; 3.5 dB; 9.9 mV | 22 kHz R; 2.5 dB; 99 mV | 1.67 kHz R; 2.7 dB; 9.9e+02 mV |
| OPA828 | 4.51 MHz; 7.3 dB; 3e+02 µV | 1.49 MHz; 7.0 dB; 3.4e+02 µV | 472 kHz; 6.8 dB; 7e+02 µV | 151 kHz; 6.8 dB; 4.3 mV | 18.3 kHz R; 1.9 dB; 40 mV | 1.61 kHz R; 0.4 dB; 4e+02 mV |
| OPA827 | 2.98 MHz; 5.1 dB; 1.6e+02 µV | 997 kHz; 4.7 dB; 2e+02 µV | 319 kHz; 4.5 dB; 6.5e+02 µV | 102 kHz; 4.5 dB; 5.2 mV | 21 kHz R; 2.5 dB; 50 mV | 1.65 kHz R; 0.9 dB; 5e+02 mV |
| OPA140 | 2.08 MHz; 5.0 dB; 1.2e+02 µV | 706 kHz; 4.4 dB; 1.5e+02 µV | 226 kHz; 4.2 dB; 4.3e+02 µV | 72.1 kHz; 4.1 dB; 3.2 mV | 22.5 kHz R; 3.9 dB; 31 mV | 1.69 kHz R; 0.3 dB; 3.1e+02 mV |
| OPA145 | 1.56 MHz; 4.7 dB; 1.6e+02 µV | 541 kHz; 3.7 dB; 2.1e+02 µV | 179 kHz; 3.5 dB; 7.5e+02 µV | 58 kHz; 3.5 dB; 6.2 mV | 18.3 kHz; 3.3 dB; 60 mV | 1.75 kHz R; 0.4 dB; 6e+02 mV |
| OPA1656 | 4.51 MHz; 4.9 dB; 1 mV | 1.94 MHz; 5.9 dB; 1.1 mV | 651 kHz; 6.0 dB; 2.3 mV | 183 kHz; 5.2 dB; 14 mV | 17.7 kHz R; 1.5 dB; 1.3e+02 mV | 1.61 kHz R; 4.0 dB; 1.3 V |
| OPA2156 | 3.42 MHz; 3.6 dB; 2.2e+02 µV | 1.26 MHz; 3.6 dB; 3.5e+02 µV | 388 kHz; 3.4 dB; 1.7 mV | 121 kHz; 3.6 dB; 15 mV | 19.9 kHz R; 5.3 dB; 1.5e+02 mV | 1.63 kHz R; 11.9 dB; 1.5 V |
| OPA320 | 3.19 MHz; 8.2 dB; 1.5e+02 µV | 1.07 MHz; 7.5 dB; 1.6e+02 µV | 345 kHz; 7.3 dB; 2e+02 µV | 110 kHz; 7.3 dB; 6.5e+02 µV | 20.3 kHz R; 3.8 dB; 5.2 mV | 1.63 kHz R; 0.4 dB; 50 mV |
| OPA381 | 3.3 MHz; 10.1 dB; 57 µV | 1.13 MHz; 10.1 dB; 3.5e+02 µV | 362 kHz; 13.6 dB; 3.2 mV | 116 kHz; 17.6 dB; 32 mV | 20.1 kHz R; 18.4 dB; 3.2e+02 mV | 1.63 kHz R; 13.3 dB; 3.2 V |
| OPA388 | 2.26 MHz; 5.9 dB; 9 µV | 774 kHz; 5.1 dB; 45 µV | 256 kHz; 5.7 dB; 4.1e+02 µV | 81.9 kHz; 9.6 dB; 4 mV | 22.5 kHz R; 17.8 dB; 40 mV | 1.67 kHz R; 26.1 dB; 4e+02 mV |
| OPA656 | 12.7 MHz; 15.0 dB; 1.9 mV | 4.11 MHz; 14.8 dB; 2.3 mV | 1.31 MHz; 14.8 dB; 6.8 mV | 179 kHz R; 8.0 dB; 52 mV | 15.6 kHz R; 1.9 dB; 5e+02 mV | 1.54 kHz R; 3.1 dB; 5 V |
| OPA657 | 33.1 MHz; 21.6 dB; 1.9 mV | 10.6 MHz; 21.6 dB; 2.3 mV | 1.86 MHz R; 16.5 dB; 6.8 mV | 151 kHz R; 6.0 dB; 52 mV | 14.9 kHz R; 1.2 dB; 5e+02 mV | 1.49 kHz R; 0.4 dB; 5 V |
| OPA818 | 46.2 MHz; 16.6 dB; 1.3 mV | 14.6 MHz; 16.5 dB; 1.3 mV | 1.84 MHz R; 9.5 dB; 2 mV | 162 kHz R; 2.3 dB; 8.3 mV | 16 kHz R; 0.6 dB; 71 mV | 1.59 kHz R; 0.5 dB; 7e+02 mV |
| ADA4817-1 | 18 MHz; 13.8 dB; 2 mV | 5.81 MHz; 13.6 dB; 2.1 mV | 1.81 MHz; 13.5 dB; 3.3 mV | 152 kHz R; 4.3 dB; 15 mV | 14.4 kHz R; 1.1 dB; 1.3e+02 mV | 1.42 kHz R; 1.3 dB; 1.3 V |
| LTC6268-10 | 57.5 MHz; 23.3 dB; 7e+02 µV | 18.4 MHz; 23.1 dB; 7e+02 µV | 1.75 MHz R; 13.0 dB; 7e+02 µV | 162 kHz R; 5.4 dB; 7.1e+02 µV | 16 kHz R; 3.5 dB; 8.2e+02 µV | 1.59 kHz R; 1.8 dB; 2 mV |
| OPA858 | 66.8 MHz; 20.4 dB; 5 mV | 21.6 MHz R; 20.6 dB; 5 mV |  |  |  |  |
| OPA211 | 4.83 MHz; 4.8 dB; 2 mV | 1.6 MHz; 12.7 dB; 19 mV | 511 kHz; 22.5 dB; 1.9e+02 mV | 163 kHz; 32.4 dB; 1.9 V | 17.9 kHz R; 42.3 dB; 19 V | 1.61 kHz R; 51.6 dB; 1.9e+02 V |
| OPA855 | 82.1 MHz; 14.9 dB; 2.3e+02 mV | 21.6 MHz R; 18.0 dB; 2.3 V |  |  |  |  |
| OPA955 | 94.3 MHz; 13.9 dB; 1e+02 mV | 20.6 MHz R; 11.5 dB; 9.8e+02 mV |  |  |  |  |
| LMH6629 | 51.8 MHz; 11.0 dB; 3.7e+02 mV | 16.6 MHz; 16.8 dB; 3.7 V |  |  |  |  |
| IF3601 composite | 1.12 MHz; 2.3 dB; n/a | 358 kHz; 2.3 dB; n/a | 113 kHz; 2.2 dB; n/a | 35.7 kHz; 2.3 dB; n/a | 11.3 kHz; 2.6 dB; n/a | 2.01 kHz R; 3.9 dB; n/a |
| LSK170 composite | 4.3 MHz; 1.2 dB; n/a | 1.39 MHz; 1.1 dB; n/a | 445 kHz; 1.1 dB; n/a | 141 kHz; 1.4 dB; n/a | 18.7 kHz R; 3.0 dB; n/a | 1.63 kHz R; 8.7 dB; n/a |
| BF862 composite | 5 MHz; 0.7 dB; n/a | 1.64 MHz; 0.7 dB; n/a | 523 kHz; 0.7 dB; n/a | 165 kHz; 1.3 dB; n/a | 17.9 kHz R; 4.6 dB; n/a | 1.61 kHz R; 11.5 dB; n/a |

**G12180-010A (InGaAs 1 mm)**

| Part | 10 kΩ | 100 kΩ | 1 MΩ | 10 MΩ | 100 MΩ | 1 GΩ |
|---|---|---|---|---|---|---|
| ADA4530-1 | 636 kHz; 8.7 dB; 40 µV | 226 kHz; 7.3 dB; 40 µV | 73.8 kHz; 6.8 dB; 40 µV | 23.6 kHz; 6.5 dB; 43 µV | 7.55 kHz; 5.1 dB; 74 µV | 2.25 kHz R; 1.6 dB; 3.8e+02 µV |
| OPA928 | 722 kHz; 10.0 dB; 25 µV | 250 kHz; 8.6 dB; 25 µV | 81.9 kHz; 8.1 dB; 25 µV | 26.2 kHz; 7.7 dB; 27 µV | 8.37 kHz; 6.0 dB; 47 µV | 2.23 kHz R; 1.5 dB; 2.4e+02 µV |
| LMP7721 | 2.06 MHz; 9.6 dB; 1.5e+02 µV | 682 kHz; 9.1 dB; 1.5e+02 µV | 218 kHz; 8.9 dB; 1.5e+02 µV | 69.7 kHz; 8.7 dB; 1.7e+02 µV | 22 kHz; 7.1 dB; 3.6e+02 µV | 1.69 kHz R; 2.4 dB; 2.2 mV |
| LMC6001A | 499 kHz; 11.1 dB; n/a | 179 kHz; 9.2 dB; n/a | 60 kHz; 8.7 dB; n/a | 19.4 kHz; 8.3 dB; n/a | 6.13 kHz; 6.4 dB; n/a | 1.94 kHz; 2.2 dB; n/a |
| LMC662 | 523 kHz; 11.3 dB; n/a | 185 kHz; 9.4 dB; n/a | 62.1 kHz; 8.9 dB; n/a | 19.9 kHz; 8.4 dB; n/a | 6.28 kHz; 6.5 dB; n/a | 2.01 kHz; 2.3 dB; n/a |
| ADA4625-1 | 1.97 MHz; 5.5 dB; 90 µV | 644 kHz; 5.1 dB; 1.8e+02 µV | 206 kHz; 5.0 dB; 1.1 mV | 65.8 kHz; 4.8 dB; 10 mV | 20.8 kHz; 3.6 dB; 99 mV | 1.71 kHz R; 0.6 dB; 9.9e+02 mV |
| OPA828 | 3.26 MHz; 9.7 dB; 3e+02 µV | 1.07 MHz; 9.4 dB; 3.4e+02 µV | 342 kHz; 9.3 dB; 7e+02 µV | 108 kHz; 9.0 dB; 4.3 mV | 20.6 kHz R; 4.0 dB; 41 mV | 1.65 kHz R; 0.1 dB; 4e+02 mV |
| OPA827 | 2.21 MHz; 7.0 dB; 1.6e+02 µV | 722 kHz; 6.6 dB; 2e+02 µV | 234 kHz; 6.5 dB; 6.5e+02 µV | 73.8 kHz; 6.3 dB; 5.2 mV | 22.5 kHz R; 4.5 dB; 50 mV | 1.69 kHz R; 0.2 dB; 5e+02 mV |
| OPA140 | 1.53 MHz; 6.8 dB; 1.2e+02 µV | 511 kHz; 6.3 dB; 1.5e+02 µV | 165 kHz; 6.1 dB; 4.3e+02 µV | 52.2 kHz; 5.8 dB; 3.2 mV | 16.5 kHz; 4.3 dB; 31 mV | 1.79 kHz R; 0.2 dB; 3.1e+02 mV |
| OPA145 | 1.12 MHz; 6.7 dB; 1.6e+02 µV | 379 kHz; 5.9 dB; 2.1e+02 µV | 124 kHz; 5.7 dB; 7.5e+02 µV | 39.2 kHz; 5.3 dB; 6.2 mV | 12.5 kHz; 3.9 dB; 60 mV | 1.94 kHz R; 0.3 dB; 6e+02 mV |
| OPA1656 | 3.5 MHz; 7.6 dB; 1 mV | 1.42 MHz; 8.8 dB; 1.1 mV | 425 kHz; 8.1 dB; 2.3 mV | 125 kHz; 7.4 dB; 14 mV | 19.9 kHz R; 2.5 dB; 1.3e+02 mV | 1.63 kHz R; 1.0 dB; 1.3 V |
| OPA2156 | 2.53 MHz; 5.7 dB; 2.2e+02 µV | 858 kHz; 5.5 dB; 3.5e+02 µV | 265 kHz; 5.2 dB; 1.7 mV | 82.8 kHz; 5.1 dB; 15 mV | 22.5 kHz R; 5.0 dB; 1.5e+02 mV | 1.67 kHz R; 5.4 dB; 1.5 V |
| OPA320 | 2.23 MHz; 10.8 dB; 1.5e+02 µV | 739 kHz; 10.4 dB; 1.6e+02 µV | 236 kHz; 10.2 dB; 2e+02 µV | 75.5 kHz; 9.9 dB; 6.6e+02 µV | 22.5 kHz R; 7.6 dB; 5.3 mV | 1.69 kHz R; 0.3 dB; 51 mV |
| OPA381 | 2.18 MHz; 13.2 dB; 57 µV | 730 kHz; 15.0 dB; 3.5e+02 µV | 234 kHz; 18.8 dB; 3.2 mV | 73.8 kHz; 22.6 dB; 32 mV | 22.5 kHz R; 24.2 dB; 3.2e+02 mV | 1.69 kHz R; 9.1 dB; 3.2 V |
| OPA388 | 1.56 MHz; 8.3 dB; 9 µV | 529 kHz; 7.7 dB; 45 µV | 171 kHz; 7.9 dB; 4.1e+02 µV | 54.7 kHz; 10.4 dB; 4 mV | 17.3 kHz; 15.7 dB; 40 mV | 1.77 kHz R; 18.4 dB; 4e+02 mV |
| OPA656 | 8.3 MHz; 18.8 dB; 1.9 mV | 2.65 MHz; 18.7 dB; 2.3 mV | 848 kHz; 18.6 dB; 6.8 mV | 196 kHz R; 15.7 dB; 52 mV | 15.1 kHz R; 3.7 dB; 5e+02 mV | 1.45 kHz R; 0.8 dB; 5 V |
| OPA657 | 21.8 MHz; 25.3 dB; 1.9 mV | 6.98 MHz; 25.3 dB; 2.3 mV | 1.88 MHz R; 23.9 dB; 6.8 mV | 141 kHz R; 11.5 dB; 52 mV | 13.4 kHz R; 2.5 dB; 5e+02 mV | 1.34 kHz R; 0.2 dB; 5 V |
| OPA818 | 29.1 MHz; 20.3 dB; 1.3 mV | 9.21 MHz; 20.3 dB; 1.3 mV | 2.16 MHz R; 17.7 dB; 2 mV | 163 kHz R; 6.6 dB; 8.4 mV | 15.8 kHz R; 1.6 dB; 72 mV | 1.58 kHz R; 0.3 dB; 7.1e+02 mV |
| ADA4817-1 | 11.3 MHz; 17.7 dB; 2 mV | 3.58 MHz; 17.4 dB; 2.1 mV | 1.16 MHz; 17.6 dB; 3.3 mV | 137 kHz R; 9.7 dB; 15 mV | 12.2 kHz R; 2.4 dB; 1.3e+02 mV | 1.22 kHz R; 0.5 dB; 1.3 V |
| LTC6268-10 | 35.8 MHz; 27.2 dB; 7e+02 µV | 11.3 MHz; 27.2 dB; 7e+02 µV | 2.01 MHz R; 22.0 dB; 7.1e+02 µV | 163 kHz R; 12.2 dB; 7.7e+02 µV | 16 kHz R; 7.7 dB; 1.4 mV | 1.59 kHz R; 2.0 dB; 7.2 mV |
| OPA858 | 42.1 MHz; 24.6 dB; 5 mV | 13.3 MHz; 24.6 dB; 5 mV |  |  |  |  |
| OPA211 | 3.38 MHz; 5.2 dB; 2 mV | 1.11 MHz; 12.8 dB; 19 mV | 349 kHz; 22.5 dB; 1.9e+02 mV | 110 kHz; 32.1 dB; 1.9 V | 20.3 kHz R; 40.0 dB; 19 V | 1.63 kHz R; 43.8 dB; 1.9e+02 V |
| OPA855 | 50.6 MHz; 18.5 dB; 2.3e+02 mV | 16.2 MHz; 20.6 dB; 2.3 V |  |  |  |  |
| OPA955 | 58.8 MHz; 17.8 dB; 1e+02 mV | 18.8 MHz; 18.0 dB; 9.8e+02 mV |  |  |  |  |
| LMH6629 | 34.6 MHz; 13.6 dB; 3.7e+02 mV | 10.9 MHz; 17.7 dB; 3.7 V |  |  |  |  |
| IF3601 composite | 1.07 MHz; 2.3 dB; n/a | 342 kHz; 2.3 dB; n/a | 109 kHz; 2.3 dB; n/a | 34.5 kHz; 2.2 dB; n/a | 11 kHz; 1.8 dB; n/a | 2.03 kHz R; 0.9 dB; n/a |
| LSK170 composite | 3.23 MHz; 1.8 dB; n/a | 1.06 MHz; 1.8 dB; n/a | 334 kHz; 1.7 dB; n/a | 107 kHz; 1.9 dB; n/a | 20.8 kHz R; 2.2 dB; n/a | 1.65 kHz R; 3.2 dB; n/a |
| BF862 composite | 3.54 MHz; 1.3 dB; n/a | 1.14 MHz; 1.2 dB; n/a | 366 kHz; 1.3 dB; n/a | 116 kHz; 1.7 dB; n/a | 20.1 kHz R; 3.3 dB; n/a | 1.63 kHz R; 5.0 dB; n/a |

**S1336-8BK (Si 5.8 mm)**

| Part | 10 kΩ | 100 kΩ | 1 MΩ | 10 MΩ | 100 MΩ | 1 GΩ |
|---|---|---|---|---|---|---|
| ADA4530-1 | 284 kHz; 14.6 dB; 40 µV | 95.1 kHz; 14.0 dB; 40 µV | 30.8 kHz; 13.8 dB; 40 µV | 9.61 kHz; 13.7 dB; 41 µV | 3.04 kHz; 13.5 dB; 52 µV | 960 Hz; 10.8 dB; 1.6e+02 µV |
| OPA928 | 319 kHz; 16.0 dB; 25 µV | 105 kHz; 15.4 dB; 25 µV | 34.1 kHz; 15.3 dB; 25 µV | 10.9 kHz; 15.2 dB; 26 µV | 3.45 kHz; 14.3 dB; 33 µV | 1.09 kHz; 10.3 dB; 1.1e+02 µV |
| LMP7721 | 878 kHz; 16.6 dB; 1.5e+02 µV | 278 kHz; 16.2 dB; 1.5e+02 µV | 88.7 kHz; 16.2 dB; 1.5e+02 µV | 28 kHz; 16.1 dB; 1.6e+02 µV | 9.07 kHz; 15.5 dB; 2.8e+02 µV | 2.17 kHz R; 9.9 dB; 1.4 mV |
| LMC6001A | 223 kHz; 16.8 dB; n/a | 75.5 kHz; 16.0 dB; n/a | 24.7 kHz; 15.8 dB; n/a | 7.81 kHz; 15.6 dB; n/a | 2.5 kHz; 14.8 dB; n/a | 789 Hz; 10.6 dB; n/a |
| LMC662 | 234 kHz; 17.1 dB; n/a | 79.1 kHz; 16.4 dB; n/a | 25.6 kHz; 16.1 dB; n/a | 8.18 kHz; 16.0 dB; n/a | 2.58 kHz; 15.1 dB; n/a | 817 Hz; 10.9 dB; n/a |
| ADA4625-1 | 878 kHz; 11.2 dB; 90 µV | 284 kHz; 11.1 dB; 1.8e+02 µV | 90.8 kHz; 11.0 dB; 1.1 mV | 28.7 kHz; 10.9 dB; 10 mV | 9.07 kHz; 10.1 dB; 99 mV | 2.2 kHz R; 5.2 dB; 9.9e+02 mV |
| OPA828 | 1.41 MHz; 16.4 dB; 3e+02 µV | 455 kHz; 16.4 dB; 3.4e+02 µV | 144 kHz; 16.3 dB; 7e+02 µV | 45.5 kHz; 16.2 dB; 4.3 mV | 14.4 kHz; 15.3 dB; 40 mV | 1.85 kHz R; 4.8 dB; 4e+02 mV |
| OPA827 | 974 kHz; 13.1 dB; 1.6e+02 µV | 315 kHz; 13.0 dB; 2e+02 µV | 99.6 kHz; 12.9 dB; 6.5e+02 µV | 31.8 kHz; 12.8 dB; 5.2 mV | 10.1 kHz; 12.1 dB; 50 mV | 2.13 kHz R; 5.6 dB; 5e+02 mV |
| OPA140 | 682 kHz; 12.8 dB; 1.2e+02 µV | 223 kHz; 12.6 dB; 1.5e+02 µV | 71.3 kHz; 12.5 dB; 4.3e+02 µV | 22.5 kHz; 12.4 dB; 3.2 mV | 7.12 kHz; 11.6 dB; 31 mV | 2.25 kHz R; 7.6 dB; 3.1e+02 mV |
| OPA145 | 482 kHz; 12.7 dB; 1.6e+02 µV | 160 kHz; 12.4 dB; 2.1e+02 µV | 50.5 kHz; 12.2 dB; 7.5e+02 µV | 16 kHz; 12.0 dB; 6.2 mV | 5.04 kHz; 11.2 dB; 60 mV | 1.63 kHz; 7.4 dB; 6e+02 mV |
| OPA1656 | 1.79 MHz; 15.7 dB; 1 mV | 573 kHz; 15.5 dB; 1.1 mV | 165 kHz; 14.7 dB; 2.3 mV | 50.5 kHz; 14.3 dB; 14 mV | 15.8 kHz; 13.5 dB; 1.3e+02 mV | 1.81 kHz R; 5.7 dB; 1.3 V |
| OPA2156 | 1.13 MHz; 12.3 dB; 2.2e+02 µV | 349 kHz; 11.8 dB; 3.5e+02 µV | 110 kHz; 11.6 dB; 1.7 mV | 34.5 kHz; 11.5 dB; 15 mV | 10.9 kHz; 11.5 dB; 1.5e+02 mV | 2.05 kHz R; 9.8 dB; 1.5 V |
| OPA320 | 952 kHz; 17.9 dB; 1.5e+02 µV | 301 kHz; 17.6 dB; 1.6e+02 µV | 96.2 kHz; 17.5 dB; 2e+02 µV | 30.4 kHz; 17.4 dB; 6.5e+02 µV | 9.61 kHz; 16.8 dB; 5.2 mV | 2.15 kHz R; 10.7 dB; 51 mV |
| OPA381 | 899 kHz; 22.2 dB; 57 µV | 291 kHz; 26.2 dB; 3.5e+02 µV | 91.9 kHz; 30.2 dB; 3.2 mV | 29.4 kHz; 34.3 dB; 32 mV | 9.28 kHz; 36.0 dB; 3.2e+02 mV | 2.17 kHz R; 29.0 dB; 3.2 V |
| OPA388 | 666 kHz; 15.0 dB; 9 µV | 213 kHz; 14.7 dB; 45 µV | 68.1 kHz; 14.7 dB; 4.1e+02 µV | 21.5 kHz; 15.3 dB; 4 mV | 6.88 kHz; 18.6 dB; 40 mV | 2.17 kHz; 22.6 dB; 4e+02 mV |
| OPA656 | 3.3 MHz; 26.8 dB; 1.9 mV | 1.04 MHz; 26.7 dB; 2.3 mV | 334 kHz; 26.8 dB; 6.8 mV | 104 kHz; 26.5 dB; 52 mV | 10.5 kHz R; 15.9 dB; 5e+02 mV | 960 Hz R; 4.1 dB; 5 V |
| OPA657 | 8.79 MHz; 33.3 dB; 1.9 mV | 2.75 MHz; 33.2 dB; 2.3 mV | 878 kHz; 33.3 dB; 6.8 mV | 78.2 kHz R; 22.3 dB; 52 mV | 7.29 kHz R; 11.8 dB; 5e+02 mV | 720 Hz R; 3.1 dB; 5 V |
| OPA818 | 11.2 MHz; 28.3 dB; 1.3 mV | 3.58 MHz; 28.3 dB; 1.3 mV | 1.14 MHz; 28.4 dB; 2 mV | 177 kHz R; 22.6 dB; 8.3 mV | 14.9 kHz R; 13.9 dB; 72 mV | 1.47 kHz R; 8.0 dB; 7e+02 mV |
| ADA4817-1 | 4.4 MHz; 25.7 dB; 2 mV | 1.41 MHz; 25.7 dB; 2.1 mV | 445 kHz; 25.8 dB; 3.3 mV | 59.3 kHz R; 19.2 dB; 15 mV | 5.16 kHz R; 12.0 dB; 1.3e+02 mV | 509 Hz R; 8.0 dB; 1.3 V |
| LTC6268-10 | 13.8 MHz; 35.5 dB; 7e+02 µV | 4.35 MHz; 35.3 dB; 7e+02 µV | 1.39 MHz; 35.4 dB; 7e+02 µV | 183 kHz R; 29.5 dB; 7.3e+02 µV | 16 kHz R; 25.1 dB; 9.6e+02 µV | 1.58 kHz R; 18.3 dB; 3.4 mV |
| OPA858 | 16.2 MHz; 32.8 dB; 5 mV | 5.12 MHz; 33.0 dB; 5 mV |  |  |  |  |
| OPA211 | 1.44 MHz; 7.8 dB; 2 mV | 455 kHz; 13.4 dB; 19 mV | 144 kHz; 22.5 dB; 1.9e+02 mV | 45.5 kHz; 32.4 dB; 1.9 V | 14.5 kHz; 41.6 dB; 19 V | 1.83 kHz R; 47.8 dB; 1.9e+02 V |
| OPA855 | 19.7 MHz; 26.5 dB; 2.3e+02 mV | 6.15 MHz; 26.9 dB; 2.3 V |  |  |  |  |
| OPA955 | 22.9 MHz; 26.0 dB; 1e+02 mV | 7.31 MHz; 26.1 dB; 9.8e+02 mV |  |  |  |  |
| LMH6629 | 13.8 MHz; 20.6 dB; 3.7e+02 mV | 4.4 MHz; 21.8 dB; 3.7 V |  |  |  |  |
| IF3601 composite | 909 kHz; 3.0 dB; n/a | 291 kHz; 3.0 dB; n/a | 91.9 kHz; 3.0 dB; n/a | 29 kHz; 3.0 dB; n/a | 9.18 kHz; 2.9 dB; n/a | 2.17 kHz R; 2.3 dB; n/a |
| LSK170 composite | 1.47 MHz; 5.4 dB; n/a | 472 kHz; 5.4 dB; n/a | 151 kHz; 5.4 dB; n/a | 47.6 kHz; 5.4 dB; n/a | 15.1 kHz; 5.7 dB; n/a | 1.83 kHz R; 5.9 dB; n/a |
| BF862 composite | 1.51 MHz; 4.7 dB; n/a | 482 kHz; 4.6 dB; n/a | 152 kHz; 4.6 dB; n/a | 48.2 kHz; 4.7 dB; n/a | 15.2 kHz; 6.0 dB; n/a | 1.81 kHz R; 8.2 dB; n/a |

**G12180-050A (InGaAs 5 mm)**

| Part | 10 kΩ | 100 kΩ | 1 MΩ | 10 MΩ | 100 MΩ | 1 GΩ |
|---|---|---|---|---|---|---|
| ADA4530-1 | 179 kHz; 18.2 dB; 40 µV | 59.3 kHz; 17.8 dB; 41 µV | 19 kHz; 17.2 dB; 46 µV | 5.99 kHz; 14.2 dB; 1e+02 µV | 1.89 kHz; 7.5 dB; 6.6e+02 µV | 606 Hz; 2.8 dB; 6.2 mV |
| OPA928 | 203 kHz; 19.8 dB; 25 µV | 65.8 kHz; 19.3 dB; 25 µV | 21 kHz; 18.6 dB; 29 µV | 6.65 kHz; 15.2 dB; 64 µV | 2.15 kHz; 7.9 dB; 4.1e+02 µV | 680 Hz; 2.1 dB; 3.9 mV |
| LMP7721 | 548 kHz; 20.5 dB; 1.5e+02 µV | 175 kHz; 20.3 dB; 1.5e+02 µV | 56 kHz; 19.8 dB; 1.7e+02 µV | 17.7 kHz; 16.4 dB; 3.9e+02 µV | 5.53 kHz; 8.7 dB; 2.5 mV | 1.75 kHz; 2.4 dB; 24 mV |
| LMC6001A | 144 kHz; 20.4 dB; n/a | 47.1 kHz; 19.8 dB; n/a | 15.2 kHz; 19.2 dB; n/a | 4.81 kHz; 15.7 dB; n/a | 1.54 kHz; 8.3 dB; n/a | 487 Hz; 2.1 dB; n/a |
| LMC662 | 151 kHz; 20.8 dB; n/a | 49.3 kHz; 20.2 dB; n/a | 15.8 kHz; 19.5 dB; n/a | 5.04 kHz; 16.1 dB; n/a | 1.61 kHz; 8.6 dB; n/a | 504 Hz; 2.2 dB; n/a |
| ADA4625-1 | 560 kHz; 15.0 dB; 90 µV | 179 kHz; 14.8 dB; 1.8e+02 µV | 56.6 kHz; 14.2 dB; 1.1 mV | 17.9 kHz; 11.0 dB; 10 mV | 5.66 kHz; 4.4 dB; 1e+02 mV | 1.79 kHz; 0.8 dB; 1e+03 mV |
| OPA828 | 899 kHz; 20.5 dB; 3e+02 µV | 284 kHz; 20.3 dB; 3.4e+02 µV | 90.8 kHz; 19.8 dB; 7.5e+02 µV | 28.7 kHz; 16.4 dB; 4.8 mV | 9.07 kHz; 8.8 dB; 45 mV | 2.17 kHz R; 1.5 dB; 4.5e+02 mV |
| OPA827 | 622 kHz; 17.0 dB; 1.6e+02 µV | 199 kHz; 16.9 dB; 2e+02 µV | 62.8 kHz; 16.3 dB; 6.7e+02 µV | 19.9 kHz; 12.9 dB; 5.4 mV | 6.28 kHz; 6.0 dB; 52 mV | 2.01 kHz; 1.3 dB; 5.2e+02 mV |
| OPA140 | 435 kHz; 16.6 dB; 1.2e+02 µV | 141 kHz; 16.5 dB; 1.5e+02 µV | 44.5 kHz; 15.8 dB; 4.4e+02 µV | 14.1 kHz; 12.5 dB; 3.4 mV | 4.44 kHz; 5.6 dB; 33 mV | 1.42 kHz; 1.1 dB; 3.2e+02 mV |
| OPA145 | 304 kHz; 16.4 dB; 1.6e+02 µV | 99.6 kHz; 16.2 dB; 2.1e+02 µV | 31.5 kHz; 15.5 dB; 7.7e+02 µV | 9.95 kHz; 12.2 dB; 6.4 mV | 3.14 kHz; 5.3 dB; 62 mV | 1.01 kHz; 1.0 dB; 6.2e+02 mV |
| OPA1656 | 1.17 MHz; 20.0 dB; 1 mV | 342 kHz; 19.1 dB; 1.1 mV | 102 kHz; 18.0 dB; 2.4 mV | 31.5 kHz; 14.5 dB; 15 mV | 9.83 kHz; 7.5 dB; 1.4e+02 mV | 2.13 kHz R; 1.5 dB; 1.4 V |
| OPA2156 | 714 kHz; 16.1 dB; 2.2e+02 µV | 218 kHz; 15.6 dB; 3.5e+02 µV | 67.3 kHz; 14.8 dB; 1.7 mV | 21.3 kHz; 11.6 dB; 16 mV | 6.72 kHz; 5.6 dB; 1.5e+02 mV | 2.15 kHz; 1.8 dB; 1.5 V |
| OPA320 | 594 kHz; 21.8 dB; 1.5e+02 µV | 190 kHz; 21.6 dB; 1.6e+02 µV | 60.7 kHz; 21.1 dB; 2.2e+02 µV | 19.2 kHz; 17.7 dB; 8.8e+02 µV | 6.06 kHz; 10.5 dB; 7.5 mV | 1.89 kHz; 3.6 dB; 73 mV |
| OPA381 | 567 kHz; 28.0 dB; 57 µV | 179 kHz; 31.9 dB; 3.5e+02 µV | 56.6 kHz; 35.5 dB; 3.2 mV | 18.1 kHz; 36.0 dB; 32 mV | 5.79 kHz; 29.1 dB; 3.2e+02 mV | 1.81 kHz; 19.3 dB; 3.2 V |
| OPA388 | 415 kHz; 18.9 dB; 9 µV | 134 kHz; 18.7 dB; 45 µV | 43 kHz; 18.2 dB; 4.1e+02 µV | 13.6 kHz; 15.1 dB; 4 mV | 4.29 kHz; 9.6 dB; 40 mV | 1.34 kHz; 7.3 dB; 4e+02 mV |
| OPA656 | 2.04 MHz; 30.9 dB; 1.9 mV | 651 kHz; 30.9 dB; 2.3 mV | 203 kHz; 30.2 dB; 7.1 mV | 65 kHz; 26.9 dB; 55 mV | 6.35 kHz R; 9.1 dB; 5.3e+02 mV | 599 Hz R; 0.3 dB; 5.3 V |
| OPA657 | 5.36 MHz; 37.3 dB; 1.9 mV | 1.71 MHz; 37.3 dB; 2.3 mV | 541 kHz R; 36.8 dB; 7.1 mV | 40.6 kHz R; 21.0 dB; 55 mV | 3.87 kHz R; 5.3 dB; 5.3e+02 mV | 400 Hz R; 0.3 dB; 5.3 V |
| OPA818 | 7.06 MHz; 32.6 dB; 1.3 mV | 2.23 MHz; 32.5 dB; 1.3 mV | 698 kHz; 31.9 dB; 2.1 mV | 177 kHz R; 27.0 dB; 10 mV | 13.3 kHz R; 10.6 dB; 90 mV | 1.3 kHz R; 2.4 dB; 8.9e+02 mV |
| ADA4817-1 | 2.72 MHz; 29.8 dB; 2 mV | 868 kHz; 29.9 dB; 2.2 mV | 274 kHz; 29.5 dB; 3.6 mV | 26.5 kHz R; 17.5 dB; 18 mV | 2.47 kHz R; 6.1 dB; 1.6e+02 mV | 261 Hz R; 1.9 dB; 1.6 V |
| LTC6268-10 | 8.49 MHz; 39.6 dB; 7e+02 µV | 2.68 MHz; 39.4 dB; 7.1e+02 µV | 858 kHz; 39.1 dB; 8.1e+02 µV | 213 kHz R; 35.0 dB; 1.8 mV | 16 kHz R; 22.3 dB; 12 mV | 1.54 kHz R; 10.4 dB; 1.1e+02 mV |
| OPA858 | 9.98 MHz; 37.1 dB; 5 mV | 3.19 MHz; 37.3 dB; 5.1 mV |  |  |  |  |
| OPA211 | 899 kHz; 10.5 dB; 2 mV | 284 kHz; 14.2 dB; 19 mV | 90.8 kHz; 22.1 dB; 1.9e+02 mV | 28.7 kHz; 28.5 dB; 1.9 V | 9.07 kHz; 30.5 dB; 19 V | 2.1 kHz R; 31.3 dB; 1.9e+02 V |
| OPA855 | 12.1 MHz; 30.7 dB; 2.3e+02 mV | 3.84 MHz; 30.8 dB; 2.3 V |  |  |  |  |
| OPA955 | 14.1 MHz; 30.2 dB; 1e+02 mV | 4.51 MHz; 30.2 dB; 9.8e+02 mV |  |  |  |  |
| LMH6629 | 8.59 MHz; 24.6 dB; 3.7e+02 mV | 2.68 MHz; 25.0 dB; 3.7 V |  |  |  |  |
| IF3601 composite | 730 kHz; 4.1 dB; n/a | 228 kHz; 4.0 dB; n/a | 73 kHz; 3.7 dB; n/a | 23.3 kHz; 2.1 dB; n/a | 7.37 kHz; 0.4 dB; n/a | 2.23 kHz R; 0.1 dB; n/a |
| LSK170 composite | 930 kHz; 8.6 dB; n/a | 297 kHz; 8.5 dB; n/a | 94 kHz; 8.0 dB; n/a | 29.7 kHz; 5.3 dB; n/a | 9.39 kHz; 1.5 dB; n/a | 2.13 kHz R; 0.3 dB; n/a |
| BF862 composite | 952 kHz; 7.8 dB; n/a | 297 kHz; 7.5 dB; n/a | 94 kHz; 7.0 dB; n/a | 30.4 kHz; 4.8 dB; n/a | 9.61 kHz; 1.5 dB; n/a | 2.13 kHz R; 0.6 dB; n/a |

**G12183-010K (InGaAs to 2.6 um, 1 mm)**

| Part | 10 kΩ | 100 kΩ | 1 MΩ | 10 MΩ | 100 MΩ | 1 GΩ |
|---|---|---|---|---|---|---|
| ADA4530-1 | 253 kHz; 13.6 dB; 69 µV | 83.8 kHz; 7.6 dB; 3.3e+02 µV | 27.1 kHz; 3.8 dB; 2.9 mV | 3.14 kHz R; 4.4 dB; 29 mV | 280 Hz R; 9.2 dB; 2.9e+02 mV | 28 Hz R; 14.8 dB; 2.9 V |
| OPA928 | 281 kHz; 14.9 dB; 43 µV | 92.9 kHz; 8.7 dB; 2e+02 µV | 30.1 kHz; 4.1 dB; 1.8 mV | 4 kHz R; 3.1 dB; 18 mV | 352 Hz R; 3.7 dB; 1.8e+02 mV | 35.6 Hz R; 4.7 dB; 1.8 V |
| LMP7721 | 765 kHz; 15.4 dB; 2.6e+02 µV | 247 kHz; 9.0 dB; 1.2 mV | 78.2 kHz; 2.9 dB; 11 mV | 25 kHz; 1.0 dB; 1.1e+02 mV | 2.3 kHz R; 0.9 dB; 1.1 V | 252 Hz R; 1.5 dB; 11 V |
| LMC6001A | 199 kHz; 15.8 dB; n/a | 67.3 kHz; 9.8 dB; n/a | 21.8 kHz; 5.8 dB; n/a | 1.96 kHz R; 4.9 dB; n/a | 183 Hz R; 4.9 dB; n/a | 19.3 Hz R; 4.9 dB; n/a |
| LMC662 | 208 kHz; 16.1 dB; n/a | 69.7 kHz; 10.0 dB; n/a | 22.5 kHz; 5.8 dB; n/a | 2.13 kHz R; 4.9 dB; n/a | 198 Hz R; 4.9 dB; n/a | 20.3 Hz R; 4.9 dB; n/a |
| ADA4625-1 | 774 kHz; 10.1 dB; 1.5e+02 µV | 250 kHz; 4.7 dB; 7.5e+02 µV | 79.1 kHz; 1.0 dB; 6.8 mV | 25.3 kHz; 0.3 dB; 67 mV | 2.38 kHz R; 0.2 dB; 6.7e+02 mV | 222 Hz R; 0.3 dB; 6.7 V |
| OPA828 | 1.24 MHz; 15.3 dB; 5.2e+02 µV | 401 kHz; 9.0 dB; 2.5 mV | 127 kHz; 2.6 dB; 22 mV | 40.1 kHz; 0.6 dB; 2.2e+02 mV | 5.28 kHz R; 0.3 dB; 2.2 V | 470 Hz R; 0.4 dB; 22 V |
| OPA827 | 868 kHz; 12.1 dB; 2.6e+02 µV | 278 kHz; 6.1 dB; 1.3 mV | 88.7 kHz; 1.5 dB; 11 mV | 28 kHz; 0.4 dB; 1.1e+02 mV | 2.9 kHz R; 0.3 dB; 1.1 V | 270 Hz R; 0.3 dB; 11 V |
| OPA140 | 601 kHz; 11.7 dB; 2.1e+02 µV | 194 kHz; 5.8 dB; 1 mV | 62.8 kHz; 1.5 dB; 9 mV | 19.9 kHz R; 0.6 dB; 89 mV | 1.5 kHz R; 0.5 dB; 8.9e+02 mV | 147 Hz R; 0.7 dB; 8.9 V |
| OPA145 | 425 kHz; 11.6 dB; 2.6e+02 µV | 139 kHz; 5.8 dB; 1.3 mV | 44.5 kHz; 1.8 dB; 11 mV | 9.95 kHz R; 0.9 dB; 1.1e+02 mV | 762 Hz R; 0.9 dB; 1.1 V | 77.9 Hz R; 1.1 dB; 11 V |
| OPA1656 | 1.62 MHz; 14.8 dB; 1.7 mV | 488 kHz; 8.0 dB; 8.3 mV | 142 kHz; 1.9 dB; 74 mV | 44 kHz; 0.4 dB; 7.3e+02 mV | 5.99 kHz R; 0.5 dB; 7.3 V | 515 Hz R; 2.1 dB; 73 V |
| OPA2156 | 997 kHz; 11.2 dB; 3.6e+02 µV | 308 kHz; 5.2 dB; 1.8 mV | 96.2 kHz; 1.1 dB; 16 mV | 30.1 kHz; 0.3 dB; 1.6e+02 mV | 3.22 kHz R; 0.7 dB; 1.6 V | 293 Hz R; 3.3 dB; 16 V |
| OPA320 | 829 kHz; 16.7 dB; 2.6e+02 µV | 265 kHz; 10.1 dB; 1.2 mV | 84.8 kHz; 3.5 dB; 11 mV | 27.1 kHz; 1.3 dB; 1.1e+02 mV | 2.65 kHz R; 1.2 dB; 1.1 V | 247 Hz R; 1.7 dB; 11 V |
| OPA381 | 792 kHz; 21.6 dB; 75 µV | 253 kHz; 19.0 dB; 5.2e+02 µV | 80.9 kHz; 15.0 dB; 5 mV | 25.9 kHz; 13.7 dB; 50 mV | 2.38 kHz R; 13.5 dB; 5e+02 mV | 222 Hz R; 13.5 dB; 5 V |
| OPA388 | 587 kHz; 13.9 dB; 13 µV | 190 kHz; 7.7 dB; 81 µV | 60 kHz; 2.4 dB; 7.6e+02 µV | 18.3 kHz R; 1.0 dB; 7.6 mV | 1.37 kHz R; 0.9 dB; 76 mV | 131 Hz R; 0.9 dB; 7.6e+02 mV |
| OPA656 | 2.84 MHz; 25.5 dB; 3.1 mV | 909 kHz; 18.8 dB; 15 mV | 291 kHz; 9.9 dB; 1.4e+02 mV | 98.4 kHz; 3.3 dB; 1.3 V | 17.5 kHz R; 0.7 dB; 13 V | 9.95 kHz R; 0.7 dB; 1.3e+02 V |
| OPA657 | 7.57 MHz; 32.0 dB; 3.1 mV | 2.42 MHz; 25.3 dB; 15 mV | 774 kHz; 16.1 dB; 1.4e+02 mV | 80 kHz R; 1.9 dB; 1.3 V | 20.1 kHz R; 0.7 dB; 13 V | 14.4 kHz R; 0.7 dB; 1.3e+02 V |
| OPA818 | 9.98 MHz; 27.3 dB; 2.1 mV | 3.15 MHz; 20.5 dB; 10 mV | 985 kHz; 11.3 dB; 91 mV | 175 kHz R; 1.7 dB; 9e+02 mV | 16.5 kHz R; 0.8 dB; 9 V | 3.87 kHz R; 2.1 dB; 90 V |
| ADA4817-1 | 3.88 MHz; 24.6 dB; 3.4 mV | 1.23 MHz; 17.9 dB; 16 mV | 397 kHz; 9.2 dB; 1.5e+02 mV | 65 kHz R; 1.7 dB; 1.4 V | 20.8 kHz R; 2.0 dB; 14 V | 16.9 kHz R; 2.2 dB; 1.4e+02 V |
| LTC6268-10 | 12 MHz; 34.3 dB; 1.2 mV | 3.84 MHz; 27.5 dB; 5.7 mV | 1.23 MHz; 18.1 dB; 51 mV | 185 kHz R; 5.6 dB; 5e+02 mV | 16 kHz R; 5.4 dB; 5 V | 1.96 kHz R; 11.6 dB; 50 V |
| OPA858 | 14.1 MHz; 31.7 dB; 8.6 mV | 4.51 MHz; 25.2 dB; 41 mV |  |  |  |  |
| OPA211 | 1.26 MHz; 6.5 dB; 2.1 mV | 401 kHz; 5.7 dB; 20 mV | 128 kHz; 5.4 dB; 2e+02 mV | 40.6 kHz; 5.4 dB; 2 V | 5.4 kHz R; 5.6 dB; 20 V | 565 Hz R; 6.9 dB; 2e+02 V |
| OPA855 | 17.1 MHz; 25.4 dB; 2.4e+02 mV | 5.42 MHz; 19.0 dB; 2.3 V |  |  |  |  |
| OPA955 | 20.1 MHz; 25.0 dB; 1e+02 mV | 6.37 MHz; 18.2 dB; 9.9e+02 mV |  |  |  |  |
| LMH6629 | 12 MHz; 19.3 dB; 3.7e+02 mV | 3.79 MHz; 13.7 dB; 3.7 V |  |  |  |  |
| IF3601 composite | 868 kHz; 2.2 dB; n/a | 271 kHz; 0.5 dB; n/a | 87.7 kHz; 0.1 dB; n/a | 27.4 kHz; 0.0 dB; n/a | 6.72 kHz R; 0.0 dB; n/a | 540 Hz R; 0.0 dB; n/a |
| LSK170 composite | 1.3 MHz; 4.6 dB; n/a | 415 kHz; 1.4 dB; n/a | 133 kHz; 0.2 dB; n/a | 42 kHz; 0.0 dB; n/a | 5.79 kHz R; 0.0 dB; n/a | 534 Hz R; 0.0 dB; n/a |
| BF862 composite | 1.31 MHz; 3.9 dB; n/a | 425 kHz; 1.2 dB; n/a | 134 kHz; 0.2 dB; n/a | 42.5 kHz; 0.0 dB; n/a | 5.79 kHz R; 0.0 dB; n/a | 534 Hz R; 0.0 dB; n/a |



## Dominant noise terms in band, ADA4625-1

| Photodiode | 10 kΩ | 100 kΩ | 1 MΩ | 10 MΩ | 100 MΩ | 1 GΩ |
|---|---|---|---|---|---|---|
| S1336-18BK (Si 1.1 mm) | $e_n\,\omega C$ 57%, $R_F$ 40%; 2.62 MHz | $e_n\,\omega C$ 56%, $R_F$ 44%; 878 kHz | $e_n\,\omega C$ 55%, $R_F$ 45%; 284 kHz | $e_n\,\omega C$ 54%, $R_F$ 45%; 90.8 kHz | $R_F$ 53%, $e_n\,\omega C$ 38%; 22 kHz R | $i_n$ 44%, $R_F$ 36%; 1.67 kHz R |
| G12180-010A (InGaAs 1 mm) | $e_n\,\omega C$ 70%, $R_F$ 28%; 1.97 MHz | $e_n\,\omega C$ 69%, $R_F$ 31%; 644 kHz | $e_n\,\omega C$ 68%, $R_F$ 31%; 206 kHz | $e_n\,\omega C$ 67%, $R_F$ 30%; 65.8 kHz | $e_n\,\omega C$ 53%, $R_F$ 24%; 20.8 kHz | diode $R_{sh}$ 77%, $i_n$ 12%; 1.71 kHz R |
| S1336-8BK (Si 5.8 mm) | $e_n\,\omega C$ 92%, $R_F$ 8%; 878 kHz | $e_n\,\omega C$ 92%, $R_F$ 8%; 284 kHz | $e_n\,\omega C$ 92%, $R_F$ 8%; 90.8 kHz | $e_n\,\omega C$ 92%, $R_F$ 8%; 28.7 kHz | $e_n\,\omega C$ 89%, $R_F$ 8%; 9.07 kHz | $e_n\,\omega C$ 59%, diode $R_{sh}$ 22%; 2.2 kHz R |
| G12180-050A (InGaAs 5 mm) | $e_n\,\omega C$ 97%, $R_F$ 3%; 560 kHz | $e_n\,\omega C$ 97%, $R_F$ 3%; 179 kHz | $e_n\,\omega C$ 96%, $R_F$ 3%; 56.6 kHz | $e_n\,\omega C$ 92%, diode $R_{sh}$ 5%; 17.9 kHz | $e_n\,\omega C$ 64%, diode $R_{sh}$ 34%; 5.66 kHz | diode $R_{sh}$ 83%, $e_n\,\omega C$ 16%; 1.79 kHz |
| G12183-010K (InGaAs to 2.6 um, 1 mm) | $e_n\,\omega C$ 89%, $R_F$ 6%; 774 kHz | $e_n\,\omega C$ 64%, diode $R_{sh}$ 30%; 250 kHz | diode $R_{sh}$ 79%, $e_n\,\omega C$ 16%; 79.1 kHz | diode $R_{sh}$ 93%, $e_n/(R_F\parallel R_{sh})$ 4%; 25.3 kHz | diode $R_{sh}$ 95%, $e_n/(R_F\parallel R_{sh})$ 5%; 2.38 kHz R | diode $R_{sh}$ 94%, $e_n/(R_F\parallel R_{sh})$ 6%; 222 Hz R |



## Dominant noise terms in band, ADA4530-1

| Photodiode | 10 kΩ | 100 kΩ | 1 MΩ | 10 MΩ | 100 MΩ | 1 GΩ |
|---|---|---|---|---|---|---|
| S1336-18BK (Si 1.1 mm) | $e_n\,\omega C$ 55%, $e_n/(R_F\parallel R_{sh})$ 25%; 888 kHz | $e_n\,\omega C$ 64%, $R_F$ 32%; 322 kHz | $e_n\,\omega C$ 64%, $R_F$ 36%; 109 kHz | $e_n\,\omega C$ 63%, $R_F$ 37%; 35.3 kHz | $e_n\,\omega C$ 63%, $R_F$ 36%; 11.3 kHz | $R_F$ 45%, $e_n\,\omega C$ 32%; 2.03 kHz R |
| G12180-010A (InGaAs 1 mm) | $e_n\,\omega C$ 71%, $e_n/(R_F\parallel R_{sh})$ 16%; 636 kHz | $e_n\,\omega C$ 79%, $R_F$ 19%; 226 kHz | $e_n\,\omega C$ 79%, $R_F$ 21%; 73.8 kHz | $e_n\,\omega C$ 77%, $R_F$ 21%; 23.6 kHz | $e_n\,\omega C$ 69%, $R_F$ 17%; 7.55 kHz | diode $R_{sh}$ 61%, $e_n\,\omega C$ 31%; 2.25 kHz R |
| S1336-8BK (Si 5.8 mm) | $e_n\,\omega C$ 92%, $e_n/(R_F\parallel R_{sh})$ 4%; 284 kHz | $e_n\,\omega C$ 96%, $R_F$ 4%; 95.1 kHz | $e_n\,\omega C$ 96%, $R_F$ 4%; 30.8 kHz | $e_n\,\omega C$ 96%, $R_F$ 4%; 9.61 kHz | $e_n\,\omega C$ 95%, $R_F$ 4%; 3.04 kHz | $e_n\,\omega C$ 92%, diode $R_{sh}$ 6%; 960 Hz |
| G12180-050A (InGaAs 5 mm) | $e_n\,\omega C$ 97%, $e_n/(R_F\parallel R_{sh})$ 2%; 179 kHz | $e_n\,\omega C$ 98%, $R_F$ 2%; 59.3 kHz | $e_n\,\omega C$ 98%, $R_F$ 2%; 19 kHz | $e_n\,\omega C$ 96%, diode $R_{sh}$ 2%; 5.99 kHz | $e_n\,\omega C$ 82%, diode $R_{sh}$ 17%; 1.89 kHz | diode $R_{sh}$ 52%, $e_n\,\omega C$ 48%; 606 Hz |
| G12183-010K (InGaAs to 2.6 um, 1 mm) | $e_n\,\omega C$ 87%, $e_n/(R_F\parallel R_{sh})$ 9%; 253 kHz | $e_n\,\omega C$ 65%, $e_n/(R_F\parallel R_{sh})$ 17%; 83.8 kHz | diode $R_{sh}$ 41%, $e_n/(R_F\parallel R_{sh})$ 41%; 27.1 kHz | $e_n/(R_F\parallel R_{sh})$ 63%, diode $R_{sh}$ 36%; 3.14 kHz R | $e_n/(R_F\parallel R_{sh})$ 88%, diode $R_{sh}$ 12%; 280 Hz R | $e_n/(R_F\parallel R_{sh})$ 97%, diode $R_{sh}$ 3%; 28 Hz R |



## Shortlist at 10 kΩ

| Photodiode | Quietest 4 ($\Delta N$; $f_{-3\,\mathrm{dB}}$) | Fastest ($f_{-3\,\mathrm{dB}}$; $\Delta N$) |
|---|---|---|
| S1336-18BK (Si 1.1 mm) | OPA2156 3.6 dB, 3.42 MHz; ADA4625-1 3.9 dB, 2.62 MHz; OPA145 4.7 dB, 1.56 MHz; OPA211 4.8 dB, 4.83 MHz | OPA955 94.3 MHz, 13.9 dB |
| G12180-010A (InGaAs 1 mm) | OPA211 5.2 dB, 3.38 MHz; ADA4625-1 5.5 dB, 1.97 MHz; OPA2156 5.7 dB, 2.53 MHz; OPA145 6.7 dB, 1.12 MHz | OPA955 58.8 MHz, 17.8 dB |
| S1336-8BK (Si 5.8 mm) | OPA211 7.8 dB, 1.44 MHz; ADA4625-1 11.2 dB, 878 kHz; OPA2156 12.3 dB, 1.13 MHz; OPA145 12.7 dB, 482 kHz | OPA955 22.9 MHz, 26.0 dB |
| G12180-050A (InGaAs 5 mm) | OPA211 10.5 dB, 899 kHz; ADA4625-1 15.0 dB, 560 kHz; OPA2156 16.1 dB, 714 kHz; OPA145 16.4 dB, 304 kHz | OPA855 12.1 MHz, 30.7 dB |
| G12183-010K (InGaAs to 2.6 um, 1 mm) | OPA211 6.5 dB, 1.26 MHz; ADA4625-1 10.1 dB, 774 kHz; OPA2156 11.2 dB, 997 kHz; OPA145 11.6 dB, 425 kHz | OPA955 20.1 MHz, 25.0 dB |



## Shortlist at 100 kΩ

| Photodiode | Quietest 4 ($\Delta N$; $f_{-3\,\mathrm{dB}}$) | Fastest ($f_{-3\,\mathrm{dB}}$; $\Delta N$) |
|---|---|---|
| S1336-18BK (Si 1.1 mm) | ADA4625-1 3.6 dB, 878 kHz; OPA2156 3.6 dB, 1.26 MHz; OPA145 3.7 dB, 541 kHz; OPA140 4.4 dB, 706 kHz | OPA855 21.6 MHz, 18.0 dB |
| G12180-010A (InGaAs 1 mm) | ADA4625-1 5.1 dB, 644 kHz; OPA2156 5.5 dB, 858 kHz; OPA145 5.9 dB, 379 kHz; OPA140 6.3 dB, 511 kHz | OPA955 18.8 MHz, 18.0 dB |
| S1336-8BK (Si 5.8 mm) | ADA4625-1 11.1 dB, 284 kHz; OPA2156 11.8 dB, 349 kHz; OPA145 12.4 dB, 160 kHz; OPA140 12.6 dB, 223 kHz | LTC6268-10 4.35 MHz, 35.3 dB |
| G12180-050A (InGaAs 5 mm) | OPA211 14.2 dB, 284 kHz; ADA4625-1 14.8 dB, 179 kHz; OPA2156 15.6 dB, 218 kHz; OPA145 16.2 dB, 99.6 kHz | LTC6268-10 2.68 MHz, 39.4 dB |
| G12183-010K (InGaAs to 2.6 um, 1 mm) | ADA4625-1 4.7 dB, 250 kHz; OPA2156 5.2 dB, 308 kHz; OPA211 5.7 dB, 401 kHz; OPA145 5.8 dB, 139 kHz | LTC6268-10 3.84 MHz, 27.5 dB |



## Shortlist at 1 MΩ

| Photodiode | Quietest 4 ($\Delta N$; $f_{-3\,\mathrm{dB}}$) | Fastest ($f_{-3\,\mathrm{dB}}$; $\Delta N$) |
|---|---|---|
| S1336-18BK (Si 1.1 mm) | OPA2156 3.4 dB, 388 kHz; ADA4625-1 3.5 dB, 284 kHz; OPA145 3.5 dB, 179 kHz; OPA140 4.2 dB, 226 kHz | OPA657 1.86 MHz, 16.5 dB |
| G12180-010A (InGaAs 1 mm) | ADA4625-1 5.0 dB, 206 kHz; OPA2156 5.2 dB, 265 kHz; OPA145 5.7 dB, 124 kHz; OPA140 6.1 dB, 165 kHz | OPA818 2.16 MHz, 17.7 dB |
| S1336-8BK (Si 5.8 mm) | ADA4625-1 11.0 dB, 90.8 kHz; OPA2156 11.6 dB, 110 kHz; OPA145 12.2 dB, 50.5 kHz; OPA140 12.5 dB, 71.3 kHz | LTC6268-10 1.39 MHz, 35.4 dB |
| G12180-050A (InGaAs 5 mm) | ADA4625-1 14.2 dB, 56.6 kHz; OPA2156 14.8 dB, 67.3 kHz; OPA145 15.5 dB, 31.5 kHz; OPA140 15.8 dB, 44.5 kHz | LTC6268-10 858 kHz, 39.1 dB |
| G12183-010K (InGaAs to 2.6 um, 1 mm) | ADA4625-1 1.0 dB, 79.1 kHz; OPA2156 1.1 dB, 96.2 kHz; OPA827 1.5 dB, 88.7 kHz; OPA140 1.5 dB, 62.8 kHz | LTC6268-10 1.23 MHz, 18.1 dB |



## Shortlist at 10 MΩ

| Photodiode | Quietest 4 ($\Delta N$; $f_{-3\,\mathrm{dB}}$) | Fastest ($f_{-3\,\mathrm{dB}}$; $\Delta N$) |
|---|---|---|
| S1336-18BK (Si 1.1 mm) | OPA818 2.3 dB, 162 kHz; ADA4625-1 3.5 dB, 90.8 kHz; OPA145 3.5 dB, 58 kHz; OPA2156 3.6 dB, 121 kHz | OPA1656 183 kHz, 5.2 dB |
| G12180-010A (InGaAs 1 mm) | ADA4625-1 4.8 dB, 65.8 kHz; OPA2156 5.1 dB, 82.8 kHz; OPA145 5.3 dB, 39.2 kHz; OPA140 5.8 dB, 52.2 kHz | LTC6268-10 163 kHz, 12.2 dB |
| S1336-8BK (Si 5.8 mm) | ADA4625-1 10.9 dB, 28.7 kHz; OPA2156 11.5 dB, 34.5 kHz; OPA145 12.0 dB, 16 kHz; OPA140 12.4 dB, 22.5 kHz | LTC6268-10 183 kHz, 29.5 dB |
| G12180-050A (InGaAs 5 mm) | ADA4625-1 11.0 dB, 17.9 kHz; OPA2156 11.6 dB, 21.3 kHz; OPA145 12.2 dB, 9.95 kHz; OPA140 12.5 dB, 14.1 kHz | LTC6268-10 213 kHz, 35.0 dB |
| G12183-010K (InGaAs to 2.6 um, 1 mm) | ADA4625-1 0.3 dB, 25.3 kHz; OPA2156 0.3 dB, 30.1 kHz; OPA1656 0.4 dB, 44 kHz; OPA827 0.4 dB, 28 kHz | LTC6268-10 185 kHz, 5.6 dB |



## Shortlist at 100 MΩ

| Photodiode | Quietest 4 ($\Delta N$; $f_{-3\,\mathrm{dB}}$) | Fastest ($f_{-3\,\mathrm{dB}}$; $\Delta N$) |
|---|---|---|
| S1336-18BK (Si 1.1 mm) | OPA818 0.6 dB, 16 kHz; OPA657 1.2 dB, 14.9 kHz; OPA1656 1.5 dB, 17.7 kHz; OPA656 1.9 dB, 15.6 kHz | OPA140 22.5 kHz, 3.9 dB |
| G12180-010A (InGaAs 1 mm) | OPA818 1.6 dB, 15.8 kHz; OPA1656 2.5 dB, 19.9 kHz; ADA4625-1 3.6 dB, 20.8 kHz; OPA145 3.9 dB, 12.5 kHz | OPA827 22.5 kHz, 4.5 dB |
| S1336-8BK (Si 5.8 mm) | ADA4625-1 10.1 dB, 9.07 kHz; OPA145 11.2 dB, 5.04 kHz; OPA2156 11.5 dB, 10.9 kHz; OPA140 11.6 dB, 7.12 kHz | LTC6268-10 16 kHz, 25.1 dB |
| G12180-050A (InGaAs 5 mm) | ADA4625-1 4.4 dB, 5.66 kHz; OPA145 5.3 dB, 3.14 kHz; OPA2156 5.6 dB, 6.72 kHz; OPA140 5.6 dB, 4.44 kHz | LTC6268-10 16 kHz, 22.3 dB |
| G12183-010K (InGaAs to 2.6 um, 1 mm) | ADA4625-1 0.2 dB, 2.38 kHz; OPA827 0.3 dB, 2.9 kHz; OPA828 0.3 dB, 5.28 kHz; OPA1656 0.5 dB, 5.99 kHz | LTC6268-10 16 kHz, 5.4 dB |



## Shortlist at 1 GΩ

| Photodiode | Quietest 4 ($\Delta N$; $f_{-3\,\mathrm{dB}}$) | Fastest ($f_{-3\,\mathrm{dB}}$; $\Delta N$) |
|---|---|---|
| S1336-18BK (Si 1.1 mm) | OPA140 0.3 dB, 1.69 kHz; OPA828 0.4 dB, 1.61 kHz; OPA145 0.4 dB, 1.75 kHz; OPA657 0.4 dB, 1.49 kHz | LMC6001A 2.2 kHz, 3.1 dB |
| G12180-010A (InGaAs 1 mm) | OPA828 0.1 dB, 1.65 kHz; OPA140 0.2 dB, 1.79 kHz; OPA827 0.2 dB, 1.69 kHz; OPA818 0.3 dB, 1.58 kHz | ADA4530-1 2.25 kHz, 1.6 dB |
| S1336-8BK (Si 5.8 mm) | OPA828 4.8 dB, 1.85 kHz; ADA4625-1 5.2 dB, 2.2 kHz; OPA827 5.6 dB, 2.13 kHz; OPA1656 5.7 dB, 1.81 kHz | OPA140 2.25 kHz, 7.6 dB |
| G12180-050A (InGaAs 5 mm) | ADA4625-1 0.8 dB, 1.79 kHz; OPA145 1.0 dB, 1.01 kHz; OPA140 1.1 dB, 1.42 kHz; OPA827 1.3 dB, 2.01 kHz | OPA828 2.17 kHz, 1.5 dB |
| G12183-010K (InGaAs to 2.6 um, 1 mm) | ADA4625-1 0.3 dB, 222 Hz; OPA827 0.3 dB, 270 Hz; OPA828 0.4 dB, 470 Hz; OPA140 0.7 dB, 147 Hz | LTC6268-10 1.96 kHz, 11.6 dB |