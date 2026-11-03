"""Curated datasheet inputs for the TIA analysis.

Scalar values are chosen here, with their datasheet source, from the
extraction records in ../data/specs/<PART>.json (which cite page, table and
figure for every number).  Curves (open-loop gain and phase, voltage- and
current-noise density) are loaded directly from those records, so they are
not retyped.

Conventions
-----------
en, in   : high-frequency white values (V/rtHz, A/rtHz), typical.
c_cm     : common-mode input capacitance of one input (F), typical.
c_diff   : differential input capacitance (F), typical.
g_min    : minimum stable noise gain (V/V) stated by the manufacturer.
dr       : dynamic-range inputs at the stated supply, typical values:
           swing_light = (V_OL, V_OH) at a light load, swing_100 = the same
           for a 100-ohm AC load (50-ohm back-terminated cable), icr = input
           common-mode range (low, high), iout_ma = linear output current,
           sr = slew rate (V/us).  Voltages are absolute for the stated
           supply rails.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

SPEC_DIR = Path(__file__).resolve().parent.parent / "data" / "specs"


def _rec(part):
    with open(SPEC_DIR / f"{part}.json", encoding="utf-8") as fh:
        return json.load(fh)


def _num(v):
    """float(v) for numbers or numeric strings; None for notes such as 'off scale'."""
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(str(v).strip())
    except (TypeError, ValueError):
        return None


def ol_points(part, f_max=None, key="open_loop_curve", g_key="gain_dB", ph_key="phase_deg"):
    """[(f_Hz, gain_dB, phase_deg or None), ...] from a part's extraction record.

    Points whose gain is missing or not numeric (e.g. 'off scale') are dropped;
    a non-numeric phase is stored as None.
    """
    pts = []
    for p in _rec(part)[key]["points"]:
        f, g = _num(p.get("f_Hz")), _num(p.get(g_key))
        if f is None or g is None:
            continue
        if f_max is not None and f > f_max:
            continue
        pts.append((f, g, _num(p.get(ph_key))))
    return pts


def noise_points(part, kind, scale):
    """Voltage ('voltage_noise', nV) or current ('current_noise', pA) curve in SI units."""
    unit_key = "nV_rtHz" if kind == "voltage_noise" else "pA_rtHz"
    out = []
    for p in _rec(part)[kind].get("curve_points", []) or []:
        f, v = p.get("f_Hz"), p.get(unit_key)
        if f is None or v is None:
            continue
        out.append((float(f), float(v) * scale))
    return out


PARTS: dict[str, dict] = {}

# ---------------------------------------------------------------------------
# TI OPA855: SBOS622D (May 2025), Production Data
# ---------------------------------------------------------------------------
PARTS["OPA855"] = dict(
    maker="TI", input="bipolar", fet=False, owned=False,
    status="Production data", datasheet="opa855.pdf (SBOS622D, May 2025)",
    g_min=7.0, gbw=8.0e9,                       # p6 EC; p25
    en=0.99e-9, in_=2.6e-12,                    # Fig 6-11 white levels (EC: 0.98 nV, 2.5 pA at 1 MHz)
    en_pts=noise_points("OPA855", "voltage_noise", 1e-9),
    in_pts=noise_points("OPA855", "current_noise", 1e-12),
    c_cm=0.6e-12, c_diff=0.2e-12,               # p6 EC
    ol=dict(points=ol_points("OPA855"), fit_f_max=4.5e9,
            calibrate=dict(gain_scale_dB=0.0, pm_target_deg=62.0, g_noise=7.0,
                           why="text p18: 62 deg at noise gain 7 (simulated); Fig 6-10 gives 74 deg"),
            source="Fig 6-10 (vector), G = 7, RL = 200 ohm, +/-2.5 V"),
    dr=dict(supply="+5 V single (or +/-2.5 V)", swing_light=(1.05, 4.10), swing_100=(1.15, 4.05),
            swing_guaranteed=(1.15, 3.95), icr=(1.1, 4.6), icr_guaranteed=(1.3, 4.4),
            iout_ma=80.0, sr=2750.0, lsbw_2vpp_mhz=850.0,
            hd_100mhz_2vpp=dict(rl200=(-65, -74), rl100=(-54.1, -69.1))),   # p6 EC; Figs 6-15/16 (97 MHz)
    iq_ma=17.8, vs_total=(3.3, 5.25),
    package="WSON-8 (DSG), 2 x 2 mm, 0.5 mm pitch, exposed pad to VS-",
    notes="Separate FB pin; PM text 62 deg vs ~74 deg from Fig 6-10 (datasheet inconsistency).",
)

# ---------------------------------------------------------------------------
# TI OPA818: SBOS940B (May 2019, rev. Dec 2025), Production Data
# ---------------------------------------------------------------------------
PARTS["OPA818"] = dict(
    maker="TI", input="FET (JFET)", fet=True, owned=True,
    status="Production data", datasheet="opa818.pdf (SBOS940B, Dec 2025)",
    g_min=7.0, gbw=2.7e9,                       # p5 EC; ~50 deg PM at G = 7 (p16)
    en=2.2e-9, in_=0.003e-12,                   # p5 EC: 2.2 nV (f >= 150 kHz); 3 fA at 10 kHz
    en_pts=noise_points("OPA818", "voltage_noise", 1e-9),       # plotted to 1 MHz only, flat beyond
    in_pts=noise_points("OPA818", "current_noise", 1e-12),      # Fig 6-20 'Simulation', rises to 2.6 pA at 100 MHz
    c_cm=1.9e-12, c_diff=0.5e-12,               # p5 EC
    ol=dict(points=ol_points("OPA818"),
            source="Fig 6-21 / 7-5 'Simulation', RL = 100 ohm, +/-5 V; plotted to 0.96 GHz"),
    dr=dict(supply="+/-6.5 V (13 V maximum recommended)",
            swing_light=(-5.4, 5.6), swing_100=(-5.3, 5.5),          # DERIVED: +/-5 V headroom (p6) at 13 V
            swing_guaranteed_pm5=(-3.67, 3.8), icr=(-6.5, 3.3),     # ICR: VS- (typ) to VS+ - 3.2 V (typ), p5-6
            iout_ma=55.0, iout_continuous_absmax_ma=25.0, sr=1400.0, lsbw_2vpp_mhz=400.0,
            hd_100mhz=dict(rl100_1vpp=(-49.2, -65.5))),             # Fig 6-13
    iq_ma=27.7, vs_total=(6.0, 13.0),
    package="WSON-8 (DRG) 3 x 3 mm with FB pin and exposed pad (to ground plane), or SOT-23-5 (DBV)",
    notes="Open-loop curve is simulated; current-noise curve labelled 'Simulation' and 'Common-mode noise'.",
)

# ---------------------------------------------------------------------------
# TI OPA846: SBOS250E (Dec 2008), Production Data -- bipolar, G >= 7
# ---------------------------------------------------------------------------
PARTS["OPA846"] = dict(
    maker="TI", input="bipolar", fet=False, owned=True,
    status="Production data", datasheet="opa846.pdf (SBOS250E, Dec 2008)",
    g_min=7.0, gbw=1.75e9,                      # p1, p3 (GBP 1750 MHz typ, 1275 min)
    en=1.2e-9, in_=2.8e-12,                     # p3 (f > 1 MHz); flat to ~98 MHz on p6
    en_pts=noise_points("OPA846", "voltage_noise", 1e-9),
    c_cm=1.8e-12, c_diff=2.0e-12,               # p3 input impedance
    ol=dict(points=ol_points("OPA846"), source="p7 open-loop gain and phase, +/-5 V, RL = 100 ohm (page default)"),
    dr=dict(supply="+/-6 V (maximum operating)", swing_light=(-4.44, 4.16), swing_100=(-4.44, 4.16),
            swing_pm5_typ=(-3.4, 3.4), icr=(-4.6, 4.5), iout_ma=80.0, sr=625.0),   # p8 curves at +/-6 V
    iq_ma=12.6, vs_total=(5.0, 12.0),
    package="SOIC-8 or SOT-23-5 (no exposed pad)",
    notes="3.8 pF total input capacitance.",
)

# ---------------------------------------------------------------------------
# TI OPA847: SBOS251E (Dec 2008), Production Data -- bipolar, G >= 12
# ---------------------------------------------------------------------------
PARTS["OPA847"] = dict(
    maker="TI", input="bipolar", fet=False, owned=True,
    status="Production data (SO-8 tube and SOT23-6 250-reel options are Last Time Buy)",
    datasheet="opa847.pdf (SBOS251E, Dec 2008)",
    g_min=12.0, gbw=3.9e9,                      # p1, p3 (3.1 GHz min)
    en=0.85e-9, in_=2.5e-12,                    # p3 (plot 2.7 pA)
    en_pts=noise_points("OPA847", "voltage_noise", 1e-9),
    c_cm=1.7e-12, c_diff=2.0e-12,               # p3 (TIA text uses 1.2 + 2.5 pF)
    ol=dict(points=ol_points("OPA847"), source="p7 open-loop gain and phase, +/-5 V, RL = 100 ohm (page default)"),
    dr=dict(supply="+/-6 V (maximum operating)", swing_light=(-4.38, 4.28), swing_100=(-4.38, 4.28),
            swing_pm5_typ=(-3.5, 3.5), icr=(-4.24, 4.3), iout_ma=75.0, sr=950.0),
    iq_ma=18.1, vs_total=(5.0, 12.0),
    package="SOIC-8 or SOT-23-6 with shutdown pin (no exposed pad)",
    notes="Minimum stable gain 12; 3.7 pF total input capacitance.",
)

# ---------------------------------------------------------------------------
# TI OPA843: SBOS268C (Dec 2008), Production Data -- bipolar, G >= 3 (headline)
# ---------------------------------------------------------------------------
PARTS["OPA843"] = dict(
    maker="TI", input="bipolar", fet=False, owned=False,
    status="Production data", datasheet="opa843.pdf (SBOS268C, Dec 2008)",
    g_min=3.0, gbw=0.8e9,
    en=2.0e-9, in_=2.8e-12,
    c_cm=1.2e-12, c_diff=1.0e-12,
    ol=dict(points=ol_points("OPA843"), source="p7, +/-5 V, RL = 100 ohm (page default)"),
    dr=dict(supply="+/-5 V (+/-6 V maximum)", swing_light=(-3.7, 3.2), swing_100=(-3.5, 3.0),
            icr=(-3.2, 3.2), iout_ma=100.0, sr=1000.0),
    iq_ma=20.2, vs_total=(8.0, 12.0),
    package="SOIC-8 or SOT-23-5",
    notes="Headline only.",
)

# ---------------------------------------------------------------------------
# TI OPA858: SBOS629B (May 2025), Production Data -- CMOS, G >= 7
# ---------------------------------------------------------------------------
PARTS["OPA858"] = dict(
    maker="TI", input="CMOS", fet=True, owned=False,
    status="Production data", datasheet="opa858.pdf (SBOS629B, May 2025)",
    g_min=7.0, gbw=5.5e9,                       # p6 EC (Fig 8-5 simulated: 5.7 GHz; Fig 6-10: 8.8 GHz)
    en=2.5e-9, in_=0.0005e-12,                  # p6: 2.5 nV at 1 MHz
    en_pts=noise_points("OPA858", "voltage_noise", 1e-9),
    in_pts=noise_points("OPA858", "current_noise", 1e-12),      # Fig 8-8: 4.65 pA at 100 MHz, ~f
    c_cm=0.62e-12, c_diff=0.2e-12,              # p6 EC
    ol=dict(points=ol_points("OPA858"),
            calibrate=dict(gain_scale_dB=20 * math.log10(5.5 / 8.8), pm_target_deg=55.0,
                           g_noise=7.0, why="table GBW 5.5 GHz and text 55 deg at noise gain 7 "
                                            "(simulated Figs 8-5/8-6) vs Fig 6-10 (8.8 GHz)"),
            source="Fig 6-10, +/-2.5 V, RL = 200 ohm (4 dB above the table GBW)"),
    dr=dict(supply="+5 V single (or +/-2.5 V)", swing_light=(1.05, 4.10), swing_100=(1.15, 4.0),
            icr=(0.0, 3.6), icr_guaranteed=(0.4, 3.4), iout_ma=80.0, sr=2000.0, lsbw_2vpp_mhz=600.0,
            overdrive_recovery_ns=200.0, hd_100mhz_2vpp=dict(rl200=(-64, -68))),
    iq_ma=20.5, vs_total=(3.3, 5.25),
    package="WSON-8 (DSG) 2 x 2 mm with FB pin, exposed pad to VS-",
    notes="Current noise rises ~f; text attributes it to gate-oxide-to-channel capacitive coupling. "
          "Overdrive recovery 200 ns.",
)

# ---------------------------------------------------------------------------
# TI OPA859: SBOS852A (May 2025), Production Data -- CMOS, unity-gain stable
# ---------------------------------------------------------------------------
PARTS["OPA859"] = dict(
    maker="TI", input="CMOS", fet=True, owned=False,
    status="Production data", datasheet="opa859.pdf (SBOS852A, May 2025)",
    g_min=1.0, gbw=0.9e9,                       # p6 EC
    en=3.3e-9, in_=0.0005e-12,
    en_pts=noise_points("OPA859", "voltage_noise", 1e-9),
    in_pts=noise_points("OPA859", "current_noise", 1e-12),      # identical to OPA858 Fig 8-8
    c_cm=0.62e-12, c_diff=0.2e-12,
    ol=dict(points=ol_points("OPA859"),
            calibrate=dict(gain_scale_dB=0.0, pm_target_deg=63.0, g_noise=1.0,
                           why="text p18: 63 deg as unity-gain buffer; Fig 6-10 gives about 75 deg"),
            source="Fig 6-10, +/-2.5 V, RL = 200 ohm"),
    dr=dict(supply="+5 V single (or +/-2.5 V)", swing_light=(1.10, 4.10), swing_100=(1.15, 4.0),
            icr=(0.0, 3.6), iout_ma=76.0, sr=1150.0, lsbw_2vpp_mhz=400.0,
            hd_100mhz_2vpp=dict(rl200=(-60, -64))),
    iq_ma=20.5, vs_total=(3.3, 5.25),
    package="WSON-8 (DSG) 2 x 2 mm with FB pin, exposed pad to VS-",
    notes="Unity-gain-stable sibling of OPA858.",
)

# ---------------------------------------------------------------------------
# TI OPA657: SBOS197F (Aug 2015), Production Data -- JFET, G >= 7 (headline)
# ---------------------------------------------------------------------------
PARTS["OPA657"] = dict(
    maker="TI", input="FET (JFET)", fet=True, owned=False,
    status="Production data", datasheet="opa657.pdf (SBOS197F, Aug 2015)",
    g_min=7.0, gbw=1.6e9,                       # p5 (Fig 16 implies 2.2-2.5 GHz)
    en=4.8e-9, in_=0.0013e-12,
    c_cm=4.5e-12, c_diff=0.7e-12,
    ol=dict(points=ol_points("OPA657"), source="Fig 16, G = 10 page header, RL = 100 ohm"),
    dr=dict(supply="+/-5 V (12 V maximum)", swing_light=(-3.9, 3.9), swing_100=(-3.5, 3.5),
            icr=(-4.0, 2.5), iout_ma=70.0, sr=700.0),
    iq_ma=14.0, vs_total=(8.0, 12.0),
    package="SOT-23-5 or SOIC-8",
    notes="5.2 pF total input capacitance; GBW table/figure mismatch.",
)

# ---------------------------------------------------------------------------
# ADI LTC6268-10: 626810f (Rev F), distributor copy -- CMOS, G >= 10
# ---------------------------------------------------------------------------
PARTS["LTC6268-10"] = dict(
    maker="ADI (Linear)", input="CMOS", fet=True, owned=False,
    status="Production (datasheet 626810f)", datasheet="ltc6268-10_distributor_copy.pdf (626810f)",
    g_min=10.0, gbw=4.0e9,                      # p4: 4 GHz typ, 3.5 GHz min by design
    en=4.0e-9, in_=0.007e-12,                   # p3: 4.0 nV at 1 MHz; 7 fA at 100 kHz
    en_pts=noise_points("LTC6268-10", "voltage_noise", 1e-9),   # G17: rises to 5.8 nV at 500 MHz
    in_pts=noise_points("LTC6268-10", "current_noise", 1e-12),  # G20: 7.1 pA at 100 MHz, 12 at 200 MHz
    c_cm=0.45e-12, c_diff=0.1e-12,              # p3 (CM DC-100 MHz, DIFF DC-200 MHz)
    ol=dict(points=None, A0_dB=86.0, pm_at_gmin=45.0,
            source="no usable open-loop curve (G21 is not the open-loop gain); constructed model, "
                   "GBW 4 GHz, 45 deg assumed at gain 10"),
    dr=dict(supply="+5 V single (or +/-2.5 V)", swing_light=(0.08, 4.93), swing_100=(0.13, 4.84),
            icr=(-0.1, 4.5), iout_ma=40.0, sr=1000.0),             # p4 swing at 10/25 mA; SR- typ
    iq_ma=16.5, vs_total=(3.1, 5.25),
    package="SOIC-8 (guard-ring NC pins) or TSOT-23-6; no exposed pad",
    notes="Manufacturer's TIA rule C_IN/C_F >= 10; current-noise curve added independently in "
          "the manufacturer's own TIA noise breakdown (p13 Fig 2).",
)

# ---------------------------------------------------------------------------
# ADI LTC6228: Rev. B (03/20), distributor copy -- bipolar, unity-gain stable
# ---------------------------------------------------------------------------
_ltc6228_pts = [(f, g, (None if ph is None else ph - 180.0)) for f, g, ph in ol_points("LTC6228")]
_ltc6228_pts = [(f, g, (-90.0 if ph is None else ph)) for f, g, ph in _ltc6228_pts]  # below 20 MHz: dominant pole
PARTS["LTC6228"] = dict(
    maker="ADI (Linear)", input="bipolar", fet=False, owned=False,
    status="Production (Rev. B)", datasheet="ltc6228_distributor_copy.pdf (Rev. B 03/20)",
    g_min=1.0, gbw=0.89e9,                      # p4
    en=0.88e-9, in_=3.0e-12,                    # p3, bias cancellation disabled
    en_pts=noise_points("LTC6228", "voltage_noise", 1e-9),      # rises above 10 MHz
    c_cm=1.5e-12, c_diff=3.5e-12,               # p3
    ol=dict(points=_ltc6228_pts, source="open-loop plot, RL = 1 kohm, +/-5 V; phase plotted as 180 + angle(A); "
                                         "phase below 20 MHz set to -90 deg (off-scale on the plot)"),
    dr=dict(supply="+/-5.75 V (11.5 V)", swing_light=(-5.74, 5.72), swing_100=(-5.61, 5.50),
            icr=(-5.85, 4.55), iout_ma=80.0, sr=500.0),
    iq_ma=16.0, vs_total=(2.8, 11.75),
    package="SOIC-8 (FB pin), TSOT-23-6 or DFN-6 2 x 2 mm",
    notes="Unity-gain stable; 5 pF total input capacitance.",
)

# ---------------------------------------------------------------------------
# ADI ADA4817-1: Rev. A (2009, Chinese edition), distributor copy -- JFET, unity-gain stable
# ---------------------------------------------------------------------------
PARTS["ADA4817-1"] = dict(
    maker="ADI", input="FET (JFET)", fet=True, owned=False,
    status="Production (copy is Rev. A of 2009; current Rev. H)", datasheet="ada4817-1_distributor_copy.pdf (Rev. A)",
    g_min=1.0, gbw=0.41e9,                      # p3 Table 1
    en=4.0e-9, in_=0.0025e-12,                  # p3: 4 nV at 100 kHz (flat to 100 MHz, Fig 30); 2.5 fA
    en_pts=noise_points("ADA4817-1", "voltage_noise", 1e-9),
    c_cm=1.3e-12, c_diff=0.1e-12,               # p3
    ol=dict(points=ol_points("ADA4817-1"), source="Fig 33, +/-5 V, RL = 100 ohm"),
    dr=dict(supply="+/-5 V (10 V maximum)", swing_light=(-4.0, 4.0), swing_100=(-3.6, 3.7),
            icr=(-5.0, 2.2), iout_ma=40.0, sr=870.0),
    iq_ma=19.0, vs_total=(5.0, 10.0),
    package="LFCSP-8 3 x 3 mm (EP floating/GND) or SOIC-8 EP",
    notes="No current-noise-vs-frequency data in this revision.",
)

# ---------------------------------------------------------------------------
# ADI ADA4899-1: Rev. C (5/2016), distributor copy -- bipolar, unity-gain stable
# ---------------------------------------------------------------------------
PARTS["ADA4899-1"] = dict(
    maker="ADI", input="bipolar", fet=False, owned=False,
    status="Production (Rev. C)", datasheet="ada4899-1_distributor_copy.pdf (Rev. C)",
    g_min=1.0, gbw=0.37e9,                      # not specified; G = +10 x 37 MHz (p14 Table 4)
    en=1.0e-9, in_=2.6e-12,                     # p3 Table 1 (bias cancellation off)
    en_pts=noise_points("ADA4899-1", "voltage_noise", 1e-9),
    c_cm=4.4e-12, c_diff=0.0,                   # single 'input capacitance' 4.4 pF (no CM/DM split)
    ol=dict(points=[(f, g, (None if ph is None else ph - 180.0)) for f, g, ph in ol_points("ADA4899-1")],
            source="Fig 15, +/-5 V, RL = 100 ohm; phase plotted as 180 + angle(A)"),
    dr=dict(supply="+/-5 V (12 V maximum)", swing_light=(-3.7, 3.7), swing_100=(-3.25, 3.25),
            icr=(-3.7, 3.7), iout_ma=None, sr=310.0),
    iq_ma=14.7, vs_total=(4.5, 12.0),
    package="LFCSP-8 3 x 3 mm (EP to ground) or SOIC-8 EP",
    notes="Input capacitance given as one 4.4 pF value; GBW not specified (about 0.3-0.39 GHz derived).",
)

# ---------------------------------------------------------------------------
# ADI AD8099: Rev. E (7/2016), distributor copy -- bipolar, external compensation
# ---------------------------------------------------------------------------
PARTS["AD8099"] = dict(
    maker="ADI", input="bipolar", fet=False, owned=False,
    status="Production (copy Rev. E; current Rev. F)", datasheet="ad8099_distributor_copy.pdf (Rev. E)",
    g_min=15.0, gbw=3.8e9,                      # uncompensated: stable above gain 15 (p15); 3.8 GHz (p1)
    en=0.95e-9, in_=2.6e-12,                    # p3 Table 1
    en_pts=noise_points("AD8099", "voltage_noise", 1e-9),
    c_cm=2.0e-12, c_diff=0.0,                   # single 'input capacitance' 2 pF
    ol=dict(points=ol_points("AD8099"), source="Fig 14, uncompensated, +/-5 V, RL = 1 kohm"),
    dr=dict(supply="+/-5 V (12 V maximum)", swing_light=(-3.8, 3.8), swing_100=(-3.6, 3.7),
            icr=(-3.7, 3.7), iout_ma=None, sr=1350.0),
    iq_ma=15.0, vs_total=(5.0, 12.0),
    package="LFCSP-8 3 x 3 mm (EP to ground) or SOIC-8 EP",
    notes="Used uncompensated (TIA noise gain must stay above ~15 at crossover); compensation "
          "network data exist only for voltage-gain configurations.",
)

# ---------------------------------------------------------------------------
# ADI ADA4895-1: Rev. B (4/2015), distributor copy -- bipolar, G >= 10
# ---------------------------------------------------------------------------
PARTS["ADA4895-1"] = dict(
    maker="ADI", input="bipolar", fet=False, owned=False,
    status="Production (Rev. B)", datasheet="ada4895-1_distributor_copy.pdf (Rev. B)",
    g_min=10.0, gbw=1.5e9,                      # p16 'in excess of 1.5 GHz'
    en=1.0e-9, in_=1.6e-12,                     # Table 2 at 100 kHz
    c_cm=3.0e-12, c_diff=11.0e-12,              # Table 2
    ol=dict(points=ol_points("ADA4895-1"), source="Fig 18, +/-2.5 V, RL = 1 kohm"),
    dr=dict(supply="+/-5 V (10 V maximum)", swing_light=(-4.97, 4.96), swing_100=(-4.85, 4.77),
            icr=(-4.9, 4.1), iout_ma=80.0, sr=943.0),
    iq_ma=3.0, vs_total=(3.0, 10.0),
    package="SOIC-8, SOT-23-6, MSOP-10 (dual)",
    notes="11 pF differential input capacitance.",
)

# ---------------------------------------------------------------------------
# ADI AD8045: Rev. C (12/2018), distributor copy -- bipolar, unity-gain stable (headline)
# ---------------------------------------------------------------------------
PARTS["AD8045"] = dict(
    maker="ADI", input="bipolar", fet=False, owned=False,
    status="Production (Rev. C)", datasheet="ad8045_distributor_copy.pdf (Rev. C)",
    g_min=1.0, gbw=0.4e9,                       # crossover 400 MHz (p17 text)
    en=3.0e-9, in_=3.2e-12,
    en_pts=noise_points("AD8045", "voltage_noise", 1e-9),
    c_cm=1.3e-12, c_diff=0.0,                   # differential capacitance not specified
    ol=dict(points=ol_points("AD8045"), source="Fig 16, +/-5 V, RL = 1 kohm"),
    dr=dict(supply="+/-5 V (12 V maximum)", swing_light=(-3.9, 3.9), swing_100=(-3.6, 3.6),
            icr=(-3.8, 3.8), iout_ma=70.0, sr=1350.0),
    iq_ma=16.0, vs_total=(3.3, 12.0),
    package="SOIC-8 EP or LFCSP-8 3 x 3 mm (EP to -VS or floating)",
    notes="Differential input capacitance not given (input-impedance plot implies ~4.3 pF at G = +1).",
)

# ---------------------------------------------------------------------------
# TI OPA856: SBOS623 (Oct 2020), Production Data -- bipolar, unity-gain stable
# ---------------------------------------------------------------------------
PARTS["OPA856"] = dict(
    maker="TI", input="bipolar", fet=False, owned=False,
    status="Production data", datasheet="opa856.pdf (SBOS623, Oct 2020)",
    g_min=1.0, gbw=1.08e9,                      # GBWP 1.08 GHz; ~57 deg PM at G = 1 (p16)
    en=0.91e-9, in_=2.55e-12,                   # flat to 100 MHz (EC: 0.9 nV, 2.5 pA)
    en_pts=noise_points("OPA856", "voltage_noise", 1e-9),
    c_cm=0.4e-12, c_diff=0.7e-12,               # EC
    ol=dict(points=ol_points("OPA856"), source="open-loop plot, +/-2.5 V, RL = 200 ohm"),
    dr=dict(supply="+5 V single (or +/-2.5 V)", swing_light=(1.05, 4.10), swing_100=(1.15, 4.0),
            icr=(1.1, 4.6), iout_ma=80.0, sr=350.0, lsbw_2vpp_mhz=110.0),   # SR: table 350 V/us (text p17 says 2750)
    iq_ma=17.2, vs_total=(3.3, 5.25),
    package="WSON-8 (DSG) 2 x 2 mm with FB pin, exposed pad to VS-",
    notes="Table slew rate 350 V/us limits large signals above ~50 MHz; HD2/HD3 -50/-45 dBc at 50 MHz, 2 Vpp.",
)

# ---------------------------------------------------------------------------
# TI THS4021: SLOS265F (July 2024), Production Data -- bipolar, G >= 10, +/-15 V
# ---------------------------------------------------------------------------
_ths4021 = ol_points("THS4021", g_key="gain_dB_15V", ph_key="phase_deg_15V")
_ths4021 += [(150e6, 19.3, -134.0), (400e6, 10.0, -189.0), (1.2e9, -15.7, None)]   # extra_points (p11 Fig 5-8)
PARTS["THS4021"] = dict(
    maker="TI", input="bipolar", fet=False, owned=False,
    status="Production data", datasheet="ths4021.pdf (SLOS265F, July 2024)",
    g_min=10.0, gbw=2.0e9,                      # p1 '2 GHz'; Fig 5-8 implies 1.5-2.1 GHz
    en=1.2e-9, in_=2.3e-12,                     # D package, f > 10 kHz
    c_cm=1.5e-12, c_diff=0.0,                   # single 'Ci' 1.5 pF
    ol=dict(points=sorted(_ths4021), source="Fig 5-8, +/-15 V trace, G = +10, RL = 150 ohm (section defaults)"),
    dr=dict(supply="+/-15 V", swing_light=(-13.6, 13.6), swing_100=(-12.9, 12.9),   # 1 kohm / 250 ohm
            icr=(-14.3, 14.3), iout_ma=200.0, sr=470.0),
    iq_ma=7.5, vs_total=(9.0, 32.0),
    package="SOIC-8 (D) or MSOP-8 PowerPAD (DGN, isolated pad)",
    notes="Only high-voltage part in the survey; slew rate 470 V/us limits swing at 100 MHz to 0.75 V peak.",
)

# ---------------------------------------------------------------------------
# TI THS4304: SLOS436A (July 2004) -- bipolar, unity-gain stable, 5 V (headline)
# ---------------------------------------------------------------------------
PARTS["THS4304"] = dict(
    maker="TI", input="bipolar", fet=False, owned=False,
    status="Production data", datasheet="ths4304.pdf (SLOS436A, July 2004)",
    g_min=1.0, gbw=0.87e9,
    en=2.4e-9, in_=2.0e-12,
    c_cm=1.5e-12, c_diff=0.0,                   # 1.5 pF each input to ground
    ol=dict(points=ol_points("THS4304"), source="Fig 26, VS = 5 V, load not stated"),
    dr=dict(supply="+5 V single", swing_light=(1.0, 4.0), swing_100=(1.1, 3.9),
            icr=(-0.2, 5.2), iout_ma=92.0, sr=790.0),
    iq_ma=18.0, vs_total=(2.7, 5.5),
    package="SOT-23-5, MSOP-8, SOIC-8",
    notes="Headline only.",
)

# ---------------------------------------------------------------------------
# TI THS4271: SLOS397F (Oct 2009) -- bipolar, unity-gain stable (headline)
# ---------------------------------------------------------------------------
PARTS["THS4271"] = dict(
    maker="TI", input="bipolar", fet=False, owned=False,
    status="Production data", datasheet="ths4271.pdf (SLOS397F, Oct 2009)",
    g_min=1.0, gbw=0.40e9,
    en=3.0e-9, in_=3.0e-12,
    c_cm=0.4e-12, c_diff=0.8e-12,
    ol=dict(points=ol_points("THS4271"), source="open-loop plot, +/-5 V"),
    dr=dict(supply="+/-5 V", swing_light=(-4.0, 4.0), swing_100=(-3.49, 3.66),
            icr=(-4.0, 4.0), iout_ma=80.0, sr=1000.0),
    iq_ma=22.0, vs_total=(5.0, 10.0),
    package="SOIC-8 (D), MSOP-8 PowerPAD (DGN), MSOP-8 (DGK), VSON-8 (DRB) 3 x 3 mm",
    notes="Headline only; may oscillate with die temperature above 60 C (datasheet note).",
)

def _ol_from_list(part, index, phase_offset=0.0):
    """Open-loop points from a record whose 'open_loop_curve' is a list of curves."""
    curve = _rec(part)["open_loop_curve"][index]
    pts = []
    for p in curve["points"]:
        f, g, ph = _num(p.get("f_Hz")), _num(p.get("gain_dB")), _num(p.get("phase_deg"))
        if f is None or g is None:
            continue
        pts.append((f, g, None if ph is None else ph + phase_offset))
    return pts


# ---------------------------------------------------------------------------
# TI LMH6629: SNOSB18I (Dec 2014), Production Data -- bipolar, COMP pin selects G >= 4 or 10
# ---------------------------------------------------------------------------
_lmh6629_common = dict(
    maker="TI", input="bipolar", fet=False, owned=False,
    status="Production data", datasheet="lmh6629.pdf (SNOSB18I, Dec 2014)",
    en=0.69e-9, in_=2.6e-12,
    c_cm=1.7e-12, c_diff=4.0e-12,               # p6: CM 1.7 pF typ, DIFF 4 pF (simulation)
    iq_ma=15.5, vs_total=(2.7, 5.5),
    package="WSON-8 (COMP pin selectable) or SOT-23-5 (fixed at G >= 10)",
)
PARTS["LMH6629 (COMP HI)"] = dict(
    _lmh6629_common, g_min=10.0, gbw=4.0e9,
    ol=dict(points=_ol_from_list("LMH6629", 0, phase_offset=-180.0),
            source="Fig 31 COMP HI, +/-2.5 V, RL = 100 ohm; phase plotted as 180 + angle(A); to 1 GHz"),
    dr=dict(supply="+5 V single", swing_light=(0.82, 4.19), swing_100=(0.82, 4.19),
            icr=(-0.3, 3.8), iout_ma=250.0, sr=1600.0),
    notes="5.7 pF total input capacitance (differential part simulated).",
)
PARTS["LMH6629 (COMP LO)"] = dict(
    _lmh6629_common, g_min=4.0, gbw=1.7e9,
    ol=dict(points=_ol_from_list("LMH6629", 1, phase_offset=-180.0),
            source="Fig 31 COMP LO, +/-2.5 V, RL = 100 ohm; phase plotted as 180 + angle(A); to 1 GHz"),
    dr=dict(supply="+5 V single", swing_light=(0.82, 4.19), swing_100=(0.82, 4.19),
            icr=(-0.3, 3.8), iout_ma=250.0, sr=530.0),
    notes="COMP LO: GBW 1.7 GHz, slew 530 V/us.",
)

# ---------------------------------------------------------------------------
# TI LMH6624: SNOSA42G (Dec 2014), Production Data -- bipolar, G >= 10
# ---------------------------------------------------------------------------
PARTS["LMH6624"] = dict(
    maker="TI", input="bipolar", fet=False, owned=False,
    status="Production data", datasheet="lmh6624.pdf (SNOSA42G, Dec 2014)",
    g_min=10.0, gbw=1.5e9,                      # stated; open-loop plots imply 1.0-1.15 GHz
    en=0.92e-9, in_=2.3e-12,
    c_cm=0.9e-12, c_diff=2.0e-12,               # simulated values
    ol=dict(points=_ol_from_list("LMH6624", 1), source="Fig 8, +/-6 V, RL = 100 ohm"),
    dr=dict(supply="+/-6 V", swing_light=(-5.2, 5.2), swing_100=(-4.9, 4.9),
            icr=(-4.5, 5.25), iout_ma=100.0, sr=350.0),
    iq_ma=12.0, vs_total=(5.0, 12.0),
    package="SOT-23-5 or SOIC-8",
    notes="Open-loop plots imply 1.0-1.15 GHz GBW against 1.5 GHz stated.",
)

def _first_sweep(points, phase_offset=0.0):
    """Keep the first monotonic frequency sweep (records sometimes append a second
    supply curve after the first) and apply a phase offset."""
    out, last_f = [], 0.0
    for f, g, ph in points:
        if f <= last_f:
            break
        out.append((f, g, None if ph is None else ph + phase_offset))
        last_f = f
    return out


# ---------------------------------------------------------------------------
# ADI LT6200-10: 62001ff (Rev F), distributor copy -- bipolar RRIO, G >= 10 (headline)
# ---------------------------------------------------------------------------
PARTS["LT6200-10"] = dict(
    maker="ADI (Linear)", input="bipolar", fet=False, owned=False,
    status="Production (62001ff)", datasheet="lt6200_family_distributor_copy.pdf (62001ff)",
    g_min=10.0, gbw=1.6e9,                      # p7: 1.6 GHz typ, 1.06 GHz min
    en=0.95e-9, in_=2.2e-12,                    # 100 kHz; HF plot rises to ~1.6 nV at 100-120 MHz
    en_pts=[(3e6, 0.87e-9), (100e6, 1.5e-9), (120e6, 1.67e-9)],
    c_cm=3.1e-12, c_diff=4.2e-12,
    ol=dict(points=_first_sweep(ol_points("LT6200-10"), -180.0),
            source="G67, +/-5 V, RL = 1 kohm, CL = 5 pF; phase plotted as 180 + angle(A); to 340 MHz"),
    dr=dict(supply="+/-5 V (12.6 V maximum)", swing_light=(-4.95, 4.90), swing_100=(-4.8, 4.7),
            icr=(-5.0, 5.0), iout_ma=60.0, sr=450.0),
    iq_ma=20.0, vs_total=(2.5, 12.6),
    package="TSOT-23-6 (S6) or SOIC-8 (S8)",
    notes="Rail-to-rail input and output; 7.3 pF total input capacitance.",
)

# ---------------------------------------------------------------------------
# ADI LT6230-10: 623012fc (Rev C), distributor copy -- bipolar RRO, G >= 10 (headline)
# ---------------------------------------------------------------------------
PARTS["LT6230-10"] = dict(
    maker="ADI (Linear)", input="bipolar", fet=False, owned=False,
    status="Production (623012fc)", datasheet="lt6230_family_distributor_copy.pdf (623012fc)",
    g_min=10.0, gbw=1.45e9,
    en=1.1e-9, in_=2.4e-12,                     # 10 kHz; an unlabelled photo shows a hump to ~5.3 nV at 20 MHz
    c_cm=2.4e-12, c_diff=6.5e-12,
    ol=dict(points=_first_sweep(ol_points("LT6230-10"), -180.0),
            source="G45, +/-5 V, RL = 1 kohm, CL = 5 pF; phase plotted as 180 + angle(A)"),
    dr=dict(supply="+/-5 V", swing_light=(-4.99, 4.99), swing_100=(-4.8, 4.8),
            icr=(-3.0, 4.0), iout_ma=30.0, sr=320.0),
    iq_ma=3.3, vs_total=(3.0, 12.6),
    package="TSOT-23-6 (S6) only",
    notes="8.9 pF total input capacitance.",
)

# ---------------------------------------------------------------------------
# ADI AD8021: Rev. F, distributor copy -- bipolar, external compensation (C_C = 0 used here)
# ---------------------------------------------------------------------------
PARTS["AD8021"] = dict(
    maker="ADI", input="bipolar", fet=False, owned=False,
    status="Production (Rev. F)", datasheet="ad8021_distributor_copy.pdf (Rev. F)",
    g_min=10.0, gbw=1.0e9,                      # C_C = 0: ~1 GHz, ~60 deg at noise gain 10 (Fig 16)
    en=2.1e-9, in_=2.1e-12,
    c_cm=1.0e-12, c_diff=0.0,                   # differential capacitance not specified
    ol=dict(points=[(f, g, (None if ph is None else ph - 180.0)) for f, g, ph in ol_points("AD8021")],
            source="Fig 16, C_C = 0, +/-5 V, ~1 kohm load; phase plotted as 180 + angle(A)"),
    dr=dict(supply="+/-12 V", swing_light=(-10.6, 10.2), swing_100=(-10.6, 10.2),
            icr=(-11.1, 11.6), iout_ma=60.0, sr=420.0),
    iq_ma=7.0, vs_total=(4.5, 24.0),
    package="SOIC-8 or MSOP-8",
    notes="The only part here that runs on +/-12 V; uncompensated slew 420 V/us (G = +10).",
)

# ---------------------------------------------------------------------------
# TI OPA955: SLOSEE6 (July 2026), ADVANCE INFORMATION (all values preliminary)
# ---------------------------------------------------------------------------
PARTS["OPA955"] = dict(
    maker="TI", input="bipolar", fet=False, owned=False,
    status="Advance information (preproduction)", datasheet="opa955.pdf (SLOSEE6, July 2026)",
    g_min=7.0, gbw=11.0e9,                      # p5 EC
    en=0.806e-9, in_=0.557e-12,                 # Fig 6-7 white levels (EC: 0.79 nV, 0.55 pA at 1 MHz)
    en_pts=noise_points("OPA955", "voltage_noise", 1e-9),
    in_pts=noise_points("OPA955", "current_noise", 1e-12),
    in_curve_is_physical=True,                  # rising i_n is the datasheet's own curve (bipolar part)
    c_cm=0.9e-12, c_diff=0.2e-12,               # p5 EC
    ol=dict(points=ol_points("OPA955"), fit_f_max=4.5e9,
            source="Fig 6-6 (vector), G = 7, RL = 200 ohm, +/-2.5 V"),
    dr=dict(supply="+5 V single (or +/-2.5 V)", swing_light=(1.05, 4.10), swing_100=(1.15, 4.05),
            swing_guaranteed=(1.15, 3.95), icr=(1.1, 4.6), icr_guaranteed=(1.35, 4.4),
            iout_ma=80.0, sr=3750.0, lsbw_2vpp_mhz=1200.0,
            hd_100mhz_2vpp=dict(rl200=(-62, -74))),
    iq_ma=20.2, vs_total=(3.3, 5.25),
    package="WSON-8 (DSG), 2 x 2 mm, 0.5 mm pitch, exposed pad (no outline drawing in this revision)",
    notes="Advance information; swing at 100 ohm assumed equal to OPA855 (no curve given).",
)
