"""Reviewed fixes of the logic round of 1 Nov 2026, read by edit_logic_round2.py.

CH9_CHECK_NOTES   rewrite the status notes of the list of checks (the old Section 9.13, new 9.7)
CH9_REFERENCES    references from other chapters into the rebuilt conclusions
FIXES             ("replace", exact old text, new text) or ("paragraph", opening words, new text),
                  each found exactly once in the note
"""

CH9_CHECK_NOTES = [
    ("*Done for the designs of Tables A8.11 and A8.13, without package parasitics (Section 5.5).*",
     "Section 5.5 runs this check for the designs of Tables A8.11 and A8.13, without package parasitics."),
    ("*Done for OPA855 (Section 5.5).*", "Section 5.5 runs it for OPA855."),
    ("*Settled by the macromodel in favour of the table (Section 5.4).*",
     "The macromodel settles it in favour of the table (Section 5.4)."),
    ("*Not settled by SPICE (Section 5.6).*", "SPICE does not settle it (Section 5.6)."),
]

CH9_REFERENCES = [
    ("Section 9.13 lists the cases where only a simulation or a measurement can settle the answer.",
     "Section 9.7 lists the cases where only a simulation or a measurement can settle the answer."),
    ("  Section 9.13 lists the measurements.", "  Section 9.7 lists the measurements."),
    ("a 1.8–2.5 dB quieter instrument (Section 9.12)", "a 1.8–2.5 dB quieter instrument (Section 9.6)"),
    ("None changes the ranking of Section 9.7, except possibly items 1 and 2.",
     "None changes the ranking of Section 9.2, except possibly items 1 and 2."),
]

FIXES = [
    # Figure 10 and its section: OPA858's robust design adds 0.25 pF, but its flat design needs none
    ("replace",
     "dark red where input capacitance had to be added to reach 45° (0.25 pF for OPA858 at 2 kΩ, 1–8 pF for the others)",
     "dark red where the robust design adds input capacitance (1–8 pF to reach 45°; 0.25 pF for OPA858 at 2 kΩ, whose flat design already reaches 558 MHz at 58° without it)"),
    ("replace",
     "OPA858, with its open-loop curve as plotted, OPA955 and OPA818 get there only with 0.25, 3 and 8 pF added at the input, and nine parts have no robust design at all.",
     "OPA955 and OPA818 get there only with 3 and 8 pF added at the input. OPA858's robust design, with its open-loop curve as plotted, also adds 0.25 pF, although its flat design already reaches 558 MHz at 58° without it. Nine parts have no robust design at all."),

    # publication: the public repository holds the note, figures, scripts and data, but no vendor
    # datasheets, application notes, SPICE model files or renderings of datasheet pages
    ("replace", "   The first takes about ten minutes here, two of them for the scans",
     "   The first takes about ten minutes, two of them for the scans"),
    ("replace", "Local copies are in `datasheets/`. TI datasheets are at",
     "The datasheets are not part of this note's repository; every one is available from its manufacturer. TI datasheets are at"),
    ("replace",
     "with the copy used; local copies are in `datasheets/integrated_tia/`, the coherent-receiver documents in `datasheets/integrated_tia/coherent/`.",
     "with the revision used; the documents are available from their manufacturers and are not part of this note's repository."),
    ("replace",
     "with the copy used; local copies are in `datasheets/fet_front_end/` and `datasheets/bjt_front_end/`.",
     "with the revision used; the documents are available from their manufacturers and are not part of this note's repository."),
    ("replace", "with the copy used; local copies are in `datasheets/hv_output_stage/`.",
     "with the revision used; the documents are available from their manufacturers and are not part of this note's repository."),
    ("paragraph", "Local copies are in `appnotes/`.",
     "Each entry gives its source; the documents themselves are not part of this note's repository."),
    ("replace", "A local copy of [S1] is in `appnotes/`. The TI model packages", "The TI model packages"),
    ("replace", "*Updated LSBF862 SPICE Model*, Rev 2 (9 February 2026); local copy `datasheets/fet_front_end/LSBF862_LinearSystems_SPICE_Rev2_2026-02-09.pdf`.",
     "*Updated LSBF862 SPICE Model*, Rev 2 (9 February 2026)."),
    ("replace", "| `datasheets/` | datasheets of every part of Chapters 2 and 6;",
     "| `datasheets/` | not part of the public repository (Appendix D gives each document's source): datasheets of every part of Chapters 2 and 6;"),
    ("replace", "| `appnotes/` | the application notes and articles [A1]–[A24], and the ngspice manual [S1] |",
     "| `appnotes/` | not part of the public repository (Appendix D gives each document's source): the application notes and articles [A1]–[A24], and the ngspice manual [S1] |"),
    ("replace", "the vendors' model packages and libraries of Table B.1, downloaded separately;",
     "the vendors' model packages and libraries of Table B.1, downloaded separately and not part of the public repository;"),
    ("replace", "holds the translated model copies (vendor files, not for redistribution) |",
     "holds the translated model copies (vendor files, not part of the public repository) |"),
    ("replace", "and the translated BFP740ESD model (vendor files, not for redistribution) |",
     "and the translated BFP740ESD model (vendor files, not part of the public repository) |"),
    ("replace",
     "| `data/digitization_checks/` | the THS3491 and OPA859 datasheet figures rendered with the readings drawn on them, the residuals against the figures' vector paths, TI's measured Fig 8-1 curves, and a manifest with the SHA-256 of every source (`scripts_archive/overlay_digitized.py`) |",
     "| `data/digitization_checks/` | the residuals of the THS3491 and OPA859 readings against the figures' vector paths, TI's measured Fig 8-1 curves as read from the datasheet, and a manifest with the SHA-256 of every source (`scripts_archive/overlay_digitized.py`, which also draws the readings on the rendered datasheet figures; those renderings are not part of the public repository) |"),
]
