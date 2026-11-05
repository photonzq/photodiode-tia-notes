"""Check that draw_iso draws the same polygons, in the same order and colours, before and after the
face computation was moved out of it into plotting.visible_faces (default view only, which is the
view of the published Figures 44, 50 and 51).

Run:  python check_iso_faces.py <plotting.py before the change>
      (for example the file from the commit before the change, written out with
       git show <commit>:pcbcap/pcbcap/plotting.py > plotting_before.py)

For each layout it prints the number of polygons drawn by each version, the largest difference of
any vertex coordinate (mm) and of any colour component (0-1), and whether they agree exactly.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[5] / "pcbcap"))
sys.path.insert(0, str(HERE.parents[1]))

import matplotlib                                         # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt                           # noqa: E402
import mpl_toolkits.mplot3d.art3d as art3d                # noqa: E402
import numpy as np                                        # noqa: E402

from pcbcap import parts                                  # noqa: E402
from pcbcap import plotting as new                        # noqa: E402

import g_opa846_3d as g846                                # noqa: E402
import g_resistor_3d as g855                              # noqa: E402

captured = []
_Original = art3d.Poly3DCollection


class _Recording(_Original):
    """Poly3DCollection that keeps a copy of the polygons and face colours it is given."""

    def __init__(self, verts, *args, **kwargs):
        captured.append(([np.array(v, dtype=float) for v in verts],
                         np.array(kwargs.get("facecolors"), dtype=float)))
        super().__init__(verts, *args, **kwargs)


def load_old(path: str):
    spec = importlib.util.spec_from_file_location("pcbcap._plotting_before", path)
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = "pcbcap"            # so that its relative imports find pcbcap.geometry
    spec.loader.exec_module(mod)
    return mod


def draw(module, lay, win):
    captured.clear()
    fig = plt.figure()
    ax = fig.add_subplot(projection="3d")
    module.draw_iso(ax, lay, win)
    plt.close(fig)
    return captured[0] if captured else ([], np.zeros((0, 4)))


def main() -> None:
    old = load_old(sys.argv[1])
    art3d.Poly3DCollection = _Recording
    cases = [("0402 on its pads", parts.resistor_on_pads(parts.ChipResistor.from_size("0402"),
                                                         parts.LandPattern.from_size("0402")),
              ((-1.0, 1.0), (-0.6, 0.6), (-0.3, 0.6))),
             ("OPA855 network", g855.opa855_layout(with_package=True, plane=True),
              ((-1.6, 1.4), (-0.8, 2.0), (-0.4, 1.0)))]
    for name in ("double_sided", "under_body", "around"):
        cases.append((f"OPA846 {name}", g846.opa846_layout(name, "0402"), ((-2.8, 2.8), (-2.6, 2.6), (-1.9, 1.4))))
    all_same = True
    for label, lay, win in cases:
        (pa, ca), (pb, cb) = draw(old, lay, win), draw(new, lay, win)
        same_n = len(pa) == len(pb)
        dv = max((float(np.max(np.abs(a - b))) for a, b in zip(pa, pb)), default=0.0) if same_n else float("nan")
        dc = float(np.max(np.abs(ca - cb))) if same_n and ca.shape == cb.shape else float("nan")
        ok = same_n and dv == 0.0 and dc == 0.0
        all_same &= ok
        print(f"{label:22s}: polygons before {len(pa):5d}, after {len(pb):5d}; largest vertex difference "
              f"{dv:.3g} mm, largest colour difference {dc:.3g}; identical: {ok}")
    print(f"all identical: {all_same}")


if __name__ == "__main__":
    main()
