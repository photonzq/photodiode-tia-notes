"""Add four fast amplifiers of the companion note to data/amplifiers.json for the 10-kOhm decade (4 November 2026):
OPA855, OPA955, LMH6629 (bipolar) and OPA858 (CMOS).

The scalar values are typed below with their datasheet pages, as the companion's extraction records give them; the
voltage- and current-noise curves are read from the digitized points of those records
(../../TIA_opamp_survey_2026-10-25/data/specs/<part>.json, read only). Each part carries max_rf = 100 kOhm:
hg_analysis.py evaluates it at 10 kOhm and 100 kOhm only. Above 100 kOhm every design on the note's photodiodes is
limited by the resistor or held to a few megahertz, where the parts' gain-bandwidth buys nothing, and the bipolar
parts' current noise equals the resistor's at R_F,crit = 4kT/i_n^2 = 2.4-2.6 kOhm (OPA855, LMH6629) and 54 kOhm
(OPA955).

Bias current at 85 C: for OPA855 and OPA955 the datasheets give no limit above 25 C; the value used is the 25 C
maximum plus the typical drift (0.08 uA/C) over 60 C, an estimate. LMH6629 gives a limit over temperature.

Usage: python add_fast_parts.py
"""
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
AMPS = HERE.parent / "data" / "amplifiers.json"
SPECS = HERE.parents[1] / "TIA_opamp_survey_2026-10-25" / "data" / "specs"

PARTS = {
    "OPA855": dict(
        maker="TI", doc="OPA855 data sheet SBOS622D, May 2025", input="bipolar, wideband, decompensated",
        supply="3.3-5.25 V", gbw=8000, min_gain=7, aol_db=76, c_cm=0.6, c_diff=0.2,
        ib_typ=12e9, ib_max25=18.5e9, ib_hot={"85": 23.3e9}, vos_max_uV=1500,
        cite="companion record OPA855.json: p. 6 (EC: GBW, A_OL, C_CM/C_DIFF, I_B, V_OS), Fig. 6-11 p. 9 "
             "(noise curves); I_B at 85 C estimated from the typical drift"),
    "OPA955": dict(
        maker="TI", doc="OPA955 data sheet SLOSEE6, July 2026, Advance Information",
        input="bipolar, wideband, decompensated; preproduction", supply="3.3-5.25 V", gbw=11000, min_gain=7,
        aol_db=76, c_cm=0.9, c_diff=0.2, ib_typ=2e9, ib_max25=5e9, ib_hot={"85": 9.8e9}, vos_max_uV=1500,
        cite="companion record OPA955.json: p. 5 (EC), Fig. 6-7 p. 8 (noise curves); Advance Information, "
             "values subject to change; I_B at 85 C estimated from the typical drift"),
    "OPA858": dict(
        maker="TI", doc="OPA858 data sheet SBOS629B, May 2025", input="CMOS, wideband, decompensated",
        supply="3.3-5.25 V", gbw=5500, min_gain=7, aol_db=75, c_cm=0.62, c_diff=0.2,
        ib_typ=400, ib_max25=5000, vos_max_uV=5000,
        cite="companion record OPA858.json: p. 6 (EC), Fig. 6-11 p. 9 (voltage noise), Fig. 8-8 p. 19 "
             "(current noise, both inputs)"),
    "LMH6629": dict(
        maker="TI", doc="LMH6629 data sheet SNOSB18I, Dec. 2014", input="bipolar, wideband, decompensated",
        supply="2.7-5.5 V", gbw=4000, min_gain=10, aol_db=78, c_cm=1.7, c_diff=4.0,
        ib_typ=15e9, ib_max25=23e9, ib_hot={"extremes": 37e9}, vos_max_uV=780,
        cite="companion record LMH6629.json: pp. 5-6 and 9 (EC at 5 V; C_DIFF from simulation), Figs. 28-29 "
             "p. 15 (noise curves); WSON-8 with the COMP pin high (4 GHz, gain >= 10)"),
}


def curves(name: str) -> tuple[dict, dict]:
    rec = json.loads((SPECS / f"{name}.json").read_text(encoding="utf-8"))
    en = {str(float(p["f_Hz"])): p["nV_rtHz"] for p in rec["voltage_noise"]["curve_points"] if p.get("nV_rtHz")}
    in_ = {str(float(p["f_Hz"])): round(p["pA_rtHz"] * 1e3, 4) for p in rec["current_noise"]["curve_points"]
           if p.get("pA_rtHz")}
    return en, in_


data = json.loads(AMPS.read_text(encoding="utf-8"))
data["_about"] = data["_about"].replace("(data/specs in that repository)", "(data/specs in the companion note's folder)")
for name, p in PARTS.items():
    en, in_ = curves(name)
    entry = {"companion": True, **{k: v for k, v in p.items() if k not in ("cite",)}, "en": en, "in_": in_,
             "max_rf": 1e5, "cite": p["cite"]}
    data["parts"][name] = entry
    print(f"{name}: {len(en)} e_n points, {len(in_)} i_n points")
AMPS.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8", newline="\n")
print("written", AMPS.name, "with", len(data["parts"]), "entries")
