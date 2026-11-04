"""Locate and render pages of PDF documents (layout-level feedback-capacitance survey).

Two sub-commands:

  find    python -I pdf_pages.py find <pdf> <regex> [--context 100]
          Prints the 1-based page index (as a PDF viewer counts pages) and a short
          context window for every match of <regex> in the page text, followed by the
          page count.  Text extraction loses figures and can split numbers, so it is
          used only to decide which pages to render; values are read from the renders.

  render  python -I pdf_pages.py render <pdf> <out_dir> --pages 1-3,7 [--dpi 160]
          [--clip x0,y0,x1,y1] [--prefix name]
          Writes <prefix>_p<NNN>[_clip]_<dpi>dpi.png for each page.  The clip
          rectangle is in PDF points; a pixel (px, py) of a render at D dpi is at
          (px*72/D, py*72/D) points.

  locate  python -I pdf_pages.py locate <pdf> <page> "<exact text>"
          Prints the bounding boxes (PDF points) of an exact text string on one
          page, so that a clip rectangle around it can be rendered and read.

The script is meant to be run in isolated mode (-I), which leaves the per-user
site-packages folder off sys.path; that folder (where PyMuPDF may be installed) is
added back explicitly below.  Downloaded PDFs are treated as data only: paths are
passed as arguments and nothing is imported from the folders that hold them.
"""
import argparse
import pathlib
import re
import site
import sys

_user_site = site.getusersitepackages()
if _user_site not in sys.path:
    sys.path.append(_user_site)

import pymupdf  # noqa: E402  (imported after the path fix above)


def parse_pages(spec, n_pages):
    """Turn '1-3,7' into [1, 2, 3, 7], keeping only pages that exist."""
    if not spec:
        return list(range(1, n_pages + 1))
    pages = []
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            start, stop = part.split("-")
            pages.extend(range(int(start), int(stop) + 1))
        elif part:
            pages.append(int(part))
    return [p for p in pages if 1 <= p <= n_pages]


def cmd_find(args):
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


def cmd_render(args):
    doc = pymupdf.open(args.pdf)
    out_dir = pathlib.Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    prefix = args.prefix or pathlib.Path(args.pdf).stem[:40]
    clip = None
    if args.clip:
        x0, y0, x1, y1 = (float(v) for v in args.clip.split(","))
        clip = pymupdf.Rect(x0, y0, x1, y1)
    for page_no in parse_pages(args.pages, doc.page_count):
        page = doc[page_no - 1]
        pix = page.get_pixmap(dpi=args.dpi, clip=clip)
        tag = "_clip" if clip is not None else ""
        name = out_dir / f"{prefix}_p{page_no:03d}{tag}_{args.dpi}dpi.png"
        pix.save(str(name))
        print(name)
    print(f"page_count={doc.page_count}")


def cmd_locate(args):
    doc = pymupdf.open(args.pdf)
    page = doc[args.page - 1]
    print(f"page {args.page}: size {page.rect.width:.1f} x {page.rect.height:.1f} pt")
    for rect in page.search_for(args.text):
        print(f"{rect.x0:.1f},{rect.y0:.1f},{rect.x1:.1f},{rect.y1:.1f}")


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_loc = sub.add_parser("locate")
    p_loc.add_argument("pdf")
    p_loc.add_argument("page", type=int)
    p_loc.add_argument("text")
    p_loc.set_defaults(func=cmd_locate)
    p_find = sub.add_parser("find")
    p_find.add_argument("pdf")
    p_find.add_argument("regex")
    p_find.add_argument("--context", type=int, default=100)
    p_find.set_defaults(func=cmd_find)
    p_render = sub.add_parser("render")
    p_render.add_argument("pdf")
    p_render.add_argument("out_dir")
    p_render.add_argument("--pages", default="")
    p_render.add_argument("--dpi", type=int, default=160)
    p_render.add_argument("--clip", default="")
    p_render.add_argument("--prefix", default="")
    p_render.set_defaults(func=cmd_render)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
