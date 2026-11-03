"""Build the PDF of one note, and keep its print HTML for the web page.

Pipeline: Markdown -> HTML with MathML (pandoc) -> PDF (headless Chrome) -> metadata (PyMuPDF).

- Equation numbers: each display equation carries \\tag{N}, where N is a number (12), a number with a letter (26a)
  or an appendix number (B.1). pandoc's MathML writer drops \\tag, so it is swapped for a marker before pandoc and
  turned into a right-aligned "(N)" with an anchor (#eq-N) afterwards.
- Cross-references: "Eq. (N)", "Section 6.2.4", "Chapter 5", "Appendix B.1", "Table A6.5", "Table A.8a" and
  "Figure 12" become internal links when the target exists; "Table A.3", for a group of tables A.3a–e, links to the
  section that holds them. A reference to another document is left as text: one after a possessive ("TI's Eq. (12)
  in SBOA122", "the companion's Section 8.10", "its Appendix B.1", "their Eq. (1)"), after a page number ("p. 3
  Table 1"), inside a citation ("[A22, Appendix A, ...") or after "Cited:" in a bibliography entry.
- Links to the other note: a relative link to a note's Markdown file points, in the PDF, to that note's PDF on the
  published site (SITE_URL). The address of that note's web page, relative to this note, is kept in data-web-href
  for build/make_web_html.py. No other local link is allowed, and the PDF is checked for links to local files.
- Title page: the title, the line under it, the notice (the first block quote), then the contents.
- Source links: bare URLs in the Markdown become links (pandoc's autolink_bare_uris).

Layout: this file lives in <repository>/build and each note in its own folder, <repository>/<folder>/<note>.md; the
PDF is written next to the note under the same name.
Usage: python build/build_pdf.py <folder>/<note>.md
Environment settings: PANDOC and CHROME name the two programs (default: `pandoc` and `chrome` on the PATH);
KEEP_HTML=1 keeps the print HTML next to the PDF, for build/make_web_html.py; SITE_URL replaces the address of the
published site.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
if len(sys.argv) != 2:
    sys.exit(__doc__)
MD = Path(sys.argv[1]).resolve()
NOTE_DIR = MD.parent
assert MD.suffix == ".md" and NOTE_DIR.parent == REPO, f"{MD} is not a note in a folder of the repository"
OUT_PDF = MD.with_suffix(".pdf")
PANDOC = os.environ.get("PANDOC", "pandoc")
CHROME = os.environ.get("CHROME", "chrome")
SITE_URL = os.environ.get("SITE_URL", "https://photonzq.github.io/photodiode-tia-notes/")
KEYWORDS = {
    "TIA_opamp_survey": ("transimpedance amplifier; balanced photodetector; operational amplifier; noise; "
                         "dynamic range; phase margin; SPICE"),
    "TIA_high_gain_survey": ("transimpedance amplifier; photodiode; operational amplifier; electrometer; noise; "
                             "feedback resistor; bandwidth; guarding; SPICE"),
}.get(MD.stem, "")
EQ_MARK = "EQNOMARK"
TAG = r"(?:[A-Z]\.\d+|\d+[a-z]?)"  # an equation number: 12, 26a or B.1
EXTRA_CSS = """
.eqn { display: flex; align-items: center; width: 100%; margin: 0.35em 0; }
.eqn-body { flex: 1 1 auto; text-align: center; }
.eqn-no { flex: 0 0 3.4em; text-align: right; color: #272727; }
a.xref { color: #1a4f9c; text-decoration: none; }
blockquote.disclaimer { margin: 1.4em 0 0.6em; padding: 0.6em 0.9em; border-left: 3px solid #8a94a6;
  background: #f4f6f9; font-size: 0.92em; color: #161616; }
blockquote.disclaimer p { margin: 0; }
"""
T0 = time.time()


def log(*args):
    print(f"[{time.time() - T0:6.0f} s]", *args, flush=True)


WORK = Path(tempfile.mkdtemp(prefix="tiapdf-"))  # short path: Chrome cannot write very long paths
md_copy = WORK / "note.md"
html_raw = WORK / "note_raw.html"
html_final = WORK / "note_print.html"
pdf_tmp = WORK / "note_print.pdf"

src = MD.read_text(encoding="utf-8")
lines = src.split("\n")
TITLE = next(ln[2:].strip() for ln in lines if ln.startswith("# "))
i_title = next(i for i, ln in enumerate(lines) if ln.startswith("# "))
SUBTITLE = next(ln.strip() for ln in lines[i_title + 1:] if ln.strip())
tags = re.findall(r"\\tag\{([^}]*)\}", src)
odd = [t for t in tags if not re.fullmatch(TAG, t)]
assert not odd, f"equation numbers of an unknown form: {odd}"
src = re.sub(r"\\tag\{(" + TAG + r")\}", lambda m: r"\qquad\text{" + EQ_MARK + m.group(1) + "}", src)
md_copy.write_text(src, encoding="utf-8")

cmd = [
    PANDOC, str(md_copy),
    "-f", "markdown-subscript-superscript-implicit_figures-raw_tex+lists_without_preceding_blankline+autolink_bare_uris",
    "-t", "html5", "--standalone", "--mathml",
    "--toc", "--toc-depth=3", "--columns=100000",
    "--embed-resources", f"--resource-path={NOTE_DIR}",
    f"--css={HERE / 'note.css'}",
    "--metadata", f"pagetitle={TITLE}",
    "--metadata", "lang=en",
    "-o", str(html_raw),
]
r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", cwd=str(NOTE_DIR))
log("pandoc rc", r.returncode, "warnings:", r.stderr.count("[WARNING]"))
print(r.stderr[:3000])
if r.returncode != 0:
    sys.exit(1)

soup = BeautifulSoup(html_raw.read_text(encoding="utf-8"), "html.parser")
body = soup.body
log("HTML parsed")

# ---- title page: title, the line under it, the notice, then the contents
first_h1 = body.find("h1")
first_h1["class"] = first_h1.get("class", []) + ["doc-title"]
sub = first_h1.find_next_sibling("p")
sub["class"] = sub.get("class", []) + ["doc-subtitle"]
notice = sub.find_next_sibling()
assert notice is not None and notice.name == "blockquote", "the notice must follow the line under the title"
notice["class"] = notice.get("class", []) + ["disclaimer"]
nav = soup.find("nav", id="TOC")
assert nav is not None, "no table of contents"
nav.extract()
top_ul = nav.find("ul")
first_li = top_ul.find("li", recursive=False)
if first_li is not None and TITLE[:20] in first_li.get_text():  # lift the chapters out of the title's entry
    inner = first_li.find("ul")
    for li in list(inner.find_all("li", recursive=False)) if inner is not None else []:
        first_li.insert_before(li.extract())
    first_li.decompose()
head = soup.new_tag("h1")
head.string = "Contents"
nav.insert(0, head)
notice.insert_after(nav)

for a in body.find_all("a"):
    if a.get_text().strip().startswith(("http://", "https://", "www.")):
        a["class"] = a.get("class", []) + ["url"]
for t in body.find_all("table"):
    ncols = max((len(tr.find_all(["td", "th"], recursive=False)) for tr in t.find_all("tr")), default=0)
    if ncols >= 7:
        t["class"] = t.get("class", []) + ["wide"]

# ---- links to the other note: its PDF on the published site; build/make_web_html.py swaps in its web page
n_note = 0
for a in body.find_all("a", href=True):
    href = a["href"]
    if href.startswith(("#", "http://", "https://", "mailto:")):
        continue
    target = (NOTE_DIR / href.split("#")[0]).resolve()
    assert target.suffix == ".md" and target.parent.parent == REPO and target.is_file(), f"local link: {href}"
    a["href"] = SITE_URL + target.relative_to(REPO).with_suffix(".pdf").as_posix()
    a["data-web-href"] = Path(os.path.relpath(target.parent, NOTE_DIR)).as_posix() + "/"
    n_note += 1
log("links to the other note", n_note)

# ---- equation numbers: marker -> right-aligned "(N)" with anchor eq-N
eq_ids = set()
for mt in list(body.find_all("mtext")):
    m = re.fullmatch(EQ_MARK + "(" + TAG + ")", mt.get_text().strip())
    if not m:
        continue
    num = m.group(1)
    assert num not in eq_ids, f"equation ({num}) is numbered twice"
    math = mt.find_parent("math")
    prev = mt.find_previous_sibling()
    if prev is not None and prev.name == "mspace":
        prev.decompose()
    mt.decompose()
    ann = math.find("annotation")
    if ann is not None:
        ann.string = re.sub(r"\\qquad\\text\{" + EQ_MARK + TAG + r"\}", "", ann.get_text()).rstrip()
    wrap = soup.new_tag("span", attrs={"class": "eqn", "id": f"eq-{num}"})
    inner = soup.new_tag("span", attrs={"class": "eqn-body"})
    no = soup.new_tag("span", attrs={"class": "eqn-no"})
    no.string = f"({num})"
    math.replace_with(wrap)
    inner.append(math)
    wrap.append(inner)
    wrap.append(no)
    eq_ids.add(num)
assert not [mt for mt in body.find_all("mtext") if EQ_MARK in mt.get_text()], "equation markers left in the HTML"
assert len(eq_ids) == len(tags), (len(eq_ids), len(tags))
log("numbered equations", len(eq_ids))

# ---- anchors: chapters, sections, appendices from the headings; tables and figures from their captions
anchors = {}
for h in body.find_all(["h2", "h3", "h4"]):
    hid, t = h.get("id"), h.get_text(" ", strip=True)
    if not hid:
        continue
    m = re.match(r"^(\d+)\.\s", t)
    if m and h.name == "h2":
        anchors[("chapter", m.group(1))] = hid
    m = re.match(r"^Appendix ([A-F])\.", t)
    if m:
        anchors[("appendix", m.group(1))] = hid
    m = re.match(r"^(\d+\.\d+(?:\.\d+)?|[A-F]\.\d+)\s", t)
    if m:
        anchors[("section", m.group(1))] = hid
        if "." in m.group(1) and m.group(1)[0].isalpha():
            anchors[("appendix", m.group(1))] = hid
    m = re.match(r"^([A-F]\d+)\.\s", t)  # "A6. Tables of Chapter 6"
    if m:
        anchors[("appendix", m.group(1))] = hid
for p in body.find_all("p"):
    em = p.find("em", recursive=False)
    if em is None or p.contents[0] is not em:
        continue
    t = em.get_text(" ", strip=True)
    m = re.match(r"^Table ([A-F]?\d*\.?\d+(?:\.\d+)?[a-z]?)\.\s", t)  # Table 4a, 6.6, A6.37, A.8a
    if m:
        p["id"] = f"tab-{m.group(1)}"
        anchors[("table", m.group(1))] = p["id"]
    m = re.match(r"^Figure (\d+)\.\s", t)
    if m:
        p["id"] = f"fig-{m.group(1)}"
        anchors[("figure", m.group(1))] = p["id"]
log("anchors", len(anchors), {k: sum(1 for a in anchors if a[0] == k) for k in
                              ("chapter", "section", "appendix", "table", "figure")})

KIND = {"Section": "section", "Sections": "section", "Chapter": "chapter", "Chapters": "chapter",
        "Appendix": "appendix", "Appendices": "appendix", "Table": "table", "Tables": "table",
        "Figure": "figure", "Figures": "figure"}
# A, A6.5, A.8a, B.1, 6.2.4, 4a; a letter only after a digit, and never the start of a word ("and Figure", "and Eq.")
NUM = r"(?:[A-F](?:\.?\d+(?:\.\d+)*[a-z]?)?|\d+(?:\.\d+)*[a-z]?)(?![A-Za-z])"
SEP = r"(?:,\s*|\s+and\s+|\s+or\s+|–|\s+to\s+)"
EQN = r"\(" + TAG + r"\)"
REF_RE = re.compile(
    r"(?P<eqs>\bEqs?\.\s*" + EQN + r"(?:\s*(?:,|and|–|-|to|or)\s*" + EQN + r")*)"
    r"|\b(?P<kw>Sections?|Chapters?|Appendix|Appendices|Tables?|Figures?)\s+(?P<list>" + NUM + r"(?:" + SEP + NUM + r")*)")
# a reference to another document: after a possessive or "its", after a page number, or inside an open citation
# bracket ("[A22, Appendix A, ..."); pandoc turns ' into ’
EXTERNAL_BEFORE = re.compile(r"(?:\w['’]s?|\b(?:its|their|his|her)|canceller as|\bp\.\s*\d+,?|\[[A-Z]\d+,[^\[\]]*)\s*$")
EXTERNAL_AFTER = re.compile(r"^\s*(?:in SBOA|\[A\d|of the companion|in the companion)")
SKIP = {"a", "math", "code", "pre", "h1", "h2", "h3", "h4", "h5", "nav", "script", "style", "annotation", "title"}
n_ref = n_eqref = n_external = 0
unresolved = set()


def link(href, text):
    a = soup.new_tag("a", href=href, attrs={"class": "xref"})
    a.string = text
    return a


def entry_text_before(s):
    """The text of the bibliography entry ("[A22] ... Cited: ...") that holds the string s, up to s, or None outside
    an entry. After the entry's "Cited:" the references are the cited document's own."""
    for li in s.find_parents("li"):
        if re.match(r"\s*\[[A-Z]\d+\]", li.get_text()):
            before = []
            for t in li.find_all(string=True):
                if t is s:
                    return "".join(before)
                before.append(str(t))
    return None


for s in list(body.find_all(string=True)):
    if not isinstance(s, NavigableString) or not re.search(r"Eq|Section|Chapter|Appendi|Table|Figure", s):
        continue
    if any(p.name in SKIP for p in s.parents if p is not None and p.name):
        continue
    text = str(s)
    pieces, pos = [], 0
    par = s.parent  # a caption's own label ("Table A6.5." at the start of its caption) is not linked
    own = (par is not None and par.name == "em" and par.parent is not None and par.parent.name == "p"
           and par.parent.get("id", "").startswith(("tab-", "fig-")) and par.contents and par.contents[0] is s)
    entry = entry_text_before(s)
    for m in REF_RE.finditer(text):
        if own and m.start() == 0:
            continue
        if (EXTERNAL_BEFORE.search(text[:m.start()]) or EXTERNAL_AFTER.match(text[m.end():])
                or (entry is not None and "Cited:" in entry + text[:m.start()])):
            n_external += 1
            continue
        if m.group("eqs"):
            phrase, start, hits = m.group(0), m.start(), []
            for mm in re.finditer(r"\((" + TAG + r")\)", phrase):
                if mm.group(1) in eq_ids:
                    hits.append((start + mm.start(), start + mm.end(), f"eq-{mm.group(1)}"))
                else:
                    unresolved.add(f"Eq. ({mm.group(1)})")
            n_eqref += len(hits)
        else:
            kind = KIND[m.group("kw")]
            lst, lst_start = m.group("list"), m.start("list")
            hits = []
            for mm in re.finditer(NUM, lst):
                key = mm.group(0)
                if kind == "figure":
                    key = re.sub(r"[a-z]$", "", key)
                tid = anchors.get((kind, key))
                if tid is None and kind == "table":  # "Table A.3" for Tables A.3a–e: the section that holds them
                    tid = anchors.get(("appendix", key))
                if tid:
                    hits.append((lst_start + mm.start(), lst_start + mm.end(), tid))
                else:
                    unresolved.add(f"{kind} {key}")
            n_ref += len(hits)
        for a0, a1, tid in hits:
            pieces.append(text[pos:a0])
            pieces.append(link(f"#{tid}", text[a0:a1]))
            pos = a1
    if not pieces:
        continue
    pieces.append(text[pos:])
    last = None
    for p in pieces:
        node = NavigableString(p) if isinstance(p, str) else p
        if last is None:
            s.replace_with(node)
        else:
            last.insert_after(node)
        last = node
log("links: references", n_ref, "equations", n_eqref, "left as text (other documents)", n_external)
log("references without a target here:", ", ".join(sorted(unresolved)) or "none")

style = soup.new_tag("style")
style.string = EXTRA_CSS
soup.head.append(style)
html_final.write_text(str(soup), encoding="utf-8")
log("html bytes", html_final.stat().st_size)

profile = WORK / "profile"
ccmd = [
    CHROME, "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
    "--disable-extensions", f"--user-data-dir={profile}",
    "--no-pdf-header-footer", "--generate-pdf-document-outline",
    "--run-all-compositor-stages-before-draw", "--virtual-time-budget=60000",
    f"--print-to-pdf={pdf_tmp}", html_final.as_uri(),
]
r = subprocess.run(ccmd, capture_output=True, text=True, timeout=1800)
log("chrome rc", r.returncode, (r.stderr or "")[-800:])
if not pdf_tmp.exists():
    sys.exit(2)

import pymupdf  # noqa: E402

doc = pymupdf.open(pdf_tmp)
uris = [ln.get("uri") for page in doc for ln in page.get_links() if ln.get("uri")]
local = [u for u in uris if not u.startswith(("https://", "http://"))]
assert not local, f"links to local files in the PDF: {local[:3]}"
toc = doc.get_toc(simple=False)
fixed = False
for entry in toc[:2]:  # Chrome drops the space at a line wrap of the title
    if entry[1] != TITLE and entry[1].replace(" ", "") == TITLE.replace(" ", ""):
        entry[1], fixed = TITLE, True
if fixed:
    doc.set_toc(toc)
doc.set_metadata({"title": TITLE, "subject": SUBTITLE, "author": "", "keywords": KEYWORDS,
                  "creator": "", "producer": ""})
doc.del_xml_metadata()
doc.save(OUT_PDF, garbage=2, deflate=True)
if os.environ.get("KEEP_HTML"):
    shutil.copy2(html_final, OUT_PDF.with_suffix(".html"))
log("pages", doc.page_count, "toc entries", len(doc.get_toc()), "web links", len(uris),
    "size MB", round(OUT_PDF.stat().st_size / 1e6, 1))
doc.close()
shutil.rmtree(WORK, ignore_errors=True)
