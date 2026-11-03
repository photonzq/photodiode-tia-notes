from pathlib import Path

p = Path(__file__).resolve().parent / "hg_schematics.py"
s = p.read_text(encoding="utf-8")


def rep(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:80])
    s = s.replace(a, b)


# guard panel: tidy ending
rep('''    s.wire(P(x_fr, yo), P(x_fr + 0.5, yo)) if kind == "film" else None
    if kind == "film":
        s.terminal(P(x_fr + 0.5, yo), "$V_{out}$")
''', '''    if kind == "film":
        s.wire(P(x_fr, yo), P(x_fr + 0.6, yo))
        s.terminal(P(x_fr + 0.6, yo), "$V_{out}$")
''')

# gain ranging: explicit loop without conditional expressions
rep('''    for y, on, rname, note in rows:
        s.dot((x_bus, y)) if y != rows[-1][0] else None
        s.switch((x_bus, y), (x_j - 0.1, y), closed=on, text="$S_{in}$" if y == rows[0][0] else None,
                 side="top")
        s.dot((x_j, y))
        s.wire((x_j - 0.1, y), (x_j, y))
        s.switch((x_j, y), (x_r0, y), closed=on, text="$S_{out}$" if y == rows[0][0] else None,
                 side="top")
        s.res((x_r0, y), (x_fr, y), rname, side="top")
        s.dot((x_fr, y)) if y != rows[-1][0] else None
        s.switch((x_j, y), (x_j, y - 1.2), closed=not on, text="$S_{sh}$" if y == rows[0][0] else None,
                 side="left")
        s.ground((x_j, y - 1.2))
        s.text((x_fr + 0.3, y + 0.35), note, va="bottom")
''', '''    for i, (y, on, rname, note) in enumerate(rows):
        first, last = i == 0, i == len(rows) - 1
        if not last:
            s.dot((x_bus, y))
            s.dot((x_fr, y))
        s.switch((x_bus, y), (x_j, y), closed=on, text="$S_{in}$" if first else None, side="top")
        s.dot((x_j, y))
        s.switch((x_j, y), (x_r0, y), closed=on, text="$S_{out}$" if first else None, side="top")
        s.res((x_r0, y), (x_fr, y), rname, side="top")
        s.switch((x_j, y), (x_j, y - 1.2), closed=not on, text="$S_{sh}$" if first else None,
                 side="left")
        s.ground((x_j, y - 1.2))
        s.text((x_fr + 0.3, y), note)
''')

# log amplifier
rep('''    s = ss.Sheet()
    pd_down(s, 0.0, bias="ground")
    op, x_fr = tia(s, 0.0, 4.6, 1.4, "x", None, y_r=0.0)  # placeholder replaced below
    s.save(out / "schem_log_amp")
''', '''    s = ss.Sheet()
    pd_down(s, 0.0, bias="ground")
    op = s.opamp((4.8, 0.0))
    s.wire((0.0, 0.0), op.in1)
    s.wire(op.in2, (4.3, op.in2[1]), (4.3, -1.6))
    s.ground((4.3, -1.6))
    x_fl, x_fr = 1.4, op.out[0] + 0.75
    q = s.npn((3.2, 1.66), angle=90)              # base below; collector left, emitter right
    y_q = q.collector[1]
    s.dot((x_fl, 0.0))
    s.wire((x_fl, 0.0), (x_fl, 3.6))
    s.dot((x_fl, y_q))
    s.wire((x_fl, y_q), q.collector)
    s.wire(q.base, (q.base[0], 1.15))
    s.ground((q.base[0], 1.15))
    s.text((q.base[0] + 0.55, 1.45), "Q", va="center")
    s.res(q.emitter, (x_fr - 0.5, y_q), "$R_E$ (optional)", side="top", color=ss.OPTIONAL, dashed=True)
    s.wire((x_fr - 0.5, y_q), (x_fr, y_q))
    s.dot((x_fr, y_q))
    s.cap((x_fl, 3.6), (x_fr, 3.6), "$C_C$", side="top")
    s.wire((x_fr, 3.6), (x_fr, op.out[1]))
    s.wire(op.out, (x_fr, op.out[1]))
    s.dot((x_fr, op.out[1]))
    out_terminal(s, x_fr, op.out[1])
    s.save(out / "schem_log_amp")
''')

# optical reset
rep('''    s = ss.Sheet()
    s.save(out / "schem_optical_reset")
''', '''    s = ss.Sheet()
    # detector at the gate node, biased from below
    s.wire((0.0, 0.0), (0.0, -0.35))
    s.diode((0.0, -0.35), (0.0, -1.65), "detector", side="right")
    s.wire((0.0, -1.65), (0.0, -2.0))
    s.supply((0.0, -2.0), "bias", up=False)
    s.dot((0.0, 0.0))
    # input JFET, then the rest of the inverting amplifier
    j = s.njfet((2.8, 0.0), mirror=True, name="input FET")
    s.wire((0.0, 0.0), j.gate)
    s.wire(j.source, (j.source[0], -0.8))
    s.ground((j.source[0], -0.8))
    y_a = 1.4
    s.wire(j.drain, (j.drain[0], y_a), (6.2, y_a))
    o = s.buffer((6.2, y_a), text="−A")
    s.text((7.2, y_a + 0.85), "amplifier", ha="center", va="bottom")
    x_o = o[0] + 0.5
    s.wire(o, (x_o, y_a))
    s.dot((x_o, y_a))
    # feedback capacitor from the output back to the gate
    x_fb, y_c = 1.4, 3.0
    s.dot((x_fb, 0.0))
    s.wire((x_fb, 0.0), (x_fb, y_c))
    s.cap((x_fb, y_c), (x_o, y_c), "$C_F$ ≈ 0.5 pF", side="top")
    s.wire((x_o, y_c), (x_o, y_a))
    s.wire((x_o, y_a), (x_o + 1.5, y_a))
    s.terminal((x_o + 1.5, y_a), "$V_{out}$")
    # window comparator on the output, switching the LED that lights the FET
    x_c = x_o + 0.8
    s.dot((x_c, y_a))
    y_l = -1.8
    s.wire((x_c, y_a), (x_c, y_l))
    oc = s.buffer((x_c, y_l), left=True, text="")
    s.text((x_c - 1.0, y_l - 0.9), "window\\ncomparator", ha="center", va="top")
    s.wire(oc, (5.4, y_l))
    s.led((5.4, y_l), (4.2, y_l), None)
    s.wire((4.2, y_l), (3.9, y_l), (3.9, y_l - 0.3))
    s.ground((3.9, y_l - 0.3))
    for k in (0.0, 0.32):
        s.arrow((4.75 + k, y_l + 0.45), (4.15 + k, y_l + 1.15), color=ss.LIGHT, width=0.13, length=0.17)
    s.text((5.3, y_l + 0.9), "LED", va="center")
    # the cryostat around detector, FET, C_F and LED
    s.box(-1.3, -3.3, 5.8, 4.0, None, color=ss.OPTIONAL, dashed=True)
    s.text((-1.15, 3.85), "cryostat, about 77 K", va="top", color=ss.OPTIONAL)
    s.save(out / "schem_optical_reset")
''')
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
