"""The feedback network of an OPA846 in SOT-23-5: three layouts, two resistor sizes, in three dimensions.

Usage:
    python g_opa846_3d.py list
    python g_opa846_3d.py estimate                      (mesh-size estimates only, no solves)
    python g_opa846_3d.py run <case> [--record <json>]

Why this script exists
----------------------
The OPA846 has no FB pin.  In its SOT-23-5 package the output (pin 1) and the inverting input
(pin 4) sit at diagonally opposite corners, 2.6 mm apart across and 1.9 mm along the package
(datasheet SBOS250E, p. 2 and p. 27), so the feedback resistor needs a route between them, and that
route, not the resistor alone, sets much of the parasitic capacitance.  Section G.13.5 of the note
infers about 0.3 pF on a bench board with this amplifier, but that board's layout is not recorded
and may be a poor one, so its value is no benchmark for these layouts.  This script computes three
layouts that the datasheet's advice allows (p. 18, item c: keep the feedback resistor close to the
output pin; where both sides of the board carry parts, put it directly under the package on the
other side):

  double_sided : R_F on the bottom side under the package, reached through vias next to pins 1 and 4;
  under_body   : R_F above pin 1 on the top side, with a trace from its far end running under the
                 package body, between the pad rows, to pin 4;
  around       : R_F below pin 4 on the top side, with a trace from pin 1 around the outside of the
                 package.

Every case uses 0402 or 0603 resistors on their IPC-7351 land patterns (companion note Table G.2), an
FR-4 board 1.6 mm thick (eps_r 4.2) with ground planes 0.2 mm inside each face, both windowed around
the package and the feedback network (datasheet p. 18, item a), and the other pins at AC ground:
pin 2 (-VS) and pin 5 (+VS) through their decoupling capacitors, pin 3 (the non-inverting input) as
in a transimpedance amplifier.

Stated assumptions (the datasheet does not dimension them):
  trace width 0.2 mm; 0.3 mm of clearance between a pin pad and the resistor's pads; vias with a
  0.3-mm drill (modelled as the square barrel with the round barrel's far field, pcbcap.packages) and
  0.55-mm pads; window margin 0.5 mm around the package's pads and the network; a four-layer board
  with its two inner ground planes 0.2 mm inside each face (no stack-up is given; this is one
  common choice); stand-off of the resistor 30 um; termination metal 15 um (as in g_resistor_3d.py).

Mesh: one level, refine 5.66, for every layout.  At that level the edge size is capped at the
15-um termination (pcbcap.meshing), so a second level at refine 4.0 (under_body_0402_fine) keeps the
same edge size and changes only the core and far sizes: it does not test the edge zone, which
carries the dominant discretisation error.  That error is not measured for these layouts.  By
analogy with the 0402 study of g_resistor_3d.py, where the 0402 at its 15-um level lies about 0.4 %
above its mesh-extrapolated value (Section G.14.5 of the note gives the current figure), it is
expected to be of the order of half a per cent.
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

from pcbcap import materials as mat                       # noqa: E402
from pcbcap import packages as pk                          # noqa: E402
from pcbcap import parts, study                            # noqa: E402
from pcbcap.meshing import MeshParams, build_mesh          # noqa: E402

EPS_PCB, EPS_AL = 4.2, 9.7
H = 1.6                      # board thickness
PLANE_DEPTHS = (0.2, 1.4)    # ground planes 0.2 mm inside each face (assumed four-layer stack)
TRACE = 0.2                  # trace width
CLEAR = 0.3                  # clearance from a pin pad's edge to the resistor's pad
MARGIN = 0.5                 # plane window beyond the package's pads and the network
BASE = MeshParams(h_edge=0.00375, h_core=0.045)
# Edge size of the grounded pins at refine 1: twice the network's h_edge there.  The ratio changes with
# refine, because the network's edge size is capped at the 15-um termination and the grounded pins'
# is not: at refine 5.66 they get 42.5 um against the network's 15 um (2.83 times), at refine 4.0
# 30 um against 15 um (2 times).  Whether the coarser size matters was not checked
# (pcbcap.packages.add_sot23).
GROUND_EDGE = 0.0075
NETS = {1: "A", 2: "gnd", 3: "gnd", 4: "B", 5: "gnd"}     # pin 1 output, pin 4 inverting input
LAYOUTS = ("double_sided", "under_body", "around")
SIZES = ("0402", "0603")


def opa846_layout(layout: str, size: str, half: float = 8.0, with_resistor: bool = True,
                  with_package: bool = True, planes: bool = True):
    """Build one layout.  ``with_resistor`` False leaves out R_F (its pads, body and film) but keeps
    the pins, traces and vias; ``with_package`` False leaves out the amplifier's leads and body (its
    pads stay).  The two switches separate the contributions of the routing and of the resistor."""
    pkg = pk.Sot23()
    res = parts.ChipResistor.from_size(size, body=mat.custom("alumina", EPS_AL))
    pads = parts.LandPattern.from_size(size)
    mount = parts.Mount()
    hp = pads.s / 2 + pads.w / 2          # distance from the resistor's centre to each pad's centre
    x1, y1 = pkg.pin_xy(1)                # (-1.3, 0.95)
    x4, y4 = pkg.pin_xy(4)                # (+1.3, -0.95)
    pad_edge = pkg.pitch + pkg.pad_width / 2     # outer edge of pins 1/5 (and 3/4) in y: 1.25
    items_top, items_bottom, traces = [], [], []

    if layout == "double_sided":
        # Vias in the inner part of pins 1 and 4, at x = -/+0.95 (the pads span 0.75-1.85 from the
        # centre line); R_F centred under the package on the bottom side, A at -x, B at +x; bottom
        # traces from each via straight to y = 0 and along x to the centre of the resistor's pad.
        xv = 0.95
        vias = [(-xv, y1, "A"), (xv, y4, "B")]
        r_center = (0.0, 0.0)
        r_side = "bottom"
        traces.append(([(-xv, y1), (-xv, 0.0), (-hp, 0.0)], "A", "bottom"))
        traces.append(([(xv, y4), (xv, 0.0), (hp, 0.0)], "B", "bottom"))
    elif layout == "under_body":
        # R_F above pin 1, its A pad centred over pin 1, 0.3 mm above that pin's pad; a short trace
        # joins them; from the B pad a trace runs down at the B pad's x, under the body, to the row of
        # pin 4 and along it to the centre of pin 4's pad.
        vias = []
        y_r = pad_edge + CLEAR + pads.l / 2
        x_r = x1 + hp
        r_center = (x_r, y_r)
        r_side = "top"
        traces.append(([(x1, y1), (x1, y_r)], "A", "top"))
        traces.append(([(x_r + hp, y_r), (x_r + hp, y4), (x4, y4)], "B", "top"))
    elif layout == "around":
        # R_F below pin 4, its B pad centred under pin 4, 0.3 mm below that pin's pad; a short trace
        # joins them; from pin 1 a trace runs out to x = -2.3 (0.45 mm beyond the pads' outer ends),
        # down the outside of the package to the resistor's row and along it to the A pad.
        vias = []
        y_r = -(pad_edge + CLEAR + pads.l / 2)
        x_r = x4 - hp
        r_center = (x_r, y_r)
        r_side = "top"
        traces.append(([(x4, y4), (x4, y_r)], "B", "top"))
        traces.append(([(x1, y1), (-2.3, y1), (-2.3, y_r), (x_r - hp, y_r)], "A", "top"))
    else:
        raise ValueError(layout)

    # The resistor's nets: resistor_assembly puts nets[0] at +x.  In every layout A is to the left.
    r_items = pk.resistor_assembly(res, pads, mount, nets=("B", "A"), x0=r_center[0], y0=r_center[1],
                                   side=r_side, board_thickness=H, name="RF")

    # Window in both planes: the bounding box (in x, y) of the package's pads, the resistor's items,
    # the traces and the vias, grown by MARGIN.
    xs, ys = [], []
    for pin in (1, 2, 3, 4, 5):
        px, py = pkg.pin_xy(pin)
        xs += [px - pkg.pad_length / 2, px + pkg.pad_length / 2]
        ys += [py - pkg.pad_width / 2, py + pkg.pad_width / 2]
    for it in r_items:
        xs += list(it.x) if hasattr(it, "x") else list(it.spans["x"])
        ys += list(it.y) if hasattr(it, "y") else list(it.spans["y"])
    for pts, _, _ in traces:
        xs += [p[0] for p in pts]
        ys += [p[1] for p in pts]
    window = {"x": (min(xs) - MARGIN, max(xs) + MARGIN), "y": (min(ys) - MARGIN, max(ys) + MARGIN)}
    plane_list = [parts.Plane(depth=d, cutout=window, mesh_size=0.04) for d in PLANE_DEPTHS] if planes else []
    board = parts.Board(thickness=H, material=mat.custom("FR4", EPS_PCB), planes=plane_list)
    lay = parts.board_layout(board, half, name=f"OPA846 {layout} {size}")
    if with_package:
        # The grounded pins (2, 3, 5) get edge elements twice as large as the network's: they only
        # shield, and this halves the elements spent on them (packages.add_sot23).
        pk.add_sot23(lay, pkg, NETS, ground_mesh=GROUND_EDGE)
    else:   # the pads alone, so that the routing still ends where it does
        for pin in (1, 2, 3, 4, 5):
            px, py = pkg.pin_xy(pin)
            parts.add_pad(lay, (px - pkg.pad_length / 2, px + pkg.pad_length / 2),
                          (py - pkg.pad_width / 2, py + pkg.pad_width / 2), 0.035, NETS[pin], name=f"pin{pin}-pad")
    for x, y, net in vias:
        pk.add_via(lay, x, y, net, H, name=f"via{net}")
    for k, (pts, net, side) in enumerate(traces):
        pk.add_trace_path(lay, pts, TRACE, net, side=side, board_thickness=H, name=f"trace{net}{k}")
    if with_resistor:
        for it in r_items:
            lay.add(it)
    return lay


# ================================================================================================
def estimate(levels=(5.66, 4.0, 2.83)) -> None:
    for layout in LAYOUTS:
        for size in SIZES:
            lay = opa846_layout(layout, size)
            est = [round(build_mesh(lay, replace(BASE, refine=r), estimate_only=True) / 1e3) for r in levels]
            print(f"{layout:13s} {size}: estimated thousands of elements at refine {levels}: {est}")


CASES: dict[str, tuple[str, object]] = {}


def network_case(layout: str, size: str, levels=(5.66,), half: float = 8.0):
    def fn():
        lines, out = [], {"levels": list(levels)}
        for lvl in levels:
            r = study.solve_layout(opa846_layout(layout, size, half=half), replace(BASE, refine=lvl), order=2)
            out[f"refine_{lvl}"] = dict(C_F=r.C_F, C_A0=r.C_A0, C_B0=r.C_B0, shares=r.contributions,
                                        dofs=r.fem["dofs"], elements=r.mesh["elements"], seconds=r.fem["total_seconds"])
            lines.append(f"refine {lvl}: C_F = {r.C_F:.2f} fF, C_A0 = {r.C_A0:.1f} fF, C_B0 = {r.C_B0:.1f} fF; "
                         f"{r.mesh['elements']} elements, {r.fem['dofs']} unknowns, {r.fem['total_seconds']:.0f} s")
        return dict(table=out, lines=lines)
    return fn


def parts_case(layout: str, size: str, level: float = 5.66):
    """The same layout without R_F, and without the package's leads and body, at one mesh: how much of
    C_F the routing and the package carry by themselves."""
    def fn():
        lines, out = [], {}
        p = replace(BASE, refine=level)
        for key, kw in (("whole", {}), ("no_resistor", dict(with_resistor=False)),
                        ("no_package", dict(with_package=False)), ("no_planes", dict(planes=False))):
            r = study.solve_layout(opa846_layout(layout, size, **kw), p, order=2)
            out[key] = dict(C_F=r.C_F, C_A0=r.C_A0, C_B0=r.C_B0)
            lines.append(f"{key:12s}: C_F = {r.C_F:.2f} fF, C_B0 = {r.C_B0:.1f} fF, {r.fem['total_seconds']:.0f} s")
        return dict(table=out, level=level, lines=lines)
    return fn


for _lay in LAYOUTS:
    for _size in SIZES:
        CASES[f"{_lay}_{_size}"] = (f"OPA846 SOT-23-5, {_lay.replace('_', ' ')}, {_size} R_F, refine 5.66",
                                    network_case(_lay, _size))
    CASES[f"{_lay}_0402_parts"] = (f"Contributions in the {_lay.replace('_', ' ')} layout, 0402 R_F",
                                   parts_case(_lay, "0402"))
# Checks of two numerical choices on one layout: a finer mesh (refine 4.0: the same 15-um edge size,
# which the thinnest feature caps, but core and far sizes 30 % smaller; it does not test the edge zone,
# see the module docstring), and a larger enclosure (16 mm; with two grounded planes most of the even
# field ends on them, so little change is expected).  The planes' edge size (mesh_size 0.04 mm at
# refine 1) is not checked in these layouts; in the OPA855 network the same choice changed C_F by
# about 0.02 fF when halved (g_resistor_3d.py, opa855_plane_edge).
CASES["under_body_0402_fine"] = ("Under-body layout, 0402, at refine 4.0 (mesh check)",
                                 network_case("under_body", "0402", levels=(4.0,)))
CASES["under_body_0402_enclosure16"] = ("Under-body layout, 0402, enclosure 16 mm (enclosure check)",
                                        network_case("under_body", "0402", half=16.0))


def run(name: str, record: str | None) -> dict:
    title, fn = CASES[name]
    print(f"[{name}] {title}")
    t0 = time.perf_counter()
    out = fn()
    out["seconds"], out["title"] = time.perf_counter() - t0, title
    for line in out.get("lines", []):
        print(f"  {line}")
    print(f"  time {out['seconds']:.0f} s")
    if record:
        p = Path(record)
        data = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
        data[name] = out
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data, indent=1, default=float), encoding="utf-8", newline="\n")
    return out


def main() -> int:
    study.lower_priority(2)
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    sub.add_parser("estimate")
    r = sub.add_parser("run")
    r.add_argument("name")
    r.add_argument("--record", default=None)
    a = ap.parse_args()
    if a.cmd == "list":
        for k, (t, _) in CASES.items():
            print(f"{k:28s} {t}")
    elif a.cmd == "estimate":
        estimate()
    else:
        run(a.name, a.record)
    return 0


if __name__ == "__main__":
    sys.exit(main())
