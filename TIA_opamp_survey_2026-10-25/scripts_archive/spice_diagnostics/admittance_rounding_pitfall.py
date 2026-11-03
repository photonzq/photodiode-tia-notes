"""Input admittance of the inverting input measured with a 1-kF DC-feed capacitor and a 1-GH
DC-feed inductor, as first tried.  It demonstrates the rounding pitfall of Section 10.2: the
capacitor's admittance (about 6e11 S at 100 MHz) makes the small input current a difference
of huge numbers, so the imaginary part of i(Vt) comes out in steps of about 2^-11 A and the
capacitance is wrong.  The 'params' check of spice_tia_checks.py uses 1 mH / 1 uF instead and
takes the pin current from the simulated node voltages (Eq. (49)).

Usage:  python admittance_rounding_pitfall.py <scripts_archive> <spice folder> <part> <work folder>
"""
import shutil
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, sys.argv[1])
from ngspice_shared import NgSpice
from spice_tia_checks import VENDOR_MODELS, amp, header, read_wrdata, run, write_deck

spice, part, work = Path(sys.argv[2]), sys.argv[3], Path(sys.argv[4])
shutil.copytree(spice / "runs" / "_models", work / "_models", dirs_exist_ok=True)
m = VENDOR_MODELS[part]
ng = NgSpice()
for mode in ("free", "grounded"):
    folder = work / "x" / f"{part}_yin_{mode}"
    deck = header(part, "input admittance with 1 kF / 1 GH", m["vs_tia"]) + amp(part, "0", "inm", "out") + (
        f"LB out inm 1G\nCB inm x 1k\nVt x 0 DC 0 AC 1\nRL out 0 {m['rl']}\n" + ("CO out 0 1\n" if mode == "grounded" else "")
        + ".control\nset wr_singlescale\nset wr_vecnames\nac dec 50 10Meg 30G\nwrdata yin.txt real(i(vt)) imag(i(vt))\n.endc\n.end\n")
    log, err = run(ng, write_deck(folder, deck))
    d = read_wrdata(folder / "yin.txt")
    f = d[:, 0]
    Y = -(d[:, 1] + 1j * d[:, 2])
    print(f"output {mode}: errors {err[:1]}")
    for x in (1e8, 5e8, 1e9, 2e9, 3e9, 5e9, 1e10):
        i = np.argmin(abs(f - x))
        print(f"  {x/1e9:5.2f} GHz: imag(i(Vt)) = {-d[i, 2]:.8e} A, C = {Y[i].imag/(2*np.pi*f[i])*1e12:6.3f} pF")
