"""Why two ADI macromodels (AD8099, ADA4899) stop with 'matrix is singular' in AC runs
(Section 10.10).

Usage: python adi_open_loop_probe.py <scripts_archive folder> [<ngspice library>]

Runs a unity-gain buffer and the open-loop fixture of spice_tia_checks.py ('aol': 1-GH DC
feedback, 1-kF input capacitor) for AD8099 and ADA4899, with an 'ac' sweep or a 'noise'
sweep, each deck in its own work folder under ./adi_open_loop_probe/.  Prints whether the
sweep ran and, for 'ac', |A| (or the buffer's gain) at 100 MHz.
"""
import re
import shutil
import sys
from pathlib import Path

import numpy as np

archive = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(archive))
from ngspice_shared import NgSpice                             # noqa: E402
from spice_tia_checks import VENDOR_MODELS, translate_model    # noqa: E402

work = Path("adi_open_loop_probe").resolve()
models = archive.parent / "spice" / "models"
FIXTURE = "LB out inm 1G\nCB inm 0 1k\n"

# name: (inverting-input node, fixture lines, analysis); the options line is per run
CASES = {
    "buffer, noise (as in 'smoke')": ("out", "", "noise"),
    "buffer, ac": ("out", "", "ac"),
    "buffer, op then ac": ("out", "", "op+ac"),
    "open-loop fixture, ac (as in 'aol')": ("inm", FIXTURE, "ac"),
    "open-loop fixture, noise": ("inm", FIXTURE, "noise"),
}
OPTIONS = {"": "", "rshunt 1e12": ".options rshunt=1e12\n", "klu": ".options klu\n"}


def deck(part, inm, fixture, analysis, opts=""):
    m = VENDOR_MODELS[part]
    lib = Path(m["lib"]).name
    inst = m["inst"].format(p="inp", n=inm, o="out")
    ctl = {"noise": "noise v(out) Vs dec 10 1k 1G\nsetplot noise1\nwrdata out.txt onoise_spectrum\n",
           "ac": "ac dec 10 1k 1G\nwrdata out.txt real(v(out)) imag(v(out))\n",
           "op+ac": "op\nac dec 10 1k 1G\nwrdata out.txt real(v(out)) imag(v(out))\n"}[analysis]
    return (f"* {part} probe\n.include {lib}\n.temp 25\nVCC vcc 0 DC 5\nVEE vee 0 DC -5\n"
            f"XU1 {inst}\nVs src 0 DC 0 AC 1\nRS src inp 1m\n{fixture}RL out 0 {m['rl']}\n{opts}"
            f".control\nset wr_singlescale\nset wr_vecnames\n{ctl}.endc\n.end\n")


LIMIT = re.compile(r"limit\(([^,]+),([^,]+),([^)]+)\)", re.I)


def limit_as_minmax(text):
    """PSpice LIMIT(x, a, b) as min(max(x, min(a, b)), max(a, b)); the arguments are split at
    commas outside parentheses, so V(200,110) stays whole."""
    out, i, low = [], 0, text.lower()
    while True:
        j = low.find("limit(", i)
        if j < 0:
            out.append(text[i:])
            return "".join(out)
        out.append(text[i:j])
        k, depth, args, start = j + 6, 1, [], j + 6
        while depth:
            c = text[k]
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
            elif c == "," and depth == 1:
                args.append(text[start:k])
                start = k + 1
            k += 1
        args.append(text[start:k - 1])
        x, a, b = args
        out.append(f"min(max({x},min({a},{b})),max({a},{b}))")
        i = k


def run_case(part, fix, tag, inm, fixture, analysis, opts=""):
    folder = work / f"{part}_{int(fix)}_{tag}"
    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir(parents=True)
    src = models / VENDOR_MODELS[part]["lib"]
    text = translate_model(src.read_text(encoding="latin-1"))
    if fix:
        text = limit_as_minmax(text)
    (folder / src.name).write_text(text, encoding="latin-1")
    (folder / "deck.cir").write_text(deck(part, inm, fixture, analysis, opts), encoding="utf-8")
    ng = NgSpice(sys.argv[2] if len(sys.argv) > 2 else None)
    out = ng.run_deck(folder / "deck.cir")
    (folder / "ngspice.log").write_text(out, encoding="utf-8")
    res = "no output"
    if (folder / "out.txt").exists():
        d = np.loadtxt(folder / "out.txt", skiprows=1, ndmin=2)
        k = int(np.argmin(abs(d[:, 0] - 1e8)))
        res = (f"output at 100 MHz {20 * np.log10(abs(d[k, 1] + 1j * d[k, 2])):.1f} dB" if d.shape[1] > 2
               else f"output noise at 100 MHz {d[k, 1] * 1e9:.2f} nV/rtHz")
    return res, "singular" in out.lower()


def main():
    variants = [("model as translated", False), ("limit() as min/max", True)]
    for part in ("AD8099", "ADA4899-1"):
        for vname, fix in variants:
            for i, (name, (inm, fixture, analysis)) in enumerate(CASES.items()):
                res, sing = run_case(part, fix, i, inm, fixture, analysis)
                print(f"{part:10s} {name + ' [' + vname + ']':58s}: {res}; singular matrix reported: {sing}")
        # the AC sweeps again, model as translated, with each option
        for oname, opts in OPTIONS.items():
            if not opts:
                continue
            for i, (name, (inm, fixture, analysis)) in enumerate(CASES.items()):
                if analysis == "noise":
                    continue
                res, sing = run_case(part, False, f"{oname.split()[0]}_{i}", inm, fixture, analysis, opts)
                print(f"{part:10s} {name + ' [.options ' + oname + ']':58s}: {res}; singular matrix reported: {sing}")


if __name__ == "__main__":
    main()
