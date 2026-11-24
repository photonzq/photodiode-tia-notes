# Exploratory check for Section 4.11 of the note, kept as the record: the board's noise floor split into a white part at the node and one at the oscilloscope, with the capacitance free and band by band; superseded by compare_opa846_1k5_board.noise_section.
# Run from this folder.
"""Scratch: split the board's floor into input-side and output-side parts (exploration before the archived script)."""
import csv
import math
import sys
from pathlib import Path

import numpy as np

from pathlib import Path as _Path
HERE = _Path(__file__).resolve().parent
ARCH = HERE.parent
sys.path.insert(0, str(ARCH))
path = Path(str(ARCH.parent / "data" / "measurements" / "opa846_1k5_board_per_MHz.csv"))
rows = [r for r in csv.reader(l for l in open(path, encoding="utf-8") if not l.startswith("#"))]
ix = {k: i for i, k in enumerate(rows[0])}
d = rows[1:]


def col(k):
    return np.array([float(r[ix[k]]) if r[ix[k]] not in ("", "nan") else np.nan for r in d])


f = 0.5 * (col("f_low_MHz") + col("f_high_MHz")) * 1e6
G, s0, s0s, ssc, sscs = col("G_V_per_A"), col("S0_V2_per_Hz"), col("S0_sigma_V2_per_Hz"), col("S_scope_V2_per_Hz"), col("S_scope_sigma_V2_per_Hz")
bad = col("flagged") > 0
use = (~bad) & (f >= 25e6) & np.isfinite(G)
kT4 = 4 * 1.380649e-23 * 295
a0 = kT4 / 1500 + (2.8e-12) ** 2 + (1.2e-9 / 1500) ** 2
y = (s0 - ssc)[use]                      # TIA's output noise at the scope input, V^2/Hz
sig = np.sqrt(s0s ** 2 + sscs ** 2)[use]
g2 = G[use] ** 2
w = (1.2e-9 * 2 * math.pi * f[use]) ** 2
for label, cols in (("C only", [g2 * w]), ("C + input white", [g2 * w, g2]), ("C + output white", [g2 * w, np.ones_like(g2)]),
                    ("C + input white + output white", [g2 * w, g2, np.ones_like(g2)])):
    A = np.column_stack(cols)
    q, *_ = np.linalg.lstsq(A / sig[:, None], (y - g2 * a0) / sig, rcond=None)
    model = g2 * a0 + A @ q
    rr = (y - model) / y
    names = ["C^2", "w^2 (input)", "u^2 (output)"][:len(cols)] if label != "C + output white" else ["C^2", "u^2 (output)"]
    txt = []
    for n, v in zip(names, q):
        if n == "C^2":
            txt.append(f"C_tot {math.copysign(math.sqrt(abs(v)), v) * 1e12:.2f} pF")
        elif n.startswith("w"):
            txt.append(f"w {math.copysign(math.sqrt(abs(v)), v) * 1e12:.2f} pA/rtHz")
        else:
            txt.append(f"u {math.copysign(math.sqrt(abs(v)), v) * 1e9:.2f} nV/rtHz")
    print(f"{label:32s}: " + ", ".join(txt) + f"; rms rel residual {100 * np.sqrt(np.mean(rr ** 2)):.1f} %, chi2_red {np.sum(((y - model) / sig) ** 2) / (len(y) - len(cols)):.0f}")
# the excess at the output, bin by bin, with C_tot fixed at the gain fit's 6.47 pF
ex_out = y - g2 * (a0 + w * (6.47e-12) ** 2)
fu = f[use]
for lo, hi in ((25e6, 50e6), (50e6, 75e6), (75e6, 100e6), (100e6, 125e6), (125e6, 150e6), (150e6, 175e6), (175e6, 200e6)):
    m = (fu >= lo) & (fu < hi)
    e = np.mean(ex_out[m])
    gi = np.sqrt(np.mean(g2[m]))
    print(f"{lo / 1e6:3.0f}-{hi / 1e6:3.0f} MHz: excess at the scope {math.copysign(math.sqrt(abs(e)), e) * 1e9:+.2f} nV/rtHz, "
          f"input-referred {math.copysign(math.sqrt(abs(e)), e) / gi * 1e12:+.2f} pA/rtHz (G {gi:.0f} V/A); TIA out noise {math.sqrt(np.mean(y[m])) * 1e9:.2f} nV/rtHz")
