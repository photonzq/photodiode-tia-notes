from pathlib import Path

p = Path(__file__).resolve().parents[1] / "make_schematics.py"
s = p.read_text(encoding="utf-8")


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (s.count(a), a)
    s = s.replace(a, b)


# Fig. 21: v_d below the wire, right of the junction
rep('    s.text((x_d + 0.2, y_d + 0.12), "$v_d$", va="bottom")\n',
    '    s.text((x_d + 0.2, y_d - 0.12), "$v_d$", va="top")\n')

# Fig. 30: Q1's name above-left of its circle
rep('''    q1 = s.npn((-3.0, -1.2), name="Q1", side="right")''',
    '''    q1 = s.npn((-3.0, -1.2))
    s.text((q1.center[0] - 0.62, q1.center[1] + 0.5), "Q1", ha="right")''')

# Fig. 31: 100-ohm labels between the monitor taps, 10-nF labels to the left
rep('''        s.res((2.1, y), (3.7, y), "100 Ω", side="bottom")''',
    '''        s.res((2.1, y), (3.7, y), "100 Ω", side="top")''')
rep('''        s.text((2.9, y + 1.05), mon + " monitor", ha="center", va="bottom")''',
    '''        s.text((2.9, y + 1.1), mon + " monitor", ha="center", va="bottom")''')
rep('''        s.cap((4.1, y), (4.1, y - 1.2), "10 nF", side="right")''',
    '''        s.cap((4.1, y), (4.1, y - 1.2), "10 nF", side="left")''')
rep('''    s.cap((x_x, y_s), (x_x, y_s - 1.3), "10 nF $\\\\parallel$\\n100 pF", side="left")''',
    '''    s.cap((x_x, y_s), (x_x, y_s - 1.3), "10 nF\\n$\\\\parallel$ 100 pF", side="left")''')

p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
