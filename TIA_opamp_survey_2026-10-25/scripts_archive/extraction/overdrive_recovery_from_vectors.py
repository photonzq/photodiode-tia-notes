"""Estimate overdrive recovery from a vector-drawn overdrive-recovery plot.

Usage
-----
python overdrive_recovery_from_vectors.py <pdf> <page> <frame x0,y0,x1,y1>
       <t_full_ns> <vout_full_V> <vin_full_V> <gain> [--tol 0.25]

* frame: plot frame in PDF points; the time axis runs 0..t_full_ns across it,
  the output (left) axis -vout_full..+vout_full and the input (right) axis
  -vin_full..+vin_full from bottom to top.
* Candidate traces are the continuous subpaths of stroked paths (>= 0.9 pt)
  inside the frame that contain Bezier pieces; the subpath with most points
  is taken as the output and the next as the input.
* For each clip polarity, finds where the ideal output gain x input comes
  back inside the clip level, then the last time within --window ns after
  that (and before the ideal output reaches a clip level again) at which
  the output still differs from gain x input by more than
  --tol volts; the difference is printed as the recovery time, with the
  largest excursion in that window.  The output trace is taken to be the
  one of the two longest subpaths with the smaller vertical extent.
"""
import argparse

import numpy as np
import pymupdf


def subpaths(drawing, n_bezier=8):
    """Split a drawing into continuous polylines (new subpath at any jump)."""
    paths, pts, last = [], [], None
    for it in drawing["items"]:
        if it[0] not in ("l", "c"):
            continue
        p0 = it[1]
        if last is None or abs(p0.x - last.x) > 1e-3 or abs(p0.y - last.y) > 1e-3:
            if len(pts) > 1:
                paths.append(np.array(pts))
            pts = [(p0.x, p0.y)]
        if it[0] == "l":
            pts.append((it[2].x, it[2].y))
            last = it[2]
        else:
            _, c1, c2, p3 = it[1:5]
            for k in range(1, n_bezier + 1):
                t = k / n_bezier
                x = (1 - t) ** 3 * p0.x + 3 * (1 - t) ** 2 * t * c1.x + 3 * (1 - t) * t ** 2 * c2.x + t ** 3 * p3.x
                y = (1 - t) ** 3 * p0.y + 3 * (1 - t) ** 2 * t * c1.y + 3 * (1 - t) * t ** 2 * c2.y + t ** 3 * p3.y
                pts.append((x, y))
            last = p3
    if len(pts) > 1:
        paths.append(np.array(pts))
    return paths


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pdf")
    ap.add_argument("page", type=int)
    ap.add_argument("frame")
    ap.add_argument("t_full", type=float)
    ap.add_argument("vout_full", type=float)
    ap.add_argument("vin_full", type=float)
    ap.add_argument("gain", type=float)
    ap.add_argument("--tol", type=float, default=0.25)
    ap.add_argument("--window", type=float, default=80.0, help="ns searched after re-entry")
    a = ap.parse_args()
    x0, y0, x1, y1 = (float(v) for v in a.frame.split(","))
    page = pymupdf.open(a.pdf)[a.page - 1]
    cands = []
    for d in page.get_drawings():
        r = d["rect"]
        if (d.get("width") or 0) >= 0.9 and r.x0 >= x0 - 2 and r.x1 <= x1 + 2 and r.y0 >= y0 - 2 and r.y1 <= y1 + 2:
            if any(it[0] == "c" for it in d["items"]):
                cands.append(d)
    polys = [sp for d in cands for sp in subpaths(d)]
    polys.sort(key=len, reverse=True)
    pair = sorted(polys[:2], key=lambda q: q[:, 1].max() - q[:, 1].min())
    po, pi = pair[0], pair[1]  # output = smaller vertical extent (it clips)
    to_t = lambda x: (x - x0) / (x1 - x0) * a.t_full
    vo = lambda y: a.vout_full - (y - y0) / (y1 - y0) * 2 * a.vout_full
    vi = lambda y: a.vin_full - (y - y0) / (y1 - y0) * 2 * a.vin_full
    to, vout = to_t(po[:, 0]), vo(po[:, 1])
    ti, vin = to_t(pi[:, 0]), vi(pi[:, 1])
    oi = np.argsort(to)
    ii = np.argsort(ti)
    tgrid = np.arange(0, a.t_full, 0.25)
    vout_g = np.interp(tgrid, to[oi], vout[oi])
    ideal = a.gain * np.interp(tgrid, ti[ii], vin[ii])
    err = vout_g - ideal
    print(f"output range on plot: {vout.min():.2f} .. {vout.max():.2f} V; input range {vin.min():.3f} .. {vin.max():.3f} V")
    for sign in (+1, -1):
        clip = vout_g.max() if sign > 0 else vout_g.min()
        driven = sign * ideal > abs(clip) - a.tol  # ideal beyond the clip level
        k = 0
        while k < len(tgrid):
            if driven[k]:
                while k < len(tgrid) and driven[k]:
                    k += 1
                t_e = tgrid[min(k, len(tgrid) - 1)]
                lim = min(abs(vout_g.max()), abs(vout_g.min())) - a.tol
                later = np.where((tgrid > t_e) & (np.abs(ideal) > lim))[0]
                t_next = tgrid[later[0]] if len(later) else tgrid[-1]
                window = (tgrid >= t_e) & (tgrid <= min(t_e + a.window, t_next))
                bad = np.where(window & (np.abs(err) > a.tol))[0]
                t_s = tgrid[bad[-1]] if len(bad) else t_e
                worst = err[window].min() if sign > 0 else err[window].max()
                print(f"  {'+' if sign > 0 else '-'} clip {clip:+.2f} V: ideal output re-enters at {t_e:.1f} ns; "
                      f"output last outside +/-{a.tol} V of ideal at {t_s:.1f} ns -> recovery {t_s - t_e:.1f} ns; "
                      f"largest excursion {worst:+.2f} V")
            else:
                k += 1


if __name__ == "__main__":
    main()
