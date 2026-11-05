"""Command line:  python -m pcbcap run <file.toml> [--out DIR]

Runs the study described by a TOML file (see config.py for the schema) at below-normal priority and
writes result.json, layout.txt and the figures into the output folder."""
from __future__ import annotations

import argparse
import sys


def main(argv=None) -> int:
    from .study import lower_priority
    lower_priority(2)                 # before NumPy's BLAS starts its threads
    from . import config

    ap = argparse.ArgumentParser(prog="python -m pcbcap", description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="run the study of a TOML file")
    r.add_argument("toml")
    r.add_argument("--out", default=None, help="output folder (default: [output] dir of the file)")
    args = ap.parse_args(argv)
    if args.cmd == "run":
        config.run(config.load(args.toml), args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
