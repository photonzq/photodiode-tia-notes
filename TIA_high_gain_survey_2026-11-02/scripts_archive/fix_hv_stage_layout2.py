from pathlib import Path

p = Path(__file__).resolve().parents[1] / "hv_output_stage" / "scripts" / "hv_schematics.py"
s = p.read_text(encoding="utf-8")


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (s.count(a), a)
    s = s.replace(a, b)


rep('    s.terminal((8.4, 0.0), "from LMC662", side="bottom")\n',
    '    s.terminal((8.4, 0.0), "from LMC662", side="right")\n')
rep('    q5 = s.pnp((10.4, 1.4), name="Q5", side="right")\n', '    q5 = s.pnp((11.9, 1.4), name="Q5", side="right")\n')
rep('    x_c = 9.4\n', '    x_c = 10.9\n')
rep('    b6 = (9.4, -3.7)\n', '    b6 = (10.9, -3.7)\n')
rep('''    s.diode(b6, (9.4, -4.5), "QD3", side="left")
    s.diode((9.4, -4.5), (9.4, -5.3), "QD4", side="left")
    s.wire((9.4, -5.3), (9.4, y_b))
    s.res(b6, (9.4, -2.1), "200 kΩ", side="left")
    s.supply((9.4, -2.1), "0 V")
''', '''    s.diode(b6, (10.9, -4.5), "QD3", side="left")
    s.diode((10.9, -4.5), (10.9, -5.3), "QD4", side="left")
    s.wire((10.9, -5.3), (10.9, y_b))
    s.res(b6, (10.9, -2.1), "200 kΩ", side="left")
    s.supply((10.9, -2.1), "0 V")
''')
rep('    q7 = s.npn((13.4, vh[1]), name="Q7", side="right")\n    q8 = s.pnp((13.4, vl[1]), name="Q8", side="right")\n',
    '    q7 = s.npn((14.9, vh[1]), name="Q7", side="right")\n    q8 = s.pnp((14.9, vl[1]), name="Q8", side="right")\n')
rep('    x_f = 15.6                                    # feedback column\n',
    '    x_f = 17.1                                    # feedback column\n')
rep('    s.wire((x_f, v_out[1]), (16.4, v_out[1]))\n    s.terminal((16.4, v_out[1]), "$V_{out}$")\n',
    '    s.wire((x_f, v_out[1]), (17.9, v_out[1]))\n    s.terminal((17.9, v_out[1]), "$V_{out}$")\n')
rep('    for x in (9.4, q6.emitter[0]):\n', '    for x in (10.9, q6.emitter[0]):\n')
rep('    s.wire((x_f, v_out[1]), (x_f, y_fb), (9.2, y_fb))\n    s.res((9.2, y_fb), (7.2, y_fb), "140 kΩ", side="top")\n    s.wire((7.2, y_fb), (x_fb, y_fb), (x_fb, 0.0), q1.base)\n',
    '    s.wire((x_f, v_out[1]), (x_f, y_fb), (10.0, y_fb))\n    s.res((10.0, y_fb), (8.0, y_fb), "140 kΩ", side="top")\n    s.wire((8.0, y_fb), (x_fb, y_fb), (x_fb, 0.0), q1.base)\n')
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
