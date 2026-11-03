"""Repair LaTeX backslash sequences that a shell heredoc turned into control
characters: BEL+'pprox' -> \\approx, TAB+'imes' -> \\times, FF+'rac' ->
\\frac, VT+... (none expected), BS+... (none expected)."""
import pathlib
import sys

FIXES = {
    "\x07pprox": r"\approx",
    "\times": r"\times",
    "\x0crac": r"\frac",
    "\x08eta": r"\beta",
}
for name in sys.argv[1:]:
    p = pathlib.Path(name)
    s = p.read_text(encoding="utf-8")
    total = 0
    for bad, good in FIXES.items():
        total += s.count(bad)
        s = s.replace(bad, good)
    p.write_text(s, encoding="utf-8", newline="")
    left = [c for c in s if ord(c) < 32 and c != "\n"]
    print(p.name, "fixed", total, "control chars left", len(left))
