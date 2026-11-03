"""Print a short identification of one or more PDF files.

Usage
-----
python pdf_identify.py <pdf> [<pdf> ...] [--chars 500]

For each file: page count, the document metadata (title, author, creation
and modification dates), and the first characters of the text of page 1
and of the last page.  Meant only to tell which datasheet and revision a
downloaded file is; read the rendered pages for the data themselves.
"""
import argparse
import sys

import pymupdf


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdfs", nargs="+")
    parser.add_argument("--chars", type=int, default=500)
    args = parser.parse_args()

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    for path in args.pdfs:
        try:
            doc = pymupdf.open(path)
        except Exception as exc:  # noqa: BLE001 - report and continue
            print(f"=== {path}: cannot open ({exc})")
            continue
        meta = doc.metadata or {}
        print(f"=== {path}")
        print(f"pages={doc.page_count}  title={meta.get('title')!r}  "
              f"author={meta.get('author')!r}")
        print(f"created={meta.get('creationDate')!r}  "
              f"modified={meta.get('modDate')!r}")
        first = " ".join(doc[0].get_text().split())
        print(f"p1: {first[:args.chars]}")
        if doc.page_count > 1:
            last = " ".join(doc[doc.page_count - 1].get_text().split())
            print(f"last: {last[:args.chars]}")
        print()


if __name__ == "__main__":
    main()
