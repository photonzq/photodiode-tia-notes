# Scripts for the parasitic feedback capacitance

These scripts support Appendix G of the note, the analytical estimate of the capacitance across the feedback resistor, and the collections of measured values, dimensions and permittivities in `../../data/parasitic_cf/`. Each script takes its paths as arguments or works relative to its own folder. Run the scripts that read downloaded PDFs in isolated mode (`python -I`).

## The estimate and its figures

| Script | What it does | Usage |
|---|---|---|
| `cf_parasitic_estimate.py` | Evaluates every formula of Appendix G (Eqs. (G.14)–(G.47)) for 0201–0805 resistors, the OPA855 pins, a ground plane and a guard strip, in both mounting orientations. It also runs eleven numerical confirmations (C1–C11) of the special functions, the maps and the limiting cases. | `python cf_parasitic_estimate.py [--json <out.json>]` |
| `make_parasitic_cf_figures.py` | Draws Figures 38–43 of Appendix G (`figures/fig38_parasitic_cf_*` to `fig43_parasitic_cf_*`, PNG at 600 dpi and PDF). The potentials in Figures 40–42 come from the closed-form maps, not from a mesh. | `python make_parasitic_cf_figures.py [outdir]` (default `../../figures`) |
| `inductance_estimates.py` | Estimates what the electrostatic model leaves out: the resistor's own series inductance (as $-L_s/R^2$ in parallel), the partial self-inductance of the routing and vias (Neumann formula), its effect on $R_F \parallel C_F$ at each design's loop crossover, and the inductance in series with the photodiode. Every formula is derived in its comments; it prints every input and substitution. | `python inductance_estimates.py` (reads `../../data/parasitic_cf/numerical/resistor_3d.json`) |

## Reading the sources

| Script | What it does | Usage |
|---|---|---|
| `find_parasitic_statements.py` | Locates the pages of local PDFs that state a parasitic or feedback capacitance, so that those pages can be rendered and read. | `python find_parasitic_statements.py <pdf or folder> [...]` |
| `pdf_overview.py` | Prints page count, metadata and the first characters of every page of a PDF, to identify documents before rendering. | `python -I pdf_overview.py <pdf> [...] [--chars 300]` |
| `pdf_pages.py` | Finds pages matching a pattern, and renders chosen pages to PNG for reading. | `python -I pdf_pages.py find <pdf> <regex>` and `python -I pdf_pages.py render <pdf> <out_dir> --pages 1-3` |
| `dump_pdf_vector_paths.py` | Dumps the vector paths and text spans of one PDF page, so that plotted curves drawn as vector graphics can be read numerically. | `python -I dump_pdf_vector_paths.py <pdf> <page> <out.json> [--clip x0,y0,x1,y1]` |
| `read_vector_impedance_curves.py` | Converts vector-drawn $\lvert Z\rvert/R$ curves into the equivalent parallel capacitance at each point. The axis calibrations are in `curve_specs/`. | see the script's docstring |
| `trace_raster_curve.py` | Reads a curve off a bitmap plot of $\lvert Z\rvert/R$ and converts it in the same way. | `python -I trace_raster_curve.py axes <image.png>`, then the tracing mode in the docstring |
| `merge_curve_readings.py` | Merges the curve readings into `data/parasitic_cf/resistor_curve_readings.csv`. | `python merge_curve_readings.py <out.csv> "<label>=<file>" ...` |
| `inferred_feedback_c.py` | Turns the bandwidths, rise times and fits printed in the board-level sources into feedback capacitances. It writes `data/parasitic_cf/inferred_values.json`. | `python -I inferred_feedback_c.py [out.json]` |
| `build_geometry_permittivity_json.py` | Regenerates `data/parasitic_cf/geometry_and_permittivity.json`, the resistor dimensions, land patterns and permittivities read from the manufacturer documents. | `python -I build_geometry_permittivity_json.py <out.json>` |

## Editing the note

The estimate was first written as a standalone document with its own equation numbers (P1)–(P49), tables P1–P3, figures P1–P6 and reference list [P1]–[P8]. That draft is not kept; it became Appendix G. The first two scripts below were applied to it and match its text, not the appendix.

| Script | What it did | Usage |
|---|---|---|
| `fill_derivation_numbers.py` | Brought the worked examples of the draft in line with the sourced inputs, after the dimensions and permittivities were collected. | `python fill_derivation_numbers.py <draft.md>` |
| `apply_review_fixes.py` | Applied the corrections of an independent review of the draft: one false claim, small slips, the gaps it found (two-dimensional decay, Rule 6 with cuts and floating conductors, onto-ness of two maps, the Landen step, 1/ln h, the film over the pads, the film-pattern equation for a patterned film) and the notation clashes. | `python apply_review_fixes.py <draft.md>` |
| `floor_effect.py` | Evaluated the flat, 1-dB and robust designs of OPA855, OPA858 and OPA955 with the floor of the design search at 0.20 and at 0.08 pF. It showed that a floor at the parasitic would move the 2-kΩ robust designs of OPA855 and OPA858 to 0.14–0.15 pF, where Section 6.2.8 finds little margin left at the corners, which is why the designs keep a minimum total of 0.2 pF. | `python floor_effect.py <scripts_archive folder>` |
| `make_appendix_g.py` | Turned the draft into Appendix G: section, equation, table and figure numbers; the note's citation style and the references [A25]–[A34] and [B3]–[B5] of Appendix D; captions for the tables that had none; and the parts that state how the note uses the estimate. | `python make_appendix_g.py <draft.md> <appendix_G.md>` |
| `revise_note_cfpar.py` | Revised the note to $C_{F,\mathrm{par}}$ = 0.08 pF (corners 0.05–0.12 pF) with a minimum total $C_F$ of 0.2 pF, added the references and files of Appendix G to Appendices D and E, and appended Appendix G. It checks the note's hash before editing. | `python revise_note_cfpar.py <note.md> <appendix_G.md> <sha256 prefix>` |
| `patch_scripts_appendix_g.py` | Pointed `cf_parasitic_estimate.py` and `make_parasitic_cf_figures.py` at Appendix G and at the figure files `fig38`–`fig43`. | `python patch_scripts_appendix_g.py <this folder>` |
| `patch_analysis_labels.py` | Brought the comments and table labels of `run_analysis.py`, `case_studies.py`, `medium_gain.py` and `starting_values.py` in line with Table 1.1; only `starting_values.py` changes a number, the external capacitor of Table A8.13 (total minus 0.08 pF). | `python patch_analysis_labels.py <scripts_archive folder>` |
| `show_sentences.py`, `show_par_lines.py`, `list_refs.py` | Listed the sentences that use a value, and every cross-reference of a Markdown file, while the revision was mapped. | see each docstring |

## Field solutions (Section G.14), in `numerical/`

These scripts use the finite-element package `pcbcap` at the root of the repository (its `README.md` describes it, and each module derives what it does). They write their records and logs to `../../data/parasitic_cf/numerical/`. Each case runs in its own process at below-normal priority; `rerun_all.sh` recomputes everything in order.

| Script | What it does | Usage |
|---|---|---|
| `numerical/g_closed_forms_2d.py` | Solves the idealised two-dimensional problem behind each exact closed form of Sections G.6–G.11 and compares (Table G.10); also gives the values that the closed forms only bracketed (Section G.14.3). | `python g_closed_forms_2d.py list`, then `run <case> [--record <json>]` |
| `numerical/g_resistor_3d.py` | Three-dimensional chip resistors on their pads: convergence and enclosure studies for 0201–0805, the permittivity corners, the flipped part, the construction details, other board materials (with the enclosure correction for three of them), and the OPA855 network of Figure 43. | `python g_resistor_3d.py list`, then `run <case> [--record <json>]` |
| `numerical/g_opa846_3d.py` | The OPA846 in SOT-23-5 with its feedback resistor in three layouts and two sizes, the contributions of the resistor, the package and the planes, and two checks of the numerical choices. | `python g_opa846_3d.py list`, `estimate`, then `run <case> [--record <json>]` |
| `numerical/run_all_3d.sh`, `numerical/run_opa846.sh` | Run every case of the two scripts above, one process per case, logging each one. | `bash run_all_3d.sh [python]`, `bash run_opa846.sh [python]` |
| `numerical/rerun_all.sh` | Deletes and recomputes every record of Section G.14: the package's checks, the 2-D comparisons, both 3-D batches and the region split of the 0402, after copying the old records to a backup folder if one is given. About 1 h 45 min on a workstation that was also in other use. | `bash rerun_all.sh [python] [backup_folder]` |
| `numerical/inspect_layouts.py` | Builds the OPA855 and OPA846 layouts as the solver receives them, draws them from above, in perspective and in a section, checks that every net's metal is one connected piece, and lists every item with its extent. No mesh is made. | `python inspect_layouts.py [out_dir]` |
| `numerical/field_regions.py` | Splits $C_{F,\mathrm{par}}$ of the 0402 model (the mesh of Figures 44c and 45) by region (alumina between the wraps and inside the terminations, FR-4 under the gap and elsewhere, air under the body and elsewhere), by sign and by distance from the part, for the text beside Figure 45. | `python field_regions.py [--record <json>]` |
| `numerical/make_numerical_figures.py` | Draws Figures 44–51 from the records (Figures 44c and 45 solve the 0402 model once). | `python make_numerical_figures.py [figure numbers]` |
| `numerical/development/` | The probes and audit checks written while the package and these cases were built, kept as they were run; its `README.md` lists them. | see that README |
| `numerical/numerical_section_template.md`, `numerical/add_numerical_section.py` | The text of Section G.14 with placeholders, and the script that fills them from the records and makes the edits elsewhere in the note (G.1, G.8, G.11, G.13.5, Table G.6, Appendices C–E), checking the note's hash first. | `python add_numerical_section.py <note.md> <sha256 prefix> [--dry-run <out.md>]` |
