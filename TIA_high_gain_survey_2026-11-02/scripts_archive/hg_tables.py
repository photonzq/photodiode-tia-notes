"""Markdown tables of the high-gain TIA note from data/results/*.json and
data/amplifiers.json.  Writes data/results/tables.md; the note's Appendix A
tables are copied from it.

Usage:  python hg_tables.py
"""
from __future__ import annotations

import json
import math

import hg_model as m

RES = m.DATA / "results"
ORDER = ["ADA4530-1", "OPA928", "LMP7721", "LMC6001A", "LMC662",
         "ADA4625-1", "OPA828", "OPA827", "OPA140", "OPA145",
         "OPA1656", "OPA2156", "OPA320", "OPA381", "OPA388",
         "OPA656", "OPA657", "OPA818", "ADA4817-1", "LTC6268-10", "OPA858", "OPA211",
         "OPA855", "OPA955", "LMH6629",
         "IF3601 composite", "LSK170 composite", "BF862 composite"]


def eng(x: float | None, unit: str, digits: int = 3) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "n/a"
    prefixes = [(1e9, "G"), (1e6, "M"), (1e3, "k"), (1, ""), (1e-3, "m"), (1e-6, "µ"),
                (1e-9, "n"), (1e-12, "p"), (1e-15, "f"), (1e-18, "a")]
    for scale, p in prefixes:
        if abs(x) >= scale * 0.9995:
            v = x / scale
            s = f"{v:.{digits}g}"
            return f"{s} {p}{unit}"
    return f"{x:.{digits}g} {unit}"


def gain_table() -> str:
    rows = json.loads((RES / "gain_table.json").read_text())
    out = ["| $R_F$ | $\\sqrt{4k_BT/R_F}$ | $2k_BT/(qR_F)$ | $I_{\\max}$ at 10 V | $I_{\\max}$ at 2.4 V | $1/(2\\pi R_FC_{par})$, 0.05 / 0.1 / 0.2 pF |",
           "|---|---|---|---|---|---|"]
    for r in rows:
        out.append(f"| {eng(r['rf'], 'Ω')} | {eng(r['johnson_A_rtHz'], 'A/√Hz')} | "
                   f"{eng(r['i_shot_equals_johnson_A'], 'A')} | {eng(r['i_max_10V_A'], 'A')} | "
                   f"{eng(r['i_max_2V4_A'], 'A')} | {eng(r['f_res_0p05pF'], 'Hz')} / "
                   f"{eng(r['f_res_0p1pF'], 'Hz')} / {eng(r['f_res_0p2pF'], 'Hz')} |")
    return "\n".join(out)


def en_in_range(name: str, f: float) -> str:
    """Datasheet voltage noise at f, interpolated only inside the range of
    the datasheet points; a dash outside it (no extrapolation in tables)."""
    amps = m.load_amps()
    a = amps[name]
    fs = [p[0] for p in a.en_pts]
    if f < min(fs) * 0.95 or f > max(fs) * 1.05:
        return "–"
    return f"{float(a.en(__import__('numpy').array([f]))[0]) * 1e9:.3g}"


def merits_table() -> str:
    rows = {r["amp"]: r for r in json.loads((RES / "amp_merits.json").read_text())}
    out = ["| Part | Input | GBW (MHz) | $C_{CM}+C_{DIFF}$ (pF) | $e_n$ at 10 Hz / 1 kHz / 100 kHz (nV/√Hz) | $i_n$ (fA/√Hz) | $R_{F,\\mathrm{crit}}=4k_BT/i_n^2$ | $I_B$ max 25 °C / 85 °C | $V_{OS}$ max (µV) |",
           "|---|---|---|---|---|---|---|---|---|"]
    for name in ORDER:
        r = rows.get(name)
        if r is None:
            continue
        c = f"{r['c_in_pF']:.3g}" if r["c_in_pF"] is not None else "not specified"
        ib25 = eng(r["ib_max25_fA"] * 1e-15, "A") if r["ib_max25_fA"] else "n/a"
        ib85 = eng(r["ib_85_fA"] * 1e-15, "A") if r["ib_85_fA"] else "n/a"
        vos = f"{r['vos_max_uV']:.3g}" if r["vos_max_uV"] else "n/a"
        out.append(f"| {name} | {r['input']} | {r['gbw_MHz']:.3g} | {c} | "
                   f"{en_in_range(name, 10.0)} / {en_in_range(name, 1e3)} / {en_in_range(name, 1e5)} | "
                   f"{r['in_fA']:.3g} | {eng(r['rf_crit_Ohm'], 'Ω')} | {ib25} / {ib85} | {vos} |")
    return "\n".join(out)


def design_tables() -> str:
    rows = json.loads((RES / "designs.json").read_text())
    sources = []
    for r in rows:
        if r["source"] not in sources:
            sources.append(r["source"])
    blocks = []
    for src in sources:
        sel = [r for r in rows if r["source"] == src]
        rfs = sorted({r["rf"] for r in sel})
        head = "| Part | " + " | ".join(eng(rf, "Ω") for rf in rfs) + " |"
        blocks.append(f"**{src}**\n\n" + head + "\n|---|" + "---|" * len(rfs))
        for name in ORDER:
            cells = []
            for rf in rfs:
                r = next((x for x in sel if x["amp"] == name and x["rf"] == rf), None)
                if r is None:
                    cells.append("")
                    continue
                flag = "R" if r["limited_by"] == "resistor" else ""
                err = r.get("i_err_85_A")
                verr = eng(err * rf, "V", 2) if err is not None else "n/a"
                cells.append(f"{eng(r['f3_Hz'], 'Hz', 3)}{(' ' + flag) if flag else ''}; "
                             f"{r['dN_vs_detector_dB']:.1f} dB; {verr}")
            blocks[-1] += f"\n| {name} | " + " | ".join(cells) + " |"
    return "\n\n".join(blocks)


TERM_NAME = {"R_F": "$R_F$", "shunt": "diode $R_{sh}$", "i_n": "$i_n$",
             "e_n_G": "$e_n/(R_F\\parallel R_{sh})$", "e_n_C": "$e_n\\,\\omega C$"}

# photodiode labels in the note's tables: capacitance and shunt resistance (Chapter 4),
# capacitance only (Chapter 6, where the shunt resistance matters only for the 14-kOhm diode)
LABEL_LONG = {"S1336-18BK": "S1336-18BK (Si, 20 pF, 2 GΩ)", "G12180-010A": "G12180-010A (InGaAs, 55 pF, 125 MΩ)",
              "S1336-8BK": "S1336-8BK (Si, 380 pF, 0.4 GΩ)", "G12180-050A": "G12180-050A (InGaAs, 1 nF, 6.5 MΩ)",
              "G12183-010K": "G12183-010K (InGaAs to 2.6 µm, 500 pF, 14 kΩ)"}
LABEL_SHORT = {"S1336-18BK": "S1336-18BK (Si, 20 pF)", "G12180-010A": "G12180-010A (InGaAs, 55 pF)",
               "S1336-8BK": "S1336-8BK (Si, 380 pF)", "G12180-050A": "G12180-050A (InGaAs, 1 nF)",
               "G12183-010K": "G12183-010K (InGaAs to 2.6 µm, 500 pF, 14 kΩ)"}


def label(src: str, labels: dict | None) -> str:
    return labels.get(src.split(" ")[0], src) if labels else src


def dominance_table(amp: str = "ADA4625-1", labels: dict | None = None) -> str:
    """Share of each noise term in the band [1 Hz, f_-3dB] for one amplifier,
    every photodiode and gain: the largest term and its share."""
    rows = json.loads((RES / "designs.json").read_text())
    sources = []
    for r in rows:
        if r["source"] not in sources:
            sources.append(r["source"])
    rfs = sorted({r["rf"] for r in rows})
    out = ["| Photodiode | " + " | ".join(eng(rf, "Ω") for rf in rfs) + " |",
           "|---|" + "---|" * len(rfs)]
    for src in sources:
        cells = []
        for rf in rfs:
            r = next(x for x in rows if x["amp"] == amp and x["source"] == src and x["rf"] == rf)
            share = r["share"]
            order = sorted(share, key=share.get, reverse=True)
            first, second = order[0], order[1]
            cells.append(f"{TERM_NAME[first]} {100 * share[first]:.0f}%, "
                         f"{TERM_NAME[second]} {100 * share[second]:.0f}%; "
                         f"{eng(r['f3_Hz'], 'Hz')}{' R' if r['limited_by'] == 'resistor' else ''}")
        out.append(f"| {label(src, labels)} | " + " | ".join(cells) + " |")
    return "\n".join(out)


def shortlist(rf: float, n: int = 4, labels: dict | None = None) -> str:
    """For one gain: per photodiode, the n quietest designs and the fastest."""
    rows = [r for r in json.loads((RES / "designs.json").read_text()) if r["rf"] == rf]
    sources = []
    for r in rows:
        if r["source"] not in sources:
            sources.append(r["source"])
    if labels:
        out = ["| Photodiode | Four quietest ($\\Delta N$; bandwidth) | Fastest (bandwidth; $\\Delta N$) |", "|---|---|---|"]
    else:
        out = [f"| Photodiode | Quietest {n} ($\\Delta N$; $f_{{-3\\,\\mathrm{{dB}}}}$) | Fastest ($f_{{-3\\,\\mathrm{{dB}}}}$; $\\Delta N$) |",
               "|---|---|---|"]
    for src in sources:
        sel = [r for r in rows if r["source"] == src and "composite" not in r["amp"]]
        # designs whose open-loop gain is below ten times the mid-band noise gain are
        # excluded from the ranking: their narrow band, not low noise, makes them look quiet
        ok = [r for r in sel if r.get("a0_over_ng", 1e9) >= 10]
        quiet = sorted(ok, key=lambda r: r["dN_vs_detector_dB"])[:n]
        fast = max(ok, key=lambda r: r["f3_Hz"])
        q = "; ".join(f"{r['amp']} {r['dN_vs_detector_dB']:.1f} dB, {eng(r['f3_Hz'], 'Hz')}" for r in quiet)
        out.append(f"| {label(src, labels)} | {q} | {fast['amp']} {eng(fast['f3_Hz'], 'Hz')}, "
                   f"{fast['dN_vs_detector_dB']:.1f} dB |")
    return "\n".join(out)


def write_note_tables() -> None:
    """Table bodies that assemble_note.py puts into the chapters in place of the
    placeholders <!-- table: name --> (captions stay in the chapter files)."""
    out = RES / "note_tables"
    out.mkdir(parents=True, exist_ok=True)
    for name, text in (("table_4a", dominance_table(labels=LABEL_LONG)),
                       ("table_4b", dominance_table("ADA4530-1", labels=LABEL_LONG))):
        (out / f"{name}.md").write_text(text + "\n", encoding="utf-8")
    for k, rf in enumerate((1e5, 1e6, 1e7, 1e8, 1e9), start=1):
        (out / f"table_6_{k}.md").write_text(shortlist(rf, labels=LABEL_SHORT) + "\n", encoding="utf-8")
    # 10 kOhm, where this note meets the companion (Section 6.9); Table 6.6 is the low-frequency table
    (out / "table_6_7.md").write_text(shortlist(1e4, labels=LABEL_SHORT) + "\n", encoding="utf-8")


def main() -> None:
    write_note_tables()
    text = ["## Gain table", gain_table(), "", "## Amplifier figures of merit", merits_table(),
            "", "## Designs (f_-3dB [R = resistor-limited]; excess over R_F + diode floor in [1 Hz, f_-3dB]; DC output error at 85 C)",
            design_tables(), "", "## Dominant noise terms in band, ADA4625-1", dominance_table(),
            "", "## Dominant noise terms in band, ADA4530-1", dominance_table("ADA4530-1")]
    for rf in (1e4, 1e5, 1e6, 1e7, 1e8, 1e9):
        text += ["", f"## Shortlist at {eng(rf, 'Ω')}", shortlist(rf)]
    (RES / "tables.md").write_text("\n\n".join(text), encoding="utf-8")
    print("tables written:", RES / "tables.md")


if __name__ == "__main__":
    main()
