# Exploratory check for Section 4.11.9 of the note, kept as the record: the first five SPICE pulses per board against the time-domain model on SPICE's node with the macromodel's 3.07 pF added; superseded by spice_board_pulses.py report, which sets each description on its own fit of the measured gain. It reads the first version of spice/results/board_pulses.json, which spice_board_pulses.py run has since replaced.
# Run from this folder.
import json, sys, math
import numpy as np
sys.path.insert(0, "..")
import tia_pulse_response as tp
sp = json.load(open("../../spice/results/board_pulses.json", encoding="utf-8"))
d = json.load(open("../../data/results/tia_pulse_response_opa846_1k5.json", encoding="utf-8"))
fr = d["fits"]["macromodel A_-"]["rational"]
rol = tp.RationalOpenLoop(fr["a0"], fr["f_p1_Hz"], fr["zeros_Hz"], fr["poles_Hz"], fr["tau_s"], fr["n_delay"], fr["note"])
sr_cal, _ = tp.calibrate_sr(rol)
P = sp["pulses"]
cx, cf = P["c_ext"], P["c_f"]
ct = cx + 3.07e-12
print(f"SPICE node: C_ext {cx*1e12:.3f} pF (C_T {ct*1e12:.3f} pF in the model), C_F {cf*1e12:.3f} pF; calibrated SR {sr_cal/1e6:.1f} V/us")
for tag, add in (("board", 0.0), ("second", 0.55e-12)):
    q = [r["q"] for r in P["runs"][tag]]
    for sr in (sr_cal, 625e6):
        t, vo, vn, x1, v_ov = tp.simulate(rol, 1500.0, ct, cf + add, sr, 3.3, q, window=45e-9, dt=2e-12)
        for k, r in enumerate(P["runs"][tag]):
            ts, vs = np.array(r["t"]), np.array(r["vo"])
            ms = tp.response_metrics(ts[ts >= 0], vs[ts >= 0], r["q"])
            mm = tp.response_metrics(t, vo[k], r["q"])
            if sr == sr_cal or k in (2, 3, 4):
                print(f"  {tag:6s} SR {sr/1e6:5.0f}: Q {r['q']*1e12:5.2f} pC | SPICE peak {ms['v_peak']:+.3f} V at {ms['t_peak']*1e9:.2f} ns, ring {ms['f_ring']/1e6:6.1f} MHz tau {ms['tau_decay']*1e9:5.2f} ns, 1% {ms['t_settle_1pct']*1e9:5.1f} ns, area/Q {ms['area_over_q']:6.0f}, max|vn| {np.max(np.abs(r['vn']))*1e3:6.1f} mV"
                      f" | model peak {mm['v_peak']:+.3f} V at {mm['t_peak']*1e9:.2f} ns, ring {mm['f_ring']/1e6:6.1f} MHz tau {mm['tau_decay']*1e9:5.2f} ns, 1% {mm['t_settle_1pct']*1e9:5.1f} ns, area/Q {mm['area_over_q']:6.0f}, max|vn| {np.max(np.abs(vn[k]))*1e3:6.1f} mV")
