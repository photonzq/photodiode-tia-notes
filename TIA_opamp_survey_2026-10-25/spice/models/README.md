# Vendor SPICE models: origin, terms, and whether they may be shared

The models below are the manufacturers' files, used unmodified. The scripts in `../../scripts_archive/` translate them into `../runs/_models/` before use (Appendix B.1 of the survey); those translated copies are never shared. None of these files is covered by the survey's own license: each stays under its manufacturer's terms. Of the model files, only the four ADI files below are part of the public repository; every other one is downloaded from its maker.

## May be shared with the survey (unmodified, under ADI's terms)

Analog Devices' SPICE model license (shown on analog.com before each download, and referenced in the header of each file) allows its models to be included with software that is distributed, provided the redistributed copies are not changed except by adding comments or by renaming for a simulator, and provided the models are not sold, rented or licensed onward. The four files below are ADI's own models (each header carries an Analog Devices copyright), not third-party models, which ADI's license excludes from redistribution.

| Part | File | Model revision | Product page |
|---|---|---|---|
| ADA4817-1 | `ADA4817-1/ada4817.cir` | Rev. 2.1, Oct 2017 | https://www.analog.com/en/products/ada4817-1.html |
| AD8099 | `AD8099/ad8099.cir` | Rev. 3.0, Sep 2015 | https://www.analog.com/en/products/ad8099.html |
| ADA4899-1 | `ADA4899-1/ada4899.cir` | Rev. 3.0, Sep 2015 | https://www.analog.com/en/products/ada4899-1.html |
| ADA4895-1 | `ADA4895-1/ADA4895.cir` | Rev. 2.1, Jul 2016 | https://www.analog.com/en/products/ada4895-1.html |

## Not to be shared: download them from ti.com

Texas Instruments' notice on its design resources (the "Important Notice and Disclaimer" at the end of every TI datasheet, e.g. the OPA657 datasheet SBOS197F, p. 40) permits their use only for developing an application with the TI part, and prohibits other reproduction. Several files add their own terms:

| Part | File | Terms in the file itself | Verdict |
|---|---|---|---|
| OPA855, OPA818, OPA856 | `opa855_a.lib`, `opa818.lib`, `opa856_a.lib` | Copyright notice only, no grant | Do not share |
| OPA858, OPA859, OPA846 | `OPA858.lib`, `OPA859.lib`, `OPA846.LIB` | Copyright, all rights reserved; warranty disclaimer | Do not share |
| OPA657, OPA847 | `OPA657.lib`, `OPA847_Model.sub` | Copying only with TI's written consent | Do not share |
| THS4021 | `ths4021.lib` | A use-only license for the user; no right to pass the model on | Do not share |
| LMH6629, LMH6624 | `LMH6629.MOD`, `LMH6624.MOD` | National Semiconductor notice: may be copied and distributed without modification, not resold or licensed | Permitted by the file's own notice, but in conflict with TI's present notice for its resources; not shared here |
| OPA955, OPA817, OPA814 | the TINA-TI files and the netlists extracted from them (`*_from_TINA.lib`) | Copyright notice only, no grant | Do not share |
| THS3491 | `THS3491/extracted/sbombp9/ths3491.lib` from TI SBOMBP9 (TINA-TI/PSpice "All In One" model v1.0, 2/16/18, subcircuit `THS3491RGT`, pins INP INN OUT PD_not VCC VEE GND). Not used: SBOMAN4, the same RGT netlist with an extra FB pin tied to OUT through 1 µΩ, and SBOMAI5, the DDA-package model (C_C9 4.7 pF and R_R28 280 Ω where the RGT model has 4 pF and 200 Ω) | Copyright, all rights reserved; warranty disclaimer | Do not share |

The download links and the file to take from each package are in `../../scripts_archive/README.md`. The package archives (`*.zip`) and the `extracted/` folders are never shared.

## The discrete transistors of the composites (Section 7.1 of the survey)

| Part | File or card | Terms | Verdict |
|---|---|---|---|
| BFP740ESD | `BFP740ESD/bfp740esd-spice-v2.mdl`, Infineon's Gummel–Poon model with the SOT-343 package and the ESD-protection network, version 2.0 of June 2011, valid to 10 GHz, subcircuit pins C B E1 E2; downloaded from https://www.infineon.com/assets/row/public/documents/24/70/bfp740esd-spice-v2.mdl | Copyright notice "(C) 2011 Infineon Technologies AG" only, no grant | Do not share; download from infineon.com |
| LSBF862 | the card printed in Linear Systems' "Updated LSBF862 SPICE Model, Rev 2 as of 02/09/2026" (reference [S23] of the survey), typed into `FET_CARDS` of `../../scripts_archive/spice_composite_checks.py` with every parameter unchanged and the model renamed from LSBF862_UPDATED to LSBF862 | None stated on the page | Reproduced in that script, credited to Linear Systems; it remains Linear Systems' model and is not covered by the survey's licence |
| CPH3910, CE3512K2 | NJF cards built for the survey from the datasheets (survey Section 7.3, Table A7.10), in `FET_CARDS` of `../../scripts_archive/spice_composite_checks.py` | The survey's own work | May be shared with the survey |

The scripts write all four transistors' cards and the translated BFP740ESD model into `../runs/_models/` (`fet_cards.lib` and its includes); like every file there, those copies are not shared.
