"""Markdown tables for the TIA amplifier survey report.

Usage: python make_tables.py <results_dir> <out_md>

Reads <results_dir>/results.json (run_analysis.py) and parts_db.PARTS and
writes the tables quoted in the report.  Numbers are rounded for display only.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

from parts_db import PARTS

ORDER = ["OPA855", "OPA858", "OPA955", "LMH6629 (COMP HI)", "LMH6629 (COMP LO)", "OPA856", "OPA859",
         "THS4304", "OPA843", "OPA846", "OPA818", "OPA847", "OPA817", "OPA814", "OPA657", "THS4271",
         "THS4021", "LMH6624", "ADA4899-1", "ADA4817-1", "AD8099", "ADA4895-1", "AD8045", "AD8021",
         "LTC6268-10", "LTC6228", "LT6200-10", "LT6230-10"]


def fmt(v, nd=1, none="–"):
    if v is None or (isinstance(v, float) and not np.isfinite(v)):
        return none
    return f"{v:.{nd}f}"


def spec_table():
    rows = ["| Part | Maker | Input | Min. stable gain | GBW (GHz) | $e_n$ (nV/√Hz) | $i_n$ (pA/√Hz) | "
            "$C_{\\mathrm{CM}}$ / $C_{\\mathrm{DIFF}}$ (pF) | Supply used (V) | Swing used (V) | Slew (V/µs) | Package |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for name in ORDER:
        if name not in PARTS:
            continue
        p = PARTS[name]
        s = p.get("dr", {})
        sw = s.get("swing_light")
        rows.append(
            f"| {name} | {p['maker']} | {p['input']} | {p['g_min']:g} | {p['gbw']/1e9:.2f} | {p['en']*1e9:.2f} | "
            f"{p['in_']*1e12:.3g}{' (rises)' if (p.get('fet') and p.get('in_pts')) or p.get('in_curve_is_physical') else ''} | "
            f"{p['c_cm']*1e12:.2g} / {p['c_diff']*1e12:.2g} | {s.get('supply', '–')} | "
            f"{(f'{sw[0]:+.2f} to {sw[1]:+.2f}') if sw else '–'} | {s.get('sr', float('nan')):.0f} | {p.get('package', '–')} |")
    return "\n".join(rows)


def stability_table(res, rf):
    key = f"RF_{rf:.0f}"
    rows = ["| Part | $C_T$ (pF) | Flat: $C_F$ required / realized (pF) | Flat: $f_{-3\\,\\mathrm{dB}}$ (MHz) | Flat: PM (°) | "
            "1-dB: $f_{-3\\,\\mathrm{dB}}$ (MHz) / PM (°) | Largest PM (°) at $C_F$ (pF), $f_{-3\\,\\mathrm{dB}}$ | "
            "Robust (PM ≥ 45°): added $C$ (pF), $C_F$ (pF), $f_{-3\\,\\mathrm{dB}}$ (MHz) |",
            "|---|---|---|---|---|---|---|---|"]
    for name in ORDER:
        if name not in res:
            continue
        x = res[name][key]
        d = x["designs"]
        fl, pk, mp, rb = d.get("flat", {}), d.get("peak1dB", {}), d.get("max_pm"), d.get("robust45")
        if fl.get("C_F_req_pF") is None:
            flat_cf = "no stable flat design"
            flat_f3 = flat_pm = "–"
        else:
            flat_cf = f"{fl['C_F_req_pF']:.2f} / {fl['C_F_real_pF']:.2f}"
            flat_f3 = fmt(fl["f3_MHz"], 0)
            flat_pm = fmt(fl["pm_deg"], 0)
        pk_s = (f"{pk['f3_MHz']:.0f} / {pk['pm_deg']:.0f}" if pk.get("C_F_req_pF") is not None else "–")
        mp_s = (f"{mp['pm_deg']:.0f} at {mp['C_F_real_pF']:.2f}, {mp['f3_MHz']:.0f} MHz" if mp else "none stable")
        rb_s = (f"{rb['C_add_pF']:.2g}, {rb['C_F_real_pF']:.2f}, {rb['f3_MHz']:.0f}" if rb else "none")
        rows.append(f"| {name} | {x['C_T_pF']:.2f} | {flat_cf} | {flat_f3} | {flat_pm} | {pk_s} | {mp_s} | {rb_s} |")
    return "\n".join(rows)


def calibrated_table(res):
    rows = ["| Part, $R_F$ | Model | Flat: $C_F$ (pF), $f_{-3\\,\\mathrm{dB}}$ (MHz), PM (°) | Robust (PM ≥ 45°): added $C$, $C_F$ (pF), $f_{-3\\,\\mathrm{dB}}$ (MHz) |",
            "|---|---|---|---|"]
    for name in ORDER:
        if name not in res:
            continue
        for rf in (1500.0, 2000.0):
            d = res[name][f"RF_{rf:.0f}"]["designs"]
            if "check_calibrated" not in d:
                continue
            for lab, dd in (("datasheet curve as plotted", d), ("calibrated to text PM and table GBW", d["check_calibrated"])):
                fl = dd.get("flat", {})
                rb = dd.get("robust45")
                fl_s = (f"{fl['C_F_real_pF']:.2f}, {fl['f3_MHz']:.0f}, {fl['pm_deg']:.0f}" if fl.get("C_F_real_pF") else "–")
                rb_s = (f"{rb['C_add_pF']:.2g}, {rb['C_F_real_pF']:.2f}, {rb['f3_MHz']:.0f}" if rb else "none")
                rows.append(f"| {name}, {rf/1e3:.1f} kΩ | {lab} | {fl_s} | {rb_s} |")
    return "\n".join(rows)


def noise_table(res, rf, tag, parts):
    key = f"RF_{rf:.0f}"
    rows = ["| Part | 1 MHz | 10 MHz | 50 MHz | 100 MHz | 150 MHz | 200 MHz | Penalty 10–150 MHz (dB) | Penalty 10–200 MHz (dB) |",
            "|---|---|---|---|---|---|---|---|---|"]
    for name in parts:
        nz = res[name][key]["noise"].get(tag)
        if not nz:
            continue
        c = nz["central"]
        h = nz.get("high")
        cells = []
        for i in range(6):
            s = f"{c['i_in_pA'][i]:.2f}"
            if h and abs(h["i_in_pA"][i] - c["i_in_pA"][i]) > 0.05:
                s += f" ({h['i_in_pA'][i]:.2f})"
            cells.append(s)
        p1 = f"{c['band_penalty_dB']['10-150 MHz']:.1f}" + (f" ({h['band_penalty_dB']['10-150 MHz']:.1f})" if h else "")
        p2 = f"{c['band_penalty_dB']['10-200 MHz']:.1f}" + (f" ({h['band_penalty_dB']['10-200 MHz']:.1f})" if h else "")
        rows.append(f"| {name} | " + " | ".join(cells) + f" | {p1} | {p2} |")
    return "\n".join(rows)


def output_noise_table(res, rf, tag, parts):
    key = f"RF_{rf:.0f}"
    rows = ["| Part | 1 MHz | 10 MHz | 50 MHz | 100 MHz | 150 MHz | 200 MHz | At 100 MHz into back-terminated 50 Ω (dBm/Hz) | Unfiltered output rms (mV) |",
            "|---|---|---|---|---|---|---|---|---|"]
    for name in parts:
        nz = res[name][key]["noise"].get(tag)
        if not nz:
            continue
        c = nz["central"]
        v100 = c["v_out_nV"][3] * 1e-9
        p_dbm = 10 * np.log10((v100 / 2) ** 2 / 50 / 1e-3)
        rows.append(f"| {name} | " + " | ".join(f"{v:.1f}" for v in c["v_out_nV"]) +
                    f" | {p_dbm:.1f} | {nz['v_out_rms_unfiltered_mV']:.2f} |")
    return "\n".join(rows)


def shot_table(res, rf, tag, parts):
    key = f"RF_{rf:.0f}"
    rows = ["| Part | 0.1 mA: total at 100 / 200 MHz (pA/√Hz) | 0.1 mA: clearance at 100 / 200 MHz (dB) | "
            "1 mA: total at 100 / 200 MHz | 1 mA: clearance (dB) | 10 mA: clearance (dB) |",
            "|---|---|---|---|---|---|"]
    for name in parts:
        nz = res[name][key]["noise"].get(tag)
        if not nz:
            continue
        w = nz["central"]["with_dc"]
        a, b, c = w["0.1 mA"], w["1 mA"], w["10 mA"]
        rows.append(f"| {name} | {a['total_pA'][3]:.1f} / {a['total_pA'][5]:.1f} | {a['shot_clearance_dB'][3]:.1f} / {a['shot_clearance_dB'][5]:.1f} | "
                    f"{b['total_pA'][3]:.1f} / {b['total_pA'][5]:.1f} | {b['shot_clearance_dB'][3]:.1f} / {b['shot_clearance_dB'][5]:.1f} | "
                    f"{c['shot_clearance_dB'][3]:.1f} / {c['shot_clearance_dB'][5]:.1f} |")
    return "\n".join(rows)


def dr_table(res, rf, tag, parts):
    key = f"RF_{rf:.0f}"
    rows = ["| Part | Supply | DC-coupled $I_{\\mathrm{DC,max}}$ (mA) | 100 MHz: $V_{\\mathrm{pk}}$ (V), limit | 150 MHz: $V_{\\mathrm{pk}}$ (V), limit | "
            "DR in 150 MHz at $I_{\\mathrm{DC}}$ = 0 / 0.1 / 1 / 10 mA (dB), 100-MHz tone | Same into back-terminated 50 Ω |",
            "|---|---|---|---|---|---|---|"]
    for name in parts:
        dr = res[name][key]["dr"].get(tag)
        if not dr:
            continue
        hz = dr["ac"]["high-Z"]
        lo = dr["ac"].get("50-ohm back-terminated (100 ohm)", hz)
        a100, a150 = hz["100 MHz"], hz["150 MHz"]
        d = a100["dr_with_dc_cancelled"]
        d50 = lo["100 MHz"]["dr_with_dc_cancelled"]
        rows.append(f"| {name} | {PARTS[name]['dr']['supply']} | {dr['I_DC_max_mA']:.2f} | {a100['v_pk_V']:.2f}, {a100['limiter']} | "
                    f"{a150['v_pk_V']:.2f}, {a150['limiter']} | "
                    + " / ".join(f"{d[k]['DR_150MHz_dB']:.1f}" for k in ("0 mA", "0.1 mA", "1 mA", "10 mA")) + " | "
                    + " / ".join(f"{d50[k]['DR_150MHz_dB']:.1f}" for k in ("0 mA", "0.1 mA", "1 mA", "10 mA")) + " |")
    return "\n".join(rows)


def corner_table(res, rf, tag, parts):
    key = f"RF_{rf:.0f}"
    rows = ["| Part | External $C_F$ (pF) | $C_{\\mathrm{PCB}}$ / $C_{F,\\mathrm{par}}$ = 0.2/0.1 pF | 0.2/0.3 | 0.5/0.1 | 0.5/0.3 |",
            "|---|---|---|---|---|---|"]
    for name in parts:
        x = res[name][key]
        c = x["corners"].get(tag)
        d = x["designs"].get(tag, {})
        if not c:
            continue
        cells = []
        for k in ("Cpcb0.2_Cfpar0.1", "Cpcb0.2_Cfpar0.3", "Cpcb0.5_Cfpar0.1", "Cpcb0.5_Cfpar0.3"):
            m = c[k]
            st = "" if m["stable"] else ", UNSTABLE"
            cells.append(f"{m['f3_MHz']:.0f} MHz, {m['pm_deg']:.0f}°, {m['peaking_dB']:+.1f} dB{st}")
        rows.append(f"| {name} | {max(d['C_F_ext_pF'], 0):.2f} | " + " | ".join(cells) + " |")
    return "\n".join(rows)


def main(results_dir: Path, out_md: Path) -> None:
    res = json.load(open(results_dir / "results.json", encoding="utf-8"))
    top = ["OPA855", "OPA858", "OPA955", "LMH6629 (COMP HI)", "OPA856", "OPA859", "THS4304", "OPA843",
           "OPA846", "OPA818"]
    out = ["# Tables generated from results.json", "",
           "## Specification table", "", spec_table(), "",
           "## Stability, 2 kOhm", "", stability_table(res, 2000.0), "",
           "## Stability, 1.5 kOhm", "", stability_table(res, 1500.0), "",
           "## Calibrated open-loop variants", "", calibrated_table(res), "",
           "## Input-referred noise, 2 kOhm, flat design (pA/rtHz)", "", noise_table(res, 2000.0, "flat", top), "",
           "## Input-referred noise, 1.5 kOhm, flat design (pA/rtHz)", "", noise_table(res, 1500.0, "flat", top), "",
           "## Input-referred noise, 2 kOhm, robust design (pA/rtHz)", "", noise_table(res, 2000.0, "robust45", top), "",
           "## Output noise, 2 kOhm, flat design (nV/rtHz)", "", output_noise_table(res, 2000.0, "flat", top), "",
           "## With DC photocurrent, 2 kOhm, flat design", "", shot_table(res, 2000.0, "flat", top), "",
           "## Dynamic range, 2 kOhm, flat design", "", dr_table(res, 2000.0, "flat", top), "",
           "## Dynamic range, 1.5 kOhm, flat design", "", dr_table(res, 1500.0, "flat", top), "",
           "## Parasitic corners, 2 kOhm, flat design (fixed external C_F)", "", corner_table(res, 2000.0, "flat", top), "",
           "## Parasitic corners, 1.5 kOhm, flat design (fixed external C_F)", "", corner_table(res, 1500.0, "flat", top), ""]
    out_md.write_text("\n".join(out), encoding="utf-8")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
