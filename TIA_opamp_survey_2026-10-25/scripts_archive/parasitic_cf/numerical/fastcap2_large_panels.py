"""The large panels in the FastCap 2.0 inputs of the film-free 0402, and what FastCap 2.0 makes of them.

Reads the panel files that fastercap_validation.py writes for FastCap 2.0 (data folder
data/parasitic_cf/fastercap/<case>/fastcap2/) and prints, for each case:

  * the number of panels, the extent of the panel centres along x, y and z, the largest panel (its longer
    diagonal), and the root cube that FastCap 2.0's placeq (mulSetup.c) makes of them: every direction in
    which the centres span less than the largest panel is widened by that panel's diagonal, half on each
    side, and the cube side at level l is 1.01 L0 / 2^l;
  * every panel larger than 2 mm across, with its conductor (or the dielectric interface it lies on), its
    two side lengths and the distance of its centroid from the part;
  * for each of them, the potential that the panel's charge, spread uniformly as FastCap 2.0's panels
    carry it, produces at the part, against the potential of the same charge put at the panel's centroid,
    which is how FastCap 2.0 forms its multipole and local expansions (mulQ2Multi in mulMulti.c,
    mulQ2Local in mulLocal.c).  Both are given as the mean inverse distance <1/r> over the panel, by
    Gauss-Legendre quadrature (two orders, to show convergence), and as 1/|centroid - point|.  The
    equal-area disc on the panel's axis, <1/r> = 2 (sqrt(R^2 + d^2) - d) / R^2 with R = sqrt(A/pi) and d the
    distance from the panel's plane, is printed next to them for comparison.

"The part" is the area-weighted centroid of the panels of conductors A and B; the potentials are also
printed at the centroids of A and of B alone.  Nothing is solved; the script only reads the panel files.

Usage:  python fastcap2_large_panels.py [case ...]
        (default: r0402_nofilm_air_fine_box8 r0402_nofilm_fine_box8)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve()
DATA = HERE.parents[3] / "data" / "parasitic_cf" / "fastercap"
CASES = ("r0402_nofilm_air_fine_box8", "r0402_nofilm_fine_box8")
LARGE = 2e-3          # panels larger than this across (m) are listed
ORDERS = (64, 256)    # Gauss-Legendre points per direction


def read_case(name: str) -> list[dict]:
    """Every panel of case ``name``: its file, its kind (conductor or dielectric), its conductor name
    (or the two permittivities of a dielectric interface) and its corners (m)."""
    out = DATA / name / "fastcap2"
    panels = []
    for line in (out / f"{name}.lst").read_text(encoding="utf-8").splitlines():
        tok = line.split()
        if not tok or tok[0] not in ("C", "D"):
            continue
        if tok[0] == "C":
            shift = np.array([float(x) for x in tok[3:6]])
            media = f"conductor touching {tok[2]}"
        else:
            shift = np.array([float(x) for x in tok[4:7]])
            media = f"dielectric interface {tok[2]}/{tok[3]}"
        for row in (out / tok[1]).read_text(encoding="utf-8").splitlines()[1:]:
            r = row.split()
            if not r or r[0] not in ("Q", "T"):
                continue
            n = 4 if r[0] == "Q" else 3
            corners = np.array([float(x) for x in r[2:2 + 3 * n]]).reshape(n, 3) + shift
            panels.append(dict(file=tok[1], kind=tok[0], media=media,
                               conductor=r[1] if tok[0] == "C" else None, corners=corners))
    return panels


def diagonal(c: np.ndarray) -> float:
    """The panel size FastCap 2.0 uses (max_diag in initcalcp, calcp.c): the longer diagonal of a
    quadrilateral, the longest edge of a triangle."""
    if len(c) == 4:
        return float(max(np.linalg.norm(c[2] - c[0]), np.linalg.norm(c[3] - c[1])))
    return float(max(np.linalg.norm(c[(k + 1) % 3] - c[k]) for k in range(3)))


def area_and_centroid(c: np.ndarray) -> tuple[float, np.ndarray]:
    """Area and area centroid of a flat triangle or quadrilateral (the latter as two triangles)."""
    tris = [c] if len(c) == 3 else [c[[0, 1, 2]], c[[0, 2, 3]]]
    a = np.array([0.5 * np.linalg.norm(np.cross(t[1] - t[0], t[2] - t[0])) for t in tris])
    g = np.array([t.mean(axis=0) for t in tris])
    return float(a.sum()), (a[:, None] * g).sum(axis=0) / a.sum()


def mean_inverse_distance(c: np.ndarray, x: np.ndarray, order: int) -> float:
    """<1/r> over a quadrilateral (bilinear map) or triangle (collapsed quadrilateral) seen from x."""
    if len(c) == 3:
        c = np.array([c[0], c[1], c[2], c[2]])
    t, w = np.polynomial.legendre.leggauss(order)
    u, v = np.meshgrid(t, t, indexing="ij")
    W = np.outer(w, w)
    N = np.stack([(1 - u) * (1 - v), (1 + u) * (1 - v), (1 + u) * (1 + v), (1 - u) * (1 + v)], axis=-1) / 4
    dNu = np.stack([-(1 - v), (1 - v), (1 + v), -(1 + v)], axis=-1) / 4
    dNv = np.stack([-(1 - u), -(1 + u), (1 + u), (1 - u)], axis=-1) / 4
    p = N @ c
    J = np.linalg.norm(np.cross(dNu @ c, dNv @ c), axis=-1)
    r = np.linalg.norm(p - x, axis=-1)
    return float((W * J / r).sum() / (W * J).sum())


def disc_on_axis(c: np.ndarray, x: np.ndarray) -> float:
    """<1/r> of the equal-area disc, seen from the point at x's distance from the panel's plane."""
    area, g = area_and_centroid(c)
    nrm = np.cross(c[1] - c[0], c[2] - c[0])
    nrm /= np.linalg.norm(nrm)
    d = abs(float(np.dot(x - g, nrm)))
    R2 = area / np.pi
    return 2.0 * (np.sqrt(R2 + d * d) - d) / R2


def report(name: str) -> None:
    panels = read_case(name)
    cent = np.array([area_and_centroid(p["corners"])[1] for p in panels])
    diag = np.array([diagonal(p["corners"]) for p in panels])
    lo, hi = cent.min(axis=0), cent.max(axis=0)
    span = hi - lo
    tile = float(diag.max())
    widened = np.where(span < tile, span + tile, span)
    L0 = float(widened.max())
    print(f"\n{name}: {len(panels)} panels "
          f"({sum(p['kind'] == 'C' for p in panels)} conductor, {sum(p['kind'] == 'D' for p in panels)} dielectric)")
    print("  centres span x, y, z = " + ", ".join(f"{s * 1e3:.3f}" for s in span) + " mm; "
          f"largest panel {tile * 1e3:.3f} mm across")
    print("  after placeq's widening: " + ", ".join(f"{s * 1e3:.3f}" for s in widened) + f" mm; root cube L0 = {L0 * 1e3:.3f} mm")
    for level in (8, 9):
        print(f"  cube side at level {level}: 1.01 x {L0 * 1e3:.3f} mm / 2^{level} = {1.01 * L0 / 2 ** level * 1e6:.1f} um")

    def centroid_of(names: tuple[str, ...]) -> np.ndarray:
        sel = [area_and_centroid(p["corners"]) for p in panels if p["conductor"] in names]
        a = np.array([s[0] for s in sel])
        g = np.array([s[1] for s in sel])
        return (a[:, None] * g).sum(axis=0) / a.sum()

    points = {"part (A and B)": centroid_of(("A", "B")), "A": centroid_of(("A",)), "B": centroid_of(("B",))}
    for k, x in points.items():
        print(f"  centroid of {k}: (" + ", ".join(f"{v * 1e3:.3f}" for v in x) + ") mm")
    x0 = points["part (A and B)"]
    big = [i for i in range(len(panels)) if diag[i] > LARGE]
    print(f"  {len(big)} panels larger than {LARGE * 1e3:.0f} mm across:")
    print("    owner | sides (mm) | centroid (mm) | |centroid - part| (mm) | 1/<1/r> quadrature "
          f"{ORDERS[0]}, {ORDERS[1]} (mm) | 1/<1/r> disc on axis (mm) | point charge / uniform charge")
    for i in sorted(big, key=lambda j: np.linalg.norm(cent[j] - x0)):
        p = panels[i]
        c = p["corners"]
        sides = sorted({round(float(np.linalg.norm(c[(k + 1) % len(c)] - c[k])) * 1e3, 3) for k in range(len(c))})
        owner = p["conductor"] if p["kind"] == "C" else p["media"]
        dist = float(np.linalg.norm(cent[i] - x0))
        q = [mean_inverse_distance(c, x0, n) for n in ORDERS]
        disc = disc_on_axis(c, x0)
        print(f"    {owner:28s} | {' x '.join(f'{s:.3f}' for s in sides):15s} | "
              f"({', '.join(f'{v * 1e3:7.3f}' for v in cent[i])}) | {dist * 1e3:6.3f} | "
              f"{1e3 / q[0]:7.3f}, {1e3 / q[1]:7.3f} | {1e3 / disc:7.3f} | {1 / dist / q[1]:.3f}")
        for k in ("A", "B"):
            xk = points[k]
            dk = float(np.linalg.norm(cent[i] - xk))
            qk = mean_inverse_distance(c, xk, ORDERS[1])
            print(f"      seen from the centroid of {k}: |centroid - {k}| = {dk * 1e3:.3f} mm, "
                  f"1/<1/r> = {1e3 / qk:.3f} mm, ratio {1 / dk / qk:.3f}")


def main(argv: list[str]) -> int:
    for name in (argv or list(CASES)):
        report(name)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
