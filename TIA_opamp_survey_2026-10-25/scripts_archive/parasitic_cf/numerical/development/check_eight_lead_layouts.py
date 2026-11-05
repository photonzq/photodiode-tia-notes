"""Checks of the eight-lead layouts of g_eight_lead_3d.py, before anything is meshed.

Run:  python check_eight_lead_layouts.py

For each layout it prints, one check per line, the value found and what it should be:
  * the number of connected pieces of metal of every net (inspect_layouts.net_pieces): one for nets A
    and B and for each unconnected pin; ground may come in several pieces, which are all at 0 V;
  * that every net expected is present, and which nets are floating;
and, for the two package models,
  * SOIC-8: how far the foot reaches into its pad and how much shoulder shows outside the body;
  * PDIP-8: how far each lead protrudes below the bottom pad, and the clearance between the lead's
    diagonal and the hole.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[5] / "pcbcap"))
sys.path.insert(0, str(HERE.parents[1]))

import matplotlib                       # noqa: E402
matplotlib.use("Agg")

from pcbcap import packages as pk       # noqa: E402

import g_eight_lead_3d as g8            # noqa: E402
import inspect_layouts as insp          # noqa: E402


def main() -> None:
    expected = {"ada4530_so8_1206": {"A", "B", "gnd", "nc3"}, "lmp7721_so8_1206": {"A", "B", "gnd", "nc5"}}
    for name in g8.LAYOUTS:
        lay = g8.build(name)
        pieces = insp.net_pieces(lay)
        nets = lay.nets()
        coarse = sum(1 for it in lay.items if getattr(it, "mesh_size", None) is not None)
        print(f"{name}: {len(lay.items)} items, {coarse} with their own edge size")
        for net in sorted(pieces):
            n = len(pieces[net])
            want = "any" if net == "gnd" else 1
            ok = net == "gnd" or n == 1
            print(f"  net {net:4s} floating {str(nets.get(net)):5s}: {n} piece(s), expected {want}: {'ok' if ok else 'CHECK'}")
        exp = expected.get(name, {"A", "B", "gnd", "nc1", "nc5", "nc8"})
        print(f"  nets present {sorted(nets)}; expected {sorted(exp)}: {'ok' if set(nets) == exp else 'CHECK'}")
        # the film's potential runs from the input net (lo) to the output net (hi)
        films = [it for it in lay.items if it.role.__class__.__name__ == "Film"]
        for f in films:
            p = f.role.profile
            print(f"  film {f.name}: hi {f.role.hi}, lo {f.role.lo}, along {p.axis} from {p.start:+.3f} to {p.end:+.3f}")
    s = pk.Soic8()
    pad_outer = s.pad_row / 2 + s.pad_length / 2
    tip = s.lead_span / 2
    shoulder_out = (s.lead_span - s.body_width) / 2 - s.foot_length - s.lead_thickness
    print(f"SOIC-8: lead tip at {tip:.4f} mm, pad outer end at {pad_outer:.4f} mm, tip inside the pad by "
          f"{pad_outer - tip:.4f} mm (should be > 0); shoulder outside the body {shoulder_out:.4f} mm (>= 0)")
    d = pk.Dip8()
    protrusion = d.lead_below - 0.035 - 1.6 - 0.035      # below the bottom pad: lead_below - t_cu - H - t_cu
    diag = math.hypot(d.lead_width, d.lead_thickness)
    diag_max = math.hypot(0.53, 0.25)
    print(f"PDIP-8: lead protrudes {protrusion:.4f} mm below the bottom pad (3.18 - 1.6 - 2 x 0.035 = 1.51); "
          f"lead diagonal {diag:.4f} mm nominal, {diag_max:.4f} mm at the widest, hole {d.drill} mm: "
          f"clearance {d.drill - diag_max:.4f} mm (> 0); square pad side {d.pad_side:.4f} mm "
          f"(1.6 x sqrt(pi)/2 = {1.6 * math.sqrt(math.pi) / 2:.4f}); filled-hole side "
          f"{pk.SQUARE_FOR_ROUND * d.drill:.4f} mm (0.84721 x 0.8 = {0.84721 * 0.8:.4f})")


if __name__ == "__main__":
    main()
