"""Balanced-detector variants of the survey numbers, and the noise budgets of the
front-end options of Sections 7.8-7.11 (bootstrap, cascode, servos, bias network).

Usage: python balanced_detector.py <out_json>             (items 1-12)
       python balanced_detector.py <out_json> variants    (item 12 only, merged into <out_json>)

 1. Node capacitance of a balanced pair: C_D = C_D,A + C_D,B.  The 2-pF option
    (1 pF per photodiode): flat and robust designs and noise for the ten leading
    amplifiers at R_F = 1.5 and 2 kOhm.
 2. Shot noise of a balanced pair: 2q(I_1 + I_2) for per-diode currents.
 3. Common-base (cascode) stage per photodiode, self-biased by its photocurrent:
    emitter resistance, emitter pole and added noise (base shot noise plus the
    transistor's voltage noise on C_D).
 4. Cascode with a standing bias current for dark operation: what the standing
    current and the transistor add, against what removing C_D saves.
 5. Summing node with cascodes (both C_D removed, 2 C_mu added): C_F window of
    OPA855 and OPA856.
 6. Bootstrapped photodiodes: the e_n*w*C_D term removed against the follower's
    own noise, and the break-even photodiode capacitance.
 7. Resistive DC-imbalance servo: injection-resistor noise for a given range,
    and the servo loop (high-pass corner, integrator time constant, filter pole).
 8. Current-splitting servo (differential pair on one photodiode): delivered
    noise, emitter pole and the common-mode rejection left by the path delay.
 9. Photodiode bias network: noise current coupled through C_D from the bias
    regulator and the current-monitor resistor, with capacitor parasitics.
10. Largest RF amplitude against tone frequency (Eq. (24), light load) and the
    shot-limited dynamic range at I_1 + I_2 = 20 mA (Eq. (26)).
11. The proposed balanced front end: OPA855 at the 1-pF baseline and the 2-pF
    option, loop metrics and noise with the imbalance servo resistor included.
12. The two front-end variants of Section 7.11, OPA855 and OPA818: nominal loop,
    worst case over the corners of peaking_tolerance.py, noise with the servo
    resistor (central and high estimates), band penalty, and the dynamic range
    in 150 MHz for a 100-MHz tone.
"""
import json
import sys

import numpy as np

import tia_model as tm
from cf_window import window
from parts_db import PARTS
from run_analysis import (C_PCB_NOM, C_FPAR_NOM, F_NOISE, design_block, noise_inputs,
                          noise_models_for, open_loop_model, robust_design)

KT = tm.K_B * tm.T_ROOM
Q = tm.Q_E
VT = KT / Q
LEADING = ["OPA855", "OPA858", "OPA955", "LMH6629 (COMP HI)", "OPA856", "OPA859", "THS4304",
           "OPA843", "OPA846", "OPA818"]
# small RF bipolar transistor used for cascode, follower and splitter stages (assumed values)
BETA, R_B, C_MU, C_JE, F_T = 100.0, 10.0, 0.2e-12, 0.3e-12, 10e9


def node_2pF(out):
    print("1. Balanced pair with 1 pF per photodiode (C_D = 2 pF at the node)")
    for R_F in (2000.0, 1500.0):
        for name in LEADING:
            p = PARTS[name]
            ol, *_ = open_loop_model(p)
            nz = noise_inputs(p)
            C_T = 2e-12 + C_PCB_NOM + p["c_cm"] + p["c_diff"]
            d = design_block(ol, R_F, C_T, C_FPAR_NOM, p["g_min"])
            rb = robust_design(ol, R_F, C_T, C_FPAR_NOM)
            flat = d["flat"]
            cf = (flat.get("C_F_real_pF") or 0.2) * 1e-12
            fm = "central"
            c = tm.noise_components(np.array([100e6, 200e6]), R_F, C_T, cf, nz, fet_model=fm)
            S_ref = np.full_like(F_NOISE, 4 * KT / R_F)
            cN = tm.noise_components(F_NOISE, R_F, C_T, cf, nz, fet_model=fm)
            pen = tm.band_average_penalty_db(F_NOISE, cN["total"], S_ref, 10e6, 150e6)
            hi = None
            if "high" in noise_models_for(p):
                ch = tm.noise_components(np.array([100e6, 200e6]), R_F, C_T, cf, nz, fet_model="high")
                hi = list(np.sqrt(ch["total"]) * 1e12)
            row = dict(C_T_pF=C_T * 1e12,
                       flat=dict(C_F_pF=flat.get("C_F_real_pF"), f3_MHz=flat.get("f3_MHz"), pm=flat.get("pm_deg")),
                       robust=None if rb is None else dict(C_add_pF=rb["C_add_pF"], C_F_pF=rb["C_F_real_pF"],
                                                           f3_MHz=rb["f3_MHz"], pm=rb["pm_deg"]),
                       noise_100_200_pA=list(np.sqrt(c["total"]) * 1e12), noise_high_pA=hi, penalty_dB=pen)
            out[f"2pF|{name}|{R_F:.0f}"] = row
            fl = row["flat"]
            fl_s = (f"flat {fl['f3_MHz']:.0f} MHz, {fl['pm']:.0f} deg" if fl["f3_MHz"] else "no flat design")
            rb_s = ("robust: none" if rb is None else
                    f"robust +{rb['C_add_pF']:.2g} pF -> {rb['f3_MHz']:.0f} MHz")
            n = row["noise_100_200_pA"]
            hs = f" (high {hi[0]:.2f} / {hi[1]:.2f})" if hi else ""
            print(f"  {R_F/1e3:g}k {name:18s} C_T {C_T*1e12:5.2f} pF | {fl_s} | {rb_s} | noise {n[0]:.2f} / {n[1]:.2f} pA{hs} | "
                  f"penalty {pen:.1f} dB")


def shot(out):
    print("\n2. Shot noise of a balanced pair, 2q(I_1 + I_2), I_1 = I_2 = I per diode")
    for I in (0.05e-3, 0.1e-3, 0.5e-3, 1e-3, 5e-3, 10e-3):
        s = np.sqrt(2 * Q * 2 * I)
        out[f"shot|{I*1e3:g}"] = s
        print(f"  I = {I*1e3:5.2f} mA per diode: total {2*I*1e3:5.1f} mA, shot {s*1e12:6.2f} pA/rtHz, "
              f"{20*np.log10(s/np.sqrt(4*KT/2000)):5.2f} dB above 2 kOhm, {20*np.log10(s/np.sqrt(4*KT/1500)):5.2f} dB above 1.5 kOhm")


def cascode(out, C_D=1e-12):
    print(f"\n3. Common-base stage per photodiode, self-biased by its photocurrent "
          f"(beta {BETA:g}, r_b {R_B:g} ohm, C_D {C_D*1e12:g} pF per diode, C_je {C_JE*1e12:g} pF, f_T {F_T/1e9:g} GHz)")
    for I in (0.1e-3, 1e-3, 10e-3):
        r_e = VT / I
        f_e = 1 / (2 * np.pi * (r_e * (C_D + C_JE) + 1 / (2 * np.pi * F_T)))
        e_cb = np.sqrt(4 * KT * (R_B + r_e / 2))
        S_base = 2 * Q * I / BETA
        res = {}
        for f in (100e6, 200e6):
            S_en = (e_cb * 2 * np.pi * f * (C_D + C_JE)) ** 2     # e_cb acts on all emitter-node capacitance
            S_shot_pair = 2 * Q * 2 * I
            add_db = 10 * np.log10(1 + 2 * (S_base + S_en) / S_shot_pair)   # two transistors
            res[f"{f/1e6:.0f}MHz"] = dict(base_pA=np.sqrt(S_base) * 1e12, en_term_pA=np.sqrt(S_en) * 1e12,
                                          added_dB_vs_pair_shot=add_db)
        out[f"cascode|{I*1e3:g}"] = dict(r_e=r_e, f_e_MHz=f_e / 1e6, e_cb_nV=e_cb * 1e9, **res)
        print(f"  I = {I*1e3:5.1f} mA: r_e {r_e:6.1f} ohm, emitter pole {f_e/1e6:7.0f} MHz, e_n(CB) {e_cb*1e9:.2f} nV/rtHz, "
              f"base shot {np.sqrt(S_base)*1e12:.2f} pA/rtHz, e_n*w*C_D {res['100MHz']['en_term_pA']:.2f} / "
              f"{res['200MHz']['en_term_pA']:.2f} pA/rtHz at 100 / 200 MHz; both transistors add "
              f"{res['100MHz']['added_dB_vs_pair_shot']:.2f} / {res['200MHz']['added_dB_vs_pair_shot']:.2f} dB to the pair's shot noise")


def cascode_dark(out):
    print("\n4. Cascode pair with a standing current I_q per transistor (from V_q through R_q), dark, 200 MHz")
    en_855 = PARTS["OPA855"]["en"]
    w = 2 * np.pi * 200e6
    for C_D_each in (0.5e-12, 1e-12):
        removed = en_855 * w * (2 * C_D_each - 2 * C_MU)       # node capacitance removed net of 2 C_mu
        for I_q, V_q in ((0.2e-3, 12.0), (1e-3, 12.0)):
            r_e = VT / I_q
            f_e = 1 / (2 * np.pi * (r_e * (C_D_each + C_JE) + 1 / (2 * np.pi * F_T)))
            e_cb = np.sqrt(4 * KT * (R_B + r_e / 2))
            S_add_each = 4 * KT * I_q / V_q + 2 * Q * I_q / BETA + (e_cb * w * (C_D_each + C_JE)) ** 2
            added = np.sqrt(2 * S_add_each)
            out[f"cascode_dark|{C_D_each*1e12:g}|{I_q*1e3:g}"] = dict(
                f_e_MHz=f_e / 1e6, e_cb_nV=e_cb * 1e9, added_pA=added * 1e12, removed_pA=removed * 1e12,
                R_q_kohm=V_q / I_q / 1e3)
            print(f"  C_D {C_D_each*1e12:g} pF each, I_q {I_q*1e3:g} mA from {V_q:g} V (R_q {V_q/I_q/1e3:g} kohm): "
                  f"emitter pole {f_e/1e6:.0f} MHz, e_n(CB) {e_cb*1e9:.2f} nV/rtHz; pair adds {added*1e12:.2f} pA/rtHz "
                  f"[R_q {np.sqrt(4*KT*I_q/V_q)*1e12:.2f}, base {np.sqrt(2*Q*I_q/BETA)*1e12:.2f}, "
                  f"e_cb*w*(C_D + C_je) {e_cb*w*(C_D_each + C_JE)*1e12:.2f} each]; OPA855 e_n*w*C removed {removed*1e12:.2f} pA/rtHz")
    print(f"  equivalent noise resistance of OPA855 e_n: {en_855**2/(4*KT):.1f} ohm; a CB stage beats it when "
          f"r_b + r_e/2 is smaller, i.e. I > {VT/(2*(en_855**2/(4*KT) - R_B))*1e3:.2f} mA")


def cascode_node(out):
    print(f"\n5. Summing node with a cascode on each photodiode: C_T = 2 C_mu ({2*C_MU*1e12:g} pF) + C_PCB + C_CM + C_DIFF")
    for name in ("OPA855", "OPA856"):
        p = PARTS[name]
        ol, *_ = open_loop_model(p)
        C_T = 2 * C_MU + C_PCB_NOM + p["c_cm"] + p["c_diff"]
        for R_F in (2000.0, 1500.0):
            wdw = window(ol, R_F, C_T)
            cap = C_T / (p["g_min"] - 1) if p["g_min"] > 1 else np.inf
            rows = {}
            for cf in (0.15e-12, 0.2e-12, 0.25e-12, 0.3e-12, 0.4e-12, 0.5e-12):
                m = tm.loop_metrics(ol, R_F, C_T, cf)
                rows[f"{cf*1e12:.2f}"] = dict(f3_MHz=m["f_3dB"] / 1e6, pm=m["pm_deg"], pk=max(m["peaking_dB"], 0.0),
                                              gm=m["gm_dB"], stable=bool(m["stable"]))
            out[f"cascode_node|{name}|{R_F:.0f}"] = dict(C_T_pF=C_T * 1e12, window=wdw, gmin_cap_pF=cap * 1e12, scan=rows)
            ws = ("none" if wdw is None else
                  f"{wdw['cf_min_pF']:.3f}-{min(wdw['cf_max_pF'], cap*1e12):.3f} pF")
            print(f"  {name} {R_F/1e3:g}k: C_T {C_T*1e12:.2f} pF, window {ws} (G_min cap {cap*1e12:.3f} pF)")
            for k, v in rows.items():
                print(f"     C_F {k}: f3 {v['f3_MHz']:.0f} MHz, PM {v['pm']:.0f}, pk {v['pk']:.1f} dB, GM {v['gm']:.1f}, "
                      f"stable {v['stable']}")


def bootstrap(out):
    print("\n6. Bootstrapped photodiodes: removed e_n*w*C_D against the follower's noise")
    I_C = 1e-3
    r_e = VT / I_C
    e_b = np.sqrt(4 * KT * (R_B + r_e / 2))
    S_ib = 2 * Q * I_C / BETA
    C_in_b = C_MU + 0.1e-12        # follower input capacitance left after bootstrapping its own C_pi (assumed)
    for name in ("OPA855", "OPA818"):
        e_n = PARTS[name]["en"]
        for f in (100e6, 200e6):
            w = 2 * np.pi * f
            for C_D in (1e-12, 2e-12):
                removed = e_n * w * C_D
                print(f"  {name}: e_n*w*C_D removed at {f/1e6:.0f} MHz, C_D {C_D*1e12:g} pF = {removed*1e12:.2f} pA/rtHz")
            if e_n > e_b:
                c_be = np.sqrt(S_ib + (e_n * w * C_in_b) ** 2) / (w * np.sqrt(e_n ** 2 - e_b ** 2))
                out[f"bootstrap|breakeven|{name}|{f/1e6:.0f}"] = c_be
                print(f"  {name}: break-even C_D at {f/1e6:.0f} MHz with a BJT follower at {I_C*1e3:g} mA: {c_be*1e12:.1f} pF")
    print(f"  BJT follower I_C {I_C*1e3:g} mA: base shot {np.sqrt(S_ib)*1e12:.2f} pA/rtHz (white), e_b {e_b*1e9:.2f} nV/rtHz")
    out["bootstrap|bjt|1"] = dict(e_b_nV=e_b * 1e9, base_shot_pA=np.sqrt(S_ib) * 1e12)


def servo(out):
    print("\n7. Resistive DC-imbalance servo: R_s = V_S / dI_max")
    for dI in (0.1e-3, 0.5e-3, 1e-3):
        for V_S in (5.0, 12.0):
            R_s = V_S / dI
            i_s = np.sqrt(4 * KT / R_s)
            row = dict(R_s=R_s, i_noise_pA=i_s * 1e12)
            for I_tot in (0.2e-3, 2e-3, 20e-3):
                shot_tot = 2 * Q * I_tot
                row[f"added_dB_at_{I_tot*1e3:g}mA_total"] = 10 * np.log10(1 + i_s ** 2 / (shot_tot + 4 * KT / 2000))
            out[f"servo|{dI*1e3:g}|{V_S:g}"] = row
            print(f"  dI_max {dI*1e3:.1f} mA, V_S {V_S:4.1f} V: R_s {R_s/1e3:6.1f} kohm, {i_s*1e12:.2f} pA/rtHz; adds "
                  f"{row['added_dB_at_0.2mA_total']:.2f} / {row['added_dB_at_2mA_total']:.2f} / {row['added_dB_at_20mA_total']:.3f} dB "
                  f"at 0.2 / 2 / 20 mA total photocurrent (with the 2-kohm R_F noise)")
    # the servo loop: integrator tau, high-pass corner R_F/(2 pi tau R_s), injection filter pole
    R_F, R_s, f_hp = 2000.0, 24e3, 1e3
    tau = R_F / (2 * np.pi * f_hp * R_s)
    R_flt, C_flt = 3.3e3, 10e-9
    f_flt = 1 / (2 * np.pi * R_flt * C_flt)
    pm = 90 - np.degrees(np.arctan(f_hp / f_flt))
    e_srv = 20e-9
    leak = [e_srv / abs(1 + 1j * 2 * np.pi * f * R_flt * C_flt) / R_s for f in (1e4, 1e6, 10e6)]
    out["servo_loop"] = dict(tau_us=tau * 1e6, f_filter_kHz=f_flt / 1e3, pm_deg=pm,
                             servo_amp_noise_through_filter_pA=[x * 1e12 for x in leak])
    print(f"  loop: f_HP {f_hp:g} Hz needs tau = {tau*1e6:.1f} us; injection filter {R_flt/1e3:g} kohm + {C_flt*1e9:g} nF "
          f"-> pole {f_flt/1e3:.1f} kHz, phase margin {pm:.0f} deg; a 20-nV/rtHz servo amplifier reaches the node as "
          + ", ".join(f"{x*1e12:.3g} pA/rtHz" for x in leak) + " at 10 kHz, 1 MHz, 10 MHz")
    for i_tol in (0.5e-12, 1e-12):
        print(f"  bias-node noise for <= {i_tol*1e12:.1f} pA/rtHz through 1 pF at 200 MHz: "
              f"e_B <= {i_tol/(2*np.pi*200e6*1e-12)*1e9:.2f} nV/rtHz")


def splitter(out):
    print("\n8. Current-splitting servo: differential pair carrying one photodiode's current I_2")
    # delivered noise: 2q f I_2 (derived in the report); emitter node r_e = V_T / I_2
    for I2, C_D in ((1e-3, 0.5e-12), (1e-3, 1e-12), (10e-3, 0.5e-12), (10e-3, 1e-12)):
        r_e = VT / I2
        tau = r_e * (C_D + 2 * C_JE) + 1 / (2 * np.pi * F_T)
        f_p = 1 / (2 * np.pi * tau)
        cmrr = {f: 20 * np.log10(abs(1 - 1 / (1 + 1j * 2 * np.pi * f * tau))) for f in (10e6, 100e6, 200e6)}
        out[f"splitter|{I2*1e3:g}|{C_D*1e12:g}"] = dict(r_e=r_e, tau_ps=tau * 1e12, f_pole_MHz=f_p / 1e6,
                                                        cmrr_dB={f"{k/1e6:.0f}MHz": v for k, v in cmrr.items()})
        print(f"  I_2 {I2*1e3:g} mA, C_D,B {C_D*1e12:g} pF: r_e {r_e:.2f} ohm, path delay {tau*1e12:.0f} ps "
              f"(pole {f_p/1e6:.0f} MHz); common-mode rejection left by the unmatched path "
              + ", ".join(f"{v:.0f} dB at {k/1e6:.0f} MHz" for k, v in cmrr.items()))
    # base-spreading-resistance noise of the pair modulates the split: dI_C2 = I_sp f (1 - f) / V_T * e_delta
    print("  base-resistance noise of the splitting pair, e_delta^2 = 4kT (r_b1 + r_b2):")
    for I_sp, f_dl, I_other in ((10e-3, 0.9, 9e-3), (10e-3, 0.8, 8e-3), (1e-3, 0.9, 0.9e-3), (0.5e-3, 0.5, 20e-3)):
        for r_b in (10.0, 50.0):
            g = I_sp * f_dl * (1 - f_dl) / VT
            i_rb = g * np.sqrt(4 * KT * 2 * r_b)
            S_node_shot = 2 * Q * (I_other + f_dl * I_sp)
            add = 10 * np.log10(1 + i_rb ** 2 / S_node_shot)
            out[f"splitter_rb|{I_sp*1e3:g}|{f_dl:g}|{r_b:g}"] = dict(g_mS=g * 1e3, i_rb_pA=i_rb * 1e12, added_dB=add)
            print(f"    I_split {I_sp*1e3:g} mA, delivered fraction {f_dl:g}, r_b' {r_b:g} ohm each: g {g*1e3:.1f} mS, "
                  f"{i_rb*1e12:.1f} pA/rtHz, adds {add:.2f} dB to the node shot noise "
                  f"({np.sqrt(S_node_shot)*1e12:.1f} pA/rtHz for {(I_other + f_dl*I_sp)*1e3:.2f} mA at the node)")
    print("  residual laser RIN of an imbalance nulled electrically: |I_1 - I_2| * 10^(RIN/20)")
    for dI in (0.1e-3, 1e-3):
        for rin in (-150.0, -160.0):
            v = dI * 10 ** (rin / 20)
            out[f"rin_res|{dI*1e3:g}|{rin:g}"] = v
            print(f"    dI {dI*1e3:g} mA, RIN {rin:g} dB/Hz: {v*1e12:.2f} pA/rtHz "
                  f"(single-ended 10 mA: {10e-3*10**(rin/20)*1e12:.0f} pA/rtHz)")


def _zc(f, C, L, R):
    w = 2 * np.pi * f
    return R + 1j * w * L + 1 / (1j * w * C)


def _bead(f, L=1e-6, R_p=600.0, R_dc=0.2):
    """Generic ferrite bead: R_dc in series with L parallel R_p (about 430 ohm at 100 MHz)."""
    jwl = 1j * 2 * np.pi * f * L
    return R_dc + jwl * R_p / (R_p + jwl)


def bias_network(out):
    print("\n9. Photodiode bias network: regulator noise e_reg (100 nV/rtHz, flat), series element, bypass at the pin")
    bank = [(1e-9, 0.25e-9, 0.10), (100e-9, 0.5e-9, 0.03), (10e-6, 1.0e-9, 0.01)]   # C, ESL, ESR (assumed)
    single = [(10e-9, 0.4e-9, 0.05)]
    configs = {"10 ohm, 1 nF + 100 nF + 10 uF": (lambda f: 10.0, bank),
               "100 ohm, 1 nF + 100 nF + 10 uF": (lambda f: 100.0, bank),
               "100 ohm, 10 nF": (lambda f: 100.0, single),
               "bead + 100 ohm, 10 nF": (lambda f: 100.0 + _bead(f), single)}
    e_reg = 100e-9
    for name, (z_series, caps) in configs.items():
        rows = {}
        for f in (1e6, 10e6, 50e6, 100e6, 200e6, 300e6):
            Zs = z_series(f)
            Zb = 1 / sum(1 / _zc(f, *c) for c in caps)
            h = abs(Zb / (Zs + Zb))
            e_B = np.sqrt(e_reg ** 2 + 4 * KT * np.real(Zs)) * h
            i_inj = 2 * np.pi * f * 1e-12 * e_B
            rows[f"{f/1e6:g}MHz"] = dict(Zb_ohm=abs(Zb), e_B_nV=e_B * 1e9, i_pA_per_pF=i_inj * 1e12)
        out[f"bias|{name}"] = rows
        print(f"  {name}: " + "; ".join(
            f"{k}: |Z_b| {v['Zb_ohm']:.3f} ohm, e_B {v['e_B_nV']:.3f} nV, i {v['i_pA_per_pF']:.3f} pA/rtHz per pF"
            for k, v in rows.items()))


def amplitude_vs_frequency(out):
    print("\n10. Largest RF amplitude against tone frequency (light load, flat design at 2 kOhm, 1-pF baseline) "
          "and shot-limited DR in 150 MHz at I_1 + I_2 = 20 mA (Eq. 26)")
    for name in ("OPA855", "OPA955", "LMH6629 (COMP HI)", "OPA856", "OPA843", "OPA846", "OPA818"):
        p = PARTS[name]
        ol, *_ = open_loop_model(p)
        s = p["dr"]
        for R_F in (2000.0, 1500.0):
            C_T = 1e-12 + C_PCB_NOM + p["c_cm"] + p["c_diff"]
            d = design_block(ol, R_F, C_T, C_FPAR_NOM, p["g_min"])
            cf = (d["flat"].get("C_F_real_pF") or 0.2) * 1e-12
            vol, voh = s["swing_light"]
            i_out = s.get("iout_ma", np.inf) * 1e-3
            row = {}
            for f0 in (20e6, 50e6, 100e6, 150e6, 200e6):
                v_sw = (voh - vol) / 2
                v_sl = s["sr"] * 1e6 / (2 * np.pi * f0)
                v_cur = i_out / (1 / R_F + 2 * np.pi * f0 * cf)
                v_pk = min(v_sw, v_sl, v_cur)
                lim = ["swing", "slew", "current"][int(np.argmin([v_sw, v_sl, v_cur]))]
                dr = 91.9 + 20 * np.log10(v_pk / (R_F / 1e3 * np.sqrt(20 * 150)))
                row[f"{f0/1e6:.0f}MHz"] = dict(v_pk=v_pk, limit=lim, DR_20mA_dB=dr)
            out[f"vpk|{name}|{R_F:.0f}"] = row
            print(f"  {name:18s} {R_F/1e3:g}k: " + "; ".join(
                f"{k} {v['v_pk']:.2f} V ({v['limit']}), DR {v['DR_20mA_dB']:.1f} dB" for k, v in row.items()))


def proposed_design(out):
    print("\n11. Proposed front end: OPA855, imbalance servo 24 kohm, noise at 100 / 200 MHz")
    p = PARTS["OPA855"]
    ol, *_ = open_loop_model(p)
    nz = noise_inputs(p)
    S_srv = 4 * KT / 24e3
    for C_D, R_F, cfs in ((1e-12, 2000.0, (0.15, 0.25, 0.35)), (2e-12, 2000.0, (0.25, 0.35, 0.45)),
                          (1e-12, 1500.0, (0.17, 0.27, 0.37)), (2e-12, 1500.0, (0.30, 0.40, 0.50))):
        C_T = C_D + C_PCB_NOM + p["c_cm"] + p["c_diff"]
        for cf_pF in cfs:
            cf = cf_pF * 1e-12
            m = tm.loop_metrics(ol, R_F, C_T, cf)
            tot = {}
            for I_tot in (0.0, 0.2e-3, 2e-3, 20e-3):
                c = tm.noise_components(np.array([100e6, 200e6]), R_F, C_T, cf, nz, i_dc=I_tot, fet_model="central")
                tot[f"{I_tot*1e3:g}mA"] = list(np.sqrt(c["total"] + S_srv) * 1e12)
            cN = tm.noise_components(F_NOISE, R_F, C_T, cf, nz, fet_model="central")
            pen = tm.band_average_penalty_db(F_NOISE, cN["total"] + S_srv, np.full_like(F_NOISE, 4 * KT / R_F),
                                             10e6, 150e6)
            key = f"proposed|{C_D*1e12:g}pF|{R_F:.0f}|{cf_pF:.2f}"
            out[key] = dict(C_T_pF=C_T * 1e12, f3_MHz=m["f_3dB"] / 1e6, pm=m["pm_deg"], pk=max(m["peaking_dB"], 0.0),
                            gm=m["gm_dB"], noise_with_servo_pA=tot, penalty_with_servo_dB=pen)
            print(f"  C_D {C_D*1e12:g} pF, R_F {R_F/1e3:g}k, C_F {cf_pF:.2f} pF: f3 {m['f_3dB']/1e6:.0f} MHz, "
                  f"PM {m['pm_deg']:.0f}, pk {max(m['peaking_dB'], 0):.1f} dB | noise " +
                  " | ".join(f"{k}: {v[0]:.2f}/{v[1]:.2f}" for k, v in tot.items()) + f" | penalty {pen:.2f} dB")


def front_end_variants(out):
    """The two front-end variants of Section 7.11, OPA855 and OPA818, at 1 and 2 pF and both R_F:
    nominal loop, worst case over the corners of Section 4.9 (C_F +/- 0.1 pF, C_T +/- 0.2 pF,
    open-loop gain at GBW MIN or -2 dB, and +1.5 dB), noise with the 24-kohm servo resistor
    (central and, for OPA818, high estimate), band penalty, and the dynamic range in 150 MHz for a
    100-MHz tone (Eq. (25), light load, imbalance at zero)."""
    import itertools
    from peaking_tolerance import GAIN_LO_DB, Scaled
    print("\n12. Front-end variants: nominal and worst-case loop, noise with the servo resistor, dynamic range")
    S_srv = 4 * KT / 24e3
    f_band = np.linspace(1e4, 150e6, 30001)
    designs = {"OPA855": [(1e-12, 2000.0, (0.25,)), (2e-12, 2000.0, (0.35,)),
                          (1e-12, 1500.0, (0.27,)), (2e-12, 1500.0, (0.40,))],
               "OPA818": [(1e-12, 2000.0, (0.45, 0.50, 0.55, 0.60)), (2e-12, 2000.0, (0.45, 0.55, 0.65, 0.75)),
                          (1e-12, 1500.0, (0.45, 0.50, 0.55, 0.60)), (2e-12, 1500.0, (0.55, 0.65, 0.75))]}
    for name, rows in designs.items():
        p = PARTS[name]
        ol, *_ = open_loop_model(p)
        nz = noise_inputs(p)
        models = {"nominal": ol, "gain low": Scaled(ol, GAIN_LO_DB.get(name, -2.0)), "gain high": Scaled(ol, +1.5)}
        fms = ["central"] + (["high"] if "high" in noise_models_for(p) else [])
        s = p["dr"]
        vol, voh = s["swing_light"]
        v_pk = min((voh - vol) / 2, s["sr"] * 1e6 / (2 * np.pi * 100e6))
        for C_D, R_F, cfs in rows:
            C_T = C_D + C_PCB_NOM + p["c_cm"] + p["c_diff"]
            for cf_pF in cfs:
                cf = cf_pF * 1e-12
                nom = tm.loop_metrics(ol, R_F, C_T, cf)
                worst_pm, worst_gm, ok, pks = np.inf, np.inf, True, []
                for (mk, olm), dcf, dct in itertools.product(models.items(), (-0.1, 0.0, 0.1), (-0.2, 0.0, 0.2)):
                    m = tm.loop_metrics(olm, R_F, C_T + dct * 1e-12, max(cf_pF + dcf, 0.05) * 1e-12)
                    if not m["stable"]:
                        ok = False
                        continue
                    worst_pm = min(worst_pm, m["pm_deg"])
                    if np.isfinite(m["gm_dB"]):
                        worst_gm = min(worst_gm, m["gm_dB"])
                    pks.append(max(m["peaking_dB"], 0.0))
                Z100, _, _ = tm.tia_tf(np.array([100e6]), ol, R_F, C_T, cf)
                row = dict(C_T_pF=C_T * 1e12, ng_inf=1 + C_T / cf, g_min=p["g_min"],
                           f3_MHz=nom["f_3dB"] / 1e6, pm=nom["pm_deg"], peak_dB=max(nom["peaking_dB"], 0.0),
                           f_peak_MHz=nom["f_peak"] / 1e6, all_corners_stable=ok, worst_pm=worst_pm,
                           worst_gm=worst_gm, peak_range_dB=(min(pks), max(pks)) if pks else None,
                           v_pk_100MHz=v_pk, noise={}, penalty_dB={}, dr_100MHz_tone_dB={})
                for fm in fms:
                    tot = {}
                    for I_tot in (0.0, 0.2e-3, 2e-3, 20e-3):
                        c = tm.noise_components(np.array([100e6, 200e6]), R_F, C_T, cf, nz, i_dc=I_tot, fet_model=fm)
                        tot[f"{I_tot*1e3:g}mA"] = list(np.sqrt(c["total"] + S_srv) * 1e12)
                    row["noise"][fm] = tot
                    cN = tm.noise_components(F_NOISE, R_F, C_T, cf, nz, fet_model=fm)
                    row["penalty_dB"][fm] = tm.band_average_penalty_db(
                        F_NOISE, cN["total"] + S_srv, np.full_like(F_NOISE, 4 * KT / R_F), 10e6, 150e6)
                    drs = {}
                    for I_tot in (0.0, 0.2e-3, 2e-3, 20e-3):
                        cb = tm.noise_components(f_band, R_F, C_T, cf, nz, i_dc=I_tot, fet_model=fm)
                        i_rms = tm.integrated_rms(f_band, cb["total"] + S_srv, f_band[0], f_band[-1])
                        drs[f"{I_tot*1e3:g}mA"] = 20 * np.log10(v_pk / abs(Z100[0]) / np.sqrt(2) / i_rms)
                    row["dr_100MHz_tone_dB"][fm] = drs
                out[f"variant|{name}|{C_D*1e12:g}pF|{R_F:.0f}|{cf_pF:.2f}"] = row
                n = row["noise"]["central"]
                hs = ""
                if "high" in row["noise"]:
                    h = row["noise"]["high"]
                    hs = f" (high {h['0mA'][0]:.2f}/{h['0mA'][1]:.2f})"
                pr = row["peak_range_dB"]
                print(f"  {name} {C_D*1e12:g} pF {R_F/1e3:g}k C_F {cf_pF:.2f}: NG_inf {row['ng_inf']:.1f} (G_min {p['g_min']:g}) | "
                      f"f3 {row['f3_MHz']:.0f} MHz, PM {row['pm']:.1f}, peak {row['peak_dB']:.1f} dB | corners stable {ok}, "
                      f"worst PM {worst_pm:.1f}, worst GM {worst_gm:.1f} dB, peak {pr[0] if pr else float('nan'):.1f}-"
                      f"{pr[1] if pr else float('nan'):.1f} dB | dark {n['0mA'][0]:.2f}/{n['0mA'][1]:.2f}{hs}, "
                      f"0.2 mA {n['0.2mA'][0]:.2f}/{n['0.2mA'][1]:.2f}, 2 mA {n['2mA'][0]:.2f}/{n['2mA'][1]:.2f}, "
                      f"20 mA {n['20mA'][0]:.2f}/{n['20mA'][1]:.2f} | penalty "
                      + "/".join(f"{v:.2f}" for v in row["penalty_dB"].values())
                      + " dB | DR " + ", ".join(f"{k} {v:.1f}" for k, v in row["dr_100MHz_tone_dB"]["central"].items()))


def main(out_path):
    out = {}
    node_2pF(out)
    shot(out)
    cascode(out)
    cascode_dark(out)
    cascode_node(out)
    bootstrap(out)
    servo(out)
    splitter(out)
    bias_network(out)
    amplitude_vs_frequency(out)
    proposed_design(out)
    front_end_variants(out)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, default=float)


def variants_only(out_path):
    """Recompute only item 12 and merge it into an existing output file."""
    with open(out_path, encoding="utf-8") as fh:
        out = json.load(fh)
    front_end_variants(out)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, default=float)


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[2] == "variants":
        variants_only(sys.argv[1])
    else:
        main(sys.argv[1])
