"""Model of a high-gain photodiode transimpedance amplifier (TIA).

The photodiode is a current source in parallel with its capacitance C_D and
shunt resistance R_sh.  The amplifier is a single-pole voltage amplifier,
A(s) = A0 / (1 + s A0 / (2 pi GBW)), with input capacitance C_CM + C_DIFF
from the inverting input to AC ground, voltage noise e_n(f) and current noise
i_n(f).  The feedback network is a two-port with short-circuit admittances
y11 (seen from the summing node with the output end grounded) and y21; it is
either a lumped R_F || C_F or a uniform distributed RC line of total
resistance R_F and total capacitance C_g to ground, with an end-to-end
capacitance C_ee in parallel (a chip resistor over a ground plane).

Exact relations used (Section 3.1 of the note):

    Z_T  = -1 / (y_f + Y_n / A),       y_f = -y21,   Y_n = Y_s + y11
    Y_s  = 1/R_sh + j w (C_D + C_CM + C_DIFF + C_stray)
    noise referred to the photocurrent (A^2/Hz):
        feedback network   4 k T Re{y11}
        photodiode shunt   4 k T / R_sh          (zero bias)
        dark current       2 q I_dark            (reverse bias)
        signal shot noise  2 q I_ph
        amplifier current  i_n(f)^2
        amplifier voltage  e_n(f)^2 |Y_n|^2      (exact, no loop-gain factor)

For the uniform RC line with theta = sqrt(j w R C_g):
    y11 = (theta / R) coth(theta) + j w C_ee
    y21 = -(theta / R) / sinh(theta) - j w C_ee
which reduce to 1/R + j w C_ee and -(1/R) - j w C_ee for C_g -> 0.
"""
from __future__ import annotations

import json
import math
import pathlib
from dataclasses import dataclass, field

import numpy as np

K_B = 1.380649e-23        # J/K
Q_E = 1.602176634e-19     # C
T_REF = 298.15            # K, 25 C, the temperature of the datasheet tables
FOUR_KT = 4.0 * K_B * T_REF
A0_DEFAULT = 1.0e6        # 120 dB open-loop DC gain for the single-pole model

DATA = pathlib.Path(__file__).resolve().parent.parent / "data"


# ---------------------------------------------------------------- amplifiers
@dataclass
class Amp:
    name: str
    gbw: float                  # Hz
    min_gain: float
    en_pts: list                # [(f, V/rtHz)]
    in_pts: list                # [(f, A/rtHz)]
    c_in: float                 # F, C_CM + C_DIFF
    ib_typ: float               # A
    ib_max25: float | None      # A
    ib_hot: dict = field(default_factory=dict)   # {"85": A, "125": A}
    vos_max: float | None = None                 # V
    input: str = ""
    supply: str = ""
    c_known: bool = True
    a0: float = A0_DEFAULT                       # DC open-loop gain (V/V)
    # optional shape of the open-loop gain beyond a single pole: [(f, |H|, phase in degrees)],
    # A(f) = single pole x H(f); H = 1 below the first point, the last point held above the last
    aol_shape: list = field(default_factory=list)
    max_rf: float | None = None                  # the sweep evaluates the part only up to this R_F

    def en(self, f: np.ndarray) -> np.ndarray:
        return _loglog(self.en_pts, f)

    def shape(self, f: np.ndarray) -> np.ndarray:
        f = np.asarray(f, dtype=float)
        if not self.aol_shape:
            return np.ones_like(f, dtype=complex)
        pts = sorted(self.aol_shape)
        lf = np.log10([p[0] for p in pts])
        lm = np.log10([p[1] for p in pts])
        ph = np.radians([p[2] for p in pts])
        x = np.log10(np.maximum(f, 1e-30))
        mag = 10.0 ** np.interp(x, np.r_[lf[0] - 3.0, lf], np.r_[0.0, lm])
        phase = np.interp(x, np.r_[lf[0] - 3.0, lf], np.r_[0.0, ph])
        return mag * np.exp(1j * phase)

    def in_(self, f: np.ndarray) -> np.ndarray:
        """Current noise.  Where the datasheet gives only a curve that starts above 1 kHz
        and rises with frequency (OPA818, LTC6268-10), the rise is continued below its first
        point with the slope from that point to the first point at least a decade above it,
        and the shot noise of the typical bias
        current, sqrt(2 q I_B), is added in quadrature there as the floor that a gate current
        cannot go below.  Otherwise the datasheet values are interpolated, flat outside."""
        out = _loglog(self.in_pts, f)
        pts = sorted(self.in_pts)
        f = np.asarray(f, dtype=float)
        # the slope of the rise: from the first point to the first point a decade or more above
        later = [p for p in pts if p[0] >= 10 * pts[0][0]] if pts else []
        if len(pts) >= 2 and pts[0][0] > 1e3 and later and later[0][1] > pts[0][1] and self.ib_typ > 0:
            (f0, v0), (f1_, v1) = pts[0], later[0]
            slope = math.log10(v1 / v0) / math.log10(f1_ / f0)
            low = f < f0
            rise = v0 * (f[low] / f0) ** slope
            out = out.copy()
            out[low] = np.sqrt(rise ** 2 + 2 * Q_E * self.ib_typ)
        return out


def _loglog(points: list, f: np.ndarray) -> np.ndarray:
    """Interpolate a noise density in log-log between datasheet points.

    Below the first point and above the last the density is held flat, except
    that a set whose first point lies at or below 1 kHz and whose two lowest
    points fall with frequency is continued below the first point with the
    slope of those two points (flicker noise), capped at the 1/f slope of the
    power density.  A set that starts above 1 kHz says nothing about flicker
    noise and is held flat below its first point.
    """
    pts = sorted(points)
    fx = np.array([p[0] for p in pts], dtype=float)
    vx = np.array([p[1] for p in pts], dtype=float)
    f = np.asarray(f, dtype=float)
    if len(fx) == 1:
        return np.full_like(f, vx[0])
    lf, lv = np.log10(fx), np.log10(vx)
    out = np.interp(np.log10(f), lf, lv)
    slope = (lv[1] - lv[0]) / (lf[1] - lf[0])
    if slope < 0 and fx[0] <= 1e3:
        slope = max(slope, -0.5)
        low = np.log10(f) < lf[0]
        out[low] = lv[0] + slope * (np.log10(f[low]) - lf[0])
    return 10.0 ** out


def load_amps(path: pathlib.Path | None = None) -> dict[str, Amp]:
    data = json.loads((path or DATA / "amplifiers.json").read_text(encoding="utf-8"))
    amps: dict[str, Amp] = {}
    for name, p in data["parts"].items():
        c_cm, c_diff = p.get("c_cm"), p.get("c_diff")
        c_known = c_cm is not None
        c_in = ((c_cm or 0.0) + (c_diff or 0.0)) * 1e-12 if c_known else 8e-12
        amps[name] = Amp(
            name=name,
            gbw=p["gbw"] * 1e6,
            min_gain=p.get("min_gain", 1),
            en_pts=[(float(k), v * 1e-9) for k, v in p["en"].items()],
            in_pts=[(float(k), v * 1e-15) for k, v in p["in_"].items()],
            c_in=c_in,
            ib_typ=(p.get("ib_typ") or 0.0) * 1e-15,
            ib_max25=(p["ib_max25"] * 1e-15) if p.get("ib_max25") else None,
            ib_hot={k: v * 1e-15 for k, v in p.get("ib_hot", {}).items()},
            vos_max=(p["vos_max_uV"] * 1e-6) if p.get("vos_max_uV") else None,
            input=p.get("input", ""),
            supply=p.get("supply", ""),
            c_known=c_known,
            a0=10 ** (p["aol_db"] / 20) if p.get("aol_db") else A0_DEFAULT,
            aol_shape=[(float(f), float(mg), float(ph)) for f, mg, ph in p.get("aol_shape", [])],
            max_rf=p.get("max_rf"),
        )
    return amps


# ------------------------------------------------------- feedback networks
def lumped_y(w: np.ndarray, rf: float, cf: float):
    y11 = 1.0 / rf + 1j * w * cf
    return y11, -y11


def urc_y(w: np.ndarray, rf: float, cg: float, cee: float):
    """Short-circuit admittances of a uniform RC line (R = rf, C = cg to
    ground) with an end-to-end capacitance cee in parallel."""
    if cg <= 0:
        return lumped_y(w, rf, cee)
    theta = np.sqrt(1j * w * rf * cg)
    e2 = np.exp(-2.0 * theta)
    small = np.abs(theta) < 1e-3
    coth = np.where(small, 1.0, (1.0 + e2) / (1.0 - e2 + 1e-300))
    csch = np.where(small, 1.0, 2.0 * np.exp(-theta) / (1.0 - e2 + 1e-300))
    # series expansions where theta is tiny (avoid 0/0)
    t2 = theta ** 2
    y11 = np.where(small, (1.0 + t2 / 3.0) / rf, theta * coth / rf)
    y21 = np.where(small, -(1.0 - t2 / 6.0) / rf, -theta * csch / rf)
    return y11 + 1j * w * cee, y21 - 1j * w * cee


def ladder_y(w: np.ndarray, rf: float, cg: float, cee: float, n: int, profile):
    """Feedback admittances of an n-section RC ladder (series rf/n; capacitance cg/n
    from each internal node, cg/(2n) from each end node, to a plane or strip) with
    cee across the ends.  profile(x) gives, for a node at fractional position x
    (0 = summing-node end, 1 = output end), the potential of the conductor under it
    as a fraction of the output voltage: 0 for a grounded plane, 1 for a plane
    driven from the output, 1/3 for a plane driven at one third of the output, x
    for an ideal graded guard (no voltage across the capacitance, as in a
    capacitively coupled distributed resistor).  Returns (y11, y_f) with
    I1 = y11 V1 - y_f V2 the current from the summing node into the network."""
    w = np.atleast_1d(np.asarray(w, dtype=float))
    x = np.arange(n + 1) / n
    a = np.array([profile(xi) for xi in x], dtype=float)
    c = np.full(n + 1, cg / n)
    c[0] = c[-1] = cg / (2 * n)
    g = n / rf
    y11 = np.empty(w.size, dtype=complex)
    yf = np.empty(w.size, dtype=complex)
    inner = np.arange(1, n)
    for k, wk in enumerate(w):
        yc = 1j * wk * c
        # internal nodes: g(2V_i - V_{i-1} - V_{i+1}) + yc_i (V_i - a_i V2) = 0
        m = np.zeros((n - 1, n - 1), dtype=complex)
        for row, i in enumerate(inner):
            m[row, row] = 2 * g + yc[i]
            if row > 0:
                m[row, row - 1] = -g
            if row < n - 2:
                m[row, row + 1] = -g
        # right-hand sides for V1 = 1 (V2 = 0) and for V2 = 1 (V1 = 0)
        b1 = np.zeros(n - 1, dtype=complex)
        b1[0] = g
        b2 = yc[inner] * a[inner]
        b2[-1] += g
        v_a = np.linalg.solve(m, b1)
        v_b = np.linalg.solve(m, b2)
        # current from node 0 into the network: g (V0 - V1node) + yc_0 (V0 - a_0 V2)
        i_a = g * (1.0 - v_a[0]) + yc[0]
        i_b = g * (0.0 - v_b[0]) - yc[0] * a[0]
        y11[k] = i_a + 1j * wk * cee
        yf[k] = -(i_b - 1j * wk * cee)
    return y11, yf


# ------------------------------------------------------------ the circuit
@dataclass
class Source:
    name: str
    c_d: float          # F
    r_sh: float         # Ohm (np.inf for an ideal diode)
    i_dark: float = 0.0  # A, used for reverse bias
    biased: bool = False  # False: zero bias, shunt thermal noise 4kT/R_sh


@dataclass
class Design:
    amp: Amp
    rf: float
    cf: float           # total lumped feedback capacitance, or C_ee for URC
    src: Source
    c_stray: float = 1e-12
    cg: float = 0.0     # distributed capacitance of R_F to ground (URC)
    a0: float | None = None   # DC open-loop gain; None takes the amplifier's own
    i_ph: float = 0.0

    def amp_gain(self, w: np.ndarray) -> np.ndarray:
        a0 = self.amp.a0 if self.a0 is None else self.a0
        wp = 2.0 * math.pi * self.amp.gbw / a0
        a = a0 / (1.0 + 1j * w / wp)
        if self.amp.aol_shape:
            a = a * self.amp.shape(np.asarray(w, dtype=float) / (2.0 * math.pi))
        return a

    def y_fb(self, w: np.ndarray):
        if self.cg > 0:
            return urc_y(w, self.rf, self.cg, self.cf)
        return lumped_y(w, self.rf, self.cf)

    def node(self, w: np.ndarray):
        c_node = self.src.c_d + self.amp.c_in + self.c_stray
        g_sh = 0.0 if not np.isfinite(self.src.r_sh) else 1.0 / self.src.r_sh
        y_s = g_sh + 1j * w * c_node
        y11, y21 = self.y_fb(w)
        return y_s, y11, -y21

    def zt(self, f: np.ndarray) -> np.ndarray:
        w = 2.0 * math.pi * np.asarray(f, dtype=float)
        y_s, y11, y_f = self.node(w)
        return -1.0 / (y_f + (y_s + y11) / self.amp_gain(w))

    def loop_gain(self, f: np.ndarray) -> np.ndarray:
        w = 2.0 * math.pi * np.asarray(f, dtype=float)
        y_s, y11, y_f = self.node(w)
        return self.amp_gain(w) * y_f / (y_s + y11)

    def noise(self, f: np.ndarray) -> dict[str, np.ndarray]:
        """Input-referred noise power densities, A^2/Hz."""
        f = np.asarray(f, dtype=float)
        w = 2.0 * math.pi * f
        y_s, y11, _ = self.node(w)
        y_n = y_s + y11
        g_sh = 0.0 if not np.isfinite(self.src.r_sh) else 1.0 / self.src.r_sh
        en = self.amp.en(f)
        c_node = self.src.c_d + self.amp.c_in + self.c_stray
        # split e_n|Y_n|^2 into its conductive and capacitive parts for the
        # dominance maps; their sum is the exact e_n^2 |Y_n|^2 for a lumped
        # network and close to it for the URC network
        g_dc = g_sh + 1.0 / self.rf
        out = {
            "R_F": FOUR_KT * np.real(y11),
            "shunt": np.full_like(f, 0.0 if self.src.biased else FOUR_KT * g_sh),
            "dark": np.full_like(f, 2 * Q_E * self.src.i_dark if self.src.biased else 0.0),
            "signal": np.full_like(f, 2 * Q_E * self.i_ph),
            "i_n": self.amp.in_(f) ** 2,
            "e_n": en ** 2 * np.abs(y_n) ** 2,
            "e_n_G": en ** 2 * g_dc ** 2,
            "e_n_C": en ** 2 * (w * (c_node + self.cf + self.cg / 3.0)) ** 2,
        }
        out["total"] = out["R_F"] + out["shunt"] + out["dark"] + out["signal"] \
            + out["i_n"] + out["e_n"]
        return out


# ----------------------------------------------------------- design rules
def response_metrics(d: Design, f: np.ndarray) -> dict:
    zt = np.abs(d.zt(f))
    z0 = zt[0]
    peak_db = 20 * math.log10(zt.max() / z0)
    below = np.nonzero(zt < z0 / math.sqrt(2.0))[0]
    f3 = float(f[below[0]]) if below.size else float("nan")
    t = d.loop_gain(f)
    cross = np.nonzero(np.abs(t) < 1.0)[0]
    if cross.size:
        i = cross[0]
        pm = 180.0 + math.degrees(np.angle(t[i]))
        fx = float(f[i])
        y_s, y11, y_f = d.node(2.0 * math.pi * f[i:i + 1])
        ng_x = float(np.abs((y_s + y11) / y_f)[0])
    else:
        pm, fx, ng_x = float("nan"), float("nan"), float("nan")
    return {"f3": f3, "peak_db": peak_db, "pm": pm, "fx": fx, "ng_at_fx": ng_x}


def choose_cf(amp: Amp, rf: float, src: Source, c_par: float, c_stray: float = 1e-12,
              cg: float = 0.0, peak_max_db: float = 0.1, f: np.ndarray | None = None):
    """Smallest feedback capacitance >= c_par whose response peaks by no more
    than peak_max_db (0.1 dB: within 0.1 dB of maximally flat)."""
    if f is None:
        f = np.logspace(-2, 9, 2200)
    grid = c_par * np.logspace(0, 3.5, 400)
    for cf in grid:
        d = Design(amp, rf, cf, src, c_stray=c_stray, cg=cg)
        m = response_metrics(d, f)
        if m["peak_db"] <= peak_max_db:
            m["cf"] = float(cf)
            m["limited_by"] = "resistor" if cf == grid[0] else "amplifier"
            return d, m
    d = Design(amp, rf, grid[-1], src, c_stray=c_stray, cg=cg)
    m = response_metrics(d, f)
    m["cf"] = float(grid[-1])
    m["limited_by"] = "unresolved"
    return d, m


def integrate(f: np.ndarray, s: np.ndarray, f1: float, f2: float) -> float:
    sel = (f >= f1) & (f <= f2)
    if sel.sum() < 2:
        return 0.0
    return float(np.trapezoid(s[sel], f[sel]))


def butterworth_cf(c_t: float, rf: float, gbw: float) -> float:
    """Maximally flat C_F of the two-pole TIA response, Eq. (22) of the note,
    C_F = sqrt(C_T / (pi R_F GBW)), with C_T the total node capacitance."""
    return math.sqrt(c_t / (math.pi * rf * gbw))
