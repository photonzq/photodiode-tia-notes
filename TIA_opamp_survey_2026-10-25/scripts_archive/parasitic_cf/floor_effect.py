"""Effect of a lower parasitic floor on the floor-bound designs (analytical model only).

Usage: python floor_effect.py <scripts_archive folder>
Evaluates design_block and robust_design of run_analysis.py for the parts whose
2-kOhm designs sit on the 0.20-pF floor, at C_F,par = 0.20 and 0.08 pF.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(sys.argv[1]).resolve()))
import run_analysis as ra  # noqa: E402

PARTS = ("OPA855", "OPA858", "OPA955")
for name in PARTS:
    p = ra.PARTS[name]
    ol, ol_fit, _, _ = ra.open_loop_model(p)
    for R_F in (1500.0, 2000.0):
        C_T = ra.C_D + ra.C_PCB_NOM + p["c_cm"] + p["c_diff"]
        for cpar in (0.20e-12, 0.08e-12):
            d = ra.design_block(ol, R_F, C_T, cpar, p["g_min"])
            rb = ra.robust_design(ol, R_F, C_T, cpar)
            parts = []
            for tag in ("flat", "peak1dB"):
                x = d[tag]
                if x.get("C_F_req_pF") is None:
                    parts.append(f"{tag}: none")
                    continue
                parts.append(f"{tag}: req {x['C_F_req_pF']:.3f} real {x['C_F_real_pF']:.3f} pF, "
                             f"{x['f3_MHz']:.0f} MHz, PM {x['pm_deg']:.1f}, pk {x['peaking_dB']:.2f} dB")
            po = d["parasitic_only"]
            parts.append(f"par-only: {po['f3_MHz']:.0f} MHz, PM {po['pm_deg']:.1f}, pk {po['peaking_dB']:.2f}, stable {po['stable']}")
            if rb:
                parts.append(f"robust: {rb['C_F_real_pF']:.3f} pF + C_add {rb['C_add_pF']:.2f}, "
                             f"{rb['f3_MHz']:.0f} MHz, PM {rb['pm_deg']:.1f}, pk {rb['peaking_dB']:.2f}")
            print(f"{name} R_F={R_F:.0f} C_Fpar={cpar*1e12:.2f} pF")
            for s in parts:
                print("   ", s)
