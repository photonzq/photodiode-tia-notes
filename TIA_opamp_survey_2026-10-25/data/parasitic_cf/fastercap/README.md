# FasterCap checks of the field solutions of Section G.14

These are the results of `scripts_archive/parasitic_cf/numerical/fastercap_validation.py`, whose docstring describes every case; `pcbcap/pcbcap/fastercap.py` explains how a layout becomes FasterCap's input and how its matrix is read. They are kept here, not in the note. Capacitances in fF.

## What the runs show

* The export is right. Every kind of panel has the area that gmsh's fragments give to within 1e-13 (table below); every panel view was looked at; a cube of 1 mm comes out at the exact 73.510 fF (0.6606782 x 4 pi eps0 a, Hwang and Mascagni, J. Appl. Phys. 95, 3798 (2004)) to +0.08 % with collocation and -0.08 % with Galerkin, and exactly 4.2 times that in a medium of 4.2; per-panel reference points and one inner point per dielectric body give the same 0402 result to 1e-5.
* FasterCap's automatic mode (-a) stops on a small change between two refinements, not on a small error: the cube on a dielectric block stops at -12 % of the half-space bound at -a0.003, while fixed refinements (-m 0.1 to 0.02, Galerkin) rise smoothly to 2.46 times the cube in air.
* FasterCap does not solve the 0402 model reliably. In the grounded 8-mm box, and in free space once the panels pass about 10 000, its GMRES solves stop converging (the 1000-iteration limit) and C_A0 turns negative; the fixed Galerkin refinement fails the same way at 64 000 to 113 000 panels. Before that point the free-space C_F lies at 31 to 35 fF and has not settled, so it neither confirms nor contradicts pcbcap's 42.09 fF (the same film-free 0402 with no ground nearby) or 39.77 +- 0.07 fF (in the 8-mm box). The cube and block cases run cleanly up to the largest refinement kept, 148 375 panels (the block, Galerkin -m0.02, 28 GMRES iterations). A Galerkin run of the free-space 0402 at -m0.1 was stopped by hand before FasterCap printed anything, so its log is empty.
* The thin metal is not the cause (the side note's Appendix D). In a uniform medium (r0402_nofilm_air_box8, every permittivity 1) FasterCap converges smoothly, with 10-25 GMRES iterations, to C_F 9.63 fF and C_A0 25.30 fF at 52 691 panels, against pcbcap's 9.870 +- 0.017 and 25.350 +- 0.015 fF (-2.5 % and -0.2 %); the 2.5 % is FasterCap's collocation error, since its Galerkin scheme on fixed meshes (-m 0.07, 0.05, 0.035 -g: 14 122 to 52 691 panels, 6-14 GMRES iterations) gives C_F 9.85, 9.87, 9.81 fF and C_A0 25.37, 25.51, 25.45 fF, within 0.6 % and 0.7 % of pcbcap. The next mesh (-m0.025 -g) stopped with exit code 1 after 212 s without printing anything. With the dielectrics and every face of the metal cut into panels no wider than the metal is thick (r0402_nofilm_finemetal_box8), its first step (15 008 panels, every solve converged) gives C_F 30.0 fF and C_A0 87.2 fF, and the refinement breaks down as before; the run did not finish within 1800 s. A third case (r0402_nofilm_fine_box8) also cuts every face inside a window of 1.7 x 0.7 x 0.47 mm around the part, dielectric ones included, into panels of 30 um or less (fastercap.ExportOptions.fine_window, fine_panel; 10 111 input panels). Galerkin on that input without refinement (-m100 -g, 20 234 panels, 17-25 GMRES iterations) gives C_F 37.18 fF and C_A0 90.58 fF, and the box's row and column still disagree by a factor of two; the automatic collocation run gives 23-32 and 81-100 fF over seven steps, then fails (GMRES at 1000, exit code 1 after 390 s), and a Galerkin run at -m0.07 exited with code 1 after 21 s without printing anything. The fault lies in the dielectrics' treatment; the board's faces away from the part (its bottom face one 16-mm panel 1.6 mm below the pads) stay coarse in every input.
* The input was checked again for errors in its dielectric part (the side note's Appendix D) and none was found: the panel files carry permittivities 1, 4.2 and 9.7 on the right faces (pad undersides 4.2, terminations' inner faces 9.7, the box walls beside the board 4.2), the '+' chain returns three conductors (g1_A, g1_B, g1_gnd), coordinates are written in metres to ten significant digits, faces are classified by probing at most 1 um off them, and reference points lie 1 um off each dielectric panel on the lower-permittivity side. FasterCap's dielectric answers break reciprocity: at 12 233 panels in the box the box's row gives -88 and -92 fF for its coupling to B and A, its column -43 and -40 fF, and in free space C_AB and C_BA differ by 7 %, while the uniform-medium matrices are symmetric to about 1 %. FasterCap's source (github.com/ediloren/FasterCap, Solver/Autorefine.cpp, CAutoRefine::PotEstimateOpt) computes a dielectric panel's row from the source panel's exact potential at points one twentieth of the centroid distance either side when the centroids lie closer than the longer side of the two panels, and from field quadratures (orders 5, 3, 2) or a point-charge formula farther out.
* FasterCap's "not diagonally dominant" warnings do not mark bad solutions in the grounded box: every row of a conductor inside the box sums to zero, so rounding alone sets them off, and the converged uniform-medium runs show them too. A negative C_A0 does mark a bad solution.
* FastCap 2.0 (the M.I.T. program, in FastFieldSolvers' Windows build 3.6) gives no result on these panel sets and is not used further; the side note's Appendix D explains why it should be avoided for models like these. In r0402_nofilm_air_fine_box8 (7939 panels) the grounded box is six panels, one per face, 16 x 16 and 16 x 17.6 mm, whose centroids lie 7.9 to 9.7 mm from the centroid of the metal; in r0402_nofilm_fine_box8 the box has 14 such panels and the board's bottom face is one 16-mm panel 1.74 mm below the metal's centroid. FastCap2 widens its root cube by the largest panel's diagonal in every direction in which the panel centres spread less than that panel (placeq in mulSetup.c), here from 17.6 to 41.4 mm, so at depth 8 its overlapped preconditioner inverts blocks of up to 2690 panels (2.5e11 operations) and the uniform case's set-up did not finish in 20 minutes. At depth 9 the set-up finished (84 % of the multiplies by multipole expansions), but GMRES on the box's column reached iteration 7448 of the 7939 the program allows (MAXITER in mulGlobal.h, one per panel) without reaching the tolerance 0.001 before the 20-minute limit, in the uniform medium whose answer pcbcap gives to 0.2 %. FastCap2's expansions place each panel's charge at its centroid (mulQ2Multi in mulMulti.c, mulQ2Local in mulLocal.c): seen from the metal's centroid, the six box faces then act on the part 19 to 28 % too strongly and the board's bottom face 3.2 times too strongly (fastcap2_large_panels.py). The program would need the far faces cut into panels small compared with their distance from the part. The dielectric case was not run at depth 8 or 9. Left to itself the program would choose depth 11 for the uniform case (78.5 GB of cube pointers) and depth 3 for the dielectric case (one preconditioner block of 10 103 panels); the runs with -d0 (no partitioning) stopped after one hour inverting the full matrix.
* The strip cases (the film as 10 to 40 strips) were exported and checked but not run, since the film-free model already fails.

## Geometry checks

Every kind of panel (a conductor net with the permittivity it touches, or a pair of permittivities) has the same area in the exported panels as in gmsh's fragments of the same layout; the views are in `views/`.

| Case | Panels | Cells | Kinds | Worst relative area difference |
|---|---|---|---|---|
| cube_free | 6 | 60 | 1 | 0.0e+00 |
| cube_on_block40_free | 20 | 210 | 3 | 1.4e-16 |
| cube_eps4p2_free | 6 | 60 | 1 | 0.0e+00 |
| r0402_nofilm_box8 | 121 | 699 | 10 | 3.5e-16 |
| r0402_nofilm_free8 | 111 | 939 | 8 | 3.7e-16 |
| r0402_nofilm_free16 | 116 | 939 | 8 | 3.5e-16 |
| r0402_nofilm_free32 | 127 | 939 | 8 | 3.5e-16 |
| r0402_nofilm_air_box8 | 78 | 699 | 3 | 2.8e-16 |
| r0402_nofilm_finemetal_box8 | 7484 | 699 | 10 | 2.5e-14 |
| r0402_nofilm_air_fine_box8 | 7939 | 1243 | 3 | 7.1e-14 |
| r0402_nofilm_fine_box8 | 10111 | 1243 | 10 | 2.5e-14 |
| r0402_strips10_box8 | 975 | 1676 | 30 | 1.1e-14 |
| r0402_strips20_box8 | 1805 | 2652 | 50 | 2.1e-14 |
| r0402_strips40_box8 | 3545 | 4536 | 90 | 4.1e-14 |
| r0402_strips10_free8 | 965 | 2176 | 28 | 1.1e-14 |
| r0402_strips20_free8 | 1795 | 3408 | 48 | 2.1e-14 |
| r0402_strips40_free8 | 3535 | 5796 | 88 | 4.1e-14 |
| r0402_strips20_free16 | 1800 | 3408 | 48 | 2.1e-14 |
| r0402_strips20_free32 | 1811 | 3408 | 48 | 2.1e-14 |

## cube_free

| FasterCap options | Panels | C | Exact | Error | Time (s) |
|---|---|---|---|---|---|
| -a0.01 | 96 | 71.7202 | 73.5104 | -2.435% | 0.1 |
| -a0.003 | 432 | 72.8762 | 73.5104 | -0.863% | 0.1 |
| -a0.001 | 2112 | 73.3493 | 73.5104 | -0.219% | 0.3 |
| -a0.0003 | 26880 | 73.5667 | 73.5104 | +0.077% | 4.8 |
| -a0.01 -g | 96 | 72.3203 | 73.5104 | -1.619% | 0.1 |
| -a0.003 -g | 96 | 72.3047 | 73.5104 | -1.640% | 0.1 |
| -a0.001 -g | 432 | 73.0606 | 73.5104 | -0.612% | 0.2 |
| -a0.0003 -g | 2112 | 73.4506 | 73.5104 | -0.081% | 0.9 |

## cube_on_block40_free

The reference is the half-space limit, 2.6 times the cube in air: an upper bound for the finite block, not its exact value.

| FasterCap options | Panels | C | Half-space limit | Below the limit | Time (s) |
|---|---|---|---|---|---|
| -m0.1 -g | 26622 | 178.4490 | 191.1269 | -6.633% | 2.3 |
| -m0.05 -g | 56114 | 180.0620 | 191.1269 | -5.789% | 5.5 |
| -m0.03 -g | 99805 | 180.5290 | 191.1269 | -5.545% | 10.7 |
| -m0.02 -g | 148375 | 180.8510 | 191.1269 | -5.377% | 17.1 |
| -a0.01 | 267 | 164.9180 | 191.1269 | -13.713% | 0.1 |
| -a0.003 | 939 | 167.6390 | 191.1269 | -12.289% | 0.2 |

## cube_eps4p2_free

| FasterCap options | Panels | C | Exact | Error | Time (s) |
|---|---|---|---|---|---|
| -a0.01 | 96 | 301.2250 | 308.7435 | -2.435% | 0.0 |
| -a0.003 | 432 | 306.0800 | 308.7435 | -0.863% | 0.1 |
| -a0.001 | 2112 | 308.0670 | 308.7435 | -0.219% | 0.3 |
| -a0.0003 | 26880 | 308.9800 | 308.7435 | +0.077% | 4.5 |
| -a0.01 -g | 96 | 303.7450 | 308.7435 | -1.619% | 0.1 |
| -a0.003 -g | 96 | 303.6800 | 308.7435 | -1.640% | 0.1 |
| -a0.001 -g | 432 | 306.8540 | 308.7435 | -0.612% | 0.2 |
| -a0.0003 -g | 2112 | 308.4930 | 308.7435 | -0.081% | 0.9 |

## r0402_nofilm_free8

| FasterCap options | Panels | $C_F$ | $C_{A0}$ | $-C_{AB}$ / $-C_{BA}$ | Asymmetry | Time (s) |
|---|---|---|---|---|---|---|
| -a0.01 -ap | 1534 | 31.044 | 83.501 | 32.141 / 29.948 | 1.9e-02 | 0.4 |
| -m0.5 -g | 63983 | 35.438 | 79.309 | 32.063 / 38.812 | 5.9e-02 | 94.9 |
| -m0.3 -g | 112931 | 132.594 | -176.095 | 118.451 / 146.737 | 3.4e-01 | 348.1 |

## r0402_nofilm_air_box8

| FasterCap options | Panels | $C_F$ | $C_{A0}$ | $-C_{AB}$ / $-C_{BA}$ | Asymmetry | Time (s) |
|---|---|---|---|---|---|---|
| -a0.01 -ap | 304 | 6.776 | 21.415 | 6.911 / 6.640 | 3.2e-04 | 0.1 |
| -a0.003 -ap | 880 | 9.060 | 23.117 | 9.067 / 9.052 | 6.8e-05 | 0.3 |
| -a0.001 -ap | 14122 | 9.601 | 25.154 | 9.598 / 9.605 | 2.9e-05 | 3.3 |
| -a0.0003 -ap | 52691 | 9.626 | 25.295 | 9.621 / 9.632 | 1.5e-05 | 14.3 |
| -m0.07 -g | 14122 | 9.852 | 25.368 | 9.846 / 9.858 | 1.0e-04 | 3.0 |
| -m0.05 -g | 27241 | 9.870 | 25.512 | 9.863 / 9.877 | 2.5e-04 | 7.6 |
| -m0.035 -g | 52691 | 9.812 | 25.451 | 9.811 / 9.813 | 5.6e-04 | 12.9 |

## r0402_nofilm_fine_box8

| FasterCap options | Panels | $C_F$ | $C_{A0}$ | $-C_{AB}$ / $-C_{BA}$ | Asymmetry | Time (s) |
|---|---|---|---|---|---|---|
| -m100 -g | 20234 | 37.182 | 90.577 | 35.670 / 38.694 | 5.8e-02 | 0.9 |

## FastCap 2.0 on the same panels

Each case's panels in FastCap 2.0's format (`<case>/fastcap2/`, with one reference point inside each dielectric body), run by the FastFieldSolvers build of FastCap2 through its automation object (`cmd_fastcap2`); `fastcap2_<options>.log` is its console output. -o is the order of the multipole expansions, -t the tolerance of the iterative solution and -d the depth of the partitioning into cubes (without -d the program chooses it).

| Case | FastCap2 options | Partitioning levels | $C_F$ | $C_{A0}$ | $-C_{AB}$ / $-C_{BA}$ | Asymmetry | Solve time (s) |
|---|---|---|---|---|---|---|---|
| r0402_nofilm_air_fine_box8 | -d0 -t0.001 | 0 | no result: stopped after 3600 s, output not kept | | | | |
| r0402_nofilm_air_fine_box8 | -o3 -t0.001 -d8 | 8 | no result: set-up unfinished when stopped after 1200 s | | | | |
| r0402_nofilm_air_fine_box8 | -o3 -t0.001 -d9 -z | 9 | no result: GMRES on column 1 (gnd) at iteration 7448 when stopped after 1200 s | | | | |
| r0402_nofilm_fine_box8 | -d0 -t0.001 | 0 | no result: stopped after 3600 s, output not kept | | | | |

## Refinement steps of every run

Each automatic run (-a) prints its matrix after every refinement step; a fixed run (-m) has one step. GMRES failures are FasterCap's "not converging after 1000 iterations"; matrix warnings are its "not diagonally dominant" and "non-negative off-diagonal" messages. In free space a correct Maxwell matrix cannot trigger them; in the grounded box every row of an enclosed conductor sums to zero, so rounding alone can trigger the first.

### cube_free, fastercap_a0.0003.log

GMRES iterations per solve: 2, 2, 3, 4, 4, 5, 6, 7, 8, 9, 11, 13, 14. GMRES failures: 0; matrix warnings: 0.

| Step | Panels | Change of the matrix | C |
|---|---|---|---|
| 1 | 12 |  | 60.646 |
| 2 | 48 | 0.147167 | 71.111 |
| 3 | 96 | 0.00837319 | 71.711 |
| 4 | 144 | 0.00922974 | 72.380 |
| 5 | 240 | 0.0050325 | 72.746 |
| 6 | 432 | 0.00182621 | 72.879 |
| 7 | 672 | 0.00174253 | 73.006 |
| 8 | 1296 | 0.00398533 | 73.298 |
| 9 | 2112 | 0.00078362 | 73.356 |
| 10 | 4176 | 0.00122696 | 73.446 |
| 11 | 7296 | 0.000418811 | 73.476 |
| 12 | 14544 | 0.00120843 | 73.565 |
| 13 | 26880 | 1.9473e-05 | 73.567 |

### cube_free, fastercap_a0.0003_g.log

GMRES iterations per solve: 2, 2, 4, 4, 5, 6, 7, 9, 9. GMRES failures: 0; matrix warnings: 0.

| Step | Panels | Change of the matrix | C |
|---|---|---|---|
| 1 | 12 |  | 70.753 |
| 2 | 48 | 0.0199848 | 72.196 |
| 3 | 96 | 0.00149525 | 72.304 |
| 4 | 144 | 0.00743579 | 72.845 |
| 5 | 240 | 0.00260824 | 73.036 |
| 6 | 432 | 0.000401988 | 73.065 |
| 7 | 672 | 0.00107871 | 73.144 |
| 8 | 1296 | 0.00390575 | 73.431 |
| 9 | 2112 | 0.000267398 | 73.451 |

### cube_free, fastercap_a0.001.log

GMRES iterations per solve: 2, 1, 2, 3, 3, 4, 5, 6, 6. GMRES failures: 0; matrix warnings: 0.

| Step | Panels | Change of the matrix | C |
|---|---|---|---|
| 1 | 12 |  | 60.646 |
| 2 | 48 | 0.147167 | 71.111 |
| 3 | 96 | 0.00837977 | 71.712 |
| 4 | 144 | 0.00920189 | 72.378 |
| 5 | 240 | 0.00503394 | 72.744 |
| 6 | 432 | 0.00181837 | 72.877 |
| 7 | 672 | 0.00170215 | 73.001 |
| 8 | 1296 | 0.00400346 | 73.294 |
| 9 | 2112 | 0.00074917 | 73.349 |

### cube_free, fastercap_a0.001_g.log

GMRES iterations per solve: 2, 1, 2, 4, 3, 5. GMRES failures: 0; matrix warnings: 0.

| Step | Panels | Change of the matrix | C |
|---|---|---|---|
| 1 | 12 |  | 70.753 |
| 2 | 48 | 0.0199848 | 72.196 |
| 3 | 96 | 0.00150798 | 72.305 |
| 4 | 144 | 0.0074232 | 72.845 |
| 5 | 240 | 0.00261388 | 73.036 |
| 6 | 432 | 0.000331831 | 73.061 |

### cube_free, fastercap_a0.003.log

GMRES iterations per solve: 1, 1, 1, 2, 1, 3. GMRES failures: 0; matrix warnings: 0.

| Step | Panels | Change of the matrix | C |
|---|---|---|---|
| 1 | 12 |  | 60.652 |
| 2 | 48 | 0.147086 | 71.111 |
| 3 | 96 | 0.00849392 | 71.720 |
| 4 | 144 | 0.00907265 | 72.377 |
| 5 | 240 | 0.00512167 | 72.749 |
| 6 | 432 | 0.00174023 | 72.876 |

### cube_free, fastercap_a0.003_g.log

GMRES iterations per solve: 1, 1, 2. GMRES failures: 0; matrix warnings: 0.

| Step | Panels | Change of the matrix | C |
|---|---|---|---|
| 1 | 12 |  | 70.752 |
| 2 | 48 | 0.0199979 | 72.196 |
| 3 | 96 | 0.00150798 | 72.305 |

### cube_free, fastercap_a0.01.log

GMRES iterations per solve: 1, 1, 1. GMRES failures: 0; matrix warnings: 0.

| Step | Panels | Change of the matrix | C |
|---|---|---|---|
| 1 | 12 |  | 60.652 |
| 2 | 48 | 0.147086 | 71.111 |
| 3 | 96 | 0.00849392 | 71.720 |

### cube_free, fastercap_a0.01_g.log

GMRES iterations per solve: 1, 1, 1. GMRES failures: 0; matrix warnings: 0.

| Step | Panels | Change of the matrix | C |
|---|---|---|---|
| 1 | 12 |  | 70.752 |
| 2 | 48 | 0.0199979 | 72.196 |
| 3 | 96 | 0.00172321 | 72.320 |

### cube_on_block40_free, fastercap_a0.003.log

GMRES iterations per solve: 4, 4, 5, 5, 5, 5, 6, 6, 6. GMRES failures: 0; matrix warnings: 0.

| Step | Panels | Change of the matrix | C |
|---|---|---|---|
| 1 | 44 |  | 132.099 |
| 2 | 54 | 0.166423 | 158.472 |
| 3 | 75 | 0.0195363 | 161.630 |
| 4 | 94 | 0.0145285 | 164.013 |
| 5 | 163 | 0.0112738 | 165.883 |
| 6 | 267 | 0.0062924 | 164.845 |
| 7 | 399 | 0.00840292 | 166.242 |
| 8 | 628 | 0.0096527 | 167.863 |
| 9 | 939 | 0.00133626 | 167.639 |

### cube_on_block40_free, fastercap_a0.01.log

GMRES iterations per solve: 3, 4, 4, 4, 4, 4. GMRES failures: 0; matrix warnings: 0.

| Step | Panels | Change of the matrix | C |
|---|---|---|---|
| 1 | 44 |  | 132.273 |
| 2 | 54 | 0.165324 | 158.472 |
| 3 | 75 | 0.0196565 | 161.650 |
| 4 | 94 | 0.0143599 | 164.005 |
| 5 | 163 | 0.0119821 | 165.994 |
| 6 | 267 | 0.00652169 | 164.918 |

### cube_on_block40_free, fastercap_m0.02_g.log

GMRES iterations per solve: 28. GMRES failures: 0; matrix warnings: 0.

| Step | Panels | Change of the matrix | C |
|---|---|---|---|
| 1 | 148375 |  | 180.851 |

### cube_on_block40_free, fastercap_m0.03_g.log

GMRES iterations per solve: 25. GMRES failures: 0; matrix warnings: 0.

| Step | Panels | Change of the matrix | C |
|---|---|---|---|
| 1 | 99805 |  | 180.529 |

### cube_on_block40_free, fastercap_m0.05_g.log

GMRES iterations per solve: 21. GMRES failures: 0; matrix warnings: 0.

| Step | Panels | Change of the matrix | C |
|---|---|---|---|
| 1 | 56114 |  | 180.062 |

### cube_on_block40_free, fastercap_m0.1_g.log

GMRES iterations per solve: 16. GMRES failures: 0; matrix warnings: 0.

| Step | Panels | Change of the matrix | C |
|---|---|---|---|
| 1 | 26622 |  | 178.449 |

### cube_eps4p2_free, fastercap_a0.0003.log

GMRES iterations per solve: 2, 2, 3, 4, 4, 5, 6, 7, 8, 9, 11, 13, 14. GMRES failures: 0; matrix warnings: 0.

| Step | Panels | Change of the matrix | C |
|---|---|---|---|
| 1 | 12 |  | 254.712 |
| 2 | 48 | 0.147167 | 298.666 |
| 3 | 96 | 0.00837319 | 301.188 |
| 4 | 144 | 0.00922974 | 303.994 |
| 5 | 240 | 0.0050325 | 305.531 |
| 6 | 432 | 0.00182621 | 306.090 |
| 7 | 672 | 0.00174253 | 306.625 |
| 8 | 1296 | 0.00398533 | 307.852 |
| 9 | 2112 | 0.00078362 | 308.093 |
| 10 | 4176 | 0.00122696 | 308.472 |
| 11 | 7296 | 0.000418811 | 308.601 |
| 12 | 14544 | 0.00120843 | 308.974 |
| 13 | 26880 | 1.9473e-05 | 308.980 |

### cube_eps4p2_free, fastercap_a0.0003_g.log

GMRES iterations per solve: 2, 2, 4, 4, 5, 6, 7, 9, 9. GMRES failures: 0; matrix warnings: 0.

| Step | Panels | Change of the matrix | C |
|---|---|---|---|
| 1 | 12 |  | 297.162 |
| 2 | 48 | 0.0199848 | 303.222 |
| 3 | 96 | 0.00149525 | 303.676 |
| 4 | 144 | 0.00743579 | 305.951 |
| 5 | 240 | 0.00260824 | 306.751 |
| 6 | 432 | 0.000401988 | 306.874 |
| 7 | 672 | 0.00107871 | 307.206 |
| 8 | 1296 | 0.00390575 | 308.410 |
| 9 | 2112 | 0.000267398 | 308.493 |

### cube_eps4p2_free, fastercap_a0.001.log

GMRES iterations per solve: 2, 1, 2, 3, 3, 4, 5, 6, 6. GMRES failures: 0; matrix warnings: 0.

| Step | Panels | Change of the matrix | C |
|---|---|---|---|
| 1 | 12 |  | 254.712 |
| 2 | 48 | 0.147167 | 298.666 |
| 3 | 96 | 0.00837977 | 301.190 |
| 4 | 144 | 0.00920189 | 303.987 |
| 5 | 240 | 0.00503394 | 305.525 |
| 6 | 432 | 0.00181837 | 306.082 |
| 7 | 672 | 0.00170215 | 306.604 |
| 8 | 1296 | 0.00400346 | 307.836 |
| 9 | 2112 | 0.00074917 | 308.067 |

### cube_eps4p2_free, fastercap_a0.001_g.log

GMRES iterations per solve: 2, 1, 2, 4, 3, 5. GMRES failures: 0; matrix warnings: 0.

| Step | Panels | Change of the matrix | C |
|---|---|---|---|
| 1 | 12 |  | 297.162 |
| 2 | 48 | 0.0199848 | 303.222 |
| 3 | 96 | 0.00150798 | 303.680 |
| 4 | 144 | 0.0074232 | 305.951 |
| 5 | 240 | 0.00261388 | 306.753 |
| 6 | 432 | 0.000331831 | 306.854 |

### cube_eps4p2_free, fastercap_a0.003.log

GMRES iterations per solve: 1, 1, 1, 2, 1, 3. GMRES failures: 0; matrix warnings: 0.

| Step | Panels | Change of the matrix | C |
|---|---|---|---|
| 1 | 12 |  | 254.737 |
| 2 | 48 | 0.147086 | 298.666 |
| 3 | 96 | 0.00849392 | 301.225 |
| 4 | 144 | 0.00907265 | 303.983 |
| 5 | 240 | 0.00512167 | 305.548 |
| 6 | 432 | 0.00174023 | 306.080 |

### cube_eps4p2_free, fastercap_a0.003_g.log

GMRES iterations per solve: 1, 1, 2. GMRES failures: 0; matrix warnings: 0.

| Step | Panels | Change of the matrix | C |
|---|---|---|---|
| 1 | 12 |  | 297.158 |
| 2 | 48 | 0.0199979 | 303.222 |
| 3 | 96 | 0.00150798 | 303.680 |

### cube_eps4p2_free, fastercap_a0.01.log

GMRES iterations per solve: 1, 1, 1. GMRES failures: 0; matrix warnings: 0.

| Step | Panels | Change of the matrix | C |
|---|---|---|---|
| 1 | 12 |  | 254.737 |
| 2 | 48 | 0.147086 | 298.666 |
| 3 | 96 | 0.00849392 | 301.225 |

### cube_eps4p2_free, fastercap_a0.01_g.log

GMRES iterations per solve: 1, 1, 1. GMRES failures: 0; matrix warnings: 0.

| Step | Panels | Change of the matrix | C |
|---|---|---|---|
| 1 | 12 |  | 297.158 |
| 2 | 48 | 0.0199979 | 303.222 |
| 3 | 96 | 0.00172321 | 303.745 |

### r0402_nofilm_box8, fastercap_a0.01.log

GMRES iterations per solve: 10, 9, 9, 11, 10, 11, 13, 12, 11, 14, 12, 12, 15, 14, 14, 18, 16, 15, 21, 18, 18, 23, 24, 23, 24, 28, 25, 31, 33, 32, 52, 70, 65, 115, 136, 107, 1000, 141, 473, 691, 1000, 1000, 1000, 1000, 675. GMRES failures: 5; matrix warnings: 7.

| Step | Panels | Change of the matrix | $C_F$ | $C_{A0}$ |
|---|---|---|---|---|
| 1 | 370 |  | 32.814 | 76.969 |
| 2 | 586 | 2.96977 | 27.308 | 94.063 |
| 3 | 809 | 0.144091 | 27.367 | 92.289 |
| 4 | 1042 | 0.0204182 | 27.225 | 92.740 |
| 5 | 1669 | 0.0809163 | 26.623 | 93.537 |
| 6 | 2654 | 0.0392165 | 26.469 | 93.903 |
| 7 | 4044 | 0.142777 | 26.819 | 92.571 |
| 8 | 5675 | 0.0427119 | 27.263 | 91.416 |
| 9 | 8835 | 0.0408787 | 28.186 | 91.770 |
| 10 | 12233 | 0.0404615 | 28.256 | 91.187 |
| 11 | 18918 | 0.0601585 | 29.856 | 74.492 |
| 12 | 26903 | 0.0482429 | 24.757 | 62.250 |
| 13 | 40386 | 0.129063 | 30.166 | 60.475 |
| 14 | 57042 | 0.076687 | 65.754 | -36.423 |

### r0402_nofilm_box8, fastercap_a0.01_ap.log

GMRES iterations per solve: 10, 9, 9, 11, 10, 11, 13, 12, 11, 14, 12, 12, 15, 14, 14, 18, 16, 15, 21, 18, 18, 23, 24, 23, 24, 28, 25, 31, 33, 32, 46, 46, 45, 71, 68, 68, 106, 96, 1000, 140, 140, 325, 198, 17. GMRES failures: 1; matrix warnings: 6.

| Step | Panels | Change of the matrix | $C_F$ | $C_{A0}$ |
|---|---|---|---|---|
| 1 | 370 |  | 32.814 | 76.969 |
| 2 | 586 | 2.96977 | 27.308 | 94.063 |
| 3 | 809 | 0.144091 | 27.367 | 92.289 |
| 4 | 1042 | 0.0204182 | 27.225 | 92.740 |
| 5 | 1669 | 0.0809163 | 26.623 | 93.537 |
| 6 | 2654 | 0.0392165 | 26.469 | 93.903 |
| 7 | 4044 | 0.142777 | 26.819 | 92.571 |
| 8 | 5675 | 0.0427119 | 27.263 | 91.416 |
| 9 | 8835 | 0.0408787 | 28.186 | 91.770 |
| 10 | 12233 | 0.0404615 | 28.256 | 91.187 |
| 11 | 18918 | 0.0605834 | 29.451 | 73.822 |
| 12 | 26903 | 0.0468157 | 26.642 | 60.460 |
| 13 | 40386 | 0.153632 | 28.696 | 254.038 |
| 14 | 57042 | 0.142586 | 33.746 | 41.272 |

### r0402_nofilm_free8, fastercap_a0.003_ap.log

GMRES iterations per solve: 9, 9, 10, 10, 10, 10, 10, 11, 11, 10, 10, 10, 11, 10, 11, 11, 12, 11, 12, 12, 17, 17, 36, 37, 106, 68, 70, 70, 82, 82, 1000, 1000, 1000, 1000, 92, 91, 1000, 1000. GMRES failures: 6; matrix warnings: 7.

| Step | Panels | Change of the matrix | $C_F$ | $C_{A0}$ |
|---|---|---|---|---|
| 1 | 350 |  | 68.364 | 1.064 |
| 2 | 393 | 0.0516814 | 64.579 | 9.298 |
| 3 | 437 | 0.31339 | 40.764 | 64.202 |
| 4 | 516 | 0.0691638 | 36.843 | 71.014 |
| 5 | 598 | 0.04917 | 33.916 | 78.388 |
| 6 | 803 | 0.0249037 | 31.904 | 82.570 |
| 7 | 1067 | 0.0146271 | 31.487 | 82.773 |
| 8 | 1534 | 0.0044948 | 31.010 | 83.547 |
| 9 | 2115 | 0.0168969 | 31.493 | 83.420 |
| 10 | 3032 | 0.0173802 | 32.044 | 85.529 |
| 11 | 4867 | 0.0568107 | 31.973 | 76.958 |
| 12 | 7283 | 0.0792567 | 33.691 | 66.992 |
| 13 | 10617 | 0.347057 | 45.964 | 120.780 |
| 14 | 16316 | 0.435792 | 37.778 | 63.708 |
| 15 | 23573 | 0.802948 | 142.508 | 389.401 |
| 16 | 34591 | 0.960934 | 223.879 | -87.704 |
| 17 | 51305 | 0.519654 | 629.155 | -310.702 |
| 18 | 75240 | 16.0864 | 19.993 | 50.409 |
| 19 | None |  | 22.976 | -1.177 |

### r0402_nofilm_free8, fastercap_a0.01_ap.log

GMRES iterations per solve: 8, 8, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 10, 9. GMRES failures: 0; matrix warnings: 1.

| Step | Panels | Change of the matrix | $C_F$ | $C_{A0}$ |
|---|---|---|---|---|
| 1 | 350 |  | 68.225 | 1.251 |
| 2 | 393 | 0.0497026 | 64.802 | 9.179 |
| 3 | 437 | 0.314236 | 40.782 | 64.270 |
| 4 | 516 | 0.069134 | 36.847 | 71.019 |
| 5 | 598 | 0.0492488 | 33.945 | 78.431 |
| 6 | 803 | 0.0248421 | 31.934 | 82.618 |
| 7 | 1067 | 0.014595 | 31.547 | 82.774 |
| 8 | 1534 | 0.00449197 | 31.044 | 83.501 |

### r0402_nofilm_free8, fastercap_m0.3_g.log

GMRES iterations per solve: 1000, 1000. GMRES failures: 2; matrix warnings: 2.

| Step | Panels | Change of the matrix | $C_F$ | $C_{A0}$ |
|---|---|---|---|---|
| 1 | 112931 |  | 132.594 | -176.095 |

### r0402_nofilm_free8, fastercap_m0.5_g.log

GMRES iterations per solve: 84, 1000. GMRES failures: 1; matrix warnings: 0.

| Step | Panels | Change of the matrix | $C_F$ | $C_{A0}$ |
|---|---|---|---|---|
| 1 | 63983 |  | 35.438 | 79.309 |

### r0402_nofilm_free8, orientation_orientation_check.lst.log

GMRES iterations per solve: 8, 8, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 10, 9. GMRES failures: 0; matrix warnings: 1.

| Step | Panels | Change of the matrix | $C_F$ | $C_{A0}$ |
|---|---|---|---|---|
| 1 | 350 |  | 68.225 | 1.251 |
| 2 | 399 | 0.0499876 | 64.781 | 9.225 |
| 3 | 443 | 0.314164 | 40.765 | 64.309 |
| 4 | 521 | 0.0690001 | 36.846 | 71.023 |
| 5 | 609 | 0.0492482 | 33.942 | 78.436 |
| 6 | 808 | 0.0248208 | 31.934 | 82.618 |
| 7 | 1075 | 0.0145956 | 31.546 | 82.775 |
| 8 | 1538 | 0.00448865 | 31.044 | 83.501 |

### r0402_nofilm_free8, orientation_r0402_nofilm_free8.lst.log

GMRES iterations per solve: 8, 8, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 10, 9. GMRES failures: 0; matrix warnings: 1.

| Step | Panels | Change of the matrix | $C_F$ | $C_{A0}$ |
|---|---|---|---|---|
| 1 | 350 |  | 68.225 | 1.251 |
| 2 | 393 | 0.0497026 | 64.802 | 9.179 |
| 3 | 437 | 0.314236 | 40.782 | 64.270 |
| 4 | 516 | 0.069134 | 36.847 | 71.019 |
| 5 | 598 | 0.0492488 | 33.945 | 78.431 |
| 6 | 803 | 0.0248421 | 31.934 | 82.618 |
| 7 | 1067 | 0.014595 | 31.547 | 82.774 |
| 8 | 1534 | 0.00449197 | 31.044 | 83.501 |

### r0402_nofilm_air_box8, fastercap_a0.0003_ap.log

GMRES iterations per solve: 14, 11, 10, 12, 11, 10, 12, 12, 11, 12, 13, 12, 13, 15, 15, 22, 25, 24, 16, 21, 22, 16, 24, 24, 15, 14, 14, 20, 22, 21, 20, 20, 20, 19, 16, 16, 15, 15, 15, 18, 17, 17. GMRES failures: 0; matrix warnings: 16.

| Step | Panels | Change of the matrix | $C_F$ | $C_{A0}$ |
|---|---|---|---|---|
| 1 | 220 |  | 3.621 | 27.980 |
| 2 | 256 | 0.267543 | 6.852 | 21.374 |
| 3 | 304 | 0.00816271 | 6.814 | 21.453 |
| 4 | 380 | 0.00811703 | 6.396 | 19.628 |
| 5 | 496 | 0.00978392 | 7.161 | 23.180 |
| 6 | 652 | 0.00385669 | 7.860 | 23.486 |
| 7 | 880 | 0.00214237 | 9.061 | 23.116 |
| 8 | 1360 | 0.00381705 | 9.102 | 23.708 |
| 9 | 2325 | 0.00250774 | 9.299 | 24.101 |
| 10 | 4065 | 0.00165278 | 9.160 | 24.557 |
| 11 | 7554 | 0.00149796 | 9.509 | 25.040 |
| 12 | 14122 | 0.000903096 | 9.601 | 25.155 |
| 13 | 27244 | 0.000889251 | 9.630 | 25.322 |
| 14 | 52691 | 0.000159897 | 9.626 | 25.295 |

### r0402_nofilm_air_box8, fastercap_a0.001_ap.log

GMRES iterations per solve: 11, 8, 8, 9, 8, 8, 9, 9, 9, 10, 10, 10, 10, 11, 11, 12, 13, 20, 11, 15, 17, 11, 18, 20, 11, 11, 11, 14, 18, 17, 15, 14, 14, 13, 11, 11. GMRES failures: 0; matrix warnings: 16.

| Step | Panels | Change of the matrix | $C_F$ | $C_{A0}$ |
|---|---|---|---|---|
| 1 | 220 |  | 3.619 | 27.979 |
| 2 | 256 | 0.267533 | 6.849 | 21.371 |
| 3 | 304 | 0.00815458 | 6.812 | 21.452 |
| 4 | 380 | 0.00814286 | 6.394 | 19.629 |
| 5 | 496 | 0.0097905 | 7.161 | 23.190 |
| 6 | 652 | 0.00381316 | 7.834 | 23.447 |
| 7 | 880 | 0.00218775 | 9.060 | 23.114 |
| 8 | 1360 | 0.00378172 | 9.097 | 23.709 |
| 9 | 2325 | 0.00251397 | 9.298 | 24.101 |
| 10 | 4065 | 0.00167368 | 9.157 | 24.561 |
| 11 | 7554 | 0.00148824 | 9.510 | 25.038 |
| 12 | 14122 | 0.000851617 | 9.601 | 25.154 |

### r0402_nofilm_air_box8, fastercap_a0.003_ap.log

GMRES iterations per solve: 9, 7, 6, 8, 7, 7, 7, 7, 7, 8, 8, 8, 8, 9, 10, 7, 10, 11, 7, 11, 12. GMRES failures: 0; matrix warnings: 14.

| Step | Panels | Change of the matrix | $C_F$ | $C_{A0}$ |
|---|---|---|---|---|
| 1 | 220 |  | 3.604 | 27.959 |
| 2 | 256 | 0.267914 | 6.837 | 21.362 |
| 3 | 304 | 0.00810066 | 6.797 | 21.441 |
| 4 | 380 | 0.00810989 | 6.385 | 19.623 |
| 5 | 496 | 0.00984229 | 7.150 | 23.205 |
| 6 | 652 | 0.00376045 | 7.834 | 23.396 |
| 7 | 880 | 0.00213791 | 9.060 | 23.117 |

### r0402_nofilm_air_box8, fastercap_a0.01_ap.log

GMRES iterations per solve: 7, 5, 5, 6, 5, 5, 5, 5, 5. GMRES failures: 0; matrix warnings: 6.

| Step | Panels | Change of the matrix | $C_F$ | $C_{A0}$ |
|---|---|---|---|---|
| 1 | 220 |  | 3.598 | 27.910 |
| 2 | 256 | 0.267244 | 6.818 | 21.331 |
| 3 | 304 | 0.00824469 | 6.776 | 21.415 |

### r0402_nofilm_air_box8, fastercap_m0.035_g.log

GMRES iterations per solve: 7, 14, 14. GMRES failures: 0; matrix warnings: 0.

| Step | Panels | Change of the matrix | $C_F$ | $C_{A0}$ |
|---|---|---|---|---|
| 1 | 52691 |  | 9.812 | 25.451 |

### r0402_nofilm_air_box8, fastercap_m0.05_g.log

GMRES iterations per solve: 7, 13, 12. GMRES failures: 0; matrix warnings: 0.

| Step | Panels | Change of the matrix | $C_F$ | $C_{A0}$ |
|---|---|---|---|---|
| 1 | 27241 |  | 9.870 | 25.512 |

### r0402_nofilm_air_box8, fastercap_m0.07_g.log

GMRES iterations per solve: 6, 11, 11. GMRES failures: 0; matrix warnings: 0.

| Step | Panels | Change of the matrix | $C_F$ | $C_{A0}$ |
|---|---|---|---|---|
| 1 | 14122 |  | 9.852 | 25.368 |

### r0402_nofilm_finemetal_box8, fastercap_a0.01_ap.log

GMRES iterations per solve: 27, 19, 19, 31, 21, 18, 35, 26, 26, 35, 28, 28, 282, 151, 169, 235, 143, 134, 1000, 160, 293, 1000, 1000, 1000, 1000, 1000, 1000, 429, 372, 366, 526, 520, 527, 596, 409, 192. GMRES failures: 7; matrix warnings: 7.

| Step | Panels | Change of the matrix | $C_F$ | $C_{A0}$ |
|---|---|---|---|---|
| 1 | 15008 |  | 30.031 | 87.151 |
| 2 | 17292 | 2.47187 | 23.163 | 96.563 |
| 3 | 20313 | 0.185787 | 24.225 | 95.003 |
| 4 | 23472 | 0.0424238 | 24.628 | 93.717 |
| 5 | 26870 | 0.0387655 | 24.997 | 94.350 |
| 6 | 33459 | 0.103807 | 32.472 | 84.018 |
| 7 | 41355 | 0.0257308 | 33.711 | 80.351 |
| 8 | 54598 | 0.117499 | 60.758 | 50.528 |
| 9 | 71012 | 0.0558514 | 25.553 | 86.944 |
| 10 | 98439 | 0.0423515 | 48.394 | 79.911 |
| 11 | 133211 | 0.0142442 | 43.607 | 81.540 |

### r0402_nofilm_fine_box8, fastercap_a0.01_ap.log

GMRES iterations per solve: 27, 19, 20, 33, 24, 23, 34, 27, 27, 285, 160, 158, 299, 208, 196, 1000, 282, 236, 1000, 568, 535, 1000, 586. GMRES failures: 3; matrix warnings: 4.

| Step | Panels | Change of the matrix | $C_F$ | $C_{A0}$ |
|---|---|---|---|---|
| 1 | 20230 |  | 31.537 | 86.421 |
| 2 | 23246 | 3.28901 | 23.057 | 100.482 |
| 3 | 27031 | 0.0739848 | 23.555 | 100.035 |
| 4 | 30576 | 0.108054 | 24.236 | 100.197 |
| 5 | 35326 | 0.0299044 | 26.726 | 92.286 |
| 6 | 43007 | 0.116538 | 25.678 | 84.068 |
| 7 | 52696 | 0.15777 | 30.846 | 80.781 |

### r0402_nofilm_fine_box8, fastercap_m100_g.log

GMRES iterations per solve: 25, 17, 17. GMRES failures: 0; matrix warnings: 2.

| Step | Panels | Change of the matrix | $C_F$ | $C_{A0}$ |
|---|---|---|---|---|
| 1 | 20234 |  | 37.182 | 90.577 |

## pcbcap, the film-free 0402

| Mesh refine | $C_F$ in the 8-mm box |
|---|---|
| 4.0 | 39.9413 |
| 2.83 | 39.8796 |
| 2.0 | 39.8394 |

Extrapolated in the mesh: 39.7651 fF, discretisation error 0.0744 fF; enclosure correction +2.3264 fF; with no ground nearby 42.0915 fF.

## pcbcap, the film-free 0402 in a uniform medium (every permittivity 1)

| Mesh refine | $C_F$ in the 8-mm box | $C_{A0}$ |
|---|---|---|
| 4.0 | 9.9129 | 25.3871 |
| 2.83 | 9.8974 | 25.3739 |
| 2.0 | 9.8875 | 25.3654 |

Extrapolated in the mesh: C_F 9.8701 +- 0.0174 fF, C_A0 25.3499 +- 0.0154 fF.

