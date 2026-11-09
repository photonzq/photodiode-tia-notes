"""Figure layout for the PDF and web page of a note built with TIA_notes/build: classify every figure and, with
--apply, mark the note up for the layout.

Rules:
- tall: a figure drawn about 6.5 in wide whose height is at least 0.9 times its width is shown at 60 % of the text
  width, centred; its image line gets {.tall}.
- side: a single-panel figure drawn at most 4.5 in wide floats to the right at 52 % of the text width with its
  caption, where the plain text after it, up to the next heading, table, display equation, image or caption,
  holds at least 80 % of the figure's height. The height is taken as 0.52 x 6.7 in x (height/width) + 0.9 in for
  the caption, and the narrow column beside it holds about 300 characters per inch of height.
- pair: two small figures with nothing between them sit side by side, each at 48 % of the text width (an outer
  div "pair" holding two divs "half").
- narrow: a small figure that can neither float nor pair is centred at 65 % of the text width with its caption.
- full: a figure drawn about 6.5 in wide that is wider than tall stays at full width.
The drawn size comes from the PNG (pixels over the stored dpi, 600 if none). "![Figure N]" and "*Figure N." stay at
the start of their lines, and every closing fence has a blank line before it, so that pandoc keeps the caption a
paragraph and the build anchors the figure. The style block that defines the classes is appended to the note. The
note's line endings are kept and nothing else changes.

Usage: python figure_layout.py <note.md> [--apply]
"""
import re
import sys
from pathlib import Path

from PIL import Image

SMALL_WIDTH_IN = 4.5
TALL_RATIO = 0.9
TEXT_WIDTH_IN, SIDE_FRACTION, CAPTION_IN, CHARS_PER_IN, FILL = 6.7, 0.52, 0.9, 300, 0.8
CLEARING = ("#", "|", "$$", "![", ":::", "*Table", "*Figure", "<style>")
FIGURE = re.compile(r"^!\[Figure (\d+)\]\(([^)\s]+)\)\s*$")
STYLE = [
    "<style>",
    "img.tall { width: 60%; }",
    "div.side { float: right; width: 52%; margin: 0.15em 0 0.8em 1.4em; break-inside: avoid; }",
    "div.side img, div.half img, div.narrow img { width: 100%; margin: 0 0 0.3em 0; }",
    "div.side p, div.half p, div.narrow p { margin: 0.2em 0; }",
    "div.pair { display: flex; justify-content: space-between; align-items: flex-start; break-inside: avoid; }",
    "div.half { width: 48%; }",
    "div.narrow { width: 65%; margin: 0.6em auto; break-inside: avoid; }",
    "img, table, .eqn, h1, h2, h3, h4, div.pair, div.narrow { clear: both; }",
    "</style>",
]


def drawn_size(path: Path) -> tuple[float, float]:
    """Drawn width and height in inches: pixels over the stored dpi, 600 if none."""
    with Image.open(path) as im:
        dpi = (im.info.get("dpi") or (600, 600))[0] or 600
        return im.size[0] / dpi, im.size[1] / dpi


def classify(lines: list[str], folder: Path) -> list[dict]:
    figs = []
    for i, line in enumerate(lines):
        m = FIGURE.match(line)
        if not m:
            continue
        num, rel = m.group(1), m.group(2)
        w, h = drawn_size(folder / rel)
        ok = (i + 3 < len(lines) and lines[i - 1] == "" and lines[i + 1] == ""
              and lines[i + 2].startswith(f"*Figure {num}. ") and lines[i + 3] == "")
        size = "small" if w <= SMALL_WIDTH_IN else ("tall" if h / w >= TALL_RATIO else "wide")
        k, chars = i + 3, 0
        while k < len(lines) and not lines[k].startswith(CLEARING):
            chars += len(lines[k])
            k += 1
        need = CHARS_PER_IN * (SIDE_FRACTION * TEXT_WIDTH_IN * h / w + CAPTION_IN)
        figs.append(dict(num=num, rel=rel, line=i, w=w, h=h, size=size, ok=ok, chars=chars, need=need,
                         next_line=k, gap_blank=all(x == "" for x in lines[i + 3:k])))
    by_line = {f["line"]: f for f in figs}
    for f in figs:
        f["layout"] = {"tall": "tall", "wide": "full"}.get(f["size"])
    for f in figs:
        if f["size"] != "small" or f["layout"]:
            continue
        nxt = by_line.get(f["next_line"])
        if not f["ok"]:
            f["layout"] = "unchanged (caption not in the expected form)"
        elif f["gap_blank"] and nxt and nxt["size"] == "small" and nxt["ok"] and not nxt["layout"]:
            f["layout"], nxt["layout"] = "pair (first)", "pair (second)"
        elif f["chars"] >= FILL * f["need"]:
            f["layout"] = "side"
        else:
            f["layout"] = "narrow"
    return figs


def apply(lines: list[str], figs: list[dict]) -> list[str]:
    out = list(lines)
    for f in sorted(figs, key=lambda f: f["line"], reverse=True):  # from the end, so earlier lines keep their place
        i, lay = f["line"], f["layout"]
        img, cap = out[i], out[i + 2] if i + 2 < len(out) else ""
        if lay == "tall":
            out[i] = img.rstrip() + "{.tall}"
        elif lay in ("side", "narrow"):
            out[i:i + 3] = [f"::: {lay}", img, "", cap, "", ":::"]
        elif lay == "pair (first)":
            out[i:i + 3] = [":::: pair", "::: half", img, "", cap, "", ":::"]
        elif lay == "pair (second)":
            out[i:i + 3] = ["::: half", img, "", cap, "", ":::", "::::"]
    return out


def main(path: str, do_apply: bool) -> None:
    p = Path(path)
    raw = p.read_bytes().decode("utf-8")
    nl = "\r\n" if "\r\n" in raw else "\n"
    lines = raw.split(nl)
    figs = classify(lines, p.parent)
    print(f"{p.name}: {len(figs)} figures, line endings {'CRLF' if nl == chr(13) + chr(10) else 'LF'}")
    print("| Figure | File | Drawn size (in) | Height/width | Size class | Text after (chars) | Needed for a float (80 %) | Layout |")
    print("|---|---|---|---|---|---|---|---|")
    for f in figs:
        small = f["size"] == "small"
        print(f"| {f['num']} | `{Path(f['rel']).name}` | {f['w']:.2f} × {f['h']:.2f} | {f['h'] / f['w']:.2f} | {f['size']} | "
              f"{f['chars'] if small else '—'} | {round(FILL * f['need']) if small else '—'} | {f['layout']} |")
    if not do_apply:
        return
    assert "<style>" not in raw, "a style block is already in the note"
    assert all(not f["layout"].startswith("unchanged") for f in figs), "a caption is not in the expected form"
    out = apply(lines, figs)
    while out and out[-1] == "":
        out.pop()
    text = nl.join(out + [""] + STYLE) + nl
    p.write_bytes(text.encode("utf-8"))
    print(f"applied; the note now has {text.count('![Figure')} figure lines")


if __name__ == "__main__":
    main(sys.argv[1], "--apply" in sys.argv[2:])
