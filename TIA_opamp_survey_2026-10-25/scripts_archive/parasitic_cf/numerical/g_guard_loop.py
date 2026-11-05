"""The guarded feedback networks inside a transimpedance loop: how much does the amplifier matter?

Usage:  python g_guard_loop.py [--out <json>]          (no solve; reads guard_ladder.json)

Why this script exists
----------------------
g_guard_ladder.py gives the feedback network's own response, -Z_F = -1 / y_F, which is the
transimpedance with an ideal amplifier.  With an amplifier of open-loop gain A, Kirchhoff's current
law at the summing node (voltage v_-) reads: the photocurrent I enters; the network delivers y_F v_o
and draws y_11 v_- (pcbcap.distributed, Eqs. (5) and (6)); the photodiode and the amplifier's input
draw Y_D v_-.  With v_o = -A v_-, I + y_F v_o + (Y_D + y_11) v_o / A = 0, so

    Z_T = v_o / I = -1 / (y_F + Y_n / A),     Y_n = Y_D + y_11,                                  (1)

the two-port form of the high-gain note's Eq. (6).  The loop gain is T = A y_F / Y_n, and
Z_T = -Z_F T / (1 + T): where |T| >> 1 the network alone sets the response, and near the loop's
crossover (|T| = 1) the amplifier shares it.  The network enters through y_F, which shapes Z_F, and
through y_11, part of Y_n.

What is evaluated.  Each layout of g_guard_ladder.py, with the amplifier it was drawn for, on the
high-gain note's 20-pF photodiode (S1336-18BK, 20 pF and a 2-GOhm shunt, its Table 1), at
R_F = 1, 10 and 100 GOhm, in three versions:
  (a) the network as computed, with the film in ten elements;
  (b) the lumped first-order network, y_F = 1/R_F + j w C_F and y_11 = 1/R_F + j w (C_F + C_B0),
      where C_B0 is the first-order capacitance of the summing node's end to ground from the same
      matrix (pcbcap.distributed.ladder: C_lo0 or C_hi0), so that (a) and (b) agree at low frequency;
  (c) the network with an ideal amplifier, Z_T = -Z_F.
Each is evaluated as it stands and with an ideal external capacitor across the resistor, of the size
that makes the first-order total equal to the maximally flat value of the high-gain note's
Eq. (18), C = sqrt((C_T + C) / (pi R_F GBW)), with C_T = C_D + C_in + C_B0; the equation is solved
by fixed-point iteration, and no capacitor is added where the network alone already exceeds it.
The amplifier is an integrator, A = 2 pi GBW / (j w), as in the high-gain note's Eq. (17); the DC
gains of these parts (111-143 dB) matter only below GBW / A_0, at most about 50 Hz, and are left out.

Amplifiers, from the high-gain note's Table A.1: ADA4530-1 2 MHz with 8 pF of input capacitance;
LMP7721 17 MHz and LMC6001 1.3 MHz, each with the 8 pF that note assumes because their data sheets
give no input capacitance (its Appendix C, item 5).

Reported for each case: the -3-dB frequency of |Z_T| relative to its DC value, the largest rise of
|Z_T| above that value (dB) and its frequency, and the loop's crossover frequency and phase margin
(180 deg + arg T where |T| = 1).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[4] / "pcbcap"))

import numpy as np                                         # noqa: E402

from pcbcap import distributed as dist                    # noqa: E402

DATA = HERE.parents[3] / "data" / "parasitic_cf" / "numerical"
C_D, R_SH = 20e-12, 2e9                    # S1336-18BK (high-gain note, Table 1)
AMPS = {"ada4530_so8_1206": ("ADA4530-1", 2e6, 8e-12),
        "lmp7721_so8_1206": ("LMP7721", 17e6, 8e-12),
        "lmc6001_dip8_bottom_guard_1206": ("LMC6001", 1.3e6, 8e-12),
        "lmc6001_dip8_bottom_1206": ("LMC6001", 1.3e6, 8e-12)}
R_VALUES = (1e9, 1e10, 1e11)


def flat_capacitance(c_t: float, r: float, gbw: float) -> float:
    """C = sqrt((C_T + C) / (pi R GBW)), the high-gain note's Eq. (18), by fixed-point iteration."""
    c = np.sqrt(c_t / (np.pi * r * gbw))
    for _ in range(50):
        c = np.sqrt((c_t + c) / (np.pi * r * gbw))
    return float(c)


def metrics(f, zt, loop):
    """-3-dB frequency and largest rise of |Z_T| relative to its value at the lowest frequency, and the
    crossover and phase margin of the loop gain."""
    mag = np.abs(zt) / abs(zt[0])
    k = int(np.argmax(mag < 1 / np.sqrt(2)))
    f3 = float(np.exp(np.interp(np.log(1 / np.sqrt(2)), np.log(mag[[k, k - 1]]), np.log(f[[k, k - 1]]))))
    kp = int(np.argmax(mag))
    a = np.abs(loop)
    kc = int(np.argmax(a < 1.0))
    fc = float(np.exp(np.interp(0.0, np.log(a[[kc, kc - 1]]), np.log(f[[kc, kc - 1]]))))
    pm = float(180.0 + np.degrees(np.angle(np.interp(np.log(fc), np.log(f), loop.real)
                                           + 1j * np.interp(np.log(fc), np.log(f), loop.imag))))
    return dict(f3dB=f3, rise_dB=float(20 * np.log10(mag[kp])), f_rise=float(f[kp]), f_cross=fc, pm_deg=pm)


def evaluate(record: dict, name: str, r: float) -> dict:
    C = np.array(record["C"])
    end = record["output_end"]
    cf = record["C_F_dc"] * 1e-15
    cb0 = (record["C_hi0"] if end == "lo" else record["C_lo0"]) * 1e-15     # the summing node's end
    amp, gbw, c_in = AMPS[name]
    c_t = C_D + c_in + cb0
    c_flat = flat_capacitance(c_t, r, gbw)
    c_ext = max(0.0, c_flat - cf)
    f = np.logspace(0, 7, 1401)
    w = 2 * np.pi * f
    A = 2 * np.pi * gbw / (1j * w)
    y_d = 1 / R_SH + 1j * w * (C_D + c_in)
    out = dict(amplifier=amp, GBW=gbw, C_T=c_t, C_F=cf, C_flat=c_flat, C_ext=c_ext)
    for label, ce in (("as built", 0.0), ("flat", c_ext)):
        yf_d = dist.feedback_admittance(C, r, f, output_end=end) + 1j * w * ce
        y11_d = dist.input_admittance(C, r, f, output_end=end) + 1j * w * ce
        yf_l = 1 / r + 1j * w * (cf + ce)
        y11_l = 1 / r + 1j * w * (cf + cb0 + ce)
        res = {}
        for kind, yf, y11 in (("distributed", yf_d, y11_d), ("lumped", yf_l, y11_l)):
            yn = y_d + y11
            res[kind] = metrics(f, -1 / (yf + yn / A), A * yf / yn)
        zf = -1 / yf_d
        res["ideal amplifier"] = metrics(f, zf, 1e12 * np.ones_like(f) * np.exp(-1j * np.pi / 2))
        out[label] = res
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    data = json.loads((DATA / "guard_ladder.json").read_text(encoding="utf-8"))
    out = {}
    for r in R_VALUES:
        for name in AMPS:
            o = evaluate(data[name], name, r)
            out[f"{name} @ {r:.0e}"] = o
            print(f"{name}, {o['amplifier']} ({o['GBW'] / 1e6:g} MHz), R_F = {r / 1e9:g} GOhm: C_T {o['C_T'] * 1e12:.2f} pF, "
                  f"C_F {o['C_F'] * 1e15:.1f} fF, flat C {o['C_flat'] * 1e15:.1f} fF, external C {o['C_ext'] * 1e15:.1f} fF")
            for label in ("as built", "flat"):
                parts = []
                for kind in ("distributed", "lumped", "ideal amplifier"):
                    m = o[label][kind]
                    pm = "" if kind == "ideal amplifier" else f", crossover {m['f_cross']:.3g} Hz, PM {m['pm_deg']:.0f} deg"
                    parts.append(f"{kind}: f3 {m['f3dB']:.4g} Hz, rise {m['rise_dB']:.2f} dB{pm}")
                print(f"   {label:9s} " + " | ".join(parts))
    if a.out:
        Path(a.out).write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
        print("wrote", Path(a.out).name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
