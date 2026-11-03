"""The 50-ohm benchmark: what a TIA has to do to be better than a photodiode pair terminated in 50 ohm.

The benchmark is the photodiode pair terminated in R_0 = 50 ohm at the summing node, followed by an
amplifier (or a 50-ohm instrument) of noise factor F referred to a 50-ohm source, whose input
compresses at P_max.  The photocurrent sees the termination in parallel with the amplifier's
matched input, R_0/2, so the amplifier receives the power I^2 R_0 / 4 from an rms current I, and the
termination is the 50-ohm source its noise figure refers to.  Then

  noise referred to the photocurrent    S_50 = F 4 k_B T / R_0                (A^2/Hz, white)
  largest undistorted tone (rms)        I_max,50 = 2 sqrt(P_max / R_0)

and its dynamic range follows from Eq. (50) of the report like any TIA's.  The optical limit: the
difference current of the balanced pair cannot exceed I_DC = I_1 + I_2 in amplitude, so no light
can produce a tone larger than I_DC / sqrt(2) rms.

For each design and photocurrent it gives
  - the electronic dynamic range of Eq. (50), 20 log10(I_max / i_n,B),
  - the usable dynamic range with the optical limit, 20 log10(min(I_max, I_DC/sqrt 2) / i_n,B),
  - the advantage over the benchmark for the same small signal, 20 log10(i_n,B,50 / i_n,B),
  - P_eq, the compression level at which the benchmark has the design's current ceiling,
  - P_x, the compression level at which the benchmark's electronic dynamic range equals the design's,
  - for each P_max, the photocurrent above which the benchmark's usable dynamic range is larger.

No simulation.  Reads spice/results/dr_comparison.json (the leading op-amp designs at their best
SPICE designs), spice/results/composite_hv_verify.json and composite_hv_tone.json (high-voltage
composite), spice/results/composite_fet_verify.json and data/results/composite_analytical.json (pHEMT
composite); writes data/results/benchmark_50ohm.json.  With --tables it reads that file back and
prints the rows of the report's three benchmark tables (the family, and the designs against it).

Usage: python benchmark_50ohm.py [--tables]
"""
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
KB, Q, T = 1.380649e-23, 1.602176634e-19, 298.15
R0, B = 50.0, 150e6
NF_DB = 2.0
P_MAX_DBM = (-20.0, -10.0, 0.0)
I_DC_POINTS = (0.0, 1e-4, 1e-3, 1e-2, 2e-2)


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def designs():
    """Largest tone (rms, A) at 100 MHz and dark band noise (A rms) of the benchmarked designs."""
    out = {}
    dr = load(ROOT / "spice" / "results" / "dr_comparison.json")["op_amps"]
    for part in ("OPA955", "OPA855", "OPA818"):
        s = dr[part]["spice"]
        i_max = s["vs_idc"]["v_pk_V"] / (np.sqrt(2) * s["vs_idc"]["z_t_ohm"])
        n0 = i_max / 10 ** (s["dr_at_dB"]["0 mA"] / 20)
        out[part] = dict(i_max=i_max, n0=n0, v_pk=s["vs_idc"]["v_pk_V"], z_t=s["vs_idc"]["z_t_ohm"],
                         source="Table A6.33 (SPICE best design)", dr_check=s["dr_at_dB"])
    fet = load(ROOT / "spice" / "results" / "composite_fet_verify.json")["CE3512K2"]
    ana = load(ROOT / "data" / "results" / "composite_analytical.json")["fet"]["CE3512K2"]["best"]["100MHz"]
    out["CE3512K2 composite"] = dict(i_max=ana["v_pk"] / (np.sqrt(2) * ana["zt_ohm"]),
                                     n0=fet["spice_nominal"]["noise_nA"] * 1e-9, v_pk=ana["v_pk"],
                                     z_t=ana["zt_ohm"], source="Table A7.4 (pHEMT composite)")
    hv = load(ROOT / "spice" / "results" / "composite_hv_verify.json")["macromodels, G2 = 5.5"]
    tone = load(ROOT / "spice" / "results" / "composite_hv_tone.json")["macromodels, G2 = 5.5"]["100MHz"]
    out["HV composite (G2 = 5.5)"] = dict(i_max=tone["claim_V"] / (np.sqrt(2) * tone["zt_ohm"]),
                                          n0=hv["spice_nominal"]["noise_nA"] * 1e-9, v_pk=tone["claim_V"],
                                          z_t=tone["zt_ohm"], source="Table A7.7 (OPA859 + THS3491)")
    return out


def shot2(i_dc):
    return 2 * Q * i_dc * B


def noise(n0, i_dc):
    return np.sqrt(n0 ** 2 + shot2(i_dc))


def bench_noise0(nf_db=NF_DB):
    return np.sqrt(10 ** (nf_db / 10) * 4 * KB * T / R0 * B)


def bench_imax(p_dbm):
    return 2 * np.sqrt(10 ** (p_dbm / 10) * 1e-3 / R0)


def dbm(p_w):
    return 10 * np.log10(p_w / 1e-3)


def usable(i_max, n_rms, i_dc):
    return 20 * np.log10(np.minimum(i_max, i_dc / np.sqrt(2)) / n_rms)


def main():
    f = 10 ** (NF_DB / 10)
    n50_0 = bench_noise0()
    res = dict(assumptions=dict(R0_ohm=R0, B_Hz=B, T_K=T, NF_dB=NF_DB, P_max_dBm=list(P_MAX_DBM),
                                termination="R_0 at the photodiodes in parallel with the amplifier's R_0 input"))
    asd_res = np.sqrt(4 * KB * T / R0)
    bench = dict(asd_R0_pA=asd_res * 1e12, asd_with_F_pA=np.sqrt(f) * asd_res * 1e12, band_nA=n50_0 * 1e9,
                 i_cross_mA=2 * f * KB * T / (Q * R0) * 1e3,
                 penalty_vs_RF_dB={"2000": 10 * np.log10(f * 2000 / R0), "1500": 10 * np.log10(f * 1500 / R0)},
                 per_pmax={})
    for p in P_MAX_DBM:
        im = bench_imax(p)
        bench["per_pmax"][f"{p:g} dBm"] = dict(
            i_max_mA_rms=im * 1e3, full_modulation_up_to_mA=np.sqrt(2) * im * 1e3,
            dr_electronic_dB={f"{i*1e3:g} mA": 20 * np.log10(im / noise(n50_0, i)) for i in I_DC_POINTS},
            dr_usable_dB={f"{i*1e3:g} mA": usable(im, noise(n50_0, i), i) for i in I_DC_POINTS if i > 0})
    res["benchmark"] = bench
    print(f"benchmark: sqrt(4kT/50) = {asd_res*1e12:.2f} pA/rtHz; with NF {NF_DB} dB {np.sqrt(f)*asd_res*1e12:.2f}; "
          f"band {n50_0*1e9:.1f} nA rms; equals shot noise at {bench['i_cross_mA']:.2f} mA; penalty over R_F "
          f"{bench['penalty_vs_RF_dB']['2000']:.1f} dB (2 kOhm), {bench['penalty_vs_RF_dB']['1500']:.1f} dB (1.5 kOhm)")
    for k, v in bench["per_pmax"].items():
        print(f"  P_max {k}: I_max {v['i_max_mA_rms']:.3f} mA rms (full modulation to {v['full_modulation_up_to_mA']:.2f} mA); "
              "DR electronic " + "/".join(f"{x:.1f}" for x in v["dr_electronic_dB"].values())
              + " | usable " + "/".join(f"{x:.1f}" for x in v["dr_usable_dB"].values()))
    grid = np.logspace(-6, -1, 5001)
    res["designs"] = {}
    for name, d in designs().items():
        i_max, n0 = d["i_max"], d["n0"]
        row = dict(source=d["source"], v_pk_V=d["v_pk"], z_t_ohm=d["z_t"], i_max_mA_rms=i_max * 1e3,
                   dark_noise_nA=n0 * 1e9, full_modulation_up_to_mA=np.sqrt(2) * i_max * 1e3,
                   p_eq_dBm=dbm(R0 / 4 * i_max ** 2), per_idc={}, crossover_mA={})
        for i in I_DC_POINTS:
            nt, nb = noise(n0, i), noise(n50_0, i)
            row["per_idc"][f"{i*1e3:g} mA"] = dict(
                noise_nA=nt * 1e9, bench_noise_nA=nb * 1e9, dr_electronic_dB=20 * np.log10(i_max / nt),
                small_signal_advantage_dB=20 * np.log10(nb / nt), p_x_dBm=dbm(R0 / 4 * (i_max * nb / nt) ** 2),
                dr_usable_dB=usable(i_max, nt, i) if i > 0 else None)
        for p in P_MAX_DBM:
            diff = usable(bench_imax(p), noise(n50_0, grid), grid) - usable(i_max, noise(n0, grid), grid)
            above = np.nonzero(diff > 0)[0]
            row["crossover_mA"][f"{p:g} dBm"] = float(grid[above[0]] * 1e3) if len(above) else None
        res["designs"][name] = row
        pi = row["per_idc"]
        print(f"{name:24s} I_max {row['i_max_mA_rms']:.3f} mA rms (full modulation to {row['full_modulation_up_to_mA']:.2f} mA), "
              f"dark {row['dark_noise_nA']:.1f} nA, P_eq {row['p_eq_dBm']:.1f} dBm")
        print("    advantage at 0/0.1/1/10/20 mA: " + "/".join(f"{v['small_signal_advantage_dB']:.1f}" for v in pi.values())
              + " dB | P_x: " + "/".join(f"{v['p_x_dBm']:.1f}" for v in pi.values()) + " dBm")
        print("    DR electronic: " + "/".join(f"{v['dr_electronic_dB']:.1f}" for v in pi.values())
              + " | usable (0.1/1/10/20 mA): " + "/".join(f"{v['dr_usable_dB']:.1f}" for v in pi.values() if v['dr_usable_dB'] is not None)
              + " | benchmark overtakes above: " + ", ".join(f"{k}: {('%.2f mA' % v) if v else 'never'}" for k, v in row["crossover_mA"].items()))
        if "dr_check" in d:
            chk = [abs(pi[k]["dr_electronic_dB"] - d["dr_check"][k]) for k in ("0 mA", "0.1 mA", "1 mA", "10 mA")]
            print(f"    check against Table A6.33: largest difference {max(chk):.3f} dB")
    out = ROOT / "data" / "results" / "benchmark_50ohm.json"
    out.write_text(json.dumps(res, indent=1, default=float), encoding="utf-8")
    print("wrote", out.relative_to(ROOT).as_posix())


def tables():
    """Markdown rows of the benchmark tables, from the saved results (rounded as printed)."""
    res = json.loads((ROOT / "data" / "results" / "benchmark_50ohm.json").read_text(encoding="utf-8"))
    f1 = lambda x: f"{x:.1f}".replace("-", "−")
    print("family:")
    for k, v in res["benchmark"]["per_pmax"].items():
        print(f"| {k.replace('-', '−')} | {v['i_max_mA_rms']:.3g} | {v['full_modulation_up_to_mA']:.3g} | "
              + " / ".join(f1(x) for x in v["dr_electronic_dB"].values()) + " | "
              + " / ".join(f1(x) for x in v["dr_usable_dB"].values()) + " |")
    label = {"OPA955": "OPA955", "OPA855": "OPA855", "OPA818": "OPA818",
             "CE3512K2 composite": "pHEMT composite (CE3512K2)",
             "HV composite (G2 = 5.5)": "high-voltage composite (OPA859 + THS3491, $G_2$ = 5.5)"}
    print("designs, ceiling and small signal:")
    for name, r in res["designs"].items():
        pi = r["per_idc"].values()
        print(f"| {label[name]} | {r['dark_noise_nA']:.1f} | {r['i_max_mA_rms']:.3f}; {r['full_modulation_up_to_mA']:.2f} | "
              f"{f1(r['p_eq_dBm'])} | " + " / ".join(f1(p["small_signal_advantage_dB"]) for p in pi) + " | "
              + " / ".join(f1(p["p_x_dBm"]) for p in pi) + " |")
    print("designs, usable dynamic range and crossover:")
    for name, r in res["designs"].items():
        pi = [p for p in r["per_idc"].values() if p["dr_usable_dB"] is not None]
        cross = " / ".join("none" if v is None else f"{v:.2f}" for v in r["crossover_mA"].values())
        print(f"| {label[name]} | " + " / ".join(f1(p["dr_usable_dB"]) for p in pi) + f" | {cross} |")


if __name__ == "__main__":
    import sys
    tables() if "--tables" in sys.argv else main()
