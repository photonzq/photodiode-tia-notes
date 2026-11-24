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
    --sr V_PER_US      slew rate; --swing V the symmetric output swing (default 3.4 V: OPA846 on +/-5 V, >= 400 ohm,
                       p. 3); --vdiff-max V the absolute maximum differential input (default 1.2 V, OPA846 p. 2),
                       only reported
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
datasheet-curve and the macromodel descriptions, at 14 pulse sizes; and on the board the slew rate at 500 and
1250 V/us, a Gaussian pulse of 50 ps and a balanced pair's doublet), writes
../data/results/tia_pulse_response_opa846_1k5.json, prints every number of the section and of Table 4.8, and with
--figure draws Figure 13 (../figures/fig37f_opa846_1k5_pulse.png and .pdf).  The runs take about two minutes;
--from-json redraws the figure from a saved results file without running them.

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
    whose current saturates, i = I_T tanh(v_d/V_ov), charges the compensation capacitance, so that the dominant
    stage obeys
        dx_1/dt = 2 pi GBW V_ov tanh(v_d/V_ov) - 2 pi f_p1 x_1,     V_ov = SR/(2 pi GBW),
    which is A_0/(1 + s/(2 pi f_p1)) for small signals and slews at exactly +/-SR when the stage is overdriven.
    x_1 is held within the swing (the high-impedance node saturates near the rails).  A linear network follows,
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

What is read off each run: the peak and its time, the compression against the linear peak, the slew-limited peak
in closed form, Eq. (36u), V_pk = SR R_F [sqrt(C_F^2 + 2 Q/(R_F SR)) - C_F] (an upper estimate in the slewing
range), the largest voltage across the inputs, the time during which the input stage delivers more than 90 % of
its tail current, the ringing, the settling to 1 % and 0.1 % of the peak, the largest excursion after 4, 10, 12.5
and 25 ns, and the area divided by Q, which Eq. (36v), int v_o dt = -R_F Q + int v_n dt, says falls short of -R_F
while the stage slews.

What the model leaves out: the input stage's own capacitance changing with its operating point, the protection
diodes from each pin to the supplies (OPA846 p. 19; they conduct only beyond the supplies), any recovery time after
the output has clipped, and the photodiode's own response time, which the gauss and rect shapes can stand in for.
Beyond --vdiff-max the part is outside its absolute maximum rating and the model is not evidence.
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
N_DELAY = 10
SWING_OPA846 = 3.4          # V, +/-5 V and >= 400 ohm (OPA846 p. 3)
VDIFF_MAX_OPA846 = 1.2      # V, absolute maximum differential input (OPA846 p. 2)


# ---------------------------------------------------------------------------------------------------------------
# the open-loop gain: a rational model for the time domain
# ---------------------------------------------------------------------------------------------------------------
class RationalOpenLoop:
    """A(s) = A0 / (1 + s/w1) * prod(1 + s/z_i) / prod(1 + s/p_j) / (1 + s tau/N)^N (frequencies in Hz)."""

    def __init__(self, a0, f_p1, zeros=(), poles=(), tau=0.0, n_delay=N_DELAY, note=""):
        self.a0, self.f_p1, self.zeros, self.poles = float(a0), float(f_p1), tuple(zeros), tuple(poles)
        self.tau, self.n_delay, self.note = float(tau), int(n_delay), note

    @property
    def gbw(self):
        return self.a0 * self.f_p1

    def post(self, f):
        """H_post: everything after the dominant pole, unity at DC."""
        s = 2j * np.pi * np.asarray(f, dtype=float)
        h = np.ones_like(s)
        for z in self.zeros:
            h = h * (1 + s / (2 * np.pi * z))
        for p in self.poles:
            h = h / (1 + s / (2 * np.pi * p))
        if self.tau > 0:
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
        p_list = [2 * np.pi * p for p in self.poles] + [self.n_delay / self.tau] * (self.n_delay if self.tau > 0 else 0)
        z_list = [2 * np.pi * z for z in self.zeros] + [None] * (len(p_list) - len(self.zeros))
        if not p_list or z_list[-1] is not None:
            raise ValueError("the rational model must have more poles (with the delay) than zeros")
        m = len(p_list)
        a, b = np.zeros((m, m)), np.zeros(m)
        cu, du = np.zeros(m), 1.0            # the input of the current section, as c.w + d.u
        for k, (p, z) in enumerate(zip(p_list, z_list)):
            a[k] += p * cu
            b[k] += p * du
            a[k, k] -= p
            if z is None:
                cu, du = np.zeros(m), 0.0
                cu[k] = 1.0
            else:
                cu, du = (p / z) * cu, (p / z) * du
                cu[k] += 1.0 - p / z
        return a, b, cu


def fit_rational(f, g_db, ph_deg, n_zeros=1, n_poles=3, f_lo=1e6, f_hi=1.2e9, band=(80e6, 700e6), note=""):
    """Least-squares fit of RationalOpenLoop to an open-loop gain (dB) and phase (deg); phase residuals count 1/6
    per degree, and the band around the crossover three times.  Returns the model, rms dB and rms deg."""
    f, g_db, ph_deg = (np.asarray(v, dtype=float) for v in (f, g_db, ph_deg))
    a0 = 10 ** (g_db[np.argmin(f)] / 20)
    sel = (f >= 3e6) & (f <= 30e6)
    gbw0 = float(np.median(10 ** (g_db[sel] / 20) * f[sel])) if sel.any() else 1e9
    m = (f >= f_lo) & (f <= f_hi)
    fm, gm, pm = f[m], g_db[m], ph_deg[m]
    w = np.where((fm >= band[0]) & (fm <= band[1]), 3.0, 1.0)
    ok = ~np.isnan(pm)

    def unpack(x):
        return RationalOpenLoop(a0, 10 ** x[0], [10 ** v for v in x[1:1 + n_zeros]],
                                [10 ** v for v in x[1 + n_zeros:1 + n_zeros + n_poles]], x[-1] * 1e-12, note=note)

    def resid(x):
        a = unpack(x).A(fm)
        rg = (20 * np.log10(np.abs(a)) - gm) * w
        php = np.degrees(np.unwrap(np.angle(a)))
        return np.concatenate([rg, (php[ok] - pm[ok]) / 6.0 * w[ok]])

    best = None
    z0 = [300e6, 600e6, 1000e6][:n_zeros]
    p0 = [800e6, 1500e6, 3000e6, 5000e6, 8000e6][:n_poles]
    for tau0 in (100.0, 250.0, 400.0):
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
    a = -(d[:, 1] + 1j * d[:, 2]) / (d[:, 3] + 1j * d[:, 4])
    ph = np.degrees(np.unwrap(np.angle(a)))
    ph -= 360.0 * np.round((ph[np.argmin(abs(f - 10e6))] + 90.0) / 360.0)
    return tm.InterpOpenLoop.from_points([(fi, 20 * math.log10(abs(ai)), pi) for fi, ai, pi in zip(f, a, ph)],
                                         note=f"SPICE A_- from {Path(path).name}")


def table_open_loop(path):
    d = np.loadtxt(path, delimiter=",", skiprows=1)
    return tm.InterpOpenLoop.from_points([(r[0], r[1], r[2]) for r in d], note=f"table {Path(path).name}")


# ---------------------------------------------------------------------------------------------------------------
# the chain to the oscilloscope, Eq. (36i), with phase
# ---------------------------------------------------------------------------------------------------------------
def chain_complex(f, kind, r_s=50.0, c_in=14e-12, f_scope=200e6):
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
    nn = 2 * n
    spec = np.fft.rfft(v, nn) * chain_complex(np.fft.rfftfreq(nn, dt), kind)
    return np.fft.irfft(spec, nn)[:n]


# ---------------------------------------------------------------------------------------------------------------
# the linear response
# ---------------------------------------------------------------------------------------------------------------
def linear_impulse(ol, rf, ct, cf, window=400e-9, dt=10e-12, chain="none"):
    """h(t) of Eq. (36s) in V per coulomb at the TIA output, and at the oscilloscope through the chain."""
    n = int(round(window / dt))
    f = np.fft.rfftfreq(n, dt)
    f[0] = 1e-3
    zt = tm.tia_tf(f, ol, rf, ct, cf)[0]
    t = np.arange(n) * dt
    h = np.fft.irfft(zt, n) / dt
    hs = np.fft.irfft(zt * chain_complex(f, chain), n) / dt
    return t, h, hs


# ---------------------------------------------------------------------------------------------------------------
# the time-domain model
# ---------------------------------------------------------------------------------------------------------------
def simulate(rol, rf, ct, cf, sr, swing, charges, pulse="delta", window=150e-9, dt=2e-12, keep_every=5,
             clamp_margin=0.3):
    """Integrate Eqs. (36t)-(36v) for all charges at once; returns t and v_o, v_n, x_1 sampled every keep_every steps."""
    q = np.asarray(charges, dtype=float)
    na = len(q)
    a_p, b_p, c_p = rol.state_space()
    m = len(b_p)
    w1, wt = 2 * np.pi * rol.f_p1, 2 * np.pi * rol.gbw
    v_ov = sr / wt
    c_sum = ct + cf
    clamp = swing + clamp_margin
    kind, par = (pulse.split(":") + [""])[:2]
    par = float(par) if par else 0.0
    jumps = {}
    if kind == "delta":
        jumps[0] = q
    elif kind == "doublet":
        jumps[0] = q
        jumps[int(round(par * 1e-12 / dt))] = -q
    if kind == "gauss":
        sig = par * 1e-12 / (2 * math.sqrt(2 * math.log(2)))
        t0 = 5 * sig

        def i_in(t):
            return q * math.exp(-0.5 * ((t - t0) / sig) ** 2) / (sig * math.sqrt(2 * math.pi))
    elif kind == "rect":
        width = par * 1e-9

        def i_in(t):
            return q / width if 0 <= t < width else 0.0 * q
    else:
        def i_in(t):
            return 0.0 * q

    def deriv(t, vn, x1, w):
        vd = -vn
        dx1 = wt * v_ov * np.tanh(vd / v_ov) - w1 * x1
        dw = a_p @ w + np.outer(b_p, x1)
        y = c_p @ w
        dy = c_p @ dw
        vo = np.clip(y, -swing, swing)
        dvo = np.where(((y >= swing) & (dy > 0)) | ((y <= -swing) & (dy < 0)), 0.0, dy)
        dvn = (i_in(t) - (vn - vo) / rf + cf * dvo) / c_sum
        return dvn, dx1, dw, vo

    nsteps = int(round(window / dt))
    vn, x1, w = np.zeros(na), np.zeros(na), np.zeros((m, na))
    out_t, out_vo, out_vn, out_x1 = [], [], [], []
    for k in range(nsteps + 1):
        if k in jumps:
            vn = vn + jumps[k] / c_sum
        t = k * dt
        if k % keep_every == 0:
            y = c_p @ w
            out_t.append(t)
            out_vo.append(np.clip(y, -swing, swing))
            out_vn.append(vn.copy())
            out_x1.append(x1.copy())
        if k == nsteps:
            break
        k1 = deriv(t, vn, x1, w)
        k2 = deriv(t + dt / 2, vn + dt / 2 * k1[0], x1 + dt / 2 * k1[1], w + dt / 2 * k1[2])
        k3 = deriv(t + dt / 2, vn + dt / 2 * k2[0], x1 + dt / 2 * k2[1], w + dt / 2 * k2[2])
        k4 = deriv(t + dt, vn + dt * k3[0], x1 + dt * k3[1], w + dt * k3[2])
        vn = vn + dt / 6 * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0])
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
    i_pk = int(np.argmax(np.abs(v)))
    v_pk = float(v[i_pk])
    a = np.abs(v)
    above1 = np.where(a > 0.01 * abs(v_pk))[0]
    above01 = np.where(a > 0.001 * abs(v_pk))[0]
    dv = np.diff(v)
    ext = np.where(np.sign(dv[1:]) != np.sign(dv[:-1]))[0] + 1           # local extrema
    last = above1[-1] if len(above1) else len(v) - 1
    ext = ext[(ext > i_pk) & (ext <= last) & (a[ext] < 0.5 * abs(v_pk))]
    ext = np.array([e for k, e in enumerate(ext) if k == 0 or np.sign(v[e]) != np.sign(v[ext[k - 1]])], dtype=int)
    f_r = tau = q_r = float("nan")
    if len(ext) >= 4:
        te, ve = t[ext], a[ext]
        f_r = 1.0 / (2.0 * float(np.mean(np.diff(te))))
        slope = np.polyfit(te, np.log(ve), 1)[0]
        tau = -1.0 / slope if slope < 0 else float("nan")
        q_r = math.pi * f_r * tau
    first_opp = np.where(np.sign(v[i_pk:]) == -np.sign(v_pk))[0]
    undershoot = float(np.max(np.abs(v[i_pk + first_opp[0]:])) / abs(v_pk)) if len(first_opp) else 0.0
    residual = {f"{tt * 1e9:g} ns": float(np.max(a[t >= tt]) / abs(v_pk)) for tt in (4e-9, 10e-9, 12.5e-9, 25e-9) if tt < t[-1]}
    out = dict(v_peak=v_pk, t_peak=float(t[i_pk]), f_ring=f_r, tau_decay=tau, q_ring=q_r,
               t_settle_1pct=float(t[above1[-1]]) if len(above1) else 0.0,
               t_settle_01pct=float(t[above01[-1]]) if len(above01) else 0.0,
               undershoot_ratio=undershoot, max_slope=float(np.max(np.abs(np.gradient(v, t)))),
               residual_after=residual)
    if q:
        out["area_over_q"] = float(np.trapezoid(v, t) / q)
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
    for name, ol, c1, c2 in (("curve", ol_curve, ct_c, cf_c), ("rational", rol, ct, cf)):
        if ol is None:
            continue
        m = tm.loop_metrics(ol, rf, c1, c2)
        res[f"loop_{name}"] = {k: (float(v) if isinstance(v, (int, float, np.floating)) else v) for k, v in m.items()}
    tl, hl, hsl = linear_impulse(rol, rf, ct, cf, chain=chain)
    lin = response_metrics(tl, hl * 1e-12, 1e-12, t_max=200e-9)
    lin_s = response_metrics(tl, hsl * 1e-12, 1e-12, t_max=200e-9)
    res["linear_rational"] = dict(tia=lin, scope=lin_s)
    keep = tl <= 80e-9
    res["linear_waveform"] = dict(t=tl[keep][::2].tolist(), tia_V_per_pC=(hl[keep][::2] * 1e-12).tolist(),
                                  scope_V_per_pC=(hsl[keep][::2] * 1e-12).tolist())
    if ol_curve is not None:
        tc, hc, hsc = linear_impulse(ol_curve, rf, ct_c, cf_c, chain=chain)
        res["linear_curve"] = dict(tia=response_metrics(tc, hc * 1e-12, 1e-12, t_max=200e-9),
                                   scope=response_metrics(tc, hsc * 1e-12, 1e-12, t_max=200e-9),
                                   precursor=float(np.max(np.abs(hc[tc > 300e-9])) / np.max(np.abs(hc))))
        res["linear_curve_waveform"] = dict(t=tc[tc <= 80e-9][::2].tolist(), tia_V_per_pC=(hc[tc <= 80e-9][::2] * 1e-12).tolist())
    h_pk = abs(lin["v_peak"]) / 1e-12                                     # V per coulomb
    if charges is None:
        charges = [v / h_pk for v in (vlin or (0.01, 0.1, 0.3, 1.0, 3.0))]
    charges = [float(c) for c in charges]
    t, vo, vn, x1, v_ov = simulate(rol, rf, ct, cf, sr, swing, charges, pulse=pulse, window=window, dt=dt)
    res["v_ov"] = v_ov
    runs = []
    for k, q in enumerate(charges):
        vs = apply_chain(t, vo[k], chain)
        mt = response_metrics(t, vo[k], q)
        ms = response_metrics(t, vs, q)
        vd_max = float(np.max(np.abs(vn[k])))
        dx1 = np.gradient(x1[k], t)
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
    tl, hl, _ = linear_impulse(rol, rf, ct, cf)
    q = 1e-16
    t, vo, _, _, _ = simulate(rol, rf, ct, cf, sr, swing, [q], window=80e-9, dt=dt, keep_every=5)
    ref = np.interp(t, tl, hl) * q
    err = float(np.max(np.abs(vo[0] - ref)) / np.max(np.abs(ref)))
    return err


# ---------------------------------------------------------------------------------------------------------------
# the cases of the note
# ---------------------------------------------------------------------------------------------------------------
NOTE_VLIN = (0.01, 0.03, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0, 1.5, 2.0, 3.0, 5.0, 7.0, 10.0)
SHOWN_VLIN = (0.01, 0.3, 1.0, 3.0, 10.0)


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
    comp = np.array([r["compression_dB"] for r in res["runs"]])
    area = np.array([abs(r["tia"]["area_over_q"]) / res["rf"] - 1.0 for r in res["runs"]])
    out = {}
    for key, y, levels in (("peak_dB", comp, (-0.1, -1.0)), ("area", area, (-1e-3, -1e-2))):
        for lev in levels:
            k = np.where(y <= lev)[0]
            if not len(k) or k[0] == 0:
                out[f"{key}_{lev:g}"] = None
                continue
            i = k[0]
            x0, x1 = math.log10(q[i - 1]), math.log10(q[i])
            xq = x0 + (lev - y[i - 1]) * (x1 - x0) / (y[i] - y[i - 1])
            qq = 10 ** xq
            out[f"{key}_{lev:g}"] = dict(q=qq, v_lin=qq * abs(res["runs"][0]["v_lin_peak"]) / res["runs"][0]["q"])
    return out


def note_cases():
    import case_studies as cs
    import compare_opa846_1k5_board as cb

    an = cs.Analytic("OPA846")
    sr = 625e6
    b = cb.read_bins(str(HERE.parent / "data" / "measurements" / "opa846_1k5_board_per_MHz.csv"))
    use = (~b["bad"]) & np.isfinite(b["G"]) & (b["f"] >= 10e6)
    f, g = b["f"][use], b["G"][use]
    h = cb.chain(f, "rc")
    mac = spice_open_loop(HERE.parent / "spice" / "runs" / "aol" / "OPA846_inverting" / "aol.txt")
    out = dict(cases=[], fits={})
    descriptions = (("datasheet curve", an.ol), ("macromodel A_-", mac))
    for name, ol in descriptions:
        rol, eg, ep = fit_rational(ol.f, ol.g_db, ol.ph_deg, 1, 3, note=name)
        print(f"{name}: rational fit {rol.describe()}; rms {eg:.2f} dB, {ep:.2f} deg")
        r_curve = cb.fit(f, g, ol, h, True)
        r_rat = cb.fit(f, g, rol, h, True)
        print(f"  the measured gain fitted with the curve: C_T {r_curve['ct'] * 1e12:.3f} pF, C_F {r_curve['cf'] * 1e12:.3f} pF, "
              f"eps {100 * r_curve['eps']:.2f} %, PM {r_curve['m']['pm_deg']:.2f} deg; with the rational model: "
              f"C_T {r_rat['ct'] * 1e12:.3f} pF, C_F {r_rat['cf'] * 1e12:.3f} pF, K {r_rat['k']:.3f}, eps {100 * r_rat['eps']:.2f} %, "
              f"PM {r_rat['m']['pm_deg']:.2f} deg, TIA peak {r_rat['pk']:+.2f} dB at {r_rat['fpk'] / 1e6:.0f} MHz")
        out["fits"][name] = dict(rational=rol.to_dict(), rms_dB=eg, rms_deg=ep, ct_curve=r_curve["ct"], cf_curve=r_curve["cf"],
                                 ct=r_rat["ct"], cf=r_rat["cf"], k=r_rat["k"], eps=r_rat["eps"], pm=r_rat["m"]["pm_deg"])
        print(f"  linear check (time-domain model against the inverse FFT of its own Z_T): "
              f"{100 * linear_check(rol, 1500.0, r_rat['ct'], r_rat['cf'], sr, SWING_OPA846):.3f} % of the peak")
        for tag, add in (("board", 0.0), ("second board, +0.55 pF", 0.55e-12)):
            res = run_case(f"{tag}, {name}", ol, rol, 1500.0, r_rat["ct"], r_rat["cf"] + add, sr, SWING_OPA846,
                           vlin=NOTE_VLIN, chain="rc", curve_ctcf=(r_curve["ct"], r_curve["cf"] + add))
            res["compression"] = compression_points(res)
            print("  compression: " + "; ".join(
                f"{k} at {v['q'] * 1e12:.3f} pC ({v['v_lin']:.3f} V linear peak)" if v else f"{k} not reached"
                for k, v in res["compression"].items()))
            v_ov, c_sum = res["v_ov"], r_rat["ct"] + r_rat["cf"] + add
            print(f"  the node jump reaches V_ov ({v_ov * 1e3:.1f} mV) at {v_ov * c_sum * 1e12:.3f} pC and "
                  f"{VDIFF_MAX_OPA846:.1f} V at {VDIFF_MAX_OPA846 * c_sum * 1e12:.2f} pC (C_T + C_F = {c_sum * 1e12:.3f} pF)")
            res.update(description=name, design=tag)
            out["cases"].append(res)
    # slew-rate sensitivity, a finite pulse width and a balanced pair's doublet, on the board (datasheet curve)
    name = descriptions[0][0]
    fr = out["fits"][name]["rational"]
    rol = RationalOpenLoop(fr["a0"], fr["f_p1_Hz"], fr["zeros_Hz"], fr["poles_Hz"], fr["tau_s"], fr["n_delay"], fr["note"])
    ct, cf = out["fits"][name]["ct"], out["fits"][name]["cf"]
    extra = []
    for tag, sr_x, pulse, vl in (("SR 500 V/us (datasheet minimum)", 500e6, "delta", (0.3, 1.0, 3.0)),
                                 ("SR 1250 V/us (twice the datasheet value)", 1250e6, "delta", (0.3, 1.0, 3.0)),
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
        lab = ("board, " if des == "board" else "+0.55 pF, ") + ("datasheet curve" if d == ds else "macromodel")
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
    ap.add_argument("--part")
    ap.add_argument("--aol-spice")
    ap.add_argument("--aol-table")
    ap.add_argument("--zeros", type=int, default=1)
    ap.add_argument("--poles", type=int, default=3)
    ap.add_argument("--rf", type=float, default=1500.0)
    ap.add_argument("--ct", type=float, help="pF")
    ap.add_argument("--cf", type=float, help="pF")
    ap.add_argument("--sr", type=float, help="V/us")
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
