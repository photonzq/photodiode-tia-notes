"""Feedback networks around amplifiers in eight-lead packages (SOIC-8 and PDIP-8), in three dimensions.

Usage:
    python g_eight_lead_3d.py list
    python g_eight_lead_3d.py estimate                  (element estimates only, no solves)
    python g_eight_lead_3d.py run <case> [--record <json>]

Why this script exists
----------------------
Section G.14.10 of the note computes the OPA846 in SOT-23-5.  The same amplifier also comes in SO-8
(data sheet SBOS250E, p. 2), and the precision and electrometer amplifiers of the high-gain note come
in SOIC-8 and PDIP-8: the OPA627/OPA637 in SOIC-8 (SBOS165C, p. 3; its PDIP version was withdrawn,
p. 33), the LMC6001 in PDIP-8 (SNOS694I, p. 3), and the ADA4530-1 and the LMP7721 in SOIC-8 with
pinouts of their own (ADA4530-1 Rev. C, p. 10; LMP7721 SNOSAW6E, p. 3).  The package models are
pcbcap.packages.Soic8 and Dip8, whose docstrings give every dimension with its source.

The layouts below are proposals, built so that they can be looked at before anything is solved.
In all of them net A is the output and net B the inverting input; the non-inverting input, both
supplies and every guard are AC ground (in a transimpedance amplifier the guard is held at the
potential of +IN), and each unconnected pin is a floating conductor of its own.

The first five use the standard pinout of a single amplifier (OPA846 SO-8, OPA637 SOIC-8, LMC6001
PDIP-8): pin 2 the inverting input, pin 3 the non-inverting input, pin 4 the negative supply, pin 6
the output, pin 7 the positive supply, and pins 1, 5 and 8 not connected inside.

  so8_double_sided   R_F on the bottom side, centred under the package, reached through vias at the
                     inner ends of the pads of pins 2 and 6.  This is what the OPA846 data sheet
                     advises for boards with parts on both sides (p. 18, item c), and the SO-8
                     counterpart of the SOT-23 layout double_sided of g_opa846_3d.py.
  so8_vias_under     as so8_double_sided, but with the vias under the body, 0.3 mm inside the inner
                     ends of the pads, each joined to its pad by a short trace on the top side.  In
                     so8_double_sided the via pads overlap the lead pads, so the vias lie under the
                     solder paste; TI's land-pattern notes ask for such vias to be "filled, plugged or
                     tented" (OPA855 data sheet SBOS622D, p. 39, note 5).  Vias beside the pads, under
                     the body, are tented by the solder mask and need nothing special.  For the 0805
                     of the high-gain case the vias would land on the resistor's own pads, so the
                     variant is built for the 0402 only.
  so8_under_body     R_F on the top side, beyond the end of the package at pins 4 and 5, with a trace
                     from each of pins 2 and 6 running inward under the body and along it to the
                     resistor (the SO-8 counterpart of the SOT-23 layout under_body).
  dip8_bottom        PDIP-8, R_F on the solder side between pins 2 and 6, centred under the package,
                     with traces on the solder side from the pads of pins 2 and 6.
  dip8_bottom_guard  as dip8_bottom, with a grounded guard ring around the input node on both sides:
                     on the solder side around the pad of pin 2, its trace and the resistor's input
                     pad, passing under the resistor between its pads; on the component side around
                     the pad of pin 2.  Both rings are joined to the pad of pin 3 (+IN), to which a
                     guard is connected in a transimpedance amplifier: the solder-side ring runs over
                     that pad, the component-side ring through a short trace.  Guard rings of this
                     kind are shown in the LMC6001 data sheet (p. 19) and the OPA627/OPA637 data sheet
                     (p. 21).

The last two follow the layouts that the makers of these amplifiers publish:

  ada4530            ADA4530-1: pin 1 +IN, 2 GRD, 3 IC, 4 V-, 5 V+, 6 OUT, 7 GRD, 8 -IN (Rev. C, p. 10;
                     pin 3 must go to V- or stay unconnected, and is left unconnected here).  The TIA
                     layout of the data sheet (p. 42, Figure 122): R_F beside the row of -IN, GRD and
                     OUT and parallel to it, one end at -IN (pin 8), the other at OUT (pin 6); a guard
                     ring around pin 8, its trace and the resistor's input half, passing between the
                     resistor's pads and driven from the guard pin 7, which lies between -IN and OUT.
                     On one side of the board, as in the figure; the guard plane and via fence of p. 43
                     are left out, and the figure's filled guard shape is drawn as a ring.
  lmp7721            LMP7721: pin 1 +IN, 2 N/C, 3 V-, 4 OUT, 5 N/C, 6 V+, 7 N/C, 8 -IN (SNOSAW6E, p. 3).
                     The layout example of the data sheet (p. 25, Section 10.1 and Figure 54): the guard
                     encircles both inputs, which lie at one end of the package; it is tied to the two
                     unconnected pins beside them (2 and 7); and it runs on both sides of the board,
                     joined (here by two vias).  R_F stands beside pin 8 as for the ADA4530-1, with the
                     guard passing between its pads.  The output, pin 4, sits at the far corner, so its
                     trace runs around the other end of the package.  On the board the guard loop is
                     closed under the body between pins 2 and 7; the data sheet's figure closes it
                     through those two pins and the lead frame.

Two board stack-ups are used.  The high-speed cases (OPA846, R_F of 0402 or 0603) have the
four-layer board of g_opa846_3d.py: ground planes 0.2 mm inside each face, windowed around the
package and the network.  The high-gain cases (OPA637, LMC6001, ADA4530-1, LMP7721) have a two-layer
board with no ground plane near the network, the usual practice around a high-impedance input; the
grounded enclosure is then the only distant ground.

Resistors.  0402 for the 2-kohm OPA846 cases.  1206 for the high-gain cases, the size that the
high-gain note's own estimate of the resistor's capacitance takes (its Section 3.4: 3.2 x 1.6 mm),
except the OPA637 case, which keeps an 0805: its vias at the inner ends of the pads of pins 2 and 6
would land on the pads of a 1206.

Mesh.  Every conductor except the resistor (its pads, solder, terminations and film) gets the edge
size that g_opa846_3d.py gives the grounded pins, 7.5 um at refine 1, instead of the layout's own
edge size, which the 15-um termination caps at 15 um (pcbcap.meshing.resolve_params); the resistor
keeps its 15-um edges, because most of the coupling sits there: in the 0402 model of Section
G.14.4, 19.4 of 40.3 fF lie in the alumina between the wraps (Section G.14.7, the paragraph beside
Figure 46).  The OPA846 cases run at refine 5.66, the level of g_opa846_3d.py (the coarse edges are
then 42 um), the high-gain cases at refine 11.3 (85 um; the core and far sizes double as well).
Without the coarser edges the leads, holes, traces and guard rings of these packages, with several
times the edge length of a SOT-23 network, would need 1.4-2.5 million elements (meshing's
a-priori estimate times 0.44, the ratio of meshed to estimated elements in g_opa846_3d.py).  The
workstation has 16 GB, about 6 GB of it free while in use, and a solve takes about 4 GB per
million elements (g_opa846_3d.py: 3.5-4.5 GB for 0.86-1.20 million), so every case is limited to
1.25 million elements (MAX_ELEMENTS, about 5 GB): a larger mesh is refused before any solver
memory is spent.  The OPA846 cases of g_opa846_3d.py kept the signal pins at the network's edge size;
here they are coarse too.  Two checks measure what these choices change.  The published SOT-23-5
layout double_sided (0402) solved with this policy (case opa846_sot23_double_sided_0402_policy)
gives C_F 0.12 fF (0.21 %) above the published value, C_A0 and C_B0 0.4 % above it, with half the
elements; the OPA637 case at refine 16 instead of 11.3 (opa637_so8_bottom_0805_refine16) moves C_F by
0.09 fF (0.1 %).  The PDIP cases run at refine 16 (LAYOUTS), the other high-gain cases at 11.3.

Stated assumptions (no document dimensions them), as in g_opa846_3d.py: trace width 0.2 mm, 0.3 mm
of clearance, vias of 0.3-mm drill with 0.55-mm pads, plane window 0.5 mm beyond the network,
resistor stand-off 30 um, termination metal 15 um; the guard ring is 0.3 mm wide with 0.3 mm of
clearance to the input node.
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
from pcbcap.geometry import Conductor                      # noqa: E402
from pcbcap.meshing import MeshParams, build_mesh          # noqa: E402

EPS_PCB, EPS_AL = 4.2, 9.7
H = 1.6                      # board thickness
PLANE_DEPTHS = (0.2, 1.4)    # four-layer board of the high-speed cases
TRACE = 0.2                  # trace width
CLEAR = 0.3                  # clearance between copper of different nets
MARGIN = 0.5                 # plane window beyond the package's pads and the network
VIA_PAD = 0.55               # via pad (packages.add_via)
GUARD = 0.3                  # guard ring width
BASE = MeshParams(h_edge=0.00375, h_core=0.045)
GROUND_EDGE = 0.0075         # edge element size of the grounded pins at refine 1 (as g_opa846_3d.py)

# Standard pinout of a single amplifier (OPA846 SO-8, OPA627/OPA637 SOIC-8, LMC6001 PDIP-8).
SINGLE_NETS = {1: "nc1", 2: "B", 3: "gnd", 4: "gnd", 5: "nc5", 6: "A", 7: "gnd", 8: "nc8"}
SINGLE_FLOATING = {1: True, 5: True, 8: True}
NET_LABELS = {"A": "net A (output, pin 6)", "B": "net B (inverting input, pin 2)",
              "nc1": "pin 1", "nc5": "pin 5", "nc8": "pin 8"}


def _resistor(size: str):
    res = parts.ChipResistor.from_size(size, body=mat.custom("alumina", EPS_AL))
    pads = parts.LandPattern.from_size(size)
    return res, pads, parts.Mount(), pads.s / 2 + pads.w / 2     # hp: resistor centre to pad centre


def _xy_extent(items):
    xs, ys = [], []
    for it in items:
        xs += list(it.x) if hasattr(it, "x") else list(it.spans["x"])
        ys += list(it.y) if hasattr(it, "y") else list(it.spans["y"])
    return xs, ys


def _ring(lay, x: tuple[float, float], y: tuple[float, float], side: str, name: str) -> None:
    """A grounded ring of width GUARD around the interior x * y, on the top or bottom copper."""
    z = (0.0, 0.035) if side == "top" else (-H - 0.035, -H)
    (x0, x1), (y0, y1), w = x, y, GUARD
    for k, (bx, by) in enumerate((((x0 - w, x1 + w), (y1, y1 + w)), ((x0 - w, x1 + w), (y0 - w, y0)),
                                  ((x0 - w, x0), (y0, y1)), ((x1, x1 + w), (y0, y1)))):
        lay.add_box(bx, by, z, net="gnd", name=f"{name}{k}")


def so8_layout(layout: str, size: str, planes: bool = True, half: float = 8.0, title: str = ""):
    """An amplifier with the standard pinout in SOIC-8 and its feedback resistor (module docstring)."""
    pkg = pk.Soic8()
    res, pads, mount, hp = _resistor(size)
    x2, y2 = pkg.pin_xy(2)                               # (-2.7, +0.635): inverting input, B
    x6, y6 = pkg.pin_xy(6)                               # (+2.7, -0.635): output, A
    inner = pkg.pad_row / 2 - pkg.pad_length / 2         # 1.925: inner end of the pads
    vias, traces = [], []
    # The bottom traces start at the edge of the via pad that faces the resistor, not at the via's
    # centre: the copper is the same (the trace's end lies inside the via pad either way), but a
    # trace begun at the centre ends half a trace width beyond it, at y = -0.735, which for the
    # 0805 is 10 um from its pad's edge at -0.725.  pcbcap.meshing caps the edge size at the layout's
    # smallest feature, the closest pair of distinct planes, so that internal plane would set it.
    yv = VIA_PAD / 2
    if layout == "double_sided":
        xv = inner + VIA_PAD / 2                         # 2.2: the via pad flush with the pad's inner end
        vias = [(-xv, y2, "B"), (xv, y6, "A")]
        r_center, r_side = (0.0, 0.0), "bottom"
        traces.append(([(xv, y6 + yv), (xv, 0.0), (hp, 0.0)], "A", "bottom"))
        traces.append(([(-xv, y2 - yv), (-xv, 0.0), (-hp, 0.0)], "B", "bottom"))
    elif layout == "vias_under":
        xv = inner - CLEAR - VIA_PAD / 2                 # 1.35: via pad 0.3 mm inside the pad's inner end
        if hp + pads.w / 2 + CLEAR > xv - VIA_PAD / 2 + 1e-9:
            raise ValueError("the vias would touch the resistor's pads; this variant is for small parts")
        vias = [(-xv, y2, "B"), (xv, y6, "A")]
        r_center, r_side = (0.0, 0.0), "bottom"
        traces.append(([(xv, y6), (x6, y6)], "A", "top"))           # via to pad, under the body
        traces.append(([(-xv, y2), (x2, y2)], "B", "top"))
        traces.append(([(xv, y6 + yv), (xv, 0.0), (hp, 0.0)], "A", "bottom"))
        traces.append(([(-xv, y2 - yv), (-xv, 0.0), (-hp, 0.0)], "B", "bottom"))
    elif layout == "under_body":
        y_end = -(1.5 * pkg.pitch + pkg.pad_width / 2)   # -2.205: outer edge of the pads of pins 4 and 5
        y_r = y_end - CLEAR - pads.l / 2                 # the resistor's pads 0.3 mm beyond them
        r_center, r_side = (0.0, y_r), "top"
        xt = inner - 0.5                                 # 1.425: traces 0.5 mm inside the pads' inner ends
        traces.append(([(x6, y6), (xt, y6), (xt, y_r), (hp, y_r)], "A", "top"))
        traces.append(([(x2, y2), (-xt, y2), (-xt, y_r), (-hp, y_r)], "B", "top"))
    else:
        raise ValueError(layout)
    r_items = pk.resistor_assembly(res, pads, mount, nets=("A", "B"), x0=r_center[0], y0=r_center[1],
                                   side=r_side, board_thickness=H, name="RF")
    xs, ys = _xy_extent(r_items)
    for pin in range(1, 9):
        px, py = pkg.pin_xy(pin)
        xs += [px - pkg.pad_length / 2, px + pkg.pad_length / 2]
        ys += [py - pkg.pad_width / 2, py + pkg.pad_width / 2]
    for pts, _, _ in traces:
        xs += [p[0] for p in pts]
        ys += [p[1] for p in pts]
    window = {"x": (min(xs) - MARGIN, max(xs) + MARGIN), "y": (min(ys) - MARGIN, max(ys) + MARGIN)}
    plane_list = [parts.Plane(depth=d, cutout=window, mesh_size=0.04) for d in PLANE_DEPTHS] if planes else []
    board = parts.Board(thickness=H, material=mat.custom("FR4", EPS_PCB), planes=plane_list)
    lay = parts.board_layout(board, half, name=title or f"SOIC-8 {layout} {size}")
    pk.add_soic8(lay, pkg, SINGLE_NETS, floating=SINGLE_FLOATING, ground_mesh=GROUND_EDGE)
    for x, y, net in vias:
        pk.add_via(lay, x, y, net, H, name=f"via{net}")
    for k, (pts, net, side) in enumerate(traces):
        pk.add_trace_path(lay, pts, TRACE, net, side=side, board_thickness=H, name=f"trace{net}{k}")
    for it in r_items:
        lay.add(it)
    return lay


def dip8_layout(layout: str, size: str, half: float = 12.0, title: str = ""):
    """An amplifier with the standard pinout in PDIP-8 and its feedback resistor (module docstring)."""
    pkg = pk.Dip8()
    res, pads, mount, hp = _resistor(size)
    x2, y2 = pkg.pin_xy(2)                               # (-3.81, +1.27): inverting input, B
    x6, y6 = pkg.pin_xy(6)                               # (+3.81, -1.27): output, A
    if layout not in ("bottom", "bottom_guard"):
        raise ValueError(layout)
    r_items = pk.resistor_assembly(res, pads, mount, nets=("A", "B"), x0=0.0, y0=0.0, side="bottom",
                                   board_thickness=H, name="RF")
    traces = [([(x6, y6), (x6, 0.0), (hp, 0.0)], "A", "bottom"),
              ([(x2, y2), (x2, 0.0), (-hp, 0.0)], "B", "bottom")]
    board = parts.Board(thickness=H, material=mat.custom("FR4", EPS_PCB), planes=[])
    lay = parts.board_layout(board, half, name=title or f"PDIP-8 {layout} {size}")
    pk.add_dip8(lay, pkg, SINGLE_NETS, H, floating=SINGLE_FLOATING, ground_mesh=GROUND_EDGE)
    for k, (pts, net, side) in enumerate(traces):
        pk.add_trace_path(lay, pts, TRACE, net, side=side, board_thickness=H, name=f"trace{net}{k}")
    for it in r_items:
        lay.add(it)
    if layout == "bottom_guard":
        hps = pkg.pad_side / 2                           # half side of a pin pad, 0.709
        # Solder side: around the pad of pin 2, its trace and the resistor's input pad (x up to -s/2);
        # the ring's right side runs under the resistor, centred between its pads.
        x_lo = x2 - hps - CLEAR
        x_hi = -GUARD / 2
        y_hi = y2 + hps + CLEAR
        # 0.35 mm below the resistor's input pad rather than 0.3: at 0.3 the ring's lower edge
        # (y = -1.5000 for the 1206) would lie 2.5 um from the edge of pin 3's lead (-1.4975), and
        # pcbcap.meshing caps the edge size at the layout's smallest feature, the closest pair of
        # distinct planes.  At 0.35 the nearest plane, the side of pin 3's hole, is 59 um away.
        y_lo = min(-pads.l / 2, -TRACE / 2) - CLEAR - 0.05
        _ring(lay, (x_lo, x_hi), (y_lo, y_hi), "bottom", "guard-bottom")
        # Component side: around the pad of pin 2, joined to the pad of pin 3 (+IN) by a short trace
        # from the ring's lower side, so that both rings are held at the potential of +IN by copper,
        # as on a board.  (The solver keeps every grounded conductor at 0 V whether it is joined or
        # not, so the trace changes the geometry that is drawn, not the condition that is imposed.)
        x3, y3 = pkg.pin_xy(3)                           # (-3.81, -1.27): +IN, the guard's potential
        _ring(lay, (x2 - hps - CLEAR, x2 + hps + CLEAR), (y2 - hps - CLEAR, y2 + hps + CLEAR), "top", "guard-top")
        pk.add_trace_path(lay, [(x3, y2 - hps - CLEAR - GUARD / 2), (x3, y3)], GUARD, "gnd", side="top",
                          board_thickness=H, name="guard-top-link")
    return lay


def _beside_pin8(pkg, pads):
    """Centre of a resistor standing along y beside the right pin row, its pads level with pins 8
    and 6 (pin pitch 1.27 mm; for a 1206 the pad centres are 2 x 1.45 = 2.9 mm apart, the pins
    2 x 1.27 = 2.54 mm), 0.3 mm beyond the outer ends of the pin pads."""
    outer = pkg.pad_row / 2 + pkg.pad_length / 2         # 3.475: outer end of the pin pads
    y8, y6 = pkg.pin_xy(8)[1], pkg.pin_xy(6)[1]
    return outer + CLEAR + pads.l / 2, (y8 + y6) / 2


def _guard_geometry(pkg, pads, x_r, y_r, hp):
    """The lines of a guard around pin 8, its trace and the input pad of a resistor standing along y
    at (x_r, y_r) (module docstring, ada4530 and lmp7721): the centre line of its lower run, which
    passes between the resistor's pads and between the pads of pins 8 and 7, 0.3 mm from the input
    pads; of its inner run, under the body, 0.3 mm inside pin 8's pad; of its top and outer runs,
    0.3 mm beyond the pad of pin 8 and the resistor's input pad."""
    inner = pkg.pad_row / 2 - pkg.pad_length / 2         # 1.925
    y8 = pkg.pin_xy(8)[1]
    pin8_bottom, pin8_top = y8 - pkg.pad_width / 2, y8 + pkg.pad_width / 2
    rb_bottom, rb_top = y_r + hp - pads.w / 2, y_r + hp + pads.w / 2      # the resistor's input pad
    y_g = min(pin8_bottom, rb_bottom) - CLEAR - GUARD / 2
    x_in = inner - CLEAR - GUARD / 2
    y_top = max(pin8_top, rb_top) + CLEAR + GUARD / 2
    x_out = x_r + pads.l / 2 + CLEAR + GUARD / 2
    return y_g, x_in, y_top, x_out


ADA4530_NETS = {1: "gnd", 2: "gnd", 3: "nc3", 4: "gnd", 5: "gnd", 6: "A", 7: "gnd", 8: "B"}
LMP7721_NETS = {1: "gnd", 2: "gnd", 3: "gnd", 4: "A", 5: "nc5", 6: "gnd", 7: "gnd", 8: "B"}


def ada4530_layout(size: str = "1206", half: float = 8.0, title: str = ""):
    """ADA4530-1 in SOIC-8 with the TIA layout of its data sheet (module docstring)."""
    pkg = pk.Soic8()
    res, pads, mount, hp = _resistor(size)
    x8, y8 = pkg.pin_xy(8)                               # (+2.7, +1.905): -IN, B
    x7, y7 = pkg.pin_xy(7)                               # (+2.7, +0.635): GRD, the guard
    x6, y6 = pkg.pin_xy(6)                               # (+2.7, -0.635): OUT, A
    x_r, y_r = _beside_pin8(pkg, pads)
    r_items = pk.resistor_assembly(res, pads, mount, nets=("B", "A"), x0=x_r, y0=y_r, side="top",
                                   board_thickness=H, name="RF", axis="y")
    board = parts.Board(thickness=H, material=mat.custom("FR4", EPS_PCB), planes=[])
    lay = parts.board_layout(board, half, name=title or f"ADA4530-1 SOIC-8 {size}")
    pk.add_soic8(lay, pkg, ADA4530_NETS, floating={3: True}, ground_mesh=GROUND_EDGE)
    pk.add_trace_path(lay, [(x8, y8), (x_r, y8)], TRACE, "B", name="traceB")
    pk.add_trace_path(lay, [(x6, y6), (x_r, y6)], TRACE, "A", name="traceA")
    y_g, x_in, y_top, x_out = _guard_geometry(pkg, pads, x_r, y_r, hp)
    pk.add_trace_path(lay, [(x_in, y_g), (x_in, y_top), (x_out, y_top), (x_out, y_g), (x_in, y_g)], GUARD,
                      "gnd", name="guard-top")
    pk.add_trace_path(lay, [(x7, y_g), (x7, y7)], GUARD, "gnd", name="guard-link")   # driven from pin 7
    for it in r_items:
        lay.add(it)
    return lay


def lmp7721_layout(size: str = "1206", half: float = 8.0, title: str = ""):
    """LMP7721 in SOIC-8 with the guard of its data sheet's layout example (module docstring)."""
    pkg = pk.Soic8()
    res, pads, mount, hp = _resistor(size)
    x8, y8 = pkg.pin_xy(8)                               # (+2.7, +1.905): -IN, B
    x7, y7 = pkg.pin_xy(7)                               # (+2.7, +0.635): N/C, tied to the guard
    x2, y2 = pkg.pin_xy(2)                               # (-2.7, +0.635): N/C, tied to the guard
    x4, y4 = pkg.pin_xy(4)                               # (-2.7, -1.905): OUT, A
    x_r, y_r = _beside_pin8(pkg, pads)
    r_items = pk.resistor_assembly(res, pads, mount, nets=("B", "A"), x0=x_r, y0=y_r, side="top",
                                   board_thickness=H, name="RF", axis="y")
    board = parts.Board(thickness=H, material=mat.custom("FR4", EPS_PCB), planes=[])
    lay = parts.board_layout(board, half, name=title or f"LMP7721 SOIC-8 {size}")
    pk.add_soic8(lay, pkg, LMP7721_NETS, floating={5: True}, ground_mesh=GROUND_EDGE)
    pk.add_trace_path(lay, [(x8, y8), (x_r, y8)], TRACE, "B", name="traceB")
    # Output: from the resistor's lower pad down past the end of the package at pins 4 and 5, along
    # that end and up to pin 4; 0.3 mm beyond the pads of pins 4 and 5.
    y_a = y_r - hp                                       # centre of the resistor's output pad
    y_end = -(1.5 * pkg.pitch + pkg.pad_width / 2) - CLEAR - TRACE / 2
    pk.add_trace_path(lay, [(x_r, y_a), (x_r, y_end), (x4, y_end), (x4, y4)], TRACE, "A", name="traceA")
    # Guard: around both inputs (pins 1 and 8), the input trace and the resistor's input pad, tied to
    # pins 2 and 7 and closed under the body between them; the same loop on the bottom side, joined
    # to the top one by two vias at its upper corners.
    y_g, x_in, y_top, x_out = _guard_geometry(pkg, pads, x_r, y_r, hp)
    x_left = -(pkg.pad_row / 2 + pkg.pad_length / 2) - CLEAR - GUARD / 2
    loop = [(x2, y2), (x_left, y2), (x_left, y_top), (x_out, y_top), (x_out, y_g), (x7, y_g), (x7, y7), (x2, y2)]
    pk.add_trace_path(lay, loop, GUARD, "gnd", side="top", board_thickness=H, name="guard-top")
    pk.add_trace_path(lay, loop, GUARD, "gnd", side="bottom", board_thickness=H, name="guard-bottom")
    for x, y in ((x_left, y_top), (x_out, y_top)):
        pk.add_via(lay, x, y, "gnd", H, name=f"guard-via{'L' if x < 0 else 'R'}")
    for it in r_items:
        lay.add(it)
    return lay


def coarsen(lay, edge: float = GROUND_EDGE, keep: str = "RF", nets=None):
    """Give every conductor without an edge size of its own the edge size ``edge`` (at refine 1),
    except the items whose name starts with ``keep`` (the resistor's pads, solder and terminations);
    with ``nets``, only the conductors on those nets.  Module docstring, "Mesh of the high-gain
    cases"; the high-speed cases use it only for the unconnected pins."""
    for it in lay.items:
        r = it.role
        if not isinstance(r, Conductor) or it.mesh_size is not None or it.name.startswith(keep):
            continue
        if nets is not None and r.net not in nets:
            continue
        it.mesh_size = edge
    return lay


SINGLE_LABELS = NET_LABELS
ADA4530_LABELS = {"A": "net A (output, pin 6)", "B": "net B (inverting input, pin 8)", "nc3": "pin 3 (IC)"}
LMP7721_LABELS = {"A": "net A (output, pin 4)", "B": "net B (inverting input, pin 8)", "nc5": "pin 5"}
HS, HG = "high-speed", "high-gain"     # mesh policies (module docstring)

LAYOUTS = {
    "opa846_so8_double_sided_0402": dict(
        build=lambda: so8_layout("double_sided", "0402"), mesh=HS, labels=SINGLE_LABELS,
        title="OPA846 in SO-8: R_F (0402) under the package on the bottom side"),
    "opa846_so8_vias_under_0402": dict(
        build=lambda: so8_layout("vias_under", "0402"), mesh=HS, labels=SINGLE_LABELS,
        title="OPA846 in SO-8: as before, with the vias under the body beside the pads"),
    "opa846_so8_under_body_0402": dict(
        build=lambda: so8_layout("under_body", "0402"), mesh=HS, labels=SINGLE_LABELS,
        title="OPA846 in SO-8: R_F (0402) beyond pins 4 and 5, traces under the body"),
    "opa637_so8_bottom_0805": dict(
        build=lambda: so8_layout("double_sided", "0805", planes=False), mesh=HG, labels=SINGLE_LABELS,
        title="OPA637 in SOIC-8: R_F (0805) under the package on the bottom side, no planes"),
    "ada4530_so8_1206": dict(
        build=lambda: ada4530_layout("1206"), mesh=HG, labels=ADA4530_LABELS,
        title="ADA4530-1 in SOIC-8: R_F (1206) beside -IN and OUT, guard from pin 7"),
    "lmp7721_so8_1206": dict(
        build=lambda: lmp7721_layout("1206"), mesh=HG, labels=LMP7721_LABELS,
        title="LMP7721 in SOIC-8: R_F (1206) beside -IN, guard on both sides"),
    # The PDIP cases run at refine 16: at 11.3 they meshed to 1.35 and 1.41 million elements, above
    # MAX_ELEMENTS (first run, 5 Nov 2026), and most of their mesh is the 1206's own 15-um edges,
    # which refine does not change.  Case opa637_so8_bottom_0805_refine16 measures what refine 16
    # instead of 11.3 changes in a high-gain case.
    "lmc6001_dip8_bottom_1206": dict(
        build=lambda: dip8_layout("bottom", "1206"), mesh=HG, labels=SINGLE_LABELS, level=16.0,
        title="LMC6001 in PDIP-8: R_F (1206) on the solder side, no planes"),
    "lmc6001_dip8_bottom_guard_1206": dict(
        build=lambda: dip8_layout("bottom_guard", "1206"), mesh=HG, labels=SINGLE_LABELS, level=16.0,
        title="LMC6001 in PDIP-8: as before, with a grounded guard ring"),
}


LEVEL = {HS: 5.66, HG: 11.3}          # refine factor of each kind of case (module docstring, "Mesh")


def build(name: str):
    """The layout ``name`` with the coarser edges of every conductor but the resistor (module
    docstring, "Mesh")."""
    return coarsen(LAYOUTS[name]["build"]())


# ================================================================================================
def estimate() -> None:
    """The a-priori element estimate of meshing.estimate_elements for every layout at its level (no
    mesh is made).  It counts more than gets meshed: for the three OPA846 layouts of g_opa846_3d.py
    it gives 1.95-2.72 million at refine 5.66, against 0.86-1.20 million meshed (records of that
    script), about 0.44 times."""
    for name, d in LAYOUTS.items():
        lvl = LEVEL[d["mesh"]]
        e = build_mesh(build(name), replace(BASE, refine=lvl), estimate_only=True)
        print(f"{name:32s}: estimate at refine {lvl}: {e / 1e3:.0f} thousand; x 0.44 = {0.44 * e / 1e3:.0f} thousand")


CASES: dict[str, tuple[str, object]] = {}
# Largest mesh a case may make (pcbcap.meshing.MeshParams.max_elements; the package's default is
# 1.5 million).  1.25 million is about 5 GB (module docstring, "Mesh").
MAX_ELEMENTS = 1.25e6


def network_case(name: str, level: float | None = None):
    level = level if level is not None else LAYOUTS[name].get("level", LEVEL[LAYOUTS[name]["mesh"]])

    def fn():
        r = study.solve_layout(build(name), replace(BASE, refine=level, max_elements=MAX_ELEMENTS), order=2)
        out = dict(C_F=r.C_F, C_A0=r.C_A0, C_B0=r.C_B0, shares=r.contributions, dofs=r.fem["dofs"],
                   elements=r.mesh["elements"], seconds=r.fem["total_seconds"], level=level)
        line = (f"refine {level}: C_F = {r.C_F:.2f} fF, C_A0 = {r.C_A0:.1f} fF, C_B0 = {r.C_B0:.1f} fF; "
                f"{r.mesh['elements']} elements, {r.fem['dofs']} unknowns, {r.fem['total_seconds']:.0f} s")
        return dict(table=out, lines=[line])
    return fn


for _name, _d in LAYOUTS.items():
    CASES[_name] = (_d["title"] + f", refine {_d.get('level', LEVEL[_d['mesh']])}", network_case(_name))
CASES["opa637_so8_bottom_0805_refine16"] = (
    "OPA637 case at refine 16 instead of 11.3 (check of the level used for the PDIP cases)",
    network_case("opa637_so8_bottom_0805", level=16.0))


def sot23_policy_case():
    """The published SOT-23-5 layout double_sided with the 0402 (g_opa846_3d.py) solved with this
    script's mesh policy (every conductor but the resistor coarse, refine 5.66).  g_opa846_3d.py kept
    the signal pins, traces and vias at the network's edge size; the difference between the two
    results is what the policy changes, so that the SO-8 results can be set against the SOT-23 ones."""
    def fn():
        import g_opa846_3d as g846                       # same folder
        lay = coarsen(g846.opa846_layout("double_sided", "0402"))
        r = study.solve_layout(lay, replace(BASE, refine=5.66, max_elements=MAX_ELEMENTS), order=2)
        out = dict(C_F=r.C_F, C_A0=r.C_A0, C_B0=r.C_B0, shares=r.contributions, dofs=r.fem["dofs"],
                   elements=r.mesh["elements"], seconds=r.fem["total_seconds"], level=5.66)
        line = (f"refine 5.66: C_F = {r.C_F:.2f} fF, C_A0 = {r.C_A0:.1f} fF, C_B0 = {r.C_B0:.1f} fF; "
                f"{r.mesh['elements']} elements, {r.fem['dofs']} unknowns, {r.fem['total_seconds']:.0f} s")
        return dict(table=out, lines=[line])
    return fn


CASES["opa846_sot23_double_sided_0402_policy"] = (
    "Published SOT-23-5 layout double_sided (0402) with this script's mesh policy (check)", sot23_policy_case())


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
            print(f"{k:32s} {t}")
    elif a.cmd == "estimate":
        estimate()
    else:
        run(a.name, a.record)
    return 0


if __name__ == "__main__":
    sys.exit(main())
