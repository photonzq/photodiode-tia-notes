from pathlib import Path

p = Path(__file__).resolve().parents[1] / "hv_output_stage" / "scripts" / "hv_schematics.py"
s = p.read_text(encoding="utf-8")


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (s.count(a), a)
    s = s.replace(a, b)


# architecture: two-line ring label, C_F label below, divider moved right
rep('    s.ring(2.3, -0.42, 4.25, 0.42, "guard ring", text_at="bottom_left")\n',
    '    s.ring(2.3, -0.42, 4.25, 0.42, "guard\\nring", text_at="bottom_left")\n')
rep('    s.cap((x_s, y_c), (x_o, y_c), "$C_F$ ≈ 0.1 pF", side="top", color=ss.PARASITIC)\n',
    '    s.cap((x_s, y_c), (x_o, y_c), "$C_F$ ≈ 0.1 pF", side="bottom", color=ss.PARASITIC)\n')
rep('''    s.wire((x_o, yo), (12.5, yo))
    s.res((12.5, yo), (14.3, yo), "980 kΩ", side="top")
    s.dot((14.3, yo))
    s.res((14.3, yo), (14.3, -2.1), "20 kΩ", side="right")
    s.ground((14.3, -2.1))
    s.wire((14.3, yo), (15.1, yo))
    s.terminal((15.1, yo), "ADC, ±2 V")
''', '''    s.wire((x_o, yo), (12.9, yo))
    s.res((12.9, yo), (14.9, yo), "980 kΩ", side="top")
    s.dot((14.9, yo))
    s.res((14.9, yo), (14.9, -2.1), "20 kΩ", side="right")
    s.ground((14.9, -2.1))
    s.wire((14.9, yo), (15.7, yo))
    s.terminal((15.7, yo), "ADC, ±2 V")
''')

# hv stage: spread the pair and move everything right of it
rep('    q2 = s.npn((4.7, 0.0), mirror=True, name="Q2", side="left")\n',
    '    q2 = s.npn((5.6, 0.0), mirror=True, name="Q2", side="left")\n')
rep('    s.res(q1.emitter, (q1.emitter[0], y_tail), "1 kΩ", side="left")\n'
    '    s.res(q2.emitter, (q2.emitter[0], y_tail), "1 kΩ", side="right")\n',
    '    s.res(q1.emitter, (q1.emitter[0], y_tail), "1 kΩ", side="right")\n'
    '    s.res(q2.emitter, (q2.emitter[0], y_tail), "1 kΩ", side="left")\n')
rep('    s.res(q3.emitter, (q3.emitter[0], y_t), "1 kΩ", side="left")\n'
    '    s.res(q4.emitter, (q4.emitter[0], y_t), "1 kΩ", side="right")\n',
    '    s.res(q3.emitter, (q3.emitter[0], y_t), "1 kΩ", side="right")\n'
    '    s.res(q4.emitter, (q4.emitter[0], y_t), "1 kΩ", side="left")\n')
rep('    q5 = s.pnp((6.9, 1.4), name="Q5", side="right")\n', '    q5 = s.pnp((7.6, 1.4), name="Q5", side="right")\n')
rep('    x_c = 5.9\n', '    x_c = 6.7\n')
rep('    b6 = (6.0, -3.3)\n', '    b6 = (6.7, -3.3)\n')
rep('''    s.diode(b6, (6.0, -4.3), "QD3", side="left")
    s.diode((6.0, -4.3), (6.0, -5.3), "QD4", side="left")
    s.wire((6.0, -5.3), (6.0, y_b))
    s.res(b6, (4.6, -3.3), "200 kΩ", side="top")
    s.ground((4.6, -3.3))
''', '''    s.diode(b6, (6.7, -4.3), "QD3", side="left")
    s.diode((6.7, -4.3), (6.7, -5.3), "QD4", side="left")
    s.wire((6.7, -5.3), (6.7, y_b))
    s.res(b6, (5.2, -3.3), "200 kΩ", side="top")
    s.ground((5.2, -3.3))
''')
rep('''    s.wire(q2.base, (5.4, 0.0))
    s.res((5.4, 0.0), (5.4, -1.5), "1 kΩ", side="right")
    s.terminal((5.4, -1.5), "from LMC662", side="bottom")
''', '''    s.wire(q2.base, (6.3, 0.0))
    s.res((6.3, 0.0), (6.3, -1.3), "1 kΩ", side="right")
    s.terminal((6.3, -1.3), "from\\nLMC662", side="bottom")
''')
rep('    q7 = s.npn((9.6, vh[1]), name="Q7", side="right")\n    q8 = s.pnp((9.6, vl[1]), name="Q8", side="right")\n',
    '    q7 = s.npn((10.3, vh[1]), name="Q7", side="right")\n    q8 = s.pnp((10.3, vl[1]), name="Q8", side="right")\n')
rep('    x_f = 11.6                                    # feedback column\n',
    '    x_f = 12.7                                    # feedback column\n')
rep('    s.wire((x_f, v_out[1]), (12.3, v_out[1]))\n    s.terminal((12.3, v_out[1]), "$V_{out}$")\n',
    '    s.wire((x_f, v_out[1]), (13.4, v_out[1]))\n    s.terminal((13.4, v_out[1]), "$V_{out}$")\n')
rep('    for x in (6.0, q6.emitter[0]):\n', '    for x in (6.7, q6.emitter[0]):\n')
rep('    s.wire((x_f, v_out[1]), (x_f, y_fb), (7.0, y_fb))\n'
    '    s.res((7.0, y_fb), (5.0, y_fb), "140 kΩ", side="top")\n'
    '    s.wire((5.0, y_fb), (x_fb, y_fb), (x_fb, 0.0), q1.base)\n',
    '    s.wire((x_f, v_out[1]), (x_f, y_fb), (8.0, y_fb))\n'
    '    s.res((8.0, y_fb), (6.0, y_fb), "140 kΩ", side="top")\n'
    '    s.wire((6.0, y_fb), (x_fb, y_fb), (x_fb, 0.0), q1.base)\n')

# guard figures: feedback junction at the right of the ring, tie at its left, two-line label
rep('    op = _tia(s, cx.end[0], 9.4, 7.5)\n'
    '    x_t = 8.5                                                         # + input and ring tie\n',
    '    op = _tia(s, cx.end[0], 9.4, 8.4)\n'
    '    x_t = 7.4                                                         # + input and ring tie\n')
rep('    s.ring(6.9, -0.42, 8.9, 0.42, "guard ring", text_at="top_right")\n',
    '    s.ring(6.9, -0.42, 8.9, 0.42, "guard\\nring", text_at="top_left")\n', 2)
rep('    op = _tia(s, tx.end[0], 9.6, 7.5)\n', '    op = _tia(s, tx.end[0], 9.6, 8.4)\n')
rep('    s.wire((tx.guardend[0], tx.guardend[1]), (tx.guardend[0], y_g), (8.4, y_g), (8.4, -0.42),\n',
    '    s.wire((tx.guardend[0], tx.guardend[1]), (tx.guardend[0], y_g), (7.4, y_g), (7.4, -0.42),\n')
rep('    s.res((x_i, y_r), (x_i, -1.5), "$R_{iso}$\\n100 Ω", side="left")\n',
    '    s.res((x_i, y_r), (x_i, -1.6), "$R_{iso}$\\n100 Ω", side="left")\n')
rep('    s.wire((x_i, -1.5), (x_i, y_g), color=ss.GUARD)\n', '    s.wire((x_i, -1.6), (x_i, y_g), color=ss.GUARD)\n')
# bootstrap: labels clear of the arrows and the ground
rep('    s.text((-0.6, -0.8), "photodiode", ha="right")\n',
    '    s.text((-0.35, 0.15), "photodiode", ha="right", va="bottom")\n')
rep('    s.text((x_c + 0.25, -1.95), "shield, driven", color=ss.GUARD)\n',
    '    s.text((x_c - 0.25, -1.95), "shield, driven", ha="right", color=ss.GUARD)\n')
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
