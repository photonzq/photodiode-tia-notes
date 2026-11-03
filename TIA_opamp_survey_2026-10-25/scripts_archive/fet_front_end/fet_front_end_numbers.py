"""Figures of merit for discrete FETs considered as a composite-TIA front end.

Usage
-----
python fet_front_end_numbers.py [<dir with vendor S-parameter .zip files> ...]

(The CEL s2p_*.zip and Mini-Circuits *_S2P.zip archives are read directly.)

For every device entry (values typed from the datasheets, with the page and
table/figure cited next to each entry) the script prints

* f_T = g_m / (2 pi C), with the capacitance named in the entry, and
* the channel-thermal input noise voltage e_n = sqrt(4 k T (2/3) / g_m)
  at T = 300 K (long-channel JFET value; gamma = 2/3).

For the pHEMTs, whose datasheets give no gate capacitance, it converts the
lowest-frequency published S-parameters to Y-parameters and prints
C_11 = Im(Y11)/omega (the short-circuit input capacitance, the same
quantity a C_iss bridge measures), Re(Y21) and |Y21|, and the resulting
|Y21| / (2 pi C_11).  These are derived numbers, not datasheet values, and
include the package and the test-fixture via inductance.
"""
import cmath
import math
import pathlib
import sys
import zipfile

K_B = 1.380649e-23   # J/K
T = 300.0            # K
GAMMA = 2.0 / 3.0
Z0 = 50.0


def ft_mhz(gm_s: float, c_f: float) -> float:
    return gm_s / (2.0 * math.pi * c_f) / 1e6


def en_thermal_nv(gm_s: float) -> float:
    return math.sqrt(4.0 * K_B * T * GAMMA / gm_s) * 1e9


# (label, g_m [S], g_m note, C [F], C note)
DEVICES = [
    # NXP BF862 product spec 2000-01-05, p4 Dynamic characteristics table
    ("BF862 TYP", 45e-3, "|yfs| TYP, VDS=8V, VGS=0", 10e-12, "Ciss TYP, VDS=8V, VGS=0"),
    ("BF862 MIN gm", 35e-3, "|yfs| MIN", 10e-12, "Ciss TYP"),
    # BF862 Fig. 6 curve reading at ID = 10 mA (capacitance at that bias not given)
    ("BF862 10mA curve", 37e-3, "Fig.6 reading, ID=10mA", 10e-12, "Ciss TYP at VGS=0 (upper bound)"),
    # NXP BF861A/B/C Rev.5 2011-09-15, Table 7 p3-4 (VDS=8V, VGS=0)
    ("BF861A min", 12e-3, "|yfs| MIN", 10e-12, "Ciss MAX"),
    ("BF861A max", 20e-3, "|yfs| MAX", 10e-12, "Ciss MAX"),
    ("BF861B min", 16e-3, "|yfs| MIN", 10e-12, "Ciss MAX"),
    ("BF861B max", 25e-3, "|yfs| MAX", 10e-12, "Ciss MAX"),
    ("BF861C min", 20e-3, "|yfs| MIN", 10e-12, "Ciss MAX"),
    ("BF861C max", 30e-3, "|yfs| MAX", 10e-12, "Ciss MAX"),
    # NXP BF545A/B/C Rev.4 2011-09-15, Table 7 p4 (|yfs| 3-6.5 mS, VGS=0, VDS=15V)
    # and Table 8 p5 (Ciss 3 pF TYP at VGS=0, VDS=15V; gfs 2 mS TYP @100 MHz, ID=1 mA)
    ("BF545 max", 6.5e-3, "|yfs| MAX, VGS=0", 3e-12, "Ciss TYP, VGS=0"),
    ("BF545 min", 3e-3, "|yfs| MIN, VGS=0", 3e-12, "Ciss TYP, VGS=0"),
    ("BF545 1mA", 2e-3, "gfs TYP @100MHz, ID=1mA", 3e-12, "Ciss TYP, VGS=0 (upper bound)"),
    # onsemi J309/D Rev.1 p2: Re(yfs) TYP 12 mmho @100 MHz (VDS=10V, ID=10mA);
    # Cgs 4.3 + Cgd 1.8 pF TYP (VDS=0, VGS=-10V, 1 MHz)
    ("J310 onsemi", 12e-3, "Re(yfs) TYP @100MHz, ID=10mA", 6.1e-12, "Cgs+Cgd TYP @VGS=-10V"),
    ("J310 onsemi gfs min", 8e-3, "gfs MIN @1kHz, ID=10mA", 7.5e-12, "Cgs+Cgd MAX @VGS=-10V"),
    ("J310 onsemi gfs max", 18e-3, "gfs MAX @1kHz, ID=10mA", 6.1e-12, "Cgs+Cgd TYP"),
    # Fairchild MMBFJ310 Rev.1.5: Fig.14 gfs ~12 mS @10 mA; Fig.10 Ciss(VDS=10V) ~6 pF @VGS=-2V
    ("J310 Fairchild curves", 12e-3, "Fig.14 reading, ID=10mA", 6.0e-12, "Fig.10 Ciss reading, VGS=-2V"),
    # InterFET J310 IF35045.R00 p2: GFS 17 TYP; Cgs 4 + Cdg 1.8 TYP (VDS=0, VGS=-10V)
    ("J310 InterFET", 17e-3, "GFS TYP @1kHz, ID=10mA", 5.8e-12, "Cgs+Cdg TYP @VGS=-10V"),
    # InterFET U310 IF35047.R00 p2: GFS 15 TYP @105 MHz (ID=10mA); Cgs 5 + Cdg 2.5 MAX (VDS=10V, VGS=-10V)
    ("U310 InterFET", 15e-3, "GFS TYP @105MHz, ID=10mA", 7.5e-12, "Cgs+Cdg MAX @VGS=-10V"),
    # Linear Systems J/SST/U308 Doc 201117 p2: gfs 14 TYP; Ciss 4 TYP (VDS=10V, VGS=-10V)
    ("J310 LinearSystems", 14e-3, "gfs TYP @1kHz, ID=10mA", 4.0e-12, "Ciss TYP @VGS=-10V"),
    # onsemi MMBF4416/D Rev.2 p1: |Yfs| 4.5-7.5 mS (VDS=15V, VGS=0); Ciss 4 pF MAX
    ("MMBF4416 min", 4.5e-3, "|Yfs| MIN, VGS=0", 4e-12, "Ciss MAX"),
    ("MMBF4416 max", 7.5e-3, "|Yfs| MAX, VGS=0", 4e-12, "Ciss MAX"),
    # InterFET 2N5397 IF35029.R00 p2: GFS 5.5-9 mS @450 MHz (ID=10mA); Ciss 5 MAX
    ("2N5397 min", 5.5e-3, "GFS MIN @450MHz", 5e-12, "Ciss MAX"),
    ("2N5397 max", 9e-3, "GFS MAX @450MHz", 5e-12, "Ciss MAX"),
    # onsemi CPH3910/D Rev.2 p1: |yfs| 30 MIN / 40 TYP (VDS=5V, VGS=0); Ciss 6.0 TYP
    ("CPH3910 TYP", 40e-3, "|yfs| TYP, VDS=5V, VGS=0", 6.0e-12, "Ciss TYP"),
    ("CPH3910 MIN gm", 30e-3, "|yfs| MIN", 6.0e-12, "Ciss TYP"),
    ("CPH3910 10mA curve", 28e-3, "Fig.5 reading, ID=10mA", 6.0e-12, "Ciss TYP at VGS=0 (upper bound)"),
    # onsemi 2SK3557/D Rev.3 p2: |yfs| 24 MIN / 35 TYP; Ciss 10.0 TYP
    ("2SK3557 TYP", 35e-3, "|yfs| TYP, VDS=5V, VGS=0", 10e-12, "Ciss TYP"),
    ("2SK3557 MIN gm", 24e-3, "|yfs| MIN", 10e-12, "Ciss TYP"),
    # Linear Systems LSBF862 Doc 201195 Rev A2: Yfs 42 TYP; Ciss 11.5 TYP
    ("LSBF862", 42e-3, "Yfs TYP, VDS=10V, VGS=0", 11.5e-12, "Ciss TYP, VDS=8V, VGS=0"),
    # Linear Systems LSK170 Doc 201110 Rev A22 p2
    ("LSK170 VGS=0", 22e-3, "Gfs TYP, VDS=10V, VGS=0", 20e-12, "Ciss TYP (ID=100uA)"),
    ("LSK170 1mA", 10e-3, "Gfs TYP, VDS=15V, ID=1mA", 20e-12, "Ciss TYP (ID=100uA)"),
    # Linear Systems LSK189 Doc 201150 Rev A20 p1 and LSK489 Doc 201151 Rev A40 p2
    ("LSK189 500uA", 1.5e-3, "Gfs TYP, ID=500uA", 4e-12, "Ciss TYP, ID=500uA"),
    ("LSK489 500uA", 1.5e-3, "Gfs TYP, ID=500uA", 4e-12, "Ciss TYP, ID=500uA"),
    # Linear Systems LS5911/12 Doc 201132 Rev A9 p2: gfs 7000 uS TYP @100 MHz; Ciss 5 MAX
    ("LS5911/12", 7e-3, "gfs TYP @100MHz, ID=5mA", 5e-12, "Ciss MAX, ID=5mA"),
    # InterFET IF3601/IF3602, IFN146, IFN860 (p2 tables)
    ("IF3601/IF3602", 175e-3, "GFS TYP, VGS=0", 650e-12, "Ciss TYP, VGS=-4V, VDS=0"),
    ("IFN146", 30e-3, "GFS TYP, VGS=0", 75e-12, "Ciss MAX"),
    ("IFN860", 40e-3, "GFS TYP, ID=10mA", 30e-12, "Ciss TYP, ID=10mA"),
]

# pHEMT DC transconductance and stated gm (no capacitance stated)
PHEMT_GM = [
    ("ATF-34143 (gm=Idss/Vp, VDS=1.5V)", 230e-3),
    ("ATF-54143 (dIds/dVgs @0.70-0.75V)", 410e-3),
    ("ATF-55143 (dIds/dVgs @0.70-0.75V)", 220e-3),
    ("CE3520K3 (VDS=2V, ID=10mA)", 62e-3),
    ("CE3512K2/CE3514M4 (VDS=2V, ID=10mA)", 69e-3),
]

# Lowest-frequency S-parameters typed from the Avago tables:
# (label, f [Hz], (|S11|, deg), (|S21|, deg), (|S12|, deg), (|S22|, deg))
SPARAMS = [
    # ATF-34143 AV02-1283EN p7, p8, p9 (first row, 0.5 GHz)
    ("ATF-34143 3V 20mA", 0.5e9, (0.96, -37), (10.079, 153), (0.035, 68), (0.40, -35)),
    ("ATF-34143 3V 40mA", 0.5e9, (0.96, -40), (11.645, 151), (0.030, 68), (0.29, -43)),
    ("ATF-34143 4V 40mA", 0.5e9, (0.95, -40), (11.973, 151), (0.030, 68), (0.33, -39)),
    # ATF-54143 AV02-0488EN p6 and p9 (first row, 0.1 GHz)
    ("ATF-54143 3V 40mA", 0.1e9, (0.99, -17.6), (25.09, 168.5), (0.009, 80.2), (0.59, -12.8)),
    ("ATF-54143 4V 60mA", 0.1e9, (0.99, -18.6), (27.80, 167.8), (0.01, 80.1), (0.58, -12.6)),
    # ATF-54143 second row (0.5 GHz) as a cross-check
    ("ATF-54143 3V 40mA @0.5G", 0.5e9, (0.83, -76.9), (18.77, 130.1), (0.036, 52.4), (0.44, -54.6)),
    # ATF-55143 AV02-0923EN p9 (first row, 0.1 GHz, and 0.5 GHz)
    ("ATF-55143 2V 20mA", 0.1e9, (0.997, -7.5), (14.512, 174.2), (0.006, 85.5), (0.722, -4.8)),
    ("ATF-55143 2V 20mA @0.5G", 0.5e9, (0.947, -36.2), (13.582, 151.8), (0.026, 69.0), (0.679, -22.9)),
]


def polar(mag_deg):
    mag, deg = mag_deg
    return cmath.rect(mag, math.radians(deg))


def s_to_y(s11, s21, s12, s22, z0=Z0):
    """Two-port S (z0 reference) to Y conversion."""
    delta = (1 + s11) * (1 + s22) - s12 * s21
    y11 = ((1 - s11) * (1 + s22) + s12 * s21) / delta / z0
    y12 = -2 * s12 / delta / z0
    y21 = -2 * s21 / delta / z0
    y22 = ((1 + s11) * (1 - s22) + s12 * s21) / delta / z0
    return y11, y12, y21, y22


def report_sparams(label, f, s11, s21, s12, s22):
    y11, y12, y21, y22 = s_to_y(polar(s11), polar(s21), polar(s12), polar(s22))
    w = 2 * math.pi * f
    c11 = y11.imag / w
    c12 = -y12.imag / w
    print(f"{label:28s} f={f/1e9:5.2f} GHz  C11=Im(Y11)/w={c11*1e12:6.3f} pF  "
          f"Cgd~-Im(Y12)/w={c12*1e12:5.3f} pF  Re(Y11)={y11.real*1e3:6.2f} mS  "
          f"Re(Y21)={y21.real*1e3:7.1f} mS  |Y21|={abs(y21)*1e3:6.1f} mS  "
          f"|Y21|/(2pi C11)={abs(y21)/(2*math.pi*c11)/1e9:6.2f} GHz  "
          f"e_n,th(|Y21|)={en_thermal_nv(abs(y21)):5.3f} nV/rtHz")


def read_touchstone_lowest(text: str):
    """Return (f_Hz, s11, s21, s12, s22) of the first data line."""
    unit, fmt, z0 = "GHZ", "MA", 50.0
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("#"):
            tok = s[1:].upper().split()
            for t in tok:
                if t in ("HZ", "KHZ", "MHZ", "GHZ"):
                    unit = t
                if t in ("MA", "DB", "RI"):
                    fmt = t
            if "R" in tok:
                z0 = float(tok[tok.index("R") + 1])
            continue
        if not s or s.startswith("!"):
            continue
        v = [float(x) for x in s.split()[:9]]
        scale = {"HZ": 1, "KHZ": 1e3, "MHZ": 1e6, "GHZ": 1e9}[unit]

        def conv(a, b):
            if fmt == "MA":
                return cmath.rect(a, math.radians(b))
            if fmt == "DB":
                return cmath.rect(10 ** (a / 20), math.radians(b))
            return complex(a, b)

        return (v[0] * scale, conv(v[1], v[2]), conv(v[3], v[4]),
                conv(v[5], v[6]), conv(v[7], v[8]), z0)
    raise ValueError("no data line")


def main() -> None:
    print("=== f_T = g_m/(2 pi C) and channel-thermal e_n = sqrt(4kT(2/3)/g_m), T = 300 K")
    print(f"4kT(2/3) = {4*K_B*T*GAMMA:.4e} V^2 S/Hz")
    for label, gm, gm_note, c, c_note in DEVICES:
        print(f"{label:24s} gm={gm*1e3:7.2f} mS ({gm_note}); C={c*1e12:6.2f} pF ({c_note}); "
              f"f_T={ft_mhz(gm, c):8.1f} MHz; e_n,th={en_thermal_nv(gm):5.3f} nV/rtHz")
    print()
    print("=== pHEMT stated g_m: channel-thermal e_n with gamma = 2/3")
    for label, gm in PHEMT_GM:
        print(f"{label:40s} gm={gm*1e3:6.1f} mS  e_n,th={en_thermal_nv(gm):5.3f} nV/rtHz")
    print()
    print("=== e_n implied by published noise resistance, e_n = sqrt(4 k T0 Rn), T0 = 290 K")
    # first (0.5 GHz) row of each typical-noise-parameter table; Avago notes that
    # Fmin below 2 GHz is extrapolated
    for label, rn50 in (("ATF-34143 3V 20mA (p7)", 0.16), ("ATF-54143 3V 40mA (p6)", 0.04),
                        ("ATF-55143 2V 20mA (p9)", 0.10), ("SAV-551+ 3V 15mA (p9)", 0.07),
                        ("SAV-541+ 3V 60mA (p9)", 0.05)):
        rn = rn50 * Z0
        print(f"{label:26s} Rn={rn:4.1f} ohm  e_n={math.sqrt(4*K_B*290.0*rn)*1e9:5.3f} nV/rtHz")
    print()
    print("=== upper bound on e_n from a published noise figure, e_n^2 <= (F-1) 4 k T0 Rg")
    for label, nf_db, rg in (("2SK3557 NF 1.0 dB TYP, Rg=1k, 1 kHz, ID=1mA", 1.0, 1e3),
                             ("IFN146 NF 1 dB TYP, RG=100, 1 kHz, ID=5mA", 1.0, 100.0),
                             ("2N4416 NF 2 dB MAX, RG=1k, 100 MHz", 2.0, 1e3),
                             ("MMBF4416 NF 2 dB MAX, Rg=100 (as printed)", 2.0, 100.0)):
        bound = math.sqrt((10 ** (nf_db / 10) - 1) * 4 * K_B * 290.0 * rg) * 1e9
        print(f"{label:44s} e_n <= {bound:5.3f} nV/rtHz")
    print()
    print("=== gate-current shot noise sqrt(2 q I_G) and the 2 kOhm feedback-resistor noise")
    q = 1.602176634e-19
    print(f"sqrt(4kT/2kOhm) = {math.sqrt(4*K_B*T/2e3)*1e12:5.3f} pA/rtHz")
    for i_g in (1e-9, 0.4e-6, 10e-6, 30e-6, 95e-6, 200e-6):
        print(f"I_G = {i_g:8.1e} A -> {math.sqrt(2*q*i_g)*1e12:6.3f} pA/rtHz")
    print()
    print("=== pHEMT input capacitance derived from published S-parameters (Z0 = 50 ohm)")
    for row in SPARAMS:
        report_sparams(*row)

    wanted = ("_2V_10mA", "_3V_10mA", "_3V_15mA", "_3V_20mA", "_3V_40mA", "_3V_60mA")
    for folder in sys.argv[1:]:
        print()
        print(f"=== Vendor Touchstone files in {pathlib.Path(folder).name} "
              "(lowest frequency in each file)")
        for z in sorted(pathlib.Path(folder).glob("*.zip")):
            with zipfile.ZipFile(z) as zf:
                for name in zf.namelist():
                    if not any(tag in name for tag in wanted):
                        continue
                    if "/data/" in name:      # skip ADS-kit copies
                        continue
                    f, s11, s21, s12, s22, z0 = read_touchstone_lowest(
                        zf.read(name).decode("latin-1"))
                    y11, y12, y21, y22 = s_to_y(s11, s21, s12, s22, z0)
                    w = 2 * math.pi * f
                    c11 = y11.imag / w
                    print(f"{pathlib.Path(name).name:40s} f={f/1e9:5.2f} GHz  "
                          f"|S11|={abs(s11):.3f}<{math.degrees(cmath.phase(s11)):7.2f}  "
                          f"|S21|={abs(s21):.3f}<{math.degrees(cmath.phase(s21)):7.2f}  "
                          f"C11={c11*1e12:6.3f} pF  Cgd~{-y12.imag/w*1e12:5.3f} pF  "
                          f"|Y21|={abs(y21)*1e3:6.1f} mS  Re(Y21)={y21.real*1e3:6.1f} mS  "
                          f"|Y21|/(2pi C11)={abs(y21)/(2*math.pi*c11)/1e9:6.2f} GHz")


if __name__ == "__main__":
    main()
