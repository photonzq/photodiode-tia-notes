from pathlib import Path

p = Path(__file__).resolve().parents[1] / "hv_output_stage" / "scripts" / "hv_schematics.py"
s = p.read_text(encoding="utf-8")

start = s.index("    s = ss.Sheet()\n    y_t, y_b = 6.0, -6.0                          # +100 V and -100 V rails\n")
end = s.index("    s.save(out / \"schem_hv_stage\")\n")
new_body = '''    s = ss.Sheet()
    y_t, y_b = 5.5, -5.5                          # +100 V and -100 V rails

    # long-tailed pair: Q1 takes the feedback (base faces left), Q2 the signal (base faces right)
    q1 = s.npn((2.0, 0.0), name="Q1", side="right")
    q2 = s.npn((6.5, 0.0), mirror=True, name="Q2", side="left")
    y_tail = -2.0
    s.res(q1.emitter, (q1.emitter[0], y_tail), "1 kΩ", side="left")
    s.res(q2.emitter, (q2.emitter[0], y_tail), "1 kΩ", side="right")
    s.wire((q1.emitter[0], y_tail), (q2.emitter[0], y_tail))
    x_tail = 0.5 * (q1.emitter[0] + q2.emitter[0])
    s.dot((x_tail, y_tail))
    s.res((x_tail, y_tail), (x_tail, y_b), "200 kΩ", side="right")

    # PNP mirror above the pair: Q3 diode-connected above Q1, Q4 above Q2
    dx = q1.collector[0] - q1.base[0]             # base-to-collector offset of a transistor
    q3 = s.pnp((q1.collector[0] + dx, 3.0), mirror=True, name="Q3", side="left")
    q4 = s.pnp((q2.collector[0] - dx, 3.0), name="Q4", side="right")
    s.wire(q3.base, q4.base)
    x_m = q3.base[0] + 0.6
    s.dot((x_m, 3.0))
    s.wire((x_m, 3.0), (x_m, 2.2), (q3.collector[0], 2.2))
    s.dot((q3.collector[0], 2.2))
    s.wire(q3.collector, q1.collector)
    s.wire(q4.collector, q2.collector)
    s.res(q3.emitter, (q3.emitter[0], y_t), "1 kΩ", side="left")
    s.res(q4.emitter, (q4.emitter[0], y_t), "1 kΩ", side="right")
    c2 = (q2.collector[0], 1.4)
    s.dot(c2)

    # signal input from the LMC662 through 1 kOhm
    s.res(q2.base, (8.4, 0.0), "1 kΩ", side="top")
    s.terminal((8.4, 0.0), "from LMC662", side="bottom")

    # voltage-amplifier stage Q5 (PNP) with its Miller capacitor
    q5 = s.pnp((10.4, 1.4), name="Q5", side="right")
    s.wire(c2, q5.base)
    s.res(q5.emitter, (q5.emitter[0], y_t), "1 kΩ", side="right")
    x_v = q5.collector[0]
    vh = (x_v, 0.6)
    s.wire(q5.collector, vh)
    s.dot(vh)
    x_c = 9.4
    s.dot((x_c, 1.4))
    s.cap((x_c, 1.4), (x_c, 0.6), "33 pF", side="left")
    s.wire((x_c, 0.6), vh)

    # bias spreader between vh and vl: QD1, QD2 (diode-connected NPN) and 100 Ohm
    s.diode(vh, (x_v, -0.5), "QD1", side="right")
    s.diode((x_v, -0.5), (x_v, -1.6), "QD2", side="right")
    s.res((x_v, -1.6), (x_v, -3.2), "100 Ω", side="right")
    vl = (x_v, -3.2)
    s.dot(vl)

    # VAS current sink Q6; its base two diode drops above -100 V, fed from 0 V
    q6 = s.npn((x_v - dx, -3.7), name="Q6", side="right")
    s.wire(vl, q6.collector)
    s.res(q6.emitter, (q6.emitter[0], y_b), "650 Ω", side="right")
    b6 = (9.4, -3.7)
    s.wire(q6.base, b6)
    s.dot(b6)
    s.diode(b6, (9.4, -4.5), "QD3", side="left")
    s.diode((9.4, -4.5), (9.4, -5.3), "QD4", side="left")
    s.wire((9.4, -5.3), (9.4, y_b))
    s.res(b6, (9.4, -2.1), "200 kΩ", side="left")
    s.supply((9.4, -2.1), "0 V")

    # complementary emitter followers Q7 (NPN) and Q8 (PNP)
    q7 = s.npn((13.4, vh[1]), name="Q7", side="right")
    q8 = s.pnp((13.4, vl[1]), name="Q8", side="right")
    s.wire(vh, q7.base)
    s.wire(vl, q8.base)
    x_e = q7.emitter[0]
    s.wire(q7.collector, (x_e, y_t))
    s.wire(q8.collector, (x_e, y_b))
    s.res(q7.emitter, (x_e, -1.2), "47 Ω", side="right")
    s.res(q8.emitter, (x_e, -1.4), "47 Ω", side="right")
    s.wire((x_e, -1.2), (x_e, -1.4))
    v_out = (x_e, -1.3)
    s.dot(v_out)
    x_f = 15.6                                    # feedback column
    s.wire(v_out, (x_f, v_out[1]))
    s.dot((x_f, v_out[1]))
    s.wire((x_f, v_out[1]), (16.4, v_out[1]))
    s.terminal((16.4, v_out[1]), "$V_{out}$")

    # rails, labelled at their left ends
    s.wire((q3.emitter[0], y_t), (x_e, y_t))
    for x in (q3.emitter[0], q4.emitter[0], q5.emitter[0]):
        s.dot((x, y_t))
    s.text((q3.emitter[0] - 0.2, y_t), "+100 V", ha="right")
    s.wire((x_tail, y_b), (x_e, y_b))
    for x in (9.4, q6.emitter[0]):
        s.dot((x, y_b))
    s.text((x_tail - 0.2, y_b), "−100 V", ha="right")

    # gain-setting divider: 140 kOhm from V_out over the top to Q1's base, 10 kOhm to ground
    x_fb, y_fb = 0.8, 6.6
    s.wire((x_f, v_out[1]), (x_f, y_fb), (9.2, y_fb))
    s.res((9.2, y_fb), (7.2, y_fb), "140 kΩ", side="top")
    s.wire((7.2, y_fb), (x_fb, y_fb), (x_fb, 0.0), q1.base)
    s.dot((x_fb, 0.0))
    s.res((x_fb, 0.0), (x_fb, -1.6), "10 kΩ", side="left")
    s.ground((x_fb, -1.6))
'''
s = s[:start] + new_body + s[end:]
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
