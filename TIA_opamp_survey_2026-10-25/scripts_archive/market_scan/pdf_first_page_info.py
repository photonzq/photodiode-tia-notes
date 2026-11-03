"""Print PDF metadata, page count and the opening text of page 1 for each
file, to fill in bibliographic details (title, document number, date).
Text extraction is used here only to identify documents, never for numbers.

Usage
-----
python pdf_first_page_info.py <chars> <pdf> [<pdf> ...]
"""
import pathlib
import sys

import pymupdf


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    chars = int(sys.argv[1])
    for name in sys.argv[2:]:
        doc = pymupdf.open(name)
        meta = {k: v for k, v in (doc.metadata or {}).items()
                if k in ("title", "author", "creationDate", "modDate") and v}
        text = " ".join(doc[0].get_text().split())[:chars]
        print(f"== {pathlib.Path(name).name} | pages={doc.page_count} | {meta}")
        print(f"   {text}")


if __name__ == "__main__":
    main()
