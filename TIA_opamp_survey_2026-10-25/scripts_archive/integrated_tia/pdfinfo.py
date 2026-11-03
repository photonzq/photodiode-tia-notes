import sys
import pymupdf

for p in sys.argv[1:]:
    d = pymupdf.open(p)
    t = d[0].get_text()
    lines = [l.strip() for l in t.splitlines() if l.strip()]
    print("==", p, "pages", d.page_count)
    print("   meta:", {k: d.metadata.get(k) for k in ("title", "subject", "creationDate", "modDate")})
    for l in lines[:6] + lines[-8:]:
        print("   |", l[:150])
