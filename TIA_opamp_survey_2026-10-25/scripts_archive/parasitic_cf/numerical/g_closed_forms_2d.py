"""Appendix G's closed forms against numerical solutions of the same two-dimensional problems.

Usage:
    python g_closed_forms_2d.py list
    python g_closed_forms_2d.py run <case> [--record <json>]

Why this script exists
----------------------
The closed forms that Appendix G derives exactly (Eqs. (G.25), (G.27), (G.28), (G.32), (G.33),
(G.38), (G.41), (G.43), (G.45) and (G.46), in Sections G.6-G.11) are exact solutions of idealised
two-dimensional problems: a half-plane, a cut layer, a block with insulating faces, and so on.  Each
case below builds exactly that problem with the pcbcap package (TIA_notes/pcbcap), solves it with
finite elements, and prints the numerical value next to the closed form evaluated by
cf_parasitic_estimate.py.  Agreement to about 1e-4 confirms both the derivation and the solver.
The appendix's parallel-plate estimates, Eqs. (G.42), (G.44) and (G.47), are not exact solutions of
any problem and are not checked here.
Where Appendix G gives only bounds (the body with the film's potential kept; the pins with pin 4
grounded; the pads reaching under the body), the numerical solution gives the value itself, and
the case says where it lies.

Conventions: every case is solved per unit permittivity (eps_r = 1 in the region of the formula),
so the printed numbers are C'/eps0, directly comparable with the dimensionless values returned by
cf_parasitic_estimate.py.  Dimensions are the 0402 nominal values of Table G.2 unless stated.
Nets: A at +x, B at -x (pcbcap's convention).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[4] / "pcbcap"))       # the pcbcap package at the repository root
sys.path.insert(0, str(HERE.parents[1]))                   # cf_parasitic_estimate.py

import cf_parasitic_estimate as ana                        # noqa: E402
from pcbcap.constants import EPS0                          # noqa: E402
from pcbcap.geometry import Film, Layout, LinearProfile    # noqa: E402
from pcbcap.meshing import MeshParams                      # noqa: E402
from pcbcap.study import lower_priority, solve_layout      # noqa: E402

# 0402 nominal (Table G.2): body and Vishay 28950 land pattern
L, W, T, A = 1.00, 0.50, 0.35, 0.20
G = L - 2 * A                      # film length between the top wraps
PW, PS = 0.55, 0.40                # pad length along the axis, gap between pads
X = PS / 2 + PW                    # outer end of a pad
# Size of the half-plane domains, whose outer boundary is open (zero flux).  Truncation estimate for
# the pads of Eq. (G.25), the case with the widest charge distribution: the odd drive is a line
# dipole far away, and a zero-flux circle of radius R lowers C' of the full-plane problem by
# C'_full^2 d^2 / (2 pi eps0 R^2) (derivation in pcbcap.checks, strips_free_space), d being the
# distance between the charge centroids of the two pads.  The half-plane problem is half of the
# full-plane one (reflection about the pads' plane), so C'_full = 2 C'_half and the relative change
# is -C'_half d^2 / (pi eps0 R^2).  With C'_half/eps0 = 0.856 (Eq. (G.25)) and d = 0.860 mm (from the
# pads' odd charge density, proportional to 1/sqrt((x^2 - a^2)(b^2 - x^2)) on a = 0.2 < |x| < b =
# 0.75 mm), R = 200 mm gives -5.0e-6 for a circle; the square box changes this by a factor of order
# 1.  That is four times below the edge error estimated next.
R_HALF = 200.0
# Element size at conductor edges.  The coplanar-strips check of pcbcap (pcbcap.checks,
# strips_free_space) gave 1.03e-4 at an edge size of 5e-4 mm, and the error of a sheet edge falls in
# proportion to the edge size (order 1, pcbcap.study), so 1e-4 mm gives about
# 1.03e-4 x (1e-4 / 5e-4) = 2.1e-5.  In 2-D a small edge size is cheap (pcbcap.meshing).
H_EDGE = 1e-4
# Other sizes, all choices.  The far size is R_HALF/10 (20 mm) in the half-plane domains, where the
# field far from the pads is smooth and weak, and 0.05 mm inside the 0.35-mm block, about seven
# elements across it.  The layer widths: the closed forms of Eqs. (G.27) and (G.41) assume layers of
# infinite width.  In a layer of thickness H between two zero-flux faces the field away from the pads
# decays as exp(-pi x / H) (its lowest mode is cos(pi z / H)), and between the pads' zero-flux plane
# and a grounded plane at depth h as exp(-pi x / (2 h)) (lowest mode sin(pi z / (2 h))).  With the
# widths used, 120 mm for the 1.6-mm layer and at least 40 h for a plane at depth h, these factors
# are e^-235 and e^-63 at the domain's edge, so the truncation of the width changes nothing.

CASES: dict[str, tuple[str, object]] = {}


def case(name: str, title: str):
    def deco(fn):
        CASES[name] = (title, fn)
        return fn
    return deco


def per_eps(res) -> float:
    """C'/eps0 from a per-unit-length result in fF/mm."""
    return res.C_F / EPS0


def mesh_line(res) -> str:
    m, f = res.mesh, res.fem
    return f"mesh {m['elements']} elements, h_edge {m['h_edge']:.1e} mm, {f['dofs']} unknowns (P{f['order']})"


def halfplane_strips(xa: tuple, xb: tuple, below: bool = True, R: float = R_HALF) -> Layout:
    """Electrodes on the edge z = 0 of a half-plane (z < 0 if below, else z > 0), rest of the edge
    insulating, open boundary far away.  Eq. (G.23)/(G.25) setting."""
    lay = Layout(2, "half-plane strips")
    lay.add_segment("z", 0.0, xa, net="A")
    lay.add_segment("z", 0.0, xb, net="B")
    z = (-R, 0.0) if below else (0.0, R)
    lay.set_enclosure({"x": (-R, R), "z": z}, boundary="open")
    lay.set_symmetry(mirror_x=True)
    return lay


# ================================================================================================
@case("G25_pads_halfplane", "Pads on the edge of a half-plane, Eq. (G.25)")
def _g25():
    res = solve_layout(halfplane_strips((PS / 2, X), (-X, -PS / 2)), MeshParams(h_edge=H_EDGE, h_far=R_HALF / 10))
    return dict(numeric=per_eps(res), closed=ana.cps(PW, PS), lines=[mesh_line(res)])


@case("G27_cut_layer", "Pads on a 1.6-mm board whose far face is cut, Eq. (G.27)")
def _g27():
    H, Rl = ana.BOARD_H, 120.0
    lay = Layout(2, "cut layer")
    lay.add_segment("z", 0.0, (PS / 2, X), net="A")
    lay.add_segment("z", 0.0, (-X, -PS / 2), net="B")
    lay.set_enclosure({"x": (-Rl, Rl), "z": (-H, 0.0)}, boundary="open")
    lay.set_symmetry(mirror_x=True)
    res = solve_layout(lay, MeshParams(h_edge=H_EDGE, h_far=1.0))
    return dict(numeric=per_eps(res), closed=ana.cps_layer_cut(PW, PS, H),
                lines=[mesh_line(res), f"layer 1.6 mm thick, {2 * Rl:g} mm wide (the formula assumes infinite width)"])


def block_layout(film: bool, slots_filled: bool = False) -> Layout:
    """The resistor body of Section G.8: |x| < L/2, 0 < z < T, terminations on the end faces and over
    the wrap length A on the top and bottom faces; the faces between the wraps insulating (cut),
    optionally the film's linear potential on the top face, optionally the slots filled with metal."""
    lay = Layout(2, "block")
    if slots_filled:
        lay.add_rect((G / 2, L / 2), (0.0, T), net="A")
        lay.add_rect((-L / 2, -G / 2), (0.0, T), net="B")
    else:
        for net, sgn in (("A", 1), ("B", -1)):
            xe = (G / 2, L / 2) if sgn > 0 else (-L / 2, -G / 2)
            lay.add_segment("x", sgn * L / 2, (0.0, T), net=net)
            lay.add_segment("z", T, xe, net=net)
            lay.add_segment("z", 0.0, xe, net=net)
    if film:
        lay.add_segment("z", T, (-G / 2, G / 2), film=Film("A", "B", LinearProfile("x", -G / 2, G / 2)))
    lay.set_enclosure({"x": (-L / 2, L / 2), "z": (0.0, T)}, boundary="open")
    lay.set_symmetry(mirror_x=True)
    return lay


@case("G28_block_upper", "Body with the slots filled with metal, upper bound, Eq. (G.28)")
def _g28():
    lay = block_layout(film=True, slots_filled=True)
    lay.set_enclosure({"x": (-L / 2, L / 2), "z": (0.0, T)}, boundary="open")
    res = solve_layout(lay, MeshParams(h_edge=H_EDGE, h_far=0.05))
    return dict(numeric=per_eps(res), closed=ana.block_slots_filled(T, G), lines=[mesh_line(res)])


@case("G32_block_lower", "Body with the film's potential released, lower bound, Eq. (G.32)")
def _g32():
    res = solve_layout(block_layout(film=False), MeshParams(h_edge=H_EDGE, h_far=0.05))
    return dict(numeric=per_eps(res), closed=ana.block_without_film(L, T, G)["value"], lines=[mesh_line(res)])


@case("G8_block_with_film", "Body with the film's potential kept and the slots open (bracketed by G.28 and G.32)")
def _g8_true():
    res = solve_layout(block_layout(film=True), MeshParams(h_edge=H_EDGE, h_far=0.05))
    lo, hi = ana.block_without_film(L, T, G)["value"], ana.block_slots_filled(T, G)
    v = per_eps(res)
    pos = (v - lo) / (hi - lo)
    return dict(numeric=v, closed=None, bracket=(lo, hi), position=pos,
                lines=[mesh_line(res), f"lower bound (G.32) {lo:.6f}, upper bound (G.28) {hi:.6f}: "
                       f"the value lies {100 * pos:.1f} % of the way from the lower to the upper bound",
                       f"per 0.5 mm of width at eps_al = 9.7: {EPS0 * 9.7 * v * W:.2f} fF "
                       f"(bracket {EPS0 * 9.7 * lo * W:.2f}-{EPS0 * 9.7 * hi * W:.2f} fF)"])


@case("G33_air_no_film", "Air above the body, electrodes only, Eq. (G.33)")
def _g33():
    res = solve_layout(halfplane_strips((G / 2, X), (-X, -G / 2), below=False), MeshParams(h_edge=H_EDGE, h_far=R_HALF / 10))
    return dict(numeric=per_eps(res), closed=ana.air_flat_without_film(G, X), lines=[mesh_line(res)])


@case("G38_air_with_film", "Air above the body with the film's potential, Eq. (G.38)")
def _g38():
    lay = halfplane_strips((G / 2, X), (-X, -G / 2), below=False)
    lay.add_segment("z", 0.0, (-G / 2, G / 2), film=Film("A", "B", LinearProfile("x", -G / 2, G / 2)))
    res = solve_layout(lay, MeshParams(h_edge=H_EDGE, h_far=R_HALF / 10))
    return dict(numeric=per_eps(res), closed=ana.air_flat_with_film(G, X)["value"], lines=[mesh_line(res)])


def plane_case(h: float):
    """Pads on a layer of thickness h over a ground plane, board surface cut outside the pads, Eq. (G.41).
    The mutual capacitance is C_F; the capacitance of one pad to ground is C_A0 = q_even."""
    Rl = max(40 * h, 20.0)
    lay = Layout(2, f"plane at {h}")
    lay.add_segment("z", 0.0, (PS / 2, X), net="A")
    lay.add_segment("z", 0.0, (-X, -PS / 2), net="B")
    lay.add_segment("z", -h, (-Rl, Rl), net="gnd")
    lay.set_enclosure({"x": (-Rl, Rl), "z": (-h, 0.0)}, boundary="open")
    lay.set_symmetry(mirror_x=True)
    res = solve_layout(lay, MeshParams(h_edge=H_EDGE, h_far=min(1.0, 5 * h)))
    bp = ana.board_over_plane(PW, PS, h)
    return dict(numeric=per_eps(res), closed=bp["mutual"],
                lines=[mesh_line(res), f"to ground: numeric {res.C_A0 / EPS0:.6f}, closed form q_even {bp['to_ground']:.6f}"
                       f" (rel. {res.C_A0 / EPS0 / bp['to_ground'] - 1:+.2e})"],
                to_ground=(res.C_A0 / EPS0, bp["to_ground"]))


@case("G41_plane_0p10", "Pads over a plane 0.10 mm below, Eq. (G.41)")
def _g41a():
    return plane_case(0.10)


@case("G41_plane_0p20", "Pads over a plane 0.20 mm below, Eq. (G.41)")
def _g41b():
    return plane_case(0.20)


@case("G41_plane_0p36", "Pads over a plane 0.36 mm below, Eq. (G.41)")
def _g41c():
    return plane_case(0.36)


@case("G43_guard", "Grounded guard strip 0.2 mm wide in the pad gap, Eq. (G.43)")
def _g43():
    wg = 0.2
    lay = halfplane_strips((PS / 2, X), (-X, -PS / 2))
    lay.add_segment("z", 0.0, (-wg / 2, wg / 2), net="gnd")
    res = solve_layout(lay, MeshParams(h_edge=H_EDGE, h_far=R_HALF / 10))
    gd = ana.guard_in_gap(PW, PS, wg)
    return dict(numeric=per_eps(res), closed=gd["mutual"], to_ground=(res.C_A0 / EPS0, gd["to_guard"]),
                lines=[mesh_line(res), f"pad to guard: numeric {res.C_A0 / EPS0:.6f}, closed form {gd['to_guard']:.6f}"
                       f" (rel. {res.C_A0 / EPS0 / gd['to_guard'] - 1:+.2e})"])


def pins_layout(middle: str, pin4_grounded: bool) -> Layout:
    """Pins 1 (net A) and 3 (net B) of the DSG package on the edge of a half-plane (one medium, per unit
    permittivity), pin 2 between them 'removed', 'thin' (a floating strip like the others) or 'wall'
    (an infinite floating slab, Eq. (G.46)), and optionally pin 4 grounded beyond pin 3."""
    p, b = ana.DSG["pitch"], ana.DSG["b"]
    R = R_HALF
    lay = Layout(2, "pins")
    # Pin 1 = A at +p, pin 3 = B at -p, pin 4 at -2p: the order along the edge is reversed relative to
    # Figure 43 so that A lies at +x, which changes nothing physical.
    lay.add_segment("z", 0.0, (p - b / 2, p + b / 2), net="A")
    lay.add_segment("z", 0.0, (-p - b / 2, -p + b / 2), net="B")
    if middle == "thin":
        lay.add_segment("z", 0.0, (-b / 2, b / 2), net="pin2", floating=True)
    elif middle == "wall":
        lay.add_rect((-b / 2, b / 2), (-R, 0.0), net="pin2", floating=True)
    if pin4_grounded:
        lay.add_segment("z", 0.0, (-2 * p - b / 2, -2 * p + b / 2), net="gnd")
    lay.set_enclosure({"x": (-R, R), "z": (-R, 0.0)}, boundary="open")
    lay.set_symmetry(mirror_x=not pin4_grounded)
    return lay


@case("G45_pins_no_middle", "Pins 1 and 3 with pin 2 removed, Eq. (G.45)")
def _g45():
    res = solve_layout(pins_layout("removed", False), MeshParams(h_edge=H_EDGE, h_far=R_HALF / 10))
    return dict(numeric=per_eps(res), closed=ana.pins(ana.DSG["b"], ana.DSG["pitch"])["without_middle"],
                lines=[mesh_line(res)])


@case("G46_pins_wall", "Pins 1 and 3 with pin 2 as a floating wall, Eq. (G.46)")
def _g46():
    res = solve_layout(pins_layout("wall", False), MeshParams(h_edge=H_EDGE, h_far=R_HALF / 10))
    return dict(numeric=per_eps(res), closed=ana.pins(ana.DSG["b"], ana.DSG["pitch"])["floating_wall"],
                lines=[mesh_line(res)])


@case("pins_thin_middle", "Pins 1 and 3 with pin 2 a thin floating strip (between G.45 and G.46)")
def _pins_thin():
    res = solve_layout(pins_layout("thin", False), MeshParams(h_edge=H_EDGE, h_far=R_HALF / 10))
    pp = ana.pins(ana.DSG["b"], ana.DSG["pitch"])
    v = per_eps(res)
    return dict(numeric=v, closed=None, bracket=(pp["without_middle"], pp["floating_wall"]),
                position=(v - pp["without_middle"]) / (pp["floating_wall"] - pp["without_middle"]),
                lines=[mesh_line(res), f"Rule 4 bracket: {pp['without_middle']:.6f} (removed) to {pp['floating_wall']:.6f} (wall)"])


@case("pins_pin4_grounded", "Effect of grounding pin 4 on the three pin models (numerical only)")
def _pins_pin4():
    out, lines = {}, []
    for middle in ("removed", "thin", "wall"):
        a = solve_layout(pins_layout(middle, False), MeshParams(h_edge=H_EDGE, h_far=R_HALF / 10))
        b = solve_layout(pins_layout(middle, True), MeshParams(h_edge=H_EDGE, h_far=R_HALF / 10))
        out[middle] = (per_eps(a), per_eps(b))
        lines.append(f"pin 2 {middle:7s}: {per_eps(a):.6f} -> {per_eps(b):.6f} with pin 4 grounded "
                     f"({100 * (per_eps(b) / per_eps(a) - 1):+.1f} %)")
    return dict(numeric=out["removed"][1], closed=None, table=out, lines=lines)


@case("A14_pads_under_body", "Pads reaching under the body across the stand-off (approximation 14)")
def _a14():
    """The body block with the film kept, above a stand-off gap t_s, with the pads on the board surface
    reaching under the body (g > s), compared with the same block whose lower face is cut.  Board
    and air outside the block are left out in both (they are the same cut regions), so the difference
    is the coupling across the gap that approximation 14 drops.  eps_al = 9.7, W = 0.5 mm."""
    lines, vals = [], {}
    eps_al = 9.7
    for ts in (0.03, 0.01):
        cut = block_layout(film=True)                               # lower face insulating
        rc = solve_layout(_rescale(cut, eps_al), MeshParams(h_edge=H_EDGE, h_far=0.05))
        full = Layout(2, "block over pads")
        full.add_rect((-L / 2, L / 2), (ts, ts + T), eps_r=eps_al, label="alumina")
        for net, sgn in (("A", 1), ("B", -1)):
            xe = (G / 2, L / 2) if sgn > 0 else (-L / 2, -G / 2)
            full.add_segment("x", sgn * L / 2, (ts, ts + T), net=net)
            full.add_segment("z", ts + T, xe, net=net)
            full.add_rect(xe, (0.0, ts), net=net)                   # solder from the pad up to the bottom wrap
            px = (PS / 2, L / 2) if sgn > 0 else (-L / 2, -PS / 2)
            full.add_segment("z", 0.0, px, net=net)                 # pad under the body
        full.add_segment("z", ts + T, (-G / 2, G / 2), film=Film("A", "B", LinearProfile("x", -G / 2, G / 2)))
        full.set_enclosure({"x": (-L / 2, L / 2), "z": (0.0, ts + T)}, boundary="open")
        full.set_symmetry(mirror_x=True)
        rf = solve_layout(full, MeshParams(h_edge=H_EDGE, h_far=0.05))
        d = (rf.C_F - rc.C_F) * W
        vals[ts] = d
        lines.append(f"t_s = {1000 * ts:.0f} um: cut model {rc.C_F:.3f} fF/mm, with the pads under the body "
                     f"{rf.C_F:.3f} fF/mm; difference over W = 0.5 mm: {d:+.2f} fF")
    lines.append("Table G.6 states 0.3 fF (a parallel-plate estimate) for t_s = 30 um")
    return dict(numeric=vals[0.03], closed=None, table={str(k): v for k, v in vals.items()}, lines=lines, unit="fF")


def _rescale(lay: Layout, eps: float) -> Layout:
    """The block layout with its interior filled with alumina of permittivity eps (the block layout
    itself has only the enclosure medium; here it becomes alumina)."""
    from pcbcap import materials as mat
    lay.enclosure.material = mat.custom("alumina", eps)
    return lay


# ================================================================================================
def run(name: str, record: str | None) -> dict:
    title, fn = CASES[name]
    print(f"[{name}] {title}")
    t0 = time.perf_counter()
    out = fn()
    dt = time.perf_counter() - t0
    for line in out.get("lines", []):
        print(f"  {line}")
    unit = out.get("unit", "C'/eps0")
    print(f"  numerical   {out['numeric']:.8f} ({unit})")
    if out.get("closed") is not None:
        rel = out["numeric"] / out["closed"] - 1
        out["rel_error"] = rel
        print(f"  closed form {out['closed']:.8f}")
        print(f"  rel. difference {rel:+.3e}")
    print(f"  time {dt:.1f} s")
    out["title"], out["seconds"] = title, dt
    if record:
        p = Path(record)
        data = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
        data[name] = {k: v for k, v in out.items() if k != "lines"} | {"lines": out.get("lines", [])}
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data, indent=1, default=float), encoding="utf-8", newline="\n")
    return out


def main() -> int:
    lower_priority(2)
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    r = sub.add_parser("run")
    r.add_argument("name")
    r.add_argument("--record", default=None)
    a = ap.parse_args()
    if a.cmd == "list":
        for k, (t, _) in CASES.items():
            print(f"{k:22s} {t}")
        return 0
    run(a.name, a.record)
    return 0


if __name__ == "__main__":
    sys.exit(main())
