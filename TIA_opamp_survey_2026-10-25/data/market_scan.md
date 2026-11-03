# Market and literature scan: high-speed op-amps and integrated TIAs for a discrete photodiode TIA

Date seen for all prices and status labels: 2026-10-25. State of this file: complete for the priority items; remaining gaps are listed under 'Open items'.

Application: photodiode about 1 pF, R_f 1.5-2 kOhm, closed-loop bandwidth at least 150-200 MHz, DC photocurrent 0.1-10 mA plus a small RF modulation; output swing, dynamic range and noise over 10-200 MHz matter.

Selection rule for section A: voltage feedback; GBW at least about 800 MHz (or decompensated with GBW at least 1 GHz); e_n at most about 3 nV/rtHz (bipolar) or 6 nV/rtHz (FET/CMOS), or unusually low input capacitance, or output swing at least +/-5 V with GBW at least 500 MHz. All numbers are typical unless marked min/max.

Source conventions: 'DS pN' = page N of the datasheet PDF (Appendix D of the note lists the revisions); 'TI page' = parametric or orderable data embedded in https://www.ti.com/product/<PART>; 'ADI search listing' = figures shown by a search engine for the named analog.com page, which was not read directly. All status and price figures were seen on 2026-10-25.

## A. Additional voltage-feedback op-amp candidates

| Part | Maker | Input | GBW (MHz) | Min. stable gain (V/V) | e_n (nV/rtHz) | i_n (pA/rtHz) | C_in (pF) | Supply | Output swing | Slew (V/us) | Packages | Lifecycle | 1ku price (USD) | Verdict | Datasheet | Sources |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| TPH2861 (also TPH2861Q automotive) | 3PEAK | bipolar (BJT) | 8000 | 7 (stable for G > 7) | 1.1 at 1 MHz | 3.1 at 1 MHz | 0.5 diff, 0.6 CM | 3.3-5.25 V | 0.9 V from V+ and 1.05 V from V- at 10 mA (about 3 Vpp on 5 V) | 2700 | DFN2x2-8 with FB pin | not checked on maker site; listed by distributors | not checked | candidate: OPA855-class part (8 GHz, G>7, FB pin); I_B -23 uA typ; SSBW 2.3 GHz, LSBW 866 MHz; Iq 19 mA | www.3peak.com (download URL not recorded); local datasheets/market_scan_candidates/tph2861.pdf (AA20231203A3) | DS p1 (features), p6 (C_IN, I_B, supply), p7 (GBW, SR, e_N, i_N, swing) |
| TPH2865Q | 3PEAK | bipolar (BJT) | 4000 | 7 (stable for G > 7) | 1.25 | not checked | not checked | 3.3-5.25 V | not checked | 1000 | DFN2x2-8, wettable flank; AEC-Q100 grade 1 | not checked on maker site | not checked | candidate: lower-power (9.8 mA) 4 GHz, G>7 part | local datasheets/market_scan_candidates/tph2865q.pdf (AA20240603A2) | DS p1 only |
| OPA2846 | Texas Instruments | bipolar | 1750 | 7 | 1.2 | not checked | not checked | 10-12 V total (+/-5 V) | not checked | 625 | SOIC-8 | ACTIVE | 5.90-7.08 | candidate: dual version of the covered OPA846 | https://www.ti.com/product/OPA2846 | TI page |
| LMH6626 | Texas Instruments | bipolar | 1600 (TI parametric) | 10 | 1.0 | not checked | not checked | 5-12 V total | not checked | 360 | SOIC-8; VSSOP-8 | ACTIVE | 3.55-4.62 | candidate: dual version of the covered LMH6624 | https://www.ti.com/product/LMH6626 | TI page |
| MAX4304 | Analog Devices (legacy Maxim) | bipolar | not stated as GBW; -3 dB BW 730 MHz at G = +2 | 2 | 2.1 | not checked | not checked | +/-5 V | not checked | 1000 | SOT23-5; SO-8 | PRODUCTION | from 5.82 (ADI search listing) | candidate: low-noise, G >= 2; datasheet not downloaded | https://www.analog.com/media/en/technical-documentation/data-sheets/max4104-max4305.pdf (not read) | ADI search listing: product page max4304.html and datasheet text |
| MAX4104 | Analog Devices (legacy Maxim) | bipolar | not stated as GBW; -3 dB BW 880 MHz at G = +1 (product page quotes 625 MHz) | 1 | 2.1 | not checked | not checked | +/-5 V | not checked | 400 | SOT23-5; SO-8 | PRODUCTION | 3.88 (product page) / 4.27 (MAX4104ESA+, sample-buy) (ADI search listing) | borderline: GBW around 600-900 MHz, unconfirmed | as MAX4304 | ADI search listing |
| LT6200-5 | Analog Devices (Linear Technology) | bipolar | 800 | 5 | 0.95 at 100 kHz | not checked | not checked | 2.5-12.6 V total | rail-to-rail output; 60 mA min output current | not checked | TSOT-23-6; SO-8 | PRODUCTION (family) | not checked (LT6200-10: 2.27-2.32) | borderline: decompensated 800 MHz, but meets the +/-5 V swing route on +/-6 V supplies | local datasheets/lt6200_family_distributor_copy.pdf | DS p1 |
| LT1226 | Analog Devices (Linear Technology) | bipolar | 1000 | 25 | 2.6 | not checked | not checked | +/-2.5 to +/-15 V | +/-12 V min into 500 Ohm on +/-15 V | 400 | PDIP-8; SO-8 (not re-checked) | PRODUCTION | from 5.33 (ADI search listing) | borderline: only >=1 GHz part with +/-12 V swing found, but G >= 25 needs (C_pd + C_in)/C_f >= 24 at crossover | local datasheets/market_scan_candidates/lt1226_distributor_copy.pdf | DS p1; status/price ADI search listing |
| LT1222 | Analog Devices (Linear Technology) | bipolar | 500 | 10 uncompensated (external compensation pin for lower gain) | 3 | not checked | not checked | +/-15 V class | +/-12 V min into 500 Ohm | 200 | PDIP-8; SO-8 | PRODUCTION | from 5.23 (ADI search listing) | borderline: large swing at exactly 500 MHz GBW | local datasheets/market_scan_candidates/lt1222_distributor_copy.pdf | DS p1; status/price ADI search listing |
| AD829 | Analog Devices | bipolar | 750 (uncompensated) | 1-20 with external compensation | 1.7 | 1.5 | not checked | +/-5 to +/-15 V | +/-3 V into 150 Ohm (at +/-5 V); larger on +/-15 V (not checked) | 230 | PDIP-8; CERDIP-8; SOIC-8; LCC-20 | PRODUCTION | from 4.50 (another listing 3.91) (ADI search listing) | borderline: high-voltage, low-noise, compensation pin | local datasheets/market_scan_candidates/ad829_distributor_copy.pdf (Rev. I) | DS p1; status/price ADI search listing |
| LTC6268 (unity-gain) | Analog Devices (Linear Technology) | CMOS (fA bias) | 500 | 1 | not checked | fA-level (not verified) | not checked | not checked | not checked | not checked | SO-8; TSOT-23-6 | RECOMMENDED FOR NEW DESIGNS | from 5.09; 4.62 (IS8#TRPBF) (ADI search listing) | borderline: qualifies only through the low-C_in route; numbers to be read from its datasheet | not checked | ADI search listing |
| ISL55190 (dual) | Renesas (Intersil) | bipolar | 800 (distributor listing; sibling ISL55191 DS gives 800 MHz at A_V = 10) | not checked | 1.2 | not checked | not checked | not checked | not checked | 268 | SOIC (others not checked) | unconfirmed: Renesas product URL returned HTTP 404; sibling ISL55191 is obsolete | not checked | borderline, probably discontinued | not checked | search-engine listings (GlobalSpec listing, ISL55191 datasheet on Digi-Key CDN) |

### A2. Parts checked and rejected

| Part | Maker | Reason | Source |
|---|---|---|---|
| OPA686, OPA687, OPA643, OPA642, OPA655 | Texas Instruments | no TI product page (HTTP 404): no longer offered | https://www.ti.com/product/<PART> |
| LMH32403, OPA2855, OPA2858, OPA2818, OPA2817, OPA2955, LMH6629-Q1 | Texas Instruments | no TI product page (HTTP 404): not a TI product | https://www.ti.com/product/<PART> |
| OPA656 | Texas Instruments | GBW 230 MHz, e_n 7 nV/rtHz | TI page |
| OPA659 | Texas Instruments | GBW 350 MHz, e_n 8.9 nV/rtHz | TI page |
| THS4631 | Texas Instruments | FET, +/-15 V, but GBW 210 MHz | TI page |
| THS4031, OPA842, LMH6628 | Texas Instruments | GBW 120 / 200 / 200 MHz | TI page |
| THS4022 | Texas Instruments | dual THS4021; TI parametric shows GBW 350 MHz (looks like BW at G = 10; check datasheet); several orderables obsolete. Kept out pending datasheet check | TI page |
| MAX4106 / MAX4107 | Analog Devices (legacy Maxim) | OBSOLETE (0.75 nV/rtHz, G >= 5 / >= 10) | ADI search listing: max4106.html, max4107.html |
| MAX4105 / MAX4305 | Analog Devices (legacy Maxim) | LAST TIME BUY (G >= 5, 430 MHz; G >= 10, 350 MHz; 2.1 nV/rtHz) | ADI search listing: max4105, max4305 pages |
| MAX4108/MAX4109/MAX4308/MAX4309 | Analog Devices (legacy Maxim) | MAX4109 page shows obsolete; family not pursued | ADI search listing |
| LTC6252 / LTC6253 / LTC6254 | Analog Devices (Linear Technology) | GBW 720 MHz, 2.75 nV/rtHz, 5.25 V max supply; LTC6252 LAST TIME BUY (PDN 23_0089, notice 20 Mar 2024, replacement ADA4891); LTC6253 from 3.67 at 1ku | DS p1 (ltc6252_distributor_copy.pdf); ADI search listing |
| LTC6226 / LTC6227 | Analog Devices (Linear Technology) | GBW 420 MHz (1 nV/rtHz, 2.8-11.75 V) | DS p1 (ltc6226_distributor_copy.pdf) |
| ISL28191 / ISL28291 | Renesas | 61 MHz -3 dB BW (1.7 nV/rtHz) | search-engine listing of renesas.com/en/products/isl28191 |
| EL5130 family | Renesas (Elantec/Intersil) | obsolete (LTB 2010), 300 MHz class | Octopart listing |
| TSH300 | STMicroelectronics | VFB, about 1 GHz GBW, 0.65 nV/rtHz, but listed as discontinued by a distributor; the st.com page gave no response | search-engine listings (cytechsystems listing; Electronic Design news item) |
| TSH330 | STMicroelectronics | current feedback | search-engine listings |
| NCS2551 | onsemi | 500 MHz VFB but 6 nV/rtHz (2006 datasheet); other onsemi high-speed parts are current feedback | https://www.onsemi.com/pdf/datasheet/ncs2551-d.pdf (search listing) |
| MCP6xxx (fastest about 30 MHz) | Microchip | GBW far too low | search-engine listings (RS listings) |
| NJM2725 (fastest found) | Nisshinbo | GBW 160 MHz (1.4 nV/rtHz, G >= 2) | search-engine listings (Mouser, RS listings) |
| LMR1701 (fastest found) | ROHM | GBW 150 MHz CMOS | search-engine listings (RS listing) |
| SGM80581/2/4 (fastest found) | SGMICRO | 220 MHz unity-gain BW, 7 nV/rtHz | search-engine listings (sg-micro.com, LCSC) |
| RS876X / RS875X (fastest found) | Runic | at most 250 MHz | search-engine listings (LCSC) |
| NSOPA series | Novosense | 1-10 MHz class | search-engine listings (press items) |

### A3. Manufacturers checked

| Maker | What was checked | Result |
|---|---|---|
| Texas Instruments (beyond covered list) | 47 product pages read | OPA2846, LMH6626 (duals of covered parts); OPA855-Q1, OPA858-Q1 automotive grades |
| Analog Devices / LT / Maxim | front pages of LTC6252, LTC6226, LT1222, LT1226, AD829, LT6200 family; search-engine listing of status/price | MAX4304, MAX4104, LT6200-5, LT1226, LT1222, AD829, LTC6268 |
| 3PEAK | TPH2861, TPH2861Q, TPH2865Q datasheets | TPH2861, TPH2865Q |
| Renesas / Intersil / Elantec | ISL28190/1, ISL55190/1, EL5130 family | ISL55190 borderline (status unconfirmed) |
| STMicroelectronics | TSH300, TSH330, TSH310 | none current |
| onsemi, Microchip, Nisshinbo, ROHM, SGMICRO, Runic, Novosense | web search of each maker's fastest parts | none above 500 MHz except onsemi NCS2551 (6 nV/rtHz) |

## B. Lifecycle status and 1ku price

| Part | Maker | Status | 1ku price (USD) | Price basis | Packages | Source | Notes |
|---|---|---|---|---|---|---|---|
| OPA846 | Texas Instruments | ACTIVE | 2.95 (OPA846IDBVR) to 3.54 (OPA846ID) | TI list price at 1ku break, per orderable | SOIC (D)-8; SOT-23 (DBV)-5 | https://www.ti.com/product/OPA846 (orderable data embedded in page) |  |
| OPA847 | Texas Instruments | ACTIVE | 6.35 (OPA847IDBVR) | TI list price at 1ku break, per orderable | SOIC (D)-8; SOT-23 (DBV)-6 | https://www.ti.com/product/OPA847 (orderable data embedded in page) | non-active orderables: OPA847ID LAST TIME BUY, OPA847IDBVT LAST TIME BUY |
| OPA843 | Texas Instruments | ACTIVE | 2.77 (OPA843IDBVR) to 3.74 (OPA843ID) | TI list price at 1ku break, per orderable | SOIC (D)-8; SOT-23 (DBV)-5 | https://www.ti.com/product/OPA843 (orderable data embedded in page) |  |
| OPA818 | Texas Instruments | ACTIVE | 7.08 (OPA818DBVR) to 8.50 (OPA818DBVT) | TI list price at 1ku break, per orderable | SOT-23 (DBV)-5; WSON (DRG)-8 | https://www.ti.com/product/OPA818 (orderable data embedded in page) |  |
| OPA817 | Texas Instruments | ACTIVE | 3.61 (OPA817DTKR) | TI list price at 1ku break, per orderable | WSON (DTK)-8 | https://www.ti.com/product/OPA817 (orderable data embedded in page) |  |
| OPA814 | Texas Instruments | ACTIVE | 4.55 (OPA814DBVR) | TI list price at 1ku break, per orderable | SOIC (D)-8; SOT-23 (DBV)-5 | https://www.ti.com/product/OPA814 (orderable data embedded in page) |  |
| OPA855 | Texas Instruments | ACTIVE | 3.05 (OPA855IDSGR) to 3.67 (OPA855IDSGT) | TI list price at 1ku break, per orderable | WSON (DSG)-8; bare die (Y) | https://www.ti.com/product/OPA855 (orderable data embedded in page) |  |
| OPA856 | Texas Instruments | ACTIVE | 2.91 (OPA856IDSGR) | TI list price at 1ku break, per orderable | WSON (DSG)-8 | https://www.ti.com/product/OPA856 (orderable data embedded in page) |  |
| OPA858 | Texas Instruments | ACTIVE | 2.92 (OPA858IDSGR) to 3.51 (OPA858IDSGT) | TI list price at 1ku break, per orderable | WSON (DSG)-8; bare die (Y) | https://www.ti.com/product/OPA858 (orderable data embedded in page) |  |
| OPA859 | Texas Instruments | ACTIVE | 2.55 (OPA859IDSGR) to 3.06 (OPA859IDSGT) | TI list price at 1ku break, per orderable | WSON (DSG)-8; bare die (Y) | https://www.ti.com/product/OPA859 (orderable data embedded in page) |  |
| OPA657 | Texas Instruments | ACTIVE | 9.00 (OPA657U/2K5) to 11.88 (OPA657N/250) | TI list price at 1ku break, per orderable | SOIC (D)-8; SOT-23 (DBV)-5 | https://www.ti.com/product/OPA657 (orderable data embedded in page) |  |
| OPA955 | Texas Instruments | PREVIEW | 6.99 (XOPA955DSGR) | TI list price at 1ku break, per orderable | WSON (DSG)-8 | https://www.ti.com/product/OPA955 (orderable data embedded in page) | product page status PREVIEW (pre-production); only orderable is the X-prefixed pre-production part. |
| LMH6629 | Texas Instruments | ACTIVE | 2.75 (LMH6629MFX/NOPB) to 3.30 (LMH6629MF/NOPB) | TI list price at 1ku break, per orderable | SOT-23 (DBV)-5; WSON (NGQ)-8 | https://www.ti.com/product/LMH6629 (orderable data embedded in page) |  |
| LMH6624 | Texas Instruments | ACTIVE | 2.61 (LMH6624MAX/NOPB) to 3.13 (LMH6624MA/NOPB) | TI list price at 1ku break, per orderable | SOIC (D)-8; SOT-23 (DBV)-5 | https://www.ti.com/product/LMH6624 (orderable data embedded in page) |  |
| THS4021 | Texas Instruments | ACTIVE | 4.49 (THS4021IDR) to 6.51 (THS4021CDGN) | TI list price at 1ku break, per orderable | HVSSOP (DGN)-8; SOIC (D)-8 | https://www.ti.com/product/THS4021 (orderable data embedded in page) | non-active orderables: THS4021CD OBSOLETE |
| THS4304 | Texas Instruments | ACTIVE | 7.49 (THS4304D) to 8.99 (THS4304DBVT) | TI list price at 1ku break, per orderable | SOIC (D)-8; SOT-23 (DBV)-5; VSSOP (DGK)-8 | https://www.ti.com/product/THS4304 (orderable data embedded in page) |  |
| THS4271 | Texas Instruments | ACTIVE | 4.36 (THS4271DGNR) to 5.62 (THS4271DGN) | TI list price at 1ku break, per orderable | HVSSOP (DGN)-8; SOIC (D)-8; VSON (DRB)-8; VSSOP (DGK)-8 | https://www.ti.com/product/THS4271 (orderable data embedded in page) |  |
| LMH6609 | Texas Instruments | ACTIVE | 1.44 (LMH6609MAX/NOPB) to 1.73 (LMH6609MA/NOPB) | TI list price at 1ku break, per orderable | SOIC (D)-8; SOT-23 (DBV)-5 | https://www.ti.com/product/LMH6609 (orderable data embedded in page) |  |
| OPA699 | Texas Instruments | ACTIVE | 3.44 (OPA699IDR) to 4.12 (OPA699ID) | TI list price at 1ku break, per orderable | SOIC (D)-8 | https://www.ti.com/product/OPA699 (orderable data embedded in page) |  |
| LMH32401 | Texas Instruments | ACTIVE | 5.26 (LMH32401IRGTR) to 6.31 (LMH32401IRGTT) | TI list price at 1ku break, per orderable | VQFN (RGT)-16; bare die (Y) | https://www.ti.com/product/LMH32401 (orderable data embedded in page) |  |
| OPA857 | Texas Instruments | ACTIVE | 2.59 (OPA857IRGTR) to 3.42 (OPA857IRGTT) | TI list price at 1ku break, per orderable | VQFN (RGT)-16 | https://www.ti.com/product/OPA857 (orderable data embedded in page) |  |
| OPA2846 | Texas Instruments | ACTIVE | 5.90 (OPA2846IDR) to 7.08 (OPA2846ID) | TI list price at 1ku break, per orderable | SOIC (D)-8 | https://www.ti.com/product/OPA2846 (orderable data embedded in page) |  |
| LMH6626 | Texas Instruments | ACTIVE | 3.55 (LMH6626MM/NOPB) to 4.62 (LMH6626MA/NOPB) | TI list price at 1ku break, per orderable | SOIC (D)-8; VSSOP (DGK)-8 | https://www.ti.com/product/LMH6626 (orderable data embedded in page) |  |
| OPA855-Q1 | Texas Instruments | ACTIVE | 3.60 (OPA855QDSGRQ1) | TI list price at 1ku break, per orderable | WSON (DSG)-8 | https://www.ti.com/product/OPA855-Q1 (orderable data embedded in page) |  |
| OPA858-Q1 | Texas Instruments | ACTIVE | 3.45 (OPA858QDSGRQ1) | TI list price at 1ku break, per orderable | WSON (DSG)-8 | https://www.ti.com/product/OPA858-Q1 (orderable data embedded in page) |  |
| THS4022 | Texas Instruments | ACTIVE | 7.29 (THS4022IDGNR) to 18.87 (THS4022ID) | TI list price at 1ku break, per orderable | HVSSOP (DGN)-8; SOIC (D)-8 | https://www.ti.com/product/THS4022 (orderable data embedded in page) | non-active orderables: THS4022CDGN OBSOLETE, THS4022CDGNR OBSOLETE, THS4022IDGN OBSOLETE |
| LMH32404 | Texas Instruments | ACTIVE | 10.71 (LMH32404IRHFR) | TI list price at 1ku break, per orderable | VQFN (RHF)-28; bare die (Y) | https://www.ti.com/product/LMH32404 (orderable data embedded in page) |  |
| LMH34400 | Texas Instruments | ACTIVE | 1.44 (LMH34400IDRLR) | TI list price at 1ku break, per orderable | SOT-5X3 (DRL)-6 | https://www.ti.com/product/LMH34400 (orderable data embedded in page) |  |
| ADA4899-1 | Analog Devices | PRODUCTION (all four models); PCN 26_0028 (16 Feb 2026) qualifies an extra wafer-fab site | from 2.85 (all four models) | ADI list 1ku, from a search-engine listing (which may be old) | 8-lead LFCSP 3 x 3 mm (CP-8-13); 8-lead SOIC_EP | search-engine listing of https://www.analog.com/en/products/ada4899-1.html | ADI lists ADA4899-1 as the replacement for the discontinued LTC6228 (PDN 23_0089) |
| ADA4817-1 | Analog Devices | PRODUCTION (5 models) | 4.00 (LFCSP-8 reels ACPZ-R7/-RL); 4.52 (SOIC-8 ARDZ variants) | ADI list 1ku, from a search-engine listing | 8-lead LFCSP 3 x 3 mm; 8-lead SOIC | search-engine listing of https://www.analog.com/en/products/ada4817-1/sample-buy.html | the product overview page listing shows 4.40 (LFCSP) / 4.98 (SOIC): the two ADI pages disagree |
| AD8099 | Analog Devices | PRODUCTION | from 3.28 (all listed models) | ADI list 1ku, from a search-engine listing (which may be old) | 8-lead LFCSP 3 x 3 mm (CP-8-13); 8-lead SOIC | search-engine listing of https://www.analog.com/en/products/ad8099.html | older ACPZ-R2 and non-Z variants discontinued (PDN 17_0009, PDN 14_0014) |
| ADA4895-1 | Analog Devices | RECOMMENDED FOR NEW DESIGNS | from 2.56; 3.23 (ADA4895-1ARJZ-R2, SOT-23) | ADI list 1ku, from a search-engine listing | 8-lead SOIC; 6-lead SOT-23 | search-engine listing of https://www.analog.com/en/products/ada4895-1.html |  |
| LTC6268-10 | Analog Devices (Linear Technology) | Production | 4.68 (LTC6268IS8-10#PBF, SO-8) to 5.44 (H-grade TSOT-23 reel) | ADI list 1ku, from a search-engine listing | SO-8; TSOT-23-6 | search-engine listing of https://www.analog.com/en/products/ltc6268-10/sample-buy.html | the overview page listing says 'from $5.15', so the two ADI pages disagree |
| LTC6228 | Analog Devices (Linear Technology) | LAST TIME BUY (discontinued): ADI PDN 23_0089 Rev A, Tower Fab3 process retirement; last-time-buy date 17 Jan 2025, last-time-ship date 28 Feb 2030 | one ADI page listing 'from 2.03'; another shows price unavailable | ADI list 1ku, from a search-engine listing (unconfirmed) | SO-8; TSOT-23-6 | search-engine listing of https://www.analog.com/en/products/ltc6228.html and https://www.analog.com/media/en/PCN/ADI_PDN_23_0089_Rev_A_Form.pdf | PDN lists ADA4899-1 as replacement; LTC6229 (dual) presumably shares the notice (not checked) |
| LT6200-10 | Analog Devices (Linear Technology) | PRODUCTION (family page and sample-buy page) | 2.27 (LT6200CS6-10, TSOT-23-6); 2.32 (LT6200CS8-10#PBF, SO-8) | ADI list 1ku, from a search-engine listing | TSOT-23-6; SO-8 | search-engine listing of https://www.analog.com/en/products/lt6200/sample-buy.html | overview page listing shows 2.50 (CS6-10) / 2.56 (CS8-10) |
| LT6230-10 | Analog Devices (Linear Technology) | PRODUCTION (family level; model-level status not shown) | 2.50 (C-grade CS6-10 reel); 2.93 (I-grade IS6-10 reel); family from 2.09 | ADI list 1ku, from a search-engine listing | TSOT-23-6 | search-engine listing of https://www.analog.com/en/products/lt6230.html | ADI names LT6236/LT6237/LT6238 as upgrades of LT6230/LT6231/LT6232 (lower wideband noise above 100 kHz); no -10 version found |
| LTC6409 | Analog Devices (Linear Technology) | RECOMMENDED FOR NEW DESIGNS (as shown on related ADI pages) | product page 'from 6.78'; sample-buy snippet inconsistent (6.78-9.48 vs 15.23-18.64 by grade) | ADI list, from a search-engine listing (unresolved) | 10-lead 3 x 2 mm QFN (datasheet front page; not re-checked) | search-engine listing of https://www.analog.com/en/products/ltc6409.html and .../ltc6409/sample-buy.html | fully differential amplifier; PDN 23_0089 names LTC6409 as replacement for LTC6400/6401/6410/6416/6417 |
| AD8021 | Analog Devices | PRODUCTION; PCN 26_0028 (16 Feb 2026) fab-site qualification | 'from 1.95' (one listing) or 'from 1.54' (another) | ADI list 1ku, from search-engine listings (they disagree) | 8-lead SOIC; 8-lead MSOP | search-engine listing of https://www.analog.com/en/products/ad8021.html |  |
| AD8045 | Analog Devices | PRODUCTION | from 2.42 (AD8045ARDZ-REEL7); 4.12 (AD8045ACPZ-R2) | ADI list 1ku, from a search-engine listing | 8-lead SOIC_N_EP; 8-lead LFCSP 3 x 3 mm | search-engine listing of https://www.analog.com/en/products/ad8045.html |  |
| LT1226 | Analog Devices (Linear Technology) | PRODUCTION (PCN 2026-0038, Aug 2026, assembly change) | from 5.33 (some models 5.47) | ADI list 1ku, from a search-engine listing | PDIP-8; SO-8 | search-engine listing of https://www.analog.com/en/products/lt1226.html | new candidate |
| LT1222 | Analog Devices (Linear Technology) | PRODUCTION (PCN 24_0234, Oct 2024, marking) | from 5.23 | ADI list 1ku, from a search-engine listing | PDIP-8; SO-8 | search-engine listing of https://www.analog.com/en/products/lt1222.html | new candidate |
| AD829 | Analog Devices | PRODUCTION | from 4.50 (another listing: from 3.91) | ADI list 1ku, from a search-engine listing | PDIP-8; CERDIP-8; SOIC-8; LCC-20 | search-engine listing of https://www.analog.com/en/products/ad829.html | new candidate |
| MAX4304 | Analog Devices (legacy Maxim) | PRODUCTION | from 5.82 | ADI list 1ku, from a search-engine listing | SOT23-5; SO-8 | search-engine listing of https://www.analog.com/en/products/max4304.html | new candidate |
| MAX4104 | Analog Devices (legacy Maxim) | PRODUCTION | 3.88 (product page); 4.27 (MAX4104ESA+, sample-buy) | ADI list 1ku, from a search-engine listing | SOT23-5; SO-8 | search-engine listing of https://www.analog.com/en/products/max4104.html | new candidate |
| LTC6268 | Analog Devices (Linear Technology) | RECOMMENDED FOR NEW DESIGNS | from 5.09; 4.62 (LTC6268IS8#TRPBF) | ADI list 1ku, from a search-engine listing | SO-8; TSOT-23-6 | search-engine listing of https://www.analog.com/en/products/ltc6268.html and /sample-buy.html; Digi-Key LTC6268IS8#PBF: Active, 7.16 at 1,000 pcs | new candidate |
| LTC6252 | Analog Devices (Linear Technology) | LAST TIME BUY (PDN 23_0089, notice 20 Mar 2024; replacement ADA4891-1/-2, not pin compatible) | price unavailable (LTC6253: from 3.67) | ADI list 1ku, from a search-engine listing | TSOT-23-6 (LTC6252) | search-engine listing of https://www.analog.com/en/products/ltc6252.html and PDN 23_0089 | rejected near-miss |
| MAX4105 / MAX4305 | Analog Devices (legacy Maxim) | LAST TIME BUY | n/a |  |  | search-engine listing of analog.com max4105 and max4305 pages | rejected |
| MAX4106 / MAX4107 | Analog Devices (legacy Maxim) | OBSOLETE | n/a |  |  | search-engine listing of analog.com max4106 and max4107 pages | rejected |
| HMC799 | Analog Devices (Hittite) | LAST TIME BUY | not checked |  | 16-lead 3 x 3 mm SMT | search-engine listing of https://www.analog.com/en/products/hmc799 | integrated TIA |

## C. Integrated TIAs and photodiode front ends

| Part | Maker | Function | Transimpedance | Bandwidth | Input-referred noise | Max. input current | DC / ambient cancellation | Lifecycle | 1ku price (USD) | Sources |
|---|---|---|---|---|---|---|---|---|---|---|
| LMH32401 | Texas Instruments | 1-ch, single-ended in, differential out; output mux via EN | 2 kOhm or 20 kOhm | 450 MHz (2 kOhm) / 275 MHz (20 kOhm), C_pd = 1 pF | 250 nA rms (2 kOhm) / 49 nA rms (20 kOhm) | 100 mA protection clamp | ambient-light cancellation range 2 mA min, 3 mA typ; settles in 18 us (0 to 100 uA, 2 kOhm); adds noise; can be disabled | ACTIVE | 5.26-6.31 | TI page; DS p9 (lmh32401.pdf, SBOS965D) |
| LMH32404 | Texas Instruments | 4-ch, single-ended in, differential out | 20 kOhm | 350 MHz, C_pd = 1 pF | 56 nA rms | 100 mA protection clamp | ambient-light cancellation (range not checked); disable for DC and low-frequency content | ACTIVE | 10.72 | TI page |
| LMH34400 | Texas Instruments | 1-ch, single-ended out, 1.0 Vpp | 40 kOhm | 240 MHz, C_pd = 1 pF | 50 nA rms | 100 mA protection clamp | ambient-light cancellation (range not checked); disable for content below 400 kHz | ACTIVE | 1.44 | TI page |
| OPA857 | Texas Instruments | 1-ch TIA (covered; datasheet in hand) | see covered extraction | TI parametric: 130 MHz | see covered extraction | see covered extraction | see covered extraction | ACTIVE | 2.59-3.42 | TI page |
| MAX40660 / MAX40661 | Analog Devices (legacy Maxim) | 1-ch lidar TIA | 25 kOhm or 50 kOhm | 490 MHz (MAX40660, C_in 0.25-5 pF); 160 MHz typ, 100 MHz min (MAX40661, C_in 10 pF) | 2.1 pA/rtHz (distributor text: 2.38) | clamp: 2 A for 10 ns; 2 ns overload recovery | not stated in the sources read | not checked | not checked | search-engine listings (ADI pages, Mouser, Farnell datasheet copy) |
| MAX40658 / MAX40659 | Analog Devices (legacy Maxim) | 1-ch lidar TIA, differential out | 18 kOhm / 36 kOhm | 360 MHz min | 45 nA rms | clamp up to 100 mA | offset input adjusts input offset current (range not checked) | PRODUCTION | not checked | search-engine listings (ADI datasheet text, RS, Mouser) |
| MAX40662 | Analog Devices (legacy Maxim) | 4-ch lidar TIA | 25 kOhm or 50 kOhm | 440 MHz typ, 300 MHz min (C_pd 0.5-5 pF) | 2.1 pA/rtHz | clamp: 2 A for 10 ns | not stated in the sources read | RECOMMENDED FOR NEW DESIGNS | not checked | ADI search listing; Mouser |
| LTC6560 / LTC6561 (quad) | Analog Devices (Linear Technology) | APD TIA, DC-coupled | 74 kOhm | 220 MHz | 4.8 pA/rtHz at 200 MHz, 64 nA rms over 200 MHz (C_in 2 pF); LTC6561 4.5 pA/rtHz, 56 nA rms | linear input 0-30 uA | none (DC-coupled) | not checked | not checked | ADI search listing; Digi-Key product highlight |
| ADA4355 | Analog Devices | uModule receiver: TIA + 1 MHz/100 MHz filter + 14-bit 125 MSPS ADC, LVDS out | 2 / 20 / 200 kOhm | set by 100 MHz (or 1 MHz) filter; 10 ns pulses | not checked | 800 uA full scale at 2 kOhm | not checked | RECOMMENDED FOR NEW DESIGNS | not checked | ADI search listing; Digi-Key product highlight |
| HMC799 | Analog Devices (Hittite) | DC-700 MHz TIA, 50 Ohm output | 10 kOhm | 700 MHz | 150 nA rms over 700 MHz; 4.6-5.6 pA/rtHz depending on C_pd | absolute max 30 mA p-p | none stated | LAST TIME BUY | not checked | ADI search listing |

## D. Application notes and references

The documents themselves are not part of the public repository; the URL column gives each source.

| Topic | Title | Author(s) | Publisher, doc. no. | Year | URL | File name | Relevance |
|---|---|---|---|---|---|---|---|
| TIA design | Transimpedance Considerations for High-Speed Amplifiers | Xavier Ramus | TI SBOA122 | 2009 | https://www.ti.com/lit/pdf/sboa122 | TI_SBOA122_transimpedance_considerations_high_speed_amps.pdf | decompensated VFB in TIAs, noise and bandwidth design |
| TIA design | What You Need to Know about Transimpedance Amplifiers - Part 1 | Samir Cherian | TI SSZTBC4 | 2023 (PDF date) | https://www.ti.com/lit/pdf/ssztbc4 | TI_SSZTBC4_what_you_need_to_know_about_TIAs_part1.pdf | loop gain, Butterworth compensation |
| TIA design | What You Need to Know about Transimpedance Amplifiers - Part 2 | Samir Cherian | TI SSZTAY1 | 2023 (PDF date) | https://www.ti.com/lit/pdf/ssztay1 | TI_SSZTAY1_what_you_need_to_know_about_TIAs_part2.pdf | arbitrary phase margin; says part 3 covers higher-order poles and decompensated amplifiers |
| TIA design | What You Need to Know about Transimpedance Amplifiers - Part 3 | Samir Cherian (expected) | TI |  | not located after three searches | not downloaded | topic per part 2: higher-order open-loop poles, decompensated amplifiers |
| Decompensated amps | AN-1604 Decompensated Operational Amplifiers (Rev. B) | TI (National Semiconductor) | TI SNOA486B | 2007, rev. 2013 | https://www.ti.com/lit/an/snoa486/snoa486.pdf | TI_SNOA486_AN-1604_decompensated_operational_amplifiers.pdf | what/why of decompensation; external and input lead-lag compensation |
| Decompensated amps | Easily improve the performance of analog circuits with decompensated amplifiers | TI Analog Design Journal | TI SLYT767A | 2019 | https://www.ti.com/lit/pdf/slyt767 | TI_SLYT767_decompensated_amplifiers_improve_analog_circuits.pdf | decompensated parts in TIAs |
| Decompensated amps | 3 Common Questions When Designing with High-speed Amplifiers | Peggy Liska | TI SSZT273 | 2023 (PDF date) | https://www.ti.com/lit/pdf/sszt273 | TI_SSZT273_3_common_questions_high_speed_amplifiers.pdf | OPA858 vs OPA859 decompensation trade-off |
| TIA design | Transimpedance Amplifier Circuit (Analog Engineer's Circuit, Rev. B) | Paul Semig | TI SBOA268B | 2024 | https://www.ti.com/lit/pdf/sboa268 | TI_SBOA268_transimpedance_amplifier_circuit.pdf | basic TIA design recipe (low speed) |
| TIA design | AN-1803 Design Considerations for a Transimpedance Amplifier | TI (National Semiconductor) | TI SNOA515A | 2008, rev. 2013 | https://www.ti.com/lit/pdf/snoa515 | TI_SNOA515_AN-1803_design_considerations_transimpedance_amplifier.pdf | TIA stability and bandwidth |
| TIA design | Compensate Transimpedance Amplifiers Intuitively | Tony Wang, Barry Ehrman | TI SBOA055A | 1993, rev. 2005 | https://www.ti.com/lit/pdf/sboa055 | TI_SBOA055_compensate_transimpedance_amplifiers_intuitively.pdf | feedback-capacitor choice |
| TIA design | TI Precision Labs: Transimpedance Amplifier-1 (slides) | Sima Jalaleddine | TI Precision Labs, High-Speed Op Amps | 2021 (PDF date) | not recorded | TI_TIPL_transimpedance_amps_introduction_slides.pdf | TIA introduction |
| Dynamic range | Maximizing the dynamic range of analog front ends having a transimpedance amplifier | TI Analog Design Journal | TI SLYT773 | 2019 | https://www.ti.com/lit/pdf/slyt773 | TI_SLYT773_maximizing_dynamic_range_AFE_with_TIA.pdf | overload, clamps, dynamic range |
| Lidar reference design | TIDA-060025: Maximizing Transimpedance Bandwidth for LIDAR and ToF Applications (Rev. A) | TI | TI TIDUEL3A | 2022 | https://www.ti.com/lit/pdf/tiduel3 | TI_TIDUEL3_TIDA-060025_maximizing_transimpedance_bandwidth_LIDAR_ToF.pdf | high-speed optical front end with decompensated op amp |
| Lidar front end | Time of Flight and LIDAR - Optical Front End Design (Rev. A) | TI | TI SBOA337A | 2022 | https://www.ti.com/lit/pdf/sboa337 | TI_SBOA337_ToF_LIDAR_optical_front_end_design.pdf | application brief |
| Noise | Noise Analysis for High-Speed Op Amps (Rev. A) | Michael Steffes | TI SBOA066A | 1996, rev. 2005 | https://www.ti.com/lit/pdf/sboa066 | TI_SBOA066_noise_analysis_high_speed_op_amps.pdf | e_n, i_n, noise-gain treatment |
| Noise | Noise Analysis of FET Transimpedance Amplifiers (AB-076) | Burr-Brown / TI | TI SBOA060 | 1994 (PDF 1999) | https://www.ti.com/lit/pdf/sboa060 | TI_SBOA060_noise_analysis_FET_transimpedance_amplifiers.pdf | e_n times input capacitance noise gain |
| Noise | Designing Photodiode Amplifier Circuits with OPA128 (AB-077) | Burr-Brown / TI | TI SBOA061 | 1994 (PDF 1999) | https://www.ti.com/lit/pdf/sboa061 | TI_SBOA061_designing_photodiode_amplifier_circuits_OPA128.pdf | photodiode amplifier noise basics |
| Noise | Comparison of Noise Performance Between a FET Transimpedance Amplifier and a Switched Integrator | Burr-Brown / TI | TI SBOA034 | 1996 | https://www.ti.com/lit/pdf/sboa034 | TI_SBOA034_noise_FET_TIA_vs_switched_integrator.pdf | low-speed comparison |
| Noise | Analysis and Measurement of Intrinsic Noise in Op Amp Circuits, Part XI: Photodiode Amplifier Noise | Art Kay, Bryan Zhao | TI TechNote, published on EN-Genius.net | 2011 | not recorded | TI_KayZhao_PartXI_photodiode_amplifier_noise.pdf | photodiode TIA noise analysis and simulation |
| Input capacitance | SPICE It Up: How to Extract the Input Capacitance of an Op Amp (Part 3) | Samir Cherian | TI SSZTBI1 | 2023 (PDF date) | https://www.ti.com/lit/pdf/ssztbi1 | TI_SSZTBI1_SPICE_it_up_extract_op_amp_input_capacitance_part3.pdf | measuring C_in, which sets the noise-gain zero |
| Input capacitance | Input Impedance Extraction and Application for High Speed Amplifiers (Insight #9) | Michael Steffes | author's note | 2019 | not recorded | Steffes_Insight9_input_impedance_extraction_high_speed_amps.pdf | input impedance of high-speed amps |
| Front ends | Photodiode Front Ends: The REAL Story | Philip C. D. Hobbs | Optics & Photonics News 12(4), 42-45 | 2001 | https://electrooptical.net/static/oldsite/www/frontends/frontends.pdf (author's site) | Hobbs_OPN2001_photodiode_front_ends_real_story.pdf | TIA noise-peak myths, bootstrapping, shot-noise-limited design |
| ADI notes | LTC6268-10 TIA design notes; Analog Dialogue photodiode TIA articles; FET current-noise rise with frequency |  | Analog Devices |  | not read: analog.com pages were not read directly | not downloaded | not checked |

## Sources not read directly

| URL | Reason |
|---|---|
| https://www.mouser.com/ProductDetail/Analog-Devices/LTC6268IS8PBF | no response |
| https://www.digikey.com/en/products/result?keywords=<PART> | search pages returned no data; one returned HTTP 403 |
| https://www.st.com/en/amplifiers-and-comparators/tsh300.html | no response |
| https://www.renesas.com/en/products/isl55190 | HTTP 404 |
| analog.com (all pages) | not read directly; only search-engine listings used |

## Open items

- 3PEAK TPH2861/TPH2865Q: lifecycle and price; TPH2865Q i_n and C_in
- LT6200-5 i_n, C_in, slew and price; LTC6268 e_n and C_in from its datasheet; MAX4104/MAX4304 GBW and output swing (datasheet not downloaded)
- ISL55190 and TSH300: maker-confirmed status
- THS4022: GBW from datasheet
- Integrated TIAs: ALC range of LMH32404 and LMH34400; status and price of MAX40660/61, LTC6560/61; MAX40658 offset-current range; ADA4355 noise
- TI 'What you need to know about TIAs' part 3: not located
- ADI app notes (LTC6268-10 TIA, Analog Dialogue, FET current-noise rise): not read; they need a download from analog.com
- Source URLs of three downloaded notes (TIPL slides, Kay/Zhao Part XI, Steffes Insight #9) were not recorded
