"""Dynamic range of the leading op-amp TIAs (SPICE and survey model) and of single-chip TIAs
(datasheet values), with the survey's definitions, Eqs. (24)-(25) (Section 11).

Usage: python dr_comparison.py [--spice <spice folder>] [--tias <integrated_tias.json>] [--out <json>]

Op amps: each part at its best design in SPICE at 1 pF and 2 kOhm (check 'pscan', Table 10.13).
  SPICE: the input-referred noise spectrum simulated at the design, and |Z_T(f0)| of the
         design's nominal corner.
  survey model: Eqs. (7) and (17) with the datasheet curve and datasheet noise, at the same C_F.
  Both use the largest undistorted amplitude V_pk of Eq. (24) from the datasheet swing (light
  load, output centred, DC removed), slew rate and output current.
Single-chip TIAs: the largest linear input-current amplitude and the input-referred noise
  density from their datasheets (data/integrated_tias.json), noise taken as white over 150 MHz
  unless a spectrum is given.  A variable-gain (coherent-receiver) TIA is taken at the one gain
  setting at which its noise is published, its linear input being its linear output swing over
  that transimpedance (Eq. (60)); a per-input DC limit (i_dc_max_A) ends its curve, and other
  settings in the record (alt_settings) are evaluated but not plotted.
Coherent class bound: 3 mAppd of linear input with shot noise only, and the in-band noise such a
  TIA may add and still match each op-amp design at 1 mA.
DR_B = 20 log10[ I_pk / sqrt(2) / sqrt( integral_0^B (S_i(f) + 2 q I_DC) df ) ], B = 150 MHz,
with I_DC = I1 + I2 of the balanced pair and the imbalance servoed to zero.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

import tia_model as tm
from parts_db import PARTS
from run_analysis import noise_inputs, open_loop_model
from spice_tia_checks import C_PCB_NOM, KT, VENDOR_MODELS, _scan_tag, read_wrdata

HERE = Path(__file__).resolve().parent
Q_E = 1.602176634e-19
B_NOISE = 150e6                     # noise bandwidth of Eq. (25)
F0 = 100e6                          # tone of panel (a)
I_DC_GRID = np.logspace(-6, np.log10(20e-3), 121)     # I1 + I2, 1 uA to 20 mA
F0_GRID = np.linspace(20e6, 200e6, 181)               # tones of panel (b), 1-MHz steps
I_DC_FIXED = 1e-3                                       # I1 + I2 of panel (b)
LEADING = ("OPA855", "OPA955", "OPA818", "LMH6629", "OPA858")
R_F, C_D = 2000.0, 1e-12


def v_pk(part, f0, C_F, R_L=np.inf):
    """Eq. (24): the largest undistorted output amplitude, light load, output centred."""
    s = PARTS[VENDOR_MODELS[part]["db"]]["dr"]
    vol, voh = s["swing_light"]
    v_swing = (voh - vol) / 2
    v_slew = s["sr"] * 1e6 / (2 * np.pi * f0)
    g = (0 if np.isinf(R_L) else 1 / R_L) + 1 / R_F + 2 * np.pi * f0 * C_F
    v_cur = (s.get("iout_ma") or np.inf) * 1e-3 / g
    vals = (v_swing, v_slew, v_cur)
    return float(min(vals)), ("swing", "slew rate", "output current")[int(np.argmin(vals))]


def f_swing_to_slew(part):
    """The tone above which the slew rate, not the swing, sets V_pk: SR / (2 pi V_sw)."""
    s = PARTS[VENDOR_MODELS[part]["db"]]["dr"]
    vol, voh = s["swing_light"]
    return s["sr"] * 1e6 / (2 * np.pi * (voh - vol) / 2)


def band_power(f, S, B=B_NOISE):
    """Integral of S from 0 to exactly B: S interpolated (log f) at B, and held at S(f[0]) below the
    first point.  The SPICE sweeps (50 points per decade from 100 kHz) have no point at 150 MHz; the
    last below it is 144.5 MHz, and stopping there would drop 3.7 % of the band."""
    inside = f < B
    ff = np.concatenate([f[inside], [B]])
    SS = np.concatenate([S[inside], [np.interp(np.log10(B), np.log10(f), S)]])
    return float(np.trapezoid(SS, ff) + SS[0] * ff[0])


def dr_db(i_pk, f, S, i_dc):
    """Eq. (25) with the photocurrent's shot noise 2 q I_DC added to the amplifier's S_i(f)."""
    return 20 * np.log10(i_pk / np.sqrt(2) / np.sqrt(band_power(f, S) + 2 * Q_E * i_dc * B_NOISE))


def spice_design(spice, part):
    """C_F of the part's best design and the folders holding its noise and nominal Z_T."""
    e = json.loads((spice / "results" / "pscan.json").read_text(encoding="utf-8"))[part]
    d = e["design"]
    cf = d["cf_pF"] * 1e-12
    noise_dir = spice / "runs" / "pscan" / _scan_tag("noise_P", part, R_F, C_D, cf)
    zt_dir = (spice / "runs" / "pscan" / _scan_tag("verify_P", part, R_F, C_D, cf) if d.get("tol_pF")
              else spice / "runs" / "pscan" / _scan_tag("P", part, R_F, C_D, cf))
    return d, cf, noise_dir, zt_dir


def op_amp_curves(spice, part):
    d, cf, noise_dir, zt_dir = spice_design(spice, part)
    n = read_wrdata(noise_dir / "noise.txt")
    f_n, S_sp = n[:, 0], n[:, 1] ** 2
    z = read_wrdata(zt_dir / "zt.txt")
    zt_sp = lambda f0: float(np.interp(np.log10(f0), np.log10(z[:, 0]), np.abs(z[:, 1] + 1j * z[:, 2])))
    p = PARTS[VENDOR_MODELS[part]["db"]]
    ol, *_ = open_loop_model(p)
    C_T = C_D + C_PCB_NOM + p["c_cm"] + p["c_diff"]
    f_s = np.logspace(4, np.log10(B_NOISE), 3000)
    S_sv = tm.noise_components(f_s, R_F, C_T, cf, noise_inputs(p))["total"]
    zt_sv = lambda f0: float(np.abs(tm.tia_tf(np.array([f0]), ol, R_F, C_T, cf)[0][0]))
    out = dict(design=dict(cf_pF=cf * 1e12, kind=d["kind"], f3_MHz=d["f3_nominal_MHz"]),
               f_swing_to_slew_MHz=f_swing_to_slew(part) / 1e6, spice={}, survey={})
    for name, (f, S, zt) in (("spice", (f_n, S_sp, zt_sp)), ("survey", (f_s, S_sv, zt_sv))):
        vp, lim = v_pk(part, F0, cf)
        i_pk = vp / zt(F0)
        out[name]["vs_idc"] = dict(i_dc_A=list(map(float, I_DC_GRID)),
                                   dr_dB=[float(dr_db(i_pk, f, S, i)) for i in I_DC_GRID],
                                   v_pk_V=vp, limiter=lim, z_t_ohm=zt(F0), i_pk_mA=i_pk * 1e3)
        rows = []
        for f0 in F0_GRID:
            vp0, lim0 = v_pk(part, f0, cf)
            rows.append(dict(f0_MHz=f0 / 1e6, v_pk_V=vp0, limiter=lim0, z_t_ohm=zt(f0),
                             dr_dB=float(dr_db(vp0 / zt(f0), f, S, I_DC_FIXED))))
        out[name]["vs_f0"] = rows
        out[name]["dr_at_dB"] = {f"{i*1e3:g} mA": float(dr_db(i_pk, f, S, i)) for i in (0.0, 1e-4, 1e-3, 1e-2)}
    return out


LIMITS_PART = "OPA818"
LIMITS_F0 = np.logspace(np.log10(10e6), np.log10(300e6), 241)       # tones of Figure 16(a)
LIMITS_I_DC = (1e-4, 1e-3, 1e-2)                                      # I1 + I2 of the floors drawn
# Large-signal ceilings drawn in Figure 16: output amplitudes (V) from the swing at two supplies,
# the 5-V parts' swing for reference, and three slew rates (V/us) around OPA818's 1400 V/us.
LIMITS_SWING = {"swing, ±6.5 V": 5.50,          # OPA818 at 13 V: -5.4/+5.6 V light load (Table 3, DERIVED)
                "swing, ±5 V": 4.00,            # OPA818 at +/-5 V, 1 kOhm: -3.9/+4.1 V typical (Table 3)
                "swing, 5-V parts": 1.525}      # OPA855/OPA955/OPA858: 1.05-4.10 V on 5 V
LIMITS_SR = (700.0, 1400.0, 2800.0)


def limits_example(spice, part=LIMITS_PART):
    """What sets the dynamic range of one design (Figure 16): the band noise floors (0-150 MHz, rms
    input current) and the largest undistorted tone (rms input current, V / (sqrt 2 |Z_T|)) set by
    the swing at two supplies and by three slew rates, against the tone and against I1 + I2."""
    d, cf, noise_dir, zt_dir = spice_design(spice, part)
    n = read_wrdata(noise_dir / "noise.txt")
    p = PARTS[VENDOR_MODELS[part]["db"]]
    C_T = C_D + C_PCB_NOM + p["c_cm"] + p["c_diff"]
    f_s = np.logspace(4, np.log10(B_NOISE), 3000)
    amp_sp = np.sqrt(band_power(n[:, 0], n[:, 1] ** 2))
    amp_sv = np.sqrt(band_power(f_s, tm.noise_components(f_s, R_F, C_T, cf, noise_inputs(p))["total"]))
    johnson = np.sqrt(4 * KT / R_F * B_NOISE)
    shot = lambda i: np.sqrt(2 * Q_E * i * B_NOISE)
    z = read_wrdata(zt_dir / "zt.txt")
    zt = lambda f0: np.interp(np.log10(f0), np.log10(z[:, 0]), np.abs(z[:, 1] + 1j * z[:, 2]))
    to_i = lambda v, f0: v / (np.sqrt(2) * zt(f0))
    f0 = LIMITS_F0
    ceil_f0 = {k: to_i(np.full_like(f0, v), f0) for k, v in LIMITS_SWING.items()}
    ceil_f0.update({f"slew rate, {sr:g} V/µs": to_i(sr * 1e6 / (2 * np.pi * f0), f0) for sr in LIMITS_SR})
    v_act = np.minimum(LIMITS_SWING["swing, ±6.5 V"], 1400.0 * 1e6 / (2 * np.pi * f0))
    ceil_f0["OPA818 on ±6.5 V"] = to_i(v_act, f0)
    ceil_100 = {k: float(to_i(v, F0)) for k, v in LIMITS_SWING.items()}
    ceil_100.update({f"slew rate, {sr:g} V/µs": float(to_i(sr * 1e6 / (2 * np.pi * F0), F0)) for sr in LIMITS_SR})
    v100, _ = v_pk(part, F0, cf)
    total = lambda i: np.sqrt(amp_sp ** 2 + shot(i) ** 2)
    return dict(part=part, cf_pF=cf * 1e12, f3_MHz=d["f3_nominal_MHz"], B_MHz=B_NOISE / 1e6, f0_MHz=F0 / 1e6,
                floors_nA=dict(johnson=johnson * 1e9, amp_spice=amp_sp * 1e9, amp_survey=amp_sv * 1e9,
                               shot={f"{i*1e3:g} mA": shot(i) * 1e9 for i in LIMITS_I_DC},
                               total_spice={f"{i*1e3:g} mA": total(i) * 1e9 for i in LIMITS_I_DC}),
                vs_f0=dict(f0_MHz=list(f0 / 1e6), z_t_ohm=list(zt(f0)),
                           ceilings_nA={k: list(v * 1e9) for k, v in ceil_f0.items()}),
                vs_idc=dict(i_dc_A=list(I_DC_GRID),
                            total_spice_nA=list(total(I_DC_GRID) * 1e9),
                            total_survey_nA=list(np.sqrt(amp_sv ** 2 + shot(I_DC_GRID) ** 2) * 1e9),
                            shot_nA=list(shot(I_DC_GRID) * 1e9), ceilings_100MHz_nA={k: v * 1e9 for k, v in ceil_100.items()}),
                ceiling_100MHz=dict(v_pk_V=v100, i_rms_nA=float(to_i(v100, F0)) * 1e9),
                dr_100MHz_dB={f"{i*1e3:g} mA": float(20 * np.log10(to_i(v100, F0) / total(i))) for i in (0.0,) + LIMITS_I_DC})


def tia_noise_density(t):
    """Input-referred noise density (A/rtHz) of a datasheet record: the stated density, or else the
    stated integrated noise spread evenly over the bandwidth it was integrated in."""
    if t.get("noise_density_A_rtHz"):
        return t["noise_density_A_rtHz"]
    if t.get("noise_rms_A") and t.get("noise_bw_Hz"):
        return t["noise_rms_A"] / np.sqrt(t["noise_bw_Hz"])
    return None


def tia_curves(t):
    """A single-chip TIA from its datasheet record: the linear input amplitude and the noise density
    taken as independent of frequency up to the TIA's bandwidth, noise white over the 150-MHz band.
    With i_dc_max_A the curve ends at that I1 + I2 and points beyond it are None."""
    i_pk = t["i_pk_lin_A"]
    S = tia_noise_density(t) ** 2
    f = np.array([1e5, B_NOISE])            # white: band_power() holds S below the first point
    S_arr = np.full_like(f, S)
    f_top = min(F0_GRID[-1], (t.get("bw_MHz") or np.inf) * 1e6)
    i_max = t.get("i_dc_max_A") or np.inf
    grid = I_DC_GRID[I_DC_GRID < i_max]
    if np.isfinite(i_max):
        grid = np.append(grid, i_max)
    dr_fix = float(dr_db(i_pk, f, S_arr, I_DC_FIXED))
    out = dict(vs_idc=dict(i_dc_A=list(map(float, grid)),
                           dr_dB=[float(dr_db(i_pk, f, S_arr, i)) for i in grid], i_pk_mA=i_pk * 1e3),
               vs_f0=[dict(f0_MHz=f0 / 1e6, dr_dB=dr_fix) for f0 in F0_GRID if f0 <= f_top],
               noise_density_pA_rtHz=np.sqrt(S) * 1e12,
               dr_at_dB={f"{i*1e3:g} mA": float(dr_db(i_pk, f, S_arr, i)) if i <= i_max else None
                         for i in (0.0, 1e-4, 1e-3, 1e-2)})
    if np.isfinite(i_max):
        out["dc_limit"] = dict(i_dc_max_mA=i_max * 1e3, dr_dB=float(dr_db(i_pk, f, S_arr, i_max)))
    alts = []
    for a in t.get("alt_settings", []):
        S_a = np.full_like(f, a["noise_density_A_rtHz"] ** 2)
        alts.append(dict(label=a["label"], z_t_ohm=a.get("z_t_ohm"), i_pk_mA=a["i_pk_lin_A"] * 1e3,
                         dr_at_dB={f"{i*1e3:g} mA": float(dr_db(a["i_pk_lin_A"], f, S_a, i))
                                   for i in (0.0, 1e-4, 1e-3, 1e-2)}))
    if alts:
        out["alt_settings"] = alts
    return out


COHERENT_I_PK = 1.5e-3      # 3 mAppd: the largest linear differential input of the coherent TIAs (Section 11.4)


def coherent_bound(ops):
    """A coherent TIA at the low gain where its 3-mAppd input stays linear: Eq. (57) with shot noise
    only, and the in-band input noise density it may add and still match each op-amp design at 1 mA."""
    shot = lambda i: 2 * Q_E * i * B_NOISE
    i_rms = COHERENT_I_PK / np.sqrt(2)
    out = dict(i_pk_mA=COHERENT_I_PK * 1e3,
               dr_shot_only_dB={f"{i*1e3:g} mA": float(20 * np.log10(i_rms / np.sqrt(shot(i))))
                                for i in (1e-4, 1e-3, 1e-2)},
               noise_to_match_at_1mA_pA_rtHz={})
    for p in ("OPA818", "OPA855", "OPA955"):
        total2 = (i_rms / 10 ** (ops[p]["spice"]["dr_at_dB"]["1 mA"] / 20)) ** 2
        out["noise_to_match_at_1mA_pA_rtHz"][p] = float(np.sqrt(max(total2 - shot(1e-3), 0.0) / B_NOISE) * 1e12)
    return out


def _fmt_dr(d):
    return ", ".join(f"{k} {v:.1f}" if v is not None else f"{k} -" for k, v in d.items())


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--spice", type=Path, default=HERE.parent / "spice")
    ap.add_argument("--tias", type=Path, default=HERE.parent / "data" / "integrated_tias.json")
    ap.add_argument("--out", type=Path, default=HERE.parent / "spice" / "results" / "dr_comparison.json")
    a = ap.parse_args()
    res = dict(definition=dict(B_MHz=B_NOISE / 1e6, f0_MHz=F0 / 1e6, i_dc_fixed_mA=I_DC_FIXED * 1e3,
                               R_F=R_F, C_D_pF=C_D * 1e12), op_amps={}, tias={})
    for part in LEADING:
        r = op_amp_curves(a.spice, part)
        res["op_amps"][part] = r
        for k in ("spice", "survey"):
            s = r[k]
            print(f"{part:8s} {k:6s}: C_F {r['design']['cf_pF']:.3f} pF, V_pk(100 MHz) {s['vs_idc']['v_pk_V']:.2f} V "
                  f"({s['vs_idc']['limiter']}), |Z_T| {s['vs_idc']['z_t_ohm']:.0f} ohm, I_pk {s['vs_idc']['i_pk_mA']:.3f} mA | "
                  + ", ".join(f"{kk} {v:.1f}" for kk, v in s["dr_at_dB"].items()) + " dB")
    lim = limits_example(a.spice)
    res["limits_example"] = lim
    fl = lim["floors_nA"]
    print(f"limits ({lim['part']}, C_F {lim['cf_pF']:.3f} pF): R_F alone {fl['johnson']:.1f}, amplifier + R_F "
          f"{fl['amp_spice']:.1f} (survey {fl['amp_survey']:.1f}) nA rms; ceiling at 100 MHz "
          f"{lim['ceiling_100MHz']['i_rms_nA']:.0f} nA rms; DR " + ", ".join(f"{k} {v:.1f}" for k, v in lim["dr_100MHz_dB"].items()) + " dB")
    if a.tias.exists():
        tias = json.loads(a.tias.read_text(encoding="utf-8"))
        for name, t in tias["parts"].items():
            if t.get("i_pk_lin_A") and tia_noise_density(t):
                e = res["tias"][name] = dict(tia_curves(t), label=t.get("label", name), record=t)
                print(f"{name:10s}: I_pk {t['i_pk_lin_A']*1e3:.4f} mA, noise {tia_noise_density(t)*1e12:.2f} pA/rtHz | "
                      + _fmt_dr(e["dr_at_dB"]) + " dB" + ("" if t.get("plotted", True) else " (not plotted)"))
                if "dc_limit" in e:
                    print(f"{'':12s}DC limit: I1 + I2 <= {e['dc_limit']['i_dc_max_mA']:g} mA, DR there "
                          f"{e['dc_limit']['dr_dB']:.1f} dB")
                for alt in e.get("alt_settings", []):
                    print(f"{'':12s}{alt['label']}: I_pk {alt['i_pk_mA']:.4f} mA | " + _fmt_dr(alt["dr_at_dB"]) + " dB")
            else:
                print(f"{name:10s}: not plotted (no linear input range or no noise figure in the record)")
        cb = res["coherent_bound"] = coherent_bound(res["op_amps"])
        print(f"coherent class, {cb['i_pk_mA']:g} mA peak, shot noise only: " + _fmt_dr(cb["dr_shot_only_dB"]) + " dB; "
              "in-band noise allowed to match at 1 mA: "
              + ", ".join(f"{p} {v:.1f}" for p, v in cb["noise_to_match_at_1mA_pA_rtHz"].items()) + " pA/rtHz")
    a.out.write_text(json.dumps(res, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
