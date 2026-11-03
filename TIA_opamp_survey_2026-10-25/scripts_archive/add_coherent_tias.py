"""Add the coherent-receiver TIAs of Section 11.4 to data/integrated_tias.json and restate
MATA-006801 at one gain setting (one-off edit, run once on 27 Oct 2026).

Values were typed in from the rendered documents in ../datasheets/integrated_tia/coherent/ and
from the vendors' product pages, as cited in each record.  The edit is made on the text, so the
file keeps its layout; the result is checked to parse as JSON.

Usage: python add_coherent_tias.py <integrated_tias.json>
"""
import json
import sys
from pathlib import Path

OLD_ABOUT_END = 'Only parts with at least 150 MHz of bandwidth and a linear (non-AGC) gain are plotted.",'
NEW_ABOUT_END = ('Only parts with at least 150 MHz of bandwidth and a linear (non-AGC) gain are plotted. '
                 'Coherent-receiver TIAs (variable gain, one photodiode on each input) are taken at the gain setting '
                 'at which their noise is published: i_pk_lin_A is their linear differential output swing over twice '
                 'that transimpedance (Eq. (60)), capped by their largest stated input; alt_settings lists other '
                 'published or bounding settings (evaluated, not plotted); i_dc_max_A is the largest I1 + I2 that '
                 'their per-input DC limit allows. Records with only notes have no usable figures.",')

OLD_MATA = '''  "MATA-006801": {
   "label": "MATA-006801 (2 kΩ, product page)", "maker": "MACOM", "z_t_ohm": 2000, "bw_MHz": 45000,
   "bw_basis": "45 GHz (product page); datasheet only on request",
   "noise_density_A_rtHz": 16e-12,
   "noise_basis": "16 pA/rtHz (product page), a figure for a 45-GHz receiver; taken as white over 0-150 MHz",
   "i_pk_lin_A": 1.5e-3,
   "i_pk_basis": "3 mApp differential linear input (product page); the gain setting at which it holds is not stated",
   "dc_handling": "not public", "input": "differential, for a balanced photodiode pair", "output": "differential",
   "status": "product page; flip-chip die, 300 mW per channel", "citations": "macom.com product page MATA-006801",
   "in_band": true, "plotted": true
  },
'''

NEW_COHERENT = '''  "MATA-006801": {
   "label": "MATA-006801 (2 kΩ, product page)", "maker": "MACOM", "z_t_ohm": 2000, "bw_MHz": 45000,
   "bw_basis": "45 GHz small-signal bandwidth (product page); datasheet only on request",
   "noise_density_A_rtHz": 16e-12,
   "noise_basis": "16 pA/rtHz input-referred (product page, specification table, beside the 2-kOhm gain; no conditions stated), a figure for a 45-GHz receiver; taken as white over 0-150 MHz",
   "i_pk_lin_A": 175e-6,
   "i_pk_basis": "the 700-mVppd output swing (product page) at the 2-kOhm gain: 0.7 V / (2 x 2 kOhm) = 175 uA peak, derived (Eq. (60)); the 3 mApp differential input the page states as linear needs 233 ohm or less, where no noise is stated",
   "alt_settings": [
    {"label": "1.5 kOhm, the manual-mode maximum, with the noise of 2 kOhm (an upper bound)", "z_t_ohm": 1500, "i_pk_lin_A": 233.3e-6, "noise_density_A_rtHz": 16e-12},
    {"label": "3 mApp with the 16 pA/rtHz of 2 kOhm (an upper bound: the two figures hold at different gains)", "z_t_ohm": 233, "i_pk_lin_A": 1.5e-3, "noise_density_A_rtHz": 16e-12}
   ],
   "gain_settings": "2 kOhm differential transimpedance (specification table); manual mode 65 ohm to 1.5 kOhm through an external pin; automatic mode holds 200-700 mVpp differential (product page)",
   "dc_handling": "not public", "input": "differential, one photodiode on each input", "output": "differential, 700 mVppd",
   "status": "product page; flip-chip die, 300 mW per channel", "citations": "macom.com product page MATA-006801 (read 27 Oct 2026)",
   "in_band": true, "plotted": true
  },
  "GX39220": {
   "label": "GX39220 (500 Ω)", "maker": "Renesas (IDT)", "z_t_ohm": 500, "bw_MHz": 65000,
   "bw_basis": "Zt bandwidth 59 MIN / 65 TYP GHz with its photodiode model, 30-50 fF, 10-40 ohm, 150-300 pH (p8-p9); low-frequency cutoff 50 TYP / 200 MAX kHz (p9); behaviour with a 1-pF photodiode not specified",
   "noise_density_A_rtHz": 28e-12,
   "noise_basis": "28 pA/rtHz TYP at Zt = 500 ohm, the average input noise at the photodiode model's current source up to f3dB (p9, note 1 on p10); 22 at 1 kOhm, 19 at 3.25 kOhm; taken as white over 0-150 MHz",
   "i_pk_lin_A": 500e-6,
   "i_pk_basis": "THD 1.5 % TYP at 1 GHz for 0.06-3 mAppd of input, 0-4 mA of DC and Vout < 500 mVppd (p9): at 500 ohm, 0.5 V / (2 x 500 ohm) = 500 uA peak, derived (Eq. (60)); the full 3 mAppd needs Zt <= 167 ohm, where no noise is stated; THD 2 % TYP for 500-550 mVppd",
   "i_dc_max_A": 8e-3,
   "alt_settings": [
    {"label": "1 kOhm", "z_t_ohm": 1000, "i_pk_lin_A": 250e-6, "noise_density_A_rtHz": 22e-12},
    {"label": "3.25 kOhm, the maximum gain", "z_t_ohm": 3250, "i_pk_lin_A": 76.92e-6, "noise_density_A_rtHz": 19e-12}
   ],
   "gain_settings": "differential transimpedance 50 ohm MAX at the minimum gain, 2800 MIN / 3250 TYP at the maximum gain, VGA range 30 dB MIN (p9); manual gain through VGC (p4); AGC loop 1.1 MHz TYP (p10)",
   "dc_handling": "input DC current 4 mA MAX on each input; DC offset between the inputs -0.5 to +0.5 mA (p9, notes 3-4 on p10); absolute maximum 6 mA per photodiode (p7); hence I1 + I2 up to 8 mA",
   "input": "differential: one photodiode on each input, INP and INN (p4); differential input current Iin = I_INP - I_INN (note 1, p10)",
   "output": "differential CML with 50-ohm loads (p13); 550 mVppd MIN at the maximum output setting, clipped at 900 mVppd (p10)",
   "status": "OBSOLETE: end-of-life notice PLC250030 (12 Sep 2025), last-time buy 12 Mar 2026, last shipment 12 Sep 2026, replacement GX39221-DNT, whose full datasheet is not public; die GX39220-DNT (p15)",
   "citations": "R08DS0227EU0100 Rev 1.00 (28 Nov 2022) p1, p4, p7-p10, p13, p15; Renesas PLC250030 p2",
   "in_band": true, "plotted": true
  },
  "RG8G32423": {
   "label": "RG8G32423 (6 kΩ)", "maker": "Renesas", "z_t_ohm": 6000, "bw_MHz": 24000,
   "bw_basis": "24-GHz 3-dB bandwidth (short-form datasheet p1); photodiode capacitance not stated",
   "noise_density_A_rtHz": 18e-12,
   "noise_basis": "'Low noise < 18 pA/rtHz' (short-form p1), conditions not stated, taken at the maximum gain; taken as white over 0-150 MHz",
   "i_pk_lin_A": 37.5e-6,
   "i_pk_basis": "'THD < 3 % for 450 mVppd output' (short-form p1): at 6 kOhm, 0.45 V / (2 x 6 kOhm) = 37.5 uA peak, derived (Eq. (60)); a looser criterion",
   "gain_settings": "differential linear gain 250 to 6,000 ohm; automatic and manual gain control (short-form p1)",
   "dc_handling": "not stated in the short form",
   "input": "differential, INxP and INxN (block diagram, p1); four channels", "output": "differential",
   "status": "ACTIVE, USD 66.15 (1ku, renesas.com product selector, 27 Oct 2026); flip-chip die RG8G32423BGGWT, -40 to +105 C",
   "citations": "short-form datasheet R08DO0023EU0100 Rev 1.00 (3 Oct 2023) p1",
   "in_band": true, "plotted": true
  },
  "TGA4868": {
   "label": "TGA4868 (4.8 kΩ)", "maker": "Qorvo", "z_t_ohm": 4800, "bw_MHz": 28000,
   "bw_basis": "28 GHz, tunable 24-32 GHz (product page)",
   "noise_density_A_rtHz": 24e-12,
   "noise_basis": "equivalent input noise 24 pA/rtHz (product page), conditions not stated, taken at the maximum gain; taken as white over 0-150 MHz",
   "i_pk_lin_A": 72.9e-6,
   "i_pk_basis": "'THD of <1% for Vout,se<350mVpp' (product page), i.e. 700 mVppd: at 4.8 kOhm, 0.7 V / (2 x 4.8 kOhm) = 72.9 uA peak, derived (Eq. (60))",
   "gain_settings": "250 to 4,800 ohm differential; output 200 to 900 mVppd (product page)",
   "dc_handling": "'able to handle large DC input currents' and offsets between them (product page); not quantified there",
   "input": "differential, two channels, OIF intradyne receiver MSA", "output": "differential",
   "status": "DISCONTINUED (product page, 27 Oct 2026); datasheet not read, qorvo.com refuses scripted downloads",
   "citations": "qorvo.com product page TGA4868 (read 27 Oct 2026)",
   "in_band": true, "plotted": false
  },
  "TGA4872": {
   "label": "TGA4872 (7.5 kΩ)", "maker": "Qorvo", "z_t_ohm": 7500, "bw_MHz": 30000,
   "bw_basis": "30 GHz (product page)",
   "noise_density_A_rtHz": 20e-12,
   "noise_basis": "equivalent input noise 20 pA/rtHz (product page), conditions not stated, taken at the maximum gain; taken as white over 0-150 MHz",
   "i_pk_lin_A": 46.7e-6,
   "i_pk_basis": "its page states no THD figure; with the < 1 % at Vout,se < 350 mVpp of its siblings TGA4861, TGA4864 and TGA4868: 0.7 V / (2 x 7.5 kOhm) = 46.7 uA peak, derived",
   "gain_settings": "100 to 7,500 ohm differential; output 200 to 900 mVppd (product page)",
   "dc_handling": "handles large DC input currents and offsets between them (product page); not quantified there",
   "input": "differential, two channels, fully differential", "output": "differential",
   "status": "DISCONTINUED: end of life announced 17 Oct 2019 (PCN 19-0183), last-time buy 28 Apr 2020 (product page)",
   "citations": "qorvo.com product page TGA4872 (read 27 Oct 2026)",
   "in_band": true, "plotted": false
  },
  "TGA4864": {
   "label": "TGA4864", "maker": "Qorvo",
   "notes": "32-Gb/s dual linear TIA with AGC: 250-4,800 ohm differential, 28 GHz (tunable 24-32 GHz), 24 pA/rtHz, output 200-900 mVppd, THD < 1 % for Vout,se < 350 mVpp, the same figures as TGA4868. DISCONTINUED: end of life announced 22 Feb 2016 (PCN16-0027), replacement TGA4872; data sheet of 17 Jan 2013 listed but not read. qorvo.com product page (read 27 Oct 2026)",
   "in_band": true, "plotted": false
  },
  "TGA4861": {
   "label": "TGA4861", "maker": "Qorvo",
   "notes": "13-Gb/s dual linear TIA with AGC for 44.6-Gb/s DP-QPSK, tunable 8.5-13.5 GHz, THD < 1 % for Vout,se < 350 mVpp; no gain or noise figure on its store page. DISCONTINUED. store.qorvo.com product page (read 27 Oct 2026)",
   "in_band": true, "plotted": false
  },
  "GX39221": {
   "label": "GX39221", "maker": "Renesas",
   "notes": "2 x 96-Gbaud linear TIA, the replacement of GX39220: differential linear gain 70 to 3,250 ohm, > 30 dB, > 60 GHz adjustable (short-form datasheet R08DO0013EU0100 Rev 1.00, 28 Sep 2023, p1); no noise, THD or input range in the public short form, and the full datasheet needs a login. ACTIVE, USD 94.19 (1ku, renesas.com product selector, 27 Oct 2026)",
   "in_band": true, "plotted": false
  },
  "RG8G31220": {
   "label": "RG8G31220", "maker": "Renesas",
   "notes": "2 x 128-Gbaud linear TIA: 50 ohm to 2.3 kOhm typical differential, > 30 dB, > 80 GHz SDD21, output clipped above 1,200 mVppd (short-form R15DO0006EU0100 Rev 1.00, 9 Feb 2026, p1); no noise or THD figure. ACTIVE, USD 157.50 (1ku, product selector, 27 Oct 2026)",
   "in_band": true, "plotted": false
  },
  "RG8G31223": {
   "label": "RG8G31223", "maker": "Renesas",
   "notes": "2 x 128-Gbaud linear TIA: 50 ohm to 2.5 kOhm typical differential, > 30 dB, > 80 GHz SDD21, output clipped above 1,200 mVppd (short-form R15DO0007EU0100 Rev 1.00, 9 Feb 2026, p1); no noise or THD figure. ACTIVE, USD 157.50 (1ku, product selector, 27 Oct 2026)",
   "in_band": true, "plotted": false
  },
  "RG8G3122B": {
   "label": "RG8G3122B", "maker": "Renesas",
   "notes": "2 x 150-Gbaud linear TIA: 75 to 1,450 ohm typical differential, > 20 dB, > 90 GHz SDD21 (short-form, 9 Feb 2026, p1); no noise or THD figure. ACTIVE, no price listed (product selector, 27 Oct 2026)",
   "in_band": true, "plotted": false
  },
  "RG8G31420": {
   "label": "RG8G31420", "maker": "Renesas",
   "notes": "4 x 128-Gbaud linear TIA: 50 to 2,300 ohm typical differential, > 30 dB, > 75 GHz (short-form, 9 Feb 2026, p1); no noise or THD figure. ACTIVE, USD 315.00 (1ku, product selector, 27 Oct 2026)",
   "in_band": true, "plotted": false
  },
  "RG8G3122A": {
   "label": "RG8G3122A", "maker": "Renesas",
   "notes": "2 x 128-Gbaud linear TIA: 50 to 1,500 ohm typical differential, > 27 dB, > 80 GHz SDD21 (short-form R08DO0012EU0100 Rev 1.00, 28 Sep 2023, p1); no noise or THD figure. OBSOLETE: PLC250030, last shipment 12 Sep 2026, replacements RG8G31220 and RG8G31223",
   "in_band": true, "plotted": false
  },
  "GX36220": {
   "label": "GX36220", "maker": "Renesas (IDT)",
   "notes": "2 x 64-Gbps linear TIA: 150 to 5,000 ohm differential, > 30 dB, > 40 GHz (short-form, 22 Mar 2018, p1); no noise or THD figure. OBSOLETE: PLC250030, last shipment 12 Sep 2026",
   "in_band": true, "plotted": false
  },
  "GX36420": {
   "label": "GX36420", "maker": "Renesas (IDT)",
   "notes": "4 x 64-Gbps linear TIA: 150 to 5,000 ohm differential, > 30 dB, > 40 GHz (IDT short-form, 20 Mar 2018, p1); no noise or THD figure. OBSOLETE: PLC250030, last shipment 12 Sep 2026",
   "in_band": true, "plotted": false
  },
  "GX32222": {
   "label": "GX32222", "maker": "Renesas (IDT)",
   "notes": "2 x 32-Gb/s linear TIA: 6,500 ohm typical differential, 25 GHz MIN, > 30 dB (short-form, 3 Nov 2017, p1); no noise or THD figure. OBSOLETE: PLC230010, last shipment 18 Jul 2024",
   "in_band": true, "plotted": false
  },
  "GX32223": {
   "label": "GX32223", "maker": "Renesas (IDT)",
   "notes": "2 x 32-Gbps linear TIA: 150 to 5,000 ohm differential, > 30 dB, > 25 GHz (short-form X0106031 Rev 1.0, 18 Nov 2020, p1); no noise or THD figure. OBSOLETE: PLC230010, last shipment 18 Jul 2024",
   "in_band": true, "plotted": false
  },
  "GX32424": {
   "label": "GX32424", "maker": "Renesas",
   "notes": "4 x 32-Gbps linear TIA for 100G/200G coherent receivers; its datasheet needs a login and was not read. ACTIVE (product selector, 27 Oct 2026)",
   "in_band": true, "plotted": false
  },
  "IN3250TA": {
   "label": "IN3250TA", "maker": "Marvell (Inphi)",
   "notes": "32-Gbaud dual-channel, differential-input linear TIA/VGA, die; product brief (revised 05/21) states no gain, bandwidth, noise, THD or input-range figure",
   "in_band": true, "plotted": false
  },
  "IN3252TA": {
   "label": "IN3252TA", "maker": "Marvell (Inphi)",
   "notes": "32-Gbaud dual-channel, high-gain linear TIA/VGA with input DC offset cancellation, die; product brief (revised 05/21) states no figures",
   "in_band": true, "plotted": false
  },
  "IN3254TA": {
   "label": "IN3254TA", "maker": "Marvell (Inphi)",
   "notes": "32-Gbaud quad-channel, high-gain linear TIA/VGA with input DC offset cancellation and SPI, die; product brief (revised 05/21) states no figures",
   "in_band": true, "plotted": false
  },
  "IN6450TA": {
   "label": "IN6450TA", "maker": "Marvell (Inphi)",
   "notes": "64-Gbaud dual-channel, differential-input linear TIA/VGA, 625-um pitch, die; product brief (revised 05/21) states no figures",
   "in_band": true, "plotted": false
  },
  "IN6452TA": {
   "label": "IN6452TA", "maker": "Marvell (Inphi)",
   "notes": "64-Gbaud dual-channel, differential-input linear TIA/VGA, 500-um pitch, die; product brief (revised 05/21) states no figures",
   "in_band": true, "plotted": false
  },
  "IN6454TA": {
   "label": "IN6454TA", "maker": "Marvell (Inphi)",
   "notes": "64-Gbaud quad-channel, differential-input linear TIA/VGA with input DC offset cancellation and SPI, die; product brief (revised 05/21) states no figures",
   "in_band": true, "plotted": false
  },
  "MxL9105": {
   "label": "MxL9105", "maker": "MaxLinear",
   "notes": "32-Gbaud dual-channel linear coherent TIA, announced 2017; no public datasheet or figures, and not listed on MaxLinear's TIA page (27 Oct 2026), which shows PAM4 parts only",
   "in_band": true, "plotted": false
  },
  "MxL9162": {
   "label": "MxL9162", "maker": "MaxLinear",
   "notes": "64-Gbaud dual-channel linear TIA for coherent receivers, announced at OFC 2017 (> 40 GHz); no public datasheet or figures, and not listed on MaxLinear's TIA page (27 Oct 2026)",
   "in_band": true, "plotted": false
  },
'''


def main():
    path = Path(sys.argv[1])
    text = path.read_text(encoding="utf-8")
    for old, new in ((OLD_ABOUT_END, NEW_ABOUT_END), (OLD_MATA, NEW_COHERENT)):
        assert text.count(old) == 1, old[:60]
        text = text.replace(old, new)
    parts = json.loads(text)["parts"]
    path.write_text(text, encoding="utf-8")
    print(f"{len(parts)} records; plotted: " + ", ".join(k for k, v in parts.items() if v.get("plotted")))


if __name__ == "__main__":
    main()
