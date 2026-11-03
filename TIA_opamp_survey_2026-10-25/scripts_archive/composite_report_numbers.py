"""Every number that Sections 11.5-11.7 of the survey quote for the two composite TIAs, printed from
the saved results (no simulation): spice/results/composite_*.json (spice_composite_checks.py),
data/results/composite_analytical.json (composite_tia.py), data/digitization_checks/
fig8-1_datasheet_curves.json (overlay_digitized.py) and spice/results/dr_comparison.json.

usage: python composite_report_numbers.py [--spice <folder>]
"""
import argparse
import json
from pathlib import Path

import numpy as np

import composite_tia as ct

HERE = Path(__file__).resolve().parent


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def fmt(v, p=1):
    return "–" if v is None else f"{v:.{p}f}"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--spice", type=Path, default=HERE.parent / "spice")
    a = ap.parse_args()
    res = a.spice / "results"
    ana = load(HERE.parent / "data" / "results" / "composite_analytical.json")
    ds81 = load(HERE.parent / "data" / "digitization_checks" / "fig8-1_datasheet_curves.json")
    ref = load(res / "composite_ths_referee.json")
    zol = load(res / "composite_ths_zol.json")
    smoke = load(res / "composite_ths_smoke.json")
    hvc = load(res / "composite_hv_compare.json")
    hvv = load(res / "composite_hv_verify.json")
    tone = load(res / "composite_hv_tone.json")
    fdev = load(res / "composite_fet_devices.json")
    fcmp = load(res / "composite_fet_compare.json")
    fver = load(res / "composite_fet_verify.json")
    drc = load(res / "dr_comparison.json")

    print("== THS3491 closed loop, Fig 9-1 circuit: -3 dB (MHz) / peaking (dB)")
    F = np.logspace(5, np.log10(5e9), 3000)
    for g, rf, rg in ((2, 976.0, 976.0), (5, 576.0, 143.0), (10, 499.0, 54.9), (20, 383.0, 20.0)):
        d = ds81[f"G{g}"]
        s = ref[f"G{g}"]
        H = ct.h2(F, g)
        m = ct.metrics(F, np.full_like(F, np.inf), H, r_f=g)
        H0 = ct.h2(F, g, c_n=0.0)
        m0 = ct.metrics(F, np.full_like(F, np.inf), H0, r_f=g)
        fc = zol["formula_check"][f"G{g}"]
        print(f"G={g:2d} R_F={rf:g}: datasheet {d['f3_MHz']:.0f} / {d['peak_dB']:.2f} | SPICE {s['f3_MHz']:.0f} / {s['peak_dB']:.2f} | "
              f"Eq.71 Fig 8-22 + 1.2 pF {fmt(m['f3_MHz'], 0)} / {m['peak_dB']:.2f} | textbook Fig 8-22 {fmt(m0['f3_MHz'], 0)} / "
              f"{m0['peak_dB']:.2f} | Eq.71 with the model's Z_OL, Z_i: {fc['formula_with_cn']['f3_MHz']:.0f} / "
              f"{fc['formula_with_cn']['peak_dB']:.2f} (model pin-to-pin {fc['spice']['f3_MHz']:.0f} / {fc['spice']['peak_dB']:.2f}), "
              f"largest deviation {fc['max_dev_dB_to_3GHz']:.2f} dB, {fc['max_dev_deg_to_3GHz']:.1f} deg")
    print("== THS3491 Z_OL at no load: Fig 8-22 against the model (pin, and internal)")
    pts = zol["noload"]["points"]
    a_int = np.load(a.spice / "runs" / "composite" / "ths_zol" / "zol_internal_noload.npy")
    fz, zi = a_int[0].real, a_int[1] + 1j * a_int[2]
    for x in (1e8, 3e8, 5e8, 7.7e8):
        k = f"{x/1e6:g}MHz"
        zd = ct.zol(np.array([x]))[0]
        j = int(np.argmin(np.abs(np.log10(fz) - np.log10(x))))
        print(f"{x/1e6:5.0f} MHz: Fig 8-22 {20*np.log10(abs(zd)):.1f} dBohm {np.degrees(np.angle(zd)):.1f} deg | model pin "
              f"{pts[k]['dB']:.1f} {pts[k]['deg']:.1f} | internal {20*np.log10(abs(zi[j])):.1f} {np.degrees(np.angle(zi[j])):.1f}")
    print("== THS3491 model noise and supply (G = 5):", smoke["Rs0.001"]["op"], "e_n", [round(x, 2) for x in smoke["e_n_nV_if_inn_as_datasheet"]],
          "i_n+", [round(x, 1) for x in smoke["i_np_pA"]], "output noise", smoke["Rs0.001"]["onoise_nV"])

    print("== HV composite, analytical (macromodel parameters) against SPICE, nominal capacitances")
    d_pm, d_gm, d_f3, d_fc, d_n = [], [], [], [], []
    for k, r in hvc.items():
        s, an = r["spice"], r["analytical"]
        if s["pm_deg"] is not None and an["pm_deg"] is not None:
            d_pm.append(abs(s["pm_deg"] - an["pm_deg"]))
        if s["gm_dB"] is not None and an["gm_dB"] is not None:
            d_gm.append(abs(s["gm_dB"] - an["gm_dB"]))
        if s["f3_MHz"] and an["f3_MHz"]:
            d_f3.append(abs(s["f3_MHz"] - an["f3_MHz"]))
        d_fc.append(abs(s["f_c_MHz"] - an["f_c_MHz"]))
        d_n.append(abs(s["noise_nA"] - an["noise_nA"]) / s["noise_nA"] * 100)
        print(f"  {k:22s} SPICE f_c {s['f_c_MHz']:.0f} PM {fmt(s['pm_deg'])} GM {fmt(s['gm_dB'])} f3 {fmt(s['f3_MHz'], 0)} "
              f"pk {s['peak_dB']:.2f} noise {s['noise_nA']:.1f} | analytical f_c {an['f_c_MHz']:.0f} PM {fmt(an['pm_deg'])} "
              f"GM {fmt(an['gm_dB'])} f3 {fmt(an['f3_MHz'], 0)} pk {an['peak_dB']:.2f} noise {an['noise_nA']:.1f}")
    print(f"  largest differences: PM {max(d_pm):.1f} deg, GM {max(d_gm):.2f} dB, f3 {max(d_f3):.1f} MHz, f_c {max(d_fc):.1f} MHz, "
          f"noise {max(d_n):.2f} %")

    print("== HV composite, plain topology (analytical, macromodel parameters): largest worst-corner PM per G2")
    for g2 in ct.G2_GRID:
        r = ana["hv"]["macromodels"][f"plain_G{g2:g}"]["largest_worst_pm"]
        n, w = r["nominal"], r["worst"]
        print(f"  G2={g2:g}: C_F {r['c_f_pF']:.3f} pF: nominal f_c {fmt(n['f_c_MHz'], 0)} MHz PM {fmt(n['pm_deg'])}, worst PM {fmt(w['pm_deg'])}")

    print("== HV composite, robust designs over the 27 corners (SPICE / analytical) and dynamic range")
    rows = {}
    for lab, v in hvv.items():
        g2, cf, cl = v["g2"], v["c_f_pF"] * 1e-12, v["c_l_pF"] * 1e-12
        cmp = ct.HVComposite("macromodels", g2)
        d = ct.hv_design(cmp, cf, cl, with_corners=False)
        sw, aw = v["spice_worst"], v["analytical_worst"]
        n_sp = v["spice_nominal"]["noise_nA"] * 1e-9
        out = []
        for f0 in (100e6, 150e6):
            vpk, lim, zt = cmp.ceiling(f0, cf, cl)
            dr_eq = [ct.dr_db(vpk / (np.sqrt(2) * zt), n_sp, i) for i in (0.0, 1e-4, 1e-3, 1e-2)]
            dr_rf = [ct.dr_db(vpk / (np.sqrt(2) * ct.R_F), n_sp, i) for i in (0.0, 1e-4, 1e-3, 1e-2)]
            out.append((f0, vpk, zt, dr_eq, dr_rf))
        rows[lab] = out
        print(f"  {lab:24s} C_F {v['c_f_pF']:.3f} C_L {v['c_l_pF']:.2f} R_F2 {ct.rf2_for(g2):.0f} | SPICE worst PM {fmt(sw['pm_deg'])} "
              f"GM {fmt(sw['gm_dB'])} pk {sw['peak_dB']:.2f} f3 {fmt(sw['f3_MHz'], 0)} robust {v['spice_robust']} | analytical "
              f"{fmt(aw['pm_deg'])} {fmt(aw['gm_dB'])} {aw['peak_dB']:.2f} {fmt(aw['f3_MHz'], 0)} | nominal f3 SPICE "
              f"{fmt(v['spice_nominal']['f3_MHz'], 0)} PM {fmt(v['spice_nominal']['pm_deg'])} | noise SPICE "
              f"{v['spice_nominal']['noise_nA']:.1f} nA, analytical {v['analytical_noise_nA']:.1f} | parts "
              + str({k: round(x, 1) for k, x in d['noise_parts_nA'].items()}))
        for f0, vpk, zt, dr_eq, dr_rf in out:
            print(f"      {f0/1e6:g} MHz: V_pk {vpk:.2f} V, |Z_T| {zt:.0f} ohm | DR Eq.56 " + "/".join(f"{x:.1f}" for x in dr_eq)
                  + " | at |Z_T| = R_F " + "/".join(f"{x:.1f}" for x in dr_rf))
    print("== single op-amp designs (Section 11, SPICE), 100 MHz, 0/0.1/1/10 mA")
    for k, o in drc["op_amps"].items():
        print(f"  {k:8s} " + "/".join(f"{x:.1f}" for x in o["spice"]["dr_at_dB"].values()))
    print("== +/-7.5 V supply, the same designs: ceiling and DR (Eq. 56, and at |Z_T| = R_F)")
    for lab, v in hvv.items():
        if not lab.startswith("macromodels"):
            continue
        g2, cf, cl = v["g2"], v["c_f_pF"] * 1e-12, v["c_l_pF"] * 1e-12
        cmp = ct.HVComposite("macromodels", g2)
        n_sp = v["spice_nominal"]["noise_nA"] * 1e-9
        for f0 in (100e6, 150e6):
            vpk, lim, zt = cmp.ceiling(f0, cf, cl, supply=7.5)
            print(f"  {lab} {f0/1e6:g} MHz: V_pk {vpk:.2f} V ({lim}) DR Eq.56 (|Z_T| {zt:.0f}) " + "/".join(
                f"{ct.dr_db(vpk / (np.sqrt(2) * zt), n_sp, i):.1f}" for i in (0.0, 1e-4, 1e-3, 1e-2)) + " | at |Z_T| = R_F "
                + "/".join(f"{ct.dr_db(vpk / (np.sqrt(2) * ct.R_F), n_sp, i):.1f}" for i in (0.0, 1e-4, 1e-3, 1e-2)))

    print("== tone sweeps (SPICE)")
    for lab, v in tone.items():
        for f0, x in v.items():
            r1 = next(s for s in x["sweep"] if abs(s["frac"] - 1.0) < 1e-9)
            print(f"  {lab} {f0}: ceiling {x['claim_V']:.2f} V ({x['limit']}); THD -60 dBc at {fmt(x['frac_at_thd_m60'], 2)} x = "
                  f"{fmt(x['frac_at_thd_m60'] and x['frac_at_thd_m60'] * x['claim_V'], 2)} V, -40 dBc at {fmt(x['frac_at_thd_m40'], 2)} x; "
                  f"at 1.0 x OPA859 +{r1['oa']['v_pos']:.2f}/-{r1['oa']['v_neg']:.2f} V")

    print("== a first stage with 0.40 nV/rtHz instead of OPA859's 3.03 nV/rtHz inside the G2 = 5.5 design: its part "
          "scaled by the ratio, the THS3491's part and R_F unchanged")
    v55 = hvv["macromodels, G2 = 5.5"]
    cmp55 = ct.HVComposite("macromodels", 5.5)
    parts = ct.hv_design(cmp55, 0.10e-12, 3.25e-12, with_corners=False)["noise_parts_nA"]
    first_new = parts["first"] * 0.40 / 3.03
    n_old = v55["spice_nominal"]["noise_nA"]
    n_new = float(np.sqrt(first_new ** 2 + parts["second"] ** 2 + parts["rf"] ** 2))
    print(f"  first-stage part {parts['first']:.1f} -> {first_new:.1f} nA; total {n_old:.1f} -> {n_new:.1f} nA; gain at 0/0.1/1/10 mA "
          + "/".join(f"{10*np.log10(((n_old*1e-9)**2 + 2*ct.Q_E*i*ct.B) / ((n_new*1e-9)**2 + 2*ct.Q_E*i*ct.B)):.2f}"
                     for i in (0.0, 1e-4, 1e-3, 1e-2)) + " dB")
    print("== distortion at 100 MHz: THS3491 datasheet (G = 5, 100 ohm) and the composite's loop at 2f and 3f")
    for g2, cf, cl, vpk in ((5.0, 0.10e-12, 3.0e-12, 7.55), (5.5, 0.10e-12, 3.25e-12, 8.30)):
        cmp = ct.HVComposite("macromodels", g2)
        T, Z, n1, n2 = cmp.solve(cf, cl)
        S = n2 * Z / cmp.H
        lf = np.log10(cmp.f)
        s_db = {x: float(20 * np.log10(np.interp(np.log10(x), lf, np.abs(S)))) for x in (100e6, 200e6, 300e6)}
        vpp = 2 * vpk
        hd2 = float(np.interp(vpp, ct.HD_VPP, ct.HD2_100M["rl100"]))
        hd3 = float(np.interp(vpp, ct.HD_VPP, ct.HD3_100M["rl100"]))
        print(f"  G2={g2}: |S| 100/200/300 MHz {s_db[100e6]:.1f}/{s_db[200e6]:.1f}/{s_db[300e6]:.1f} dB | at {vpp:.1f} Vpp THS3491 "
              f"HD2 {hd2:.1f} HD3 {hd3:.1f} dBc -> composite HD2 {hd2 + s_db[200e6]:.1f} HD3 {hd3 + s_db[300e6]:.1f}")
        for lim in (-50.0, -55.0, -60.0):
            need3 = lim - s_db[300e6]
            need2 = lim - s_db[200e6]
            vg = np.linspace(1.0, 24.0, 2301)
            ok = (np.interp(vg, ct.HD_VPP, ct.HD3_100M["rl100"]) <= need3) & (np.interp(vg, ct.HD_VPP, ct.HD2_100M["rl100"]) <= need2)
            first_bad = vg[np.argmax(~ok)] if (~ok).any() else vg[-1]
            vpk_lim = min(first_bad / 2, vpk)
            n_sp = hvv[f"macromodels, G2 = {g2:g}"]["spice_nominal"]["noise_nA"] * 1e-9
            zt = cmp.ceiling(100e6, cf, cl)[2]
            h2v = float(np.interp(first_bad, ct.HD_VPP, ct.HD2_100M["rl100"]))
            h3v = float(np.interp(first_bad, ct.HD_VPP, ct.HD3_100M["rl100"]))
            print(f"     at {first_bad:.2f} Vpp: THS3491 HD2 {h2v:.1f} HD3 {h3v:.1f} dBc, composite {h2v + s_db[200e6]:.1f} / "
                  f"{h3v + s_db[300e6]:.1f} dBc")
            print(f"     HD2 and HD3 <= {lim:.0f} dBc up to {first_bad:.2f} Vpp -> V_pk {vpk_lim:.2f} V, DR Eq.56 (|Z_T| {zt:.0f}) "
                  + "/".join(f"{ct.dr_db(vpk_lim / (np.sqrt(2) * zt), n_sp, i):.1f}" for i in (0.0, 1e-4, 1e-3, 1e-2))
                  + " | at |Z_T| = R_F "
                  + "/".join(f"{ct.dr_db(vpk_lim / (np.sqrt(2) * ct.R_F), n_sp, i):.1f}" for i in (0.0, 1e-4, 1e-3, 1e-2)))

    print("== discrete-FET composite: devices at the composite's operating point (ngspice)")
    for dev, v in fdev.items():
        op = v["op"]
        print(f"  {dev}: V_G {op['v(g)']:.3f} V, V_DS1 {op['v(x)']:.3f} V, V_d {op['v(d)']:.3f} V, I_D {-op['i(vdd)']*1e3:.2f} mA, "
              f"R_D {ct.FET_DESIGN[dev]['r_d']:g} | Q1 at 1 MHz {v['y_J1_1MHz']} | Q2 {v['y_J2_1MHz']} | e_n {v['e_n_nV']} | buffer {v['buffer_100MHz']}")
    print("== FET composite, analytical against SPICE (nominal)")
    for dev in ("CE3512K2", "CPH3910", "LSBF862"):
        ks = [k for k in fcmp if k.startswith(dev)]
        st = [fcmp[k] for k in ks if fcmp[k]["spice"]["pm_deg"] is not None and fcmp[k]["spice"]["pm_deg"] > 0]
        dpm = max(abs(r["spice"]["pm_deg"] - r["analytical"]["pm_deg"]) for r in st)
        dn = max(abs(fcmp[k]["spice"]["noise_nA"] - fcmp[k]["analytical"]["noise_nA"]) for k in ks)
        df3 = max(abs(fcmp[k]["spice"]["f3_MHz"] - fcmp[k]["analytical"]["f3_MHz"]) for k in ks)
        print(f"  {dev}: {len(ks)} designs, of them {len(st)} with positive PM: largest |dPM| {dpm:.2f} deg, |df3| {df3:.1f} MHz, |dnoise| {dn:.2f} nA")
    print("== FET composite, verified designs")
    for dev, v in fver.items():
        sw, aw = v["spice_worst"], v["analytical_worst"]
        cmp = ct.FETComposite(dev)
        cn, cf = v["c_n_pF"] * 1e-12, v["c_f_pF"] * 1e-12
        d = ct.fet_design(cmp, cn, cf, with_corners=False)
        n_sp = v["spice_nominal"]["noise_nA"] * 1e-9
        vpk, lim, zt = cmp.ceiling(100e6, cn, cf)
        dr_eq = "/".join(f"{ct.dr_db(vpk / (np.sqrt(2) * zt), n_sp, i):.1f}" for i in (0.0, 1e-4, 1e-3, 1e-2))
        print(f"  {dev}: DR Eq.56 at 100 MHz (|Z_T| {zt:.0f}): {dr_eq}; g_m/C11 at 1 MHz "
              f"{fdev[dev]['y_J1_1MHz']['gm_mS'] / fdev[dev]['y_J1_1MHz']['c11_pF']:.1f} mS/pF "
              f"(f_T {fdev[dev]['y_J1_1MHz']['gm_mS'] / fdev[dev]['y_J1_1MHz']['c11_pF'] / (2 * np.pi):.2f} GHz)")
        print(f"  {dev}: C_N {v['c_n_pF']:.1f} C_F {v['c_f_pF']:.2f} | SPICE worst PM {fmt(sw['pm_deg'])} GM {fmt(sw['gm_dB'])} pk "
              f"{sw['peak_dB']:.2f} f3 {fmt(sw['f3_MHz'], 0)} | analytical {fmt(aw['pm_deg'])} {fmt(aw['gm_dB'])} {aw['peak_dB']:.2f} "
              f"{fmt(aw['f3_MHz'], 0)} | nominal f3 {fmt(v['spice_nominal']['f3_MHz'], 0)} |Z_T(0)| {v['spice_nominal']['z_lf_ohm']:.0f} "
              f"|Z_T(100 MHz)| {zt:.0f} | noise SPICE {v['spice_nominal']['noise_nA']:.1f} analytical {v['analytical_noise_nA']:.1f} parts "
              + str({k: round(x, 1) for k, x in d['noise_parts_nA'].items()})
              + " | DR at |Z_T| = R_F, 1.5 V: " + "/".join(f"{ct.dr_db(vpk / (np.sqrt(2) * ct.R_F), n_sp, i):.1f}" for i in (0.0, 1e-4, 1e-3, 1e-2)))
    # the output's DC offset: the gate sits at V_GS when the source is grounded
    s = ct.PARTS["OPA859"]["dr"]["swing_light"]
    lo, hi = s[0] - 2.5, s[1] - 2.5
    for dev, v in fdev.items():
        vdc = v["op"]["v(oa)"]
        amp = min(hi - vdc, vdc - lo)
        print(f"  {dev}: output DC {vdc:.3f} V in the OPA859's {lo:.2f}..{hi:.2f} V: largest symmetric amplitude {amp:.2f} V "
              f"({20*np.log10(amp/1.5):+.1f} dB against 1.5 V)")


if __name__ == "__main__":
    main()
