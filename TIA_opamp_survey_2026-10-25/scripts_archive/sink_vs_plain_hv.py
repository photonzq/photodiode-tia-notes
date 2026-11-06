"""A resistive DC sink at the summing node against a plain DC-coupled TIA with a larger output range (Section 8.6).

Usage: python sink_vs_plain_hv.py [--figure OUT_STEM]

With --figure it also draws Figure 33 of the note, the resistor floor of both schemes against the voltage across
the resistor that carries the DC, as OUT_STEM.png (600 dpi) and OUT_STEM.pdf, in the style of the plotting guide
(the note's file is figures/fig26b_sink_vs_plain).

Why this script exists
----------------------
Option A of Section 8.2 removes the DC photocurrent through a resistor R_s whose far end a slow servo
moves, and Eq. (69) states its cost relative to the shot noise of the current it carries. That cost holds at
the design current. This script evaluates what the sink costs below that current and in the dark, when
the servo's output range is limited, and how it compares with a plain DC-coupled TIA whose amplifier swings
the DC itself and whose output is AC-coupled into a later stage (Option D of Section 8.5 with a
high-voltage first stage). All values at 25 degC, as in the note.

1. The resistor floor at the summing node
-----------------------------------------
Every resistor between the summing node and an AC ground injects its Johnson current noise 4 k_B T / R.
With a sink, R_F and R_s both do (the far end of R_s is bypassed), so the floor is that of R_F || R_s:
    S_R = 4 k_B T (1/R_F + 1/R_s).
The sink must carry the largest photocurrent I_max with the voltage V_S the servo can apply, so
R_s <= V_S / I_max, and with the largest R_s allowed
    S_R,sink  = (4 k_B T / R_F) (1 + I_max R_F / V_S).                                (1)
A plain DC-coupled TIA carries the DC through its own feedback resistor, R_F' <= V_A / I_max, with V_A
the part of its output range left for the DC. Where V_A >= I_max R_F the band's own R_F fits:
    S_R,plain = (4 k_B T / R_F) max(1, I_max R_F / V_A).                              (2)
Both follow from one bound: a resistor that carries the current I across the voltage V adds
4 k_B T / R = 4 k_B T I / V = (2 k_B T / (q V)) 2 q I, i.e. 51.4 mV / V times the shot noise of I
(the note's Eq. (30)), whatever drives it.

At equal voltage, V_S = V_A = V and x = I_max R_F / V, Eqs. (1) and (2) differ by the factor
(1 + x) / max(1, x), which lies between 1 and 2 (0 and 3 dB, the maximum at x = 1). The sink wins only
with a larger voltage of its own:
    V_S > V_A I_max R_F / (I_max R_F - V_A)            (for V_A < I_max R_F).          (3)

2. The photocurrent at which the light takes over
--------------------------------------------------
The floor S_R equals the shot noise 2 q I_eq of the current
    I_eq = (2 k_B T / q) (1/R_F + 1/R_s),                                             (4)
25.7 uA for 2 kOhm alone (Section 6.10). From the resistors alone, the excess over pure shot noise at the
photocurrent I is 10 log10(1 + I_eq / I); the amplifier adds the terms of Eq. (33) on top.

3. Band noise of the OPA855 design with a sink
-----------------------------------------------
Table A4.1 gives 50.2 nA rms over 0-150 MHz for OPA855 at 2 kOhm (model), which already contains R_F. A
sink adds its white floor over the band B, and the photocurrent adds its shot noise:
    i_B = sqrt(50.2^2 + (4 k_B T / R_s + 2 q I) B)      in nA, with B = 150 MHz.        (5)
One pA^2/Hz over 150 MHz is 150 nA^2.

4. The amplifier's voltage noise at the low end
-----------------------------------------------
The amplifier's e_n sits at the summing node and drives every conductance there. Its input-referred
current is e_n (1/R_F + 1/R_s + j w C_T); at low frequency the capacitive part vanishes and
    S_en = e_n^2 (1/R_F + 1/R_s)^2       (sink),         e_n'^2 / R_F'^2       (plain),  (6)
the same structure as Eqs. (1) and (2). Evaluated for OPA846 at 100 Hz with its single-corner form,
e_n = 1.2 nV/rtHz x sqrt(1 + 1.9 kHz / f) (Section 4.4 and data/specs/OPA846.json).

5. Excess (1/f) noise of the resistor that carries the DC
----------------------------------------------------------
With the noise index NI in uV/V per decade (Section 6.9), the excess voltage density across a resistor
with the DC voltage V is 10^(NI/20) uV/V x V / sqrt(f ln 10). As a current at the node, divided by R,
    S_ex = 10^(NI/10) (1 uV/V)^2 I^2 / (f ln 10),                                      (7)
which depends on the current and the noise index only, not on R or V: the same in both schemes for the
same resistor technology. Evaluated at NI = -32 dB, the figure Section 6.9 asks of the servo resistor.

6. Power and self-heating of the resistor that carries the DC
-------------------------------------------------------------
It dissipates P = V I, so its rating caps the voltage: V <= P_70 / I. Vishay rates its TNPW e3 thin-film
chip resistors, in the general operation mode with the film at up to 125 degC, at 0.070, 0.110, 0.140 and
0.270 W for the 0402, 0603, 0805 and 1206 sizes (document 28758, revision 10-Apr-2026, p. 2). With the
thermal resistance theta and the temperature coefficient alpha the resistance changes by
    dR/R = alpha theta P,
and the ratings give theta = (125 - 70) K / 0.270 W = 204 K/W for the 1206 (its power and advanced modes,
0.420 W to 155 degC and 0.520 W to 175 degC, give 202 K/W). Its temperature coefficients are +-50, 25, 15
and 10 ppm/K (p. 1). In the plain TIA this resistor sets the AC transimpedance, so the gain follows the DC
level with a thermal lag; in the sink it is R_s, whose drift the servo absorbs.

7. The later stage that rejects the DC (plain TIA)
---------------------------------------------------
(a) Its input voltage noise e_f is referred to the input through the first stage's resistor, e_f / R_F'
    (the note's Eq. (72)); after a sink, through R_F. At equal voltage the plain scheme's extra
    e_f^2 (1/R_V^2 - 1/R_F^2) offsets the sink's 4 k_B T / R_F only above
    e_f = sqrt((4 k_B T / R_F) / (1/R_V^2 - 1/R_F^2)).                                (8)
(b) A passive high-pass, series C into a resistor R to ground, puts R's Johnson voltage at its output
    through 1 / (1 + j f / f_HP), i.e. sqrt(4 k_B T R) f_HP / f well above the corner.
(c) Recovery after a DC step dI. The sink's integrator sees an error clipped at the fast amplifier's
    swing V_sat, so it ramps at V_sat / tau_int; with Eq. (80), tau_int = R_F / (2 pi f_HP R_s), it must
    move the far end of R_s by dI R_s, which takes
        t_sink = (dI R_F / V_sat) / (2 pi f_HP),                                        (9)
    independent of R_s, while the summing node has left virtual ground. A capacitor-coupled later stage
    with the same overall gain decays exponentially and is back in its linear range V_lin after
        t_plain = ln(dI R_F / V_lin) / (2 pi f_HP),                                     (10)
    while the TIA itself stays linear.

8. Laser RIN
------------
The measured RIN is S_i / I_DC^2, and its floor is the shot noise, RIN_shot = 2 q / I_DC. Every electronic
term divided by I_DC^2 is an apparent RIN: the excess noise of Eq. (7) gives 10^(NI/10) (1 uV/V)^2 / (f ln 10)
at any current, equal to RIN_shot at I = 2 q / that value; the servo's noise e_s on V_S gives (e_s / V_S)^2 at
the full current; an amplifier's input noise i gives i^2 / I_DC^2. A first-order high-pass at f_HP lowers the
RIN measured at f by 10 log10(1 + f_HP^2 / f^2).

The script's Eqs. (1)-(10) are the note's Eqs. (72a), (72d), (72e), (72b), (72c), (72f), (72i), the unnumbered
break-even of the later stage's noise, (72g) and (72h); Section 8 here is the note's Eq. (72j).
"""
import math
import sys

KT = 4.116e-21                      # J, k_B T at 25 degC (the note's value)
Q = 1.602177e-19                    # C
FOUR_KT = 4 * KT / 1e3 * 1e24       # 4 k_B T / (1 kOhm) in pA^2/Hz: 16.46
TWO_KT_Q = 2 * KT / Q               # V: 0.05138
SHOT = 2 * Q * 1e-3 * 1e24          # 2 q x 1 mA in pA^2/Hz: 320.4
B_HZ = 150e6
NA2_PER_PA2HZ = B_HZ / 1e6          # 1 pA^2/Hz over 150 MHz in nA^2: 150
BAND_OPA855 = 50.2                  # nA rms, Table A4.1 (model), includes R_F = 2 kOhm

I_MAX = 10.0                        # mA, the single-ended example of Sections 8.1-8.5
R_F = 2.0                           # kOhm, the band's resistor
CURRENTS = (0.1, 1.0, 10.0)         # mA


def floor_sink(v_s):
    r_s = v_s / I_MAX                                  # kOhm (V / mA)
    return r_s, FOUR_KT * (1 / R_F + 1 / r_s)


def floor_plain(v_a):
    r_f1 = min(R_F, v_a / I_MAX)
    return r_f1, FOUR_KT / r_f1


def main():
    print(f"4 k_B T / 1 kOhm = {FOUR_KT:.3f} pA^2/Hz; 2 k_B T / q = {TWO_KT_Q * 1e3:.2f} mV; "
          f"2 q x 1 mA = {SHOT:.2f} pA^2/Hz; I_max = {I_MAX:g} mA; R_F = {R_F:g} kOhm, so I_max R_F = {I_MAX * R_F:g} V")
    s_ref = FOUR_KT / R_F
    rows = [("2 kOhm alone, no DC (reference)", "ref", None),
            ("plain, Option D first stage (5-V part)", "plain", 2.86),
            ("sink, Option A as drawn", "sink", 5.0),
            ("plain, V_A = 10 V", "plain", 10.0),
            ("sink, servo on +-15 V", "sink", 12.0),
            ("plain, V_A = 20 V = I_max R_F", "plain", 20.0),
            ("sink, V_S = 20 V", "sink", 20.0),
            ("sink, V_S = 24 V", "sink", 24.0),
            ("sink, +-100-V stage", "sink", 90.0)]
    print("\n== 1-2. Resistor floor, Eqs. (1), (2) and (4)")
    for name, kind, v in rows:
        if kind == "ref":
            desc, s = f"R_F = {R_F:g} kOhm", s_ref
        elif kind == "sink":
            r_s, s = floor_sink(v)
            desc = f"V_S = {v:g} V: R_s = {v:g}/{I_MAX:g} = {r_s:.3g} kOhm; {FOUR_KT:.2f} x (1/{R_F:g} + 1/{r_s:.3g})"
        else:
            r1, s = floor_plain(v)
            desc = f"V_A = {v:g} V: R_F' = {r1:.3g} kOhm; {FOUR_KT:.2f}/{r1:.3g}"
        i_eq = s / SHOT * 1e3                                # uA
        exc = [10 * math.log10(1 + i_eq / (i * 1e3)) for i in CURRENTS]
        power = "" if v is None else f"; P = V x I_max = {v * I_MAX / 1e3:.3g} W"
        print(f"  {name}: {desc} = {s:.2f} pA^2/Hz = {math.sqrt(s):.2f} pA/rtHz, "
              f"{10 * math.log10(s / s_ref):+.2f} dB on 2 kOhm; I_eq = {i_eq:.1f} uA; "
              f"excess over shot at 0.1 / 1 / 10 mA = {exc[0]:.2f} / {exc[1]:.3f} / {exc[2]:.4f} dB{power}")

    print("\n== 1. Break-even voltage of the sink, Eq. (3)")
    for v_a in (2.86, 5.0, 10.0, 15.0):
        ir = I_MAX * R_F
        print(f"  V_A = {v_a:g} V: V_S > {v_a:g} x {ir:g} / ({ir:g} - {v_a:g}) = {v_a * ir / (ir - v_a):.3g} V")
    for v in (5.0, 10.0, 20.0, 40.0):
        x = I_MAX * R_F / v
        print(f"  equal voltage {v:g} V: x = {x:.2f}, (1 + x)/max(1, x) = {(1 + x) / max(1, x):.3f} "
              f"= {10 * math.log10((1 + x) / max(1, x)):.2f} dB in favour of the plain TIA")

    f24, f10 = floor_sink(24.0)[1], floor_plain(10.0)[1]
    print(f"  sink at 24 V against plain at 10 V: 10 log10({f10:.2f}/{f24:.2f}) = {10 * math.log10(f10 / f24):.2f} dB; "
          f"at 1 mA the 24-V sink dissipates {24 * 1e-3 * 1e3:.0f} mW and its floor is "
          f"{FOUR_KT * (1 / R_F + 1 / 24.0):.2f} pA^2/Hz ({10 * math.log10((1 / R_F + 1 / 24.0) * R_F):+.2f} dB on 2 kOhm)")

    print("\n== 3. OPA855 band noise over 0-150 MHz with a sink, Eq. (5)")
    for v_s in (None, 5.0, 12.0, 20.0, 24.0, 90.0):
        extra = 0.0 if v_s is None else FOUR_KT / (v_s / I_MAX)
        parts = []
        for i in (0.0,) + CURRENTS:
            tot = math.sqrt(BAND_OPA855 ** 2 + (extra + SHOT * i) * NA2_PER_PA2HZ)
            base = math.sqrt(BAND_OPA855 ** 2 + SHOT * i * NA2_PER_PA2HZ)
            parts.append(f"{i:g} mA {tot:.1f} nA ({20 * math.log10(tot / base):+.2f} dB)")
        label = "no sink" if v_s is None else f"V_S = {v_s:g} V (R_s = {v_s / I_MAX:.3g} kOhm, +{extra:.2f} pA^2/Hz = +{extra * NA2_PER_PA2HZ:.0f} nA^2)"
        print(f"  {label}: " + "; ".join(parts))

    print("\n== 4. OPA846's e_n at 100 Hz on the node's conductance, Eq. (6)")
    e_n = 1.2 * math.sqrt(1 + 1.9 / 0.1)
    print(f"  e_n(100 Hz) = 1.2 x sqrt(1 + 1.9/0.1) = {e_n:.3f} nV/rtHz, e_n^2 = {e_n ** 2:.2f}")
    print(f"  no sink: {e_n ** 2:.2f} x (1/{R_F:g})^2 = {e_n ** 2 / R_F ** 2:.2f} pA^2/Hz")
    for v_s in (12.0, 24.0, 90.0):
        r_s = v_s / I_MAX
        print(f"  sink V_S = {v_s:g} V: {e_n ** 2:.2f} x (1/{R_F:g} + 1/{r_s:.3g})^2 = {e_n ** 2 * (1 / R_F + 1 / r_s) ** 2:.2f} pA^2/Hz")
    print(f"  plain V_A = 10 V with the same e_n: {e_n ** 2:.2f} x (1/1)^2 = {e_n ** 2:.2f} pA^2/Hz")
    i_n = 2.8 * math.sqrt(1 + 0.45 / 0.1)
    print(f"  OPA846's i_n(100 Hz) = 2.8 x sqrt(1 + 0.45/0.1) = {i_n:.2f} pA/rtHz, {i_n ** 2:.1f} pA^2/Hz")
    s_r12 = floor_sink(12.0)[1]
    tot0 = FOUR_KT / R_F + e_n ** 2 / R_F ** 2 + i_n ** 2
    tot12 = s_r12 + e_n ** 2 * (1 / R_F + 1 / 1.2) ** 2 + i_n ** 2
    share = (e_n ** 2 * (1 / R_F + 1 / 1.2) ** 2 - e_n ** 2 / R_F ** 2) / (tot12 - tot0)
    print(f"  OPA846's total at 100 Hz in the dark: {FOUR_KT / R_F:.2f} + {e_n ** 2 / R_F ** 2:.2f} + {i_n ** 2:.1f} = {tot0:.1f} pA^2/Hz "
          f"without a sink, {s_r12:.2f} + {e_n ** 2 * (1 / R_F + 1 / 1.2) ** 2:.1f} + {i_n ** 2:.1f} = {tot12:.1f} with the 12-V sink, "
          f"{10 * math.log10(tot12 / tot0):+.2f} dB; e_n's share of the rise {100 * share:.0f} %")
    e_s, r_s12 = 20.0, 1.2
    print(f"  servo noise {e_s:g} nV/rtHz through {r_s12:g} kOhm: {e_s / r_s12:.1f} pA/rtHz, {(e_s / r_s12) ** 2:.0f} pA^2/Hz, "
          f"{(e_s / r_s12) ** 2 / s_r12:.1f} times the 12-V floor; sqrt(4 k_B T R_s) = "
          + ", ".join(f"{math.sqrt(4 * KT * r * 1e3) * 1e9:.2f} nV/rtHz at {r:g} kOhm" for r in (1.2, 2.4)))

    print("\n== 5. Excess noise of the DC-carrying resistor, Eq. (7)")
    for ni, why in ((20 * math.log10(0.05), "TNPW e3 chart, 0.05 uV/V (document 28758, p. 9)"), (-32.0, "Section 6.9's requirement")):
        for i_ma in (1.0, 10.0):
            for f in (100.0, 1000.0):
                s = 10 ** (ni / 10) * 1e-12 * (i_ma * 1e-3) ** 2 / (f * math.log(10)) * 1e24
                print(f"  NI = {ni:.2f} dB ({why}), I = {i_ma:g} mA, f = {f:g} Hz: 10^({ni / 10:.3f}) x 1e-12 x ({i_ma:g}e-3)^2 / "
                      f"({f:g} x ln 10) = {s:.4g} pA^2/Hz, {100 * s / (SHOT * i_ma):.2f} % of the shot noise")

    print("\n== 6. Power and self-heating of the DC-carrying resistor (TNPW e3, document 28758)")
    p70 = {"0402": 0.070, "0603": 0.110, "0805": 0.140, "1206": 0.270}       # W, general mode, film <= 125 degC (p. 2)
    print("  largest voltage at 10 mA, P_70 / I: " + ", ".join(f"{k} {p / (I_MAX * 1e-3):.0f} V" for k, p in p70.items()))
    theta = (125 - 70) / p70["1206"]
    print(f"  theta(1206) = (125 - 70) K / {p70['1206']} W = {theta:.0f} K/W; power and advanced modes: "
          f"{(155 - 70) / 0.420:.0f} and {(175 - 70) / 0.520:.0f} K/W")
    for v in (10.0, 24.0):
        p = v * I_MAX / 1e3
        for alpha in (25, 10):
            dr = alpha * theta * p
            print(f"  V = {v:g} V at {I_MAX:g} mA: P = {p:.3g} W, dT = {theta * p:.1f} K, dR/R = {dr:.0f} ppm at {alpha} ppm/K "
                  f"({20 * math.log10(1 + dr * 1e-6):.4f} dB)")

    print("\n== 7. The later stage that rejects the DC")
    for e_f in (1.0, 2.0, 5.0):
        print(f"  (a) e_f = {e_f:g} nV/rtHz: through R_F' = 1 kOhm {e_f ** 2:.2f} pA^2/Hz, through R_F = 2 kOhm {e_f ** 2 / 4:.2f} pA^2/Hz")
    for r_v in (1.0, 1.2):
        e_be = math.sqrt((FOUR_KT / R_F) / (1 / r_v ** 2 - 1 / R_F ** 2))
        print(f"  (a) Eq. (8), equal voltage with R_V = {r_v:g} kOhm: e_f = sqrt({FOUR_KT / R_F:.3f} / "
              f"(1/{r_v:g}^2 - 1/{R_F:g}^2)) = {e_be:.2f} nV/rtHz")
    f_hp, f = 10.0, 100.0
    for r in (10e3, 1e6):
        e_r = math.sqrt(4 * KT * r) * 1e9
        e_out = e_r / math.sqrt(1 + (f / f_hp) ** 2)
        print(f"  (b) R = {r / 1e3:g} kOhm, C = {1 / (2 * math.pi * f_hp * r) * 1e9:.3g} nF for {f_hp:g} Hz: e_R = {e_r:.2f} nV/rtHz, "
              f"at {f:g} Hz {e_out:.3f} nV/rtHz, through 1 kOhm {e_out:.3f} pA/rtHz = {e_out ** 2:.2f} pA^2/Hz")
    d_i, v_sat = 10.0, 1.52
    for f_hp in (10.0, 1000.0):
        tau = 1 / (2 * math.pi * f_hp)
        ratio = d_i * R_F / v_sat
        print(f"  (c) dI = {d_i:g} mA, f_HP = {f_hp:g} Hz, tau = {tau * 1e3:.3g} ms, dI R_F / V_sat = {d_i * R_F:g}/{v_sat:g} = {ratio:.2f}: "
              f"sink {ratio * tau * 1e3:.3g} ms (Eq. (9)), capacitor-coupled {math.log(ratio) * tau * 1e3:.3g} ms (Eq. (10))")

    print("\n== 8. Laser RIN (the note's Eq. (72j))")
    db = lambda x: 10 * math.log10(x)                                         # noqa: E731
    print("  RIN_shot = 2q/I_DC: " + ", ".join(f"{db(2 * Q / (i * 1e-3)):.1f} dB/Hz at {i:g} mA" for i in (10.0, 1.0, 0.1)))
    rin_ex = {f: (0.05e-6) ** 2 / (f * math.log(10)) for f in (100.0, 1000.0)}
    print("  excess noise of the DC resistor, 0.05 uV/V: " + ", ".join(f"{db(r):.1f} dB/Hz at {f:g} Hz" for f, r in rin_ex.items())
          + f"; {db(2 * Q / 10e-3) - db(rin_ex[100.0]):.1f} dB below RIN_shot at 10 mA; equal at 100 Hz for "
          f"I = 2q/RIN = {2 * Q / rin_ex[100.0] * 1e3:.1f} mA")
    print(f"  servo noise (e_s/V_S)^2, 20 nV/rtHz on 12 V: {db((20e-9 / 12) ** 2):.1f} dB/Hz")
    for name, s_pa2 in (("OPA855 at 100 Hz, 113 pA/rtHz (Section 4.2)", 113.0 ** 2), ("OPA855 at 1 kHz, 36.1 pA/rtHz", 36.1 ** 2),
                        ("OPA846 at 100 Hz, 7.20 + 43.1 pA^2/Hz", 7.20 + 43.1)):
        rin = s_pa2 * 1e-24 / (10e-3) ** 2
        print(f"  {name}: {db(rin):.1f} dB/Hz at 10 mA, {db(rin) - db(2 * Q / 10e-3):+.1f} dB on RIN_shot")
    print(f"  high-pass at f_HP: the RIN read at f is low by 10 log10(1 + f_HP^2/f^2): {db(2):.2f} dB at the corner, "
          f"{db(1 + 0.01):.3f} dB a decade above")


P_1206 = 0.270     # W: TNPW1206 e3 with its film at up to 125 degC (Vishay document 28758, p. 2)


def draw(out_stem):
    """Figure 33: Eqs. (1) and (2) in dB on 2 kOhm alone, with the configurations of Table 8.1."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.ticker import FixedFormatter, FixedLocator, NullLocator

    colors = {"primary": "#385C9E", "warm": "#9E403D", "annotation": "#767676", "text": "#272727",
              "axes": "#000000", "highlight": "#EED671"}
    plt.rcParams.update({
        "figure.facecolor": "#FFFFFF", "axes.facecolor": "#FFFFFF", "axes.edgecolor": colors["axes"],
        "axes.labelcolor": colors["text"], "text.color": colors["text"], "xtick.color": colors["axes"],
        "ytick.color": colors["axes"], "font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans", "sans-serif"],
        "font.size": 8.0, "axes.labelsize": 8.0, "xtick.labelsize": 8.0, "ytick.labelsize": 8.0, "legend.fontsize": 8.0,
        "axes.linewidth": 0.8, "xtick.top": True, "ytick.right": True, "xtick.direction": "in", "ytick.direction": "in",
        "legend.frameon": False, "axes.grid": False, "text.usetex": False, "mathtext.fontset": "cm",
        "axes.formatter.use_mathtext": True, "pdf.fonttype": 42, "ps.fonttype": 42, "savefig.facecolor": "white",
        "savefig.bbox": "tight"})

    def db_sink(v):
        return 10 * np.log10(1 + I_MAX * R_F / np.asarray(v, dtype=float))

    def db_plain(v):
        return 10 * np.log10(np.maximum(1.0, I_MAX * R_F / np.asarray(v, dtype=float)))

    v = np.logspace(0, 2, 600)
    fig, ax = plt.subplots(figsize=(4.2, 3.24), constrained_layout=True)
    v_limit = P_1206 / (I_MAX * 1e-3)                                  # 27 V at 10 mA
    ax.axvspan(v_limit, 100, color=colors["highlight"], alpha=0.24, linewidth=0, zorder=0, label="_nolegend_")
    ax.text(50, 12.6, "more than 0.27 W\nin a 1206 at 10 mA", ha="center", va="top", color=colors["annotation"])
    ax.plot(v, db_sink(v), color=colors["primary"], linewidth=1.5, label="Sink of Option A, Eq. (72a)")
    ax.plot(v, db_plain(v), color=colors["warm"], linewidth=1.5, linestyle=(0, (5, 2)),
            label="Plain DC-coupled TIA, Eq. (72d)")
    sinks = ((5.0, "Option A as drawn", (7, 3), "left"), (12.0, "±12-V servo", (6, 3), "left"),
             (20.0, None, None, None), (24.0, "24 V", (0, -6), "center"), (90.0, "90 V", (-2, 6), "right"))
    for vs, text, off, ha in sinks:
        y = float(db_sink(vs))
        ax.plot(vs, y, "o", color=colors["primary"], markersize=4, zorder=3)
        if text:
            ax.annotate(text, (vs, y), xytext=off, textcoords="offset points", ha=ha,
                        va="bottom" if off[1] > 0 else "top")
    plains = ((2.86, "Option D", (-6, -3), "right", "top"), (10.0, "10 V", (-5, -4), "right", "top"),
              (20.0, "20 V", (5, 2), "left", "bottom"))
    for va_, text, off, ha, va in plains:
        y = float(db_plain(va_))
        ax.plot(va_, y, "s", color=colors["warm"], markersize=4, zorder=3, clip_on=False)
        ax.annotate(text, (va_, y), xytext=off, textcoords="offset points", ha=ha, va=va, color=colors["warm"])
    ax.annotate("", xy=(20.0, float(db_sink(20.0))), xytext=(10.0, float(db_plain(10.0))),
                arrowprops=dict(arrowstyle="->", color=colors["annotation"], linewidth=0.8, shrinkA=4, shrinkB=4))
    ax.set_xscale("log")
    ax.set_xlim(1, 100)
    ax.set_ylim(0, 14)
    ticks = [1, 2, 5, 10, 20, 50, 100]
    ax.xaxis.set_major_locator(FixedLocator(ticks))
    ax.xaxis.set_major_formatter(FixedFormatter([str(t) for t in ticks]))
    ax.xaxis.set_minor_locator(NullLocator())
    ax.set_xlabel("Voltage across the resistor that carries the DC (V)")
    ax.set_ylabel("Resistor floor relative to 2 kΩ alone (dB)")
    ax.legend(loc="lower left")
    out = str(out_stem)
    fig.savefig(out + ".png", dpi=600)
    fig.savefig(out + ".pdf")
    plt.close(fig)
    print(f"Figure 33 written to {out}.png and .pdf; the shaded range starts at {P_1206:g} W / {I_MAX:g} mA = {v_limit:.0f} V")


if __name__ == "__main__":
    main()
    if "--figure" in sys.argv:
        draw(sys.argv[sys.argv.index("--figure") + 1])
