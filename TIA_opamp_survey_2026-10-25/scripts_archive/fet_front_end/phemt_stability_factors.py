"""Rollett's K and the Edwards-Sinsky mu of a transistor from its vendor S-parameter file (survey
Section 11.5: CE3512K2 at 2 V, 10 mA).  mu < 1 or K < 1 means the transistor alone can oscillate
with some passive source and load terminations at that frequency.

  K  = (1 - |S11|^2 - |S22|^2 + |D|^2) / (2 |S12 S21|),   D = S11 S22 - S12 S21
  mu = (1 - |S11|^2) / (|S22 - D conj(S11)| + |S12 S21|)

usage: python phemt_stability_factors.py <zip of Touchstone files> <part of a file name>
e.g.   python phemt_stability_factors.py ../../datasheets/fet_front_end/CE3512K2_CEL_s2p.zip 2V_10mA
"""
import cmath
import math
import sys
import zipfile


def read_s2p(text):
    hdr = [ln for ln in text.splitlines() if ln.strip().startswith("#")][0].upper().split()
    scale = {"HZ": 1, "KHZ": 1e3, "MHZ": 1e6, "GHZ": 1e9}[next(t for t in hdr if t in ("HZ", "KHZ", "MHZ", "GHZ"))]
    fmt = next((t for t in hdr if t in ("MA", "DB", "RI")), "MA")
    rows = []
    for ln in text.splitlines():
        s = ln.strip()
        if not s or s.startswith(("!", "#")):
            continue
        v = [float(x) for x in s.split()[:9]]
        if len(v) < 9:
            continue
        if fmt == "MA":
            sp = [cmath.rect(v[i], math.radians(v[i + 1])) for i in (1, 3, 5, 7)]
        elif fmt == "DB":
            sp = [cmath.rect(10 ** (v[i] / 20), math.radians(v[i + 1])) for i in (1, 3, 5, 7)]
        else:
            sp = [complex(v[i], v[i + 1]) for i in (1, 3, 5, 7)]
        rows.append((v[0] * scale, *sp))          # f, S11, S21, S12, S22 (Touchstone order)
    return rows


def main():
    zpath, key = sys.argv[1], sys.argv[2]
    with zipfile.ZipFile(zpath) as zf:
        name = next(n for n in zf.namelist() if key in n)
        rows = read_s2p(zf.read(name).decode("latin-1"))
    print(name)
    out = []
    for f, s11, s21, s12, s22 in rows:
        d = s11 * s22 - s12 * s21
        k = (1 - abs(s11) ** 2 - abs(s22) ** 2 + abs(d) ** 2) / (2 * abs(s12 * s21))
        mu = (1 - abs(s11) ** 2) / (abs(s22 - d * s11.conjugate()) + abs(s12 * s21))
        out.append((f, k, mu))
    below = [r for r in out if r[2] < 1]
    print(f"{out[0][0]/1e9:.1f}-{out[-1][0]/1e9:.1f} GHz, {len(out)} points; mu < 1 at {len(below)} of them"
          + (f", from {below[0][0]/1e9:.1f} to {below[-1][0]/1e9:.1f} GHz" if below else ""))
    i = min(range(len(out)), key=lambda j: out[j][2])
    print(f"smallest mu {out[i][2]:.3f} at {out[i][0]/1e9:.1f} GHz")
    for x in (2e9, 5e9, 10e9, 20e9):
        j = min(range(len(out)), key=lambda m: abs(out[m][0] - x))
        print(f"  {out[j][0]/1e9:5.1f} GHz: K {out[j][1]:.3f}, mu {out[j][2]:.3f}")


if __name__ == "__main__":
    main()
