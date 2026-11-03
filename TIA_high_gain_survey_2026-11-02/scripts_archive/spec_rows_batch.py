"""Run spec_rows.py over the electrical-characteristics pages of several
datasheets, one stacked PNG per datasheet.

Usage
-----
python spec_rows_batch.py <out_dir> <pdf> [<pdf> ...] [--dpi 125]

The pages are those whose text contains "electrical characteristics" or
"specifications" (case-insensitive) among the first 14 pages; the strips are
the rows of the parameters that matter for a high-gain transimpedance
amplifier.  Text search only locates the rows; the values are read from the
renders.
"""
import argparse
import pathlib
import subprocess
import sys

import pymupdf

TERMS = ";".join([
    "Input bias current", "Input current noise", "current noise density",
    "Input voltage noise", "voltage noise density", "Voltage noise",
    "Current noise", "Gain-bandwidth", "Gain bandwidth", "Unity-gain bandwidth",
    "Input capacitance", "INPUT IMPEDANCE", "Differential", "Common-mode input",
    "Input offset voltage", "Offset voltage", "Gain bandwidth product",
])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("out_dir")
    parser.add_argument("pdfs", nargs="+")
    parser.add_argument("--dpi", type=int, default=125)
    args = parser.parse_args()
    here = pathlib.Path(__file__).resolve().parent
    for pdf in args.pdfs:
        doc = pymupdf.open(pdf)
        pages = []
        for index in range(min(14, doc.page_count)):
            text = doc[index].get_text().lower()
            if "electrical characteristics" in text or "specifications" in text:
                pages.append(str(index + 1))
        if not pages:
            print(f"{pdf}: no specification pages found")
            continue
        out = pathlib.Path(args.out_dir) / (pathlib.Path(pdf).stem + "_rows.png")
        subprocess.run([sys.executable, str(here / "spec_rows.py"), pdf,
                        str(out), "--pages", ",".join(pages), "--terms", TERMS,
                        "--header", "PARAMETER", "--dpi", str(args.dpi),
                        "--above", "3", "--below", "22"], check=False)


if __name__ == "__main__":
    main()
