"""Secondary tables for the report, derived from results.json.

Usage: python report_numbers.py <results_dir> <out_md>

1. Noise components at 100 and 200 MHz (flat design, central model; FET and
   rising-i_n parts also give the 'high' total).
2. Band-integrated input noise (rms) over 10-150 and 10-200 MHz.
3. All noise referred to the photocurrent:
   (a) total input-referred noise at 100 MHz for I_DC = I_1 + I_2 = 0, 0.1, 1, 10
       and 20 mA (20 mA is 10 mA in each diode of a balanced pair);
   (b) output noise divided by the in-band gain R_F (pA/rtHz) at the spot
       frequencies, and the unfiltered output rms divided by R_F (nA rms);
   (c) OPA855 at 2 kOhm: the instrument noise, referred to the input, that
       degrades the TIA floor by <= 0.5 dB, with its noise figure and the TIA
       noise at the instrument in dBm/Hz as translations:
       i_inst[pA] = 0.907 * 10^(NF/20) / |Z_T|[kohm].
4. Largest RF photocurrent at 100 MHz (V_pk / |Z_T|) and the modulation depth
   it represents at I_DC = 1 and 10 mA (DC cancelled).
"""
import json
import math
import sys
from pathlib import Path

K_B, T, Q_E = 1.380649e-23, 298.15, 1.602176634e-19

PARTS_SHOWN = ["OPA855", "OPA858", "OPA955", "LMH6629 (COMP HI)", "OPA856", "OPA859", "THS4304",
               "OPA843", "OPA846", "OPA818"]


def fmt(x, nd=2):
    return "–" if x is None else f"{x:.{nd}f}"


def main(results_dir, out_md):
    r = json.load(open(Path(results_dir) / "results.json", encoding="utf-8"))
    lines = []
    for R_F in (2000, 1500):
        key = f"RF_{R_F}"
        lines.append(f"\n## Noise components, {R_F/1000:g} kOhm, flat design (pA/rtHz)\n")
        lines.append("| Part | Frequency | $R_F$ Johnson | $i_n$ | $e_n$ term | FET/rising-$i_n$ extra (high) | Total central (high) |")
        lines.append("|---|---|---|---|---|---|---|")
        for name in PARTS_SHOWN:
            nb = r[name][key]["noise"].get("flat")
            if not nb:
                continue
            c = nb["central"]
            hi = nb.get("high")
            for j, f in ((3, 100), (5, 200)):
                parts = c["parts_pA"]
                extra = hi["parts_pA"]["fet_hf"][j] if hi else None
                tot_hi = hi["i_in_pA"][j] if hi else None
                lines.append(f"| {name} | {f} MHz | {parts['RF'][j]:.2f} | {parts['i_n'][j]:.2f} | {parts['e_n'][j]:.2f} | "
                             f"{fmt(extra)} | {c['i_in_pA'][j]:.2f}" + (f" ({tot_hi:.2f})" if tot_hi else "") + " |")
        lines.append(f"\n## Band-integrated input noise, {R_F/1000:g} kOhm, flat design (nA rms)\n")
        lines.append("| Part | 10–150 MHz central (high) | 10–200 MHz central (high) | $R_F$ alone, 10–150 / 10–200 MHz |")
        lines.append("|---|---|---|---|")
        i_rf = math.sqrt(4 * 1.380649e-23 * 298.15 / R_F)
        ref150, ref200 = i_rf * math.sqrt(140e6) * 1e9, i_rf * math.sqrt(190e6) * 1e9
        for name in PARTS_SHOWN:
            nb = r[name][key]["noise"].get("flat")
            if not nb:
                continue
            c, hi = nb["central"], nb.get("high")
            s150 = f"{c['band_rms_nA']['10-150 MHz']:.1f}" + (f" ({hi['band_rms_nA']['10-150 MHz']:.1f})" if hi else "")
            s200 = f"{c['band_rms_nA']['10-200 MHz']:.1f}" + (f" ({hi['band_rms_nA']['10-200 MHz']:.1f})" if hi else "")
            lines.append(f"| {name} | {s150} | {s200} | {ref150:.1f} / {ref200:.1f} |")
        lines.append(f"\n## Total input-referred noise at 100 MHz, {R_F/1000:g} kOhm, flat design (pA/rtHz)\n")
        lines.append("| Part | dark | 0.1 mA | 1 mA | 10 mA | 20 mA (10 mA per diode) |")
        lines.append("|---|---|---|---|---|---|")
        for name in PARTS_SHOWN:
            nb = r[name][key]["noise"].get("flat")
            if not nb:
                continue
            c = nb["central"]
            vals = [c["i_in_pA"][3]] + [c["with_dc"][k]["total_pA"][3] for k in ("0.1 mA", "1 mA", "10 mA")]
            vals.append(math.sqrt(vals[-1] ** 2 + 2 * Q_E * 10e-3 * 1e24))     # +10 mA of shot noise, pA^2/Hz
            lines.append(f"| {name} | " + " | ".join(f"{v:.2f}" for v in vals) + " |")
        lines.append(f"\n## Output noise divided by R_F, {R_F/1000:g} kOhm, flat design, dark "
                     "(pA/rtHz at 1, 10, 50, 100, 150, 200 MHz; unfiltered output rms / R_F in nA rms)\n")
        lines.append("| Part | 1 MHz | 10 MHz | 50 MHz | 100 MHz | 150 MHz | 200 MHz | Unfiltered rms / $R_F$ (nA) |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for name in PARTS_SHOWN:
            nb = r[name][key]["noise"].get("flat")
            if not nb:
                continue
            c = nb["central"]
            v = [x / (R_F / 1e3) for x in c["v_out_nV"]]
            rms = nb["v_out_rms_unfiltered_mV"] / (R_F / 1e3) * 1e3
            lines.append(f"| {name} | " + " | ".join(f"{x:.2f}" for x in v) + f" | {rms:.0f} |")
        if R_F == 2000:
            c = r["OPA855"][key]["noise"]["flat"]["central"]
            zt = c["v_out_nV"][3] / c["i_in_pA"][3]                             # kOhm at 100 MHz
            lines.append(f"\n## OPA855, 2 kOhm, 100 MHz: instrument noise for <= 0.5 dB degradation "
                         f"(|Z_T| = {zt:.3f} kOhm)\n")
            lines.append("| I_1 + I_2 | TIA input noise (pA/rtHz) | allowed instrument noise, input-referred (pA/rtHz) | "
                         "equivalent NF (dB) | TIA noise at the instrument (dBm/Hz) |")
            lines.append("|---|---|---|---|---|")
            vals = [c["i_in_pA"][3]] + [c["with_dc"][k]["total_pA"][3] for k in ("0.1 mA", "1 mA", "10 mA")]
            vals.append(math.sqrt(vals[-1] ** 2 + 2 * Q_E * 10e-3 * 1e24))
            k_inst = 2 * math.sqrt(K_B * T * 50.0) * 1e9                        # nV/rtHz: 0.907 at 25 C
            p_kt = 10 * math.log10(K_B * T / 1e-3)                               # dBm/Hz: -173.86
            for lab, v in zip(("dark", "0.1 mA", "1 mA", "10 mA", "20 mA"), vals):
                i_all = v * math.sqrt(10 ** 0.05 - 1)
                nf = 20 * math.log10(i_all * zt / k_inst)
                p_tia = 10 * math.log10((v * zt * 1e-9 / 2) ** 2 / 50.0 / 1e-3)
                lines.append(f"| {lab} | {v:.2f} | {i_all:.2f} | {nf:.1f} | {p_tia:.1f} |")
            lines.append(f"\nConstants: 2 sqrt(k_B T x 50 ohm) = {k_inst:.4f} nV/rtHz; k_B T = {p_kt:.2f} dBm/Hz.")
        lines.append(f"\n## Largest RF photocurrent at 100 MHz, DC cancelled, {R_F/1000:g} kOhm, flat design\n")
        lines.append("| Part | $V_{pk}$ (V), limit | $I_{pk}$ (mA) | Modulation depth at 1 mA / 10 mA |")
        lines.append("|---|---|---|---|")
        for name in PARTS_SHOWN:
            dr = r[name][key]["dr"].get("flat")
            if not dr:
                continue
            a = dr["ac"]["high-Z"]["100 MHz"]
            ipk = a["i_ph_pk_mA"]
            lines.append(f"| {name} | {a['v_pk_V']:.2f}, {a['limiter']} | {ipk:.2f} | "
                         f"{min(ipk / 1.0, 9.99) * 100:.0f} % / {ipk / 10.0 * 100:.1f} % |")
    Path(out_md).write_text("# Secondary tables generated from results.json\n" + "\n".join(lines) + "\n",
                            encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
