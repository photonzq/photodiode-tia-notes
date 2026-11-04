"""Dump the vector paths and the text spans of one PDF page (optionally inside a clip
rectangle) to a JSON file, so that plotted curves drawn as vector graphics can be read
numerically instead of by eye.

Usage
-----
python dump_pdf_vector_paths.py <pdf> <page> <out.json> [--clip x0,y0,x1,y1] [--bezier-steps 8]

* <page> is the 1-based page index as a PDF viewer counts it.
* The clip rectangle is in PDF points (1/72 inch), origin at the top-left of the page,
  y increasing downwards (the PyMuPDF convention).  A pixel coordinate (px, py) read
  off a render made at D dpi converts to points as (px * 72 / D, py * 72 / D).
* Every path is written with its stroke colour, fill colour, line width and the list
  of its vertices.  Cubic Bezier segments are sampled at --bezier-steps points.
* Text spans (for example axis tick labels) are written with their bounding boxes.

Only the geometry is exported; mapping it to data coordinates (axis calibration) and
any fitting are done separately (see fit_shunt_capacitance.py).
"""
import argparse
import json

import pymupdf


def bezier(p0, p1, p2, p3, steps):
    """Sample a cubic Bezier segment (endpoints included)."""
    pts = []
    for k in range(steps + 1):
        t = k / steps
        a = (1 - t) ** 3
        b = 3 * (1 - t) ** 2 * t
        c = 3 * (1 - t) * t ** 2
        d = t ** 3
        pts.append((a * p0.x + b * p1.x + c * p2.x + d * p3.x,
                    a * p0.y + b * p1.y + c * p2.y + d * p3.y))
    return pts


def path_points(path, steps):
    """Return the vertices of a PyMuPDF drawing as a list of (x, y) tuples."""
    pts = []
    for item in path["items"]:
        kind = item[0]
        if kind == "l":
            seg = [(item[1].x, item[1].y), (item[2].x, item[2].y)]
        elif kind == "c":
            seg = bezier(item[1], item[2], item[3], item[4], steps)
        elif kind == "re":
            r = item[1]
            seg = [(r.x0, r.y0), (r.x1, r.y0), (r.x1, r.y1), (r.x0, r.y1), (r.x0, r.y0)]
        elif kind == "qu":
            q = item[1]
            seg = [(q.ul.x, q.ul.y), (q.ur.x, q.ur.y), (q.lr.x, q.lr.y), (q.ll.x, q.ll.y)]
        else:
            continue
        if pts and seg and abs(pts[-1][0] - seg[0][0]) < 1e-6 and abs(pts[-1][1] - seg[0][1]) < 1e-6:
            seg = seg[1:]
        pts.extend(seg)
    return pts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf")
    parser.add_argument("page", type=int)
    parser.add_argument("out_json")
    parser.add_argument("--clip", default="")
    parser.add_argument("--bezier-steps", type=int, default=8)
    args = parser.parse_args()

    doc = pymupdf.open(args.pdf)
    page = doc[args.page - 1]
    clip = None
    if args.clip:
        clip = pymupdf.Rect(*(float(v) for v in args.clip.split(",")))

    paths = []
    for path in page.get_drawings():
        rect = path["rect"]
        if clip is not None and not rect.intersects(clip):
            continue
        paths.append({
            "stroke": [round(c, 4) for c in (path.get("color") or [])],
            "fill": [round(c, 4) for c in (path.get("fill") or [])],
            "width": path.get("width"),
            "rect": [rect.x0, rect.y0, rect.x1, rect.y1],
            "points": [[round(x, 3), round(y, 3)] for x, y in path_points(path, args.bezier_steps)],
        })

    spans = []
    for block in page.get_text("dict", clip=clip)["blocks"]:
        for line in block.get("lines", []):
            for span in line["spans"]:
                text = span["text"].strip()
                if text:
                    spans.append({"text": text, "bbox": [round(v, 3) for v in span["bbox"]]})

    with open(args.out_json, "w", encoding="utf-8") as fh:
        json.dump({"pdf": args.pdf, "page": args.page, "clip": args.clip,
                   "paths": paths, "spans": spans}, fh, indent=1)
    print(f"{len(paths)} paths, {len(spans)} text spans -> {args.out_json}")


if __name__ == "__main__":
    main()
