"""Where the coupling of the 0402 model sits: C_F split by region, for the text beside Figure 46.

Usage:
    python field_regions.py [--record <json>]

What it computes
----------------
C_F is the integral of eps (|grad phi_o|^2 - |grad phi_e|^2) over the volume, multiplied by the
number of mirror images (Eqs. (G.52) and (G.53) of the note; pcbcap.capacitance, section 2).
pcbcap.capacitance already splits that integral by material (the shares of Section G.14.6).  This
script splits it further by position, using each tetrahedron's centroid, so that the paragraph
describing Figure 46 can give numbers for what the colour map shows:

  alumina between the wraps      the body with |x| below the inner edge of the top wraps
  alumina inside a termination   the rest of the body, enclosed by the cap on three sides
  board under the gap            FR-4 with |x| below the inner edge of the pads and |y| within the
                                 pads' half-width, over the whole thickness of the board
  board elsewhere                the rest of the FR-4
  air under the body             air below the body's lower face, within its footprint
  air elsewhere                  the rest of the air

The model, the mesh (the middle level of the 0402 study, refine 2.83) and the enclosure (8 mm) are
those of Figures 44c and 45 (make_numerical_figures.py, solved_0402), so the regions add up to the
C_F printed there.  The quarter model covers x >= 0, y >= 0; its mirror images have the same
contributions, so every region's sum is multiplied by 4, as C_F is.

It also prints the most negative element density and the sum of all negative contributions, which
show whether any region subtracts from C_F (the density is |grad phi_o|^2 - |grad phi_e|^2, so it
is negative wherever the even drive's field is the stronger).
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / "pcbcap"))           # the package at the repository root
sys.path.insert(0, str(HERE))

from pcbcap import study                                        # noqa: E402
from pcbcap.capacitance import _labels                          # noqa: E402
from pcbcap.plotting import _element_measures, section_triangles  # noqa: E402
import g_resistor_3d as g3                                      # noqa: E402


def item(lay, name):
    return next(it for it in lay.items if it.name == name)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--record", type=Path, default=None)
    args = ap.parse_args()
    study.lower_priority(2)

    lay = g3.layout("0402")
    res, prob = study.solve_layout(lay, replace(g3.BASE, refine=2.83), order=2, keep_fields=True,
                                   return_problem=True)
    phi_o, phi_e = res.fields["phi_odd"], res.fields["phi_even"]
    md = prob.md
    f = 2 ** (int(md.clipped.get("x", False)) + int(md.clipped.get("y", False)))
    per_el = f * (prob.elemental(phi_o, phi_o) - prob.elemental(phi_e, phi_e))   # fF per element
    labels = _labels(prob)
    cen = prob.mesh.p[:, prob.mesh.t].mean(axis=1)                               # (3, M) centroids, mm
    x, y, z = np.abs(cen[0]), np.abs(cen[1]), cen[2]

    body, top_a, pad_a = item(lay, "R-body"), item(lay, "R-topA"), item(lay, "padA")
    x_wrap = min(top_a.x)                     # inner edge of the top wrap of A
    x_pad = min(pad_a.x)                      # inner edge of the pad of A (half the gap)
    y_pad = max(abs(v) for v in pad_a.y)      # half-width of the pads
    z_body = min(body.z)                      # lower face of the body
    x_body, y_body = max(abs(v) for v in body.x), max(abs(v) for v in body.y)
    board_name = item(lay, "board").role.name
    alumina_name = body.role.name
    air_name = lay.enclosure.material.name

    al = labels == alumina_name
    bd = labels == board_name
    ai = labels == air_name
    regions = {
        "alumina between the wraps": al & (x < x_wrap),
        "alumina inside a termination": al & (x >= x_wrap),
        "board under the gap": bd & (x < x_pad) & (y < y_pad),
        "board elsewhere": bd & ~((x < x_pad) & (y < y_pad)),
        "air under the body": ai & (z < z_body) & (x < x_body) & (y < y_body),
        "air elsewhere": ai & ~((z < z_body) & (x < x_body) & (y < y_body)),
    }
    covered = np.zeros_like(al)
    for sel in regions.values():
        covered |= sel
    other = ~covered & (per_el != 0.0)

    total = float(per_el.sum())
    print(f"0402, refine 2.83, enclosure 8 mm: C_F = {res.C_F:.4f} fF (solver), sum of elements {total:.4f} fF")
    print(f"geometry: inner edge of the top wraps x = {x_wrap:.3f} mm, inner edge of the pads x = {x_pad:.3f} mm, "
          f"pad half-width {y_pad:.3f} mm, lower face of the body z = {z_body:.3f} mm")
    out = {}
    pos, negp = per_el > 0, per_el < 0
    print(f"  {'region':30s} {'total':>8s}          {'positive':>9s} {'negative':>9s}  (fF)")
    for name, sel in regions.items():
        v = float(per_el[sel].sum())
        vp, vn = float(per_el[sel & pos].sum()), float(per_el[sel & negp].sum())
        out[name] = dict(total=v, positive=vp, negative=vn)
        print(f"  {name:30s} {v:8.3f} fF {100 * v / total:6.1f} %  {vp:9.3f} {vn:9.3f}")
    print(f"  {'(elements in no region)':30s} {float(per_el[other].sum()):8.3f} fF")
    # The negative part by distance from the centre of the part: the even drive's field, of a charged
    # body, falls off more slowly than the odd drive's, of a dipole, so far away it is the stronger.
    r = np.sqrt(cen[0] ** 2 + cen[1] ** 2 + (cen[2] - 0.2) ** 2)
    shells = [(0.0, 0.5), (0.5, 1.0), (1.0, 2.0), (2.0, 4.0), (4.0, np.inf)]
    print("  by distance from (0, 0, 0.2) mm:   total     positive  negative  (fF)")
    out_shells = {}
    for lo, hi in shells:
        sel = (r >= lo) & (r < hi)
        v, vp, vn = (float(per_el[sel].sum()), float(per_el[sel & pos].sum()),
                     float(per_el[sel & negp].sum()))
        out_shells[f"{lo}-{hi}"] = dict(total=v, positive=vp, negative=vn)
        print(f"    {lo:3.1f} to {hi:3.1f} mm               {v:8.3f}  {vp:8.3f}  {vn:8.3f}")

    vol = _element_measures(prob)                                               # element volumes, mm^3
    dens = per_el / (f * vol)                                                   # fF mm^-3, as in Figure 46b
    k = int(np.argmin(dens))
    kmax = int(np.argmax(dens))
    neg = float(per_el[per_el < 0].sum())
    print(f"most negative element density {dens[k]:.4g} fF/mm^3 at centroid "
          f"({cen[0, k]:.3f}, {cen[1, k]:.3f}, {cen[2, k]:.3f}) mm in {labels[k]}")
    print(f"largest element density {dens[kmax]:.4g} fF/mm^3 at centroid "
          f"({cen[0, kmax]:.3f}, {cen[1, kmax]:.3f}, {cen[2, kmax]:.3f}) mm in {labels[kmax]}")
    print(f"sum of all negative contributions {neg:.4f} fF ({100 * neg / total:.2f} % of C_F)")

    # What Figure 46b shows: the elements cut by the plane y = 0 inside the figure's window.
    _, _, elem, _ = section_triangles(prob)
    sec = np.unique(elem)
    win = sec[(np.abs(cen[0, sec]) < 0.9) & (cen[2, sec] > -0.3) & (cen[2, sec] < 0.6)]
    print(f"on the plane y = 0 within |x| < 0.9 mm, -0.3 < z < 0.6 mm: {win.size} elements, density from "
          f"{dens[win].min():.4g} to {dens[win].max():.4g} fF/mm^3")

    # The odd potential in the outer half of each termination's interior (Figure 46a): element means.
    phi_mean = prob.basis.interpolate(phi_o).value.mean(axis=1)
    inner = al & (x > x_wrap + 0.5 * (x_body - x_wrap))
    print(f"odd potential in the alumina with {x_wrap + 0.5 * (x_body - x_wrap):.3f} < x < {x_body:.3f} mm: "
          f"{phi_mean[inner].min():.4f} to {phi_mean[inner].max():.4f} V (termination at 0.5 V)")
    if args.record:
        rec = dict(C_F=res.C_F, regions=out, by_distance=out_shells, negative_sum=neg,
                   most_negative_density=float(dens[k]), most_negative_at=[float(v) for v in cen[:, k]],
                   largest_density=float(dens[kmax]), largest_at=[float(v) for v in cen[:, kmax]],
                   largest_in=str(labels[kmax]),
                   section_window_density=[float(dens[win].min()), float(dens[win].max())],
                   odd_potential_outer_half_of_termination=[float(phi_mean[inner].min()),
                                                            float(phi_mean[inner].max())],
                   geometry=dict(x_wrap=x_wrap, x_pad=x_pad, y_pad=y_pad, z_body=z_body, x_body=x_body))
        args.record.write_text(json.dumps(rec, indent=2), encoding="utf-8")
        print(f"recorded in {args.record.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
