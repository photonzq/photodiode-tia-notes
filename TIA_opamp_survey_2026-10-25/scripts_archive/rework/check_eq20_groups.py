"""Check the grouping of the decompensated parts in Section 6.2.1 against Eq. (20).

For every part of parts_db.py with a minimum stable gain above about 1.5, print the minimum source
capacitance of Eq. (20) at R_F = 2 kOhm, C_T,min [pF] = 318.3 (G_min - 1)^2 / (R_F[kOhm] GBW[MHz]),
against the node capacitance of the baseline, C_T = 1 pF + 0.35 pF + C_CM + C_DIFF, and whether the
part meets the condition.  Used for the logic round of 1 Nov 2026 (Section 6.2.1 lists LMH6624,
THS4021, AD8099, AD8021 and LTC6268-10 as missing Eq. (20), and OPA846, OPA818, OPA847, OPA657,
LT6230-10 and OPA955 as meeting it).

Usage, from scripts_archive/: python rework/check_eq20_groups.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import parts_db as P  # noqa: E402

R_F_KOHM = 2.0
for name, d in P.PARTS.items():
    g, gbw = d.get("g_min"), d.get("gbw")
    if not g or g <= 1.5 or not gbw:
        continue
    ct_min = 318.3 * (g - 1) ** 2 / (R_F_KOHM * gbw / 1e6)
    ct = 1.0 + 0.35 + ((d.get("c_cm") or 0) + (d.get("c_diff") or 0)) * 1e12
    verdict = "meets" if ct >= ct_min else "misses"
    print(f"{name:24s} G_min {g:5.1f}  GBW {gbw / 1e9:5.2f} GHz  C_T,min {ct_min:5.2f} pF  C_T {ct:5.2f} pF  {verdict}")
