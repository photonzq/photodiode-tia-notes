r"""Reviewed fixes of the logic round of 1 Nov 2026 for Chapter 6, read by edit_logic_round2.py.

Sections 6.2-6.4 each open with the mechanism behind their ranking before the chart; results that the
macromodels of Chapter 5 have since changed are stated with them; the notes that explain asterisks in
Tables A6.5, A6.6 and A6.13 move under those tables; the SPICE how-to of Section 6.5 moves to
Appendix B.1.
"""

LEAD_62 = r"""Stability is compared first, because it removes most candidates before noise is considered. A 1-pF photodiode on a 2-kΩ feedback resistor gives a high-frequency noise gain of only about 7–12, which is exactly the minimum stable gain of the decompensated amplifiers, and these include most of the parts with sub-nanovolt $e_n$. The loop also crosses over while the noise gain is still rising, and that lead costs 14–30° of phase in the designs of Table A6.11, compared with a resistive stage at the same gain (Eq. (21), Section 4.4). A decompensated part therefore needs enough source capacitance for its GBW (Eq. (20)) and, in addition, enough phase of its own, $\phi_A$, at the crossover; a unity-gain-stable part has no such trap, and its GBW sets its bandwidth through Eq. (18). These phase margins come from the datasheet open-loop curves; the vendors' macromodels give OPA818, OPA955 and AD8099 more phase margin, and OPA858 and LMH6629 less (Sections 5.5, 5.9 and 6.5)."""

GROUPS_621 = r"""- LMH6624, THS4021, AD8099, AD8021 and LTC6268-10 miss Eq. (20): their source capacitance is too small for their GBW and minimum stable gain. For THS4021, $C_{T,\min}$ = 318.3 × 9²/(2 × 2000) = 6.45 pF against the 2.85 pF present.
- OPA846, OPA818, OPA847, OPA657, LT6230-10 and OPA955 meet Eq. (20) (OPA818 needs 2.12 pF and has 3.75 pF, Section 3.2) but have too little phase of their own at the crossover (Eq. (21), Section 6.2.6). OPA955's plotted curve leaves only about 40° at a gain of 7 (Table A6.2), so its flat design has 36°, and a smaller $C_F$ lowers it further (30° at 0.15 pF, Table A6.13).
- ADA4895-1 and LT6200-10 carry 14 and 7.3 pF of input capacitance of their own and reach 45° only with 8 and 1 pF added, at 39 and 99 MHz.
- Unity-gain-stable parts with too little GBW for 150 MHz: ADA4899-1, ADA4817-1, AD8045 and THS4271.
- LTC6228, whose 5 pF of input capacitance and 0.89 GHz GBW give at most 44°.

With 2 pF added, OPA955 is the quietest robust design of all (Section 6.2.6), and in the vendors' macromodels OPA818, OPA955 and AD8099 reach robust designs (Section 6.5)."""

CORNERS_625 = r"""- **OPA955, OPA855 and OPA858 are the most sensitive (Tables A6.9 and A6.10).** Their flat designs rely on the parasitic alone. If an 0201 resistor with small pads gives only 0.1 pF, OPA855 and OPA858 fall to 35–38° with 3.0–3.8 dB of peaking and OPA955 to 17–18° with 8.0–8.7 dB; with 0.3 pF OPA855 and OPA858 give a well-damped 320 MHz at 2 kΩ. These parts are therefore safest with a deliberate total of about 0.25 pF (Section 8.10).
- **OPA818 and OPA846 have no margin to lose.** Their flat designs sit at 28–34°, and 0.1 pF of parasitic takes OPA818 to 24–27° with 2.4–2.8 dB of peaking and OPA846 to 27–33°.
- **The unity-gain-stable parts move by about 30 % in bandwidth and never fall below 49°;** OPA843 ($G_{\min}$ = 3) falls to 45–46° and LMH6629 to 44–46°."""

LEAD_63 = r"""Noise is compared second, and over most of the planned range it decides little. The shot noise of the pair is already 5.66 pA/√Hz at 0.1 mA, 5.9 dB above the 2.87 pA/√Hz of a 2-kΩ resistor, and 17.90 pA/√Hz at 1 mA (Sections 1.1 and 3.2). The amplifier adds a flat part, chiefly the base-current shot noise $i_n$ of a bipolar input, and the term $e_n\omega C_{\mathrm{tot}}$, which rises with frequency and with the total input capacitance (Eq. (23)). Its noise therefore matters only near 0.1 mA and at 150–200 MHz, and the ranking follows $i_n$ and the product $e_nC_{\mathrm{tot}}$, not $e_n$ alone."""

LEAD_64 = r"""Dynamic range is the ratio of the largest undistorted tone, $I_{\max} = V_{\mathrm{pk}}/(\sqrt2\,\lvert Z_T(f_0)\rvert)$, to the band noise (Eq. (31)). The amplifier's dark noise sets the floor only below the photocurrent at which the shot noise of the pair equals it, $I_{\mathrm{DC}}^{\times}$ of Eq. (51): 31–63 µA for the 5-V parts and 0.10–0.15 mA for the noisier OPA818 (Figure 16, Section 6.6.3). Above it the shot noise, the same for every part, sets the floor, and the dynamic range approaches Eq. (33): it falls by 10 dB per decade of photocurrent and rises by 6 dB for every doubling of $V_{\mathrm{pk}}$. The ceiling is the smaller of the swing and the slew-rate amplitude of Eq. (30), which cross at $f_{\times} = \mathrm{SR}/(2\pi V_{\mathrm{sw}})$ (Eq. (52)), so a larger supply helps only for tones below $f_{\times}$."""

NOTE_A65 = r"""\* These values of $C_F$ exceed $C_T/(G_{\min}-1)$, so the high-frequency noise gain falls below the manufacturer's minimum stable gain. Within that rule the largest phase margins are:
- OPA818: 33.8° at 0.625 pF (237 MHz);
- OPA846: 34.5° at 0.858 pF (176 MHz);
- LMH6629 (COMP HI): 57.8° at 0.78 pF (136 MHz).

The model sees these designs as stable only because the curves stop at about 1 GHz (Section 6.2.4). OPA846's entry, 35° at 0.85 pF, already lies within the rule and carries no asterisk."""

NOTE_A66 = r"""\* Above $C_T/(G_{\min}-1)$; see the note to Table A6.5. Within the rule, OPA818 reaches 28.5° and OPA846 28.9°."""

NOTE_A613 = r"""\* OPA855: every flagged combination is a second loop-gain crossing at the plotted 4–7 GHz open-loop bump. It occurs at the upper $C_F$ corner, where $NG_\infty = 1 + C_T/C_F$ falls to 6.6–7.7, around the minimum stable gain of 7, while the margin at the main crossover stays at 55–63°. Table A4.5 shows that the plotted bump overstates the real one, but the vendor's macromodel loses gain margin at the same corners (Section 5.5): by Eq. (47) it has only $20\log_{10}(6.6/5.3)$ = 1.9 dB to $20\log_{10}(7.7/5.3)$ = 3.2 dB there. The flags therefore mark the upper edge of the $C_F$ window at gigahertz frequencies, not a peaking limit."""

B1_POINTS = r"""**Points specific to the further amplifiers of Section 6.5.**
- **PSpice's capacitor model type `CAP`** (THS4021) is ngspice's `C`; the translation renames it.
- **AD8099 and ADA4899-1 stop every `ac` sweep with "matrix is singular"**, while `noise` sweeps of the same circuit run. Some node of these two models has no AC path to ground. `.options rshunt=1e12`, which puts 1 TΩ from every node to ground, cures it and leaves their noise unchanged to the printed digits; it is applied to these two models only (`scripts_archive/spice_diagnostics/adi_open_loop_probe.py`).
- **TI's newer models declare their noiseless resistors as `RES ( TCE=0 T_ABS=-273.15)`** (OPA955, OPA814). The translation must find `T_ABS` anywhere in the card. A translation that misses it leaves these resistors at about 27 K, as described above for the noiseless resistors of the TI models, and OPA955's input noise then comes out at 76–406 nV/√Hz instead of its 0.80 nV/√Hz.
- **The TINA-TI netlists** are extracted unchanged (Table B.1)."""

FIXES = [
    # 6.1.1
    ("span", "Type labels: TYP typical; MIN / MAX guaranteed limit (25 °C unless stated)", "n.s. not specified.",
     "Type labels are those of Section 1.5."),
    # 6.2
    ("replace", "Figure 10 shows the result for every analysed part at both feedback resistors:",
     LEAD_62 + "\n\nFigure 10 shows the result for every analysed part at both feedback resistors:"),
    ("replace", "Nine parts have no robust design at all.",
     "Seven more reach 45° only below 150 MHz, and nine parts have no robust design at all."),
    # 6.2.1
    ("span", "\\* These values of $C_F$ exceed $C_T/(G_{\\min}-1)$", "only because the curves stop at about 1 GHz (Section 6.2.4).",
     "Entries marked with an asterisk in Table A6.5 use a $C_F$ above $C_T/(G_{\\min}-1)$, where the high-frequency noise gain falls below the manufacturer's minimum stable gain; the model finds them stable only because the curves stop at about 1 GHz (Section 6.2.4)."),
    ("replace", "These give 55–69° flat designs at 134–195 MHz, and 150–231 MHz with up to 1 dB of peaking.",
     "These give 49–69° flat designs at 134–195 MHz (OPA843 49°), and 150–231 MHz in their robust designs."),
    ("span", "- Decompensated parts whose GBW is too small for their $G_{\\min}$:",
     "with 2 pF added it is the quietest robust design of all (Section 6.2.6).", GROUPS_621),
    # 6.2.2
    ("delete", "\\* Above $C_T/(G_{\\min}-1)$; see the note to Table A6.5.", "OPA818 reaches 28.5° and OPA846 28.9°."),
    ("replace", "The unity-gain-stable parts gain 15–30 % in bandwidth: OPA856 reaches 263 MHz and OPA859 239 MHz robustly.",
     "The unity-gain-stable parts gain 11–15 % in robust bandwidth and 15–16 % in flat bandwidth (Tables A6.5 and A6.6), close to the $\\sqrt{2/1.5}$ = 1.15 of Eq. (18): OPA856 reaches 263 MHz and OPA859 239 MHz robustly."),
    # 6.2.3
    ("replace", "#### 6.2.3 Calibrated open-loop variants\n\n**What the calibration changes.**",
     "#### 6.2.3 Calibrated open-loop variants\n\nThe calibrated variant of Section 4.5 scales the plotted curve to the table GBW and adds the delay that reproduces the stated phase margin (Table A4.2); Table A6.7 compares the two.\n\n**What the calibration changes.**"),
    ("replace",
     "Since only the calibrated variant comes close to TI's closed-loop table (Table A4.5), the OPA858 entries in the noise and dynamic-range tables, which use the plotted curve, should be read as optimistic.",
     "Only the calibrated variant comes close to TI's closed-loop table (Table A4.5), and the macromodel sides with the table (Section 5.4), so OPA858's bandwidths and phase margins from the plotted curve are optimistic. Its noise and dynamic range at a given $C_F$ depend little on the open-loop curve (Eq. (23)), and SPICE confirms them within 0.2 dB (Section 6.6.2)."),
    # 6.2.4
    ("replace", "A useful design therefore needs a window of total $C_F$ that is wide compared with that tolerance.",
     "A useful design therefore needs a window of total $C_F$ that is wide compared with that tolerance. Table A6.8 gives it for every part that has one."),
    ("replace", "A target of 0.25 pF total sits in the middle: ±0.1 pF of parasitic variation stays inside it",
     "A target of 0.25 pF total sits in the middle: on the datasheet curve ±0.1 pF of parasitic variation stays inside it"),
    ("replace", "a narrower noise bandwidth needs a filter after the TIA.",
     "a narrower noise bandwidth needs a filter after the TIA. The vendor's macromodel narrows the window to 0.157–0.300 pF, because its gain margin at 3–4 GHz falls to 3 dB at $C_F = C_T/6.5$ (Eq. (47)); the total $C_F$ must then be held to 0.230 ± 0.070 pF or trimmed on the first board (Section 5.5)."),
    # 6.2.5
    ("span", "- **OPA855 and OPA858 are the most sensitive.**",
     "- **The unity-gain-stable parts move by 30 % in bandwidth but never fall below 49°.**", CORNERS_625),
    # 6.2.6
    ("replace", "why OPA818, OPA846 and OPA847 fail, and what added capacitance buys",
     "why OPA818, OPA846 and OPA847 fail on their datasheet curves, and what added capacitance buys"),
    ("replace", "The phase margin saturates at 34°, with $|NG(f_c)|$ already at or below the minimum stable gain of 7.",
     "The phase margin saturates at 34°, with $|NG(f_c)|$ already at or below the minimum stable gain of 7. In its macromodel, which reproduces the datasheet's measured closed loop at a gain of 7, OPA818 keeps 39–45° at the worst capacitance corner (Sections 5.4–5.5)."),
    ("replace", "for the two short-listed parts and for OPA955 and OPA855 for comparison",
     "for OPA818 and OPA846 and, for comparison, OPA955 and OPA855"),
    ("replace",
     "- **The OPA818 and OPA846 designs that reach 45° lose more than 6 dB of noise and drop below 160 MHz.** These are the 5–8 pF cases.",
     "- **The OPA818 and OPA846 designs that reach 45° need 5–8 pF, lose 3.7–8.3 dB of band noise and drop below 160 MHz.** OPA818 loses 6.1–8.3 dB and OPA846 3.7–5.4 dB against their flat designs (Tables A6.12 and A6.15)."),
    # 6.2.7
    ("replace", "#### 6.2.7 Transimpedance responses and the bandwidth–noise trade\n\n![Figure 11]",
     "#### 6.2.7 Transimpedance responses and the bandwidth–noise trade\n\nFigure 11 shows why a flat response does not prove a stable loop: OPA818 and OPA846 are flat at 32–34° of phase margin, because the roll-off of $Z_F$ hides the loop's peaking (Section 5.2). In Figure 12 a part reaches the wide, quiet corner only if its own loop supplies the phase margin, as OPA855's does; added input capacitance costs $e_n\\omega C$ noise (Section 6.2.6).\n\n![Figure 11]"),
    # 6.2.8
    ("span", "\\* OPA855: every flagged combination is a second loop-gain crossing", "rather than a peaking limit.",
     "Table A6.13 flags OPA855's combinations at the upper $C_F$ corner; the note to the table explains them."),
    # 6.3
    ("replace", "All noise numbers in this section use Eq. (23) for the design named in each table",
     LEAD_63 + "\n\nAll noise numbers in this section use Eq. (23) for the design named in each table"),
    ("replace",
     "- The tables show ten amplifiers, those with a usable design at ≥ 150 MHz plus the two short-listed parts; Figure 13 adds every other part with a stable flat design.",
     "- The tables show ten amplifiers: the nine parts with a robust design at ≥ 150 MHz in Figure 10 (LMH6629 with the COMP pin high only) and OPA846, which was on the starting list (Section 2.2). Figure 13 adds every other part with a stable flat design."),
    ("replace", "Over 10–150 MHz that integrates to 33.9 nA rms, and over 10–200 MHz to 39.6 nA rms.",
     "Over 10–150 MHz that integrates to 33.9 nA rms, and over 10–200 MHz to 39.6 nA rms.\n- Band noise in Sections 6.2–6.3 is integrated over 10–150 MHz (Eq. (25)), and the dynamic ranges of Sections 6.4–6.8 over 0–150 MHz (Eqs. (31) and (49)); the lowest 10 MHz raise the Johnson noise of 2 kΩ from 33.9 to 35.1 nA rms and the shot noise of 0.1 mA from 67.0 to 69.3 nA rms."),
    ("replace",
     "In the dark a TIA is therefore more sensitive than the plain termination by the difference: 17.1 dB for OPA955, 14.9 dB for OPA855 and 0.9 dB for OPA657, the noisiest part.",
     "In the dark a TIA is therefore more sensitive than the plain termination by the difference of the two penalties over 10–150 MHz: 17.1 dB for OPA955, 14.9 dB for OPA855 and 0.9 dB for OPA657, the noisiest part. With the macromodels' band noise over 0–150 MHz, the measure $A$ of Section 6.8, OPA955 and OPA855 lead by 17.2 and 15.0 dB (Table A6.35)."),
    # 6.3.3
    ("replace", " For OPA855 at 2 kΩ, dark, 4.17 pA/√Hz and 1.996 kΩ give −154.6 dBm/Hz.", " Section 3.2 works it for OPA855."),
    ("replace", "**The last column matters for a broadband instrument.**",
     "**The last column of Table A6.22 matters for a broadband instrument.**"),
    ("replace",
     "A first-order or second-order filter at 200–250 MHz after the TIA removes this excess and costs nothing in band. The dynamic ranges of Section 6.4 assume such a filter.",
     "A filter after the TIA removes most of this excess and costs nothing in signal-to-noise ratio in band. The dynamic ranges of Sections 6.4–6.8 assume an ideal noise band of 150 MHz; a second-order Butterworth filter at 200 MHz has a noise bandwidth of $1.11\\times200$ = 222 MHz and leaves $10\\log_{10}(222/150)$ = 1.7 dB more shot noise at high photocurrent, against 6.2 dB without a filter."),
    # 6.3.4
    ("replace", "**The regime picture of Section 9.1, in numbers.**",
     "**The regime of Section 1.1, in numbers (Tables A6.23 and A6.24).**"),
    # 6.4
    ("replace", "Figure 15 shows the electronic dynamic range (Eq. (31)) in 150 MHz for a 100-MHz tone of the ten amplifiers",
     LEAD_64 + "\n\nFigure 15 shows the electronic dynamic range (Eq. (31)) in 150 MHz for a 100-MHz tone of the ten amplifiers"),
    ("replace", "From 0.1 mA up the order follows the output amplitude instead:",
     "From 0.1 mA up the order follows the ceiling $I_{\\max}$ instead:"),
    ("replace",
     "The dashed lines mark the 50-Ω benchmark compressing at −10 dBm. In this electronic measure it leads every amplifier from 0.1 mA up, by 1.8 dB (OPA818) to 12.4 dB (OPA856) at 0.1 mA and by 7.3 to 19.0 dB at 1 mA, but most of the tones that lead assumes are larger than the light can supply, which Section 6.8 accounts for.",
     "The dashed lines mark the 50-Ω benchmark compressing at −10 dBm, which Section 6.8 sets against these designs."),
    # 6.4.2
    ("replace",
     "gives Table A6.26. The current limit includes a 100-Ω load (50-Ω back-termination plus 50-Ω instrument) and never binds for these parts.",
     "gives Table A6.26. This is the amplitude at which the output clips or slews, not a distortion limit (Section 6.4.4). At 100 and 150 MHz the current limit, with a 100-Ω load (50-Ω back-termination plus 50-Ω instrument), never binds for these parts."),
    ("replace", "provided the peaking is equalized (Section 6.2.8) or OPA818 works in a second stage (Section 8.5).",
     "provided the peaking is equalized (Section 6.2.8), which its macromodel shows to be unnecessary at $C_F$ = 0.55–0.65 pF (Section 5.5), or OPA818 works in a second stage (Section 8.5)."),
    ("replace",
     "- **Into a back-terminated 50-Ω load** OPA818 becomes current-limited at about 5.2 V at 20 MHz (55 mA into the 95 Ω of the load in parallel with $R_F$), 0.4 dB below the light-load value. The 5-V parts lose about 0.1 V of swing (Section 6.4.2).",
     "- **Into a back-terminated 50-Ω load**, Eq. (30) with OPA818's 55 mA of linear output current allows about 5.2 V at 20 MHz (55 mA into the 95 Ω of the load in parallel with $R_F$), 0.4 dB below the light-load value. A sustained tone at that level exceeds the 25-mA absolute-maximum continuous output current of Section 6.1.2, since a sine of 55 mA peak carries $55/\\sqrt2$ = 38.9 mA rms. At 100 MHz the slew-limited 2.23 V drives 2.23 V / 95.2 Ω = 23.4 mA peak, 16.6 mA rms, within the rating. The 5-V parts lose about 0.1 V of swing into this load."),
    # 6.4.3
    ("replace",
     "- **At ≥ 1 mA the dynamic range follows Eq. (33).** It depends only on $V_{\\mathrm{pk}}$ and $R_F$. So OPA818 leads by 3.3 dB (2.23 V against 1.52 V), and 1.5 kΩ gains 2.5 dB over 2 kΩ for every part.",
     "- **From 1 mA up the dynamic range approaches Eq. (33), which depends only on the ceiling.** OPA818's 2.23 V against 1.52 V is worth 3.3 dB, reached at 10 mA; at 1 mA its amplifier noise leaves 3.1 dB (Section 6.6.2). The smaller $R_F$ of 1.5 kΩ gains up to $20\\log_{10}(2/1.5)$ = 2.5 dB, but only 2.0–2.1 dB for OPA843 and THS4304 (Table A6.30), whose flat designs are already rolling off at 100 MHz. Eq. (31) credits a smaller $\\lvert Z_T(f_0)\\rvert$ with a larger $I_{\\max}$: OPA843's $\\lvert Z_T\\rvert$ = 1.59 V / 0.91 mA = 1.75 kΩ, 1.2 dB below $R_F$, places it second at 1 and 10 mA in Table A6.29, and, as for LMH6629 in Section 6.6.2, that credit holds only for a tone at 100 MHz."),
    ("replace",
     "- **The back-termination costs 0–0.6 dB.** The 5-V parts lose about 0.1 V of swing into 100 Ω; the slew-limited parts lose nothing.",
     "- **The back-termination costs 0–0.6 dB**, the swing the 5-V parts lose into 100 Ω (Section 6.4.2)."),
    ("replace",
     "which presumes a post-filter (Section 6.3.3). Without one, a broadband digitizer integrates the shot noise over the TIA's own noise bandwidth: about 619 MHz for OPA855, which costs 6.2 dB at high photocurrent.",
     "which presumes a post-filter (Section 6.3.3)."),
    ("replace", "- *Above 26 µA the solid lines fall at 10 dB per decade, because shot noise takes over (Eq. (33)).*",
     "- *Above $I_{\\mathrm{DC}}^{\\times}$ of Eq. (51), where the shot noise equals the dark band noise, the solid lines approach 10 dB per decade (Eq. (33)); for OPA818 in this model $I_{\\mathrm{DC}}^{\\times} = (70.7\\ \\mathrm{nA})^2/(2\\times1.602\\times10^{-19}\\ \\mathrm{C}\\times150\\ \\mathrm{MHz})$ = 0.104 mA. The 25.7 µA of Section 1.1 is the crossover for $R_F$ alone.*"),
    ("paragraph", "Section 6.6.2 recomputes Table A6.29 for the five leading amplifiers from their SPICE macromodels.",
     "Section 6.6 recomputes these numbers from the macromodels and shows, for OPA818, which noise and which large-signal limit set them (Figure 19)."),
    # 6.4.4
    ("replace",
     "- **OPA818's second harmonic** is the weakest of the leading parts (−43 dBc at 2 Vpp into 100 Ω). Its larger swing buys dynamic range against noise, but not linearity at full scale.",
     "- **OPA818's second harmonic is the weakest of the leading parts.** At 100 MHz its datasheet gives −43 dBc at 2 Vpp into 100 Ω and −50 dBc into 1 kΩ, less than half of its 4.46-Vpp ceiling (2.23 V peak), against −65 dBc for OPA855 at 2 Vpp into 200 Ω (Table A6.31). Its larger swing buys dynamic range against noise, not against distortion. Where the receiver sets a distortion limit, each ceiling is the amplitude at which the distortion reaches it, as Section 7.2 does for the high-voltage composite, and OPA818's lead holds only if its distortion at that amplitude is acceptable."),
    ("replace", "- The bipolar parts recover in 2–3 ns.",
     "- OPA855, OPA955 and LMH6629 recover in 2–3 ns, OPA856 in about 1 ns and OPA846 in about 19 ns (Table A6.31)."),
    ("replace", "- OPA858 needs 200 ns, which is long enough to blank several microseconds of signal after a strong optical pulse.",
     "- OPA858 needs 200 ns, 20 periods of a 100-MHz tone, after each overload."),
    # 6.5
    ("span", "**Getting the models to run.** Four points beyond Appendix B.1:", "their datasheets' test circuits in Table A5.5.",
     "Appendix B.1 lists four points these models need beyond the general procedure, and Appendix B.2 says where to obtain the model files (Table B.1), which are not distributed with this note. Our own designs for the further parts are in Tables A5.4, A5.6 and A5.11, and their datasheets' test circuits in Table A5.5."),
    ("replace", "with a window only 0.141 pF wide (Table A5.8)", "with a window only 0.141 pF wide (Table A6.32)"),
    ("replace", "- **The FET-input parts confirm Table A2.4.**", "- **The JFET-input parts confirm Table A2.4.**"),
    ("replace", "OPA818 (2.2 nV/√Hz on 2.4 pF) is the only FET part above 150 MHz.",
     "OPA818 (2.2 nV/√Hz on 2.4 pF) is the only JFET-input part above 150 MHz; the CMOS-input OPA858 and OPA859 reach 446 and 209 MHz (Table A6.32)."),
    # 6.6.2
    ("replace", "Their slew rates would take over only above $\\mathrm{SR}/(2\\pi V_{\\mathrm{sw}})$ = 209 MHz",
     "Their slew rates would take over only above the crossover of Eq. (52) (Section 6.6.3), $\\mathrm{SR}/(2\\pi V_{\\mathrm{sw}})$ = 209 MHz"),
    # 6.7
    ("replace",
     "Two kinds are compared here: the lidar TIAs of Section 2.5, and the TIAs of coherent optical receivers, which are made for a balanced photodiode pair with one photodiode on each of two inputs.",
     "Three kinds are compared here: the lidar TIAs and the coherent-receiver TIAs of Section 2.5, the latter made for a balanced photodiode pair with one photodiode on each of two inputs, and three optical-communication TIAs, which prove not to be linear amplifiers."),
    ("replace", "**LMH32401 at 2 kΩ is the only lidar TIA within reach, and it is 10.5–13.5 dB behind at 1 mA.**",
     "**LMH32401 at 2 kΩ is the only lidar TIA within reach, and it is 10.4–13.5 dB behind at 1 mA.**"),
    ("replace",
     "- **The DC limits of Section 2.5 no longer decide.** For a TIA with one input the pair's DC never reaches that input; only the residual imbalance does, which the servo of Section 8.8 holds near zero. The ambient-light cancellation of the TI parts and the OFFSET inputs of the Maxim parts would carry that residual,",
     "- **The DC is no obstacle in the balanced pair.** The ambient-light cancellation of the TI parts and the OFFSET inputs of the Maxim parts would carry the residual imbalance, which the servo of Section 8.8 holds near zero,"),
    # 6.8
    ("replace", "the OPA859–THS3491 composite at a gain of 5.5 (Table A7.7); their band noise and their ceiling at a 100-MHz tone come from those tables.",
     "the OPA859–THS3491 composite at a gain of 5.5 (Table A7.7); their band noise and their ceiling at a 100-MHz tone come from those tables. The two composites are designed in Chapter 7; they appear here so that every front end meets the benchmark in one place."),
    ("replace", "A 50-Ω amplifier that compresses at −10 dBm therefore has the larger electronic dynamic range from 0.1 mA up.",
     "A 50-Ω amplifier that compresses at −10 dBm therefore has the larger electronic dynamic range from 0.1 mA up. Against the ten amplifiers of Figure 15 its lead is 1.8 dB (OPA818) to 12.4 dB (OPA856) at 0.1 mA and 7.3 to 19.0 dB at 1 mA, but most of the tones it assumes are larger than the light can supply."),
    # conclusions, Table 9.1 (kept from the old Section 9.7)
    ("replace", "Highest dynamic range of all the candidates at every photocurrent, by up to 11 dB for tones at 20–50 MHz (Table A6.28).",
     "Highest dynamic range of all the candidates from about 70 µA up, by up to 11 dB for tones at 20–50 MHz (Table A6.28)."),
    # appendices: the table notes and the SPICE points
    ("replace", "| LT6230-10 | 10.25 | 2.07 / 2.07 | 97 | 28 | 99 / 26 | 31 at 2.82, 48 MHz | none |",
     "| LT6230-10 | 10.25 | 2.07 / 2.07 | 97 | 28 | 99 / 26 | 31 at 2.82, 48 MHz | none |\n\n" + NOTE_A65),
    ("replace", "| LT6230-10 | 10.25 | 2.47 / 2.47 | 116 | 25 | 116 / 24 | 27 at 3.00, 97 MHz | none |",
     "| LT6230-10 | 10.25 | 2.47 / 2.47 | 116 | 25 | 116 / 24 | 27 at 3.00, 97 MHz | none |\n\n" + NOTE_A66),
    ("replace", "| OPA855 | 1.5 | 0.20 | 52 | 0.2 dB at 319 MHz | 746 | flagged* | 29 | 3.3 | 0–5.5 dB, up to 660 MHz | 4.50 | 321 |",
     "| OPA855 | 1.5 | 0.20 | 52 | 0.2 dB at 319 MHz | 746 | flagged* | 29 | 3.3 | 0–5.5 dB, up to 660 MHz | 4.50 | 321 |\n\n" + NOTE_A613),
    ("replace", "\n### B.2 Reproducing the runs\n", "\n" + B1_POINTS + "\n\n### B.2 Reproducing the runs\n"),
]
