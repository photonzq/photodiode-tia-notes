# Exploratory check for Section 4.11.9 of the note, kept as the record: Tests 1 and 2 of the slew-rate limit at four internal slew rates on both rational open loops, before the calibration; superseded by tia_pulse_response.note_cases (Table 4.9).
# Run from this folder.
import json, sys
sys.path.insert(0, "..")
import tia_pulse_response as tp
d = json.load(open("../../data/results/tia_pulse_response_opa846_1k5.json", encoding="utf-8"))
for name, fr in d["fits"].items():
    r = fr["rational"]
    rol = tp.RationalOpenLoop(r["a0"], r["f_p1_Hz"], r["zeros_Hz"], r["poles_Hz"], r["tau_s"], r["n_delay"], r["note"])
    t1 = tp.open_loop_slew_check(rol, 625e6)
    print(f"{name}: Test 1, open loop, v_d = 0.5 V: ramp {t1['ramp_slope'] / 1e6:.3f} V/us against SR 625 (error {100 * t1['rel_error']:+.4f} %), steepest {t1['steepest'] / 1e6:.1f} V/us, V_ov {t1['v_ov'] * 1e3:.1f} mV")
    rows = tp.g10_step_test(rol, [500e6, 625e6, 750e6, 1000e6])
    for s, rr in zip([500, 625, 750, 1000], rows):
        print(f"   Test 2, G = +10, {rr['step']:.3f}-V step, internal SR {s} V/us: 10-90 % {rr['avg_10_90'] / 1e6:.1f}, 20-80 % {rr['avg_20_80'] / 1e6:.1f}, steepest {rr['steepest'] / 1e6:.1f} V/us")
    for tgt in (625e6, 500e6):
        for key in ("avg_10_90", "avg_20_80"):
            s, _ = tp.calibrate_sr(rol, target=tgt, key=key)
            print(f"   calibrated: {key} = {tgt / 1e6:.0f} V/us needs internal SR {s / 1e6:.1f} V/us")
