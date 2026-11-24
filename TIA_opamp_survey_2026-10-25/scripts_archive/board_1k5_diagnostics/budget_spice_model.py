# Exploratory check for Section 4.11.9 of the note, kept as the record: where a pulse's charge has gone by the output's peak, in SPICE and in the model: the share that the node's own voltage drives through R_F came out the same in both, which pointed to the input stage. It reads the first version of spice/results/board_pulses.json.
# Run from this folder.
"""Scratch: where the charge of a large pulse goes, in SPICE and in the time-domain model, on the same node.

At the time of the output's peak, Kirchhoff at the summing node integrated from before the pulse gives
    Q = C_F (v_n - v_o) + (1/R_F) int (v_n - v_o) dt + [charge still on the node's own capacitance]
with v_n, v_o relative to their values before the pulse.  The node's own capacitance is C_ext + the amplifier's input
in SPICE (the input part is nonlinear and partly behind 2.35 nH), and C_T in the model.  The term (1/R_F) int v_n dt
is the charge the node's own voltage pushes through R_F, which shortens the slew; the slopes are printed too.
"""
import json
import sys
from pathlib import Path

import numpy as np

ARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ARCH))
import tia_pulse_response as tp  # noqa: E402

R_F = 1500.0
sp = json.loads((ARCH.parent / "spice" / "results" / "board_pulses.json").read_text(encoding="utf-8"))
d = json.loads((ARCH.parent / "data" / "results" / "tia_pulse_response_opa846_1k5.json").read_text(encoding="utf-8"))
fr = d["fits"]["macromodel A_-"]["rational"]
rol = tp.RationalOpenLoop(fr["a0"], fr["f_p1_Hz"], fr["zeros_Hz"], fr["poles_Hz"], fr["tau_s"], fr["n_delay"], fr["note"])
P = sp["pulses"]
cx, cf = P["c_ext"], P["c_f"]
ct = cx + 3.07e-12
SR_CAL = 686.5e6


def budget(t, vo, vn, q, c_node):
    i = int(np.argmax(np.abs(vo)))
    sel = slice(0, i + 1)
    q_cf = cf * (vn[i] - vo[i])
    q_rn = np.trapezoid(vn[sel], t[sel]) / R_F
    q_ro = -np.trapezoid(vo[sel], t[sel]) / R_F
    q_node = c_node * vn[i]
    slope = np.gradient(vo, t)
    # average slope from 10 to 90 % of the peak on the leading edge
    a = np.abs(vo[: i + 1])
    k10 = int(np.where(a >= 0.1 * a[-1])[0][0])
    k90 = int(np.where(a >= 0.9 * a[-1])[0][0])
    avg = 0.8 * a[-1] / (t[k90] - t[k10]) if k90 > k10 else float("nan")
    return dict(v_pk=vo[i], t_pk=t[i], q_cf=q_cf, q_rn=q_rn, q_ro=q_ro, q_node=q_node,
                rest=q - q_cf - q_rn - q_ro - q_node, steep=np.max(np.abs(slope[: i + 1])), avg=avg,
                vn_max=np.max(np.abs(vn)), t_delay=t[k10])


rows = []
for tag, add in (("board", 0.0),):
    runs = P["runs"][tag]
    qs = [r["q"] for r in runs]
    tm_, vo_m, vn_m, x1_m, v_ov = tp.simulate(rol, R_F, ct, cf + add, SR_CAL, 3.3, qs, window=20e-9, dt=1e-12, keep_every=2)
    for k, r in enumerate(runs):
        ts, vs, ns = np.array(r["t"]), np.array(r["vo"]), np.array(r["vn"])
        bs = budget(ts, vs, ns, r["q"], cx)
        bm = budget(tm_, vo_m[k], vn_m[k], r["q"], ct)
        for name, b in (("SPICE", bs), ("model", bm)):
            print(f"{tag} Q {r['q'] * 1e12:5.2f} pC {name:5s}: peak {b['v_pk']:+.3f} V at {b['t_pk'] * 1e9:5.2f} ns, 10 % at {b['t_delay'] * 1e9:5.2f} ns, "
                  f"slope 10-90 % of peak {b['avg'] / 1e6:6.0f}, steepest {b['steep'] / 1e6:6.0f} V/us, max v_n {b['vn_max'] * 1e3:6.1f} mV | "
                  f"of Q: C_F {b['q_cf'] / r['q'] * 100:5.1f} %, R_F by v_n {b['q_rn'] / r['q'] * 100:5.1f} %, R_F by v_o {b['q_ro'] / r['q'] * 100:5.1f} %, "
                  f"on C_node {b['q_node'] / r['q'] * 100:5.1f} %, rest {b['rest'] / r['q'] * 100:5.1f} %")
print(f"V_ov of the model at SR {SR_CAL / 1e6:.1f}: {v_ov * 1e3:.1f} mV")
