"""Render PDF pages (or a clipped region of one page) to PNG images.

Usage
-----
python render_pdf_pages.py <pdf> <out_dir> [--dpi 160] [--pages 1-5,7]
                           [--clip x0,y0,x1,y1] [--prefix name]

* Page numbers on the command line are 1-based PDF page indices (not the
  printed page numbers, which often differ).
* The clip rectangle is given in PDF points (1/72 inch) of the page.  A
  pixel coordinate (px, py) read off a render made at D dpi converts to
  points as (px * 72 / D, py * 72 / D).
* Output files are named <prefix>_p<NNN>[_clip]_<dpi>dpi.png.
"""
import argparse
import pathlib

import pymupdf


def parse_pages(spec: str, n_pages: int) -> list[int]:
    """Turn '1-3,7' into [1, 2, 3, 7], keeping only valid page numbers."""
    if not spec:
        return list(range(1, n_pages + 1))
    pages: list[int] = []
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            start, stop = part.split("-")
            pages.extend(range(int(start), int(stop) + 1))
        elif part:
            pages.append(int(part))
    return [p for p in pages if 1 <= p <= n_pages]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf")
    parser.add_argument("out_dir")
    parser.add_argument("--dpi", type=int, default=160)
    parser.add_argument("--pages", default="")
    parser.add_argument("--clip", default="")
    parser.add_argument("--prefix", default="")
    args = parser.parse_args()

    doc = pymupdf.open(args.pdf)
    out_dir = pathlib.Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    prefix = args.prefix or pathlib.Path(args.pdf).stem

    clip = None
    if args.clip:
        x0, y0, x1, y1 = (float(v) for v in args.clip.split(","))
        clip = pymupdf.Rect(x0, y0, x1, y1)

    for page_no in parse_pages(args.pages, doc.page_count):
        page = doc[page_no - 1]
        pix = page.get_pixmap(dpi=args.dpi, clip=clip)
        tag = "_clip" if clip is not None else ""
        name = out_dir / f"{prefix}_p{page_no:03d}{tag}_{args.dpi}dpi.png"
        pix.save(name)
        print(name)
    print(f"page_count={doc.page_count}  page_size_pt={tuple(round(v, 1) for v in doc[0].rect)}")


if __name__ == "__main__":
    main()
