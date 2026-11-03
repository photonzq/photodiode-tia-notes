"""Turn the print HTML that build/build_pdf.py keeps (KEEP_HTML=1) into the web page index.html of a note's folder,
for GitHub Pages.

- Figures: the print HTML embeds every PNG as a data URI; each is matched by content to its file in the note's
  figures/ and replaced by a relative link, so the page loads its images separately.
- Links to the other note: build/build_pdf.py points them at the other note's PDF and keeps the address of that
  note's web page, relative to this one, in data-web-href; the web page links to the web page.
- Screen layout: a screen-only stylesheet (centred column, larger type, scrollable wide tables) is added; the print
  styles are left as they are, so printing the page still follows the PDF layout.
- A floating "Contents" link returns to the table of contents; it appears once the reader has scrolled past the
  contents and is hidden when printing.
- A link to the PDF version is placed under the notice on the title block.

Usage (from the repository, after `KEEP_HTML=1 python build/build_pdf.py <folder>/<note>.md`):
    python build/make_web_html.py <folder>/<note>.md [--remove-print-html]
"""
import base64
import hashlib
import re
import sys
from pathlib import Path

args = [a for a in sys.argv[1:] if not a.startswith("--")]
if len(args) != 1:
    sys.exit(__doc__)
MD = Path(args[0]).resolve()
SRC = MD.with_suffix(".html")
OUT = MD.parent / "index.html"
FIGS = MD.parent / "figures"
PDF_NAME = MD.with_suffix(".pdf").name

SCREEN_CSS = """
<style>
@media screen {
  html { font-size: 11pt; }
  body { max-width: 64rem; margin: 0 auto; padding: 1.5rem 1.25rem 4rem; }
  h1.doc-title { margin-top: 1.5rem; font-size: 2.4rem; }
  p.doc-subtitle { margin-bottom: 1.2rem; font-size: 1.3rem; }
  h1, h2 { font-size: 2rem; margin-top: 2.4em; }
  h3 { font-size: 1.5rem; margin-top: 1.8em; }
  h4 { font-size: 1.25rem; margin-top: 1.5em; }
  h5 { font-size: 1.1rem; margin-top: 1.2em; }
  table { font-size: 9pt; }
  table.wide { font-size: 8.4pt; }
  .table-scroll { overflow-x: auto; }
  nav#TOC { font-size: 10pt; }
  nav#TOC h1 { font-size: 1.8rem; }
  p.pdf-link { margin: 0.8em 0 1.6em; }
  a.to-contents { position: fixed; right: 1.2rem; bottom: 1.2rem; z-index: 10; padding: 0.4em 0.9em;
    border-radius: 1.2em; background: #1d2f55; color: #fff; font-size: 0.95rem; opacity: 0.85;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.3); }
  a.to-contents:hover, a.to-contents:focus { opacity: 1; }
}
@media print {
  a.to-contents { display: none; }
}
</style>
"""

BACK_LINK = """
<a class="to-contents" href="#TOC" title="Back to the table of contents">&#8593; Contents</a>
<script>
(function () {
  var link = document.querySelector("a.to-contents"), toc = document.getElementById("TOC");
  if (!link || !toc) return;
  function update() { link.style.visibility = toc.getBoundingClientRect().bottom < 0 ? "visible" : "hidden"; }
  window.addEventListener("scroll", update, { passive: true });
  update();
})();
</script>
"""

html = SRC.read_text(encoding="utf-8")
by_hash = {hashlib.sha256(p.read_bytes()).hexdigest(): p.name for p in FIGS.glob("*.png")}
unmatched = []


def swap(m):
    data = base64.b64decode(m.group(2))
    name = by_hash.get(hashlib.sha256(data).hexdigest())
    if name is None:
        unmatched.append(len(data))
        return m.group(0)
    return f'src="{FIGS.name}/{name}"'


def web_link(m):
    """An <a> tag that points at the other note's PDF, turned to point at its web page."""
    tag = m.group(0)
    web = re.search(r'\sdata-web-href="([^"]*)"', tag).group(1)
    tag = re.sub(r'\sdata-web-href="[^"]*"', "", tag)
    return re.sub(r'\shref="[^"]*"', f' href="{web}"', tag, count=1)


html, n_img = re.subn(r'src="data:(image/png);base64,([^"]+)"', swap, html)
assert not unmatched, f"{len(unmatched)} embedded images match no figure file"
html, n_note = re.subn(r'<a\b[^>]*\sdata-web-href="[^"]*"[^>]*>', web_link, html)
html = html.replace("</head>", SCREEN_CSS + "</head>", 1)
html = re.sub(r"(<table\b[^>]*>.*?</table>)", r'<div class="table-scroll">\1</div>', html, flags=re.S)
m = re.search(r'<blockquote class="disclaimer">.*?</blockquote>', html, re.S)
assert m, "no notice block found"
link = f'\n<p class="pdf-link"><a href="{PDF_NAME}">PDF version</a></p>'
html = html[:m.end()] + link + html[m.end():]
assert 'id="TOC"' in html, "no table of contents to link back to"
assert html.count("</body>") == 1
html = html.replace("</body>", BACK_LINK + "</body>", 1)
assert "data:image" not in html
OUT.write_text(html, encoding="utf-8", newline="\n")
print(f"{n_img} figures linked, {n_note} links to the other note; {OUT.name} {OUT.stat().st_size / 1e6:.1f} MB")
if "--remove-print-html" in sys.argv:
    SRC.unlink()
    print("removed", SRC.name)
