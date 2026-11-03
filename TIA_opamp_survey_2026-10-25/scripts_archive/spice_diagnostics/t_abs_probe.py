"""Johnson noise of a 1-kOhm resistor whose model sets PSpice's T_ABS, in ngspice with
ngbehavior=psa, at .temp 25 and .temp 75: is T_ABS read as an absolute temperature?
Result with ngspice-46 (Section 10.2): T_ABS = x gives the noise of (27 + x) degC whatever
.temp is, so T_ABS = -273.15 gives 27.0 K instead of 0 K; noisy=0 gives none.

Usage:  python t_abs_probe.py <scripts_archive> <work folder>
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, sys.argv[1])
from ngspice_shared import NgSpice

work = Path(sys.argv[2])
work.mkdir(parents=True, exist_ok=True)
ng = NgSpice()
KB = 1.380649e-23
for circuit_t in (25, 75):
    for model in ("t_abs=-273.15", "t_abs=0", "t_abs=100", "noisy=0", ""):
        deck = (f"* T_ABS probe\n.temp {circuit_t}\nV1 a 0 DC 0 AC 1\nR1 a b rt 1k\nRL b 0 rq 1G\n"
                f".model rt res({model})\n.model rq res(noisy=0)\n"
                ".control\nset wr_singlescale\nset wr_vecnames\nnoise v(b) V1 lin 1 1Meg 1Meg\n"
                "setplot noise1\nwrdata out.txt onoise_spectrum\n.endc\n.end\n")
        (work / "deck.cir").write_text(deck)
        ng.run_deck(work / "deck.cir")
        d = np.loadtxt(work / "out.txt", skiprows=1, ndmin=2)
        v = d[0, 1]
        T = v ** 2 / (4 * KB * 1e3)
        print(f".temp {circuit_t} C, model res({model or 'default'}): {v*1e9:.3f} nV/rtHz -> {T:.1f} K ({T-273.15:.1f} C)")
