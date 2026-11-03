"""Low-frequency noise of the 2-kOhm balanced-pair TIA (Section 6.9, 3 November 2026): the
input-referred noise at 100 Hz, 1 kHz and 10 kHz of the ten amplifiers carried forward, from the
voltage- and current-noise curves digitized from their datasheets (data/specs/<part>.json,
"curve_points"), against the floor of R_F and the shot noise of I1 + I2.

At these frequencies the capacitive term of Eq. (23) is negligible (2 pi x 10 kHz x 6 pF = 0.4 uS
against 1/R_F = 500 uS), so the amplifier adds i_n(f)^2 + (e_n(f)/R_F)^2. Within a digitized curve the
density is interpolated log-log. Below a curve's first point the value is not data: it continues the
curve's lowest-decade slope, no steeper than 1/f in power, and is marked as an extrapolation.

Writes Table A6.37 (Markdown, caption included) to data/results/table_a6_37.md, and with an argument a
text summary that adds 10 kHz.

Usage: python low_frequency_noise.py [OUT_TXT]
"""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARTS = ["OPA955", "OPA846", "OPA843", "OPA818", "LMH6629", "OPA858", "OPA859", "THS4304", "OPA856", "OPA855"]
LABEL = {"LMH6629": "LMH6629 (COMP HI)"}
CURVES = {"OPA855": "Fig 6-11 (p9)", "OPA955": "Fig 6-7 (p8)", "OPA858": "Figs 6-11 (p9) and 8-8 (p19)",
          "OPA859": "Figs 6-11 (p9) and 8-8 (p19)", "OPA856": "Fig 7-5 (p7)", "LMH6629": "Figs 28 and 29 (p15)",
          "THS4304": "Fig 18 (p10)", "OPA843": "noise plot (p6)", "OPA846": "noise plot (p6)",
          "OPA818": "Figs 6-19 and 6-20 (p10), the latter labelled simulation"}
R_F = 2e3
KT4 = 4 * 1.380649e-23 * 298.15
Q = 1.602176634e-19
CURRENTS_MA = [0.0, 0.1, 1.0, 10.0]


def curve(spec, key, unit):
    return sorted((p["f_Hz"], p[unit]) for p in spec[key].get("curve_points", []))


def density(pts, f):
    """(value, extrapolated?) at f from a curve given as [(f, value)]."""
    fx = [p[0] for p in pts]
    vx = [p[1] for p in pts]
    if fx[0] / 1.06 <= f < fx[0]:
        return vx[0], False             # a curve that starts within 6 % above f: its first point is read
    if f >= fx[0]:
        if f >= fx[-1]:
            return vx[-1], False
        for (f0, v0), (f1, v1) in zip(pts, pts[1:]):
            if f0 <= f <= f1:
                t = math.log10(f / f0) / math.log10(f1 / f0)
                return 10 ** (math.log10(v0) + t * math.log10(v1 / v0)), False
    # below the first point: continue the slope of the lowest decade, capped at -0.5 (1/f in power)
    later = [p for p in pts if p[0] >= 3 * fx[0]] or pts[1:]
    f1, v1 = later[0]
    slope = min(max(math.log10(v1 / vx[0]) / math.log10(f1 / fx[0]), -0.5), 0.0)
    return vx[0] * (f / fx[0]) ** slope, True


def floor(i_ma):
    return math.sqrt(KT4 / R_F + 2 * Q * i_ma * 1e-3) * 1e12          # pA/rtHz


def point(part, f):
    spec = json.loads((ROOT / "data" / "specs" / f"{part}.json").read_text(encoding="utf-8"))
    en, xe = density(curve(spec, "voltage_noise", "nV_rtHz"), f)
    i_n, xi = density(curve(spec, "current_noise", "pA_rtHz"), f)
    added = math.sqrt(i_n ** 2 + (en * 1e-9 / R_F * 1e12) ** 2)
    db = [10 * math.log10(1 + added ** 2 / floor(i) ** 2) for i in CURRENTS_MA]
    return dict(en=en, xe=xe, i_n=i_n, xi=xi, added=added, db=db, extrap=xe or xi)


def fmt(v, extrap):
    return f"{v:.3g}" + ("†" if extrap else "")


def table_a6_37():
    lines = ["*Table A6.37. Noise at low frequency at $R_F$ = 2 kΩ, from each datasheet's noise curves (last "
             "column): the voltage and current noise at 1 kHz and 100 Hz, the noise the amplifier adds referred to "
             "the photocurrent, $\\sqrt{i_n^2 + (e_n/R_F)^2}$, and what that adds to the floor of $R_F$ and the shot "
             "noise of $I_1 + I_2$ = 0, 0.1, 1 and 10 mA. Where a curve starts at most 6 % above 1 kHz or 100 Hz "
             "(1.03–1.05 kHz for OPA855, OPA858 and OPA859, 102–105 Hz for OPA818 and OPA955), its first point is "
             "used. Values marked † lie further below the first plotted point of a curve and continue it at its "
             "lowest-decade slope, at most 1/f in power; they are extrapolations, not data. Amplifiers: OPA955, OPA846, OPA843, OPA818, LMH6629 (COMP HI), OPA858, OPA859, THS4304, OPA856 "
             "and OPA855 (one per row), ordered by the noise they add at 1 kHz.*", "",
             "| Amplifier | $e_n$ (nV/√Hz) / $i_n$ (pA/√Hz) at 1 kHz | at 100 Hz | Added noise at 1 kHz / 100 Hz "
             "(pA/√Hz) | Added to the floor at 1 kHz: 0 / 0.1 / 1 / 10 mA (dB) | at 100 Hz: 0 / 0.1 / 1 / 10 mA (dB) "
             "| Curves |",
             "|---|---|---|---|---|---|---|"]
    for part in PARTS:
        k, h = point(part, 1e3), point(part, 100.0)
        lines.append(
            f"| {LABEL.get(part, part)} | {fmt(k['en'], k['xe'])} / {fmt(k['i_n'], k['xi'])} | "
            f"{fmt(h['en'], h['xe'])} / {fmt(h['i_n'], h['xi'])} | "
            f"{fmt(k['added'], k['extrap'])} / {fmt(h['added'], h['extrap'])} | "
            + " / ".join(f"{d:.1f}" for d in k["db"]) + " | " + " / ".join(f"{d:.1f}" for d in h["db"])
            + f" | {CURVES[part]} |")
    return "\n".join(lines)


def summary():
    lines = ["floor (R_F Johnson + shot noise of I1 + I2): "
             + ", ".join(f"{i:g} mA {floor(i):.2f} pA/rtHz" for i in CURRENTS_MA)]
    for part in PARTS:
        lines.append(part)
        for f in (100.0, 1e3, 1e4):
            p = point(part, f)
            lines.append(f"  {f:>7g} Hz: e_n {fmt(p['en'], p['xe'])} nV, i_n {fmt(p['i_n'], p['xi'])} pA, "
                         f"added {p['added']:.2f} pA/rtHz; dB over the floor at 0/0.1/1/10 mA: "
                         + " / ".join(f"{d:.1f}" for d in p["db"]))
    return "\n".join(lines)


def main():
    out = ROOT / "data" / "results" / "table_a6_37.md"
    out.write_text(table_a6_37() + "\n", encoding="utf-8", newline="\n")
    print("written", out.relative_to(ROOT).as_posix())
    if len(sys.argv) > 1:
        Path(sys.argv[1]).write_text(summary() + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
