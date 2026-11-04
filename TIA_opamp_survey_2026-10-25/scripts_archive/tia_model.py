"""Analytical model of an inverting photodiode transimpedance amplifier (TIA).

Everything is in SI units unless a name says otherwise (``_pF``, ``_MHz`` ...).

Circuit
-------
* Photodiode: current source in parallel with C_D, from the inverting input to
  AC ground (the bias side is decoupled).
* The inverting node also carries the PCB pad/trace capacitance C_PCB and the
  amplifier input capacitances: the common-mode capacitance C_CM of the
  inverting input to ground and the differential capacitance C_DIFF to the
  non-inverting input, which is AC-grounded.  Their sum is C_T.
* Feedback: R_F in parallel with C_F (C_F = external capacitor + parasitic).
* Amplifier: open-loop gain A(s) (``OpenLoopModel``), output treated as an
  ideal voltage source (open-loop output impedance neglected).

Closed loop
-----------
    Z_F(s)  = R_F / (1 + s R_F C_F)
    NG(s)   = 1 + s C_T Z_F(s) = (1 + s R_F (C_T + C_F)) / (1 + s R_F C_F)
    T(s)    = A(s) / NG(s)                      (loop gain)
    Z_T(s)  = -Z_F(s) T(s) / (1 + T(s))          (transimpedance)

Input-referred current noise (power spectral density, A^2/Hz)
-------------------------------------------------------------
    S_i = 4kT/R_F + i_n^2 + e_n^2 |1/R_F + j w (C_T + C_F)|^2 + 2 q I_DC
The e_n term is independent of the loop gain (the closed-loop factor cancels
when output noise is referred back through Z_T).

Where the note uses each function (numbering of 4 November 2026)
-----------------------------------------------------------------
This module is "our analytical model" of the note: every dashed curve labelled
"analytical model" or "model" in its figures, and every number not labelled
SPICE, comes from the functions below, fed with the datasheet values of
parts_db.PARTS through run_analysis.open_loop_model() and noise_inputs().
  InterpOpenLoop         the primary open-loop model of Section 3.5: the gain
                         (dB) and phase (deg) digitized from the datasheet's
                         open-loop plot, interpolated in log10(f)
  OpenLoopModel,         the check model of Section 3.5, Eq. (18): a dominant
  fit_open_loop          pole, two higher poles and a delay fitted to the same
                         points
  calibrated_interp      the calibrated variant of Section 3.5 (Table A3.2,
                         Section 6.2.3): the curve scaled to the table GBW, with
                         the delay that gives the text's phase margin
  tia_tf                 Z_F, NG, T and Z_T: Eqs. (8), (9) and (10)
  loop_metrics           crossover, phase margin, gain margin, second crossing,
                         -3-dB bandwidth and peaking as Section 3.5 defines
                         them; NG at the crossover and NG_inf (Eq. (11))
  design_cf              the flat and 1-dB designs of Section 1.5 (the design
                         search of Section 3.5)
  cf_max_for_gmin        the minimum-gain rule of Section 6.2.4,
                         C_F <= C_T/(G_min - 1)
  butterworth_cf_single_pole, butterworth_f3_single_pole
                         the single-pole Butterworth design, Eq. (14)
  min_ct_for_gmin        the minimum source capacitance, Eq. (16)
  loglog_interp          the datasheet noise curves, interpolated log-log
  noise_components       Eq. (19) term by term ('central'); the long-channel
                         lower bound of Eq. (23) ('low'); the datasheet's rising
                         current-noise curve added as an upper bound
                         ('high'); Eq. (24) names the three; the photodiode
                         series-resistance term of Section 3.6
  band_average_penalty_db  the band penalty of Eq. (21)
  integrated_rms         the band noise in the denominator of Eq. (27)
  johnson_current_asd, shot_current_asd
                         the reference levels of Table A3.3
The scripts written before 27 October 2026 cite older equation numbers in their
own docstrings; rework/TIA_opamp_survey.map.txt and
rework/case_studies_reorder.map.txt convert them.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import brentq, least_squares

K_B = 1.380649e-23        # J/K
Q_E = 1.602176634e-19     # C
T_ROOM = 298.15           # K (25 C, the temperature of datasheet tables)


# ---------------------------------------------------------------------------
# Open-loop gain model
# ---------------------------------------------------------------------------
@dataclass
class OpenLoopModel:
    """A(s) = A0 exp(-s tau) / (1 + s/w1) / prod(1 + s/w_k) * prod(1 + s/w_z)."""

    A0: float
    f_p1: float
    f_poles_hi: tuple = ()
    f_zeros: tuple = ()
    tau: float = 0.0
    note: str = ""

    def A(self, f):
        s = 2j * np.pi * np.asarray(f, dtype=float)
        a = self.A0 / (1.0 + s / (2 * np.pi * self.f_p1))
        for fp in self.f_poles_hi:
            a = a / (1.0 + s / (2 * np.pi * fp))
        for fz in self.f_zeros:
            a = a * (1.0 + s / (2 * np.pi * fz))
        if self.tau:
            a = a * np.exp(-s * self.tau)
        return a

    @property
    def gbw(self) -> float:
        """Gain-bandwidth product of the dominant-pole part (Hz)."""
        return self.A0 * self.f_p1


@dataclass
class InterpOpenLoop:
    """Open-loop gain interpolated directly from digitized datasheet points
    (the primary model of Section 3.5).

    The points are those of each part's extraction record, data/specs/<PART>.json,
    read from the datasheet's open-loop gain and phase plot (from the PDF's vector
    paths where the plot is vector graphics, about +/-0.2 dB and +/-1 deg; from the
    raster otherwise, about +/-0.5-1 dB and +/-2-5 deg).  Phases plotted as
    180 deg + angle(A) were shifted by -180 deg when the records were made.

    Magnitude (dB) and phase (deg) are interpolated linearly in log10(f).
    Below the first point the first values are held.  Above the last
    magnitude point the last log-log slope is extended; above the last phase
    point the phase is extended linearly in f (a pure-delay continuation).
    Beyond the plotted range a gain margin or second crossing is therefore only
    indicative (Section 3.5).  The curve is the gain from the non-inverting
    input, as datasheets plot it; the TIA drives the inverting input, which
    Section 5.3 compares (A_- against A_+).
    """

    f: np.ndarray
    g_db: np.ndarray
    ph_deg: np.ndarray
    note: str = ""

    @classmethod
    def from_points(cls, points, note=""):
        p = np.array([[q[0], q[1], np.nan if q[2] is None else q[2]] for q in points], dtype=float)
        p = p[np.argsort(p[:, 0])]
        return cls(f=p[:, 0], g_db=p[:, 1], ph_deg=p[:, 2], note=note)

    def A(self, f):
        f = np.atleast_1d(np.asarray(f, dtype=float))
        lf, x = np.log10(f), np.log10(self.f)
        g = np.interp(lf, x, self.g_db)
        slope = (self.g_db[-1] - self.g_db[-2]) / (x[-1] - x[-2])
        g = np.where(lf > x[-1], self.g_db[-1] + slope * (lf - x[-1]), g)
        m = ~np.isnan(self.ph_deg)
        fp, pp = self.f[m], self.ph_deg[m]
        ph = np.interp(lf, np.log10(fp), pp)
        dpdf = (pp[-1] - pp[-2]) / (fp[-1] - fp[-2])
        ph = np.where(f > fp[-1], pp[-1] + dpdf * (f - fp[-1]), ph)
        return 10 ** (g / 20) * np.exp(1j * np.radians(ph))

    @property
    def A0(self) -> float:
        return float(10 ** (self.g_db.max() / 20))

    @property
    def gbw(self) -> float:
        """GBW estimated as 100 x the frequency where |A| = 40 dB."""
        x = np.log10(self.f)
        i = np.where((self.g_db[:-1] >= 40) & (self.g_db[1:] < 40))[0]
        if not len(i):
            return float("nan")
        i = i[0]
        xc = x[i] + (40 - self.g_db[i]) * (x[i + 1] - x[i]) / (self.g_db[i + 1] - self.g_db[i])
        return float(100 * 10 ** xc)


def calibrated_interp(base: "InterpOpenLoop", gain_scale_dB: float, pm_target_deg: float,
                      g_noise: float) -> "InterpOpenLoop":
    """Copy of an interpolated curve with its magnitude shifted by gain_scale_dB and an
    added pure delay chosen so that the phase margin at a resistive noise gain g_noise
    equals pm_target_deg.  Used to reconcile a plotted open-loop curve with the
    phase margin and GBW stated in the datasheet text and table."""
    def make(tau):
        return InterpOpenLoop(f=base.f.copy(), g_db=base.g_db + gain_scale_dB,
                              ph_deg=base.ph_deg - 360.0 * base.f * tau,
                              note=f"{base.note}; scaled {gain_scale_dB:+.1f} dB, +{tau*1e12:.0f} ps delay")

    def pm_err(tau):
        C_F = 100e-12
        m = loop_metrics(make(tau), 2000.0, (g_noise - 1) * C_F, C_F)
        return m["pm_deg"] - pm_target_deg

    if pm_err(0.0) <= 0:
        return make(0.0)
    tau = brentq(pm_err, 0.0, 400e-12, xtol=1e-14)
    return make(tau)


def fit_open_loop(points, A0=None, n_hi_poles=2, use_delay=True,
                  f_min_fit=1e6, gbw_hint=None, f_max_fit=None):
    """Fit OpenLoopModel to digitized (f_Hz, gain_dB, phase_deg) points.

    The phase must be the phase of A(jw) itself: 0 deg at DC, -90 deg above
    the dominant pole, falling further at high frequency.  Points below
    ``f_min_fit`` are used for the gain only.
    Returns (model, rms_gain_error_dB, rms_phase_error_deg).
    """
    pts = np.array([[p[0], p[1], np.nan if p[2] is None else p[2]]
                    for p in points], dtype=float)
    if f_max_fit is not None:
        pts = pts[pts[:, 0] <= f_max_fit]
    f, g_db, ph = pts[:, 0], pts[:, 1], pts[:, 2]
    if A0 is None:
        A0 = 10 ** (g_db[np.argmin(f)] / 20)
    if gbw_hint is None:
        # gain*frequency on the -20 dB/dec part, taken at the point nearest 0 dB+20
        idx = np.argmin(np.abs(g_db - 20))
        gbw_hint = 10 ** (g_db[idx] / 20) * f[idx]
    f_p1_0 = gbw_hint / A0

    def unpack(x):
        f_p1 = 10 ** x[0]
        hi = tuple(10 ** v for v in x[1:1 + n_hi_poles])
        tau = x[1 + n_hi_poles] * 1e-12 if use_delay else 0.0
        return OpenLoopModel(A0=A0, f_p1=f_p1, f_poles_hi=hi, tau=tau)

    def resid(x):
        m = unpack(x)
        a = m.A(f)
        r_g = 20 * np.log10(np.abs(a)) - g_db
        ph_model = np.degrees(np.unwrap(np.angle(a)))
        mask = (~np.isnan(ph)) & (f >= f_min_fit)
        r_p = (ph_model[mask] - ph[mask]) / 6.0   # 6 deg ~ 1 dB weight
        return np.concatenate([r_g, r_p])

    x0 = [np.log10(f_p1_0)] + [np.log10(gbw_hint * k) for k in (1.0, 3.0)[:n_hi_poles]]
    if use_delay:
        x0.append(10.0)
    lb = [np.log10(f_p1_0) - 2] + [7.0] * n_hi_poles + ([0.0] if use_delay else [])
    ub = [np.log10(f_p1_0) + 2] + [11.5] * n_hi_poles + ([400.0] if use_delay else [])
    sol = least_squares(resid, x0, bounds=(lb, ub))
    m = unpack(sol.x)
    a = m.A(f)
    rg = 20 * np.log10(np.abs(a)) - g_db
    ph_model = np.degrees(np.unwrap(np.angle(a)))
    mask = ~np.isnan(ph)
    rp = ph_model[mask] - ph[mask]
    return m, float(np.sqrt(np.mean(rg ** 2))), float(np.sqrt(np.mean(rp ** 2))) if mask.any() else float("nan")


# ---------------------------------------------------------------------------
# Closed-loop TIA
# ---------------------------------------------------------------------------
def tia_tf(f, ol: OpenLoopModel, R_F, C_T, C_F):
    """Return Z_T (complex, ohm), NG (complex) and loop gain T at frequencies f.

    The inverting TIA of Figure 1 with an amplifier of open-loop gain A(f) and an
    ideal output (Section 3.2):
        Z_F = R_F / (1 + s R_F C_F)                      Eq. (8)
        NG  = 1 + s C_T Z_F,   T = A / NG                Eq. (10)
        Z_T = -Z_F T / (1 + T)                           Eq. (9)
    with s = j 2 pi f, C_T the total capacitance from the summing node to AC
    ground (Eq. (7): photodiode, board and the amplifier's C_CM + C_DIFF) and C_F
    the total feedback capacitance.  Z_T leaves out the photocurrent that reaches
    the output directly through C_F, which matters only above a few GHz
    (Section 5.2, Figure 9c)."""
    s = 2j * np.pi * np.asarray(f, dtype=float)
    Z_F = R_F / (1 + s * R_F * C_F)          # feedback network, Eq. (8)
    NG = 1 + s * C_T * Z_F                   # noise gain, Eq. (10)
    A = ol.A(f)                              # open-loop gain from the datasheet curve
    T = A / NG                               # loop gain, Eq. (10)
    Z_T = -Z_F * T / (1 + T)                 # transimpedance, Eq. (9)
    return Z_T, NG, T


F_GRID = np.logspace(4, 10.7, 6000)   # 10 kHz .. 50 GHz


def loop_metrics(ol, R_F, C_T, C_F, f=F_GRID):
    """Loop and closed-loop figures of merit for one design.

    f_c / pm_deg : first downward crossing of |T| = 1 and its phase margin.
    ng_at_fc     : |NG| at that crossing (compare with the minimum stable gain).
    second_crossing : True if |T| rises above 1 again above 1.2 f_c (the loop
                   regains gain, e.g. at an open-loop resonance); such a design
                   is treated as unstable.
    gm_dB        : gain margin at the first frequency where the loop phase
                   reaches -180 deg (NaN if it never does in the grid).
    f_3dB, peaking_dB : of |Z_T| / R_F.

    These are the loop metrics of Section 3.5, read on F_GRID (6000 points
    from 10 kHz to 50 GHz, logarithmically spaced), and the closed-loop
    figures that every table of the note quotes for "our analytical model".
    """
    Z_T, NG, T = tia_tf(f, ol, R_F, C_T, C_F)
    magT = np.abs(T)
    phT = np.degrees(np.unwrap(np.angle(T)))  # continuous phase, so that -180 deg is found once
    # crossover: the first grid interval in which |T| falls through 1
    idx = np.where((magT[:-1] >= 1) & (magT[1:] < 1))[0]
    second = False
    if len(idx) == 0:
        f_c, pm, ng_c = np.nan, np.nan, np.nan
    else:
        i = idx[0]
        # interpolate log|T| linearly in log f to the exact crossing, and the phase with it
        x0, x1 = np.log10(f[i]), np.log10(f[i + 1])
        y0, y1 = np.log10(magT[i]), np.log10(magT[i + 1])
        xc = x0 + (0 - y0) * (x1 - x0) / (y1 - y0)
        f_c = 10 ** xc
        pm = 180 + np.interp(xc, [x0, x1], [phT[i], phT[i + 1]])     # phase margin, 180 deg + angle(T)
        # |NG| at the crossover, the gain at which a decompensated amplifier is used (Section 3.4)
        ng_c = np.abs(1 + 2j * np.pi * f_c * C_T * R_F / (1 + 2j * np.pi * f_c * R_F * C_F))
        # a loop that regains |T| >= 1 above 1.2 f_c (e.g. on an open-loop bump at GHz) counts as unstable
        above = f > 1.2 * f_c
        second = bool(np.any(magT[above] >= 1.0))
    # gain margin: -20 log|T| at the first grid point where the phase has reached -180 deg
    k = np.where(phT <= -180)[0]
    gm = -20 * np.log10(magT[k[0]]) if len(k) else np.nan
    # closed loop: |Z_T| relative to R_F, its largest value (peaking) and its -3-dB point
    H = np.abs(Z_T) / R_F
    peak_db = 20 * np.log10(H.max())
    f_peak = f[np.argmax(H)]
    below = np.where(H < 1 / np.sqrt(2))[0]   # the first point below -3 dB, interpolated in log f
    f3 = np.nan
    if len(below):
        j = below[0]
        if j > 0:
            x0, x1 = np.log10(f[j - 1]), np.log10(f[j])
            y0, y1 = H[j - 1], H[j]
            f3 = 10 ** (x0 + (1 / np.sqrt(2) - y0) * (x1 - x0) / (y1 - y0))
        else:
            f3 = f[0]
    stable = bool(np.isfinite(pm) and pm > 0 and not second)
    return dict(f_c=f_c, pm_deg=pm, ng_at_fc=ng_c, f_3dB=f3,
                peaking_dB=peak_db, f_peak=f_peak, gm_dB=gm,
                second_crossing=second, stable=stable,
                ng_hf=1 + C_T / C_F if C_F > 0 else np.inf)


CF_SCAN = np.logspace(np.log10(0.02e-12), np.log10(3e-12), 160)


def design_cf(ol, R_F, C_T, peaking_target_dB, cf_grid=CF_SCAN):
    """Smallest total C_F that is stable and peaks no more than the target.

    C_F is scanned on a log grid from small to large; the first grid value
    that is stable (single crossing, positive phase margin) and meets the
    peaking target brackets the answer, which is then refined by bisection
    against the previous grid value.  Returns NaN if no grid value qualifies.
    """
    def ok(cf):
        m = loop_metrics(ol, R_F, C_T, cf)
        return m["stable"] and m["peaking_dB"] <= peaking_target_dB

    prev = None
    for cf in cf_grid:
        if ok(cf):
            if prev is None:
                return cf
            lo, hi = np.log10(prev), np.log10(cf)
            for _ in range(30):
                mid = 0.5 * (lo + hi)
                if ok(10 ** mid):
                    hi = mid
                else:
                    lo = mid
            return 10 ** hi
        prev = cf
    return np.nan


def cf_max_for_gmin(C_T, g_min):
    """Largest C_F keeping the high-frequency noise gain 1 + C_T/C_F >= g_min."""
    return C_T / (g_min - 1) if g_min > 1 else np.inf


# ---------------------------------------------------------------------------
# Single-pole closed forms (used in the report derivations and as a check)
# ---------------------------------------------------------------------------
def butterworth_cf_single_pole(R_F, C_T, gbw):
    """Exact Butterworth C_F for A(s) = w_A / s:  (R_F C_F)^2 = 2 R_F C_T/w_A - 1/w_A^2."""
    wA = 2 * np.pi * gbw
    val = 2 * R_F * C_T / wA - 1 / wA ** 2
    return np.sqrt(val) / R_F if val > 0 else 0.0


def butterworth_f3_single_pole(R_F, C_T, C_F, gbw):
    """-3 dB frequency of the Butterworth design: sqrt(GBW / (2 pi R_F (C_T + C_F)))."""
    return np.sqrt(gbw / (2 * np.pi * R_F * (C_T + C_F)))


def min_ct_for_gmin(R_F, gbw, g_min):
    """Smallest C_T for which the single-pole Butterworth design has NG_HF >= g_min."""
    return 2 * (g_min - 1) ** 2 / (2 * np.pi * gbw * R_F)


# ---------------------------------------------------------------------------
# Noise
# ---------------------------------------------------------------------------
def loglog_interp(f, pts, default, extrapolate_high=False):
    """Interpolate a spectral density given as [(f, value), ...] in log-log space.

    Below the tabulated range the first value is held.  Above it the last
    value is held, or, with extrapolate_high=True, the log-log slope of the
    last segment is continued (used for rising current-noise curves).
    """
    f = np.asarray(f, dtype=float)
    if not pts:
        return np.full_like(f, default, dtype=float)
    p = np.array(sorted(pts), dtype=float)
    x, y = np.log10(p[:, 0]), np.log10(p[:, 1])
    out = np.interp(np.log10(f), x, y)
    if extrapolate_high and len(p) >= 2:
        slope = (y[-1] - y[-2]) / (x[-1] - x[-2])
        lf = np.log10(f)
        out = np.where(lf > x[-1], y[-1] + slope * (lf - x[-1]), out)
    return 10 ** out


@dataclass
class NoiseInputs:
    en_flat: float                 # V/rtHz (high-frequency flat value)
    in_flat: float                 # A/rtHz (white input current noise)
    en_pts: list = field(default_factory=list)   # [(f, V/rtHz)]
    in_pts: list = field(default_factory=list)   # [(f, A/rtHz)] datasheet curve
    c_in_amp: float = 0.0          # C_CM + C_DIFF (F), part of C_T
    c_gate: float = 0.0            # gate capacitance of one input transistor (F), ~2 C_DIFF
    fet: bool = False


def noise_components(f, R_F, C_T, C_F, nz: NoiseInputs, i_dc=0.0, T=T_ROOM,
                     fet_model="central", R_s=0.0, C_D=0.0):
    """Input-referred current-noise PSD components (A^2/Hz) at frequencies f.

    fet_model selects how a FET part's high-frequency current noise is handled:
      'central' : e_n acting on C_T (C_T includes the amplifier's C_in) plus the
                  low-frequency white i_n only (no separate HF current term).
      'low'     : complete long-channel picture of a FET differential pair with an
                  ideal tail: the induced gate noise of the inverting-side
                  transistor (van der Ziel, correlation c = 0.395j with its channel
                  noise) and the tail-node motion coupled through C_gs.  The f^2
                  term becomes e_n^2 w^2 [C_tot^2 - 0.25 C_g C_tot + 0.325 C_g^2]
                  (C_g = gate capacitance of one transistor = c_gate, about
                  2 C_DIFF), i.e. slightly below 'central' for C_g < C_tot.
      'high'    : the datasheet's rising current-noise curve added as an
                  independent term on top of 'central'.  If that curve is the
                  e_n*w*C_in coupling itself, this double counts it, so it is
                  an upper bound.
    R_s, C_D: optional photodiode series resistance and junction capacitance;
    the Johnson noise of R_s drives a current 4kT R_s (w C_D)^2 into the node.

    The 'central' total is Eq. (19) of the note, term by term:
        S_i = 4 k_B T / R_F                 'RF'   Johnson noise of R_F
            + i_n^2                         'i_n'  amplifier current noise (white level)
            + e_n(f)^2 [1/R_F^2 + (w C_tot)^2]   'e_n'  voltage noise through 1/R_F and
                                                    C_tot = C_T + C_F (the e_n term of the
                                                    note's figures)
            + 2 q I_DC                      'shot' shot noise of the pair's I_1 + I_2
    with e_n(f) the datasheet curve (en_pts, interpolated by loglog_interp, its
    end values held outside it) or the flat value en_flat.  Eq. (23) is the 'low'
    bound and Eq. (24) names the three estimates (Section 3.7).  The result is
    input-referred, i.e. divided by |Z_T|: it does not depend on the loop gain.
    """
    f = np.asarray(f, dtype=float)
    w = 2 * np.pi * f
    en = loglog_interp(f, nz.en_pts, nz.en_flat)       # e_n(f) from the datasheet curve, or flat
    S_RF = np.full_like(f, 4 * K_B * T / R_F)            # Johnson noise of R_F (2.87 pA/rtHz at 2 kOhm)
    S_in = np.full_like(f, nz.in_flat ** 2)              # white current noise of the inverting input
    C_tot = C_T + C_F                                    # all capacitance that e_n drives (Eq. (19))
    S_en = en ** 2 * ((1 / R_F) ** 2 + (w * C_tot) ** 2)  # e_n through 1/R_F and through C_tot
    S_extra = np.zeros_like(f)
    if fet_model == "low" and nz.fet:
        Cg = nz.c_gate
        S_en = en ** 2 * ((1 / R_F) ** 2
                          + w ** 2 * (C_tot ** 2 - 0.25 * Cg * C_tot + 0.325 * Cg ** 2))
    elif fet_model == "high" and nz.in_pts:
        # datasheet current-noise curve above its white level, added independently;
        # the white level is taken as the minimum of the curve above 1 MHz
        S_extra = loglog_interp(f, nz.in_pts, nz.in_flat, extrapolate_high=True) ** 2 - nz.in_flat ** 2
        S_extra = np.where(f >= 1e6, np.clip(S_extra, 0, None), 0.0)
    S_rs = 4 * K_B * T * R_s * (w * C_D) ** 2
    S_shot = np.full_like(f, 2 * Q_E * i_dc)
    total = S_RF + S_in + S_en + S_extra + S_rs + S_shot
    return dict(RF=S_RF, i_n=S_in, e_n=S_en, fet_hf=S_extra, pd_rs=S_rs,
                shot=S_shot, total=total)


def band_average_penalty_db(f, S_total, S_ref, f_lo, f_hi):
    """10 log10 of the ratio of band-integrated PSDs (linear frequency integral)."""
    m = (f >= f_lo) & (f <= f_hi)
    return 10 * np.log10(np.trapezoid(S_total[m], f[m]) / np.trapezoid(S_ref[m], f[m]))


def integrated_rms(f, S, f_lo, f_hi, weight=None):
    """sqrt(integral S |weight|^2 df) between f_lo and f_hi."""
    m = (f >= f_lo) & (f <= f_hi)
    w2 = 1.0 if weight is None else np.abs(weight[m]) ** 2
    return float(np.sqrt(np.trapezoid(S[m] * w2, f[m])))


# ---------------------------------------------------------------------------
# Thermal and shot references
# ---------------------------------------------------------------------------
def johnson_current_asd(R, T=T_ROOM):
    return np.sqrt(4 * K_B * T / R)


def shot_current_asd(i_dc):
    return np.sqrt(2 * Q_E * i_dc)
