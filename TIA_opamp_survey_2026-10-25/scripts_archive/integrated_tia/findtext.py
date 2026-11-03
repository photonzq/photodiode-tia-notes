"""Locate pages containing search terms (case-insensitive), to choose pages to render.

usage: python -I findtext.py <pdf> term1 [term2 ...]
"""
import sys
import pymupdf

pdf = sys.argv[1]
terms = [t.lower() for t in sys.argv[2:]]
d = pymupdf.open(pdf)
print("pages:", d.page_count)
for i in range(d.page_count):
    t = d[i].get_text().lower()
    hits = [term for term in terms if term in t]
    if hits:
        print(i + 1, hits)
