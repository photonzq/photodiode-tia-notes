"""List a downloaded model zip, extract it into a target folder (no path traversal),
and report per text file: size, SPICE subcircuit headers, encryption markers, and
any control-language or shell commands that a simulator could execute."""
import re
import sys
import zipfile
from pathlib import Path

zip_path, out_dir = Path(sys.argv[1]), Path(sys.argv[2])
out_dir.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(zip_path) as z:
    for info in z.infolist():
        name = info.filename
        target = (out_dir / name).resolve()
        if not str(target).startswith(str(out_dir.resolve())):
            print("SKIPPED (path traversal):", name)
            continue
        print(f"{info.file_size:9d}  {name}")
        if not info.is_dir():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(z.read(info))

ENC = re.compile(r"\$CDNENCSTART|\$CDNENCFINISH|encrypt|\.protect|\.unprotect", re.I)
CTRL = re.compile(r"^\s*\.control\b|^\s*shell\b|\bsystem\s*\(|^\s*\.exec\b", re.I | re.M)
for f in sorted(out_dir.rglob("*")):
    if not f.is_file():
        continue
    data = f.read_bytes()
    text = data.decode("latin-1")
    printable = sum(c.isprintable() or c in "\r\n\t" for c in text[:20000]) / max(1, min(len(text), 20000))
    subckts = re.findall(r"^\s*\.subckt\s+(\S+)\s+(.*)$", text, flags=re.I | re.M)
    print(f"\n== {f.relative_to(out_dir)}  ({len(data)} bytes, printable {printable:.0%})")
    print("   encryption markers:", len(ENC.findall(text)), "| control/shell lines:", len(CTRL.findall(text)))
    for s in subckts[:6]:
        print("   .SUBCKT", s[0], "pins:", s[1][:160])
