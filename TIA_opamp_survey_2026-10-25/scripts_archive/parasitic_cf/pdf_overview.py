"""Print a short overview of one or more PDF documents: page count, metadata
(title, author, creation and modification dates) and the first characters of
the text of every page.

Usage:
    python -I pdf_overview.py <pdf> [<pdf> ...] [--chars 300]

The overview is used only to identify a document (title, document number,
revision or date) and to decide which pages to render with pdf_pages.py.
Values quoted in the notes are read from the rendered page images, because
dimension drawings and tables are lost or garbled in extracted text.

Run in isolated mode (-I) with the paths passed as arguments; downloaded PDFs
are treated as data only.  The per-user site-packages folder (where PyMuPDF
may be installed) is added back to sys.path explicitly.
"""
import argparse
import site
import sys

_user_site = site.getusersitepackages()
if _user_site not in sys.path:
    sys.path.append(_user_site)

import pymupdf  # noqa: E402  (imported after the path fix above)


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pdfs", nargs="+")
    parser.add_argument("--chars", type=int, default=300)
    args = parser.parse_args()
    for path in args.pdfs:
        print(f"===== {path}")
        try:
            doc = pymupdf.open(path)
        except Exception as exc:  # a damaged file is reported, not fatal
            print(f"not readable: {exc}")
            continue
        print(f"page_count={doc.page_count}")
        meta = doc.metadata or {}
        for key in ("title", "author", "subject", "creationDate", "modDate", "producer"):
            print(f"{key}: {meta.get(key, '')}")
        for index, page in enumerate(doc, start=1):
            text = " ".join(page.get_text().split())
            print(f"--- p{index:03d}: {text[:args.chars]}")
        print()


if __name__ == "__main__":
    main()
