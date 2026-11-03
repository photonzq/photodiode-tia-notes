"""LTspice checks of the high-gain TIA note, for the Analog Devices models that ship with
LTspice (some of them encrypted, so that only LTspice can run them).  LTspice is run as a
headless engine on netlists written here (LTspice.exe -b -ascii <deck>.net), and its ASCII
.raw files are parsed here.

Usage:  python hg_ltspice.py <check> [<check> ...]
        <check> = designs | models | logamp

  designs  ADA4530-1, ADA4625-1 and LTC6268-10 in the TIA designs of the sweep (100 kOhm-
           1 GOhm on the 20-pF and 380-pF photodiodes, C_F as designed by hg_analysis.py):
           transimpedance and input-referred noise against the analytic model.
  models   each model's own input voltage noise and input current noise (unity-gain buffer,
           with and without a noiseless resistor in series with the + input).
  logamp   AD8304 and ADL5303: output voltage, small-signal bandwidth and output noise at
           100 pA-10 mA, against Eqs. (31), (33) and (35) of the note.

The LTspice executable is found at the default per-user install location or from the
LTSPICE environment variable.  Decks and raw files go to spice/runs/lt_<check>/<case>/,
summaries to spice/results/lt_<check>.json.
"""
from __future__ import annotations

import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

import hg_model as m
from hg_spice import SOURCES, SWEEP_NAMES, C_STRAY, band, f3_peak

ROOT = Path(__file__).resolve().parent.parent
RUNS = ROOT / "spice" / "runs"
RESULTS = ROOT / "spice" / "results"
EXE = Path(os.environ.get("LTSPICE", Path.home() / "AppData/Local/Programs/ADI/LTspice/LTspice.exe"))

LT_MODELS = {
    "ADA4530-1": dict(lib=".lib ADI1.lib", inst="{p} {n} vcc vee {o} grd ADA4530-1", vs=5.0,
                      extra="RGRD grd 0 1Meg\n", source="LTspice library ADI1.lib, subcircuit ADA4530-1"),
    "ADA4625-1": dict(lib=".lib ADA4625-1.sub", inst="{p} {n} vcc vee {o} ADA4625-1", vs=15.0,
                      source="LTspice library ADA4625-1.sub (encrypted)"),
    "LTC6268-10": dict(lib=".lib LTC2.lib", inst="{p} {n} {o} vcc vee vcc LTC6268-10", vs=2.5,
                       source="LTspice library LTC2.lib, subcircuit LTC6268-10"),
}


# ---------------------------------------------------------------- engine
def run_lt(folder: Path, name: str, text: str, timeout: float = 600) -> dict:
    folder.mkdir(parents=True, exist_ok=True)
    net = folder / f"{name}.net"
    with open(net, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    raw = folder / f"{name}.raw"
    if raw.exists():
        raw.unlink()
    subprocess.run([str(EXE), "-b", "-ascii", net.name], cwd=folder, timeout=timeout,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    log = folder / f"{name}.log"
    log_text = ""
    if log.exists():
        b = log.read_bytes()
        log_text = b.decode("utf-16-le", errors="replace") if b[1:2] == b"\x00" else b.decode("latin-1")
    if not raw.exists():
        raise RuntimeError(f"LTspice wrote no raw file for {net}:\n{log_text[-800:]}")
    return parse_raw(raw) | {"log": log_text}


def parse_raw(path: Path) -> dict:
    """ASCII .raw (UTF-16LE or 8-bit): variable names and a (points x variables) array,
    complex for AC analyses.  Stepped runs keep all steps in sequence."""
    b = path.read_bytes()
    text = b.decode("utf-16-le", errors="replace") if b[1:2] == b"\x00" else b.decode("latin-1")
    head, _, body = text.partition("Values:")
    names = []
    in_vars = False
    flags = ""
    for ln in head.splitlines():
        if ln.startswith("Flags:"):
            flags = ln
        if ln.startswith("Variables:"):
            in_vars = True
            continue
        if in_vars and ln.strip():
            names.append(ln.split()[1])
    nv = len(names)
    tokens = body.split()
    complex_data = "complex" in flags
    vals = []
    i = 0
    row = []
    while i < len(tokens):
        tok = tokens[i]
        if not row:          # point index precedes the scale value
            i += 1
            tok = tokens[i]
        if complex_data:
            re_, im_ = tok.split(",")
            row.append(complex(float(re_), float(im_)))
        else:
            row.append(float(tok.split(",")[0]))
        i += 1
        if len(row) == nv:
            vals.append(row)
            row = []
    arr = np.array(vals)
    return {"names": names, "data": arr, "flags": flags}


def col(res: dict, name: str) -> np.ndarray:
    names = [k.lower() for k in res["names"]]
    key = name.lower()
    if key == "v(inoise)" and key not in names:
        key = "i(inoise)"          # LTspice's name when the input source is a current source
    return res["data"][:, names.index(key)]


def header(part: str, title: str) -> str:
    mm = LT_MODELS[part]
    return (f"* {title}\n{mm['lib']}\n.temp 25\n.options plotwinsize=0 numdgt=15\n"
            f"VCC vcc 0 {mm['vs']:g}\nVEE vee 0 {-mm['vs']:g}\n{mm.get('extra', '')}")


def amp(part: str, p: str, n: str, o: str) -> str:
    return "XU1 " + LT_MODELS[part]["inst"].format(p=p, n=n, o=o) + "\n"


# ---------------------------------------------------------------- designs
def check_designs() -> dict:
    sweep = json.loads((m.DATA / "results" / "designs.json").read_text())
    amps = m.load_amps()
    out = []
    for part in LT_MODELS:
        for sname, (c_d, r_sh) in list(SOURCES.items())[:2]:
            for rf in (1e5, 1e6, 1e7, 1e8, 1e9):
                d0 = next(r for r in sweep if r["amp"] == part and r["rf"] == rf
                          and r["source"] == SWEEP_NAMES[sname])
                c_f = d0["cf_pF"] * 1e-12
                case = f"{part}_{sname}_{rf:.0e}"
                folder = RUNS / "lt_designs" / case
                body = (header(part, case) + amp(part, "0", "inm", "out")
                        + f"RF out inm {rf:g}\nCF out inm {c_f:.6g}\nCD inm 0 {c_d + C_STRAY:.6g}\n"
                          f"RSH inm 0 {r_sh:g}\nIph 0 inm 0 AC 1\nRL out 0 10k\n")
                ac = run_lt(folder, "ac", body + ".ac dec 20 0.1 1e8\n.end\n")
                nz = run_lt(folder, "noise", body + ".noise V(out) Iph dec 20 0.1 1e8\n.end\n")
                f = np.real(col(ac, "frequency"))
                z = col(ac, "V(out)")
                fn = np.real(col(nz, "frequency"))
                inoise = np.real(col(nz, "V(inoise)"))
                f3s, pks = f3_peak(f, z)
                d = m.Design(amps[part], rf, c_f, m.Source(sname, c_d, r_sh), c_stray=C_STRAY)
                f3a, pka = f3_peak(f, d.zt(f))
                na = d.noise(fn)
                floor = m.FOUR_KT / rf + m.FOUR_KT / r_sh
                dn_s = 10 * math.log10(band(fn, inoise ** 2, 1.0, f3s) / (floor * (f3s - 1.0)))
                dn_a = 10 * math.log10(band(fn, na["total"], 1.0, f3a) / (floor * (f3a - 1.0)))
                np.save(folder / "compare.npy", np.vstack([fn, inoise, np.sqrt(na["total"]),
                                                           np.interp(np.log10(fn), np.log10(f), np.abs(z)),
                                                           np.abs(d.zt(fn))]))
                out.append(dict(part=part, source=sname, rf=rf, cf_pF=c_f * 1e12, f3_spice=f3s, f3_model=f3a,
                                peak_spice=pks, peak_model=pka, dN_spice=dn_s, dN_model=dn_a,
                                zt0_spice=float(abs(z[0])), engine="LTspice"))
                print(f"{case}: f3 {f3s:.4g}/{f3a:.4g} Hz, peak {pks:.2f}/{pka:.2f} dB, dN {dn_s:.2f}/{dn_a:.2f} dB",
                      flush=True)
    return {"designs": out}


def check_models() -> dict:
    out = {}
    for part in LT_MODELS:
        res = {}
        for label, r_s in (("en", 0.0), ("in_1e8", 1e8), ("in_1e10", 1e10)):
            folder = RUNS / "lt_models" / f"{part}_{label}"
            src = (f"VS src 0 0 AC 1\nRS src inp {r_s:g} noiseless\n" if r_s else "VS inp 0 0 AC 1\n")
            body = header(part, f"{part} {label}") + amp(part, "inp", "out", "out") + src + "RL out 0 10k\n"
            nz = run_lt(folder, "noise", body + ".noise V(out) VS dec 10 0.01 1e7\n.end\n")
            res[label] = dict(f=np.real(col(nz, "frequency")).tolist(), inoise=np.real(col(nz, "V(inoise)")).tolist())
        f = np.array(res["en"]["f"])
        en = np.array(res["en"]["inoise"])
        for r_s, label in ((1e8, "in_1e8"), (1e10, "in_1e10")):
            tot = np.array(res[label]["inoise"])
            res[label]["in_A"] = (np.sqrt(np.clip(tot ** 2 - en ** 2, 0, None)) / r_s).tolist()
        out[part] = res
        e1k = float(np.interp(3.0, np.log10(f), en))
        i10 = float(np.interp(1.0, np.log10(f), np.array(res["in_1e8"]["in_A"])))
        print(f"{part}: e_n(1 kHz) = {e1k * 1e9:.3g} nV/rtHz, i_n(10 Hz) = {i10 * 1e15:.3g} fA/rtHz", flush=True)
    return {"models": out}


# ---------------------------------------------------------------- logarithmic amplifiers
LOGAMPS = {
    # pins: VSUM INPT VPDB VREF ACOM VLOG BFIN VOUT VPS BFNG VNEG|GND PWDN
    "AD8304": dict(lib=".lib AD8304.lib",
                   inst="XU1 vsum inpt vpdb vref 0 vlog vlog vout vps vout 0 0 AD8304",
                   source="LTspice library AD8304.lib"),
    "ADL5303": dict(lib=".lib ADL5303.sub",
                    inst="XU1 vsum inpt vpdb vref 0 vlog vlog vout vps vout 0 0 ADL5303",
                    source="LTspice library ADL5303.sub (encrypted)"),
}
CURRENTS = [1e-10, 1e-9, 1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 1e-2]


def check_logamp() -> dict:
    out = {}
    for part, mm in LOGAMPS.items():
        rows = []
        for i_in in CURRENTS:
            case = f"{part}_{i_in:.0e}"
            folder = RUNS / "lt_logamp" / case
            body = (f"* {case}\n{mm['lib']}\n.temp 25\n.options plotwinsize=0 numdgt=15\n"
                    "VPS vps 0 5\n" + mm["inst"] + "\n"
                    f"Iin 0 inpt {i_in:g} AC 1\nCPD inpt 0 10p\nRL vout 0 10k\n")
            op = run_lt(folder, "op", body + ".op\n.end\n")
            ac = run_lt(folder, "ac", body + ".ac dec 20 1 1e8\n.end\n")
            nz = run_lt(folder, "noise", body + ".noise V(vlog) Iin dec 20 10 1e7\n.end\n")
            v_log = float(np.real(col(op, "V(vlog)"))[0])
            f = np.real(col(ac, "frequency"))
            h = col(ac, "V(vlog)")
            f3, pk = f3_peak(f, h)
            fn = np.real(col(nz, "frequency"))
            vn = np.real(col(nz, "V(onoise)"))
            vn_1k = float(np.interp(3.0, np.log10(fn), vn))
            np.save(folder / "ac_noise.npy", np.vstack([fn, vn, np.interp(np.log10(fn), np.log10(f), np.abs(h))]))
            rows.append(dict(i_in=i_in, v_log=v_log, f3=f3, peak=pk, vn_1k=vn_1k,
                             small_signal_gain=float(abs(h[0]))))
            print(f"{case}: VLOG {v_log:.4f} V, f3 {f3:.4g} Hz, peak {pk:.2f} dB, "
                  f"noise at 1 kHz {vn_1k * 1e6:.3g} uV/rtHz", flush=True)
        out[part] = rows
    return {"logamp": out}


CHECKS = {"designs": check_designs, "models": check_models, "logamp": check_logamp}


def main() -> None:
    if not EXE.exists():
        sys.exit(f"LTspice not found at {EXE}; set LTSPICE")
    RESULTS.mkdir(parents=True, exist_ok=True)
    for name in sys.argv[1:] or list(CHECKS):
        res = CHECKS[name]()
        with open(RESULTS / f"lt_{name}.json", "w", encoding="utf-8", newline="\n") as fh:
            json.dump(res, fh, indent=1)
        print(f"== lt_{name} written", flush=True)


if __name__ == "__main__":
    main()
