"""Simulations behind the two design examples of Chapter 4: OPA855 and OPA846 at R_F = 2 kOhm.

Usage:
    python case_studies.py run    [--ngspice <library>] [--spice <spice folder>] [--steps nominal cd cf tone]
    python case_studies.py tables [--spice <spice folder>] [--out <markdown file>]

'run' simulates each design with the vendor's macromodel in ngspice, with the fixtures and the
loop-gain method of Chapter 5 (decks under <spice>/runs/case_studies/, which the archive does not
keep), evaluates our analytical model of Chapter 3 at the same points, and writes everything to
<spice>/results/case_studies.json.  --steps runs only the named parts and keeps the others from
the existing file.  'tables' prints the tables of Appendix A4 from that file and writes them to
../data/results/case_studies_tables.md.  make_case_figures.py draws the figures from the same file;
neither runs a simulation.

The designs (Table 4.1 of the note): photodiode capacitance C_D = 1 pF at the summing node, board
capacitance 0.35 pF, R_F = 2 kOhm, total feedback capacitance C_F = 0.20 pF for OPA855 (the
parasitic floor; no capacitor is fitted) and 0.75 pF for OPA846 (the flat design of the analytical
model, 0.745 pF).  Small-signal runs use the supplies and loads of Chapter 5: OPA855 on +/-2.5 V
with 200 ohm, OPA846 on +/-5 V with 100 ohm.  The large-signal runs use a 1-Mohm load and the
supply of Table A6.3, +/-2.5 V (5 V) for OPA855 and +/-6 V for OPA846.

What is simulated for each design:
  nominal  loop gain by Middlebrook's double injection (Eqs. (37)-(39)), transimpedance, input- and
           output-referred noise from 100 kHz to 10 GHz, and a 10-uA photocurrent step (20 mV at the
           output) with a 20-ps rise;
  cd       the same at C_D = 0-5 pF with C_F fixed: how the design responds to the photodiode;
  cf       loop gain and transimpedance on a grid of total C_F at every C_D.  At each C_D the C_F
           that gives the widest bandwidth with phase margin >= 45 deg, gain margin >= 3 dB and
           <= 1 dB of peaking, with C_F >= 0.20 pF (the parasitic floor of Table 1.1), is chosen;
           if no C_F meets all three, the one with the smallest shortfall,
           (45 - PM)+/45 + (3 - GM)+/3 + (peak - 1)+/1, is reported and marked;
  tone     large-signal limits: a sine photocurrent at 20-200 MHz whose output amplitude runs from
           0.5 to 1.3 times the amplitude of Eq. (26), as in Section 5.7; THD from harmonics 2-5.
The dynamic range in 150 MHz (Eq. (27)) is computed from the simulated noise, the transimpedance at
100 MHz and the amplitude of Eq. (26), for I1 + I2 from 1 uA to 20 mA.

Our analytical model (Section 3.5) is evaluated at every point with the datasheet open-loop curve
and the central noise estimate (Eq. (19) with the datasheet e_n, i_n and input capacitance).  Its
step response is the inverse Fourier transform of its transimpedance with the same 20-ps rise.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

import tia_model as tm
from parts_db import PARTS
from run_analysis import C_PCB_NOM, noise_inputs, open_loop_model
from spice_tia_checks import (KT, VENDOR_MODELS, _crossing, band_integral, header, loop_metrics_from_T,
                              prepared_model, read_wrdata, run, tia_body, write_deck, zt_metrics)

HERE = Path(__file__).resolve().parent
Q_E = tm.Q_E

# the two designs; cf_grid_pF is the grid of total C_F scanned at every photodiode capacitance
CASES = {
    "OPA855": dict(R_F=2000.0, C_F=0.20e-12, vs=2.5, vs_tone=2.5,
                   cf_grid_pF=[round(x, 3) for x in np.arange(0.10, 0.6001, 0.02)],
                   tone_fractions=[round(x, 2) for x in np.arange(0.5, 1.301, 0.1)]),
    # the OPA846 model distorts smoothly well below the amplitude of Eq. (26), so its sweep
    # starts at 0.05 of it to find the -60 and -40 dBc points at every frequency
    "OPA846": dict(R_F=2000.0, C_F=0.75e-12, vs=5.0, vs_tone=6.0,
                   cf_grid_pF=[round(x, 3) for x in np.arange(0.30, 2.0001, 0.05)],
                   tone_fractions=[0.05, 0.1, 0.15, 0.2, 0.3, 0.4] + [round(x, 2) for x in np.arange(0.5, 1.301, 0.1)]),
}
C_D_NOM = 1.0e-12
CD_GRID_pF = (0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0)
CF_FLOOR_pF = 0.20
CRIT = dict(pm_deg=45.0, gm_dB=3.0, peak_dB=1.0)
SPOT_F = (1e6, 10e6, 50e6, 100e6, 150e6, 200e6)
TONE_F = (20e6, 50e6, 100e6, 150e6, 200e6)
I_DC_TABLE = (0.0, 1e-4, 1e-3, 1e-2, 2e-2)
I_DC_CURVE = np.logspace(-6, math.log10(2e-2), 61)
DR_BAND = 150e6
F0 = 100e6                      # tone frequency of the dynamic range (Section 3.8)
STEP_A = 10e-6                  # photocurrent step
STEP_RISE = 20e-12
NF_INST_dB = 10.0               # instrument of Eq. (34)
F_CURVE = (1e5, 1e10)           # frequency range of the saved transimpedance curves


def cd_key(c_pF):
    return f"{c_pF:g}"


def folder_for(spice, part, kind, C_D, C_F):
    """Deck folder <spice>/runs/case_<part>/<kind>_D.._F../: two levels below runs/, so that the
    decks' '.include ../../_models/...' (spice_tia_checks.header) finds the translated models."""
    name = f"{kind}_D{C_D * 1e12:.2f}p_F{C_F * 1e12:.3f}p".replace(".", "p")
    return spice / "runs" / f"case_{part}" / name


# ---------------------------------------------------------------- SPICE runs
def spice_ac(ng, spice, part, R_F, C_D, C_F, vs, kind="ac", keep=False):
    """One deck, three AC sweeps (100 kHz-30 GHz, 100 points per decade): the voltage and the
    current injection of Middlebrook's method, then the transimpedance."""
    m = VENDOR_MODELS[part]
    folder = folder_for(spice, part, kind, C_D, C_F)
    deck = header(part, f"{part} TIA, C_D {C_D * 1e12:g} pF, C_F {C_F * 1e12:g} pF", vs) + tia_body(
        part, R_F, C_D + C_PCB_NOM, C_F, m["rl"], vinj_ac=1, iinj_ac=0) + (
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
    out = dict(f_c_MHz=lm["f_c_MHz"], pm_deg=lm["pm_deg"], gm_dB=lm["gm_dB"], second_MHz=lm["second_crossing_MHz"],
               f3_MHz=zm["f3_MHz"], peak_dB=zm["peak_dB"], f_peak_MHz=zm["f_peak_MHz"],
               zt_100MHz_ohm=float(np.interp(math.log10(F0), np.log10(f), np.abs(Z))), errors=err[:2])
    if keep:
        return out, f, T, Z
    return out


def spice_noise(ng, spice, part, R_F, C_D, C_F, vs):
    """Input-referred (inoise) and output (onoise) noise density, 100 kHz-10 GHz, 50 points per decade."""
    m = VENDOR_MODELS[part]
    folder = folder_for(spice, part, "noise", C_D, C_F)
    deck = header(part, f"{part} TIA noise, C_D {C_D * 1e12:g} pF, C_F {C_F * 1e12:g} pF", vs) + tia_body(
        part, R_F, C_D + C_PCB_NOM, C_F, m["rl"]) + (
        ".control\nset wr_singlescale\nset wr_vecnames\nnoise v(oa) Iph dec 50 100k 10G\n"
        "setplot noise1\nwrdata noise.txt inoise_spectrum onoise_spectrum\n.endc\n.end\n")
    log, err = run(ng, write_deck(folder, deck))
    d = read_wrdata(folder / "noise.txt")
    return d[:, 0], d[:, 1], d[:, 2], err[:2]


def spice_step(ng, spice, part, R_F, C_D, C_F, vs):
    """A 10-uA photocurrent step with a 20-ps rise, starting at 2 ns; the output sign is flipped
    so that the step is positive."""
    m = VENDOR_MODELS[part]
    folder = folder_for(spice, part, "step", C_D, C_F)
    deck = header(part, f"{part} TIA step, C_D {C_D * 1e12:g} pF, C_F {C_F * 1e12:g} pF", vs) + tia_body(
        part, R_F, C_D + C_PCB_NOM, C_F, m["rl"],
        iph=f"Iph 0 inm PULSE(0 {STEP_A:g} 2n {STEP_RISE:g} {STEP_RISE:g} 30n 60n)") + (
        ".control\nset wr_singlescale\nset wr_vecnames\ntran 1p 32n 0 2p\nlinearize v(oa)\n"
        "wrdata step.txt v(oa)\n.endc\n.end\n")
    log, err = run(ng, write_deck(folder, deck))
    d = read_wrdata(folder / "step.txt")
    return d[:, 0], -d[:, 1], err[:2]


def step_metrics(t, v, t0=2e-9):
    v0 = float(np.mean(v[t < t0 - 0.1e-9]))
    vf = float(np.mean(v[(t > 25e-9) & (t < 31.5e-9)]))
    step = vf - v0
    after = t > t0
    over = float((np.max(v[after]) - vf) / step * 100)
    i10 = np.where(after & (v - v0 >= 0.1 * step))[0][0]
    i90 = np.where(after & (v - v0 >= 0.9 * step))[0][0]
    # settling to 1 % of the step: the last time the error exceeds 1 %
    err = np.abs(v - vf) > 0.01 * abs(step)
    k = np.where(after & err)[0]
    t_settle = float(t[k[-1]] - t0) if len(k) else 0.0
    return dict(step_mV=step * 1e3, overshoot_pct=max(0.0, over), rise_10_90_ps=float((t[i90] - t[i10]) * 1e12),
                settle_1pct_ns=t_settle * 1e9)


def spice_tone(ng, spice, part, R_F, C_D, C_F, vs, f0, frac, claim, zmag):
    """A sine photocurrent of amplitude frac * claim / |Z_T(f0)| into the design with a 1-Mohm load;
    48 periods at 256 points per period, the last 32 windowed (Hann) and transformed."""
    folder = folder_for(spice, part, f"tone_f{f0 / 1e6:g}M_a{frac:g}", C_D, C_F)
    ipk = frac * claim / zmag
    period = 1 / f0
    tstep = period / 256
    tstop = 48 * period
    deck = header(part, f"{part} TIA tone {f0 / 1e6:g} MHz at {frac:g} x the amplitude of Eq. (26)", vs) + tia_body(
        part, R_F, C_D + C_PCB_NOM, C_F, 1e6, iph=f"Iph 0 inm SIN(0 {ipk:.6e} {f0:g})") + (
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
    return dict(frac=float(frac), ipk_mA=ipk * 1e3, v_pos=float(np.max(vv)), v_neg=float(-np.min(vv)),
                hd2_dBc=float(20 * np.log10(h[1] / h[0])), hd3_dBc=float(20 * np.log10(h[2] / h[0])),
                thd_dBc=float(10 * np.log10(sum(x ** 2 for x in h[1:]) / h[0] ** 2)), errors=err[:1])


# ---------------------------------------------------------------- analytical model
class Analytic:
    """Our analytical model of Chapter 3 for one amplifier: the model behind every dashed
    curve ("analytical model", "model") of Figures 4 and 6-8 and every model column of
    Tables A4.1-A4.3.  It is the same model as in every other table of the note
    (run_analysis.py), only evaluated at the points of Chapter 4.

    Inputs, all from the part's record in parts_db.PARTS, where each value cites its
    datasheet page:
      - the open-loop gain A(f): magnitude and phase digitized from the datasheet's
        open-loop plot (data/specs/<PART>.json), interpolated in log f by
        tia_model.InterpOpenLoop (Section 3.5); run_analysis.open_loop_model builds it;
      - the noise: the datasheet's voltage-noise curve e_n(f) and white current noise
        i_n (run_analysis.noise_inputs); for these bipolar parts the central estimate of
        Section 3.7 is the only one;
      - the input capacitance C_CM + C_DIFF from the datasheet table.
    The board adds C_PCB = 0.35 pF and the photodiode pair C_D (Table 1.1), so the
    capacitance from the summing node to AC ground is C_T = C_D + C_PCB + C_CM + C_DIFF
    (Eq. (7)).  The feedback capacitance C_F is the total, external plus parasitic.

    What the model leaves out, and the macromodels contain: the amplifier's output
    impedance, the difference between the gain from the inverting and from the
    non-inverting input above 1 GHz, frequency-dependent input admittance, and any
    large-signal behaviour (Sections 3.5 and 5.3).
    """

    def __init__(self, part):
        self.p = PARTS[VENDOR_MODELS[part]["db"]]       # datasheet record of the part
        self.ol, *_ = open_loop_model(self.p)            # primary model: the interpolated datasheet curve
        self.nz = noise_inputs(self.p)                   # e_n(f), i_n, C_CM + C_DIFF
        self.c_in = self.p["c_cm"] + self.p["c_diff"]   # amplifier input capacitance, part of C_T

    def C_T(self, C_D):
        """Total capacitance from the summing node to AC ground, Eq. (7)."""
        return C_D + C_PCB_NOM + self.c_in

    def loop(self, R_F, C_D, C_F):
        """Loop and closed-loop figures of one design, as tia_model.loop_metrics defines them
        (Section 3.5), on 6000 log-spaced points from 10 kHz to 50 GHz:
          Z_F = R_F/(1 + s R_F C_F) (Eq. (8)),  NG = 1 + s C_T Z_F,  T = A/NG (Eq. (10)),
          Z_T = -Z_F T/(1 + T) (Eq. (9));
          f_c_MHz   first downward crossing of |T| = 1 (log-log interpolation);
          pm_deg    180 deg + angle(T) at f_c;
          gm_dB     -20 log|T| where the unwrapped loop phase first reaches -180 deg;
          stable, second  False / True if |T| regains 1 above 1.2 f_c (a second crossing);
          f3_MHz    first frequency at which |Z_T|/R_F falls below 1/sqrt(2);
          peak_dB   20 log of the largest |Z_T|/R_F, floored at 0;
          ng_at_fc  |NG| at f_c, and ng_hf the high-frequency noise gain 1 + C_T/C_F (Eq. (11));
          zt_100MHz_ohm  |Z_T| at F0 = 100 MHz, the tone of the dynamic range (Eq. (27)).
        The gain margin rests on the curve's extrapolation above its last plotted point
        (about 1 GHz for OPA846, 9.7 GHz for OPA855) and is indicative only (Section 5.3)."""
        m = tm.loop_metrics(self.ol, R_F, self.C_T(C_D), C_F)
        fin = lambda x: None if x is None or not np.isfinite(x) else float(x)   # NaN -> None for JSON
        Z, _, _ = tm.tia_tf(np.array([F0]), self.ol, R_F, self.C_T(C_D), C_F)
        return dict(f_c_MHz=fin(m["f_c"] / 1e6), pm_deg=fin(m["pm_deg"]), gm_dB=fin(m["gm_dB"]),
                    f3_MHz=fin(m["f_3dB"] / 1e6), peak_dB=max(0.0, float(m["peaking_dB"])),
                    stable=bool(m["stable"]), second=bool(m["second_crossing"]),
                    ng_at_fc=fin(m["ng_at_fc"]), ng_hf=fin(m["ng_hf"]), zt_100MHz_ohm=float(abs(Z[0])))

    def noise(self, R_F, C_D, C_F, f, i_dc=0.0):
        """Input-referred noise density (A/rtHz) and its terms (A^2/Hz), Eq. (19):
            S_i(f) = 4 k_B T/R_F + i_n^2 + e_n(f)^2 [1/R_F^2 + (2 pi f C_tot)^2] + 2 q I_DC,
            C_tot = C_T + C_F,  T = 298.15 K,
        evaluated by tia_model.noise_components with the central estimate.  The terms dict
        holds 'RF', 'i_n', 'e_n' (the whole voltage-noise term, as drawn in Figures 4d and
        6d) and 'shot', besides two terms that are zero here."""
        c = tm.noise_components(np.asarray(f, float), R_F, self.C_T(C_D), C_F, self.nz, i_dc=i_dc)
        return np.sqrt(c["total"]), c

    def step(self, R_F, C_D, C_F, f_max=40e9, df=1e6):
        """Step response of the model's transimpedance to the photocurrent step of the SPICE
        runs (Figures 4c and 6c): STEP_A with a linear rise of STEP_RISE, starting at 2 ns.

        The input current's derivative is a rectangular pulse of width tau = STEP_RISE and
        area STEP_A, whose Fourier transform is STEP_A sinc(f tau) exp(-j pi f tau) (numpy's
        sinc(x) = sin(pi x)/(pi x)).  The output's derivative is therefore the inverse
        transform of H(f) = Z_T(f) sinc(f tau) exp(-j pi f tau), times STEP_A, and the output
        is its running integral.

        Numerically: Z_T is sampled at f_k = k df, k = 0..N-1 (df = 1 MHz up to 40 GHz).  With
        M = 2(N - 1) real samples spaced dt = 1/(M df), numpy's irfft returns
        (1/M) sum_k H_k exp(j 2 pi k n/M) over the Hermitian spectrum, which is h(t_n) dt; so
        the running integral of h is simply cumsum(irfft(H)), and its last value is H_0 =
        Z_T(0) = -R_F, i.e. the 20-mV final value for 10 uA.  The record is periodic in
        1/df = 1 us, far longer than the 30 ns kept, so the wrap-around is negligible.  Z_T is
        evaluated at 1 Hz in place of f = 0 (the curve is interpolated in log f) and its
        imaginary part there dropped.  The sign is flipped like the SPICE output of the
        inverting TIA, and the time axis shifted by the 2-ns delay of the SPICE pulse.  Above
        the datasheet curve's last point the model's A(f) is extrapolated (InterpOpenLoop);
        |Z_T| is small there and the step does not depend on it."""
        n = int(round(f_max / df)) + 1
        f = np.arange(n) * df
        f[0] = 1.0                                       # stands for DC (log10(0) is undefined)
        Z, _, _ = tm.tia_tf(f, self.ol, R_F, self.C_T(C_D), C_F)
        Z[0] = Z[0].real
        win = np.sinc(f * STEP_RISE) * np.exp(-1j * np.pi * f * STEP_RISE)   # the 20-ps ramp of the source
        h = np.fft.irfft(Z * win)                        # h(t_n) dt for a unit-area input pulse
        dt = 1 / (len(h) * df)
        v = -np.cumsum(h) * STEP_A                       # running integral; flipped like the SPICE output
        t = np.arange(len(h)) * dt + 2e-9                # the SPICE pulse starts at 2 ns
        keep = t <= 32e-9
        return np.concatenate([[0.0, 2e-9 - dt], t[keep]]), np.concatenate([[0.0, 0.0], v[keep]])


# ---------------------------------------------------------------- helpers
def spot(f, y, x):
    """y at frequency x, interpolated linearly in log f (the spot values of the tables)."""
    return float(np.interp(math.log10(x), np.log10(f), y))


def band_rms(f, S, lo, hi):
    """sqrt of the integral of the density S over exactly lo..hi (spice_tia_checks.band_integral)."""
    return math.sqrt(band_integral(f, S, lo, hi))


def penalty(f, inn, R_F, lo=10e6, hi=150e6):
    """Band penalty of Eq. (21): the input-referred noise power integrated over 10-150 MHz
    against the Johnson noise of R_F over the same band, in dB."""
    return 10 * math.log10(band_integral(f, inn ** 2, lo, hi) / (4 * KT / R_F * (hi - lo)))


def vpk_claim(part, f0):
    """Largest output amplitude at f0 by Eq. (26), from the datasheet: the smaller of half the
    output range with a light load (the swing of Table A6.28, centred) and the slew-rate limit
    SR/(2 pi f0).  The output-current term of Eq. (26) is not binding for these two designs at
    1 Mohm.  Returns the amplitude (V peak) and which of the two sets it."""
    s = PARTS[VENDOR_MODELS[part]["db"]]["dr"]
    vol, voh = s["swing_light"]
    v_sw, v_sr = (voh - vol) / 2, s["sr"] * 1e6 / (2 * math.pi * f0)
    return min(v_sw, v_sr), ("swing" if v_sw <= v_sr else "slew rate")


def dynamic_range(S_band, zt, vpk, i_dc):
    """Eqs. (27) and (28): electronic and usable dynamic range in DR_BAND for a tone of amplitude vpk
    at F0, with S_band the integral of the input-referred noise density from 0 to DR_BAND (A^2).
        I_max = V_pk / (sqrt(2) |Z_T(F0)|)                  largest photocurrent tone, rms
        i_n,B = sqrt(S_band + 2 q I_DC B)                   band noise with the shot noise of I_1 + I_2
        DR    = 20 log10(I_max / i_n,B)                     Eq. (27), electronic
        DR_usable = 20 log10(min(I_max, I_DC/sqrt(2)) / i_n,B)   Eq. (28), the light's own ceiling
    S_band comes from the SPICE noise (100 kHz to 150 MHz; the part below 100 kHz is 0.07 % of
    the band) or from the model's Eq. (19) on a linear grid from 10 kHz."""
    i_max = vpk / (math.sqrt(2) * zt)                        # largest tone in photocurrent, rms
    i_nb = math.sqrt(S_band + 2 * Q_E * i_dc * DR_BAND)      # band noise including shot noise
    elec = 20 * math.log10(i_max / i_nb)
    usable = None if i_dc == 0 else 20 * math.log10(min(i_max, i_dc / math.sqrt(2)) / i_nb)
    return elec, usable, i_nb


def choose_cf(rows, cf_grid):
    """The widest-band C_F >= the floor that meets all three criteria; else the smallest shortfall."""
    best, best_f3 = None, -1.0
    for cf, r in zip(cf_grid, rows):
        if cf < CF_FLOOR_pF - 1e-9 or r["pm_deg"] is None or r["f3_MHz"] is None:
            continue
        ok = (r["pm_deg"] >= CRIT["pm_deg"] and r["gm_dB"] is not None and r["gm_dB"] >= CRIT["gm_dB"]
              and r["peak_dB"] <= CRIT["peak_dB"] and not r.get("second_MHz") and not r.get("second"))
        if ok and r["f3_MHz"] > best_f3:
            best, best_f3 = cf, r["f3_MHz"]
    if best is not None:
        return best, True

    def shortfall(r):
        gm = r["gm_dB"] if r["gm_dB"] is not None else 99.0
        return (max(0.0, CRIT["pm_deg"] - r["pm_deg"]) / CRIT["pm_deg"] + max(0.0, CRIT["gm_dB"] - gm) / CRIT["gm_dB"]
                + max(0.0, r["peak_dB"] - CRIT["peak_dB"]) / CRIT["peak_dB"])
    cands = [(shortfall(r), -(r["f3_MHz"] or 0), cf) for cf, r in zip(cf_grid, rows)
             if cf >= CF_FLOOR_pF - 1e-9 and r["pm_deg"] is not None and not r.get("second_MHz")
             and not r.get("second")]
    return (min(cands)[2], False) if cands else (None, False)


def first_estimate(part, an, R_F, C_F, zt_model):
    """The four equations of Section 4.1 (Eqs. (33)-(36)) with the datasheet values, in their
    practical units (kOhm, pF, MHz, nV/rtHz, pA/rtHz, mA), exactly as Sections 4.2 and 4.4 work
    them by hand.  zt_model is the model's |Z_T| at 100 MHz (Analytic.loop), used in Eq. (34)."""
    p = an.p
    rf_k = R_F / 1e3                               # R_F in kOhm
    en, i_n = p["en"] * 1e9, p["in_"] * 1e12       # e_n in nV/rtHz, i_n in pA/rtHz (datasheet values)
    c_t = an.C_T(C_D_NOM) * 1e12                   # C_T in pF, Eq. (7)
    c_tot = c_t + C_F * 1e12                       # C_tot = C_T + C_F
    gbw = p["gbw"] / 1e6                           # GBW in MHz
    # Eq. (33) at f = 100 MHz: 16.47/R_F + i_n^2 + e_n^2/R_F^2 + (6.283e-3 e_n f C_tot)^2, in pA^2/Hz
    terms = dict(RF=16.47 / rf_k, i_n=i_n ** 2, en_RF=en ** 2 / rf_k ** 2, en_C=(6.283e-3 * en * 100 * c_tot) ** 2)
    i_eq0 = math.sqrt(sum(terms.values()))                       # dark
    i_eq1 = math.sqrt(sum(terms.values()) + 320.4 * 1.0)         # + 320.4 pA^2/Hz per mA of I_DC
    shot1 = math.sqrt(320.4)                                     # shot noise of 1 mA alone
    i_inst = 0.907 * 10 ** (NF_INST_dB / 20) / (zt_model / 1e3)  # Eq. (34), instrument of NF_INST_dB
    vpk, lim = vpk_claim(part, F0)                               # Eq. (26) at 100 MHz
    cf_bw = 17.84 * math.sqrt(c_t / (rf_k * gbw))                # maximally flat C_F, Eq. (15)
    out = dict(C_T_pF=c_t, C_tot_pF=c_tot, terms_pA2=terms, i_eq_0mA_pA=i_eq0, i_eq_1mA_pA=i_eq1,
               shot_1mA_pA=shot1, excess_1mA_dB=20 * math.log10(i_eq1 / shot1),
               i_inst_pA=i_inst, inst_add_dark_dB=10 * math.log10(1 + i_inst ** 2 / i_eq0 ** 2),
               inst_add_1mA_dB=10 * math.log10(1 + i_inst ** 2 / i_eq1 ** 2),
               Pn_dark_dBm_Hz=-173.0 + 20 * math.log10(i_eq0 * zt_model / 1e3),
               cf_butterworth_pF=cf_bw, f3_single_pole_MHz=12.62 * math.sqrt(gbw / (rf_k * c_tot)),
               f3_single_pole_at_cf_bw_MHz=12.62 * math.sqrt(gbw / (rf_k * (c_t + cf_bw))),
               ct_min_pF=318.3 * (p["g_min"] - 1) ** 2 / (rf_k * gbw), vpk_V=vpk, vpk_limit=lim,
               dr_shot_dB={f"{i:g} mA": 91.9 + 20 * math.log10(vpk / (rf_k * math.sqrt(i * DR_BAND / 1e6)))
                           for i in (1.0, 10.0, 20.0)},
               en=en, i_n=i_n, gbw_MHz=gbw, g_min=p["g_min"], c_cm_pF=p["c_cm"] * 1e12, c_diff_pF=p["c_diff"] * 1e12,
               sr_V_us=p["dr"]["sr"], swing=list(p["dr"]["swing_light"]))
    return out


def r6(x):
    return None if x is None else float(f"{x:.6g}")


# ---------------------------------------------------------------- the run
def run_case(ng, spice, part, steps, old):
    cs = CASES[part]
    R_F, C_F, vs = cs["R_F"], cs["C_F"], cs["vs"]
    an = Analytic(part)
    res = dict(old) if old else {}
    res["design"] = dict(R_F=R_F, C_F_pF=C_F * 1e12, C_D_pF=C_D_NOM * 1e12, C_PCB_pF=C_PCB_NOM * 1e12,
                         C_in_datasheet_pF=an.c_in * 1e12, supply_small_signal_V=vs, R_L_ohm=VENDOR_MODELS[part]["rl"],
                         supply_tone_V=cs["vs_tone"], model=VENDOR_MODELS[part]["source"])
    f_noise_model = np.logspace(5, 10, 2001)

    if "nominal" in steps or "cd" in steps:
        sweep, curves = [], dict(zt_f_Hz=None, zt_dB={}, zt_deg={}, noise_f_Hz=None, noise_in_pA={}, noise_out_nV={})
        for c_pF in CD_GRID_pF:
            C_D = c_pF * 1e-12
            ac, f, T, Z = spice_ac(ng, spice, part, R_F, C_D, C_F, vs, kind="fixed", keep=True)
            fn, inn, onn, nerr = spice_noise(ng, spice, part, R_F, C_D, C_F, vs)
            ts, vstep, serr = spice_step(ng, spice, part, R_F, C_D, C_F, vs)
            st = step_metrics(ts, vstep)
            sel = (f >= F_CURVE[0] * 0.999) & (f <= F_CURVE[1] * 1.001)
            if curves["zt_f_Hz"] is None:
                curves["zt_f_Hz"] = [r6(x) for x in f[sel]]
                curves["noise_f_Hz"] = [r6(x) for x in fn]
            k = cd_key(c_pF)
            curves["zt_dB"][k] = [round(float(x), 4) for x in 20 * np.log10(np.abs(Z[sel]))]
            curves["zt_deg"][k] = [round(float(x), 3) for x in np.degrees(np.unwrap(np.angle(-Z[sel])))]
            curves["noise_in_pA"][k] = [r6(x * 1e12) for x in inn]
            curves["noise_out_nV"][k] = [r6(x * 1e9) for x in onn]
            S_band = band_integral(fn, inn ** 2, fn[0], DR_BAND)
            noise = dict(spot_pA={f"{x / 1e6:g} MHz": spot(fn, inn, x) * 1e12 for x in SPOT_F},
                         penalty_10_150_dB=penalty(fn, inn, R_F), band_0_150_nA=math.sqrt(S_band) * 1e9,
                         v_out_rms_mV=math.sqrt(band_integral(fn, onn ** 2, fn[0], fn[-1])) * 1e3,
                         v_out_rms_150MHz_mV=math.sqrt(band_integral(fn, onn ** 2, fn[0], DR_BAND)) * 1e3)
            # analytical model at the same point
            a = an.loop(R_F, C_D, C_F)
            ain, _ = an.noise(R_F, C_D, C_F, f_noise_model)
            a_S_band = band_integral(f_noise_model, ain ** 2, f_noise_model[0], DR_BAND)
            a_noise = dict(spot_pA={f"{x / 1e6:g} MHz": float(an.noise(R_F, C_D, C_F, [x])[0][0] * 1e12) for x in SPOT_F},
                           penalty_10_150_dB=penalty(f_noise_model, ain, R_F), band_0_150_nA=math.sqrt(a_S_band) * 1e9)
            ta, va = an.step(R_F, C_D, C_F)
            a_step = step_metrics(ta, va)
            row = dict(C_D_pF=c_pF, C_T_pF=an.C_T(C_D) * 1e12, NG_inf=1 + an.C_T(C_D) / C_F,
                       spice=dict(**ac, **st, noise=noise, errors_noise=nerr, errors_step=serr),
                       analytical=dict(**a, **{k2: v2 for k2, v2 in a_step.items() if k2 != "step_mV"}, noise=a_noise))
            sweep.append(row)
            if abs(c_pF - C_D_NOM * 1e12) < 1e-9:
                sel_t = (f >= 1e6) & (f <= 3e10)
                curves["loop_f_Hz"] = [r6(x) for x in f[sel_t]]
                curves["loop_dB"] = [round(float(x), 4) for x in 20 * np.log10(np.abs(T[sel_t]))]
                curves["loop_deg"] = [round(float(x), 3) for x in np.degrees(np.unwrap(np.angle(T[sel_t])))]
                keep = slice(None, None, 5)
                curves["step_t_ns"] = [round(float(x) * 1e9, 4) for x in ts[keep]]
                curves["step_mV"] = [round(float(x) * 1e3, 5) for x in vstep[keep]]
                curves["step_analytical_t_ns"] = [round(float(x) * 1e9, 4) for x in ta]
                curves["step_analytical_mV"] = [round(float(x) * 1e3, 5) for x in va]
                res["nominal"] = row
                res["first_estimate"] = first_estimate(part, an, R_F, C_F, a["zt_100MHz_ohm"])
            print(f"{part} C_D {c_pF:4.2f} pF, C_F {C_F * 1e12:.2f} pF | SPICE f_c {ac['f_c_MHz']:.0f} MHz, "
                  f"PM {ac['pm_deg']:.1f}, GM {ac['gm_dB'] if ac['gm_dB'] is None else round(ac['gm_dB'], 1)} dB, "
                  f"f3 {ac['f3_MHz']:.0f} MHz, peak {ac['peak_dB']:.2f} dB, overshoot {st['overshoot_pct']:.1f} %, "
                  f"noise 100 MHz {noise['spot_pA']['100 MHz']:.2f} pA, penalty {noise['penalty_10_150_dB']:.2f} dB | "
                  f"model PM {a['pm_deg']:.1f}, f3 {a['f3_MHz']:.0f} MHz, peak {a['peak_dB']:.2f} dB, "
                  f"noise {a_noise['spot_pA']['100 MHz']:.2f} pA | errors {ac['errors'][:1]}{nerr[:1]}{serr[:1]}")
        res["cd_sweep"] = sweep
        res["curves"] = curves

    if "cf" in steps:
        grid = cs["cf_grid_pF"]
        by_cd, redesign = {}, []
        for c_pF in CD_GRID_pF:
            C_D = c_pF * 1e-12
            srows, arows = [], []
            for cf_pF in grid:
                r = spice_ac(ng, spice, part, R_F, C_D, cf_pF * 1e-12, vs, kind="cf")
                srows.append({k: r[k] for k in ("f_c_MHz", "pm_deg", "gm_dB", "second_MHz", "f3_MHz", "peak_dB")})
                arows.append({k: v for k, v in an.loop(R_F, C_D, cf_pF * 1e-12).items()
                              if k in ("f_c_MHz", "pm_deg", "gm_dB", "f3_MHz", "peak_dB", "stable", "second")})
            by_cd[cd_key(c_pF)] = dict(spice=srows, analytical=arows)
            cf_s, ok_s = choose_cf(srows, grid)
            # the analytical choice uses phase margin and peaking only: its gain margins are not reliable
            # (Section 5.3), so the gain-margin criterion is waived for it
            arows_gm = [dict(r, gm_dB=99.0 if r["stable"] else None) for r in arows]
            cf_a, ok_a = choose_cf(arows_gm, grid)
            entry = dict(C_D_pF=c_pF, spice=dict(C_F_pF=cf_s, meets=ok_s), analytical=dict(C_F_pF=cf_a, meets=ok_a))
            if cf_s is not None:
                i = grid.index(cf_s)
                entry["spice"].update(srows[i])
                fn, inn, onn, nerr = spice_noise(ng, spice, part, R_F, C_D, cf_s * 1e-12, vs)
                entry["spice"]["penalty_10_150_dB"] = penalty(fn, inn, R_F)
                entry["spice"]["noise_100MHz_pA"] = spot(fn, inn, 100e6) * 1e12
            if cf_a is not None:
                i = grid.index(cf_a)
                entry["analytical"].update(arows[i])
                ain, _ = an.noise(R_F, C_D, cf_a * 1e-12, f_noise_model)
                entry["analytical"]["penalty_10_150_dB"] = penalty(f_noise_model, ain, R_F)
            redesign.append(entry)
            s = entry["spice"]
            print(f"{part} C_D {c_pF:4.2f} pF: chosen C_F (SPICE) {cf_s} pF {'meets' if ok_s else 'SHORTFALL'}: "
                  f"PM {s.get('pm_deg') and round(s['pm_deg'], 1)}, GM {s.get('gm_dB') and round(s['gm_dB'], 1)}, "
                  f"f3 {s.get('f3_MHz') and round(s['f3_MHz'])} MHz, peak {s.get('peak_dB') and round(s['peak_dB'], 2)} dB | "
                  f"analytical {cf_a} pF {'meets' if ok_a else 'SHORTFALL'}")
        res["cf_scan"] = dict(cf_pF=grid, by_cd=by_cd)
        res["redesign"] = redesign

    if "tone" in steps:
        zt_row = next(r for r in res["cd_sweep"] if abs(r["C_D_pF"] - C_D_NOM * 1e12) < 1e-9)
        zt_curve = res["curves"]
        f_c, z_db = np.array(zt_curve["zt_f_Hz"]), np.array(zt_curve["zt_dB"][cd_key(C_D_NOM * 1e12)])
        rows = {}
        for f0 in TONE_F:
            zmag = 10 ** (float(np.interp(math.log10(f0), np.log10(f_c), z_db)) / 20)
            claim, lim = vpk_claim(part, f0)
            sweep = [spice_tone(ng, spice, part, R_F, C_D_NOM, C_F, cs["vs_tone"], f0, fr, claim, zmag)
                     for fr in cs["tone_fractions"]]
            fr = np.array([r["frac"] for r in sweep])
            thd = np.array([r["thd_dBc"] for r in sweep])
            x60, x40 = _crossing(fr, thd, -60.0), _crossing(fr, thd, -40.0)
            rows[f"{f0 / 1e6:g} MHz"] = dict(claim_V=claim, limit=lim, zt_ohm=zmag, frac_at_thd_m60=x60, frac_at_thd_m40=x40,
                                             v_at_thd_m60=None if x60 is None else x60 * claim,
                                             v_at_thd_m40=None if x40 is None else x40 * claim, sweep=sweep)
            print(f"{part} tone {f0 / 1e6:5.0f} MHz: Eq. (26) {claim:.3f} V ({lim}); THD -60 dBc at "
                  f"{'-' if x60 is None else f'{x60 * claim:.3f} V ({x60:.2f} x)'}, -40 dBc at "
                  f"{'-' if x40 is None else f'{x40 * claim:.3f} V ({x40:.2f} x)'}; errors {sweep[0]['errors']}")
        res["tone"] = rows

    # dynamic range from the nominal noise (SPICE) and from the analytical model
    if "cd_sweep" in res:
        nom = next(r for r in res["cd_sweep"] if abs(r["C_D_pF"] - C_D_NOM * 1e12) < 1e-9)
        cur = res["curves"]
        fn = np.array(cur["noise_f_Hz"])
        inn = np.array(cur["noise_in_pA"][cd_key(C_D_NOM * 1e12)]) * 1e-12
        S_spice = band_integral(fn, inn ** 2, fn[0], DR_BAND)
        f_lin = np.linspace(1e4, DR_BAND, 30001)
        ain, _ = an.noise(R_F, C_D_NOM, C_F, f_lin)
        S_model = float(np.trapezoid(ain ** 2, f_lin))
        vpk, lim = vpk_claim(part, F0)
        dr = dict(vpk_V=vpk, limit=lim, zt_spice_ohm=nom["spice"]["zt_100MHz_ohm"],
                  zt_model_ohm=nom["analytical"]["zt_100MHz_ohm"], table={}, curve=dict(i_dc_mA=[], spice=[],
                                                                                    spice_usable=[], model=[]))
        for i_dc in I_DC_TABLE:
            e_s, u_s, n_s = dynamic_range(S_spice, dr["zt_spice_ohm"], vpk, i_dc)
            e_m, u_m, n_m = dynamic_range(S_model, dr["zt_model_ohm"], vpk, i_dc)
            dr["table"][f"{i_dc * 1e3:g} mA"] = dict(spice_dB=e_s, spice_usable_dB=u_s, spice_noise_nA=n_s * 1e9,
                                                     model_dB=e_m, model_usable_dB=u_m, model_noise_nA=n_m * 1e9)
        for i_dc in I_DC_CURVE:
            e_s, u_s, _ = dynamic_range(S_spice, dr["zt_spice_ohm"], vpk, i_dc)
            e_m, _, _ = dynamic_range(S_model, dr["zt_model_ohm"], vpk, i_dc)
            dr["curve"]["i_dc_mA"].append(r6(i_dc * 1e3))
            dr["curve"]["spice"].append(round(e_s, 3))
            dr["curve"]["spice_usable"].append(round(u_s, 3))
            dr["curve"]["model"].append(round(e_m, 3))
        dr["i_max_mA_rms"] = vpk / (math.sqrt(2) * dr["zt_spice_ohm"]) * 1e3
        # the same with the amplitude at which the macromodel's THD reaches -40 or -60 dBc at F0
        tone0 = res.get("tone", {}).get(f"{F0 / 1e6:g} MHz")
        dr["at_thd"] = {}
        for lev in ("m40", "m60"):
            v_t = tone0 and tone0.get(f"v_at_thd_{lev}")
            if v_t:
                dr["at_thd"][lev] = dict(v_pk_V=v_t, table={
                    f"{i * 1e3:g} mA": dynamic_range(S_spice, dr["zt_spice_ohm"], v_t, i)[0] for i in I_DC_TABLE})
        res["dr"] = dr
        print(f"{part} DR (SPICE noise) " + ", ".join(f"{k} {v['spice_dB']:.1f}" for k, v in dr["table"].items())
              + " dB | model " + ", ".join(f"{k} {v['model_dB']:.1f}" for k, v in dr["table"].items()) + " dB")
    return res


def load_results(spice):
    """The summary (case_studies.json) with the curves (case_studies_curves.json) merged back in."""
    res_file = spice / "results" / "case_studies.json"
    cur_file = spice / "results" / "case_studies_curves.json"
    res = json.loads(res_file.read_text(encoding="utf-8")) if res_file.exists() else {}
    if cur_file.exists():
        for part, cur in json.loads(cur_file.read_text(encoding="utf-8")).items():
            res.setdefault(part, {})["curves"] = cur
    return res


def save_results(spice, res):
    """The curves go to a compact file of their own, the rest to an indented summary."""
    out = spice / "results"
    out.mkdir(parents=True, exist_ok=True)
    summary = {k: ({kk: vv for kk, vv in v.items() if kk != "curves"} if isinstance(v, dict) else v)
               for k, v in res.items()}
    curves = {k: v["curves"] for k, v in res.items() if isinstance(v, dict) and "curves" in v}
    (out / "case_studies.json").write_text(json.dumps(summary, indent=1, default=float), encoding="utf-8", newline="\n")
    (out / "case_studies_curves.json").write_text(json.dumps(curves, separators=(",", ":"), default=float),
                                                  encoding="utf-8", newline="\n")


def main_run(a):
    from ngspice_shared import NgSpice
    spice = Path(a.spice)
    out_file = spice / "results" / "case_studies.json"
    old = load_results(spice)
    ng = NgSpice(a.ngspice)
    for part in CASES:
        prepared_model(part, spice)
    res = dict(old)
    res["settings"] = dict(C_D_grid_pF=list(CD_GRID_pF), C_F_floor_pF=CF_FLOOR_pF, criteria=CRIT,
                           spot_MHz=[x / 1e6 for x in SPOT_F], tone_MHz=[x / 1e6 for x in TONE_F],
                           tone_fractions={k: v["tone_fractions"] for k, v in CASES.items()}, dr_band_MHz=DR_BAND / 1e6, tone_for_dr_MHz=F0 / 1e6,
                           step_uA=STEP_A * 1e6, step_rise_ps=STEP_RISE * 1e12, nf_instrument_dB=NF_INST_dB)
    for part in a.parts:
        res[part] = run_case(ng, spice, part, a.steps, old.get(part))
        save_results(spice, res)
    print("written", out_file, "and case_studies_curves.json")


# ---------------------------------------------------------------- comparisons (no simulation)
def benchmark_rows(res, part):
    """The design against the 50-ohm benchmark of Section 2.1 (benchmark_50ohm.py's definitions), with the
    simulated band noise (0-150 MHz) and |Z_T| at 100 MHz, and with the analytical model's:
        S_50 = 4 F k_B T / R_0, NF = 2 dB, B = 150 MHz         Eq. (1)
        A    = 20 log10(i_n,B,50 / i_n,B)                       small-signal advantage (Section 2.1)
        P_eq = (R_0/4) I_max^2,  P_x = P_eq + A                  Eq. (5)
    and the photocurrent above which the chain's usable dynamic range (Eq. (28)) exceeds the
    design's, for P_max = -20, -10 and 0 dBm."""
    import benchmark_50ohm as b5
    r = res[part]
    nom = r["nominal"]
    n50 = b5.bench_noise0()
    vpk = r["dr"]["vpk_V"]
    out = {}
    for src, zt, n0 in (("spice", nom["spice"]["zt_100MHz_ohm"], nom["spice"]["noise"]["band_0_150_nA"] * 1e-9),
                        ("model", nom["analytical"]["zt_100MHz_ohm"], nom["analytical"]["noise"]["band_0_150_nA"] * 1e-9)):
        i_max = vpk / (math.sqrt(2) * zt)
        row = dict(i_max_mA_rms=i_max * 1e3, p_eq_dBm=float(b5.dbm(b5.R0 / 4 * i_max ** 2)), per_idc={}, crossover_mA={})
        for i in (0.0, 1e-4, 1e-3, 1e-2):
            nt, nb = b5.noise(n0, i), b5.noise(n50, i)
            row["per_idc"][f"{i * 1e3:g} mA"] = dict(advantage_dB=float(20 * np.log10(nb / nt)),
                                                    p_x_dBm=float(b5.dbm(b5.R0 / 4 * (i_max * nb / nt) ** 2)))
        grid = np.logspace(-6, -1, 5001)
        for p in b5.P_MAX_DBM:
            diff = b5.usable(b5.bench_imax(p), b5.noise(n50, grid), grid) - b5.usable(i_max, b5.noise(n0, grid), grid)
            above = np.nonzero(diff > 0)[0]
            row["crossover_mA"][f"{p:g} dBm"] = float(grid[above[0]] * 1e3) if len(above) else None
        out[src] = row
    return out


def fitted_noise(spice, part, C_D, C_F, R_F, f):
    """Eq. (19) with the e_n, the capacitance its e_n drives and the i_n fitted to the macromodel in
    Section 5.3 (spice/runs/params/<part>_fit.npy, written by spice_tia_checks.py params)."""
    path = spice / "runs" / "params" / f"{part}_fit.npy"
    if not path.exists():
        return None
    fit = np.load(path)
    lf = math.log10(f)
    en, cs, i_n = (float(np.interp(lf, np.log10(fit[0]), fit[k])) for k in (1, 2, 3))
    w = 2 * math.pi * f
    terms = dict(RF=4 * KT / R_F, i_n=i_n ** 2, en_RF=en ** 2 / R_F ** 2,
                 en_C=(en * w * (C_D + C_PCB_NOM + C_F + cs)) ** 2)
    return dict(e_n_nV=en * 1e9, c_model_pF=cs * 1e12, i_n_pA=i_n * 1e12,
                terms_pA2={k: v * 1e24 for k, v in terms.items()}, total_pA=math.sqrt(sum(terms.values())) * 1e12)


# ---------------------------------------------------------------- tables
def fmt(x, d=1, none="–"):
    return none if x is None else f"{x:.{d}f}"


def main_tables(a):
    spice = Path(a.spice)
    res = load_results(spice)
    lines = []
    for part in CASES:
        r = res[part]
        nom = r["nominal"]
        s, m = nom["spice"], nom["analytical"]
        lines.append(f"## {part}, R_F = 2 kOhm, C_F = {r['design']['C_F_pF']:.2f} pF, C_D = 1 pF\n")
        lines.append("| Quantity | Analytical model | SPICE |\n|---|---|---|")
        lines.append(f"| crossover (MHz) | {fmt(m['f_c_MHz'], 0)} | {fmt(s['f_c_MHz'], 0)} |")
        lines.append(f"| phase margin (deg) | {fmt(m['pm_deg'])} | {fmt(s['pm_deg'])} |")
        lines.append(f"| gain margin (dB) | {fmt(m['gm_dB'])} | {fmt(s['gm_dB'])} |")
        lines.append(f"| -3 dB bandwidth (MHz) | {fmt(m['f3_MHz'], 0)} | {fmt(s['f3_MHz'], 0)} |")
        lines.append(f"| peaking (dB) | {fmt(m['peak_dB'], 2)} | {fmt(s['peak_dB'], 2)} |")
        lines.append(f"| abs Z_T at 100 MHz (kOhm) | {fmt(m['zt_100MHz_ohm'] / 1e3, 3)} | {fmt(s['zt_100MHz_ohm'] / 1e3, 3)} |")
        lines.append(f"| step overshoot (%) | {fmt(m['overshoot_pct'], 1)} | {fmt(s['overshoot_pct'], 1)} |")
        lines.append(f"| step rise 10-90 % (ps) | {fmt(m['rise_10_90_ps'], 0)} | {fmt(s['rise_10_90_ps'], 0)} |")
        lines.append(f"| step settling to 1 % (ns) | {fmt(m['settle_1pct_ns'], 2)} | {fmt(s['settle_1pct_ns'], 2)} |")
        for k in m["noise"]["spot_pA"]:
            lines.append(f"| noise at {k} (pA/rtHz) | {fmt(m['noise']['spot_pA'][k], 2)} | {fmt(s['noise']['spot_pA'][k], 2)} |")
        lines.append(f"| penalty 10-150 MHz (dB) | {fmt(m['noise']['penalty_10_150_dB'], 2)} | {fmt(s['noise']['penalty_10_150_dB'], 2)} |")
        lines.append(f"| band noise 0-150 MHz (nA rms) | {fmt(m['noise']['band_0_150_nA'], 1)} | {fmt(s['noise']['band_0_150_nA'], 1)} |")
        lines.append(f"| output noise, unfiltered (mV rms) | – | {fmt(s['noise']['v_out_rms_mV'], 3)} |")
        lines.append(f"| output noise to 150 MHz (mV rms) | – | {fmt(s['noise']['v_out_rms_150MHz_mV'], 3)} |")
        if "dr" in r:
            for k, v in r["dr"]["table"].items():
                lines.append(f"| DR at {k} (dB) | {fmt(v['model_dB'])} | {fmt(v['spice_dB'])} "
                             f"(usable {fmt(v['spice_usable_dB'])}) |")
        lines.append("")
        fe = r["first_estimate"]
        bm = benchmark_rows(res, part)
        for src, row in bm.items():
            lines.append(f"Against the 50-ohm benchmark ({src}): I_max {row['i_max_mA_rms']:.3f} mA rms, P_eq "
                         f"{row['p_eq_dBm']:.1f} dBm; advantage A " + ", ".join(
                             f"{k} {v['advantage_dB']:.2f} dB (P_x {v['p_x_dBm']:.1f} dBm)" for k, v in row["per_idc"].items())
                         + "; benchmark's usable DR larger above " + ", ".join(
                             f"{k}: {'never' if v is None else f'{v:.2f} mA'}" for k, v in row["crossover_mA"].items()))
        fn = fitted_noise(spice, part, C_D_NOM, r["design"]["C_F_pF"] * 1e-12, 2000.0, 100e6)
        if fn:
            lines.append("Eq. (19) at 100 MHz with the macromodel's fitted quantities: " + json.dumps(
                {k: (round(v, 3) if isinstance(v, float) else {kk: round(vv, 3) for kk, vv in v.items()}) for k, v in fn.items()}))
        lines.append("First estimate: " + json.dumps({k: (round(v, 4) if isinstance(v, float) else v)
                                                       for k, v in fe.items() if not isinstance(v, dict)}))
        lines.append("Terms (pA^2/Hz): " + json.dumps({k: round(v, 3) for k, v in fe["terms_pA2"].items()}))
        lines.append("DR_shot: " + json.dumps({k: round(v, 2) for k, v in fe["dr_shot_dB"].items()}) + "\n")
        lines.append("| C_D (pF) | C_T (pF) | NG_inf | f_c (MHz) | PM (deg) | GM (dB) | f3 (MHz) | peak (dB) | "
                     "overshoot (%) | settle (ns) | noise 100 MHz (pA/rtHz) | penalty (dB) | model PM | model f3 | "
                     "model peak | model noise 100 MHz | model penalty |")
        lines.append("|" + "---|" * 17)
        for row in r["cd_sweep"]:
            s, m = row["spice"], row["analytical"]
            lines.append(f"| {row['C_D_pF']:g} | {row['C_T_pF']:.2f} | {row['NG_inf']:.2f} | {fmt(s['f_c_MHz'], 0)} | "
                         f"{fmt(s['pm_deg'])} | {fmt(s['gm_dB'])} | {fmt(s['f3_MHz'], 0)} | {fmt(s['peak_dB'], 2)} | "
                         f"{fmt(s['overshoot_pct'], 1)} | {fmt(s['settle_1pct_ns'], 2)} | {fmt(s['noise']['spot_pA']['100 MHz'], 2)} | "
                         f"{fmt(s['noise']['penalty_10_150_dB'], 2)} | {fmt(m['pm_deg'])} | {fmt(m['f3_MHz'], 0)} | "
                         f"{fmt(m['peak_dB'], 2)} | {fmt(m['noise']['spot_pA']['100 MHz'], 2)} | {fmt(m['noise']['penalty_10_150_dB'], 2)} |")
        lines.append("")
        if "redesign" in r:
            lines.append("| C_D (pF) | SPICE C_F (pF) | meets | f_c | PM | GM | f3 | peak | penalty | model C_F | meets | "
                         "model PM | model f3 | model peak | model penalty |")
            lines.append("|" + "---|" * 15)
            for e in r["redesign"]:
                s, m = e["spice"], e["analytical"]
                lines.append(f"| {e['C_D_pF']:g} | {fmt(s['C_F_pF'], 2)} | {'yes' if s['meets'] else 'no'} | "
                             f"{fmt(s.get('f_c_MHz'), 0)} | {fmt(s.get('pm_deg'))} | {fmt(s.get('gm_dB'))} | "
                             f"{fmt(s.get('f3_MHz'), 0)} | {fmt(s.get('peak_dB'), 2)} | {fmt(s.get('penalty_10_150_dB'), 2)} | "
                             f"{fmt(m['C_F_pF'], 2)} | {'yes' if m['meets'] else 'no'} | {fmt(m.get('pm_deg'))} | "
                             f"{fmt(m.get('f3_MHz'), 0)} | {fmt(m.get('peak_dB'), 2)} | {fmt(m.get('penalty_10_150_dB'), 2)} |")
            lines.append("")
        if "tone" in r:
            lines.append("| tone (MHz) | Eq. (26) (V) | limit | abs Z_T (kOhm) | V at -60 dBc | x | V at -40 dBc | x | "
                         "HD2 at 1.0 x | HD3 at 1.0 x |")
            lines.append("|" + "---|" * 10)
            for k, v in r["tone"].items():
                one = next(x for x in v["sweep"] if abs(x["frac"] - 1.0) < 1e-9)
                lines.append(f"| {k} | {v['claim_V']:.3f} | {v['limit']} | {v['zt_ohm'] / 1e3:.3f} | "
                             f"{fmt(v['v_at_thd_m60'], 3)} | {fmt(v['frac_at_thd_m60'], 2)} | {fmt(v['v_at_thd_m40'], 3)} | "
                             f"{fmt(v['frac_at_thd_m40'], 2)} | {one['hd2_dBc']:.1f} | {one['hd3_dBc']:.1f} |")
            lines.append("")
    text = "\n".join(lines)
    out = Path(a.out) if a.out else HERE.parent / "data" / "results" / "case_studies_tables.md"
    out.write_text("# Tables of the two design examples (generated by scripts_archive/case_studies.py)\n\n" + text,
                   encoding="utf-8", newline="\n")
    print(text)
    print("written", out)


def note_tables(res):
    """Tables A4.1-A4.4 of the note, in its Markdown format, from the saved results."""
    f1, f2 = (lambda x: fmt(x, 1)), (lambda x: fmt(x, 2))
    a, b = res["OPA855"], res["OPA846"]
    L = ["### A4. Tables of Chapter 4: Two design examples: OPA855 and OPA846 at 2 kΩ", ""]
    L.append("*Table A4.1. The two designs at $C_D$ = 1 pF in our analytical model (datasheet open-loop curve, "
             "central noise estimate) and in SPICE with the vendors' macromodels. The dynamic range is Eq. (27) in "
             "150 MHz for a 100-MHz tone, with the amplitude of Eq. (26), 1.525 V for OPA855 and 0.995 V for OPA846, "
             "and the transimpedance at 100 MHz of the same column; the usable figure is Eq. (28); the last row uses "
             "the amplitude at which the OPA846 macromodel's THD reaches −40 dBc at 100 MHz, 0.66 V. Amplifiers: "
             "OPA855 ($C_F$ = 0.20 pF) and OPA846 ($C_F$ = 0.75 pF), $R_F$ = 2 kΩ.*")
    L.append("")
    L.append("| Quantity | OPA855, model | OPA855, SPICE | OPA846, model | OPA846, SPICE |")
    L.append("|---|---|---|---|---|")

    def row(name, get, form):
        vals = []
        for r in (a, b):
            for src in ("analytical", "spice"):
                v = get(r, src)
                vals.append("–" if v is None else form(v))
        L.append(f"| {name} | " + " | ".join(vals) + " |")
    nm = lambda r, s: r["nominal"][s]
    row("Crossover $f_c$ (MHz)", lambda r, s: nm(r, s)["f_c_MHz"], lambda v: f"{v:.0f}")
    row("Phase margin (°)", lambda r, s: nm(r, s)["pm_deg"], f1)
    row("Gain margin (dB)", lambda r, s: nm(r, s)["gm_dB"], f1)
    row("$f_{-3\\,\\mathrm{dB}}$ (MHz)", lambda r, s: nm(r, s)["f3_MHz"], lambda v: f"{v:.0f}")
    row("Peaking (dB)", lambda r, s: nm(r, s)["peak_dB"], f2)
    row("$\\lvert Z_T\\rvert$ at 100 MHz (kΩ)", lambda r, s: nm(r, s)["zt_100MHz_ohm"] / 1e3, lambda v: f"{v:.3f}")
    row("Step: overshoot (%)", lambda r, s: nm(r, s)["overshoot_pct"], f1)
    row("Step: rise, 10–90 % (ps)", lambda r, s: nm(r, s)["rise_10_90_ps"], lambda v: f"{v:.0f}")
    row("Step: settling to 1 % (ns)", lambda r, s: nm(r, s)["settle_1pct_ns"], f2)
    for k in ("10 MHz", "50 MHz", "100 MHz", "150 MHz", "200 MHz"):
        row(f"Noise at {k} (pA/√Hz)", lambda r, s, k=k: nm(r, s)["noise"]["spot_pA"][k], f2)
    row("Penalty over 10–150 MHz (dB)", lambda r, s: nm(r, s)["noise"]["penalty_10_150_dB"], f2)
    row("Band noise, 0–150 MHz (nA rms)", lambda r, s: nm(r, s)["noise"]["band_0_150_nA"], f1)
    row("Output noise, unfiltered (mV rms)", lambda r, s: None if s != "spice" else nm(r, s)["noise"]["v_out_rms_mV"],
        lambda v: f"{v:.3f}")
    row("Output noise to 150 MHz (mV rms)", lambda r, s: None if s != "spice" else nm(r, s)["noise"]["v_out_rms_150MHz_mV"],
        lambda v: f"{v:.3f}")
    for i in ("0 mA", "0.1 mA", "1 mA", "10 mA", "20 mA"):
        row(f"Dynamic range at {i} (dB)",
            lambda r, s, i=i: r["dr"]["table"][i]["model_dB" if s == "analytical" else "spice_dB"], f1)
    row("Usable dynamic range at 0.1 mA (dB)",
        lambda r, s: r["dr"]["table"]["0.1 mA"]["model_usable_dB" if s == "analytical" else "spice_usable_dB"], f1)
    vals = ["–", "–", "–", "–"]
    m40 = b["dr"].get("at_thd", {}).get("m40")
    if m40:
        vals[3] = " / ".join(f"{m40['table'][i]:.1f}" for i in ("0 mA", "0.1 mA", "1 mA", "10 mA"))
    L.append("| Dynamic range at 0 / 0.1 / 1 / 10 mA with the −40-dBc amplitude (dB) | " + " | ".join(vals) + " |")
    L.append("")

    L.append("*Table A4.2. The two designs against the photodiode capacitance with $C_F$ fixed at the design value: "
             "SPICE, with our analytical model in brackets. $C_T$ and $NG_\\infty = 1 + C_T/C_F$ use the datasheets' "
             "input capacitances (OPA855 0.8 pF, OPA846 3.8 pF); the macromodels contain 0.80 and 3.07 pF. The noise "
             "is without photocurrent. Amplifiers: OPA855 ($C_F$ = 0.20 pF) and OPA846 ($C_F$ = 0.75 pF), "
             "$R_F$ = 2 kΩ.*")
    L.append("")
    L.append("| Part | $C_D$ (pF) | $C_T$ (pF) | $NG_\\infty$ | $f_c$ (MHz) | Phase margin (°) | Gain margin (dB) | "
             "$f_{-3\\,\\mathrm{dB}}$ (MHz) | Peaking (dB) | Overshoot (%) | Noise at 100 MHz (pA/√Hz) | "
             "Penalty, 10–150 MHz (dB) |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for part, r in (("OPA855", a), ("OPA846", b)):
        for x in r["cd_sweep"]:
            s, m = x["spice"], x["analytical"]
            L.append(f"| {part} | {x['C_D_pF']:g} | {x['C_T_pF']:.2f} | {x['NG_inf']:.2f} | {s['f_c_MHz']:.0f} | "
                     f"{s['pm_deg']:.1f} ({m['pm_deg']:.1f}) | {f1(s['gm_dB'])} | {s['f3_MHz']:.0f} ({m['f3_MHz']:.0f}) | "
                     f"{s['peak_dB']:.2f} ({m['peak_dB']:.2f}) | {s['overshoot_pct']:.1f} ({m['overshoot_pct']:.1f}) | "
                     f"{s['noise']['spot_pA']['100 MHz']:.2f} ({m['noise']['spot_pA']['100 MHz']:.2f}) | "
                     f"{s['noise']['penalty_10_150_dB']:.2f} ({m['noise']['penalty_10_150_dB']:.2f}) |")
    L.append("")

    L.append("*Table A4.3. Total $C_F$ chosen anew at each photodiode capacitance: the widest bandwidth with a phase "
             "margin of at least 45°, a gain margin of at least 3 dB and at most 1 dB of peaking at that $C_D$, never "
             "below the 0.20-pF parasitic floor. Where no $C_F$ of the grid meets all three (\"no\"), the one with the "
             "smallest shortfall, $(45 - \\phi_M)^+/45 + (3 - \\mathrm{GM})^+/3 + (\\mathrm{peaking} - 1)^+/1$, is given. "
             "SPICE scans 0.10–0.60 pF in 0.02-pF steps for OPA855 and 0.30–2.00 pF in 0.05-pF steps for OPA846; our "
             "analytical model is scanned on the same grid without the gain-margin criterion, which it does not give "
             "reliably (Section 5.3). Amplifiers: OPA855 and OPA846, $R_F$ = 2 kΩ.*")
    L.append("")
    L.append("| Part | $C_D$ (pF) | $C_F$, SPICE (pF) | Meets | Phase margin (°) | Gain margin (dB) | "
             "$f_{-3\\,\\mathrm{dB}}$ (MHz) | Peaking (dB) | Penalty (dB) | $C_F$, model (pF) | Meets | "
             "Phase margin, model (°) | $f_{-3\\,\\mathrm{dB}}$, model (MHz) |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for part, r in (("OPA855", a), ("OPA846", b)):
        for e in r["redesign"]:
            s, m = e["spice"], e["analytical"]
            L.append(f"| {part} | {e['C_D_pF']:g} | {s['C_F_pF']:.2f} | {'yes' if s['meets'] else 'no'} | "
                     f"{f1(s.get('pm_deg'))} | {f1(s.get('gm_dB'))} | {fmt(s.get('f3_MHz'), 0)} | {f2(s.get('peak_dB'))} | "
                     f"{f2(s.get('penalty_10_150_dB'))} | {m['C_F_pF']:.2f} | {'yes' if m['meets'] else 'no'} | "
                     f"{f1(m.get('pm_deg'))} | {fmt(m.get('f3_MHz'), 0)} |")
    L.append("")

    L.append("*Table A4.4. Large-signal limits in the macromodels: the amplitude of Eq. (26) from the datasheet's swing "
             "and slew rate, and the output amplitudes at which the THD of harmonics 2–5 (Eq. (48)) reaches −60 and "
             "−40 dBc, with their fraction of Eq. (26) in brackets, and the second and third harmonics at the amplitude "
             "of Eq. (26). The amplitude is stepped by 0.1 from 0.5 to 1.3 times Eq. (26), and for OPA846 also at 0.05, "
             "0.1, 0.15, 0.2, 0.3 and 0.4 times; where the THD does not cross a level within that range, the bound is "
             "given. 1-MΩ load, OPA855 on ±2.5 V, OPA846 on ±6 V. Amplifiers: OPA855 ($C_F$ = 0.20 pF) and OPA846 "
             "($C_F$ = 0.75 pF), $R_F$ = 2 kΩ, $C_D$ = 1 pF.*")
    L.append("")
    L.append("| Part | Tone | Amplitude of Eq. (26) | Set by | SPICE: amplitude at THD = −60 dBc | at THD = −40 dBc | "
             "At the amplitude of Eq. (26): HD2, HD3 |")
    L.append("|---|---|---|---|---|---|---|")

    def level(v, key, lev):
        x = v[f"v_at_thd_{key}"]
        if x is not None:
            return f"{x:#.3g} V ({v[f'frac_at_thd_{key}']:.2f} ×)"
        sw = v["sweep"]
        if sw[0]["thd_dBc"] >= lev:
            return f"below {sw[0]['frac'] * v['claim_V']:#.3g} V ({sw[0]['frac']:g} ×)"
        return f"above {sw[-1]['frac'] * v['claim_V']:#.3g} V ({sw[-1]['frac']:g} ×)"
    neg = lambda x: f"{x:.1f}".replace("-", "−")
    for part, r in (("OPA855", a), ("OPA846", b)):
        for k, v in r["tone"].items():
            one = next(x for x in v["sweep"] if abs(x["frac"] - 1.0) < 1e-9)
            L.append(f"| {part} | {k} | {v['claim_V']:.3f} V | {v['limit']} | {level(v, 'm60', -60)} | "
                     f"{level(v, 'm40', -40)} | {neg(one['hd2_dBc'])}, {neg(one['hd3_dBc'])} dBc |")
    L.append("")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("action", choices=("run", "tables", "notetables"))
    ap.add_argument("--ngspice", default=None, help="path of the ngspice shared library")
    ap.add_argument("--spice", default=str(HERE.parent / "spice"), help="spice folder (models/, runs/, results/)")
    ap.add_argument("--parts", nargs="+", default=list(CASES), choices=list(CASES))
    ap.add_argument("--steps", nargs="+", default=["nominal", "cd", "cf", "tone"],
                    choices=["nominal", "cd", "cf", "tone"])
    ap.add_argument("--out", default=None, help="markdown file for 'tables'")
    a = ap.parse_args()
    if a.action == "run":
        main_run(a)
    elif a.action == "tables":
        main_tables(a)
    else:
        out = Path(a.out) if a.out else HERE.parent / "data" / "results" / "case_studies_note_tables.md"
        out.write_text(note_tables(load_results(Path(a.spice))), encoding="utf-8", newline="\n")
        print("written", out)


if __name__ == "__main__":
    main()
