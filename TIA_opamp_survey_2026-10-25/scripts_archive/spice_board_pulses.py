"""SPICE check of the pulse model of Section 4.11.8 (Section 4.11.9, Tables 4.10 and 4.11, Figures 14 and 15): the vendor's OPA846
macromodel in ngspice on the measured board's node, driven by the same short photocurrent pulses as the time-domain
model of tia_pulse_response.py, and in the datasheet's slew-rate test; the time-domain model beside it.

Usage:
    python spice_board_pulses.py run    [--ngspice LIB] [--spice SPICE_DIR] [--steps fit slew pulses probe]
    python spice_board_pulses.py report [--spice SPICE_DIR] [--figure [OUT_STEM]]

'run' simulates and writes <spice>/results/board_pulses.json; the decks and ngspice's raw outputs go to
<spice>/runs/board_pulses/, which stays local.  The fit takes about a minute, the other steps about half a minute.
'report' runs the time-domain model at the same charges (about a minute), prints every number of Section 4.11.9 and
the rows of Tables 4.10 and 4.11, with --figure draws Figure 14 (../figures/fig37g_opa846_1k5_spice_pulses.png and .pdf) and with --summary
Figure 15 (../figures/fig37h_opa846_1k5_spice_summary.png and .pdf).

The circuit is that of spice_tia_checks.tia_body: the macromodel on +/-5 V with its non-inverting input grounded,
R_F = 1.5 kOhm in parallel with C_F from the output to the summing node, C_ext from the summing node to ground, a
100-ohm load (the load of the open-loop run that gives A_-, Chapter 5), and the photocurrent source Iph into the
summing node.

Step 'fit': the board's node in the full macromodel.  The fits of Table 4.4 use only the macromodel's open-loop gain
A_- and its 3.07 pF of input capacitance in the note's equations; the full macromodel also has its input resistance,
its input transistors and its output stage inside the loop.  Its external node capacitance C_ext and feedback
capacitance C_F are therefore fitted to the measured gain again, in the same way (Eqs. (36j) and (36k), with the
50-ohm, 14-pF chain of Eq. (36i)), but with the transimpedance from SPICE AC runs: a coarse grid and a finer one
around its best point.

Step 'slew': Test 2 of Section 4.11.8 in SPICE, the datasheet's slew-rate test circuit (OPA846 p. 3: a non-inverting
gain of +10 with 453 and 50 ohm, 100-ohm load, +/-5 V), a 2-V output step from 20-ps input edges, as in
case_opa846_1k5.slew_test; its output waveform is kept for Figure 14a.

Step 'pulses': a reference pulse of 1 fC gives SPICE's own linear peak per charge, h_pk, on each board (its node jump,
about 0.2 mV, is 0.3 % of the input stage's overdrive voltage, so the stage is linear).  Then the 14 pulse sizes of
the note (tia_pulse_response.NOTE_VLIN, as the linear peak they would reach: Q = V_lin/|h_pk|) on the board and on the
second board (C_F + 0.55 pF).  The photocurrent is a trapezoid PULSE(0 I 2n 10p 10p 20p), rise and fall of 10 ps and
20 ps flat, so its charge is I x 30 ps; at the loop's speed this is a delta (Section 4.11.8: a 50-ps Gaussian gives
the same peaks as a delta within 0.01 dB).  Time is counted from the pulse's centre, and the output and the summing
node are read relative to their values before the pulse (the macromodel's DC offset is removed).  The metrics are
those of tia_pulse_response.response_metrics, on the full 1-ps waveform; the waveforms of the pulse sizes that
Figure 13 draws are kept at 20-ps steps up to 30 ns, and the probe's at 10-ps steps up to 8 ns.

Step 'probe': the macromodel's own input stage during the pulses of 1, 3 and 10 V of linear peak on the board.  The
macromodel (OPA846.LIB) is a bipolar differential pair, Q_Q1 (base at the non-inverting pin) and Q_Q2 (base at node 2,
behind L_L1 = 2.35 nH from the inverting pin), with 5-ohm emitter resistors to the tail node 15, a 1.475-mA tail
current I_I1 and 200-ohm collector loads R_R10, R_R11 (nodes 11, 12) to node 10 = V+ - 1.4 V.  A transconductance
G_G3 = 30.51 mS x V(12, 11) drives the integrating node 17 (C_C2 = 7.95 pF in parallel with R_R14 = 503 kOhm), which a
unity-gain copy (node 18) and an output stage carry to the output.  The pair's current difference is therefore read
from the voltage across the collector loads, i_17 = 30.51 mS x V(12, 11), and its static maximum, with the whole tail
current in one collector, is 30.51 mS x 200 ohm x alpha x 1.475 mA = 8.94 mA (alpha = BF/(BF + 1), BF = 157), which
slews node 17 at 8.94 mA/7.95 pF = 1125 V/us.  The probe records v_n, node 2, the tail node 15, i_17, nodes 17 and 18
and the output.

The comparison ('report'): tia_pulse_response's time-domain model with the macromodel's A_- (its rational fit), on
its own fit of the measured gain (the note's 'macromodel A_-' case: C_T 7.43 pF, C_F 0.318 pF), at SPICE's charges;
its internal slew rate is calibrated in the datasheet's test (tia_pulse_response.calibrate_sr), and 625 V/us taken as
the steepest slope is run as well; the swing is the datasheet's +/-3.3 V into 100 ohm (OPA846 p. 3).  Both
descriptions are fitted to the same measured gain, so their linear responses should agree; what can differ is the
large-signal mechanism: the model's tanh stage with a linear node capacitance against the macromodel's transistors.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

import tia_pulse_response as tp

HERE = Path(__file__).resolve().parent
PART = "OPA846"
R_F = 1500.0
VS, RL = 5.0, 100.0                      # supply and load, as in the macromodel's open-loop run (Chapter 5)
PULSE_EDGE, PULSE_FLAT = 10e-12, 20e-12  # s: the trapezoid's charge is I (PULSE_FLAT + PULSE_EDGE)
T_PULSE = 2e-9                           # s, the pulse's start in the transient run
T_CENTRE = T_PULSE + PULSE_EDGE + PULSE_FLAT / 2      # its centre, taken as the arrival time t = 0
T_RESPONSE = 80e-9                       # s simulated after the pulse (the largest pulses settle to 0.1 % in ~60 ns)
Q_REF = 1e-15                            # C, the linear reference pulse
ADD_V2 = 0.55e-12                        # F, the second board's added feedback capacitance (Section 4.11.7)
SWING_100 = 3.3                          # V, +/-5 V into 100 ohm (OPA846 p. 3)
PROBE_VLIN = (1.0, 3.0, 10.0)            # V of linear peak: the pulses whose input stage the probe records
KEEP_DT, KEEP_T = 20e-12, 30e-9          # the kept waveforms: 20-ps steps up to 30 ns after the pulse
DESIGNS = (("board", 0.0), ("second", ADD_V2))

# The macromodel's input stage, read off OPA846.LIB (see the module docstring)
MAC_I_TAIL = 1.475e-3                    # A, I_I1
MAC_R_LOAD = 200.0                       # ohm, R_R10 and R_R11
MAC_G3 = 30.51e-3                        # S, G_G3 (PSpice 'M' is milli)
MAC_C17 = 7.95e-12                       # F, C_C2
MAC_ALPHA = 157.0 / 158.0                # BF/(BF + 1) of the NPN8 model
MAC_R_E = 5.0                            # ohm, R_R12 and R_R13, the emitter resistors
MAC_C1 = 0.35e-12                        # F, C_C1 from the inverting pin to ground, outside L_L1
MAC_L1 = 2.35e-9                         # H, L_L1 from the inverting pin to Q_Q2's base (node 2)
V_T = 0.025693                           # V, kT/q at 25 degC (the decks' .temp 25)
I17_MAX = MAC_G3 * MAC_R_LOAD * MAC_ALPHA * MAC_I_TAIL     # A, 8.94 mA: the whole tail current in one collector
SR17 = I17_MAX / MAC_C17                 # V/s, 1125 V/us: node 17's slope at that current
# the pair's own overdrive voltage: the slope of its current difference at v_d = 0 is 1/(r_e + R_E), with
# r_e = V_T/(I_T/2) for each transistor at half the tail current, so V_ov = I_T/g_m = I_T (r_e + R_E)
V_OV_MAC = MAC_I_TAIL * (V_T / (MAC_I_TAIL / 2) + MAC_R_E)


def c_je_q1(v_be):
    """Q_Q1's base-emitter junction capacitance (F) at the bias v_be, as SPICE computes it from the NPN8 model of
    OPA846.LIB: CJE = 0.112 pF per unit area times the area 10, VJE = 0.7591 V, MJE = 0.5406, and above FC VJE
    (FC = 0.8273) the linear extension that SPICE uses for forward bias."""
    c0, vj, m, fc = 10 * 0.112e-12, 0.7591, 0.5406, 0.8273
    v = np.asarray(v_be, dtype=float)
    reverse = c0 / (1 - np.minimum(v, fc * vj) / vj) ** m
    forward = c0 / (1 - fc) ** (1 + m) * (1 - fc * (1 + m) + m * v / vj)
    return np.where(v < fc * vj, reverse, forward)


def deck_folder(spice, name):
    """Two levels below runs/, so that spice_tia_checks.header()'s '.include ../../_models/...' resolves."""
    return spice / "runs" / "board_pulses" / name.replace(".", "p")


def compact_wave(t, ys, t_max=KEEP_T, dt=KEEP_DT, digits=5):
    """Waveforms resampled at dt from t = -0.1 ns to t_max (relative to the pulse), rounded to `digits` significant
    digits, for the results file."""
    tk = np.arange(-0.1e-9, t_max + dt / 2, dt)
    out = {"t": [float(f"{x:.6g}") for x in tk]}
    for k, y in ys.items():
        out[k] = [float(f"{v:.{digits}g}") for v in np.interp(tk, t, y)]
    return out


# ---------------------------------------------------------------------------------------------------------------
# step 1: the board's node in the full macromodel
# ---------------------------------------------------------------------------------------------------------------
def ac_zt(ng, spice, c_ext, c_f):
    """|Z_T| from an AC run of the full macromodel: a 1-A AC photocurrent into the summing node, v(oa) read."""
    from spice_tia_checks import header, read_wrdata, run, tia_body, write_deck
    folder = deck_folder(spice, f"ac_X{c_ext * 1e12:.3f}p_F{c_f * 1e12:.4f}p")
    deck = header(PART, f"OPA846 board fit, C_ext {c_ext * 1e12:g} pF, C_F {c_f * 1e12:g} pF", VS) + tia_body(
        PART, R_F, c_ext, c_f, RL, iph="Iph 0 inm DC 0 AC 1") + (
        ".control\nset wr_singlescale\nset wr_vecnames\nac dec 200 1M 1G\n"
        "wrdata zt.txt real(v(oa)) imag(v(oa))\n.endc\n.end\n")
    log, err = run(ng, write_deck(folder, deck))
    d = read_wrdata(folder / "zt.txt")
    return d[:, 0], np.abs(d[:, 1] + 1j * d[:, 2]), err[:1]


def residual_from(f_sp, z_sp, f, g, h):
    """Eqs. (36j)-(36k) with the SPICE transimpedance interpolated (in log f) onto the measured bins: the model's
    shape M_k = |Z_T| |H_chain|, the scale K that fits it best, and the rms relative residual epsilon."""
    z = np.interp(np.log10(f), np.log10(f_sp), z_sp) * h
    u = z / g
    k = np.sum(u) / np.sum(u * u)                                  # least squares of (1 - K u_k), Eq. (36k)
    return float(np.sqrt(np.mean((1.0 - k * u) ** 2))), float(k)


def fit_node(ng, spice):
    """Step 1: C_ext and C_F of the full macromodel fitted to the measured gain (coarse grid, then a finer one)."""
    import compare_opa846_1k5_board as cb
    b = cb.read_bins(str(HERE.parent / "data" / "measurements" / "opa846_1k5_board_per_MHz.csv"))
    use = (~b["bad"]) & np.isfinite(b["G"]) & (b["f"] >= 10e6)      # the bins of Section 4.11.4
    f, g = b["f"][use], b["G"][use]
    h = cb.chain(f, "rc")                                            # the 50-ohm, 14-pF chain, Eq. (36i)
    tried = []

    def evaluate(cx, cf):
        fz, zt, err = ac_zt(ng, spice, cx, cf)
        eps, k = residual_from(fz, zt, f, g, h)
        pk = 20 * math.log10(float(np.max(zt)) / zt[0])
        tried.append(dict(c_ext=cx, c_f=cf, eps=eps, k=k, peak_dB=pk, f_peak=float(fz[int(np.argmax(zt))]), errors=err))
        print(f"  C_ext {cx * 1e12:.3f} pF, C_F {cf * 1e12:.4f} pF: eps {100 * eps:.2f} %, K {k:.3f}, TIA peak {pk:+.2f} dB")
        return eps

    # coarse grid around the partial description's fit (C_ext 4.36 pF, C_F 0.318 pF)
    for cx in np.arange(3.6e-12, 5.41e-12, 0.3e-12):
        for cf in np.arange(0.16e-12, 0.401e-12, 0.04e-12):
            evaluate(cx, cf)
    best = min(tried, key=lambda r: r["eps"])
    # finer grid around the coarse best
    for cx in np.arange(best["c_ext"] - 0.2e-12, best["c_ext"] + 0.201e-12, 0.1e-12):
        for cf in np.arange(best["c_f"] - 0.03e-12, best["c_f"] + 0.0301e-12, 0.01e-12):
            if not any(abs(r["c_ext"] - cx) < 1e-16 and abs(r["c_f"] - cf) < 1e-16 for r in tried):
                evaluate(cx, cf)
    best = min(tried, key=lambda r: r["eps"])
    print(f"best: C_ext {best['c_ext'] * 1e12:.3f} pF, C_F {best['c_f'] * 1e12:.4f} pF, eps {100 * best['eps']:.2f} %, K {best['k']:.3f}")
    return dict(best=best, tried=tried)


# ---------------------------------------------------------------------------------------------------------------
# step 2: the datasheet's slew-rate test
# ---------------------------------------------------------------------------------------------------------------
def slew_run(ng, spice, step=2.0):
    """Test 2 in SPICE: G = +10 (453 and 50 ohm), 100-ohm load, +/-5 V, an output step of `step` volts centred on 0 V
    from 20-ps input edges at 5 ns.  Returns the 10-90 % and 20-80 % average slopes, the steepest slope and the
    waveform (time from the input edge)."""
    from spice_tia_checks import header, read_wrdata, run, write_deck
    vin = step / 20.0                                         # +/- step/20 at the input, 10.06 x 2 vin at the output
    folder = deck_folder(spice, f"slew_{step:g}V")
    deck = header(PART, f"OPA846 slew test, G = +10, {step:g}-V output step", VS) + (
        "XU1 inp inm vcc vee oa OPA846\nRF oa inm 453\nRG inm 0 50\nRL oa 0 100\n"
        f"VIN inp 0 PULSE({-vin:g} {vin:g} 5n 20p 20p 25n 50n)\n"
        ".control\nset wr_singlescale\nset wr_vecnames\ntran 1p 30n 0 1p\nlinearize v(oa) v(xu1.11) v(xu1.12)\n"
        "wrdata slew.txt v(oa) v(xu1.11) v(xu1.12)\n.endc\n.end\n")
    log, err = run(ng, write_deck(folder, deck))
    d = read_wrdata(folder / "slew.txt")
    t, v = d[:, 0], d[:, 1]
    i17 = MAC_G3 * (d[:, 3] - d[:, 2])                         # the input stage's current into the integrating node
    v0 = float(np.mean(v[(t > 3e-9) & (t < 4.9e-9)]))          # before the edge
    v1 = float(np.mean(v[(t > 25e-9) & (t < 29.5e-9)]))        # settled
    dv = v1 - v0
    after = t > 5e-9

    def cross(frac):
        # the first time after the edge at which the output has covered `frac` of the step, interpolated
        k = int(np.where(after & (v - v0 >= frac * dv))[0][0])
        return float(t[k - 1] + (v0 + frac * dv - v[k - 1]) * (t[k] - t[k - 1]) / (v[k] - v[k - 1]))

    slope = np.gradient(v, t)
    wave = compact_wave(t - 5e-9 - 10e-12, {"vo": v - (v0 + v1) / 2}, t_max=15e-9)
    k = int(np.argmax(np.abs(i17)))
    return dict(step=dv, avg_10_90=0.8 * dv / (cross(0.9) - cross(0.1)), avg_20_80=0.6 * dv / (cross(0.8) - cross(0.2)),
                steepest=float(np.max(slope[after])), i17_max_ratio=float(abs(i17[k]) / I17_MAX),
                t_i17_max=float(t[k] - 5e-9 - 10e-12), wave=wave, errors=err[:1])


# ---------------------------------------------------------------------------------------------------------------
# steps 3 and 4: pulses on the board's node
# ---------------------------------------------------------------------------------------------------------------
def pulse_deck(title, c_ext, c_f, q, nodes, t_stop):
    """The board's circuit with a trapezoid photocurrent pulse of charge q starting at T_PULSE; ngspice writes the
    listed node voltages on a uniform 1-ps grid (linearize) to pulse.txt."""
    from spice_tia_checks import header, tia_body
    i_peak = q / (PULSE_FLAT + PULSE_EDGE)        # trapezoid area = I (flat + edge)
    vecs = " ".join(f"v({n})" for n in nodes)
    return header(PART, title, VS) + tia_body(
        PART, R_F, c_ext, c_f, RL,
        iph=f"Iph 0 inm PULSE(0 {i_peak:.6e} {T_PULSE:g} {PULSE_EDGE:g} {PULSE_EDGE:g} {PULSE_FLAT:g} 1)") + (
        f".control\nset wr_singlescale\nset wr_vecnames\ntran 1p {t_stop:g} 0 2p\nlinearize {vecs}\n"
        f"wrdata pulse.txt {vecs}\n.endc\n.end\n")


def pulse_run(ng, spice, c_ext, c_f, q, tag):
    """One transient run: returns t (from the pulse's centre), v_o and v_n relative to their values before the pulse."""
    from spice_tia_checks import read_wrdata, run, write_deck
    folder = deck_folder(spice, f"pulse_{tag}_Q{q * 1e12:.5f}p")
    deck = pulse_deck(f"OPA846 board pulse, {tag}, Q {q * 1e12:g} pC", c_ext, c_f, q, ("oa", "inm"), T_PULSE + T_RESPONSE)
    log, err = run(ng, write_deck(folder, deck))
    d = read_wrdata(folder / "pulse.txt")
    t, vo, vn = d[:, 0], d[:, 1], d[:, 2]
    pre = (t > 1.0e-9) & (t < 1.95e-9)                 # before the pulse: the DC operating point
    keep = t >= T_PULSE - 0.2e-9
    return t[keep] - T_CENTRE, vo[keep] - np.mean(vo[pre]), vn[keep] - np.mean(vn[pre]), err[:1]


def pulses_step(ng, spice, c_ext, c_f):
    """Step 3: the linear reference and the 14 pulse sizes on both boards; metrics on the full waveforms."""
    out = {}
    for tag, add in DESIGNS:
        t, vo, vn, err = pulse_run(ng, spice, c_ext, c_f + add, Q_REF, tag)
        h = tp.response_metrics(t, vo / Q_REF * 1e-12, 1e-12)        # the linear response per pC
        h_pk = abs(h["v_peak"]) / 1e-12                                # V per coulomb
        ref = dict(q=Q_REF, h_pk=h_pk, metrics=h, wave=compact_wave(t, {"vo_per_pC": vo / Q_REF * 1e-12}), errors=err)
        print(f"  {tag}: linear peak {h['v_peak']:+.4f} V/pC at {h['t_peak'] * 1e9:.2f} ns, {h['f_ring'] / 1e6:.1f} MHz, "
              f"tau {h['tau_decay'] * 1e9:.2f} ns, 1 % at {h['t_settle_1pct'] * 1e9:.1f} ns")
        runs = []
        for v_lin in tp.NOTE_VLIN:
            q = v_lin / h_pk
            t, vo, vn, err = pulse_run(ng, spice, c_ext, c_f + add, q, tag)
            m = tp.response_metrics(t, vo, q)
            r = dict(q=q, v_lin_peak=-v_lin, tia=m, compression_dB=20 * math.log10(abs(m["v_peak"]) / v_lin),
                     vn_max=float(np.max(np.abs(vn))), errors=err)
            if any(abs(v_lin - s) < 1e-6 * s for s in tp.SHOWN_VLIN):
                r["wave"] = compact_wave(t, {"vo": vo, "vn": vn})
            print(f"    Q {q * 1e12:7.4f} pC ({v_lin:g} V linear): peak {m['v_peak']:+.3f} V at {m['t_peak'] * 1e9:.2f} ns "
                  f"({r['compression_dB']:+.2f} dB), max v_n {r['vn_max'] * 1e3:.1f} mV, 1 % at {m['t_settle_1pct'] * 1e9:.1f} ns, "
                  f"area/Q {m['area_over_q']:.0f} ohm{', ' + err[0] if err else ''}")
            runs.append(r)
        out[tag] = dict(reference=ref, runs=runs)
    return out


PROBE_NODES = ("oa", "inm", "xu1.2", "xu1.15", "xu1.10", "xu1.11", "xu1.12", "xu1.17", "xu1.18")


def probe_step(ng, spice, c_ext, c_f, h_pk):
    """Step 4: the macromodel's internal nodes during three pulses on the board (see the module docstring)."""
    from spice_tia_checks import read_wrdata, run, write_deck
    out = []
    for v_lin in PROBE_VLIN:
        q = v_lin / h_pk
        folder = deck_folder(spice, f"probe_Q{q * 1e12:.4f}p")
        deck = pulse_deck(f"OPA846 board, input-stage probe, Q {q * 1e12:g} pC", c_ext, c_f, q, PROBE_NODES, T_PULSE + 12e-9)
        log, err = run(ng, write_deck(folder, deck))
        d = read_wrdata(folder / "pulse.txt")
        t = d[:, 0] - T_CENTRE
        v = {n: d[:, 1 + k] for k, n in enumerate(PROBE_NODES)}
        pre = (t > -1.0e-9) & (t < -0.05e-9)
        i17 = MAC_G3 * (v["xu1.12"] - v["xu1.11"])           # into node 17; negative pulls the output down
        rel = {n: v[n] - np.mean(v[n][pre]) for n in ("oa", "inm", "xu1.2", "xu1.17", "xu1.18")}
        out.append(dict(v_lin=v_lin, q=q, i17_quiescent=float(np.mean(i17[pre])), tail_quiescent=float(np.mean(v["xu1.15"][pre])),
                        errors=err[:1],
                        wave=compact_wave(t, {"vn": rel["inm"], "v_base": rel["xu1.2"], "v_tail": v["xu1.15"], "i17": i17,
                                              "v17": rel["xu1.17"], "v18": rel["xu1.18"], "vo": rel["oa"]},
                                          t_max=8e-9, dt=10e-12)))
        print(f"  probe {v_lin:g} V linear ({q * 1e12:.3f} pC): largest |i_17| {np.max(np.abs(i17)) * 1e3:.1f} mA "
              f"({np.max(np.abs(i17)) / I17_MAX:.2f} of its static maximum), tail node from {out[-1]['tail_quiescent']:+.3f} "
              f"to {np.max(v['xu1.15']):+.3f} V")
    return out


DOUBLET_Q = (0.3e-12, 1e-12, 3e-12, 7.5e-12)    # C per photodiode, as in tia_pulse_response's doublet variant
DOUBLET_SKEW = 50e-12                           # s: the second photodiode's pulse arrives this much later


def doublet_step(ng, spice, c_ext, c_f):
    """Step 5: a balanced pair whose two pulses arrive 50 ps apart, on the board: +Q into the summing node (Iph), then
    -Q drawn from it (Iph2, the second photodiode), each the trapezoid of step 3.  Returns the largest voltage at the
    summing node (across the inputs) and at the input transistor's base (node 2), and the output's largest excursion."""
    from spice_tia_checks import header, read_wrdata, run, tia_body, write_deck
    out = []
    for q in DOUBLET_Q:
        i_peak = q / (PULSE_FLAT + PULSE_EDGE)
        trap = f"{PULSE_EDGE:g} {PULSE_EDGE:g} {PULSE_FLAT:g} 1)"
        src = (f"Iph 0 inm PULSE(0 {i_peak:.6e} {T_PULSE:g} {trap}\n"
               f"Iph2 inm 0 PULSE(0 {i_peak:.6e} {T_PULSE + DOUBLET_SKEW:g} {trap}")
        folder = deck_folder(spice, f"doublet_Q{q * 1e12:.2f}p")
        deck = header(PART, f"OPA846 board, doublet, Q {q * 1e12:g} pC", VS) + tia_body(PART, R_F, c_ext, c_f, RL, iph=src) + (
            ".control\nset wr_singlescale\nset wr_vecnames\ntran 1p 22n 0 2p\nlinearize v(oa) v(inm) v(xu1.2)\n"
            "wrdata pulse.txt v(oa) v(inm) v(xu1.2)\n.endc\n.end\n")
        log, err = run(ng, write_deck(folder, deck))
        d = read_wrdata(folder / "pulse.txt")
        t, vo, vn, vb = d[:, 0] - T_CENTRE, d[:, 1], d[:, 2], d[:, 3]
        pre = (t > -1.0e-9) & (t < -0.05e-9)
        vo, vn, vb = vo - np.mean(vo[pre]), vn - np.mean(vn[pre]), vb - np.mean(vb[pre])
        k = int(np.argmax(np.abs(vo)))
        out.append(dict(q=q, vn_max=float(np.max(np.abs(vn))), vbase_max=float(np.max(np.abs(vb))), vo_peak=float(vo[k]),
                        t_peak=float(t[k]), errors=err[:1]))
        print(f"  doublet {q * 1e12:g} pC: largest v_n {out[-1]['vn_max'] * 1e3:.0f} mV, base {out[-1]['vbase_max'] * 1e3:.0f} mV, "
              f"output {vo[k] * 1e3:+.0f} mV at {t[k] * 1e9:.2f} ns")
    return out


def main_run(a):
    from ngspice_shared import NgSpice
    from spice_tia_checks import prepared_model
    spice = Path(a.spice)
    path = spice / "results" / "board_pulses.json"
    res = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    ng = NgSpice(a.ngspice)
    prepared_model(PART, spice)
    if "fit" in a.steps:
        print("Step 1: the full macromodel's node fitted to the measured gain")
        res["fit"] = fit_node(ng, spice)
    best = res["fit"]["best"]
    if "slew" in a.steps:
        print("Step 2: the datasheet's slew-rate test")
        res["slew"] = slew_run(ng, spice)
        s = res["slew"]
        print(f"  2-V step: {s['avg_10_90'] / 1e6:.0f} V/us from 10 to 90 %, {s['avg_20_80'] / 1e6:.0f} V/us from 20 to 80 %, "
              f"steepest {s['steepest'] / 1e6:.0f} V/us; the input stage's current reaches {s['i17_max_ratio']:.2f} of its "
              f"static maximum, {s['t_i17_max'] * 1e9:.2f} ns after the edge")
    if "pulses" in a.steps:
        print("Step 3: pulses")
        res["pulses"] = dict(c_ext=best["c_ext"], c_f=best["c_f"], add_v2=ADD_V2, rl=RL, vs=VS,
                             designs=pulses_step(ng, spice, best["c_ext"], best["c_f"]))
    if "probe" in a.steps:
        print("Step 4: the macromodel's input stage")
        h_pk = res["pulses"]["designs"]["board"]["reference"]["h_pk"]
        res["probe"] = probe_step(ng, spice, best["c_ext"], best["c_f"], h_pk)
    if "doublet" in a.steps:
        print("Step 5: a balanced pair's two pulses 50 ps apart")
        res["doublet"] = doublet_step(ng, spice, best["c_ext"], best["c_f"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(res), encoding="utf-8")
    print(f"written {path} ({path.stat().st_size / 1e6:.2f} MB)")


# ---------------------------------------------------------------------------------------------------------------
# the comparison with the time-domain model
# ---------------------------------------------------------------------------------------------------------------
def model_description():
    """The note's 'macromodel A_-' description: its rational open loop and its own fit of the measured gain, read
    from the results of tia_pulse_response.py --note."""
    d = json.loads((HERE.parent / "data" / "results" / "tia_pulse_response_opa846_1k5.json").read_text(encoding="utf-8"))
    fit = d["fits"]["macromodel A_-"]
    fr = fit["rational"]
    rol = tp.RationalOpenLoop(fr["a0"], fr["f_p1_Hz"], fr["zeros_Hz"], fr["poles_Hz"], fr["tau_s"], fr["n_delay"], fr["note"])
    return rol, fit["ct"], fit["cf"]


def model_runs(rol, ct, cf, sr, charges):
    """The time-domain model at the given charges (delta pulses): metrics as for SPICE, compression against the
    model's own linear peak, and the waveforms (10-ps steps)."""
    tl, hl, _ = tp.linear_impulse(rol, R_F, ct, cf)
    lin = tp.response_metrics(tl, hl * 1e-12, 1e-12, t_max=200e-9)
    h_pk = abs(lin["v_peak"]) / 1e-12
    t, vo, vn, x1, v_ov = tp.simulate(rol, R_F, ct, cf, sr, SWING_100, charges, window=T_RESPONSE, dt=2e-12)
    runs = []
    for k, q in enumerate(charges):
        m = tp.response_metrics(t, vo[k], q)
        runs.append(dict(q=q, v_lin_peak=-q * h_pk, tia=m, compression_dB=20 * math.log10(abs(m["v_peak"]) / (q * h_pk)),
                         vn_max=float(np.max(np.abs(vn[k])))))
    keep = t <= KEEP_T
    lw = tl <= KEEP_T
    return dict(linear=lin, h_pk=h_pk, v_ov=v_ov, runs=runs, t=t[keep], vo=vo[:, keep], vn=vn[:, keep],
                lin_t=tl[lw], lin_v=hl[lw] * 1e-12)


def report(a):
    spice = Path(a.spice)
    res = json.loads((spice / "results" / "board_pulses.json").read_text(encoding="utf-8"))
    rol, ct, cf = model_description()
    sr_cal, _ = tp.calibrate_sr(rol)                 # the internal slew rate that gives 625 V/us in Test 2
    w_t = 2 * math.pi * rol.gbw
    fit = res["fit"]["best"]
    print(f"The full macromodel's node (fitted to the measured gain): C_ext {fit['c_ext'] * 1e12:.3f} pF, C_F {fit['c_f'] * 1e12:.3f} pF, "
          f"eps {100 * fit['eps']:.2f} %, K {fit['k']:.3f}, TIA peak {fit['peak_dB']:+.2f} dB at {fit['f_peak'] / 1e6:.0f} MHz")
    print(f"The model's node (the note's 'macromodel A_-' fit): C_T {ct * 1e12:.3f} pF, C_F {cf * 1e12:.3f} pF; "
          f"GBW {rol.gbw / 1e6:.0f} MHz; calibrated SR {sr_cal / 1e6:.1f} V/us, V_ov = SR/(2 pi GBW) = {sr_cal / w_t * 1e3:.1f} mV")

    # Test 2: the datasheet's test circuit, macromodel against the model
    s = res["slew"]
    t2 = tp.g10_step_test(rol, [625e6, sr_cal])
    print("\nTest 2, G = +10, 2-V step (10-90 % average, 20-80 % average, steepest, V/us):")
    print(f"  macromodel (SPICE):              {s['avg_10_90'] / 1e6:5.0f} {s['avg_20_80'] / 1e6:5.0f} {s['steepest'] / 1e6:5.0f}"
          f"   (its input stage's current up to {s['i17_max_ratio']:.2f} of its static maximum, {s['t_i17_max'] * 1e9:.2f} ns "
          f"after the edge)")
    for lab, r in (("model, 625 V/us as the plateau", t2[0]), (f"model, calibrated {sr_cal / 1e6:.1f} V/us", t2[1])):
        print(f"  {lab:32s} {r['avg_10_90'] / 1e6:5.0f} {r['avg_20_80'] / 1e6:5.0f} {r['steepest'] / 1e6:5.0f}")
    print(f"  the macromodel's static plateau at node 17: {I17_MAX * 1e3:.2f} mA / {MAC_C17 * 1e12:.2f} pF = {SR17 / 1e6:.0f} V/us; "
          f"its pair's V_ov = I_T (V_T/(I_T/2) + R_E) = {V_OV_MAC * 1e3:.1f} mV")
    sr_2080, _ = tp.calibrate_sr(rol, key="avg_20_80")
    print(f"  the model calibrated on the 20-80 % average instead: {sr_2080 / 1e6:.1f} V/us")

    # the pulses
    cmp = {}
    for tag, add in DESIGNS:
        sp = res["pulses"]["designs"][tag]
        charges = [r["q"] for r in sp["runs"]]
        mc = model_runs(rol, ct, cf + add, sr_cal, charges)
        m6 = model_runs(rol, ct, cf + add, 625e6, charges)
        cmp[tag] = dict(cal=mc, sr625=m6)
        h, l = sp["reference"]["metrics"], mc["linear"]
        print(f"\n=== {tag}: linear response per pC (SPICE | model)")
        for key, unit, sc, fmt in (("v_peak", "V/pC", 1, "+.4f"), ("t_peak", "ns", 1e9, ".2f"), ("f_ring", "MHz", 1e-6, ".1f"),
                                   ("tau_decay", "ns", 1e9, ".2f"), ("q_ring", "", 1, ".2f"), ("undershoot_ratio", "", 1, ".3f"),
                                   ("t_settle_1pct", "ns", 1e9, ".1f"), ("t_settle_01pct", "ns", 1e9, ".1f")):
            print(f"  {key:18s} {h[key] * sc:{fmt}} | {l[key] * sc:{fmt}} {unit}")
        print(f"  pulses (SPICE | model at {sr_cal / 1e6:.1f} V/us | model at 625 V/us as the plateau):")
        for rs, rm, r6 in zip(sp["runs"], mc["runs"], m6["runs"]):
            ms, mm = rs["tia"], rm["tia"]
            print(f"  Q {rs['q'] * 1e12:7.4f} pC ({abs(rs['v_lin_peak']):5.2f} V lin): peak {ms['v_peak']:+.3f} | {mm['v_peak']:+.3f} | "
                  f"{r6['tia']['v_peak']:+.3f} V; below linear {-rs['compression_dB']:.2f} | {-rm['compression_dB']:.2f} | "
                  f"{-r6['compression_dB']:.2f} dB; at {ms['t_peak'] * 1e9:.2f} | {mm['t_peak'] * 1e9:.2f} ns; 1 % at "
                  f"{ms['t_settle_1pct'] * 1e9:.1f} | {mm['t_settle_1pct'] * 1e9:.1f} ns; area short {100 * (1 - abs(ms['area_over_q']) / R_F):.2f} | "
                  f"{100 * (1 - abs(mm['area_over_q']) / R_F):.2f} %; max v_n {rs['vn_max'] * 1e3:.0f} | {rm['vn_max'] * 1e3:.0f} mV; "
                  f"ringing {ms['f_ring'] / 1e6:.1f} | {mm['f_ring'] / 1e6:.1f} MHz")
        for name, runs in (("SPICE", sp["runs"]), ("model", mc["runs"]), ("model 625", m6["runs"])):
            cp = tp.compression_points(dict(rf=R_F, runs=runs))
            print(f"  {name}: " + "; ".join(f"{k} at {v['q'] * 1e12:.3f} pC ({v['v_lin']:.3f} V)" if v else f"{k} not reached"
                                             for k, v in cp.items()))
        # the summing node's largest excursion: SPICE against the model, and the charge at which it reaches the
        # absolute maximum of 1.2 V across the inputs (interpolated in Q between the runs)
        q = np.array(charges)
        vs, vm = np.array([r["vn_max"] for r in sp["runs"]]), np.array([r["vn_max"] for r in mc["runs"]])
        lin = q * sp["reference"]["h_pk"] <= 0.1                   # the linear sizes, up to 0.1 V of linear peak
        c_pin = res["pulses"]["c_ext"] + res["pulses"]["c_f"] + add + MAC_C1
        print(f"  largest v_n, SPICE over model: {np.mean(vs[lin] / vm[lin]):.2f} at the linear sizes; "
              f"(C_T + C_F)/(C_ext + C_F + C_C1) = {(ct + cf + add) * 1e12:.3f}/{c_pin * 1e12:.3f} = {(ct + cf + add) / c_pin:.2f}")
        for name, v in (("SPICE", vs), ("model", vm)):
            k = np.where(v >= tp.VDIFF_MAX_OPA846)[0]
            q12 = float(np.interp(tp.VDIFF_MAX_OPA846, v[k[0] - 1:k[0] + 1], q[k[0] - 1:k[0] + 1])) if len(k) and k[0] > 0 else None
            print(f"  {name}: 1.2 V across the inputs at " + (f"{q12 * 1e12:.2f} pC" if q12 else "no run"))
        print(f"  Eq. (36t) with the whole node, 1.2 V x {(ct + cf + add) * 1e12:.3f} pF = {1.2 * (ct + cf + add) * 1e12:.2f} pC; "
              f"with the capacitance outside L_L1, 1.2 V x {c_pin * 1e12:.3f} pF = {1.2 * c_pin * 1e12:.2f} pC")

    # the rows of Table 4.10 (SPICE / model at the calibrated slew rate) and the macromodel's row of Table 4.9
    print("\nTable 4.10 rows:")
    for tag, sizes in (("board", (0.01, 0.1, 0.3, 0.7, 1.0, 1.5, 3.0, 5.0, 10.0)), ("second", (0.01, 0.3, 1.0, 3.0, 10.0))):
        name = "Board" if tag == "board" else "+0.55 pF"
        for rs, rm in zip(res["pulses"]["designs"][tag]["runs"], cmp[tag]["cal"]["runs"]):
            v_lin = abs(rs["v_lin_peak"])
            if not any(abs(v_lin - s) < 1e-6 * s for s in sizes):
                continue
            ms, mm = rs["tia"], rm["tia"]
            sh = [100 * (1 - abs(m["area_over_q"]) / R_F) for m in (ms, mm)]
            vn = [rs["vn_max"] * 1e3, rm["vn_max"] * 1e3]
            print(f"| {name} | {rs['q'] * 1e12:.3g} pC ({v_lin:g} V) | {abs(ms['v_peak']):.3f} / {abs(mm['v_peak']):.3f} V, "
                  f"{ms['t_peak'] * 1e9:.2f} / {mm['t_peak'] * 1e9:.2f} ns | {tp.signed(rs['compression_dB'])} / "
                  f"{tp.signed(rm['compression_dB'])} dB | {ms['t_settle_1pct'] * 1e9:.1f} / {mm['t_settle_1pct'] * 1e9:.1f} ns | "
                  + " / ".join(tp.signed(x).lstrip("+") if abs(x) < 10 else f"{x:.1f}" for x in sh) + " % | "
                  + " / ".join(f"{x:.1f}" if x < 10 else f"{x:.0f}" for x in vn) + " mV |")
    print("\nTable 4.9, the macromodel's row:")
    print(f"| Macromodel in SPICE | {SR17 / 1e6:.0f} V/µs at its integrating node (Eq. (36w)) | {V_OV_MAC * 1e3:.1f} mV | – | "
          f"{s['avg_10_90'] / 1e6:.1f} V/µs | {s['avg_20_80'] / 1e6:.1f} V/µs | {s['steepest'] / 1e6:.0f} V/µs |")

    # the macromodel's input stage
    print(f"\nThe macromodel's input stage (static maximum of i_17: {I17_MAX * 1e3:.2f} mA, node 17 at {SR17 / 1e6:.0f} V/us):")
    for p in res["probe"]:
        w = {k: np.array(v) for k, v in p["wave"].items()}
        t = w["t"]
        i = w["i17"]                                             # into node 17; about 0 at rest (balanced pair)
        k_pk = int(np.argmax(np.abs(i)))
        # the main slew: from 0.6 ns until the node falls below 0.15 V (the pair is still fully switched)
        below = np.where((t > 0.6e-9) & (w["vn"] < 0.15))[0]
        line = (f"  {p['v_lin']:g} V linear ({p['q'] * 1e12:.3f} pC): |i_17| up to {abs(i[k_pk]) * 1e3:.1f} mA "
                f"({abs(i[k_pk]) / I17_MAX:.2f} x) at {t[k_pk] * 1e9:.2f} ns; v_n up to {np.max(w['vn']) * 1e3:.0f} mV, node 2 up to "
                f"{np.max(w['v_base']) * 1e3:.0f} mV, tail node {p['tail_quiescent']:+.3f} -> {np.max(w['v_tail']):+.3f} V")
        if len(below) and t[below[0]] > 0.8e-9:
            sel = (t >= 0.6e-9) & (t <= t[below[0]])
            t1, t2 = t[sel][0], t[sel][-1]
            frac = float(np.mean(-i[sel])) / I17_MAX
            dvo = (np.interp(t2, t, w["vo"]) - np.interp(t1, t, w["vo"])) / (t2 - t1)
            gain = (np.interp(t2, t, w["vo"]) - np.interp(t1, t, w["vo"])) / (np.interp(t2, t, w["v18"]) - np.interp(t1, t, w["v18"]))
            dtail = (np.interp(t2, t, w["v_tail"]) - np.interp(t1, t, w["v_tail"])) / (t2 - t1)
            # while the tail node falls at dV/dt, a capacitance C there supplies C |dV/dt| of the tail current, and the
            # conducting transistor carries only I_T - C |dV/dt|: C = (1 - fraction) I_T / |dV/dt|
            c_tail = (1 - frac) * MAC_I_TAIL / abs(dtail) if dtail < 0 else float("nan")
            line += (f"; from {t1 * 1e9:.1f} to {t2 * 1e9:.2f} ns i_17 is {frac:.2f} of its maximum on average, the output falls at "
                     f"{-dvo / 1e6:.0f} V/us, output/node 18 = {gain:.3f}, the tail falls at {-dtail / 1e6:.0f} V/us "
                     f"(a deficit of {(1 - frac) * MAC_I_TAIL * 1e3:.2f} mA, as from {c_tail * 1e12:.2f} pF at the tail)")
            # the main capacitance at the tail: Q_Q1's base-emitter junction (its base at ground, its emitter 5 ohm from
            # the tail), over the bias it passes through in the same interval, averaged by charge (Delta Q / Delta V)
            vbe = -w["v_tail"][sel]
            vv = np.linspace(vbe.min(), vbe.max(), 400)
            c_avg = np.trapezoid(c_je_q1(vv), vv) / (vv[-1] - vv[0])
            line += (f"; Q_Q1's V_BE runs from {vbe[0]:+.2f} to {vbe[-1]:+.2f} V, its C_je from {c_je_q1(vbe[0]) * 1e12:.2f} to "
                     f"{c_je_q1(vbe[-1]) * 1e12:.2f} pF, {c_avg * 1e12:.2f} pF averaged by charge")
        print(line)

    # the balanced pair's doublet: SPICE against the model on the model's own node
    if "doublet" in res:
        qd = [r["q"] for r in res["doublet"]]
        t, vo, vn, _, _ = tp.simulate(rol, R_F, ct, cf, sr_cal, SWING_100, qd, pulse="doublet:50", window=30e-9, dt=1e-12)
        print("\nA balanced pair, -Q 50 ps after +Q (SPICE | model):")
        rows = []
        for k, r in enumerate(res["doublet"]):
            j = int(np.argmax(np.abs(vo[k])))
            print(f"  {r['q'] * 1e12:4.1f} pC: largest v_n {r['vn_max'] * 1e3:.0f} | {np.max(np.abs(vn[k])) * 1e3:.0f} mV "
                  f"(base {r['vbase_max'] * 1e3:.0f} mV); output {r['vo_peak'] * 1e3:+.0f} | {vo[k][j] * 1e3:+.0f} mV")
            rows.append(f"| {r['q'] * 1e12:.1f} pC | {r['vn_max'] * 1e3:.0f} / {np.max(np.abs(vn[k])) * 1e3:.0f} mV | "
                        f"{r['vbase_max'] * 1e3:.0f} mV | {tp.signed(r['vo_peak'] * 1e3, 0)} / {tp.signed(vo[k][j] * 1e3, 0)} mV |")
        print("\nTable 4.11 rows:\n" + "\n".join(rows))
    if a.figure:
        draw(res, cmp, rol, sr_cal, a.figure)
    if a.summary:
        draw_summary(res, cmp, sr_cal, a.summary)


def draw(res, cmp, rol, sr_cal, stem):
    """Figure 14: (a) Test 2 in SPICE and in the model; (b) the linear responses; (c) large pulses on the board;
    (d) the input stage's current into the integrating node, SPICE against the model's tanh."""
    import matplotlib.pyplot as plt
    from make_case_figures import PANEL, panel_label
    from make_figures import COLORS, DASH, LW, configure_plot_style, export

    configure_plot_style()
    blue, red, grey, green = COLORS["primary"], COLORS["warm_accent"], COLORS["neutral"], COLORS["cool_accent"]
    purple = COLORS["purple_accent"]
    fig, axs = plt.subplots(2, 2, figsize=(2 * PANEL[0], 2 * PANEL[1]), constrained_layout=True)

    # (a) Test 2: the datasheet's G = +10 circuit, 2-V step
    ax = axs[0, 0]
    s = res["slew"]["wave"]
    ax.plot(np.array(s["t"]) * 1e9, s["vo"], color=grey, lw=LW, label="macromodel (SPICE)")
    for sr, col, ls, lab in ((sr_cal, red, "-", f"model, {sr_cal / 1e6:.0f} V/µs (calibrated)"),
                             (625e6, blue, DASH, "model, 625 V/µs as steepest slope")):
        # the same test as Test 2 of tia_pulse_response (g10_step_test), its waveform centred on 0 V and timed from
        # the middle of the input edge, as the SPICE waveform is
        _, (t, v) = tp.g10_step_test(rol, [sr], return_wave=True)
        ax.plot(t * 1e9, v[0], color=col, ls=ls, lw=LW, label=lab)
    ax.set_xlim(-1, 8)
    ax.set_xlabel("Time after the input edge (ns)")
    ax.set_ylabel("Output, gain of +10 (V)")
    ax.legend(loc="lower right", fontsize=7.0)
    panel_label(ax, "(a)", x=0.025)

    # (b) the linear responses per pC; SPICE as a wide light line, so that the model's dashes on top leave it visible
    ax = axs[0, 1]
    for tag, col in (("board", blue), ("second", green)):
        ref = res["pulses"]["designs"][tag]["reference"]["wave"]
        mc = cmp[tag]["cal"]
        lab = "board" if tag == "board" else "+0.55 pF"
        ax.plot(np.array(ref["t"]) * 1e9, ref["vo_per_pC"], color=col, lw=2.6, alpha=0.45, label=f"{lab}, SPICE")
        ax.plot(mc["lin_t"] * 1e9, mc["lin_v"], color=red if tag == "board" else purple, ls=DASH, lw=LW, label=f"{lab}, model")
    ax.axhline(0, color=COLORS["annotation"], lw=0.6)
    ax.set_xlim(-0.5, 30)
    ax.set_xlabel("Time (ns)")
    ax.set_ylabel("TIA output per charge (V/pC)")
    ax.legend(loc="lower right", fontsize=7.0)
    panel_label(ax, "(b)", x=0.025)

    # (c) large pulses on the board: SPICE solid, model dashed
    ax = axs[1, 0]
    sp = res["pulses"]["designs"]["board"]["runs"]
    mc = cmp["board"]["cal"]
    for v_lin, col in ((1.0, green), (3.0, purple), (10.0, red)):
        k = [j for j, r in enumerate(sp) if abs(abs(r["v_lin_peak"]) - v_lin) < 1e-6 * v_lin][0]
        r = sp[k]
        ax.plot(np.array(r["wave"]["t"]) * 1e9, r["wave"]["vo"], color=col, lw=LW,
                label=f"{r['q'] * 1e12:.2f} pC ({v_lin:g} V linear)")
        ax.plot(mc["t"] * 1e9, mc["vo"][k], color=col, ls=DASH, lw=LW)
    ax.axhline(0, color=COLORS["annotation"], lw=0.6)
    ax.set_xlim(-0.5, 16)
    ax.set_xlabel("Time (ns)")
    ax.set_ylabel("TIA output (V)")
    ax.legend(loc="lower right", fontsize=7.0, title="solid SPICE, dashed model", title_fontsize=7.0)
    panel_label(ax, "(c)", x=0.025)

    # (d) the current into the integrating node as a fraction of its static maximum
    ax = axs[1, 1]
    v_ov = sr_cal / (2 * math.pi * rol.gbw)
    for p, col in zip(res["probe"], (green, purple, red)):
        if p["v_lin"] == 1.0:
            continue
        w = p["wave"]
        ax.plot(np.array(w["t"]) * 1e9, np.array(w["i17"]) / I17_MAX, color=col, lw=LW,
                label=f"{p['q'] * 1e12:.2f} pC ({p['v_lin']:g} V linear)")
        k = [j for j, r in enumerate(sp) if abs(abs(r["v_lin_peak"]) - p["v_lin"]) < 1e-6 * p["v_lin"]][0]
        ax.plot(mc["t"] * 1e9, np.tanh(-mc["vn"][k] / v_ov), color=col, ls=DASH, lw=LW)
    ax.axhline(0, color=COLORS["annotation"], lw=0.6)
    for y in (-1, 1):
        ax.axhline(y, color=COLORS["annotation"], lw=0.8, ls=":")
    ax.set_xlim(-0.2, 6)
    ax.set_xlabel("Time (ns)")
    ax.set_ylabel("Input stage's current / its static maximum")
    ax.legend(loc="lower right", fontsize=7.0, title="solid SPICE, dashed model", title_fontsize=7.0)
    panel_label(ax, "(d)", x=0.025)
    export(fig, Path(stem))
    print(f"Figure 14 written to {stem}.png and .pdf")


def draw_summary(res, cmp, sr_cal, stem):
    """Figure 15: Table 4.10 for the board against the charge, the macromodel in SPICE against the time-domain model
    with A_- at the calibrated slew rate and with 625 V/us taken as its internal value (the runs before the
    calibration).  (a) the peak output with the linear peak dotted; (b) the peak against the linear peak in dB;
    (c) the time of the peak; (d) the settling to 1 % of the peak; (e) the area shortfall of Eq. (36v); (f) the
    largest voltage across the inputs, with the absolute maximum of 1.2 V.  It also prints what the calibration changes
    in the model, from 625 V/us to the calibrated value, over the pulses from 0.7 pC up."""
    import matplotlib.pyplot as plt
    from make_case_figures import PANEL, panel_label
    from make_figures import COLORS, DASH, LW, configure_plot_style, export

    configure_plot_style()
    sp = res["pulses"]["designs"]["board"]["runs"]
    cal, old = cmp["board"]["cal"]["runs"], cmp["board"]["sr625"]["runs"]
    # what the calibration changes: the calibrated model against the one with 625 V/us, from 0.7 pC up
    big = [k for k, r in enumerate(cal) if r["q"] >= 0.7e-12]
    d_pk = [abs(cal[k]["tia"]["v_peak"]) / abs(old[k]["tia"]["v_peak"]) - 1 for k in big]
    d_tp = [(cal[k]["tia"]["t_peak"] - old[k]["tia"]["t_peak"]) * 1e9 for k in big]
    d_ts = [(cal[k]["tia"]["t_settle_1pct"] - old[k]["tia"]["t_settle_1pct"]) * 1e9 for k in big]
    # the area shortfall is 100 (1 - |area|/R_F), so its change, calibrated minus 625, is 100 (|area_625| - |area_cal|)/R_F
    d_ar = [100 * (abs(old[k]["tia"]["area_over_q"]) - abs(cal[k]["tia"]["area_over_q"])) / R_F for k in big]
    print(f"\nThe calibration (625 -> {sr_cal / 1e6:.1f} V/us), pulses from 0.7 pC up, calibrated minus 625: peak "
          f"{100 * min(d_pk):+.1f} to {100 * max(d_pk):+.1f} %, time of the peak {min(d_tp):+.2f} to {max(d_tp):+.2f} ns, "
          f"settling to 1 % {min(d_ts):+.1f} to {max(d_ts):+.1f} ns, area shortfall {min(d_ar):+.2f} to {max(d_ar):+.2f} points")
    series = (("macromodel in SPICE", sp, COLORS["neutral"], "-", "o"),
              (f"model, {sr_cal / 1e6:.1f} V/µs (calibrated)", cal, COLORS["warm_accent"], "-", "s"),
              ("model, 625 V/µs taken as the internal value", old, COLORS["primary"], DASH, "^"))
    fig, axs = plt.subplots(3, 2, figsize=(2 * PANEL[0], 3 * PANEL[1]), constrained_layout=True)
    quantities = (  # panel, y value of one run, y label, log y
        (axs[0, 0], lambda r: abs(r["tia"]["v_peak"]), "Peak output (V)", True),
        (axs[0, 1], lambda r: r["compression_dB"], "Peak against linear (dB)", False),
        (axs[1, 0], lambda r: r["tia"]["t_peak"] * 1e9, "Time of the peak (ns)", False),
        (axs[1, 1], lambda r: r["tia"]["t_settle_1pct"] * 1e9, "Settling to 1 % of the peak (ns)", False),
        (axs[2, 0], lambda r: 100 * (1 - abs(r["tia"]["area_over_q"]) / R_F), "Area shortfall, Eq. (36v) (%)", False),
        (axs[2, 1], lambda r: r["vn_max"] * 1e3, "Largest voltage across the inputs (mV)", True),
    )
    for ax, fy, ylab, logy in quantities:
        for lab, runs, col, ls, mk in series:
            q = np.array([r["q"] for r in runs]) * 1e12
            ax.plot(q, [fy(r) for r in runs], color=col, ls=ls, lw=LW, marker=mk, ms=3.0, label=lab)
        ax.set_xscale("log")
        if logy:
            ax.set_yscale("log")
        ax.set_xlabel("Charge per pulse (pC)")
        ax.set_ylabel(ylab)
    q = np.array([r["q"] for r in sp]) * 1e12
    axs[0, 0].plot(q, [abs(r["v_lin_peak"]) for r in sp], color=COLORS["annotation"], ls=":", lw=1.0, label="linear peak (SPICE)")
    axs[0, 1].axhline(0, color=COLORS["annotation"], lw=0.6)
    axs[2, 0].axhline(0, color=COLORS["annotation"], lw=0.6)
    axs[2, 1].axhline(tp.VDIFF_MAX_OPA846 * 1e3, color=COLORS["annotation"], lw=0.8, ls=DASH)
    axs[2, 1].text(0.05, tp.VDIFF_MAX_OPA846 * 1e3 * 1.15, "absolute maximum, 1.2 V", color=COLORS["annotation"])
    for ax, lab in zip(axs.flat, ("(a)", "(b)", "(c)", "(d)", "(e)", "(f)")):
        panel_label(ax, lab, x=0.025 if lab not in ("(b)",) else 0.9)
    handles, labels = axs[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside lower center", ncol=2)
    Path(stem).parent.mkdir(parents=True, exist_ok=True)
    export(fig, Path(stem))
    print(f"Figure 15 written to {stem}.png and .pdf")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("action", choices=("run", "report"))
    ap.add_argument("--ngspice", default=None)
    ap.add_argument("--spice", default=str(HERE.parent / "spice"))
    ap.add_argument("--steps", nargs="+", default=["fit", "slew", "pulses", "probe", "doublet"])
    ap.add_argument("--figure", nargs="?", const=str(HERE.parent / "figures" / "fig37g_opa846_1k5_spice_pulses"), default=None)
    ap.add_argument("--summary", nargs="?", const=str(HERE.parent / "figures" / "fig37h_opa846_1k5_spice_summary"),
                    default=None, help="with report: Figure 15, Table 4.10 for the board against the charge")
    a = ap.parse_args()
    if a.action == "run":
        main_run(a)
    else:
        report(a)


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    main()
