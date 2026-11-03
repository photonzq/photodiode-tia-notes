import pathlib
import sys

p = pathlib.Path(sys.argv[1])
s = p.read_text(encoding="utf-8")
n = s.count("\times")  # a TAB followed by "imes": a lost backslash-t
s = s.replace("\times", r"\times")
p.write_text(s, encoding="utf-8", newline="")
print(p.name, "fixed", n)
