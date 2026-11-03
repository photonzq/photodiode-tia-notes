"""SPICE checks of the high-gain TIA note, with the vendors' macromodels in ngspice
(the shared library that KiCad 10 installs, driven by ngspice_shared.py).

Usage:  python hg_spice.py <check> [<check> ...]
        <check> = designs | models | distributed | composite

  designs      the TIA designs of the sweep (C_F as designed by hg_analysis.py) for seven
               op amps at 100 kOhm-1 GOhm on the 20-pF and 380-pF photodiodes: transimpedance
               (ac) and input-referred noise (noise, referred to the photocurrent source),
               against the analytic model of hg_model.py at the same C_F.
  models       each macromodel's own input voltage noise (unity-gain buffer, + input
               driven) and input current noise (the same with a noiseless 100-MOhm or
               10-GOhm resistor in series), against the datasheet values.
  distributed  a 1-GOhm feedback resistor as a 20-section RC ladder (0.05 pF end to end,
               0.3 pF to the conductor beneath it) with that conductor grounded, driven
               from the output, driven at one third of the output, split into four
               strips driven at their mid-point potentials, or graded ideally; OPA140 and
               OPA928 on the 20-pF photodiode: transimpedance, step response and noise,
               against hg_model.ladder_y with a single-pole amplifier.
  composite    a cascoded LSBF862 common-source stage (Linear Systems' card) followed by
               OPA140, at 100 kOhm-10 MOhm on the 380-pF and 1-nF photodiodes, against
               OPA140 alone and against the analytic model.

The vendor model files are not part of the note's publication; spice/models/README.md
gives their sources.  They are translated into spice/runs/_models/ (PSpice T_ABS
noiseless resistors to ngspice noisy=0, CAP models to C; the translation is copied from
the companion note's spice_tia_checks.py).  Decks, logs and raw data go to
spice/runs/<check>/<case>/; summaries to spice/results/<check>.json.
"""
from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

import numpy as np

import hg_model as m
from ngspice_shared import NgSpice

ROOT = Path(__file__).resolve().parent.parent
SPICE = ROOT / "spice"
RUNS = SPICE / "runs"
RESULTS = SPICE / "results"

MODELS = {
    "OPA928": dict(lib="OPA928/extracted/OPAx928.LIB", inst="{p} {n} vcc vee {o} grd1 grd2 OPAX928", vs=15.0,
                   extra="RG1 grd1 0 1MEG\nRG2 grd2 0 1MEG\n", source="TI SBOMCC0, OPA928 PSpice Model (Rev. A)"),
    "OPA140": dict(lib="OPA140/extracted/OPAx140.LIB", inst="{p} {n} vcc vee {o} OPAx140", vs=15.0,
                   source="TI SBOM493, OPAx140 PSpice Model (Rev. D)"),
    "OPA828": dict(lib="OPA828/extracted/OPAx828.LIB", inst="{p} {n} vcc vee {o} OPAx828", vs=15.0,
                   source="TI SBOMAJ0, OPAx828 PSpice Model (Rev. D)"),
    "OPA320": dict(lib="OPA320/extracted/OPAx320-Q1.LIB", inst="{p} {n} vcc vee {o} OPAx320-Q1", vs=2.5,
                   source="TI SBOM437, OPAx320 PSpice Model (Rev. G), file OPAx320-Q1.LIB"),
    "OPA1656": dict(lib="OPA1656/extracted/OPA1656.LIB", inst="{p} {n} vcc vee {o} OPA1656", vs=15.0,
                    source="TI SBOMAW6, OPA1656 PSpice Model (Rev. C)"),
    "OPA2156": dict(lib="OPA2156/extracted/OPA2156.LIB", inst="{p} {n} vcc vee {o} OPA2156", vs=15.0,
                    source="TI SBOMAR0, OPA2156 PSpice Model (Rev. B)"),
    "OPA818": dict(lib="OPA818/opa818.lib", inst="{p} {n} {o} vcc vee OPA818", vs=5.0,
                   source="TI SBOMB74B, as in the companion note"),
    "OPA657": dict(lib="OPA657/OPA657.lib", inst="vee vcc {n} {p} {o} OPA657", vs=5.0,
                   source="TI SBOM137, OPA657 PSpice Model (Rev. F), as in the companion note"),
    "ADA4817-1": dict(lib="ADA4817-1/ada4817.cir", inst="{p} {n} vcc vee {o} {o} vcc ADA4817", vs=5.0,
                      source="ADI ADA4817 SPICE Macro Model, Rev. 2.1 (2017), as in the companion note"),
}

# Linear Systems' published LSBF862 card, as typed into the companion note's
# spice_composite_checks.py (FET_CARDS); it remains Linear Systems' model.
LSBF862 = (".model LSBF862 NJF (VTO=-0.79 BETA=2.658E-2 VTOTC=-2.5m BETATCE=-0.5 LAMBDA=0.03 RD=7.5 RS=7.5 "
           "IS=1E-14 ISR=1E-13 N=1 NR=2 XTI=3 ZXTI=1 ALPHA=1E-4 VK=180 CGS=8P CGD=3.5P PB=0.5 M=0.33 MJ=0.33 "
           "FC=0.5 KF=8.75E-17 AF=1 GDSNOI=2 NLEV=3 MFG=Linear_Systems)")

SOURCES = {"S1336-18BK": (20e-12, 2e9), "S1336-8BK": (380e-12, 0.4e9),
           "G12180-050A": (1e-9, 6.5e6)}
SWEEP_NAMES = {"S1336-18BK": "S1336-18BK (Si 1.1 mm)", "S1336-8BK": "S1336-8BK (Si 5.8 mm)",
               "G12180-050A": "G12180-050A (InGaAs 5 mm)"}
C_STRAY = 1e-12

# ---------------------------------------------------------------- models
_RES_TABS = re.compile(r"^(\s*\.model\s+)(\S+)(\s+)res\s*\(([^)]*?)\bt_abs\s*=\s*([-+0-9.eE]+)([^)]*)\)",
                       re.I | re.M)
_CAP_MODEL = re.compile(r"^(\s*\.model\s+\S+\s+)cap(\b)", re.I | re.M)


def translate_model(text: str) -> str:
    """PSpice to ngspice (copied from the companion note's spice_tia_checks.py): ngspice
    takes T_ABS as an offset from 27 C, so the 'noiseless' resistors (T_ABS = -273) would
    be noisy at about 27 K; they become resistor models with noisy=0.  Other T_ABS values
    become instance temperatures; the PSpice capacitor model type CAP becomes C."""
    other = {}

    def card(mm):
        name, t = mm.group(2), float(mm.group(5))
        rest = " ".join(re.sub(r"\btce\s*=\s*0+(\.0*)?\b", "", mm.group(4) + " " + mm.group(6), flags=re.I).split())
        if t <= -273.0:
            return f"{mm.group(1)}{name}{mm.group(3)}R ({rest + ' ' if rest else ''}noisy=0)"
        other[name.lower()] = t
        return f"{mm.group(1)}{name}{mm.group(3)}R ({rest})"

    text = _RES_TABS.sub(card, text)
    text = _CAP_MODEL.sub(r"\1C\2", text)
    if other:
        lines = text.splitlines()
        for i, ln in enumerate(lines):
            tok = ln.split()
            if len(tok) >= 5 and tok[0][:1].upper() == "R" and tok[3].lower() in other:
                lines[i] = ln + f" temp={other[tok[3].lower()]:g}"
        text = "\n".join(lines) + "\n"
    return text


def prepare_models() -> None:
    dst_dir = RUNS / "_models"
    dst_dir.mkdir(parents=True, exist_ok=True)
    for part, mm in MODELS.items():
        src = SPICE / "models" / mm["lib"]
        dst = dst_dir / Path(mm["lib"]).name
        dst.write_text(translate_model(src.read_text(encoding="latin-1")), encoding="latin-1")
    (dst_dir / "fet_cards.lib").write_text("* Linear Systems LSBF862 card (unchanged)\n" + LSBF862 + "\n",
                                          encoding="utf-8")


def header(part: str, title: str) -> str:
    mm = MODELS[part]
    return (f"* {title}\n.include ../../_models/{Path(mm['lib']).name}\n.temp 25\n"
            f"VCC vcc 0 DC {mm['vs']:g}\nVEE vee 0 DC {-mm['vs']:g}\n{mm.get('extra', '')}")


def amp(part: str, p: str, n: str, o: str, name: str = "XU1") -> str:
    return f"{name} " + MODELS[part]["inst"].format(p=p, n=n, o=o) + "\n"


def write_deck(folder: Path, text: str, name: str = "deck.cir") -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return path


def run(ng: NgSpice, deck: Path) -> list[str]:
    out = ng.run_deck(deck)
    with open(deck.with_suffix(".log"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(out)
    return [ln for ln in out.splitlines()
            if re.search(r"\berror\b|singular|timestep too small|no convergence|aborted", ln, re.I)]


def read_cols(path: Path) -> np.ndarray:
    return np.loadtxt(path, skiprows=1, ndmin=2)


CONTROL_AC = ("set wr_singlescale\nset wr_vecnames\n"
              "ac dec {ppd} {f1:g} {f2:g}\nwrdata {name} v(out)\n")
CONTROL_NOISE = ("set wr_singlescale\nset wr_vecnames\n"
                 "noise v(out) {src} dec {ppd} {f1:g} {f2:g}\nsetplot noise1\n"
                 "wrdata {name} inoise_spectrum onoise_spectrum\n")


# ---------------------------------------------------------------- metrics
def f3_peak(f: np.ndarray, z: np.ndarray) -> tuple[float, float]:
    mag = np.abs(z)
    ref = mag[0]
    below = np.nonzero(mag < ref / math.sqrt(2.0))[0]
    if below.size:
        i = below[0]
        x = np.interp(ref / math.sqrt(2.0), [mag[i], mag[i - 1]], [math.log10(f[i]), math.log10(f[i - 1])])
        f3 = 10 ** x
    else:
        f3 = float("nan")
    return float(f3), float(20 * math.log10(mag.max() / ref))


def band(f: np.ndarray, s: np.ndarray, lo: float, hi: float) -> float:
    """Integral of s over exactly [lo, hi], the end values interpolated in log f."""
    inside = (f > lo) & (f < hi)
    ends = np.interp(np.log10([lo, hi]), np.log10(f), s)
    return float(np.trapezoid(np.concatenate([[ends[0]], s[inside], [ends[1]]]),
                              np.concatenate([[lo], f[inside], [hi]])))


# ---------------------------------------------------------------- designs
def check_designs(ng: NgSpice) -> dict:
    sweep = json.loads((m.DATA / "results" / "designs.json").read_text())
    amps = m.load_amps()
    out = []
    for part in MODELS:
        for sname, (c_d, r_sh) in list(SOURCES.items())[:2]:
            for rf in (1e5, 1e6, 1e7, 1e8, 1e9):
                d0 = next(r for r in sweep if r["amp"] == part and r["rf"] == rf
                          and r["source"] == SWEEP_NAMES[sname])
                c_f = d0["cf_pF"] * 1e-12
                case = f"{part}_{sname}_{rf:.0e}"
                folder = RUNS / "designs" / case
                body = (header(part, case) + amp(part, "0", "inm", "out")
                        + f"RF out inm {rf:g}\nCF out inm {c_f:.6g}\nCD inm 0 {c_d + C_STRAY:.6g}\n"
                          f"RSH inm 0 {r_sh:g}\nIph 0 inm DC 0 AC 1\nRL out 0 10k\n")
                f1, f2 = 0.1, 1e8
                errs = run(ng, write_deck(folder, body + ".control\n"
                                          + CONTROL_AC.format(ppd=20, f1=f1, f2=f2, name="zt.txt")
                                          + ".endc\n.end\n", "ac.cir"))
                errs += run(ng, write_deck(folder, body + ".control\n"
                                           + CONTROL_NOISE.format(src="Iph", ppd=20, f1=f1, f2=f2, name="noise.txt")
                                           + ".endc\n.end\n", "noise.cir"))
                zt = read_cols(folder / "zt.txt")
                nz = read_cols(folder / "noise.txt")
                f = zt[:, 0]
                z = zt[:, 1] + 1j * zt[:, 2]
                fn, inoise = nz[:, 0], nz[:, 1]
                f3s, pks = f3_peak(f, z)
                d = m.Design(amps[part], rf, c_f, m.Source(sname, c_d, r_sh), c_stray=C_STRAY)
                za = d.zt(f)
                f3a, pka = f3_peak(f, za)
                na = d.noise(fn)
                floor = m.FOUR_KT / rf + m.FOUR_KT / r_sh
                dn_s = 10 * math.log10(band(fn, inoise ** 2, 1.0, f3s) / (floor * (f3s - 1.0)))
                dn_a = 10 * math.log10(band(fn, na["total"], 1.0, f3a) / (floor * (f3a - 1.0)))
                dn_a_sband = 10 * math.log10(band(fn, na["total"], 1.0, f3s) / (floor * (f3s - 1.0)))
                np.save(folder / "compare.npy", np.vstack([fn, inoise, np.sqrt(na["total"]),
                                                           np.abs(np.interp(np.log10(fn), np.log10(f), np.abs(z))),
                                                           np.abs(d.zt(fn))]))
                out.append(dict(part=part, source=sname, rf=rf, cf_pF=c_f * 1e12,
                                f3_spice=f3s, f3_model=f3a, peak_spice=pks, peak_model=pka,
                                dN_spice=dn_s, dN_model=dn_a, dN_model_spice_band=dn_a_sband,
                                zt0_spice=float(abs(z[0])), errors=errs[:3]))
                print(f"{case}: f3 {f3s:.4g}/{f3a:.4g} Hz, peak {pks:.2f}/{pka:.2f} dB, "
                      f"dN {dn_s:.2f}/{dn_a:.2f} dB{' ERR' if errs else ''}", flush=True)
    return {"designs": out}


# ---------------------------------------------------------------- models' own noise
DATASHEET_EN_IN = {
    "OPA928": ({100: 18, 1000: 15}, {0.1: 0.07}),
    "OPA140": ({10: 8, 100: 5.8, 1000: 5.1}, {1000: 0.8}),
    "OPA828": ({10: 7.5, 100: 4.8, 1000: 4.0}, {1000: 1.2}),
    "OPA320": ({1000: 8.5, 10000: 7}, {1000: 0.6}),
    "OPA818": ({1000: 8.4, 10000: 3.32, 150000: 2.2}, {10000: 3.0}),
    "OPA657": ({770: 6.4, 9500: 5.0, 100000: 4.8}, {100000: 1.3}),
    "ADA4817-1": ({1000: 11.8, 10000: 5.4, 100000: 4.0}, {100000: 2.5}),
}


def check_models(ng: NgSpice) -> dict:
    out = {}
    for part in MODELS:
        res = {}
        for label, r_s in (("en", 0.0), ("in_1e8", 1e8), ("in_1e10", 1e10)):
            folder = RUNS / "models" / f"{part}_{label}"
            src = (f"VS src 0 DC 0 AC 1\nRS src inp rq {r_s:g}\n.model rq r(noisy=0)\n" if r_s
                   else "VS inp 0 DC 0 AC 1\n")
            body = header(part, f"{part} {label}") + amp(part, "inp", "out", "out") + src + "RL out 0 10k\n"
            errs = run(ng, write_deck(folder, body + ".control\n"
                                      + CONTROL_NOISE.format(src="VS", ppd=10, f1=0.01, f2=1e7, name="noise.txt")
                                      + ".endc\n.end\n"))
            nz = read_cols(folder / "noise.txt")
            res[label] = dict(f=nz[:, 0].tolist(), inoise=nz[:, 1].tolist(), errors=errs[:3])
        f = np.array(res["en"]["f"])
        en = np.array(res["en"]["inoise"])
        for r_s, label in ((1e8, "in_1e8"), (1e10, "in_1e10")):
            tot = np.array(res[label]["inoise"])
            res[label]["in_A"] = (np.sqrt(np.clip(tot ** 2 - en ** 2, 0, None)) / r_s).tolist()
        out[part] = res
        e1k = float(np.interp(3.0, np.log10(f), en))
        i10 = float(np.interp(1.0, np.log10(f), np.array(res["in_1e8"]["in_A"])))
        print(f"{part}: e_n(1 kHz) = {e1k * 1e9:.3g} nV/rtHz, i_n(10 Hz, 100 MOhm) = {i10 * 1e15:.3g} fA/rtHz", flush=True)
    return {"models": out}


# ---------------------------------------------------------------- distributed resistor
N_SEC = 20
PROFILES = {
    "lumped (no plane)": None,
    "plane at ground": lambda x: 0.0,
    "plane at output": lambda x: 1.0,
    "plane at 1/3 output": lambda x: 1.0 / 3.0,
    "four strips, graded": lambda x: (min(int(x * 4), 3) + 0.5) / 4,
    "ideal graded guard": lambda x: x,
}


def ladder_text(rf: float, cee: float, cg: float, profile, n: int = N_SEC) -> str:
    """Feedback network between inm (x = 0) and out (x = 1) as an n-section ladder; the
    conductor under each node is driven by an ideal voltage-controlled source at
    profile(x) times the output voltage."""
    lines = [f"CEE out inm {cee:.6g}"]
    names = ["inm"] + [f"n{i}" for i in range(1, n)] + ["out"]
    for i in range(n):
        lines.append(f"RF{i} {names[i + 1]} {names[i]} {rf / n:.6g}")
    if profile is not None:
        drives = {}
        for i, node in enumerate(names):
            x = i / n
            a = round(float(profile(x)), 9)
            if a not in drives:
                drives[a] = f"pl{len(drives)}"
                if a == 0.0:
                    lines.append(f"V{drives[a]} {drives[a]} 0 DC 0")
                else:
                    lines.append(f"E{drives[a]} {drives[a]} 0 out 0 {a:.9g}")
            c = cg / n if 0 < i < n else cg / (2 * n)
            lines.append(f"CG{i} {node} {drives[a]} {c:.6g}")
    return "\n".join(lines) + "\n"


def check_distributed(ng: NgSpice) -> dict:
    amps = m.load_amps()
    out = []
    rf, cee, cg = 1e9, 0.05e-12, 0.3e-12
    c_d, r_sh = SOURCES["S1336-18BK"]
    for part in ("OPA140", "OPA928"):
        for label, prof in PROFILES.items():
            case = f"{part}_{label.replace(' ', '_').replace('/', '')}"
            folder = RUNS / "distributed" / case
            net = ladder_text(rf, cee, 0.0 if prof is None else cg, prof)
            base = (header(part, case) + amp(part, "0", "inm", "out") + net
                    + f"CD inm 0 {c_d + C_STRAY:.6g}\nRSH inm 0 {r_sh:g}\nRL out 0 10k\n")
            errs = run(ng, write_deck(folder, base + "Iph 0 inm DC 0 AC 1\n.control\n"
                                      + CONTROL_AC.format(ppd=40, f1=1.0, f2=1e6, name="zt.txt")
                                      + ".endc\n.end\n", "ac.cir"))
            errs += run(ng, write_deck(folder, base + "Iph 0 inm DC 0 AC 1\n.control\n"
                                       + CONTROL_NOISE.format(src="Iph", ppd=40, f1=1.0, f2=1e6, name="noise.txt")
                                       + ".endc\n.end\n", "noise.cir"))
            errs += run(ng, write_deck(folder, base + "Iph 0 inm PULSE(0 100p 0.5m 1u 1u 1 2)\n.control\n"
                                       "set wr_singlescale\nset wr_vecnames\ntran 1u 4m 0 1u\n"
                                       "wrdata step.txt v(out)\n.endc\n.end\n", "tran.cir"))
            zt = read_cols(folder / "zt.txt")
            f = zt[:, 0]
            z = zt[:, 1] + 1j * zt[:, 2]
            nz = read_cols(folder / "noise.txt")
            st = read_cols(folder / "step.txt")
            # analytic: ladder admittances with a single-pole amplifier
            w = 2 * math.pi * f
            if prof is None:
                y11, y21 = m.lumped_y(w, rf, cee)
                yf = -y21
            else:
                y11, yf = m.ladder_y(w, rf, cg, cee, 200, prof)
            a = amps[part]
            gain = a.a0 / (1 + 1j * w / (2 * math.pi * a.gbw / a.a0))
            y_s = 1 / r_sh + 1j * w * (c_d + C_STRAY + a.c_in)
            za = -1 / (yf + (y_s + y11) / gain)
            f3s, pks = f3_peak(f, z)
            f3a, pka = f3_peak(f, za)
            np.save(folder / "compare.npy", np.vstack([f, np.abs(z), np.abs(za), np.angle(z), np.angle(za)]))
            np.save(folder / "noise.npy", nz.T)
            np.save(folder / "step.npy", st.T)
            v = st[:, 1]
            t = st[:, 0]
            v0 = float(np.interp(0.45e-3, t, v))
            vend = float(v[-1])
            over = float((v.min() - vend) / (v0 - vend)) if vend < v0 else float((v.max() - vend) / (vend - v0))
            out.append(dict(part=part, profile=label, f3_spice=f3s, f3_model=f3a, peak_spice=pks, peak_model=pka,
                            step_overshoot=over, errors=errs[:3]))
            print(f"{case}: f3 {f3s:.4g}/{f3a:.4g} Hz, peak {pks:.2f}/{pka:.2f} dB, overshoot {100 * over:.1f}%"
                  f"{' ERR' if errs else ''}", flush=True)
    return {"distributed": out, "rf": rf, "cee": cee, "cg": cg}


# ---------------------------------------------------------------- composite front end
def composite_text(title: str, rf: float, c_f: float, c_d: float, r_sh: float, cc: float) -> str:
    """Cascoded LSBF862 (J1 common source, J2 cascode, gate at 2.5 V) with a 1-kOhm drain
    load at 15 V, followed by OPA140 as a non-inverting integrator stage whose + input
    senses the drain and whose - input sits at 5 V; R_F from the OPA140 output to J1's gate
    (the summing node).  The loop sets the drain at 5 V, so I_D = 10 mA and g_m R_D is
    about 33; cc across the OPA140 (from its output to its - input, through 1 kOhm to the
    5-V reference) sets the composite's gain-bandwidth."""
    # The second stage is an ideal integrator: 1 mS from (v_d - 5 V) into cc, with 1 GOhm across cc
    # for a DC gain of 10^6, buffered to the output.  With the macromodel of an op amp there, the DC
    # solver found latched states (J1 cut off, the op amp's input clamps conducting); the ideal stage
    # has one DC solution.  Its own noise is left out: an op amp's 5 nV/rtHz divided by the JFET
    # stage's g_m R_D of about 33 would add about 0.15 nV/rtHz to the JFET's 0.6 nV/rtHz.
    return (f"* {title}\n.include ../../_models/fet_cards.lib\n.temp 25\n"
            "VDD vdd 0 DC 15\nVB2 b2 0 DC 2.5\nVREF ref 0 DC 5\n"
            "J1 x inm 0 LSBF862\nJ2 d b2 x LSBF862\nRD vdd d 1k\n"
            f"G2 0 n2 d ref 1m\nCC n2 0 {cc:.6g}\nRCC n2 0 1G\nE3 out 0 n2 0 1\n"
            + f"RF out inm {rf:g}\nCF out inm {c_f:.6g}\nCD inm 0 {c_d + C_STRAY:.6g}\nRSH inm 0 {r_sh:g}\n"
              "RL out 0 10k\n"
              ".nodeset v(out)=-0.18 v(inm)=-0.18 v(d)=5 v(x)=2.68\n")


def check_composite(ng: NgSpice) -> dict:
    amps = m.load_amps()
    sweep = json.loads((m.DATA / "results" / "designs.json").read_text())
    out = []
    for sname in ("S1336-8BK", "G12180-050A"):
        c_d, r_sh = SOURCES[sname]
        for rf in (1e5, 1e6, 1e7):
            ref = next(r for r in sweep if r["amp"] == "OPA140" and r["rf"] == rf
                       and r["source"] == SWEEP_NAMES[sname])
            comp = next(r for r in sweep if r["amp"] == "BF862 composite" and r["rf"] == rf
                        and r["source"] == SWEEP_NAMES[sname])
            case = f"LSBF862_OPA140_{sname}_{rf:.0e}"
            folder = RUNS / "composite" / case
            # cc = 106 pF puts the integrator's unity gain at 1 mS / (2 pi 106 pF) = 1.5 MHz, so with
            # g_m R_D of about 33 the composite has about 50 MHz, the value assumed for the analytic
            # composites.  C_F starts at the analytic design's value and grows by 20% per step until
            # the response is within 0.1 dB of flat (the rule of Section 1.4).
            c_f = comp["cf_pF"] * 1e-12
            for _ in range(30):
                body = composite_text(case, rf, c_f, c_d, r_sh, cc=106e-12)
                errs = run(ng, write_deck(folder, body + "Iph 0 inm DC 0 AC 1\n.control\nop\nprint v(d) v(inm) "
                                          "v(out) i(VDD)\n" + CONTROL_AC.format(ppd=20, f1=0.1, f2=1e8,
                                                                                 name="zt.txt")
                                          + ".endc\n.end\n", "ac.cir"))
                zt = read_cols(folder / "zt.txt")
                if zt.shape[1] >= 3 and f3_peak(zt[:, 0], zt[:, 1] + 1j * zt[:, 2])[1] <= 0.1:
                    break
                c_f *= 1.2
            errs += run(ng, write_deck(folder, body + "Iph 0 inm DC 0 AC 1\n.control\n"
                                       + CONTROL_NOISE.format(src="Iph", ppd=20, f1=0.1, f2=1e8, name="noise.txt")
                                       + ".endc\n.end\n", "noise.cir"))
            zt = read_cols(folder / "zt.txt")
            f = zt[:, 0]
            z = zt[:, 1] + 1j * zt[:, 2]
            nz = read_cols(folder / "noise.txt")
            fn, inoise = nz[:, 0], nz[:, 1]
            f3s, pks = f3_peak(f, z)
            floor = m.FOUR_KT / rf + m.FOUR_KT / r_sh
            dn_s = 10 * math.log10(band(fn, inoise ** 2, 1.0, f3s) / (floor * (f3s - 1.0)))
            # OPA140 alone at its own design, from the designs check if present
            d_ref = m.Design(amps["OPA140"], rf, ref["cf_pF"] * 1e-12, m.Source(sname, c_d, r_sh), c_stray=C_STRAY)
            np.save(folder / "compare.npy", np.vstack([fn, inoise, np.sqrt(d_ref.noise(fn)["total"])]))
            out.append(dict(source=sname, rf=rf, cf_pF=c_f * 1e12, f3_spice=f3s, peak_spice=pks, dN_spice=dn_s,
                            dN_model_BF862=comp["dN_vs_detector_dB"], f3_model_BF862=comp["f3_Hz"],
                            dN_model_OPA140=ref["dN_vs_detector_dB"], f3_model_OPA140=ref["f3_Hz"],
                            errors=errs[:3]))
            print(f"{case}: f3 {f3s:.4g} Hz (BF862 model {comp['f3_Hz']:.4g}), peak {pks:.2f} dB, dN {dn_s:.2f} dB "
                  f"(BF862 model {comp['dN_vs_detector_dB']:.2f}, OPA140 alone {ref['dN_vs_detector_dB']:.2f})"
                  f"{' ERR' if errs else ''}", flush=True)
    return {"composite": out}


CHECKS = {"designs": check_designs, "models": check_models, "distributed": check_distributed,
          "composite": check_composite}


def main() -> None:
    """python hg_spice.py [check ...] [--parts PART,PART]: with --parts, the designs and
    models checks run only for those parts, and their results replace those parts' entries
    in the existing result files; the other entries are kept."""
    args = sys.argv[1:]
    parts = None
    if "--parts" in args:
        i = args.index("--parts")
        parts = args[i + 1].split(",")
        args = args[:i] + args[i + 2:]
    names = args or list(CHECKS)
    prepare_models()
    ng = NgSpice()
    RESULTS.mkdir(parents=True, exist_ok=True)
    for name in names:
        path = RESULTS / f"{name}.json"
        if parts and name in ("designs", "models"):
            saved = dict(MODELS)
            MODELS.clear()
            MODELS.update({p: saved[p] for p in parts})
            try:
                new = CHECKS[name](ng)
            finally:
                MODELS.clear()
                MODELS.update(saved)
            res = json.loads(path.read_text()) if path.exists() else {name: [] if name == "designs" else {}}
            if name == "designs":
                res["designs"] = [r for r in res["designs"] if r["part"] not in parts] + new["designs"]
            else:
                res["models"].update(new["models"])
        else:
            res = CHECKS[name](ng)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(res, fh, indent=1)
        print(f"== {name} written", flush=True)


if __name__ == "__main__":
    main()
