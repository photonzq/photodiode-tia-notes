# FastHenry runs of the side note on copper thickness

These are the results of `scripts_archive/fasthenry_traces.py`; its docstring explains every model. "DC" is 1 kHz with one filament (a uniform current); at 308 MHz each trace is cut into n_w x n_h filaments across its width and thickness, ratio 2. The skin depth of copper (rho = 1.7e-8 ohm m) is 3.74 um at 308 MHz. Inductances in nH, resistances in mOhm.

## All runs

| Group | Copper (um) | Length (mm) | Plane | Frequency | Filaments | L (nH) | R (mOhm) | Time (s) |
|---|---|---|---|---|---|---|---|---|
| alone | 1 | 2.8 | - | DC | 1 x 1 | 2.1563 | 238.000 | 0.2 |
| alone | 1 | 2.8 | - | 308 MHz | 13 x 1 | 2.1203 | 284.881 | 0.2 |
| alone | 17.5 | 2.8 | - | DC | 1 x 1 | 2.1113 | 13.600 | 0.2 |
| alone | 17.5 | 2.8 | - | 308 MHz | 9 x 5 | 2.0336 | 43.906 | 0.2 |
| alone | 17.5 | 2.8 | - | 308 MHz | 13 x 7 | 2.0329 | 45.076 | 0.2 |
| alone | 35 | 2.8 | - | DC | 1 x 1 | 2.0681 | 6.800 | 0.2 |
| alone | 35 | 2.8 | - | 308 MHz | 9 x 5 | 1.9692 | 36.871 | 0.2 |
| alone | 35 | 2.8 | - | 308 MHz | 13 x 7 | 1.9682 | 38.152 | 0.4 |
| alone | 70 | 2.8 | - | DC | 1 x 1 | 1.9915 | 3.400 | 0.2 |
| alone | 70 | 2.8 | - | 308 MHz | 9 x 5 | 1.8720 | 25.673 | 0.2 |
| alone | 70 | 2.8 | - | 308 MHz | 13 x 7 | 1.8702 | 29.966 | 0.2 |
| plane | 17.5 | 3 | standard | 308 MHz | 13 x 7 | 1.1977 | 70.715 | 2.0 |
| plane | 17.5 | 6 | standard | 308 MHz | 13 x 7 | 2.4215 | 138.445 | 2.4 |
| plane | 35 | 3 | standard | 308 MHz | 13 x 7 | 1.1492 | 63.212 | 2.2 |
| plane | 35 | 6 | standard | 308 MHz | 13 x 7 | 2.3245 | 123.423 | 2.4 |
| plane | 70 | 3 | standard | 308 MHz | 13 x 7 | 1.0814 | 54.156 | 2.0 |
| plane | 70 | 6 | standard | 308 MHz | 13 x 7 | 2.1890 | 105.247 | 2.0 |
| plane | 1 | 3 | standard | 308 MHz | 13 x 1 | 1.2682 | 324.896 | 1.0 |
| plane | 1 | 6 | standard | 308 MHz | 13 x 1 | 2.5628 | 647.801 | 1.0 |
| plane | 17.5 | 3 | standard | DC | 1 x 1 | 1.5806 | 26.845 | 0.6 |
| plane | 17.5 | 6 | standard | DC | 1 x 1 | 3.2858 | 47.741 | 0.6 |
| plane | 35 | 3 | standard | DC | 1 x 1 | 1.5435 | 19.560 | 0.8 |
| plane | 35 | 6 | standard | DC | 1 x 1 | 3.2094 | 33.170 | 0.6 |
| plane | 70 | 3 | standard | DC | 1 x 1 | 1.4793 | 15.917 | 0.8 |
| plane | 70 | 6 | standard | DC | 1 x 1 | 3.0770 | 25.884 | 0.6 |
| plane | 35 | 3 | coarse | 308 MHz | 13 x 7 | 1.1490 | 63.227 | 1.2 |
| plane | 35 | 6 | coarse | 308 MHz | 13 x 7 | 2.3243 | 123.495 | 1.0 |
| plane | 35 | 3 | wide | 308 MHz | 13 x 7 | 1.1481 | 63.023 | 4.0 |
| plane | 35 | 6 | wide | 308 MHz | 13 x 7 | 2.3210 | 122.865 | 4.8 |

## Inductance per unit length over the plane

L' = (L(6 mm) - L(3 mm)) / 3 mm, the loop inductance per unit length without the ends.

| Copper (um) | Plane | Frequency | Filaments | L' (nH/mm) | R' (mOhm/mm) |
|---|---|---|---|---|---|
| 1 | standard | 308 MHz | 13 x 1 | 0.43153 | 107.635 |
| 17.5 | standard | DC | 1 x 1 | 0.56839 | 6.965 |
| 17.5 | standard | 308 MHz | 13 x 7 | 0.40791 | 22.577 |
| 35 | standard | DC | 1 x 1 | 0.55533 | 4.537 |
| 35 | coarse | 308 MHz | 13 x 7 | 0.39177 | 20.089 |
| 35 | standard | 308 MHz | 13 x 7 | 0.39176 | 20.070 |
| 35 | wide | 308 MHz | 13 x 7 | 0.39099 | 19.947 |
| 70 | standard | DC | 1 x 1 | 0.53256 | 3.322 |
| 70 | standard | 308 MHz | 13 x 7 | 0.36921 | 17.030 |
