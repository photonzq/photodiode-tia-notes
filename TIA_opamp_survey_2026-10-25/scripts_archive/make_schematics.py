"""Schematics of the balanced-photodiode TIA note (Figure 1, Figures 3 and 5 of Chapter 4, and Figures 27 onwards).

Every schematic uses schematic_style.py: one scale, one canvas width, white background.
Each function draws one figure and names the part values it shows; the values are those
of the note's text and tables, cited in the function's docstring.

Usage:  python make_schematics.py [OUT_DIR] [NAME ...]
        OUT_DIR defaults to ../figures; with names, only those figures are drawn.
"""
from __future__ import annotations

import sys
from pathlib import Path

import schematic_style as ss

HERE = Path(__file__).resolve().parent


def fig01_tia_circuit(out: Path) -> None:
    """Figure 1 (Section 1.3): the inverting TIA with the balanced photodiode pair and
    every capacitance that sets stability and noise.  Parasitic capacitances in grey,
    the optional DC servo dashed."""
    s = ss.Sheet()
    # balanced pair at x = 0: upper diode from the node (anode) to +V_B (cathode), lower
    # diode from -V_B (anode) to the node (cathode); both conduct photocurrent upwards
    s.photodiode((0.0, 0.35), (0.0, 1.65))
    s.photodiode((0.0, -1.65), (0.0, -0.35))
    s.wire((0.0, 1.65), (0.0, 2.1))
    s.supply((0.0, 2.1), "$+V_B$")
    s.wire((0.0, -1.65), (0.0, -2.1))
    s.supply((0.0, -2.1), "$-V_B$", up=False)
    s.wire((0.0, 0.35), (0.0, -0.35))
    s.dot((0.0, 0.0))
    s.arrow((0.5, 1.45), (0.5, 0.55))
    s.text((0.68, 1.0), "$i_1$", color=ss.CURRENT)
    s.arrow((0.5, -0.55), (0.5, -1.45))
    s.text((0.68, -1.0), "$i_2$", color=ss.CURRENT)

    # summing node and its capacitances to AC ground
    x_in = 11.2                                  # op amp's inverting input
    s.wire((0.0, 0.0), (x_in, 0.0))
    for x, name in ((1.7, r"$C_D$"), (3.6, r"$C_{\mathrm{PCB}}$"), (5.5, r"$C_{\mathrm{CM}}$")):
        s.dot((x, 0.0))
        s.cap((x, 0.0), (x, -1.4), name, color=ss.PARASITIC)
        s.ground((x, -1.4), color=ss.PARASITIC)
    # optional DC servo: a current sink from the node
    s.dot((7.4, 0.0))
    s.isource((7.4, 0.0), (7.4, -1.4), None, color=ss.OPTIONAL, dashed=True)
    s.ground((7.4, -1.4), color=ss.OPTIONAL)
    s.text((7.4, -2.05), "DC servo", ha="center", va="top", color=ss.OPTIONAL)

    # op amp; C_DIFF between its inputs; + input to V_REF
    op = s.opamp((x_in, 0.0), name="$A(s)$")
    x_cd = 9.7
    s.dot((x_cd, 0.0))
    s.cap((x_cd, 0.0), (x_cd, op.in2[1]), r"$C_{\mathrm{DIFF}}$", color=ss.PARASITIC)
    s.wire(op.in2, (x_cd, op.in2[1]))
    s.dot((x_cd, op.in2[1]))
    s.wire((x_cd, op.in2[1]), (x_cd, -1.9))
    s.terminal((x_cd, -1.9), r"$V_{\mathrm{REF}}$ (AC ground)", side="right")

    # feedback: R_F below, C_F above, from the output column back to the node
    x_fl, x_fr = 10.45, 14.4
    y_r, y_c = 1.35, 2.45
    s.dot((x_fl, 0.0))
    s.wire((x_fl, 0.0), (x_fl, y_c))
    s.dot((x_fl, y_r))
    s.res((x_fl, y_r), (x_fr, y_r), "$R_F$  1.5 or 2 kΩ", side="bottom")
    s.cap((x_fl, y_c), (x_fr, y_c), r"$C_F = C_{F,\mathrm{ext}} + C_{F,\mathrm{par}}$", side="top")
    s.wire((x_fr, y_c), (x_fr, op.out[1]))
    s.dot((x_fr, y_r))
    s.wire(op.out, (x_fr, op.out[1]))
    s.dot((x_fr, op.out[1]))
    s.text((x_fr + 0.15, op.out[1] - 0.3), "$v_o$", va="top")

    # optional 50-ohm back-termination into the instrument
    x_l = 16.7
    s.res((x_fr, op.out[1]), (x_l - 0.5, op.out[1]), "$R_S$  50 Ω", side="top")
    s.wire((x_l - 0.5, op.out[1]), (x_l, op.out[1]))
    s.res((x_l, op.out[1]), (x_l, -2.3), "50-Ω input\n(or high-Z)", side="right")
    s.ground((x_l, -2.3))
    s.save(out / "fig01_tia_circuit")


# ----------------------------------------------------------------- helpers --
def pd_pair(s: ss.Sheet, x: float = 0.0, supplies: bool = True, light: str = "left") -> None:
    """The balanced pair of Figure 1 at column x, summing node at y = 0: the upper diode
    from the node (anode) to +V_B, the lower from -V_B to the node (cathode)."""
    s.photodiode((x, 0.35), (x, 1.65), light=light)
    s.photodiode((x, -1.65), (x, -0.35), light=light)
    s.wire((x, 0.35), (x, -0.35))
    s.dot((x, 0.0))
    if supplies:
        s.wire((x, 1.65), (x, 2.1))
        s.supply((x, 2.1), "$+V_B$")
        s.wire((x, -1.65), (x, -2.1))
        s.supply((x, -2.1), "$-V_B$", up=False)


def single_pd(s: ss.Sheet, x: float = 0.0) -> None:
    """One photodiode, anode on the summing node (y = 0), cathode to +V_B."""
    s.photodiode((x, 0.35), (x, 1.65))
    s.wire((x, 0.35), (x, 0.0))
    s.wire((x, 1.65), (x, 2.1))
    s.supply((x, 2.1), "$+V_B$")


def tia(s: ss.Sheet, x_node0: float, x_in: float, x_fl: float, rf: str, cf: str | None,
        name: str | None = None, name_at: str = "below", y_r: float = 1.35, y_c: float = 2.45,
        vref: str | None = r"$V_{\mathrm{REF}}$", x_vref: float | None = None, out_ext: float = 0.75):
    """Inverting TIA: summing-node wire from x_node0 to the - input at x_in, R_F (and C_F
    above it) from the output column back to the node at x_fl, + input to a V_REF
    terminal.  Returns the op-amp element and the x of the output column."""
    op = s.opamp((x_in, 0.0), name=name, name_at=name_at)
    s.wire((x_node0, 0.0), op.in1)
    x_fr = op.out[0] + out_ext
    top = y_c if cf is not None else y_r
    s.dot((x_fl, 0.0))
    s.wire((x_fl, 0.0), (x_fl, top))
    s.res((x_fl, y_r), (x_fr, y_r), rf, side="bottom" if cf is not None else "top")
    if cf is not None:
        s.dot((x_fl, y_r))
        s.dot((x_fr, y_r))
        s.cap((x_fl, y_c), (x_fr, y_c), cf, side="top")
    s.wire((x_fr, top), (x_fr, op.out[1]))
    s.wire(op.out, (x_fr, op.out[1]))
    s.dot((x_fr, op.out[1]))
    if vref:
        xv = x_vref if x_vref is not None else x_in - 0.6
        s.wire(op.in2, (xv, op.in2[1]), (xv, -1.6))
        s.terminal((xv, -1.6), vref, side="bottom")
    return op, x_fr


# ------------------------------------------------------- Chapter 7 composites --
def fig21_discrete_composite(out: Path) -> None:
    """Section 7.1: common-source input transistor Q1 at the summing node, cascode Q2 with
    its gate at V_B2, R_D from V_DD = 15 V, compensation C_N at the drain, an ideal DC
    level shift into the OPA859 unity-gain buffer, R_F || C_F back to the summing node
    and a 200-ohm load.  Values of the CE3512K2 (pHEMT) design of Table A7.4 and of
    FET_DESIGN in composite_tia.py: R_D 1.1 kOhm (10 mA), V_B2 = 1.5 V, V_LS = 4.5 V,
    C_N 8 pF, C_F 0.55 pF.  R_g is the optional gate stopper of Eq. (63)."""
    s = ss.Sheet()
    pd_pair(s, 0.0)
    x_fb = 0.9
    s.wire((0.0, 0.0), (1.6, 0.0))
    s.dot((x_fb, 0.0))
    s.text((x_fb + 0.12, 0.12), "$v_g$", va="bottom")
    s.res((1.6, 0.0), (3.0, 0.0), "$R_g$ (optional)", side="bottom", color=ss.OPTIONAL, dashed=True)
    q1 = s.njfet((4.2, 0.0), mirror=True, name="Q1")
    s.wire((3.0, 0.0), q1.gate)
    s.wire(q1.source, (q1.source[0], -0.8))
    s.ground((q1.source[0], -0.8))
    q2 = s.njfet((4.2, 1.6), mirror=True, name="Q2")
    s.wire(q1.drain, q2.source)
    s.dot((q1.drain[0], 0.98))
    s.text((q1.drain[0] - 0.15, 0.98), "$v_x$", ha="right")
    # cascode gate at V_B2, bypassed
    s.wire(q2.gate, (3.3, 1.6))
    s.dot((3.3, 1.6))
    s.cap((3.3, 1.6), (3.3, 0.7), None)
    s.ground((3.3, 0.7))
    s.wire((3.3, 1.6), (2.5, 1.6))
    s.terminal((2.5, 1.6), "$V_{B2}$ 1.5 V", side="top")
    # drain: R_D to V_DD, C_N to ground, level shift into the buffer
    x_d = q2.drain[0]
    y_d = 2.7
    s.wire(q2.drain, (x_d, y_d))
    s.dot((x_d, y_d))
    s.text((x_d + 0.2, y_d - 0.12), "$v_d$", va="top")
    s.res((x_d, y_d), (x_d, 4.2), "$R_D$\n1.1 kΩ", side="left")
    s.supply((x_d, 4.2), "15 V")
    x_n = 6.5
    s.wire((x_d, y_d), (x_n, y_d))
    s.dot((x_n, y_d))
    s.cap((x_n, y_d), (x_n, 1.3), "$C_N$\n8 pF", side="right")
    s.ground((x_n, 1.3))
    s.vsource((9.4, y_d), (x_n + 0.6, y_d), "$V_{LS}$ 4.5 V", side="top")
    s.wire((x_n, y_d), (x_n + 0.6, y_d))
    o = s.buffer((9.4, y_d))
    s.text((10.4, y_d + 0.85), "OPA859", ha="center", va="bottom")
    x_o = o[0] + 0.5
    s.wire(o, (x_o, y_d))
    s.dot((x_o, y_d))
    s.text((x_o + 0.12, y_d + 0.12), "$v_o$", va="bottom")
    s.wire((x_o, y_d), (x_o + 0.9, y_d))
    s.res((x_o + 0.9, y_d), (x_o + 0.9, 1.0), "200 Ω", side="right")
    s.ground((x_o + 0.9, 1.0))
    # feedback R_F || C_F from v_o back to the summing node, over the top
    y_r, y_c = 5.6, 6.7
    s.wire((x_fb, 0.0), (x_fb, y_c))
    s.dot((x_fb, y_r))
    s.res((x_fb, y_r), (x_o, y_r), "$R_F$  2 kΩ", side="bottom")
    s.cap((x_fb, y_c), (x_o, y_c), "$C_F$  0.55 pF", side="top")
    s.wire((x_o, y_c), (x_o, y_d))
    s.dot((x_o, y_r))
    s.save(out / "fig21_discrete_composite")


def fig22_hv_composite(out: Path) -> None:
    """Section 7.2: the dual-feedback composite.  OPA859 (+ input grounded) at the summing
    node, THS3491 as a non-inverting stage of gain G_2 = 1 + R_F2/R_G2 inside the R_F
    loop, C_L from the OPA859's output back to the summing node, 100-ohm load.  Values of
    the G_2 = 5.5 design of Table A7.7: R_F2 568 ohm (R_G2 = 568/4.5 = 126 ohm), total
    C_F 0.100 pF with R_F split into two 1-kOhm resistors (Section 8.10), C_L 3.25 pF."""
    s = ss.Sheet()
    pd_pair(s, 0.0)
    x_in = 4.4
    op1 = s.opamp((x_in, 0.0), name="OPA859\n±2.5 V", name_at="below")
    s.wire((0.0, 0.0), op1.in1)
    s.wire(op1.in2, (3.9, op1.in2[1]), (3.9, -1.5))
    s.ground((3.9, -1.5))
    s.dot((3.9, op1.in2[1]))
    x_1 = op1.out[0] + 0.5                        # v_1 column
    s.wire(op1.out, (x_1, op1.out[1]))
    s.dot((x_1, op1.out[1]))
    s.text((x_1 + 0.05, op1.out[1] - 0.15), "$v_1$", va="top")
    # THS3491, non-inverting: + input level with v_1, - input below
    op2 = s.opamp((x_1 + 1.0, op1.out[1] - 0.9), minus_on_top=False, name="THS3491\n±15 V",
                  name_at="above")
    s.wire((x_1, op1.out[1]), op2.in2)
    x_2 = op2.out[0] + 0.5                        # v_2 column
    s.wire(op2.out, (x_2, op2.out[1]))
    s.dot((x_2, op2.out[1]))
    s.text((x_2 + 0.12, op2.out[1] - 0.15), "$v_2$", va="top")
    x_m = op2.in1[0] - 0.5
    s.wire(op2.in1, (x_m, op2.in1[1]), (x_m, -2.6))
    s.dot((x_m, -2.6))
    s.res((x_m, -2.6), (x_2, -2.6), "$R_{F2}$  568 Ω", side="bottom")
    s.wire((x_2, -2.6), (x_2, op2.out[1]))
    s.dot((x_2, -2.6))
    s.res((x_m, -2.6), (x_m, -4.0), "$R_{G2}$\n126 Ω", side="left")
    s.ground((x_m, -4.0))
    s.wire((x_2, op2.out[1]), (x_2 + 0.9, op2.out[1]))
    s.res((x_2 + 0.9, op2.out[1]), (x_2 + 0.9, -2.6), "100 Ω", side="right")
    s.ground((x_2 + 0.9, -2.6))
    # local loop C_L (v_1 to the node) and outer loop R_F || C_F (v_2 to the node)
    x_l, y_l = 3.1, 1.3
    s.dot((x_l, 0.0))
    s.wire((x_l, 0.0), (x_l, y_l))
    s.cap((x_l, y_l), (x_1, y_l), "$C_L$  3.25 pF", side="top")
    s.wire((x_1, y_l), (x_1, op1.out[1]))
    x_f, y_r, y_c = 1.9, 2.8, 4.0
    s.dot((x_f, 0.0))
    s.wire((x_f, 0.0), (x_f, y_c))
    s.dot((x_f, y_r))
    s.res((x_f, y_r), (0.5 * (x_f + x_2), y_r), None)
    s.res((0.5 * (x_f + x_2), y_r), (x_2, y_r), None)
    s.text((0.5 * (x_f + x_2), y_r + 0.42), "$R_F$  2 × 1 kΩ", ha="center", va="bottom")
    s.cap((x_f, y_c), (x_2, y_c), "$C_F$  0.100 pF (total)", side="top")
    s.wire((x_2, y_c), (x_2, op2.out[1]))
    s.dot((x_2, y_r))
    s.save(out / "fig22_hv_composite")


# ------------------------------------------------- Chapter 8: DC options A-D --
def fig23_option_a(out: Path) -> None:
    """Section 8.2, Option A: R_s from the summing node to a far end bypassed to ground,
    driven through an RC filter by a slow integrator that integrates v_o - V_set without
    inversion (sensed on its + input), so that the loop through the inverting TIA is
    negative.  R_s = V_S/I_DC (500 ohm at 10 mA for V_S = 5 V, Table A8.1); 10-nF bypass."""
    s = ss.Sheet()
    single_pd(s, 0.0)
    x_s = 1.9
    op, x_fr = tia(s, 0.0, 5.6, 4.8, "$R_F$", "$C_F$", x_vref=5.1)
    s.dot((x_s, 0.0))
    y_x = -3.3
    s.res((x_s, 0.0), (x_s, y_x), "$R_s = V_S/I_{\\mathrm{DC}}$\n500 Ω at 10 mA", side="left")
    s.dot((x_s, y_x))
    s.cap((x_s, y_x), (x_s, -4.6), "10 nF", side="left")
    s.ground((x_s, -4.6))
    # output and the servo below the TIA, its integrator facing left
    s.wire((x_fr, op.out[1]), (x_fr + 0.8, op.out[1]))
    s.terminal((x_fr + 0.8, op.out[1]), "$v_o$")
    y_p = -2.85                                  # integrator's + input row
    s.wire((x_fr, op.out[1]), (x_fr, y_p))
    u2 = s.opamp((x_fr - 0.6, y_p - 0.9), minus_on_top=False, left=True, name="integrator",
                 name_at="above")
    s.wire((x_fr, y_p), u2.in2)
    s.res((x_fr + 1.6, u2.in1[1]), u2.in1, "$R_i$", side="bottom")
    s.terminal((x_fr + 1.6, u2.in1[1]), "$V_{set}$")
    x_ci = u2.in1[0] + 0.3
    s.dot((x_ci, u2.in1[1]))
    s.wire((x_ci, u2.in1[1]), (x_ci, -5.0))
    s.cap((x_ci, -5.0), (u2.out[0], -5.0), "$C_i$", side="bottom")
    s.wire((u2.out[0], -5.0), u2.out)
    s.dot(u2.out)
    s.res(u2.out, (x_s, y_x), "RC filter", side="top")
    s.save(out / "fig23_option_a")


def fig24_option_b(out: Path) -> None:
    """Section 8.3, Option B: the photodiode's DC through R_b from its anode to a negative
    bias, the RF through C_c into the TIA.  R_b 500 ohm (5 V at 10 mA), C_c 10 nF (32 kHz
    with R_b)."""
    s = ss.Sheet()
    s.photodiode((0.0, 0.35), (0.0, 1.65))
    s.wire((0.0, 1.65), (0.0, 2.1))
    s.supply((0.0, 2.1), "$+V_B$")
    s.wire((0.0, 0.35), (0.0, 0.0))
    s.dot((0.0, 0.0))
    s.res((0.0, 0.0), (0.0, -1.7), "$R_b$\n500 Ω", side="left")
    s.supply((0.0, -1.7), "$-V_{\\mathrm{bias}}$", up=False)
    s.wire((0.0, 0.0), (0.8, 0.0))
    s.cap((0.8, 0.0), (2.4, 0.0), "$C_c$  10 nF", side="top")
    op, x_fr = tia(s, 2.4, 4.6, 3.8, "$R_F$", "$C_F$")
    s.wire((x_fr, op.out[1]), (x_fr + 0.8, op.out[1]))
    s.terminal((x_fr + 0.8, op.out[1]), "$v_o$")
    s.save(out / "fig24_option_b")


def fig25_option_c(out: Path) -> None:
    """Section 8.4, Option C: a choke L_ch (1 uH) between the summing node and the sink,
    which is still a resistor R_s to a bypassed servo voltage as in Option A; the choke's
    self-capacitance (0.1-0.5 pF) in grey."""
    s = ss.Sheet()
    single_pd(s, 0.0)
    x_l = 1.7
    s.dot((x_l, 0.0))
    s.ind((x_l, 0.0), (x_l, -1.6), "$L_{\\mathrm{ch}}$\n1 µH", side="left")
    s.dot((x_l, -0.2))
    s.dot((x_l, -1.4))
    s.wire((x_l, -0.2), (x_l + 0.8, -0.2))
    s.cap((x_l + 0.8, -0.2), (x_l + 0.8, -1.4), "0.1–0.5 pF", side="right", color=ss.PARASITIC)
    s.wire((x_l + 0.8, -1.4), (x_l, -1.4))
    s.res((x_l, -1.6), (x_l, -3.2), "$R_s$", side="left")
    s.terminal((x_l, -3.2), "to the bypassed far end\nand servo of Option A", side="right")
    op, x_fr = tia(s, 0.0, 5.6, 4.8, "$R_F$", "$C_F$")
    s.wire((x_fr, op.out[1]), (x_fr + 0.8, op.out[1]))
    s.terminal((x_fr + 0.8, op.out[1]), "$v_o$")
    s.save(out / "fig25_option_c")


def fig26_option_d(out: Path) -> None:
    """Section 8.5, Option D: a first TIA with R_F1 = 286 ohm carries the DC (OPA856, C_F1
    1.6 pF), then an AC-coupled voltage stage of gain G_2 = 7 (OPA855), R_F1 G_2 = 2 kOhm."""
    s = ss.Sheet()
    single_pd(s, 0.0)
    op, x_fr = tia(s, 0.0, 2.4, 1.6, "$R_{F1}$  286 Ω", "$C_{F1}$  1.6 pF", name="OPA856",
                   name_at="below")
    s.cap((x_fr, op.out[1]), (x_fr + 1.8, op.out[1]), "$C_c$", side="top")
    x_b = x_fr + 2.4
    s.wire((x_fr + 1.8, op.out[1]), (x_b, op.out[1]))
    s.dot((x_fr + 2.0, op.out[1]))
    s.res((x_fr + 2.0, op.out[1]), (x_fr + 2.0, -2.2), "DC\nreturn", side="left")
    s.ground((x_fr + 2.0, -2.2))
    o = s.buffer((x_b, op.out[1]), text="×7")
    s.text((x_b + 1.0, op.out[1] + 0.85), "OPA855, $G_2$ = 7", ha="center", va="bottom")
    s.wire(o, (o[0] + 0.6, o[1]))
    s.terminal((o[0] + 0.6, o[1]), "$v_o$")
    s.save(out / "fig26_option_d")


# ------------------------------------------- Chapter 8: bootstrap and cascode --
def fig27_bootstrap(out: Path) -> None:
    """Section 8.6: a unity-gain follower whose input is the summing node drives the far
    (bias-side) terminal of the photodiode through C_c, so the voltage across C_D stays
    constant; R_B feeds the DC bias.  Bipolar follower at 1 mA (Table A8.4)."""
    s = ss.Sheet()
    s.photodiode((0.0, 0.35), (0.0, 1.65))
    s.wire((0.0, 0.35), (0.0, 0.0))
    s.dot((0.0, 0.0))
    y_b = 2.4
    s.wire((0.0, 1.65), (0.0, y_b))
    s.dot((0.0, y_b))
    s.res((0.0, y_b), (0.0, 4.0), "$R_B$", side="left")
    s.supply((0.0, 4.0), "$+V_B$")
    x_cd = 1.0
    s.wire((0.0, y_b), (x_cd, y_b))
    s.dot((x_cd, y_b))
    s.dot((x_cd, 0.0))
    s.cap((x_cd, 0.0), (x_cd, y_b), "$C_D$", side="right", color=ss.PARASITIC)
    s.cap((x_cd, y_b), (2.6, y_b), "$C_c$", side="bottom")
    x_in = 5.1
    o = s.buffer((x_in, y_b), left=True)
    s.wire(o, (2.6, y_b))
    s.text((x_in - 1.0, y_b + 0.85), "follower, bipolar, 1 mA", ha="center", va="bottom")
    s.dot((x_in, 0.0))
    s.wire((x_in, 0.0), (x_in, y_b))
    op, x_fr = tia(s, 0.0, 6.9, 6.1, "$R_F$", "$C_F$", y_r=3.4, y_c=4.5)
    s.wire((x_fr, op.out[1]), (x_fr + 0.8, op.out[1]))
    s.terminal((x_fr + 0.8, op.out[1]), "$v_o$")
    s.save(out / "fig27_bootstrap")


def fig28_cascode(out: Path) -> None:
    """Section 8.7: a common-base PNP between the upper photodiode and the summing node,
    a common-base NPN between the node and the lower photodiode, bases AC-grounded at
    their bias; optional standing currents I_q through R_q = V_q/I_q from +-12 V
    (Table A8.6); the node sees the collector-base capacitances, 2 C_mu (grey)."""
    s = ss.Sheet()
    qa = s.pnp((-0.541, 1.2), name="$Q_A$")
    s.wire(qa.collector, (0.0, 0.0))
    e1 = (0.0, 2.2)
    s.wire(qa.emitter, e1)
    s.dot(e1)
    s.photodiode(e1, (0.0, 3.5))
    s.wire((0.0, 3.5), (0.0, 3.9))
    s.supply((0.0, 3.9), "$+V_B$")
    qb = s.npn((-0.541, -1.2), name="$Q_B$")
    s.wire(qb.collector, (0.0, 0.0))
    e2 = (0.0, -2.2)
    s.wire(qb.emitter, e2)
    s.dot(e2)
    s.photodiode((0.0, -3.5), e2)
    s.wire((0.0, -3.5), (0.0, -3.9))
    s.supply((0.0, -3.9), "$-V_B$", up=False)
    s.dot((0.0, 0.0))
    # bases at their bias, bypassed to ground
    for q, y, txt in ((qa, 1.2, "bias"), (qb, -1.2, "bias")):
        s.wire(q.base, (-1.5, y))
        s.dot((-1.5, y))
        s.cap((-1.5, y), (-1.5, y - 1.0), None)
        s.ground((-1.5, y - 1.0))
        s.wire((-1.5, y), (-2.2, y))
        s.terminal((-2.2, y), txt, side="left")
    # optional standing currents into the emitter nodes
    s.wire(e1, (1.3, e1[1]))
    s.res((1.3, e1[1]), (1.3, 3.7), "$R_q$", side="right", color=ss.OPTIONAL, dashed=True)
    s.supply((1.3, 3.7), "+12 V", color=ss.OPTIONAL)
    s.wire(e2, (1.3, e2[1]))
    s.res((1.3, e2[1]), (1.3, -3.7), "$R_q$", side="right", color=ss.OPTIONAL, dashed=True)
    s.supply((1.3, -3.7), "−12 V", up=False, color=ss.OPTIONAL)
    # the node's remaining capacitance and the TIA
    s.dot((2.3, 0.0))
    s.cap((2.3, 0.0), (2.3, -1.4), "$2C_\\mu$", side="right", color=ss.PARASITIC)
    s.ground((2.3, -1.4), color=ss.PARASITIC)
    op, x_fr = tia(s, 0.0, 5.0, 4.2, "$R_F$", "$C_F$", y_r=1.6, y_c=2.7)
    s.wire((x_fr, op.out[1]), (x_fr + 0.8, op.out[1]))
    s.terminal((x_fr + 0.8, op.out[1]), "$v_o$")
    s.save(out / "fig28_cascode")


# -------------------------------------------------------- Chapter 8: servos --
def fig29_optical_servo(out: Path) -> None:
    """Section 8.8 (b): a slow integrator nulls the TIA's DC output by trimming a tunable
    optical splitter (for example a thermo-optic Mach-Zehnder) ahead of the two diodes."""
    s = ss.Sheet()
    pd_pair(s, 0.0, light="none")
    # splitter block and the two optical paths to the diodes
    x0, x1 = -4.6, -2.2
    s.box(x0, -1.6, x1, 1.6, "tunable\nsplitter", color=ss.LIGHT)
    s.arrow((x0 - 1.5, 0.0), (x0, 0.0), color=ss.LIGHT)
    s.text((x0 - 0.75, 0.15), "light", ha="center", va="bottom", color=ss.LIGHT)
    for y in (1.0, -1.0):
        s.arrow((x1, y), (-0.4, y), color=ss.LIGHT)
    op, x_fr = tia(s, 0.0, 3.4, 2.6, "$R_F$", "$C_F$", x_vref=2.9)
    s.wire((x_fr, op.out[1]), (x_fr + 0.8, op.out[1]))
    s.terminal((x_fr + 0.8, op.out[1]), "$v_o$")
    # integrator below, driving the splitter's heater
    y_s = -3.6
    s.wire((x_fr, op.out[1]), (x_fr, y_s))
    s.res((x_fr, y_s), (x_fr - 1.8, y_s), "RC", side="top")
    s.box(x_fr - 5.2, y_s - 0.7, x_fr - 1.8, y_s + 0.7, "slow integrator\nset point $V_{\\mathrm{REF}}$")
    s.wire((x_fr - 5.2, y_s), (0.5 * (x0 + x1), y_s), (0.5 * (x0 + x1), -1.6))
    s.text((0.5 * (x0 + x1) + 0.15, -2.4), "heater", va="center")
    s.save(out / "fig29_optical_servo")


def fig30_current_splitter(out: Path) -> None:
    """Section 8.8 (c), the topology of Hobbs' Fig. 3 applied to the pair: the lower diode,
    made slightly stronger, feeds the common emitters of Q1/Q2; Q2 delivers the fraction f
    to the summing node, Q1 returns 1 - f to a supply; the servo drives Q1's base through a
    divider of at least 20:1 with an RF bypass, Q2's base sits at a bypassed bias; a
    matching common-base PNP Q3 on the upper diode (Table A8.10)."""
    s = ss.Sheet()
    # upper diode through the matching cascode Q3
    q3 = s.pnp((-0.541, 1.2), name="Q3")
    s.wire(q3.collector, (0.0, 0.0))
    e1 = (0.0, 2.2)
    s.wire(q3.emitter, e1)
    s.photodiode(e1, (0.0, 3.5))
    s.wire((0.0, 3.5), (0.0, 3.9))
    s.supply((0.0, 3.9), "$+V_B$")
    s.wire(q3.base, (-1.4, 1.2))
    s.dot((-1.4, 1.2))
    s.cap((-1.4, 1.2), (-1.4, 0.2), None)
    s.ground((-1.4, 0.2))
    s.wire((-1.4, 1.2), (-2.0, 1.2))
    s.terminal((-2.0, 1.2), "bias", side="left")
    # Q2 delivers f I_2 to the node; Q1 returns (1 - f) I_2 to the supply
    q2 = s.npn((0.541, -1.2), mirror=True, name="Q2", side="left")
    s.wire(q2.collector, (0.0, 0.0))
    s.dot((0.0, 0.0))
    q1 = s.npn((-3.0, -1.2))
    s.text((q1.center[0] - 0.62, q1.center[1] + 0.5), "Q1", ha="right")
    s.wire(q1.collector, (q1.collector[0], -0.4))
    s.supply((q1.collector[0], -0.4), "$+V_{CC}$")
    y_e = -2.3
    s.wire(q1.emitter, (q1.emitter[0], y_e), (0.0, y_e), q2.emitter)
    s.dot((0.0, y_e))
    s.photodiode((0.0, -3.7), (0.0, y_e))
    s.wire((0.0, -3.7), (0.0, -4.1))
    s.supply((0.0, -4.1), "$-V_B$", up=False)
    s.wire(q2.base, (1.4, -1.2))
    s.dot((1.4, -1.2))
    s.cap((1.4, -1.2), (1.4, -2.3), None)
    s.ground((1.4, -2.3))
    s.wire((1.4, -1.2), (2.1, -1.2))
    s.terminal((2.1, -1.2), "bias", side="bottom")
    # divider and RF bypass at Q1's base, fed by the servo
    x_d = -4.2
    s.wire(q1.base, (x_d, -1.2))
    s.dot((x_d, -1.2))
    s.res((x_d, -1.2), (x_d, -2.8), None)
    s.ground((x_d, -2.8))
    s.dot((x_d - 0.9, -1.2))
    s.cap((x_d - 0.9, -1.2), (x_d - 0.9, -2.3), None)
    s.ground((x_d - 0.9, -2.3))
    s.res((x_d - 0.9, -1.2), (x_d - 2.6, -1.2), "≥ 20:1\ndivider", side="top")
    s.wire((x_d, -1.2), (x_d - 0.9, -1.2))
    # TIA and the servo integrator below
    op, x_fr = tia(s, 0.0, 4.6, 3.8, "$R_F$", "$C_F$", x_vref=4.1)
    s.wire((x_fr, op.out[1]), (x_fr + 0.8, op.out[1]))
    s.terminal((x_fr + 0.8, op.out[1]), "$v_o$")
    y_s = -5.4
    s.wire((x_fr, op.out[1]), (x_fr, y_s))
    s.res((x_fr, y_s), (x_fr - 1.8, y_s), "RC", side="top")
    s.box(x_fr - 5.2, y_s - 0.7, x_fr - 1.8, y_s + 0.7, "servo integrator\nset point $V_{\\mathrm{REF}}$")
    x_w = x_d - 2.6
    s.wire((x_fr - 5.2, y_s), (x_w, y_s), (x_w, -1.2))
    s.save(out / "fig30_current_splitter")


def fig31_front_end(out: Path) -> None:
    """Section 8.9 and Table A8.10: the proposed balanced front end.  Each bias pin is fed
    from a linear regulator through bulk capacitance, a ferrite bead and a 100-ohm monitor
    resistor to one 10-nF low-inductance capacitor at the pin; both diodes at the summing
    node; OPA855 (A, 5 V, V_REF 2.58 V) or OPA818 (B, +-6.5 V, V_REF 0.1 V); R_F 2 kOhm;
    total C_F 0.25 pF (A) or 0.55 pF (B); the electronic imbalance servo of Section 8.8 (d):
    sensing through 1 kOhm / 1 nF, integrator on +-12 V with tau = 13 us, injection through
    3.3 kOhm into 10 nF || 100 pF and R_s = 24 kOhm; a second-order low-pass at 200-250 MHz."""
    s = ss.Sheet()
    x_p = 5.4                                   # photodiode column
    s.photodiode((x_p, 0.35), (x_p, 1.65))
    s.photodiode((x_p, -1.65), (x_p, -0.35))
    s.wire((x_p, 0.35), (x_p, -0.35))
    s.dot((x_p, 0.0))
    for sg, lab, mon in ((1, "$+V_B$", "$I_1$"), (-1, "$-V_B$", "$I_2$")):
        y = 2.7 * sg
        s.wire((x_p, 1.65 * sg), (x_p, y))
        s.terminal((-0.6, y), lab, side="left")
        s.wire((-0.6, y), (0.3, y))
        s.dot((0.3, y))
        s.cap((0.3, y), (0.3, y - 1.2), "bulk", side="left")
        s.ground((0.3, y - 1.2))
        s.bead((0.3, y), (1.5, y), "FB", side="bottom")
        s.wire((1.5, y), (2.1, y))
        s.res((2.1, y), (3.7, y), "100 Ω", side="top")
        s.dot((2.1, y))
        s.dot((3.7, y))
        for xm in (2.1, 3.7):
            s.wire((xm, y), (xm, y + 0.8))
            s.terminal((xm, y + 0.8), None)
        s.text((2.9, y + 1.1), mon + " monitor", ha="center", va="bottom")
        s.wire((3.7, y), (x_p, y))
        s.dot((4.1, y))
        s.cap((4.1, y), (4.1, y - 1.2), "10 nF", side="left")
        s.ground((4.1, y - 1.2))
    # the TIA
    op, x_fr = tia(s, x_p, 10.2, 9.4, "$R_F$  2 kΩ", "$C_F$  0.25 pF (A), 0.55 pF (B)",
                   name="OPA855 (A)\nor OPA818 (B)", name_at="below", vref=None)
    s.wire(op.in2, (9.8, op.in2[1]), (9.8, -1.5))
    s.terminal((9.8, -1.5), "$V_{\\mathrm{REF}}$", side="left")
    # post-filter and output
    s.wire((x_fr, op.out[1]), (x_fr + 0.5, op.out[1]))
    s.box(x_fr + 0.5, op.out[1] - 0.75, x_fr + 3.0, op.out[1] + 0.75, "low-pass\n200–250 MHz")
    s.wire((x_fr + 3.0, op.out[1]), (x_fr + 3.5, op.out[1]))
    s.terminal((x_fr + 3.5, op.out[1]), "to ADC")
    # the imbalance servo below: sense, integrate, inject
    y_s = -4.6
    s.wire((x_fr, op.out[1]), (x_fr, y_s))
    s.res((x_fr, y_s), (x_fr - 1.7, y_s), "1 kΩ", side="top")
    s.dot((x_fr - 1.7, y_s))
    s.cap((x_fr - 1.7, y_s), (x_fr - 1.7, y_s - 1.2), "1 nF", side="right")
    s.ground((x_fr - 1.7, y_s - 1.2))
    s.box(x_fr - 5.3, y_s - 0.7, x_fr - 2.3, y_s + 0.7, "integrator, ±12 V\n$\\tau$ = 13 µs")
    s.wire((x_fr - 1.7, y_s), (x_fr - 2.3, y_s))
    x_x = 6.3
    s.res((x_fr - 5.3, y_s), (x_x + 0.0, y_s), "3.3 kΩ", side="top")
    s.dot((x_x, y_s))
    s.cap((x_x, y_s), (x_x, y_s - 1.3), "10 nF\n$\\parallel$ 100 pF", side="left")
    s.ground((x_x, y_s - 1.3))
    s.res((x_x, y_s), (x_x, 0.0), "$R_s$\n24 kΩ", side="right")
    s.dot((x_x, 0.0))
    s.save(out / "fig31_front_end")


# ----------------------------------------------------- Chapter 4 design examples --
def case_schematic(out: Path, stem: str, part: str, c_cm: str, c_diff: str, cf_ext: str | None,
                   r_l: str, vs: str) -> None:
    """One of the two designs of Chapter 4 (Table 4.1) as simulated: the balanced pair with
    its bias pins decoupled by 10 nF, 1 pF of photodiode capacitance and 0.35 pF of board at
    the summing node, the amplifier's input capacitances, R_F = 2 kOhm, the parasitic 0.20 pF
    across it and, for OPA846, a 0.55-pF capacitor; split supplies with the non-inverting
    input grounded; the load R_L of the small-signal runs.  Parasitics in grey."""
    s = ss.Sheet()
    # balanced pair at x = 0, summing node at y = 0; each bias pin decoupled to the left,
    # clear of the light arrows
    s.photodiode((0.0, 0.35), (0.0, 1.65))
    s.photodiode((0.0, -1.65), (0.0, -0.35))
    s.wire((0.0, 0.35), (0.0, -0.35))
    s.dot((0.0, 0.0))
    for sg, lab in ((1, "$+V_B$"), (-1, "$-V_B$")):
        y = 2.15 * sg
        s.wire((0.0, 1.65 * sg), (0.0, 2.75 * sg))
        s.supply((0.0, 2.75 * sg), lab, up=sg > 0)
        s.dot((0.0, y))
        s.cap((0.0, y), (-1.5, y), "10 nF", side="top")
        s.ground((-1.5, y))
    # capacitances from the summing node to AC ground, labels in two lines to the right
    x_in, x_cd = 11.8, 10.6
    s.wire((0.0, 0.0), (x_in, 0.0))
    for x, name, value in ((2.1, "$C_D$", "1 pF"), (4.6, "$C_{\\mathrm{PCB}}$", "0.35 pF"),
                           (7.1, "$C_{\\mathrm{CM}}$", c_cm)):
        s.dot((x, 0.0))
        s.cap((x, 0.0), (x, -1.4), None, color=ss.PARASITIC)
        s.text((x + 0.38, -0.7), f"{name}\n{value}", ha="left", va="center", color=ss.PARASITIC)
        s.ground((x, -1.4), color=ss.PARASITIC)
    op = s.opamp((x_in, 0.0))
    s.dot((x_cd, 0.0))
    s.cap((x_cd, 0.0), (x_cd, op.in2[1]), None, color=ss.PARASITIC)
    s.text((x_cd - 0.65, -0.6), f"$C_{{\\mathrm{{DIFF}}}}$\n{c_diff}", ha="right", va="center", color=ss.PARASITIC)
    s.wire(op.in2, (x_cd, op.in2[1]))
    s.dot((x_cd, op.in2[1]))
    s.wire((x_cd, op.in2[1]), (x_cd, -1.75))
    s.ground((x_cd, -1.75))
    # supplies, and the part's name below its inputs
    s.wire(op.vd, (op.vd[0], op.vd[1] + 0.45))
    s.supply((op.vd[0], op.vd[1] + 0.45), f"+{vs}", side="right")
    s.wire(op.vs, (op.vs[0], op.vs[1] - 0.45))
    s.supply((op.vs[0], op.vs[1] - 0.45), f"−{vs}", up=False, side="right")
    s.text((op.vs[0] - 0.42, op.vs[1] - 0.45), part, ha="right", va="center")
    # feedback: R_F, then the capacitors above it, 1.3 units apart
    x_fl, x_fr = x_in - 0.6, op.out[0] + 0.8
    y_r, dy = 1.75, 1.3
    caps = [(None, cf_ext)] if cf_ext else []
    caps.append((ss.PARASITIC, "$C_{F,\\mathrm{par}}$  0.20 pF" + ("" if cf_ext else "  (no capacitor fitted)")))
    top = y_r + dy * len(caps)
    s.dot((x_fl, 0.0))
    s.wire((x_fl, 0.0), (x_fl, top))
    s.dot((x_fl, y_r))
    s.res((x_fl, y_r), (x_fr, y_r), "$R_F$  2 kΩ", side="top")
    for k, (color, lab) in enumerate(caps):
        y = y_r + dy * (k + 1)
        if k < len(caps) - 1:
            s.dot((x_fl, y))
            s.dot((x_fr, y))
        s.cap((x_fl, y), (x_fr, y), lab, side="top", color=color)
    s.dot((x_fr, y_r))
    s.wire((x_fr, top), (x_fr, op.out[1]))
    s.wire(op.out, (x_fr, op.out[1]))
    s.dot((x_fr, op.out[1]))
    s.text((x_fr + 0.15, op.out[1] - 0.3), "$v_o$", va="top")
    # load
    x_l = x_fr + 1.6
    s.wire((x_fr, op.out[1]), (x_l, op.out[1]))
    s.res((x_l, op.out[1]), (x_l, op.out[1] - 2.0), f"$R_L$  {r_l}", side="right")
    s.ground((x_l, op.out[1] - 2.0))
    s.save(out / stem)


def fig32_case_opa855(out: Path) -> None:
    """Section 4.2, Table 4.1: OPA855, C_CM 0.6 pF, C_DIFF 0.2 pF; no feedback capacitor, the
    0.20 pF of R_F and its pads alone; +-2.5 V (the 5-V supply); R_L 200 ohm."""
    case_schematic(out, "fig32_case_opa855_schematic", "OPA855", "0.6 pF", "0.2 pF", None, "200 Ω", "2.5 V")


def fig34_case_opa846(out: Path) -> None:
    """Section 4.4, Table 4.1: OPA846, C_CM 1.8 pF, C_DIFF 2.0 pF; 0.55 pF fitted across R_F,
    0.75 pF in total; +-5 V; R_L 100 ohm."""
    case_schematic(out, "fig34_case_opa846_schematic", "OPA846", "1.8 pF", "2.0 pF",
                   "$C_{F,\\mathrm{ext}}$  0.55 pF", "100 Ω", "5 V")


FIGURES = {f.__name__: f for f in (
    fig01_tia_circuit, fig21_discrete_composite, fig22_hv_composite, fig23_option_a,
    fig24_option_b, fig25_option_c, fig26_option_d, fig27_bootstrap, fig28_cascode,
    fig29_optical_servo, fig30_current_splitter, fig31_front_end, fig32_case_opa855,
    fig34_case_opa846)}


def main(argv: list[str]) -> None:
    ss.configure()
    out = Path(argv[1]) if len(argv) > 1 else HERE.parent / "figures"
    names = argv[2:] or list(FIGURES)
    for name in names:
        FIGURES[name](out)
        print("drawn", name)


if __name__ == "__main__":
    main(sys.argv)
