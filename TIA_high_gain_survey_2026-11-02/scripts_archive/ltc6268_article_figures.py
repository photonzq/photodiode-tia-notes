"""Render high-resolution crops of figures that are split across pages.

Written for the browser printout of G. Brisebois, "Op Amp Combines Femtoamp
Bias Current with 4GHz Gain Bandwidth Product, Shines New Light on Photonics
Applications" (Analog Devices technical article, 2015), whose Figure 12 (bias
current against common-mode voltage) falls across a page break. The clip
rectangles below fit that printout only.

Usage: python -P ltc6268_article_figures.py <pdf> <outdir>
Page size is US Letter (612 x 792 pt); clip rectangles are in points.
"""
import sys
import pymupdf
from PIL import Image

pdf, outdir = sys.argv[1], sys.argv[2]
doc = pymupdf.open(pdf)
DPI = 400


def clip(page_index, x0, y0, x1, y1, name):
    pix = doc[page_index].get_pixmap(dpi=DPI, clip=pymupdf.Rect(x0, y0, x1, y1))
    path = f"{outdir}/{name}.png"
    pix.save(path)
    return path


# Figure 12: bottom of page 8 + top of page 9 (0-based pages 7 and 8)
a = clip(7, 40, 655, 612, 792, "fig12_top")
b = clip(8, 40, 0, 612, 112, "fig12_bottom")
ia, ib = Image.open(a), Image.open(b)
w = max(ia.width, ib.width)
out = Image.new("RGB", (w, ia.height + ib.height), "white")
out.paste(ia, (0, 0))
out.paste(ib, (0, ia.height))
out.save(f"{outdir}/fig12_full.png")

# Right half only (the bias-current plot), larger
a = clip(7, 360, 655, 612, 792, "fig12p_top")
b = clip(8, 360, 0, 612, 112, "fig12p_bottom")
ia, ib = Image.open(a), Image.open(b)
w = max(ia.width, ib.width)
out = Image.new("RGB", (w, ia.height + ib.height), "white")
out.paste(ia, (0, 0))
out.paste(ib, (0, ia.height))
out.save(f"{outdir}/fig12_plot.png")

# Figure 5 (page 5, 0-based 4)
clip(4, 60, 225, 330, 400, "fig5")
print("done")
