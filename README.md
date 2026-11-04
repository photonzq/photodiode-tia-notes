# Photodiode transimpedance amplifiers: two design studies and amplifier surveys

This repository holds two notes on the choice of operational amplifier for a photodiode transimpedance amplifier (TIA). Together they cover feedback resistors from 1.5 kΩ to 1 GΩ: a balanced receiver with milliamperes of DC photocurrent and at least 150 MHz of bandwidth, extended up to 10 kΩ for smaller photocurrents, and front ends for weak light and moderate gain whose feedback resistors lie between 10 kΩ and 1 GΩ. The two notes meet at 10 kΩ, where both analyses are run and compared.

These notes were created with significant AI assistance. They may contain errors, so check the cited datasheet pages, tables and scripts before relying on a figure.

## The two notes

**Operational amplifiers for a balanced-photodiode transimpedance amplifier: 1 pF, 1.5–2 kΩ, ≥ 150 MHz, 0.1–10 mA of DC photocurrent** (folder [`TIA_opamp_survey_2026-10-25/`](TIA_opamp_survey_2026-10-25/)). The note covers the front end of a balanced optical receiver: a photodiode pair with 1 pF at the summing node, a 1.5–2-kΩ feedback resistor, at least 150 MHz of bandwidth and 0.1–10 mA of DC photocurrent, and it follows the design up to 10 kΩ for a pair that carries less light. Read it as a [web page](https://photonzq.github.io/photodiode-tia-notes/TIA_opamp_survey_2026-10-25/), as a [PDF](TIA_opamp_survey_2026-10-25/TIA_opamp_survey.pdf), or in its Markdown source, [`TIA_opamp_survey.md`](TIA_opamp_survey_2026-10-25/TIA_opamp_survey.md), which GitHub also renders with its equations.

**Operational amplifiers for high-gain photodiode transimpedance amplifiers: 10 kΩ to 1 GΩ, from DC to tens of megahertz** (folder [`TIA_high_gain_survey_2026-11-02/`](TIA_high_gain_survey_2026-11-02/)). The note covers weak light and moderate gain: signal photocurrents from about a picoampere to a few hundred microamperes, bandwidths from below a kilohertz to about 100 MHz, and photodiodes of any material with capacitances from a few picofarads to several nanofarads. Read it as a [web page](https://photonzq.github.io/photodiode-tia-notes/TIA_high_gain_survey_2026-11-02/), as a [PDF](TIA_high_gain_survey_2026-11-02/TIA_high_gain_survey.pdf), or in its Markdown source, [`TIA_high_gain_survey.md`](TIA_high_gain_survey_2026-11-02/TIA_high_gain_survey.md), which is assembled from the chapter files in `parts/`.

## Which note to read

The photocurrent and the bandwidth decide. The photocurrent's shot noise equals the Johnson noise of the feedback resistor $R_F$ at $I = 2k_BT/(qR_F)$, which is 51.4 mV divided by $R_F$ at 25 °C, and a bandwidth $B$ allows at most $R_F = 1/(2\pi BC_{par})$, where $C_{par}$ is the resistor's own capacitance: 10.6 kΩ at 150 MHz and 159 kΩ at 10 MHz for 0.1 pF. With tens of microamperes or more and a bandwidth above about 50 MHz, the feedback resistor is a few kilohms, the light sets the noise floor, and the amplifier's stability and output swing decide the design: that is the balanced-photodiode note. With a few microamperes or less, the resistor must be 10 kΩ or more to keep its noise below the signal's, and the amplifier's voltage noise acting on the node capacitance and, as the gain rises, its input current, the photodiode's shunt resistance and the feedback resistor's own capacitance decide the design: that is the high-gain note. At 10 kΩ, where the notes meet, both models are evaluated, and they agree on the bandwidth of the fast parts they share within 2–15%. Each note opens with a box that says the same, and Table 0 of the high-gain note compares the two regimes line by line.

## What each note does

**The balanced-photodiode note** starts from three properties of the problem. The light, not the amplifier, sets the noise floor over most of the range; the DC photocurrent must stay out of the feedback resistor, which the balanced pair makes possible; and the 1-pF, 2-kΩ operating point is hard to stabilize, which removes most fast, low-noise amplifiers before noise is considered. From these it sets out the approaches, the list of candidates and a plain 50-Ω termination as the benchmark (Chapter 2), and works through the theory and its open-loop model (Chapter 3), two design examples, OPA855 and OPA846 at 2 kΩ, checked in simulation (Chapter 4), a cross-check against the manufacturers' SPICE macromodels (Chapter 5), a comparison of 25 amplifiers in stability, noise and dynamic range, against the 50-Ω benchmark, at low frequencies and with feedback resistors up to 10 kΩ (Chapter 6), composite front ends with a discrete input transistor or a high-voltage output stage (Chapter 7), the handling of the DC photocurrent and the proposed front end (Chapter 8), and the conclusions (Chapter 9). The tables are in Appendix A.

**The high-gain note** is built around three facts. The feedback resistor sets a noise floor that no amplifier can beat. The amplifier enters through its current noise, through its voltage noise acting on the admittance of the summing node, and through its DC errors, and the weights of these terms change from one gain decade to the next. The bandwidth has two ceilings, the amplifier's and that of the resistor's own capacitance, and above the crossover between them the resistor behaves as a distributed RC line. The note describes the circuit and the photodiode (Chapter 1), derives the noise (Chapter 2) and the bandwidth, the stability and the behaviour of the distributed resistor (Chapter 3), and maps which noise term dominates at each gain and frequency (Chapter 4). It then surveys 25 op amps and three discrete-JFET front ends (Chapter 5), and selects amplifiers for each gain decade, for photodiodes with low shunt resistance or large capacitance, for signals at low frequency, and at 10 kΩ, where the notes meet and the choice between wideband FET and low-noise bipolar parts depends on the band (Chapter 6). It also covers gain ranging, logarithmic amplifiers and switched integrators (Chapter 7) and the DC errors, leakage and guarding (Chapter 8). Chapter 9 checks the model against the manufacturers' SPICE models, and Chapter 10 gives the conclusions. The tables are in Appendix A.

## What is in this repository

| Path | Contents |
|---|---|
| `README.md`, `index.html` | This overview, and the same text as the landing page of the web site |
| `LICENSE` | The CC0 1.0 Universal dedication |
| `build/` | The build of the PDFs and web pages, shared by both notes, and its stylesheet |
| `TIA_opamp_survey_2026-10-25/` | The balanced-photodiode note and its files |
| `TIA_high_gain_survey_2026-11-02/` | The high-gain note and its files |

In the two tables below, the paths are relative to the note's folder.

### The balanced-photodiode note

| Path | Contents |
|---|---|
| `TIA_opamp_survey.md` | The note |
| `TIA_opamp_survey.pdf`, `index.html` | The note as a PDF and as a web page, with its section, table, figure and equation references as links |
| `figures/` | Figures 1–37 as PNG and PDF; Appendix E of the note maps the file names to the figure numbers |
| `data/specs/` | One extraction record per amplifier, with a page or figure citation for every value and the digitized open-loop and noise curves |
| `data/market_scan.md`, `data/market_scan.json` | The candidate scan, the rejected parts, lifecycle status and prices, the integrated TIAs and the list of application notes |
| `data/integrated_tias.json` | The single-chip TIA records of Section 6.7 |
| `data/results/` | The output of the analysis scripts, with the tables generated from it |
| `data/digitization_checks/` | The residuals of the digitized THS3491 and OPA859 curves against the datasheet figures' vector paths |
| `spice/results/` | The results of every SPICE check, one JSON file per check, and the tables generated from them |
| `spice/models/` | `README.md` with the source and terms of every vendor model used, and the four Analog Devices model files that ADI's terms allow to be shared unmodified |
| `scripts_archive/` | Every script used for the analysis, the SPICE checks, the figures and the edits of the note, indexed in `scripts_archive/README.md` |

The manufacturers' datasheets and application notes, the Texas Instruments and Infineon SPICE models, and the renderings of datasheet figures are not included. Appendix D of the note gives each document's source and revision, and `spice/models/README.md` gives the download page of every model. The decks, logs and data that the SPICE checks write to `spice/runs/` (about 500 MB) are not included either; running the checks regenerates them.

### The high-gain note

| Path | Contents |
|---|---|
| `TIA_high_gain_survey.md` | The note, assembled from `parts/` by `scripts_archive/assemble_note.py` |
| `TIA_high_gain_survey.pdf`, `index.html` | The note as a PDF and as a web page, with its section, table, figure and equation references as links |
| `parts/` | The chapters as separate files, the source of the note |
| `figures/` | Figures 1–23 as PNG and PDF; Appendix E of the note maps the file names to the figure numbers |
| `data/photodiodes.json`, `data/amplifiers.json` | The photodiode examples of Table 1 and the amplifier data of Table A.1, each value with its datasheet page |
| `data/results/` | The output of the analysis scripts; `data/results/note_tables/` holds the table bodies that `assemble_note.py` inserts into the chapters |
| `spice/results/` | The summaries of the SPICE checks of Chapter 9 |
| `spice/models/README.md` | The source of every vendor model the checks use |
| `scripts_archive/` | The model, the analysis, the SPICE checks, the figures and the edits of the note, indexed in `scripts_archive/README.md` |

The datasheets, application notes and papers read for the note, the vendor SPICE models and the decks and logs that the SPICE checks write to `spice/runs/` are not included. Appendix D of the note gives each document's source, and `spice/models/README.md` gives each model's.

## Building the PDFs and the web pages

`build/build_pdf.py` turns a note's Markdown into HTML with pandoc (MathML for the equations) and prints it to PDF with headless Chrome. With `KEEP_HTML=1` it also keeps the HTML, from which `build/make_web_html.py` makes the `index.html` of the note's folder. `build/make_landing.py` makes the landing page `index.html` from this README. The scripts run from the repository folder with Python 3, BeautifulSoup and PyMuPDF. `build/build_pdf.py` runs `pandoc` and `chrome`, and `build/make_landing.py` runs `pandoc`, each from the PATH or as named by `PANDOC` and `CHROME`. For the high-gain note, for example:

```
python TIA_high_gain_survey_2026-11-02/scripts_archive/assemble_note.py
KEEP_HTML=1 python build/build_pdf.py TIA_high_gain_survey_2026-11-02/TIA_high_gain_survey.md
python build/make_web_html.py TIA_high_gain_survey_2026-11-02/TIA_high_gain_survey.md --remove-print-html
python build/make_landing.py
```

The first line assembles the note from its chapter files; the balanced-photodiode note is edited directly and needs no such step. In a PDF, the link to the other note points to that note's PDF on the web site, whose address `SITE_URL` can change; on a web page it points to the other note's web page. The site is served as static files, as the empty `.nojekyll` file tells GitHub Pages.

## Reproducing the numbers

**The balanced-photodiode note.** The analysis needs Python 3 with NumPy, SciPy and Matplotlib; the PDF extraction tools also need PyMuPDF. The SPICE checks need ngspice 45 or later as a shared library, for example the one installed with KiCad 10, and the vendor models of Table B.1 of the note. Appendix B.2 of the note lists the steps, and `scripts_archive/README.md` says what each script does. The scripts, their docstrings and the tables they generate use the section, table and equation numbers that the note had when they were written; `scripts_archive/rework/TIA_opamp_survey.map.txt` and `scripts_archive/rework/case_studies_reorder.map.txt` convert each of them to the present number.

**The high-gain note.** The analysis needs the same Python packages, with Pillow for the PDF tools. The SPICE checks run the Texas Instruments models in the ngspice shared library of KiCad 10 and the Analog Devices models in LTspice. Appendix B.4 of the note lists the scripts in the order in which they run, and `scripts_archive/README.md` says what each one does. The analytic scripts run in under a minute and the SPICE checks in a few minutes.

## Licence

The notes, their figures, scripts and data are dedicated to the public domain under CC0 1.0 Universal; no copyright is reserved. See [LICENSE](LICENSE). The manufacturers' SPICE model files are not covered: each remains under its vendor's terms, which the `spice/models/README.md` of each note gives. Nor is the LSBF862 model card that the scripts of both notes reproduce, which remains Linear Systems' model.
