"""Draw digitized datasheet readings on the rendered datasheet figure, to check them by eye, and
print each reading's residual against the figure's own vector path.

usage: python overlay_digitized.py [--zoom 4] [--out-dir <dir>] [--spice <json>]

Each check renders the figure from the PDF at zoom x 72 dpi.  The axis calibration is the plot
frame (the vector rectangle of the axes, in PDF points, listed by integrated_tia/spans.py) with the
axis values at its edges; tick-label centres sit about 0.35 pt below the grid lines and are not
used.  Thin cyan crosses mark grid intersections computed from that calibration: they must sit on
the printed grid, which checks the calibration itself.  Readings are hollow rings that the curve
should pass through; model curves are dashed lines.  The residual table reads the curve's vector
path (stroke colour given per series) at each reading's abscissa with the same calibration.

The readings are imported from the files the analysis itself uses (composite_tia.py for the
THS3491, data/specs/OPA859.json through parts_db.ol_points for the OPA859), so the images show
exactly the numbers that enter the calculations.  For audit, <out-dir>/manifest.json records, per
image: the datasheet file and its SHA-256, page, plot frame, axis calibration and clip; every
series drawn with its source (file, variable) and the values drawn; and the SHA-256 of each source
file at the time of drawing.  The one-off probes run alongside are in
digitization_checks/datasheet_figure_probes.py.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pymupdf
from PIL import Image, ImageDraw, ImageFont

import composite_tia as ct
from parts_db import ol_points

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
THS_PDF = ROOT / "datasheets" / "hv_output_stage" / "THS3491_TI_SBOS875C_2023-02.pdf"


class Axis:
    """Value -> PDF points, linear in the value (or in its log10), fixed by the frame edges."""

    def __init__(self, p0, v0, p1, v1, log=False):
        self.log, self.p0, self.p1 = log, p0, p1
        self.t0, self.t1 = self._t(v0), self._t(v1)

    def _t(self, v):
        v = np.asarray(v, float)
        return np.log10(v) if self.log else v

    def pt(self, v):
        return self.p0 + (self._t(v) - self.t0) * (self.p1 - self.p0) / (self.t1 - self.t0)

    def val(self, p):
        t = self.t0 + (np.asarray(p, float) - self.p0) * (self.t1 - self.t0) / (self.p1 - self.p0)
        return 10 ** t if self.log else t


def path_xy(page, frame, color, tol=0.06):
    """Points (PDF points) of every stroked path of the given RGB colour inside the frame,
    sorted by x; Bezier segments contribute their end points."""
    grow = pymupdf.Rect(frame[0] - 1, frame[1] - 1, frame[2] + 1, frame[3] + 1)
    pts = []
    for dr in page.get_drawings():
        c = dr.get("color")
        if c is None or max(abs(a - b) for a, b in zip(c, color)) > tol:
            continue
        sub = []
        for it in dr["items"]:
            if it[0] == "l":
                sub += [it[1], it[2]]
            elif it[0] == "c":
                sub += [it[1], it[4]]
        sub = [p for p in sub if grow.contains(p)]
        if len(sub) < 8:
            continue
        xs = [p.x for p in sub]
        ys = [p.y for p in sub]
        if max(xs) - min(xs) < 5 or max(ys) - min(ys) < 2:   # grid line or legend swatch
            continue
        pts += list(zip(xs, ys))
    pts.sort()
    return np.array(pts)


def read_path(xy, ax_x, ax_y, xs):
    """Ordinate of the path at abscissae xs (values), interpolated in PDF points."""
    px = ax_x.pt(xs)
    order = np.argsort(xy[:, 0])
    x, y = xy[order, 0], xy[order, 1]
    out = np.interp(px, x, y, left=np.nan, right=np.nan)
    return ax_y.val(out)


def dashed(draw, pts, fill, width, dash=10, gap=7):
    """Dashed polyline through pixel points."""
    run, on = 0.0, True
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        seg = float(np.hypot(x1 - x0, y1 - y0))
        pos = 0.0
        while pos < seg:
            step = min((dash if on else gap) - run, seg - pos)
            if on:
                a, b = pos / seg, (pos + step) / seg
                draw.line([(x0 + a * (x1 - x0), y0 + a * (y1 - y0)), (x0 + b * (x1 - x0), y0 + b * (y1 - y0))],
                          fill=fill, width=width)
            pos += step
            run += step
            if run >= (dash if on else gap) - 1e-9:
                run, on = 0.0, not on


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _rel(path):
    try:
        return Path(path).resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return Path(path).name


def manifest_entry(chk, zoom, spice_path):
    """What one image shows and where each drawn value came from."""
    def axis(ax):
        return dict(pt0=ax.p0, pt1=ax.p1, value0=float(10 ** ax.t0 if ax.log else ax.t0),
                    value1=float(10 ** ax.t1 if ax.log else ax.t1), log=ax.log)
    out = dict(image=f"{chk['name']}.png", pdf=_rel(chk["pdf"]), pdf_sha256=sha256(chk["pdf"]), page=chk["page"],
               frame_pt=list(chk["frame"]), clip_pt=list(chk["clip"]), zoom=zoom, x_axis=axis(chk["x"]),
               y_axes={k: axis(v) for k, v in chk["y"].items()}, series=[], models=[])
    for s in chk.get("series", []):
        out["series"].append(dict(label=s["label"], source=s["source"], axis=s["axis"],
                                  x=[float(v) for v in s["x"]], y=[float(v) for v in s["y"]]))
    for m in chk.get("models", []):
        out["models"].append(dict(label=m.get("label", ""), source=m.get("source", "")))
    if spice_path is not None and chk["name"] in json.loads(Path(spice_path).read_text(encoding="utf-8")):
        out["models"].append(dict(label="SPICE curves", source=_rel(spice_path)))
    return out


def font(size):
    for name in ("arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def overlay(chk, zoom, out_dir, spice=None):
    doc = pymupdf.open(chk["pdf"])
    page = doc[chk["page"] - 1]
    clip = pymupdf.Rect(*chk["clip"])
    pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), clip=clip)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    drw = ImageDraw.Draw(img)

    def px(xp, yp):
        return (np.asarray(xp) - clip.x0) * zoom, (np.asarray(yp) - clip.y0) * zoom

    ax_x = chk["x"]
    # calibration crosses at grid intersections
    for gx in chk["grid_x"]:
        for gy in chk["grid_y"]:
            u, v = px(ax_x.pt(gx), chk["y"]["left"].pt(gy))
            drw.line([(u - 9, v), (u + 9, v)], fill=(0, 200, 255), width=1)
            drw.line([(u, v - 9), (u, v + 9)], fill=(0, 200, 255), width=1)
    rows = []
    for s in chk.get("series", []):
        ax_y = chk["y"][s["axis"]]
        xs, ys = np.asarray(s["x"], float), np.asarray(s["y"], float)
        ok = np.isfinite(ys)
        u, v = px(ax_x.pt(xs[ok]), ax_y.pt(ys[ok]))
        r = 6 if zoom <= 5 else 9
        for a, b in zip(u, v):
            drw.ellipse([a - r, b - r, a + r, b + r], outline=s["ring"], width=2)
        if s.get("path_color") is not None:
            xy = path_xy(page, chk["frame"], s["path_color"])
            truth = read_path(xy, ax_x, ax_y, xs) if len(xy) else np.full_like(xs, np.nan)
            for x, y, t in zip(xs, ys, truth):
                rows.append(dict(check=chk["name"], series=s["label"], x=float(x), reading=float(y),
                                 path=float(t), resid=float(y - t)))
    for m in chk.get("models", []) + (spice or {}).get(chk["name"], []):
        ax_y = chk["y"][m.get("axis", "left")]
        xs, ys = np.asarray(m["x"], float), np.asarray(m["y"], float)
        fr = chk["frame"]
        xp, yp = ax_x.pt(xs), ax_y.pt(ys)
        keep = np.isfinite(yp) & (xp >= fr[0]) & (xp <= fr[2]) & (yp >= fr[1]) & (yp <= fr[3])
        u, v = px(xp[keep], yp[keep])
        pts = list(zip(u, v))
        if len(pts) > 1:
            if m.get("style") == "dotted":
                dashed(drw, pts, m["color"], 3, dash=3, gap=5)
            else:
                dashed(drw, pts, m["color"], 3)
    f = font(int(4.2 * zoom))
    y0 = 4
    for line in chk["legend"]:
        drw.text((8, y0), line, fill=(120, 0, 120), font=f)
        y0 += int(5.2 * zoom)
    out = out_dir / f"{chk['name']}.png"
    img.save(out)
    return out, rows


def checks(zoom_inset):
    zol_frame = (334.0, 326.1, 525.4, 461.1)                     # Fig 8-22, p16
    zol = dict(pdf=THS_PDF, page=16, frame=zol_frame,
               x=Axis(334.0, 1e2, 525.4, 1e9, log=True),
               y={"left": Axis(461.1, 40.0, 326.1, 140.0), "right": Axis(461.1, -150.0, 326.1, 0.0)},
               y_range=(40, 140),
               series=[dict(label="|Z_OL| (dBohm)", x=ct.ZOL_F, y=ct.ZOL_DB, axis="left", ring=(0, 90, 255),
                            path_color=(0, 0, 0), source="scripts_archive/composite_tia.py: ZOL_F, ZOL_DB"),
                       dict(label="phase (deg)", x=ct.ZOL_F, y=ct.ZOL_PH, axis="right", ring=(0, 170, 0),
                            path_color=(1, 0, 0), source="scripts_archive/composite_tia.py: ZOL_F, ZOL_PH")])
    vmax_frame = (217.5, 186.7, 408.0, 321.7)                    # Fig 9-4, p29
    vmax = dict(pdf=THS_PDF, page=29, frame=vmax_frame,
                x=Axis(217.5, 1.0, 408.0, 1000.0, log=True),
                y={"left": Axis(321.7, 0.0, 186.7, 30.0)}, y_range=(0, 30),
                series=[dict(label="+/-15 V (Vpp)", x=ct.VMAX_15_F / 1e6, y=ct.VMAX_15, axis="left",
                             ring=(0, 90, 255), path_color=(0, 0, 0),
                             source="scripts_archive/composite_tia.py: VMAX_15_F (Hz, drawn in MHz), VMAX_15"),
                        dict(label="+/-7.5 V (Vpp)", x=ct.VMAX_7p5_F / 1e6, y=ct.VMAX_7p5, axis="left",
                             ring=(0, 170, 0), path_color=(1, 0, 0),
                             source="scripts_archive/composite_tia.py: VMAX_7p5_F (Hz, drawn in MHz), VMAX_7p5")])
    # THS3491 Fig 8-13 (HD2) and Fig 8-14 (HD3) against output swing, p15
    hd = {}
    for key, frame, arr in (("HD2", (96.2, 130.4, 287.2, 265.4), ct.HD2_100M), ("HD3", (345.0, 130.4, 536.0, 265.4), ct.HD3_100M)):
        hd[key] = dict(pdf=THS_PDF, page=15, frame=frame, x=Axis(frame[0], 0.0, frame[2], 25.0),
                       y={"left": Axis(frame[3], -120.0, frame[1], 0.0)}, y_range=(-120, 0),
                       series=[dict(label=f"{key} 100 MHz 100 ohm", x=ct.HD_VPP, y=arr["rl100"], axis="left",
                                    ring=(0, 90, 255), path_color=(1, 0, 0),
                                    source=f"scripts_archive/composite_tia.py: HD_VPP, {key}_100M['rl100']"),
                               dict(label=f"{key} 100 MHz 1 kohm", x=ct.HD_VPP, y=arr["rl1k"], axis="left",
                                    ring=(0, 170, 0), path_color=(0.161, 0.361, 0.459),
                                    source=f"scripts_archive/composite_tia.py: HD_VPP, {key}_100M['rl1k']")])
    # the composite's first stage: OPA859 (SBOS852A) Fig 6-10, p9, readings in data/specs/OPA859.json
    pts = ol_points("OPA859")
    f859 = np.array([p[0] for p in pts])
    a859 = dict(pdf=ROOT / "datasheets" / "opa859.pdf", page=9, frame=(337.0, 329.3, 518.5, 457.6),
                x=Axis(337.0, 1e4, 518.5, 5e9, log=True),
                y={"left": Axis(457.6, -15.0, 329.3, 75.0), "right": Axis(457.6, -225.0, 329.3, 45.0)},
                y_range=(-15, 75),
                series=[dict(label="OPA859 |A| (dB)", x=f859, y=[p[1] for p in pts], axis="left", ring=(0, 90, 255),
                             path_color=(0, 0, 0),
                             source="data/specs/OPA859.json: open_loop_curve.points f_Hz, gain_dB (parts_db.ol_points)"),
                        dict(label="OPA859 phase", x=f859, y=[np.nan if p[2] is None else p[2] for p in pts],
                             axis="right", ring=(0, 170, 0), path_color=(1, 0, 0),
                             source="data/specs/OPA859.json: open_loop_curve.points f_Hz, phase_deg (parts_db.ol_points)")])
    resp_frame = (94.2, 130.5, 285.2, 265.8)                     # Fig 8-1, p13
    fm = np.logspace(0, np.log10(4000), 600)
    models, models0 = [], []
    for g, col in FIG81_GAINS:
        models.append(dict(x=fm, y=20 * np.log10(np.abs(ct.h2(fm * 1e6, g)) / g), color=col,
                           label=f"G = {g}, Eq. (71)", source="composite_tia.h2 (Fig 8-22 readings, C_N2, R_I, RF2_TABLE)"))
        models0.append(dict(x=fm, y=20 * np.log10(np.abs(ct.h2(fm * 1e6, g, c_n=0.0)) / g), color=col,
                            label=f"G = {g}, textbook", source="composite_tia.h2 with c_n = 0 (Fig 8-22 readings)"))
    resp = dict(pdf=THS_PDF, page=13, frame=resp_frame, x=Axis(94.2, 1.0, 285.2, 4000.0, log=True),
                y={"left": Axis(265.8, -15.0, 130.5, 3.0)}, y_range=(-15, 3), models=models)
    out = [
        dict(zol, name="THS3491_Fig8-22_Zol_full", clip=(300, 318, 560, 498), grid_x=[1e3, 1e5, 1e7, 1e9],
             grid_y=[40, 60, 80, 100, 120, 140],
             legend=["rings: readings in composite_tia.py (blue |Z_OL|, green phase)",
                     "cyan crosses: grid points from the frame calibration"]),
        dict(zol, name="THS3491_Fig8-22_Zol_inset_100MHz-1GHz", clip=(494, 398, 528, 464), zoom=zoom_inset,
             grid_x=[1e8, 2e8, 5e8, 1e9], grid_y=[50, 60, 70],
             legend=["100 MHz - 1 GHz", "rings: readings"]),
        dict(zol, name="THS3491_Fig8-22_Zol_inset_100kHz-100MHz", clip=(412, 318, 500, 420), zoom=zoom_inset / 2,
             grid_x=[1e5, 1e6, 1e7, 1e8], grid_y=[70, 80, 90, 100, 110, 120, 130],
             legend=["100 kHz - 100 MHz", "rings: readings"]),
        dict(vmax, name="THS3491_Fig9-4_Vmax_full", clip=(185, 180, 425, 345), grid_x=[1, 10, 100, 1000],
             grid_y=[0, 5, 10, 15, 20, 25, 30],
             legend=["rings: readings in composite_tia.py", "cyan crosses: frame calibration"]),
        dict(vmax, name="THS3491_Fig9-4_Vmax_inset_10-500MHz", clip=(278, 196, 394, 316), zoom=zoom_inset / 2,
             grid_x=[10, 100], grid_y=[5, 10, 15, 20, 25],
             legend=["10 - 500 MHz", "rings: readings"]),
        dict(hd["HD2"], name="THS3491_Fig8-13_HD2_vs_swing", clip=(62, 120, 300, 290), grid_x=[0, 10, 20],
             grid_y=[-120, -80, -40, 0],
             legend=["rings: readings (blue 100 MHz 100 ohm,", "green 100 MHz 1 kohm)"]),
        dict(hd["HD3"], name="THS3491_Fig8-14_HD3_vs_swing", clip=(312, 120, 552, 290), grid_x=[0, 10, 20],
             grid_y=[-120, -80, -40, 0],
             legend=["rings: readings (blue 100 MHz 100 ohm,", "green 100 MHz 1 kohm)"]),
        dict(a859, name="OPA859_Fig6-10_Aol_full", clip=(305, 318, 560, 500), grid_x=[1e4, 1e6, 1e8],
             grid_y=[-15, 15, 45, 75],
             legend=["rings: data/specs/OPA859.json (blue |A|, green phase)",
                     "cyan crosses: frame calibration"]),
        dict(a859, name="OPA859_Fig6-10_Aol_inset_10MHz-5GHz", clip=(428, 326, 522, 460), zoom=zoom_inset / 2,
             grid_x=[1e7, 1e8, 1e9], grid_y=[-15, 0, 15, 30],
             legend=["10 MHz - 5 GHz", "rings: readings"]),
        dict(resp, name="THS3491_Fig8-1_textbook_formula", clip=(62, 120, 300, 302), models=models0,
             grid_x=[1, 10, 100, 1000], grid_y=[-15, -12, -9, -6, -3, 0, 3],
             legend=["dashed: G/(1+(R_F2+G r_i)/Z_OL), Z_OL from Fig 8-22",
                     "(no inverting-node capacitance)"]),
        dict(resp, name="THS3491_Fig8-1_model_check", clip=(62, 120, 300, 302), grid_x=[1, 10, 100, 1000],
             grid_y=[-15, -12, -9, -6, -3, 0, 3],
             legend=["dashed: Eq. (71), Z_OL from Fig 8-22, C_n 1.2 pF",
                     "dotted: TI SPICE model, Fig 9-1 circuit"]),
        dict(zol, name="THS3491_Fig8-22_Zol_spice", clip=(300, 318, 560, 498), series=[],
             grid_x=[1e3, 1e5, 1e7, 1e9], grid_y=[40, 60, 80, 100, 120, 140],
             legend=["dotted: TI SPICE model, Z_OL at the pin (blue dB, green deg)",
                     "dashed: the model's internal Z_OL (C12 removed)"]),
    ]
    return out


FIG81_GAINS = ((2, (0, 0, 0)), (5, (230, 0, 0)), (10, (110, 110, 110)), (20, (40, 100, 120)))
FIG81_PATH_COLORS = {2: (0, 0, 0), 5: (1, 0, 0), 10: (0.724, 0.724, 0.724), 20: (0.161, 0.361, 0.459)}


def fig81_datasheet():
    """TI's measured responses of Fig 8-1 read off their vector paths: -3 dB frequency (first
    crossing) and peaking, per gain."""
    doc = pymupdf.open(THS_PDF)
    page = doc[12]
    frame = (94.2, 130.5, 285.2, 265.8)
    ax, ay = Axis(94.2, 1.0, 285.2, 4000.0, log=True), Axis(265.8, -15.0, 130.5, 3.0)
    out = {}
    for g, col in FIG81_PATH_COLORS.items():
        xy = path_xy(page, frame, col)
        f = ax.val(xy[:, 0])
        v = ay.val(xy[:, 1])
        order = np.argsort(f)
        f, v = f[order], v[order]
        k = np.where(v < -3)[0]
        f3 = float(10 ** np.interp(-3, [v[k[0]], v[k[0] - 1]], [np.log10(f[k[0]]), np.log10(f[k[0] - 1])])) if len(k) else None
        i = int(np.argmax(v))
        out[f"G{g}"] = dict(f3_MHz=f3, peak_dB=float(max(v.max(), 0.0)), f_peak_MHz=float(f[i]))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--zoom", type=float, default=4.0)
    ap.add_argument("--out-dir", type=Path, default=ROOT / "data" / "digitization_checks")
    ap.add_argument("--spice", type=Path, default=None,
                    help="JSON {check name: [{x, y, color, style}]} of SPICE curves to add")
    a = ap.parse_args()
    a.out_dir.mkdir(parents=True, exist_ok=True)
    spice = None
    if a.spice is not None and a.spice.exists():
        spice = json.loads(a.spice.read_text(encoding="utf-8"))
        for v in spice.values():
            for m in v:
                m["color"] = tuple(m["color"])
    all_rows = []
    manifest = dict(sources={p: sha256(ROOT / p) for p in ("scripts_archive/composite_tia.py",
                                                           "scripts_archive/overlay_digitized.py",
                                                           "scripts_archive/parts_db.py",
                                                           "data/specs/OPA859.json")},
                    images=[])
    if a.spice is not None and a.spice.exists():
        manifest["sources"][_rel(a.spice)] = sha256(a.spice)
    for chk in checks(zoom_inset=16.0):
        zoom = chk.get("zoom", a.zoom)
        out, rows = overlay(chk, zoom, a.out_dir, spice)
        manifest["images"].append(manifest_entry(chk, zoom, a.spice if spice else None))
        print("wrote", out.name)
        if "inset" not in chk["name"]:
            all_rows += rows
    (a.out_dir / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    if all_rows:
        print(f"\n{'series':16s} {'x':>10s} {'reading':>9s} {'path':>9s} {'resid':>7s}")
        for r in all_rows:
            print(f"{r['series']:16s} {r['x']:10.4g} {r['reading']:9.2f} {r['path']:9.2f} {r['resid']:7.2f}")
        (a.out_dir / "residuals.json").write_text(json.dumps(all_rows, indent=1), encoding="utf-8")
    ds = fig81_datasheet()
    print("\nFig 8-1, TI's measured curves:")
    for k, v in ds.items():
        print(f"  {k}: -3 dB {v['f3_MHz']:.0f} MHz, peak {v['peak_dB']:.2f} dB at {v['f_peak_MHz']:.0f} MHz")
    (a.out_dir / "fig8-1_datasheet_curves.json").write_text(json.dumps(ds, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
