from pathlib import Path

p = Path(__file__).resolve().parent / "hg_schematics.py"
s = p.read_text(encoding="utf-8")


def rep(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:90])
    s = s.replace(a, b)


# Figure 1: two-line label for the amplifier's input capacitance
rep('    for x, lab in ((8.6, "$C_{PCB}$"), (10.3, "$C_{CM} + C_{DIFF}$")):\n',
    '    for x, lab in ((8.6, "$C_{PCB}$"), (10.3, "$C_{CM} +$\\n$C_{DIFF}$")):\n')

# Figure 6: photodiode at the input, ring tie further right, op-amp output wired
rep('''    op = s.opamp(P(3.0, 0.0))
    s.wire(P(0.0, 0.0), op.in1)
    s.terminal(P(0.0, 0.0), None)
    s.text(P(0.0, 0.3), "from the\\nphotodiode", ha="center", va="bottom")
    s.ring(ox + 0.6, oy - 0.42, ox + 1.9, oy + 0.42, "guard\\nring", text_at="bottom_left")
    s.wire(op.in2, P(1.6, op.in2[1] - oy), P(1.6, -1.6))
    s.wire(P(1.6, -0.42), P(1.6, op.in2[1] - oy), color=ss.GUARD)
    s.dot(P(1.6, op.in2[1] - oy))
    s.ground(P(1.6, -1.6))
''', '''    op = s.opamp(P(3.0, 0.0))
    s.wire(P(0.0, 0.0), P(0.0, -0.35))
    s.photodiode(P(0.0, -0.35), P(0.0, -1.65))
    s.wire(P(0.0, -1.65), P(0.0, -2.0))
    s.ground(P(0.0, -2.0))
    s.wire(P(0.0, 0.0), op.in1)
    s.ring(ox + 0.6, oy - 0.42, ox + 2.1, oy + 0.42, "guard\\nring", text_at="bottom_left")
    s.wire(op.in2, P(1.85, op.in2[1] - oy), P(1.85, -1.6))
    s.wire(P(1.85, -0.42), P(1.85, op.in2[1] - oy), color=ss.GUARD)
    s.dot(P(1.85, op.in2[1] - oy))
    s.ground(P(1.85, -1.6))
''')
rep('''    s.wire(P(x_fr, top), P(x_fr, op.out[1] - oy))
    s.dot(P(x_fr, op.out[1] - oy))
    yo = op.out[1] - oy
''', '''    s.wire(P(x_fr, top), P(x_fr, op.out[1] - oy))
    s.wire(op.out, P(x_fr, op.out[1] - oy))
    s.dot(P(x_fr, op.out[1] - oy))
    yo = op.out[1] - oy
''')

# Figure 7: photodiode at the input; label the divider as six equal resistors
rep('''    op = s.opamp((11.0, 0.0))
    s.terminal((0.0, 0.0), "from the photodiode", side="top")
    s.wire((0.0, 0.0), op.in1)
''', '''    op = s.opamp((11.0, 0.0))
    pd_down(s, 0.0, bias="ground")
    s.wire((0.0, 0.0), op.in1)
''')
rep('''    for k in range(6):
        s.res((xd, ys[k]), (xd, ys[k + 1]), "1 kΩ" if k == 0 else None, side="left")
''', '''    for k in range(6):
        s.res((xd, ys[k]), (xd, ys[k + 1]), None)
    s.text((xd - 0.5, 0.5 * (ys[0] + ys[6])), "six equal\\nresistors,\\n1 kΩ each", ha="right")
''')

# Figure 9: larger stage triangle, label clear of the output column
rep('''    o = s.buffer((x_fr2, op2.out[1]), text="×100")
    s.text((x_fr2 + 1.0, op2.out[1] + 0.85), "voltage stage", ha="center", va="bottom")
''', '''    o = s.buffer((x_fr2, op2.out[1]), text="×100", h=1.8)
    s.text((x_fr2 + 0.55, op2.out[1] + 1.05), "voltage stage", va="bottom")
''')

# Figure 12: feedback a little higher, clear of the 15 V label
rep('''    y_r, y_c = 5.6, 6.7
    s.dot((x_fb, 0.0))
    s.wire((x_fb, 0.0), (x_fb, y_c))
    s.dot((x_fb, y_r))
    s.res((x_fb, y_r), (x_o, y_r), "$R_F$", side="bottom")''', '''    y_r, y_c = 5.9, 7.0
    s.dot((x_fb, 0.0))
    s.wire((x_fb, 0.0), (x_fb, y_c))
    s.dot((x_fb, y_r))
    s.res((x_fb, y_r), (x_o, y_r), "$R_F$", side="bottom")''')

# Figure 16: plain diode for the LED (red light arrows only), C_F inside the cryostat
rep('''    s.cap((x_fb, y_c), (x_o, y_c), "$C_F$ ≈ 0.5 pF", side="top")
    s.wire((x_o, y_c), (x_o, y_a))''', '''    s.cap((x_fb, y_c), (4.4, y_c), "$C_F$ ≈ 0.5 pF", side="top")
    s.wire((4.4, y_c), (x_o, y_c), (x_o, y_a))''')
rep('''    s.led((5.4, y_l), (4.2, y_l), None)''', '''    s.diode((5.4, y_l), (4.2, y_l), None)''')
rep('''    s.box(-1.3, -3.3, 5.8, 4.0, None, color=ss.OPTIONAL, dashed=True)''',
    '''    s.box(-1.3, -3.3, 6.0, 4.0, None, color=ss.OPTIONAL, dashed=True)''')
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
