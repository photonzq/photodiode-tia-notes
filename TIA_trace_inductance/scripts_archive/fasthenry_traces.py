"""FastHenry runs for the side note TIA_trace_inductance: traces 0.2 mm wide of 17.5, 35 and 70 um
copper, alone and 0.2 mm above a plane, at DC and at 308 MHz.

Usage (from this folder):
    python fasthenry_traces.py run alone|plane|all
    python fasthenry_traces.py report        # writes ../data/fasthenry/README.md

Why this script exists
----------------------
The note asks how much the copper's thickness changes the inductance of a trace.  Its closed forms
(trace_thickness.py) are the partial self-inductance of a bar that carries a uniform current and, over
a plane, the microstrip formula of Hammerstad and Jensen with its thickness correction.  FastHenry
(FastFieldSolvers' build FastHenry2 of the MIT program; FastHenry User's Guide, version 3.0) solves the
same problems with every conductor cut into filaments, so at high frequency it also computes what the
closed forms leave out: the current crowding to the edges and to the face that looks at the plane, and
the return current in the plane.  Two groups:
  * alone: a trace 2.8 mm long and 0.2 mm wide, the longest trace of Table C.1 of the side note
    TIA_feedback_layouts, 1, 17.5, 35 and 70 um thick.  At DC (1 kHz, one filament: a uniform current)
    it is the bar of the note's Eq. (2); at 308 MHz, the loop crossover of the balanced-photodiode
    note's OPA846 design, it is cut into 9 x 5 and 13 x 7 filaments across its width and thickness,
    each half as wide as its inner neighbour, as the side note's Appendix C does.  The 1-um strip
    stands for a strip without thickness: one filament at DC, 13 across its width at 308 MHz.
  * plane: the same trace with its lower face 0.2 mm above the top face of a plane, 3 and 6 mm long.
    The difference of the two loop inductances, divided by 3 mm, is the inductance per unit length L'
    without the ends.  The plane is a copper sheet 2 um thick, 10 mm long and 4 mm wide, cut into cells
    0.5 mm along the trace and 0.05 mm across it (seg1 = 20, seg2 = 80).  At 308 MHz it acts as the
    ideal plane of the microstrip formula: the sheet's resistance is about 2 % of the reactance of the
    return path, and the field inside the sheet adds less than 0.5 % to L'.  The port lies between the
    trace's near end and the plane node below it; the far end is joined to the plane node below it by
    an ideal short (.equiv), so neither end has a vertical conductor, and both cancel in the difference.
    Checks for the 35-um trace: a plane with cells 0.1 mm across (seg2 = 40) and a plane 8 mm wide
    (seg2 = 160).  At DC the return current spreads over the whole plane, so L' at DC describes this
    plane rather than a microstrip line.
Every conductor is copper, rho = 1.7e-8 ohm m, as in the side note's Appendix C.  Each run is one
FastHenry2 input at one frequency, run through FastHenry2's automation interface (the same calls as the
side note's fasthenry_validation.py); the inputs, the impedance matrices (Zc_<run>.mat) and the results
are kept in ../data/fasthenry/.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve()
DATA = HERE.parents[1] / "data" / "fasthenry"
RHO = 1.7e-8                                  # ohm m, as the side note's Appendix C
SIGMA_MM = 1.0 / RHO * 1e-3                   # 1/(ohm mm): FastHenry's unit of conductivity with .units mm
F_DC, F_HF = 1e3, 308e6                       # "DC" (uniform current) and the OPA846 design's crossover
LEVELS = [(9, 5), (13, 7)]                    # filaments across width and thickness, ratio 2
W = 0.2                                       # mm, the trace's width (Table C.1 of the side note)
COPPER = [0.0175, 0.035, 0.070]               # mm: 1/2, 1 and 2 oz copper
THIN = 0.001                                  # mm, the strip without thickness
L_ALONE = 2.8                                 # mm, the longest trace of Table C.1
GAP = 0.2                                     # mm, from the plane's top face to the trace's lower face
LENGTHS = (3.0, 6.0)                          # mm, the two traces over the plane
X0 = 2.0                                      # mm, where the traces start on the plane
SHEET = 0.002                                 # mm, the plane's thickness
PLANES = {                                    # name: (length, width, seg1, seg2), mm
    "standard": (10.0, 4.0, 20, 80),
    "coarse": (10.0, 4.0, 20, 40),
    "wide": (10.0, 8.0, 20, 160),
}


def skin_depth_mm(f: float) -> float:
    """delta = sqrt(2 rho / (omega mu0)), in mm."""
    return math.sqrt(2 * RHO / (2 * math.pi * f * 4e-7 * math.pi)) * 1e3


# ================================================================================================
# Writing FastHenry input
# ================================================================================================
class Model:
    """A FastHenry input with millimetre units and copper by default."""

    def __init__(self, title: str):
        self.lines = [f"* {title}", ".units mm", f".default sigma={SIGMA_MM:.6g}"]
        self.n_nodes = 0

    def node(self, x: float, y: float, z: float) -> str:
        name = f"N{self.n_nodes}"
        self.n_nodes += 1
        self.lines.append(f"{name} x={x:.9g} y={y:.9g} z={z:.9g}")
        return name

    def trace(self, x0: float, x1: float, z: float, t: float, level) -> tuple[str, str]:
        """A trace along x from x0 to x1, width W across y, thickness t, its centre plane at z."""
        a, b = self.node(x0, 0.0, z), self.node(x1, 0.0, z)
        self.lines.append(f"E0 {a} {b} w={W:.9g} h={t:.9g} nwinc={level[0]} nhinc={level[1]} rw=2 rh=2")
        return a, b

    def plane(self, name: str, kind: str, z: float, taps: dict) -> None:
        """A uniformly discretised plane (FastHenry guide, p. 15) from x = 0 along the trace, centred on
        y = 0, its centre plane at z, with the named nodes ``taps`` {name: (x, y)} on it (p. 16)."""
        length, width, s1, s2 = PLANES[kind]
        s = (f"G{name} x1=0 y1={-width / 2:.9g} z1={z:.9g} x2={length:.9g} y2={-width / 2:.9g} z2={z:.9g} "
             f"x3={length:.9g} y3={width / 2:.9g} z3={z:.9g} thick={SHEET:.9g} sigma={SIGMA_MM:.6g} "
             f"seg1={s1} seg2={s2}")
        for tap, (x, y) in taps.items():
            s += f"\n+ {tap} ({x:.9g},{y:.9g},{z:.9g})"
        self.lines.append(s)

    def equiv(self, *nodes: str) -> None:
        self.lines.append(".equiv " + " ".join(nodes))

    def text(self, a: str, b: str, f: float) -> str:
        return "\n".join(self.lines + [f".external {a} {b} port", f".freq fmin={f:.9g} fmax={f:.9g} ndec=1",
                                       ".end"]) + "\n"


# ================================================================================================
# Running FastHenry2 and reading Zc.mat (as fasthenry_validation.py of the side note)
# ================================================================================================
_ZC = re.compile(r"Impedance matrix for frequency = ([0-9.eE+-]+) (\d+) x (\d+)\s*\n(.*?)(?=Impedance matrix|\Z)", re.S)


def read_zc(path: Path) -> list[tuple[float, complex]]:
    """(frequency, Z of the first port) for every matrix in a Zc.mat file (FastHenry guide, Section 2.2)."""
    out = []
    for m in _ZC.finditer(path.read_text()):
        f = float(m.group(1))
        first = m.group(4).strip().splitlines()[0]
        nums = re.findall(r"[-+]?[0-9.]+(?:[eE][-+]?\d+)?j?", first.replace(" ", ""))
        out.append((f, complex(float(nums[0]), float(nums[1].rstrip("j")))))
    return out


def run(folder: Path, name: str, text: str, timeout: float = 1800.0) -> dict:
    """Write ``name``.inp, run it in FastHenry2 (automation object FastHenry2.Document, its Run method
    with a command line), and return R (ohm) and L (nH) at the input's one frequency."""
    import win32com.client
    folder.mkdir(parents=True, exist_ok=True)
    inp = folder / f"{name}.inp"
    inp.write_text(text, encoding="ascii", newline="\n")
    zc = folder / f"Zc_{name}.mat"
    if zc.exists():
        zc.unlink()
    fh = win32com.client.Dispatch("FastHenry2.Document")
    t0 = time.perf_counter()
    try:
        if not fh.Run(f'"{inp}" -S _{name}'):
            raise RuntimeError("FastHenry2 did not start")
        while fh.IsRunning:
            if time.perf_counter() - t0 > timeout:
                fh.Stop()
                raise TimeoutError(f"{name}: no result within {timeout:g} s")
            time.sleep(0.2)
    finally:
        try:
            fh.Quit()
        except Exception:
            pass
    dt = time.perf_counter() - t0
    if not zc.exists():
        raise FileNotFoundError(f"{name}: FastHenry2 wrote no {zc.name}")
    f, z = read_zc(zc)[0]
    return dict(f=f, R_ohm=z.real, L_nH=z.imag / (2 * math.pi * f) * 1e9, seconds=dt)


# ================================================================================================
# The groups
# ================================================================================================
def group_alone(folder: Path) -> list[dict]:
    rows = []
    cases = [(THIN, F_DC, (1, 1)), (THIN, F_HF, (13, 1))]
    for t in COPPER:
        cases += [(t, F_DC, (1, 1))] + [(t, F_HF, lev) for lev in LEVELS]
    for t, f, lev in cases:
        m = Model(f"trace {L_ALONE} mm x {W} mm x {t * 1e3:g} um, alone")
        a, b = m.trace(0.0, L_ALONE, 0.0, t, lev)
        r = run(folder, f"alone_{t * 1e3:g}um_{f:.0e}_{lev[0]}x{lev[1]}", m.text(a, b, f))
        rows.append(dict(group="alone", t_um=t * 1e3, length_mm=L_ALONE, plane="", level=f"{lev[0]} x {lev[1]}", **r))
        print(f"  alone, {t * 1e3:g} um, {f:.3g} Hz, {lev}: {r['L_nH']:.4f} nH ({r['seconds']:.1f} s)")
    return rows


def group_plane(folder: Path) -> list[dict]:
    rows = []
    cases = [(t, F_HF, (13, 7), "standard") for t in COPPER] + [(THIN, F_HF, (13, 1), "standard")]
    cases += [(t, F_DC, (1, 1), "standard") for t in COPPER]
    cases += [(0.035, F_HF, (13, 7), "coarse"), (0.035, F_HF, (13, 7), "wide")]
    z_plane = -SHEET / 2                       # the sheet's top face at z = 0
    for t, f, lev, kind in cases:
        for length in LENGTHS:
            m = Model(f"trace {length} mm x {W} mm x {t * 1e3:g} um, {GAP} mm over the {kind} plane")
            a, b = m.trace(X0, X0 + length, GAP + t / 2, t, lev)
            m.plane("p", kind, z_plane, {"Npa": (X0, 0.0), "Npb": (X0 + length, 0.0)})
            m.equiv(b, "Npb")
            r = run(folder, f"plane_{kind}_{t * 1e3:g}um_{length:g}mm_{f:.0e}_{lev[0]}x{lev[1]}",
                    m.text(a, "Npa", f))
            rows.append(dict(group="plane", t_um=t * 1e3, length_mm=length, plane=kind,
                             level=f"{lev[0]} x {lev[1]}", **r))
            print(f"  plane ({kind}), {t * 1e3:g} um, {length:g} mm, {f:.3g} Hz, {lev}: "
                  f"{r['L_nH']:.4f} nH ({r['seconds']:.1f} s)")
    return rows


GROUPS = {"alone": group_alone, "plane": group_plane}


# ================================================================================================
# Per-unit-length values and the report
# ================================================================================================
def records() -> list[dict]:
    rows = []
    for g in GROUPS:
        path = DATA / g / "results.json"
        if path.exists():
            rows += json.loads(path.read_text(encoding="utf-8"))
    return rows


def per_length(rows: list[dict]) -> list[dict]:
    """L' = (L(6 mm) - L(3 mm)) / 3 mm for every thickness, frequency, filament level and plane."""
    out = []
    keys = {(r["t_um"], r["f"], r["level"], r["plane"]) for r in rows if r["group"] == "plane"}
    for t, f, lev, kind in sorted(keys):
        pair = {r["length_mm"]: r for r in rows if r["group"] == "plane" and (r["t_um"], r["f"], r["level"], r["plane"]) == (t, f, lev, kind)}
        if set(pair) == set(LENGTHS):
            dl = LENGTHS[1] - LENGTHS[0]
            out.append(dict(t_um=t, f=f, level=lev, plane=kind,
                            Lp_nH_per_mm=(pair[LENGTHS[1]]["L_nH"] - pair[LENGTHS[0]]["L_nH"]) / dl,
                            Rp_mohm_per_mm=(pair[LENGTHS[1]]["R_ohm"] - pair[LENGTHS[0]]["R_ohm"]) / dl * 1e3))
    return out


def report() -> None:
    rows = records()
    lines = ["# FastHenry runs of the side note on copper thickness", "",
             "These are the results of `scripts_archive/fasthenry_traces.py`; its docstring explains every model. "
             "\"DC\" is 1 kHz with one filament (a uniform current); at 308 MHz each trace is cut into n_w x n_h "
             "filaments across its width and thickness, ratio 2. The skin depth of copper (rho = 1.7e-8 ohm m) "
             f"is {skin_depth_mm(F_HF) * 1e3:.2f} um at 308 MHz. Inductances in nH, resistances in mOhm.", "",
             "## All runs", "",
             "| Group | Copper (um) | Length (mm) | Plane | Frequency | Filaments | L (nH) | R (mOhm) | Time (s) |",
             "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        fr = "DC" if r["f"] < 1e4 else f"{r['f'] / 1e6:.0f} MHz"
        lines.append(f"| {r['group']} | {r['t_um']:g} | {r['length_mm']:g} | {r['plane'] or '-'} | {fr} | {r['level']} | "
                     f"{r['L_nH']:.4f} | {r['R_ohm'] * 1e3:.3f} | {r['seconds']:.1f} |")
    lines += ["", "## Inductance per unit length over the plane", "",
              "L' = (L(6 mm) - L(3 mm)) / 3 mm, the loop inductance per unit length without the ends.", "",
              "| Copper (um) | Plane | Frequency | Filaments | L' (nH/mm) | R' (mOhm/mm) |", "|---|---|---|---|---|---|"]
    for p in per_length(rows):
        fr = "DC" if p["f"] < 1e4 else f"{p['f'] / 1e6:.0f} MHz"
        lines.append(f"| {p['t_um']:g} | {p['plane']} | {fr} | {p['level']} | {p['Lp_nH_per_mm']:.5f} | {p['Rp_mohm_per_mm']:.3f} |")
    (DATA / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {DATA / 'README.md'}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="fasthenry_traces.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("group", choices=list(GROUPS) + ["all"])
    sub.add_parser("report")
    args = ap.parse_args(argv)
    if args.cmd == "run":
        for g in (GROUPS if args.group == "all" else [args.group]):
            print(f"[{g}]")
            rows = GROUPS[g](DATA / g)
            (DATA / g / "results.json").write_text(json.dumps(rows, indent=1), encoding="utf-8", newline="\n")
    else:
        report()
    return 0


if __name__ == "__main__":
    sys.exit(main())
