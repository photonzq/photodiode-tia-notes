"""Render a clipped figure at high dpi and overlay calibrated guide lines.

usage: python -I guides.py <pdf> <page1based> <out.png> <dpi> <clip x0,y0,x1,y1>
         <xcal xa,fa,xb,fb,log|lin> <ycal ya,va,yb,vb,log|lin>
         <xmarks f1,f2,...> [<ymarks v1,v2,...>]
Coordinates in PDF points.  xcal maps PDF x -> axis value; ycal maps PDF y -> axis value.
Vertical guides (red) at xmarks, horizontal guides (blue, dashed look) at ymarks.
"""
import sys, math
import pymupdf

pdf, pno, out, dpi = sys.argv[1], int(sys.argv[2]), sys.argv[3], int(sys.argv[4])
clip = pymupdf.Rect(*map(float, sys.argv[5].split(",")))
xa, fa, xb, fb, xmode = sys.argv[6].split(",")
ya, va, yb, vb, ymode = sys.argv[7].split(",")
xa, fa, xb, fb = map(float, (xa, fa, xb, fb))
ya, va, yb, vb = map(float, (ya, va, yb, vb))
xmarks = [float(v) for v in sys.argv[8].split(",")] if len(sys.argv) > 8 and sys.argv[8] else []
ymarks = [float(v) for v in sys.argv[9].split(",")] if len(sys.argv) > 9 and sys.argv[9] else []


def tr(v, mode):
    return math.log10(v) if mode == "log" else v


def x_of(f):
    return xa + (tr(f, xmode) - tr(fa, xmode)) / (tr(fb, xmode) - tr(fa, xmode)) * (xb - xa)


def y_of(v):
    return ya + (tr(v, ymode) - tr(va, ymode)) / (tr(vb, ymode) - tr(va, ymode)) * (yb - ya)


d = pymupdf.open(pdf)
pg = d[pno - 1]
shape = pg.new_shape()
for f in xmarks:
    x = x_of(f)
    shape.draw_line((x, clip.y0), (x, clip.y1))
    shape.finish(color=(1, 0, 0), width=0.25)
for v in ymarks:
    y = y_of(v)
    shape.draw_line((clip.x0, y), (clip.x1, y))
    shape.finish(color=(0, 0, 1), width=0.2, dashes="[1 1] 0")
shape.commit()
pg.get_pixmap(dpi=dpi, clip=clip).save(out)
print("saved", out)
for f in xmarks:
    print("xmark", f, "at x =", round(x_of(f), 2))
for v in ymarks:
    print("ymark", v, "at y =", round(y_of(v), 2))
