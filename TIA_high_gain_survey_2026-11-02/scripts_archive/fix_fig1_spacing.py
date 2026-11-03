from pathlib import Path

p = Path(__file__).resolve().parent / "hg_schematics.py"
s = p.read_text(encoding="utf-8")


def rep(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:80])
    s = s.replace(a, b)


rep('''    the amplifier's i_n at the summing node and e_n in series with its + input."""''',
    '''    the amplifier's i_n at the summing node and e_n between its + input pin and the amplifier.
    C_DIFF runs from the inverting input to the grounded non-inverting pin, which is why it adds
    to C_CM in the summing node's capacitance."""''')
rep('    x_in = 13.3\n    for x, lab in ((1.7, "$C_D$"), (3.2, "$R_{sh}$")):\n',
    '    x_in = 14.1\n    for x, lab in ((1.8, "$C_D$"), (3.3, "$R_{sh}$")):\n')
rep('    for x, lab in ((4.9, "$i_{PD}$"), (6.9, "$i_n$")):\n',
    '    for x, lab in ((5.0, "$i_{PD}$"), (7.0, "$i_n$")):\n')
rep('    for x, lab in ((8.6, "$C_{PCB}$"), (10.1, "$C_{CM}$")):\n',
    '    for x, lab in ((8.8, "$C_{PCB}$"), (10.6, "$C_{CM}$")):\n')
rep('''    x_d, x_e, y_p = 11.6, 12.75, -2.5
    s.dot((x_d, 0.0))
    s.cap((x_d, 0.0), (x_d, y_p), "$C_{DIFF}$", side="left", color=ss.PARASITIC)
''', '''    x_d, x_e, y_p = 12.2, 13.5, -2.5
    s.dot((x_d, 0.0))
    s.cap((x_d, 0.0), (x_d, y_p), None, color=ss.PARASITIC)
    s.text((x_d + 0.3, -0.45), "$C_{DIFF}$", color=ss.PARASITIC)
''')
rep('    x_fl, x_fr = 12.3, op.out[0] + 0.75\n', '    x_fl, x_fr = 13.3, op.out[0] + 0.75\n')
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
