"""OPA846 at R_F = 1.5 kOhm on the node of Chapter 4: the parasitic feedback capacitance alone, and the nearly
flat design, at large amplitude (Section 4.10 of the note).

Usage:
    python case_opa846_1k5.py run    [--ngspice LIB] [--spice SPICE_DIR] [--steps slew loop osc steps tones]
    python case_opa846_1k5.py report [--spice SPICE_DIR]
    python case_opa846_1k5.py figure [--spice SPICE_DIR] [--out OUT_STEM]

'run' simulates with the vendor's macromodel in ngspice (decks under <spice>/runs/case_OPA846_1k5/, which the
archive does not keep) and evaluates the closed forms below and our analytical model (case_studies.Analytic, the
datasheet open-loop curve of Section 3.5); everything goes to <spice>/results/case_opa846_1k5.json.  'report'
prints the numbers of Section 4.10 and Tables 4.2 and 4.3 from that file; 'figure' draws Figure 9 from it, in
the files figures/fig37b_case_opa846_1k5.png and .pdf.  --steps runs only the named parts and keeps the others
from the existing file.  The equation numbers below are those of the note, Eqs. (36a)-(36g).

The circuit is the OPA846 design of Section 4.4 (Table 4.1, Figure 5) with R_F = 1.5 kOhm: the pair's 1 pF plus
0.35 pF of board at the summing node, and the amplifier's C_CM + C_DIFF = 3.8 pF, so C_T = 5.15 pF (Eq. (7)).
Two feedback capacitances are studied:
  - the parasitic alone, C_F,par = 0.08 pF with the corners 0.05 and 0.12 pF of Table 1.1;
  - the flat design, 0.70 pF in total (0.62 pF fitted beside the parasitic), the C_F at which the
    macromodel's transimpedance stops peaking (0.65 dB at 0.60 pF, none at 0.70 pF).
Small-signal runs use the supply and load of Section 4.5 (+/-5 V, 100 ohm, the load of the datasheet's
open-loop curve); the large-signal runs those of Section 4.7 (+/-6 V, 1 Mohm).

The closed forms
----------------
(a) Phase margin, Eq. (17):  phi_M = [180 deg + angle A(f_c)] - [arctan(f_c/f_z) - arctan(f_c/f_p)],
    f_z = 1/(2 pi R_F (C_T + C_F)),  f_p = 1/(2 pi R_F C_F).  With the parasitic alone f_p lies near 1.3 GHz,
    far above the crossover, so the noise gain's lead arctan(f_c/f_p) is only about 8 deg and the amplifier's
    own phase must carry the loop.

(b) Where an unstable loop settles.  The oscillation grows at the frequency f_osc where the loop phase reaches
    -180 deg, until the amplifier's gain at that frequency has fallen by the loop's excess gain |T(f_osc)|.  A
    voltage-feedback amplifier whose compensation capacitance C_c is charged by its input stage of tail current
    I_T and transconductance g_m has SR = I_T/C_c and GBW = g_m/(2 pi C_c).  To deliver an output of amplitude V
    at f the stage must supply C_c 2 pi f V, i.e. the fraction
        x = 2 pi f V / SR = V / V_SR(f),      V_SR(f) = SR/(2 pi f)                                  (36a)
    of I_T.  For x << 1 the stage is linear; as x approaches 1 it saturates, the gain at f falls, and the
    oscillation stops growing.  It grows near the loop's crossover f_c, and the amplitude it settles at is close
    to V_SR there:
        V_osc ~ SR/(2 pi f_c).                                                                         (36b)
    Which slew rate applies is itself a question.  The datasheet's 625 V/us is the 10-90 % slope of a 2-V step
    (PDF p3).  A sine that slews fully becomes a triangle of slope +/-SR, peak SR/(4f) and fundamental
    (8/pi^2) SR/(4f) = 2 SR/(pi^2 f).  At the -3 dB point of the datasheet's 5-Vpp large-signal response,
    85 MHz at G = +10 (PDF p4), that fundamental is 2.5 V x 10^(-3/20) = 1.77 V, so the part slews a sine at
        SR_sine = pi^2 f V_1 / 2 = pi^2 x 85 MHz x 1.77 V / 2 = 742 V/us,                               (36c)
    19 % above the step's 625 V/us.

(c) Slew limiting of a step.  A linear step response whose steepest slope is S_1 per volt of step slews from
    the step
        V_step,SR = SR / S_1.                                                                         (36d)

(d) Distortion from the same input stage below the slew limit.  Let the stage be a bipolar pair,
    i = I_T tanh(v_d/V_ov) with V_ov = I_T/g_m = SR/(2 pi GBW) (for OPA846, 625 V/us and 1750 MHz give
    56.8 mV, close to the 2 V_T = 51.4 mV of an undegenerated pair).  A sine output V sin(wt) needs
    i/I_T = x cos(wt), hence v_d = V_ov artanh(x cos wt) = V_ov [x cos wt + (x^3/3) cos^3 wt + ...].  The cubic
    term is an error voltage at the input with a third harmonic of amplitude V_ov x^3/12, which the loop carries
    to the output like any input-referred voltage, through H_e = A/(1 + A/NG) = NG T/(1 + T) at 3f:
        HD3 = (V_ov / (12 V)) x^3 |H_e(3f)| = (V_ov |H_e(3f)| / (12 V_SR(f))) x^2.                        (36e)
    It has no free parameter.  In the datasheet's G = +10 circuit (NG = 10, 2 Vpp) it gives -104.4, -86.4, -75.8
    and -68.4 dBc at 5, 10, 15 and 20 MHz against the curve's -113, -89.5, -77.5 and -69.8 dBc (PDF p5), close
    where the slew-induced term dominates and pessimistic below 10 MHz, where the curve falls faster.
    The second harmonic needs an asymmetry that the symmetric pair does not contain.  Written as an input error
    c_2 V_ov x^2 at 2f, the lowest even term of the same expansion, it reaches the output as
        HD2 = c_2 (V_ov |H_e(2f)| / V_SR(f)) x,                                                         (36f)
    and c_2 = 0.0215 is fitted to the datasheet's 20-MHz HD2 at 200 ohm (-66.2 dBc, PDF p5); with it Eq. (36f)
    gives -90.2, -78.2 and -71.2 dBc at 5, 10 and 15 MHz against the curve's -86.0, -76.2 and -70.1 dBc.  The
    datasheet's HD2 at 5 MHz falls from -76 to -99.3 dBc between 100 and 500 ohm (PDF p5), so most of it comes
    from the load current, and the TIA's lighter load makes Eq. (36f) an upper estimate there.
    Solving Eqs. (36e) and (36f) for V gives the amplitudes at which each harmonic reaches a level D (as a ratio):
        V_D,3 = V_SR(f) sqrt(12 D V_SR(f) / (V_ov |H_e(3f)|)),   V_D,2 = D V_SR(f)^2 / (c_2 V_ov |H_e(2f)|);   (36g)
    the two together, added in power, reach D where HD2^2 + HD3^2 = D^2, a quadratic in V^2.

Datasheet inputs (OPA846, SBOS250E): SR 625 V/us typical, 500 V/us minimum at 25 degC (2-V step, G = +10,
PDF p3); GBP 1750 MHz (G >= +40, PDF p3); swing -4.44 to +4.16 V on +/-6 V (PDF p8), 4.30 V centred; output
current 80 mA (PDF p3); HD2/HD3 against frequency at G = +10, 2 Vpp, 200 ohm (PDF p5).
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

import case_studies as cs
import tia_model as tm
from spice_tia_checks import header, loop_metrics_from_T, prepared_model, read_wrdata, run, tia_body, write_deck, zt_metrics

HERE = Path(__file__).resolve().parent
PART = "OPA846"
R_F = 1500.0
C_D = 1.0e-12
CF_PAR = (0.05e-12, 0.08e-12, 0.12e-12)        # Table 1.1: nominal 0.08 pF, corners 0.05 and 0.12 pF
CF_FLAT = 0.70e-12                              # nearly flat design: 0.62 pF fitted + 0.08 pF parasitic
CF_SCAN = (0.05, 0.08, 0.12, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 1.00, 1.10)   # pF, Figure 9a
VS_SMALL, RL_SMALL = 5.0, 100.0                 # Section 4.5
VS_LARGE, RL_LARGE = 6.0, 1e6                   # Section 4.7
SR_DS, SR_DS_MIN = 625e6, 500e6                 # V/s, PDF p3
GBW_DS = 1750e6                                 # Hz, PDF p3
V_SW = (4.16 + 4.44) / 2                        # V, +/-6 V swing, PDF p8
V_OV = SR_DS / (2 * math.pi * GBW_DS)           # V, Eq. (36e)
# Eq. (36c): the slope a fully slewing sine reaches, from the 5-Vpp large-signal -3-dB frequency (PDF p4, 85 MHz)
SR_SINE = (5.0 / 2) * 10 ** (-3 / 20) * math.pi ** 2 * 85e6 / 2
TONE_F = (20e6, 50e6, 100e6, 150e6)
FRACTIONS = (0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3)
STEP_OUT_V = (0.1, 0.5, 1.0, 2.0, 4.0)         # output steps of the flat design, V
SLEW_STEPS_V = (0.2, 2.0, 4.0, 6.0)            # output steps of the datasheet's G = +10 circuit
DS_HD3 = {5e6: -113.0, 10e6: -89.5, 15e6: -77.5, 20e6: -69.8}   # dBc, PDF p5, 2 Vpp, 200 ohm, G = +10
RESULTS = "case_opa846_1k5.json"


def deck_folder(spice, name):
    """Two levels below runs/, so that header()'s '.include ../../_models/...' resolves."""
    return spice / "runs" / "case_OPA846_1k5" / name.replace(".", "p")


# ---------------------------------------------------------------- SPICE
def slew_test(ng, spice):
    """The datasheet's AC test circuit (PDF p3: G = +10, R_F = 453 ohm, R_G = 50 ohm, R_L = 100 ohm, +/-5 V):
    output steps centred on 0 V, 20-ps input edges; returns the 10-90 % rise, the average slope over it
    (0.8 step / t_r) and the steepest slope."""
    out = []
    for step in SLEW_STEPS_V:
        vin = step / 20.0
        folder = deck_folder(spice, f"slew_{step:g}V")
        deck = header(PART, f"OPA846 slew test, G = +10, {step:g}-V output step", 5.0) + (
            "XU1 inp inm vcc vee oa OPA846\nRF oa inm 453\nRG inm 0 50\nRL oa 0 100\n"
            f"VIN inp 0 PULSE({-vin:g} {vin:g} 5n 20p 20p 25n 50n)\n"
            ".control\nset wr_singlescale\nset wr_vecnames\ntran 2p 30n 0 2p\nlinearize v(oa)\nwrdata slew.txt v(oa)\n"
            ".endc\n.end\n")
        log, err = run(ng, write_deck(folder, deck))
        d = read_wrdata(folder / "slew.txt")
        t, v = d[:, 0], d[:, 1]
        v0 = float(np.mean(v[(t > 3e-9) & (t < 4.9e-9)]))
        v1 = float(np.mean(v[(t > 25e-9) & (t < 29.5e-9)]))
        after = t > 5e-9
        i10 = np.where(after & (v - v0 >= 0.1 * (v1 - v0)))[0][0]
        i90 = np.where(after & (v - v0 >= 0.9 * (v1 - v0)))[0][0]
        tr = float(t[i90] - t[i10])
        slope = np.diff(v) / np.diff(t)
        out.append(dict(step_V=step, swing_V=v1 - v0, rise_10_90_ns=tr * 1e9, avg_slope_V_per_us=0.8 * (v1 - v0) / tr / 1e6,
                        max_slope_V_per_us=float(np.max(slope[after[1:]])) / 1e6, errors=err[:1]))
    return out


LSBW_F = (20e6, 50e6, 70e6, 85e6, 100e6, 120e6, 150e6, 191e6, 250e6)
DS_LSBW = {5.0: 85e6, 2.0: 191e6}               # -3 dB at G = +10, 100 ohm, PDF p4 (noninverting large-signal response)


def lsbw_test(ng, spice):
    """The datasheet's noninverting large-signal frequency response (PDF p4: G = +10, 453/50 ohm, 100 ohm, +/-5 V):
    a sine input of V_pp/20 peak; the output's fundamental against frequency, and the -3 dB frequency (17 dB)."""
    out = {}
    for vpp, f_ds in DS_LSBW.items():
        rows = []
        for f0 in LSBW_F:
            folder = deck_folder(spice, f"lsbw_{vpp:g}Vpp_{f0 / 1e6:g}M")
            period = 1 / f0
            tstep, tstop = period / 256, 48 * period
            deck = header(PART, f"OPA846 G = +10, {vpp:g} Vpp at {f0 / 1e6:g} MHz", 5.0) + (
                "XU1 inp inm vcc vee oa OPA846\nRF oa inm 453\nRG inm 0 50\nRL oa 0 100\n"
                f"VIN inp 0 SIN(0 {vpp / 20:g} {f0:g})\n"
                f".control\nset wr_singlescale\nset wr_vecnames\ntran {tstep:.4e} {tstop:.4e} 0 {tstep:.4e}\n"
                "linearize v(oa)\nwrdata ls.txt v(oa)\n.endc\n.end\n")
            log, err = run(ng, write_deck(folder, deck))
            d = read_wrdata(folder / "ls.txt")
            t, v = d[:, 0], d[:, 1]
            sel = t >= tstop - 32 * period - tstep / 2
            vv = v[sel][:32 * 256]
            vv = vv - np.mean(vv)
            spec = np.abs(np.fft.rfft(vv * np.hanning(len(vv))))
            v1 = float(4 * spec[32] / len(vv))
            rows.append(dict(f_MHz=f0 / 1e6, v1_V=v1, gain_dB=20 * math.log10(v1 / (vpp / 20)),
                             max_slope_V_per_us=float(np.max(np.abs(np.diff(vv) / tstep))) / 1e6, errors=err[:1]))
        f3 = None
        for r0, r1 in zip(rows, rows[1:]):
            if r0["gain_dB"] >= 17.0 > r1["gain_dB"]:
                f3 = 10 ** (math.log10(r0["f_MHz"]) + (17.0 - r0["gain_dB"]) / (r1["gain_dB"] - r0["gain_dB"])
                            * (math.log10(r1["f_MHz"]) - math.log10(r0["f_MHz"])))
        out[f"{vpp:g}"] = dict(rows=rows, f3_MHz=f3, datasheet_f3_MHz=f_ds / 1e6)
    return out


DS_HD2 = {1e6: -90.8, 2e6: -88.6, 5e6: -86.0, 10e6: -76.2, 15e6: -70.1, 20e6: -66.2}   # dBc, PDF p5, as DS_HD3
# 5-MHz distortion against the load, 2 Vpp, G = +10: (HD2, HD3) in dBc from the curve of PDF p5 ("5MHz harmonic
# distortion vs load resistance"; HD3 is drawn only to 200 ohm); 500 ohm HD3 from the table of PDF p3
DS_LOAD_5M = {100: (-76.0, -109.0), 150: (-81.0, -111.0), 200: (-86.0, -112.9), 300: (-92.4, None),
              400: (-95.8, None), 500: (-99.3, -112.0)}
QUIESCENT_DS_mA = 12.6                           # PDF p3, +/-5 V


def g10_tone(ng, spice, f0, rl, name):
    """The datasheet's G = +10 circuit (PDF p3: R_F = 453 ohm, R_G = 50 ohm, +/-5 V) with a 2-Vpp output at f0 into
    rl: the output's fundamental, HD2 and HD3 (last 32 of 48 periods, Hann window) and the mean supply current."""
    folder = deck_folder(spice, name)
    period = 1 / f0
    tstep, tstop = period / 256, 48 * period
    deck = header(PART, f"OPA846 G = +10, 2 Vpp into {rl:g} ohm at {f0 / 1e6:g} MHz", 5.0) + (
        f"XU1 inp inm vcc vee oa OPA846\nRF oa inm 453\nRG inm 0 50\nRL oa 0 {rl:g}\n"
        f"VIN inp 0 SIN(0 0.1 {f0:g})\n"
        f".control\nset wr_singlescale\nset wr_vecnames\ntran {tstep:.4e} {tstop:.4e} 0 {tstep:.4e}\n"
        "linearize v(oa) i(VCC)\nwrdata hd.txt v(oa) i(VCC)\n.endc\n.end\n")
    log, err = run(ng, write_deck(folder, deck))
    d = read_wrdata(folder / "hd.txt")
    t, v, icc = d[:, 0], d[:, 1], d[:, -1]
    sel = t >= tstop - 32 * period - tstep / 2
    vv = v[sel][:32 * 256]
    vv = vv - np.mean(vv)
    spec = np.abs(np.fft.rfft(vv * np.hanning(len(vv))))
    h = [spec[32 * k] for k in (1, 2, 3)]
    return dict(v1_V=float(4 * h[0] / len(vv)), hd2_dBc=float(20 * np.log10(h[1] / h[0])),
                hd3_dBc=float(20 * np.log10(h[2] / h[0])), supply_mA=float(-np.mean(icc[sel])) * 1e3, errors=err[:1])


def hd_ds_test(ng, spice):
    """The datasheet's distortion test (PDF p5: G = +10, 2 Vpp, 200 ohm) at 1-20 MHz: the macromodel's HD2 and HD3
    against the curve's, and Eqs. (36e) and (36f) for the same circuit (NG = 10)."""
    an = cs.Analytic(PART)
    out = []
    for f0 in sorted(DS_HD2):
        r = g10_tone(ng, spice, f0, 200.0, f"hdds_{f0 / 1e6:g}M")
        A2, A3 = an.ol.A(np.array([2 * f0, 3 * f0]))
        v_sr = SR_DS / (2 * math.pi * f0)
        x = r["v1_V"] / v_sr
        eq3 = V_OV * abs(A3 / (1 + A3 / 10.0)) / (12 * v_sr) * x ** 2
        r.update(f_MHz=f0 / 1e6, ds_hd2_dBc=DS_HD2[f0], ds_hd3_dBc=DS_HD3.get(f0), eq3_dBc=20 * math.log10(eq3),
                 x=x, A2=float(abs(A2)))
        out.append(r)
    return out


def hd_load_test(ng, spice):
    """The datasheet's 5-MHz distortion against the load (PDF p5) and the macromodel's, 2 Vpp, G = +10; 1 Mohm gives
    the model's quiescent current."""
    out = []
    for rl in tuple(DS_LOAD_5M) + (1e6,):
        r = g10_tone(ng, spice, 5e6, float(rl), f"hdload_{rl:g}ohm")
        ds = DS_LOAD_5M.get(rl, (None, None))
        r.update(R_L_ohm=float(rl), ds_hd2_dBc=ds[0], ds_hd3_dBc=ds[1])
        out.append(r)
    return out


def ac_run(ng, spice, C_F, vs, rl, keep=False):
    """Loop gain by Middlebrook's double injection and the transimpedance, 100 kHz-30 GHz (as case_studies.spice_ac,
    with the supply and load given)."""
    folder = deck_folder(spice, f"ac_F{C_F * 1e12:.3f}p_V{vs:g}_R{rl:g}")
    deck = header(PART, f"OPA846 TIA 1.5k, C_F {C_F * 1e12:g} pF, +/-{vs:g} V, R_L {rl:g}", vs) + tia_body(
        PART, R_F, C_D + cs.C_PCB_NOM, C_F, rl, vinj_ac=1, iinj_ac=0) + (
        ".control\nset wr_singlescale\nset wr_vecnames\nac dec 100 100k 30G\n"
        "wrdata vinj.txt real(v(oa)) imag(v(oa)) real(v(fb)) imag(v(fb))\n"
        "alter @vinj[acmag] = 0\nalter @iinj[acmag] = 1\nac dec 100 100k 30G\n"
        "wrdata iinj.txt real(i(vinj)) imag(i(vinj))\n"
        "alter @iinj[acmag] = 0\nalter @iph[acmag] = 1\nac dec 100 100k 30G\n"
        "wrdata zt.txt real(v(oa)) imag(v(oa))\n.endc\n.end\n")
    log, err = run(ng, write_deck(folder, deck))
    v, c, z = (read_wrdata(folder / n) for n in ("vinj.txt", "iinj.txt", "zt.txt"))
    f = v[:, 0]
    Tv = -(v[:, 1] + 1j * v[:, 2]) / (v[:, 3] + 1j * v[:, 4])
    iv = c[:, 1] + 1j * c[:, 2]
    Ti = iv / (1 - iv)
    T = (Tv * Ti - 1) / (Tv + Ti + 2)
    Z = z[:, 1] + 1j * z[:, 2]
    lm, zm = loop_metrics_from_T(f, T), zt_metrics(z[:, 0], Z)
    # the frequency where the loop phase first reaches -180 deg, and |T| there
    ph = np.unwrap(np.angle(T))
    k = np.where(ph <= -math.pi)[0]
    f180 = float(f[k[0]]) if len(k) else None
    t180 = float(abs(T[k[0]])) if len(k) else None
    res = dict(C_F_pF=C_F * 1e12, vs=vs, rl=rl, f_c_MHz=lm["f_c_MHz"], pm_deg=lm["pm_deg"], gm_dB=lm["gm_dB"],
               f180_MHz=None if f180 is None else f180 / 1e6, T_at_f180=t180,
               f3_MHz=zm["f3_MHz"], peak_dB=zm["peak_dB"], f_peak_MHz=zm["f_peak_MHz"], errors=err[:1])
    return (res, f, T, Z) if keep else res


def kick(ng, spice, C_F, t_stop=400e-9):
    """The parasitic-only design on +/-6 V with 1 Mohm, kicked by a 10-uA photocurrent step at 2 ns."""
    folder = deck_folder(spice, f"kick_F{C_F * 1e12:.3f}p")
    deck = header(PART, f"OPA846 TIA 1.5k kick, C_F {C_F * 1e12:g} pF", VS_LARGE) + tia_body(
        PART, R_F, C_D + cs.C_PCB_NOM, C_F, RL_LARGE, iph="Iph 0 inm PULSE(0 10e-6 2n 20p 20p 1u 2u)") + (
        f".control\nset wr_singlescale\nset wr_vecnames\ntran 5p {t_stop:.4e} 0 5p\nlinearize v(oa)\nwrdata kick.txt v(oa)\n"
        ".endc\n.end\n")
    log, err = run(ng, write_deck(folder, deck))
    d = read_wrdata(folder / "kick.txt")
    t, v = d[:, 0], d[:, 1]
    win = []
    for a in np.arange(20e-9, t_stop - 1e-12, 20e-9):
        sel = (t >= a) & (t < a + 20e-9)
        vv = v[sel] - np.mean(v[sel])
        up = np.where(np.diff(np.sign(vv)) > 0)[0]
        f_osc = (len(up) - 1) / (t[sel][up[-1]] - t[sel][up[0]]) if len(up) > 2 else None
        win.append(dict(t0_ns=a * 1e9, pp_V=float(np.ptp(v[sel])), f_MHz=None if f_osc is None else f_osc / 1e6,
                        max_slope_V_per_us=float(np.max(np.abs(np.diff(v[sel]) / np.diff(t[sel])))) / 1e6))
    last = win[-1]
    return dict(C_F_pF=C_F * 1e12, windows=win, settled_pp_V=last["pp_V"], settled_f_MHz=last["f_MHz"],
                settled_max_slope_V_per_us=last["max_slope_V_per_us"], errors=err[:1],
                curve=dict(t_ns=(t[::20] * 1e9).round(4).tolist(), v=v[::20].round(5).tolist()))


def steps(ng, spice):
    """The flat design on +/-6 V with 1 Mohm: photocurrent steps whose final output is STEP_OUT_V, 20-ps rise."""
    out = []
    for vo in STEP_OUT_V:
        i = vo / R_F
        folder = deck_folder(spice, f"step_{vo:g}V")
        deck = header(PART, f"OPA846 TIA 1.5k flat, {vo:g}-V output step", VS_LARGE) + tia_body(
            PART, R_F, C_D + cs.C_PCB_NOM, CF_FLAT, RL_LARGE, iph=f"Iph 0 inm PULSE(0 {i:.6e} 2n 20p 20p 30n 60n)") + (
            ".control\nset wr_singlescale\nset wr_vecnames\ntran 1p 32n 0 1p\nlinearize v(oa)\nwrdata step.txt v(oa)\n"
            ".endc\n.end\n")
        log, err = run(ng, write_deck(folder, deck))
        d = read_wrdata(folder / "step.txt")
        t, v = d[:, 0], -d[:, 1]
        m = cs.step_metrics(t, v)
        slope = np.diff(v) / np.diff(t)
        m.update(step_V=vo, i_step_mA=i * 1e3, max_slope_V_per_us=float(np.max(slope[t[1:] > 2e-9])) / 1e6, errors=err[:1])
        sel = t <= 14e-9
        m["curve"] = dict(t_ns=(t[sel][::5] * 1e9).round(4).tolist(), v_norm=(v[sel][::5] / (m["step_mV"] / 1e3)).round(5).tolist())
        out.append(m)
    return out


def tone(ng, spice, f0, frac, claim, zmag):
    """case_studies.spice_tone with the 1.5-kOhm flat design and its own deck folder."""
    folder = deck_folder(spice, f"tone_f{f0 / 1e6:g}M_a{frac:g}")
    ipk = frac * claim / zmag
    period = 1 / f0
    tstep, tstop = period / 256, 48 * period
    deck = header(PART, f"OPA846 TIA 1.5k flat, tone {f0 / 1e6:g} MHz at {frac:g} x Eq. (26)", VS_LARGE) + tia_body(
        PART, R_F, C_D + cs.C_PCB_NOM, CF_FLAT, RL_LARGE, iph=f"Iph 0 inm SIN(0 {ipk:.6e} {f0:g})") + (
        f".control\nset wr_singlescale\nset wr_vecnames\ntran {tstep:.4e} {tstop:.4e} 0 {tstep:.4e}\n"
        f"linearize v(oa)\nwrdata tone.txt v(oa)\n.endc\n.end\n")
    log, err = run(ng, write_deck(folder, deck))
    d = read_wrdata(folder / "tone.txt")
    t, v = d[:, 0], d[:, 1]
    sel = t >= tstop - 32 * period - tstep / 2
    vv = v[sel][:32 * 256]
    vv = vv - np.mean(vv)
    spec = np.abs(np.fft.rfft(vv * np.hanning(len(vv))))
    h = [spec[32 * k] for k in (1, 2, 3, 4, 5)]
    # fundamental amplitude: the Hann window's coherent gain is 0.5, and rfft sums N samples
    v1 = float(2 * h[0] / (0.5 * len(vv)))
    return dict(frac=frac, ipk_mA=ipk * 1e3, v1_V=v1, hd2_dBc=float(20 * np.log10(h[1] / h[0])),
                hd3_dBc=float(20 * np.log10(h[2] / h[0])),
                thd_dBc=float(10 * np.log10(sum(x ** 2 for x in h[1:]) / h[0] ** 2)), errors=err[:1])


def crossing(xs, ys, level):
    """First x (log interpolation) at which y rises through level; None if it never does."""
    for (x0, y0), (x1, y1) in zip(zip(xs, ys), zip(xs[1:], ys[1:])):
        if y0 < level <= y1:
            return float(10 ** (math.log10(x0) + (level - y0) / (y1 - y0) * (math.log10(x1) - math.log10(x0))))
    return None


# ---------------------------------------------------------------- closed forms and our model
def analytic():
    an = cs.Analytic(PART)
    C_T = an.C_T(C_D)
    out = dict(C_T_pF=C_T * 1e12, V_ov_mV=V_OV * 1e3, loop={}, osc={}, flat={}, hd3_check={})
    for cf in CF_SCAN:
        out["loop"][f"{cf:g}"] = an.loop(R_F, C_D, cf * 1e-12)
    f = np.logspace(6, 10, 8000)
    # Eq. (17) for the parasitic alone, and the -180 deg frequency of the loop
    for C_F in CF_PAR:
        Z, NG, T = tm.tia_tf(f, an.ol, R_F, C_T, C_F)
        m = an.loop(R_F, C_D, C_F)
        fc = m["f_c_MHz"] * 1e6
        A_fc = an.ol.A(np.array([fc]))[0]
        f_z, f_p = 1 / (2 * math.pi * R_F * (C_T + C_F)), 1 / (2 * math.pi * R_F * C_F)
        phi_A = 180 + math.degrees(np.angle(A_fc))
        ang_ng = math.degrees(math.atan(fc / f_z) - math.atan(fc / f_p))
        ph = np.unwrap(np.angle(T))
        k = np.where(ph <= -math.pi)[0][0]
        f180 = float(f[k])
        out["osc"][f"{C_F * 1e12:g}"] = dict(
            f_c_MHz=fc / 1e6, f_z_MHz=f_z / 1e6, f_p_MHz=f_p / 1e6, phi_A_deg=phi_A, angle_NG_deg=ang_ng,
            pm_deg=phi_A - ang_ng, f180_MHz=f180 / 1e6, T_at_f180=float(abs(T[k])),
            V_osc_V=SR_DS / (2 * math.pi * fc), V_osc_sine_V=SR_SINE / (2 * math.pi * fc))         # Eq. (36b) at f_c
    def he(f, ng):
        """|H_e| = |A/(1 + A/NG)| at f, with A from the datasheet curve."""
        A = an.ol.A(np.array([f]))[0]
        return float(abs(A / (1 + A / ng)))

    # Eq. (36f): the second harmonic needs an asymmetry, whose size c_2 is fitted to the datasheet's 20-MHz HD2 in
    # its G = +10 circuit (NG = 10, 2 Vpp): HD2 = c_2 (V_ov |H_e(2f)| / V_SR(f)) x
    f_fit = 20e6
    v_sr20 = SR_DS / (2 * math.pi * f_fit)
    c2 = 10 ** (DS_HD2[f_fit] / 20) / (V_OV * he(2 * f_fit, 10.0) / v_sr20 * (1.0 / v_sr20))
    out["c2"] = c2
    # Eqs. (36e) and (36f) against the datasheet's G = +10 curves (NG = 10, 2 Vpp, 1 V peak)
    for fds in sorted(DS_HD3):
        v_sr = SR_DS / (2 * math.pi * fds)
        x = 1.0 / v_sr
        hd3 = V_OV * he(3 * fds, 10.0) / (12 * v_sr) * x ** 2
        hd2 = c2 * V_OV * he(2 * fds, 10.0) / v_sr * x
        out["hd3_check"][f"{fds / 1e6:g}"] = dict(eq3_dBc=20 * math.log10(hd3), datasheet_dBc=DS_HD3[fds],
                                                 eq3b_dBc=20 * math.log10(hd2), datasheet_hd2_dBc=DS_HD2[fds],
                                                 He=he(3 * fds, 10.0))
    # the flat design: transimpedance, slew limit in output volts and in photocurrent (Eq. (26)), and the
    # amplitudes at which Eqs. (36e), (36f) and their sum in power reach -60 and -40 dBc
    fl = {}
    for f0 in TONE_F:
        fa = np.array([f0, 2 * f0, 3 * f0])
        Z, NG, T = tm.tia_tf(fa, an.ol, R_F, C_T, CF_FLAT)
        A = an.ol.A(fa)
        He = np.abs(A / (1 + A / NG))
        v_sr = SR_DS / (2 * math.pi * f0)
        vpk, which = min(V_SW, v_sr), ("swing" if V_SW <= v_sr else "slew rate")          # Eq. (26)

        def thd(v):
            x = v / v_sr
            return math.hypot(c2 * V_OV * He[1] / v_sr * x, V_OV * He[2] / (12 * v_sr) * x ** 2)

        rec = dict(zt_ohm=float(abs(Z[0])), He_2f=float(He[1]), He_3f=float(He[2]), V_SR_V=v_sr, V_pk_V=vpk,
                   set_by=which, I_SR_mA=v_sr / abs(Z[0]) * 1e3, I_pk_mA=vpk / abs(Z[0]) * 1e3)
        for lvl in (-60, -40):
            D = 10 ** (lvl / 20)
            rec[f"V_hd3_m{-lvl}_V"] = v_sr * math.sqrt(12 * D * v_sr / (V_OV * He[2]))     # Eq. (36g)
            rec[f"V_hd2_m{-lvl}_V"] = D * v_sr ** 2 / (c2 * V_OV * He[1])                     # Eq. (36f) solved for V
            lo, hi = 1e-5, 100.0                                                              # bisection on the sum
            for _ in range(200):
                mid = math.sqrt(lo * hi)
                lo, hi = (mid, hi) if thd(mid) < D else (lo, mid)
            rec[f"V_thd_m{-lvl}_V"] = lo
        rec["hd_at_vpk_dBc"] = 20 * math.log10(thd(vpk))
        fl[f"{f0 / 1e6:g}"] = rec
    out["flat"] = fl
    # Eq. (36d): the steepest slope of our model's linear step response per volt
    t, v = an.step(R_F, C_D, CF_FLAT)
    s1 = float(np.max(np.diff(v) / np.diff(t))) / (cs.STEP_A * R_F)
    out["step"] = dict(S1_per_ns=s1 * 1e-9, V_step_SR_V=SR_DS / s1, V_step_SR_min_V=SR_DS_MIN / s1)
    return out


# ---------------------------------------------------------------- driver
def main_run(a):
    from ngspice_shared import NgSpice
    spice = Path(a.spice)
    path = spice / "results" / RESULTS
    res = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    ng = NgSpice(a.ngspice)
    prepared_model(PART, spice)
    res["settings"] = dict(R_F=R_F, C_D_pF=C_D * 1e12, C_F_par_pF=[x * 1e12 for x in CF_PAR], C_F_flat_pF=CF_FLAT * 1e12,
                           small=dict(vs=VS_SMALL, rl=RL_SMALL), large=dict(vs=VS_LARGE, rl=RL_LARGE),
                           SR_V_per_us=SR_DS / 1e6, SR_min_V_per_us=SR_DS_MIN / 1e6, GBW_MHz=GBW_DS / 1e6, V_sw=V_SW)
    res["analytic"] = analytic()
    if "slew" in a.steps:
        res["slew"] = slew_test(ng, spice)
        res["lsbw"] = lsbw_test(ng, spice)
    if "hdds" in a.steps:
        res["hd_ds"] = hd_ds_test(ng, spice)
        res["hd_load"] = hd_load_test(ng, spice)
    if "loop" in a.steps:
        res["loop"] = {"small": [ac_run(ng, spice, cf * 1e-12, VS_SMALL, RL_SMALL) for cf in CF_SCAN],
                       "large": [ac_run(ng, spice, cf, VS_LARGE, RL_LARGE) for cf in CF_PAR + (CF_FLAT,)]}
        _, f, T, Z = ac_run(ng, spice, CF_FLAT, VS_LARGE, RL_LARGE, keep=True)
        res["zt_flat_large"] = dict(f=f[::10].tolist(), mag=np.abs(Z)[::10].tolist())
    if "osc" in a.steps:
        res["osc"] = [kick(ng, spice, cf) for cf in CF_PAR]
    if "steps" in a.steps:
        res["steps"] = steps(ng, spice)
    if "tones" in a.steps:
        zt = res["zt_flat_large"]
        tones = {}
        for f0 in TONE_F:
            zmag = float(np.interp(math.log10(f0), np.log10(zt["f"]), zt["mag"]))
            claim = min(V_SW, SR_DS / (2 * math.pi * f0))
            rows = [tone(ng, spice, f0, fr, claim, zmag) for fr in FRACTIONS]
            amps = [r["v1_V"] for r in rows]
            tones[f"{f0 / 1e6:g}"] = dict(claim_V=claim, zt_ohm=zmag, rows=rows,
                                         thd_m60_V=crossing(amps, [r["thd_dBc"] for r in rows], -60),
                                         thd_m40_V=crossing(amps, [r["thd_dBc"] for r in rows], -40),
                                         hd3_m60_V=crossing(amps, [r["hd3_dBc"] for r in rows], -60),
                                         hd3_m40_V=crossing(amps, [r["hd3_dBc"] for r in rows], -40))
        res["tones"] = tones
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(res, indent=1), encoding="utf-8")
    print("written", path)


def main_report(a):
    res = json.loads((Path(a.spice) / "results" / RESULTS).read_text(encoding="utf-8"))
    an = res["analytic"]
    print(f"C_T = {an['C_T_pF']:.2f} pF; V_ov = SR/(2 pi GBW) = 625 V/us / (2 pi x 1750 MHz) = {an['V_ov_mV']:.1f} mV")
    print("== our model, loop against total C_F")
    for k, m in an["loop"].items():
        print(f"  {k} pF: f_c {m['f_c_MHz']:.1f} MHz, PM {m['pm_deg']:.1f}, GM {m['gm_dB']}, peak {m['peak_dB']:.2f} dB, f3 {m['f3_MHz']:.0f} MHz, stable {m['stable']}")
    print("== Eq. (17) and the -180-deg frequency, parasitic alone (our model)")
    for k, o in an["osc"].items():
        print(f"  {k} pF: f_c {o['f_c_MHz']:.1f} MHz, f_z {o['f_z_MHz']:.2f}, f_p {o['f_p_MHz']:.0f} MHz, phi_A {o['phi_A_deg']:.1f}, "
              f"angle NG {o['angle_NG_deg']:.1f}, PM {o['pm_deg']:.1f}; f180 {o['f180_MHz']:.1f} MHz, |T| there {o['T_at_f180']:.2f}; "
              f"Eq. (36b) at f_c: {o['V_osc_V']:.3f} V (625 V/us), {o['V_osc_sine_V']:.3f} V (742 V/us)")
    print(f"== Eqs. (36e) and (36f) against the datasheet's G = +10 curves (c_2 = {an['c2']:.4f}, fitted at 20 MHz)")
    for k, c in an["hd3_check"].items():
        print(f"  {k} MHz: HD3 Eq. (36e) {c['eq3_dBc']:.1f}, datasheet {c['datasheet_dBc']}; HD2 Eq. (36f) {c['eq3b_dBc']:.1f}, datasheet {c['datasheet_hd2_dBc']} dBc")
    print("== the flat design, Eqs. (36a), (36e)-(36g), (26)")
    for k, d in an["flat"].items():
        print(f"  {k} MHz: |Z_T| {d['zt_ohm']:.0f} ohm, V_SR {d['V_SR_V']:.3f} V, V_pk {d['V_pk_V']:.3f} V ({d['set_by']}), I_pk {d['I_pk_mA']:.3f} mA; "
              f"|H_e| {d['He_2f']:.2f} (2f), {d['He_3f']:.2f} (3f); -60 dBc: HD3 {d['V_hd3_m60_V']:.3f}, HD2 {d['V_hd2_m60_V']:.3f}, sum {d['V_thd_m60_V']:.3f} V; "
              f"-40 dBc: HD3 {d['V_hd3_m40_V']:.3f}, HD2 {d['V_hd2_m40_V']:.3f}, sum {d['V_thd_m40_V']:.3f} V; at V_pk {d['hd_at_vpk_dBc']:.1f} dBc")
    print(f"== Eq. (36d): S_1 = {an['step']['S1_per_ns']:.3f} /ns, V_step,SR = {an['step']['V_step_SR_V']:.3f} V ({an['step']['V_step_SR_min_V']:.3f} V at 500 V/us)")
    if "slew" in res:
        print("== the macromodel in the datasheet's G = +10 circuit")
        for s in res["slew"]:
            print(f"  {s['step_V']:g}-V step: swing {s['swing_V']:.3f} V, 10-90 % {s['rise_10_90_ns']:.3f} ns, average slope "
                  f"{s['avg_slope_V_per_us']:.0f} V/us, steepest {s['max_slope_V_per_us']:.0f} V/us")
    if "lsbw" in res:
        print("== the macromodel's large-signal response in the datasheet's G = +10 circuit (PDF p4)")
        for k, v in res["lsbw"].items():
            print(f"  {k} Vpp: -3 dB at {v['f3_MHz']} MHz (datasheet {v['datasheet_f3_MHz']:g} MHz); " +
                  ", ".join(f"{r['f_MHz']:g} MHz {r['gain_dB']:.2f} dB" for r in v["rows"]))
    if "hd_ds" in res:
        print("== the macromodel's distortion in the datasheet's G = +10 circuit, 2 Vpp, 200 ohm (PDF p5)")
        for r in res["hd_ds"]:
            print(f"  {r['f_MHz']:g} MHz: v1 {r['v1_V']:.3f} V, HD2 {r['hd2_dBc']:.1f} (datasheet {r['ds_hd2_dBc']}), "
                  f"HD3 {r['hd3_dBc']:.1f} (datasheet {r['ds_hd3_dBc']}), Eq. (36e) {r['eq3_dBc']:.1f} dBc, supply {r['supply_mA']:.2f} mA")
    if "hd_load" in res:
        print("== the same at 5 MHz against the load (PDF p5 curve; 500-ohm HD3 from PDF p3)")
        for r in res["hd_load"]:
            print(f"  {r['R_L_ohm']:g} ohm: HD2 {r['hd2_dBc']:.1f} (datasheet {r['ds_hd2_dBc']}), HD3 {r['hd3_dBc']:.1f} "
                  f"(datasheet {r['ds_hd3_dBc']}), supply {r['supply_mA']:.2f} mA")
    if "loop" in res:
        print("== SPICE loop gain")
        for kind in ("small", "large"):
            for m in res["loop"][kind]:
                print(f"  {kind} {m['C_F_pF']:.2f} pF: f_c {m['f_c_MHz']:.1f} MHz, PM {m['pm_deg']:.1f}, GM {m['gm_dB']}, "
                      f"f180 {m['f180_MHz']}, |T| {m['T_at_f180']}, f3 {m['f3_MHz']}, peak {m['peak_dB']:.2f} dB at {m['f_peak_MHz']} MHz")
    if "osc" in res:
        print("== SPICE: the parasitic alone, kicked")
        for o in res["osc"]:
            w = o["windows"]
            print(f"  {o['C_F_pF']:.2f} pF: p-p " + ", ".join(f"{x['pp_V']:.3f}" for x in w[::4]) +
                  f" V; settled {o['settled_pp_V']:.3f} Vpp at {o['settled_f_MHz']} MHz, steepest {o['settled_max_slope_V_per_us']:.0f} V/us")
    if "steps" in res:
        print("== SPICE: steps of the flat design")
        for s in res["steps"]:
            print(f"  {s['step_V']:g} V ({s['i_step_mA']:.3f} mA): rise {s['rise_10_90_ps']:.0f} ps, overshoot {s['overshoot_pct']:.1f} %, "
                  f"settle 1 % {s['settle_1pct_ns']:.2f} ns, steepest {s['max_slope_V_per_us']:.0f} V/us")
    if "tones" in res:
        print("== SPICE: tones of the flat design")
        for k, tt in res["tones"].items():
            print(f"  {k} MHz (Eq. (26) {tt['claim_V']:.3f} V, |Z_T| {tt['zt_ohm']:.0f} ohm): THD -60 dBc at {tt['thd_m60_V']}, -40 at {tt['thd_m40_V']}; "
                  f"HD3 -60 at {tt['hd3_m60_V']}, -40 at {tt['hd3_m40_V']} V")
            for r in tt["rows"]:
                print(f"     {r['frac']:4.2f}: {r['v1_V']:.3f} V, HD2 {r['hd2_dBc']:.1f}, HD3 {r['hd3_dBc']:.1f}, THD {r['thd_dBc']:.1f}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("action", choices=("run", "report", "figure"))
    ap.add_argument("--ngspice", default=None)
    ap.add_argument("--spice", default=str(HERE.parent / "spice"))
    ap.add_argument("--steps", nargs="+", default=["slew", "hdds", "loop", "osc", "steps", "tones"])
    ap.add_argument("--out", default=str(HERE.parent / "figures" / "fig37b_case_opa846_1k5"))
    a = ap.parse_args()
    if a.action == "run":
        main_run(a)
    elif a.action == "report":
        main_report(a)
    else:
        draw(json.loads((Path(a.spice) / "results" / RESULTS).read_text(encoding="utf-8")), a.out)


def draw(res, out_stem):
    """Figure 9 of the note from the recorded results.  The SPICE curves and points are read from the file; the
    closed forms are evaluated here with the datasheet open-loop curve (case_studies.Analytic), as in analytic()."""
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
    from make_case_figures import PANEL, panel_label
    from make_figures import COLORS, DASH, LW, configure_plot_style, export, log_axes

    configure_plot_style()
    an_rec, an = res["analytic"], cs.Analytic(PART)
    C_T, c2 = an.C_T(C_D), an_rec["c2"]
    blue, red, grey, ann = COLORS["primary"], COLORS["warm_accent"], COLORS["neutral"], COLORS["annotation"]
    # panels 2.8 in tall instead of PANEL's 3.24 in, so that the figure and its caption fit on one printed page
    fig, axs = plt.subplots(3, 2, figsize=(2 * PANEL[0], 3 * 2.8), constrained_layout=True)

    # (a) phase margin against the total feedback capacitance
    ax = axs[0, 0]
    ax.axvspan(0.05, 0.12, color=COLORS["highlight"], alpha=0.24, lw=0, zorder=0)
    ax.axhline(0.0, color=ann, lw=0.8)
    sm, lg, ml = res["loop"]["small"], res["loop"]["large"], an_rec["loop"]
    ax.plot([m["C_F_pF"] for m in sm], [m["pm_deg"] for m in sm], "o-", color=grey, lw=LW, ms=3.5,
            label="SPICE, ±5 V, 100 Ω")
    ax.plot([m["C_F_pF"] for m in lg], [m["pm_deg"] for m in lg], "s", color=red, ms=5, mfc="white", mew=1.2,
            label="SPICE, ±6 V, 1 MΩ")
    ax.plot([float(k) for k in ml], [m["pm_deg"] for m in ml.values()], color=grey, lw=LW, ls=DASH,
            label="analytical model")
    ax.axvline(CF_FLAT * 1e12, color=ann, lw=0.8, ls=":")
    ax.text(0.085, 41.5, "parasitic\nalone", ha="center", va="top")
    ax.text(0.72, 8.0, "0.70-pF design", ha="left", va="center")
    ax.set_xlim(0, 1.15)
    ax.set_ylim(-20, 45)
    ax.set_xlabel(r"Total feedback capacitance $C_F$ (pF)")
    ax.set_ylabel("Phase margin (°)")
    ax.legend(loc="lower right")
    panel_label(ax, "(a)", x=0.94)

    # (b) the parasitic alone, kicked by a 10-uA step: the last 12 ns of the 400-ns run, and Eq. (36b)
    ax = axs[0, 1]
    o08 = an_rec["osc"]["0.08"]
    lo, hi = o08["V_osc_V"], o08["V_osc_sine_V"]
    for s in (1, -1):
        ax.axhspan(min(s * lo, s * hi), max(s * lo, s * hi), color=COLORS["highlight"], alpha=0.24, lw=0, zorder=0)
    for o, col in zip(res["osc"], (blue, grey, red)):
        t, v = np.array(o["curve"]["t_ns"]), np.array(o["curve"]["v"])
        t0 = t[-1] - 12.0
        sel = t >= t0
        ax.plot(t[sel] - t0, v[sel], color=col, lw=LW,
                label=f"{o['C_F_pF']:.2f} pF: {o['settled_pp_V']:.2f} Vpp, {o['settled_f_MHz']:.0f} MHz")
    ax.set_xlim(0, 12)
    ax.set_ylim(-1.3, 2.15)
    ax.set_xlabel("Time from 388 ns (ns)")
    ax.set_ylabel("Output voltage (V)")
    h, l = ax.get_legend_handles_labels()
    h.append(Patch(color=COLORS["highlight"], alpha=0.24, lw=0))
    l.append(f"Eq. (36b), 625–742 V/µs: ±{lo:.2f} to ±{hi:.2f} V")
    ax.legend(h, l, loc="upper left", fontsize=7.2)
    panel_label(ax, "(b)", x=0.94)

    # (c) photocurrent steps of the 0.70-pF design, normalized to their final value
    ax = axs[1, 0]
    step_cols = (blue, COLORS["teal_accent"], COLORS["cool_accent"], COLORS["purple_accent"], red)
    for s, col in zip(res["steps"], step_cols):
        t, vn = np.array(s["curve"]["t_ns"]) - 2.0, np.array(s["curve"]["v_norm"])
        vn = vn - np.mean(vn[(t > -1.5) & (t < -0.1)])      # (v - v0)/step: v0 is the output before the step
        ax.plot(t, vn, color=col, lw=LW,
                label=f"{s['step_V']:g} V: {s['rise_10_90_ps'] / 1e3:.2f} ns, {s['overshoot_pct']:.1f} %")
    ax.axhline(1.0, color=ann, lw=0.8, ls=":")
    st = an_rec["step"]
    ax.text(11.8, 0.13, f"Eq. (36d): slewing\nabove {st['V_step_SR_V']:.2f} V at 625 V/µs", ha="right", va="center")
    ax.set_xlim(-0.5, 12)
    ax.set_ylim(-0.05, 1.3)
    ax.set_xlabel("Time from the step (ns)")
    ax.set_ylabel("Output / final value")
    ax.legend(loc="upper right", bbox_to_anchor=(1.0, 0.73), fontsize=7.2, title="step: 10–90 %, overshoot",
              title_fontsize=7.2)
    panel_label(ax, "(c)", x=0.94)

    # (d) largest amplitude against the tone frequency: Eq. (26), the closed forms and the macromodel's THD
    ax = axs[1, 1]
    fq = np.logspace(7, math.log10(3e8), 400)
    v_sr = SR_DS / (2 * math.pi * fq)
    vpk = np.minimum(V_SW, v_sr)
    he = {}
    for k in (2, 3):
        A = an.ol.A(k * fq)
        NG = tm.tia_tf(k * fq, an.ol, R_F, C_T, CF_FLAT)[1]
        he[k] = np.abs(A / (1 + A / NG))
    a2 = c2 * V_OV * he[2] / v_sr ** 2            # HD2 = a2 V, Eq. (36f)
    b3 = V_OV * he[3] / (12 * v_sr ** 3)           # HD3 = b3 V^2, Eq. (36e)
    ax.plot(fq, vpk, color=grey, lw=LW, label="Eq. (26)")
    for lvl, col in ((-60, blue), (-40, red)):
        D = 10 ** (lvl / 20)
        v_sum = np.sqrt((-a2 ** 2 + np.sqrt(a2 ** 4 + 4 * b3 ** 2 * D ** 2)) / (2 * b3 ** 2))
        v_hd3 = v_sr * np.sqrt(12 * D * v_sr / (V_OV * he[3]))                    # Eq. (36g)
        ax.plot(fq, np.where(v_sum < vpk, v_sum, np.nan), color=col, lw=LW, ls=DASH,
                label=f"${lvl}$ dBc, HD2 + HD3, Eqs. (36e)–(36g)")
        ax.plot(fq, np.where(v_hd3 < vpk, v_hd3, np.nan), color=col, lw=LW, ls=":",
                label=f"${lvl}$ dBc, HD3 alone, Eq. (36g)")
    tn = res["tones"]
    fr = np.array([float(k) * 1e6 for k in tn])
    v40 = np.array([np.nan if x["thd_m40_V"] is None else x["thd_m40_V"] for x in tn.values()])
    v60 = np.array([np.nan if x["thd_m60_V"] is None else x["thd_m60_V"] for x in tn.values()])
    ax.plot(fr, v60, "s", color=blue, ms=5, mfc="white", mew=1.2, label="$-60$ dBc, SPICE THD")
    ax.plot(fr, v40, "o", color=red, ms=5, label="$-40$ dBc, SPICE THD")
    log_axes(ax)
    ax.set_xlim(1e7, 3e8)
    ax.set_ylim(0.01, 10)
    ax.set_xlabel("Tone frequency (Hz)")
    ax.set_ylabel("Output amplitude (V peak)")
    ax.legend(loc="lower left", fontsize=7.2)
    panel_label(ax, "(d)", x=0.94)

    # (e) the datasheet's distortion test (G = +10, 2 Vpp, 200 ohm): datasheet, macromodel, Eqs. (36e) and (36f)
    ax = axs[2, 0]
    hd = res["hd_ds"]
    f1 = np.array([r["f_MHz"] * 1e6 for r in hd])
    ax.plot(f1, [r["ds_hd2_dBc"] for r in hd], "o", color=blue, ms=5, label="HD2, datasheet")
    f3 = [r["f_MHz"] * 1e6 for r in hd if r["ds_hd3_dBc"] is not None]
    ax.plot(f3, [r["ds_hd3_dBc"] for r in hd if r["ds_hd3_dBc"] is not None], "s", color=red, ms=5,
            label="HD3, datasheet")
    ax.plot(f1, [r["hd2_dBc"] for r in hd], color=blue, lw=LW, label="HD2, SPICE")
    ax.plot(f1, [r["hd3_dBc"] for r in hd], color=red, lw=LW, label="HD3, SPICE")
    ff = np.logspace(6, math.log10(2.0e7), 200)
    vs = SR_DS / (2 * math.pi * ff)
    x = 1.0 / vs                                    # 1 V peak
    A2, A3 = an.ol.A(2 * ff), an.ol.A(3 * ff)
    he2, he3 = np.abs(A2 / (1 + A2 / 10.0)), np.abs(A3 / (1 + A3 / 10.0))
    ax.plot(ff, 20 * np.log10(c2 * V_OV * he2 / vs * x), color=blue, lw=LW, ls=DASH, label="HD2, Eq. (36f)")
    ax.plot(ff, 20 * np.log10(V_OV * he3 / (12 * vs) * x ** 2), color=red, lw=LW, ls=DASH, label="HD3, Eq. (36e)")
    log_axes(ax, x=True, y=False)
    ax.set_xlim(0.9e6, 2.2e7)
    ax.set_ylim(-155, -40)
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Harmonic (dBc)")
    ax.legend(loc="lower right", fontsize=7.2, ncol=2)
    panel_label(ax, "(e)", x=0.94)

    # (f) the same test at 5 MHz against the load
    ax = axs[2, 1]
    hl = [r for r in res["hd_load"] if r["R_L_ohm"] < 1e5]
    R = [r["R_L_ohm"] for r in hl]
    ax.plot(R, [r["ds_hd2_dBc"] for r in hl], "o", color=blue, ms=5, label="HD2, datasheet")
    ax.plot([r["R_L_ohm"] for r in hl if r["ds_hd3_dBc"] is not None],
            [r["ds_hd3_dBc"] for r in hl if r["ds_hd3_dBc"] is not None], "s", color=red, ms=5, label="HD3, datasheet")
    ax.plot(R, [r["hd2_dBc"] for r in hl], color=blue, lw=LW, label="HD2, SPICE")
    ax.plot(R, [r["hd3_dBc"] for r in hl], color=red, lw=LW, label="HD3, SPICE")
    q = [r for r in res["hd_load"] if r["R_L_ohm"] >= 1e5][0]
    ax.text(0.03, 0.05, f"quiescent supply current: SPICE {q['supply_mA']:.2f} mA, datasheet {QUIESCENT_DS_mA:g} mA",
            transform=ax.transAxes, ha="left", va="bottom", fontsize=7.2)
    ax.set_xlim(80, 520)
    ax.set_ylim(-125, -42)
    ax.set_xlabel(r"Load resistance $R_L$ ($\Omega$)")
    ax.set_ylabel("Harmonic at 5 MHz (dBc)")
    ax.legend(loc="upper right", bbox_to_anchor=(1.0, 0.93), fontsize=7.2, ncol=2)
    panel_label(ax, "(f)", x=0.94)
    export(fig, Path(out_stem))
    print(f"Figure 9 written to {out_stem}.png and .pdf")


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    main()
