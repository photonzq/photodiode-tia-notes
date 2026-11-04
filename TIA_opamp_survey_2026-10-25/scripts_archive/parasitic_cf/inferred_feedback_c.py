"""Feedback capacitances inferred from published bandwidths, rise times and fits.

Every input below is a number printed in the cited source (page given in the
comment).  The script only does the arithmetic that turns those numbers into a
total feedback capacitance, so that each inferred value in
../../data/parasitic_cf/tia_feedback_parasitics.json can be reproduced.

Usage:  python -I inferred_feedback_c.py [out.json]

1. Single-pole bound, C = 1/(2 pi R f).  When a TIA's bandwidth is limited by the
   feedback resistor and its own shunt capacitance, f_-3dB = 1/(2 pi R C).  If other
   poles also limit the bandwidth, the same formula gives an upper bound on C.
   Rise times are converted with f = 0.35/t_r (10-90 %, single pole).
2. Balanced-detector fit (Rev. Sci. Instrum. 88, 113109 (2017), arXiv:1709.05213,
   Table I, arXiv p. 3): the paper's Eq. (3), p = (2 pi R_F C_F + 1/(A0 f0)) f*,
   solved for the total feedback capacitance,
   C_F,tot = (p/f* - 1/(A0 f0)) / (2 pi R_F),
   with A0 f0 = 3.9 GHz (OPA847 gain-bandwidth product) and first-order error
   propagation of the quoted uncertainties of p and f*.
3. Two equal series sections (TI TIDA-060025): each section is R/2 in parallel with
   C_sec = C_cap + c_par, and two equal sections in series give C_tot = C_sec/2.
4. Board-material scaling quoted in the LTC DC2414A demo manual (p. 3): the same
   layout on FR-4 instead of a dielectric with relative permittivity 3.4 gives
   30 % to 40 % more parasitic capacitance.
5. Second-order TIA step response used to judge the TIDA-060025 edges.  With a
   single-pole op amp of gain-bandwidth w_A = 2 pi GBW, total input capacitance C_T
   (diode + op amp + board, excluding C_F) and feedback R_F || C_F,
   Z_T(s) = -R_F / [1 + s (R_F C_F + 1/w_A) + s^2 R_F (C_F + C_T) / w_A],
   so w_n^2 = w_A / (R_F (C_F + C_T)) and zeta = (w_n / 2) (R_F C_F + 1/w_A).
   The 10-90 % rise time is found numerically from the closed-form step response.
   Inputs: R_F = 2 x 4.99 kohm, GBW = 5.5 GHz (OPA858 typical), C_T = 1.9 pF
   (1.1-pF photodiode + 0.8-pF OPA858 input, as in TI's simulation) or 2.0 pF
   (TI's estimate including the board), C_F = 75, 85, 100, 125 fF.
"""
import json
import math
import sys

TWO_PI = 2.0 * math.pi


def c_from_bandwidth(r_ohm, f_hz):
    """Total feedback capacitance (F) that alone would set f_-3dB = f_hz at R = r_ohm."""
    return 1.0 / (TWO_PI * r_ohm * f_hz)


def f_from_rc(r_ohm, c_farad):
    """RC corner frequency (Hz)."""
    return 1.0 / (TWO_PI * r_ohm * c_farad)


def bandwidth_cases():
    cases = [
        # label, R (ohm), bandwidth (Hz) or None, rise time (s) or None, source note
        ("LTC6268-10, 0805, basic layout", 402e3, 4e6, None,
         "LTC6268-10 datasheet p.14, Fig. 5 (87 ns); LT Journal V25N2 Fig. 4 (88 ns)"),
        ("LTC6268-10, shield under whole resistor", 402e3, 34e6, None,
         "LTC6268-10 datasheet p.14-15, Fig. 7 (10.3 ns, 34 MHz total system)"),
        ("LTC6268, 0603, basic layout", 499e3, 2.5e6, None,
         "ADI article 'Transimpedance Amplifier Noise Considerations', Fig. 7"),
        ("LTC6268, 0603, minimal pads + ground trace near output end", 499e3, 11.2e6, None,
         "same article, Fig. 9 (11.2 MHz); the capacitance is not stated there"),
        ("DC2414A U1, 1206, extreme ground shield, R_F = 10 Mohm", 10e6, None, 100e-9,
         "DC2414A demo manual p.2 ('rise times as low as 100ns'; manual quotes ~7 fF)"),
        ("DN399, 1 Mohm with 0.1 pF capacitor", 1e6, 350e3, None,
         "LT Design Note 399 p.1, Fig. 1 (350 kHz; note estimates ~0.4 pF total)"),
    ]
    rows = []
    for label, r, bw, tr, note in cases:
        if bw is None:
            bw = 0.35 / tr
        c = c_from_bandwidth(r, bw)
        rows.append({"case": label, "R_ohm": r, "bandwidth_Hz": bw,
                     "C_total_fF": round(c * 1e15, 2), "source": note})
    return rows


def rc_corner_checks():
    checks = [
        ("Burr-Brown AB-075 p.6: 0.5 pF across 100 Mohm", 100e6, 0.5e-12, "quoted 3.2 kHz"),
        ("LTC6228 datasheet p.20: 400 fF across 5 kohm", 5e3, 400e-15, "quoted 79 MHz"),
        ("DC2414A manual p.2: 70 fF (0805 in air) across 10 Mohm", 10e6, 70e-15, "quoted 220 kHz"),
        ("Usenet post (2022): 100 fF across 4 kohm", 4e3, 100e-15, "quoted 400 MHz"),
        ("2 kohm with 0.10 pF", 2e3, 0.10e-12, "context for a 2-kohm TIA"),
        ("2 kohm with 0.20 pF", 2e3, 0.20e-12, "context for a 2-kohm TIA"),
        ("2 kohm with 0.30 pF", 2e3, 0.30e-12, "context for a 2-kohm TIA"),
    ]
    return [{"case": label, "R_ohm": r, "C_fF": c * 1e15,
             "corner_MHz": round(f_from_rc(r, c) / 1e6, 4), "note": note}
            for label, r, c, note in checks]


def balanced_detector_fits(gbw_hz=3.9e9):
    # R_F (ohm), nominal C_F (F), f* (Hz), sigma f*, p, sigma p   [Table I, arXiv p.3]
    table = [
        (12e3, 0.0, 47.3e6, 3e6, 0.63, 0.05),
        (12e3, 0.3e-12, 44.5e6, 3e6, 1.9, 0.1),
        (4.3e3, 0.3e-12, 73.3e6, 4e6, 0.75, 0.05),
        (2e3, 0.4e-12, 103e6, 5e6, 0.54, 0.05),
    ]
    rows = []
    for r, c_nom, fstar, sf, p, sp in table:
        num = p / fstar - 1.0 / gbw_hz
        c_tot = num / (TWO_PI * r)
        # first-order propagation: dC/dp = 1/(f* 2pi R), dC/df* = -p/(f*^2 2pi R)
        sc = math.hypot(sp / (fstar * TWO_PI * r), p * sf / (fstar ** 2 * TWO_PI * r))
        rows.append({"R_F_ohm": r, "C_F_nominal_pF": c_nom * 1e12,
                     "C_F_total_pF": round(c_tot * 1e12, 3),
                     "sigma_pF": round(sc * 1e12, 3),
                     "parasitic_pF": round((c_tot - c_nom) * 1e12, 3)})
    return rows


def tida060025_series(c_cap=0.15e-12):
    return [{"c_par_per_section_fF": cpar * 1e15,
             "C_total_fF": round((c_cap + cpar) / 2 * 1e15, 1)}
            for cpar in (0.0, 20e-15, 50e-15, 100e-15)]


def fr4_scaling():
    return [{"value_on_er3p4_fF": v, "on_FR4_fF_low": round(v * 1.3, 1),
             "on_FR4_fF_high": round(v * 1.4, 1)} for v in (100.0, 33.0, 7.0)]


def step_rise_time_10_90(wn, zeta, n=200000):
    """10-90 % rise time (s) of wn^2/(s^2 + 2 zeta wn s + wn^2), from the exact step response."""
    def y(t):
        if zeta < 1.0:
            wd = wn * math.sqrt(1.0 - zeta ** 2)
            phi = math.acos(zeta)
            return 1.0 - math.exp(-zeta * wn * t) * math.sin(wd * t + phi) / math.sqrt(1.0 - zeta ** 2)
        if zeta == 1.0:
            return 1.0 - math.exp(-wn * t) * (1.0 + wn * t)
        s1 = -wn * (zeta - math.sqrt(zeta ** 2 - 1.0))
        s2 = -wn * (zeta + math.sqrt(zeta ** 2 - 1.0))
        return 1.0 + (s2 * math.exp(s1 * t) - s1 * math.exp(s2 * t)) / (s1 - s2)
    t_end = 20.0 / wn
    dt = t_end / n
    t10 = t90 = None
    for i in range(1, n + 1):
        t = i * dt
        v = y(t)
        if t10 is None and v >= 0.1:
            t10 = t
        if v >= 0.9:
            t90 = t
            break
    return t90 - t10


def tia_edge(c_f, c_t, gbw_hz=5.5e9, r_f=2 * 4.99e3):
    """10-90 % edge (s) of the second-order TIA model for feedback C_F and input C_T."""
    w_a = TWO_PI * gbw_hz
    wn = math.sqrt(w_a / (r_f * (c_f + c_t)))
    zeta = 0.5 * wn * (r_f * c_f + 1.0 / w_a)
    return step_rise_time_10_90(wn, zeta), wn, zeta


def tida060025_edges():
    rows = []
    for c_t in (1.9e-12, 2.0e-12):
        for c_f in (75e-15, 85e-15, 100e-15, 125e-15):
            tr, wn, zeta = tia_edge(c_f, c_t)
            rows.append({"C_T_pF": c_t * 1e12, "C_F_fF": round(c_f * 1e15, 1),
                         "f_n_MHz": round(wn / TWO_PI / 1e6, 1), "zeta": round(zeta, 3),
                         "t_r_10_90_ns": round(tr * 1e9, 3)})
    return rows


def tida060025_cf_from_edges(c_t=1.9e-12):
    """C_F that reproduces each measured edge after calibrating the model to TI's simulation.

    TI's TINA simulation with C_F = 75 fF and a 1.1-pF diode (C_T about 1.9 pF with the
    0.8-pF amplifier input) gives 1.18 ns (10-90 % rise) and 1.20 ns (90-10 % fall),
    TIDUEL3A Table 3-1.  The model is scaled by k = t_TI / t_model(75 fF) for each edge,
    then C_F is solved so that k * t_model(C_F) equals the measured edge.
    """
    t_model_75 = tia_edge(75e-15, c_t)[0]
    cases = [("fall 90-10 %, 100-ns pulse", 1.20e-9, 1.11e-9),
             ("fall 90-10 %, 20-ns pulse", 1.20e-9, 1.12e-9),
             ("rise 10-90 %, 100-ns pulse", 1.18e-9, 1.68e-9),
             ("rise 10-90 %, 20-ns pulse", 1.18e-9, 1.72e-9)]
    rows = []
    for label, t_sim, t_meas in cases:
        k = t_sim / t_model_75
        lo, hi = 5e-15, 400e-15
        for _ in range(80):
            mid = 0.5 * (lo + hi)
            if k * tia_edge(mid, c_t)[0] < t_meas:
                lo = mid
            else:
                hi = mid
        rows.append({"edge": label, "TI_simulated_ns": t_sim * 1e9, "measured_ns": t_meas * 1e9,
                     "calibration_k": round(k, 3), "C_F_reproducing_fF": round(0.5 * (lo + hi) * 1e15, 1)})
    return rows


def tida060025_fall_sensitivity(t_meas=1.11e-9, t_sim=1.20e-9):
    """C_F reproducing the 1.11-ns fall edge if the real board's GBW or C_T differ from
    the values behind TI's simulation (calibration factor kept at its nominal value)."""
    k = t_sim / tia_edge(75e-15, 1.9e-12)[0]
    rows = []
    for gbw in (4.5e9, 5.5e9, 6.5e9):
        for c_t in (1.7e-12, 1.9e-12, 2.1e-12):
            lo, hi = 5e-15, 400e-15
            for _ in range(80):
                mid = 0.5 * (lo + hi)
                if k * tia_edge(mid, c_t, gbw_hz=gbw)[0] < t_meas:
                    lo = mid
                else:
                    hi = mid
            rows.append({"GBW_GHz": gbw / 1e9, "C_T_pF": c_t * 1e12,
                         "C_F_reproducing_fF": round(0.5 * (lo + hi) * 1e15, 1)})
    return rows


def main():
    out = {
        "bandwidth_bounds": bandwidth_cases(),
        "rc_corner_checks": rc_corner_checks(),
        "balanced_detector_2017_total_cf": balanced_detector_fits(),
        "tida060025_two_series_sections": tida060025_series(),
        "tida060025_second_order_edges": tida060025_edges(),
        "tida060025_cf_from_measured_edges": tida060025_cf_from_edges(),
        "tida060025_fall_edge_sensitivity": tida060025_fall_sensitivity(),
        "dc2414a_fr4_scaling": fr4_scaling(),
    }
    print(json.dumps(out, indent=2))
    if len(sys.argv) > 1:
        with open(sys.argv[1], "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=2)


if __name__ == "__main__":
    main()
