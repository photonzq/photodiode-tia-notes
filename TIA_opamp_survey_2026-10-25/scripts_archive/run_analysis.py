"""Compute stability, bandwidth, noise and dynamic range for every candidate.

Usage: python run_analysis.py <out_dir>

Inputs come from parts_db.PARTS (curated datasheet values with citations).
Outputs (in <out_dir>): results.json plus Markdown tables that the report
quotes.  Everything is analytical: open-loop models are fitted to digitized
datasheet curves (tia_model.fit_open_loop); no SPICE model is used.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

import tia_model as tm
from parts_db import PARTS

# ---------------------------------------------------------------------------
# Common assumptions (Section 1 of the report)
# ---------------------------------------------------------------------------
C_D = 1.0e-12
C_PCB_NOM, C_PCB_RANGE = 0.35e-12, (0.2e-12, 0.5e-12)
C_FPAR_NOM, C_FPAR_RANGE = 0.20e-12, (0.1e-12, 0.3e-12)
R_F_LIST = (1500.0, 2000.0)
SPOT_F = (1e6, 10e6, 50e6, 100e6, 150e6, 200e6)
BANDS = ((10e6, 150e6), (10e6, 200e6))
I_DC_LIST = (0.0, 1e-4, 1e-3, 1e-2)
PEAK_FLAT_DB, PEAK_AGGR_DB = 0.01, 1.0
CF_DISCRETE_MIN = 0.1e-12      # smallest practical discrete feedback capacitor
F_NOISE = np.linspace(1e4, 400e6, 40001)   # linear grid for band integrals
DR_BAND = 150e6
DR_FREQS = (100e6, 150e6)


def open_loop_model(p):
    """Open-loop models of a part.

    Returns (primary, check, rms_g, rms_p): the primary model interpolates the
    digitized datasheet curve directly; the check model is the pole-delay fit
    of Eq. (15).  Parts without a digitized curve get a constructed model.
    """
    ol = p["ol"]
    if ol.get("points"):
        A0 = 10 ** (ol["A0_dB"] / 20) if ol.get("A0_dB") is not None else None
        fit, rms_g, rms_p = tm.fit_open_loop(
            ol["points"], A0=A0, n_hi_poles=ol.get("n_hi_poles", 2),
            use_delay=ol.get("use_delay", True), gbw_hint=p.get("gbw"),
            f_max_fit=ol.get("fit_f_max"))
        fit.note = f"pole-delay fit, rms {rms_g:.2f} dB / {rms_p:.1f} deg"
        interp = tm.InterpOpenLoop.from_points(
            ol["points"], note=f"interpolated datasheet curve ({len(ol['points'])} points)")
        return interp, fit, rms_g, rms_p
    # Fallback: dominant pole from GBW, second pole placed so that the phase
    # margin at the minimum stable gain is ol['pm_at_gmin'] degrees.
    A0 = 10 ** (ol.get("A0_dB", 80) / 20)
    gbw = p["gbw"]
    g_min = max(p["g_min"], 1.0)
    pm = ol.get("pm_at_gmin", 45.0)
    f_c = gbw / g_min
    f_p2 = f_c / np.tan(np.radians(90 - pm))
    model = tm.OpenLoopModel(A0=A0, f_p1=gbw / A0, f_poles_hi=(f_p2,),
                             note=f"constructed: GBW {gbw/1e9:.2f} GHz, PM {pm:.0f} deg at G={g_min:g}")
    return model, None, float("nan"), float("nan")


def noise_inputs(p):
    return tm.NoiseInputs(en_flat=p["en"], in_flat=p["in_"],
                          en_pts=p.get("en_pts", []), in_pts=p.get("in_pts", []),
                          c_in_amp=p["c_cm"] + p["c_diff"],
                          c_gate=2 * p["c_diff"], fet=p.get("fet", False))


def noise_models_for(p):
    """Which current-noise treatments apply (Section 2.7)."""
    if p.get("fet"):
        return ("central", "low", "high") if p.get("in_pts") else ("central", "low")
    if p.get("in_curve_is_physical") or p.get("in_rises"):
        return ("central", "high")
    return ("central",)


def _metrics_row(m):
    return dict(f3_MHz=m["f_3dB"] / 1e6, pm_deg=m["pm_deg"], gm_dB=m["gm_dB"],
                fc_MHz=m["f_c"] / 1e6, ng_at_fc=m["ng_at_fc"], ng_hf=m["ng_hf"],
                peaking_dB=m["peaking_dB"], stable=m["stable"],
                second_crossing=m["second_crossing"])


def design_block(ol, R_F, C_T, C_Fpar, g_min):
    """Flat (<= 0.01 dB) and 1-dB designs plus the parasitic-only case.

    'required' is the total C_F the design calls for; 'realized' is what a
    board can have, max(required, C_F,par).  Metrics are for the realized C_F.
    """
    out = dict(C_F_max_for_gmin_pF=tm.cf_max_for_gmin(C_T, g_min) * 1e12)
    for tag, target in (("flat", PEAK_FLAT_DB), ("peak1dB", PEAK_AGGR_DB)):
        cf = tm.design_cf(ol, R_F, C_T, target)
        if not np.isfinite(cf):
            out[tag] = dict(C_F_req_pF=None, note="no stable C_F meets the peaking target")
            continue
        cf_real = max(cf, C_Fpar)
        m = tm.loop_metrics(ol, R_F, C_T, cf_real)
        cf_ext = cf - C_Fpar
        flags = []
        if cf_ext < 0:
            flags.append("parasitic C_F exceeds the required value; realized design is parasitic-limited")
        elif cf_ext < CF_DISCRETE_MIN:
            flags.append("external C_F below 0.1 pF: not a reproducible discrete part")
        if not m["stable"]:
            flags.append("UNSTABLE at the realized C_F")
        elif np.isfinite(m["pm_deg"]) and m["pm_deg"] < 45:
            flags.append("phase margin below 45 deg")
        if np.isfinite(m["ng_at_fc"]) and m["ng_at_fc"] < g_min:
            flags.append("noise gain at crossover below the minimum stable gain")
        row = dict(C_F_req_pF=cf * 1e12, C_F_real_pF=cf_real * 1e12, C_F_ext_pF=cf_ext * 1e12)
        row.update(_metrics_row(m))
        row["flags"] = flags
        out[tag] = row
    m = tm.loop_metrics(ol, R_F, C_T, C_Fpar)
    out["parasitic_only"] = dict(C_F_real_pF=C_Fpar * 1e12, **_metrics_row(m))
    # largest phase margin over stable, realizable C_F (>= the parasitic value)
    best = None
    for cf in tm.CF_SCAN:
        if cf < C_Fpar:
            continue
        mm = tm.loop_metrics(ol, R_F, C_T, cf)
        if mm["stable"] and (best is None or mm["pm_deg"] > best[1]["pm_deg"]):
            best = (cf, mm)
    if best:
        out["max_pm"] = dict(C_F_real_pF=best[0] * 1e12, C_F_ext_pF=(best[0] - C_Fpar) * 1e12,
                             **_metrics_row(best[1]))
    return out


C_ADD_SCAN = (0.0, 0.25e-12, 0.5e-12, 1e-12, 1.5e-12, 2e-12, 3e-12, 4e-12, 6e-12, 8e-12)
PM_ROBUST = 45.0


def robust_design(ol, R_F, C_T0, C_Fpar, pm_min=PM_ROBUST, peak_max=PEAK_AGGR_DB):
    """Widest bandwidth with phase margin >= pm_min and peaking <= peak_max.

    Searches deliberately added input capacitance C_add (to raise the noise gain
    of decompensated parts) together with the total feedback capacitance C_F
    (never below the parasitic value).  Returns None if nothing qualifies.
    """
    best = None
    for c_add in C_ADD_SCAN:
        C_T = C_T0 + c_add
        for cf in tm.CF_SCAN:
            if cf < C_Fpar:
                continue
            m = tm.loop_metrics(ol, R_F, C_T, cf)
            if not (m["stable"] and m["pm_deg"] >= pm_min and m["peaking_dB"] <= peak_max):
                continue
            if best is None or m["f_3dB"] > best["f3_MHz"] * 1e6:
                best = dict(C_add_pF=c_add * 1e12, C_T_pF=C_T * 1e12, C_F_real_pF=cf * 1e12,
                            C_F_ext_pF=(cf - C_Fpar) * 1e12, **_metrics_row(m))
    return best


def corner_block(ol, R_F, p, cf_ext_nom):
    """Fixed board (one external C_F) evaluated at the parasitic corners."""
    rows = {}
    for c_pcb in C_PCB_RANGE:
        for c_par in C_FPAR_RANGE:
            ct = C_D + c_pcb + p["c_cm"] + p["c_diff"]
            cf = max(cf_ext_nom, 0.0) + c_par
            m = tm.loop_metrics(ol, R_F, ct, cf)
            rows[f"Cpcb{c_pcb*1e12:.1f}_Cfpar{c_par*1e12:.1f}"] = dict(C_T_pF=ct * 1e12, C_F_pF=cf * 1e12,
                                                                     **_metrics_row(m))
    return rows


def noise_block(ol, nz, R_F, C_T, C_F, fet_models):
    """Spot and band noise (input-referred and output-referred) for one design."""
    f_spot = np.array(SPOT_F)
    Z_T, _, _ = tm.tia_tf(f_spot, ol, R_F, C_T, C_F)
    i_rf = tm.johnson_current_asd(R_F)
    res = {}
    for fm in fet_models:
        comp = tm.noise_components(f_spot, R_F, C_T, C_F, nz, fet_model=fm)
        tot = np.sqrt(comp["total"])
        res[fm] = dict(
            f_MHz=[f / 1e6 for f in SPOT_F],
            i_in_pA=list(tot * 1e12),
            parts_pA={k: list(np.sqrt(v) * 1e12) for k, v in comp.items() if k != "total"},
            v_out_nV=list(tot * np.abs(Z_T) * 1e9),
            penalty_vs_RF_dB=list(20 * np.log10(tot / i_rf)),
            ratio_to_50ohm_dB=list(20 * np.log10(tot / tm.johnson_current_asd(50.0))),
        )
        compN = tm.noise_components(F_NOISE, R_F, C_T, C_F, nz, fet_model=fm)
        S_ref = np.full_like(F_NOISE, 4 * tm.K_B * tm.T_ROOM / R_F)
        res[fm]["band_penalty_dB"] = {
            f"{lo/1e6:.0f}-{hi/1e6:.0f} MHz": tm.band_average_penalty_db(F_NOISE, compN["total"], S_ref, lo, hi)
            for lo, hi in BANDS}
        res[fm]["band_rms_nA"] = {
            f"{lo/1e6:.0f}-{hi/1e6:.0f} MHz": tm.integrated_rms(F_NOISE, compN["total"], lo, hi) * 1e9
            for lo, hi in BANDS}
        # with photocurrent shot noise: excess of total over (shot + R_F) at 100 and 200 MHz
        shot = {}
        for idc in I_DC_LIST[1:]:
            c2 = tm.noise_components(f_spot, R_F, C_T, C_F, nz, i_dc=idc, fet_model=fm)
            ideal = 4 * tm.K_B * tm.T_ROOM / R_F + 2 * tm.Q_E * idc
            shot[f"{idc*1e3:g} mA"] = dict(
                total_pA=list(np.sqrt(c2["total"]) * 1e12),
                excess_over_shot_plus_RF_dB=list(10 * np.log10(c2["total"] / ideal)),
                shot_clearance_dB=list(10 * np.log10(2 * tm.Q_E * idc / (c2["total"] - 2 * tm.Q_E * idc))))
        res[fm]["with_dc"] = shot
    # wideband output noise, no post-filter (needs the A(s) model above crossover)
    f_w = np.logspace(4, 10.3, 20000)
    Zw, _, _ = tm.tia_tf(f_w, ol, R_F, C_T, C_F)
    cw = tm.noise_components(f_w, R_F, C_T, C_F, nz, fet_model="central")
    res["v_out_rms_unfiltered_mV"] = float(np.sqrt(np.trapezoid(cw["total"] * np.abs(Zw) ** 2, f_w)) * 1e3)
    res["v_out_rms_RF_only_mV"] = float(np.sqrt(np.trapezoid(cw["RF"] * np.abs(Zw) ** 2, f_w)) * 1e3)
    return res


def dr_block(p, ol, nz, R_F, C_T, C_F):
    """DC headroom, AC amplitude limits and dynamic range (Section 6 definitions)."""
    out = {}
    s = p.get("dr")
    if not s:
        return None
    VOL, VOH = s["swing_light"]
    lo_icr, hi_icr = s["icr"]
    # DC-coupled maximum photocurrent, both photodiode orientations
    i_down = (min(hi_icr, VOH) - VOL) / R_F
    i_up = (VOH - max(lo_icr, VOL)) / R_F
    out["I_DC_max_mA"] = max(i_down, i_up) * 1e3
    out["I_DC_max_orientation"] = "photocurrent into the node (output falls)" if i_down >= i_up \
        else "photocurrent out of the node (output rises)"
    out["swing_light_V"] = [VOL, VOH]
    loads = {"high-Z": (s["swing_light"], np.inf)}
    if s.get("swing_100"):
        loads["50-ohm back-terminated (100 ohm)"] = (s["swing_100"], 100.0)
    i_out = (s.get("iout_ma") or np.inf) * 1e-3
    sr = s["sr"] * 1e6
    rows = {}
    f_band = np.linspace(1e4, DR_BAND, 30001)
    for load_name, ((vol, voh), R_L) in loads.items():
        r = {}
        for f0 in DR_FREQS:
            Z, _, _ = tm.tia_tf(np.array([f0]), ol, R_F, C_T, C_F)
            v_swing = (voh - vol) / 2
            v_slew = sr / (2 * np.pi * f0)
            G_load = (0 if np.isinf(R_L) else 1 / R_L) + 1 / R_F + 2 * np.pi * f0 * C_F
            v_cur = i_out / G_load
            v_pk = min(v_swing, v_slew, v_cur)
            limiter = ["swing", "slew rate", "output current"][int(np.argmin([v_swing, v_slew, v_cur]))]
            i_pk = v_pk / np.abs(Z[0])
            res_f = dict(v_pk_V=v_pk, limiter=limiter, i_ph_pk_mA=i_pk * 1e3,
                         v_swing_pk_V=v_swing, v_slew_pk_V=v_slew, v_current_pk_V=v_cur)
            drs = {}
            for idc in I_DC_LIST:
                comp = tm.noise_components(f_band, R_F, C_T, C_F, nz, i_dc=idc)
                i_rms = tm.integrated_rms(f_band, comp["total"], f_band[0], f_band[-1])
                S0 = tm.noise_components(np.array([f0]), R_F, C_T, C_F, nz, i_dc=idc)["total"][0]
                drs[f"{idc*1e3:g} mA"] = dict(
                    noise_rms_nA=i_rms * 1e9,
                    DR_150MHz_dB=20 * np.log10(i_pk / np.sqrt(2) / i_rms),
                    CNR_1Hz_dBHz=20 * np.log10(i_pk / np.sqrt(2) / np.sqrt(S0)))
            res_f["dr_with_dc_cancelled"] = drs
            r[f"{f0/1e6:.0f} MHz"] = res_f
        rows[load_name] = r
    out["ac"] = rows
    return out


def run(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    results = {}
    for name, p in PARTS.items():
        ol, ol_fit, rms_g, rms_p = open_loop_model(p)
        nz = noise_inputs(p)
        fet_models = noise_models_for(p)
        olinfo = dict(primary=ol.note, gbw_from_curve_GHz=ol.gbw / 1e9)
        if ol_fit is not None:
            olinfo.update(fit=dict(A0_dB=20 * np.log10(ol_fit.A0), f_p1_Hz=ol_fit.f_p1,
                                   f_hi_Hz=list(ol_fit.f_poles_hi), tau_ps=ol_fit.tau * 1e12,
                                   gbw_GHz=ol_fit.gbw / 1e9, note=ol_fit.note,
                                   rms_dB=rms_g, rms_deg=rms_p))
        pr = dict(open_loop=olinfo, c_amp_pF=(p["c_cm"] + p["c_diff"]) * 1e12)
        for R_F in R_F_LIST:
            key = f"RF_{R_F:.0f}"
            C_T = C_D + C_PCB_NOM + p["c_cm"] + p["c_diff"]
            d = design_block(ol, R_F, C_T, C_FPAR_NOM, p["g_min"])
            if ol_fit is not None:
                d["check_with_fit"] = design_block(ol_fit, R_F, C_T, C_FPAR_NOM, p["g_min"])
            d["robust45"] = robust_design(ol, R_F, C_T, C_FPAR_NOM)
            cal = p["ol"].get("calibrate")
            if cal and isinstance(ol, tm.InterpOpenLoop):
                ol_cal = tm.calibrated_interp(ol, cal["gain_scale_dB"], cal["pm_target_deg"], cal["g_noise"])
                d["check_calibrated"] = design_block(ol_cal, R_F, C_T, C_FPAR_NOM, p["g_min"])
                d["check_calibrated"]["robust45"] = robust_design(ol_cal, R_F, C_T, C_FPAR_NOM)
                d["check_calibrated"]["model"] = ol_cal.note
            corners = {}
            noise = {}
            dr = {}
            for tag in ("flat", "peak1dB"):
                if d[tag].get("C_F_req_pF") is None:
                    continue
                cf_eff = d[tag]["C_F_real_pF"] * 1e-12
                corners[tag] = corner_block(ol, R_F, p, d[tag]["C_F_ext_pF"] * 1e-12)
                noise[tag] = noise_block(ol, nz, R_F, C_T, cf_eff, fet_models)
                dr[tag] = dr_block(p, ol, nz, R_F, C_T, cf_eff)
            if d.get("robust45"):
                rb = d["robust45"]
                ct_r, cf_r = rb["C_T_pF"] * 1e-12, rb["C_F_real_pF"] * 1e-12
                noise["robust45"] = noise_block(ol, nz, R_F, ct_r, cf_r, fet_models)
                dr["robust45"] = dr_block(p, ol, nz, R_F, ct_r, cf_r)
            pr[key] = dict(C_T_pF=C_T * 1e12, designs=d, corners=corners, noise=noise, dr=dr)
        results[name] = pr
        print(f"{name:12s} done  ({ol.note})")
    with open(out_dir / "results.json", "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=1, default=lambda o: None if o is None else float(o))


if __name__ == "__main__":
    run(Path(sys.argv[1]))
