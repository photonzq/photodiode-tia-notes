"""Describing a layout: boxes, sheets, nets, films, the enclosure and its symmetries.

Why this module exists
----------------------
The solver needs to know, for every point of space, what is there: which insulator (and so which
permittivity), or which conductor (and so which potential).  This module is the vocabulary for
saying that.  It knows nothing about meshes or finite elements; ``meshing.py`` turns a ``Layout``
into a mesh and ``fem.py`` solves on it.  Keeping the description separate means the same layout
can be meshed coarsely or finely, in three dimensions or as its two-dimensional cross-section,
and checked for symmetry, without being rebuilt.

Coordinates and units
---------------------
Lengths are in millimetres (see ``constants.py``).  The package's convention for a resistor on a
board, which the builders in ``parts.py`` follow, is
    x : along the resistor axis; net "A" lies at +x and net "B" at -x;
    y : across the resistor, in the board plane;
    z : up; the board's top surface is z = 0.
A two-dimensional layout is the cross-section in the (x, z) plane; its points are (x, z).

What a layout contains
----------------------
* ``Box`` (3-D) / ``Rect`` (2-D): an axis-aligned volume (area) filled either with a dielectric or
  with conductor.  Boxes may overlap: a later item replaces an earlier one where they overlap
  ("painter's order").  This is how a copper pad is placed on top of a board, or a termination
  over the end of a resistor body, without having to cut holes by hand.
* ``Sheet`` (3-D) / ``Segment`` (2-D): an axis-aligned conductor of zero thickness (a rectangle in
  3-D, a line segment in 2-D).  It is used for metal that is thin compared with every gap (a
  ground plane, a thin pad) and for resistive films.
* Roles.  ``Dielectric`` gives a permittivity.  ``Conductor`` gives a net name: all conductors with
  the same net are at the same potential.  The net "gnd" is held at 0 V in every solve.  A
  conductor marked ``floating`` is connected to nothing: its potential is unknown and its net
  charge is zero (an unconnected pin).  ``Film`` is a resistive film between two nets; its
  potential is prescribed point by point, as explained under ``LinearProfile``.
* ``Enclosure``: the box that bounds the computation, filled with a dielectric (air by default),
  with a boundary condition on its faces (see ``Enclosure``).
* Symmetry flags: if the layout is its own mirror image, the solver can work on a half or a
  quarter of it (see ``capacitance.py`` for why the result is still exact).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from typing import Callable, Sequence

import numpy as np

from . import materials as mat

Interval = tuple[float, float]
AXES_3D = ("x", "y", "z")
AXES_2D = ("x", "z")
GROUND = "gnd"


# ================================================================================================
# Roles: what fills a box or a sheet
# ================================================================================================
@dataclass(frozen=True)
class Dielectric:
    """An insulator.  ``label`` groups regions in result tables (for example every piece of the
    board is labelled "board" even if the layout splits it into several boxes)."""

    material: mat.Material
    label: str = ""

    @property
    def eps_r(self) -> float:
        return self.material.eps_r

    @property
    def name(self) -> str:
        return self.label or self.material.name


@dataclass(frozen=True)
class Conductor:
    """A perfect conductor on net ``net``.

    Inside a perfect conductor in electrostatic equilibrium the field is zero, so the potential is
    the same everywhere on and in it.  The solver therefore fixes the potential of every mesh
    degree of freedom that belongs to the conductor (Dirichlet condition), or, for a floating
    conductor, ties them to one shared unknown (see ``fem.py``).
    """

    net: str
    floating: bool = False

    def __post_init__(self):
        if self.floating and self.net == GROUND:
            raise ValueError("the ground net cannot be floating")


@dataclass(frozen=True)
class LinearProfile:
    """The DC potential of a uniform straight film, as a fraction u in [0, 1] of the voltage between
    its two terminals.

    Derivation, for a rectangular film with its terminations on two opposite sides.  At DC the film
    carries a current density J = -grad(phi) / R_s (Ohm's law, sheet resistance R_s), and charge
    conservation, div J = 0, makes phi satisfy Laplace's equation in the film.  Its boundary
    conditions are phi = V_lo on the low-side termination, phi = V_hi on the high-side one, and zero
    normal current, d(phi)/dn = 0, on the two side edges, which border insulator.  The linear function
        phi = V_lo + (V_hi - V_lo) * u,   u(s) = (s - start) / (end - start),   s = coordinate along ``axis``,
    meets all three: it is harmonic (its second derivatives vanish), it takes the termination
    values at s = start and s = end, and its gradient points along ``axis``, so its normal derivative
    on the side edges, which run along ``axis``, is zero.  By uniqueness of the solution of Laplace's
    equation with these conditions, it is the film's potential.  The argument needs a rectangle with
    straight terminations across its whole width; trim cuts or a meander make the potential
    non-linear (the companion note's approximation 4), and such a film needs another profile.

    Outside [start, end] the value is clipped to [0, 1]; such points only occur on a film that
    reaches under a termination, where the termination's potential governs anyway.  The clipped
    function has kinks at s = start and s = end.  It is reproduced exactly by the elements only
    because the film sheet itself ends at those coordinates, so the kinks fall on mesh lines; a film
    sheet that extended past them would carry the kink inside an element.

    Why the DC potential is the right boundary data.  With displacement current, the current along
    the film is no longer constant: it changes by j omega times the charge per length that the film
    sheds to its surroundings (companion note, Eq. (G.5)).  That change is small while omega R C << 1,
    with R the film's resistance and C the part of the capacitance that loads the film (its coupling
    to everything at other potentials), and then the film's potential is its DC distribution to first
    order in frequency.  The companion note derives the resulting feedback capacitance,
    C_F = -v^T C u with v = 1 - u (its Section G.2.3, Eqs. (G.6)-(G.9)); the field form of that
    expression is in ``capacitance.py``.  The note also gives the first neglected terms, of second
    order: for a uniform RC line, a conductance 7 (omega R C)^2 / 360 relative to 1/R and a change of
    31 (omega R C)^2 / 2520 relative to the effective capacitance (paragraph after its Eq. (G.8)).  At
    a TIA's own -3 dB point omega R_F C_F is about 1, so the condition "<< 1" fails there; it is these
    small coefficients, 1.9 % and 1.2 % at omega R C = 1, that keep the DC profile accurate.
    """

    axis: str
    start: float
    end: float

    def __post_init__(self):
        if self.end == self.start:
            raise ValueError("a film profile needs start != end")

    def __call__(self, coords: np.ndarray, axes: Sequence[str]) -> np.ndarray:
        """Evaluate u at points ``coords`` (shape (dim, n)) whose rows are named by ``axes``."""
        row = list(axes).index(self.axis)
        s = coords[row]
        return np.clip((s - self.start) / (self.end - self.start), 0.0, 1.0)

    def mirrored(self, axis: str) -> "LinearProfile":
        """Profile of the mirror image (coordinate ``axis`` -> -coordinate).  Mirroring the film
        along its own axis swaps which end is which, so start and end change sign."""
        if axis != self.axis:
            return self
        return LinearProfile(self.axis, -self.start, -self.end)


@dataclass(frozen=True)
class Film:
    """A resistive film between nets ``hi`` (where u = 1) and ``lo`` (where u = 0).

    Its potential is prescribed as phi = V_lo + (V_hi - V_lo) * u(position).  ``profile`` is any
    callable ``(coords, axes) -> u``; ``LinearProfile`` covers a plain film.  For a patterned film
    (trim cut, meander) the user supplies the DC potential of that pattern instead.
    """

    hi: str
    lo: str
    profile: Callable

    def potential(self, coords: np.ndarray, axes: Sequence[str], v_hi: float, v_lo: float) -> np.ndarray:
        u = self.profile(coords, axes)
        return v_lo + (v_hi - v_lo) * u


Role = Dielectric | Conductor | Film


# ================================================================================================
# Primitives
# ================================================================================================
def _check_interval(iv: Interval, what: str) -> Interval:
    a, b = float(iv[0]), float(iv[1])
    if not b > a:
        raise ValueError(f"{what}: interval {iv} must have hi > lo")
    return (a, b)


@dataclass
class Box:
    """Axis-aligned box [x0, x1] x [y0, y1] x [z0, z1] (3-D) filled with ``role``."""

    x: Interval
    y: Interval
    z: Interval
    role: Dielectric | Conductor
    name: str = ""
    mesh_size: float | None = None   # element size at this item's edges (meshing.py); None = global h_edge

    def __post_init__(self):
        self.x = _check_interval(self.x, f"box {self.name} x")
        self.y = _check_interval(self.y, f"box {self.name} y")
        self.z = _check_interval(self.z, f"box {self.name} z")
        if isinstance(self.role, Film):
            raise TypeError("a film is a sheet, not a box")

    @property
    def spans(self) -> dict[str, Interval]:
        return {"x": self.x, "y": self.y, "z": self.z}


@dataclass
class Rect:
    """Axis-aligned rectangle [x0, x1] x [z0, z1] of a two-dimensional (x, z) layout."""

    x: Interval
    z: Interval
    role: Dielectric | Conductor
    name: str = ""
    mesh_size: float | None = None

    def __post_init__(self):
        self.x = _check_interval(self.x, f"rect {self.name} x")
        self.z = _check_interval(self.z, f"rect {self.name} z")
        if isinstance(self.role, Film):
            raise TypeError("a film is a segment, not a rectangle")

    @property
    def spans(self) -> dict[str, Interval]:
        return {"x": self.x, "z": self.z}


@dataclass
class Sheet:
    """Zero-thickness axis-aligned rectangle in a 3-D layout.

    ``normal`` is the axis perpendicular to the sheet and ``at`` its coordinate.  ``spans`` gives
    the extent along the two other axes, as a dict such as {"x": (x0, x1), "y": (y0, y1)}.
    ``holes`` is a list of such dicts, rectangles removed from the sheet (a cut-out in a ground
    plane under a resistor, for example).
    """

    normal: str
    at: float
    spans: dict[str, Interval]
    role: Conductor | Film
    name: str = ""
    holes: list[dict[str, Interval]] = field(default_factory=list)
    mesh_size: float | None = None

    def __post_init__(self):
        if self.normal not in AXES_3D:
            raise ValueError("normal must be 'x', 'y' or 'z'")
        need = [a for a in AXES_3D if a != self.normal]
        if sorted(self.spans) != sorted(need):
            raise ValueError(f"sheet {self.name}: spans must be given for axes {need}")
        self.spans = {a: _check_interval(self.spans[a], f"sheet {self.name} {a}") for a in need}
        self.at = float(self.at)
        if isinstance(self.role, Dielectric):
            raise TypeError("a sheet has no volume, so it cannot be a dielectric")


@dataclass
class Segment:
    """Zero-thickness line segment of a two-dimensional (x, z) layout: ``normal`` 'z' gives a
    horizontal segment at z = at spanning x; 'x' a vertical one at x = at spanning z."""

    normal: str
    at: float
    span: Interval
    role: Conductor | Film
    name: str = ""
    mesh_size: float | None = None

    def __post_init__(self):
        if self.normal not in AXES_2D:
            raise ValueError("normal must be 'x' or 'z' in a 2-D layout")
        self.span = _check_interval(self.span, f"segment {self.name}")
        self.at = float(self.at)
        if isinstance(self.role, Dielectric):
            raise TypeError("a segment cannot be a dielectric")

    @property
    def along(self) -> str:
        return "x" if self.normal == "z" else "z"


Item = Box | Rect | Sheet | Segment


@dataclass
class Enclosure:
    """The outer box of the computation and its boundary condition.

    ``boundary`` is "ground" or "open" and applies to every face; ``faces`` can override single faces,
    with keys "xmin", "xmax", "ymin", "ymax", "zmin", "zmax" (no y keys in 2-D).

    * "ground" (Dirichlet, phi = 0): the enclosure is a grounded metal box.  Far from the layout it
      stands for the ground "at infinity" or for a real shield.
    * "open" (homogeneous Neumann, zero normal field): no field line leaves through the face.  It is
      the natural condition of the variational problem: nothing has to be imposed.  It is also the
      exact condition on a plane of mirror symmetry for an even potential, and it represents an
      insulating cut (Rule 3 of the companion note's Section G.4.3).

    Which kind stands for "nothing nearby".  Only a grounded enclosure does, and only in 3-D.
      * Grounded, 3-D: as the box grows, the capacitances converge to those of the layout with ground
        at infinity, and study.enclosure_correction extrapolates to that limit (the 1/R law is
        derived there).
      * Open, around a layout with no grounded conductor of its own: the even drive (A and B at the
        same potential, capacitance.py) then has nowhere to send its field lines, so it stores no
        energy, and the computed C_F is twice the odd energy.  That is the two-terminal capacitance
        of the pair, C_2t = C_m + C_A0 C_B0 / (C_A0 + C_B0) (companion note, Eq. (G.4)), not the mutual
        capacitance C_m; for a symmetric pair the two differ by C_A0 / 2.  An open box is therefore the
        right model of an isolated pair with no ground anywhere, as in the closed-form checks of
        coplanar strips, but not of a pair whose ground lies far away.
      * Grounded, 2-D: per unit length, the capacitance of a net to a distant ground behaves as
        2 pi eps / ln(R / a), which falls to zero only logarithmically, so a 2-D cross-section has no
        finite "ground at infinity" limit, and study.enclosure_correction refuses 2-D layouts.
    The far boundary is never exactly at infinity; ``study.py`` estimates how much a grounded 3-D
    result moves when the enclosure is enlarged.
    """

    spans: dict[str, Interval]
    boundary: str = "ground"
    faces: dict[str, str] = field(default_factory=dict)
    material: mat.Material = field(default_factory=lambda: mat.get("air"))

    def __post_init__(self):
        self.spans = {a: _check_interval(v, f"enclosure {a}") for a, v in self.spans.items()}
        for kind in [self.boundary, *self.faces.values()]:
            if kind not in ("ground", "open"):
                raise ValueError(f"boundary condition {kind!r}: use 'ground' or 'open'")

    def face_condition(self, face: str) -> str:
        return self.faces.get(face, self.boundary)


# ================================================================================================
# The layout
# ================================================================================================
class Layout:
    """An ordered collection of items plus an enclosure and symmetry flags.

    Order matters for overlapping volumes: an item added later replaces earlier ones where they
    overlap.  Sheets and segments do not displace volumes; they are embedded in them.
    """

    def __init__(self, dim: int = 3, name: str = ""):
        if dim not in (2, 3):
            raise ValueError("dim must be 2 or 3")
        self.dim = dim
        self.name = name
        self.items: list[Item] = []
        self.enclosure: Enclosure | None = None
        # Mirror symmetries (see ``set_symmetry``).
        self.mirror_x: bool = False
        self.mirror_y: bool = False
        self.pair: tuple[str, str] = ("A", "B")

    # ---------------------------------------------------------------------------------------------
    @property
    def axes(self) -> tuple[str, ...]:
        return AXES_3D if self.dim == 3 else AXES_2D

    def add(self, item: Item) -> Item:
        ok3 = isinstance(item, (Box, Sheet))
        ok2 = isinstance(item, (Rect, Segment))
        if (self.dim == 3 and not ok3) or (self.dim == 2 and not ok2):
            raise TypeError(f"{type(item).__name__} does not belong in a {self.dim}-D layout")
        self.items.append(item)
        return item

    @staticmethod
    def _role(material=None, eps_r=None, net=None, floating=False, label="") -> Dielectric | Conductor:
        """Build a role from keyword arguments: exactly one of (material or eps_r) or net."""
        if net is not None:
            if material is not None or eps_r is not None:
                raise ValueError("give either a net (conductor) or a material (dielectric), not both")
            return Conductor(net, floating)
        if material is None and eps_r is None:
            raise ValueError("give a material, an eps_r or a net")
        m = mat.custom(label or f"eps{eps_r:g}", eps_r) if eps_r is not None else mat.get(material)
        return Dielectric(m, label)

    def add_box(self, x: Interval, y: Interval, z: Interval, *, material=None, eps_r=None, net=None,
                floating=False, label="", name="", mesh_size=None) -> Box:
        return self.add(Box(x, y, z, self._role(material, eps_r, net, floating, label), name, mesh_size))

    def add_rect(self, x: Interval, z: Interval, *, material=None, eps_r=None, net=None,
                 floating=False, label="", name="", mesh_size=None) -> Rect:
        return self.add(Rect(x, z, self._role(material, eps_r, net, floating, label), name, mesh_size))

    def add_sheet(self, normal: str, at: float, spans: dict[str, Interval], *, net=None,
                  floating=False, film: Film | None = None, holes=(), name="", mesh_size=None) -> Sheet:
        role = film if film is not None else Conductor(net, floating)
        return self.add(Sheet(normal, at, dict(spans), role, name, list(holes), mesh_size))

    def add_segment(self, normal: str, at: float, span: Interval, *, net=None, floating=False,
                    film: Film | None = None, name="", mesh_size=None) -> Segment:
        role = film if film is not None else Conductor(net, floating)
        return self.add(Segment(normal, at, span, role, name, mesh_size))

    def set_enclosure(self, spans: dict[str, Interval] | None = None, *, margin: float | None = None,
                      boundary: str = "ground", faces: dict[str, str] | None = None,
                      material="air") -> Enclosure:
        """Set the enclosure explicitly (``spans``) or as the bounding box of all items grown by
        ``margin`` on every side."""
        if spans is None:
            if margin is None:
                raise ValueError("give spans or a margin")
            bb = self.bounding_box()
            spans = {a: (bb[a][0] - margin, bb[a][1] + margin) for a in self.axes}
        self.enclosure = Enclosure(spans, boundary, dict(faces or {}), mat.get(material))
        return self.enclosure

    def set_symmetry(self, mirror_x: bool = False, mirror_y: bool = False, pair=("A", "B")) -> None:
        """Declare mirror symmetries.

        mirror_x : the layout maps onto itself under x -> -x when net pair[0] and net pair[1]
            are exchanged (a two-terminal part centred at x = 0, terminal A at +x, B at -x).
        mirror_y : the layout maps onto itself under y -> -y with every net unchanged (3-D only).

        ``check_symmetry`` verifies the declaration; ``capacitance.py`` explains how the solver uses it.
        """
        if mirror_y and self.dim == 2:
            raise ValueError("a 2-D (x, z) layout has no y axis to mirror")
        self.mirror_x, self.mirror_y, self.pair = bool(mirror_x), bool(mirror_y), tuple(pair)

    # ---------------------------------------------------------------------------------------------
    def nets(self) -> dict[str, bool]:
        """All conductor nets (films' terminals included), mapped to whether they are floating."""
        out: dict[str, bool] = {}
        for it in self.items:
            r = it.role
            if isinstance(r, Conductor):
                if out.get(r.net, r.floating) != r.floating:
                    raise ValueError(f"net {r.net!r} is floating on some items and connected on others")
                out[r.net] = r.floating
            elif isinstance(r, Film):
                out.setdefault(r.hi, False)
                out.setdefault(r.lo, False)
        return out

    def item_extent(self, it: Item) -> dict[str, Interval]:
        """Extent of an item along every axis (a sheet has zero extent along its normal)."""
        if isinstance(it, (Box, Rect)):
            return dict(it.spans)
        if isinstance(it, Sheet):
            d = dict(it.spans)
            d[it.normal] = (it.at, it.at)
            return d
        d = {it.along: it.span, it.normal: (it.at, it.at)}
        return d

    def bounding_box(self, only_conductors: bool = False) -> dict[str, Interval]:
        lo = {a: math.inf for a in self.axes}
        hi = {a: -math.inf for a in self.axes}
        for it in self.items:
            if only_conductors and isinstance(it.role, Dielectric):
                continue
            for a, (u, v) in self.item_extent(it).items():
                lo[a], hi[a] = min(lo[a], u), max(hi[a], v)
        if any(math.isinf(lo[a]) for a in self.axes):
            raise ValueError("the layout has no items (of the requested kind)")
        return {a: (lo[a], hi[a]) for a in self.axes}

    def core_bounding_box(self) -> dict[str, Interval]:
        """Bounding box of the conductors that carry signal (every net but ground) and of the films.

        This is where the field between the nets is strong, so meshing.py resolves it finely (the
        "core").  Grounded conductors are left out because a ground plane spanning the board would
        otherwise stretch the core over the whole board; ground that matters, such as a guard trace
        between the pads, lies inside this box anyway.  A layout with only ground conductors falls
        back to all conductors."""
        lo = {a: math.inf for a in self.axes}
        hi = {a: -math.inf for a in self.axes}
        for it in self.items:
            r = it.role
            if isinstance(r, Dielectric) or (isinstance(r, Conductor) and r.net == GROUND):
                continue
            for a, (u, v) in self.item_extent(it).items():
                lo[a], hi[a] = min(lo[a], u), max(hi[a], v)
        if any(math.isinf(lo[a]) for a in self.axes):
            return self.bounding_box(only_conductors=True)
        return {a: (lo[a], hi[a]) for a in self.axes}

    def smallest_feature(self) -> float:
        """Smallest positive dimension of any item and smallest positive distance between distinct
        coordinate planes of conductor items along each axis.

        Used by meshing.resolve_params twice: to choose the default edge size, and as an upper cap on
        the edge size at every refinement level, whether the edge size is the default or set by the
        user.  The field varies on the scale of the smallest gap or thickness, so an element larger
        than that cannot resolve it.  Because of the cap, a study whose coarser levels would exceed
        it does not refine uniformly; study.converge checks for that."""
        vals = []
        for it in self.items:
            for (u, v) in self.item_extent(it).values():
                if v > u:
                    vals.append(v - u)
        for a in self.axes:
            planes = sorted({c for it in self.items if not isinstance(it.role, Dielectric)
                             for c in self.item_extent(it)[a]})
            vals += [q - p for p, q in zip(planes, planes[1:]) if q - p > 1e-9]
        return min(vals)

    # ---------------------------------------------------------------------------------------------
    def check_symmetry(self, tol: float = 1e-9) -> None:
        """Raise ValueError unless every declared mirror symmetry holds.

        Why the check matters.  The symmetric solve (capacitance.py) computes only part of the field
        and multiplies by 2 or 4.  If the layout were not symmetric the result would be silently
        wrong, so the declaration is verified: every item's mirror image must also be an item of the
        layout, with the same role (nets exchanged as declared), films must carry a profile that
        maps onto itself, and the enclosure must be symmetric too: its span along the mirror axis
        must be centred on zero and its two faces normal to that axis must carry the same boundary
        condition, because the half-domain solve keeps only the face at the positive end.
        """
        for axis, active in (("x", self.mirror_x), ("y", self.mirror_y)):
            if not active:
                continue
            if self.enclosure is not None:
                lo, hi = self.enclosure.spans[axis]
                if abs(lo + hi) > tol * max(1.0, abs(hi)):
                    raise ValueError(f"enclosure span along {axis} ({lo}, {hi}) is not centred on 0")
                cmin = self.enclosure.face_condition(axis + "min")
                cmax = self.enclosure.face_condition(axis + "max")
                if cmin != cmax:
                    raise ValueError(f"enclosure faces {axis}min ({cmin}) and {axis}max ({cmax}) differ, "
                                     f"so the layout is not symmetric under {axis} -> -{axis}")
            swap = {self.pair[0]: self.pair[1], self.pair[1]: self.pair[0]} if axis == "x" else {}
            keys = [self._key(it, tol) for it in self.items]
            mirrored = [self._key(self._mirror(it, axis, swap), tol) for it in self.items]
            if sorted(keys) != sorted(mirrored):
                missing = sorted(set(mirrored) - set(keys))
                raise ValueError(f"layout is not symmetric under {axis} -> -{axis}; e.g. no item matches "
                                 f"{missing[:2]}")
            # A film's profile must map onto itself: phi(-x) under exchanged nets equals phi(x).
            for it in self.items:
                if isinstance(it.role, Film):
                    self._check_film_symmetry(it, axis, swap)

    def _mirror(self, it: Item, axis: str, swap: dict[str, str]) -> Item:
        def flip(iv):
            return (-iv[1], -iv[0])

        role = it.role
        if isinstance(role, Conductor):
            role = Conductor(swap.get(role.net, role.net), role.floating)
        elif isinstance(role, Film):
            prof = role.profile.mirrored(axis) if isinstance(role.profile, LinearProfile) else role.profile
            role = Film(swap.get(role.hi, role.hi), swap.get(role.lo, role.lo), prof)
        if isinstance(it, (Box, Rect)):
            spans = {a: (flip(v) if a == axis else v) for a, v in it.spans.items()}
            return replace(it, role=role, **spans)
        if isinstance(it, Sheet):
            spans = {a: (flip(v) if a == axis else v) for a, v in it.spans.items()}
            holes = [{a: (flip(v) if a == axis else v) for a, v in h.items()} for h in it.holes]
            at = -it.at if it.normal == axis else it.at
            return Sheet(it.normal, at, spans, role, it.name, holes, it.mesh_size)
        span = flip(it.span) if it.along == axis else it.span
        at = -it.at if it.normal == axis else it.at
        return Segment(it.normal, at, span, role, it.name, it.mesh_size)

    @staticmethod
    def _key(it: Item, tol: float):
        """Hashable description of an item's type, extent and role, rounded to ``tol``."""
        digits = max(0, int(round(-math.log10(tol))))

        def r(v):
            return round(v, digits) + 0.0          # + 0.0 turns -0.0 into 0.0

        role = it.role
        if isinstance(role, Dielectric):
            rk = ("diel", role.name, r(role.eps_r))
        elif isinstance(role, Conductor):
            rk = ("cond", role.net, role.floating)
        else:
            rk = ("film", tuple(sorted((role.hi, role.lo))))
        if isinstance(it, (Box, Rect)):
            ext = tuple((a, r(u), r(v)) for a, (u, v) in sorted(it.spans.items()))
            return (type(it).__name__, ext, rk)
        if isinstance(it, Sheet):
            ext = tuple((a, r(u), r(v)) for a, (u, v) in sorted(it.spans.items()))
            holes = tuple(sorted(tuple((a, r(u), r(v)) for a, (u, v) in sorted(h.items())) for h in it.holes))
            return ("Sheet", it.normal, r(it.at), ext, holes, rk)
        return ("Segment", it.normal, r(it.at), r(it.span[0]), r(it.span[1]), rk)

    def _check_film_symmetry(self, it: Item, axis: str, swap: dict[str, str]) -> None:
        """Check numerically that the film's potential is symmetric as required.

        Under x -> -x with A <-> B exchanged, the film potential phi = V_lo + (V_hi - V_lo) u must
        map onto itself, which for a film from B to A means u(-x) = 1 - u(x).  Under y -> -y with
        nets unchanged it means u(x, -y) = u(x, y).  Both are tested at a grid of 7 points per axis
        over the film.  For a LinearProfile that is a proof, not a sample: both sides of each relation
        are linear (or constant) along the film between the clip points, which lie on the film's ends,
        and two linear functions that agree at two or more points agree everywhere.  For any other
        profile the grid is only a spot check.
        """
        role: Film = it.role
        ext = self.item_extent(it)
        axes = self.axes
        grids = [np.linspace(*ext[a], 7) if ext[a][1] > ext[a][0] else np.array([ext[a][0]]) for a in axes]
        pts = np.array(np.meshgrid(*grids, indexing="ij")).reshape(len(axes), -1)
        u = role.profile(pts, axes)
        mp = pts.copy()
        mp[axes.index(axis)] *= -1.0
        um = role.profile(mp, axes)
        exchanged = swap.get(role.hi) == role.lo
        target = 1.0 - u if exchanged else u
        if np.max(np.abs(um - target)) > 1e-9:
            raise ValueError(f"film {it.name!r}: its potential is not symmetric under {axis} -> -{axis}")

    # ---------------------------------------------------------------------------------------------
    def section_y0(self, name: str | None = None) -> "Layout":
        """The cross-section of a 3-D layout in the plane y = 0, as a 2-D (x, z) layout.

        Each item that the plane cuts becomes its trace in the plane: a box becomes a rectangle, a
        sheet normal to z becomes a horizontal segment, a sheet normal to x a vertical one.  Sheets
        normal to y are parallel to the plane and are dropped.  A hole of a sheet removes its part
        of the segment where the hole spans y = 0.  The 2-D model then describes a layout that is
        uniform along y, and its results are per unit length (fF/mm).  The x mirror symmetry is
        kept; the y mirror has no meaning in 2-D.
        """
        if self.dim != 3:
            raise ValueError("only a 3-D layout has a y = 0 section")

        def cuts(iv):  # the plane y = 0 cuts an interval when it lies inside it (edges included)
            return iv[0] <= 0.0 <= iv[1] and iv[1] > iv[0]

        out = Layout(2, name or f"{self.name} (section y = 0)")
        for it in self.items:
            if isinstance(it, Box):
                if cuts(it.y):
                    out.add(Rect(it.x, it.z, it.role, it.name, it.mesh_size))
            elif isinstance(it, Sheet):
                if it.normal == "y":
                    continue
                if not cuts(it.spans["y"]):
                    continue
                if it.normal == "z":
                    pieces = [it.spans["x"]]
                    for h in it.holes:
                        if cuts(h["y"]):
                            pieces = _subtract(pieces, h["x"])
                    for k, pc in enumerate(pieces):
                        out.add(Segment("z", it.at, pc, it.role, f"{it.name}#{k}", it.mesh_size))
                else:  # normal x: vertical segment along z
                    pieces = [it.spans["z"]]
                    for h in it.holes:
                        if cuts(h["y"]):
                            pieces = _subtract(pieces, h["z"])
                    for k, pc in enumerate(pieces):
                        out.add(Segment("x", it.at, pc, it.role, f"{it.name}#{k}", it.mesh_size))
        if self.enclosure is not None:
            e = self.enclosure
            faces = {f: c for f, c in e.faces.items() if f[0] in "xz"}
            out.enclosure = Enclosure({"x": e.spans["x"], "z": e.spans["z"]}, e.boundary, faces, e.material)
        out.set_symmetry(mirror_x=self.mirror_x, pair=self.pair)
        return out

    def summary(self) -> str:
        """A plain-text table of the items, for logs and for checking a layout by eye."""
        lines = [f"Layout {self.name!r}, {self.dim}-D, {len(self.items)} items; "
                 f"mirror_x={self.mirror_x} mirror_y={self.mirror_y}"]
        for k, it in enumerate(self.items):
            r = it.role
            if isinstance(r, Dielectric):
                rs = f"dielectric {r.name} eps_r={r.eps_r:g}"
            elif isinstance(r, Conductor):
                rs = f"conductor net={r.net}" + (" (floating)" if r.floating else "")
            else:
                rs = f"film {r.lo}->{r.hi}"
            ext = ", ".join(f"{a}=[{u:.4g},{v:.4g}]" for a, (u, v) in self.item_extent(it).items())
            lines.append(f"  {k:3d} {type(it).__name__:7s} {it.name:18s} {rs:34s} {ext}")
        if self.enclosure:
            e = self.enclosure
            ext = ", ".join(f"{a}=[{u:.4g},{v:.4g}]" for a, (u, v) in e.spans.items())
            lines.append(f"  enclosure {ext}; boundary {e.boundary} {e.faces or ''}")
        return "\n".join(lines)


def _subtract(pieces: list[Interval], hole: Interval) -> list[Interval]:
    """Remove the interval ``hole`` from a list of disjoint intervals."""
    out = []
    for a, b in pieces:
        if hole[1] <= a or hole[0] >= b:
            out.append((a, b))
            continue
        if hole[0] > a:
            out.append((a, hole[0]))
        if hole[1] < b:
            out.append((hole[1], b))
    return out
