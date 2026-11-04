"""Put the theory before the design examples and add the OPA846 design (4 November 2026).

The note had Chapter 3, a design example (OPA855 at 2 kOhm), before Chapter 4, the theory.  This
script exchanges them: the theory becomes Chapter 3, and Chapter 4 becomes the two design examples,
OPA855 and OPA846 at 2 kOhm, whose text is case_chapter_2026-11-04.md (written in the new numbering)
and whose appendix tables, Tables A4.1-A4.4, are generated from the simulations by
case_studies.py notetables (data/results/case_studies_note_tables.md).

Every reference in the rest of the note is renumbered in one pass, through tokens, so that no number
is mapped twice:
  sections  3.1 -> 4.1, 3.2 -> 4.2, 3.3 -> 4.8, 3.4 -> 4.9; 4.k -> 3.k
  chapters  3 <-> 4 (a list that then holds both is put back in order)
  equations (7)-(10) -> (33)-(36), (11)-(36) -> (7)-(32); the rest unchanged
  tables    3.1 -> 4.1, A4.k -> A3.k
  figures   N >= 3 -> N + 6 (the six new figures of Chapter 4 are 3-8)
Equation numbers of other documents are left alone: inside citation brackets ([A22, Eq. (16), ...]),
after a possessive (TI's Eq. (12), Hobbs' Eq. (8)) and in the reference list (Appendix D).  Code
spans and URLs are never touched.  The targeted rewrites below are anchored on the old text and must
match exactly once; their replacements are written in the new numbering between U+27E6 and U+27E7,
which protects them from the renumbering.

Checks on the result: equation tags 1..N in order; figures 1..N in order of appearance; every cited
section, chapter, appendix section, table, equation and figure exists.  Writes the new note, and
case_studies_reorder.map.txt (old -> new numbers) and case_studies_reorder.refs.txt (every rewritten
reference) next to this script.

Usage: python reorder_case_studies.py <old note.md> <new note.md> <chapter.md> <appendix tables.md>
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LB, RB = "\u27e6", "\u27e7"
PROTECT = re.compile(r"```.*?```|`[^`\n]*`|https?://[^\s)|]+|" + LB + "[^" + RB + "]*" + RB, re.S)
CITATION = re.compile(r"\[[ADS]\d+[^\]\n]*\]")
UNIT = r"(?![\d.]*\s?(?:dB|pF|fF|nF|mA|µA|nA|pA|kΩ|Ω|MHz|GHz|kHz|Hz|V\b|mV|%|ns|ps|µs|°|K\b|mW|W\b))"
SEP = r"(?:–|, and |, | and | or | to )"
LOG = []

SEC_MAP = {"3.1": "4.1", "3.2": "4.2", "3.3": "4.8", "3.4": "4.9"}
SEC_MAP.update({f"4.{k}": f"3.{k}" for k in range(1, 11)})
CH_MAP = {"3": "4", "4": "3"}
TAB_MAP = {"3.1": "4.1"}
TAB_MAP.update({f"A4.{k}": f"A3.{k}" for k in range(1, 8)})


def eq_map(n):
    if 7 <= n <= 10:
        return n + 26
    if 11 <= n <= 36:
        return n - 4
    return n


def fig_map(n):
    return n if n < 3 else n + 6


def lit(s):
    return LB + s + RB


# ------------------------------------------------------------------ targeted rewrites (old text)
PRE = [
    # opening: the order of the chapters
    ("Chapter 3 is a design example: we lay out one promising design, OPA855 at 2 kΩ, with four equations written in "
     "practical units, and Chapter 4 derives those equations and the open-loop model that gives the phase margins.",
     lit("Chapter 3 derives the theory: the feedback loop and its stability with a decompensated amplifier, the "
         "open-loop model that gives the phase margins, the noise and the definitions of dynamic range. Chapter 4 "
         "applies it to two designs, OPA855 and OPA846 at 2 kΩ: it lays each out with four equations written in "
         "practical units and checks it in simulation, with our analytical model and with the vendor's SPICE "
         "macromodel, against the photodiode and feedback capacitances, for large signals and against the benchmark.")),
    # Section 1.5
    ("The SPICE numbers come from the manufacturers' macromodels: Chapter 5 checks the analytical estimates against them,",
     "The SPICE numbers come from the manufacturers' macromodels: " + lit("Chapter 4 sets the two side by side for its "
     "two designs,") + " Chapter 5 checks the analytical estimates against them,"),
    # Section 2.1
    ("Section 3.3 applies these three comparisons to the design example of Chapter 3,",
     lit("Section 4.8 applies these three comparisons to the two design examples of Chapter 4,")),
    # opening of the theory chapter
    ("The design example of Chapter 3 used four equations without proof. This chapter derives them from the circuit of "
     "Figure 1, together with the open-loop model that gives the phase margins and the definitions of dynamic range, and "
     "then checks the model where it can be checked without a simulator.",
     lit("Before any design is laid out, this chapter derives the relations that every design in this note rests on, "
         "from the circuit of Figure 1: the transimpedance, the noise gain and the loop gain, the stability of a "
         "decompensated amplifier, the open-loop model that gives the phase margins, the noise and the definitions of "
         "dynamic range. It then checks the model where it can be checked without a simulator. Chapter 4 applies these "
         "relations to two designs and collects the four that give a first estimate in practical units.")),
    # Section 4.3 (new 3.3)
    ("These are the formulas behind Eq. (9) of Chapter 3 and the starting point of every design in Chapter 6.",
     lit("These are the formulas behind the bandwidth estimate of Eq. (35), with which Chapter 4 lays out its two "
         "designs, and the starting point of every design in Chapter 6.")),
    ("Eq. (18) becomes the form used in Chapter 3:", "Eq. (18) becomes " + lit("the form that Chapter 4 uses (Eq. (35)):")),
    # Section 4.6 (new 3.6)
    ("Eq. (23) becomes Eq. (7) of Chapter 3:", "Eq. (23) becomes " + lit("the form that Chapter 4 collects as Eq. (33):")),
    ("*Example.* For the 2-kΩ OPA855 design at 100 MHz, Section 3.2 finds that an instrument with a 10-dB noise figure "
     "adds 1.44 pA/√Hz,",
     "*Example.* For the 2-kΩ OPA855 design of " + lit("Section 4.2") + " at 100 MHz, an instrument with a 10-dB noise "
     "figure adds 1.44 pA/√Hz,"),
    # Section 4.10 (new 3.10)
    ("the two quantities that the designs of this note can only assume (Table 1.1).",
     "the two quantities that the designs of this note can only assume (Table 1.1)." + lit(" Sections 4.4 and 4.5 lay "
     "out and simulate the design that the same amplifier gives at 2 kΩ on this note's 1-pF photodiode.")),
    # Chapter 5 opening
    ("Before Chapter 6 compares the candidates on those numbers, this chapter tests the model against the manufacturers' "
     "SPICE macromodels in the same circuits.",
     "Before Chapter 6 compares the candidates on those numbers, this chapter tests the model against the manufacturers' "
     "SPICE macromodels in the same circuits." + lit(" Chapter 4 has already set two of these macromodels against our "
     "model, for its OPA855 and OPA846 designs; this chapter explains the methods used there and extends the test to "
     "the leading candidates.")),
    # Appendix A
    ("the values of the design example (Table 3.1)", "the values of the two design examples " + lit("(Table 4.1)")),
    # Appendix B.2: the runs of Chapter 4, after the paragraph on the runs of Chapter 5
    ("The checks can also be run one at a time, in the order of the script's help text.\n4. **Find the results**:",
     "The checks can also be run one at a time, in the order of the script's help text.\n\n"
     + lit("   The two design examples of Chapter 4 have a driver of their own:\n"
           "   ```\n"
           "   python case_studies.py run\n"
           "   python case_studies.py tables\n"
           "   python case_studies.py notetables\n"
           "   python make_case_figures.py\n"
           "   python make_schematics.py ../figures fig32_case_opa855 fig34_case_opa846\n"
           "   ```\n"
           "   `case_studies.py run` takes about four minutes, half of it for the large-signal runs; `--parts` and "
           "`--steps nominal cd cf tone` run parts of it and keep the rest of `spice/results/case_studies.json`. "
           "`tables` writes every result, with the comparisons against the 50-Ω benchmark, to "
           "`data/results/case_studies_tables.md`, and `notetables` writes Tables A4.1–A4.4 as printed here.\n")
     + "4. **Find the results**:"),
    ("   - the translated model copies under `spice/runs/_models/`;",
     "   - the translated model copies under `spice/runs/_models/`;\n"
     + lit("   - the decks of Chapter 4 under `spice/runs/case_<PART>/`, and its results in "
           "`spice/results/case_studies.json`, with the curves in `case_studies_curves.json`;")),
    # Appendix C, item 18
    ("It also draws 4.8 mA of quiescent current against 12.6 mA. Its margins in Chapter 5 are therefore optimistic.",
     "It also draws 4.8 mA of quiescent current against 12.6 mA. Its margins in " + lit("Chapters 4 and 5") + " are "
     "therefore optimistic." + lit(" The 2-kΩ design of Section 4.4 has 44.7° in the model against 34.1° with the "
     "datasheet curve. Above 20 MHz the model also distorts from far below its slew-rate limit, reaching −40 dBc at "
     "0.66 V and −60 dBc at 78 mV at 100 MHz, while the datasheet plots distortion only up to 20 MHz (Section 4.7); "
     "only a measurement can tell whether the part does the same.")),
    # Appendix E
    ("| `figures/` | Figures 1–31 as PNG (600 dpi) and PDF.", lit("| `figures/` | Figures 1–37 as PNG (600 dpi) and PDF.")),
    ("`fig01` and `fig21`–`fig31` are Figure 1 and the schematics of Chapters 7 and 8, Figures 21–31 "
     "(`scripts_archive/make_schematics.py`, in the shared style of `scripts_archive/schematic_style.py`); `fig02`–`fig06` "
     "are Figures 14, 11, 2, 12 and 16 (`scripts_archive/make_figures.py`); `fig07`–`fig16` are Figures 3–9 and 17–19 "
     "(`scripts_archive/make_spice_figures.py`); and `fig17`–`fig20` are Figures 10, 13, 15 and 20 "
     "(`scripts_archive/make_narrative_figures.py`) |",
     lit("`fig01` and `fig21`–`fig31` are Figure 1 and the schematics of Chapters 7 and 8, Figures 27–37 "
         "(`scripts_archive/make_schematics.py`, in the shared style of `scripts_archive/schematic_style.py`); "
         "`fig02`–`fig06` are Figures 20, 17, 2, 18 and 22 (`scripts_archive/make_figures.py`); `fig07`–`fig16` are "
         "Figures 9–15 and 23–25 (`scripts_archive/make_spice_figures.py`); `fig17`–`fig20` are Figures 16, 19, 21 and 26 "
         "(`scripts_archive/make_narrative_figures.py`); and `fig32`–`fig37` are Figures 3–8 of Chapter 4, the two "
         "schematics from `scripts_archive/make_schematics.py` and the simulations from "
         "`scripts_archive/make_case_figures.py` |")),
    ("the 50-Ω benchmark family and the leading designs against it (Sections 2.1 and 6.8; Tables A2.2, A6.35 and A6.36), "
     "from `scripts_archive/benchmark_50ohm.py`, whose `--tables` option prints the table rows |",
     "the 50-Ω benchmark family and the leading designs against it (Sections 2.1 and 6.8; Tables A2.2, A6.35 and A6.36), "
     "from `scripts_archive/benchmark_50ohm.py`, whose `--tables` option prints the table rows |\n"
     + lit("| `data/results/case_studies_tables.md`, `case_studies_note_tables.md` | the two design examples of Chapter 4: "
           "every result, with the comparisons against the 50-Ω benchmark, and Tables A4.1–A4.4 as printed here "
           "(`scripts_archive/case_studies.py`, actions `tables` and `notetables`) |")),
    ("and `dr_comparison.json` with the dynamic-range comparison of Section 6.6 (`scripts_archive/dr_comparison.py`) |",
     "and `dr_comparison.json` with the dynamic-range comparison of Section 6.6 (`scripts_archive/dr_comparison.py`)"
     + lit("; `case_studies.json` and `case_studies_curves.json` hold the simulations of Chapter 4 "
           "(`scripts_archive/case_studies.py`), whose decks it writes under `spice/runs/case_<PART>/`") + " |"),
    ("the 50-Ω benchmark and the charts of Chapter 6 use `benchmark_50ohm.py` and `make_narrative_figures.py` |",
     "the 50-Ω benchmark and the charts of Chapter 6 use `benchmark_50ohm.py` and `make_narrative_figures.py`"
     + lit("; the design examples of Chapter 4 use `case_studies.py` and `make_case_figures.py`") + " |"),
    ("use the section, table and equation numbers of this note before its reorganization of 27 October 2026; "
     "`scripts_archive/rework/TIA_opamp_survey.map.txt` converts every such number to the present one,",
     "use the section, table and equation numbers of this note before its reorganization of 27 October 2026"
     + lit(", and those written before 4 November 2026 the order in which a design example preceded the theory; "
           "`scripts_archive/rework/TIA_opamp_survey.map.txt` and `scripts_archive/rework/case_studies_reorder.map.txt` "
           "convert every such number to the present one,")),
]


def spans(pattern, text):
    return [(m.start(), m.end()) for m in pattern.finditer(text)]


def inside(pos, sp):
    return any(a <= pos < b for a, b in sp)


def sub_skip(pattern, fn, text, skip):
    out, last = [], 0
    for m in pattern.finditer(text):
        if inside(m.start(), skip):
            continue
        rep = fn(m)
        if rep is None:
            continue
        out.append(text[last:m.start()])
        out.append(rep)
        last = m.end()
    out.append(text[last:])
    return "".join(out)


def renumber(text, appendix_d):
    skip = spans(PROTECT, text) + spans(CITATION, text)

    sec_item = r"\d+(?:\.\d+)*" + UNIT + r"(?:\s\([a-e]\))?"
    sec_pat = re.compile(r"\b(Sections?) (" + sec_item + r"(?:" + SEP + sec_item + r")*)")

    def sec_fn(m):
        parts = re.split("(" + SEP + ")", m.group(2))
        changed = False
        for i in range(0, len(parts), 2):
            core, _, sub = parts[i].partition(" (")
            if core in SEC_MAP:
                parts[i] = SEC_MAP[core] + ((" (" + sub) if sub else "")
                changed = True
        if not changed:
            return None
        new = m.group(1) + " " + "".join(parts)
        LOG.append(("S", m.group(0), new))
        return new
    text = sub_skip(sec_pat, sec_fn, text, skip)
    skip = spans(PROTECT, text) + spans(CITATION, text)

    ch_pat = re.compile(r"\b(Chapters?) (\d+" + UNIT + r"(?:" + SEP + r"\d+" + UNIT + r")*)")

    def ch_fn(m):
        parts = re.split("(" + SEP + ")", m.group(2))
        nums = [parts[i] for i in range(0, len(parts), 2)]
        if not any(n in CH_MAP for n in nums):
            return None
        mapped = [CH_MAP.get(n, n) for n in nums]
        if "3" in mapped and "4" in mapped:
            mapped = sorted(mapped, key=int)
        for k, i in enumerate(range(0, len(parts), 2)):
            parts[i] = mapped[k]
        new = m.group(1) + " " + "".join(parts)
        LOG.append(("C", m.group(0), new))
        return new
    text = sub_skip(ch_pat, ch_fn, text, skip)
    skip = spans(PROTECT, text) + spans(CITATION, text)

    eq_pat = re.compile(r"\b(Eqs?\.) (\(\d+\)(?:" + SEP + r"\(\d+\))*)")
    a0 = text.find("## Appendix D. References")
    a1 = text.find("## Appendix E.", a0)
    eq_skip = skip + [(a0, a1)]

    def eq_fn(m):
        before = text_ref[0][max(0, m.start() - 8):m.start()]
        after = text_ref[0][m.end():m.end() + 12]
        if re.search(r"(['’]s?|\bits|\btheir|\bhis|\bher) $", before) or re.match(r"\s*\[[ADS]\d+| in SBOA", after):
            LOG.append(("E-kept", m.group(0), (before + " … " + after).strip()))
            return None
        nums = re.findall(r"\((\d+)\)", m.group(2))
        seps = re.findall(r"\)(" + SEP + r")\(", m.group(2))
        if not any(eq_map(int(n)) != int(n) for n in nums):
            return None
        new = m.group(1) + " " + f"({eq_map(int(nums[0]))})" + "".join(
            s + f"({eq_map(int(n))})" for s, n in zip(seps, nums[1:]))
        for s, a, b in zip(seps, nums, nums[1:]):
            if s == "–" and eq_map(int(b)) - eq_map(int(a)) != int(b) - int(a):
                raise SystemExit(f"equation range broken by the move: {m.group(0)}")
        LOG.append(("E", m.group(0), new))
        return new
    text_ref = [text]
    text = sub_skip(eq_pat, eq_fn, text, eq_skip)
    text = re.sub(r"\\tag\{(\d+)\}", lambda m: "\\tag{" + str(eq_map(int(m.group(1)))) + "}", text)
    skip = spans(PROTECT, text) + spans(CITATION, text)

    tid = r"(?:A\d\.\d+|[A-F]\.\d+|\d+\.\d+[a-z]?)" + UNIT
    tab_pat = re.compile(r"\b(Tables?) (" + tid + r"(?:" + SEP + tid + r")*)")

    def tab_fn(m):
        parts = re.split("(" + SEP + ")", m.group(2))
        changed = False
        for i in range(0, len(parts), 2):
            if parts[i] in TAB_MAP:
                parts[i] = TAB_MAP[parts[i]]
                changed = True
        if not changed:
            return None
        new = m.group(1) + " " + "".join(parts)
        LOG.append(("T", m.group(0), new))
        return new
    text = sub_skip(tab_pat, tab_fn, text, skip)
    skip = spans(PROTECT, text) + spans(CITATION, text)

    fig_pat = re.compile(r"\b(Figures?) (\d+)((?:\([a-f]\)(?:–\([a-f]\))?|[a-f](?:–[a-f])?(?![a-z]))?)"
                         r"((?:" + SEP + r"\d+" + UNIT + r"(?:\([a-f]\)|[a-f](?![a-z]))?)*)")

    def fig_fn(m):
        n0 = int(m.group(2))
        rest = re.sub(r"(" + SEP + r")(\d+)", lambda mm: mm.group(1) + str(fig_map(int(mm.group(2)))), m.group(4))
        new = f"{m.group(1)} {fig_map(n0)}{m.group(3)}{rest}"
        if new == m.group(0):
            return None
        LOG.append(("F", m.group(0), new))
        return new
    text = sub_skip(fig_pat, fig_fn, text, skip)
    return text


def check(text):
    problems = []
    tags = [int(x) for x in re.findall(r"\\tag\{(\d+)\}", text)]
    if tags != list(range(1, len(tags) + 1)):
        problems.append(("equation tags out of order", tags[:40]))
    figs = [int(x) for x in re.findall(r"^!\[Figure (\d+)\]", text, re.M)]
    if figs != list(range(1, len(figs) + 1)):
        problems.append(("figures out of order", figs))
    caps = [int(x) for x in re.findall(r"^\*Figure (\d+)\. ", text, re.M)]
    if caps != figs:
        problems.append(("figure captions differ from images", caps))
    heads = set()
    for m in re.finditer(r"^(#{2,4}) (.+)$", text, re.M):
        t = m.group(2)
        mm = re.match(r"^(\d+)\. ", t)
        if mm:
            heads.add(("Chapter", mm.group(1)))
        mm = re.match(r"^(\d+\.\d+(?:\.\d+)?) ", t)
        if mm:
            heads.add(("Section", mm.group(1)))
        mm = re.match(r"^Appendix ([A-Z])\. ", t)
        if mm:
            heads.add(("Appendix", mm.group(1)))
        mm = re.match(r"^([A-Z]\.?\d+)\.? ", t)
        if mm:
            heads.add(("Appendix", mm.group(1)))
    skip = spans(PROTECT, text) + spans(CITATION, text)
    ref = re.compile(r"\b(Sections?|Chapters?) (\d+(?:\.\d+)*" + UNIT + r"(?:\s\([a-e]\))?(?:" + SEP + r"\d+(?:\.\d+)*"
                     + UNIT + r"(?:\s\([a-e]\))?)*)")
    for m in ref.finditer(text):
        if inside(m.start(), skip):
            continue
        kind = "Section" if m.group(1).startswith("Section") else "Chapter"
        for it in re.split(SEP, m.group(2)):
            it = it.split(" (")[0].strip()
            if (kind, it) not in heads:
                problems.append(("missing " + kind, it, text[max(0, m.start() - 50):m.end() + 10]))
    a0 = text.find("## Appendix D. References")
    a1 = text.find("## Appendix E.", a0)
    for m in re.finditer(r"\bEqs?\. (\(\d+\)(?:" + SEP + r"\(\d+\))*)", text):
        if inside(m.start(), skip + [(a0, a1)]):
            continue
        for x in re.findall(r"\((\d+)\)", m.group(1)):
            if not 1 <= int(x) <= len(tags):
                problems.append(("equation out of range", x, text[max(0, m.start() - 40):m.end()]))
    captions = set(re.findall(r"^\*Table ([A-Z]\d*\.\d+|\d+\.\d+)\. ", text, re.M))
    for m in re.finditer(r"\bTables? ((?:[A-F]\d?\.)?\d+(?:\.\d+)?(?:" + SEP + r"(?:[A-F]\d?\.)?\d+(?:\.\d+)?)*)", text):
        if inside(m.start(), skip):
            continue
        for x in re.split(SEP, m.group(1)):
            if re.fullmatch(r"(?:[A-F]\d?\.)?\d+\.\d+|[A-F]\d?\.\d+", x) and x not in captions:
                problems.append(("missing table", x, text[max(0, m.start() - 40):m.end() + 10]))
    for m in re.finditer(r"\bFigures? (\d+)", text):
        if not inside(m.start(), skip) and not 1 <= int(m.group(1)) <= len(figs):
            problems.append(("figure out of range", m.group(0)))
    return problems, len(tags), len(figs)


def main():
    old_path, new_path, chapter_path, tables_path = map(Path, sys.argv[1:5])
    text = old_path.read_text(encoding="utf-8")
    for a, b in PRE:
        n = text.count(a)
        if n != 1:
            raise SystemExit(f"anchor found {n} times: {a[:90]}")
        text = text.replace(a, b)
    p3 = text.index("\n## 3. A design example")
    p4 = text.index("\n## 4. TIA theory")
    p5 = text.index("\n## 5. SPICE cross-check")
    head, old3, theory, rest = text[:p3 + 1], text[p3 + 1:p4 + 1], text[p4 + 1:p5 + 1], text[p5 + 1:]
    # the old Chapter 3 is replaced as a whole by the new Chapter 4; its separator goes with it
    assert old3.rstrip().endswith("---"), "chapter separator"
    a0 = text.find("## Appendix D. References")
    body = renumber(head + "\x00" + theory + "\x01" + rest, a0)
    head, theory, rest = re.split("[\x00\x01]", body)
    # headings of the theory chapter
    theory = theory.replace("## 4. TIA theory", "## 3. TIA theory", 1)
    theory, n_sec = re.subn(r"^### 4\.(\d+) ", r"### 3.\1 ", theory, flags=re.M)
    assert n_sec == 10, n_sec
    # Appendix A: the theory's tables become A3, the design examples' tables are A4
    assert rest.count("### A4. Tables of Chapter 3: TIA theory") == 1      # its chapter number is already mapped
    rest = rest.replace("### A4. Tables of Chapter 3: TIA theory", "### A3. Tables of Chapter 3: TIA theory")
    i5 = rest.index("### A5. Tables of Chapter 5")
    tables = tables_path.read_text(encoding="utf-8").strip("\n") + "\n\n"
    rest = rest[:i5] + tables + rest[i5:]
    chapter = chapter_path.read_text(encoding="utf-8").strip("\n") + "\n\n---\n\n"
    new = head + theory + chapter + rest
    new = new.replace(LB, "").replace(RB, "")
    problems, n_eq, n_fig = check(new)
    new_path.write_text(new, encoding="utf-8", newline="\n")
    (HERE / "case_studies_reorder.refs.txt").write_text(
        "\n".join(f"{k}\t{a}\t->\t{b}" for k, a, b in LOG) + "\n", encoding="utf-8", newline="\n")
    m = ["sections old->new"] + [f"{k}\t{v}" for k, v in SEC_MAP.items()]
    m += ["chapters old->new", "3\t4", "4\t3", "equations old->new"]
    m += [f"{n}\t{eq_map(n)}" for n in range(7, 37)]
    m += ["tables old->new"] + [f"{k}\t{v}" for k, v in TAB_MAP.items()]
    m += ["figures old->new"] + [f"{n}\t{fig_map(n)}" for n in range(3, 32)]
    m += ["new items", "Section 4.3, 4.4, 4.5, 4.6, 4.7: new", "Figures 3-8: new (fig32-fig37)",
          "Tables A4.1-A4.4: new", "Table 4.1: old Table 3.1 with an OPA846 column"]
    (HERE / "case_studies_reorder.map.txt").write_text("\n".join(m) + "\n", encoding="utf-8", newline="\n")
    print(f"equations {n_eq}, figures {n_fig}, references rewritten {sum(1 for x in LOG if x[0] != 'E-kept')}, "
          f"kept as other documents' {sum(1 for x in LOG if x[0] == 'E-kept')}")
    for p in problems:
        print("PROBLEM", p)
    print("written", new_path)


if __name__ == "__main__":
    main()
