# Scripts for the TIA op-amp survey

This folder holds every script used to produce the survey `../TIA_opamp_survey.md`: the analytical model, the analysis runs, the checks, the figures and tables, the datasheet-curve extraction tools and the market-scan helpers.

**Requirements.** Python 3.13 with NumPy, SciPy and Matplotlib. PyMuPDF is needed only for the PDF tools, schemdraw only for the schematics, and ngspice only for the SPICE cross-check (below).

**Conventions.**
- All paths are passed as arguments or are relative to this folder.
- No script needs credentials.
- `market_scan/ti_product_pages.py` fetches public TI product pages and sends no personal data.
- **Numbering.** The section, table, figure and equation numbers quoted in this index and in the scripts' docstrings are those of the report before it was put into its narrative order on 27 October 2026, the numbering the scripts were written for. `rework/TIA_opamp_survey.map.txt` converts every old number to the present one: old Section 10 is now Chapter 5, old Section 11.4 is Section 6.7, old Sections 11.5–11.7 are Sections 7.1–7.3, old Table 11.1 is Table A6.33, old Figures 7–16 are Figures 3–9 and 17–19, and old Eqs. (56)–(75) are Eqs. (49)–(68). The rows for `benchmark_50ohm.py`, `make_narrative_figures.py` and `rework/` use the present numbering. The logic round of 1 November 2026 kept every equation, table and figure number but merged the conclusions: Sections 9.1–9.13 of the 27 October numbering are now Section 9.1 (old 9.1), 9.2 (old 9.6, 9.7 and 9.10, and the choice of amplifier in 9.8–9.9), 9.3 (the front end of 9.8–9.9), 9.4 (old 9.3–9.5), 9.5 (old 9.2 and 9.11), 9.6 (old 9.12) and 9.7 (old 9.13). It also added Section 6.3.5, the 2-pF option. On 4 November 2026 the theory moved before the design example, and Chapter 4 became two design examples with six new figures (below, "The two design examples of Chapter 4"). `rework/case_studies_reorder.map.txt` converts the numbers of 3 November to the present ones: Sections 3.1–3.4 → 4.1, 4.2, 4.8 and 4.9, Sections 4.k → 3.k, Eqs. (7)–(10) → (33)–(36), Eqs. (11)–(36) → (7)–(32), Table 3.1 → 4.1, Tables A4.k → A3.k and Figures 3–31 → 9–37. The 27 October map followed by this one gives the present number of any number of the original report.
- **Files outside the public repository.** Some scripts read the manufacturers' datasheets, application notes and SPICE models from `../datasheets/`, `../appnotes/` and `../spice/models/`, and the SPICE checks write their decks and logs to `../spice/runs/`. These are not part of the public repository: Appendix D of the note gives each document's source, `../spice/models/README.md` the download page and terms of every model (only the four ADI model files are included), and the checks regenerate `../spice/runs/`.

## Order of use

Run from this folder:

```
python run_analysis.py ../data/results                    # results.json (all parts, both R_F)
python make_tables.py ../data/results ../data/results/tables.md
python make_figures.py ../data/results ../figures          # Figures 2-6
python make_schematics.py ../figures                        # Figure 1 and Figures 27-32 and 34-38 (schematics)
python cf_window.py ../data/results/cf_window.json
python added_cap_tradeoff.py ../data/results/added_cap_tradeoff.json
python cf_sensitivity.py ../data/results/cf_sensitivity.json
python starting_values.py ../data/results/starting_values.md
python report_numbers.py ../data/results ../data/results/report_numbers.md
python peaking_tolerance.py ../data/results/peaking_tolerance.json
python peaking_tolerance.py bench                          # prints Table 4.11
python balanced_detector.py ../data/results/balanced_detector.json
python check_datasheet_examples.py                         # prints Table 4.1 comparisons
```

`run_analysis.py` takes about a minute; the others take seconds to a minute.

## Model and analysis

| Script | Purpose | Inputs | Outputs |
|---|---|---|---|
| `tia_model.py` | Analytical TIA model, with these parts: (1) open-loop models: interpolated datasheet curve, pole-delay fit, calibrated variant; (2) $Z_T$, noise gain and loop gain; (3) loop metrics: crossover, phase and gain margin, second crossing, −3 dB, peaking; (4) feedback-capacitor design; (5) noise components, with the central, low and high FET current-noise treatments | – (library) | – |
| `parts_db.py` | Curated datasheet inputs for every part, with page citations. It loads the digitized open-loop and noise curves from `../data/specs/<PART>.json` and normalises phase conventions | `../data/specs/*.json` | – (library) |
| `run_analysis.py` | Runs the whole analysis for every part at both $R_F$: (1) flat, 1-dB, largest-phase-margin and robust designs; (2) calibrated and fitted checks; (3) parasitic corners; (4) spot and band noise with and without DC photocurrent; (5) DC limits and dynamic range | `parts_db` | `results.json` |
| `cf_window.py` | Window of total $C_F$ with phase margin ≥ 45°, gain margin ≥ 3 dB and peaking ≤ 1 dB, for the leading parts at three PCB capacitances | `parts_db` | `cf_window.json` |
| `added_cap_tradeoff.py` | Phase margin, bandwidth and noise against deliberately added input capacitance (OPA818, OPA846, OPA955, OPA855) | `parts_db` | `added_cap_tradeoff.json` |
| `cf_sensitivity.py` | Response of candidate designs to the total $C_F$ and to $C_{\mathrm{PCB}}$ | `parts_db` | `cf_sensitivity.json` |
| `starting_values.py` | Recommended starting values and their tolerance to the feedback capacitance (Table 8.1) | `parts_db` | `starting_values.md` |
| `peaking_tolerance.py` | Designs that accept transimpedance peaking but must not oscillate: worst-case phase and gain margin over $C_F$ ±0.1 pF, $C_T$ ±0.2 pF and open-loop gain from GBW MIN to +1.5 dB, plus the spread of the peak an equalizer must follow. The `bench` argument evaluates the 1.2-kΩ OPA846 bench board with $C_T$ = 12–16 pF | `parts_db` | `peaking_tolerance.json`; printed table |
| `report_numbers.py` | Secondary report tables: (1) noise components; (2) band-integrated rms; (3) all noise referred to the photocurrent: totals at 100 MHz for $I_1 + I_2$ = 0–20 mA, output noise divided by $R_F$ and the unfiltered rms divided by $R_F$, and the instrument noise, referred to the photocurrent, that degrades OPA855's floor by ≤ 0.5 dB (Tables 0.4, 5.6, 5.7); (4) largest RF photocurrent | `results.json` | `report_numbers.md` |
| `balanced_detector.py` | Balanced photodiode pair and front-end options (Sections 1.5 and 7.8–7.11): (1) the 2-pF option for the ten leading parts at both $R_F$; (2) shot noise of the pair; (3) self-biased cascode pair; (4) cascode pair in the dark with a standing current; (5) $C_F$ window with cascodes; (6) bootstrapping and its break-even capacitance; (7) resistive imbalance servo and its loop; (8) current-splitting servo: path delay, base-resistance noise, residual intensity noise; (9) bias-network noise with capacitor and ferrite parasitics; (10) largest RF amplitude against tone frequency; (11) the proposed front end; (12) the two front-end variants, OPA855 and OPA818: nominal and worst-case loop over the corners of `peaking_tolerance.py`, noise with the servo resistor, dynamic range for a 100-MHz tone. The optional second argument `variants` recomputes only item 12 and merges it into the existing JSON. Transistor and capacitor parasitics are assumed values stated in the script | `parts_db`, `cf_window`, `peaking_tolerance` | `balanced_detector.json`; printed tables |

## Checks

| Script | What it checks |
|---|---|
| `check_model_single_pole.py` | The model against the closed-form single-pole Butterworth results of Section 2.3 |
| `check_theory_numbers.py` | Every number quoted in Section 2 (constants, reference levels, worked examples) |
| `check_pm_resistive_gain.py` | Phase margin of the interpolated open-loop curves at a resistive noise gain, against the datasheet statements |
| `check_datasheet_examples.py` | The model against every closed-loop and TIA response printed in the datasheets, including TI's TIA-calculator curves (Table 4.1) |
| `opa846_1k2_check.py` | A bench OPA846 TIA ($R_F$ = 1.2 kΩ, 1.45 kΩ measured at 50 MHz, about 7 pA/√Hz measured at 50 MHz) against the model: finds the input and feedback capacitance that reproduce the measured transimpedance, and the noise the model predicts there |
| `check_math_extract.py` | Extracts every math span of the report and parses it with latex2mathml. It also flags non-dollar delimiters and pipes inside table math. It works on any Markdown file and needs the Python package `latex2mathml` (run with version 3.81.1). Usage: `python check_math_extract.py <report.md> <spans.json>` |
| `check_previewer_rules.py` | Checks every inline math span against the stricter rules of Markdown previewers, which the two parsers do not test: no space just inside a dollar sign, no digit after the closing one, no letter or digit before the opening one, no `\|` in a table row's math. It works on any Markdown file. Usage: `python check_previewer_rules.py <note.md> [...]` |
| `check_xref_links.py` | Lists how `build/build_pdf.py` will treat each cross-reference of a note without building it: which it links to the note's own targets, which it leaves unresolved, and which it leaves as text because they name another document ("the high-gain note's Table 3"). It applies the build's own patterns. Usage: `python check_xref_links.py <note.md> [--all]` |
| `katex_check.js` | Renders the spans from `check_math_extract.py` with KaTeX, which is the second parser. It reports parse errors only, because KaTeX's strict-mode warnings are switched off. The KaTeX file is `dist/katex.min.js` of the npm package `katex`; it is not kept here, and it has been run with versions 0.16.11 and 0.16.22. Usage: `node katex_check.js <katex.min.js> <spans.json>` |
| `check_report_refs.py` | Cross-reference consistency of the report: equation tags in order, every "Eq. (n)" within range, every cited table, section and figure present, no duplicate table captions, every table caption naming its amplifiers. Usage: `python check_report_refs.py <report.md>` |

## Figures and tables

| Script | Output |
|---|---|
| `make_schematics.py` | The schematics: `fig01_tia_circuit` (Figure 1) and `fig21`–`fig31` (Figures 27–32 and 34–38: the two composites of Chapter 7, Options A–D, bootstrapping, cascoding, the optical-split and current-splitter servos, and the proposed front end of Chapter 8). Each function's docstring names the section and table its part values come from; `fig32_case_opa855` and `fig34_case_opa846` are Figures 3 and 5 of Chapter 4. Usage: `python make_schematics.py [OUT_DIR] [NAME ...]` |
| `schematic_style.py` | The drawing style of every schematic, the same as in the high-gain note: one scale (0.30 in per drawing unit) and one canvas width (6.5 in), so that all schematics print at the same scale; white background, 1-pt lines, Arial labels at 8 pt with Computer Modern mathematics; parasitic elements grey, light red, guards green, optional parts dashed. Imported by `make_schematics.py`. |
| `make_circuit_figure.py` | The earlier drawing of `fig01_tia_circuit` in plain Matplotlib, replaced on 3 November 2026 by `make_schematics.py` and kept for the record; running it would overwrite the present Figure 1. |
| `make_figures.py` | `fig02_input_noise_2k`, `fig03_transimpedance_2k`, `fig04_landscape_en_gbw`, `fig05_bandwidth_vs_noise_penalty_2k`, `fig06_dynamic_range_vs_idc_2k` (PNG at 600 dpi and PDF) |
| `make_tables.py` | `tables.md`: specification, stability, calibrated variants, noise, output noise, shot clearance, dynamic range and corner tables |
| `make_narrative_figures.py` | The comparison charts of Chapter 6, from `../data/results/results.json` and `../data/results/benchmark_50ohm.json`, in the style of the plotting guide (Arial 8 pt, 600-dpi PNG and PDF): `fig17_bandwidth_phase_margin_all_parts` (Figure 10: robust bandwidth and flat-design phase margin of all 26 configurations at both $R_F$), `fig18_noise_penalty_all_parts` (Figure 13: band penalty over 10–150 MHz of the 21 configurations with a stable flat design, with the 50-Ω benchmark), `fig19_dynamic_range_all_parts` (Figure 15: electronic dynamic range of the ten amplifiers of Table A6.29 in the dark and at 0.1, 1 and 10 mA, with the benchmark at −10 dBm), `fig20_benchmark_50ohm` (Figure 20: small-signal advantage and usable dynamic range of the leading designs against the benchmark family). Runs no simulation; seconds. Usage: `python make_narrative_figures.py [--fig-dir <dir>]` |

## The 50-Ω benchmark

| Script | Purpose |
|---|---|
| `benchmark_50ohm.py` | The benchmark of Sections 2.1 and 6.8: the photodiode pair terminated in 50 Ω in parallel with the input of an amplifier of noise figure NF (2 dB) that compresses at $P_{\max}$ (−20, −10, 0 dBm). Eqs. (1)–(6) and (32): noise $4Fk_BT/R_0$, ceiling $2\sqrt{P_{\max}/R_0}$, electronic and usable dynamic range, $P_{\mathrm{eq}}$, $P_x$ and the photocurrent above which the benchmark overtakes each design. Reads the SPICE results of the leading op-amp designs (`../spice/results/dr_comparison.json`) and of the two composites (`composite_fet_verify.json`, `composite_hv_verify.json`, `composite_hv_tone.json`, `../data/results/composite_analytical.json`); writes `../data/results/benchmark_50ohm.json`. `--tables` prints the rows of Tables A2.2, A6.35 and A6.36 from that file. Runs no simulation; seconds. Usage: `python benchmark_50ohm.py [--tables]` |

## SPICE cross-check (Section 10)

**Requirements.** ngspice built as a shared library with its XSPICE code models, plus NumPy. KiCad 10.0 installs ngspice-46 as `bin/ngspice.dll`, with the code models in `lib/ngspice/*.cm`, and `ngspice_shared.py` finds them there. Otherwise set `NGSPICE_LIBRARY` to the library and `NGSPICE_CODEMODELS` to the folder of the `.cm` files.

**Vendor models.** They are not part of this archive and must not be redistributed. Download them from the TI product pages and place each library file under `../spice/models/<PART>/`:

| Part | Package | File to place |
|---|---|---|
| OPA855 | SBOMB43D, https://www.ti.com/lit/zip/sbomb43 | `OPA855/opa855_a.lib` |
| OPA818 | SBOMB74B, https://www.ti.com/lit/zip/sbomb74 | `OPA818/opa818.lib` |
| OPA856 | SBOMBI1, https://www.ti.com/lit/zip/sbombi1 | `OPA856/opa856_a.lib` |
| OPA858 | SBOMBK7, https://www.ti.com/lit/zip/sbombk7 | `OPA858/OPA858.lib` |
| LMH6629 | SNOM133, https://www.ti.com/lit/zip/snom133 | `LMH6629/LMH6629.MOD` |
| OPA859 | SBOMBQ2, https://www.ti.com/lit/zip/sbombq2 | `OPA859/OPA859.lib`, copied out of the package's `OPA859-PSpiceFiles/SCHEMATIC1/TransientAnalysis/` folder |
| OPA846 | SBOC005C, https://www.ti.com/lit/zip/sboc005 | `OPA846/OPA846.LIB` |
| OPA657 | SBOM137 (Rev. F), https://www.ti.com/lit/zip/sbom137 | `OPA657/OPA657.lib` |
| OPA847 | SBOC037 (Rev. A), https://www.ti.com/lit/zip/sboc037 | `OPA847/OPA847_Model.sub` |
| LMH6624 | SNOM130, https://www.ti.com/lit/zip/snom130 | `LMH6624/LMH6624.MOD`, from the zip inside the package |
| THS4021 | SLOJ004 (Rev. A), https://www.ti.com/lit/zip/sloj004 | `THS4021/ths4021.lib` |
| THS3491 (Section 11.6) | SBOMBP9, https://www.ti.com/lit/zip/sbombp9 | `THS3491/extracted/sbombp9/ths3491.lib`, the package unzipped into `THS3491/extracted/sbombp9/` |

The bipolar transistor of the composites comes from Infineon: BFP740ESD, https://www.infineon.com/assets/row/public/documents/24/70/bfp740esd-spice-v2.mdl, saved as `BFP740ESD/bfp740esd-spice-v2.mdl` (Section 11.5). The LSBF862, CPH3910 and CE3512K2 cards are written by `spice_composite_checks.py` itself (`FET_CARDS`).

Three TI parts come only as TINA-TI files. Their netlists are plain text inside; `extract_tina_model.py` copies them out unchanged (usage below):

| Part | Package | File to place |
|---|---|---|
| OPA955 | SLOM544, https://www.ti.com/lit/zip/slom544 | `OPA955/OPA955_from_TINA.lib`, extracted from `OPA955.TSM` in the package |
| OPA817 | SBOMCB7, https://www.ti.com/lit/tsc/sbomcb7 | `OPA817/OPA817_from_TINA.lib`, extracted from the `.tsc` file |
| OPA814 | SBOMCE1, https://www.ti.com/lit/zip/sbomce1 | `OPA814/OPA814_from_TINA.lib`, extracted from `OPA814_v1p1.TSM` in the package |

The ADI models are behind a license agreement on analog.com. It allows unmodified copies to accompany distributed software; modified copies may not be redistributed. Accept it on each product page's "SPICE Macro Model" link and save the file:

| Part | Link | File to place |
|---|---|---|
| ADA4817-1 | https://www.analog.com/media/en/simulation-models/spice-models/ada4817.cir | `ADA4817-1/ada4817.cir` |
| AD8099 | https://www.analog.com/media/en/simulation-models/spice-models/ad8099.cir | `AD8099/ad8099.cir` |
| ADA4899-1 | https://www.analog.com/media/en/simulation-models/spice-models/ada4899.cir | `ADA4899-1/ada4899.cir` |
| ADA4895-1 | https://www.analog.com/media/en/simulation-models/spice-models/ADA4895.cir | `ADA4895-1/ADA4895.cir` |

`python inspect_model_zip.py <package.zip> <empty folder>` extracts a package without path traversal. It lists each `.SUBCKT` line, and flags encryption markers and any control or shell command, before a model is used.

**Order of use**, from this folder:

```
python spice_tia_checks.py all        # about 10 minutes; or one check at a time
python spice_tia_checks.py all --parts OPA657 OPA847   # only these parts, merged into the results
python spice_report_tables.py         # writes ../spice/results/tables.md
python dr_comparison.py               # Section 11: dynamic range, ../spice/results/dr_comparison.json
python make_spice_figures.py          # Figures 7-16 into ../figures; no simulation
```

| Script | Purpose |
|---|---|
| `ngspice_shared.py` | The driver. It loads ngspice as a shared library through ctypes, from an argument, `NGSPICE_LIBRARY`, the system search, or KiCad's and ngspice's default install folders. It loads the XSPICE code models, sets PSpice compatibility, and runs a deck from inside its own folder (`run_deck`). Usage as a script prints the ngspice version |
| `spice_tia_checks.py` | Every SPICE check of Section 10: `smoke`, `aol`, `params`, `referee`, `loop`, `zt`, `noise`, `step`, `tone`, `bench`, `cfscan` (total-$C_F$ scans of variants A and B, about 860 short runs), `pscan` (every part's widest-band robust design at 1 pF and 2 kΩ: total $C_F$ from 0.10 to 2.40 pF in 0.05-pF steps at the three photodiode capacitances, about 140 short runs per part), `consistency`, or `all`. `--parts <PART> ...` runs the per-part checks for those parts only and merges their results into the existing files (`tone`, `bench` and `cfscan` are then skipped). The model translation also turns PSpice's capacitor model type `CAP` into ngspice's `C` (THS4021). It writes a translated copy of each vendor model (PSpice `T_ABS` noiseless resistors become `noisy=0`, Section 10.2) and one deck per case under `../spice/runs/<check>/<case>/`, with ngspice's log beside it. It writes one JSON file per check to `../spice/results/`. Usage: `python spice_tia_checks.py <check> [--ngspice <library>] [--spice <folder>]` |
| `spice_report_tables.py` | Turns the JSON results into the Markdown tables of Section 10 (`../spice/results/tables.md`) |
| `make_spice_figures.py` | Figures 7–14 of Section 10 and Figures 15–16 of Section 11 from the saved results and arrays, in the style of `make_figures.py`: `fig07_spice_loop_gain_hidden_margin`, `fig08_spice_open_loop_gain`, `fig09_spice_cf_scan_variant_A`, `fig10_spice_cf_scan_variant_B`, `fig11_spice_noise`, `fig12_spice_noise_vs_margin_bandwidth`, `fig13_spice_bench_board`, `fig14_spice_best_design_all_parts`, `fig15_dynamic_range_comparison`, `fig16_dynamic_range_limits_opa818` (PNG at 600 dpi and PDF). It runs no simulation and prints the numbers quoted in the captions. Usage: `python make_spice_figures.py [--spice <folder>] [--out <folder>] [--only 7 9 ...]` |
| `dr_comparison.py` | Section 11: dynamic range in 150 MHz (Eqs. (56)–(57)) of the five leading amplifiers at their best SPICE designs (check `pscan`), from the saved noise spectra and transimpedance, against the survey's model at the same $C_F$, over $I_1 + I_2$ = 1 µA–20 mA and tones of 20–200 MHz; the floors and ceilings of the OPA818 design for Figure 16; and the single-chip TIAs of `../data/integrated_tias.json`. A variable-gain coherent-receiver TIA is evaluated at the one gain at which its noise is published (Eq. (60)); a per-input DC limit (`i_dc_max_A`) ends its curve, other settings (`alt_settings`) are evaluated but not plotted, and the class bound of Eq. (61) (3 mAppd with shot noise only, and the in-band noise allowed to match each op-amp design at 1 mA) is stored as `coherent_bound`. The band integral runs over exactly 0–150 MHz. Saved data only, no simulation. Usage: `python dr_comparison.py [--spice <folder>] [--tias <json>] [--out <json>]` |
| `fet_composite_bound.py` | Section 11.5: what a discrete-FET composite front end could buy at 1 pF and 2 kΩ, from Eqs. (62)–(65). It prints (0) the op amps' noise at 100 MHz split into $R_F$, current noise and $e_n$ on the capacitance (survey model at the SPICE designs' $C_F$); (1) the largest gain of a noiseless amplifier over the SPICE designs (Table 11.3); (2) the transit frequency a FET needs to match OPA855 and OPA955; (3) every device of `fet_front_end/` at its datasheet operating point (Table 11.4). It reads `../spice/results/dr_comparison.json`; no simulation. Usage: `python fet_composite_bound.py [--spice <folder>]` |
| `reintegrate_penalties.py` | Recomputes the band penalties stored in `../spice/results/noise.json`, `cfscan.json` and `pscan.json` over exactly 10–150 MHz from the saved spectra, with `band_penalty()` of `spice_tia_checks.py`. The noise sweeps have 50 points per decade, so their last point below 150 MHz is 144.5 MHz; the earlier integral stopped there, and its penalties were 0.03–0.30 dB low. Run once on 26 Oct 2026; a fresh `spice_tia_checks.py` run gives the same values. No simulation. Usage: `python reintegrate_penalties.py [--spice <folder>]` |
| `inspect_model_zip.py` | Safe extraction and inspection of a model package (above) |
| `extract_tina_model.py` | Copies a TI macromodel's netlist out of a TINA-TI `.TSM` macro or `.TSC` schematic, unchanged: TINA-TI stores it as plain text, one line per record (a zero byte, a 4-byte big-endian length, the line and a NUL). It follows the record chain from the `.subckt` line back to the header comments and forward to the last `.ends`; it decrypts or reconstructs nothing. Checked on OPA818, whose TINA-TI file (SBOMB21A) yields all 259 netlist lines of its PSpice library. Usage: `python extract_tina_model.py <file.TSM or .TSC> <subckt name> <output .lib>` |
| `ngspice_shared_probe.py` | Minimal check that ngspice loads as a shared library; prints its version, no simulation. Usage: `python ngspice_shared_probe.py <path to the ngspice library>` |

### `spice_diagnostics/`: the diagnostic runs behind Sections 10.2, 10.4, 10.7 and 10.10

Each simulating script takes the path of this folder as its first argument and copies the translated models into its own work folder; `band_edge_check.py` only reads saved spectra. None writes into `../spice/`.

| Script | What it showed |
|---|---|
| `t_abs_probe.py` | PSpice's `T_ABS` in ngspice-46: a resistor with `T_ABS` = $x$ has the Johnson noise of (27 + $x$) °C whatever `.temp` is, so TI's "noiseless" resistors (`T_ABS` = −273.15) are at 27 K (Table 10.2). Usage: `python t_abs_probe.py <scripts_archive> <work folder>` |
| `admittance_rounding_pitfall.py` | With 1-kF and 1-GH fixture elements the input current is quantised to multiples of 2⁻¹¹ A, and the input capacitance comes out wrong by up to about 20 %. Usage: `python admittance_rounding_pitfall.py <scripts_archive> <spice folder> <part> <work folder>` |
| `compare_loop_gain.py` | The SPICE loop gain against $A/NG$ from the macromodel's own curve: they agree to 2 GHz and part above it. Usage: `python compare_loop_gain.py <scripts_archive> <spice folder> <part> <R_F> <C_D> <C_F>` |
| `aol_inverting_input.py` | The gain from the inverting input differs from that from the non-inverting input above 1 GHz. With it, the measured admittance and the output impedance, Eq. (52) reproduces every SPICE loop to 0.1°. Usage: `python aol_inverting_input.py <scripts_archive> <spice folder> <work folder> <part> ...` |
| `tone_probe.py` | One tone run, timed: 0.3 s per run, numerical floor below −138 dBc, no change with `reltol` = 10⁻⁵. Usage: `python tone_probe.py <scripts_archive> <spice folder> <work folder> <part> <f0> <peak current> [<options>]` |
| `adi_open_loop_probe.py` | Section 10.10: the AD8099 and ADA4899 macromodels stop every `ac` sweep with "matrix is singular" while `noise` sweeps of the same circuit run; rewriting PSpice's `limit()` and using KLU do not help, `.options rshunt=1e12` does. Usage, from a work folder: `python adi_open_loop_probe.py <scripts_archive>` |
| `band_edge_check.py` | Section 10.7: how much of the 10–150 MHz band the 50-points-per-decade noise sweeps miss. Their last point below 150 MHz is 144.5 MHz, so a grid-point integral covers 10–144.5 MHz and puts every band penalty 0.03–0.30 dB low (most for the FET parts, whose noise rises fastest). Reads the saved spectra, writes nothing. Usage: `python band_edge_check.py [--spice <spice folder>]` |

## Composite TIAs and the datasheet-figure checks (Sections 11.5–11.7)

| Script | Purpose |
|---|---|
| `composite_tia.py` | Analytical loop gain, transimpedance, noise, output ceiling and dynamic range of the composite TIAs at 1 pF and 2 kΩ. The high-voltage composite (OPA859 driving a THS3491 inside the $R_F$ loop, plain and dual-feedback, Section 11.6) follows Eqs. (71)–(73); the discrete-transistor composites (LSBF862, CPH3910, CE3512K2, and BFP740ESD at 1, 3 and 10 mA, each cascoded with an OPA859 buffer, Section 11.5) follow Eqs. (67)–(68) with the device data that `spice_composite_checks.py fet_devices` saves. It holds the THS3491 readings: Fig 8-22 open-loop transimpedance (magnitude and phase at 26 frequencies), Table 9-2, the vertices of both Fig 9-4 curves, and HD2 and HD3 at 100 MHz against swing from Figs 8-13 and 8-14; and the closed-loop gain of a current-feedback stage with the capacitance at its inverting node (Eq. (71)). The main run scans every design over its capacitance corners (high-voltage composite at $G_2$ = 2–8, discrete composites at $C_N$ = 0–100 pF and $C_F$ = 0.10–1.50 pF) and writes `../data/results/composite_analytical.json`, with, per discrete transistor, the robust design of largest dynamic range at 0.1 mA (`best`) and, where none is robust, the widest-band design that keeps the margins (`widest_with_margins`), as Table 11.6 uses them; `--fine` scans the dual-feedback composite at $G_2$ = 4–7, $C_L$ = 2.0–4.0 pF and $C_F$ = 0.100–0.300 pF and writes `../data/results/composite_hv_fine_scan.json` (about 15 s). No simulation. Usage: `python composite_tia.py [--out <json>]`, `python composite_tia.py --fine` |
| `spice_composite_checks.py` | The SPICE checks of the composites with the vendors' models (OPA859 as in Section 10; THS3491 from TI SBOMBP9). `ths_smoke`: operating point and the model's noise at G = 5. `ths_referee`: the datasheet's Fig 9-1 test circuit at the four gains of Table 9-2, for comparison with Fig 8-1. `ths_zol`: the model's open-loop transimpedance as Fig 8-22 defines it, the internal transimpedance with the 1.2-pF inverting-node capacitance taken out, and Eq. (71) against the model's own closed loop. `hv_compare`: 16 designs of the high-voltage composite at nominal capacitances against Eqs. (72)–(73). `hv_verify`: the four robust designs of Table 11.9 and two designs of the datasheet description over their 27 corners. `hv_tone`: tone runs at 100 and 150 MHz from 0.5 to 1.3 times the analytical ceiling. `fet_devices`: each transistor's two-port admittances, DC currents and input voltage noise at its composite's operating point, and the buffer's gain and input admittance. `fet_compare`: 36 discrete-transistor designs at nominal capacitances against Eqs. (67)–(68). `fet_verify`: the six designs of Table 11.6 over their nine corners. The transistor cards (`FET_CARDS`) and their sources are documented in the script and in `../spice/models/README.md`. Decks and logs are under `../spice/runs/composite/<check>/<case>/` and results in `../spice/results/composite_<check>.json`. Every log is scanned for convergence aids and failures (gmin or source stepping, singular matrix, time step too small, errors, warnings), which are recorded per deck in `../spice/results/composite_convergence.json` together with what was done about each (`CONVERGENCE_NOTES`, `NETLIST_NOTES`); the check `notes` rewrites only those notes, without running a deck. Usage: `python spice_composite_checks.py <check> [--ngspice <library>] [--spice <folder>]` |
| `overlay_digitized.py` | Draws the readings on the rendered datasheet figure, to check them by eye, and prints each reading's residual against the figure's own vector path. Figures: THS3491 Fig 8-22 (with insets at 100 kHz–100 MHz and 100 MHz–1 GHz) and Fig 9-4 (with an inset at 10–500 MHz), OPA859 Fig 6-10 (the composite's first stage, readings from `../data/specs/OPA859.json`), and THS3491 Fig 8-1 with Eq. (71), the textbook formula and the SPICE model's response. The axis calibration is the plot frame; cyan crosses at calibrated grid points show that it lands on the printed grid. The readings are imported from the files the analysis uses, so the images show the numbers that enter the calculations. It writes the PNGs, `residuals.json`, `fig8-1_datasheet_curves.json` (TI's measured −3 dB and peaking per gain) and `manifest.json` to `../data/digitization_checks/`. The manifest records, per image, the datasheet file and its SHA-256, the page, frame, calibration and clip, every series drawn with its source file and variable and the values drawn, and the SHA-256 of each source file. Usage: `python overlay_digitized.py [--zoom 4] [--out-dir <dir>] [--spice ../spice/results/composite_overlay_curves.json]` |
| `digitization_checks/datasheet_figure_probes.py` | The one-off probes run during the figure checks of 27 Oct 2026, kept so that each step can be repeated: figure captions and condition lines with their positions (`captions`), the `integrated_tia/spans.py` calls that gave each figure's tick labels and frame (`spans`), the figures rendered without overlay (`plain`), every vertex of the Fig 9-4 curves and the Fig 8-22 paths read at the analysis frequencies, the values in `composite_tia.py` (`vertices`), the stroke colours of the Fig 8-1 curves (`colours`), the electrical-characteristics lines on input capacitance, impedance and noise (`ec`), the test-circuit pages and page 27 rendered (`testcircuit`), and the largest residual per series (`residuals`). Reads the PDFs only. Usage: `python digitization_checks/datasheet_figure_probes.py <probe> [--out-dir <dir>]` |
| `composite_report_numbers.py` | Prints every number that Sections 11.5–11.7 quote, from the saved results of `composite_tia.py`, `spice_composite_checks.py` and `overlay_digitized.py` and from `../spice/results/dr_comparison.json`: Table 11.7 and the THS3491 open-loop comparison; the plain and dual-feedback designs with their dynamic range at 100 and 150 MHz by Eq. (56) and with $\lvert Z_T\rvert = R_F$; the ±7.5-V case; the tone runs; the lower-noise first stage; the distortion-limited ceilings with Eq. (74); and the transistors and discrete composites of Tables 11.5–11.6, with their output DC level. No simulation. Usage: `python composite_report_numbers.py [--spice <folder>]` |

The THS3491 readings in `composite_tia.py` are the figures' vector paths read with the plot frame as the axis calibration; the tick-label centres sit about 0.36 pt below their grid lines and are not used. Their largest residuals against the paths are 0.005 dB and 0.005° (Fig 8-22) and 0.008 V (Fig 9-4). The Fig 9-4 values are the vertices of the curves, which are drawn as straight lines in $\log f$ between tabulated points. The OPA859 readings of `../data/specs/OPA859.json` have largest residuals of 0.10 dB and 0.16°. They skip the narrow notch near 2.7 GHz, between the readings at 2 and 3 GHz.

## Report-assembly helper

| Script | Purpose |
|---|---|
| `splice_section_7_11.py` | Replaces Section 7.11 of the report part file with its two-variant version; run in the folder that holds the part files |
| `assemble_section11.py` | One-off edit of 27 Oct 2026 that inserted the first Section 11 and Section 0.7 into the report, with Table A2.2 and Appendix 1 item 19, from draft text files. It asserts that every anchor occurs once. Usage: `python assemble_section11.py <report.md> <folder with the drafts>` |
| `add_coherent_tias.py` | One-off edit of 27 Oct 2026 of `../data/integrated_tias.json`: restates MATA-006801 at the gain at which its noise is published and adds the coherent-receiver TIAs (GX39220, RG8G32423, the Qorvo, Renesas, Marvell and MaxLinear parts), with their page citations. It edits the text so the file keeps its layout, and checks that the result parses. Usage: `python add_coherent_tias.py <integrated_tias.json>` |
| `edit_report_coherent_fet.py` | One-off edit of 27 Oct 2026 of the report: the coherent-receiver TIAs in Section 11.4 (Eqs. (60)–(61)), the discrete-FET front end as Section 11.5 (Eqs. (62)–(65), Tables 11.3–11.4), the verdict as Section 11.6, and the matching changes to Sections 0 and 0.7 and Appendices 1–4. Every edit is anchored on whole lines that must occur once. Usage: `python edit_report_coherent_fet.py <report.md>` |
| `edit_report_composites.py` | One-off edit of 27 Oct 2026 of the report: Section 11.5 extended with the discrete-transistor composites (Eqs. (66)–(70), Tables 11.5–11.6, [A23]–[A24], and the bias, package and layout of RF transistors at the summing node), Section 11.6 the high-voltage output stage (Eqs. (71)–(75), Tables 11.7–11.11), Section 11.7 the SPICE models, decks and convergence (Tables 11.12–11.13), the verdict as Section 11.8, and the matching changes to the reading guide, Sections 0.7 and 11 and Appendices 1–4 (Table A2.4, [S21]–[S23]). Every edit is anchored on whole lines, or one exact phrase, that must occur once, and the report keeps its LF line ends. Usage: `python edit_report_composites.py <report.md>` |

## `rework/`: the narrative order of the report

On 27 October 2026 the report was put into the order in which the design is worked out, with every old block of text kept: what we are designing (Chapter 1), the approaches and the 50-Ω benchmark (2), a first op-amp TIA worked through (3), the theory (4), the SPICE cross-check (5), the op amps compared in charts (6), composite front ends (7), the proposed front end and its DC handling (8) and the conclusions (9). The tables moved to Appendix A, except Tables 1.1, 3.1 and 9.1; the SPICE how-to became Appendix B, and the old Appendices 1–4 became C–F. The report as it was before is kept as `../TIA_opamp_survey_before_rework_2026-10-27.md`.

| File | Purpose |
|---|---|
| `rework_narrative.py` | The engine. It cuts the old report into blocks, puts them in the order of `rework_plan.py` with their new headings and the new text, moves the tables to Appendix A, and renumbers every section, equation, table, figure and appendix reference through tokens that name the old item, so that no number is mapped twice. Equation numbers inside citation brackets and in the reference list belong to the cited papers and are left alone. It checks that every old block is used once, every reference resolves, the 81 equation tags run in order, ranges stay ranges, and every cited section, table, equation and figure exists. Usage: `python rework_narrative.py ../../TIA_opamp_survey_before_rework_2026-10-27.md ../../TIA_opamp_survey.md .`; it reproduces the report as reorganized on 27 October 2026, and later edits are made in the report itself |
| `rework_plan.py` | The plan read by the engine: the old→new section map, the new chapter openings, transitions and sections (the 50-Ω benchmark of Section 2.1, the worked comparison of Section 3.3, the electronic and usable dynamic range of Section 4.8, the chart sections of Chapter 6 and Section 6.8, the conclusions of Section 9.5), the hand edits of old text with their exact anchors, and the first-person-plural replacements of the old self-references |
| `report_inventory.py` | Lists the old report's blocks with their tables, equation tags, figures and first and last paragraphs, which the plan was built from. Usage: `python report_inventory.py <report.md> [--full <first line> <last line>]` |
| `check_content_kept.py` | Confirms that every line of the old report survives: each line is normalized (reference numbers and the words that name them removed, self-references dropped) and looked up in the new report; the lines it lists are the old headings, the old front matter and chapter-11 roadmap that the new openings replace, and the hand edits of the plan. Usage: `python check_content_kept.py <old report.md> <new report.md>` |
| `TIA_opamp_survey.map.txt` | Written by the engine: every old equation, figure, table and section number with its present one |
| `TIA_opamp_survey.refs.txt` | Written by the engine: how often each voice replacement applied, the problems found (none), and every rewritten reference with its old and new form and count |

### The logic round of 1 November 2026

The report was then edited so that it reads as one argument: the opening states the three properties of the problem that decide the design, each chapter opens with the question it answers, each comparison of Chapter 6 opens with its mechanism before its chart, results are stated once where they are derived and pointed to elsewhere, and the thirteen sections of the conclusions were merged into seven. Every changed number was checked against the tables and data of the report before it was encoded. The edit also restores four equation numbers of cited papers (TI's SBOA122 Eqs. (12) and (13), Hobbs [A11] Eq. (8) and Hobbs [A22] Eq. (7)) that the 27 October engine had renumbered because they stood outside citation brackets. The report as it was before is kept as `../TIA_opamp_survey_before_logic_round_2026-11-01.md`; the edit reproduces the present report from it.

| File | Purpose |
|---|---|
| `edit_logic_round2.py` | Applies the round: the new opening and chapter openings, the rebuilt conclusions, the references into them, and the reviewed fixes of the modules below, in that order. Every edit is an exact replacement of text that must occur exactly once (operations `replace`, `paragraph`, `span`, `delete` and `move`), so the script stops at the first anchor that does not match. Reads and writes with LF line endings. Usage, from `rework/`: `python edit_logic_round2.py ../../TIA_opamp_survey_before_logic_round_2026-11-01.md ../../TIA_opamp_survey.md` |
| `logic_round2_text.py` | The new text: the opening of the report, the openings of Chapters 1, 2, 4, 6 and 8, and the seven sections of the conclusions |
| `logic_round2_fixes.py` | The status notes of the list of checks, the references into the rebuilt conclusions, and the publication fixes (datasheets, application notes and vendor model files are named with their sources and are not part of the public repository) |
| `logic_round2_fixes_ch1_4.py` | Fixes in Chapters 1–4: the question, the imbalance cost, the selection rule, the 50-Ω benchmark's definitions, the single-chip TIAs of Section 2.5, the worked example, the section leads and assumptions of Chapter 4; moves the 2-pF option to Section 6.3.5, the numerical method of Section 4.9 to Section 4.5, and the bench board's relation to Figure 12 to Section 6.2.7 |
| `logic_round2_fixes_ch5.py` | Fixes in Chapter 5: a short opening; Section 5.1 becomes the motivation of the cross-check and Section 5.9 holds every finding once; corrected statements in Sections 5.2–5.8 |
| `logic_round2_fixes_ch6.py` | Fixes in Chapter 6: mechanism-first leads of Sections 6.2–6.4, the corrected grouping of the parts that fail (by Eq. (20)), the corners, the post-filter, the notes of Tables A6.5, A6.6 and A6.13 moved under their tables, and the SPICE points of Section 6.5 moved to Appendix B.1 |
| `logic_round2_fixes_ch7_8.py` | Fixes in Chapters 7–8: the question of Section 7.1 first and the device physics before the verdicts, the specification and the verdict of Section 7.2, what the front end of Section 8.9 is before its two variants, one window per part in Section 8.10, and the leads of Sections 8.8 and 8.11 |
| `check_numbers_kept.py` | Lists the numbers of the old report (with their units or ranges) that the new report no longer contains, so that each can be confirmed as a correction or a restatement. Usage: `python check_numbers_kept.py <old.md> <new.md> [<first line> <last line>]` |
| `check_eq20_groups.py` | Checks the grouping of the decompensated parts in Section 6.2.1: the minimum source capacitance of Eq. (20) at 2 kΩ for every part of `parts_db.py`, against the baseline node capacitance. Usage, from `scripts_archive/`: `python rework/check_eq20_groups.py` |

### The schematics and wording round of 3 November 2026

The circuit drawings were redrawn with `make_schematics.py` and `schematic_style.py` and inserted as Figures 21–31, Chapter 3 and Section 4.7 were reworded, and every heading and section opening of the report was given plain wording and the reason for the section. A consistency sweep followed: the words drawn inside the figures and the names, citations and abbreviations of the text were brought in line with one another. Each edit replaces text that must occur exactly once, in a report that must still have the hash it had when the edit was written, so these scripts record the edits and do not apply to the present report again.

| File | Purpose |
|---|---|
| `edit_companion_schematics.py` | Inserts Figures 21–31 with their captions and the references to them, the new caption of Figure 1 and the Appendix E row |
| `edit_companion_language.py` | Chapter 3 as a design example: its headings and opening, the explanation of $C_{CM} + C_{DIFF}$ at its first use, and the same wording where other chapters refer to it |
| `edit_section_4_7_context.py` | Section 4.7: its plain heading, and the opening that says why the current noise of a FET input matters at 2 kΩ and why the answer is a range |
| `plain_wording_pass.py` | Applies the 46 heading and opening changes of `plain_wording_pass_pairs.txt`. Usage: `python plain_wording_pass.py [PAIRS_FILE] [EXPECTED_HASH]` |
| `plain_wording_pass_pairs.txt` | The old and new texts of that pass |
| `extract_openings.py` | Lists every heading of a Markdown note with its first paragraph, from which the pass was reviewed (used on both notes). Usage: `python extract_openings.py <note.md> <out.txt>` |
| `fix_figs_1.py`, `fix_figs_2.py` | Label and spacing patches to `make_schematics.py` during the redraw (Figures 21–23, 30 and 31); historical, the archived `make_schematics.py` contains them |
| `fix_style3.py` | A patch to `schematic_style.py` (a rotation angle for the transistor helpers, and switch and LED helpers) that also copied the style to the high-gain note's archive and to its high-voltage study; historical |
| `src_test.py` | A probe of how schemdraw places source elements, after which the two-terminal helper of `schematic_style.py` uses `endpoints()`; historical |
| `archive_session_scripts.py` | Copies the one-off scripts of 2–3 November 2026 from a working folder into this folder and into the high-gain note's archive, with absolute paths made relative. Usage: `python archive_session_scripts.py <working folder> <folder holding both notes>` |
| `consistency_sweep_figure_labels.py` | The words drawn in Figures 3, 5–9, 18 and 19 brought in line with the report: "analytical model" for the earlier "survey", and Eqs. (37), (39), (47) and (23) for the numbers these equations had before the narrative order. Figure 20 names the two composites as the text does. Edits `make_spice_figures.py` and `make_narrative_figures.py`, which then redraw the figures from saved results (`--only 7 9 10 11 12 13 15 16`, and `fig_benchmark` for fig20) |
| `consistency_sweep_text.py`, `consistency_sweep_pairs.txt` | The text side of the sweep: the pHEMT and high-voltage composites named and pointed to (Sections 7.1 and 7.2) wherever they appear before Chapter 7, figures and tables cited in the sections that hold them, abbreviations defined at first use, and "gain–bandwidth" spelled with an en dash. The row labels that `benchmark_50ohm.py --tables` prints follow the new names |
| `citation_order.py` | Lists where each figure and table of a note is cited, and flags any that the section holding it does not cite. Usage: `python citation_order.py <note.md>` |
| `section_ref_overlap.py` | Flags section references whose surrounding words share nothing with the cited section, for a reader to check. Usage: `python section_ref_overlap.py <note.md> [min_shared]` |
| `renumber_section_8_6_figure_33.py` | One-off edit that made room for the new Section 8.6 and Figure 33: it shifts Sections 8.6–8.11 to 8.7–8.12 and Figures 33–51 to 34–52 in the headings, captions, image lines and every reference the build treats as the note's own. It uses the build's reference patterns, leaves other documents' references and quoted datasheet words alone, prints every change for review, and writes only if the file's hash matches. Applied to the note and to `parasitic_cf/numerical/numerical_section_template.md`. Usage: `python renumber_section_8_6_figure_33.py FILE EXPECTED_HASH [--dry-run]` |
| `renumber_pointers_outside_note.py` | The same shift in the files outside the note that point at those numbers: the high-gain note and its part file, this README, `parasitic_cf/INDEX.md`, the docstrings and comments of the current scripts, the text of the interactive layout pages and pcbcap's one pointer. Each replacement must occur as often as listed, or nothing is written. Historical one-off scripts, their README rows and the run records keep the numbers of their time. Usage: `python renumber_pointers_outside_note.py [--dry-run]` |
| `reorder_g14_figures.py` | One-off edit that numbers the first three figures of Section G.14 in the order in which they are cited and placed: the checks of the field solver become Figure 45, the model Figure 46 and its field Figure 47 (they were 47, 45 and 46), in the note, its G.14 template, `parasitic_cf/INDEX.md` and three script docstrings; the image files keep their names. Each replacement must occur as often as listed, or nothing is written. Usage: `python reorder_g14_figures.py [--dry-run]` |

## Low-frequency noise (Section 6.9, 3 November 2026)

| Script | Purpose |
|---|---|
| `low_frequency_noise.py` | The 2-kΩ TIA's input-referred noise at low frequency for the ten amplifiers carried forward, from the voltage- and current-noise curves digitized in `data/specs/`, against the Johnson noise of $R_F$ and the shot noise of $I_1 + I_2$. Writes Table A6.37 (1 kHz and 100 Hz, caption included) to `data/results/table_a6_37.md`; values below a curve's first point are marked as 1/f extrapolations. With an argument it also writes a text summary that adds 10 kHz. Usage: `python low_frequency_noise.py [OUT_TXT]` |
| `rework/low_frequency_section.py`, `rework/low_frequency_section_pairs.txt` | One-off edit that added Section 6.9 and Table A6.37 to the report, with the references to them in the opening of Chapter 6, in Section 9.2 and in Appendix C (item 21). Usage: `python rework/low_frequency_section.py [EXPECTED_HASH]` |

## The shared repository (3 November 2026)

The report now shares one repository with the high-gain note: each note has its own folder, and the build of the PDFs and web pages, `build/` at the root of the repository, serves both.

| Script | Purpose |
|---|---|
| `rework/apply_pairs.py`, `rework/publication_pairs.txt` | Applies a file of old/new text pairs to the report, each old text exactly once, and only if the report still has the hash given. The pairs file says in Appendix E that the build sits at the root of the repository. Usage: `python rework/apply_pairs.py rework/publication_pairs.txt 0a01b9205bb8` |

## The two design examples of Chapter 4 (4 November 2026)

Chapter 3 is the theory and Chapter 4 lays out two designs, OPA855 at 0.20 pF and OPA846 at 0.75 pF, both at $R_F$ = 2 kΩ and 1 pF, and checks each with our analytical model and with the vendor's macromodel. The rows below use the present numbering.

| Script | Purpose |
|---|---|
| `case_studies.py` | Every simulation of Chapter 4, with the vendors' macromodels in ngspice (through `spice_tia_checks.py`'s decks, Middlebrook's double injection and its model translation) and our analytical model at the same points. `run` simulates, for each design, the loop gain, transimpedance, noise (100 kHz–10 GHz) and a 10-µA step at $C_D$ = 0–5 pF with $C_F$ fixed; a scan of total $C_F$ at every $C_D$ (0.10–0.60 pF in 0.02-pF steps for OPA855, 0.30–2.00 pF in 0.05-pF steps for OPA846), from which the widest-band $C_F$ that keeps 45°, 3 dB of gain margin and ≤ 1 dB of peaking is chosen; and the large-signal tones of Section 5.7 at 20–200 MHz. It writes `../spice/results/case_studies.json` and the curves to `case_studies_curves.json`; the decks go to `../spice/runs/case_<PART>/`. About four minutes. `tables` writes every result, with the designs against the 50-Ω benchmark (definitions of `benchmark_50ohm.py`) and Eq. (19) with the macromodels' fitted quantities, to `../data/results/case_studies_tables.md`; `notetables` writes Tables A4.1–A4.4 to `../data/results/case_studies_note_tables.md`. Usage: `python case_studies.py run [--parts OPA855 OPA846] [--steps nominal cd cf tone]`, `python case_studies.py tables`, `python case_studies.py notetables` |
| `make_case_figures.py` | Figures 4 and 6–8 from the saved results, with our analytical model's curves computed from `parts_db.py`: `fig33_case_opa855_simulation` and `fig35_case_opa846_simulation` (transimpedance, loop gain, step, noise and its terms at 1 pF; transimpedance and noise at 0–5 pF), `fig36_case_design_space` (both designs against $C_F$ and $C_D$) and `fig37_case_large_signal_dr` (largest amplitude against frequency, dynamic range against $I_1 + I_2$). No simulation. Usage: `python make_case_figures.py [--spice <folder>] [--out <folder>] [--only opa855 opa846 space large]` |
| `case_low_end.py` | The low end of the two designs of Chapter 4 in closed form (Eqs. (33a) and (33b)): checks the single-corner forms of the 1/f noise against every point of the digitized curves in `data/specs/`, then gives each design's white floor $S_0$, 1/f weight $K$ and corner $K/S_0$ at $I_1 + I_2$ = 0, 0.1, 1 and 10 mA, the spot noise at 100 Hz, 1 kHz and 10 kHz, what the 1/f noise adds to the band noise for low edges of 100 Hz, 1 kHz and 10 kHz, and the frequency where the two designs' noise is equal. No simulation. Usage: `python case_low_end.py` |
| `case_timing_test.py` | A timing and sanity test of the building blocks of `case_studies.py` (loop gain, noise at 100 MHz, the step in SPICE and in our model), run once while that script was written to see how long each simulation takes. Usage: `python case_timing_test.py <scripts_archive folder>` |
| `make_schematics.py`, functions `fig32_case_opa855` and `fig34_case_opa846` | Figures 3 and 5, the two designs as simulated with every value of Table 4.1, drawn by `case_schematic()` in the shared style. Usage: `python make_schematics.py ../figures fig32_case_opa855 fig34_case_opa846` |
| `rework/reorder_case_studies.py` | Puts the theory before the design examples: exchanges Chapters 3 and 4, inserts the new Chapter 4 (`rework/case_chapter_2026-11-04.md`, written in the present numbering) and its Tables A4.1–A4.4, renumbers every reference to sections, chapters, equations, tables and figures in one pass through tokens (equations of other documents left alone: in citation brackets, after a possessive, before a citation bracket, and in Appendix D), applies the anchored rewrites of the openings and appendices, and checks equation tags, figure order and every cited item. Writes `rework/case_studies_reorder.map.txt` and `rework/case_studies_reorder.refs.txt`. Usage, from `rework/`: `python reorder_case_studies.py <note of 3 November.md> <new note.md> case_chapter_2026-11-04.md ../../data/results/case_studies_note_tables.md` |
| `rework/case_chapter_2026-11-04.md` | The text of Chapter 4 as inserted, in the present numbering |

## Larger feedback resistors (Section 6.10, 4 November 2026)

The report now follows the leading amplifiers up to 10 kΩ, where the high-gain note takes over; the two notes meet there.

| Script | Purpose |
|---|---|
| `medium_gain.py` | The analysis of Chapter 6 at $R_F$ = 2, 3, 5 and 10 kΩ for the ten amplifiers carried forward, with `run_analysis.robust_design` but no capacitance added at the input, for 0.2 pF and 0.1 pF across $R_F$: bandwidth, phase margin, the band penalty over 10 MHz to the lower of 150 MHz and the bandwidth (central FET model), and the DC photocurrent of the pair whose shot noise equals the TIA's noise. Writes Tables A6.38–A6.39 (captions included) to `../data/results/table_a6_38.md` and `table_a6_39.md`, and everything to `../data/results/medium_gain.json`, which also keeps the widest design with added input capacitance and the designs with the calibrated curves of OPA855, OPA858 and OPA859. About two minutes. Usage: `python medium_gain.py` |
| `rework/medium_gain_section.py`, `rework/medium_gain_section_pairs.txt` | One-off edit that added Section 6.10 and Tables A6.38–A6.39, with the box, the chapter overview, the opening of Chapter 6, Section 9.2 and Appendices C (item 22) and E, and dropped the date from the subtitle. Usage: `python rework/medium_gain_section.py [EXPECTED_HASH]` |
| `rework/spice_10k_pairs.txt` | One-off edit, applied with `rework/apply_pairs.py`, that adds the SPICE check at 10 kΩ run by the high-gain note (its Section 9.8) to the end of Section 6.10 and to Appendix C item 22. Usage: `python rework/apply_pairs.py rework/spice_10k_pairs.txt b4a53a4e920e` |
| `rework/spice_10k_opa955_pairs.txt` | The follow-up of the same day that adds OPA955 to that SPICE check, in the same two places. Usage: `python rework/apply_pairs.py rework/spice_10k_opa955_pairs.txt e12c3198f854` |

The high-gain note's `scripts_archive/hg_cross_check_companion.py` imports `tia_model.py`, `parts_db.py` and `run_analysis.py` from this folder to run this note's model on its own node at 2 kΩ and 10 kΩ. Its `scripts_archive/hg_spice_medium.py` imports the same three modules, reads `../data/results/medium_gain.json` for the designs of Table A6.38, and runs OPA855, OPA955 and OPA818 on this note's node in SPICE at 10 kΩ, with this note's supplies, loads and double injection, writing only into the high-gain note's folder.

## The DC sink against a plain DC-coupled TIA (Section 8.6)

| Script | Purpose |
|---|---|
| `sink_vs_plain_hv.py` | Compares Option A's resistive DC sink (Section 8.2) with a plain DC-coupled TIA whose amplifier swings the DC itself and whose output is AC-coupled into a later stage (Option D of Section 8.5 with a high-voltage first stage), in closed form, for the single-ended example of 10 mA at 2 kΩ. Its docstring derives Eqs. (1)–(10). It prints: the resistor floor of each scheme for a given voltage across the resistor that carries the DC; the voltage at which the sink breaks even; the photocurrent at which the light takes over; the OPA855 band noise with the sink at 0–10 mA; OPA846's 1/f voltage noise on the node's conductance at 100 Hz; the excess noise and self-heating of the DC-carrying resistor; and, for the later DC-rejecting stage, its noise and its recovery after a step. These are the numbers of Section 8.6 and Table 8.1, and those of the servo resistor's excess noise in Section 6.9. With `--figure OUT_STEM` it also draws Figure 33 (`figures/fig26b_sink_vs_plain`, PNG at 600 dpi and PDF). Usage: `python sink_vs_plain_hv.py [--figure OUT_STEM]`. |

## The parasitic feedback capacitance (Appendix G, 4 November 2026)

Appendix G estimates the capacitance across the feedback resistor from the geometry of the resistor, its pads and the amplifier's pins, and Table 1.1 takes its value: 0.08 pF, with corners at 0.05 and 0.12 pF. The scripts are in `parasitic_cf/`, indexed in `parasitic_cf/INDEX.md`, and their data in `../data/parasitic_cf/`.

The analysis scripts keep their constants `C_FPAR_NOM` = 0.2 pF and `C_FPAR_RANGE` = (0.1, 0.3) pF (`run_analysis.py`), `CF_FLOOR_pF` = 0.20 (`case_studies.py`) and `C_FPARS` = (0.2, 0.1) pF (`medium_gain.py`). Since Appendix G was added they stand for the minimum total $C_F$ of every design, for that total moved by ∓0.1 pF, and for the two values across $R_F$ of Section 6.10, so every number the scripts compute is unchanged. Only their comments and the labels of the tables they write were changed (`parasitic_cf/patch_analysis_labels.py`), and `starting_values.py` now gives the external capacitor of Table A8.13 as the total minus 0.08 pF. The output files in `../data/results/` were written before Appendix G: their numbers are those of the note, but some of their labels still call 0.2 pF the parasitic, and the external capacitors in `starting_values.md` are the totals minus 0.2 pF. The note's tables carry the present labels. `make_schematics.py` draws Figures 3 and 5 with the fitted capacitor beside the 0.08-pF parasitic, 0.12 pF for OPA855 and 0.67 pF for OPA846.

## PDF helpers

| Script | Purpose |
|---|---|
| `render_pdf_pages.py` | Render PDF pages, or a clipped region of one page, to PNG for reading |
| `pdf_find_text.py` | List the pages whose text matches a regular expression. Used only to locate pages, which were then rendered and read |

## `extraction/`: datasheet-curve extraction tools

These tools were used to read curves and values off the datasheets. Vector-drawn plots were read from the PDF path data; raster plots were read by pixel colour, and every reading was compared with the rendered figure. Several were renamed when archived; the content is unchanged.

| Script | Purpose |
|---|---|
| `pdf_vector_curves.py` | Digitize curves drawn as vector paths in a PDF plot: dump the paths, map them to data units with the axis calibration |
| `pdf_vector_paths_sampler.py` | Sample vector-path curves at chosen abscissae, as a cross-check on visual readings |
| `vector_curve_extract.py`, `vector_curve_reader.py`, `vector_curve_probe.py`, `digitize_vector_curves.py` | Variants of the same vector-path reading, as written for different datasheet layouts |
| `vector_ids_by_style.py` | Select path ids from a `pdf_vector_curves.py` dump by stroke style and region |
| `pdf_drawing_items.py` | Print the path items of selected drawings on a page in data units |
| `plot_frames_and_labels.py` | List plot frames on PDF pages with their tick labels and titles, for axis calibration |
| `overdrive_recovery_from_vectors.py` | Estimate overdrive-recovery time from a vector-drawn transient plot |
| `raster_curve_digitizer.py`, `raster_plot_digitize.py`, `raster_color_column_digitizer.py`, `raster_column_sampler.py`, `digitize_curve.py` | Read curve values off rendered (PNG) plots by pixel colour along columns |
| `plot_grid_probe.py` | Find gridlines and curve crossings in a rendered plot, for calibration |
| `spec_json_to_md.py` | Render a part's JSON extraction record as the Markdown spec sheet in `../data/specs/` |

During extraction, two different tools were written under the name `pdf_vector_curves.py`, and one copy briefly replaced the other. The archive keeps the original under that name and the second tool as `pdf_vector_paths_sampler.py`.

## `market_scan/`: candidate, lifecycle and price scan

See `market_scan/INDEX.md`. These scripts fetch TI product pages for lifecycle status and 1ku prices, merge the results into `../data/market_scan.json`, and render `../data/market_scan.md`.

## `fet_front_end/`: discrete-FET front-end datasheet survey

The datasheets, SPICE-parameter documents and vendor S-parameter archives read for this survey are in `../datasheets/fet_front_end/`. Pages were located with `pdf_find_text.py` and rendered with `render_pdf_pages.py` (above); every value was read from the rendered page.

| Script | Purpose |
|---|---|
| `fet_front_end/pdf_identify.py` | Print page count, metadata and the first text of each PDF, to tell which datasheet and revision a downloaded file is |
| `fet_front_end/pdf_page_text.py` | Print the extracted text of chosen pages, only to locate tables |
| `fet_front_end/fet_front_end_numbers.py` | Datasheet values typed in with their page and table/figure; prints $f_T = g_m/(2\pi C)$ and the channel-thermal $e_n = \sqrt{4kT(2/3)/g_m}$ at 300 K for each device; converts the lowest-frequency published S-parameters of the pHEMTs (Avago tables typed in; CEL and Mini-Circuits Touchstone files read from the zip archives) to Y-parameters and prints $C_{11} = \mathrm{Im}(Y_{11})/\omega$, $\mathrm{Re}(Y_{21})$ and $\lvert Y_{21}\rvert$ |
| `fet_front_end/phemt_stability_factors.py` | Section 11.5: Rollett's K and the Edwards–Sinsky μ of a transistor from its vendor S-parameter file; prints the range where μ < 1, the smallest μ, and K and μ at 2, 5, 10 and 20 GHz. For CE3512K2 at 2 V and 10 mA, μ < 1 at 2.0–12.6 GHz (0.19 at 2 GHz) and at 19.9–26 GHz, K = 0.23 at 2 GHz and 0.92 at 10 GHz |

Run from `fet_front_end/`:

```
python fet_front_end_numbers.py ../../datasheets/fet_front_end
python phemt_stability_factors.py ../../datasheets/fet_front_end/CE3512K2_CEL_s2p.zip 2V_10mA
```

The bipolar transistor of Section 11.5 (Infineon BFP740ESD) has its datasheets in `../datasheets/bjt_front_end/` and its SPICE model in `../spice/models/BFP740ESD/`.

## `integrated_tia/`: integrated-TIA datasheet extraction

The datasheets read for the integrated-TIA comparison (TI LMH32401, LMH32404, LMH34400, OPA857; ADI MAX40658/59, MAX40660/61, MAX40662, LTC6561, HMC799, ADA4355; Phyworks/Maxim PHY1095 and PHY1090; Maxim MAX3654) are in `../datasheets/integrated_tia/`. Each file name carries the document number, revision and the source of the copy. Pages were located with `findtext.py`, rendered with `render.py` or `montage.py`, and every value was read from the rendered page. Curve values were read from the vector paths of the plots, with the axis calibration taken from the tick-label positions printed by `spans.py`. Coordinates are in PDF points.

The coherent-receiver TIA documents of Section 11.4 are in `../datasheets/integrated_tia/coherent/`: Renesas's GX39220 datasheet, its short-form datasheets and the end-of-life notices PLC230010 and PLC250030 that give the status of its older parts, and Marvell's product briefs. Every page was rendered with `render_all_pages.py` and read; the values are typed into `../data/integrated_tias.json` by `../add_coherent_tias.py`.

| Script | Purpose |
|---|---|
| `integrated_tia/pdfinfo.py` | Print page count, metadata and the first and last text lines of a PDF, to identify the document and revision |
| `integrated_tia/render_all_pages.py` | Render every page of several PDFs to PNG (160 dpi, or the value of the environment variable `DPI`) and print each document's page count, title and date; used for the coherent-receiver documents in `../datasheets/integrated_tia/coherent/`, every page of which was read. Usage: `python render_all_pages.py <output folder> <a.pdf> [<b.pdf> ...]` |
| `integrated_tia/findtext.py` | List the pages that contain given words, only to locate pages to render |
| `integrated_tia/render.py` | Render chosen pages to PNG at a chosen dpi |
| `integrated_tia/montage.py` | Render clipped regions of several pages and stack them into one PNG |
| `integrated_tia/spans.py` | Print text spans (tick labels, legends) and plot-frame rectangles inside a region, for axis calibration |
| `integrated_tia/guides.py` | Render a clipped plot at high dpi with calibrated vertical and horizontal guide lines, for reading raster or filled curves by eye |
| `integrated_tia/vcurves.py` | Read each stroked curve (one path per curve) at given x values, with a median over a small window for noisy measured curves |
| `integrated_tia/vcolor.py` | Same, for curves drawn as many short paths, grouped by stroke colour |
| `integrated_tia/vinterp.py` | Build one polyline from all segments of a chosen colour and interpolate it at given x values |
| `integrated_tia/vlin.py` | Read curves on linear-linear axes (transfer curves, bandwidth versus capacitance) |
| `integrated_tia/vbw.py` | Find the −1 dB and −3 dB frequencies of plotted frequency responses relative to a reference frequency |
| `integrated_tia/vint.py` | Integrate a plotted noise-density curve, $\sqrt{\int i_n^2(f)\,df}$, between given frequencies |

Example, run from `integrated_tia/` (LMH32401 Fig 6-11, 2 kΩ input noise density, page 12):

```
python vcurves.py ../../datasheets/integrated_tia/LMH32401_TI_SBOS965D_2023-01.pdf 12 95.5,527.3,287.1,662.4 95.5,1e4,287.1,1e9,log 662.4,5,527.3,20,log 1e7,5e7,1e8,1.5e8,2e8 0.03
python vint.py ../../datasheets/integrated_tia/LMH32401_TI_SBOS965D_2023-01.pdf 12 95.5,527.3,287.1,662.4 95.5,1e4,287.1,1e9,log 662.4,5,527.3,20,log 1e4 1.5e8 1e-12
```

Lifecycle status and 1ku prices were read from the public TI product pages (embedded offer data) and from the analog.com product pages; no script was needed for these.
