from pathlib import Path

p = Path(__file__).resolve().parents[1] / "make_schematics.py"
s = p.read_text(encoding="utf-8")


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (s.count(a), a)
    s = s.replace(a, b)


# Fig. 21: R_D label to the left, v_d label right of the junction
rep('    s.text((x_d - 0.15, y_d + 0.1), "$v_d$", ha="right", va="bottom")\n'
    '    s.res((x_d, y_d), (x_d, 4.2), "$R_D$\\n1.1 kΩ", side="right")\n',
    '    s.text((x_d + 0.2, y_d + 0.12), "$v_d$", va="bottom")\n'
    '    s.res((x_d, y_d), (x_d, 4.2), "$R_D$\\n1.1 kΩ", side="left")\n')

# Fig. 22: C_L, R_F and C_F labels above their parts, loops raised
rep('''    x_l, y_l = 3.1, 1.1
    s.dot((x_l, 0.0))
    s.wire((x_l, 0.0), (x_l, y_l))
    s.cap((x_l, y_l), (x_1, y_l), "$C_L$  3.25 pF", side="bottom")''',
    '''    x_l, y_l = 3.1, 1.3
    s.dot((x_l, 0.0))
    s.wire((x_l, 0.0), (x_l, y_l))
    s.cap((x_l, y_l), (x_1, y_l), "$C_L$  3.25 pF", side="top")''')
rep('''    x_f, y_r, y_c = 1.9, 2.3, 3.4''', '''    x_f, y_r, y_c = 1.9, 2.8, 4.0''')
rep('''    s.text((0.5 * (x_f + x_2), y_r - 0.42), "$R_F$  2 × 1 kΩ", ha="center", va="top")''',
    '''    s.text((0.5 * (x_f + x_2), y_r + 0.42), "$R_F$  2 × 1 kΩ", ha="center", va="bottom")''')

# Fig. 23: R_s label to the left, integrator named above
rep('''    s.res((x_s, 0.0), (x_s, y_x), "$R_s = V_S/I_{\\\\mathrm{DC}}$\\n500 Ω at 10 mA", side="right")''',
    '''    s.res((x_s, 0.0), (x_s, y_x), "$R_s = V_S/I_{\\\\mathrm{DC}}$\\n500 Ω at 10 mA", side="left")''')
rep('''    u2 = s.opamp((x_fr - 0.6, y_p - 0.9), minus_on_top=False, left=True, name="integrator",
                 name_at="below")''',
    '''    u2 = s.opamp((x_fr - 0.6, y_p - 0.9), minus_on_top=False, left=True, name="integrator",
                 name_at="above")''')
rep('''    s.res((x_fr + 1.6, u2.in1[1]), u2.in1, None)''',
    '''    s.res((x_fr + 1.6, u2.in1[1]), u2.in1, "$R_i$", side="bottom")''')
rep('''    s.cap((x_ci, -5.0), (u2.out[0], -5.0), None)''',
    '''    s.cap((x_ci, -5.0), (u2.out[0], -5.0), "$C_i$", side="bottom")''')
rep('''    s.save(out / "fig23_option_a")''',
    '''    s.save(out / "fig23_option_a")''')

# Fig. 24: coupling capacitor clear of the diode; output terminal
rep('''    s.cap((0.0, 0.0), (1.8, 0.0), "$C_c$  10 nF", side="top")
    tia(s, 1.8, 4.0, 3.2, "$R_F$", "$C_F$")''',
    '''    s.wire((0.0, 0.0), (0.8, 0.0))
    s.cap((0.8, 0.0), (2.4, 0.0), "$C_c$  10 nF", side="top")
    op, x_fr = tia(s, 2.4, 4.6, 3.8, "$R_F$", "$C_F$")
    s.wire((x_fr, op.out[1]), (x_fr + 0.8, op.out[1]))
    s.terminal((x_fr + 0.8, op.out[1]), "$v_o$")''')

# Fig. 25: output terminal
rep('''    tia(s, 0.0, 5.6, 4.8, "$R_F$", "$C_F$")
    s.save(out / "fig25_option_c")''',
    '''    op, x_fr = tia(s, 0.0, 5.6, 4.8, "$R_F$", "$C_F$")
    s.wire((x_fr, op.out[1]), (x_fr + 0.8, op.out[1]))
    s.terminal((x_fr + 0.8, op.out[1]), "$v_o$")
    s.save(out / "fig25_option_c")''')

# Fig. 27: C_c label below, output terminal
rep('''    s.cap((x_cd, y_b), (2.6, y_b), "$C_c$", side="top")''',
    '''    s.cap((x_cd, y_b), (2.6, y_b), "$C_c$", side="bottom")''')
rep('''    tia(s, 0.0, 6.9, 6.1, "$R_F$", "$C_F$", y_r=3.4, y_c=4.5)
    s.save(out / "fig27_bootstrap")''',
    '''    op, x_fr = tia(s, 0.0, 6.9, 6.1, "$R_F$", "$C_F$", y_r=3.4, y_c=4.5)
    s.wire((x_fr, op.out[1]), (x_fr + 0.8, op.out[1]))
    s.terminal((x_fr + 0.8, op.out[1]), "$v_o$")
    s.save(out / "fig27_bootstrap")''')

# Fig. 28: standing-current resistors further right; output terminal
rep('''    s.wire(e1, (0.9, e1[1]))
    s.res((0.9, e1[1]), (0.9, 3.7), "$R_q$", side="right", color=ss.OPTIONAL, dashed=True)
    s.supply((0.9, 3.7), "+12 V", color=ss.OPTIONAL)
    s.wire(e2, (0.9, e2[1]))
    s.res((0.9, e2[1]), (0.9, -3.7), "$R_q$", side="right", color=ss.OPTIONAL, dashed=True)
    s.supply((0.9, -3.7), "−12 V", up=False, color=ss.OPTIONAL)''',
    '''    s.wire(e1, (1.3, e1[1]))
    s.res((1.3, e1[1]), (1.3, 3.7), "$R_q$", side="right", color=ss.OPTIONAL, dashed=True)
    s.supply((1.3, 3.7), "+12 V", color=ss.OPTIONAL)
    s.wire(e2, (1.3, e2[1]))
    s.res((1.3, e2[1]), (1.3, -3.7), "$R_q$", side="right", color=ss.OPTIONAL, dashed=True)
    s.supply((1.3, -3.7), "−12 V", up=False, color=ss.OPTIONAL)''')
rep('''    tia(s, 0.0, 5.0, 4.2, "$R_F$", "$C_F$", y_r=1.6, y_c=2.7)
    s.save(out / "fig28_cascode")''',
    '''    op, x_fr = tia(s, 0.0, 5.0, 4.2, "$R_F$", "$C_F$", y_r=1.6, y_c=2.7)
    s.wire((x_fr, op.out[1]), (x_fr + 0.8, op.out[1]))
    s.terminal((x_fr + 0.8, op.out[1]), "$v_o$")
    s.save(out / "fig28_cascode")''')

# Fig. 29: the word "light" above its arrow
rep('''    s.text((x0 - 1.6, 0.0), "light", ha="right", color=ss.LIGHT)''',
    '''    s.text((x0 - 0.75, 0.15), "light", ha="center", va="bottom", color=ss.LIGHT)''')
rep('''    s.box(x_fr - 4.6, y_s - 0.7, x_fr - 1.8, y_s + 0.7, "slow integrator\\nset point $V_{\\\\mathrm{REF}}$")
    s.wire((x_fr - 4.6, y_s), (0.5 * (x0 + x1), y_s), (0.5 * (x0 + x1), -1.6))''',
    '''    s.box(x_fr - 5.2, y_s - 0.7, x_fr - 1.8, y_s + 0.7, "slow integrator\\nset point $V_{\\\\mathrm{REF}}$")
    s.wire((x_fr - 5.2, y_s), (0.5 * (x0 + x1), y_s), (0.5 * (x0 + x1), -1.6))''')

# Fig. 30: transistor labels off the base wires; wider integrator box
rep('''    q2 = s.npn((0.541, -1.2), mirror=True, name="Q2", side="right")''',
    '''    q2 = s.npn((0.541, -1.2), mirror=True, name="Q2", side="left")''')
rep('''    q1 = s.npn((-3.0, -1.2), name="Q1", side="left")''',
    '''    q1 = s.npn((-3.0, -1.2), name="Q1", side="right")''')
rep('''    s.box(x_fr - 4.6, y_s - 0.7, x_fr - 1.8, y_s + 0.7, "servo integrator\\nset point $V_{\\\\mathrm{REF}}$")
    x_w = x_d - 2.6
    s.wire((x_fr - 4.6, y_s), (x_w, y_s), (x_w, -1.2))''',
    '''    s.box(x_fr - 5.2, y_s - 0.7, x_fr - 1.8, y_s + 0.7, "servo integrator\\nset point $V_{\\\\mathrm{REF}}$")
    x_w = x_d - 2.6
    s.wire((x_fr - 5.2, y_s), (x_w, y_s), (x_w, -1.2))''')

# Fig. 31: re-spaced bias chains, photodiodes at x = 5.4, labels clear of each other
rep('''    x_p = 4.6                                   # photodiode column''',
    '''    x_p = 5.4                                   # photodiode column''')
rep('''        s.terminal((-0.4, y), lab, side="left")
        s.wire((-0.4, y), (0.5, y))
        s.dot((0.5, y))
        s.cap((0.5, y), (0.5, y - 1.2), "bulk", side="right")
        s.ground((0.5, y - 1.2))
        s.bead((0.5, y), (1.8, y), "FB", side="top" if sg > 0 else "bottom")
        s.res((1.8, y), (3.4, y), "100 Ω", side="bottom")
        s.dot((1.8, y))
        s.dot((3.4, y))
        for xm in (1.8, 3.4):
            s.wire((xm, y), (xm, y + 0.8))
            s.terminal((xm, y + 0.8), None)
        s.text((2.6, y + 0.8), mon + " monitor", ha="center", va="center")
        s.wire((3.4, y), (x_p, y))
        s.dot((3.9, y))
        s.cap((3.9, y), (3.9, y - 1.2), "10 nF", side="left")
        s.ground((3.9, y - 1.2))''',
    '''        s.terminal((-0.6, y), lab, side="left")
        s.wire((-0.6, y), (0.3, y))
        s.dot((0.3, y))
        s.cap((0.3, y), (0.3, y - 1.2), "bulk", side="left")
        s.ground((0.3, y - 1.2))
        s.bead((0.3, y), (1.5, y), "FB", side="bottom")
        s.wire((1.5, y), (2.1, y))
        s.res((2.1, y), (3.7, y), "100 Ω", side="bottom")
        s.dot((2.1, y))
        s.dot((3.7, y))
        for xm in (2.1, 3.7):
            s.wire((xm, y), (xm, y + 0.8))
            s.terminal((xm, y + 0.8), None)
        s.text((2.9, y + 1.05), mon + " monitor", ha="center", va="bottom")
        s.wire((3.7, y), (x_p, y))
        s.dot((4.1, y))
        s.cap((4.1, y), (4.1, y - 1.2), "10 nF", side="right")
        s.ground((4.1, y - 1.2))''')
rep('''    op, x_fr = tia(s, x_p, 9.2, 8.4, "$R_F$  2 kΩ", "$C_F$  0.25 pF (A), 0.55 pF (B)",
                   name="OPA855 (A)\\nor OPA818 (B)", name_at="below", vref=None)
    s.wire(op.in2, (8.8, op.in2[1]), (8.8, -1.5))
    s.terminal((8.8, -1.5), "$V_{\\\\mathrm{REF}}$", side="left")
    # post-filter and output
    s.wire((x_fr, op.out[1]), (x_fr + 0.6, op.out[1]))
    s.box(x_fr + 0.6, op.out[1] - 0.75, x_fr + 3.2, op.out[1] + 0.75, "low-pass\\n200–250 MHz")
    s.wire((x_fr + 3.2, op.out[1]), (x_fr + 3.8, op.out[1]))
    s.terminal((x_fr + 3.8, op.out[1]), "to digitizer", side="bottom")''',
    '''    op, x_fr = tia(s, x_p, 10.2, 9.4, "$R_F$  2 kΩ", "$C_F$  0.25 pF (A), 0.55 pF (B)",
                   name="OPA855 (A)\\nor OPA818 (B)", name_at="below", vref=None)
    s.wire(op.in2, (9.8, op.in2[1]), (9.8, -1.5))
    s.terminal((9.8, -1.5), "$V_{\\\\mathrm{REF}}$", side="left")
    # post-filter and output
    s.wire((x_fr, op.out[1]), (x_fr + 0.5, op.out[1]))
    s.box(x_fr + 0.5, op.out[1] - 0.75, x_fr + 3.0, op.out[1] + 0.75, "low-pass\\n200–250 MHz")
    s.wire((x_fr + 3.0, op.out[1]), (x_fr + 3.5, op.out[1]))
    s.terminal((x_fr + 3.5, op.out[1]), "to ADC")''')
rep('''    x_x = 5.4
''', '''    x_x = 6.3
''')
rep('''    s.cap((x_x, y_s), (x_x, y_s - 1.3), "10 nF\\n∥ 100 pF", side="left")''',
    '''    s.cap((x_x, y_s), (x_x, y_s - 1.3), "10 nF $\\\\parallel$\\n100 pF", side="left")''')

p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
