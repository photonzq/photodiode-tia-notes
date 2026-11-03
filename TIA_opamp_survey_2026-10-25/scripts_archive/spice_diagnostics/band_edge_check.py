"""How much the 50-points-per-decade SPICE noise grid misses of the 10-150 MHz band.

Usage: python band_edge_check.py [--spice <spice folder>]

The noise sweeps (dec 50 from 100 kHz) have no point at 150 MHz: the last one below it is
144.5 MHz.  The penalties of Section 10 integrate the saved spectra over the grid points in
10-150 MHz, i.e. over 10-144.5 MHz.  This compares that with the integral over exactly
10-150 MHz, the spectrum interpolated (log f) at 150 MHz.  Saved data only; nothing is simulated.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from spice_tia_checks import DESIGNS, KT, _scan_tag, read_wrdata, tag  # noqa: E402


def band_integral(f, S, lo, hi):
    """Integral of S over exactly [lo, hi]: grid points inside, end values interpolated in log f."""
    inside = (f > lo) & (f < hi)
    ends = np.interp(np.log10([lo, hi]), np.log10(f), S)
    ff = np.concatenate([[lo], f[inside], [hi]])
    SS = np.concatenate([[ends[0]], S[inside], [ends[1]]])
    return float(np.trapezoid(SS, ff))


def penalties(f, inn, R_F):
    S = inn ** 2
    band = (f >= 10e6) & (f <= 150e6)
    old = 10 * np.log10(np.trapezoid(S[band], f[band]) / (4 * KT / R_F * (f[band][-1] - f[band][0])))
    new = 10 * np.log10(band_integral(f, S, 10e6, 150e6) / (4 * KT / R_F * 140e6))
    return old, new


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--spice", type=Path, default=Path(__file__).resolve().parents[2] / "spice")
    a = ap.parse_args()
    pscan = json.loads((a.spice / "results" / "pscan.json").read_text(encoding="utf-8"))
    print("best designs at 1 pF / 2 kOhm (Table 10.13):")
    for part, e in pscan.items():
        d = e.get("design") or {}
        if d.get("cf_pF") is None:
            continue
        p = a.spice / "runs" / "pscan" / _scan_tag("noise_P", part, 2000.0, 1e-12, d["cf_pF"] * 1e-12) / "noise.txt"
        if not p.exists():
            print(f"  {part:10s} no saved spectrum")
            continue
        n = read_wrdata(p)
        old, new = penalties(n[:, 0], n[:, 1], 2000.0)
        print(f"  {part:10s} C_F {d['cf_pF']:.3f} pF: penalty on grid {old:6.2f} dB, exact band {new:6.2f} dB, "
              f"difference {new - old:+.3f} dB")
    print("designs of Sections 10.6-10.7 (check 'noise'):")
    for part, R_F, C_D, C_F, label in DESIGNS:
        p = a.spice / "runs" / "noise" / tag(part, R_F, C_D, C_F) / "noise.txt"
        if not p.exists():
            continue
        n = read_wrdata(p)
        old, new = penalties(n[:, 0], n[:, 1], R_F)
        print(f"  {part:10s} {label:28s}: on grid {old:6.2f} dB, exact band {new:6.2f} dB, difference {new - old:+.3f} dB")


if __name__ == "__main__":
    main()
