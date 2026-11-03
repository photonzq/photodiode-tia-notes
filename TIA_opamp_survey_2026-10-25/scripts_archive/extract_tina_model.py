"""Extract the SPICE netlist of a TI macromodel from a TINA-TI file (.TSM macro or .TSC
schematic), for parts that TI offers only in that form (Section 10.10).

Usage: python extract_tina_model.py <file.TSM|.TSC> <subckt name> <output .lib>

TINA-TI stores the model's netlist as plain text, one line per record: a zero byte, a
4-byte big-endian length N, then N bytes holding the line and a terminating NUL.  Starting
at the record that
holds '.subckt <name>', the record chain is followed forward to its end, and backward to the
first record that chains into it (the model's header comments).  Nothing is decrypted or
reconstructed: a file whose netlist is not stored this way is reported, not guessed at.
"""
import sys
from pathlib import Path


def record(b, p):
    """(text, next position) of a record at p, or None if p does not start a valid record."""
    if p < 0 or p + 5 > len(b) or b[p] != 0:
        return None
    n = int.from_bytes(b[p + 1:p + 5], "big")
    if not 1 <= n <= 4096 or p + 5 + n > len(b) or b[p + 5 + n - 1] != 0:
        return None
    body = b[p + 5:p + 5 + n - 1]
    if any(c < 9 or 13 < c < 32 or c == 127 for c in body):   # comments may hold Latin-1 characters
        return None
    return body.decode("latin-1"), p + 5 + n


def extract(b, name):
    key = f".subckt {name}".lower().encode()
    i = b.lower().find(key)
    if i < 0:
        raise SystemExit(f"no '.subckt {name}' in the file")
    start = i - 5
    if record(b, start) is None:
        raise SystemExit("the .subckt line is not stored as a length-prefixed record")
    # backward: earliest position whose record chain reaches 'start'
    reach = {start}
    for j in range(start - 1, max(start - 200000, 0) - 1, -1):
        r = record(b, j)
        if r and r[1] in reach:
            reach.add(j)
    first = min(reach)
    lines, p = [], first
    while True:
        r = record(b, p)
        if r is None:
            break
        lines.append(r[0])
        p = r[1]
    return lines


def main():
    src, name, out = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
    lines = extract(src.read_bytes(), name)
    # keep the model only: up to the last '.ends' of the chain
    last = max(k for k, ln in enumerate(lines) if ln.strip().lower().startswith(".ends"))
    lines = lines[:last + 1]
    out.write_text("\n".join(lines) + "\n", encoding="latin-1")
    n_sub = sum(ln.strip().lower().startswith(".subckt") for ln in lines)
    n_end = sum(ln.strip().lower().startswith(".ends") for ln in lines)
    print(f"{src.name}: {len(lines)} lines, {n_sub} .subckt / {n_end} .ends -> {out}")


if __name__ == "__main__":
    main()
