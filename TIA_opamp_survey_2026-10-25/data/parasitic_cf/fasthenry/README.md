# FastHenry checks of the inductance estimates

These are the results of `scripts_archive/parasitic_cf/fasthenry_validation.py`, which checks `inductance_estimates.py` (parts B, C and F) with FastHenry2; its docstring explains every model. All values are partial inductances of the stated open path, in nH; the estimate is that of `inductance_estimates.py` for the same piece. "DC" is 1 kHz with one filament per segment (uniform current). At high frequency each segment is cut into filaments across its width and thickness (n_w x n_h, ratio 2); the three levels are a convergence series. Skin depth of copper (rho = 1.7e-8 ohm m): 3.74 um at 308 MHz, 2.32 um at 801 MHz.

## What the runs show

* The formulas are right: a strip 1 um thick with uniform current reproduces Eq. (B3) to 0.13-0.27 %, and cages of 64 strips approach Eq. (B4) to 0.7 % (via) and 0.4 % (PDIP-8 hole). The field models' square barrels match the round tubes to 0.7 % at 308 MHz (they are 11-14 % higher at DC).
* Single pieces lie below the estimates, as the script argues: the 35-um copper traces by 4-8 % at DC and 9-16 % at 308 and 801 MHz, the gull-wing leads of the SOT-23-5 and SOIC-8 by 17-27 %.
* The PDIP-8 lead lies 19-26 % above its estimate. Its filled hole and its shoulder stand in line and carry the current the same way, so their mutual inductance, which the estimate leaves out, adds: 2 x 0.263 nH for collinear filaments (collinear_mutual(), the side note's Eq. (C.1)). FastHenry's excess is smaller, 0.35 nH at DC and 0.25 nH at 308 MHz, because the filaments of conductors this wide meet off their common line, which lowers the mutual term, and the shoulder's thickness lowers its own term.
* The whole paths (leads, vias and traces, without the 2 x 2.35 nH inside the package) lie within -6.3 % to +4.3 % of part (F). Every piece but the vias lies 9-27 % below its estimate at 308 MHz, so the mutual terms that the estimate leaves out add more than they take away. The path crosses from one side of the package to the other instead of going out to the resistor and back: on each side the via stands in line with the lead's riser (the PDIP-8's hole with its shoulder) and carries the current the same way, and the traces of the two sides run the same way; the vertical pieces of the two sides, which carry opposite currents, stand 2.7-8.0 mm apart. inductance_estimates.py calls its sum an estimate on the high side partly because it leaves the mutual terms out; for these layouts that reason does not hold, while its totals do.
* The windowed ground planes lower the SOT-23-5 and SOIC-8 paths by 0.9 % and 0.7 % at 308 MHz.
* Convergence: between the two finest filament levels the traces and the whole paths move by 0.15 % or less and the square barrels and the leads, whose thick cross-sections the filaments resolve last, by up to 0.9 %; between the plane grids of 64 and 96 the paths move by 0.15 % or less.

## segments

| Item | Frequency | Filaments / grid | FastHenry (nH) | Estimate (nH) | Ratio | R (mOhm) | Time (s) |
|---|---|---|---|---|---|---|---|
| strip 0.35 mm, 1 um, uniform | DC | 1 x 1 | 0.1347 | 0.1351 | 0.9973 | 29.750 | 0.2 |
| strip 0.35 mm, 35-um copper | DC | 1 x 1 | 0.1241 | 0.1351 | 0.9189 | 0.850 | 0.2 |
| strip 0.35 mm, 35-um copper | 308 MHz | 5 x 3 | 0.1164 | 0.1351 | 0.8616 | 2.409 | 0.2 |
| strip 0.35 mm, 35-um copper | 308 MHz | 9 x 5 | 0.1147 | 0.1351 | 0.8494 | 4.005 | 0.2 |
| strip 0.35 mm, 35-um copper | 308 MHz | 13 x 7 | 0.1146 | 0.1351 | 0.8486 | 4.138 | 0.2 |
| strip 0.35 mm, 35-um copper | 801 MHz | 5 x 3 | 0.1162 | 0.1351 | 0.8604 | 2.514 | 0.2 |
| strip 0.35 mm, 35-um copper | 801 MHz | 9 x 5 | 0.1140 | 0.1351 | 0.8441 | 5.428 | 0.2 |
| strip 0.35 mm, 35-um copper | 801 MHz | 13 x 7 | 0.1139 | 0.1351 | 0.8430 | 6.469 | 0.2 |
| strip 1 mm, 1 um, uniform | DC | 1 x 1 | 0.5725 | 0.5735 | 0.9982 | 85.000 | 0.2 |
| strip 1 mm, 35-um copper | DC | 1 x 1 | 0.5413 | 0.5735 | 0.9438 | 2.429 | 0.2 |
| strip 1 mm, 35-um copper | 308 MHz | 5 x 3 | 0.5140 | 0.5735 | 0.8963 | 7.427 | 0.5 |
| strip 1 mm, 35-um copper | 308 MHz | 9 x 5 | 0.5083 | 0.5735 | 0.8863 | 12.655 | 0.2 |
| strip 1 mm, 35-um copper | 308 MHz | 13 x 7 | 0.5080 | 0.5735 | 0.8857 | 13.090 | 0.4 |
| strip 1 mm, 35-um copper | 801 MHz | 5 x 3 | 0.5135 | 0.5735 | 0.8954 | 7.753 | 0.2 |
| strip 1 mm, 35-um copper | 801 MHz | 9 x 5 | 0.5060 | 0.5735 | 0.8823 | 17.220 | 0.2 |
| strip 1 mm, 35-um copper | 801 MHz | 13 x 7 | 0.5055 | 0.5735 | 0.8815 | 20.604 | 0.4 |
| strip 2.8 mm, 1 um, uniform | DC | 1 x 1 | 2.1563 | 2.1592 | 0.9987 | 238.000 | 0.2 |
| strip 2.8 mm, 35-um copper | DC | 1 x 1 | 2.0681 | 2.1592 | 0.9578 | 6.800 | 0.2 |
| strip 2.8 mm, 35-um copper | 308 MHz | 5 x 3 | 1.9851 | 2.1592 | 0.9194 | 21.442 | 0.2 |
| strip 2.8 mm, 35-um copper | 308 MHz | 9 x 5 | 1.9692 | 2.1592 | 0.9120 | 36.871 | 0.2 |
| strip 2.8 mm, 35-um copper | 308 MHz | 13 x 7 | 1.9682 | 2.1592 | 0.9115 | 38.152 | 0.4 |
| strip 2.8 mm, 35-um copper | 801 MHz | 5 x 3 | 1.9836 | 2.1592 | 0.9187 | 22.389 | 0.2 |
| strip 2.8 mm, 35-um copper | 801 MHz | 9 x 5 | 1.9624 | 2.1592 | 0.9088 | 50.232 | 0.2 |
| strip 2.8 mm, 35-um copper | 801 MHz | 13 x 7 | 1.9610 | 2.1592 | 0.9082 | 60.203 | 0.4 |

## tubes

| Item | Frequency | Filaments / grid | FastHenry (nH) | Estimate (nH) | Ratio | R (mOhm) | Time (s) |
|---|---|---|---|---|---|---|---|
| via as a cage of 8 | DC | 8 strips | 0.6844 | 0.6961 | 0.9833 | 3.038 | 0.2 |
| via as a cage of 16 | DC | 16 strips | 0.6898 | 0.6961 | 0.9910 | 3.038 | 0.2 |
| via as a cage of 32 | DC | 32 strips | 0.6910 | 0.6961 | 0.9927 | 3.038 | 0.2 |
| via as a cage of 64 | DC | 64 strips | 0.6913 | 0.6961 | 0.9931 | 3.038 | 0.4 |
| via, square barrel 0.254 mm | DC | 1 x 1 | 0.7740 | 0.6961 | 1.1119 | 0.421 | 0.2 |
| via, square barrel 0.254 mm | 308 MHz | 5 x 3 | 0.7201 | 0.6961 | 1.0345 | 1.475 | 0.2 |
| via, square barrel 0.254 mm | 308 MHz | 9 x 5 | 0.7046 | 0.6961 | 1.0123 | 4.602 | 0.2 |
| via, square barrel 0.254 mm | 308 MHz | 13 x 7 | 0.7006 | 0.6961 | 1.0065 | 6.079 | 0.2 |
| PDIP-8 hole as a cage of 8 | DC | 8 strips | 0.4298 | 0.4375 | 0.9824 | 1.139 | 0.2 |
| PDIP-8 hole as a cage of 16 | DC | 16 strips | 0.4344 | 0.4375 | 0.9928 | 1.139 | 0.2 |
| PDIP-8 hole as a cage of 32 | DC | 32 strips | 0.4353 | 0.4375 | 0.9950 | 1.139 | 0.2 |
| PDIP-8 hole as a cage of 64 | DC | 64 strips | 0.4357 | 0.4375 | 0.9958 | 1.139 | 0.4 |
| PDIP-8 hole, square barrel 0.678 mm | DC | 1 x 1 | 0.5003 | 0.4375 | 1.1434 | 0.059 | 0.2 |
| PDIP-8 hole, square barrel 0.678 mm | 308 MHz | 5 x 3 | 0.4579 | 0.4375 | 1.0467 | 0.184 | 0.2 |
| PDIP-8 hole, square barrel 0.678 mm | 308 MHz | 9 x 5 | 0.4445 | 0.4375 | 1.0160 | 0.614 | 0.2 |
| PDIP-8 hole, square barrel 0.678 mm | 308 MHz | 13 x 7 | 0.4406 | 0.4375 | 1.0072 | 1.514 | 0.2 |

## leads

| Item | Frequency | Filaments / grid | FastHenry (nH) | Estimate (nH) | Ratio | R (mOhm) | Time (s) |
|---|---|---|---|---|---|---|---|
| SOT-23-5 lead | DC | 1 x 1 | 0.2187 | 0.2655 | 0.8235 | 0.234 | 0.2 |
| SOT-23-5 lead | 308 MHz | 5 x 3 | 0.2010 | 0.2655 | 0.7571 | 0.612 | 0.2 |
| SOT-23-5 lead | 308 MHz | 9 x 5 | 0.1956 | 0.2655 | 0.7365 | 1.607 | 0.2 |
| SOT-23-5 lead | 308 MHz | 13 x 7 | 0.1943 | 0.2655 | 0.7318 | 2.711 | 0.4 |
| SOIC-8 lead | DC | 1 x 1 | 0.4502 | 0.5455 | 0.8252 | 0.306 | 0.2 |
| SOIC-8 lead | 308 MHz | 5 x 3 | 0.4145 | 0.5455 | 0.7598 | 0.855 | 0.2 |
| SOIC-8 lead | 308 MHz | 9 x 5 | 0.4038 | 0.5455 | 0.7402 | 2.412 | 0.2 |
| SOIC-8 lead | 308 MHz | 13 x 7 | 0.4014 | 0.5455 | 0.7357 | 4.148 | 0.4 |
| PDIP-8 lead | DC | 1 x 1 | 1.7105 | 1.3611 | 1.2566 | 1.269 | 0.2 |
| PDIP-8 lead | 308 MHz | 5 x 3 | 1.6398 | 1.3611 | 1.2047 | 1.538 | 0.2 |
| PDIP-8 lead | 308 MHz | 9 x 5 | 1.6194 | 1.3611 | 1.1898 | 2.124 | 0.2 |
| PDIP-8 lead | 308 MHz | 13 x 7 | 1.6137 | 1.3611 | 1.1855 | 3.707 | 0.4 |

## paths

| Item | Frequency | Filaments / grid | FastHenry (nH) | Estimate (nH) | Ratio | R (mOhm) | Time (s) |
|---|---|---|---|---|---|---|---|
| SOT-23-5 path | DC | 1 x 1 | 3.3410 | 3.4110 | 0.9795 | 13.465 | 0.2 |
| SOT-23-5 path | 308 MHz | 5 x 3 | 3.2280 | 3.4110 | 0.9464 | 28.194 | 0.2 |
| SOT-23-5 path | 308 MHz | 9 x 5 | 3.2009 | 3.4110 | 0.9384 | 44.871 | 0.6 |
| SOT-23-5 path | 308 MHz | 13 x 7 | 3.1974 | 3.4110 | 0.9374 | 48.448 | 1.8 |
| SOIC-8 path | DC | 1 x 1 | 5.3814 | 5.4416 | 0.9889 | 18.150 | 0.2 |
| SOIC-8 path | 308 MHz | 5 x 3 | 5.1757 | 5.4416 | 0.9511 | 43.212 | 0.2 |
| SOIC-8 path | 308 MHz | 9 x 5 | 5.1279 | 5.4416 | 0.9423 | 71.572 | 0.6 |
| SOIC-8 path | 308 MHz | 13 x 7 | 5.1210 | 5.4416 | 0.9411 | 77.302 | 3.0 |
| PDIP-8 path | DC | 1 x 1 | 10.0778 | 9.6654 | 1.0427 | 24.906 | 0.2 |
| PDIP-8 path | 308 MHz | 5 x 3 | 9.6797 | 9.6654 | 1.0015 | 73.386 | 0.2 |
| PDIP-8 path | 308 MHz | 9 x 5 | 9.5894 | 9.6654 | 0.9921 | 125.056 | 0.4 |
| PDIP-8 path | 308 MHz | 13 x 7 | 9.5749 | 9.6654 | 0.9906 | 132.426 | 1.0 |

## planes

| Item | Frequency | Filaments / grid | FastHenry (nH) | Estimate (nH) | Ratio | R (mOhm) | Time (s) |
|---|---|---|---|---|---|---|---|
| SOT-23-5 path over the planes | 308 MHz | 9 x 5, plane 32 x 32 | 3.1816 | 3.4110 | 0.9328 | 44.892 | 1.8 |
| SOT-23-5 path over the planes | 308 MHz | 9 x 5, plane 64 x 64 | 3.1727 | 3.4110 | 0.9302 | 44.900 | 13.3 |
| SOT-23-5 path over the planes | 308 MHz | 9 x 5, plane 96 x 96 | 3.1707 | 3.4110 | 0.9296 | 44.904 | 62.0 |
| SOIC-8 path over the planes | 308 MHz | 9 x 5, plane 32 x 32 | 5.1006 | 5.4416 | 0.9373 | 71.619 | 1.4 |
| SOIC-8 path over the planes | 308 MHz | 9 x 5, plane 64 x 64 | 5.1002 | 5.4416 | 0.9373 | 71.624 | 10.7 |
| SOIC-8 path over the planes | 308 MHz | 9 x 5, plane 96 x 96 | 5.0930 | 5.4416 | 0.9359 | 71.618 | 41.9 |

## Numbers quoted in the side note

The side note `TIA_feedback_layouts` quotes these values in Section 4 and Appendix C; `side_note_numbers()` computes them from the records above.

* Eq. (4)'s strip (1 um thick, uniform current), three lengths: -0.27 to -0.13 % of Eq. (4).
* via as a cage of 64 thin strips: 0.6913 nH against Eq. (4)'s tube 0.6961 nH (-0.69 %).
* PDIP-8 hole as a cage of 64 thin strips: 0.4357 nH against Eq. (4)'s tube 0.4375 nH (-0.42 %).
* Traces 0.2 mm wide, 35-um copper, 0.35/1.0/2.8 mm long, at DC: 0.1241 nH (-8.1 %), 0.5413 nH (-5.6 %), 2.0681 nH (-4.2 %).
* Traces 0.2 mm wide, 35-um copper, 0.35/1.0/2.8 mm long, at 308 MHz: 0.1146 nH (-15.1 %), 0.5080 nH (-11.4 %), 1.9682 nH (-8.8 %).
* Traces 0.2 mm wide, 35-um copper, 0.35/1.0/2.8 mm long, at 801 MHz: 0.1139 nH (-15.7 %), 0.5055 nH (-11.9 %), 1.9610 nH (-9.2 %).
* SOT-23-5 lead: sum 0.2655 nH; FastHenry 0.2187 nH at DC (-17.6 %), 0.1943 nH at 308 MHz (-26.8 %).
* SOIC-8 lead: sum 0.5455 nH; FastHenry 0.4502 nH at DC (-17.5 %), 0.4014 nH at 308 MHz (-26.4 %).
* PDIP-8 lead: sum 1.3611 nH; FastHenry 1.7105 nH at DC (+25.7 %), 1.6137 nH at 308 MHz (+18.6 %).
* Eq. (C.1) for the PDIP-8 hole (1.600 mm) and shoulder (2.285 mm): 0.1 nH/mm x [1.600 ln(3.885/1.600) + 2.285 ln(3.885/2.285)] mm = 0.1 x (1.4194 + 1.2128) = 0.2632 nH; 2M = 0.5264 nH. FastHenry's lead exceeds the sum by 0.3493 nH at DC and 0.2525 nH at 308 MHz.
* SOT-23-5 path: sum 3.4110 nH; FastHenry 3.3410 nH at DC (-2.1 %), 3.1974 nH at 308 MHz (-6.3 %).
* SOIC-8 path: sum 5.4416 nH; FastHenry 5.3814 nH at DC (-1.1 %), 5.1210 nH at 308 MHz (-5.9 %).
* PDIP-8 path: sum 9.6654 nH; FastHenry 10.0778 nH at DC (+4.3 %), 9.5749 nH at 308 MHz (-0.9 %).
* SOT-23-5 path with 9 x 5 filaments: 3.2009 nH without the planes, 3.1707 nH over them (-0.94 %).
* SOIC-8 path with 9 x 5 filaments: 5.1279 nH without the planes, 5.0930 nH over them (-0.68 %).
* SOT-23-5: via at |x| = 0.9500 mm, riser at |x| = 0.9500 mm (in line within 0.0000 mm); the two sides' vias 2.687 mm apart, their risers 2.687 mm apart.
* SOIC-8: via at |x| = 2.2000 mm, riser at |x| = 2.1575 mm (in line within 0.0425 mm); the two sides' vias 4.580 mm apart, their risers 4.498 mm apart.
* PDIP-8: the two sides' holes and shoulders 8.032 mm apart.
* SOT-23-5: L_x = 8.1110 nH (sum) and 7.8974 nH (FastHenry, 308 MHz, 13 x 7), each with 2 x 2.35 nH inside; delta_1 = 2.278 % and 2.218 %; delta_2 = 0.438 deg (FastHenry); f_1% higher by +1.34 %; over the planes L_x = 7.8673 nH, delta_1 = 2.210 %.
* SOIC-8: L_x = 10.1416 nH (sum) and 9.8210 nH (FastHenry, 308 MHz, 13 x 7), each with 2 x 2.35 nH inside; delta_1 = 2.849 % and 2.759 %; delta_2 = 0.544 deg (FastHenry); f_1% higher by +1.62 %; over the planes L_x = 9.7863 nH, delta_1 = 2.749 %.
* PDIP-8: L_x = 14.3654 nH (sum) and 14.2749 nH (FastHenry, 308 MHz, 13 x 7), each with 2 x 2.35 nH inside; delta_1 = 4.035 % and 4.010 %; delta_2 = 0.791 deg (FastHenry); f_1% higher by +0.32 %.
* Outermost filament of the trace at 13 x 7: 1.05 um across the width, 1.59 um across the thickness (skin depth 3.74 um at 308 MHz).
* Outermost filament of the SOT-23-5 lead at 13 x 7: 2.11 um across the width, 6.82 um across the thickness (skin depth 3.74 um at 308 MHz).
* Outermost filament of the SOIC-8 lead at 13 x 7: 2.16 um across the width, 8.64 um across the thickness (skin depth 3.74 um at 308 MHz).
* Outermost filament of the PDIP-8 shoulder at 13 x 7: 7.68 um across the width, 11.36 um across the thickness (skin depth 3.74 um at 308 MHz).
* From 9 x 5 to 13 x 7 filaments the paths change by 0.11-0.15 %.
* From 9 x 5 to 13 x 7 filaments the leads change by 0.36-0.64 %.
* From 9 x 5 to 13 x 7 filaments the traces change by 0.05-0.13 %.
* From 9 x 5 to 13 x 7 filaments the tubes (square barrels) change by 0.57-0.87 %.
* From plane grids of 64 x 64 to 96 x 96 the paths change by 0.064-0.141 %.

