# Scripts of the high-gain TIA note

Every script used to extract the data, compute the results, run the SPICE checks, draw the figures and assemble the note. They need Python 3 with NumPy, SciPy and Matplotlib; the PDF tools also need PyMuPDF and Pillow, and the mathematics check needs latex2mathml and Node.js with KaTeX. The SPICE checks need the ngspice shared library that KiCad 10 installs and LTspice. The analytic scripts take under a minute, and the SPICE checks a few minutes.

## Analysis

| Script | What it does |
|---|---|
| `hg_model.py` | The circuit model: the exact transimpedance and input-referred noise of Eqs. (6) and (8), the lumped and distributed (uniform RC line, Eq. (25)) feedback networks, the N-section ladder under a conductor with any potential profile (`ladder_y`, Section 3.4), the interpolation of datasheet noise curves with the shot-noise floor of Section 2.3, the datasheet DC open-loop gain of each amplifier, an optional tabulated shape of the open-loop gain beyond a single pole (used for OPA1656), and the design rule for the feedback capacitance (smallest value at or above the resistor's own capacitance that keeps the response within 0.1 dB of maximally flat). Imported by the other scripts. |
| `hg_analysis.py` | The design sweep of Chapter 6: every amplifier of `data/amplifiers.json` on the five photodiodes at 100 kΩ–1 GΩ, with the mid-band noise gain and its ratio to the open-loop gain. Writes `data/results/designs.json`, `gain_table.json` and `amp_merits.json`. Usage: `python hg_analysis.py` |
| `hg_numbers.py` | The numbers quoted in Chapters 3, 5 and 7: the distributed feedback resistor (peaking, corners, noise rise, output-driven plane), the accuracy of an N-section ladder, the parallel-plate estimate of a chip resistor's capacitance to the plane, the limits of equalization, the discrete-JFET composites and the logarithmic amplifier. Writes `data/results/numbers.json`. Usage: `python hg_numbers.py` |
| `hg_figures.py` | Figures 2, 3, 5, 10 and 11 (PNG at 600 dpi and PDF) in `figures/`, written as `fig1`–`fig5`, the names under which they were first drawn. Usage: `python hg_figures.py` |
| `hg_schematics.py` | The schematics, Figures 1, 4, 6–9 and 12–16, written as `figures/schem_*`: the circuit with its noise sources, the feedback resistor as an RC line, the driven conductors and the guarded split resistor, equalization, the T-network, the discrete-JFET composite of Section 9.5, gain ranging, the log amplifier, the switched integrator and the optical reset. Each function names the section and the values it draws. Usage: `python hg_schematics.py [OUT_DIR] [NAME ...]` |
| `schematic_style.py` | The drawing style shared with the companion notes: one scale (0.30 in per drawing unit) and one canvas width (6.5 in), so that all schematics print at the same scale; white background, 1-pt lines, Arial labels at 8 pt with Computer Modern mathematics; parasitic elements grey, noise sources purple, light red, guards green, optional parts dashed. Needs schemdraw. |
| `hg_tables.py` | Markdown tables from the results: gain table, figures of merit, the full sweep, the dominant noise terms (Tables 4a–4b) and the per-decade shortlists (Tables 6.1–6.5), which leave out the designs that fail the open-loop-gain condition of Section 3.1. Writes `data/results/tables.md`, and the table bodies of Chapters 4 and 6 to `data/results/note_tables/`. Usage: `python hg_tables.py` |
| `hg_appendix_tables.py` | The tables of Appendix A, written to `parts/11_appendix_a.md`, with the designs that fail the open-loop-gain condition marked "A"; Tables A.8a–b come from `hg_low_frequency_noise.py`. Usage: `python hg_appendix_tables.py` |
| `add_aol.py` | Adds the datasheet DC open-loop gain of each amplifier, with its page, to `data/amplifiers.json`. Usage: `python add_aol.py` |
| `set_gbw_opa1656.py` | One-off edit of 2 November 2026: sets OPA1656's gain–bandwidth to its 53 MHz at a gain of 100, after `hg_spice_gbw_check.py`. Usage: `python set_gbw_opa1656.py` |
| `add_aol_shape.py` | Stores the shape of a part's open-loop gain beyond a single pole, from its SPICE model's open-loop run (`spice/runs/<part>/aol/aol.npy`), in `data/amplifiers.json`; `hg_model.py` multiplies the single pole by it. Used for OPA1656 and OPA2156. Usage: `python add_aol_shape.py OPA2156` |
| `set_gbw.py` | Sets one part's gain–bandwidth in `data/amplifiers.json`, with a note on its source; used on 2 November 2026 for OPA2156 (25 MHz). Usage: `python set_gbw.py PART MHZ "NOTE"` |
| `edit_ch9_opa2156.py` | One-off edit of 2 November 2026 that added the OPA2156 gain–bandwidth check to Chapter 9 and updated its counts and closed-form statistics. Usage: `python edit_ch9_opa2156.py` |
| `t_network_vs_second_stage.py` | A T-network in the feedback path against a single 1-GΩ resistor and against a smaller resistor followed by a voltage stage, with the note's two-port model: bandwidth, noise at 100 Hz, in-band excess and output offset (ADA4625-1 on the 20-pF photodiode). Usage: `python t_network_vs_second_stage.py` |
| `integrator_vs_tia.py` | Noise charges per measurement for a switched integrator against a resistor-limited TIA: the resistor's $2\sqrt{k_BTC_{par}}$, reset noise, the photodiode's shunt and dark-current noise, the amplifier's series noise with double sampling, and the channel charge of a MOS reset switch. Usage: `python integrator_vs_tia.py` |
| `set_in_lmc662.py` | One-off edit of 2 November 2026: sets LMC662's input current noise to the 0.2 fA/√Hz of its data sheet's Revision C, as quoted in Revision D's history (Section 2.3). Usage: `python set_in_lmc662.py` |
| `replace_section.py` | Replaces one section of a chapter file in `parts/` by a new text, refusing to write unless the old section contains a given guard text; used on 2 November 2026 for Section 7.3. Usage: `python replace_section.py PART START END NEW_TEXT GUARD` |
| `hg_low_frequency_noise.py` | Section 6.8: the input-referred noise of every design of the sweep at low frequency against the resistor-plus-diode floor. Writes Table 6.6, the critical voltage noise of Eq. (30a) at 100 Hz, to `data/results/note_tables/table_6_6.md`, and supplies Tables A.8a–b (100 Hz and 10 Hz, with the provenance of each amplifier's noise: datasheet, interpolated, extrapolated or held flat) to `hg_appendix_tables.py`. With an argument it also writes a text summary at 10 Hz, 100 Hz and 1 kHz beside the band excess $\Delta N$. Usage: `python hg_low_frequency_noise.py [OUT_TXT]` |
| `hg_equal_bandwidth_check.py` | Compares OPA1656 and OPA2156 at equal bandwidth on the 20-pF photodiode, with OPA1656's $C_F$ raised to OPA2156's bandwidth. Usage: `python hg_equal_bandwidth_check.py` |

## SPICE checks (Chapter 9)

| Script | What it does |
|---|---|
| `ngspice_shared.py` | Loads ngspice-46 as the shared library of KiCad 10 and runs decks from Python. Copied from the companion note. |
| `hg_spice.py` | The ngspice checks: the TIA designs with the Texas Instruments and ADA4817-1 macromodels (`designs`), the macromodels' own noise (`models`), the distributed feedback resistor as a 20-section ladder under six conductor treatments (`distributed`) and the LSBF862 composite (`composite`). Translates TI's noiseless resistors for ngspice. Writes decks, logs and arrays to `spice/runs/` and summaries to `spice/results/`; with `--parts`, the designs and models checks run only for the named parts and replace their entries in the result files. Usage: `python hg_spice.py designs|models|distributed|composite [--parts OPA1656]` |
| `hg_ltspice.py` | The LTspice checks, with LTspice run headless (`LTspice.exe -b -ascii`) on netlists written by the script: the TIA designs and the noise of ADA4530-1, ADA4625-1 and LTC6268-10 (`designs`, `models`), and the logarithmic amplifiers AD8304 and ADL5303 (`logamp`). Usage: `python hg_ltspice.py designs|models|logamp` |
| `hg_spice_gbw_check.py` | The open-loop gain in SPICE (loop closed at DC only through 1 TH) of a part whose data sheet gives two gain–bandwidths, its noise, and its ten designs at the $C_F$ of the sweep against the model with the data file's value and with the alternative. Writes `spice/results/<part>_gbw.json`. Usage: `python hg_spice_gbw_check.py OPA1656 53` or `python hg_spice_gbw_check.py OPA2156 25` |
| `hg_spice_tables.py` | Tables 9.1–9.6, written to `data/results/note_tables/`. Usage: `python hg_spice_tables.py` |
| `hg_spice_figures.py` | Figures 17–23 (PNG at 600 dpi and PDF) in `figures/`, written as `fig6`–`fig12`. Usage: `python hg_spice_figures.py` |

Order of running: `add_aol.py` (once), `hg_analysis.py`, `hg_numbers.py`, `hg_figures.py`, `hg_schematics.py`, `hg_tables.py`, `hg_appendix_tables.py`, the SPICE checks, `hg_spice_tables.py`, `hg_spice_figures.py`, then `assemble_note.py`.

## The note

The PDF and the web page of the note are built by `build/build_pdf.py` and `build/make_web_html.py` at the root of the repository, which its README describes.

| Script | What it does |
|---|---|
| `assemble_note.py` | Concatenates `parts/*.md` in file-name order into `TIA_high_gain_survey.md` with LF line endings, and replaces each line `<!-- table: name -->` by the table body `data/results/note_tables/<name>.md`. |
| `check_refs.py` | Checks the assembled note: equation tags 1…N in order, every cited equation, section, table and figure present, figure files present, no control characters. References to the companion note and to datasheet tables are skipped. |
| `check_math_extract.py` | Extracts every mathematics span, converts it with latex2mathml and writes the spans to a JSON file; reports non-dollar delimiters and table cells split by `|`. Copied from the companion note. Usage: `python check_math_extract.py TIA_high_gain_survey.md <spans.json>` |
| `katex_check.js` | Renders the spans with KaTeX, the second parser. Copied from the companion note. Usage: `node katex_check.js <katex.min.js> <spans.json>` |
| `edit_section_3_4.py` | One-off edit of 2 November 2026 that replaced Section 3.4 of `parts/03_bandwidth.md` by its expanded text, keeping Figure 3, Table 3 and the capacitance estimate unchanged. Usage: `python edit_section_3_4.py NEW_TEXT.md` |
| `edit_ch9_opa1656.py` | One-off edit of 2 November 2026 that added the OPA1656 gain–bandwidth check to Chapter 9 and updated its counts and closed-form statistics. Usage: `python edit_ch9_opa1656.py` |
| `edit_table_placeholders.py` | One-off edit of 2 November 2026 that replaced the hand-copied bodies of Tables 4a–4b and 6.1–6.5 by placeholders filled by `assemble_note.py`. Usage: `python edit_table_placeholders.py` |

## One-off edits of 2–3 November 2026

Each edit replaces text that must occur exactly once, and most refuse to write unless the file still has the hash it had when the edit was written, so these scripts record the edits and do not apply to the present files again.

| Script | What it does |
|---|---|
| `edit_hg_parts_schematics.py` | Renumbers the figures in `parts/` (old 1–12 become 2, 3, 5, 10, 11 and 17–23) and inserts the eleven schematics as Figures 1, 4, 6–9 and 12–16, with their captions and the references to them |
| `edit_hg_scripts_numbers.py` | Brings the figure numbers in the plot scripts' docstrings and in this README up to that renumbering |
| `edit_fig1_caption.py` | The caption of Figure 1: $C_{CM}$ and $C_{DIFF}$ explained, and why $e_n$ drives a current through every capacitance at the summing node |
| `plain_wording_pass.py` | Plain headings, chapter and section openings that give the reason for each section, and the companion's noise equation cited as its Eq. (23); applies `plain_wording_pass_pairs.txt` to `parts/`, after which `assemble_note.py` is run. Usage: `python plain_wording_pass.py [PAIRS_FILE]` |
| `plain_wording_pass_pairs.txt` | The old and new texts of that pass, each group headed by its file in `parts/` and that file's hash before the edit |
| `low_frequency_pairs.txt` | Section 6.8 (signals at low frequency) and its links, 3 November 2026, applied with `plain_wording_pass.py`: the opening of Chapter 6, a bullet in the opening summary, step 10 of Section 10.1 and Appendix C item 22. Run `hg_low_frequency_noise.py` and `hg_appendix_tables.py` first, then `assemble_note.py`. Usage: `python plain_wording_pass.py low_frequency_pairs.txt` |
| `consistency_sweep_pairs.txt` | The consistency sweep of 3 November 2026, applied with `plain_wording_pass.py`: Table A.2, not A.1, cited for $R_{F,\mathrm{crit}}$; Tables 6.2–6.5 and A.6 cited where they stand; the CCDR named in the caption of Figure 6; the four designs of Figure 18 and the twelve macromodels of Figure 19 stated; the companion's Section 4.10 cited for a resistor at the non-inverting input; and TI written out at first use. Usage: `python plain_wording_pass.py consistency_sweep_pairs.txt` |
| `publication_pairs.txt` | Prepares the note for the public repository it shares with the companion note, 3 November 2026, applied with `plain_wording_pass.py`: Appendix E adds the PDF and the web page and says which files the repository holds, and two sentences no longer call the companion's folder a separate repository. Usage: `python plain_wording_pass.py publication_pairs.txt` |
| `fill_hg_schem.py`, `fix_hg_schem2.py`, `fix_fig1_spacing.py` | Patches to `hg_schematics.py` while the schematics were drawn (Figures 1, 6, 7, 9, 12–14 and 16); historical, the archived `hg_schematics.py` contains them |
| `edit_hv_captions.py` | Moves the explanations that the old drawings carried into the captions of `hv_output_stage/hv_output_stage.md`, and explains the stage's remaining parts in the caption of its Figure 3; that study of a high-voltage output stage is not part of the public repository |
| `fix_hv.py`, `fix_hv_stage_layout.py`, `fix_hv_stage_layout2.py` | Patches to `hv_output_stage/scripts/hv_schematics.py` while the high-voltage stage was redrawn wider; historical, the archived `hv_schematics.py` contains them |
| `urc_checks.py` | Quick numerical checks, with `hg_model.py`, of the first-order results for the distributed feedback resistor of Section 3.4: the first-order coefficient for several conductor profiles, the line's noise against frequency and its band average, and the second-order term |
| `fix_ctrl.py`, `fix_tabs.py` | Repair LaTeX backslash sequences that a shell here-document had turned into control characters. Usage: `python fix_ctrl.py FILE` |

## Reading datasheets

| Script | What it does |
|---|---|
| `pdf_find_text.py` | Lists the pages of a PDF whose text matches a regular expression, to locate a value; the value itself is read from a render. Copied from the companion note. |
| `render_pdf_pages.py` | Renders whole pages, or a clipped region, to PNG. Copied from the companion note. |
| `spec_rows.py` | Renders the rows of a specification table that contain given terms, or the figure next to a given caption, as labelled strips stacked into one PNG, so that a value can be read from the rendered page without rendering every page whole. |
| `spec_rows_batch.py` | Runs `spec_rows.py` over the electrical-characteristics pages of several datasheets with the terms that matter for a high-gain TIA. |
