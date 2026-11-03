"""Shared drawing style for the schematics of the photodiode-TIA notes.

Every schematic is drawn with schemdraw on one scale (INCHES_PER_UNIT) and saved on a
canvas of one width (CANVAS_IN) with a white background.  A document that scales its
figures to the text width therefore shows every schematic at the same scale, with the
same line width and the same label size.  Labels are Arial at FONT_SIZE with Computer
Modern for mathematics.  Real parts are drawn in black, parasitic elements in grey,
light in red, guards and shields in green, and optional parts dashed.

All coordinates are in drawing units; a resistor's zig-zag is 1 unit long.

Import this module, call configure() once, build a Sheet, and call Sheet.save(stem).
"""
from __future__ import annotations

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.transforms import Bbox  # noqa: E402
import schemdraw  # noqa: E402
import schemdraw.elements as elm  # noqa: E402
from schemdraw.segments import Segment, SegmentPoly  # noqa: E402

FONT_SIZE = 8.0
LW = 1.0                  # line width of every wire and symbol, points
INCHES_PER_UNIT = 0.30    # drawing scale shared by all schematics
CANVAS_IN = 6.5           # width of every saved schematic, inches
DOT_R = 0.075             # junction dot radius, units
LABEL_GAP = 0.42          # distance from a component's axis to its label, units
OPAMP_SCALE = 0.72
BJT_SCALE = 0.72
GND_SCALE = 0.85

COLORS = {
    "primary": "#385C9E", "neutral": "#4D4D4D", "warm_accent": "#9E403D",
    "cool_accent": "#477A57", "purple_accent": "#6B5B95", "teal_accent": "#3F7F82",
    "annotation": "#767676", "text": "#272727", "axes": "#000000",
}
INK = COLORS["axes"]                 # real parts and wires
PARASITIC = COLORS["annotation"]     # parasitic capacitances
LIGHT = COLORS["warm_accent"]        # light and optical paths
GUARD = COLORS["cool_accent"]        # guards and shields
CURRENT = COLORS["primary"]          # current arrows
OPTIONAL = COLORS["neutral"]         # optional parts (drawn dashed)
NOISE = COLORS["purple_accent"]      # noise sources
DASH = "--"


def configure() -> None:
    """Fonts and PDF text settings, and schemdraw's defaults."""
    plt.rcParams.update({
        "font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans", "sans-serif"],
        "font.size": FONT_SIZE, "text.usetex": False, "mathtext.fontset": "cm",
        "pdf.fonttype": 42, "ps.fonttype": 42, "text.color": COLORS["text"],
        "figure.facecolor": "white", "savefig.facecolor": "white",
    })
    schemdraw.use("matplotlib")
    schemdraw.config(unit=2.0, inches_per_unit=INCHES_PER_UNIT, lblofst=0.12,
                     fontsize=FONT_SIZE, font="Arial", color=INK, lw=LW,
                     bgcolor="white", margin=0.15)


class Bead(elm.Element2Term):
    """Ferrite bead: a filled bar on the wire."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        w, h = 0.55, 0.14
        self.segments.append(Segment([(0, 0), (0, 0), (w, 0)]))
        self.segments.append(SegmentPoly([(0, h), (w, h), (w, -h), (0, -h)], fill=INK))


def _mid(p1, p2):
    return (0.5 * (p1[0] + p2[0]), 0.5 * (p1[1] + p2[1]))


class Sheet:
    """A schematic: thin helpers around one schemdraw Drawing, in absolute coordinates."""

    def __init__(self):
        self.d = schemdraw.Drawing(show=False)

    # ------------------------------------------------------------- primitives --
    def add(self, e):
        return self.d.add(e)

    def wire(self, *pts, color: str | None = None, dashed: bool = False, lw: float | None = None):
        """Straight wire through the given points."""
        for a, b in zip(pts[:-1], pts[1:]):
            e = elm.Line().at(a).to(b)
            if color:
                e = e.color(color)
            if dashed:
                e = e.linestyle(DASH)
            if lw:
                e = e.linewidth(lw)
            self.add(e)

    def dot(self, p, color: str | None = None):
        e = elm.Dot(radius=DOT_R).at(p)
        return self.add(e.color(color) if color else e)

    def terminal(self, p, text: str | None = None, side: str = "right", color: str | None = None):
        """Open circle with an optional label beside it."""
        e = elm.Dot(open=True, radius=0.09).at(p)
        self.add(e.color(color) if color else e)
        if text:
            off = {"right": (0.22, 0.0, "left", "center"), "left": (-0.22, 0.0, "right", "center"),
                   "top": (0.0, 0.22, "center", "bottom"), "bottom": (0.0, -0.22, "center", "top")}[side]
            self.text((p[0] + off[0], p[1] + off[1]), text, ha=off[2], va=off[3], color=color)

    def text(self, p, s: str, ha: str = "left", va: str = "center", color: str | None = None,
             size: float = FONT_SIZE):
        self.add(elm.Label().at(p).label(s, fontsize=size, color=color or COLORS["text"],
                                         halign=ha, valign=va))

    def arrow(self, tail, tip, color: str = CURRENT, width: float = 0.16, length: float = 0.22,
              lw: float | None = None):
        e = elm.Arrow(arrowwidth=width, arrowlength=length).at(tail).to(tip).color(color)
        if lw:
            e = e.linewidth(lw)
        self.add(e)

    # ------------------------------------------------------------- two-terminal --
    def _label(self, p1, p2, text, side, color, gap=LABEL_GAP):
        if not text:
            return
        m = _mid(p1, p2)
        horizontal = abs(p2[0] - p1[0]) >= abs(p2[1] - p1[1])
        if side is None:
            side = "top" if horizontal else "right"
        if side == "top":
            self.text((m[0], m[1] + gap), text, ha="center", va="bottom", color=color)
        elif side == "bottom":
            self.text((m[0], m[1] - gap), text, ha="center", va="top", color=color)
        elif side == "right":
            self.text((m[0] + gap, m[1]), text, ha="left", va="center", color=color)
        else:
            self.text((m[0] - gap, m[1]), text, ha="right", va="center", color=color)

    def _two(self, e, p1, p2, text, side, color, dashed, gap=LABEL_GAP):
        e = e.endpoints(p1, p2)          # .to() is ignored by schemdraw's sources
        if color:
            e = e.color(color)
        if dashed:
            e = e.linestyle(DASH)
        self.add(e)
        self._label(p1, p2, text, side, color, gap)
        return e

    def res(self, p1, p2, text=None, side=None, color=None, dashed=False):
        return self._two(elm.Resistor(), p1, p2, text, side, color, dashed)

    def cap(self, p1, p2, text=None, side=None, color=None, dashed=False):
        return self._two(elm.Capacitor(), p1, p2, text, side, color, dashed)

    def ind(self, p1, p2, text=None, side=None, color=None, dashed=False):
        return self._two(elm.Inductor2(loops=3), p1, p2, text, side, color, dashed)

    def bead(self, p1, p2, text=None, side=None, color=None):
        return self._two(Bead(), p1, p2, text, side, color, False)

    def diode(self, p_anode, p_cathode, text=None, side=None, color=None):
        return self._two(elm.Diode(), p_anode, p_cathode, text, side, color, False)

    def isource(self, p1, p2, text=None, side=None, color=None, dashed=False):
        """Current source whose arrow points from p1 to p2."""
        return self._two(elm.SourceI(), p1, p2, text, side, color, dashed, gap=0.75)

    def vsource(self, p_minus, p_plus, text=None, side=None, color=None):
        return self._two(elm.SourceV(), p_minus, p_plus, text, side, color, False, gap=0.75)

    def photodiode(self, p_anode, p_cathode, text=None, side=None, light: str = "left"):
        """Diode with two straight light arrows aimed at its body from `light` ('left',
        'right', 'top' or 'bottom'; 'none' draws no arrows)."""
        e = self.diode(p_anode, p_cathode, text, side)
        if light == "none":
            return e
        c = _mid(p_anode, p_cathode)
        vertical = abs(p_cathode[1] - p_anode[1]) > abs(p_cathode[0] - p_anode[0])
        if vertical:
            sx = -1.0 if light == "left" else 1.0
            ang = math.radians(-35.0 if sx < 0 else -145.0)
            target = (c[0] + sx * 0.36, c[1] + 0.02)
        else:
            sy = 1.0 if light == "top" else -1.0
            ang = math.radians(-55.0 if sy > 0 else 55.0)
            target = (c[0] - 0.02, c[1] + sy * 0.36)
        dv = (math.cos(ang), math.sin(ang))
        pv = (-dv[1], dv[0])
        for k in (-0.5, 0.5):
            tip = (target[0] + k * 0.26 * pv[0], target[1] + k * 0.26 * pv[1])
            tail = (tip[0] - 0.62 * dv[0], tip[1] - 0.62 * dv[1])
            self.arrow(tail, tip, color=LIGHT, width=0.13, length=0.17)
        return e

    # ------------------------------------------------------------- one-terminal --
    def ground(self, p, color=None):
        e = elm.Ground().at(p).scale(GND_SCALE)
        self.add(e.color(color) if color else e)

    def supply(self, p, text: str, up: bool = True, color=None, side: str | None = None):
        """Supply or bias terminal: a short lead and a bar, with the label beyond the bar
        or, with side='right' or 'left', beside it."""
        e = (elm.Vdd() if up else elm.Vss()).at(p).scale(0.8)
        self.add(e.color(color) if color else e)
        yb = p[1] + (0.32 if up else -0.32)
        if side == "right":
            self.text((p[0] + 0.3, yb), text, ha="left", va="center", color=color)
        elif side == "left":
            self.text((p[0] - 0.3, yb), text, ha="right", va="center", color=color)
        else:
            y = p[1] + (0.55 if up else -0.55)
            self.text((p[0], y), text, ha="center", va="bottom" if up else "top", color=color)

    # ------------------------------------------------------------- active parts --
    def opamp(self, minus_at, minus_on_top: bool = True, name: str | None = None,
              name_at: str = "inside", scale: float = OPAMP_SCALE, left: bool = False):
        """Op amp with leads, its inverting input at minus_at, facing right (or left).
        Anchors of the returned element: in1 (inverting), in2 (non-inverting), out."""
        e = elm.Opamp(leads=True).scale(scale)
        e = e.left() if left else e.right()
        if minus_on_top == left:      # facing left turns the symbol upside down
            e = e.flip()
        e = self.add(e.anchor("in1").at(minus_at))
        if name:
            cx = 0.5 * (e.in1[0] + e.out[0])
            if name_at == "inside":
                self.text((cx - 0.12, e.out[1]), name, ha="center", va="center")
            elif name_at == "above":
                top = max(e.in1[1], e.in2[1]) + 0.55 * scale
                self.text((cx - 0.2, top + 0.25), name, ha="center", va="bottom")
            else:
                bot = min(e.in1[1], e.in2[1]) - 0.55 * scale
                self.text((cx - 0.2, bot - 0.25), name, ha="center", va="top")
        return e

    def npn(self, base_at, mirror: bool = False, name: str | None = None, side: str = "right",
            angle: float = 0.0):
        """NPN with its base at base_at; angle rotates it counter-clockwise (degrees)."""
        e = elm.BjtNpn(circle=True).theta(angle).scale(BJT_SCALE)
        if mirror:
            e = e.reverse()
        e = self.add(e.anchor("base").at(base_at))
        self._tlabel(e, name, side)
        return e

    def pnp(self, base_at, mirror: bool = False, name: str | None = None, side: str = "right",
            angle: float = 0.0):
        e = elm.BjtPnp(circle=True).theta(angle).scale(BJT_SCALE)
        if mirror:
            e = e.reverse()
        e = self.add(e.anchor("base").at(base_at))
        self._tlabel(e, name, side)
        return e

    def njfet(self, gate_at, mirror: bool = False, name: str | None = None, side: str = "right",
              angle: float = 0.0):
        e = elm.JFetN(circle=True).theta(angle).scale(BJT_SCALE)
        if mirror:
            e = e.reverse()
        e = self.add(e.anchor("gate").at(gate_at))
        self._tlabel(e, name, side)
        return e

    def switch(self, p1, p2, closed: bool = False, text=None, side=None, color=None):
        """Single-pole switch, drawn open or closed."""
        return self._two(elm.Switch(nc=closed), p1, p2, text, side, color, False)

    def led(self, p_anode, p_cathode, text=None, side=None, color=None):
        return self._two(elm.LED(), p_anode, p_cathode, text, side, color, False)

    def _tlabel(self, e, name, side):
        if not name:
            return
        c = e.center
        if side == "right":
            self.text((c[0] + 0.62, c[1]), name, ha="left")
        else:
            self.text((c[0] - 0.62, c[1]), name, ha="right")

    def buffer(self, in_at, left: bool = False, text: str = "×1", h: float = 1.3,
               lead: float = 0.45):
        """Unity-gain buffer: a triangle with one input lead and one output lead.
        Returns the output point."""
        sgn = -1.0 if left else 1.0
        x0, y0 = in_at
        xb = x0 + sgn * lead                 # back edge
        xa = xb + sgn * 0.866 * h            # apex
        self.wire((x0, y0), (xb, y0))
        self.wire((xb, y0 - h / 2), (xb, y0 + h / 2), (xa, y0), (xb, y0 - h / 2))
        out = (xa + sgn * lead, y0)
        self.wire((xa, y0), out)
        if text:
            self.text((xb + sgn * 0.866 * h * 0.36, y0), text, ha="center", va="center")
        return out

    def box(self, x0, y0, x1, y1, text: str | None = None, color=None, dashed=False):
        self.wire((x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0), color=color, dashed=dashed)
        if text:
            self.text((0.5 * (x0 + x1), 0.5 * (y0 + y1)), text, ha="center", va="center", color=color)

    def ring(self, x0, y0, x1, y1, text: str | None = "guard ring", text_at: str = "top"):
        """Guard ring around a node: a dashed green rectangle with its name."""
        self.box(x0, y0, x1, y1, color=GUARD, dashed=True)
        if text:
            vert, _, horiz = text_at.partition("_")
            y, va = (y1 + 0.12, "bottom") if vert == "top" else (y0 - 0.12, "top")
            x, ha = {"": (0.5 * (x0 + x1), "center"), "left": (x0, "left"),
                     "right": (x1, "right")}[horiz]
            self.text((x, y), text, ha=ha, va=va, color=GUARD)

    # ------------------------------------------------------------------- output --
    def save(self, stem: Path, canvas_in: float = CANVAS_IN) -> tuple[float, float]:
        """Write stem.png (600 dpi) and stem.pdf on a white canvas canvas_in wide, with
        the drawing centred.  Returns the drawing's own width and the canvas height,
        both in inches.  Refuses a drawing wider than the canvas."""
        self.d.draw(show=False)
        fig = self.d.fig.getfig()
        fig.patch.set_facecolor("white")
        fig.canvas.draw()
        bb = fig.get_tightbbox(fig.canvas.get_renderer())
        pad = 0.06
        width = bb.width + 2 * pad
        if width > canvas_in + 1e-6:
            raise ValueError(f"{stem.name}: drawing is {width:.2f} in wide, canvas {canvas_in} in")
        cx = 0.5 * (bb.x0 + bb.x1)
        box = Bbox.from_extents(cx - canvas_in / 2, bb.y0 - pad, cx + canvas_in / 2, bb.y1 + pad)
        stem.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(stem.with_suffix(".png"), dpi=600, bbox_inches=box, facecolor="white",
                    transparent=False)
        fig.savefig(stem.with_suffix(".pdf"), bbox_inches=box, facecolor="white", transparent=False)
        plt.close(fig)
        return width, box.height
