# Exploratory check for Section 4.11.9 of the note, kept as the record: the first five SPICE pulses against the model on its own fit, drawn; superseded by Figure 14. It reads the first version of spice/results/board_pulses.json.
# Run from this folder.
"""Scratch: SPICE pulses against the time-domain model on its own fit (macromodel's A_-), to look at the shapes."""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ARCH))
import tia_pulse_response as tp  # noqa: E402

OUT = Path(__file__).resolve().parent
R_F = 1500.0
sp = json.loads((ARCH.parent / "spice" / "results" / "board_pulses.json").read_text(encoding="utf-8"))
d = json.loads((ARCH.parent / "data" / "results" / "tia_pulse_response_opa846_1k5.json").read_text(encoding="utf-8"))
fit = d["fits"]["macromodel A_-"]
fr = fit["rational"]
rol = tp.RationalOpenLoop(fr["a0"], fr["f_p1_Hz"], fr["zeros_Hz"], fr["poles_Hz"], fr["tau_s"], fr["n_delay"], fr["note"])
runs = sp["pulses"]["runs"]["board"]
qs = [r["q"] for r in runs]
t, vo, vn, x1, v_ov = tp.simulate(rol, R_F, fit["ct"], fit["cf"], 686.5e6, 3.3, qs, window=45e-9, dt=1e-12, keep_every=2)

fig, ax = plt.subplots(2, 2, figsize=(10, 7))
r0 = runs[0]
ax[0, 0].plot(np.array(r0["t"]) * 1e9, np.array(r0["vo"]) / r0["q"] * 1e-12, "k-", label="SPICE")
ax[0, 0].plot(t * 1e9, vo[0] / qs[0] * 1e-12, "r--", label="model, own fit")
ax[0, 0].set_xlim(-0.5, 40); ax[0, 0].set_title("0.01 pC, V per pC"); ax[0, 0].legend()
for k, c in ((2, "C0"), (3, "C1"), (4, "C2")):
    r = runs[k]
    ax[0, 1].plot(np.array(r["t"]) * 1e9, r["vo"], "-", color=c, label=f"SPICE {r['q'] * 1e12:g} pC")
    ax[0, 1].plot(t * 1e9, vo[k], "--", color=c)
    ax[1, 0].plot(np.array(r["t"]) * 1e9, np.array(r["vn"]) * 1e3, "-", color=c)
    ax[1, 0].plot(t * 1e9, vn[k] * 1e3, "--", color=c)
    ax[1, 1].plot(np.array(r["t"]) * 1e9, r["vo"], "-", color=c)
    ax[1, 1].plot(t * 1e9, vo[k], "--", color=c)
ax[0, 1].set_xlim(-0.5, 15); ax[0, 1].legend(); ax[0, 1].set_title("v_o (V), dashed: model")
ax[1, 0].set_xlim(-0.2, 6); ax[1, 0].set_title("v_n (mV)")
ax[1, 1].set_xlim(-0.1, 1.5); ax[1, 1].set_ylim(-1.2, 0.3); ax[1, 1].set_title("v_o, first 1.5 ns")
for a in ax.flat:
    a.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(OUT / "diag_waveforms.png", dpi=110)
for k, r in enumerate(runs):
    ts, vs = np.array(r["t"]), np.array(r["vo"])
    ms = tp.response_metrics(ts[ts >= 0], vs[ts >= 0], r["q"])
    mm = tp.response_metrics(t, vo[k], r["q"])
    print(f"Q {r['q'] * 1e12:5.2f} pC | SPICE {ms['v_peak']:+.4f} V at {ms['t_peak'] * 1e9:.2f} ns, {ms['f_ring'] / 1e6:.1f} MHz, "
          f"tau {ms['tau_decay'] * 1e9:.2f} ns, 1 % {ms['t_settle_1pct'] * 1e9:.1f} ns, undershoot {ms['undershoot_ratio']:.3f}, area/Q {ms['area_over_q']:.0f} | "
          f"model {mm['v_peak']:+.4f} V at {mm['t_peak'] * 1e9:.2f} ns, {mm['f_ring'] / 1e6:.1f} MHz, tau {mm['tau_decay'] * 1e9:.2f} ns, "
          f"1 % {mm['t_settle_1pct'] * 1e9:.1f} ns, undershoot {mm['undershoot_ratio']:.3f}, area/Q {mm['area_over_q']:.0f}, max v_n {np.max(vn[k]) * 1e3:.0f} mV")
