"""Recommended starting component values and their tolerance (Table A8.13).

Usage: python starting_values.py <out_md>

For each recommended design (part, R_F, added input capacitance, target total
C_F) evaluate the nominal response (C_PCB = 0.35 pF) and the response when the
total C_F is 0.1 pF lower or higher (the tolerance of the fitted capacitor and of
the parasitic, Table 1.1), and at the C_PCB corners 0.2 and 0.5 pF.  The external
capacitor is the total minus the 0.08-pF parasitic of Table 1.1 (Appendix G).
Writes a Markdown table.
"""
import sys
from pathlib import Path

import tia_model as tm
from parts_db import PARTS
from run_analysis import C_D, open_loop_model

C_FPAR_PF = 0.08   # parasitic feedback capacitance of Table 1.1 (Appendix G)

DESIGNS = [  # label, part, R_F, C_add (pF), target total C_F (pF)
    ("OPA855", "OPA855", 2000.0, 0.0, 0.25),
    ("OPA855", "OPA855", 1500.0, 0.0, 0.27),
    ("OPA856", "OPA856", 2000.0, 0.0, 0.55),
    ("OPA856", "OPA856", 1500.0, 0.0, 0.65),
    ("LMH6629 (COMP HI)", "LMH6629 (COMP HI)", 2000.0, 0.0, 0.55),
    ("LMH6629 (COMP HI)", "LMH6629 (COMP HI)", 1500.0, 0.0, 0.65),
    ("OPA818", "OPA818", 2000.0, 0.0, 0.55),
    ("OPA818", "OPA818", 1500.0, 0.0, 0.55),
    ("OPA818 + 2 pF", "OPA818", 2000.0, 2.0, 0.75),
    ("OPA955 + 2 pF", "OPA955", 2000.0, 2.0, 0.31),
    ("OPA955 + 3 pF", "OPA955", 1500.0, 3.0, 0.44),
]


def fmt(m):
    s = f"{m['f_3dB']/1e6:.0f} MHz, {m['pm_deg']:.0f}°, {max(m['peaking_dB'], 0.0):.1f} dB"
    return s if m["stable"] else s + " (unstable)"


def main(out_md):
    rows = ["| Design | $R_F$ | Total $C_F$ target (external) | Nominal: $f_{-3\\,\\mathrm{dB}}$, PM, peaking | "
            "Total −0.1 pF | Total +0.1 pF | $C_{\\mathrm{PCB}}$ 0.2 / 0.5 pF | "
            "$NG_\\infty$ at target vs $G_{\\min}$ |",
            "|---|---|---|---|---|---|---|---|"]
    for label, part, R_F, c_add, cf in DESIGNS:
        p = PARTS[part]
        ol, *_ = open_loop_model(p)
        C_T = C_D + (0.35 + c_add) * 1e-12 + p["c_cm"] + p["c_diff"]
        nom = tm.loop_metrics(ol, R_F, C_T, cf * 1e-12)
        lo = tm.loop_metrics(ol, R_F, C_T, (cf - 0.1) * 1e-12)
        hi = tm.loop_metrics(ol, R_F, C_T, (cf + 0.1) * 1e-12)
        c02 = tm.loop_metrics(ol, R_F, C_T - 0.15e-12, cf * 1e-12)
        c05 = tm.loop_metrics(ol, R_F, C_T + 0.15e-12, cf * 1e-12)
        ng = 1 + C_T / (cf * 1e-12)
        ext = cf - C_FPAR_PF
        ext_s = f"{ext:.2f} pF" if ext >= 0.1 else ("none (parasitic only)" if ext <= 0.02 else f"{ext:.2f} pF (below a discrete part)")
        rows.append(f"| {label} | {R_F/1000:g} kΩ | {cf:.2f} pF ({ext_s}) | {fmt(nom)} | {fmt(lo)} | {fmt(hi)} | "
                    f"{c02['f_3dB']/1e6:.0f} / {c05['f_3dB']/1e6:.0f} MHz, {c02['pm_deg']:.0f}° / {c05['pm_deg']:.0f}° | "
                    f"{ng:.1f} vs {p['g_min']:g} |")
    text = "\n".join(rows)
    Path(out_md).write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main(sys.argv[1])
