"""Time one transient tone run and read its harmonics, with and without tighter tolerances.
Used to set the resolution of the 'tone' check: 0.3 s per run, a numerical floor below
-138 dBc at 0.1 of full scale, and no change with reltol = 1e-5.

Usage:  python tone_probe.py <scripts_archive> <spice folder> <work folder> <part> <f0 in Hz> <peak current in A> [<.options text>]
        e.g. python tone_probe.py .. ../../spice ./work OPA855 100e6 0.08e-3 reltol=1e-5
"""
import shutil
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, sys.argv[1])
from ngspice_shared import NgSpice
from spice_tia_checks import C_PCB_NOM, VENDOR_MODELS, header, read_wrdata, run, tia_body, write_deck

spice, work = Path(sys.argv[2]), Path(sys.argv[3])
part, f0, ipk = sys.argv[4], float(sys.argv[5]), float(sys.argv[6])
opts = sys.argv[7] if len(sys.argv) > 7 else ""
shutil.copytree(spice / "runs" / "_models", work / "_models", dirs_exist_ok=True)
m = VENDOR_MODELS[part]
R_F, C_D, C_F = 2000.0, 1e-12, (0.25e-12 if part == "OPA855" else 0.55e-12)
ng = NgSpice()
period = 1 / f0
tstep, tstop = period / 256, 48 * period
folder = work / "x" / f"{part}_tone_probe"
deck = header(part, "tone probe", m["vs_tia"]) + tia_body(part, R_F, C_D + C_PCB_NOM, C_F, 1e6,
                                                         iph=f"Iph 0 inm SIN(0 {ipk:.6e} {f0:g})") + (
    (f".options {opts}\n" if opts else "")
    + f".control\nset wr_singlescale\nset wr_vecnames\ntran {tstep:.4e} {tstop:.4e} 0 {tstep:.4e}\n"
    "linearize v(oa)\nwrdata tone.txt v(oa)\n.endc\n.end\n")
t0 = time.time()
log, err = run(ng, write_deck(folder, deck))
dt = time.time() - t0
d = read_wrdata(folder / "tone.txt")
t, v = d[:, 0], d[:, 1]
sel = t >= tstop - 32 * period - tstep / 2
vv = v[sel][:32 * 256]
vv = vv - vv.mean()
spec = np.abs(np.fft.rfft(vv * np.hanning(len(vv))))
h = [spec[32 * k] for k in range(1, 6)]
print(f"{part} {f0/1e6:g} MHz, {ipk*1e3:.3f} mA pk, options '{opts}': {dt:.1f} s, n={len(vv)}, out {(vv.max()-vv.min())/2:.3f} V pk, "
      + ", ".join(f"HD{k+1} {20*np.log10(h[k]/h[0]):.1f}" for k in range(1, 5)) + f" dBc; errors {err[:1]}")
