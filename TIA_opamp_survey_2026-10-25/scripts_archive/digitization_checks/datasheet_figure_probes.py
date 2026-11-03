"""The one-off probes run while checking the datasheet-figure readings (2026-10-27), kept so
that each step can be repeated.  They read the PDFs only; nothing is written except the PNGs of
'plain' and 'testcircuit'.

usage: python datasheet_figure_probes.py <probe> [--out-dir <dir>]
  captions     figure captions and the typical-characteristics condition lines, with their
               positions (PDF points), on THS3491 pages 13, 16, 29 and OPA859 page 9
  spans        the integrated_tia/spans.py calls that gave each figure's tick labels and plot
               frame (printed as command lines; run them from scripts_archive/)
  plain        the three THS3491 figures rendered without overlay (zoom 4)
  vertices     Fig 9-4: every vertex of both curves; Fig 8-22: the vector paths read with the
               frame calibration at the frequencies of composite_tia.ZOL_F (the values in
               composite_tia.py), the low-frequency plateau and the end of the phase trace
  colours      stroke colours and widths of the paths inside the Fig 8-1 frame (which curve is
               which gain)
  ec           lines of the THS3491 electrical-characteristics pages (5-12) that mention
               capacitance, input resistance or impedance, transimpedance or noise
  testcircuit  the pages that mention test circuits, and page 27 (Fig 9-1, Table 9-2) rendered
  residuals    the largest residual per series in <out-dir>/residuals.json (overlay_digitized.py)

Paths are relative to the survey folder (two levels above this file).
"""
import argparse
import collections
import json
import math
import sys
from pathlib import Path

import numpy as np
import pymupdf

HERE = Path(__file__).resolve().parent
ARCHIVE = HERE.parent
ROOT = ARCHIVE.parent
sys.path.insert(0, str(ARCHIVE))

THS_PDF = ROOT / "datasheets" / "hv_output_stage" / "THS3491_TI_SBOS875C_2023-02.pdf"
OPA859_PDF = ROOT / "datasheets" / "opa859.pdf"


def captions(_):
    d = pymupdf.open(THS_PDF)
    for pno in (13, 16, 29):
        for b in d[pno - 1].get_text("dict")["blocks"]:
            for ln in b.get("lines", []):
                t = "".join(s["text"] for s in ln["spans"])
                if (t.startswith("Figure") or "Table 9-2" in t or "unless" in t or t.startswith("at T")
                        or t.startswith("At ")):
                    print("THS3491", pno, [round(v, 1) for v in ln["bbox"]], t)
    d = pymupdf.open(OPA859_PDF)
    for i in range(d.page_count):
        for b in d[i].get_text("dict")["blocks"]:
            for ln in b.get("lines", []):
                t = "".join(s["text"] for s in ln["spans"])
                if t.startswith(("Figure 6-9", "Figure 6-10", "Figure 6-11")):
                    print("OPA859", i + 1, [round(v, 1) for v in ln["bbox"]], t)


def spans(_):
    ths = THS_PDF.relative_to(ROOT).as_posix()
    opa = OPA859_PDF.relative_to(ROOT).as_posix()
    for what, pdf, page, clip in (("THS3491 p13 condition lines", ths, 13, "50 80 560 120"),
                                  ("THS3491 Fig 8-22", ths, 16, "300 315 560 512"),
                                  ("THS3491 Fig 9-4", ths, 29, "100 120 520 364"),
                                  ("THS3491 Fig 8-1", ths, 13, "50 118 305 316"),
                                  ("OPA859 Fig 6-10", opa, 9, "300 315 560 503")):
        print(f"# {what}\npython integrated_tia/spans.py ../{pdf} {page} {clip}")


def plain(a):
    a.out_dir.mkdir(parents=True, exist_ok=True)
    d = pymupdf.open(THS_PDF)
    for name, pno, clip in (("fig8-22", 16, (300, 318, 560, 498)), ("fig9-4", 29, (185, 180, 425, 345)),
                            ("fig8-1", 13, (62, 120, 300, 302))):
        pix = d[pno - 1].get_pixmap(matrix=pymupdf.Matrix(4, 4), clip=pymupdf.Rect(*clip))
        pix.save(a.out_dir / f"plain_{name}.png")
        print(name, pix.width, pix.height)


def vertices(_):
    from overlay_digitized import Axis, path_xy, read_path
    import composite_tia as ct
    d = pymupdf.open(THS_PDF)
    pg = d[28]
    fr = (217.5, 186.7, 408.0, 321.7)
    ax, ay = Axis(217.5, 1.0, 408.0, 1000.0, log=True), Axis(321.7, 0.0, 186.7, 30.0)
    for col, lab in (((0, 0, 0), "15V"), ((1, 0, 0), "7.5V")):
        xy = path_xy(pg, fr, col)
        f, v = ax.val(xy[:, 0]), ay.val(xy[:, 1])
        u = []
        for x, y in zip(f, v):
            if not u or abs(np.log10(x) - np.log10(u[-1][0])) > 1e-4 or abs(y - u[-1][1]) > 1e-3:
                u.append((x, y))
        print(lab, len(u), "vertices")
        print("  " + "  ".join(f"({x:.1f},{y:.2f})" for x, y in u))
    pg = d[15]
    fr = (334.0, 326.1, 525.4, 461.1)
    ax = Axis(334.0, 1e2, 525.4, 1e9, log=True)
    ayl, ayr = Axis(461.1, 40.0, 326.1, 140.0), Axis(461.1, -150.0, 326.1, 0.0)
    blk, red = path_xy(pg, fr, (0, 0, 0)), path_xy(pg, fr, (1, 0, 0))
    print("black path npts", len(blk), "x range MHz", ax.val(blk[:, 0].min()) / 1e6, ax.val(blk[:, 0].max()) / 1e6)
    print("red path npts", len(red), "end f MHz", ax.val(red[:, 0].max()) / 1e6, "end phase",
          ayr.val(red[red[:, 0].argmax(), 1]))
    print("ZOL_DB", ", ".join(f"{x:.2f}" for x in read_path(blk, ax, ayl, ct.ZOL_F)))
    print("ZOL_PH", ", ".join(f"{x:.2f}" for x in read_path(red, ax, ayr, ct.ZOL_F)))
    print("low-f plateau dB", read_path(blk, ax, ayl, np.array([200.0, 1e3, 1e4])))


def colours(_):
    d = pymupdf.open(THS_PDF)
    pg = d[12]
    fr = pymupdf.Rect(94.2 - 1, 130.5 - 1, 285.2 + 1, 265.8 + 1)
    c = collections.Counter()
    for dr in pg.get_drawings():
        col = dr.get("color")
        if col is None or not fr.intersects(dr["rect"]):
            continue
        c[(tuple(round(x, 3) for x in col), round(dr.get("width") or 0, 2))] += sum(1 for it in dr["items"] if it[0] in "lc")
    for k, v in c.most_common(12):
        print(k, v)


def ec(_):
    d = pymupdf.open(THS_PDF)
    keys = ("capacitance", "input resistance", "input impedance", "transimpedance", "inverting input", "noise")
    for i in range(4, 12):
        lines = d[i].get_text().splitlines()
        for k, ln in enumerate(lines):
            if any(s in ln.lower() for s in keys):
                print(i + 1, "|", " / ".join(x.strip() for x in lines[k:k + 6]))


def testcircuit(a):
    d = pymupdf.open(THS_PDF)
    for i in range(d.page_count):
        for ln in d[i].get_text().splitlines():
            if ("Figure 9-" in ln or "Parameter Measurement" in ln or "Test Circuit" in ln
                    or "test circuit" in ln) and len(ln) < 120:
                print(i + 1, ln)
    a.out_dir.mkdir(parents=True, exist_ok=True)
    d[26].get_pixmap(dpi=150).save(a.out_dir / "ths3491_p27.png")


def residuals(a):
    rows = json.loads((a.out_dir / "residuals.json").read_text(encoding="utf-8"))
    for s in sorted({r["series"] for r in rows}):
        v = [r["resid"] for r in rows if r["series"] == s and not math.isnan(r["resid"])]
        print(f"{s:16s} n={len(v):2d} max|resid|={max(abs(x) for x in v):.3f} mean={sum(v)/len(v):+.3f}")


PROBES = dict(captions=captions, spans=spans, plain=plain, vertices=vertices, colours=colours, ec=ec,
              testcircuit=testcircuit, residuals=residuals)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("probe", choices=list(PROBES))
    ap.add_argument("--out-dir", type=Path, default=ROOT / "data" / "digitization_checks")
    a = ap.parse_args()
    PROBES[a.probe](a)


if __name__ == "__main__":
    main()
