"""Render the rows of a datasheet table, or the figures above given captions,
as horizontal strips stacked into one PNG, so that a parameter can be read off
the rendered page without rendering every page whole.

Usage
-----
python spec_rows.py <pdf> <out.png> --terms "Input bias current;Current noise"
                    [--pages 4-9] [--dpi 150] [--above 4] [--below 12]
                    [--header "PARAMETER"] [--figures "Input Voltage Noise"]
                    [--fig-height 250]

* ``--terms`` are literal strings (case-insensitive) separated by ``;``.  Each
  hit becomes a strip across the full page width, from ``above`` points above
  the hit to ``below`` points under it, so that the test conditions and the
  MIN/TYP/MAX/UNIT columns of the same row are on the strip.
* ``--header`` adds the strip of the table's column header on every page that
  has a hit, so that the columns can be identified.
* ``--figures`` are caption strings; for each hit the strip is the column
  (left half, right half or full width) of the caption, from ``fig-height``
  points above the caption to its bottom.
* Text search only locates the strips; the values are read from the renders.
  Every strip is labelled with its 1-based PDF page index.
"""
import argparse
import pathlib

import pymupdf
from PIL import Image, ImageDraw


def parse_pages(spec: str, n_pages: int) -> list[int]:
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


def merge(bands: list[pymupdf.Rect]) -> list[pymupdf.Rect]:
    """Merge strips that overlap vertically and share the same x-range."""
    out: list[pymupdf.Rect] = []
    for band in sorted(bands, key=lambda r: (r.x0, r.y0)):
        for i, kept in enumerate(out):
            if abs(kept.x0 - band.x0) < 1 and abs(kept.x1 - band.x1) < 1 \
                    and band.y0 <= kept.y1 and band.y1 >= kept.y0:
                out[i] = kept | band
                break
        else:
            out.append(pymupdf.Rect(band))
    return sorted(out, key=lambda r: (r.y0, r.x0))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf")
    parser.add_argument("out")
    parser.add_argument("--terms", default="")
    parser.add_argument("--pages", default="")
    parser.add_argument("--dpi", type=int, default=150)
    parser.add_argument("--above", type=float, default=4.0)
    parser.add_argument("--below", type=float, default=12.0)
    parser.add_argument("--header", default="")
    parser.add_argument("--figures", default="")
    parser.add_argument("--fig-height", type=float, default=250.0)
    parser.add_argument("--title-above", action="store_true",
                        help="the figure title sits above the plot "
                             "(Hamamatsu style): take the strip below it")
    args = parser.parse_args()

    doc = pymupdf.open(args.pdf)
    terms = [t for t in args.terms.split(";") if t.strip()]
    captions = [t for t in args.figures.split(";") if t.strip()]
    strips: list[tuple[int, Image.Image]] = []
    for pno in parse_pages(args.pages, doc.page_count):
        page = doc[pno - 1]
        width = page.rect.width
        bands: list[pymupdf.Rect] = []
        for term in terms:
            for hit in page.search_for(term):
                bands.append(pymupdf.Rect(0, hit.y0 - args.above, width,
                                          hit.y1 + args.below))
        if bands and args.header:
            for hit in page.search_for(args.header):
                bands.append(pymupdf.Rect(0, hit.y0 - 3, width, hit.y1 + 10))
        for caption in captions:
            for hit in page.search_for(caption):
                if hit.x1 < width / 2 + 20:
                    x0, x1 = 0, width / 2 + 10
                elif hit.x0 > width / 2 - 20:
                    x0, x1 = width / 2 - 10, width
                else:
                    x0, x1 = 0, width
                if args.title_above:
                    bands.append(pymupdf.Rect(x0, hit.y0 - 3, x1,
                                              hit.y1 + args.fig_height))
                else:
                    bands.append(pymupdf.Rect(x0, hit.y0 - args.fig_height,
                                              x1, hit.y1 + 2))
        for band in merge(bands):
            band = band & page.rect
            pix = page.get_pixmap(dpi=args.dpi, clip=band)
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            strips.append((pno, img))

    if not strips:
        print("no hits")
        return
    label_h = 14
    total_h = sum(img.height + label_h + 2 for _, img in strips)
    total_w = max(img.width for _, img in strips)
    sheet = Image.new("RGB", (total_w, total_h), "white")
    draw = ImageDraw.Draw(sheet)
    y = 0
    for pno, img in strips:
        draw.rectangle([0, y, total_w, y + label_h - 1], fill=(225, 225, 225))
        draw.text((4, y + 1), f"PDF page {pno}", fill=(0, 0, 0))
        y += label_h
        sheet.paste(img, (0, y))
        y += img.height + 2
    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    print(f"{out} {sheet.width}x{sheet.height} from {len(strips)} strips")


if __name__ == "__main__":
    main()
