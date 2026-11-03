"""Open-loop gain driven at the inverting input (non-inverting input grounded) against the gain
driven at the non-inverting input, and the TIA loop gain rebuilt from it with the measured
input admittance and output impedance (Eq. (52)).  This is the diagnosis that the remaining
gain-margin difference came from the two inputs' different gains above 1 GHz (Section 10.4);
the 'aol' and 'consistency' checks of spice_tia_checks.py now do the same.

Usage:  python aol_inverting_input.py <scripts_archive> <spice folder> <work folder> <part> [<part> ...]
Needs the results of spice_tia_checks.py aol, params and loop.
"""
import shutil
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, sys.argv[1])
from ngspice_shared import NgSpice
from spice_tia_checks import (C_PCB_NOM, DESIGNS, VENDOR_MODELS, TableOpenLoop, amp, header, loop_metrics_from_T,
                              read_wrdata, run, tag, write_deck)

spice, work = Path(sys.argv[2]), Path(sys.argv[3])
shutil.copytree(spice / "runs" / "_models", work / "_models", dirs_exist_ok=True)
ng = NgSpice()


def on(z, fl):
    return np.interp(np.log10(fl), np.log10(z[0]), z[1]) + 1j * np.interp(np.log10(fl), np.log10(z[0]), z[2])


for part in sys.argv[4:]:
    m = VENDOR_MODELS[part]
    folder = work / "x" / f"{part}_aol_inv"
    deck = header(part, "open-loop gain from the inverting input", m["vs_aol"]) + amp(part, "0", "inm", "out") + (
        f"Vn x 0 DC 0 AC 1\nCB inm x 1u\nLB out inm 1m\nRL out 0 {m['rl']}\n"
        ".control\nset wr_singlescale\nset wr_vecnames\nac dec 50 100k 30G\n"
        "wrdata aol.txt real(v(out)) imag(v(out)) real(v(inm)) imag(v(inm))\n.endc\n.end\n")
    log, err = run(ng, write_deck(folder, deck))
    d = read_wrdata(folder / "aol.txt")
    f = d[:, 0]
    A_inv = -(d[:, 1] + 1j * d[:, 2]) / (d[:, 3] + 1j * d[:, 4])
    a = np.load(spice / "runs" / "aol" / part / "aol.npy")
    ol = TableOpenLoop(a[0], a[1] + 1j * a[2])
    print(part, err[:1])
    for x in (1e7, 1e8, 1e9, 2e9, 3e9, 4e9, 5e9, 7e9):
        i = np.argmin(abs(f - x))
        An = ol.A(np.array([f[i]]))[0]
        print(f"  {x/1e9:5.2f} GHz: A(IN-) {20*np.log10(abs(A_inv[i])):6.2f} dB {np.degrees(np.angle(A_inv[i])):7.1f} deg | "
              f"A(IN+) {20*np.log10(abs(An)):6.2f} dB {np.degrees(np.angle(An)):7.1f} deg")
    ol_i = TableOpenLoop(f, A_inv)
    for dpart, R_F, C_D, C_F, label in DESIGNS:
        if dpart != part:
            continue
        lp = np.load(spice / "runs" / "loop" / tag(part, R_F, C_D, C_F) / "loop.npy")
        fl = lp[0]
        s = 2j * np.pi * fl
        Yin = on(np.load(spice / "runs" / "params" / f"{part}_yin_grounded.npy"), fl)
        Zo = on(np.load(spice / "runs" / "params" / f"{part}_zout.npy"), fl)
        Y_node = s * (C_D + C_PCB_NOM) + Yin
        Z_F = R_F / (1 + s * R_F * C_F)
        RL = m["rl"]
        Z_L = 1 / (1 / RL + 1 / (Z_F + 1 / Y_node))
        T = ol_i.A(fl) / (1 + Z_F * Y_node) * (RL + Zo) / RL * Z_L / (Z_L + Zo)
        r = loop_metrics_from_T(fl, T)
        r2 = loop_metrics_from_T(fl, lp[1] + 1j * lp[2])
        print(f"  {label}: A(IN-) with Z_o: PM {r['pm_deg']:.1f}, GM {r['gm_dB']:.1f} dB, f_c {r['f_c_MHz']:.0f} | "
              f"SPICE PM {r2['pm_deg']:.1f}, GM {r2['gm_dB']:.1f} dB, f_c {r2['f_c_MHz']:.0f}")
