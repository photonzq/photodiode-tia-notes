"""Leaded packages, vias, traces and parts on the bottom side of the board.

Why this module exists
----------------------
``parts.py`` builds a chip resistor on its pads and a leadless (WSON) package.  A layout around an
amplifier in a leaded package, such as the OPA846 in SOT-23-5, also needs
  * the gull-wing leads, which stand above their pads and face each other across the package,
  * vias, which carry a net through the board,
  * traces with corners, and
  * parts mounted on the bottom side, as TI recommends for the feedback resistor of the OPA846.
It also builds the two common eight-lead packages, the SOIC-8 (gull-wing leads, like the SOT-23) and
the PDIP-8 (leads through plated holes), in which the precision and electrometer amplifiers of the
high-gain note come.  This module adds those, with the same conventions as parts.py (mm; z up;
board top at z = 0).

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
from .geometry import GROUND, Box, Film, Interval, Layout, LinearProfile, Sheet


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
                      name: str = "R", axis: str = "x") -> list:
    """The items of a chip resistor on its pads (pads, solder, body, terminations, film), centred at
    (x0, y0) with its axis along ``axis`` (nets[0] at +x, or at +y), on the top or the bottom side.

    The top-side assembly is built exactly as parts.resistor_on_pads builds it.  For axis "y" it is
    then turned by +90 degrees about the vertical line through (x0, y0) (_rotate_z90), and for the
    bottom side reflected through the board's mid-plane, z -> -H - z (see the module docstring); the
    two operations commute, since one acts on x and y and the other on z."""
    if axis not in ("x", "y"):
        raise ValueError("axis must be 'x' or 'y'")
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
    items = tmp.items if axis == "x" else [_rotate_z90(it, x0, y0) for it in tmp.items]
    if side == "top":
        return items
    if side != "bottom":
        raise ValueError("side must be 'top' or 'bottom'")
    return [_mirror_z(it, -board_thickness / 2) for it in items]


def _rotate_z90(it, x0: float, y0: float):
    """Turn an item by +90 degrees about the vertical line through (x0, y0):
        (x, y) -> (x0 - (y - y0), y0 + (x - x0)),
    which takes the +x direction into +y.  A box's y-interval [c, d] becomes the x-interval
    [x0 - (d - y0), x0 - (c - y0)] and its x-interval [a, b] the y-interval [y0 + (a - x0), y0 + (b - x0)].
    A rotation keeps every distance, so the part is the same part, standing along y.  The film's
    linear profile along x, u = (x - start)/(end - start), becomes the same function of y with
    start and end moved by the same map, y0 + (start - x0) and y0 + (end - x0): the end at +x, where
    u = 1 (the hi net), is now at +y."""
    def new_x(iv_y):
        return (x0 - (iv_y[1] - y0), x0 - (iv_y[0] - y0))

    def new_y(iv_x):
        return (y0 + (iv_x[0] - x0), y0 + (iv_x[1] - x0))

    if isinstance(it, Box):
        return replace(it, x=new_x(it.y), y=new_y(it.x))
    if isinstance(it, Sheet) and it.normal == "z":
        role = it.role
        if isinstance(role, Film):
            p = role.profile
            if not (isinstance(p, LinearProfile) and p.axis == "x"):
                raise TypeError("only a linear film profile along x can be turned")
            role = Film(role.hi, role.lo, LinearProfile("y", y0 + (p.start - x0), y0 + (p.end - x0)))
        spans = {"x": new_x(it.spans["y"]), "y": new_y(it.spans["x"])}
        holes = [{"x": new_x(h["y"]), "y": new_y(h["x"])} for h in it.holes]
        return Sheet("z", it.at, spans, role, it.name, holes, it.mesh_size)
    raise TypeError(f"cannot turn {type(it).__name__} {it.name}")


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


# ================================================================================================
# Eight-lead packages: SOIC-8 (gull-wing leads) and PDIP-8 (leads through plated holes)
# ================================================================================================
def _span(a: float, b: float) -> Interval:
    return (min(a, b), max(a, b))


def eight_pin_xy(pin: int, row: float, pitch: float, x0: float = 0.0, y0: float = 0.0) -> tuple[float, float]:
    """Centre of pin ``pin`` of an eight-lead dual-row package seen from above.

    Pins 1-4 run down the left side (x < 0) from +y to -y and pins 5-8 up the right side, so pin 1
    is at the top left and pin 8 opposite it, as in the top views of every data sheet used here.
    ``row`` is the distance between the two rows' centre lines and ``pitch`` the distance between
    neighbours in a row.  Pin k of the left row (k = 1..4) and pin 9 - k of the right row sit at the
    same height, y = (5/2 - k) pitch: +1.5, +0.5, -0.5 and -1.5 pitches for k = 1, 2, 3, 4."""
    if not 1 <= pin <= 8:
        raise ValueError("an eight-lead package has pins 1-8")
    k = pin if pin <= 4 else 9 - pin
    x = -row / 2 if pin <= 4 else row / 2
    return x0 + x, y0 + (2.5 - k) * pitch


@dataclass
class Soic8:
    """SOIC-8 with the narrow body (TI D0008A; JEDEC MS-012, variation AA).

    Package outline: TI drawing 4214825/C on p. 29 of the OPA846 data sheet (SBOS250E).  The same
    drawing is in the data sheets of the LMC662 (SNOSC51D, p. 30), the LMP7721 (SNOSAW6E, p. 32) and
    the OPA627/OPA637 (SBOS165C, p. 43).  It gives the body 4.81-5.00 mm long (along the pin rows, y
    here) and 3.81-3.98 mm wide, the lead span from tip to tip 5.80-6.19 mm, the pitch 1.27 mm, the
    lead width 0.31-0.51 mm and thickness 0.13-0.25 mm, the foot length 0.41-1.27 mm, the stand-off
    0.11-0.25 mm and a height of 1.75 mm at most.  It gives no lower limit of the height; Analog
    Devices' drawing of the same JEDEC outline (R-8, ADA4530-1 data sheet Rev. C, p. 52, Figure 139)
    gives 1.35-1.75 mm.

    Defaults: the midpoint of each range (body 4.905 x 3.895 mm, span 5.995 mm, lead 0.41 x 0.19 mm,
    foot 0.84 mm, stand-off 0.18 mm).  The body's thickness is the height less the stand-off,
    1.55 - 0.18 = 1.37 mm, with 1.55 mm the midpoint of ADI's 1.35-1.75 mm.  Example board layout
    (TI, p. 30 of the OPA846 data sheet): pads 1.55 mm across the package by 0.6 mm along it, with the
    two rows' pad centres 5.4 mm apart.

    shoulder_height : height of the lead's exit above the body's lower face.  No drawing dimensions
        it.  Detail A of TI's drawing shows the lead leaving the body near half its height, so the
        default (None) takes half the body's thickness.
    """

    body_length: float = 4.905
    body_width: float = 3.895
    body_height: float = 1.37
    standoff: float = 0.18
    lead_span: float = 5.995
    lead_width: float = 0.41
    lead_thickness: float = 0.19
    foot_length: float = 0.84
    shoulder_height: float | None = None
    pitch: float = 1.27
    pad_length: float = 1.55         # across the package (x)
    pad_width: float = 0.6           # along the pin row (y)
    pad_row: float = 5.4             # distance between the two rows' pad centres
    mould: str | mat.Material = "mould"

    def __post_init__(self):
        if self.shoulder_height is None:
            self.shoulder_height = self.body_height / 2
        reach = (self.lead_span - self.body_width) / 2      # how far the lead reaches beyond the body
        if self.foot_length + self.lead_thickness > reach + 1e-12:
            raise ValueError("the foot and the riser do not fit within the lead's reach beyond the body")

    def pin_xy(self, pin: int, x0: float = 0.0, y0: float = 0.0) -> tuple[float, float]:
        """Centre of pin ``pin``'s land pad (eight_pin_xy with the pad rows)."""
        return eight_pin_xy(pin, self.pad_row, self.pitch, x0, y0)


def add_soic8(lay: Layout, pkg: Soic8, nets: dict[int, str], x0: float = 0.0, y0: float = 0.0,
              floating: dict[int, bool] | None = None, t_cu: float = 0.035, lead_mesh: float | None = None,
              ground_mesh: float | None = None, name: str = "soic8") -> None:
    """Land pads, gull-wing leads and moulded body of an SOIC-8 centred at (x0, y0).

    Built as add_sot23 builds the SOT-23-5 (module docstring): each lead is a foot lying on its pad,
    a riser one lead thickness wide at the inner end of the foot, and a shoulder from the body's side
    to the riser at ``shoulder_height`` above the body's lower face.  At the default dimensions the
    lead reaches (5.995 - 3.895)/2 = 1.05 mm beyond the body; the foot takes 0.84 mm of it and the
    riser 0.19 mm, so 0.02 mm of shoulder shows outside the body.  The lead frame inside the body is
    not modelled (module docstring).

    ``nets`` gives every pin 1-8 a net.  A pin with no internal connection is marked in ``floating``
    and needs a net of its own: all conductors of one floating net share one unknown potential, so
    two unconnected pins given the same floating net would be joined.  ``lead_mesh`` and
    ``ground_mesh`` work as in add_sot23."""
    floating = floating or {}
    hw = pkg.lead_width / 2
    lt = pkg.lead_thickness
    z_pad = t_cu                                     # the foot rests on the pad (solder joint = conductor)
    z_body = z_pad + pkg.standoff                    # lower face of the body
    z_sh = z_body + pkg.shoulder_height              # centre of the shoulder
    # mould body first, so that the leads painted afterwards replace it where they touch
    lay.add_box((x0 - pkg.body_width / 2, x0 + pkg.body_width / 2),
                (y0 - pkg.body_length / 2, y0 + pkg.body_length / 2),
                (z_body, z_body + pkg.body_height), material=pkg.mould, label="mould", name=f"{name}-body")
    for pin in range(1, 9):
        net = nets[pin]
        fl = floating.get(pin, False)
        px, py = pkg.pin_xy(pin, x0, y0)
        side = -1.0 if px < x0 else 1.0
        ms = ground_mesh if (net == GROUND and ground_mesh is not None) else lead_mesh
        lay.add_box((px - pkg.pad_length / 2, px + pkg.pad_length / 2),
                    (py - pkg.pad_width / 2, py + pkg.pad_width / 2), (0.0, t_cu), net=net, floating=fl,
                    name=f"{name}-pin{pin}-pad", mesh_size=ms)
        x_b = x0 + side * pkg.body_width / 2         # the body's side
        x_t = x0 + side * pkg.lead_span / 2          # the lead's tip
        x_f = x_t - side * pkg.foot_length           # inner end of the foot, where the riser stands
        y = (py - hw, py + hw)
        lay.add_box(_span(x_f, x_t), y, (z_pad, z_pad + lt), net=net, floating=fl,
                    name=f"{name}-pin{pin}-foot", mesh_size=ms)
        lay.add_box(_span(x_f, x_f - side * lt), y, (z_pad, z_sh + lt / 2), net=net, floating=fl,
                    name=f"{name}-pin{pin}-riser", mesh_size=ms)
        lay.add_box(_span(x_b, x_f), y, (z_sh - lt / 2, z_sh + lt / 2), net=net, floating=fl,
                    name=f"{name}-pin{pin}-shoulder", mesh_size=ms)


@dataclass
class Dip8:
    """PDIP-8 (TI P (R-PDIP-T8), drawing 4040082/E; within JEDEC MS-001, variation BA).

    Package outline: p. 33 of the LMC662 data sheet (SNOSC51D); the same drawing is p. 25 of the
    LMC6001 data sheet (SNOS694I).  It gives the body 9.02-10.16 mm long and 6.10-6.60 mm wide; the
    leads 1.14-1.78 mm wide above the seating plane (the shoulders on which the package stands) and
    0.38-0.53 mm wide below it, 0.25 mm thick (nominal), at a pitch of 2.54 mm; 7.62-8.26 mm across the
    two rows of leads at the gauge plane, 0.38 mm above the seating plane; at least 3.18 mm of lead
    below the seating plane; the body at least 0.51 mm above the seating plane; and a seated height
    of 5.08 mm at most.

    Defaults:
      * body 9.59 x 6.35 mm, shoulders 1.46 mm and leads 0.455 mm wide: the midpoints of the ranges;
      * lead thickness 0.25 mm: the nominal value;
      * the two rows 7.62 mm apart between the leads' centre lines, the 0.300-inch spacing of the
        board's holes.  The leads are taken as straight down into their holes, so the width across
        them is 7.62 + 0.25 = 7.87 mm, inside the drawing's 7.62-8.26 mm (the drawing lets the leads
        splay out to 10.92 mm at their tips before they are inserted);
      * stand-off 0.51 mm and lead length below the seating plane 3.18 mm: the drawing's minima.  The
        package stands on its top pads, 35 um above the board, so an uncut lead of that length ends
        3.18 - 0.035 = 3.145 mm below the board's top surface: 1.545 mm below the lower surface of a
        1.6-mm board and 1.51 mm below the bottom pad.  A lead cut after soldering protrudes less;
      * body_height 3.30 mm: TI's drawing does not dimension the body's thickness (it only bounds it
        by the seated height less the stand-off, 5.08 - 0.51 = 4.57 mm).  Analog Devices' drawing of
        the same JEDEC outline (N-8, AD620 data sheet Rev. H, p. 19, Figure 50, "compliant to JEDEC
        standards MS-001") gives it as 2.92-4.95 mm with 3.30 mm nominal, and the nominal is taken;
      * exit_height: the height of the leads' exit above the body's lower face, not dimensioned
        either; the default (None) takes half the body's thickness, as for the SOIC.

    The board's side, which the package drawing does not give: plated holes of ``drill`` 0.8 mm with
    round pads of diameter ``pad`` 1.6 mm on both outer layers, a common choice for this lead.  The
    lead's diagonal is at most sqrt(0.53^2 + 0.25^2) = 0.586 mm, which leaves 0.8 - 0.586 = 0.21 mm
    for the solder.  The hole, filled with solder around the lead, is one conductor: a square of side
    SQUARE_FOR_ROUND x drill = 0.678 mm, the square with the round hole's far field (module
    docstring).  Each round pad becomes the square of the same area, of side pad x sqrt(pi)/2 =
    1.418 mm, which keeps the pad's capacitance to a plane close beneath it (proportional to its
    area)."""

    body_length: float = 9.59
    body_width: float = 6.35
    body_height: float = 3.30
    standoff: float = 0.51
    row: float = 7.62
    pitch: float = 2.54
    shoulder_width: float = 1.46
    lead_width: float = 0.455
    lead_thickness: float = 0.25
    lead_below: float = 3.18
    exit_height: float | None = None
    drill: float = 0.8
    pad: float = 1.6
    mould: str | mat.Material = "mould"

    def __post_init__(self):
        if self.exit_height is None:
            self.exit_height = self.body_height / 2
        if self.row / 2 - self.lead_thickness / 2 <= self.body_width / 2:
            raise ValueError("the leads' vertical parts must lie outside the body")

    def pin_xy(self, pin: int, x0: float = 0.0, y0: float = 0.0) -> tuple[float, float]:
        """Centre of pin ``pin``'s hole (eight_pin_xy with the rows of holes)."""
        return eight_pin_xy(pin, self.row, self.pitch, x0, y0)

    @property
    def pad_side(self) -> float:
        """Side of the square pad with the round pad's area: pad x sqrt(pi)/2."""
        return self.pad * math.sqrt(math.pi) / 2


def add_dip8(lay: Layout, pkg: Dip8, nets: dict[int, str], board_thickness: float, x0: float = 0.0,
             y0: float = 0.0, floating: dict[int, bool] | None = None, t_cu: float = 0.035,
             lead_mesh: float | None = None, ground_mesh: float | None = None, name: str = "dip8") -> None:
    """Plated holes with their pads, leads and moulded body of a PDIP-8 centred at (x0, y0).

    Each lead is three boxes, all one lead thickness wide in x:
      * the exit: a horizontal stretch, as wide as the shoulder, from the body's side to the vertical
        part of the lead, at ``exit_height`` above the body's lower face;
      * the shoulder: vertical, from the exit down to the seating plane, which is the top of the pads
        (the package stands on its shoulders);
      * the pin: the narrow part, from the seating plane down ``lead_below``, through the top pad,
        the hole and the bottom pad and out below the board.
    The board adds, per pin, the top and bottom pads and the filled hole (Dip8 docstring).  The lead
    frame inside the body is not modelled, as for the SOT-23 (module docstring).  A ground plane must
    not cross a hole of another net: leave the package out of the plane (a cut-out around it, as in
    the study scripts) or give the plane a hole there.  ``nets``, ``floating``, ``lead_mesh`` and
    ``ground_mesh`` work as in add_soic8."""
    floating = floating or {}
    H, c = board_thickness, pkg.lead_thickness
    z_seat = t_cu                                    # the shoulders stand on the top pads
    z_body = z_seat + pkg.standoff                   # lower face of the body
    z_exit = z_body + pkg.exit_height                # centre of the exit stretch
    hb = SQUARE_FOR_ROUND * pkg.drill / 2            # half side of the filled hole
    hp = pkg.pad_side / 2                            # half side of a pad
    if z_seat - pkg.lead_below > -board_thickness - t_cu:
        raise ValueError("the lead is too short to pass through the board")
    lay.add_box((x0 - pkg.body_width / 2, x0 + pkg.body_width / 2),
                (y0 - pkg.body_length / 2, y0 + pkg.body_length / 2),
                (z_body, z_body + pkg.body_height), material=pkg.mould, label="mould", name=f"{name}-body")
    for pin in range(1, 9):
        net = nets[pin]
        px, py = pkg.pin_xy(pin, x0, y0)
        side = -1.0 if px < x0 else 1.0
        ms = ground_mesh if (net == GROUND and ground_mesh is not None) else lead_mesh
        kw = dict(net=net, floating=floating.get(pin, False), mesh_size=ms)
        xs, ys = (px - hp, px + hp), (py - hp, py + hp)
        lay.add_box(xs, ys, (0.0, t_cu), name=f"{name}-pin{pin}-padtop", **kw)
        lay.add_box(xs, ys, (-H - t_cu, -H), name=f"{name}-pin{pin}-padbottom", **kw)
        lay.add_box((px - hb, px + hb), (py - hb, py + hb), (-H, 0.0), name=f"{name}-pin{pin}-hole", **kw)
        xl = (px - c / 2, px + c / 2)
        lay.add_box(xl, (py - pkg.lead_width / 2, py + pkg.lead_width / 2), (z_seat - pkg.lead_below, z_seat),
                    name=f"{name}-pin{pin}-pin", **kw)
        yw = (py - pkg.shoulder_width / 2, py + pkg.shoulder_width / 2)
        lay.add_box(xl, yw, (z_seat, z_exit + c / 2), name=f"{name}-pin{pin}-shoulder", **kw)
        lay.add_box(_span(x0 + side * pkg.body_width / 2, px - side * c / 2), yw, (z_exit - c / 2, z_exit + c / 2),
                    name=f"{name}-pin{pin}-exit", **kw)
