"""The two design examples of Chapter 4 at the low end of the band: 1/f corners, spot noise and band noise.

Usage: python case_low_end.py

Why this script exists
----------------------
Eq. (33) of the note takes the amplifier's noise densities at their white levels. Below about 100 kHz
both densities rise, and this script evaluates, in closed form, what that does to the OPA855 and OPA846
designs at 2 kOhm (Sections 4.2 and 4.4), down to 100 Hz.

The form of the 1/f noise. As in Section 6.9, each density has one corner:
    e_n^2(f) = e_w^2 (1 + f_ce / f),     i_n^2(f) = i_w^2 (1 + f_ci / f),
with e_w and i_w the white levels of Table 4.1 and f_ce, f_ci the corners recorded in data/specs/<part>.json
(derived from the datasheets' noise curves; this script checks the form against every curve point).

The design's noise at the low end. Below about 100 kHz the capacitive term of Eq. (33),
(2 pi f e_n C_tot)^2, is negligible: at 100 kHz it is (6.283e-3 x 1.2 x 0.1 x 5.90)^2 = 2e-5 pA^2/Hz for
OPA846 against a floor of 16 pA^2/Hz. Eq. (33) then reads, in pA^2/Hz with f in kHz,
    i_eq^2(f) = S_0 + K / f,
    S_0 = 16.47 / R_F + i_w^2 + e_w^2 / R_F^2 + 320.4 I_DC          (the white floor at the low end),
    K   = i_w^2 f_ci + e_w^2 f_ce / R_F^2                            (the 1/f coefficient, pA^2/Hz x kHz),
with R_F in kOhm, e in nV/rtHz, i in pA/rtHz and I_DC in mA. The 1/f part equals the white floor, and
the noise power has doubled, at the design's own corner
    f_c = K / S_0,
which falls as the shot noise of I_DC raises S_0.

The band noise. Integrated from a low edge f_low to the band edge B, the 1/f part adds
    Delta I^2 = K ln(B / f_low)      (K in pA^2/Hz x Hz = pA^2)
to the band noise in power; with B = 150 MHz it is compared with the band noise of Table A4.1
(our model: 50.2 nA rms for OPA855 and 69.0 nA rms for OPA846, both integrated from 0 to 150 MHz).

Printed: the curve check, S_0, K and f_c at I_DC = 0, 0.1, 1 and 10 mA, the spot noise at 100 Hz, 1 kHz
and 10 kHz against the floor (and the curves' own values for comparison with Table A6.37), the band
increment for f_low = 100 Hz, 1 kHz and 10 kHz, and the frequency where the two designs' noise is equal.
"""
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPECS = HERE.parent / "data" / "specs"
R_F = 2.0                                   # kOhm
FLOOR_R = 16.47 / R_F                       # 4 k T / R_F in pA^2/Hz at 25 degC (Eq. (33))
SHOT = 320.4                                # 2 q I_DC in pA^2/Hz per mA (Eq. (33))
B = 150e3                                   # band edge in kHz
DESIGNS = {  # white levels of Table 4.1, C_tot of Sections 4.2 and 4.4, band noise of Table A4.1 (model)
    "OPA855": dict(e_w=0.99, i_w=2.6, c_tot=2.35, band_nA=50.2),
    "OPA846": dict(e_w=1.2, i_w=2.8, c_tot=5.90, band_nA=69.0),
}
I_DC = (0.0, 0.1, 1.0, 10.0)                # mA
SPOTS = (0.1, 1.0, 10.0)                    # kHz


def corners(part):
    spec = json.loads((SPECS / f"{part}.json").read_text(encoding="utf-8"))
    return (spec["voltage_noise"]["one_over_f_corner_Hz"] / 1e3, spec["current_noise"]["one_over_f_corner_Hz"] / 1e3,
            [(p["f_Hz"] / 1e3, p["nV_rtHz"]) for p in spec["voltage_noise"]["curve_points"]],
            [(p["f_Hz"] / 1e3, p["pA_rtHz"]) for p in spec["current_noise"]["curve_points"]])


def curve_at(points, f):
    """Log-log interpolation inside a digitized curve; None outside it."""
    pts = sorted(points)
    if not pts[0][0] <= f <= pts[-1][0]:
        return None
    for (f0, y0), (f1, y1) in zip(pts, pts[1:]):
        if f0 <= f <= f1:
            t = math.log(f / f0) / math.log(f1 / f0)
            return math.exp(math.log(y0) + t * math.log(y1 / y0))
    return pts[-1][1]


def noise(d, fce, fci, f, idc, cap=True):
    """Input-referred noise in pA^2/Hz at f (kHz): Eq. (33) with the 1/f forms."""
    en2 = d["e_w"] ** 2 * (1 + fce / f)
    in2 = d["i_w"] ** 2 * (1 + fci / f)
    capt = (6.283e-3 * math.sqrt(en2) * (f / 1e3) * d["c_tot"]) ** 2 if cap else 0.0
    return FLOOR_R + in2 + en2 / R_F ** 2 + capt + SHOT * idc


def main():
    out = {}
    for part, d in DESIGNS.items():
        fce, fci, vpts, ipts = corners(part)
        print(f"===== {part}: e_w = {d['e_w']} nV/rtHz, i_w = {d['i_w']} pA/rtHz, f_ce = {fce:g} kHz, f_ci = {fci:g} kHz")
        worst = 0.0
        for kind, pts, w, fc in (("e_n", vpts, d["e_w"], fce), ("i_n", ipts, d["i_w"], fci)):
            devs = [20 * math.log10(w * math.sqrt(1 + fc / f) / y) for f, y in pts if f <= 1e3]
            worst = max(worst, max(abs(x) for x in devs))
            print(f"  {kind}: single-corner form against the curve up to 1 MHz: "
                  + ", ".join(f"{x:+.2f}" for x in devs) + " dB")
        K = d["i_w"] ** 2 * fci + d["e_w"] ** 2 * fce / R_F ** 2
        print(f"  K = {d['i_w']}^2 x {fci:g} + {d['e_w']}^2 x {fce:g} / {R_F:g}^2 = "
              f"{d['i_w'] ** 2 * fci:.2f} + {d['e_w'] ** 2 * fce / R_F ** 2:.3f} = {K:.2f} pA^2/Hz x kHz")
        rec = dict(K=K, corners={}, spots={}, band={})
        for idc in I_DC:
            s0 = FLOOR_R + d["i_w"] ** 2 + d["e_w"] ** 2 / R_F ** 2 + SHOT * idc
            fc = K / s0
            rec["corners"][idc] = dict(S0=s0, f_c_kHz=fc)
            floor = FLOOR_R + SHOT * idc
            spots = []
            for f in SPOTS:
                tot = noise(d, fce, fci, f, idc)
                en_c, in_c = curve_at(vpts, f), curve_at(ipts, f)
                curve_txt = ""
                if en_c is not None and in_c is not None:
                    tot_c = FLOOR_R + in_c ** 2 + en_c ** 2 / R_F ** 2 + SHOT * idc
                    curve_txt = f" (curves {10 * math.log10(tot_c / floor):.1f} dB)"
                spots.append(f"{f:g} kHz {math.sqrt(tot):.2f} pA/rtHz, +{10 * math.log10(tot / floor):.1f} dB{curve_txt}")
                rec["spots"].setdefault(idc, {})[f] = dict(pA=math.sqrt(tot), dB=10 * math.log10(tot / floor))
            print(f"  I_DC = {idc:g} mA: S_0 = {s0:.2f} pA^2/Hz, f_c = K/S_0 = {fc:.3g} kHz; above the floor of "
                  f"R_F and shot noise ({math.sqrt(floor):.2f} pA/rtHz): " + "; ".join(spots))
        for flow in (0.1, 1.0, 10.0):
            d_i2 = K * 1e3 * math.log(B / flow) / 1e6                # nA^2
            tot = math.sqrt(d["band_nA"] ** 2 + d_i2)
            rec["band"][flow] = dict(dI2_nA2=d_i2, total_nA=tot, dB=20 * math.log10(tot / d["band_nA"]))
            print(f"  band from {flow:g} kHz to 150 MHz: K ln(B/f_low) = {K * 1e3:.4g} pA^2 x {math.log(B / flow):.3f} = "
                  f"{d_i2:.4g} nA^2, sqrt({d['band_nA']}^2 + {d_i2:.3g}) = {tot:.3f} nA rms, +{20 * math.log10(tot / d['band_nA']):.3f} dB")
        out[part] = rec
    # the frequency where the two designs' noise is equal, in the dark
    a, b = DESIGNS["OPA855"], DESIGNS["OPA846"]
    ca, cb = corners("OPA855")[:2], corners("OPA846")[:2]
    lo, hi = 1.0, 1e5
    for _ in range(200):
        mid = math.sqrt(lo * hi)
        if noise(a, *ca, mid, 0.0) > noise(b, *cb, mid, 0.0):
            lo = mid
        else:
            hi = mid
    print(f"===== equal noise in the dark at {lo:.4g} kHz: OPA855 {math.sqrt(noise(a, *ca, lo, 0)):.3f}, "
          f"OPA846 {math.sqrt(noise(b, *cb, lo, 0)):.3f} pA/rtHz; OPA846 is quieter below, OPA855 above")
    return out


if __name__ == "__main__":
    main()
