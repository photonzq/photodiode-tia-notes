# Vendor SPICE models used in Chapter 9

The checks of Chapter 9 read the manufacturers' SPICE models from this folder, one subfolder per part. The model files are not part of the public repository and are not covered by the note's CC0 dedication: each remains under its vendor's terms, which come with the download. To repeat the checks, download each package from the address below and unpack it so that the file in the last column sits at that path; `scripts_archive/hg_spice.py` and `scripts_archive/hg_spice_medium.py` read it from there.

| Folder | Part | Model | Download | File read by the scripts |
|---|---|---|---|---|
| `OPA928/` | OPA928 | Texas Instruments PSpice model SBOMCC0, Rev. A | https://www.ti.com/lit/zip/sbomcc0 | `OPA928/extracted/OPAx928.LIB` |
| `OPA140/` | OPA140 | Texas Instruments PSpice model SBOM493, Rev. D | https://www.ti.com/lit/zip/sbom493 | `OPA140/extracted/OPAx140.LIB` |
| `OPA828/` | OPA828 | Texas Instruments PSpice model SBOMAJ0, Rev. D | https://www.ti.com/lit/zip/sbomaj0 | `OPA828/extracted/OPAx828.LIB` |
| `OPA320/` | OPA320 | Texas Instruments PSpice model SBOM437, Rev. G | https://www.ti.com/lit/zip/sbom437 | `OPA320/extracted/OPAx320-Q1.LIB` |
| `OPA1656/` | OPA1656 | Texas Instruments PSpice model SBOMAW6, Rev. C | https://www.ti.com/lit/zip/sbomaw6 | `OPA1656/extracted/OPA1656.LIB` |
| `OPA2156/` | OPA2156 | Texas Instruments PSpice model SBOMAR0, Rev. B | https://www.ti.com/lit/zip/sbomar0 | `OPA2156/extracted/OPA2156.LIB` |
| `OPA818/` | OPA818 | Texas Instruments PSpice model SBOMB74B, the file the companion note also uses | https://www.ti.com/lit/zip/sbomb74 | `OPA818/opa818.lib` |
| `OPA657/` | OPA657 | Texas Instruments PSpice model SBOM137, Rev. F, the file the companion note also uses | https://www.ti.com/lit/zip/sbom137 | `OPA657/OPA657.lib` |
| `OPA855/` | OPA855 | Texas Instruments unencrypted PSpice model package SBOMB43D, Rev. D, the file the companion note also uses (Section 9.8) | https://www.ti.com/lit/zip/sbomb43 | `OPA855/opa855_a.lib` |
| `OPA858/` | OPA858 | Texas Instruments PSpice model SBOMBK7, the file the companion note also uses (Section 9.8) | https://www.ti.com/lit/zip/sbombk7 | `OPA858/OPA858.lib` |
| `LMH6629/` | LMH6629 | Texas Instruments (National Semiconductor) PSpice model SNOM133, the file the companion note also uses, with the COMP pin tied high (Section 9.8) | https://www.ti.com/lit/zip/snom133 | `LMH6629/LMH6629.MOD` |
| `OPA955/` | OPA955 | Texas Instruments TINA-TI model SLOM544, netlist dated 2026-07-06. TI supplies it only as a TINA-TI file; the companion note's `scripts_archive/extract_tina_model.py` copies the netlist out of `OPA955.TSM` unchanged, and the file here is that copy (Section 9.8) | https://www.ti.com/lit/zip/slom544 | `OPA955/OPA955_from_TINA.lib` |
| `ADA4817-1/` | ADA4817-1 | Analog Devices SPICE model, Rev. 2.1 | The companion note's folder of this repository includes the file unmodified, under ADI's terms: `../../TIA_opamp_survey_2026-10-25/spice/models/ADA4817-1/ada4817.cir` | `ADA4817-1/ada4817.cir` |

The Analog Devices models of ADA4530-1, ADA4625-1, LTC6268-10, AD8304 and ADL5303 are not needed here. They ship with LTspice and are read from its library (`ADI1.lib`, `ADA4625-1.sub`, `LTC2.lib`, `AD8304.lib` and `ADL5303.sub`). The LSBF862 model card used for the composite of Section 9.5 is Linear Integrated Systems' published card, typed into `scripts_archive/hg_spice.py` as it was typed in the companion note; it remains their model and is not covered by the note's dedication.
