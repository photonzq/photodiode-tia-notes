"""Engine of the narrative rework of the survey report (27 Oct 2026).

It cuts the report into its blocks (the front matter, every '##' chapter introduction and every
'###' section), puts them into the order of rework_plan.PLAN with the new headings and the new text
that the plan supplies, moves every table except rework_plan.KEEP_INLINE into Appendix A (grouped by
the chapter it now belongs to), and renumbers every reference: sections, equations, tables, figures
and appendices.  References are first turned into tokens that name the OLD item and only then
resolved to the new numbers, so no number is mapped twice.

New text in the plan writes its references in one of two ways:
  - an existing equation, table or figure by its OLD number ("Eq. (25)", "Table 7.4", "Figure 15"),
    which is renumbered like the old text;
  - everything else between U+27E6 and U+27E7 brackets, which the tokenizer does not touch:
      [[Section 2.1]] [[Chapters 5 and 7]] [[Appendix A]]   written in the new numbering, kept as is
      [[E:key]] [[F:key]] [[T:key]]                         a new equation, figure or table
    (the brackets are shown here as [[ ]]).  A new table is written in the plan with the caption
    "*Table Nk. ...*" and is moved into Appendix A like any other.
Replacement strings inside a block (the plan's "replace" option) may use old section numbers, which
are then renumbered with the block.  Equation references inside a citation bracket ([A22, Eq. (16),
p. 918]) and in the reference list point to other documents and are left alone.

Every step checks itself: each old block is used exactly once, each table placed once, every token
resolved, the equation tags numbered 1..N in order, ranges stay ranges, and every section, chapter,
appendix, equation, table and figure that the finished text cites exists.  The rewritten references
are listed in <out>.refs.txt for review, and the old-to-new numbers in <out>.map.txt.

Usage: python rework_narrative.py <old report.md> <new report.md> [<folder for the .map and .refs logs>]
"""
import re
import sys
from pathlib import Path

import rework_plan as P

LB, RB = "\u27e6", "\u27e7"            # literal / new-item markers in the plan's text
TL, TR = "\u27ea", "\u27eb"            # internal tokens for old references
LOG = []                               # (kind, original, resolved) of every rewritten reference
OLD_SEQ, NEW_SEQ = [], []              # section ids in old and in new document order


def read(path):
    with open(path, encoding="utf-8", newline="") as fh:
        return fh.read()


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


# ------------------------------------------------------------------ parsing
def parse(text):
    """Blocks keyed by old id: 'front', 'ch<N>' (chapter intro), '<N>.<M>' (section),
    'app<N>' and 'app2:<name>'.  Each block is (heading line, body lines)."""
    lines = text.split("\n")
    first = next(i for i, l in enumerate(lines) if l.startswith("## "))
    blocks = {"front": ("", lines[:first])}
    order = ["front"]
    key, ctx = None, None
    for l in lines[first:]:
        m_ch = re.match(r"^## (\d+)\. ", l)
        m_app = re.match(r"^## Appendix (\d)\. ", l)
        m_sec = re.match(r"^### (\d+\.\d+) ", l)
        if m_ch:
            key = ctx = f"ch{m_ch.group(1)}"
        elif m_app:
            key = ctx = f"app{m_app.group(1)}"
        elif m_sec:
            key = m_sec.group(1)
        elif l.startswith("### ") and ctx == "app2":
            key = "app2:" + l[4:].split(" (")[0].strip().lower().replace(" ", "_")
        else:
            blocks[key][1].append(l)
            continue
        assert key not in blocks, key
        blocks[key] = (l, [])
        order.append(key)
    for k in order:                                    # strip separators and blank edges
        h, body = blocks[k]
        while body and body[-1].strip() in ("", "---"):
            body.pop()
        while body and body[0].strip() == "":
            body.pop(0)
        blocks[k] = (h, body)
    return blocks, order


TABLE_STAR = re.compile(r"^\*Table ([0-9A-Z][0-9A-Za-z.]*?)\. ")
TABLE_H4 = re.compile(r"^#### Table ([0-9][0-9a-z]*)\. (.*)$")


def split_tables(body, keep):
    """Remove the table units from a body; return (body, [(id, unit lines)])."""
    out, moved = [], []
    i = 0
    while i < len(body):
        l = body[i]
        m = TABLE_STAR.match(l) or TABLE_H4.match(l)
        if not m:
            out.append(l)
            i += 1
            continue
        tid = m.group(1)
        j = i + 1
        while j < len(body) and not body[j].startswith("|"):
            assert l.startswith("####") or body[j].strip() == "", (tid, body[j][:60])
            j += 1
        k = j
        while k < len(body) and body[k].startswith("|"):
            k += 1
        unit = body[i:k]
        if tid in keep:
            out.extend(unit)
        else:
            moved.append((tid, unit))
            while out and out[-1].strip() == "":          # no double blank lines where it was
                out.pop()
            out.append("")
            while k < len(body) and body[k].strip() == "":
                k += 1
        i = k
    while out and out[-1].strip() == "":
        out.pop()
    return out, moved


def caption_to_star(unit, new_id_token):
    """The caption line of a table unit with its id replaced by a token (#### captions become
    italic caption lines)."""
    l = unit[0]
    m = TABLE_H4.match(l)
    if m:
        rest = m.group(2).rstrip()
        if not rest.endswith("."):
            rest += "."
        return [f"*Table {new_id_token}. {rest}*"] + unit[1:]
    m = TABLE_STAR.match(l)
    return [f"*Table {new_id_token}. " + l[m.end():]] + unit[1:]


UNBRACKETED_REF = re.compile(r"\b(Sections?|Chapters?|Appendix|Appendices) [\dA-F]")


def assemble(blocks, order):
    used, seen_tables, appendix_tables, out = set(), set(), [], []
    state = {"chapter": None, "front_done": False}

    def note_chapter(first_line):
        m = re.match(r"^## (\d+)\. ", first_line)
        if m:
            state["chapter"] = m.group(1)
        m = re.match(r"^## Appendix ([A-Z])\. ", first_line)
        if m:
            state["chapter"] = "app" + m.group(1)

    def emit(lines):
        if lines and lines[0].startswith("## ") and state["front_done"] and out and out[-1] != "---":
            out.append("---")
        ch = state["chapter"]
        if ch is not None and not ch.startswith("app"):
            lines, moved = split_tables(lines, P.KEEP_INLINE)
            for tid, unit in moved:
                assert tid not in seen_tables, tid
                seen_tables.add(tid)
                appendix_tables.append((ch, tid, unit))
        while lines and lines[0].strip() == "":
            lines = lines[1:]
        if lines:
            out.append("\n".join(lines))

    for item in P.PLAN:
        kind = item[0]
        if kind == "text":
            text = item[1].strip("\n")
            prose = "\n".join(l for l in text.split("\n") if not l.startswith("#"))
            bad = UNBRACKETED_REF.findall(re.sub(LB + "[^" + RB + "]*" + RB, "", prose))
            assert not bad, ("unbracketed reference in new text", bad, text[:80])
            lines = text.split("\n")
            note_chapter(lines[0])
            emit(lines)
            if lines[0].startswith("# "):
                state["front_done"] = True
            continue
        assert kind == "block", item
        key, heading, opts = item[1], item[2], (item[3] if len(item) > 3 else {})
        h, body = blocks[key]
        body = list(body)
        if "range" in opts:                              # part of a block between two line prefixes
            a, b = opts["range"]
            ia = 0 if a is None else next(i for i, l in enumerate(body) if l.startswith(a))
            ib = len(body) if b is None else next(i for i, l in enumerate(body) if l.startswith(b))
            body = body[ia:ib]
            while body and body[-1].strip() == "":
                body.pop()
            tag = (key, a, b)
        else:
            tag = key
        assert tag not in used, tag
        used.add(tag)
        text = "\n".join(body)
        for old, new in opts.get("replace", []):
            n = text.count(old)
            assert n == 1, (key, old[:70], n)
            text = text.replace(old, new)
        body = text.split("\n")
        if heading:
            note_chapter(heading)
        emit(([heading, ""] if heading else []) + body)
    keys_used = {t if isinstance(t, str) else t[0] for t in used}
    missing = [k for k in order if k not in keys_used and k not in P.DROP]
    assert not missing, ("blocks not placed", missing)
    extra = [k for k in P.DROP if k in keys_used]
    assert not extra, ("dropped blocks used", extra)
    return "\n\n".join(out) + "\n", appendix_tables


def appendix_a(appendix_tables):
    """Appendix A: the moved tables by chapter, with their caption ids as tokens."""
    parts = []
    by_ch = {}
    for ch, tid, unit in appendix_tables:
        by_ch.setdefault(ch, []).append((tid, unit))
    for ch in sorted(by_ch, key=int):
        parts.append(f"### A{ch}. Tables of Chapter {ch}: {P.CHAPTER_TITLES[ch]}")
        for tid, unit in by_ch[ch]:
            parts.append("\n".join(caption_to_star(unit, f"{TL}T:{tid}{TR}")))
    return "\n\n".join(parts)


# ------------------------------------------------------------------ references
PROTECT = re.compile(r"```.*?```|`[^`\n]*`|https?://[^\s)|]+|" + LB + "[^" + RB + "]*" + RB, re.S)
CITATION = re.compile(r"\[[ADS]\d+[^\]\n]*\]")
UNIT = r"(?![\d.]*\s?(?:dB|pF|fF|nF|mA|µA|nA|pA|kΩ|Ω|MHz|GHz|kHz|Hz|V\b|mV|%|ns|ps|µs|°|K\b|mW|W\b))"
SEC_ITEM = r"\d+(?:\.\d+)*" + UNIT + r"(?:\s\([a-e]\))?"
SEP = r"(?:–|, and |, | and | or | to )"


def spans_of(pattern, text):
    return [(m.start(), m.end()) for m in pattern.finditer(text)]


def inside(pos, spans):
    return any(a <= pos < b for a, b in spans)


def split_list(s):
    toks = re.split(f"({SEP})", s)
    return toks[0::2], toks[1::2]


def tokenize(text, old_sections, old_tables, old_figs, n_eq_old):
    partial = []

    def sub_iter(pattern, fn, s, extra_skip=()):
        spans = spans_of(PROTECT, s)
        res, last = [], 0
        for m in pattern.finditer(s):
            if inside(m.start(), spans) or inside(m.start(), extra_skip):
                continue
            rep = fn(m)
            if rep is None:
                continue
            res.append(s[last:m.start()])
            res.append(rep)
            last = m.end()
        res.append(s[last:])
        return "".join(res)

    def keep_prefix(items, seps, valid, core=lambda x: x):
        keep, rest = [], ""
        for i, it in enumerate(items):
            if core(it) not in valid:
                rest = (seps[i - 1] if i else "") + it + "".join(s + x for s, x in zip(seps[i:], items[i + 1:]))
                break
            keep.append((seps[i - 1] if i else "", it))
        return keep, rest

    sec_pat = re.compile(r"\b(Sections?) (" + SEC_ITEM + r"(?:" + SEP + SEC_ITEM + r")*)")

    def sec_fn(m):
        items, seps = split_list(m.group(2))
        keep, rest = keep_prefix(items, seps, old_sections, lambda x: x.split(" (")[0])
        if not keep:
            return None
        if rest:
            partial.append(m.group(0))
        return f"{TL}S:{m.group(1)}:" + "|".join(sep + it for sep, it in keep) + f"#{m.group(0)}{TR}" + rest

    text = sub_iter(sec_pat, sec_fn, text)
    eq_pat = re.compile(r"\b(Eqs?\.) (\(\d+\)(?:" + SEP + r"\(\d+\))*)")

    def eq_fn(m):
        nums = re.findall(r"\((\d+)\)", m.group(2))
        if any(not (1 <= int(n) <= n_eq_old) for n in nums):
            return None
        seps = re.findall(r"\)(" + SEP + r")\(", m.group(2))
        tok = nums[0] + "".join(s + n for s, n in zip(seps, nums[1:]))
        return f"{TL}E:{m.group(1)}:{tok}#{m.group(0)}{TR}"

    text = sub_iter(eq_pat, eq_fn, text, list(P.skip_eq_spans(text)) + spans_of(CITATION, text))
    text = re.sub(r"\\tag\{(\d+)\}", lambda m: f"\\tag{{{TL}EQTAG:{m.group(1)}{TR}}}", text)
    tid = r"(?:A\d\.\d|\d+\.\d+[a-z]?|\d[a-f])" + UNIT
    tab_pat = re.compile(r"\b(Tables?) (" + tid + r"(?:" + SEP + tid + r")*)")

    def tab_fn(m):
        items, seps = split_list(m.group(2))
        keep, rest = keep_prefix(items, seps, old_tables)
        if not keep:
            return None
        if rest:
            partial.append(m.group(0))
        return f"{TL}T:{m.group(1)}:" + "|".join(sep + it for sep, it in keep) + f"#{m.group(0)}{TR}" + rest

    text = sub_iter(tab_pat, tab_fn, text)
    fig_pat = re.compile(r"\b(Figures?) (\d+)((?:\([a-d]\)(?:–\([a-d]\))?|[a-d](?![a-z]))?)"
                         r"((?:" + SEP + r"\d+" + UNIT + r"(?:\([a-d]\)|[a-d](?![a-z]))?)*)")

    def fig_fn(m):
        nums = [m.group(2)] + re.findall(r"(?:" + SEP + r")(\d+)", m.group(4))
        if any(n not in old_figs for n in nums):
            return None
        return f"{TL}F:{m.group(1)}:{m.group(2)}{m.group(3)}{m.group(4)}#{m.group(0)}{TR}"

    text = sub_iter(fig_pat, fig_fn, text)
    text = sub_iter(re.compile(r"\bAppendix ([1-4])\b"), lambda m: f"{TL}APP:{m.group(1)}#{m.group(0)}{TR}", text)
    return text, partial


def resolve(text):
    eq_new, n = {}, 0
    for m in re.finditer(r"\\tag\{(?:" + TL + r"EQTAG:(\d+)" + TR + "|" + LB + r"E:([\w-]+)" + RB + r")\}", text):
        n += 1
        k = m.group(1) or ("new:" + m.group(2))
        assert k not in eq_new, k
        eq_new[k] = n
    fig_new, nf = {}, 0
    for m in re.finditer(r"^!\[(?:" + TL + r"F:Figures?:(\d+)#[^" + TR + "]*" + TR + "|Figure " + LB + r"F:([\w-]+)" + RB
                         + r")\]", text, re.M):
        nf += 1
        k = m.group(1) or ("new:" + m.group(2))
        assert k not in fig_new, k
        fig_new[k] = nf
    tab_new = dict(P.KEEP_INLINE)
    tab_new.update(P.FIXED_TABLES)
    counters, ch = {}, None
    for m in re.finditer(r"^### A(\d+)\. |^\*Table " + TL + r"T:([^" + TR + "]+)" + TR, text, re.M):
        if m.group(1):
            ch = m.group(1)
            continue
        counters[ch] = counters.get(ch, 0) + 1
        tab_new[m.group(2)] = f"A{ch}.{counters[ch]}"
    sec = P.SECTION_MAP

    def sec_render(word, body):
        rendered = []
        for p in body.split("|"):
            m = re.match(r"^(" + SEP + r")?(.*)$", p)
            sep, it = m.group(1) or "", m.group(2)
            core, sub = (it.split(" (", 1) + [""])[:2]
            sub = (" (" + sub) if sub else ""
            kind, nid = sec[core]
            rendered.append((sep, kind, nid + sub, core))
        kinds = {k for _, k, _, _ in rendered}
        if len(kinds) == 1:
            kind = kinds.pop()
            w = kind + ("s" if len(rendered) > 1 else "")
            if kind == "Appendix" and len(rendered) > 1:
                w = "Appendices"
            out = w + " " + "".join(sep + nid for sep, _, nid, _ in rendered)
        else:
            out = "".join(sep + kind + " " + nid for sep, kind, nid, _ in rendered)
        for a, b in zip(rendered, rendered[1:]):
            if b[0] == "–":
                oa, ob = a[3], b[3]
                na, nb = sec[oa][1], sec[ob][1]
                d_old = OLD_SEQ.index(ob) - OLD_SEQ.index(oa)
                d_new = (NEW_SEQ.index(nb) - NEW_SEQ.index(na)) if na in NEW_SEQ and nb in NEW_SEQ else None
                if d_old != d_new:
                    LOG.append(("RANGE?", f"Sections {oa}–{ob}", out))
        return out

    def table_render(word, body):
        rendered = []
        for p in body.split("|"):
            m = re.match(r"^(" + SEP + r")?(.*)$", p)
            rendered.append((m.group(1) or "", tab_new[m.group(2)], m.group(2)))
        for a, b in zip(rendered, rendered[1:]):
            if b[0] == "–":
                pa, pb = re.match(r"^(.*\.)(\d+)$", a[1]), re.match(r"^(.*\.)(\d+)$", b[1])
                if not (pa and pb and pa.group(1) == pb.group(1) and int(pb.group(2)) > int(pa.group(2))):
                    LOG.append(("RANGE?", f"Tables {a[2]}–{b[2]}", f"{a[1]}–{b[1]}"))
        return word + " " + "".join(sep + nid for sep, nid, _ in rendered)

    def eq_render(word, body):
        toks = re.split("(" + SEP + ")", body)
        res = word + " "
        for k, t in enumerate(toks):
            res += t if k % 2 else f"({eq_new[t]})"
        for k in range(1, len(toks), 2):
            if toks[k] == "–":
                a, b = int(toks[k - 1]), int(toks[k + 1])
                if eq_new[str(b)] - eq_new[str(a)] != b - a:
                    LOG.append(("RANGE?", f"Eqs. ({a})–({b})", res))
        return res

    def fig_render(word, body):
        m = re.match(r"^(\d+)((?:\([a-d]\)(?:–\([a-d]\))?|[a-d])?)(.*)$", body)
        res = f"{word} {fig_new[m.group(1)]}{m.group(2)}"
        last = int(m.group(1))
        for mm in re.finditer(r"(" + SEP + r")(\d+)(\([a-d]\)|[a-d])?", m.group(3)):
            res += mm.group(1) + str(fig_new[mm.group(2)]) + (mm.group(3) or "")
            if mm.group(1) == "–" and fig_new[mm.group(2)] - fig_new[str(last)] != int(mm.group(2)) - last:
                LOG.append(("RANGE?", f"Figures {last}–{mm.group(2)}", res))
            last = int(mm.group(2))
        return res

    def tok(m):
        kind, rest = m.group(1), m.group(2)
        orig = ""
        if "#" in rest:
            rest, orig = rest.split("#", 1)
        if kind == "EQTAG":
            return str(eq_new[rest])
        if kind == "T" and ":" not in rest:
            return tab_new[rest]
        if kind == "APP":
            new = "Appendix " + P.APPENDIX_MAP[rest]
        else:
            word, body = rest.split(":", 1)
            new = {"S": sec_render, "E": eq_render, "T": table_render, "F": fig_render}[kind](word, body)
        LOG.append((kind, orig, new))
        return new

    text = re.sub(TL + r"([A-Z]+):([^" + TR + "]+)" + TR, tok, text)

    def lit(m):
        body = m.group(1)
        if body.startswith("E:"):
            return str(eq_new["new:" + body[2:]])
        if body.startswith("F:"):
            return str(fig_new["new:" + body[2:]])
        if body.startswith("T:"):
            return tab_new.get("new:" + body[2:]) or tab_new[body[2:]]
        return body

    text = re.sub(LB + r"([^" + RB + "]+)" + RB, lit, text)
    return text, eq_new, fig_new, tab_new


# ------------------------------------------------------------------ checks on the finished text
def check_output(text, n_eq, n_fig):
    problems = []
    skip = spans_of(PROTECT, text) + spans_of(CITATION, text)
    skip_eq = skip + list(P.skip_eq_spans(text))
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
    ref = re.compile(r"\b(Sections?|Chapters?|Appendix|Appendices) ((?:[A-F](?:\.(?=\d))?)?\d*(?:\.\d+)*" + UNIT
                     + r"(?:\s\([a-e]\))?(?:" + SEP + r"(?:[A-F](?:\.(?=\d))?)?\d+(?:\.\d+)*" + UNIT
                     + r"(?:\s\([a-e]\))?)*)")
    for m in ref.finditer(text):
        if inside(m.start(), skip):
            continue
        kind = {"Sections": "Section", "Chapters": "Chapter", "Appendices": "Appendix"}.get(m.group(1), m.group(1))
        for it in re.split(SEP, m.group(2)):
            it = it.split(" (")[0].strip()
            if not it:
                problems.append(("empty reference", text[max(0, m.start() - 40):m.end() + 20]))
            elif (kind, it) not in heads:
                problems.append(("missing " + kind, it, text[max(0, m.start() - 50):m.end() + 10]))
    for m in re.finditer(r"\bEqs?\. (\(\d+\)(?:" + SEP + r"\(\d+\))*)", text):
        if inside(m.start(), skip_eq):
            continue
        for x in re.findall(r"\((\d+)\)", m.group(1)):
            if not 1 <= int(x) <= n_eq:
                problems.append(("equation out of range", x))
    captions = set(re.findall(r"^\*Table ([A-Z]\d*\.\d+|\d+\.\d+)\. ", text, re.M))
    for m in re.finditer(r"\bTables? ((?:[A-F]\d?\.)?\d+(?:\.\d+)?(?:" + SEP + r"(?:[A-F]\d?\.)?\d+(?:\.\d+)?)*)", text):
        if inside(m.start(), skip):
            continue
        for x in re.split(SEP, m.group(1)):
            if re.fullmatch(r"(?:[A-F]\d?\.)?\d+\.\d+|[A-F]\d?\.\d+", x) and x not in captions:
                problems.append(("missing table", x, text[max(0, m.start() - 40):m.end() + 10]))
    quoted = spans_of(re.compile(r'"[^"\n]*"'), text)            # quotations from datasheets
    for m in re.finditer(r"\bFigures? (\d+)", text):
        if not inside(m.start(), skip + quoted) and not 1 <= int(m.group(1)) <= n_fig:
            problems.append(("figure out of range", m.group(0)))
    for m in re.finditer(r"survey", text, re.I):
        ctx = text[max(0, m.start() - 30):m.end() + 30]
        if not re.search(r"surveyed|TIA_opamp_survey|amplifier survey", ctx):
            problems.append(("survey wording", ctx))
    return problems


def main():
    old_text = read(sys.argv[1])
    blocks, order = parse(old_text)
    OLD_SEQ.extend(k for k in order if re.fullmatch(r"\d+\.\d+", k))
    old_tables = set(re.findall(r"^\*Table ([0-9A-Z][0-9A-Za-z.]*?)\. ", old_text, re.M)) | set(
        re.findall(r"^#### Table ([0-9][0-9a-z]*)\. ", old_text, re.M))
    old_figs = set(re.findall(r"^!\[Figure (\d+)\]", old_text, re.M))
    n_eq_old = len(re.findall(r"\\tag\{\d+\}", old_text))
    body, app_tables = assemble(blocks, order)
    assert body.count(P.APPENDIX_A_MARKER) == 1
    body = body.replace(P.APPENDIX_A_MARKER, appendix_a(app_tables))
    NEW_SEQ.extend(re.findall(r"^#{3,4} ([A-Z]?\d*\.\d+(?:\.\d+)?) ", body, re.M))
    voice_counts = []
    for pat, rep in P.VOICE:
        body, n = re.subn(pat, rep, body)
        voice_counts.append((pat, n))
    body, partial = tokenize(body, set(P.SECTION_MAP), old_tables, old_figs, n_eq_old)
    body, eq_new, fig_new, tab_new = resolve(body)
    left = re.findall("[" + TL + TR + LB + RB + "]", body)
    assert not left, ("unresolved tokens", len(left))
    tags = [int(x) for x in re.findall(r"\\tag\{(\d+)\}", body)]
    assert tags == list(range(1, len(tags) + 1)), "equation tags out of order"
    for k, v in P.EXPECTED_FIGS.items():
        assert fig_new[k] == v, ("figure order", k, fig_new[k], v)
    problems = check_output(body, len(tags), len(fig_new))
    write(sys.argv[2], body)
    out = Path(sys.argv[2])
    if len(sys.argv) > 3:
        out = Path(sys.argv[3]) / out.name
    out.with_suffix(".map.txt").write_text(
        "equations old->new\n" + "\n".join(f"{k}\t{v}" for k, v in eq_new.items())
        + "\n\nfigures old->new\n" + "\n".join(f"{k}\t{v}" for k, v in fig_new.items())
        + "\n\ntables old->new\n" + "\n".join(f"{k}\t{v}" for k, v in tab_new.items())
        + "\n\nsections old->new\n" + "\n".join(f"{k}\t{v[0]} {v[1]}" for k, v in P.SECTION_MAP.items()) + "\n",
        encoding="utf-8")
    uniq = {}
    for kind, orig, new in LOG:
        uniq[(kind, orig, new)] = uniq.get((kind, orig, new), 0) + 1
    out.with_suffix(".refs.txt").write_text(
        "voice rules (count, pattern)\n" + "\n".join(f"{n}\t{p}" for p, n in voice_counts)
        + "\n\npartial reference lists (left part renumbered, rest kept)\n" + "\n".join(partial)
        + "\n\nproblems\n" + "\n".join(repr(p) for p in problems)
        + "\n\nrewritten references (kind, original, new, count)\n"
        + "\n".join(f"{k}\t{o}\t{n}\t{c}" for (k, o, n), c in sorted(uniq.items())) + "\n", encoding="utf-8")
    ranges = [x for x in LOG if x[0] == "RANGE?"]
    print(f"written {len(body.splitlines())} lines; {len(tags)} equations, {len(fig_new)} figures, "
          f"{sum(1 for v in tab_new.values() if v.startswith('A'))} appendix-A tables; "
          f"{len(problems)} problems, {len(ranges)} range warnings, {len(partial)} partial lists")
    for p in problems[:80]:
        print("  PROBLEM", p)
    for r in ranges:
        print("  RANGE", r)
    for p in partial:
        print("  PARTIAL", p)


if __name__ == "__main__":
    main()
