# Exploratory check for Section 4.11.9 of the note, kept as the record: the macromodel's internal nodes (pin, base, tail, collector loads, integrating node, output) during three pulses on the board; superseded by the probe step of spice_board_pulses.py.
# Run from this folder.
"""Scratch: the macromodel's internal nodes during a large pulse on the board's node (SPICE's own fit).

Nodes of OPA846.LIB: 2 = Q2's base (behind L_L1 = 2.35 nH from the inverting pin), 15 = the tail (5 ohm to each
emitter, 1.475 mA to V-), 11 and 12 = the collectors (200 ohm each to node 10 = V+ - 1.4 V), 17 = the integrating
node (G_G3 = 30.51 mS x V(12,11) into 7.95 pF || 503 kohm), 18 = its unity-gain copy (1 kohm || 80 fF, clamped near
the rails), 23 = the output stage before R_R18 = 5 ohm.  Collector currents from the loads: I_C = (V10 - V1x)/200.
"""
import sys
from pathlib import Path

import numpy as np

ARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ARCH))
from ngspice_shared import NgSpice  # noqa: E402
from spice_tia_checks import header, prepared_model, read_wrdata, run, tia_body, write_deck  # noqa: E402

SPICE = ARCH.parent / "spice"
ng = NgSpice(None)
prepared_model("OPA846", SPICE)
NODES = ["oa", "inm", "xu1.2", "xu1.15", "xu1.10", "xu1.11", "xu1.12", "xu1.17", "xu1.18", "xu1.23"]
for q in (0.7e-12, 2e-12, 7e-12):
    i_pk = q / 30e-12
    folder = SPICE / "runs" / "board_pulses" / f"probe_Q{q * 1e12:.1f}p".replace(".", "p")
    deck = header("OPA846", f"probe {q * 1e12:g} pC", 5.0) + tia_body(
        "OPA846", 1500.0, 4.10e-12, 0.29e-12, 100.0, iph=f"Iph 0 inm PULSE(0 {i_pk:.6e} 2n 10p 10p 20p 1)") + (
        ".control\nset wr_singlescale\nset wr_vecnames\ntran 1p 12n 0 1p\nlinearize " + " ".join(f"v({n})" for n in NODES)
        + "\nwrdata probe.txt " + " ".join(f"v({n})" for n in NODES) + "\n.endc\n.end\n")
    log, err = run(ng, write_deck(folder, deck))
    d = read_wrdata(folder / "probe.txt")
    t = d[:, 0] - 2.02e-9
    v = {n: d[:, 1 + k] for k, n in enumerate(NODES)}
    pre = (t > -1e-9) & (t < -0.05e-9)
    base = {n: float(np.mean(v[n][pre])) for n in NODES}
    ic1 = (v["xu1.10"] - v["xu1.11"]) / 200
    ic2 = (v["xu1.10"] - v["xu1.12"]) / 200
    i17 = 30.51e-3 * (v["xu1.12"] - v["xu1.11"])
    print(f"\n=== Q {q * 1e12:g} pC; before the pulse: I_C1 {ic1[pre].mean() * 1e3:.3f} mA, I_C2 {ic2[pre].mean() * 1e3:.3f} mA, "
          f"V17 {base['xu1.17']:+.3f} V, V18 {base['xu1.18']:+.3f}, out {base['oa']:+.3f}")
    for tt in (0.0, 0.01, 0.02, 0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.6, 0.8, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0):
        k = int(np.argmin(np.abs(t - tt * 1e-9)))
        s17 = np.gradient(v["xu1.17"], t)[k]
        so = np.gradient(v["oa"], t)[k]
        print(f"  t {tt:4.2f} ns: v_n {1e3 * (v['inm'][k] - base['inm']):7.1f} mV, base(2) {1e3 * (v['xu1.2'][k] - base['xu1.2']):7.1f} mV, "
              f"tail(15) {v['xu1.15'][k]:+.3f} V, I_C1 {ic1[k] * 1e3:7.3f} mA, I_C2 {ic2[k] * 1e3:7.3f} mA, "
              f"i into 17 {i17[k] * 1e3:8.2f} mA (= {i17[k] / 7.95e-12 / 1e6:7.0f} V/us), dV17/dt {s17 / 1e6:7.0f}, "
              f"V17 {v['xu1.17'][k] - base['xu1.17']:+.3f}, V18 {v['xu1.18'][k] - base['xu1.18']:+.3f}, "
              f"out {v['oa'][k] - base['oa']:+.3f} V, dvo/dt {so / 1e6:7.0f} V/us, gain out/18 "
              f"{(v['oa'][k] - base['oa']) / (v['xu1.18'][k] - base['xu1.18'] + 1e-12):.3f}")
