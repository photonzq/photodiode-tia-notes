"""Closed forms, the numbers quoted and the figures of the side note TIA_trace_inductance.

Usage (from this folder):
    python trace_thickness.py numbers     # prints every number of the note, with its equation
    python trace_thickness.py figures     # writes ../figures/fig1_thickness and fig2_internal (.png, .pdf)

What it computes
----------------
* A trace alone, with no plane beneath it (the note's Section 3).  The partial mutual inductance of two
  parallel filaments of length l at the distance d, M(l, d) (Eq. (1), the side note
  TIA_feedback_layouts' Eq. (3)), averaged over pairs of points of the cross-section: for a strip
  without thickness with the density 2(w - s)/w^2 of the side note's Eq. (4), and for a rectangle w x t
  with the density 4(w - a)(t - b)/(w^2 t^2) of the two offsets a and b (the note's Eq. (2)).  This is
  the partial self-inductance with a uniform current, which FastHenry computes with one filament.  The
  geometric mean distance g = exp<ln d> of the cross-section (Eq. (3)) shows why the thickness enters
  only weakly, and Eq. (4) is the shift it makes.
* A trace over a plane (Section 4).  L' = Z_L1/c0 (Eq. (5)) with the microstrip formula of Hammerstad
  and Jensen in a homogeneous medium (Eqs. (6) and (7)) and their thickness correction (Eq. (8)), as
  given in the Qucs technical documentation, section "Single microstrip line", Eqs. (11.4), (11.6) and
  (11.22).
* The copper's own inductance below a few megahertz (Section 5): the internal impedance of a conductor
  with its field on one face, Z' w = rho k coth(k t), k = (1 + j)/delta (Eq. (9)), expressed as the
  height it adds to the gap of a wide trace (Eq. (10)).
* What this means for the 2-kOhm OPA846 design of the side note's Section 4 (Section 6, Eq. (11)).
Copper has rho = 1.7e-8 ohm m, as in the side note's Appendix C.  The FastHenry results come from
fasthenry_traces.py (../data/fasthenry/); run it first.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy import integrate

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))
import fasthenry_traces as fh                 # noqa: E402

FIG = HERE.parents[1] / "figures"
MU0_2PI = 0.2                                 # mu0/(2 pi) in nH/mm
MU0 = 4e-7 * math.pi                          # H/m
RHO = fh.RHO                                  # ohm m
W, L_ALONE = fh.W, fh.L_ALONE                 # mm
COPPER = fh.COPPER                            # mm
OZ = {0.0175: "1/2 oz", 0.035: "1 oz", 0.070: "2 oz"}


# ================================================================================================
# A trace with no plane beneath it
# ================================================================================================
def mutual(l: float, d: float) -> float:
    """Eq. (1): partial mutual inductance (nH) of two parallel filaments of length l at distance d (mm)."""
    return MU0_2PI * (l * math.asinh(l / d) - math.sqrt(l * l + d * d) + d)


def l_strip(l: float, w: float) -> float:
    """The side note's Eq. (4): a strip without thickness, uniform current (nH)."""
    return integrate.quad(lambda s: 2 * (w - s) / w ** 2 * mutual(l, s), 0, w, limit=200)[0]


def l_bar(l: float, w: float, t: float) -> float:
    """Eq. (2): a bar w x t with a uniform current, the average of Eq. (1) over its cross-section (nH)."""
    f = lambda b, a: 4 * (w - a) * (t - b) / (w * w * t * t) * mutual(l, math.hypot(a, b))  # noqa: E731
    return integrate.dblquad(f, 0, w, 0, t, epsabs=1e-10, epsrel=1e-9)[0]


def gmd_strip(w: float) -> float:
    """exp<ln s> over the density 2(w - s)/w^2: w exp(-3/2) (mm)."""
    return w * math.exp(-1.5)


def gmd_rect(w: float, t: float) -> float:
    """Eq. (3): the geometric mean distance of a rectangle w x t from itself (mm)."""
    f = lambda b, a: 4 * (w - a) * (t - b) / (w * w * t * t) * math.log(math.hypot(a, b))  # noqa: E731
    return math.exp(integrate.dblquad(f, 0, w, 0, t, epsabs=1e-12, epsrel=1e-10)[0])


# ================================================================================================
# A trace over a plane
# ================================================================================================
def width_correction(w: float, h: float, t: float) -> float:
    """Eq. (8): Hammerstad and Jensen's widening for the thickness t in a homogeneous medium (mm)."""
    if t <= 0:
        return 0.0
    coth = 1.0 / math.tanh(math.sqrt(6.517 * w / h))
    return t / math.pi * math.log(1 + 4 * math.e / (t / h * coth ** 2))


def lp_microstrip(w: float, h: float, t: float = 0.0) -> float:
    """Eqs. (5)-(8): inductance per unit length (nH/mm) of a trace w x t at the height h over a plane."""
    w1 = w + width_correction(w, h, t)
    fu = 6 + (2 * math.pi - 6) * math.exp(-(30.666 * h / w1) ** 0.7528)
    return MU0_2PI * math.log(fu * h / w1 + math.sqrt(1 + (2 * h / w1) ** 2))


# ================================================================================================
# Below a few megahertz: the copper's own inductance
# ================================================================================================
def skin_depth_um(f: float) -> float:
    return math.sqrt(2 * RHO / (2 * math.pi * f * MU0)) * 1e6


def added_height_um(t_um: float, f: float) -> float:
    """Eqs. (9)-(10): Im(rho k coth(k t)) / (omega mu0), the height (um) that one conductor of thickness
    t adds to the gap of a wide trace through the field inside it."""
    omega = 2 * math.pi * f
    delta = skin_depth_um(f) * 1e-6
    k = (1 + 1j) / delta
    z = RHO * k / np.tanh(k * t_um * 1e-6)
    return float(z.imag / (omega * MU0) * 1e6)


# ================================================================================================
# FastHenry records
# ================================================================================================
def fh_alone() -> dict:
    """{(t_um, 'DC' | 'HF'): L_nH} for the trace alone, HF at 13 x 7 (13 x 1 for the 1-um strip)."""
    rows = json.loads((fh.DATA / "alone" / "results.json").read_text(encoding="utf-8"))
    out = {}
    for r in rows:
        key = "DC" if r["f"] < 1e4 else "HF"
        if key == "HF" and r["level"] not in ("13 x 7", "13 x 1"):
            continue
        out[(round(r["t_um"], 3), key)] = r["L_nH"]
    return out


def fh_plane() -> dict:
    """{(t_um, 'DC' | 'HF', plane): L' in nH/mm}."""
    rows = json.loads((fh.DATA / "plane" / "results.json").read_text(encoding="utf-8"))
    return {(round(p["t_um"], 3), "DC" if p["f"] < 1e4 else "HF", p["plane"]): p["Lp_nH_per_mm"]
            for p in fh.per_length(rows)}


# ================================================================================================
# The numbers of the note
# ================================================================================================
def pct(a: float, b: float) -> str:
    return f"{100 * (a / b - 1):+.2f} %"


def numbers() -> None:
    print("== Section 3: a trace 2.8 mm long and 0.2 mm wide with no plane beneath it")
    l0 = l_strip(L_ALONE, W)
    g0 = gmd_strip(W)
    print(f"Eq. (4) of the side note, strip without thickness: {l0:.4f} nH; g = 0.2 exp(-1.5) = {g0:.5f} mm")
    alone = fh_alone()
    lb35 = l_bar(L_ALONE, W, 0.035)
    for t in COPPER:
        g = gmd_rect(W, t)
        lb = l_bar(L_ALONE, W, t)
        est = l0 - MU0_2PI * L_ALONE * math.log(g / g0)
        print(f"  t = {t * 1e3:g} um ({OZ[t]}): g = {g:.5f} mm = {g / (W + t):.5f} (w + t); "
              f"ln(g/g0) = {math.log(g / g0):.5f}; Eq. (4) of this note: {l0:.4f} - 0.2 x 2.8 x {math.log(g / g0):.5f} "
              f"= {est:.4f} nH; Eq. (2): {lb:.4f} nH ({pct(lb, lb35)} vs 1 oz); "
              f"FastHenry DC {alone[(t * 1e3, 'DC')]:.4f} nH ({pct(alone[(t * 1e3, 'DC')], lb)} vs Eq. (2)); "
              f"308 MHz {alone[(t * 1e3, 'HF')]:.4f} nH")
    for key in ("DC", "HF"):
        ref = alone[(35.0, key)]
        txt = ", ".join(f"{t:g} um {pct(alone[(t, key)], ref)}" for t in (1.0, 17.5, 70.0))
        print(f"  FastHenry {key} against 35 um: {txt}")
    print(f"  FastHenry, DC to 308 MHz: " + ", ".join(
        f"{t:g} um {pct(alone[(t, 'HF')], alone[(t, 'DC')])}" for t in (1.0, 17.5, 35.0, 70.0)))
    for l in (2.8, 20.0):
        rel = [math.log(gmd_rect(W, t) / g0) / (math.log(2 * l / g0) - 1) for t in COPPER]
        print(f"  long-trace estimate of -dL/L from zero thickness, l = {l:g} mm: "
              + ", ".join(f"{t * 1e3:g} um {100 * r:.2f} %" for t, r in zip(COPPER, rel)))

    print("\n== Section 4: over a plane, w = 0.2 mm, h = 0.2 mm")
    w, h = W, fh.GAP
    plane = fh_plane()
    for t in (0.0, 0.0175, 0.035, 0.070):
        dw = width_correction(w, h, t)
        lp = lp_microstrip(w, h, t)
        tu = 1.0 if t == 0 else t * 1e3
        fhv = plane.get((tu, "HF", "standard"))
        fhs = f"FastHenry 308 MHz {fhv:.5f} nH/mm ({pct(fhv, lp)} vs Eq. (6))" if fhv else ""
        print(f"  t = {t * 1e3:g} um: dW = {dw * 1e3:.2f} um, u1 = {(w + dw) / h:.4f}, L' = {lp:.5f} nH/mm "
              f"({pct(lp, lp_microstrip(w, h, 0.035))} vs 1 oz); {fhs}")
    if plane:
        ref = plane[(35.0, "HF", "standard")]
        print("  FastHenry at 308 MHz against 35 um: " + ", ".join(
            f"{t:g} um {pct(plane[(t, 'HF', 'standard')], ref)}" for t in (1.0, 17.5, 70.0)))
        for kind in ("coarse", "wide"):
            if (35.0, "HF", kind) in plane:
                print(f"  35 um, {kind} plane: {plane[(35.0, 'HF', kind)]:.5f} nH/mm ({pct(plane[(35.0, 'HF', kind)], ref)})")
        dc = {t: plane.get((t, "DC", "standard")) for t in (17.5, 35.0, 70.0)}
        if all(dc.values()):
            print("  DC (return spread over the 4-mm plane): " + ", ".join(
                f"{t:g} um {v:.5f} nH/mm" for t, v in dc.items())
                  + f"; 70 vs 35 um {pct(dc[70.0], dc[35.0])}")
    # the substitution of Eqs. (6)-(7) for 1 oz
    t = 0.035
    coth = 1.0 / math.tanh(math.sqrt(6.517 * w / h))
    dw = width_correction(w, h, t)
    u1 = (w + dw) / h
    fu = 6 + (2 * math.pi - 6) * math.exp(-(30.666 / u1) ** 0.7528)
    print(f"  substitution, 1 oz: t/h = {t / h:.4f}; sqrt(6.517 w/h) = {math.sqrt(6.517 * w / h):.4f}; "
          f"coth^2 = {coth ** 2:.4f}; 4e/(t/h coth^2) = {4 * math.e / (t / h * coth ** 2):.3f}; "
          f"t/pi = {t / math.pi * 1e3:.3f} um; ln(1 + ...) = {math.log(1 + 4 * math.e / (t / h * coth ** 2)):.4f}; "
          f"dW = {dw * 1e3:.2f} um; W1/h = {u1:.4f}; f_u = {fu:.5f}; f_u h/W1 = {fu / u1:.4f}; "
          f"sqrt(1 + (2h/W1)^2) = {math.sqrt(1 + (2 / u1) ** 2):.4f}; ln = {math.log(fu / u1 + math.sqrt(1 + (2 / u1) ** 2)):.4f}")
    print("  other stack-ups (closed form), L' in nH/mm for 1/2, 1, 2 oz; 1 oz with h halved and with w doubled:")
    for w2, h2 in ((0.2, 0.2), (0.3, 0.2), (0.2, 0.1), (0.3, 1.5), (3.0, 0.1)):
        v = [lp_microstrip(w2, h2, t) for t in COPPER]
        print(f"    w {w2:g} mm, h {h2:g} mm: " + ", ".join(f"{x:.4f}" for x in v)
              + f"; 1 -> 2 oz {pct(v[2], v[1])}; 0 -> 1 oz {pct(v[1], lp_microstrip(w2, h2, 0.0))}; "
              f"h halved {pct(lp_microstrip(w2, h2 / 2, 0.035), v[1])}; w doubled {pct(lp_microstrip(2 * w2, h2, 0.035), v[1])}")

    print("\n== Section 5: the copper's own inductance")
    for f in (1e6, 1e7, 3.08e8):
        print(f"  skin depth at {f / 1e6:g} MHz: {skin_depth_um(f):.2f} um")
    for t in COPPER:
        f_eq = RHO / (math.pi * MU0 * (t * 1e-3) ** 2)
        print(f"  {OZ[t]}: skin depth = thickness at {f_eq / 1e6:.2f} MHz; added height "
              + ", ".join(f"{f / 1e6:g} MHz {added_height_um(t * 1e3, f):.2f}" for f in (1e5, 1e6, 3e6, 1e7, 1e8, 3.08e8))
              + f" um; t/3 = {t * 1e3 / 3:.2f} um")
    d = skin_depth_um(1e8)
    print(f"  at 100 MHz: delta = {d:.2f} um; rho/delta = {RHO / (d * 1e-6) * 1e3:.2f} mOhm per square; "
          f"delta/2 for each of two conductors over a 0.2-mm gap: {2 * (d / 2) / 200 * 100:.2f} % of the gap")
    for t in COPPER:
        kt = (1 + 1j) * t * 1e3 / d
        print(f"    {OZ[t]}: t/delta = {t * 1e3 / d:.2f}; current density on the far face against the near face "
              f"|1/cosh(kt)| = {100 / abs(np.cosh(kt)):.2f} %; DC resistance per square rho/t = {RHO / (t * 1e-3) * 1e3:.3f} mOhm")
    for h in (0.1, 0.2):
        r = {t: 2 * t * 1e3 / 3 / (h * 1e3) for t in COPPER}
        print(f"  wide trace, gap {h:g} mm, both conductors alike, DC limit: "
              + ", ".join(f"{OZ[t]} +{100 * v:.1f} %" for t, v in r.items())
              + f"; 2 oz against 1 oz {100 * ((1 + r[0.070]) / (1 + r[0.035]) - 1):+.1f} %")

    print("\n== Section 6: the OPA846 design in SOIC-8 (side note, Section 4)")
    lx, traces, f_c, c_f = 10.14, 4.35, 308e6, 0.75e-12
    hf = fh_alone()
    drop = 1 - hf[(70.0, "HF")] / hf[(35.0, "HF")]
    rise = hf[(17.5, "HF")] / hf[(35.0, "HF")] - 1
    d1 = (2 * math.pi * f_c) ** 2 * lx * 1e-9 * c_f
    for label, frac in (("70 um", -drop), ("17.5 um", rise)):
        dl = traces * frac
        d1n = (2 * math.pi * f_c) ** 2 * (lx + dl) * 1e-9 * c_f
        print(f"  {label}: traces and vias change by at most {frac * 100:+.2f} % x {traces} nH = {dl:+.3f} nH; "
              f"delta_1 = {100 * d1:.3f} % -> {100 * d1n:.3f} % ({100 * (d1n - d1):+.3f} percentage points)")


# ================================================================================================
# Figures: Arial at 8 pt, a muted palette, ticks inside on all four sides, 600-dpi PNG and PDF
# ================================================================================================
COLORS = {"primary": "#385C9E", "warm_accent": "#9E403D", "cool_accent": "#477A57", "neutral": "#4D4D4D",
          "annotation": "#767676", "text": "#272727", "axes": "#000000", "background": "#FFFFFF"}


def configure_plot_style() -> None:
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "figure.facecolor": COLORS["background"], "axes.facecolor": COLORS["background"],
        "axes.edgecolor": COLORS["axes"], "axes.labelcolor": COLORS["text"], "text.color": COLORS["text"],
        "xtick.color": COLORS["axes"], "ytick.color": COLORS["axes"], "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "DejaVu Sans", "sans-serif"], "font.size": 8.0, "axes.labelsize": 8.0,
        "axes.titlesize": 8.0, "xtick.labelsize": 8.0, "ytick.labelsize": 8.0, "legend.fontsize": 8.0,
        "axes.linewidth": 0.8, "axes.spines.top": True, "axes.spines.right": True, "xtick.top": True,
        "ytick.right": True, "xtick.direction": "in", "ytick.direction": "in", "legend.frameon": False,
        "axes.grid": False, "text.usetex": False, "mathtext.fontset": "cm", "axes.formatter.use_mathtext": True,
        "pdf.fonttype": 42, "ps.fonttype": 42, "savefig.facecolor": "white", "savefig.bbox": "tight"})


def save(fig, stem: str) -> None:
    import matplotlib.pyplot as plt
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / f"{stem}.png", dpi=600)
    fig.savefig(FIG / f"{stem}.pdf")
    plt.close(fig)
    print(f"wrote {FIG / stem}.png and .pdf")


def figure_thickness() -> None:
    """Figure 1: inductance against copper thickness, relative to 35 um, for the trace alone at DC and
    308 MHz and for the trace over the plane at 308 MHz; lines are closed forms, points FastHenry."""
    import matplotlib.pyplot as plt
    configure_plot_style()
    alone, plane = fh_alone(), fh_plane()
    fig, ax = plt.subplots(figsize=(4.2, 3.24), constrained_layout=True)
    ts = np.linspace(0.001, 0.080, 80)
    lb35 = l_bar(L_ALONE, W, 0.035)
    l0 = l_strip(L_ALONE, W)
    g0 = gmd_strip(W)
    shift = lambda t: l0 - MU0_2PI * L_ALONE * math.log(gmd_rect(W, t) / g0)  # noqa: E731  (Eq. (4))
    bar = np.array([shift(t) for t in ts])
    ax.plot(ts * 1e3, 100 * (bar / shift(0.035) - 1), color=COLORS["primary"], lw=1.5,
            label="Alone, uniform current: Eq. (4)")
    ms35 = lp_microstrip(W, fh.GAP, 0.035)
    ms = np.array([lp_microstrip(W, fh.GAP, t) for t in ts])
    ax.plot(ts * 1e3, 100 * (ms / ms35 - 1), color=COLORS["cool_accent"], lw=1.5,
            label="Over the plane: Eqs. (6)–(8)")
    tk = [1.0, 17.5, 35.0, 70.0]
    ax.plot(tk, [100 * (alone[(t, "DC")] / alone[(35.0, "DC")] - 1) for t in tk], "o", color=COLORS["primary"],
            ms=4, label="Alone, DC: FastHenry")
    ax.plot(tk, [100 * (alone[(t, "HF")] / alone[(35.0, "HF")] - 1) for t in tk], "s", color=COLORS["warm_accent"],
            ms=4, ls=(0, (5, 2)), lw=1.5, label="Alone, 308 MHz: FastHenry")
    if plane:
        ax.plot(tk, [100 * (plane[(t, "HF", "standard")] / plane[(35.0, "HF", "standard")] - 1) for t in tk], "^",
                color=COLORS["cool_accent"], ms=4.5, label="Over the plane, 308 MHz: FastHenry")
    ax.axhline(0, color=COLORS["annotation"], lw=0.6, zorder=0)
    ax.set_xticks([0, 17.5, 35, 70])
    ax.set_xticklabels(["0", "17.5\n(½ oz)", "35\n(1 oz)", "70\n(2 oz)"])
    ax.set_xlim(-2, 80)
    ax.set_xlabel(r"Copper thickness, $t$ (µm)")
    ax.set_ylabel("Inductance against 35-µm copper (%)")
    ax.legend(loc="upper right")
    save(fig, "fig1_thickness")


def figure_internal() -> None:
    """Figure 2: the height that one conductor adds to the gap of a wide trace, Eqs. (8)-(9), against
    frequency, for 1/2, 1 and 2 oz copper, with the thick-copper limit delta/2."""
    import matplotlib.pyplot as plt
    from matplotlib.ticker import LogFormatterMathtext
    configure_plot_style()
    fig, ax = plt.subplots(figsize=(4.2, 3.24), constrained_layout=True)
    f = np.logspace(4, 9, 300)
    for t, c in zip(COPPER, (COLORS["primary"], COLORS["warm_accent"], COLORS["cool_accent"])):
        ax.plot(f, [added_height_um(t * 1e3, x) for x in f], color=c, lw=1.5,
                label=f"{t * 1e3:g} µm ({OZ[t].replace('1/2', '½')})")
    ax.plot(f, [skin_depth_um(x) / 2 for x in f], color=COLORS["neutral"], lw=1.5, ls=(0, (5, 2)),
            label=r"$\delta/2$, thick copper")
    ax.set_xscale("log")
    ax.xaxis.set_major_formatter(LogFormatterMathtext())
    ax.set_xlim(1e4, 1e9)
    ax.set_ylim(0, 26)
    ax.set_xlabel(r"Frequency, $f$ (Hz)")
    ax.set_ylabel("Height added to the gap (µm)")
    ax.legend(loc="upper right")
    save(fig, "fig2_internal")


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "numbers"
    if what == "numbers":
        numbers()
    elif what == "figures":
        figure_thickness()
        figure_internal()
    else:
        sys.exit(f"unknown command {what!r}; use numbers or figures")
