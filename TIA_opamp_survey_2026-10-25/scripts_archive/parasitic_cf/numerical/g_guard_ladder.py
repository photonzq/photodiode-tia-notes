"""The guarded feedback networks as distributed RC lines: the feedback impedance against frequency.

Usage:
    python g_guard_ladder.py list
    python g_guard_ladder.py run <case> [--record <json>]
    python g_guard_ladder.py response <record json> [--figure <stem>]     (no solve)

Why this script exists
----------------------
In the guard layouts of g_eight_lead_3d.py (ADA4530-1, LMP7721, LMC6001 with guard rings), as in the
layouts the amplifiers' makers publish, the guard passes under the feedback resistor between its
pads.  The guard then couples to the film, and the field solutions of g_eight_lead_3d.py, which hold
the film at its DC potential, give only the first-order feedback capacitance (pcbcap.distributed,
module docstring).  This script computes the feedback impedance at all frequencies with the film
divided into n = 10 finite elements, from the capacitance matrix of their hat functions
(pcbcap.distributed), for the three guarded layouts and, for comparison, the unguarded PDIP-8 layout.

Each case meshes the layout of g_eight_lead_3d.py with its film split into 10 sub-films (n = 8 would
put a division 12.5 um from another plane, which pcbcap.meshing would take as the smallest feature),
at the mesh level of that script, and solves the 11 fields of capacitance.maxwell_matrix over the
node nets.  The record holds the 11 x 11 capacitance matrix (fF); "response" evaluates the feedback
impedance from it, which needs no solve.

The response is evaluated for R_F = 1 GOhm.  Everything depends on omega R_F only (the capacitances
are fixed), so for another R_F the frequencies scale as 1 / R_F.  For each case "response" gives:
  * the lumped first-order corner f_1 = 1 / (2 pi R_F C_F), with C_F = -v^T C u (pcbcap.distributed,
    the same value as capacitance.two_port on this mesh);
  * C_g, the film's capacitance to the grounded conductors (guard, supply and +IN pins, enclosure),
    taken as n / (n - 1) times the row sums of the n - 1 inner nodes, which is exact for a uniform
    film, where each inner node carries C_g / n and each end node C_g / (2n); and |theta| at f_1,
    sqrt(omega_1 R_F C_g) = sqrt(C_g / C_F), the electrical length of the high-gain note's Section 3.4;
  * the frequency where |Z_F| falls to R_F / sqrt(2), f_3dB, and the largest |Z_F| / R_F (above 1
    means the response peaks);
  * at f_1 and 3 f_1: |Z_F| and its phase against the lumped model R_F / (1 + j omega R_F C_F), and
    y_F written as G + j omega C: G R_F and the effective capacitance C;
  * the film's noise, Re{y_11} R_F, the ratio of its noise power to that of a lumped resistor
    (pcbcap.distributed, Eq. (6)): its value at f_1 and 3 f_1, and its mean from 0 to f_3dB;
  * for each number, the estimated error of ten elements: the same number from five elements, whose
    capacitance matrix follows exactly from the ten-element one (pcbcap.distributed.coarsen), and
    Richardson's rule, error = (five - ten) / 3 for an error that falls as 1/n^2.  Against the exact
    uniform RC line this estimate matches the true error (pcbcap.checks, uniform_rc_line).  The
    curves of the figure end where the estimated error of |Z_F| or of the noise reaches 2 %: above
    that frequency the film's potential varies within one element and ten elements no longer
    resolve it.
"--out" writes these numbers (without the curves) to a JSON file.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import replace
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[4] / "pcbcap"))

import numpy as np                                         # noqa: E402

from pcbcap import distributed as dist                    # noqa: E402
from pcbcap import study                                  # noqa: E402
from pcbcap.fem import Problem                            # noqa: E402
from pcbcap.meshing import build_mesh                     # noqa: E402

import g_eight_lead_3d as g8                              # noqa: E402

N_ELEMENTS = 10
R_F = 1e9
CASES = ("lmc6001_dip8_bottom_1206", "lmc6001_dip8_bottom_guard_1206", "ada4530_so8_1206", "lmp7721_so8_1206")
LABELS = {"lmc6001_dip8_bottom_1206": "LMC6001, PDIP-8, no guard",
          "lmc6001_dip8_bottom_guard_1206": "LMC6001, PDIP-8, guard rings",
          "ada4530_so8_1206": "ADA4530-1, SOIC-8, guard",
          "lmp7721_so8_1206": "LMP7721, SOIC-8, guard"}


def run(name: str, record: str | None) -> dict:
    d = g8.LAYOUTS[name]
    level = d.get("level", g8.LEVEL[d["mesh"]])
    t0 = time.perf_counter()
    lay, nodes = dist.split_film(g8.build(name), N_ELEMENTS)
    md = build_mesh(lay, replace(g8.BASE, refine=level, max_elements=g8.MAX_ELEMENTS))
    prob = Problem(lay, md, order=2)
    res = dist.ladder(prob, nodes)
    out_end = "hi" if nodes[-1] == "A" else "lo"          # which end of the film is the output, net A
    res.update(case=name, title=d["title"], n=N_ELEMENTS, level=level, output_end=out_end,
               elements=int(md.stats["elements"]), seconds=time.perf_counter() - t0)
    print(f"[{name}] {d['title']}, n = {N_ELEMENTS}, refine {level}: {res['elements']} elements, "
          f"{res['seconds']:.0f} s; first-order C_F = {res['C_F_dc']:.2f} fF; output end {out_end}")
    if record:
        p = Path(record)
        data = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
        data[name] = res
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data, indent=1, default=float), encoding="utf-8", newline="\n")
    return res


def _crossing(f, y, level, rising):
    """The first frequency where y crosses ``level`` (upwards if rising), interpolated in log f; None
    if it never does."""
    hit = y >= level if rising else y < level
    if not hit.any() or hit[0]:
        return None
    k = int(np.argmax(hit))
    t = (level - y[k - 1]) / (y[k] - y[k - 1])          # linear in y between the two samples
    return float(np.exp(np.log(f[k - 1]) + t * (np.log(f[k]) - np.log(f[k - 1]))))


F_PLOT = np.logspace(1.0, np.log10(3e5), 401)      # the figure's common grid, 10 Hz - 300 kHz at 1 GOhm
MAX_ERROR = 0.02                                   # the curves end where the estimated error reaches 2 %


def _model(C, end, f):
    """Z_F / R_F and the noise power Re{y_11} R_F of one capacitance matrix at the frequencies f."""
    z = 1.0 / (dist.feedback_admittance(C, R_F, f, output_end=end) * R_F)
    noise = (dist.input_admittance(C, R_F, f, output_end=end) * R_F).real
    return z, noise


def _numbers(C, end, cf, f1):
    """f_3dB, the peak, the values at f_1 and 3 f_1 and the mean noise up to f_3dB for one matrix."""
    f = np.logspace(np.log10(f1) - 2, np.log10(f1) + 1, 301)
    z, noise = _model(C, end, f)
    mag = np.abs(z)
    f3 = _crossing(f, mag, 1 / np.sqrt(2), rising=False)
    fb = np.linspace(0.0, f3, 2001)                                          # 0 .. f_3dB, linear grid
    nb = _model(C, end, fb)[1]
    at = {}
    for mult in (1.0, 3.0):
        zz, nn = _model(C, end, [mult * f1])
        y = 1.0 / zz[0]                                                      # y_F R_F = G R_F + j w R_F C
        at[f"{mult:g} f1"] = dict(mag=float(abs(zz[0])), phase_deg=float(np.degrees(np.angle(zz[0]))),
                                  G_eff=float(y.real), C_eff_fF=float(y.imag * cf / mult), noise=float(nn[0]))
    return dict(f3dB=f3, peak=float(mag.max()), f_peak=float(f[int(np.argmax(mag))]), at=at,
                noise_mean_to_f3dB=float(np.trapezoid(nb, fb) / f3))


def evaluate(r: dict) -> dict:
    """The numbers of the module docstring for one record (no solve), each with the error estimate
    of distributed.coarsen: the same quantity from 5 elements, and (5 - 10) / 3 as the error of 10
    elements (Richardson, error ~ 1/n^2).  The curves are on the common grid F_PLOT and end where the
    estimated error of |Z_F| or of the noise reaches MAX_ERROR."""
    C = np.array(r["C"])
    C5 = dist.coarsen(C, 2)
    end = r["output_end"]
    n = len(C) - 1
    cf = r["C_F_dc"]
    f1 = 1.0 / (2 * np.pi * R_F * cf * 1e-15)
    a, b = _numbers(C, end, cf, f1), _numbers(C5, end, cf, f1)

    def err(x10, x5):
        return abs(x5 - x10) / 3 / abs(x10)

    out = dict(C_F_dc=cf, f1=f1, f3dB=a["f3dB"], f3dB_over_f1=a["f3dB"] / f1, err_f3dB=err(a["f3dB"], b["f3dB"]),
               peak=a["peak"], f_peak=a["f_peak"], err_peak=err(a["peak"], b["peak"]),
               noise_mean_to_f3dB=a["noise_mean_to_f3dB"],
               err_noise_mean=err(a["noise_mean_to_f3dB"], b["noise_mean_to_f3dB"]), at={})
    for key in a["at"]:
        q10, q5 = a["at"][key], b["at"][key]
        out["at"][key] = dict(q10, **{f"err_{k}": err(q10[k], q5[k]) for k in ("mag", "G_eff", "C_eff_fF", "noise")})
        out["at"][key]["err_phase_deg"] = abs(q5["phase_deg"] - q10["phase_deg"]) / 3
        mult = float(key.split()[0])
        out["at"][key]["mag_lumped"] = float(1 / np.sqrt(1 + mult ** 2))
        out["at"][key]["phase_lumped_deg"] = float(-np.degrees(np.arctan(mult)))
    ground = np.array(r["ground"])
    out["C_g"] = float(ground[1:-1].sum() * n / (n - 1))
    out["theta_f1"] = float(np.sqrt(out["C_g"] / cf))
    z, noise = _model(C, end, F_PLOT)
    z5, noise5 = _model(C5, end, F_PLOT)
    e = np.maximum(np.abs(z5 - z) / 3 / np.abs(z), np.abs(noise5 - noise) / 3 / noise)
    bad = e > MAX_ERROR
    out["f_valid"] = float(F_PLOT[int(np.argmax(bad))]) if bad.any() else None
    keep = ~np.logical_or.accumulate(bad)
    zl = 1.0 / (1.0 + 1j * F_PLOT / f1)                                      # lumped, first order
    out["curve"] = dict(f=F_PLOT.tolist(), z_re=np.where(keep, z.real, np.nan).tolist(),
                        z_im=np.where(keep, z.imag, np.nan).tolist(), noise=np.where(keep, noise, np.nan).tolist(),
                        zl_re=zl.real.tolist(), zl_im=zl.imag.tolist())
    return out


def response(record: str, figure: str | None = None, out_json: str | None = None) -> dict:
    data = json.loads(Path(record).read_text(encoding="utf-8"))
    eight = json.loads((Path(record).parent / "eight_lead_3d.json").read_text(encoding="utf-8"))
    out = {}
    for name in CASES:
        if name not in data:
            continue
        o = evaluate(data[name])
        o["C_F_eight_lead"] = eight.get(name, {}).get("table", {}).get("C_F")
        out[name] = o
        a1, a3 = o["at"]["1 f1"], o["at"]["3 f1"]
        fv = f"{o['f_valid']:.3g} Hz ({o['f_valid'] / o['f1']:.2f} f_1)" if o["f_valid"] else "beyond the grid"
        print(f"{LABELS[name]}: C_F (first order) {o['C_F_dc']:.2f} fF on this mesh, {o['C_F_eight_lead']:.2f} fF in "
              f"eight_lead_3d.json; C_g {o['C_g']:.1f} fF, |theta| at f_1 {o['theta_f1']:.2f}")
        print(f"   f_1 = {o['f1']:.0f} Hz, f_3dB = {o['f3dB']:.0f} Hz ({o['f3dB_over_f1']:.3f} f_1, est. error "
              f"{o['err_f3dB']:.1e}) at R_F = 1 GOhm; largest |Z_F|/R_F {o['peak']:.4f} at {o['f_peak']:.3g} Hz "
              f"(est. error {o['err_peak']:.1e}); estimated error below 2 % up to {fv}")
        for key, a in (("f_1", a1), ("3 f_1", a3)):
            print(f"   at {key}: |Z_F|/R_F {a['mag']:.3f} ({a['err_mag']:.1e}; lumped {a['mag_lumped']:.3f}), phase "
                  f"{a['phase_deg']:.1f} deg ({a['err_phase_deg']:.2f} deg; lumped {a['phase_lumped_deg']:.1f}); "
                  f"G R_F {a['G_eff']:.3f} ({a['err_G_eff']:.1e}), C {a['C_eff_fF']:.1f} fF ({a['err_C_eff_fF']:.1e}); "
                  f"noise Re(y_11) R_F {a['noise']:.3f} ({a['err_noise']:.1e})")
        print(f"   mean noise power from 0 to f_3dB {o['noise_mean_to_f3dB']:.3f} "
              f"({10 * np.log10(o['noise_mean_to_f3dB']):.2f} dB; est. error {o['err_noise_mean']:.1e})")
    if out_json:
        slim = {k: {a: b for a, b in v.items() if a != "curve"} for k, v in out.items()}
        p = Path(out_json)
        p.write_text(json.dumps(dict(R_F=R_F, n=N_ELEMENTS, cases=slim), indent=1), encoding="utf-8", newline="\n")
        print("wrote", p.name)
    if figure:
        draw(out, figure)
    return out


def draw(out: dict, stem: str) -> None:
    """Three panels against frequency at R_F = 1 GOhm, one colour per layout: (a) |Z_F| / R_F and (b)
    the phase of Z_F, with the film in ten elements (solid) and the lumped first-order model R_F || C_F
    (dashed); (c) the film's noise power relative to a lumped resistor, Re{y_11} R_F, which the lumped
    model holds at 1 (grey, dashed).  The solid curves end where the estimated error of ten elements
    reaches MAX_ERROR (evaluate)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.ticker import LogFormatterMathtext
    from pcbcap import plotting
    plotting.use_style()
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(4.2, 6.2), sharex=True, constrained_layout=True)
    colours = plotting.COLOR_CYCLE
    grey = plotting.COLORS["neutral"]
    for k, (name, o) in enumerate(out.items()):
        f = np.array(o["curve"]["f"])
        z = np.array(o["curve"]["z_re"]) + 1j * np.array(o["curve"]["z_im"])
        zl = np.array(o["curve"]["zl_re"]) + 1j * np.array(o["curve"]["zl_im"])
        c = colours[k % len(colours)]
        ax1.plot(f, np.abs(z), color=c, lw=1.5, label=f"{LABELS[name]}")
        ax1.plot(f, np.abs(zl), color=c, lw=1.5, ls=plotting.DASHED)
        ax2.plot(f, np.degrees(np.angle(z)), color=c, lw=1.5)
        ax2.plot(f, np.degrees(np.angle(zl)), color=c, lw=1.5, ls=plotting.DASHED)
        ax3.plot(f, o["curve"]["noise"], color=c, lw=1.5)
    ax3.axhline(1.0, color=grey, lw=1.5, ls=plotting.DASHED)
    ax1.set_xscale("log")
    ax1.set_yscale("log")
    ax1.set_ylim(1e-2, 2.0)
    ax1.set_ylabel(r"$|Z_F|\,/\,R_F$")
    ax1.yaxis.set_major_formatter(LogFormatterMathtext())
    ax1.legend(loc="lower left")
    ax2.set_ylabel(r"Phase of $Z_F$ (deg)")
    ax2.set_ylim(-95, 5)
    ax2.set_yticks([-90, -60, -30, 0])
    ax2.legend(handles=[Line2D([], [], color=grey, lw=1.5, label="film in ten elements"),
                        Line2D([], [], color=grey, lw=1.5, ls=plotting.DASHED,
                               label=r"lumped $R_F\parallel C_F$, first-order $C_F$")], loc="lower left")
    ax3.set_ylabel(r"Noise power, $R_F\,\mathrm{Re}\{y_{11}\}$")
    ax3.set_ylim(0.95, 1.65)
    ax3.set_xlabel(r"Frequency at $R_F$ = 1 G$\Omega$ (Hz)")
    ax3.xaxis.set_major_formatter(LogFormatterMathtext())
    for ax, letter in zip((ax1, ax2, ax3), "abc"):
        ax.set_title(f"({letter})", loc="left")      # above the axes, where no curve can run into it
    plotting.export(fig, stem)


def main() -> int:
    study.lower_priority(2)
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    r = sub.add_parser("run")
    r.add_argument("name")
    r.add_argument("--record", default=None)
    s = sub.add_parser("response")
    s.add_argument("record")
    s.add_argument("--figure", default=None)
    s.add_argument("--out", default=None)
    a = ap.parse_args()
    if a.cmd == "list":
        for k in CASES:
            print(f"{k:32s} {LABELS[k]}")
    elif a.cmd == "run":
        run(a.name, a.record)
    else:
        response(a.record, a.figure, a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
