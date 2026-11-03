"""List plot frames on PDF pages with their axis tick labels and titles.

Usage
-----
python plot_frames_and_labels.py <pdf> <pages>   (pages like 4-9 or 4,6)

A plot frame is taken to be a stroked rectangle-like path (5 points, line
width >= 0.9 pt) between 120 and 260 pt wide.  For each frame the script
prints the frame box in PDF points, the words just left of it (left-axis
ticks with their y centre), right of it (right-axis ticks), below it (x-axis
ticks with their x centre and the axis title) and above it (plot title).
Use the tick positions to build two-point axis calibrations.  Text
extraction is only a locator: confirm against the rendered page.
"""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import pymupdf


def parse_pages(spec):
    pages = []
    for part in spec.split(","):
        if "-" in part:
            a, b = part.split("-")
            pages.extend(range(int(a), int(b) + 1))
        else:
            pages.append(int(part))
    return pages


def main():
    doc = pymupdf.open(sys.argv[1])
    for pno in parse_pages(sys.argv[2]):
        page = doc[pno - 1]
        words = page.get_text("words")
        frames = []
        for d in page.get_drawings():
            r = d["rect"]
            if (d.get("width") or 0) >= 0.9 and 120 < r.width < 260 and 80 < r.height < 200:
                items = d["items"]
                if len(items) in (1, 4) or (len(items) == 1 and items[0][0] == "re"):
                    frames.append(r)
                elif len(items) <= 4:
                    frames.append(r)
        seen = []
        for r in frames:
            if any(abs(r.x0 - s.x0) < 1 and abs(r.y0 - s.y0) < 1 for s in seen):
                continue
            seen.append(r)
            print(f"=== page {pno} frame ({r.x0:.2f},{r.y0:.2f})-({r.x1:.2f},{r.y1:.2f})")
            title = [w for w in words if r.x0 - 10 < (w[0] + w[2]) / 2 < r.x1 + 10 and r.y0 - 32 < w[3] <= r.y0 + 1]
            print("  title:", " ".join(w[4] for w in sorted(title, key=lambda w: (round(w[1]), w[0]))))
            left = [w for w in words if w[2] <= r.x0 + 1 and w[2] > r.x0 - 40 and r.y0 - 6 < (w[1] + w[3]) / 2 < r.y1 + 6]
            print("  left :", " ".join(f"{w[4]}@y{(w[1] + w[3]) / 2:.1f}" for w in sorted(left, key=lambda w: w[1])))
            right = [w for w in words if w[0] >= r.x1 - 1 and w[0] < r.x1 + 40 and r.y0 - 6 < (w[1] + w[3]) / 2 < r.y1 + 6]
            print("  right:", " ".join(f"{w[4]}@y{(w[1] + w[3]) / 2:.1f}" for w in sorted(right, key=lambda w: w[1])))
            below = [w for w in words if r.y1 - 1 <= w[1] < r.y1 + 30 and r.x0 - 15 < (w[0] + w[2]) / 2 < r.x1 + 15]
            print("  below:", " ".join(f"{w[4]}@x{(w[0] + w[2]) / 2:.1f}" for w in sorted(below, key=lambda w: (round(w[1] / 4), w[0]))))


if __name__ == "__main__":
    main()
