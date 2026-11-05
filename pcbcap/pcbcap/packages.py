"""Leaded packages, vias, traces and parts on the bottom side of the board.

Why this module exists
----------------------
``parts.py`` builds a chip resistor on its pads and a leadless (WSON) package.  A layout around an
amplifier in a leaded package, such as the OPA846 in SOT-23-5, also needs
  * the gull-wing leads, which stand above their pads and face each other across the package,
  * vias, which carry a net through the board,
  * traces with corners, and
  * parts mounted on the bottom side, as TI recommends for the feedback resistor of the OPA846.
This module adds those, with the same conventions as parts.py (mm; z up; board top at z = 0).

Modelling choices, and why
--------------------------
* A gull-wing lead is up to three boxes of the lead's width and thickness: the foot, which lies on
  the pad; the riser, which climbs from the foot towards the body; and a shoulder, the horizontal
  stretch between the body's side and the riser.  At the nominal SOT-23 dimensions the shoulder has
  no length outside the body: the lead reaches (lead span - body width)/2 = (2.8 - 1.6)/2 = 0.6 mm
  beyond the body, which the foot (0.45 mm) and the riser (one lead thickness, 0.15 mm) use up
  exactly, so the shoulder box coincides with the riser and the riser stands against the body's
  side.  The box is kept for packages with a longer lead.  A real lead is bent with rounded corners
  and a drafted riser (4-15 degrees on the DBV0005A drawing); the boxes keep its position, width,
  thickness and height, which are what set its capacitance to its neighbours.
* The lead frame inside the body (the fingers, the die pad, the bond wires) is not modelled: no
  datasheet gives its geometry (as approximation 12 of the companion note says for the WSON).
* A via is a square barrel through the board, with square pads on the layers it joins.  The square
  is not as wide as the round drill: its side is 0.8472 times the drill diameter, so that it has the
  same far field.  Derivation.  Seen from a distance much larger than its width, a long conductor of
  any cross-section has the field of a round wire of a certain radius, the conformal radius of the
  cross-section: the map f from the outside of the unit circle onto the outside of the cross-section,
  normalised so that f(w) ~ c w at infinity, scales by c at large distances, so the field far away is
  that of a circle of radius c.  For a square, the Schwarz-Christoffel formula for the outside of a
  polygon with four right-angled corners gives f'(w) = c (1 + w^-4)^(1/2).  The side s is the image of
  a quarter of the unit circle between two of the points that map to corners, w = e^(i pi/4) and
  e^(i 3 pi/4): with |f'(e^(i theta))| = c |1 + e^(-4 i theta)|^(1/2) = c (2 |cos 2 theta|)^(1/2),
      s = c sqrt(2) int_{pi/4}^{3 pi/4} |cos 2 theta|^(1/2) d theta = c sqrt(2) int_0^(pi/2) cos(u)^(1/2) du
        = c sqrt(2) (sqrt(pi)/2) Gamma(3/4) / Gamma(5/4) = c 4 pi^(3/2) / Gamma(1/4)^2,
  using int_0^(pi/2) cos^p = (sqrt(pi)/2) Gamma((p+1)/2)/Gamma(p/2 + 1), Gamma(1/4) Gamma(3/4) =
  pi sqrt(2) and Gamma(5/4) = Gamma(1/4)/4.  So c = Gamma(1/4)^2 s / (4 pi^(3/2)) = 0.5902 s.  A round
  barrel of diameter d has c = d/2, and the square with the same c has s = (d/2)/0.5902 = 0.8472 d.
  (A square of side d would have the far field of a 1.18 times wider barrel.)  Near the barrel the
  two shapes differ, but the nearest other conductor in these layouts is at least 0.5 mm, almost
  twice the drill diameter, away.  The pads are kept square, of side ``pad``.
* A trace is a chain of axis-aligned boxes through given corner points; each box is extended by
  half the width at its ends, so that consecutive boxes overlap at the corners.
* A part on the bottom side is built as on the top side and then reflected through the board's
  mid-plane: z -> -H - z.  A reflection keeps every distance, so the part is the same part, now
  hanging below the board with its film facing away from it.
"""
from __future__ import annotations

import math

from dataclasses import dataclass, field, replace

from . import materials as mat
from . import parts
from .geometry import GROUND, Box, Interval, Layout, Sheet


# ================================================================================================
@dataclass
class Sot23:
    """SOT-23-5 (TI DBV0005A), nominal values of the OPA846 datasheet (SBOS250E), pp. 26-27.

    Package outline (p. 26): body 2.75-3.05 mm long (along the pin rows) and 1.45-1.75 mm wide,
    lead span tip to tip 2.6-3.0 mm, pitch 0.95 mm, lead width 0.3-0.5 mm, lead thickness
    0.08-0.22 mm, foot length 0.3-0.6 mm, overall height 0.90-1.45 mm, stand-off 0.00-0.15 mm, and a
    body thickness given as the reference dimension (1.1).  Each default below is the midpoint of its
    range (2.9, 1.6, 2.8, 0.4, 0.15, 0.45, 0.075), except the body height, which is the reference
    value 1.1.  Example board layout (p. 27): pads 1.1 mm x 0.6 mm, rows 2.6 mm apart between pad
    centres.  Pins (p. 2, top view): 1, 2, 3 down the left side, 5 and 4 down the right side, pin 1
    at the top left.  The drawing's optional support pin (its note 5) is not modelled.

    shoulder_height : height of the lead's exit from the body above the body's lower face.  The
        drawing does not dimension it; 0.45 mm (about the middle of a 1.1-mm body) is assumed.
    """

    body_length: float = 2.9
    body_width: float = 1.6
    body_height: float = 1.1
    standoff: float = 0.075
    lead_span: float = 2.8
    lead_width: float = 0.4
    lead_thickness: float = 0.15
    foot_length: float = 0.45
    shoulder_height: float = 0.45
    pitch: float = 0.95
    pad_length: float = 1.1          # across the package (x)
    pad_width: float = 0.6           # along the pin row (y)
    pad_row: float = 2.6             # distance between the two rows' pad centres
    mould: str | mat.Material = "mould"

    def pin_xy(self, pin: int, x0: float = 0.0, y0: float = 0.0) -> tuple[float, float]:
        """Centre of pin ``pin``'s land pad.  Left column (x < 0): pins 1, 2, 3 from +y to -y; right
        column: pin 5 at +y, pin 4 at -y (the top view of the datasheet's p. 2)."""
        xs = -self.pad_row / 2 if pin in (1, 2, 3) else self.pad_row / 2
        ys = {1: self.pitch, 2: 0.0, 3: -self.pitch, 5: self.pitch, 4: -self.pitch}[pin]
        return x0 + xs, y0 + ys


def add_sot23(lay: Layout, pkg: Sot23, nets: dict[int, str], x0: float = 0.0, y0: float = 0.0,
              floating: dict[int, bool] | None = None, t_cu: float = 0.035, lead_mesh: float | None = None,
              ground_mesh: float | None = None) -> None:
    """Land pads, gull-wing leads and moulded body of a SOT-23-5 centred at (x0, y0).

    ``lead_mesh`` sets the edge element size (meshing.py, ``mesh_size``) of the signal pins' pads and
    leads, ``ground_mesh`` that of the grounded pins.  A grounded pin next to the network only shields
    it, so a coarser size there saves elements where they are expected to matter least.  That
    expectation has not been checked by a calculation with equal sizes; the coarser size adds a
    mesh error that a convergence study at fixed ratio between the two sizes still extrapolates."""
    floating = floating or {}
    hw = pkg.lead_width / 2
    z_pad = t_cu                                     # the foot rests on the pad (solder joint = conductor)
    z_body = z_pad + pkg.standoff                    # lower face of the body
    z_sh = z_body + pkg.shoulder_height              # centre of the shoulder
    lt = pkg.lead_thickness
    # mould body first, so that the leads painted afterwards replace it where they enter
    lay.add_box((x0 - pkg.body_width / 2, x0 + pkg.body_width / 2),
                (y0 - pkg.body_length / 2, y0 + pkg.body_length / 2),
                (z_body, z_body + pkg.body_height), material=pkg.mould, label="mould", name="sot23-body")
    for pin in (1, 2, 3, 4, 5):
        net = nets[pin]
        fl = floating.get(pin, False)
        px, py = pkg.pin_xy(pin, x0, y0)
        side = -1.0 if px < x0 else 1.0
        ms = ground_mesh if (net == GROUND and ground_mesh is not None) else lead_mesh
        # land pad (a copper box of thickness t_cu, as parts.add_pad makes it, with this pin's edge size)
        lay.add_box((px - pkg.pad_length / 2, px + pkg.pad_length / 2),
                    (py - pkg.pad_width / 2, py + pkg.pad_width / 2), (0.0, t_cu), net=net, floating=fl,
                    name=f"pin{pin}-pad", mesh_size=ms)
        # lead: x measured outward from the body's side (x_b) to the tip (x_t)
        x_b = x0 + side * pkg.body_width / 2
        x_t = x0 + side * pkg.lead_span / 2
        x_f = x_t - side * pkg.foot_length          # inner end of the foot
        x_r = x_f                                    # the riser sits at the inner end of the foot

        def span(a, b):
            return (min(a, b), max(a, b))

        y = (py - hw, py + hw)
        lay.add_box(span(x_f, x_t), y, (z_pad, z_pad + lt), net=net, floating=fl, name=f"pin{pin}-foot",
                    mesh_size=ms)
        lay.add_box(span(x_r, x_r - side * lt), y, (z_pad, z_sh + lt / 2), net=net, floating=fl,
                    name=f"pin{pin}-riser", mesh_size=ms)
        lay.add_box(span(x_b, x_r), y, (z_sh - lt / 2, z_sh + lt / 2), net=net, floating=fl,
                    name=f"pin{pin}-shoulder", mesh_size=ms)


# ================================================================================================
# Side of the square with the same conformal radius as a circle of unit diameter (module docstring):
# 0.5 / (Gamma(1/4)^2 / (4 pi^(3/2))) = 2 pi^(3/2) / Gamma(1/4)^2 = 0.84721.
SQUARE_FOR_ROUND = 2.0 * math.pi ** 1.5 / math.gamma(0.25) ** 2


def add_via(lay: Layout, x: float, y: float, net: str, board_thickness: float, drill: float = 0.3,
            pad: float = 0.55, t_cu: float = 0.035, name: str = "via") -> None:
    """A plated through-hole: a square barrel from the bottom copper to the top copper, of side
    SQUARE_FOR_ROUND times the drill diameter (the square with the far field of the round barrel;
    module docstring), with square pads of side ``pad`` on both outer layers."""
    H = board_thickness
    d, p = SQUARE_FOR_ROUND * drill / 2, pad / 2
    lay.add_box((x - d, x + d), (y - d, y + d), (-H, 0.0), net=net, name=f"{name}-barrel")
    lay.add_box((x - p, x + p), (y - p, y + p), (0.0, t_cu), net=net, name=f"{name}-top")
    lay.add_box((x - p, x + p), (y - p, y + p), (-H - t_cu, -H), net=net, name=f"{name}-bottom")


def add_trace_path(lay: Layout, points: list[tuple[float, float]], width: float, net: str,
                   t_cu: float = 0.035, side: str = "top", board_thickness: float = 1.6,
                   name: str = "trace") -> None:
    """A trace through the corner points [(x, y), ...], each leg parallel to x or to y.

    Each leg is a box of the trace's width, extended by half the width beyond both of its corner
    points, so that consecutive legs overlap in a square at the corner (a mitre-free 90-degree turn).
    ``side`` 'top' puts the copper on z = [0, t_cu]; 'bottom' on z = [-H - t_cu, -H]."""
    hw = width / 2
    z = (0.0, t_cu) if side == "top" else (-board_thickness - t_cu, -board_thickness)
    for k, ((xa, ya), (xb, yb)) in enumerate(zip(points, points[1:])):
        if ya == yb:
            xr, yr = (min(xa, xb) - hw, max(xa, xb) + hw), (ya - hw, ya + hw)
        elif xa == xb:
            xr, yr = (xa - hw, xa + hw), (min(ya, yb) - hw, max(ya, yb) + hw)
        else:
            raise ValueError("each leg of a trace must run along x or along y")
        lay.add_box(xr, yr, z, net=net, name=f"{name}{k}")


# ================================================================================================
def resistor_assembly(res: parts.ChipResistor, pads: parts.LandPattern, mount: parts.Mount, nets=("A", "B"),
                      x0: float = 0.0, y0: float = 0.0, side: str = "top", board_thickness: float = 1.6,
                      name: str = "R") -> list:
    """The items of a chip resistor on its pads (pads, solder, body, terminations, film), centred at
    (x0, y0) with its axis along x (nets[0] at +x), on the top or the bottom side of the board.

    The top-side assembly is built exactly as parts.resistor_on_pads builds it; for the bottom side
    it is then reflected through the board's mid-plane, z -> -H - z (see the module docstring)."""
    tmp = Layout(3, "assembly")
    w, l, s, tc = pads.w, pads.l, pads.s, pads.t_cu
    pad_x = {nets[0]: (x0 + s / 2, x0 + s / 2 + w), nets[1]: (x0 - s / 2 - w, x0 - s / 2)}
    pad_y = (y0 - l / 2, y0 + l / 2)
    for net in nets:
        parts.add_pad(tmp, pad_x[net], pad_y, tc, net, name=f"{name}-pad{net}")
    z_bottom = tc + mount.standoff
    if mount.standoff > 0:
        L, W, a = res.L, res.W, res.a
        for sgn, net in ((+1, nets[0]), (-1, nets[1])):
            wrap_x = (x0 + L / 2 - a, x0 + L / 2) if sgn > 0 else (x0 - L / 2, x0 - L / 2 + a)
            sx = (max(wrap_x[0], pad_x[net][0]), min(wrap_x[1], pad_x[net][1]))
            sy = (max(y0 - W / 2, pad_y[0]), min(y0 + W / 2, pad_y[1]))
            if sx[1] > sx[0] and sy[1] > sy[0]:
                tmp.add_box(sx, sy, (tc, z_bottom), net=net, name=f"{name}-solder{net}")
    parts.add_resistor(tmp, res, z_bottom, x0=x0, y0=y0, nets=nets, name=name)
    if side == "top":
        return tmp.items
    if side != "bottom":
        raise ValueError("side must be 'top' or 'bottom'")
    return [_mirror_z(it, -board_thickness / 2) for it in tmp.items]


def _mirror_z(it, zm: float):
    """Reflection of an item through the plane z = zm (z -> 2 zm - z)."""
    if isinstance(it, Box):
        return replace(it, z=(2 * zm - it.z[1], 2 * zm - it.z[0]))
    if isinstance(it, Sheet):
        if it.normal == "z":
            return Sheet("z", 2 * zm - it.at, dict(it.spans), it.role, it.name, list(it.holes), it.mesh_size)
        spans = dict(it.spans)
        spans["z"] = (2 * zm - it.spans["z"][1], 2 * zm - it.spans["z"][0])
        return Sheet(it.normal, it.at, spans, it.role, it.name, list(it.holes), it.mesh_size)
    raise TypeError(type(it))
