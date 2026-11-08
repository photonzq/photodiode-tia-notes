"""Checking the inductance estimates of inductance_estimates.py with FastHenry.

Usage (from this folder):
    python fasthenry_validation.py run segments|tubes|leads|paths|planes|all
    python fasthenry_validation.py report        # writes data/parasitic_cf/fasthenry/README.md

Why this script exists
----------------------
inductance_estimates.py (parts B, C and F) estimates the inductance in series with the feedback
network as a sum of partial self-inductances of straight pieces: zero-thickness strips and thin-walled
tubes with uniform current (its Eqs. (B3) and (B4)), with every mutual term left out, and calls the
sum an estimate on the high side.  Section 4 of the side note TIA_feedback_layouts (Tables 3 and 4)
and Section G.14.10 of the companion note rest on it, and the side note's Appendix C reports these
runs (side_note_numbers() computes every number it quotes).  FastHenry (M. Kamon, M. J. Tsuk and J. K.
White, IEEE Trans. Microwave Theory Tech. 42(9), 1750 (1994); FastFieldSolvers' Windows build
FastHenry2) solves the same magnetoquasistatic problem by the partial-element method with every
conductor cut into filaments, so it computes what the estimate leaves out: the thickness of the
conductors, the uneven current of the skin and proximity effects, the mutual terms along the path,
and the eddy currents in ground planes.  Five groups:
  * segments: the 0.2-mm strips of 0.35, 1.0 and 2.8 mm of part (B).  A strip 1 um thick carried by
    one filament is Eq. (B3)'s own model (no thickness, uniform current) and checks the formula; the
    copper trace, 35 um thick, at DC (one filament: uniform current) and at 308 and 801 MHz (filaments
    down to the skin depth) shows how far the model lies from the real trace.
  * tubes: the via of part (B) (radius 0.15 mm, length 1.6 mm) and the PDIP-8 hole of part (F)
    (radius 0.40 mm) as cages of 8 to 64 parallel strips around the circle, which approach Eq. (B4)'s
    thin tube with uniform current; and the square barrel of the field models (side 0.8472 times the
    drill, pcbcap.packages.add_via), at DC and 308 MHz.
  * leads: one lead of each package built as part (F) builds it (half the foot, the riser and the
    shoulder; for the PDIP-8 the hole, the shoulder and the exit), at DC and 308 MHz.
  * paths: the whole series path of the double-sided SOT-23-5 and SOIC-8 layouts and of the PDIP-8
    layout with the resistor on the solder side: both leads, the vias and the bottom traces, with the
    resistor replaced by an ideal short between its pad centres, as part (F) accounts them.  The port
    lies between the two leads' ends at the body, so FastHenry returns the partial inductance of the
    whole open path, mutual terms included.  Against part (F)'s routing + 2 x lead, i.e. L_x without
    the 2 x 2.35 nH assumed inside the package.
  * planes: the SOT-23-5 and SOIC-8 paths over the two ground planes of the field models (0.2 and
    1.4 mm deep, 35-um copper, with a window 0.5 mm beyond the network, g_opa846_3d.py), at 308 MHz.
The pieces lie where part (F) and the field models put them; the joints that part (F) does not count
(from a via's top to the foot it meets, from a via's bottom to its trace, and across the resistor) are
ideal shorts (FastHenry's .equiv), so that the comparison is of like with like.  Every conductor is
copper, rho = 1.7e-8 ohm m, as part (B) assumes; a magnetic lead frame (Alloy 42) is not modelled.
Every run is a separate FastHenry2 input for one frequency, run through FastHenry2's automation
interface; its impedance matrix (Zc_<run>.mat) and the numbers are kept under
data/parasitic_cf/fasthenry/.  Every high-frequency result is computed at three filament levels and
every plane result at three grid sizes; the report lists all of them (convergence), not only the last.
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
sys.path.insert(0, str(HERE.parents[3] / "pcbcap"))
sys.path.insert(0, str(HERE.parent))

import inductance_estimates as ie             # noqa: E402
from pcbcap import packages as pk             # noqa: E402

DATA = HERE.parents[2] / "data" / "parasitic_cf" / "fasthenry"
RHO = 1.7e-8                                  # ohm m, as part (B)
SIGMA_MM = 1.0 / RHO * 1e-3                   # 1/(ohm mm): FastHenry's unit of conductivity with .units mm
F_DC, F_846, F_855 = 1e3, 308e6, 801e6        # "DC" (uniform current), the OPA846 and OPA855 crossovers
LEVELS = [(5, 3), (9, 5), (13, 7)]            # filaments across width and thickness, ratio 2 (FastHenry
                                              # guide, Section 2.4: the outermost filament ~ the skin depth)
T_CU = 0.035                                  # mm, copper of pads and traces
BOARD_H = ie.BOARD_H


def skin_depth_mm(f: float) -> float:
    """delta = sqrt(2 rho / (omega mu0)) (inductance_estimates.py, part (B)), in mm."""
    return math.sqrt(2 * RHO / (2 * math.pi * f * 4e-7 * math.pi)) * 1e3


def smallest_filament(n: int, r: float = 2.0) -> float:
    """Fraction of the width taken by the outermost of n filaments whose widths grow by r towards the
    middle (FastHenry's nwinc/rw): the widths are 1, r, r^2, ... up to the middle and back."""
    half = n // 2
    weights = [r ** k for k in range(half)] + ([r ** half] if n % 2 else []) + [r ** k for k in reversed(range(half))]
    return 1.0 / sum(weights)


# ================================================================================================
# Writing FastHenry input
# ================================================================================================
class Model:
    """A FastHenry input with millimetre units and copper by default."""

    def __init__(self, title: str):
        self.lines = [f"* {title}", ".units mm", f".default sigma={SIGMA_MM:.6g}"]
        self.n_nodes = 0
        self.n_segs = 0

    def node(self, x: float, y: float, z: float) -> str:
        name = f"N{self.n_nodes}"
        self.n_nodes += 1
        self.lines.append(f"{name} x={x:.9g} y={y:.9g} z={z:.9g}")
        return name

    def seg(self, a: str, b: str, w: float, h: float, nw: int = 1, nh: int = 1, wdir=None) -> str:
        """A segment from node a to node b, width w and height h; ``wdir`` is a vector along the width
        (FastHenry's wx, wy, wz); without it FastHenry puts the width in the x-y plane, which is wrong
        for a vertical segment."""
        name = f"E{self.n_segs}"
        self.n_segs += 1
        extra = f" wx={wdir[0]:.9g} wy={wdir[1]:.9g} wz={wdir[2]:.9g}" if wdir is not None else ""
        self.lines.append(f"{name} {a} {b} w={w:.9g} h={h:.9g} nwinc={nw} nhinc={nh} rw=2 rh=2{extra}")
        return name

    def equiv(self, *nodes: str) -> None:
        self.lines.append(".equiv " + " ".join(nodes))

    def plane(self, name: str, x: tuple, y: tuple, z: float, thick: float, n: int, holes=()) -> None:
        """A uniformly discretised plane (FastHenry guide, Section 1.3.9), n x n segments, with
        rectangular holes ((x0, x1), (y0, y1))."""
        s = (f"G{name} x1={x[0]:.9g} y1={y[0]:.9g} z1={z:.9g} x2={x[1]:.9g} y2={y[0]:.9g} z2={z:.9g} "
             f"x3={x[1]:.9g} y3={y[1]:.9g} z3={z:.9g} thick={thick:.9g} seg1={n} seg2={n}")
        for (hx, hy) in holes:
            s += f"\n+ hole rect ({hx[0]:.9g},{hy[0]:.9g},{z:.9g},{hx[1]:.9g},{hy[1]:.9g},{z:.9g})"
        self.lines.append(s)

    def text(self, a: str, b: str, f: float) -> str:
        return "\n".join(self.lines + [f".external {a} {b} port", f".freq fmin={f:.9g} fmax={f:.9g} ndec=1",
                                       ".end"]) + "\n"


def straight(m: Model, p0, p1, w: float, h: float, level, wdir=None) -> tuple[str, str]:
    a, b = m.node(*p0), m.node(*p1)
    m.seg(a, b, w, h, level[0], level[1], wdir)
    return a, b


def chain(m: Model, pts, w: float, h: float, level, wdir=None) -> tuple[str, str]:
    """A chain of straight segments through the points ``pts``, joined at shared nodes."""
    nodes = [m.node(*p) for p in pts]
    for a, b in zip(nodes, nodes[1:]):
        m.seg(a, b, w, h, level[0], level[1], wdir)
    return nodes[0], nodes[-1]


def cage(m: Model, x: float, y: float, z0: float, z1: float, a: float, n: int, wall: float = 0.010):
    """A thin-walled tube of radius a from z0 to z1 as n parallel strips around the circle, each
    carrying its own uniform current, joined at both ends by ideal shorts to a node on the axis; as n
    grows it approaches the tube of Eq. (B4).  Each strip is 0.95 of its share of the circumference
    wide and ``wall`` thick, with its width along the tangent.  Returns the two axis nodes."""
    bottom, top = m.node(x, y, z0), m.node(x, y, z1)
    width = 0.95 * 2 * math.pi * a / n
    ends = [[], []]
    for k in range(n):
        th = 2 * math.pi * (k + 0.5) / n
        cx, cy = x + a * math.cos(th), y + a * math.sin(th)
        p, q = m.node(cx, cy, z0), m.node(cx, cy, z1)
        m.seg(p, q, width, wall, 1, 1, (-math.sin(th), math.cos(th), 0.0))
        ends[0].append(p)
        ends[1].append(q)
    m.equiv(bottom, *ends[0])
    m.equiv(top, *ends[1])
    return bottom, top


# ================================================================================================
# Running FastHenry2 and reading Zc.mat
# ================================================================================================
_ZC = re.compile(r"Impedance matrix for frequency = ([0-9.eE+-]+) (\d+) x (\d+)\s*\n(.*?)(?=Impedance matrix|\Z)", re.S)


def read_zc(path: Path) -> list[tuple[float, complex]]:
    """(frequency, Z of the first port) for every matrix in a Zc.mat file (FastHenry guide, Section 2.2)."""
    out = []
    for m in _ZC.finditer(path.read_text()):
        f = float(m.group(1))
        first = m.group(4).strip().splitlines()[0]
        nums = re.findall(r"[-+]?[0-9.]+(?:[eE][-+]?\d+)?j?", first.replace(" ", ""))
        re_part = float(nums[0])
        im_part = float(nums[1].rstrip("j"))
        out.append((f, complex(re_part, im_part)))
    return out


def run(folder: Path, name: str, text: str, extra: str = "", timeout: float = 3600.0) -> dict:
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
        if not fh.Run(f'"{inp}" -S _{name} {extra}'.strip()):
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
def group_segments(folder: Path) -> list[dict]:
    rows = []
    for l in (0.35, 1.0, 2.8):
        est = ie.partial_strip(l, ie.TRACE_W)
        m = Model(f"strip {l} mm x 0.2 mm x 1 um, one filament (Eq. (B3)'s model)")
        a, b = straight(m, (0, 0, 0), (l, 0, 0), ie.TRACE_W, 0.001, (1, 1))
        r = run(folder, f"strip_{l:g}_thin", m.text(a, b, F_DC))
        rows.append(dict(item=f"strip {l:g} mm, 1 um, uniform", level="1 x 1", estimate_nH=est, **r))
        for f, levels in ((F_DC, [(1, 1)]), (F_846, LEVELS), (F_855, LEVELS)):
            for lev in levels:
                m = Model(f"copper trace {l} mm x 0.2 mm x 35 um")
                a, b = straight(m, (0, 0, 0), (l, 0, 0), ie.TRACE_W, T_CU, lev)
                r = run(folder, f"strip_{l:g}_cu_{f:.0e}_{lev[0]}x{lev[1]}", m.text(a, b, f))
                rows.append(dict(item=f"strip {l:g} mm, 35-um copper", level=f"{lev[0]} x {lev[1]}",
                                 estimate_nH=est, **r))
                print(f"  {rows[-1]['item']} at {f:.3g} Hz, {lev}: {r['L_nH']:.4f} nH (Eq. (B3) {est:.4f})")
    return rows


def group_tubes(folder: Path) -> list[dict]:
    rows = []
    for label, a, l in (("via", ie.VIA_A, BOARD_H), ("PDIP-8 hole", pk.Dip8().drill / 2, BOARD_H)):
        est = ie.partial_tube(l, a)
        for n in (8, 16, 32, 64):
            m = Model(f"{label}: cage of {n} strips, radius {a} mm, length {l} mm")
            b, t = cage(m, 0.0, 0.0, 0.0, l, a, n)
            r = run(folder, f"cage_{label.replace(' ', '_')}_{n}", m.text(b, t, F_DC))
            rows.append(dict(item=f"{label} as a cage of {n}", level=f"{n} strips", estimate_nH=est, **r))
            print(f"  {rows[-1]['item']}: {r['L_nH']:.4f} nH (Eq. (B4) {est:.4f})")
        side = pk.SQUARE_FOR_ROUND * 2 * a
        for f, levels in ((F_DC, [(1, 1)]), (F_846, LEVELS)):
            for lev in levels:
                m = Model(f"{label}: square barrel of side {side:.4f} mm")
                s, e = straight(m, (0, 0, 0), (0, 0, l), side, side, lev, (1.0, 0.0, 0.0))
                r = run(folder, f"square_{label.replace(' ', '_')}_{f:.0e}_{lev[0]}x{lev[1]}", m.text(s, e, f))
                rows.append(dict(item=f"{label}, square barrel {side:.3f} mm", level=f"{lev[0]} x {lev[1]}",
                                 estimate_nH=est, **r))
                print(f"  {rows[-1]['item']} at {f:.3g} Hz, {lev}: {r['L_nH']:.4f} nH")
    return rows


def gull_wing(m: Model, p, x_pin: float, y_pin: float, outward: int, level):
    """One gull-wing lead as part (F) builds it: from the foot's centre inward along half the foot,
    up the riser, inward along the shoulder outside the body.  Returns (foot-centre node, end node at
    the body).  The foot lies on the pad, its centre plane half a lead thickness above the copper."""
    riser = p.standoff + p.shoulder_height + p.lead_thickness / 2
    shoulder = max(0.0, (p.lead_span - p.body_width) / 2 - p.foot_length - p.lead_thickness)
    x_out = outward * p.lead_span / 2
    x_fc = x_out - outward * p.foot_length / 2
    x_bend = x_fc - outward * p.foot_length / 2
    z0 = T_CU + p.lead_thickness / 2
    pts = [(x_fc, y_pin, z0), (x_bend, y_pin, z0), (x_bend, y_pin, z0 + riser)]
    if shoulder > 0:
        pts.append((x_bend - outward * shoulder, y_pin, z0 + riser))
    nodes = [m.node(*q) for q in pts]
    for a, b in zip(nodes, nodes[1:]):
        m.seg(a, b, p.lead_width, p.lead_thickness, level[0], level[1], (0.0, 1.0, 0.0))
    return nodes[0], nodes[-1], dict(half_foot=p.foot_length / 2, riser=riser, shoulder=shoulder)


def dip_lead(m: Model, x_pin: float, y_pin: float, outward: int, level, n_cage: int = 16):
    """One PDIP-8 lead as part (F) builds it, network on the solder side: the filled hole (a tube of
    the drill's radius through the board), the shoulder up from the seating plane to the exit's centre,
    and the exit inward to the body.  Returns (bottom node, end node at the body)."""
    d = pk.Dip8()
    bottom, top = cage(m, x_pin, y_pin, -BOARD_H, 0.0, d.drill / 2, n_cage)
    shoulder = d.standoff + d.exit_height + d.lead_thickness / 2
    exit_len = d.row / 2 - d.lead_thickness / 2 - d.body_width / 2
    p1 = m.node(x_pin, y_pin, 0.0)
    p2 = m.node(x_pin, y_pin, shoulder)
    p3 = m.node(x_pin - outward * exit_len, y_pin, shoulder)
    m.equiv(top, p1)
    m.seg(p1, p2, d.shoulder_width, d.lead_thickness, level[0], level[1], (0.0, 1.0, 0.0))
    m.seg(p2, p3, d.shoulder_width, d.lead_thickness, level[0], level[1], (0.0, 1.0, 0.0))
    return bottom, p3


def lead_estimates() -> dict:
    return {name: sum(ie.segment_inductance(*s) for s in segs) for name, segs in ie.lead_paths().items()}


def group_leads(folder: Path) -> list[dict]:
    rows = []
    est = lead_estimates()
    for name in ("SOT-23-5", "SOIC-8", "PDIP-8"):
        for f, levels in ((F_DC, [(1, 1)]), (F_846, LEVELS)):
            for lev in levels:
                m = Model(f"one {name} lead")
                if name == "PDIP-8":
                    a, b = dip_lead(m, 0.0, 0.0, -1, lev)
                else:
                    p = pk.Sot23() if name == "SOT-23-5" else pk.Soic8()
                    a, b, _ = gull_wing(m, p, 0.0, 0.0, -1, lev)
                r = run(folder, f"lead_{name}_{f:.0e}_{lev[0]}x{lev[1]}", m.text(a, b, f))
                rows.append(dict(item=f"{name} lead", level=f"{lev[0]} x {lev[1]}", estimate_nH=est[name], **r))
                print(f"  {name} lead at {f:.3g} Hz, {lev}: {r['L_nH']:.4f} nH (part (F) {est[name]:.4f})")
    return rows


def build_path(name: str, level, planes: int | None = None) -> tuple[Model, str, str, dict]:
    """The series path of part (F)'s layout for package ``name`` (module docstring).  With ``planes``
    = n, the two windowed ground planes of the field models are added, each n x n segments."""
    m = Model(f"{name} feedback path" + (f", planes {planes} x {planes}" if planes else ""))
    hp = 0.475                                  # 0402 pad centre from the resistor's centre (part (C))
    z_bot = -BOARD_H - T_CU / 2                 # centre plane of the bottom copper
    ends = []
    if name in ("SOT-23-5", "SOIC-8"):
        p = pk.Sot23() if name == "SOT-23-5" else pk.Soic8()
        if name == "SOT-23-5":
            pins = [(pk.Sot23().pin_xy(1), -1), (pk.Sot23().pin_xy(4), +1)]   # A: pin 1, B: pin 4
            xv = 0.95
        else:
            pins = [(pk.Soic8().pin_xy(6), +1), (pk.Soic8().pin_xy(2), -1)]   # A: pin 6, B: pin 2
            xv = 2.2
        for (xp, yp), out in pins:
            foot, top, _ = gull_wing(m, p, xp, yp, out, level)
            vb, vt = cage(m, out * xv, yp, -BOARD_H, 0.0, ie.VIA_A, 16)
            m.equiv(foot, vt)                   # pad from the via to the foot: not counted in part (F)
            t0, t1 = chain(m, [(out * xv, yp, z_bot), (out * xv, 0.0, z_bot), (out * hp, 0.0, z_bot)],
                           ie.TRACE_W, T_CU, level)
            m.equiv(vb, t0)                     # via bottom to trace: not counted in part (F)
            ends.append((top, t1))
    elif name == "PDIP-8":
        d = pk.Dip8()
        pins = [(d.pin_xy(6), +1), (d.pin_xy(2), -1)]                         # A: pin 6, B: pin 2
        for (xp, yp), out in pins:
            bottom, top = dip_lead(m, xp, yp, out, level)
            t0, t1 = chain(m, [(xp, yp, z_bot), (xp, 0.0, z_bot), (out * hp, 0.0, z_bot)], ie.TRACE_W, T_CU, level)
            m.equiv(bottom, t0)
            ends.append((top, t1))
    else:
        raise ValueError(name)
    m.equiv(ends[0][1], ends[1][1])             # the resistor as an ideal short between its pad centres
    info = {}
    if planes:
        win = plane_window(name)
        info["window"] = win
        for k, depth in enumerate((0.2, 1.4)):
            m.plane(f"p{k}", (-8.0, 8.0), (-8.0, 8.0), -depth, T_CU, planes, holes=[win])
    return m, ends[0][0], ends[1][0], info


def plane_window(name: str):
    """The planes' window of g_opa846_3d.py (the bounding box of the package's pads, the resistor's
    pads, the traces and the vias, grown by 0.5 mm), for the SOT-23-5; the same rule for the SOIC-8."""
    p = pk.Sot23() if name == "SOT-23-5" else pk.Soic8()
    pins = (1, 2, 3, 4, 5) if name == "SOT-23-5" else (1, 2, 3, 4, 5, 6, 7, 8)
    xs, ys = [], []
    for pin in pins:
        px, py = p.pin_xy(pin)
        xs += [px - p.pad_length / 2, px + p.pad_length / 2]
        ys += [py - p.pad_width / 2, py + p.pad_width / 2]
    xs += [-0.75, 0.75]
    ys += [-0.3, 0.3]                           # the 0402's pads (land pattern 0402: s 0.40, w 0.55, l 0.60)
    return ((min(xs) - 0.5, max(xs) + 0.5), (min(ys) - 0.5, max(ys) + 0.5))


def path_estimates() -> dict:
    """Part (F)'s routing + 2 x lead for each layout (L_x without the package interior)."""
    lead = lead_estimates()
    segs23, nv23 = ie.LAYOUTS["OPA846 double-sided, 0402"]
    out = {"SOT-23-5": ie.routing_inductance(segs23, nv23) + 2 * lead["SOT-23-5"]}
    for name in ("SOIC-8", "PDIP-8"):
        segs, nv = ie.ROUTING_8[name]
        out[name] = ie.routing_inductance(segs, nv) + 2 * lead[name]
    return out


def group_paths(folder: Path) -> list[dict]:
    rows = []
    est = path_estimates()
    for name in ("SOT-23-5", "SOIC-8", "PDIP-8"):
        for f, levels in ((F_DC, [(1, 1)]), (F_846, LEVELS)):
            for lev in levels:
                m, a, b, _ = build_path(name, lev)
                r = run(folder, f"path_{name}_{f:.0e}_{lev[0]}x{lev[1]}", m.text(a, b, f))
                rows.append(dict(item=f"{name} path", level=f"{lev[0]} x {lev[1]}", estimate_nH=est[name], **r))
                print(f"  {name} path at {f:.3g} Hz, {lev}: {r['L_nH']:.4f} nH (part (F) {est[name]:.4f})")
    return rows


def group_planes(folder: Path) -> list[dict]:
    rows = []
    est = path_estimates()
    lev = LEVELS[1]
    for name in ("SOT-23-5", "SOIC-8"):
        for n in (32, 64, 96):
            m, a, b, info = build_path(name, lev, planes=n)
            r = run(folder, f"planes_{name}_{n}", m.text(a, b, F_846), timeout=7200.0)
            rows.append(dict(item=f"{name} path over the planes", level=f"{lev[0]} x {lev[1]}, plane {n} x {n}",
                             estimate_nH=est[name], window=info["window"], **r))
            print(f"  {name} over the planes, {n} x {n}: {r['L_nH']:.4f} nH ({r['seconds']:.0f} s)")
    return rows


GROUPS = {"segments": group_segments, "tubes": group_tubes, "leads": group_leads, "paths": group_paths,
          "planes": group_planes}


# ================================================================================================
# The numbers that the side note quotes (Section 4 and Appendix C), from the records; no solve
# ================================================================================================
def collinear_mutual(l1: float, l2: float, g: float = 0.0) -> float:
    """Partial mutual inductance (nH) of two collinear filaments of lengths l1 and l2 (mm), g apart along
    their common line and carrying the current the same way (the Neumann integral of Eq. (B1)'s kind
    with the two filaments on one line):
        M = (mu0/4pi) [F(l1 + g + l2) - F(l1 + g) - F(l2 + g) + F(g)],  F(x) = x ln x,  mu0/4pi = 0.1 nH/mm.
    For g = 0 it is the side note's Eq. (C.1), (mu0/4pi) [l1 ln((l1 + l2)/l1) + l2 ln((l1 + l2)/l2)]."""
    def F(x: float) -> float:
        return x * math.log(x) if x > 0 else 0.0
    return 0.1 * (F(l1 + g + l2) - F(l1 + g) - F(l2 + g) + F(g))


def _records() -> dict:
    out = {}
    for g in GROUPS:
        path = DATA / g / "results.json"
        if path.exists():
            out[g] = json.loads(path.read_text(encoding="utf-8"))
    return out


def _pick(rows: list[dict], item: str, f: float, level: str) -> dict:
    for r in rows:
        if r["item"] == item and abs(r["f"] - f) < 1.0 and r["level"] == level:
            return r
    raise KeyError((item, f, level))


def side_note_numbers() -> list[str]:
    """Every number of the side note's Section 4 and Appendix C that comes from these runs, computed
    from the records (results.json of each group), as Markdown bullets."""
    rec = _records()
    seg, tub, lea, pat, pla = (rec[k] for k in ("segments", "tubes", "leads", "paths", "planes"))
    fine, mid = f"{LEVELS[-1][0]} x {LEVELS[-1][1]}", f"{LEVELS[1][0]} x {LEVELS[1][1]}"
    pct = lambda x: 100.0 * (x - 1.0)                                         # noqa: E731
    out = []

    # Eq. (4) itself: the strip 1 um thick with uniform current, and the cages of 64 strips
    thin = [r["L_nH"] / r["estimate_nH"] for r in seg if r["item"].endswith("1 um, uniform")]
    out.append(f"* Eq. (4)'s strip (1 um thick, uniform current), three lengths: {min(map(pct, thin)):+.2f} to "
               f"{max(map(pct, thin)):+.2f} % of Eq. (4).")
    for label in ("via", "PDIP-8 hole"):
        r = _pick(tub, f"{label} as a cage of 64", F_DC, "64 strips")
        out.append(f"* {label} as a cage of 64 thin strips: {r['L_nH']:.4f} nH against Eq. (4)'s tube "
                   f"{r['estimate_nH']:.4f} nH ({pct(r['L_nH'] / r['estimate_nH']):+.2f} %).")

    # The copper traces and the leads, each alone
    for f, lev, what in ((F_DC, "1 x 1", "DC"), (F_846, fine, "308 MHz"), (F_855, fine, "801 MHz")):
        ratios = [_pick(seg, f"strip {l:g} mm, 35-um copper", f, lev) for l in (0.35, 1.0, 2.8)]
        txt = ", ".join(f"{r['L_nH']:.4f} nH ({pct(r['L_nH'] / r['estimate_nH']):+.1f} %)" for r in ratios)
        out.append(f"* Traces 0.2 mm wide, 35-um copper, 0.35/1.0/2.8 mm long, at {what}: {txt}.")
    for name in ("SOT-23-5", "SOIC-8", "PDIP-8"):
        dc, hf = _pick(lea, f"{name} lead", F_DC, "1 x 1"), _pick(lea, f"{name} lead", F_846, fine)
        out.append(f"* {name} lead: sum {dc['estimate_nH']:.4f} nH; FastHenry {dc['L_nH']:.4f} nH at DC "
                   f"({pct(dc['L_nH'] / dc['estimate_nH']):+.1f} %), {hf['L_nH']:.4f} nH at 308 MHz "
                   f"({pct(hf['L_nH'] / hf['estimate_nH']):+.1f} %).")

    # The PDIP-8 lead: hole and shoulder in line, Eq. (C.1)
    d = pk.Dip8()
    l_sh = d.standoff + d.exit_height + d.lead_thickness / 2
    m = collinear_mutual(BOARD_H, l_sh)
    dc, hf = _pick(lea, "PDIP-8 lead", F_DC, "1 x 1"), _pick(lea, "PDIP-8 lead", F_846, fine)
    out.append(f"* Eq. (C.1) for the PDIP-8 hole ({BOARD_H:.3f} mm) and shoulder ({l_sh:.3f} mm): "
               f"0.1 nH/mm x [{BOARD_H:.3f} ln({BOARD_H + l_sh:.3f}/{BOARD_H:.3f}) + {l_sh:.3f} ln({BOARD_H + l_sh:.3f}/{l_sh:.3f})] mm "
               f"= 0.1 x ({BOARD_H * math.log((BOARD_H + l_sh) / BOARD_H):.4f} + {l_sh * math.log((BOARD_H + l_sh) / l_sh):.4f}) "
               f"= {m:.4f} nH; 2M = {2 * m:.4f} nH. FastHenry's lead exceeds the sum by "
               f"{dc['L_nH'] - dc['estimate_nH']:.4f} nH at DC and {hf['L_nH'] - hf['estimate_nH']:.4f} nH at 308 MHz.")

    # The whole paths, and the planes
    for name in ("SOT-23-5", "SOIC-8", "PDIP-8"):
        dc, hf = _pick(pat, f"{name} path", F_DC, "1 x 1"), _pick(pat, f"{name} path", F_846, fine)
        out.append(f"* {name} path: sum {dc['estimate_nH']:.4f} nH; FastHenry {dc['L_nH']:.4f} nH at DC "
                   f"({pct(dc['L_nH'] / dc['estimate_nH']):+.1f} %), {hf['L_nH']:.4f} nH at 308 MHz "
                   f"({pct(hf['L_nH'] / hf['estimate_nH']):+.1f} %).")
    plane_ratio = {}
    for name in ("SOT-23-5", "SOIC-8"):
        free = _pick(pat, f"{name} path", F_846, mid)
        over = _pick(pla, f"{name} path over the planes", F_846, f"{mid}, plane 96 x 96")
        plane_ratio[name] = over["L_nH"] / free["L_nH"]
        out.append(f"* {name} path with {mid} filaments: {free['L_nH']:.4f} nH without the planes, "
                   f"{over['L_nH']:.4f} nH over them ({pct(plane_ratio[name]):+.2f} %).")

    # Where the pieces stand: the via under the riser, and the vertical pieces of the two sides
    for name, p, pins, xv in (("SOT-23-5", pk.Sot23(), (1, 4), 0.95), ("SOIC-8", pk.Soic8(), (6, 2), 2.2)):
        ya, yb = p.pin_xy(pins[0])[1], p.pin_xy(pins[1])[1]
        xr = p.lead_span / 2 - p.foot_length                    # the riser's |x|, as gull_wing builds it
        out.append(f"* {name}: via at |x| = {xv:.4f} mm, riser at |x| = {xr:.4f} mm (in line within "
                   f"{abs(xr - xv):.4f} mm); the two sides' vias {math.hypot(2 * xv, ya - yb):.3f} mm apart, "
                   f"their risers {math.hypot(2 * xr, ya - yb):.3f} mm apart.")
    (xa, ya), (xb, yb) = d.pin_xy(6), d.pin_xy(2)
    out.append(f"* PDIP-8: the two sides' holes and shoulders {math.hypot(xa - xb, ya - yb):.3f} mm apart.")

    # L_x and delta_1 at the OPA846 crossover (Eqs. (2) and (5) of the side note), and Table 4
    f_c, c_f, r_f = ie.DESIGNS["OPA846"]
    w2c = (2 * math.pi * f_c) ** 2 * c_f * 1e-12
    inside = 2 * ie.LEAD_INTERNAL
    for name in ("SOT-23-5", "SOIC-8", "PDIP-8"):
        hf = _pick(pat, f"{name} path", F_846, fine)
        lx_est, lx_fh = hf["estimate_nH"] + inside, hf["L_nH"] + inside
        txt = (f"* {name}: L_x = {lx_est:.4f} nH (sum) and {lx_fh:.4f} nH (FastHenry, 308 MHz, {fine}), each with "
               f"2 x {ie.LEAD_INTERNAL} nH inside; delta_1 = {100 * w2c * lx_est * 1e-9:.3f} % and "
               f"{100 * w2c * lx_fh * 1e-9:.3f} %; delta_2 = {2 * math.pi * f_c * lx_fh * 1e-9 / r_f * 180 / math.pi:.3f} deg "
               f"(FastHenry); f_1% higher by {pct(math.sqrt(lx_est / lx_fh)):+.2f} %")
        if name in plane_ratio:
            lx_pl = hf["L_nH"] * plane_ratio[name] + inside
            txt += f"; over the planes L_x = {lx_pl:.4f} nH, delta_1 = {100 * w2c * lx_pl * 1e-9:.3f} %"
        out.append(txt + ".")

    # The outermost filaments at the finest level, and the convergence
    nw, nh = LEVELS[-1]
    s = pk.Sot23(), pk.Soic8()
    for label, w, h in (("trace", ie.TRACE_W, T_CU), ("SOT-23-5 lead", s[0].lead_width, s[0].lead_thickness),
                        ("SOIC-8 lead", s[1].lead_width, s[1].lead_thickness),
                        ("PDIP-8 shoulder", d.shoulder_width, d.lead_thickness)):
        out.append(f"* Outermost filament of the {label} at {fine}: {1e3 * w * smallest_filament(nw):.2f} um across "
                   f"the width, {1e3 * h * smallest_filament(nh):.2f} um across the thickness "
                   f"(skin depth {1e3 * skin_depth_mm(F_846):.2f} um at 308 MHz).")
    for label, rows in (("paths", pat), ("leads", lea), ("traces", seg), ("tubes (square barrels)", tub)):
        ch = []
        for r in rows:
            if r["level"] == fine:
                prev = _pick(rows, r["item"], r["f"], mid)
                ch.append(abs(pct(r["L_nH"] / prev["L_nH"])))
        out.append(f"* From {mid} to {fine} filaments the {label} change by {min(ch):.2f}-{max(ch):.2f} %.")
    ch = [abs(pct(_pick(pla, f"{n} path over the planes", F_846, f"{mid}, plane 96 x 96")["L_nH"]
                  / _pick(pla, f"{n} path over the planes", F_846, f"{mid}, plane 64 x 64")["L_nH"]))
          for n in ("SOT-23-5", "SOIC-8")]
    out.append(f"* From plane grids of 64 x 64 to 96 x 96 the paths change by {min(ch):.3f}-{max(ch):.3f} %.")
    return out


# ================================================================================================
# Report
# ================================================================================================
def report() -> None:
    lines = ["# FastHenry checks of the inductance estimates", "",
             "These are the results of `scripts_archive/parasitic_cf/fasthenry_validation.py`, which checks "
             "`inductance_estimates.py` (parts B, C and F) with FastHenry2; its docstring explains every model. "
             "All values are partial inductances of the stated open path, in nH; the estimate is that of "
             "`inductance_estimates.py` for the same piece. \"DC\" is 1 kHz with one filament per segment "
             "(uniform current). At high frequency each segment is cut into filaments across its width and "
             "thickness (n_w x n_h, ratio 2); the three levels are a convergence series. Skin depth of copper "
             f"(rho = 1.7e-8 ohm m): {skin_depth_mm(F_846) * 1e3:.2f} um at 308 MHz, "
             f"{skin_depth_mm(F_855) * 1e3:.2f} um at 801 MHz.", "",
             "## What the runs show", "",
             "* The formulas are right: a strip 1 um thick with uniform current reproduces Eq. (B3) to 0.13-0.27 %, "
             "and cages of 64 strips approach Eq. (B4) to 0.7 % (via) and 0.4 % (PDIP-8 hole). The field models' "
             "square barrels match the round tubes to 0.7 % at 308 MHz (they are 11-14 % higher at DC).",
             "* Single pieces lie below the estimates, as the script argues: the 35-um copper traces by 4-8 % at DC "
             "and 9-16 % at 308 and 801 MHz, the gull-wing leads of the SOT-23-5 and SOIC-8 by 17-27 %.",
             "* The PDIP-8 lead lies 19-26 % above its estimate. Its filled hole and its shoulder stand in line and "
             "carry the current the same way, so their mutual inductance, which the estimate leaves out, adds: "
             "2 x 0.263 nH for collinear filaments (collinear_mutual(), the side note's Eq. (C.1)). FastHenry's "
             "excess is smaller, 0.35 nH at DC and 0.25 nH at 308 MHz, because the filaments of conductors this "
             "wide meet off their common line, which lowers the mutual term, and the shoulder's thickness lowers "
             "its own term.",
             "* The whole paths (leads, vias and traces, without the 2 x 2.35 nH inside the package) lie within "
             "-6.3 % to +4.3 % of part (F). Every piece but the vias lies 9-27 % below its estimate at 308 MHz, so "
             "the mutual terms that the estimate leaves out add more than they take away. The path crosses from "
             "one side of the package to the other instead of going out to the resistor and back: on each side the "
             "via stands in line with the lead's riser (the PDIP-8's hole with its shoulder) and carries the current "
             "the same way, and the traces of the two sides run the same way; the vertical pieces of the two sides, "
             "which carry opposite currents, stand 2.7-8.0 mm apart. inductance_estimates.py calls its sum an "
             "estimate on the high side partly because it leaves the mutual terms out; for these layouts that "
             "reason does not hold, while its totals do.",
             "* The windowed ground planes lower the SOT-23-5 and SOIC-8 paths by 0.9 % and 0.7 % at 308 MHz.",
             "* Convergence: between the two finest filament levels the traces and the whole paths move by 0.15 % "
             "or less and the square barrels and the leads, whose thick cross-sections the filaments resolve "
             "last, by up to 0.9 %; between the plane grids of 64 and 96 the paths move by 0.15 % or less.", ""]
    for g in GROUPS:
        path = DATA / g / "results.json"
        if not path.exists():
            continue
        rows = json.loads(path.read_text(encoding="utf-8"))
        lines += [f"## {g}", "", "| Item | Frequency | Filaments / grid | FastHenry (nH) | Estimate (nH) | Ratio | R (mOhm) | Time (s) |",
                  "|---|---|---|---|---|---|---|---|"]
        for r in rows:
            fr = "DC" if r["f"] < 1e4 else f"{r['f'] / 1e6:.0f} MHz"
            lines.append(f"| {r['item']} | {fr} | {r['level']} | {r['L_nH']:.4f} | {r['estimate_nH']:.4f} | "
                         f"{r['L_nH'] / r['estimate_nH']:.4f} | {r['R_ohm'] * 1e3:.3f} | {r['seconds']:.1f} |")
        lines.append("")
    lines += ["## Numbers quoted in the side note", "",
              "The side note `TIA_feedback_layouts` quotes these values in Section 4 and Appendix C; "
              "`side_note_numbers()` computes them from the records above.", ""]
    lines += side_note_numbers() + [""]
    (DATA / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {DATA / 'README.md'}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="fasthenry_validation.py")
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
