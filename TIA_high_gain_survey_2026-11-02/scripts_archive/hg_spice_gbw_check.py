"""Check of the gain-bandwidth product that the model uses for a part whose data sheet gives
two values (2 November 2026): OPA1656 (20 MHz at unity gain, 53 MHz at a gain of 100, data
sheet p. 6) and OPA2156 (20 and 25 MHz, data sheet p. 6).  The script runs the part's TI
PSpice model (hg_spice.MODELS) in ngspice:

1. its open-loop gain and phase, from an AC analysis with the loop closed at DC only,
   through a 1-TH inductor, and the inverting input held at signal ground by 1 F;
2. its input voltage and current noise, as in hg_spice.check_models;
3. the ten TIA designs of the sweep on the 20-pF and 380-pF photodiodes, at the C_F of
   the designs in data/results/designs.json, against the analytic model with the data
   file's gain-bandwidth and with the alternative value GBW_ALT.

Results go to spice/results/<part>_gbw.json and the decks to spice/runs/.

Usage:  python hg_spice_gbw_check.py [PART GBW_ALT_MHz]      (default: OPA1656 53)
"""
from __future__ import annotations

import dataclasses
import json
import math
import sys

import numpy as np

import hg_model as m
import hg_spice as hs
from ngspice_shared import NgSpice

PART = sys.argv[1] if len(sys.argv) > 1 else "OPA1656"
GBW_ALT = (float(sys.argv[2]) if len(sys.argv) > 2 else 53.0) * 1e6
TAG = PART.lower()


def open_loop(ng: NgSpice) -> dict:
    folder = hs.RUNS / TAG / "aol"
    body = (hs.header(PART, f"{PART} open-loop gain") + hs.amp(PART, "inp", "inm", "out")
            + "VIN inp 0 DC 0 AC 1\nLFB out inm 1e12\nCFB inm 0 1\nRL out 0 10k\n")
    errs = hs.run(ng, hs.write_deck(folder, body + ".control\n"
                                    + hs.CONTROL_AC.format(ppd=40, f1=0.01, f2=1e9, name="aol.txt")
                                    + ".endc\n.end\n"))
    d = hs.read_cols(folder / "aol.txt")
    f, a = d[:, 0], d[:, 1] + 1j * d[:, 2]
    mag = np.abs(a)
    i_u = int(np.argmax(mag < 1.0))
    f_u = float(np.exp(np.interp(0.0, -np.log(mag[i_u - 1:i_u + 1]), np.log(f[i_u - 1:i_u + 1]))))
    phase_u = float(np.degrees(np.angle(a[i_u])))
    at = {}
    for fx in (10, 100, 1e3, 1e4, 1e5, 3e5, 1e6, 3e6, 1e7):
        ax = float(np.exp(np.interp(math.log(fx), np.log(f), np.log(mag))))
        ph = float(np.degrees(np.interp(math.log(fx), np.log(f), np.unwrap(np.angle(a)))))
        at[f"{fx:g}"] = dict(gain=ax, gain_db=20 * math.log10(ax), gbw_MHz=ax * fx / 1e6, phase_deg=ph)
    np.save(folder / "aol.npy", np.vstack([f, mag, np.degrees(np.unwrap(np.angle(a)))]))
    return dict(a0_db=float(20 * math.log10(mag[0])), f_unity_MHz=f_u / 1e6, phase_at_unity_deg=phase_u,
                at=at, errors=errs[:3])


def only(part: str, check):
    saved = dict(hs.MODELS)
    hs.MODELS.clear()
    hs.MODELS[part] = saved[part]
    try:
        return check()
    finally:
        hs.MODELS.clear()
        hs.MODELS.update(saved)


def designs(ng: NgSpice) -> list:
    rows = only(PART, lambda: hs.check_designs(ng))["designs"]
    amp = m.load_amps()[PART]
    alt = dataclasses.replace(amp, gbw=GBW_ALT)
    f = np.logspace(-1, 8, 181)
    for r in rows:
        c_d, r_sh = hs.SOURCES[r["source"]]
        d = m.Design(alt, r["rf"], r["cf_pF"] * 1e-12, m.Source(r["source"], c_d, r_sh), c_stray=hs.C_STRAY)
        f3, pk = hs.f3_peak(f, d.zt(f))
        floor = m.FOUR_KT / r["rf"] + m.FOUR_KT / r_sh
        dn = 10 * math.log10(hs.band(f, d.noise(f)["total"], 1.0, f3) / (floor * (f3 - 1.0)))
        r.update(f3_model_alt=f3, peak_model_alt=pk, dN_model_alt=dn)
        print(f"{r['source']} {r['rf']:.0e}: f3 SPICE {r['f3_spice']:.4g}, model {amp.gbw / 1e6:g} MHz "
              f"{r['f3_model']:.4g}, {GBW_ALT / 1e6:g} MHz {f3:.4g} Hz; "
              f"dN {r['dN_spice']:.2f} / {r['dN_model']:.2f} / {dn:.2f} dB", flush=True)
    return rows


def noise(ng: NgSpice) -> dict:
    amp = m.load_amps()[PART]
    hs.DATASHEET_EN_IN[PART] = ({fq: v * 1e9 for fq, v in amp.en_pts}, {fq: v * 1e15 for fq, v in amp.in_pts})
    return only(PART, lambda: hs.check_models(ng))


def main() -> None:
    hs.prepare_models()
    ng = NgSpice()
    res = dict(source=hs.MODELS[PART]["source"], gbw_alt_MHz=GBW_ALT / 1e6, open_loop=open_loop(ng))
    print(json.dumps(res["open_loop"], indent=1), flush=True)
    res["noise"] = noise(ng)
    res["designs"] = designs(ng)
    hs.RESULTS.mkdir(parents=True, exist_ok=True)
    out = hs.RESULTS / f"{TAG}_gbw.json"
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(res, fh, indent=1)
    print("written", out)


if __name__ == "__main__":
    main()
