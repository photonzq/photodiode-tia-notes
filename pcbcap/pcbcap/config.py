"""Building and running a resistor-on-board study from a TOML file.

Why this module exists
----------------------
Most questions about a layout ("how much worse is an 0805?", "what does a Rogers board change?",
"what if the plane is 0.2 mm below?") change a few numbers of the same construction.  A TOML file
states those numbers; this module turns it into a layout with the builders of ``parts.py``, runs the
convergence and enclosure studies of ``study.py``, and writes the results and figures.  Every key
is optional except the resistor and pad sizes; an omitted key takes the builder's documented
default.

Schema (all lengths in mm)
--------------------------
    name = "0402 on FR-4"
    [resistor]   size = "0402"  corner = "nominal"   # or L, W, T, a explicitly
                 t_term = 0.015  side_wraps = false  film = "up"  film_width = 0.5
                 body = "alumina"                     # or body_eps_r = 9.9
    [pads]       size = "0402"                        # or w, l, s explicitly
                 t_cu = 0.035
    [board]      thickness = 1.6  material = "FR4"    # or eps_r = 3.66
                 [[board.planes]]  depth = 0.2  cutout = { x = [-1.5, 1.5], y = [-1.0, 1.0] }
                 [board.mask]      thickness = 0.02  clearance = 0.05
    [mount]      standoff = 0.03  fillet_height = 0.0
    [enclosure]  half = 8.0  boundary = "ground"  extrapolate = true
    [mesh]       order = 2  refine = [4.0, 2.83, 2.0]  # three levels: Richardson; one level: single solve
    [output]     dir = "results/0402_fr4"  figures = true

Defaults, and why.  enclosure.half = 8 mm, four times the length of the largest part studied (an
0805, 2 mm), the base enclosure of the companion note's studies; the enclosure extrapolation then
adds 16 and 32 mm (study.enclosure_correction).  mesh.refine = [4.0, 2.83, 2.0], steps of sqrt(2)
from the coarsest level used in the companion note's studies; with the 3-D default edge size
(thinnest feature / 4) refine 4 is exactly the level at which the edge size reaches the thinnest
feature, so no level is capped.  study.converge refuses levels that would be capped
(study.check_levels).  These are choices; a study of another layout may need others.
"""
from __future__ import annotations

import json
import tomllib
from dataclasses import replace
from pathlib import Path

from . import materials as mat
from . import parts, study
from .meshing import MeshParams


def load(path: str | Path) -> dict:
    with open(path, "rb") as fh:
        return tomllib.load(fh)


def build_layout(cfg: dict, enclosure_half: float | None = None):
    """The layout described by ``cfg`` (a parsed TOML dict)."""
    r = dict(cfg.get("resistor", {}))
    if "size" in r:
        size = r.pop("size")
        corner = r.pop("corner", "nominal")
        body_eps = r.pop("body_eps_r", None)
        res = parts.ChipResistor.from_size(size, corner, **r)
    else:
        body_eps = r.pop("body_eps_r", None)
        res = parts.ChipResistor(**r)
    if body_eps is not None:
        res = replace(res, body=mat.custom(f"body eps {body_eps:g}", body_eps))
    p = dict(cfg.get("pads", {}))
    pads = parts.LandPattern.from_size(p.pop("size"), **p) if "size" in p else parts.LandPattern(**p)
    b = dict(cfg.get("board", {}))
    planes = [parts.Plane(depth=pl["depth"], cutout=_spans(pl.get("cutout")), net=pl.get("net", "gnd"))
              for pl in b.pop("planes", [])]
    mask = b.pop("mask", None)
    eps = b.pop("eps_r", None)
    if eps is not None:
        b["material"] = mat.custom(f"board eps {eps:g}", eps)
    board = parts.Board(planes=planes, mask=parts.SolderMask(**mask) if mask else None, **b)
    mount = parts.Mount(**cfg.get("mount", {}))
    enc = cfg.get("enclosure", {})
    half = enclosure_half if enclosure_half is not None else enc.get("half", 8.0)
    return parts.resistor_on_pads(res, pads, board, mount, enclosure_half=half,
                                  boundary=enc.get("boundary", "ground"), name=cfg.get("name", ""))


def _spans(d):
    if d is None:
        return None
    return {k: tuple(v) for k, v in d.items()}


def run(cfg: dict, out_dir: str | Path | None = None, log=print) -> dict:
    """Convergence study, optional enclosure extrapolation, results file and figures."""
    out = Path(out_dir or cfg.get("output", {}).get("dir", "pcbcap_results"))
    out.mkdir(parents=True, exist_ok=True)
    mesh_cfg = dict(cfg.get("mesh", {}))
    order = mesh_cfg.pop("order", 2)
    levels = mesh_cfg.pop("refine", [4.0, 2.83, 2.0])
    params = MeshParams(**mesh_cfg)
    lay = build_layout(cfg)
    (out / "layout.txt").write_text(lay.summary() + "\n", encoding="utf-8", newline="\n")
    log(f"{cfg.get('name', '')}: convergence over refine = {levels}")
    conv = study.converge(lay, factors=tuple(levels), params=params, order=order, keep_fields=True, log=log) \
        if len(levels) == 3 else None
    if conv is None:
        single = study.solve_layout(lay, replace(params, refine=levels[0]), order, keep_fields=True)
        result = dict(C_F=dict(finest=single.C_F), C_A0=dict(finest=single.C_A0), contributions=single.contributions)
        last = single
    else:
        result = conv.to_dict()
        last = conv.last
    enc = cfg.get("enclosure", {})
    if enc.get("extrapolate", True) and enc.get("boundary", "ground") == "ground":
        half = enc.get("half", 8.0)
        corr = study.enclosure_correction(lambda m: build_layout(cfg, enclosure_half=m),
                                          margins=(half, 2 * half, 4 * half),
                                          params=replace(params, refine=max(levels)), order=order, log=log)
        result["enclosure"] = corr
        best = conv.value() if conv else result["C_F"]["finest"]
        result["C_F_free_space"] = best + corr["dC_F"]
    (out / "result.json").write_text(json.dumps(result, indent=1, default=float), encoding="utf-8", newline="\n")
    log(f"  results written to {out / 'result.json'}")
    if cfg.get("output", {}).get("figures", True):
        figures(lay, last, out, cfg, order, params, levels)
    return result


def figures(lay, res, out: Path, cfg: dict, order, params, levels) -> None:
    """Layout views, and field maps of the finest level: the odd potential and the density of C_F
    (plotting.coupling_map).  No convergence plot is drawn here; result.json holds the levels."""
    import matplotlib.pyplot as plt
    from . import plotting as pl

    pl.use_style()
    bb = lay.core_bounding_box()
    pad = 0.3
    win_xy = ((bb["x"][0] - pad, bb["x"][1] + pad), (bb["y"][0] - pad, bb["y"][1] + pad))
    win_xz = ((bb["x"][0] - pad, bb["x"][1] + pad), (-0.4, bb["z"][1] + 0.3))
    fig, axs = plt.subplots(1, 2, figsize=(6.5, 2.6), constrained_layout=True)
    pl.draw_top(axs[0], lay, win_xy)
    pl.draw_section(axs[1], lay, win_xz)
    pl.export(fig, out / "layout")
    fig = plt.figure(figsize=(4.2, 3.24), constrained_layout=True)
    ax = fig.add_subplot(projection="3d")
    pl.draw_iso(ax, lay, (win_xy[0], win_xy[1], (-0.3, bb["z"][1] + 0.1)))
    pl.export(fig, out / "layout_iso")
    # The field maps need the Problem, which converge() does not keep, so the finest level is solved
    # again.  That is the most expensive solve of the study (for the 0402 example about a third of the
    # study's time); it is the price of not holding the largest mesh in memory during the study.
    r2, prob = study.solve_layout(lay, replace(params, refine=levels[-1]), order, keep_fields=True,
                                  return_problem=True)
    if prob.md.dim == 3 and not prob.md.clipped.get("y", False):
        return
    phi_o, phi_e = r2.fields.get("phi_odd"), r2.fields.get("phi_even")
    if phi_o is None:
        return
    fig, ax = plt.subplots(figsize=(6.5, 2.6), constrained_layout=True)
    pl.field_map(ax, prob, phi_o, "potential", parity="odd", window=win_xz)
    pl.export(fig, out / "field_potential")
    fig, ax = plt.subplots(figsize=(6.5, 2.6), constrained_layout=True)
    pl.coupling_map(ax, prob, phi_o, phi_e, window=win_xz)
    pl.export(fig, out / "field_coupling")
