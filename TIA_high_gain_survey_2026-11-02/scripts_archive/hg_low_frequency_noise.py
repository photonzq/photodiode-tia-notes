"""Input-referred noise at low frequency (10 Hz, 100 Hz, 1 kHz) for every design of the sweep,
against the floor of the feedback resistor and the photodiode, for Section 6.8 of the note
(3 November 2026).

Each design is the sweep's own (the feedback capacitance of data/results/designs.json). The noise is
Eq. (8) of the note, evaluated with the datasheet points of data/amplifiers.json as hg_model.py
interpolates them; it does not depend on the loop gain (Eq. (7)). Where a frequency lies below an
amplifier's first voltage-noise point the model either continues the datasheet slope or holds the
first value; the tables say which, so that held values are not mistaken for data.

Writes data/results/note_tables/table_6_6.md (the critical voltage noise of Eq. (30a) at 100 Hz);
hg_appendix_tables.py takes Tables A.8a-b from tables_a8(). With an argument, also writes a text
summary with the excess at 10 Hz, 100 Hz and 1 kHz beside the band excess of the sweep.

Usage: python hg_low_frequency_noise.py [OUT_TXT]
"""
import json
import math
import sys
from pathlib import Path

import numpy as np

import hg_model as m
from hg_analysis import C_STRAY, RFS, SOURCES
from hg_tables import ORDER, eng

FREQS = [10.0, 100.0, 1000.0]
C_AMP_TYPICAL = 10e-12          # input capacitance assumed for Table 6.6, a precision part's order
LABELS = {"S1336-18BK": "S1336-18BK (Si, 20 pF, 2 GΩ)", "G12180-010A": "G12180-010A (InGaAs, 55 pF, 125 MΩ)",
          "S1336-8BK": "S1336-8BK (Si, 380 pF, 0.4 GΩ)", "G12180-050A": "G12180-050A (InGaAs, 1 nF, 6.5 MΩ)",
          "G12183-010K": "G12183-010K (InGaAs to 2.6 µm, 500 pF, 14 kΩ)"}


def short(src):
    return src.name.split(" ")[0]


def provenance(points, f):
    """How the model obtains the density at f from the datasheet points."""
    pts = sorted(points)
    fx = [p[0] for p in pts]
    if any(abs(math.log10(x / f)) < 0.07 for x in fx):
        return "datasheet"
    if fx[0] < f < fx[-1]:
        return "interpolated"
    if f < fx[0]:
        if len(pts) > 1 and pts[1][1] < pts[0][1] and fx[0] <= 1e3:
            return "extrapolated"
        return "held"
    return "held"


def excess():
    """{(amp, rf, source): [dB at 10 Hz, 100 Hz, 1 kHz]} and {(amp, rf, source): band dN of the sweep}."""
    amps = m.load_amps()
    rows = json.loads((m.DATA / "results" / "designs.json").read_text(encoding="utf-8"))
    cf_of = {(r["amp"], r["rf"], r["source"]): r["cf_pF"] * 1e-12 for r in rows}
    dn_of = {(r["amp"], r["rf"], r["source"]): r["dN_vs_detector_dB"] for r in rows}
    out = {}
    for src in SOURCES:
        for name in ORDER:
            for rf in RFS:
                key = (name, rf, src.name)
                if key not in cf_of:
                    continue
                d = m.Design(amps[name], rf, cf_of[key], src, c_stray=C_STRAY)
                nz = d.noise(np.array(FREQS))
                out[key] = list(10 * np.log10(nz["total"] / (nz["R_F"] + nz["shunt"])))
    return amps, out, dn_of


def e_crit(src, rf, f=100.0):
    """Eq. (30a): the voltage noise that alone would double the floor at f, in V/rtHz."""
    g = 1 / rf + (0.0 if not np.isfinite(src.r_sh) else 1 / src.r_sh)
    c = src.c_d + C_AMP_TYPICAL + C_STRAY
    return math.sqrt(m.FOUR_KT * g) / math.hypot(g, 2 * math.pi * f * c)


def table_6_6_body():
    head = ("| Photodiode | " + " | ".join(eng(rf, "Ω") for rf in RFS) + " |\n"
            "|---|" + "---|" * len(RFS))
    rows = [f"| {LABELS[short(src)]} | " + " | ".join(f"{e_crit(src, rf) * 1e9:.1f}" for rf in RFS) + " |"
            for src in SOURCES]
    return head + "\n" + "\n".join(rows)


def _density_cell(amp, f):
    en = float(amp.en(np.array([f]))[0]) * 1e9
    i_n = float(amp.in_(np.array([f]))[0]) * 1e15
    tag = {"datasheet": "", "interpolated": " (interp.)", "extrapolated": " (extrap.)", "held": " (held)"}
    return f"{en:.3g}{tag[provenance(amp.en_pts, f)]}; {i_n:.3g}{tag[provenance(amp.in_pts, f)]}"


def tables_a8():
    amps, ex, _ = excess()
    out = []
    for letter, f, k in (("a", 100.0, 1), ("b", 10.0, 0)):
        out += [f"*Table A.8{letter}. Excess noise at {f:g} Hz over the floor of the resistor and the photodiode "
                f"(dB), for $R_F$ = {' / '.join(eng(rf, 'Ω') for rf in RFS)}, with each design's feedback "
                f"capacitance from the sweep; the noise density does not depend on the loop gain (Eq. (7)), so the "
                f"designs that Tables 6.1–6.5 and 6.7 leave out are included; a dash marks a gain at which a part "
                f"is not evaluated (Section 6.9). The second column gives $e_n$ (nV/√Hz) and "
                f"$i_n$ (fA/√Hz) at {f:g} Hz as the model takes them from Table A.1: read at that frequency, "
                f"interpolated between datasheet points, extrapolated along the datasheet slope, or held at the "
                f"nearest datasheet value, which makes the entry a lower bound. `hg_low_frequency_noise.py`.*", "",
                "| Amplifier | $e_n$; $i_n$ | " + " | ".join(LABELS[short(s)] for s in SOURCES) + " |",
                "|---|---|" + "---|" * len(SOURCES)]
        for name in ORDER:
            cells = []
            for src in SOURCES:
                vals = [ex.get((name, rf, src.name)) for rf in RFS]
                cells.append(" / ".join("–" if v is None else f"{v[k]:.1f}" for v in vals))
            out.append(f"| {name} | {_density_cell(amps[name], f)} | " + " | ".join(cells) + " |")
        out.append("")
    return "\n".join(out).rstrip("\n")


def summary_text():
    amps, ex, dn_of = excess()
    lines = ["Excess over the R_F + R_sh floor at 10 Hz / 100 Hz / 1 kHz (dB), with the band dN of the sweep"]
    for src in SOURCES:
        lines.append(f"=== {src.name}")
        for name in ORDER:
            cells = []
            for rf in RFS:
                v = ex.get((name, rf, src.name))
                cells.append("-" if v is None else
                             f"{v[0]:.1f}/{v[1]:.1f}/{v[2]:.1f} [{dn_of[(name, rf, src.name)]:.1f}]")
            lines.append(f"  {name:18s} " + "  ".join(f"{c:>24s}" for c in cells))
    return "\n".join(lines)


def main():
    table = m.DATA / "results" / "note_tables" / "table_6_6.md"
    table.write_text(table_6_6_body() + "\n", encoding="utf-8", newline="\n")
    print("written", table.relative_to(m.DATA.parent).as_posix())
    if len(sys.argv) > 1:
        Path(sys.argv[1]).write_text(summary_text() + "\n", encoding="utf-8")
        print("written", sys.argv[1])


if __name__ == "__main__":
    main()
