*Table A6.39. Larger feedback resistors with 0.1 pF of feedback parasitic (an optimistic layout): the robust design of each amplifier carried forward (the widest bandwidth with a phase margin of at least 45° and at most 1 dB of peaking, as in Table A9.2, but with no capacitance added at the input) on the 1-pF node with 0.35 pF of board capacitance. Each cell gives the −3 dB bandwidth and the phase margin; the band-average input-referred noise over 10 MHz to the lower of 150 MHz and the bandwidth, against the Johnson noise of $R_F$ (central FET model, Section 3.7); and the DC photocurrent of the pair whose shot noise equals that noise. Each open-loop curve as plotted; Section 6.10 gives OPA858 with its calibrated curve (Table A6.7). Amplifiers: the ten carried forward. `medium_gain.py`.*

| Part | 2 kΩ | 3 kΩ | 5 kΩ | 10 kΩ |
|---|---|---|---|---|
| OPA855 | 706 MHz, 49°; 3.1 dB; 53 µA | 571 MHz, 50°; 4.0 dB; 44 µA | 402 MHz, 57°; 5.5 dB; 36 µA | 200 MHz, 70°; 7.8 dB; 31 µA |
| OPA955 | needs added input capacitance | needs added input capacitance | 447 MHz, 46°; 1.8 dB; 16 µA | 232 MHz, 55°; 3.0 dB; 10 µA |
| LMH6629 (COMP HI) | 276 MHz, 45°; 4.6 dB; 74 µA | 223 MHz, 47°; 5.7 dB; 64 µA | 169 MHz, 49°; 7.4 dB; 57 µA | 120 MHz, 49°; 9.1 dB; 42 µA |
| OPA856 | 231 MHz, 47°; 3.2 dB; 54 µA | 192 MHz, 48°; 4.1 dB; 44 µA | 149 MHz, 49°; 5.5 dB; 37 µA | 105 MHz, 51°; 7.4 dB; 28 µA |
| OPA858 | 737 MHz, 48°; 3.8 dB; 62 µA | 592 MHz, 50°; 4.7 dB; 50 µA | 408 MHz, 58°; 6.1 dB; 42 µA | 200 MHz, 71°; 8.5 dB; 36 µA |
| OPA859 | 211 MHz, 53°; 6.0 dB; 102 µA | 174 MHz, 53°; 7.0 dB; 86 µA | 134 MHz, 55°; 7.8 dB; 61 µA | 96 MHz, 56°; 7.7 dB; 30 µA |
| THS4304 | 191 MHz, 56°; 6.1 dB; 105 µA | 157 MHz, 55°; 7.3 dB; 91 µA | 122 MHz, 56°; 7.8 dB; 62 µA | 86 MHz, 56°; 8.5 dB; 36 µA |
| OPA818 | needs added input capacitance | needs added input capacitance | 146 MHz, 45°; 9.0 dB; 82 µA | 136 MHz, 45°; 10.9 dB; 63 µA |
| OPA846 | needs added input capacitance | needs added input capacitance | 116 MHz, 45°; 7.9 dB; 63 µA | 91 MHz, 46°; 9.5 dB; 46 µA |
| OPA843 | 150 MHz, 45°; 7.0 dB; 128 µA | 127 MHz, 45°; 7.3 dB; 92 µA | 97 MHz, 47°; 7.9 dB; 63 µA | 69 MHz, 48°; 9.3 dB; 43 µA |
