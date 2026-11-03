"""Make the landing page index.html at the root of the repository from README.md, for GitHub Pages.

The page is the README as pandoc renders it (MathML for the formulas), with a screen stylesheet. Its links into the
note folders stay relative, so the page works on the published site and from a local copy alike.

Usage (from the repository): python build/make_landing.py
Environment setting: PANDOC names the program (default: `pandoc` on the PATH).
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
README = REPO / "README.md"
OUT = REPO / "index.html"
PANDOC = os.environ.get("PANDOC", "pandoc")
CSS = """<style>
html { font-family: Arial, "Segoe UI Symbol", "Cambria Math", sans-serif; font-size: 11pt; line-height: 1.45;
  color: #161616; background: #fff; }
body { max-width: 56rem; margin: 0 auto; padding: 1.5rem 1.25rem 4rem; }
h1, h2, h3 { font-family: Arial, sans-serif; color: #1d2f55; line-height: 1.2; }
h1 { font-size: 2.1rem; margin: 1.5rem 0 0.8rem; }
h2 { font-size: 1.5rem; margin-top: 2em; padding-bottom: 0.2em; border-bottom: 1px solid #c8d0e0; }
h3 { font-size: 1.2rem; margin-top: 1.6em; }
a { color: #1a4f9c; text-decoration: none; }
a:hover, a:focus { text-decoration: underline; }
code { font-family: Consolas, "Courier New", monospace; font-size: 0.92em; overflow-wrap: anywhere; }
pre { background: #f4f6f9; padding: 0.6em 0.8em; overflow-x: auto; font-size: 0.9em; }
table { border-collapse: collapse; width: 100%; font-size: 0.93em; margin: 0.8em 0 1.1em; }
th, td { border: 1px solid #b9bfca; padding: 0.3em 0.5em; vertical-align: top; text-align: left; }
th { background: #e9edf5; }
math { font-family: "Cambria Math", "STIX Two Math", math; }
</style>
"""

title = next(ln[2:].strip() for ln in README.read_text(encoding="utf-8").split("\n") if ln.startswith("# "))
with tempfile.TemporaryDirectory() as tmp:
    header = Path(tmp) / "style.html"
    header.write_text(CSS, encoding="utf-8")
    cmd = [PANDOC, str(README), "-f", "markdown-implicit_figures+autolink_bare_uris", "-t", "html5",
           "--standalone", "--mathml", "--columns=100000", "-M", "document-css=false",
           "-M", f"pagetitle={title}", "-M", "lang=en", f"--include-in-header={header}", "-o", str(OUT)]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", cwd=str(REPO))
print(r.stderr[:2000])
if r.returncode != 0:
    sys.exit(1)
html = OUT.read_text(encoding="utf-8")
OUT.write_text(html, encoding="utf-8", newline="\n")
print(f"{OUT.name} {OUT.stat().st_size / 1e3:.0f} kB")
