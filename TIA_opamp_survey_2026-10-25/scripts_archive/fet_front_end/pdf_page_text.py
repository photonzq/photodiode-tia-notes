"""Print the extracted text of selected PDF pages (to locate tables only).

Usage
-----
python pdf_page_text.py <pdf> <pages> [--chars 4000]

<pages> is a 1-based list such as "2,3" or "2-4".  Text extraction loses
figures and may scramble table columns; confirm every value on the
rendered page image before using it.
"""
import argparse
import sys

import pymupdf


def parse_pages(spec: str) -> list[int]:
    pages: list[int] = []
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-")
            pages.extend(range(int(a), int(b) + 1))
        elif part:
            pages.append(int(part))
    return pages


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf")
    parser.add_argument("pages")
    parser.add_argument("--chars", type=int, default=4000)
    args = parser.parse_args()

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    doc = pymupdf.open(args.pdf)
    for page_no in parse_pages(args.pages):
        if not 1 <= page_no <= doc.page_count:
            continue
        text = " ".join(doc[page_no - 1].get_text().split())
        print(f"=== PDF page {page_no} of {doc.page_count}")
        print(text[: args.chars])
        print()


if __name__ == "__main__":
    main()
