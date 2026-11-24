"""Impulse and pulse response of a photodiode TIA, linear and with the amplifier's slew-rate and swing limits
(Section 4.11.8 of the note, Eqs. (36p)-(36v), Figure 13 and Table 4.8).

Usage:
    python tia_pulse_response.py --part OPA846 --rf 1500 --ct 6.0 --cf 0.368 [options]
    python tia_pulse_response.py --aol-spice AOL_TXT --sr 625 --rf 1500 --ct 7.43 --cf 0.318 [options]
    python tia_pulse_response.py --aol-table CSV --sr 625 --rf 1500 --ct 5 --cf 0.5 [options]
    python tia_pulse_response.py --note [--figure [OUT_STEM]] [--from-json RESULTS_JSON]

The open-loop gain
    --part NAME        the amplifier's datasheet open-loop curve as the note digitized it (case_studies.Analytic),
                       with its datasheet slew rate (parts_db) unless --sr is given
    --aol-spice PATH   or an inverting-input open-loop run of spice_tia_checks.py aol, A_- = -v(out)/v(inm)
    --aol-table CSV    or a table with the columns f_Hz, gain_dB, phase_deg (phase of A itself, -90 deg above the
                       dominant pole)
    --zeros N, --poles N   the rational model fitted to it for the time-domain run (default 1 and 3; see below)
The circuit
    --rf OHM, --ct PF, --cf PF   feedback resistor, total node capacitance C_T (photodiodes, board and the amplifier's
                       own input capacitance) and total feedback capacitance C_F
    --sr V_PER_US      slew rate, used as the steepest slope of the input stage (its plateau) unless --sr-test is given
    --sr-test GAIN STEP   or the datasheet's slew-rate test: a non-inverting gain GAIN (R_G = 50 ohm) and an output
                       step of STEP volts, in which the model's 10-90 % average slope is made equal to --sr (the
                       internal slew rate is calibrated, as --note does with OPA846's 10 and 2 V)
    --swing V          the symmetric output swing (default 3.4 V: OPA846 on +/-5 V, >= 400 ohm, p. 3); --vdiff-max V
                       the absolute maximum differential input (default 1.2 V, OPA846 p. 2), only reported
The pulses
    --vlin LIST        sizes as the peak a linear TIA would reach, in V (default 0.01,0.1,0.3,1,3)
    --charges LIST     or as charges in pC (1 pC is 1 pJ of light at a responsivity of 1 A/W)
    --pulse SHAPE      delta (default) | gauss:FWHM_PS | rect:WIDTH_NS | doublet:SEP_PS (+Q, then -Q SEP_PS later:
                       two photodiodes of a balanced pair whose pulses arrive at different times)
    --chain KIND       none | rc | rc2 | rc1, the chain of Eq. (36i) to the oscilloscope (compare_opa846_1k5_board.py);
                       its output is reported beside the TIA's
    --window NS, --dt PS   simulated time (default 150 ns) and RK4 step (default 2 ps)
    --json PATH        write every number and the waveforms
--note runs the cases of Section 4.11.8 (the measured OPA846 board and the second board with 0.55 pF added, in the
datasheet-curve and the macromodel descriptions, at 14 pulse sizes, with the internal slew rate calibrated in the
datasheet's test; and on the board the slew rate calibrated to the datasheet's minimum, 625 V/us taken as the
steepest slope, twice the calibrated value, a Gaussian pulse of 50 ps and a balanced pair's doublet), writes
../data/results/tia_pulse_response_opa846_1k5.json, prints every number of the section and of Tables 4.8 and 4.9
(Tests 1 and 2 of the slew-rate limit), and with --figure draws Figure 13 (../figures/fig37f_opa846_1k5_pulse.png and
.pdf).  The runs take about two minutes; --from-json redraws the figure from a saved results file without running
them.  spice_board_pulses.py checks these runs against the vendor's macromodel in SPICE (Section 4.11.9).

The linear response (Eqs. (36p) and (36q))
    h(t) = (1/2 pi) int Z_T(w) e^{jwt} dw,   v_o(t) = Q h(t) for a charge Q delivered in a time short against the loop,
evaluated as an inverse FFT of Z_T on a uniform grid (spacing 1/window = 2.5 MHz, up to 1/(2 dt_lin) = 50 GHz,
dt_lin = 10 ps), with Z_T from Eqs. (8)-(10); the same for the voltage at the oscilloscope, Z_T H_chain.  Its time
integral is Z_T(0), about -R_F: the output returns to zero, and its area is -R_F Q.  The ringing is read from the
extrema after the peak while they lie between 50 % and 1 % of it: the frequency f_r from their mean spacing, the
decay time from a straight line through log|extremum| against time, and Q_r = pi f_r tau_d.  An interpolated
open-loop curve is not exactly causal, and its inverse transform has a precursor before t = 0, which is printed;
the rational model below has none.

The time-domain model with the large-signal limits (Eqs. (36r)-(36t))
    The amplifier is the usual description of a voltage-feedback part (Section 4.10): a differential input stage
    whose current saturates, i = I_T tanh(v_d/V_ov), charges the compensation capacitance C_c, so that the dominant
    stage obeys C_c dx_1/dt = I_T tanh(v_d/V_ov) - x_1/R_1, with R_1 the resistance that sets the finite DC gain.
    Two datasheet-like numbers fix the stage: its largest slope SR = I_T/C_c (the whole tail current, |v_d| >> V_ov)
    and its unity-gain frequency w_t = 2 pi GBW = g_m/C_c, with g_m = I_T/V_ov the slope of the tanh at the origin.
    Dividing by C_c and using both, I_T/C_c = SR = w_t V_ov, so V_ov = SR/w_t and
        dx_1/dt = 2 pi GBW V_ov tanh(v_d/V_ov) - 2 pi f_p1 x_1,     V_ov = SR/(2 pi GBW),
    which is A_0/(1 + s/(2 pi f_p1)) for small signals (tanh u ~ u gives dx_1/dt = w_t v_d - w_1 x_1, and
    A_0 = w_t/w_1) and slews at exactly +/-SR when the stage is overdriven (tanh -> +/-1; w_1 x_1 <= 2 pi f_p1 x 3.7 V,
    about 0.001 V/us, is negligible).  x_1 is held within the swing (the high-impedance node saturates near the
    rails).  A linear network follows,
        H_post(s) = prod_i (1 + s/z_i) / prod_j (1 + s/p_j) x (1 + s tau/N)^-N,   N = 10,
    unity at DC: the higher poles, any zeros, and the excess phase as a delay tau approximated by N equal poles.  The
    output v_o is H_post x_1 clipped to +/-swing.  The summing node, with the photocurrent i(t) flowing into it and
    the non-inverting input at ground (v_d = -v_n), obeys Kirchhoff's law
        (C_T + C_F) dv_n/dt = i(t) - (v_n - v_o)/R_F + C_F dv_o/dt.
    A delta pulse of charge Q is an instantaneous jump of v_n by Q/(C_T + C_F), Eq. (36s): the output cannot move
    within the pulse, so the charge divides over C_T and C_F.  The stage slews from about Q_SR = V_ov (C_T + C_F),
    and Q_max = vdiff_max (C_T + C_F) puts the absolute maximum across the inputs, Eq. (36t).  The equations are
    integrated with a fixed-step fourth-order Runge-Kutta scheme, all pulse sizes at once.
    The rational model (A_0, f_p1, z_i, p_j, tau) is fitted by least squares to the open-loop gain (dB) and phase
    (deg/6) from 1 MHz to 1.2 GHz, with three times the weight from 80 to 700 MHz, around the crossover.  It is
    printed with its error; for a small pulse the time-domain run reproduces the inverse FFT of its own Z_T (the
    'linear check' line), and its Z_T is compared with that of the curve.  Fitted to a measured gain, it is
    refitted to that gain (--note does this for the board), because a phase margin of 13 deg moves by a degree or
    two between descriptions that differ by 1 deg in phase.

Checking the slew-rate limit, and calibrating it (Table 4.9)
    Test 1 (open_loop_slew_check): with a constant v_d = 0.5 V >> V_ov and no feedback the output must ramp at SR;
    the ramp's slope over the middle of its travel is printed with its relative error against SR, and the steepest
    slope, which H_post's lead zero can push above SR on the first edge.
    Test 2 (g10_step_test): the datasheet's own slew-rate test, a non-inverting gain of +10 (453 and 50 ohm) and a
    2-V output step from 20-ps input edges.  There the stage is overdriven only at first: v_d = v_in - v_o/10 falls
    as the output rises, so the average slope from 10 to 90 % of the step is lower than the steepest slope.  The
    datasheet gives one number, 625 V/us (typical), 500 V/us (minimum), without saying between which points it is
    measured; the macromodel, run in that circuit, gives 619 V/us from 10 to 90 % (Table 4.3), so the 10-90 %
    average is taken as the datasheet's definition.  calibrate_sr finds the internal SR (the tanh stage's plateau) at
    which the model's 10-90 % average equals the datasheet's number, and --note uses that internal SR.
    spice_board_pulses.py repeats Test 2 with the macromodel and compares the pulses with it (Section 4.11.9).

What is read off each run: the peak and its time, the compression against the linear peak, the slew-limited peak
in closed form, Eq. (36u), V_pk = SR R_F [sqrt(C_F^2 + 2 Q/(R_F SR)) - C_F] (an upper estimate in the slewing
range), the largest voltage across the inputs, the time during which the input stage delivers more than 90 % of
its tail current, the ringing, the settling to 1 % and 0.1 % of the peak, the largest excursion after 4, 10, 12.5
and 25 ns, and the area divided by Q, which Eq. (36v), int v_o dt = -R_F Q + int v_n dt, says falls short of -R_F
while the stage slews.

What the model leaves out: the input stage's own capacitance changing with its operating point (the input
transistors' capacitance stops loading the node once the pair has switched, and the capacitance at the pair's tail
node first adds to and then takes from the current that charges C_c; Section 4.11.9 measures both in the
macromodel), the protection diodes from each pin to the supplies (OPA846 p. 19; they conduct only beyond the
supplies), any recovery time after the output has clipped, and the photodiode's own response time, which the gauss
and rect shapes can stand in for.  Beyond --vdiff-max the part is outside its absolute maximum rating and the model
is not evidence.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

import tia_model as tm

HERE = Path(__file__).resolve().parent
N_DELAY = 10                # number of equal poles that stand in for the open loop's pure delay, (1 + s tau/N)^-N
SWING_OPA846 = 3.4          # V, +/-5 V and >= 400 ohm (OPA846 p. 3)
VDIFF_MAX_OPA846 = 1.2      # V, absolute maximum differential input (OPA846 p. 2)

# Units throughout: SI (V, A, s, F, ohm, Hz).  Sign convention: the photocurrent i_ph flows INTO the summing node
# (the inverting input), so the TIA's output goes negative for a positive charge, v_o = -R_F Q at DC.


# ---------------------------------------------------------------------------------------------------------------
# the open-loop gain: a rational model for the time domain
# ---------------------------------------------------------------------------------------------------------------
class RationalOpenLoop:
    """A(s) = A0 / (1 + s/w1) * prod(1 + s/z_i) / prod(1 + s/p_j) / (1 + s tau/N)^N (frequencies in Hz).

    The dominant pole w1 (with A0) is the part that the input stage's tanh drives in simulate(); everything after it
    is H_post, which has unity gain at DC.  An interpolated datasheet curve cannot be used in the time domain (its gain
    and phase were digitized separately and are not exactly causal), so it is replaced by this causal fit."""

    def __init__(self, a0, f_p1, zeros=(), poles=(), tau=0.0, n_delay=N_DELAY, note=""):
        self.a0, self.f_p1, self.zeros, self.poles = float(a0), float(f_p1), tuple(zeros), tuple(poles)
        self.tau, self.n_delay, self.note = float(tau), int(n_delay), note

    @property
    def gbw(self):
        # gain-bandwidth product of the dominant pole alone: |A| ~ GBW/f well above f_p1, before the higher poles
        return self.a0 * self.f_p1

    def post(self, f):
        """H_post: everything after the dominant pole, unity at DC."""
        s = 2j * np.pi * np.asarray(f, dtype=float)
        h = np.ones_like(s)
        for z in self.zeros:
            h = h * (1 + s / (2 * np.pi * z))           # each zero: (1 + s/z), a phase lead
        for p in self.poles:
            h = h / (1 + s / (2 * np.pi * p))           # each higher pole: 1/(1 + s/p)
        if self.tau > 0:
            # a delay e^{-s tau} written as N equal poles; its phase is N atan(w tau/N) ~ w tau, its gain falls slowly
            h = h / (1 + s * self.tau / self.n_delay) ** self.n_delay
        return h

    def A(self, f):
        s = 2j * np.pi * np.asarray(f, dtype=float)
        return self.a0 / (1 + s / (2 * np.pi * self.f_p1)) * self.post(f)

    def describe(self):
        return (f"A0 {self.a0:.4g}, f_p1 {self.f_p1 / 1e3:.2f} kHz (GBW {self.gbw / 1e6:.0f} MHz), zeros "
                f"{[round(z / 1e6, 1) for z in self.zeros]} MHz, poles {[round(p / 1e6, 1) for p in self.poles]} MHz, "
                f"delay {self.tau * 1e12:.0f} ps as {self.n_delay} poles")

    def to_dict(self):
        return dict(a0=self.a0, f_p1_Hz=self.f_p1, zeros_Hz=list(self.zeros), poles_Hz=list(self.poles),
                    tau_s=self.tau, n_delay=self.n_delay, gbw_Hz=self.gbw, note=self.note)

    def state_space(self):
        """(A_p, B_p, C_p) of H_post as a cascade of first-order sections, x' = A_p x + B_p u, y = C_p x.

        A section (1 + s/z)/(1 + s/p) is w' = p (u - w), y = (p/z) u + (1 - p/z) w; a pole is w' = p (u - w), y = w.
        The cascade ends in a pole, so y has no direct term."""
        # Check of the section with a zero: Y/U = p/z + (1 - p/z) p/(s + p) = (p s/z + p)/(s + p) = (1 + s/z)/(1 + s/p).
        # Angular frequencies: the higher poles first, then the N delay poles at N/tau rad/s each; the zeros are
        # paired with the first poles.  Every section has unity DC gain, so H_post(0) = 1.
        p_list = [2 * np.pi * p for p in self.poles] + [self.n_delay / self.tau] * (self.n_delay if self.tau > 0 else 0)
        z_list = [2 * np.pi * z for z in self.zeros] + [None] * (len(p_list) - len(self.zeros))
        if not p_list or z_list[-1] is not None:
            raise ValueError("the rational model must have more poles (with the delay) than zeros")
        m = len(p_list)
        a, b = np.zeros((m, m)), np.zeros(m)
        # The input u_k of section k is a linear combination of the section states w and of the cascade's input u:
        # u_k = cu . w + du * u.  Section 1 is driven by u itself (cu = 0, du = 1).
        cu, du = np.zeros(m), 1.0
        for k, (p, z) in enumerate(zip(p_list, z_list)):
            # w_k' = p (u_k - w_k) = p (cu . w + du u) - p w_k   ->  row k of A_p and entry k of B_p
            a[k] += p * cu
            b[k] += p * du
            a[k, k] -= p
            # the output of section k, which drives section k + 1:
            if z is None:
                # a pole: y_k = w_k
                cu, du = np.zeros(m), 0.0
                cu[k] = 1.0
            else:
                # a zero-pole pair: y_k = (p/z) u_k + (1 - p/z) w_k
                cu, du = (p / z) * cu, (p / z) * du
                cu[k] += 1.0 - p / z
        # the last section is a pole, so its output is y = cu . w with du = 0: C_p = cu
        return a, b, cu


def fit_rational(f, g_db, ph_deg, n_zeros=1, n_poles=3, f_lo=1e6, f_hi=1.2e9, band=(80e6, 700e6), note=""):
    """Least-squares fit of RationalOpenLoop to an open-loop gain (dB) and phase (deg); phase residuals count 1/6
    per degree, and the band around the crossover three times.  Returns the model, rms dB and rms deg."""
    f, g_db, ph_deg = (np.asarray(v, dtype=float) for v in (f, g_db, ph_deg))
    a0 = 10 ** (g_db[np.argmin(f)] / 20)                    # DC gain fixed at the lowest-frequency point
    sel = (f >= 3e6) & (f <= 30e6)
    # start value of the GBW: |A| f on the -20 dB/decade part between 3 and 30 MHz
    gbw0 = float(np.median(10 ** (g_db[sel] / 20) * f[sel])) if sel.any() else 1e9
    m = (f >= f_lo) & (f <= f_hi)
    fm, gm, pm = f[m], g_db[m], ph_deg[m]
    w = np.where((fm >= band[0]) & (fm <= band[1]), 3.0, 1.0)   # weight 3 around the TIA's crossover
    ok = ~np.isnan(pm)                                          # points without a phase reading count in gain only

    # the free parameters x: log10 f_p1, log10 of each zero and pole (Hz), and tau in ps
    def unpack(x):
        return RationalOpenLoop(a0, 10 ** x[0], [10 ** v for v in x[1:1 + n_zeros]],
                                [10 ** v for v in x[1 + n_zeros:1 + n_zeros + n_poles]], x[-1] * 1e-12, note=note)

    def resid(x):
        a = unpack(x).A(fm)
        rg = (20 * np.log10(np.abs(a)) - gm) * w                 # gain error in dB
        php = np.degrees(np.unwrap(np.angle(a)))
        return np.concatenate([rg, (php[ok] - pm[ok]) / 6.0 * w[ok]])   # 6 degrees weigh as much as 1 dB

    best = None
    z0 = [300e6, 600e6, 1000e6][:n_zeros]
    p0 = [800e6, 1500e6, 3000e6, 5000e6, 8000e6][:n_poles]
    for tau0 in (100.0, 250.0, 400.0):                           # three starts of the delay; the best cost is kept
        x0 = [math.log10(gbw0 / a0)] + [math.log10(v) for v in z0] + [math.log10(v) for v in p0] + [tau0]
        lb = [x0[0] - 1] + [7.5] * n_zeros + [7.5] * n_poles + [0.0]
        ub = [x0[0] + 1] + [10.5] * n_zeros + [11.0] * n_poles + [800.0]
        sol = least_squares(resid, x0, bounds=(lb, ub))
        if best is None or sol.cost < best.cost:
            best = sol
    r = unpack(best.x)
    a = r.A(fm)
    eg = 20 * np.log10(np.abs(a)) - gm
    ep = np.degrees(np.unwrap(np.angle(a)))[ok] - pm[ok]
    return r, float(np.sqrt(np.mean(eg ** 2))), float(np.sqrt(np.mean(ep ** 2)))


def spice_open_loop(path):
    """A_- = -v(out)/v(inm) from spice_tia_checks.py aol (columns f, re/im out, re/im inm), as an InterpOpenLoop."""
    d = np.loadtxt(path, skiprows=1)
    f = d[:, 0]
    a = -(d[:, 1] + 1j * d[:, 2]) / (d[:, 3] + 1j * d[:, 4])    # the gain from the inverting input, sign removed
    ph = np.degrees(np.unwrap(np.angle(a)))
    ph -= 360.0 * np.round((ph[np.argmin(abs(f - 10e6))] + 90.0) / 360.0)   # the branch with -90 deg at 10 MHz
    return tm.InterpOpenLoop.from_points([(fi, 20 * math.log10(abs(ai)), pi) for fi, ai, pi in zip(f, a, ph)],
                                         note=f"SPICE A_- from {Path(path).name}")


def table_open_loop(path):
    d = np.loadtxt(path, delimiter=",", skiprows=1)
    return tm.InterpOpenLoop.from_points([(r[0], r[1], r[2]) for r in d], note=f"table {Path(path).name}")


# ---------------------------------------------------------------------------------------------------------------
# the chain to the oscilloscope, Eq. (36i), with phase
# ---------------------------------------------------------------------------------------------------------------
def chain_complex(f, kind, r_s=50.0, c_in=14e-12, f_scope=200e6):
    # V_scope/V_out of Eq. (36i) without the cable's pure delay: the 50-ohm source into the oscilloscope's C_in,
    # optionally followed by a first- or second-order (Butterworth) front end at f_scope
    f = np.asarray(f, dtype=float)
    if kind == "none":
        return np.ones_like(f, dtype=complex)
    s = 2j * np.pi * f
    h = 1.0 / (1.0 + s * r_s * c_in)
    wc = 2 * np.pi * f_scope
    if kind == "rc1":
        h = h / (1 + s / wc)
    elif kind == "rc2":
        h = h / (1 + math.sqrt(2) * s / wc + (s / wc) ** 2)
    return h


def apply_chain(t, v, kind):
    """The chain applied to a waveform sampled uniformly from t = 0 (zero-padded FFT; the pulse decays within it)."""
    if kind == "none":
        return v.copy()
    n = len(t)
    dt = t[1] - t[0]
    nn = 2 * n                                  # zero padding to twice the length: no wrap-around of the response
    spec = np.fft.rfft(v, nn) * chain_complex(np.fft.rfftfreq(nn, dt), kind)
    return np.fft.irfft(spec, nn)[:n]


# ---------------------------------------------------------------------------------------------------------------
# the linear response
# ---------------------------------------------------------------------------------------------------------------
def linear_impulse(ol, rf, ct, cf, window=400e-9, dt=10e-12, chain="none"):
    """h(t) of Eq. (36p) in V per coulomb at the TIA output, and at the oscilloscope through the chain."""
    # Discrete inverse transform: with n samples of step dt, the frequency grid is k/(n dt) and
    #   h(t_j) = integral Z_T(f) e^{j 2 pi f t_j} df  ~  sum_k Z_T(f_k) e^{j 2 pi k j/n} / (n dt) = irfft(Z_T) / dt,
    # since numpy's irfft already divides by n.  A delta of charge Q then gives v_o(t) = Q h(t).
    n = int(round(window / dt))
    f = np.fft.rfftfreq(n, dt)
    f[0] = 1e-3                                 # Z_T at f = 0 from a point just above it (the models take log f)
    zt = tm.tia_tf(f, ol, rf, ct, cf)[0]         # Eqs. (8)-(10): Z_T = -Z_F T/(1 + T)
    t = np.arange(n) * dt
    h = np.fft.irfft(zt, n) / dt
    hs = np.fft.irfft(zt * chain_complex(f, chain), n) / dt
    return t, h, hs


# ---------------------------------------------------------------------------------------------------------------
# the time-domain model
# ---------------------------------------------------------------------------------------------------------------
def simulate(rol, rf, ct, cf, sr, swing, charges, pulse="delta", window=150e-9, dt=2e-12, keep_every=5,
             clamp_margin=0.3):
    """Integrate Eqs. (36r)-(36t) for all charges at once; returns t and v_o, v_n, x_1 sampled every keep_every steps.

    The slew-rate limit.  The input stage is a differential pair whose output current saturates at its tail
    current: i = I_T tanh(v_d/V_ov).  It charges the compensation capacitance C_c, so the dominant stage's output
    x_1 obeys C_c dx_1/dt = I_T tanh(v_d/V_ov) - (leak that sets the finite DC gain).  Dividing by C_c and naming
        SR = I_T/C_c  (the largest |dx_1/dt|, reached when |v_d| >> V_ov, tanh -> +/-1),
        w_t = 2 pi GBW = g_m/C_c with g_m = I_T/V_ov  (the slope of the tanh at the origin, d i/d v_d = I_T/V_ov),
    gives dx_1/dt = SR tanh(v_d/V_ov) - w_1 x_1, and the two names fix V_ov = I_T/g_m = SR/w_t.  So
        dx_1/dt = w_t V_ov tanh(v_d/V_ov) - w_1 x_1,
    which is exactly what deriv() computes below.  For |v_d| << V_ov, tanh(u) ~ u and dx_1/dt = w_t v_d - w_1 x_1,
    i.e. X_1(s) = w_t/(s + w_1) V_d(s) = A0/(1 + s/w_1) V_d(s): the small-signal dominant pole, unchanged.  For
    |v_d| >> V_ov, |dx_1/dt| -> SR - w_1 x_1, and w_1 x_1 is at most 2 pi f_p1 x 3.7 V ~ 0.001 V/us, so x_1
    slews at SR.  H_post has unity DC gain, so a ramp of x_1 at SR leaves H_post, after its own transient, as a
    ramp of v_o at the same SR; on a fast edge a lead zero in H_post can make the instantaneous dv_o/dt exceed SR.
    """
    q = np.asarray(charges, dtype=float)          # one column per pulse size; every state below is a row vector
    na = len(q)
    a_p, b_p, c_p = rol.state_space()             # H_post as x' = A_p x + B_p x_1, v_o = C_p x (before the clip)
    m = len(b_p)
    w1, wt = 2 * np.pi * rol.f_p1, 2 * np.pi * rol.gbw     # dominant pole and unity-gain frequency, rad/s
    v_ov = sr / wt                                # the overdrive voltage of the tanh: V_ov = SR/(2 pi GBW)
    c_sum = ct + cf                               # the capacitance the summing node sees with the output held
    clamp = swing + clamp_margin                  # the high-impedance node x_1 saturates a little beyond the swing
    kind, par = (pulse.split(":") + [""])[:2]
    par = float(par) if par else 0.0
    # Delta-like pulses are applied as instantaneous charges: a charge Q delivered faster than anything in the loop
    # raises v_n by Q/(C_T + C_F) (Eq. (36s)), because the output (a voltage source) cannot move in that instant and
    # the charge divides over C_T (to ground) and C_F (to the output).  jumps: step index -> charge per column.
    jumps = {}
    if kind == "delta":
        jumps[0] = q
    elif kind == "doublet":
        jumps[0] = q                               # +Q now, -Q after par picoseconds (a balanced pair's skew)
        jumps[int(round(par * 1e-12 / dt))] = -q
    # Pulses of finite length are a photocurrent i_in(t) in the node equation instead.
    if kind == "gauss":
        sig = par * 1e-12 / (2 * math.sqrt(2 * math.log(2)))   # FWHM -> standard deviation
        t0 = 5 * sig                                           # centre 5 sigma after t = 0, so it starts near zero

        def i_in(t):
            return q * math.exp(-0.5 * ((t - t0) / sig) ** 2) / (sig * math.sqrt(2 * math.pi))   # area = Q
    elif kind == "rect":
        width = par * 1e-9

        def i_in(t):
            return q / width if 0 <= t < width else 0.0 * q                               # area = Q
    else:
        def i_in(t):
            return 0.0 * q

    def deriv(t, vn, x1, w):
        # the right-hand side of Eq. (36r) for state (v_n, x_1, w); returns the derivatives and the clipped output
        vd = -vn                                              # v_d = v_+ - v_- with the non-inverting input at ground
        dx1 = wt * v_ov * np.tanh(vd / v_ov) - w1 * x1        # dominant stage: slews at w_t V_ov = SR
        dw = a_p @ w + np.outer(b_p, x1)                      # H_post driven by x_1
        y = c_p @ w                                           # H_post's output before the swing limit
        dy = c_p @ dw                                         # its slope (no direct term: the cascade ends in a pole)
        vo = np.clip(y, -swing, swing)                        # output swing limit
        # while the output sits at the limit and would go further, it does not move
        dvo = np.where(((y >= swing) & (dy > 0)) | ((y <= -swing) & (dy < 0)), 0.0, dy)
        # Kirchhoff at the summing node: i_in + (v_o - v_n)/R_F + C_F d(v_o - v_n)/dt - C_T dv_n/dt = 0
        dvn = (i_in(t) - (vn - vo) / rf + cf * dvo) / c_sum
        return dvn, dx1, dw, vo

    nsteps = int(round(window / dt))
    vn, x1, w = np.zeros(na), np.zeros(na), np.zeros((m, na))   # start at rest: the TIA's DC offsets are left out
    out_t, out_vo, out_vn, out_x1 = [], [], [], []
    for k in range(nsteps + 1):
        if k in jumps:
            vn = vn + jumps[k] / c_sum                         # Eq. (36s)
        t = k * dt
        if k % keep_every == 0:                                # record before the step
            y = c_p @ w
            out_t.append(t)
            out_vo.append(np.clip(y, -swing, swing))
            out_vn.append(vn.copy())
            out_x1.append(x1.copy())
        if k == nsteps:
            break
        # classical fourth-order Runge-Kutta step for all pulse sizes at once
        k1 = deriv(t, vn, x1, w)
        k2 = deriv(t + dt / 2, vn + dt / 2 * k1[0], x1 + dt / 2 * k1[1], w + dt / 2 * k1[2])
        k3 = deriv(t + dt / 2, vn + dt / 2 * k2[0], x1 + dt / 2 * k2[1], w + dt / 2 * k2[2])
        k4 = deriv(t + dt, vn + dt * k3[0], x1 + dt * k3[1], w + dt * k3[2])
        vn = vn + dt / 6 * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0])
        # the high-impedance node saturates: x_1 is held within +/-clamp after each step (no wind-up)
        x1 = np.clip(x1 + dt / 6 * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1]), -clamp, clamp)
        w = w + dt / 6 * (k1[2] + 2 * k2[2] + 2 * k3[2] + k4[2])
    return (np.array(out_t), np.array(out_vo).T, np.array(out_vn).T, np.array(out_x1).T, v_ov)


# ---------------------------------------------------------------------------------------------------------------
# what is read off a response
# ---------------------------------------------------------------------------------------------------------------
def response_metrics(t, v, q=None, t_max=None):
    """Peak, ringing frequency and decay, settling and slope of one pulse response (v in V, t in s).

    The ringing is read from the extrema after the peak while they lie between 50 % and 1 % of it: its frequency
    from their mean spacing (half a period), its decay time tau from a straight line through log|extremum| against
    time, and Q = pi f tau.  Only t <= t_max is used (an inverse FFT wraps its precursor round to the window's end)."""
    if t_max is not None:
        keep = t <= t_max
        t, v = t[keep], v[keep]
    i_pk = int(np.argmax(np.abs(v)))                   # the largest excursion, of either sign
    v_pk = float(v[i_pk])
    a = np.abs(v)
    above1 = np.where(a > 0.01 * abs(v_pk))[0]          # samples still above 1 % (0.1 %) of the peak; the last one
    above01 = np.where(a > 0.001 * abs(v_pk))[0]        # is the settling time
    dv = np.diff(v)
    ext = np.where(np.sign(dv[1:]) != np.sign(dv[:-1]))[0] + 1           # local extrema
    last = above1[-1] if len(above1) else len(v) - 1
    # extrema after the peak, below half of it and before the response settles to 1 %, alternating in sign
    ext = ext[(ext > i_pk) & (ext <= last) & (a[ext] < 0.5 * abs(v_pk))]
    ext = np.array([e for k, e in enumerate(ext) if k == 0 or np.sign(v[e]) != np.sign(v[ext[k - 1]])], dtype=int)
    f_r = tau = q_r = float("nan")
    if len(ext) >= 4:
        te, ve = t[ext], a[ext]
        f_r = 1.0 / (2.0 * float(np.mean(np.diff(te))))   # successive extrema are half a period apart
        slope = np.polyfit(te, np.log(ve), 1)[0]          # envelope ~ exp(-t/tau): log|v| falls linearly in t
        tau = -1.0 / slope if slope < 0 else float("nan")
        q_r = math.pi * f_r * tau                         # Eq. (36q)
    first_opp = np.where(np.sign(v[i_pk:]) == -np.sign(v_pk))[0]
    undershoot = float(np.max(np.abs(v[i_pk + first_opp[0]:])) / abs(v_pk)) if len(first_opp) else 0.0
    # the largest excursion after a given time, as a fraction of the peak (what the next pulse of a train finds)
    residual = {f"{tt * 1e9:g} ns": float(np.max(a[t >= tt]) / abs(v_pk)) for tt in (4e-9, 10e-9, 12.5e-9, 25e-9) if tt < t[-1]}
    out = dict(v_peak=v_pk, t_peak=float(t[i_pk]), f_ring=f_r, tau_decay=tau, q_ring=q_r,
               t_settle_1pct=float(t[above1[-1]]) if len(above1) else 0.0,
               t_settle_01pct=float(t[above01[-1]]) if len(above01) else 0.0,
               undershoot_ratio=undershoot, max_slope=float(np.max(np.abs(np.gradient(v, t)))),
               residual_after=residual)
    if q:
        out["area_over_q"] = float(np.trapezoid(v, t) / q)   # Eq. (36v): -R_F in the linear range
    return out


def run_case(label, ol_curve, rol, rf, ct, cf, sr, swing, vlin=None, charges=None, pulse="delta", chain="rc",
             window=150e-9, dt=2e-12, vdiff_max=VDIFF_MAX_OPA846, verbose=True, curve_ctcf=None):
    """Linear and large-signal responses of one design; returns a dict with metrics and waveforms.

    curve_ctcf: (C_T, C_F) at which the curve itself is evaluated, when a measured gain gives the two descriptions
    different capacitances (the default is the same as the rational model's)."""
    res = dict(label=label, rf=rf, ct=ct, cf=cf, sr=sr, swing=swing, pulse=pulse, chain=chain, rational=rol.to_dict(),
               rational_text=rol.describe())
    ct_c, cf_c = curve_ctcf or (ct, cf)
    res["curve_ct"], res["curve_cf"] = ct_c, cf_c
    # loop metrics (Section 3.5) of the interpolated curve and of its rational fit
    for name, ol, c1, c2 in (("curve", ol_curve, ct_c, cf_c), ("rational", rol, ct, cf)):
        if ol is None:
            continue
        m = tm.loop_metrics(ol, rf, c1, c2)
        res[f"loop_{name}"] = {k: (float(v) if isinstance(v, (int, float, np.floating)) else v) for k, v in m.items()}
    # the linear impulse response of the rational model (Eq. (36p)), per pC, at the TIA and at the oscilloscope
    tl, hl, hsl = linear_impulse(rol, rf, ct, cf, chain=chain)
    lin = response_metrics(tl, hl * 1e-12, 1e-12, t_max=200e-9)
    lin_s = response_metrics(tl, hsl * 1e-12, 1e-12, t_max=200e-9)
    res["linear_rational"] = dict(tia=lin, scope=lin_s)
    keep = tl <= 80e-9
    res["linear_waveform"] = dict(t=tl[keep][::2].tolist(), tia_V_per_pC=(hl[keep][::2] * 1e-12).tolist(),
                                  scope_V_per_pC=(hsl[keep][::2] * 1e-12).tolist())
    # the same from the interpolated curve, as a check (it has a precursor before t = 0, measured from the tail)
    if ol_curve is not None:
        tc, hc, hsc = linear_impulse(ol_curve, rf, ct_c, cf_c, chain=chain)
        res["linear_curve"] = dict(tia=response_metrics(tc, hc * 1e-12, 1e-12, t_max=200e-9),
                                   scope=response_metrics(tc, hsc * 1e-12, 1e-12, t_max=200e-9),
                                   precursor=float(np.max(np.abs(hc[tc > 300e-9])) / np.max(np.abs(hc))))
        res["linear_curve_waveform"] = dict(t=tc[tc <= 80e-9][::2].tolist(), tia_V_per_pC=(hc[tc <= 80e-9][::2] * 1e-12).tolist())
    # pulse sizes: given as charges, or as the linear peak they would reach, Q = V_lin / |h|_peak
    h_pk = abs(lin["v_peak"]) / 1e-12                                     # V per coulomb
    if charges is None:
        charges = [v / h_pk for v in (vlin or (0.01, 0.1, 0.3, 1.0, 3.0))]
    charges = [float(c) for c in charges]
    t, vo, vn, x1, v_ov = simulate(rol, rf, ct, cf, sr, swing, charges, pulse=pulse, window=window, dt=dt)
    res["v_ov"] = v_ov
    runs = []
    for k, q in enumerate(charges):
        vs = apply_chain(t, vo[k], chain)                  # the same waveform at the oscilloscope (linear chain)
        mt = response_metrics(t, vo[k], q)
        ms = response_metrics(t, vs, q)
        vd_max = float(np.max(np.abs(vn[k])))              # the largest voltage across the inputs, |v_d| = |v_n|
        dx1 = np.gradient(x1[k], t)
        # time during which the input stage delivers more than 90 % of its tail current (|dx_1/dt| > 0.9 SR)
        slewing = float(np.sum(np.abs(dx1) > 0.9 * sr) * (t[1] - t[0]))
        # Eq. (36u): the output slews at SR until the node is discharged through C_F and R_F
        v_closed = sr * rf * (math.sqrt(cf ** 2 + 2 * q / (rf * sr)) - cf)
        runs.append(dict(q=q, v_lin_peak=q * h_pk * np.sign(lin["v_peak"]), tia=mt, scope=ms, vd_max=vd_max, v_pk_closed_form=v_closed,
                         vd_max_over_vov=vd_max / v_ov, beyond_vdiff_max=vd_max > vdiff_max,
                         node_jump=q / (ct + cf), slew_time=slewing,
                         clipped=bool(np.any(np.abs(vo[k]) >= swing * 0.999)),
                         compression_dB=20 * math.log10(abs(mt["v_peak"]) / (q * h_pk))))
    res["runs"] = runs
    keep = t <= 60e-9
    res["waveforms"] = dict(t=t[keep].tolist(), vo=[v[keep].tolist() for v in vo],
                            vscope=[apply_chain(t, v, chain)[keep].tolist() for v in vo])
    if verbose:
        report(res)
    return res


def report(res):
    lc = res.get("loop_curve") or {}
    lr = res["loop_rational"]
    print(f"\n=== {res['label']}: R_F {res['rf']:.0f} ohm, C_T {res['ct'] * 1e12:.3f} pF, C_F {res['cf'] * 1e12:.3f} pF, "
          f"SR {res['sr'] / 1e6:.0f} V/us, swing {res['swing']:.2f} V, V_ov {res['v_ov'] * 1e3:.1f} mV, pulse {res['pulse']}")
    print(f"  rational open loop: {res['rational_text']}")
    if lc:
        print(f"  loop, curve (C_T {res['curve_ct'] * 1e12:.3f} pF, C_F {res['curve_cf'] * 1e12:.3f} pF): f_c {lc['f_c'] / 1e6:.1f} MHz, PM {lc['pm_deg']:.2f} deg, GM {lc['gm_dB']:.1f} dB, peaking {lc['peaking_dB']:+.2f} dB "
              f"at {lc['f_peak'] / 1e6:.0f} MHz, f_3dB {lc['f_3dB'] / 1e6:.0f} MHz")
    print(f"  loop, rational: f_c {lr['f_c'] / 1e6:.1f} MHz, PM {lr['pm_deg']:.2f} deg, GM {lr['gm_dB']:.1f} dB, peaking {lr['peaking_dB']:+.2f} dB "
          f"at {lr['f_peak'] / 1e6:.0f} MHz, f_3dB {lr['f_3dB'] / 1e6:.0f} MHz")
    for key in ("linear_curve", "linear_rational"):
        if key not in res:
            continue
        for where in ("tia", "scope"):
            m = res[key][where]
            print(f"  {key.replace('linear_', 'linear, ')} at the {where}: peak {m['v_peak']:+.4f} V/pC at {m['t_peak'] * 1e9:.2f} ns, "
                  f"ringing {m['f_ring'] / 1e6:.1f} MHz, decay {m['tau_decay'] * 1e9:.2f} ns (Q {m['q_ring']:.2f}), undershoot "
                  f"{m['undershoot_ratio']:.3f}, 1 % at {m['t_settle_1pct'] * 1e9:.1f} ns, 0.1 % at {m['t_settle_01pct'] * 1e9:.1f} ns, "
                  f"steepest {m['max_slope'] / 1e6:.0f} V/us per pC" + (f", area/Q {m.get('area_over_q', float('nan')):.1f} ohm" if where == "tia" else "")
                  + "; largest excursion after " + ", ".join(f"{k} {100 * v:.2f} %" for k, v in m["residual_after"].items()) + " of the peak")
        if key == "linear_curve":
            print(f"  the curve's inverse transform has a precursor of {100 * res[key]['precursor']:.2f} % of its peak "
                  f"(the digitized gain and phase are not exactly causal)")
    for r in res["runs"]:
        m, s = r["tia"], r["scope"]
        print(f"  Q {r['q'] * 1e12:8.4f} pC (linear peak {r['v_lin_peak']:+.3f} V): node jump {r['node_jump'] * 1e3:7.1f} mV "
              f"({r['node_jump'] / res['v_ov']:.2f} V_ov), max |v_d| {r['vd_max'] * 1e3:7.1f} mV{' BEYOND abs max' if r['beyond_vdiff_max'] else ''}; "
              f"TIA peak {m['v_peak']:+.3f} V at {m['t_peak'] * 1e9:.2f} ns ({r['compression_dB']:+.2f} dB; Eq. (36u) "
              f"{r['v_pk_closed_form']:.3f} V), steepest {m['max_slope'] / 1e6:.0f} V/us "
              f"({m['max_slope'] / res['sr']:.2f} SR), slewing {r['slew_time'] * 1e9:.2f} ns, ringing {m['f_ring'] / 1e6:.1f} MHz, "
              f"decay {m['tau_decay'] * 1e9:.2f} ns, 1 % at {m['t_settle_1pct'] * 1e9:.1f} ns, 0.1 % at {m['t_settle_01pct'] * 1e9:.1f} ns, "
              f"area/Q {m['area_over_q']:.0f} ohm{', CLIPPED' if r['clipped'] else ''}; at the scope peak {s['v_peak']:+.3f} V, "
              f"1 % at {s['t_settle_1pct'] * 1e9:.1f} ns")


def linear_check(rol, rf, ct, cf, sr, swing, dt=2e-12):
    """The time-domain model at a pulse far below any limit against the inverse FFT of its own Z_T."""
    # Two independent computations of the same linear response: the inverse FFT of Z_T built from rol.A(f)
    # (frequency domain), and the Runge-Kutta integration of Eq. (36r) with the same rol (time domain), at a charge so
    # small (1e-4 pC, a node jump of about 16 uV) that the tanh is linear and nothing clips.  Their largest
    # difference, relative to the peak, checks the state-space realisation, the node equation and the integration.
    tl, hl, _ = linear_impulse(rol, rf, ct, cf)
    q = 1e-16
    t, vo, _, _, _ = simulate(rol, rf, ct, cf, sr, swing, [q], window=80e-9, dt=dt, keep_every=5)
    ref = np.interp(t, tl, hl) * q
    err = float(np.max(np.abs(vo[0] - ref)) / np.max(np.abs(ref)))
    return err


# ---------------------------------------------------------------------------------------------------------------
# checks of the slew-rate limit, and its calibration against the datasheet's own test
# ---------------------------------------------------------------------------------------------------------------
def run_amplifier(rol, sr, swing, vd_of, t_end, dt=1e-12, x_init=0.0, clamp_margin=0.3):
    """The amplifier of Eq. (36r) alone, with the feedback supplied by the caller: v_d = vd_of(t, v_o).

    The same equations as simulate() (the tanh stage, H_post and the swing clip), written once more without the
    summing node so that the amplifier can be put into other circuits: a constant v_d (open loop) or the datasheet's
    non-inverting test circuit.  sr may be an array: one column per slew rate.  x_init is the DC output at t = 0, at
    which every state of H_post starts too (each of its sections has unity DC gain).  Returns t and v_o."""
    srv = np.atleast_1d(np.asarray(sr, dtype=float))
    a_p, b_p, c_p = rol.state_space()
    w1, wt = 2 * np.pi * rol.f_p1, 2 * np.pi * rol.gbw
    v_ov = srv / wt                                   # one overdrive voltage per column, V_ov = SR/(2 pi GBW)
    clamp = swing + clamp_margin
    x1 = np.full(len(srv), float(x_init))
    w = np.full((len(b_p), len(srv)), float(x_init))

    def deriv(t, x1, w):
        y = c_p @ w
        vo = np.clip(y, -swing, swing)
        vd = vd_of(t, vo)
        dx1 = wt * v_ov * np.tanh(vd / v_ov) - w1 * x1          # the same line as in simulate()
        dw = a_p @ w + np.outer(b_p, x1)
        return dx1, dw

    n = int(round(t_end / dt))
    ts, vos = [], []
    for k in range(n + 1):
        t = k * dt
        ts.append(t)
        vos.append(np.clip(c_p @ w, -swing, swing))
        if k == n:
            break
        k1 = deriv(t, x1, w)
        k2 = deriv(t + dt / 2, x1 + dt / 2 * k1[0], w + dt / 2 * k1[1])
        k3 = deriv(t + dt / 2, x1 + dt / 2 * k2[0], w + dt / 2 * k2[1])
        k4 = deriv(t + dt, x1 + dt * k3[0], w + dt * k3[1])
        x1 = np.clip(x1 + dt / 6 * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0]), -clamp, clamp)
        w = w + dt / 6 * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1])
    return np.array(ts), np.array(vos).T


def open_loop_slew_check(rol, sr, swing=SWING_OPA846, v_d=0.5):
    """Test 1: with a constant v_d >> V_ov and no feedback, the output must ramp at exactly SR once H_post's own
    transient has passed.  Starts at -swing + 0.2 V so that the ramp has room.  Returns the ramp's slope (V/s) over
    the middle of its travel, its relative error against SR, and the steepest slope (the lead zero's overshoot)."""
    t, vo = run_amplifier(rol, [sr], swing, lambda t, vo: v_d, t_end=2 * swing / sr, x_init=-swing + 0.2)
    v = vo[0]
    sel = (v > -swing + 1.0) & (v < swing - 1.0)       # the middle of the travel, away from the start and the clip
    slope = float(np.polyfit(t[sel], v[sel], 1)[0])
    return dict(sr=sr, v_ov=sr / (2 * np.pi * rol.gbw), ramp_slope=slope, rel_error=slope / sr - 1,
                steepest=float(np.max(np.gradient(v, t))))


def g10_step_test(rol, srs, swing=SWING_OPA846, step=2.0, r_f=453.0, r_g=50.0, t0=2e-9, edge=20e-12, t_end=20e-9,
                  return_wave=False):
    """Test 2, the datasheet's slew-rate test (OPA846 p. 3): a non-inverting gain of 1 + R_F/R_G = +10.06 with
    453 and 50 ohm, an output step of `step` volts centred on 0 V, and 20-ps input edges, as in case_opa846_1k5.py's
    SPICE run of the macromodel.  v_d = v_in - beta v_o with beta = R_G/(R_F + R_G).  For every slew rate in srs it
    returns the 10-90 % and 20-80 % average slopes and the steepest slope of the output, in V/s; with return_wave
    also (t, v_o), t counted from the middle of the input edge and v_o centred on 0 V."""
    beta = r_g / (r_f + r_g)
    a = 0.5 * step * beta                               # input amplitude: the output swings about step/2 each way
    a0 = rol.a0
    v_o0 = -a * a0 / (1 + a0 * beta)                    # the DC output before the edge (linear, v_d = v_o/A0)

    def v_in(t):
        return -a + 2 * a * min(max((t - t0) / edge, 0.0), 1.0)

    t, vo = run_amplifier(rol, srs, swing, lambda t, vo: v_in(t) - beta * vo, t_end=t_end, x_init=v_o0)
    out, waves = [], []
    for v in vo:
        v0 = float(np.mean(v[t < t0 - 0.2e-9]))          # before the edge
        v1 = float(np.mean(v[t > t_end - 3e-9]))         # settled
        dv = v1 - v0

        def cross(frac):
            # the first time after the edge at which the output has covered `frac` of the step, interpolated
            k = int(np.where((t > t0) & (v - v0 >= frac * dv))[0][0])
            return float(t[k - 1] + (v0 + frac * dv - v[k - 1]) * (t[k] - t[k - 1]) / (v[k] - v[k - 1]))
        out.append(dict(step=dv, avg_10_90=0.8 * dv / (cross(0.9) - cross(0.1)),
                        avg_20_80=0.6 * dv / (cross(0.8) - cross(0.2)), steepest=float(np.max(np.gradient(v, t)))))
        waves.append(v - (v0 + v1) / 2)
    if return_wave:
        return out, (t - t0 - edge / 2, np.array(waves))
    return out


def calibrate_sr(rol, target=625e6, key="avg_10_90", step=2.0, grid=None, **test):
    """The internal slew rate (the steepest slope of the tanh stage) at which the model's output in the datasheet's
    test circuit has the datasheet's average slope `target`: Test 2 on a grid of internal slew rates from 0.8 to 2.5
    times the target in steps of 1 % of it, interpolated (the average slope rises monotonically with SR).  `test`
    passes the circuit to g10_step_test (r_f, r_g, swing) for a part whose datasheet uses another gain."""
    grid = np.arange(0.8, 2.501, 0.01) * target if grid is None else np.asarray(grid)
    rows = g10_step_test(rol, grid, step=step, **test)
    y = np.array([r[key] for r in rows])
    if not np.all(np.diff(y) > 0) or not y[0] <= target <= y[-1]:
        raise ValueError("Test 2's average slope is not monotonic in SR on the grid, or the target is outside it")
    return float(np.interp(target, y, grid)), [dict(sr=float(s), **r) for s, r in zip(grid, rows)]


# ---------------------------------------------------------------------------------------------------------------
# the cases of the note
# ---------------------------------------------------------------------------------------------------------------
NOTE_VLIN =(0.01, 0.03, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0, 1.5, 2.0, 3.0, 5.0, 7.0, 10.0)   # pulse sizes, as linear peaks (V)
SHOWN_VLIN = (0.01, 0.3, 1.0, 3.0, 10.0)                                                 # those drawn in Figure 13c, d


def compact(out, t_max=30e-9, step=2, lin_t_max=80e-9, lin_step=2, digits=6, shown=SHOWN_VLIN):
    """Keep the results file small: the output waveforms up to t_max at every step-th sample (20 ps), for every run
    of the variants and for the pulse sizes of Figure 13 (`shown`, as linear peaks) of the main cases, the others
    left as null; no oscilloscope copy of them (their metrics stay in 'runs'); the linear responses up to lin_t_max
    at every lin_step-th sample (40 ps), the curve's only as metrics; every number rounded to `digits` significant
    digits."""
    def trim(w, keys, tm, st):
        keep = [i for i, t in enumerate(w["t"]) if t <= tm][::st]
        new = {"t": [w["t"][i] for i in keep]}
        for k in keys:
            if k in w:
                v = w[k]
                new[k] = [[row[i] for i in keep] for row in v] if v and isinstance(v[0], list) else [v[i] for i in keep]
        return new

    def rnd(x):
        if isinstance(x, float):
            return float(f"{x:.{digits}g}")
        if isinstance(x, dict):
            return {k: rnd(v) for k, v in x.items()}
        if isinstance(x, (list, tuple)):
            return [rnd(v) for v in x]
        return x

    for res in out.get("cases", []) + out.get("variants", []):
        if "waveforms" in res:
            res["waveforms"] = trim(res["waveforms"], ("vo",), t_max, step)
        if "linear_waveform" in res:
            res["linear_waveform"] = trim(res["linear_waveform"], ("tia_V_per_pC", "scope_V_per_pC"), lin_t_max, lin_step)
        res.pop("linear_curve_waveform", None)
    for res in out.get("cases", []):
        if "waveforms" in res:
            res["waveforms"]["vo"] = [v if any(abs(abs(r["v_lin_peak"]) - s) < 1e-6 * s for s in shown) else None
                                      for v, r in zip(res["waveforms"]["vo"], res["runs"])]
    return rnd(json.loads(json.dumps(out, default=float)))


def compression_points(res):
    """Charges (and linear peaks) at which the peak output falls 0.1 and 1 dB below the linear one, and at which
    the output's area falls 0.1 and 1 % short of R_F Q; interpolated in log Q between the runs."""
    q = np.array([r["q"] for r in res["runs"]])
    comp = np.array([r["compression_dB"] for r in res["runs"]])                  # peak / linear peak, dB (<= 0)
    area = np.array([abs(r["tia"]["area_over_q"]) / res["rf"] - 1.0 for r in res["runs"]])   # area / (R_F Q) - 1
    out = {}
    for key, y, levels in (("peak_dB", comp, (-0.1, -1.0)), ("area", area, (-1e-3, -1e-2))):
        for lev in levels:
            k = np.where(y <= lev)[0]                 # the first run past the level ...
            if not len(k) or k[0] == 0:
                out[f"{key}_{lev:g}"] = None
                continue
            i = k[0]
            # ... and linear interpolation in log Q between it and the run before
            x0, x1 = math.log10(q[i - 1]), math.log10(q[i])
            xq = x0 + (lev - y[i - 1]) * (x1 - x0) / (y[i] - y[i - 1])
            qq = 10 ** xq
            out[f"{key}_{lev:g}"] = dict(q=qq, v_lin=qq * abs(res["runs"][0]["v_lin_peak"]) / res["runs"][0]["q"])
    return out


def note_cases():
    import case_studies as cs
    import compare_opa846_1k5_board as cb

    an = cs.Analytic("OPA846")                     # the datasheet open-loop curve of our analytical model
    sr_ds, sr_ds_min = 625e6, 500e6                # V/s, the datasheet's typical and minimum slew rate (OPA846 p. 3)
    # the measured gain of the board, the same bins and chain as Section 4.11.4
    b = cb.read_bins(str(HERE.parent / "data" / "measurements" / "opa846_1k5_board_per_MHz.csv"))
    use = (~b["bad"]) & np.isfinite(b["G"]) & (b["f"] >= 10e6)
    f, g = b["f"][use], b["G"][use]
    h = cb.chain(f, "rc")
    # the macromodel's open-loop gain from its inverting input, from the AC run of Chapter 5 (the only SPICE input)
    mac = spice_open_loop(HERE.parent / "spice" / "runs" / "aol" / "OPA846_inverting" / "aol.txt")
    out = dict(cases=[], fits={}, slew_tests={})
    descriptions = (("datasheet curve", an.ol), ("macromodel A_-", mac))
    for name, ol in descriptions:
        # 1. a causal rational form of the open loop
        rol, eg, ep = fit_rational(ol.f, ol.g_db, ol.ph_deg, 1, 3, note=name)
        print(f"{name}: rational fit {rol.describe()}; rms {eg:.2f} dB, {ep:.2f} deg")
        # 1b. the slew-rate limit: Test 1 (open loop, the ramp's slope against SR) and Test 2 (the datasheet's
        # G = +10 circuit), and the internal slew rate at which Test 2 gives the datasheet's 625 V/us (typical) and
        # 500 V/us (minimum) as the 10-90 % average slope
        sr, _ = calibrate_sr(rol, target=sr_ds)
        sr_min, _ = calibrate_sr(rol, target=sr_ds_min)
        t1 = open_loop_slew_check(rol, sr)
        t2 = g10_step_test(rol, [sr_ds, sr, sr_min])
        out["slew_tests"][name] = dict(sr_cal=sr, sr_min_cal=sr_min, test1=t1, test2_625=t2[0], test2_cal=t2[1], test2_min=t2[2])
        print(f"  Test 1 at {sr / 1e6:.1f} V/us: ramp {t1['ramp_slope'] / 1e6:.2f} V/us ({100 * t1['rel_error']:+.4f} %), steepest "
              f"{t1['steepest'] / 1e6:.0f} V/us, V_ov {t1['v_ov'] * 1e3:.1f} mV")
        for lab, r in (("625 V/us as the steepest slope", t2[0]), (f"calibrated {sr / 1e6:.1f} V/us", t2[1]),
                       (f"minimum, calibrated {sr_min / 1e6:.1f} V/us", t2[2])):
            print(f"  Test 2, {lab}: 10-90 % {r['avg_10_90'] / 1e6:.1f}, 20-80 % {r['avg_20_80'] / 1e6:.1f}, steepest "
                  f"{r['steepest'] / 1e6:.1f} V/us")
        # 2. the board's C_T and C_F fitted to the measured gain with the curve (Table 4.4) and with the rational form
        r_curve = cb.fit(f, g, ol, h, True)
        r_rat = cb.fit(f, g, rol, h, True)
        print(f"  the measured gain fitted with the curve: C_T {r_curve['ct'] * 1e12:.3f} pF, C_F {r_curve['cf'] * 1e12:.3f} pF, "
              f"eps {100 * r_curve['eps']:.2f} %, PM {r_curve['m']['pm_deg']:.2f} deg; with the rational model: "
              f"C_T {r_rat['ct'] * 1e12:.3f} pF, C_F {r_rat['cf'] * 1e12:.3f} pF, K {r_rat['k']:.3f}, eps {100 * r_rat['eps']:.2f} %, "
              f"PM {r_rat['m']['pm_deg']:.2f} deg, TIA peak {r_rat['pk']:+.2f} dB at {r_rat['fpk'] / 1e6:.0f} MHz")
        out["fits"][name] = dict(rational=rol.to_dict(), rms_dB=eg, rms_deg=ep, ct_curve=r_curve["ct"], cf_curve=r_curve["cf"],
                                 ct=r_rat["ct"], cf=r_rat["cf"], k=r_rat["k"], eps=r_rat["eps"], pm=r_rat["m"]["pm_deg"])
        # 3. the time-domain model against the inverse FFT of the same Z_T, in its linear range
        print(f"  linear check (time-domain model against the inverse FFT of its own Z_T): "
              f"{100 * linear_check(rol, 1500.0, r_rat['ct'], r_rat['cf'], sr, SWING_OPA846):.3f} % of the peak")
        # 4. the board and the second board (+0.55 pF) at 14 pulse sizes
        for tag, add in (("board", 0.0), ("second board, +0.55 pF", 0.55e-12)):
            res = run_case(f"{tag}, {name}", ol, rol, 1500.0, r_rat["ct"], r_rat["cf"] + add, sr, SWING_OPA846,
                           vlin=NOTE_VLIN, chain="rc", curve_ctcf=(r_curve["ct"], r_curve["cf"] + add))
            res["compression"] = compression_points(res)
            print("  compression: " + "; ".join(
                f"{k} at {v['q'] * 1e12:.3f} pC ({v['v_lin']:.3f} V linear peak)" if v else f"{k} not reached"
                for k, v in res["compression"].items()))
            v_ov, c_sum = res["v_ov"], r_rat["ct"] + r_rat["cf"] + add
            # Eq. (36t): the charges at which the node jump reaches V_ov and the absolute maximum across the inputs
            print(f"  the node jump reaches V_ov ({v_ov * 1e3:.1f} mV) at {v_ov * c_sum * 1e12:.3f} pC and "
                  f"{VDIFF_MAX_OPA846:.1f} V at {VDIFF_MAX_OPA846 * c_sum * 1e12:.2f} pC (C_T + C_F = {c_sum * 1e12:.3f} pF)")
            res.update(description=name, design=tag)
            out["cases"].append(res)
    # slew-rate sensitivity, a finite pulse width and a balanced pair's doublet, on the board (datasheet curve)
    name = descriptions[0][0]
    fr = out["fits"][name]["rational"]
    rol = RationalOpenLoop(fr["a0"], fr["f_p1_Hz"], fr["zeros_Hz"], fr["poles_Hz"], fr["tau_s"], fr["n_delay"], fr["note"])
    ct, cf = out["fits"][name]["ct"], out["fits"][name]["cf"]
    sr, sr_min = out["slew_tests"][name]["sr_cal"], out["slew_tests"][name]["sr_min_cal"]
    extra = []
    for tag, sr_x, pulse, vl in (("SR at the datasheet minimum, calibrated", sr_min, "delta", (0.3, 1.0, 3.0)),
                                 ("SR 625 V/us as the steepest slope", sr_ds, "delta", (0.3, 1.0, 3.0)),
                                 ("SR twice the calibrated value", 2 * sr, "delta", (0.3, 1.0, 3.0)),
                                 ("Gaussian pulse of 50 ps FWHM", sr, "gauss:50", (0.3, 1.0, 3.0)),
                                 ("doublet, -Q 50 ps after +Q", sr, "doublet:50", None)):
        charges = None if vl else [0.3e-12, 1e-12, 3e-12, 7.5e-12]
        res = run_case(f"board, {name}, {tag}", None, rol, 1500.0, ct, cf, sr_x, SWING_OPA846, vlin=vl, charges=charges,
                       pulse=pulse, chain="rc")
        res.update(description=name, design="board", variant=tag)
        if tag.startswith("SR"):
            res.pop("waveforms", None)
        extra.append(res)
    out["variants"] = extra
    return out


def signed(x, nd=2):
    """A signed number for the note's tables: a true minus sign, and no sign on a value that rounds to zero."""
    r = round(x, nd)
    if r == 0:
        return f"{0:.{nd}f}"
    return ("+" if r > 0 else "−") + f"{abs(r):.{nd}f}"


def note_tables(out):
    """The Markdown rows of Table 4.8 (large pulses) and of the model's rows of Table 4.9 (Tests 1 and 2), from the
    results of note_cases(); the macromodel's row of Table 4.9 comes from spice_board_pulses.py report."""
    cases = {(c["description"], c["design"]): c for c in out["cases"]}
    labels = {"datasheet curve": "datasheet curve", "macromodel A_-": "macromodel's $A_-$"}
    print("\nTable 4.8 rows:")
    for desc, design, sizes in (("datasheet curve", "board", (0.1, 0.3, 0.7, 1.0, 2.0, 3.0, 5.0, 10.0)),
                                ("macromodel A_-", "board", (1.0, 3.0, 10.0)),
                                ("datasheet curve", "second board, +0.55 pF", (0.1, 0.3, 1.0, 3.0, 10.0))):
        c = cases[(desc, design)]
        name = ("Board, " if design == "board" else "+0.55 pF, ") + labels[desc]
        for r in c["runs"]:
            v_lin = abs(r["v_lin_peak"])
            if not any(abs(v_lin - s) < 1e-6 * s for s in sizes):
                continue
            m = r["tia"]
            jump = r["node_jump"] * 1e3
            ratio = r["node_jump"] / c["v_ov"]
            jump_txt = (f"{jump:.1f}" if jump < 300 else f"{jump:.0f}") + " mV (" + (f"{ratio:.2f}" if ratio < 10 else f"{ratio:.1f}") \
                + " $V_{ov}$)" + (", beyond the absolute maximum" if r["beyond_vdiff_max"] else "")
            slew = r["slew_time"] * 1e9
            slew_txt = "0" if slew < 0.005 else (f"{slew:.2f} ns" if slew < 10 else f"{slew:.1f} ns")
            short = 100 * (1 - abs(m["area_over_q"]) / c["rf"])
            ring = "none" if not np.isfinite(m["f_ring"]) else f"{m['f_ring'] / 1e6:.1f} MHz"
            q_txt = f"{r['q'] * 1e12:.3f}" if r["q"] < 1e-12 else f"{r['q'] * 1e12:#.3g}"
            print(f"| {name} | {q_txt} pC | " + (f"{v_lin:.2f}" if v_lin < 10 else f"{v_lin:.1f}") + f" V | {jump_txt} | {abs(m['v_peak']):.3f} V, {m['t_peak'] * 1e9:.2f} ns | "
                  f"{-r['compression_dB']:.2f} dB | " + ("–" if v_lin < 1 else f"{r['v_pk_closed_form']:.2f} V") + f" | {slew_txt} | "
                  f"{ring} | {m['t_settle_1pct'] * 1e9:.1f} ns | " + (f"{short:.2f}" if short < 10 else f"{short:.1f}") + " % |")
    print("\nTable 4.9 rows (the model's):")
    for desc in ("datasheet curve", "macromodel A_-"):
        s = out["slew_tests"][desc]
        gbw = out["fits"][desc]["rational"]["gbw_Hz"]
        for key, sr, what in (("test2_625", 625e6, "the datasheet's value"),
                              ("test2_cal", s["sr_cal"], "calibrated to 625 V/µs"),
                              ("test2_min", s["sr_min_cal"], "calibrated to 500 V/µs")):
            r = s[key]
            t1 = s["test1"] if key == "test2_cal" else None
            t1_txt = (f"{t1['ramp_slope'] / 1e6:.2f} V/µs ({signed(100 * t1['rel_error'], 4)} %), steepest {t1['steepest'] / 1e6:.0f} V/µs"
                      if t1 else "–")
            print(f"| Model, {labels[desc]} | {sr / 1e6:.1f} V/µs ({what}) | {sr / (2 * math.pi * gbw) * 1e3:.1f} mV | {t1_txt} | "
                  f"{r['avg_10_90'] / 1e6:.1f} V/µs | {r['avg_20_80'] / 1e6:.1f} V/µs | {r['steepest'] / 1e6:.0f} V/µs |")


def draw(out, stem):
    import matplotlib.pyplot as plt
    from make_case_figures import PANEL, panel_label
    from make_figures import COLORS, DASH, LW, configure_plot_style, export

    configure_plot_style()
    blue, red, grey, green = COLORS["primary"], COLORS["warm_accent"], COLORS["neutral"], COLORS["cool_accent"]
    purple, teal = COLORS["purple_accent"], COLORS["teal_accent"]
    cases = {(c["description"], c["design"]): c for c in out["cases"]}
    ds, mm = "datasheet curve", "macromodel A_-"
    fig, axs = plt.subplots(3, 2, figsize=(2 * PANEL[0], 3 * PANEL[1]), constrained_layout=True)

    # (a) linear impulse responses at the TIA output, per pC
    ax = axs[0, 0]
    for (d, des), col, ls in (((ds, "board"), blue, "-"), ((mm, "board"), red, "-"),
                              ((ds, "second board, +0.55 pF"), blue, DASH), ((mm, "second board, +0.55 pF"), red, DASH)):
        c = cases[(d, des)]
        w = c["linear_waveform"]
        lab = ("board, " if des == "board" else "+0.55 pF, ") + ("datasheet curve" if d == ds else "macromodel's $A_-$")
        ax.plot(np.array(w["t"]) * 1e9, w["tia_V_per_pC"], color=col, ls=ls, lw=LW, label=lab)
    ax.axhline(0, color=COLORS["annotation"], lw=0.6)
    ax.set_xlim(0, 40)
    ax.set_xlabel("Time (ns)")
    ax.set_ylabel("TIA output per charge (V/pC)")
    ax.legend(loc="upper right", fontsize=7.2)
    panel_label(ax, "(a)", x=0.025)

    # (b) the same at the oscilloscope
    ax = axs[0, 1]
    for (d, des), col, ls in (((ds, "board"), blue, "-"), ((mm, "board"), red, "-"),
                              ((ds, "second board, +0.55 pF"), blue, DASH), ((mm, "second board, +0.55 pF"), red, DASH)):
        w = cases[(d, des)]["linear_waveform"]
        ax.plot(np.array(w["t"]) * 1e9, w["scope_V_per_pC"], color=col, ls=ls, lw=LW)
    ax.axhline(0, color=COLORS["annotation"], lw=0.6)
    ax.set_xlim(0, 40)
    ax.set_xlabel("Time (ns)")
    ax.set_ylabel("At the oscilloscope per charge (V/pC)")
    panel_label(ax, "(b)", x=0.025)

    # (c), (d) large pulses, normalized to the charge: the board and the second board, datasheet curve
    cols = [grey, green, purple, red, teal]
    for ax, des, lab in ((axs[1, 0], "board", "(c)"), (axs[1, 1], "second board, +0.55 pF", "(d)")):
        c = cases[(ds, des)]
        w = c["waveforms"]
        t = np.array(w["t"]) * 1e9
        shown = [k for k, r in enumerate(c["runs"]) if any(abs(abs(r["v_lin_peak"]) - v) < 1e-6 * v for v in SHOWN_VLIN)]
        for j, k in enumerate(shown):
            r = c["runs"][k]
            ax.plot(t, np.array(w["vo"][k]) / (r["q"] * 1e12), color=cols[j], lw=LW if j else 2.4,
                    alpha=1.0 if j else 0.45, label=f"{r['q'] * 1e12:.3g} pC ({abs(r['v_lin_peak']):.3g} V linear)")
        ax.axhline(0, color=COLORS["annotation"], lw=0.6)
        ax.set_xlim(0, 25)
        ax.set_xlabel("Time (ns)")
        ax.set_ylabel("TIA output per charge (V/pC)")
        ax.legend(loc="lower right", fontsize=7.0)
        panel_label(ax, lab, x=0.025)

    # (e) peak output against charge
    ax = axs[2, 0]
    for (d, des), col, ls, mk in (((ds, "board"), blue, "-", "o"), ((mm, "board"), red, "-", "s"),
                                  ((ds, "second board, +0.55 pF"), blue, DASH, "o"), ((mm, "second board, +0.55 pF"), red, DASH, "s")):
        c = cases[(d, des)]
        q = np.array([r["q"] for r in c["runs"]]) * 1e12
        vp = np.array([abs(r["tia"]["v_peak"]) for r in c["runs"]])
        vl = np.array([abs(r["v_lin_peak"]) for r in c["runs"]])
        ax.plot(q, vp, ls=ls, marker=mk, ms=3.0, color=col, lw=LW, mfc="white" if des != "board" else col)
        ax.plot(q, vl, ls=":", color=col, lw=0.9)
    q_abs = VDIFF_MAX_OPA846 * min(c["ct"] + c["cf"] for c in out["cases"]) * 1e12
    ax.axvspan(q_abs, 20, color=COLORS["highlight"], alpha=0.24, lw=0, zorder=0)
    ax.text(q_abs * 0.93, 0.0125, "1.2 V across\nthe inputs", fontsize=7.2, ha="right", va="bottom", color=COLORS["text"])
    ax.axhline(SWING_OPA846, color=COLORS["annotation"], lw=0.8, ls=DASH)
    ax.text(0.006, SWING_OPA846 * 1.12, "output swing", fontsize=7.2, color=COLORS["annotation"])
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(0.005, 15)
    ax.set_xlabel("Charge per pulse (pC)")
    ax.set_ylabel("Peak TIA output (V)")
    panel_label(ax, "(e)", x=0.025)

    # (f) settling time to 1 % against charge, and the steepest slope over SR
    ax = axs[2, 1]
    for (d, des), col, ls, mk in (((ds, "board"), blue, "-", "o"), ((mm, "board"), red, "-", "s"),
                                  ((ds, "second board, +0.55 pF"), blue, DASH, "o"), ((mm, "second board, +0.55 pF"), red, DASH, "s")):
        c = cases[(d, des)]
        q = np.array([r["q"] for r in c["runs"]]) * 1e12
        ts = np.array([r["tia"]["t_settle_1pct"] for r in c["runs"]]) * 1e9
        ax.plot(q, ts, ls=ls, marker=mk, ms=3.0, color=col, lw=LW, mfc="white" if des != "board" else col)
    ax.set_xscale("log")
    ax.set_xlim(0.005, 15)
    ax.set_ylim(0, None)
    ax.set_xlabel("Charge per pulse (pC)")
    ax.set_ylabel("Settling to 1 % of the peak (ns)")
    panel_label(ax, "(f)", x=0.94)
    export(fig, Path(stem))
    print(f"Figure 13 written to {stem}.png and .pdf")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--note", action="store_true")
    ap.add_argument("--figure", nargs="?", const=str(HERE.parent / "figures" / "fig37f_opa846_1k5_pulse"), default=None)
    ap.add_argument("--from-json", help="with --note: redraw the figure from this results file instead of running the cases")
    ap.add_argument("--tables", action="store_true", help="with --note: print the Markdown rows of Tables 4.8 and 4.9")
    ap.add_argument("--part")
    ap.add_argument("--aol-spice")
    ap.add_argument("--aol-table")
    ap.add_argument("--zeros", type=int, default=1)
    ap.add_argument("--poles", type=int, default=3)
    ap.add_argument("--rf", type=float, default=1500.0)
    ap.add_argument("--ct", type=float, help="pF")
    ap.add_argument("--cf", type=float, help="pF")
    ap.add_argument("--sr", type=float, help="V/us")
    ap.add_argument("--sr-test", type=float, nargs=2, metavar=("GAIN", "STEP"),
                    help="calibrate the internal slew rate in a non-inverting test of this gain and output step (V)")
    ap.add_argument("--swing", type=float, default=SWING_OPA846)
    ap.add_argument("--vdiff-max", type=float, default=VDIFF_MAX_OPA846)
    ap.add_argument("--vlin")
    ap.add_argument("--charges")
    ap.add_argument("--pulse", default="delta")
    ap.add_argument("--chain", default="none", choices=("none", "rc", "rc2", "rc1"))
    ap.add_argument("--window", type=float, default=150.0, help="ns")
    ap.add_argument("--dt", type=float, default=2.0, help="ps")
    ap.add_argument("--json")
    a = ap.parse_args()
    if a.note:
        path = HERE.parent / "data" / "results" / "tia_pulse_response_opa846_1k5.json"
        if a.from_json:
            out = json.loads(Path(a.from_json).read_text(encoding="utf-8"))
        else:
            out = compact(note_cases())
            path.write_bytes(json.dumps(out).encode("utf-8"))
            print(f"\nwritten {path}")
        if a.tables:
            note_tables(out)
        if a.figure:
            draw(out, a.figure)
        return
    if a.part:
        import case_studies as cs
        import parts_db
        ol = cs.Analytic(a.part).ol
        sr = a.sr * 1e6 if a.sr else parts_db.PARTS[a.part]["dr"]["sr"] * 1e6
    elif a.aol_spice or a.aol_table:
        ol = spice_open_loop(a.aol_spice) if a.aol_spice else table_open_loop(a.aol_table)
        if not a.sr:
            ap.error("--sr is needed with --aol-spice or --aol-table")
        sr = a.sr * 1e6
    else:
        ap.error("give --part, --aol-spice, --aol-table or --note")
    if a.ct is None or a.cf is None:
        ap.error("--ct and --cf are needed")
    rol, eg, ep = fit_rational(ol.f, ol.g_db, ol.ph_deg, a.zeros, a.poles, note=ol.note)
    print(f"rational fit: {rol.describe()}; rms {eg:.2f} dB, {ep:.2f} deg")
    if a.sr_test:
        # calibrate the internal slew rate in the datasheet's non-inverting test (R_G = 50 ohm, R_F = 50 (G - 1))
        gain, step = a.sr_test
        test = dict(r_f=50.0 * (gain - 1), r_g=50.0, swing=a.swing)
        sr_int, _ = calibrate_sr(rol, target=sr, step=step, **test)
        r = g10_step_test(rol, [sr_int], step=step, **test)[0]
        print(f"Test 2: the internal slew rate {sr_int / 1e6:.1f} V/us gives {r['avg_10_90'] / 1e6:.1f} V/us from 10 to 90 % of a "
              f"{step:g}-V step in a gain of {gain:g} (steepest {r['steepest'] / 1e6:.0f} V/us)")
        sr = sr_int
    t1 = open_loop_slew_check(rol, sr, swing=a.swing)
    print(f"Test 1: the open-loop ramp at {sr / 1e6:.1f} V/us has slope {t1['ramp_slope'] / 1e6:.2f} V/us "
          f"({100 * t1['rel_error']:+.4f} %), steepest {t1['steepest'] / 1e6:.0f} V/us, V_ov {t1['v_ov'] * 1e3:.1f} mV")
    ct, cf = a.ct * 1e-12, a.cf * 1e-12
    print(f"linear check: {100 * linear_check(rol, a.rf, ct, cf, sr, a.swing, dt=a.dt * 1e-12):.3f} % of the peak")
    vlin = [float(v) for v in a.vlin.split(",")] if a.vlin else None
    charges = [float(v) * 1e-12 for v in a.charges.split(",")] if a.charges else None
    res = run_case("command line", ol, rol, a.rf, ct, cf, sr, a.swing, vlin=vlin, charges=charges, pulse=a.pulse,
                   chain=a.chain, window=a.window * 1e-9, dt=a.dt * 1e-12, vdiff_max=a.vdiff_max)
    if a.json:
        Path(a.json).write_text(json.dumps(res, default=float), encoding="utf-8")
        print(f"written {a.json}")


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    main()
