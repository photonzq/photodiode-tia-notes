"""SPICE cross-check of the survey's analytical model with the vendors' macromodels (ngspice).

Usage:  python spice_tia_checks.py <check> [--ngspice <library>] [--spice <spice folder>]
                                  [--parts <PART> ...]
        <check> = smoke | aol | params | referee | loop | zt | noise | step | tone |
                  bench | cfscan | pscan | consistency | all
        --parts runs the per-part checks for those parts only and merges the results into
        the existing results files (tone, bench and cfscan are skipped).

The vendor models are not part of this archive.  Download them from the product pages
and place the model files as listed in VENDOR_MODELS below, under <spice folder>/models
(default: ../spice relative to this script).  Decks are generated under
<spice folder>/runs/<check>/<case>/ with relative include paths, run through ngspice
loaded as a shared library (ngspice_shared.py), and summarized in
<spice folder>/results/<check>.json.  spice_report_tables.py turns those into the
tables of Section 10.  Run 'aol' and 'params' before 'referee', and 'loop', 'zt',
'noise' and 'params' before 'consistency'; 'all' runs them in a working order.

Checks (equation and section numbers refer to the survey):
  smoke  operating point and the models' own noise (e_n, i_n) in a unity-gain buffer.
  aol    open-loop gain and phase of each macromodel, driven at the non-inverting input
         and at the inverting input (Eq. (48)), against the digitized datasheet curve used
         by the analytical model (Section 2.5).
  referee  the datasheets' own closed-loop test circuits (Section 10.5, Eq. (53)).
  loop   loop gain of each TIA design by Middlebrook's double injection (Eqs. (44)-(46)):
         voltage and current injected in turn between the amplifier output and the
         feedback network; crossover, phase and gain margin, second crossings; nominal and
         the corners C_F +/- 0.1 pF, C_D +/- 0.2 pF.  Compared with the analytical model
         run with the datasheet curve.
  zt     transimpedance: bandwidth and peaking.
  noise  input-referred noise density (ngspice .noise referred to the photocurrent source)
         against Eq. (17), central and high estimates.
  step   small-signal step response: overshoot and rise time.
  tone   large-signal limits: output amplitude swept over 0.5-1.3 times Table 6.2b.
  params the macromodels' input admittance (Eq. (49)), open-loop output impedance
         (Eq. (50)), e_n, i_n and the capacitance their e_n drives (Eq. (51)).
  bench  the OPA846 bench board of Section 5.5 (needs 'params').
  cfscan total-C_F scans of variants A and B over the photodiode-capacitance corners:
         variant A's window and variant B's smallest stable C_F, each checked at its nine
         corners, with noise (Section 10.6).
  pscan  every part's widest-band robust design at 1 pF and 2 kOhm from a total-C_F scan
         over the photodiode-capacitance corners, with noise (Section 10.10).
  consistency  the analytical model run with the macromodels' own parameters (Eqs. (7),
         (8), (52)) against the SPICE results.
"""
import argparse
import json
import math
import re
from pathlib import Path

import numpy as np

import tia_model as tm
from ngspice_shared import NgSpice
from parts_db import PARTS
from run_analysis import C_PCB_NOM, noise_inputs, noise_models_for, open_loop_model

HERE = Path(__file__).resolve().parent
KT = tm.K_B * tm.T_ROOM

# model file per part (relative to <spice folder>/models), its pin order, and test conditions:
# supplies for the open-loop comparison (as on the datasheet curve) and for the TIA, and the
# load of the datasheet open-loop curve.
VENDOR_MODELS = {
    "OPA855": dict(lib="OPA855/opa855_a.lib", inst="{p} {n} {o} vcc vee OPA855", vs_aol=2.5, vs_tia=2.5,
                   rl=200.0, db="OPA855", source="TI SBOMB43D, OPA855 Unencrypted PSpice Model Package (Rev. D)"),
    "OPA818": dict(lib="OPA818/opa818.lib", inst="{p} {n} {o} vcc vee OPA818", vs_aol=5.0, vs_tia=6.5,
                   rl=100.0, db="OPA818", source="TI SBOMB74B, PSPICE Circuit Containing OPA818 Model (Rev. B)"),
    "OPA856": dict(lib="OPA856/opa856_a.lib", inst="{p} {n} vcc vee {o} OPA856", vs_aol=2.5, vs_tia=2.5,
                   rl=200.0, db="OPA856", source="TI SBOMBI1, OPA856 Unencrypted PSPICE Model Package"),
    "OPA858": dict(lib="OPA858/OPA858.lib", inst="{p} {n} vcc vee {o} OPA858", vs_aol=2.5, vs_tia=2.5,
                   rl=200.0, db="OPA858", source="TI SBOMBK7, OPA858 PSpice Model"),
    "LMH6629": dict(lib="LMH6629/LMH6629.MOD", inst="{p} {n} vcc vee {o} vcc LMH6629", vs_aol=2.5, vs_tia=2.5,
                    rl=100.0, db="LMH6629 (COMP HI)", source="TI SNOM133, LMH6629 PSPICE Model (COMP pin high)"),
    "OPA859": dict(lib="OPA859/OPA859.lib", inst="{p} {n} vcc vee {o} vcc OPA859", vs_aol=2.5, vs_tia=2.5,
                   rl=200.0, db="OPA859", source="TI SBOMBQ2, OPA859 PSpice Model (power-down pin high)"),
    "OPA846": dict(lib="OPA846/OPA846.LIB", inst="{p} {n} vcc vee {o} OPA846", vs_aol=5.0, vs_tia=5.0,
                   rl=100.0, db="OPA846", source="TI SBOC005C, OPA846 PSpice Model (Rev. C)"),
    # parts the survey found less suitable (Sections 4.2 and 4.7), for comparison; supplies and
    # loads as on the open-loop curve the survey digitized
    "OPA657": dict(lib="OPA657/OPA657.lib", inst="vee vcc {n} {p} {o} OPA657", vs_aol=5.0, vs_tia=5.0,
                   rl=100.0, db="OPA657", source="TI SBOM137, OPA657 PSpice Model (Rev. F)"),
    "OPA847": dict(lib="OPA847/OPA847_Model.sub", inst="{p} {n} vcc {o} vcc vee OPA847_Model", vs_aol=5.0,
                   vs_tia=5.0, rl=100.0, db="OPA847", source="TI SBOC037, OPA847 PSpice Model (Rev. A); disable pin at V+"),
    "LMH6624": dict(lib="LMH6624/LMH6624.MOD", inst="{p} {n} vcc vee {o} LMH6624", vs_aol=6.0, vs_tia=6.0,
                    rl=100.0, db="LMH6624", source="TI SNOM130, LMH6624 PSPICE Model"),
    "THS4021": dict(lib="THS4021/ths4021.lib", inst="{p} {n} vcc vee {o} THS4021", vs_aol=15.0, vs_tia=15.0,
                    rl=150.0, db="THS4021", source="TI SLOJ004, THS4021 PSpice Model (Rev. A)"),
    # ADI macromodels: FB pin to the output; PD tied to V+ where the datasheet says it must
    # not float (ADA4817-1), otherwise left open as on the datasheets (pulled up inside);
    # AD8099's compensation pin CC open (uncompensated, as the survey's open-loop curve)
    "ADA4817-1": dict(lib="ADA4817-1/ada4817.cir", inst="{p} {n} vcc vee {o} {o} vcc ADA4817", vs_aol=5.0,
                      vs_tia=5.0, rl=100.0, db="ADA4817-1", source="ADI ADA4817 SPICE Macro Model, Rev. 2.1 (2017)"),
    # these two stop every 'ac' sweep with "matrix is singular" (their 'noise' sweeps run):
    # a node without an AC path to ground; 1 Tohm from every node to ground cures it
    # (spice_diagnostics/adi_open_loop_probe.py)
    "AD8099": dict(lib="AD8099/ad8099.cir", inst="{p} {n} vcc vee {o} {o} npd ncc AD8099", vs_aol=5.0, vs_tia=5.0,
                   rl=1000.0, db="AD8099", options=".options rshunt=1e12\n",
                   source="ADI AD8099 SPICE Macro Model, Rev. 3.0 (2015)"),
    "ADA4899-1": dict(lib="ADA4899-1/ada4899.cir", inst="{p} {n} vcc vee {o} {o} npd ADA4899", vs_aol=5.0,
                      vs_tia=5.0, rl=100.0, db="ADA4899-1", options=".options rshunt=1e12\n",
                      source="ADI ADA4899 SPICE Macro Model, Rev. 3.0 (2015)"),
    "ADA4895-1": dict(lib="ADA4895-1/ADA4895.cir", inst="{p} {n} vcc vee {o} npd ADA4895", vs_aol=2.5, vs_tia=2.5,
                      rl=1000.0, db="ADA4895-1", source="ADI ADA4895 SPICE Macro Model, Rev. 2.1 (2016)"),
    # parts TI offers only as TINA-TI files; the netlists are extracted unchanged by
    # extract_tina_model.py (Section 10.10).  OPA817 and OPA814 are outside the survey's
    # analysis (Table 3e): db=None, so only the checks that need no datasheet curve run
    "OPA955": dict(lib="OPA955/OPA955_from_TINA.lib", inst="{p} {n} {o} vcc vee OPA955", vs_aol=2.5, vs_tia=2.5,
                   rl=200.0, db="OPA955", source="TI SLOM544, OPA955 TINA-TI SPICE model (netlist dated 2026-07-06)"),
    "OPA817": dict(lib="OPA817/OPA817_from_TINA.lib", inst="{p} {n} {o} vcc vee OPA817", vs_aol=5.0, vs_tia=5.0,
                   rl=100.0, db=None, source="TI SBOMCB7, OPA817 TINA-TI reference circuit (model Rev. A, 2022)"),
    "OPA814": dict(lib="OPA814/OPA814_from_TINA.lib", inst="{p} {n} {o} vcc vee OPA814", vs_aol=5.0, vs_tia=5.0,
                   rl=100.0, db=None, source="TI SBOMCE1, OPA814 TINA-TI reference design (model v1.1, 2023)"),
}
# datasheet values of the parts outside the survey's analysis, as in Table 3e
SPICE_ONLY = {
    "OPA817": dict(input="FET (JFET)", fet=True, iq_ma=23.5, en=4.5e-9, c_cm=2.9e-12, c_diff=0.1e-12),
    "OPA814": dict(input="FET (JFET)", fet=True, iq_ma=16.0, en=5.3e-9, c_cm=2.5e-12, c_diff=0.2e-12),
}


def datasheet(part):
    """The survey's datasheet record of a part, or the Table 3e values for a SPICE-only part."""
    db = VENDOR_MODELS[part]["db"]
    return PARTS[db] if db else SPICE_ONLY[part]


# checks that do not run per part; skipped when --parts selects a subset
PART_INDEPENDENT = ("tone", "bench", "cfscan")

# TIA designs: part, R_F, photodiode capacitance at the node, total C_F, label
DESIGNS = [
    ("OPA855", 2000.0, 1e-12, 0.25e-12, "A, 1 pF, 2 kOhm"),
    ("OPA855", 2000.0, 2e-12, 0.35e-12, "A, 2 pF, 2 kOhm"),
    ("OPA855", 1500.0, 1e-12, 0.27e-12, "A, 1 pF, 1.5 kOhm"),
    ("OPA855", 1500.0, 2e-12, 0.40e-12, "A, 2 pF, 1.5 kOhm"),
    ("OPA818", 2000.0, 1e-12, 0.55e-12, "B, 1 pF, 2 kOhm"),
    ("OPA818", 2000.0, 2e-12, 0.55e-12, "B, 2 pF, 2 kOhm"),
    ("OPA818", 1500.0, 1e-12, 0.55e-12, "B, 1 pF, 1.5 kOhm"),
    ("OPA818", 1500.0, 2e-12, 0.65e-12, "B, 2 pF, 1.5 kOhm"),
    ("OPA856", 2000.0, 1e-12, 0.55e-12, "Table 8.1, 2 kOhm"),
    ("LMH6629", 2000.0, 1e-12, 0.55e-12, "Table 8.1, 2 kOhm"),
    ("OPA858", 2000.0, 1e-12, 0.25e-12, "as OPA855, 2 kOhm"),
    ("OPA859", 2000.0, 1e-12, 0.54e-12, "flat design, 2 kOhm"),
    ("OPA846", 2000.0, 1e-12, 0.75e-12, "flat design, 2 kOhm"),
    # the survey's own choices at 1 pF and 2 kOhm: the flat design where one exists, otherwise
    # the C_F of largest phase margin (Section 4.7; none of these reaches 45 deg)
    ("OPA657", 2000.0, 1e-12, 0.99e-12, "flat design, 2 kOhm"),
    ("OPA847", 2000.0, 1e-12, 0.35e-12, "largest-PM design, 2 kOhm"),
    ("LMH6624", 2000.0, 1e-12, 1.17e-12, "largest-PM design, 2 kOhm"),
    ("THS4021", 2000.0, 1e-12, 0.66e-12, "largest-PM design, 2 kOhm"),
    # ADI parts: the survey's robust design (45 deg, <= 1 dB) where one exists without added
    # capacitance, else the flat design; AD8099 has none, so the parasitic C_F alone
    ("ADA4817-1", 2000.0, 1e-12, 0.82e-12, "robust design, 2 kOhm"),
    ("ADA4899-1", 2000.0, 1e-12, 1.28e-12, "robust design, 2 kOhm"),
    ("ADA4895-1", 2000.0, 1e-12, 1.31e-12, "flat design, 2 kOhm"),
    ("AD8099", 2000.0, 1e-12, 0.20e-12, "parasitic C_F only, 2 kOhm"),
    # OPA955: the survey reaches 45 deg only with 3 pF added at the node; without it, its
    # largest-PM design (38.8 deg in the survey)
    ("OPA955", 2000.0, 1e-12, 0.25e-12, "largest-PM design, 2 kOhm"),
]
# the datasheets' own closed-loop test circuits and what the datasheets state about them
REFEREE = {
    "OPA855": dict(rf=453.0, rg=75.0, rl=200.0, vs=2.5, pm=62.0, bw=None, peak=None,
                   stated="62 deg at noise gain 7 (p18)"),
    "OPA818": dict(rf=301.0, rg=50.5, rl=100.0, vs=5.0, pm=50.0, bw=765.0, peak=1.4,
                   stated="about 50 deg at noise gain 7 (p16); 765 MHz and 1.4 dB peaking (p5)"),
    "OPA858": dict(rf=453.0, rg=75.0, rl=200.0, vs=2.5, pm=55.0, bw=1200.0, peak=1.0,
                   stated="55 deg at noise gain 7 (p18); 1.2 GHz and < 1 dB peaking at G = 7 (p6)"),
    "OPA856": dict(rf=None, rg=None, rl=200.0, vs=2.5, pm=57.0, bw=None, peak=None,
                   stated="about 57 deg as a unity-gain buffer (p16)"),
    "LMH6629": dict(rf=249.0, rg=27.4, rl=100.0, vs=2.5, pm=None, bw=900.0, peak=0.0,
                    stated="900 MHz, no peaking at Av = +10, RL = 100 ohm, COMP high (p5)"),
    "OPA859": dict(rf=None, rg=None, rl=200.0, vs=2.5, pm=63.0, bw=1800.0, peak=None,
                   stated="about 63 deg as a unity-gain buffer (p18); 1.8 GHz at G = 1 (p6)"),
    "OPA846": dict(rf=300.0, rg=50.0, rl=100.0, vs=5.0, pm=None, bw=500.0, peak=3.1,
                   stated="500 MHz at G = +7, RG = 50 ohm (p3); +3.1 dB near 350 MHz, -3 dB at 499 MHz (p4 curve)"),
    # the further parts (Section 10.10); none of these datasheets states a phase margin.
    # Optional: rs in series with +IN, cf across R_F, extra netlist lines (compensation)
    "OPA657": dict(rf=453.0, rg=75.5, rl=100.0, vs=5.0, pm=None, bw=350.0, peak=7.0,
                   stated="350 MHz and 7 dB peaking at G = +7 (p5); RF/RG not printed, 453/75.5 ohm from the page header"),
    "OPA847": dict(rf=431.2, rg=39.2, rl=100.0, vs=5.0, pm=None, bw=600.0, peak=4.5,
                   stated="600 MHz and 4.5 dB peaking (7 dB max) at G = +12, RG = 39.2 ohm (p3, p10)"),
    "LMH6624": dict(rf=500.0, rg=55.6, rl=100.0, vs=6.0, pm=None, bw=None, peak=None,
                    stated="no table value at Av = +10; curve with RF = 500 ohm, RL not printed: about 215 MHz, +0.7 dB (p11 Fig 14)"),
    "THS4021": dict(rf=220.0, rg=24.4, rl=150.0, vs=15.0, pm=None, bw=290.0, peak=None,
                    stated="290 MHz at G = +10, +/-15 V (p6, SOIC); curve +1.6 dB (p10 Fig 5-1)"),
    "ADA4817-1": dict(rf=None, rg=None, rl=100.0, vs=5.0, pm=None, bw=1050.0, peak=None,
                      stated="1050 MHz at G = +1 (p3); curve +3.1 dB (p8 Fig 8)"),
    "AD8099": dict(rf=250.0, rg=250.0, rl=1000.0, vs=5.0, pm=None, bw=700.0, peak=3.1, rs=50.0, cf=1.5e-12,
                   extra="RCC ncc ncc1 50\nC1CC ncc ncc1 1.5p\nCCC ncc1 vee 4p\n",
                   stated="700 MHz and 3.1 dB peaking at G = +2 with the SOIC compensation network (p17 Table 4, Fig 61)"),
    "ADA4899-1": dict(rf=None, rg=None, rl=1000.0, vs=5.0, pm=None, bw=605.0, peak=None, rs=24.9,
                      stated="605 MHz at G = +1 with RS = 24.9 ohm, RL = 1 kohm (p14 Table 4); curve +0.8 dB (p6 Fig 5)"),
    "ADA4895-1": dict(rf=249.0, rg=27.7, rl=1000.0, vs=2.5, pm=None, bw=216.0, peak=None,
                      stated="216 MHz at G = +10, +/-2.5 V (p4 Table 3); curve +2.1 dB (p10 Fig 8)"),
    "OPA955": dict(rf=453.0, rg=75.5, rl=200.0, vs=2.5, pm=None, bw=2800.0, peak=1.3,
                   stated="2.8 GHz at G = +7, 100 mVpp (p5, advance information); curve 2.95 GHz with +1.3 dB, RF = 453 ohm (p7 Fig 6-1)"),
}
# the bench board of Section 5.5: OPA846, R_F = 1.2 kOhm, no external C_F (0.30 pF total
# assumed), measured |Z_T| = 1.45 kOhm and about 7 pA/rtHz at 50 MHz; total node capacitance
# C_T (photodiode, board and the amplifier's own input) to try
BENCH = dict(part="OPA846", R_F=1200.0, C_F=0.30e-12, C_T=(5.15e-12, 12e-12, 14e-12, 16e-12),
             zt_meas=1450.0, noise_meas_pA=7.0, f_meas=50e6)
SPOT_F = (1e6, 10e6, 50e6, 100e6, 150e6, 200e6)
TONE_F = (20e6, 50e6, 100e6, 150e6, 200e6)


def tag(part, R_F, C_D, C_F, extra=""):
    return f"{part}_R{R_F/1e3:g}k_D{C_D*1e12:g}p_F{C_F*1e12:.2f}p{extra}".replace(".", "p")


# a PSpice resistor model card with T_ABS anywhere in its parameter list (TI's newer models
# write 'RES ( TCE=0 T_ABS=-273.15)')
_RES_TABS = re.compile(r"^(\s*\.model\s+)(\S+)(\s+)res\s*\(([^)]*?)\bt_abs\s*=\s*([-+0-9.eE]+)([^)]*)\)", re.I | re.M)
_CAP_MODEL = re.compile(r"^(\s*\.model\s+\S+\s+)cap(\b)", re.I | re.M)


def translate_model(text):
    """Make a PSpice model read as intended by ngspice.  ngspice takes PSpice's T_ABS
    (absolute device temperature) as an offset from its nominal 27 C, so the models'
    'noiseless' resistors (T_ABS = -273.15 C) would still be noisy, at about 27 K.
    Those model cards become ngspice resistor models with noisy=0; resistors of any other
    T_ABS model keep their noise and get that temperature as an instance parameter."""
    other = {}

    def card(m):
        name, t = m.group(2), float(m.group(5))
        # the other parameters are kept; a zero TCE is dropped (no effect)
        rest = " ".join(re.sub(r"\btce\s*=\s*0+(\.0*)?\b", "", m.group(4) + " " + m.group(6), flags=re.I).split())
        if t <= -273.0:
            return f"{m.group(1)}{name}{m.group(3)}R ({rest + ' ' if rest else ''}noisy=0)"
        other[name.lower()] = t
        return f"{m.group(1)}{name}{m.group(3)}R ({rest})"

    text = _RES_TABS.sub(card, text)
    # PSpice's capacitor model type CAP is ngspice's C (same TC1/TC2 parameters); THS4021
    text = _CAP_MODEL.sub(r"\1C\2", text)
    if other:
        lines = text.splitlines()
        for i, ln in enumerate(lines):
            tok = ln.split()
            if len(tok) >= 5 and tok[0][:1].upper() == "R" and tok[3].lower() in other:
                lines[i] = ln + f" temp={other[tok[3].lower()]:g}"
        text = "\n".join(lines) + "\n"
    return text


def prepared_model(part, spice):
    """Translated copy of the vendor model under runs/_models/ (the original is not touched)."""
    src = spice / "models" / VENDOR_MODELS[part]["lib"]
    dst = spice / "runs" / "_models" / src.name
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(translate_model(src.read_text(encoding="latin-1")), encoding="latin-1")
    return dst


def header(part, title, vs):
    m = VENDOR_MODELS[part]
    lib = Path(m["lib"]).name
    return (f"* {title}\n.include ../../_models/{lib}\n.temp 25\n{m.get('options', '')}"
            f"VCC vcc 0 DC {vs}\nVEE vee 0 DC {-vs}\n")


def amp(part, p, n, o):
    return "XU1 " + VENDOR_MODELS[part]["inst"].format(p=p, n=n, o=o) + "\n"


def tia_body(part, R_F, C_ext, C_F, R_L, vinj_ac=0, iinj_ac=0, iph=None):
    """Inverting TIA: summing node inm, amplifier output oa, feedback side of the injection fb."""
    iph = iph or "Iph 0 inm DC 0 AC 0"
    return (amp(part, "0", "inm", "oa")
            + f"Vinj fb oa DC 0 AC {vinj_ac}\nIinj 0 fb DC 0 AC {iinj_ac}\n"
            + f"RF fb inm {R_F}\nCF fb inm {C_F}\nCX inm 0 {C_ext}\nRL oa 0 {R_L}\n{iph}\n")


def write_deck(folder, text):
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "deck.cir"
    path.write_text(text, encoding="utf-8")
    return path


def read_wrdata(path):
    data = np.loadtxt(path, skiprows=1, ndmin=2)
    return data


def band_integral(f, S, lo, hi):
    """Integral of S over exactly [lo, hi]: the grid points inside, and the end values interpolated
    in log f.  The noise sweeps (50 points per decade from 100 kHz) have no point at 150 MHz; the
    last below it is 144.5 MHz, and stopping there drops 3.9 % of a 10-150 MHz band."""
    inside = (f > lo) & (f < hi)
    ends = np.interp(np.log10([lo, hi]), np.log10(f), S)
    return float(np.trapezoid(np.concatenate([[ends[0]], S[inside], [ends[1]]]),
                              np.concatenate([[lo], f[inside], [hi]])))


def band_penalty(f, inn, R_F, lo=10e6, hi=150e6):
    """Band-integrated input noise over the Johnson noise of R_F, lo to hi, in dB."""
    return 10 * np.log10(band_integral(f, inn ** 2, lo, hi) / (4 * KT / R_F * (hi - lo)))


def run(ng, deck):
    out = ng.run_deck(deck)
    (deck.parent / "ngspice.log").write_text(out, encoding="utf-8")
    errors = [ln for ln in out.splitlines() if "error" in ln.lower() and "errors: 0" not in ln.lower()]
    return out, errors


class TableOpenLoop:
    """Open-loop model from a complex frequency response (log-frequency interpolation of
    magnitude in dB and unwrapped phase), with the interface of tia_model's models."""

    def __init__(self, f, A):
        self.lf = np.log10(f)
        self.mag = 20 * np.log10(np.abs(A))
        self.ph = np.unwrap(np.angle(A))

    def A(self, f):
        x = np.log10(np.atleast_1d(np.asarray(f, dtype=float)))
        m = np.interp(x, self.lf, self.mag)
        p = np.interp(x, self.lf, self.ph)
        out = 10 ** (m / 20) * np.exp(1j * p)
        return out if np.ndim(f) else out[0]


def loop_metrics_from_T(f, T):
    mag = np.abs(T)
    ph = np.degrees(np.unwrap(np.angle(T)))
    above = mag >= 1
    idx = np.where(above[:-1] & ~above[1:])[0]
    res = dict(f_c_MHz=None, pm_deg=None, gm_dB=None, second_crossing_MHz=None)
    if len(idx):
        i = idx[0]
        x = (0 - 20 * np.log10(mag[i])) / (20 * np.log10(mag[i + 1]) - 20 * np.log10(mag[i]))
        fc = 10 ** (np.log10(f[i]) + x * (np.log10(f[i + 1]) - np.log10(f[i])))
        res["f_c_MHz"] = fc / 1e6
        res["pm_deg"] = 180 + float(np.interp(np.log10(fc), np.log10(f), ph))
        later = np.where(~above[i + 1:-1] & above[i + 2:])[0]
        if len(later):
            res["second_crossing_MHz"] = float(f[i + 2 + later[0]] / 1e6)
        j = np.where((ph[i:-1] > -180) & (ph[i + 1:] <= -180))[0]
        if len(j):
            k = i + j[0]
            res["gm_dB"] = float(-20 * np.log10(np.interp(-180, [ph[k + 1], ph[k]], [mag[k + 1], mag[k]])))
    return res


def zt_metrics(f, Z):
    mag = np.abs(Z)
    z0 = mag[0]
    below = np.where(mag < z0 / math.sqrt(2))[0]
    f3 = None
    if len(below):
        i = below[0]
        f3 = float(10 ** np.interp(z0 / math.sqrt(2), [mag[i], mag[i - 1]], [np.log10(f[i]), np.log10(f[i - 1])]))
    k = int(np.argmax(mag))
    return dict(z_lf_ohm=float(z0), f3_MHz=None if f3 is None else f3 / 1e6,
                peak_dB=float(max(0.0, 20 * np.log10(mag[k] / z0))), f_peak_MHz=float(f[k] / 1e6))


def analytical(part, R_F, C_D, C_F, ol=None):
    p = PARTS[VENDOR_MODELS[part]["db"]]
    if ol is None:
        ol, *_ = open_loop_model(p)
    C_T = C_D + C_PCB_NOM + p["c_cm"] + p["c_diff"]
    m = tm.loop_metrics(ol, R_F, C_T, C_F)
    return dict(C_T_pF=C_T * 1e12, f_c_MHz=m.get("f_c", np.nan) / 1e6 if m.get("f_c") else None,
                pm_deg=m["pm_deg"], gm_dB=m["gm_dB"], f3_MHz=m["f_3dB"] / 1e6, peak_dB=max(0.0, m["peaking_dB"]),
                stable=bool(m["stable"]))


# ---------------------------------------------------------------- checks

def check_smoke(ng, spice):
    """Unity-gain buffer with the non-inverting input at AC ground: the output noise is e_n
    (plus i_n times ~0 ohm); with 1 kOhm in series with IN+, the excess is i_n * 1 kOhm."""
    res = {}
    for part, m in VENDOR_MODELS.items():
        out = {}
        for rs in (0.001, 1000.0):
            folder = spice / "runs" / "smoke" / f"{part}_Rs{rs:g}".replace(".", "p")
            deck = header(part, f"{part} buffer noise, Rs = {rs} ohm", m["vs_aol"]) + amp(part, "inp", "out", "out") + (
                f"Vs src 0 DC 0 AC 1\nRS src inp {rs}\nRL out 0 {m['rl']}\n.model rnl r(noisy=0)\n"
                ".control\nset wr_singlescale\nset wr_vecnames\nop\nprint v(out) i(vcc) i(vee)\n"
                "noise v(out) Vs dec 10 1k 1G\nsetplot noise1\nwrdata noise.txt onoise_spectrum\n.endc\n.end\n")
            if rs > 1:
                deck = deck.replace(f"RS src inp {rs}", f"RS src inp rnl {rs}")
            log, err = run(ng, write_deck(folder, deck))
            d = read_wrdata(folder / "noise.txt")
            f, on = d[:, 0], d[:, 1]
            out[f"Rs{rs:g}"] = dict(errors=err[:5], onoise_nV={f"{x/1e6:g}MHz": float(np.interp(np.log10(x), np.log10(f), on) * 1e9)
                                                              for x in (1e4, 1e6, 10e6, 100e6)})
            for ln in log.splitlines():
                if "v(out) =" in ln or "i(vcc) =" in ln:
                    out.setdefault("op", []).append(ln.strip())
        e = np.array([out["Rs0.001"]["onoise_nV"][k] for k in ("1MHz", "10MHz", "100MHz")])
        r = np.array([out["Rs1000"]["onoise_nV"][k] for k in ("1MHz", "10MHz", "100MHz")])
        out["e_n_nV"] = list(e)
        out["i_n_pA_from_1k"] = list(np.sqrt(np.maximum(r ** 2 - e ** 2, 0)) / 1e3 * 1e3)   # nV / 1 kOhm -> pA
        res[part] = out
        print(f"{part}: e_n {e.round(3)} nV/rtHz at 1/10/100 MHz; i_n (from 1 kOhm) "
              f"{np.round(out['i_n_pA_from_1k'], 2)} pA/rtHz; op {out.get('op', [])[:2]}; errors {out['Rs0.001']['errors'][:2]}")
    return res


def check_aol(ng, spice):
    res = {}
    for part, m in VENDOR_MODELS.items():
        folder = spice / "runs" / "aol" / part
        deck = header(part, f"{part} open-loop gain", m["vs_aol"]) + amp(part, "inp", "inm", "out") + (
            f"Vp inp 0 DC 0 AC 1\nLB out inm 1G\nCB inm 0 1k\nRL out 0 {m['rl']}\n"
            ".control\nset wr_singlescale\nset wr_vecnames\nac dec 50 10k 30G\n"
            "wrdata aol.txt real(v(out)) imag(v(out)) real(v(inm)) imag(v(inm))\n.endc\n.end\n")
        log, err = run(ng, write_deck(folder, deck))
        d = read_wrdata(folder / "aol.txt")
        f = d[:, 0]
        A = (d[:, 1] + 1j * d[:, 2]) / (1 - (d[:, 3] + 1j * d[:, 4]))
        np.save(folder / "aol.npy", np.vstack([f, A.real, A.imag]))
        # the same gain driven at the inverting input (non-inverting input grounded), as in
        # the TIA; moderate DC-feed elements, the gain from the simulated pin voltage
        folder_i = spice / "runs" / "aol" / f"{part}_inverting"
        deck = header(part, f"{part} open-loop gain from the inverting input", m["vs_aol"]) + amp(part, "0", "inm", "out") + (
            f"Vn x 0 DC 0 AC 1\nCB inm x 1u\nLB out inm 1m\nRL out 0 {m['rl']}\n"
            ".control\nset wr_singlescale\nset wr_vecnames\nac dec 50 100k 30G\n"
            "wrdata aol.txt real(v(out)) imag(v(out)) real(v(inm)) imag(v(inm))\n.endc\n.end\n")
        log_i, err_i = run(ng, write_deck(folder_i, deck))
        err += err_i
        d = read_wrdata(folder_i / "aol.txt")
        A_inv = -(d[:, 1] + 1j * d[:, 2]) / (d[:, 3] + 1j * d[:, 4])
        np.save(folder / "aol_inverting.npy", np.vstack([d[:, 0], A_inv.real, A_inv.imag]))
        ol = open_loop_model(PARTS[m["db"]])[0] if m["db"] else None   # no survey curve for SPICE-only parts
        rows = {}
        ol_inv = TableOpenLoop(d[:, 0], A_inv)
        for x in (1e5, 1e6, 1e7, 1e8, 3e8, 1e9, 2e9, 3e9, 5e9, 7e9, 1e10):
            As = complex(np.interp(np.log10(x), np.log10(f), A.real), np.interp(np.log10(x), np.log10(f), A.imag))
            ph_s = float(np.interp(np.log10(x), np.log10(f), np.degrees(np.unwrap(np.angle(A)))))
            Ad = complex(ol.A(np.array([x]))[0]) if ol else None
            A_in = complex(ol_inv.A(np.array([x]))[0])
            rows[f"{x/1e6:g}MHz"] = dict(spice_dB=20 * math.log10(abs(As)), spice_deg=ph_s,
                                         datasheet_dB=20 * math.log10(abs(Ad)) if Ad else None,
                                         datasheet_deg=math.degrees(np.angle(Ad)) if Ad else None,
                                         inverting_dB=20 * math.log10(abs(A_in)), inverting_deg=math.degrees(np.angle(A_in)))
        ugf = f[np.where(np.abs(A) < 1)[0][0]] if np.any(np.abs(A) < 1) else None
        res[part] = dict(errors=err[:5], rows=rows, unity_gain_MHz=None if ugf is None else float(ugf / 1e6))
        print(f"{part}: unity-gain {res[part]['unity_gain_MHz']} MHz; errors {err[:2]}")
        for k, v in rows.items():
            ds = (f"{v['datasheet_dB']:6.1f} dB {v['datasheet_deg']:7.1f} deg" if v["datasheet_dB"] is not None
                  else "none in the survey")
            print(f"   {k:>8}: SPICE {v['spice_dB']:6.1f} dB {v['spice_deg']:7.1f} deg | datasheet curve {ds} | "
                  f"SPICE from IN- {v['inverting_dB']:6.1f} dB {v['inverting_deg']:7.1f} deg")
    return res


def _pm_resistive(ol, ng_gain):
    """Phase margin of a resistive stage of noise gain ng_gain: 180 deg + angle(A) where |A| = ng_gain."""
    f = np.logspace(5, 10.4, 6000)
    A = ol.A(f)
    mag = np.abs(A)
    ph = np.degrees(np.unwrap(np.angle(A)))
    i = np.where((mag[:-1] >= ng_gain) & (mag[1:] < ng_gain))[0]
    if not len(i):
        return None, None
    i = i[0]
    fx = float(10 ** np.interp(np.log10(ng_gain), [np.log10(mag[i + 1]), np.log10(mag[i])],
                               [np.log10(f[i + 1]), np.log10(f[i])]))
    return fx / 1e6, 180 + float(np.interp(np.log10(fx), np.log10(f), ph))


def _closed_loop(f, A_fwd, A_loop, rf, rg, c_in, rl=None, Zo=None):
    """Non-inverting stage R_F/R_G with c_in from the inverting input to ground (Eq. (53)):
    beta = Z_G/(Z_G + R_F), Z_G = R_G || 1/(s c_in); T = A_loop beta, G = A_fwd/(1 + T).
    A buffer has rf = None (beta = 1).  With rl and Zo, A is corrected from the load R_L of
    the open-loop measurement to R_L in parallel with the feedback network, as in Eq. (52)."""
    s = 2j * np.pi * f
    if rf:
        Zg = rg / (1 + s * rg * c_in)
        beta = Zg / (Zg + rf)
        Zfb = rf + Zg
    else:
        beta, Zfb = np.ones_like(s), None
    if Zo is not None and Zfb is not None:
        ZL = 1 / (1 / rl + 1 / Zfb)
        k = (rl + Zo) / rl * ZL / (ZL + Zo)
        A_fwd, A_loop = A_fwd * k, A_loop * k
    T = A_loop * beta
    lm, zm = loop_metrics_from_T(f, T), zt_metrics(f, A_fwd / (1 + T))
    return dict(pm_deg=lm["pm_deg"], f_c_MHz=lm["f_c_MHz"], f3_MHz=zm["f3_MHz"], peak_dB=zm["peak_dB"])


def check_referee(ng, spice):
    """The datasheets' own closed-loop circuits: closed-loop bandwidth and peaking, and the
    loop gain by Middlebrook's double injection, against the datasheet statements and the
    resistive-stage phase margin of each open-loop description.  The same circuit is also
    evaluated analytically: (a) with the datasheet curve and no input capacitance, as in
    Table 4.1; (b) with the datasheet curve and the datasheet's C_CM + C_DIFF; (c) with the
    macromodel's own parameters (requires 'aol' and 'params'), which must reproduce SPICE."""
    res = {}
    for part, r in REFEREE.items():
        m = VENDOR_MODELS[part]
        folder = spice / "runs" / "referee" / part
        fb = (f"RF fb inm {r['rf']}\nRG inm 0 {r['rg']}\n" if r["rf"] else "RF fb inm 0.001\n")
        if r.get("cf"):
            fb += f"CFB fb inm {r['cf']}\n"
        src = f"Vp src 0 DC 0 AC 1\nRS src inp {r['rs']}\n" if r.get("rs") else "Vp inp 0 DC 0 AC 1\n"
        deck = header(part, f"{part} datasheet test circuit", r["vs"]) + amp(part, "inp", "inm", "oa") + (
            f"{src}Vinj fb oa DC 0 AC 0\nIinj 0 fb DC 0 AC 0\n{fb}RL oa 0 {r['rl']}\n{r.get('extra', '')}"
            ".control\nset wr_singlescale\nset wr_vecnames\nac dec 100 100k 30G\n"
            "wrdata cl.txt real(v(oa)) imag(v(oa))\n"
            "alter @vp[acmag] = 0\nalter @vinj[acmag] = 1\nac dec 100 100k 30G\n"
            "wrdata vinj.txt real(v(oa)) imag(v(oa)) real(v(fb)) imag(v(fb))\n"
            "alter @vinj[acmag] = 0\nalter @iinj[acmag] = 1\nac dec 100 100k 30G\n"
            "wrdata iinj.txt real(i(vinj)) imag(i(vinj))\n.endc\n.end\n")
        log, err = run(ng, write_deck(folder, deck))
        cl = read_wrdata(folder / "cl.txt")
        v = read_wrdata(folder / "vinj.txt")
        c = read_wrdata(folder / "iinj.txt")
        f = cl[:, 0]
        G = cl[:, 1] + 1j * cl[:, 2]
        Tv = -(v[:, 1] + 1j * v[:, 2]) / (v[:, 3] + 1j * v[:, 4])
        iv = c[:, 1] + 1j * c[:, 2]
        T = (Tv * (iv / (1 - iv)) - 1) / (Tv + iv / (1 - iv) + 2)
        cm = zt_metrics(f, G)
        lm = loop_metrics_from_T(f, T)
        ng_gain = 1 + r["rf"] / r["rg"] if r["rf"] else 1.0
        ol_ds, *_ = open_loop_model(PARTS[m["db"]])
        a = np.load(spice / "runs" / "aol" / part / "aol.npy")
        ol_sp = TableOpenLoop(a[0], a[1] + 1j * a[2])
        res[part] = dict(stated=r["stated"], spice_closed_loop=cm, spice_loop=lm,
                         resistive_pm_datasheet_curve=_pm_resistive(ol_ds, ng_gain),
                         resistive_pm_macromodel_curve=_pm_resistive(ol_sp, ng_gain), errors=err[:3])
        p = PARTS[m["db"]]
        A_ds = ol_ds.A(f)
        if r.get("cf") or r.get("extra"):
            # an externally compensated circuit: the open-loop curves describe the uncompensated
            # amplifier, so Eq. (53) does not apply; only the SPICE circuit is reported
            print(f"{part}: compensated test circuit, SPICE only: f3 {cm['f3_MHz'] and round(cm['f3_MHz'])} MHz, "
                  f"peak {cm['peak_dB']:.2f} dB, PM {lm['pm_deg'] and round(lm['pm_deg'], 1)} | stated {r['stated']}")
            continue
        res[part]["analytical_datasheet_no_cin"] = _closed_loop(f, A_ds, A_ds, r["rf"], r["rg"], 0.0)
        res[part]["analytical_datasheet_with_cin"] = _closed_loop(f, A_ds, A_ds, r["rf"], r["rg"], p["c_cm"] + p["c_diff"])
        pfile = spice / "runs" / "params" / f"{part}_yin_grounded.npy"
        if pfile.exists():
            a_inv = np.load(spice / "runs" / "aol" / part / "aol_inverting.npy")
            zo = np.load(spice / "runs" / "params" / f"{part}_zout.npy")
            yi = np.load(pfile)
            on = lambda z: np.interp(np.log10(f), np.log10(z[0]), z[1]) + 1j * np.interp(np.log10(f), np.log10(z[0]), z[2])
            c_model = float(np.interp(8.0, np.log10(yi[0]), yi[2] / (2 * np.pi * yi[0])))
            res[part]["macromodel_parameters"] = _closed_loop(f, ol_sp.A(f), on(a_inv), r["rf"], r["rg"], c_model,
                                                              rl=r["rl"], Zo=on(zo))
        rd, rs = res[part]["resistive_pm_datasheet_curve"], res[part]["resistive_pm_macromodel_curve"]
        print(f"{part} (noise gain {ng_gain:.2f}): stated {r['stated']} | SPICE circuit: f3 "
              f"{cm['f3_MHz'] and round(cm['f3_MHz'])} MHz, peak {cm['peak_dB']:.2f} dB, PM {lm['pm_deg'] and round(lm['pm_deg'],1)} "
              f"at {lm['f_c_MHz'] and round(lm['f_c_MHz'])} MHz | from curves: datasheet {rd[1] and round(rd[1],1)} deg at "
              f"{rd[0] and round(rd[0])} MHz, macromodel {rs[1] and round(rs[1],1)} deg at {rs[0] and round(rs[0])} MHz | errors {err[:1]}")
        for k in ("analytical_datasheet_no_cin", "analytical_datasheet_with_cin", "macromodel_parameters"):
            if k in res[part]:
                v = res[part][k]
                print(f"      {k}: f3 {v['f3_MHz'] and round(v['f3_MHz'])} MHz, peak {v['peak_dB']:.2f} dB, "
                      f"PM {v['pm_deg'] and round(v['pm_deg'], 1)} at {v['f_c_MHz'] and round(v['f_c_MHz'])} MHz")
    return res


def check_loop(ng, spice):
    res = {}
    for part, R_F, C_D, C_F, label in DESIGNS:
        m = VENDOR_MODELS[part]
        aol_file = spice / "runs" / "aol" / part / "aol.npy"
        ol_spice = TableOpenLoop(*(lambda a: (a[0], a[1] + 1j * a[2]))(np.load(aol_file))) if aol_file.exists() else None
        corners = {}
        for dcf in (-0.1e-12, 0.0, 0.1e-12):
            for dcd in (-0.2e-12, 0.0, 0.2e-12):
                cf, cd = C_F + dcf, C_D + dcd
                folder = spice / "runs" / "loop" / tag(part, R_F, cd, cf)
                deck = header(part, f"{part} TIA loop gain, {label}", m["vs_tia"]) + tia_body(
                    part, R_F, cd + C_PCB_NOM, cf, m["rl"], vinj_ac=1, iinj_ac=0) + (
                    ".control\nset wr_singlescale\nset wr_vecnames\nac dec 100 100k 30G\n"
                    "wrdata vinj.txt real(v(oa)) imag(v(oa)) real(v(fb)) imag(v(fb))\n"
                    "alter @vinj[acmag] = 0\nalter @iinj[acmag] = 1\nac dec 100 100k 30G\n"
                    "wrdata iinj.txt real(i(vinj)) imag(i(vinj))\n.endc\n.end\n")
                log, err = run(ng, write_deck(folder, deck))
                v = read_wrdata(folder / "vinj.txt")
                c = read_wrdata(folder / "iinj.txt")
                f = v[:, 0]
                Tv = -(v[:, 1] + 1j * v[:, 2]) / (v[:, 3] + 1j * v[:, 4])
                iv = c[:, 1] + 1j * c[:, 2]
                Ti = iv / (1 - iv)
                T = (Tv * Ti - 1) / (Tv + Ti + 2)
                np.save(folder / "loop.npy", np.vstack([f, T.real, T.imag, Tv.real, Tv.imag]))
                met = loop_metrics_from_T(f, T)
                met_v = loop_metrics_from_T(f, Tv)
                key = f"dCF{dcf*1e12:+.1f}_dCD{dcd*1e12:+.1f}"
                corners[key] = dict(spice=met, spice_voltage_injection_only=met_v, errors=err[:3],
                                    analytical_datasheet=analytical(part, R_F, cd, cf),
                                    analytical_spice_aol=None if ol_spice is None else analytical(part, R_F, cd, cf, ol_spice))
        nom = corners["dCF+0.0_dCD+0.0"]
        pms = [c["spice"]["pm_deg"] for c in corners.values() if c["spice"]["pm_deg"] is not None]
        res[f"{part}|{label}"] = dict(part=part, R_F=R_F, C_D_pF=C_D * 1e12, C_F_pF=C_F * 1e12, corners=corners,
                                      spice_worst_pm=min(pms) if pms else None,
                                      second_crossings=[k for k, c in corners.items() if c["spice"]["second_crossing_MHz"]])
        a, s, sa = nom["analytical_datasheet"], nom["spice"], nom["analytical_spice_aol"]
        print(f"{part} {label}: SPICE f_c {s['f_c_MHz'] and round(s['f_c_MHz'])} MHz, PM {s['pm_deg'] and round(s['pm_deg'],1)}, "
              f"GM {s['gm_dB'] and round(s['gm_dB'],1)} dB | worst PM over C corners {res[f'{part}|{label}']['spice_worst_pm'] and round(res[f'{part}|{label}']['spice_worst_pm'],1)} | "
              f"analytical (datasheet curve) PM {a['pm_deg']:.1f} | analytical (macromodel curve) PM "
              f"{sa and round(sa['pm_deg'],1)} | voltage injection only PM {nom['spice_voltage_injection_only']['pm_deg'] and round(nom['spice_voltage_injection_only']['pm_deg'],1)}"
              f" | 2nd crossings {res[f'{part}|{label}']['second_crossings']}")
    return res


def check_zt(ng, spice):
    res = {}
    for part, R_F, C_D, C_F, label in DESIGNS:
        m = VENDOR_MODELS[part]
        folder = spice / "runs" / "zt" / tag(part, R_F, C_D, C_F)
        deck = header(part, f"{part} TIA transimpedance, {label}", m["vs_tia"]) + tia_body(
            part, R_F, C_D + C_PCB_NOM, C_F, m["rl"], iph="Iph 0 inm DC 0 AC 1") + (
            ".control\nset wr_singlescale\nset wr_vecnames\nac dec 100 100k 10G\n"
            "wrdata zt.txt real(v(oa)) imag(v(oa))\n.endc\n.end\n")
        log, err = run(ng, write_deck(folder, deck))
        d = read_wrdata(folder / "zt.txt")
        Z = d[:, 1] + 1j * d[:, 2]
        np.save(folder / "zt.npy", np.vstack([d[:, 0], Z.real, Z.imag]))
        met = zt_metrics(d[:, 0], Z)
        a = analytical(part, R_F, C_D, C_F)
        res[f"{part}|{label}"] = dict(spice=met, analytical=dict(f3_MHz=a["f3_MHz"], peak_dB=a["peak_dB"]), errors=err[:3])
        print(f"{part} {label}: SPICE f3 {met['f3_MHz'] and round(met['f3_MHz'])} MHz, peak {met['peak_dB']:.2f} dB at "
              f"{met['f_peak_MHz']:.0f} MHz | analytical f3 {a['f3_MHz']:.0f} MHz, peak {a['peak_dB']:.2f} dB | errors {err[:1]}")
    return res


def check_noise(ng, spice):
    res = {}
    for part, R_F, C_D, C_F, label in DESIGNS:
        m = VENDOR_MODELS[part]
        folder = spice / "runs" / "noise" / tag(part, R_F, C_D, C_F)
        deck = header(part, f"{part} TIA noise, {label}", m["vs_tia"]) + tia_body(
            part, R_F, C_D + C_PCB_NOM, C_F, m["rl"]) + (
            ".control\nset wr_singlescale\nset wr_vecnames\nnoise v(oa) Iph dec 50 100k 1G\n"
            "setplot noise1\nwrdata noise.txt inoise_spectrum onoise_spectrum\n.endc\n.end\n")
        log, err = run(ng, write_deck(folder, deck))
        d = read_wrdata(folder / "noise.txt")
        f, inn = d[:, 0], d[:, 1]
        p = PARTS[m["db"]]
        nz = noise_inputs(p)
        C_T = C_D + C_PCB_NOM + p["c_cm"] + p["c_diff"]
        spot = {}
        for x in SPOT_F:
            row = dict(spice_pA=float(np.interp(np.log10(x), np.log10(f), inn) * 1e12))
            for fm in ["central"] + (["high"] if "high" in noise_models_for(p) else []):
                c = tm.noise_components(np.array([x]), R_F, C_T, C_F, nz, fet_model=fm)
                row[f"analytical_{fm}_pA"] = float(np.sqrt(c["total"][0]) * 1e12)
            spot[f"{x/1e6:g}MHz"] = row
        pen = band_penalty(f, inn, R_F)
        res[f"{part}|{label}"] = dict(spot=spot, spice_penalty_10_150_dB=float(pen), errors=err[:3])
        print(f"{part} {label}: " + "; ".join(
            f"{k} {v['spice_pA']:.2f} (model {v['analytical_central_pA']:.2f}"
            + (f"/{v['analytical_high_pA']:.2f}" if "analytical_high_pA" in v else "") + ")"
            for k, v in spot.items()) + f" pA/rtHz | penalty {pen:.2f} dB")
    return res


def check_step(ng, spice):
    res = {}
    for part, R_F, C_D, C_F, label in DESIGNS:
        m = VENDOR_MODELS[part]
        folder = spice / "runs" / "step" / tag(part, R_F, C_D, C_F)
        deck = header(part, f"{part} TIA small-signal step, {label}", m["vs_tia"]) + tia_body(
            part, R_F, C_D + C_PCB_NOM, C_F, m["rl"], iph="Iph 0 inm PULSE(0 10u 2n 20p 20p 30n 60n)") + (
            ".control\nset wr_singlescale\nset wr_vecnames\ntran 1p 32n 0 2p\nlinearize v(oa)\n"
            "wrdata step.txt v(oa)\n.endc\n.end\n")
        log, err = run(ng, write_deck(folder, deck))
        d = read_wrdata(folder / "step.txt")
        t, v = d[:, 0], -d[:, 1]
        v0 = float(np.mean(v[t < 1.9e-9]))
        vf = float(np.mean(v[(t > 25e-9) & (t < 31.5e-9)]))
        step = vf - v0
        after = t > 2e-9
        over = float((np.max(v[after]) - vf) / step * 100)
        i10 = np.where(after & (v - v0 >= 0.1 * step))[0][0]
        i90 = np.where(after & (v - v0 >= 0.9 * step))[0][0]
        res[f"{part}|{label}"] = dict(step_mV=step * 1e3, overshoot_pct=over, rise_10_90_ps=float((t[i90] - t[i10]) * 1e12),
                                      errors=err[:3])
        print(f"{part} {label}: step {step*1e3:.2f} mV, overshoot {over:.1f} %, 10-90 % rise {(t[i90]-t[i10])*1e12:.0f} ps")
    return res


def _vpk_claim(part, f0, R_F):
    p = PARTS[VENDOR_MODELS[part]["db"]]
    s = p["dr"]
    vol, voh = s["swing_light"]
    return min((voh - vol) / 2, s["sr"] * 1e6 / (2 * math.pi * f0))


TONE_FRACTIONS = np.round(np.arange(0.5, 1.301, 0.05), 2)


def _crossing(x, y, level):
    """First x at which y rises through level (linear interpolation), or None."""
    i = np.where((y[:-1] < level) & (y[1:] >= level))[0]
    if not len(i):
        return None
    i = i[0]
    return float(x[i] + (level - y[i]) * (x[i + 1] - x[i]) / (y[i + 1] - y[i]))


def check_tone(ng, spice):
    """Large-signal limits: a sine photocurrent at 20-200 MHz whose output amplitude is swept
    from 0.5 to 1.3 times the amplitude of Table 6.2b (Eq. (24): the smaller of half the
    output range and SR/(2 pi f)).  The output is read over the last 32 of 48 periods
    (256 points per period, Hann window); harmonics 2-5 give THD.  The macromodels limit
    swing and slew rate hard and are otherwise nearly linear (about -140 dBc at 0.1 x), so
    the check locates the limits, not the small-signal distortion of the real part."""
    res = {}
    zt_root = spice / "runs" / "zt"
    for part, R_F, C_D, C_F, label in DESIGNS:
        if part not in ("OPA855", "OPA818") or C_D != 1e-12 or R_F != 2000.0:
            continue
        m = VENDOR_MODELS[part]
        zt = np.load(zt_root / tag(part, R_F, C_D, C_F) / "zt.npy")
        rows = {}
        for f0 in TONE_F:
            zmag = float(np.interp(np.log10(f0), np.log10(zt[0]), np.abs(zt[1] + 1j * zt[2])))
            claim = _vpk_claim(part, f0, R_F)
            sweep = []
            for frac in TONE_FRACTIONS:
                ipk = frac * claim / zmag
                folder = spice / "runs" / "tone" / tag(part, R_F, C_D, C_F, f"_f{f0/1e6:g}M_a{frac:g}")
                period = 1 / f0
                tstep = period / 256
                tstop = 48 * period
                deck = header(part, f"{part} TIA tone {f0/1e6:g} MHz at {frac:g} x the amplitude of Table 6.2b",
                              m["vs_tia"]) + tia_body(part, R_F, C_D + C_PCB_NOM, C_F, 1e6,
                                                      iph=f"Iph 0 inm SIN(0 {ipk:.6e} {f0:g})") + (
                    f".control\nset wr_singlescale\nset wr_vecnames\ntran {tstep:.4e} {tstop:.4e} 0 {tstep:.4e}\n"
                    f"linearize v(oa)\nwrdata tone.txt v(oa)\n.endc\n.end\n")
                log, err = run(ng, write_deck(folder, deck))
                d = read_wrdata(folder / "tone.txt")
                t, v = d[:, 0], d[:, 1]
                sel = t >= tstop - 32 * period - tstep / 2
                vv = v[sel][:32 * 256]
                vv = vv - np.mean(vv)
                spec = np.abs(np.fft.rfft(vv * np.hanning(len(vv))))
                h = [spec[32 * k] for k in (1, 2, 3, 4, 5)]
                sweep.append(dict(frac=float(frac), ipk_mA=ipk * 1e3, v_pos=float(np.max(vv)), v_neg=float(-np.min(vv)),
                                  hd2_dBc=float(20 * np.log10(h[1] / h[0])), hd3_dBc=float(20 * np.log10(h[2] / h[0])),
                                  thd_dBc=float(10 * np.log10(sum(x ** 2 for x in h[1:]) / h[0] ** 2)), errors=err[:1]))
            fr = np.array([r["frac"] for r in sweep])
            thd = np.array([r["thd_dBc"] for r in sweep])
            x60, x40 = _crossing(fr, thd, -60.0), _crossing(fr, thd, -40.0)
            rows[f"{f0/1e6:g}MHz"] = dict(claim_V=claim, zt_ohm=zmag, frac_at_thd_m60=x60, frac_at_thd_m40=x40,
                                         v_at_thd_m60=None if x60 is None else x60 * claim,
                                         v_at_thd_m40=None if x40 is None else x40 * claim, sweep=sweep)
            r1 = next(r for r in sweep if abs(r["frac"] - 1.0) < 1e-9)
            print(f"{part} {label} {f0/1e6:5.0f} MHz: Table 6.2b {claim:.2f} V; THD -60 dBc at "
                  f"{'-' if x60 is None else f'{x60*claim:.2f} V ({x60:.2f} x)'}, -40 dBc at "
                  f"{'-' if x40 is None else f'{x40*claim:.2f} V ({x40:.2f} x)'}; at 1.0 x: +{r1['v_pos']:.2f}/-{r1['v_neg']:.2f} V, "
                  f"HD2 {r1['hd2_dBc']:.1f}, HD3 {r1['hd3_dBc']:.1f}, THD {r1['thd_dBc']:.1f} dBc")
        res[f"{part}|{label}"] = rows
    return res


C_EXT_FIT = (0.0, 1e-12, 3e-12, 6e-12)
PARAM_F = (10e6, 50e6, 100e6, 200e6, 500e6)


def _at(f, y, x):
    return float(np.interp(np.log10(x), np.log10(f), y))


def check_params(ng, spice):
    """Each macromodel's own input parameters, as the TIA sees them.
    (1) Admittance of the inverting input with the non-inverting input grounded, with the
        output free (open loop) and with the output held at AC ground by 1 F:
        C_in = Im(Y)/w.  Equal values mean no internal capacitance from output to input.
    (2) e_n(f) of the open-loop amplifier, both inputs at AC ground, noiseless load.
    (3) The TIA's input-referred noise with noiseless R_F and R_L at four external input
        capacitances C_ext.  At each frequency S(C_ext) = i_n^2 + e_n^2 [1/R_F^2 +
        w^2 (C_0 + C_ext)^2] is solved (least squares) for e_n, C_0 and i_n, where C_0 - C_F
        is the capacitance of the model's own that its e_n source drives."""
    res = {}
    R_F, C_F = 2000.0, 0.25e-12
    noiseless = ".model rnl r(noisy=0)\n"
    for part, m in VENDOR_MODELS.items():
        out = dict(errors=[])
        for mode in ("free", "grounded"):
            # moderate DC-feed elements (1 mH, 1 uF): a 1-kF capacitor would swamp the small
            # input current in rounding error.  The current into the pin is the source current
            # plus the current through LB, both from the simulated node voltages.
            folder = spice / "runs" / "params" / f"{part}_yin_{mode}"
            deck = header(part, f"{part} inverting-input admittance, output {mode}", m["vs_tia"]) + amp(
                part, "0", "inm", "out") + (
                f"LB out inm 1m\nCB inm x 1u\nVt x 0 DC 0 AC 1\nRL out 0 {m['rl']}\n"
                + ("CO out 0 1u\n" if mode == "grounded" else "")
                + ".control\nset wr_singlescale\nset wr_vecnames\nac dec 50 1Meg 30G\n"
                "wrdata yin.txt real(i(vt)) imag(i(vt)) real(v(inm)) imag(v(inm)) real(v(out)) imag(v(out))\n"
                ".endc\n.end\n")
            log, err = run(ng, write_deck(folder, deck))
            out["errors"] += err[:2]
            d = read_wrdata(folder / "yin.txt")
            f = d[:, 0]
            s = 2j * np.pi * f
            v_in, v_out = d[:, 3] + 1j * d[:, 4], d[:, 5] + 1j * d[:, 6]
            Y = (-(d[:, 1] + 1j * d[:, 2]) + (v_out - v_in) / (s * 1e-3)) / v_in
            np.save(spice / "runs" / "params" / f"{part}_yin_{mode}.npy", np.vstack([f, Y.real, Y.imag]))
            C = Y.imag / (2 * np.pi * f)
            out[f"c_in_{mode}_pF"] = {f"{x/1e6:g}MHz": _at(f, C, x) * 1e12 for x in (1e6, 10e6, 100e6, 1e9, 3e9)}
            out[f"r_in_{mode}_kohm"] = 1e-3 / _at(f, Y.real, 1e8)
        folder = spice / "runs" / "params" / f"{part}_zout"
        deck = header(part, f"{part} open-loop output impedance", m["vs_tia"]) + amp(part, "inp", "inm", "out") + (
            "Vp inp 0 DC 0 AC 0\nLB out inm 1G\nCB inm 0 1k\nIz 0 out DC 0 AC 1\n"
            ".control\nset wr_singlescale\nset wr_vecnames\nac dec 100 100k 30G\n"
            "wrdata zout.txt real(v(out)) imag(v(out))\n.endc\n.end\n")
        log, err = run(ng, write_deck(folder, deck))
        out["errors"] += err[:2]
        d = read_wrdata(folder / "zout.txt")
        Zo = d[:, 1] + 1j * d[:, 2]
        np.save(spice / "runs" / "params" / f"{part}_zout.npy", np.vstack([d[:, 0], Zo.real, Zo.imag]))
        out["z_out_open_loop_ohm"] = {f"{x/1e6:g}MHz": [round(_at(d[:, 0], Zo.real, x), 2), round(_at(d[:, 0], Zo.imag, x), 2)]
                                      for x in (1e6, 100e6, 1e9, 3e9, 5e9)}
        folder = spice / "runs" / "params" / f"{part}_en"
        deck = header(part, f"{part} open-loop input voltage noise", m["vs_tia"]) + amp(part, "inp", "inm", "out") + (
            f"Vp inp 0 DC 0 AC 1\nLB out inm 1G\nCB inm 0 1k\nRL out 0 rnl {m['rl']}\n{noiseless}"
            ".control\nset wr_singlescale\nset wr_vecnames\nnoise v(out) Vp dec 20 1Meg 1G\n"
            "setplot noise1\nwrdata en.txt inoise_spectrum\n.endc\n.end\n")
        log, err = run(ng, write_deck(folder, deck))
        out["errors"] += err[:2]
        d = read_wrdata(folder / "en.txt")
        out["e_n_open_loop_nV"] = {f"{x/1e6:g}MHz": _at(d[:, 0], d[:, 1], x) * 1e9 for x in PARAM_F}
        S = []
        for c_ext in C_EXT_FIT:
            folder = spice / "runs" / "params" / f"{part}_tia_noise_C{c_ext*1e12:g}p"
            deck = header(part, f"{part} TIA noise, noiseless R_F, C_ext = {c_ext*1e12:g} pF", m["vs_tia"]) + amp(
                part, "0", "inm", "oa") + (
                f"RF oa inm rnl {R_F}\nCF oa inm {C_F}\n" + (f"CX inm 0 {c_ext}\n" if c_ext > 0 else "")
                + f"RL oa 0 rnl {m['rl']}\nIph 0 inm DC 0 AC 0\n{noiseless}"
                ".control\nset wr_singlescale\nset wr_vecnames\nnoise v(oa) Iph dec 20 1Meg 1G\n"
                "setplot noise1\nwrdata noise.txt inoise_spectrum\n.endc\n.end\n")
            log, err = run(ng, write_deck(folder, deck))
            out["errors"] += err[:2]
            d = read_wrdata(folder / "noise.txt")
            f = d[:, 0]
            S.append(d[:, 1] ** 2)
        # fitted in pA^2/Hz and pF, which keeps the least-squares problem well scaled
        cp = np.array(C_EXT_FIT) * 1e12
        X = np.vstack([np.ones(len(cp)), cp, cp ** 2]).T
        (a, b, q), *_ = np.linalg.lstsq(X, np.array(S) * 1e24, rcond=None)
        w = 2 * np.pi * f
        en = np.sqrt(np.clip(q, 0, None)) / w
        C0 = b / (2 * q) * 1e-12
        in2 = a * 1e-24 - en ** 2 / R_F ** 2 - (en * w * C0) ** 2
        np.save(spice / "runs" / "params" / f"{part}_fit.npy", np.vstack([f, en, C0 - C_F, np.sqrt(np.clip(in2, 0, None))]))
        out["fit"] = {f"{x/1e6:g}MHz": dict(e_n_nV=_at(f, en, x) * 1e9, c_seen_pF=_at(f, C0 - C_F, x) * 1e12,
                                            i_n_pA=_at(f, np.sqrt(np.clip(in2, 0, None)), x) * 1e12) for x in PARAM_F}
        res[part] = out
        p = datasheet(part)
        print(f"{part}: C_in (output free / grounded) at 100 MHz {out['c_in_free_pF']['100MHz']:.3f} / "
              f"{out['c_in_grounded_pF']['100MHz']:.3f} pF, at 3 GHz {out['c_in_free_pF']['3000MHz']:.3f} / "
              f"{out['c_in_grounded_pF']['3000MHz']:.3f} pF, R_in {out['r_in_free_kohm']:.3g} kOhm "
              f"(datasheet C_CM + C_DIFF {(p['c_cm'] + p['c_diff'])*1e12:.2f} pF); "
              f"e_n open loop {[round(v, 3) for v in out['e_n_open_loop_nV'].values()]} nV/rtHz; errors {out['errors'][:1]}")
        print(f"   open-loop output impedance (ohm, real/imag): {out['z_out_open_loop_ohm']}")
        for k, v in out["fit"].items():
            print(f"   {k:>7}: fit e_n {v['e_n_nV']:.3f} nV/rtHz, capacitance seen by e_n {v['c_seen_pF']:.2f} pF, "
                  f"i_n {v['i_n_pA']:.2f} pA/rtHz")
    return res


def check_bench(ng, spice):
    """The OPA846 bench board of Section 5.5 in SPICE: loop gain (Middlebrook), transimpedance
    and input-referred noise for R_F = 1.2 kOhm, C_F = 0.30 pF and several total node
    capacitances C_T (the macromodel's own input capacitance, from 'params', is part of C_T),
    against the measured 1.45 kOhm and 7 pA/rtHz at 50 MHz and the survey's model (Table 5.10)."""
    b = BENCH
    part, R_F, C_F = b["part"], b["R_F"], b["C_F"]
    m = VENDOR_MODELS[part]
    p = PARTS[m["db"]]
    c_in = json.loads((spice / "results" / "params.json").read_text(encoding="utf-8"))[part]["c_in_grounded_pF"]["100MHz"] * 1e-12
    ol_ds, *_ = open_loop_model(p)
    nz = noise_inputs(p)
    res = dict(c_in_model_pF=c_in * 1e12, rows={})
    for C_T in b["C_T"]:
        c_ext = C_T - c_in
        # one folder level below runs/<check>/, like every other deck, so that the relative
        # .include ../../_models/ resolves
        name = f"{part}_R{R_F/1e3:g}k_CT{C_T*1e12:g}p_F{C_F*1e12:.2f}p".replace(".", "p")
        folder_loop = spice / "runs" / "bench" / f"{name}_loop"
        folder_zn = spice / "runs" / "bench" / f"{name}_zt_noise"
        deck = header(part, f"{part} bench TIA, C_T = {C_T*1e12:g} pF", m["vs_tia"]) + tia_body(
            part, R_F, c_ext, C_F, m["rl"], vinj_ac=1, iinj_ac=0) + (
            ".control\nset wr_singlescale\nset wr_vecnames\nac dec 100 100k 30G\n"
            "wrdata vinj.txt real(v(oa)) imag(v(oa)) real(v(fb)) imag(v(fb))\n"
            "alter @vinj[acmag] = 0\nalter @iinj[acmag] = 1\nac dec 100 100k 30G\n"
            "wrdata iinj.txt real(i(vinj)) imag(i(vinj))\n.endc\n.end\n")
        log, err = run(ng, write_deck(folder_loop, deck))
        v, c = read_wrdata(folder_loop / "vinj.txt"), read_wrdata(folder_loop / "iinj.txt")
        f = v[:, 0]
        Tv = -(v[:, 1] + 1j * v[:, 2]) / (v[:, 3] + 1j * v[:, 4])
        Ti = (c[:, 1] + 1j * c[:, 2]) / (1 - (c[:, 1] + 1j * c[:, 2]))
        lm = loop_metrics_from_T(f, (Tv * Ti - 1) / (Tv + Ti + 2))
        deck = header(part, f"{part} bench TIA transimpedance and noise, C_T = {C_T*1e12:g} pF", m["vs_tia"]) + tia_body(
            part, R_F, c_ext, C_F, m["rl"], iph="Iph 0 inm DC 0 AC 1") + (
            ".control\nset wr_singlescale\nset wr_vecnames\nac dec 100 100k 10G\n"
            "wrdata zt.txt real(v(oa)) imag(v(oa))\nnoise v(oa) Iph dec 50 1Meg 1G\n"
            "setplot noise1\nwrdata noise.txt inoise_spectrum\n.endc\n.end\n")
        log2, err2 = run(ng, write_deck(folder_zn, deck))
        z = read_wrdata(folder_zn / "zt.txt")
        Z = np.abs(z[:, 1] + 1j * z[:, 2])
        k = int(np.argmax(Z))
        zm = zt_metrics(z[:, 0], z[:, 1] + 1j * z[:, 2])
        nn = read_wrdata(folder_zn / "noise.txt")
        # the survey's model at the same C_T and C_F (datasheet curve, Eq. (17) central)
        fa = np.array([b["f_meas"]])
        Za, _, _ = tm.tia_tf(fa, ol_ds, R_F, C_T, C_F)
        ma = tm.loop_metrics(ol_ds, R_F, C_T, C_F)
        na = {fx: float(np.sqrt(tm.noise_components(np.array([fx]), R_F, C_T, C_F, nz)["total"][0]) * 1e12) for fx in (10e6, 50e6)}
        row = dict(spice=dict(pm_deg=lm["pm_deg"], f_c_MHz=lm["f_c_MHz"], gm_dB=lm["gm_dB"],
                              zt_50MHz_ohm=_at(z[:, 0], Z, b["f_meas"]), peak_dB=20 * math.log10(Z[k] / Z[0]),
                              f_peak_MHz=float(z[k, 0] / 1e6), f3_MHz=zm["f3_MHz"],
                              noise_10MHz_pA=_at(nn[:, 0], nn[:, 1], 10e6) * 1e12,
                              noise_50MHz_pA=_at(nn[:, 0], nn[:, 1], 50e6) * 1e12),
                   survey=dict(pm_deg=ma["pm_deg"], zt_50MHz_ohm=float(abs(Za[0])), peak_dB=ma["peaking_dB"],
                               f_peak_MHz=ma["f_peak"] / 1e6, f3_MHz=ma["f_3dB"] / 1e6,
                               noise_10MHz_pA=na[10e6], noise_50MHz_pA=na[50e6]),
                   errors=(err + err2)[:3])
        res["rows"][f"{C_T*1e12:g}pF"] = row
        s, a = row["spice"], row["survey"]
        print(f"{part} bench C_T {C_T*1e12:5.2f} pF (C_ext {c_ext*1e12:.2f}): SPICE PM {s['pm_deg']:.1f} deg at {s['f_c_MHz']:.0f} MHz, "
              f"GM {s['gm_dB'] if s['gm_dB'] is None else round(s['gm_dB'], 1)} dB, |Z_T(50 MHz)| {s['zt_50MHz_ohm']:.0f} ohm, "
              f"peak {s['peak_dB']:.1f} dB at {s['f_peak_MHz']:.0f} MHz, noise 10/50 MHz {s['noise_10MHz_pA']:.2f}/{s['noise_50MHz_pA']:.2f} | "
              f"survey PM {a['pm_deg']:.1f}, |Z_T| {a['zt_50MHz_ohm']:.0f}, peak {a['peak_dB']:.1f} dB at {a['f_peak_MHz']:.0f} MHz, "
              f"noise {a['noise_10MHz_pA']:.2f}/{a['noise_50MHz_pA']:.2f} | errors {row['errors'][:1]}")
    return res


# feedback-capacitance scans (Section 10.6): variant A for the edges of its C_F window,
# variant B for the bandwidth that a smaller C_F buys.  Total C_F on a grid; photodiode
# capacitance at its nominal value and +/-0.2 pF; criteria as in Section 4.5.
CF_SCAN = dict(
    A=dict(part="OPA855", configs=((2000.0, 1e-12), (1500.0, 1e-12), (2000.0, 2e-12), (1500.0, 2e-12)),
           cf_pF=np.round(np.arange(0.06, 0.6001, 0.02), 3)),
    B=dict(part="OPA818", configs=((2000.0, 1e-12), (1500.0, 1e-12), (2000.0, 2e-12), (1500.0, 2e-12)),
           cf_pF=np.round(np.arange(0.15, 0.8001, 0.025), 4)))
CF_DCD_pF = (-0.2, 0.0, 0.2)
CF_CRITERIA = dict(pm_deg=45.0, gm_dB=3.0, peak_dB=1.0)
B_PM_LEVELS = (45.0, 40.0)
B_TOLERANCES_pF = (0.1, 0.05)


def _scan_point(ng, folder, part, R_F, C_D, C_F, title):
    """One deck, three AC sweeps: Middlebrook's two injections, then the transimpedance."""
    m = VENDOR_MODELS[part]
    deck = header(part, title, m["vs_tia"]) + tia_body(part, R_F, C_D + C_PCB_NOM, C_F, m["rl"], vinj_ac=1, iinj_ac=0) + (
        ".control\nset wr_singlescale\nset wr_vecnames\nac dec 100 100k 30G\n"
        "wrdata vinj.txt real(v(oa)) imag(v(oa)) real(v(fb)) imag(v(fb))\n"
        "alter @vinj[acmag] = 0\nalter @iinj[acmag] = 1\nac dec 100 100k 30G\n"
        "wrdata iinj.txt real(i(vinj)) imag(i(vinj))\n"
        "alter @iinj[acmag] = 0\nalter @iph[acmag] = 1\nac dec 100 100k 30G\n"
        "wrdata zt.txt real(v(oa)) imag(v(oa))\n.endc\n.end\n")
    log, err = run(ng, write_deck(folder, deck))
    v, c, z = (read_wrdata(folder / n) for n in ("vinj.txt", "iinj.txt", "zt.txt"))
    f = v[:, 0]
    Tv = -(v[:, 1] + 1j * v[:, 2]) / (v[:, 3] + 1j * v[:, 4])
    iv = c[:, 1] + 1j * c[:, 2]
    Ti = iv / (1 - iv)
    lm = loop_metrics_from_T(f, (Tv * Ti - 1) / (Tv + Ti + 2))
    zm = zt_metrics(z[:, 0], z[:, 1] + 1j * z[:, 2])
    return dict(f_c_MHz=lm["f_c_MHz"], pm_deg=lm["pm_deg"], gm_dB=lm["gm_dB"], second_MHz=lm["second_crossing_MHz"],
                f3_MHz=zm["f3_MHz"], peak_dB=zm["peak_dB"], errors=err[:2])


def _window(x, crit):
    """Largest contiguous range of x that meets every criterion (y, level, sense): sense +1
    requires y >= level, -1 requires y <= level.  The edges are refined by linear
    interpolation of the criterion that fails just outside.  Returns (lo, hi, lo_by, hi_by,
    lo_open, hi_open); an open edge lies beyond the scanned range."""
    ok = np.ones(len(x), bool)
    for y, lev, s in crit:
        ok &= s * (np.asarray(y, float) - lev) >= 0
    runs, start = [], None
    for i, o in enumerate(ok):
        if o and start is None:
            start = i
        if start is not None and (not o or i == len(ok) - 1):
            runs.append((start, i if o else i - 1))
            start = None
    if not runs:
        return None
    s, e = max(runs, key=lambda r: r[1] - r[0])

    def refine(i_in, i_out):
        best, by = x[i_out], None
        for (y, lev, sg), name in zip(crit, ("pm", "gm", "peak", "x")):
            if sg * (y[i_out] - lev) < 0 <= sg * (y[i_in] - lev):
                xc = x[i_in] + (lev - y[i_in]) * (x[i_out] - x[i_in]) / (y[i_out] - y[i_in])
                if abs(xc - x[i_in]) <= abs(best - x[i_in]):
                    best, by = xc, name
        return float(best), by
    lo, lo_by = (float(x[s]), None) if s == 0 else refine(s, s - 1)
    hi, hi_by = (float(x[e]), None) if e == len(x) - 1 else refine(e, e + 1)
    return dict(lo_pF=lo, hi_pF=hi, lo_by=lo_by, hi_by=hi_by, lo_open=s == 0, hi_open=e == len(x) - 1)


def _scan_tag(prefix, part, R_F, C_D, C_F):
    return f"{prefix}_{part}_R{R_F/1e3:g}k_D{C_D*1e12:.2f}p_F{C_F*1e12:.3f}p".replace(".", "p")


def _finite(v):
    return None if v is None or not np.isfinite(v) else float(v)


def _noise_point(ng, folder, part, R_F, C_D, C_F, title):
    m = VENDOR_MODELS[part]
    deck = header(part, title, m["vs_tia"]) + tia_body(part, R_F, C_D + C_PCB_NOM, C_F, m["rl"]) + (
        ".control\nset wr_singlescale\nset wr_vecnames\nnoise v(oa) Iph dec 50 100k 1G\n"
        "setplot noise1\nwrdata noise.txt inoise_spectrum\n.endc\n.end\n")
    run(ng, write_deck(folder, deck))
    d = read_wrdata(folder / "noise.txt")
    f, inn = d[:, 0], d[:, 1]
    pen = band_penalty(f, inn, R_F)
    return dict(noise_100MHz_pA=_at(f, inn, 100e6) * 1e12, noise_200MHz_pA=_at(f, inn, 200e6) * 1e12, penalty_dB=float(pen))


def _verify(ng, spice, variant, part, R_F, C_D, centre_pF, tol_pF, check="cfscan"):
    """The nine corners of a proposed design: total C_F = centre +/- tol, C_D +/- 0.2 pF."""
    pts = []
    for dcf in (-tol_pF, 0.0, tol_pF):
        for dcd in CF_DCD_pF:
            cf, cd = (centre_pF + dcf) * 1e-12, C_D + dcd * 1e-12
            folder = spice / "runs" / check / _scan_tag(f"verify_{variant}", part, R_F, cd, cf)
            r = _scan_point(ng, folder, part, R_F, cd, cf, f"{part} C_F scan check, centre {centre_pF:g} pF")
            pts.append(dict(cf_pF=round(centre_pF + dcf, 4), dcd_pF=dcd, **r))
    nom = next(p for p in pts if abs(p["cf_pF"] - centre_pF) < 1e-9 and p["dcd_pF"] == 0.0)
    gms = [p["gm_dB"] for p in pts if p["gm_dB"] is not None]
    return dict(centre_pF=centre_pF, tol_pF=tol_pF, pm_min=min(p["pm_deg"] for p in pts),
                gm_min=min(gms) if gms else None, peak_max=max(p["peak_dB"] for p in pts),
                f3_nominal_MHz=nom["f3_MHz"], peak_nominal_dB=nom["peak_dB"], pm_nominal=nom["pm_deg"],
                f3_range_MHz=[min(p["f3_MHz"] for p in pts), max(p["f3_MHz"] for p in pts)], corners=pts)


def check_cfscan(ng, spice):
    """Scan the total feedback capacitance of both variants (Section 10.6).
    Variant A: the window in which phase margin >= 45 deg, gain margin >= 3 dB and peaking
    <= 1 dB hold at all three photodiode capacitances, its centre and half-width, and the
    same window from the survey's model over the same corners.  Variant B: the smallest
    total C_F that keeps 45 deg (and 40 deg) at all three photodiode capacitances, and
    the centre that keeps it over a C_F tolerance of 0.1 (and 0.05) pF.  Every proposed
    centre is then checked at its nine corners, and its noise simulated."""
    res = {}
    for variant, sc in CF_SCAN.items():
        part = sc["part"]
        p = PARTS[VENDOR_MODELS[part]["db"]]
        ol_ds, *_ = open_loop_model(p)
        res[variant] = {}
        for R_F, C_D in sc["configs"]:
            key = f"{C_D*1e12:g} pF, {R_F/1e3:g} kOhm"
            grid = {}
            survey = {}
            for dcd in CF_DCD_pF:
                rows, srows = [], []
                for cf_pF in sc["cf_pF"]:
                    cf, cd = cf_pF * 1e-12, C_D + dcd * 1e-12
                    folder = spice / "runs" / "cfscan" / _scan_tag(variant, part, R_F, cd, cf)
                    rows.append(_scan_point(ng, folder, part, R_F, cd, cf, f"{part} C_F scan, variant {variant}"))
                    ma = tm.loop_metrics(ol_ds, R_F, cd + C_PCB_NOM + p["c_cm"] + p["c_diff"], cf)
                    srows.append(dict(pm_deg=_finite(ma["pm_deg"]), gm_dB=_finite(ma["gm_dB"]),
                                      peak_dB=max(0.0, float(ma["peaking_dB"])), f3_MHz=_finite(ma["f_3dB"] / 1e6),
                                      stable=bool(ma["stable"])))
                grid[f"{dcd:+.1f}"] = rows
                survey[f"{dcd:+.1f}"] = srows
            x = np.array(sc["cf_pF"])

            def stack(src, q, fill):
                return np.array([[fill if r[q] is None else r[q] for r in src[k]] for k in src])
            pm, gm, pk = stack(grid, "pm_deg", -1e9), stack(grid, "gm_dB", 1e9), stack(grid, "peak_dB", 0.0)
            spm, sgm, spk = stack(survey, "pm_deg", -1e9), stack(survey, "gm_dB", 1e9), stack(survey, "peak_dB", 0.0)
            sstab = np.array([[r["stable"] for r in survey[k]] for k in survey])
            spm = np.where(sstab, spm, -1e9)          # a second crossing counts as unstable
            i0 = list(grid).index("+0.0")
            f3n = np.array([np.nan if r["f3_MHz"] is None else r["f3_MHz"] for r in grid["+0.0"]])
            out = dict(cf_pF=list(map(float, x)), grid=grid, survey=survey)
            if variant == "A":
                crit = CF_CRITERIA
                out["window_all_corners"] = _window(x, [(pm.min(0), crit["pm_deg"], 1), (gm.min(0), crit["gm_dB"], 1),
                                                        (pk.max(0), crit["peak_dB"], -1)])
                out["window_nominal"] = _window(x, [(pm[i0], crit["pm_deg"], 1), (gm[i0], crit["gm_dB"], 1),
                                                    (pk[i0], crit["peak_dB"], -1)])
                out["survey_window_all_corners"] = _window(x, [(spm.min(0), crit["pm_deg"], 1), (sgm.min(0), crit["gm_dB"], 1),
                                                               (spk.max(0), crit["peak_dB"], -1)])
                out["survey_window_nominal"] = _window(x, [(spm[i0], crit["pm_deg"], 1), (sgm[i0], crit["gm_dB"], 1),
                                                           (spk[i0], crit["peak_dB"], -1)])
                w = out["window_all_corners"]
                if w:
                    centre = round((w["lo_pF"] + w["hi_pF"]) / 2 / 0.005) * 0.005
                    tol = np.floor((w["hi_pF"] - w["lo_pF"]) / 2 / 0.005) * 0.005
                    out["proposal"] = _verify(ng, spice, variant, part, R_F, C_D, round(centre, 4), round(float(tol), 4))
                    out["proposal"]["f3_centre_interp_MHz"] = float(np.interp(centre, x, f3n))
            else:
                out["edges"] = {}
                out["proposals"] = {}
                for lev in B_PM_LEVELS:
                    w = _window(x, [(pm.min(0), lev, 1), (gm.min(0), CF_CRITERIA["gm_dB"], 1)])
                    ws = _window(x, [(spm.min(0), lev, 1), (sgm.min(0), CF_CRITERIA["gm_dB"], 1)])
                    out["edges"][f"{lev:g}"] = dict(spice=w, survey=ws)
                    if w:
                        for tol in B_TOLERANCES_pF:
                            centre = round(np.ceil((w["lo_pF"] + tol) / 0.01 - 1e-9) * 0.01, 3)
                            pr = _verify(ng, spice, variant, part, R_F, C_D, centre, tol)
                            pr["peak_nominal_interp_dB"] = float(np.interp(centre, x, pk[i0]))
                            out["proposals"][f"{lev:g}|{tol:g}"] = pr
            # noise at the proposed centres
            props = [out["proposal"]] if variant == "A" and "proposal" in out else list(out.get("proposals", {}).values())
            for pr in props:
                folder = spice / "runs" / "cfscan" / _scan_tag(f"noise_{variant}", part, R_F, C_D, pr["centre_pF"] * 1e-12)
                pr["noise"] = _noise_point(ng, folder, part, R_F, C_D, pr["centre_pF"] * 1e-12, f"{part} noise at C_F {pr['centre_pF']:g} pF")
            res[variant][key] = out
            if variant == "A":
                w, wn, sw = out["window_all_corners"], out["window_nominal"], out["survey_window_all_corners"]
                pr = out.get("proposal")
                fmtw = lambda q: "none" if not q else (f"{'<=' if q['lo_open'] else ''}{q['lo_pF']:.3f} ({q['lo_by']}) to "
                                                       f"{'>=' if q['hi_open'] else ''}{q['hi_pF']:.3f} ({q['hi_by']}) pF")
                print(f"A {key}: SPICE window, all corners {fmtw(w)}; nominal C_D {fmtw(wn)} | survey model, all corners {fmtw(sw)}")
                if pr:
                    print(f"     centre {pr['centre_pF']:.3f} +/- {pr['tol_pF']:.3f} pF: worst PM {pr['pm_min']:.1f}, GM {pr['gm_min']:.1f} dB, "
                          f"peak {pr['peak_max']:.2f} dB; nominal f3 {pr['f3_nominal_MHz']:.0f} MHz (range {pr['f3_range_MHz'][0]:.0f}-"
                          f"{pr['f3_range_MHz'][1]:.0f}); noise 100/200 MHz {pr['noise']['noise_100MHz_pA']:.2f}/"
                          f"{pr['noise']['noise_200MHz_pA']:.2f} pA/rtHz, penalty {pr['noise']['penalty_dB']:.2f} dB")
            else:
                for lev in B_PM_LEVELS:
                    e = out["edges"][f"{lev:g}"]
                    print(f"B {key}: worst PM >= {lev:g} deg from C_F = {e['spice'] and round(e['spice']['lo_pF'], 3)} pF (SPICE), "
                          f"{e['survey'] and round(e['survey']['lo_pF'], 3)} pF (survey model)")
                for k, pr in out["proposals"].items():
                    print(f"     {k}: centre {pr['centre_pF']:.3f} +/- {pr['tol_pF']:.3f} pF: worst PM {pr['pm_min']:.1f}, nominal f3 "
                          f"{pr['f3_nominal_MHz']:.0f} MHz, peak {pr['peak_nominal_dB']:.2f} dB (max {pr['peak_max']:.2f}); noise 100/200 "
                          f"{pr['noise']['noise_100MHz_pA']:.2f}/{pr['noise']['noise_200MHz_pA']:.2f}, penalty {pr['noise']['penalty_dB']:.2f} dB")
    return res


def check_consistency(ng, spice):
    """The analytical model run with each macromodel's own parameters, against the SPICE TIA
    results of 'loop', 'zt' and 'noise', at two levels:
      survey  : the survey's model, T = A/NG with NG = 1 + s C_T Z_F, using the macromodel's
                gain driven at the non-inverting input ('aol') and its input capacitance;
      two-port: the gain driven at the inverting input, the measured input admittance Y_in(f)
                and the open-loop output impedance Z_o(f) loaded by R_L and the feedback
                network:  T = A_- (R_L + Z_o)/R_L * Z_L/(Z_L + Z_o) / (1 + Z_F Y_node).
    Noise: Eq. (17) with the e_n, capacitance and i_n fitted in 'params'.  Agreement at the
    second level shows that the circuit simulation holds nothing beyond these parameters."""
    def load(name):
        return json.loads((spice / "results" / f"{name}.json").read_text(encoding="utf-8"))
    loop, zt, noise = load("loop"), load("zt"), load("noise")
    res = {}
    g = lambda v: float("nan") if v is None else v
    for part, R_F, C_D, C_F, label in DESIGNS:
        key = f"{part}|{label}"
        lp = np.load(spice / "runs" / "loop" / tag(part, R_F, C_D, C_F) / "loop.npy")
        f = lp[0]
        s = 2j * np.pi * f

        def on_grid(path):
            z = np.load(path)
            return (np.interp(np.log10(f), np.log10(z[0]), z[1])
                    + 1j * np.interp(np.log10(f), np.log10(z[0]), z[2]))
        A_plus = on_grid(spice / "runs" / "aol" / part / "aol.npy")
        A_minus = on_grid(spice / "runs" / "aol" / part / "aol_inverting.npy")
        Y_in = on_grid(spice / "runs" / "params" / f"{part}_yin_grounded.npy")
        Zo = on_grid(spice / "runs" / "params" / f"{part}_zout.npy")
        Y_node = s * (C_D + C_PCB_NOM) + Y_in
        C_T = float(Y_node[np.argmin(abs(f - 1e8))].imag / (2 * np.pi * 1e8))
        Z_F = R_F / (1 + s * R_F * C_F)
        RL = VENDOR_MODELS[part]["rl"]
        Z_L = 1 / (1 / RL + 1 / (Z_F + 1 / Y_node))
        T1 = A_plus / (1 + s * C_T * Z_F)
        T2 = A_minus * (RL + Zo) / RL * Z_L / (Z_L + Zo) / (1 + Z_F * Y_node)
        out = dict(C_T_pF=C_T * 1e12)
        for name, T in (("survey", T1), ("two_port", T2)):
            lm, zm = loop_metrics_from_T(f, T), zt_metrics(f, -Z_F * T / (1 + T))
            out[name] = dict(f_c_MHz=lm["f_c_MHz"], pm_deg=lm["pm_deg"], gm_dB=lm["gm_dB"],
                             f3_MHz=zm["f3_MHz"], peak_dB=zm["peak_dB"])
        s_loop = loop[key]["corners"]["dCF+0.0_dCD+0.0"]["spice"]
        out["spice"] = dict(f_c_MHz=s_loop["f_c_MHz"], pm_deg=s_loop["pm_deg"], gm_dB=s_loop["gm_dB"],
                            f3_MHz=zt[key]["spice"]["f3_MHz"], peak_dB=zt[key]["spice"]["peak_dB"])
        fit = np.load(spice / "runs" / "params" / f"{part}_fit.npy")
        spot = {}
        for x in SPOT_F[1:]:
            en, cs, i_n = (_at(fit[0], fit[k], x) for k in (1, 2, 3))
            w = 2 * math.pi * x
            S = 4 * KT / R_F + i_n ** 2 + en ** 2 * (1 / R_F ** 2 + (w * (C_D + C_PCB_NOM + C_F + cs)) ** 2)
            spot[f"{x/1e6:g}MHz"] = dict(model_pA=math.sqrt(S) * 1e12, spice_pA=noise[key]["spot"][f"{x/1e6:g}MHz"]["spice_pA"])
        out["noise"] = spot
        res[key] = out
        print(f"{part} {label}: C_T {C_T*1e12:.2f} pF | survey, two-port, SPICE: " + "; ".join(
            f"{q} " + ", ".join(f"{g(out[k][q]):.{dg}f}" for k in ("survey", "two_port", "spice"))
            for q, dg in (("f_c_MHz", 0), ("pm_deg", 1), ("gm_dB", 1), ("f3_MHz", 0), ("peak_dB", 2))))
        print("      noise (model/SPICE) " + "; ".join(f"{k} {v['model_pA']:.2f}/{v['spice_pA']:.2f}" for k, v in spot.items()))
    return res


# in a working order for 'all': referee needs aol and params; tone needs zt; consistency
# needs aol, params, loop, zt and noise
# every part's best design in SPICE at 1 pF and 2 kOhm (Section 10.10): total C_F on a
# 0.05-pF grid, photodiode capacitance at nominal and +/-0.2 pF, the criteria of Section 4.5
PART_SCAN = dict(R_F=2000.0, C_D=1e-12, cf_pF=np.round(np.arange(0.10, 2.4001, 0.05), 3))


def check_pscan(ng, spice):
    """Each part's widest-band robust design in SPICE at 1 pF and 2 kOhm.  The total C_F is
    stepped over PART_SCAN at the three photodiode capacitances, and the window in which
    phase margin >= 45 deg, gain margin >= 3 dB and peaking <= 1 dB hold at all three, with
    no second crossing, is found as in 'cfscan'.  The design is the window's lower edge plus
    0.05 pF if the window is at least 0.10 pF wide (it then holds for C_F +/- 0.05 pF);
    otherwise the window's centre with the tolerance it allows; without a window, the C_F of
    the largest worst-case phase margin.  A design with a tolerance is checked at its nine
    corners, and its noise is simulated.  A grid already in results/pscan.json for the same
    PART_SCAN is reused (delete that file to rerun the scan itself)."""
    sc = PART_SCAN
    R_F, C_D = sc["R_F"], sc["C_D"]
    x = np.array(sc["cf_pF"])
    cache_file = spice / "results" / "pscan.json"
    cache = json.loads(cache_file.read_text(encoding="utf-8")) if cache_file.exists() else {}
    res = {}
    for part in VENDOR_MODELS:
        old = cache.get(part, {})
        if (old.get("cf_pF") == list(map(float, x)) and old.get("R_F", R_F) == R_F
                and old.get("C_D_pF", C_D * 1e12) == C_D * 1e12):
            grid = old["grid"]
            print(f"{part}: scan grid reused from results/pscan.json")
        else:
            grid = {}
            for dcd in CF_DCD_pF:
                rows = []
                for cf_pF in x:
                    cf, cd = cf_pF * 1e-12, C_D + dcd * 1e-12
                    folder = spice / "runs" / "pscan" / _scan_tag("P", part, R_F, cd, cf)
                    rows.append(_scan_point(ng, folder, part, R_F, cd, cf, f"{part} C_F scan, 1 pF, 2 kOhm"))
                grid[f"{dcd:+.1f}"] = rows

        def stack(q, fill):
            return np.array([[fill if r[q] is None else r[q] for r in grid[k]] for k in grid])
        pm, gm, pk = stack("pm_deg", -1e9), stack("gm_dB", 1e9), stack("peak_dB", 0.0)
        sec = np.array([[r["second_MHz"] is not None for r in grid[k]] for k in grid]).any(0)
        wpm, wgm, wpk = pm.min(0), gm.min(0), pk.max(0)
        wpm_ok = np.where(sec, -1e9, wpm)          # a second crossing counts as failing
        w = _window(x, [(wpm_ok, CF_CRITERIA["pm_deg"], 1), (wgm, CF_CRITERIA["gm_dB"], 1),
                        (wpk, CF_CRITERIA["peak_dB"], -1)])
        f3 = np.array([[np.nan if r["f3_MHz"] is None else r["f3_MHz"] for r in grid[k]] for k in grid])
        i0 = list(grid).index("+0.0")
        j = int(np.argmax(wpm_ok))
        if w and w["hi_pF"] - w["lo_pF"] >= 0.10:
            centre, tol = round(np.ceil((w["lo_pF"] + 0.05) / 0.005 - 1e-9) * 0.005, 3), 0.05
            kind = "robust over C_F +/- 0.05 pF"
        elif w:
            centre = round(round((w["lo_pF"] + w["hi_pF"]) / 2 / 0.005) * 0.005, 3)
            tol = round(float(np.floor((w["hi_pF"] - w["lo_pF"]) / 2 / 0.005) * 0.005), 3)
            kind = f"robust over C_F +/- {tol:.3f} pF only"
        else:
            centre, tol, kind = float(x[j]), 0.0, "criteria not met: largest worst-case PM"
        if tol > 0:
            pr = _verify(ng, spice, "P", part, R_F, C_D, centre, tol, check="pscan")
            design = dict(kind=kind, cf_pF=centre, tol_pF=tol, worst_pm=pr["pm_min"], worst_gm=pr["gm_min"],
                          worst_peak=pr["peak_max"], f3_nominal_MHz=pr["f3_nominal_MHz"], f3_range_MHz=pr["f3_range_MHz"],
                          corners=pr["corners"])
        else:
            design = dict(kind=kind, cf_pF=centre, tol_pF=0.0, worst_pm=float(wpm[j]), worst_gm=_finite(wgm[j]),
                          worst_peak=float(wpk[j]), f3_nominal_MHz=_finite(f3[i0, j]),
                          f3_range_MHz=[_finite(np.nanmin(f3[:, j])), _finite(np.nanmax(f3[:, j]))])
        folder = spice / "runs" / "pscan" / _scan_tag("noise_P", part, R_F, C_D, centre * 1e-12)
        design["noise"] = _noise_point(ng, folder, part, R_F, C_D, centre * 1e-12, f"{part} noise at C_F {centre:g} pF")
        res[part] = dict(R_F=R_F, C_D_pF=C_D * 1e12, cf_pF=list(map(float, x)), grid=grid, window=w, design=design,
                         best_pm=dict(cf_pF=float(x[j]), worst_pm=float(wpm[j]), f3_nominal_MHz=_finite(f3[i0, j])))
        d = design
        print(f"{part}: {d['kind']}, C_F {d['cf_pF']:.3f} pF: worst PM {d['worst_pm']:.1f}, GM "
              f"{d['worst_gm'] if d['worst_gm'] is None else round(d['worst_gm'], 1)} dB, peak {d['worst_peak']:.2f} dB, "
              f"f3 {d['f3_nominal_MHz'] and round(d['f3_nominal_MHz'])} MHz (range {d['f3_range_MHz']}); noise 100 MHz "
              f"{d['noise']['noise_100MHz_pA']:.2f} pA/rtHz, penalty {d['noise']['penalty_dB']:.2f} dB | window "
              f"{w and (round(w['lo_pF'], 3), round(w['hi_pF'], 3), w['lo_by'], w['hi_by'])} | best worst-case PM "
              f"{wpm[j]:.1f} at {x[j]:.2f} pF")
    return res


CHECKS = dict(smoke=check_smoke, aol=check_aol, params=check_params, referee=check_referee, loop=check_loop,
              zt=check_zt, noise=check_noise, step=check_step, tone=check_tone, bench=check_bench,
              cfscan=check_cfscan, pscan=check_pscan, consistency=check_consistency)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("check", choices=list(CHECKS) + ["all"])
    ap.add_argument("--ngspice", default=None, help="path of the ngspice shared library")
    ap.add_argument("--spice", default=str(HERE.parent / "spice"), help="spice folder (models/, runs/, results/)")
    ap.add_argument("--parts", nargs="+", default=None,
                    help="run only these parts; their results are merged into the existing results files")
    a = ap.parse_args()
    spice = Path(a.spice)
    if a.parts:
        unknown = set(a.parts) - set(VENDOR_MODELS)
        if unknown:
            raise SystemExit(f"unknown parts: {sorted(unknown)}")
        for table in (VENDOR_MODELS, REFEREE):
            for k in [k for k in table if k not in a.parts]:
                del table[k]
        DESIGNS[:] = [d for d in DESIGNS if d[0] in a.parts]
    ng = NgSpice(a.ngspice)
    for part in VENDOR_MODELS:
        prepared_model(part, spice)
    names = list(CHECKS) if a.check == "all" else [a.check]
    if a.parts:
        names = [n for n in names if n not in PART_INDEPENDENT]
    for name in names:
        print(f"\n===== {name}")
        out = CHECKS[name](ng, spice)
        (spice / "results").mkdir(parents=True, exist_ok=True)
        path = spice / "results" / f"{name}.json"
        if a.parts and path.exists():
            merged = json.loads(path.read_text(encoding="utf-8"))
            merged.update(out)
            out = merged
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=1, default=float)


if __name__ == "__main__":
    main()
