"""Tables of Chapter 9 of the high-gain TIA note (the SPICE checks), written as table bodies
to data/results/note_tables/table_9_<k>.md for assemble_note.py.

Usage:  python hg_spice_tables.py
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

import hg_model as m
from hg_tables import eng

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "spice" / "results"
OUT = m.DATA / "results" / "note_tables"
ORDER = ["OPA928", "ADA4530-1", "OPA140", "OPA828", "ADA4625-1", "OPA320", "OPA1656", "OPA2156", "OPA818",
         "OPA657", "ADA4817-1", "LTC6268-10"]
ENGINE = {"ADA4530-1": "LTspice", "ADA4625-1": "LTspice", "LTC6268-10": "LTspice"}
AD8304_TPC9_1KHZ = {1e-9: 40.0, 1e-8: 5.5, 1e-7: 1.0, 1e-6: 0.17, 1e-5: 0.15}


def load(name: str) -> dict:
    return json.loads((RES / f"{name}.json").read_text())


def table_designs() -> str:
    sweep = {(r["amp"], r["rf"], r["source"].split(" ")[0]): r
             for r in json.loads((m.DATA / "results" / "designs.json").read_text())}
    rows = load("designs")["designs"] + load("lt_designs")["designs"]
    out = ["| Amplifier | Engine | Designs | $f_{-3\\,\\mathrm{dB}}$: median / largest deviation | "
           "$\\Delta N$: median / largest difference | Designs with $A_0 < 10\\,NG$ |", "|---|---|---|---|---|---|"]
    for part in ORDER:
        sel = [r for r in rows if r["part"] == part]
        ok = [r for r in sel if sweep[(part, r["rf"], r["source"])]["a0_over_ng"] >= 10]
        dev_f = [100 * (r["f3_spice"] / r["f3_model"] - 1) for r in ok]
        dev_n = [r["dN_spice"] - r["dN_model"] for r in ok]
        nflag = len(sel) - len(ok)
        big_f = max(dev_f, key=abs) if dev_f else float("nan")
        big_n = max(dev_n, key=abs) if dev_n else float("nan")
        out.append(f"| {part} | {ENGINE.get(part, 'ngspice')} | {len(sel)} | "
                   f"{np.median(np.abs(dev_f)):.1f}% / {big_f:+.1f}% | "
                   f"{np.median(np.abs(dev_n)):.2f} / {big_n:+.2f} dB | {nflag} |")
    return "\n".join(out)


def table_flagged() -> str:
    sweep = {(r["amp"], r["rf"], r["source"].split(" ")[0]): r
             for r in json.loads((m.DATA / "results" / "designs.json").read_text())}
    rows = load("designs")["designs"]
    out = ["| Design | $A_0$ (datasheet) | Mid-band $NG$ | $f_{-3\\,\\mathrm{dB}}$, SPICE / model | "
           "Resistor pole $1/(2\\pi R_FC_F)$ |", "|---|---|---|---|---|"]
    for r in rows:
        s = sweep[(r["part"], r["rf"], r["source"])]
        if s["a0_over_ng"] >= 10 or r["source"] != "S1336-8BK":
            continue
        a0 = 20 * math.log10(s["ng_mid"] * s["a0_over_ng"])
        f_r = 1 / (2 * math.pi * r["rf"] * r["cf_pF"] * 1e-12)
        out.append(f"| {r['part']}, {eng(r['rf'], 'Ω')}, 380 pF | {a0:.0f} dB | {s['ng_mid']:.0f} | "
                   f"{eng(r['f3_spice'], 'Hz')} / {eng(r['f3_model'], 'Hz')} | {eng(f_r, 'Hz')} |")
    return "\n".join(out)


def table_models() -> str:
    ng = load("models")["models"]
    lt = load("lt_models")["models"]
    amps = m.load_amps()
    out = ["| Amplifier | $e_n$ at 1 kHz, model / datasheet (nV/√Hz) | $i_n$ at 10 Hz, model (fA/√Hz) | "
           "Datasheet $i_n$ (fA/√Hz) |", "|---|---|---|---|"]
    for part in ORDER:
        res = ng.get(part) or lt.get(part)
        f = np.array(res["en"]["f"])
        en = np.array(res["en"]["inoise"])
        e1k = float(np.interp(3.0, np.log10(f), en)) * 1e9
        i10 = float(np.interp(1.0, np.log10(f), np.array(res["in_1e8"]["in_A"]))) * 1e15
        a = amps[part]
        pts = sorted(a.en_pts)
        lo, hi = pts[0][0], pts[-1][0]
        ds = f"{float(a.en(np.array([1e3]))[0]) * 1e9:.3g}" if lo * 0.95 <= 1e3 <= hi * 1.05 else "–"
        din = "; ".join(f"{v * 1e15:.3g} at {eng(fq, 'Hz')}" for fq, v in sorted(a.in_pts)[:2])
        out.append(f"| {part} | {e1k:.3g} / {ds} | {i10:.3g} | {din} |")
    return "\n".join(out)


def table_distributed() -> str:
    res = load("distributed")["distributed"]
    labels = ["lumped (no plane)", "plane at ground", "plane at output", "plane at 1/3 output",
              "four strips, graded", "ideal graded guard"]
    out = ["| Conductor under $R_F$ | OPA140: $f_{-3\\,\\mathrm{dB}}$ SPICE / model; peak; step overshoot | "
           "OPA928: $f_{-3\\,\\mathrm{dB}}$ SPICE / model; peak; step overshoot |", "|---|---|---|"]
    for lab in labels:
        cells = []
        for part in ("OPA140", "OPA928"):
            r = next(x for x in res if x["part"] == part and x["profile"] == lab)
            cells.append(f"{eng(r['f3_spice'], 'Hz')} / {eng(r['f3_model'], 'Hz')}; "
                         f"{r['peak_spice']:.2f} / {r['peak_model']:.2f} dB; {100 * abs(r['step_overshoot']):.0f}%")
        out.append(f"| {lab} | " + " | ".join(cells) + " |")
    return "\n".join(out)


def table_composite() -> str:
    res = load("composite")["composite"]
    out = ["| Photodiode | $R_F$ | LSBF862 cascode, SPICE: $f_{-3\\,\\mathrm{dB}}$; $\\Delta N$ | "
           "BF862 composite, model | OPA140 alone, model |", "|---|---|---|---|---|"]
    for r in res:
        lab = "S1336-8BK, 380 pF" if r["source"] == "S1336-8BK" else "G12180-050A, 1 nF"
        out.append(f"| {lab} | {eng(r['rf'], 'Ω')} | {eng(r['f3_spice'], 'Hz')}; {r['dN_spice']:.1f} dB | "
                   f"{eng(r['f3_model_BF862'], 'Hz')}; {r['dN_model_BF862']:.1f} dB | "
                   f"{eng(r['f3_model_OPA140'], 'Hz')}; {r['dN_model_OPA140']:.1f} dB |")
    return "\n".join(out)


def table_logamp() -> str:
    res = load("lt_logamp")["logamp"]
    vt = m.K_B * m.T_REF / m.Q_E
    scale = 0.2 / math.log(10)
    out = ["| Current | $V_{LOG}$, AD8304 / ADL5303 model | $f_{-3\\,\\mathrm{dB}}$, AD8304 model | "
           "Eq. (33) with 1.5 pF | Noise at 1 kHz, AD8304 model (µV/√Hz) | AD8304 measured, TPC 9 | "
           "Eq. (35) at 200 mV/decade |", "|---|---|---|---|---|---|---|"]
    for ra, rb in zip(res["AD8304"], res["ADL5303"]):
        i = ra["i_in"]
        meas = AD8304_TPC9_1KHZ.get(i)
        out.append(f"| {eng(i, 'A')} | {ra['v_log']:.3f} / {rb['v_log']:.3f} V | {eng(ra['f3'], 'Hz')}"
                   f"{' (peak ' + format(ra['peak'], '.1f') + ' dB)' if ra['peak'] > 0.5 else ''} | "
                   f"{eng(i / (2 * math.pi * vt * 1.5e-12), 'Hz')} | {ra['vn_1k'] * 1e6:.3g} | "
                   f"{('about ' + format(meas, 'g')) if meas else '–'} | {scale * math.sqrt(4 * m.Q_E / i) * 1e6:.3g} |")
    return "\n".join(out)


def table_medium_20pf() -> str:
    """Table 9.7: the 10-kOhm designs on the 20-pF photodiode (hg_spice_medium.py)."""
    res = load("medium")["designs_20pF"]
    label = {"own design": "Sweep's design", "held to 10 MHz": "Held to 10 MHz", "held to 30 MHz": "Held to 30 MHz"}
    out = ["| Amplifier | Design | $C_F$ | $f_{-3\\,\\mathrm{dB}}$, SPICE / model | Peak, SPICE / model | "
           "$\\Delta N$ over [1 Hz, $B$], SPICE / model ($B$) |", "|---|---|---|---|---|---|"]
    for r in res:
        out.append(f"| {r['part']} | {label[r['design']]} | {r['cf_pF']:.3f} pF | "
                   f"{r['f3_spice'] / 1e6:.1f} / {r['f3_model'] / 1e6:.1f} MHz | "
                   f"{r['peak_spice']:.2f} / {r['peak_model']:.2f} dB | "
                   f"{r['dN_spice']:.1f} / {r['dN_model']:.1f} dB ({r['band_Hz'] / 1e6:.1f} MHz) |")
    return "\n".join(out)


def table_medium_node() -> str:
    """Table 9.8: the 10-kOhm designs on the companion's 1-pF node, SPICE against both notes' models."""
    order = ("OPA855", "OPA955", "OPA818")
    res = sorted(load("medium")["companion_node"], key=lambda r: (order.index(r["part"]), r["cf_pF"]))
    out = ["| Amplifier, $C_F$ | Design | $f_{-3\\,\\mathrm{dB}}$: SPICE / companion / this note | "
           "Phase margin: SPICE / companion / this note | Noise over the band: SPICE / companion / this note |",
           "|---|---|---|---|---|"]
    for r in res:
        s, a, h = r["spice"], r["companion_model"], r["this_note_model"]
        design = ("This note's, 0.1 pF of parasitic" if r["design"].startswith("this note")
                  else "Companion's Table A6.38, 0.2 pF")
        out.append(f"| {r['part']}, {r['cf_pF']:.3f} pF | {design} | "
                   f"{s['f3_Hz'] / 1e6:.0f} / {a['f3_Hz'] / 1e6:.0f} / {h['f3_Hz'] / 1e6:.0f} MHz | "
                   f"{s['pm_deg']:.1f}° / {a['pm_deg']:.1f}° / {h['pm_deg']:.1f}° | "
                   f"{s['penalty_dB']:.1f} / {a['penalty_dB']:.1f} / {h['penalty_dB']:.1f} dB "
                   f"({r['band_MHz'][0]:.0f}–{r['band_MHz'][1]:.0f} MHz) |")
    return "\n".join(out)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in (("table_9_1", table_designs), ("table_9_2", table_flagged), ("table_9_3", table_models),
                     ("table_9_4", table_distributed), ("table_9_5", table_composite), ("table_9_6", table_logamp),
                     ("table_9_7", table_medium_20pf), ("table_9_8", table_medium_node)):
        (OUT / f"{name}.md").write_text(fn() + "\n", encoding="utf-8")
        print(name)
        print(fn())


if __name__ == "__main__":
    main()
