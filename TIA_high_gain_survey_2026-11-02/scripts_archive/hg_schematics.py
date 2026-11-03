"""Schematics of the high-gain TIA note, in the shared style of schematic_style.py (one
scale, one canvas width, white background).  Each function draws one figure; its docstring
names the section and the values it shows.  Written to ../figures/ as 600-dpi PNG and PDF.

  schem_tia_noise         Figure 1   (Section 1.1) the circuit, its parasitics and noise sources
  schem_rc_line           Figure 4   (Section 3.4) the feedback resistor as an RC line
  schem_guard_drives      Figure 6   (Section 3.4) driving the conductor beneath the resistor
  schem_split_resistor    Figure 7   (Section 3.4) a split resistor with guarded junctions
  schem_equalizer         Figure 8   (Section 3.5) equalization and its calibration
  schem_t_network         Figure 9   (Section 3.5) T-network against a voltage stage
  schem_jfet_composite    Figure 12  (Section 5.8) the discrete-JFET composite of Section 9.5
  schem_gain_ranging      Figure 13  (Section 7.1) gain ranging with T-switches
  schem_log_amp           Figure 14  (Section 7.2) the transdiode logarithmic amplifier
  schem_integrator        Figure 15  (Section 7.3) the switched integrator
  schem_optical_reset     Figure 16  (Section 7.3) optical reset of a charge-sensitive amplifier

Usage:  python hg_schematics.py [OUT_DIR] [NAME ...]
"""
from __future__ import annotations

import sys
from pathlib import Path

import schematic_style as ss

FIG = Path(__file__).resolve().parent.parent / "figures"


def tia(s: ss.Sheet, x_node0: float, x_in: float, x_fl: float, rf: str, cf: str | None,
        y_r: float = 1.35, y_c: float = 2.45, ground_plus: bool = True, x_plus: float | None = None,
        out_ext: float = 0.75, name: str | None = None, name_at: str = "below"):
    """Inverting TIA: summing-node wire from x_node0 to the - input at x_in, R_F (and C_F
    above it) from the output column back to the node at x_fl, + input grounded.
    Returns the op-amp element and the x of the output column."""
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
    if ground_plus:
        xp = x_plus if x_plus is not None else x_in - 0.5
        s.wire(op.in2, (xp, op.in2[1]), (xp, -1.6))
        s.ground((xp, -1.6))
    return op, x_fr


def pd_down(s: ss.Sheet, x: float = 0.0, bias: str = "0 V", label: str | None = None) -> None:
    """Photodiode from the summing node (anode, y = 0) down to a bias terminal (cathode)."""
    s.wire((x, 0.0), (x, -0.35))
    s.photodiode((x, -0.35), (x, -1.65))
    s.wire((x, -1.65), (x, -2.0))
    if bias == "ground":
        s.ground((x, -2.0))
    else:
        s.supply((x, -2.0), bias, up=False)
    if label:
        s.text((x + 0.42, -1.0), label)
    s.dot((x, 0.0))


def out_terminal(s: ss.Sheet, x_fr: float, y: float, text: str = "$V_{out}$", length: float = 0.8):
    s.wire((x_fr, y), (x_fr + length, y))
    s.terminal((x_fr + length, y), text)


def panel_label(s: ss.Sheet, p, text: str) -> None:
    s.text(p, text, ha="left", va="top")


# ------------------------------------------------------------- Section 1.1 --
def schem_tia_noise(out: Path) -> None:
    """Figure 1: the inverting TIA with the photodiode as current source, C_D and R_sh, the
    board and amplifier capacitances (grey), R_F with C_F = C_par (+ C_add), and the noise
    sources of Eq. (8) (purple): i_R of R_F, i_PD of the photodiode (thermal and shot),
    the amplifier's i_n at the summing node and e_n between its + input pin and the amplifier.
    C_DIFF runs from the inverting input to the grounded non-inverting pin, which is why it adds
    to C_CM in the summing node's capacitance."""
    s = ss.Sheet()
    pd_down(s, 0.0, bias="0 V or $V_B$")
    s.arrow((0.5, -1.45), (0.5, -0.55))
    s.text((0.68, -1.0), "$I_{ph}$", color=ss.CURRENT)
    x_in = 14.1
    for x, lab in ((1.8, "$C_D$"), (3.3, "$R_{sh}$")):
        s.dot((x, 0.0))
        if lab == "$R_{sh}$":
            s.res((x, 0.0), (x, -1.4), lab, color=ss.PARASITIC)
        else:
            s.cap((x, 0.0), (x, -1.4), lab, color=ss.PARASITIC)
        s.ground((x, -1.4), color=ss.PARASITIC)
    for x, lab in ((5.0, "$i_{PD}$"), (7.0, "$i_n$")):
        s.dot((x, 0.0))
        s.isource((x, 0.0), (x, -1.6), lab, color=ss.NOISE)
        s.ground((x, -1.6), color=ss.NOISE)
    for x, lab in ((8.8, "$C_{PCB}$"), (10.6, "$C_{CM}$")):
        s.dot((x, 0.0))
        s.cap((x, 0.0), (x, -1.4), lab, color=ss.PARASITIC)
        s.ground((x, -1.4), color=ss.PARASITIC)
    op = s.opamp((x_in, 0.0))
    s.wire((0.0, 0.0), op.in1)
    # C_DIFF from the inverting input to the non-inverting input pin, which is grounded;
    # e_n sits between that pin and the amplifier, so it acts on C_DIFF as on every other
    # capacitance at the summing node
    x_d, x_e, y_p = 12.2, 13.5, -2.5
    s.dot((x_d, 0.0))
    s.cap((x_d, 0.0), (x_d, y_p), None, color=ss.PARASITIC)
    s.text((x_d + 0.3, -0.45), "$C_{DIFF}$", color=ss.PARASITIC)
    s.wire((x_d, y_p), (x_e, y_p))
    s.dot((x_e, y_p))
    s.wire(op.in2, (x_e, op.in2[1]))
    s.vsource((x_e, y_p), (x_e, op.in2[1]), "$e_n$", side="right", color=ss.NOISE)
    s.wire((x_e, y_p), (x_e, y_p - 0.3))
    s.ground((x_e, y_p - 0.3))
    # feedback: R_F, its noise i_R, and C_F
    x_fl, x_fr = 13.3, op.out[0] + 0.75
    y_r, y_i, y_c = 1.5, 3.0, 4.5
    s.dot((x_fl, 0.0))
    s.wire((x_fl, 0.0), (x_fl, y_c))
    for y in (y_r, y_i):
        s.dot((x_fl, y))
        s.dot((x_fr, y))
    s.res((x_fl, y_r), (x_fr, y_r), "$R_F$", side="bottom")
    s.isource((x_fl, y_i), (x_fr, y_i), None, color=ss.NOISE)
    s.text((0.5 * (x_fl + x_fr) + 0.7, y_i + 0.1), "$i_R$", va="bottom", color=ss.NOISE)
    s.cap((x_fl, y_c), (x_fr, y_c), "$C_F = C_{par} + C_{add}$", side="top", color=ss.PARASITIC)
    s.wire((x_fr, y_c), (x_fr, op.out[1]))
    s.wire(op.out, (x_fr, op.out[1]))
    s.dot((x_fr, op.out[1]))
    out_terminal(s, x_fr, op.out[1])
    s.save(out / "schem_tia_noise")


# ------------------------------------------------------------- Section 3.4 --
def schem_rc_line(out: Path) -> None:
    """Figure 4: the resistive film as a ladder of N slices, R/N in series with C_g/N from
    each slice to the conductor beneath it, held at a(u) V_out; C_ee from end cap to end cap."""
    s = ss.Sheet()
    x0, x1, n = 1.2, 14.2, 5
    s.terminal((0.0, 0.0), "summing node\n(virtual ground)", side="left")
    s.wire((0.0, 0.0), (x0, 0.0))
    xs = [x0 + k * (x1 - x0) / n for k in range(n + 1)]
    for k in range(n):
        s.res((xs[k], 0.0), (xs[k + 1], 0.0), "$R/N$" if k == 0 else None, side="top")
    y_b = -1.9
    for k in range(1, n):
        s.dot((xs[k], 0.0))
        s.cap((xs[k], 0.0), (xs[k], y_b), "$C_g/N$" if k == 1 else None, side="left",
              color=ss.PARASITIC)
    s.wire((xs[1] - 0.6, y_b), (xs[n - 1] + 0.6, y_b), color=ss.GUARD, lw=3.0)
    s.text((0.5 * (x0 + x1), y_b - 0.3), "conductor beneath the film, held at $a(u)\\,V_{out}$",
           ha="center", va="top", color=ss.GUARD)
    s.wire((x1, 0.0), (x1 + 1.0, 0.0))
    s.terminal((x1 + 1.0, 0.0), "$V_{out}$")
    # end-to-end capacitance over the top
    y_e = 1.5
    s.dot((x0, 0.0))
    s.dot((x1, 0.0))
    s.wire((x0, 0.0), (x0, y_e))
    s.wire((x1, 0.0), (x1, y_e))
    s.cap((x0, y_e), (x1, y_e), "$C_{ee}$", side="top", color=ss.PARASITIC)
    s.text((x0, -0.35), "$u = 0$", ha="center", va="top")
    s.text((x1, -0.35), "$u = 1$", ha="center", va="top")
    s.save(out / "schem_rc_line")


def _guard_panel(s: ss.Sheet, ox: float, oy: float, kind: str) -> None:
    """One panel of Figure 6: a TIA whose R_F has a conductor beside it, driven as `kind`."""
    def P(x, y):
        return (ox + x, oy + y)
    op = s.opamp(P(3.0, 0.0))
    s.wire(P(0.0, 0.0), P(0.0, -0.35))
    s.photodiode(P(0.0, -0.35), P(0.0, -1.65))
    s.wire(P(0.0, -1.65), P(0.0, -2.0))
    s.ground(P(0.0, -2.0))
    s.wire(P(0.0, 0.0), op.in1)
    s.ring(ox + 0.6, oy - 0.42, ox + 2.1, oy + 0.42, "guard\nring", text_at="bottom_left")
    s.wire(op.in2, P(1.85, op.in2[1] - oy), P(1.85, -1.6))
    s.wire(P(1.85, -0.42), P(1.85, op.in2[1] - oy), color=ss.GUARD)
    s.dot(P(1.85, op.in2[1] - oy))
    s.ground(P(1.85, -1.6))
    x_fl, x_fr = 1.2, op.out[0] - ox + 0.75
    y_r, y_g = 1.6, 2.4
    s.dot(P(x_fl, 0.0))
    s.wire(P(x_fl, 0.0), P(x_fl, y_r))
    s.res(P(x_fl, y_r), P(x_fr, y_r), "$R_F$", side="bottom")
    s.wire(P(x_fr, y_r), P(x_fr, op.out[1] - oy))
    s.wire(op.out, P(x_fr, op.out[1] - oy))
    s.dot(P(x_fr, op.out[1] - oy))
    yo = op.out[1] - oy
    if kind == "plane":
        s.wire(P(x_fl + 0.9, y_g), P(x_fr - 0.9, y_g), color=ss.GUARD, lw=3.0)
        s.text(P(0.5 * (x_fl + x_fr), y_g + 0.25), "plane at $V_{out}/3$", ha="center", va="bottom",
               color=ss.GUARD)
        xd = x_fr + 1.0
        s.wire(P(x_fr, yo), P(xd, yo))
        s.res(P(xd, yo), P(xd, -2.0), "2 kΩ", side="right")
        s.dot(P(xd, -2.0))
        s.res(P(xd, -2.0), P(xd, -3.5), "1 kΩ", side="right")
        s.ground(P(xd, -3.5))
        s.wire(P(xd, -2.0), P(xd - 0.7, -2.0))
        s.terminal(P(xd - 0.7, -2.0), "to plane", side="left", color=ss.GUARD)
    elif kind == "strips":
        span = x_fr - x_fl
        for k, lab in enumerate(("1/8", "3/8", "5/8", "7/8")):
            xc = x_fl + span * (2 * k + 1) / 8
            s.wire(P(xc - 0.4, y_g), P(xc + 0.4, y_g), color=ss.GUARD, lw=3.0)
            s.text(P(xc, y_g + 0.2), lab, ha="center", va="bottom", color=ss.GUARD)
        s.text(P(0.5 * (x_fl + x_fr), y_g + 0.75), "strips at fractions of $V_{out}$", ha="center",
               va="bottom", color=ss.GUARD)
        xd = x_fr + 1.0
        s.wire(P(x_fr, yo), P(xd, yo))
        ys = [yo, -1.6, -2.75, -3.9, -5.05, -6.2]
        vals = ("1 kΩ", "2 kΩ", "2 kΩ", "2 kΩ", "1 kΩ")
        for k in range(5):
            s.res(P(xd, ys[k]), P(xd, ys[k + 1]), vals[k], side="left")
        for k, lab in enumerate(("7/8", "5/8", "3/8", "1/8")):
            s.dot(P(xd, ys[k + 1]))
            s.wire(P(xd, ys[k + 1]), P(xd + 0.6, ys[k + 1]))
            s.terminal(P(xd + 0.6, ys[k + 1]), lab, color=ss.GUARD)
        s.ground(P(xd, ys[5]))


def _film_panel(s: ss.Sheet, ox: float, oy: float) -> None:
    """Panel (c) of Figure 6: R_F and a guard film beneath it, each drawn as four equal
    slices with their junctions aligned.  R_F runs from the summing node (virtual ground) to
    V_out and the guard film from ground to V_out, so both junctions of every pair sit at
    the same potential, V_out/4, V_out/2 and 3V_out/4, and the capacitance between the films
    (grey) carries no current.  The guard's grounded end lies under the summing-node end,
    as the n-well does under the polysilicon resistor in Seidl's CCDR."""
    def P(x, y):
        return (ox + x, oy + y)
    op = s.opamp(P(6.0, 0.0))
    s.wire(P(0.0, 0.0), P(0.0, -0.35))
    s.photodiode(P(0.0, -0.35), P(0.0, -1.65))
    s.wire(P(0.0, -1.65), P(0.0, -2.0))
    s.ground(P(0.0, -2.0))
    s.wire(P(0.0, 0.0), op.in1)
    s.ring(ox + 0.5, oy - 0.42, ox + 2.0, oy + 0.42, "guard\nring", text_at="bottom_left")
    s.wire(op.in2, P(1.75, op.in2[1] - oy), P(1.75, -1.6))
    s.wire(P(1.75, -0.42), P(1.75, op.in2[1] - oy), color=ss.GUARD)
    s.dot(P(1.75, op.in2[1] - oy))
    s.ground(P(1.75, -1.6))
    x_fl, x0 = 0.9, 1.4
    x_fr = op.out[0] - ox + 0.75
    yo = op.out[1] - oy
    y_r, y_g = 3.0, 1.8
    xs = [x0 + k * (x_fr - x0) / 4 for k in range(5)]
    # R_F in four slices from the summing node to the output
    s.dot(P(x_fl, 0.0))
    s.wire(P(x_fl, 0.0), P(x_fl, y_r), P(x0, y_r))
    for k in range(4):
        s.res(P(xs[k], y_r), P(xs[k + 1], y_r), None)
    s.text(P(0.5 * (x0 + x_fr), y_r + 0.42), "$R_F$", ha="center", va="bottom")
    # the guard film in four slices from ground to the output
    for k in range(4):
        s.res(P(xs[k], y_g), P(xs[k + 1], y_g), None, color=ss.GUARD)
    s.wire(P(x0, y_g), P(x0, y_g - 0.3), color=ss.GUARD)
    s.ground(P(x0, y_g - 0.3), color=ss.GUARD)
    s.text(P(0.5 * (x0 + x_fr), y_g - 0.42), "guard film, from ground to $V_{out}$", ha="center", va="top",
           color=ss.GUARD)
    # the capacitance between the films joins points at equal potential
    for k, lab in ((1, "$V_{out}/4$"), (2, "$V_{out}/2$"), (3, "$3V_{out}/4$")):
        s.dot(P(xs[k], y_r))
        s.dot(P(xs[k], y_g), color=ss.GUARD)
        s.cap(P(xs[k], y_r), P(xs[k], y_g), None, color=ss.PARASITIC)
        s.text(P(xs[k] + 0.42, 0.5 * (y_r + y_g)), lab)
    s.text(P(xs[1] - 0.42, 0.5 * (y_r + y_g)), "$C_g$", ha="right", color=ss.PARASITIC)
    # the output column joins both films' output ends
    s.dot(P(x_fr, y_g))
    s.wire(P(x_fr, y_r), P(x_fr, yo))
    s.wire(op.out, P(x_fr, yo))
    s.dot(P(x_fr, yo))
    s.wire(P(x_fr, yo), P(x_fr + 0.6, yo))
    s.terminal(P(x_fr + 0.6, yo), "$V_{out}$")


def schem_guard_drives(out: Path) -> None:
    """Figure 6: (a) a plane at V_out/3 from a 2 kOhm / 1 kOhm divider; (b) four strips at
    V_out/8, 3/8, 5/8, 7/8 from a 1-2-2-2-1 kOhm divider; (c) the ideal graded guard, a
    resistive film from ground to V_out beneath R_F (the principle of Seidl's CCDR), with the
    capacitance between the films joining points at equal potential.  In each, the summing
    node keeps its own guard ring at its potential, ground."""
    s = ss.Sheet()
    _guard_panel(s, 0.0, 0.0, "plane")
    panel_label(s, (-1.0, 3.6), "(a)")
    _guard_panel(s, 10.6, 0.0, "strips")
    panel_label(s, (9.6, 3.6), "(b)")
    _film_panel(s, 0.0, -7.8)
    panel_label(s, (-1.0, -4.3), "(c)")
    s.save(out / "schem_guard_drives")


def schem_split_resistor(out: Path) -> None:
    """Figure 7: R_F split into three 333-MOhm resistors; each junction pad sits in a guard
    at its own low-frequency potential (V_out/3, 2V_out/3) and each body has a strip at its
    mid-point potential (V_out/6, V_out/2, 5V_out/6), all from one divider of six equal
    resistors; the summing node keeps its guard ring at ground (Section 3.4, Step 10)."""
    s = ss.Sheet()
    op = s.opamp((11.0, 0.0))
    pd_down(s, 0.0, bias="ground")
    s.wire((0.0, 0.0), op.in1)
    s.ring(0.6, -0.42, 2.0, 0.42, "guard\nring", text_at="bottom_left")
    s.wire(op.in2, (10.4, op.in2[1]), (10.4, -1.6))
    s.ground((10.4, -1.6))
    x_fl, x_fr = 1.3, op.out[0] + 0.75
    y_r, y_g = 1.8, 2.7
    s.dot((x_fl, 0.0))
    s.wire((x_fl, 0.0), (x_fl, y_r))
    xs = [x_fl + k * (x_fr - x_fl) / 3 for k in range(4)]
    for k in range(3):
        s.res((xs[k], y_r), (xs[k + 1], y_r), "333 MΩ", side="bottom")
        xc = 0.5 * (xs[k] + xs[k + 1])
        s.wire((xc - 0.6, y_g), (xc + 0.6, y_g), color=ss.GUARD, lw=3.0)
        s.text((xc, y_g + 0.2), ("1/6", "1/2", "5/6")[k], ha="center", va="bottom", color=ss.GUARD)
    for k, lab in ((1, "1/3"), (2, "2/3")):
        s.dot((xs[k], y_r))
        s.box(xs[k] - 0.3, y_r - 0.3, xs[k] + 0.3, y_r + 0.3, color=ss.GUARD, dashed=True)
        s.text((xs[k], y_r - 0.45), lab, ha="center", va="top", color=ss.GUARD)
    s.wire((x_fr, y_r), (x_fr, op.out[1]))
    s.wire(op.out, (x_fr, op.out[1]))
    s.dot((x_fr, op.out[1]))
    # the divider of six equal resistors, taps labelled by their fraction of V_out
    xd = x_fr + 1.1
    s.wire((x_fr, op.out[1]), (xd, op.out[1]))
    ys = [op.out[1] - 1.05 * k for k in range(7)]
    for k in range(6):
        s.res((xd, ys[k]), (xd, ys[k + 1]), None)
    s.text((xd - 0.5, 0.5 * (ys[0] + ys[6])), "six equal\nresistors,\n1 kΩ each", ha="right")
    for k, lab in enumerate(("5/6", "2/3", "1/2", "1/3", "1/6")):
        s.dot((xd, ys[k + 1]))
        s.wire((xd, ys[k + 1]), (xd + 0.6, ys[k + 1]))
        s.terminal((xd + 0.6, ys[k + 1]), lab, color=ss.GUARD)
    s.ground((xd, ys[6]))
    s.text((0.5 * (x_fl + x_fr), y_g + 0.75), "guards and strips at fractions of $V_{out}$", ha="center",
           va="bottom", color=ss.GUARD)
    s.save(out / "schem_split_resistor")


# ------------------------------------------------------------- Section 3.5 --
def schem_equalizer(out: Path) -> None:
    """Figure 8: an equalizer after the TIA, (1 + sR_FC_F)/(1 + sR_FC_F/k), and the
    calibration of the resistor's response by a known current injected through C_inj."""
    s = ss.Sheet()
    pd_down(s, 0.0, bias="ground")
    # calibration injection, dashed: generator and C_inj into the summing node
    x_i = 1.8
    s.dot((x_i, 0.0))
    s.cap((x_i, 0.0), (x_i, -1.1), "$C_{inj}$", side="right", color=ss.OPTIONAL, dashed=True)
    s.vsource((x_i, -2.6), (x_i, -1.1), "$V$", side="right", color=ss.OPTIONAL)
    s.ground((x_i, -2.6), color=ss.OPTIONAL)
    op, x_fr = tia(s, 0.0, 4.6, 3.8, "$R_F$", "$C_F$")
    xb0, xb1 = x_fr + 0.7, x_fr + 5.2
    yo = op.out[1]
    s.wire((x_fr, yo), (xb0, yo))
    s.box(xb0, yo - 0.9, xb1, yo + 0.9, "equalizer\n$\\frac{1 + sR_FC_F}{1 + sR_FC_F/k}$")
    out_terminal(s, xb1, yo)
    s.save(out / "schem_equalizer")


def schem_t_network(out: Path) -> None:
    """Figure 9: (a) a T-network, R_1 = 10 MOhm with R_2 = 9.9 kOhm and R_3 = 100 Ohm, so
    k = 1 + R_2/R_3 = 100 and 1 GOhm of transimpedance (Eq. (29a)); (b) the same 10 MOhm
    followed by a voltage stage of gain 100 (t_network_vs_second_stage.py)."""
    s = ss.Sheet()
    # (a) T-network
    panel_label(s, (-1.0, 3.6), "(a)")
    op = s.opamp((5.0, 0.0))
    s.terminal((0.0, 0.0), "$I$", side="left")
    s.wire((0.0, 0.0), op.in1)
    s.wire(op.in2, (4.5, op.in2[1]), (4.5, -1.6))
    s.ground((4.5, -1.6))
    x_fl, x_fr = 1.0, op.out[0] + 0.75
    y = 2.4
    s.dot((x_fl, 0.0))
    s.wire((x_fl, 0.0), (x_fl, y))
    x_t = 3.6
    s.res((x_fl, y), (x_t, y), "$R_1$ 10 MΩ", side="top")
    s.dot((x_t, y))
    s.res((x_t, y), (x_fr, y), "$R_2$ 9.9 kΩ", side="top")
    s.res((x_t, y), (x_t, 0.95), "$R_3$\n100 Ω", side="left")
    s.ground((x_t, 0.95))
    s.text((x_t + 0.2, y + 0.15), "T", va="bottom")
    s.wire((x_fr, y), (x_fr, op.out[1]))
    s.wire(op.out, (x_fr, op.out[1]))
    s.dot((x_fr, op.out[1]))
    out_terminal(s, x_fr, op.out[1], length=0.6)
    # (b) R_1 alone, then a voltage stage of gain 100
    ox = 10.3
    panel_label(s, (ox - 0.6, 3.6), "(b)")
    op2 = s.opamp((ox + 2.6, 0.0))
    s.terminal((ox + 0.4, 0.0), "$I$", side="left")
    s.wire((ox + 0.4, 0.0), op2.in1)
    s.wire(op2.in2, (ox + 2.1, op2.in2[1]), (ox + 2.1, -1.6))
    s.ground((ox + 2.1, -1.6))
    x_fl2, x_fr2 = ox + 1.3, op2.out[0] + 0.75
    s.dot((x_fl2, 0.0))
    s.wire((x_fl2, 0.0), (x_fl2, 1.6))
    s.res((x_fl2, 1.6), (x_fr2, 1.6), "$R_1$ 10 MΩ", side="top")
    s.wire((x_fr2, 1.6), (x_fr2, op2.out[1]))
    s.wire(op2.out, (x_fr2, op2.out[1]))
    s.dot((x_fr2, op2.out[1]))
    o = s.buffer((x_fr2, op2.out[1]), text="×100", h=1.8)
    s.text((x_fr2 + 0.55, op2.out[1] + 1.05), "voltage stage", va="bottom")
    out_terminal(s, o[0], o[1], length=0.4)
    s.save(out / "schem_t_network")


# ------------------------------------------------------------- Section 5.8 --
def schem_jfet_composite(out: Path) -> None:
    """Figure 12: the composite of Section 9.5 (hg_spice.composite_text): J1 LSBF862 in
    common source at the summing node, cascode J2 with its gate at 2.5 V, R_D = 1 kOhm from
    15 V (drain at 5 V, 10 mA, g_m R_D about 33), an integrator sensing the drain against
    5 V through 1 kOhm with C_c = 106 pF (unity gain at 1.5 MHz), R_F || C_F to J1's gate."""
    s = ss.Sheet()
    pd_down(s, 0.0, bias="0 V", label="$C_D$, $R_{sh}$")
    x_fb = 1.1
    j1 = s.njfet((3.4, 0.0), mirror=True, name="J1")
    s.wire((0.0, 0.0), j1.gate)
    s.wire(j1.source, (j1.source[0], -0.8))
    s.ground((j1.source[0], -0.8))
    j2 = s.njfet((3.4, 1.9), mirror=True, name="J2")
    s.wire(j1.drain, j2.source)
    s.wire(j2.gate, (2.5, 1.9))
    s.dot((2.5, 1.9))
    s.cap((2.5, 1.9), (2.5, 0.85), None)
    s.ground((2.5, 0.85))
    s.wire((2.5, 1.9), (1.9, 1.9))
    s.terminal((1.9, 1.9), "2.5 V", side="top")
    x_d, y_d = j2.drain[0], 3.1
    s.wire(j2.drain, (x_d, y_d))
    s.dot((x_d, y_d))
    s.res((x_d, y_d), (x_d, 4.4), "$R_D$\n1 kΩ", side="left")
    s.supply((x_d, 4.4), "15 V")
    # integrator: + input on the drain, - input through 1 kOhm to 5 V, C_c in its feedback
    u = s.opamp((7.0, y_d - 0.9), minus_on_top=False, name="integrator", name_at="above")
    s.wire((x_d, y_d), u.in2)
    s.dot((6.6, u.in1[1]))
    s.wire(u.in1, (5.8, u.in1[1]))
    s.res((5.8, u.in1[1]), (5.8, 0.5), "1 kΩ", side="left")
    s.terminal((5.8, 0.5), "5 V", side="bottom")
    x_o = u.out[0] + 0.7
    s.wire((6.6, u.in1[1]), (6.6, 1.0))
    s.cap((6.6, 1.0), (x_o, 1.0), "$C_c$ 106 pF", side="bottom")
    s.wire((x_o, 1.0), (x_o, u.out[1]))
    s.wire(u.out, (x_o, u.out[1]))
    s.dot((x_o, u.out[1]))
    # R_F || C_F from the output back to J1's gate, over the top
    y_r, y_c = 5.9, 7.0
    s.dot((x_fb, 0.0))
    s.wire((x_fb, 0.0), (x_fb, y_c))
    s.dot((x_fb, y_r))
    s.res((x_fb, y_r), (x_o, y_r), "$R_F$", side="bottom")
    s.cap((x_fb, y_c), (x_o, y_c), "$C_F$", side="top")
    s.wire((x_o, y_c), (x_o, u.out[1]))
    s.dot((x_o, y_r))
    out_terminal(s, x_o, u.out[1])
    s.save(out / "schem_jfet_composite")


# ------------------------------------------------------------- Section 7 ----
def schem_gain_ranging(out: Path) -> None:
    """Figure 13: two ranges, each with a T-switch at the summing-node end of its feedback
    resistor: an inner switch S_in, an outer switch S_out and a shunt S_sh that ties their
    junction to the summing node's potential, ground, when the range is off (Section 7.1).
    Range 1 is selected (S_in, S_out closed, S_sh open), range 2 is off."""
    s = ss.Sheet()
    pd_down(s, 0.0, bias="ground")
    op = s.opamp((7.6, 0.0))
    s.wire((0.0, 0.0), op.in1)
    s.wire(op.in2, (7.1, op.in2[1]), (7.1, -1.6))
    s.ground((7.1, -1.6))
    x_bus, x_j, x_r0 = 1.2, 3.1, 5.0
    x_fr = op.out[0] + 0.75
    rows = ((2.0, True, "$R_{F1}$", "range 1, selected"), (4.6, False, "$R_{F2}$", "range 2, off"))
    s.dot((x_bus, 0.0))
    s.wire((x_bus, 0.0), (x_bus, rows[-1][0]))
    s.wire((x_fr, op.out[1]), (x_fr, rows[-1][0]))
    for i, (y, on, rname, note) in enumerate(rows):
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
    s.dot((x_fr, op.out[1]))
    s.wire(op.out, (x_fr, op.out[1]))
    out_terminal(s, x_fr, op.out[1])
    s.save(out / "schem_gain_ranging")


def schem_log_amp(out: Path) -> None:
    """Figure 14: the transdiode logarithmic amplifier of Section 7.2: an NPN with its
    collector at the summing node, its base at ground and its emitter driven by the output
    through an optional R_E, and the compensation capacitor C_C across it (Eqs. (31)-(34))."""
    s = ss.Sheet()
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


def schem_integrator(out: Path) -> None:
    """Figure 15: a switched integrator in the arrangement of IVC102 (Section 7.3): the input
    switch S1 (integrate or hold), C_int (10, 30 or 60 pF, or all three for 100 pF) in the
    feedback path, the reset switch S2 across it, and an ADC that samples V_1 after the
    reset and V_2 after the integration time T (double sampling)."""
    s = ss.Sheet()
    pd_down(s, 0.0, bias="ground")
    x_s0, x_s1 = 0.7, 2.3
    s.switch((x_s0, 0.0), (x_s1, 0.0), closed=True, text="$S_1$ integrate/hold", side="top")
    s.wire((0.0, 0.0), (x_s0, 0.0))
    op = s.opamp((5.2, 0.0))
    s.wire((x_s1, 0.0), op.in1)
    s.wire(op.in2, (4.7, op.in2[1]), (4.7, -1.6))
    s.ground((4.7, -1.6))
    x_fl, x_fr = 3.6, op.out[0] + 0.75
    y_c, y_s = 1.6, 2.9
    s.dot((x_fl, 0.0))
    s.wire((x_fl, 0.0), (x_fl, y_s))
    s.dot((x_fl, y_c))
    s.cap((x_fl, y_c), (x_fr, y_c), "$C_{int}$  10, 30, 60 or 100 pF", side="bottom")
    s.switch((x_fl, y_s), (x_fr, y_s), closed=False, text="$S_2$ reset", side="top")
    s.dot((x_fr, y_c))
    s.wire((x_fr, y_s), (x_fr, op.out[1]))
    s.wire(op.out, (x_fr, op.out[1]))
    s.dot((x_fr, op.out[1]))
    s.box(0.45, -1.25, x_fr + 0.35, y_s + 0.95, None, color=ss.OPTIONAL, dashed=True)
    s.text((0.6, y_s + 0.8), "IVC102", va="top", color=ss.OPTIONAL)
    out_terminal(s, x_fr, op.out[1], "ADC: $V_1$ after reset,\n$V_2$ after $T$", length=1.2)
    s.save(out / "schem_integrator")


def schem_optical_reset(out: Path) -> None:
    """Figure 16: optical reset of a charge-sensitive preamplifier (Section 7.3; LBL-8135,
    LBL-13214): the detector at the gate of the input JFET, a feedback capacitor of about
    0.5 pF, and an LED, switched by a window comparator on the output, whose light raises
    the current of the JFET's drain-gate junction to 0.1-1 uA and so discharges C_F;
    detector, C_F, LED and JFET sit together in the cryostat."""
    s = ss.Sheet()
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
    s.cap((x_fb, y_c), (4.4, y_c), "$C_F$ ≈ 0.5 pF", side="top")
    s.wire((4.4, y_c), (x_o, y_c), (x_o, y_a))
    s.wire((x_o, y_a), (x_o + 1.5, y_a))
    s.terminal((x_o + 1.5, y_a), "$V_{out}$")
    # window comparator on the output, switching the LED that lights the FET
    x_c = x_o + 0.8
    s.dot((x_c, y_a))
    y_l = -1.8
    s.wire((x_c, y_a), (x_c, y_l))
    oc = s.buffer((x_c, y_l), left=True, text="")
    s.text((x_c - 1.0, y_l - 0.9), "window\ncomparator", ha="center", va="top")
    s.wire(oc, (5.4, y_l))
    s.diode((5.4, y_l), (4.2, y_l), None)
    s.wire((4.2, y_l), (3.9, y_l), (3.9, y_l - 0.3))
    s.ground((3.9, y_l - 0.3))
    for k in (0.0, 0.32):
        s.arrow((4.75 + k, y_l + 0.45), (4.15 + k, y_l + 1.15), color=ss.LIGHT, width=0.13, length=0.17)
    s.text((5.3, y_l + 0.9), "LED", va="center")
    # the cryostat around detector, FET, C_F and LED
    s.box(-1.3, -3.3, 6.0, 4.0, None, color=ss.OPTIONAL, dashed=True)
    s.text((-1.3, 4.15), "cryostat, about 77 K", va="bottom", color=ss.OPTIONAL)
    s.save(out / "schem_optical_reset")


FIGURES = {f.__name__: f for f in (
    schem_tia_noise, schem_rc_line, schem_guard_drives, schem_split_resistor, schem_equalizer,
    schem_t_network, schem_jfet_composite, schem_gain_ranging, schem_log_amp, schem_integrator,
    schem_optical_reset)}


def main(argv: list[str]) -> None:
    ss.configure()
    out = Path(argv[1]) if len(argv) > 1 else FIG
    for name in argv[2:] or list(FIGURES):
        FIGURES[name](out)
        print("drawn", name)


if __name__ == "__main__":
    main(sys.argv)
