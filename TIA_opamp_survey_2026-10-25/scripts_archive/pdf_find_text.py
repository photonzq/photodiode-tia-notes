"""List the PDF pages whose text matches a regular expression.

Usage
-----
python pdf_find_text.py <pdf> <regex> [--context 80]

Prints, for every match, the 1-based PDF page index and a short context
window.  Text extraction loses figures and can break words at line ends or
ligatures, so use it only to locate pages; read the rendered page itself.
"""
import argparse
import re
import sys

import pymupdf


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf")
    parser.add_argument("regex")
    parser.add_argument("--context", type=int, default=80)
    args = parser.parse_args()

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    pattern = re.compile(args.regex, re.IGNORECASE)
    doc = pymupdf.open(args.pdf)
    for index, page in enumerate(doc, start=1):
        text = " ".join(page.get_text().split())
        for match in pattern.finditer(text):
            start = max(0, match.start() - args.context)
            stop = min(len(text), match.end() + args.context)
            print(f"p{index:03d}: ...{text[start:stop]}...")
    print(f"page_count={doc.page_count}")


if __name__ == "__main__":
    main()
