"""Numbers quoted in the text of the high-gain TIA note (no simulation).

Prints and writes data/results/numbers.json:
  1. the feedback resistor as a uniform RC line: response peaking, the
     effective capacitance C_ee - C_g/6, the input loading C_g/3, the
     frequency at which its noise current Re{y11} has doubled, and the
     corner with the plane under the resistor driven from the output;
  2. a parallel-plate estimate of a chip resistor's capacitance to a
     ground plane (dimensions stated below, an estimate, not a measurement);
  3. how far equalization can extend the band before e_n * w * C_T reaches
     the resistor-plus-diode floor, f_e = sqrt(S_floor) / (2 pi e_n C_T);
  4. discrete-JFET composites against the lowest-noise monolithic part:
     ratio of e_n * C_T and the bandwidth ratio at equal e_n*C noise,
     (ratio)^(2/3);
  5. a transdiode log amplifier: f_-3dB = I / (2 pi V_T C_C) and the
     output noise V_T * sqrt(4 q / I) per rtHz;
  6. the crossover gain R_F* = C_T / (pi GBW C_par^2) at which the
     resistor's own capacitance takes over the bandwidth.

Usage:  python hg_numbers.py
"""
from __future__ import annotations

import json
import math

import numpy as np

import hg_model as m

EPS0 = 8.8541878128e-12


def urc_numbers() -> list[dict]:
    rows = []
    f = np.logspace(0, 7, 7000)
    w = 2 * math.pi * f
    for rf in (1e7, 1e8, 1e9):
        for cee, cg in ((0.05e-12, 0.0), (0.05e-12, 0.1e-12), (0.05e-12, 0.3e-12),
                        (0.05e-12, 0.6e-12), (0.1e-12, 0.3e-12)):
            y11, y21 = m.urc_y(w, rf, cg, cee)
            zt = np.abs(1.0 / (-y21)) / rf
            peak_db = 20 * math.log10(zt.max())
            f_peak = float(f[np.argmax(zt)])
            below = np.nonzero(zt < 1 / math.sqrt(2))[0]
            f3 = float(f[below[0]]) if below.size else float("nan")
            # output-driven plane: transfer admittance y11
            zo = np.abs(1.0 / y11) / rf
            below_o = np.nonzero(zo < 1 / math.sqrt(2))[0]
            f3_o = float(f[below_o[0]]) if below_o.size else float("nan")
            # frequency where the line's noise current density has doubled
            ratio = np.real(y11) * rf
            dbl = np.nonzero(ratio >= 2.0)[0]
            f_dbl = float(f[dbl[0]]) if dbl.size else float("nan")
            rows.append({
                "rf": rf, "cee_pF": cee * 1e12, "cg_pF": cg * 1e12,
                "c_eff_first_order_pF": (cee - cg / 6) * 1e12,
                "input_loading_pF": cg / 3 * 1e12,
                "peak_dB": peak_db, "f_peak_Hz": f_peak if peak_db > 0.01 else None,
                "f3_ground_plane_Hz": f3, "f3_lumped_cee_Hz": 1 / (2 * math.pi * rf * cee),
                "f3_output_plane_Hz": f3_o,
                "f_noise_doubled_Hz": f_dbl,
                "f_noise_doubled_series_Hz": math.sqrt(45) / (2 * math.pi * rf * cg) if cg else None,
            })
    return rows


def ladder_error() -> list[dict]:
    """Largest error of an N-section RC ladder (series R/N, shunt C/N at each
    internal node, C/(2N) at the two ends) against the exact uniform line,
    in |y21| and arg(y21), for omega*R*C_g up to 100 (theta up to 10)."""
    rows = []
    r, c = 1.0, 1.0
    wrc = np.logspace(-2, 2, 400)
    _, y21x = m.urc_y(wrc / (r * c), r, c, 0.0)
    for n in (3, 5, 10, 20, 50):
        errs_m, errs_p = [], []
        for k, w in enumerate(wrc):
            # nodal admittance matrix of the ladder, nodes 0..n, ends 0 and n
            y = np.zeros((n + 1, n + 1), dtype=complex)
            g = n / r
            for i in range(n):
                y[i, i] += g; y[i + 1, i + 1] += g
                y[i, i + 1] -= g; y[i + 1, i] -= g
            for i in range(n + 1):
                share = 0.5 if i in (0, n) else 1.0
                y[i, i] += 1j * w * c / n * share
            # short-circuit y21: drive node n with 1 V, ground node 0, solve internal
            inner = list(range(1, n))
            if inner:
                a = y[np.ix_(inner, inner)]
                b = -y[np.ix_(inner, [n])].ravel()
                v_in = np.linalg.solve(a, b)
            else:
                v_in = np.array([])
            v = np.zeros(n + 1, dtype=complex)
            v[n] = 1.0
            v[1:n] = v_in
            i0 = (y[0, :] @ v)          # current into node 0 from the network
            errs_m.append(abs(abs(i0) / abs(y21x[k]) - 1.0))
            errs_p.append(abs(np.degrees(np.angle(i0) - np.angle(y21x[k]))))
        sel = wrc <= 30
        rows.append({"sections": n,
                     "max_mag_err_wRC_le_30": float(np.max(np.array(errs_m)[sel])),
                     "max_phase_err_deg_wRC_le_30": float(np.max(np.array(errs_p)[sel]))})
    return rows


def plate_estimate() -> dict:
    """1206 body 3.2 mm x 1.6 mm, film on top of a 0.55 mm alumina substrate
    (eps_r 9.8), 35 um solder/air gap, plane under 0.2 mm (four-layer) or
    1.5 mm (two-layer) FR-4 (eps_r 4.4).  Series plates, no fringing."""
    area = 3.2e-3 * 1.6e-3
    out = {"assumed": "film area 3.2 x 1.6 mm; alumina 0.55 mm, er 9.8; gap 35 um air; FR-4 er 4.4"}
    c_al = EPS0 * 9.8 * area / 0.55e-3
    c_gap = EPS0 * 1.0 * area / 35e-6
    for name, h in (("four_layer_0p2mm", 0.2e-3), ("two_layer_1p5mm", 1.5e-3)):
        c_fr4 = EPS0 * 4.4 * area / h
        c = 1.0 / (1 / c_al + 1 / c_gap + 1 / c_fr4)
        out[name + "_pF"] = c * 1e12
    out["alumina_pF"] = c_al * 1e12
    out["gap_pF"] = c_gap * 1e12
    return out


def equalization_limits() -> list[dict]:
    amps = m.load_amps()
    rows = []
    for amp in ("ADA4625-1", "OPA140", "ADA4530-1", "OPA928"):
        a = amps[amp]
        for rf in (1e8, 1e9):
            for c_d, r_sh, name in ((20e-12, 2e9, "S1336-18BK"), (380e-12, 0.4e9, "S1336-8BK")):
                c_t = c_d + a.c_in + 1e-12 + 0.1e-12
                floor = m.FOUR_KT / rf + m.FOUR_KT / r_sh
                # solve e_n(f) * 2 pi f C_T = sqrt(floor) on a grid (e_n varies with f)
                f = np.logspace(0, 7, 4000)
                lhs = a.en(f) * 2 * math.pi * f * c_t
                k = np.nonzero(lhs >= math.sqrt(floor))[0]
                f_e = float(f[k[0]]) if k.size else float("nan")
                rows.append({"amp": amp, "rf": rf, "source": name, "c_t_pF": c_t * 1e12,
                             "f_e_Hz": f_e, "f_res_0p1pF_Hz": 1 / (2 * math.pi * rf * 0.1e-12)})
    return rows


def composites() -> list[dict]:
    amps = m.load_amps()
    rows = []
    ref = amps["ADA4625-1"]
    for c_d in (100e-12, 380e-12, 1e-9, 3.7e-9):
        f = np.array([1e4])
        base = float(ref.en(f)[0]) * (c_d + ref.c_in + 1e-12)
        for name in ("IF3601 composite", "LSK170 composite", "BF862 composite"):
            a = amps[name]
            prod = float(a.en(f)[0]) * (c_d + a.c_in + 1e-12)
            r = base / prod
            rows.append({"c_d_pF": c_d * 1e12, "device": name,
                         "en_C_ref": base, "en_C_dev": prod, "ratio": r,
                         "dB": 20 * math.log10(r), "bandwidth_ratio_equal_noise": r ** (2 / 3)})
    # capacitive matching: e_n^2 proportional to 1/C_iss at fixed f_T
    return rows


def log_amp() -> list[dict]:
    vt = m.K_B * m.T_REF / m.Q_E
    rows = []
    for i in (1e-10, 1e-9, 1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3):
        row = {"I_A": i, "r_e_Ohm": vt / i,
               "vn_out_V_rtHz": vt * math.sqrt(4 * m.Q_E / i),
               "rel_noise_per_rtHz": math.sqrt(4 * m.Q_E / i)}
        for cc in (10e-12, 100e-12, 1e-9):
            row[f"f3_Cc_{cc * 1e12:g}pF_Hz"] = i / (2 * math.pi * vt * cc)
        rows.append(row)
    return rows


def crossover_gains() -> list[dict]:
    rows = []
    for gbw in (2e6, 20e6, 200e6):
        for c_t in (10e-12, 100e-12, 1e-9):
            for c_par in (0.05e-12, 0.1e-12, 0.2e-12):
                rows.append({"gbw_MHz": gbw / 1e6, "c_t_pF": c_t * 1e12, "c_par_pF": c_par * 1e12,
                             "rf_star_Ohm": c_t / (math.pi * gbw * c_par ** 2)})
    return rows


def main() -> None:
    out = {
        "urc": urc_numbers(), "ladder": ladder_error(), "plate": plate_estimate(),
        "equalization": equalization_limits(), "composites": composites(),
        "log_amp": log_amp(), "crossover": crossover_gains(),
        "constants": {"4kT": m.FOUR_KT, "kT_q": m.K_B * m.T_REF / m.Q_E, "T": m.T_REF},
    }
    (m.DATA / "results" / "numbers.json").write_text(json.dumps(out, indent=1))
    for k, v in out.items():
        print("==", k)
        if isinstance(v, list):
            for r in v:
                print({kk: (round(vv, 4) if isinstance(vv, float) and abs(vv) < 1e4 else
                            (f"{vv:.3g}" if isinstance(vv, float) else vv)) for kk, vv in r.items()})
        else:
            print(v)


if __name__ == "__main__":
    main()
