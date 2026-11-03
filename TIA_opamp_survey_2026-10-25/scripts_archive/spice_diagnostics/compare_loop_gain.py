"""Compare the Middlebrook loop gain from SPICE with A/NG built from the macromodel's own
open-loop curve (driven at the non-inverting input), for one design, at a list of frequencies.
This is the comparison that showed the two agree to 2 GHz and part above it (Section 10.4).

Usage:  python compare_loop_gain.py <scripts_archive> <spice folder> <part> <R_F> <C_D> <C_F>
        e.g. python compare_loop_gain.py .. ../../spice OPA855 2000 1e-12 0.25e-12
Needs the results of spice_tia_checks.py aol, params and loop.
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, sys.argv[1])
import tia_model as tm
from spice_tia_checks import TableOpenLoop, tag, C_PCB_NOM

spice = Path(sys.argv[2])
part, R_F, C_D, C_F = sys.argv[3], float(sys.argv[4]), float(sys.argv[5]), float(sys.argv[6])
params = json.loads((spice / "results" / "params.json").read_text())
a = np.load(spice / "runs" / "aol" / part / "aol.npy")
ol = TableOpenLoop(a[0], a[1] + 1j * a[2])
C_T = C_D + C_PCB_NOM + params[part]["c_in_grounded_pF"]["100MHz"] * 1e-12
L = np.load(spice / "runs" / "loop" / tag(part, R_F, C_D, C_F) / "loop.npy")
f = L[0]
T = L[1] + 1j * L[2]
Tv = L[3] + 1j * L[4]
_, NG, Ta = tm.tia_tf(f, ol, R_F, C_T, C_F)


def ph(z):
    return np.degrees(np.unwrap(np.angle(z)))


for x in (1e7, 1e8, 3e8, 6e8, 1e9, 1.5e9, 2e9, 3e9, 4e9, 5e9, 6e9, 8e9, 1e10):
    i = np.argmin(abs(f - x))
    print(f"{x/1e9:6.2f} GHz | SPICE T {20*np.log10(abs(T[i])):7.2f} dB {ph(T)[i]:8.1f} deg | "
          f"A/NG {20*np.log10(abs(Ta[i])):7.2f} dB {ph(Ta)[i]:8.1f} deg | T_v only {20*np.log10(abs(Tv[i])):7.2f} dB {ph(Tv)[i]:8.1f}")
