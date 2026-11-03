"""Analytical loop gain, transimpedance, noise, output ceiling and dynamic range of the composite
TIAs at the survey's baseline (1 pF photodiode, 0.35 pF board, R_F = 2 kOhm, 150-MHz band).

High-voltage composite (Section 11.6).  A fast low-noise first stage (OPA859) inverts at the
summing node and drives a high-voltage current-feedback stage (THS3491, non-inverting gain G2)
inside the R_F loop.  Two topologies:
  plain  R_F || C_F from the high-voltage output v2 to the summing node v_s;
  dual   as plain, plus C_L from the first stage's output v1 to the summing node (a local loop).
The first stage is a Thevenin source E = A1 (e1 - v_s) behind its open-loop output impedance Z_o
(e1 is its input voltage noise); the second stage gives v2 = H2 (v1 + e2) and loads v1 with Y_in2.
The two node equations (Eq. (72))
  (Y_T + Y_F + Y_L) v_s - (Y_L + Y_F H2) v1 = i_in + Y_F H2 e2
  (A1 - Y_L Z_o) v_s + (1 + Z_o (Y_in2 + Y_L)) v1 = A1 e1
with Y_T = j w C_T (photodiode, board, first-stage input), Y_F = 1/R_F + j w C_F and Y_L = j w C_L
give the transimpedance Z_T = v2 / i_in, the loop gain at the first stage's output (Eq. (73))
  T = A1 K / (1 + Z_o (Y_in2 + Y_L - Y_L K)),   K = (Y_L + Y_F H2) / Y_s,  Y_s = Y_T + Y_F + Y_L,
and each noise source's input-referred transfer (its v2 divided by Z_T).  With Z_o = 0 they reduce
to T = A1 (Y_L + H2 Y_F) / Y_s, with e1 seen through |Y_s| and e2 through |Y_L + Y_s/A1|.
H2 is Eq. (71): H2 = G(s) / (1 + (R_F2 + G(s) Z_i) / Z_OL),  G(s) = 1 + R_F2/R_G2 + s R_F2 C_n.

Two descriptions of the stages:
  macromodels  the OPA859 macromodel's gain from the inverting input (corrected from its 200-ohm
               load to open circuit), open-loop output impedance, input capacitance and e_n
               (Section 10: spice/runs/aol, spice/runs/params); the THS3491 macromodel's internal
               Z_OL and Z_i at 100 ohm with C_n = 1.2 pF (spice_composite_checks.py ths_zol), input
               50 kOhm || 1.5 pF.  The SPICE checks of the composites test this description.
  datasheet    the OPA859 from its datasheet (Fig 6-10 open loop, Z_o = 0, C_CM + C_DIFF, the e_n
               curve) with the THS3491 as above: its own Fig 8-22 open loop does not reproduce its
               Fig 8-1 closed loop above about 300 MHz (overlay_digitized.py), so it is not used for
               H2.  Input 50 kOhm || 1.2 pF (p9).
The THS3491's noise referred to its input, e2, is from its datasheet (e_n, i_n-, R_F2 and R_G2).
Ceiling: the smallest of the THS3491's recommended maximum output (Fig 9-4) and slew rate, and
|H2| times the first stage's swing and slew-rate limits.

Usage: python composite_tia.py [--out <json>]     (no simulation; about a minute)
       python composite_tia.py --fine              (the finer scan of Section 11.6; about 15 s)
"""
from __future__ import annotations

import argparse
import json
from functools import lru_cache
from pathlib import Path

import numpy as np

import tia_model as tm
from parts_db import PARTS
from run_analysis import C_PCB_NOM, noise_inputs, open_loop_model

HERE = Path(__file__).resolve().parent
SPICE = HERE.parent / "spice"
Q_E, KT = 1.602176634e-19, tm.K_B * tm.T_ROOM
R_F, C_D, B = 2000.0, 1e-12, 150e6
F = np.logspace(5, np.log10(5e9), 1500)

# ---------------------------------------------------------------- THS3491 (SBOS875C)
# Fig 8-22 (p16): open-loop transimpedance (dBohm) and phase (deg), no load.  Every value is the
# figure's vector path read at that frequency with the plot frame (334.0, 326.1)-(525.4, 461.1) pt
# as calibration: 100 Hz-1 GHz, 140-40 dBohm, 0 to -150 deg (overlay_digitized.py draws them on
# the figure and prints the residuals; data/digitization_checks/).  The low-frequency plateau is
# 138.1 dBohm.  The phase trace leaves the plot at -149.4 deg, 770 MHz.
ZOL_F = np.array([1e5, 3e5, 1e6, 3e6, 1e7, 2e7, 5e7, 7e7, 1e8, 1.5e8, 2e8, 2.5e8, 3e8, 3.5e8, 4e8, 4.5e8,
                  5e8, 5.5e8, 6e8, 6.5e8, 7e8, 7.5e8, 7.69e8, 8e8, 9e8, 9.567e8])
ZOL_DB = np.array([126.92, 117.62, 107.17, 97.64, 87.19, 81.15, 73.20, 70.27, 67.17, 63.70, 61.21, 59.30,
                   57.73, 56.56, 55.66, 54.86, 54.19, 53.59, 53.07, 52.65, 52.27, 51.96, 51.85, 51.68, 51.22,
                   51.01])
ZOL_PH = np.array([-85.54, -88.45, -89.57, -90.02, -90.64, -91.38, -93.54, -94.94, -97.10, -100.63, -104.15,
                   -107.55, -110.57, -113.21, -116.63, -120.59, -124.55, -128.75, -133.07, -137.61, -142.29,
                   -147.21, -149.30, np.nan, np.nan, np.nan])
# beyond 769 MHz the phase is extrapolated linearly in f (a delay) from 600-769 MHz
R_I = 15.0                                   # inverting-input resistance, typ (p9)
# capacitance at the inverting node: the datasheet states none; TI's model (SBOMBP9) has 1.2 pF
# at its internal inverting node (C_C12), which reproduces the model's closed loop (Eq. (71))
C_N2 = 1.2e-12
RF2_TABLE = {2: 976.0, 5: 576.0, 10: 499.0, 20: 383.0}   # Table 9-2, RGT package (p27)
# Fig 9-4 (p29): maximum recommended output voltage (Vpp) against frequency (MHz).  The curves are
# straight lines in log f between tabulated points; these are those vertices, read off the vector
# paths with the frame (217.5, 186.7)-(408.0, 321.7) pt: 1-1000 MHz, 30-0 V.
VMAX_15_F = np.array([1.0, 10.0, 20.0, 30.0, 40.0, 50.0, 60.1, 70.0, 80.0, 90.0, 100.0, 105.0, 110.0, 120.0,
                      150.0, 165.0, 185.0, 205.0, 229.9, 254.8, 279.9, 304.8, 330.0, 355.0, 379.9, 404.6, 429.7,
                      439.7, 455.1, 475.1, 499.9, 524.8]) * 1e6
VMAX_15 = np.array([26.00, 26.00, 25.00, 24.50, 24.00, 23.00, 22.00, 21.50, 21.00, 20.51, 20.10, 20.00, 17.83,
                    15.89, 14.17, 12.62, 11.26, 10.03, 8.94, 7.97, 7.11, 6.33, 5.65, 5.04, 4.49, 4.00, 3.57, 3.18,
                    2.84, 2.53, 2.25, 2.01])
VMAX_7p5_F = np.array([1.0, 10.0, 20.0, 30.0, 40.0, 50.0, 60.1, 70.0, 80.0, 90.0, 100.0, 115.1, 135.0, 150.0,
                       165.0, 185.0, 205.0, 229.9, 249.8, 270.0, 294.7, 324.9, 374.7, 399.7, 449.6, 499.9]) * 1e6
VMAX_7p5 = np.array([12.01, 12.01, 12.01, 11.76, 11.76, 11.76, 11.76, 11.51, 11.00, 10.51, 10.21, 10.01, 8.94,
                     7.97, 7.11, 6.33, 5.65, 5.04, 4.49, 4.00, 3.57, 3.18, 2.84, 2.53, 2.25, 2.01])
# Fig 8-13 / 8-14 (p15): HD2 and HD3 (dBc) against output swing (Vpp) at 100 MHz, G = 5, +/-15 V,
# R_L = 100 ohm and 1 kOhm; vector paths read with the frames (96.2, 130.4)-(287.2, 265.4) and
# (345.0, 130.4)-(536.0, 265.4) pt: 0-25 Vpp, 0 to -120 dBc.  The p8 table gives -60 / -51 dBc at
# 100 MHz, 10 Vpp, which the 100-ohm curves reproduce (-60.3 / -51.3).
HD_VPP = np.array([1.0, 2.5, 5.0, 7.5, 10.0, 12.5, 15.0, 17.5, 20.0, 22.5, 24.0])
HD2_100M = dict(rl100=np.array([-73.66, -68.10, -64.24, -62.20, -60.29, -58.30, -56.37, -54.17, -51.23, -44.69, -38.35]),
                rl1k=np.array([-75.49, -67.51, -61.14, -58.01, -56.00, -54.36, -52.91, -51.49, -50.08, -48.65, -47.84]))
HD3_100M = dict(rl100=np.array([-72.57, -70.34, -57.80, -53.42, -51.31, -50.58, -50.41, -49.71, -46.91, -34.09, -19.67]),
                rl1k=np.array([-74.61, -62.12, -54.04, -51.19, -50.43, -50.97, -51.98, -52.72, -52.05, -44.77, -36.00]))
THS = dict(sr=8000.0, swing_15=13.5, en=1.7e-9, inp=15e-12, inn=20e-12)   # p1, p8-p9
THS_ZIN = dict(macromodels=(50e3, 1.5e-12), datasheet=(50e3, 1.2e-12))   # model G_G5, C_C11; datasheet p9


def rf2_for(g2):
    """Gain-setting R_F2 for a non-inverting gain g2, interpolated in Table 9-2."""
    gs = np.array(sorted(RF2_TABLE))
    return float(np.interp(g2, gs, [RF2_TABLE[g] for g in gs]))


def zol(f):
    """THS3491 open-loop transimpedance (complex, ohm): the digitized curve, phase extended beyond
    769 MHz with the slope (delay) of 600-769 MHz, magnitude beyond 957 MHz with its last slope."""
    f = np.asarray(f, float)
    lf = np.log10(f)
    mag_db = np.interp(lf, np.log10(ZOL_F), ZOL_DB)
    hi = lf > np.log10(ZOL_F[-1])
    slope = (ZOL_DB[-1] - ZOL_DB[-4]) / (np.log10(ZOL_F[-1]) - np.log10(ZOL_F[-4]))
    mag_db = np.where(hi, ZOL_DB[-1] + slope * (lf - np.log10(ZOL_F[-1])), mag_db)
    ok = np.isfinite(ZOL_PH)
    fp, pp = ZOL_F[ok], ZOL_PH[ok]
    ph = np.interp(lf, np.log10(fp), pp)
    d = (pp[-1] - pp[-4]) / (fp[-1] - fp[-4])           # deg per Hz above 600 MHz
    ph = np.where(f > fp[-1], pp[-1] + d * (f - fp[-1]), ph)
    ph = np.where(f < fp[0], pp[0], ph)
    return 10 ** (mag_db / 20) * np.exp(1j * np.radians(ph))


def h2(f, g2, c_n=None, zol_fn=None):
    """THS3491 closed-loop non-inverting gain g2 with Table 9-2's R_F2 (current feedback, Eq. (71)):
    H2 = G(s) / (1 + (R_F2 + G(s) r_i) / Z_OL),  G(s) = 1 + R_F2/R_G2 + s R_F2 C_n,
    where C_n is the capacitance at the inverting node (it acts across R_G2).  c_n = 0 gives the
    textbook form G / (1 + (R_F2 + G r_i)/Z_OL)."""
    c_n = C_N2 if c_n is None else c_n
    rf2 = rf2_for(g2)
    gs = g2 + 2j * np.pi * np.asarray(f, float) * rf2 * c_n
    return gs / (1 + (rf2 + gs * R_I) / (zol_fn or zol)(f))


def _interp_c(f, fx, z):
    """Complex response at f from samples: log-f interpolation of log|z| and of the unwrapped phase."""
    lf, lx = np.log10(np.asarray(f, float)), np.log10(fx)
    return np.exp(np.interp(lf, lx, np.log(np.abs(z))) + 1j * np.interp(lf, lx, np.unwrap(np.angle(z))))


@lru_cache(maxsize=None)
def _ths_internal(load):
    a = np.load(SPICE / "runs" / "composite" / "ths_zol" / f"zol_internal_{load}.npy")
    return a[0], a[1] + 1j * a[2], a[3] + 1j * a[4]


def h2_model(f, g2, load="RL100", c_n=None):
    """Eq. (71) with the THS3491 macromodel's internal Z_OL and error-current path impedance Z_i
    (spice_composite_checks.py ths_zol) and C_n = 1.2 pF."""
    fz, zol_m, zi_m = _ths_internal(load)
    c_n = C_N2 if c_n is None else c_n
    rf2 = rf2_for(g2)
    f = np.asarray(f, float)
    gs = g2 + 2j * np.pi * f * rf2 * c_n
    return gs / (1 + (rf2 + gs * _interp_c(f, fz, zi_m)) / _interp_c(f, fz, zol_m))


def e2_density(g2):
    """THS3491 noise referred to its non-inverting input (V/rtHz): e_n, i_nn R_F2 and the Johnson
    noise of R_F2 and R_G2, divided by g2; i_np sees the first stage's few-ohm output (negligible)."""
    rf2 = rf2_for(g2)
    rg2 = rf2 / (g2 - 1)
    out2 = (THS["en"] * g2) ** 2 + (THS["inn"] * rf2) ** 2 + 4 * KT * rf2 + 4 * KT * rf2 ** 2 / rg2
    return float(np.sqrt(out2) / g2)


def vmax_ths(f0, supply=15):
    """Fig 9-4 amplitude (V, half the Vpp), interpolated in log f as the figure is drawn."""
    fv, vv = (VMAX_15_F, VMAX_15) if supply == 15 else (VMAX_7p5_F, VMAX_7p5)
    return float(np.interp(np.log10(f0), np.log10(fv), vv)) / 2


# ---------------------------------------------------------------- generic loop metrics
def metrics(f, T, Z, r_f=R_F):
    """Crossover, phase margin, gain margin (at the first -180 deg crossing after the crossover;
    None when the phase stays above -180 deg up to the grid's end), second crossing, and the
    transimpedance's -3 dB frequency and peaking relative to its low-frequency value."""
    magT = np.abs(T)
    phT = np.degrees(np.unwrap(np.angle(T)))
    out = dict(f_c_MHz=None, pm_deg=None, gm_dB=None, second=False)
    idx = np.where((magT[:-1] >= 1) & (magT[1:] < 1))[0]
    if len(idx):
        i = idx[0]
        x0, x1 = np.log10(f[i]), np.log10(f[i + 1])
        y0, y1 = np.log10(magT[i]), np.log10(magT[i + 1])
        xc = x0 - y0 * (x1 - x0) / (y1 - y0)
        out["f_c_MHz"] = 10 ** xc / 1e6
        out["pm_deg"] = 180 + float(np.interp(xc, [x0, x1], [phT[i], phT[i + 1]]))
        out["second"] = bool(np.any(magT[f > 1.2 * 10 ** xc] >= 1))
        k = np.where((phT[i:-1] > -180) & (phT[i + 1:] <= -180))[0]
        if len(k):
            j = i + k[0]
            out["gm_dB"] = float(-20 * np.log10(np.interp(-180, [phT[j + 1], phT[j]], [magT[j + 1], magT[j]])))
    H = np.abs(Z)
    out["peak_dB"] = float(max(0.0, 20 * np.log10(H.max() / H[0])))
    below = np.where(H < H[0] / np.sqrt(2))[0]
    out["f3_MHz"] = None
    if len(below) and below[0] > 0:
        j = below[0]
        out["f3_MHz"] = float(10 ** np.interp(H[0] / np.sqrt(2), [H[j], H[j - 1]],
                                              [np.log10(f[j]), np.log10(f[j - 1])]) / 1e6)
    return out


def _worse(a, b, sense):
    """The worse of two figures (sense -1: smaller is worse; +1: larger is worse); None counts as
    no limit (a gain margin that never occurs, a -3 dB point beyond the grid)."""
    if a is None:
        return b
    if b is None:
        return a
    return min(a, b) if sense < 0 else max(a, b)


def band(f, S, b=B):
    """Integral of S (A^2/Hz) over 0..b, held at S(f[0]) below the first point."""
    inside = f < b
    ff = np.concatenate([f[inside], [b]])
    ss = np.concatenate([S[inside], [np.interp(np.log10(b), np.log10(f), S)]])
    return float(np.trapezoid(ss, ff) + ss[0] * ff[0])


def dr_db(i_max_rms, noise_rms, i_dc):
    return float(20 * np.log10(i_max_rms / np.sqrt(noise_rms ** 2 + 2 * Q_E * i_dc * B)))


# ---------------------------------------------------------------- high-voltage composite
STAGE1 = "OPA859"
RL_AOL = 200.0          # load of the OPA859 macromodel's open-loop extraction (Section 10, 'aol')


class Stage1:
    """The first stage as a Thevenin source: gain A1 from the inverting input, open-loop output
    impedance Z_o, its capacitance at the summing node and its input voltage noise e_n."""

    def __init__(self, flavour):
        p = PARTS[STAGE1]
        self.flavour, self.dr, self.nz = flavour, p["dr"], noise_inputs(p)
        if flavour == "macromodels":
            a = np.load(SPICE / "runs" / "aol" / STAGE1 / "aol_inverting.npy")
            z = np.load(SPICE / "runs" / "params" / f"{STAGE1}_zout.npy")
            y = np.load(SPICE / "runs" / "params" / f"{STAGE1}_yin_grounded.npy")
            e = np.loadtxt(SPICE / "runs" / "params" / f"{STAGE1}_en" / "en.txt", skiprows=1)
            self._a, self._z, self._e = (a[0], a[1] + 1j * a[2]), (z[0], z[1] + 1j * z[2]), (e[:, 0], e[:, 1])
            self.c_in = float(np.interp(8.0, np.log10(y[0]), y[2] / (2 * np.pi * y[0])))
        else:
            self.ol, *_ = open_loop_model(p)
            self.c_in = p["c_cm"] + p["c_diff"]

    def Zo(self, f):
        if self.flavour == "macromodels":
            return _interp_c(f, *self._z)
        return np.zeros(np.shape(f), complex)

    def A(self, f):
        if self.flavour == "macromodels":
            return _interp_c(f, *self._a) * (RL_AOL + self.Zo(f)) / RL_AOL
        return self.ol.A(np.asarray(f, float))

    def e_n(self, f):
        if self.flavour == "macromodels":
            fe, en = self._e
            return np.exp(np.interp(np.log10(f), np.log10(fe), np.log(en)))
        return tm.loglog_interp(np.asarray(f, float), self.nz.en_pts, self.nz.en_flat)


class HVComposite:
    """Both stages tabulated on a frequency grid, for one second-stage gain."""

    def __init__(self, flavour, g2, f=F):
        self.flavour, self.g2, self.f = flavour, g2, np.asarray(f, float)
        self.s1 = Stage1(flavour)
        self.A, self.Zo, self.en = self.s1.A(self.f), self.s1.Zo(self.f), self.s1.e_n(self.f)
        self.H = h2_model(self.f, g2)
        r_in2, c_in2 = THS_ZIN[flavour]
        self.yin2 = 1 / r_in2 + 2j * np.pi * self.f * c_in2
        self.e2 = e2_density(g2)
        self.rf2 = rf2_for(g2)

    def c_t(self, c_d=C_D):
        return c_d + C_PCB_NOM + self.s1.c_in

    def solve(self, c_f, c_l, c_d=C_D, r_f=R_F):
        """Eqs. (72)-(73): loop gain T at the first stage's output, transimpedance Z_T = v2/i_in,
        and the input-referred transfers of e1 (A/V) and e2 (A/V)."""
        w = 2 * np.pi * self.f
        A, Zo, H, yin2 = self.A, self.Zo, self.H, self.yin2
        yT, yF, yL = 1j * w * self.c_t(c_d), 1 / r_f + 1j * w * c_f, 1j * w * c_l
        ys = yT + yF + yL
        a11, a12 = ys, -(yL + yF * H)
        a21, a22 = A - yL * Zo, 1 + Zo * (yin2 + yL)
        det = a11 * a22 - a12 * a21

        def v2(b1, b2, e2=0.0):
            return H * ((a11 * b2 - a21 * b1) / det + e2)

        Z = v2(1.0, 0.0)
        n_e1 = v2(0.0, A) / Z
        n_e2 = v2(yF * H, 0.0, 1.0) / Z
        K = (yL + yF * H) / ys
        T = A * K / (1 + Zo * (yin2 + yL - yL * K))
        return T, Z, n_e1, n_e2

    def noise(self, c_f, c_l, c_d=C_D, r_f=R_F):
        """Input-referred noise current PSD (A^2/Hz): total and parts."""
        T, Z, n1, n2 = self.solve(c_f, c_l, c_d, r_f)
        first = np.abs(n1) ** 2 * self.en ** 2 + self.s1.nz.in_flat ** 2
        second = np.abs(n2) ** 2 * self.e2 ** 2
        rf = np.full_like(self.f, 4 * KT / r_f)
        return dict(total=first + second + rf, first=first, second=second, rf=rf)

    def ceiling(self, f0, c_f, c_l, supply=15):
        """Largest undistorted output amplitude (V) at f0, its limit, and |Z_T(f0)|."""
        T, Z, *_ = self.solve(c_f, c_l)
        lf = np.log10(self.f)
        h0 = float(np.interp(np.log10(f0), lf, np.abs(self.H)))
        z0 = float(np.interp(np.log10(f0), lf, np.abs(Z)))
        s = self.s1.dr
        v1 = min((s["swing_light"][1] - s["swing_light"][0]) / 2, s["sr"] * 1e6 / (2 * np.pi * f0))
        lims = {"first stage (swing or slew rate) times |H2|": v1 * h0,
                f"THS3491 recommended maximum (Fig 9-4, +/-{supply} V)": vmax_ths(f0, supply),
                "THS3491 slew rate": THS["sr"] * 1e6 / (2 * np.pi * f0)}
        k = min(lims, key=lims.get)
        return lims[k], k, z0


def corners(c_f, c_l):
    """C_D +/- 0.2 pF and C_F +/- 0.1 pF (as Section 10), and C_L +/- 0.1 pF when C_L is used."""
    out = []
    for dcd in (-0.2e-12, 0.0, 0.2e-12):
        for dcf in (-0.1e-12, 0.0, 0.1e-12):
            for dcl in ((-0.1e-12, 0.0, 0.1e-12) if c_l > 0 else (0.0,)):
                out.append((C_D + dcd, max(c_f + dcf, 0.02e-12), c_l + dcl))
    return out


def hv_design(cmp, c_f, c_l, supply=15, with_corners=True):
    T, Z, *_ = cmp.solve(c_f, c_l)
    m = metrics(cmp.f, T, Z)
    worst = dict(pm_deg=m["pm_deg"], gm_dB=m["gm_dB"], peak_dB=m["peak_dB"], f3_MHz=m["f3_MHz"],
                 second=m["second"])
    if with_corners:
        for cd, cf, cl in corners(c_f, c_l):
            Tc, Zc, *_ = cmp.solve(cf, cl, c_d=cd)
            mc = metrics(cmp.f, Tc, Zc)
            if mc["pm_deg"] is None:                 # no crossover found: treat as failing
                worst["pm_deg"] = -999.0
            worst["pm_deg"] = _worse(worst["pm_deg"], mc["pm_deg"], -1)
            worst["gm_dB"] = _worse(worst["gm_dB"], mc["gm_dB"], -1)
            worst["peak_dB"] = _worse(worst["peak_dB"], mc["peak_dB"], +1)
            worst["f3_MHz"] = _worse(worst["f3_MHz"], mc["f3_MHz"], -1)
            worst["second"] = worst["second"] or mc["second"]
    nz = cmp.noise(c_f, c_l)
    n_rms = np.sqrt(band(cmp.f, nz["total"]))
    out = dict(flavour=cmp.flavour, g2=cmp.g2, rf2=cmp.rf2, c_f_pF=c_f * 1e12, c_l_pF=c_l * 1e12, nominal=m,
               worst=worst, noise_nA=n_rms * 1e9,
               noise_parts_nA={k: np.sqrt(band(cmp.f, v)) * 1e9 for k, v in nz.items() if k != "total"})
    for f0 in (100e6, 150e6):
        v, lim, zt = cmp.ceiling(f0, c_f, c_l, supply)
        imax = v / (np.sqrt(2) * zt)
        out[f"{f0/1e6:g}MHz"] = dict(v_pk=v, limit=lim, zt_ohm=zt,
                                    dr_dB={f"{i*1e3:g} mA": dr_db(imax, n_rms, i) for i in (0.0, 1e-4, 1e-3, 1e-2)})
    return out


# ---------------------------------------------------------------- discrete-FET composite
# Q1 (common source; gate = summing node g, drain = node x), Q2 (cascode; source x, gate at AC
# ground, drain = node d), R_D from d to V_DD, compensation C_N at d, the OPA859 as a unity-gain
# buffer from d (through an ideal level shift) to the output v_o, R_F || C_F from v_o to g.  With
# each FET's common-source two-port Y-parameters at its own operating point (y11, y12, y21, y22 for
# Q1; y'.. for Q2, whose gate-source voltage is -v_x and drain-source voltage v_d - v_x), the
# buffer gain B and input admittance Y_b, and Y_x = j w (C_D + C_PCB), the node equations are
# (Eq. (67)):
#   g:  (Y_x + Y_F + y11) v_g + y12 v_x - Y_F B v_d = i_in
#   x:  y21 v_g + (y22 + S') v_x - (y'12 + y'22) v_d = 0,         S' = y'11 + y'12 + y'21 + y'22
#   d:  -(y'21 + y'22) v_x + (1/R_D + j w C_N + Y_b + y'22) v_d = 0
# and v_o = B v_d.  The loop gain at the buffer's output (Eq. (68)) is T = -B v_d with the
# feedback side of R_F || C_F driven at 1 V (row g's right side Y_F, i_in = 0).  Noise: R_F and
# the gate current (2 q I_G) enter at g as currents; Q1's channel noise is a drain current y21 e_1
# (e_1: its input voltage noise with the gate AC-grounded) leaving node x, Q2's a current y'21 e_2
# from d to x; R_D's current enters at d; the buffer's e_b adds Y_F B e_b to row g and B e_b to
# v_o.  Device data: spice_composite_checks.py fet_devices (ngspice at the composite's operating
# point).
# Each design: device kind and model, drain (collector) resistor, gate current, and the operating
# point aimed at (V): gate/base v_g, source/emitter v_s (an ideal, noiseless DC source; 0 = ground),
# Q1's drain/collector v_x and Q2's v_d.  The bipolar designs (Infineon BFP740ESD, Infineon's
# Gummel-Poon model file bfp740esd-spice-v2.mdl) put the emitter at -V_BE so that the summing
# node sits near 0 V, and keep V_CE at about 2 V (V(BR)CEO 4.2 V min); r_b = RB + RE of the
# model's transistor for the base-resistance noise.
FET_DESIGN = {
    "LSBF862": dict(kind="fet", model="LSBF862", r_d=360.0, i_g=0.0, vdd=15.0, v_g=0.0, v_s=0.0, v_x=5.0, v_d=8.0),
    "CPH3910": dict(kind="fet", model="CPH3910", r_d=220.0, i_g=0.0, vdd=15.0, v_g=0.0, v_s=0.0, v_x=5.0, v_d=8.0),
    "CE3512K2": dict(kind="fet", model="CE3512K2", r_d=1100.0, i_g=1e-6, vdd=15.0, v_g=-0.5, v_s=0.0, v_x=2.0,
                     v_d=4.0),
    "BFP740ESD_1mA": dict(kind="bjt", model="BFP740ESD", r_d=11700.0, i_g=0.0, vdd=15.0, v_g=0.0, v_s=-0.73,
                          v_x=1.3, v_d=3.3, r_b=6.41),
    "BFP740ESD_3mA": dict(kind="bjt", model="BFP740ESD", r_d=3900.0, i_g=0.0, vdd=15.0, v_g=0.0, v_s=-0.76,
                          v_x=1.3, v_d=3.3, r_b=6.41),
    "BFP740ESD_10mA": dict(kind="bjt", model="BFP740ESD", r_d=1170.0, i_g=0.0, vdd=15.0, v_g=0.0, v_s=-0.79,
                           v_x=1.3, v_d=3.3, r_b=6.41),
}
FET_RL = 200.0                      # buffer output load (as the OPA859 TIA decks of Section 10)


class FETComposite:
    """The discrete-FET composite on a frequency grid, from the saved device data."""

    def __init__(self, dev, f=F):
        self.dev, self.f = dev, np.asarray(f, float)
        d = SPICE / "runs" / "composite" / "fet_devices" / dev
        self.y1 = [self._c(np.load(d / "y_J1.npy"), k) for k in (1, 2, 3, 4)]
        self.y2 = [self._c(np.load(d / "y_J2.npy"), k) for k in (1, 2, 3, 4)]
        e = np.load(d / "en.npy")
        self.e1 = np.exp(np.interp(np.log10(self.f), np.log10(e[0]), np.log(e[1])))
        b = np.load(d / "buffer.npy")
        self.B, self.Yb = self._c(b, 1), self._c(b, 2)
        self.eb = Stage1("macromodels").e_n(self.f)             # OPA859 input voltage noise
        self.design = FET_DESIGN[dev]
        dcf = d / "dc.json"
        self.dc = json.loads(dcf.read_text(encoding="utf-8")) if dcf.exists() else {}

    def _c(self, arr, k):
        """Row k of a saved complex array, on this grid (real and imaginary parts interpolated in
        log f; the admittances pass through zero phase, so log-magnitude interpolation is avoided)."""
        lf, lx = np.log10(self.f), np.log10(arr[0].real)
        return np.interp(lf, lx, arr[k].real) + 1j * np.interp(lf, lx, arr[k].imag)

    def solve(self, c_n, c_f, c_d=C_D, r_f=R_F):
        """Eqs. (67)-(68): T, Z_T = v_o / i_in, and the input-referred transfer of every noise source."""
        w = 2 * np.pi * self.f
        y11, y12, y21, y22 = self.y1
        z11, z12, z21, z22 = self.y2
        yx, yF = 1j * w * (c_d + C_PCB_NOM), 1 / r_f + 1j * w * c_f
        yN = 1 / self.design["r_d"] + 1j * w * c_n + self.Yb
        B = self.B
        S = z11 + z12 + z21 + z22
        M = np.zeros((len(self.f), 3, 3), complex)
        M[:, 0, 0], M[:, 0, 1], M[:, 0, 2] = yx + yF + y11, y12, -yF * B
        M[:, 1, 0], M[:, 1, 1], M[:, 1, 2] = y21, y22 + S, -(z12 + z22)
        M[:, 2, 1], M[:, 2, 2] = -(z21 + z22), yN + z22

        def vo(rhs, extra=0.0):
            v = np.linalg.solve(M, rhs[..., None])[..., 0]
            return B * (v[:, 2] + extra)

        one, zero = np.ones_like(self.f, complex), np.zeros_like(self.f, complex)
        Z = vo(np.stack([one, zero, zero], -1))
        # each FET's noise is its drain-current noise y21 e (e: its input voltage noise with the gate
        # AC-grounded): it flows from drain to source, so the gate node moves and every capacitance
        # there, C_gs included, carries noise current.  (A source in series with the gate terminal
        # instead would hold the intrinsic gate still and leave C_gs out.)
        n = dict(e1=vo(np.stack([zero, -y21, zero], -1)) / Z,
                 e2=vo(np.stack([zero, z21, -z21], -1)) / Z,
                 rd=vo(np.stack([zero, zero, one], -1)) / Z,
                 eb=vo(np.stack([yF * B, zero, zero], -1), extra=1.0) / Z,
                 # bipolar sources: a current at node x (Q1's collector shot noise), a current from d
                 # to x (Q2's), a current into x (Q2's base current, which leaves through its emitter),
                 # and a voltage in series with Q1's base terminal (its base resistance): with it the
                 # summing node moves but the transistor's own input capacitance carries no noise current
                 ix=vo(np.stack([zero, -one, zero], -1)) / Z,
                 ixd=vo(np.stack([zero, one, -one], -1)) / Z,
                 ix2=vo(np.stack([zero, one, zero], -1)) / Z,
                 series=vo(np.stack([-y11, -y21, zero], -1)) / Z)
        M_open = M.copy()
        M_open[:, 0, 2] = 0.0                                 # break at the buffer output
        v = np.linalg.solve(M_open, np.stack([yF, zero, zero], -1)[..., None])[..., 0]
        T = -B * v[:, 2]
        return T, Z, n

    def noise(self, c_n, c_f, c_d=C_D, r_f=R_F):
        T, Z, n = self.solve(c_n, c_f, c_d, r_f)
        d = self.design
        parts = dict(rf=np.full_like(self.f, 4 * KT / r_f), rd=np.abs(n["rd"]) ** 2 * 4 * KT / d["r_d"],
                     buffer=np.abs(n["eb"]) ** 2 * self.eb ** 2)
        if d["kind"] == "bjt":
            dc = self.dc
            parts.update(base=np.full_like(self.f, 2 * Q_E * dc["i_b1"]),
                         q1_collector=np.abs(n["ix"]) ** 2 * 2 * Q_E * dc["i_c1"],
                         q1_rb=np.abs(n["series"]) ** 2 * 4 * KT * d["r_b"],
                         q2=np.abs(n["ixd"]) ** 2 * 2 * Q_E * dc["i_c2"] + np.abs(n["ix2"]) ** 2 * 2 * Q_E * dc["i_b2"])
        else:
            parts.update(gate=np.full_like(self.f, 2 * Q_E * d["i_g"]), q1=np.abs(n["e1"]) ** 2 * self.e1 ** 2,
                         q2=np.abs(n["e2"]) ** 2 * self.e1 ** 2)
        parts["total"] = sum(parts.values())
        return parts

    def ceiling(self, f0, c_n, c_f):
        """The OPA859 buffer's swing and slew-rate limits at f0, and |Z_T(f0)|."""
        T, Z, n = self.solve(c_n, c_f)
        s = PARTS[STAGE1]["dr"]
        v = min((s["swing_light"][1] - s["swing_light"][0]) / 2, s["sr"] * 1e6 / (2 * np.pi * f0))
        return v, "OPA859 buffer (swing or slew rate)", float(np.interp(np.log10(f0), np.log10(self.f), np.abs(Z)))


def fet_design(cmp, c_n, c_f, with_corners=True):
    T, Z, _ = cmp.solve(c_n, c_f)
    m = metrics(cmp.f, T, Z)
    worst = dict(pm_deg=m["pm_deg"], gm_dB=m["gm_dB"], peak_dB=m["peak_dB"], f3_MHz=m["f3_MHz"], second=m["second"])
    if with_corners:
        for cd, cf, _ in corners(c_f, 0.0):
            Tc, Zc, _ = cmp.solve(c_n, cf, c_d=cd)
            mc = metrics(cmp.f, Tc, Zc)
            if mc["pm_deg"] is None:
                worst["pm_deg"] = -999.0
            worst["pm_deg"] = _worse(worst["pm_deg"], mc["pm_deg"], -1)
            worst["gm_dB"] = _worse(worst["gm_dB"], mc["gm_dB"], -1)
            worst["peak_dB"] = _worse(worst["peak_dB"], mc["peak_dB"], +1)
            worst["f3_MHz"] = _worse(worst["f3_MHz"], mc["f3_MHz"], -1)
            worst["second"] = worst["second"] or mc["second"]
    nz = cmp.noise(c_n, c_f)
    n_rms = np.sqrt(band(cmp.f, nz["total"]))
    out = dict(dev=cmp.dev, c_n_pF=c_n * 1e12, c_f_pF=c_f * 1e12, z_lf_ohm=float(abs(Z[0])), nominal=m, worst=worst,
               noise_nA=n_rms * 1e9, noise_parts_nA={k: np.sqrt(band(cmp.f, v)) * 1e9 for k, v in nz.items() if k != "total"})
    for f0 in (100e6, 150e6):
        v, lim, zt = cmp.ceiling(f0, c_n, c_f)
        imax = v / (np.sqrt(2) * zt)
        out[f"{f0/1e6:g}MHz"] = dict(v_pk=v, limit=lim, zt_ohm=zt,
                                    dr_dB={f"{i*1e3:g} mA": dr_db(imax, n_rms, i) for i in (0.0, 1e-4, 1e-3, 1e-2)})
    return out


CN_GRID_pF = (0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0, 10.0, 15.0, 20.0, 30.0, 45.0, 60.0, 80.0, 100.0)
CF_GRID_FET_pF = np.round(np.arange(0.10, 1.501, 0.05), 3)


def fet_scan(dev):
    cmp = FETComposite(dev)
    return cmp, [fet_design(cmp, cn * 1e-12, cf * 1e-12) for cn in CN_GRID_pF for cf in CF_GRID_FET_pF]


CF_GRID_pF = np.round(np.arange(0.10, 1.501, 0.025), 3)
CL_GRID_pF = (0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0)
G2_GRID = (2.0, 3.0, 4.0, 5.0, 6.0, 8.0)
CRITERIA = dict(pm=45.0, gm=3.0, peak=1.0, f3=150.0)


def robust(r, pm=CRITERIA["pm"], gm=CRITERIA["gm"], peak=CRITERIA["peak"], f3=CRITERIA["f3"]):
    w = r["worst"]
    return (w["pm_deg"] is not None and w["pm_deg"] >= pm and (w["gm_dB"] is None or w["gm_dB"] >= gm)
            and w["peak_dB"] <= peak and (w["f3_MHz"] is None or w["f3_MHz"] >= f3) and not w["second"])


def hv_scan(flavour, g2, topo):
    cmp = HVComposite(flavour, g2)
    cls = (0.0,) if topo == "plain" else tuple(c * 1e-12 for c in CL_GRID_pF)
    rows = [hv_design(cmp, cf * 1e-12, cl) for cl in cls for cf in CF_GRID_pF]
    return cmp, rows


# the finer scan of the dual-feedback composite around its robust region (Section 11.6)
FINE_G2 = (4.0, 4.5, 5.0, 5.5, 6.0, 7.0)
FINE_CL_pF = np.round(np.arange(2.0, 4.001, 0.25), 3)
FINE_CF_pF = np.round(np.arange(0.10, 0.3001, 0.025), 3)


def hv_fine_scan():
    """Every (G2, C_L, C_F) of the fine grid in both descriptions, each design over its 27 corners.
    Per description and gain: the number of designs, the number robust (CRITERIA), and the robust
    designs ordered by their dynamic range at 1 mA for a 100-MHz tone."""
    out = {}
    for flavour in ("macromodels", "datasheet"):
        out[flavour] = {}
        for g2 in FINE_G2:
            cmp = HVComposite(flavour, g2)
            rows = [hv_design(cmp, cf * 1e-12, cl * 1e-12) for cl in FINE_CL_pF for cf in FINE_CF_pF]
            good = sorted((r for r in rows if robust(r)), key=lambda r: -r["100MHz"]["dr_dB"]["1 mA"])
            out[flavour][f"G{g2:g}"] = dict(n_designs=len(rows), n_robust=len(good), robust=good)
            print(f"[{flavour}] G2={g2:g}: robust {len(good)}/{len(rows)}")
            for r in good:
                w = r["worst"]
                print(f"    C_F {r['c_f_pF']:.3f} C_L {r['c_l_pF']:.2f} | worst PM {w['pm_deg']:.1f} pk "
                      f"{w['peak_dB']:.2f} f3 {w['f3_MHz']:.0f} | nominal f3 {r['nominal']['f3_MHz']:.0f} | noise "
                      f"{r['noise_nA']:.1f} nA | DR100 " + "/".join(f"{v:.1f}" for v in r["100MHz"]["dr_dB"].values()))
    return out


def _line(r):
    n, w = r["nominal"], r["worst"]
    fmt = lambda v, p=1: "none" if v is None else f"{v:.{p}f}"
    return (f"C_F {r['c_f_pF']:.3f} pF, C_L {r['c_l_pF']:.1f} pF | nominal f_c {fmt(n['f_c_MHz'], 0)} MHz PM "
            f"{fmt(n['pm_deg'])} GM {fmt(n['gm_dB'])} f3 {fmt(n['f3_MHz'], 0)} pk {n['peak_dB']:.2f} | worst PM "
            f"{fmt(w['pm_deg'])} GM {fmt(w['gm_dB'])} pk {w['peak_dB']:.2f} f3 {fmt(w['f3_MHz'], 0)} | noise "
            f"{r['noise_nA']:.1f} nA (2nd {r['noise_parts_nA']['second']:.1f}) | Vpk100 {r['100MHz']['v_pk']:.2f} DR "
            + "/".join(f"{v:.1f}" for v in r["100MHz"]["dr_dB"].values()))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=HERE.parent / "data" / "results" / "composite_analytical.json")
    ap.add_argument("--fine", action="store_true",
                    help="only the finer scan of the dual-feedback composite, to composite_hv_fine_scan.json")
    a = ap.parse_args()
    if a.fine:
        grid = dict(g2=FINE_G2, c_l_pF=list(FINE_CL_pF), c_f_pF=list(FINE_CF_pF))
        path = a.out.parent / "composite_hv_fine_scan.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(dict(criteria=CRITERIA, grid=grid, scan=hv_fine_scan()), indent=1, default=float),
                        encoding="utf-8")
        return
    res = dict(criteria=CRITERIA, hv={})
    for flavour in ("macromodels", "datasheet"):
        res["hv"][flavour] = {}
        for g2 in G2_GRID:
            for topo in ("plain", "dual"):
                cmp, rows = hv_scan(flavour, g2, topo)
                good = [r for r in rows if robust(r)]
                best = max(good, key=lambda r: (r["100MHz"]["dr_dB"]["1 mA"], r["worst"]["pm_deg"])) if good else None
                top = max(rows, key=lambda r: r["worst"]["pm_deg"] if r["worst"]["pm_deg"] is not None else -1e9)
                res["hv"][flavour][f"{topo}_G{g2:g}"] = dict(n_designs=len(rows), n_robust=len(good), best=best,
                                                              largest_worst_pm=top)
                print(f"[{flavour}] G2={g2:g} {topo:5s} robust {len(good):3d}/{len(rows)}")
                if best:
                    print("     best robust:", _line(best))
                print("     largest worst-corner PM:", _line(top))
    res["fet"] = {}
    for dev in FET_DESIGN:
        cmp, rows = fet_scan(dev)
        good = [r for r in rows if robust(r)]
        best = max(good, key=lambda r: (r["100MHz"]["dr_dB"]["0.1 mA"], r["worst"]["pm_deg"])) if good else None
        # where no design is robust (the JFETs), Table 11.6 takes the widest-band design that keeps the
        # phase margin, gain margin and peaking criteria at every corner
        margins = [r for r in rows if robust(r, f3=0.0)]
        widest = max(margins, key=lambda r: r["worst"]["f3_MHz"] or 0.0) if margins else None
        top = max(rows, key=lambda r: r["worst"]["pm_deg"] if r["worst"]["pm_deg"] is not None else -1e9)
        res["fet"][dev] = dict(n_designs=len(rows), n_robust=len(good), best=best, n_with_margins=len(margins),
                               widest_with_margins=widest, largest_worst_pm=top)
        print(f"[FET] {dev}: robust {len(good)}/{len(rows)}, margins kept by {len(margins)}")
        for lab, r in (("best robust", best), ("widest band with the margins", widest), ("largest worst-corner PM", top)):
            if r is None:
                continue
            n, w = r["nominal"], r["worst"]
            fmt = lambda v, p=1: "none" if v is None else f"{v:.{p}f}"
            print(f"     {lab}: C_N {r['c_n_pF']:.1f} pF, C_F {r['c_f_pF']:.2f} pF | |Z_T| LF {r['z_lf_ohm']:.0f} | nominal "
                  f"f_c {fmt(n['f_c_MHz'], 0)} PM {fmt(n['pm_deg'])} GM {fmt(n['gm_dB'])} f3 {fmt(n['f3_MHz'], 0)} pk "
                  f"{n['peak_dB']:.2f} | worst PM {fmt(w['pm_deg'])} GM {fmt(w['gm_dB'])} pk {w['peak_dB']:.2f} f3 "
                  f"{fmt(w['f3_MHz'], 0)} | noise {r['noise_nA']:.1f} nA "
                  + str({k: round(v, 1) for k, v in r['noise_parts_nA'].items()})
                  + " | DR100 " + "/".join(f"{v:.1f}" for v in r["100MHz"]["dr_dB"].values()))
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(res, indent=1, default=float), encoding="utf-8")


if __name__ == "__main__":
    main()
