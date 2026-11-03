"""List the numbers of an old version of the report that the new version no longer contains.

A "number" is a numeric token with its unit or range as written (for example "0.230 ± 0.070 pF",
"62.5–69.1°", "−47 dBc", "1.16–1.17 mA"); section, equation, table and figure numbers are ignored.
Every token of the old text (or of a line range of it) is looked up in the new text; the tokens that
no longer occur anywhere are printed with their old line, so that each can be checked: either it is
restated in other words, or it has to be put back.  Used to confirm that merging repeated passages
kept every distinct number.

Usage: python check_numbers_kept.py <old.md> <new.md> [<first line> <last line> of the old text]
"""
import re
import sys

REF = re.compile(r"\b(?:Sections?|Chapters?|Appendix|Appendices|Tables?|Figures?|Fig\.?|Eqs?\.|items?|p|pp\.)"
                 r"\s*[A-F]?\(?\d+(?:\.\d+)*[a-z]?\)?(?:(?:–|, | and )\(?[A-F]?\d+(?:\.\d+)*[a-z]?\)?)*")
UNIT = r"(?:\s?(?:%|°|dBc|dBm|dB|pA/√Hz|nA rms|nA|µA|mA|A\b|pF|fF|nF|µF|kΩ|Ω|MHz|GHz|kHz|Hz|nV/√Hz|V/µs|V\b|mV|ns|µs|ps|W\b|mW|K\b|°C|mS/pF|mS|pA²/Hz))?"
NUM = re.compile(r"[−-]?\d+(?:[.,]\d+)?(?:\s?(?:±|–|to)\s?[−-]?\d+(?:[.,]\d+)?)*" + UNIT)


def tokens(text):
    text = REF.sub(" ", text)
    out = []
    for m in NUM.finditer(text):
        t = m.group(0).strip()
        if re.fullmatch(r"[−-]?\d", t):                # single digits are list markers and counts
            continue
        out.append(t)
    return out


def main():
    old = open(sys.argv[1], encoding="utf-8").read().split("\n")
    new = open(sys.argv[2], encoding="utf-8").read()
    a, b = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (1, len(old))
    new_norm = re.sub(r"\s+", " ", REF.sub(" ", new))
    missing = []
    for i in range(a - 1, b):
        for t in tokens(old[i]):
            if t not in new_norm and t.replace(" ", "") not in new_norm.replace(" ", ""):
                missing.append((i + 1, t))
    print(f"lines {a}-{b} of the old text: {len(missing)} numbers not found in the new text")
    for i, t in missing:
        print(f"L{i}: {t}    | {old[i - 1].strip()[:150]}")


if __name__ == "__main__":
    main()
