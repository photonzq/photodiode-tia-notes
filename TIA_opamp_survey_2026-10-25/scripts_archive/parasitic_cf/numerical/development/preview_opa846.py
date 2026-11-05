"""Draw the three OPA846 layouts (0402 and 0603) from the study script's builder, to check them by eye."""
import sys
from pathlib import Path

NUM = Path(__file__).resolve().parents[1]          # the numerical/ folder
sys.path.insert(0, str(NUM))
import matplotlib.pyplot as plt          # noqa: E402
import g_opa846_3d as g                   # noqa: E402
from pcbcap import plotting as pl         # noqa: E402

pl.use_style()
out = Path(sys.argv[1])
for size in ("0402", "0603"):
    fig, axs = plt.subplots(1, 3, figsize=(9.5, 3.6), constrained_layout=True)
    for ax, layout in zip(axs, g.LAYOUTS):
        lay = g.opa846_layout(layout, size)
        pl.draw_top(ax, lay, ((-3.2, 3.2), (-3.2, 3.2)))
        ax.set_title(f"{layout} {size}", loc="left")
    fig.savefig(out / f"opa846_top_{size}.png", dpi=150)
    plt.close(fig)
fig = plt.figure(figsize=(9.5, 3.6), constrained_layout=True)
for k, layout in enumerate(g.LAYOUTS):
    ax = fig.add_subplot(1, 3, k + 1, projection="3d")
    pl.draw_iso(ax, g.opa846_layout(layout, "0402"), ((-2.8, 2.8), (-2.8, 2.8), (-2.2, 1.3)))
    ax.set_title(layout, loc="left")
fig.savefig(out / "opa846_iso_0402.png", dpi=150)
print("written")
