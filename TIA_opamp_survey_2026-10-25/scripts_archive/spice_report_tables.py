"""Tables of the SPICE section (Section 10) from the results of spice_tia_checks.py.

Usage:  python spice_report_tables.py [--spice <spice folder>] [--out <tables.md>]

Reads <spice folder>/results/*.json and the arrays saved under <spice folder>/runs/, and
writes the tables as Markdown (default: <spice folder>/results/tables.md).  Run the checks
first:  python spice_tia_checks.py all
"""
import argparse
import json
import math
import re
from pathlib import Path

import numpy as np

import tia_model as tm
from parts_db import PARTS
from run_analysis import C_PCB_NOM, noise_inputs, noise_models_for, open_loop_model
from spice_tia_checks import DESIGNS, KT, REFEREE, VENDOR_MODELS, datasheet, tag

HERE = Path(__file__).resolve().parent
LABEL = {part: m["db"] or part for part, m in VENDOR_MODELS.items()}   # the survey's name of each part


def fmt(x, d=1, none="–"):
    return none if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.{d}f}"


def design_name(part, R_F, C_D, C_F, label):
    variant = {"OPA855": "A", "OPA818": "B"}.get(part)
    head = f"{part} ({variant})" if variant else part
    return f"{head}, {C_D*1e12:g} pF, {R_F/1e3:g} kΩ, $C_F$ = {C_F*1e12:.2f} pF"


def table_parameters(res):
    smoke, params, aol = res["smoke"], res["params"], res["aol"]
    rows = ["| Amplifier | $I_Q$ (mA): SPICE / datasheet | $e_n$ (nV/√Hz): SPICE / datasheet | $i_n$ at 10 / 100 MHz (pA/√Hz): SPICE fit | "
            "$C_{\\mathrm{in}}$ (pF): SPICE / datasheet $C_{CM} + C_{DIFF}$ | capacitance driven by $e_n$ (pF) | $R_{\\mathrm{in}}$ | "
            "$Z_o$ at 100 MHz / 1 GHz (Ω) | unity gain from IN+ (GHz) |",
            "|---|---|---|---|---|---|---|---|---|"]
    for part in VENDOR_MODELS:
        p = datasheet(part)
        op = " ".join(smoke[part].get("op", []))
        m_iq = re.search(r"i\(vcc\) = (-?[0-9.]+e[-+][0-9]+)", op)
        iq = abs(float(m_iq.group(1))) * 1e3 if m_iq else None
        pr = params[part]
        zo = pr["z_out_open_loop_ohm"]
        z1, z2 = zo["100MHz"], zo["1000MHz"]
        rows.append(
            f"| {LABEL[part]} | {fmt(iq)} / {p['iq_ma']:.1f} | {pr['fit']['10MHz']['e_n_nV']:.2f} / {p['en']*1e9:.2f} | "
            f"{pr['fit']['10MHz']['i_n_pA']:.2f} / {pr['fit']['100MHz']['i_n_pA']:.2f} | "
            f"{pr['c_in_grounded_pF']['100MHz']:.2f} / {(p['c_cm'] + p['c_diff'])*1e12:.2f} | {pr['fit']['100MHz']['c_seen_pF']:.2f} | "
            f"{rin(pr['r_in_grounded_kohm'])} | {abs(complex(*z1)):.1f} / {abs(complex(*z2)):.1f} | {aol[part]['unity_gain_MHz']/1e3:.2f} |")
    return "\n".join(rows)


def rin(kohm):
    return f"{kohm/1e3:.0f} MΩ" if kohm >= 1e3 else f"{kohm:.2f} kΩ"


def near(d, s):
    """Datasheet phase d moved by whole turns to within 180 degrees of the SPICE phase s."""
    return d - 360 * round((d - s) / 360)


def table_open_loop(res):
    aol = res["aol"]
    rows = ["| Amplifier | 100 MHz | 300 MHz | 1 GHz | 3 GHz | from IN− at 1 GHz | from IN− at 3 GHz |",
            "|---|---|---|---|---|---|---|"]
    for part in VENDOR_MODELS:
        r = aol[part]["rows"]
        if not VENDOR_MODELS[part]["db"]:
            continue                      # outside the survey: no datasheet curve to compare
        pts = PARTS[VENDOR_MODELS[part]["db"]]["ol"]["points"]
        mag_end = max(p[0] for p in pts)
        ph_end = max(p[0] for p in pts if p[2] is not None)

        def cell(k):
            x = float(k.replace("MHz", "")) * 1e6
            sp = f"{r[k]['spice_dB']:.1f} dB, {r[k]['spice_deg']:.0f}°"
            if x <= 1.05 * ph_end:
                ds = f"{r[k]['datasheet_dB']:.1f} dB, {near(r[k]['datasheet_deg'], r[k]['spice_deg']):.0f}°"
            elif x <= 1.05 * mag_end:
                ds = f"{r[k]['datasheet_dB']:.1f} dB, phase not plotted"
            else:
                ds = "not plotted"
            return f"{sp} / {ds}"
        inv = lambda k: (f"{r[k]['inverting_dB'] - r[k]['spice_dB']:+.1f} dB, "
                         f"{(r[k]['inverting_deg'] - r[k]['spice_deg'] + 180) % 360 - 180:+.0f}°")
        rows.append(f"| {LABEL[part]} | {cell('100MHz')} | {cell('300MHz')} | {cell('1000MHz')} | {cell('3000MHz')} | "
                    f"{inv('1000MHz')} | {inv('3000MHz')} |")
    return "\n".join(rows)


def table_referee(res):
    ref = res["referee"]
    rows = ["| Amplifier and circuit | Datasheet statement | SPICE: $f_{-3\\,\\mathrm{dB}}$, peak; PM at $f_c$ | Datasheet curve, no $C_{\\mathrm{in}}$ (Table 4.1) | "
            "Datasheet curve with $C_{CM} + C_{DIFF}$ | Macromodel parameters, Eq. (53) |",
            "|---|---|---|---|---|---|"]
    circuit = {"OPA855": "non-inverting, 453 Ω / 75 Ω, $R_L$ = 200 Ω, ±2.5 V",
               "OPA818": "non-inverting, 301 Ω / 50.5 Ω, $R_L$ = 100 Ω, ±5 V",
               "OPA858": "non-inverting, 453 Ω / 75 Ω, $R_L$ = 200 Ω, ±2.5 V",
               "OPA856": "unity-gain buffer, $R_L$ = 200 Ω, ±2.5 V",
               "LMH6629": "non-inverting, 249 Ω / 27.4 Ω, $R_L$ = 100 Ω, ±2.5 V",
               "OPA859": "unity-gain buffer, $R_L$ = 200 Ω, ±2.5 V",
               "OPA846": "non-inverting, 300 Ω / 50 Ω, $R_L$ = 100 Ω, ±5 V",
               "OPA657": "non-inverting, 453 Ω / 75.5 Ω, $R_L$ = 100 Ω, ±5 V",
               "OPA847": "non-inverting, 431 Ω / 39.2 Ω, $R_L$ = 100 Ω, ±5 V",
               "LMH6624": "non-inverting, 500 Ω / 55.6 Ω, $R_L$ = 100 Ω, ±6 V",
               "THS4021": "non-inverting, 220 Ω / 24.4 Ω, $R_L$ = 150 Ω, ±15 V",
               "ADA4817-1": "unity-gain buffer, $R_L$ = 100 Ω, ±5 V",
               "AD8099": "non-inverting, 250 Ω / 250 Ω with 1.5 pF across $R_F$, 50 Ω in series with IN+, "
                         "CC network 50 Ω ∥ 1.5 pF then 4 pF to −$V_S$, $R_L$ = 1 kΩ, ±5 V",
               "ADA4899-1": "unity-gain buffer, 24.9 Ω in series with IN+, $R_L$ = 1 kΩ, ±5 V",
               "ADA4895-1": "non-inverting, 249 Ω / 27.7 Ω, $R_L$ = 1 kΩ, ±2.5 V",
               "OPA955": "non-inverting, 453 Ω / 75.5 Ω, $R_L$ = 200 Ω, ±2.5 V"}
    order = ["OPA855", "OPA818", "OPA858", "OPA856", "LMH6629", "OPA859", "OPA846"]
    for part in order + [p for p in ref if p not in order]:
        r = ref[part]
        s, lp = r["spice_closed_loop"], r["spice_loop"]
        cell = lambda k: ("not applicable (externally compensated)" if k not in r else
                          f"{fmt(r[k]['f3_MHz'], 0)} MHz, {r[k]['peak_dB']:.2f} dB; {fmt(r[k]['pm_deg'])}° at "
                          f"{fmt(r[k]['f_c_MHz'], 0)} MHz")
        rows.append(f"| {LABEL[part]}, {circuit[part]} | {r['stated']} | {fmt(s['f3_MHz'], 0)} MHz, {s['peak_dB']:.2f} dB; "
                    f"{fmt(lp['pm_deg'])}° at {fmt(lp['f_c_MHz'], 0)} MHz | {cell('analytical_datasheet_no_cin')} | "
                    f"{cell('analytical_datasheet_with_cin')} | {cell('macromodel_parameters')} |")
    return "\n".join(rows)


def table_pscan(res):
    """Every part's widest-band robust design at 1 pF and 2 kOhm (check 'pscan')."""
    scan = res["pscan"]
    rows = ["| Amplifier | Window meeting all criteria (edges set by) | Design: total $C_F$ | Worst PM / GM / peaking over its corners | "
            "$f_{-3\\,\\mathrm{dB}}$ nominal (range) | Noise at 100 MHz; penalty 10–150 MHz | Largest worst-case PM (at $C_F$) |",
            "|---|---|---|---|---|---|---|"]
    order = sorted(scan, key=lambda p: (not scan[p]["design"]["tol_pF"], -(scan[p]["design"]["f3_nominal_MHz"] or 0)))
    for part in order:
        e = scan[part]
        d, w, b = e["design"], e["window"], e["best_pm"]
        win = ("none" if not w else f"{w['lo_pF']:.3f}–{w['hi_pF']:.3f} pF ({w['lo_by'] or 'scan'} / {w['hi_by'] or 'beyond 2.40 pF'})"
               if not w["hi_open"] else f"{w['lo_pF']:.3f} pF to beyond 2.40 pF ({w['lo_by']} / –)")
        des = (f"{d['cf_pF']:.3f} ± {d['tol_pF']:.3f} pF" if d["tol_pF"] else f"{d['cf_pF']:.2f} pF (criteria not met)")
        gm = "–" if d["worst_gm"] is None else f"{d['worst_gm']:.1f} dB"
        rng = d["f3_range_MHz"]
        rows.append(f"| {LABEL[part]} | {win} | {des} | {d['worst_pm']:.1f}° / {gm} / {d['worst_peak']:.2f} dB | "
                    f"{fmt(d['f3_nominal_MHz'], 0)} MHz ({fmt(rng[0], 0)}–{fmt(rng[1], 0)}) | "
                    f"{d['noise']['noise_100MHz_pA']:.2f} pA/√Hz; {d['noise']['penalty_dB']:.2f} dB | "
                    f"{b['worst_pm']:.1f}° ({b['cf_pF']:.2f} pF) |")
    return "\n".join(rows)


def table_loop(res):
    loop, zt, step = res["loop"], res["zt"], res["step"]
    rows = ["| Design | SPICE nominal: $f_c$, PM, GM | SPICE over 9 corners: worst PM / worst GM | Survey model (datasheet curve): PM nominal / worst of 9 | "
            "SPICE $f_{-3\\,\\mathrm{dB}}$, peak | Survey $f_{-3\\,\\mathrm{dB}}$, peak | Step: overshoot, 10–90 % |",
            "|---|---|---|---|---|---|---|"]
    for part, R_F, C_D, C_F, label in DESIGNS:
        key = f"{part}|{label}"
        cs = loop[key]["corners"]
        nom = cs["dCF+0.0_dCD+0.0"]
        s = nom["spice"]
        pm_w = min(c["spice"]["pm_deg"] for c in cs.values())
        gms = [c["spice"]["gm_dB"] for c in cs.values() if c["spice"]["gm_dB"] is not None]
        gm_w = min(gms) if gms else None
        gmt = lambda g: "no −180° crossing" if g is None else f"{g:.1f} dB"
        a_nom = nom["analytical_datasheet"]["pm_deg"]
        a_w = min(c["analytical_datasheet"]["pm_deg"] for c in cs.values())
        flag = " (second crossing at 1 corner)" if any(not c["analytical_datasheet"]["stable"] for c in cs.values()) else ""
        z, za = zt[key]["spice"], zt[key]["analytical"]
        st = step[key]
        rows.append(f"| {design_name(part, R_F, C_D, C_F, label)} | {s['f_c_MHz']:.0f} MHz, {s['pm_deg']:.1f}°, {gmt(s['gm_dB'])} | "
                    f"{pm_w:.1f}° / {gmt(gm_w)} | {a_nom:.1f}° / {a_w:.1f}°{flag} | {z['f3_MHz']:.0f} MHz, {z['peak_dB']:.2f} dB | "
                    f"{za['f3_MHz']:.0f} MHz, {za['peak_dB']:.2f} dB | {st['overshoot_pct']:.1f} %, {st['rise_10_90_ps']:.0f} ps |")
    return "\n".join(rows)


def table_grid(res, key):
    cs = res["loop"][key]["corners"]
    rows = ["| Total $C_F$ | $C_D$ − 0.2 pF | $C_D$ nominal | $C_D$ + 0.2 pF |", "|---|---|---|---|"]
    d = res["loop"][key]
    for dcf in ("-0.1", "+0.0", "+0.1"):
        cells = []
        for dcd in ("-0.2", "+0.0", "+0.2"):
            c = cs[f"dCF{dcf}_dCD{dcd}"]
            star = " *" if not c["analytical_datasheet"]["stable"] else ""
            cells.append(f"{c['spice']['pm_deg']:.1f}° / {c['spice']['gm_dB']:.1f} dB ({c['analytical_datasheet']['pm_deg']:.1f}°{star})")
        rows.append(f"| {d['C_F_pF'] + float(dcf):.2f} pF | " + " | ".join(cells) + " |")
    return "\n".join(rows)


def table_consistency(res):
    con = res["consistency"]
    rows = ["| Design | $C_T$ of the model (pF) | Survey method, Eqs. (7)–(8): PM, GM, $f_{-3\\,\\mathrm{dB}}$ | Two-port, Eq. (52): PM, GM, $f_{-3\\,\\mathrm{dB}}$ | "
            "SPICE: PM, GM, $f_{-3\\,\\mathrm{dB}}$ | Noise, Eq. (17) against SPICE, 10–200 MHz |",
            "|---|---|---|---|---|---|"]
    for part, R_F, C_D, C_F, label in DESIGNS:
        r = con[f"{part}|{label}"]
        cell = lambda v: f"{v['pm_deg']:.1f}°, {fmt(v['gm_dB'])} dB, {v['f3_MHz']:.0f} MHz"
        dev = max(abs(v["model_pA"] / v["spice_pA"] - 1) for v in r["noise"].values()) * 100
        rows.append(f"| {design_name(part, R_F, C_D, C_F, label)} | {r['C_T_pF']:.2f} | {cell(r['survey'])} | {cell(r['two_port'])} | "
                    f"{cell(r['spice'])} | within {dev:.1f} % |")
    return "\n".join(rows)


def table_noise(res, spice):
    noise = res["noise"]
    rows = ["| Design | 50 MHz | 100 MHz | 200 MHz | Penalty 10–150 MHz: SPICE / survey central (high) |",
            "|---|---|---|---|---|"]
    for part, R_F, C_D, C_F, label in DESIGNS:
        key = f"{part}|{label}"
        sp = noise[key]["spot"]
        cell = lambda k: (f"{sp[k]['spice_pA']:.2f} / {sp[k]['analytical_central_pA']:.2f}"
                          + (f" ({sp[k]['analytical_high_pA']:.2f})" if "analytical_high_pA" in sp[k] else ""))
        p = PARTS[VENDOR_MODELS[part]["db"]]
        nz = noise_inputs(p)
        C_T = C_D + C_PCB_NOM + p["c_cm"] + p["c_diff"]
        f = np.logspace(7, np.log10(150e6), 400)
        ref = np.full_like(f, 4 * KT / R_F)
        pen = []
        for fm in ["central"] + (["high"] if "high" in noise_models_for(p) else []):
            S = tm.noise_components(f, R_F, C_T, C_F, nz, fet_model=fm)["total"]
            pen.append(10 * np.log10(np.trapezoid(S, f) / np.trapezoid(ref, f)))
        pen_s = f"{pen[0]:.2f}" + (f" ({pen[1]:.2f})" if len(pen) > 1 else "")
        rows.append(f"| {design_name(part, R_F, C_D, C_F, label)} | {cell('50MHz')} | {cell('100MHz')} | {cell('200MHz')} | "
                    f"{noise[key]['spice_penalty_10_150_dB']:.2f} / {pen_s} dB |")
    return "\n".join(rows)


def table_tone(res):
    tone = res["tone"]
    rows = ["| Amplifier, design | Tone | Table 6.2b amplitude | SPICE: amplitude at THD = −60 dBc | at THD = −40 dBc | At the Table 6.2b amplitude: HD2, HD3 |",
            "|---|---|---|---|---|---|"]
    for key, fr in tone.items():
        part = key.split("|")[0]
        for fk, r in fr.items():
            r1 = next(x for x in r["sweep"] if abs(x["frac"] - 1.0) < 1e-9)
            a60 = "–" if r["v_at_thd_m60"] is None else f"{r['v_at_thd_m60']:.2f} V ({r['frac_at_thd_m60']:.2f} ×)"
            a40 = "–" if r["v_at_thd_m40"] is None else f"{r['v_at_thd_m40']:.2f} V ({r['frac_at_thd_m40']:.2f} ×)"
            variant = {"OPA855": "A", "OPA818": "B"}[part]
            rows.append(f"| {part} ({variant}), 1 pF, 2 kΩ | {fk.replace('MHz', ' MHz')} | {r['claim_V']:.2f} V | {a60} | {a40} | "
                        f"{r1['hd2_dBc']:.1f}, {r1['hd3_dBc']:.1f} dBc |")
    return "\n".join(rows)


def table_bench(res):
    b = res["bench"]
    rows = ["| Total node capacitance $C_T$ | SPICE: PM, GM | SPICE: $\\lvert Z_T\\rvert$ at 50 MHz; peak | SPICE noise at 10 / 50 MHz (pA/√Hz) | "
            "Survey model: PM; $\\lvert Z_T\\rvert$ at 50 MHz; peak | Survey noise at 10 / 50 MHz (pA/√Hz) |",
            "|---|---|---|---|---|---|"]
    for k, r in b["rows"].items():
        s, a = r["spice"], r["survey"]
        rows.append(f"| {k.replace('pF', ' pF')} | {s['pm_deg']:.1f}°, {fmt(s['gm_dB'])} dB | {s['zt_50MHz_ohm']/1e3:.2f} kΩ; "
                    f"{s['peak_dB']:+.1f} dB at {s['f_peak_MHz']:.0f} MHz | {s['noise_10MHz_pA']:.2f} / {s['noise_50MHz_pA']:.2f} | "
                    f"{a['pm_deg']:.1f}°; {a['zt_50MHz_ohm']/1e3:.2f} kΩ; {a['peak_dB']:+.1f} dB at {a['f_peak_MHz']:.0f} MHz | "
                    f"{a['noise_10MHz_pA']:.2f} / {a['noise_50MHz_pA']:.2f} |")
    return "\n".join(rows)


def _win(w, survey=False):
    if not w:
        return "none"
    # in the survey model a second loop-gain crossing is scored as a failed phase margin
    by = {"pm": "second crossing" if survey else "PM", "gm": "GM", "peak": "peaking", None: "scan end"}
    lo = f"{'≤ ' if w['lo_open'] else ''}{w['lo_pF']:.3f}"
    hi = f"{'≥ ' if w['hi_open'] else ''}{w['hi_pF']:.3f}"
    lo_by = "peaking" if survey and w["lo_by"] == "peak" else by[w["lo_by"]]
    return f"{lo}–{hi} pF ({lo_by} / {by[w['hi_by']]})"


def table_cfscan_windows(res):
    """Variant A: windows of total C_F from SPICE and from the survey's model, and the minimum-gain rule."""
    a = res["cfscan"]["A"]
    rows = ["| Configuration | SPICE, nominal $C_D$ | SPICE, $C_D$ ± 0.2 pF | Survey model, $C_D$ ± 0.2 pF | Minimum-gain rule $C_T/6$, $C_D$ − 0.2 pF / nominal |",
            "|---|---|---|---|---|"]
    for key, r in a.items():
        cd = float(key.split(" pF")[0])
        rule = [(cd + d + 0.35 + 0.80) / 6 for d in (-0.2, 0.0)]
        rows.append(f"| {key.replace('kOhm', 'kΩ')} | {_win(r['window_nominal'])} | {_win(r['window_all_corners'])} | "
                    f"{_win(r['survey_window_all_corners'], survey=True)} | {rule[0]:.3f} / {rule[1]:.3f} pF |")
    return "\n".join(rows)


def table_cfscan_A_proposals(res):
    a = res["cfscan"]["A"]
    rows = ["| Configuration | Total $C_F$ (tolerance) | Nine corners: worst PM / worst GM / largest peaking | "
            "$f_{-3\\,\\mathrm{dB}}$: nominal (range over corners) | Noise at 100 / 200 MHz (pA/√Hz); penalty 10–150 MHz |",
            "|---|---|---|---|---|"]
    for key, r in a.items():
        p = r.get("proposal")
        if not p:
            continue
        n = p["noise"]
        rows.append(f"| {key.replace('kOhm', 'kΩ')} | {p['centre_pF']:.3f} ± {p['tol_pF']:.3f} pF | {p['pm_min']:.1f}° / "
                    f"{p['gm_min']:.1f} dB / {p['peak_max']:.2f} dB | {p['f3_nominal_MHz']:.0f} MHz ({p['f3_range_MHz'][0]:.0f}–"
                    f"{p['f3_range_MHz'][1]:.0f} MHz) | {n['noise_100MHz_pA']:.2f} / {n['noise_200MHz_pA']:.2f}; {n['penalty_dB']:.2f} dB |")
    return "\n".join(rows)


def table_cfscan_B(res):
    b = res["cfscan"]["B"]
    zt = res["zt"]
    present = {(R_F, C_D): (C_F, label) for part, R_F, C_D, C_F, label in DESIGNS if part == "OPA818"}
    rows = ["| Configuration | Present design: total $C_F$, $f_{-3\\,\\mathrm{dB}}$ | Requirement over the corners | "
            "Smallest $C_F$ meeting it at exactly that $C_F$: SPICE / survey model | Proposed total $C_F$ (tolerance) | "
            "Nine corners: worst PM | $f_{-3\\,\\mathrm{dB}}$ nominal (range) | Peaking nominal (largest) | Noise at 100 / 200 MHz; penalty |",
            "|---|---|---|---|---|---|---|---|---|"]
    for (R_F, C_D), (C_F0, label) in present.items():
        key = f"{C_D*1e12:g} pF, {R_F/1e3:g} kOhm"
        r = b[key]
        f30 = zt[f"OPA818|{label}"]["spice"]["f3_MHz"]
        first = True
        for lev, e in r["edges"].items():
            if e["spice"] is None:
                # the level is not reached anywhere in the scan: give the best worst case
                g = r["grid"]
                worst = [min(g[k][i]["pm_deg"] for k in g) for i in range(len(r["cf_pF"]))]
                i = int(np.argmax(worst))
                head = (f"| {key.replace('kOhm', 'kΩ')} | {C_F0*1e12:.2f} pF, {f30:.0f} MHz |" if first else "| | |")
                rows.append(f"{head} PM ≥ {lev}° | not reached: best worst case {worst[i]:.1f}° at {r['cf_pF'][i]:.2f} pF / none "
                            f"| – | – | – | – | – |")
                first = False
        for k, p in r["proposals"].items():
            lev, tol = k.split("|")
            e = r["edges"][lev]
            sp = "none" if not e["spice"] else f"{e['spice']['lo_pF']:.3f} pF"
            su = "none" if not e["survey"] else f"{e['survey']['lo_pF']:.3f} pF"
            n = p["noise"]
            head = (f"| {key.replace('kOhm', 'kΩ')} | {C_F0*1e12:.2f} pF, {f30:.0f} MHz |" if first else "| | |")
            rows.append(f"{head} PM ≥ {lev}°, $C_F$ ± {float(tol):g} pF | {sp} / {su} | {p['centre_pF']:.2f} ± {float(tol):g} pF | "
                        f"{p['pm_min']:.1f}° | {p['f3_nominal_MHz']:.0f} MHz ({p['f3_range_MHz'][0]:.0f}–{p['f3_range_MHz'][1]:.0f}) | "
                        f"{p['peak_nominal_dB']:.2f} dB ({p['peak_max']:.2f} dB) | {n['noise_100MHz_pA']:.2f} / {n['noise_200MHz_pA']:.2f}; "
                        f"{n['penalty_dB']:.2f} dB |")
            first = False
    return "\n".join(rows)


def cfscan_rules(res, c_in_pF=0.80, c_pcb_pF=0.35):
    """Variant A: where the gain margin crosses 3 dB and 0 dB, per configuration and photodiode
    corner, with the high-frequency noise gain NG = 1 + C_T/C_F there (C_T includes the
    model's own 0.80 pF); and the lower edge from phase margin alone."""
    out = []
    a = res["cfscan"]["A"]
    for key, r in a.items():
        cd0 = float(key.split(" pF")[0])
        x = np.array(r["cf_pF"])
        for k, rows in r["grid"].items():
            gm = np.array([np.nan if q["gm_dB"] is None or q["pm_deg"] < 0 else q["gm_dB"] for q in rows])
            ct = cd0 + float(k) + c_pcb_pF + c_in_pF
            parts = []
            for level in (3.0, 0.0):
                idx = np.where((gm[:-1] >= level) & ~(gm[1:] >= level))[0]
                if len(idx):
                    i = idx[0]
                    if np.isnan(gm[i + 1]):
                        parts.append(f"GM {level:g} dB: beyond {x[i]:.2f} pF")
                        continue
                    xc = x[i] + (level - gm[i]) * (x[i + 1] - x[i]) / (gm[i + 1] - gm[i])
                    parts.append(f"GM {level:g} dB at C_F {xc:.3f} pF, NG {1 + ct / xc:.2f}")
                else:
                    parts.append(f"GM {level:g} dB: not reached")
            out.append(f"{key}, C_D {cd0 + float(k):.1f} pF: " + "; ".join(parts))
        pm = np.array([[q["pm_deg"] for q in rows] for rows in r["grid"].values()]).min(0)
        i = np.where((pm[:-1] < 45) & (pm[1:] >= 45))[0]
        if len(i):
            i = i[0]
            out.append(f"{key}: worst-case PM reaches 45 deg at C_F {x[i] + (45 - pm[i]) * (x[i+1] - x[i]) / (pm[i+1] - pm[i]):.3f} pF")
    for key, r in res["cfscan"]["B"].items():
        g = r["grid"]["+0.0"]
        i = 0
        out.append(f"B {key}: at the smallest C_F {r['cf_pF'][i]:.2f} pF, nominal f3 {g[i]['f3_MHz']:.0f} MHz with {g[i]['peak_dB']:.1f} dB peaking; "
                   f"crossover {g[i]['f_c_MHz']:.0f} MHz")
    return "\n".join(out)


def hidden_margin(res, spice):
    """|Z_T|/R_F at its high-frequency bump for the worst-GM corner of each OPA855 design,
    from the SPICE loop gain (Z_T = -Z_F T/(1+T)), to show how little a closed-loop plot reveals."""
    out = []
    for part, R_F, C_D, C_F, label in DESIGNS:
        if part != "OPA855":
            continue
        cs = res["loop"][f"{part}|{label}"]["corners"]
        k = min(cs, key=lambda kk: cs[kk]["spice"]["gm_dB"] if cs[kk]["spice"]["gm_dB"] is not None else 1e9)
        dcf = float(k.split("_")[0][3:]) * 1e-12
        dcd = float(k.split("_")[1][3:]) * 1e-12
        lp = np.load(spice / "runs" / "loop" / tag(part, R_F, C_D + dcd, C_F + dcf) / "loop.npy")
        f, T = lp[0], lp[1] + 1j * lp[2]
        Z_F = R_F / (1 + 2j * np.pi * f * R_F * (C_F + dcf))
        H = np.abs(-Z_F * T / (1 + T)) / R_F
        hi = (f > 2e9) & (f < 8e9)
        i = np.argmax(np.where(hi, H, 0))
        lo = f < 1e9
        out.append(f"{design_name(part, R_F, C_D, C_F, label)}, corner {k}: GM {cs[k]['spice']['gm_dB']:.1f} dB; "
                   f"|Z_T|/R_F bump {20*np.log10(H[i]):.1f} dB at {f[i]/1e9:.2f} GHz; in-band peak "
                   f"{20*np.log10(H[lo].max()):.2f} dB")
    return "\n".join(out)


def typeset(block):
    """Typographic minus before numbers and degree signs, as in the rest of the survey;
    table separator rows and math are left alone."""
    out = []
    for line in block.splitlines():
        if line.startswith("|---"):
            out.append(line)
            continue
        parts = re.split(r"(\$[^$]*\$)", line)
        parts = [p if p.startswith("$") else re.sub(r"(?<![\w.])-(?=\d)", "−", p.replace(" deg ", "° ").replace(" deg)", "°)"))
                 for p in parts]
        out.append("".join(parts))
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--spice", default=str(HERE.parent / "spice"))
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    spice = Path(a.spice)
    names = ("smoke", "aol", "referee", "loop", "zt", "noise", "step", "tone", "params", "bench", "cfscan", "pscan", "consistency")
    res = {n: json.loads((spice / "results" / f"{n}.json").read_text(encoding="utf-8")) for n in names}
    parts = [("Macromodel parameters", table_parameters(res)), ("Open-loop gain: macromodel / datasheet curve", table_open_loop(res)),
             ("Datasheet test circuits", table_referee(res)), ("TIA loop, corners, response", table_loop(res)),
             ("OPA855 1 pF 2 kOhm corner grid", table_grid(res, "OPA855|A, 1 pF, 2 kOhm")),
             ("OPA855 1 pF 1.5 kOhm corner grid", table_grid(res, "OPA855|A, 1 pF, 1.5 kOhm")),
             ("Consistency", table_consistency(res)), ("Noise", table_noise(res, spice)), ("Tone", table_tone(res)),
             ("OPA846 bench board", table_bench(res)),
             ("Variant A C_F windows", table_cfscan_windows(res)),
             ("Variant A proposed C_F", table_cfscan_A_proposals(res)),
             ("Variant B smaller C_F", table_cfscan_B(res)),
             ("Best design of every part, 1 pF, 2 kOhm", table_pscan(res)),
             ("C_F scan rules (text)", cfscan_rules(res)),
             ("Hidden margin (text)", hidden_margin(res, spice))]
    text = "\n\n".join(f"### {t}\n\n{typeset(b)}" for t, b in parts) + "\n"
    out = Path(a.out) if a.out else spice / "results" / "tables.md"
    out.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
