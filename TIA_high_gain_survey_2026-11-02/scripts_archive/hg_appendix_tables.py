"""Appendix A tables of the high-gain TIA note, generated from
data/amplifiers.json and data/results/*.json.  Writes parts/10_appendix_a.md.

Usage:  python hg_appendix_tables.py
"""
from __future__ import annotations

import json
import math
import pathlib

import hg_model as m
from hg_common_mode import figure_a1_markdown, table_a9
from hg_tables import ORDER, eng

ROOT = pathlib.Path(__file__).resolve().parent.parent
RES = m.DATA / "results"
OUT = ROOT / "parts" / "11_appendix_a.md"
SOURCES_ORDER = ["S1336-18BK (Si 1.1 mm)", "G12180-010A (InGaAs 1 mm)", "S1336-8BK (Si 5.8 mm)",
                 "G12180-050A (InGaAs 5 mm)", "G12183-010K (InGaAs to 2.6 um, 1 mm)"]
SOURCE_LABEL = {
    "S1336-18BK (Si 1.1 mm)": "S1336-18BK: Si, 20 pF, 2 GΩ",
    "G12180-010A (InGaAs 1 mm)": "G12180-010A: InGaAs, 55 pF, 125 MΩ",
    "S1336-8BK (Si 5.8 mm)": "S1336-8BK: Si, 380 pF, 0.4 GΩ",
    "G12180-050A (InGaAs 5 mm)": "G12180-050A: InGaAs, 1 nF, 6.5 MΩ",
    "G12183-010K (InGaAs to 2.6 um, 1 mm)": "G12183-010K: InGaAs to 2.6 µm, 500 pF, 14 kΩ",
}


def fmt_points(pts: dict, unit_scale: float = 1.0) -> str:
    items = sorted(((float(k), v) for k, v in pts.items()), key=lambda x: x[0])
    out = []
    for f, v in items:
        out.append(f"{v * unit_scale:.3g} at {eng(f, 'Hz')}")
    return "; ".join(out)


def table_a1() -> str:
    data = json.loads((m.DATA / "amplifiers.json").read_text(encoding="utf-8"))["parts"]
    head = ("*Table A.1. Amplifier data used in this note, typical values at 25 °C unless marked. "
            "$e_n$ in nV/√Hz and $i_n$ in fA/√Hz at the frequencies given; $I_B$ maximum at 25 °C and at the "
            "higher temperatures the datasheet gives; $C_{CM}$ and $C_{DIFF}$ in pF. Pages are PDF pages of the "
            "document named. Curves marked \"companion\" were digitized for the companion note and are taken from "
            "its records. Source: `data/amplifiers.json`.*\n\n"
            "| Part | Document | Input | GBW (MHz); min. gain | $e_n$ | $i_n$ | $C_{CM}$ / $C_{DIFF}$ | $I_B$ typ; max 25 °C; hot | $V_{OS}$ max | Pages |\n"
            "|---|---|---|---|---|---|---|---|---|---|")
    rows = [head]
    for name in ORDER:
        p = data.get(name)
        if p is None:
            continue
        en = fmt_points(p["en"])
        if len(p["en"]) > 6:
            pts = sorted(((float(k), v) for k, v in p["en"].items()), key=lambda x: x[0])
            en = f"curve, {len(pts)} points: {pts[0][1]:.3g} at {eng(pts[0][0], 'Hz')} to {pts[-1][1]:.3g} at {eng(pts[-1][0], 'Hz')}"
        inn = fmt_points(p["in_"])
        if len(p["in_"]) > 6:
            pts = sorted(((float(k), v) for k, v in p["in_"].items()), key=lambda x: x[0])
            inn = f"curve, {len(pts)} points: {pts[0][1]:.3g} at {eng(pts[0][0], 'Hz')} to {pts[-1][1]:.3g} at {eng(pts[-1][0], 'Hz')}"
        c = "not given" if p.get("c_cm") is None else f"{p['c_cm']:g} / {p.get('c_diff') or 0:g}"
        ib_typ = eng(p["ib_typ"] * 1e-15, "A") if p.get("ib_typ") else "–"
        ib25 = eng(p["ib_max25"] * 1e-15, "A") if p.get("ib_max25") else "–"
        hot = ", ".join(f"{eng(v * 1e-15, 'A')} at {k} °C" if k != "extremes" else f"{eng(v * 1e-15, 'A')} at the temperature extremes"
                        for k, v in p.get("ib_hot", {}).items()) or "–"
        vos = f"{p['vos_max_uV']:g} µV" if p.get("vos_max_uV") else "–"
        gbw = f"{p['gbw']:g}; {p.get('min_gain', 1):g}"
        note = p.get("cite", "")
        rows.append(f"| {name} | {p.get('doc', '')} | {p.get('input', '')} | {gbw} | {en} | {inn} | {c} | "
                    f"{ib_typ}; {ib25}; {hot} | {vos} | {note} |")
    rows.append("")
    rows.append("Notes to Table A.1. For LTC6268-10 the voltage-noise points at 1 Hz–1 kHz are estimated from its "
                "0.1–10 Hz noise of 12.6 µV peak to peak, assuming a $1/f$ density and a peak-to-peak value of 6.6 "
                "times the rms (Appendix B.1). The composites' gain–bandwidth product of 50 MHz is an assumption, and "
                "their current noise is the shot noise of the maximum gate current, an upper bound. OPA381 and OPA388 "
                "are auto-zero and zero-drift parts; their bias currents at 85 °C are datasheet limits (OPA388) or the "
                "25 °C limit doubled every 10 °C (OPA381), the latter an assumption. OPA858, OPA855, OPA955 and LMH6629 "
                "come from the companion note's records and are evaluated at 10 kΩ and 100 kΩ only (Section 6.9). "
                "OPA955's datasheet is Advance Information, for a preproduction part, so its values may change. The "
                "85-°C bias currents of OPA855 and OPA955 are the 25-°C maximum plus the typical drift over 60 °C, an "
                "estimate, and LMH6629's $C_{DIFF}$ of 4 pF is a simulated value. The bias currents hold at the "
                "input common-mode voltage of each specification, mid-supply unless the Pages column names another; "
                "Section 8.6 and Table A.9 give their dependence on that voltage.")
    return "\n".join(rows)


def table_a2() -> str:
    rows = {r["amp"]: r for r in json.loads((RES / "amp_merits.json").read_text())}
    out = ["*Table A.2. Derived figures of merit: the critical feedback resistance of Eq. (11), above which the "
           "amplifier's current noise exceeds the resistor's Johnson noise, and the optimum source resistance of "
           "Eq. (14) with $e_n$ at 1 kHz (or the nearest specified frequency). $i_n$ is the lowest-frequency "
           "specified value. For the wideband bipolar parts that value lies on a $1/f$ rise; their white current noise "
           "above 1 MHz, 2.5 pA/√Hz for OPA855, 2.6 pA/√Hz for LMH6629 and 0.55 pA/√Hz for OPA955, gives "
           "$R_{F,\\mathrm{crit}}$ = 2.6, 2.4 and 54 kΩ, the values that apply in a band of megahertz (Section 6.9).*", "",
           "| Part | $e_n$ at 1 kHz (nV/√Hz) | $i_n$ (fA/√Hz) | $R_{F,\\mathrm{crit}}$ | $R_{opt}$ | $C_{CM}+C_{DIFF}$ (pF) | GBW (MHz) |",
           "|---|---|---|---|---|---|---|"]
    for name in ORDER:
        r = rows.get(name)
        if r is None:
            continue
        c = f"{r['c_in_pF']:.3g}" if r["c_in_pF"] is not None else "not given"
        out.append(f"| {name} | {r['en_1kHz']:.3g} | {r['in_fA']:.3g} | {eng(r['rf_crit_Ohm'], 'Ω')} | "
                   f"{eng(r['r_opt_Ohm'], 'Ω')} | {c} | {r['gbw_MHz']:.4g} |")
    return "\n".join(out)


def table_a3() -> str:
    rows = json.loads((RES / "designs.json").read_text())
    rfs = sorted({r["rf"] for r in rows})
    blocks = []
    for letter, src in zip("abcde", SOURCES_ORDER):
        sel = [r for r in rows if r["source"] == src]
        cap = (f"*Table A.3{letter}. Designs on the {SOURCE_LABEL[src]} photodiode: −3 dB bandwidth (\"R\" = "
               "resistor-limited, $C_F = C_{par}$ = 0.1 pF; \"A\" = the amplifier's DC open-loop gain is less than ten "
               "times the mid-band noise gain $(C_T + C_F)/C_F$, Section 3.1); excess noise $\\Delta N$ over the "
               "resistor-plus-diode floor "
               "in [1 Hz, $f_{-3\\,\\mathrm{dB}}$], Eq. (16); DC output error at 85 °C from the maximum $V_{OS}$ and "
               "$I_B$, Eq. (38) without leakage. A dash marks a gain at which a part is not evaluated: the companion "
               "note's fast parts OPA858, OPA855, OPA955 and LMH6629 are evaluated at 10 kΩ and 100 kΩ only "
               "(Section 6.9). `hg_analysis.py`.*")
        head = "| Part | " + " | ".join(eng(rf, "Ω") for rf in rfs) + " |"
        block = [cap, "", head, "|---|" + "---|" * len(rfs)]
        for name in ORDER:
            cells = []
            for rf in rfs:
                r = next((x for x in sel if x["amp"] == name and x["rf"] == rf), None)
                if r is None:
                    cells.append("–")
                    continue
                flag = " R" if r["limited_by"] == "resistor" else ""
                if r.get("a0_over_ng", 1e9) < 10:
                    flag += " A"
                err = r.get("i_err_85_A")
                verr = eng(err * rf, "V", 2) if err is not None else "n/a"
                cells.append(f"{eng(r['f3_Hz'], 'Hz')}{flag}; {r['dN_vs_detector_dB']:.1f} dB; {verr}")
            block.append(f"| {name} | " + " | ".join(cells) + " |")
        blocks.append("\n".join(block))
    return "\n\n".join(blocks)


def table_a4() -> str:
    num = json.loads((RES / "numbers.json").read_text())
    out = ["*Table A.4. Crossover gain $R_F^* = C_T/(\\pi\\,GBW\\,C_{par}^2)$, Eq. (20), above which the feedback "
           "resistor's own capacitance sets the bandwidth.*", "",
           "| GBW | $C_T$ | $C_{par}$ = 0.05 pF | 0.1 pF | 0.2 pF |", "|---|---|---|---|---|"]
    rows = num["crossover"]
    for gbw, cts in ((2.0, (10.0, 100.0, 1000.0)), (20.0, (10.0, 100.0, 1000.0)), (200.0, (10.0, 100.0, 1000.0)),
                     (2000.0, (1.0, 10.0, 100.0))):
        for ct in cts:
            vals = [next(r for r in rows if math.isclose(r["gbw_MHz"], gbw, rel_tol=1e-6)
                         and math.isclose(r["c_t_pF"], ct, rel_tol=1e-6)
                         and math.isclose(r["c_par_pF"], cp, rel_tol=1e-6))
                    for cp in (0.05, 0.1, 0.2)]
            out.append(f"| {gbw:g} MHz | {ct:g} pF | " + " | ".join(eng(v["rf_star_Ohm"], "Ω") for v in vals) + " |")
    return "\n".join(out)


def table_a5() -> str:
    num = json.loads((RES / "numbers.json").read_text())
    out = ["*Table A.5. How far equalization can extend the band: the frequency $f_e$ at which $e_n\\,\\omega C_T$ "
           "reaches the resistor-plus-diode floor, Eq. (13), with $e_n(f)$ from the datasheet curve, against the "
           "resistor's own pole $f_R$ for 0.1 pF. Equalizing beyond $f_R$ pays only up to about $f_e$. `hg_numbers.py`.*",
           "", "| Amplifier | $R_F$ | Photodiode | $C_T + C_{par}$ | $f_e$ | $f_R$ |", "|---|---|---|---|---|---|"]
    for r in num["equalization"]:
        out.append(f"| {r['amp']} | {eng(r['rf'], 'Ω')} | {r['source']} | {r['c_t_pF']:.3g} pF | "
                   f"{eng(r['f_e_Hz'], 'Hz')} | {eng(r['f_res_0p1pF_Hz'], 'Hz')} |")
    return "\n".join(out)


def table_a6() -> str:
    num = json.loads((RES / "numbers.json").read_text())
    out = ["*Table A.6. Discrete-JFET composites against ADA4625-1: the reduction of $e_n\\,C_T$ at 10 kHz, with "
           "the device's input capacitance and 1 pF of board capacitance included, and the bandwidth ratio at "
           "equal $e_n\\,\\omega C$ noise, $(\\text{ratio})^{2/3}$. `hg_numbers.py`.*", "",
           "| Photodiode capacitance | Device | Reduction of $e_n C_T$ | Bandwidth ratio at equal noise |",
           "|---|---|---|---|"]
    for r in num["composites"]:
        out.append(f"| {r['c_d_pF']:g} pF | {r['device'].replace(' composite', '')} | "
                   f"{r['dB']:.1f} dB (×{r['ratio']:.2f}) | {r['bandwidth_ratio_equal_noise']:.2f} |")
    return "\n".join(out)


def table_a7() -> str:
    num = json.loads((RES / "numbers.json").read_text())
    out = ["*Table A.7. A transdiode logarithmic amplifier at 25 °C: the transistor's small-signal resistance "
           "$r_e = V_T/I$, the bandwidth $I/(2\\pi V_TC_C)$ of Eq. (33) for three compensation capacitors, and the "
           "relative noise $\\sqrt{4q/I}$ of Eq. (35). `hg_numbers.py`.*", "",
           "| Current | $r_e$ | $f_{-3\\,\\mathrm{dB}}$, 10 pF | 100 pF | 1 nF | Relative noise per √Hz | Output noise per √Hz at 59.2 mV/decade |",
           "|---|---|---|---|---|---|---|"]
    for r in num["log_amp"]:
        out.append(f"| {eng(r['I_A'], 'A')} | {eng(r['r_e_Ohm'], 'Ω')} | {eng(r['f3_Cc_10pF_Hz'], 'Hz')} | "
                   f"{eng(r['f3_Cc_100pF_Hz'], 'Hz')} | {eng(r['f3_Cc_1000pF_Hz'], 'Hz')} | "
                   f"{r['rel_noise_per_rtHz']:.3g} | {eng(r['vn_out_V_rtHz'], 'V/√Hz')} |")
    return "\n".join(out)


def table_a8() -> str:
    """Tables A.8a-b, the excess noise at 100 Hz and 10 Hz, from hg_low_frequency_noise.py."""
    import hg_low_frequency_noise as lf
    return lf.tables_a8()


def main() -> None:
    parts = ["## Appendix A. Tables", "",
             "The tables below are generated by `scripts_archive/hg_appendix_tables.py` from the data and result files "
             "named in their captions, so that no number is typed by hand.", "",
             "### A.1 Amplifier data", "", table_a1(), "",
             "### A.2 Figures of merit", "", table_a2(), "",
             "### A.3 The design sweep", "", table_a3(), "",
             "### A.4 Crossover gains", "", table_a4(), "",
             "### A.5 Limits of equalization", "", table_a5(), "",
             "### A.6 Discrete-JFET composites", "", table_a6(), "",
             "### A.7 Logarithmic amplifier", "", table_a7(), "",
             "### A.8 Noise at low frequency", "", table_a8(), "",
             "### A.9 Bias current against common-mode voltage", "", table_a9(), "", figure_a1_markdown(), "",
             "---", ""]
    OUT.write_text("\n".join(parts), encoding="utf-8", newline="")
    print("written", OUT)


if __name__ == "__main__":
    main()
