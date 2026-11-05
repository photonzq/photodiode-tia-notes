"""Three-dimensional field solutions of chip resistors on their pads (Appendix G, numerical section).

Usage:
    python g_resistor_3d.py list
    python g_resistor_3d.py run <case> [--record <json>]

Why this script exists
----------------------
Appendix G estimates the capacitance across the feedback resistor from two-dimensional cross-sections
multiplied by widths, which leaves out the field around the ends and the sides of the part
(approximation 1), the thickness of pads and terminations, the solder and the stand-off.  Each case
here solves the full three-dimensional layout built by pcbcap.parts, with
  * a mesh-convergence study (three meshes, Richardson extrapolation; pcbcap.study), and
  * an enclosure study (three enclosure sizes; the field of a layout without its own ground reaches
    the enclosure walls, and the result is extrapolated to an infinitely distant enclosure),
and compares the result with the closed-form estimate of cf_parasitic_estimate.py for the same
dimensions and permittivities.

Every case runs at below-normal priority with two threads.  The finest quarter-domain meshes of the
size studies have up to about 0.34 million elements (0402 at refine 2); the full-domain OPA855
network has about 0.6 million elements (0.83-0.85 million P2 unknowns).  Memory was measured only for
the OPA846 cases (3.5-4.5 GB per solve at about 1 million elements).

Common inputs:
  * assumptions, varied in details_0402: stand-off 30 um, copper 35 um, termination metal 15 um, no
    side wraps, no fillets, no solder mask, film on top ("up");
  * published values within the ranges of the companion note's Table G.3 (pcbcap.materials):
    FR-4 eps_r 4.2 (Isola 370HR, 4.24 at 100 MHz and 4.17 at 1 GHz), alumina eps_r 9.7 (CoorsTek
    AD-995 at 1 MHz), and the mould compound of the OPA855 package 3.55, the midpoint of 3.1-4.0;
  * board 1.6 mm, no planes, as the OPA855 datasheet (SBOS622D p. 29) asks under the feedback network.
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
sys.path.insert(0, str(HERE.parents[1]))

import cf_parasitic_estimate as ana                     # noqa: E402
from pcbcap import materials as mat                     # noqa: E402
from pcbcap import parts, study                         # noqa: E402
from pcbcap.meshing import MeshParams                   # noqa: E402

EPS_PCB, EPS_AL = 4.2, 9.7
# Sizes at refine 1; every run scales them by its refine factor.  h_edge = 15 um / 4, so that refine 4
# reaches the 15-um cap exactly (pcbcap.meshing: the edge size is capped at the thinnest feature, the
# termination metal).  h_core = 0.045 mm is a choice, 0.18 mm at refine 4: it keeps the finest 0402
# mesh near 0.34 million elements; it scales with refine, so its effect is part of the extrapolation.
# The far size (enclosure extent / 12) and the grading 0.3 are pcbcap's defaults (pcbcap.meshing).
BASE = MeshParams(h_edge=0.00375, h_core=0.045)
# Refinement levels, coarse to fine.  No level is coarser than 4 at the edges (study.check_levels).
# 0201 and 0402 step by sqrt(2) (2.83/2 = 1.415).  0603 and 0805 stop at 2.83 to keep the finest
# quarter mesh affordable, so their steps are 1.19 (4/3.36 and 3.36/2.83).  Small steps amplify
# mesh-to-mesh scatter in the extrapolation: the observed orders and the effect of forcing the
# expected order instead are reported with the results (Section G.14 of the note).
LEVELS = {"0201": (4.0, 2.83, 2.0), "0402": (4.0, 2.83, 2.0),
          "0603": (4.0, 3.36, 2.83), "0805": (4.0, 3.36, 2.83)}
# Enclosure margins: 8 mm, four times the length of the largest part (an 0805, 2 mm), then 16 and
# 32 mm for the extrapolation in 1/R (pcbcap.study.enclosure_correction).  Choices.
ENCLOSURE = (8.0, 16.0, 32.0)

CASES: dict[str, tuple[str, object]] = {}


def case(name, title):
    def deco(fn):
        CASES[name] = (title, fn)
        return fn
    return deco


def layout(size: str, eps_pcb=EPS_PCB, eps_al=EPS_AL, half=ENCLOSURE[0], film="up", mount=None, board=None,
           res_kw=None, pads_kw=None):
    res = parts.ChipResistor.from_size(size, film=film, body=mat.custom("alumina", eps_al), **(res_kw or {}))
    pads = parts.LandPattern.from_size(size, **(pads_kw or {}))
    board = board or parts.Board(material=mat.custom("FR4", eps_pcb))
    return parts.resistor_on_pads(res, pads, board, mount or parts.Mount(), enclosure_half=half,
                                  name=f"{size} on eps {eps_pcb:g}")


def analytic_at(size: str, eps_pcb=EPS_PCB, eps_al=EPS_AL, film="up") -> dict:
    """Appendix G's estimate for the same size with the permittivities fixed at the given values
    (so that the bracket shows only the modelling bounds, not the permittivity spread)."""
    saved = ana.EPS_PCB, ana.EPS_AL
    try:
        ana.EPS_PCB, ana.EPS_AL = (eps_pcb, eps_pcb), (eps_al, eps_al)
        r = ana.resistor_on_pads(size, film, "nominal")
    finally:
        ana.EPS_PCB, ana.EPS_AL = saved
    return dict(lower_bound=r["lower_bound_2d"], central=r["central"], upper_estimate=r["upper_estimate"],
                board=r["board"], block=r["block"], air=r["air"])


def full_study(size: str, **kw) -> dict:
    """Convergence at three meshes, enclosure extrapolation at the coarsest mesh, comparison.

    The result C_F_best is the value with no ground nearby: the mesh-extrapolated value at the 8-mm
    enclosure plus the enclosure correction dC_F found on the coarsest mesh.  Adding the two is
    justified in pcbcap.study (module docstring, "How the correction is combined with a mesh study"):
    the correction's own mesh error is about twice the relative mesh error of the capacitance to
    ground at that level, of the order of 1 % of the correction.  By Rule 6 of the companion note this
    no-ground value is the largest the layout can have; any ground nearby lowers it."""
    lv = LEVELS[size]
    print(f"  mesh convergence, refine levels {lv}:")
    conv = study.converge(layout(size, **kw), factors=lv, params=BASE, order=2)
    print(f"  enclosure sizes {ENCLOSURE} mm at refine {lv[0]}:")
    enc = study.enclosure_correction(lambda m: layout(size, half=m, **kw), margins=ENCLOSURE,
                                     params=replace(BASE, refine=lv[0]), order=2)
    best = conv.value() + enc["dC_F"]
    return dict(convergence=conv.to_dict(), enclosure=enc, C_F_best=best,
                discretisation_error=conv.C_F["error"], enclosure_correction=enc["dC_F"])


def print_comparison(out: dict, an: dict) -> list[str]:
    best = out["C_F_best"]
    lines = [f"C_F (finest mesh, enclosure 8 mm): {out['convergence']['C_F']['finest']:.2f} fF",
             f"C_F extrapolated in the mesh: {out['convergence']['C_F'].get('extrapolated') or float('nan'):.2f} fF "
             f"(observed order {out['convergence']['C_F'].get('order') or float('nan'):.2f}); "
             f"discretisation error estimate {out['discretisation_error']:.2f} fF",
             f"enclosure correction to infinity {out['enclosure_correction']:+.2f} fF "
             f"(observed decay order {out['enclosure'].get('order_C_F') or float('nan'):.2f})",
             f"C_F with no ground nearby (mesh-extrapolated + enclosure correction) = {best:.2f} fF",
             f"Appendix G at the same permittivities: lower bound {an['lower_bound']:.2f}, central {an['central']:.2f}, "
             f"upper estimate {an['upper_estimate']:.2f} fF; the field solution lies at "
             f"{100 * (best - an['lower_bound']) / (an['upper_estimate'] - an['lower_bound']):.0f} % of that bracket",
             "shares at the finest mesh: " + ", ".join(f"{k} {v:.2f}" for k, v in out["convergence"]["contributions"].items())
             + f" fF; Appendix G terms: board {an['board'][0]:.2f}-{an['board'][1]:.2f}, body {an['block'][0]:.2f}-"
             f"{an['block'][1]:.2f}, air {an['air'][0]:.2f}-{an['air'][1]:.2f} fF"]
    return lines


# ================================================================================================
for _size in ("0201", "0402", "0603", "0805"):
    def _make(size=_size):
        def fn():
            out = full_study(size)
            an = analytic_at(size)
            out["analytic"] = an
            out["lines"] = print_comparison(out, an)
            return out
        return fn
    CASES[f"size_{_size}"] = (f"{_size} on FR-4 (eps 4.2), alumina 9.7, film up, planes removed", _make())


@case("eps_corners_0402", "0402 at the permittivity corners of Table G.3 (middle mesh, enclosure 8 mm)")
def _eps_corners():
    """FR-4 3.65/4.6 and alumina 9.4/10.0, solved at the middle mesh of the 0402 study with the
    8-mm enclosure.  The values are raw; the nominal case's mesh and enclosure corrections (size_0402)
    show how far such raw values lie from the converged, free-space ones."""
    lines, out = [], {}
    for name, ep, ea in (("low", 3.65, 9.4), ("nominal", 4.2, 9.7), ("high", 4.6, 10.0)):
        r = study.solve_layout(layout("0402", eps_pcb=ep, eps_al=ea), replace(BASE, refine=2.83), order=2)
        out[name] = dict(eps_pcb=ep, eps_al=ea, C_F=r.C_F, shares=r.contributions)
        lines.append(f"{name:7s}: eps_pcb {ep}, eps_al {ea}: C_F = {r.C_F:.2f} fF (mesh at refine 2.83, enclosure 8 mm)")
    return dict(table=out, lines=lines)


@case("film_down_0402", "0402 mounted upside down (film facing the board), single mesh")
def _film_down():
    lines, out = [], {}
    for film in ("up", "down"):
        r = study.solve_layout(layout("0402", film=film), replace(BASE, refine=2.83), order=2)
        out[film] = dict(C_F=r.C_F, C_A0=r.C_A0, shares=r.contributions)
        lines.append(f"film {film:4s}: C_F = {r.C_F:.2f} fF, C_A0 = {r.C_A0:.2f} fF (refine 2.83, enclosure 8 mm)")
    lines.append(f"difference down - up: {out['down']['C_F'] - out['up']['C_F']:+.2f} fF")
    return dict(table=out, lines=lines)


# Board permittivities, each from its manufacturer's document as collected, with document, page and
# test frequency, in data/parasitic_cf/substrate_permittivity.md: RT/duroid 5880 2.20 (Rogers
# PUB# 92-101), RO3003 3.00 at 10 GHz (Rogers PUB# 92-130), I-Tera MT40 3.45 for 2-10 GHz (Isola
# data sheet), RO4350B 3.66, Rogers's design value over 8-40 GHz (PUB# 92-004, p. 3; its 1-GHz chart
# reads about 3.76), MEGTRON 6 3.71 at 1 GHz (Panasonic); FR-4 4.2 and 4.6 are the nominal value and
# upper end of pcbcap.materials; "air" removes the board's dielectric to show the limit.
SUBSTRATES = [("air (board removed)", 1.0), ("RT/duroid 5880", 2.20), ("RO3003", 3.00), ("I-Tera MT40", 3.45),
              ("RO4350B (design)", 3.66), ("MEGTRON 6 (1 GHz)", 3.71), ("FR-4 nominal", 4.2), ("FR-4 high", 4.6)]


def substrate_case(size: str):
    lvl = LEVELS[size][1]

    def fn():
        lines, rows = [], []
        for name, ep in SUBSTRATES:
            r = study.solve_layout(layout(size, eps_pcb=ep), replace(BASE, refine=lvl), order=2)
            rows.append(dict(material=name, eps_pcb=ep, C_F=r.C_F, C_A0=r.C_A0, shares=r.contributions,
                             analytic=analytic_at(size, eps_pcb=ep)))
            lines.append(f"{name:22s} eps {ep:4.2f}: C_F = {r.C_F:6.2f} fF; board share {r.contributions.get('board', 0):5.2f} fF;"
                         f" {r.fem['total_seconds']:.0f} s")
        ref = next(x for x in rows if x["material"] == "FR-4 nominal")["C_F"]
        for x in rows:
            x["relative_to_FR4"] = x["C_F"] / ref
        lines.append("relative to FR-4 (4.2): " + ", ".join(f"{x['eps_pcb']:g}: {x['C_F'] / ref:.3f}" for x in rows))
        return dict(rows=rows, refine=lvl, lines=lines)
    return fn


CASES["substrates_0402"] = ("0402: board permittivity from 1 to 4.6 (single mesh)", substrate_case("0402"))
CASES["substrates_0805"] = ("0805: board permittivity from 1 to 4.6 (single mesh)", substrate_case("0805"))


@case("substrates_enclosure_0402", "0402: enclosure correction for three board permittivities (refine 4)")
def _substrates_enclosure():
    """The substrate cases are computed with the enclosure at 8 mm.  The enclosure correction to an
    infinitely distant ground depends on the board: it grows with the square of the capacitance to
    ground (pcbcap.study), which a board of lower permittivity reduces.  This case computes the
    correction for no board (air), the lowest-permittivity laminate (RT/duroid 5880) and FR-4, so that
    the ratios of Table G.13 can also be given with no ground nearby."""
    lines, out = [], {}
    for name, ep in (("air (board removed)", 1.0), ("RT/duroid 5880", 2.20), ("FR-4 nominal", 4.2)):
        enc = study.enclosure_correction(lambda m, e=ep: layout("0402", eps_pcb=e, half=m), margins=ENCLOSURE,
                                         params=replace(BASE, refine=4.0), order=2)
        out[name] = dict(eps_pcb=ep, dC_F=enc["dC_F"], order=enc.get("order_C_F"), C_F=enc["C_F"],
                         dC_A0=enc["dC_A0"])
        lines.append(f"{name:22s} eps {ep:4.2f}: enclosure correction {enc['dC_F']:+.3f} fF "
                     f"(order {enc.get('order_C_F') or float('nan'):.2f}), dC_A0 {enc['dC_A0']:+.3f} fF")
    return dict(table=out, lines=lines)


@case("details_0402", "0402: effect of each modelling detail (single mesh)")
def _details():
    """One change at a time from the reference model, at the middle mesh of the 0402 study.

    Why these values: the termination metal and the stand-off are assumptions (pcbcap.parts), so each
    is doubled (15 to 30 um) or moved to a lower and an upper plausible value (10 and 50 um around 30);
    side wraps are an option no drawing settles; a fillet of a third of T is a moderate wedge; 18 and
    70 um are the two copper weights next to 35 um (half-ounce and 2-ounce); the mask takes
    pcbcap.parts.SolderMask's defaults (20 um, eps 4.0).  Each variant is meshed afresh at the same
    refine level, so differences smaller than the mesh error at that level (about 0.12 fF, the
    distance of the 0402 reference at refine 2.83 from its extrapolated value) are not resolved."""
    variants = [
        ("reference", {}),
        ("termination metal 30 um", dict(res_kw=dict(t_term=0.03))),
        ("side wraps", dict(res_kw=dict(side_wraps=True))),
        ("stand-off 10 um", dict(mount=parts.Mount(standoff=0.01))),
        ("stand-off 50 um", dict(mount=parts.Mount(standoff=0.05))),
        ("solder fillet 1/3 of T", dict(mount=parts.Mount(fillet_height=1 / 3))),
        ("copper 18 um", dict(pads_kw=dict(t_cu=0.018))),
        ("copper 70 um", dict(pads_kw=dict(t_cu=0.070))),
        ("solder mask 20 um, eps 4.0", dict(board=parts.Board(material=mat.custom("FR4", EPS_PCB),
                                                                 mask=parts.SolderMask()))),
    ]
    lines, out = [], {}
    for name, kw in variants:
        r = study.solve_layout(layout("0402", **kw), replace(BASE, refine=2.83), order=2)
        out[name] = dict(C_F=r.C_F, C_A0=r.C_A0)
        lines.append(f"{name:28s}: C_F = {r.C_F:.2f} fF, C_A0 = {r.C_A0:.2f} fF, {r.fem['total_seconds']:.0f} s")
    ref = out["reference"]["C_F"]
    for name in out:
        out[name]["delta"] = out[name]["C_F"] - ref
    lines.append("change from the reference: " + ", ".join(f"{k}: {v['delta']:+.2f}" for k, v in out.items() if k != "reference"))
    return dict(table=out, lines=lines)


# ================================================================================================
# The layout of Figure 43: an 0402 beside pins 1-4 of the OPA855 (DSG0008A), as in the datasheet's
# layout example.  Figure 43 draws the resistor along its vertical axis with pin 1 (FB) at the top;
# here the drawing is turned by 90 degrees so that the resistor lies along x with net A (pin 1, FB) at
# +x, which is pcbcap's convention.  Figure coordinates (X, Y) map to x = Y - 0.25, y = X + 1.85, so:
#   resistor centre (0, 0); pins 1-4 at x = 0.5, 0.0, -0.5, -1.0; package edge at y = 0.85;
#   board pads of the pins y = 0.65..1.15 (0.2 mm outside the body, 0.3 mm under it);
#   package body x = -1.25..0.75, y = 0.85..2.85; thermal pad x = -1.05..0.55, y = 1.40..2.30.
# Traces of width 0.2 mm (an assumption: the datasheet's example does not dimension them) join each
# resistor pad to its pin, centred on the pin, from the pad's edge (y = 0.3) to the pin pad (y = 0.65).
# Pins 5-8 lie on the far edge, 1.9 mm away, and are left out (pcbcap.parts.WsonPackage gives the sign
# of that omission as unknown).
# Where the resistor sits is an assumption too: Figure 43 is a schematic drawing of the datasheet's
# layout example without dimensions for the resistor's position, which here is centred on pin 2 with
# its pads 0.35 mm from the pin pads.  Figure 43 also draws the resistor's pads 0.50 mm long with a
# 0.50-mm gap; the model uses the Vishay 28950 land pattern of Table G.2 (0.55 mm, gap 0.40 mm), as
# every other case does.
# ================================================================================================
def opa855_layout(half: float = ENCLOSURE[0], with_package: bool = True, plane: bool = False,
                  plane_edge: float = 0.04):
    res = parts.ChipResistor.from_size("0402", body=mat.custom("alumina", EPS_AL))
    pads = parts.LandPattern.from_size("0402")
    planes = []
    if plane:
        # Plane 0.2 mm below the surface, cut out under the feedback network and pins 1-4 with a 0.5-mm
        # margin (the margin is an assumption; the datasheet asks for the cut-out but gives no size).
        # Its cut-out border lies 0.2 mm down and at least 0.5 mm away from the network, so it is meshed
        # with a coarser edge size (plane_edge at refine 1); case opa855_plane_edge checks that choice.
        planes = [parts.Plane(depth=0.2, cutout={"x": (-1.625, 1.25), "y": (-0.8, 1.65)}, mesh_size=plane_edge)]
    board = parts.Board(material=mat.custom("FR4", EPS_PCB), planes=planes)
    lay = parts.resistor_on_pads(res, pads, board, parts.Mount(), enclosure_half=half, symmetric=False,
                                 name="OPA855 feedback network" if with_package else "0402 alone (full domain)")
    if with_package:
        tc = pads.t_cu
        for xc, net in ((0.5, "A"), (-0.5, "B")):
            parts.add_trace(lay, (xc - 0.1, xc + 0.1), (pads.l / 2, 0.65), tc, net, name=f"trace{net}")
        pkg = parts.WsonPackage(edge_y=0.85, x_pins=(0.5, 0.0, -0.5, -1.0), nets=("A", "pin2", "B", "gnd"),
                                floating=(False, True, False, False), body_x=(-1.25, 0.75),
                                thermal_x=(-1.05, 0.55), thermal_y=(0.55, 1.45),
                                mould=mat.custom("mould", 3.55))
        parts.add_wson(lay, pkg, t_cu=tc)
    return lay


@case("opa855_layout", "0402 beside the OPA855 pins as in Figure 43, full domain (no symmetry)")
def _opa855():
    """Same-mesh comparison: the resistor alone and the whole feedback network on identical mesh
    parameters, so that the part of their difference that comes from the resistor's own mesh error
    cancels; two mesh levels show how much each value moves with the core and far sizes.  The
    planes-removed layout (the note's assumption) is then repeated with a cut-out plane 0.2 mm below.

    What the two levels do not test: both have the same, capped, 15-um edge size, and the edge zone
    carries the dominant discretisation error.  Its size is known from size_0402: at refine 4, whose
    edges are also 15 um, the 0402 lies 0.18 fF (0.44 %) above its mesh-extrapolated value.  The
    network values here carry an error of that kind, which this case does not measure.  A full domain
    at a finer edge size was not attempted, for memory."""
    lines, out = [], {"levels": [6.73, 5.66]}
    for lvl in out["levels"]:
        p = replace(BASE, refine=lvl)
        r0 = study.solve_layout(opa855_layout(with_package=False), p, order=2)
        r1 = study.solve_layout(opa855_layout(with_package=True), p, order=2)
        out[f"refine_{lvl}"] = dict(alone=r0.C_F, network=r1.C_F, added=r1.C_F - r0.C_F,
                                    alone_A0=r0.C_A0, network_A0=r1.C_A0, network_B0=r1.C_B0,
                                    shares=r1.contributions, dofs=r1.fem["dofs"])
        lines.append(f"refine {lvl}: resistor alone {r0.C_F:.2f} fF, whole network {r1.C_F:.2f} fF, "
                     f"added by traces, pins and package {r1.C_F - r0.C_F:+.2f} fF; C_B0 (summing node) "
                     f"{r1.C_B0:.1f} fF; {r1.fem['dofs']} unknowns, {r1.fem['total_seconds']:.0f} s")
    p = replace(BASE, refine=5.66)
    rp = study.solve_layout(opa855_layout(with_package=True, plane=True), p, order=2)
    out["plane_cutout"] = dict(network=rp.C_F, A0=rp.C_A0, B0=rp.C_B0, shares=rp.contributions)
    lines.append(f"with a plane 0.2 mm below, cut out 0.5 mm around the network (refine 5.66): C_F = {rp.C_F:.2f} fF, "
                 f"C_B0 = {rp.C_B0:.1f} fF")
    print("  enclosure sizes for the whole network at refine 5.66:")
    enc = study.enclosure_correction(lambda m: opa855_layout(half=m, with_package=True), margins=ENCLOSURE,
                                     params=p, order=2)
    out["enclosure"] = enc
    lines.append(f"enclosure correction to infinity for the whole network {enc['dC_F']:+.2f} fF "
                 f"(observed decay order {enc.get('order_C_F') or float('nan'):.2f})")
    return dict(table=out, lines=lines)


@case("opa855_plane_edge", "Check of the plane's coarser edge size in the OPA855 network (refine 6.73)")
def _opa855_plane_edge():
    """The cut-out border of the plane is meshed with a coarser edge size than the parts.  This case
    halves that size; if C_F moves by much less than the plane's own effect, the choice is adequate.
    It runs at refine 6.73, the coarser of the two levels of opa855_layout, whereas the plane value
    quoted from opa855_layout is at refine 5.66; the plane's edge size scales with refine in both, so
    the check bounds the effect at the coarser level, where it is larger."""
    p = replace(BASE, refine=6.73)
    lines, out = [], {}
    for pe in (0.04, 0.02):
        r = study.solve_layout(opa855_layout(with_package=True, plane=True, plane_edge=pe), p, order=2)
        out[str(pe)] = dict(C_F=r.C_F, B0=r.C_B0, dofs=r.fem["dofs"])
        lines.append(f"plane edge {pe} mm at refine 1 ({pe * 6.73:.3f} mm here): C_F = {r.C_F:.3f} fF, "
                     f"C_B0 = {r.C_B0:.2f} fF, {r.fem['dofs']} unknowns, {r.fem['total_seconds']:.0f} s")
    lines.append(f"change on halving the plane's edge size: {out['0.02']['C_F'] - out['0.04']['C_F']:+.3f} fF")
    return dict(table=out, lines=lines)


# ================================================================================================
def run(name: str, record: str | None) -> dict:
    title, fn = CASES[name]
    print(f"[{name}] {title}")
    t0 = time.perf_counter()
    out = fn()
    out["seconds"] = time.perf_counter() - t0
    out["title"] = title
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
    r = sub.add_parser("run")
    r.add_argument("name")
    r.add_argument("--record", default=None)
    a = ap.parse_args()
    if a.cmd == "list":
        for k, (t, _) in CASES.items():
            print(f"{k:18s} {t}")
        return 0
    run(a.name, a.record)
    return 0


if __name__ == "__main__":
    sys.exit(main())
