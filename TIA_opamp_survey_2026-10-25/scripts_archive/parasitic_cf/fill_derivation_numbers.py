"""Bring the worked examples of the derivation (data/parasitic_cf/parasitic_cf_derivation.md)
in line with the sourced inputs of cf_parasitic_estimate.py: nominal 0402 body with a 0.20-mm
top termination (film length 0.60 mm) and the IPC-7351 land pattern (gap 0.40 mm, pad length
0.55 mm, pad width 0.60 mm), the permittivity ranges of Table P3, and a 0.2-mm guard strip.

Usage: python fill_derivation_numbers.py <derivation.md>

Each replacement must match the text exactly once; the script stops otherwise.  The numbers
written here are the ones printed by cf_parasitic_estimate.py and by the worked-example
evaluation recorded in the derivation.
"""
import sys
from pathlib import Path

PAIRS = [
    # Section 7.1
    ("For pads as long as the gap ($w = s$, as for an 0402 on its usual land pattern), $m = 1/4$, $K(1/4) = 1.685750$ and $K(3/4) = 2.156516$, so $K(m)/K(1 - m) = 0.781701$. Each unit of relative permittivity then contributes $0.781701\\times8.854188$ fF/mm = 6.92 fF/mm.",
     "For the IPC-7351 land pattern of an 0402 (Table P2: $w$ = 0.55 mm, $s$ = 0.40 mm), $m = (0.55/0.95)^2 = 0.335180$, $K(m) = 1.735059$ and $K(1 - m) = 2.026536$, so $K(m)/K(1 - m) = 0.856170$. Each unit of relative permittivity then contributes $0.856170\\times8.854188$ fF/mm = 7.58 fF/mm."),
    # Section 7.3
    ("For $w = s$ = 0.5 mm and $H$ = 1.6 mm:", "For the 0402 pads ($w$ = 0.55 mm, $s$ = 0.40 mm) and $H$ = 1.6 mm:"),
    ("- $\\pi w/2H = 0.490874$ and $\\pi(s + w)/2H = 0.981748$, so $m_H = 0.198264$.",
     "- $\\pi w/2H = 0.539961$ and $\\pi(s + w)/2H = 0.932660$, so $m_H = 0.278369$."),
    ("- The ratio $K(m_H)/K(1 - m_H)$ is 0.733581, against 0.781701 for the half-space: the lower bound is 6 % below the upper one.",
     "- The ratio $K(m_H)/K(1 - m_H)$ is 0.806931, against 0.856170 for the half-space: the lower bound is 5.8 % below the upper one."),
    # Section 8 worked example
    ("**An 0402 body.** With $L$ = 1.00 mm, $T$ = 0.35 mm and $a$ = 0.25 mm (so $g$ = 0.50 mm):",
     "**An 0402 body.** With the nominal values of Table P2, $L$ = 1.00 mm, $T$ = 0.35 mm and $a$ = 0.20 mm (so $g$ = 0.60 mm):"),
    ("- Then $K(m_b)g/L = 1.173024$, $\\sigma = 0.843412$ and $\\mu = 0.835335\\times0.843412^4 = 0.422689$.",
     "- Then $K(m_b)g/L = 1.407629$, $\\sigma = 0.909953$ and $\\mu = 0.835335\\times0.909953^4 = 0.572712$."),
    ("- With $K(1 - \\mu) = 1.925781$ and $K(\\mu) = 1.793591$, Eq. (P32) gives 0.536851 against $T/g = 0.700000$ from Eq. (P28).",
     "- With $K(1 - \\mu) = 1.796933$ and $K(\\mu) = 1.921129$, Eq. (P32) gives 0.467676 against $T/g = 0.583333$ from Eq. (P28)."),
    ("the block lies between $9.6\\times8.854188\\times0.5\\times0.536851$ = 22.8 fF and $9.6\\times8.854188\\times0.5\\times0.7$ = 29.7 fF.",
     "the block lies between $9.6\\times8.854188\\times0.5\\times0.467676$ = 19.9 fF and $9.6\\times8.854188\\times0.5\\times0.583333$ = 24.8 fF."),
    ("*Figure P4. The potential in an 0402 body ($L$ = 1.0 mm, $T$ = 0.35 mm, $g$ = 0.5 mm)",
     "*Figure P4. The potential in an 0402 body ($L$ = 1.0 mm, $T$ = 0.35 mm, $g$ = 0.6 mm)"),
    # Section 9
    ("The direction of this approximation is not fixed by the rules of Section 4, so its size is judged from the result: the air term is under 10 % of the total (Section 12).",
     "The direction of this approximation is not fixed by the rules of Section 4, so its size is judged from the result: the air term is about a tenth of the total (Section 12)."),
    ("For the 0402 ($g$ = 0.5 mm, $X$ = 0.75 mm) this is again $1/4$, because here $g = s$, and the ratio is 0.781701.",
     "For the 0402 ($g$ = 0.60 mm, $X$ = 0.75 mm), $m_{\\mathrm{air}} = (0.45/1.05)^2 = 0.183673$ and the ratio is 0.719288."),
    ("For the 0402, Eq. (P38) gives 0.821086, 5 % above the 0.781701 without the film.",
     "For the 0402, Eq. (P38) gives 0.760252, 5.7 % above the 0.719288 without the film."),
    # Figure P6 caption and Section 10.3
    ("and the pad $[u_1,u_2]$ with $u_1$ = 25.4 and $u_2 = 6.5\\times10^4$.*",
     "and the pad $[u_1,u_2]$ with $u_1$ = 11.6 and $u_2 = 6.5\\times10^4$.*"),
    ("For the 0402 pads ($w = s$ = 0.5 mm), per unit $\\varepsilon_{\\mathrm{pcb}}\\varepsilon_0$ and per millimetre of pad width:",
     "For the 0402 pads ($w$ = 0.55 mm, $s$ = 0.40 mm), per unit $\\varepsilon_{\\mathrm{pcb}}\\varepsilon_0$ and per millimetre of pad width:"),
    ("| 0.10 mm | 0.000 | 5.88 |", "| 0.10 mm | 0.001 | 6.38 |"),
    ("| 0.20 mm | 0.013 | 3.37 |", "| 0.20 mm | 0.028 | 3.61 |"),
    ("| 0.36 mm | 0.072 | 2.20 |", "| 0.36 mm | 0.112 | 2.31 |"),
    ("| no plane (Eq. (P25)) | 0.782 | 0 |", "| no plane (Eq. (P25)) | 0.856 | 0 |"),
    ("A plane at 0.2 mm therefore removes the board's 17 fF from across an 0402. It adds $3.37\\times4.2\\times8.854\\times0.6$ = 75 fF from each pad to ground.",
     "With $\\varepsilon_{\\mathrm{pcb}}$ = 4.2, a plane at 0.2 mm therefore removes 18.5 of the board's 19.1 fF from across an 0402. It adds $3.61\\times4.2\\times8.854\\times0.6$ = 80 fF from each pad to ground."),
    # Section 10.4
    ("For an 0402 ($A_f = gW$ = 0.25 mm², $\\varepsilon_{\\mathrm{al}}$ = 9.6, $\\varepsilon_{\\mathrm{pcb}}$ = 4.2) over a plane at 0.2 mm, with $t_s$ = 30 µm, $C_g$ is 19 fF with the film up and 28 fF with the film down, so the film term is −3.2 fF or −4.8 fF.",
     "For an 0402 ($A_f = gW$ = 0.30 mm², $\\varepsilon_{\\mathrm{al}}$ = 9.6, $\\varepsilon_{\\mathrm{pcb}}$ = 4.2) over a plane at 0.2 mm, with $t_s$ = 30 µm, $C_g$ is 23 fF with the film up and 34 fF with the film down, so the film term is −3.9 fF or −5.7 fF."),
    # Section 10.5
    ("For an 0402 with a 0.3-mm strip (0.1 mm clearance to each pad) and $t_s$ = 30 µm:",
     "For an 0402 with a 0.2-mm strip (0.1 mm clearance to each pad), $t_s$ = 30 µm and the middle permittivities of Table P3:"),
    ("- **Board coupling.** The board's contribution falls from 17.2 to 9.3 fF.",
     "- **Board coupling.** The board's contribution falls from 18.8 to 11.3 fF."),
    ("- **Film term.** It is −4.4 fF with the film up ($C_g$ = 20 fF) and −9.7 fF with the film down ($C_g$ = 44 fF).",
     "- **Film term.** It is −3.2 fF with the film up ($C_g$ = 13 fF) and −7.1 fF with the film down ($C_g$ = 30 fF)."),
    ("- **Cost.** The summing node gains 19 fF from its pad to the strip, plus $C_g/2$: 29 fF in all with the film up and 41 fF with it down.",
     "- **Cost.** The summing node gains 17 fF from its pad to the strip, plus $C_g/2$: 24 fF in all with the film up and 32 fF with it down."),
    # Section 10.6
    ("A plane at 0.2 mm, for example, adds 75 fF to $C_T$ = 2.15 pF (+3.5 %) to remove about 20 fF that must then be fitted back.",
     "A plane at 0.2 mm, for example, adds 80 fF to $C_T$ = 2.15 pF (+3.7 %) to remove about 22 fF that must then be fitted back."),
    # Section 10.7
    ("The gain is $(\\varepsilon_{\\mathrm{pcb}} - 1)\\varepsilon_0W$ times the 5 % film excess of Section 9.2, which is about 0.6 fF for an 0402.",
     "The gain is about $\\varepsilon_0W(\\varepsilon_{\\mathrm{pcb}}\\Delta_{\\mathrm{board}} - \\Delta_{\\mathrm{air}})$, where $\\Delta_{\\mathrm{board}}$ and $\\Delta_{\\mathrm{air}}$ are the excesses of Eq. (P38) over Eq. (P33) in the two half-planes, about 0.04 each; for an 0402 this is 0.6 fF."),
    ("so $C_g$ of Eqs. (P42) and (P44) grows: for the 0402 over a 0.3-mm guard, from 20 to 44 fF. The film term of Eq. (P10) grows from −4.4 to −9.7 fF.",
     "so $C_g$ of Eqs. (P42) and (P44) grows: for the 0402 over a 0.2-mm guard, from 13 to 30 fF. The film term of Eq. (P10) grows from −3.2 to −7.1 fF."),
    ("with more removed from across $R_F$ and more added to $C_T$ (41 instead of 29 fF).",
     "with more removed from across $R_F$ and more added to $C_T$ (32 instead of 24 fF)."),
    # Section 11
    ("The two bounds of the two-dimensional model are 15.6–19.0 fF without the middle pin and 17.6–21.3 fF with the wall, over the permittivity ranges of Section 3.",
     "The two bounds of the two-dimensional model are 14.9–18.7 fF without the middle pin and 16.7–21.0 fF with the wall, over the permittivity ranges of Table P3."),
    ("which is 2.2 fF for $t_{\\mathrm{wall}}$ = 0.1 mm and 4.5 fF for 0.2 mm.",
     "which is 2.1 fF for $t_{\\mathrm{wall}}$ = 0.1 mm and 4.3 fF for 0.2 mm, with $\\varepsilon_{\\mathrm m}$ = 4.0."),
    # Section 12 table
    ("| A7 | Air region flattened onto one plane | Not fixed | Air term 7–9 % of the total; film and no-film versions differ by 5 % |",
     "| A7 | Air region flattened onto one plane | Not fixed | Air term about a tenth of the total; film and no-film versions differ by 5–6 % |"),
    ("| A8 | Board as a half-space (upper) or a cut layer (lower) | Bracketed | Eq. (P27): 6 % apart for an 0402 on 1.6 mm |",
     "| A8 | Board as a half-space (upper) or a cut layer (lower) | Bracketed | Eq. (P27): 5.8 % apart for an 0402 on 1.6 mm |"),
    ("| Upper estimate (Rule 6) | 15.6–21.3 fF plus 2.2–4.5 fF |",
     "| Upper estimate (Rule 6) | 14.9–21.0 fF plus 2.1–4.3 fF |"),
    ("| A14 | Gap under the body ($t_s$) ignored except in Section 10 | Small | Tens of µm against gaps of 0.3–1 mm |",
     "| A14 | Gap under the body ($t_s$) ignored except in Section 10 | Small | Tens of µm against gaps of 0.3–1 mm |\n| A15 | Block thickness $T$ taken as the data sheets' overall height, which includes the terminations and coatings | Raises | The alumina is thinner by the termination metal, tens of µm; the tolerance band of Table P2 covers it |"),
    # Section 13.2
    ("For a 20-µm cut between regions 0.2 mm wide on alumina ($\\varepsilon_{\\mathrm{al}}$ = 9.9), $C'_{\\mathrm{cut}}$ = 136 fF/mm. A 0.6-mm cut across which half the voltage drops ($\\Delta\\varphi/V = 0.5$) then adds $136\\times0.6\\times0.25$ = 20 fF.",
     "For a 20-µm cut between regions 0.2 mm wide on alumina ($\\varepsilon_{\\mathrm{al}}$ = 10.0), $C'_{\\mathrm{cut}}$ = 137 fF/mm. A 0.6-mm cut across which half the voltage drops ($\\Delta\\varphi/V = 0.5$) then adds $137\\times0.6\\times0.25$ = 21 fF."),
]


def main():
    p = Path(sys.argv[1])
    t = p.read_text(encoding="utf-8")
    for old, new in PAIRS:
        n = t.count(old)
        if n != 1:
            raise SystemExit(f"expected one match, found {n}: {old[:90]!r}")
        t = t.replace(old, new)
    p.write_text(t, encoding="utf-8", newline="\n")
    print(f"{len(PAIRS)} replacements applied")


if __name__ == "__main__":
    main()
