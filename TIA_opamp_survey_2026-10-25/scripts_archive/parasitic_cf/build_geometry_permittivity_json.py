"""Build data/parasitic_cf/geometry_and_permittivity.json from values transcribed by eye
from rendered pages of manufacturer documents (chip-resistor body dimensions, recommended
land patterns, and the relative permittivity of alumina, FR-4 laminates, solder masks and
epoxy mould compounds, plus the leadframe thickness of a 0.5 mm pitch SON package).

Usage:
    python -I build_geometry_permittivity_json.py <output.json>

Every number below was read from the page image named in the record (page numbers count
as a PDF viewer counts them).  The script only expands the compact tables into a flat list
of records and computes min/max from the stated tolerances; it does not read any PDF.
Records flagged "derived": true are arithmetic on stated values (formula in "notes").
"""
import json
import re
import sys
from decimal import Decimal

# ---------------------------------------------------------------------------------------
# Document registry
# ---------------------------------------------------------------------------------------
DOCS = {
    "PANA_ERJ": dict(
        manufacturer="Panasonic Industry Co., Ltd.",
        document_title="Thick Film Chip Resistors, ERJ type, ERJ XG, 1G, 2G, 3G, 6G series",
        document_number="AOA0000C301",
        revision_or_date="pages 1-3 dated 22-Dec-22 (PDF modified 2026-03-25)",
        url="https://industrial.panasonic.com/cdbs/www-data/pdf/RDA0000/AOA0000C301.pdf",
        local_file="Panasonic_AOA0000C301_ERJ_thick_film_general.pdf"),
    "PANA_ERJP": dict(
        manufacturer="Panasonic Industry Co., Ltd.",
        document_title="Precision Thick Film Chip Resistors, ERJ type (ERJ 1R, 2R, 3R, 6R; 2RK, 3EK, 6EN ...)",
        document_number="AOA0000C304",
        revision_or_date="pages 1-4 dated 29-May-25",
        url="https://industrial.panasonic.com/cdbs/www-data/pdf/RDA0000/AOA0000C304.pdf",
        local_file="Panasonic_AOA0000C304_ERJ_precision_thick_film.pdf"),
    "PANA_ERA": dict(
        manufacturer="Panasonic Industry Co., Ltd.",
        document_title="Metal Film (Thin Film) Chip Resistors, High Reliability Type, ERA*A",
        document_number="AOA0000C307",
        revision_or_date="pages 1-3 dated 24-Apr-24",
        url="https://industrial.panasonic.com/cdbs/www-data/pdf/RDM0000/AOA0000C307.pdf",
        local_file="Panasonic_AOA0000C307_ERA_thin_film_high_reliability.pdf"),
    "PANA_LAND": dict(
        manufacturer="Panasonic Industry Co., Ltd.",
        document_title="Surface Mount Resistors, Land Pattern (Recommended land pattern dimensions)",
        document_number="DMM0000COL17",
        revision_or_date="pages dated 24-Dec-25",
        url="https://industrial.panasonic.com/cdbs/www-data/pdf/RDM0000/DMM0000COL17.pdf",
        local_file="Panasonic_DMM0000COL17_recommended_land_pattern_dimensions.pdf"),
    "YAGEO_RC": dict(
        manufacturer="YAGEO Corporation",
        document_title="Data sheet: General purpose chip resistors, RC_L series, sizes 0075-2512",
        document_number="PYu-RC_Group_51_RoHS_L",
        revision_or_date="Product specification V.14, November 14, 2025",
        url="https://yageogroup.com/content/datasheet/asset/file/PYU-RC_GROUP_51_ROHS_L",
        local_file="Yageo_PYu-RC_Group_51_RoHS_L_RC_thick_film.pdf"),
    "YAGEO_RT": dict(
        manufacturer="YAGEO Corporation",
        document_title="Data sheet: Thin film chip resistors, high precision - high stability, RT series 0.01% to 1%, TCR 5 to 50",
        document_number="PYu-RT_1-to-0.01_RoHS_L",
        revision_or_date="Product specification V.17, February 12, 2026",
        url="https://yageogroup.com/content/datasheet/asset/file/PYU-RT_1-TO-0-01_ROHS_L",
        local_file="Yageo_PYU-RT_1-to-0.01_RoHS_L_RT_thin_film.pdf"),
    "YAGEO_MOUNT": dict(
        manufacturer="YAGEO Corporation",
        document_title="Data sheet: Chip resistors, Mounting",
        document_number="PYu-R_Mount_10",
        revision_or_date="Product specification V.10, February 13, 2018",
        url="https://yageogroup.com/content/Resource%20Library/Product%20Guide-Catalog/yageo_PYu-R_Mount_10_19050818_343.pdf",
        local_file="Yageo_PYu-R_Mount_10_chip_resistors_mounting.pdf"),
    "VISHAY_CRCW": dict(
        manufacturer="Vishay Intertechnology (Vishay Draloric)",
        document_title="D/CRCW e3 Standard Thick Film Chip Resistors",
        document_number="20035",
        revision_or_date="Revision 14-Apr-2026",
        url="https://www.vishay.com/docs/20035/dcrcwe3.pdf",
        local_file="Vishay_20035_CRCW_e3_thick_film.pdf"),
    "VISHAY_TNPW": dict(
        manufacturer="Vishay Intertechnology (Vishay Draloric/Beyschlag)",
        document_title="TNPW e3 High Stability Thin Film Flat Chip Resistors",
        document_number="28758",
        revision_or_date="Revision 10-Apr-2026",
        url="https://www.vishay.com/docs/28758/tnpw_e3.pdf",
        local_file="Vishay_28758_TNPW_e3_thin_film.pdf"),
    "VISHAY_PAD": dict(
        manufacturer="Vishay Intertechnology (Vishay Draloric/Beyschlag)",
        document_title="Recommended Solder Pad Dimensions, Vishay Draloric / Beyschlag Surface-Mount Resistors and Fuses",
        document_number="28950",
        revision_or_date="Revision 12-Jul-2022",
        url="https://www.vishay.com/docs/28950/recsoldpaddims-drabeyresfus.pdf",
        local_file="Vishay_28950_solder_pad_dimensions.pdf"),
    "VISHAY_60107": dict(
        manufacturer="Vishay Intertechnology (Vishay Thin Film)",
        document_title="Frequency Response of Thin Film Chip Resistors (Technical Note)",
        document_number="60107",
        revision_or_date="Revision 04-Feb-09",
        url="https://www.vishay.com/docs/60107/freqresp.pdf",
        local_file="Vishay_60107_frequency_response_thin_film_chip_resistors.pdf"),
    "KOA_RK73B": dict(
        manufacturer="KOA Speer Electronics, Inc.",
        document_title="RK73B general purpose 2%, 5% tolerance thick film chip resistor",
        document_number="RK73B (catalog pages 21-22)",
        revision_or_date="page 1 dated 10/26/25",
        url="https://www.koaspeer.com/pdfs/RK73B.pdf",
        local_file="KOA_Speer_RK73B_thick_film_general.pdf"),
    "KOA_RK73H": dict(
        manufacturer="KOA Speer Electronics, Inc.",
        document_title="RK73H precision 0.5%, 1% tolerance thick film chip resistor",
        document_number="RK73H (catalog pages 23-24)",
        revision_or_date="page 1 dated 10/26/25",
        url="https://www.koaspeer.com/pdfs/RK73H.pdf",
        local_file="KOA_Speer_RK73H_thick_film_precision.pdf"),
    "KOA_RN73H": dict(
        manufacturer="KOA Speer Electronics, Inc.",
        document_title="RN73H long term precision thin (metal) film flat chip resistors (high reliability, for automotive)",
        document_number="RN73H (catalog pages 32-33)",
        revision_or_date="page 1 dated 08/14/26",
        url="https://www.koaspeer.com/pdfs/RN73H.pdf",
        local_file="KOA_Speer_RN73H_thin_film.pdf"),
    "KOA_APPB": dict(
        manufacturer="KOA Speer Electronics, Inc.",
        document_title="Appendix B, pad dimensions (standard soldering pad dimensions)",
        document_number="Appendix B (catalog pages 267-270)",
        revision_or_date="page 1 (reflow) dated 04/15/26; page 3 (flow) dated 3/28/25",
        url="https://www.koaspeer.com/pdfs/Appendix_B.pdf",
        local_file="KOA_Speer_Appendix_B_pad_dimensions.pdf"),
    "TT_WCR": dict(
        manufacturer="TT Electronics plc",
        document_title="General Purpose Surface Mounted Resistors, WCR Series",
        document_number="WCR",
        revision_or_date="issue 09.26",
        url="https://www.ttelectronics.com/TTElectronics/media/ProductFiles/Datasheets/WCR.pdf",
        local_file="TT_Electronics_WCR_thick_film_chip.pdf"),
    "TT_PCF": dict(
        manufacturer="TT Electronics plc",
        document_title="Precision Thin Film Nichrome Chip Resistors, PCF Series",
        document_number="PCF",
        revision_or_date="issue 07.26",
        url="https://www.ttelectronics.com/TTElectronics/media/ProductFiles/Datasheets/PCF.pdf",
        local_file="TT_Electronics_PCF_thin_film_chip.pdf"),
    "KYO_CAT": dict(
        manufacturer="KYOCERA Corporation",
        document_title="Characteristics of Fine Ceramics (catalog), Characteristic Table of Fine Ceramics",
        document_number="008/026/2505",
        revision_or_date="(c) 2025; PDF dated 2026-03-27",
        url="https://global.kyocera.com/prdct/fc/pdf/catalog/material.pdf",
        local_file="Kyocera_fine_ceramics_material_characteristics.pdf"),
    "KYO_WEB": dict(
        manufacturer="KYOCERA Corporation",
        document_title="Alumina (Al2O3) Packages / Substrates, Material Properties (web page)",
        document_number="-",
        revision_or_date="retrieved 2026-11-04",
        url="https://global.kyocera.com/prdct/semicon/search_material/detail/alumina.html",
        local_file="Kyocera_semicon_alumina_material_page.html"),
    "CT_2026": dict(
        manufacturer="CeramTec GmbH",
        document_title="Advanced Ceramics for Electronic Applications: Material properties of Rubalit, Alunit, Zirkolit and Sinalit",
        document_number="CA240158/EN/2601/IM",
        revision_or_date="(c) 2026; PDF dated 2026-05-20",
        url="https://ceramtec-group.com/fileadmin/user_upload/Corporate/11_Downloads/06_Electronic_Heatsinks/Datasheet_Electronic_Applications.pdf",
        local_file="CeramTec_Datasheet_Electronic_Applications.pdf"),
    "CT_2022": dict(
        manufacturer="CeramTec GmbH",
        document_title="Advanced Ceramics for Electronic Applications: Material properties of Rubalit, Alunit and Zirkolit",
        document_number="CA210105/EN/2111/IM",
        revision_or_date="PDF dated 2022-04-01",
        url="https://configure.ceramtec-group.com/assets/substrates/configurator/Datasheet_Advanced_Ceramics_Electronics.pdf",
        local_file="CeramTec_Datasheet_Advanced_Ceramics_Electronics.pdf"),
    "COORS_9215": dict(
        manufacturer="CoorsTek, Inc.",
        document_title="Electronic Substrates Overview, Thin-Film & Thick-Film Ceramic Substrates",
        document_number="02381 F",
        revision_or_date="(c) 2025; PDF dated 2025-10-02",
        url="https://coorstek.com/media/9215/electronic-substrates-overview-thin-film-thick-film-ceramic-substrates.pdf",
        local_file="CoorsTek_9215_electronic_substrates_overview.pdf"),
    "COORS_02084": dict(
        manufacturer="CoorsTek, Inc.",
        document_title="Semiconductor Oxides Material Properties (chart)",
        document_number="02084 REV E",
        revision_or_date="(c) 2025; PDF dated 2025-11-22",
        url="https://www.coorstek.com/media/8908/semiconductor-oxides-material-properties-chart-02084.pdf",
        local_file="CoorsTek_02084_RevE_semiconductor_oxides_properties_chart.pdf"),
    "ISOLA": dict(
        manufacturer="Isola Group",
        document_title="370HR Industry Leading, Standard Loss, Thermally Robust Epoxy Laminate and Prepreg",
        document_number="370HR data sheet",
        revision_or_date="footer: Revision No: C, last updated April 15, 2021 (revision list ends with D, 4/21)",
        url="https://www.isola-group.com/wp-content/uploads/data-sheets/370hr.pdf",
        local_file="Isola_370HR_laminate_prepreg_data_sheet.pdf"),
    "PANA_R1755V": dict(
        manufacturer="Panasonic Corporation, Electronic Materials Business Division",
        document_title="Laminate R-1755V, Prepreg R-1650V Data Sheet, High Reliability Glass Epoxy Multi-layer Materials (High Tg & Low CTE type)",
        document_number="No. 19070536",
        revision_or_date="Jul. 2019",
        url="https://api.pim.na.industrial.panasonic.com/file_stream/main/fileversion/180183",
        local_file="Panasonic_R-1755V_R-1650V_data_sheet_No19070536.pdf"),
    "VENTEC_DS": dict(
        manufacturer="Ventec International Group",
        document_title="VT-47 Laminate/Prepreg, Properties Sheet IPC-4101E /97 /98 /99 /101 /126",
        document_number="VT-47 (Version B4 /97 /98 /99 /101 /126)",
        revision_or_date="published 19/03/20",
        url="https://www.ventec-group.com/media/113588/200319vt-47-v2.pdf",
        local_file="Ventec_VT-47_datasheet_200319_v2.pdf"),
    "VENTEC_PG": dict(
        manufacturer="Ventec International Group",
        document_title="VT-47 Process Guide (VT-47 CCL/Laminate, VT-47 PP/Prepreg)",
        document_number="VT-47 process guide",
        revision_or_date="Version 12/08/2025",
        url="https://www.ventec-group.com/media/115109/250812-vt-47-pgl.pdf",
        local_file="Ventec_VT-47_PGL_250812.pdf"),
    "TAIYO_G24K": dict(
        manufacturer="Taiyo Ink Mfg. Co., Ltd.",
        document_title="Technical data (Japanese), developable solder resist PSR-4000 G24K/CA-40 G24 (green)",
        document_number="MS-00150100, MS-00140800",
        revision_or_date="2016.02 (archived copy of 2017-09-20)",
        url="https://web.archive.org/web/20170920220534/http://www.taiyo-hd.co.jp/_cms/wp-content/uploads/2016/01/PSR4000G24K_CA40G24_TD_J.pdf",
        local_file="Taiyo_PSR-4000_G24K_CA-40_G24_TDS_JA_2016-02_archived.pdf"),
    "TAIYO_EG23": dict(
        manufacturer="Taiyo Ink Mfg. Co., Ltd.",
        document_title="Technical data (Japanese), developable solder resist PSR-4000 EG23/CA-40 G23K (black)",
        document_number="MS-00139200, MS-00137100",
        revision_or_date="2016.02 (archived copy of 2017-09-20)",
        url="https://web.archive.org/web/20170920232339/http://www.taiyo-hd.co.jp/_cms/wp-content/uploads/2016/01/PSR4000EG23_CA40G23K_TD_J.pdf",
        local_file="Taiyo_PSR-4000_EG23_CA-40_G23K_TDS_JA_2016-02_archived.pdf"),
    "TAIYO_D10ME": dict(
        manufacturer="Taiyo Ink Mfg. Co., Ltd.",
        document_title="Technical Data Sheet PSR-4000 D10ME/CA-40 D10 (black, matte)",
        document_number="MS-00255201, MS-00255301",
        revision_or_date="Feb. 2016 (archived copy of 2017-10-15)",
        url="https://web.archive.org/web/20171015140334/http://www.taiyo-hd.co.jp/_cms/wp-content/uploads/2016/01/PSR4000D10ME_CA40D10_TD_E.pdf",
        local_file="Taiyo_PSR-4000_D10ME_CA-40_D10_TDS_Feb2016_archived.pdf"),
    "PETERS": dict(
        manufacturer="Lackwerke Peters GmbH + Co. KG",
        document_title="Technical Report Elpemer 2467 (two-pack photoimageable solder resist)",
        document_number="-",
        revision_or_date="PDF dated 2015-02-18 (copy hosted by a PCB manufacturer)",
        url="https://www.wedirekt.com/web/cms/content/_files//pdf1/technical_report_elpemer_2467.pdf",
        local_file="Peters_Elpemer_2467_technical_report_hosted_wedirekt.pdf"),
    "IPC_S12_2": dict(
        manufacturer="IPC conference paper (authors from Intel and Taiyo America)",
        document_title="Loss Tangent and Dielectric Constant of Solder Mask Measured with Split-Post Dielectric Resonators",
        document_number="S12-2",
        revision_or_date="2005 (PDF dated 2005-02-02)",
        url="https://www.electronics.org/system/files/technical_resource/E17%26S12-2.pdf",
        local_file="IPC_APEX2005_S12-2_solder_mask_Dk_SPDR_Intel_TaiyoAmerica.pdf"),
    "PANA_CV8710": dict(
        manufacturer="Panasonic Corporation, Electronic Materials Business Division",
        document_title="Data Sheet, Encapsulation Materials, CV8710 series",
        document_number="No. 200908-3",
        revision_or_date="Sep. 2020",
        url="https://api.pim.na.industrial.panasonic.com/file_stream/main/fileversion/247174",
        local_file="Panasonic_CV8710_series_EMC_data_sheet_No200908-3.pdf"),
    "HITACHI_CEL": dict(
        manufacturer="Hitachi Chemical (now Resonac)",
        document_title="Technical data sheet of Hitachi Chemical Epoxy molding compound, CEL-9220HF10",
        document_number="-",
        revision_or_date="PDF dated 2016-01-04 (copy attached to a TI E2E forum post)",
        url="https://e2e.ti.com/cfs-file/__key/communityserver-discussions-components-files/196/TDS-of-CEL_2D00_9220HF10.pdf",
        local_file="Hitachi_Chemical_CEL-9220HF10_EMC_TDS_hosted_TI_E2E.pdf"),
    "TI_E2E": dict(
        manufacturer="Texas Instruments (E2E forum)",
        document_title="PCA9306-Q1: the relative dielectric constants of the molding compound (forum thread 1440097)",
        document_number="-",
        revision_or_date="thread locked; retrieved 2026-11-04",
        url="https://e2e.ti.com/support/interface-group/interface/f/interface-forum/1440097/pca9306-q1-the-relative-dielectric-constants-of-the-molding-compound",
        local_file=None),
    "TI_OPA855": dict(
        manufacturer="Texas Instruments",
        document_title="OPA855 8GHz Gain Bandwidth Product, Gain of 7V/V Stable, Bipolar Input Amplifier datasheet (Rev. D); package outline DSG0008A",
        document_number="SBOS622D; drawing 4218900/E 08/2022",
        revision_or_date="Rev. D (PDF dated 2026-09-04)",
        url="https://www.ti.com/lit/ds/symlink/opa855.pdf",
        local_file="TI_OPA855_datasheet_SBOS622D_DSG0008A_outline.pdf"),
    "TI_SCBA017": dict(
        manufacturer="Texas Instruments",
        document_title="Quad Flatpack No-Lead Logic Packages (Rev. D)",
        document_number="SCBA017D",
        revision_or_date="2004 (PDF dated 2004-04-15)",
        url="https://www.ti.com/lit/an/scba017d/scba017d.pdf",
        local_file="TI_SCBA017D_QFN_logic_packages_RGY.pdf"),
    "TI_SLUA271": dict(
        manufacturer="Texas Instruments",
        document_title="QFN and SON PCB Attachment (Rev. C)",
        document_number="SLUA271C",
        revision_or_date="Rev. C (PDF dated 2023-12-07)",
        url="https://www.ti.com/lit/an/slua271c/slua271c.pdf",
        local_file="TI_SLUA271_QFN_SON_PCB_attachment.pdf"),
}

RECORDS = []


def tol_range(value, tol):
    """Return (min, max) for a numeric nominal value and a tolerance string such as
    '+/-0.05', '+0.10/-0.05' or 'max'.  Percentage tolerances, free text and empty
    strings give (None, None)."""
    if not isinstance(value, (int, float)) or not tol or "%" in tol:
        return None, None
    v = Decimal(str(value))
    m = re.match(r"\+/-\s*([0-9.]+)\s*$", tol)
    if m:
        d = Decimal(m.group(1))
        return float(v - d), float(v + d)
    m = re.match(r"\+([0-9.]+)/-([0-9.]+)\s*$", tol)
    if m:
        return float(v - Decimal(m.group(2))), float(v + Decimal(m.group(1)))
    if tol.startswith("max"):
        return None, float(v)
    return None, None


def add(item, doc, quantity, value, unit, tol="", page=None, fig="", part="", size=None,
        technology=None, definition=None, frequency=None, conditions=None, notes=None,
        vmin=None, vmax=None, derived=False):
    rec = dict(item=item, quantity=quantity, size_eia_inch=size, technology=technology,
               value=value, unit=unit, tolerance_or_range=tol or None)
    lo, hi = tol_range(value, tol) if isinstance(value, (int, float)) else (None, None)
    rec["min"] = vmin if vmin is not None else lo
    rec["max"] = vmax if vmax is not None else hi
    rec.update(frequency=frequency, conditions=conditions, definition=definition,
               part_or_material=part)
    rec.update(DOCS[doc])
    rec.update(pdf_page=page, figure_or_table=fig)
    if derived:
        rec["derived"] = True
    rec["notes"] = notes
    RECORDS.append(rec)


# ---------------------------------------------------------------------------------------
# Item 1: chip-resistor body dimensions
# columns: size, part, (L, tol), (W, tol), (H, tol), (top, tol), (bottom, tol)
# ---------------------------------------------------------------------------------------
BODY = {
    "PANA_ERJ": dict(
        tech="thick film", page=3, fig="Dimensions (not to scale): drawing and table",
        labels=("L", "W", "T", "a (top)", "b (bottom)"),
        rows=[("0201", "ERJ1G", (0.60, "+/-0.03"), (0.30, "+/-0.03"), (0.23, "+/-0.03"), (0.10, "+/-0.05"), (0.15, "+/-0.05")),
              ("0402", "ERJ2G", (1.00, "+/-0.05"), (0.50, "+/-0.05"), (0.35, "+/-0.05"), (0.20, "+/-0.10"), (0.25, "+/-0.05")),
              ("0603", "ERJ3G", (1.60, "+/-0.15"), (0.80, "+0.15/-0.05"), (0.45, "+/-0.10"), (0.30, "+/-0.20"), (0.30, "+/-0.15")),
              ("0805", "ERJ6G", (2.00, "+/-0.20"), (1.25, "+/-0.10"), (0.60, "+/-0.10"), (0.40, "+/-0.20"), (0.40, "+/-0.20")),
              ("1206", "ERJ8G", (3.20, "+0.05/-0.20"), (1.60, "+0.05/-0.15"), (0.60, "+/-0.10"), (0.50, "+/-0.20"), (0.50, "+/-0.20"))],
        note="The precision thick-film series (ERJ1R, 2R, 3R/3E, 6R/6E; AOA0000C304 page 4) lists identical dimensions."),
    "YAGEO_RC": dict(
        tech="thick film", page=4, fig="Fig. 9 Chip resistor outlines; Table 1",
        labels=("L", "W", "H", "I1 (top)", "I2 (bottom)"),
        rows=[("0201", "RC0201", (0.60, "+/-0.03"), (0.30, "+/-0.03"), (0.23, "+/-0.03"), (0.10, "+/-0.05"), (0.15, "+/-0.05")),
              ("0402", "RC0402", (1.00, "+/-0.05"), (0.50, "+/-0.05"), (0.35, "+/-0.05"), (0.20, "+/-0.10"), (0.25, "+/-0.10")),
              ("0603", "RC0603", (1.60, "+/-0.10"), (0.80, "+/-0.10"), (0.45, "+/-0.10"), (0.25, "+/-0.15"), (0.25, "+/-0.15")),
              ("0805", "RC0805", (2.00, "+/-0.10"), (1.25, "+/-0.10"), (0.50, "+/-0.10"), (0.35, "+/-0.20"), (0.35, "+/-0.20")),
              ("1206", "RC1206", (3.10, "+/-0.10"), (1.60, "+/-0.10"), (0.55, "+/-0.10"), (0.45, "+/-0.20"), (0.45, "+/-0.20"))],
        note=None),
    "VISHAY_CRCW": dict(
        tech="thick film", page=11, fig="DIMENSIONS drawing; DIMENSIONS AND MASS table",
        labels=("L", "W", "H", "T2 (top)", "T1 (bottom)"),
        rows=[("0402", "CRCW0402 e3", (1.0, "+/-0.05"), (0.5, "+/-0.05"), (0.35, "+/-0.05"), (0.2, "+/-0.10"), (0.25, "+/-0.10")),
              ("0603", "CRCW0603 e3", (1.55, "+0.10/-0.05"), (0.85, "+/-0.10"), (0.45, "+/-0.05"), (0.3, "+/-0.20"), (0.3, "+/-0.20")),
              ("0805", "CRCW0805 e3", (2.0, "+0.20/-0.10"), (1.25, "+/-0.15"), (0.5, "+/-0.10"), (0.3, "+/-0.20"), (0.3, "+0.20/-0.10")),
              ("1206", "CRCW1206 e3", (3.2, "+0.10/-0.20"), (1.6, "+/-0.15"), (0.55, "+/-0.05"), (0.4, "+/-0.20"), (0.45, "+/-0.20"))],
        note="CRCW e3 starts at 0402; no 0201 in this data sheet."),
    "KOA_RK73B": dict(
        tech="thick film", page=1, fig="dimensions and construction: drawing and table (mm values in italics)",
        labels=("L", "W", "t", "c (top)", "d (bottom)"),
        rows=[("0201", "RK73B1H", (0.6, "+/-0.03"), (0.3, "+/-0.03"), (0.23, "+/-0.03"), (0.1, "+/-0.05"), (0.15, "+/-0.05")),
              ("0402", "RK73B1E", (1.0, "+0.1/-0.05"), (0.5, "+/-0.05"), (0.35, "+/-0.05"), (0.2, "+/-0.1"), (0.25, "+0.05/-0.1")),
              ("0603", "RK73B1J", (1.6, "+/-0.2"), (0.8, "+/-0.1"), (0.45, "+/-0.1"), (0.3, "+/-0.1"), (0.3, "+/-0.1")),
              ("0805", "RK73B2A", (2.0, "+/-0.2"), (1.25, "+/-0.1"), (0.5, "+/-0.1"), (0.4, "+/-0.2"), (0.3, "+0.2/-0.1")),
              ("1206", "RK73B2B", (3.2, "+/-0.2"), (1.6, "+/-0.2"), (0.6, "+/-0.1"), (0.5, "+/-0.3"), (0.4, "+0.2/-0.1"))],
        note="RK73H (precision 0.5%/1%, page 1 dated 10/26/25) lists the same numbers for 1H, 1E, 1J and 2A; the AEC 'AT' variants differ."),
    "TT_WCR": dict(
        tech="thick film", page=1, fig="Physical Data: dimensions table and drawing (tolerances +/-0.1 unless stated)",
        labels=("L", "W", "T", "C (top)", "A (bottom)"),
        rows=[("0201", "WCR0201", (0.6, "+/-0.03"), (0.3, "+/-0.03"), (0.23, "+/-0.03"), (0.1, "+/-0.05"), (0.15, "+/-0.05")),
              ("0402", "WCR0402", (1.0, "+/-0.1"), (0.5, "+/-0.05"), (0.35, "+/-0.05"), (0.2, "+/-0.1"), (0.25, "+/-0.1")),
              ("0603", "WCR0603", (1.6, "+/-0.1"), (0.8, "+/-0.1"), (0.45, "+/-0.1"), (0.3, "+/-0.2"), (0.3, "+/-0.2")),
              ("0805", "WCR0805", (2.0, "+/-0.15"), (1.25, "+0.15/-0.1"), (0.55, "+/-0.1"), (0.4, "+/-0.2"), (0.4, "+/-0.2")),
              ("1206", "WCR1206", (3.1, "+/-0.15"), (1.55, "+0.15/-0.1"), (0.55, "+/-0.1"), (0.45, "+/-0.2"), (0.45, "+/-0.2"))],
        note="Tolerances not printed in a cell take the table's default of +/-0.1 mm; for 0603 and 0805 one merged cell gives C and A."),
    "PANA_ERA": dict(
        tech="thin film", page=3, fig="Dimensions (not to scale): drawing and table",
        labels=("L", "W", "T", "a (top)", "b (bottom)"),
        rows=[("0201", "ERA1A", (0.60, "+/-0.03"), (0.30, "+/-0.03"), (0.23, "+/-0.03"), (0.15, "+/-0.05"), (0.15, "+/-0.05")),
              ("0402", "ERA2A", (1.00, "+/-0.10"), (0.50, "+0.10/-0.05"), (0.35, "+/-0.05"), (0.15, "+/-0.10"), (0.25, "+/-0.10")),
              ("0603", "ERA3A", (1.60, "+/-0.20"), (0.80, "+/-0.20"), (0.45, "+/-0.10"), (0.30, "+/-0.20"), (0.30, "+/-0.20")),
              ("0805", "ERA6A", (2.00, "+/-0.20"), (1.25, "+/-0.10"), (0.50, "+/-0.10"), (0.40, "+/-0.25"), (0.40, "+/-0.25"))],
        note=None),
    "YAGEO_RT": dict(
        tech="thin film", page=4, fig="Fig. 5 Chip resistor outlines; Table 1",
        labels=("L", "W", "H", "I1 (top)", "I2 (bottom)"),
        rows=[("0201", "RT0201", (0.60, "+/-0.03"), (0.30, "+/-0.03"), (0.23, "+/-0.03"), (0.10, "+/-0.05"), (0.15, "+/-0.05")),
              ("0402", "RT0402", (1.00, "+/-0.10"), (0.50, "+/-0.05"), (0.30, "+/-0.05"), (0.20, "+/-0.10"), (0.25, "+/-0.10")),
              ("0603", "RT0603", (1.60, "+/-0.10"), (0.80, "+/-0.10"), (0.45, "+/-0.10"), (0.25, "+/-0.15"), (0.25, "+/-0.15")),
              ("0805", "RT0805", (2.00, "+/-0.10"), (1.25, "+/-0.10"), (0.50, "+/-0.10"), (0.35, "+/-0.20"), (0.35, "+/-0.20"))],
        note=None),
    "VISHAY_TNPW": dict(
        tech="thin film", page=15, fig="DIMENSIONS drawing; DIMENSIONS AND MASS table",
        labels=("L", "W", "H", "Tt (top)", "Tb (bottom)"),
        rows=[("0201", "TNPW0201 e3", (0.6, "+/-0.05"), (0.3, "+/-0.05"), (0.23, "+/-0.03"), (0.12, "+/-0.05"), (0.12, "+/-0.05")),
              ("0402", "TNPW0402 e3", (1.0, "+/-0.05"), (0.5, "+/-0.05"), (0.35, "+/-0.05"), (0.2, "+/-0.10"), (0.2, "+/-0.10")),
              ("0603", "TNPW0603 e3", (1.55, "+/-0.05"), (0.85, "+/-0.10"), (0.45, "+/-0.10"), (0.3, "+/-0.20"), (0.3, "+/-0.20")),
              ("0805", "TNPW0805 e3", (2.0, "+/-0.1"), (1.25, "+/-0.15"), (0.45, "+/-0.10"), (0.4, "+/-0.20"), (0.4, "+/-0.20"))],
        note="The table gives one column 'Tt / Tb' for the top and bottom terminations."),
    "KOA_RN73H": dict(
        tech="thin film", page=1, fig="dimensions and construction: drawing and table (mm values in italics)",
        labels=("L", "W", "t", "c (top)", "d (bottom)"),
        rows=[("0201", "RN73H1H", (0.6, "+/-0.05"), (0.3, "+/-0.05"), (0.25, "+/-0.05"), (0.15, "+/-0.05"), (0.15, "+/-0.05")),
              ("0402", "RN73H1E", (1.0, "+0.1/-0.05"), (0.5, "+/-0.05"), (0.35, "+/-0.05"), (0.25, "+/-0.1"), (0.25, "+0.05/-0.1")),
              ("0603", "RN73H1J", (1.6, "+/-0.2"), (0.8, "+/-0.1"), (0.45, "+/-0.1"), (0.3, "+/-0.1"), (0.3, "+/-0.1")),
              ("0805", "RN73H2A", (2.0, "+/-0.2"), (1.25, "+/-0.2"), (0.5, "+/-0.1"), (0.4, "+/-0.2"), (0.3, "+0.2/-0.1"))],
        note="The inch value printed for 1H length reads '0.24+/-.002' (a misprint for .024); the mm value 0.6+/-0.05 is used. "
             "RN73R (page 1 dated 10/24/25) lists the same numbers for 1E, 1J and 2A; the older RN73 sheet carries an 'EOL' watermark."),
    "TT_PCF": dict(
        tech="thin film", page=2, fig="Physical Data: dimensions table and drawing",
        labels=("L", "W", "T max", "C (top)", "A (bottom)"),
        rows=[("0201", "PCF0201", (0.58, "+/-0.05"), (0.29, "+/-0.05"), (0.26, "max"), (0.12, "+/-0.05"), (0.15, "+/-0.05")),
              ("0402", "PCF0402", (1.0, "+/-0.1"), (0.5, "+/-0.05"), (0.55, "max"), (0.2, "+/-0.15"), (0.25, "+/-0.15")),
              ("0603", "PCF0603", (1.6, "+/-0.2"), (0.8, "+/-0.2"), (0.65, "max"), (0.3, "+/-0.25"), (0.35, "+/-0.25")),
              ("0805", "PCF0805", (2.0, "+/-0.2"), (1.25, "+/-0.2"), (0.65, "max"), (0.3, "+/-0.25"), (0.4, "+/-0.25"))],
        note="Thickness is given only as a maximum (T max)."),
}

QNAMES = ["body length L", "body width W", "body thickness H", "top termination length",
          "bottom termination length"]
DEFS = ["overall length along the resistor axis, including terminations",
        "body width across the resistor axis",
        "overall height including terminations and coatings",
        "length of the termination metal on the top (film) face, measured from the chip end",
        "length of the termination metal on the bottom (board) face, measured from the chip end"]

for doc, spec in BODY.items():
    for row in spec["rows"]:
        size, part = row[0], row[1]
        for k in range(5):
            val, tol = row[2 + k]
            label = spec["labels"][k]
            add(1, doc, QNAMES[k], val, "mm", tol=tol, page=spec["page"], fig=spec["fig"],
                part=part, size=size, technology=spec["tech"],
                definition=f"{DEFS[k]} (drawing label {label})", notes=spec["note"])

# construction statements (resistive film face, termination coverage, substrate)
CONSTR = [
    ("PANA_ERJ", 2, "Construction drawing", "thick film",
     "Thick film resistive element on the top face of the alumina substrate under the protective coating; "
     "three-layer electrodes (inner, middle, outer) wrap the end face onto top and bottom. "
     "Side faces: the dimension drawing (page 3) shows the termination only in profile; coverage of the side faces is not shown or stated. "
     "Substrate labelled 'Alumina substrate'; purity not stated."),
    ("PANA_ERA", 3, "Construction drawing", "thin film",
     "'High reliability metal film' on the top face of the 'Alumina substrate' under the protective coating; "
     "inner, middle and outer electrodes wrap the end. Side-face coverage not shown or stated. Purity not stated."),
    ("YAGEO_RC", 4, "Fig. 9 and CONSTRUCTION text", "thick film",
     "Resistive layer on the top of the ceramic substrate under a primary glass layer and overcoat; inner electrodes top and bottom; "
     "termination (Ni/matte tin) wraps the end onto top and bottom. Text: 'constructed on top of a high-grade ceramic body'. "
     "Side-face coverage not shown. Purity not stated."),
    ("YAGEO_RT", 4, "Fig. 5 and CONSTRUCTION text", "thin film",
     "Resistive layer on the top face of the ceramic substrate under a protective coat; termination (Ni/matte tin) wraps the end onto top and bottom. "
     "Text: 'constructed out of a high-grade ceramic body'. Side-face coverage not shown. Purity not stated."),
    ("VISHAY_CRCW", 4, "Construction text (column 1)", "thick film",
     "'A cermet film layer and a glass-over are deposited on a high grade (Al2O3) ceramic substrate with its prepared inner contacts.' "
     "The page-11 drawing shows the film on the top face and the terminations wrapping onto top (T2) and bottom (T1). Purity not stated."),
    ("VISHAY_TNPW", 5, "Construction text (column 1)", "thin film",
     "'A homogeneous film of special metal alloy is deposited on a high grade ceramic substrate (Al2O3)'; "
     "'inner contacts are deposited on both sides'. The page-15 drawing shows the film on the top face. Purity not stated."),
    ("KOA_RK73B", 1, "dimensions and construction drawing", "thick film",
     "Resistive film on the top face of the ceramic substrate under the protective coating; inner electrode with Ni and Sn plating wraps the end onto top (c) and bottom (d). "
     "Side-face coverage not shown. Purity not stated ('Ceramic Substrate')."),
    ("KOA_RN73H", 1, "dimensions and construction drawing", "thin film",
     "Resistive film (meander) on the top face of the ceramic substrate under the protective coating; Ni and Sn plating wrap the end onto top (c) and bottom (d). "
     "Side-face coverage not shown. Purity not stated."),
]
for doc, page, fig, tech, text in CONSTR:
    add(1, doc, "construction: resistive-film face, termination coverage, substrate", None, "-",
        page=page, fig=fig, technology=tech, part=DOCS[doc]["document_title"], notes=text)

# ---------------------------------------------------------------------------------------
# Item 2: recommended land patterns (reflow unless stated)
# ---------------------------------------------------------------------------------------
LP_DEFS = {
    "gap": "gap between the inner edges of the two pads (pad-to-pad, under the chip body)",
    "pad_length": "pad length along the resistor axis",
    "pad_width": "pad width across the resistor axis",
    "overall": "overall length from the outer edge of one pad to the outer edge of the other",
}

# Panasonic: a = gap, b = overall, c = width; ranges
PANA_LP = [("0201", "0603 (0201)", (0.3, 0.4), (0.8, 0.9), (0.25, 0.35)),
           ("0402", "1005 (0402)", (0.5, 0.6), (1.4, 1.6), (0.4, 0.6)),
           ("0603", "1608 (0603)", (0.7, 0.9), (2.0, 2.2), (0.8, 1.0)),
           ("0805", "2012 (0805)", (1.0, 1.4), (3.2, 3.8), (0.9, 1.4))]
for size, row, a, b, c in PANA_LP:
    for key, label, rng in (("gap", "a", a), ("overall", "b", b), ("pad_width", "c", c)):
        add(2, "PANA_LAND", f"land pattern {key.replace('_', ' ')}", f"{rng[0]} to {rng[1]}", "mm",
            tol=f"{rng[0]} to {rng[1]}", vmin=rng[0], vmax=rng[1], page=1,
            fig="Example of a land pattern for the rectangular type (drawing and table, row " + row + ")",
            part="ERJ (general purpose), ERA, ERJPC/PB and other rectangular chip resistors",
            size=size, definition=f"{LP_DEFS[key]} (drawing label {label})", notes="Reflow or flow not distinguished.")
    lo = (b[0] - a[1]) / 2
    hi = (b[1] - a[0]) / 2
    add(2, "PANA_LAND", "land pattern pad length", f"{round(lo, 3)} to {round(hi, 3)}", "mm",
        tol=f"{round(lo, 3)} to {round(hi, 3)}", vmin=round(lo, 3), vmax=round(hi, 3), page=1,
        fig="derived from the a and b ranges", part="ERJ, ERA and other rectangular types", size=size,
        definition=LP_DEFS["pad_length"], derived=True,
        notes="Not stated in the document; (b_min - a_max)/2 to (b_max - a_min)/2.")

# Yageo: A overall, B gap, C pad length, D pad width
YAGEO_LP = {"reflow": [("0201", 1.0, 0.3, 0.35, 0.4), ("0402", 1.5, 0.5, 0.5, 0.6),
                       ("0603", 2.6, 0.8, 0.9, 0.8), ("0805", 3.0, 1.2, 0.9, 1.2)],
            "wave": [("0603", 2.70, 0.90, 0.90, 0.80), ("0805", 3.30, 1.30, 1.00, 1.30)]}
for mode, rows in YAGEO_LP.items():
    tab = "Table 1 (reflow)" if mode == "reflow" else "Table 2 (wave)"
    for size, A, B, C, D in rows:
        for key, label, val in (("overall", "A", A), ("gap", "B", B), ("pad_length", "C", C), ("pad_width", "D", D)):
            add(2, "YAGEO_MOUNT", f"land pattern {key.replace('_', ' ')}", val, "mm", page=4,
                fig=f"Fig. 4 Single resistor chips recommended dimensions of footprints; {tab}",
                part="YAGEO single chip resistors (RC, RT ...)", size=size,
                definition=f"{LP_DEFS[key]} (drawing label {label})", conditions=f"{mode} soldering",
                notes="Placement accuracy column: 0402 +/-0.15, 0603 and 0805 +/-0.25, 0201 N/A.")

# Vishay CRCW: G gap, Y pad length, X pad width, Z overall
CRCW_LP = {"reflow": [("0402", 0.45, 0.6, 0.6, 1.65), ("0603", 0.75, 0.75, 1.00, 2.25), ("0805", 1.00, 0.95, 1.45, 2.90),
                      ("1206", 1.50, 1.05, 1.80, 3.60)],
           "wave": [("0603", 0.65, 1.10, 1.25, 2.85), ("0805", 0.90, 1.30, 1.60, 3.50), ("1206", 1.40, 1.40, 1.95, 4.20)]}
for mode, rows in CRCW_LP.items():
    for size, G, Y, X, Z in rows:
        for key, label, val in (("gap", "G", G), ("pad_length", "Y", Y), ("pad_width", "X", X), ("overall", "Z", Z)):
            add(2, "VISHAY_CRCW", f"land pattern {key.replace('_', ' ')}", val, "mm", page=11,
                fig="SOLDER PAD DIMENSIONS drawing; RECOMMENDED SOLDER PAD DIMENSIONS table", part=f"CRCW{size} e3",
                size=size, definition=f"{LP_DEFS[key]} (drawing label {label})", conditions=f"{mode} soldering")

# Vishay 28950 (Draloric/Beyschlag thin-film chips, i.e. TNPW): two reflow tables
V28950 = {"IPC-7351 reflow": [("0201", 0.27, 0.43, 0.42, 1.13), ("0402", 0.40, 0.55, 0.60, 1.50),
                              ("0603", 0.70, 0.90, 1.00, 2.50), ("0805", 1.00, 0.90, 1.45, 2.80),
                              ("1206", 1.75, 1.15, 1.80, 4.05)],
          "IEC 61188-6-2 reflow": [("0201", 0.30, 0.24, 0.32, 0.78), ("0402", 0.55, 0.35, 0.55, 1.25),
                                   ("0603", 0.90, 0.55, 0.90, 2.00), ("0805", 1.10, 0.65, 1.30, 2.40),
                                   ("1206", 2.10, 0.80, 1.65, 3.70)],
          "wave": [("0603", 0.55, 1.10, 1.10, 2.75), ("0805", 0.80, 1.25, 1.50, 3.30), ("1206", 1.40, 1.50, 1.90, 4.40)]}
for mode, rows in V28950.items():
    tab = {"IPC-7351 reflow": "table BASED ON IPC-7351, REFLOW SOLDERING",
           "IEC 61188-6-2 reflow": "table BASED ON IEC 61188-6-2, REFLOW SOLDERING",
           "wave": "table WAVE SOLDERING"}[mode]
    for size, G, Y, X, Z in rows:
        for key, label, val in (("gap", "G", G), ("pad_length", "Y", Y), ("pad_width", "X", X), ("overall", "Z", Z)):
            add(2, "VISHAY_PAD", f"land pattern {key.replace('_', ' ')}", val, "mm", page=1,
                fig=f"Recommended solder pad dimensions drawing; {tab}",
                part="Vishay Draloric/Beyschlag thin film chip resistors (TNPW, MCT/MCS ...)", size=size,
                definition=f"{LP_DEFS[key]} (drawing label {label})", conditions=mode)

# KOA Appendix B: A gap, B overall, C pad width, D pad length
KOA_LP = {"reflow": (1, "Flat Type Components - For Reflow Soldering (drawing); For Reflow Soldering table",
                     [("0201", "1H", 0.25, 0.7, 0.3, 0.225), ("0402", "1E", 0.5, 1.3, 0.3, 0.4),
                      ("0603", "1J", 1.0, 2.0, 0.6, 0.5), ("0805", "2A", 1.3, 2.5, 1.05, 0.6)]),
          "flow": (3, "Flat Type Components - For Flow Soldering (drawing); For Flow Soldering table",
                   [("0402", "1E", 0.5, 1.5, 0.5, 0.5), ("0603", "1J", 1.0, 2.4, 0.8, 0.7),
                    ("0805", "2A", 1.3, 3.1, 1.25, 0.9)])}
for mode, (page, fig, rows) in KOA_LP.items():
    for size, style, A, B, C, D in rows:
        for key, label, val in (("gap", "A", A), ("overall", "B", B), ("pad_width", "C", C), ("pad_length", "D", D)):
            add(2, "KOA_APPB", f"land pattern {key.replace('_', ' ')}", val, "mm", page=page, fig=fig,
                part=f"RK73, RN73 and related flat chips, style {style}", size=size,
                definition=f"{LP_DEFS[key]} (drawing label {label})", conditions=f"{mode} soldering",
                notes="RK73 AT / SG73 AT etc. have a separate row with larger pads.")

# ---------------------------------------------------------------------------------------
# Item 3: alumina relative permittivity and substrate purity
# ---------------------------------------------------------------------------------------
KYO = [("AO476O (A476)", 96, 9.4, 4), ("AO473O (A473)", 92, 9.0, 6), ("AO479O (A479)", 99, 9.9, 2),
       ("AO479S (A479S)", 99.5, 9.9, 1), ("AO479M/AO479G (A479M/A479G)", 99.5, 9.9, 1),
       ("AO479U (A479U)", 99.6, 10, None), ("AO480S (A480S)", 99.7, 9.9, 1)]
for mat, purity, dk, tand in KYO:
    add(3, "KYO_CAT", "relative permittivity of alumina", dk, "-", page=3,
        fig="Characteristic Table of Fine Ceramics, row 'Dielectric Constant (1MHz)', test method JIS C 2141",
        part=f"Kyocera {mat}, Al2O3 content {purity} %", frequency="1 MHz",
        conditions="typical value; JIS C 2141",
        notes=(f"Dielectric loss angle (1 MHz) {tand} x 1e-4." if tand is not None else "Dielectric loss angle (1 MHz) <1 x 1e-4.")
        + " The catalog footnote says the values are typical material properties.")
for mat, dk1, dk2, note in [("A473", 9.1, 8.5, "loss tangent 5e-4 at 1 MHz, 10e-4 at 2 GHz"),
                            ("A476", 9.4, None, "loss tangent 4e-4 at 1 MHz; no 2 GHz value given")]:
    add(3, "KYO_WEB", "relative permittivity of alumina", dk1, "-", page=None,
        fig="Material Properties table, 'Dielectric Constant 1MHz'", part=f"Kyocera {mat} (packaging/substrate alumina)",
        frequency="1 MHz", conditions="representative value", notes=note + "; alumina content not stated on this page.")
    if dk2 is not None:
        add(3, "KYO_WEB", "relative permittivity of alumina", dk2, "-", page=None,
            fig="Material Properties table, 'Dielectric Constant 2GHz'", part=f"Kyocera {mat} (packaging/substrate alumina)",
            frequency="2 GHz", conditions="representative value", notes=note)

for mat, purity, dk, tol, loss in [("Rubalit 708S C (tape cast)", ">= 96.0", 9.8, None, "<= 5e-3"),
                                    ("Rubalit 708 HP C (tape cast)", ">= 96.0", 9.8, None, "<= 5e-3"),
                                    ("Rubalit 708 D (dry pressed)", ">= 95.8", "8.3 to 11.3", (8.3, 11.3), "<= 10e-3"),
                                    ("Rubalit 798", ">= 98.0", 10.2, None, "<= 5e-3"),
                                    ("Rubalit 710F C (tape cast)", "+/- 99.6 (as printed)", "8.5 to 11.5", (8.5, 11.5), "<= 10e-3")]:
    add(3, "CT_2026", "relative permittivity of alumina", dk, "-",
        tol=(f"{tol[0]} to {tol[1]}" if tol else "+/-10 % (sheet footnote: measurement tolerance for all values)"),
        vmin=(tol[0] if tol else None), vmax=(tol[1] if tol else None), page=2,
        fig="Material Properties table, row 'Dielectric constant @ 1 MHz'",
        part=f"CeramTec {mat}, Al2O3 content {purity} wt-%", frequency="1 MHz",
        conditions="standard values from test samples (DIN/DIN-VDE or CeramTec standards)",
        notes=f"Dielectric loss factor @ 1 MHz {loss}.")
for mat, purity, lo, hi in [("Rubalit 708S C", ">= 96.0", 8.3, 11.3), ("Rubalit 708 HP C", ">= 96.0", 8.3, 11.3),
                            ("Rubalit 708 D", ">= 95.8", 8.3, 11.3), ("Rubalit 710F C", "+/- 99.6 (as printed)", 8.5, 11.5)]:
    add(3, "CT_2022", "relative permittivity of alumina", f"{lo} to {hi}", "-", tol=f"{lo} to {hi}", vmin=lo, vmax=hi,
        page=2, fig="Material Properties table, row 'Dielectric constant' (three sub-rows)",
        part=f"CeramTec {mat}, Al2O3 content {purity} wt-%", frequency="1 GHz, 10 MHz and 100 MHz (same range for all three)",
        conditions="2 mm thickness, Ra <= 0.4 um",
        notes="Loss factor <= 10e-3 at the same frequencies (708 D and 708S C).")
for mat, purity, dk1, dk2 in [("AD-995-I2", "nom. 99.5", 9.7, 9.8), ("AD-995-I4", "min. 99.5", 9.8, 9.8),
                              ("AD-996-SI", "min. 99.5", 9.8, 9.8), ("AD-995-LT", "nom. 99.5", 9.8, 9.8)]:
    add(3, "COORS_02084", "relative permittivity of alumina", dk1, "-", page=1,
        fig="Semiconductor Oxides Material Properties chart, row 'Dielectric Constant 1 MHz' (ASTM-D150)",
        part=f"CoorsTek {mat}, {purity} % Al2O3 (structural/semiconductor-equipment grade, not a substrate grade)",
        frequency="1 MHz", conditions="ASTM D150; typical value")
    add(3, "COORS_02084", "relative permittivity of alumina", dk2, "-", page=1,
        fig="Semiconductor Oxides Material Properties chart, row 'Dielectric Constant 4-5 GHz' (TE011 resonant mode)",
        part=f"CoorsTek {mat}, {purity} % Al2O3 (structural/semiconductor-equipment grade, not a substrate grade)",
        frequency="4-5 GHz", conditions="TE011 resonant mode; typical value")
add(3, "COORS_9215", "relative permittivity of alumina", None, "-", page=2,
    fig="SUBSTRATE PROPERTIES BY FAMILY table",
    part="CoorsTek ADS-96R (thick film) and SuperStrate 996 (thin film)",
    notes="not found: the overview table lists flexural strength, CTE, thermal conductivity, dielectric strength and volume resistivity, "
          "but no dielectric constant; the per-product data sheets on GlobalSpec returned HTTP 403 and CoorsTek offers the design guides on request.")
# substrate purity stated by resistor makers
for doc, page, fig, text, val in [
        ("TT_WCR", 1, "Construction", "'The chips have a high alumina substrate (96% minimum) with a ruthenium oxide resistance element'", 96),
        ("TT_PCF", 2, "Construction", "'A thin-film material is selectively deposited on a 96% alumina substrate'", 96),
        ("VISHAY_60107", 1, "EXPERIMENTAL", "'Precision thin film resistors ... were constructed on high performance 99.5 % alumina substrates with case sizes of 0201, 0402, and 0603' (Vishay Thin Film flip-chip and wrap-around parts)", 99.5)]:
    add(3, doc, "resistor substrate alumina purity stated by the resistor maker", val, "% Al2O3",
        tol=("minimum" if doc == "TT_WCR" else None), vmin=(val if doc == "TT_WCR" else None),
        page=page, fig=fig, part=DOCS[doc]["document_title"], notes=text)

# ---------------------------------------------------------------------------------------
# Item 4: FR-4 laminates and solder masks
# ---------------------------------------------------------------------------------------
for f, dk, method, df in [("100 MHz", 4.24, "IPC-TM-650 2.5.5.3", 0.0150), ("1 GHz", 4.17, "IPC-TM-650 2.5.5.9", 0.0161),
                          ("2 GHz", 4.04, "Bereskin stripline", 0.0210), ("5 GHz", 3.92, "Bereskin stripline", 0.0250),
                          ("10 GHz", 3.92, "Bereskin stripline", 0.0250)]:
    add(4, "ISOLA", "relative permittivity of FR-4 laminate", dk, "-", page=2,
        fig="Typical Values Table, row 'Dk, Permittivity'", part="Isola 370HR laminate and prepreg",
        frequency=f, conditions=f"typical value; test method {method}; construction and resin content not stated",
        notes=f"Df at the same frequency {df}.")
add(4, "PANA_R1755V", "relative permittivity of FR-4 laminate", 4.70, "-", page=2,
    fig="Specification / Laminate R-1755V, row 'Dielectric Constant (Dk) @ 1MHz'", part="Panasonic R-1755V laminate",
    frequency="1 MHz", conditions="IPC TM-650 2.5.5.9, C-24/23/50; sample thickness 32 mil (0.8 mm); typical, not guaranteed",
    notes="Df 0.013 at 1 MHz.")
add(4, "PANA_R1755V", "relative permittivity of FR-4 laminate", 4.44, "-", page=2,
    fig="Specification / Laminate R-1755V, row 'Dielectric Constant (Dk) @ 1GHz'", part="Panasonic R-1755V laminate",
    frequency="1 GHz", conditions="IPC TM-650 2.5.5.9, C-24/23/50; sample thickness 32 mil (0.8 mm); typical, not guaranteed",
    notes="Df 0.016 at 1 GHz.")
for cloth, rc, thk, d1, d100, d1g in [("7628", "46%", "0.20 mm, 1 ply", 4.70, 4.57, 4.44),
                                      ("2116", "46%", "0.10 mm, 1 ply", 4.70, 4.57, 4.44),
                                      ("1080", "60%", "0.07 mm, 1 ply", 4.38, 4.24, 4.14),
                                      ("106", "71%", "0.05 mm, 1 ply", 4.20, 4.05, 3.95),
                                      ("1504", "41%", "0.13 mm, 1 ply", 4.85, 4.70, 4.63)]:
    for f, dk in (("100 MHz", d100), ("1 GHz", d1g)):
        add(4, "PANA_R1755V", "relative permittivity of FR-4 laminate", dk, "-", page=3,
            fig="Specification / Laminate R-1755V (No. 19070536 - 2), table '1MHz - 1GHz ; IPC TM650-2.5.5.9'",
            part=f"Panasonic R-1755V laminate, cloth {cloth}, resin content {rc}, {thk}", frequency=f,
            conditions="typical, not guaranteed", notes=f"Same row: {d1} at 1 MHz.")
for f, lo, hi in (("100 MHz", 4.05, 4.70), ("1 GHz", 3.95, 4.63)):
    add(4, "PANA_R1755V", "relative permittivity of FR-4 laminate (range over all listed constructions)", f"{lo} to {hi}", "-",
        tol=f"{lo} to {hi}", vmin=lo, vmax=hi, page=3,
        fig="Specification / Laminate R-1755V (No. 19070536 - 2), whole table", part="Panasonic R-1755V laminate, 106 to 7628 constructions",
        frequency=f, conditions="typical, not guaranteed")
for f, lo, hi in (("100 MHz", 3.78, 4.13), ("1 GHz", 3.65, 4.02)):
    add(4, "PANA_R1755V", "relative permittivity of FR-4 prepreg (range over all listed constructions)", f"{lo} to {hi}", "-",
        tol=f"{lo} to {hi}", vmin=lo, vmax=hi, page=5,
        fig="Specification / Prepreg R-1650V (No. 19070536 - 4), table '1MHz - 1GHz ; IPC TM650-2.5.5.9'",
        part="Panasonic R-1650V prepreg, 106/1067/1078/1080, resin content 65-80 %", frequency=f, conditions="typical, not guaranteed")
add(4, "VENTEC_DS", "relative permittivity of FR-4 laminate", 4.27, "-", tol="specification 5.2 maximum", vmax=5.2, page=2,
    fig="Properties Sheet, row 'DK @ 1GHz RC 50%'", part="Ventec VT-47, resin content 50 %", frequency="1 GHz",
    conditions="IPC-TM-650 2.5.5.9; typical value 4.27, specification 5.2 maximum", notes="DF @ 1 GHz: typical 0.016, specification 0.035 maximum.")
for desc, dk in [("core 0.059 in, 8-7628, resin content 44 %", 4.28), ("core 0.008 in, 1-7628, resin content 46 %", 4.22),
                 ("core 0.014 in, 2-7628, resin content 41 %", 4.35), ("core 0.004 in, 1-2116, resin content 45 %", 4.20),
                 ("core 0.002 in, 1-1067, resin content 65 %", 3.75)]:
    add(4, "VENTEC_PG", "relative permittivity of FR-4 laminate", dk, "-", page=3,
        fig="Laminates Availability table ('DK values are for impedance design'), column DK @ 1GHz", part=f"Ventec VT-47 {desc}",
        frequency="1 GHz", conditions="values for impedance design")
add(4, "VENTEC_PG", "relative permittivity of FR-4 laminate (range over all listed cores)", "3.75 to 4.35", "-", tol="3.75 to 4.35",
    vmin=3.75, vmax=4.35, page=3, fig="Laminates Availability table, column DK @ 1GHz", part="Ventec VT-47 cores 0.002-0.059 in",
    frequency="1 GHz", conditions="values for impedance design; no 100 MHz column")
add(4, "VENTEC_PG", "relative permittivity of FR-4 prepreg (range over all listed styles)", "3.45 to 4.25", "-", tol="3.45 to 4.25",
    vmin=3.45, vmax=4.25, page=2, fig="Prepreg Availability table, column DK @ 1GHz", part="Ventec VT-47 prepregs 106 to 7628",
    frequency="1 GHz", conditions="values for impedance design")
# solder masks
for doc, part, ini, cond, df in [("TAIYO_G24K", "Taiyo PSR-4000 G24K/CA-40 G24 (green, screen-print LPI)", 4.1, 4.8, "0.024 initial, 0.041 after humidification"),
                                 ("TAIYO_EG23", "Taiyo PSR-4000 EG23/CA-40 G23K (black, screen-print LPI)", 4.5, 4.9, "0.025 initial, 0.042 after humidification"),
                                 ("TAIYO_D10ME", "Taiyo PSR-4000 D10ME/CA-40 D10 (black matte LPI)", 3.5, 3.7, "0.02 initial, 0.03 conditioned")]:
    for state, dk in (("initial", ini), ("after humidification (25-65 C cycle, 90 % RH, 7 days)", cond)):
        add(4, doc, "relative permittivity of liquid photoimageable solder mask", dk, "-", page=4,
            fig="Coating (end) properties table, row 'dielectric constant' (1 MHz, in-house method)", part=part,
            frequency="1 MHz", conditions=f"Taiyo in-house method; {state}; measured at room temperature",
            notes=f"Dissipation factor {df}.")
add(4, "PETERS", "relative permittivity of liquid photoimageable solder mask", 3.7, "-", tol="approx.", page=5,
    fig="Electrical properties table, row 'Dielectric constant er'", part="Peters Elpemer 2467 series",
    frequency="1 MHz", conditions="based on IPC-4101A", notes="Dissipation factor approx. 0.029 (1-100 MHz).")
for cond, dk in (("21.1 C and 15 % RH", 3.22), ("29.4 C and 55 % RH", 3.29), ("37.8 C and 95 % RH", 3.48)):
    add(4, "IPC_S12_2", "relative permittivity of liquid photoimageable solder mask", dk, "-", tol="+/-0.02 (graph reading)",
        page=7, fig="Figure 10 - Relative Permittivity of LPI C in Varying Environmental Conditions (3.2 GHz resonator points)",
        part="'LPI C', a two-part Taiyo America LPI solder mask not identified by name", frequency="3.2 GHz",
        conditions=f"split-post dielectric resonator; {cond}",
        notes="Read by eye from the plotted points; the 1.25 GHz points of the same figure lie at about 2.84-2.96 (dry) and 3.22 (37.8 C, 95 % RH).")

# ---------------------------------------------------------------------------------------
# Item 5: epoxy mould compound
# ---------------------------------------------------------------------------------------
for part, df in (("Panasonic CV8710U", 0.010), ("Panasonic CV8710MYC (low alpha)", 0.016)):
    add(5, "PANA_CV8710", "relative permittivity of epoxy mould compound", 4.0, "-", page=2,
        fig="Specification table, row 'Dielectric Constant (1MHz)', JIS K6911", part=part, frequency="1 MHz",
        conditions="JIS K6911; typical, not guaranteed",
        notes=f"Dissipation factor {df}; fused-silica filler 88-88.5 wt%; series intended for laminate-substrate packages (PoP, MCP, mould underfill, FBGA), not leadframe QFN.")
add(5, "HITACHI_CEL", "relative permittivity of epoxy mould compound", 3.1, "-", page=1,
    fig="Table 3. Physical property, row 'Dielectric constant at 1MHz'", part="Hitachi Chemical CEL-9220HF10", frequency="1 MHz",
    conditions="based on Hitachi Chemical experiments; not guaranteed",
    notes="Dissipation factor 1.1 % at 1 MHz; spherical filler 90 wt%; package type not stated; copy attached to a TI E2E forum post.")
add(5, "TI_E2E", "relative permittivity of the mould compound of a TI leadless package", None, "-", page=None,
    fig="forum reply", part="PCA9306-Q1 mould compounds 'SID#450207' and 'SID#R-32'",
    notes="not found: the TI reply says this 'isn't information that I can share on a public forum' and refers the asker to TI customer support.")

# ---------------------------------------------------------------------------------------
# Item 6: leadframe thickness of a 0.5 mm pitch WSON/SON
# ---------------------------------------------------------------------------------------
add(6, "TI_OPA855", "leadframe (terminal) thickness, WSON DSG0008A", None, "mm", page=38,
    fig="PACKAGE OUTLINE DSG0008A, WSON - 0.8 mm max height (4218900/E 08/2022)", part="TI DSG0008A, 8-pin WSON, 2 mm x 2 mm, 0.5 mm pitch",
    notes="not stated in the outline drawing.")
for q, val, tol, vmin, vmax, note in [
        ("side wall metal thickness DIM A, option 1", 0.1, None, None, None, "Table 'SIDE WALL METAL THICKNESS DIM A' on the outline; meaning as drawn, not a leadframe thickness."),
        ("side wall metal thickness DIM A, option 2", 0.2, None, None, None, "Same table, option 2."),
        ("package height", "0.7 to 0.8", "0.7 to 0.8", 0.7, 0.8, None),
        ("standoff (seating height)", "0.00 to 0.05", "0.00 to 0.05", 0.0, 0.05, None),
        ("terminal width", "0.18 to 0.32", "0.18 to 0.32", 0.18, 0.32, "8X"),
        ("terminal length", "0.2 to 0.4", "0.2 to 0.4", 0.2, 0.4, "8X"),
        ("terminal pitch", 0.5, None, None, None, "6X basic dimension")]:
    add(6, "TI_OPA855", q + ", WSON DSG0008A", val, "mm", tol=tol, vmin=vmin, vmax=vmax, page=38,
        fig="PACKAGE OUTLINE DSG0008A (4218900/E 08/2022)", part="TI DSG0008A, 8-pin WSON, 0.5 mm pitch", notes=note)
add(6, "TI_SCBA017", "leadframe thickness (QFN, TI package RGY)", 0.20, "mm", tol="nominal", page=6,
    fig="Figure 2. 14-Pin QFN Package Dimensions, side view callout '0.20 NOMINAL LEAD FRAME'",
    part="TI RGY 14-pin QFN (3.5 mm x 3.5 mm, 0.5 mm pitch); not the DSG package",
    notes="Supplementary; a different, older leadless package from the same vendor.")
add(6, "TI_SLUA271", "leadframe material of TI QFN/SON packages", "copper", "-", page=3,
    fig="Section 1.1 Introduction", part="TI QFN and SON packages",
    notes="'thermally enhanced plastic packages that use conventional copper leadframe technology'; no thickness given.")


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    with open(sys.argv[1], "w", encoding="utf-8") as fh:
        json.dump(RECORDS, fh, indent=1, ensure_ascii=False)
    print(f"wrote {len(RECORDS)} records to {sys.argv[1]}")


if __name__ == "__main__":
    main()
