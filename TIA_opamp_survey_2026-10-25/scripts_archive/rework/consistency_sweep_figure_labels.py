"""Consistency sweep of 3 November 2026: the words drawn inside the figures brought in line with the
report. The SPICE figures (Figures 3 and 5-9, 18 and 19) still called our analytical model "the
survey" and quoted equation numbers from before the report was put into its narrative order, and
Figure 20 named the two composites by labels that the text does not use.

Edits make_spice_figures.py and make_narrative_figures.py in place; each old text must occur once.
Redraw afterwards with  python make_spice_figures.py --only 7 9 10 11 12 13 15 16  and with
make_narrative_figures.fig_benchmark for fig20 (no simulation is run).
"""
from pathlib import Path

ARCH = Path(__file__).resolve().parents[1]

EDITS = {
    "make_spice_figures.py": [
        ('label=r"survey, $A/NG$ (datasheet curve)"', 'label=r"analytical model, $A/NG$ (datasheet curve)"'),
        ('f"survey: back to 0 dB\\nat {f_second/1e9:.1f} GHz"',
         'f"analytical model: back to\\n0 dB at {f_second/1e9:.1f} GHz"'),
        ('label="survey, datasheet curve"', 'label="analytical model, datasheet curve"'),
        ('label=f"double injection, Eq. (46): GM', 'label=f"double injection, Eq. (39): GM'),
        ('label=f"voltage injection alone, Eq. (44): GM', 'label=f"voltage injection alone, Eq. (37): GM'),
        ('label=r"survey model, $C_D$ = 1.0 pF"', 'label=r"analytical model, $C_D$ = 1.0 pF"'),
        ('label=r"Eq. (54), $|A_-(f_{180})|$ = 5.3"', 'label=r"Eq. (47), $|A_-(f_{180})|$ = 5.3"'),
        ('"solid: SPICE\\ndashed: survey model"', '"solid: SPICE\\ndashed: analytical model"'),
        ('label="survey, central estimate"', 'label="analytical model, central estimate"'),
        ('label="survey, central to high (FET)"', 'label="analytical model, central to high (FET)"'),
        ('label="Eq. (17) with the fitted terms"', 'label="Eq. (23) with the fitted terms"'),
        # shorter in Figure 8, whose legend must clear the OPA818 point
        ('label="survey (datasheet curves)"', 'label="analytical model"'),
        ('label="survey, central to high noise (FET)"', 'label="up to the high estimate (FET)"'),
        ('axs[0].plot(fs, db(Z), color=col, lw=LW, ls=DASH, label="survey model, 14 pF")',
         'axs[0].plot(fs, db(Z), color=col, lw=LW, ls=DASH, label="analytical model, 14 pF")'),
        ('axs[1].plot(fs, np.sqrt(S) * 1e12, color=col, lw=LW, ls=DASH, label="survey model, 14 pF")',
         'axs[1].plot(fs, np.sqrt(S) * 1e12, color=col, lw=LW, ls=DASH, label="analytical model, 14 pF")'),
        ('label=r"survey model, same $C_F$"', 'label=r"analytical model, same $C_F$"'),
        ('label="total noise, survey model"', 'label="total noise, analytical model"'),
    ],
    "make_narrative_figures.py": [
        ('    fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.4, 3.24), constrained_layout=True)\n'
         '    for name, d in designs.items():',
         '    # the names the report uses: the composites of Sections 7.1 and 7.2\n'
         '    labels = {"CE3512K2 composite": "pHEMT composite", "HV composite (G2 = 5.5)": "high-voltage composite"}\n'
         '    fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.4, 3.24), constrained_layout=True)\n'
         '    for name, d in designs.items():'),
        ('label=name.replace(" (G2 = 5.5)", ""))', 'label=labels.get(name, name))'),
    ],
}

for name, pairs in EDITS.items():
    path = ARCH / name
    s = path.read_text(encoding="utf-8")
    for old, new in pairs:
        n = s.count(old)
        assert n == 1, f"{name}: found {n} times: {old[:70]!r}"
        s = s.replace(old, new)
    path.write_bytes(s.encode("utf-8"))
    print(f"{name}: {len(pairs)} labels changed")
