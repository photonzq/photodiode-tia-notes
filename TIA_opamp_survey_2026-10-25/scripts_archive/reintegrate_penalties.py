"""Recompute the SPICE noise penalties of Section 10 over exactly 10-150 MHz from the saved spectra.

Usage: python reintegrate_penalties.py [--spice <spice folder>]

Until 26 Oct 2026 the checks 'noise', 'cfscan' and 'pscan' integrated the saved noise spectra over
the grid points between 10 and 150 MHz.  The sweeps have 50 points per decade from 100 kHz, so the
last point below 150 MHz is 144.5 MHz and the band was 10-144.5 MHz.  spice_tia_checks.py now uses
band_penalty(), which interpolates the spectrum at the band edges.  This script applies the same
integral to the noise.txt files those checks saved and rewrites the penalty entries of
results/noise.json, cfscan.json and pscan.json in place.  Nothing is simulated.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from spice_tia_checks import CF_SCAN, DESIGNS, _scan_tag, band_penalty, read_wrdata, tag


def penalty(folder, R_F):
    n = read_wrdata(folder / "noise.txt")
    return band_penalty(n[:, 0], n[:, 1], R_F)


def update(entry, field, new, label):
    old = entry[field]
    entry[field] = new
    print(f"  {label:44s} {old:6.2f} -> {new:6.2f} dB ({new - old:+.3f})")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--spice", type=Path, default=Path(__file__).resolve().parent.parent / "spice")
    a = ap.parse_args()
    runs, results = a.spice / "runs", a.spice / "results"
    data = {name: json.loads((results / f"{name}.json").read_text(encoding="utf-8"))
            for name in ("noise", "cfscan", "pscan")}

    print("noise.json (designs of Sections 10.6-10.7):")
    for part, R_F, C_D, C_F, label in DESIGNS:
        key = f"{part}|{label}"
        if key in data["noise"]:
            update(data["noise"][key], "spice_penalty_10_150_dB",
                   penalty(runs / "noise" / tag(part, R_F, C_D, C_F), R_F), key)

    print("cfscan.json (proposed centres of variants A and B):")
    for variant, sc in CF_SCAN.items():
        part = sc["part"]
        for R_F, C_D in sc["configs"]:
            key = f"{C_D * 1e12:g} pF, {R_F / 1e3:g} kOhm"
            out = data["cfscan"].get(variant, {}).get(key)
            if not out:
                continue
            props = ({"proposal": out["proposal"]} if variant == "A" and "proposal" in out
                     else out.get("proposals", {}))
            for k, pr in props.items():
                folder = runs / "cfscan" / _scan_tag(f"noise_{variant}", part, R_F, C_D, pr["centre_pF"] * 1e-12)
                update(pr["noise"], "penalty_dB", penalty(folder, R_F), f"{variant} {key} {k}")

    print("pscan.json (every part's best design):")
    for part, e in data["pscan"].items():
        d = e["design"]
        folder = runs / "pscan" / _scan_tag("noise_P", part, e["R_F"], e["C_D_pF"] * 1e-12, d["cf_pF"] * 1e-12)
        update(d["noise"], "penalty_dB", penalty(folder, e["R_F"]), part)

    for name, out in data.items():
        with open(results / f"{name}.json", "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=1, default=float)


if __name__ == "__main__":
    main()
