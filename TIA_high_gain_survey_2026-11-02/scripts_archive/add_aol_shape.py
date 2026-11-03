"""Edit of 2 November 2026: add to data/amplifiers.json the shape of an amplifier's open-loop
gain beyond a single pole, taken from its TI PSpice model as simulated by
hg_spice_gbw_check.py (spice/runs/<part>/aol/aol.npy).  Used for OPA1656 (SBOMAW6, Rev. C)
and OPA2156 (SBOMAR0, Rev. B).

The shape is H(f) = A_model(f) / A_1(f), where A_model is the macromodel's open-loop gain and
A_1 a single pole with the macromodel's own DC gain and its gain-bandwidth at 1 kHz.  H is
1 at low frequency; above a few hundred kilohertz it carries the macromodel's extra roll-off
and phase lag.  hg_model multiplies the single pole of the data sheet by H.

Usage:  python add_aol_shape.py [PART]      (default: OPA1656)
"""
import json
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
PATH = ROOT / "data" / "amplifiers.json"
PART = sys.argv[1] if len(sys.argv) > 1 else "OPA1656"
MODEL = {"OPA1656": "SBOMAW6 Rev. C", "OPA2156": "SBOMAR0 Rev. B"}

f, mag, ph = np.load(ROOT / "spice" / "runs" / PART.lower() / "aol" / "aol.npy")
a = mag * np.exp(1j * np.radians(ph))
a0 = mag[0]
gbw = float(np.exp(np.interp(math.log(1e3), np.log(f), np.log(mag)))) * 1e3
a1 = a0 / (1.0 + 1j * f * a0 / gbw)
h = a / a1
pts = []
for fx in np.logspace(3, 8, 26):
    hx = complex(np.interp(math.log(fx), np.log(f), h.real) + 1j * np.interp(math.log(fx), np.log(f), h.imag))
    pts.append([float(f"{fx:.4g}"), round(abs(hx), 4), round(math.degrees(math.atan2(hx.imag, hx.real)), 2)])

data = json.loads(PATH.read_text(encoding="utf-8"))
part = data["parts"][PART]
part["aol_shape"] = pts
part["aol_shape_note"] = (f"Open-loop gain beyond a single pole, H(f) = A/A_1, from TI's PSpice model {MODEL[PART]} "
                          f"(DC gain {20 * math.log10(a0):.1f} dB, {gbw / 1e6:.1f} MHz at 1 kHz); "
                          "rows are f in Hz, |H|, phase of H in degrees (add_aol_shape.py).")
with open(PATH, "w", encoding="utf-8", newline="\n") as fh:
    json.dump(data, fh, indent=1, ensure_ascii=False)
for p in pts:
    if abs(math.log10(p[0]) % 1) < 1e-6:
        print(PART, p)
