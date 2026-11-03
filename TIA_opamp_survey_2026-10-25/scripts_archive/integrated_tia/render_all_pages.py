"""Render every page of the PDFs given as arguments to PNG (dpi from env DPI, default 160).
Output: <outdir>/<stem>_p<N>.png, N 1-based. Usage: python render_pdfs.py OUTDIR a.pdf b.pdf ..."""
import os
import sys
from pathlib import Path

import pymupdf

out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
dpi = int(os.environ.get("DPI", "160"))
for p in sys.argv[2:]:
    d = pymupdf.open(p)
    stem = Path(p).stem
    for i in range(d.page_count):
        d[i].get_pixmap(dpi=dpi).save(str(out / f"{stem}_p{i + 1}.png"))
    print(f"{stem}: {d.page_count} pages; metadata title={d.metadata.get('title')!r} date={d.metadata.get('creationDate')!r}")
