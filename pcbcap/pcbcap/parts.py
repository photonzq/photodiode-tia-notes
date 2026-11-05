"""Builders for common parts: chip resistors, land patterns, boards, planes, solder mask, packages.

Why this module exists
----------------------
``geometry.Layout`` accepts any boxes and sheets.  Building a resistor on a board from them by hand
is error-prone (a pad in the wrong place, a termination on the wrong face), and every study would
repeat the same lines.  The builders here encode the construction once, with every modelling choice
written next to the code that makes it, and with dimensions taken from manufacturers' documents.

Conventions (as in geometry.py): x along the resistor, net A at +x and net B at -x, y across, z up,
board top surface at z = 0, lengths in mm.

Modelling choices, and why
--------------------------
* The resistor body is an alumina box of the overall length L, width W and height T.  Datasheets give
  T as the overall height including terminations and coatings, so using it for the alumina slightly
  raises the capacitance (approximation 15 of the companion note's Table G.6); the termination
  boxes below then replace the alumina where the metal is.
* Each termination is a conductor made of boxes of thickness ``t_term``: an end cap over the whole end
  face, a top wrap and a bottom wrap of length ``a`` (and optionally side wraps).  They are painted
  over the alumina, so the alumina under a wrap is thinner by t_term, as on a real part.  Their
  thickness changes C_F little: doubling it from 15 to 30 um adds 0.63 fF (1.6 %) to an 0402 (case
  details_0402 of the study scripts).  Making them boxes rather than zero-thickness sheets gives
  their edges the singularity of a right-angled metal edge, where the potential varies as r^(2/3),
  instead of the r^(1/2) of a sheet edge (fem.py, Step 2), as on the real part.
* The film is a zero-thickness sheet on the top face between the wraps (on the bottom face if the
  part is mounted upside down), with the linear DC potential of a plain film
  (geometry.LinearProfile).  It covers the full width W unless ``film_width`` says otherwise.
* The pads are copper boxes of thickness ``t_cu``, 35 um by default, the nominal thickness of 1-oz
  copper (1 oz, 28.35 g, spread over 1 square foot, 929.0 cm^2, at the density of copper,
  8.96 g/cm^3, is 34.1 um thick); the copper weight of a real board is a choice of its maker.  With
  t_cu = 0 the pads become sheets.  The body rests a stand-off ``standoff`` above the pads; under each
  bottom wrap the gap is filled with solder (conductor), elsewhere with air.  An optional solder
  fillet on each end face is a staircase of boxes approximating the wedge of a real fillet.
* The board is one dielectric box of thickness H.  Ground planes are conductor sheets at a depth below
  the top surface, with an optional rectangular cut-out (as the OPA855 datasheet, SBOS622D p. 29,
  asks under the feedback network).  The solder mask is a dielectric layer on the board surface with
  openings around the pads.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import materials as mat
from .geometry import GROUND, Film, Interval, Layout, LinearProfile

# ------------------------------------------------------------------------------------------------
# Dimensions from manufacturers' documents (companion note, Table G.2; every value with its page in
# data/parasitic_cf/geometry_and_permittivity.md).
#   Body: Panasonic ERJ (AOA0000C301 p. 3), Yageo RC (RC_L V.14 p. 4 Table 1), Vishay CRCW (20035 p. 11),
#   KOA RK73B (p. 1), TT Electronics WCR (p. 1).  Stored: the nominal L and W, and (min, nominal, max)
#   of T and a.  The tolerances of L and W in Table G.2 (+-0.03 to +-0.10 mm) are not stored, so the
#   corners of ChipResistor.from_size vary T and a only.
#   Pads: IPC-7351-based reflow land pattern of Vishay document 28950 (Rev. 12-Jul-2022, p. 1).
#
# 1206, added for the high-gain layouts (not in Table G.2; the same five documents and pages, read
# for this size, and the same rule as Table G.2: the value that most makers print, with a range
# that spans all of them where they differ):
#   Panasonic ERJ8G   L 3.20 +0.05/-0.20, W 1.60 +0.05/-0.15, T 0.60 +-0.10, a 0.50 +-0.20
#                     (marked "not recommended for new design" on p. 3);
#   Yageo RC1206      L 3.10 +-0.10, W 1.60 +-0.10, T 0.55 +-0.10, a 0.45 +-0.20;
#   Vishay CRCW1206   L 3.2 +0.10/-0.20, W 1.6 +-0.15, T 0.55 +-0.05, a (T2, top) 0.4 +-0.20;
#   KOA RK73B2B       L 3.2 +-0.2, W 1.6 +-0.2, T 0.6 +-0.1, a (c) 0.5 +-0.3;
#   TT WCR1206        L 3.1 +-0.15, W 1.55 +0.15/-0.1, T 0.55 +-0.1, a (C) 0.45 +-0.2.
#   L = 3.20 (three of five; Yageo and TT 3.10), W = 1.60 (four of five).  T = 0.55 (three of five),
#   from 0.45 (0.55 - 0.10) to 0.70 (0.60 + 0.10).  For a the five nominal values are 0.40, 0.45 (two)
#   and 0.50 (two), so no value is printed by most makers; the median, 0.45, is taken, with the
#   tolerance that four of the five print, +-0.20: 0.25 to 0.65.
#   Pads, Vishay 28950 p. 1 (IPC-7351 reflow): gap G 1.75, pad length Y 1.15, pad width X 1.80.
# ------------------------------------------------------------------------------------------------
CHIP_SIZES = {
    #        L     W              T (min, nom, max)    a (min, nom, max)
    "0201": dict(L=0.60, W=0.30, T=(0.20, 0.23, 0.26), a=(0.05, 0.10, 0.15)),
    "0402": dict(L=1.00, W=0.50, T=(0.30, 0.35, 0.40), a=(0.10, 0.20, 0.30)),
    "0603": dict(L=1.60, W=0.80, T=(0.35, 0.45, 0.55), a=(0.10, 0.30, 0.50)),
    "0805": dict(L=2.00, W=1.25, T=(0.40, 0.50, 0.70), a=(0.20, 0.40, 0.60)),
    "1206": dict(L=3.20, W=1.60, T=(0.45, 0.55, 0.70), a=(0.25, 0.45, 0.65)),
}
LAND_PATTERNS = {
    # w = pad length along the resistor axis, l = pad width across it, s = gap between pads (mm)
    "0201": dict(w=0.43, l=0.42, s=0.27),
    "0402": dict(w=0.55, l=0.60, s=0.40),
    "0603": dict(w=0.90, l=1.00, s=0.70),
    "0805": dict(w=0.90, l=1.45, s=1.00),
    "1206": dict(w=1.15, l=1.80, s=1.75),
}
_CORNER = {"min": 0, "nominal": 1, "max": 2}


@dataclass
class ChipResistor:
    """A two-terminal chip resistor.  Symbols as in the companion note's Figure 38.

    L, W, T : overall length, width and height (mm).
    a       : length of the top (and bottom) termination wrap; the film length is g = L - 2a.
    t_term  : thickness of the termination metal (mm).  No datasheet gives it; the default 0.015 mm
              is an assumption.  Doubling it to 0.030 mm adds 0.63 fF to an 0402 (details_0402).
    side_wraps : whether the terminations also cover the long side faces over the length a.  No
              construction drawing states this (companion note, Section G.3), so it is an option.
    film    : "up" (normal mounting, film facing away from the board) or "down" (upside down).
    film_width : width of the film across the part; default W.
    body    : the substrate material (alumina by default).
    """

    L: float
    W: float
    T: float
    a: float
    t_term: float = 0.015
    side_wraps: bool = False
    film: str = "up"
    film_width: float | None = None
    body: str | mat.Material = "alumina"

    @classmethod
    def from_size(cls, size: str, corner: str = "nominal", **kw) -> "ChipResistor":
        """Dimensions of size code ``size`` at the 'min', 'nominal' or 'max' corner of T and a."""
        d = CHIP_SIZES[size]
        i = _CORNER[corner]
        return cls(L=d["L"], W=d["W"], T=d["T"][i], a=d["a"][i], **kw)

    @property
    def g(self) -> float:
        """Film length between the inner edges of the top wraps."""
        return self.L - 2.0 * self.a

    def __post_init__(self):
        if self.film not in ("up", "down"):
            raise ValueError("film must be 'up' or 'down'")
        if not (0 < self.a < self.L / 2):
            raise ValueError("need 0 < a < L/2")
        if not (0 < self.t_term < min(self.a, self.T / 2)):
            raise ValueError("need 0 < t_term < min(a, T/2)")


@dataclass
class LandPattern:
    """Two rectangular pads.  w along the axis, l across, s between them, t_cu copper thickness."""

    w: float
    l: float
    s: float
    t_cu: float = 0.035

    @classmethod
    def from_size(cls, size: str, **kw) -> "LandPattern":
        d = LAND_PATTERNS[size]
        return cls(w=d["w"], l=d["l"], s=d["s"], **kw)


@dataclass
class Plane:
    """A conductor sheet at ``depth`` below the board's top surface (net ``net``, ground by default),
    covering the whole board except an optional rectangular ``cutout`` {"x": (x0, x1), "y": (y0, y1)}.

    ``mesh_size`` sets the element size at the plane's edges (the cut-out border), which can be
    coarser than at the parts when the plane lies well below and away from them (meshing.py)."""

    depth: float
    cutout: dict[str, Interval] | None = None
    net: str = GROUND
    mesh_size: float | None = None


@dataclass
class SolderMask:
    """A dielectric layer of ``thickness`` on the board surface, open over each pad grown by
    ``clearance`` on every side.

    thickness 0.02 mm: the middle of the 10-30 um of the companion note's Section G.3.
    clearance 0.05 mm: an assumption, inside the 0.07 mm maximum of TI's land-pattern drawings for
    non-solder-mask-defined pads (OPA855 datasheet p. 39, OPA846 datasheet p. 27)."""

    thickness: float = 0.02
    material: str | mat.Material = "solder_mask"
    clearance: float = 0.05


@dataclass
class Board:
    """The printed-circuit board: a dielectric slab of ``thickness`` below z = 0.

    ``size`` is its lateral extent (sx, sy) centred on the origin; None makes it fill the enclosure,
    which represents a board much larger than the parts (the enclosure is then the only lateral
    limit, and the enclosure study of study.py extrapolates both to infinity together)."""

    thickness: float = 1.6
    material: str | mat.Material = "FR4"
    size: tuple[float, float] | None = None
    planes: list[Plane] = field(default_factory=list)
    mask: SolderMask | None = None


@dataclass
class Mount:
    """How the part sits on its pads.

    standoff : gap between the pad top and the body's lower face (mm).  Under the bottom wraps it is
               solder; elsewhere air.  No document specifies it (companion note, Section G.10.4);
               the default 0.03 mm is an assumption.  The study varies it: 0.01 and 0.05 mm change
               C_F of an 0402 by +0.30 and +0.11 fF (details_0402).
    fillet_height : height of the solder fillet on each end face, as a fraction of T (0 = none).
    fillet_length : how far the fillet reaches out over the pad from the end face (mm); clipped to
               the pad.
    fillet_steps : number of boxes in the staircase that approximates the fillet's wedge.
    The fillet defaults (no fillet; 0.15 mm and 3 steps when one is asked for) are choices, not
    measured shapes.  A fillet of T/3 on an 0402 changes C_F by -0.01 fF (details_0402), less than
    the mesh error of that comparison, because it sits on the outer end faces, which face away from
    the other terminal.
    """

    standoff: float = 0.03
    fillet_height: float = 0.0
    fillet_length: float = 0.15
    fillet_steps: int = 3


# ================================================================================================
def board_layout(board: Board, enclosure_half: float, above: float | None = None, below: float | None = None,
                 name: str = "", boundary: str = "ground") -> Layout:
    """A 3-D layout holding only the board (and its planes and mask), inside an enclosure of
    half-width ``enclosure_half`` in x and y, extending ``above`` over the top surface and ``below``
    under the bottom (both default to enclosure_half)."""
    R = float(enclosure_half)
    above = R if above is None else above
    below = R if below is None else below
    lay = Layout(3, name)
    H = board.thickness
    sx, sy = board.size if board.size is not None else (2 * R, 2 * R)
    bx, by = (-sx / 2, sx / 2), (-sy / 2, sy / 2)
    lay.add_box(bx, by, (-H, 0.0), material=board.material, label="board", name="board")
    for k, pl in enumerate(board.planes):
        if not (0 < pl.depth <= H):
            raise ValueError("a plane must lie inside the board (0 < depth <= thickness)")
        holes = [dict(pl.cutout)] if pl.cutout else []
        lay.add_sheet("z", -pl.depth, {"x": bx, "y": by}, net=pl.net, holes=holes, name=f"plane{k}",
                      mesh_size=pl.mesh_size)
    lay.set_enclosure({"x": (-R, R), "y": (-R, R), "z": (-H - below, above)}, boundary=boundary)
    return lay


def add_pad(lay: Layout, x: Interval, y: Interval, t_cu: float, net: str, floating: bool = False,
            name: str = "pad") -> None:
    """A copper pad on the board surface: a box of thickness t_cu, or a sheet when t_cu = 0."""
    if t_cu > 0:
        lay.add_box(x, y, (0.0, t_cu), net=net, floating=floating, name=name)
    else:
        lay.add_sheet("z", 0.0, {"x": x, "y": y}, net=net, floating=floating, name=name)


def add_mask(lay: Layout, board: Board, openings: list[tuple[Interval, Interval]]) -> None:
    """Solder mask over the board surface, removed over each opening (x, y) grown by the clearance.

    The mask is one box over the board; each opening is then painted with the enclosure medium (air),
    which by the painter's order of geometry.py removes the mask there.  Pads painted afterwards fill
    the openings' centres."""
    m = board.mask
    if m is None:
        return
    R = lay.enclosure.spans["x"][1]
    sx, sy = board.size if board.size is not None else (2 * R, 2 * R)
    lay.add_box((-sx / 2, sx / 2), (-sy / 2, sy / 2), (0.0, m.thickness), material=m.material,
                label="solder mask", name="mask")
    c = m.clearance
    for k, (ox, oy) in enumerate(openings):
        lay.add_box((ox[0] - c, ox[1] + c), (oy[0] - c, oy[1] + c), (0.0, m.thickness), material="air",
                    label="air", name=f"mask-open{k}")


def add_resistor(lay: Layout, res: ChipResistor, z_bottom: float, x0: float = 0.0, y0: float = 0.0,
                 nets=("A", "B"), name: str = "R") -> None:
    """Body, terminations and film of ``res`` with its lower face at z = z_bottom, centred at
    (x0, y0), axis along x, net nets[0] at +x and nets[1] at -x."""
    L, W, T, a, t = res.L, res.W, res.T, res.a, res.t_term
    xb, yb, zb = (x0 - L / 2, x0 + L / 2), (y0 - W / 2, y0 + W / 2), (z_bottom, z_bottom + T)
    lay.add_box(xb, yb, zb, material=res.body, label="alumina" if res.body == "alumina" else "", name=f"{name}-body")
    for sgn, net in ((+1, nets[0]), (-1, nets[1])):
        # x-interval of this end's wrap region and of its end cap
        xe = (x0 + L / 2 - a, x0 + L / 2) if sgn > 0 else (x0 - L / 2, x0 - L / 2 + a)
        xc = (x0 + L / 2 - t, x0 + L / 2) if sgn > 0 else (x0 - L / 2, x0 - L / 2 + t)
        lay.add_box(xc, yb, zb, net=net, name=f"{name}-cap{net}")
        lay.add_box(xe, yb, (zb[1] - t, zb[1]), net=net, name=f"{name}-top{net}")
        lay.add_box(xe, yb, (zb[0], zb[0] + t), net=net, name=f"{name}-bot{net}")
        if res.side_wraps:
            lay.add_box(xe, (yb[0], yb[0] + t), zb, net=net, name=f"{name}-sideL{net}")
            lay.add_box(xe, (yb[1] - t, yb[1]), zb, net=net, name=f"{name}-sideR{net}")
    # The film: on the face away from the board ("up") or towards it ("down"), between the wraps.
    g = res.g
    fw = res.film_width if res.film_width is not None else W
    zf = zb[1] if res.film == "up" else zb[0]
    film = Film(hi=nets[0], lo=nets[1], profile=LinearProfile("x", x0 - g / 2, x0 + g / 2))
    lay.add_sheet("z", zf, {"x": (x0 - g / 2, x0 + g / 2), "y": (y0 - fw / 2, y0 + fw / 2)}, film=film,
                  name=f"{name}-film")


def resistor_on_pads(res: ChipResistor, pads: LandPattern, board: Board | None = None,
                     mount: Mount | None = None, enclosure_half: float = 10.0, nets=("A", "B"),
                     boundary: str = "ground", symmetric: bool = True, name: str = "") -> Layout:
    """A chip resistor soldered on its two pads on a board, centred at the origin.

    With ``symmetric`` the layout declares both mirror symmetries (x with A <-> B, and y); the
    declaration is checked when the layout is meshed, so an asymmetric board (a cut-out off centre,
    say) is reported instead of silently computed wrongly."""
    board = board or Board()
    mount = mount or Mount()
    lay = board_layout(board, enclosure_half, name=name or "resistor on pads", boundary=boundary)
    w, l, s, tc = pads.w, pads.l, pads.s, pads.t_cu
    pad_x = {nets[0]: (s / 2, s / 2 + w), nets[1]: (-s / 2 - w, -s / 2)}
    pad_y = (-l / 2, l / 2)
    add_mask(lay, board, [(pad_x[nets[0]], pad_y), (pad_x[nets[1]], pad_y)])
    for net in nets:
        add_pad(lay, pad_x[net], pad_y, tc, net, name=f"pad{net}")
    z_bottom = tc + mount.standoff
    # Solder under each bottom wrap: from the pad top to the body's lower face, where the wrap and the
    # pad overlap in x and y.
    if mount.standoff > 0:
        L, W, a = res.L, res.W, res.a
        for sgn, net in ((+1, nets[0]), (-1, nets[1])):
            wrap_x = (L / 2 - a, L / 2) if sgn > 0 else (-L / 2, -L / 2 + a)
            sx = (max(wrap_x[0], pad_x[net][0]), min(wrap_x[1], pad_x[net][1]))
            sy = (max(-W / 2, pad_y[0]), min(W / 2, pad_y[1]))
            if sx[1] > sx[0] and sy[1] > sy[0]:
                lay.add_box(sx, sy, (tc, z_bottom), net=net, name=f"solder{net}")
    # Optional solder fillet on each end face: a staircase of boxes, widest at the bottom.
    if mount.fillet_height > 0:
        n, hf = mount.fillet_steps, mount.fillet_height * res.T
        for sgn, net in ((+1, nets[0]), (-1, nets[1])):
            for k in range(n):
                reach = mount.fillet_length * (n - k) / n
                xr = (res.L / 2, min(res.L / 2 + reach, s / 2 + w)) if sgn > 0 else \
                     (max(-res.L / 2 - reach, -s / 2 - w), -res.L / 2)
                zr = (tc + hf * k / n, tc + hf * (k + 1) / n)
                if xr[1] > xr[0]:
                    lay.add_box(xr, (max(-res.W / 2, pad_y[0]), min(res.W / 2, pad_y[1])), zr, net=net,
                                name=f"fillet{net}{k}")
    add_resistor(lay, res, z_bottom, nets=nets)
    if symmetric:
        lay.set_symmetry(mirror_x=True, mirror_y=True, pair=nets)
    return lay


# ================================================================================================
@dataclass
class WsonPackage:
    """An 8-pin WSON/SON package with a thermal pad, as the OPA855's DSG0008A (OPA855 datasheet
    SBOS622D, pp. 38-39).

    Dimensions and where they come from:
      * body 2.0 x 2.0 mm (body_x, body_depth): midpoint of 1.9-2.1 mm (p. 38);
      * body_height 0.75 mm: midpoint of the overall height 0.7-0.8 mm (p. 38);
      * pitch 0.5 mm and board pads 0.25 mm wide (pin_width) by 0.5 mm long (pad_length): the example
        board layout (p. 39);
      * under_body 0.3 mm: the board pads' centres lie 1.9 mm apart across the package (p. 39), so a
        pad 0.5 mm long spans 0.95 - 0.25 = 0.70 mm to 0.95 + 0.25 = 1.20 mm from the package's
        centre line; the body edge is at 1.0 mm (half of 2.0), so 1.0 - 0.70 = 0.30 mm of the pad lies
        under the body and 0.20 mm outside;
      * wall_height 0.2 mm: the drawing gives two manufacturing options for the terminals' exposed
        side-wall metal, 0.1 or 0.2 mm (p. 38, "side wall metal thickness, dim A").  The default takes
        option 2, 0.2 mm, which gives the larger coupling: the companion note's Eq. (G.47) puts the
        side-wall term at 2.1 fF for 0.1 mm against 4.3 fF for 0.2 mm;
      * thermal pad 1.6 x 0.9 mm (thermal_x, thermal_y): the exposed pad, 1.6 +-0.1 by 0.9 +-0.1 mm
        (p. 38), with the same land on the board (p. 39);
      * standoff 0.03 mm: the solder under each terminal; assumed (the drawing's 0.00-0.05 mm is the
        package's own stand-off, not the joint).
    Pins (p. 3, Table 5-1): 1 FB, 2 NC (do not connect, hence floating), 3 IN-, 4 IN+; 5 VS-, 6 OUT,
    7 VS+, 8 PD; thermal pad to VS-.

    The pins are placed along one edge (pins 1-4); only that edge is modelled.  Pins 5-8 lie 1.9 mm
    away (p. 39).  OUT (pin 6) is the output, the same node as FB at the frequencies of interest, so
    leaving it out lowers C_F (Rule 2 of the companion note: less metal on A); VS-, VS+ and PD are AC
    grounds, so leaving them out raises C_F (Rule 6).  The sign of the omission is therefore not
    known; its size is small because of the 1.9-mm distance.  Each pin has a net name; use the
    floating flag for an unconnected pin.

    edge_y  : y of the package edge on the pin side; the body extends to +y from there.
    x_pins  : x positions of the pin centres (pin 1 first).
    """

    edge_y: float
    x_pins: tuple[float, ...]
    nets: tuple[str, ...]
    floating: tuple[bool, ...]
    body_x: Interval = (-1.0, 1.0)
    body_depth: float = 2.0
    body_height: float = 0.75
    pin_width: float = 0.25
    pad_length: float = 0.5
    under_body: float = 0.3
    wall_height: float = 0.2
    thermal_x: Interval = (-0.8, 0.8)
    thermal_y: Interval = (0.55, 1.45)
    thermal_net: str = GROUND
    standoff: float = 0.03
    mould: str | mat.Material = "mould"


def add_wson(lay: Layout, pkg: WsonPackage, t_cu: float = 0.035) -> None:
    """Board pads, terminal metal, thermal pad and mould body of a WSON package.

    The board pad of each pin runs from ``pad_length - under_body`` outside the body edge to
    ``under_body`` inside it.  The package terminal above the inner part is a metal block of height
    ``wall_height`` (its exposed side wall), on a solder layer of ``standoff``.  The mould body fills
    the package outline above the standoff; the terminals and the exposed thermal pad are painted
    over it.  The die, bond wires and lead fingers inside are not modelled (approximation 12 of the
    companion note): no published geometry exists for them."""
    y_edge = pkg.edge_y
    z_body = t_cu + pkg.standoff
    # mould body over the package outline
    lay.add_box(pkg.body_x, (y_edge, y_edge + pkg.body_depth), (z_body, z_body + pkg.body_height),
                material=pkg.mould, label="mould", name="package")
    for k, (xc, net, fl) in enumerate(zip(pkg.x_pins, pkg.nets, pkg.floating), start=1):
        xp = (xc - pkg.pin_width / 2, xc + pkg.pin_width / 2)
        yp = (y_edge - (pkg.pad_length - pkg.under_body), y_edge + pkg.under_body)
        add_pad(lay, xp, yp, t_cu, net, floating=fl, name=f"pin{k}-pad")
        # solder and terminal metal under the body
        yt = (y_edge, y_edge + pkg.under_body)
        lay.add_box(xp, yt, (t_cu, z_body + pkg.wall_height), net=net, floating=fl, name=f"pin{k}-term")
    # thermal pad: board copper plus the package's exposed pad above it
    ty = (y_edge + pkg.thermal_y[0], y_edge + pkg.thermal_y[1])
    add_pad(lay, pkg.thermal_x, ty, t_cu, pkg.thermal_net, name="thermal-pad")
    lay.add_box(pkg.thermal_x, ty, (t_cu, z_body + pkg.wall_height), net=pkg.thermal_net, name="thermal-term")


def add_trace(lay: Layout, x: Interval, y: Interval, t_cu: float, net: str, name: str = "trace") -> None:
    """A rectangular copper trace on the board surface (same construction as a pad)."""
    add_pad(lay, x, y, t_cu, net, name=name)
