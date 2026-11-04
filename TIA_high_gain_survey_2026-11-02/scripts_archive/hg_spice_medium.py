"""SPICE checks at 10 kOhm, where this note meets the companion (Section 9.8, 4 November 2026).

The vendors' macromodels run in ngspice (the shared library that KiCad 10 installs, through ngspice_shared.py) and
are compared with the analytic models at the same feedback capacitance.

1. The 20-pF photodiode (S1336-18BK, 2 GOhm), with 1 pF of board capacitance and a 10-kOhm load as in the designs
   check of hg_spice.py, at R_F = 10 kOhm for OPA818, OPA858, OPA855, OPA955 and LMH6629 (COMP pin high): the sweep's own
   design (the smallest C_F >= 0.1 pF within 0.1 dB of maximally flat, data/results/designs.json) and the designs
   of Table 6.8 held to 10 MHz and 30 MHz (data/results/medium_gain.json). Transimpedance (ac) and input-referred
   noise (noise, referred to the photocurrent source) against hg_model.py: the -3 dB bandwidth, the peaking, the
   noise density at 1, 10 and 30 MHz, and the excess noise Delta N of Eq. (16) over [1 Hz, B] for both, with B the
   model's bandwidth (the column's bandwidth for the designs of Table 6.8); each one's Delta N over its own
   bandwidth is kept in the JSON file as well.
2. The companion's node, a 1-pF photodiode pair with 0.35 pF of board capacitance, with the companion's supplies
   and loads (its spice_tia_checks.py), at R_F = 10 kOhm for OPA855, OPA955 and OPA818: this note's design for 0.1 pF
   of parasitic (0.10 pF for OPA855 and OPA955, which is also the companion model's design; OPA818 0.195 pF, against
   0.193 pF in the companion's Table A6.39), and the companion's Table A6.38 design for its nominal 0.2 pF (read from
   its data/results/medium_gain.json). OPA955's model is TI's TINA-TI netlist as the companion extracted it.
   Transimpedance, the loop gain by Middlebrook's double injection, and noise, against this note's single-pole
   model and the companion's open-loop model (its tia_model.py, parts_db.py and run_analysis.py, imported read
   only): bandwidth, peaking, phase margin, the noise density at 10 and 50 MHz, and the companion's band average
   over 10 MHz to the lower of 150 MHz and its model's bandwidth, against the Johnson noise of R_F.

The model files are read from spice/models/ (spice/models/README.md gives their sources) and translated into
spice/runs/_models/ as in hg_spice.py. Decks, logs and arrays go to spice/runs/medium/<case>/, the summary to
spice/results/medium.json. Run with python -B so that no bytecode is written into the companion's folder.

Usage: python -B hg_spice_medium.py
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

import hg_model as m
import hg_spice as hs
from ngspice_shared import NgSpice

HERE = Path(__file__).resolve().parent
COMPANION = HERE.parents[1] / "TIA_opamp_survey_2026-10-25"
sys.path.append(str(COMPANION / "scripts_archive"))   # appended, so that this folder's modules come first
import tia_model as tm  # noqa: E402
from parts_db import PARTS  # noqa: E402
from run_analysis import C_PCB_NOM, noise_inputs, open_loop_model  # noqa: E402

RF = 1e4
# the four models that the other checks of this note do not use, instantiated as in the companion's
# spice_tia_checks.py
hs.MODELS.update({
    "OPA955": dict(lib="OPA955/OPA955_from_TINA.lib", inst="{p} {n} {o} vcc vee OPA955", vs=2.5,
                   source="TI SLOM544, OPA955 TINA-TI model (netlist dated 2026-07-06), extracted unchanged as in "
                          "the companion note"),
    "OPA855": dict(lib="OPA855/opa855_a.lib", inst="{p} {n} {o} vcc vee OPA855", vs=2.5,
                   source="TI SBOMB43D, OPA855 unencrypted PSpice model package (Rev. D), as in the companion note"),
    "OPA858": dict(lib="OPA858/OPA858.lib", inst="{p} {n} vcc vee {o} OPA858", vs=2.5,
                   source="TI SBOMBK7, OPA858 PSpice model, as in the companion note"),
    "LMH6629": dict(lib="LMH6629/LMH6629.MOD", inst="{p} {n} vcc vee {o} vcc LMH6629", vs=2.5,
                    source="TI SNOM133, LMH6629 PSpice model with the COMP pin high, as in the companion note"),
})
PARTS_20 = ("OPA818", "OPA858", "OPA855", "OPA955", "LMH6629")
TARGETS = (10e6, 30e6)
SPOT_20 = (1e6, 10e6, 30e6)

# the companion's TIA decks: each part's supply and load (vs_tia and rl in its spice_tia_checks.py)
COMPANION_DECK = {"OPA855": dict(vs=2.5, rl=200.0), "OPA955": dict(vs=2.5, rl=200.0), "OPA818": dict(vs=6.5, rl=100.0)}
C_D_NODE = 1e-12
NODE = m.Source("companion 1-pF node", C_D_NODE, math.inf)
SPOT_NODE = (10e6, 50e6)
F_HG = np.logspace(-2, 9.5, 2600)          # the frequency grid of hg_medium_gain.py
F_LIN = np.linspace(1e4, 400e6, 40001)      # the frequency grid of the companion's medium_gain.py


def prepare(parts) -> None:
    """Translated copies of the vendor models under spice/runs/_models/ (the originals are not touched)."""
    dst_dir = hs.RUNS / "_models"
    dst_dir.mkdir(parents=True, exist_ok=True)
    for part in parts:
        src = hs.SPICE / "models" / hs.MODELS[part]["lib"]
        (dst_dir / src.name).write_text(hs.translate_model(src.read_text(encoding="latin-1")), encoding="latin-1")


def loop_metrics_from_t(f: np.ndarray, t: np.ndarray) -> dict:
    """Crossover, phase margin and gain margin of a loop gain T(f), as in the companion's spice_tia_checks.py."""
    mag = np.abs(t)
    ph = np.degrees(np.unwrap(np.angle(t)))
    above = mag >= 1
    idx = np.where(above[:-1] & ~above[1:])[0]
    res = dict(f_c_Hz=None, pm_deg=None, gm_dB=None)
    if len(idx):
        i = idx[0]
        x = (0 - 20 * np.log10(mag[i])) / (20 * np.log10(mag[i + 1]) - 20 * np.log10(mag[i]))
        fc = 10 ** (np.log10(f[i]) + x * (np.log10(f[i + 1]) - np.log10(f[i])))
        res["f_c_Hz"] = float(fc)
        res["pm_deg"] = float(180 + np.interp(np.log10(fc), np.log10(f), ph))
        j = np.where((ph[i:-1] > -180) & (ph[i + 1:] <= -180))[0]
        if len(j):
            k = i + j[0]
            res["gm_dB"] = float(-20 * np.log10(np.interp(-180, [ph[k + 1], ph[k]], [mag[k + 1], mag[k]])))
    return res


# ---------------------------------------------------------------- the 20-pF photodiode
def check_20pf(ng: NgSpice, amps: dict) -> list:
    sweep = json.loads((m.DATA / "results" / "designs.json").read_text(encoding="utf-8"))
    eqbw = json.loads((m.DATA / "results" / "medium_gain.json").read_text(encoding="utf-8"))["equal_bandwidth"]
    c_d, r_sh = hs.SOURCES["S1336-18BK"]
    src = m.Source("S1336-18BK", c_d, r_sh)
    floor = m.FOUR_KT / RF + m.FOUR_KT / r_sh
    out = []
    for part in PARTS_20:
        d0 = next(r for r in sweep if r["amp"] == part and r["rf"] == RF
                  and r["source"] == hs.SWEEP_NAMES["S1336-18BK"])
        designs = [("own design", d0["cf_pF"] * 1e-12, None)]
        for target in TARGETS:
            r = next(x for x in eqbw if x["amp"] == part and x["rf"] == RF and x["target_Hz"] == target)
            designs.append((f"held to {target / 1e6:g} MHz", r["cf_pF"] * 1e-12, target))
        for label, c_f, target in designs:
            case = f"{part}_20pF_10k_" + ("own" if target is None else f"{target / 1e6:g}MHz")
            folder = hs.RUNS / "medium" / case
            body = (hs.header(part, case) + hs.amp(part, "0", "inm", "out")
                    + f"RF out inm {RF:g}\nCF out inm {c_f:.6g}\nCD inm 0 {c_d + hs.C_STRAY:.6g}\n"
                      f"RSH inm 0 {r_sh:g}\nIph 0 inm DC 0 AC 1\nRL out 0 10k\n")
            errs = hs.run(ng, hs.write_deck(folder, body + ".control\n"
                                            + hs.CONTROL_AC.format(ppd=40, f1=0.1, f2=1e9, name="zt.txt")
                                            + ".endc\n.end\n", "ac.cir"))
            errs += hs.run(ng, hs.write_deck(folder, body + ".control\n"
                                             + hs.CONTROL_NOISE.format(src="Iph", ppd=40, f1=0.1, f2=1e9,
                                                                       name="noise.txt")
                                             + ".endc\n.end\n", "noise.cir"))
            zt = hs.read_cols(folder / "zt.txt")
            nz = hs.read_cols(folder / "noise.txt")
            f, z = zt[:, 0], zt[:, 1] + 1j * zt[:, 2]
            fn, inoise = nz[:, 0], nz[:, 1]
            d = m.Design(amps[part], RF, c_f, src, c_stray=hs.C_STRAY)
            f3s, pks = hs.f3_peak(f, z)
            f3a, pka = hs.f3_peak(f, d.zt(f))
            na = d.noise(fn)["total"]
            b = target or f3a

            def dn(s: np.ndarray, hi: float) -> float:
                return 10 * math.log10(hs.band(fn, s, 1.0, hi) / (floor * (hi - 1.0)))

            spot = {f"{x / 1e6:g} MHz": dict(
                spice_pA=float(np.interp(np.log10(x), np.log10(fn), inoise) * 1e12),
                model_pA=float(math.sqrt(np.interp(np.log10(x), np.log10(fn), na)) * 1e12)) for x in SPOT_20}
            np.save(folder / "compare.npy", np.vstack([fn, inoise, np.sqrt(na),
                                                       np.interp(np.log10(fn), np.log10(f), np.abs(z)),
                                                       np.abs(d.zt(fn))]))
            row = dict(part=part, design=label, cf_pF=c_f * 1e12, band_Hz=b, f3_spice=f3s, f3_model=f3a,
                       peak_spice=pks, peak_model=pka, dN_spice=dn(inoise ** 2, b), dN_model=dn(na, b),
                       dN_spice_own=dn(inoise ** 2, f3s), dN_model_own=dn(na, f3a), spot=spot,
                       zt0_spice=float(abs(z[0])), errors=errs[:3])
            out.append(row)
            print(f"{case}: C_F {c_f * 1e12:.3f} pF, f3 {f3s / 1e6:.1f}/{f3a / 1e6:.1f} MHz, peak "
                  f"{pks:.2f}/{pka:.2f} dB, dN over [1 Hz, {b / 1e6:.1f} MHz] {row['dN_spice']:.2f}/"
                  f"{row['dN_model']:.2f} dB; " + "; ".join(f"{k} {v['spice_pA']:.2f}/{v['model_pA']:.2f}"
                                                            for k, v in spot.items())
                  + f" pA/rtHz{' ERR' if errs else ''}", flush=True)
    return out


# ---------------------------------------------------------------- the companion's 1-pF node
def node_header(part: str, title: str) -> str:
    vs = COMPANION_DECK[part]["vs"]
    return (f"* {title}\n.include ../../_models/{Path(hs.MODELS[part]['lib']).name}\n.temp 25\n"
            f"VCC vcc 0 DC {vs:g}\nVEE vee 0 DC {-vs:g}\n")


def node_body(part: str, c_f: float, vinj_ac: int = 0, iinj_ac: int = 0, iph_ac: int = 0) -> str:
    """The companion's inverting TIA: summing node inm, amplifier output oa, feedback side of the injection fb."""
    return (hs.amp(part, "0", "inm", "oa")
            + f"Vinj fb oa DC 0 AC {vinj_ac}\nIinj 0 fb DC 0 AC {iinj_ac}\n"
            + f"RF fb inm {RF:g}\nCF fb inm {c_f:.6g}\nCX inm 0 {C_D_NODE + C_PCB_NOM:.6g}\n"
              f"RL oa 0 {COMPANION_DECK[part]['rl']:g}\nIph 0 inm DC 0 AC {iph_ac}\n")


def check_node(ng: NgSpice, amps: dict) -> list:
    ours = {r["amp"]: r for r in json.loads((m.DATA / "results" / "medium_gain.json").read_text(encoding="utf-8"))
            ["cross_check"] if r["rf"] == RF}
    a638 = {r["amp"]: r for r in json.loads((COMPANION / "data" / "results" / "medium_gain.json")
                                            .read_text(encoding="utf-8"))
            if r["rf"] == RF and abs(r["c_fpar_pF"] - 0.2) < 1e-9}
    designs = ([(p, ours[p]["cf_pF"] * 1e-12, "this note's design for 0.1 pF of parasitic") for p in COMPANION_DECK]
               + [(p, a638[p]["design"]["C_F_real_pF"] * 1e-12, "the companion's Table A6.38 design (0.2 pF)")
                  for p in COMPANION_DECK])
    s_ref = 4 * tm.K_B * tm.T_ROOM / RF
    out = []
    for part, c_f, label in designs:
        case = f"{part}_node1pF_10k_CF{c_f * 1e12:.3f}p".replace(".", "p")
        folder = hs.RUNS / "medium" / case
        errs = hs.run(ng, hs.write_deck(folder, node_header(part, case) + node_body(part, c_f, iph_ac=1)
                                        + ".control\nset wr_singlescale\nset wr_vecnames\nac dec 100 100k 10G\n"
                                          "wrdata zt.txt real(v(oa)) imag(v(oa))\n.endc\n.end\n", "zt.cir"))
        errs += hs.run(ng, hs.write_deck(folder, node_header(part, case) + node_body(part, c_f, vinj_ac=1)
                                         + ".control\nset wr_singlescale\nset wr_vecnames\nac dec 100 100k 30G\n"
                                           "wrdata vinj.txt real(v(oa)) imag(v(oa)) real(v(fb)) imag(v(fb))\n"
                                           "alter @vinj[acmag] = 0\nalter @iinj[acmag] = 1\nac dec 100 100k 30G\n"
                                           "wrdata iinj.txt real(i(vinj)) imag(i(vinj))\n.endc\n.end\n", "loop.cir"))
        errs += hs.run(ng, hs.write_deck(folder, node_header(part, case) + node_body(part, c_f, iph_ac=1)
                                         + ".control\nset wr_singlescale\nset wr_vecnames\n"
                                           "noise v(oa) Iph dec 50 100k 1G\nsetplot noise1\n"
                                           "wrdata noise.txt inoise_spectrum onoise_spectrum\n.endc\n.end\n",
                                         "noise.cir"))
        zt = hs.read_cols(folder / "zt.txt")
        f, z = zt[:, 0], zt[:, 1] + 1j * zt[:, 2]
        v = hs.read_cols(folder / "vinj.txt")
        c = hs.read_cols(folder / "iinj.txt")
        tv = -(v[:, 1] + 1j * v[:, 2]) / (v[:, 3] + 1j * v[:, 4])
        iv = c[:, 1] + 1j * c[:, 2]
        ti = iv / (1 - iv)
        t = (tv * ti - 1) / (tv + ti + 2)
        nz = hs.read_cols(folder / "noise.txt")
        fn, inoise = nz[:, 0], nz[:, 1]
        f3s, pks = hs.f3_peak(f, z)
        lp = loop_metrics_from_t(v[:, 0], t)
        # the companion's open-loop model at the same C_F
        p = PARTS[part]
        ol = open_loop_model(p)[0]
        c_t = C_D_NODE + C_PCB_NOM + p["c_cm"] + p["c_diff"]
        mt = tm.loop_metrics(ol, RF, c_t, c_f)
        s_comp = tm.noise_components(F_LIN, RF, c_t, c_f, noise_inputs(p), fet_model="central")["total"]
        # this note's single-pole model at the same C_F
        d = m.Design(amps[part], RF, c_f, NODE, c_stray=C_PCB_NOM)
        hm = m.response_metrics(d, F_HG)
        s_hg = d.noise(F_LIN)["total"]
        f_hi = min(150e6, mt["f_3dB"])
        sel = (F_LIN >= 10e6) & (F_LIN <= f_hi)

        def avg_db(s: np.ndarray) -> float:
            return 10 * math.log10(np.trapezoid(s[sel], F_LIN[sel]) / (F_LIN[sel][-1] - F_LIN[sel][0]) / s_ref)

        spot = {f"{x / 1e6:g} MHz": dict(
            spice_pA=float(np.interp(np.log10(x), np.log10(fn), inoise) * 1e12),
            companion_pA=float(math.sqrt(np.interp(x, F_LIN, s_comp)) * 1e12),
            this_note_pA=float(math.sqrt(np.interp(x, F_LIN, s_hg)) * 1e12)) for x in SPOT_NODE}
        np.save(folder / "compare.npy", np.vstack([v[:, 0], t.real, t.imag]))
        np.save(folder / "noise.npy", nz.T)
        row = dict(part=part, design=label, cf_pF=c_f * 1e12, supply_V=COMPANION_DECK[part]["vs"],
                   load_ohm=COMPANION_DECK[part]["rl"],
                   spice=dict(f3_Hz=f3s, peak_dB=pks, pm_deg=lp["pm_deg"], f_c_Hz=lp["f_c_Hz"], gm_dB=lp["gm_dB"],
                              penalty_dB=10 * math.log10(hs.band(fn, inoise ** 2, 10e6, f_hi) / (f_hi - 10e6) / s_ref)),
                   companion_model=dict(f3_Hz=mt["f_3dB"], peak_dB=max(0.0, mt["peaking_dB"]), pm_deg=mt["pm_deg"],
                                        f_c_Hz=mt["f_c"], penalty_dB=avg_db(s_comp),
                                        penalty_own_method_dB=tm.band_average_penalty_db(
                                            F_LIN, s_comp, np.full_like(F_LIN, s_ref), 10e6, f_hi)),
                   this_note_model=dict(f3_Hz=hm["f3"], peak_dB=hm["peak_db"], pm_deg=hm["pm"],
                                        penalty_dB=avg_db(s_hg)),
                   band_MHz=[10.0, f_hi / 1e6], spot=spot, errors=errs[:3])
        out.append(row)
        s, a, h = row["spice"], row["companion_model"], row["this_note_model"]
        print(f"{case} ({label}): f3 {s['f3_Hz'] / 1e6:.1f} / {a['f3_Hz'] / 1e6:.1f} / {h['f3_Hz'] / 1e6:.1f} MHz; "
              f"peak {s['peak_dB']:.2f} / {a['peak_dB']:.2f} / {h['peak_dB']:.2f} dB; PM "
              f"{s['pm_deg'] if s['pm_deg'] is None else round(s['pm_deg'], 1)} / {a['pm_deg']:.1f} / "
              f"{h['pm_deg']:.1f} deg; noise 10-{f_hi / 1e6:.0f} MHz {s['penalty_dB']:.2f} / {a['penalty_dB']:.2f} "
              f"/ {h['penalty_dB']:.2f} dB (SPICE / companion / this note)" + (" ERR" if errs else ""), flush=True)
    return out


def main() -> None:
    amps = m.load_amps()
    prepare(set(PARTS_20) | set(COMPANION_DECK))
    ng = NgSpice()
    res = {"rf": RF, "designs_20pF": check_20pf(ng, amps), "companion_node": check_node(ng, amps),
           "models": {p: hs.MODELS[p]["source"] for p in sorted(set(PARTS_20) | set(COMPANION_DECK))}}
    hs.RESULTS.mkdir(parents=True, exist_ok=True)
    with open(hs.RESULTS / "medium.json", "w", encoding="utf-8", newline="\n") as fh:
        json.dump(res, fh, indent=1)
    print("== medium written", flush=True)


if __name__ == "__main__":
    main()
